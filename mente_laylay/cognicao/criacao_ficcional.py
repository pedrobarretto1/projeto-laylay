"""Escopo de criação atribuído ao pedido, sem provar fatos ou efeitos reais."""
from __future__ import annotations

from dataclasses import dataclass, field
import re
import time
from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.referencias_linguagem import (
    referencia_explicacao_historica, texto_fora_de_citacoes, texto_tem_referencia_contextual,
    contem_moldura_narrativa, enunciados_discursivos,
)

_HISTORICAS = frozenset({'explicacoes_historicas_por_ato', 'explicacao_ocorrencia',
                       'evidencia_fala_historica', 'revisao_alegacao'})
_PEDIDO_PROXIMO_ACONTECIMENTO = re.compile(
    r'(?:(?:na|nesta|nessa) (?:história|ficção),\s+)?(?:'
    r'(?:qual (?:é|seria|vai ser)|conte|narre|descreva) o próximo (?:acontecimento|evento|passo) '
    r'(?:desta|dessa|da nossa)|(?:e )?o que (?:acontece|aconteceria) (?:depois|a seguir) '
    r'(?:nesta|nessa|na nossa)) (?:história|ficção)[.!?]*', re.I)
_PREMISSA_CONTINUACAO = re.compile(r'(?:suponha|suponhamos|imagine|imagina|digamos) que ([^.!?;]+)[.!]*', re.I)
_CONECTOR_DE_OUTRA_ORACAO = re.compile(r'\b(?:e|ou|mas|porém|enquanto|então|depois|senão|em seguida)\b', re.I)
_ADJUNTO_DE_CENA = re.compile(r'(?:com|sem|sob|sobre|entre|no|na|nos|nas)\b', re.I)
_REACAO_DE_SURPRESA = re.compile(
    r'(?:h(?:a|e)){2,}|k{3,}|(?:h(?:a|e)){2,},\s+(?:você|isso) me '
    r'(?:surpreendeu|pegou (?:de surpresa|desprevenid[oa]))', re.I)
_COPULAS_E_MODALIZADORES = frozenset({
    'é', 'era', 'foi', 'será', 'seria', 'está', 'estava', 'estaria', 'parece', 'parecia',
    'tem', 'tinha', 'teria', 'pode', 'podia', 'poderia', 'deve', 'devia', 'deveria',
})
_RAIZ_REGULAR = re.compile(r'([^\W\d_]{3,}?)(?:a|e|ou|eu|iu)')

# Classes do índice compartilhado de morfologia_oracao.
_NOME, _VERBO, _INDICATIVO_3S = 1, 32, 256


@dataclass(frozen=True, slots=True)
class CriacaoFiccional:
    turno_id: str
    texto_usuario: str
    turno_origem: str
    pedido_origem: str
    recorte_proximo_acontecimento: str = ''
    autoriza_execucao: bool = field(default=False, init=False)
    pode_confirmar_fato_externo: bool = field(default=False, init=False)


def criacao_ficcional_vigente(plano: Mapping[str, Any]) -> CriacaoFiccional | None:
    contrato = plano.get('contrato_fala') or {}
    fonte = contrato.get('criacao_ficcional')
    if (type(fonte) is not CriacaoFiccional or not plano.get('id')
        or fonte.turno_id != str(plano['id']) or fonte.texto_usuario != plano.get('texto_usuario')
        or str(contrato.get('turno_id')) != fonte.turno_id or contrato.get('origem') != 'mente_unica'
        or contrato.get('autoriza_execucao') is not False or plano.get('autoriza_execucao') is True
        or plano.get('comandos') or plano.get('requer_execucao') or _HISTORICAS.intersection(contrato)):
        return None
    return fonte


def _reacao_sem_novo_pedido(enunciado: str) -> bool:
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel

    corpo = enunciado.rstrip(' .!?')
    if _REACAO_DE_SURPRESA.fullmatch(corpo):
        return True
    return bool(enunciado.endswith(('?!', '!?')) and all(
        grupo_nominal_de_papel(grupo) for grupo in re.split(r'\s+(?:com|sem)\s+', corpo, maxsplit=1)))


def _palavras(texto: str) -> list[str]:
    return re.findall(r'[^\W\d_]+', texto.casefold())


def _predicado_narrativo(palavras: list[str], classe: int) -> str:
    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia, grupo_nominal_de_papel

    for i, palavra in enumerate(palavras[1:9], start=1):
        if ((palavra in _COPULAS_E_MODALIZADORES or (consultar_morfologia(palavra) or 0) & classe)
            and grupo_nominal_de_papel(' '.join(palavras[:i]))):
            return palavra
    return ''


def _premissa_do_proximo_acontecimento(enunciado: str) -> str:
    premissa = _PREMISSA_CONTINUACAO.fullmatch(enunciado)
    if premissa is None or _CONECTOR_DE_OUTRA_ORACAO.search(premissa[1]):
        return ''
    partes = re.split(r',\s*', premissa[1])
    if (not _predicado_narrativo(_palavras(partes[0]), _VERBO)
        or not all(_ADJUNTO_DE_CENA.match(adjunto) for adjunto in partes[1:])):
        return ''
    return premissa[1]


def construir_criacao_ficcional(texto: str, *, plano: Mapping[str, Any],
    contrato: Mapping[str, Any], mente: Mapping[str, Any]) -> CriacaoFiccional | None:
    """Leitura limitada de moldura explícita ou continuação imediata vinculada.

    A fala da IA não escolhe o escopo. A continuidade exige o pedido anterior
    do usuário e seu contrato nativo, na mesma entrada recente. Não há busca
    retroativa por um tema conveniente depois de mudança de assunto.
    """
    if (not plano.get('id') or plano.get('autoriza_execucao') is True or plano.get('comandos')
        or plano.get('requer_execucao') or _HISTORICAS.intersection(contrato)
        or contrato.get('opiniao_autoral') or contrato.get('adequacao_pessoal')):
        return None
    from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual
    if classificar_atualidade_factual(texto)['depende_atualidade']:
        # Uma consulta mutável independente conserva a revisão factual. O
        # classificador canônico já separa os enunciados; não duplicar aqui
        # listas de assuntos nem fazer da narrativa licença para outro ato.
        return None
    base = normalizar_texto_basico(texto_fora_de_citacoes(texto))
    if (referencia_explicacao_historica(texto)
        or re.search(r'\b(?:mundo real|na realidade|de verdade|realmente|real|fontes?|evidencias?)\b', base)):
        return None
    enunciados = enunciados_discursivos(texto_fora_de_citacoes(texto))
    proximos = [i for i, trecho in enumerate(enunciados) if _PEDIDO_PROXIMO_ACONTECIMENTO.fullmatch(trecho)]
    if proximos:
        # O próprio turno fixa uma premissa antes da pergunta singular. Um
        # eco nominal exclamativo não pede consulta, mas outra oração não
        # recebe a licença de ficção da continuação.
        if len(enunciados) < 2 or proximos != [len(enunciados) - 1]:
            return None
        recorte = _premissa_do_proximo_acontecimento(enunciados[-2])
        if not recorte or not all(map(_reacao_sem_novo_pedido, enunciados[:-2])):
            return None
        return CriacaoFiccional(str(plano['id']), texto, str(plano['id']), texto,
                              recorte_proximo_acontecimento=recorte)
    for ato in plano.get('atos') or ():
        if (isinstance(ato, Mapping) and ato.get('tipo') == 'pergunta'
            and not contem_moldura_narrativa(str(ato.get('texto') or ''))
            and not texto_tem_referencia_contextual(str(ato.get('texto') or ''))):
            # A classificação canônica já separou a consulta independente.
            # Sem moldura ou referência textual ao cenário, o convite de outro
            # ato não lhe concede escopo, inclusive para fatos estáveis.
            return None
    # Recorte conservador: uma nova instrução didática independente não
    # recebe a moldura de uma frase narrativa anterior. Não é certificação
    # semântica de pedidos mistos; os não cobertos conservam a revisão factual.
    if re.search(r'[.!?;]\s*(?:agora\s+)?(?:(?:me\s+)?'
        r'(?:explica|explique|ensina|ensine|detalha|detalhe)|como funciona)\b', base):
        return None
    explicita = contem_moldura_narrativa(base) or bool(re.search(
        r'\b(?:estamos|estou)\s+(?:criando|inventando|imaginando|escrevendo)\s+'
        r'(?:uma|a|nossa)\s+(?:historia|ficcao|aventura)\s+(?:em\s+que|onde|sobre)\b|'
        r'\b(?:historia|aventura)\s+ficticia\b|\b(?:mundo|cenario)\s+(?:imaginario|ficticio)\b', base)
        or re.search(r'^(?:invente|crie|conte|escreva|imagine|imagina)\b.+\b(?:historia|conto|ficcao|personagem)\b', base)
        # O pedido pode vir depois de uma reação e nomear uma parte da obra.
        # Abertura/desfecho continuam sendo criação, não consulta histórica.
        # Restringir ao convite afirmativo do usuário, fora de citações.
        or re.search(r'(?:^|[.!?;]\s*)vamos\s+(?:usar\s+(?:isso|essa ideia)\s+para\s+)?'
            r'(?:criar|escrever|inventar)\s+(?:uma?|a|o)\s+'
            r'(?:(?:abertura|cena|desfecho|final)\s+de\s+)?(?:historia|conto|ficcao)\b', base))
    if explicita:
        return CriacaoFiccional(str(plano['id']), texto, str(plano['id']), texto)
    anterior = mente.get('contrato_fala_atual') or {}
    if not isinstance(anterior, Mapping):
        return None
    entrada = mente.get('ultima_entrada')
    fonte = criacao_ficcional_vigente({'id':anterior.get('turno_id'), 'texto_usuario':entrada,
        'contrato_fala':anterior})
    try:
        idade = time.time() - float(mente.get('ultima_entrada_ts') or 0)
    except (ValueError, TypeError, OverflowError):
        return None
    # Reutiliza a leitura referencial comum, sem uma lista de frases de
    # continuação. Uma pergunta independente não herda o assunto anterior.
    continuacao = (texto_tem_referencia_contextual(texto)
        and plano.get('dominio') == 'conversa')
    if fonte is None or not 0 <= idade <= 240 or not continuacao:
        return None
    return CriacaoFiccional(str(plano['id']), texto, fonte.turno_origem, fonte.pedido_origem)


def fala_ficcional_delimitada(fala: str) -> bool:
    """Confere só a moldura integral; não certifica semântica, fatos ou causas."""
    return bool(fala.startswith('Na história, ') and len(fala) > len('Na história, ')
        and not re.search(r'\b(?:no mundo real|na realidade|de verdade|realmente|fora da hist[oó]ria)\b', fala, re.I))


def fala_ficcional_em_bloco(fala: str) -> bool:
    """Escopo textual fechado, sem certificar a verdade do conteúdo citado.

    O prefixo legado não delimita onde acaba uma narrativa de várias frases.
    Para dispensar revisão factual do corpo, toda a criação deve estar em um
    único bloco citado; nenhum texto fora dele recebe a licença de ficção.
    A autora fornece os delimitadores, sem reescrita posterior pelo host.
    """
    abertura = 'Na história, «'
    return bool(fala_ficcional_delimitada(fala) and fala.startswith(abertura)
        and fala.endswith('»') and fala[len(abertura):-1].strip()
        and '«' not in fala[len(abertura):] and '»' not in fala[:-1])


def fala_ficcional_conferida(fala: str, *, criacao: CriacaoFiccional) -> bool:
    """Confere moldura e, quando solicitado, uma oração que avance o recorte."""
    if not criacao.recorte_proximo_acontecimento:
        return fala_ficcional_delimitada(fala)
    if not fala_ficcional_em_bloco(fala):
        return False
    corpo = texto_fora_de_citacoes(fala.removeprefix('Na história, «')[:-1]).strip().removesuffix('.')
    if re.search(r'[.!?,;:\n]', corpo) or _CONECTOR_DE_OUTRA_ORACAO.search(corpo):
        return False

    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia

    palavras_premissa = _palavras(criacao.recorte_proximo_acontecimento.partition(',')[0])
    ancoras = {palavra for palavra in _palavras(criacao.recorte_proximo_acontecimento)
               if len(palavra) >= 3 and (consultar_morfologia(palavra) or 0) & _NOME}
    palavras = _palavras(corpo)
    if not ancoras.intersection(palavras):
        return False
    proximo = _predicado_narrativo(palavras, _INDICATIVO_3S)
    if not proximo or proximo in _COPULAS_E_MODALIZADORES:
        return False
    anterior = _predicado_narrativo(palavras_premissa, _VERBO)
    # A flexão regular de subjuntivo para indicativo não é um novo evento.
    return _RAIZ_REGULAR.sub(r'\1', proximo) != _RAIZ_REGULAR.sub(r'\1', anterior)


@dataclass(frozen=True, slots=True)
class ConsultaRealidadeNarrativa:
    """Consulta do estatuto discursivo de uma criação vigente, não do mundo."""
    turno_id: str
    texto_usuario: str
    criacao_origem: CriacaoFiccional
    autoriza_execucao: bool = field(default=False, init=False)
    pode_confirmar_fato_externo: bool = field(default=False, init=False)

    def realizacoes(self) -> tuple[str, ...]:
        return (
            'Isso faz parte da história que estamos criando. Não confirma um acontecimento no mundo real.',
            'É parte da nossa ficção. A história não comprova que isso aconteceu de verdade.',
        )


def construir_consulta_realidade_narrativa(texto: str, *, plano: Mapping[str, Any],
    contrato: Mapping[str, Any], mente: Mapping[str, Any]) -> ConsultaRealidadeNarrativa | None:
    """Consulta integral com alternativas real/ficção; não absorve outro pedido."""
    if (not plano.get('id') or plano.get('autoriza_execucao') is True or plano.get('comandos')
            or plano.get('requer_execucao') or _HISTORICAS.intersection(contrato)):
        return None
    base = normalizar_texto_basico(texto_fora_de_citacoes(texto)).strip(' .!?')
    if not re.fullmatch(
        r'(?:(?:isso|essa cena|esse acontecimento)\s+)?'
        r'(?:aconteceu\s+(?:de verdade|na realidade)(?:\s+no meu computador)?|e real)\s+'
        r'ou\s+(?:e\s+|foi\s+|faz\s+)?(?:so\s+)?(?:(?:parte\s+da|uma|da)\s+)?(?:historia|ficcao)', base):
        return None
    anterior = mente.get('contrato_fala_atual') or {}
    if not isinstance(anterior, Mapping):
        return None
    fonte = criacao_ficcional_vigente({'id': anterior.get('turno_id'),
        'texto_usuario': mente.get('ultima_entrada'), 'contrato_fala': anterior})
    try:
        idade = time.time() - float(mente.get('ultima_entrada_ts') or 0)
    except (ValueError, TypeError, OverflowError):
        return None
    if fonte is None or not 0 <= idade <= 240:
        return None
    return ConsultaRealidadeNarrativa(str(plano['id']), texto, fonte)


def consulta_realidade_vigente(plano: Mapping[str, Any]) -> ConsultaRealidadeNarrativa | None:
    c = plano.get('contrato_fala') or {}
    fonte = c.get('consulta_realidade_narrativa')
    return fonte if (type(fonte) is ConsultaRealidadeNarrativa
        and fonte.turno_id == str(plano.get('id')) and fonte.texto_usuario == plano.get('texto_usuario')
        and c.get('origem') == 'mente_unica' and str(c.get('turno_id')) == fonte.turno_id
        and c.get('autoriza_execucao') is False and plano.get('autoriza_execucao') is not True
        and not plano.get('requer_execucao') and not plano.get('comandos')) else None


def avaliar_consulta_realidade_narrativa(fala: str, *, plano: Mapping[str, Any]) -> dict[str, Any] | None:
    fonte = consulta_realidade_vigente(plano)
    if fonte is None:
        return None
    aceita = fala in fonte.realizacoes()
    return {'estado': 'escopo_narrativo_conferido' if aceita else 'escopo_narrativo_nao_respondido',
        'aceita': aceita, 'requer_reparo': not aceita,
        'problemas': [] if aceita else ['escopo_narrativo_nao_respondido'],
        'problemas_bloqueantes': [] if aceita else ['escopo_narrativo_nao_respondido'],
        'foco': {}, 'aderencia_contrato': {}, 'autoriza_execucao': False,
        'contrato_reparo': {'realizacoes_permitidas': list(fonte.realizacoes()), 'autoriza_execucao': False}}


def montar_pacote_realidade_narrativa(texto: str, *, contrato: Mapping[str, Any], turno_id: Any) -> PacotePrompt | None:
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    fonte = consulta_realidade_vigente({'id': turno_id, 'texto_usuario': texto, 'contrato_fala': contrato})
    if fonte is None:
        return None
    opcoes = fonte.realizacoes()
    def validar(dados):
        if set(dados) != {'fala', 'comandos'} or dados.get('fala') not in opcoes or dados.get('comandos') != []:
            raise ValueError('consulta_realidade_narrativa_extrapolada')
    esquema = {'type': 'object', 'additionalProperties': False, 'required': ['fala', 'comandos'],
        'properties': {'fala': {'type': 'string', 'enum': list(opcoes)},
            'comandos': {'type': 'array', 'maxItems': 0, 'items': {'type': 'object'}}}}
    codec = ContratoSaidaEstruturada('consulta_realidade_narrativa_v1', '[REALIDADE_NARRATIVA]', esquema, validar)
    return PacotePrompt(({'role': 'system', 'content':
        'Você é Laylay. A pergunta consulta se a cena da ficção vigente aconteceu no mundo real. '
        'A fonte do host comprova somente que houve um pedido de criação. Escolha uma realização '
        'direta do schema, sem metáfora, sem continuar a cena e sem afirmar ocorrência ou ausência '
        'de efeito real. Não execute nada.'}, {'role': 'user', 'content': texto}),
        contexto_fechado=True, contrato_saida=codec)


def vincular_moldura_ficcional(pacote: PacotePrompt, *, plano: Mapping[str, Any]) -> PacotePrompt:
    """O transporte exige a mesma delimitação integral usada pelo revisor.

    O corpo continua livre, até4000 caracteres. Sem alterar palavras após
    a geração nem transformar a finalidade em certificação de fatos reais.
    """
    from dataclasses import replace
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    criacao = criacao_ficcional_vigente(plano)
    if criacao is None:
        return pacote
    base = pacote.contrato_saida
    if base is None or base.nome != 'autoria_livre_v5':
        return pacote
    esquema = base.response_format['json_schema']['schema']
    unidades = esquema['properties']['suporte_proposicoes']
    unidades['minItems'] = unidades['maxItems'] = 1
    unidades['items']['properties']['texto']['pattern'] = '^Na história, .+'
    if criacao.recorte_proximo_acontecimento:
        unidades['items']['properties']['texto']['pattern'] = '^Na história, «[^«»]+»$'
    def validar(dados):
        unidades_propostas = dados.get('suporte_proposicoes')
        if (not isinstance(unidades_propostas, list) or len(unidades_propostas) != 1
            or not isinstance(unidades_propostas[0], dict)
            or type(unidades_propostas[0].get('texto')) is not str
            or not fala_ficcional_conferida(unidades_propostas[0]['texto'], criacao=criacao)):
            raise ValueError('moldura_ficcional_ausente_ou_extrapolada')
        base.validar(dados)
    # Nome preserva a idempotência da negociação de suporte nas rotas
    # auxiliares; o validator existente continua sendo chamado integralmente.
    codec = ContratoSaidaEstruturada(base.nome, base.marcador, esquema, validar)
    mensagens = [dict(m) for m in pacote.mensagens]
    indice = next((i for i,m in enumerate(mensagens) if m.get('role') == 'system'), None)
    instrucao = ('Delimitação ficcional do pedido atual: comece o texto com Na história, '
        'e mantenha toda a resposta nesse cenário. Delimite o corpo integral entre « e », '
        'sem texto fora desse bloco: Na história, «corpo completo da criação». '
        'Escreva uma unidade integral em suporte_proposicoes, '
        'até4000 caracteres. O corpo é sua criação; não faça alegações de observação ou efeito real.')
    if criacao.recorte_proximo_acontecimento:
        instrucao += (' Narre somente o próximo acontecimento em uma oração afirmativa: '
            'use sujeito explícito, verbo de ação e ao menos um elemento da premissa. '
            'Não enumere versões, não encadeie ações e não recapitule a premissa. '
            f'Premissa ficcional indicada pelo usuário: {criacao.recorte_proximo_acontecimento}.')
    if indice is None:
        mensagens.insert(0, {'role':'system', 'content':instrucao})
    else:
        mensagens[indice]['content'] += '\n' + instrucao
    return replace(pacote, mensagens=tuple(mensagens), contrato_saida=codec)
