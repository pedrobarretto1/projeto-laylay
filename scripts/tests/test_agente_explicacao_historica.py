"""Uma ocorrência própria não é evidência do motivo de outro agente."""
import pytest
from dataclasses import replace

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt
from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.decisao_observada import ExplicacaoOcorrencia
from scripts.tests.test_explicacao_ocorrencia import episodio

from scripts.tests.test_motivo_decisao_composicao import decisao_instalada as coletar_instalada


@pytest.fixture(scope="module")
def agentes_instalados(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("LAYLAY_COLETAR_AGENTE_EXPLICACAO", "1")
        return coletar_instalada.__wrapped__(tmp_path_factory)


def test_recuperacao_instalada_nao_atribui_decisao_propria_a_outro_agente(agentes_instalados):
    casos = agentes_instalados["consultas_agentes"]
    assert casos[0]["fonte_owner"] and "mudanca emocional causal" in casos[0]["preparada"]["fala"]
    for c in casos[1:5]:
        assert c["plano"]["autoriza_execucao"] is False and not c["plano"]["requer_execucao"]
        assert c["fonte_owner"] is None, (
            "Primeira fronteira: a seleção usa tipo da ação e ignora o agente perguntado.", c["texto"])
        fala = c["preparada"]["fala"]
        assert "mudanca emocional causal" not in fala and "outra pessoa ou de um grupo" in fala
        assert c["guarda_final"]["fala"] == fala and not c["preparada"]["comandos"]
    for c in casos[5:]:
        assert c["fonte_owner"] and "mudanca emocional causal" in c["preparada"]["fala"]


def test_ciclo_instalado_separa_agentes_publica_uma_vez_e_nao_executa(agentes_instalados):
    for t in agentes_instalados["turnos_agentes"]:
        assert len(t["textos"]) == 1
        fala = t["textos"][0]
        assert "outra pessoa ou de um grupo" in fala
        if "Por que você" in t["texto"]:
            assert fala.count("Sobre ") == 2 and "mudanca emocional causal" in fala
        else:
            assert "mudanca emocional causal" not in fala
        assert not t["executores"] and t["motores_antes"] == t["motores_depois"]
        assert t["plano"]["autoriza_execucao"] is False and not t["plano"]["comandos"]
        assert not any(m["tipo_chamada"] in {"reparo_factual", "reparo_comunicacao"} for m in t["modelos"])


def test_qwen_local_nao_transfere_decisao_da_laylay_ao_usuario(agentes_instalados):
    if "qwen_real" not in agentes_instalados:
        pytest.skip("Sonda opcional exige LAYLAY_DECISAO_QWEN_REAL=1.")
    for g in agentes_instalados["qwen_real"]["geracoes"]:
        assert g["modelos"] and g["modelos"][0]["resultado"]["sucesso"]
        assert any(h.get("status") == 200 for h in g["http"])
        assert len(g["finais_isolados"]) == 1 and not g["porta_executor"]
        fala = g["finais_isolados"][0]["fala"]
        assert "outra pessoa ou de um grupo" in fala and "mudanca emocional causal" not in fala
        assert not g["finais_isolados"][0]["comandos"]


def contrato(texto, *, fonte=None, mente=None):
    t = classificar_modalidade_turno(texto)
    p = {"id": t["id"], "texto_usuario": texto, "autoriza_execucao": False,
         "requer_execucao": False, "comandos": []}
    if fonte is not None:
        fonte = replace(fonte, turno_consulta=str(t["id"]), texto_consulta=texto)
    p["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=t, plano=p,
        explicacao_ocorrencia=fonte, mente=mente)
    return p


@pytest.mark.parametrize("texto", ["Por que eu fiz esse gesto?", "Por que ela fez esse gesto?",
    "Por que ele apagou esse arquivo?", "Por que eles desligaram essa tomada?",
    "Por que nós fizemos esse movimento?", "O que me levou a fazer esse gesto?",
    "O que levou ela a apagar esse arquivo?"])
@pytest.mark.parametrize("com_fonte", [False, True])
def test_agente_da_consulta_limita_fontes_proprias_em_qualquer_dominio(texto, com_fonte):
    owner = "executor_arquivos" if "arquivo" in texto else "executor_iot" if "tomada" in texto else "executor_corpo"
    motivo = {"executor_arquivos": "pedido_explicito_de_copia", "executor_iot": "regra_autorizada_do_usuario",
              "executor_corpo": "mudanca_emocional_causal"}[owner]
    f = ExplicacaoOcorrencia("provisoria", texto, (episodio(owner, motivo=motivo),), "unica") if com_fonte else None
    p = contrato(texto, fonte=f)
    assert "explicacao_ocorrencia" in p["contrato_fala"]
    a = avaliar_fala_historica("A decisão foi motivada por mudanca emocional causal.", plano=p)
    assert a["problemas"] and "mudanca emocional causal" not in a["fala"]
    assert "outra pessoa ou de um grupo" in a["fala"]
    assert motivo.replace("_", " ") not in a["fala"]
    assert not avaliar_fala_historica(a["fala"], plano=p)["problemas"]
    assert motivo.replace("_", " ") not in formatar_contrato_fala_para_prompt(p["contrato_fala"])


@pytest.mark.parametrize("texto", ["Por que você fez esse gesto quando eu cheguei?",
    "Por que você fez esse gesto para ela?", "Por que a Laylay fez esse gesto?",
    "O que motivou esse movimento?"])
def test_mencao_de_outro_participante_nao_troca_o_agente_da_acao(texto):
    p = contrato(texto, fonte=ExplicacaoOcorrencia("provisoria", texto, (episodio(),), "unica"))
    assert "mudanca emocional causal" in avaliar_fala_historica("Foi por rotina.", plano=p)["fala"]


def test_citacao_de_fala_propria_nao_prova_causa_de_terceiro():
    from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada
    fala = "O gesto aconteceu."
    registro = registrar_fala_observada(None, ocorrencia_id="f1", turno_id="antigo", fala=fala,
        resultados=(), canal="texto_publicado")
    p = contrato(f'Por que ela fez esse gesto quando você disse "{fala}"?',
        mente={"registro_semantico": registro, "ultima_resposta": fala})
    assert "evidencia_fala_historica" not in p["contrato_fala"]
    assert "outra pessoa ou de um grupo" in avaliar_fala_historica("Fui eu.", plano=p)["fala"]


@pytest.mark.parametrize("texto,papel", [
    ("Por que eu fiz isso?", "enunciador"), ("Por que você fez isso?", "destinatario"),
    ("Por que eles apagaram o arquivo?", "terceiro"), ("Por que nós fizemos isso?", "grupo"),
    ("Por que a gente apagou isso?", "grupo"), ("Por que a Laylay fez isso?", "destinatario"),
    ("Por que eu apaguei a nota?", "enunciador"), ("O que te levou a fazer isso?", "destinatario"),
    ("O que me levou a fazer isso?", "enunciador"), ("O que levou ela a fazer isso?", "terceiro"),
    ("Por que você fez isso quando eu cheguei?", "destinatario"),
    ('Por que você disse "Por que eu fiz isso?"?', "destinatario"),
    ("Por que ela faria isso?", ""), ("Por que nós faremos isso?", ""),
    ("Por que eu estou fazendo isso?", ""), ("Por que o servidor caiu?", ""),
    ("Por que eu sou assim?", ""), ("Por que eu vou fazer isso?", ""),
    ("Por que nós estamos fazendo isso?", ""),
    ('Traduza "por que eu fiz esse gesto?"', ""),
])
def test_papel_gramatical_e_da_acao_principal_e_nao_de_palavras_soltas(texto, papel):
    from mente_laylay.cognicao.referencias_linguagem import agente_explicacao_retrospectiva
    assert agente_explicacao_retrospectiva(texto) == papel


def test_composto_mantem_limite_do_outro_agente_e_motivo_da_laylay_separados():
    texto = "Por que ela fez esse gesto? Por que você fez esse gesto?"
    turno = classificar_modalidade_turno(texto)
    chamadas = []
    def recuperar(literal, *, turno):
        chamadas.append(literal)
        # Simula owner que ainda fornece fonte própria para ambas: o contrato
        # compartilhado também precisa recusar a atribuição incompatível.
        return ExplicacaoOcorrencia(str(turno["id"]), literal, (episodio(),), "unica")
    p = {"id": turno["id"], "texto_usuario": texto, "autoriza_execucao": False,
         "requer_execucao": False, "comandos": []}
    p["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=p,
        recuperar_explicacao_ocorrencia=recuperar)
    a = avaliar_fala_historica("As duas tiveram o mesmo motivo.", plano=p)
    partes = a["fala"].split(' Sobre ')
    assert len(partes) == 2 and len(chamadas) == 2
    assert "mudanca emocional causal" not in partes[0] and "outra pessoa ou de um grupo" in partes[0]
    assert "mudanca emocional causal" in partes[1]
    assert not avaliar_fala_historica(a["fala"], plano=p)["problemas"]


@pytest.mark.parametrize("texto", ["Por que eu estou fazendo esse gesto?", "Por que ela faz esse gesto?",
    "Por que nós faremos esse gesto?"])
def test_agente_explicito_nao_depende_de_haver_ocorrencia_passada(texto):
    from mente_laylay.cognicao.referencias_linguagem import agente_explicacao_causal
    from scripts.tests.test_explicacao_ocorrencia import owner_com_historico
    agente, retrospectiva = agente_explicacao_causal(texto)
    assert agente in {"enunciador", "terceiro", "grupo"} and retrospectiva is False
    _, runtime = owner_com_historico()
    assert runtime.recuperar_explicacao(texto, turno={"id": "consulta"}) is None


def test_contrato_de_fala_entregue_tambem_nao_prova_causa_de_outro_agente():
    from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada, recuperar_evidencia_da_fala
    registro = registrar_fala_observada(None, ocorrencia_id="f1", turno_id="antigo",
        fala="O gesto aconteceu.", resultados=(), canal="texto_publicado")
    texto = 'Por que ela fez esse gesto quando você disse "O gesto aconteceu."?'
    p = contrato(texto)
    c = p["contrato_fala"]
    c.pop("explicacao_ocorrencia", None)
    c["evidencia_fala_historica"] = recuperar_evidencia_da_fala(texto, {"registro_semantico": registro})
    c["texto_consulta_historica"] = texto
    assert "fala foi entregue" not in formatar_contrato_fala_para_prompt(c)
    a = avaliar_fala_historica("O registro confirma as ações.", plano=p)
    assert "outra pessoa ou de um grupo" in a["fala"] and "fala foi entregue" not in a["fala"]
