"""Retoma uma criação publicada em um recorte de autoria e condição explícitas."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Literal, Mapping, TYPE_CHECKING

from mente_laylay.cognicao.normalizacao_linguagem import (
    normalizar_texto_basico, pedido_repeticao_itens_mencionados,
)
from mente_laylay.cognicao.referencias_linguagem import (
    complemento_recordacao_dialogo, enunciados_discursivos, intervalos_citados, texto_fora_de_citacoes,
)

if TYPE_CHECKING:
    from mente_laylay.cognicao.continuidade_resposta import RespostasAnterioresTurno
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta


ABERTURA_RETOMADA_CRIACAO = re.compile(
    r"(?:(?:e|ent[aã]o)\s+)?(?P<transicao>agora),?\s+"
    r"(?:eu\s+)?(?:quero|queria|gostaria\s+de)\s+[^:;.!?]+:\s*",
    re.I,
)
MATRIZ_RETOMADA_CRIACAO = re.compile(
    r"(?:qual|quais|que|o que)\s+(?:era|eram|foi|foram)\s+(?P<objeto>[^:;.!?]+?)"
    r"\s+que\s+(?:voc[eê]|tu)\s+(?:inventou|criou|imaginou|descreveu|escreveu|contou|prop[oô]s)\b"
    r"(?P<destino>[^:;.!?]*)\?",
    re.I,
)
_REACAO = re.compile(r'(?:acertou|boa|certo|[oó]timo|perfeito|isso)[.!]+', re.I)
_FORMA = re.compile(r'(?:conte|diga|explique|responda) com suas palavras[.!]*', re.I)
_LEMBRANCA_DE_DETALHE = re.compile(
    r'(?:[ée]\s+(?:s[oó]|apenas)\s+para\s+)?(?:lembrar|recordar)\s+(?:um|o)\s+detalhe'
    r'\s+que\s+(?:voc[eê]|tu)\s+(?:j[aá]\s+)?(?:contou|descreveu)[.!]*', re.I,
)
_DESCRICAO_NA_CENA = re.compile(
    r'(?:[^:;.!?]+:\s*)?(?:(?:no|na)\s+(?:come[cç]o|in[ií]cio)\s+d[oa]\s+[^,;.!?]+,\s*)?'
    r'(?:voc[eê]|tu)\s+(?:descreveu|mencionou|inventou)\s+um[a]?\s+(?P<objeto>[^\W\d_]+)'
    r'\s+n[oa]\s+(?P<local>[^\W\d_]+)\s+d[oa]s?\s+(?P<cenario>[^\W\d_]+)[.!]', re.I,
)
_DEFINICAO = re.compile(
    r'\bque eu (?:imagino|imaginei|invento|inventei|crio|criei|descrevi|escrevi|propus) '
    r'[ée] (?P<artigo>um|uma) (?P<nome>[^,.!?;:«»"\n]+?)(?=\s+que\b|[.!?]|$)',
    re.I,
)
_COORDENACAO_DA_REGRA = re.compile(r'\b(?:e|ou|mas|por[eé]m|enquanto|ent[aã]o)\b', re.I)
_FONTE_NEGADA_OU_INCERTA = re.compile(r'\b(?:nao|nunca|talvez|supostamente)\b')
_DESCRICAO_NOMINAL = re.compile(
    r'(?:e\s+)?(?:no|na)\s+[^,;.!?]+,\s*'
    r'(?P<grupo>um[a]?\s+(?P<nome>[^\W\d_]+)\s+(?P<atributo>[^\W\d_]+))'
    r'(?:,\s+como se\s+[^,;.!?]+)?[.!]', re.I,
)
_DETALHE_ORIGINAL = re.compile(
    r'(?:(?:s[oó] que|mas),?\s+)?na\s+(?:primeira\s+descri[cç][aã]o|descri[cç][aã]o\s+original),\s*'
    r'(?P<artigo>[oa])\s+(?P<objeto>[^\W\d_]+)\s+(?P<verbo>era|estava)\s+(?P<atributo>[^\W\d_]+)[.!]', re.I,
)
_PEDIDO_DE_CORRECAO = re.compile(
    r'(?:(?:voce )?(?:pode|poderia) reconhecer|reconheca) (?:a|essa|esta) diferenca e '
    r'(?:ajustar|corrigir|ajuste|corrija|reformule) a descricao,? '
    r'sem (?:apagar|perder|mudar) o que ja (?:tinhamos|estava) (?:combinado )?na historia[?!.]',
)
_DETALHES_PROPOSTOS = re.compile(r'agora imagino (?P<material>[^,;.!?]+?) e (?P<extra>[^,;.!?]+)', re.I)
_LIMITE = 'Não lembro dessa versão com segurança. Você lembra de algum detalhe da cena?'
_CONSULTA_PRIMEIRA_MENSAGEM = re.compile(
    r'(?:(?:agora )?(?:vamos testar sua memoria|quero lembrar):\s*)?'
    r'qual (?:era|foi) o nome d[oa] (?P<objeto>[a-z-]+(?: [a-z-]+){0,2}) '
    r'que (?:inventamos|criamos|imaginamos) n[oa] (?:comeco|inicio) '
    r'd(?:esta|essa|a) (?:sessao|conversa),? e (?:que|qual) (?:alimento|detalhe|objeto) '
    r'aparecia na (?:piada da )?primeira mensagem\?'
)
_FORMA_LEMBRANCA = re.compile(
    r'(?:sem consultar nada,\s*)?(?:basta |so )?lembrar d(?:a nossa|esta|essa) conversa[.!]*'
)
_MOLDURA_MENSAGEM_INICIAL = re.compile(
    r'\b(?:a primeira mensagem|a mensagem inicial)(?: d(?:ele|ela))? '
    r'(?:e|era|foi|dizia)\s*:\s*$'
)


@dataclass(frozen=True, slots=True)
class ConsultaPropostaInicial:
    objeto: str
    hoje: bool
    tema_aplicacao: str = ''


def recorte_ato_proposta_inicial(texto: str) -> ConsultaPropostaInicial | None:
    """Identifica a publicação consultada, sem buscar fatos recentes."""
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel

    if intervalos_citados(texto):
        return None
    ato = re.sub(
        r'^(?:eu\s+)?(?:quero|queria|vou)\s+(?:checar|conferir|retomar|testar)\s+'
        r'(?:(?:a|nossa|minha)\s+)?(?:continuidade|mem[oó]ria|lembran[cç]a)\s*:\s*',
        '', texto.strip(), flags=re.I,
    )
    complemento = complemento_recordacao_dialogo(ato) or ato.rstrip('?')
    consulta = re.fullmatch(
        r'qual\s+(?P<objeto>[^:;.!?]+?)\s+(?:voc[eê]|tu)\s+(?:prop[oô]s|sugeriu)\s+na\s+'
        r'(?:primeira mensagem|mensagem inicial)\s+(?P<escopo>de hoje|d(?:esta|essa) (?:conversa|sess[aã]o))',
        complemento, re.I,
    ) if ato.endswith('?') else None
    if consulta is None or not grupo_nominal_de_papel(consulta['objeto']):
        return None
    return ConsultaPropostaInicial(consulta['objeto'], consulta['escopo'].casefold() == 'de hoje')


def _recorte_proposta_inicial(texto: str) -> ConsultaPropostaInicial | None:
    from dataclasses import replace
    from mente_laylay.cognicao.fundamentacao_factual import _preambulo_sem_outro_pedido
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel

    partes = enunciados_discursivos(texto)
    for i, parte in enumerate(partes):
        consulta = recorte_ato_proposta_inicial(parte)
        if consulta is not None:
            break
        if not _preambulo_sem_outro_pedido(parte):
            return None
    else:
        return None
    cauda = partes[i + 1:]
    if not cauda:
        return consulta
    if len(cauda) != 1:
        return None
    objeto = re.escape(consulta.objeto)
    aplicacao = re.fullmatch(
        rf'como (?:voc[eê] )?(?:aplicaria|usaria) (?:ess[ea]|est[ea]|[oa]) {objeto} '
        r'(?:[àa]|na|em nossa) (?:nossa |esta )?conversa sobre (?P<tema>[^:;.!?]+)\?', cauda[0], re.I,
    )
    if aplicacao is None or not all(grupo_nominal_de_papel(g) for g in re.split(r'\s+e\s+', aplicacao['tema'], flags=re.I)):
        return None
    return replace(consulta, tema_aplicacao=aplicacao['tema'])


def _extrair_proposta_publicada(fala: str, objeto: str) -> tuple[str, str] | None:
    """Extrai uma proposta explícita da autora e a pergunta que ela escolheu fazer."""
    alvo = re.escape(objeto)
    abertura = re.compile(
        r'(?:^|[—–]\s*)(?:e\s+)?(?:'
        rf'se eu pudesse (?:escolher|propor|sugerir) um[a]? {alvo},\s*seria|'
        rf'como {alvo},\s*(?:eu\s+)?(?:proponho|sugiro|escolheria))\s+', re.I,
    )
    candidatas = []
    for parte in enunciados_discursivos(fala):
        citacoes = intervalos_citados(parte)
        for m in abertura.finditer(parte):
            if any(a <= m.start() < b for a, b in citacoes):
                continue
            restantes = [(a, b) for a, b in citacoes if a >= m.end()]
            corpo = parte[m.end():].strip()
            if not restantes:
                if corpo and '?' not in corpo:
                    candidatas.append((corpo.rstrip('. '), ''))
            elif len(restantes) == 1:
                inicio, fim = restantes[0]
                acao = parte[m.end():inicio].strip()
                pergunta = parte[inicio + 1:fim - 1].strip()
                if (acao.endswith(':') and pergunta.endswith('?') and pergunta.count('?') == 1
                        and all(c not in pergunta for c in '«»') and not parte[fim:].strip(' .!')):
                    candidatas.append((acao[:-1].strip(), pergunta))
    return candidatas[0] if len(candidatas) == 1 else None


@dataclass(frozen=True, slots=True)
class _CorrecaoDeDetalhe:
    sujeito: str
    verbo: str
    atributo: str
    material_proposto: str = ''
    detalhe_proposto: str = ''

    @property
    def detalhe(self) -> str:
        return f'{self.sujeito} {self.verbo} {self.atributo}'

    def descricao_ajustada(self, material_observado: str = '') -> str:
        material = self.material_proposto or material_observado
        qualificacao = f' de {material}' if material else ''
        extra = f', com {self.detalhe_proposto}' if self.detalhe_proposto else ''
        return f'Fica assim: {self.sujeito}{qualificacao} {self.verbo} {self.atributo}{extra}.'


@dataclass(frozen=True, slots=True)
class ConsultaDetalhesCena:
    papel: str = ''
    quantidade: int = 0
    citacao: str = ''
    detalhe_corrigido: str = ''


@dataclass(frozen=True, slots=True)
class RetomadaCriacao:
    turno_id: str
    texto_usuario: str
    ancora: tuple[str, ...]
    pede_regra: bool
    fonte: ReferenciaFalaConsulta | None
    alternativas: tuple[ReferenciaFalaConsulta, ...] = ()
    objeto_descrito: str = ''
    correcao: _CorrecaoDeDetalhe | None = None
    versao_recente: ReferenciaFalaConsulta | None = None
    primeira_mensagem: bool = False
    objeto_nomeado: str = ''
    escolha_inicial: str = ''
    proposta_inicial: ConsultaPropostaInicial | None = None
    consulta_reencontro: Literal['tema', 'pergunta'] | None = None
    respostas_reencontro: RespostasAnterioresTurno | None = None
    papeis_cena: tuple[str, str] = ()
    consulta_exemplo: str = ''
    exemplo_do_usuario: str = ''
    consulta_distincao: bool = False
    distincao_do_usuario: str = ''
    detalhes_cena: ConsultaDetalhesCena | None = None
    consulta_lista_usuario: bool = False
    lista_do_usuario: str = ''
    personagem_consultado: str = ''


def _consulta_detalhes_cena(texto: str) -> ConsultaDetalhesCena | None:
    citados = intervalos_citados(texto)
    if not citados:
        m = re.fullmatch(
            r'(?:na|em sua|na sua|na ultima) (?:resposta|fala)(?: anterior)?,? '
            r'a (primeira|segunda) (?:pessoa|personagem) (?:se )?(?:lembrou|recordou) (?:d[eo] )?'
            r'(dois|tres|quatro|[234]) detalhes(?: de [^.!?;]+)?[.!] '
            r'(?:quais (?:foram|eram) (?:esses|os) detalhes|quais detalhes foram citados|quais foram)\?'
            r'(?: (?:nao invente nada que nao tenha sido dito|sem inventar)[.!]?)?',
            normalizar_texto_basico(texto))
        if m:
            numeros = {'dois': 2, 'tres': 3, 'quatro': 4}
            return ConsultaDetalhesCena(m[1], int(m[2]) if m[2].isdigit() else numeros[m[2]])
    elif len(citados) == 1:
        inicio, fim = citados[0]
        base = normalizar_texto_basico(texto[:inicio] + 'trecho citado' + texto[fim:])
        m = re.fullmatch(
            r'na (?:fala|resposta) completa voce (?:disse|escreveu) trecho citado[.!] '
            r'(?P<detalhe>[^.!?;]+?) tambem (?:e|foi) um detalhe (?:lembrado|citado|mencionado)\. '
            r'(?:voce )?(?:concorda|aceita) (?:com )?(?:essa|a) correcao\? '
            r'explique em uma frase como evitar omissoes ao recuperar (?:falas|citacoes) recentes[.!]?', base)
        if m:
            return ConsultaDetalhesCena(citacao=texto[inicio + 1:fim - 1], detalhe_corrigido=m['detalhe'])
    return None


def _citacoes_atribuidas_da_cena(cena: str) -> dict[str, str]:
    """Duas vozes delimitadas. Resumos da assistente ficam fora das aspas."""
    citacoes = intervalos_citados(cena)
    if len(citacoes) != 2:
        return {}
    primeira, segunda = citacoes
    moldura1 = normalizar_texto_basico(cena[:primeira[0]])
    moldura2 = normalizar_texto_basico(cena[primeira[1]:segunda[0]]).lstrip(' .—–-')
    verbo = r'(?:(?:poderia|pode) (?:dizer|responder)|diz|disse|diria|responde|respondeu|responderia)'
    if not (re.fullmatch(r'(?:uma|a primeira(?: pessoa| personagem)?) ' + verbo + ':', moldura1)
            and re.fullmatch(r'(?:e )?a (?:outra|segunda)(?: pessoa| personagem)? ' + verbo + ':', moldura2)):
        return {}
    return {papel: cena[inicio + 1:fim - 1] for papel, (inicio, fim) in
            zip(('primeira', 'segunda'), citacoes)}


def _itens_lembrados(citacao: str) -> tuple[str, ...]:
    lista = re.fullmatch(r'[^.!?;:]+?\b(?:lembra|recorda|lembro de|recordo de)\s+([^.!?;:]+)[.!]?', citacao, re.I)
    return _itens_da_lista(lista[1]) if lista else ()


def _itens_da_lista(lista: str) -> tuple[str, ...]:
    itens = tuple(p.strip() for p in re.split(r',\s*|\s+e\s+(?=(?:o|a|os|as|um|uma|meu|minha)\b)', lista, flags=re.I))
    if 2 <= len(itens) <= 4 and len(set(itens)) == len(itens) and all(
        re.fullmatch(r'(?:o|a|os|as|um|uma|meu|minha|os meus|as minhas) [\w -]+', p, re.I) for p in itens
    ):
        return itens
    return ()


def _recortar_lista_do_usuario(anterior: str, pedido: re.Match[str]) -> str:
    """Exige um único trecho enumerado sob o referente da pergunta."""
    quantidade = {'dois': 2, 'tres': 3, 'quatro': 4}.get(pedido['quantidade'])
    if quantidade is None:
        quantidade = int(pedido['quantidade'])
    referente = pedido['referente']
    candidatas = []
    for enunciado in enunciados_discursivos(anterior):
        moldura, separador, lista = enunciado.partition(':')
        if not separador:
            continue
        moldura = normalizar_texto_basico(moldura)
        if referente:
            alvo = referente
            if moldura.startswith(('imagine ', 'imagina ')):
                alvo = re.sub(r' imaginari[oa]$', '', alvo)
            ancora = (
                r'\b(?:(?:na|no|num|numa|em (?:um|uma)|um|uma) )'
                + re.escape(alvo)
                + r'(?: com (?:dois|tres|quatro|[234]) (?:objetos|itens|elementos|detalhes|nomes))?'
            )
        else:
            ancora = r'\b(?:objetos|itens|elementos|detalhes|nomes)'
        if not re.search(ancora + r'$', moldura):
            continue
        literal = lista.strip().rstrip('.')
        if len(_itens_da_lista(literal)) == quantidade:
            candidatas.append(literal)
    return candidatas[0] if len(candidatas) == 1 else ''


def _personagem_de_fala_recente(texto: str) -> str:
    if intervalos_citados(texto):
        return ''
    consulta = re.fullmatch(
        r'(?:na|em sua|na sua) (?:fala|cena|historia) que voce (?:acabou de )?'
        r'(?:criar|escrever|contar|criou|escreveu|contou), '
        r'qual (?:foi|era) a pergunta d[oa] (?P<papel>[\w-]+)'
        r'(?: que (?:estava|ficou|andava) com (?:o|a|um|uma) [\w-]+(?: [\w-]+)?)?\? '
        r'(?:voce )?(?:pode|consegue|poderia) (?:citar|repetir) a (?:fala|frase) '
        r'(?:inteira|completa) que (?:ele|ela) (?:disse|fez|falou)\?',
        normalizar_texto_basico(texto),
    )
    return consulta['papel'] if consulta else ''


def _citar_fala_do_personagem(retomada: RetomadaCriacao) -> str:
    cena = _ultima_fala_publicada(retomada)
    alvo = retomada.personagem_consultado
    fim_anterior = 0
    candidatas = []
    for inicio, fim in intervalos_citados(cena):
        moldura = normalizar_texto_basico(cena[fim_anterior:inicio]).strip(' .,!?—–')
        autor = re.fullmatch(
            r'(?P<emissor>[oa] [\w-]+)(?: com (?:o|a|um|uma) [\w-]+(?: [\w-]+)?)?'
            r'\s+(?:diz|disse|responde|respondeu|pergunta|perguntou):', moldura,
        )
        if autor and autor['emissor'][2:] == alvo:
            candidatas.append(cena[inicio + 1:fim - 1])
        fim_anterior = fim
    if len(candidatas) != 1 or '?' not in candidatas[0] or any(c in candidatas[0] for c in '«»'):
        return ''
    return f'Na cena, a fala foi: «{candidatas[0]}»'


def _realizar_detalhes_cena(retomada: RetomadaCriacao, pedido: ConsultaDetalhesCena) -> str:
    if not pedido.citacao:
        citacao = _citacoes_atribuidas_da_cena(_ultima_fala_publicada(retomada)).get(pedido.papel, '')
        itens = _itens_lembrados(citacao)
        if len(itens) != pedido.quantidade:
            return ''
        lista = ' e '.join((', '.join(f'«{i}»' for i in itens[:-1]), f'«{itens[-1]}»'))
        return f'A {pedido.papel} pessoa lembrou de {lista}.'
    fonte = retomada.respostas_reencontro
    if not fonte or not fonte.vigente(retomada.texto_usuario, retomada.turno_id):
        return ''
    candidatas = [
        cita for fala in fonte.falas for cita in _citacoes_atribuidas_da_cena(fala).values()
        if ' '.join(cita.split()) == ' '.join(pedido.citacao.split())
    ]
    if len(candidatas) != 1:
        return ''
    def termos_item(item: str) -> str:
        normal = re.sub(r'^(?:[oa]s?|meu|minha) ', '', normalizar_texto_basico(item), count=1)
        return re.sub(r'\bde (?:crianca|da infancia|infancia)\b', ' de infancia', normal)
    itens = [i for i in _itens_lembrados(candidatas[0]) if termos_item(i) == termos_item(pedido.detalhe_corrigido)]
    if len(itens) != 1:
        return ''
    return (f'Sim, «{itens[0]}» estava na fala da personagem. '
            'Para evitar omissões, eu confiro a fala inteira e comparo cada item citado com o resumo.')


def _consulta_distincao_citacao(texto: str) -> bool:
    if intervalos_citados(texto):
        return False
    partes = [normalizar_texto_basico(parte) for parte in enunciados_discursivos(texto)]
    perguntas = [i for i, parte in enumerate(partes) if parte.endswith('?')]
    if len(perguntas) != 1:
        return False
    i = perguntas[0]
    return bool(any(re.match(r'(?:na nossa conversa anterior|no ultimo encontro|da ultima vez) '
                             r'(?:discutimos|conversamos|falamos)\b', parte) for parte in partes[:i])
        and re.fullmatch(
            r'qual (?:era|foi) a diferenca (?:que conversamos |que discutimos )?entre '
            r'citar (?:exatamente )?o que (?:alguem|a pessoa) disse e interpretar '
            r'o que (?:essa pessoa|ela|alguem) quis dizer\?', partes[i])
        and all(re.fullmatch(r'se nao lembrar, (?:diga|admita) (?:isso )?sem inventar[.!]?', p) for p in partes[i+1:]))


def _distincao_publicada(entradas: tuple[str, ...]) -> str:
    for entrada in reversed(entradas):
        for parte in enunciados_discursivos(entrada):
            if (not intervalos_citados(parte) and not any(c in parte for c in '«»')
                    and re.fullmatch(r'(?:uma |a )?cita[cç][aã]o [^.!?;]+,?\s*'
                                     r'enquanto (?:uma |a )?interpreta[cç][aã]o [^.!?;]+\.', parte, re.I)):
                return parte
    return ''


def _consulta_exemplo_recente(texto: str) -> str:
    partes = enunciados_discursivos(texto)
    if len(partes) != 2 or intervalos_citados(texto):
        return ''
    consulta = complemento_recordacao_dialogo(partes[0])
    referencia = re.fullmatch(
        r'o exemplo que acabei de (?:mencionar|contar|dar|descrever),? sobre ([^?!;]+)',
        consulta, re.I)
    if not referencia or not re.fullmatch(
        r'(?:diga|explique|conte) (?:o motivo da demora|por que (?:ele|ela) demorou) '
        r'e como (?:o outro amigo|a outra pessoa|o outro|a outra) se sentiu[.!]?',
        normalizar_texto_basico(partes[1])):
        return ''
    return referencia[1]


def _recortar_exemplo(anterior: str, referencia: str) -> str:
    from mente_laylay.cognicao.seletor_contexto import _tokens

    # A pergunta subsequente não faz parte da situação relatada. Recuperar
    # somente a premissa introduzida pelo interlocutor no turno anterior.
    partes = enunciados_discursivos(anterior)
    if not partes or intervalos_citados(partes[0]):
        return ''
    premissa = re.fullmatch(
        r'(?:vamos (?:discutir|imaginar) (?:um dilema|um exemplo|uma situação)|'
        r'(?:imagina|imagine|exemplo|considere (?:este|esse) exemplo)):\s+'
        r'(?P<situacao>[^.!?;]+)\.', partes[0], re.I)
    if (premissa and len(_tokens(referencia) & _tokens(premissa['situacao'])) >= 2
            and re.search(r'\b(?:sente|sentiu)\b[^.!?]+,\s*(?:mas|e)\b', premissa['situacao'], re.I)
            and not any(c in premissa['situacao'] for c in '«»')):
        return premissa['situacao']
    return ''


def _papeis_da_consulta(texto: str) -> tuple[str, ...]:
    """Vincula a pergunta retrospectiva e a leitura a personagens distintos."""
    if intervalos_citados(texto):
        return ()
    base = normalizar_texto_basico(texto)
    papel = r'(primeira|segunda)(?: pessoa| personagem)?'
    consulta = re.fullmatch(
        r'(?:(?:quero|queria) (?:testar|ver|conferir) se voce (?:acompanhou|lembra) '
        r'(?:a|da) (?:cena|historia|conversa)(?: que (?:inventamos|criamos))?:\s*)?'
        r'(?:qual|que) (?:foi|era) a (?:frase|fala) (?:da|com que a) ' + papel
        + r'(?: (?:abriu|iniciou|comecou) (?:a conversa|espaco para conversar))?,? e '
        r'(?:qual|o que) (?:foi|era) (?:a |o )(?:principal )?(?:preocupacao|receio|medo) da '
        + papel + r'\?(?: (?:nao (?:crie|invente|acrescente) detalhes novos|sem inventar)[.!]?)?', base)
    if not consulta or consulta[1] == consulta[2]:
        return ()
    return consulta.groups()


def _realizar_falas_da_cena(retomada: RetomadaCriacao) -> str:
    cena = _ultima_fala_publicada(retomada)
    falas = {}
    fim_anterior = 0
    for inicio, fim in intervalos_citados(cena):
        moldura = normalizar_texto_basico(cena[fim_anterior:inicio]).lstrip(' .')
        autor = re.fullmatch(r'a (primeira|segunda)(?: pessoa| personagem)? '
                             r'(?:(?:poderia|pode) (?:dizer|responder|perguntar)|'
                             r'disse|diria|respondeu|responderia|perguntou|perguntaria):', moldura)
        conteudo = cena[inicio + 1:fim - 1]
        if not autor or autor[1] in falas or not conteudo.strip() or any(c in conteudo for c in '«»'):
            return ''
        falas[autor[1]] = conteudo
        fim_anterior = fim
    if cena[fim_anterior:].strip(' .!') or set(falas) != set(retomada.papeis_cena):
        return ''
    literal, leitura = retomada.papeis_cena
    segunda = falas[leitura]
    # Dar a pista na voz do personagem sem converter a interpretação em lembrança.
    pista = re.search(r'\b(?:prefiro|receio|tenho medo de|me preocupa)\b[^.!?]*', segunda, re.I)
    trecho = pista[0] if pista and pista.start() > 0 else segunda
    return (f'A {literal} disse: «{falas[literal]}» '
            f'A pista sobre a preocupação da {leitura} está na fala dela: «{trecho}»')


def pedido_tema_e_pergunta_reencontro(texto: str) -> bool:
    """Reconhece os dois pedidos vinculados ao tema do encontro anterior."""
    partes = enunciados_discursivos(texto)
    if not partes or intervalos_citados(texto):
        return False
    condicional = re.fullmatch(
        r'(?:(?:oi|ola)(?:, \w+)?[.!] )?(?:sou (?:o |a )?[\w-]+, voltando para mais uma conversa(?: nossa)?\. )?'
        r'(?:no encontro anterior|na conversa anterior) voce (?:sugeriu|propos|escolheu) um (?:assunto|tema) '
        r'para retomarmos\. (?:voce )?(?:consegue|pode) (?:lembrar|recordar) qual (?:foi|era)\? '
        r'se lembrar, (?:me )?(?:diga|conte) o que gostaria de (?:investigar|explorar) nele'
        r'(?:; se nao, pode admitir sem inventar)?[.!]?', normalizar_texto_basico(texto))
    if condicional:
        return True
    ultimo = normalizar_texto_basico(partes[-1])
    if not re.fullmatch(
        r'(?:sem eu (?:te |lhe )?lembrar qual era:\s*)?(?:voce )?'
        r'(?:(?:consegue|conseguiria|pode|poderia) )?(?:recuperar|lembrar|retomar) '
        r'(?:esse|este|o) (?:tema|assunto) e (?:dizer|propor|formular|indicar) '
        r'qual pergunta (?:(?:voce )?gostaria de (?:explorar|fazer)|(?:voce )?(?:faria|exploraria))'
        r'(?: primeiro)?\?', ultimo,
    ):
        return False
    encontro = re.compile(
        r'(?:da ultima vez|na (?:ultima|outra) conversa|no ultimo encontro)[, ]+voce '
        r'(?:escolheu|propos|sugeriu|deixou) (?:um|o) (?:tema|assunto) '
        r'para (?:retomarmos|o proximo encontro|a proxima conversa)[.!]',
    )
    anteriores = [normalizar_texto_basico(p) for p in partes[:-1]]
    if not anteriores or not encontro.fullmatch(anteriores[-1]):
        return False
    return all(re.fullmatch(r'(?:oi|ola)(?:[, ]+[a-z]+)?[.!]|'
                            r'(?:sou|aqui e) o? ?[a-z0-9-]+, (?:de volta|voltando) '
                            r'(?:para|pra) (?:outra|mais uma) conversa[.!]', p) for p in anteriores[:-1])


def _pede_pergunta_publicada_no_reencontro(texto: str) -> bool:
    """Consulta conjunta à pergunta deixada pela assistente e ao motivo."""
    if intervalos_citados(texto):
        return False
    partes = [normalizar_texto_basico(p) for p in enunciados_discursivos(texto)]
    if len(partes) < 2:
        return False
    anterior = re.fullmatch(
        r'(?:(?:em|no) (?:nosso |ultimo )?encontro(?: anterior)?|na (?:ultima conversa|conversa anterior)|'
        r'da ultima vez)[, ]+voce (?:deixou|sugeriu|propos|escolheu|formulou) '
        r'uma pergunta(?: sobre [\w -]+)?[.!]', partes[-2],
    )
    pedido = re.fullmatch(
        r'(?:voce )?(?:(?:pode|poderia|consegue|conseguiria) )?(?:lembrar|recordar|recuperar) '
        r'qual (?:foi|era) e (?:explicar|dizer) (?:o que (?:te|lhe) levou a (?:essa|esta|a) pergunta|'
        r'por que (?:a |voce a )?escolheu)(?:, sem inventar(?: lembrancas)?(?: caso nao consiga)?)?\?',
        partes[-1],
    )
    return bool(anterior and pedido and all(re.fullmatch(
        r'(?:oi|ola)(?:[, ]+[a-z]+)?[.!]|(?:sou|aqui e) (?:o |a )?[a-z0-9-]+ '
        r'(?:de novo|de volta)[.!]', p) for p in partes[:-2]))


def _ultima_fala_publicada(retomada: RetomadaCriacao) -> str:
    from mente_laylay.cognicao.continuidade_resposta import RespostasAnterioresTurno

    fonte = retomada.respostas_reencontro
    if (type(fonte) is not RespostasAnterioresTurno
            or not fonte.vigente(retomada.texto_usuario, retomada.turno_id) or not fonte.falas):
        return ''
    return fonte.falas[-1]


def _realizar_pergunta_reencontro(retomada: RetomadaCriacao) -> str:
    fala = _ultima_fala_publicada(retomada)
    citados = intervalos_citados(fala)
    molduras = [m for m in re.finditer(
        r'(?:^|(?<=[.!])\s+)(?:para (?:[oa]|noss[oa]) (?:pr[oó]ximo encontro|pr[oó]xima conversa)),? '
        r'(?:eu )?(?:gostaria de saber|queria perguntar|deixaria a pergunta|proponho (?:a|uma) pergunta):\s*',
        fala, re.I,
    ) if not any(a <= m.start() < b for a, b in citados)]
    if len(molduras) != 1:
        return ''
    moldura = molduras[0]
    corpo = fala[moldura.end():].strip()
    aspas = intervalos_citados(corpo)
    if aspas and aspas[0][0] == 0:
        fim = aspas[0][1]
        pergunta = corpo[1:fim - 1]
        if pergunta.count('?') != 1:
            return ''
        restantes = list(enunciados_discursivos(corpo[fim:].lstrip('. ')))
    else:
        pergunta, *restantes = enunciados_discursivos(corpo) or ('',)
        # Uma alternativa elabora a mesma pergunta quando explicita opções.
        # Uma segunda pergunta autônoma deixa a fonte ambígua.
        if restantes and re.fullmatch(r'(?:[ée]|seria) [^?!]+,?\s+ou [^?!]+\?', restantes[0], re.I):
            pergunta += ' ' + restantes.pop(0)
    if not pergunta.endswith('?') or intervalos_citados(pergunta) or any(c in pergunta for c in '«»'):
        return ''
    resposta = f'Eu deixei esta pergunta: «{pergunta}»'
    if restantes:
        if (len(restantes) == 1 and not intervalos_citados(restantes[0])
                and re.fullmatch(r'(?:eu )?(?:escolhi|propus|fiz) (?:essa|esta|a) pergunta '
                                 r'porque [^!?;]+[.]', restantes[0], re.I)):
            return f'{resposta} E expliquei: «{restantes[0]}»'
        return ''
    contexto = enunciados_discursivos(fala[:moldura.start()])
    if contexto and contexto[-1].endswith('.') and not intervalos_citados(contexto[-1]):
        resposta += f' Na mesma resposta, eu disse: «{contexto[-1]}»'
    return resposta + ' O motivo da escolha não ficou explícito ali.'


def _realizar_tema_reencontro(retomada: RetomadaCriacao) -> str:
    # O recorte vem da última fala entregue no histórico do canal. Uma
    # ocorrência anterior parecida não ocupa o lugar da última despedida.
    anterior = _ultima_fala_publicada(retomada)
    resumo = re.fullmatch(r'(?:construímos|discutimos|exploramos) duas ideias(?: importantes)?: '
        r'uma sobre (?P<primeira>[^;.!?]+); e outra sobre (?P<segunda>[^;.!?]+)\.', anterior, re.I)
    if resumo and not intervalos_citados(anterior) and not any(c in anterior for c in '«»'):
        primeira = resumo['primeira'].split(' — ')[0].strip()
        segunda = resumo['segunda'].split(',')[0].strip()
        return (f'Falamos de «{primeira}» e de «{segunda}». Naquele resumo deixei a escolha em aberto. '
                f'Eu começaria agora pela primeira ideia. Como ela aparece numa conversa de verdade?')
    temas = []
    for parte in enunciados_discursivos(_ultima_fala_publicada(retomada)):
        proposta = re.fullmatch(
            r'(?:o tema|o assunto|a quest[aã]o) que (?:eu )?(?:gostaria de|quero) retomar '
            r'[ée] (?P<tema>[^.!?;:—–]+?)(?:\s+[—–]\s+[^.!?]+)?[.!]?', parte, re.I,
        )
        if proposta is not None and not intervalos_citados(proposta['tema']):
            temas.append(proposta['tema'].strip())
    if len(temas) != 1 or not temas[0] or any(c in temas[0] for c in '«»'):
        return ''
    return (f'O tema que ficou para retomarmos foi «{temas[0]}». '
            'Minha primeira pergunta seria: que situação concreta ajudaria a entender melhor essa ideia?')


def recorte_escolha_inicial(texto: str) -> str:
    """Retoma a proposta inicial para um tema explícito, sem validar sua categoria."""
    from mente_laylay.cognicao.fundamentacao_factual import _preambulo_sem_outro_pedido
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel
    if intervalos_citados(texto):
        return ''
    partes = list(enunciados_discursivos(texto))
    if not partes or not re.fullmatch(
        r'(?:quero )?(?:s[oó]|apenas|somente) o nome(?:, sem (?:nenhum comando|explicar))?[.!]*',
        partes[-1], re.I):
        return ''
    partes.pop()
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    if not partes or any(not _preambulo_sem_outro_pedido(p) and (
        '?' in p or classificar_modalidade_turno(p).get('modalidade') not in {'conversa', 'reacao'}
        or classificar_modalidade_turno(p).get('autoriza_execucao')) for p in partes[:-1]):
        return ''
    m = re.fullmatch(
        r'(?:(?:agora )?(?:desafio|teste) de mem[oó]ria:\s*)?'
        r'no (?:come[cç]o|in[ií]cio) d(?:esta|essa) (?:sess[aã]o|conversa),\s*'
        r'qual foi [oa] (?P<categoria>[^:;.!?]+?) que (?:voc[eê]|tu) '
        r'(?:inventou|criou|prop[oô]s) para [oa] (?P<tema>[^:;.!?]+)\?',
        re.sub(r'^[^\w]+', '', partes[-1]), re.I)
    if not m or not grupo_nominal_de_papel(m['categoria']):
        return ''
    grupos = re.split(r'\s+d(?:e|o|a|os|as)\s+', m['tema'])
    return normalizar_texto_basico(m['tema']) if all(grupo_nominal_de_papel(g) for g in grupos) else ''


def _nome_escolha_inicial(fala: str, tema: str) -> str:
    """Só a proposta nominal publicada após a retomada explícita do tema.

    O modo condicional pertence à escolha fictícia registrada. Isso não prova
    criação ou execução externa, nem certifica a categoria proposta na consulta.
    """
    partes = enunciados_discursivos(fala)
    if len(partes) < 2:
        return ''
    topico = normalizar_texto_basico(partes[0]).strip(' ?!.,')
    topico = re.sub(r'^(?:ah,? )?[oa] ', '', topico)
    if not (topico == tema or topico.startswith(tema + ' de ')):
        return ''
    trecho = partes[1]
    aspas = intervalos_citados(trecho)
    if not aspas:
        return ''
    inicio, fim = aspas[0]
    if not re.fullmatch(r'(?:eu )?(?:escolheria|proporia|sugeriria) [oa] ', trecho[:inicio], re.I):
        return ''
    # A continuação deve explicar uma escolha única, não oferecer alternativas.
    if not re.match(r'^\s*(?:[.!?]|$|[—–:]\s)', trecho[fim:]):
        return ''
    nome = trecho[inicio+1:fim-1]
    return nome if re.fullmatch(r'[\w -]{1,100}', nome) else ''


def recorte_nome_publicado(texto: str) -> str:
    """Consulta integral ao nome autorado no diálogo, sem qualificar efeitos.

    A matriz de lembrança e a interrogativa direta têm o mesmo complemento:
    nome/título/apelido criado pela destinatária para um grupo nominal.
    Outros atos, autores ou consultas sobre o mundo não cabem neste recorte.
    """
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel

    if intervalos_citados(texto):
        return ''
    partes = enunciados_discursivos(texto)
    if partes and re.fullmatch(r'(?:só|so|somente|apenas) o (?:nome|apelido|título|titulo)'
                              r'(?:,? sem explicar)?[.!]*', partes[-1], re.I):
        partes = partes[:-1]
    if len(partes) != 1:
        return ''
    consulta = re.fullmatch(
        r'(?:mudando (?:um pouco|de assunto):\s*)?'
        r'(?:(?:voc[eê] )?(?:ainda )?(?:se )?(?:lembra|recorda) do|qual (?:era|foi) o) '
        r'(?:nome|apelido|t[ií]tulo) que (?:(?:voc[eê]|tu) )?(?:inventou|criou|escolheu|deu) '
        r'para (?:o|a) (?P<objeto>[^:;.!?]+?) (?:nesta|nessa) (?:conversa|sess[aã]o)\?',
        partes[0], re.I)
    if consulta is None:
        return ''
    objeto = consulta['objeto'].casefold()
    grupos = re.split(r'\s+com\s+', objeto)
    if len(grupos) > 2 or not all(grupo_nominal_de_papel(g) for g in grupos):
        return ''
    return normalizar_texto_basico(objeto)


def _nome_publicado(fala: str, objeto: str, *, conferir_qualificador: bool = True) -> str:
    """Extrai só a nomeação assertiva; o restante não vira prova de causa.

    Um qualificador atual pode referir o único objeto antes não qualificado.
    Nunca se apaga qualificador de uma fonte para unificar objetos distintos.
    A unicidade entre publicações é conferida pelo seletor abaixo.
    """
    nomes = []
    for trecho in enunciados_discursivos(fala):
        citacoes = intervalos_citados(trecho)
        if not citacoes:
            continue
        inicio, fim = citacoes[0]
        matriz = normalizar_texto_basico(trecho[:inicio]).rstrip(': ')
        m = re.fullmatch(r'(?:o|a) (.+?) (?:se chama|se chamava|vai se chamar)', matriz)
        if m is None:
            continue
        if conferir_qualificador and m[1] not in {objeto, objeto.partition(' com ')[0]}:
            continue
        if not conferir_qualificador and m[1].split()[0] != objeto.split()[0]:
            continue
        nome = trecho[inicio + 1:fim - 1].strip()
        cauda = trecho[fim:].strip()
        if cauda and not re.match(r'^(?:[.!]$|,\s*(?:porque|pois)\s)', cauda, re.I):
            continue
        if re.fullmatch(r'[\w -]{1,80}', nome):
            nomes.append(nome)
    return nomes[0] if len(nomes) == 1 else ''


def recorte_primeira_mensagem(texto: str) -> str:
    from mente_laylay.cognicao.fundamentacao_factual import _preambulo_sem_outro_pedido

    partes = enunciados_discursivos(texto_fora_de_citacoes(texto))
    if partes and _FORMA_LEMBRANCA.fullmatch(normalizar_texto_basico(partes[-1])):
        partes = partes[:-1]
    consulta = _CONSULTA_PRIMEIRA_MENSAGEM.fullmatch(normalizar_texto_basico(partes[-1])) if partes else None
    if consulta is None or any(not _preambulo_sem_outro_pedido(p) for p in partes[:-1]):
        return ''
    return consulta['objeto']


def _realizar_primeira_mensagem(retomada: RetomadaCriacao) -> tuple[str, str]:
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta

    fonte = retomada.fonte
    if type(fonte) is not ReferenciaFalaConsulta or not fonte.vigente(retomada.texto_usuario, retomada.turno_id):
        return '', 'ausente'
    texto = fonte.conteudo
    objeto = re.escape(retomada.ancora[0])
    nomeacao = re.compile(rf'\b{objeto} (?:vai se chamar|se chama|se chamava|chamar-se-ia)\s*:?\s*$')
    pares = []
    citacoes = intervalos_citados(texto)
    for (inicio, fim), (inicio_fala, fim_fala) in zip(citacoes, citacoes[1:]):
        antes = normalizar_texto_basico(texto[:inicio])
        entre = normalizar_texto_basico(texto[fim:inicio_fala])
        nome = texto[inicio + 1:fim - 1].strip()
        mensagem = texto[inicio_fala + 1:fim_fala - 1].strip()
        if (nomeacao.search(antes) and not _FONTE_NEGADA_OU_INCERTA.search(antes)
                and _MOLDURA_MENSAGEM_INICIAL.search(entre)
                and re.fullmatch(r'[\w -]{1,80}', nome) and mensagem and '«' not in mensagem and '»' not in mensagem):
            pares.append((nome, mensagem))
    if len(pares) != 1:
        return '', 'ausente'
    nome, mensagem = pares[0]
    return f'O nome era «{nome}». Na primeira mensagem, eu disse: «{mensagem}»', 'primeira_mensagem_publicada'


@dataclass(frozen=True, slots=True)
class _ConteudoCriacao:
    definicao: str
    pronome: str
    regra: str

    def realizar(self, *, pede_regra: bool) -> tuple[str, str]:
        identidade = f'Era {self.definicao}.'
        if not pede_regra:
            return identidade, 'criacao_publicada'
        if not self.regra:
            return f'{identidade} Não lembro com segurança como {self.pronome} funcionava.', 'identidade_sem_regra'
        if _COORDENACAO_DA_REGRA.search(self.regra):
            return f'{identidade} Naquela versão, eu descrevi assim: «{self.regra}».', 'criacao_publicada'
        # Só se retoma o sujeito já identificado. O predicado, o modalizador
        # e a condição ficam integrais, incluindo polaridade e tempo verbal.
        predicado = self.regra.split(' ', 2)[2]
        return f'{identidade} Naquela versão, {self.pronome} {predicado}.', 'criacao_publicada'


def _recorte_da_consulta(texto: str) -> tuple[tuple[str, ...], bool] | None:
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel

    if intervalos_citados(texto):
        return None
    partes = list(enunciados_discursivos(texto))
    if partes and _REACAO.fullmatch(partes[0]):
        partes.pop(0)
    if partes and _FORMA.fullmatch(partes[-1]):
        partes.pop()
    if not 1 <= len(partes) <= 2:
        return None
    consulta = MATRIZ_RETOMADA_CRIACAO.fullmatch(ABERTURA_RETOMADA_CRIACAO.sub('', partes[0], count=1))
    if consulta is None:
        return None
    objeto = normalizar_texto_basico(consulta['objeto'])
    nucleo = re.fullmatch(r'(?:o|a|um|uma) ([a-z]+)(?: [a-z]+)*', objeto)
    alvo = re.fullmatch(r'\s+para\s+(?:o|a)\s+(.+)', consulta['destino'])
    if not nucleo or not alvo or not grupo_nominal_de_papel(alvo[1]):
        return None
    ancora = tuple(re.split(r'\s+d(?:o|a)\s+', normalizar_texto_basico(alvo[1]), maxsplit=1))
    if not all(termo and len(termo) >= 3 for termo in ancora):
        return None
    if len(partes) == 2:
        referencia = rf'(?:esse|essa|este|esta|o|a) {re.escape(nucleo[1])}'
        pergunta = rf'(?:e )?(?:o que fazia {referencia} funcionar|como {referencia} funcionava)\?'
        if not re.fullmatch(pergunta, normalizar_texto_basico(partes[1])):
            return None
    return ancora, len(partes) == 2


def _recorte_de_detalhe(texto: str) -> tuple[tuple[str, ...], str] | None:
    if intervalos_citados(texto):
        return None
    partes = enunciados_discursivos(texto)
    if len(partes) < 3 or not _LEMBRANCA_DE_DETALHE.fullmatch(partes[-1]):
        return None
    descricao = _DESCRICAO_NA_CENA.fullmatch(partes[-3])
    if descricao is None or any('?' in parte for parte in partes[:-2]):
        return None
    objeto, local, cenario = (normalizar_texto_basico(descricao[c]) for c in ('objeto', 'local', 'cenario'))
    if not re.fullmatch(rf'como era (?:a|o|essa|esse|esta|este) {re.escape(objeto)}\?',
                        normalizar_texto_basico(partes[-2])):
        return None
    return (local, cenario), objeto


def _recorte_de_correcao(texto: str) -> _CorrecaoDeDetalhe | None:
    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia, grupo_nominal_de_papel
    from mente_laylay.cognicao.fundamentacao_factual import _preambulo_sem_outro_pedido

    partes = enunciados_discursivos(texto)
    if (len(partes) < 2 or intervalos_citados(texto) or any('?' in parte for parte in partes[:-1])
            or not _PEDIDO_DE_CORRECAO.fullmatch(normalizar_texto_basico(partes[-1]))):
        return None
    originais = [(i, m) for i, parte in enumerate(partes[:-1]) if (m := _DETALHE_ORIGINAL.fullmatch(parte))]
    if len(originais) != 1:
        return None
    indice, original = originais[0]
    sujeito = f"{original['artigo'].lower()} {original['objeto']}"
    if (not grupo_nominal_de_papel(sujeito) or not (consultar_morfologia(original['atributo']) or 0) & 2
            or any(not _preambulo_sem_outro_pedido(p) for i, p in enumerate(partes[:-1])
                   if i != indice and not re.match(r'^(?:agora imagino|depois voc[eê] descreveu|voc[eê] deu)\b', p, re.I))):
        return None
    propostas = [m for parte in partes[indice + 1:-1]
                 if (m := _DETALHES_PROPOSTOS.fullmatch(re.split(r',\s+mas\s+', parte.rstrip('.!'), maxsplit=1, flags=re.I)[0]))]
    if len(propostas) == 1 and all(grupo_nominal_de_papel(propostas[0][c]) for c in ('material', 'extra')):
        return _CorrecaoDeDetalhe(sujeito, original['verbo'].lower(), original['atributo'],
                                 propostas[0]['material'], propostas[0]['extra'])
    return _CorrecaoDeDetalhe(sujeito, original['verbo'].lower(), original['atributo'])


def _publicou_atributo_original(fala: str, correcao: _CorrecaoDeDetalhe) -> bool:
    _, objeto = normalizar_texto_basico(correcao.sujeito).split()
    detalhe = normalizar_texto_basico(correcao.detalhe)
    atributo = normalizar_texto_basico(correcao.atributo)
    partes = enunciados_discursivos(fala)
    for indice, parte in enumerate(partes):
        if intervalos_citados(parte):
            continue
        if normalizar_texto_basico(parte).rstrip('.') == 'na historia, ' + detalhe:
            return True
        descricao = _DESCRICAO_NOMINAL.fullmatch(parte)
        if not indice or not descricao:
            continue
        cena = normalizar_texto_basico(texto_fora_de_citacoes(partes[indice - 1]))
        if (normalizar_texto_basico(descricao['nome']) == objeto
                and normalizar_texto_basico(descricao['atributo']) == atributo
                and re.search(r'\b(?:ha|havia|tem|tinha|existe|existia)\s+um[a]?\b', cena)
                and not _FONTE_NEGADA_OU_INCERTA.search(cena) and not cena.endswith('?')):
            return True
    return False


def _comparar_descricao(fala: str, correcao: _CorrecaoDeDetalhe) -> tuple[str, str]:
    """Só afirma omissão quando outra descrição do mesmo objeto foi publicada."""
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel

    sujeito = re.escape(correcao.sujeito)
    objeto = re.escape(correcao.sujeito.split()[1])
    atributo = re.escape(correcao.atributo)
    partes = enunciados_discursivos(fala)
    primeira = partes[0] if partes else ''
    if re.fullmatch(rf'(?:(?:{sujeito}) (?:era|estava)|era um[a]? {objeto}) {atributo}[.!]', primeira, re.I):
        return 'presente', ''
    if re.search(rf'\b{atributo}\b', fala, re.I):
        return '', ''
    material = re.match(rf'^{sujeito} era de (?P<material>[^,;.!?]+)[,.]', primeira, re.I)
    if material and grupo_nominal_de_papel(material['material']):
        return 'omitido', material['material']
    return '', ''


def _descreve_objeto(fala: str, correcao: _CorrecaoDeDetalhe) -> bool:
    sujeito = re.escape(correcao.sujeito)
    objeto = re.escape(correcao.sujeito.split()[1])
    return bool(re.match(rf'(?:{sujeito}\s+(?:era|estava|tinha)|era\s+um[a]?\s+{objeto})\b', fala, re.I))


def _extrair_conteudo(fala: str, *, ancora: tuple[str, ...], objeto_descrito: str = '') -> _ConteudoCriacao | None:
    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia, grupo_nominal_de_papel

    def menciona(texto: str, termo: str) -> bool:
        return bool(re.search(rf'\b{re.escape(termo)}\b', normalizar_texto_basico(texto)))

    externo = texto_fora_de_citacoes(fala)
    if not all(menciona(externo, termo) for termo in ancora):
        return None
    partes = enunciados_discursivos(fala)
    if objeto_descrito:
        # A descrição nominal publicada fica junto da cena. Preservar a
        # grafia da fonte e extrair só o atributo diretamente enunciado.
        atributos = set()
        local, cenario = map(re.escape, ancora)
        local_da_cena = re.compile(
            rf'\b{local}\s+(?:(?:chei[oa]|replet[oa])\s+)?d(?:e|[oa]s?)\s+{cenario}\b',
        )
        for anterior, trecho in zip(partes, partes[1:]):
            contexto = normalizar_texto_basico(texto_fora_de_citacoes(anterior))
            cena = local_da_cena.search(contexto)
            if (cena is None or _FONTE_NEGADA_OU_INCERTA.search(contexto[:cena.start()])
                    or intervalos_citados(trecho)):
                continue
            descricao = _DESCRICAO_NOMINAL.fullmatch(trecho)
            if (descricao and normalizar_texto_basico(descricao['nome']) == objeto_descrito
                    and (consultar_morfologia(descricao['atributo']) or 0) & 2):
                atributos.add(descricao['grupo'])
        if len(atributos) == 1:
            return _ConteudoCriacao(atributos.pop(), '', '')
        return None
    # O local precisa estar na mesma declaração que introduz o objeto.
    # O nome do cenário pode aparecer em outra frase, desde que na mesma fala.
    definicoes = [(i, d) for i, trecho in enumerate(partes) if not intervalos_citados(trecho)
                  and not trecho.endswith('?') and menciona(trecho, ancora[0])
                  for d in _DEFINICAO.finditer(trecho)]
    if len(definicoes) != 1:
        return None
    indice, definicao = definicoes[0]
    prefixo = normalizar_texto_basico(partes[indice][:definicao.start()])
    if _FONTE_NEGADA_OU_INCERTA.search(prefixo):
        return None
    if len(ancora) == 2:
        local, cenario = map(re.escape, ancora)
        if re.search(rf'\b{local}\s+d[oa]\s+(?!{cenario}\b)', prefixo):
            return None
    nome = definicao['nome']
    if not grupo_nominal_de_papel(nome):
        return None
    indefinido = definicao['artigo'].lower()
    artigo, pronome = ('o', 'ele') if indefinido == 'um' else ('a', 'ela')
    entidade = re.escape(nome.split()[0])
    padrao = re.compile(
        rf'(?:^|,\s*e\s+)(?P<regra>{artigo} {entidade} (?:s[oó]|somente|apenas) '
        r'[^.!?;:,«»"“”()\[\]{}—–]+? (?:se|quando) [^.!?;:,«»"“”()\[\]{}—–]+)\.$', re.I,
    )
    regras = {m['regra'] for trecho in partes[indice + 1:] if not intervalos_citados(trecho)
              for m in padrao.finditer(trecho)}
    regra = next(iter(regras)) if len(regras) == 1 else ''
    return _ConteudoCriacao(f'{indefinido} {nome}', pronome, regra)


def construir_retomada_criacao(texto: str, *, plano: Mapping[str, Any],
                              mente: Mapping[str, Any],
                              respostas_recentes: RespostasAnterioresTurno | None = None,
                              mensagens_anteriores_usuario: tuple[str, ...] = ()) -> RetomadaCriacao | None:
    from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual
    from mente_laylay.memoria_mental.registro_semantico import (
        ReferenciaFalaConsulta, selecionar_fala_observada, selecionar_primeira_fala_textual,
    )

    if (not plano.get('id') or plano.get('texto_usuario') != texto or plano.get('autoriza_execucao') is not False
            or plano.get('requer_execucao') or plano.get('comandos')):
        return None
    consulta_lista = pedido_repeticao_itens_mencionados(texto)
    if consulta_lista:
        anterior = mensagens_anteriores_usuario[-1] if mensagens_anteriores_usuario else ''
        return RetomadaCriacao(str(plano['id']), texto, (), False, None,
            consulta_lista_usuario=True, lista_do_usuario=_recortar_lista_do_usuario(anterior, consulta_lista))
    personagem = _personagem_de_fala_recente(texto)
    if personagem:
        return RetomadaCriacao(str(plano['id']), texto, (), False, None,
            respostas_reencontro=respostas_recentes, personagem_consultado=personagem)
    detalhes = _consulta_detalhes_cena(texto)
    if detalhes is not None:
        return RetomadaCriacao(str(plano['id']), texto, (), False, None,
                              respostas_reencontro=respostas_recentes, detalhes_cena=detalhes)
    if _consulta_distincao_citacao(texto):
        return RetomadaCriacao(str(plano['id']), texto, (), False, None,
            consulta_distincao=True, distincao_do_usuario=_distincao_publicada(mensagens_anteriores_usuario))
    consulta_exemplo = _consulta_exemplo_recente(texto)
    if consulta_exemplo:
        return RetomadaCriacao(str(plano['id']), texto, (), False, None,
            consulta_exemplo=consulta_exemplo,
            exemplo_do_usuario=mensagens_anteriores_usuario[-1] if mensagens_anteriores_usuario else '')
    papeis = _papeis_da_consulta(texto)
    if papeis:
        return RetomadaCriacao(str(plano['id']), texto, (), False, None,
                              papeis_cena=papeis, respostas_reencontro=respostas_recentes)
    if pedido_tema_e_pergunta_reencontro(texto):
        return RetomadaCriacao(str(plano['id']), texto, (), False, None,
                              consulta_reencontro='tema', respostas_reencontro=respostas_recentes)
    if _pede_pergunta_publicada_no_reencontro(texto):
        return RetomadaCriacao(str(plano['id']), texto, (), False, None,
                              consulta_reencontro='pergunta', respostas_reencontro=respostas_recentes)
    proposta = _recorte_proposta_inicial(texto)
    if proposta is not None and classificar_atualidade_factual(texto)['depende_atualidade']:
        proposta = None
    escolha_inicial = recorte_escolha_inicial(texto)
    if escolha_inicial or proposta is not None:
        registro = mente.get('registro_semantico') or {}
        observada = selecionar_primeira_fala_textual(registro) if isinstance(registro, Mapping) else {}
        fonte = None
        if observada and not observada.get('resultados') and observada['turno_id'] != str(plano['id']):
            fonte = ReferenciaFalaConsulta(str(plano['id']), texto, observada['id'], observada['turno_id'],
                                          observada['fala'], observada['ts'])
        return RetomadaCriacao(str(plano['id']), texto, (), False, fonte,
                              escolha_inicial=escolha_inicial, proposta_inicial=proposta)
    objeto_nomeado = recorte_nome_publicado(texto)
    if objeto_nomeado:
        turno_id = str(plano['id'])
        registro = mente.get('registro_semantico') or {}
        candidatas = []
        for item in registro.get('falas_observadas', ()) if isinstance(registro, Mapping) else ():
            if not isinstance(item, Mapping) or not isinstance(item.get('id'), str):
                continue
            observada = selecionar_fala_observada(registro, ocorrencia_id=item['id'])
            if (not observada or observada.get('resultados') or observada['turno_id'] == turno_id
                    or not _nome_publicado(observada['fala'], objeto_nomeado, conferir_qualificador=False)):
                continue
            candidatas.append(ReferenciaFalaConsulta(turno_id, texto, observada['id'],
                observada['turno_id'], observada['fala'], observada['ts']))
        fonte = candidatas[0] if len(candidatas) == 1 else None
        return RetomadaCriacao(turno_id, texto, (), False, fonte, objeto_nomeado=objeto_nomeado)
    objeto_inicial = recorte_primeira_mensagem(texto)
    if objeto_inicial:
        turno_id = str(plano['id'])
        registro = mente.get('registro_semantico') or {}
        observada = selecionar_primeira_fala_textual(registro) if isinstance(registro, Mapping) else {}
        fonte = None
        if observada and not observada.get('resultados') and observada['turno_id'] != turno_id:
            fonte = ReferenciaFalaConsulta(turno_id, texto, observada['id'], observada['turno_id'],
                                            observada['fala'], observada['ts'])
        return RetomadaCriacao(turno_id, texto, (objeto_inicial,), False, fonte, primeira_mensagem=True)
    recorte = _recorte_da_consulta(texto)
    detalhe = _recorte_de_detalhe(texto) if recorte is None else None
    correcao = _recorte_de_correcao(texto) if recorte is None and detalhe is None else None
    if not (recorte or detalhe or correcao) or classificar_atualidade_factual(texto)['depende_atualidade']:
        return None
    ancora, objeto = detalhe if detalhe else (recorte[0] if recorte else (), '')
    pede_regra = recorte[1] if recorte else False
    turno_id = str(plano['id'])
    registro = mente.get('registro_semantico') or {}
    candidatas = []
    for item in registro.get('falas_observadas', ()) if isinstance(registro, Mapping) else ():
        if not isinstance(item, Mapping) or not isinstance(item.get('id'), str):
            continue
        observada = selecionar_fala_observada(registro, ocorrencia_id=item['id'])
        if not observada or observada.get('resultados') or observada['turno_id'] == turno_id:
            continue
        fonte = ReferenciaFalaConsulta(turno_id, texto, observada['id'], observada['turno_id'],
                                        observada['fala'], observada['ts'])
        if fonte.vigente(texto, turno_id):
            candidatas.append(fonte)
    if correcao is not None:
        originais = [f for f in candidatas if _publicou_atributo_original(f.conteudo, correcao)]
        fonte = originais[0] if len(originais) == 1 else None
        recente = max(candidatas, key=lambda f: f.ts, default=None)
        # A retificação aponta à última descrição. Um assunto interveniente
        # não permite buscar retroativamente outra fala parecida e chamá-la de última.
        if (not fonte or recente is None or recente.ts <= fonte.ts
                or not _descreve_objeto(recente.conteudo, correcao)
                or sum(f.ts == recente.ts for f in candidatas) != 1):
            recente = None
        return RetomadaCriacao(turno_id, texto, (), False, fonte, correcao=correcao, versao_recente=recente)
    candidatas = [f for f in candidatas if _extrair_conteudo(f.conteudo, ancora=ancora, objeto_descrito=objeto)]
    fonte = candidatas[0] if len(candidatas) == 1 else None
    alternativas = tuple(candidatas) if len(candidatas) == 2 else ()
    return RetomadaCriacao(turno_id, texto, ancora, pede_regra, fonte, alternativas, objeto)


def _realizar_retomada(retomada: RetomadaCriacao) -> tuple[str, str]:
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta

    def conteudo(fonte: ReferenciaFalaConsulta | None) -> _ConteudoCriacao | None:
        if type(fonte) is ReferenciaFalaConsulta and fonte.vigente(retomada.texto_usuario, retomada.turno_id):
            return _extrair_conteudo(fonte.conteudo, ancora=retomada.ancora, objeto_descrito=retomada.objeto_descrito)
        return None

    if unico := conteudo(retomada.fonte):
        return unico.realizar(pede_regra=retomada.pede_regra)
    if len(retomada.alternativas) == 2:
        primeira, segunda = map(conteudo, retomada.alternativas)
        if primeira and segunda:
            if primeira.definicao != segunda.definicao:
                fala = f'Você quer retomar a versão com {primeira.definicao} ou com {segunda.definicao}?'
                return fala, 'esclarecimento_de_versao'
            if primeira.regra and segunda.regra and primeira.regra != segunda.regra:
                if _COORDENACAO_DA_REGRA.search(primeira.regra + ' ' + segunda.regra):
                    fala = f'Qual regra você quer retomar, «{primeira.regra}» ou «{segunda.regra}»?'
                else:
                    fala = f'Você quer a versão em que {primeira.regra} ou aquela em que {segunda.regra}?'
                return fala, 'esclarecimento_de_versao'
    return '', 'ausente'


def _realizar_correcao(retomada: RetomadaCriacao, correcao: _CorrecaoDeDetalhe) -> tuple[str, str]:
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta

    fonte = retomada.fonte
    if (type(fonte) is not ReferenciaFalaConsulta or not fonte.vigente(retomada.texto_usuario, retomada.turno_id)
            or not _publicou_atributo_original(fonte.conteudo, correcao)):
        return '', 'ausente'
    recente = retomada.versao_recente
    estado, material = '', ''
    if (type(recente) is ReferenciaFalaConsulta and recente.vigente(retomada.texto_usuario, retomada.turno_id)
            and recente.ts > fonte.ts and recente.turno_origem != fonte.turno_origem):
        estado, material = _comparar_descricao(recente.conteudo, correcao)
    inicio = f'Na primeira descrição, {correcao.detalhe}.'
    if estado == 'omitido':
        return (f'{inicio} Na última, falei de {material} e deixei esse detalhe de fora. '
                + correcao.descricao_ajustada(material), 'correcao_conferida')
    if estado == 'presente':
        return (f'{inicio} Esse detalhe já aparece na descrição mais recente. '
                + correcao.descricao_ajustada(), 'detalhe_preservado')
    return f'{inicio} {correcao.descricao_ajustada()}', 'detalhe_original_conferido'


def _realizar_proposta_inicial(retomada: RetomadaCriacao, consulta: ConsultaPropostaInicial) -> str:
    from datetime import date
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta

    fonte = retomada.fonte
    if (type(fonte) is not ReferenciaFalaConsulta or not fonte.vigente(retomada.texto_usuario, retomada.turno_id)
            or (consulta.hoje and date.fromtimestamp(fonte.ts) != date.today())):
        return ''
    proposta = _extrair_proposta_publicada(fonte.conteudo, consulta.objeto)
    if proposta is None:
        return ''
    acao, pergunta = proposta
    if not acao or any(c in acao for c in '«»'):
        return ''
    if pergunta:
        resposta = f'Na primeira mensagem, sugeri {acao}: «{pergunta}».'
    else:
        resposta = f'Na primeira mensagem, sugeri: «{acao}».'
    if consulta.tema_aplicacao:
        passo = 'faria essa pergunta' if pergunta else 'discutiria essa proposta'
        resposta += f' Na conversa sobre {consulta.tema_aplicacao}, eu {passo} antes de tirar uma conclusão.'
    return resposta


def avaliar_retomada_criacao(fala: str, *, plano: Mapping[str, Any]) -> dict[str, Any]:
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta
    contrato = plano.get('contrato_fala') or {}
    retomada = contrato.get('retomada_criacao')
    texto, turno_id = plano.get('texto_usuario'), str(plano.get('id') or '')
    realizacao, cobertura = '', 'ausente'
    limite = _LIMITE
    if (type(retomada) is RetomadaCriacao and retomada.turno_id == turno_id
            and retomada.texto_usuario == texto and contrato.get('origem') == 'mente_unica'
            and str(contrato.get('turno_id')) == turno_id and contrato.get('autoriza_execucao') is False
            and plano.get('autoriza_execucao') is False and not plano.get('comandos')
            and not plano.get('requer_execucao')):
        correcao = retomada.correcao
        if retomada.consulta_lista_usuario:
            limite = 'Pode repetir a lista para eu conferir os itens com as suas palavras?'
            if pedido_repeticao_itens_mencionados(texto) and retomada.lista_do_usuario:
                realizacao = retomada.lista_do_usuario + '.'
                cobertura = 'lista_literal_do_interlocutor'
        elif retomada.personagem_consultado:
            limite = 'Qual fala do personagem você quer que eu cite?'
            if retomada.personagem_consultado == _personagem_de_fala_recente(texto):
                realizacao = _citar_fala_do_personagem(retomada)
                cobertura = 'fala_atribuida_ao_personagem' if realizacao else 'ausente'
        elif retomada.detalhes_cena is not None:
            limite = 'Pode me mostrar a fala completa da personagem para eu conferir os detalhes?'
            if retomada.detalhes_cena == _consulta_detalhes_cena(texto):
                realizacao = _realizar_detalhes_cena(retomada, retomada.detalhes_cena)
                cobertura = 'detalhes_da_fala_publicada' if realizacao else 'ausente'
        elif retomada.consulta_distincao:
            limite = 'Pode me lembrar como formulamos a diferença entre citação e interpretação?'
            if _consulta_distincao_citacao(texto) and retomada.distincao_do_usuario:
                realizacao = f'Você resumiu a diferença assim: «{retomada.distincao_do_usuario}»'
                cobertura = 'distincao_do_interlocutor'
        elif retomada.consulta_exemplo:
            limite = 'Pode me lembrar do exemplo para eu conferir o motivo da demora e como a outra pessoa se sentiu?'
            if retomada.consulta_exemplo == _consulta_exemplo_recente(texto):
                situacao = _recortar_exemplo(retomada.exemplo_do_usuario, retomada.consulta_exemplo)
                if situacao:
                    realizacao = f'No exemplo que você contou: «{situacao}.»'
                    cobertura = 'exemplo_do_interlocutor'
        elif retomada.papeis_cena:
            limite = 'Você pode me lembrar das falas de cada pessoa nessa cena?'
            if retomada.papeis_cena == _papeis_da_consulta(texto):
                realizacao = _realizar_falas_da_cena(retomada)
                cobertura = 'falas_da_cena_publicada' if realizacao else 'ausente'
        elif retomada.consulta_reencontro == 'pergunta':
            limite = 'Não encontrei essa pergunta no histórico disponível. Qual trecho você lembra?'
            if _pede_pergunta_publicada_no_reencontro(texto):
                realizacao = _realizar_pergunta_reencontro(retomada)
                cobertura = 'pergunta_publicada_de_reencontro' if realizacao else 'ausente'
        elif retomada.consulta_reencontro == 'tema':
            limite = 'Não encontrei o tema que ficou para retomarmos. Qual você lembra que combinamos?'
            if pedido_tema_e_pergunta_reencontro(texto):
                realizacao = _realizar_tema_reencontro(retomada)
                cobertura = 'tema_e_pergunta_de_reencontro' if realizacao else 'ausente'
        elif retomada.proposta_inicial is not None:
            limite = 'Você lembra de como formulei a proposta na primeira mensagem?'
            if retomada.proposta_inicial == _recorte_proposta_inicial(texto):
                realizacao = _realizar_proposta_inicial(retomada, retomada.proposta_inicial)
                cobertura = 'proposta_inicial_publicada' if realizacao else 'ausente'
        elif retomada.escolha_inicial and retomada.escolha_inicial == recorte_escolha_inicial(texto):
            fonte = retomada.fonte
            if type(fonte) is ReferenciaFalaConsulta and fonte.vigente(texto, turno_id):
                realizacao = _nome_escolha_inicial(fonte.conteudo, retomada.escolha_inicial)
                cobertura = 'escolha_inicial_publicada' if realizacao else 'ausente'
            limite = f'Qual proposta inicial para {retomada.escolha_inicial} você quer retomar?'
        elif retomada.objeto_nomeado and retomada.objeto_nomeado == recorte_nome_publicado(texto):
            from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta
            fonte = retomada.fonte
            if type(fonte) is ReferenciaFalaConsulta and fonte.vigente(texto, turno_id):
                realizacao = _nome_publicado(fonte.conteudo, retomada.objeto_nomeado)
                cobertura = 'nome_publicado' if realizacao else 'ausente'
            limite = f'Qual nome você quer retomar para {retomada.objeto_nomeado}?'
        elif correcao is not None and correcao == _recorte_de_correcao(texto):
            realizacao, cobertura = _realizar_correcao(retomada, correcao)
            limite = f'Vou manter o detalhe que você apontou na história: {correcao.detalhe}.'
        elif retomada.primeira_mensagem and retomada.ancora == (recorte_primeira_mensagem(texto),):
            realizacao, cobertura = _realizar_primeira_mensagem(retomada)
            limite = 'Não tenho o texto da primeira mensagem para conferir esses detalhes.'
        elif correcao is None and not retomada.primeira_mensagem:
            realizacao, cobertura = _realizar_retomada(retomada)
    esperada = realizacao or limite
    aceita = ' '.join(str(fala or '').split()) == ' '.join(esperada.split())
    return {'fala': esperada, 'problemas': [] if aceita else ['retomada_criacao_sem_apoio'],
            'acao': 'aceita' if aceita else 'ajustada', 'fonte_valida': bool(realizacao),
            'cobertura': cobertura if aceita else 'ausente',
            'prova_semantica_livre': False, 'autoriza_execucao': False}
