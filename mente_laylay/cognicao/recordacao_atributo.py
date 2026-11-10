"""Conferência extrativa de atributo lembrado, sem inferência factual livre.

A escolha interrogada não é evidência. O host vincula a consulta completa a
declarações do usuário e conserva versões, autoria e modalizadores. Só uma
relação nominal/copulativa fechada permite a realização elíptica; fora dela
não se inventa um valor nem se certifica o conteúdo como fato externo.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
import unicodedata
from typing import Any, Mapping

from mente_laylay.cognicao.referencias_linguagem import (
    complemento_recordacao_dialogo, enunciados_discursivos, intervalos_citados,
    trecho_retificacao_do_enunciador,
)
from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia, grupo_nominal_de_papel

_PALAVRA = r'[^\W\d_]+'
_COPULA = r'(?:era|eram|é|são|estava|estavam|está|estão)'
_RETIFICACAO = re.compile(r'^(?:corre[cç][aã]o|corrigindo)\s*:\s*', re.I)


def _literal(texto: str) -> str:
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', texto).casefold()).strip(' .!')


def _identidade(texto: str) -> tuple[str, ...]:
    grupos = re.split(r'\s+d(?:e|o|a|os|as)\s+', _literal(texto))
    if len(grupos) > 2:
        return ()
    nomes = []
    for grupo in grupos:
        grupo = re.sub(r'^(?:(?:o|a|os|as|um|uma|uns|umas)\s+)?(?:noss[oa]s?\s+)?', '', grupo)
        if not grupo_nominal_de_papel(grupo):
            return ()
        nomes.append(grupo)
    return tuple(nomes)


@dataclass(frozen=True, slots=True)
class ConsultaAtributo:
    sujeito: str
    identidade: tuple[str, ...]
    alternativas: tuple[str, ...]


def _consulta(texto: str) -> ConsultaAtributo | None:
    partes = enunciados_discursivos(texto, separar_ponto_e_virgula=False)
    perguntas = [p for p in partes if p.endswith('?')]
    if len(perguntas) != 1:
        return None
    complemento = complemento_recordacao_dialogo(perguntas[0])
    m = re.fullmatch(rf'se\s+(?P<objeto>.+?)\s+{_COPULA}\s+(?P<valores>.+)', complemento, re.I)
    aberta = re.fullmatch(rf'como\s+{_COPULA}\s+(?P<objeto>.+)', complemento, re.I)
    if (m is None and aberta is None) or intervalos_citados(texto):
        return None
    valores = ()
    if m is not None:
        valores = tuple(_literal(v) for v in re.split(r'\s*,\s*|\s+ou\s+', m['valores']))
        if not 2 <= len(valores) <= 8 or len(set(valores)) != len(valores):
            return None
        if not all(re.fullmatch(_PALAVRA, v) and (consultar_morfologia(v) or 0) & 2 for v in valores):
            return None
    sujeito = (m if m is not None else aberta)['objeto']
    identidade = _identidade(sujeito)
    if not identidade:
        return None
    # Não absorver outra pergunta/ordem como parte da resposta elíptica.
    from mente_laylay.cognicao.normalizacao_linguagem import tipo_transformacao_conversacional
    from mente_laylay.cognicao.fundamentacao_factual import _preambulo_sem_outro_pedido
    for parte in partes:
        if parte == perguntas[0]:
            continue
        if tipo_transformacao_conversacional(parte) == 'formato_resposta':
            continue
        if partes.index(parte) > partes.index(perguntas[0]):
            return None
        if not _preambulo_sem_outro_pedido(parte):
            # Predicação introdutória com cópula, sem outro verbo diretivo.
            palavras = re.findall(_PALAVRA, parte)
            if (not palavras or not re.fullmatch(_COPULA, palavras[0], re.I)
                    or any((t := consultar_morfologia(p) or 0) & 32 and not t & 1 for p in palavras[1:])):
                return None
    return ConsultaAtributo(sujeito, identidade, valores)


def _predicacao_integral(texto: str) -> tuple[tuple[str, ...], str, str] | None:
    """Forma integral: conserva cópula/tempo, sujeito e atributo, sem anexos.

    A identidade nominal pode variar nos artigos já normalizados pelo owner.
    Isso não certifica sinônimos, pronomes, causas ou equivalência semântica livre.
    """
    m = re.fullmatch(rf'(?P<objeto>.+?)\s+(?P<copula>{_COPULA})\s+(?P<valor>{_PALAVRA})', _literal(texto))
    if m is None:
        return None
    relacao = _relacao(texto)
    if relacao is None:
        return None
    return relacao[0], m['copula'], relacao[1]


def _conteudo_declarado(frase: str) -> str:
    citacoes = intervalos_citados(frase)
    if not citacoes:
        matriz, separador, conteudo = frase.partition(':')
        if separador:
            declaracao = re.fullmatch(r'(?:eu\s+)?(?:declaro|defino)\s+(.+)', matriz.strip(), re.I)
            rotulo = declaracao[1] if declaracao else re.sub(r'\s+é$', '', matriz.strip(), flags=re.I)
            if (declaracao or rotulo != matriz.strip()) and _identidade(rotulo):
                return conteudo.strip()
        return frase
    if len(citacoes) != 1:
        return ''
    inicio, fim = citacoes[0]
    posterior = frase[fim:].strip(' .!')
    # O segmentador mantém ponto dentro de aspas junto da pergunta seguinte.
    # Só uma interrogativa independente pode seguir essa declaração; ressalva,
    # correção ou continuação declarativa não são descartadas para extrair valor.
    pergunta_seguinte = bool(frase[inicio + 1:fim - 1].rstrip().endswith(('.', '!'))
        and re.fullmatch(r'(?:qual|quais|quem|como|quando|onde|por qu[eê]|o que)\s+[^?]+\?', posterior, re.I))
    if posterior and not pergunta_seguinte:
        return ''
    matriz = frase[:inicio].strip().rstrip(':').strip()
    declaracao = re.fullmatch(r'(?:eu\s+)?(?:declaro|defino)\s+(.+)', matriz, re.I)
    rotulo = declaracao[1] if declaracao else re.sub(r'\s+é$', '', matriz, flags=re.I)
    if (not declaracao and rotulo == matriz) or not _identidade(rotulo):
        return ''
    return frase[inicio + 1:fim - 1]


def _relacao(frase: str) -> tuple[tuple[str, ...], str] | None:
    base = _literal(frase)
    # Estes operadores não pertencem à relação assertiva conferida. O léxico
    # também registra "não" substantivado; isso não o torna sujeito aqui.
    if re.search(r'\b(?:não|nao|nunca|jamais|talvez|se)\b', base):
        return None
    copula = re.fullmatch(rf'(?P<objeto>.+?)\s+{_COPULA}\s+(?P<valor>{_PALAVRA})', base)
    if copula:
        identidade = _identidade(copula['objeto'])
        valor = copula['valor']
    else:
        # Grupo nominal atribuído, seguido de verbo indicativo: o atributo
        # modifica este nome, não qualquer objeto que apareça no texto.
        leituras = []
        for verbo in re.finditer(_PALAVRA, base):
            if not (consultar_morfologia(verbo[0]) or 0) & 256:
                continue
            nominal = re.fullmatch(rf'(?P<grupo>.+?)\s+(?P<valor>{_PALAVRA})\s+', base[:verbo.start()])
            if nominal and (consultar_morfologia(nominal['valor']) or 0) & 2:
                grupo = _identidade(nominal['grupo'])
                if grupo:
                    leituras.append((grupo, nominal['valor']))
        if len(leituras) != 1:
            return None
        grupo, valor = leituras[0]
        # A concordância precisa distinguir B de A. "Gato de chapéu azul"
        # admite dois referentes; "pato de óculos roxos" só concorda com B.
        if len(grupo) == 2:
            adjetivo = ((consultar_morfologia(valor) or 0) >> 13) & 15
            generos = [((consultar_morfologia(g) or 0) >> 9) & 15 for g in grupo]
            if not adjetivo or not generos[0] or not generos[1] or adjetivo & generos[0] or not adjetivo & generos[1]:
                return None
        identidade = tuple(reversed(grupo)) if len(grupo) == 2 else grupo
    if not identidade or not (consultar_morfologia(valor) or 0) & 2:
        return None
    return identidade, valor


@dataclass(frozen=True, slots=True)
class RecordacaoAtributo:
    turno_id: str
    texto_usuario: str
    consulta: ConsultaAtributo
    valor: str
    estado: str
    fontes: tuple[tuple[int, str, str], ...]
    declaracao: str = ''

    def resposta(self) -> str:
        if self.valor:
            if not self.consulta.alternativas:
                return f'Você descreveu: «{self.declaracao}».'
            return self.valor[0].upper() + self.valor[1:] + '.'
        return f'Como você tinha descrito {self.consulta.sujeito}?'

    def aceita(self, fala: str) -> bool:
        if _literal(fala) == _literal(self.resposta()):
            return True
        if self.consulta.alternativas or not self.valor:
            return False
        origem = _predicacao_integral(self.declaracao)
        return origem is not None and _predicacao_integral(fala) == origem


def construir_recordacao_atributo(texto: str, *, plano: Mapping[str, Any],
                                  mente: Mapping[str, Any]) -> RecordacaoAtributo | None:
    if (not plano.get('id') or plano.get('texto_usuario') != texto
            or plano.get('autoriza_execucao') is not False or plano.get('requer_execucao')
            or plano.get('comandos') or plano.get('texto_operacional')):
        return None
    consulta = _consulta(texto)
    if consulta is None:
        return None
    valor, estado = '', 'fonte_ausente'
    declaracao = ''
    fontes = []
    from mente_laylay.cognicao.proveniencia_informacao import classificar_proveniencia_informacao
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    bloqueadas = {normalizar_texto_basico(str(f.get('texto') or ''))
                  for f in plano.get('relatos_usuario') or ()
                  if isinstance(f, dict) and classificar_proveniencia_informacao(f).get('bloqueada')}
    for i, mensagem in enumerate(mente.get('messages') or ()):
        if not isinstance(mensagem, dict) or mensagem.get('role') != 'user':
            continue
        original = mensagem.get('content')
        if not isinstance(original, str) or not original or original == texto:
            continue
        # Sem o teto de relatos pessoais de 500 caracteres: uma correção
        # longa também precisa invalidar ou atualizar a versão anterior.
        fontes.append((i, hashlib.sha256(original.encode('utf8')).hexdigest(), original))
        for frase in enunciados_discursivos(original, separar_ponto_e_virgula=False):
            if frase.endswith('?') and not intervalos_citados(frase):
                continue
            retificacao = trecho_retificacao_do_enunciador(frase)
            corrigindo = bool(_RETIFICACAO.match(frase) or retificacao)
            corpo = retificacao or _RETIFICACAO.sub('', frase)
            declarado = _conteudo_declarado(corpo)
            relacao = _relacao(declarado) if declarado else None
            if relacao and relacao[0] != consulta.identidade:
                continue
            if relacao:
                novo = relacao[1]
                if normalizar_texto_basico(original) in bloqueadas:
                    valor, estado = '', 'fonte_bloqueada'
                elif corrigindo or estado == 'fonte_ausente' or (estado == 'conferido' and novo == valor):
                    valor, estado = novo, 'conferido'
                    declaracao = declarado
                else:
                    valor, estado = '', 'versoes_conflitantes'
            elif (corrigindo or all(re.search(r'(?<!\w)' + re.escape(n) + r'(?!\w)', _literal(corpo))
                                    for n in consulta.identidade)):
                valor, estado = '', 'relacao_nao_conferida'
    if valor and consulta.alternativas and valor not in consulta.alternativas:
        # Sem ontologia de atributos, não confundir peso com cor. Alternativas
        # delimitam a pergunta; nunca criam o valor que a fonte não declarou.
        valor, estado = '', 'dimensao_nao_conferida'
    return RecordacaoAtributo(str(plano['id']), texto, consulta, valor, estado, tuple(fontes),
                             declaracao if valor else '')


def avaliar_recordacao_atributo(fala: str, *, plano: Mapping[str, Any]) -> dict[str, Any] | None:
    contrato = plano.get('contrato_fala') or {}
    fonte = contrato.get('recordacao_atributo')
    if (type(fonte) is not RecordacaoAtributo or fonte.turno_id != str(plano.get('id'))
            or fonte.texto_usuario != plano.get('texto_usuario')
            or str(contrato.get('turno_id')) != fonte.turno_id or contrato.get('origem') != 'mente_unica'
            or contrato.get('autoriza_execucao') is not False or plano.get('autoriza_execucao') is not False
            or plano.get('requer_execucao') or plano.get('comandos') or plano.get('texto_operacional')):
        return None
    resposta = fonte.resposta()
    r = {'admissivel': fonte.aceita(fala), 'estado': 'recordacao_atributo_' + fonte.estado,
         'semantica_verificada': False, 'prova_implicacao': False, 'autoriza_execucao': False,
         'pode_confirmar_fato_externo': False, 'realizacoes': [resposta],
         'fontes_historicas': [{'indice': i, 'sha256': h} for i, h, _ in fonte.fontes]}
    r['resposta_conferida' if fonte.valor else 'esclarecimento_recordacao'] = resposta
    return r
