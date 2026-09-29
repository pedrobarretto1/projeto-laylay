"""Sonda offline: Qwen propõe um critério, mas não escolhe suas fontes.

O painel de revisão é usado só depois da resposta do modelo. Nenhum estado
deste módulo aprova fala, pesquisa, treino ou efeito no runtime da Laylay.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Mapping

from mente_laylay.cognicao.contrato_inventario_contextual import ReferenteContextual
from scripts.analises.grafo_premissas_didaticas import (
    CondicaoDidatica, FonteDidatica, PremissaDidatica, ReferenteAncorado,
    RegraDidatica, conferir_qualificacao_na_conversa,
)


DADOS = Path(__file__).parent / "dados"
ENTRADAS = DADOS / "sonda_criterios_entradas_v1.json"
REVISAO = DADOS / "sonda_criterios_revisao_v1.json"
_CAMPOS = {
    "estado", "motivo", "fonte_id", "referente_id", "atributo", "operador",
    "limiar", "unidade", "direcao_implicacao", "citacao_condicao",
}
_DETALHES = _CAMPOS - {"estado", "motivo"}
_MOTIVOS_ABSTENCAO = {
    "criterio_ausente", "referente_indeterminado", "rotulo_nao_declarado",
    "efeito_eh_acao", "regra_composta", "outro_indeterminado",
}
_DIRECOES = {
    "condicoes_suficientes", "condicoes_necessarias", "equivalencia",
}


def carregar_painel() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    entradas = json.loads(ENTRADAS.read_text(encoding="utf-8"))
    revisao = json.loads(REVISAO.read_text(encoding="utf-8"))
    casos = entradas["casos"]
    gabarito = revisao["casos"]
    if (entradas.get("versao") != revisao.get("versao")
            or len({item["id"] for item in casos}) != len(casos)
            or {item["id"] for item in casos} != set(gabarito)):
        raise ValueError("painel e revisao divergentes")
    return casos, gabarito


def preparar_entrada_modelo(caso: Mapping[str, object]) -> dict[str, object]:
    """Não transmite gabarito nem permite ao modelo escrever uma fonte nova."""
    return {campo: caso[campo] for campo in (
        "fontes", "referentes", "medida", "rotulo_alvo",
    )}


def _formato_proposta() -> dict[str, object]:
    return {
        "type": "object", "additionalProperties": False,
        "required": sorted(_CAMPOS),
        "properties": {
            "estado": {"type": "string", "enum": ["abster", "criterio_candidato"]},
            "motivo": {"type": "string", "enum": ["", *sorted(_MOTIVOS_ABSTENCAO)]},
            "operador": {"type": "string", "enum": ["", "<", "<=", ">", ">=", "=", "!="]},
            "direcao_implicacao": {"type": "string", "enum": ["", *sorted(_DIRECOES)]},
            **{campo: {"type": "string"} for campo in
               _DETALHES - {"operador", "direcao_implicacao"}},
        },
    }


def _validar_formato(proposta: object) -> bool:
    if (not isinstance(proposta, Mapping) or set(proposta) != _CAMPOS
            or any(not isinstance(valor, str) or len(valor) > 300
                   for valor in proposta.values())
            or proposta["estado"] not in {"abster", "criterio_candidato"}):
        return False
    if proposta["estado"] == "abster":
        return (proposta["motivo"] in _MOTIVOS_ABSTENCAO
                and all(not proposta[campo] for campo in _DETALHES))
    return (proposta["motivo"] == ""
            and all(proposta[campo].strip()
                    for campo in _DETALHES - {"unidade"})
            and proposta["operador"] in {"<", "<=", ">", ">=", "=", "!="}
            and proposta["direcao_implicacao"] in _DIRECOES)


def _conferir_grafo_do_caso(
    caso: Mapping[str, object], proposta: Mapping[str, str],
    *, registro_vigencia: object = None,
) -> dict[str, object]:
    """Monta grafo com texto integral do painel, nunca texto de fonte proposto."""
    escopo = f"painel_criterios:{caso['id']}"
    fontes_brutas = caso["fontes"]
    por_id = {item["id"]: item["texto"] for item in fontes_brutas}
    fonte_regra = por_id.get(proposta["fonte_id"])
    if fonte_regra is None:
        return {"estado": "fonte_desconhecida", "aprovado_para_compor": False}
    fontes = tuple(
        FonteDidatica(item["id"], "usuario", escopo, item["texto"])
        for item in fontes_brutas
    )
    referentes = tuple(
        ReferenteAncorado(
            ReferenteContextual(item["id"], item["tipo"], item["grandeza"],
                                "usuario", escopo),
            item["fonte_id"], item["citacao"],
        ) for item in caso["referentes"]
    )
    medida = caso["medida"]
    premissa = PremissaDidatica(
        "medida", medida["referente_id"], medida["atributo"],
        medida["valor"], medida["unidade"], medida["fonte_id"],
        medida["citacao"],
    )
    regra = RegraDidatica(
        "criterio", (CondicaoDidatica(
            proposta["referente_id"], proposta["atributo"],
            proposta["operador"], proposta["limiar"], proposta["unidade"],
            proposta["fonte_id"], proposta["citacao_condicao"],
        ),), proposta["referente_id"], "estado", caso["rotulo_alvo"],
        proposta["fonte_id"], fonte_regra, "unico",
        proposta["direcao_implicacao"],
    )
    conferir = conferir_qualificacao_na_conversa
    opcoes = {}
    if registro_vigencia is not None:
        # Registro explícito; esta função não registra revisão nem inventa
        # seu owner. Sem registro, a conferência automática exige cobertura
        # literal do contexto posterior, sem afirmar vigência semântica.
        from scripts.analises.contrato_vigencia_criterios import (
            conferir_qualificacao_com_vigencia,
        )
        conferir = conferir_qualificacao_com_vigencia
        opcoes["registro"] = registro_vigencia
    return conferir(
        fontes, referentes, (premissa,), (regra,), escopo=escopo,
        premissa_id="medida", regra_id="criterio", rotulo=caso["rotulo_alvo"],
        texto_atual=fontes_brutas[-1]["texto"],
        mensagens=[{"role": "user", "content": item["texto"]}
                   for item in fontes_brutas[:-1]],
        **opcoes,
    )


def conferir_proposta(
    caso: Mapping[str, object], revisao: Mapping[str, object], proposta: object,
) -> dict[str, object]:
    """Aferição local; nem gabarito alinhado equivale a fala aprovada."""
    base = {"estado": "entrada_invalida", "alinhado_revisao": False,
            "aprovado_para_producao": False, "autoriza_efeito": False}
    if not isinstance(revisao, Mapping) or revisao.get("estado") not in {
        "abster", "criterio_candidato",
    } or not _validar_formato(proposta):
        return base
    if proposta["estado"] == "abster":
        alinhado = (revisao["estado"] == "abster"
                    and proposta["motivo"] == revisao.get("motivo"))
        return {**base, "estado": (
            "abstencao_compativel" if alinhado else
            "abstencao_em_criterio_disponivel" if revisao["estado"] != "abster"
            else "abstencao_motivo_divergente"
        ), "alinhado_revisao": alinhado}
    try:
        if not caso["medida"]["referente_id"]:
            return {**base, "estado": "referente_indeterminado"}
        grafo = _conferir_grafo_do_caso(caso, proposta)
    except (KeyError, TypeError, ValueError, AttributeError):
        return base
    if (revisao["estado"] == "criterio_candidato"
            and grafo["estado"] not in {
                "condicao_numerica_satisfeita_relacao_pendente",
                "condicao_numerica_nao_satisfeita",
                "direcao_implicacao_pendente",
            }):
        return {**base, "estado": "grafo_rejeitou_proposta",
                "grafo_estado": grafo["estado"]}
    campos_revisados = _DETALHES
    alinhado = (revisao["estado"] == "criterio_candidato"
                and all(proposta[campo] == revisao.get(campo)
                        for campo in campos_revisados))
    estado = (
        "forcou_criterio_ausente" if revisao["estado"] == "abster" else
        "proposta_divergente" if not alinhado else
        "proposta_alinhada_revisao_pendente"
    )
    return {**base, "estado": estado, "alinhado_revisao": alinhado,
            "grafo_estado": grafo["estado"],
            "grafo_comparacao_numerica": bool(grafo.get("comparacao_numerica"))}


def medir_caso(
    caso: Mapping[str, object], revisao: Mapping[str, object],
    *, url: str = "http://127.0.0.1:11434/api/chat",
    modelo: str = "qwen3:4b-instruct",
) -> dict[str, object]:
    """Uma proposta local por caso; a revisão não entra no prompt."""
    import requests

    sistema = (
        "Você propõe uma regra tipada para o rótulo_alvo, não responde ao usuário. "
        "Use apenas fontes fornecidas. Se só houver medida, limiar numérico, "
        "regra que aciona dispositivo ou rótulo diferente, abstenha-se. "
        "Se o referente da medida estiver vazio/indeterminado, abstenha-se, "
        "mesmo que haja regra sobre um dos possíveis referentes. "
        "Uma regra 'apenas se' é necessária, não suficiente; pode ser "
        "selecionada como candidata, mas nunca autoriza concluir o rótulo. "
        "Quando houver regra explícita para o rótulo, escolha fonte_id "
        "existente e copie citacao_condicao literalmente da fonte, com o "
        "limiar e unidade. Para abster, preencha motivo e deixe todos os "
        "demais campos vazios. Para candidato, deixe motivo vazio. Não crie "
        "fontes, não converse e não execute ações."
    )
    inicio = time.monotonic()
    try:
        resposta = requests.post(
            url,
            json={"model": modelo, "stream": False, "format": _formato_proposta(),
                  "options": {"temperature": 0, "num_predict": 450},
                  "messages": [
                      {"role": "system", "content": sistema},
                      {"role": "user", "content": json.dumps(
                          preparar_entrada_modelo(caso), ensure_ascii=False,
                      )},
                  ]},
            timeout=90,
        )
        resposta.raise_for_status()
        proposta = json.loads(resposta.json()["message"]["content"])
        afericao = conferir_proposta(caso, revisao, proposta)
        return {"id": caso["id"], "duracao_s": round(time.monotonic()-inicio, 2),
                "proposta": proposta, "afericao": afericao}
    except (requests.RequestException, KeyError, TypeError, ValueError) as erro:
        return {"id": caso.get("id"), "duracao_s": round(time.monotonic()-inicio, 2),
                "erro": type(erro).__name__, "aprovado_para_producao": False}


def main() -> None:
    casos, revisao = carregar_painel()
    for caso in casos:
        print(json.dumps(medir_caso(caso, revisao[caso["id"]]),
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
