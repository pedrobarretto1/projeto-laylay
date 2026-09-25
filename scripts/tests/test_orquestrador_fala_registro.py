from __future__ import annotations

import threading
import time

import pytest

from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional
from mente_laylay.integracao.politicas_composicao import construir_estado_visual
from mente_laylay.personalidade.diretor_fala import dirigir_fala

from mente_laylay.personalidade.orquestrador_fala_runtime import (
    DEPENDENCIAS_ORQUESTRADOR_FALA,
    OrquestradorFalaRuntime,
)


def _servicos_completos() -> dict:
    return {nome: object() for nome in DEPENDENCIAS_ORQUESTRADOR_FALA}


class _EstadoFala:
    def __init__(self, mental: dict) -> None:
        self.mental = dict(mental)
        self.conversacional: dict = {}

    def substituir(self, dominio: str, valor: dict) -> None:
        assert dominio == "mental"
        self.mental = dict(valor)


class _VozFalsa:
    def __init__(self, retornos=None) -> None:
        self.falas = []
        self.retornos = list(retornos or [True])

    def falar(self, *args, **kwargs):
        self.falas.append((args, kwargs))
        return self.retornos.pop(0) if self.retornos else True


def _runtime_de_fala(*, voz=None, turno_id="turno-1"):
    estado = _EstadoFala({
        "turno_atual": {"id": turno_id},
        "plano_turno_atual": {
            "id": turno_id,
            "fase": "planejado",
            "requer_execucao": True,
            "texto_usuario": "liga a luz",
        },
    })
    voz = voz or _VozFalsa()
    logs = []
    runtime = OrquestradorFalaRuntime(servicos_iniciais={
        "_registrar_mente_curta": lambda *_args, **_kwargs: None,
        "_estado_compartilhado_runtime": estado,
        "_encerrar_topico_mente": lambda mental, conversa, **_kwargs: (mental, conversa),
        "salvar_memoria": lambda: None,
        "print": logs.append,
        "_dirigir_fala_mente": lambda fala, **kwargs: {
            "fala": fala,
            "emocao": kwargs.get("emocao") or "calma",
            "nivel": kwargs.get("nivel") or 1,
        },
        "_voz_runtime": voz,
        "_registrar_continuidade_da_fala_mente": lambda mental, *_args, **_kwargs: mental,
        "_threading": threading,
        "_agendar_fala_proativa": lambda *_args, **_kwargs: False,
    })
    return runtime, estado, voz, logs


def _resultado_luz(*, cor="roxo", confirmado=True):
    return {
        "intent": "IOT_CONTROL",
        "status": "cor_ajustada",
        "alvo": "lampada_quarto",
        "params": {"acao": "ajustar_cor", "cor": cor},
        "confirmado": confirmado,
    }


def _publicar_alegria_causal(estado: _EstadoFala) -> None:
    evento = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="resultado positivo confirmado",
        evidencia_ref="resultado:turno:alegria", natureza_evidencia="fato_observado",
        responsabilidade="ambigua", confianca=0.96,
        permite_expressao=True, emocao="feliz", nivel=2,
        ts=time.time(),
    )
    estado.conversacional = aplicar_evento_emocional(
        estado.conversacional, evento,
    )


def test_diretor_final_nao_publica_tom_sem_episodio_causal() -> None:
    runtime, estado, voz, _logs = _runtime_de_fala()
    runtime.conectar_servicos({
        **runtime._servicos, "_dirigir_fala_mente": dirigir_fala,
    })
    estado.mental["especialistas_turno_atual"] = {
        "social": {"funcao": "elogio"}, "operacional": {"ativo": False},
    }
    publicados = []
    runtime.registrar_observador_texto_final(
        lambda _fala, emocao, nivel, **_kwargs:
        publicados.append((emocao, nivel)),
    )

    assert runtime.falar("Obrigada pelo elogio.")

    visual = construir_estado_visual(
        conversa_get=lambda chave, padrao=None: estado.conversacional.get(chave, padrao),
        plano_get=lambda: {},
    )
    esperado = (visual["emotion"], visual["level"])
    assert esperado == ("calma", 1)
    assert publicados == [esperado]
    assert voz.falas[-1][0][1:3] == esperado
    assert estado.mental["direcao_fala_atual"]["emocao"] == "calma"
    assert estado.mental["direcao_fala_atual"]["tom"] == "calma"


def test_orquestrador_consulta_namespace_legado_apenas_uma_vez() -> None:
    chamadas = []
    runtime = OrquestradorFalaRuntime(
        lambda: chamadas.append(True) or {"print": object(), "SEGREDO": object()}
    )

    runtime._ns()
    runtime._ns()
    assert chamadas == [True]
    assert runtime.servicos_registrados == ("print",)


def test_conexao_final_valida_filtra_e_congela_servicos() -> None:
    runtime = OrquestradorFalaRuntime(servicos_iniciais={})
    incompletos = _servicos_completos()
    incompletos.pop("_voz_runtime")
    with pytest.raises(RuntimeError, match="_voz_runtime"):
        runtime.conectar_servicos(incompletos)

    servicos = _servicos_completos()
    voz_final = servicos["_voz_runtime"]
    servicos["SEGREDO"] = object()
    runtime.conectar_servicos(servicos)
    servicos["_voz_runtime"] = object()
    servicos["novo"] = object()

    assert runtime._ns()["_voz_runtime"] is voz_final
    assert len(runtime.servicos_registrados) == len(DEPENDENCIAS_ORQUESTRADOR_FALA)
    assert "SEGREDO" not in runtime.servicos_registrados
    assert "novo" not in runtime.servicos_registrados


def test_mesmo_resultado_confirmado_fala_uma_unica_vez_no_turno() -> None:
    runtime, _estado, voz, logs = _runtime_de_fala()
    resultado = _resultado_luz()

    assert runtime.falar_resultado_operacional(
        resultado, "Pronto, deixei a luz roxa.", "debochada", 2,
    ) is True
    assert runtime.falar_resultado_operacional(
        resultado, "A lâmpada ficou roxa, bem bonitinha.", "feliz", 2,
    ) is True

    assert [chamada[0][0] for chamada in voz.falas] == ["Pronto, deixei a luz roxa."]
    assert any("duplicada suprimida" in linha for linha in logs)
    assert runtime.diagnostico()["duplicadas_suprimidas"] == 1


def test_resultados_operacionais_diferentes_preservam_duas_falas() -> None:
    runtime, _estado, voz, _logs = _runtime_de_fala()

    runtime.falar_resultado_operacional(_resultado_luz(cor="roxo"), "Ficou roxa.")
    runtime.falar_resultado_operacional(_resultado_luz(cor="azul"), "Agora ficou azul.")

    assert [chamada[0][0] for chamada in voz.falas] == [
        "Ficou roxa.", "Agora ficou azul.",
    ]


def test_novo_turno_pode_confirmar_novamente_o_mesmo_resultado() -> None:
    runtime, estado, voz, _logs = _runtime_de_fala()
    resultado = _resultado_luz()

    runtime.falar_resultado_operacional(resultado, "Ficou roxa.")
    estado.mental["turno_atual"] = {"id": "turno-2"}
    estado.mental["plano_turno_atual"] = {
        "id": "turno-2", "fase": "planejado", "requer_execucao": True,
    }
    runtime.falar_resultado_operacional(resultado, "Ficou roxa de novo.")

    assert [chamada[0][0] for chamada in voz.falas] == [
        "Ficou roxa.", "Ficou roxa de novo.",
    ]


def test_conversa_e_resultado_nao_confirmado_nao_sao_silenciados() -> None:
    runtime, estado, voz, _logs = _runtime_de_fala()
    estado.mental["plano_turno_atual"]["requer_execucao"] = False

    runtime.falar("Eu tô aqui.")
    runtime.falar("Eu tô aqui.")
    runtime.falar_resultado_operacional(
        _resultado_luz(confirmado=False), "A lâmpada não respondeu.",
    )
    runtime.falar_resultado_operacional(
        _resultado_luz(confirmado=False), "Ainda não respondeu.",
    )

    assert len(voz.falas) == 4


def test_rejeicao_da_voz_libera_nova_tentativa_do_resultado() -> None:
    runtime, _estado, voz, _logs = _runtime_de_fala(
        voz=_VozFalsa([False, True]),
    )
    resultado = _resultado_luz()

    assert runtime.falar_resultado_operacional(resultado, "Ficou roxa.") is False
    assert runtime.falar_resultado_operacional(resultado, "Ficou roxa.") is True

    assert len(voz.falas) == 2
    diagnostico = runtime.diagnostico()
    assert diagnostico["rejeitadas_voz"] == 1
    assert diagnostico["emitidas"] == 1


def test_observador_recebe_apenas_fala_aceita_pela_fronteira_final() -> None:
    runtime, _estado, _voz, _logs = _runtime_de_fala(
        voz=_VozFalsa([False, True]),
    )
    _publicar_alegria_causal(_estado)
    publicadas = []
    runtime.registrar_observador_fala_final(
        lambda texto, emocao, nivel, **dados: publicadas.append(
            (texto, emocao, nivel, dados),
        )
    )

    assert runtime.falar("candidato recusado") is False
    assert runtime.falar("resposta consolidada", "feliz", 2) is True

    assert publicadas == [
        (
            "resposta consolidada", "feliz", 2,
            {"proativa": False, "mensagem_id": "turno:turno-1"},
        ),
    ]
    assert _voz.falas[-1][1]["_texto_publicado_antecipado"] is True


def test_texto_final_chega_ao_terminal_mesmo_se_a_voz_recusar() -> None:
    runtime, _estado, voz, _logs = _runtime_de_fala(
        voz=_VozFalsa([False]),
    )
    _publicar_alegria_causal(_estado)
    publicadas = []
    runtime.registrar_observador_texto_final(
        lambda texto, emocao, nivel, **dados: publicadas.append(
            (texto, emocao, nivel, dados),
        ) or True
    )

    assert runtime.falar("Resposta visual independente.", "feliz", 2) is False

    assert publicadas == [(
        "Resposta visual independente.", "feliz", 2,
        {"proativa": False, "mensagem_id": "turno:turno-1"},
    )]
    assert voz.falas[-1][1]["_texto_publicado_antecipado"] is True


def test_publicacao_visual_imediata_registra_latencia_sem_esperar_audio() -> None:
    runtime, _estado, voz, _logs = _runtime_de_fala()
    metricas = []
    runtime.conectar_servicos({
        **runtime._servicos,
        "_registrar_metrica_diagnostico": (
            lambda *args, **kwargs: metricas.append((args, kwargs))
        ),
    })
    publicadas = []
    runtime.registrar_observador_fala_final(
        lambda texto, *_args, **_kwargs: publicadas.append(texto) or True
    )

    assert runtime.falar("Resposta pronta.") is True

    assert publicadas == ["Resposta pronta."]
    assert voz.falas[-1][1]["wait"] is False
    assert any(
        args[0] == "tts_texto_visivel" and kwargs["fase"] == "texto_final"
        for args, kwargs in metricas
    )



def test_fronteira_operacional_preserva_sucesso_confirmado() -> None:
    runtime, _estado, voz, _logs = _runtime_de_fala()
    resultado = {
        "intent": "APP_OPEN",
        "status": "app_aberto",
        "alvo": "Chrome",
        "executou": True,
        "confirmado": True,
    }

    runtime.falar_resultado_operacional(
        resultado,
        "Pronto, abri o Chrome.",
    )

    assert voz.falas[-1][0][0] == "Pronto, abri o Chrome."


def test_fronteira_operacional_corrige_sucesso_sem_confirmacao() -> None:
    runtime, _estado, voz, logs = _runtime_de_fala()
    resultado = {
        "intent": "APP_OPEN",
        "status": "app_aberto",
        "alvo": "Chrome",
        "executou": True,
        "confirmado": None,
    }

    runtime.falar_resultado_operacional(
        resultado,
        "Pronto, abri o Chrome.",
    )

    fala = voz.falas[-1][0][0].casefold()
    assert "comando foi enviado" in fala
    assert "não consegui confirmar" in fala
    assert "pronto, abri" not in fala
    assert any("GUARDIÃO:RESULTADO" in linha for linha in logs)


def test_fronteira_operacional_corrige_acao_nao_confirmada() -> None:
    runtime, _estado, voz, logs = _runtime_de_fala()
    resultado = {
        "intent": "APP_OPEN",
        "status": "falha_confirmacao_app",
        "alvo": "Chrome",
        "executou": False,
        "confirmado": False,
    }

    runtime.falar_resultado_operacional(
        resultado,
        "Pronto, abri o Chrome.",
    )

    fala = voz.falas[-1][0][0].casefold()
    assert "não foi executada nem confirmada" in fala
    assert "pronto, abri" not in fala
    assert any("GUARDIÃO:RESULTADO" in linha for linha in logs)


def test_fronteira_operacional_valida_resultado_acao_real_sem_confirmacao() -> None:
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao

    runtime, _estado, voz, logs = _runtime_de_fala()
    resultado = ResultadoAcao(
        intent="APP_OPEN",
        status="app_aberto",
        alvo="Chrome",
        executou=True,
        confirmado=None,
        confirmacao_oferecida="visual",
        evidencia_confirmacao="janela_visivel",
    )

    runtime.falar_resultado_operacional(
        resultado,
        "Pronto, abri o Chrome.",
    )

    fala = voz.falas[-1][0][0].casefold()
    assert "comando foi enviado" in fala
    assert "não consegui confirmar" in fala
    assert "pronto, abri" not in fala
    assert any("GUARDIÃO:RESULTADO" in linha for linha in logs)


def test_fronteira_operacional_falha_fechada_se_resultado_nao_serializa() -> None:
    class _ResultadoQuebrado:
        def como_dict(self):
            raise RuntimeError("receipt corrompido")

    runtime, _estado, voz, logs = _runtime_de_fala()

    runtime.falar_resultado_operacional(
        _ResultadoQuebrado(),
        "Pronto, abri o Chrome.",
    )

    fala = voz.falas[-1][0][0].casefold()
    assert "não consegui validar o resultado dessa ação com segurança" in fala
    assert "pronto, abri" not in fala
    assert any("GUARDIÃO:RESULTADO" in linha for linha in logs)


@pytest.mark.parametrize("bruto", [None, {}, [], "receipt inválido"])
@pytest.mark.parametrize("fala", ["Pronto, abri o Chrome.", "Salvei o arquivo.", "Liguei a luz."])
def test_receipt_inutilizavel_nao_chega_como_sucesso_ao_texto_ou_voz(bruto, fala):
    from types import SimpleNamespace
    runtime, estado, voz, logs = _runtime_de_fala()
    textos = []
    runtime.registrar_observador_texto_final(lambda texto, *a, **kw: textos.append(texto))
    resultado = SimpleNamespace(como_dict=lambda: bruto)
    assert runtime.falar_resultado_operacional(resultado, fala)
    assert textos == [voz.falas[-1][0][0]]
    assert "não consegui validar o resultado" in textos[0].casefold()
    assert estado.mental["ultima_resposta"] == textos[0]
    assert runtime.diagnostico()["resultados_retidos"] == 0


def test_receipt_corrompido_nao_reserva_confirmacao_de_recibo_posterior_valido():
    class Corrompido:
        intent = "APP_OPEN"
        status = "app_aberto"
        alvo = "Chrome"
        confirmado = True
        def como_dict(self):
            raise RuntimeError("corrompido")
    runtime, _, voz, _ = _runtime_de_fala()
    runtime.falar_resultado_operacional(Corrompido(), "Pronto, abri o Chrome.")
    assert runtime.diagnostico()["resultados_retidos"] == 0
    valido = dict(intent="APP_OPEN", status="app_aberto", alvo="Chrome", confirmado=True, executou=True)
    runtime.falar_resultado_operacional(valido, "Pronto, abri o Chrome.")
    assert len(voz.falas) == 2
    assert voz.falas[-1][0][0] == "Pronto, abri o Chrome."


def test_atributo_serializador_corrompido_ainda_tem_conclusao_observavel():
    class Corrompido:
        @property
        def como_dict(self):
            raise ValueError("atributo indisponível")
    runtime, _, voz, _ = _runtime_de_fala()
    assert runtime.falar_resultado_operacional(Corrompido(), "Feito.")
    assert "não consegui validar" in voz.falas[-1][0][0].casefold()


def test_receipt_invalido_atravessa_diretor_e_fila_reais_sem_sucesso_falso():
    from mente_laylay.personalidade.diretor_fala import dirigir_fala
    from mente_laylay.personalidade.voz_runtime import VozRuntime
    voz = VozRuntime(
        fallback_fala="fallback", voice="voz", edge_tts_mod=None,
        sounddevice_mod=None, soundfile_mod=None, pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **kw: texto,
        ducking_volume_cb=lambda *_: None,
        modular_audio_params_cb=lambda *_: ("", "", ""),
        compor_fala_proativa_cb=lambda itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_: None,
        interrupt_event=threading.Event(),
    )
    # Só a reprodução física é excluída; usamos direção e enfileiramento reais.
    voz.worker_started = True
    runtime, estado, _, _ = _runtime_de_fala(voz=voz)
    runtime.conectar_servicos({**runtime._servicos, "_dirigir_fala_mente": dirigir_fala})
    textos = []
    runtime.registrar_observador_texto_final(lambda texto, *a, **kw: textos.append(texto))
    assert runtime.falar_resultado_operacional(None, "Pronto, salvei o arquivo.")
    pedido = voz.fila.get_nowait()
    assert "não consegui validar" in pedido["texto"].casefold()
    assert textos == [pedido["texto"]]
    assert estado.mental["ultima_resposta"] == pedido["texto"]
