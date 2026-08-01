from __future__ import annotations

from mente_laylay.autonomia.validacao_ambiente import ValidadorAmbiente
from tests.fakes_navegador import NavegadorLeituraFake, NavegadorOperacoesFake


def test_resolver_estado_ausente_ou_com_erro_retorna_retrato_vazio() -> None:
    assert ValidadorAmbiente({}).resolver_estado_alvo("chrome") == {}
    assert ValidadorAmbiente({
        "_resolver_alvo_ambiente": lambda _nome: (_ for _ in ()).throw(
            RuntimeError("indisponível")
        )
    }).resolver_estado_alvo("chrome") == {}


def test_esperar_programa_fechar_confirma_transicao_observada() -> None:
    leituras = iter([
        {"programa_aberto": True},
        {"programa_aberto": False},
    ])
    pausas: list[float] = []
    validador = ValidadorAmbiente(
        {"_resolver_alvo_ambiente": lambda _nome: next(leituras)},
        sleep_cb=pausas.append,
    )

    assert validador.esperar_programa_fechar("chrome", tentativas=3) is True
    assert pausas == [0.2]


def test_esperar_programa_fechar_nao_confirma_se_continua_aberto() -> None:
    validador = ValidadorAmbiente(
        {"_resolver_alvo_ambiente": lambda _nome: {"programa_aberto": True}},
        sleep_cb=lambda _segundos: None,
    )

    assert validador.esperar_programa_fechar(
        "chrome", tentativas=2, intervalo=0
    ) is False


def test_esperar_aba_atual_fechar_detecta_mudanca_de_url() -> None:
    validador = ValidadorAmbiente(
        {
            "_registro_navegador_leitura_runtime": NavegadorLeituraFake(aba={
                "url": "https://outro.example",
                "title": "Outra aba",
            })
        },
        sleep_cb=lambda _segundos: None,
    )

    assert validador.esperar_aba_fechar(
        "", {"url": "https://antes.example", "title": "Antes"}
    ) is True


def test_alvo_preciso_remove_www_e_preserva_nome_sem_url() -> None:
    validador = ValidadorAmbiente({
        "_montar_url_site_ou_busca": lambda alvo: (
            "https://www.youtube.com" if alvo == "youtube" else alvo
        )
    })

    assert validador.alvo_preciso_para_aba("youtube") == "youtube.com"
    assert validador.alvo_preciso_para_aba("calculadora") == "calculadora"


def test_correspondencia_de_url_aceita_url_host_ou_titulo() -> None:
    validador = ValidadorAmbiente({})

    assert validador.aba_corresponde_url(
        "youtube.com",
        "https://youtube.com/watch?v=1",
        {"url": "https://youtube.com/watch?v=1&t=2"},
    ) is True
    assert validador.aba_corresponde_url(
        "youtube", "", {"title": "YouTube - vídeo"}
    ) is True


def test_abrir_url_no_pc_b_envia_remoto_sem_validacao_local() -> None:
    enviados: list[dict] = []
    validador = ValidadorAmbiente(
        {"_enviar_pc_b": enviados.append}, destino="pc_b"
    )

    assert validador.abrir_url_com_validacao("https://example.com") is True
    assert enviados == [{"action": "open_url", "url": "https://example.com"}]


def test_abertura_local_repassa_foco_e_exige_confirmacao_observavel() -> None:
    aberturas: list[tuple] = []
    validador = ValidadorAmbiente(
        {
            "_registro_navegador_operacoes_runtime": NavegadorOperacoesFake(
                abrir_cb=lambda *args, **kwargs: (
                    aberturas.append((args, kwargs)) or True
                )
            ),
            "_registro_navegador_leitura_runtime": NavegadorLeituraFake(aba={
                "url": "https://example.com/pagina",
                "title": "Example",
            }),
        },
        texto_original="abre o site e traz para frente",
        sleep_cb=lambda _segundos: None,
    )

    assert validador.abrir_url_com_validacao(
        "https://example.com", alvo="example.com"
    ) is True
    assert aberturas == [(("https://example.com",), {
        "auto_click": False,
        "permitir_foco": True,
    })]
