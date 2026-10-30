"""Autoria subjetiva limitada: posição não comprova causa, experiência ou capacidade.

O vocabulário de tipos vem da memória existente. A escolha pertence à autora;
o host confere forma, pergunta e continuidade da publicação, nunca sentimento.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, TYPE_CHECKING

from mente_laylay.cognicao.referencias_linguagem import (
    PerspectivaEnunciador, consulta_opiniao_propria, objeto_retificacao_assunto,
    consulta_explicacao_gosto,
    consulta_relacao_criterio_autoral,
    operando_opiniao_literal,
    CATEGORIAS_PREFERENCIA,
)
from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta
from mente_laylay.cognicao.criterio_autoral import (
    CriterioAutoralEmissao, CriterioAutoralPublicado, CRITERIOS_AUTORAIS,
    criterio_publicado_da_fala, validar_codigo_criterio, criterio_origem_vigente,
    FundamentoCriterioAutoral, fundamento_criterio_vigente,
)

if TYPE_CHECKING:
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt


@dataclass(frozen=True, slots=True)
class OpiniaoAutoral:
    turno_id: str
    texto_usuario: str
    modo: str
    categoria: str
    declaracoes: tuple[str, ...]
    referencia: ReferenciaFalaConsulta | None = None
    criterio: CriterioAutoralPublicado | None = None
    autoriza_execucao: bool = False
    prova_factual: bool = False
    fundamentos: tuple[FundamentoCriterioAutoral, ...] = ()


_LIMITE_MOTIVO = 'Essa fala não trouxe um motivo para a preferência.'
_LIMITE_VINCULO = 'Não tenho uma declaração de gosto correspondente a essa pergunta para explicar o motivo.'


def _sem_favorito(categoria: str) -> str:
    nome, _, genero = CATEGORIAS_PREFERENCIA[categoria]
    feminino = genero == 'a'
    return f"Ainda não escolhi um{'a' if feminino else ''} {nome} favorit{'a' if feminino else 'o'}."


def _declaracoes_da_fala(fala: str) -> tuple[str, ...]:
    """Só o ato integral coberto; uma oração causal não é absorvida."""
    base = str(fala)
    sufixo = ' ' + _LIMITE_MOTIVO
    if base.endswith(sufixo):
        base = base[:-len(sufixo)]
    if base.startswith('Quis dizer que '):
        base = base[len('Quis dizer que '):]
    correcao = re.fullmatch(r'Sim, estou falando de (?P<objeto>[\w]+(?:[ -][\w]+){0,5}): (?P<declaracao>.+)', base)
    if correcao:
        declaracao = correcao['declaracao'][:1].upper() + correcao['declaracao'][1:]
        if not _correcao_vincula_objeto(correcao['objeto'], declaracao):
            return ()
        base = declaracao
    base = base[:1].upper() + base[1:]
    declaracao = re.fullmatch(r'Eu (?:prefiro|(?:não )?gosto de) (?P<valor>[\w]+(?:[ -][\w]+){0,3})\.', base)
    if declaracao and operando_opiniao_literal(declaracao['valor']):
        return (base,)
    if base == 'Não tenho um estilo musical preferido.':
        return (base,)
    if base in tuple(_sem_favorito(c) for c in CATEGORIAS_PREFERENCIA):
        return (base,)
    return ()


def _categoria_declaracao(declaracao: str) -> str:
    from mente_laylay.memoria_mental.memoria_pessoas import classificar_gosto_explicito
    if declaracao == 'Não tenho um estilo musical preferido.':
        return 'genero_musical'
    for categoria in CATEGORIAS_PREFERENCIA:
        if declaracao == _sem_favorito(categoria):
            return 'favorito:' + categoria
    valor = re.sub(r'^Eu (?:prefiro|(?:não )?gosto de) ', '', declaracao).rstrip('.')
    return 'genero_musical' if classificar_gosto_explicito(valor)[0] == 'genero_musical' else ''


def _declaracoes_para_motivo(fala: str) -> tuple[str, ...]:
    """Não declarar ausência de motivo por uma gramática aberta de nomes.

    Um nome composto sem tipo conhecido também pode esconder uma finalidade
    ou oração. Só unidade nominal simples ou tipo já reconhecido entra aqui;
    demais textos continuam sem cobertura, não são causas verificadas.
    """
    declaracoes = _declaracoes_da_fala(fala)
    if not declaracoes:
        return ()
    declaracao = declaracoes[0]
    valor = re.sub(r'^Eu (?:prefiro|(?:não )?gosto de) ', '', declaracao).rstrip('.')
    return declaracoes if _categoria_declaracao(declaracao) or ' ' not in valor else ()


def _declaracoes_observadas(registro: Mapping[str, Any] | None, fala: Mapping[str, Any], *,
    para_motivo: bool = False) -> tuple[str, ...]:
    criterio = criterio_publicado_da_fala(registro, fala)
    if criterio is not None:
        return (criterio.declaracao,)
    return (_declaracoes_para_motivo if para_motivo else _declaracoes_da_fala)(str(fala.get('fala') or ''))


def _opcoes_consulta(pergunta: Mapping[str, Any]) -> tuple[str, tuple[str, ...]]:
    from mente_laylay.memoria_mental.memoria_pessoas import generos_musicais_conhecidos, classificar_gosto_explicito
    if pergunta['tipo'] == 'categoria':
        return 'genero_musical', tuple(f'Eu prefiro {g}.' for g in generos_musicais_conhecidos()) + (
            'Não tenho um estilo musical preferido.',)
    if pergunta['tipo'] == 'favorito':
        # Autoria não qualifica a existência/categoria de um título proposto.
        # Sem inventário de alvos fundamentados, não criar um favorito factual
        # nem iniciar pesquisa obrigatória para sustentar uma conversa casual.
        categoria = str(pergunta['categoria'])
        return 'favorito:' + categoria, (_sem_favorito(categoria),)
    if pergunta['tipo'] == 'polar':
        alvo = str(pergunta['alvo'])
        categoria = 'genero_musical' if classificar_gosto_explicito(alvo)[0] == 'genero_musical' else ''
        if not categoria and ' ' in alvo:
            return '', ()
        return categoria, (f'Eu gosto de {alvo}.', f'Eu não gosto de {alvo}.')
    if pergunta['tipo'] == 'escolha':
        return '', tuple(f'Eu prefiro {a}.' for a in pergunta['alternativas'])
    return '', ()


def _correcao_vincula_objeto(correcao: str, declaracao: str) -> bool:
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    objeto = re.sub(r'^Eu (?:prefiro|(?:não )?gosto de) ', '', declaracao).rstrip('.')
    return (normalizar_texto_basico(correcao) == normalizar_texto_basico(objeto)
        or (_categoria_declaracao(declaracao) == 'genero_musical'
            and normalizar_texto_basico(correcao) in {'musica', 'musicas', 'genero musical', 'estilo musical'}))


def _motivo_vincula_declaracao(consulta: Mapping[str, Any], declaracao: str) -> bool:
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    if consulta['tipo'] == 'eliptica':
        return True
    m = re.fullmatch(r'Eu (?P<negacao>não )?(?P<verbo>prefiro|gosto de) (?P<alvo>[\w]+(?:[ -][\w]+){0,3})\.', declaracao)
    return bool(m and ('preferir' if m['verbo'] == 'prefiro' else 'gostar') == consulta.get('predicado')
        and bool(m['negacao']) == consulta.get('negada')
        and normalizar_texto_basico(m['alvo']) == consulta.get('alvo'))


def _fundamentos_disponiveis(plano: Mapping[str, Any], mente: Mapping[str, Any],
    declaracoes: tuple[str, ...]) -> tuple[FundamentoCriterioAutoral, ...]:
    """Reaproveita fonte lida, com alvo e TTL próprios; não inicia pesquisa."""
    import math
    import time
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    from mente_laylay.cognicao.pesquisa_multifonte import _frase_afirma_sobre_alvo
    from mente_laylay.cognicao.revisao_suporte_autoria import conferir_apoio_fonte
    base = plano.get('fundamentacao_factual') or mente.get('fundamentacao_factual_anterior') or {}
    if not isinstance(base, dict):
        return ()
    expira_em = base.get('evidencia_expira_em')
    if type(expira_em) not in (int, float) or not math.isfinite(expira_em) or time.time() >= expira_em:
        return ()
    alvos = list(dict.fromkeys(re.sub(r'^Eu (?:prefiro|(?:não )?gosto de) ', '', d).rstrip('.') for d in declaracoes))
    itens = []
    for fonte in (base.get('fontes') or ())[:5]:
        if not isinstance(fonte, dict):
            continue
        alvo = str(fonte.get('alvo') or base.get('tema') or '')
        relacionados = [a for a in alvos if normalizar_texto_basico(a) == normalizar_texto_basico(alvo)]
        trecho, identidade = fonte.get('trecho'), fonte.get('url')
        if (len(relacionados) != 1 or type(trecho) is not str or type(identidade) is not str
            or not _frase_afirma_sobre_alvo(trecho, relacionados[0])):
            continue
        parecer, lida = conferir_apoio_fonte(identidade, trecho, fundamentacao=base)
        if lida is not None and parecer['estado'] == 'literal_integral_na_fonte':
            item = FundamentoCriterioAutoral(lida['snapshot_id'], relacionados[0], identidade, trecho, expira_em)
            if item not in itens:
                itens.append(item)
    return tuple(itens)


def construir_opiniao_autoral(texto: str, *, turno: Mapping[str, Any],
    plano: Mapping[str, Any], contrato: Mapping[str, Any], mente: Mapping[str, Any]) -> OpiniaoAutoral | None:
    from mente_laylay.memoria_mental.registro_semantico import selecionar_fala_observada
    perspectiva = contrato.get('perspectiva_enunciador')
    if (type(perspectiva) is not PerspectivaEnunciador or not perspectiva.vigente(texto, plano.get('id'))
        or str(turno.get('id')) != perspectiva.turno_id
        or turno.get('autoriza_execucao') is not False or plano.get('autoriza_execucao') is not False
        or plano.get('requer_execucao') or plano.get('comandos')
        or turno.get('natureza_entrada') == 'evento' or plano.get('natureza_entrada') == 'evento'
        or 'metalinguagem' in contrato.get('atos', ())
        or {'revisao_alegacao', 'evidencia_fala_historica', 'explicacao_ocorrencia',
            'explicacoes_historicas_por_ato'}.intersection(contrato)):
        return None
    pergunta = consulta_opiniao_propria(texto)
    explicacao = consulta_explicacao_gosto(texto)
    if consulta_relacao_criterio_autoral(texto):
        # O leitor integral confere um ato de relação. Seu "entre X e Y"
        # pode conter fronteiras do segmentador, sem ser dois pedidos.
        fala = selecionar_fala_observada(mente.get('registro_semantico'))
        criterio = criterio_publicado_da_fala(mente.get('registro_semantico'), fala)
        if criterio is None:
            return None
        referencia = ReferenciaFalaConsulta(perspectiva.turno_id,texto,fala['id'],
            fala['turno_id'],fala['fala'],fala['ts'])
        return OpiniaoAutoral(perspectiva.turno_id,texto,'relacao_criterio',
            _categoria_declaracao(criterio.declaracao),(criterio.declaracao,),referencia,criterio)
    if explicacao:
        if len(turno.get('segmentos') or ()) > 1:
            return None
        fala = selecionar_fala_observada(mente.get('registro_semantico'))
        anteriores = _declaracoes_observadas(mente.get('registro_semantico'), fala, para_motivo=True)
        # Um porquê solto continua sob o owner do contexto quando não há
        # opinião integral identificada. Jamais capturar um receipt de ação.
        if not anteriores and explicacao['tipo'] == 'eliptica':
            return None
        referencia = ReferenciaFalaConsulta(perspectiva.turno_id, texto, fala['id'],
            fala['turno_id'], fala['fala'], fala['ts']) if anteriores else None
        criterio = criterio_publicado_da_fala(mente.get('registro_semantico'), fala) if anteriores else None
        return OpiniaoAutoral(perspectiva.turno_id, texto, 'explicacao_gosto',
            _categoria_declaracao(anteriores[0]) if anteriores else '', anteriores, referencia, criterio)
    if pergunta and len(turno.get('segmentos') or ()) > 1:
        return None
    declaracoes: tuple[str, ...] = ()
    categoria = ''
    modo = 'opiniao'
    referencia = None
    criterio = None
    if pergunta:
        categoria, declaracoes = _opcoes_consulta(pergunta)
    else:
        correcao = objeto_retificacao_assunto(texto)
        esclarecimento = 'esclarecimento' in contrato.get('atos', ())
        if not (esclarecimento or correcao):
            return None
        # Seleção canônica de identidade da publicação, não ultima_resposta.
        fala = selecionar_fala_observada(mente.get('registro_semantico'))
        anteriores = _declaracoes_observadas(mente.get('registro_semantico'), fala)
        if not anteriores:
            return None
        categoria = _categoria_declaracao(anteriores[0])
        if correcao:
            if not _correcao_vincula_objeto(correcao, anteriores[0]):
                return None
            modo = 'correcao_assunto'
        else:
            modo = 'esclarecimento'
        referencia = ReferenciaFalaConsulta(perspectiva.turno_id, texto, fala['id'],
            fala['turno_id'], fala['fala'], fala['ts'])
        if not referencia.vigente(texto, perspectiva.turno_id):
            return None
        declaracoes = anteriores
        criterio = criterio_publicado_da_fala(mente.get('registro_semantico'), fala)
    if not declaracoes:
        return None
    # Nova pergunta equivalente conserva a posição recém-publicada. Uma
    # preferência diferente só nasce de outro ato autoral, não de recência.
    if pergunta:
        fala = selecionar_fala_observada(mente.get('registro_semantico'))
        anteriores = _declaracoes_observadas(mente.get('registro_semantico'), fala)
        if len(anteriores) == 1 and anteriores[0] in declaracoes:
            declaracoes = anteriores
    return OpiniaoAutoral(perspectiva.turno_id, texto, modo, categoria, declaracoes, referencia, criterio,
        fundamentos=_fundamentos_disponiveis(plano, mente, declaracoes) if modo == 'opiniao' else ())


def realizacoes_opiniao(texto: str, *, contrato: Mapping[str, Any], turno_id: Any) -> tuple[str, ...]:
    fonte = contrato.get('opiniao_autoral')
    perspectiva = contrato.get('perspectiva_enunciador')
    if (type(fonte) is not OpiniaoAutoral or type(perspectiva) is not PerspectivaEnunciador
        or not perspectiva.vigente(texto, turno_id) or fonte.turno_id != str(turno_id)
        or fonte.texto_usuario != texto or str(contrato.get('turno_id')) != str(turno_id)
        or contrato.get('autoriza_execucao') is not False or fonte.autoriza_execucao or fonte.prova_factual):
        return ()
    if fonte.modo == 'opiniao':
        pergunta = consulta_opiniao_propria(texto)
        categoria, permitidas = _opcoes_consulta(pergunta) if pergunta else ('', ())
        return fonte.declaracoes if (fonte.categoria == categoria and fonte.declaracoes
            and all(d in permitidas for d in fonte.declaracoes)) else ()
    if fonte.modo == 'explicacao_gosto':
        consulta = consulta_explicacao_gosto(texto)
        if consulta is None:
            return ()
        if fonte.referencia is None:
            return (_LIMITE_VINCULO,) if not fonte.declaracoes and consulta['tipo'] == 'explicita' else ()
        if (type(fonte.referencia) is not ReferenciaFalaConsulta
            or not fonte.referencia.vigente(texto, turno_id)
            or fonte.declaracoes != ((fonte.criterio.declaracao,) if type(fonte.criterio) is CriterioAutoralPublicado
                                     else _declaracoes_para_motivo(fonte.referencia.conteudo))
            or len(fonte.declaracoes) != 1):
            return ()
        if not _motivo_vincula_declaracao(consulta, fonte.declaracoes[0]):
            return (_LIMITE_VINCULO,)
        if fonte.criterio is not None:
            criterio = fonte.criterio
            if (type(criterio) is not CriterioAutoralPublicado
                or criterio.declaracao != fonte.declaracoes[0]
                or criterio.portadora_id != fonte.referencia.ocorrencia_id
                or criterio.turno_portador != fonte.referencia.turno_origem
                or criterio.fala_portadora != fonte.referencia.conteudo
                or not criterio_origem_vigente(criterio)
                or criterio.codigo not in CRITERIOS_AUTORAIS or criterio.codigo == 'nao_declarado'):
                return ()
            nome = CRITERIOS_AUTORAIS[criterio.codigo]
            inicio = fonte.declaracoes[0] + f' O critério que registrei para essa escolha foi {nome}. '
            fundamento = criterio.fundamento
            if fundamento_criterio_vigente(fundamento):
                return (inicio + f'Considerei esta descrição: «{fundamento.trecho}» Fonte: {fundamento.fonte_id}. '
                    'Relacionar essa descrição ao critério é uma avaliação declarada, sem comprovar a causa da preferência.',)
            return (inicio + 'Não tenho uma base factual conferida para relacionar esse critério à opção. '
                    'Isso declara minha preferência, sem comprovar características da opção ou uma causa psicológica.',)
        return (fonte.declaracoes[0] + ' ' + _LIMITE_MOTIVO,)
    if (type(fonte.referencia) is not ReferenciaFalaConsulta
        or not fonte.referencia.vigente(texto, turno_id)
        or (fonte.criterio is not None and not criterio_origem_vigente(fonte.criterio))
        or fonte.declaracoes != ((fonte.criterio.declaracao,) if type(fonte.criterio) is CriterioAutoralPublicado
                                 else _declaracoes_da_fala(fonte.referencia.conteudo))):
        return ()
    if fonte.modo == 'esclarecimento':
        if 'esclarecimento' not in contrato.get('atos', ()):
            return ()
        return tuple('Quis dizer que ' + d[:1].lower() + d[1:] for d in fonte.declaracoes)
    if fonte.modo == 'relacao_criterio':
        criterio = fonte.criterio
        if (not consulta_relacao_criterio_autoral(texto) or type(criterio) is not CriterioAutoralPublicado
            or criterio.portadora_id != fonte.referencia.ocorrencia_id
            or criterio.turno_portador != fonte.referencia.turno_origem
            or criterio.fala_portadora != fonte.referencia.conteudo):
            return ()
        nome = CRITERIOS_AUTORAIS[criterio.codigo]
        inicio = fonte.declaracoes[0]+f' Registrei {nome} como critério. '
        fundamento = criterio.fundamento
        descricao = (f'Considerei esta descrição: «{fundamento.trecho}» Fonte: {fundamento.fonte_id}. '
            if fundamento_criterio_vigente(fundamento)
            else 'Não tenho uma descrição factual vigente vinculada a esse critério. ')
        return (inicio+descricao+'Não registrei uma regra que mostre como a descrição atende ao critério. '
            'A fonte não comprova essa relação avaliativa nem a causa da preferência.',)
    if fonte.modo == 'correcao_assunto':
        objeto = objeto_retificacao_assunto(texto)
        if not objeto or not all(_correcao_vincula_objeto(objeto, d) for d in fonte.declaracoes):
            return ()
        tema = 'música' if fonte.categoria == 'genero_musical' else objeto
        return tuple(f'Sim, estou falando de {tema}: ' + d[:1].lower() + d[1:] for d in fonte.declaracoes)
    return ()


def criterio_para_publicacao(plano: Mapping[str, Any], fala: str) -> CriterioAutoralEmissao | CriterioAutoralPublicado | None:
    """Prepara um vínculo; somente o callback de entrega o registra como publicado."""
    import hashlib
    from mente_laylay.cognicao.suporte_autoria import SuporteAutoriaProposto, AutoriaRevisadaProposta
    texto = str(plano.get('texto_usuario') or '')
    leitura = avaliar_opiniao_autoral(texto, fala, plano=plano)
    revisao = plano.get('ultima_verificacao') or {}
    fonte = (plano.get('contrato_fala') or {}).get('opiniao_autoral')
    if (leitura is None or leitura['aceita'] is not True
        or revisao.get('aceita') is not True or revisao.get('fala') != fala):
        return None
    if fonte.modo != 'opiniao':
        # Uma resposta aceita pode recusar a premissa da consulta. Ela possui
        # sua própria publicação, sem carregar o critério de outra declaração.
        return (fonte.criterio if fonte.criterio is not None
            and fonte.criterio.declaracao.casefold() in fala.casefold() else None)
    suporte = plano.get('suporte_autoria_proposto')
    revisada = plano.get('autoria_revisada_proposta')
    if type(revisada) is AutoriaRevisadaProposta:
        if len(revisada.partes) != 1:
            return None
        suporte = revisada.suporte_composto()
    if (type(suporte) is not SuporteAutoriaProposto or suporte.turno_id != str(plano.get('id'))
        or suporte.texto_usuario != texto or suporte.fala_original != fala):
        return None
    proposta = suporte.declaracao.como_dict()
    codigo = proposta.get('criterio_autoral_proposto')
    if (proposta.get('estado') != 'revisao_semantica_pendente' or proposta.get('cobertura_textual') is not True
        or codigo not in CRITERIOS_AUTORAIS or codigo == 'nao_declarado'):
        return None
    referencia = proposta.get('fundamento_criterio_proposto')
    fundamento = None
    if referencia not in (None, 'sem_fundamento'):
        candidatos = [f for f in fonte.fundamentos if type(f) is FundamentoCriterioAutoral
            and f.snapshot_id == referencia and fundamento_criterio_vigente(f)
            and _alvo_fundamento_corresponde(f, fala)]
        if len(candidatos) != 1:
            return None
        fundamento = candidatos[0]
    return CriterioAutoralEmissao(str(plano['id']), texto, fala, codigo,
        hashlib.sha256(json_para_identidade(suporte).encode('utf8')).hexdigest(), fundamento)


def _alvo_fundamento_corresponde(fundamento: FundamentoCriterioAutoral, fala: str) -> bool:
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    valor = re.sub(r'^Eu (?:prefiro|(?:não )?gosto de) ', '', fala).rstrip('.')
    return normalizar_texto_basico(valor) == normalizar_texto_basico(fundamento.alvo)


def json_para_identidade(suporte: Any) -> str:
    import json
    return json.dumps({'turno_id': suporte.turno_id, 'texto_usuario': suporte.texto_usuario,
        'fala': suporte.fala_original, 'declaracao': suporte.declaracao.como_dict()},
        ensure_ascii=False, sort_keys=True, allow_nan=False)


def avaliar_opiniao_autoral(texto: str, fala: str, *, plano: Mapping[str, Any]) -> dict[str, Any] | None:
    contrato = plano.get('contrato_fala') or {}
    if 'opiniao_autoral' not in contrato:
        return None
    opcoes = realizacoes_opiniao(texto, contrato=contrato, turno_id=plano.get('id'))
    aceita = bool(opcoes and fala in opcoes and not plano.get('requer_execucao')
        and not plano.get('comandos') and plano.get('autoriza_execucao') is False)
    problemas = [] if aceita else ['opiniao_autoral_extrapolada']
    return {'aceita': aceita, 'requer_reparo': not aceita, 'problemas': problemas,
        'problemas_bloqueantes': problemas, 'somente_consultiva': False,
        'foco': {}, 'ultima_resposta': '',
        'contrato_reparo': {'opiniao_autoral': True, 'autoriza_execucao': False},
        'aderencia_contrato': {'avaliado': True, 'aceita': aceita,
            'prova_semantica_livre': False, 'prova_factual': False, 'autoriza_execucao': False},
        'autoriza_execucao': False}


def montar_pacote_opiniao(texto: str, *, contrato: Mapping[str, Any], turno_id: Any) -> PacotePrompt | None:
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    opcoes = realizacoes_opiniao(texto, contrato=contrato, turno_id=turno_id)
    if not opcoes:
        return None

    opinativa = contrato['opiniao_autoral'].modo == 'opiniao'
    fundamentos = tuple(f for f in contrato['opiniao_autoral'].fundamentos if fundamento_criterio_vigente(f)) if opinativa else ()
    def validar(dados: dict[str, Any]) -> None:
        campos = {'fala', 'comandos', 'criterio_autoral'} if opinativa else {'fala', 'comandos'}
        if fundamentos:
            campos.add('fundamento_criterio')
        if set(dados) != campos or dados.get('fala') not in opcoes or dados.get('comandos') != []:
            raise ValueError('opiniao_autoral_extrapolada')
        if opinativa:
            validar_codigo_criterio(dados['criterio_autoral'])
        if fundamentos:
            referencia = dados['fundamento_criterio']
            if referencia != 'sem_fundamento' and (dados['criterio_autoral'] == 'nao_declarado'
                or not any(f.snapshot_id == referencia and _alvo_fundamento_corresponde(f, dados['fala']) for f in fundamentos)):
                raise ValueError('fundamento_nao_vinculado_a_escolha')

    esquema = {
        'type': 'object', 'additionalProperties': False, 'required': ['fala', 'comandos'],
        'properties': {'fala': {'type': 'string', 'enum': list(opcoes)},
            'comandos': {'type': 'array', 'maxItems': 0, 'items': {'type': 'object'}}}}
    if opinativa:
        esquema['required'].append('criterio_autoral')
        esquema['properties']['criterio_autoral'] = {'type': 'string', 'enum': list(CRITERIOS_AUTORAIS)}
    if fundamentos:
        esquema['required'].append('fundamento_criterio')
        esquema['properties']['fundamento_criterio'] = {'type':'string',
            'enum':['sem_fundamento', *(f.snapshot_id for f in fundamentos)]}
    codec = ContratoSaidaEstruturada('opiniao_autoral_v1', '[OPINIAO_AUTORAL]', esquema, validar)
    return PacotePrompt(({'role': 'system', 'content':
        'Você é Laylay. Responda diretamente à pergunta de gosto, sem avisos técnicos de citações. '
        'Escolha uma posição subjetiva concreta dentre as realizações permitidas. '
        'Não infira seu gosto pelo gosto do usuário. Uma escolha de autoria não é prova de '
        'sentimento, experiência, causa, capacidade, fato externo ou ação. Nos esclarecimentos '
        'e correções preserve a declaração publicada. Não acrescente explicações inventadas. '
        + ('Nesta escolha declare também criterio_autoral: curiosidade, afinidade_estetica, clareza '
           'ou simplicidade são critérios avaliativos que você pode adotar agora; nao_declarado '
           'significa que não adotou nenhum. Não são propriedades comprovadas da opção, '
           'experiências ou causas psicológicas. O registro só se conclui após a publicação.' if opinativa else '')
        + _formatar_fundamentos(fundamentos)},
        {'role': 'user', 'content': texto}), contexto_fechado=True, contrato_saida=codec)


def _formatar_fundamentos(fundamentos: tuple[FundamentoCriterioAutoral, ...]) -> str:
    import json
    if not fundamentos:
        return ''
    return ('\nDESCRIÇÕES INDIVIDUAIS CONFERIDAS: ' + json.dumps([
        {'id':f.snapshot_id, 'alvo':f.alvo, 'trecho':f.trecho, 'fonte':f.fonte_id} for f in fundamentos], ensure_ascii=False)
        + '\nSe considerar uma descrição como base da sua avaliação, declare seu id em fundamento_criterio. '
        'Escolha somente base cujo alvo corresponde à opção que escolheu. Caso contrário use sem_fundamento. '
        'A fonte sustenta somente a citação; sua relação com o critério é avaliação assumida, não uma prova. '
        'Não acrescente características à fala nem declare causa psicológica, experiência ou autorização.')
