# P0_REVISAO_INTRA_TURNO_B1_2_1_20260816
from __future__ import annotations

import inspect

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    _iniciar_planejamento_turno,
    alinhar_identidade_plano_revisao,
)
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno


def _plano_para_texto_efetivo(texto_efetivo: str) -> dict:
    turno = classificar_modalidade_turno(
        texto_efetivo,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    return planejar_turno(texto_efetivo, turno=turno, mente={})


def test_plano_preserva_fala_original_sem_reintroduzir_alvo_descartado() -> None:
    original = "Abre o Opera... não, abre a Calculadora."
    revisao = resolver_revisao_intra_turno(original)

    assert revisao["detectada"] is True
    assert revisao["resolvida"] is True
    assert revisao["cancelada"] is False
    efetivo = revisao["texto_operacional_efetivo"]
    assert efetivo == "abre a Calculadora"

    plano_semantico = _plano_para_texto_efetivo(efetivo)
    assert plano_semantico["texto_usuario"] == efetivo

    plano = alinhar_identidade_plano_revisao(
        plano_semantico,
        texto_original=original,
        texto_operacional_efetivo=efetivo,
        revisao_intra_turno=revisao,
    )

    # Identidade/correlação: fala realmente recebida.
    assert plano["texto_usuario"] == original

    # Cognição operacional: somente a proposta final.
    assert plano["texto_operacional_efetivo"] == efetivo
    assert plano["revisao_intra_turno"]["tipo"] == "substituicao_comando"
    assert plano["requer_execucao"] is True

    atos = " ".join(str(item.get("texto") or "") for item in plano["atos"]).casefold()
    assert "calculadora" in atos
    assert "opera" not in atos


def test_plano_de_revisao_musical_guarda_original_e_final_separados() -> None:
    original = "Pausa a música... esquece, continua tocando."
    revisao = resolver_revisao_intra_turno(original)
    efetivo = revisao["texto_operacional_efetivo"]

    plano = alinhar_identidade_plano_revisao(
        {"texto_usuario": efetivo, "requer_execucao": True},
        texto_original=original,
        texto_operacional_efetivo=efetivo,
        revisao_intra_turno=revisao,
    )

    assert plano["texto_usuario"] == original
    assert plano["texto_operacional_efetivo"] == "continua música"
    assert plano["revisao_intra_turno"]["tipo"] == "substituicao_acao"


def test_cancelamento_mantem_identidade_original_e_visao_operacional_vazia() -> None:
    original = "Apaga o arquivo segredo.txt... não apaga."
    revisao = resolver_revisao_intra_turno(original)

    assert revisao["detectada"] is True
    assert revisao["resolvida"] is True
    assert revisao["cancelada"] is True

    plano = alinhar_identidade_plano_revisao(
        {"texto_usuario": original, "requer_execucao": False},
        texto_original=original,
        texto_operacional_efetivo=revisao["texto_operacional_efetivo"],
        revisao_intra_turno=revisao,
    )

    assert plano["texto_usuario"] == original
    assert plano["texto_operacional_efetivo"] == ""
    assert plano["revisao_intra_turno"]["cancelada"] is True
    assert plano["requer_execucao"] is False


def test_turno_sem_revisao_nao_inventa_metadado_de_revisao() -> None:
    original = "Abre a Calculadora."
    plano = alinhar_identidade_plano_revisao(
        {"texto_usuario": original, "dominio": "sistema"},
        texto_original=original,
        texto_operacional_efetivo="",
        revisao_intra_turno={
            "detectada": False,
            "resolvida": False,
            "texto_operacional_efetivo": "",
        },
    )

    assert plano["texto_usuario"] == original
    assert "texto_operacional_efetivo" not in plano
    assert "revisao_intra_turno" not in plano
    assert plano["dominio"] == "sistema"


def test_alinhamento_ocorre_depois_do_planejamento_e_antes_dos_consumidores() -> None:
    fonte = inspect.getsource(_iniciar_planejamento_turno)

    indice_planejamento = fonte.index(
        "plano = ns['_planejar_turno_mente'](texto_cognitivo"
    )
    indice_alinhamento = fonte.index(
        "plano = alinhar_identidade_plano_revisao("
    )
    indice_evidencia = fonte.index(
        "evidencia_habilidades_getter = ns.get('_evidencia_habilidades_turno_mente')"
    )

    assert indice_planejamento < indice_alinhamento < indice_evidencia
    assert "texto_original=texto" in fonte
    assert "texto_operacional_efetivo=texto_efetivo" in fonte
