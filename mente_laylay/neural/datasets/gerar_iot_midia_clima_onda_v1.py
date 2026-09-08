"""Completa as seis variantes finais do catálogo neural v0.

Gera exemplos para IOT_CONTROL on/off, MEDIA_CONTROL next/pause/play e WEATHER
sem consultar o Frozen. O lote é staging e nunca concede autoridade.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


MOLDURAS = (
    ("direta", "{imperativo}"),
    ("polida", "por favor {imperativo}"),
    ("modal", "pode {infinitivo}"),
    ("desejo", "quero que você {subjuntivo}"),
    ("sera_que", "será que pode {infinitivo}"),
    ("tem_como", "tem como {infinitivo}"),
    ("condicional", "se puder {imperativo}"),
    ("consegue", "consegue {infinitivo}"),
)

DISPOSITIVOS = (
    "a lâmpada do quarto",
    "o ventilador",
    "a tomada do escritório",
    "a luz da sala",
    "o abajur",
    "a cafeteira",
)

ALVOS_MIDIA = (
    "a música atual",
    "a faixa que está tocando",
    "a reprodução atual",
    "o áudio atual",
    "a playlist",
    "o som que está tocando",
)

LOCAIS_CLIMA = (
    "São Paulo hoje",
    "Curitiba amanhã",
    "Recife no fim de semana",
    "Porto Alegre esta noite",
    "Belo Horizonte pela manhã",
    "Salvador nos próximos dias",
)


# Cada paradigma cruza oito molduras e três alvos (24 exemplos).
ACOES = {
    ("IOT_CONTROL", "on"): (
        ("ligar", "ligar {alvo}", "liga {alvo}", "ligue {alvo}"),
        ("acender", "acender {alvo}", "acende {alvo}", "acenda {alvo}"),
        ("ativar", "ativar {alvo}", "ativa {alvo}", "ative {alvo}"),
        ("energizar", "energizar {alvo}", "energiza {alvo}", "energize {alvo}"),
        ("funcionar", "colocar {alvo} para funcionar", "coloca {alvo} para funcionar", "coloque {alvo} para funcionar"),
    ),
    ("IOT_CONTROL", "off"): (
        ("desligar", "desligar {alvo}", "desliga {alvo}", "desligue {alvo}"),
        ("apagar", "apagar {alvo}", "apaga {alvo}", "apague {alvo}"),
        ("desativar", "desativar {alvo}", "desativa {alvo}", "desative {alvo}"),
        ("cortar", "cortar a energia de {alvo}", "corta a energia de {alvo}", "corte a energia de {alvo}"),
        ("parar", "parar {alvo}", "para {alvo}", "pare {alvo}"),
        ("deixar_desligado", "deixar {alvo} desligado", "deixa {alvo} desligado", "deixe {alvo} desligado"),
    ),
    ("MEDIA_CONTROL", "next"): (
        ("pular", "pular para {alvo}", "pula para {alvo}", "pule para {alvo}"),
        ("avancar", "avançar para {alvo}", "avança para {alvo}", "avance para {alvo}"),
        ("passar", "passar para {alvo}", "passa para {alvo}", "passe para {alvo}"),
        ("tocar_seguinte", "tocar a próxima depois de {alvo}", "toca a próxima depois de {alvo}", "toque a próxima depois de {alvo}"),
        ("mudar", "mudar de {alvo}", "muda de {alvo}", "mude de {alvo}"),
    ),
    ("MEDIA_CONTROL", "pause"): (
        ("pausar", "pausar {alvo}", "pausa {alvo}", "pause {alvo}"),
        ("parar", "parar {alvo}", "para {alvo}", "pare {alvo}"),
        ("interromper", "interromper {alvo}", "interrompe {alvo}", "interrompa {alvo}"),
        ("suspender", "suspender {alvo}", "suspende {alvo}", "suspenda {alvo}"),
        ("dar_pausa", "dar uma pausa em {alvo}", "dá uma pausa em {alvo}", "dê uma pausa em {alvo}"),
        ("deixar_pausado", "deixar {alvo} pausado", "deixa {alvo} pausado", "deixe {alvo} pausado"),
    ),
    ("MEDIA_CONTROL", "play"): (
        ("continuar", "continuar {alvo}", "continua {alvo}", "continue {alvo}"),
        ("reproduzir", "reproduzir {alvo}", "reproduz {alvo}", "reproduza {alvo}"),
        ("retomar", "retomar {alvo}", "retoma {alvo}", "retome {alvo}"),
        ("voltar", "voltar a tocar {alvo}", "volta a tocar {alvo}", "volte a tocar {alvo}"),
        ("iniciar", "iniciar {alvo}", "inicia {alvo}", "inicie {alvo}"),
    ),
    ("WEATHER", "query"): (
        ("consultar", "consultar a previsão para {alvo}", "consulta a previsão para {alvo}", "consulte a previsão para {alvo}"),
        ("ver", "ver a previsão de {alvo}", "vê a previsão de {alvo}", "veja a previsão de {alvo}"),
        ("conferir", "conferir o tempo em {alvo}", "confere o tempo em {alvo}", "confira o tempo em {alvo}"),
        ("saber", "saber como fica o tempo em {alvo}", "mostra como fica o tempo em {alvo}", "mostre como fica o tempo em {alvo}"),
        ("descobrir", "descobrir o clima de {alvo}", "descobre o clima de {alvo}", "descubra o clima de {alvo}"),
    ),
}

ALVOS = {
    ("IOT_CONTROL", "on"): DISPOSITIVOS,
    ("IOT_CONTROL", "off"): DISPOSITIVOS,
    ("MEDIA_CONTROL", "next"): ALVOS_MIDIA,
    ("MEDIA_CONTROL", "pause"): ALVOS_MIDIA,
    ("MEDIA_CONTROL", "play"): ALVOS_MIDIA,
    ("WEATHER", "query"): LOCAIS_CLIMA,
}

NEGADAS = {
    ("IOT_CONTROL", "on"): (
        ("nao", "não ligue {alvo}"), ("evitar", "evita acender {alvo}"),
        ("dispensar", "não precisa ativar {alvo}"), ("recusar", "prefiro não ligar {alvo}"),
        ("cancelar", "cancela a ativação de {alvo}"),
    ),
    ("IOT_CONTROL", "off"): (
        ("nao", "não desligue {alvo}"), ("evitar", "evita apagar {alvo}"),
        ("dispensar", "não precisa desativar {alvo}"), ("recusar", "prefiro não desligar {alvo}"),
    ),
    ("MEDIA_CONTROL", "next"): (
        ("nao", "não pule {alvo}"), ("evitar", "evita avançar de {alvo}"),
        ("dispensar", "não precisa passar de {alvo}"), ("recusar", "prefiro não mudar de {alvo}"),
        ("manter", "deixa {alvo} como está"), ("cancelar", "cancela o avanço de {alvo}"),
    ),
    ("MEDIA_CONTROL", "pause"): (
        ("nao", "não pause {alvo}"), ("evitar", "evita parar {alvo}"),
        ("dispensar", "não precisa interromper {alvo}"), ("recusar", "prefiro não pausar {alvo}"),
    ),
    ("MEDIA_CONTROL", "play"): (
        ("nao", "não reproduza {alvo}"), ("evitar", "evita retomar {alvo}"),
        ("dispensar", "não precisa continuar {alvo}"), ("recusar", "prefiro não tocar {alvo}"),
        ("cancelar", "cancela a reprodução de {alvo}"),
    ),
    ("WEATHER", "query"): (
        ("nao", "não consulte a previsão de {alvo}"), ("evitar", "evita conferir o tempo em {alvo}"),
        ("dispensar", "não precisa ver o clima de {alvo}"), ("recusar", "prefiro não saber a previsão de {alvo}"),
        ("deixar", "deixa a consulta de {alvo} para depois"), ("cancelar", "cancela a busca do clima de {alvo}"),
    ),
}

# Estes enunciados não negam um comando anterior: eles pedem afirmativamente
# que o dispositivo permaneça no estado descrito pela própria superfície.
# Portanto, ensinam a ação de destino e negated=False.
ESTADOS_AFIRMATIVOS_IOT = (
    ("off", "manter_desligado", "mantenha {alvo} desligado"),
    ("on", "manter_ligado", "mantenha {alvo} ligado"),
    ("on", "continuar_funcionando", "deixa {alvo} funcionando"),
)

ESTADOS_AFIRMATIVOS_MIDIA = (
    ("play", "continuar_sem_pausar", "continue com {alvo} sem pausar"),
    ("play", "deixar_continuar", "deixa {alvo} continuar"),
    ("pause", "manter_pausado", "mantenha {alvo} pausado"),
)

HARD_NEGATIVES = {
    "iot": (
        ("relato_passado", "a", "ontem eu liguei {alvo} à noite"), ("relato_passado", "b", "mais cedo eu desliguei {alvo}"),
        ("terceiro", "a", "meu irmão acendeu {alvo}"), ("terceiro", "b", "ela apagou {alvo} antes de sair"),
        ("futuro", "a", "amanhã vou configurar {alvo}"), ("futuro", "b", "depois pretendo ligar {alvo}"),
        ("hipotese", "a", "se estivesse frio eu ligaria {alvo}"), ("hipotese", "b", "se fosse minha casa eu apagaria {alvo}"),
        ("citacao", "a", "ele disse liga {alvo} e saiu"), ("citacao", "b", "ela escreveu desliga {alvo}"),
        ("meta", "a", "a frase acenda {alvo} parece uma ordem"), ("meta", "b", "desligar {alvo} é um exemplo de comando"),
        ("interface", "a", "esse botão liga {alvo} automaticamente"), ("interface", "b", "o sensor desliga {alvo} sozinho"),
        ("tutorial", "a", "o manual ensina como configurar {alvo}"), ("tutorial", "b", "vi um vídeo sobre instalar {alvo}"),
        ("preferencia", "a", "eu gosto de {alvo} ligado à noite"), ("preferencia", "b", "prefiro {alvo} desligado durante o dia"),
        ("evento", "a", "{alvo} ligou sozinho"), ("evento", "b", "{alvo} apagou após a queda de energia"),
    ),
    "music": (
        ("relato_passado", "a", "ontem eu pausei {alvo}"), ("relato_passado", "b", "mais cedo eu avancei {alvo}"),
        ("terceiro", "a", "meu irmão retomou {alvo}"), ("terceiro", "b", "ela interrompeu {alvo}"),
        ("futuro", "a", "depois vou continuar {alvo}"), ("futuro", "b", "amanhã pretendo ouvir {alvo}"),
        ("hipotese", "a", "se estivesse sozinho eu pausaria {alvo}"), ("hipotese", "b", "numa festa eu avançaria {alvo}"),
        ("citacao", "a", "ele disse pausa {alvo} e saiu"), ("citacao", "b", "ela escreveu continua {alvo}"),
        ("meta", "a", "a frase pule {alvo} parece uma ordem"), ("meta", "b", "pausar {alvo} é um exemplo de comando"),
        ("interface", "a", "esse botão avança {alvo} automaticamente"), ("interface", "b", "o player retoma {alvo} sozinho"),
        ("tutorial", "a", "o manual explica como pausar {alvo}"), ("tutorial", "b", "vi um vídeo sobre controlar {alvo}"),
        ("preferencia", "a", "eu gosto de continuar {alvo} do início"), ("preferencia", "b", "prefiro ouvir {alvo} sem interrupção"),
        ("evento", "a", "{alvo} pausou sozinho"), ("evento", "b", "{alvo} avançou depois do anúncio"),
    ),
    "weather": (
        ("relato_passado", "a", "ontem eu consultei a previsão de {alvo}"), ("relato_passado", "b", "mais cedo eu vi o clima de {alvo}"),
        ("terceiro", "a", "meu irmão conferiu o tempo em {alvo}"), ("terceiro", "b", "ela pesquisou a previsão de {alvo}"),
        ("futuro", "a", "amanhã vou consultar o clima de {alvo}"), ("futuro", "b", "depois pretendo ver o tempo em {alvo}"),
        ("hipotese", "a", "se viajasse eu conferiria o clima de {alvo}"), ("hipotese", "b", "num passeio eu olharia a previsão de {alvo}"),
        ("citacao", "a", "ele disse consulte o clima de {alvo}"), ("citacao", "b", "ela escreveu veja a previsão de {alvo}"),
        ("meta", "a", "a frase confira o tempo em {alvo} parece uma ordem"), ("meta", "b", "consultar {alvo} é um exemplo de comando"),
        ("interface", "a", "esse painel mostra o clima de {alvo} automaticamente"), ("interface", "b", "o aplicativo atualiza a previsão de {alvo} sozinho"),
        ("tutorial", "a", "o manual explica como consultar o clima de {alvo}"), ("tutorial", "b", "vi um vídeo sobre prever o tempo em {alvo}"),
        ("preferencia", "a", "eu gosto da previsão de {alvo} em gráficos"), ("preferencia", "b", "prefiro dados detalhados sobre {alvo}"),
        ("evento", "a", "a previsão de {alvo} mudou de repente"), ("evento", "b", "o alerta de {alvo} apareceu sozinho"),
    ),
}


def _dominio(intent: str) -> str:
    return {"IOT_CONTROL": "iot", "MEDIA_CONTROL": "music", "WEATHER": "weather"}[intent]


def _exemplo(texto: str, *, intent: str, is_command: bool, negated: bool,
             action: str, family: str, source: str, domain: str) -> dict[str, Any]:
    return {"text": texto, "intent": intent, "is_command": is_command,
            "negated": negated, "action": action, "family": family,
            "validation_group": family.rsplit("_", 1)[0],
            "source": source, "domain": domain}


def _gerar_variante(intent: str, action: str) -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    alvos = ALVOS[(intent, action)]
    for indice, (label, infinitivo, imperativo, subjuntivo) in enumerate(ACOES[(intent, action)]):
        for indice_molde, (modalidade, molde) in enumerate(MOLDURAS):
            familia = f"iot_midia_clima_v1_{intent.casefold()}_{action}_{label}_{modalidade}"
            for deslocamento in range(3):
                alvo = alvos[(indice + indice_molde + deslocamento * 2) % len(alvos)]
                texto = molde.format(infinitivo=infinitivo.format(alvo=alvo),
                                      imperativo=imperativo.format(alvo=alvo),
                                      subjuntivo=subjuntivo.format(alvo=alvo))
                exemplos.append(_exemplo(texto, intent=intent, is_command=True,
                    negated=False, action=action, family=familia,
                    source="MANUAL_PARAPHRASE", domain=_dominio(intent)))
    for indice, (mecanismo, molde) in enumerate(NEGADAS[(intent, action)]):
        for variante in ("a", "b"):
            familia = f"iot_midia_clima_v1_{intent.casefold()}_{action}_negada_{mecanismo}_{variante}"
            base = 0 if variante == "a" else 3
            for deslocamento in range(2):
                alvo = alvos[(indice + base + deslocamento * 2) % len(alvos)]
                exemplo = _exemplo(molde.format(alvo=alvo), intent=intent,
                    is_command=True, negated=True, action=action, family=familia,
                    source="HARD_NEGATIVE", domain=_dominio(intent))
                exemplos.append(exemplo)
    return exemplos


def _gerar_estados_afirmativos_iot() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for indice, (action, mecanismo, molde) in enumerate(ESTADOS_AFIRMATIVOS_IOT):
        for variante in ("a", "b"):
            familia = (
                "iot_midia_clima_v1_iot_control_"
                f"{action}_estado_{mecanismo}_{variante}"
            )
            base = 0 if variante == "a" else 3
            for deslocamento in range(2):
                alvo = DISPOSITIVOS[(indice + base + deslocamento * 2) % len(DISPOSITIVOS)]
                exemplos.append(_exemplo(
                    molde.format(alvo=alvo), intent="IOT_CONTROL",
                    is_command=True, negated=False, action=action,
                    family=familia, source="MANUAL_PARAPHRASE", domain="iot",
                ))
    return exemplos


def _gerar_estados_afirmativos_midia() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for indice, (action, mecanismo, molde) in enumerate(
        ESTADOS_AFIRMATIVOS_MIDIA
    ):
        for variante in ("a", "b"):
            familia = (
                "iot_midia_clima_v1_media_control_"
                f"{action}_estado_{mecanismo}_{variante}"
            )
            base = 0 if variante == "a" else 3
            for deslocamento in range(2):
                alvo = ALVOS_MIDIA[(indice + base + deslocamento * 2) % len(ALVOS_MIDIA)]
                exemplos.append(_exemplo(
                    molde.format(alvo=alvo), intent="MEDIA_CONTROL",
                    is_command=True, negated=False, action=action,
                    family=familia, source="MANUAL_PARAPHRASE", domain="music",
                ))
    return exemplos


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos = [item for intent, action in ACOES for item in _gerar_variante(intent, action)]
    exemplos.extend(_gerar_estados_afirmativos_iot())
    exemplos.extend(_gerar_estados_afirmativos_midia())
    alvos_dominio = {"iot": DISPOSITIVOS, "music": ALVOS_MIDIA, "weather": LOCAIS_CLIMA}
    for domain, moldes in HARD_NEGATIVES.items():
        alvos = alvos_dominio[domain]
        for indice, (mecanismo, variante, molde) in enumerate(moldes):
            familia = f"iot_midia_clima_v1_{domain}_nao_comando_{mecanismo}_{variante}"
            for deslocamento in range(2):
                alvo = alvos[(indice + deslocamento * 3) % len(alvos)]
                exemplos.append(_exemplo(molde.format(alvo=alvo), intent="NONE",
                    is_command=False, negated=False, action="none", family=familia,
                    source="HARD_NEGATIVE", domain=domain))
    return exemplos


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, int]:
    itens = [dict(item) for item in exemplos]
    textos = [_normalizar(item.get("text", "")) for item in itens]
    if len(textos) != len(set(textos)):
        repetidos = [t for t, n in Counter(textos).items() if n > 1]
        raise ValueError(f"o lote contém textos duplicados: {repetidos[:3]}")
    resumo = {"total": len(itens), "max_exemplos_por_familia": max(
        Counter(item["family"] for item in itens).values(), default=0)}
    for domain in HARD_NEGATIVES:
        resumo[f"hard_negatives_{domain}"] = sum(
            not item["is_command"] and item["domain"] == domain for item in itens)
    for intent, action in ACOES:
        chave = f"{intent.casefold()}_{action}"
        comandos = [i for i in itens if i["intent"] == intent and i["action"] == action]
        resumo[chave] = len(comandos)
        resumo[f"{chave}_negados"] = sum(i["negated"] for i in comandos)
        resumo[f"{chave}_familias"] = len({i["family"] for i in comandos})
    esperado = {"total": 1032, "max_exemplos_por_familia": 3,
        "hard_negatives_iot": 40, "hard_negatives_music": 40,
        "hard_negatives_weather": 40}
    for intent, action in ACOES:
        chave = f"{intent.casefold()}_{action}"
        if (intent, action) == ("IOT_CONTROL", "on"):
            esperado[chave] = 148; esperado[f"{chave}_negados"] = 20
            esperado[f"{chave}_familias"] = 54
        elif (intent, action) == ("IOT_CONTROL", "off"):
            esperado[chave] = 164; esperado[f"{chave}_negados"] = 16
            esperado[f"{chave}_familias"] = 58
        elif (intent, action) == ("MEDIA_CONTROL", "play"):
            esperado[chave] = 148; esperado[f"{chave}_negados"] = 20
            esperado[f"{chave}_familias"] = 54
        elif (intent, action) == ("MEDIA_CONTROL", "pause"):
            esperado[chave] = 164; esperado[f"{chave}_negados"] = 16
            esperado[f"{chave}_familias"] = 58
        else:
            esperado[chave] = 144; esperado[f"{chave}_negados"] = 24
            esperado[f"{chave}_familias"] = 52
    if resumo != esperado:
        raise ValueError(f"cotas inesperadas: {resumo!r} != {esperado!r}")
    return resumo


def escrever_lote(destino: str | Path) -> dict[str, int]:
    exemplos = gerar_exemplos(); resumo = validar_lote(exemplos)
    caminho = Path(destino); caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = "".join(json.dumps(i, ensure_ascii=False, separators=(",", ":")) + "\n" for i in exemplos)
    descritor, temporario = tempfile.mkstemp(prefix=f".{caminho.name}.", suffix=".tmp", dir=str(caminho.parent))
    try:
        with os.fdopen(descritor, "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(conteudo); arquivo.flush(); os.fsync(arquivo.fileno())
        Path(temporario).replace(caminho)
    except Exception:
        Path(temporario).unlink(missing_ok=True); raise
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", default="mente_laylay/neural/datasets/candidatos/iot_midia_clima_onda_v1.jsonl")
    args = parser.parse_args(); resumo = escrever_lote(args.destino)
    print(json.dumps({"destino": args.destino, **resumo}, ensure_ascii=False))


if __name__ == "__main__":
    main()
