"""Finalidade de formular uma fala, sem conferir fatos no texto proposto."""
from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import tipo_transformacao_conversacional
from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
from mente_laylay.cognicao.referencias_linguagem import texto_fora_de_citacoes, enunciados_discursivos
from mente_laylay.personalidade.proporcao_resposta import classificar_proporcao

_FINALIDADES_DIVERGENTES = frozenset({'explicacao_ocorrencia','explicacoes_historicas_por_ato',
    'evidencia_fala_historica','revisao_alegacao','opiniao_autoral','adequacao_pessoal','criacao_ficcional'})

_CONSULTA_FORMULACAO = re.compile(
    r'\b(?:qual|que)\s+(?:frase|resposta|mensagem|pergunta|texto|palavras)\b'
    r'[^.!?;]*\b(?:diria|falaria|escreveria|perguntaria|responderia)\b', re.I,
)

_CONSULTA_ACRESCIMO = re.compile(
    r'(?:qual|que)\s+(?:frase|mensagem|texto)(?:\s+[^\W\d_]+){0,3}?\s+'
    r'(?:voc[eê]\s+)?(?:acrescentaria|escreveria|sugeriria|proporia)\s*\?', re.I)


@dataclass(frozen=True, slots=True)
class RetificacaoRedacao:
    turno_id: str
    texto_usuario: str
    negacao_ocorrencia: str
    autoriza_execucao: bool = field(default=False, init=False)
    comprova_efeito: bool = field(default=False, init=False)

    def instrucao(self) -> str:
        return (f'O usuário corrigiu a ocorrência: «{self.negacao_ocorrencia}». '
                'Reconheça essa correção literalmente numa frase, sem repetir a cena como lembrança. '
                'Depois proponha a redação pedida, identificando-a como proposta: '
                'Eu acrescentaria/escreveria/sugeriria: «texto proposto». '
                'A proposta não é relato de experiência nem prova de fato. Não acrescente alegações fora dela.')

    def aceita(self, fala: str) -> bool:
        from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
        forma = re.fullmatch(r'(?P<reconhecimento>[^.!?]+)[.!]\s+'
            r'(?:Eu )?(?:acrescentaria|escreveria|sugeriria|proporia):\s*«(?P<proposta>[^«»]+)»[.!]?',
            fala.strip(), re.I)
        if forma is None:
            return False
        reconhecida = re.sub(r'^(?:voc[eê] tem raz[aã]o|entendi|certo|correto)\s*:\s*',
                             '', forma['reconhecimento'], flags=re.I)
        return (normalizar_texto_basico(reconhecida) == normalizar_texto_basico(self.negacao_ocorrencia)
                and bool(forma['proposta'].strip()))


def construir_retificacao_redacao(texto: str, *, plano: Mapping[str, Any]) -> RetificacaoRedacao | None:
    if (not plano.get('id') or plano.get('texto_usuario') != texto
            or plano.get('autoriza_execucao') is not False or plano.get('requer_execucao') or plano.get('comandos')):
        return None
    # A citação permanece dado, mas seu ponto final ainda pode separar a
    # consulta seguinte. Não apagar essa fronteira junto com o conteúdo.
    from mente_laylay.cognicao.referencias_linguagem import intervalos_citados
    externo = texto
    for inicio, fim in reversed(intervalos_citados(texto)):
        delimitador = '.' if texto[inicio:fim][-2:-1] in '.!?' else ''
        externo = externo[:inicio] + ' [citacao]' + delimitador + ' ' + externo[fim:]
    partes = enunciados_discursivos(externo)
    if not partes or _CONSULTA_ACRESCIMO.fullmatch(partes[-1].strip()) is None:
        return None
    negacoes = []
    for parte in partes[:-1]:
        m = re.match(r'^(?:S[oó] um detalhe:\s*)?(?P<negacao>n[aã]o\s+'
            r'(?:houve|ocorreu|aconteceu)\s+(?:esse|essa|este|esta)\s+[^,;.!?]+)(?:[,;.!]|$)', parte, re.I)
        if m is not None:
            negacoes.append(m['negacao'])
    if len(negacoes) != 1:
        return None
    return RetificacaoRedacao(str(plano['id']), texto, negacoes[0])


def retificacao_redacao_vigente(plano: Mapping[str, Any]) -> RetificacaoRedacao | None:
    contrato = plano.get('contrato_fala') or {}
    fonte = contrato.get('retificacao_redacao')
    if (type(fonte) is RetificacaoRedacao and str(plano.get('id')) == fonte.turno_id
            and contrato.get('origem') == 'mente_unica' and str(contrato.get('turno_id')) == fonte.turno_id
            and contrato.get('autoriza_execucao') is False
            and fonte == construir_retificacao_redacao(str(plano.get('texto_usuario') or ''), plano=plano)):
        return fonte
    return None


@dataclass(frozen=True, slots=True)
class RedacaoDiscursiva:
    turno_id: str
    texto_usuario: str
    intervalo_pedido: tuple[int, int]
    intervalo_consulta: tuple[int, int]
    autoriza_execucao: bool = field(default=False, init=False)
    pode_confirmar_fato_externo: bool = field(default=False, init=False)


def construir_redacao_discursiva(texto: str, *, turno: Mapping[str, Any],
    plano: Mapping[str, Any], contrato: Mapping[str, Any]) -> RedacaoDiscursiva | None:
    """Reusa os atos e fontes do owner canônico, nunca o perfil de tamanho.

    Recorte explícito: conflito do roteiro matemático com uma consulta de
    formulação seguida de redação no canal atual. O perfil só demonstra
    elegibilidade para corrigir esse conflito, nunca a finalidade ou o fato.
    Outras perguntas/instruções ou fontes históricas não
    herdam essa finalidade; não há continuidade inferida da fala do modelo.
    """
    if (not plano.get('id') or plano.get('autoriza_execucao') is True
        or plano.get('requer_execucao') or plano.get('comandos')
        or str(contrato.get('turno_id')) != str(plano['id'])
        or contrato.get('origem') != 'mente_unica'
        or _FINALIDADES_DIVERGENTES.intersection(contrato)
        or (contrato.get('roteiro_concreto') or {}).get('estrategia') != 'explicacao_didatica'
        or classificar_proporcao(texto) != 'matematica'):
        return None
    segmentos = turno.get('segmentos') or ()
    fontes = fontes_textuais_dos_segmentos(texto, segmentos)
    if len(fontes) != len(segmentos) or len(fontes) < 2:
        return None
    redacoes, consultas = [], []
    for segmento, fonte in zip(segmentos, fontes):
        f = fonte.como_dict()
        trecho = f['texto_original']
        if segmento.get('autoriza_execucao') or segmento.get('natureza_acao') == 'instrucao_ou_explicacao':
            return None
        if (segmento.get('natureza_acao') == 'transformacao_conversacional'
            and tipo_transformacao_conversacional(trecho) == 'redacao'):
            redacoes.append(tuple(f['intervalo']))
        elif _CONSULTA_FORMULACAO.search(texto_fora_de_citacoes(trecho)):
            consultas.append(tuple(f['intervalo']))
        elif segmento.get('modalidade') not in {'conversa','correcao'}:
            return None
    if len(redacoes) != 1 or len(consultas) != 1 or redacoes[0][0] < consultas[0][1]:
        return None
    return RedacaoDiscursiva(str(plano['id']), texto, redacoes[0], consultas[0])


def redacao_discursiva_vigente(plano: Mapping[str, Any]) -> RedacaoDiscursiva | None:
    c = plano.get('contrato_fala') or {}
    f = c.get('redacao_discursiva')
    if (type(f) is not RedacaoDiscursiva or not plano.get('id')
        or f.turno_id != str(plano['id']) or f.texto_usuario != plano.get('texto_usuario')
        or str(c.get('turno_id')) != f.turno_id or c.get('origem') != 'mente_unica'
        or c.get('autoriza_execucao') is not False or plano.get('autoriza_execucao') is True
        or plano.get('requer_execucao') or plano.get('comandos')
        or _FINALIDADES_DIVERGENTES.intersection(c)):
        return None
    i, j = f.intervalo_pedido
    a, b = f.intervalo_consulta
    if not (0 <= a < b <= i < j <= len(f.texto_usuario)
        and tipo_transformacao_conversacional(f.texto_usuario[i:j]) == 'redacao'
        and _CONSULTA_FORMULACAO.search(texto_fora_de_citacoes(f.texto_usuario[a:b]))):
        return None
    return f


def conferir_redacao_nao_assertiva(texto: str, *, plano: Mapping[str, Any]) -> dict[str, Any] | None:
    """Confere uma proposta integral de verificação, não a verdade da conta.

    Gramática fechada de ato não assertivo: nenhuma causa, conclusão factual,
    operação executada ou oração extra recebe suporte por usar 'eu diria'.
    Outras formulações permanecem na revisão normal, com suas fontes.
    """
    retificacao = retificacao_redacao_vigente(plano)
    if retificacao is not None and retificacao.aceita(texto):
        from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel
        proposta = texto.split('«', 1)[1].rsplit('»', 1)[0].strip().rstrip('.!')
        # Reconhecimento literal não dá suporte a qualquer alegação colocada
        # entre aspas. Somente redação nominal; orações seguem revisão normal.
        if not all(grupo_nominal_de_papel(p.strip()) for p in proposta.split(',')):
            return None
        return {'tipo_ato': 'retificacao_com_proposta', 'ato_conferido': True,
            'fonte': {'tipo': 'utterance_atual', 'texto': retificacao.negacao_ocorrencia,
                      'turno_id': retificacao.turno_id},
            'realizacao': {'texto': texto, 'escopo': 'correcao_literal_e_proposta_delimitada'},
            'estado_real_verificado': False, 'semantica_verificada': False, 'prova_implicacao': False,
            'pode_confirmar_fato_externo': False, 'autoriza_execucao': False}
    pergunta = conferir_pergunta_de_escolha(texto, plano=plano)
    if pergunta is not None:
        return pergunta
    f = redacao_discursiva_vigente(plano)
    if f is None:
        return None
    moldura = re.fullmatch(r'Eu (?:diria|perguntaria|sugeriria):\s*(?P<corpo>.+)', texto)
    if moldura is None:
        return None
    corpo = moldura['corpo']
    if corpo.startswith('«') and corpo.endswith('».'):
        corpo = corpo[1:-2]
    if not re.fullmatch(
        r'(?:[Vv]amos|[Pp]odemos|[Pp]oderíamos) (?:conferir|verificar|rever|checar) '
        r'(?:isso|isto|(?:a|essa|esta) (?:conta|equação|informação|afirmação|conclusão)|'
        r'(?:os|esses|estes) dados|(?:as|essas|estas) informações)'
        r'(?: juntos)?(?: antes de (?:decidir|concluir|tomar (?:a|essa) decisão))?[.?]', corpo,
    ):
        return None
    i, j = f.intervalo_pedido
    return {'tipo_ato':'redacao_nao_assertiva','ato_conferido':True,
        'fonte':{'tipo':'utterance_atual','texto':f.texto_usuario[i:j],'intervalo':[i,j],
                 'turno_id':f.turno_id},
        'realizacao':{'texto':texto,'escopo':'proposta_de_verificacao'},
        'estado_real_verificado':False,'semantica_verificada':False,'prova_implicacao':False,
        'pode_confirmar_fato_externo':False,'autoriza_execucao':False}


def conferir_pergunta_de_escolha(texto: str, *, plano: Mapping[str, Any]) -> dict[str, Any] | None:
    """Confere escolha hipotética sem qualificador factual ou oração acrescentada."""
    from mente_laylay.cognicao.quantidade_perguntas import pergunta_solicitada_vigente
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel
    from mente_laylay.cognicao.contrato_fala import explicacao_exige_apoio_individual
    pedido = pergunta_solicitada_vigente(plano)
    if (pedido is None or not pedido.aceita(texto) or explicacao_exige_apoio_individual(plano)
            or plano.get('natureza_entrada') == 'evento'):
        return None
    forma = re.fullmatch(
        r'(?:[\w]+(?: [\w]+)?,\s*)?(?:[Qq]ual|[Qq]ue) (?P<objeto>[^\W\d_]+) '
        r'(?:você|voce|tu) (?:escolheria|preferiria|proporia|mudaria)\?', texto)
    hipotetica = False
    if forma is None or not grupo_nominal_de_papel(forma['objeto']):
        hipotetica = _pergunta_condicional_de_criacao(texto, pedido.texto_usuario)
        if not hipotetica:
            return None
    return {'tipo_ato': 'pergunta_de_escolha', 'ato_conferido': True,
        'fonte': {'tipo': 'utterance_atual', 'texto': pedido.texto_usuario, 'turno_id': pedido.turno_id},
        'realizacao': {'texto': texto, 'escopo': ('criacao_condicionada_ao_pedido' if hipotetica
                                                else 'escolha_hipotetica_sem_afirmacao')},
        'estado_real_verificado': False, 'semantica_verificada': False, 'prova_implicacao': False,
        'pode_confirmar_fato_externo': False, 'autoriza_execucao': False}


def _pergunta_condicional_de_criacao(texto: str, pedido: str) -> bool:
    """Hipótese nominal do usuário, consequência irrealis e fala futura citada.

    Confere o alcance integral da pergunta; não prova existência, experiência
    ou efeito. A hipótese precisa estar no pedido, nunca só na proposta da IA.
    Relativa passada, explicação causal e oração externa não pertencem ao recorte.
    """
    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia, grupo_nominal_de_papel
    from mente_laylay.cognicao.referencias_linguagem import intervalos_citados
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico

    corpo = texto.strip()
    while corpo and (corpo[-1].isspace() or unicodedata.category(corpo[-1]) in {'So', 'Sk', 'Mn'}):
        corpo = corpo[:-1]
    forma = re.fullmatch(
        r'[Ss]e eu tivesse (?P<hipotese>uma? [^,;.!?]+), (?:qual|que) seria '
        r'(?P<resultado>[^,;.!?]+?) que (?:ele|ela) faria quando (?:você|voce|tu) perguntar '
        r'(?P<citacao>.+)\?', corpo)
    if forma is None:
        return False
    hipotese = forma['hipotese']
    nominal = hipotese.split()
    if (len(nominal) < 2 or len(nominal) > 5
            or not re.fullmatch(r'[^\W\d_]+', nominal[1])
            or any(not (consultar_morfologia(p) or 0) & 2 for p in nominal[2:])):
        return False
    # O nome pode ser uma entidade fornecida pelo usuário. A repetição só
    # vincula o antecedente hipotético, sem torná-lo fato verificável.
    antecedentes = re.findall(r'\bse eu tivesse ([^,;.!?]+),',
        normalizar_texto_basico(texto_fora_de_citacoes(pedido)))
    if normalizar_texto_basico(hipotese) not in antecedentes:
        return False
    resultado = re.sub(r'\s+(?:mais|menos)\s+(?=[^\W\d_]+$)', ' ', forma['resultado'])
    if not grupo_nominal_de_papel(resultado):
        return False
    citacao = forma['citacao']
    return intervalos_citados(citacao) == ((0, len(citacao)),)
