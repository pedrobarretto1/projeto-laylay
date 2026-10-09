from __future__ import annotations

from copy import deepcopy
import inspect
import json
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.cognicao import decisao_turno
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import alinhar_identidade_plano_revisao
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime


def _frame(texto: str, *, revisada: bool = False) -> dict:
    revisao = resolver_revisao_intra_turno(texto) if revisada else {}
    efetivo = revisao.get("texto_operacional_efetivo") or texto
    turno = classificar_modalidade_turno(efetivo)
    retrato, _ = construir_retrato_turno(efetivo, turno=turno, mente={}, contexto_perceptivo={})
    turno["retrato_id"] = retrato["id"]
    plano = planejar_turno(efetivo, turno=turno, mente={})
    if revisada:
        turno.update(texto=texto, texto_original=texto, texto_operacional_efetivo=efetivo)
        plano = alinhar_identidade_plano_revisao(
            plano, texto_original=texto, texto_operacional_efetivo=efetivo,
            revisao_intra_turno=revisao,
        )
    return {"turno_atual": turno, "plano_turno_atual": plano, "retrato_turno_atual": retrato}


def _atribuir_id(frame: dict, identidade) -> None:
    frame["turno_atual"].update(id=identidade, retrato_id=identidade)
    frame["plano_turno_atual"].update(id=identidade, retrato_id=identidade)
    frame["plano_turno_atual"]["decisao_turno"]["turno_id"] = identidade
    frame["retrato_turno_atual"]["id"] = identidade


def _principal(frame: dict, texto: str, *, bruto: str | None = None, sucesso: bool = True):
    return ContratoPropostaPrincipal(
        turno_id=frame["turno_atual"]["id"], texto_usuario=texto,
        resposta_bruta=bruto if bruto is not None else '{"fala":"Vou verificar.","comandos":[]}',
        sucesso_modelo=sucesso,
    )


def _filtrar(frame: dict, comandos: list, principal):
    # Enquanto a fronteira ainda não recebe a fonte, reproduz a rota existente.
    # Os REDs comportamentais abaixo permanecem os mesmos após acrescentá-la.
    opcoes = {}
    if "proposta_principal" in inspect.signature(decisao_turno.filtrar_comandos_pelo_turno).parameters:
        opcoes["proposta_principal"] = principal
    return decisao_turno.filtrar_comandos_pelo_turno(
        comandos, turno=frame["turno_atual"], plano=frame["plano_turno_atual"],
        retrato=frame["retrato_turno_atual"], **opcoes,
    )


@pytest.mark.parametrize("texto,intent", [
    ("cria a playlist foco", "PLAYLIST_CREATE"),
    ("liga a lâmpada", "IOT_CONTROL"),
    ("abre a Calculadora", "APP_OPEN"),
    ("apaga o arquivo foco", "DELETE_ITEM"),
])
def test_mesma_fala_em_nova_ocorrencia_nao_reutiliza_proposta_antiga(texto, intent) -> None:
    original = _frame(texto)
    principal = _principal(original, texto)
    comando = {"intent": intent, "params": {}}
    assert _filtrar(original, [comando], principal)["comandos"] == [comando]
    atual = deepcopy(original)
    _atribuir_id(atual, original["turno_atual"]["id"] + 1)
    assert decisao_turno.motivo_incoerencia_contratos_turno(
        atual["turno_atual"], atual["plano_turno_atual"], atual["retrato_turno_atual"],
    ) == ""
    resultado = _filtrar(atual, [comando], principal)
    assert resultado["comandos"] == [], "coerência do frame novo não vincula a emissão antiga"
    assert resultado["proposta_vinculada"] is False
    assert "proposta principal" in resultado["rejeitados"][0]["motivo"]


def test_troca_coerente_de_operacao_nao_prova_incompatibilidade_da_proposta_original() -> None:
    original = _frame("apaga o arquivo foco")
    principal = _principal(original, "apaga o arquivo foco")
    comando = {"intent": "DELETE_ITEM", "params": {}}
    assert _filtrar(original, [comando], principal)["comandos"] == [comando]
    atual = _frame("cria a playlist foco")
    resultado = _filtrar(atual, [comando], principal)
    assert resultado.get("proposta_vinculada") is False
    assert "intenção incompatível" not in resultado["rejeitados"][0]["motivo"]


def test_id_reutilizado_com_outro_texto_nao_vincula_emissao() -> None:
    original = _frame("cria a playlist foco")
    principal = _principal(original, "cria a playlist foco")
    atual = _frame("cria a playlist estudo")
    _atribuir_id(atual, original["turno_atual"]["id"])
    resultado = _filtrar(atual, [{"intent": "PLAYLIST_CREATE", "params": {}}], principal)
    assert resultado["comandos"] == []
    assert resultado["proposta_vinculada"] is False
    assert resultado["ocorrencia_vinculada"] is False
    assert "texto" in resultado["rejeitados"][0]["motivo"]


@pytest.mark.parametrize("principal", [None, {}, {"turno_id": 42, "origem": "llm_principal"}])
def test_fonte_nao_tipada_nao_reconstroi_vinculo(principal) -> None:
    frame = _frame("cria a playlist foco")
    resultado = _filtrar(frame, [{"intent": "PLAYLIST_CREATE", "params": {}}], principal)
    assert resultado["comandos"] == []
    assert resultado["proposta_vinculada"] is False


@pytest.mark.parametrize("bruto,sucesso", [
    ("", True), ("__LAYLAY_LLM_TIMEOUT__", True), ('{"fala":"Oi"}', False),
])
def test_falha_ou_ausencia_da_fonte_nao_e_validacao_de_proposta(bruto, sucesso) -> None:
    frame = _frame("cria a playlist foco")
    principal = _principal(frame, "cria a playlist foco", bruto=bruto, sucesso=sucesso)
    assert principal.proveniencia_conhecida is False
    resultado = _filtrar(frame, [{"intent": "PLAYLIST_CREATE", "params": {}}], principal)
    assert resultado["comandos"] == []
    assert resultado["proposta_vinculada"] is False
    assert resultado["ocorrencia_vinculada"] is True


@pytest.mark.parametrize("texto,intent,revisada", [
    ("Abre o Opera... não, abre a Calculadora.", "APP_OPEN", True),
    ("Liga a lâmpada... não, desliga a lâmpada.", "IOT_CONTROL", True),
    ("Toca uma música do C418", "MUSIC_SEARCH", False),
    ("cria a playlist foco " + "com uma descrição extensa " * 25, "PLAYLIST_CREATE", False),
])
def test_vinculo_preserva_revisao_e_representacao_textual_publicada(texto, intent, revisada) -> None:
    frame = _frame(texto, revisada=revisada)
    _atribuir_id(frame, " 42 ")
    principal = _principal(frame, "  " + texto + "  ")
    comando = {"intent": intent, "params": {}}
    resultado = _filtrar(frame, [comando], principal)
    assert resultado["comandos"] == [comando]
    assert resultado.get("proposta_vinculada") is True
    assert principal.autoriza_execucao is False


def _validador(estado: EstadoCompartilhadoRuntime):
    criar = getattr(decisao_turno, "criar_validador_comandos_turno_runtime", None)
    if callable(criar):
        return criar(estado_runtime=estado)
    # Callback anterior: preservado aqui exclusivamente para reproduzir RED.
    return lambda comandos: decisao_turno.filtrar_comandos_pelo_turno(
        comandos, turno=dict(estado.mental["turno_atual"]),
        plano=dict(estado.mental["plano_turno_atual"]), retrato=dict(estado.mental["retrato_turno_atual"]),
    )


@pytest.mark.parametrize("trocar,legado,zerar,pergunta", [
    (False, False, False, False), (True, False, False, False), (False, True, False, False),
    (True, False, True, False), (True, False, False, True),
])
def test_runtime_encaminha_fonte_e_interrompe_publicacao_da_resposta_obsoleta(trocar, legado, zerar, pergunta) -> None:
    texto = "você conhece playlists?" if pergunta else "cria a playlist foco"
    original = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=original)
    candidato = {"intent": "PLAYLIST_CREATE", "params": {}}
    chamadas = []
    pedidos = []
    registros = []
    chamadas_legadas = []
    validador = _validador(estado)

    def validar_legado(comandos):
        chamadas_legadas.append(comandos)
        return validador(comandos)

    callback_validacao = validar_legado if legado else validador

    def emitir(pedido):
        pedidos.append(pedido)
        return ResultadoModelo(json.dumps({"fala": "Vou verificar.", "comandos": [candidato]}), True)

    def preparar(_texto, bruto):
        if trocar:
            atual = deepcopy(original)
            _atribuir_id(atual, original["turno_atual"]["id"] + 1)
            estado.substituir("mental", atual)
        preparada = json.loads(bruto)
        if zerar:
            preparada["comandos"] = []
        return preparada

    def dispatcher(_ctx, _texto, comandos, *_args):
        chamadas.append(("dispatcher", comandos))
        return {"erros": []}

    runtime = RespostaIARuntime(
        contexto_getter=lambda: {
            "obter_turno_atual": lambda: estado.obter_copia("mental", "turno_atual"),
            "usar_modo_rapido": lambda _texto: False,
            "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda _texto: PacotePrompt(())),
            "modelo_llm": SimpleNamespace(executar=emitir),
            "preparar_resposta": preparar,
            "validar_comandos_planejados": callback_validacao,
            "atualizar_plano_turno": lambda *_a, **_k: chamadas.append(("publicacao", None)),
            "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
            "executar_comandos_json": dispatcher,
            "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
            "finalizar_execucao": lambda *_a: chamadas.append(("finalizacao", None)) or {},
        },
        log=lambda *args: registros.append(args),
    )
    runtime.processar(texto)
    assert len(pedidos) == 1
    assert pedidos[0].tipo_chamada == "principal"
    assert chamadas_legadas == ([[candidato]] if legado else [])
    if trocar:
        assert chamadas == [], "a fonte antiga deve parar antes de writer, dispatcher e finalização"
        assert any("proposta principal" in str(item).casefold() for item in registros)
    else:
        despachados = next(itens for nome, itens in chamadas if nome == "dispatcher")
        assert len(despachados) == 1 and despachados[0]["id_solicitacao"]
        assert {chave: valor for chave, valor in despachados[0].items()
                if chave != "id_solicitacao"} == candidato
        # O receipt da execução é publicado antes da finalização da fala.
        assert [nome for nome, _ in chamadas] == ["publicacao", "dispatcher", "publicacao", "finalizacao"]


def test_formato_legado_nao_passa_a_declarar_vinculo_de_fonte() -> None:
    estado = EstadoCompartilhadoRuntime(mental=_frame("cria a playlist foco"))
    callback = _validador(estado)
    comando = {"intent": "PLAYLIST_CREATE", "params": {}}
    resultado = callback([comando])
    assert resultado["comandos"] == [comando]
    assert "proposta_vinculada" not in resultado


def test_emissao_vinculada_nao_autoriza_acao_em_pergunta() -> None:
    texto = "você conhece a Calculadora?"
    frame = _frame(texto)
    principal = _principal(frame, texto)
    resultado = _filtrar(frame, [{"intent": "APP_OPEN", "params": {}}], principal)
    assert resultado["proposta_vinculada"] is True
    assert resultado["autoriza_execucao"] is False
    assert resultado["comandos"] == []
    assert resultado["rejeitados"][0]["motivo"] == "turno não autorizou execução"


def test_vinculo_legitimo_preserva_rejeicao_operacional_do_mesmo_frame() -> None:
    texto = "cria a playlist foco"
    frame = _frame(texto)
    principal = _principal(frame, texto)
    resultado = _filtrar(frame, [{"intent": "DELETE_ITEM", "params": {}}], principal)
    assert resultado["proposta_vinculada"] is True
    assert resultado["comandos"] == []
    assert resultado["rejeitados"][0]["motivo"] == "intenção incompatível com a operação explícita"
    assert principal.autoriza_execucao is False


@pytest.mark.parametrize("separador", [" ", "\n", "\t"])
def test_espaco_no_limite_publicado_nao_diverge_da_fala_original_completa(separador) -> None:
    prefixo = "cria a playlist foco "
    texto = prefixo + "a" * (499 - len(prefixo)) + separador + "continua"
    frame = _frame(texto)
    assert decisao_turno.motivo_incoerencia_contratos_turno(
        frame["turno_atual"], frame["plano_turno_atual"], frame["retrato_turno_atual"],
    ) == ""
    principal = _principal(frame, texto)
    resultado = _filtrar(frame, [{"intent": "PLAYLIST_CREATE", "params": {}}], principal)
    assert resultado["comandos"], "a mesma fala truncada no espaço continua pertencendo à emissão"
    assert resultado["proposta_vinculada"] is True
    assert principal.texto_usuario == texto


def _processar_com_retorno_moderno(
    retorno, *, texto="cria a playlist foco", bruto='{"fala":"Oi"}', sucesso=True,
    usar_validador_real=False,
):
    estado = EstadoCompartilhadoRuntime(mental=_frame(texto))
    validador_real = _validador(estado)
    candidato = {"intent": "PLAYLIST_CREATE", "params": {}}
    chamadas = []
    falhas = []
    chamadas_validacao = []
    entregues = []
    pedidos = []

    def emitir(pedido):
        pedidos.append(pedido)
        return ResultadoModelo(bruto, sucesso)

    def dispatcher(_ctx, _texto, comandos, *_args):
        chamadas.append("dispatcher")
        entregues.append(comandos)
        return {"erros": []}

    def legado(comandos):
        chamadas_validacao.append("legado")
        return {"comandos": comandos}

    def moderno(_comandos, _principal):
        chamadas_validacao.append("moderno")
        if usar_validador_real:
            return validador_real.validar_proposta(_comandos, _principal)
        return retorno

    legado.validar_proposta = moderno
    runtime = RespostaIARuntime(
        contexto_getter=lambda: {
            "obter_turno_atual": lambda: estado.obter_copia("mental", "turno_atual"),
            "usar_modo_rapido": lambda _texto: False,
            "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda _texto: PacotePrompt(())),
            "modelo_llm": SimpleNamespace(executar=emitir),
            "preparar_resposta": lambda *_args: {"fala": "Vou verificar.", "comandos": [candidato]},
            "validar_comandos_planejados": legado,
            "atualizar_plano_turno": lambda *_a, **_k: chamadas.append("publicacao"),
            "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
            "executar_comandos_json": dispatcher,
            "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
            "finalizar_execucao": lambda *_a: chamadas.append("finalizacao") or {},
            "registrar_falha_diagnostico": lambda *a, **k: falhas.append((a, k)),
        }, log=lambda *_args: None,
    )
    runtime.processar(texto)
    return chamadas, chamadas_validacao, falhas, entregues, pedidos


@pytest.mark.parametrize("retorno", [
    None, [], {}, {"comandos": [{"intent": "PLAYLIST_CREATE"}]},
    {"comandos": [{"intent": "PLAYLIST_CREATE"}], "proposta_vinculada": "sim", "ocorrencia_vinculada": True},
    {"comandos": [{"intent": "PLAYLIST_CREATE"}], "rejeitados": [], "proposta_vinculada": False, "ocorrencia_vinculada": True},
    {"comandos": [{"intent": "PLAYLIST_CREATE"}], "rejeitados": [], "proposta_vinculada": True, "ocorrencia_vinculada": True, "autoriza_execucao": False},
])
def test_retorno_moderno_invalido_aborta_sem_repetir_callback_legado(retorno) -> None:
    chamadas, chamadas_validacao, falhas, entregues, pedidos = _processar_com_retorno_moderno(retorno)
    assert chamadas == []
    assert chamadas_validacao == ["moderno"]
    assert falhas and falhas[0][0] == ("turno", "erro_resposta_ia")
    assert entregues == []
    assert len(pedidos) == 1


def test_retorno_moderno_nao_restabelece_comandos_vetados_pela_autoridade_congelada() -> None:
    retorno = {
        "comandos": [{"intent": "PLAYLIST_CREATE", "params": {}}], "rejeitados": [],
        "proposta_vinculada": True, "ocorrencia_vinculada": True,
    }
    chamadas, chamadas_validacao, falhas, entregues, pedidos = _processar_com_retorno_moderno(
        retorno, texto="você conhece playlists?",
    )
    assert entregues == [[]], "correlação não autoriza os comandos fabricados pelo callback"
    assert chamadas_validacao == ["moderno"]
    assert falhas == []
    assert len(pedidos) == 1


@pytest.mark.parametrize("usar_validador_real", [False, True])
@pytest.mark.parametrize("bruto,sucesso", [("__LAYLAY_LLM_TIMEOUT__", True), ("", False)])
def test_falha_do_modelo_no_mesmo_turno_preserva_conclusao_sem_comandos(bruto, sucesso, usar_validador_real) -> None:
    retorno = {
        "comandos": [], "rejeitados": [],
        "proposta_vinculada": False, "ocorrencia_vinculada": True,
    }
    chamadas, chamadas_validacao, falhas, entregues, pedidos = _processar_com_retorno_moderno(
        retorno, bruto=bruto, sucesso=sucesso, usar_validador_real=usar_validador_real,
    )
    assert "finalizacao" in chamadas
    assert entregues == [[]]
    assert chamadas_validacao == ["moderno"]
    assert falhas == []
    assert len(pedidos) == 1


@pytest.mark.parametrize("bruto,sucesso", [
    ("__LAYLAY_LLM_TIMEOUT__", True), ("", True), ('{"fala":"Oi"}', False),
])
def test_retorno_moderno_nao_promove_fonte_capturada_insuficiente(bruto, sucesso) -> None:
    retorno = {
        "comandos": [{"intent": "PLAYLIST_CREATE", "params": {}}], "rejeitados": [],
        "proposta_vinculada": True, "ocorrencia_vinculada": True,
    }
    chamadas, chamadas_validacao, falhas, entregues, pedidos = _processar_com_retorno_moderno(
        retorno, bruto=bruto, sucesso=sucesso,
    )
    assert chamadas == [], "o callback não materializa procedência que falta na fonte capturada"
    assert chamadas_validacao == ["moderno"]
    assert falhas and falhas[0][0] == ("turno", "erro_resposta_ia")
    assert entregues == []
    assert len(pedidos) == 1


def test_runtime_transporta_snapshot_original_tipado_apos_reparo_real(monkeypatch) -> None:
    from mente_laylay.autonomia import processamento_resposta_ia as processamento
    from mente_laylay.autonomia import resposta_ia_runtime as modulo_resposta

    texto = "cria a playlist foco"
    comando = {
        "intent": "PLAYLIST_CREATE",
        "params": {"nome_playlist": "foco", "target": "pc_b", "extra": {"itens": [1]}},
    }
    bruto = json.dumps({"fala": "Entendi seu pedido.", "comandos": [comando]})
    reparada = '{"fala":"Entendi seu pedido.","comandos":[]}'
    estado = EstadoCompartilhadoRuntime(mental=_frame(texto))
    validador = _validador(estado)
    capturas = []
    capturas_validacao = []
    pedidos = []
    entregues = []
    normalizar_real = modulo_resposta.normalizar_resposta_preparada

    class ObservarValidador:
        def __call__(self, comandos):
            return validador(comandos)

        def validar_proposta(self, comandos, principal):
            return validador.validar_proposta(comandos, principal)

        def validar_proposta_original(self, comandos, principal, extracao):
            capturas_validacao.append(extracao)
            metodo = getattr(validador, "validar_proposta_original", None)
            return metodo(comandos, principal, extracao) if callable(metodo) else self.validar_proposta(comandos, principal)

    def observar_normalizacao(dados, **kwargs):
        contrato = normalizar_real(dados, **kwargs)
        capturas.append(contrato)
        return contrato

    def emitir(pedido):
        pedidos.append(pedido)
        return ResultadoModelo(bruto, True)

    def preparar(t, original):
        return processamento.preparar_resposta_para_execucao(
            t, original, enviar_mensagem_cb=None, limpar_texto_fala_cb=lambda fala: fala,
            fallback_fala="Estou aqui.", memoria_sqlite=None, log=lambda *_args: None,
        )

    def dispatcher(_ctx, _texto, comandos, *_args):
        entregues.append(comandos)
        return {"erros": []}

    monkeypatch.setattr(processamento, "corrigir_saida_malformada_da_ia", lambda *_args: reparada)
    monkeypatch.setattr(modulo_resposta, "normalizar_resposta_preparada", observar_normalizacao)
    runtime = RespostaIARuntime(
        contexto_getter=lambda: {
            "obter_turno_atual": lambda: estado.obter_copia("mental", "turno_atual"),
            "usar_modo_rapido": lambda _texto: False,
            "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda _texto: PacotePrompt(())),
            "modelo_llm": SimpleNamespace(executar=emitir),
            "preparar_resposta": preparar,
            "validar_comandos_planejados": ObservarValidador(),
            "atualizar_plano_turno": lambda *_a, **_k: None,
            "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
            "executar_comandos_json": dispatcher,
            "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
            "finalizar_execucao": lambda *_a: {},
        }, log=lambda *_args: None,
    )
    runtime.processar(texto)
    assert len(capturas) == 1
    contrato = capturas[0]
    assert contrato.proposta_principal.resposta_bruta == bruto
    assert contrato.extracao_original.resposta_bruta == bruto
    assert contrato.extracao_original.comandos_originais[0].como_dict() == comando
    assert contrato.extracao_original.comandos_normalizados[0].como_dict() == comando
    assert contrato.extracao_original.proposta_operacional_explicita is True
    assert contrato.extracao_original.autoriza_execucao is False
    assert capturas_validacao == [contrato.extracao_original], "o validador precisa da fonte preservada, inclusive com lista final vazia"
    assert contrato.resposta_bruta == reparada
    assert contrato.comandos == ()
    assert entregues == [[]]
    assert len(pedidos) == 1 and pedidos[0].tipo_chamada == "principal"


def _validar_original(frame: dict, bruto: str, *, comandos_finais=(), sucesso=True):
    from mente_laylay.autonomia.higiene_resposta_ia import decodificar_resposta_da_ia

    principal = _principal(frame, frame["turno_atual"]["texto"], bruto=bruto, sucesso=sucesso)
    extracao = decodificar_resposta_da_ia(bruto).extracao
    callback = _validador(EstadoCompartilhadoRuntime(mental=frame))
    moderno = getattr(callback, "validar_proposta_original", None)
    if callable(moderno):
        resultado = moderno(list(comandos_finais), principal, extracao)
    else:
        resultado = callback.validar_proposta(list(comandos_finais), principal)
    return resultado, principal, extracao


@pytest.mark.parametrize("texto", [
    "cria a playlist foco", "crie a playlist estudo", "liga a lâmpada", "desliga o ventilador",
])
def test_violacao_original_de_intencao_sobrevive_a_lista_reparada_vazia(texto) -> None:
    frame = _frame(texto)
    bruto = json.dumps({"fala": "Vou verificar.", "comandos": [
        {"intent": "DELETE_ITEM", "params": {"alvo": "documento pessoal"}},
    ]})
    resultado, principal, extracao = _validar_original(frame, bruto)
    assert principal.proveniencia_conhecida and extracao.normalizacao_completa
    assert resultado["proposta_vinculada"] is True
    assert resultado["rejeitados"] == []
    provas = resultado.get("violacoes_proposta_original", ())
    assert len(provas) == 1, "o reparo não pode apagar a prova da incompatibilidade original"
    prova = provas[0]
    assert prova.turno_id == str(frame["turno_atual"]["id"])
    assert prova.indice_comando == 0 and prova.intent == "DELETE_ITEM"
    assert prova.motivo == "intenção incompatível com a operação explícita"
    assert prova.autoriza_execucao is False and prova.comprova_efeito_externo is False
    assert "documento pessoal" not in repr(prova)


@pytest.mark.parametrize("texto", ["como apagar o arquivo foco?", "não apague o arquivo estudo"])
def test_proposta_original_de_efeito_viola_veto_explicito_sem_virar_receipt(texto) -> None:
    frame = _frame(texto)
    assert frame["turno_atual"]["veto_execucao_operacional"] is True
    bruto = json.dumps({"fala": "Vou verificar.", "comandos": [{"intent": "DELETE_ITEM", "params": {}}]})
    resultado, _, _ = _validar_original(frame, bruto)
    provas = resultado.get("violacoes_proposta_original", ())
    assert len(provas) == 1, "a proposta explícita precisa ser comparada ao veto do mesmo turno"
    assert provas[0].motivo == "turno não autorizou execução"
    assert resultado["comandos"] == []


@pytest.mark.parametrize("texto,comando", [
    ("cria a playlist foco", {"acao": "criar_playlist", "alvo": "foco"}),
    ("liga a lâmpada", {"acao": "ligar", "alvo": "lampada_quarto"}),
    ("cria a playlist foco", {"intent": "PLAYLIST_CREATE", "params": {"nome_playlist": ""}}),
    ("abre a Calculadora", {"intent": "DELETE_ITEM", "params": {}}),
])
def test_alias_parametros_ou_retrato_sem_cobertura_nao_provam_erro_original(texto, comando) -> None:
    resultado, _, _ = _validar_original(_frame(texto), json.dumps({"fala": "Entendi.", "comandos": [comando]}))
    assert resultado.get("violacoes_proposta_original", ()) == ()


@pytest.mark.parametrize("original_invalido", [False, True])
def test_prova_original_nao_confunde_reparo_com_autoria(original_invalido) -> None:
    frame = _frame("cria a playlist foco")
    correto = {"intent": "PLAYLIST_CREATE", "params": {"nome_playlist": "foco"}}
    incorreto = {"intent": "DELETE_ITEM", "params": {}}
    original, final = (incorreto, correto) if original_invalido else (correto, incorreto)
    resultado, _, _ = _validar_original(
        frame, json.dumps({"fala": "Entendi.", "comandos": [original]}), comandos_finais=[final],
    )
    assert resultado["comandos"] == ([correto] if original_invalido else [])
    assert len(resultado.get("violacoes_proposta_original", ())) == int(original_invalido)


@pytest.mark.parametrize("bruto,sucesso", [
    ("Eu poderia usar delete_item: foco", True),
    ('{"fala":"Entendi.","comandos":[{"intent":"DELETE_ITEM","params":{}}]', True),
    ('{"fala":"Entendi.","comandos":[{"intent":"DELETE_ITEM","params":{"x":NaN}}]}', True),
    ('{"fala":"Entendi.","comandos":[{"intent":"DELETE_ITEM","acao":"criar_playlist"}]}', True),
    ('{"fala":"Entendi.","comandos":[{"intent":"DELETE_ITEM","params":{}}]}', False),
    ("__LAYLAY_LLM_TIMEOUT__", True),
    ('{"fala":"Entendi.","comandos":[]}', True),
    ('{"fala":"Entendi.","comandos":[{"intent":"DELETE_ITEM","params":{}},{"action":"unknown"}]}', True),
])
def test_fonte_incompleta_incerta_ou_tecnica_nao_prova_violacao(bruto, sucesso) -> None:
    resultado, _, _ = _validar_original(_frame("cria a playlist foco"), bruto, sucesso=sucesso)
    assert resultado.get("violacoes_proposta_original", ()) == ()


@pytest.mark.parametrize("campo,valor", [
    ("autoriza_execucao", "sim"), ("veto_execucao_operacional", 0),
    ("requer_execucao", "sim"), ("permite_acao", 1),
    ("intents_permitidos", ["PLAYLIST_CREATE", None]),
    ("intents_permitidos", "PLAYLIST_CREATE"), ("operacao_explicita", ""),
    ("proprietario", []), ("intents_permitidos", ["INTENT_INEXISTENTE"]),
])
def test_frame_malformado_nao_certifica_culpa_por_coercao(campo, valor) -> None:
    frame = _frame("cria a playlist foco")
    destino = (
        frame["turno_atual"] if campo in {"autoriza_execucao", "veto_execucao_operacional"}
        else frame["plano_turno_atual"] if campo == "requer_execucao"
        else frame["plano_turno_atual"]["decisao_turno"] if campo in {"permite_acao", "proprietario"}
        else frame["retrato_turno_atual"]
    )
    destino[campo] = valor
    resultado, _, _ = _validar_original(frame, '{"fala":"Entendi.","comandos":[{"intent":"DELETE_ITEM","params":{}}]}')
    assert resultado.get("violacoes_proposta_original", ()) == ()


def test_prova_exige_ocorrencia_vigente_e_extracao_da_mesma_emissao() -> None:
    from mente_laylay.autonomia.higiene_resposta_ia import decodificar_resposta_da_ia

    original = _frame("cria a playlist foco")
    bruto = '{"fala":"Entendi.","comandos":[{"intent":"DELETE_ITEM","params":{}}]}'
    principal = _principal(original, original["turno_atual"]["texto"], bruto=bruto)
    estado = EstadoCompartilhadoRuntime(mental=deepcopy(original))
    callback = _validador(estado)
    metodo = callback.validar_proposta_original
    extracao = decodificar_resposta_da_ia(bruto).extracao
    assert len(metodo([], principal, extracao)["violacoes_proposta_original"]) == 1
    outra_extracao = decodificar_resposta_da_ia(bruto.replace("Entendi.", "Entendi!")).extracao
    assert metodo([], principal, outra_extracao)["violacoes_proposta_original"] == ()
    assert metodo([], principal, {"normalizacao_completa": True})["violacoes_proposta_original"] == ()
    _atribuir_id(estado.mental, original["turno_atual"]["id"] + 1)
    resultado = metodo([], principal, extracao)
    assert resultado["ocorrencia_vinculada"] is False
    assert resultado["violacoes_proposta_original"] == ()


def test_filtro_executavel_e_prova_original_usam_um_unico_snapshot_real(monkeypatch) -> None:
    from mente_laylay.autonomia.higiene_resposta_ia import decodificar_resposta_da_ia
    from dataclasses import FrozenInstanceError

    frame = _frame("cria a playlist foco")
    bruto = '{"fala":"Entendi.","comandos":[{"intent":"DELETE_ITEM","params":{}}]}'
    principal = _principal(frame, frame["turno_atual"]["texto"], bruto=bruto)
    estado = EstadoCompartilhadoRuntime(mental=frame)
    snapshot_real = estado.snapshot
    capturas = []

    def capturar():
        snapshot = snapshot_real()
        capturas.append(snapshot)
        # Uma nova ocorrência depois da captura não reclassifica a fonte.
        _atribuir_id(estado.mental, frame["turno_atual"]["id"] + 1)
        return snapshot

    monkeypatch.setattr(estado, "snapshot", capturar)
    resultado = _validador(estado).validar_proposta_original(
        [], principal, decodificar_resposta_da_ia(bruto).extracao,
    )
    assert len(capturas) == 1
    assert resultado["proposta_vinculada"] is True
    assert len(resultado["violacoes_proposta_original"]) == 1
    prova = resultado["violacoes_proposta_original"][0]
    with pytest.raises(FrozenInstanceError):
        prova.motivo = "outro"


@pytest.mark.parametrize("estado_fonte", ["vigente", "obsoleta", "nao_vinculada"])
def test_runtime_diagnostica_violacao_original_reparada_sem_receipt_ou_chamada_extra(monkeypatch, estado_fonte) -> None:
    from mente_laylay.autonomia import processamento_resposta_ia as processamento

    texto = "cria a playlist foco"
    frame = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=frame)
    bruto = '{"fala":"Vou verificar.","comandos":[{"intent":"DELETE_ITEM","params":{"alvo":"conteudo privado"}}]}'
    reparada = '{"fala":"Entendi seu pedido.","comandos":[]}'
    pedidos, diagnosticos, entregues, publicacoes = [], [], [], []

    def emitir(pedido):
        pedidos.append(pedido)
        return ResultadoModelo(bruto, True)

    def preparar(t, original):
        preparada = processamento.preparar_resposta_para_execucao(
            t, original, enviar_mensagem_cb=None, limpar_texto_fala_cb=lambda fala: fala,
            fallback_fala="Estou aqui.", memoria_sqlite=None, log=lambda *_args: None,
        )
        if estado_fonte == "obsoleta":
            _atribuir_id(estado.mental, frame["turno_atual"]["id"] + 1)
        return preparada

    def dispatch(_ctx, _texto, comandos, *_args):
        entregues.append(comandos)
        return {"erros": []}

    monkeypatch.setattr(processamento, "corrigir_saida_malformada_da_ia", lambda *_args: reparada)
    validador = _validador(estado)
    if estado_fonte == "nao_vinculada":
        validar_real = validador.validar_proposta_original

        def negar_vinculo(*args):
            resultado = validar_real(*args)
            assert resultado["violacoes_proposta_original"]
            resultado["proposta_vinculada"] = False
            return resultado

        monkeypatch.setattr(validador, "validar_proposta_original", negar_vinculo)
    runtime = RespostaIARuntime(
        contexto_getter=lambda: {
            "obter_turno_atual": lambda: estado.obter_copia("mental", "turno_atual"),
            "usar_modo_rapido": lambda _texto: False,
            "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda _texto: PacotePrompt(())),
            "modelo_llm": SimpleNamespace(executar=emitir),
            "preparar_resposta": preparar,
            "validar_comandos_planejados": validador,
            "registrar_decisao_diagnostico": lambda *a, **k: diagnosticos.append((a, k)),
            "atualizar_plano_turno": lambda *a, **k: publicacoes.append((a, k)),
            "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
            "executar_comandos_json": dispatch,
            "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
            "finalizar_execucao": lambda *_a: {},
        }, log=lambda *_args: None,
    )
    runtime.processar(texto)
    assert len(pedidos) == 1 and pedidos[0].tipo_chamada == "principal"
    assert entregues == ([] if estado_fonte == "obsoleta" else [[]])
    eventos = [item for item in diagnosticos if item[1].get("categoria") == "proposta_original"]
    assert len(eventos) == int(estado_fonte == "vigente")
    if eventos:
        assert eventos[0][0][:2] == ("turno", "violacao_proposta")
        assert "intenção incompatível" in str(eventos[0])
        assert "conteudo privado" not in str(eventos[0])
    assert not any(k.get("erros") for _, k in publicacoes), "proposta rejeitada não é falha de um executor"


@pytest.mark.parametrize("campo,valor", [
    ("turno_id", {}), ("indice_comando", True), ("indice_comando", -1),
    ("intent", "texto pessoal"), ("motivo", "o modelo disse que errou"),
    ("proprietario", []), ("operacao_explicita", {"alvo": "privado"}),
])
def test_prova_tipada_recusa_metadados_malformados_antes_do_diagnostico(campo, valor) -> None:
    from mente_laylay.cognicao.contratos_turno import ViolacaoPropostaPrincipal

    campos = dict(
        turno_id="42", indice_comando=0, intent="DELETE_ITEM",
        motivo="intenção incompatível com a operação explícita",
        proprietario="operacional", operacao_explicita="playlist_criar",
    )
    campos[campo] = valor
    with pytest.raises(ValueError, match="Prova de violação"):
        ViolacaoPropostaPrincipal(**campos)


def test_avaliacao_pura_recusa_restricao_nao_coletavel_sem_coercao() -> None:
    from mente_laylay.autonomia.higiene_resposta_ia import decodificar_resposta_da_ia

    frame = _frame("cria a playlist foco")
    bruto = '{"fala":"Entendi.","comandos":[{"intent":"DELETE_ITEM","params":{}}]}'
    principal = _principal(frame, frame["turno_atual"]["texto"], bruto=bruto)
    frame["retrato_turno_atual"]["intents_permitidos"] = 42
    assert decisao_turno.avaliar_violacoes_proposta_original(
        principal, decodificar_resposta_da_ia(bruto).extracao,
        turno=frame["turno_atual"], plano=frame["plano_turno_atual"], retrato=frame["retrato_turno_atual"],
    ) == ()


def test_provas_conservam_posicao_de_candidatos_originais_sem_mesclar_intents() -> None:
    comandos = [
        {"intent": "PLAYLIST_CREATE", "params": {"nome_playlist": "foco"}},
        {"intent": "DELETE_ITEM", "params": {"alvo": "a"}},
        {"intent": "DELETE_ITEM", "params": {"alvo": "b"}},
    ]
    resultado, _, _ = _validar_original(
        _frame("cria a playlist foco"), json.dumps({"fala": "Entendi.", "comandos": comandos}),
    )
    provas = resultado["violacoes_proposta_original"]
    assert [item.indice_comando for item in provas] == [1, 2]
    assert [item.intent for item in provas] == ["DELETE_ITEM", "DELETE_ITEM"]


def test_metadados_de_violacao_no_json_do_modelo_nao_materializam_prova() -> None:
    bruto = json.dumps({
        "fala": "Entendi.", "comandos": [],
        "violacoes_proposta_original": [{"turno_id": "42", "intent": "DELETE_ITEM", "motivo": "turno não autorizou execução"}],
        "responsabilidade": "laylay", "confianca_responsabilidade": 1.0,
    })
    resultado, _, _ = _validar_original(_frame("cria a playlist foco"), bruto)
    assert resultado["violacoes_proposta_original"] == ()
