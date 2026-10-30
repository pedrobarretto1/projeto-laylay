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
    contem_moldura_narrativa,
)

_HISTORICAS = frozenset({'explicacoes_historicas_por_ato', 'explicacao_ocorrencia',
                       'evidencia_fala_historica', 'revisao_alegacao'})


@dataclass(frozen=True, slots=True)
class CriacaoFiccional:
    turno_id: str
    texto_usuario: str
    turno_origem: str
    pedido_origem: str
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
    base = normalizar_texto_basico(texto_fora_de_citacoes(texto))
    if (referencia_explicacao_historica(texto)
        or re.search(r'\b(?:mundo real|na realidade|de verdade|realmente|real|fontes?|evidencias?)\b', base)):
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
        or re.search(r'^(?:invente|crie|conte|escreva|imagine|imagina)\b.+\b(?:historia|conto|ficcao|personagem)\b', base))
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
    if criacao_ficcional_vigente(plano) is None:
        return pacote
    base = pacote.contrato_saida
    if base is None or base.nome != 'autoria_livre_v5':
        return pacote
    esquema = base.response_format['json_schema']['schema']
    unidades = esquema['properties']['suporte_proposicoes']
    unidades['minItems'] = unidades['maxItems'] = 1
    unidades['items']['properties']['texto']['pattern'] = '^Na história, .+'
    def validar(dados):
        unidades_propostas = dados.get('suporte_proposicoes')
        if (not isinstance(unidades_propostas, list) or len(unidades_propostas) != 1
            or not isinstance(unidades_propostas[0], dict)
            or type(unidades_propostas[0].get('texto')) is not str
            or not fala_ficcional_delimitada(unidades_propostas[0]['texto'])):
            raise ValueError('moldura_ficcional_ausente_ou_extrapolada')
        base.validar(dados)
    # Nome preserva a idempotência da negociação de suporte nas rotas
    # auxiliares; o validator existente continua sendo chamado integralmente.
    codec = ContratoSaidaEstruturada(base.nome, base.marcador, esquema, validar)
    mensagens = [dict(m) for m in pacote.mensagens]
    indice = next((i for i,m in enumerate(mensagens) if m.get('role') == 'system'), None)
    instrucao = ('Delimitação ficcional do pedido atual: comece o texto com Na história, '
        'e mantenha toda a resposta nesse cenário. Escreva uma unidade integral em suporte_proposicoes, '
        'até4000 caracteres. O corpo é sua criação; não faça alegações de observação ou efeito real.')
    if indice is None:
        mensagens.insert(0, {'role':'system', 'content':instrucao})
    else:
        mensagens[indice]['content'] += '\n' + instrucao
    return replace(pacote, mensagens=tuple(mensagens), contrato_saida=codec)
