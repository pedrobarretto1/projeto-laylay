from __future__ import annotations

from datetime import datetime, timedelta
import os
import tempfile

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.preferencias_sugestoes_runtime import (
    PreferenciasSugestoesRuntime,
)
from mente_laylay.autonomia.sugestoes_sistema import processar_confirmacao_sugestao
from mente_laylay.memoria_mental.maturidade_aprendizado import (
    MaturidadeAprendizadoRuntime,
)
from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime


def _memoria_temporaria():
    pasta = tempfile.TemporaryDirectory()
    return pasta, MemoriaSQLite(os.path.join(pasta.name, "memoria.sqlite"))


def test_observacao_isolada_nao_vira_regra() -> None:
    pasta, memoria = _memoria_temporaria()
    try:
        memoria.registrar_evidencia_aprendizado(
            chave="rotina:noite:vscode", tipo="rotina_observada", escopo="noite",
            valor={"descricao_humana": "usa VS Code à noite"},
            sinal=0.35, origem="observacao_ambiente", contexto={"periodo": "noite"},
        )
        maturidade = MaturidadeAprendizadoRuntime(
            memoria_sqlite=memoria, contexto_getter=lambda: {"periodo": "noite"},
        )
        avaliacao = maturidade.avaliar("rotina:noite:vscode")

        assert avaliacao["nivel"] == "hipotese"
        assert avaliacao["aplicavel"] is False
    finally:
        pasta.cleanup()


def test_evidencias_em_dias_diferentes_promovem_preferencia_provavel() -> None:
    pasta, memoria = _memoria_temporaria()
    try:
        for evidencia in ("dia um", "dia dois", "dia três"):
            memoria.registrar_evidencia_aprendizado(
                chave="musica:foco", tipo="preferencia_musical", escopo="trabalho",
                valor={"descricao_humana": "prefere música de foco trabalhando"},
                sinal=1.0, origem="feedback_usuario", evidencia=evidencia,
                contexto={"aplicativo": "Code.exe"},
            )
        conn = memoria._conectar()
        try:
            ids = [row[0] for row in conn.execute(
                "SELECT id FROM aprendizado_eventos WHERE chave = ? ORDER BY id",
                ("musica:foco",),
            ).fetchall()]
            base = datetime.now()
            for indice, evento_id in enumerate(ids):
                conn.execute(
                    "UPDATE aprendizado_eventos SET criado_em = ? WHERE id = ?",
                    ((base - timedelta(days=len(ids) - indice)).isoformat(" "), evento_id),
                )
            conn.commit()
        finally:
            conn.close()
        maturidade = MaturidadeAprendizadoRuntime(
            memoria_sqlite=memoria,
            contexto_getter=lambda: {"aplicativo": "Code.exe"},
        )
        avaliacao = maturidade.avaliar("musica:foco")

        assert avaliacao["nivel"] == "provavel"
        assert avaliacao["dias_com_evidencia"] == 3
        assert avaliacao["aplicavel"] is True
    finally:
        pasta.cleanup()


def test_preferencia_confirmada_respeita_contexto() -> None:
    pasta, memoria = _memoria_temporaria()
    contexto = {"periodo": "noite"}
    try:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=memoria, contexto_getter=lambda: dict(contexto),
            log=lambda *_args: None,
        )
        hipotese = motor.registrar_contraproposta("TIME_WIND_DOWN", {
            "alternativa": {"intent": "IOT_CONTROL", "params": {"acao": "ajustar_brilho"}},
            "descricao": "diminuir o brilho",
            "evidencia": "prefiro diminuir o brilho",
        })
        assert hipotese["status"] == "ativa"
        assert motor.avaliar_hipotese("preferencia_sugestao:TIME_WIND_DOWN")["aplicavel"]

        contexto["periodo"] = "manha"
        avaliacao = motor.avaliar_hipotese("preferencia_sugestao:TIME_WIND_DOWN")
        assert avaliacao["aplicavel"] is False
        assert "periodo" in avaliacao["motivos"][0]
    finally:
        pasta.cleanup()


def test_preferencia_declarada_global_ignora_mudanca_de_periodo() -> None:
    pasta, memoria = _memoria_temporaria()
    contexto = {"periodo": "noite"}
    try:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=memoria, contexto_getter=lambda: dict(contexto),
            log=lambda *_args: None,
        )
        motor.registrar_contraproposta("VOLUME", {
            "alternativa": {"intent": "VOLUME", "params": {"nivel_volume": 25}},
            "descricao": "deixar o volume em 25 por cento",
            "evidencia": "de agora em diante sempre prefiro 25 por cento",
        })
        contexto["periodo"] = "manha"

        avaliacao = motor.avaliar_hipotese("preferencia_sugestao:VOLUME")
        assert avaliacao["global"] is True
        assert avaliacao["aplicavel"] is True
    finally:
        pasta.cleanup()


def test_excecoes_repetidas_suspendem_preferencia() -> None:
    pasta, memoria = _memoria_temporaria()
    try:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=memoria, contexto_getter=lambda: {"periodo": "noite"},
            log=lambda *_args: None,
        )
        motor.registrar_contraproposta("TIME_WIND_DOWN", {
            "alternativa": {"intent": "IOT_CONTROL", "params": {"acao": "ajustar_brilho"}},
            "descricao": "diminuir o brilho", "evidencia": "prefiro diminuir o brilho",
        })
        chave = "preferencia_sugestao:TIME_WIND_DOWN"
        atual = memoria.obter_hipotese_aprendizado(chave)
        for numero in range(3):
            memoria.registrar_evidencia_aprendizado(
                chave=chave, tipo=atual["tipo"], escopo=atual["escopo"],
                valor=atual["valor"], sinal=-1.0, origem="excecao_usuario",
                evidencia=f"exceção {numero}", contexto={"periodo": "noite"},
            )

        avaliacao = motor.avaliar_hipotese(chave)
        assert avaliacao["aplicavel"] is False
        assert avaliacao["evidencias_negativas"] == 3
    finally:
        pasta.cleanup()


def test_preferencia_runtime_grava_envelope_e_filtra_contexto() -> None:
    pasta, memoria = _memoria_temporaria()
    contexto = {"periodo": "noite"}
    logs = []
    try:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=memoria, contexto_getter=lambda: dict(contexto),
            log=lambda *_args: None,
        )
        namespace = {
            "MEMORIA_SQLITE": memoria,
            "_motor_aprendizado_runtime": motor,
            "_chave_preferencia_sugestao_mente": lambda comando, _payload: comando,
            "salvar_memoria": lambda: None,
            "print": lambda mensagem: logs.append(mensagem),
        }
        runtime = PreferenciasSugestoesRuntime(lambda: namespace)
        registro = {
            "alternativa": {"intent": "IOT_CONTROL", "params": {"acao": "ajustar_brilho"}},
            "descricao": "diminuir o brilho", "evidencia": "prefiro diminuir o brilho",
        }
        assert runtime.registrar("TIME_WIND_DOWN", registro)
        mesma_noite = runtime.obter("TIME_WIND_DOWN", {})
        assert mesma_noite["_aprendizado"]["hipotese_chave"].endswith("TIME_WIND_DOWN")

        contexto["periodo"] = "manha"
        assert runtime.obter("TIME_WIND_DOWN", {}) is None
        assert any("não aplicada" in mensagem for mensagem in logs)
    finally:
        pasta.cleanup()


def test_recusa_de_sugestao_aprendida_registra_excecao() -> None:
    agora = __import__("time").time()
    continuidades = {
        "comando_sugerido": "EXECUTE_INTENT",
        "comando_sugerido_payload": {
            "descricao": "diminuir o brilho",
            "preferencia_origem_chave": "TIME_WIND_DOWN",
            "intent": {"intent": "IOT_CONTROL", "params": {"acao": "ajustar_brilho"}},
        },
        "comando_sugerido_estado": "PENDING_CONFIRM",
        "comando_sugerido_ts": agora,
    }
    excecoes = []

    tratado = processar_confirmacao_sugestao({
        "continuidades_get": lambda chave, padrao=None: continuidades.get(chave, padrao),
        "classificar_confirmacao_local": lambda _texto: False,
        "resetar_sugestao": lambda: continuidades.update(comando_sugerido_estado="NONE"),
        "registrar_excecao_preferencia": lambda chave, texto: excecoes.append((chave, texto)),
        "falar": lambda *_args: None,
        "resposta_conversa_local": lambda _texto: "Tudo bem.",
        "sugestao_bloqueada_ate": {},
    }, "não, hoje deixa como está")

    assert tratado is True
    assert excecoes == [("TIME_WIND_DOWN", "não, hoje deixa como está")]
