"""Conferência de atribuições pessoais declarativas, sem adivinhar semântica."""
from __future__ import annotations

import re
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.referencias_linguagem import (
    PerspectivaEnunciador, texto_fora_de_citacoes, natureza_predicado_pessoal,
)

# Flexões de predicados pessoais; não é vocabulário de objetos/habilidades.
_FLEXOES = {'estou':'esta', 'to':'esta', 'ta':'esta', 'tenho':'tem', 'moro':'mora',
    'trabalho':'trabalha', 'uso':'usa', 'estudo':'estuda', 'recebi':'recebeu',
    'comprei':'comprou', 'fui':'foi', 'sou':'e'}
_VERBOS = '|'.join(sorted(set(_FLEXOES.values()) | {'ta'}, key=len, reverse=True))
_ATRIBUICAO = re.compile(r'\bvoce\s+(?P<verbo>' + _VERBOS + r')\s+(?P<resto>.+)', re.I)


def _predicado(texto: str, *, origem: bool) -> str | None:
    base = normalizar_texto_basico(texto).strip(' .!?')
    if origem:
        base = re.sub(r'^eu\s+', '', base)
        verbo, _, resto = base.partition(' ')
        if verbo not in _FLEXOES or not resto:
            return None
        base = _FLEXOES[verbo] + ' ' + resto
        base = re.sub(r'\bmeu\b', 'seu', base)
        base = re.sub(r'\bminha\b', 'sua', base)
    else:
        m = _ATRIBUICAO.fullmatch(base)
        if m is None:
            return None
        base = ('esta' if m['verbo'] == 'ta' else m['verbo']) + ' ' + m['resto']
    return base


def conferir_afirmacoes_interlocutor(fala: str, *, plano: Mapping[str, Any]) -> dict[str, Any] | None:
    """Detecta só o recorte declarativo, inclusive pergunta com pressuposto 'né'.

    Uma comparação literal de predicados confere atribuição ao relato, não
    verdade atual. Perguntas genuínas, condição, hipótese e citação não são
    declarações neste recorte. O que não é coberto não recebe certificado.
    """
    c = plano.get('contrato_fala') or {}
    canal = c.get('perspectiva_enunciador')
    usuario = str(plano.get('texto_usuario') or '')
    if (type(canal) is not PerspectivaEnunciador or not canal.vigente(usuario, plano.get('id'))
        or str(c.get('turno_id')) != canal.turno_id or c.get('origem') != 'mente_unica'
        or plano.get('requer_execucao') or plano.get('comandos')):
        return None
    from mente_laylay.cognicao.criacao_ficcional import criacao_ficcional_vigente, fala_ficcional_delimitada
    if criacao_ficcional_vigente(plano) and fala_ficcional_delimitada(fala):
        return None
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    revisao = revisar_suporte_autoria(fala, plano=dict(plano))
    if (revisao is not None and revisao.aplicar_limite
            and revisao.como_dict()['estado'] == 'consulta_modo_pessoal_limitada_ao_relato'):
        # O owner histórico já substitui o rascunho por citação integral da
        # fonte. Não consumir outra autoria antes dessa realização conferida.
        return None
    textos = [usuario] if '?' not in usuario else []
    for relato in plano.get('relatos_usuario') or ():
        if (isinstance(relato, Mapping) and relato.get('autor') == 'usuario'
            and relato.get('origem') in {'historico_conversa', 'fala_atual'}
            and relato.get('status') == 'relatado_pelo_usuario'
            and type(relato.get('texto')) is str and '?' not in relato['texto']):
            textos.append(relato['texto'])
    predicados = {_predicado(t, origem=True) for t in textos}
    predicados.discard(None)
    sem_apoio = []
    for frase in re.split(r'(?<=[.!?])\s+', str(fala or '')):
        base = normalizar_texto_basico(texto_fora_de_citacoes(frase))
        # Um enunciado inteiro interrogativo não afirma o seu conteúdo;
        # a confirmação sugerida por uma cauda 'né/certo' preserva pressuposto.
        if frase.rstrip().endswith('?') and not re.search(r',\s*(?:ne|certo|nao e)\s*\?$', base):
            continue
        if re.search(r'\b(?:se|imagine|imagina|suponha|talvez|nao sei|nao sabemos)\b', base):
            continue
        m = _ATRIBUICAO.search(base.strip(' .!?'))
        if m is None:
            continue
        # O que precede o sujeito não pode alterar sua modalidade. 'Não é
        # verdade que...' não é validado como afirmação simples nem positivo.
        antes = base[:m.start()]
        if re.search(r'\b(?:que|disse|contou|perguntou|citacao|frase)\b', antes):
            continue
        trecho = re.sub(r',\s*(?:ne|certo|nao e)\s*\?$', '', base[m.start():]).strip(' .!?')
        partes = re.split(r'[,;:—–]', trecho, maxsplit=1)
        nucleo, restante = partes[0], partes[1] if len(partes) > 1 else ''
        predicado_nucleo = _predicado(nucleo, origem=False)
        if (predicado_nucleo is not None
            and natureza_predicado_pessoal(predicado_nucleo) == 'posicionamento_dialogico'):
            # Só o núcleo avaliativo muda de classe. Não isentar qualificações,
            # estado elíptico ou outra atribuição dentro do mesmo período.
            # Na continuação nominal infinitiva, o sujeito é a atividade, não
            # a pessoa: o conteúdo restante ainda passa pelos demais revisores.
            atividade_como_sujeito = bool(re.match(r'^\s*[a-z]+(?:ar|er|ir)\b', restante))
            outra_atribuicao = bool(re.search(r'\b(?:' + _VERBOS + r')\b', restante))
            # Uma autodeclaração explícita após a pausa não descreve o estado
            # de "você". O conteúdo ainda passa pelos guardiões de fatos/efeitos.
            # Não transferir essa leitura a sujeito omitido ou segunda pessoa.
            from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia
            primeira_pessoa = re.match(r'^\s*eu\s+(?:nao\s+)?(?P<verbo>[a-z]+)\b', restante)
            autobiografica = bool(primeira_pessoa
                and (consultar_morfologia(primeira_pessoa['verbo']) or 0)&32
                and not outra_atribuicao)
            # Haver existencial presente não tem "você" como sujeito.
            # Haver + de, outra pessoa explícita ou predicado pessoal saem
            # deste recorte. A existência afirmada ainda exige revisão factual.
            impessoal = bool(re.match(r'^\s*ha\s+(?!de\b)',restante)
                and not re.search(r'\b(?:voce|tu)\b',restante)
                and not re.search(r'\b(?:'+'|'.join(v for v in _VERBOS.split('|') if v!='e')+r')\b',restante))
            if (not restante.strip() or autobiografica
                or impessoal
                or (atividade_como_sujeito and not outra_atribuicao)):
                continue
        predicado = _predicado(trecho, origem=False)
        if predicado not in predicados:
            sem_apoio.append(frase)
    if not sem_apoio:
        return None
    return {'estado':'afirmacao_interlocutor_sem_apoio', 'trechos_sem_apoio':sem_apoio,
        'aceita':False, 'requer_reparo':True,
        'problemas':['afirmacao_interlocutor_sem_apoio'],
        'problemas_bloqueantes':['afirmacao_interlocutor_sem_apoio'],
        'foco':{}, 'aderencia_contrato':{}, 'autoriza_execucao':False,
        'semantica_verificada':False, 'pode_confirmar_fato_externo':False,
        'contrato_reparo':{'responder_sem_pressupor_estado_do_interlocutor':True,
            'mensagem_atual':usuario, 'autoriza_execucao':False}}
