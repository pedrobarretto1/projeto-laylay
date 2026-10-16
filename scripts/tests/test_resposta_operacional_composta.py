"""Uma cadeia publica receipts por efeito e uma resposta pelo pedido inteiro."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.dispatcher_comandos_json import executar_comandos_json
from mente_laylay.autonomia.finalizacao_execucao_ia import finalizar_execucao_resposta_ia
from mente_laylay.integracao.contexto_execucao_ia import ContextoIntencaoRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.personalidade.orquestrador_fala_runtime import OrquestradorFalaRuntime
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
from mente_laylay.personalidade.planejador_resposta import fala_factual_resultados_compostos
from mente_laylay.cognicao.preferencia_humor import extrair_preferencia_humor


def _montar(*, falha=False, redundante=False, modelo_invalido=False):
    estado = EstadoCompartilhadoRuntime()
    estado.mental.update({
        "turno_atual": {"id": "pedido-composto", "autoriza_execucao": True},
        "plano_turno_atual": {
            "id": "pedido-composto", "fase": "planejado", "requer_execucao": True,
            "texto_usuario": "liga a luz e coloca a playlist piano", "comandos": [],
        },
    })
    falas, textos, receipts, chamadas = [], [], [], []
    class Voz:
        def falar(self, texto, *_args, **_kwargs):
            falas.append(texto)
            return True
    orquestrador = OrquestradorFalaRuntime(servicos_iniciais={
        "_estado_compartilhado_runtime": estado,
        "_voz_runtime": Voz(), "print": lambda *_a: None,
        "_dirigir_fala_mente": lambda texto, **_k: {"fala": texto},
        "_registrar_continuidade_da_fala_mente": lambda mental, *_a, **_k: mental,
    })
    orquestrador.registrar_observador_texto_final(lambda texto, *_a, **_k: textos.append(texto))

    def modelo(mensagens, **kwargs):
        dados = json.loads(mensagens[1]["content"])
        chamadas.append((dados, kwargs))
        if "resultados" not in dados:
            if dados["alvo"] == "piano":
                return "Não consegui abrir a playlist piano." if falha else "Abri a playlist piano."
            return "A lâmpada do quarto já estava ligada; não repeti o comando." if redundante else "Liguei a lâmpada do quarto."
        itens = dados["resultados"]
        luz = "A lâmpada do quarto já estava ligada, então não repeti o comando" if redundante else "Liguei a lâmpada do quarto"
        piano = "não consegui abrir a playlist piano" if falha else "abri a playlist piano"
        if modelo_invalido:
            piano = "a playlist piano está tocando"  # Falha não pode virar sucesso.
        fala = luz + " e " + piano + "."
        return json.dumps({"fala": fala, "trechos": [
            {"id_solicitacao": itens[0]["id_solicitacao"], "trecho": luz},
            {"id_solicitacao": itens[1]["id_solicitacao"], "trecho": piano},
        ]}, ensure_ascii=False)

    def registrar(receipt, *_a, **_k):
        receipts.append(receipt.como_dict())
        return True
    servicos = {
        "falar_com_lipsync": orquestrador.falar,
        "_falar_resultado_operacional": orquestrador.falar_resultado_operacional,
        "_agrupar_resultados_operacionais": getattr(orquestrador, "agrupar_resultados_operacionais", lambda **_k: nullcontext()),
        "_acumular_resultado_operacional": getattr(orquestrador, "acumular_resultado_operacional", lambda *_a, **_k: False),
        "_registrar_resultado_execucao": registrar,
        "enviar_mensagem": modelo,
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_texto_depende_de_contexto": lambda _t: False,
        "_texto_parece_consulta_operacional": lambda _t: True,
        "detectar_intencao_deterministica": lambda texto: {
            "intent": "IOT_CONTROL" if "luz" in texto else "PLAYLIST_PLAY",
            "params": {"alvo": "lâmpada do quarto" if "luz" in texto else "piano"},
        },
    }
    contexto = ContextoIntencaoRuntime(namespace_getter=lambda: servicos, estado_getter=lambda: dict(estado.mental))
    ciclo = CicloComandosRuntime(namespace_getter=lambda: servicos, contexto_intencao_runtime=contexto, log=lambda *_a: None)

    def executor(resultado, texto):
        alvo = resultado["params"]["alvo"]
        status = ("ja_estava_ligado" if redundante else "ligado") if alvo != "piano" else ("falha_execucao" if falha else "playlist_aberta")
        ok = status != "falha_execucao"
        adaptador = AdaptadorResultadoOperacional(resultado, resultado["params"], texto, "pc_a", contexto.montar())
        adaptador.marcar_resultado(status, ok, confirmado=ok)
        adaptador.falar_por_status(status, "Lâmpada do quarto ligada. Pronta pra brilhar." if alvo != "piano" else "Deixei piano aberto e em foco. Já puxei piano pra tocar.", alvo=alvo)
        return ok
    ciclo.executar_intencao = executor
    return ciclo, orquestrador, estado, falas, textos, receipts, chamadas, servicos


@pytest.mark.parametrize("texto", [
    "liga a luz e coloca a playlist piano",
    "liga a luz e depois coloca a playlist piano",
])
def test_pedido_composto_tem_uma_autoria_e_uma_entrega(texto):
    ciclo, _o, _e, falas, textos, receipts, chamadas, _s = _montar()
    assert ciclo.processar_cadeia(texto)
    assert len(receipts) == 2
    assert len({item["id_solicitacao"] for item in receipts}) == 2
    assert all(item["confirmado"] is True for item in receipts)
    assert len(chamadas) == 1, "autoria deve receber os dois resultados juntos"
    assert len(textos) == len(falas) == 1
    assert textos == falas == ["Liguei a lâmpada do quarto e abri a playlist piano."]
    assert [item["id_solicitacao"] for item in chamadas[0][0]["resultados"]] == [item["id_solicitacao"] for item in receipts]


def test_falha_parcial_e_nao_execucao_das_proximas_etapas_sao_preservadas():
    ciclo, _o, _e, falas, textos, receipts, chamadas, _s = _montar(falha=True)
    assert ciclo.processar_cadeia("liga a luz e depois coloca a playlist piano e depois abre o chrome")
    assert len(receipts) == 2
    assert receipts[0]["confirmado"] is True
    assert receipts[1]["confirmado"] is False
    assert len(textos) == len(falas) == 1
    assert "Liguei a lâmpada" in falas[0] and "não consegui abrir a playlist piano" in falas[0]
    assert len(chamadas) == 1


def test_estado_ja_satisfeito_nao_vira_nova_execucao():
    ciclo, _o, _e, falas, textos, receipts, chamadas, _s = _montar(redundante=True)
    assert ciclo.processar_cadeia("liga a luz e coloca a playlist piano")
    assert receipts[0]["executou"] is False and receipts[0]["confirmado"] is True
    assert len(textos) == len(falas) == len(chamadas) == 1
    assert "não repeti" in falas[0] and "playlist piano" in falas[0]


def test_autoria_nao_promove_falha_parcial_a_sucesso_total():
    ciclo, _o, _e, falas, textos, receipts, chamadas, _s = _montar(falha=True, modelo_invalido=True)
    assert ciclo.processar_cadeia("liga a luz e coloca a playlist piano")
    assert len(textos) == len(falas) == 1
    assert "não consegui" in falas[0].casefold()
    assert "está tocando" not in falas[0]
    assert receipts[1]["confirmado"] is False


def test_resultado_de_turno_antigo_nao_se_publica_no_novo_turno():
    ciclo, _o, estado, falas, textos, receipts, _chamadas, _s = _montar()
    executar = ciclo.executar_intencao
    def mudar_turno(resultado, texto):
        retorno = executar(resultado, texto)
        if resultado["params"]["alvo"] == "piano":
            estado.mental["turno_atual"] = {"id": "outro-pedido", "autoriza_execucao": True}
        return retorno
    ciclo.executar_intencao = mudar_turno
    assert ciclo.processar_cadeia("liga a luz e coloca a playlist piano")
    assert len(receipts) == 2
    assert falas == textos == []


@pytest.mark.parametrize("falha", [False, True])
def test_dispatcher_e_finalizacao_publicam_uma_resposta_do_pedido(falha):
    ciclo, _o, _e, falas, textos, receipts, chamadas, servicos = _montar(falha=falha)
    comandos = [
        {"intent": "IOT_CONTROL", "params": {"alvo": "lâmpada do quarto"}},
        {"intent": "PLAYLIST_PLAY", "params": {"alvo": "piano", "nome_playlist": "piano"}},
    ]
    ctx = dict(servicos, executar_intencao=ciclo.executar_intencao)
    dispatch = executar_comandos_json(ctx, "liga a luz e coloca a playlist piano", comandos, "", "comando", False, False, False)
    assert len(receipts) == 2
    assert len(textos) == len(falas) == 1
    assert len(chamadas) == 1
    assert dispatch["resposta_composta_publicada"] is True
    ctx_final = dict(servicos, resposta_operacional_composta=dispatch,
                     limpar_resposta_da_ia=lambda texto: (texto, []))
    resultado_final = finalizar_execucao_resposta_ia(ctx_final, comandos, dispatch["erros"], "", False, True, False)
    assert resultado_final["fala"] == falas[0]
    assert resultado_final["tipo"] == "operacional_composta"
    assert len(textos) == len(falas) == len(chamadas) == 1


@pytest.mark.parametrize("violacao", ["omissao", "id_estrangeiro", "sobreposicao", "troca_alvos", "sucesso_falso", "alegacao_extra", "instrucao"])
def test_autoria_composta_exige_vinculo_integro_de_cada_receipt(violacao):
    itens = [
        ResultadoAcao(intent="IOT_CONTROL", status="ligado", alvo="lâmpada do quarto", executou=True, confirmado=True, origem="executor", id_solicitacao="luz"),
        ResultadoAcao(intent="PLAYLIST_PLAY", status="falha_execucao", alvo="piano", executou=False, confirmado=False, origem="executor", id_solicitacao="piano"),
    ]
    luz, piano = "Liguei a lâmpada do quarto", "não consegui abrir a playlist piano"
    fala = luz + " e " + piano + "."
    partes = [{"id_solicitacao": "luz", "trecho": luz}, {"id_solicitacao": "piano", "trecho": piano}]
    dados = {"fala": fala, "trechos": partes}
    if violacao == "omissao": partes.pop()
    elif violacao == "id_estrangeiro": partes[1]["id_solicitacao"] = "outra-ocorrencia"
    elif violacao == "sobreposicao": partes[0]["trecho"] = fala
    elif violacao == "troca_alvos": partes[0]["trecho"], partes[1]["trecho"] = piano, luz
    elif violacao == "sucesso_falso":
        dados["fala"] = fala.replace(piano, "abri a playlist piano")
        partes[1]["trecho"] = "abri a playlist piano"
    elif violacao == "alegacao_extra": dados["fala"] += " E apaguei seu arquivo."
    elif violacao == "instrucao": dados["comandos"] = [{"intent": "DELETE_ITEM"}]
    resultado = personalizar_confirmacao_composta_llm(itens, "A luz foi ligada; piano falhou.", enviar_mensagem=lambda *_a, **_k: json.dumps(dados))
    assert not resultado.usada_llm
    assert resultado.fala == "A luz foi ligada; piano falhou."


def test_turno_muda_durante_autoria_sem_publicar_fala_tardia():
    ciclo, _o, estado, falas, textos, receipts, chamadas, servicos = _montar()
    original = servicos["enviar_mensagem"]
    def modelo(mensagens, **kwargs):
        resultado = original(mensagens, **kwargs)
        estado.mental["turno_atual"] = {"id": "outra-conversa", "autoriza_execucao": True}
        return resultado
    ciclo.contexto_intencao_runtime._servicos_estaticos["enviar_mensagem"] = modelo
    assert ciclo.processar_cadeia("liga a luz e coloca a playlist piano")
    assert len(receipts) == 2 and len(chamadas) == 1
    assert falas == textos == []


def test_pedido_unico_preserva_autoria_e_entrega_imediata():
    ciclo, _o, _e, falas, textos, receipts, chamadas, _s = _montar()
    assert ciclo.executar_intencao({"intent": "IOT_CONTROL", "params": {"alvo": "lâmpada do quarto"}}, "liga a luz")
    assert len(receipts) == len(chamadas) == len(textos) == len(falas) == 1
    assert "resultados" not in chamadas[0][0]


def test_atualizacao_da_mesma_ocorrencia_substitui_a_certeza_antiga():
    _c, orquestrador, _e, falas, textos, _r, _ch, _s = _montar()
    with orquestrador.agrupar_resultados_operacionais(texto_usuario="abre a Calculadora e toca piano") as lote:
        sucesso = ResultadoAcao(intent="APP_OPEN", status="app_aberto", alvo="Calculadora", executou=True, confirmado=True, origem="executor", id_solicitacao="mesma-ocorrencia")
        falha = ResultadoAcao(intent="APP_OPEN", status="falha_execucao", alvo="Calculadora", executou=False, confirmado=False, origem="executor", id_solicitacao="mesma-ocorrencia")
        assert orquestrador.acumular_resultado_operacional(sucesso, "Abri a Calculadora.")
        assert orquestrador.acumular_resultado_operacional(falha, "Não consegui abrir a Calculadora.")
        assert len(lote.resultados) == 1
        assert lote.resultados[0].status == "falha_execucao"
        assert lote.resultados[0].confirmado is False
    assert len(falas) == len(textos) == 1
    assert "não consegui" in falas[0].casefold() and "Calculadora" in falas[0]


def test_fala_direta_do_executor_chega_ao_lote_com_receipt_da_invocacao():
    from mente_laylay.autonomia.roteador_intencao import executar_intencao
    _c, owner, _e, falas, textos, receipts, _ch, servicos = _montar()
    ctx = {**servicos, "organizar_janelas_robusto": lambda esquerda, direita: {
        "ok": True, "executou": True, "confirmado": True, "status": "layout_confirmado",
        "nome_esquerda": esquerda, "nome_direita": direita}}
    with owner.agrupar_resultados_operacionais(texto_usuario="esquerda, direita, esquerda",
            enviar_mensagem=lambda *_a, **_k: "") as lote:
        for indice, lado in enumerate(("left", "right", "left")):
            assert executar_intencao({"intent": "ORGANIZAR_DESKTOP", "params": {lado: "Calculadora"},
                "id_solicitacao": f"layout-{indice}"}, "pedido autorizado", ctx)
        assert len(receipts) == 3, "a publicação de todos os efeitos precede a apresentação"
        assert len(lote.resultados) == 3, "fala comum perdeu o vínculo com os receipts publicados"
        assert [r.id_solicitacao for r in lote.resultados] == [f"layout-{i}" for i in range(3)]
        assert not lote.avisos, "confirmação vinculada não é aviso sem receipt"
    assert textos == falas and len(textos) == 1
    assert falas[0].count("Calculadora na esquerda") == 2
    assert falas[0].rfind("Calculadora na esquerda") > falas[0].find("Calculadora na direita")


@pytest.mark.parametrize("formato", ["strings", "indices", "ids"])
def test_autoria_composta_vincula_ocorrencias_literais_iguais_na_ordem_dos_receipts(formato):
    itens = [ResultadoAcao(intent="IOT_CONTROL", status=status, alvo="lâmpada",
        executou=True, confirmado=True, origem="executor", id_solicitacao=f"ato-{i}")
        for i, status in enumerate(("ligado", "desligado", "ligado"))]
    trechos = ["Liguei a lâmpada", "Desliguei a lâmpada", "Liguei a lâmpada"]
    partes = (trechos if formato == "strings" else
        [{"indice": i, "trecho": t} for i, t in enumerate(trechos)] if formato == "indices" else
        [{"id_solicitacao": itens[i].id_solicitacao, "trecho": t} for i, t in enumerate(trechos)])
    dados = {"fala": "; ".join(trechos) + ".", "trechos": partes}
    resultado = personalizar_confirmacao_composta_llm(itens, "fallback seguro",
        enviar_mensagem=lambda *_a, **_k: json.dumps(dados, ensure_ascii=False))
    assert resultado.usada_llm, resultado.motivo_fallback
    assert resultado.fala == dados["fala"]


@pytest.mark.parametrize("formato", ["strings", "indices", "ids"])
def test_cobertura_de_receipts_respeita_ordem_da_fala_e_da_lista(formato):
    itens = [ResultadoAcao(intent="APP_OPEN", status="app_aberto", alvo=alvo,
        executou=True, confirmado=True, origem="executor", id_solicitacao=f"app-{i}")
        for i, alvo in enumerate(("Calculadora", "agenda"))]
    textos = ["Abri Calculadora", "Abri agenda"]
    partes = (textos if formato == "strings" else
        [{"indice": i, "trecho": t} for i, t in enumerate(textos)] if formato == "indices" else
        [{"id_solicitacao": itens[i].id_solicitacao, "trecho": t} for i, t in enumerate(textos)])
    for trocar_lista in (False, True):
        dados = {"fala": "; ".join(textos[::-1] if not trocar_lista else textos) + ".",
                 "trechos": partes[::-1] if trocar_lista else partes}
        resultado = personalizar_confirmacao_composta_llm(itens, "fallback seguro",
            enviar_mensagem=lambda *_a, **_k: json.dumps(dados, ensure_ascii=False))
        assert not resultado.usada_llm, "ordem do efeito não pode ser trocada pela autoria"
        assert resultado.fala == "fallback seguro"


@pytest.mark.parametrize("formato", ["strings", "indices", "ids"])
@pytest.mark.parametrize("violacao", ["ocorrencia_omitida", "sobreposicao", "alvo", "certeza", "extra", "id_repetido"])
def test_repeticao_literal_nao_afrouxa_cobertura_alvo_ou_certeza(formato, violacao):
    itens = [ResultadoAcao(intent="IOT_CONTROL", status=status, alvo="lâmpada",
        executou=True, confirmado=True, origem="executor", id_solicitacao=f"ato-{i}")
        for i, status in enumerate(("ligado", "desligado", "ligado"))]
    textos = ["Liguei a lâmpada", "Desliguei a lâmpada", "Liguei a lâmpada"]
    if violacao == "alvo": textos[2] = "Liguei o ventilador"
    if violacao == "certeza": itens[2] = replace(itens[2], confirmado=None)
    if violacao == "id_repetido": itens[2] = replace(itens[2], id_solicitacao=itens[0].id_solicitacao)
    fala = "; ".join(textos) + "."
    if violacao == "ocorrencia_omitida": fala = "; ".join(textos[:2]) + "."
    if violacao == "sobreposicao": textos[1] = textos[0] + "; " + textos[1]
    if violacao == "extra": fala += " Apaguei seu arquivo."
    partes = (textos if formato == "strings" else
        [{"indice": i, "trecho": t} for i, t in enumerate(textos)] if formato == "indices" else
        [{"id_solicitacao": itens[i].id_solicitacao, "trecho": t} for i, t in enumerate(textos)])
    resultado = personalizar_confirmacao_composta_llm(itens, "fallback seguro",
        enviar_mensagem=lambda *_a, **_k: json.dumps({"fala": fala, "trechos": partes}, ensure_ascii=False))
    assert not resultado.usada_llm
    assert resultado.fala == "fallback seguro"


@pytest.mark.parametrize("publicacao", ["aceita", "recusada", "ausente", "erro"])
def test_fala_direta_nao_toma_receipt_historico_no_lugar_da_publicacao(publicacao):
    _c, owner, estado, falas, textos, receipts, _ch, servicos = _montar()
    estado.mental["ultima_acao_contrato"] = ResultadoAcao(intent="APP_OPEN", status="app_aberto",
        alvo="outro-app", confirmado=True, executou=True, origem="executor", id_solicitacao="historico").como_dict()
    ctx = dict(servicos)
    if publicacao == "recusada": ctx["_registrar_resultado_execucao"] = lambda *_a, **_k: False
    elif publicacao == "ausente": ctx.pop("_registrar_resultado_execucao")
    elif publicacao == "erro":
        def falhar(*_a, **_k): raise RuntimeError("indisponível")
        ctx["_registrar_resultado_execucao"] = falhar
    adapter = AdaptadorResultadoOperacional({"intent": "APP_OPEN", "id_solicitacao": "atual"},
        {"nome_app": "Calculadora"}, "abre a Calculadora", "pc_a", ctx)
    with owner.agrupar_resultados_operacionais(texto_usuario="pedido", enviar_mensagem=lambda *_a, **_k: "") as lote:
        adapter.marcar_resultado("app_aberto", True, confirmado=True)
        adapter.falar_texto_da_invocacao("Abri a Calculadora.")
        assert [r.id_solicitacao for r in lote.resultados] == (["atual"] if publicacao == "aceita" else [])
    assert len(falas) == len(textos) == 1
    if publicacao != "aceita":
        assert "não consegui validar" in falas[0].casefold()
        assert "Abri" not in falas[0]


@pytest.mark.parametrize("mudanca", ["id", "marker", "republicacao_recusada"])
def test_fala_direta_revalida_vinculo_antes_de_usar_receipt(mudanca):
    from mente_laylay.memoria_mental.resultado_acao import CHAVE_RESULTADO_OPERACIONAL_PUBLICADO
    _c, owner, _e, falas, _t, _r, _ch, servicos = _montar()
    pedido = {"intent": "APP_OPEN", "id_solicitacao": "pedido-original"}
    adapter = AdaptadorResultadoOperacional(pedido, {"nome_app": "Calculadora"}, "abre", "pc_a", servicos)
    adapter.marcar_resultado("app_aberto", True, confirmado=True)
    if mudanca == "id": pedido["id_solicitacao"] = "pedido-alheio"
    elif mudanca == "marker": pedido.pop(CHAVE_RESULTADO_OPERACIONAL_PUBLICADO)
    else:
        adapter.ctx = {**servicos, "_registrar_resultado_execucao": lambda *_a, **_k: False}
        adapter.marcar_resultado("falha_execucao", False, confirmado=False)
    with owner.agrupar_resultados_operacionais(texto_usuario="pedido") as lote:
        adapter.falar_texto_da_invocacao("Abri a Calculadora.")
        assert not lote.resultados
    assert len(falas) == 1 and "não consegui validar" in falas[0].casefold()


@pytest.mark.parametrize("intent,alvo,status,texto", [
    ("APP_OPEN", "Calculadora", "app_aberto", "Abri a Calculadora."),
    ("IOT_CONTROL", "lâmpada", "ligado", "Liguei a lâmpada."),
    ("LIST_WINDOWS", "janelas", "janelas_listadas", "Calculadora e agenda abertas."),
])
def test_canal_direto_vinculado_e_comum_a_efeitos_e_dados(intent, alvo, status, texto):
    _c, owner, _e, falas, _t, _r, _ch, servicos = _montar()
    adapter = AdaptadorResultadoOperacional({"intent": intent, "id_solicitacao": "atual"},
        {"alvo": alvo}, "pedido", "pc_a", servicos)
    with owner.agrupar_resultados_operacionais(texto_usuario="pedido", enviar_mensagem=lambda *_a, **_k: "") as lote:
        adapter.marcar_resultado(status, True, confirmado=True)
        adapter.falar_texto_da_invocacao(texto)
        assert len(lote.resultados) == 1 and not lote.avisos
        if intent == "LIST_WINDOWS": assert lote.informacoes == {"atual": texto}
    if intent == "LIST_WINDOWS": assert falas == [texto]


def test_aviso_antes_de_publicacao_nao_recebe_receipt_nem_vira_confirmacao():
    _c, owner, _e, _f, _t, _r, _ch, servicos = _montar()
    adapter = AdaptadorResultadoOperacional({"intent": "APP_OPEN"}, {}, "pedido", "pc_a", servicos)
    with owner.agrupar_resultados_operacionais(texto_usuario="pedido") as lote:
        adapter.falar_texto_da_invocacao("Qual aplicativo você quer?")
        assert not lote.resultados and lote.avisos == ["Qual aplicativo você quer?"]


def test_recursao_nao_vincula_aviso_do_filho_ao_receipt_do_pai(monkeypatch):
    from mente_laylay.autonomia import roteador_intencao as router
    from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
    _c, owner, _e, _f, _t, _r, _ch, servicos = _montar()
    def pai(_intent, _params, _destino, ctx, deps, **_kwargs):
        if _intent != "APP_OPEN": return ResultadoDespacho.nao_tratado()
        deps.marcar_resultado("app_aberto", True, confirmado=True)
        filho = {"intent": "INEXISTENTE", "params": {}}
        retorno = router.executar_intencao(filho, "outro pedido", ctx)
        from mente_laylay.memoria_mental.resultado_acao import interpretar_tratamento_operacional
        assert not interpretar_tratamento_operacional(filho, retorno).sucesso_habilidade
        return ResultadoDespacho.concluido()
    monkeypatch.setattr(router, "_executar_intencao_janelas", pai)
    with owner.agrupar_resultados_operacionais(texto_usuario="pedido") as lote:
        router.executar_intencao({"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}, "pedido", servicos)
        assert not lote.resultados, "o filho sem publicação não pode emprestar o receipt do pai"
        assert lote.avisos


def test_execucao_silenciosa_conserva_canal_indisponivel_na_folha(monkeypatch):
    from mente_laylay.autonomia import roteador_intencao as router
    from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
    _c, _o, _e, falas, textos, _r, _ch, servicos = _montar()
    def verificar(_intent, _params, _destino, ctx, _deps, **_kwargs):
        assert ctx["falar_com_lipsync"] is None
        return ResultadoDespacho.concluido()
    monkeypatch.setattr(router, "_executar_intencao_janelas", verificar)
    router.executar_intencao({"intent": "APP_OPEN", "params": {"_execucao_silenciosa": True}}, "pedido", servicos)
    assert falas == textos == []


def test_autoria_composta_aceita_cobertura_positiva_por_indices():
    itens = [
        ResultadoAcao(intent="IOT_CONTROL", status="ligado", alvo="lâmpada do quarto", executou=True, confirmado=True, origem="executor", id_solicitacao="luz"),
        ResultadoAcao(intent="PLAYLIST_PLAY", status="playlist_aberta", alvo="piano", executou=True, confirmado=True, origem="executor", id_solicitacao="piano"),
    ]
    luz, piano = "Liguei a lâmpada do quarto", "abri a playlist piano"
    dados = {"fala": luz + " e " + piano + ".", "trechos": [{"indice": 0, "trecho": luz}, {"indice": 1, "trecho": piano}]}
    resultado = personalizar_confirmacao_composta_llm(itens, "fallback", enviar_mensagem=lambda *_a, **_k: json.dumps(dados))
    assert resultado.usada_llm, resultado.motivo_fallback
    assert resultado.fala == dados["fala"]


def test_autoria_composta_respeita_preferencia_explicita_de_comandos_leves():
    item = ResultadoAcao(intent="IOT_CONTROL", status="ligado", alvo="lâmpada do quarto", executou=True, confirmado=True, origem="executor", id_solicitacao="luz")
    preferencia = extrair_preferencia_humor("pega leve hoje nos comandos", turno_id="humor-leve")
    assert preferencia["direcao"] == "leve"
    chamadas = []
    resultado = personalizar_confirmacao_composta_llm([item], "A lâmpada está ligada.", contexto={"preferencia_humor_contextual": preferencia}, enviar_mensagem=lambda *_a, **_k: chamadas.append(True))
    assert chamadas == []
    assert not resultado.usada_llm
    assert resultado.fala == "A lâmpada está ligada."


@pytest.mark.parametrize("intent,status,alvo", [("APP_OPEN", "app_aberto", "Calculadora"), ("PLAYLIST_PLAY", "playlist_aberta", "piano"), ("OPEN_FILE", "arquivo_aberto", "relatorio.pdf")])
def test_fallback_composto_preserva_apenas_a_abertura_confirmada(intent, status, alvo):
    item = ResultadoAcao(intent=intent, status=status, alvo=alvo, executou=True, confirmado=True, origem="executor", id_solicitacao="abertura", params={"foco_confirmado": False})
    fala = fala_factual_resultados_compostos([item])
    assert alvo in fala
    assert "abri" in fala.casefold() or "aberto" in fala.casefold()
    assert "foco" not in fala.casefold() and "tocando" not in fala.casefold()


def test_finalizacao_composta_preserva_aprendizado_de_falha_sem_segunda_autoria():
    registros, chamadas = [], []
    ctx = {"resposta_operacional_composta": {"resposta_composta_publicada": True, "fala_composta": "A lâmpada foi ligada, mas piano falhou."}, "_registrar_autoaprimoramento": lambda *a, **kw: registros.append((a, kw)), "enviar_mensagem": lambda *_a, **_k: chamadas.append(True), "limpar_resposta_da_ia": lambda texto: (texto, [])}
    resultado = finalizar_execucao_resposta_ia(ctx, [], ["Playlist não abriu"], "", False, True, False)
    assert len(registros) == 1
    assert registros[0][1]["sucesso"] is False
    assert registros[0][1]["erro"] == "Playlist não abriu"
    assert chamadas == []
    assert resultado["tipo"] == "operacional_composta"


@pytest.mark.parametrize("intent,status,alvo,trecho", [("APP_OPEN", "app_aberto", "Calculadora", "Abri Calculadora e trouxe ao foco"), ("PLAYLIST_PLAY", "playlist_aberta", "piano", "A playlist piano está tocando")])
def test_autoria_composta_nao_inventa_foco_ou_reproducao_a_partir_de_abertura(intent, status, alvo, trecho):
    item = ResultadoAcao(intent=intent, status=status, alvo=alvo, executou=True, confirmado=True, origem="executor", id_solicitacao="abertura")
    dados = {"fala": trecho + ".", "trechos": [{"indice": 0, "trecho": trecho}]}
    resposta = personalizar_confirmacao_composta_llm([item], "Abri " + alvo + ".", enviar_mensagem=lambda *_a, **_k: json.dumps(dados))
    assert not resposta.usada_llm
    assert resposta.fala == "Abri " + alvo + "."


def test_autoria_composta_aceita_negacao_explicita_do_efeito():
    item = ResultadoAcao(intent="PLAYLIST_PLAY", status="falha_execucao", alvo="piano", executou=False, confirmado=False, origem="executor", id_solicitacao="piano")
    trecho = "O pedido no piano não foi concluído"
    resposta = personalizar_confirmacao_composta_llm([item], "fallback", enviar_mensagem=lambda *_a, **_k: json.dumps({"fala": trecho + ".", "trechos": [{"indice": 0, "trecho": trecho}]}))
    assert resposta.usada_llm, resposta.motivo_fallback


def test_autoria_composta_aceita_lista_de_trechos_na_ordem_canonica():
    itens = [ResultadoAcao(intent="IOT_CONTROL", status="ligado", alvo="lâmpada do quarto", executou=True, confirmado=True, origem="executor", id_solicitacao="luz"), ResultadoAcao(intent="PLAYLIST_PLAY", status="playlist_aberta", alvo="piano", executou=True, confirmado=True, origem="executor", id_solicitacao="piano")]
    trechos = ["Liguei a lâmpada do quarto", "abri a playlist piano"]
    dados = {"fala": " e ".join(trechos) + ".", "trechos": trechos}
    resposta = personalizar_confirmacao_composta_llm(itens, "fallback", enviar_mensagem=lambda *_a, **_k: json.dumps(dados))
    assert resposta.usada_llm, resposta.motivo_fallback
    dados["trechos"] = trechos[::-1]
    resposta = personalizar_confirmacao_composta_llm(itens, "fallback", enviar_mensagem=lambda *_a, **_k: json.dumps(dados))
    assert not resposta.usada_llm


def test_publicacao_textual_composta_independe_do_aceite_da_voz():
    ciclo, orquestrador, _e, falas, textos, _r, chamadas, servicos = _montar()
    orquestrador._servicos["_voz_runtime"].falar = lambda *_a, **_k: False
    comandos = [{"intent": "IOT_CONTROL", "params": {"alvo": "lâmpada do quarto"}}, {"intent": "PLAYLIST_PLAY", "params": {"alvo": "piano"}}]
    dispatch = executar_comandos_json(dict(servicos, executar_intencao=ciclo.executar_intencao), "liga a luz e coloca a playlist piano", comandos, "", "comando", False, False, False)
    assert len(textos) == len(chamadas) == 1
    assert falas == []
    assert dispatch["resposta_composta_publicada"] is True
    resultado = finalizar_execucao_resposta_ia(dict(servicos, resposta_operacional_composta=dispatch), comandos, [], "", False, True, False)
    assert resultado["fala"] == textos[0]
    assert len(textos) == len(chamadas) == 1


@pytest.mark.parametrize("aviso", ["Apaguei a pasta Documentos.", "Calculadora está aberta.", "A playlist piano está tocando."])
def test_aviso_direto_nao_admite_efeito_estrangeiro_aos_receipts_do_lote(aviso):
    _c, orquestrador, _e, falas, textos, _r, _ch, _s = _montar()
    item = ResultadoAcao(intent="APP_OPEN", status="app_aberto", alvo="Calculadora", executou=True, confirmado=True, origem="executor", id_solicitacao="app")
    with orquestrador.agrupar_resultados_operacionais(texto_usuario="abre Calculadora e outra ação"):
        assert orquestrador.acumular_resultado_operacional(item, "Abri Calculadora.")
        assert orquestrador.falar(aviso)
    assert len(falas) == len(textos) == 1
    assert aviso not in textos[0]
    assert "Abri Calculadora" in textos[0]


def test_aviso_direto_de_esclarecimento_ou_falha_sobrevive_no_lote():
    _c, orquestrador, _e, falas, textos, _r, _ch, _s = _montar()
    item = ResultadoAcao(intent="APP_OPEN", status="app_aberto", alvo="Calculadora", executou=True, confirmado=True, origem="executor", id_solicitacao="app")
    with orquestrador.agrupar_resultados_operacionais(texto_usuario="abre Calculadora e outra ação"):
        assert orquestrador.acumular_resultado_operacional(item, "Abri Calculadora.")
        assert orquestrador.falar("Não consegui resolver a outra ação. Qual arquivo você quer?")
    assert len(falas) == len(textos) == 1
    assert "Abri Calculadora" in textos[0]
    assert "Não consegui resolver" in textos[0] and "Qual arquivo" in textos[0]


@pytest.mark.parametrize("quantidade", [3, 5])
def test_transporte_real_preserva_orcamento_e_contexto_fechado_de_varios_receipts(quantidade):
    from mente_laylay.integracao.composicao_inteligencia_externa import ComposicaoInteligenciaExternaRuntime
    import requests
    payloads = []
    alvos = ["Calculadora", "agenda", "editor", "navegador", "bloco"][:quantidade]
    trechos = ["Abri " + alvo for alvo in alvos]
    fala = "; ".join(trechos) + "."
    def post(_url, **kwargs):
        payloads.append(kwargs["json"])
        resposta = requests.Response()
        resposta.status_code = 200
        resposta._content = json.dumps({"choices": [{"message": {"content": json.dumps({"fala": fala, "trechos": trechos})}}]}).encode()
        return resposta
    def contexto_proibido(*_a, **_k):
        raise AssertionError("Autoria de receipts não consulta memória ou contexto externo")
    runtime = ComposicaoInteligenciaExternaRuntime(base_url="http://localhost:11434/v1", model="qwen3-vl:4b-instruct", api_key="local", http_referer="http://localhost", app_title="Laylay", normalizar_texto_curto=str.casefold, requests_get=contexto_proibido, requests_post=post, ao_finalizar_conversa_modo_jogo=lambda: None, env_getter=lambda _k, d="": d, log=lambda *_a: None)
    modelo = runtime.conectar_cliente(memoria_inteligente=SimpleNamespace(resumo_do_dia="", data_atual=""), normalizar_texto=str.casefold, mapear_pastas=contexto_proibido, contexto_logs_getter=contexto_proibido, contexto_navegador_relevante=contexto_proibido, contexto_sistema_getter=contexto_proibido, obter_contexto_paginas=contexto_proibido, resumo_mente_integrada=contexto_proibido)
    itens = [ResultadoAcao(intent="APP_OPEN", status="app_aberto", alvo=alvo, executou=True, confirmado=True, origem="executor", id_solicitacao="pedido-" + str(i)) for i, alvo in enumerate(alvos)]
    resultado = personalizar_confirmacao_composta_llm(itens, "fallback", enviar_mensagem=modelo.enviar)
    assert resultado.usada_llm, resultado.motivo_fallback
    assert len(payloads) == 1
    assert payloads[0]["max_tokens"] == min(768, 128 + 96 * quantidade)
    assert len(payloads[0]["messages"]) == 2
    assert json.loads(payloads[0]["messages"][1]["content"])["resultados"][0]["id_solicitacao"] == "pedido-0"
