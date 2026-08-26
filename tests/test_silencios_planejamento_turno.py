from __future__ import annotations

from mente_laylay.cognicao.orquestrador_turno_runtime import (
    anexar_estado_visual_recente_seguro,
    obter_contexto_jogo_seguro,
    resolver_repeticao_operacional_segura,
)
from mente_laylay.memoria_mental.observabilidade import ObservabilidadeMenteRuntime


class _Quebra:
    def __init__(self, metodo: str) -> None:
        setattr(self, metodo, self._falhar)

    @staticmethod
    def _falhar():
        raise RuntimeError("C:/segredo/do_usuario nao pode aparecer")


def _namespace_observavel() -> tuple[dict, dict]:
    estado: dict = {}

    def obter(chave, padrao):
        return estado.get(chave, padrao)

    def atualizar(**campos):
        estado.update(campos)

    observabilidade = ObservabilidadeMenteRuntime(
        estado_getter=obter,
        estado_setter=atualizar,
    )
    return {"_observabilidade_mente_runtime": observabilidade}, estado


def test_falha_na_repeticao_nao_some_do_diagnostico() -> None:
    ns, estado = _namespace_observavel()
    ns["_resolver_repeticao_ultima_acao"] = lambda _texto: (_ for _ in ()).throw(
        RuntimeError("conteudo privado")
    )

    assert resolver_repeticao_operacional_segura(ns, "tenta de novo") is None

    falha = estado["diagnostico_falhas"][-1]
    assert falha["codigo"] == "falha_resolver_repeticao"
    assert falha["classe"] == "defeito"
    assert falha["impacto"] == "turno"
    assert falha["fallback"] == "conversa_sem_repeticao"
    assert "privado" not in repr(falha)


def test_falha_no_contexto_de_jogo_usa_fallback_e_fica_visivel() -> None:
    ns, estado = _namespace_observavel()
    ns["_modo_jogo_runtime"] = _Quebra("contexto_atual")

    assert obter_contexto_jogo_seguro(ns) == {}

    falha = estado["diagnostico_falhas"][-1]
    assert falha["codigo"] == "falha_contexto_atual"
    assert falha["classe"] == "degradacao"
    assert falha["fallback"] == "turno_sem_contexto_jogo"
    assert "segredo" not in repr(falha)


def test_falha_na_recencia_visual_nao_apaga_o_contexto_do_jogo() -> None:
    ns, estado = _namespace_observavel()
    ns["_registro_visao_jogo_leitura_runtime"] = _Quebra("tem_analise_recente")

    contexto = anexar_estado_visual_recente_seguro(ns, {"ativo": True, "jogo": "Teste"})

    assert contexto == {
        "ativo": True,
        "jogo": "Teste",
        "analise_visual_recente": False,
    }
    falha = estado["diagnostico_falhas"][-1]
    assert falha["codigo"] == "falha_verificar_analise_recente"
    assert falha["impacto"] == "turno"
    assert falha["fallback"] == "turno_sem_memoria_visual_recente"


def test_sondagens_saudaveis_nao_geram_falha() -> None:
    ns, estado = _namespace_observavel()
    ns["_resolver_repeticao_ultima_acao"] = lambda _texto: None
    ns["_modo_jogo_runtime"] = type(
        "ModoJogo", (), {"contexto_atual": lambda self: {"ativo": False}}
    )()
    ns["_registro_visao_jogo_leitura_runtime"] = type(
        "Visao", (), {"tem_analise_recente": lambda self: True}
    )()

    assert resolver_repeticao_operacional_segura(ns, "oi") is None
    contexto = obter_contexto_jogo_seguro(ns)
    assert anexar_estado_visual_recente_seguro(ns, contexto)["analise_visual_recente"] is True
    assert estado.get("diagnostico_falhas", []) == []
