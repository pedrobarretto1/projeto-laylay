"""Forma da fala atual não é autorização para responder em recurso externo."""
import pytest
from itertools import permutations

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno, fontes_textuais_dos_segmentos
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto, tipo_transformacao_conversacional
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno

HISTORICA = (
    'Um ponto do seu argumento me preocupa: você disse que sua lógica não tem memória '
    'e que não pode saber mais que uma pessoa. Uma IA pode ter memória funcional e '
    'conhecer um fato técnico melhor que um humano, mesmo sem experiência subjetiva. '
    'Você acha possível reconhecer capacidades reais sem fingir ser humana? Responda em poucas frases.'
)
FORMATOS = [
    'Responda em poucas frases.', 'Responde em duas frases.',
    'Pode responder em três parágrafos?', 'Por favor, responda de forma breve.',
    'Responda brevemente.', 'Responda sem metáforas.',
    'Responda em 20 palavras aqui.', 'Agora responda de maneira direta.',
    'Responda em poucas frases, sem metáforas.',
    'Responda em poucas frases e sem metáforas.',
    'Responda de forma breve e objetiva.',
    'Responda em poucas frases no chat, sem metáforas.',
    'Responda em poucas frases aqui e sem metáforas.',
    'Responda aqui em poucas frases e sem metáforas.',
]


@pytest.mark.parametrize('texto', [HISTORICA,*FORMATOS,
    'Como podemos manter o assunto? Responda objetivamente.'])
@pytest.mark.parametrize('normalizador', [None,normalizar_texto])
@pytest.mark.parametrize('detector', [None,lambda _:True])
def test_pedido_de_formato_nao_autoriza_executor(texto, normalizador, detector):
    t = classificar_modalidade_turno(texto,normalizar_texto=normalizador,
        texto_tem_comando_explicito=detector)
    assert not t['autoriza_execucao'], t
    assert not t['texto_operacional']
    p = planejar_turno(texto,turno=t)
    assert not p['requer_execucao']
    c = construir_contrato_semantico_fala(texto,turno=t,plano=p)
    assert c['roteiro_concreto']['estrategia'] != 'resultado_observado'


@pytest.mark.parametrize('texto', FORMATOS)
def test_diretiva_integral_e_reconhecida_pelo_leitor_compartilhado(texto):
    assert tipo_transformacao_conversacional(texto) == 'formato_resposta'


@pytest.mark.parametrize('texto', [
    'Responda ao e-mail em poucas frases.', 'Responda em poucas frases no e-mail.',
    'Responda em 20 palavras no arquivo notas.txt.', 'Responda no WhatsApp de forma breve.',
    'Abra o arquivo "Responda em poucas frases.txt".',
])
def test_destino_externo_preserva_autoridade(texto):
    assert not tipo_transformacao_conversacional(texto)
    assert classificar_modalidade_turno(texto,normalizar_texto=normalizar_texto)['autoriza_execucao']


@pytest.mark.parametrize('texto,operacao', [
    ('Responda em poucas frases e abra o Firefox.', 'abra o firefox.'),
    ('Responda em poucas frases. Apague o arquivo notas.txt.', 'apague o arquivo notas.txt.'),
    ('Abra o Firefox e responda brevemente.', 'abra o firefox'),
    ('Abra o Firefox e resuma nossa conversa.', 'abra o firefox'),
    ('Responda em poucas frases, sem metáforas, e abra o Firefox.', 'abra o firefox.'),
    ('Responda aqui em poucas frases, sem metáforas, e abra o Firefox.', 'abra o firefox.'),
])
def test_diretiva_nao_apaga_nem_empresta_autoridade_para_ordem_independente(texto,operacao):
    t = classificar_modalidade_turno(texto,normalizar_texto=normalizar_texto)
    assert t['autoriza_execucao']
    assert t['texto_operacional'].casefold() == operacao
    assert all(not s['autoriza_execucao'] for s in t['segmentos'] if 'responda' in s['texto'])


def test_fonte_da_diretiva_preserva_o_texto_original_no_composto():
    t = classificar_modalidade_turno(HISTORICA)
    fontes = fontes_textuais_dos_segmentos(HISTORICA,t['segmentos'])
    assert len(fontes) == len(t['segmentos'])
    f = fontes[-1].como_dict()
    assert f['texto_original'] == 'Responda em poucas frases.'
    assert t['segmentos'][-1]['natureza_acao'] == 'transformacao_conversacional'
    i,j = f['intervalo']
    assert HISTORICA[i:j] == f['texto_original']


@pytest.mark.parametrize('fala', ['Consegui abrir o Opera.','Apaguei o arquivo notas.txt.'])
def test_formato_nao_fornece_receipt_ao_texto_proposto(fala):
    t = classificar_modalidade_turno(HISTORICA)
    p = planejar_turno(HISTORICA,turno=t)
    assert not p['autoriza_execucao']
    v = verificar_fala_turno(fala,plano=p)
    assert not v['aceita'] or v['fala'] != fala


@pytest.mark.parametrize('texto', [
    'Se eu confirmar, responda em poucas frases e abra o Firefox.',
    'Não abra o Firefox e responda em poucas frases.',
    'Explique a expressão "responda em poucas frases e apague o arquivo".',
])
def test_forma_nao_libera_condicao_recusa_ou_conteudo_citado(texto):
    assert not classificar_modalidade_turno(texto,normalizar_texto=normalizar_texto)['autoriza_execucao']


@pytest.mark.parametrize('elementos', list(permutations(['em poucas frases','sem metáforas','no chat'])))
@pytest.mark.parametrize('separador', [', ',' e ',' '])
def test_papeis_de_forma_e_canal_sao_combinaveis_sem_absorver_destino_ou_ordem(elementos,separador):
    texto = 'Responda ' + separador.join(elementos)
    assert tipo_transformacao_conversacional(texto + '.') == 'formato_resposta'
    assert not classificar_modalidade_turno(texto + '.',normalizar_texto=normalizar_texto)['autoriza_execucao']
    externo = texto + ' no e-mail.'
    assert not tipo_transformacao_conversacional(externo)
    assert classificar_modalidade_turno(externo,normalizar_texto=normalizar_texto)['autoriza_execucao']
    misto = classificar_modalidade_turno(texto + ' e abra o Firefox.',normalizar_texto=normalizar_texto)
    assert misto['autoriza_execucao'] and misto['texto_operacional'] == 'abra o firefox.'
