"""RED diagnóstico separado: recurso vídeo não pertence à busca musical."""
import pytest
from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto


@pytest.mark.parametrize("texto", [
    "coloca um video do jazzghost", "coloca um vídeo de astronomia",
    "coloca um video de engenharia", "toca um vídeo sobre jardinagem",
    "coloca um video de programação no youtube",
])
def test_tipo_video_explicito_nao_e_admitido_pelo_executor_musical(texto):
    r = detectar_intencao_deterministica_mente(texto, {"normalizar_texto": normalizar_texto})
    assert r and r["intent"] != "MUSIC_SEARCH", r


@pytest.mark.parametrize("texto", ["coloca a musica duality", "toca a musica video killed the radio star"])
def test_video_em_titulo_musical_nao_muda_tipo_do_pedido(texto):
    r = detectar_intencao_deterministica_mente(texto, {"normalizar_texto": normalizar_texto})
    assert r and r["intent"] == "MUSIC_SEARCH", r
