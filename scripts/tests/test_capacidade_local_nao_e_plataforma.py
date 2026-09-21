"""Documento de controle local não comprova plataforma externa ou efeito."""
from copy import deepcopy
import json

import pytest

from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from tests.test_reparo_preserva_objetivo_turno import plano_explicacao


TEXTO = "como eu poderia aumentar o volume?"
INTRODUCAO = "Para aumentar o volume, você pode dizer 'aumenta o volume'. "
HISTORICA = "Eu vou usar o sistema operacional local para ajustar o volume do seu PC, sem precisar de conexão com outro dispositivo."


@pytest.mark.parametrize("explicacao", [
    HISTORICA,
    "Eu uso o sistema operacional local para controlar o volume do seu PC.",
    "Eu posso usar o sistema operacional local para organizar as janelas do seu PC.",
    "Eu utilizo o sistema operacional local para abrir os programas do seu PC.",
])
def test_implementacao_documentada_nao_exige_fonte_de_plataforma(explicacao):
    plano = plano_explicacao(TEXTO)
    assert plano["contrato_fala"]["documentacao_capacidades"]
    fala = INTRODUCAO + explicacao
    resultado = verificar_fala_turno(fala, plano=plano, origem="ia_final")
    assert "plataforma_sem_evidencia" not in resultado["problemas"]
    assert resultado["fala"] == fala
    assert not plano.get("comandos")
    assert plano["autoriza_execucao"] is False


@pytest.mark.parametrize("mudanca", [
    "sem_documento", "outro_turno", "outra_pergunta", "origem_llm",
    "outra_estrategia", "indisponivel", "somente_remoto", "json_invalido",
])
def test_documento_ausente_incompativel_ou_antigo_nao_libera_fala(mudanca):
    plano = deepcopy(plano_explicacao(TEXTO))
    contrato = plano["contrato_fala"]
    if mudanca == "sem_documento":
        contrato["documentacao_capacidades"] = ""
    elif mudanca == "outro_turno":
        contrato["turno_id"] = "outro"
    elif mudanca == "outra_pergunta":
        contrato["roteiro_concreto"]["ancora_literal"] = "outro assunto"
    elif mudanca == "origem_llm":
        contrato["origem"] = "llm"
    elif mudanca == "outra_estrategia":
        contrato["roteiro_concreto"]["estrategia"] = "resposta_direta"
    elif mudanca == "json_invalido":
        contrato["documentacao_capacidades"] = "documento inválido"
    else:
        docs = json.loads(contrato["documentacao_capacidades"])
        if mudanca == "indisponivel":
            docs[0]["estado"] = "indisponivel"
        else:
            docs[0]["limites_contextuais"] = [r for r in docs[0]["limites_contextuais"] if r["escopo"] != "controle_local"]
        contrato["documentacao_capacidades"] = json.dumps(docs)
    resultado = verificar_fala_turno(INTRODUCAO + HISTORICA, plano=plano)
    assert "plataforma_sem_evidencia" in resultado["problemas"]


@pytest.mark.parametrize("alegacao", [
    "GTA 6 funciona no seu PC.",
    "O jogo funciona no sistema operacional do seu PC.",
    "Eu uso o sistema operacional local para rodar GTA 6 no seu PC.",
    "Eu uso o sistema operacional local para ajustar o volume do seu PC e rodar qualquer jogo no seu PC.",
    "Eu uso o sistema operacional local para ajustar o volume do seu PC, pois ele é compatível com qualquer jogo.",
    "Eu uso o sistema operacional local para ajustar o volume do seu PC, sem precisar de conexão com outro dispositivo. O jogo funciona no PC.",
    "Esse jogo foi anunciado para PS4.",
    "O programa está disponível para Windows.",
])
def test_documentacao_local_nao_fundamenta_compatibilidade_externa(alegacao):
    resultado = verificar_fala_turno(INTRODUCAO + alegacao, plano=plano_explicacao(TEXTO))
    assert "plataforma_sem_evidencia" in resultado["problemas"]


@pytest.mark.parametrize("alegacao", [
    "O arquivo foi salvo.", "O navegador está aberto.",
    "O aparelho pesa 70 kg.", "O filme foi lançado em 2025.",
])
def test_explicacao_nao_prova_estado_efeito_data_ou_medida(alegacao):
    fala = INTRODUCAO + HISTORICA + " " + alegacao
    resultado = verificar_fala_turno(fala, plano=plano_explicacao(TEXTO))
    assert resultado["problemas"]
    assert not resultado["aceita"] or resultado["fala"] != fala
