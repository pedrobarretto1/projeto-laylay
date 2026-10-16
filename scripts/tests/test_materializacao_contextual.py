"""Materialização por publicação qualificada, sem admissão ou novo efeito."""
from copy import deepcopy
from dataclasses import replace
import time

import pytest

from mente_laylay.autonomia.orquestrador_deterministico import DeteccaoDeterministicaRuntime
from mente_laylay.autonomia.roteador_deterministico import extrair_intencao_abrir_app
from mente_laylay.autonomia.coordenador_intencao import resolver_referencias_da_intencao
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal, SnapshotComandoIA
from mente_laylay.cognicao.decisao_turno import criar_validador_comandos_turno_runtime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_resultado_execucao
from mente_laylay.memoria_mental.contexto_imediato import referencia_contextual_imediata
from mente_laylay.memoria_mental.observacao_execucao import ExecucaoObservada
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from scripts.tests.test_decisao_unica_turno import _contratos_reais_do_filtro


def preparar(texto="abre o aplicativo Calculadora e coloca ela à esquerda"):
    turno, plano, retrato = _contratos_reais_do_filtro(texto)
    estado = EstadoCompartilhadoRuntime(mental={"turno_atual": turno,
        "plano_turno_atual": plano, "retrato_turno_atual": retrato})
    normalizar = lambda valor: str(valor).casefold()
    apps = {"calculadora": "calc.exe", "notepad": "notepad.exe"}
    sites = {"github": "https://github.com", "youtube": "https://youtube.com"}
    detector = DeteccaoDeterministicaRuntime(namespace_getter=lambda: {
        "_normalizar_texto_com_apelidos": normalizar,
        "_extrair_intencao_abrir_app": lambda valor: extrair_intencao_abrir_app(valor,
            normalizar_texto=normalizar, limpar_destino=lambda valor: valor, apps_map=apps, sites_diretos=sites)}, estado_getter=lambda: {},
        sites_diretos=sites, apps_map=apps)
    validar = criar_validador_comandos_turno_runtime(estado_runtime=estado,
        resolver_ato=lambda literal, frame: detector.detectar(literal, estado_mental=frame))
    proposta = ContratoPropostaPrincipal(turno_id=str(turno["id"]), texto_usuario=texto,
                                        resposta_bruta='{"fala":"diagnóstico","comandos":[]}')
    resultado = validar.validar_proposta([], proposta)
    assert resultado["autoriza_execucao"] and resultado["atos_aguardando_materializacao"]
    ato = resultado["atos_aguardando_materializacao"][-1]
    primeiro = detector.detectar(turno["segmentos"][0]["texto"], estado_mental=estado.snapshot()["mental"])
    assert primeiro, "alcançar interpretação do antecedente antes da fronteira contextual"
    pedido = {**primeiro, "id_solicitacao": "invocacao-do-antecedente"}
    intent = pedido["intent"]
    params = deepcopy(pedido["params"])
    alvo = params.get("nome_app") or params.get("alvo") or params.get("url") or ""
    receipt = ResultadoAcao(intent=intent, params=params, alvo=alvo,
        id_solicitacao=pedido["id_solicitacao"], origem="executor", confirmado=True,
        executou=True, status={"VOLUME": "volume_ajustado", "OPEN_URL": "url_aberta"}.get(intent, "app_aberto"))
    observacao = ExecucaoObservada(str(turno["id"]), SnapshotComandoIA(pedido),
                                  (SnapshotComandoIA(receipt.como_dict()),), True, (time.monotonic(),))
    return validar, estado, proposta, ato, observacao, receipt


def materializar(validar, ato, proposta, observacoes):
    metodo = getattr(validar, "materializar_ato_contextual", None)
    return metodo(ato, proposta, observacoes) if callable(metodo) else None


@pytest.mark.parametrize("params,alvo", [
    ({"left": "Calculadora"}, "Calculadora"),
    ({"right": "Notepad"}, "Notepad"),
    ({"esquerda": "ensaio na direita"}, "ensaio na direita"),
    ({"left": "Calculadora", "right": "Notepad"}, ""),
    ({}, ""),
])
def test_referencia_de_resultado_composto_usa_alvo_estruturado_nao_descricao(params, alvo):
    from mente_laylay.memoria_mental.contexto_imediato import _referencia_de_continuidade
    registro = {"dominio": "app", "intent": "ORGANIZAR_DESKTOP",
        "alvo": "Descrição para apresentação; não é uma entidade", "params": params}
    referencia = _referencia_de_continuidade(registro)
    assert referencia.get("alvo", "") == alvo
    if not alvo:
        assert referencia == {}, "layout plural/sem alvo não identifica app único"


@pytest.mark.parametrize("texto,intent,chave,valor", [
    ("abre o aplicativo Calculadora e coloca ela à esquerda", "ORGANIZAR_DESKTOP", "left", "calculadora"),
    ("abre o aplicativo Notepad e coloca ele à direita", "ORGANIZAR_DESKTOP", "right", "notepad"),
    ("abre o aplicativo Calculadora e maximiza ela", "MAXIMIZE_WINDOW", "nome_app", "calculadora"),
    ("abre o aplicativo Notepad e bota ele em foco", "APP_OPEN", "nome_app", "notepad"),
    ("abre o site github e fecha ele", "CLOSE_TAB", "alvo", "github"),
])
def test_owner_canonico_resolve_mas_principal_precisa_transportar_materializacao(texto, intent, chave, valor):
    validar, estado, proposta, ato, obs, receipt = preparar(texto)
    # Contraprova: gramática/continuidade já sabem materializar o referente.
    projecao = registrar_resultado_execucao({}, receipt)
    literal = ato.como_dict()["texto_original"]
    referencia = referencia_contextual_imediata(mente_integrada_estado=projecao, foco_vivo={}, texto_atual=literal)
    retrato = {"referencia_resolvida": {"tipo": referencia.get("tipo"), "nome": referencia.get("alvo"),
                                       "dados": referencia.get("params")}}
    projecao["turno_atual"] = {"id": ato.turno_id, "texto": literal, "autoriza_execucao": True,
        "referencia_resolvida": retrato["referencia_resolvida"]}
    controle = resolver_referencias_da_intencao(validar._resolver_ato(literal, projecao), retrato)
    assert controle and controle["intent"] == intent, "não confundir falha da gramática com falta da ligação"
    antes = estado.snapshot()
    resultado = materializar(validar, ato, proposta, (obs,))
    assert resultado is not None, "obrigação não atravessou a materialização com receipt da invocação"
    pedido = resultado.pedido.como_dict()
    assert pedido["intent"] == intent and pedido["params"][chave] == valor
    assert resultado.indice_antecedente == 0
    assert resultado.ato == ato and resultado.observacao == obs
    assert resultado.autoriza_execucao is False and resultado.comprova_efeito is False
    assert estado.snapshot() == antes, "materialização não publica estado nem efeito"


@pytest.mark.parametrize("alteracao", [
    {"confirmado": False, "executou": False, "status": "falha_execucao"},
    {"confirmado": None}, {"executou": False, "status": "envio_sem_observacao"},
])
def test_receipt_falho_incerto_ou_sem_efeito_nao_materializa(alteracao):
    validar, _, proposta, ato, obs, receipt = preparar()
    ultimo = replace(receipt, **alteracao)
    atualizado = replace(obs, publicacoes=(SnapshotComandoIA(ultimo.como_dict()),))
    assert materializar(validar, ato, proposta, (atualizado,)) is None


def test_idempotencia_confirmada_continua_referenciavel_sem_novo_efeito():
    validar, _, proposta, ato, obs, receipt = preparar()
    receipt = replace(receipt, executou=False, status="ja_aberto_focado")
    obs = replace(obs, retorno_legado=False, publicacoes=(SnapshotComandoIA(receipt.como_dict()),))
    assert materializar(validar, ato, proposta, (obs,)) is not None


def test_publicacao_final_incerta_nao_empresta_a_anterior_confirmada():
    validar, _, proposta, ato, obs, receipt = preparar()
    final = replace(receipt, confirmado=None, status="envio_sem_observacao")
    obs = replace(obs, publicacoes=(*obs.publicacoes, SnapshotComandoIA(final.como_dict())),
                  instantes_publicacao=(*obs.instantes_publicacao, time.monotonic()))
    assert materializar(validar, ato, proposta, (obs,)) is None


@pytest.mark.parametrize("modo", ["vazio", "cache", "dict", "turno_alheio", "alvo_alheio", "duplicado"])
def test_observacao_nao_qualificada_nao_empresta_ultima_acao(modo):
    validar, estado, proposta, ato, obs, receipt = preparar()
    estado.atualizar("mental", lambda atual: {**atual, **registrar_resultado_execucao({}, receipt)})
    observacoes = (obs,)
    if modo == "vazio": observacoes = ()
    elif modo == "cache": observacoes = (replace(obs, publicacoes=(), instantes_publicacao=()),)
    elif modo == "dict": observacoes = (obs.como_dict(),)
    elif modo == "turno_alheio": observacoes = (replace(obs, turno_id="outro-turno"),)
    elif modo == "alvo_alheio":
        pedido = {**obs.pedido.como_dict(), "params": {"nome_app": "Notepad"}}
        observacoes = (replace(obs, pedido=SnapshotComandoIA(pedido)),)
    else: observacoes = (obs, obs)
    assert materializar(validar, ato, proposta, observacoes) is None


@pytest.mark.parametrize("campo", ["turno_atual", "plano_turno_atual", "retrato_turno_atual"])
def test_frame_obsoleto_e_recusado_antes_de_resolver(campo):
    validar, estado, proposta, ato, obs, _ = preparar()
    novo = estado.obter_copia("mental", campo)
    novo["id"] = "outro-frame"
    estado.atualizar("mental", lambda atual: {**atual, campo: novo})
    validar._resolver_ato = lambda *_: pytest.fail("não resolver frame obsoleto")
    assert materializar(validar, ato, proposta, (obs,)) is None


def test_frame_trocado_durante_resolucao_nao_publica_materializacao():
    validar, estado, proposta, ato, obs, _ = preparar()
    original = validar._resolver_ato
    def trocar(literal, frame):
        candidato = original(literal, frame)
        if literal == ato.como_dict()["texto_original"]:
            atual = estado.obter_copia("mental", "turno_atual")
            atual["autoriza_execucao"] = False
            estado.atualizar("mental", lambda mental: {**mental, "turno_atual": atual})
        return candidato
    validar._resolver_ato = trocar
    assert materializar(validar, ato, proposta, (obs,)) is None


def test_dois_apps_anteriores_nao_escolhem_alvo_por_ultima_posicao():
    texto = "abre o aplicativo Calculadora e abre o aplicativo Notepad e coloca ela à esquerda"
    validar, estado, proposta, ato, obs, _ = preparar(texto)
    segundo = validar._resolver_ato(estado.snapshot()["mental"]["turno_atual"]["segmentos"][1]["texto"],
                                   estado.snapshot()["mental"])
    pedido = {**segundo, "id_solicitacao": "segunda-invocacao"}
    receipt = ResultadoAcao(intent=pedido["intent"], params=pedido["params"], alvo="notepad",
        origem="executor", id_solicitacao=pedido["id_solicitacao"], executou=True, confirmado=True, status="app_aberto")
    segunda_obs = ExecucaoObservada(ato.turno_id, SnapshotComandoIA(pedido), (SnapshotComandoIA(receipt.como_dict()),), True, (time.monotonic(),))
    assert materializar(validar, ato, proposta, (obs, segunda_obs)) is None


def test_referente_compativel_pode_ser_anterior_ao_ultimo_ato_independente():
    texto = "abre o aplicativo Calculadora e coloca o volume em 40 e coloca ela à esquerda"
    validar, estado, proposta, ato, obs, _ = preparar(texto)
    volume = validar._resolver_ato(estado.snapshot()["mental"]["turno_atual"]["segmentos"][1]["texto"],
                                 estado.snapshot()["mental"])
    pedido = {**volume, "id_solicitacao": "invocacao-volume"}
    receipt = ResultadoAcao(intent="VOLUME", params=pedido["params"], origem="executor",
        id_solicitacao=pedido["id_solicitacao"], executou=True, confirmado=True, status="volume_ajustado")
    volume_obs = ExecucaoObservada(ato.turno_id, SnapshotComandoIA(pedido), (SnapshotComandoIA(receipt.como_dict()),), True, (time.monotonic(),))
    resultado = materializar(validar, ato, proposta, (obs, volume_obs))
    assert resultado is not None and resultado.indice_antecedente == 0
    assert resultado.pedido.como_dict()["params"]["left"] == "calculadora"


def test_snapshots_materializados_nao_podem_alterar_obrigacao_ou_receipt():
    validar, _, proposta, ato, obs, _ = preparar()
    resultado = materializar(validar, ato, proposta, (obs,))
    antes = resultado.como_dict()
    resultado.pedido.como_dict()["params"]["left"] = "outro"
    resultado.referencia.como_dict()["alvo"] = "outro"
    assert resultado.como_dict() == antes
    assert ato.como_dict()["autoriza_execucao"] is False


def test_proposta_tecnica_sem_proveniencia_nao_materializa():
    validar, _, proposta, ato, obs, _ = preparar()
    proposta = replace(proposta, resposta_bruta="", sucesso_modelo=False)
    assert materializar(validar, ato, proposta, (obs,)) is None


def test_ato_da_fonte_original_nao_sobrevive_a_revogacao_do_segmento():
    validar, estado, proposta, ato, obs, _ = preparar()
    turno = estado.obter_copia("mental", "turno_atual")
    turno["segmentos"][ato.indice]["autoriza_execucao"] = False
    turno["segmentos"][ato.indice]["veto_execucao_operacional"] = True
    estado.atualizar("mental", lambda atual: {**atual, "turno_atual": turno})
    assert materializar(validar, ato, proposta, (obs,)) is None


def test_duas_ordens_identicas_nao_identificam_antecedente_por_adivinhacao():
    validar, _, proposta, ato, obs, _ = preparar(
        "abre o aplicativo Calculadora e abre o aplicativo Calculadora e coloca ela à esquerda")
    assert materializar(validar, ato, proposta, (obs,)) is None


def test_dict_diagnostico_nao_volta_como_ato_executavel():
    validar, _, proposta, ato, obs, _ = preparar()
    assert materializar(validar, ato.como_dict(), proposta, (obs,)) is None


def test_sem_instante_observado_projecao_nao_rejuvenesce_receipt():
    validar, _, proposta, ato, obs, _ = preparar()
    obs = replace(obs, instantes_publicacao=())
    assert materializar(validar, ato, proposta, (obs,)) is None, "timestamp da projeção não é idade da publicação"


def test_materializacao_nao_troca_maquina_do_referente_por_default_local():
    validar, _, proposta, ato, obs, receipt = preparar()
    original = validar._resolver_ato
    def resolver(literal, frame):
        resultado = original(literal, frame)
        if literal != ato.como_dict()["texto_original"] and resultado:
            resultado["params"]["target"] = "pc_b"
        return resultado
    validar._resolver_ato = resolver
    pedido = obs.pedido.como_dict()
    pedido["params"]["target"] = "pc_b"
    receipt = replace(receipt, params={**receipt.params, "target": "pc_b"})
    remoto = replace(obs, pedido=SnapshotComandoIA(pedido), publicacoes=(SnapshotComandoIA(receipt.como_dict()),))
    assert materializar(validar, ato, proposta, (remoto,)) is None


def test_principal_instalado_admite_continuacao_confirmada_e_recusa_incerta():
    from scripts.analises.sonda_escopo_propostas_mistas import coletar
    relatorio = coletar()
    assert relatorio["fontes_estaveis"]
    positivos = {c["id"]: c for c in relatorio["pipelines_instalados"]}
    caso = positivos["principal_materializado_sem_admissao"]
    assert not caso["falhas"]
    assert caso["materializacoes_observadas"]
    assert [p["intent"] for p in caso["recebidos"]] == ["APP_OPEN", "ORGANIZAR_DESKTOP"]
    assert len(caso["falas_porta_isolada"]) == 1
    assert caso["plano"]["fase"] == "executado" and not caso["plano"]["erros"]
    incerto = positivos["principal_incerto_nao_materializa"]
    assert not incerto["falhas"] and not incerto["materializacoes_observadas"]
    assert len(incerto["recebidos"]) == 1
    assert relatorio["runtime_main_validado"] is False
