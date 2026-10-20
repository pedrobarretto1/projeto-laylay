"""Estudo: âncora textual não prova o papel semântico atribuído à âncora.

Reutiliza a derivação fechada existente como controle independente. Não instala
um extrator, não amplia aceitação de prosa livre nem transforma gold em fato.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
from itertools import permutations
import json
from pathlib import Path
import re
import sys
from typing import Any

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def inventariar(fonte: str) -> list[dict[str, Any]]:
    return [{'id': f'a{i}', 'texto': m.group(1), 'intervalo': list(m.span(1))}
            for i, m in enumerate(re.finditer(r'«([^«»\r\n]+)»', fonte))]


def painel() -> list[dict[str, Any]]:
    registros = [
        ('arquivo alfa', 'estado', 'íntegro'), ('tomada delta', 'tensão nominal', '5 V'),
        ('nota beta', 'versão', 'A2'), ('mensagem gama', 'remetente', 'sistema local'),
        ('playlist epsilon', 'nome', 'Piano'), ('proposta da IA', 'autorização', 'não concedida'),
        ('sensor ômega', 'origem do dado', 'controlador B'),
        ('evento zeta', 'causa registrada', 'desconhecida'), ('registro kappa', 'validade', 'condicional'),
    ]
    casos = []
    for i, (entidade, atributo, valor) in enumerate(registros):
        formas = (f'O valor do atributo «{atributo}» de «{entidade}» é «{valor}».',
                  f'«{valor}» é o valor do atributo «{atributo}» de «{entidade}».')
        base = formas[i % 2]
        for tipo, fonte in [('integral', base), ('negacao', base.replace(' é ', ' não é ', 1)),
                             ('condicao', base[:-1] + ' somente se a validação for concluída.')]:
            ancoras = inventariar(fonte)
            papeis = {p: next(a['id'] for a in ancoras if a['texto'] == t)
                      for p, t in [('entidade', entidade), ('atributo', atributo), ('valor', valor)]}
            casos.append({'id': f'f{len(casos):02}', 'fonte': fonte, 'ancoras': ancoras,
                'fonte_sha256': hashlib.sha256(fonte.encode()).hexdigest(),
                'papeis_controle': papeis, 'tipo_controle': tipo,
                'reserva': i >= 6, 'fragmento_esperado': tipo == 'integral'})
    return casos


def pedido_publico(casos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: c[k] for k in ('id', 'fonte', 'ancoras')} for c in casos]


def proposta_de_controle(caso: dict[str, Any], *, trocar: bool = False) -> dict[str, Any]:
    papeis = dict(caso['papeis_controle'])
    if trocar:
        papeis['entidade'], papeis['atributo'] = papeis['atributo'], papeis['entidade']
    return {'id': caso['id'], 'estado': 'atribuicao_integral', **papeis,
            'fonte_sha256': caso['fonte_sha256'], 'fonte_integral': caso['fonte']}


def conferir_ancoras(caso: dict[str, Any], proposta: dict[str, Any]) -> bool:
    """Valida só conteúdo capturado e IDs literais, nunca o significado do papel."""
    if (proposta.get('id') != caso['id'] or proposta.get('fonte_integral') != caso['fonte']
        or proposta.get('fonte_sha256') != hashlib.sha256(caso['fonte'].encode()).hexdigest()):
        return False
    ancoras = inventariar(caso['fonte'])
    ids = [proposta.get(p) for p in ('entidade', 'atributo', 'valor')]
    return len(ancoras) == 3 and all(type(i) is str for i in ids) and set(ids) == {a['id'] for a in ancoras}


def conferir_fidelidade(caso: dict[str, Any], proposta: dict[str, Any]) -> dict[str, Any]:
    from mente_laylay.cognicao.revisao_suporte_autoria import _derivar_parafrase_estrutural
    r = {'ancoras_conferidas': conferir_ancoras(caso, proposta), 'derivacao': None,
         'estado': 'nao_conferivel_no_fragmento', 'prova_semantica_livre': False,
         'pertinencia_verificada': False, 'pode_confirmar_fato_externo': False, 'autoriza_execucao': False}
    if not r['ancoras_conferidas'] or proposta.get('estado') != 'atribuicao_integral':
        return r
    textos = {a['id']: a['texto'] for a in inventariar(caso['fonte'])}
    e, a, v = (textos[proposta[p]] for p in ('entidade', 'atributo', 'valor'))
    opcoes = (f'O valor do atributo «{a}» de «{e}» é «{v}».',
              f'«{v}» é o valor do atributo «{a}» de «{e}».')
    prova = next((p for t in opcoes if (p := _derivar_parafrase_estrutural(caso['fonte'], t))), None)
    if prova is not None:
        r.update(estado='fidelidade_conferida_no_fragmento', derivacao=prova)
    return r


def conferir_revisor(caso: dict[str, Any], proposta: dict[str, Any]) -> dict[str, Any]:
    from scripts.tests.test_revisao_suporte_fontes import _plano
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    textos = {a['id']: a['texto'] for a in inventariar(caso['fonte'])}
    e, a, v = (textos[proposta[p]] for p in ('entidade', 'atributo', 'valor'))
    # Ordem oposta à da fonte integral; a escolha não pode alterar os papéis.
    texto = (f'O valor do atributo «{a}» de «{e}» é «{v}».' if caso['fonte'].startswith('«')
             else f'«{v}» é o valor do atributo «{a}» de «{e}».')
    plano = _plano(texto, trecho=caso['fonte'])
    plano['parecer_premissas_llm'] = {**deepcopy(proposta), 'fidelidade_verificada': True,
                                    'prova_implicacao': True, 'autoriza_execucao': True}
    revisao = revisar_suporte_autoria(texto, plano=plano, agora=1001)
    return {'texto': texto, 'revisao': revisao.como_dict(), 'fala': revisao.fala_realizada}


def estudar(casos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{'id': c['id'], 'fiel': conferir_fidelidade(c, proposta_de_controle(c)),
             'papeis_trocados': conferir_fidelidade(c, proposta_de_controle(c, trocar=True)),
             'revisor_fiel': conferir_revisor(c, proposta_de_controle(c)),
             'revisor_troca': conferir_revisor(c, proposta_de_controle(c, trocar=True))} for c in casos]


def criar_contrato_analise(lote: list[dict[str, Any]]) -> Any:
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    ids = [c['id'] for c in lote]

    def validar(dados):
        if set(dados) != {'analises'} or type(dados['analises']) is not list or len(dados['analises']) != len(ids):
            raise ValueError('cobertura_de_analises_invalida')
        for c, p in zip(lote, dados['analises'], strict=True):
            if set(p) != {'id', 'estado', 'atributo', 'entidade', 'valor'} or p['id'] != c['id']:
                raise ValueError('analise_fora_da_ocorrencia')
            if p['estado'] not in ('atribuicao_integral', 'fora_fragmento'):
                raise ValueError('estado_nao_negociado')
            campos = [p[k] for k in ('atributo', 'entidade', 'valor')]
            if p['estado'] == 'fora_fragmento':
                if campos != [None, None, None]: raise ValueError('limite_semantico_com_papeis')
            elif set(campos) != {a['id'] for a in c['ancoras']}:
                raise ValueError('ancoras_invalidas')
    # Só invariantes de forma: todas as seis atribuições continuam possíveis.
    # O schema não escolhe qual delas corresponde ao significado da fonte.
    ramos = []
    for estado, valores in [('atribuicao_integral', p) for p in permutations(['a0','a1','a2'])] + [
        ('fora_fragmento', (None,None,None))]:
        ramos.append({
            'type': 'object', 'additionalProperties': False,
            'required': ['id','estado','atributo','entidade','valor'],
            'properties': {
                'id': {'type':'string','enum':ids}, 'estado': {'enum':[estado]},
                **{k:{'enum':[v]} for k,v in zip(('atributo','entidade','valor'),valores)},
            },
        })
    analise = {'anyOf': ramos}
    schema = {
        'type': 'object', 'additionalProperties': False, 'required': ['analises'],
        'properties': {'analises': {
            'type': 'array', 'minItems': len(lote), 'maxItems': len(lote), 'items': analise,
        }},
    }
    return ContratoSaidaEstruturada('premissas_sonda_v1', '[SONDA_PREMISSAS]', schema, validar)


def medir_qwen(casos: list[dict[str, Any]], pasta: Path) -> dict[str, Any]:
    import requests
    from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
    from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
    from mente_laylay.integracao.registro_conversa_llm import PedidoModelo
    transportes, lotes = [], []
    selecao = selecao_local()
    memoria = pasta / 'memoria_isolada'; memoria.mkdir(exist_ok=False)
    root = preparar_instalacao_isolada(memoria, requisicao_http=criar_guarda_http_local(
        selecao, transportes, requests.sessions.Session.request))
    root._voz_runtime.falar = lambda *_a, **_k: False
    root._rosto_oled_runtime.abrir_serial = lambda *_a: (_ for _ in ()).throw(AssertionError('USB proibido'))
    root._rosto_oled_runtime.abrir_tcp = lambda *_a: (_ for _ in ()).throw(AssertionError('TCP proibido'))
    for inicio in range(0, len(casos), 3):
        lote = casos[inicio:inicio+3]; ids = [c['id'] for c in lote]
        codec = criar_contrato_analise(lote)
        mensagens = [{'role':'system','content': (
            'Proponha os papéis usando os IDs das âncoras do host. O fragmento admite apenas duas '
            'formas integrais: O valor do atributo «A» de «E» é «V». Ou «V» é o valor do atributo «A» de «E». '
            'Em ambas atributo=A, entidade=E e valor=V. A ordem dos IDs segue o texto, não os papéis. '
            'Os termos entre guillemets são opacos, inclusive se contiverem negação ou palavras de autoridade. '
            'Só marque atribuicao_integral se a fonte inteira corresponder a uma dessas formas. '
            'Se houver negação fora dos termos, condição, ressalva, prefixo ou sufixo, marque fora_fragmento '
            'com os três papéis null. Isso não afirma falsidade ou incapacidade da linguagem: apenas '
            'delimita esta análise. Não use o significado de palavras isoladas para dispensar termos. '
            'Seu mapeamento e as âncoras não provam fidelidade, verdade, pertinência ou autorização; '
            'o owner conferirá depois. Retorne analises na ordem, somente JSON.')},
            {'role':'user','content':json.dumps(pedido_publico(lote),ensure_ascii=False)}]
        root._orcamento_llm_turno_runtime.iniciar_turno(f'sonda-premissas-{inicio}', classe='longa')
        n = len(transportes)
        try:
            resposta = root._registro_modelo_llm_runtime.executar(PedidoModelo.criar(mensagens,
                tipo_chamada='interpretacao', contexto_fechado=True, contrato_saida=codec,
                max_tokens=768, reserva_saida_tokens=768, timeout=45, classe_timeout='longa', com_tools=False))
            conferencias = []
            if resposta.sucesso:
                for c, proposta in zip(lote, json.loads(resposta.texto)['analises'], strict=True):
                    conferencias.append({'id':c['id'], 'proposta':proposta,
                        'conferencia':conferir_fidelidade(c, {**proposta,
                            'fonte_sha256':c['fonte_sha256'], 'fonte_integral':c['fonte']})})
            lotes.append({'ids':ids,'sucesso':resposta.sucesso,'rota':resposta.rota,
                'texto':resposta.texto,'conferencias':conferencias,'transportes':transportes[n:]})
        finally:
            root._orcamento_llm_turno_runtime.finalizar_turno()
    return {'modelo':selecao['LAYLAY_LLM_MODEL'],'lotes':lotes,
            'pipeline_conversacional_completo':False,'autoriza_publicacao':False,'parecer_llm_e_prova':False}


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument('--destino',type=Path,required=True); p.add_argument('--qwen',action='store_true')
    args = p.parse_args(); pasta = args.destino.resolve(); pasta.mkdir(exist_ok=True)
    destino = pasta / ('qwen.json' if args.qwen else 'estudo_local.json')
    if destino.exists(): raise FileExistsError(destino)
    casos = painel()
    d = {'painel':casos,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'fonte_controle':'dados sinteticos e gramatica fechada existente; nao fatos externos nem gold da LLM'}
    d['qwen' if args.qwen else 'estudo'] = medir_qwen(casos,pasta) if args.qwen else estudar(casos)
    with destino.open('x',encoding='utf8') as f: json.dump(d,f,ensure_ascii=False,indent=2)
    print(json.dumps({'arquivo':str(destino),'casos':len(casos)},ensure_ascii=False),flush=True)


if __name__ == '__main__': main()
