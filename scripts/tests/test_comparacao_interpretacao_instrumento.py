"""Contratos do instrumento com PortaLLM substituída, não runtime instalado.

Codec e extração são reais. Os callbacks do root mínimo apenas capturam
registro/admissão; nenhum teste representa executor, receipt ou efeito real.
"""
from __future__ import annotations

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mente_laylay.cognicao.saida_interpretacao_principal import (
    criar_contrato_saida_interpretacao_principal,
)
from mente_laylay.integracao.registro_conversa_llm import (
    RegistroModeloLLM,
    ResultadoModelo,
)
from scripts.analises.avaliacao_interpretacao_natural import (
    avaliar_atos,
    avaliar_comandos,
    preparar_mensagens,
)
from scripts.analises.sonda_ordem_interpretacao import _medir_por_ato


TEXTO = "abre o aplicativo Calculadora"
TURNO = {"id": "turno-instrumental", "texto": TEXTO}
COMANDO = {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}


def _envelope() -> dict:
    return {
        "fala": "Vou verificar o pedido.",
        "emocao": "calma",
        "nivel_emocao": 1,
        "tipo_interacao": "conversa",
        "leitura_turno": [{
            "tipo": "pedido_acao",
            "conteudo": TEXTO,
            "interpretacao": {
                "texto_original": TEXTO,
                "operacao": "abrir",
                "tipo_recurso": "app",
                "alvo": "Calculadora",
                "destino": "",
                "condicao": "",
                "parametros": {},
                "referencias": [],
                "dependencias": [],
            },
        }],
        "leitura_emocional": {
            "estado_usuario": "nenhum",
            "intensidade": 0,
            "causa_expressa": "",
            "trecho_evidencia": "",
            "natureza_evidencia": "inferencia",
            "hipotetica": False,
            "alvo": "estado_geral",
            "confianca": 0.0,
        },
        "comandos": [deepcopy(COMANDO)],
        "aprendizados": [],
    }


def _root_minimo(
    resposta: ResultadoModelo | None = None,
    *,
    leitura_registrada: bool = True,
    admitidos: list[dict] | None = None,
) -> tuple[SimpleNamespace, Mock, dict]:
    """Porta substituída e capturadores, não composição ou validador reais."""
    registros = {"leituras": [], "validacoes": []}
    porta = Mock(return_value=resposta or ResultadoModelo("", False))

    def registrar(texto, leitura, proposta):
        registros["leituras"].append((texto, deepcopy(leitura), proposta))
        return leitura_registrada

    def validar(comandos, proposta):
        registros["validacoes"].append((deepcopy(comandos), proposta))
        return {"comandos": deepcopy(admitidos or []), "rejeitados": []}

    servico = SimpleNamespace(executar=porta, diagnostico=lambda: {})
    root = SimpleNamespace(
        _registro_modelo_llm_runtime=RegistroModeloLLM.criar(servico),
        _interpretacao_intencao_runtime=SimpleNamespace(_contexto=lambda: {}),
        _composicao_turno_runtime=SimpleNamespace(registrar_leitura_proposta=registrar),
        _validador_comandos_turno_runtime=SimpleNamespace(validar_proposta=validar),
    )
    return root, porta, registros


def _medir(root, *, modelo_real: bool = True, fonte: dict | None = None, pos=None):
    return _medir_por_ato(root, TEXTO, deepcopy(TURNO), deepcopy(fonte or {}),
        modelo_real=modelo_real, indicios_pos=pos)


def _pacote_pos(*, pos: str = "VERB", lemma: str = "abrir") -> dict:
    return {
        "texto": TEXTO,
        "modelo": "modelo-pos-fixture",
        "versao_modelo": "1.0-fixture",
        "versao_spacy": "fixture-sem-carregamento",
        "pipeline": ["parser"],
        "segundos": 0.125,
        "tokens": [{"texto": "abre", "inicio": 0, "fim": 4,
            "lemma": lemma, "pos": pos, "dep": "ROOT", "cabeca": 0}],
    }


def test_sem_modelo_nao_consulta_porta_nem_registra_ou_valida_proposta():
    root, porta, registros = _root_minimo()
    resultado = _medir(root, modelo_real=False)

    porta.assert_not_called()
    assert registros == {"leituras": [], "validacoes": []}
    assert resultado["estado_geracao"] == "nao_executada"
    assert resultado["semantica_avaliavel"] is False
    assert resultado["propostos"] == resultado["atos"] == resultado["admitidos"] == []
    assert resultado["autoriza_execucao"] is resultado["comprova_efeito"] is False


def test_falha_modelo_nao_vira_semantica_avaliavel_ou_admissao():
    # Nem um JSON estruturalmente válido compensa o sucesso=False da porta.
    bruto = json.dumps(_envelope(), ensure_ascii=False)
    root, porta, registros = _root_minimo(ResultadoModelo(bruto, False))
    resultado = _medir(root)

    porta.assert_called_once()
    assert resultado["estado_geracao"] == "falha_modelo_ou_contrato"
    assert resultado["semantica_avaliavel"] is False
    assert resultado["propostos"] == resultado["admitidos"] == []
    assert registros == {"leituras": [], "validacoes": []}
    assert resultado["autoriza_execucao"] is resultado["comprova_efeito"] is False


def test_json_tipificado_sem_marcador_chega_ao_codec_extrator_e_capturadores():
    dados = _envelope()
    bruto = json.dumps(dados, ensure_ascii=False)
    codec = criar_contrato_saida_interpretacao_principal(TEXTO)
    assert codec.decodificar_json(bruto) == dados
    assert codec.marcador not in bruto
    root, porta, registros = _root_minimo(ResultadoModelo(bruto, True))

    resultado = _medir(root)

    porta.assert_called_once()
    pedido = porta.call_args.args[0]
    assert pedido.com_tools is False
    assert pedido.contrato_saida.nome == codec.nome
    assert pedido.contrato_saida.decodificar_json(bruto) == dados
    assert resultado["estado_geracao"] == "concluida"
    assert resultado["semantica_avaliavel"] is True
    assert resultado["leitura_registrada"] is True
    assert resultado["proposta"] == dados
    assert resultado["propostos"] == [COMANDO]
    assert len(registros["leituras"]) == len(registros["validacoes"]) == 1
    assert registros["leituras"][0][0] == TEXTO
    assert registros["validacoes"][0][0] == [COMANDO]
    assert registros["validacoes"][0][1].texto_usuario == TEXTO
    interpretacao = resultado["atos"][0]["interpretacao"]
    assert interpretacao["operacao"] == "abrir"
    assert interpretacao["alvo"] == "Calculadora"
    assert interpretacao["autoriza_execucao"] is interpretacao["comprova_efeito"] is False
    assert resultado["autoriza_execucao"] is resultado["comprova_efeito"] is False


@pytest.mark.parametrize("bruto", [
    "prefixo " + json.dumps(_envelope(), ensure_ascii=False),
    "[INTERPRETACAO_PRINCIPAL] " + json.dumps(_envelope(), ensure_ascii=False),
    '{"leitura_turno":[]}',
])
def test_formato_recusado_nao_vira_registro_ou_admissao(bruto):
    root, porta, registros = _root_minimo(ResultadoModelo(bruto, True))
    resultado = _medir(root)

    porta.assert_called_once()
    assert resultado["estado_geracao"] == "formato_recusado"
    assert resultado["semantica_avaliavel"] is False
    assert resultado["admitidos"] == []
    assert registros == {"leituras": [], "validacoes": []}


def test_fonte_falsa_recusada_pelo_codec_real_nao_chega_aos_capturadores():
    dados = _envelope()
    dados["leitura_turno"][0]["interpretacao"]["texto_original"] = "abre o Notepad"
    root, _, registros = _root_minimo(ResultadoModelo(json.dumps(dados), True))
    resultado = _medir(root)

    assert resultado["estado_geracao"] == "formato_recusado"
    assert resultado["semantica_avaliavel"] is False
    assert registros == {"leituras": [], "validacoes": []}


def test_metadados_gold_e_identidade_do_caso_nao_entram_nas_mensagens():
    fonte = {
        "id": "CASO_SOMENTE_AVALIACAO_997",
        "familia": "FAMILIA_SOMENTE_AVALIACAO_997",
        "esperados": [{"intent": "GOLD_COMANDO_997"}],
        "atos_esperados": [{"tipo": "GOLD_ATO_997"}],
        "ultima_acao_contrato": {
            "intent": "APP_OPEN", "alvo": "Calculadora", "confirmado": True,
            "id_solicitacao": "OCORRENCIA_NAO_PUBLICA_997",
        },
    }
    antes = deepcopy(fonte)
    root, porta, _ = _root_minimo(ResultadoModelo(json.dumps(_envelope()), True))
    resultado = _medir(root, fonte=fonte)

    mensagens = porta.call_args.args[0].mensagens
    assert list(mensagens) == resultado["mensagens_diagnosticas"]
    payload = json.dumps(mensagens, ensure_ascii=False)
    for marcador in (fonte["id"], fonte["familia"], "GOLD_COMANDO_997", "GOLD_ATO_997",
                     "OCORRENCIA_NAO_PUBLICA_997"):
        assert marcador not in payload
    assert "esperados" not in resultado["contexto_modelo"]
    assert "atos_esperados" not in resultado["contexto_modelo"]
    assert fonte == antes


@pytest.mark.parametrize("registrada", [False, True])
def test_geracao_registro_e_admissao_continuam_fronteiras_distintas(registrada):
    root, _, registros = _root_minimo(
        ResultadoModelo(json.dumps(_envelope()), True), leitura_registrada=registrada)
    resultado = _medir(root)

    assert resultado["estado_geracao"] == "concluida"
    assert resultado["semantica_avaliavel"] is True
    assert resultado["leitura_registrada"] is registrada
    assert resultado["propostos"] == [COMANDO]
    assert resultado["atos"]
    assert resultado["admitidos"] == []
    assert len(registros["validacoes"]) == 1
    assert resultado["autoriza_execucao"] is resultado["comprova_efeito"] is False


def test_formato_valido_nao_vira_acerto_semantico_ou_efeito():
    dados = _envelope()
    dados["comandos"][0]["params"]["nome_app"] = "Notepad"
    root, _, _ = _root_minimo(ResultadoModelo(json.dumps(dados), True))
    resultado = _medir(root)

    assert resultado["estado_geracao"] == "concluida"
    assert resultado["semantica_avaliavel"] is True
    comandos = avaliar_comandos([COMANDO], resultado["propostos"])
    atos = avaliar_atos([{"tipo": "pedido_acao", "interpretacao": {
        "operacao": "abrir", "tipo_recurso": "app", "alvo": "Calculadora"}}], resultado["atos"])
    assert comandos["campos_avaliados_corretos"] is False
    assert atos["campos_avaliados_corretos"] is True
    assert resultado["admitidos"] == []
    for avaliacao in (comandos, atos):
        assert avaliacao["autoriza_execucao"] is avaliacao["comprova_efeito"] is False


def test_captura_de_admissao_nao_e_receipt_nem_prova_de_efeito():
    root, _, registros = _root_minimo(
        ResultadoModelo(json.dumps(_envelope()), True), admitidos=[COMANDO])
    resultado = _medir(root)

    assert resultado["admitidos"] == [COMANDO]
    assert len(registros["validacoes"]) == 1
    assert resultado["autoriza_execucao"] is resultado["comprova_efeito"] is False
    assert "receipt" not in resultado
    assert not hasattr(root, "executar_intencao")


def test_pos_e_ablacao_do_mesmo_texto_contexto_e_schema_sem_gold():
    retorno = ResultadoModelo(json.dumps(_envelope()), True)
    root, porta, _ = _root_minimo(retorno)
    sem_pos = _medir(root)
    verbo = _medir(root, pos=_pacote_pos())
    nominal = _medir(root, pos=_pacote_pos(pos="NOUN", lemma="abertura"))

    pedidos = [chamada.args[0] for chamada in porta.call_args_list]
    assert len(pedidos) == 3
    assert [p.mensagens[1] for p in pedidos] == [{"role": "user", "content": TEXTO}] * 3
    assert all(p.contrato_saida.response_format == pedidos[0].contrato_saida.response_format
               for p in pedidos)
    assert all(p.mensagens[0]["content"].startswith(pedidos[0].mensagens[0]["content"])
               for p in pedidos[1:])
    assert pedidos[1].mensagens[0]["content"] != pedidos[2].mensagens[0]["content"]
    assert sem_pos["contexto_modelo"] == verbo["contexto_modelo"] == nominal["contexto_modelo"]
    assert sem_pos["propostos"] == verbo["propostos"] == nominal["propostos"] == [COMANDO]
    assert sem_pos["pos_segundos_precomputados"] is None
    assert verbo["pos_segundos_precomputados"] == nominal["pos_segundos_precomputados"] == 0.125
    assert verbo["custo_pos_incluido_na_latencia"] is nominal["custo_pos_incluido_na_latencia"] is False
    assert verbo["autoriza_execucao"] is nominal["autoriza_execucao"] is False


def test_pos_de_outra_fala_e_recusado_antes_de_consultar_porta():
    pacote = _pacote_pos()
    pacote["texto"] = "abre o Notepad"
    root, porta, registros = _root_minimo(ResultadoModelo(json.dumps(_envelope()), True))

    with pytest.raises(ValueError, match="literal íntegro"):
        _medir(root, pos=pacote)

    porta.assert_not_called()
    assert registros == {"leituras": [], "validacoes": []}


def test_preparacao_pos_nao_muta_texto_ou_pacote():
    pacote = _pacote_pos()
    antes = deepcopy(pacote)
    contexto = {"procedencia": "fixture_diagnostica_sem_efeito_real"}
    mensagens = preparar_mensagens(TEXTO, contexto, indicios_pos=pacote)

    assert mensagens[-1] == {"role": "user", "content": TEXTO}
    assert pacote == antes
    assert contexto == {"procedencia": "fixture_diagnostica_sem_efeito_real"}
