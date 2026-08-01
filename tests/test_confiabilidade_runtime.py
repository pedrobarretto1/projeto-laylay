from __future__ import annotations

import datetime as dt
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.agendamento_mental import AgendaRuntime
from mente_laylay.autonomia.composicao_servicos import (
    ComposicaoServicosLaylayRuntime,
    criar_composicao_servicos_padrao,
)
from mente_laylay.autonomia.servicos_background import (
    GerenciadorServicosBackground,
    OrquestradorInicializacao,
)
from mente_laylay.personalidade.voz_runtime import VozRuntime
from mente_laylay.personalidade.terminal_laylay import escutar_texto_terminal


def _agenda(tmp_path, *, relogio, executar, tolerancia=3600.0):
    return AgendaRuntime(
        str(tmp_path / "agendamentos.json"),
        falar_cb=lambda *_: None,
        abrir_programa_cb=lambda *_: None,
        enviar_pc_b_cb=lambda *_: None,
        enviar_chrome_local_cb=lambda *_: None,
        executar_comando_conteudo_cb=lambda *_: None,
        executar_intencao_cb=executar,
        time_cb=lambda: relogio["agora"].timestamp(),
        now_cb=lambda: relogio["agora"],
        sleep_cb=lambda *_: None,
        log=lambda *_: None,
        tolerancia_recorrente_s=tolerancia,
        retry_base_s=10,
    )


def test_agenda_so_consome_acao_depois_de_confirmacao_e_tenta_novamente(tmp_path):
    relogio = {"agora": dt.datetime(2026, 7, 15, 23, 27, 0)}
    resultados = iter((False, True))
    agenda = _agenda(tmp_path, relogio=relogio, executar=lambda *_: next(resultados))
    agenda.save([{
        "id": "luz-1", "tipo": "once", "ativo": True,
        "ts_execucao": relogio["agora"].timestamp() - 1,
        "intencao_no_disparo": {
            "intent": "IOT_CONTROL", "params": {"acao": "desligar", "alvo": "lampada_quarto"},
        },
    }])

    agenda.processar_ciclo()
    falhou = agenda.load()[0]
    assert falhou["ativo"] is True
    assert falhou["tentativas_falhas"] == 1

    relogio["agora"] += dt.timedelta(seconds=10)
    agenda.processar_ciclo()
    concluido = agenda.load()[0]
    assert concluido["ativo"] is False
    assert "tentativas_falhas" not in concluido


def test_agenda_recorrente_recupera_atraso_sem_repetir_apos_reinicio(tmp_path):
    relogio = {"agora": dt.datetime(2026, 7, 15, 23, 28, 0)}
    execucoes = []
    agenda = _agenda(
        tmp_path, relogio=relogio,
        executar=lambda intencao, _texto: execucoes.append(intencao) or True,
    )
    agenda.save([{
        "id": "rotina-luz", "tipo": "daily", "ativo": True, "hora": "23:27",
        "intencao_no_disparo": {
            "intent": "IOT_CONTROL", "params": {"acao": "desligar", "alvo": "lampada_quarto"},
        },
    }])

    agenda.processar_ciclo()
    agenda_reiniciada = _agenda(
        tmp_path, relogio=relogio,
        executar=lambda intencao, _texto: execucoes.append(intencao) or True,
    )
    agenda_reiniciada.processar_ciclo()

    assert len(execucoes) == 1
    assert agenda.load()[0]["ultimo_disparo_data"] == "2026-07-15"


def test_salvamento_da_agenda_e_atomico_e_deixa_json_valido(tmp_path):
    relogio = {"agora": dt.datetime(2026, 7, 15, 12, 0, 0)}
    agenda = _agenda(tmp_path, relogio=relogio, executar=lambda *_: True)

    assert agenda.save([{"id": "a", "ativo": True}]) is True
    with open(tmp_path / "agendamentos.json", encoding="utf-8") as arquivo:
        assert json.load(arquivo) == [{"id": "a", "ativo": True}]
    assert not list(tmp_path.glob("*.tmp"))


def test_supervisor_reinicia_servico_apos_falha_sem_duplicar_a_mente():
    chamadas = []
    esperas = []
    supervisor = GerenciadorServicosBackground(
        reiniciar_apos_falha=True,
        atraso_reinicio_s=2,
        sleep=esperas.append,
        log=lambda *_: None,
    )

    def servico():
        chamadas.append("mesmo-servico")
        if len(chamadas) == 1:
            raise RuntimeError("falha transitória")

    supervisor._iniciados.add("Ouvido")
    supervisor._executar_protegido("Ouvido", servico)

    assert chamadas == ["mesmo-servico", "mesmo-servico"]
    assert esperas == [2]
    assert "Ouvido" not in supervisor.ativos()


def test_supervisor_encaminha_queda_de_servico_ao_diagnostico_central():
    falhas = []
    supervisor = GerenciadorServicosBackground(
        log=lambda *_: None,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
    )

    supervisor._iniciados.add("Visão Jogo")
    supervisor._executar_protegido(
        "Visão Jogo", lambda: (_ for _ in ()).throw(RuntimeError("falhou")),
    )

    assert falhas[0][0] == ("servico_Visão Jogo", "queda_background")
    assert isinstance(falhas[0][1]["erro"], RuntimeError)


def test_supervisor_registra_ciclo_de_queda_reinicio_e_recuperacao() -> None:
    eventos = []
    falhas = []
    chamadas = []
    supervisor = GerenciadorServicosBackground(
        reiniciar_apos_falha=True,
        atraso_reinicio_s=2,
        sleep=lambda _segundos: None,
        log=lambda *_: None,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        registrar_evento=lambda *args, **kwargs: eventos.append((args, kwargs)),
    )

    def servico():
        chamadas.append(1)
        if len(chamadas) == 1:
            raise RuntimeError("conteudo privado")

    supervisor._iniciados.add("Ouvido")
    supervisor._executar_protegido("Ouvido", servico)

    assert [args[1] for args, _kwargs in eventos] == [
        "ativo", "queda", "reinicio_agendado", "reiniciando", "finalizado",
    ]
    assert eventos[1][1]["fallback"] == "reinicio_agendado"
    assert eventos[2][1]["atraso_s"] == 2
    assert falhas[0][1]["classe"] == "degradacao"
    assert falhas[0][1]["impacto"] == "servico"
    assert falhas[0][1]["fallback"] == "reinicio_agendado"


def test_supervisor_nao_imprime_mensagem_privada_da_excecao() -> None:
    logs = []
    supervisor = GerenciadorServicosBackground(log=logs.append)
    supervisor._iniciados.add("Visao")

    supervisor._executar_protegido(
        "Visao",
        lambda: (_ for _ in ()).throw(RuntimeError("senha=segredo absoluto")),
    )

    texto = " ".join(logs).casefold()
    assert "runtimeerror" in texto
    assert "senha" not in texto
    assert "segredo" not in texto


def test_falha_ao_criar_thread_tambem_chega_uma_vez_ao_diagnostico() -> None:
    eventos = []
    falhas = []

    def thread_factory(**_kwargs):
        raise OSError("C:/segredo/driver privado")

    supervisor = GerenciadorServicosBackground(
        thread_factory=thread_factory,
        log=lambda *_: None,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        registrar_evento=lambda *args, **kwargs: eventos.append((args, kwargs)),
    )

    resultado = supervisor.iniciar_varios({"Microfone": lambda: None})

    assert resultado == {"Microfone": False}
    assert len(falhas) == 1
    assert falhas[0][0] == ("servico_Microfone", "falha_inicializacao")
    assert falhas[0][1]["fallback"] == "servico_indisponivel"
    assert [args[1] for args, _kwargs in eventos] == ["falha_inicializacao"]


def test_supervisor_usa_um_unico_prazo_para_encerrar_todas_as_threads():
    relogio = {"agora": 10.0}
    esperas = []

    class ThreadSimulada:
        def join(self, timeout):
            esperas.append(timeout)
            relogio["agora"] += 0.4

    supervisor = GerenciadorServicosBackground(
        monotonic=lambda: relogio["agora"],
        log=lambda *_: None,
    )
    supervisor._threads = {
        "um": ThreadSimulada(),
        "dois": ThreadSimulada(),
        "tres": ThreadSimulada(),
    }

    supervisor.encerrar(timeout_s=1.0)

    assert [round(valor, 1) for valor in esperas] == [1.0, 0.6, 0.2]


def test_supervisor_compartilha_sinal_unico_e_interrompe_esperas():
    supervisor = GerenciadorServicosBackground(log=lambda *_: None)

    assert supervisor.evento_parada.is_set() is False
    assert supervisor.deve_parar() is False
    assert supervisor.aguardar(0) is False

    supervisor.solicitar_encerramento()

    assert supervisor.evento_parada.is_set() is True
    assert supervisor.deve_parar() is True
    assert supervisor.aguardar(30) is True


def test_encerramento_desbloqueia_servico_em_espera_sem_consumir_o_timeout():
    supervisor = GerenciadorServicosBackground(log=lambda *_: None)
    saiu = threading.Event()

    def servico():
        supervisor.aguardar(30)
        saiu.set()

    assert supervisor.iniciar("espera-longa", servico) is True
    inicio = time.monotonic()
    supervisor.encerrar(timeout_s=1.0)

    assert saiu.wait(0.2) is True
    assert time.monotonic() - inicio < 0.5
    assert supervisor.ativos() == ()


def test_prompt_aberto_e_cancelado_sem_virar_falha_da_mente() -> None:
    falhas = []
    supervisor = GerenciadorServicosBackground(
        log=lambda *_: None,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
    )
    leitor_iniciado = threading.Event()

    class StdinTTY:
        @staticmethod
        def isatty():
            return True

    def leitor(_prompt, *, deve_continuar, sleep_fn, **_kwargs):
        leitor_iniciado.set()
        while deve_continuar():
            sleep_fn(0.005)
        return None

    def chat_terminal():
        escutar_texto_terminal(
            estado_ativo=lambda: True,
            processar_texto=lambda _texto: None,
            stdin=StdinTTY(),
            raw_print=lambda *_args, **_kwargs: None,
            sleep_fn=time.sleep,
            log=lambda *_: None,
            deve_continuar=lambda: not supervisor.deve_parar(),
            ler_linha_fn=leitor,
        )

    assert supervisor.iniciar("Laylay-Chat-Terminal", chat_terminal) is True
    assert leitor_iniciado.wait(0.3) is True

    supervisor.encerrar(timeout_s=0.5)

    assert supervisor.ativos() == ()
    assert falhas == []


def test_supervisor_nao_exibe_traceback_com_segundo_ctrl_c_no_encerramento():
    logs = []

    class ThreadInterrompida:
        def join(self, timeout):
            raise KeyboardInterrupt

    supervisor = GerenciadorServicosBackground(log=logs.append)
    supervisor._threads = {"Ouvido": ThreadInterrompida()}

    supervisor.encerrar()
    supervisor.encerrar()

    assert logs == ["\n🛑 Encerramento acelerado por novo Ctrl+C."]
    assert supervisor.iniciar("tardio", lambda: None) is False


def test_supervisor_marca_servico_vivo_apos_prazo_como_orfao() -> None:
    eventos = []
    falhas = []

    class ThreadOrfa:
        def is_alive(self):
            return True

        def join(self, timeout):
            return None

    supervisor = GerenciadorServicosBackground(
        log=lambda *_: None,
        registrar_evento=lambda *args, **kwargs: eventos.append((args, kwargs)),
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
    )
    supervisor._iniciados.add("Travado")
    supervisor._threads = {"Travado": ThreadOrfa()}

    supervisor.encerrar(timeout_s=0)

    assert eventos == [(('Travado', 'orfao'), {
        'tentativa': 0, 'atraso_s': 0.0,
        'fallback': 'encerramento_do_processo',
    })]
    assert falhas[0][0] == ("servico_Travado", "servico_orfao")
    assert falhas[0][1]["classe"] == "degradacao"
    assert falhas[0][1]["impacto"] == "servico"
    assert falhas[0][1]["fallback"] == "encerramento_do_processo"


def test_inicializacao_registra_controles_antes_das_threads_pesadas():
    ordem = []

    class _ServicosFake:
        def iniciar_varios(self, threads):
            ordem.append(("threads", tuple(threads)))
            return {nome: True for nome in threads}

    runtime = OrquestradorInicializacao(
        servicos=_ServicosFake(),
        log=lambda *_: None,
    )
    runtime.iniciar(
        etapas={"memoria": lambda: ordem.append("etapa")},
        threads={"Whisper": lambda: None},
        hotkeys=lambda: ordem.append("hotkeys"),
    )
    assert ordem == ["etapa", "hotkeys", ("threads", ("Whisper",))]


def test_composicao_adapta_servicos_cooperativos_sem_repetir_regra_no_main():
    class Gerenciador:
        deve_parar = staticmethod(lambda: False)
        aguardar = staticmethod(lambda _segundos: False)

    recebidos = []

    def somente_parada(**kwargs):
        recebidos.append(kwargs)

    def parada_e_espera(**kwargs):
        recebidos.append(kwargs)

    composicao = ComposicaoServicosLaylayRuntime(
        gerenciador=Gerenciador(),
        etapas={},
        threads={"simples": lambda: None},
        threads_com_parada={"parada": somente_parada},
        threads_com_espera={"espera": parada_e_espera},
        log=lambda *_: None,
    )
    catalogo = composicao.catalogo_threads()

    catalogo["parada"]()
    catalogo["espera"]()

    assert tuple(catalogo) == ("simples", "parada", "espera")
    assert recebidos[0] == {"deve_parar": Gerenciador.deve_parar}
    assert recebidos[1] == {
        "deve_parar": Gerenciador.deve_parar,
        "aguardar_fn": Gerenciador.aguardar,
    }


def test_composicao_tenta_todos_os_finalizadores_mesmo_com_falha():
    eventos, falhas = [], []

    class Gerenciador:
        def solicitar_encerramento(self):
            eventos.append("sinal")

    def falhar():
        eventos.append("voz")
        raise RuntimeError("falha")

    composicao = ComposicaoServicosLaylayRuntime(
        gerenciador=Gerenciador(),
        etapas={},
        threads={},
        encerramento=(
            ("memoria", lambda: eventos.append("memoria")),
            ("voz", falhar),
            ("avatar", lambda: eventos.append("avatar")),
        ),
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        log=lambda *_: None,
    )

    resultado = composicao.encerrar()

    assert eventos == ["sinal", "memoria", "voz", "avatar"]
    assert resultado == {"memoria": True, "voz": False, "avatar": True}
    assert falhas[0][0] == ("encerramento", "voz")


def test_composicao_compartilha_um_unico_prazo_com_todos_os_finalizadores() -> None:
    relogio = {"agora": 10.0}
    recebidos = []

    class Gerenciador:
        def solicitar_encerramento(self):
            recebidos.append(("sinal", None))

        def encerrar(self, timeout_s):
            recebidos.append(("supervisor", timeout_s))

    def finalizador(nome):
        def executar(timeout_s):
            recebidos.append((nome, timeout_s))
            relogio["agora"] += 0.4

        return executar

    chamado_sem_timeout = []
    composicao = ComposicaoServicosLaylayRuntime(
        gerenciador=Gerenciador(),
        etapas={},
        threads={},
        encerramento=(
            ("voz", finalizador("voz")),
            ("avatar", finalizador("avatar")),
            ("gamebar", finalizador("gamebar")),
            ("memoria", lambda: chamado_sem_timeout.append(True)),
        ),
        monotonic=lambda: relogio["agora"],
        timeout_encerramento_s=1.0,
        log=lambda *_: None,
    )

    resultado = composicao.encerrar()

    limites = {nome: round(valor, 1) for nome, valor in recebidos if valor is not None}
    assert limites == {
        "voz": 1.0, "avatar": 0.6, "gamebar": 0.2, "supervisor": 0.0,
    }
    assert chamado_sem_timeout == [True]
    assert resultado == {
        "voz": True, "avatar": True, "gamebar": True, "memoria": True,
    }


def test_ciclo_de_vida_completo_inicia_sinaliza_e_encerra_sem_servico_vivo():
    """Linha de base da P0: composição e supervisor atravessam o ciclo real."""
    eventos = []
    prontos = {nome: threading.Event() for nome in ("Ouvido", "Agenda")}
    supervisor = GerenciadorServicosBackground(log=lambda *_: None)
    orquestrador = OrquestradorInicializacao(
        servicos=supervisor,
        log=lambda *_: None,
    )

    def servico(nome):
        def executar():
            eventos.append(f"{nome}:iniciado")
            prontos[nome].set()
            supervisor.aguardar(30)
            eventos.append(f"{nome}:encerrado")

        return executar

    composicao = ComposicaoServicosLaylayRuntime(
        gerenciador=supervisor,
        etapas={"memoria": lambda: eventos.append("memoria:carregada")},
        threads={nome: servico(nome) for nome in prontos},
        hotkeys=(("chat", lambda: eventos.append("hotkey:chat")),),
        encerramento=(
            ("memoria", lambda: eventos.append("memoria:salva")),
            ("voz", lambda: eventos.append("voz:encerrada")),
        ),
        log=lambda *_: None,
    )

    resultado_inicio = composicao.iniciar(orquestrador)
    assert all(evento.wait(0.5) for evento in prontos.values())
    assert resultado_inicio == {
        "etapas": {"memoria": True},
        "threads": {"Ouvido": True, "Agenda": True},
    }
    assert set(supervisor.ativos()) == {"Agenda", "Ouvido"}

    resultado_fim = composicao.encerrar()
    supervisor.encerrar(timeout_s=1.0)

    assert resultado_fim == {"memoria": True, "voz": True}
    assert supervisor.ativos() == ()
    assert "memoria:salva" in eventos
    assert "voz:encerrada" in eventos
    assert "Ouvido:encerrado" in eventos
    assert "Agenda:encerrado" in eventos
    assert supervisor.iniciar("tardio", lambda: None) is False


def test_catalogo_padrao_valida_e_monta_todas_as_conexoes():
    eventos = []

    class Runtime:
        def iniciar(self):
            eventos.append("iniciar")

        def executar(self, **kwargs):
            eventos.append(kwargs)

        def encerrar(self):
            eventos.append("encerrar")

        def parar(self):
            eventos.append("parar")

    class Gerenciador:
        deve_parar = staticmethod(lambda: False)
        aguardar = staticmethod(lambda _segundos: False)

        def solicitar_encerramento(self):
            eventos.append("sinal")

    nomes_funcoes = (
        "carregar_memoria", "_preparar_autonomia_segura_padrao",
        "_preparar_sugestoes_proativas_jogo",
        "init_memoria_contexto_diaria", "_carregar_playlists_para_memoria",
        "_iniciar_worker_de_falas", "_escutar_texto_do_chat_terminal",
        "run_ws_server_in_thread", "gmail_daemon", "_agenda_daemon",
        "monitor_rotina_daemon", "_porteiro_daemon", "_monitor_saude_daemon",
        "registrar_hotkeys_modo_chat", "registrar_hotkey_barra_comando",
        "salvar_memoria",
    )
    namespace = {nome: (lambda: True) for nome in nomes_funcoes}
    namespace["_renovar_sessao_conversa"] = lambda motivo, nova: eventos.append((motivo, nova))
    for nome in (
        "_gamebar_bridge_runtime", "_avatar_runtime", "_ouvido_whisper_runtime",
        "_observador_inventario_jogo_runtime", "_observador_presenca_jogo_runtime",
        "_diretor_presenca_runtime", "_observador_area_transferencia_runtime",
        "_monitor_janelas_runtime",
        "_ritmo_circadiano_runtime", "_motor_temporal_runtime",
        "_motor_aprendizado_runtime", "_rede_associativa_runtime", "_voz_runtime",
        "_barra_comando_runtime",
    ):
        namespace[nome] = Runtime()

    composicao = criar_composicao_servicos_padrao(
        namespace, gerenciador=Gerenciador(), log=lambda *_: None,
    )

    assert len(composicao.etapas) == 10
    assert len(composicao.catalogo_threads()) == 16
    assert "Laylay-Chat-Terminal" in composicao.threads_com_parada
    assert "Laylay-Chat-Terminal" not in composicao.threads
    assert tuple(nome for nome, _finalizar in composicao.encerramento) == (
        "barra_comando", "avatar", "gamebar", "voz",
        "rede_associativa", "memoria",
    )
    composicao.etapas["iniciar nova sessão conversacional"]()
    assert eventos[-1] == ("inicio_programa", True)


def test_worker_de_voz_e_entregue_ao_supervisor_sem_criar_thread_lateral() -> None:
    servicos = []
    threads_laterais = []

    class ThreadLateral:
        def __init__(self, **kwargs):
            threads_laterais.append(kwargs)

        def start(self):
            return None

    runtime = VozRuntime(
        fallback_fala="fallback", voice="voz",
        edge_tts_mod=object(), sounddevice_mod=object(),
        soundfile_mod=object(), pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("", "", ""),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        interrupt_event=threading.Event(),
        iniciar_servico_cb=lambda nome, target: servicos.append((nome, target)) or True,
        thread_factory=ThreadLateral,
        log=lambda *_args: None,
    )

    runtime.iniciar_worker()
    runtime.iniciar_worker()

    assert len(servicos) == 1
    assert servicos[0][0] == "Laylay-SpeechQueue"
    assert callable(servicos[0][1])
    assert threads_laterais == []


def test_transacao_da_agenda_preserva_duas_inclusoes_concorrentes(tmp_path):
    relogio = {"agora": dt.datetime(2026, 7, 15, 12, 0, 0)}
    agenda = _agenda(tmp_path, relogio=relogio, executar=lambda *_: True)
    agenda.save([])

    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(
            lambda numero: agenda.transacionar(
                lambda lista: lista.append({"id": str(numero), "ativo": True})
            ),
            (1, 2),
        ))

    assert resultados == [True, True]
    assert {item["id"] for item in agenda.load()} == {"1", "2"}


def test_sqlite_usa_wal_e_aceita_escritas_de_servicos_concorrentes(tmp_path):
    memoria = MemoriaSQLite(str(tmp_path / "mente.sqlite"))

    with memoria._conectar() as conexao:
        assert conexao.execute("PRAGMA journal_mode").fetchone()[0].casefold() == "wal"
        assert conexao.execute("PRAGMA busy_timeout").fetchone()[0] == 15000

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(
            lambda numero: memoria.salvar_preferencia(f"servico_{numero}", numero),
            range(24),
        ))

    preferencias = memoria.carregar_preferencias()
    assert all(preferencias[f"servico_{numero}"] == str(numero) for numero in range(24))
