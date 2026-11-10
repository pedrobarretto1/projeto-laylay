"""Formato estrito da entrega conversacional, vinculado à fala atual."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.referencias_linguagem import enunciados_discursivos, intervalos_citados


DESCUMPRIDO = 'formato_breve_descumprido'
_FORMATO = re.compile(
    r'(?:(?:responda|responde|diga)\s+em\s+|(?:so|apenas|somente)\s+)?'
    r'uma (?P<unidade>frase|palavra)(?:\s+(?:so|ja basta|e suficiente))?'
    r'(?:,\s*(?:por favor|sem repetir a (?:mensagem|resposta|fala) anterior))?[.!]*'
)
_PALAVRA = re.compile(r'[^\W\d_]+(?:-[^\W\d_]+)*[.!]?', re.UNICODE)
_FIM_CITADO = re.compile(r'([.!?])(?:["”»’\']+)(?:[.!?]+)?(?=\s|$)')


@dataclass(frozen=True, slots=True)
class FormatoBreve:
    turno_id: str
    texto_usuario: str
    unidade: str
    evita_repeticao: bool

    def instrucao(self) -> str:
        instrucoes = f'Entregue exatamente uma {self.unidade}, sem preâmbulo nem complemento.'
        return instrucoes + (' Não repita a mensagem anterior.' if self.evita_repeticao else '')

    def aceita(self, fala: str, *, ultima_resposta: str = '') -> bool:
        resposta = fala.strip()
        if (self.evita_repeticao and ultima_resposta
                and normalizar_texto_basico(resposta) == normalizar_texto_basico(ultima_resposta)):
            return False
        if self.unidade == 'frase':
            projecao = _FIM_CITADO.sub(r'\1', resposta)
            partes = enunciados_discursivos(projecao, intervalos_protegidos=(), separar_ponto_e_virgula=False)
            return len(partes) == 1 and bool(re.search(r'[^\W_]', resposta))
        citacoes = intervalos_citados(resposta)
        if citacoes == ((0, len(resposta)),):
            resposta = resposta[1:-1]
        return bool(_PALAVRA.fullmatch(resposta))


def construir_formato_breve(texto: str, *, plano: Mapping[str, Any]) -> FormatoBreve | None:
    if (not plano.get('id') or plano.get('texto_usuario') != texto or plano.get('autoriza_execucao') is not False
            or plano.get('requer_execucao') or plano.get('comandos')):
        return None
    partes = enunciados_discursivos(texto)
    if not partes:
        return None
    ultimo = normalizar_texto_basico(partes[-1])
    pedido = _FORMATO.fullmatch(ultimo)
    if pedido is None:
        # A qualificação prévia já resolve unidade, quantidade e modificadores.
        # Reutilizar esse owner evita reclassificar "frase curta" por outro
        # léxico. O contrato de entrega continua limitado às unidades que sabe
        # verificar, sem deduzir uma frase de "até/duas ou três/pelo menos".
        from mente_laylay.cognicao.qualificacao_intencao import qualificar_intencao_por_capacidades
        qualificacoes = [q for parte in partes
                        if (q := qualificar_intencao_por_capacidades(parte)) is not None]
        if len(qualificacoes) != 1:
            return None
        candidato = qualificacoes[0].candidatos[0]
        if candidato.quantidade not in {'uma', '1'} or candidato.unidade not in {'frase', 'palavra'}:
            return None
        return FormatoBreve(str(plano['id']), texto, candidato.unidade, False)
    return FormatoBreve(str(plano['id']), texto, pedido['unidade'], 'sem repetir' in ultimo)


def formato_breve_vigente(plano: Mapping[str, Any]) -> FormatoBreve | None:
    contrato = plano.get('contrato_fala') or {}
    formato = contrato.get('formato_breve')
    if (type(formato) is FormatoBreve and formato.unidade in {'frase', 'palavra'}
            and formato.turno_id == str(plano.get('id')) and formato.texto_usuario == plano.get('texto_usuario')
            and str(contrato.get('turno_id')) == formato.turno_id and contrato.get('origem') == 'mente_unica'
            and contrato.get('autoriza_execucao') is False and plano.get('autoriza_execucao') is False
            and not plano.get('requer_execucao') and not plano.get('comandos')):
        return formato
    return None
