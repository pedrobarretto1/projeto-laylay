"""Uma condição não observada não vira autorização ao cortar sua consequência."""
import pytest

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import (
    autoriza_execucao_efetiva,
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto


ORDENS = ("abre a calculadora", "pausa a música", "liga a luz", "apaga o arquivo notas.txt")


def classificar(texto, normalizador=True):
    return classificar_modalidade_turno(
        texto,
        normalizar_texto=normalizar_texto if normalizador else None,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
        # Uma oferta anterior válida não satisfaz a condição deste novo pedido.
        confirmacao_contextual_valida=True,
    )


@pytest.mark.parametrize("ordem", ORDENS)
@pytest.mark.parametrize("moldura", [
    "Quando eu disser pronto, {}.",
    "Quando eu disser pronto {}.",
    "Só quando eu confirmar, {}.",
    "Se eu confirmar depois, {}.",
    "Caso eu dê autorização, {}.",
    "{} só se eu confirmar depois.",
    "{} apenas se eu autorizar.",
    "{}, só se eu confirmar depois.",
    "Quando eu disser pronto; {}.",
])
@pytest.mark.parametrize("normalizador", [False, True])
def test_condicao_e_consequencia_nao_concedem_autoridade_agora(ordem, moldura, normalizador):
    texto = moldura.format(ordem)
    turno = classificar(texto, normalizador)
    assert len(turno["segmentos"]) == 1, turno["segmentos"]
    assert not autoriza_execucao_efetiva(turno), turno
    assert turno["texto_operacional"] == ""
    assert bloqueia_execucao_operacional_prioritaria(texto, classificacao=turno)


@pytest.mark.parametrize("texto", [
    "Quando eu confirmar, abre a calculadora e pausa a música.",
    "Só quando eu confirmar, liga a luz e desliga o ventilador.",
    "Abre a calculadora e pausa a música só se eu confirmar depois.",
])
def test_conjunto_dependente_nao_perde_condicao(texto):
    turno = classificar(texto)
    assert not autoriza_execucao_efetiva(turno), turno["segmentos"]
    assert turno["texto_operacional"] == ""


def test_qualificador_posposto_com_verbo_na_condicao_nao_e_outra_ordem():
    turno = classificar("Abre a calculadora, se eu abrir o navegador.")
    assert not autoriza_execucao_efetiva(turno)


@pytest.mark.parametrize("texto", [
    "Abre a calculadora agora; quando eu confirmar, pausa a música.",
    "Abre a calculadora. Se eu confirmar depois, pausa a música.",
    "Abre a calculadora e, se eu confirmar depois, pausa a música.",
    "Abre a calculadora e se eu confirmar depois, pausa a música.",
    "Quando eu confirmar, pausa a música; abre a calculadora agora.",
    "Pausa a música só se eu confirmar depois. Abre a calculadora agora.",
])
def test_autoridade_de_ordem_independente_nao_vaza_para_condicional(texto):
    turno = classificar(texto)
    assert len(turno["segmentos"]) == 2, turno["segmentos"]
    assert autoriza_execucao_efetiva(turno)
    assert "abre a calculadora" in turno["texto_operacional"]
    assert "pausa a música" not in turno["texto_operacional"]
    assert len([s for s in turno["segmentos"] if s["autoriza_execucao"]]) == 1


def test_condicao_em_argumento_citado_nao_e_restricao_da_ordem():
    turno = classificar('Abre o arquivo "apenas se autorizado.txt"')
    assert autoriza_execucao_efetiva(turno)
    assert len(turno["segmentos"]) == 1


def test_duas_ordens_imediatas_continuam_autorizadas():
    turno = classificar("Abre a calculadora e pausa a música")
    assert len(turno["segmentos"]) == 2
    assert all(s["autoriza_execucao"] for s in turno["segmentos"])


@pytest.mark.parametrize("ordem", ORDENS)
@pytest.mark.parametrize("separador", ["; ", ". ", "! "])
@pytest.mark.parametrize("qualificador", [
    "somente quando eu confirmar", "só se eu autorizar", "apenas quando eu pedir",
])
@pytest.mark.parametrize("normalizador", [False, True])
def test_condicao_posposta_apos_fronteira_independente_nao_absorve_primeiro_ato(
    ordem, separador, qualificador, normalizador,
):
    # RED descoberto na investigação do contrato explicativo. A primeira
    # divergência é segmentação, antes da explicação: não confundir os owners
    # nem remover o caso para declarar GREEN. O snapshot explicativo não
    # corrigia esse corte; a mesma fronteira deve funcionar em vários domínios.
    turno = classificar(f"Abre a calculadora{separador}{ordem} {qualificador}", normalizador)
    assert len(turno["segmentos"]) == 2
    assert turno["segmentos"][0]["autoriza_execucao"] is True
    assert turno["segmentos"][1]["autoriza_execucao"] is False
    assert turno["segmentos"][1]["natureza_acao"] == "condicao_nao_verificada"


@pytest.mark.parametrize("texto", [
    "Abre a calculadora e pausa a música só se eu confirmar",
    "Abre a calculadora, pausa a música somente quando eu confirmar",
    "Abre a calculadora; somente quando eu confirmar",
    "Quando eu confirmar; liga a luz",
    "Abre a calculadora. Só se eu confirmar",
])
def test_fronteira_sem_consequencia_independente_nao_libera_acao(texto):
    turno = classificar(texto)
    assert not autoriza_execucao_efetiva(turno)
    assert turno["texto_operacional"] == ""


def test_condicao_posposta_preserva_tambem_ordem_independente_posterior():
    turno = classificar("Abre a calculadora; liga a luz só se eu confirmar; pausa a música")
    assert len(turno["segmentos"]) == 3
    assert [s["autoriza_execucao"] for s in turno["segmentos"]] == [True, False, True]
    assert "luz" not in turno["texto_operacional"]


def test_condicao_investigada_nao_e_condicao_para_executar_a_pesquisa():
    turno = classificar("Pesquisa se eu posso cultivar orquídeas na sombra")
    assert autoriza_execucao_efetiva(turno)
    assert "pesquisa" in turno["texto_operacional"]


@pytest.mark.parametrize("texto", [
    "Abre a calculadora agora; quando eu confirmar, pausa a música.",
    "Abre a calculadora e se eu confirmar depois, pausa a música.",
    "Liga a luz agora; quando eu confirmar, abre a calculadora.",
])
def test_consumidor_prioritario_recebe_so_atos_autorizados(texto):
    from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime

    turno = classificar(texto)
    estado = EstadoCompartilhadoRuntime(mental={"turno_atual": turno})
    recebidos = []
    ns = {
        "_estado_compartilhado_runtime": estado,
        "_normalizar_texto_com_apelidos": normalizar_texto,
        "_texto_tem_comando_explicito": texto_tem_comando_explicito,
        "processar_comandos_em_cadeia": lambda trecho, origem: recebidos.append(trecho) or True,
    }
    runtime = ComandosImediatosRuntime(namespace_getter=lambda: ns, loop_getter=lambda: None)
    assert runtime.processar_prioritarios(texto)
    assert recebidos == [turno["texto_operacional"]]
    assert dict(estado.mental["turno_atual"]) == turno
