from __future__ import annotations

from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


class _MemoriaEvidencias:
    def __init__(self) -> None:
        self.eventos: list[dict] = []

    def registrar_evidencia_aprendizado(self, **dados):
        self.eventos.append(dict(dados))
        return {"chave": dados["chave"], "confianca": 0.1, "status": "candidata"}


def test_pendencia_expirada_so_ensina_silencio_apos_dez_minutos_sem_resposta():
    memoria = _MemoriaEvidencias()
    motor = MotorAprendizadoRuntime(
        memoria_sqlite=memoria, contexto_getter=lambda: {}, log=lambda *_: None,
    )
    base = {
        "origem": "caixa_entrada_pessoal", "acao": "guardar nota",
        "referencia": "nota recente", "pergunta": "Quer guardar a nota?",
        "status": "expirada", "criada_em": 100.0,
    }

    assert motor.observar_evento_pendencia(
        "expirada", {**base, "encerrada_em": 400.0},
    ) is None
    assert motor.observar_evento_pendencia(
        "expirada", {**base, "encerrada_em": 700.0, "respondida_em": 650.0},
    ) is None
    assert memoria.eventos == []

    registrado = motor.observar_evento_pendencia(
        "expirada", {**base, "encerrada_em": 700.0},
    )

    assert registrado is not None
    assert len(memoria.eventos) == 1
    assert memoria.eventos[0]["sinal"] < 0
    assert memoria.eventos[0]["confirmado_usuario"] is False


def test_confirmacao_de_exclusao_expirada_nao_vira_preferencia_pessoal():
    memoria = _MemoriaEvidencias()
    motor = MotorAprendizadoRuntime(
        memoria_sqlite=memoria, contexto_getter=lambda: {}, log=lambda *_: None,
    )

    resultado = motor.observar_evento_pendencia("expirada", {
        "origem": "lixeira_laylay", "acao": "confirmar exclusao",
        "pergunta": "Confirma excluir?", "referencia": "arquivo",
        "status": "expirada", "criada_em": 100.0, "encerrada_em": 800.0,
    })

    assert resultado["persistido"] is False
    assert memoria.eventos == []


def test_pendencia_canonica_publica_silencio_somente_apos_prazo_qualificado():
    memoria = _MemoriaEvidencias()
    motor = MotorAprendizadoRuntime(
        memoria_sqlite=memoria, contexto_getter=lambda: {}, log=lambda *_: None,
    )
    instante = [100.0]
    estado: dict = {}

    def atualizar(transformar):
        novo = transformar(dict(estado))
        estado.clear()
        estado.update(novo)
        return estado

    pendencias = PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        agora=lambda: instante[0],
        evento_cb=motor.observar_evento_pendencia,
        log=lambda *_: None,
    )
    pendencias.registrar(
        origem="caixa_entrada_pessoal", acao="guardar nota",
        pergunta="Quer guardar a nota?", referencia="nota 1", ttl_s=300.0,
    )
    instante[0] = 400.0
    assert pendencias.obter() is None
    assert memoria.eventos == []

    pendencias.registrar(
        origem="caixa_entrada_pessoal", acao="guardar nota",
        pergunta="Quer guardar a nota?", referencia="nota 2", ttl_s=600.0,
    )
    instante[0] = 1000.0
    assert pendencias.obter() is None
    assert len(memoria.eventos) == 1
    assert memoria.eventos[0]["valor"]["alvo"] == "nota 2"
