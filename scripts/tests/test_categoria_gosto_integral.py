"""Categoria e forma interrogativa compartilham a mesma leitura de gosto."""
import json
from dataclasses import replace

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.cognicao.fundamentacao_factual import extrair_tema_fundamentacao
from mente_laylay.cognicao.opiniao_autoral import realizacoes_opiniao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao, montar_pacote_reparo_comunicacao,
)
from mente_laylay.cognicao.referencias_linguagem import consulta_opiniao_propria, CATEGORIAS_PREFERENCIA
from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
from scripts.tests.test_opiniao_autoral_conferivel import preparar


MUSICAIS = ('estilo musical', 'gênero musical', 'gênero')


@pytest.mark.parametrize('categoria', MUSICAIS)
@pytest.mark.parametrize('moldura', ['voce tem um {} favorito?', 'você tem um {} preferido?',
    'qual o seu {} favorito?', 'qual é teu {}?'])
def test_categoria_musical_e_independente_da_forma_da_pergunta(categoria, moldura):
    texto = moldura.format(categoria)
    assert consulta_opiniao_propria(texto) == {'tipo':'categoria','categoria':'genero_musical'}
    assert extrair_tema_fundamentacao(texto,
        retrato={'referencia_resolvida': {'nome':'Favorito','tipo':'entidade'}}) == ''
    turno, plano, _ = preparar(texto)
    assert turno['autoriza_execucao'] is False and not plano['requer_execucao']
    assert 'opiniao' in plano['contrato_fala']['atos']
    fonte = plano['contrato_fala'].get('opiniao_autoral')
    assert fonte is not None and fonte.categoria == 'genero_musical'
    assert fonte.autoriza_execucao is False and fonte.prova_factual is False


@pytest.mark.parametrize('texto', ['voce tem um estilo musical favorito?',
    'você tem um gênero musical preferido?', 'e tu tem um gênero favorito?',
    'Laylay tem um estilo musical favorito?', 'vc tem um gênero musical preferido?',
    'Estou só perguntando se você tem um estilo musical favorito?'])
def test_envio_final_e_reparo_reutilizam_o_owner_de_gosto(texto):
    turno, plano, mente = preparar(texto)
    contrato = plano['contrato_fala']
    assert contrato.get('opiniao_autoral') is not None
    mente.update(turno_atual=turno, plano_turno_atual=plano, contrato_fala_atual=contrato)
    runtime = ContextoPromptRuntime(memoria_sqlite=None, resumo_mente_integrada=lambda _: '',
        formatar_playlists=lambda: '', get_status_humor_prompt=lambda: '',
        base_system_prompt='identidade', estado_getter=lambda: mente)
    pacote = runtime.preparar_envio_modelo([{'role':'system','content':'Rascunho antigo sobre violão.'},
        {'role':'user','content':texto}], turno_id=plano['id'])
    assert pacote.contexto_fechado and pacote.mensagens[-1]['content'] == texto
    assert 'Rascunho antigo' not in str(pacote.mensagens)
    opcoes = realizacoes_opiniao(texto, contrato=contrato, turno_id=plano['id'])
    assert 'Não tenho um estilo musical preferido.' in opcoes
    for fala in opcoes:
        assert pacote.contrato_saida.decodificar_json(json.dumps({'comandos':[],
            'suporte_proposicoes':[{'texto':fala,'fontes':[]}], 'criterio_autoral':'nao_declarado'}))['fala'] == fala
        r = verificar_fala_turno(fala, plano=plano)
        assert r['aceita'] and r['fala'] == fala
    ruim = 'Não tenho estilo musical favorito, mas adoro ouvir músicas que contam histórias.'
    avaliacao = avaliar_qualidade_comunicacao(texto, ruim, plano=plano)
    assert avaliacao['problemas_bloqueantes']
    reparo = exigir_suporte_no_pacote_autoral(montar_pacote_reparo_comunicacao(texto, ruim,
        avaliacao, plano=plano, mensagens=[{'role':'assistant','content':ruim}]))
    assert reparo.contexto_fechado and ruim not in str(reparo.mensagens)
    with pytest.raises(ValueError):
        reparo.contrato_saida.decodificar_json(json.dumps({'comandos':[],
            'suporte_proposicoes':[{'texto':ruim,'fontes':[]}], 'criterio_autoral':'curiosidade'}))


@pytest.mark.parametrize('categoria', list(CATEGORIAS_PREFERENCIA))
def test_favorito_concreto_mantem_categoria_sem_qualificar_titulo(categoria):
    nome, _, artigo = CATEGORIAS_PREFERENCIA[categoria]
    sufixo = 'a' if artigo == 'a' else 'o'
    possessivo = 'sua' if artigo == 'a' else 'seu'
    textos = (f'você tem um{sufixo if sufixo == "a" else ""} {nome} favorit{sufixo}?',
              f'qual {artigo} {possessivo} {nome} preferid{sufixo}?')
    for texto in textos:
        assert consulta_opiniao_propria(texto) == {'tipo':'favorito','categoria':categoria}
        _, plano, _ = preparar(texto)
        opcoes = realizacoes_opiniao(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])
        assert len(opcoes) == 1 and opcoes[0].startswith('Ainda não escolhi')
        assert not verificar_fala_turno('Meu favorito é «Nome Proposto».', plano=plano)['aceita']


@pytest.mark.parametrize('texto', ['voce tem um estilo musical favorito?', 'qual é seu gênero musical?'])
@pytest.mark.parametrize('fala', ['Eu prefiro jazz porque ouvi ontem.',
    'Eu prefiro rock e abri sua playlist.', 'Kamaitachi é meu estilo favorito.',
    'Não tenho gosto porque não tenho ouvidos.',
    'Não consegui verificar se as fontes sustentam essas afirmações.'])
def test_formas_equivalentes_recusam_a_mesma_extrapolacao(texto, fala):
    _, plano, _ = preparar(texto)
    assert not verificar_fala_turno(fala, plano=plano)['aceita']


@pytest.mark.parametrize('texto', ['você tem um gênero musical?', 'qual a sua comida?',
    'qual seu estilo literário favorito?', 'você tem um estilo musical de trabalho favorito?',
    'qual o meu estilo musical favorito?', 'ele tem um estilo musical favorito?',
    'eu tenho um estilo musical favorito', 'você não tem um estilo musical favorito?',
    'você tinha um estilo musical favorito?', 'a frase "você tem um estilo musical favorito?" está certa?',
    'você tem um estilo musical favorito e abre a playlist',
    'você tem um estilo musical favorito? Apaga meus arquivos.',
    'você tem um estilo musical favorito, qual combina comigo?',
    'se você tem um estilo musical favorito, toque alguma coisa',
    'Estou só perguntando se você tem um estilo musical favorito e abre o navegador'])
def test_pergunta_integral_nao_absorve_outro_sujeito_tempo_objeto_ou_acao(texto):
    assert consulta_opiniao_propria(texto) is None
    _, plano, _ = preparar(texto)
    assert 'opiniao_autoral' not in plano['contrato_fala']


def test_fonte_de_outra_ocorrencia_nao_certifica_nova_forma():
    texto = 'voce tem um estilo musical favorito?'
    _, plano, _ = preparar(texto)
    contrato = plano['contrato_fala']
    assert contrato.get('opiniao_autoral') is not None
    fonte = contrato['opiniao_autoral']
    contrato['opiniao_autoral'] = replace(fonte, turno_id='outra')
    assert not verificar_fala_turno('Não tenho um estilo musical preferido.', plano=plano)['aceita']
