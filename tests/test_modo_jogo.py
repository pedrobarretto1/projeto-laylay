from __future__ import annotations

from mente_laylay.integracao.llm_http import LLMHttpRuntime
from mente_laylay.percepcao.modo_jogo import (
    ModoJogoRuntime,
    pedido_foco_explicito,
    processo_parece_jogo,
)


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
    assert "poupando a placa" in resposta.json()["choices"][0]["message"]["content"]


def test_conversa_principal_pode_acordar_modelo_uma_vez_e_descarrega_depois() -> None:
    chamadas = []
    descarregamentos = []

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
    assert descarregamentos == [True]


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
