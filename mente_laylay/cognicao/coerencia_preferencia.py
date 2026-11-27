"""Sugestões de escolha podem ser comparadas somente no cenário a que se referem."""

from __future__ import annotations

import re
from typing import Any, Mapping

from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.referencias_linguagem import (
    PerspectivaEnunciador, enunciados_discursivos, operando_opiniao_literal, texto_fora_de_citacoes,
)


_DETERMINANTE = r"(?:o|a|os|as|um|uma|algo)"
_CONSULTA = re.compile(
    r"^(?:e\s+)?(?:voce|vc|tu|laylay|lay)\s+"
    r"(?:prefere|preferiria|escolheria|iria\s+(?:mais\s+)?de|"
    r"ficaria\s+com|optaria\s+por)\s+"
    r"(?P<a>[^?,.!:;]+?)\s+ou\s+(?P<b>[^?,.!:;]+)\?*$"
)
_ESCOLHE = (r"(?:prefiro|escolho|escolheria|(?:vou|iria) de|(?:fico|ficaria) com|"
            r"(?:opto|optaria) por|gosto mais (?:de|do|da))")
_FAVORITO = r"(?:(?:o\s+)?meu\s+|(?:a\s+)?minha\s+)(?:preferid[oa]|favorit[oa])"
_MELHOR = r"(?:(?:e|fica|seria|ficaria)\s+(?:ainda\s+)?melhor|melhor\s+ainda)"
_ADVERSATIVO = re.compile(r"[,;]?\s*\b(?:mas|porem|contudo|entretanto)\b[,\s]+")
_RETIFICACAO = re.compile(r"^(?:pensando melhor|mudei de ideia|revendo a escolha)\s*[:,]\s*")
_ESCOPO = r"(?:se|caso|quando|para|pra|em|na|no|nas|nos)\s+"
_MESMO_ESCOPO = re.compile(r"(?:na|no|para (?:a|o))\s+mesm[oa](?:\s+\w+){0,3}$")
_CENARIO_INDEFINIDO = re.compile(r"^(?:para|pra|(?:se|caso) (?:for|fosse|seja))\s+um[a]?\s+(?P<alvo>.+)$")
_ESCOLHA_DE_CONDUTA = re.compile(
    r"(?:e )?(?:voc[eê]|vc|tu) (?:[ée]|seria|fica|ficaria) mais (?P<atitude>[^\W\d_]+) "
    r"ou (?P<modo>ia|iria|preferiria) (?P<conduta>[^\W\d_]+r(?: [\w-]+){0,12})\?",
    re.IGNORECASE,
)
_OUTRA_RELACAO_NA_ESCOLHA = re.compile(
    r"\b(?:quando|porque|pois|antes|depois|embora|caso|se|eu|me|mim|comigo|"
    r"voce|tu|te|ti|contigo|meus?|minhas?|teus?|tuas?|seus?|suas?)\b"
)


def escolha_cotidiana_de_conduta(texto: str) -> str:
    """Localiza a única pergunta, que contrasta duas atitudes da interlocutora."""
    autoral = texto_fora_de_citacoes(texto)
    partes = enunciados_discursivos(autoral)
    if not partes or autoral.count("?") != 1:
        return ""
    return partes[-1] if realizacoes_escolha_cotidiana(partes[-1]) else ""


def realizacoes_escolha_cotidiana(pergunta: str) -> tuple[str, ...]:
    """As duas alternativas do interlocutor em primeira pessoa e no hipotético."""
    pergunta = " ".join(pergunta.split())
    leitura = _ESCOLHA_DE_CONDUTA.fullmatch(pergunta)
    if leitura is None or _OUTRA_RELACAO_NA_ESCOLHA.search(normalizar_texto_basico(leitura["conduta"])):
        return ()
    atitude = leitura["atitude"].casefold()
    conduta = leitura["modo"].casefold() + " " + leitura["conduta"]
    return (f"Eu seria mais {atitude}.", f"Acho que eu seria mais {atitude}.",
            f"Eu {conduta}.", f"Eu {conduta}, confesso.")


def _sem_determinante(valor: str) -> str:
    return re.sub(rf"^{_DETERMINANTE}\s+", "", valor).strip()


def alternativas_preferencia(trecho: str) -> tuple[str, ...]:
    """Reconhece uma comparação nominal dirigida à assistente."""
    achado = _CONSULTA.fullmatch(normalizar_texto_basico(texto_fora_de_citacoes(trecho)))
    if not achado:
        return ()
    opcoes = tuple(_sem_determinante(achado[chave]) for chave in ("a", "b"))
    if len(set(opcoes)) == 2 and all(operando_opiniao_literal(opcao) for opcao in opcoes):
        return opcoes
    return ()


def alternativas_preferencia_vigentes(
    contrato: Mapping[str, Any], texto: str, turno_id: Any,
) -> tuple[str, ...]:
    """Vincula a comparação ao ato do host, sem tomar a fala gerada como fonte."""
    perspectiva = contrato.get("perspectiva_enunciador")
    opcoes = contrato.get("alternativas_preferencia")
    if (contrato.get("origem") == "mente_unica" and contrato.get("autoriza_execucao") is False
            and "opiniao" in contrato.get("atos", ())
            and type(perspectiva) is PerspectivaEnunciador and perspectiva.vigente(texto, turno_id)
            and str(contrato.get("turno_id")) == perspectiva.turno_id
            and isinstance(opcoes, (list, tuple)) and len(opcoes) == 2
            and all(isinstance(opcao, str) and operando_opiniao_literal(opcao) for opcao in opcoes)):
        return tuple(opcoes)
    return ()


def _formas_opcao(opcoes: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    esquerda, direita = (opcao.split() for opcao in opcoes)
    formas = [{opcoes[0]}, {opcoes[1]}]
    if len(esquerda) == len(direita) == 2 and esquerda[0] == direita[0]:
        formas[0].add(esquerda[1])
        formas[1].add(direita[1])
    elif {len(esquerda), len(direita)} == {1, 2}:
        maior = 0 if len(esquerda) == 2 else 1
        palavras = esquerda if maior == 0 else direita
        menor = opcoes[1 - maior]
        # O substantivo pode estar elidido quando ambos os sufixos
        # funcionam como adjetivos. Não formar híbridos entre dois nomes.
        if all((consultar_morfologia(palavra) or 0) & 2 for palavra in (menor, palavras[1])):
            formas[maior].add(palavras[1])
            formas[1 - maior].add(f"{palavras[0]} {menor}")
    return tuple(tuple(sorted(variantes, key=lambda valor: (-len(valor), valor))) for variantes in formas)


def _escopo_literal(escopo: str) -> str:
    return re.sub(r"^(?:pra|(?:se|caso) (?:for|fosse|seja))\s+", "para ", escopo).strip()


def _ler_posicao(parte: str, formas: tuple[tuple[str, ...], ...]) -> tuple[int, str, str] | None:
    escopo = ""
    if re.match(rf"^{_ESCOPO}", parte):
        condicao, separador, predicado = parte.partition(",")
        if separador:
            escopo, parte = condicao, predicado.strip()
    parte = re.sub(r"^(?:eu\s+)?acho\s+que\s+", "", parte)
    for indice, variantes in enumerate(formas):
        alternativa = rf"(?:{_DETERMINANTE}\s+)?(?:{'|'.join(map(re.escape, variantes))})\b"
        direta = re.match(rf"^(?:eu\s+)?{_ESCOLHE}\s+{alternativa}", parte)
        favorita = re.match(rf"^{alternativa}\s+(?:(?:e|seria)\s+{_FAVORITO}|{_MELHOR})\b", parte)
        if direta or favorita:
            resto = parte[(direta or favorita).end():].strip()
            if favorita and re.match(r"^segundo\s+", resto):
                continue
            if resto.startswith("que ") and favorita:
                # Um comparativo que nomeia terceiro não compara o par.
                outra = "|".join(map(re.escape, formas[1 - indice]))
                if not re.match(rf"^que\s+(?:{_DETERMINANTE}\s+)?(?:{outra})\b", resto):
                    continue
            if not escopo and re.match(rf"^{_ESCOPO}", resto) and resto != "no geral":
                escopo = re.split(r"[,.;]|\s+(?:porque|pois)\b", resto, maxsplit=1)[0]
            return indice, _escopo_literal(escopo), resto
        # A condição pode apenas renomear a própria opção avaliada. "Se for
        # X, fica melhor" escolhe X, sem introduzir um segundo cenário.
        if (re.fullmatch(rf"(?:se|caso)\s+(?:for|fosse|seja)\s+{alternativa}", escopo)
                and re.match(rf"^{_MELHOR}\b", parte)):
            return indice, "", parte
    return None


def preferencia_conflitante(fala: str, opcoes: tuple[str, ...]) -> bool:
    """Confere compromissos explícitos da autora. Menção e apoio factual são outros atos."""
    formas = _formas_opcao(opcoes)
    posicoes: dict[str, int] = {}
    ultimo_escopo = ""
    for enunciado in enunciados_discursivos(texto_fora_de_citacoes(fala)):
        if enunciado.endswith("?"):
            continue
        for parte in _ADVERSATIVO.split(normalizar_texto_basico(enunciado)):
            parte = parte.strip(" ,.;")
            retificacao = _RETIFICACAO.match(parte)
            posicao = _ler_posicao(parte[retificacao.end():] if retificacao else parte, formas)
            if posicao is None:
                continue
            lado, escopo, _ = posicao
            if _MESMO_ESCOPO.fullmatch(escopo):
                escopo = ultimo_escopo
            if not retificacao and escopo in posicoes and posicoes[escopo] != lado:
                return True
            posicoes[escopo] = lado
            ultimo_escopo = escopo
    return False


def frase_de_preferencia_condicional(frase: str, opcoes: tuple[str, ...]) -> bool:
    """Reconhece condição hipotética e escolha sem alegações adicionais."""
    if not opcoes or not frase or frase.rstrip().endswith("?"):
        return False
    condicao, separador, _ = frase.partition(",")
    if not separador or any(c.isupper() for c in condicao[1:]):
        return False
    hipotese = _CENARIO_INDEFINIDO.fullmatch(normalizar_texto_basico(condicao))
    if hipotese is None or not operando_opiniao_literal(hipotese["alvo"]):
        return False
    posicao = _ler_posicao(normalizar_texto_basico(frase).rstrip(".!"), _formas_opcao(opcoes))
    return posicao is not None and not posicao[2]
