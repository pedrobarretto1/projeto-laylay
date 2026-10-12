"""Consultar o significado de um ato não autoriza suas operações mencionadas."""
import pytest

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import (
    autoriza_execucao_efetiva,
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
    extrair_nucleo_pedido_operacional,
)
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto


ACOES = ("abrir a calculadora", "pausar a música", "ligar a luz", "apagar o arquivo notas.txt")


def classificar(texto, normalizador=True, detector=True):
    return classificar_modalidade_turno(
        texto,
        normalizar_texto=normalizar_texto if normalizador else None,
        texto_tem_comando_explicito=texto_tem_comando_explicito if detector else None,
        confirmacao_contextual_valida=True,
    )


@pytest.mark.parametrize("acao", ACOES)
@pytest.mark.parametrize("predicado", ["significa o quê", "quer dizer o que"])
@pytest.mark.parametrize("pontuacao", ["?", ""])
@pytest.mark.parametrize("portas", [(False, True), (True, True), (False, False)])
def test_predicado_discursivo_governa_o_ato_inteiro(acao, predicado, pontuacao, portas):
    texto = f"Pode {acao} {predicado}{pontuacao}"
    turno = classificar(texto, *portas)
    assert len(turno["segmentos"]) == 1
    assert not autoriza_execucao_efetiva(turno), turno
    assert turno["texto_operacional"] == ""
    assert turno["veto_execucao_operacional"] is True
    assert bloqueia_execucao_operacional_prioritaria(texto, classificacao=turno)
    assert extrair_nucleo_pedido_operacional(texto) is None


@pytest.mark.parametrize("texto", [
    "Pode abrir a calculadora e fechar o navegador significa o quê?",
    "Abre a calculadora e pausa a música significa o quê",
    "Pode abrir a calculadora e fechar o navegador, significa o quê?",
])
def test_expressao_consultada_nao_libera_primeira_operacao_do_conjunto(texto):
    turno = classificar(texto)
    assert len(turno["segmentos"]) == 1, turno["segmentos"]
    assert not autoriza_execucao_efetiva(turno)
    assert turno["texto_operacional"] == ""


@pytest.mark.parametrize("texto", [
    "Pode abrir a calculadora significa o quê? Pausa a música.",
    "Pode abrir a calculadora significa o quê; pausa a música.",
    "Pausa a música; pode abrir a calculadora significa o quê?",
    "Pausa a música. Pode abrir a calculadora e fechar o navegador significa o quê?",
    "Pode abrir a calculadora significa o quê e pausa a música.",
    "Pode abrir a calculadora significa o quê, mas pausa a música.",
])
def test_pergunta_nao_empresta_autoridade_da_ordem_independente(texto):
    turno = classificar(texto)
    assert len(turno["segmentos"]) == 2, turno["segmentos"]
    assert autoriza_execucao_efetiva(turno)
    assert "pausa a música" in turno["texto_operacional"]
    assert "calculadora" not in turno["texto_operacional"]
    assert len([s for s in turno["segmentos"] if s["autoriza_execucao"]]) == 1


@pytest.mark.parametrize("texto", [
    'Pode abrir o arquivo "isso significa o quê.txt"?',
    'Pode abrir o arquivo “quer dizer o quê.txt”?',
    "Pode abrir a calculadora?",
    "Pode pausar a música",
])
def test_pergunta_polida_e_literal_nao_recebem_veto_por_palavra_solto(texto):
    assert autoriza_execucao_efetiva(classificar(texto))


def test_ordem_e_explicacao_independente_nao_viram_mencao_integral():
    turno = classificar("Abre a calculadora e me explica o que significa API?")
    assert autoriza_execucao_efetiva(turno)
    assert "abre a calculadora" in turno["texto_operacional"]
    assert "api" not in turno["texto_operacional"]


@pytest.mark.parametrize("texto,autoriza", [
    ("Pode abrir a calculadora significa o quê?", False),
    ("Pode ligar a luz significa o quê", False),
    ("Pode abrir a calculadora e fechar o navegador significa o quê?", False),
    ("Pausa a música; pode abrir a calculadora significa o quê?", True),
    ("Pode abrir a calculadora significa o quê? Pausa a música.", True),
])
def test_consumidor_nao_reinterpreta_consulta_como_cadeia_autorizada(texto, autoriza):
    from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime

    turno = classificar(texto)
    estado = EstadoCompartilhadoRuntime(mental={"turno_atual": turno})
    recebidos = []
    executadas = []
    ns = {
        "_estado_compartilhado_runtime": estado,
        "_normalizar_texto_com_apelidos": normalizar_texto,
        "_texto_tem_comando_explicito": texto_tem_comando_explicito,
        "processar_comandos_em_cadeia": lambda trecho, origem: recebidos.append(trecho) or True,
        # Um detector agressivo não deve ressuscitar autoridade negada.
        "detectar_intencao_deterministica": lambda _texto: {"intent": "APP_OPEN", "params": {"nome_app": "calculadora"}},
        "executar_intencao": lambda *args, **kwargs: executadas.append(args) or True,
    }
    runtime = ComandosImediatosRuntime(namespace_getter=lambda: ns, loop_getter=lambda: None)
    assert runtime.processar_prioritarios(texto) is autoriza
    assert recebidos == ([turno["texto_operacional"]] if autoriza else [])
    assert executadas == []
    assert dict(estado.mental["turno_atual"]) == turno


@pytest.mark.parametrize("acao", ["open_app", "youtube_control", "ligar", "delete_item"])
def test_comando_proposto_pela_llm_nao_recupera_autoridade_da_consulta(acao):
    from mente_laylay.autonomia.processamento_resposta_ia import filtrar_comandos_sem_pedido_atual

    permitidos, bloqueados = filtrar_comandos_sem_pedido_atual(
        "Pode abrir a calculadora e fechar o navegador significa o quê?",
        [{"acao": acao, "params": {}}],
    )
    assert permitidos == []
    assert bloqueados == [acao]
