"""Adjunto de finalidade e sujeito do relato não concedem ordem à assistente."""

import pytest
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

from mente_laylay.cognicao.modalidade_turno import (
    _evidencia_ato_operacional,
    autoriza_execucao_efetiva,
    classificar_modalidade_turno,
)
from mente_laylay.cognicao.plano_turno import planejar_turno


RELATO_HISTORICO = (
    "antes eu falei caderno verde, mas para desenho vou usar o amarelo"
)


@pytest.mark.parametrize("texto", [
    RELATO_HISTORICO,
    "antes eu falei caderno verde, mas para desenho eu vou usar o amarelo",
    "para desenho vou usar o amarelo",
    "para desenho eu vou usar o amarelo",
    "para estudar vou abrir o navegador",
    "para estudar eu vou abrir o navegador",
    "para organizar meus arquivos vou criar uma pasta",
    "para organizar meus arquivos eu vou criar uma pasta",
    "para a leitura vou acender a lâmpada",
    "para a leitura eu vou acender a lâmpada",
    "para música eu vou ouvir jazz",
    "para o desenho, vou usar o amarelo",
    "para o desenho, eu vou usar o amarelo",
    "para desenho você usa o amarelo",
    "para estudar o Leo vai abrir o navegador",
    "para estudar o Leo abre o navegador",
    "para estudar Leo abre o navegador",
    "para estudar minha irmã abre o navegador",
])
def test_relato_com_finalidade_anteposta_nao_cria_autorizacao(texto):
    turno = classificar_modalidade_turno(texto)
    assert not autoriza_execucao_efetiva(turno), turno
    assert not turno["texto_operacional"], turno
    assert all(not s["autoriza_execucao"] for s in turno["segmentos"])


@pytest.mark.parametrize("texto", [
    "para desenho qual cor combina?",
    "para estudar qual navegador é melhor?",
    "para organizar os arquivos, como eu crio uma pasta?",
])
def test_pergunta_com_finalidade_anteposta_nao_cria_autorizacao(texto):
    turno = classificar_modalidade_turno(texto)
    assert not autoriza_execucao_efetiva(turno), turno
    assert turno["modalidade"] == "pergunta", turno


@pytest.mark.parametrize("texto", [
    "para desenho vou usar o amarelo",
    "para estudar eu vou abrir o navegador",
    "para desenhar",
])
def test_preposicao_nao_prova_fronteira_operacional(texto):
    evidencia, origem = _evidencia_ato_operacional(texto, normalizar_texto=None)
    assert not evidencia, (texto, origem)


def test_finalidade_antes_de_pedido_nao_vira_segundo_comando():
    turno = classificar_modalidade_turno("para desenhar, abra o navegador")
    assert autoriza_execucao_efetiva(turno)
    comandos = [s for s in turno["segmentos"] if s["autoriza_execucao"]]
    assert len(comandos) == 1, comandos
    assert not any(s["texto"].strip() == "para desenhar" for s in comandos)


@pytest.mark.parametrize("texto,nucleo", [
    ("para desenhar abra o navegador", "abra o navegador"),
    ("para estudar abre a calculadora", "abre a calculadora"),
    ("para organizar os arquivos cria uma pasta", "cria uma pasta"),
    ("para ler o livro abra o navegador", "abra o navegador"),
    ("para organizar o arquivo crie uma pasta", "crie uma pasta"),
    ("para desenho pode abrir o navegador para mim?", "pode abrir o navegador para mim?"),
    ("para estudar eu preciso que você abra o navegador", "eu preciso que você abra o navegador"),
])
def test_finalidade_sem_virgula_preserva_oracao_diretiva_real(texto, nucleo):
    turno = classificar_modalidade_turno(texto)
    assert autoriza_execucao_efetiva(turno), turno
    comandos = [s for s in turno["segmentos"] if s["autoriza_execucao"]]
    assert [s["texto"] for s in comandos] == [nucleo], comandos


def test_plano_compartilhado_nao_exige_execucao_de_mudanca_relatada():
    turno = classificar_modalidade_turno(RELATO_HISTORICO)
    plano = planejar_turno(RELATO_HISTORICO, turno=turno)
    assert not plano["autoriza_execucao"], plano
    assert not plano["requer_execucao"], plano
    assert not any(a["requer_execucao"] for a in plano["atos"])


@pytest.mark.parametrize("texto", [
    "vou usar o amarelo",
    "eu vou usar o amarelo",
    "vou abrir o navegador para estudar",
    "eu vou abrir o navegador para estudar",
    "antes eu falei verde, mas vou usar amarelo",
    "para estudar talvez eu abra o navegador",
])
def test_controles_de_relato_sem_autorizacao(texto):
    assert not autoriza_execucao_efetiva(classificar_modalidade_turno(texto))


@pytest.mark.parametrize("texto", [
    "para a música",
    "pare a música",
    "para motores",
    "para motor",
    "para ventilador",
    "para computador",
    "para os motores",
    "pare o corpo",
    "para agora",
    "para de falar",
    "para devagar",
    "para a música porque eu vou dormir",
    'para o arquivo "eu vou usar amanhã"',
    "abre o navegador para estudar",
    "eu vou desenhar, mas abre o navegador",
    "para estudar eu vou abrir o navegador; liga a lâmpada",
])
def test_pedido_atual_independente_conserva_autoridade(texto):
    turno = classificar_modalidade_turno(texto)
    assert autoriza_execucao_efetiva(turno), turno


def test_ato_independente_nao_autoriza_o_relato_anterior():
    turno = classificar_modalidade_turno(
        "para estudar eu vou abrir o navegador; liga a lâmpada"
    )
    comandos = [s for s in turno["segmentos"] if s["autoriza_execucao"]]
    assert len(comandos) == 1, comandos
    assert comandos[0]["texto"].strip() == "liga a lâmpada"


def test_composicao_instalada_preserva_relato_e_pedido_independente(tmp_path):
    codigo = textwrap.dedent(r'''
        import sys, json, os, importlib.util
        from pathlib import Path
        from types import ModuleType
        apps = ModuleType('AppOpener')
        apps.open = apps.close = lambda *a, **k: False
        apps.give_appnames = lambda *a, **k: {}
        sys.modules['AppOpener'] = apps
        if arquivo := os.environ.get('LAYLAY_MODALIDADE_BASELINE'):
            nome = 'mente_laylay.cognicao.modalidade_turno'
            spec = importlib.util.spec_from_file_location(nome, arquivo)
            modulo = importlib.util.module_from_spec(spec)
            sys.modules[nome] = modulo
            spec.loader.exec_module(modulo)
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        root = preparar_instalacao_isolada(Path(sys.argv[1]))
        casos = []
        for texto in [
            'antes eu falei caderno verde, mas para desenho vou usar o amarelo',
            'para estudar eu vou abrir o navegador; liga a lâmpada',
        ]:
            root._estado_compartilhado_runtime.substituir('mental', criar_estado_mental_inicial())
            turno = root._iniciar_planejamento_turno(texto, origem='teste_relato_composto')
            plano = root._estado_compartilhado_runtime.mental['plano_turno_atual']
            casos.append({'texto': texto, 'turno': {k: turno.get(k) for k in
                ['autoriza_execucao', 'segmentos', 'texto_operacional']},
                'plano': {k: plano.get(k) for k in ['autoriza_execucao', 'requer_execucao', 'atos']}})
        sys.__stdout__.write('RELATO_COMPOSTO_JSON=' + json.dumps(casos, ensure_ascii=False) + '\n')
    ''')
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "LAYLAY_NEURAL_MODE": "off",
           "LAYLAY_NEURAL_COLETA_ENTRADAS": "0", "LAYLAY_IOT_MODO": "simulado",
           "LAYLAY_TERMINAL_2": "0", "LAYLAY_MICROFONE_ATIVO": "0",
           "LAYLAY_BRIEFING_INICIAL": "0", "LAYLAY_FALAS_INICIAIS": "0",
           "LAYLAY_PRESENCA": "0", "LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR": "0",
           "LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR": "0", "GMAIL_USER": " ",
           "GMAIL_APP_PASSWORD": " "}
    resultado = subprocess.run(
        [sys.executable, "-c", codigo, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2], env=env,
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    linhas = [linha.split("=", 1)[1] for linha in resultado.stdout.splitlines()
              if linha.startswith("RELATO_COMPOSTO_JSON=")]
    assert linhas, resultado.stdout + resultado.stderr
    dados = json.loads(linhas[-1])
    relato, misto = dados
    assert not relato["turno"]["autoriza_execucao"], relato
    assert not relato["plano"]["requer_execucao"], relato
    comandos = [s for s in misto["turno"]["segmentos"] if s["autoriza_execucao"]]
    assert [s["texto"] for s in comandos] == ["liga a lâmpada"], misto
