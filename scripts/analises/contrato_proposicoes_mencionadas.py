"""Representação offline de proposições e molduras; não interpreta nem executa.

O host preserva fontes e regiões entre aspas. O proponente fornece trechos,
papéis, polaridade e vínculos de moldura, sempre pendentes de revisão semântica.
Ocorrência literal e contenção NÃO comprovam esses papéis ou vínculos.
Não há ligação com o runtime, registro de vigência ou treino.
"""

from __future__ import annotations

from dataclasses import asdict

from mente_laylay.arquivos.nome_natural import mapear_pares_aspas_globais
from scripts.analises.grafo_premissas_didaticas import FonteDidatica
from scripts.analises.sonda_produtor_condicoes_v2 import _ancorar_trecho


TIPOS_MOLDURA = ("pedido", "pergunta", "hipotese", "relato", "metalinguagem", "indeterminada")
TIPOS_PROPOSICAO = ("acao", "estado", "indeterminada")
PAPEIS_OBJETO = ("entidade", "texto", "outro", "indeterminado")
POLARIDADES = ("positiva", "negativa", "indeterminada")
LIMITES = {"molduras": 32, "proposicoes": 16}
BASE = {
    "semantica_verificada": False, "cobertura_semantica_verificada": False,
    "referente_resolvido": False, "autoriza_efeito": False,
    "pode_registrar_vigencia": False, "aprovado_para_producao": False,
}


def _texto(valor: object) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


def _span(texto: str, trecho: object, *, deslocamento: int = 0) -> dict | None:
    if not _texto(trecho):
        return None
    literal = _ancorar_trecho(texto, trecho)
    if literal is None:
        return None
    inicio = texto.index(literal) + deslocamento
    return {"inicio": inicio, "fim": inicio + len(literal), "texto": literal}


def _contem(externo: dict, interno: dict) -> bool:
    return externo["inicio"] <= interno["inicio"] < interno["fim"] <= externo["fim"]


def _aspas(fonte: FonteDidatica) -> dict:
    """Reusa o mapeador canônico sem achatar pares aninhados.

    Uma região entre aspas também pode ser um filename ou título: não é,
    por si só, uma moldura semântica de citação de ordem.
    """
    pares = mapear_pares_aspas_globais(fonte.texto)
    regioes = []
    for inicio, fechamento in sorted((pares or {}).items()):
        fim = fechamento + 1
        envolventes = [r for r in regioes if r["inicio"] < inicio < fim < r["fim"]]
        pai = max(envolventes, key=lambda r: r["inicio"]) if envolventes else None
        regioes.append({"id": f"q{len(regioes)}", "inicio": inicio, "fim": fim,
                        "texto": fonte.texto[inicio:fim], "pai_id": pai["id"] if pai else ""})
    return {"fonte_id": fonte.identificador, "aspas_coerentes": pares is not None,
            "regioes_entre_aspas": regioes}


def conferir_proposicoes_mencionadas(
    fontes: tuple[FonteDidatica, ...], proposta: object, *, escopo: str,
) -> dict[str, object]:
    """Confere estrutura/proveniência, não a interpretação dos trechos.

    O proponente não fornece offsets nem flags de autoridade. O host ancora
    molduras e proposições na fonte; predicado/objeto na proposição respectiva.
    Pais de moldura devem existir, conter seus filhos, pertencer à mesma fonte
    e não formar ciclo. Molduras coextensivas são permitidas; não são fundidas.
    Lista vazia, objeto desconhecido e fonte com aspas incoerentes conservam
    a incerteza. Nada disso certifica ausência de evento ou discurso direto.
    """
    base = {**BASE, "estado": "estrutura_invalida", "fontes": [],
            "aspas_por_fonte": [], "molduras": [], "proposicoes": []}

    def falha(estado: str) -> dict:
        # Nunca publicar uma parte conferida como um grafo completo.
        return {**base, "estado": estado}

    if (not _texto(escopo) or not isinstance(fontes, tuple) or not fontes
            or any(not isinstance(f, FonteDidatica) for f in fontes)):
        return falha("fontes_invalidas")
    if (any(not _texto(f.identificador) or not _texto(f.texto) for f in fontes)
            or len({f.identificador for f in fontes}) != len(fontes)):
        return falha("identidade_de_fonte_invalida")
    if any(f.escopo != escopo for f in fontes):
        return falha("escopo_divergente")
    if any(not isinstance(f.origem, str) or f.origem not in {"usuario", "pesquisa_verificada"}
           for f in fontes):
        return falha("origem_de_fonte_invalida")
    por_fonte = {f.identificador: f for f in fontes}
    aspas = {f.identificador: _aspas(f) for f in fontes}
    base = {**base, "fontes": [asdict(f) for f in fontes],
            "aspas_por_fonte": list(aspas.values())}
    if (not isinstance(proposta, dict) or set(proposta) != {"molduras", "proposicoes"}
            or any(not isinstance(proposta[k], list) or len(proposta[k]) > limite
                   for k, limite in LIMITES.items())):
        return falha("proposta_invalida")

    campos = {
        "molduras": {"id", "fonte_id", "tipo", "trecho", "pai_id"},
        "proposicoes": {"id", "fonte_id", "tipo", "trecho", "predicado", "objeto",
                        "papel_objeto", "polaridade", "moldura_id"},
    }
    for grupo in campos:
        itens = proposta[grupo]
        if any(not isinstance(i, dict) or set(i) != campos[grupo]
               or any(not isinstance(v, str) for v in i.values()) for i in itens):
            return falha("proposta_invalida")
        if (any(not _texto(i["id"]) for i in itens)
                or len({i["id"] for i in itens}) != len(itens)):
            return falha("identidade_de_proposta_invalida")
        if any(i["fonte_id"] not in por_fonte for i in itens):
            return falha("fonte_desconhecida")

    molduras = {}
    for item in proposta["molduras"]:
        if item["tipo"] not in TIPOS_MOLDURA:
            return falha("tipo_de_moldura_invalido")
        span = _span(por_fonte[item["fonte_id"]].texto, item["trecho"])
        if span is None:
            return falha("moldura_sem_ancora_unica")
        molduras[item["id"]] = {"id": item["id"], "fonte_id": item["fonte_id"],
                               "tipo_proposto": item["tipo"], "pai_id": item["pai_id"], **span}
    for item in molduras.values():
        if item["pai_id"]:
            pai = molduras.get(item["pai_id"])
            if (pai is None or pai["fonte_id"] != item["fonte_id"] or not _contem(pai, item)):
                return falha("parentesco_de_moldura_invalido")
        visitados = {item["id"]}
        cursor = item["pai_id"]
        while cursor:
            if cursor in visitados:
                return falha("ciclo_de_molduras")
            visitados.add(cursor)
            pai = molduras.get(cursor)
            if pai is None:
                return falha("parentesco_de_moldura_invalido")
            cursor = pai["pai_id"]

    proposicoes = []
    for item in proposta["proposicoes"]:
        if (item["tipo"] not in TIPOS_PROPOSICAO or item["papel_objeto"] not in PAPEIS_OBJETO
                or item["polaridade"] not in POLARIDADES):
            return falha("rotulo_de_proposicao_invalido")
        span = _span(por_fonte[item["fonte_id"]].texto, item["trecho"])
        if span is None:
            return falha("proposicao_sem_ancora_unica")
        predicado = _span(span["texto"], item["predicado"], deslocamento=span["inicio"])
        if predicado is None:
            return falha("predicado_fora_da_proposicao_ou_ambiguo")
        objeto = None
        if item["objeto"]:
            objeto = _span(span["texto"], item["objeto"], deslocamento=span["inicio"])
            if objeto is None:
                return falha("objeto_fora_da_proposicao_ou_ambiguo")
        elif item["papel_objeto"] != "indeterminado":
            return falha("objeto_ausente_sem_abstencao")
        moldura = molduras.get(item["moldura_id"])
        if item["moldura_id"] and (moldura is None or moldura["fonte_id"] != item["fonte_id"]
                                    or not _contem(moldura, span)):
            return falha("vinculo_de_proposicao_invalido")
        regioes = aspas[item["fonte_id"]]["regioes_entre_aspas"]
        proposicoes.append({"id": item["id"], "fonte_id": item["fonte_id"], **span,
                            "tipo_proposto": item["tipo"], "predicado": predicado, "objeto": objeto,
                            "papel_objeto_proposto": item["papel_objeto"],
                            "polaridade_proposta": item["polaridade"], "moldura_id": item["moldura_id"],
                            "aspas_do_predicado": [r["id"] for r in regioes if _contem(r, predicado)],
                            "aspas_do_objeto": [r["id"] for r in regioes if objeto and _contem(r, objeto)]})
    return {**base, "estado": "proposicoes_ancoradas_revisao_pendente",
            "molduras": list(molduras.values()), "proposicoes": proposicoes}
