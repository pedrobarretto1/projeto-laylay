"""Catálogo -> contrato -> transporte; ensinar não é propor uma execução."""
from copy import deepcopy
import json

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from tests.test_catalogo_referencias_aplicativos import mapa_da_composicao


def preparar(texto, mapa=None):
    mapa = mapa or mapa_da_composicao()
    turno = {**classificar_modalidade_turno(texto), "id": 81}
    plano = planejar_turno(texto, turno=turno, mente={})
    plano["evidencia_capacidades"] = mapa.evidencia_conversacional(texto, turno=turno)
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={})
    estado = {"turno_atual": turno, "contrato_fala_atual": contrato}
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None, resumo_mente_integrada=lambda _: "", formatar_playlists=lambda: "",
        get_status_humor_prompt=lambda: "", base_system_prompt="PERSONALIDADE EXTENSA",
        estado_getter=lambda: estado, mapa_habilidades_prompt=mapa.contexto_para_prompt,
    )
    mensagens = [{"role": "system", "content": "PERSONALIDADE EXTENSA"},
                 {"role": "assistant", "content": "Eu estou escutando o player."},
                 {"role": "user", "content": texto}]
    return estado, runtime, mensagens


@pytest.mark.parametrize("texto,dominio", [
    ("como eu poderia pausar a música?", "musica"),
    ("me ensina como pausar a música", "musica"),
    # P12/P13: classificação e recuperação reais, sem compensar no preparador.
    ("como eu poderia aumentar o volume?", "sistema"),
    ("como eu poderia abrir a calculadora?", "sistema"),
    ("como eu faria para abrir um programa?", "sistema"),
    ("como eu poderia ligar a lâmpada?", "iot"),
    ("como eu faria para criar um arquivo?", "arquivos"),
    ("como eu poderia fechar a aba?", "navegador"),
])
@pytest.mark.parametrize("rapido", [False, True])
def test_explicacao_recebe_documentacao_sem_tarefas_de_planejamento(texto, dominio, rapido):
    estado, runtime, mensagens = preparar(texto)
    assert estado["turno_atual"]["autoriza_execucao"] is False
    contrato = estado["contrato_fala_atual"]
    assert contrato["roteiro_concreto"]["estrategia"] == "explicacao_capacidades"
    documento = json.loads(contrato["documentacao_capacidades"])
    assert dominio in {item["dominio"] for item in documento}
    antes = deepcopy(mensagens)
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=81)
    assert pacote.contexto_fechado
    assert mensagens == antes
    assert pacote.mensagens[-1] == mensagens[-1]
    transporte = preparar_payload_llm(list(pacote.mensagens), model="teste", modo_rapido=rapido,
                                      contexto_fechado=pacote.contexto_fechado)
    assert transporte["messages"] == list(pacote.mensagens)
    sistema = pacote.mensagens[0]["content"]
    assert contrato["documentacao_capacidades"] in sistema
    assert '"fala"' in sistema
    assert "leitura_emocional" not in sistema
    assert "PERSONALIDADE EXTENSA" not in sistema
    assert "Eu estou escutando" not in sistema


@pytest.mark.parametrize("texto", [
    "pode pausar a música", "pode pausar a música?", "a música está tocando",
    "preciso que você não pause a música", "como eu faço isso?",
    "como eu poderia pausar a música e abrir a calculadora?",
    "não pause a música e abra a calculadora", 'traduza "pausa a música"',
    "a frase 'pausa a música' é um comando?",
    "pausar a música pode travar o jogo?",
])
def test_outras_tarefas_nao_sao_reduzidas_a_explicacao(texto):
    estado, runtime, mensagens = preparar(texto)
    assert estado["contrato_fala_atual"]["roteiro_concreto"]["estrategia"] != "explicacao_capacidades"
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=81)
    assert "Documentação da habilidade" not in str(pacote.mensagens)


def test_indisponibilidade_e_parcial_nao_herdam_exemplos_executaveis():
    def mapa(operacional):
        return MapaHabilidadesRuntime(operacional_getter=lambda: operacional)
    texto = "como eu poderia pausar a música?"
    off = mapa({"dominios": {"musica": {"estado": "indisponivel", "motivo": "integracao_desconectada"}}})
    estado, runtime, mensagens = preparar(texto, off)
    doc = json.loads(estado["contrato_fala_atual"]["documentacao_capacidades"])
    assert doc[0]["estado"] == "indisponivel"
    assert doc[0]["exemplos"] == []
    assert doc[0]["motivo"] == "integracao_desconectada"
    assert runtime.preparar_envio_modelo(mensagens, turno_id=81).contexto_fechado
    # Os exemplos legados são por domínio: não atribuir todos a um intent.
    parcial = mapa({"capacidades": {"MEDIA_CONTROL": {"estado": "indisponivel"}}})
    estado, runtime, mensagens = preparar(texto, parcial)
    assert not estado["contrato_fala_atual"].get("documentacao_capacidades")
    assert not runtime.preparar_envio_modelo(mensagens, turno_id=81).contexto_fechado


@pytest.mark.parametrize("alvo,campo,valor", [
    ("turno_atual", "id", 80), ("turno_atual", "autoriza_execucao", True),
    ("turno_atual", "modalidade_geral", "misto"),
    ("contrato_fala_atual", "turno_id", 80),
    ("contrato_fala_atual", "documentacao_capacidades", ""),
])
def test_projecao_falha_aberta_para_fluxo_completo_quando_contrato_nao_e_do_turno(alvo, campo, valor):
    estado, runtime, mensagens = preparar("como eu poderia pausar a música?")
    estado[alvo][campo] = valor
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=81)
    assert not pacote.contexto_fechado
    assert list(pacote.mensagens) == mensagens


def test_fonte_nao_canonica_nao_produz_documentacao():
    estado, _, _ = preparar("como eu poderia pausar a música?")
    turno = estado["turno_atual"]
    plano = planejar_turno(turno["texto"], turno=turno, mente={})
    plano["evidencia_capacidades"] = {"fonte": "llm", "documentacao_capacidades": "inventada"}
    contrato = construir_contrato_semantico_fala(turno["texto"], turno=turno, plano=plano)
    assert not contrato.get("documentacao_capacidades")


def test_proposta_do_modelo_nao_substitui_autorizacao_e_fala_minima_chega_ao_verificador():
    from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
    from mente_laylay.cognicao.plano_turno import verificar_fala_turno
    texto = "como eu poderia pausar a música?"
    estado, _, _ = preparar(texto)
    plano = planejar_turno(texto, turno=estado["turno_atual"], mente={})
    plano["contrato_fala"] = estado["contrato_fala_atual"]
    fala = "Para pausar a música, basta dizer 'pausa a música'."
    for comandos in (None, [{"acao": "youtube_control", "alvo": "pause"}]):
        envelope = {"fala": fala}
        if comandos is not None:
            envelope["comandos"] = comandos
        preparado = preparar_resposta_para_execucao(
            texto, json.dumps(envelope, ensure_ascii=False),
            enviar_mensagem_cb=lambda *a, **k: pytest.fail("não deve precisar de reparo"),
            limpar_texto_fala_cb=lambda t: t, fallback_fala="Contingência", memoria_sqlite=None,
            contexto_comunicacao={"plano_turno": plano}, log=lambda _: None,
        )
        assert preparado["comandos"] == []
        assert preparado["fala"] == fala
        verificado = verificar_fala_turno(preparado["fala"], plano=plano, origem="ia_final")
        assert verificado["aceita"] and verificado["fala"] == fala
