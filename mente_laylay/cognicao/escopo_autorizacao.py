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


@dataclass(frozen=True, slots=True)
class AutorizacaoAto:
    turno_id: str
    indice: int
    texto: str
    pedido: SnapshotComandoIA

    def __post_init__(self) -> None:
        if not (isinstance(self.turno_id, str) and self.turno_id.strip() == self.turno_id
                and self.turno_id and type(self.indice) is int and self.indice >= 0
                and isinstance(self.texto, str) and self.texto.strip()
                and isinstance(self.pedido, SnapshotComandoIA)):
            raise ValueError("Autorização por ato exige identidade, fonte e snapshot canônicos.")


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
    return texto_pede_ajuste_parametrico_contextual(fonte) or len(segmentos) > 1 or any(isinstance(s, Mapping) and (
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
        frame = deepcopy(dict(mental))
        # Um resolver não pode usar a permissão agregada como se pertencesse
        # ao ato isolado. O texto classificado identifica o ato; somente seu
        # recorte original comprovado fornece argumentos ao resolver.
        frame["turno_atual"] = {**deepcopy(dict(segmento)), "id": turno.get("id"),
                               "texto": fonte_resolucao, "texto_original": fonte_resolucao,
                               "texto_operacional": fonte_resolucao,
                               "segmentos": [deepcopy(dict(segmento))]}
        try:
            pedido = resolver(fonte_resolucao, frame)
            if not isinstance(pedido, dict) or not isinstance(pedido.get("params"), dict):
                continue
            autorizacoes.append(AutorizacaoAto(str(turno.get("id") or ""), indice,
                                              texto, SnapshotComandoIA(pedido)))
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
    """Uma operação exata por ato: não emprestar alvo ou repetir o efeito."""
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
        if identidade == _identidade_operacional(autorizacao.pedido.como_dict()):
            return autorizacao.indice
    return None
