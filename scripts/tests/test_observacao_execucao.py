"""Receipts aceitos desta invocação, não bool, cache ou última ação."""
from dataclasses import FrozenInstanceError
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
from dataclasses import replace

import pytest

from mente_laylay.autonomia import coordenador_intencao
from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.autonomia.dispatcher_comandos_json import executar_comandos_json
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


def criar_ciclo(monkeypatch, *, intent="APP_OPEN", aceito=True, confirmado=True,
                executou=True, retorno=True, publicar=True):
    publicacoes = []
    contexto = {"turno_atual": {"id": "turno-original"}}

    def registrar(receipt, *_args, **_kwargs):
        publicacoes.append(receipt)
        return aceito

    contexto["_registrar_resultado_execucao"] = registrar

    def executor(pedido, texto, ctx):
        if publicar:
            adapter = AdaptadorResultadoOperacional(pedido, pedido["params"], texto, "local", ctx)
            adapter.marcar_resultado("estado_observado", executou=executou,
                confirmado=confirmado, alvo_resolvido="alvo-do-executor")
        return retorno

    monkeypatch.setattr(coordenador_intencao, "executar_intencao", executor)
    ciclo = coordenador_intencao.CicloComandosRuntime(namespace_getter=lambda: {},
        contexto_intencao_runtime=SimpleNamespace(montar=lambda: contexto))
    params = {"APP_OPEN": {"nome_app": "Calculadora"},
              "VOLUME": {"acao": "set", "nivel_volume": 40},
              "IOT_CONTROL": {"acao": "ligar", "alvo": "lampada_quarto"}}[intent]
    pedido = {"intent": intent, "params": params,
              "id_solicitacao": "solicitacao-original"}
    return ciclo, pedido, contexto, publicacoes


def despachar(ciclo, pedido):
    ctx = {"executar_intencao": ciclo.executar_intencao}
    observar = getattr(ciclo, "executar_intencao_observando", None)
    if callable(observar):
        ctx["executar_intencao_observando"] = observar
    return executar_comandos_json(ctx, "pedido explícito", [pedido], "", "comando", False, False, False)


@pytest.mark.parametrize("intent", ["APP_OPEN", "VOLUME", "IOT_CONTROL"])
def test_publicacao_aceita_chega_ao_dispatcher_vinculada_a_invocacao(monkeypatch, intent):
    ciclo, pedido, _, publicados = criar_ciclo(monkeypatch, intent=intent)
    resultado = despachar(ciclo, pedido)
    assert len(publicados) == 1, "alcançar a publicação antes de testar transporte"
    observacoes = resultado.get("execucoes_observadas", ())
    assert len(observacoes) == 1, "receipt aceito se perdeu no retorno bool do executor"
    observacao = observacoes[0]
    assert observacao.turno_id == "turno-original"
    assert observacao.pedido.como_dict()["id_solicitacao"] == pedido["id_solicitacao"]
    assert len(observacao.publicacoes) == 1
    assert observacao.publicacoes[0].como_dict() == publicados[0].como_dict()
    assert observacao.autoriza_execucao is False
    assert observacao.retorno_legado is True
    assert len(observacao.instantes_publicacao) == 1 and observacao.publicacao_recente()


@pytest.mark.parametrize("aceito,publicar", [(False, True), (True, False)])
def test_retorno_true_sem_publicacao_aceita_nao_produz_receipt(monkeypatch, aceito, publicar):
    ciclo, pedido, _, _ = criar_ciclo(monkeypatch, aceito=aceito, publicar=publicar)
    resultado = despachar(ciclo, pedido)
    observacoes = resultado.get("execucoes_observadas", ())
    assert len(observacoes) == 1, "observação de invocação deve distinguir ausência de receipt"
    assert observacoes[0].publicacoes == ()
    assert observacoes[0].retorno_legado is True
    assert observacoes[0].instantes_publicacao == ()


@pytest.mark.parametrize("idade,recente", [(0, True), (299, True), (300, True), (301, False), (-1, False)])
def test_idade_da_publicacao_original_manda_no_ttl(monkeypatch, idade, recente):
    ciclo, pedido, _, _ = criar_ciclo(monkeypatch)
    obs = ciclo.executar_intencao_observando(pedido, "pedido")
    instante = obs.instantes_publicacao[-1]
    assert obs.publicacao_recente(agora=instante + idade) is recente
    assert not replace(obs, instantes_publicacao=()).publicacao_recente(agora=instante)


@pytest.mark.parametrize("tempo", [float("nan"), float("inf"), -1.0, True])
def test_instantes_malformados_nao_criam_recencia(monkeypatch, tempo):
    ciclo, pedido, _, _ = criar_ciclo(monkeypatch)
    obs = ciclo.executar_intencao_observando(pedido, "pedido")
    with pytest.raises(ValueError):
        replace(obs, instantes_publicacao=(tempo,))


def test_republicacao_preserva_instante_distinto_por_receipt(monkeypatch):
    ciclo, pedido, _, _ = criar_ciclo(monkeypatch)
    def executor(_pedido, _texto, ctx):
        for confirmado in (True, None):
            ctx["_registrar_resultado_execucao"](ResultadoAcao(intent="APP_OPEN", origem="executor",
                id_solicitacao=pedido["id_solicitacao"], confirmado=confirmado, executou=True))
        return True
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", executor)
    obs = ciclo.executar_intencao_observando(pedido, "pedido")
    assert len(obs.instantes_publicacao) == len(obs.publicacoes) == 2
    assert obs.instantes_publicacao[0] <= obs.instantes_publicacao[1]
    assert obs.publicacoes[-1].como_dict()["confirmado"] is None


@pytest.mark.parametrize("confirmado,executou,retorno", [
    (False, False, False), (None, True, True), (True, False, False), (True, True, False),
])
def test_transporte_preserva_falha_incerteza_idempotencia_e_bool_distintos(
    monkeypatch, confirmado, executou, retorno,
):
    ciclo, pedido, _, publicados = criar_ciclo(monkeypatch, confirmado=confirmado,
        executou=executou, retorno=retorno)
    observado = ciclo.executar_intencao_observando(pedido, "pedido")
    assert len(publicados) == len(observado.publicacoes) == 1
    receipt = observado.publicacoes[0].como_dict()
    assert receipt["confirmado"] is confirmado and receipt["executou"] is executou
    assert observado.retorno_legado is retorno


@pytest.mark.parametrize("alteracao", [
    {"id_solicitacao": "outra-solicitacao"}, {"intent": "IOT_CONTROL"},
    {"origem": "modelo"}, {"id_solicitacao": ""},
])
def test_publicacao_alheia_nao_integra_observacao_da_invocacao(monkeypatch, alteracao):
    ciclo, pedido, _, publicados = criar_ciclo(monkeypatch)

    def executor(_pedido, _texto, ctx):
        dados = dict(intent="APP_OPEN", id_solicitacao="solicitacao-original", origem="executor",
                     executou=True, confirmado=True, alvo="Calculadora")
        dados.update(alteracao)
        ctx["_registrar_resultado_execucao"](ResultadoAcao(**dados))
        return True

    monkeypatch.setattr(coordenador_intencao, "executar_intencao", executor)
    observado = ciclo.executar_intencao_observando(pedido, "pedido")
    assert len(publicados) == 1
    assert observado.publicacoes == ()


def test_dict_falso_marcador_e_ultima_acao_nao_sao_publicacao_tipificada(monkeypatch):
    ciclo, pedido, contexto, _ = criar_ciclo(monkeypatch)
    falso = dict(intent="APP_OPEN", id_solicitacao=pedido["id_solicitacao"], origem="executor",
                 confirmado=True, executou=True)
    contexto["ultima_acao_contrato"] = falso
    pedido["_laylay_resultado_operacional_publicado"] = pedido["id_solicitacao"]
    monkeypatch.setattr(coordenador_intencao, "executar_intencao",
        lambda _p, _t, ctx: ctx["_registrar_resultado_execucao"](falso) or True)
    observado = ciclo.executar_intencao_observando(pedido, "pedido")
    assert observado.publicacoes == ()


def test_cache_restaura_tratamento_mas_nao_republica_receipt(monkeypatch):
    ciclo, pedido, _, publicados = criar_ciclo(monkeypatch)
    primeiro = ciclo.executar_intencao_observando(pedido, "pedido")
    segundo = ciclo.executar_intencao_observando(pedido, "pedido")
    assert len(publicados) == 1 and len(primeiro.publicacoes) == 1
    assert segundo.publicacoes == () and segundo.retorno_legado is True


def preparar_atos_cache(monkeypatch, **kwargs):
    from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
    from mente_laylay.cognicao.escopo_autorizacao import AutorizacaoAto
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    ciclo, pedido, contexto, publicados = criar_ciclo(monkeypatch, **kwargs)
    turno = classificar_modalidade_turno("abre o aplicativo Calculadora e abre o aplicativo Calculadora")
    turno["id"] = "turno-original"
    contexto["turno_atual"] = turno
    atos = tuple(AutorizacaoAto(turno["id"], i, s["texto"], SnapshotComandoIA(pedido))
                 for i, s in enumerate(turno["segmentos"]))
    assert len(atos) == 2
    return ciclo, pedido, contexto, publicados, atos


@pytest.mark.parametrize("confirmado,retorno", [(True, True), (False, False), (None, True)])
def test_mesmo_ato_com_novo_id_nao_repete_efeito_mas_ato_distinto_repete(monkeypatch, confirmado, retorno):
    ciclo, pedido, _, publicados, atos = preparar_atos_cache(monkeypatch, confirmado=confirmado, retorno=retorno)
    a, b = atos
    primeiro = ciclo.executar_ato_observando(dict(pedido), a.texto, a, vigente=lambda: True)
    retry = ciclo.executar_ato_observando({**pedido, "id_solicitacao": "retry"}, a.texto, a, vigente=lambda: True)
    novo = ciclo.executar_ato_observando({**pedido, "id_solicitacao": "ato-b"}, b.texto, b, vigente=lambda: True)
    assert len(publicados) == 2 and len(primeiro.publicacoes) == len(novo.publicacoes) == 1
    assert retry.publicacoes == retry.instantes_publicacao == ()
    assert retry.retorno_legado is retorno


@pytest.mark.parametrize("ordem", ["ato_antes", "legado_antes"])
def test_porta_sem_indice_nao_contorna_deduplicacao_do_ato(monkeypatch, ordem):
    ciclo, pedido, _, publicados, atos = preparar_atos_cache(monkeypatch)
    a = atos[0]
    escopado = lambda: ciclo.executar_ato_observando(dict(pedido), a.texto, a, vigente=lambda: True)
    legado = lambda: ciclo.executar_intencao_observando({**pedido, "id_solicitacao": "legado"}, "outra camada")
    primeiro, segundo = (escopado, legado) if ordem == "ato_antes" else (legado, escopado)
    assert len(primeiro().publicacoes) == 1
    assert segundo().publicacoes == () and len(publicados) == 1
    if ordem == "legado_antes":
        # Sem origem não inventar qual dos dois atos consumiu a publicação.
        assert ciclo.executar_ato_observando(dict(pedido), atos[1].texto, atos[1], vigente=lambda: True).publicacoes == ()
        assert len(publicados) == 1


@pytest.mark.parametrize("modo", ["dict", "turno", "indice", "texto", "alvo", "sem_porta", "revogado", "fase_encerrada"])
def test_indice_forjado_ou_admissao_invalida_nao_abre_cache_nem_executor(monkeypatch, modo):
    ciclo, pedido, contexto, publicados, atos = preparar_atos_cache(monkeypatch)
    a, texto, vigente = atos[0], atos[0].texto, lambda: True
    if modo == "dict": a = {"indice": 1, "turno_id": "turno-original"}
    elif modo == "turno": a = replace(a, turno_id="turno-alheio")
    elif modo == "indice": a = replace(a, indice=99)
    elif modo == "texto": texto = "apaga o arquivo"
    elif modo == "alvo": pedido = {**pedido, "params": {"nome_app": "Notepad"}}
    elif modo == "sem_porta": vigente = None
    elif modo == "revogado": contexto["turno_atual"]["segmentos"][0]["autoriza_execucao"] = False
    elif modo == "fase_encerrada": contexto["plano_turno_atual"] = {"id": "turno-original", "fase": "executado"}
    with pytest.raises(ValueError):
        ciclo.executar_ato_observando(dict(pedido), texto, a, vigente=vigente)
    assert not publicados and not ciclo._execucoes_turno


def test_vigencia_e_revalidada_apos_reserva_antes_do_efeito(monkeypatch):
    ciclo, pedido, _, publicados, atos = preparar_atos_cache(monkeypatch)
    verificacoes = []
    def revogar():
        verificacoes.append(True)
        return len(verificacoes) == 1
    with pytest.raises(ValueError, match="revogada antes do efeito"):
        ciclo.executar_ato_observando(dict(pedido), atos[0].texto, atos[0], vigente=revogar)
    assert len(verificacoes) == 2 and not publicados


def test_retry_concorrente_do_mesmo_ato_e_legado_esperam_um_unico_executor(monkeypatch):
    from threading import Event
    import time
    ciclo, pedido, _, publicados, atos = preparar_atos_cache(monkeypatch)
    entrou, liberar = Event(), Event()
    original = coordenador_intencao.executar_intencao
    def lento(*args):
        entrou.set()
        assert liberar.wait(timeout=5)
        return original(*args)
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", lento)
    a = atos[0]
    with ThreadPoolExecutor(max_workers=3) as pool:
        primeiro = pool.submit(ciclo.executar_ato_observando, dict(pedido), a.texto, a, vigente=lambda: True)
        assert entrou.wait(timeout=5)
        retry = pool.submit(ciclo.executar_ato_observando, {**pedido, "id_solicitacao": "retry"}, a.texto, a, vigente=lambda: True)
        legado = pool.submit(ciclo.executar_intencao_observando, {**pedido, "id_solicitacao": "legado"}, "fallback")
        limite = time.monotonic() + 3
        try:
            while ciclo.diagnostico_linguagem_natural()["execucao_turno"]["aguardadas"] < 2 and time.monotonic() < limite:
                time.sleep(.001)
            assert ciclo.diagnostico_linguagem_natural()["execucao_turno"]["aguardadas"] == 2
        finally:
            liberar.set()
        resultados = [f.result(timeout=5) for f in (primeiro, retry, legado)]
    assert len(publicados) == 1 and [len(o.publicacoes) for o in resultados] == [1, 0, 0]


def test_atos_distintos_concorrentes_nao_compartilham_cache_ou_receipts(monkeypatch):
    ciclo, pedido, _, publicados, atos = preparar_atos_cache(monkeypatch)
    barreira = Barrier(2)
    original = coordenador_intencao.executar_intencao
    def concorrente(*args):
        barreira.wait(timeout=5)
        return original(*args)
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", concorrente)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(ciclo.executar_ato_observando, {**pedido, "id_solicitacao": f"ato-{i}"},
            a.texto, a, vigente=lambda: True) for i, a in enumerate(atos)]
        resultados = [f.result(timeout=5) for f in futuros]
    assert len(publicados) == 2 and all(len(o.publicacoes) == 1 for o in resultados)
    assert len({o.publicacoes[0].como_dict()["id_solicitacao"] for o in resultados}) == 2


def test_turno_capturado_nao_e_reatribuido_quando_resultado_chega_tarde(monkeypatch):
    ciclo, pedido, contexto, _ = criar_ciclo(monkeypatch)
    executor = coordenador_intencao.executar_intencao

    def tardio(*args):
        contexto["turno_atual"] = {"id": "novo-turno"}
        return executor(*args)

    monkeypatch.setattr(coordenador_intencao, "executar_intencao", tardio)
    observado = ciclo.executar_intencao_observando(pedido, "pedido")
    assert len(observado.publicacoes) == 1 and observado.turno_id == "turno-original"
    assert observado.turno_id != contexto["turno_atual"]["id"]
    assert observado.autoriza_execucao is False


def test_snapshots_nao_compartilham_params_mutaveis_com_executor_ou_chamador(monkeypatch):
    ciclo, pedido, _, publicados = criar_ciclo(monkeypatch)
    pedido["params"]["opcoes"] = {"valores": [1, 2]}
    observado = ciclo.executar_intencao_observando(pedido, "pedido")
    pedido["params"]["opcoes"]["valores"].append(3)
    publicados[0].params["opcoes"]["valores"].append(4)
    observado.como_dict()["publicacoes"][0]["params"]["opcoes"]["valores"].append(5)
    assert observado.pedido.como_dict()["params"]["opcoes"]["valores"] == [1, 2]
    assert observado.publicacoes[0].como_dict()["params"]["opcoes"]["valores"] == [1, 2]
    with pytest.raises(FrozenInstanceError):
        observado.turno_id = "outro"


def test_resultado_sem_projecao_json_nao_muda_efeito_ou_bool(monkeypatch):
    ciclo, pedido, _, publicados = criar_ciclo(monkeypatch)
    def executor(_pedido, _texto, ctx):
        ctx["_registrar_resultado_execucao"](ResultadoAcao(intent="APP_OPEN",
            id_solicitacao=pedido["id_solicitacao"], origem="executor", params={"objeto": object()}))
        return True
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", executor)
    observado = ciclo.executar_intencao_observando(pedido, "pedido")
    assert len(publicados) == 1 and observado.retorno_legado is True
    assert observado.publicacoes == ()


def test_dispatcher_nao_aceita_dict_de_observacao_e_nao_repete_efeito(monkeypatch):
    ciclo, pedido, _, _ = criar_ciclo(monkeypatch)
    chamadas = []
    ctx = {"executar_intencao": lambda *_: pytest.fail("não repetir efeito"),
           "executar_intencao_observando": lambda *_: chamadas.append(True) or {"confirmado": True}}
    resultado = executar_comandos_json(ctx, "pedido", [pedido], "", "comando", False, False, False)
    assert chamadas == [True] and resultado["execucoes_observadas"] == ()
    assert "observação não pertence" in resultado["erros"][0]


def test_vigencia_fecha_antes_da_proxima_invocacao_mesmo_com_receipt_aceito(monkeypatch):
    ciclo, pedido, contexto, publicados = criar_ciclo(monkeypatch)
    executor = coordenador_intencao.executar_intencao
    def tardio(*args):
        contexto["turno_atual"] = {"id": "novo-turno"}
        return executor(*args)
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", tardio)
    outro = {"intent": "VOLUME", "params": {"nivel_volume": 40}}
    ctx = {"executar_intencao": ciclo.executar_intencao,
        "executar_intencao_observando": ciclo.executar_intencao_observando,
        "proposta_principal_vigente": lambda: contexto["turno_atual"]["id"] == "turno-original"}
    resultado = executar_comandos_json(ctx, "pedido", [pedido, outro], "", "comando", False, False, False)
    assert len(publicados) == len(resultado["execucoes_observadas"]) == 1
    assert "não está vigente" in resultado["erros"][0]


def test_publicacao_none_mantem_semantica_do_registrador_canonico(monkeypatch):
    ciclo, pedido, _, _ = criar_ciclo(monkeypatch, aceito=None)
    observado = ciclo.executar_intencao_observando(pedido, "pedido")
    assert len(observado.publicacoes) == 1


def test_invocacoes_concorrentes_nao_compartilham_coletor_de_receipts(monkeypatch):
    ciclo, pedido, _, publicados = criar_ciclo(monkeypatch)
    barreira = Barrier(2)
    def executor(atual, _texto, ctx):
        barreira.wait(timeout=5)
        ctx["_registrar_resultado_execucao"](ResultadoAcao(intent="APP_OPEN",
            id_solicitacao=atual["id_solicitacao"], origem="executor", alvo=atual["params"]["nome_app"]))
        return True
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", executor)
    outro = {"intent": "APP_OPEN", "params": {"nome_app": "Notepad"}, "id_solicitacao": "solicitacao-b"}
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(ciclo.executar_intencao_observando, pedido, "pedido-a")
        b = pool.submit(ciclo.executar_intencao_observando, outro, "pedido-b")
        observacoes = [a.result(timeout=5), b.result(timeout=5)]
    assert len(publicados) == 2
    for observado in observacoes:
        assert len(observado.publicacoes) == 1
        receipt = observado.publicacoes[0].como_dict()
        assert receipt["id_solicitacao"] == observado.pedido.como_dict()["id_solicitacao"]
        assert receipt["alvo"] == observado.pedido.como_dict()["params"]["nome_app"]


def test_observacao_alheia_tipificada_nao_passa_com_mesmo_id_e_params_divergentes(monkeypatch):
    from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
    from mente_laylay.memoria_mental.observacao_execucao import ExecucaoObservada
    ciclo, pedido, _, _ = criar_ciclo(monkeypatch)
    def forjar(atual, _texto):
        falso = {**atual, "params": {"nome_app": "outro-app"}}
        return ExecucaoObservada("turno-original", SnapshotComandoIA(falso), (), True)
    ctx = {"executar_intencao": ciclo.executar_intencao, "executar_intencao_observando": forjar}
    resultado = executar_comandos_json(ctx, "pedido", [pedido], "", "comando", False, False, False)
    assert not resultado["execucoes_observadas"]
    assert "observação não pertence" in resultado["erros"][0]


def test_composicao_instalada_transporta_publicacao_real_com_efeito_isolado():
    from scripts.analises.sonda_escopo_propostas_mistas import coletar
    relatorio = coletar()
    assert relatorio["fontes_estaveis"]
    casos = relatorio["observacoes_execucao_instaladas"]
    assert len(casos) == 4 and all(c["observador_instalado"] for c in casos)
    assert all(not c["falhas"] and not c["efeito_real_validado"] for c in casos)
    assert relatorio["runtime_main_validado"] is False
