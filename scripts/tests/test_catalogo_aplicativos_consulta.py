from __future__ import annotations

from mente_laylay.integracao.catalogo_aplicativos import (
    criar_catalogo_aplicativos_runtime,
)
from mente_laylay.integracao.composicao_entrada_interacao import (
    DEPENDENCIAS_COMANDOS_IMEDIATOS,
    DEPENDENCIAS_CONTEXTO_CHAT,
)
from mente_laylay.integracao.contexto_conversa import (
    montar_contexto_inicio_chat_por_grupos,
)
from mente_laylay.integracao.contexto_execucao_ia import (
    DEPENDENCIAS_EXECUCAO_INTENCAO,
)


def test_catalogo_aceita_alias_suportado_e_qualificador_natural() -> None:
    catalogo = criar_catalogo_aplicativos_runtime(
        apps_map={"steam": "steam", "krita": "krita"},
        nomes_instalados_getter=lambda: (),
    )

    assert catalogo.validar("steam") is True
    assert catalogo.validar("cliente steam") is True
    assert catalogo.validar("editor krita") is True


def test_catalogo_aceita_nome_descoberto_sem_acoplar_parser_ao_appopener() -> None:
    catalogo = criar_catalogo_aplicativos_runtime(
        apps_map={},
        nomes_instalados_getter=lambda: ("Opera GX", "Ferramenta de Captura"),
    )

    assert catalogo.validar("opera gx") is True
    assert catalogo.validar("ferramenta de captura") is True


def test_catalogo_aceita_nome_base_de_app_descoberto_com_qualificador() -> None:
    catalogo = criar_catalogo_aplicativos_runtime(
        apps_map={},
        nomes_instalados_getter=lambda: ("Navegador Opera",),
    )

    assert catalogo.validar("opera") is True


def test_catalogo_aceita_app_observado_aberto_mesmo_se_ainda_nao_for_conhecido() -> None:
    catalogo = criar_catalogo_aplicativos_runtime(
        apps_map={},
        nomes_instalados_getter=lambda: (),
    )

    assert catalogo.validar(
        "aplicativo novo",
        estado={"programa_aberto": True},
    ) is True


def test_catalogo_rejeita_substantivo_fora_do_dominio_e_falha_de_descoberta() -> None:
    def falhar() -> tuple[str, ...]:
        raise RuntimeError("inventário indisponível")

    catalogo = criar_catalogo_aplicativos_runtime(
        apps_map={"opera": "opera"},
        nomes_instalados_getter=falhar,
    )

    assert catalogo.validar("porta") is False
    assert catalogo.validar("arquivo relatório") is False
    assert catalogo.validar("menu do jogo") is False
    assert catalogo.diagnostico()["autoriza_execucao"] is False


def test_validador_chega_a_todos_os_caminhos_reais_da_consulta() -> None:
    validador = lambda _nome, **_kwargs: True

    assert "_validar_alvo_app_consulta" in DEPENDENCIAS_COMANDOS_IMEDIATOS
    assert "_validar_alvo_app_consulta" in DEPENDENCIAS_CONTEXTO_CHAT
    assert "_validar_alvo_app_consulta" in DEPENDENCIAS_EXECUCAO_INTENCAO

    contexto_chat = montar_contexto_inicio_chat_por_grupos(
        execucao={"validar_alvo_app_consulta": validador},
    )
    assert contexto_chat["_validar_alvo_app_consulta"] is validador
