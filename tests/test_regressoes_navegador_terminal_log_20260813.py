from __future__ import annotations

from mente_laylay.autonomia.executor_navegador import (
    DependenciasExecutorNavegador,
    executar_intencao_navegador,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.integracao.ambiente_navegacao import AmbienteNavegacaoRuntime
from mente_laylay.integracao.chrome_comandos import validar_e_enviar_comando
from tests.fakes_navegador import NavegadorLeituraFake, NavegadorOperacoesFake


def _contexto_deterministico(estado: dict | None = None) -> dict:
    return {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "texto_conversa_casual_sem_acao": lambda _texto: False,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "limpar_nome_playlist": lambda texto: str(texto).strip(),
        "extrair_nome_playlist": lambda _texto: "",
        "detectar_playlist_nome_direto": lambda _texto: "",
        "normalizar_query_musical": lambda texto: str(texto).strip(),
        "extrair_intencao_abrir_app": lambda _texto: None,
        "sites_diretos": {},
        "apps_map": {},
        "mente_integrada_estado": dict(estado or {}),
    }


def _dependencias(eventos: list[tuple], *, abrir=lambda *_a, **_k: True):
    return DependenciasExecutorNavegador(
        marcar_resultado=lambda status, **kwargs: eventos.append(
            ("resultado", status, kwargs)
        ),
        falar_por_status=lambda status, fallback, **kwargs: eventos.append(
            ("fala_status", status, fallback, kwargs)
        ),
        abrir_url_com_validacao=abrir,
        alvo_preciso_para_aba=lambda alvo: alvo,
        esperar_aba_fechar=lambda *_args: True,
        esperar_programa_fechar=lambda _alvo: True,
        executar_recursivo=lambda *_args: True,
    )


def test_terminal_log_pesquisa_web_publica_resultado_confirmado() -> None:
    comando = detectar_intencao_deterministica_mente(
        "Pesquisa por documentação do Python.",
        _contexto_deterministico(),
    )
    assert comando == {
        "intent": "SEARCH",
        "params": {"query": "documentação do python", "engine": "google"},
    }

    eventos: list[tuple] = []
    aberturas: list[tuple] = []
    despacho = executar_intencao_navegador(
        "SEARCH",
        comando["params"],
        "Pesquisa por documentação do Python.",
        "pc_a",
        {},
        _dependencias(
            eventos,
            abrir=lambda url, **kwargs: aberturas.append((url, kwargs)) or True,
        ),
    )

    assert despacho.retorno is True
    assert aberturas == [(
        "https://www.google.com/search?q=documenta%C3%A7%C3%A3o%20do%20python",
        {"alvo": "documentação do python", "auto_click": False},
    )]
    assert eventos[0] == (
        "resultado",
        "busca_aberta",
        {
            "executou": True,
            "confirmado": True,
            "detalhe": "a página de resultados foi relida no navegador",
        },
    )


def test_terminal_log_abre_primeiro_resultado_somente_da_busca_confirmada() -> None:
    estado = {
        "ultima_acao_intent": "SEARCH",
        "ultima_acao_status": "busca_aberta",
        "ultima_acao_confirmada": True,
        "ultima_acao_params": {"query": "documentação do Python"},
    }
    comando = detectar_intencao_deterministica_mente(
        "Abre o primeiro resultado.",
        _contexto_deterministico(estado),
    )
    assert comando == {
        "intent": "SEARCH",
        "params": {
            "query": "documentação do Python",
            "abrir_resultado": 1,
            "origem": "continuacao_resultado_web",
        },
    }

    navegador = NavegadorOperacoesFake()
    eventos: list[tuple] = []
    despacho = executar_intencao_navegador(
        "SEARCH",
        comando["params"],
        "Abre o primeiro resultado.",
        "pc_a",
        {"_registro_navegador_operacoes_runtime": navegador},
        _dependencias(eventos),
    )
    assert despacho.retorno is True
    assert navegador.chamadas == [(
        "click_first_result", {"query": "documentação do Python"},
    )]
    assert eventos[0][0:2] == ("resultado", "resultado_web_aberto")
    assert eventos[0][2]["confirmado"] is True

    sem_evidencia = {**estado, "ultima_acao_confirmada": False}
    assert detectar_intencao_deterministica_mente(
        "Abre o primeiro resultado.",
        _contexto_deterministico(sem_evidencia),
    ) is None


def test_terminal_log_lista_somente_abas_observadas_sem_llm() -> None:
    comando = detectar_intencao_deterministica_mente(
        "Quais abas estão abertas?",
        _contexto_deterministico(),
    )
    assert comando == {"intent": "LIST_TABS", "params": {}}

    falas: list[str] = []
    chamadas_llm: list[object] = []
    eventos: list[tuple] = []
    leitura = NavegadorLeituraFake(abas=[
        {
            "id": 11,
            "title": "Documentação do Python",
            "url": "https://docs.python.org/3/",
            "active": True,
        },
        {
            "id": 12,
            "title": "Prime Video",
            "url": "https://www.primevideo.com/",
        },
    ])
    despacho = executar_intencao_navegador(
        "LIST_TABS",
        {},
        "Quais abas estão abertas?",
        "pc_a",
        {
            "_registro_navegador_leitura_runtime": leitura,
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "enviar_mensagem": lambda *_args, **_kwargs: chamadas_llm.append(True),
        },
        _dependencias(eventos),
    )
    assert despacho.retorno is True
    assert chamadas_llm == []
    assert len(falas) == 1
    assert "Documentação do Python — docs.python.org" in falas[0]
    assert "Prime Video — primevideo.com" in falas[0]
    assert "chatgpt" not in falas[0].casefold()
    assert eventos[0][0:2] == ("resultado", "abas_listadas")


def test_terminal_log_fecha_essa_aba_pelo_id_observado_sem_ctrl_w() -> None:
    eventos: list[tuple] = []
    navegador = NavegadorOperacoesFake()
    leitura = NavegadorLeituraFake(
        aba={
            "tabId": 41,
            "title": "Documentação do Python",
            "url": "https://docs.python.org/3/",
        },
        abas=[{
            "id": 41,
            "title": "Documentação do Python",
            "url": "https://docs.python.org/3/",
            "active": True,
        }],
    )
    despacho = executar_intencao_navegador(
        "CLOSE_TAB",
        {},
        "Fecha essa aba.",
        "pc_a",
        {
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": navegador,
            # O contexto confirma que "essa" aponta para um site, mas não
            # pode transformar a aba atual num alvo fictício chamado "site".
            "_contexto_aponta_site_web": lambda _texto: True,
        },
        _dependencias(eventos),
    )
    assert despacho.retorno is True
    assert navegador.chamadas == [("close_tabs", {"ids": [41]})]
    assert eventos[0][2]["alvo_resolvido"] == "Documentação do Python"
    assert eventos[0][2]["params_resolvidos"]["tab_id"] == 41


def test_terminal_log_fecha_prime_video_sem_encerrar_opera() -> None:
    eventos: list[tuple] = []
    navegador = NavegadorOperacoesFake()
    leitura = NavegadorLeituraFake(abas=[
        {
            "id": 51,
            "title": "YouTube - Opera",
            "url": "https://www.youtube.com/",
            "active": True,
        },
        {
            "id": 52,
            "title": "Prime Video",
            "url": "https://www.primevideo.com/detail/0ABC",
        },
    ])
    despacho = executar_intencao_navegador(
        "CLOSE_TAB",
        {"alvo": "prime video"},
        "Fecha a aba do Prime Video.",
        "pc_a",
        {
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": navegador,
        },
        _dependencias(eventos),
    )
    assert despacho.retorno is True
    assert navegador.chamadas == [("close_tabs", {"ids": [52]})]
    assert all(acao not in {"close_native", "close_app"} for acao, _ in navegador.chamadas)
    assert eventos[0][2]["params_resolvidos"]["url_aba"].startswith(
        "https://www.primevideo.com/"
    )


def test_terminal_log_fecha_somente_abas_paradas_previamente_sugeridas() -> None:
    comando = detectar_intencao_deterministica_mente(
        "Fecha as abas paradas.",
        _contexto_deterministico(),
    )
    assert comando == {"intent": "CLOSE_IDLE_TABS", "params": {}}

    class PorteiroObservado:
        def __init__(self) -> None:
            self.abas_sugeridas = [
                "https://docs.python.org/3/",
                "https://www.primevideo.com/detail/0ABC",
            ]

        def fechar_sugeridas(self) -> bool:
            self.abas_sugeridas.clear()
            return True

    eventos: list[tuple] = []
    porteiro = PorteiroObservado()
    despacho = executar_intencao_navegador(
        comando["intent"],
        comando["params"],
        "Fecha as abas paradas.",
        "pc_a",
        {"_executar_fechar_abas_paradas": porteiro.fechar_sugeridas},
        _dependencias(eventos),
    )

    assert despacho.retorno is True
    assert eventos == [(
        "resultado",
        "abas_paradas_fechadas",
        {
            "executou": True,
            "confirmado": True,
            "alvo_resolvido": "abas paradas sugeridas",
            "params_resolvidos": {
                "abas_sugeridas": [
                    "https://docs.python.org/3/",
                    "https://www.primevideo.com/detail/0ABC",
                ],
                "quantidade": 2,
            },
            "detalhe": "o porteiro confirmou o fechamento de cada aba previamente sugerida",
        },
    )]


def test_falha_ao_fechar_aba_nunca_cai_em_fechamento_nativo() -> None:
    eventos: list[tuple] = []
    navegador = NavegadorOperacoesFake(resultado=False)
    leitura = NavegadorLeituraFake(abas=[{
        "id": 52,
        "title": "Prime Video",
        "url": "https://www.primevideo.com/",
    }])
    despacho = executar_intencao_navegador(
        "CLOSE_TAB",
        {"alvo": "prime video"},
        "Fecha a aba do Prime Video.",
        "pc_a",
        {
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": navegador,
        },
        _dependencias(eventos),
    )
    assert despacho.retorno is False
    assert navegador.chamadas == [("close_tabs", {"ids": [52]})]
    assert eventos[0][0:2] == ("resultado", "falha_execucao")


def test_falha_de_leitura_das_abas_nao_vira_lista_vazia_confirmada() -> None:
    class LeituraQueFalha:
        def conectado(self) -> bool:
            return True

        def listar_abas(self, timeout_s=5.0):
            raise OSError("ponte indisponível")

    falas: list[str] = []
    eventos: list[tuple] = []
    despacho = executar_intencao_navegador(
        "LIST_TABS",
        {},
        "Quais abas estão abertas?",
        "pc_a",
        {
            "_registro_navegador_leitura_runtime": LeituraQueFalha(),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "relatar_falha": lambda *_args, **_kwargs: None,
        },
        _dependencias(eventos),
    )

    assert despacho.retorno is False
    assert eventos == [(
        "resultado",
        "falha_execucao",
        {
            "executou": False,
            "confirmado": False,
            "detalhe": "a extensão falhou antes de devolver a lista de abas",
        },
    )]
    assert falas == [
        "Não consegui ler as abas agora; a extensão não devolveu uma lista verificável."
    ]


def test_ambiente_preserva_id_e_estado_observado_das_abas() -> None:
    class Solicitacoes:
        def solicitar_lista_abas(self, timeout_s=5.0):
            return [{
                "id": 7,
                "title": "Python",
                "url": "https://docs.python.org/",
                "active": True,
                "audible": False,
                "windowId": 2,
                "lastAccessed": 123.0,
            }]

    ambiente = AmbienteNavegacaoRuntime(servicos_iniciais={})
    ambiente._solicitacoes = Solicitacoes()
    abas = ambiente.listar_abas()
    assert abas == [{
        "titulo": "Python",
        "title": "Python",
        "url": "https://docs.python.org/",
        "id": 7,
        "tabId": 7,
        "active": True,
        "audible": False,
        "pinned": False,
        "discarded": False,
        "windowId": 2,
        "lastAccessed": 123.0,
    }]


def test_transporte_exige_confirmacao_real_para_resultado_e_fechamento() -> None:
    chamadas: list[tuple] = []
    contexto = {
        "ALLOWED_ACTIONS": {"click_first_result", "close_tabs"},
        "connected_extensions": {"extensao"},
        "ws_loop": object(),
        "broadcast_command": lambda *_args: None,
        "executar_chrome_confirmado": (
            lambda mensagem, timeout_s: chamadas.append((mensagem, timeout_s)) or True
        ),
    }
    assert validar_e_enviar_comando(
        contexto, "click_first_result", {"query": "documentação do Python"},
    ) is True
    assert validar_e_enviar_comando(
        contexto, "close_tabs", {"ids": [52]},
    ) is True
    assert chamadas == [
        ((
            {"action": "click_first_result", "query": "documentação do Python"}
        ), 6.0),
        (({"action": "close_tabs", "ids": [52]}), 4.0),
    ]
