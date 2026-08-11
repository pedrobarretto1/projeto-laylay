from mente_laylay.memoria_mental.continuidade_geral import (
    registrar_evento_continuidade,
    resolver_continuacao_aditiva,
    selecionar_continuidade,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    foco_por_dominio,
    resolver_repeticao_ultima_acao,
    registrar_mente_curta,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.contexto_imediato import (
    referencia_contextual_imediata,
    resolver_comando_acao_geral_contextual,
)
from mente_laylay.memoria_mental.pendencia import criar_pendencia, limpar_pendencia, registrar_pendencia
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.memoria_mental.continuidade_semantica import resolver_continuidade_semantica


def test_um_contrato_preserva_dominios_sem_contaminacao():
    estado = estado_mental_inicial()
    estado = registrar_evento_continuidade(
        estado,
        evento="acao",
        intent="MUSIC_SEARCH",
        alvo="Duality - Slipknot",
        params={"query": "Duality - Slipknot"},
        status="musica_aberta",
    )
    estado = registrar_resultado_execucao(
        estado,
        {
            "intent": "IOT_CONTROL",
            "params": {"acao": "ajustar_cor", "alvo": "lampada_quarto", "cor": "roxo"},
            "status": "cor_ajustada",
            "executou": True,
            "confirmado": True,
        },
        "deixa a luz roxa",
    )

    atual = selecionar_continuidade(estado, texto="tenta de novo")
    musica = selecionar_continuidade(estado, texto="pausa a musica")

    assert atual["dominio"] == "iot"
    assert atual["alvo"] == "lampada_quarto"
    assert musica["dominio"] == "musica"
    assert musica["alvo"] == "Duality - Slipknot"


def test_resultado_confirmado_fecha_pendencia_da_mesma_intencao() -> None:
    estado = registrar_pendencia(
        estado_mental_inicial(),
        criar_pendencia(
            origem="oferta_musical",
            tipo="escolha",
            dominio="musica",
            conteudo="Qual música você quer?",
            intencao="MUSIC_SEARCH",
            foi_falada=True,
        ),
    )

    estado = registrar_resultado_execucao(
        estado,
        {
            "intent": "MUSIC_SEARCH",
            "params": {"query": "Remember The Time"},
            "status": "musica_reproduzindo",
            "executou": True,
            "confirmado": True,
        },
        "Remember The Time",
    )

    assert estado["pendencia_atual"] == {}
    assert estado["ultima_pendencia_encerrada"]["status"] == "resolvida_por_execucao"


def test_resultado_sem_confirmacao_preserva_pendencia_da_mesma_intencao() -> None:
    estado = registrar_pendencia(
        estado_mental_inicial(),
        criar_pendencia(
            origem="oferta_musical",
            tipo="escolha",
            dominio="musica",
            conteudo="Qual música você quer?",
            intencao="MUSIC_SEARCH",
            foi_falada=True,
        ),
    )

    estado = registrar_resultado_execucao(
        estado,
        {
            "intent": "MUSIC_SEARCH",
            "params": {"query": "Remember The Time"},
            "status": "musica_enviada_sem_confirmacao",
            "executou": True,
            "confirmado": None,
        },
        "Remember The Time",
    )

    assert estado["pendencia_atual"]["status"] == "ativa"


def test_referencia_imediata_prefere_a_continuidade_geral():
    estado = estado_mental_inicial()
    estado = registrar_evento_continuidade(
        estado,
        evento="acao",
        intent="PLAYLIST_PLAY",
        alvo="alternativo",
        params={"nome_playlist": "alternativo"},
        status="playlist_aberta",
    )

    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado,
        foco_vivo={},
        texto_atual="coloca ela de novo",
    )

    assert referencia["origem_continuidade"] == "geral"
    assert referencia["tipo"] == "playlist"
    assert referencia["alvo"] == "alternativo"


def test_curadoria_da_laylay_mantem_propriedade_na_continuidade() -> None:
    estado = registrar_evento_continuidade(
        estado_mental_inicial(),
        evento="acao",
        intent="LAYLAY_PLAYLIST_LIST",
        alvo="xodos_que_eu_seperei",
        params={"nome_playlist": "xodos_que_eu_seperei"},
        status="playlists_listadas",
    )

    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado,
        foco_vivo={},
        texto_atual="quais músicas tem nela?",
    )
    comando = resolver_comando_acao_geral_contextual(
        "quais músicas tem nela",
        referencia,
        ultima_playlist="sendo sendo",
    )

    assert estado["continuidade_geral"]["dominio_ativo"] == "playlist_laylay"
    assert referencia["tipo"] == "playlist_laylay"
    assert referencia["alvo"] == "xodos_que_eu_seperei"
    assert comando == {
        "intent": "LAYLAY_PLAYLIST_LIST",
        "params": {
            "nome_playlist": "xodos_que_eu_seperei",
            "referencia_contextual": True,
        },
    }


def test_playlist_do_usuario_continua_separada_da_curadoria_da_laylay() -> None:
    comando = resolver_comando_acao_geral_contextual(
        "quais músicas tem nela",
        {
            "tipo": "playlist",
            "alvo": "sendo sendo",
            "params": {"nome_playlist": "sendo sendo"},
        },
    )

    assert comando == {
        "intent": "PLAYLIST_LIST",
        "params": {
            "nome_playlist": "sendo sendo",
            "referencia_contextual": True,
        },
    }


def test_pendencia_usa_o_mesmo_contrato_e_e_encerrada():
    estado = estado_mental_inicial()
    estado = registrar_pendencia(
        estado,
        criar_pendencia(
            origem="lixeira_laylay",
            tipo="confirmacao",
            dominio="arquivos",
            conteudo="Enviar antonio para a lixeira?",
            intencao="CONFIRM_DELETE_ITEM",
            foi_falada=True,
        ),
    )
    pendente = selecionar_continuidade(estado, texto="sim")
    assert pendente["dominio"] == "arquivos"
    assert pendente["evento"] == "pendencia"

    estado = limpar_pendencia(estado, motivo="confirmada")
    assert selecionar_continuidade(estado, dominio="arquivos") == {}


def test_nome_de_musica_completa_esclarecimento_sem_voltar_para_llm():
    mental = registrar_mente_curta(
        estado_mental_inicial(),
        texto_usuario="coloca uma música",
        resposta_ia="Me diz a música.",
        intencao="MUSIC_SEARCH",
        habilidade="musica",
    )

    class EstadoFalso:
        def __init__(self, mente):
            self.mental = mente

        def substituir(self, dominio, valor):
            assert dominio == "mental"
            self.mental = valor

    estado = EstadoFalso(mental)
    runtime = EstadoContextoRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_curto": lambda texto: str(texto).casefold().strip(),
        },
        estado_runtime_getter=lambda: estado,
    )

    resultado = runtime.resolver_pergunta_curta_contextual_intencao("love me")

    assert resultado == {
        "intent": "MUSIC_SEARCH",
        "params": {"query": "love me", "origem": "continuacao_busca"},
    }
    assert estado.mental["pendencia_atual"] == {}


def test_recomendacao_secundaria_nao_substitui_esclarecimento_musical():
    mental = registrar_mente_curta(
        estado_mental_inicial(),
        texto_usuario="coloca uma música",
        resposta_ia="Qual faixa você quer?",
        intencao="MUSIC_SEARCH",
        habilidade="musica",
    )
    id_esclarecimento = mental["pendencia_atual"]["id"]

    mental = registrar_mente_curta(
        mental,
        texto_usuario="coloca uma música",
        resposta_ia=(
            "Vou te jogar uma nova na mesa: Supercombo - Piloto Automatico. "
            "Não executei nada, só recomendei mesmo."
        ),
        intencao="MUSIC_OPINION_CHAT",
        alvo="Supercombo - Piloto Automatico",
        habilidade="musica",
    )

    assert mental["pendencia_atual"]["id"] == id_esclarecimento
    assert mental["pendencia_atual"]["tipo"] == "esclarecimento"
    continuidade = selecionar_continuidade(mental, dominio="musica")
    assert continuidade["evento"] == "pendencia"
    assert continuidade["origem"] == "esclarecimento_operacional"


def test_repeticao_semantica_usa_dominio_ativo_da_continuidade_geral():
    estado = estado_mental_inicial()
    estado = registrar_evento_continuidade(
        estado,
        evento="acao",
        intent="MEDIA_CONTROL",
        alvo="musica",
        params={"acao": "pause"},
        status="midia_pause",
    )
    estado = registrar_resultado_execucao(
        estado,
        {
            "intent": "IOT_CONTROL",
            "params": {"acao": "ajustar_cor", "alvo": "lampada_quarto", "cor": "roxo"},
            "status": "cor_ajustada",
            "executou": True,
            "confirmado": True,
        },
        "deixa a luz roxa",
    )

    decisao = resolver_continuidade_semantica(
        "tenta de novo",
        mente=estado,
    )

    assert decisao.dominio == "iot"
    assert decisao.intent == "IOT_CONTROL"


def test_continuidade_geral_nasce_como_fonte_oficial():
    continuidade = estado_mental_inicial()["continuidade_geral"]
    assert continuidade["modo"] == "oficial"
    assert continuidade["fonte_autoritativa"] is True


def test_foco_oficial_vence_espelho_legado_conflitante():
    estado = estado_mental_inicial()
    estado["focos_por_dominio"] = {
        "musica": {"alvo": "faixa errada", "intencao": "MUSIC_SEARCH", "ts": 9999999999.0},
    }
    estado = registrar_evento_continuidade(
        estado,
        evento="acao",
        intent="PLAYLIST_PLAY",
        alvo="alternativo",
        params={"nome_playlist": "alternativo"},
        status="playlist_aberta",
        reexecutavel=True,
    )

    foco = foco_por_dominio(estado, "musica")
    assert foco["alvo"] == "alternativo"
    assert foco["origem_continuidade"] == "geral_oficial"


def test_repeticao_oficial_vence_ultima_acao_legada_conflitante():
    estado = estado_mental_inicial()
    estado.update({
        "ultima_acao_intent": "MEDIA_CONTROL",
        "ultima_acao_params": {"acao": "pause"},
        "ultima_acao_reexecutavel": True,
    })
    estado = registrar_evento_continuidade(
        estado,
        evento="acao",
        intent="IOT_CONTROL",
        alvo="lampada_quarto",
        params={"acao": "ajustar_cor", "alvo": "lampada_quarto", "cor": "roxo"},
        status="cor_ajustada",
        reexecutavel=True,
    )

    resultado = resolver_repeticao_ultima_acao(
        "tenta de novo",
        estado,
        lambda texto: texto.casefold(),
    )
    assert resultado["intent"] == "IOT_CONTROL"
    assert resultado["params"]["alvo"] == "lampada_quarto"


def test_repeticao_de_link_copiado_preserva_url_completa():
    url = (
        "https://www.youtube.com/watch?v=gndkfhyh5mo"
        "&list=RDgndkfhyh5mo&start_radio=1"
    )
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "OPEN_URL",
            "params": {"url": url},
            "status": "url_aberta",
            "executou": True,
            "confirmado": True,
        },
        "abre o link que eu copiei",
        origem="area_transferencia",
    )

    resultado = resolver_repeticao_ultima_acao(
        "tenta de novo",
        estado,
        lambda texto: texto.casefold(),
    )

    assert resultado == {"intent": "OPEN_URL", "params": {"url": url}}


def test_essa_tambem_herda_ultima_operacao_compativel_e_nao_contexto_de_jogo():
    estado = estado_mental_inicial()
    # O jogo estava no contexto pouco antes, como no terminal real.
    estado = registrar_evento_continuidade(
        estado,
        evento="percepcao",
        intent="GAME_VISION",
        alvo="Path of Exile 2",
        params={"jogo": "Path of Exile 2"},
        status="analise_visual_solicitada",
    )
    estado = registrar_evento_continuidade(
        estado,
        evento="acao",
        intent="PLAYLIST_ADD",
        alvo="sendo sendo",
        params={"nome_playlist": "sendo sendo"},
        status="playlist_musica_adicionada",
    )

    assert resolver_continuacao_aditiva(estado, texto="essa também") == {
        "intent": "PLAYLIST_ADD",
        "params": {
            "nome_playlist": "sendo sendo",
            "referencia_contextual": True,
        },
    }


def test_continuacao_aditiva_nao_repete_operacao_sem_politica_segura():
    estado = registrar_evento_continuidade(
        estado_mental_inicial(),
        evento="acao",
        intent="DELETE_ITEM",
        alvo="relatorio.txt",
        params={"alvo": "relatorio.txt"},
        status="movido_para_lixeira",
    )

    assert resolver_continuacao_aditiva(estado, texto="esse também") == {}


def test_continuacao_aditiva_rejeita_resultado_anterior_com_falha():
    estado = registrar_evento_continuidade(
        estado_mental_inicial(),
        evento="acao",
        intent="PLAYLIST_ADD",
        alvo="sendo sendo",
        params={"nome_playlist": "sendo sendo"},
        status="falha_execucao",
    )

    assert resolver_continuacao_aditiva(estado, texto="mais essa") == {}


def test_acao_nova_sem_politica_nao_esconde_continuacao_aditiva_compativel():
    estado = registrar_evento_continuidade(
        estado_mental_inicial(),
        evento="acao",
        intent="PLAYLIST_ADD",
        alvo="sendo sendo",
        params={"nome_playlist": "sendo sendo"},
        status="playlist_musica_adicionada",
    )
    estado = registrar_evento_continuidade(
        estado,
        evento="acao",
        intent="IOT_CONTROL",
        alvo="lampada_quarto",
        params={"acao": "ligar", "alvo": "lampada_quarto"},
        status="ligado",
    )

    assert resolver_continuacao_aditiva(estado, texto="essa também") == {
        "intent": "PLAYLIST_ADD",
        "params": {
            "nome_playlist": "sendo sendo",
            "referencia_contextual": True,
        },
    }


def test_resultado_da_caixa_nao_cria_segunda_pendencia_paralela():
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "INBOX_DELETE",
            "params": {"nota_id": "abc123", "alvo": "testar a caixa"},
        },
        "apaga essa nota",
        False,
        origem="caixa_entrada_pessoal",
        status="aguardando_confirmacao",
    )

    assert estado["pendencia_atual"] == {}
    assert estado["continuidade_geral"]["dominio_ativo"] == "caixa_entrada"

    estado = registrar_resultado_execucao(
        estado,
        {"intent": "CANCEL_INBOX_ACTION", "params": {}},
        "não",
        True,
        origem="caixa_entrada_pessoal",
        status="cancelado",
    )
    assert estado["pendencia_atual"] == {}
