"""Adequação ao enunciador não se comprova pelo gosto da autora da resposta."""
from dataclasses import asdict, replace
import json

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao, montar_pacote_reparo_comunicacao,
)
from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria, exigir_suporte_no_pacote_autoral
from scripts.tests.test_opiniao_autoral_conferivel import preparar


CONSULTAS = ('me fala lay, que estilo combina comigo?', 'que estilo combina comigo?',
    'qual estilo musical combina comigo?', 'que aplicativo combina comigo?',
    'qual jogo combina comigo?', 'qual cor combina comigo?', 'que livro combina comigo?',
    'me diga, qual filme combina comigo?', 'Laylay, qual roupa combina comigo?',
    'que estilo combina mais comigo?', 'qual o estilo que combina comigo?',
    'me fala, Lay, que estilo combina comigo?', 'qual o aplicativo que mais combina comigo?',
    'qual filme mais combina comigo?')


def quadro(texto):
    turno, plano, mente = preparar(texto, 'Eu prefiro rock.', 'qual o seu estilo musical?')
    contrato = plano['contrato_fala']
    mente.update(turno_atual=turno, plano_turno_atual=plano, contrato_fala_atual=contrato)
    runtime = ContextoPromptRuntime(memoria_sqlite=None, resumo_mente_integrada=lambda _: '',
        formatar_playlists=lambda: '', get_status_humor_prompt=lambda: '',
        base_system_prompt='identidade', estado_getter=lambda: mente)
    pacote = runtime.preparar_envio_modelo([{'role':'system','content':'Opinião anterior: Eu prefiro rock.'},
        {'role':'user','content':texto}], turno_id=plano['id'])
    return turno, plano, mente, pacote


@pytest.mark.parametrize('texto,categoria', tuple(zip(CONSULTAS, (
    'estilo', 'estilo', 'estilo musical', 'aplicativo', 'jogo', 'cor', 'livro',
    'filme', 'roupa', 'estilo', 'estilo', 'estilo', 'aplicativo', 'filme'))))
def test_alvo_e_relacao_atual_chegam_a_autoria_e_revisao(texto, categoria):
    _, plano, _, pacote = quadro(texto)
    contrato = plano['contrato_fala']
    fonte = contrato.get('adequacao_pessoal')
    assert fonte is not None, 'primeira fronteira: pedido de adequação não tem alvo/predicado próprio'
    dados = asdict(fonte)
    assert dados['alvo'] == 'usuario' and dados['relacao'] == 'adequacao'
    assert dados['categoria'] == categoria, 'artigo, relativo ou advérbio não integra o objeto da escolha'
    assert dados['texto_usuario'] == texto and dados['turno_id'] == str(plano['id'])
    assert dados['prova_factual'] is False and dados['autoriza_execucao'] is False
    assert contrato['atos'] == ['adequacao_pessoal']
    assert contrato['roteiro_concreto']['estrategia'] == 'adequacao_ao_usuario'
    assert pacote.contexto_fechado and pacote.mensagens[-1]['content'] == texto
    assert 'Opinião anterior:' not in str(pacote.mensagens)
    from mente_laylay.cognicao.adequacao_pessoal import realizacoes_adequacao
    opcoes = realizacoes_adequacao(texto, contrato=contrato, turno_id=plano['id'])
    assert len(opcoes) >= 2
    for fala in opcoes:
        assert 'prefiro rock' not in fala and ('?' in fala or 'me conta' in fala)
        assert pacote.contrato_saida.decodificar_json(json.dumps({'comandos':[],
            'suporte_proposicoes':[{'texto':fala,'fontes':[]}]}))['fala'] == fala
        r = verificar_fala_turno(fala, plano=plano)
        assert r['aceita'] and r['fala'] == fala
        assert r['revisao_suporte_autoria']['pode_confirmar_fato_externo'] is False


@pytest.mark.parametrize('texto,fala', [
    (CONSULTAS[0], 'Lay, não tenho estilo musical favorito, mas a ideia de algo intenso e direto me chama a atenção.'),
    ('que aplicativo combina comigo?', 'Eu prefiro Firefox.'),
    ('qual jogo combina comigo?', 'Ainda não escolhi um jogo favorito.'),
    ('que estilo combina comigo?', 'Rock combina com você porque você é rebelde.'),
    ('qual cor combina comigo?', 'Azul combina com você porque sua pele é clara.'),
    ('que estilo combina comigo?', 'Talvez rock combine com você, pois eu gosto.'),
    ('que estilo combina comigo?', 'Sobre estilo, o que você procura? Abri sua playlist.'),
])
def test_gosto_da_autora_e_palpite_sobre_usuario_nao_respondem_por_si(texto, fala):
    _, plano, _, _ = quadro(texto)
    r = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
    assert r['problemas_bloqueantes'] and not r['aceita'], r
    assert not verificar_fala_turno(fala, plano=plano)['aceita']


def test_reparo_preserva_o_mesmo_alvo_sem_reintroduzir_rascunho():
    texto, ruim = CONSULTAS[0], 'Eu prefiro rock.'
    _, plano, _, _ = quadro(texto)
    avaliacao = avaliar_qualidade_comunicacao(texto, ruim, plano=plano)
    assert avaliacao['problemas_bloqueantes']
    pacote = exigir_suporte_no_pacote_autoral(montar_pacote_reparo_comunicacao(texto, ruim,
        avaliacao, plano=plano, mensagens=[{'role':'assistant','content':ruim}]))
    assert pacote.contexto_fechado and ruim not in str(pacote.mensagens)
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({'comandos':[],
            'suporte_proposicoes':[{'texto':ruim,'fontes':[]}]}))


@pytest.mark.parametrize('mutacao', ['turno', 'texto', 'categoria', 'dict', 'ausente', 'perspectiva'])
def test_fonte_alterada_nao_cai_em_revisao_generica(mutacao):
    texto = 'que aplicativo combina comigo?'
    _, plano, _, _ = quadro(texto)
    contrato = plano['contrato_fala']
    fonte = contrato.get('adequacao_pessoal')
    assert fonte is not None
    if mutacao == 'turno': contrato['adequacao_pessoal'] = replace(fonte, turno_id='outro')
    elif mutacao == 'texto': contrato['adequacao_pessoal'] = replace(fonte, texto_usuario='outro')
    elif mutacao == 'categoria': contrato['adequacao_pessoal'] = replace(fonte, categoria='estilo')
    elif mutacao == 'dict': contrato['adequacao_pessoal'] = asdict(fonte)
    elif mutacao == 'ausente': del contrato['adequacao_pessoal']
    else: del contrato['perspectiva_enunciador']
    assert not verificar_fala_turno('Eu prefiro Firefox.', plano=plano)['aceita']


def test_proposta_estrangeira_nao_recebe_suporte_do_ato_atual():
    texto = 'que estilo combina comigo?'
    _, plano, _, _ = quadro(texto)
    assert plano['contrato_fala'].get('adequacao_pessoal') is not None
    from mente_laylay.cognicao.adequacao_pessoal import realizacoes_adequacao
    fala = realizacoes_adequacao(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])[0]
    plano['suporte_autoria_proposto'] = capturar_suporte_autoria(ContratoPropostaPrincipal('outro', texto,
        json.dumps({'comandos':[], 'suporte_proposicoes':[{'texto':fala,'fontes':[]}]})))
    assert not verificar_fala_turno(fala, plano=plano)['aceita']


@pytest.mark.parametrize('texto', ['qual o seu estilo musical?', 'qual é meu estilo favorito?',
    'que estilo combina com ela?', 'que estilo combina com você?',
    'rock combina comigo', 'que estilo combinava comigo?', 'que estilo combina comigo e abre o navegador',
    'que estilo combina comigo? Apaga meus arquivos.', 'a frase "que estilo combina comigo?" está certa?',
    'se eu perguntar que estilo combina comigo, o que você diria?',
    'não me diga que estilo combina comigo', 'me fala sobre a Laylay, que estilo combina comigo?',
    'que estilo e cor combinam comigo?'])
def test_outra_relacao_pessoa_e_ato_adicional_nao_sao_absorvidos(texto):
    _, plano, _, _ = quadro(texto)
    assert 'adequacao_pessoal' not in plano['contrato_fala']


@pytest.mark.parametrize('mutacao', ['evento', 'autoridade', 'comandos'])
def test_pedido_operacional_ou_evento_nao_recebe_ato_conversacional(mutacao):
    texto = 'que aplicativo combina comigo?'
    turno, plano, mente = preparar(texto)
    if mutacao == 'evento': turno['natureza_entrada'] = 'evento'
    elif mutacao == 'autoridade': turno['autoriza_execucao'] = plano['autoriza_execucao'] = True
    else: plano['comandos'] = [{'intent':'APP_OPEN','params':{'nome_app':'Firefox'}}]
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    assert 'adequacao_pessoal' not in contrato
