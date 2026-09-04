"""Completa a cobertura de VOLUME:down/up sem consultar o Frozen.

O piloto v1 cobre principalmente negações. Esta onda adiciona comandos
afirmativos distribuídos por famílias de verbo e modalidade, além de contrastes
não operacionais. O lote é staging: não treina, não promove e não autoriza.
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


OBJETOS = ("o volume", "o som", "o áudio")

# label, infinitivo, imperativo, subjuntivo. Cada verbo cruza quatro molduras,
# formando famílias independentes sem separar apenas o objeto entre folds.
VERBOS_DOWN = (
    ("baixar", "baixar {objeto}", "baixa {objeto}", "baixe {objeto}"),
    ("diminuir", "diminuir {objeto}", "diminui {objeto}", "diminua {objeto}"),
    ("reduzir", "reduzir {objeto}", "reduz {objeto}", "reduza {objeto}"),
    ("suavizar", "suavizar {objeto}", "suaviza {objeto}", "suavize {objeto}"),
    ("atenuar", "atenuar {objeto}", "atenua {objeto}", "atenue {objeto}"),
    ("cortar", "cortar um pouco de {objeto}", "corta um pouco de {objeto}", "corte um pouco de {objeto}"),
    ("descer", "descer {objeto}", "desce {objeto}", "desça {objeto}"),
    ("mais_baixo", "fazer {objeto} ficar mais baixo", "faz {objeto} ficar mais baixo", "faça {objeto} ficar mais baixo"),
    ("tirar", "tirar um pouco de {objeto}", "tira um pouco de {objeto}", "tire um pouco de {objeto}"),
    ("intensidade", "reduzir a intensidade de {objeto}", "reduz a intensidade de {objeto}", "reduza a intensidade de {objeto}"),
    ("nivel", "baixar o nível de {objeto}", "baixa o nível de {objeto}", "baixe o nível de {objeto}"),
)

VERBOS_UP = (
    ("aumentar", "aumentar um pouco {objeto}", "aumenta um pouco {objeto}", "aumente um pouco {objeto}"),
    ("subir", "subir {objeto}", "sobe {objeto}", "suba {objeto}"),
    ("elevar", "elevar {objeto}", "eleva {objeto}", "eleve {objeto}"),
    ("intensificar", "intensificar {objeto}", "intensifica {objeto}", "intensifique {objeto}"),
    ("amplificar", "amplificar {objeto}", "amplifica {objeto}", "amplifique {objeto}"),
    ("reforcar", "reforçar {objeto}", "reforça {objeto}", "reforce {objeto}"),
    ("mais_alto", "fazer {objeto} ficar mais alto", "faz {objeto} ficar mais alto", "faça {objeto} ficar mais alto"),
    ("mais_forte", "colocar {objeto} mais forte", "coloca {objeto} mais forte", "coloque {objeto} mais forte"),
    ("dar_volume", "dar mais volume para {objeto}", "dá mais volume para {objeto}", "dê mais volume para {objeto}"),
    ("intensidade", "aumentar a intensidade de {objeto}", "aumenta a intensidade de {objeto}", "aumente a intensidade de {objeto}"),
    ("nivel", "subir o nível de {objeto}", "sobe o nível de {objeto}", "suba o nível de {objeto}"),
)

MOLDURAS = (
    ("direta", "{imperativo}"),
    ("polida", "por favor {imperativo}"),
    ("modal", "pode {infinitivo}"),
    ("desejo", "quero que você {subjuntivo}"),
)

NAO_COMANDOS = (
    ("relato_passado", "a", "ontem eu ajustei {objeto} durante o filme"),
    ("relato_passado", "b", "mais cedo eu mexi em {objeto} do computador"),
    ("relato_terceiro", "a", "meu irmão aumentou {objeto} na festa"),
    ("relato_terceiro", "b", "ela diminuiu {objeto} antes da reunião"),
    ("plano_futuro", "a", "amanhã vou configurar {objeto} com calma"),
    ("plano_futuro", "b", "depois eu pretendo ajustar {objeto}"),
    ("hipotese", "a", "se fosse meu aparelho eu baixaria {objeto}"),
    ("hipotese", "b", "numa festa eu aumentaria {objeto}"),
    ("citacao", "a", "ele disse aumenta {objeto} e foi embora"),
    ("citacao", "b", "ela escreveu diminui {objeto} na mensagem"),
    ("metalinguagem", "a", "a frase baixa {objeto} parece uma ordem"),
    ("metalinguagem", "b", "aumenta {objeto} é apenas um exemplo de comando"),
    ("interface", "a", "esse controle altera {objeto} automaticamente"),
    ("interface", "b", "o aplicativo consegue regular {objeto} sozinho"),
    ("tutorial", "a", "o manual ensina como ajustar {objeto}"),
    ("tutorial", "b", "assisti a um vídeo sobre configurar {objeto}"),
    ("preferencia", "a", "eu gosto de {objeto} mais baixo para estudar"),
    ("preferencia", "b", "prefiro {objeto} mais alto em festas"),
    ("comparacao", "a", "na televisão antiga {objeto} era mais fraco"),
    ("comparacao", "b", "neste fone {objeto} parece mais intenso"),
    ("evento_automatico", "a", "{objeto} aumentou sozinho durante o jogo"),
    ("evento_automatico", "b", "{objeto} ficou baixo depois da atualização"),
    ("pergunta_tecnica", "a", "como funciona o controle de {objeto}"),
    ("pergunta_tecnica", "b", "qual componente mede {objeto} do sistema"),
    ("assunto", "a", "a conversa era sobre {objeto} do notebook"),
    ("assunto", "b", "estávamos discutindo a qualidade de {objeto}"),
    ("desejo_passado", "a", "ontem eu queria {objeto} um pouco mais alto"),
    ("desejo_passado", "b", "mais cedo tive vontade de baixar {objeto}"),
    ("pedido_reportado", "a", "ela pediu que eu aumentasse {objeto}"),
    ("pedido_reportado", "b", "ele queria que eu reduzisse {objeto}"),
)


def _exemplo(
    texto: str,
    *,
    intent: str,
    is_command: bool,
    action: str,
    family: str,
    source: str,
) -> dict[str, Any]:
    return {
        "text": texto,
        "intent": intent,
        "is_command": is_command,
        "negated": False,
        "action": action,
        "family": family,
        "validation_group": family.rsplit("_", 1)[0],
        "source": source,
        "domain": "audio",
    }


def _gerar_comandos(
    verbos: Iterable[tuple[str, str, str, str]],
    *,
    action: str,
) -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for label, infinitivo, imperativo, subjuntivo in verbos:
        for modalidade, molde in MOLDURAS:
            familia = f"volume_v2_{action}_{label}_{modalidade}"
            for objeto in OBJETOS:
                texto = molde.format(
                    infinitivo=infinitivo.format(objeto=objeto),
                    imperativo=imperativo.format(objeto=objeto),
                    subjuntivo=subjuntivo.format(objeto=objeto),
                )
                exemplos.append(_exemplo(
                    texto,
                    intent="VOLUME",
                    is_command=True,
                    action=action,
                    family=familia,
                    source="MANUAL_PARAPHRASE",
                ))
    return exemplos


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos = [
        *_gerar_comandos(VERBOS_DOWN, action="down"),
        *_gerar_comandos(VERBOS_UP, action="up"),
    ]
    for mecanismo, variante, molde in NAO_COMANDOS:
        familia = f"volume_v2_nao_comando_{mecanismo}_{variante}"
        for objeto in OBJETOS[:2]:
            exemplos.append(_exemplo(
                molde.format(objeto=objeto),
                intent="NONE",
                is_command=False,
                action="none",
                family=familia,
                source="HARD_NEGATIVE",
            ))
    return exemplos


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, int]:
    itens = [dict(item) for item in exemplos]
    textos = [_normalizar(item.get("text", "")) for item in itens]
    if len(textos) != len(set(textos)):
        repetidos = [texto for texto, total in Counter(textos).items() if total > 1]
        raise ValueError(f"o lote contém textos duplicados: {repetidos[:3]}")
    down = [item for item in itens if item["action"] == "down"]
    up = [item for item in itens if item["action"] == "up"]
    nao_comandos = [item for item in itens if not item["is_command"]]
    observado = {
        "total": len(itens),
        "volume_down": len(down),
        "volume_up": len(up),
        "nao_comandos": len(nao_comandos),
        "familias_down": len({item["family"] for item in down}),
        "familias_up": len({item["family"] for item in up}),
        "familias_nao_comando": len({item["family"] for item in nao_comandos}),
        "max_exemplos_por_familia": max(
            Counter(item["family"] for item in itens).values(),
            default=0,
        ),
    }
    esperado = {
        "total": 324,
        "volume_down": 132,
        "volume_up": 132,
        "nao_comandos": 60,
        "familias_down": 44,
        "familias_up": 44,
        "familias_nao_comando": 30,
        "max_exemplos_por_familia": 3,
    }
    if observado != esperado:
        raise ValueError(f"cotas inesperadas: {observado!r} != {esperado!r}")
    return observado


def escrever_lote(destino: str | Path) -> dict[str, int]:
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in exemplos
    )
    descritor, temporario = tempfile.mkstemp(
        prefix=f".{caminho.name}.",
        suffix=".tmp",
        dir=str(caminho.parent),
    )
    try:
        with os.fdopen(descritor, "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        Path(temporario).replace(caminho)
    except Exception:
        Path(temporario).unlink(missing_ok=True)
        raise
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default="mente_laylay/neural/datasets/candidatos/volume_onda_v2.jsonl",
    )
    args = parser.parse_args()
    resumo = escrever_lote(args.destino)
    print(json.dumps({"destino": args.destino, **resumo}, ensure_ascii=False))


if __name__ == "__main__":
    main()
