import time

import pytest

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
    ContextoImediatoRuntime,
    referencia_contextual_imediata,
    resolver_comando_acao_geral_contextual,
)
from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.foco_contexto import atualizar_foco_vivo
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


def test_open_url_confirmado_fecha_ele_como_aba_mesmo_apos_fala_conversacional():
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "OPEN_URL",
            "params": {"alvo": "ifood"},
            "status": "url_aberta",
            "executou": True,
            "confirmado": True,
        },
        "abre o ifood",
    )
    # Reproduz o turno real: a confirmação falada foi registrada depois da
    # ação e, por ser uma fala sem intent, tornou ``conversa`` o domínio ativo.
    estado = atualizar_foco_vivo(
        estado,
        texto="abre o ifood",
        resposta="Ifood já está aberto e em foco.",
        normalizar_texto_cb=lambda valor: str(valor).casefold(),
    )
    assert estado["continuidade_geral"]["dominio_ativo"] == "conversa"

    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado,
        foco_vivo={},
        texto_atual="fecha ele",
        normalizar_texto=lambda valor: str(valor).casefold(),
    )
    comando = resolver_comando_acao_geral_contextual("fecha ele", referencia)

    assert referencia["tipo"] == "site"
    assert referencia["alvo"] == "ifood"
    assert referencia["origem_continuidade"] == "contrato_confirmado"
    assert comando == {"intent": "CLOSE_TAB", "params": {"alvo": "ifood"}}


def test_sequencia_real_open_url_ifood_fecha_ele_chega_ao_close_tab():
    mental = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "OPEN_URL",
            "params": {"alvo": "ifood"},
            "status": "url_aberta",
            "executou": True,
            "confirmado": True,
        },
        "abre o ifood",
    )
    mental = atualizar_foco_vivo(
        mental,
        texto="abre o ifood",
        resposta="Ifood já está aberto e em foco.",
        normalizar_texto_cb=normalizar_texto,
    )
    estado = EstadoCompartilhadoRuntime(mental=mental)
    contexto_imediato = ContextoImediatoRuntime(
        estado_runtime_getter=lambda: estado,
        servicos_iniciais={
            "_normalizar_texto_com_apelidos": normalizar_texto,
            "_alvo_corrigido_atual": lambda: "",
            "_registrar_alvo_corrigido": lambda _alvo: None,
            "falar_com_lipsync": lambda *_args: None,
            "_contexto_musical_ativo": lambda: False,
            "_estrutura_arquivo_recente": lambda _ttl: {},
            "_foco_vivo_atual": lambda **_kwargs: {},
            "enviar_mensagem": lambda *_args, **_kwargs: None,
        },
    )
    turno = classificar_modalidade_turno(
        "fecha ele", normalizar_texto=normalizar_texto,
    )

    resultado, rota = resolver_intencao(
        "fecha ele",
        "terminal",
        {
            "normalizar_texto": normalizar_texto,
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: True,
            "detectar_intencao_deterministica": lambda _texto: None,
            "resolver_comando_contextual_forcado": contexto_imediato.resolver,
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "tentar_intencao_ai_primeiro": lambda _texto: None,
            "registrar_arbitragem_turno": lambda *_args: None,
            "turno_atual": turno,
            "retrato_turno_atual": {},
            "continuidade_geral": dict(
                estado.mental.get("continuidade_geral") or {}
            ),
        },
    )

    assert resultado is not None
    assert resultado["intent"] == "CLOSE_TAB"
    assert resultado["params"]["alvo"] == "ifood"
    assert rota == "contexto-semantica"


def test_fecha_ele_preserva_distincao_entre_app_e_aba():
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "APP_OPEN",
            "params": {"nome_app": "steam"},
            "status": "app_iniciado_focado",
            "executou": True,
            "confirmado": True,
        },
        "abre a steam",
    )
    estado = atualizar_foco_vivo(
        estado,
        texto="abre a steam",
        resposta="Steam está aberta.",
        normalizar_texto_cb=lambda valor: str(valor).casefold(),
    )

    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado,
        foco_vivo={},
        texto_atual="fecha ele",
        normalizar_texto=lambda valor: str(valor).casefold(),
    )

    assert referencia["tipo"] == "app"
    assert resolver_comando_acao_geral_contextual("fecha ele", referencia) == {
        "intent": "CLOSE_APP",
        "params": {"nome_app": "steam"},
    }


def test_acao_web_nao_confirmada_nao_ganha_salienca_de_contrato():
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "OPEN_URL",
            "params": {"alvo": "ifood"},
            "status": "falha_execucao",
            "executou": False,
            "confirmado": False,
        },
        "abre o ifood",
    )
    estado = atualizar_foco_vivo(
        estado,
        texto="abre o ifood",
        resposta="Não consegui abrir.",
        normalizar_texto_cb=lambda valor: str(valor).casefold(),
    )

    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado,
        foco_vivo={},
        texto_atual="fecha ele",
        normalizar_texto=lambda valor: str(valor).casefold(),
    )

    assert referencia.get("origem_continuidade") != "contrato_confirmado"


def test_acao_web_apenas_enviada_nao_ganha_salienca_de_contrato():
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "OPEN_URL",
            "params": {"alvo": "ifood"},
            "status": "url_enviada_sem_confirmacao",
            "executou": True,
            "confirmado": None,
        },
        "abre o ifood",
    )
    estado = atualizar_foco_vivo(
        estado,
        texto="abre o ifood",
        resposta="Enviei a abertura, mas não consegui confirmar.",
        normalizar_texto_cb=lambda valor: str(valor).casefold(),
    )

    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado,
        foco_vivo={},
        texto_atual="fecha ele",
        normalizar_texto=lambda valor: str(valor).casefold(),
    )

    assert referencia.get("origem_continuidade") != "contrato_confirmado"


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


def test_essa_tambem_recupera_destino_do_ultimo_resultado_confirmado():
    """Reproduz o runtime quando a projecao derivada chega incompleta."""
    agora = time.time()
    estado = estado_mental_inicial()
    estado.update({
        "continuidade_geral": {
            "dominios": {
                "musica": {
                    "intent": "PLAYLIST_ADD",
                    "params": {},
                    "status": "playlist_musica_adicionada",
                    "ativa": True,
                    "ts": agora,
                    "expira_em": agora + 900.0,
                },
            },
        },
        "ultima_acao_intent": "PLAYLIST_ADD",
        "ultima_acao_params": {},
        "ultima_acao_alvo": "vmz",
        "ultima_acao_status": "playlist_musica_adicionada",
        "ultima_acao_ok": True,
        "ultima_acao_confirmada": True,
        "ultima_acao_ts": agora,
        "ultima_acao_contrato": {
            "intent": "PLAYLIST_ADD",
            "alvo": "vmz",
            "status": "playlist_musica_adicionada",
            "dominio": "musica",
            "executou": True,
            "confirmado": True,
        },
    })

    assert resolver_continuacao_aditiva(estado, texto="essa tambem") == {
        "intent": "PLAYLIST_ADD",
        "params": {
            "nome_playlist": "vmz",
            "referencia_contextual": True,
        },
    }


@pytest.mark.parametrize(
    ("intent", "executou", "confirmado", "idade_s"),
    [
        ("PLAYLIST_ADD", False, False, 0.0),
        ("PLAYLIST_ADD", True, False, 0.0),
        ("PLAYLIST_ADD", True, True, 301.0),
        ("DELETE_ITEM", True, True, 0.0),
    ],
)
def test_fallback_atomico_nao_promove_resultado_inseguro_ou_expirado(
    intent: str,
    executou: bool,
    confirmado: bool,
    idade_s: float,
):
    agora = time.time()
    estado = estado_mental_inicial()
    estado.update({
        "continuidade_geral": {},
        "ultima_acao_intent": intent,
        "ultima_acao_params": {},
        "ultima_acao_alvo": "vmz",
        "ultima_acao_status": (
            "playlist_musica_adicionada" if executou else "falha_execucao"
        ),
        "ultima_acao_ok": executou,
        "ultima_acao_confirmada": confirmado,
        "ultima_acao_ts": agora - idade_s,
        "ultima_acao_contrato": {
            "intent": intent,
            "alvo": "vmz",
            "status": (
                "playlist_musica_adicionada" if executou else "falha_execucao"
            ),
            "executou": executou,
            "confirmado": confirmado,
        },
    })

    assert resolver_continuacao_aditiva(
        estado,
        texto="essa também",
        ttl_s=300.0,
    ) == {}


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
