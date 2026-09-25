"""Sonda offline: selecionar texto lido antes da composição didática.

Sobreposição lexical é apenas um filtro conservador de recuperação, não
prova que a frase ensina o conceito ou que duas fontes são compatíveis.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from mente_laylay.cognicao.pesquisa_multifonte import _frases_completas, _tokens
from scripts.analises.sonda_composicao_extrativa_ensino import validar_unidade


_DEFINICAO = re.compile(
    r"\b(?:é|são|significa|consiste|representa|refere-se|"
    r"podem\s+viver|completam\s+(?:seu|o seu)\s+ciclo|"
    r"estamos\s+realizando)\b",
    re.IGNORECASE,
)
_EXEMPLO = re.compile(r"\b(?:um exemplo|os exemplos incluem|por exemplo)\b", re.I)
_REFERENCIA = re.compile(r"^(?:os exemplos|isso|esse|essa|eles|elas)\b", re.I)
_CONDICAO = re.compile(r"\b(?:se|apenas|em climas|desde que|quando|dependend[oa])\b", re.I)
_INICIO_COMPARATIVO = re.compile(r"^enquanto\b", re.I)
_PREAMBULO = re.compile(r"^(?:em|na|no|numa|n[oe]s?\s+estudos?)\b", re.I)
_FORMATO_PEDIDO = frozenset({"exemplo", "exemplos", "papel", "simples", "iniciante"})


def _tem_sujeito_do_tema(frase: str, foco: set[str]) -> bool:
    if _REFERENCIA.search(frase) or frase.startswith("Se é novo"):
        return False
    # Uma subclasse situada ("algumas ... apenas em climas quentes")
    # é contexto/exceção, não definição geral da classe.
    if re.match(r"^algum(?:a|as|s)?\b", frase, re.I):
        return False
    if re.match(r"^sempre que\b", frase, re.I):
        return bool(_tokens(frase) & foco)
    if _INICIO_COMPARATIVO.search(frase):
        return bool(_tokens(frase[:90]) & foco)
    predicado = _DEFINICAO.search(frase)
    if not predicado:
        return False
    sujeito = frase[:predicado.start()]
    # Frases com oração relativa antes do verbo não definem necessariamente
    # o assunto: "O fotoperíodo, que se refere ... luz" não define luz.
    if ", que " in sujeito.casefold():
        sujeito = sujeito.split(",", 1)[0]
    elif "," in sujeito and _PREAMBULO.match(sujeito):
        sujeito = sujeito.rsplit(",", 1)[-1]
    return bool(_tokens(sujeito) & foco)


def selecionar_unidades(
    fontes: Mapping[str, Mapping[str, str]],
    tema: str,
    pedido: str = "",
) -> dict[str, Any]:
    foco = (_tokens(f"{tema} {pedido}") - _FORMATO_PEDIDO)
    candidatos: list[dict[str, Any]] = []
    pendencias: list[dict[str, str]] = []
    for fonte_id, fonte in fontes.items():
        corpo = str(fonte.get("trecho") or "")
        frases = _frases_completas(corpo)
        for indice, frase in enumerate(frases):
            papel = "exemplo" if _EXEMPLO.search(frase) else (
                "definicao" if _tem_sujeito_do_tema(frase, foco) else ""
            )
            if not papel:
                continue
            inicio = indice
            if _REFERENCIA.search(frase):
                if indice == 0:
                    pendencias.append({"fonte_id": fonte_id,
                                       "motivo": "referencia_sem_antecedente"})
                    continue
                # Uma lista anafórica não é exemplo isolado. O enunciado
                # condicional e seu sujeito, quando contíguos, viajam juntos.
                inicio = max(0, indice - 1)
                if inicio and _CONDICAO.search(frases[inicio]):
                    inicio -= 1
            trecho = " ".join(frases[inicio:indice + 1])
            proposta = {"tipo": "literal", "papel": papel,
                        "fonte_id": fonte_id, "trecho": trecho}
            validacao = validar_unidade(proposta, fontes, pedido)
            if validacao["estado"] != "literal_rastreavel":
                pendencias.append({"fonte_id": fonte_id, "motivo": validacao["estado"]})
                continue
            # Tema citado numa introdução ("Na aula sobre luz, um exemplo
            # de bactéria...") não vincula o exemplo ao assunto pedido.
            trecho_relevancia = trecho
            if papel == "exemplo" and inicio == indice and "," in frase:
                antes, depois = frase.split(",", 1)
                if _PREAMBULO.match(antes):
                    trecho_relevancia = depois
            termos = _tokens(trecho_relevancia)
            sobreposicao = foco & termos
            if not sobreposicao:
                pendencias.append({"fonte_id": fonte_id, "papel": papel,
                                   "trecho": trecho,
                                   "motivo": "ligacao_semantica_pendente"})
                continue
            candidatos.append({**proposta, "cobertura": sorted(sobreposicao),
                               "pontuacao": len(sobreposicao)})

    # Uma definição genérica que apenas menciona o tema não deve deslocar
    # outra que também explica o foco específico do pedido.
    definicoes = sorted(
        (item for item in candidatos if item["papel"] == "definicao"),
        key=lambda item: (-item["pontuacao"], item["fonte_id"]),
    )
    escolhidas: list[dict[str, Any]] = []
    coberto: set[str] = set()
    for item in definicoes:
        ganho = set(item["cobertura"]) - coberto
        if not escolhidas or ganho:
            escolhidas.append(item)
            coberto.update(item["cobertura"])
        if len(escolhidas) >= 3:
            break
    exemplos = sorted(
        (item for item in candidatos if item["papel"] == "exemplo"),
        key=lambda item: (-item["pontuacao"], item["fonte_id"]),
    )
    if exemplos:
        escolhidas.append(exemplos[0])
    return {
        "estado": "candidatos" if escolhidas else "sem_evidencia",
        "unidades": [{chave: item[chave] for chave in ("tipo", "papel", "fonte_id", "trecho")}
                     for item in escolhidas],
        "pendencias": pendencias,
        "criterio": "sobreposicao_lexical_nao_e_prova_semantica",
        "aprovado_para_producao": False,
    }
