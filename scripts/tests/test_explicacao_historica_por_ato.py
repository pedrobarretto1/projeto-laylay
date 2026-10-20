"""Uma fonte de um ato não responde silenciosamente por todos os atos."""
import pytest
from dataclasses import asdict, replace
import time

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt
from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
from mente_laylay.memoria_mental.decisao_observada import ExplicacaoOcorrencia
from scripts.tests.test_explicacao_ocorrencia import episodio

from scripts.tests.test_motivo_decisao_composicao import decisao_instalada as coletar_instalada


def realizacoes_explicacoes_por_ato(*args, **kwargs):
    # Import tardio mantém o RED instalado executável com fontes anteriores,
    # sem fazer a coleta falhar pela API nova antes da fronteira causal.
    from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_explicacoes_por_ato as realizar
    return realizar(*args, **kwargs)


@pytest.fixture(scope="module")
def multiplas_instaladas(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("LAYLAY_COLETAR_EXPLICACAO_MULTIPLA", "1")
        return coletar_instalada.__wrapped__(tmp_path_factory)


def test_explicacao_composta_conserva_cobertura_de_cada_ato_canonico(multiplas_instaladas):
    for c in multiplas_instaladas["consultas_multiplas"]:
        p = c["plano"]
        assert p["autoriza_execucao"] is False and not p["requer_execucao"]
        assert len(c["turno"]["segmentos"]) == 2, "A leitura deve ter preservado ambos os atos antes do binding."
        assert c["fonte_owner"] and c["fonte_owner"]["episodios"], "Controle: fonte corporal ainda existe."
        assert "explicacoes_historicas_por_ato" in p["contrato_fala"], (
            "Primeira fronteira: uma fonte parcial foi promovida à cobertura da consulta inteira.", c["texto"])
        fala = c["preparada"]["fala"]
        assert "mudanca emocional causal" in fala
        # A elipse não possui ator/consulta causal próprios na leitura atual.
        # Não inventar essa interpretação: conservar a parte como não respondida.
        limite = ("ainda não foi respondida" if c["turno"]["segmentos"][1]["texto"].startswith(("apagou", "qual é"))
                  else "não prova que a ação não aconteceu")
        assert limite in fala
        assert c["guarda_final"]["fala"] == fala
        assert not c["preparada"]["comandos"]


def test_ciclo_instalado_publica_uma_conclusao_sem_perder_ato_ou_gerar_efeito(multiplas_instaladas):
    for t in multiplas_instaladas["turnos_multiplos"]:
        assert len(t["textos"]) == 1, (t["texto"], t["modo"])
        fala = t["textos"][0]
        assert "mudanca emocional causal" in fala and "não prova que a ação não aconteceu" in fala
        assert fala.count("Sobre ") == 2
        assert not t["executores"] and t["motores_antes"] == t["motores_depois"]
        assert t["plano"]["autoriza_execucao"] is False and not t["plano"]["comandos"]
        assert not any(m["tipo_chamada"] in {"reparo_factual", "reparo_comunicacao"} for m in t["modelos"])


def test_modelo_local_real_conclui_ambas_as_partes_com_limites(multiplas_instaladas):
    if "qwen_real" not in multiplas_instaladas:
        pytest.skip("Sonda opcional exige LAYLAY_DECISAO_QWEN_REAL=1.")
    for g in multiplas_instaladas["qwen_real"]["geracoes"]:
        assert g["modelos"] and g["modelos"][0]["resultado"]["sucesso"]
        assert any(h.get("status") == 200 for h in g["http"])
        assert len(g["finais_isolados"]) == 1 and not g["porta_executor"]
        final = g["finais_isolados"][0]
        assert "mudanca emocional causal" in final["fala"]
        assert "não prova que a ação não aconteceu" in final["fala"]
        assert final["fala"].count("Sobre ") == 2 and not final["comandos"]


def consulta(texto=None, *, recuperar=None, mente=None):
    texto = texto or "Por que você apagou esse arquivo? Por que você desligou essa tomada?"
    turno = classificar_modalidade_turno(texto)
    p = {"id": turno["id"], "texto_usuario": texto, "autoriza_execucao": False,
         "requer_execucao": False, "comandos": []}
    p["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=p,
        mente=mente, recuperar_explicacao_ocorrencia=recuperar)
    return turno, p


def owner_dois_dominios(texto, *, turno):
    if "arquivo" not in texto and "tomada" not in texto:
        return None
    arquivo = "arquivo" in texto
    e = episodio("executor_arquivos" if arquivo else "executor_iot",
        "copia_arquivo" if arquivo else "tomada_desligada",
        "pedido_explicito_de_copia" if arquivo else "regra_autorizada_do_usuario",
        confirmado=True if arquivo else False)
    return ExplicacaoOcorrencia(str(turno["id"]), texto, (e,), "unica")


def test_fontes_distintas_conservam_ordem_motivos_e_confirmacoes_sem_causa_comum():
    chamadas = []
    def recuperar(texto, *, turno):
        chamadas.append(texto)
        return owner_dois_dominios(texto, turno=turno)
    t, p = consulta(recuperar=recuperar)
    f = p["contrato_fala"]["explicacoes_historicas_por_ato"]
    assert chamadas == [parte.fonte_textual.como_dict()["texto_original"] for parte in f.partes]
    assert all(p["texto_usuario"] != c for c in chamadas)
    assert [parte.ato.indice for parte in f.partes] == [0, 1]
    fala = realizacoes_explicacoes_por_ato(f)[0]
    assert "pedido explicito de copia" in fala and "regra autorizada do usuario" in fala
    assert fala.index("copia arquivo") < fala.index("tomada desligada")
    assert "confirmação registrada" in fala and "sem confirmação" in fala
    assert not avaliar_fala_historica(fala, plano=p)["problemas"]
    candidatos = [fala.split(' Sobre ')[0], fala + " As duas ações tiveram a mesma causa: o servidor caiu.",
                  "Fiz as duas porque você estava triste."]
    for candidata in candidatos:
        assert validar_alegacoes_da_fala(candidata, plano=p)["problemas"]
        assert not avaliar_qualidade_comunicacao(p["texto_usuario"], candidata, plano=p)["aceita"]
        assert not validar_aderencia_contrato_fala(p["texto_usuario"], candidata,
            contrato_fala=p["contrato_fala"], turno_id=p["id"])["aceita"]
    assert formatar_contrato_fala_para_prompt(p["contrato_fala"]) == formatar_contrato_fala_para_prompt(p["contrato_fala"], compacto=True)


@pytest.mark.parametrize("estado", ["ausente", "ambigua", "sem_motivo", "vencida"])
def test_limite_da_segunda_fonte_nao_apaga_a_primeira_nem_se_torna_sucesso_total(estado):
    def recuperar(texto, *, turno):
        fonte = owner_dois_dominios(texto, turno=turno)
        if "arquivo" in texto:
            return fonte
        if estado == "ausente": return None
        e = fonte.episodios[0]
        if estado == "ambigua": return replace(fonte, episodios=(e, replace(e, id="outro")), referencia="ambigua")
        if estado == "sem_motivo": return replace(fonte, episodios=(replace(e, decisao=None, justificativa_registrada=False),))
        return replace(fonte, episodios=(replace(e, iniciada_em=time.time()-1000, encerrada_em=time.time()-999,
            decisao=None, justificativa_registrada=False),))
    _, p = consulta(recuperar=recuperar)
    fala = avaliar_fala_historica("Pronto, tudo explicado.", plano=p)["fala"]
    assert "pedido explicito de copia" in fala
    assert {"ausente": "não prova que a ação não aconteceu", "ambigua": "qual delas",
            "sem_motivo": "motivo da escolha não foi registrado", "vencida": "evidência histórica válida"}[estado] in fala


@pytest.mark.parametrize("alteracao", ["json", "turno", "texto", "comandos", "autoridade"])
def test_pacote_estrangeiro_ou_operacional_nao_ganha_cobertura_por_formato(alteracao):
    _, p = consulta(recuperar=owner_dois_dominios)
    f = p["contrato_fala"]["explicacoes_historicas_por_ato"]
    if alteracao == "json": p["contrato_fala"]["explicacoes_historicas_por_ato"] = asdict(f)
    elif alteracao == "turno": p["id"] = "outro"
    elif alteracao == "texto": p["texto_usuario"] = "outra consulta"
    elif alteracao == "comandos": p["comandos"] = [{"intent": "IOT_CONTROL"}]
    else: p["autoriza_execucao"] = True
    a = avaliar_fala_historica("Foi por rotina.", plano=p)
    assert a["problemas"] == ["evidencia_historica_invalida"]
    assert "pedido explicito de copia" not in a["fala"] and a["autoriza_execucao"] is False


@pytest.mark.parametrize("alteracao", ["texto_ato", "turno_fonte", "json", "indice", "intervalo"])
def test_fonte_de_outro_ato_e_segmentacao_adulterada_nao_emprestam_motivo(alteracao):
    def recuperar(texto, *, turno):
        f = owner_dois_dominios(texto, turno=turno)
        if alteracao == "texto_ato": return replace(f, texto_consulta="Outra pergunta")
        if alteracao == "turno_fonte": return replace(f, turno_consulta="estrangeiro")
        if alteracao == "json": return asdict(f)
        return f
    t, p = consulta(recuperar=recuperar)
    if alteracao in {"indice", "intervalo"}:
        f = p["contrato_fala"]["explicacoes_historicas_por_ato"]
        parte = f.partes[0]
        dados = parte.fonte_textual.como_dict()
        if alteracao == "indice": dados["indice_segmento"] = 1
        else: dados["intervalo"] = [0, 2]
        with pytest.raises(ValueError):
            replace(f, partes=(replace(parte, fonte_textual=SnapshotComandoIA(dados)), f.partes[1]))
    else:
        f = p["contrato_fala"]["explicacoes_historicas_por_ato"]
        assert all(parte.falha_fonte and parte.ocorrencia is None and parte.fala is None for parte in f.partes)
        avaliacao = avaliar_fala_historica("Foi por rotina.", plano=p)
        assert avaliacao["problemas"] and "pedido explicito de copia" not in avaliacao["fala"]


def test_citacao_de_fala_e_ocorrencia_nao_trocam_fontes():
    from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada
    fala = "A luz foi desligada."
    registro = registrar_fala_observada(None, ocorrencia_id="f1", turno_id="antigo", fala=fala,
        resultados=(), canal="texto_publicado")
    texto = f'Por que você disse "{fala}"? Por que você apagou esse arquivo?'
    _, p = consulta(texto, recuperar=owner_dois_dominios, mente={"registro_semantico": registro, "ultima_resposta": fala})
    f = p["contrato_fala"]["explicacoes_historicas_por_ato"]
    assert f.partes[0].fala and f.partes[0].ocorrencia is None
    assert f.partes[1].ocorrencia and f.partes[1].fala is None
    resposta = avaliar_fala_historica("Eu vi e confirmei as duas ações.", plano=p)["fala"]
    assert "fala foi entregue" in resposta and "pedido explicito de copia" in resposta


def test_pergunta_de_outro_tipo_continua_visivel_sem_receber_causa_do_gesto():
    _, p = consulta("Por que você apagou esse arquivo? Qual é a capital do Brasil?", recuperar=owner_dois_dominios)
    f = p["contrato_fala"]["explicacoes_historicas_por_ato"]
    assert f.partes[1].ocorrencia is None and f.partes[1].fala is None
    resposta = realizacoes_explicacoes_por_ato(f)[0]
    assert "Qual é a capital do Brasil?" in resposta and "ainda não foi respondida" in resposta


def test_sem_obrigacao_retrospectiva_nao_cria_julgamento_historico():
    def proibido(*a, **k): raise AssertionError("Não deve consultar histórico.")
    _, p = consulta("Por que o céu é azul? Qual é a capital do Brasil?", recuperar=proibido)
    assert "explicacoes_historicas_por_ato" not in p["contrato_fala"]


@pytest.mark.parametrize("falha", ["excecao", "json", "turno_estrangeiro"])
def test_falha_da_segunda_consulta_nao_apaga_fonte_valida_da_primeira(falha):
    def recuperar(texto, *, turno):
        f = owner_dois_dominios(texto, turno=turno)
        if "arquivo" in texto: return f
        if falha == "excecao": raise RuntimeError("Owner indisponível")
        if falha == "json": return asdict(f)
        return replace(f, turno_consulta="outro_turno")
    _, p = consulta(recuperar=recuperar)
    fala = avaliar_fala_historica("Consegui explicar tudo.", plano=p)["fala"]
    assert "pedido explicito de copia" in fala
    assert "evidência histórica válida para explicar esta parte" in fala


@pytest.mark.parametrize("alteracao", ["autoridade", "requer_execucao", "comandos"])
def test_consulta_composta_nao_contorna_dono_operacional_ou_receipts(alteracao):
    t, p = consulta()
    if alteracao == "autoridade":
        t["autoriza_execucao"] = True
        p["autoriza_execucao"] = True
    elif alteracao == "requer_execucao": p["requer_execucao"] = True
    else: p["comandos"] = [{"intent": "IOT_CONTROL"}]
    def proibido(*a, **k): raise AssertionError("Não consultar owner no fluxo operacional.")
    contrato = construir_contrato_semantico_fala(p["texto_usuario"], turno=t, plano=p,
        recuperar_explicacao_ocorrencia=proibido)
    assert "explicacoes_historicas_por_ato" not in contrato


def test_perguntas_repetidas_mantem_identidade_textual_sem_criar_ocorrencias():
    _, p = consulta("Por que você apagou esse arquivo? Por que você apagou esse arquivo?", recuperar=owner_dois_dominios)
    f = p["contrato_fala"]["explicacoes_historicas_por_ato"]
    assert [parte.ato.indice for parte in f.partes] == [0, 1]
    assert f.partes[0].fonte_textual.como_dict()["intervalo"] != f.partes[1].fonte_textual.como_dict()["intervalo"]
    assert [parte.ocorrencia.episodios[0].id for parte in f.partes] == ["e1", "e1"]
    assert realizacoes_explicacoes_por_ato(f)[0].count("Sobre ") == 2


def test_realizacao_permitida_e_estavel_com_grafia_e_espacos_originais():
    texto = "Por que você  apagou esse arquivo?   Por que você desligou essa tomada?"
    _, p = consulta(texto, recuperar=owner_dois_dominios)
    f = p["contrato_fala"]["explicacoes_historicas_por_ato"]
    fala = realizacoes_explicacoes_por_ato(f)[0]
    assert f.partes[0].fonte_textual.como_dict()["texto_original"] == "Por que você  apagou esse arquivo?"
    a = avaliar_fala_historica(fala, plano=p)
    assert not a["problemas"], "Uma realização oferecida pelo próprio contrato deve ser aceita."
    assert a["fala"] == fala
    assert avaliar_fala_historica(a["fala"], plano=p) == a
