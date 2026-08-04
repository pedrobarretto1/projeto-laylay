from mente_laylay.memoria_mental.busca_youtube import extrair_resultados_youtube_busca


HTML_MIX_LONGO = (
    '"videoId":"abcdefghijk",'
    '"title":{"runs":[{"text":"C418 Minecraft Music 1 Hour Relaxing Mix"}]},'
    '"longBylineText":{"runs":[{"text":"Ambient Channel"}]},'
    '"lengthText":{"simpleText":"1:02:03"}'
)

HTML_RESULTADO_ATUAL = (
    '"videoId":"aBkTkxKDduc",'
    '"title":{"runs":[{"text":"C418  - Sweden - Minecraft Volume Alpha"}],'
    '"accessibility":{"accessibilityData":{"label":"C418 Sweden"}}},'
    '"longBylineText":{"runs":[{"text":"SMORT",'
    '"navigationEndpoint":{"browseEndpoint":{"browseId":"canal"}}}]},'
    '"lengthText":{"accessibility":{"accessibilityData":{"label":"3 minutos"}},'
    '"simpleText":"3:36"}'
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


def test_extrator_aceita_metadados_extras_do_html_atual_do_youtube() -> None:
    resultados = extrair_resultados_youtube_busca(
        HTML_RESULTADO_ATUAL,
        "C418 - Sweden Minecraft Volume Alpha",
        tipo_resultado="faixa",
    )

    assert resultados == [{
        "video_id": "aBkTkxKDduc",
        "title": "C418  - Sweden - Minecraft Volume Alpha",
        "channel": "SMORT",
        "url": "https://www.youtube.com/watch?v=aBkTkxKDduc",
        "score": resultados[0]["score"],
        "duration": "3:36",
    }]
    assert resultados[0]["score"] >= 15
