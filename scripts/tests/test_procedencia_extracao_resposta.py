from __future__ import annotations

from dataclasses import FrozenInstanceError
from copy import deepcopy
import json

import pytest

from mente_laylay.autonomia import higiene_resposta_ia as higiene
from mente_laylay.autonomia import processamento_resposta_ia as processamento
from mente_laylay.autonomia import dispatcher_comandos_json as dispatcher
from mente_laylay.cognicao.contratos_turno import (
    ContratoPropostaPrincipal, ExtracaoRespostaIA, SnapshotComandoIA, normalizar_resposta_preparada,
)


def _decodificar(bruto, **kwargs):
    decodificar = getattr(higiene, "decodificar_resposta_da_ia", None)
    assert callable(decodificar), "o decoder canônico precisa preservar a procedência da extração"
    return decodificar(bruto, **kwargs)


COMANDO = {"acao": "open_app", "alvo": "Calculadora"}
EXPLICACAO = "Eu poderia usar open_app: Calculadora"


@pytest.mark.parametrize("bruto,metodo,quantidade,explicita", [
    (json.dumps({"fala": "Vou abrir.", "comandos": [COMANDO]}), "json_objeto", 1, True),
    (json.dumps({"fala": EXPLICACAO, "comandos": []}), "json_objeto", 0, False),
    (json.dumps({"fala": "Entendi."}), "json_objeto", 0, False),
    (EXPLICACAO, "recuperacao_padrao_textual", 1, False),
    ('{"fala":"Vou abrir.","comandos":[{"acao":"open_app","alvo":"Calculadora"}]',
     "recuperacao_campo_comandos", 1, False),
    ("fala:'Vou abrir.' comandos:[{'acao':'open_app','alvo':'Calculadora'}]",
     "recuperacao_campo_comandos", 1, False),
    ('{"fala":"Oi.', "recuperacao_fala", 0, False),
    ('{"fala":', "json_invalido_bloqueado", 0, False),
    ("Tudo bem por aqui.", "texto_livre", 0, False),
    (("Vou abrir.", [COMANDO]), "tupla_legada", 1, False),
    (json.dumps(json.dumps({"fala": "Vou abrir.", "comandos": [COMANDO]})),
     "json_envelope_textual", 1, False),
    (r'{\"fala\":\"Vou abrir.\",\"comandos\":[{\"acao\":\"open_app\",\"alvo\":\"Calculadora\"}]}',
     "json_envelope_textual", 1, False),
    ('```json\n' + json.dumps({"fala": "Vou abrir.", "comandos": [COMANDO]}) + '\n```',
     "json_objeto", 1, True),
])
def test_decoder_preserva_caminho_sem_promover_recuperacao_a_proposta_explicita(
    bruto, metodo, quantidade, explicita,
) -> None:
    legado = higiene.limpar_resposta_da_ia(bruto)
    resultado = _decodificar(bruto)
    assert resultado.como_legado() == legado
    extracao = resultado.extracao
    assert extracao.metodo == metodo
    assert extracao.quantidade_comandos == quantidade
    assert extracao.proposta_operacional_explicita is explicita
    assert extracao.resposta_bruta == (bruto if isinstance(bruto, str) else None)
    assert extracao.origem == "decoder_canonico"
    assert extracao.autoriza_execucao is False
    assert "Calculadora" not in repr(extracao)
    with pytest.raises(FrozenInstanceError):
        extracao.metodo = "json_objeto"


@pytest.mark.parametrize("campo", ["intent", "acao", "action"])
def test_none_e_filtrado_antes_de_contar_propostas(campo) -> None:
    bruto = json.dumps({"fala": "Entendi.", "comandos": [{campo: " NONE "}]})
    resultado = _decodificar(bruto)
    assert resultado.como_legado()[1] == []
    assert resultado.extracao.quantidade_comandos == 0
    assert resultado.extracao.proposta_operacional_explicita is False


def test_metadados_do_modelo_nao_definem_procedencia_ou_autoridade() -> None:
    bruto = json.dumps({
        "fala": EXPLICACAO, "comandos": [],
        "extracao_original": {"metodo": "json_objeto", "quantidade_comandos": 1},
        "origem": "executor", "autoriza_execucao": True,
    })
    extracao = _decodificar(bruto).extracao
    assert extracao.quantidade_comandos == 0
    assert extracao.proposta_operacional_explicita is False
    assert extracao.origem == "decoder_canonico"
    assert extracao.autoriza_execucao is False


@pytest.mark.parametrize("metodo", [[], {}, None])
def test_metodo_interno_malformado_preserva_ausencia_de_evidencia(metodo) -> None:
    extracao = ExtracaoRespostaIA(
        resposta_bruta='{"comandos":[{}]}', metodo=metodo,
        campo_comandos_presente=True, quantidade_comandos=1,
    )
    assert extracao.metodo == "desconhecido"
    assert extracao.proposta_operacional_explicita is False
    assert extracao.autoriza_execucao is False


@pytest.mark.parametrize("bruto", [None, "", "__LAYLAY_LLM_TIMEOUT__"])
def test_fonte_ausente_ou_tecnica_nao_e_proposta_operacional(bruto) -> None:
    extracao = _decodificar(bruto).extracao
    assert extracao.proposta_operacional_explicita is False
    assert extracao.autoriza_execucao is False


def _preparar(bruto, **kwargs):
    return processamento.preparar_resposta_para_execucao(
        "abra a Calculadora", bruto,
        enviar_mensagem_cb=None, limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="Estou aqui.", memoria_sqlite=None,
        log=lambda *_args: None, **kwargs,
    )


def test_preparador_conserva_decodificacao_original_antes_de_substituir_por_reparo(monkeypatch) -> None:
    original = '{"fala":"Vou abrir.","comandos":[{"acao":"open_app","alvo":"Calculadora"}]'
    reparada = '{"fala":"Vou abrir a Calculadora.","comandos":[]}'
    decodificar = getattr(processamento, "decodificar_resposta_da_ia", None)
    assert callable(decodificar), "a composição do preparador deve usar o decoder com procedência"
    ordem = []

    def observar(bruto, **kwargs):
        resultado = decodificar(bruto, **kwargs)
        ordem.append(bruto)
        return resultado

    def reparar(*_args):
        assert ordem == [original], "a primeira decodificação precisa preceder o reparo"
        return reparada

    monkeypatch.setattr(processamento, "decodificar_resposta_da_ia", observar)
    monkeypatch.setattr(processamento, "corrigir_saida_malformada_da_ia", reparar)
    preparada = _preparar(original)
    extracao = preparada.get("extracao_original")
    assert extracao is not None
    assert extracao.resposta_bruta == original
    assert extracao.metodo == "recuperacao_campo_comandos"
    assert extracao.proposta_operacional_explicita is False
    assert preparada["resposta_bruta"] == reparada
    assert preparada["comandos"] == []
    assert ordem.count(original) == 1


def test_preparador_reusa_resultado_original_sem_segunda_decodificacao(monkeypatch) -> None:
    bruto = json.dumps({"fala": "Vou abrir.", "comandos": [COMANDO]})
    decodificar = getattr(processamento, "decodificar_resposta_da_ia", None)
    assert callable(decodificar)
    entradas = []

    def observar(texto, **kwargs):
        entradas.append(texto)
        return decodificar(texto, **kwargs)

    monkeypatch.setattr(processamento, "decodificar_resposta_da_ia", observar)
    preparada = _preparar(bruto)
    assert entradas == [bruto]
    assert preparada["comandos"] == [COMANDO]
    assert preparada["extracao_original"].proposta_operacional_explicita is True


@pytest.mark.parametrize("forjada", [
    {"metodo": "json_objeto", "resposta_bruta": "Oi", "quantidade_comandos": 1},
    "json_objeto", None,
])
def test_normalizador_nao_materializa_extracao_de_mapping(forjada) -> None:
    contrato = normalizar_resposta_preparada({"fala": "Oi", "extracao_original": forjada})
    assert getattr(contrato, "extracao_original", "ausente") is None
    assert "extracao_original" not in contrato.como_dict()


@pytest.mark.parametrize("vinculada", [True, False])
def test_transporte_vincula_extracao_a_string_principal_exata(vinculada) -> None:
    original = json.dumps({"fala": "Vou abrir.", "comandos": [COMANDO]})
    extracao = _decodificar(original if vinculada else '{"fala":"Outra saída","comandos":[]}').extracao
    proposta = ContratoPropostaPrincipal(turno_id=42, texto_usuario="abra a Calculadora", resposta_bruta=original)
    contrato = normalizar_resposta_preparada({"fala": "Fala final", "extracao_original": extracao}, proposta_principal=proposta)
    assert contrato.extracao_original is (extracao if vinculada else None)
    assert contrato.proposta_principal is proposta


def _copiar_snapshots(extracao, campo="comandos_originais"):
    snapshots = getattr(extracao, campo, None)
    assert snapshots is not None, f"a extração deve conservar {campo} antes do reparo"
    assert isinstance(snapshots, tuple)
    return [item.como_dict() if item is not None else None for item in snapshots]


@pytest.mark.parametrize("intent", ["APP_OPEN", "PLAYLIST_CREATE", "IOT_CONTROL"])
def test_snapshot_conserva_parametros_originais_sem_alias_aninhado(intent) -> None:
    comando = {
        "intent": intent,
        "params": {"alvo": "ação ç", "target": "pc_b", "itens": [True, None, 2, {"valor": 1.5}]},
    }
    original = deepcopy(comando)
    resultado = _decodificar(json.dumps({"fala": "Entendi.", "comandos": [comando]}))
    assert _copiar_snapshots(resultado.extracao) == [original]
    resultado.comandos[0]["params"]["itens"][-1]["valor"] = 99
    copia = _copiar_snapshots(resultado.extracao)
    copia[0]["params"]["itens"].append("modificada")
    assert _copiar_snapshots(resultado.extracao) == [original]
    assert _copiar_snapshots(deepcopy(resultado.extracao)) == [original]
    assert resultado.extracao.candidatos_preservados is True
    assert resultado.extracao.autoriza_execucao is False
    assert "ação ç" not in repr(resultado.extracao)
    assert "ação ç" not in repr(resultado.extracao.comandos_originais)
    with pytest.raises(FrozenInstanceError):
        resultado.extracao.comandos_originais[0].autoriza_execucao = True


def test_snapshot_da_tupla_legada_e_isolado_sem_promover_proposta_explicita() -> None:
    comando = {"acao": "open_app", "alvo": "Calculadora", "contexto": {"itens": [1]}}
    original = deepcopy(comando)
    resultado = _decodificar(("Entendi.", [comando]))
    assert _copiar_snapshots(resultado.extracao) == [original]
    comando["contexto"]["itens"].append(2)
    assert _copiar_snapshots(resultado.extracao) == [original]
    assert resultado.extracao.proposta_operacional_explicita is False


def test_snapshot_precede_callback_de_limpeza_da_fala() -> None:
    comando = {"acao": "open_app", "alvo": "Calculadora"}
    original = deepcopy(comando)

    def limpar(fala):
        comando["alvo"] = "Outro aplicativo"
        return fala

    resultado = _decodificar(("Entendi.", [comando]), limpar_texto_fala_cb=limpar)
    assert _copiar_snapshots(resultado.extracao) == [original]


@pytest.mark.parametrize("comando,intent", [
    ({"acao": "criar_playlist", "alvo": "foco"}, "PLAYLIST_CREATE"),
    ({"acao": "open_app", "alvo": "Calculadora"}, "APP_OPEN"),
    ({"acao": "ligar", "alvo": "lampada_quarto"}, "IOT_CONTROL"),
    ({"acao": "deletar_item", "alvo": "foco.txt"}, "DELETE_ITEM"),
    ({"acao": "volume_set", "nivel": 42}, "VOLUME"),
])
def test_visao_do_alias_original_reusa_adaptador_canonico(comando, intent, monkeypatch) -> None:
    adaptar = dispatcher.adaptar_acao_json_para_intencao
    esperado = adaptar(deepcopy(comando))
    assert esperado["intent"] == intent
    chamadas = []

    def observar(dados, *args, **kwargs):
        chamadas.append(deepcopy(dados))
        return adaptar(dados, *args, **kwargs)

    monkeypatch.setattr(dispatcher, "adaptar_acao_json_para_intencao", observar)
    resultado = _decodificar(json.dumps({"fala": "Entendi.", "comandos": [comando]}))
    assert _copiar_snapshots(resultado.extracao) == [comando]
    assert _copiar_snapshots(resultado.extracao, "comandos_normalizados") == [esperado]
    assert chamadas == [comando]
    assert resultado.comandos == [comando], "a visão de evidência não altera a lista executável"
    assert resultado.extracao.normalizacao_completa is True
    assert resultado.extracao.autoriza_execucao is False


@pytest.mark.parametrize("comando", [
    {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora", "target": "pc_b", "extra": [1]}},
    {"intent": "PLAYLIST_CREATE", "params": {"nome_playlist": "foco", "target": "pc_b"}},
    {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto", "extra": {"v": 2}}},
])
def test_forma_canonica_preserva_params_sem_passar_pelo_adaptador_flat(comando, monkeypatch) -> None:
    def proibido(*_args, **_kwargs):
        pytest.fail("o adaptador flat não interpreta params de uma intent canônica")

    monkeypatch.setattr(dispatcher, "adaptar_acao_json_para_intencao", proibido)
    resultado = _decodificar(json.dumps({"fala": "Entendi.", "comandos": [comando]}))
    assert _copiar_snapshots(resultado.extracao, "comandos_normalizados") == [comando]
    assert resultado.extracao.normalizacao_completa is True


@pytest.mark.parametrize("comando", [
    {"intent": "APP_OPEN", "acao": "open_app", "alvo": "Calculadora"},
    {"intent": "DELETE_ITEM", "acao": "open_app", "alvo": "Calculadora"},
    {"acao": "acao_desconhecida", "alvo": "foco"},
    {"intent": "INTENT_DESCONHECIDA", "params": {}},
    {"intent": "APP_OPEN", "params": "Calculadora"},
    {"acao": "open_app", "params": {"nome_app": "Calculadora"}},
])
def test_forma_incerta_conserva_original_sem_fabricar_normalizacao(comando) -> None:
    resultado = _decodificar(json.dumps({"fala": "Entendi.", "comandos": [comando]}))
    assert _copiar_snapshots(resultado.extracao) == [comando]
    assert _copiar_snapshots(resultado.extracao, "comandos_normalizados") == [None]
    assert resultado.extracao.candidatos_preservados is True
    assert resultado.extracao.normalizacao_completa is False
    assert resultado.comandos == [comando]


def test_posicao_original_sobrevive_a_candidato_nao_normalizavel_e_none() -> None:
    comandos = [{"acao": "acao_desconhecida"}, {"intent": "NONE"}, COMANDO]
    resultado = _decodificar(json.dumps({"fala": "Entendi.", "comandos": comandos}))
    assert _copiar_snapshots(resultado.extracao) == [comandos[0], COMANDO]
    assert _copiar_snapshots(resultado.extracao, "comandos_normalizados") == [
        None, dispatcher.adaptar_acao_json_para_intencao(COMANDO),
    ]
    assert resultado.extracao.quantidade_comandos == 2
    assert resultado.extracao.normalizacao_completa is False


@pytest.mark.parametrize("bruto", [EXPLICACAO, '{"fala":"Entendi.","comandos":[{"acao":"open_app","alvo":"Calculadora"}]'])
def test_snapshot_e_alias_nao_promovem_recuperacao_a_evidencia_explicita(bruto) -> None:
    resultado = _decodificar(bruto)
    assert _copiar_snapshots(resultado.extracao)
    assert resultado.extracao.normalizacao_completa is True
    assert resultado.extracao.proposta_operacional_explicita is False


def test_snapshot_vazio_nao_e_normalizacao_operacional() -> None:
    resultado = _decodificar(json.dumps({"fala": EXPLICACAO, "comandos": []}))
    assert _copiar_snapshots(resultado.extracao) == []
    assert _copiar_snapshots(resultado.extracao, "comandos_normalizados") == []
    assert resultado.extracao.candidatos_preservados is True
    assert resultado.extracao.normalizacao_completa is False
    assert resultado.extracao.proposta_operacional_explicita is False


@pytest.mark.parametrize("valor", [float("nan"), float("inf"), {1, 2}])
def test_payload_sem_snapshot_json_confiavel_nao_vira_evidencia(valor) -> None:
    comando = {"acao": "open_app", "alvo": "Calculadora", "extra": valor}
    resultado = _decodificar(("Entendi.", [comando]))
    assert hasattr(resultado.extracao, "candidatos_preservados")
    assert resultado.extracao.candidatos_preservados is False
    assert resultado.extracao.comandos_originais is None
    assert resultado.extracao.comandos_normalizados is None
    assert resultado.comandos == [comando]


@pytest.mark.parametrize("original", [
    '{"fala":"Entendi.","comandos":[{"acao":"open_app","alvo":"Calculadora"}]}',
    '{"fala":"Entendi.","comandos":[{"acao":"open_app","alvo":"Calculadora"}]',
])
def test_preparador_preserva_snapshot_e_visao_antes_do_reparo(original, monkeypatch) -> None:
    reparada = '{"fala":"Entendi.","comandos":[{"acao":"criar_playlist","alvo":"estudo"}]}'
    monkeypatch.setattr(processamento, "corrigir_saida_malformada_da_ia", lambda *_args: reparada)
    preparada = _preparar(original)
    assert preparada["resposta_bruta"] == reparada
    extracao = preparada["extracao_original"]
    assert extracao.resposta_bruta == original
    assert _copiar_snapshots(extracao) == [COMANDO]
    assert _copiar_snapshots(extracao, "comandos_normalizados") == [dispatcher.adaptar_acao_json_para_intencao(COMANDO)]
    proposta = ContratoPropostaPrincipal(turno_id=42, texto_usuario="abra a Calculadora", resposta_bruta=original)
    contrato = normalizar_resposta_preparada(preparada, proposta_principal=proposta)
    assert contrato.extracao_original is extracao
    assert _copiar_snapshots(contrato.extracao_original) == [COMANDO]


@pytest.mark.parametrize("valor", [(1, 2), {1: "chave convertida"}])
def test_snapshot_nao_converte_tipos_nao_json(valor) -> None:
    with pytest.raises(ValueError):
        SnapshotComandoIA({"extra": valor})


@pytest.mark.parametrize("originais,quantidade,normalizados", [
    ((COMANDO,), 1, (None,)),
    ((SnapshotComandoIA(COMANDO),), 2, (SnapshotComandoIA(COMANDO),)),
    (None, 1, (SnapshotComandoIA(COMANDO),)),
])
def test_metadado_interno_incompleto_nao_materializa_snapshot(originais, quantidade, normalizados) -> None:
    extracao = ExtracaoRespostaIA(
        quantidade_comandos=quantidade, comandos_originais=originais, comandos_normalizados=normalizados,
    )
    assert extracao.comandos_originais is None
    assert extracao.comandos_normalizados is None
    assert extracao.candidatos_preservados is False
    assert extracao.normalizacao_completa is False


def test_erro_na_normalizacao_conserva_snapshot_e_compatibilidade_legada(monkeypatch) -> None:
    def falhar(*_args):
        raise RuntimeError("adaptador indisponível")

    monkeypatch.setattr(higiene, "normalizar_candidato_json_para_intencao", falhar)
    resultado = _decodificar(json.dumps({"fala": "Entendi.", "comandos": [COMANDO]}))
    assert _copiar_snapshots(resultado.extracao) == [COMANDO]
    assert _copiar_snapshots(resultado.extracao, "comandos_normalizados") == [None]
    assert resultado.comandos == [COMANDO]
    assert resultado.extracao.normalizacao_completa is False


def test_visao_canonica_reconsulta_catalogo_compartilhado(monkeypatch) -> None:
    monkeypatch.setattr(dispatcher, "intents_registradas", lambda: frozenset())
    comando = {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}
    resultado = _decodificar(json.dumps({"fala": "Entendi.", "comandos": [comando]}))
    assert _copiar_snapshots(resultado.extracao) == [comando]
    assert _copiar_snapshots(resultado.extracao, "comandos_normalizados") == [None]
    assert resultado.extracao.normalizacao_completa is False
