from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


RAIZ = Path(__file__).resolve().parents[1]
CONTENT = RAIZ / "extençao_google" / "content_script.js"
BACKGROUND = RAIZ / "extençao_google" / "background.js"


def _funcao_javascript(codigo: str, assinatura: str) -> str:
    inicio = codigo.index(assinatura)
    abre = codigo.index("{", inicio)
    profundidade = 0
    for indice in range(abre, len(codigo)):
        if codigo[indice] == "{":
            profundidade += 1
        elif codigo[indice] == "}":
            profundidade -= 1
            if profundidade == 0:
                return codigo[inicio:indice + 1]
    raise AssertionError(f"Função incompleta: {assinatura}")


def test_extrator_prefere_descendente_sem_cortar_nome_legitimo() -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js não está disponível para executar o helper da extensão")
    codigo = CONTENT.read_text(encoding="utf-8")
    helper = _funcao_javascript(
        codigo, "function _laylayYoutubeChannelText(node)",
    )
    programa = f"""
{helper}
const leaf = (text) => ({{ textContent: text }});
const container = (fallback, map) => ({{
  textContent: fallback,
  matches: () => false,
  querySelector: (selector) => map[selector] || null,
}});
const duran = container("Duran Duran Duran Duran", {{ "#text": leaf("Duran Duran") }});
const osteve = container("OSteve OSteve", {{
  "a[href*='/@'], a[href*='/channel/'], a[href*='/c/'], a[href*='/user/']": leaf("OSteve")
}});
const fallback = container("Canal legado", {{}});
console.log(JSON.stringify([
  _laylayYoutubeChannelText(duran),
  _laylayYoutubeChannelText(osteve),
  _laylayYoutubeChannelText(fallback),
]));
"""
    resultado = subprocess.run(
        [node, "-e", programa], check=True, capture_output=True,
        text=True, encoding="utf-8",
    )
    assert json.loads(resultado.stdout) == [
        "Duran Duran", "OSteve", "Canal legado",
    ]


def test_todas_as_capturas_do_content_script_usam_o_descendente_especifico() -> None:
    codigo = CONTENT.read_text(encoding="utf-8")
    helper = _funcao_javascript(
        codigo, "function _laylayYoutubeChannelText(node)",
    )

    assert 'node.querySelector?.("#text")' in helper
    assert "a[href*='/@']" in helper
    assert 'node.querySelector?.("yt-formatted-string")' in helper
    assert helper.index('node.querySelector?.("#text")') < helper.index(
        "return normalize(node.textContent)",
    )
    assert codigo.count("_laylayYoutubeChannelText(channelNode)") == 3
    assert "_laylayYoutubeChannelText(ch)" in codigo
    assert "channelNode?.textContent" not in codigo


def test_funcoes_injetadas_do_background_sao_autocontidas() -> None:
    codigo = BACKGROUND.read_text(encoding="utf-8")
    player = _funcao_javascript(
        codigo, "function inspectYouTubePlayerInPage()",
    )
    dados = _funcao_javascript(
        codigo, "function inspectYouTubeDataInPage()",
    )

    for bloco in (player, dados):
        assert "const channelText = (node) =>" in bloco
        assert 'node.querySelector?.("#text")' in bloco
        assert "a[href*='/channel/']" in bloco
        assert "return normalize(node.textContent)" in bloco
    assert "channel: channelText(channelItem)" in player
    assert "channel: channelText(channelNode)" in player
    assert "canal: channelText(channelNode)" in dados
    assert "channelNode?.textContent" not in player
    assert "channelNode?.textContent" not in dados
