"""Finalidade de formular uma fala, sem conferir fatos no texto proposto."""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import tipo_transformacao_conversacional
from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
from mente_laylay.cognicao.referencias_linguagem import texto_fora_de_citacoes
from mente_laylay.personalidade.proporcao_resposta import classificar_proporcao

_FINALIDADES_DIVERGENTES = frozenset({'explicacao_ocorrencia','explicacoes_historicas_por_ato',
    'evidencia_fala_historica','revisao_alegacao','opiniao_autoral','adequacao_pessoal','criacao_ficcional'})

_CONSULTA_FORMULACAO = re.compile(
    r'\b(?:qual|que)\s+(?:frase|resposta|mensagem|pergunta|texto|palavras)\b'
    r'[^.!?;]*\b(?:diria|falaria|escreveria|perguntaria|responderia)\b', re.I,
)


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
