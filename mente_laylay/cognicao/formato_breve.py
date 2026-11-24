"""Formato estrito da entrega conversacional, vinculado à fala atual."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico, pedido_dialogo_discursivo
from mente_laylay.cognicao.referencias_linguagem import enunciados_discursivos, intervalos_citados, texto_fora_de_citacoes


DESCUMPRIDO = 'formato_breve_descumprido'
_FORMATO = re.compile(
    r'(?:(?:responda|responde|diga)\s+em\s+|(?:so|apenas|somente)\s+)?'
    r'uma (?P<unidade>frase|palavra)(?:\s+(?:so|ja basta|e suficiente))?'
    r'(?:,\s*(?:por favor|sem repetir a (?:mensagem|resposta|fala) anterior))?[.!]*'
)
_PALAVRA = re.compile(r'[^\W\d_]+(?:-[^\W\d_]+)*[.!]?', re.UNICODE)
_FIM_CITADO = re.compile(r'([.!?])(?:["”»’\']+)(?:[.!?]+)?(?=\s|$)')
_QUANTIDADE_DE_FRASES = re.compile(
    r'(?:(?:[^.!?;:]{1,65}:)\s*)?(?:diga|responda|explique|conte) em '
    r'(?P<quantidade>duas|tres|quatro|cinco|[2-5]) frases\b'
)


@dataclass(frozen=True, slots=True)
class FormatoBreve:
    turno_id: str
    texto_usuario: str
    unidade: str
    evita_repeticao: bool
    conteudo_anteposto: str = ''
    quantidade: int = 1

    def instrucao(self) -> str:
        if self.unidade == 'fala':
            return f'Escreva exatamente {self.quantidade} falas. Identifique cada personagem antes da fala.'
        if self.conteudo_anteposto:
            return (f'Entregue o conteúdo solicitado ({self.conteudo_anteposto}) e exatamente uma frase de motivo. '
                    'Pode reunir ambos numa frase; se separar, a primeira parte deve conter '
                    'somente a escolha/nome, sem justificativa. Não acrescente outra frase ao motivo.')
        instrucoes = (f'Entregue exatamente {self.quantidade} frases, sem pergunta extra nem preâmbulo.'
                      if self.quantidade > 1 else
                      f'Entregue exatamente uma {self.unidade}, sem preâmbulo nem complemento.')
        return instrucoes + (' Não repita a mensagem anterior.' if self.evita_repeticao else '')

    def aceita(self, fala: str, *, ultima_resposta: str = '') -> bool:
        resposta = fala.strip()
        if self.unidade == 'fala':
            return _quantidade_de_falas(resposta) == self.quantidade
        if (self.evita_repeticao and ultima_resposta
                and normalizar_texto_basico(resposta) == normalizar_texto_basico(ultima_resposta)):
            return False
        if self.unidade == 'frase':
            projecao = _FIM_CITADO.sub(r'\1', resposta)
            partes = enunciados_discursivos(projecao, intervalos_protegidos=(), separar_ponto_e_virgula=False)
            if self.conteudo_anteposto and len(partes) == 2:
                return _conteudo_sem_justificativa(partes[0])
            return len(partes) == self.quantidade and bool(re.search(r'[^\W_]', resposta))
        citacoes = intervalos_citados(resposta)
        if citacoes == ((0, len(resposta)),):
            resposta = resposta[1:-1]
        return bool(_PALAVRA.fullmatch(resposta))


def _quantidade_de_falas(resposta: str) -> int:
    """Conta intervenções delimitadas. Interrogações internas pertencem à mesma fala."""
    corpo = texto_fora_de_citacoes(resposta).strip()
    marcador = r'(?:[—–]\s+|(?:[^\W\d_]+(?:\s+[^\W\d_]+){0,2}|\d+)\s*:\s*)'
    inicios = list(re.finditer(r'(?:^|(?<=[.!?])\s+|\n+)' + marcador, corpo))
    if not inicios or inicios[0].start() != 0:
        return 0
    limites = [m.start() for m in inicios[1:]] + [len(corpo)]
    if not all(corpo[m.end():fim].strip() for m, fim in zip(inicios, limites)):
        return 0
    return len(inicios)


def construir_formato_breve(texto: str, *, plano: Mapping[str, Any]) -> FormatoBreve | None:
    if (not plano.get('id') or plano.get('texto_usuario') != texto or plano.get('autoriza_execucao') is not False
            or plano.get('requer_execucao') or plano.get('comandos')):
        return None
    partes = enunciados_discursivos(texto)
    if not partes:
        return None
    numeros_por_extenso = {'duas': 2, 'tres': 3, 'quatro': 4, 'cinco': 5}
    for parte in partes:
        ext = _QUANTIDADE_DE_FRASES.match(normalizar_texto_basico(parte))
        if ext:
            valor = ext['quantidade']
            quantidade = int(valor) if valor.isdecimal() else numeros_por_extenso[valor]
            return FormatoBreve(str(plano['id']), texto, 'frase', False, quantidade=quantidade)
    quantidades = [m['quantidade'] for parte in partes if (m := pedido_dialogo_discursivo(parte))]
    if len(quantidades) == 1 and quantidades[0]:
        valor = quantidades[0]
        numeros = {'uma': 1, 'duas': 2, 'tres': 3, 'quatro': 4, 'cinco': 5}
        n = int(valor) if valor.isdecimal() and len(valor) <= 3 else numeros.get(valor)
        if n:
            return FormatoBreve(str(plano['id']), texto, 'fala', False, quantidade=n)
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
    if (type(formato) is FormatoBreve and formato.unidade in {'frase', 'palavra', 'fala'}
            and formato.turno_id == str(plano.get('id')) and formato.texto_usuario == plano.get('texto_usuario')
            and str(contrato.get('turno_id')) == formato.turno_id and contrato.get('origem') == 'mente_unica'
            and contrato.get('autoriza_execucao') is False and plano.get('autoriza_execucao') is False
            and not plano.get('requer_execucao') and not plano.get('comandos')):
        return formato
    return None


def restaurar_linhas_dialogo(fala: str, plano: Mapping[str, Any]) -> str:
    formato = formato_breve_vigente(plano)
    if not formato or formato.unidade != 'fala' or not formato.aceita(fala):
        return fala
    citados = intervalos_citados(fala)
    cortes = [m.span() for m in re.finditer(
        r'(?<=[.!?]) +(?=(?:[^\W\d_]+(?: [\w-]+){0,2}): )', fala)
        if not any(a <= m.start() < b for a,b in citados)]
    if len(cortes) + 1 == formato.quantidade:
        for a,b in reversed(cortes):
            fala = fala[:a] + '\n' + fala[b:]
    return fala


def dialogo_ficcional_inteiramente_atribuido(fala: str, plano: Mapping[str, Any]) -> bool:
    """Usa o formato vigente para distinguir personagens da voz da assistente."""
    formato = formato_breve_vigente(plano)
    if formato is None or formato.unidade != 'fala' or not formato.aceita(fala):
        return False
    pedido = pedido_dialogo_discursivo(formato.texto_usuario)
    if pedido is None or not pedido['genero']:
        return False
    linhas = restaurar_linhas_dialogo(fala, plano).splitlines()
    if len(linhas) != formato.quantidade:
        return False
    personagens = set()
    for linha in linhas:
        nome, separador, corpo = linha.partition(':')
        if (not separador or not corpo.strip()
                or not re.fullmatch(r'[^\W\d_]+(?: [\w-]+){0,2}', nome)
                or re.search(r'\b(?:laylay|lay|assistente|eu)\b', nome, re.I)):
            return False
        personagens.add(nome.casefold())
    return len(personagens) >= 2


def vincular_dialogo_ao_pacote(pacote, *, plano: Mapping[str, Any]):
    from dataclasses import replace
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    from mente_laylay.cognicao.suporte_autoria import conferir_suporte_proposicoes

    formato = formato_breve_vigente(plano)
    base = pacote.contrato_saida
    if (not formato or formato.unidade != 'fala' or formato.quantidade > 8 or pacote.contexto_fechado
            or not base or base.nome not in {'autoria_livre_v5', 'autoria_referenciada_v5'}):
        return pacote
    esquema = base.response_format['json_schema']['schema']
    unidades = esquema['properties']['suporte_proposicoes']
    formas = unidades['items'].get('anyOf', [unidades['items']])
    if any('pattern' in f['properties']['texto'] for f in formas):
        return pacote
    unidades['minItems'] = unidades['maxItems'] = formato.quantidade
    dupla_anonima = any(
        m and re.fullmatch(r'(?:(?:essas|estas|aquelas) )?(?:duas|2) pessoas', m['participantes'] or '')
        for parte in enunciados_discursivos(formato.texto_usuario)
        if (m := pedido_dialogo_discursivo(parte)))
    for forma in formas:
        forma['required'].append('personagem')
        forma['properties']['personagem'] = {'type': 'string', 'minLength': 1, 'maxLength': 40}
        if dupla_anonima:
            forma['properties']['personagem']['enum'] = ['Pessoa A', 'Pessoa B']

    def validar(dados):
        itens = dados.get('suporte_proposicoes')
        if not isinstance(itens, list) or len(itens) != formato.quantidade:
            raise ValueError('quantidade_de_falas_divergente')
        linhas = []
        declaracoes = []
        personagens = set()
        for item in itens:
            personagem = item.get('personagem') if isinstance(item, dict) else None
            if (not isinstance(personagem, str) or len(personagem) > 40
                    or (dupla_anonima and personagem not in {'Pessoa A', 'Pessoa B'})
                    or not re.fullmatch(r'[^\W\d_]+(?: [\w-]+){0,2}', personagem)
                    or not isinstance(item.get('texto'), str) or not item['texto'].strip()):
                raise ValueError('intervencao_sem_personagem_ou_texto')
            linha = f"{personagem}: {item['texto']}"
            personagens.add(personagem.casefold())
            linhas.append(linha)
            declaracoes.append({k:v for k,v in item.items() if k != 'personagem'} | {'texto':linha})
        fala = '\n'.join(linhas)
        if (len(itens) > 1 and len(personagens) < 2) or not formato.aceita(fala):
            raise ValueError('intervencoes_fora_do_formato')
        proposta = {**dados, 'suporte_proposicoes': declaracoes}
        base.validar(proposta)
        proposta['fala'] = fala
        conferir_suporte_proposicoes(proposta)
        dados.update(proposta)

    codec = ContratoSaidaEstruturada(base.nome, base.marcador, esquema, validar)
    instrucao = ('Cada item de suporte_proposicoes é uma intervenção no diálogo. Preencha personagem com '
                 'quem fala, respeitando os participantes da cena. Use nomes distintos para pessoas distintas. '
                 'Alterne os interlocutores. Em texto, escreva as palavras que esse personagem dirige ao outro, '
                 'sem narrador nem rótulo. Termine a fala com pontuação. Preserve as fontes de cada item.')
    return replace(pacote, contrato_saida=codec, mensagens=(
        {'role': 'system', 'content': instrucao}, *pacote.mensagens))
