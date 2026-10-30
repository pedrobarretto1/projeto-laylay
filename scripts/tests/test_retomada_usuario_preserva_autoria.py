"""Consulta ao dizer do usuário exige atribuição e apoio, mesmo fora da gramática."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.tests.test_obrigacao_apoio_explicacao import plano_autoral
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao, montar_mensagens_reparo_comunicacao,
)
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao


CASOS = [
    ('eu prefiro Obsidian', 'qual aplicativo eu tinha dito preferir',
     'Eu não disse qual aplicativo preferia, só perguntei.', 'Você disse que prefere Obsidian.'),
    ('eu não gosto de café', 'qual bebida eu tinha dito não gostar',
     'Eu não disse que não gostava de café. Foi só uma pergunta.', 'Você contou que não gosta de café.'),
    ('eu não gosto de chá', 'o que eu disse sobre chá',
     'Eu não gosto de chá. Obrigada por me avisar.', 'Você disse não gostar de chá.'),
    ('eu gosto de rock', 'eu contei que não gosto de rock?',
     'Eu não gosto de rock. Foi o que você disse no início.', 'Você disse que gosta de rock.'),
]


def plano_com_fonte(fonte, pedido, fala):
    plano = plano_autoral(pedido, fala)
    turno = classificar_modalidade_turno(pedido)
    plano.update(ato_principal=turno['ato_principal'],
        atos=[{'tipo': s['modalidade']} for s in turno['segmentos']], autoriza_execucao=False)
    plano['contrato_fala'] = construir_contrato_semantico_fala(
        pedido, turno=turno, plano=plano)
    assert set(plano['contrato_fala']['atos']) == {'pergunta'}
    plano['relatos_usuario'] = [{'id': 'dialogo:usuario:1:' + hashlib.sha256(fonte.encode('utf8')).hexdigest(),
        'autor': 'usuario', 'origem': 'historico_conversa', 'status': 'relatado_pelo_usuario', 'texto': fonte}]
    # Estes controles de autoria pressupõem que o nome é de um app. Agora
    # explicitam essa fonte de tipo, separada da preferência do usuário.
    from mente_laylay.cognicao.categoria_preferencia import montar_apoios_categoria_preferencia
    from mente_laylay.integracao.catalogo_aplicativos import CatalogoAplicativosRuntime
    apoio = montar_apoios_categoria_preferencia(plano,
        catalogo_aplicativos=CatalogoAplicativosRuntime(apps_map={'obsidian': 'obsidian'}))
    if apoio is not None:
        plano['apoios_categoria_preferencia'] = apoio
    return plano


@pytest.mark.parametrize('fonte,pedido,ruim,boa', CASOS)
def test_fora_do_recorte_nao_aprova_nucleo_em_pessoa_errada(fonte, pedido, ruim, boa):
    plano = plano_com_fonte(fonte, pedido, ruim)
    q = avaliar_qualidade_comunicacao(pedido, ruim, plano=plano)
    assert not q['aceita'] and q['requer_reparo'], 'rascunho fora da gramática foi aceito sem conferência do relato'
    assert 'retomada_usuario_sem_nucleo_conferido' in q['problemas_bloqueantes']
    final = verificar_fala_turno(ruim, plano=plano)
    assert final['fala'] != ruim, 'guardião final publicou a pessoa indevida'


@pytest.mark.parametrize('fonte,pedido,ruim,boa', CASOS)
def test_relato_atribuido_e_sustentado_permanece_natural(fonte, pedido, ruim, boa):
    plano = plano_com_fonte(fonte, pedido, boa)
    q = avaliar_qualidade_comunicacao(pedido, boa, plano=plano)
    assert 'retomada_usuario_sem_nucleo_conferido' not in q['problemas_bloqueantes']
    assert verificar_fala_turno(boa, plano=plano)['fala'] == boa


def test_citacao_integral_preserva_relato_fora_da_gramatica_de_preferencias():
    fonte = 'Meu cachorro não vai ao encontro. Ele fica em casa.'
    pedido = 'o que eu disse sobre meu cachorro?'
    fala = f'Você contou: «{fonte}».'
    plano = plano_com_fonte(fonte, pedido, fala)
    q = avaliar_qualidade_comunicacao(pedido, fala, plano=plano)
    assert 'retomada_usuario_sem_nucleo_conferido' not in q['problemas_bloqueantes']
    assert verificar_fala_turno(fala, plano=plano)['fala'] == fala


@pytest.mark.parametrize('variante', ['autor', 'hash', 'contestado', 'pergunta_atual'])
def test_rotulo_ou_citacao_sem_fonte_qualificada_nao_vira_apoio(variante):
    fonte, pedido, _, boa = CASOS[0]
    plano = plano_com_fonte(fonte, pedido, boa)
    item = plano['relatos_usuario'][0]
    if variante == 'autor': item['autor'] = 'laylay'
    elif variante == 'hash': item['id'] = 'dialogo:usuario:1:' + '0' * 64
    elif variante == 'contestado': item['status'] = 'contestado'
    else:
        item.update(texto=pedido, origem='fala_atual', id='entrada:usuario:turno:' + hashlib.sha256(pedido.encode('utf8')).hexdigest())
        boa = f'Você contou: «{pedido}».'
    q = avaliar_qualidade_comunicacao(pedido, boa, plano=plano)
    assert 'retomada_usuario_sem_nucleo_conferido' in q['problemas_bloqueantes']


@pytest.mark.parametrize('variante', ['outro_turno', 'dict_proposto', 'execucao'])
def test_contrato_alheio_ou_operacao_nao_recebe_julgamento_de_retomada(variante):
    fonte, pedido, ruim, _ = CASOS[0]
    plano = plano_com_fonte(fonte, pedido, ruim)
    if variante == 'outro_turno':
        plano['contrato_fala']['perspectiva_enunciador'] = replace(plano['contrato_fala']['perspectiva_enunciador'], turno_id='outro')
    elif variante == 'dict_proposto':
        plano['contrato_fala']['perspectiva_enunciador'] = {'turno_id': plano['id'], 'texto_usuario': pedido}
    else: plano['requer_execucao'] = True
    q = avaliar_qualidade_comunicacao(pedido, ruim, plano=plano)
    assert 'retomada_usuario_sem_nucleo_conferido' not in q['problemas']


@pytest.mark.parametrize('reparo', ['corrigido', 'invertido', 'timeout'])
def test_composicao_repara_com_fonte_ou_limita_sem_publicar_inversao(reparo):
    fonte, pedido, ruim, boa = CASOS[0]
    plano = plano_com_fonte(fonte, pedido, ruim)
    chamadas = []
    def enviar(mensagens, **opcoes):
        chamadas.append((mensagens, opcoes))
        if reparo == 'timeout': return '__LAYLAY_LLM_TIMEOUT__'
        return json.dumps({'fala': boa if reparo == 'corrigido' else ruim, 'comandos': []})
    saida = preparar_resposta_para_execucao(pedido, json.dumps({'fala': ruim, 'comandos': []}),
        enviar_mensagem_cb=enviar, limpar_texto_fala_cb=lambda f: f,
        fallback_fala='fallback', memoria_sqlite=None,
        contexto_comunicacao={'plano_turno': plano, 'mensagens': [
            {'role': 'user', 'content': fonte}, {'role': 'assistant', 'content': ruim}]}, log=lambda *a: None)
    assert chamadas, 'a inversão atravessou a preparação sem reparo'
    assert saida['fala'] != ruim and not saida['comandos']
    if reparo == 'corrigido': assert saida['fala'] == boa
    if reparo == 'timeout': assert len(chamadas) == 1


def test_reparo_recebe_fonte_literal_sem_reintroduzir_rascunho_como_premissa():
    fonte, pedido, ruim, _ = CASOS[0]
    plano = plano_com_fonte(fonte, pedido, ruim)
    q = avaliar_qualidade_comunicacao(pedido, ruim, plano=plano)
    mensagens = [{'role': 'user', 'content': fonte}, {'role': 'assistant', 'content': ruim},
        *[{'role': 'user', 'content': f'Observei uma nuvem {i}.'} for i in range(5)]]
    reparo = montar_mensagens_reparo_comunicacao(pedido, ruim, q, mensagens=mensagens)
    tarefa = json.loads(reparo[-1]['content'])
    assert 'rascunho_rejeitado' not in tarefa
    assert any(f['role'] == 'user' and f['content'] == fonte for f in tarefa['fontes_dialogo'])


def coletar_factory(perfil: Path, *, reparo_corrigido: bool = False) -> dict:
    # Mesmo composition root isolado já usado para leitura/apoio pessoal;
    # apenas a folha HTTP fornece propostas controladas, nunca o revisor.
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    casos = [(fonte, pedido, fala) for fonte, pedido, ruim, boa in CASOS for fala in [ruim, boa]]
    codigo = CODIGO_FACTORY
    descoberta = 'apps.give_appnames=lambda *a,**k:{}'
    assert codigo.count(descoberta) == 1
    codigo = codigo.replace(descoberta, "apps.give_appnames=lambda *a,**k:['obsidian']")
    if reparo_corrigido:
        bloco = "proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],'comandos':[]}"
        assert codigo.count(bloco) == 1
        # Varia somente a folha de geração no reparo; o revisor permanece real.
        boas = {pedido: f'Você contou: «{fonte}».' for fonte, pedido, _, _ in CASOS}
        novo = ("fala_proposta=rascunho\n"
            "    try:tarefa=json.loads(kwargs['json']['messages'][-1]['content'])\n"
            "    except (ValueError,TypeError):tarefa={}\n"
            "    if isinstance(tarefa,dict) and 'retomada_usuario_sem_nucleo_conferido' in tarefa.get('problemas',[]):\n"
            "        fala_proposta=" + repr(boas) + ".get(tarefa.get('mensagem_atual'),rascunho)\n"
            "    proposta={'suporte_proposicoes':[{'texto':fala_proposta,'fontes':[]}],'comandos':[]}")
        codigo = codigo.replace(bloco, novo)
    r = subprocess.run([sys.executable, '-B', '-c', codigo, str(perfil), json.dumps(casos)],
        cwd=Path(__file__).resolve().parents[2], env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=90)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    return json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('MODO_PESSOAL_JSON=')))


def test_factory_repara_ou_limita_primeira_pessoa_e_preserva_relato_apoiado(tmp_path):
    prova = coletar_factory(tmp_path)
    assert not prova['efeitos'] and not prova['audio_gerado']
    for i, c in enumerate(prova['casos']):
        assert set(c['plano']['contrato_fala']['atos']) == {'pergunta'}
        assert any(f['texto'] == c['fonte'] for f in c['plano']['relatos_usuario'])
        assert len(c['respostas']) == 1
        if i % 2 == 0: assert c['respostas'] != [c['rascunho']], 'inversão publicada na factory'
        else: assert c['respostas'] == [c['rascunho']], 'relato apoiado foi bloqueado'
        assert not c['plano']['autoriza_execucao'] and not c['plano']['comandos']


def test_factory_entrega_reparo_apoiado_apos_rascunho_em_primeira_pessoa(tmp_path):
    prova = coletar_factory(tmp_path, reparo_corrigido=True)
    assert not prova['efeitos'] and not prova['audio_gerado']
    for i, c in enumerate(prova['casos']):
        fonte, _, _, boa = CASOS[i // 2]
        assert c['respostas'] == [f'Você contou: «{fonte}».' if i % 2 == 0 else boa]
        assert not c['plano']['autoriza_execucao'] and not c['plano']['comandos']
        if i % 2 == 0:
            assert len(c['envios']) == 2
            negociado = c['envios'][-1]['response_format']['json_schema']
            assert negociado['name'] == 'autoria_com_suporte_v2'
            unidades = negociado['schema']['properties']['suporte_proposicoes']
            assert unidades['minItems'] == unidades['maxItems'] == 1
            assert f'Você contou: «{fonte}».' in unidades['items']['properties']['texto']['enum']
            assert c['rascunho'] not in unidades['items']['properties']['texto']['enum']
