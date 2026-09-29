"""A API externa so propoe um julgamento offline; nao recebe gabarito."""

import json
import sys

import pytest
import requests

from scripts.analises import sonda_openrouter_fronteira as sonda
from scripts.analises.sonda_avaliador_fronteira_independente import (
    FORMATO,
    preparar_entrada,
)


class Resposta:
    status_code = 200

    def json(self):
        return {
            "model": "outro/modelo",
            "usage": {"prompt_tokens": 30, "completion_tokens": 20},
            "choices": [{"message": {"content": json.dumps({
                "relacao": "sujeito_seguinte",
                "citacao": "o cliente e o gerente chegarem",
            })}}],
        }


def test_chamada_unica_envia_fonte_mas_nao_gabarito_parse_ou_chave_no_corpo():
    chamadas = []

    def enviar(*args, **kwargs):
        chamadas.append((args, kwargs))
        return Resposta()

    casos, _ = sonda.carregar_painel_fronteira(22)
    entrada = preparar_entrada(casos[0])["entrada"]
    proposta, meta = sonda.consultar_openrouter(
        "instrucoes", entrada, FORMATO,
        modelo="outro/modelo", chave="segredo-local", enviar=enviar,
    )
    assert len(chamadas) == 1
    args, kwargs = chamadas[0]
    assert args == (sonda.URL,)
    assert kwargs["headers"] == {
        "Authorization": "Bearer segredo-local",
        "X-OpenRouter-Metadata": "enabled",
    }
    assert kwargs["json"]["model"] == "outro/modelo"
    assert kwargs["json"]["provider"] == {"require_parameters": True}
    assert kwargs["json"]["response_format"]["json_schema"]["schema"] \
        == FORMATO
    corpo = json.dumps(kwargs["json"], ensure_ascii=False)
    assert entrada["fonte"] in corpo
    assert "segredo-local" not in corpo
    assert "gabarito" not in corpo
    assert "pos_" not in corpo
    assert proposta["relacao"] == "sujeito_seguinte"
    assert meta["modelo_recebido"] == "outro/modelo"


def test_amostragem_fixa_so_e_enviada_quando_solicitada():
    chamadas = []

    def enviar(*_args, **kwargs):
        chamadas.append(kwargs["json"])
        return Resposta()

    sonda.consultar_openrouter(
        "s", {}, FORMATO, modelo="outro/modelo", chave="segredo",
        temperatura=0, semente=42, enviar=enviar,
    )
    assert chamadas[0]["temperature"] == 0
    assert chamadas[0]["seed"] == 42
    assert "segredo" not in json.dumps(chamadas[0])

    sonda.consultar_openrouter(
        "s", {}, FORMATO, modelo="outro/modelo", chave="segredo",
        enviar=enviar,
    )
    assert "temperature" not in chamadas[1]
    assert "seed" not in chamadas[1]


def test_sonda_registra_provedor_e_fingerprint_sem_expor_metadados_brutos():
    class RespostaComRota:
        status_code = 200

        def json(self):
            return {
                **Resposta().json(),
                "id": "gen-teste",
                "system_fingerprint": "fp-teste",
                "openrouter_metadata": {
                    "endpoints": {"available": [
                        {"provider": "OpenAI", "selected": True},
                        {"provider": "Outro", "selected": False},
                    ]},
                    "segredo_inesperado": "nao_publicar",
                },
                "choices": [{"finish_reason": "stop", "message": {
                    "content": json.dumps({"relacao": "indeterminado",
                                           "citacao": ""}),
                }}],
            }

    chamadas = []

    def enviar(*_args, **kwargs):
        chamadas.append(kwargs)
        return RespostaComRota()

    _, meta = sonda.consultar_openrouter(
        "s", {}, FORMATO, modelo="outro/modelo", chave="segredo",
        enviar=enviar,
    )
    assert chamadas[0]["headers"]["X-OpenRouter-Metadata"] == "enabled"
    assert meta["id_geracao"] == "gen-teste"
    assert meta["fingerprint_sistema"] == "fp-teste"
    assert meta["provedor_selecionado"] == "OpenAI"
    assert meta["motivo_termino"] == "stop"
    assert "segredo_inesperado" not in json.dumps(meta)


def test_provedor_fixo_na_sonda_nao_permita_fallback_para_outro():
    chamadas = []

    def enviar(*_args, **kwargs):
        chamadas.append(kwargs["json"])
        return Resposta()

    sonda.consultar_openrouter(
        "s", {}, FORMATO, modelo="outro/modelo", chave="segredo",
        provedor="openai", enviar=enviar,
    )
    assert chamadas[0]["provider"] == {
        "require_parameters": True,
        "only": ["openai"],
        "allow_fallbacks": False,
    }


def test_hash_do_pedido_identifica_entrada_igual_sem_incluir_chave():
    def enviar(*_args, **_kwargs):
        return Resposta()

    def medir(entrada):
        return sonda.consultar_openrouter(
            "s", entrada, FORMATO, modelo="outro/modelo",
            chave="segredo-local", temperatura=0, semente=42,
            provedor="openai", enviar=enviar,
        )[1]["sha256_pedido"]

    primeiro = medir({"frase": "uma frase"})
    assert len(primeiro) == 64
    assert primeiro == medir({"frase": "uma frase"})
    assert primeiro != medir({"frase": "outra frase"})
    assert "segredo-local" not in primeiro


def test_erro_http_ou_transporte_nao_expoe_chave_nem_corpo():
    class Erro:
        status_code = 401

        def json(self):
            return {"chave": "segredo-local"}

    with pytest.raises(sonda.ErroConsultaOpenRouter, match="HTTP 401") \
            as capturado:
        sonda.consultar_openrouter(
            "s", {}, FORMATO, modelo="outro/modelo",
            chave="segredo-local", enviar=lambda *_a, **_k: Erro(),
        )
    assert "segredo-local" not in str(capturado.value)

    def timeout(*_args, **_kwargs):
        raise requests.ReadTimeout("segredo-local")

    with pytest.raises(sonda.ErroConsultaOpenRouter, match="ReadTimeout") \
            as capturado:
        sonda.consultar_openrouter(
            "s", {}, FORMATO, modelo="outro/modelo",
            chave="segredo-local", enviar=timeout,
        )
    assert "segredo-local" not in str(capturado.value)


def test_sem_modelo_ou_chave_nao_faz_chamada():
    def proibido(*_args, **_kwargs):
        raise AssertionError("nao deve consultar")

    for modelo, chave in (("", "x"), ("outro/modelo", "")):
        with pytest.raises(ValueError):
            sonda.consultar_openrouter(
                "s", {}, FORMATO, modelo=modelo, chave=chave,
                enviar=proibido,
            )


def test_cli_usa_um_caso_sintetico_e_nao_publica_chave(monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "segredo-local")
    monkeypatch.setattr(sys, "argv", [
        "sonda_openrouter_fronteira", "--modelo", "outro/modelo",
    ])
    chamadas = []

    def consultar(sistema, entrada, formato, *, modelo, chave):
        chamadas.append((sistema, entrada, formato, modelo, chave))
        return ({"relacao": "sujeito_seguinte",
                 "citacao": "o cliente e o gerente chegarem"},
                {"modelo_recebido": "outro/modelo"})

    monkeypatch.setattr(sonda, "consultar_openrouter", consultar)
    sonda.main()
    saida = capsys.readouterr().out
    resultado = json.loads(saida)
    assert len(chamadas) == 1
    assert chamadas[0][4] == "segredo-local"
    assert "segredo-local" not in saida
    assert resultado["painel"] == "v22_diagnostico_nao_holdout"
    assert resultado["resultado"]["estado"] \
        == "julgamento_ancorado_revisao_pendente"
    assert resultado["autoriza_efeito"] is False


def test_cli_reutiliza_credencial_protegida_sem_pedir_input(monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LAYLAY_LLM_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", [
        "sonda_openrouter_fronteira", "--modelo", "outro/modelo",
    ])
    chamadas = []

    def carregar():
        monkeypatch.setenv("OPENROUTER_API_KEY", "credencial-protegida")
        return True

    def consultar(_sistema, _entrada, _formato, *, modelo, chave):
        chamadas.append((modelo, chave))
        return ({"relacao": "indeterminado", "citacao": ""}, {})

    monkeypatch.setattr(sonda, "carregar_segredo_no_ambiente", carregar)
    monkeypatch.setattr(sonda.getpass, "getpass", lambda *_: pytest.fail(
        "nao deve pedir input quando a credencial esta salva",
    ))
    monkeypatch.setattr(sonda, "consultar_openrouter", consultar)
    sonda.main()
    assert chamadas == [("outro/modelo", "credencial-protegida")]
    assert "credencial-protegida" not in capsys.readouterr().out


def test_cli_v23_envia_so_um_caso_novo_sem_gabarito(monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "segredo-local")
    monkeypatch.setattr(sys, "argv", [
        "sonda_openrouter_fronteira", "--modelo", "outro/modelo",
        "--painel", "23", "--caso", "PINTOR_ROLO_PINCEL_CLIENTES",
    ])
    entradas = []

    def consultar(_sistema, entrada, _formato, *, modelo, chave):
        entradas.append(entrada)
        assert modelo == "outro/modelo"
        assert chave == "segredo-local"
        return ({"relacao": "indeterminado", "citacao": ""}, {})

    monkeypatch.setattr(sonda, "consultar_openrouter", consultar)
    sonda.main()
    saida = json.loads(capsys.readouterr().out)
    assert len(entradas) == 1
    assert "o pincel" in entradas[0]["fonte"]
    assert "gabarito" not in str(entradas[0])
    assert saida["caso"] == "PINTOR_ROLO_PINCEL_CLIENTES"
    assert saida["painel"] == "v23_primeira_medicao_parcialmente_invalida"
    assert saida["autoriza_efeito"] is False


def test_cli_viabilidade_faz_duas_consultas_isoladas(monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "segredo-local")
    monkeypatch.setattr(sys, "argv", [
        "sonda_openrouter_fronteira", "--modelo", "outro/modelo",
        "--painel", "25", "--caso", "FERREIRO_MARTELO_ALICATE_APRENDIZ",
        "--contrato", "viabilidade",
    ])
    entradas = []

    def consultar(_sistema, entrada, _formato, *, modelo, chave):
        assert modelo == "outro/modelo"
        assert chave == "segredo-local"
        entradas.append(entrada)
        if len(entradas) == 1:
            resposta = {"viabilidade": "viavel", "motivo": "nenhum",
                        "citacao": ""}
        else:
            resposta = {"viabilidade": "inviavel",
                        "motivo": "concordancia",
                        "citacao": "o alicate e a aprendiz chegar"}
        return resposta, {"modelo_recebido": modelo,
                          "uso": {"cost": 0.0001}}

    monkeypatch.setattr(sonda, "consultar_openrouter", consultar)
    sonda.main()
    saida_texto = capsys.readouterr().out
    saida = json.loads(saida_texto)
    assert len(entradas) == 2
    assert entradas[0] != entradas[1]
    assert all(set(entrada) == {"frase_com_leitura", "trechos_condicoes"}
               for entrada in entradas)
    assert "segredo-local" not in saida_texto
    assert saida["contrato"] == "viabilidade"
    assert saida["numero_consultas"] == 2
    assert len(saida["consultas"]) == 2
    assert saida["custo_total_observado_usd"] == pytest.approx(0.0002)
    assert saida["resultado"]["relacao_proposta"] == "objeto_anterior"
    assert saida["autoriza_efeito"] is False


def test_cli_transmite_provedor_e_amostragem_as_duas_consultas(monkeypatch,
                                                               capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "segredo-local")
    monkeypatch.setattr(sys, "argv", [
        "sonda_openrouter_fronteira", "--modelo", "outro/modelo",
        "--painel", "25", "--caso", "FERREIRO_MARTELO_ALICATE_APRENDIZ",
        "--contrato", "viabilidade", "--provedor", "openai",
        "--temperatura", "0", "--semente", "42",
    ])
    parametros = []

    def consultar(_sistema, _entrada, _formato, *, modelo, chave,
                  provedor, temperatura, semente):
        parametros.append((modelo, chave, provedor, temperatura, semente))
        return {"viabilidade": "incerta", "motivo": "incerteza",
                "citacao": ""}, {}

    monkeypatch.setattr(sonda, "consultar_openrouter", consultar)
    sonda.main()
    saida = json.loads(capsys.readouterr().out)
    assert parametros == [
        ("outro/modelo", "segredo-local", "openai", 0, 42),
        ("outro/modelo", "segredo-local", "openai", 0, 42),
    ]
    assert saida["provedor_solicitado"] == "openai"
    assert saida["numero_consultas"] == 2
    assert saida["aprovado_para_producao"] is False
