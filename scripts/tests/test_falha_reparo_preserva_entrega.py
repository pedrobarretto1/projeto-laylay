"""A falha observada no reparo não perde a fonte na publicação e revisão final."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal, normalizar_resposta_preparada
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import verificar_fala_turno


def preparar(resposta_reparo="__LAYLAY_LLM_TIMEOUT__"):
    texto = "o que você acha disso?"
    turno = classificar_modalidade_turno(texto)
    plano = {"id": turno["id"], "texto_usuario": texto, "comandos": [], "requer_execucao": False}
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano)
    bruto = json.dumps({"fala": "Estou acompanhando nossa conversa.", "comandos": []})
    resposta = preparar_resposta_para_execucao(texto, bruto,
        enviar_mensagem_cb=lambda *_a, **_kw: resposta_reparo,
        limpar_texto_fala_cb=lambda v: v, fallback_fala="fallback", memoria_sqlite=None,
        contexto_contingencia={"plano_turno_atual": plano},
        contexto_comunicacao={"plano_turno": plano, "mensagens": []}, log=lambda *_a: None)
    proposta = ContratoPropostaPrincipal(turno_id=str(plano["id"]), texto_usuario=texto,
        resposta_bruta=bruto, sucesso_modelo=True)
    return plano, resposta, proposta


def test_falha_de_reparo_com_principal_valida_atravessa_normalizacao_e_revisao():
    plano, resposta, proposta = preparar()
    assert resposta["fala"] == "Minha resposta não ficou pronta dentro do tempo disponível."
    fonte = resposta.get("falha_resposta_observada")
    assert fonte is not None, "primeira divergência: retorno negativo do reparo perdeu sua fonte antes da entrega"
    normalizada = normalizar_resposta_preparada(resposta, proposta_principal=proposta).como_dict()
    assert normalizada.get("falha_resposta_observada") is fonte
    plano["falha_resposta_observada"] = fonte
    r = verificar_fala_turno(resposta["fala"], plano=plano)
    assert r["aceita"] is True and r["problemas"] == []
    assert verificar_fala_turno(resposta["fala"] + " Apaguei o arquivo.", plano=plano).get("conclusao") is None


@pytest.mark.parametrize("mutacao", ["json", "id", "texto", "digest", "sentinela", "comando", "ausente"])
def test_fonte_de_reparo_nao_admite_json_outro_turno_ou_confirmacao_de_efeito(mutacao):
    plano, resposta, proposta = preparar()
    fonte = resposta.get("falha_resposta_observada")
    assert fonte is not None, "a captura de falha deve existir antes de testar sua admissão"
    dados = {**plano, "falha_resposta_observada": fonte}
    if mutacao == "json": dados["falha_resposta_observada"] = asdict(fonte)
    elif mutacao == "id": dados["id"] = "outro"
    elif mutacao == "texto": dados["texto_usuario"] = "outro assunto"
    elif mutacao == "comando": dados["comandos"] = [{"intent": "DELETE_FILE"}]
    elif mutacao == "ausente": dados.pop("falha_resposta_observada")
    elif mutacao == "sentinela": dados["falha_resposta_observada"] = replace(fonte, estado_tecnico="erro arbitrário")
    elif mutacao == "digest":
        normalizada = normalizar_resposta_preparada({**resposta,
            "falha_resposta_observada": replace(fonte, principal_sha256="incorreto")},
            proposta_principal=proposta).como_dict()
        assert normalizada.get("falha_resposta_observada") is None
        return
    assert verificar_fala_turno(resposta["fala"], plano=dados).get("conclusao") is None


def test_reparo_falho_na_conversa_instalada_mantem_causa_e_continua_no_turno_seguinte(tmp_path):
    pasta = tmp_path / "sequencia"
    codigo = ("from pathlib import Path; from scripts.analises.sonda_conversa_continua import coletar; "
        "coletar(Path(__import__('sys').argv[1]),modelo_real=False,falhas_reparo=True,"
        "entradas=('oi laylay, como voce ta?','o que você acha disso?','valeu por conversar comigo'))")
    p = subprocess.run([sys.executable, "-c", codigo, str(pasta)], capture_output=True,
        cwd=Path(__file__).resolve().parents[2], text=True, encoding="utf8", timeout=90)
    assert p.returncode == 0, p.stdout + p.stderr
    r = json.loads((pasta / "conversa.json").read_text(encoding="utf8"))["resultados"]
    assert len(r) == 3 and all(len(t["respostas"]) == 1 and not t["executores_recusados"] for t in r)
    assert r[1]["respostas"] == ["Minha resposta não ficou pronta dentro do tempo disponível."]
    assert r[1]["plano"].get("falha_resposta_observada") is not None
    assert r[2]["plano"].get("falha_resposta_observada") is None


def test_rejeicao_semantica_observada_tambem_preserva_fonte_ate_a_revisao_final():
    plano, resposta, proposta = preparar(json.dumps({"fala": "Estou acompanhando nossa conversa.", "comandos": []}))
    assert resposta["fala"] == "Não consegui formular uma resposta confiável desta vez."
    fonte = normalizar_resposta_preparada(resposta, proposta_principal=proposta).como_dict().get("falha_resposta_observada")
    assert fonte is not None, "a rejeição observada não pode perder a causa por não ser falha HTTP"
    r = verificar_fala_turno(resposta["fala"], plano={**plano, "falha_resposta_observada": fonte})
    assert r["aceita"] is True and r["problemas"] == []


@pytest.mark.parametrize("mutacao", ["json", "sem_problemas", "estado_tecnico_misturado"])
def test_limite_de_rejeicao_nao_aceita_fonte_sem_a_observacao_do_avaliador(mutacao):
    plano, resposta, proposta = preparar(json.dumps({"fala": "Estou acompanhando nossa conversa.", "comandos": []}))
    fonte = resposta.get("falha_resposta_observada")
    assert fonte is not None
    if mutacao == "json": fonte = asdict(fonte)
    elif mutacao == "sem_problemas": fonte = replace(fonte, problemas_revisao=())
    else: fonte = replace(fonte, estado_tecnico="__LAYLAY_LLM_TIMEOUT__")
    assert verificar_fala_turno(resposta["fala"], plano={**plano,
        "falha_resposta_observada": fonte}).get("conclusao") is None


def test_rejeicao_semantica_na_composicao_instalada_nao_pede_contexto_ja_fornecido(tmp_path):
    pasta = tmp_path / "rejeicao"
    codigo = ("from pathlib import Path; from scripts.analises.sonda_conversa_continua import coletar; "
        "coletar(Path(__import__('sys').argv[1]),modelo_real=False,"
        "entradas=('hoje tive uma aula puxada','mas consegui terminar os exercícios','o que você acha disso?'))")
    p = subprocess.run([sys.executable, "-c", codigo, str(pasta)], capture_output=True,
        cwd=Path(__file__).resolve().parents[2], text=True, encoding="utf8", timeout=90)
    assert p.returncode == 0, p.stdout + p.stderr
    r = json.loads((pasta / "conversa.json").read_text(encoding="utf8"))["resultados"]
    assert all(len(t["respostas"]) == 1 and not t["executores_recusados"] for t in r)
    assert r[2]["respostas"] == ["Não consegui formular uma resposta confiável desta vez."]
