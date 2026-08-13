from __future__ import annotations

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_janelas import (
    DependenciasExecutorJanelas,
    executar_intencao_janelas,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.percepcao.janelas_sistema import maximizar_janela
from tests.fakes_navegador import NavegadorOperacoesFake


def _dependencias(
    eventos: list[tuple],
    *,
    alvo_preciso=lambda alvo: f"host:{alvo}",
    esperar_aba=lambda *_args: True,
    esperar_programa=lambda _alvo: True,
    executar=lambda *_args: True,
) -> DependenciasExecutorJanelas:
    return DependenciasExecutorJanelas(
        marcar_resultado=lambda status, **kwargs: eventos.append(("resultado", status, kwargs)),
        falar_por_status=lambda status, fallback, **kwargs: eventos.append(
            ("fala_status", status, fallback, kwargs)
        ),
        falar_resultado_janela=lambda nome, status: eventos.append(
            ("fala_janela", nome, status)
        ),
        alvo_preciso_para_aba=alvo_preciso,
        esperar_aba_fechar=esperar_aba,
        esperar_programa_fechar=esperar_programa,
        executar_recursivo=executar,
    )


def test_contrato_resultado_despacho_distingue_intencao_nao_tratada() -> None:
    nao_tratado = ResultadoDespacho.nao_tratado()
    tratado = ResultadoDespacho.concluido()

    assert nao_tratado.tratado is False
    assert nao_tratado.retorno is False
    assert tratado.tratado is True
    assert tratado.retorno is True


def test_falha_real_de_janela_chega_ao_diagnostico_central() -> None:
    falhas = []

    class Janela:
        title = "Discord"
        isMinimized = False

        @staticmethod
        def activate():
            raise RuntimeError("Windows recusou foco")

    class Gw:
        @staticmethod
        def getAllWindows():
            return [Janela()]

    assert maximizar_janela(
        Gw(), None, "discord", psutil_mod=None,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
    ) is False
    assert falhas[0][0] == ("janelas_sistema", "maximizacao_janela")
    assert isinstance(falhas[0][1]["erro"], RuntimeError)


def test_executor_janelas_nao_interfere_em_outro_dominio() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_janelas(
        "VOLUME",
        {"acao": "set", "nivel_volume": 30},
        "pc_a",
        {},
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.nao_tratado()
    assert eventos == []


def test_organizar_desktop_preserva_parametros_e_confirma_layout_observado() -> None:
    eventos: list[tuple] = []
    organizacoes: list[tuple[str, str]] = []
    falas: list[tuple] = []

    despacho = executar_intencao_janelas(
        "ORGANIZAR_DESKTOP",
        {"esquerda": "vscode", "direita": "opera"},
        "pc_a",
        {
            "organizar_janelas_robusto": lambda esquerda, direita: (
                organizacoes.append((esquerda, direita))
                or {
                    "ok": True,
                    "executou": True,
                    "confirmado": True,
                    "status": "layout_confirmado",
                    "nome_esquerda": "vscode",
                    "nome_direita": "opera",
                }
            ),
            "falar_com_lipsync": lambda *args: falas.append(args),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert organizacoes == [("vscode", "opera")]
    assert eventos == [(
        "resultado", "layout_confirmado",
        {"executou": True, "confirmado": True},
    )]
    assert falas == [(
        "Pronto: VS Code ficou à esquerda e Opera, à direita.",
        "feliz",
        1,
    )]


def test_organizar_desktop_move_so_o_lado_pedido() -> None:
    eventos: list[tuple] = []
    organizacoes: list[tuple[str, str]] = []
    falas: list[tuple] = []

    despacho = executar_intencao_janelas(
        "ORGANIZAR_DESKTOP",
        {"left": "steam", "modo": "posicionar"},
        "pc_a",
        {
            "organizar_janelas_robusto": lambda esquerda, direita: (
                organizacoes.append((esquerda, direita))
                or {
                    "ok": True, "executou": True, "confirmado": True,
                    "status": "layout_confirmado", "nome_esquerda": "steam",
                    "nome_direita": "",
                }
            ),
            "falar_com_lipsync": lambda *args: falas.append(args),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert organizacoes == [("steam", "")]
    assert eventos == [(
        "resultado", "layout_confirmado",
        {"executou": True, "confirmado": True},
    )]
    assert falas == [(
        "Pronto, deixei Steam à esquerda.",
        "feliz", 1,
    )]


def test_organizacao_automatica_explica_a_prioridade_observada() -> None:
    eventos: list[tuple] = []
    falas: list[tuple] = []
    prioridades = [
        {"titulo": "VS Code", "motivos": ["janela em foco"]},
        {"titulo": "Chrome", "motivos": ["reproduzindo áudio", "uso recente"]},
    ]

    despacho = executar_intencao_janelas(
        "ORGANIZAR_DESKTOP",
        {"modo": "automatico"},
        "pc_a",
        {
            "organizar_janelas_robusto": lambda *_args: {
                "ok": True,
                "executou": True,
                "confirmado": True,
                "status": "layout_confirmado",
                "nome_esquerda": "VS Code",
                "nome_direita": "Chrome",
                "prioridades": prioridades,
            },
            "falar_com_lipsync": lambda *args: falas.append(args),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert eventos == [(
        "resultado",
        "layout_confirmado",
        {
            "executou": True,
            "confirmado": True,
            "detalhe": (
                "prioridade automática: VS Code: estava em foco; "
                "Chrome: estava reproduzindo áudio"
            ),
        },
    )]
    assert falas == [(
        "Pronto: VS Code ficou à esquerda e Chrome, à direita.",
        "feliz",
        1,
    )]


def test_organizacao_nao_narra_titulos_tecnicos_nem_motivos_internos() -> None:
    eventos: list[tuple] = []
    falas: list[tuple] = []
    esquerda = (
        "1043 patrick jane pegou o telefone dela- o mentalista edit pros "
        "bandido edit mentalist - youtube - opera"
    )
    direita = "laylay.py - projeto lay - Visual Studio Code"

    despacho = executar_intencao_janelas(
        "ORGANIZAR_DESKTOP",
        {"modo": "automatico"},
        "pc_a",
        {
            "organizar_janelas_robusto": lambda *_args: {
                "ok": True,
                "executou": True,
                "confirmado": True,
                "status": "layout_confirmado",
                "nome_esquerda": esquerda,
                "nome_direita": direita,
                "prioridades": [
                    {"titulo": esquerda, "motivos": ["reproduzindo áudio"]},
                    {"titulo": direita, "motivos": ["janela em foco"]},
                ],
            },
            "falar_com_lipsync": lambda *args: falas.append(args),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert falas == [(
        "Pronto: YouTube ficou à esquerda e VS Code, à direita.",
        "feliz",
        1,
    )]
    assert "prioridade automática" in eventos[0][2]["detalhe"]


def test_maximizar_no_pc_b_mantem_payload_e_status() -> None:
    eventos: list[tuple] = []
    remotos: list[dict] = []

    despacho = executar_intencao_janelas(
        "MAXIMIZE_WINDOW",
        {"nome_app": "opera"},
        "pc_b",
        {"_enviar_pc_b": remotos.append},
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert remotos == [{"action": "maximize_window", "app": "opera"}]
    assert eventos[0] == ("resultado", "janela_maximizada_pc_b", {"executou": True})
    assert eventos[1][0:3] == (
        "fala_status",
        "janela_maximizada_pc_b",
        "Maximizando opera no PC B.",
    )


def test_abrir_app_no_pc_b_preserva_mapeamento() -> None:
    eventos: list[tuple] = []
    remotos: list[dict] = []

    despacho = executar_intencao_janelas(
        "APP_OPEN",
        {"nome_app": "discord"},
        "pc_b",
        {
            "_enviar_pc_b": remotos.append,
            "APPS_MAP": {"discord": "Discord.exe"},
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert remotos == [{"action": "open_app", "app": "Discord.exe", "quantidade": 1}]
    assert eventos[0] == ("resultado", "app_aberto_pc_b", {"executou": True})


def test_roteador_principal_delega_app_open_ao_executor_de_janelas() -> None:
    falas: list[str] = []
    resultados = []

    retorno = executar_intencao(
        {"intent": "APP_OPEN", "params": {"nome_app": "discord"}},
        "abre o discord",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "APPS_MAP": {"discord": "Discord.exe"},
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": True,
                "programa_em_foco": True,
            },
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: resultados.append(
                contrato
            ),
        },
    )

    assert retorno is True
    assert resultados and resultados[0].status == "ja_aberto_focado"
    assert falas


def test_close_app_local_preserva_mapeamento_e_confirmacao() -> None:
    eventos: list[tuple] = []
    fechados: list[str] = []

    despacho = executar_intencao_janelas(
        "CLOSE_APP",
        {"nome_app": "discord"},
        "pc_a",
        {
            "APPS_MAP": {"discord": "Discord.exe"},
            "_resolver_alvo_ambiente": lambda _nome: {"programa_aberto": True},
            "fechar_programa": fechados.append,
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert fechados == ["Discord.exe"]
    assert eventos[0] == ("resultado", "app_fechado", {"executou": True})


def test_close_app_reconhece_site_aberto_apenas_como_aba() -> None:
    eventos: list[tuple] = []
    chrome: list[tuple] = []
    navegador = NavegadorOperacoesFake()

    despacho = executar_intencao_janelas(
        "CLOSE_APP",
        {"nome_app": "youtube"},
        "pc_a",
        {
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": False,
                "aba_aberta": True,
            },
            "_registro_navegador_operacoes_runtime": navegador,
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    chrome.extend(navegador.chamadas)
    assert chrome == [("close_specific_tab", {"target": "host:youtube"})]
    assert eventos[0] == (
        "resultado",
        "aba_fechada_em_vez_de_app",
        {"executou": True},
    )


def test_close_app_nao_confirma_aba_quando_extensao_recusa() -> None:
    eventos: list[tuple] = []
    despacho = executar_intencao_janelas(
        "CLOSE_APP",
        {"nome_app": "tuya"},
        "pc_a",
        {
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": False,
                "aba_aberta": True,
                "url": "https://iot.tuya.com/cloud/",
            },
            "enviar_comando_chrome": lambda *_args: False,
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert eventos[0] == ("resultado", "falha_execucao", {"executou": False})


def test_close_app_no_pc_b_preserva_mapeamento_remoto() -> None:
    eventos: list[tuple] = []
    remotos: list[dict] = []

    despacho = executar_intencao_janelas(
        "CLOSE_APP",
        {"nome_app": "steam"},
        "pc_b",
        {
            "APPS_MAP": {"steam": "Steam.exe"},
            "_enviar_pc_b": remotos.append,
            "_resolver_alvo_ambiente": lambda _nome: {"programa_aberto": True},
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert remotos == [{"action": "close_app", "app": "Steam.exe"}]
    assert eventos[0] == ("resultado", "app_fechado_pc_b", {"executou": True})


def test_fechar_programa_legado_redireciona_para_close_app() -> None:
    eventos: list[tuple] = []
    recursivos: list[tuple] = []

    despacho = executar_intencao_janelas(
        "FECHAR_PROGRAMA",
        {"programa": "opera"},
        "pc_a",
        {},
        _dependencias(
            eventos,
            executar=lambda resultado, texto, _ctx: recursivos.append((resultado, texto)) or True,
        ),
        texto_original="fecha o opera",
    )

    assert despacho == ResultadoDespacho.concluido()
    assert recursivos == [(
        {"intent": "CLOSE_APP", "params": {"nome_app": "opera"}},
        "fecha o opera",
    )]


def test_roteador_principal_delega_close_app_e_confirma_releitura() -> None:
    estado = {"aberto": True}
    resultados = []

    retorno = executar_intencao(
        {"intent": "CLOSE_APP", "params": {"nome_app": "discord"}},
        "fecha o discord",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "APPS_MAP": {"discord": "Discord.exe"},
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": estado["aberto"],
            },
            "fechar_programa": lambda _nome: estado.update(aberto=False),
            "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: resultados.append(
                contrato
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    )

    assert retorno is True
    assert resultados and resultados[0].status == "app_fechado"
