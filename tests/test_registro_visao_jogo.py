from __future__ import annotations

from pathlib import Path

import pytest

from mente_laylay.integracao.registro_visao_jogo import (
    registrar_visao_jogo_analise,
    registrar_visao_jogo_leitura,
)
from mente_laylay.percepcao.visao_jogo.portas_runtime import (
    criar_visao_jogo_analise_runtime,
    criar_visao_jogo_leitura_runtime,
)


class _Sessoes:
    def perfil(self, _identidade):
        return {"classe": "Monge", "segredo": "não entra no diagnóstico"}


class _Visao:
    habilitado = True
    credencial_disponivel = True

    def __init__(self) -> None:
        self.em_andamento = False
        self.sessoes = _Sessoes()
        self.chamadas: list[tuple] = []
        self.contexto_jogo = lambda: {
            "ativo": True, "titulo": "Path of Exile 2", "processo": "poe2.exe",
        }
        # Estes membros perigosos pertencem ao runtime interno e não podem
        # atravessar os registros públicos.
        self.capturar = lambda _ctx: "IMAGEM_BASE64_PRIVADA"
        self.analisar_imagem = lambda _imagem, _prompt: "rascunho privado"

    def tem_analise_recente(self, max_idade_s=900.0): return max_idade_s > 0
    def observar_texto_usuario(self, texto):
        self.chamadas.append(("observar", texto)); return {"classe": "Monge"}
    def executar(self, params): self.chamadas.append(("executar", params)); return True
    def aplicar_referencia_item(self, texto): self.chamadas.append(("referencia", texto)); return False
    def continuar_analise_recente(self, texto): self.chamadas.append(("continuar", texto)); return False
    def continuar_pendencia(self, texto, pendencia): self.chamadas.append(("pendencia", texto, pendencia)); return False
    def processar_atualizacao_perfil(self, texto): self.chamadas.append(("perfil", texto)); return False


def _registros():
    visao = _Visao()
    leitura = registrar_visao_jogo_leitura(
        criar_visao_jogo_leitura_runtime(visao=visao)
    )
    analise = registrar_visao_jogo_analise(
        criar_visao_jogo_analise_runtime(visao=visao)
    )
    return visao, leitura, analise


def test_composicao_valida_os_dois_contratos() -> None:
    with pytest.raises(RuntimeError, match="leitura"):
        registrar_visao_jogo_leitura(object())
    with pytest.raises(RuntimeError, match="análise"):
        registrar_visao_jogo_analise(object())


def test_leitura_nao_expoe_captura_modelo_ou_autorizacao() -> None:
    visao, leitura, _ = _registros()

    assert leitura.tem_analise_recente() is True
    assert leitura.perfil_atual()["classe"] == "Monge"
    assert visao.chamadas == []
    assert not hasattr(leitura, "capturar")
    assert not hasattr(leitura, "analisar_imagem")
    assert leitura.diagnostico()["captura_persistida"] is False
    assert leitura.diagnostico()["imagem_exposta"] is False
    assert leitura.diagnostico()["autoriza_execucao"] is False


def test_analise_publica_so_operacoes_nomeadas_e_metricas_sanitizadas() -> None:
    visao, _, analise = _registros()

    assert analise.executar({"tipo": "avaliacao_item", "segredo": "local"}) is True
    diagnostico = analise.diagnostico()

    assert visao.chamadas[0][0] == "executar"
    assert diagnostico["solicitacoes"] == 1
    assert diagnostico["aceitas"] == 1
    assert "segredo" not in repr(diagnostico)
    assert not hasattr(analise, "capturar")
    assert not hasattr(analise, "analisar_imagem")
    assert diagnostico["captura_exposta"] is False
    assert diagnostico["prompt_exposto"] is False
    assert diagnostico["autoriza_execucao"] is False


def test_observacao_de_texto_nao_dispara_analise() -> None:
    visao, leitura, _ = _registros()

    observado = leitura.observar_texto_usuario("ainda estou no menu")

    assert observado == {"classe": "Monge"}
    assert visao.chamadas == [("observar", "ainda estou no menu")]
    assert not any(chamada[0] == "executar" for chamada in visao.chamadas)


def test_registros_nao_publicam_o_servico_interno_no_repr() -> None:
    _, leitura, analise = _registros()

    assert "IMAGEM_BASE64_PRIVADA" not in repr(leitura)
    assert "IMAGEM_BASE64_PRIVADA" not in repr(analise)


def test_composicao_principal_nao_republica_runtime_visual_bruto() -> None:
    fonte = (Path(__file__).resolve().parents[1] / "laylay.py").read_text(
        encoding="utf-8"
    )

    assert "_executar_visao_jogo_intent =" not in fonte
    assert not any(
        linha.strip().startswith("_visao_jogo_runtime =")
        for linha in fonte.splitlines()
    )
    assert '"_executar_visao_jogo_intent"' not in fonte
    assert '"_visao_jogo_runtime"' not in fonte
