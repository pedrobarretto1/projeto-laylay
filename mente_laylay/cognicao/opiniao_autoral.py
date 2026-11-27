"""Autoria subjetiva limitada: posição não comprova causa, experiência ou capacidade.

O vocabulário de tipos vem da memória existente. A escolha pertence à autora;
o host confere forma, pergunta e continuidade da publicação, nunca sentimento.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
import re
from typing import Any, Mapping, TYPE_CHECKING

from mente_laylay.cognicao.referencias_linguagem import (
    PerspectivaEnunciador, consulta_opiniao_propria, objeto_retificacao_assunto,
    consulta_explicacao_gosto,
    consulta_relacao_criterio_autoral,
    enunciados_discursivos,
    intervalos_citados,
    operando_opiniao_literal,
    pedido_sentido_fala_propria,
    CATEGORIAS_PREFERENCIA,
)
from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta
from mente_laylay.cognicao.criterio_autoral import (
    CriterioAutoralEmissao, CriterioAutoralPublicado, CRITERIOS_AUTORAIS,
    criterio_publicado_da_fala, validar_codigo_criterio, criterio_origem_vigente,
    FundamentoCriterioAutoral, fundamento_criterio_vigente,
    MOTIVOS_NA_POSICAO_AUTORAL, RECONHECIMENTO_ESCOPO_OPINIAO, nucleo_declaracao_autoral,
    separar_motivo_na_posicao,
)
from mente_laylay.cognicao.normalizacao_linguagem import (
    SAUDACOES_CONVERSACIONAIS, normalizar_texto_basico, normalizar_texto_curto,
    separar_saudacao_inicial,
)
from mente_laylay.personalidade.perfil_amizade import IDENTIDADE_VOZ_LAYLAY, orientar_registro_amizade

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
    generos_recusados: tuple[ReferenciaFalaConsulta, ...] = ()


_LIMITE_MOTIVO = 'Essa fala não trouxe um motivo para a preferência.'
_MOTIVO_PENDENTE = 'Ainda não tenho um motivo claro pra te dar.'
_LIMITE_CERTEZA = 'Falei com mais certeza do que devia. Ainda não tenho uma opinião tão formada sobre isso.'
_CONFIRMA_PERGUNTA_MOTIVO = 'Você quis perguntar por quê?'
_SEM_RAZAO_NEGATIVA = 'Ainda não tenho uma razão clara pra te dar.'
_SEM_RAZAO_CONCRETA = 'Sem uma razão concreta, eu devia ter deixado isso em aberto.'
_RETOMA_POSICAO = 'Eu disse que '
_POSICAO_EM_ABERTO = 'Ainda tô formando uma opinião sobre '
_MOTIVO_POSICAO_EM_ABERTO = 'Deixei em aberto. Ainda não tenho uma razão pra dizer que gosto ou que não gosto.'
_LIMITE_VINCULO = 'Não tenho uma declaração de gosto correspondente a essa pergunta para explicar o motivo.'
_CRITERIO_EM_CONVERSA = {
    'curiosidade': ('Foi por curiosidade mesmo.', 'Eu estava falando da minha curiosidade pela ideia.'),
    'afinidade_estetica': ('Foi mais pelo estilo mesmo.', 'Eu estava falando de gosto pelo estilo em geral.'),
    'clareza': ('Pesei a clareza nessa escolha.', 'Clareza foi o que eu levei em conta nessa escolha.'),
    'simplicidade': ('Me guiei pela simplicidade nessa escolha.', 'Simplicidade foi o que pesou pra mim nessa escolha.'),
}


def _categoria_ampla(alvo: str) -> tuple[str, str] | None:
    normal = normalizar_texto_basico(alvo)
    for categoria, (singular, plural, _) in CATEGORIAS_PREFERENCIA.items():
        for forma in (singular, plural):
            if normal == normalizar_texto_basico(forma):
                return 'geral:' + categoria, forma
    return None


def _consulta_categoria_ampla(texto: str) -> dict[str, Any] | None:
    leitura = consulta_opiniao_propria(texto)
    if leitura is None or leitura['tipo'] != 'polar':
        return None
    return leitura if _categoria_ampla(str(leitura['alvo'])) else None


def _consulta_dialogada(texto: str, *, anterior: str = '') -> tuple[dict[str, Any] | None, str]:
    """Compõe atos sociais fechados sem absorver outro pedido ou citação."""
    if intervalos_citados(texto):
        return None, ''
    saudacao, corpo = separar_saudacao_inicial(texto)
    if saudacao and corpo:
        # A moldura tem poucas palavras. O núcleo literal mantém os acentos
        # e nomes que a leitura lexical da saudação normaliza.
        for inicio in islice(re.finditer(r'\b\w', texto), 6):
            nucleo = texto[inicio.start():]
            if normalizar_texto_curto(nucleo) == corpo:
                consulta = consulta_opiniao_propria(nucleo)
                return (consulta, SAUDACOES_CONVERSACIONAIS[saudacao]) if consulta else (None, '')
        return None, ''

    atos = enunciados_discursivos(texto)
    if not atos or len(atos) > 2:
        return None, ''
    termo = None
    if len(atos) == 2:
        primeiro = normalizar_texto_basico(atos[0])
        aclaracao = re.fullmatch(r'como assim(?: (?:com|de|do|da|por|pelo|pela|sobre) '
                                 r'(?P<termo>\w+(?: \w+){0,3}))?\?', primeiro)
        termo = aclaracao['termo'] if aclaracao else None
        if not pedido_sentido_fala_propria(atos[0]) and not aclaracao:
            return None, ''
    ultimo = normalizar_texto_basico(atos[-1])
    matriz = re.match(r'^(?:eu )?(?:(?:to|estou)(?: so| apenas)? perguntando|(?:quis|quero) saber) se ', ultimo)
    if len(atos) > 1 and not matriz:
        return None, ''
    nucleo = ultimo[matriz.end():] if matriz else ultimo
    escopo = re.fullmatch(r'(?P<consulta>.+?)(?:,? (?:no|em) geral|,? de forma geral)'
        r'(?:\s*,?\s+(?:e |mas )?nao (?:de )?(?:um[a]? )?(?P<restrito>\w+(?: \w+){0,2}) '
        r'(?:especific[oa]|em particular))?[.!?]*', nucleo)
    if escopo is None:
        return None, ''
    consulta = _consulta_categoria_ampla(escopo['consulta'])
    restrito = escopo['restrito']
    if restrito and restrito not in {'estilo', 'genero', 'tipo', 'titulo', 'exemplo'} and not _categoria_ampla(restrito):
        return None, ''
    if termo and termo != restrito and not re.search(rf'\b{re.escape(termo)}\b', normalizar_texto_basico(anterior)):
        return None, ''
    return consulta, RECONHECIMENTO_ESCOPO_OPINIAO if consulta and matriz else ''


def _consulta_opiniao_turno(texto: str, *, anterior: str = '') -> tuple[dict[str, Any] | None, str]:
    consulta, moldura = _consulta_dialogada(texto, anterior=anterior)
    return consulta or consulta_opiniao_propria(texto), moldura


def _criterios_cabiveis(categoria: str) -> tuple[str, ...]:
    return ('curiosidade', 'nao_declarado') if categoria.startswith('geral:') else tuple(CRITERIOS_AUTORAIS)


def _motivos_da_posicao(declaracao: str, *, categoria: str, tipo: str) -> tuple[str, ...]:
    # Curiosidade ou afinidade abstrata não fundamentam rejeição. Títulos,
    # reconsiderações e respostas que já expressam limite seguem seus owners.
    if not _forma_canonica_declaracao(declaracao).startswith(('Eu gosto de ', 'Eu prefiro ')):
        return ()
    grupo = ('categoria_geral' if categoria.startswith('geral:') else
             'genero_musical' if categoria == 'genero_musical' else
             'escolha' if tipo == 'escolha' else '')
    return tuple(f'{declaracao} {motivo}' for _, motivo in MOTIVOS_NA_POSICAO_AUTORAL.get(grupo, ()))


def _genero_em_grupo_nominal(valor: str) -> bool:
    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia
    from mente_laylay.memoria_mental.memoria_pessoas import classificar_gosto_explicito

    if not operando_opiniao_literal(valor):
        return False
    if classificar_gosto_explicito(valor)[0] == 'genero_musical':
        return True
    palavras = valor.split()
    for i in range(len(palavras) - 1, 0, -1):
        if classificar_gosto_explicito(' '.join(palavras[:i]))[0] == 'genero_musical':
            return all((consultar_morfologia(p) or 0) & 2 for p in palavras[i:])
    return False


def _consulta_de_gosto_com_contexto(texto: str) -> dict[str, object] | None:
    """Uma consulta final pode retomar um único gênero nomeado no enunciado anterior."""
    if intervalos_citados(texto):
        return None
    atos = enunciados_discursivos(texto)
    if len(atos) < 2 or not atos[-1].endswith('?') or any(not a.endswith(('.', '!')) for a in atos[:-1]):
        return None
    direta = consulta_opiniao_propria(atos[-1])
    if direta:
        return direta
    pergunta = re.fullmatch(r'(?:e )?(?:voc[eê]|vc|tu|laylay|lay)\s+(?P<negacao>n[aã]o\s+)?'
        r'(?:gosta|curte|aprecia)\s+(?:(?:de\s+)?(?:esse|este)|desse|deste)\s+'
        r'(?:tipo de m[uú]sica|estilo(?: musical)?|g[eê]nero(?: musical)?)\?', atos[-1], re.I)
    if pergunta is None:
        return None
    premissa = re.fullmatch(
        r'(?:(?:(?:eu\s+)?acho que\s+)?(?:hoje|agora)\s+'
        r'(?:combina com|pede|vai bem com|cai bem com)|'
        r'(?:eu\s+)?(?:estou|t[oô]|estava|tava)\s+(?:ouvindo|escutando|falando de))'
        r'\s+(?:um[a]?\s+)?(?P<alvo>[\w -]+)[.!]', atos[-2], re.I)
    if premissa is None:
        return None
    alvo = premissa['alvo'].strip().casefold()
    if not _genero_em_grupo_nominal(alvo):
        return None
    return {'tipo': 'polar', 'alvo': alvo, 'predicado': 'gostar', 'negada': bool(pergunta['negacao'])}


def _sem_favorito(categoria: str) -> str:
    nome, _, genero = CATEGORIAS_PREFERENCIA[categoria]
    feminino = genero == 'a'
    return f"Ainda não escolhi um{'a' if feminino else ''} {nome} favorit{'a' if feminino else 'o'}."


def _sem_exemplar(categoria: str) -> tuple[str, ...]:
    nome, _, genero = CATEGORIAS_PREFERENCIA[categoria]
    artigo = 'uma' if genero == 'a' else 'um'
    return (f'Ainda não tenho {artigo} {nome} que eu diria que é a minha cara.',
            f'Não escolhi {artigo} {nome} pra chamar de favorito. Quer uma sugestão pelo clima?')


def _categoria_autoria_obra(texto: str) -> str:
    if intervalos_citados(texto):
        return ''
    base = normalizar_texto_basico(texto)
    leitura = re.fullmatch(r'(?:e )?quem (?:fez|criou|escreveu|compos|canta|cantou) '
                          r'(?:ess[ea]|est[ea]|aquel[ea]) (?P<obra>\w+)\?', base)
    return leitura['obra'] if leitura and leitura['obra'] in CATEGORIAS_PREFERENCIA else ''


def _forma_canonica_declaracao(fala: str) -> str:
    fala = nucleo_declaracao_autoral(fala)
    if fala.startswith('Curto ') and fala.endswith(', sim.'):
        return 'Eu gosto de ' + fala.removeprefix('Curto ').removesuffix(', sim.') + '.'
    if fala.startswith('Não curto '):
        return 'Eu não gosto de ' + fala.removeprefix('Não curto ')
    return fala


def _declaracoes_da_fala(fala: str) -> tuple[str, ...]:
    """Só o ato integral coberto; uma oração causal não é absorvida."""
    base = nucleo_declaracao_autoral(str(fala))
    for limite in (_LIMITE_MOTIVO, _MOTIVO_PENDENTE, _CONFIRMA_PERGUNTA_MOTIVO, _MOTIVO_POSICAO_EM_ABERTO,
                   _SEM_RAZAO_NEGATIVA, _SEM_RAZAO_CONCRETA):
        if base.endswith(' ' + limite):
            base = base.removesuffix(' ' + limite)
            break
    for abertura in ('Quis dizer que ', _RETOMA_POSICAO):
        if base.startswith(abertura):
            base = base.removeprefix(abertura)
            break
    correcao = re.fullmatch(r'Sim, estou falando de (?P<objeto>[\w]+(?:[ -][\w]+){0,5}): (?P<declaracao>.+)', base)
    if correcao:
        declaracao = correcao['declaracao'][:1].upper() + correcao['declaracao'][1:]
        if not _correcao_vincula_objeto(correcao['objeto'], declaracao):
            return ()
        base = declaracao
    base = base[:1].upper() + base[1:]
    declaracao = re.fullmatch(r'Eu (?:prefiro|(?:não )?gosto de) (?P<valor>[\w]+(?:[ -][\w]+){0,3})\.',
        _forma_canonica_declaracao(base))
    if declaracao and operando_opiniao_literal(declaracao['valor']):
        return (base,)
    if base.startswith(_POSICAO_EM_ABERTO) and base.endswith('.') and operando_opiniao_literal(
        base.removeprefix(_POSICAO_EM_ABERTO).removesuffix('.')
    ):
        return (base,)
    if base == 'Não tenho um estilo musical preferido.':
        return (base,)
    if base in tuple(_sem_favorito(c) for c in CATEGORIAS_PREFERENCIA):
        return (base,)
    return ()


def _categoria_declaracao(declaracao: str) -> str:
    if declaracao == 'Não tenho um estilo musical preferido.':
        return 'genero_musical'
    for categoria in CATEGORIAS_PREFERENCIA:
        if declaracao == _sem_favorito(categoria):
            return 'favorito:' + categoria
    valor = _alvo_declarado(declaracao)
    if categoria := _categoria_ampla(valor):
        return categoria[0]
    return 'genero_musical' if _genero_em_grupo_nominal(valor) else ''


def _alvo_declarado(declaracao: str) -> str:
    forma = _forma_canonica_declaracao(declaracao).removeprefix(_POSICAO_EM_ABERTO)
    return re.sub(r'^Eu (?:prefiro|(?:não )?gosto de) ', '', forma).rstrip('.')


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
    valor = _alvo_declarado(declaracao)
    return declaracoes if _categoria_declaracao(declaracao) or ' ' not in valor else ()


def _declaracoes_observadas(registro: Mapping[str, Any] | None, fala: Mapping[str, Any], *,
    para_motivo: bool = False) -> tuple[str, ...]:
    criterio = criterio_publicado_da_fala(registro, fala)
    if criterio is not None:
        return (nucleo_declaracao_autoral(criterio.declaracao),)
    return (_declaracoes_para_motivo if para_motivo else _declaracoes_da_fala)(str(fala.get('fala') or ''))


def _opcoes_consulta(pergunta: Mapping[str, Any]) -> tuple[str, tuple[str, ...]]:
    from mente_laylay.memoria_mental.memoria_pessoas import generos_musicais_conhecidos
    if pergunta['tipo'] == 'categoria':
        return 'genero_musical', tuple(f'Eu prefiro {g}.' for g in generos_musicais_conhecidos()) + (
            'Não tenho um estilo musical preferido.',)
    if pergunta['tipo'] == 'favorito':
        # Autoria não qualifica a existência/categoria de um título proposto.
        # Sem inventário de alvos fundamentados, não criar um favorito factual
        # nem iniciar pesquisa obrigatória para sustentar uma conversa casual.
        categoria = str(pergunta['categoria'])
        return 'favorito:' + categoria, (_sem_favorito(categoria),)
    if pergunta['tipo'] == 'exemplar':
        categoria = str(pergunta['categoria'])
        return 'exemplar:' + categoria, _sem_exemplar(categoria)
    if pergunta['tipo'] == 'polar':
        alvo = str(pergunta['alvo'])
        ampla = _categoria_ampla(alvo)
        categoria, alvo = ampla or ('genero_musical' if _genero_em_grupo_nominal(alvo) else '', alvo)
        if not categoria and ' ' in alvo:
            return '', ()
        return categoria, (f'Eu gosto de {alvo}.', f'Eu não gosto de {alvo}.',
                           f'Curto {alvo}, sim.', f'Não curto {alvo}.', _POSICAO_EM_ABERTO + alvo + '.')
    if pergunta['tipo'] == 'escolha':
        return '', tuple(f'Eu prefiro {a}.' for a in pergunta['alternativas'])
    return '', ()


def _correcao_vincula_objeto(correcao: str, declaracao: str) -> bool:
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    objeto = _alvo_declarado(declaracao)
    return (normalizar_texto_basico(correcao) == normalizar_texto_basico(objeto)
        or (_categoria_declaracao(declaracao) == 'genero_musical'
            and normalizar_texto_basico(correcao) in {'musica', 'musicas', 'genero musical', 'estilo musical'}))


def _motivo_vincula_declaracao(consulta: Mapping[str, Any], declaracao: str) -> bool:
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    if declaracao.startswith(_POSICAO_EM_ABERTO):
        return (not consulta.get('categoria') or consulta['categoria'] == _categoria_declaracao(declaracao)) and (
            consulta['tipo'] == 'eliptica' or normalizar_texto_basico(_alvo_declarado(declaracao)) == consulta.get('alvo'))
    if consulta['tipo'] == 'eliptica':
        return (not consulta.get('categoria') or consulta['categoria'] == _categoria_declaracao(declaracao)) and (
            not consulta.get('negada') or _forma_canonica_declaracao(declaracao).startswith('Eu não gosto de '))
    m = re.fullmatch(r'Eu (?P<negacao>não )?(?P<verbo>prefiro|gosto de) (?P<alvo>[\w]+(?:[ -][\w]+){0,3})\.',
        _forma_canonica_declaracao(declaracao))
    return bool(m and ('preferir' if m['verbo'] == 'prefiro' else 'gostar') == consulta.get('predicado')
        and bool(m['negacao']) == consulta.get('negada')
        and normalizar_texto_basico(m['alvo']) == consulta.get('alvo'))


def _generos_recusados(registro: Mapping[str, Any] | None, texto: str, turno_id: str) -> tuple[ReferenciaFalaConsulta, ...]:
    from mente_laylay.memoria_mental.registro_semantico import selecionar_fala_observada

    encontrados: dict[str, ReferenciaFalaConsulta | None] = {}
    for item in reversed((registro or {}).get('falas_observadas', ())):
        if not isinstance(item, Mapping) or not item.get('id'):
            continue
        fala = selecionar_fala_observada(registro, ocorrencia_id=item['id'])
        declaracoes = _declaracoes_observadas(registro, fala)
        if len(declaracoes) != 1 or _categoria_declaracao(declaracoes[0]) != 'genero_musical':
            continue
        declaracao = declaracoes[0]
        alvo = normalizar_texto_basico(_alvo_declarado(declaracao))
        if alvo not in encontrados:
            encontrados[alvo] = (ReferenciaFalaConsulta(turno_id, texto, fala['id'], fala['turno_id'],
                fala['fala'], fala['ts']) if _forma_canonica_declaracao(declaracao).startswith('Eu não gosto de ')
                else None)
    return tuple(fonte for fonte in encontrados.values() if fonte is not None)


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
    alvos = list(dict.fromkeys(_alvo_declarado(d) for d in declaracoes))
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
    registro = mente.get('registro_semantico')
    publicada = selecionar_fala_observada(registro)
    anterior = str(publicada.get('fala') or '')
    pergunta, moldura = _consulta_opiniao_turno(texto, anterior=anterior)
    explicacao = consulta_explicacao_gosto(texto)
    categoria_obra = _categoria_autoria_obra(texto)
    if categoria_obra and len(turno.get('segmentos') or ()) <= 1 and anterior in _sem_exemplar(categoria_obra):
        referencia = ReferenciaFalaConsulta(perspectiva.turno_id, texto, publicada['id'],
            publicada['turno_id'], anterior, publicada['ts'])
        return OpiniaoAutoral(perspectiva.turno_id, texto, 'autoria_sem_obra', categoria_obra, (), referencia)
    if consulta_relacao_criterio_autoral(texto):
        # O leitor integral confere um ato de relação. Seu "entre X e Y"
        # pode conter fronteiras do segmentador, sem ser dois pedidos.
        fala = selecionar_fala_observada(mente.get('registro_semantico'))
        criterio = criterio_publicado_da_fala(mente.get('registro_semantico'), fala)
        if criterio is None:
            return None
        referencia = ReferenciaFalaConsulta(perspectiva.turno_id,texto,fala['id'],
            fala['turno_id'],fala['fala'],fala['ts'])
        declaracao = nucleo_declaracao_autoral(criterio.declaracao)
        return OpiniaoAutoral(perspectiva.turno_id,texto,'relacao_criterio',
            _categoria_declaracao(declaracao),(declaracao,),referencia,criterio)
    if explicacao:
        if len(turno.get('segmentos') or ()) > 1:
            return None
        fala = selecionar_fala_observada(mente.get('registro_semantico'))
        anteriores = _declaracoes_observadas(mente.get('registro_semantico'), fala, para_motivo=True)
        # Um porquê solto continua sob o owner do contexto quando não há
        # opinião integral identificada. Jamais capturar um receipt de ação.
        if explicacao['tipo'] == 'eliptica' and not anteriores:
            return None
        if explicacao.get('categoria') and not _motivo_vincula_declaracao(explicacao, anteriores[0]):
            return None
        referencia = ReferenciaFalaConsulta(perspectiva.turno_id, texto, fala['id'],
            fala['turno_id'], fala['fala'], fala['ts']) if anteriores else None
        criterio = criterio_publicado_da_fala(mente.get('registro_semantico'), fala) if anteriores else None
        return OpiniaoAutoral(perspectiva.turno_id, texto, 'explicacao_gosto',
            _categoria_declaracao(anteriores[0]) if anteriores else '', anteriores, referencia, criterio)
    segmentos = turno.get('segmentos') or ()
    if len(segmentos) > 1:
        from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
        from mente_laylay.cognicao.identidade_conversacional import IDENTIDADE_LAYLAY

        fontes = fontes_textuais_dos_segmentos(texto, segmentos)
        conector_isolado = (len(segmentos) == 2 and normalizar_texto_basico(
            segmentos[0].get('texto', '')).rstrip(', ') in {'e', 'entao', 'mas', *IDENTIDADE_LAYLAY['apelidos']})
        if pergunta and (not (moldura or conector_isolado) or not fontes or any(s.get('modalidade') not in {'conversa', 'pergunta'}
            for s in segmentos)):
            return None
        # Uma pergunta factual independente ou solicitação prática não
        # vira premissa do gosto. A moldura explícita já foi lida inteira.
        if (pergunta is None and segmentos[-1].get('modalidade') == 'pergunta'
            and all(s.get('modalidade') == 'conversa' for s in segmentos[:-1])
            and fontes):
            pergunta = _consulta_de_gosto_com_contexto(texto)
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
        anteriores = _declaracoes_observadas(registro, publicada)
        if moldura == RECONHECIMENTO_ESCOPO_OPINIAO and anterior:
            referencia = ReferenciaFalaConsulta(perspectiva.turno_id, texto, publicada['id'],
                publicada['turno_id'], anterior, publicada['ts'])
        if len(anteriores) == 1:
            if anteriores[0] in declaracoes and moldura != RECONHECIMENTO_ESCOPO_OPINIAO:
                declaracoes = anteriores
            else:
                anterior = normalizar_texto_basico(_forma_canonica_declaracao(anteriores[0]))
                equivalentes = tuple(d for d in declaracoes
                    if normalizar_texto_basico(_forma_canonica_declaracao(d)) == anterior)
                if equivalentes:
                    declaracoes = equivalentes
    return OpiniaoAutoral(perspectiva.turno_id, texto, modo, categoria, declaracoes, referencia, criterio,
        fundamentos=_fundamentos_disponiveis(plano, mente, declaracoes) if modo == 'opiniao' else (),
        generos_recusados=_generos_recusados(registro, texto, perspectiva.turno_id)
            if pergunta and pergunta['tipo'] == 'categoria' else ())


def realizacoes_opiniao(texto: str, *, contrato: Mapping[str, Any], turno_id: Any) -> tuple[str, ...]:
    fonte = contrato.get('opiniao_autoral')
    perspectiva = contrato.get('perspectiva_enunciador')
    if (type(fonte) is not OpiniaoAutoral or type(perspectiva) is not PerspectivaEnunciador
        or not perspectiva.vigente(texto, turno_id) or fonte.turno_id != str(turno_id)
        or fonte.texto_usuario != texto or str(contrato.get('turno_id')) != str(turno_id)
        or contrato.get('autoriza_execucao') is not False or fonte.autoriza_execucao or fonte.prova_factual):
        return ()
    if fonte.modo == 'opiniao':
        anterior = fonte.referencia.conteudo if (type(fonte.referencia) is ReferenciaFalaConsulta
            and fonte.referencia.vigente(texto, turno_id)) else ''
        pergunta, moldura = _consulta_opiniao_turno(texto, anterior=anterior)
        pergunta = pergunta or _consulta_de_gosto_com_contexto(texto)
        categoria, permitidas = _opcoes_consulta(pergunta) if pergunta else ('', ())
        if fonte.categoria != categoria or any(d not in permitidas for d in fonte.declaracoes):
            return ()
        excluidos = set()
        if pergunta and pergunta['tipo'] == 'categoria':
            for referencia in fonte.generos_recusados:
                if type(referencia) is ReferenciaFalaConsulta and referencia.vigente(texto, turno_id):
                    for d in _declaracoes_da_fala(referencia.conteudo):
                        if _forma_canonica_declaracao(d).startswith('Eu não gosto de '):
                            excluidos.add(normalizar_texto_basico(_alvo_declarado(d)))
        declaracoes = tuple(d for d in fonte.declaracoes
                            if normalizar_texto_basico(_alvo_declarado(d)) not in excluidos)
        opcoes = declaracoes
        if pergunta and moldura != RECONHECIMENTO_ESCOPO_OPINIAO:
            opcoes += tuple(opcao for d in declaracoes
                for opcao in _motivos_da_posicao(d, categoria=categoria, tipo=pergunta['tipo']))
        return tuple(moldura + d for d in opcoes)
    if fonte.modo == 'autoria_sem_obra':
        categoria = _categoria_autoria_obra(texto)
        referencia = fonte.referencia
        if (not categoria or categoria != fonte.categoria or type(referencia) is not ReferenciaFalaConsulta
            or not referencia.vigente(texto, turno_id) or referencia.conteudo not in _sem_exemplar(categoria)):
            return ()
        return ('Qual é o nome? Eu ainda não dei nenhum título na resposta anterior.',)
    if fonte.modo == 'explicacao_gosto':
        consulta = consulta_explicacao_gosto(texto)
        if consulta is None:
            return ()
        if fonte.referencia is None:
            return (_LIMITE_VINCULO,) if not fonte.declaracoes and consulta['tipo'] == 'explicita' else ()
        if (type(fonte.referencia) is not ReferenciaFalaConsulta
            or not fonte.referencia.vigente(texto, turno_id)
            or fonte.declaracoes != ((nucleo_declaracao_autoral(fonte.criterio.declaracao),)
                                     if type(fonte.criterio) is CriterioAutoralPublicado
                                     else _declaracoes_para_motivo(fonte.referencia.conteudo))
            or len(fonte.declaracoes) != 1):
            return ()
        if not _motivo_vincula_declaracao(consulta, fonte.declaracoes[0]):
            if consulta['tipo'] == 'eliptica' and consulta.get('negada'):
                return (fonte.declaracoes[0] + ' ' + _CONFIRMA_PERGUNTA_MOTIVO,)
            return (_LIMITE_VINCULO,)
        declaracao = fonte.declaracoes[0]
        if declaracao.startswith(_POSICAO_EM_ABERTO):
            return (declaracao + ' ' + _MOTIVO_POSICAO_EM_ABERTO,)
        contextual_negativa = ((consulta.get('negada') or consulta.get('questiona_motivo'))
            and _forma_canonica_declaracao(declaracao).startswith('Eu não gosto de '))
        if fonte.criterio is not None:
            criterio = fonte.criterio
            if (type(criterio) is not CriterioAutoralPublicado
                or nucleo_declaracao_autoral(criterio.declaracao) != fonte.declaracoes[0]
                or criterio.portadora_id != fonte.referencia.ocorrencia_id
                or criterio.turno_portador != fonte.referencia.turno_origem
                or criterio.fala_portadora != fonte.referencia.conteudo
                or not criterio_origem_vigente(criterio)
                or criterio.codigo not in CRITERIOS_AUTORAIS or criterio.codigo == 'nao_declarado'):
                return ()
            if criterio.codigo not in _criterios_cabiveis(fonte.categoria):
                return (fonte.declaracoes[0] + ' Eu estava falando de gosto em geral. Ainda não te dei um motivo específico.',)
            _, motivo_publicado = separar_motivo_na_posicao(criterio.declaracao)
            if motivo_publicado == 'curiosidade' and not fundamento_criterio_vigente(criterio.fundamento):
                return (declaracao + ' O que pesou foi a curiosidade de explorar essa opção. Ainda não tenho um exemplo específico em mente.',)
            if fonte.categoria.startswith('geral:'):
                if _forma_canonica_declaracao(fonte.declaracoes[0]).startswith('Eu não gosto de '):
                    return (fonte.declaracoes[0] + ' Até tenho curiosidade pelo assunto. Só não tenho um motivo específico pra te dar.',)
                return (fonte.declaracoes[0] + ' Tenho curiosidade de saber o que chama a atenção de cada pessoa nesse assunto.',)
            nome = CRITERIOS_AUTORAIS[criterio.codigo]
            inicio = fonte.declaracoes[0] + f' O critério que registrei para essa escolha foi {nome}. '
            fundamento = criterio.fundamento
            if consulta.get('questiona_certeza') and not fundamento_criterio_vigente(fundamento):
                return (_LIMITE_CERTEZA,)
            if fundamento_criterio_vigente(fundamento):
                return (inicio + f'Considerei esta descrição: «{fundamento.trecho}» Fonte: {fundamento.fonte_id}. '
                    'Relacionar essa descrição ao critério é uma avaliação declarada, sem comprovar a causa da preferência.',)
            if contextual_negativa or (criterio.codigo == 'curiosidade'
                and _forma_canonica_declaracao(declaracao).startswith('Eu não gosto de ')):
                limite = _SEM_RAZAO_CONCRETA if consulta.get('questiona_motivo') else _SEM_RAZAO_NEGATIVA
                return (_RETOMA_POSICAO + declaracao[:1].lower() + declaracao[1:] + ' ' + limite,)
            motivo, _ = _CRITERIO_EM_CONVERSA[criterio.codigo]
            if consulta.get('questiona_motivo'):
                return (f'{fonte.declaracoes[0]} {motivo} É uma impressão geral. Ainda não consigo apontar um detalhe.',)
            return (f'{fonte.declaracoes[0]} {motivo} Não tenho um detalhe específico pra apontar.',)
        if consulta.get('questiona_certeza'):
            return (_LIMITE_CERTEZA,)
        if fonte.categoria.startswith('geral:'):
            return (fonte.declaracoes[0] + ' Falei de gosto em geral. Não tenho um motivo mais específico pra te dar.',)
        if consulta.get('negada') or consulta.get('questiona_motivo'):
            return (fonte.declaracoes[0] + ' ' + _MOTIVO_PENDENTE,)
        return (fonte.declaracoes[0] + ' ' + _LIMITE_MOTIVO,)
    if (type(fonte.referencia) is not ReferenciaFalaConsulta
        or not fonte.referencia.vigente(texto, turno_id)
        or (fonte.criterio is not None and not criterio_origem_vigente(fonte.criterio))
        or fonte.declaracoes != ((nucleo_declaracao_autoral(fonte.criterio.declaracao),)
                                 if type(fonte.criterio) is CriterioAutoralPublicado
                                 else _declaracoes_da_fala(fonte.referencia.conteudo))):
        return ()
    if fonte.modo == 'esclarecimento':
        if 'esclarecimento' not in contrato.get('atos', ()):
            return ()
        criterio = fonte.criterio
        if criterio is not None:
            if (criterio.codigo not in _CRITERIO_EM_CONVERSA
                or criterio.portadora_id != fonte.referencia.ocorrencia_id
                or criterio.turno_portador != fonte.referencia.turno_origem
                or criterio.fala_portadora != fonte.referencia.conteudo):
                return ()
            _, sentido = _CRITERIO_EM_CONVERSA[criterio.codigo]
            if criterio.codigo not in _criterios_cabiveis(fonte.categoria):
                sentido = 'Eu estava falando do assunto em geral.'
            return (f'{sentido} {fonte.declaracoes[0]}',)
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
            and fonte.criterio.codigo in _criterios_cabiveis(fonte.categoria)
            and nucleo_declaracao_autoral(fonte.criterio.declaracao).casefold() in fala.casefold() else None)
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
    _, motivo_na_fala = separar_motivo_na_posicao(fala)
    if (proposta.get('estado') != 'revisao_semantica_pendente' or proposta.get('cobertura_textual') is not True
        or codigo not in _criterios_cabiveis(fonte.categoria) or codigo == 'nao_declarado'
        or nucleo_declaracao_autoral(fala).startswith(_POSICAO_EM_ABERTO)
        or (motivo_na_fala is not None and motivo_na_fala != codigo)):
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
    valor = _alvo_declarado(fala)
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

    fonte = contrato['opiniao_autoral']
    opinativa = fonte.modo == 'opiniao' and not fonte.categoria.startswith('exemplar:')
    criterios = _criterios_cabiveis(fonte.categoria)
    fundamentos = tuple(f for f in fonte.fundamentos if fundamento_criterio_vigente(f)) if opinativa else ()
    def validar(dados: dict[str, Any]) -> None:
        campos = {'fala', 'comandos', 'criterio_autoral'} if opinativa else {'fala', 'comandos'}
        if fundamentos:
            campos.add('fundamento_criterio')
        if set(dados) != campos or dados.get('fala') not in opcoes or dados.get('comandos') != []:
            raise ValueError('opiniao_autoral_extrapolada')
        if opinativa:
            codigo = validar_codigo_criterio(dados['criterio_autoral'])
            _, motivo_na_fala = separar_motivo_na_posicao(dados['fala'])
            # Só a realização inteira já conferida pode trazer o motivo.
            # A etiqueta auxiliar não substitui nem invalida o que se falou.
            if nucleo_declaracao_autoral(dados['fala']).startswith(_POSICAO_EM_ABERTO):
                codigo = 'nao_declarado'
            elif motivo_na_fala is not None:
                codigo = motivo_na_fala
            if codigo not in criterios:
                raise ValueError('criterio_fora_do_escopo_da_opiniao')
            dados['criterio_autoral'] = codigo
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
        esquema['required'].insert(0, 'criterio_autoral')
        esquema['properties']['criterio_autoral'] = {'type': 'string', 'enum': list(criterios)}
    if fundamentos:
        esquema['required'].append('fundamento_criterio')
        esquema['properties']['fundamento_criterio'] = {'type':'string',
            'enum':['sem_fundamento', *(f.snapshot_id for f in fundamentos)]}
    codec = ContratoSaidaEstruturada('opiniao_autoral_v1', '[OPINIAO_AUTORAL]', esquema, validar)
    return PacotePrompt(({'role': 'system', 'content':
        IDENTIDADE_VOZ_LAYLAY + ' ' + orientar_registro_amizade(permite_metafora=False) + ' '
        'Responda à pergunta de gosto como numa conversa, sem avisos técnicos de citações. '
        'Escolha uma posição subjetiva concreta dentre as realizações permitidas. '
        'Retribua a saudação quando ela fizer parte da conversa. '
        'Quando houver duas maneiras de dizer a mesma coisa, prefira a mais coloquial. '
        'Não infira seu gosto pelo gosto do usuário. Uma escolha de autoria não é prova de '
        'sentimento, experiência, causa, capacidade, fato externo ou ação. Nos esclarecimentos '
        'e correções preserve a declaração publicada. Não acrescente explicações inventadas. '
        + ('Escolha primeiro o criterio_autoral que realmente combina com a posição. '
           'Se houver uma opção com motivo pertinente, prefira essa opção à resposta seca. '
           'Vontade de explorar ou descobrir pede curiosidade; interesse pelo estilo pede afinidade_estetica. '
           'Confira o par: curiosidade não explica rejeitar algo. '
           'Se ainda estiver formando opinião, escolha a opção que deixa a posição em aberto e use nao_declarado. '
           'O critério é avaliativo. Não descreve propriedades comprovadas da opção, '
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
