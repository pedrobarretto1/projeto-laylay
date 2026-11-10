"""Um ato pode delimitar alvos distintos sem multiplicar a fala do usuário."""
from copy import deepcopy

import pytest

from mente_laylay.autonomia.roteador_deterministico import extrair_intencao_abrir_app
from mente_laylay.cognicao.decisao_turno import criar_validador_comandos_turno_runtime
from mente_laylay.cognicao.escopo_autorizacao import construir_autorizacoes_por_ato
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime


def resolver_real(texto: str, _frame: dict) -> dict | None:
    # Resolver nominal de produção, sem substituir sua seleção por mapa do teste.
    return extrair_intencao_abrir_app(
        texto, normalizar_texto=normalizar_texto, limpar_destino=lambda t: t,
        apps_map={"calculadora": "calc.exe", "bloco de notas": "notepad.exe", "paint": "mspaint.exe"},
        sites_diretos={"google": "https://google.com", "youtube": "https://youtube.com"},
    )


def runtime(texto: str, resolver=resolver_real):
    turno = classificar_modalidade_turno(texto)
    retrato, _ = construir_retrato_turno(texto, turno=turno, mente={}, contexto_perceptivo={})
    turno["retrato_id"] = retrato["id"]
    plano = planejar_turno(texto, turno=turno, mente={})
    estado = EstadoCompartilhadoRuntime(mental={"turno_atual": turno,
        "plano_turno_atual": plano, "retrato_turno_atual": retrato})
    return criar_validador_comandos_turno_runtime(estado_runtime=estado, resolver_ato=resolver), estado


def app(nome: str) -> dict:
    return {"intent": "APP_OPEN", "params": {"nome_app": nome}}


@pytest.mark.parametrize("texto,esperados", [
    ("abre a Calculadora e o Bloco de Notas", [app("Calculadora"), app("Bloco de Notas")]),
    ("abre a Calculadora, o Bloco de Notas e o Paint", [app("Calculadora"), app("Bloco de Notas"), app("Paint")]),
    ("abre o site Google e o site YouTube", [
        {"intent": "OPEN_URL", "params": {"alvo": "google"}},
        {"intent": "OPEN_URL", "params": {"alvo": "youtube"}},
    ]),
])
def test_alvos_nominais_do_mesmo_ato_tem_cardinalidade_propria_e_owner_compartilhado(texto, esperados):
    validar, estado = runtime(texto)
    antes = estado.snapshot()
    assert len(antes["mental"]["turno_atual"]["segmentos"]) == 1
    r = validar(deepcopy(esperados))
    assert r["comandos"] == esperados, "primeira fronteira: escopo singular perde um alvo enumerado"
    assert r["atos_autorizados_vinculados"] == [0]
    assert len(r["escopo_operacional_por_ato"]) == len(esperados)
    assert estado.snapshot() == antes


def test_enumeracao_nao_empresta_slot_para_duplicata_alvo_estranho_ou_destino():
    validar, _ = runtime("abre a Calculadora e o Bloco de Notas")
    calc, bloco = app("Calculadora"), app("Bloco de Notas")
    remoto = deepcopy(bloco)
    remoto["params"]["target"] = "pc_b"
    r = validar([app("Paint"), calc, deepcopy(calc), remoto, bloco, deepcopy(bloco)])
    assert r["comandos"] == [calc, bloco]
    assert len(r["rejeitados"]) == 4


def test_propostas_nao_definem_membros_e_resolucao_parcial_nao_usa_substring():
    validar, estado = runtime("abre a Calculadora e o Bloco de Notas Inexistente")
    assert resolver_real("abre o Bloco de Notas Inexistente", {}) == {
        "intent": "APP_OPEN", "params": {"nome_app": "bloco de notas"},
    }, "controle: o resolver legado aceita substring, sem provar alvo exato"
    r = validar([app("Calculadora"), app("Bloco de Notas")])
    assert r["comandos"] == [], "um membro não resolvido impede declarar o conjunto qualificado"
    mental = estado.snapshot()["mental"]
    assert construir_autorizacoes_por_ato(mental["turno_atual"], mental, resolver_real) == ()


@pytest.mark.parametrize("texto", [
    "abre a Calculadora ou o Bloco de Notas",
    "não abre a Calculadora e o Bloco de Notas",
    "quando eu confirmar, abre a Calculadora e o Bloco de Notas",
    "abre a Calculadora e o Bloco de Notas só se eu confirmar",
    "abre a Calculadora e o Bloco de Notas se eu confirmar",
    "abre a Calculadora e não o Bloco de Notas",
    "abre a Calculadora e o Bloco de Notas no outro pc",
])
def test_alternativa_negacao_condicao_e_modificador_indeterminado_nao_materializam_conjunto(texto):
    validar, _ = runtime(texto)
    assert validar([app("Calculadora"), app("Bloco de Notas")])["comandos"] == []


def test_repetir_nome_na_enumeracao_nao_autoriza_repetir_efeito():
    validar, _ = runtime("abre a Calculadora e a Calculadora")
    pedido = app("Calculadora")
    assert validar([pedido, deepcopy(pedido)])["comandos"] == [pedido]


@pytest.mark.parametrize("texto", [
    'abre o aplicativo "Calculadora e Bloco de Notas"',
    'abre o aplicativo "A ou B"',
    "cria a pasta E Depois",
])
def test_conector_dentro_de_nome_nao_cria_membros(texto):
    validar, estado = runtime(texto)
    mental = estado.snapshot()["mental"]
    autorizacoes = construir_autorizacoes_por_ato(mental["turno_atual"], mental, resolver_real)
    assert len(autorizacoes) <= 1
    assert len(validar([app("Calculadora"), app("Bloco de Notas")])["comandos"]) <= 1


def test_recortes_preservam_fonte_original_sem_inventar_atos_ou_verbo():
    texto = "Abre a Calculadora e o Bloco de Notas"
    validar, estado = runtime(texto)
    r = validar([app("Calculadora"), app("Bloco de Notas")])
    assert len(r["escopo_operacional_por_ato"]) == 2
    from mente_laylay.cognicao.coordenacao_nominal import ler_coordenacao_nominal

    fonte = ler_coordenacao_nominal(texto)
    assert fonte.fonte_textual == texto
    assert fonte.nucleo == (0, 4)
    assert [texto[slice(*i)] for i in fonte.alvos] == ["a Calculadora", "o Bloco de Notas"]
    assert fonte.projetar(1) == "Abre o Bloco de Notas"
    # Projeção é entrada derivada do resolver, nunca fonte do segmento original.
    assert len(estado.mental["turno_atual"]["segmentos"]) == 1
    assert all(a["texto"] == estado.mental["turno_atual"]["segmentos"][0]["texto"]
               for a in r["escopo_operacional_por_ato"])
