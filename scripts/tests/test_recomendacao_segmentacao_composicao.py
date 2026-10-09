"""P02/P06 usam os callbacks instalados em laylay.py; efeitos ficam nas portas."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope="module")
def composicao_real() -> dict:
    codigo = textwrap.dedent('''
        import json, os
        import requests
        from mente_laylay.integracao import instancia_unica
        nome_real = instancia_unica.nome_mutex_instancia
        instancia_unica.nome_mutex_instancia = lambda identificador: nome_real(
            str(identificador) + ".pytest-p02-p06-" + str(os.getpid()))
        import laylay as root
        estado = root._estado_compartilhado_runtime
        root._composicao_turno_runtime._servicos["_coleta_entradas_neurais"] = None
        contexto = root._resposta_ia_runtime._contexto()
        pesquisa = root._pesquisa_contextual_runtime
        def indisponivel(*args, **kwargs):
            raise requests.ConnectionError("fonte indisponível no controle")
        pesquisa.requests_get = indisponivel
        saidas = {}
        for texto in (
            "pode me recomendar um modelo que seja bom e barato",
            "quero um modelo do modulo dc-dc que possa alimentar um esp32 super mini, 4 motores e uma tela oled alem de uma bateria de litio de 5V",
            "oi lay, pode me recomendar um filme?",
        ):
            turno = root._iniciar_planejamento_turno(texto, origem="teste_composicao")
            plano = dict(estado.mental["plano_turno_atual"])
            final = contexto["contexto_finalizacao_runtime"].montar()
            falas = []
            final["messages"] = [{"role": "user", "content": texto}]
            final["falar_com_lipsync"] = lambda fala, *args: falas.append(fala) or True
            final["memoria_inteligente"] = None
            final["salvar_memoria"] = lambda: None
            contexto["finalizar_execucao"](final, [], [],
                "Recomendo o Modelo Inventado. É perfeito e barato.", False, False, False)
            saidas[texto] = {
                "fala": falas, "estrategia": plano["contrato_fala"]["roteiro_concreto"]["estrategia"],
                "autoriza": turno["autoriza_execucao"],
                "verificacao": estado.mental["plano_turno_atual"].get("ultima_verificacao"),
            }
        class Resposta:
            text = '<ol><li><i><a href="/wiki/A">Título A</a></i></li><li><i><a href="/wiki/B">Título B</a></i></li><li><i><a href="/wiki/C">Título C</a></i></li></ol>'
            def raise_for_status(self): pass
        pesquisa.requests_get = lambda *args, **kwargs: Resposta()
        texto = "me recomenda um filme de romance"
        root._iniciar_planejamento_turno(texto, origem="teste_composicao")
        fonte = estado.mental["plano_turno_atual"]["fundamentacao_factual"]
        saidas["fonte_observada"] = {
            "fonte": fonte,
            "verificacao": root._verificar_fala_do_turno(
                "Título B tem um enredo perfeito e ganhou sete prêmios.", origem="ia_final"),
        }
        for nome in ("antonio.txt", "relatorio.final.pdf", "backup.tar.gz"):
            texto = f"preciso que voce nao apague o arquivo {nome}?"
            turno = root._iniciar_planejamento_turno(texto, origem="teste_composicao")
            saidas[nome] = {
                "turno": turno,
                "validacao": contexto["validar_comandos_planejados"]([
                    {"intent": "DELETE_ITEM", "params": {"nome": nome}}]),
            }
        print("P02_P06_JSON=" + json.dumps(saidas, ensure_ascii=False))
    ''')
    ambiente = dict(os.environ, GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ",
        LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
        LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0",
        LAYLAY_FALAS_INICIAIS="0", LAYLAY_PRESENCA="0")
    processo = subprocess.run([sys.executable, "-c", codigo],
        cwd=Path(__file__).resolve().parents[2], env=ambiente,
        capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert processo.returncode == 0, processo.stdout + processo.stderr
    linha = next(l for l in processo.stdout.splitlines() if l.startswith("P02_P06_JSON="))
    return json.loads(linha.split("=", 1)[1])


@pytest.mark.parametrize("texto", (
    "pode me recomendar um modelo que seja bom e barato",
    "quero um modelo do modulo dc-dc que possa alimentar um esp32 super mini, 4 motores e uma tela oled alem de uma bateria de litio de 5V",
    "oi lay, pode me recomendar um filme?",
))
def test_finalizador_instalado_nao_publica_recomendacao_sem_fonte(composicao_real, texto):
    dados = composicao_real[texto]
    assert dados["estrategia"] in {"preparacao_recomendacao", "resposta_multiacto"}
    assert not dados["autoriza"]
    assert dados["verificacao"]["aceita"] is True
    assert "recomendacao_sem_candidato_verificado" in dados["verificacao"]["problemas"]
    assert len(dados["fala"]) == 1
    assert "Modelo Inventado" not in dados["fala"][0]
    assert "opção verificada" in dados["fala"][0]


def test_composicao_pesquisa_liga_candidato_a_trecho_sem_certificar_atributos(composicao_real):
    dados = composicao_real["fonte_observada"]
    assert dados["fonte"]["confiavel"] is True
    assert dados["fonte"]["candidatos"] == ["Título A", "Título B", "Título C"]
    assert dados["fonte"]["fontes"][0]["url"].startswith("https://pt.wikipedia.org/wiki/")
    fala = dados["verificacao"]["fala"]
    assert "Título B" in fala
    assert "sete prêmios" not in fala
    assert "Não confirmei" in fala


@pytest.mark.parametrize("nome", ("antonio.txt", "relatorio.final.pdf", "backup.tar.gz"))
def test_composicao_preserva_filename_e_barreira_de_recusa(composicao_real, nome):
    dados = composicao_real[nome]
    assert len(dados["turno"]["segmentos"]) == 1
    assert nome in dados["turno"]["segmentos"][0]["texto"]
    assert dados["turno"]["modalidade"] == "recusa"
    assert not dados["turno"]["autoriza_execucao"]
    assert dados["validacao"]["comandos"] == []
