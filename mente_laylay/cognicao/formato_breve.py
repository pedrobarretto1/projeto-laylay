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
    conteudo_anteposto: str = ''

    def instrucao(self) -> str:
        if self.conteudo_anteposto:
            return (f'Entregue o conteúdo solicitado ({self.conteudo_anteposto}) e exatamente uma frase de motivo. '
                    'Pode reunir ambos numa frase; se separar, a primeira parte deve conter '
                    'somente a escolha/nome, sem justificativa. Não acrescente outra frase ao motivo.')
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
            if self.conteudo_anteposto and len(partes) == 2:
                return _conteudo_sem_justificativa(partes[0])
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
        candidatos = qualificacoes[0].candidatos
        if len(candidatos) == 2:
            conteudo, formato = candidatos
            if (conteudo.capacidade == 'conversa.conteudo_resposta'
                    and conteudo.quantidade in {'um', 'uma', '1'}
                    and formato.capacidade == 'conversa.formato_resposta'
                    and formato.quantidade in {'uma', '1'} and formato.unidade == 'frase'
                    and formato.conteudo in {'motivo', 'justificativa'}):
                return FormatoBreve(str(plano['id']), texto, 'frase', False, conteudo.unidade)
            return None
        if len(candidatos) != 1:
            return None
        candidato = candidatos[0]
        if candidato.quantidade not in {'uma', '1'} or candidato.unidade not in {'frase', 'palavra'}:
            return None
        return FormatoBreve(str(plano['id']), texto, candidato.unidade, False)
    return FormatoBreve(str(plano['id']), texto, pedido['unidade'], 'sem repetir' in ultimo)


def _conteudo_sem_justificativa(texto: str) -> bool:
    """Primeira parte nominal, com ato de escolha e infinitivo opcionais.

    Não confere a pertinência da escolha; apenas impede que uma justificativa
    já iniciada ganhe mais uma frase por ser contada como nome da escolha.
    """
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel, consultar_morfologia
    corpo = re.sub(r'^(?:eu\s+)?(?:escolho|escolheria|prefiro|preferiria)\s+', '', texto.strip(), flags=re.I)
    corpo = corpo.rstrip(' .!')
    palavras = corpo.split()
    if palavras and re.fullmatch(r'[^\W\d_]+(?:ar|er|ir)', palavras[0]) and (consultar_morfologia(palavras[0]) or 0) & 32:
        corpo = ' '.join(palavras[1:])
    return grupo_nominal_de_papel(corpo)


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
