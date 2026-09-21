"""Respostas locais publicadas pertencem ao mesmo diálogo que respostas LLM."""
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.integracao.registro_conversa_llm import EstadoConversaRuntime
from tests.test_orquestrador_fala_registro import _runtime_de_fala, _VozFalsa


@pytest.mark.parametrize("texto", (
    "você pode alterar o volume", "você pode alterar o volume?",
    "você consegue pausar a música", "quais suas habilidades?",
))
def test_resposta_prioritaria_publicada_entra_no_historico_sem_chamar_modelo(texto):
    historico, publicados, executados = [], [], []
    conversa = EstadoConversaRuntime(
        getter=lambda: historico,
        setter=lambda novas: historico.__setitem__(slice(None), novas),
    )
    fala, estado, _, _ = _runtime_de_fala(turno_id=81)
    turno = {**classificar_modalidade_turno(texto), "id": 81}
    estado.mental.update(turno_atual=turno, plano_turno_atual=planejar_turno(texto, turno=turno))
    fala.registrar_observador_texto_final(lambda texto, *a, **k: publicados.append(texto) or True)
    mapa = MapaHabilidadesRuntime()
    imediato = ComandosImediatosRuntime(namespace_getter=lambda: {
        "_estado_compartilhado_runtime": estado,
        "_responder_pergunta_capacidade_local": lambda t: mapa.responder_pergunta_capacidade(t, turno=turno),
        "falar_com_lipsync": fala.falar,
        "executar_intencao": lambda *a: executados.append(a) or True,
    }, loop_getter=lambda: None)
    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "obter_turno_atual": lambda: turno,
        "processar_comandos_prioritarios": imediato.processar_prioritarios,
        "estado_conversa": conversa,
        "textos_publicados_turno": getattr(fala, "textos_publicados_turno", lambda _: ()),
        "modelo_llm": SimpleNamespace(executar=lambda _: pytest.fail("rota local chamou LLM")),
    }, log=lambda *a: None)

    runtime.processar(texto)

    # Primeiro a saída realmente observável; depois sua publicação no diálogo.
    assert publicados and len(publicados) == 1
    assert executados == []
    assert historico == [{"role": "user", "content": texto},
                         {"role": "assistant", "content": publicados[0]}]
    from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
    from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT_RAPIDO
    payload = preparar_payload_llm([
        {"role": "system", "content": BASE_SYSTEM_PROMPT_RAPIDO},
        *historico, {"role": "system", "content": "Contrato do turno atual."},
        {"role": "user", "content": "eu alterei o volume"},
    ], model="teste", modo_rapido=True)
    assert payload["messages"][1:3] == historico


@pytest.mark.parametrize("aceita", (True, False))
def test_receipt_textual_independe_de_audio_e_nao_aceita_proatividade(aceita):
    fala, _, _, _ = _runtime_de_fala(voz=_VozFalsa([aceita]), turno_id="local-1")
    fala.registrar_observador_texto_final(lambda *a, **k: True)
    fala.falar("Consigo ajustar o volume quando você pede.")
    fala.falar("Uma observação espontânea.", _proativa=True)
    assert fala.textos_publicados_turno("local-1") == ("Consigo ajustar o volume quando você pede.",)
    assert fala.textos_publicados_turno("outro-turno") == ()


def test_fala_recusada_por_todos_os_canais_nao_produz_receipt_textual():
    fala, _, _, _ = _runtime_de_fala(voz=_VozFalsa([False]), turno_id="local-1")
    fala.registrar_observador_texto_final(lambda *a, **k: False)
    fala.falar("Uma resposta não entregue.")
    assert fala.textos_publicados_turno("local-1") == ()


def test_registro_local_vincula_chat_de_origem_sem_criar_entrada_antecipada():
    ativa = ["a"]
    conversas = {"a": [], "b": []}
    estado = EstadoConversaRuntime(
        getter=lambda: conversas[ativa[0]], setter=lambda m: conversas.__setitem__(ativa[0], m),
        conversation_id_getter=lambda: ativa[0],
        getter_conversa=lambda c: conversas[c],
        setter_conversa=lambda m, c: conversas.__setitem__(c, m),
    )
    registrar = estado.preparar_registro_local("local-1", "você pode alterar o volume")
    assert conversas == {"a": [], "b": []}
    assert not registrar("")
    ativa[0] = "b"
    assert registrar("Consigo ajustar o volume.")
    assert not registrar("Duplicada.")
    assert conversas["b"] == []
    assert [m["role"] for m in conversas["a"]] == ["user", "assistant"]
    assert conversas["a"][-1]["content"] == "Consigo ajustar o volume."


def test_tratado_sem_texto_publicado_nao_fabrica_resposta_no_historico():
    historico = []
    estado = EstadoConversaRuntime(getter=lambda: historico, setter=lambda m: historico.__setitem__(slice(None), m))
    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "estado_conversa": estado, "processar_comandos_prioritarios": lambda _: True,
        "textos_publicados_turno": lambda _: (),
    }, log=lambda *a: None)
    runtime.processar("Uma entrada consumida sem fala.")
    assert historico == []


@pytest.mark.parametrize("rota", ("prioritario", "pre_fluxo"))
def test_rotas_locais_preservam_textos_publicados_na_ordem_e_nao_o_plano(rota):
    historico = []
    estado = EstadoConversaRuntime(getter=lambda: historico, setter=lambda m: historico.__setitem__(slice(None), m))
    fala, mental, _, _ = _runtime_de_fala(turno_id=81)
    fala.registrar_observador_texto_final(lambda *a, **k: True)
    def processar(*args):
        fala.falar("Uma parte confirmada da resposta.")
        fala.falar("A segunda parte explica uma falha.")
        return True
    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "obter_turno_atual": lambda: {"id": 81}, "estado_conversa": estado,
        "processar_comandos_prioritarios": processar if rota == "prioritario" else lambda _: False,
        "processar_inicio_fluxo": processar,
        "textos_publicados_turno": fala.textos_publicados_turno,
        "modelo_llm": object(),
    }, log=lambda *a: None)
    runtime.processar("Uma entrada de teste.")
    assert historico[-1]["content"] == "Uma parte confirmada da resposta.\nA segunda parte explica uma falha."
    assert len(historico) == 2


def test_receipts_sao_limitados_e_uma_copia_nao_altera_o_owner():
    fala, estado, _, _ = _runtime_de_fala(turno_id=1)
    fala.registrar_observador_texto_final(lambda *a, **k: True)
    for i in range(1, 67):
        estado.mental["turno_atual"] = {"id": i}
        fala.falar(f"Resposta {i}.")
    assert fala.textos_publicados_turno(1) == ()
    assert fala.textos_publicados_turno(66) == ("Resposta 66.",)
    copia = list(fala.textos_publicados_turno(66))
    copia.clear()
    assert fala.textos_publicados_turno(66) == ("Resposta 66.",)


@pytest.mark.parametrize("fronteira", ("vinculo", "publicacao"))
def test_falha_de_historico_nao_impede_execucao_nem_conclusao_local(fronteira):
    eventos, falhas = [], []
    def falhar(*a):
        raise RuntimeError("Armazenamento indisponível")
    estado = SimpleNamespace(preparar_registro_local=falhar if fronteira == "vinculo" else lambda *a: falhar)
    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "estado_conversa": estado,
        "processar_comandos_prioritarios": lambda _: eventos.append("tratado") or True,
        "textos_publicados_turno": lambda _: ("Resposta publicada.",),
        "atualizar_plano_turno": eventos.append,
        "registrar_falha_diagnostico": lambda *a, **k: falhas.append(a),
    }, log=lambda *a: None)
    runtime.processar("Uma entrada de teste.")
    assert eventos == ["tratado", "tratado_prioritario"]
    assert falhas[0] == ("historico", "falha_registro_local")


def test_composicao_principal_injeta_receipt_do_orquestrador_real():
    import ast
    from pathlib import Path
    arvore = ast.parse((Path(__file__).resolve().parents[2] / "laylay.py").read_text(encoding="utf-8-sig"))
    atribuicao = next(n for n in arvore.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "_resposta_ia_runtime" for t in n.targets))
    getter = next(k.value for k in atribuicao.value.keywords if k.arg == "contexto_getter")
    conexoes = {k.value: ast.unparse(v) for k, v in zip(getter.body.keys, getter.body.values) if isinstance(k, ast.Constant)}
    assert conexoes["textos_publicados_turno"] == "_orquestrador_fala_runtime.textos_publicados_turno"
    assert conexoes["estado_conversa"] == "_registros_principais_runtime.estado_conversa"


def test_atalho_social_real_tambem_entra_no_historico():
    historico = []
    estado = EstadoConversaRuntime(getter=lambda: historico, setter=lambda m: historico.__setitem__(slice(None), m))
    fala, _, _, _ = _runtime_de_fala(turno_id=81)
    fala.registrar_observador_texto_final(lambda *a, **k: True)
    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "obter_turno_atual": lambda: {"id": 81}, "estado_conversa": estado,
        "modo_jogo_ativo": True, "usar_modo_rapido": lambda _: True,
        "_resposta_conversa_rapida_local": lambda _: "Oi, estou por aqui.",
        "falar_com_lipsync": fala.falar,
        "textos_publicados_turno": fala.textos_publicados_turno,
        "modelo_llm": SimpleNamespace(executar=lambda _: pytest.fail("atalho chamou LLM")),
    }, log=lambda *a: None)
    runtime.processar("oi")
    assert fala.textos_publicados_turno(81) == ("Oi, estou por aqui.",)
    assert historico == [{"role": "user", "content": "oi"},
                         {"role": "assistant", "content": "Oi, estou por aqui."}]


def test_emissor_curto_legado_nao_duplica_par_e_repeticao_nova_e_preservada(tmp_path):
    from tests.test_conversas_multiplas_c1 import _gerenciador
    from mente_laylay.personalidade.resposta_conversacional_runtime import RespostaConversacionalRuntime
    _, estado, chats = _gerenciador(tmp_path)
    chats.inicializar_legado(mensagens=[])
    conversa = EstadoConversaRuntime(
        getter=lambda: estado.memoria_conversa.get("messages", []),
        setter=lambda m: estado.atualizar_campos("memoria_conversa", messages=m),
        conversation_id_getter=chats.id_ativo, getter_conversa=chats.mensagens,
        setter_conversa=chats.substituir_mensagens,
    )
    fala, _, _, _ = _runtime_de_fala(turno_id=81)
    fala.registrar_observador_texto_final(lambda *a, **k: True)
    curto = RespostaConversacionalRuntime(namespace_getter=lambda: {
        "falar_com_lipsync": fala.falar, "_registrar_mente_curta": lambda *a, **k: None,
        "memoria_inteligente": SimpleNamespace(adicionar_interacao=lambda *a: None),
        "salvar_memoria": lambda: None,
    }, estado_runtime_getter=lambda: estado, fallback_fala="", log=lambda *a: None)
    for turno_id in (81, 82):
        registrar = conversa.preparar_registro_local(turno_id, "oi")
        assert curto.emitir_resposta_curta("oi", "Oi, estou por aqui.")
        assert registrar("Oi, estou por aqui.")
        assert not registrar("Oi, estou por aqui.")
    assert [m for m in conversa.mensagens() if m["role"] != "system"] == [
        {"role": "user", "content": "oi"}, {"role": "assistant", "content": "Oi, estou por aqui."},
        {"role": "user", "content": "oi"}, {"role": "assistant", "content": "Oi, estou por aqui."},
    ]
