"""Vínculo de propostas a atos autorizados; não resolve linguagem nem executa.

A resolução vem do serviço canônico injetado. Sem resolução inequívoca não
existe escopo. IDs de ocorrência e dados da LLM não concedem autorização.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from typing import Any, Callable, Mapping

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
from mente_laylay.cognicao.gramatica_operacional import texto_pede_ajuste_parametrico_contextual
from mente_laylay.cognicao.coordenacao_nominal import (
    CoordenacaoNominal, ler_coordenacao_nominal, alvo_resolvido_exato,
)


@dataclass(frozen=True, slots=True)
class AutorizacaoAto:
    turno_id: str
    indice: int
    texto: str
    pedido: SnapshotComandoIA
    indice_alvo: int = 0
    fonte_nominal: CoordenacaoNominal | None = None

    def __post_init__(self) -> None:
        if not (isinstance(self.turno_id, str) and self.turno_id.strip() == self.turno_id
                and self.turno_id and type(self.indice) is int and self.indice >= 0
                and isinstance(self.texto, str) and self.texto.strip()
                and isinstance(self.pedido, SnapshotComandoIA)):
            raise ValueError("Autorização por ato exige identidade, fonte e snapshot canônicos.")
        if type(self.indice_alvo) is not int or self.indice_alvo < 0 or (
            self.fonte_nominal is None and self.indice_alvo != 0
        ) or (self.fonte_nominal is not None and (
            type(self.fonte_nominal) is not CoordenacaoNominal or not self.fonte_nominal.inequivoca
            or not self.indice_alvo < len(self.fonte_nominal.alvos)
        )):
            raise ValueError("Autorização nominal exige membro da fonte qualificada.")

    @property
    def chave_consumo(self) -> tuple[int, int]:
        return self.indice, self.indice_alvo


@dataclass(frozen=True, slots=True)
class AtoAguardandoMaterializacao:
    """Obrigação do turno, não comando, permissão, receipt ou fila autônoma."""

    turno_id: str
    indice: int
    fonte_textual: str
    fonte: SnapshotComandoIA

    def __post_init__(self) -> None:
        if (not isinstance(self.turno_id, str) or not self.turno_id.strip() or self.turno_id != self.turno_id.strip()
            or type(self.indice) is not int or self.indice < 0
            or not isinstance(self.fonte_textual, str)
            or not isinstance(self.fonte, SnapshotComandoIA)):
            raise ValueError("obrigacao_contextual_sem_identidade")
        dados = self.fonte.como_dict()
        intervalo = dados.get("intervalo")
        if (set(dados) != {"indice_segmento", "texto_original", "intervalo", "origem", "autoriza_execucao", "comprova_efeito"}
            or type(dados.get("indice_segmento")) is not int or dados.get("indice_segmento") != self.indice
            or dados.get("origem") != "segmentacao_canonica"
            or dados.get("autoriza_execucao") is not False or dados.get("comprova_efeito") is not False
            or not isinstance(intervalo, list) or len(intervalo) != 2
            or any(type(i) is not int for i in intervalo)
            or not 0 <= intervalo[0] < intervalo[1] <= len(self.fonte_textual)
            or self.fonte_textual[slice(*intervalo)] != dados.get("texto_original")):
            raise ValueError("obrigacao_contextual_sem_fonte_vinculada")

    def como_dict(self) -> dict[str, Any]:
        dados = self.fonte.como_dict()
        return {"turno_id": self.turno_id, "indice": self.indice,
            "texto_original": dados["texto_original"], "intervalo": dados["intervalo"],
            "origem": dados["origem"], "estado": "aguarda_materializacao_contextual",
            "autoriza_execucao": False, "comprova_efeito": False}


def coletar_atos_aguardando_materializacao(turno: Mapping[str, Any]) -> tuple[AtoAguardandoMaterializacao, ...]:
    """Conserva pedidos contextuais sem atribuir antecedente ou alvo futuro.

    A classificação declara necessidade de contexto, não dependência causal
    da etapa anterior. Fonte literal ausente/ambígua não é reconstruída aqui.
    """
    from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
    segmentos = turno.get("segmentos") or ()
    if len(segmentos) <= 1:
        return ()
    texto = str(turno.get("texto_original") or turno.get("texto") or "")
    fontes = fontes_textuais_dos_segmentos(texto, segmentos)
    if len(fontes) != len(segmentos):
        return ()
    return tuple(AtoAguardandoMaterializacao(str(turno.get("id") or ""), indice, texto, fontes[indice])
        for indice, s in enumerate(segmentos) if isinstance(s, Mapping)
        and s.get("autoriza_execucao") is True and s.get("depende_contexto") is True
        and not s.get("veto_execucao_operacional") and not s.get("requer_esclarecimento"))


def exige_escopo_por_ato(turno: Mapping[str, Any]) -> bool:
    """Mais de um ato exige escopo próprio, mesmo com permissão agregada.

    O retrato global não delimita cada operação/alvo do conjunto: pode tanto
    excluir outro pedido legítimo quanto aceitar um alvo que ninguém pediu.
    Reutiliza-se o resolver e o vínculo exato existentes; ausência de resolução
    continua fechada. Atribuição paramétrica elíptica também exige vínculo:
    um valor ilegível ou referente ausente não autoriza outro domínio. Os
    demais atos únicos conservam seu contrato agregado anterior.
    """
    segmentos = turno.get("segmentos") or ()
    fonte = turno.get("texto_operacional_efetivo", turno.get("texto_original") or turno.get("texto") or "")
    return ler_coordenacao_nominal(str(fonte)) is not None or texto_pede_ajuste_parametrico_contextual(fonte) or len(segmentos) > 1 or any(isinstance(s, Mapping) and (
        s.get("autoriza_execucao") is False or s.get("veto_execucao_operacional") is True
    ) for s in segmentos)


def construir_autorizacoes_por_ato(
    turno: Mapping[str, Any], mental: Mapping[str, Any],
    resolver: Callable[[str, dict], dict | None] | None,
) -> tuple[AutorizacaoAto, ...]:
    """Resolve só atos autorizados no frame capturado; falhas ficam fechadas."""
    if not callable(resolver):
        return ()
    from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
    segmentos = turno.get("segmentos") or ()
    fonte_turno = str(turno.get("texto_original") or turno.get("texto") or "")
    fontes = fontes_textuais_dos_segmentos(fonte_turno, segmentos)
    if len(fontes) != len(segmentos):
        return ()
    autorizacoes = []
    for indice, segmento in enumerate(segmentos):
        if not isinstance(segmento, Mapping) or not (
            segmento.get("autoriza_execucao") is True
            and not segmento.get("veto_execucao_operacional")
            and not segmento.get("requer_esclarecimento")
            and not segmento.get("depende_contexto")
        ):
            continue
        texto = str(segmento.get("texto") or "").strip()
        if not texto:
            continue
        fonte_resolucao = fontes[indice].como_dict()["texto_original"]
        nominal = ler_coordenacao_nominal(fonte_resolucao)
        if nominal is not None and not nominal.inequivoca:
            continue
        frame = deepcopy(dict(mental))
        # Um resolver não pode usar a permissão agregada como se pertencesse
        # ao ato isolado. O texto classificado identifica o ato; somente seu
        # recorte original comprovado fornece argumentos ao resolver.
        frame["turno_atual"] = {**deepcopy(dict(segmento)), "id": turno.get("id"),
                               "texto": fonte_resolucao, "texto_original": fonte_resolucao,
                               "texto_operacional": fonte_resolucao,
                               "segmentos": [deepcopy(dict(segmento))]}
        try:
            membros = range(len(nominal.alvos)) if nominal else range(1)
            resolvidos, identidades = [], set()
            for membro in membros:
                # O segmento e sua fonte continuam integrais. Apenas a entrada
                # do resolver é uma projeção dos recortes explícitos do ato.
                pedido = resolver(nominal.projetar(membro) if nominal else fonte_resolucao, deepcopy(frame))
                if (not isinstance(pedido, dict) or not isinstance(pedido.get("params"), dict)
                    or nominal is not None and not alvo_resolvido_exato(pedido, nominal, membro)):
                    resolvidos = []  # Cardinalidade do conjunto não comprovada.
                    break
                identidade = _identidade_operacional(pedido)
                if identidade is None:
                    resolvidos = []
                    break
                if identidade in identidades:
                    continue  # Repetir o nome num conjunto não pede repetir o efeito.
                identidades.add(identidade)
                resolvidos.append(AutorizacaoAto(str(turno.get("id") or ""), indice,
                    texto, SnapshotComandoIA(pedido), membro, nominal))
            autorizacoes.extend(resolvidos)
        except Exception:
            # Indeterminação ou dependência indisponível não é permissão.
            continue
    return tuple(autorizacoes)


def _identidade_operacional(comando: dict) -> str | None:
    # Este adaptador já é o owner da equivalência flat/canônica. Não extrair
    # intenção, verbo ou alvo novamente da frase dentro do porteiro.
    from mente_laylay.autonomia.dispatcher_comandos_json import normalizar_candidato_json_para_intencao

    try:
        normalizado = normalizar_candidato_json_para_intencao(comando, compactar_aliases=True)
        if normalizado is None:
            return None
        params = deepcopy(normalizado["params"])
        params.setdefault("target", "pc_a")
        # Identificador de aplicativo Windows é insensível a caixa. Conteúdo,
        # caminhos, consultas e URLs NÃO sofrem normalização lexical aqui.
        if isinstance(params.get("nome_app"), str):
            params["nome_app"] = params["nome_app"].casefold()
        return json.dumps({"intent": normalizado["intent"], "params": params},
                          ensure_ascii=False, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError, KeyError):
        return None


def vincular_proposta_ao_ato(
    comando: dict, turno: Mapping[str, Any],
    autorizacoes: tuple[AutorizacaoAto, ...], usados: set[int],
) -> int | None:
    """Compatibilidade dos consumidores por ato; não alterar seu índice."""
    autorizacao = vincular_proposta_ao_escopo(comando, turno, autorizacoes, usados)
    return autorizacao.indice if autorizacao is not None else None


def vincular_proposta_ao_escopo(
    comando: dict, turno: Mapping[str, Any],
    autorizacoes: tuple[AutorizacaoAto, ...], usados: set[int | tuple[int, int]],
) -> AutorizacaoAto | None:
    """Uma operação por escopo de alvo, conservando a identidade do ato."""
    identidade = _identidade_operacional(comando)
    if identidade is None:
        return None
    segmentos = turno.get("segmentos") or ()
    for autorizacao in autorizacoes:
        if not isinstance(autorizacao, AutorizacaoAto) or (
            autorizacao.turno_id != str(turno.get("id") or "")
            or not autorizacao.turno_id
            or type(autorizacao.indice) is not int
            or autorizacao.indice in usados
            or autorizacao.chave_consumo in usados
            or not 0 <= autorizacao.indice < len(segmentos)
        ):
            continue
        segmento = segmentos[autorizacao.indice]
        if not isinstance(segmento, Mapping) or not (
            segmento.get("autoriza_execucao") is True
            and not segmento.get("veto_execucao_operacional")
            and not segmento.get("depende_contexto")
            and not segmento.get("requer_esclarecimento")
            and str(segmento.get("texto") or "").strip() == autorizacao.texto
        ):
            continue
        if autorizacao.fonte_nominal is not None:
            from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
            fontes = fontes_textuais_dos_segmentos(
                str(turno.get("texto_original") or turno.get("texto") or ""), segmentos,
            )
            if len(fontes) != len(segmentos) or autorizacao.fonte_nominal != ler_coordenacao_nominal(
                fontes[autorizacao.indice].como_dict()["texto_original"]
            ):
                continue
        if identidade == _identidade_operacional(autorizacao.pedido.como_dict()):
            return autorizacao
    return None
