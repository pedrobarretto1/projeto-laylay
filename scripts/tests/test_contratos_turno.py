from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia import resposta_ia_runtime as modulo_resposta
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao import contratos_turno as modulo_contratos
from mente_laylay.cognicao.contratos_turno import (
    ContratoDecisaoTurno,
    ContratoRespostaTurno,
    normalizar_resposta_preparada,
)
from mente_laylay.cognicao.decisao_turno import consolidar_arbitragem
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo


class _MemoriaFalsa:
    def salvar_aprendizados_semanticos(self, itens):
        return list(itens or [])


def test_decisao_preserva_campos_legados_adicionais() -> None:
    contrato = ContratoDecisaoTurno.de_mapping({
        "turno_id": 42,
        "modalidade": "COMANDO",
        "proprietario": "OPERACIONAL",
        "permite_acao": True,
        "confianca": "0.8764",
        "campo_legado": {"preservar": True},
    })

    dados = contrato.como_dict()

    assert dados["modalidade"] == "comando"
    assert dados["proprietario"] == "operacional"
    assert dados["confianca"] == 0.876
    assert dados["campo_legado"] == {"preservar": True}


def test_arbitragem_continua_retornando_dicionario_compativel() -> None:
    base = ContratoDecisaoTurno(
        turno_id=7,
        modalidade="comando",
        proprietario="operacional",
        permite_acao=True,
    ).como_dict()

    consolidado = consolidar_arbitragem(base, {
        "decisao": {"intent": "open_url"},
        "origem": "deterministico",
        "confianca": 0.91,
    })

    assert isinstance(consolidado, dict)
    assert consolidado["intencao"] == "OPEN_URL"
    assert consolidado["status"] == "decidida"
    assert consolidado["permite_acao"] is True


def test_resposta_tipificada_faz_copias_defensivas() -> None:
    comando = {"intent": "TESTE", "params": {"valor": 1}}
    leitura = {"relacao": "independente"}
    contrato = ContratoRespostaTurno(
        fala="  resposta completa  ",
        comandos=(comando,),
        leitura_semantica=leitura,
    )
    comando["intent"] = "ALTERADO"
    leitura["relacao"] = "alterada"

    dados = contrato.como_dict()

    assert dados["fala"] == "resposta completa"
    assert dados["comandos"][0]["intent"] == "TESTE"
    assert dados["leitura_semantica"]["relacao"] == "independente"


def test_normalizador_de_resposta_descarta_comandos_malformados() -> None:
    contrato = normalizar_resposta_preparada({
        "fala": "Oi",
        "comandos": [{"intent": "OK"}, "invalido", None],
        "aprendizados": ["um"],
    })

    assert contrato.como_dict()["comandos"] == [{"intent": "OK"}]


def test_normalizador_de_resposta_aceita_campos_opcionais_nulos() -> None:
    contrato = normalizar_resposta_preparada({
        "fala": "Ainda estou aqui.",
        "comandos": None,
        "aprendizados": None,
        "leitura_semantica": None,
    })

    assert contrato.como_dict() == {
        "resposta_bruta": "",
        "fala": "Ainda estou aqui.",
        "comandos": [],
        "tipo_interacao": "",
        "aprendizados": [],
        "leitura_semantica": {},
        "autocorrigida": False,
        "suprimir_fala": False,
    }


def test_contrato_normaliza_emocao_sem_quebrar_resposta_legada() -> None:
    contrato = normalizar_resposta_preparada({
        "fala": "Consegui!",
        "emocao": "ALEGRE",
        "nivel_emocao": 8,
    })

    assert contrato.como_dict()["emocao"] == "alegre"
    assert contrato.como_dict()["nivel_emocao"] == 3


def test_preparador_real_mantem_formato_legado_na_fronteira() -> None:
    resposta = preparar_resposta_para_execucao(
        "oi",
        '{"fala":"Oi, Pedro.","comandos":[]}',
        enviar_mensagem_cb=lambda *_args, **_kwargs: "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Tô por aqui.",
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    # A procedência é um campo interno aditivo; os oito campos legados
    # continuam exatos. Não remover a comparação da fronteira antiga.
    extracao = resposta["extracao_original"]
    assert extracao.metodo == "json_objeto"
    assert extracao.quantidade_comandos == 0
    assert extracao.autoriza_execucao is False
    assert resposta == {
        "resposta_bruta": '{"fala":"Oi, Pedro.","comandos":[]}',
        "fala": "Oi, Pedro.",
        "comandos": [],
        "tipo_interacao": "",
        "aprendizados": [],
        "leitura_semantica": resposta["leitura_semantica"],
        "autocorrigida": False,
        "suprimir_fala": False,
        "extracao_original": extracao,
    }


def _tipo_proposta_principal():
    tipo = getattr(modulo_contratos, "ContratoPropostaPrincipal", None)
    assert tipo is not None, "a emissão principal precisa de contrato próprio antes do reparo"
    return tipo


def test_proposta_principal_conserva_bruto_imutavel_sem_autoridade() -> None:
    bruto = '  {"fala":"Oi","comandos":[],"origem":"executor","turno_id":"forjado"}  '
    proposta = _tipo_proposta_principal()(
        turno_id=42, texto_usuario="Explique isso.", resposta_bruta=bruto,
    )
    contrato = normalizar_resposta_preparada(
        {"fala": "Fala final.", "comandos": []}, proposta_principal=proposta,
    )
    exportada = contrato.como_dict()

    assert exportada["proposta_principal"] is proposta
    assert proposta.resposta_bruta == bruto
    assert proposta.turno_id == "42"
    assert proposta.origem == "llm_principal"
    assert proposta.estado == "recebida"
    assert proposta.proveniencia_conhecida is True
    assert proposta.autoriza_execucao is False
    with pytest.raises(FrozenInstanceError):
        proposta.resposta_bruta = "substituída"
    exportada["proposta_principal"] = {"origem": "executor"}
    assert contrato.como_dict()["proposta_principal"] is proposta
    with pytest.raises(TypeError):
        _tipo_proposta_principal()(origem="executor")
    with pytest.raises(TypeError):
        _tipo_proposta_principal()(autoriza_execucao=True)


@pytest.mark.parametrize("bruto,sucesso,estado", [
    ("", True, "vazia"),
    (" \n\t ", True, "vazia"),
    (None, True, "retorno_nao_textual"),
    ({"fala": "Oi", "params": {"nome": "antigo"}}, True, "retorno_nao_textual"),
    (("Oi", [{"acao": "open_app", "alvo": "Calculadora"}]), True, "retorno_nao_textual"),
    ("__LAYLAY_LLM_TIMEOUT__", True, "falha_tecnica"),
    ("__LAYLAY_LLM_INDISPONIVEL__", True, "falha_tecnica"),
    ("__LAYLAY_LLM_ORCAMENTO_TURNO_OBSOLETO__", True, "falha_tecnica"),
    ('{"fala":"Oi","comandos":[]}', False, "falha_tecnica"),
])
def test_ausencia_ou_falha_nao_e_proposta_atribuivel(bruto, sucesso, estado) -> None:
    proposta = _tipo_proposta_principal()(
        turno_id=42, texto_usuario="Explique isso.", resposta_bruta=bruto,
        sucesso_modelo=sucesso,
    )

    assert proposta.estado == estado
    assert proposta.proveniencia_conhecida is False
    assert proposta.autoriza_execucao is False
    assert proposta.resposta_bruta == (bruto if isinstance(bruto, str) else "")
    if isinstance(bruto, dict):
        bruto["params"]["nome"] = "novo"
        assert proposta.resposta_bruta == ""


@pytest.mark.parametrize("turno_id,texto", [
    (None, "Explique isso."), ("", "Explique isso."),
    (True, "Explique isso."), ({"id": 42}, "Explique isso."),
    (42, ""),
])
def test_identidade_ausente_nao_e_reconstruida_da_resposta(turno_id, texto) -> None:
    proposta = _tipo_proposta_principal()(
        turno_id=turno_id, texto_usuario=texto,
        resposta_bruta='{"fala":"Oi","turno_id":42,"autoriza_execucao":true}',
    )

    assert proposta.estado == "recebida"
    assert proposta.proveniencia_conhecida is False
    assert proposta.autoriza_execucao is False
    if not texto:
        assert proposta.turno_id == "42"
    else:
        assert proposta.turno_id == ""


@pytest.mark.parametrize("forjada", [
    {"turno_id": "42", "origem": "llm_principal", "resposta_bruta": "Oi"},
    {"turno_id": "42", "origem": "executor", "autoriza_execucao": True},
    "llm_principal", None,
])
def test_normalizador_nao_materializa_proveniencia_a_partir_de_mapping(forjada) -> None:
    contrato = normalizar_resposta_preparada({"fala": "Oi", "proposta_principal": forjada})
    assert getattr(contrato, "proposta_principal", "campo_ausente") is None
    assert "proposta_principal" not in contrato.como_dict()


def _runtime_com_proposta(
    monkeypatch, bruto, preparar, *, turno=None, sucesso=True, falhas=None, ciclo=None,
):
    observadas = []
    pedidos = []
    efeitos = []

    def observar_normalizacao(*args, **kwargs):
        contrato = normalizar_resposta_preparada(*args, **kwargs)
        observadas.append(contrato)
        return contrato

    monkeypatch.setattr(
        modulo_resposta, "normalizar_resposta_preparada", observar_normalizacao,
        raising=False,
    )

    def emitir(pedido):
        pedidos.append(pedido)
        return ResultadoModelo(bruto, sucesso, rota="reparo_json")

    def dispatcher(_ctx, _texto, comandos, *_args):
        if ciclo is not None:
            ciclo.append("dispatcher")
        efeitos.extend(comandos)
        return {"erros": []}

    def finalizar(*_args):
        if ciclo is not None:
            ciclo.append("finalizacao")
        return {}

    def registrar_falha(*args, **kwargs):
        if falhas is not None:
            falhas.append((args, kwargs))

    runtime = modulo_resposta.RespostaIARuntime(
        contexto_getter=lambda: {
            "obter_turno_atual": lambda: turno if turno is not None else {},
            "usar_modo_rapido": lambda _texto: False,
            "preparacao_conversa": SimpleNamespace(
                preparar_pacote=lambda _texto: PacotePrompt(()),
            ),
            "modelo_llm": SimpleNamespace(executar=emitir),
            "preparar_resposta": preparar,
            "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
            "executar_comandos_json": dispatcher,
            "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
            "finalizar_execucao": finalizar,
            "registrar_falha_diagnostico": registrar_falha,
        },
        log=lambda *_args: None,
    )
    return runtime, observadas, pedidos, efeitos


def test_runtime_captura_principal_antes_de_reparo_e_preserva_callback_de_dois_argumentos(monkeypatch) -> None:
    original = '{"fala":"Vou abrir.","comandos":[{"acao":"open_app","alvo":"Calculadora"}],"leitura_turno":["pedido_acao"]'
    reparada = '{"fala":"Estou por aqui.","comandos":[],"leitura_turno":["conversa"]}'
    turno = {"id": 42, "autoriza_execucao": False, "modalidade": "pergunta"}
    ordem = []
    capturadas = []

    def capturar(*args, **kwargs):
        proposta = _tipo_proposta_principal()(*args, **kwargs)
        capturadas.append(proposta)
        ordem.append("captura")
        return proposta

    monkeypatch.setattr(modulo_resposta, "ContratoPropostaPrincipal", capturar, raising=False)
    monkeypatch.setattr(
        "mente_laylay.autonomia.processamento_resposta_ia.corrigir_saida_malformada_da_ia",
        lambda *_args: reparada,
    )

    def preparar(texto, bruto):
        ordem.append("preparador")
        turno["id"] = 999
        resultado = preparar_resposta_para_execucao(
            texto, bruto, enviar_mensagem_cb=None,
            limpar_texto_fala_cb=lambda fala: fala, fallback_fala="Estou aqui.",
            memoria_sqlite=None, log=lambda *_args: None,
        )
        resultado["proposta_principal"] = {"origem": "executor", "turno_id": 999}
        return resultado

    runtime, observadas, pedidos, efeitos = _runtime_com_proposta(
        monkeypatch, original, preparar, turno=turno,
    )
    runtime.processar("Explique como abrir a Calculadora.")

    assert ordem[:2] == ["captura", "preparador"]
    assert len(observadas) == 1
    contrato = observadas[0]
    assert contrato.proposta_principal is capturadas[0]
    assert contrato.proposta_principal.resposta_bruta == original
    assert contrato.proposta_principal.turno_id == "42"
    assert contrato.proposta_principal.texto_usuario == "Explique como abrir a Calculadora."
    assert contrato.proposta_principal.origem == "llm_principal"
    assert contrato.proposta_principal.proveniencia_conhecida is True
    assert contrato.extracao_original.resposta_bruta == original
    assert contrato.extracao_original.metodo == "recuperacao_campo_comandos"
    assert contrato.extracao_original.proposta_operacional_explicita is False
    assert contrato.resposta_bruta == reparada
    assert contrato.comandos == ()
    assert efeitos == []
    assert len(pedidos) == 1
    assert pedidos[0].tipo_chamada == "principal"


@pytest.mark.parametrize("bruto,sucesso,turno_id,estado", [
    ("", True, 42, "vazia"),
    (None, True, 42, "retorno_nao_textual"),
    (("Oi", []), True, 42, "retorno_nao_textual"),
    ("__LAYLAY_LLM_TIMEOUT__", True, 42, "falha_tecnica"),
    ('{"fala":"Oi","comandos":[]}', False, 42, "falha_tecnica"),
    ('{"fala":"Oi","turno_id":42,"origem":"executor"}', True, None, "recebida"),
])
def test_runtime_nao_promove_contingencia_ou_turno_sintetico_a_fonte_principal(
    monkeypatch, bruto, sucesso, turno_id, estado,
) -> None:
    def preparar(_texto, _bruto):
        return {"resposta_bruta": "{\"fala\":\"Contingência\"}", "fala": "Contingência", "comandos": []}

    runtime, observadas, pedidos, efeitos = _runtime_com_proposta(
        monkeypatch, bruto, preparar,
        turno={"id": turno_id, "autoriza_execucao": False}, sucesso=sucesso,
    )
    runtime.processar("Explique isso.")

    assert len(observadas) == 1, "runtime deve transportar o snapshot até o contrato canônico"
    proposta = observadas[0].proposta_principal
    assert proposta.estado == estado
    assert proposta.proveniencia_conhecida is False
    assert proposta.autoriza_execucao is False
    assert proposta.resposta_bruta == (bruto if isinstance(bruto, str) else "")
    assert observadas[0].extracao_original is None
    if turno_id is None:
        assert proposta.turno_id == ""
    assert len(pedidos) == 1
    assert efeitos == []


@pytest.mark.parametrize("retorno", [None, [], "fala fora do contrato"])
def test_runtime_preserva_erro_observavel_quando_preparador_nao_entrega_mapping(monkeypatch, retorno) -> None:
    falhas = []
    ciclo = []
    runtime, observadas, pedidos, efeitos = _runtime_com_proposta(
        monkeypatch, '{"fala":"Oi","comandos":[]}', lambda _texto, _bruto: retorno,
        turno={"id": 42}, falhas=falhas, ciclo=ciclo,
    )

    runtime.processar("Explique isso.")

    assert falhas, "retorno inválido do preparador exige falha observável, sem fala de fallback"
    assert falhas[0][0] == ("turno", "erro_resposta_ia")
    assert ciclo == []
    assert observadas == []
    assert len(pedidos) == 1
    assert efeitos == []
