from __future__ import annotations

from types import SimpleNamespace

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_navegador import (
    DependenciasExecutorNavegador,
    executar_intencao_navegador,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from tests.fakes_navegador import NavegadorOperacoesFake


def _dependencias(
    eventos: list[tuple],
    *,
    abrir=lambda *_args, **_kwargs: True,
    executar=lambda *_args, **_kwargs: True,
) -> DependenciasExecutorNavegador:
    return DependenciasExecutorNavegador(
        marcar_resultado=lambda status, **kwargs: eventos.append(("resultado", status, kwargs)),
        falar_por_status=lambda status, fallback, **kwargs: eventos.append(
            ("fala_status", status, fallback, kwargs)
        ),
        abrir_url_com_validacao=abrir,
        alvo_preciso_para_aba=lambda alvo: f"host:{alvo}",
        esperar_aba_fechar=lambda alvo, *_args: bool(alvo or alvo == ""),
        esperar_programa_fechar=lambda _alvo: True,
        executar_recursivo=executar,
    )


def test_executor_navegador_nao_interfere_em_outro_dominio() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_navegador(
        "VOLUME", {}, "volume em 20", "pc_a", {}, _dependencias(eventos)
    )

    assert despacho == ResultadoDespacho.nao_tratado()
    assert eventos == []


def test_open_url_preserva_normalizacao_validacao_e_status() -> None:
    eventos: list[tuple] = []
    aberturas: list[tuple] = []

    despacho = executar_intencao_navegador(
        "OPEN_URL",
        {"site": "YouTube"},
        "abre o youtube",
        "pc_a",
        {
            "_contexto_aponta_site_web": lambda _alvo: True,
            "_normalizar_texto_com_apelidos": lambda alvo: alvo.casefold(),
            "_montar_url_site_ou_busca": lambda alvo: f"https://{alvo}.com",
        },
        _dependencias(
            eventos,
            abrir=lambda url, **kwargs: aberturas.append((url, kwargs)) or True,
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert aberturas == [(
        "https://youtube.com",
        {"alvo": "youtube", "auto_click": False},
    )]
    assert eventos[0] == ("resultado", "url_aberta", {"executou": True})
    assert eventos[1][0:2] == ("fala_status", "url_aberta")


def test_open_url_completa_preserva_query_e_nao_passa_por_normalizador() -> None:
    eventos: list[tuple] = []
    aberturas: list[tuple] = []
    chamadas_linguisticas: list[tuple[str, str]] = []
    url = (
        "https://www.youtube.com/watch?v=gndkfhyh5mo"
        "&list=RDgndkfhyh5mo&start_radio=1"
    )

    despacho = executar_intencao_navegador(
        "OPEN_URL",
        {"url": url},
        "abre o link que eu copiei",
        "pc_a",
        {
            "_contexto_aponta_site_web": lambda alvo: (
                chamadas_linguisticas.append(("contexto", alvo)) or True
            ),
            "_normalizar_texto_com_apelidos": lambda alvo: (
                chamadas_linguisticas.append(("normalizar", alvo)) or "url-destruida"
            ),
            "_montar_url_site_ou_busca": lambda alvo: (
                chamadas_linguisticas.append(("montar", alvo)) or "https://url-destruida"
            ),
        },
        _dependencias(
            eventos,
            abrir=lambda endereco, **kwargs: aberturas.append((endereco, kwargs)) or True,
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert chamadas_linguisticas == []
    assert aberturas == [(url, {"alvo": url, "auto_click": False})]
    assert eventos[0] == ("resultado", "url_aberta", {"executou": True})


def test_close_idle_tabs_preserva_retorno_falso_quando_falha() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_navegador(
        "CLOSE_IDLE_TABS",
        {},
        "fecha abas paradas",
        "pc_a",
        {"_executar_fechar_abas_paradas": lambda: False},
        _dependencias(eventos),
    )

    assert despacho.tratado is True
    assert despacho.retorno is False
    assert eventos == [(
        "resultado", "falha_execucao",
        {
            "executou": False,
            "confirmado": False,
            "alvo_resolvido": "abas paradas sugeridas",
            "params_resolvidos": {"abas_sugeridas": [], "quantidade": 0},
            "detalhe": "ao menos uma aba sugerida não devolveu confirmação de fechamento",
        },
    )]


def test_voltar_aba_anterior_escolhe_a_mais_recente_e_confirma_foco() -> None:
    eventos: list[tuple] = []

    class Leitura:
        ativa = 9
        abas = [
            {"id": 7, "title": "Python", "url": "https://python.org", "windowId": 1, "lastAccessed": 20},
            {"id": 8, "title": "Outra", "url": "https://example.com", "windowId": 1, "lastAccessed": 10},
            {"id": 9, "title": "Google", "url": "https://google.com", "windowId": 1, "lastAccessed": 30, "active": True},
        ]

        def conectado(self):
            return True

        def aba_ativa(self, timeout_s=4.0):
            return {"tabId": self.ativa}

        def listar_abas(self, timeout_s=5.0):
            return [dict(aba) for aba in self.abas]

    leitura = Leitura()

    class Operacoes:
        def focar_aba(self, tab_id):
            leitura.ativa = tab_id
            return True

    despacho = executar_intencao_navegador(
        "SWITCH_PREVIOUS_TAB",
        {},
        "volta para a aba anterior",
        "pc_a",
        {
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": Operacoes(),
            "falar_com_lipsync": lambda *_args: None,
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert leitura.ativa == 7
    assert eventos == [(
        "resultado",
        "aba_anterior_focada",
        {
            "executou": True,
            "confirmado": True,
            "alvo_resolvido": "Python — python.org",
            "detalhe": "a extensão releu a aba como ativa",
        },
    )]


def test_voltar_aba_anterior_aguarda_evento_de_foco_sem_repetir_comando(monkeypatch) -> None:
    eventos: list[tuple] = []
    leituras = iter((9, 9, 7))
    focos: list[int] = []
    monkeypatch.setattr(
        "mente_laylay.autonomia.executor_navegador.time.sleep",
        lambda _segundos: None,
    )

    class Leitura:
        def conectado(self):
            return True

        def aba_ativa(self, timeout_s=4.0):
            return {"tabId": next(leituras)}

        def listar_abas(self, timeout_s=5.0):
            return [
                {"id": 7, "title": "Python", "url": "https://python.org", "windowId": 1, "lastAccessed": 20},
                {"id": 9, "title": "Google", "url": "https://google.com", "windowId": 1, "lastAccessed": 30, "active": True},
            ]

    class Operacoes:
        def focar_aba(self, tab_id):
            focos.append(tab_id)
            return True

    despacho = executar_intencao_navegador(
        "SWITCH_PREVIOUS_TAB", {}, "volta para a aba anterior", "pc_a",
        {
            "_registro_navegador_leitura_runtime": Leitura(),
            "_registro_navegador_operacoes_runtime": Operacoes(),
            "falar_com_lipsync": lambda *_args: None,
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert focos == [7]
    assert eventos[-1][2]["confirmado"] is True


def test_close_tab_no_pc_b_preserva_alvo_preciso() -> None:
    eventos: list[tuple] = []
    remotos: list[dict] = []

    despacho = executar_intencao_navegador(
        "CLOSE_TAB",
        {"site": "youtube"},
        "fecha a aba do youtube",
        "pc_b",
        {
            "_enviar_pc_b": remotos.append,
            "_eh_alvo_site_web": lambda _alvo: True,
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert remotos == [{"action": "close_specific_tab", "target": "host:youtube"}]
    assert eventos[0] == (
        "resultado",
        "fechamento_aba_solicitado",
        {
            "executou": True,
            "confirmado": None,
            "alvo_resolvido": "youtube",
            "params_resolvidos": {},
            "detalhe": (
                "o cliente remoto recebeu a solicitação, mas não devolveu "
                "o estado final da aba"
            ),
        },
    )


def test_close_tab_nao_escala_para_fechar_programa() -> None:
    eventos: list[tuple] = []
    programas_fechados: list[str] = []
    navegador = NavegadorOperacoesFake()

    despacho = executar_intencao_navegador(
        "CLOSE_TAB",
        {"alvo": "prime video"},
        "fecha a aba do Prime Video",
        "pc_a",
        {
            "_registro_navegador_leitura_runtime": SimpleNamespace(
                aba_ativa=lambda: {
                    "title": "Prime Video",
                    "url": "https://www.primevideo.com/",
                },
            ),
            "_resolver_alvo_ambiente": lambda _alvo: {"programa_aberto": True},
            "_eh_alvo_site_web": lambda _alvo: False,
            "fechar_programa": programas_fechados.append,
            "_registro_navegador_operacoes_runtime": navegador,
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert programas_fechados == []
    assert navegador.chamadas == [(
        "close_specific_tab", {"target": "host:prime video"},
    )]
    assert eventos[0] == (
        "resultado",
        "aba_fechada",
        {
            "executou": True,
            "confirmado": True,
            "alvo_resolvido": "prime video",
            "params_resolvidos": {},
            "detalhe": "a extensão confirmou a remoção da aba observada",
        },
    )


def test_search_de_clima_continua_redirecionando_sem_abrir_google() -> None:
    eventos: list[tuple] = []
    recursivos: list[tuple] = []

    despacho = executar_intencao_navegador(
        "SEARCH",
        {"query": "tempo em Boituva"},
        "como está o tempo em Boituva",
        "pc_a",
        {},
        _dependencias(
            eventos,
            executar=lambda resultado, texto, _ctx: recursivos.append((resultado, texto)) or True,
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert recursivos == [(
        {"intent": "WEATHER", "params": {"local": "tempo em Boituva"}},
        "como está o tempo em Boituva",
    )]
    assert eventos == []


def test_search_conversacional_continua_usando_ia_sem_abrir_navegador() -> None:
    eventos: list[tuple] = []
    falas: list[str] = []
    mensagens: list[dict] = []
    chrome: list[tuple] = []

    despacho = executar_intencao_navegador(
        "SEARCH",
        {"query": "como você está"},
        "como você está",
        "pc_a",
        {
            "messages": mensagens,
            "enviar_mensagem": lambda _messages: "Estou bem e curiosa.",
            "_remover_prefixo_exec": lambda texto: texto,
            "limpar_resposta": lambda texto: texto,
            "enviar_comando_chrome": lambda *args: chrome.append(args),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert chrome == []
    assert falas == ["Estou bem e curiosa."]
    assert mensagens == [
        {"role": "user", "content": "como você está"},
        {"role": "assistant", "content": "Estou bem e curiosa."},
    ]


def test_roteador_principal_delega_close_idle_tabs_ao_executor_web() -> None:
    resultados = []

    retorno = executar_intencao(
        {"intent": "CLOSE_IDLE_TABS", "params": {}},
        "fecha as abas paradas",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_executar_fechar_abas_paradas": lambda: True,
            "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: resultados.append(
                contrato
            ),
        },
    )

    assert retorno is True
    assert resultados and resultados[0].status == "abas_paradas_fechadas"
    assert resultados[0].confirmado is True
