from __future__ import annotations

from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.integracao.adaptadores_aplicacao_runtime import (
    AdaptadoresAplicacaoRuntime,
)
from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
from mente_laylay.memoria_mental.disponibilidade_operacional import (
    DisponibilidadeOperacionalRuntime,
)
from mente_laylay.memoria_mental.diagnostico_mente import DiagnosticoMenteRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.estado_continuidades import (
    estado_continuidades_inicial,
)
from mente_laylay.memoria_mental.estado_musical import estado_musical_inicial
from mente_laylay.memoria_mental.estado_percepcao import estado_percepcao_inicial
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime
from mente_laylay.memoria_mental.saude_mente import SaudeMenteRuntime


def _disponibilidade(**substituicoes):
    getters = {
        "navegador_leitura_getter": lambda: {
            "conectado": False,
            "leitura_aba_disponivel": True,
            "listagem_disponivel": True,
        },
        "navegador_operacoes_getter": lambda: {
            "comandos_disponiveis": True,
            "navegacao_disponivel": True,
        },
        "conversa_llm_getter": lambda: {
            "modelo_disponivel": True,
            "estado_disponivel": True,
            "estado": "saudavel",
            "falhas_consecutivas": 0,
        },
        "visao_leitura_getter": lambda: {
            "habilitado": True,
            "credencial_disponivel": True,
        },
        "visao_analise_getter": lambda: {"analise_disponivel": True},
        "area_transferencia_getter": lambda: {
            "leitura_disponivel": True,
            "escrita_disponivel": True,
            "investigacao_disponivel": True,
        },
        "caixa_entrada_getter": lambda: {"persistencia_disponivel": True},
        "notificacoes_getter": lambda: {"persistencia_disponivel": True},
        "iot_getter": lambda: {
            "configurado": True,
            "provedor_disponivel": True,
            "total_dispositivos": 2,
        },
        "avatar_getter": lambda: {
            "preferencia_ativa": False,
            "assets_disponiveis": True,
            "processo_ativo": False,
            "visual_externo_ativo": False,
        },
    }
    getters.update(substituicoes)
    return DisponibilidadeOperacionalRuntime(**getters)


def test_chrome_desconectado_nao_aparece_como_navegador_disponivel() -> None:
    operacional = _disponibilidade()
    mapa = MapaHabilidadesRuntime(
        operacional_getter=operacional.snapshot,
    )

    snapshot = mapa.snapshot()

    assert snapshot["dominios"]["navegador"]["estado"] == "indisponivel"
    assert snapshot["capacidades"]["OPEN_URL"]["disponivel"] is False
    assert snapshot["capacidades"]["RESUMIR_PAGINA"]["disponivel"] is False
    assert "chrome_ws_conectado" in snapshot["capacidades"]["OPEN_URL"]["ausentes"]
    assert "não está disponível" in mapa.responder_pergunta_capacidade(
        "Lay, você consegue resumir a página atual?"
    ).casefold()


def test_provedor_ou_credencial_ausente_degrada_capacidade_correta() -> None:
    operacional = _disponibilidade(
        conversa_llm_getter=lambda: {
            "modelo_disponivel": False,
            "estado_disponivel": False,
            "estado": "indisponivel",
        },
        visao_leitura_getter=lambda: {
            "habilitado": True,
            "credencial_disponivel": False,
        },
    )
    snapshot = operacional.snapshot()

    assert snapshot["dominios"]["conversa"]["estado"] == "indisponivel"
    assert "modelo_ou_provedor" in snapshot["dominios"]["conversa"]["ausentes"]
    assert snapshot["dominios"]["visao"]["estado"] == "indisponivel"
    assert "credencial_visao" in snapshot["dominios"]["visao"]["ausentes"]


def test_avatar_depende_de_preferencia_recursos_e_processo_real() -> None:
    desligado = _disponibilidade().snapshot()["dominios"]["avatar"]
    ativo = _disponibilidade(
        avatar_getter=lambda: {
            "preferencia_ativa": True,
            "assets_disponiveis": True,
            "processo_ativo": True,
            "visual_externo_ativo": False,
        },
    ).snapshot()["dominios"]["avatar"]

    assert desligado["estado"] == "indisponivel"
    assert desligado["motivo"] == "preferencia_desativada"
    assert ativo["estado"] == "disponivel"
    assert ativo["evidencia_recente"] is True


def _estado() -> EstadoCompartilhadoRuntime:
    return EstadoCompartilhadoRuntime(
        continuidades=estado_continuidades_inicial(),
        musical=estado_musical_inicial(),
        percepcao=estado_percepcao_inicial(),
        mental=estado_mental_inicial(),
        conversacional={"current_emotion": "calma", "is_speaking": False},
        memoria_conversa={"messages": [], "memoria_fatos": [], "memoria_eventos": []},
    )


def test_validador_detecta_pendencia_ligada_a_estado_privado() -> None:
    estado = _estado()
    privado = {"pendencia_acao_canonica": {}}
    pendencia_privada = PendenciaAcaoRuntime(
        estado_getter=lambda: privado,
        estado_atualizar=lambda atualizador: atualizador(privado),
        log=lambda *_args: None,
    )

    validacao = estado.validar_estrutura(conexoes={
        "estado_compartilhado": estado,
        "pendencia_runtime": pendencia_privada,
        "classificador_confirmacao": lambda _texto: None,
        "motor_aprendizado": object(),
    })

    assert validacao["ok"] is False
    assert "pendencia_runtime:estado_privado" in validacao["invalidos"]
    assert "motor_aprendizado.registrar_feedback_contextual" in validacao["ausentes"]


def test_retrato_operacional_inclui_dominios_antes_omitidos() -> None:
    snapshot = _disponibilidade().snapshot()

    for dominio in (
        "area_transferencia", "caixa_entrada", "email", "iot", "avatar",
        "navegador", "visao", "conversa",
    ):
        assert dominio in snapshot["dominios"]
    assert snapshot["probes_executados"] is False
    assert snapshot["fonte"] == "diagnosticos_dos_runtimes"


def test_diagnostico_distingue_estrutura_de_disponibilidade_e_fala_a_limitacao() -> None:
    falas: list[str] = []
    logs: list[str] = []
    runtime = DiagnosticoMenteRuntime(
        estado_getter=lambda: {
            "mental": {}, "conversacional": {}, "percepcao": {},
            "continuidades": {},
        },
        saude_getter=lambda: {"mente": {"status": "saudavel"}},
        estrutura_getter=lambda: {"ok": True, "ausentes": [], "invalidos": []},
        disponibilidade_operacional_getter=_disponibilidade().snapshot,
        falar=lambda texto, *_args: falas.append(texto),
        log=logs.append,
    )

    diagnostico = runtime.mostrar()

    assert diagnostico["saude"]["degradado"] == 0
    assert diagnostico["saude_operacional"]["estado"] == "degradado"
    assert "navegador" in diagnostico["saude_operacional"]["capacidades_indisponiveis"]
    assert "disponibilidade limitada em" in falas[0]
    assert "navegador" in falas[0]
    assert "disponibilidade operacional:" in logs[0]


class _ConexaoValidavel:
    def validar_conexoes(self) -> None:
        return None


class _Diagnostico:
    def __init__(self, dados: dict) -> None:
        self._dados = dados

    def diagnostico(self) -> dict:
        return dict(self._dados)


class _Motor:
    def registrar_feedback_contextual(self, **_dados):
        return None


def test_auditoria_nao_confunde_callable_com_disponibilidade_real() -> None:
    estado = _estado()
    pendencia = PendenciaAcaoRuntime(
        estado_getter=lambda: estado.mental,
        estado_atualizar=lambda atualizador: estado.atualizar(
            "mental", atualizador,
        ),
        log=lambda *_args: None,
    )
    saude = SaudeMenteRuntime()
    navegador_leitura = _Diagnostico({
        "conectado": False,
        "leitura_aba_disponivel": True,
        "listagem_disponivel": True,
    })
    navegador_operacoes = _Diagnostico({
        "comandos_disponiveis": True,
        "navegacao_disponivel": True,
    })
    ns = {
        "_estado_compartilhado_runtime": estado,
        "_saude_mente_runtime": saude,
        "_pendencia_acao_runtime": pendencia,
        "_classificar_confirmacao_local": lambda _texto: None,
        "_motor_aprendizado_runtime": _Motor(),
        "_aprendizado_runtime": None,
        "_chrome_ws_contexto_runtime": _ConexaoValidavel(),
        "_contexto_intencao_runtime": _ConexaoValidavel(),
        "_ciclo_comandos_runtime": _ConexaoValidavel(),
        "falar_com_lipsync": lambda *_args: None,
        "carregar_memoria": lambda: None,
        "salvar_memoria": lambda: None,
        "_gmail_buscar_nao_lidos": lambda: [],
        "gmail_daemon": lambda: None,
        "run_ws_server_in_thread": lambda: None,
        "_registro_modelo_llm_runtime": _Diagnostico({"disponivel": True}),
        "_registro_navegador_leitura_runtime": navegador_leitura,
        "_registro_navegador_operacoes_runtime": navegador_operacoes,
        "_registro_iot_runtime": _Diagnostico({
            "configurado": True,
            "provedor_disponivel": False,
            "total_dispositivos": 2,
        }),
        "_area_transferencia_runtime": _Diagnostico({"leitura_disponivel": True}),
        "_caixa_entrada_pessoal_runtime": _Diagnostico({"persistencia_disponivel": True}),
        "_central_notificacoes_runtime": _Diagnostico({"persistencia_disponivel": True}),
        "_avatar_runtime": _Diagnostico({
            "preferencia_ativa": False,
            "assets_disponiveis": True,
            "processo_ativo": False,
        }),
        "_agenda_runtime": _Diagnostico({"disponivel": True}),
        "print": lambda *_args: None,
    }
    runtime = AdaptadoresAplicacaoRuntime(namespace_getter=lambda: ns)

    runtime.auditar_saude_mente()
    snapshot = saude.snapshot()

    assert snapshot["navegador"]["status"] == "degradado"
    assert snapshot["navegador_tipado"]["status"] == "degradado"
    assert snapshot["navegador"]["ausentes"] == ["chrome_ws_conectado"]
    assert snapshot["iot"]["status"] == "indisponivel"
    assert snapshot["area_transferencia"]["status"] == "saudavel"
