from __future__ import annotations

from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.autonomia.contexto_resposta_ia import criar_contexto_prompt_runtime


def test_mapa_cobre_catalogo_canonico_sem_autorizar_execucao() -> None:
    mapa = MapaHabilidadesRuntime()

    snapshot = mapa.snapshot()
    diagnostico = mapa.diagnostico()

    assert set(snapshot["capacidades"]) == set(intents_registradas())
    assert diagnostico["catalogadas"] == len(intents_registradas())
    assert diagnostico["autoriza_execucao"] is False
    assert mapa.consultar("IOT_CONTROL")["dominio"] == "iot"
    assert mapa.consultar("INTENT_INEXISTENTE")["motivo"] == "capacidade_nao_registrada"


def test_prompt_seleciona_so_habilidades_relevantes_ao_turno() -> None:
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt("coloca uma música e pausa depois")

    assert "- musica [disponivel]" in contexto
    assert "- arquivos" not in contexto
    assert "não autoriza ações" in contexto


def test_mapa_explica_curadoria_propria_sem_autorizar_acao() -> None:
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt("quais playlists você criou?")
    resposta = mapa.responder_pergunta_capacidade(
        "você consegue criar suas próprias playlists?"
    )

    assert "curadorias próprias" in contexto
    assert "histórico musical confirmado" in resposta
    assert "não invento músicas" in resposta
    assert mapa.responder_pergunta_capacidade("toque sua playlist") == ""


def test_pergunta_sobre_capacidades_mostra_todos_os_dominios() -> None:
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt("Lay, o que você consegue fazer?")

    for dominio in ("musica", "sistema", "navegador", "visao", "agenda", "arquivos", "email", "iot", "conversa"):
        assert f"- {dominio} [" in contexto


def test_llm_conhece_navegador_tipado_sem_promessa_de_execucao_arbitraria() -> None:
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt(
        "você consegue ver minhas abas e interagir com uma página?"
    )
    resposta = mapa.responder_pergunta_capacidade(
        "Lay, você consegue consultar e controlar o navegador?"
    )

    assert "- navegador [disponivel]" in contexto
    assert "consultar a aba ativa" in contexto.casefold()
    assert "comandos arbitrários" in contexto.casefold()
    assert "leitura do navegador não autoriza uma ação" in resposta.casefold()
    assert "comando arbitrário" in resposta.casefold()


def test_mapa_conhece_resumo_sem_transformar_pergunta_em_execucao() -> None:
    mapa = MapaHabilidadesRuntime()

    capacidade = mapa.consultar("RESUMIR_PAGINA")
    resposta = mapa.responder_pergunta_capacidade(
        "Você consegue resumir a página atual?"
    )

    assert capacidade["disponivel"] is True
    assert capacidade["proprietario"].endswith("comandos_imediatos")
    assert "resumir a página atual" in resposta.casefold()
    assert mapa.responder_pergunta_capacidade("resume a página atual") == ""


def test_llm_conhece_conversa_tipificada_sem_confundir_com_autorizacao() -> None:
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt("Lay, você consegue conversar e explicar coisas?")
    resposta = mapa.responder_pergunta_capacidade(
        "Lay, você consegue conversar e explicar coisas?"
    )

    assert "- conversa [" in contexto
    assert "contexto da conversa separado das lembranças duráveis" in resposta
    assert "não salva tudo" in resposta
    assert "nem autoriza uma ação" in resposta
    assert "cliente de rede" not in resposta
    assert "executor" not in resposta


def test_indisponibilidade_temporaria_expira_e_sucesso_recupera() -> None:
    agora = [100.0]
    mapa = MapaHabilidadesRuntime(
        relogio=lambda: agora[0], ttl_indisponivel_s=10, ttl_observacao_s=30,
    )

    mapa.registrar_resultado(
        {"intent": "IOT_CONTROL", "status": "indisponivel", "executou": False}
    )
    assert mapa.snapshot()["capacidades"]["IOT_CONTROL"]["disponivel"] is False

    mapa.registrar_resultado(
        {"intent": "IOT_CONTROL", "status": "ligado", "confirmado": True}
    )
    assert mapa.snapshot()["capacidades"]["IOT_CONTROL"]["disponivel"] is True

    mapa.registrar_resultado(
        {"intent": "IOT_CONTROL", "status": "indisponivel", "executou": False}
    )
    agora[0] = 111.0
    assert mapa.snapshot()["capacidades"]["IOT_CONTROL"]["disponivel"] is True


def test_falha_de_um_alvo_nao_desliga_habilidade_inteira() -> None:
    mapa = MapaHabilidadesRuntime()

    mapa.registrar_resultado(
        {"intent": "APP_OPEN", "status": "nao_encontrado", "executou": False}
    )
    registro = mapa.snapshot()["capacidades"]["APP_OPEN"]

    assert registro["disponivel"] is True
    assert registro["estado"] == "degradado"


def test_saude_do_modulo_alias_bloqueia_dominio_correspondente() -> None:
    mapa = MapaHabilidadesRuntime(
        saude_getter=lambda: {"gmail": {"status": "indisponivel"}}
    )

    snapshot = mapa.snapshot()

    assert snapshot["capacidades"]["EMAIL_READ"]["disponivel"] is False
    assert snapshot["dominios"]["email"]["estado"] == "indisponivel"


def test_contexto_da_llm_recebe_mapa_compacto_e_contextual() -> None:
    mapa = MapaHabilidadesRuntime()
    runtime = criar_contexto_prompt_runtime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _texto: "",
        formatar_playlists=lambda: "",
        get_status_humor_prompt=lambda: "calma",
        base_system_prompt="PROMPT BASE {status_humor}",
        estado_getter=lambda: {"messages": [], "turno_atual": {}},
        mapa_habilidades_prompt=mapa.contexto_para_prompt,
    )

    mensagens, prompt = runtime.preparar("apaga essa pasta")

    assert mensagens[0]["content"] == prompt
    assert "HABILIDADES REAIS RELEVANTES" in prompt
    assert "- arquivos [disponivel]" in prompt
    assert "- musica" not in prompt
    assert len(mapa.contexto_para_prompt("apaga essa pasta")) < 900


def test_mapa_diferencia_consulta_real_de_pergunta_sobre_capacidade() -> None:
    mapa = MapaHabilidadesRuntime()

    assert mapa.parece_consulta_operacional("quais emails novos eu tenho?") is True
    assert mapa.parece_consulta_operacional("como está a lâmpada do quarto?") is True
    assert mapa.parece_consulta_operacional("encontra o código que controla a lâmpada") is True
    assert mapa.parece_consulta_operacional("você consegue ler meus emails?") is False
    assert mapa.parece_consulta_operacional("se eu pedir, você apaga uma pasta?") is False
    assert mapa.parece_consulta_operacional("não procura esse arquivo") is False


def test_pergunta_de_capacidade_recebe_resposta_real_sem_executar() -> None:
    mapa = MapaHabilidadesRuntime()

    assert "lixeira" in mapa.responder_pergunta_capacidade(
        "você consegue apagar uma pasta?"
    ).casefold()
    assert "fechar" in mapa.responder_pergunta_capacidade(
        "se eu pedir para fechar o navegador, você consegue?"
    ).casefold()
    assert mapa.responder_pergunta_capacidade("fecha o navegador") == ""


def test_llm_recebe_caixa_de_entrada_como_habilidade_real() -> None:
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt("anota essa ideia na minha caixa de entrada")
    resposta = mapa.responder_pergunta_capacidade(
        "Lay, você consegue guardar minhas ideias e notas?"
    )

    assert "- caixa_entrada [disponivel]" in contexto
    assert "guardar, classificar" in contexto
    assert "caixa de entrada" in resposta.casefold()
    assert "resumir uma discussão" in resposta.casefold()
    assert "transformar uma nota em lembrete" in resposta.casefold()


def test_llm_sabe_que_avatar_visual_existe_sem_prometer_edicao() -> None:
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt("quais skins combinam com seu avatar?")
    resposta = mapa.responder_pergunta_capacidade(
        "Lay, você consegue pensar em skins para o seu avatar?"
    )

    assert "- avatar [disponivel]" in contexto
    assert "avatar visual" in contexto.casefold()
    assert "tenho um avatar visual" in resposta.casefold()
    assert "executor confirmar" in resposta.casefold()


def test_llm_conhece_investigacao_interna_de_erro_copiado() -> None:
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt(
        "você consegue detectar e investigar uma mensagem de erro copiada?"
    )
    resposta = mapa.responder_pergunta_capacidade(
        "Lay, você consegue investigar um erro copiado?"
    )

    assert "- area_transferencia [disponivel]" in contexto
    assert "CLIPBOARD_INVESTIGATE" in mapa.snapshot()["dominios"]["area_transferencia"]["intents"]
    assert "pesquisar internamente" in contexto.casefold()
    assert "sem abrir uma aba" in resposta.casefold()
    assert "não guardo o texto automaticamente" in resposta.casefold()


def test_llm_conhece_analise_cooperativa_de_item_no_jogo() -> None:
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt(
        "essa bota é boa para a minha build no jogo?"
    )
    resposta = mapa.responder_pergunta_capacidade(
        "Lay, você consegue analisar um item do jogo para a minha build?"
    )

    assert "- visao [disponivel]" in contexto
    assert "pesquisar evidências confiáveis" in contexto.casefold()
    assert "quadro atual" in resposta.casefold()
    assert "build e o inventário" in resposta.casefold()
    assert "captura é transitória" in resposta.casefold()
    assert "não fica persistida" in resposta.casefold()
    assert "não autoriza uma nova análise" in resposta.casefold()
    assert "mouse sobre ele" in resposta.casefold()
    assert "em vez de inventar" in resposta.casefold()
