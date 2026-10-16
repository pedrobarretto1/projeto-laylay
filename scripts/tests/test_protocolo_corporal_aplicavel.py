"""Somente uma saída corporal habilitada recebe sua gramática de proposta."""

import copy

import pytest

from mente_laylay.cognicao.modelo_corporal import (
    formatar_modelo_corporal, formatar_realidade_corporal,
)
from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from mente_laylay.integracao.llm_http import compactar_payload_llm_local
from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT, BASE_SYSTEM_PROMPT_RAPIDO


def modelo_inativo(conectada=False):
    return {
        "origem": "owner_corpo_usb", "turno_id": "turno-atual",
        "conectada": conectada, "companhia_ativa": False, "passeio_ativo": False,
        "condicao": {"estado": "pronta" if conectada else "desconectada",
                     "autoriza_execucao": False},
        "percepcao_fisica": {"deslocamento": "nao_medido", "obstaculos": "nao_medido"},
        "ultima_experiencia": {"id": "experiencia-1", "turno_id": "turno-original",
                              "confirmado": True, "prova_deslocamento": False,
                              "pertence_ao_turno_atual": False},
        "intencao_em_curso": {"nome": "interagir", "motivo": "objetivo antigo",
                              "pontuacoes": {"interagir": 90}, "turno_id": "turno-original",
                              "pertence_ao_turno_atual": False, "sessao_vigente": False},
        "objetivo_para_continuar": {"objetivo_id": "0123456789ab",
                                   "continuidade_disponivel": False},
        "experiencia": {"historico_recente": [{"nome": "expressar", "turno_id": "antigo",
                                              "confirmado": True, "prova_deslocamento": False}],
                        "aprendizado_conectado": True,
                        "feedback": {"tipo": "recusa", "aceito": True}},
    }


@pytest.mark.parametrize("conectada", [False, True])
def test_estado_explicitamente_inativo_nao_oferece_gramatica_de_proposta(conectada):
    modelo = modelo_inativo(conectada)
    antes = copy.deepcopy(modelo)
    realidade = formatar_realidade_corporal(modelo)
    prompt = formatar_modelo_corporal(modelo)
    assert prompt.startswith(realidade), "primeiro preservar fatos, depois selecionar regras"
    sufixo = prompt[len(realidade):]
    assert "Escolha nome:" not in sufixo
    assert "Estrutura para continuidade" not in sufixo
    assert '"intencao_corporal":' not in sufixo
    assert "omita intencao_corporal" in sufixo
    assert "FORMATO ESTRUTURAL OBRIGATÓRIO DO JSON" in sufixo
    assert "campos do contrato principal" in sufixo
    assert modelo == antes, "projeção não muda estado, TTL ou autoridade"


@pytest.mark.parametrize("companhia", [True, None, 0, "false", "False", "ausente"])
def test_ativo_ou_indeterminado_conserva_protocolo_de_proposta(companhia):
    modelo = modelo_inativo()
    if companhia == "ausente":
        modelo.pop("companhia_ativa")
    else:
        modelo["companhia_ativa"] = companhia
    prompt = formatar_modelo_corporal(modelo)
    assert "Escolha nome:" in prompt and "Estrutura para continuidade" in prompt
    assert '"intencao_corporal":' in prompt
    assert "Nunca invente identificadores" in prompt


@pytest.mark.parametrize("rapido", [False, True], ids=["normal", "rapido"])
@pytest.mark.parametrize("texto", [
    "Como funciona seu motor? Só explica, não mova nada.",
    "Me ensina uma variável em Python.",
    "Você consegue pesquisar uma notícia?",
])
def test_porta_preserva_realidade_e_veto_sem_protocolo_inativo(texto, rapido):
    modelo = modelo_inativo()
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None, resumo_mente_integrada=lambda _: "",
        formatar_playlists=lambda: "", get_status_humor_prompt=lambda: "",
        base_system_prompt=BASE_SYSTEM_PROMPT,
        estado_getter=lambda: {"modelo_corporal": modelo},
    )
    mensagens = (
        [{"role": "system", "content": BASE_SYSTEM_PROMPT},
         {"role": "system", "content": runtime.preparar_instrucao_rapida(texto)}]
        if rapido else list(runtime.preparar_pacote(texto).mensagens)
    )
    mensagens.append({"role": "user", "content": texto})
    payload = preparar_payload_llm(mensagens, model="qwen3:4b-instruct",
                                  max_tokens=256, endpoint_local=True,
                                  modo_rapido=rapido)
    assert payload["response_format"] == {"type": "json_object"}
    for _ in range(2):
        instrucao = payload["messages"][-2]["content"]
        assert formatar_realidade_corporal(modelo) in instrucao
        assert "Escolha nome:" not in instrucao
        assert "omita intencao_corporal" in instrucao
        assert payload["messages"][-1] == {"role": "user", "content": texto}
        # A porta rápida já substitui a base pela versão rápida canônica.
        base = BASE_SYSTEM_PROMPT_RAPIDO if rapido else BASE_SYSTEM_PROMPT
        assert base in payload["messages"][0]["content"]
        payload = compactar_payload_llm_local(payload)


def test_estado_inativo_nao_restringe_comando_manual_nem_confirma_movimento():
    from scripts.tests.test_companhia_corporal import montar
    estado, esp, rosto, corpo, _, _ = montar()
    modelo = corpo.modelo_para_mente("manual")
    assert modelo["companhia_ativa"] is False
    prompt = formatar_modelo_corporal(modelo)
    assert "omita intencao_corporal" in prompt
    assert "prova_deslocamento=false significa NÃO MEDIDO" in prompt
    assert not any(p.startswith("MOTOR ") for p in esp.enviados)
    resultado = corpo.executar("CORPO_MOVER", {"direcao": "frente", "duracao_ms": 250})
    assert resultado["ok"]
    assert not corpo.modelo_para_mente("manual")["companhia_ativa"]
    assert not estado.mental["corpo_motor"]["prova_rotacao"]
    assert corpo.executar("CORPO_PARAR", {})["ok"]
    rosto.encerrar()


def test_protocolo_ativo_conserva_objetivo_e_receipt_sem_replay(monkeypatch):
    from scripts.tests.test_objetivo_corporal_entre_turnos import preparar_objetivo
    estado, _, rosto, corpo, _, _, objetivo = preparar_objetivo(monkeypatch)
    modelo = corpo.modelo_para_mente("novo")
    assert modelo["companhia_ativa"] is True
    prompt = formatar_modelo_corporal(modelo)
    assert "Escolha nome:" in prompt
    assert objetivo in prompt and "historico_recente" in prompt
    assert "Novo turno exige proposta atual" in prompt
    assert "nunca ausência de movimento" in prompt
    rosto.encerrar()


@pytest.mark.parametrize("modelo", [None, {}, {"origem": "llm", "companhia_ativa": False}])
def test_origem_nao_confiavel_nao_adquire_contrato_corporal(modelo):
    assert formatar_modelo_corporal(modelo) == ""
