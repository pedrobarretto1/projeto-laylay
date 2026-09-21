from mente_laylay.memoria_mental.pendencia import (
    criar_pendencia,
    pendencia_ativa,
    registrar_pendencia,
)


def test_pergunta_generica_nao_apaga_oferta_estruturada_do_clipboard() -> None:
    estado = registrar_pendencia(
        {},
        criar_pendencia(
            origem="observador_area_transferencia",
            tipo="oferta_acao",
            dominio="area_transferencia",
            conteudo="Quer que eu investigue?",
            opcoes=[{"rotulo": "aceitar", "acao": "investigar_erro"}],
            intencao="CLIPBOARD_OFFER",
        ),
    )

    estado = registrar_pendencia(
        estado,
        criar_pendencia(
            origem="pergunta_aberta",
            tipo="confirmacao",
            dominio="conversa",
            conteudo="Quer que eu investigue?",
        ),
    )

    ativa = pendencia_ativa(estado)
    assert ativa is not None
    assert ativa["origem"] == "observador_area_transferencia"
    assert ativa["dominio"] == "area_transferencia"
    assert ativa["opcoes"][0]["acao"] == "investigar_erro"


def test_nova_pendencia_estruturada_ainda_pode_substituir_pergunta_social() -> None:
    estado = registrar_pendencia(
        {},
        criar_pendencia(
            origem="pergunta_aberta",
            tipo="bem_estar",
            dominio="conversa",
            conteudo="Tudo bem?",
        ),
    )
    estado = registrar_pendencia(
        estado,
        criar_pendencia(
            origem="observador_area_transferencia",
            tipo="oferta_acao",
            dominio="area_transferencia",
            conteudo="Quer que eu investigue?",
            opcoes=[{"acao": "investigar_erro"}],
            intencao="CLIPBOARD_OFFER",
        ),
    )

    ativa = pendencia_ativa(estado)
    assert ativa is not None
    assert ativa["origem"] == "observador_area_transferencia"
