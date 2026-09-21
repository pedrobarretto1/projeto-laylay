from copy import deepcopy
import json

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.integracao.registro_conversa_llm import RegistroPreparacaoConversa
from mente_laylay.personalidade.proporcao_resposta import limite_tokens_resposta


def _preparar(texto):
    turno = classificar_modalidade_turno(texto)
    turno["id"] = 81
    plano = planejar_turno(texto, turno=turno, mente={})
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={})
    estado = {"turno_atual": turno, "contrato_fala_atual": contrato}
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None, resumo_mente_integrada=lambda _: "",
        formatar_playlists=lambda: "", get_status_humor_prompt=lambda: "",
        base_system_prompt="Personalidade e outras tarefas", estado_getter=lambda: estado,
    )
    return estado, RegistroPreparacaoConversa.criar(runtime)


@pytest.mark.parametrize("texto", (
    "preciso que você não pause a música", "não ligue a lâmpada",
    "não apague o arquivo notas.txt", "não abra a calculadora",
    "eu não perguntei se o Discord está aberto",
))
def test_ato_decidido_recebe_tarefa_de_fala_sem_reclassificar_nem_apagar_utterance(texto):
    estado, registro = _preparar(texto)
    assert not estado["turno_atual"]["autoriza_execucao"]
    historico = [{"role": "system", "content": "PERSONALIDADE"},
                 {"role": "assistant", "content": "A música está tocando."},
                 {"role": "user", "content": texto}]
    antes = deepcopy(historico)
    pacote = registro.preparar_envio_modelo(historico, turno_id=81)
    assert pacote.contexto_fechado
    assert historico == antes
    assert pacote.mensagens[-1] == antes[-1]
    assert "A música está tocando" not in str(pacote.mensagens)
    assert "leitura_emocional" not in str(pacote.mensagens)
    assert '"comandos":[]' in str(pacote.mensagens)
    for mudanca in ({"turno_id": 80}, {"turno_id": None}):
        contrato = estado["contrato_fala_atual"]
        estado["contrato_fala_atual"] = {**contrato, **mudanca}
        assert not registro.preparar_envio_modelo(historico, turno_id=81).contexto_fechado
        estado["contrato_fala_atual"] = contrato
    for mudanca in ({"autoriza_execucao": True}, {"modalidade_geral": "misto"}, {"id": 80}):
        turno = estado["turno_atual"]
        estado["turno_atual"] = {**turno, **mudanca}
        assert not registro.preparar_envio_modelo(historico, turno_id=81).contexto_fechado
        estado["turno_atual"] = turno


@pytest.mark.parametrize("texto", (
    "pode pausar a música", "pode pausar a música?", "você consegue pausar a música",
    "como eu poderia pausar a música?", "a música está tocando",
    "não pause a música e abra a calculadora",
))
def test_pergunta_relato_pedido_e_misto_nao_viram_recusa_curta(texto):
    _, registro = _preparar(texto)
    mensagens = [{"role": "user", "content": texto}]
    pacote = registro.preparar_envio_modelo(mensagens, turno_id=81)
    assert not pacote.contexto_fechado
    assert list(pacote.mensagens) == mensagens


def test_envelope_principal_nao_herda_128_tokens_da_fala_curta():
    assert limite_tokens_resposta("preciso que você não pause a música", envelope_estruturado=True) >= 256
    assert limite_tokens_resposta("qual você prefere?", envelope_estruturado=True) >= 256
    assert limite_tokens_resposta("oi lay") == 128  # orçamento simples continua disponível
    assert limite_tokens_resposta("explique como isso funciona", envelope_estruturado=True) == 512


@pytest.mark.parametrize("rapido", [False, True])
def test_pacote_fechado_nao_perde_demonstracoes_na_preparacao(rapido):
    from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
    texto = "preciso que você não pause a música"
    _, registro = _preparar(texto)
    pacote = registro.preparar_envio_modelo([{"role": "user", "content": texto}], turno_id=81)
    payload = preparar_payload_llm(list(pacote.mensagens), model="teste", modo_rapido=rapido,
                                  contexto_fechado=pacote.contexto_fechado)
    assert payload["messages"] == list(pacote.mensagens)


@pytest.mark.parametrize("rapido", [False, True])
def test_orquestrador_preserva_utterance_e_envia_apenas_realizacao_do_ato(rapido):
    from types import SimpleNamespace
    from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
    from mente_laylay.integracao.registro_conversa_llm import EstadoConversaRuntime, ResultadoModelo
    from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
    texto = "preciso que você não pause a música"
    estado, registro = _preparar(texto)
    historico, pedidos = [], []
    estado["messages"] = historico
    conversa = EstadoConversaRuntime(
        getter=lambda: historico,
        setter=lambda novas: historico.__setitem__(slice(None), novas),
    )
    fala = "Certo, não vou pausar a música."
    def modelo(pedido):
        pedidos.append(pedido)
        payload = preparar_payload_llm(list(pedido.mensagens), model="teste",
            max_tokens=pedido.max_tokens, modo_rapido=pedido.modo_rapido,
            contexto_fechado=pedido.contexto_fechado)
        assert payload["messages"] == list(pedido.mensagens)
        return ResultadoModelo(json.dumps({"fala": fala, "comandos": []}), True)
    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "marcar_inicio_turno": lambda *a, **k: None,
        "obter_turno_atual": lambda: estado["turno_atual"],
        "processar_comandos_prioritarios": lambda _: False,
        "contexto_inicio": lambda: {}, "processar_inicio_fluxo": lambda *a: False,
        "usar_modo_rapido": lambda _: rapido, "texto_depende_de_contexto": lambda _: False,
        "modo_jogo_ativo": lambda: False, "preparacao_conversa": registro,
        "estado_conversa": conversa, "modelo_llm": SimpleNamespace(executar=modelo),
        "preparar_resposta": lambda *a: {"resposta_bruta": "{}", "fala": fala,
            "comandos": [], "tipo_interacao": "conversa", "leitura_semantica": {}},
        "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
        "executar_comandos_json": lambda *a, **k: {"erros": []},
        "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
        "finalizar_execucao": lambda *a, **k: {"fala": fala, "registrar_no_historico": True},
    }, log=lambda *a, **k: None)
    runtime.processar(texto, origem="terminal")
    assert len(pedidos) == 1
    assert pedidos[0].contexto_fechado
    assert pedidos[0].max_tokens == 256
    assert {"role": "user", "content": texto} in historico
    assert "reduza o brilho" not in str(historico)  # exemplos não viram memória
