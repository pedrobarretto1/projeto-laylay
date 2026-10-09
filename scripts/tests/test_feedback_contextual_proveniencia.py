"""Identidade e proveniência de feedback pertencem ao aprendizado comum."""

from concurrent.futures import ThreadPoolExecutor
import sqlite3

import pytest

from memoria_sqlite import MemoriaSQLite
from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime


def _motor(memoria):
    return MotorAprendizadoRuntime(
        memoria_sqlite=memoria, contexto_getter=lambda: {"atividade": "programacao"},
        log=lambda *_: None,
    )


def _registrar(motor, *, identidade="entrega-a", dominio="jogo", tipo="aceitacao", aceito=True):
    return motor.registrar_feedback_contextual(
        tipo=tipo, aceito=aceito, resultado="boa dica", origem="presenca", alvo="salto",
        id_evento=identidade,
        proveniencia={"id_entrega": identidade, "dominio": dominio,
                     "origem_produtor": "observador_jogo", "entregue": True},
    )


def test_feedback_persiste_vinculo_e_contexto_da_emissao_sem_preferencia_explicita(tmp_path):
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    hipotese = _registrar(_motor(memoria))
    assert hipotese and hipotese["evidencias_positivas"] == 1
    evento = memoria.listar_eventos_aprendizado(hipotese["chave"])[0]
    assert evento["contexto"]["proveniencia"]["id_entrega"] == "entrega-a"
    assert evento["contexto"]["proveniencia"]["dominio"] == "jogo"
    assert evento["id_evento"] == "feedback_contextual:entrega-a"
    assert evento["confirmado_usuario"] is False
    assert hipotese["status"] == "candidata"


def test_reentrega_de_feedback_nao_aumenta_peso_apos_recriar_motor(tmp_path):
    caminho = str(tmp_path / "memoria.sqlite")
    primeiro = _registrar(_motor(MemoriaSQLite(caminho)))
    segundo = _registrar(_motor(MemoriaSQLite(caminho)))
    assert primeiro and segundo
    assert segundo["evidencias_positivas"] == 1
    assert segundo["confianca"] == primeiro["confianca"]
    assert len(MemoriaSQLite(caminho).listar_eventos_aprendizado(segundo["chave"])) == 1


def test_mesma_ocorrencia_concorrente_atualiza_hipotese_uma_vez(tmp_path):
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    motores = [_motor(memoria), _motor(memoria)]
    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(_registrar, motores))
    assert all(resultados)
    assert len(memoria.listar_eventos_aprendizado(resultados[0]["chave"])) == 1
    assert memoria.obter_hipotese_aprendizado(resultados[0]["chave"])["evidencias_positivas"] == 1


def test_identidade_nao_transfere_feedback_entre_dominios(tmp_path):
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    motor = _motor(memoria)
    primeira = _registrar(motor, dominio="jogo")
    assert primeira
    assert _registrar(motor, dominio="arquivos") is None
    assert len(memoria.listar_hipoteses_aprendizado(limit=20)) == 1
    assert len(memoria.listar_eventos_aprendizado(primeira["chave"])) == 1


def test_dominios_distintos_e_novas_ocorrencias_preservam_acumulacao(tmp_path):
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    motor = _motor(memoria)
    jogo = _registrar(motor)
    arquivos = _registrar(motor, identidade="entrega-b", dominio="arquivos")
    jogo_novo = _registrar(motor, identidade="entrega-c")
    assert jogo and arquivos and jogo_novo
    assert jogo["chave"] != arquivos["chave"]
    assert jogo_novo["evidencias_positivas"] == 2
    assert arquivos["evidencias_positivas"] == 1


def test_chamadas_legadas_sem_identidade_continuam_acumulando(tmp_path):
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    motor = _motor(memoria)
    for _ in range(2):
        hipotese = motor.registrar_feedback_contextual(
            tipo="aceitacao", aceito=True, origem="arquivos", alvo="nota.txt",
        )
    assert hipotese["evidencias_positivas"] == 2


@pytest.mark.parametrize("tipo", ["correcao", "repeticao"])
def test_tipo_explicito_de_feedback_nao_vira_silencio_por_aceito_indeterminado(tmp_path, tipo):
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    motor = _motor(memoria)
    hipotese = motor.registrar_feedback_contextual(tipo=tipo, aceito=None, origem="presenca")
    evento = memoria.listar_eventos_aprendizado(hipotese["chave"])[0]
    assert evento["sinal"] == pytest.approx(-0.35), "tipo explícito foi reduzido a silêncio"
    assert evento["confirmado_usuario"] is False


def test_migracao_preserva_evidencia_antiga_e_permita_novas_identidades(tmp_path):
    caminho = str(tmp_path / "memoria.sqlite")
    with sqlite3.connect(caminho) as conn:
        conn.execute("""CREATE TABLE aprendizado_eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, chave TEXT NOT NULL,
            tipo TEXT NOT NULL, escopo TEXT NOT NULL, valor_json TEXT NOT NULL,
            contexto_json TEXT NOT NULL, evidencia TEXT NOT NULL, sinal REAL NOT NULL,
            origem TEXT NOT NULL, confirmado_usuario INTEGER NOT NULL, criado_em TEXT NOT NULL
        )""")
        conn.execute("INSERT INTO aprendizado_eventos VALUES (1, 'antiga', 'padrao', 'geral', '{}', '{}', 'antiga', 1, 'observacao', 0, '2026-10-01')")
    memoria = MemoriaSQLite(caminho)
    assert _registrar(_motor(memoria))
    antigo = memoria.listar_eventos_aprendizado("antiga")[0]
    assert antigo["evidencia"] == "antiga" and antigo["id_evento"] == ""


def test_id_de_feedback_nao_pode_divergir_da_proveniencia(tmp_path):
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    with pytest.raises(ValueError, match="identidade"):
        _motor(memoria).registrar_feedback_contextual(
            tipo="aceitacao", aceito=True, origem="presenca", id_evento="entrega-a",
            proveniencia={"id_entrega": "entrega-b"},
        )
    assert memoria.listar_hipoteses_aprendizado(limit=10) == []


@pytest.mark.parametrize("mudanca", [{"origem_produtor": "outra_fonte"}, {"entregue": False}])
def test_duplicata_nao_confirma_proveniencia_incompativel(tmp_path, mudanca):
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    motor = _motor(memoria)
    primeira = _registrar(motor)
    assert primeira
    assert motor.registrar_feedback_contextual(
        tipo="aceitacao", aceito=True, resultado="boa dica", origem="presenca", alvo="salto",
        id_evento="entrega-a",
        proveniencia={"id_entrega": "entrega-a", "dominio": "jogo",
                     "origem_produtor": "observador_jogo", "entregue": True, **mudanca},
    ) is None, "duplicata confirmou contrato com outra proveniência"
    assert len(memoria.listar_eventos_aprendizado(primeira["chave"])) == 1


def test_replay_preserva_proveniencia_com_contexto_atual_diferente(tmp_path):
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    motor = _motor(memoria)
    primeiro = _registrar(motor)
    motor.contexto_getter = lambda: {"atividade": "musica", "periodo": "manha"}
    replay = _registrar(motor)
    assert replay and replay["confianca"] == primeiro["confianca"]
    assert len(memoria.listar_eventos_aprendizado(primeiro["chave"])) == 1
