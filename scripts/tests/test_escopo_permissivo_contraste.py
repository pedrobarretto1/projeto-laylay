"""Moldura permissiva e contraste não inventam uma ordem para a assistente."""
import json
from pathlib import Path
import pytest
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.cognicao.plano_turno import planejar_turno

CASOS=json.loads((Path(__file__).parent/'fixtures/papo_casual.json').read_text(encoding='utf8'))
TEXTOS=[c['entrada']for c in CASOS if c['id']in {'papo-004','papo-008'}]
TEXTOS += ['Deixa eu mudar de assunto.', 'Deixe eu abrir o arquivo.',
    'Me deixa desligar a tomada.', 'Deixe-me organizar os livros.',
    'Deixe-me pôr a música.', 'Deixe-me só abrir o arquivo.',
    'Deixe-me me conectar ao Wi-Fi.', 'Deixe-me me desligar da rede.',
    'Me deixe te mostrar o desenho.',
    'Não muda o robô, muda o jeito que a gente convive com ele.',
    'Não abre a pasta, abre a discussão.', 'Não apaga o problema, apaga a lembrança.']

@pytest.mark.parametrize('texto',TEXTOS)
@pytest.mark.parametrize('detector',[None,lambda _:True])
def test_matriz_com_outro_agente_ou_contraste_nao_cria_autorizacao(texto,detector):
    t=classificar_modalidade_turno(texto,normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=detector)
    assert not t['autoriza_execucao'],t
    assert not t['texto_operacional']
    assert not planejar_turno(texto,turno=t)['requer_execucao']

@pytest.mark.parametrize('texto',[
    'Deixa a janela aberta.', 'Deixe a luz ligada.',
    'Não apaga o arquivo. Abre o navegador.',
    'Não apaga o arquivo, mas abra o navegador.',
    'Deixa eu mudar de assunto. Abra o navegador.',
    'Não muda o robô, mas por favor abre o navegador.',
    'Deixa eu terminar e abra o navegador.',
    'Deixa eu mudar de assunto e abre o navegador.',
    'Deixe-me a luz ligada.', 'Deixe-me a janela aberta.',
])
def test_pedido_independente_a_assistente_preserva_autoridade(texto):
    assert classificar_modalidade_turno(texto)['autoriza_execucao']
