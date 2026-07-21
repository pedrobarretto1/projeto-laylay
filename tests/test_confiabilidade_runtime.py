from __future__ import annotations

import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.agendamento_mental import AgendaRuntime
from mente_laylay.autonomia.servicos_background import GerenciadorServicosBackground


def _agenda(tmp_path, *, relogio, executar, tolerancia=3600.0):
    return AgendaRuntime(
        str(tmp_path / "agendamentos.json"),
        falar_cb=lambda *_: None,
        abrir_programa_cb=lambda *_: None,
        enviar_pc_b_cb=lambda *_: None,
        enviar_chrome_local_cb=lambda *_: None,
        executar_exec_cb=lambda *_: None,
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
