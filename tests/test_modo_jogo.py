from __future__ import annotations

import threading
import time

from mente_laylay.integracao.llm_http import FALHA_LLM_OCUPADA, LLMHttpRuntime
from mente_laylay.percepcao.modo_jogo import (
    ModoJogoRuntime,
    pedido_foco_explicito,
    processo_parece_jogo,
)
from mente_laylay.percepcao.compatibilidade_overlay_jogo import (
    CompatibilidadeOverlayJogoRuntime,
    calcular_estilo_sem_bordas,
    estrategia_alternancia_tela,
    pressionar_f11_global_seguro,
)


class _ThreadImediata:
    def __init__(self, *, target, **_kwargs):
        self.target = target

    def start(self):
        self.target()


def test_estilo_borderless_preserva_flags_que_nao_sao_moldura() -> None:
    ws_visible = 0x10000000
    estilo_completo = ws_visible | 0x00C00000 | 0x00040000 | 0x00080000
    assert calcular_estilo_sem_bordas(estilo_completo) == ws_visible


def test_compatibilidade_overlay_adapta_cada_janela_uma_vez() -> None:
    adaptados = []
    runtime = CompatibilidadeOverlayJogoRuntime(
        converter=lambda hwnd: adaptados.append(hwnd) or True,
        thread_factory=_ThreadImediata,
        log=lambda *_: None,
    )
    assert runtime.preparar({"hwnd": 77}) is True
    assert runtime.preparar({"hwnd": 77}) is True
    assert adaptados == [77]


def test_compatibilidade_overlay_pode_ser_desativada() -> None:
    runtime = CompatibilidadeOverlayJogoRuntime(
        habilitado=False,
        converter=lambda _hwnd: (_ for _ in ()).throw(AssertionError()),
        thread_factory=_ThreadImediata,
    )
    assert runtime.preparar({"hwnd": 77}) is False


def test_hytale_usa_f11_e_outros_jogos_preservam_alt_enter() -> None:
    assert estrategia_alternancia_tela({"exe": "Hytale.exe"}) == "f11"
    assert estrategia_alternancia_tela({"title": "Hytale"}) == "f11"
    assert estrategia_alternancia_tela({"exe": "cs2.exe"}) == "alt_enter"


def test_f11_global_so_vai_ao_jogo_focado_e_sempre_e_solto() -> None:
    class User32Fake:
        def __init__(self, foco):
            self.foco = foco
            self.eventos = []

        def GetForegroundWindow(self):
            return self.foco

        def keybd_event(self, vk, scan, flags, extra):
            self.eventos.append((vk, scan, flags, extra))

    focado = User32Fake(77)
    outro = User32Fake(88)

    assert pressionar_f11_global_seguro(77, focado) is True
    assert focado.eventos == [(0x7A, 0x57, 0, 0), (0x7A, 0x57, 0x0002, 0)]
    assert pressionar_f11_global_seguro(77, outro) is False
    assert outro.eventos == []


def test_compatibilidade_repassa_retrato_e_tenta_novamente_apos_falha() -> None:
    agora = [10.0]
    chamadas = []

    def converter(hwnd, *, retrato=None):
        chamadas.append((hwnd, dict(retrato or {})))
        return len(chamadas) > 1

    runtime = CompatibilidadeOverlayJogoRuntime(
        converter=converter,
        thread_factory=_ThreadImediata,
        clock=lambda: agora[0],
        intervalo_nova_tentativa_s=3.0,
        log=lambda *_: None,
    )
    retrato = {"hwnd": 91, "exe": "Hytale.exe"}

    assert runtime.preparar(retrato) is True
    agora[0] = 11.0
    assert runtime.preparar(retrato) is True
    assert len(chamadas) == 1
    agora[0] = 13.1
    assert runtime.preparar(retrato) is True
    assert chamadas == [(91, retrato), (91, retrato)]


def test_compatibilidade_para_de_enviar_teclas_apos_limite_de_falhas() -> None:
    agora = [0.0]
    chamadas = []
    logs = []
    runtime = CompatibilidadeOverlayJogoRuntime(
        converter=lambda hwnd: chamadas.append(hwnd) or False,
        thread_factory=_ThreadImediata,
        clock=lambda: agora[0],
        intervalo_nova_tentativa_s=1.0,
        max_tentativas_por_janela=3,
        log=logs.append,
    )

    for instante in (0.0, 1.0, 3.0, 20.0, 40.0):
        agora[0] = instante
        runtime.preparar({"hwnd": 55})

    assert chamadas == [55, 55, 55]
    assert len(logs) == 3
    assert "interrompida" in logs[-1]


def test_navegador_nunca_vira_jogo_mesmo_com_titulo_de_game() -> None:
    assert not processo_parece_jogo(
        "chrome.exe",
        "Minecraft - YouTube",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    )
    assert not processo_parece_jogo(
        "opera.exe",
        "Fortnite em tela cheia",
        r"C:\Users\Pedro\AppData\Local\Programs\Opera\opera.exe",
    )


def test_launcher_nao_e_jogo_mas_executavel_instalado_na_pasta_da_steam_e() -> None:
    assert not processo_parece_jogo(
        "steam.exe", "Steam", r"C:\Program Files (x86)\Steam\steam.exe"
    )
    assert not processo_parece_jogo(
        "EpicGamesLauncher.exe",
        "Epic Games Launcher",
        r"C:\Program Files (x86)\Epic Games\Launcher\EpicGamesLauncher.exe",
    )
    assert processo_parece_jogo(
        "MeuJogo.exe",
        "Meu Jogo",
        r"D:\SteamLibrary\steamapps\common\Meu Jogo\MeuJogo.exe",
    )


def test_java_so_conta_como_jogo_quando_a_janela_confirma_minecraft() -> None:
    assert not processo_parece_jogo("javaw.exe", "Ferramenta Java", r"C:\Java\javaw.exe")
    assert processo_parece_jogo("javaw.exe", "Minecraft 1.21", r"C:\Java\javaw.exe")


def test_soulframe_independente_e_reconhecido_fora_de_loja_famosa() -> None:
    assert processo_parece_jogo(
        "Soulframe.x64.exe",
        "Soulframe",
        r"C:\Users\Pedro\Downloads\pasta organizada\jogos\SoulFrame\Downloaded\Public\Soulframe.x64.exe",
        memoria_mb=7393,
        linha_comando="Soulframe.x64.exe -windowMode:2 -graphicsDriver:dx12 -gpuPreference:2 -shaderCache:1",
    )


def test_jogo_independente_pode_ser_inferido_por_multiplos_sinais_fortes() -> None:
    assert processo_parece_jogo(
        "Nebula.x64.exe",
        "Nebula",
        r"D:\Indies\Nebula\Nebula.x64.exe",
        memoria_mb=1800,
        linha_comando="Nebula.x64.exe -graphicsDriver=dx12 -fullscreen",
    )
    assert not processo_parece_jogo(
        "notepad++.exe",
        "Notas do jogo - Notepad++",
        r"C:\Program Files\Notepad++\notepad++.exe",
        memoria_mb=1200,
        linha_comando="notepad++.exe notas.txt",
    )


def test_navegador_continua_excluido_mesmo_com_memoria_e_argumentos_graficos() -> None:
    assert not processo_parece_jogo(
        "chrome.exe",
        "Soulframe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        memoria_mb=2400,
        linha_comando="chrome.exe --use-angle=d3d11 --start-fullscreen",
    )


def test_modo_jogo_exige_estabilidade_e_mantem_bloqueio_no_alt_tab() -> None:
    agora = [100.0]
    bloqueios = []
    descarregamentos = []
    runtime = ModoJogoRuntime(
        definir_bloqueio_llm=bloqueios.append,
        descarregar_modelo=lambda: descarregamentos.append(True) or True,
        clock=lambda: agora[0],
        entrada_estavel_s=4,
        tolerancia_saida_s=10,
        log=lambda *_args: None,
    )
    retrato = {
        "exe": "cs2.exe",
        "title": "Counter-Strike 2",
        "process_path": r"D:\SteamLibrary\steamapps\common\Counter-Strike\cs2.exe",
    }
    assert not runtime.observar(retrato, True)["ativo"]
    agora[0] = 104.0
    assert runtime.observar(retrato, True)["ativo"]
    assert bloqueios == [True]
    assert descarregamentos == [True]

    agora[0] = 109.0
    assert runtime.observar({"exe": "discord.exe"}, False)["ativo"]
    agora[0] = 115.0
    assert not runtime.observar({"exe": "discord.exe"}, False)["ativo"]
    assert bloqueios == [True, False]


def test_geracao_local_em_andamento_ativa_modo_jogo_na_primeira_deteccao() -> None:
    bloqueios = []
    descarregamentos = []
    runtime = ModoJogoRuntime(
        definir_bloqueio_llm=bloqueios.append,
        descarregar_modelo=lambda: descarregamentos.append(True) or True,
        llm_em_andamento=lambda: True,
        clock=lambda: 100.0,
        entrada_estavel_s=4,
        log=lambda *_args: None,
    )
    retrato = {
        "exe": "cs2.exe", "title": "Counter-Strike 2",
        "process_path": r"D:\SteamLibrary\steamapps\common\Counter-Strike\cs2.exe",
    }

    assert runtime.observar(retrato, True)["ativo"] is True
    assert bloqueios == [True]
    assert descarregamentos == [True]


def test_modo_jogo_nao_espera_requisicao_http_local_terminar() -> None:
    iniciou = threading.Event()
    liberar = threading.Event()

    class Resposta:
        status_code = 200
        text = "ok"

    def postar(_url, **_kwargs):
        iniciou.set()
        liberar.wait(2.0)
        return Resposta()

    runtime = LLMHttpRuntime(
        base_url="http://localhost:11434/v1",
        local_timeout=10,
        remote_timeout=10,
        requests_post=postar,
        print_fn=lambda *_args: None,
    )
    thread = threading.Thread(target=lambda: runtime.post({}, {
        "messages": [{"role": "user", "content": "responda isso"}],
        "max_tokens": 100,
    }))
    thread.start()
    assert iniciou.wait(1.0)
    assert runtime.requisicao_local_em_andamento is True

    comeco = time.monotonic()
    runtime.definir_modo_jogo(True)
    duracao = time.monotonic() - comeco

    assert duracao < 0.1
    assert runtime.modo_jogo_ativo is True
    liberar.set()
    thread.join(2.0)
    assert not thread.is_alive()
    assert runtime.requisicao_local_em_andamento is False


def test_llm_local_nao_faz_requisicao_durante_modo_jogo() -> None:
    chamadas = []
    runtime = LLMHttpRuntime(
        base_url="http://localhost:11434/v1",
        local_timeout=10,
        remote_timeout=10,
        requests_post=lambda *_args, **_kwargs: chamadas.append(True),
        print_fn=lambda *_args: None,
    )
    runtime.definir_modo_jogo(True)
    resposta = runtime.post({}, {
        "messages": [{"role": "user", "content": "conversa comigo"}],
        "max_tokens": 100,
    })
    assert chamadas == []
    assert resposta.json()["choices"][0]["message"]["content"] == FALHA_LLM_OCUPADA
    assert resposta.motivo == "economia_modo_jogo"
    assert resposta.classe == "esperada"
    assert resposta.impacto == "nenhum"
    assert resposta.fallback == "bloqueio_modelo_local_em_jogo"


def test_conversa_principal_pode_acordar_modelo_uma_vez_e_descarrega_depois() -> None:
    chamadas = []
    descarregamentos = []
    timers = []

    class TimerFalso:
        def __init__(self, intervalo, callback):
            self.intervalo = intervalo
            self.callback = callback
            self.cancelado = False
            self.iniciado = False
            timers.append(self)

        def start(self):
            self.iniciado = True

        def cancel(self):
            self.cancelado = True

    class Resposta:
        status_code = 200
        text = "ok"

    def postar(_url, **kwargs):
        chamadas.append(kwargs["json"])
        return Resposta()

    runtime = LLMHttpRuntime(
        base_url="http://localhost:11434/v1",
        local_timeout=10,
        remote_timeout=10,
        requests_post=postar,
        print_fn=lambda *_args: None,
        ao_finalizar_conversa_modo_jogo=lambda: descarregamentos.append(True),
        timer_factory=TimerFalso,
    )
    runtime.definir_modo_jogo(True)

    resposta = runtime.post({}, {
        "messages": [
            {"role": "system", "content": "Você é a Laylay."},
            {"role": "user", "content": "por que você falou vida de estilista?"},
        ],
        "max_tokens": 900,
        "_laylay_conversa_modo_jogo": True,
    })

    assert resposta.status_code == 200
    assert len(chamadas) == 1
    assert chamadas[0]["max_tokens"] == 256
    assert "_laylay_conversa_modo_jogo" not in chamadas[0]
    assert descarregamentos == []
    assert len(timers) == 1
    assert timers[0].iniciado is True
    assert timers[0].intervalo == 60.0

    timers[0].callback()

    assert descarregamentos == [True]
    assert runtime.estado_sessao_jogo == "encerrada"


def test_nova_fala_renova_sessao_e_timer_antigo_nao_descarrega() -> None:
    timers = []
    descarregamentos = []

    class TimerFalso:
        def __init__(self, _intervalo, callback):
            self.callback = callback
            self.cancelado = False
            timers.append(self)

        def start(self):
            pass

        def cancel(self):
            self.cancelado = True

    class Resposta:
        status_code = 200
        text = "ok"

    runtime = LLMHttpRuntime(
        base_url="http://localhost:11434/v1",
        local_timeout=10,
        remote_timeout=10,
        requests_post=lambda *_args, **_kwargs: Resposta(),
        print_fn=lambda *_args: None,
        ao_finalizar_conversa_modo_jogo=lambda: descarregamentos.append(True),
        timer_factory=TimerFalso,
    )
    runtime.definir_modo_jogo(True)
    payload = {
        "messages": [{"role": "user", "content": "oi"}],
        "_laylay_conversa_modo_jogo": True,
    }

    runtime.post({}, payload)
    runtime.post({}, payload)

    assert len(timers) == 2
    assert timers[0].cancelado is True
    timers[0].callback()
    assert descarregamentos == []
    timers[1].callback()
    assert descarregamentos == [True]


def test_conversa_no_jogo_usa_timeout_curto_sem_alterar_modelo() -> None:
    chamadas = []

    class Resposta:
        status_code = 200
        text = "ok"

    def postar(_url, **kwargs):
        chamadas.append(kwargs)
        return Resposta()

    runtime = LLMHttpRuntime(
        base_url="http://localhost:11434/v1",
        local_timeout=45,
        remote_timeout=30,
        game_timeout=7,
        requests_post=postar,
        print_fn=lambda *_args: None,
    )
    runtime.definir_modo_jogo(True)
    runtime.post({}, {
        "model": "Qwen2.5",
        "messages": [{"role": "user", "content": "responda rápido"}],
        "max_tokens": 500,
        "_laylay_conversa_modo_jogo": True,
    })

    assert chamadas[0]["timeout"] == 7
    assert chamadas[0]["json"]["model"] == "Qwen2.5"
    assert chamadas[0]["json"]["max_tokens"] == 256


def test_classificador_json_recebe_none_sem_acordar_modelo_no_jogo() -> None:
    runtime = LLMHttpRuntime(
        base_url="http://127.0.0.1:11434/v1",
        local_timeout=10,
        remote_timeout=10,
        requests_post=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError()),
        print_fn=lambda *_args: None,
    )
    runtime.definir_modo_jogo(True)
    resposta = runtime.post({}, {
        "messages": [{"role": "system", "content": "Responda JSON com intent e params"}],
        "max_tokens": 100,
    })
    assert resposta.json()["choices"][0]["message"]["content"] == '{"intent":"NONE","params":{}}'


def test_troca_de_tela_so_e_liberada_quando_o_foco_foi_pedido() -> None:
    assert not pedido_foco_explicito("abre o youtube")
    assert not pedido_foco_explicito("coloca uma música")
    assert pedido_foco_explicito("traz o chrome pra frente")
    assert pedido_foco_explicito("coloca o discord em foco")
    assert pedido_foco_explicito("maximiza o navegador")
