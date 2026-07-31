from mente_laylay.autonomia.execucao_ia import CoordenadorExecRuntime
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime
from mente_laylay.percepcao.observador_area_transferencia import (
    classificar_resposta_oferta,
    oferta_deve_ceder_a_novo_comando,
)


def _runtime(agora=lambda: 100.0):
    estado = EstadoCompartilhadoRuntime(mental={})
    runtime = PendenciaAcaoRuntime(
        estado_getter=lambda: estado.mental,
        estado_atualizar=lambda atualizar: estado.atualizar("mental", atualizar),
        agora=agora,
        log=lambda *_args: None,
    )
    return runtime, estado


def test_confirmacao_natural_e_consumida_antes_da_llm_pela_composicao_real() -> None:
    pendencias, _estado = _runtime()
    criada = pendencias.registrar(
        origem="observador_area_transferencia",
        acao="investigar_erro",
        pergunta="Quer que eu investigue?",
        referencia="hash-erro",
    )
    executadas, chamadas_llm = [], []

    def processar_prioritario(texto: str) -> bool:
        resultado = pendencias.resolver(
            texto,
            classificar_dominio=classificar_resposta_oferta,
        )
        if resultado.get("status") == "aceitar":
            executadas.append(resultado["pendencia"]["acao"])
            pendencias.concluir(resultado["pendencia"]["id"], "concluida")
        return bool(resultado.get("tratado"))

    turnos = []
    contexto = {
        "marcar_inicio_turno": lambda texto: turnos.append(texto),
        "obter_turno_atual": lambda: {},
        "processar_comandos_prioritarios": processar_prioritario,
        "enviar_mensagem": lambda texto, **_kwargs: chamadas_llm.append(texto),
    }
    resposta = RespostaIARuntime(
        contexto_getter=lambda: contexto,
        log=lambda *_args: None,
    )

    coordenador = CoordenadorExecRuntime(
        contexto_exec_getter=lambda: None,
        resposta_ia_getter=lambda: resposta,
        loop_getter=lambda: None,
        log=lambda *_args: None,
    )
    thread = coordenador.agendar("quero sim")
    thread.join(timeout=2)

    assert criada
    assert turnos == ["quero sim"]
    assert executadas == ["investigar_erro"]
    assert chamadas_llm == []
    assert pendencias.obter() is None


def test_aceite_e_atomico_e_nao_executa_duas_vezes() -> None:
    runtime, _estado = _runtime()
    runtime.registrar(
        origem="observador_area_transferencia",
        acao="investigar_erro",
        pergunta="Quer que eu investigue?",
    )

    primeira = runtime.resolver("pode sim", classificar_dominio=classificar_resposta_oferta)
    segunda = runtime.resolver("sim", classificar_dominio=classificar_resposta_oferta)

    assert primeira["status"] == "aceitar"
    assert segunda["status"] == "em_processamento"


def test_recusa_natural_encerra_sem_autorizar() -> None:
    runtime, _estado = _runtime()
    criada = runtime.registrar(
        origem="observador_area_transferencia",
        acao="investigar_erro",
        pergunta="Quer que eu investigue?",
    )

    resposta = runtime.resolver("agora não", classificar_dominio=classificar_resposta_oferta)
    runtime.concluir(criada["id"], "recusada")

    assert resposta["status"] == "recusar"
    assert runtime.obter() is None


def test_oferta_opcional_cede_a_comando_novo_sem_classifica_lo_como_recusa() -> None:
    eh_comando = lambda texto: texto.startswith("coloca ") or texto == "essa também"

    assert oferta_deve_ceder_a_novo_comando(
        "coloca essa musica na playlist sendo sendo",
        "explicar_codigo",
        texto_tem_comando_explicito=eh_comando,
    ) is True
    assert oferta_deve_ceder_a_novo_comando(
        "essa também",
        "resumir_texto",
        texto_tem_comando_explicito=eh_comando,
    ) is True
    assert oferta_deve_ceder_a_novo_comando(
        "quero sim",
        "resumir_texto",
        texto_tem_comando_explicito=eh_comando,
    ) is False
    assert oferta_deve_ceder_a_novo_comando(
        "não, deixa quieto",
        "resumir_texto",
        texto_tem_comando_explicito=eh_comando,
    ) is False


def test_resposta_indireta_usa_interpretacao_contextual_compartilhada() -> None:
    runtime, _estado = _runtime()
    runtime.registrar(
        origem="observador_area_transferencia",
        acao="investigar_erro",
        pergunta="Quer que eu investigue?",
    )
    consultas = []

    resposta = runtime.resolver(
        "seria ótimo",
        classificar_dominio=classificar_resposta_oferta,
        classificar_contextual=lambda texto, pergunta: consultas.append((texto, pergunta)) or True,
    )

    assert resposta["status"] == "aceitar"
    assert consultas == [("seria ótimo", "Quer que eu investigue?")]


def test_pendencia_expira_sem_chegar_a_llm_como_confirmacao_valida() -> None:
    relogio = [100.0]
    runtime, _estado = _runtime(agora=lambda: relogio[0])
    runtime.registrar(
        origem="observador_area_transferencia",
        acao="investigar_erro",
        pergunta="Quer que eu investigue?",
        ttl_s=5,
    )
    relogio[0] = 106.0

    assert runtime.obter() is None
    assert runtime.resolver("sim")["status"] == "sem_pendencia"
