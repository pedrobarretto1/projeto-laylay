from __future__ import annotations

import pytest

from mente_laylay.integracao.registro_arquivos import registrar_arquivos_leitura


class _ArquivosFake:
    def __init__(self) -> None:
        self.pesquisas = []
        self.abertos = []

    def pesquisar(self, consulta, **opcoes):
        self.pesquisas.append((consulta, opcoes))
        return {
            "consulta": consulta,
            "resultados": [
                {
                    "caminho": "C:/projeto/configuracao.env",
                    "nome": "configuracao.env",
                    "trecho": "GMAIL_APP_PASSWORD=segredo",
                    "sensivel": True,
                    "conteudo": "GMAIL_APP_PASSWORD=segredo",
                    "conteudo_norm": "gmail app password segredo",
                    "raiz": "C:/projeto",
                    "credenciais": {"token": "segredo"},
                    "local_key": "segredo",
                },
                {
                    "caminho": "C:/projeto/controlador.py",
                    "nome": "controlador.py",
                    "trecho": "def controlar_lampada(): ...",
                    "sensivel": False,
                },
            ],
        }

    def abrir(self, caminho):
        self.abertos.append(caminho)
        return True

    def diagnostico(self):
        return {
            "arquivos_indexados": 12,
            "pesquisas": 3,
            "somente_leitura": True,
            "envia_conteudo_externo": False,
            "projeto_raiz": "C:/segredo/projeto",
            "credenciais": "nunca expor",
        }


def test_registro_de_arquivos_expoe_apenas_operacoes_de_leitura() -> None:
    servico = _ArquivosFake()
    registro = registrar_arquivos_leitura(servico)

    retorno = registro.pesquisar(
        "controla a lâmpada", limite=3, somente_projeto=True
    )

    assert servico.pesquisas == [(
        "controla a lâmpada",
        {"limite": 3, "forcar_indice": False, "somente_projeto": True},
    )]
    assert retorno["resultados"][0]["trecho"] == ""
    assert "conteudo" not in retorno["resultados"][0]
    assert "conteudo_norm" not in retorno["resultados"][0]
    assert "raiz" not in retorno["resultados"][0]
    assert "credenciais" not in retorno["resultados"][0]
    assert "local_key" not in retorno["resultados"][0]
    assert retorno["resultados"][1]["trecho"].startswith("def controlar")
    assert not hasattr(registro, "escrever")
    assert not hasattr(registro, "criar_arquivo")
    assert not hasattr(registro, "apagar")


def test_registro_de_arquivos_abre_por_delegacao_e_sanitiza_diagnostico() -> None:
    servico = _ArquivosFake()
    registro = registrar_arquivos_leitura(servico)

    assert registro.abrir("C:/projeto/controlador.py") is True
    assert servico.abertos == ["C:/projeto/controlador.py"]
    assert registro.diagnostico() == {
        "arquivos_indexados": 12,
        "pesquisas": 3,
        "somente_leitura": True,
        "envia_conteudo_externo": False,
    }
    assert "segredo" not in repr(registro)


def test_registro_de_arquivos_rejeita_servico_incompleto_na_composicao() -> None:
    class _Incompleto:
        def pesquisar(self, _consulta, **_opcoes):
            return {"resultados": []}

    with pytest.raises(RuntimeError, match="operações ausentes: abrir, diagnostico"):
        registrar_arquivos_leitura(_Incompleto())
