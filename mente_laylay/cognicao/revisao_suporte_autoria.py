"""Revisão do suporte proposto, sem autoaprovação de implicação pela LLM."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from typing import Any
from urllib.parse import urlsplit

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
from mente_laylay.cognicao.fundamentacao_factual import avaliar_validade_fundamentacao
from mente_laylay.cognicao.proveniencia_informacao import (
    classificar_proveniencia_informacao, referencia_alegacao_da_fonte,
)
from mente_laylay.cognicao.suporte_autoria import SuporteAutoriaProposto, AutoriaRevisadaProposta
from mente_laylay.cognicao.validacao_contrato_fala import conferir_ato_social, inventariar_atos_autoria


@dataclass(frozen=True, slots=True)
class RevisaoSuporteAutoria:
    dados: SnapshotComandoIA
    fala_realizada: str
    aplicar_limite: bool
    semantica_verificada: bool = field(default=False, init=False)
    prova_implicacao: bool = field(default=False, init=False)
    autoriza_execucao: bool = field(default=False, init=False)

    def como_dict(self) -> dict[str, Any]:
        return {**self.dados.como_dict(), "semantica_verificada": False,
                "prova_implicacao": False, "autoriza_execucao": False}


_LIMITE = "Não consegui verificar se as fontes citadas sustentam essas afirmações."
_APOIOS_CONFERIDOS = frozenset({"literal_integral_na_fonte", "parafrase_estrutural_conferida"})


def _derivar_parafrase_estrutural(fonte: str, proposicao: str) -> dict[str, Any] | None:
    """Confere uma equivalência em gramática fechada, não prosa arbitrária.

    `valor(atributo, entidade) = literal` e sua ordem invertida denotam a mesma
    atribuição. Os três termos entre guillemets são identificadores textuais
    opacos: não se resolvem pronomes, sinônimos, unidades ou entidades externas.
    A leitura integral das duas formas impede eliminar ressalvas da fonte ou
    acrescentar conclusões. Nenhum papel ou passo proposto pela IA é consumido.
    """
    atomo = r"«(?P<%s>[^«»\r\n]{1,120})»"
    atributo, entidade, valor = (atomo % papel for papel in ("atributo", "entidade", "valor"))
    formas = (
        ("valor_atributo", rf"O valor do atributo {atributo} de {entidade} é {valor}\."),
        ("valor_anteposto", rf"{valor} é o valor do atributo {atributo} de {entidade}\."),
    )

    def ler(texto: str) -> dict[str, Any] | None:
        for nome, padrao in formas:
            leitura = re.fullmatch(padrao, texto, flags=re.IGNORECASE)
            if leitura is None:
                continue
            papeis = leitura.groupdict()
            if any(t != t.strip() or not t.isprintable() for t in papeis.values()):
                return None
            return {"forma": nome, "papeis": papeis,
                    "intervalos": {p: list(leitura.span(p)) for p in papeis}}
        return None

    origem, destino = ler(fonte), ler(proposicao)
    if (origem is None or destino is None or origem["forma"] == destino["forma"]
        or origem["papeis"] != destino["papeis"]):
        return None
    return {
        "regra": "simetria_valor_atributo_v1",
        "escopo": "equivalencia_de_atribuicoes_textuais_integrais",
        "formas": {"fonte": origem["forma"], "proposicao": destino["forma"]},
        "papeis": origem["papeis"],
        "intervalos": {"fonte": origem["intervalos"], "proposicao": destino["intervalos"]},
        "fonte_sha256": hashlib.sha256(fonte.encode("utf-8")).hexdigest(),
        "proposicao_sha256": hashlib.sha256(proposicao.encode("utf-8")).hexdigest(),
        "apoio_estrutural_conferido": True,
        "prova_semantica_livre": False, "pode_confirmar_fato_externo": False,
        "autoriza_execucao": False,
    }


def revisar_suporte_autoria(
    fala: str, *, plano: dict[str, Any], agora: float | None = None,
) -> RevisaoSuporteAutoria | None:
    """Lê apenas fontes individuais do contexto canônico deste turno.

    Identidade literal integral permite citação atribuída. Uma derivação da
    gramática fechada permite paráfrase atribuída, sem certificar verdade externa
    ou implicação livre. Resumo agregado, opinião da LLM, nome de rota e
    referências internas não substituem conteúdo observado.
    """
    suporte = plano.get("suporte_autoria_proposto")
    revisada = plano.get("autoria_revisada_proposta")
    if type(revisada) is AutoriaRevisadaProposta:
        suporte = revisada.suporte_composto()
    if type(suporte) is not SuporteAutoriaProposto:
        return None

    def resultado(estado: str, proposicoes: list[dict[str, Any]], fontes: list[dict[str, Any]],
                  realizada: str = fala, aplicar: bool = False) -> RevisaoSuporteAutoria:
        return RevisaoSuporteAutoria(SnapshotComandoIA({
            "estado": estado, "turno_id": str(plano.get("id") or ""),
            "proposicoes": proposicoes, "fontes_lidas": fontes,
            "pode_confirmar_fato_externo": False,
        }), realizada, aplicar)

    if (suporte.turno_id != str(plano.get("id") or "")
        or suporte.texto_usuario != plano.get("texto_usuario")):
        return resultado("autoria_de_outra_ocorrencia", [], [], _LIMITE,
                         fala == suporte.fala_original)
    declaracao = suporte.declaracao.como_dict()
    if declaracao.get("estado") != "revisao_semantica_pendente" or declaracao.get("cobertura_textual") is not True:
        return resultado("declaracao_sem_cobertura", [], [])

    fundamentacao = plano.get("fundamentacao_factual")
    base = avaliar_validade_fundamentacao(fundamentacao if isinstance(fundamentacao, dict) else {}, agora=agora)
    fontes_brutas = base.get("fontes")
    fontes = [dict(f) for f in fontes_brutas[:5] if isinstance(f, dict)] if isinstance(fontes_brutas, list) else []
    proveniencia = classificar_proveniencia_informacao(base, contexto="fundamentacao_factual")
    admissivel = (base.get("confiavel") is True and base.get("evidencia_dentro_validade") is not False
                  and proveniencia.get("pode_sustentar_fato_externo") is True)
    snapshots: list[dict[str, Any]] = []

    def conferir_fonte(identidade: str, texto: str) -> dict[str, Any]:
        r = {"id": identidade}
        if referencia_alegacao_da_fonte(identidade):
            return {**r, "estado": "referencia_interna_sem_prova_externa"}
        candidatas = [f for f in fontes if f.get("url") == identidade]
        if not candidatas:
            return {**r, "estado": "fonte_sem_conteudo_individual" if identidade == base.get("fonte") else "fonte_nao_resolvida"}
        if len(candidatas) != 1:
            return {**r, "estado": "fonte_ambigua"}
        if base.get("evidencia_dentro_validade") is False:
            return {**r, "estado": "fonte_fora_validade"}
        if not admissivel:
            return {**r, "estado": "fonte_nao_admissivel"}
        fonte = candidatas[0]
        trecho = fonte.get("trecho")
        try:
            url = urlsplit(identidade)
            url_valida = url.scheme in {"http", "https"} and bool(url.netloc)
        except ValueError:
            url_valida = False
        if not url_valida or type(trecho) is not str or not trecho.strip() or len(trecho) > 850:
            return {**r, "estado": "fonte_sem_conteudo_conferivel"}
        snapshot_id = hashlib.sha256((identidade + "\0" + trecho).encode("utf-8")).hexdigest()
        if not any(f["snapshot_id"] == snapshot_id for f in snapshots):
            snapshots.append({"id": identidade, "trecho": trecho, "snapshot_id": snapshot_id})
        if texto == trecho:
            return {**r, "estado": "literal_integral_na_fonte", "snapshot_id": snapshot_id}
        derivacao = _derivar_parafrase_estrutural(trecho, texto)
        if derivacao is not None:
            return {**r, "estado": "parafrase_estrutural_conferida", "snapshot_id": snapshot_id,
                    "derivacao": derivacao}
        estado = "trecho_parcial_sem_implicacao" if texto in trecho else "apoio_semantico_pendente"
        return {**r, "estado": estado, "snapshot_id": snapshot_id}

    proposicoes: list[dict[str, Any]] = []
    literais: list[str] = []
    parafrases: list[str] = []
    atos_sociais: list[str] = []
    tem_referencia = False
    propostas = declaracao.get("proposicoes") or []
    declara_alvos = any("ato_proposto" in p for p in propostas)
    alvos = {a["id"]: a for a in inventariar_atos_autoria(plano)} if declara_alvos else {}
    for proposta in propostas:
        texto = proposta["texto"]
        referencias = proposta["fontes"]
        tem_referencia = tem_referencia or bool(referencias)
        revisoes = [conferir_fonte(f, texto) for f in referencias]
        estado = ("sem_fontes_declaradas" if not revisoes else
                  next((f["estado"] for f in revisoes if f["estado"] not in _APOIOS_CONFERIDOS),
                       "parafrase_estrutural_conferida" if any(
                           f["estado"] == "parafrase_estrutural_conferida" for f in revisoes)
                       else "literal_integral_na_fonte"))
        proposicoes.append({"texto": texto, "fontes": revisoes, "estado": estado,
                            "pode_confirmar_fato_externo": False})
        ato_social = conferir_ato_social(texto, plano=plano) if not referencias else None
        if declara_alvos:
            alvo = alvos.get(proposta.get("ato_proposto"))
            compativel = bool(alvo is not None and (
                (alvo["tipo"] == "saudacao" and ato_social is not None
                 and ato_social["tipo_ato"] == alvo["tipo"]
                 and ato_social["fonte"]["intervalo"] == alvo["intervalo"])
                or (alvo["tipo"] == "pergunta" and ato_social is None)))
            proposicoes[-1]["vinculo_ato"] = {
                "id_proposto": proposta.get("ato_proposto"),
                "fonte_atual_identificada": alvo is not None,
                "fonte": alvo, "realizacao_social_conferida": compativel and ato_social is not None,
                "pertinencia_semantica_verificada": False, "autoriza_execucao": False,
            }
            if not compativel:
                estado = "alvo_discursivo_nao_conferido"
                proposicoes[-1]["estado"] = estado
                ato_social = None
        if ato_social is not None:
            proposicoes[-1].update(estado="ato_social_conferido", conferencia_ato_social=ato_social)
            atos_sociais.append(texto)
        if estado == "literal_integral_na_fonte":
            literais.append(texto)
        elif estado == "parafrase_estrutural_conferida":
            parafrases.append(texto)

    requer_revisao = bool(tem_referencia or fontes or base.get("requer_evidencia_recente"))
    realizada = _LIMITE
    if literais or parafrases or atos_sociais:
        if parafrases or atos_sociais:
            # Citação e paráfrase têm atribuições distintas; agrupá-las por
            # classe trocaria a ordem das unidades originais da autora.
            realizada = " ".join(
                p["texto"] if p["estado"] == "ato_social_conferido" else
                "Parafraseando os trechos consultados: " + p["texto"]
                if p["estado"] == "parafrase_estrutural_conferida"
                else "Os trechos consultados registram: «" + p["texto"] + "»."
                for p in proposicoes if p["estado"] in _APOIOS_CONFERIDOS or p["estado"] == "ato_social_conferido")
        else:
            realizada = "Os trechos consultados registram: " + "; ".join("«" + t + "»" for t in literais)
        if len(literais) + len(parafrases) + len(atos_sociais) < len(proposicoes):
            separador = " " if realizada.endswith(".") else ". "
            realizada += separador + "Há outras afirmações cujo apoio não consegui verificar."
        if len(realizada) > 4000:
            realizada = _LIMITE
    # Só a própria emissão ou a realização limitada deste mesmo contrato pode
    # receber este julgamento. Não tomar o suporte para fala de outro owner.
    if fala not in {suporte.fala_original, realizada}:
        # Ausência de vínculo não cancela a obrigação de fonte da conversa.
        # Não julgar o texto novo com a prova do antigo, nem substituir aqui
        # a conclusão operacional cujo owner valida os receipts.
        limitar = bool(requer_revisao and not plano.get("requer_execucao") and not plano.get("comandos"))
        return resultado("fala_nao_vinculada", proposicoes, snapshots,
                         _LIMITE if limitar else fala, limitar)
    return resultado("revisao_limitada" if requer_revisao else "sem_obrigacao_de_fonte_individual",
                     proposicoes, snapshots, realizada if requer_revisao else fala, requer_revisao)
