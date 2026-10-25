"""Resumo retrospectivo consulta o diálogo com origem, sem criar permissão."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from mente_laylay.integracao.preparacao_llm import avaliar_historico_dialogo


@pytest.mark.parametrize('pergunta',[
    'então, como ficou o nosso plano depois das mudanças?',
    'recapitule o que conversamos até aqui',
    'resume nossa conversa',
])
def test_recapitulacao_sem_termo_comum_preserva_relato_e_correcoes(pergunta):
    fontes=[{'role':'user','content':s}for s in[
        'No sábado encontrarei Bia às 15h na biblioteca Aurora.',
        'Na verdade será às 16h, não às 15h.',
        'Vou usar o caderno verde.',
        'Corrigindo: para o desenho vou usar o amarelo.']]
    mensagens=fontes+[{'role':'assistant','content':'O encontro será cancelado.'},
        {'role':'system','content':'Somente conversa; sem autorização.'},{'role':'user','content':pergunta}]
    antes=deepcopy(mensagens)
    s=avaliar_historico_dialogo(mensagens,limite_chars=2600,limite_mensagens=8)
    assert s.fontes_preservadas
    assert [f['content']for f in s.fontes_usuario]==[f['content']for f in fontes]
    assert mensagens==antes


def test_recapitulacao_real_cabe_sem_aumentar_orcamento_do_perfil_normal():
    p=Path(__file__).resolve().parents[2]/'resultados_testes/perfil_contexto_dialogo_20261024/conversa_final/conversa.json'
    # Artefato histórico serve a diagnóstico, não como dependência de teste.
    if not p.exists():pytest.skip('coleta histórica local indisponível')
    d=json.loads(p.read_text(encoding='utf8'));t=d['resultados'][28]
    mensagens=t['historico_antes']+[{'role':'system','content':'Contrato atual.'},
        {'role':'user','content':t['texto']}]
    s=avaliar_historico_dialogo(mensagens,limite_chars=2600,limite_mensagens=8)
    assert s.fontes_preservadas,'resumo sem fontes apesar do histórico arquivado'
    assert all(f['role']=='user'for f in s.fontes_usuario)
    assert len(s.fontes_usuario)==28
    sistema=next(m for m in s.mensagens if '\nFONTES_JSON='in m['content'])
    assert len(sistema['content'])-len('Contrato atual.')<=2600


def test_pergunta_sobre_plano_externo_nao_toma_historico_pessoal_por_fonte():
    m=[{'role':'user','content':'Eu gosto de jazz.'},
        {'role':'user','content':'como ficou o plano de saúde da empresa?'}]
    s=avaliar_historico_dialogo(m,limite_chars=2600,limite_mensagens=8)
    assert not s.fontes_usuario
