"""Segunda leitura experimental da fronteira, sem entrada do parser POS.

Somente sonda offline. A resposta do modelo é proposta, não prova semântica,
aprovação de ensino, fala ou autorização de efeito.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, Mapping

from scripts.analises.sonda_produtor_candidatos_v1 import gerar_candidatos


RELACOES = frozenset({
    "objeto_anterior", "sujeito_seguinte", "indeterminado",
})
FORMATO = {
    "type": "object", "additionalProperties": False,
    "required": ["relacao", "citacao"],
    "properties": {
        "relacao": {"type": "string", "enum": sorted(RELACOES)},
        "citacao": {"type": "string"},
    },
}
FORMATO_PARES = {
    "type": "object", "additionalProperties": False,
    "required": ["relacao"],
    "properties": {"relacao": {"type": "string", "enum": sorted(RELACOES)}},
}
SISTEMA = (
    "Leia a frase inteira. Há três fragmentos literais separados por 'e'. "
    "Decida apenas a função do fragmento do meio: ele completa o objeto "
    "da oração anterior, inicia um sujeito composto da oração seguinte, "
    "ou é indeterminado? Responda 'objeto_anterior', "
    "'sujeito_seguinte' ou 'indeterminado'. Para uma decisão, copie em "
    "'citacao' um trecho contínuo da frase que inclua o fragmento do meio "
    "e o lado escolhido. Para indeterminado, use citação vazia. Não invente "
    "trechos, não converse e não execute ações."
)
SISTEMA_AMBIGUIDADE_EXPLICITA = (
    "Leia a frase inteira e compare as duas partições dos três fragmentos "
    "separados por 'e': (anterior + meio) | seguinte e anterior | "
    "(meio + seguinte). Se as duas leituras conservarem concordância "
    "gramatical e sentido plausível, responda 'indeterminado', mesmo que "
    "uma pareça mais natural; use citação vazia. Só escolha "
    "'objeto_anterior' ou 'sujeito_seguinte' quando a outra partição for "
    "inviável. Nesse caso, copie em 'citacao' um trecho contínuo literal "
    "que inclua o fragmento do meio e o lado escolhido. Não invente "
    "trechos, não converse e não execute ações."
)
SISTEMA_PARES = (
    "Compare duas leituras literais da mesma frase. A pergunta é onde o "
    "fragmento do meio pertence: ele completa o objeto da primeira ação "
    "ou é parte do sujeito da segunda ação? Use o verbo, concordância e "
    "significado das duas leituras; não escolha só pela proximidade nem "
    "pela ordem das opções. Se ambas forem plausíveis, use indeterminado. "
    "Responda somente com a chave relacao, usando objeto_anterior, "
    "sujeito_seguinte ou indeterminado. Não converse nem execute ações."
)
DADOS = Path(__file__).resolve().parent / "dados"


def _base(estado: str) -> dict[str, object]:
    return {"estado": estado, "aprovado_para_producao": False,
            "autoriza_efeito": False}


def preparar_entrada(caso: Mapping[str, object]) -> dict[str, object]:
    gerados = gerar_candidatos(caso)
    trechos = gerados["candidatos"]
    if (gerados["estado"] != "candidatos_gerados_revisao_pendente"
            or gerados["estrutura_plana_possivel"] is not True
            or gerados["conectivo_textual"] != "e"
            or len(trechos) != 3):
        return _base("abstencao_estrutura_lexical")
    return {**_base("entrada_literal_preparada"), "entrada": {
        "fonte": caso["fonte"],
        "fragmentos": [
            {chave: trecho[chave] for chave in ("id", "citacao", "inicio", "fim")}
            for trecho in trechos
        ],
    }}


def validar_julgamento(
    caso: Mapping[str, object], bruto: object,
) -> dict[str, object]:
    preparada = preparar_entrada(caso)
    if preparada["estado"] != "entrada_literal_preparada":
        return _base("abstencao_estrutura_lexical")
    if (not isinstance(bruto, Mapping) or set(bruto) != {"relacao", "citacao"}
            or not isinstance(bruto["relacao"], str)
            or bruto["relacao"] not in RELACOES
            or not isinstance(bruto["citacao"], str)):
        return _base("entrada_invalida")
    relacao = bruto["relacao"]
    citacao = bruto["citacao"]
    if relacao == "indeterminado":
        return ({**_base("abstencao_modelo"), "relacao": relacao}
                if not citacao else _base("entrada_invalida"))
    if not 3 <= len(citacao) <= 160:
        return _base("entrada_invalida")
    fonte = preparada["entrada"]["fonte"]
    if fonte.count(citacao) != 1:
        return _base("citacao_nao_literal_unica")
    inicio = fonte.index(citacao)
    fim = inicio + len(citacao)
    anterior, meio, seguinte = preparada["entrada"]["fragmentos"]
    if relacao == "objeto_anterior":
        lado_valido = (anterior["inicio"] <= inicio < anterior["fim"]
                       and fim == meio["fim"])
    else:
        lado_valido = (inicio == meio["inicio"]
                       and seguinte["inicio"] < fim <= seguinte["fim"])
    if not lado_valido:
        return _base("citacao_fora_do_lado_declarado")
    return {**_base("julgamento_ancorado_revisao_pendente"),
            "relacao": relacao, "citacao": citacao,
            "inicio_citacao": inicio, "fim_citacao": fim}


def propor(
    caso: Mapping[str, object],
    consultar: Callable[..., object],
    *,
    sistema: str = SISTEMA,
) -> dict[str, object]:
    preparada = preparar_entrada(caso)
    if preparada["estado"] != "entrada_literal_preparada":
        return preparada
    bruto = consultar(sistema, preparada["entrada"], FORMATO)
    return {**validar_julgamento(caso, bruto), "resposta_bruta": bruto}


def preparar_pares(caso: Mapping[str, object]) -> dict[str, object]:
    preparada = preparar_entrada(caso)
    if preparada["estado"] != "entrada_literal_preparada":
        return _base("abstencao_estrutura_lexical")
    fonte = preparada["entrada"]["fonte"]
    anterior, meio, seguinte = preparada["entrada"]["fragmentos"]
    objeto = {
        "relacao": "objeto_anterior",
        "trechos_condicoes": [
            fonte[anterior["inicio"]:meio["fim"]], seguinte["citacao"],
        ],
    }
    sujeito = {
        "relacao": "sujeito_seguinte",
        "trechos_condicoes": [
            anterior["citacao"], fonte[meio["inicio"]:seguinte["fim"]],
        ],
    }
    return {**_base("pares_literais_preparados"), "entrada": {
        "fonte": fonte, "fragmento_medio": meio["citacao"],
        "leituras": [objeto, sujeito],
    }}


def propor_pares(
    caso: Mapping[str, object],
    consultar: Callable[..., object],
) -> dict[str, object]:
    preparada = preparar_pares(caso)
    if preparada["estado"] != "pares_literais_preparados":
        return preparada
    entrada = preparada["entrada"]
    respostas = [
        consultar(SISTEMA_PARES, {**entrada, "leituras": leituras},
                  FORMATO_PARES)
        for leituras in (entrada["leituras"],
                        list(reversed(entrada["leituras"])))
    ]
    observadas = []
    for resposta in respostas:
        if (not isinstance(resposta, Mapping)
                or set(resposta) != {"relacao"}
                or not isinstance(resposta["relacao"], str)
                or resposta["relacao"] not in RELACOES):
            return {**_base("rotulo_invalido"), "respostas_brutas": respostas}
        observadas.append(resposta["relacao"])
    if observadas[0] != observadas[1]:
        return {**_base("abstencao_por_ordem"), "respostas_brutas": respostas}
    if observadas[0] == "indeterminado":
        return {**_base("abstencao_modelo"), "respostas_brutas": respostas}
    return {**_base("rotulo_concordante_revisao_pendente"),
            "relacao": observadas[0], "respostas_brutas": respostas}


def aferir_pares(
    gabarito: Mapping[str, object], resultado: Mapping[str, object],
) -> dict[str, object]:
    esperado = gabarito.get("relacao")
    if not isinstance(esperado, str) or esperado not in RELACOES:
        return _base("referencia_invalida")
    if resultado.get("estado") == "abstencao_modelo":
        return _base("abstencao_compativel_revisao_local"
                     if esperado == "indeterminado"
                     else "abstencao_em_caso_definido")
    if resultado.get("estado") != "rotulo_concordante_revisao_pendente":
        return _base("proposta_nao_aferida")
    return _base("alinhado_revisao_local"
                 if resultado.get("relacao") == esperado
                 else "divergente_revisao_local")


def aferir(
    gabarito: Mapping[str, object], resultado: Mapping[str, object],
) -> dict[str, object]:
    esperado = gabarito.get("relacao")
    if not isinstance(esperado, str) or esperado not in RELACOES:
        return _base("referencia_invalida")
    if resultado.get("estado") not in {
        "julgamento_ancorado_revisao_pendente", "abstencao_modelo",
    }:
        return _base("proposta_nao_aferida")
    observado = resultado.get("relacao")
    if observado == "indeterminado":
        return _base("abstencao_modelo")
    return _base("alinhado_revisao_local" if observado == esperado
                 else "divergente_revisao_local")


def aferir_rotulo_bruto(
    gabarito: Mapping[str, object], resultado: Mapping[str, object],
) -> dict[str, object]:
    """Mede só o rótulo emitido, inclusive quando a citação foi rejeitada."""
    esperado = gabarito.get("relacao")
    if not isinstance(esperado, str) or esperado not in RELACOES:
        return _base("referencia_invalida")
    bruto = resultado.get("resposta_bruta")
    if (not isinstance(bruto, Mapping)
            or set(bruto) != {"relacao", "citacao"}
            or not isinstance(bruto["relacao"], str)
            or bruto["relacao"] not in RELACOES
            or not isinstance(bruto["citacao"], str)):
        return _base("rotulo_bruto_invalido")
    return _base("rotulo_bruto_alinhado_revisao_local"
                 if bruto["relacao"] == esperado
                 else "rotulo_bruto_divergente_revisao_local")


def carregar_painel_fronteira(
    versao: int,
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    if versao not in (22, 23, 24, 25, 26, 27, 28):
        raise ValueError("versao de painel de fronteira desconhecida")
    entradas = json.loads((DADOS / f"sonda_fronteira_entradas_v{versao}.json")
                          .read_text(encoding="utf-8"))
    revisao = json.loads((DADOS / f"sonda_fronteira_revisao_v{versao}.json")
                         .read_text(encoding="utf-8"))
    casos = entradas.get("casos")
    ouro = revisao.get("casos")
    if (entradas.get("versao") != versao or revisao.get("versao") != versao
            or not isinstance(casos, list) or not isinstance(ouro, dict)
            or any(not isinstance(caso, dict)
                   or not isinstance(caso.get("id"), str)
                   for caso in casos)):
        raise ValueError(f"painel v{versao} invalido")
    ids = [caso["id"] for caso in casos]
    if (not ids or len(ids) != len(set(ids)) or set(ids) != set(ouro)
            or any(not isinstance(ouro[item], dict)
                   or ouro[item].get("relacao") not in RELACOES
                   for item in ids)):
        raise ValueError(f"gabarito v{versao} nao corresponde as entradas")
    return casos, ouro


def carregar_painel_v22(
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    return carregar_painel_fronteira(22)


def main() -> None:
    import requests

    from scripts.analises.sonda_produtor_condicoes_v2 import _consultar_modelo

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", default="qwen3:4b-instruct")
    parser.add_argument("--url", default="http://127.0.0.1:11434/api/chat")
    parser.add_argument("--contrato", choices=("citacao", "pares"),
                        default="citacao")
    args = parser.parse_args()
    casos, gabarito = carregar_painel_v22()

    def consultar(sistema, entrada, formato):
        return _consultar_modelo(sistema, entrada, formato,
                                 url=args.url, modelo=args.modelo)

    for caso in casos:
        try:
            resultado = (propor_pares(caso, consultar)
                         if args.contrato == "pares"
                         else propor(caso, consultar))
        except (requests.RequestException, KeyError, TypeError,
                ValueError, OSError) as erro:
            resultado = {**_base("erro_consulta"),
                         "tipo_erro": type(erro).__name__}
        afericao = (aferir_pares(gabarito[caso["id"]], resultado)
                    if args.contrato == "pares"
                    else aferir(gabarito[caso["id"]], resultado))
        rotulo_bruto = (None if args.contrato == "pares" else
                        aferir_rotulo_bruto(gabarito[caso["id"]], resultado))
        print(json.dumps({"id": caso["id"], "proposta": resultado,
                          "contrato": args.contrato,
                          "afericao": afericao,
                          "afericao_rotulo_bruto": rotulo_bruto,
                          "aprovado_para_producao": False,
                          "autoriza_efeito": False},
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
