# -*- coding: utf-8 -*-
# M1 / turno 149 — regressão da ponte de estado musical no coordenador.

from mente_laylay.autonomia.coordenador_intencao import (
    CicloComandosRuntime,
    DEPENDENCIAS_CICLO_COMANDOS,
)
from mente_laylay.autonomia.detectores_playlist import (
    detectar_playlist_contextual_musica_atual,
)


class _ContextoIntencaoFake:
    def __init__(self, dados):
        self._dados = dict(dados)

    def montar(self):
        return dict(self._dados)


def _runtime(contexto):
    return CicloComandosRuntime(
        namespace_getter=lambda: {},
        contexto_intencao_runtime=_ContextoIntencaoFake(contexto),
    )


def _limpar_nome_playlist(valor):
    return str(valor or "").strip(" .,!?:;")


def test_m1_wiring_repassa_getter_musical_do_contexto_tipado():
    def musica_estado_get(chave, default=None):
        return {"ultima_playlist": "caos sonora"}.get(chave, default)

    contexto = _runtime({
        "_musica_estado_get": musica_estado_get,
        "turno_atual": {},
        "retrato_turno_atual": {},
    })._montar_contexto_resolucao()

    assert contexto["musica_estado_get"] is musica_estado_get
    assert contexto["musica_estado_get"]("ultima_playlist", "") == "caos sonora"


def test_m1_wiring_alimenta_detector_com_playlist_recente():
    def musica_estado_get(chave, default=None):
        return {"ultima_playlist": "caos sonora"}.get(chave, default)

    contexto = _runtime({
        "_musica_estado_get": musica_estado_get,
        "turno_atual": {},
        "retrato_turno_atual": {},
    })._montar_contexto_resolucao()

    resultado = detectar_playlist_contextual_musica_atual(
        "adiciona essa também na caos sonora",
        params_cb=lambda **kwargs: kwargs,
        limpar_nome_playlist=_limpar_nome_playlist,
        ultima_playlist=contexto["musica_estado_get"](
            "ultima_playlist", ""
        ),
    )

    assert isinstance(resultado, dict), resultado
    assert resultado["intent"] == "PLAYLIST_ADD", resultado
    assert resultado["params"]["nome_playlist"] == "caos sonora", resultado
    assert resultado["params"].get("referencia_contextual") is True, resultado


def test_m1_wiring_nao_fabrica_estado_musical_quando_servico_ausente():
    contexto = _runtime({
        "turno_atual": {},
        "retrato_turno_atual": {},
    })._montar_contexto_resolucao()

    assert contexto.get("musica_estado_get") is None


def test_m1_wiring_getter_nao_vira_dependencia_global_do_ciclo():
    # O serviço pertence ao ContextoIntencaoRuntime. Esta regressão impede
    # "consertar" o wiring furando a composição do ciclo.
    assert "_musica_estado_get" not in DEPENDENCIAS_CICLO_COMANDOS
