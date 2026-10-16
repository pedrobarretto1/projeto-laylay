"""Uma explicação compartilha a fonte na geração, revisão e guarda final."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
import time

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt
from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica, realizacoes_explicacao_ocorrencia
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
from mente_laylay.memoria_mental.decisao_observada import DecisaoObservada, EpisodioExplicavel, ExplicacaoOcorrencia


def episodio(owner="executor_corpo", nome="alegria_balanco", motivo="mudanca_emocional_causal", **campos):
    agora = time.time()
    decisao = DecisaoObservada("d1", "owner_decisao", "expressar", motivo, "origem", "s1", "i1", "o1",
        agora - 3, SnapshotComandoIA({"referencia_causal": ["evento-1"]}))
    e = EpisodioExplicavel("e1", owner, nome, "origem", "s1", agora - 2, agora - 1, "i1", decisao,
        True, True, "PWM e parada elétrica" if owner == "executor_corpo" else "estado consultado",
        "Não há medição de deslocamento neste registro." if owner == "executor_corpo" else "Esta leitura não comprova o estado atual.")
    return replace(e, **campos)


def plano(fonte=None):
    texto = "Por que você fez esse gesto?"
    turno = {"id": "consulta", "modalidade": "pergunta", "autoriza_execucao": False}
    p = {"id": "consulta", "texto_usuario": texto, "autoriza_execucao": False, "requer_execucao": False, "comandos": []}
    fonte = fonte or ExplicacaoOcorrencia("consulta", texto, (episodio(),), "unica")
    p["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=p, explicacao_ocorrencia=fonte)
    return p


@pytest.mark.parametrize("owner,nome,motivo", [
    ("executor_corpo", "gesto_1", "mudanca_emocional_causal"),
    ("executor_arquivos", "arquivo_1", "pedido_explicito_de_copia"),
    ("executor_iot", "tomada_1", "regra_autorizada_do_usuario"),
])
def test_mesmo_contrato_aceita_apenas_realizacao_sustentada_em_owners_distintos(owner, nome, motivo):
    e = episodio(owner, nome, motivo)
    p = plano(ExplicacaoOcorrencia("consulta", "Por que você fez esse gesto?", (e,), "unica"))
    opcoes = realizacoes_explicacao_ocorrencia(p["contrato_fala"]["explicacao_ocorrencia"])
    assert len(opcoes) == 1
    assert motivo.replace("_", " ") in opcoes[0] and nome.replace("_", " ") in opcoes[0]
    for fala, aceito in [(opcoes[0], True), (opcoes[0] + " Porque o servidor estava fora do ar.", False),
                          ("Eu não fiz nada.", False), ("Agendei isso para depois.", False)]:
        assert (not bool(validar_alegacoes_da_fala(fala, plano=p)["problemas"])) is aceito
        assert avaliar_qualidade_comunicacao(p["texto_usuario"], fala, plano=p)["aceita"] is aceito
        assert validar_aderencia_contrato_fala(p["texto_usuario"], fala,
            contrato_fala=p["contrato_fala"], turno_id=p["id"])["aceita"] is aceito
    assert formatar_contrato_fala_para_prompt(p["contrato_fala"]) == formatar_contrato_fala_para_prompt(p["contrato_fala"], compacto=True)
    assert json.dumps(opcoes[0], ensure_ascii=False) in formatar_contrato_fala_para_prompt(p["contrato_fala"])


@pytest.mark.parametrize("confirmado,esperado", [(True, "confirmação registrada"), (False, "sem confirmação"), (None, "confirmação desconhecida")])
def test_motivo_independe_do_resultado_e_nao_comprova_causa_externa(confirmado, esperado):
    e = episodio(confirmado=confirmado)
    fonte = ExplicacaoOcorrencia("consulta", "Por que você fez esse gesto?", (e,), "unica")
    fala = realizacoes_explicacao_ocorrencia(fonte)[0]
    assert "mudanca emocional causal" in fala and esperado in fala
    assert "sem comprovar uma causa externa" in fala and "estado atual" in fala


@pytest.mark.parametrize("sem_decisao", [True, False])
def test_fonte_antiga_ou_proposta_llm_nao_recebe_rationale_posterior(sem_decisao):
    e = episodio(decisao=None if sem_decisao else episodio().decisao, justificativa_registrada=False)
    fala = realizacoes_explicacao_ocorrencia(ExplicacaoOcorrencia("c", "por quê?", (e,), "unica"))[0]
    assert "motivo da escolha não foi registrado" in fala
    assert "tentativa registrada" in fala and "confirmação registrada" in fala
    assert "mudanca emocional causal" not in fala


@pytest.mark.parametrize("alteracao", ["turno", "texto", "idade", "json", "comandos", "autoridade"])
def test_fonte_invalida_nao_pode_ser_aprovada_por_formato_ou_contexto(alteracao):
    p = plano()
    if alteracao == "turno": p["id"] = "outra"
    elif alteracao == "texto": p["texto_usuario"] = "outra pergunta"
    elif alteracao == "comandos": p["comandos"] = [{"intent": "IOT_CONTROL"}]
    elif alteracao == "autoridade": p["autoriza_execucao"] = True
    elif alteracao == "json": p["contrato_fala"]["explicacao_ocorrencia"] = asdict(p["contrato_fala"]["explicacao_ocorrencia"])
    elif alteracao == "idade":
        f = p["contrato_fala"]["explicacao_ocorrencia"]
        p["contrato_fala"]["explicacao_ocorrencia"] = replace(f, episodios=(replace(f.episodios[0], encerrada_em=time.time()-901, iniciada_em=time.time()-905, decisao=None, justificativa_registrada=False),))
    antes = deepcopy(p)
    avaliacao = avaliar_fala_historica("Foi rotina agendada.", plano=p)
    assert avaliacao["problemas"] == ["evidencia_historica_invalida"]
    assert "Não tenho evidência histórica válida" in avaliacao["fala"]
    assert p == antes and avaliacao["autoriza_execucao"] is False


def owner_com_historico(quantidade=1, *, com_fonte=True):
    from scripts.tests.test_decisao_observada import experiencia, fonte
    estado, runtime = experiencia()
    # Mesmas portas de ocorrência/resultado; nenhum motor ou inferência.
    for i in range(quantidade):
        d = fonte(id=f"d{i}") if com_fonte else None
        e = runtime.iniciar(nome=f"gesto_{i}", origem_intencao="mente_causal", perfil="bancada",
            intencao_id="proposta-1", decisao_origem=d)
        runtime.registrar(e, {"ok": True}, [{"ok": True, "parada_confirmada": True, "aplicacao_pwm_confirmada": True}])
    return estado, runtime


@pytest.mark.parametrize("texto", ["Por que você fez esse gesto?", "O que motivou esse movimento?",
    "Qual foi o motivo daquele gesto?", "Explique essa decisão corporal."])
def test_owner_resolve_variantes_sem_depender_da_frase_historica(texto):
    estado, runtime = owner_com_historico()
    antes = estado.retrato_dominio("mental")
    f = runtime.recuperar_explicacao(texto, turno={"id": "nova"})
    assert f.referencia == "unica" and f.episodios[0].decisao.motivo == "mudanca_emocional_causal"
    assert estado.retrato_dominio("mental") == antes


@pytest.mark.parametrize("texto", ["Por que o servidor caiu?", "Qual música toca?", "Por que um gesto expressa emoção?",
    "Traduza 'por que você fez esse gesto?'", "Por que você vai fazer esse gesto?"])
def test_owner_nao_escolhe_episodio_para_assunto_geral_citacao_ou_futuro(texto):
    _, runtime = owner_com_historico()
    assert runtime.recuperar_explicacao(texto, turno={"id": "nova"}) is None


def test_duas_ocorrencias_exigem_referencia_sem_emprestar_ultima_acao():
    estado, runtime = owner_com_historico(2)
    estado.atualizar_campos("mental", ultima_acao_contrato={"intent": "IOT_CONTROL", "confirmado": True})
    f = runtime.recuperar_explicacao("Por que você fez esse gesto?", turno={"id": "nova"})
    assert f.referencia == "ambigua" and len(f.episodios) == 2
    assert "qual delas" in realizacoes_explicacao_ocorrencia(f, agora=101)[0]
    alvo = f.episodios[0].id
    unica = runtime.recuperar_explicacao(f"Por que você fez esse gesto {alvo}?", turno={"id": "nova"})
    assert unica.referencia == "unica" and unica.episodios[0].id == alvo


def test_owner_sem_fonte_continua_explicando_limite_sem_negação_da_tentativa():
    _, runtime = owner_com_historico(com_fonte=False)
    f = runtime.recuperar_explicacao("Por que você fez esse gesto?", turno={"id": "nova"})
    assert "motivo da escolha não foi registrado" in realizacoes_explicacao_ocorrencia(f, agora=101)[0]
    runtime.clock = lambda: 1002.0
    f = runtime.recuperar_explicacao("Por que você fez esse gesto?", turno={"id": "nova"})
    assert f.referencia == "ausente"
    assert "não prova que a ação não aconteceu" in realizacoes_explicacao_ocorrencia(f, agora=1002)[0]


def test_fonte_de_outra_ocorrencia_nao_apaga_tentativa_nem_justifica_esta():
    estado, runtime = owner_com_historico()
    historico = estado.obter_copia("mental", "historico_corporal", [])
    historico[0]["decisao_origem"]["intencao_id"] = "outra_intencao"
    estado.atualizar_campos("mental", historico_corporal=historico)
    f = runtime.recuperar_explicacao("Por que você fez esse gesto?", turno={"id": "nova"})
    assert f.referencia == "unica" and f.episodios[0].decisao is None
    fala = realizacoes_explicacao_ocorrencia(f, agora=101)[0]
    assert "tentativa registrada" in fala and "motivo da escolha não foi registrado" in fala


@pytest.mark.parametrize("referencia", ['"gesto inexistente"', '00000000000000000000000000000000'])
def test_referencia_explicita_desconhecida_nao_empresta_unica_ocorrencia_recente(referencia):
    _, runtime = owner_com_historico()
    f = runtime.recuperar_explicacao(f"Por que você fez esse gesto {referencia}?", turno={"id": "nova"})
    assert f.referencia == "ausente" and not f.episodios


@pytest.mark.parametrize("alteracao", ["dict", "turno", "texto"])
def test_binding_de_fonte_invalida_nao_desliga_o_contrato(alteracao):
    f = ExplicacaoOcorrencia("consulta", "Por que você fez esse gesto?", (episodio(),), "unica")
    if alteracao == "dict": f = asdict(f)
    elif alteracao == "turno": f = replace(f, turno_consulta="outra")
    elif alteracao == "texto": f = replace(f, texto_consulta="Outra pergunta")
    p = plano(f)
    assert "explicacao_ocorrencia" in p["contrato_fala"]
    avaliacao = avaliar_fala_historica("Foi o servidor.", plano=p)
    assert avaliacao["problemas"] == ["evidencia_historica_invalida"]


@pytest.mark.parametrize("complemento", ["", " explicação registrada" * 40])
def test_citacao_de_fala_entregue_nao_e_substituida_por_episodio_de_acao(complemento):
    from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada
    registro = registrar_fala_observada(None, ocorrencia_id="f1", turno_id="antigo",
        fala="Vi você fazer esse gesto." + complemento, resultados=(), canal="texto_publicado")
    texto = 'Quando você disse "Vi você fazer esse gesto.' + complemento + '", por que disse isso?'
    f = ExplicacaoOcorrencia("consulta", texto, (episodio(),), "unica")
    contrato = construir_contrato_semantico_fala(texto,
        turno={"id": "consulta", "modalidade": "pergunta", "autoriza_execucao": False},
        plano={"id": "consulta"}, mente={"registro_semantico": registro}, explicacao_ocorrencia=f)
    assert "evidencia_fala_historica" in contrato and "explicacao_ocorrencia" not in contrato
