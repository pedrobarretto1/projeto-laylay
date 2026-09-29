"""Piloto offline: fonte/abstencao primeiro, normalizacao somente depois.

As guardas usam o texto integral do painel, sem usar o gabarito para decidir
chamadas do modelo. Toda proposta continua pendente de revisao semantica.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Callable, Mapping

from scripts.analises.sonda_produtor_criterios_v1 import (
    conferir_proposta, preparar_entrada_modelo,
)
from scripts.analises.sonda_produtor_candidatos_v1 import gerar_candidatos
from scripts.analises.sinal_relacao_condicional import (
    analisar_efeito_qualificativo, analisar_marcador_condicional,
)


DADOS = Path(__file__).parent / "dados"
ENTRADAS = DADOS / "sonda_criterios_entradas_v2.json"
REVISAO = DADOS / "sonda_criterios_revisao_v2.json"
_MOTIVOS = {
    "criterio_ausente", "referente_indeterminado", "rotulo_nao_declarado",
    "efeito_eh_acao", "regra_composta", "outro_indeterminado",
}
_CAMPOS_NORMALIZACAO = {
    "referente_id", "atributo", "operador", "limiar", "unidade",
    "direcao_implicacao", "citacao_condicao",
}
_CAMPOS_SLOTS = _CAMPOS_NORMALIZACAO - {"direcao_implicacao", "citacao_condicao"}


def preparar_normalizacao_segmentada(fonte: str, rotulo: str) -> dict[str, object]:
    """Reusa sinais literais, sem revisão e sem inferir slots ou autoridade."""
    base = {"estado": "segmentacao_pendente", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    candidatos = gerar_candidatos({"fonte": fonte})
    sinal = analisar_marcador_condicional(fonte)
    efeito = analisar_efeito_qualificativo(fonte, rotulo)
    if (candidatos["estado"] != "candidatos_gerados_revisao_pendente"
            or candidatos["conectivo_textual"] != "unico"
            or len(candidatos["candidatos"]) != 1
            or sinal["estado"] != "marcador_explicito"
            or efeito["estado"] != "efeito_qualificativo_literal_revisao_pendente"):
        return base
    condicao = candidatos["candidatos"][0]
    if not (condicao["fim"] <= efeito["inicio"]
            or efeito["fim"] <= condicao["inicio"]):
        return base
    return {**base, "estado": "segmentos_literais_revisao_pendente",
            "condicao": condicao, "efeito": efeito, "direcao": sinal}


def _rotulo_literal_no_texto(rotulo: str, texto: str) -> bool:
    return bool(re.search(
        rf"(?<!\w){re.escape(rotulo)}(?!\w)", texto, flags=re.IGNORECASE,
    ))


def _fontes_com_rotulo_literal(caso: Mapping[str, object]) -> list[str]:
    """Filtro necessario, nunca certificado de criterio ou de implicacao."""
    try:
        rotulo = caso["rotulo_alvo"]
        fontes = caso["fontes"]
        if (not isinstance(rotulo, str) or not rotulo.strip()
                or not isinstance(fontes, list)):
            return []
        return sorted({item["id"] for item in fontes
                       if isinstance(item, Mapping)
                       and isinstance(item.get("id"), str)
                       and isinstance(item.get("texto"), str)
                       and _rotulo_literal_no_texto(rotulo, item["texto"])})
    except (KeyError, TypeError):
        return []


def _fontes_com_condicao_unica(caso: Mapping[str, object]) -> list[str]:
    """Veto estrutural conservador; nao certifica efeito nem semantica."""
    ids_literais = set(_fontes_com_rotulo_literal(caso))
    fontes = caso.get("fontes")
    if not isinstance(fontes, list):
        return []
    candidatos = []
    for fonte in fontes:
        if (not isinstance(fonte, Mapping)
                or fonte.get("id") not in ids_literais
                or not isinstance(fonte.get("texto"), str)):
            continue
        segmentos = gerar_candidatos({"fonte": fonte["texto"]})
        if (segmentos["estado"] == "candidatos_gerados_revisao_pendente"
                and segmentos["conectivo_textual"] == "unico"
                and len(segmentos["candidatos"]) == 1):
            candidatos.append(fonte["id"])
    return sorted(set(candidatos))


def carregar_painel() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    entradas = json.loads(ENTRADAS.read_text(encoding="utf-8"))
    revisao = json.loads(REVISAO.read_text(encoding="utf-8"))
    casos, gabarito = entradas["casos"], revisao["casos"]
    ids = [caso["id"] for caso in casos]
    if (entradas.get("versao") != 2 or revisao.get("versao") != 2
            or len(ids) != len(set(ids)) or set(ids) != set(gabarito)):
        raise ValueError("painel v2 divergente da revisao")
    return casos, gabarito


def conferir_selecao(
    caso: Mapping[str, object], proposta: object,
    *, exigir_condicao_unica: bool = False,
) -> dict[str, object]:
    """Pista literal e identidade da medida; nao prova que a regra e correta."""
    base = {"estado": "entrada_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    if (not isinstance(proposta, Mapping)
            or set(proposta) != {"estado", "motivo", "fonte_id"}
            or any(not isinstance(valor, str) or len(valor) > 120
                   for valor in proposta.values())):
        return base
    if proposta["estado"] == "abster":
        if proposta["motivo"] not in _MOTIVOS or proposta["fonte_id"]:
            return base
        return {**base, "estado": "abstencao_estrutural"}
    if (proposta["estado"] != "fonte_candidata" or proposta["motivo"]
            or not proposta["fonte_id"]):
        return base
    try:
        if not isinstance(caso["medida"]["referente_id"], str):
            return base
        if not caso["medida"]["referente_id"]:
            return {**base, "estado": "referente_indeterminado"}
        fontes = caso["fontes"]
        if (not isinstance(fontes, list)
                or any(not isinstance(item, Mapping)
                       or not isinstance(item.get("id"), str)
                       or not isinstance(item.get("texto"), str)
                       for item in fontes)):
            return base
        correspondentes = [item["texto"] for item in fontes
                          if item["id"] == proposta["fonte_id"]]
        if len(correspondentes) != 1:
            return {**base, "estado": "fonte_desconhecida_ou_duplicada"}
        rotulo = caso["rotulo_alvo"]
        if not isinstance(rotulo, str) or not rotulo.strip():
            return base
        if not _rotulo_literal_no_texto(rotulo, correspondentes[0]):
            return {**base, "estado": "rotulo_sem_ancora_literal"}
    except (KeyError, TypeError, AttributeError):
        return base
    if (exigir_condicao_unica
            and proposta["fonte_id"] not in _fontes_com_condicao_unica(caso)):
        return {**base, "estado": "estrutura_condicional_inconclusiva"}
    return {**base, "estado": "fonte_literal_candidata_revisao_pendente",
            "fonte_id": proposta["fonte_id"]}


def confrontar_selecao(
    caso: Mapping[str, object], revisao: Mapping[str, object], proposta: object,
    *, exigir_condicao_unica: bool = False,
) -> dict[str, object]:
    """Confronto diagnostico separado da guarda que decide a segunda chamada."""
    estrutura = conferir_selecao(
        caso, proposta, exigir_condicao_unica=exigir_condicao_unica,
    )
    base = {**estrutura, "alinhado_revisao": False}
    if not isinstance(revisao, Mapping) or revisao.get("estado") not in {
        "abster", "criterio_candidato",
    }:
        return {**base, "estado_revisao": "revisao_invalida"}
    if estrutura["estado"] == "abstencao_estrutural":
        alinhado = (revisao["estado"] == "abster"
                    and proposta["motivo"] == revisao.get("motivo"))
        return {**base, "estado_revisao": (
            "abstencao_alinhada" if alinhado else "abstencao_divergente"
        ), "alinhado_revisao": alinhado}
    if estrutura["estado"] == "fonte_literal_candidata_revisao_pendente":
        alinhado = (revisao["estado"] == "criterio_candidato"
                    and proposta["fonte_id"] == revisao.get("fonte_id"))
        return {**base, "estado_revisao": (
            "selecao_alinhada" if alinhado else "selecao_divergente"
        ), "alinhado_revisao": alinhado}
    return {**base, "estado_revisao": "selecao_rejeitada"}


def _formato_selecao(fontes_com_rotulo_literal: list[str]) -> dict[str, object]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["estado", "motivo", "fonte_id"],
        "properties": {
            "estado": {"type": "string", "enum": ["abster", "fonte_candidata"]},
            "motivo": {"type": "string", "enum": ["", *sorted(_MOTIVOS)]},
            "fonte_id": {"type": "string", "enum": [
                "", *fontes_com_rotulo_literal,
            ]},
        },
    }


def _formato_normalizacao(*, segmentada: bool = False) -> dict[str, object]:
    campos = _CAMPOS_SLOTS if segmentada else _CAMPOS_NORMALIZACAO
    return {
        "type": "object", "additionalProperties": False,
        "required": sorted(campos),
        "properties": {
            "operador": {"type": "string", "enum": ["<", "<=", ">", ">=", "=", "!="]},
            **({"direcao_implicacao": {"type": "string", "enum": [
                "condicoes_suficientes", "condicoes_necessarias", "equivalencia",
            ]}} if not segmentada else {}),
            **{campo: {"type": "string"} for campo in
               campos - {"operador", "direcao_implicacao"}},
        },
    }


def _consultar_modelo(
    sistema: str, entrada: Mapping[str, object], formato: Mapping[str, object],
    *, url: str, modelo: str,
) -> object:
    import requests

    resposta = requests.post(
        url,
        json={"model": modelo, "stream": False, "format": formato,
              "options": {"temperature": 0, "num_predict": 350},
              "messages": [
                  {"role": "system", "content": sistema},
                  {"role": "user", "content": json.dumps(
                      entrada, ensure_ascii=False,
                  )},
              ]},
        timeout=90,
    )
    resposta.raise_for_status()
    return json.loads(resposta.json()["message"]["content"])


def medir_caso(
    caso: Mapping[str, object], revisao: Mapping[str, object],
    *, url: str = "http://127.0.0.1:11434/api/chat",
    modelo: str = "qwen3:4b-instruct",
    consulta: Callable[..., object] | None = None,
    exigir_condicao_unica: bool = False,
    normalizacao_segmentada: bool = False,
) -> dict[str, object]:
    """Revisao nunca governa o gate: apenas a estrutura decide a etapa 2."""
    import requests

    inicio = time.monotonic()
    consultar = consulta or _consultar_modelo
    fontes_com_rotulo_literal = _fontes_com_rotulo_literal(caso)
    fontes_com_condicao_unica = (
        _fontes_com_condicao_unica(caso) if exigir_condicao_unica else []
    )
    fontes_elegiveis = (fontes_com_condicao_unica if exigir_condicao_unica
                        else fontes_com_rotulo_literal)
    selecao_sistema = (
        "Selecione SOMENTE uma fonte de uma regra que defina o rotulo_alvo "
        "para o referente da medida. Nao extraia operador, numero nem unidade. "
        "Fonte que so relata medida ou aciona alarme/controle nao define "
        "rotulo. Fonte com outro rotulo tambem nao serve. Se o referente_id "
        "da medida estiver vazio, abstenha-se. Se nenhuma fonte serve, "
        "estado=abster, motivo apropriado e fonte_id vazio. Se houver "
        "fonte explicita, estado=fonte_candidata, motivo vazio e fonte_id "
        "exato, limitado aos IDs elegiveis fornecidos. A presenca literal do "
        "rotulo e necessaria, mas nao prova que a fonte seja uma regra. "
        "Nao responda ao usuario nem execute acao."
    )
    try:
        selecao = consultar(
            selecao_sistema, {
                **preparar_entrada_modelo(caso),
                "fontes_com_rotulo_literal": fontes_com_rotulo_literal,
                **({"fontes_com_condicao_unica": fontes_com_condicao_unica}
                   if exigir_condicao_unica else {}),
            }, _formato_selecao(fontes_elegiveis),
            url=url, modelo=modelo,
        )
        afericao_selecao = confrontar_selecao(
            caso, revisao, selecao,
            exigir_condicao_unica=exigir_condicao_unica,
        )
        resultado = {"id": caso["id"], "selecao": selecao,
                     "afericao_selecao": afericao_selecao,
                     "normalizacao": "nao_executada"}
        if afericao_selecao["estado"] != "fonte_literal_candidata_revisao_pendente":
            return {**resultado, "duracao_s": round(time.monotonic()-inicio, 2)}
        fonte_id = selecao["fonte_id"]
        fonte = next(item["texto"] for item in caso["fontes"]
                     if item["id"] == fonte_id)
        segmentos = None
        if normalizacao_segmentada:
            segmentos = preparar_normalizacao_segmentada(fonte, caso["rotulo_alvo"])
            resultado["segmentacao"] = segmentos
            if segmentos["estado"] != "segmentos_literais_revisao_pendente":
                return {**resultado, "duracao_s": round(time.monotonic()-inicio, 2)}
        normalizacao_sistema = (
            "A fonte integral ja foi escolhida. Normalize SOMENTE a condicao "
            "numerica desta fonte para o rotulo_alvo e o referente da medida. "
            "Copie citacao_condicao literalmente como trecho continuo da "
            "fonte. Operador compara atributo com limiar: 'abaixo de' e <; "
            "'acima de' e >. Em 'rotulo apenas se condicao', a condicao e "
            "necessaria, nao suficiente. Unidade pode ser vazia em contagem. "
            "Nao mude fonte_id, nao escreva efeito, nao converse ou execute."
        )
        entrada = {"fonte_id": fonte_id, "fonte_integral": fonte,
                   "referentes": caso["referentes"], "medida": caso["medida"],
                   "rotulo_alvo": caso["rotulo_alvo"]}
        if normalizacao_segmentada:
            normalizacao_sistema = (
                "Extraia somente os cinco slots da condicao_literal fornecida: "
                "referente_id, atributo, operador, limiar e unidade. "
                "Escolha o referente_id do inventario e copie o atributo da "
                "condicao. 'abaixo de' indica <; 'acima de' indica >. "
                "limiar e o numero da condicao, nao a medida observada; unidade "
                "e a unidade desse numero, vazia para contagem. "
                "Nao extraia dados do efeito, nao devolva citacoes nem direcao "
                "logica: esses campos pertencem ao host. Retorne apenas JSON."
            )
            entrada = {"fonte_id": fonte_id, "fonte_integral": fonte,
                       "condicao_literal": segmentos["condicao"],
                       "efeito_literal": segmentos["efeito"],
                       "direcao_literal": segmentos["direcao"],
                       "referentes": caso["referentes"]}
        normalizacao = consultar(
            normalizacao_sistema, entrada,
            _formato_normalizacao(segmentada=normalizacao_segmentada),
            url=url, modelo=modelo,
        )
        if (not isinstance(normalizacao, Mapping)
                or set(normalizacao) != (_CAMPOS_SLOTS if normalizacao_segmentada
                                        else _CAMPOS_NORMALIZACAO)
                or any(not isinstance(valor, str) or len(valor) > 300
                       for valor in normalizacao.values())):
            return {**resultado, "normalizacao": normalizacao,
                    "afericao_final": {
                        "estado": "normalizacao_invalida",
                        "aprovado_para_producao": False,
                        "autoriza_efeito": False,
                    }, "duracao_s": round(time.monotonic()-inicio, 2)}
        # A segunda chamada não pode propor nem substituir a fonte escolhida.
        proposta = {"estado": "criterio_candidato", "motivo": "",
                    **normalizacao, "fonte_id": fonte_id}
        if normalizacao_segmentada:
            proposta.update(
                citacao_condicao=segmentos["condicao"]["citacao"],
                direcao_implicacao=segmentos["direcao"]["direcao"],
            )
        return {**resultado, "normalizacao": normalizacao,
                "proposta": proposta,
                "afericao_final": conferir_proposta(caso, revisao, proposta),
                "duracao_s": round(time.monotonic()-inicio, 2)}
    except (requests.RequestException, KeyError, TypeError, ValueError,
            StopIteration) as erro:
        return {"id": caso.get("id"), "erro": type(erro).__name__,
                "duracao_s": round(time.monotonic()-inicio, 2),
                "aprovado_para_producao": False}


def main() -> None:
    casos, revisao = carregar_painel()
    for caso in casos:
        print(json.dumps(medir_caso(caso, revisao[caso["id"]]),
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
