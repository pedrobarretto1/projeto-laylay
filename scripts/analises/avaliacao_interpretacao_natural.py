"""Instrumentos offline; gold nunca integra pedido, autoridade ou estado vivo."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any


def carregar_corpus(caminho: Path) -> dict[str, Any]:
    dados = json.loads(caminho.read_text(encoding="utf-8-sig"))
    if (not isinstance(dados, dict) or dados.get("versao") != 1
            or dados.get("finalidade") != "desenvolvimento"
            or dados.get("anotacao") != "IA_nao_revisada_por_humano"):
        raise ValueError("corpus exige desenvolvimento e procedência explícita da anotação")
    casos = dados.get("casos")
    if not isinstance(casos, list) or not 1 <= len(casos) <= 250:
        raise ValueError("corpus exige de 1 a 250 casos")
    ids = set()
    for caso in casos:
        if (not isinstance(caso, dict) or set(caso) != {
                "id", "familia", "texto", "contexto", "esperados", "atos_esperados"}
                or any(not isinstance(caso[k], str) or not caso[k].strip()
                       for k in ("id", "familia", "texto"))
                or len(caso["texto"]) > 2000 or caso["id"] in ids):
            raise ValueError("identidade ou campos do caso inválidos")
        ids.add(caso["id"])
        if caso["contexto"] not in {"", "volume", "app", "playlist"}:
            raise ValueError("contexto não pertence às fixtures declaradas")
        for chave in ("esperados", "atos_esperados"):
            if not isinstance(caso[chave], list) or any(not isinstance(v, dict) for v in caso[chave]):
                raise ValueError("gabarito exige lista de objetos")
    return dados


def _folhas(valor: dict[str, Any], prefixo: str = "") -> dict[str, Any]:
    resultado = {}
    for chave, item in valor.items():
        nome = f"{prefixo}.{chave}" if prefixo else chave
        if isinstance(item, dict) and item:
            resultado.update(_folhas(item, nome))
        else:
            resultado[nome] = item
    return resultado


def _igual(esperado: Any, observado: Any, campo: str) -> bool:
    if type(esperado) is not type(observado):
        return False
    if isinstance(esperado, str) and campo in {
            "intent", "tipo", "params.nome_app", "interpretacao.operacao", "interpretacao.tipo_recurso"}:
        return esperado.casefold() == observado.casefold()
    return esperado == observado


def _avaliar(esperados: list[dict], observados: list[dict]) -> dict[str, Any]:
    """Compara campos anotados por posição; não afirma semântica dos omitidos."""
    por_campo: dict[str, dict[str, int]] = {}
    divergencias = []
    for indice, esperado in enumerate(esperados):
        atual = _folhas(observados[indice]) if indice < len(observados) else {}
        for campo, valor in _folhas(esperado).items():
            medida = por_campo.setdefault(campo, {"acertos": 0, "avaliados": 0})
            medida["avaliados"] += 1
            correto = campo in atual and _igual(valor, atual[campo], campo)
            medida["acertos"] += int(correto)
            if not correto:
                divergencias.append({"indice": indice, "campo": campo,
                    "esperado": deepcopy(valor), "observado": atual.get(campo),
                    "campo_presente": campo in atual})
    ausentes, extras = max(0, len(esperados) - len(observados)), max(0, len(observados) - len(esperados))
    return {"campos_avaliados_corretos": not divergencias and not ausentes and not extras,
        "ausentes": ausentes, "extras": extras, "divergencias": divergencias,
        "por_campo": por_campo, "campos_nao_anotados_avaliados": False,
        "autoriza_execucao": False, "comprova_efeito": False}


def avaliar_comandos(esperados: list[dict], observados: list[dict]) -> dict[str, Any]:
    return _avaliar(esperados, [c for c in observados if c.get("intent") not in (None, "", "NONE")])


def avaliar_atos(esperados: list[dict], observados: list[dict]) -> dict[str, Any]:
    return _avaliar(esperados, observados)


def validar_indicios_pos(texto: str, pacote: dict[str, Any]) -> dict[str, Any]:
    """Nem tokens pré-computados podem pertencer a outra fala ou perder origem."""
    if (not isinstance(pacote, dict) or pacote.get("texto") != texto
            or any(not isinstance(pacote.get(k), str) or not pacote[k]
                   for k in ("modelo", "versao_modelo", "versao_spacy"))
            or not isinstance(pacote.get("pipeline"), list)
            or not isinstance(pacote.get("tokens"), list)
            or type(pacote.get("segundos")) not in (int, float)
            or not math.isfinite(pacote["segundos"]) or pacote["segundos"] < 0):
        raise ValueError("indícios POS sem procedência ou literal íntegro")
    ultimo_fim = 0
    for token in pacote["tokens"]:
        if (not isinstance(token, dict) or set(token) != {
                "texto", "inicio", "fim", "lemma", "pos", "dep", "cabeca"}
                or any(type(token[k]) is not int for k in ("inicio", "fim", "cabeca"))
                or any(not isinstance(token[k], str) for k in ("texto", "lemma", "pos", "dep"))
                or not ultimo_fim <= token["inicio"] < token["fim"] <= len(texto)
                or texto[token["inicio"]:token["fim"]] != token["texto"]
                or not 0 <= token["cabeca"] < len(texto)):
            raise ValueError("token POS não vinculado ao literal")
        ultimo_fim = token["fim"]
    return deepcopy(pacote)


def preparar_mensagens(
    texto: str, contexto: dict[str, Any], *, indicios_pos: dict[str, Any] | None = None,
    catalogo: str = "",
) -> list[dict[str, str]]:
    """Só texto/contexto explícitos: não aceita caso/gold ou estado pessoal."""
    from mente_laylay.cognicao.leitura_semantica_turno import INSTRUCAO_INTERPRETACAO_POR_ATO
    from mente_laylay.especialistas.capacidades import intents_registradas
    instrucao = ("Ensaio diagnóstico de interpretação, sem executar nem narrar sucesso. "
        "Use o envelope canônico; fala curta, aprendizados vazios. "
        "Comandos são propostas de pedidos atuais, não autorização. "
        "Contexto sintético só sugere referentes, não prova efeito neste ensaio.\n"
        + INSTRUCAO_INTERPRETACAO_POR_ATO + "\nIntents do catálogo canônico: "
        + json.dumps(sorted(intents_registradas()), ensure_ascii=False)
        + "\nCapacidades recuperadas pelo catálogo instalado: " + catalogo
        + "\nContexto diagnóstico qualificado: " + json.dumps(contexto, ensure_ascii=False))
    if indicios_pos is not None:
        pacote = validar_indicios_pos(texto, indicios_pos)
        instrucao += ("\nIndícios morfossintáticos falíveis; não são leitura semântica, "
            "permissão ou confirmação: " + json.dumps({
                "modelo": pacote["modelo"], "tokens": pacote["tokens"]}, ensure_ascii=False))
    return [{"role": "system", "content": instrucao}, {"role": "user", "content": texto}]


def exportar_pos(corpus: Path, destino: Path, modelo: str = "pt_core_news_sm") -> None:
    """Executar no ambiente externo; nenhum import da aplicação ou efeito."""
    import spacy
    casos = carregar_corpus(corpus)["casos"]
    inicio = time.monotonic()
    nlp = spacy.load(modelo)
    carga = time.monotonic() - inicio
    pacotes = {}
    for caso in casos:
        inicio = time.monotonic()
        doc = nlp(caso["texto"])
        pacote = {"texto": caso["texto"], "modelo": modelo,
            "versao_modelo": nlp.meta["version"], "versao_spacy": spacy.__version__,
            "pipeline": list(nlp.pipe_names), "segundos": time.monotonic() - inicio,
            "tokens": [{"texto": t.text, "inicio": t.idx, "fim": t.idx + len(t.text),
                "lemma": t.lemma_, "pos": t.pos_, "dep": t.dep_, "cabeca": t.head.idx} for t in doc]}
        pacotes[caso["id"]] = validar_indicios_pos(caso["texto"], pacote)
    resultado = {"corpus_sha256": hashlib.sha256(corpus.read_bytes()).hexdigest(),
        "config_spacy_sha256": hashlib.sha256(nlp.config.to_str().encode()).hexdigest(),
        "carga_modelo_segundos": carga, "memoria_residente_medida": False,
        "pacotes": pacotes, "aprovado_para_producao": False}
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exportar-pos", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parents[2]
    if not args.saida.resolve().is_relative_to((raiz / "resultados_testes").resolve()):
        parser.error("saída deve pertencer a resultados_testes")
    exportar_pos(args.exportar_pos, args.saida)
