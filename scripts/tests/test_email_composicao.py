"""Composição instalada em subprocesso, com rede/modelo externos controlados."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture(scope="module")
def email_instalado(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("email_instalado")
    processo = subprocess.run([sys.executable, "scripts/analises/sonda_email_v1.py", "--saida", str(pasta)],
        cwd=Path(__file__).resolve().parents[2], env=dict(os.environ, PYTHONIOENCODING="utf-8"),
        capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert processo.returncode == 0, processo.stderr[-4000:]
    return json.loads((pasta / "relatorio.json").read_text(encoding="utf-8"))


def test_composicao_instalada_reutiliza_estado_pendencia_e_owner(email_instalado):
    assert all(email_instalado["instalacao"].values())
    assert email_instalado["somente_leitura_imap"]


def test_pergunta_do_usuario_chega_ao_leitor_e_publica_uma_resposta(email_instalado):
    for caso in email_instalado["casos"]:
        assert caso["comando"]["intent"] == "EMAIL_READ"
        assert caso["comando"]["params"]["modo"] == "conteudo"
        assert caso["tratado"]
        assert caso["status"] == "email_conteudo_lido"
        assert len(caso["falas"]) == len(caso["vozes"]) == 1


def test_consciencia_da_habilidade_informa_limites_e_revisao(email_instalado):
    fala = email_instalado["catalogo"]
    assert "corpo" in fala and "rascunhos locais" in fala and "confirmação" in fala
    assert "várias contas ainda não" in fala


def test_criacao_edicao_revisao_e_confirmacao_passam_pela_rota_instalada(email_instalado):
    casos = email_instalado["operacoes"]
    assert casos[0]["status"] == "rascunho_salvo"
    assert casos[1]["status"] == "rascunho_salvo"
    assert casos[2]["status"] == "aguardando_confirmacao" and casos[2]["pendencia"]
    assert casos[2]["novos_envios"] == 0
    assert casos[3]["novos_envios"] == 0 and casos[3]["pendencia"]
    assert casos[4]["status"] == "email_enviado" and casos[4]["novos_envios"] == 1
    assert casos[5]["novos_envios"] == 0
    assert len(email_instalado["envios_sinteticos"]) == 1


def test_identidade_explicita_e_alvo_inexistente_na_composicao_instalada(email_instalado):
    casos = email_instalado["identidade_rascunhos"]
    assert [c["status"] for c in casos] == ["rascunho_descartado", "rascunho_nao_encontrado", "rascunho_lido"]
    assert all(c["tratado"] and c["novos_envios"] == 0 and not c["pendencia"] for c in casos)
    assert all(c["ativo"] == c["outro_id"] for c in casos)


def test_consulta_manual_satisfaz_aviso_atrasado_na_composicao_instalada(email_instalado):
    r=email_instalado["notificacao_apos_consulta"]
    assert r["agendado_antes"] and r["tratado"] and r["respostas_manuais"]==1
    assert r["repetidos_apos_flush"]==0 and r["pendentes_depois"]==0
    assert not r["repetido_agendado_depois"]
    assert r["novo_agendado"] and len(r["novos_textos"])==1
    assert "Outra mensagem nova" in r["novos_textos"][0]
