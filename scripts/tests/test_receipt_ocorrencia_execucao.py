"""Receipt pertence ao turno capturado antes do efeito, não à frase vigente."""

from copy import deepcopy

import pytest

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.cognicao.contratos_turno import ContratoOcorrenciaTurno
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno
from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime
from mente_laylay.integracao.contexto_execucao_ia import ContextoIntencaoRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.resultado_acao import CHAVE_RESULTADO_OPERACIONAL_PUBLICADO
from scripts.tests.test_publicacao_ocorrencia_turno import _frame, _nova_ocorrencia


DOMINIOS = (
    ("abre a Calculadora", "APP_OPEN", {"nome_app": "Calculadora"}, "app_iniciado_focado"),
    ("liga a lâmpada", "IOT_CONTROL", {"alvo": "lampada_quarto", "acao": "ligar"}, "ligado"),
    ("cria a playlist foco", "PLAYLIST_CREATE", {"nome_playlist": "foco"}, "playlist_criada"),
)


def _montar(texto, *, base_callback=None):
    original = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=original)
    consumos = []
    ns = {
        "_estado_compartilhado_runtime": estado,
        "_registrar_resultado_execucao_base": base_callback or (lambda *_a, **_k: consumos.append("base")),
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_concluir_correcao_interpretacao_mente": lambda *_a, **_k: {},
        "_limpar_pergunta_aberta": lambda: consumos.append("limpar"),
        "_suspender_topico_conversacional": lambda *_: consumos.append("suspender"),
        "print": lambda *_: None,
    }
    publicador = AdaptadoresAplicacaoRuntime(lambda: ns)
    servicos = {"_registrar_resultado_execucao": publicador.registrar_resultado_execucao}
    vincular = getattr(publicador, "vincular_registro_resultado_execucao", None)
    if callable(vincular): servicos["_vincular_registro_resultado_execucao"] = vincular
    contexto = ContextoIntencaoRuntime(namespace_getter=lambda: servicos,
        estado_getter=lambda: estado.snapshot()["mental"])
    return estado, publicador, contexto, consumos, original


@pytest.mark.parametrize("texto,intent,params,status", DOMINIOS)
@pytest.mark.parametrize("troca", ("controle", "mesma_frase", "outra_frase", "vazio"))
def test_resultado_da_execucao_antiga_nao_alimenta_plano_e_contexto_do_novo_turno(texto, intent, params, status, troca):
    estado, publicador, contexto, consumos, original = _montar(texto)
    ctx = contexto.montar()
    pedido = {"intent": intent, "params": params, "id_solicitacao": "pedido-capturado"}
    adaptador = AdaptadorResultadoOperacional(pedido, params, texto, "pc_a", ctx)
    if troca != "controle":
        novo = {} if troca == "vazio" else _nova_ocorrencia(original) if troca == "mesma_frase" else _frame("como você está?")
        estado.substituir("mental", novo)
    antes = estado.snapshot()
    adaptador.marcar_resultado(status, True, confirmado=True, evidencia_confirmacao="efeito observado do pedido original")
    mental = estado.snapshot()["mental"]
    if troca == "controle":
        assert consumos == ["base", "limpar", "suspender"]
        assert mental["plano_turno_atual"]["comandos"][0]["id_solicitacao"] == "pedido-capturado"
        assert pedido[CHAVE_RESULTADO_OPERACIONAL_PUBLICADO] == "pedido-capturado"
        assert not mental.get("resultados_execucao_tardios")
    else:
        assert consumos == [], "primeira fronteira: receipt estrangeiro não chega a base/aprendizado/limpadores"
        tardios = mental.pop("resultados_execucao_tardios", [])
        assert mental == antes["mental"], "plano, última ação e pendências vigentes permanecem intactos"
        assert CHAVE_RESULTADO_OPERACIONAL_PUBLICADO not in pedido
        assert adaptador._receipt_publicado is None
        assert len(tardios) == 1, "efeito real tardio deve ficar disponível para reconciliação"
        assert tardios[0]["turno_id"] == str(original["turno_atual"]["id"])
        receipt = tardios[0]["resultado"]
        assert receipt["id_solicitacao"] == "pedido-capturado"
        assert receipt["intent"] == intent and receipt["status"] == status and receipt["confirmado"] is True


@pytest.mark.parametrize("texto,intent,params,status", DOMINIOS)
def test_troca_durante_consumidor_nao_restaura_plano_antigo_no_commit(texto, intent, params, status):
    estado, publicador, contexto, consumos, original = _montar(texto)
    novos = []
    def mudar(*_a, **_k):
        estado.substituir("mental", _nova_ocorrencia(original))
        novos.append(estado.snapshot())
    publicador._ns()["_registrar_resultado_execucao_base"] = mudar
    pedido = {"intent": intent, "id_solicitacao": "pedido-capturado"}
    adaptador = AdaptadorResultadoOperacional(pedido, params, texto, "pc_a", contexto.montar())
    adaptador.marcar_resultado(status, True, confirmado=True)
    atual = estado.snapshot()["mental"]
    assert novos, "a publicação começou legitimamente e alcançou a intercalação"
    atual.pop("resultados_execucao_tardios", None)
    assert atual == novos[-1]["mental"], "commit não pode restaurar plano capturado antes do callback"
    assert consumos == [] and CHAVE_RESULTADO_OPERACIONAL_PUBLICADO not in pedido


def test_origem_do_callback_nao_pode_ser_substituida_por_contexto_do_receipt():
    texto, intent, params, status = DOMINIOS[0]
    estado, _, contexto, consumos, original = _montar(texto)
    ctx = contexto.montar()
    novo = _nova_ocorrencia(original)
    estado.substituir("mental", novo)
    adaptador = AdaptadorResultadoOperacional({"intent": intent}, params, texto, "pc_a", ctx)
    adaptador.marcar_resultado(status, True, confirmado=True,
        contexto_resultado={"turno_id": novo["turno_atual"]["id"], "ocorrencia_turno": {"turno_id": novo["turno_atual"]["id"]}})
    assert consumos == []
    assert estado.obter_copia("mental", "resultados_execucao_tardios")[0]["turno_id"] == str(original["turno_atual"]["id"])


def test_contexto_legado_sem_factory_conserva_callback_original():
    registrar = lambda *_a, **_k: True
    contexto = ContextoIntencaoRuntime(namespace_getter=lambda: {"_registrar_resultado_execucao": registrar}, estado_getter=lambda: {})
    assert contexto.montar()["_registrar_resultado_execucao"] is registrar


@pytest.mark.parametrize("frase", ["coloca ela à esquerda", "fecha esse aplicativo", "maximiza ele"])
@pytest.mark.parametrize("vinculado", [True, False])
def test_resultado_tardio_nao_troca_referente_do_pedido_natural_atual(frase, vinculado):
    from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
    from mente_laylay.memoria_mental.contexto_imediato import referencia_contextual_imediata
    estado, publicador, contexto, _, _ = _montar("abre a Calculadora")
    ns = publicador._ns()
    base = EstadoContextoRuntime(namespace_getter=lambda: ns, estado_runtime_getter=lambda: estado)
    ns.update(_registrar_resultado_execucao_base=base.registrar_resultado_execucao,
        _normalizar_texto_com_apelidos=str.casefold, _atualizar_foco_vivo=base.atualizar_foco_vivo)
    ctx_antigo = contexto.montar()
    if not vinculado:
        # Contraprova explícita da porta legada: remove SOMENTE o vínculo,
        # mantendo publicador, contexto compartilhado e resolver reais.
        ctx_antigo["_registrar_resultado_execucao"] = publicador.registrar_resultado_execucao
    velho = AdaptadorResultadoOperacional({"intent":"APP_OPEN"}, {"nome_app":"Calculadora"},
        "abre a Calculadora", "pc_a", ctx_antigo)
    estado.substituir("mental", _frame("abre o Bloco de Notas"))
    novo = AdaptadorResultadoOperacional({"intent":"APP_OPEN"}, {"nome_app":"Bloco de Notas"},
        "abre o Bloco de Notas", "pc_a", contexto.montar())
    novo.marcar_resultado("app_iniciado_focado", True, confirmado=True)
    antes = referencia_contextual_imediata(mente_integrada_estado=estado.retrato_dominio("mental"),
        foco_vivo={}, texto_atual=frase, dominio_preferido="app")
    assert antes["alvo"] == "Bloco de Notas", "controle: referente atual chegou ao resolver"
    velho.marcar_resultado("app_iniciado_focado", True, confirmado=True)
    depois = referencia_contextual_imediata(mente_integrada_estado=estado.retrato_dominio("mental"),
        foco_vivo={}, texto_atual=frase, dominio_preferido="app")
    assert depois["alvo"] == ("Bloco de Notas" if vinculado else "Calculadora")
    assert bool(estado.mental.get("resultados_execucao_tardios")) is vinculado


def test_troca_entre_derivacao_e_commit_nao_anexa_receipt_a_plano_novo():
    estado, _, contexto, _, original = _montar("abre a Calculadora")
    adaptador = AdaptadorResultadoOperacional({"intent":"APP_OPEN"}, {"nome_app":"Calculadora"},
        "abre a Calculadora", "pc_a", contexto.montar())
    atualizar = estado.atualizar
    novo = _nova_ocorrencia(original)
    def trocar(dominio, callback, **campos):
        estado.substituir("mental", novo)
        estado.atualizar = atualizar
        return atualizar(dominio, callback, **campos)
    estado.atualizar = trocar
    adaptador.marcar_resultado("app_iniciado_focado", True, confirmado=True)
    atual = estado.retrato_dominio("mental")
    assert atual.pop("resultados_execucao_tardios")
    assert atual == EstadoCompartilhadoRuntime(mental=novo).retrato_dominio("mental")
    assert adaptador._receipt_publicado is None


def test_fallback_do_ciclo_nao_reinterpreta_receipt_tardio_como_turno_atual():
    from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
    estado, publicador, contexto, consumos, original = _montar("abre a Calculadora")
    ns = {**publicador._ns(), "_registrar_resultado_execucao": publicador.registrar_resultado_execucao}
    ciclo = CicloComandosRuntime(namespace_getter=lambda: ns, contexto_intencao_runtime=contexto,
        log=lambda *_a: None)
    resolucao = ciclo._montar_contexto_resolucao()
    estado.substituir("mental", _nova_ocorrencia(original))
    aceito = resolucao["registrar_resultado_execucao"]({"intent":"APP_OPEN",
        "id_solicitacao":"fallback-antigo","params":{"nome_app":"Calculadora"},
        "status":"app_iniciado_focado","confirmado":True,"executou":True,"origem":"executor"},
        "abre a Calculadora",True,origem="executor",status="app_iniciado_focado")
    assert aceito is False and consumos == [], "fallback não pode contornar vínculo do contexto de execução"
    assert len(estado.mental["resultados_execucao_tardios"]) == 1


@pytest.mark.parametrize("texto,intent,params,status", DOMINIOS)
@pytest.mark.parametrize("fronteira", ["entrada_base", "foco"])
def test_commit_interno_do_contexto_nao_restaura_turno_superado(texto, intent, params, status, fronteira):
    from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
    estado, publicador, contexto, consumos, _ = _montar(texto)
    ns = publicador._ns()
    base = EstadoContextoRuntime(namespace_getter=lambda: ns, estado_runtime_getter=lambda: estado)
    atual = EstadoCompartilhadoRuntime(mental=_frame("abre o Bloco de Notas")).retrato_dominio("mental")
    trocas = []
    def trocar():
        if not trocas:
            estado.substituir("mental", atual)
            trocas.append(True)
    def registrar(*args, **kwargs):
        if fronteira == "entrada_base": trocar()
        return base.registrar_resultado_execucao(*args, **kwargs)
    def foco(mental, **kwargs):
        if fronteira == "foco": trocar()
        return base.atualizar_foco_vivo(mental, **kwargs)
    ns.update(_registrar_resultado_execucao_base=registrar,
        _normalizar_texto_com_apelidos=str.casefold, _atualizar_foco_vivo=foco)
    adapter = AdaptadorResultadoOperacional({"intent": intent, "id_solicitacao": "receipt-na-base"},
        params, texto, "pc_a", contexto.montar())
    adapter.marcar_resultado(status, True, confirmado=True)
    assert trocas, "teste deve alcançar a fronteira interna, não falhar no import"
    depois = estado.retrato_dominio("mental")
    tardios = depois.pop("resultados_execucao_tardios", [])
    assert depois == atual, "primeira RED: substituição interna não pode reintroduzir contexto/plano antigo"
    assert len(tardios) == 1 and tardios[0]["resultado"]["id_solicitacao"] == "receipt-na-base"
    assert adapter._receipt_publicado is None and consumos == []


def test_commit_contextual_rederiva_sobre_mudanca_concorrente_do_mesmo_turno():
    from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
    estado, publicador, contexto, _, _ = _montar("abre a Calculadora")
    ns = publicador._ns()
    base = EstadoContextoRuntime(namespace_getter=lambda: ns, estado_runtime_getter=lambda: estado)
    chamadas = []
    def foco(mental, **kwargs):
        chamadas.append(True)
        if len(chamadas) == 1:
            estado.atualizar_campos("mental", observacao_independente="preservar")
        return base.atualizar_foco_vivo(mental, **kwargs)
    ns.update(_registrar_resultado_execucao_base=base.registrar_resultado_execucao,
        _normalizar_texto_com_apelidos=str.casefold, _atualizar_foco_vivo=foco)
    adapter = AdaptadorResultadoOperacional({"intent":"APP_OPEN"}, {"nome_app":"Calculadora"},
        "abre a Calculadora", "pc_a", contexto.montar())
    adapter.marcar_resultado("app_iniciado_focado", True, confirmado=True)
    assert chamadas, "derivação real deve ser exercitada"
    assert estado.mental.get("observacao_independente") == "preservar", "CAS não apaga dados concorrentes do mesmo turno"
    assert adapter._receipt_publicado is not None
    assert estado.mental["ultimo_app_janela"] == "Calculadora"
    assert not estado.mental.get("resultados_execucao_tardios")


def test_derivador_contextual_nao_bloqueia_leitor_em_outra_thread():
    from threading import Event, Thread
    from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
    estado, publicador, contexto, _, _ = _montar("abre a Calculadora")
    ns = publicador._ns()
    base = EstadoContextoRuntime(namespace_getter=lambda: ns, estado_runtime_getter=lambda: estado)
    leituras, threads = [], []
    def foco(mental, **kwargs):
        terminou = Event()
        thread = Thread(target=lambda: (estado.retrato_dominio("mental"), terminou.set()))
        threads.append(thread)
        thread.start()
        leituras.append(terminou.wait(1))
        return base.atualizar_foco_vivo(mental, **kwargs)
    ns.update(_registrar_resultado_execucao_base=base.registrar_resultado_execucao,
        _normalizar_texto_com_apelidos=str.casefold, _atualizar_foco_vivo=foco)
    adapter = AdaptadorResultadoOperacional({"intent":"APP_OPEN"}, {"nome_app":"Calculadora"},
        "abre a Calculadora", "pc_a", contexto.montar())
    try:
        adapter.marcar_resultado("app_iniciado_focado", True, confirmado=True)
    finally:
        for thread in threads: thread.join(timeout=2)
    assert leituras and all(leituras), "derivador externo não pode ficar sob o lock central"
    assert adapter._receipt_publicado is not None


def test_contencao_contextual_limitada_preserva_receipt_sem_promover_sucesso():
    from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
    estado, publicador, contexto, consumos, _ = _montar("abre a Calculadora")
    ns = publicador._ns()
    base = EstadoContextoRuntime(namespace_getter=lambda: ns, estado_runtime_getter=lambda: estado)
    tentativas = []
    def foco(mental, **kwargs):
        tentativas.append(True)
        estado.atualizar_campos("mental", atualizacao_independente=len(tentativas))
        return base.atualizar_foco_vivo(mental, **kwargs)
    ns.update(_registrar_resultado_execucao_base=base.registrar_resultado_execucao,
        _normalizar_texto_com_apelidos=str.casefold, _atualizar_foco_vivo=foco)
    adapter = AdaptadorResultadoOperacional({"intent":"APP_OPEN", "id_solicitacao":"contencao"},
        {"nome_app":"Calculadora"}, "abre a Calculadora", "pc_a", contexto.montar())
    adapter.marcar_resultado("app_iniciado_focado", True, confirmado=True)
    assert len(tentativas) == 4, "contenção não pode prender o fluxo indefinidamente"
    assert estado.mental["atualizacao_independente"] == 4
    assert not estado.mental.get("ultima_acao_contrato")
    assert not estado.mental["plano_turno_atual"]["comandos"]
    assert not consumos and adapter._receipt_publicado is None
    registros = estado.mental["resultados_execucao_tardios"]
    assert len(registros) == 1 and registros[0]["motivo"] == "commit_contextual_recusado"
    assert registros[0]["resultado"]["id_solicitacao"] == "contencao"


@pytest.mark.parametrize("texto,intent,params,status", DOMINIOS)
@pytest.mark.parametrize("correlacionada", [True, False])
@pytest.mark.parametrize("troca", ["controle", "pendencia_derivacao", "pendencia_commit", "turno_commit", "historico_commit"])
def test_consumo_da_correcao_confere_ocorrencia_e_pendencia_no_commit(
    texto, intent, params, status, correlacionada, troca, monkeypatch,
):
    from types import SimpleNamespace
    from mente_laylay.memoria_mental.correcoes_interpretacao import (
        abrir_correcao_interpretacao, concluir_correcao_interpretacao,
    )
    estado, publicador, contexto, _, original = _montar(texto)
    pendente = abrir_correcao_interpretacao({"ultima_entrada":"pedido interpretado errado"},
        texto if correlacionada else "corrige outro pedido", eh_correcao=True, agora=100)
    outra = {**pendente, "ts":101}  # Mesma frase, outra ocorrência da pendência.
    estado.atualizar_campos("mental", correcao_interpretacao_pendente=pendente,
        historico_correcoes_interpretacao=[{"origem":"anterior"}])
    observados, trocas = [], []
    ns = publicador._ns()
    ns["_especialista_neural_comandos_runtime"] = SimpleNamespace(
        observar_resultado=lambda *_a, **_k: None,
        observar_correcao=lambda registro: observados.append(deepcopy(registro)),
    )
    def derivar(pendente_recebida, **kwargs):
        resultado = concluir_correcao_interpretacao(pendente_recebida, **kwargs, agora=102)
        if troca == "pendencia_derivacao":
            estado.atualizar_campos("mental", correcao_interpretacao_pendente=outra)
            trocas.append(True)
        return resultado
    ns["_concluir_correcao_interpretacao_mente"] = derivar
    def intercalar():
        if trocas or troca not in {"pendencia_commit", "turno_commit", "historico_commit"}: return
        trocas.append(True)
        if troca == "turno_commit":
            novo = _nova_ocorrencia(original)
            novo.update(correcao_interpretacao_pendente=outra,
                historico_correcoes_interpretacao=[{"origem":"turno_novo"}])
            estado.substituir("mental", novo)
        elif troca == "pendencia_commit":
            atualizar_campos("mental", correcao_interpretacao_pendente=outra)
        else:
            atualizar_campos("mental", historico_correcoes_interpretacao=[{"origem":"concorrente"}])
    atualizar_campos, transacionar = estado.atualizar_campos, estado.atualizar_dominios
    def campos(dominio, **valores):
        if "correcao_interpretacao_pendente" in valores: intercalar()
        return atualizar_campos(dominio, **valores)
    def transacao(dominios, callback):
        intercalar()
        return transacionar(dominios, callback)
    monkeypatch.setattr(estado, "atualizar_campos", campos)
    monkeypatch.setattr(estado, "atualizar_dominios", transacao)
    adapter = AdaptadorResultadoOperacional({"intent":intent, "id_solicitacao":"correcao-capturada"},
        params, texto, "pc_a", contexto.montar())
    adapter.marcar_resultado(status, True, confirmado=True)
    if troca != "controle": assert trocas, "intercalação deve alcançar a fronteira real"
    mental = estado.retrato_dominio("mental")
    if troca in {"pendencia_derivacao", "pendencia_commit", "turno_commit"}:
        assert mental["correcao_interpretacao_pendente"] == outra, "não consumir outra pendência, mesmo com texto igual"
        assert not observados, "correção não consumida não gera aprendizado"
        assert mental["historico_correcoes_interpretacao"] == [
            {"origem":"turno_novo" if troca == "turno_commit" else "anterior"}]
        if troca == "turno_commit":
            assert adapter._receipt_publicado is None
            assert len(mental["resultados_execucao_tardios"]) == 1
        else:
            assert adapter._receipt_publicado is not None, "receipt vigente independe da pendência concorrente"
    else:
        assert mental["correcao_interpretacao_pendente"] == {}
        historico = mental["historico_correcoes_interpretacao"]
        assert historico[0] == {"origem":"concorrente" if troca == "historico_commit" else "anterior"}
        assert len(historico) == (2 if correlacionada else 1)
        assert len(observados) == int(correlacionada)
        if correlacionada:
            assert historico[-1]["intent_correta"] == intent
            assert historico[-1]["params_corretos"] == params


@pytest.mark.parametrize("troca", ["mesmo_turno", "outro_turno", "erro_observador"])
def test_aprendizado_recebe_evento_ja_consumido_sem_mutar_historico_ou_pendencia_nova(troca):
    from types import SimpleNamespace
    from mente_laylay.memoria_mental.correcoes_interpretacao import (
        abrir_correcao_interpretacao, concluir_correcao_interpretacao,
    )
    estado, publicador, contexto, _, original = _montar("abre a Calculadora")
    pendente = abrir_correcao_interpretacao({}, "abre a Calculadora", eh_correcao=True, agora=100)
    estado.atualizar_campos("mental", correcao_interpretacao_pendente=pendente)
    outra, observados = {**pendente, "ts":101}, []
    def observar(correcao):
        antes = estado.retrato_dominio("mental")
        observados.append(antes)
        assert antes["correcao_interpretacao_pendente"] == {}, "evento só sai depois do consumo"
        assert antes["historico_correcoes_interpretacao"][-1] == correcao
        correcao["intent_correta"] = "FORJADA"
        if troca == "outro_turno":
            novo = _nova_ocorrencia(original)
            novo.update(correcao_interpretacao_pendente=outra,
                historico_correcoes_interpretacao=[{"origem":"novo_turno"}])
            estado.substituir("mental", novo)
        else:
            estado.atualizar_campos("mental", correcao_interpretacao_pendente=outra)
        if troca == "erro_observador": raise RuntimeError("observador indisponível")
    ns = publicador._ns()
    ns.update(_concluir_correcao_interpretacao_mente=concluir_correcao_interpretacao,
        _especialista_neural_comandos_runtime=SimpleNamespace(
            observar_resultado=lambda *_a, **_k: None, observar_correcao=observar))
    adapter = AdaptadorResultadoOperacional({"intent":"APP_OPEN"}, {"nome_app":"Calculadora"},
        "abre a Calculadora", "pc_a", contexto.montar())
    adapter.marcar_resultado("app_iniciado_focado", True, confirmado=True)
    assert len(observados) == 1
    assert estado.mental["correcao_interpretacao_pendente"] == outra
    historico = estado.mental["historico_correcoes_interpretacao"]
    if troca == "outro_turno": assert historico == [{"origem":"novo_turno"}]
    else: assert historico[-1]["intent_correta"] == "APP_OPEN"


def test_dois_receipts_concorrentes_consumem_uma_correcao_apenas_uma_vez():
    from threading import Barrier, Thread
    from types import SimpleNamespace
    from mente_laylay.memoria_mental.correcoes_interpretacao import (
        abrir_correcao_interpretacao, concluir_correcao_interpretacao,
    )
    estado, publicador, contexto, _, _ = _montar("abre a Calculadora")
    pendente = abrir_correcao_interpretacao({}, "abre a Calculadora", eh_correcao=True, agora=100)
    estado.atualizar_campos("mental", correcao_interpretacao_pendente=pendente,
        historico_correcoes_interpretacao=[{"numero":n} for n in range(30)])
    barreira, observados, erros = Barrier(2, timeout=5), [], []
    def derivar(registro, **kwargs):
        concluida = concluir_correcao_interpretacao(registro, **kwargs, agora=101)
        barreira.wait()
        return concluida
    ns = publicador._ns()
    ns.update(_concluir_correcao_interpretacao_mente=derivar,
        _especialista_neural_comandos_runtime=SimpleNamespace(
            observar_resultado=lambda *_a, **_k: None,
            observar_correcao=lambda correcao: observados.append(deepcopy(correcao))))
    adapters = [AdaptadorResultadoOperacional({"intent":"APP_OPEN", "id_solicitacao":f"correcao-{n}"},
        {"nome_app":"Calculadora"}, "abre a Calculadora", "pc_a", contexto.montar()) for n in range(2)]
    def publicar(adapter):
        try: adapter.marcar_resultado("app_iniciado_focado", True, confirmado=True)
        except Exception as erro: erros.append(erro)
    threads = [Thread(target=publicar, args=(adapter,), daemon=True) for adapter in adapters]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=7)
    assert not erros and all(not thread.is_alive() for thread in threads)
    assert all(adapter._receipt_publicado is not None for adapter in adapters)
    assert len(estado.mental["plano_turno_atual"]["comandos"]) == 2
    assert estado.mental["correcao_interpretacao_pendente"] == {}
    historico = estado.mental["historico_correcoes_interpretacao"]
    assert len(historico) == 30 and historico[0] == {"numero":1}
    assert historico[-1]["intent_correta"] == "APP_OPEN" and len(observados) == 1


def _montar_entrada_vinculada(estado, publicador, *, loop_getter=lambda: None, servicos=None):
    from mente_laylay.integracao.composicao_entrada_interacao import ComposicaoEntradaInteracaoRuntime
    from scripts.tests.test_composicao_entrada_interacao import _com_memoria
    ns = _com_memoria({**publicador._ns(),
        "_registrar_resultado_execucao":publicador.registrar_resultado_execucao,
        "_vincular_registro_resultado_execucao":publicador.vincular_registro_resultado_execucao,
        **(servicos or {})})
    composicao = ComposicaoEntradaInteracaoRuntime(servicos=ns,
        estado_mental_getter=lambda: estado.retrato_dominio("mental"), sites_diretos={}, apps_map={})
    comandos, chat = composicao.conectar(servicos=ns, loop_getter=loop_getter,
        estado_chat_getter=lambda: {}, memoria_sqlite=None)
    return composicao, comandos, chat


@pytest.mark.parametrize("texto,intent,params,status", DOMINIOS)
@pytest.mark.parametrize("porta", ["comandos", "chat"])
def test_composicao_de_entrada_vincula_publicador_antes_dos_callers_legados(texto, intent, params, status, porta):
    estado, publicador, _, consumos, original = _montar(texto)
    _, comandos, chat = _montar_entrada_vinculada(estado, publicador)
    runtime = comandos if porta == "comandos" else chat
    callback = runtime.namespace_getter()["_registrar_resultado_execucao"]
    estado.substituir("mental", _nova_ocorrencia(original))
    antes = estado.retrato_dominio("mental")
    retorno = callback({"intent":intent,"params":params,"id_solicitacao":"legado-capturado"},
        texto, True, origem="executor", status=status)
    assert not consumos, "primeira RED: caller legado não pode alcançar consumers do turno novo"
    depois = estado.retrato_dominio("mental")
    tardios = depois.pop("resultados_execucao_tardios", [])
    assert retorno is False and depois == antes and len(tardios) == 1
    assert tardios[0]["turno_id"] == str(original["turno_atual"]["id"])


@pytest.mark.parametrize("resultado", [True, False, "erro"])
def test_resumo_no_loop_real_reconcilia_callback_tardio_sem_contaminar_turno_atual(resultado):
    import asyncio
    async def cenario():
        estado, publicador, _, consumos, original = _montar("resume esta página")
        iniciou, liberar, terminou = asyncio.Event(), asyncio.Event(), asyncio.Event()
        async def resumir():
            iniciou.set()
            await liberar.wait()
            if resultado == "erro": raise RuntimeError("leitura falhou")
            return resultado
        registrar = publicador.registrar_resultado_execucao
        def observar(*args, **kwargs):
            try: return registrar(*args, **kwargs)
            finally: terminou.set()
        publicador.registrar_resultado_execucao = observar
        composicao, comandos, _ = _montar_entrada_vinculada(estado, publicador,
            loop_getter=asyncio.get_running_loop,
            servicos={"resumir_pagina_ou_video":resumir})
        assert comandos._processar_resumo_pagina("resume esta página", comandos.namespace_getter()) is True
        await asyncio.wait_for(iniciou.wait(), 2)
        estado.substituir("mental", _nova_ocorrencia(original))
        antes = estado.retrato_dominio("mental")
        liberar.set()
        await asyncio.wait_for(terminou.wait(), 2)
        assert not consumos, "resumo admitido no loop antigo não chega ao contexto novo"
        depois = estado.retrato_dominio("mental")
        tardios = depois.pop("resultados_execucao_tardios", [])
        assert depois == antes and len(tardios) == 1
        assert tardios[0]["resultado"]["status"] == ("resumo_concluido" if resultado is True else "falha_execucao")
        assert tardios[0]["turno_id"] == str(original["turno_atual"]["id"])
    asyncio.run(cenario())


@pytest.mark.parametrize("porta", ["comandos", "chat"])
def test_entrada_recria_vinculo_por_invocacao_e_nao_congela_turno_do_startup(porta):
    estado, publicador, _, consumos, original = _montar("abre a Calculadora")
    composicao, comandos, chat = _montar_entrada_vinculada(estado, publicador)
    assert "_vincular_registro_resultado_execucao" in composicao.servicos_interacao_registrados
    runtime = comandos if porta == "comandos" else chat
    primeiro = runtime.namespace_getter()["_registrar_resultado_execucao"]
    novo = _nova_ocorrencia(original)
    estado.substituir("mental", novo)
    segundo = runtime.namespace_getter()["_registrar_resultado_execucao"]
    assert segundo is not primeiro and segundo.__wrapped__ == publicador.registrar_resultado_execucao
    assert segundo({"intent":"APP_OPEN", "id_solicitacao":"atual"}, "abre a Calculadora", True,
        status="app_iniciado_focado") is not False
    assert consumos == ["base", "limpar", "suspender"]
    assert estado.mental["plano_turno_atual"]["comandos"][0]["id_solicitacao"] == "atual"
    assert not estado.mental.get("resultados_execucao_tardios")


def _montar_resposta_curta(estado, publicador, executar, aprender):
    from mente_laylay.personalidade.composicao_resposta_conversacional import ComposicaoRespostaConversacionalRuntime
    from scripts.tests.test_composicao_resposta_conversacional import _servicos_completos
    servicos = {**_servicos_completos(),
        "executar_intencao":executar,
        "_registrar_resultado_execucao":publicador.registrar_resultado_execucao,
        "_vincular_registro_resultado_execucao":publicador.vincular_registro_resultado_execucao,
        "_registrar_autoaprimoramento":aprender}
    composicao = ComposicaoRespostaConversacionalRuntime(estado_runtime_getter=lambda: estado,
        fallback_fala="", log=lambda *_a: None)
    return composicao, composicao.conectar(servicos=servicos)


@pytest.mark.parametrize("texto,intent,params,status", DOMINIOS)
@pytest.mark.parametrize("troca", ["controle", "mesma_frase", "outra_frase"])
@pytest.mark.parametrize("executou", [True, False])
def test_helper_curto_preserva_origem_do_receipt_e_nao_aprende_resultado_estrangeiro(
    texto, intent, params, status, troca, executou,
):
    estado, publicador, _, consumos, original = _montar(texto)
    efeitos, aprendizado, antes = [], [], []
    def executar(resultado, texto_recebido):
        efeitos.append((deepcopy(resultado), texto_recebido))
        if troca != "controle":
            estado.substituir("mental", _nova_ocorrencia(original) if troca == "mesma_frase" else _frame("como você está?"))
        antes.append(estado.retrato_dominio("mental"))
        return executou
    _, runtime = _montar_resposta_curta(estado, publicador, executar,
        lambda *_a, **_k: aprendizado.append(True))
    retorno = runtime.executar_intencao_curta({"intent":intent,"params":params,
        "id_solicitacao":"helper-curto", "status":status if executou else "falha_execucao",
        "confirmado":executou}, texto, origem="sonda_curta")
    assert len(efeitos) == 1 and retorno is executou, "bool legado não cancela efeito nem pede repetição"
    mental = estado.retrato_dominio("mental")
    if troca == "controle":
        assert consumos == ["base", "limpar", "suspender"]
        assert aprendizado == ([True] if executou else [])
        assert mental["plano_turno_atual"]["comandos"][0]["id_solicitacao"] == "helper-curto"
    else:
        assert not consumos, "primeira RED: namespace interno não pode perder a origem pré-executor"
        tardios = mental.pop("resultados_execucao_tardios", [])
        assert mental == antes[0] and len(tardios) == 1
        assert tardios[0]["turno_id"] == str(original["turno_atual"]["id"])
        assert not aprendizado, "receipt rejeitado não pode alimentar aprendizado como turno atual"


def test_helper_curto_recebe_factory_fresca_sem_capturar_turno_do_startup():
    estado, publicador, _, consumos, original = _montar("abre a Calculadora")
    efeitos, aprendizado = [], []
    composicao, runtime = _montar_resposta_curta(estado, publicador,
        lambda *_a: efeitos.append(True) or True, lambda *_a, **_k: aprendizado.append(True))
    callback_antigo = runtime._ns()["_registrar_resultado_execucao"]
    estado.substituir("mental", _nova_ocorrencia(original))
    callback_atual = runtime._ns()["_registrar_resultado_execucao"]
    assert callback_atual is not callback_antigo
    assert callback_atual.__wrapped__ == publicador.registrar_resultado_execucao
    assert "_vincular_registro_resultado_execucao" in composicao.servicos_registrados
    assert runtime.executar_intencao_curta({"intent":"APP_OPEN", "id_solicitacao":"invocacao-atual"},
        "abre a Calculadora", origem="teste") is True
    assert len(efeitos) == 1 and aprendizado == [True] and len(consumos) == 3
    assert not estado.mental.get("resultados_execucao_tardios")


def test_helper_curto_respeita_recusa_explicita_tambem_em_porta_sem_factory():
    estado, publicador, _, _, _ = _montar("abre a Calculadora")
    efeitos, aprendizado, publicacoes = [], [], []
    composicao, runtime = _montar_resposta_curta(estado, publicador,
        lambda *_a: efeitos.append(True) or True, lambda *_a, **_k: aprendizado.append(True))
    composicao._servicos.pop("_vincular_registro_resultado_execucao")
    def recusar(*_a, **_k):
        publicacoes.append(True)
        return False
    composicao._servicos["_registrar_resultado_execucao"] = recusar
    assert runtime._ns()["_registrar_resultado_execucao"] is recusar
    assert runtime.executar_intencao_curta({"intent":"APP_OPEN"}, "abre a Calculadora", origem="teste") is True
    assert efeitos == [True] and publicacoes == [True] and not aprendizado


@pytest.mark.parametrize("texto,intent,params,status", DOMINIOS)
@pytest.mark.parametrize("troca", ["controle", "mesma_frase", "outra_frase"])
def test_fallback_marcado_nao_republica_receipt_mas_informa_ocorrencia_superada(texto, intent, params, status, troca):
    estado, publicador, contexto, consumos, original = _montar(texto)
    ctx = contexto.montar()
    pedido = {"intent":intent,"params":params,"id_solicitacao":"detalhado"}
    adapter = AdaptadorResultadoOperacional(pedido, params, texto, "pc_a", ctx)
    adapter.marcar_resultado(status, True, confirmado=True, evidencia_confirmacao="fixture detalhada")
    assert adapter._receipt_publicado is not None
    assert pedido[CHAVE_RESULTADO_OPERACIONAL_PUBLICADO] == "detalhado"
    historico_original = estado.retrato_dominio("mental")
    if troca != "controle":
        estado.substituir("mental", _nova_ocorrencia(original) if troca == "mesma_frase" else _frame("como você está?"))
    antes = estado.retrato_dominio("mental")
    consumidores_antes = list(consumos)
    retorno = ctx["_registrar_resultado_execucao"](pedido, texto, True, origem="fallback")
    assert retorno is (None if troca == "controle" else False), "duplicata superada não equivale a ausência de recusa"
    assert consumos == consumidores_antes and estado.retrato_dominio("mental") == antes
    assert historico_original["plano_turno_atual"]["comandos"][0]["status"] == status
    assert adapter._receipt_publicado.evidencia_confirmacao == "fixture detalhada"


@pytest.mark.parametrize("texto,intent,params,status", DOMINIOS)
@pytest.mark.parametrize("troca", ["controle", "mesma_frase", "outra_frase"])
def test_helper_curto_nao_aprende_fallback_superado_de_receipt_moderno(texto, intent, params, status, troca):
    estado, publicador, contexto, consumos, original = _montar(texto)
    efeitos, aprendizado, recibos, antes = [], [], [], []
    def executar(pedido, texto_recebido):
        efeitos.append(True)
        adapter = AdaptadorResultadoOperacional(pedido, params, texto_recebido, "pc_a", contexto.montar())
        adapter.marcar_resultado(status, True, confirmado=True)
        recibos.append(adapter._receipt_publicado)
        if troca != "controle":
            estado.substituir("mental", _nova_ocorrencia(original) if troca == "mesma_frase" else _frame("como você está?"))
        antes.append(estado.retrato_dominio("mental"))
        return True
    _, runtime = _montar_resposta_curta(estado, publicador, executar,
        lambda *_a, **_k: aprendizado.append(True))
    assert runtime.executar_intencao_curta({"intent":intent,"params":params,"id_solicitacao":"moderno-helper"},
        texto, origem="teste_moderno") is True
    assert len(efeitos) == 1 and len(consumos) == 3 and recibos[0] is not None
    assert estado.retrato_dominio("mental") == antes[0], "fallback não é nova publicação de efeito"
    assert aprendizado == ([True] if troca == "controle" else []), "deduplicação de receipt estrangeiro não alimenta aprendizado atual"


def test_fallback_marcado_recusa_origem_ausente_sem_reconstruir_receipt():
    estado, _, contexto, consumos, _ = _montar("abre a Calculadora")
    ctx = contexto.montar()
    pedido = {"intent":"APP_OPEN", "params":{"nome_app":"Calculadora"}}
    adapter = AdaptadorResultadoOperacional(pedido, pedido["params"], "abre a Calculadora", "pc_a", ctx)
    adapter.marcar_resultado("app_iniciado_focado", True, confirmado=True)
    assert adapter._receipt_publicado is not None
    estado.substituir("mental", {})
    antes, consumidos = estado.retrato_dominio("mental"), list(consumos)
    assert ctx["_registrar_resultado_execucao"](pedido, "abre a Calculadora", True, origem="fallback") is False
    assert estado.retrato_dominio("mental") == antes and consumos == consumidos


@pytest.mark.parametrize("texto,intent,params,status", DOMINIOS)
def test_atualizacao_explicita_de_receipt_marcado_continua_usando_guardas_normais(texto, intent, params, status):
    estado, _, contexto, consumos, original = _montar(texto)
    ctx = contexto.montar()
    pedido = {"intent":intent, "params":params, "id_solicitacao":"atualizacao-explicita"}
    adapter = AdaptadorResultadoOperacional(pedido, params, texto, "pc_a", ctx)
    adapter.marcar_resultado(status, True, confirmado=True)
    assert adapter._receipt_publicado is not None
    consumidos = list(consumos)
    assert ctx["_registrar_resultado_execucao"](pedido, texto, True, origem="fallback", status=status) is not False
    assert len(consumos) == len(consumidos) * 2, "status explícito não é descarte genérico de duplicata"
    estado.substituir("mental", _nova_ocorrencia(original))
    antes, consumidos = estado.retrato_dominio("mental"), list(consumos)
    assert ctx["_registrar_resultado_execucao"](pedido, texto, True, origem="fallback", status=status) is False
    depois = estado.retrato_dominio("mental")
    tardios = depois.pop("resultados_execucao_tardios", [])
    assert depois == antes and consumos == consumidos
    assert len(tardios) == 1 and tardios[0]["resultado"]["status"] == status


@pytest.mark.parametrize("fronteira", ["antes_corrotina", "captura", "modelo", "entre_fala_contexto"])
@pytest.mark.parametrize("resposta", ["normal", "sentinela", "erro"])
def test_publicacao_do_resumo_preserva_ocorrencia_desde_a_invocacao(fronteira, resposta):
    import asyncio
    from mente_laylay.cognicao.resumo_conteudo import ResumoConteudoRuntime
    estado, publicador, _, _, original = _montar("resume esta página")
    falas, contextos = [], []
    novo = _nova_ocorrencia(original)
    def trocar(): estado.substituir("mental", novo)
    async def captura():
        if fronteira == "captura": trocar()
        return {"success":True,"data":{"url":"https://exemplo.test/texto", "title":"Manutenção",
            "content":"A manutenção preventiva reduz falhas. Testes pequenos ajudam a validar mudanças."}}
    def modelo(*_a, **_k):
        if fronteira == "modelo": trocar()
        if resposta == "erro": raise RuntimeError("modelo indisponível")
        return "__LLM_TIMEOUT__" if resposta == "sentinela" else "A manutenção preventiva reduz falhas. Testes pequenos validam mudanças."
    def falar(*args, **kwargs):
        falas.append(args)
        if fronteira == "entre_fala_contexto": trocar()
        return True
    ns = {"websocket_disponivel":lambda:True,"solicitar_conteudo":captura,"falar":falar,
        "enviar_mensagem":modelo,"limpar_resposta":str,"remover_prefixo_exec":str,
        "transcript_api":object(),"registrar_contexto_resumo":lambda registro: contextos.append(registro)}
    factory = getattr(publicador, "vincular_publicacao_conteudo", None)
    if callable(factory): ns["vincular_publicacao_conteudo"] = factory
    runtime = ResumoConteudoRuntime(namespace_getter=lambda:ns, log=lambda *_a:None)
    tarefa = runtime.resumir()
    if fronteira == "antes_corrotina": trocar()
    resultado = asyncio.run(tarefa)
    assert len(falas) == (1 if fronteira == "entre_fala_contexto" else 0), "primeira RED: conteúdo tardio não alcança porta de fala"
    assert not contextos, "publicação contextual antiga não chega ao novo turno"
    assert resultado is False, "resumo retido não é entrega concluída"


def test_publicacao_do_resumo_atual_mantem_modelo_cache_fala_e_contexto():
    import asyncio
    from mente_laylay.cognicao.resumo_conteudo import ResumoConteudoRuntime
    estado, publicador, _, _, _ = _montar("resume esta página")
    falas, contextos, modelos = [], [], []
    ns = {"websocket_disponivel":lambda:True,
        "solicitar_conteudo":lambda: asyncio.sleep(0,result={"success":True,"data":{
            "url":"https://exemplo.test/texto", "title":"Manutenção", "content":"A manutenção preventiva reduz falhas. Testes pequenos validam mudanças."}}),
        "falar":lambda *_a,**_k:falas.append(True),"limpar_resposta":str,"remover_prefixo_exec":str,
        "transcript_api":object(),"registrar_contexto_resumo":lambda registro:contextos.append(registro),
        "enviar_mensagem":lambda *_a,**_k: modelos.append(True) or "A manutenção preventiva reduz falhas. Testes pequenos validam mudanças."}
    factory = getattr(publicador, "vincular_publicacao_conteudo", None)
    if callable(factory): ns["vincular_publicacao_conteudo"] = factory
    runtime = ResumoConteudoRuntime(namespace_getter=lambda:ns, log=lambda *_a:None)
    assert asyncio.run(runtime.resumir()) is True
    assert asyncio.run(runtime.resumir()) is True
    assert len(modelos) == 1 and len(falas) == len(contextos) == 2
    assert contextos[-1]["status"] == "concluido_cache"


def test_vinculo_de_publicacao_e_reutilizavel_e_recusa_impede_portas_dependentes():
    _, publicador, _, _, _ = _montar("abre a Calculadora")
    efeitos = []
    contexto = publicador.vincular_publicacao_conteudo({
        "entregar_resultado":lambda: efeitos.append("entrega") or False,
        "registrar_memoria":lambda: efeitos.append("memoria")},
        portas=("entregar_resultado", "registrar_memoria"))
    assert contexto["publicacao_vigente"]() is True
    assert contexto["entregar_resultado"]() is False
    assert contexto["registrar_memoria"]() is False
    assert contexto["publicacao_vigente"]() is False and efeitos == ["entrega"]


def test_recusa_da_fala_do_resumo_nao_publica_contexto_nem_sucesso():
    import asyncio
    from mente_laylay.cognicao.resumo_conteudo import ResumoConteudoRuntime
    _, publicador, _, _, _ = _montar("resume esta página")
    contextos, falas = [], []
    runtime = ResumoConteudoRuntime(namespace_getter=lambda:{
        "websocket_disponivel":lambda:True,
        "solicitar_conteudo":lambda:asyncio.sleep(0,result={"success":True,"data":{
            "url":"https://exemplo.test", "title":"Manutenção", "content":"A manutenção preventiva reduz falhas. Testes pequenos validam mudanças."}}),
        "falar":lambda *_a:falas.append(True) or False,
        "registrar_contexto_resumo":lambda registro:contextos.append(registro),
        "enviar_mensagem":lambda *_a,**_k:"A manutenção preventiva reduz falhas.",
        "limpar_resposta":str,"remover_prefixo_exec":str,"transcript_api":object(),
        "vincular_publicacao_conteudo":publicador.vincular_publicacao_conteudo}, log=lambda *_a:None)
    assert asyncio.run(runtime.resumir()) is False
    assert falas == [True] and not contextos


def _montar_contexto_conteudo():
    from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
    estado, publicador, _, _, original = _montar("resume esta página")
    ns = publicador._ns()
    base = EstadoContextoRuntime(namespace_getter=lambda: ns, estado_runtime_getter=lambda: estado)
    observacoes = []
    ns.update(_normalizar_texto_com_apelidos=str.casefold,
        _eh_alvo_site_web=lambda *_a: False,
        _atualizar_foco_vivo=base.atualizar_foco_vivo,
        _conversa_estado_get=lambda chave, padrao=None: estado.obter("conversacional", chave, padrao),
        _registrar_mente_curta_base=base.registrar_mente_curta,
        _registrar_mente_curta=publicador.registrar_mente_curta,
        salvar_memoria=lambda: observacoes.append("persistencia"))
    # Serviço nativo de derivação, quando disponível; não simula o owner.
    derivar = getattr(base, "derivar_mente_curta", None)
    if callable(derivar): ns["_derivar_mente_curta"] = derivar
    return estado, publicador, ns, observacoes, original


@pytest.mark.parametrize("fronteira", ["normalizador", "foco"])
@pytest.mark.parametrize("troca", ["mesma_frase", "outra_frase", "sem_turno"])
def test_contexto_conteudo_nao_restaura_turno_durante_derivacao_nativa(fronteira, troca):
    estado, publicador, ns, observacoes, original = _montar_contexto_conteudo()
    novos = []
    chave = "_normalizar_texto_com_apelidos" if fronteira == "normalizador" else "_atualizar_foco_vivo"
    callback = ns[chave]
    def intercalar(*args, **kwargs):
        if not novos:
            mental = (_nova_ocorrencia(original) if troca == "mesma_frase"
                else _frame("abre o Bloco de Notas") if troca == "outra_frase" else {})
            estado.substituir("mental", mental)
            estado.atualizar_campos("memoria_conversa", messages=[{"role":"user", "content":"pedido atual"}])
            estado.atualizar_campos("conversacional", ultimo_topico_conversa="assunto atual")
            novos.append(estado.snapshot())
        return callback(*args, **kwargs)
    ns[chave] = intercalar
    ctx = publicador.vincular_publicacao_conteudo({"registrar_contexto":publicador.registrar_contexto_resumo_pagina})
    resultado = ctx["registrar_contexto"]({"referente":"Manutenção", "resumo":"Testes pequenos validam mudanças."})
    assert novos, "RED precisa alcançar a derivação contextual nativa"
    assert estado.snapshot() == novos[-1], "primeira fronteira: commit antigo não substitui nenhum domínio atual"
    assert observacoes == [], "recusa contextual não persiste nem anuncia aprendizado"
    assert resultado is False


def test_contexto_conteudo_nao_expoe_publicacao_parcial_durante_derivacao():
    estado, publicador, ns, observacoes, _ = _montar_contexto_conteudo()
    antes, leituras = estado.snapshot(), []
    normalizar = ns["_normalizar_texto_com_apelidos"]
    def ler(texto):
        leituras.append(estado.snapshot())
        return normalizar(texto)
    ns["_normalizar_texto_com_apelidos"] = ler
    publicador.registrar_contexto_resumo_pagina({"referente":"Manutenção", "resumo":"Testes pequenos validam mudanças."})
    assert leituras and all(leitura == antes for leitura in leituras), "derivação não publica último resumo antes de resposta/mensagens/tópico"
    depois = estado.snapshot()
    assert depois["mental"]["ultima_resposta"] == "Testes pequenos validam mudanças."
    assert depois["memoria_conversa"]["messages"][-1]["content"] == "Testes pequenos validam mudanças."
    assert depois["conversacional"]["ultimo_topico_conversa"] == "Manutenção"
    assert observacoes == ["persistencia"]


@pytest.mark.parametrize("dominio", ["mental", "memoria_conversa", "conversacional"])
def test_contexto_conteudo_rederiva_conflito_vigente_sem_perder_writer(dominio):
    estado, publicador, ns, observacoes, original = _montar_contexto_conteudo()
    normalizar, conflitos = ns["_normalizar_texto_com_apelidos"], []
    def intercalar(texto):
        if not conflitos:
            estado.atualizar_campos(dominio, writer_independente={"valor":42})
            if dominio == "memoria_conversa":
                estado.atualizar_campos(dominio, messages=[{"role":"system", "content":"mensagem concorrente"}])
            conflitos.append(True)
        return normalizar(texto)
    ns["_normalizar_texto_com_apelidos"] = intercalar
    assert publicador.registrar_contexto_resumo_pagina({"referente":"Manutenção", "resumo":"Resumo vigente."}) is True
    depois = estado.snapshot()
    assert depois[dominio]["writer_independente"] == {"valor":42}
    assert depois["mental"]["turno_atual"] == original["turno_atual"]
    assert depois["mental"]["ultima_resposta"] == "Resumo vigente."
    if dominio == "memoria_conversa":
        assert depois[dominio]["messages"][0]["content"] == "mensagem concorrente"
    assert observacoes == ["persistencia"], "retry não duplica consumers nem histórico"
    assert len(depois["memoria_conversa"]["messages"]) == (3 if dominio == "memoria_conversa" else 2)


def test_contexto_conteudo_contencao_continua_recusa_sem_publicacao_parcial():
    estado, publicador, ns, observacoes, _ = _montar_contexto_conteudo()
    normalizar, conflitos = ns["_normalizar_texto_com_apelidos"], []
    def intercalar(texto):
        conflitos.append(True)
        estado.atualizar_campos("mental", writer_independente=len(conflitos))
        return normalizar(texto)
    ns["_normalizar_texto_com_apelidos"] = intercalar
    assert publicador.registrar_contexto_resumo_pagina({"referente":"Manutenção", "resumo":"Resumo vigente."}) is False
    assert 1 <= len(conflitos) <= 30, "tentativas limitadas não travam a conversa"
    depois = estado.snapshot()
    assert not depois["mental"].get("ultimo_resumo_pagina")
    assert not depois["mental"].get("ultima_resposta")
    assert not depois["memoria_conversa"].get("messages")
    assert not depois["conversacional"].get("ultimo_topico_conversa")
    assert observacoes == []


def test_contexto_conteudo_vinculado_conserva_origem_antes_da_entrada_da_porta():
    estado, publicador, _, observacoes, original = _montar_contexto_conteudo()
    novos = []
    def porta(registro, *, _ocorrencia):
        estado.substituir("mental", _nova_ocorrencia(original))
        novos.append(estado.snapshot())
        return publicador.registrar_contexto_resumo_pagina(registro, _ocorrencia=_ocorrencia)
    contexto = publicador.vincular_publicacao_conteudo({"conteudo":porta},
        portas=("conteudo",), portas_com_ocorrencia=("conteudo",))
    assert contexto["conteudo"]({"referente":"Manutenção", "resumo":"Resumo antigo."},
        _ocorrencia=ContratoOcorrenciaTurno("injetada", "frase forjada")) is False
    assert estado.snapshot() == novos[-1] and observacoes == []


def test_contexto_conteudo_derivacao_e_observadores_fora_do_lock():
    from threading import Thread
    from types import SimpleNamespace
    estado, publicador, ns, observacoes, _ = _montar_contexto_conteudo()
    callbacks = []
    normalizar = ns["_normalizar_texto_com_apelidos"]
    def verificar_lock(nome):
        leituras = []
        leitor = Thread(target=lambda: leituras.append(estado.snapshot()), daemon=True)
        leitor.start()
        leitor.join(timeout=2)
        assert not leitor.is_alive(), f"{nome} não pode prender leitor por callback externo sob lock"
        callbacks.append((nome, leituras[0]))
    def normalizador(texto):
        verificar_lock("derivacao")
        return normalizar(texto)
    ns["_normalizar_texto_com_apelidos"] = normalizador
    ns["_motor_aprendizado_runtime"] = SimpleNamespace(observar_interacao=lambda *_a, **_k: verificar_lock("aprendizado"))
    ns["_rede_associativa_runtime"] = SimpleNamespace(observar_interacao=lambda **_k: verificar_lock("rede"))
    assert publicador.registrar_contexto_resumo_pagina({"referente":"Manutenção", "resumo":"Resumo vigente."}) is True
    for nome, snapshot in callbacks:
        if nome in {"aprendizado", "rede"}:
            assert snapshot["mental"]["ultimo_resumo_pagina"]["resumo"] == "Resumo vigente."
            assert snapshot["memoria_conversa"]["messages"][-1]["content"] == "Resumo vigente."
            assert snapshot["conversacional"]["ultimo_topico_conversa"] == "Manutenção"
    assert [nome for nome, _ in callbacks].count("aprendizado") == 1
    assert [nome for nome, _ in callbacks].count("rede") == 1
    assert observacoes == ["persistencia"]


def test_contexto_conteudo_sem_derivador_canonico_nao_improvisa_estado():
    estado, publicador, ns, observacoes, _ = _montar_contexto_conteudo()
    ns.pop("_derivar_mente_curta")
    antes = estado.snapshot()
    assert publicador.registrar_contexto_resumo_pagina({"referente":"Manutenção", "resumo":"Resumo vigente."}) is False
    assert estado.snapshot() == antes and observacoes == []


def test_contexto_conteudo_sem_texto_nao_inventa_mensagens_ou_aprendizado():
    estado, publicador, _, observacoes, _ = _montar_contexto_conteudo()
    assert publicador.registrar_contexto_resumo_pagina({"referente":"Manutenção", "status":"sem_conteudo"}) is True
    depois = estado.snapshot()
    assert depois["mental"]["ultimo_resumo_pagina"]["status"] == "sem_conteudo"
    assert not depois["memoria_conversa"].get("messages") and not depois["conversacional"].get("ultimo_topico_conversa")
    assert observacoes == ["persistencia"]


@pytest.mark.parametrize("intent,alvo,habilidade", [("APP_OPEN","Chrome","aplicativos"),
    ("IOT_CONTROL","lâmpada","iot"), ("CREATE_FILE","teste.txt","arquivo")])
def test_derivacao_canonica_e_reutilizavel_sem_escrever_ou_observar(intent, alvo, habilidade):
    estado, _, ns, observacoes, _ = _montar_contexto_conteudo()
    antes = estado.snapshot()
    mental = deepcopy(antes["mental"])
    candidato = ns["_derivar_mente_curta"](mental, antes["conversacional"],
        texto_usuario="pedido para diagnóstico", resposta_ia="Resultado contextual.",
        intencao=intent, alvo=alvo, habilidade=habilidade)
    assert candidato["ultima_intencao"] == intent and candidato["ultimo_alvo"] == alvo
    assert candidato["ultima_resposta"] == "Resultado contextual."
    assert mental == antes["mental"] and estado.snapshot() == antes and observacoes == []


@pytest.mark.parametrize("porta", ["base", "adaptador"])
def test_registro_legado_usa_retrato_sem_copiar_lock_das_colecoes_vivas(porta):
    estado, publicador, ns, observacoes, _ = _montar_contexto_conteudo()
    estado.atualizar_campos("mental", dados_aninhados={"lista":[{"valor":42}]})
    callback = ns["_registrar_mente_curta_base"] if porta == "base" else publicador.registrar_mente_curta
    callback("pedido de diagnóstico", "Resposta vigente.", "APP_OPEN", "Chrome", "janela", "aplicativos")
    depois = estado.retrato_dominio("mental")
    assert depois["ultima_resposta"] == "Resposta vigente."
    assert depois["dados_aninhados"] == {"lista":[{"valor":42}]}
    assert observacoes == []
