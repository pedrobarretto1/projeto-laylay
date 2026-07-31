from mente_laylay.memoria_mental.busca_youtube import extrair_resultados_youtube_busca


HTML_MIX_LONGO = (
    '"videoId":"abcdefghijk",'
    '"title":{"runs":[{"text":"C418 Minecraft Music 1 Hour Relaxing Mix"}]},'
    '"longBylineText":{"runs":[{"text":"Ambient Channel"}]},'
    '"lengthText":{"simpleText":"1:02:03"}'
)


def test_mix_longo_so_e_aceito_quando_foi_pedido() -> None:
    query = "C418 Minecraft relaxing music mix 1 hour"

    como_mix = extrair_resultados_youtube_busca(
        HTML_MIX_LONGO, query, tipo_resultado="selecao_longa"
    )
    como_faixa = extrair_resultados_youtube_busca(
        HTML_MIX_LONGO, query, tipo_resultado="faixa"
    )

    assert como_mix[0]["url"] == "https://www.youtube.com/watch?v=abcdefghijk"
    assert como_mix[0]["duration"] == "1:02:03"
    assert como_faixa == []
