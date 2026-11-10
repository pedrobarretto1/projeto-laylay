"""Fundamentação e validação factual geral para respostas conversacionais."""

from __future__ import annotations

import json
import hashlib
import math
import re
import time
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, Iterable

from mente_laylay.cognicao.normalizacao_linguagem import PADRAO_COORDENACAO_OPERACIONAL, texto_e_metalinguistico
from mente_laylay.cognicao.referencias_linguagem import (
    contem_moldura_narrativa,
    enunciados_discursivos,
    intervalos_citados,
    texto_fora_de_citacoes,
    trecho_retificacao_do_enunciador,
)
from mente_laylay.cognicao.gramatica_operacional import texto_consulta_estado_recurso
from mente_laylay.cognicao.retomada_criacao import ABERTURA_RETOMADA_CRIACAO, MATRIZ_RETOMADA_CRIACAO
from mente_laylay.cognicao.proveniencia_informacao import (
    classificar_proveniencia_informacao,
    limitar_proveniencia_invalida,
)
from mente_laylay.memoria_mental.memoria_confiavel import (
    extrair_aprendizados_pessoais_explicitos,
)


_TIPOS_OPERACIONAIS = {
    "app", "janela", "site", "iot", "dispositivo", "arquivo", "pasta",
    "playlist", "musica",
}

_ABERTURA_CONSULTA = re.compile(
    r"^(?:quem|qual|quais|quando|onde|como|quanto|o que|por que|porque|"
    r"me (?:fala|diz|conte)|(?:você|voce) (?:viu|soube|sabe))\b",
    re.IGNORECASE,
)
_SINAL_TEMPO_EXPLICITO = re.compile(
    r"\b(?:agora|hoje|neste momento|atualmente|recente(?:mente)?|últim[oa]s?|ultim[oa]s?|"
    r"esta semana|este mês|este mes|este ano|ainda|já saiu|ja saiu)\b",
    re.IGNORECASE,
)
_PEDIDO_NOMEACAO_DO_DIALOGO = re.compile(
    r'(?:(?:qual|que)\s+(?:(?:seria|e)\s+)?(?:um\s+|o\s+)?'
    r'(?:nome|titulo)(?:\s+\w+){0,2}\s+'
    r'(?:(?:voce|tu)\s+(?:daria|escolheria)\s+)?(?:para\s+|a\s+)'
    r'|como\s+(?:voce|tu)\s+chamaria\s+)'
    r'(?:a\s+)?(?:nossa|esta|essa)\s+(?:conversa|historia|resposta|mensagem|frase)'
    r'(?:\s+de\s+(?:hoje|ontem|agora))?[?!.]*'
)
_TEMPO_NO_ANTECEDENTE_HIPOTETICO = re.compile(
    r"se\s+(?:[^\W\d_]+\s+){0,4}(?P<verbo>[^\W\d_]+ss(?:e|es|emos|em))\b"
    r"[^,:;.!?—()]*\s+(?:agora|hoje|neste momento)"
    r"(?:,|\s+—\s*(?P<aposto>[^—.!?;:]+)\s*—\s*,?|\s+\((?P<parentese>[^().!?;:]+)\),)\s*"
    r"(?P<consulta>(?:qual|quais|que|como|quem|onde|quando|quanto|o que)\s+[^,:;.!?]+?)"
    r"(?P<vocativo>,\s*(?:laylay|lay))?\?",
    re.IGNORECASE,
)
_MATRIZ_DE_ELABORACAO = re.compile(
    r"(?:qual|quais|que)\s+seri(?:a|am)\s+(?:o\s+|a\s+)?"
    r"(?:meu|minha|seu|sua|nosso|nossa)\s+"
    r"(?:plano|ideia|estrat[eé]gia|proposta|abordagem|roteiro)\s+para\s+\S.*|"
    r"(?:qual|que)\s+(?:papel|personagem|tema|abordagem|prioridade)\s+"
    r"(?:(?:eu|voc[eê]|n[oó]s)\s+)?escolher(?:ia|ias|[ií]amos|iam)(?:\s+.+)?|"
    r"como\s+(?:(?:eu|voc[eê]|n[oó]s)\s+)?"
    r"(?:(?:organiz|planej|improvis)ar|dividir)(?:ia|ias|[ií]amos|iam)\s+\S.*",
    re.IGNORECASE,
)
_MATRIZ_DE_PROPOSTA = re.compile(
    r"(?:qual|que)\s+seria\s+(?:a\s+)?(?:minha|sua|nossa)\s+(?:ideia|proposta)",
    re.IGNORECASE,
)
_ORDEM_NO_TEXTO_HIPOTETICO = re.compile(
    r"(?:(?:na|nesta|nessa)\s+(?:hist[oó]ria|fic[cç][aã]o)[:,]\s*)?"
    r"(?:(?:(?:e )?voc[eê],\s*)?(?:laylay|lay):\s*)?"
    r"se\s+[\w\s]+?\s+(?P<verbo>[\w-]+sse)\s+"
    r"[oa]\s+(?:primeir[oa]|[uú]ltim[oa])\s+"
    r"(?:(?P<colecao>livro\s+(?:dessa|desta)\s+biblioteca)|"
    r"(?:cap[ií]tulo|p[aá]gina|cena)\s+(?:d[oa]|dess[ea]|dest[ea])\s+"
    r"(?:livro|conto|hist[oó]ria|romance|roteiro|pe[cç]a|poema)),\s*"
    r"(?:qual|que)\s+seria\s+[oa]\s+(?:primeir[oa]|[uú]ltim[oa])\s+"
    r"(?:frase|linha|verso|fala)(?:\s+escrit[oa])?\s+nel[ea]\?",
    re.IGNORECASE,
)
_CONSULTA_PESSOAL_OU_INTERNA = re.compile(
    r"\b(?:como (?:você|voce|tu) (?:está|esta|tá|ta)|como (?:você|voce) se sente|"
    r"qual (?:é|e) meu nome|o que (?:você|voce) lembra de mim|"
    r"como (?:eu|meu|minha) (?:estou|sou|está|esta))\b",
    re.IGNORECASE,
)
_CONSULTA_MATEMATICA = re.compile(
    r"(?:\bquanto\s+(?:é|e|dá|da)\b.*\d|\d\s*(?:\+|-|x|×|\*|/|÷)\s*\d)",
    re.IGNORECASE,
)
_RETOMADA_ENUNCIACAO = re.compile(
    r"^\W*(?:voc[eê]|tu)\s+(?:disse|falou|perguntou|respondeu|afirmou|explicou)\b",
    re.IGNORECASE,
)
_CONSULTA_ESTADO_OBSERVAVEL = re.compile(
    r"\b(?:(?:ainda\s+)?(?:esta|ta)|continua|segue|permanece)\s+"
    r"(?:abert[oa]s?|fechad[oa]s?|ativ[oa]s?|rodando|em\s+execucao)\b",
    re.IGNORECASE,
)
_AFIRMACAO_ATUAL_MUTAVEL = re.compile(
    r"\b(?:n[aã]o vai ter|vai ter|vai sair|vai lan[cç]ar|nova gera[cç][aã]o|"
    r"exclusiv[oa]|compat[ií]vel|suporte oficial)\b",
    re.IGNORECASE,
)
_ANCORA_HISTORICA = re.compile(
    r"\b(?:em|no ano de|na década de|na decada de)\s+(?:18|19|20)\d{2}\b|"
    r"\b(?:quando nasceu|quando morreu|quem inventou|história de|historia de)\b",
    re.IGNORECASE,
)

_DOMINIOS_ATUALIDADE = (
    (
        "tempo_real",
        900.0,
        re.compile(
            r"\b(?:clima|tempo agora|temperatura|previsão do tempo|previsao do tempo|"
            r"cotação|cotacao|câmbio|cambio|placar|resultado do jogo|trânsito|transito)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "acontecimento_recente",
        3600.0,
        re.compile(
            r"\b(?:notícia|noticia|novidade|aconteceu|acontecendo|eleição|eleicao|"
            r"foi anunciado|acabou de|últimas notícias|ultimas noticias)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "agenda_ou_disponibilidade",
        21600.0,
        re.compile(
            r"\b(?:quando (?:sai|lança|lanca|começa|comeca)|data de lançamento|data de lancamento|"
            r"vai sair|vai lançar|vai lancar|estreia|agenda|horário do jogo|horario do jogo|"
            r"disponível|disponivel|em estoque|preço|preco|quanto custa)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "estado_mutavel",
        86400.0,
        re.compile(
            r"\b(?:versão|versao|atualização|atualizacao|presidente|governador|prefeito|"
            r"ceo|diretor executivo|lei vigente|regra atual|requisito|especificação atual|"
            r"especificacao atual|compatível|compativel|suporte oficial)\b",
            re.IGNORECASE,
        ),
    ),
)


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9\s.-]", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def _tempo_qualifica_antecedente(texto: str, *, consulta_unica: bool) -> bool:
    leitura = _TEMPO_NO_ANTECEDENTE_HIPOTETICO.fullmatch(texto)
    if not leitura:
        return False
    consulta = leitura["consulta"]
    aposto = leitura["aposto"] or leitura["parentese"]
    proposta = _MATRIZ_DE_PROPOSTA.fullmatch(consulta)
    if aposto or leitura["vocativo"] or proposta:
        # A proposta do interlocutor precisa ocupar a matriz inteira e ser
        # a única consulta. O aposto não estende a dispensa a outros atos.
        if not consulta_unica or not proposta:
            return False
        from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel
        if aposto and not all(grupo_nominal_de_papel(item.strip()) for item in
                re.split(r"\s*,\s*|\s+(?:e|ou)\s+", aposto, flags=re.IGNORECASE)):
            return False
    elif (not _MATRIZ_DE_ELABORACAO.fullmatch(consulta) or _SINAL_TEMPO_EXPLICITO.search(consulta) or re.search(
            rf"\b(?:{PADRAO_COORDENACAO_OPERACIONAL}|mas|ou|nem|por[eé]m)\b",
            consulta, re.IGNORECASE)):
        return False
    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia

    tipo = consultar_morfologia(leitura["verbo"]) or 0
    if not tipo & 32 or tipo & (1 | 256):
        return False
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    # Uma segunda interrogação pode aparecer em ordem declarativa, sem
    # repetir "qual"/"quem". Reutilizar o leitor de atos em vez de dispensá-la.
    matriz = classificar_modalidade_turno(consulta + "?")
    return len(matriz["segmentos"]) == 1 and not matriz["autoriza_execucao"]


def classificar_atualidade_factual(
    texto: str,
    *,
    turno: Dict[str, Any] | None = None,
    _consulta_unica: bool = True,
    _ordem_em_cena: bool = False,
) -> Dict[str, Any]:
    """Classifica consultas cujo valor factual pode mudar com o tempo.

    A decisão combina forma da fala, referência temporal e domínio mutável. Um
    termo isolado não basta: comandos, matemática e perguntas pessoais ficam
    fora mesmo quando contêm palavras como ``agora``.
    """
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    normalizado = _normalizar(bruto)
    leitura = dict(turno or {})
    modalidade = str(
        leitura.get("modalidade_geral") or leitura.get("modalidade") or ""
    ).casefold()
    consulta_externa = texto_fora_de_citacoes(bruto)
    ordem_em_cena = _ordem_em_cena or contem_moldura_narrativa(consulta_externa)
    consulta_unica = _consulta_unica and sum(
        "?" in trecho or bool(_ABERTURA_CONSULTA.search(trecho))
        for trecho in enunciados_discursivos(consulta_externa)
    ) <= 1
    eh_consulta = bool(
        "?" in consulta_externa
        or (modalidade in {"pergunta", "misto"}
            and not intervalos_citados(bruto)
            and not re.search(r'[.!;]\s*$', consulta_externa))
        or _ABERTURA_CONSULTA.search(consulta_externa)
        or texto_consulta_estado_recurso(bruto)
    )
    base = {
        "depende_atualidade": False,
        "classe": "estavel",
        "validade_sugerida_s": 0.0,
        "confianca": 0.0,
        "motivos": [],
    }
    if texto_e_metalinguistico(bruto):
        return {**base, "motivos": ["fala_metalinguistica"]}
    segmentos = leitura.get("segmentos")
    fontes_inconsistentes = False
    if isinstance(segmentos, list) and len(segmentos)>1:
        from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
        fontes = fontes_textuais_dos_segmentos(bruto, segmentos, limite_segmentos=32, limite_trecho=4000)
        if len(fontes)==len(segmentos):
            # Interrogação, tema mutável e tempo pertencem ao mesmo ato.
            # Não somar o presidente de uma história à pergunta de cortesia
            # de outro trecho. Fontes incoerentes mantêm a leitura conservadora.
            avaliacoes = []
            for indice, (fonte, segmento) in enumerate(zip(fontes, segmentos)):
                dados_fonte = fonte.como_dict()
                literal = dados_fonte["texto_original"]
                # Uma confirmação elíptica consulta a proposição imediatamente
                # anterior. Não tratá-las como tema e pergunta independentes.
                from mente_laylay.cognicao.referencias_linguagem import pergunta_confirmatoria_eliptica
                if indice and pergunta_confirmatoria_eliptica(literal):
                    literal = fontes[indice-1].como_dict()["texto_original"] + ', ' + literal
                elif indice:
                    anterior = fontes[indice-1].como_dict()
                    fim_anterior = anterior["intervalo"][1]
                    inicio_atual = dados_fonte["intervalo"][0]
                    if re.fullmatch(r"\s*,\s*", bruto[fim_anterior:inicio_atual]):
                        trecho_contiguo = bruto[anterior["intervalo"][0]:dados_fonte["intervalo"][1]]
                        if _ORDEM_NO_TEXTO_HIPOTETICO.fullmatch(trecho_contiguo):
                            # A vírgula separou a condição da matriz. Só a
                            # construção integral do owner recupera esse elo.
                            literal = trecho_contiguo
                avaliacoes.append(classificar_atualidade_factual(
                    literal, turno={"modalidade": segmento.get("modalidade")}, _consulta_unica=consulta_unica,
                    _ordem_em_cena=ordem_em_cena))
            atuais = [a for a in avaliacoes if a["depende_atualidade"]]
            if atuais:
                return min(atuais, key=lambda a: a["validade_sugerida_s"])
            return {**base, "confianca": 0.85, "motivos": ["atos_sem_consulta_mutavel"]}
        fontes_inconsistentes = True
    if not fontes_inconsistentes:
        from mente_laylay.cognicao.referencias_linguagem import pergunta_confirmatoria_eliptica
        enunciados = enunciados_discursivos(bruto)
        if len(enunciados)>1:
            avaliacoes = []
            for indice, enunciado in enumerate(enunciados):
                if indice and pergunta_confirmatoria_eliptica(enunciado):
                    enunciado = enunciados[indice-1] + ', ' + enunciado
                # A modalidade pertence ao segmento composto, não a cada
                # enunciado. A consulta concreta conserva sua própria forma.
                avaliacoes.append(classificar_atualidade_factual(enunciado, _consulta_unica=consulta_unica,
                    _ordem_em_cena=ordem_em_cena))
            atuais = [a for a in avaliacoes if a['depende_atualidade']]
            return min(atuais,key=lambda a:a['validade_sugerida_s']) if atuais else {
                **base,'confianca':0.85,'motivos':['enunciados_sem_consulta_mutavel']}
    afirmacao_mutavel = bool(_AFIRMACAO_ATUAL_MUTAVEL.search(bruto) or (
        eh_consulta and re.search(r"\b(?:ps\s*[3456]|playstation\s*[3456]|xbox|switch|pc)\b", bruto, re.I)))
    if not normalizado or (not eh_consulta and not afirmacao_mutavel):
        return {**base, "classe": "nao_consulta", "motivos": ["fala_nao_consultiva"]}
    if _CONSULTA_PESSOAL_OU_INTERNA.search(bruto) or _RETOMADA_ENUNCIACAO.search(bruto):
        return {**base, "classe": "contexto_pessoal", "motivos": ["resposta_vem_da_mente_local"]}
    if _CONSULTA_MATEMATICA.search(bruto):
        return {**base, "motivos": ["resultado_deterministico"]}
    if _CONSULTA_ESTADO_OBSERVAVEL.search(normalizado) or texto_consulta_estado_recurso(bruto):
        return {
            "depende_atualidade": True,
            "classe": "estado_observavel",
            "validade_sugerida_s": 30.0,
            "confianca": 0.97,
            "motivos": ["estado_atual_exige_observacao"],
        }

    # Em uma introdução volitiva seguida de pergunta retrospectiva sobre
    # autoria, o marcador inicial situa o ato de perguntar. Outros sinais
    # de tempo e domínios mutáveis continuam sob a classificação normal.
    abertura = ABERTURA_RETOMADA_CRIACAO.match(consulta_externa)
    inicio_tempo = (
        abertura.end("transicao")
        if abertura and MATRIZ_RETOMADA_CRIACAO.fullmatch(consulta_externa, abertura.end())
        else 0
    )
    sinal_temporal = bool(_SINAL_TEMPO_EXPLICITO.search(bruto, inicio_tempo))
    if _ANCORA_HISTORICA.search(bruto) and not sinal_temporal:
        return {**base, "classe": "historica", "motivos": ["ancora_historica_explicita"]}

    for classe, validade, padrao in _DOMINIOS_ATUALIDADE:
        if padrao.search(bruto):
            motivos = [f"dominio:{classe}"]
            if sinal_temporal:
                motivos.append("marcador_temporal_explicito")
            return {
                "depende_atualidade": True,
                "classe": classe,
                "validade_sugerida_s": validade,
                "confianca": 0.96 if sinal_temporal else 0.88,
                "motivos": motivos,
            }

    if afirmacao_mutavel:
        return {
            "depende_atualidade": True,
            "classe": "agenda_ou_disponibilidade",
            "validade_sugerida_s": 21600.0,
            "confianca": 0.9,
            "motivos": ["afirmacao_sobre_plataforma_ou_disponibilidade"],
        }

    if sinal_temporal:
        ordem = _ORDEM_NO_TEXTO_HIPOTETICO.fullmatch(consulta_externa)
        if ordem and (not ordem['colecao'] or ordem_em_cena) and all(
                         m[0].casefold() in {'último', 'última', 'ultimo', 'ultima'}
                         for m in _SINAL_TEMPO_EXPLICITO.finditer(bruto)):
            from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia
            classe_verbo = consultar_morfologia(ordem['verbo']) or 0
            if classe_verbo & 32 and not classe_verbo & (1 | 256):
                return {**base, 'confianca': 0.85, 'motivos': ['ordem_do_texto_hipotetico']}
        if _tempo_qualifica_antecedente(consulta_externa, consulta_unica=consulta_unica):
            # Exigir elaboração positiva, pois uma ida hipotética também
            # pode motivar consulta factual (portão do voo, saldo, preço).
            return {**base, "confianca": 0.85, "motivos": ["tempo_do_antecedente_hipotetico"]}
        from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
        if re.fullmatch(r'(?:se\s+[^,;.!?]+,\s*)?o que\s+(?:viria|vem|passa)\s+(?:(?:a|na|pela)\s+)?'
            r'(?:sua|tua)\s+(?:cabeca|mente)(?:\s+agora)?[?!.]*', normalizar_texto_basico(bruto)):
            return {**base,'classe':'contexto_pessoal','motivos':['elaboracao_da_interlocutora']}
        # Nomear um artefato do próprio diálogo é uma proposta local. O tempo
        # qualifica esse artefato, não uma fonte externa recente. Domínios e
        # afirmações mutáveis acima conservam sua obrigação de evidência.
        convite = re.fullmatch(r'vamos\s+[^:;.!?]+:\s*(?P<consulta>[^:;.!?]+)[?!.]*', bruto, re.I)
        alvo_nomeacao = _normalizar(convite['consulta']) if convite else normalizado
        if _PEDIDO_NOMEACAO_DO_DIALOGO.fullmatch(alvo_nomeacao):
            return {**base, 'classe': 'contexto_pessoal',
                    'motivos': ['nomeacao_de_artefato_do_dialogo']}
        return {
            "depende_atualidade": True,
            "classe": "recente_generica",
            "validade_sugerida_s": 21600.0,
            "confianca": 0.82,
            "motivos": ["marcador_temporal_explicito"],
        }
    return {**base, "confianca": 0.85, "motivos": ["sem_sinal_de_mutabilidade"]}


def avaliar_validade_fundamentacao(
    fundamentacao: Dict[str, Any] | None,
    *,
    agora: float | None = None,
) -> Dict[str, Any]:
    """Invalida evidência temporal vencida sem apagar fatos estáveis."""
    base = dict(fundamentacao or {})
    atualidade = dict(base.get("atualidade") or {})
    if not bool(
        base.get("requer_evidencia_recente")
        or atualidade.get("depende_atualidade")
    ):
        return base

    instante = float(agora if agora is not None else time.time())
    try:
        expira_em = float(base.get("evidencia_expira_em"))
    except (TypeError, ValueError):
        expira_em = 0.0
    validade_conhecida = expira_em > 0.0
    dentro_validade = bool(validade_conhecida and instante < expira_em)
    base["evidencia_dentro_validade"] = dentro_validade
    try:
        obtida_em = float(base.get("evidencia_obtida_em") or instante)
    except (TypeError, ValueError):
        obtida_em = instante
    base["evidencia_idade_s"] = max(0.0, instante - obtida_em)
    base["evidencia_expirada"] = not dentro_validade
    if dentro_validade or not base.get("confiavel"):
        return base

    # Preserva apenas metadados para diagnóstico. O conteúdo vencido não pode
    # continuar no prompt nem servir ao verificador como limite factual.
    base.update({
        "confiavel": False,
        "confianca": 0.0,
        "resumo": "",
        "fonte": "",
        "motivo": (
            "validade_evidencia_desconhecida"
            if not validade_conhecida
            else "evidencia_temporal_expirada"
        ),
    })
    base["proveniencia"] = limitar_proveniencia_invalida(base.get("proveniencia"))
    return base


def _tema_numerado_plausivel(valor: str, *, posicao_no_texto: int = 0) -> bool:
    candidato = str(valor or "").strip()
    achado = re.fullmatch(
        r"(?P<nome>[A-Za-zÀ-ÿ]{2,16})(?P<separador>\s*)(?P<numero>\d{1,3})",
        candidato,
    )
    if not achado:
        return True
    nome = achado.group("nome")
    if nome.casefold() in {"ps", "xbox"}:
        return False
    return bool(
        not achado.group("separador")
        or len(re.findall(r"[A-Z]", nome)) >= 2
        or (nome[:1].isupper() and posicao_no_texto > 0)
    )


def extrair_tema_fundamentacao(
    texto: str,
    *,
    retrato: Dict[str, Any] | None = None,
    registro_semantico: Dict[str, Any] | None = None,
) -> str:
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    alvo, restante = separar_descricao_de_nomeacao(bruto)
    if alvo and retrato and retrato.get('alvo_nomeacao_autoral') == alvo:
        return ""
    if alvo:
        bruto = restante
    from mente_laylay.cognicao.referencias_linguagem import consulta_opiniao_propria
    if consulta_opiniao_propria(bruto) is not None:
        return ""
    # Perguntas sobre a preferência da própria Laylay e instruções de estilo
    # continuam conversacionais. Já uma preferência declarada pelo usuário
    # pode cooperar com memória e pesquisa: a declaração é a evidência pessoal
    # e a pesquisa serve apenas como enriquecimento auxiliar.
    if re.search(
        r"\b(?:voc[eê]|tu)\s+(?:gosta|curte|prefere)\b", bruto,
        flags=re.IGNORECASE,
    ):
        return ""
    referencia_previa = re.search(
        r"\b(?:dele|dela|deles|delas|desse|dessa|disso)\b",
        bruto,
        flags=re.IGNORECASE,
    )
    preferencias_declaradas = extrair_aprendizados_pessoais_explicitos(bruto)
    if preferencias_declaradas and not referencia_previa:
        return str(preferencias_declaradas[0].get("valor") or "").strip()[:160]
    if re.search(
        r"\b(?:explique|explica|responda|fale|diga)\b.*\b(?:como\s+(?:uma\s+)?"
        r"crian[cç]a|de\s+(?:um\s+)?jeito|de\s+forma|simples|resumid[oa]|"
        r"detalhad[oa]|curt[oa])\b",
        bruto, flags=re.IGNORECASE,
    ):
        return ""

    recomendacao = re.search(
        r"\b(?:recomenda|recomende|recomendar|indica|indique|sugere|sugira)\b"
        r"[^?!.]{0,100}\b(?P<categoria>filme|s[eé]rie|livro|jogo)\b"
        r"(?:\s+(?:de|do\s+g[eê]nero)\s+(?P<genero>[a-zA-ZÀ-ÿ -]{2,40}))?",
        bruto,
        flags=re.IGNORECASE,
    )
    if recomendacao:
        categoria = recomendacao.group("categoria").casefold()
        genero = str(recomendacao.group("genero") or "").strip(" ,.!?;:\"'")
        return f"{categoria} de {genero}"[:160] if genero else categoria[:160]
    snapshot = dict(retrato or {})
    referencia = dict(snapshot.get("referencia_resolvida") or {})
    tipo = str(referencia.get("tipo") or "").casefold()
    nome = str(referencia.get("nome") or "").strip()
    if (
        nome
        and tipo not in _TIPOS_OPERACIONAIS
        and _tema_numerado_plausivel(nome)
    ):
        return nome[:160]

    # Títulos sequenciais costumam aparecer como GTA 6, GTA6, FIFA 27 etc.
    # Capturar o primeiro evita que a plataforma citada depois (PS4/PS5) vire
    # o tema principal da pesquisa.
    titulo_numerado = re.search(
        r"\b(?P<nome>(?!PS\s*$|Xbox\s*$)[A-Za-zÀ-ÿ]{2,16})(?P<separador>\s*)(?P<numero>\d{1,3})\b",
        bruto,
    )
    if titulo_numerado:
        nome = titulo_numerado.group("nome")
        separador = titulo_numerado.group("separador")
        # Sem espaço, a combinação costuma ser um identificador real (GTA6,
        # iPhone15). Com espaço, exigimos aparência de sigla/título; assim
        # verbos comuns como "contou 20" não viram assunto pesquisável.
        parece_titulo = _tema_numerado_plausivel(
            f"{nome}{separador}{titulo_numerado.group('numero')}",
            posicao_no_texto=titulo_numerado.start(),
        )
        if parece_titulo:
            tema = f"{nome} {titulo_numerado.group('numero')}".strip()
            return tema[:160]
    padroes = (
        r"^(?:voc[eê]\s+)?(?:j[aá]\s+)?(?:ouviu(?:\s+falar)?|conhece)\s+(?:d[oa]|de\s+)?(.+?)[?!.]*$",
        r"^(?:quem\s+(?:e|é)|o\s+que\s+(?:e|é))\s+(.+?)[?!.]*$",
        r"^(?:o\s+que\s+(?:voce|você)\s+acha|qual\s+(?:a\s+)?sua\s+opini[aã]o)\s+(?:d[oa]|de|sobre)\s+(.+?)[?!.]*$",
        r"^(?:fala|fale|me\s+fala|explique|me\s+explica)\s+(?:de|do|da|sobre)\s+(.+?)[?!.]*$",
        r"^(?:que|qual)\s+(?:outra\s+)?m[uú]sica\s+(?:d[oa]|de)\s+(.+?)(?:\s+voc[eê]\s+(?:gosta|curte))?[?!.]*$",
        r"^(?:voc[eê]\s+)?(?:gosta|curte)\s+(?:d[oa]|de)\s+(.+?)[?!.]*$",
        r"^(?:eu\s+)?(?:ou[cç]o|escuto|curto|gosto\s+d[ea])\s+(?:bastante\s+)?(.+?)[?!.]*$",
    )
    for padrao in padroes:
        achado = re.search(padrao, bruto, flags=re.IGNORECASE)
        if achado:
            tema = achado.group(1).strip(" ,.!?;:\"'")
            if 1 <= len(tema.split()) <= 8:
                return tema[:160]

    registro = dict(registro_semantico or {})
    tema_recomendacao = extrair_tema_recomendacao_contextual(bruto, registro)
    if tema_recomendacao:
        return tema_recomendacao
    entidades = dict(registro.get("entidades") or {})
    ativa = dict(entidades.get(str(registro.get("entidade_ativa_id") or "")) or {})
    nome_ativo = str(ativa.get("nome") or "").strip()
    if re.search(r"\b(?:ele|ela|dele|dela|desse|dessa|isso|esse|essa)\b", bruto, flags=re.IGNORECASE):
        return nome_ativo[:160]
    return ""


def extrair_tema_recomendacao_contextual(
    texto: str,
    registro_semantico: Dict[str, Any] | None,
) -> str:
    """Materializa categoria + preferência sem depender da fala da assistente.

    A fala intermediária pode ser uma pergunta autoral ou uma contingência
    genérica. O referente semântico confirmado continua sendo o dono do tema;
    a pendência textual não precisa adivinhar novamente o domínio.
    """
    registro = dict(registro_semantico or {})
    entidades = dict(registro.get("entidades") or {})
    ativa = dict(entidades.get(str(registro.get("entidade_ativa_id") or "")) or {})
    categoria = str(ativa.get("nome") or "").strip()
    if categoria.casefold() not in {"filme", "serie", "série", "livro", "jogo"}:
        return ""
    fala = re.sub(r"\s+", " ", str(texto or "")).strip()
    preferencia = re.search(
        r"\b(?:quero|prefiro|pode\s+ser)\b[^.!?]{0,50}\bde\s+"
        r"(?P<genero>[a-zA-ZÀ-ÿ -]{2,40})[.!?]*$",
        fala,
        flags=re.IGNORECASE,
    ) or re.fullmatch(
        r"de\s+(?P<genero>[a-zA-ZÀ-ÿ -]{2,40})[.!?]*",
        fala,
        flags=re.IGNORECASE,
    )
    if not preferencia:
        return ""
    genero = str(preferencia.group("genero") or "").strip(" ,.!?;:\"'")
    return f"{categoria} de {genero}"[:160] if genero else ""


def montar_fundamentacao(
    tema: str,
    pesquisa: Dict[str, Any] | None,
    *,
    agora: float | None = None,
    atualidade: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    dados = dict(pesquisa or {})
    instante = float(agora if agora is not None else time.time())
    resumo = re.sub(r"\s+", " ", str(dados.get("resumo") or "")).strip()
    try:
        confianca = float(dados.get("confianca") or 0.0)
    except (TypeError, ValueError):
        confianca = 0.0
    confiavel = bool(dados.get("ok") and resumo and confianca >= 0.60)
    candidatos = [
        re.sub(r"\s+", " ", str(item or "")).strip()[:100]
        for item in list(dados.get("candidatos") or [])[:12]
        if re.sub(r"\s+", " ", str(item or "")).strip()
    ]
    classificacao_atualidade = dict(atualidade or {})
    try:
        obtida_em = float(dados.get("evidencia_obtida_em") or instante)
    except (TypeError, ValueError):
        obtida_em = instante
    try:
        validade_fonte = max(0.0, float(dados.get("evidencia_validade_s") or 1800.0))
    except (TypeError, ValueError):
        validade_fonte = 1800.0
    try:
        validade_atualidade = max(
            0.0, float(classificacao_atualidade.get("validade_sugerida_s") or 0.0)
        )
    except (TypeError, ValueError):
        validade_atualidade = 0.0
    validade_efetiva = (
        min(validade_fonte, validade_atualidade)
        if classificacao_atualidade.get("depende_atualidade") and validade_atualidade
        else validade_fonte
    )
    expira_em = obtida_em + validade_efetiva
    idade_s = max(0.0, instante - obtida_em)
    dentro_validade = bool(validade_efetiva > 0.0 and instante < expira_em)
    fundamentacao = {
        "tema": str(tema or "").strip()[:160],
        "titulo": str(dados.get("titulo") or tema or "").strip()[:160],
        "resumo": resumo[:1200] if confiavel else "",
        "candidatos": candidatos if confiavel else [],
        "fonte": str(dados.get("fonte") or "").strip()[:120] if confiavel else "",
        "confianca": round(confianca, 3) if confiavel else 0.0,
        "confiavel": confiavel,
        "motivo": "fonte_contextual_suficiente" if confiavel else str(dados.get("motivo") or "sem_fonte_suficiente"),
        "ts": instante,
        "atualidade": classificacao_atualidade,
        "requer_evidencia_recente": bool(classificacao_atualidade.get("depende_atualidade")),
        "evidencia_disponivel": bool(dados.get("ok") and resumo),
        "evidencia_obtida_em": obtida_em,
        "evidencia_obtida_em_iso": datetime.fromtimestamp(obtida_em, timezone.utc).isoformat(),
        "evidencia_validade_s": validade_efetiva,
        "evidencia_expira_em": expira_em,
        "evidencia_expira_em_iso": datetime.fromtimestamp(expira_em, timezone.utc).isoformat(),
        "evidencia_idade_s": idade_s,
        "evidencia_dentro_validade": dentro_validade,
        "evidencia_cache": bool(dados.get("evidencia_cache", False)),
        "fontes": [
            {
                "titulo": str(item.get("titulo") or "")[:160],
                "url": str(item.get("url") or "")[:500],
                "dominio": str(item.get("dominio") or "")[:120],
                "alvo": str(item.get("alvo") or "")[:100],
                "trecho": re.sub(r"\s+", " ", str(item.get("trecho") or "")).strip()[:850],
            }
            for item in list(dados.get("fontes") or [])[:5]
            if confiavel and isinstance(item, dict) and item.get("url") and item.get("trecho")
        ],
    }
    fundamentacao["proveniencia"] = classificar_proveniencia_informacao(
        fundamentacao,
        contexto="fundamentacao_factual",
    )
    return avaliar_validade_fundamentacao(fundamentacao, agora=instante)


_GRUPOS_ESPECIFICOS = (
    {"politica", "politico", "deputado", "senador", "presidente", "partido", "mandato", "eleito"},
    {"crime", "preso", "condenado", "fraude", "assassinato", "processo"},
    {"doenca", "diagnostico", "cancer", "internado", "sindrome", "tratamento"},
    {"premio", "premiado", "campeao", "venceu", "vencedor", "indicacao"},
    {"mpb", "jazz", "pop", "rock", "rap", "trap", "samba", "soul", "funk", "reggae", "metal", "blues", "axe"},
    {"fundador", "diretor", "autor", "criador", "inventor", "desenvolvedor", "produtor"},
    {"nascimento", "nasceu", "morreu", "falecido", "casado", "filho", "filha"},
    {"mora", "vive", "cidade", "pais", "brasileiro", "brasileira", "paulista", "carioca", "nacionalidade"},
    {"processador", "ram", "vram", "resolucao", "chipset", "nucleos", "threads"},
    {"ps4", "ps5", "playstation", "xbox", "switch", "plataforma", "compatibilidade"},
)

_FAMILIARIDADE_INVENTADA = re.compile(
    r"\b(?:j[aá]\s+ouvi|(?:eu\s+)?ouvi\s+(?:(?:alg|um)as?|muitas?)\s+m[uú]sicas?|"
    r"ouvi\s+(?:tudo|o\s+cat[aá]logo)|acompanho\s+(?:ele|ela|o\s+trabalho)|"
    r"conhe[cç]o\s+(?:bem|todo|toda)|experimentei\s+(?:todo|toda)|assisti\s+todos?|li\s+todos?)\b",
    re.IGNORECASE,
)

_MEDIDA_ESPECIFICA = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:kb|mb|gb|tb|hz|khz|mhz|ghz|fps|mp|megapixels?|"
    r"km|kg|gramas?|metros?|milimetros?|polegadas?|watts?|w)\b",
    re.IGNORECASE,
)


def _plataformas_citadas(texto: str) -> set[str]:
    normalizado = _normalizar(texto)
    plataformas: set[str] = set()
    for numero in (4, 5, 6):
        if re.search(rf"\b(?:ps\s*{numero}|playstation\s*{numero})\b", normalizado):
            plataformas.add(f"ps{numero}")
    if re.search(r"\bxbox\s+series\s+x\b", normalizado):
        plataformas.add("xbox_series_x")
    if re.search(r"\bxbox\s+series\s+s\b", normalizado):
        plataformas.add("xbox_series_s")
    if re.search(r"\bnintendo\s+switch\s*2\b", normalizado):
        plataformas.add("switch_2")
    if re.search(r"\b(?:pc|windows)\b", normalizado):
        plataformas.add("pc")
    return plataformas


_DESCRICAO_CONTROLE_LOCAL = re.compile(
    # Papel documental de recurso, não compatibilidade externa. Moldura
    # fechada: outra oração/predicado não herda a evidência da implementação.
    r"eu\s+(?:(?:vou|posso)\s+)?(?:usar|uso|utilizar|utilizo)\s+"
    r"o\s+sistema\s+operacional\s+local\s+para\s+"
    r"(?:ajustar|controlar|abrir|fechar|maximizar|organizar)\s+"
    r"(?:o|a|os|as)\s+(?P<recurso>volume|janelas?|programas?)\s+"
    r"(?:do|no)\s+(?:seu|meu|nosso)\s+pc"
    r"(?:\s+sem\s+precisar\s+de\s+conexao\s+com\s+outro\s+(?:dispositivo|computador))?\.?",
)


def _recursos_locais_documentados(documentacao: str) -> set[str]:
    """Lê apenas o escopo do catálogo; não cria evidência de estado ou efeito."""
    try:
        documentos = json.loads(documentacao)
    except (TypeError, ValueError):
        return set()
    if not isinstance(documentos, list):
        return set()
    recursos: set[str] = set()
    for documento in documentos:
        if not isinstance(documento, dict) or documento.get("estado") != "disponivel":
            continue
        regras = documento.get("limites_contextuais")
        if not isinstance(regras, (list, tuple)):
            continue
        for regra in regras:
            if (isinstance(regra, dict) and regra.get("escopo") == "controle_local"
                    and regra.get("responsavel") == "Laylay"):
                recursos.update(re.findall(
                    r"\b(?:volume|janelas?|programas?)\b", _normalizar(regra.get("quando")),
                ))
    return recursos


_DESTAQUE_CITADO = re.compile(
    r'["“]([^"”\n]{2,})["”]|\'([^\'\n]{2,})\'|‘([^’\n]{2,})’|'
    r'(?<!\*)\*{1,2}([^*\n]{2,})\*{1,2}(?!\*)'
)
_DESTAQUE_NOMEACAO = re.compile(_DESTAQUE_CITADO.pattern + r'|«([^«»\n]{2,})»')
_INTRODUCAO_ENUNCIADO = re.compile(
    # A preposição pode introduzir o conteúdo citado do pedido. Reconhecer
    # essa relação não exige reconhecer/executar o verbo dentro da citação.
    # "pedir para tocar 'X'" não encaixa: tocar está FORA do enunciado citado.
    r"\b(?:diga|dizer|digite|digitar|fale|falar|escreva|escrever|"
    r"(?:pe[cç]a|pedir)(?:\s+(?:para|pra))?|pergunte|perguntar|pense|pensar|"
    r"diria|responderia|escreveria|"
    r"(?:quer|quis|queria)\s+dizer\s+com|"
    r"(?:o|um)\s+comando|(?:a|uma)\s+(?:frase|pergunta))"
    r"(?:\s+(?:para|a)\s+(?:mim|ela|ele|voc[eê]|si\s+mesm[oa]))?"
    r"\s*,?\s*(?:(?:algo\s+)?como|por\s+exemplo|(?:exatamente\s+)?assim)?\s*:?\s*$", re.IGNORECASE,
)
_EXEMPLO_CONTEUDO_DISCURSIVO = re.compile(
    # Exemplo do que o interlocutor pode expressar, não uma obra ou um estado
    # observado. A relação inteira precisa preceder a citação: ouvir música,
    # menção de filme e uma nova oração não herdam essa moldura.
    r"\b(?:escutar|ouvir|ler|entender)\s+o\s+que\s+(?:voc[eê]|tu)\s+"
    r"(?:(?:est[aá]|t[aá])\s+(?:pensando|sentindo)|pensa|sente|quer\s+dizer)"
    r"\s*[,—–-]\s*(?:mesmo\s+que|ainda\s+que)\s+seja\s+"
    r"(?:(?:s[oó]|apenas)\s+)?um\s*$", re.IGNORECASE,
)
_EXEMPLO_PEDIDO_INDIRETO = re.compile(
    r"\bpedir\s+para\s+[^.!?;\"'“”‘’]{1,100}[,—–]\s*"
    r"(?:por\s+exemplo|como(?:\s+em)?)\s*:?\s*$", re.IGNORECASE,
)
_REFERENCIA_OPERACIONAL_CITADA = re.compile(
    r"\b(?:app|aplicativo|arquivo|pasta|aba|janela|dispositivo|playlist)"
    r"\s+(?:chamad[oa]\s+)?$", re.IGNORECASE,
)
_REFERENCIA_CONCEITUAL_CITADA = re.compile(
    # Nome de conceito/método não é uma obra. Só tipifica a referência:
    # não mascara datas, medidas ou alegações feitas sobre esse conceito.
    r"\b(?:m[eé]todo|conceito|termo)\s+(?:(?:de|do|da)\s+)?$",
    re.IGNORECASE,
)
_PROGRAMA_OPERACIONAL_CITADO = re.compile(
    # "Programa" sozinho também pode nomear uma obra de rádio/TV.
    r"\b(?:abrir|abre|abra|fechar|fecha|feche|executar|instalar|maximizar|minimizar)"
    r"\s+(?:(?:o|um|esse)\s+)?programa\s+(?:chamado\s+)?$", re.IGNORECASE,
)
_EXEMPLO_NOVA_FRASE = re.compile(r"[.!?]\s+(?:por\s+)?exemplo\s*:\s*$", re.IGNORECASE)
_HIPOTESE_DE_ENUNCIADO = re.compile(
    r"^se\s+[^.!?;:,\n]+,\s*(?:eu\s+)?(?:diria|responderia|escreveria)"
    r"\s*:\s*(?=\[enunciado\])", re.IGNORECASE,
)
_ORIENTACAO_PEDIDO = re.compile(
    r"\b(?:pode|basta|[eé]\s+s[oó])\s+(?:"
    r"pedir(?!\s+(?:(?:o|a|um|uma)\s+)?(?:filme|m[uú]sica|livro|s[eé]rie|t[ií]tulo|obra)\b)|"
    r"dizer|digitar|falar|escrever)\b",
    re.IGNORECASE,
)
_TIPO_OBRA = r"(?:filmes?|livros?|m[uú]sicas?|can[cç][aã]o|can[cç][oõ]es|s[eé]ries?|obras?|t[ií]tulos?|programas?|[aá]lbu(?:m|ns)|jogos?)"
_MOLDURA_OBRA = re.compile(
    # Relação nominal/seleção, não mera ocorrência de 'filme' na frase.
    # 'o filme é "bom"' não nomeia obra; 'o filme chamado "X"' nomeia.
    rf"\b(?:{_TIPO_OBRA}"
    r"(?:\s+(?:mais\s+)?(?:famos[oa]s?|conhecid[oa]s?|recentes?|nov[oa]s?))?"
    r"(?:\s+(?:dele|dela|deles|delas))?"
    r"(?:\s+(?:chamad[oa]s?|intitulad[oa]s?|se\s+chama))?|"
    rf"{_TIPO_OBRA}(?:\s+(?:mais\s+)?(?:famos[oa]s?|conhecid[oa]s?|favorit[oa]s?))?"
    r"\s+(?:dele|dela|deles|delas)\s+(?:[eé]|s[aã]o)|"
    r"(?:recomendo|recomende|recomendar|sugiro|sugerir|indico|indicar|"
    r"assista|assistir|leia|ler|ou[cç]a|ouvir|escute|escutar|toque|tocar)"
    rf"(?:\s+(?:a|ao|o|os|as|um|uma|uns|umas|este|esta|estes|estas))?"
    rf"(?:\s+(?:algo|{_TIPO_OBRA}))?)"
    r"\s*(?:[,—–-]\s*)?(?:(?:por\s+exemplo)|"
    r"(?:mesmo\s+que|ainda\s+que)\s+seja\s+(?:(?:s[oó]|apenas)\s+)?um)?\s*:?\s*$",
    re.IGNORECASE,
)
_TIPO_OBRA_POSPOSTO = re.compile(
    rf"^\s+[eé]\s+(?:um|uma)\s+{_TIPO_OBRA}\b", re.IGNORECASE,
)
_ENUMERACAO_CITADA = re.compile(r"\s*(?:,\s*(?:(?:e|ou)\s+)?|(?:e|ou)\s+)(?:um\s+)?", re.IGNORECASE)
_APRESENTACAO_DE_OBRA = re.compile(
    r"\b(?:(?:a[ií]|aqui)\s+)?vai(?:\s+uma)?"
    r"(?:\s+que\s+eu\s+(?:adoro|gosto))?\s*:\s*$",
    re.IGNORECASE,
)

_ARTEFATO_NOMEAVEL = r"(?:jogo|conto|historia|narrativa|roteiro|livro|filme|serie|obra|cancao|musica|poema|romance)"
_ALVO_NOMEACAO = (
    rf"(?:para|pra|com|ao|a)\s+(?P<alvo>(?:(?:o|a|este|esta|esse|essa|nosso|nossa|um|uma)\s+)?"
    rf"{_ARTEFATO_NOMEAVEL}(?P<descricao>\s+de\s+[\w-]+(?:\s+[\w-]+){{0,3}})?)"
)
_PEDIDO_NOMEACAO = re.compile(
    r"(?:(?:qual|que)\s+(?:nome|titulo)\s+(?:(?:voce|tu)\s+)?"
    r"(?:daria|escolheria|proporia|sugeriria|sugere|combinaria|ficaria\s+bem)|"
    r"(?:invente|sugira|crie|proponha|escolha)\s+um\s+(?:nome|titulo))\s+"
    + _ALVO_NOMEACAO
)
_PEDIDO_IDENTIFICACAO_TITULO = re.compile(
    r"\b(?:nome|titulo)\s+(?:oficial|original|real|verdadeiro|registrado|publicado)\b|"
    r"\b(?:qual|que)\s+(?:e\s+o\s+)?(?:nome|titulo)(?:\s+(?:d[ao]\b|dele\b|dela\b|"
    r"(?:a\s+editora|o\s+estudio)\s+(?:publicou|usou)\b)|\s*$)|"
    r"\bcomo\s+(?:se\s+chama|(?:ele|ela|o\s+jogo|a\s+obra)\s+se\s+chama)\b|"
    r"\b(?:quero|preciso|confirme|consulte|descubra)\s+(?:saber\s+)?o\s+(?:nome|titulo)\b|"
    r"\bnao\s+(?:quero|preciso\s+de)\s+(?:uma\s+)?sugest(?:ao|oes)\b"
)
_MOLDURA_NOME_PROPOSTO = re.compile(
    r"\b(?:(?:t[ií]tulo|nome)(?:\s+(?:sugerido|proposto))?|"
    r"sugest[aã]o(?:\s+de\s+(?:t[ií]tulo|nome))?)\s*:\s*$|"
    r"\b(?:eu\s+)?(?:chamaria\s+de|sugeriria|proporia)\s*:?\s*$", re.IGNORECASE,
)
_MOLDURA_TITULO_IDENTIFICADO = re.compile(
    r"\b(?:encontrei|achei|localizei)\s*:?\s*$|"
    r"\b(?:t[ií]tulo|nome)(?:\s+(?:oficial|original|real|verdadeiro|registrado|publicado))?"
    r"\s+[eé]\s*:?\s*$", re.IGNORECASE,
)
_TITULO_IDENTIFICADO_NO_ENTORNO = re.compile(
    r"\b(?:t[ií]tulo|nome)\s+(?:oficial|original|real|verdadeiro|registrado|publicado)\b",
    re.IGNORECASE,
)


def _finalidade_nomeacao(texto_usuario: str) -> tuple[bool, bool]:
    """Lê o ato da entrada vigente, com alvo explícito e sem adotar citações."""
    proposta = identificacao = False
    for enunciado in enunciados_discursivos(texto_fora_de_citacoes(texto_usuario)):
        texto = _normalizar(enunciado).rstrip(".")
        if _PEDIDO_IDENTIFICACAO_TITULO.search(texto):
            identificacao = True
        elif _PEDIDO_NOMEACAO.fullmatch(texto) or _PEDIDO_NOMEACAO_DO_DIALOGO.fullmatch(texto):
            proposta = True
        else:
            retificacao = _normalizar(trecho_retificacao_do_enunciador(enunciado))
            identificacao |= bool(re.match(r"(?:o\s+)?(?:nome|titulo)\b", retificacao))
    return proposta, identificacao


def separar_descricao_de_nomeacao(texto: str) -> tuple[str, str]:
    """Separa o alvo descrito dos enunciados que podem conter nomes próprios."""
    if ' de ' not in texto.casefold():
        return '', texto
    partes = enunciados_discursivos(texto)
    alvos = []
    for indice, parte in enumerate(partes):
        pedido = _PEDIDO_NOMEACAO.fullmatch(_normalizar(parte).rstrip('.'))
        if (pedido is not None and pedido['descricao'] and not intervalos_citados(parte)
                and not re.search(r'\b(?:e|ou|mas|porem|tambem|chamad[oa])\b', pedido['descricao'])):
            quantidade = len(pedido['alvo'].split())
            alvos.append((indice, ' '.join(parte.rstrip(' .!?;').split()[-quantidade:])))
    if len(alvos) != 1 or _finalidade_nomeacao(texto)[1]:
        return '', texto
    indice, alvo = alvos[0]
    return alvo, ' '.join(partes[:indice] + partes[indice + 1:])


def alvo_nomeacao_autoral(texto: str) -> str:
    """Identifica o alvo de uma proposta sem absorver outras solicitações."""
    alvo, restante = separar_descricao_de_nomeacao(texto)
    if not alvo or not restante:
        return alvo
    if all(_preambulo_sem_outro_pedido(parte) for parte in enunciados_discursivos(restante)):
        return alvo
    return ''


def _preambulo_sem_outro_pedido(texto: str) -> bool:
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia

    leitura = classificar_modalidade_turno(texto)
    if leitura.get('modalidade') != 'conversa' or leitura.get('natureza_acao') != 'nenhuma':
        return False
    base = _normalizar(texto).rstrip('.')
    if re.fullmatch(r'(?:vamos|podemos) (?:deixar|guardar|adiar) (?:\w+ ){1,6}'
                    r'para (?:depois|mais tarde|outro momento)', base):
        return True
    # A modalidade de conversa também abriga imperativos de autoria/ensino.
    # Sem distinguir esses verbos, um título poderia consumir a outra tarefa.
    abertura = re.sub(r'^(?:(?:agora|tamb[eé]m|depois|por favor|me|n[aã]o|voc[eê]|tu)[ ,]+)+',
                      '', texto.casefold())
    primeira = re.match(r'[^\W\d_]+', abertura)
    tipo = consultar_morfologia(primeira[0]) if primeira else None
    return tipo is not None and not tipo & 32  # verbo no léxico canônico


def _indicio_de_obra(prefixo: str, sufixo: str, *, contexto_obra: bool = False) -> bool:
    if _MOLDURA_OBRA.search(prefixo) or _TIPO_OBRA_POSPOSTO.search(sufixo):
        return True
    if contexto_obra and _APRESENTACAO_DE_OBRA.search(prefixo):
        return True
    exemplo = _EXEMPLO_NOVA_FRASE.search(prefixo)
    if exemplo:
        anterior = re.split(r"(?<=[.!?])\s+", prefixo[:exemplo.start()])[-1]
        return bool(_MOLDURA_OBRA.search(anterior))
    return False


def _citacao_didatica(prefixo: str, trecho: str) -> bool:
    # Escopo local: "diga 'X'" cita um enunciado; "diga o título 'X'" não.
    # Não concede confiança à frase inteira nem a outra citação posterior.
    if (_INTRODUCAO_ENUNCIADO.search(prefixo)
            or _EXEMPLO_CONTEUDO_DISCURSIVO.search(prefixo)):
        return True
    novo_exemplo = _EXEMPLO_NOVA_FRASE.search(prefixo)
    frase_anterior = (
        re.split(r"(?<=[.!?])\s+", prefixo[:novo_exemplo.start()])[-1]
        if novo_exemplo else ""
    )
    if _EXEMPLO_PEDIDO_INDIRETO.search(prefixo) or (
        novo_exemplo and _ORIENTACAO_PEDIDO.search(frase_anterior)
    ):
        # Reusa a leitura canônica só para reconhecer um exemplo de pedido.
        # O trecho continua citação da ASSISTENTE, jamais utterance autorizante.
        from mente_laylay.cognicao.identidade_conversacional import analisar_identidade_turno
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
        # Um enunciado endereçado à assistente continua exemplo mesmo se o
        # classificador operacional não souber executar o verbo. A moldura de
        # pedido acima é necessária: vocativo sozinho não isenta uma obra.
        identidade = analisar_identidade_turno(_normalizar(trecho), falante="assistente")
        if identidade["vocativo_laylay"] and identidade["texto_sem_vocativo"]:
            return True
        leitura = classificar_modalidade_turno(trecho)
        return leitura.get("natureza_acao") in {"pedido_direto", "consulta"}
    return False


def contem_citacao_destacada(texto: str) -> bool:
    """Citação pode coexistir com fatos externos mesmo quando não nomeia obra."""
    return bool(_DESTAQUE_CITADO.search(str(texto or "")))


def _destaques_com_papel(
    texto: str, *, texto_usuario: str = "", contexto_obra: bool = False,
) -> list[tuple[re.Match[str], str]]:
    destaques = []
    fim_anterior, papel_anterior = 0, ""
    pede_proposta, pede_identificacao = _finalidade_nomeacao(texto_usuario)
    nomeacao_em_pauta = pede_proposta or pede_identificacao
    destaques_do_turno = _DESTAQUE_NOMEACAO if nomeacao_em_pauta else _DESTAQUE_CITADO
    # Resposta só de nomes pode herdar o tipo solicitado. Isso não transforma
    # toda ênfase de uma conversa sobre filmes em título nem concede autoridade.
    resposta_nominal = bool(
        re.search(rf"\b{_TIPO_OBRA}\b", texto_usuario, re.IGNORECASE)
        and destaques_do_turno.search(texto)
        and re.fullmatch(r"[\s,.;:!?\d\-]*(?:(?:e|ou)[\s,.;:!?\d\-]*)*",
                         destaques_do_turno.sub("", texto), re.IGNORECASE)
    )
    contexto_obra = contexto_obra or bool(re.search(
        rf"\b{_TIPO_OBRA}\b", texto_usuario, re.IGNORECASE,
    ))
    identificacao_no_entorno = nomeacao_em_pauta and bool(
        _TITULO_IDENTIFICADO_NO_ENTORNO.search(destaques_do_turno.sub("", texto))
    )
    for destaque in destaques_do_turno.finditer(texto):
        # Só enumeração direta herda o papel: "diga A ou B". Uma oração
        # como "e recomendo B" inicia outra relação e será avaliada do zero.
        papel_enumerado = papel_anterior if _ENUMERACAO_CITADA.fullmatch(
            texto[fim_anterior:destaque.start()]
        ) else ""
        prefixo = texto[:destaque.start()]
        sufixo = texto[destaque.end():]
        moldura_nominal = _MOLDURA_NOME_PROPOSTO.search(prefixo)
        nome_isolado = (not prefixo or _MOLDURA_NOME_PROPOSTO.fullmatch(prefixo)) and bool(
            re.fullmatch(r"\s*[.!?]*\s*", sufixo)
        )
        # Referências já tipificadas podem aparecer entre o verbo de pedir e
        # seu exemplo. Só essas referências são abstraídas, preservando frases,
        # títulos e outras citações como fronteiras da relação linguística.
        prefixo_relacional = prefixo
        for anterior, papel_anterior in reversed(destaques):
            if papel_anterior == "referencia_operacional":
                prefixo_relacional = (
                    prefixo_relacional[:anterior.start()] + "[recurso]"
                    + prefixo_relacional[anterior.end():]
                )
        if (_REFERENCIA_OPERACIONAL_CITADA.search(prefixo)
                or _PROGRAMA_OPERACIONAL_CITADO.search(prefixo)):
            papel = "referencia_operacional"
        elif _REFERENCIA_CONCEITUAL_CITADA.search(prefixo):
            papel = "referencia_conceitual"
        elif not _TIPO_OBRA_POSPOSTO.search(sufixo) and (
            papel_enumerado == "enunciado" or _citacao_didatica(
                prefixo_relacional, next(g for g in destaque.groups() if g is not None),
            )
        ):
            papel = "enunciado"
        elif pede_proposta and not pede_identificacao and nome_isolado:
            # A entrega inteira é uma denominação para o artefato pedido.
            # Um rótulo dentro de um rascunho misto não basta para essa leitura.
            papel = "nome_proposto"
        elif nomeacao_em_pauta and (
            nome_isolado or moldura_nominal or identificacao_no_entorno
            or _MOLDURA_TITULO_IDENTIFICADO.search(prefixo)
            or _indicio_de_obra(prefixo, sufixo, contexto_obra=contexto_obra)
        ):
            papel = "obra_identificada" if pede_identificacao else "nomeacao_inconclusiva"
        elif (papel_enumerado == "obra_candidata" or resposta_nominal
              or _indicio_de_obra(
                  prefixo, sufixo, contexto_obra=contexto_obra,
              )):
            papel = "obra_candidata"
        else:
            # Ausência de tipo não é evidência de obra. Também NÃO isenta
            # o conteúdo dos demais verificadores: datas/medidas seguem visíveis.
            papel = "indeterminado"
        destaques.append((destaque, papel))
        fim_anterior, papel_anterior = destaque.end(), papel
    return destaques


def _sem_enunciados_didaticos(texto: str, *, posicoes: set[int] | None = None) -> str:
    if posicoes is None:
        posicoes = {m.start() for m, papel in _destaques_com_papel(texto) if papel == "enunciado"}
    projetado = _DESTAQUE_CITADO.sub(
        lambda m: "[enunciado]" if m.start() in posicoes else m.group(0), texto,
    )
    # A condição de um exemplo de fala não afirma que o cenário ocorreu.
    # Só a moldura local com uma única oração condicional é abstraída;
    # predicados fora dela e da citação continuam nos verificadores factuais.
    return _HIPOTESE_DE_ENUNCIADO.sub('[hipotese_de_fala] ', projetado)


def extrair_titulos_citados(texto: str, *, texto_usuario: str = "") -> list[str]:
    """Extrai obras com indício relacional; aspas sozinhas não tipificam obra."""
    bruto = str(texto or "")
    return list(dict.fromkeys(
        next(g for g in m.groups() if g is not None).strip()
        for m, papel in _destaques_com_papel(bruto, texto_usuario=texto_usuario)
        if papel in {"obra_candidata", "obra_identificada"}
    ))


def nomeacao_exige_reparo(fala: str, *, texto_usuario: str, contexto_obra: bool = False) -> bool:
    """Projeta a decisão do revisor factual para a tentativa de reautoria."""
    papeis = {papel for _, papel in _destaques_com_papel(
        fala, texto_usuario=texto_usuario, contexto_obra=contexto_obra,
    )}
    return _nomeacao_fora_do_escopo(texto_usuario, papeis)


def _nomeacao_fora_do_escopo(texto_usuario: str, papeis: set[str]) -> bool:
    return ('nomeacao_inconclusiva' in papeis
            or ('nome_proposto' not in papeis and bool(alvo_nomeacao_autoral(texto_usuario))))


def _titulos_citados(texto: str) -> list[str]:
    return extrair_titulos_citados(texto)


def _predicados_sem_copula_de_foco_prospectivo(frase: str, tema: str) -> str:
    """Distingue foco de participante futuro de uma atribuição ao tema.

    Em ``X é quem P``/``é X quem P``/``quem P é X`` (também com ``que``
    nas duas primeiras formas), a cópula destaca X, não todo objeto
    presente em P. Somente ``ir no presente + infinitivo`` participa
    deste recorte: um plano futuro não confirma ocorrência passada ou efeito.
    Mascara apenas a cópula quando o foco não contém o tema; os predicados
    restantes continuam nas mesmas regras factuais. Não confere X, não resolve
    pronomes, não declara apoio do histórico nem autoriza executar o plano.
    """
    palavra = r"[\wÀ-ÿ]+(?:['’-][\wÀ-ÿ]+)*"
    foco = rf"(?P<foco>{palavra}(?:\s+{palavra}){{0,7}})"
    inicio = r"(?:^|[.!?;:,]\s*)"
    perifrase = r"(?:vai|vão|vao|vou|vamos)\s+[\wÀ-ÿ]+r\b"
    prospectivo = rf"(?:quem|que)\s+{perifrase}"
    formas = (
        rf"{inicio}{foco}\s+(?P<copula>é|e|foi|era)\s+{prospectivo}",
        rf"{inicio}(?P<copula>é|e|foi|era)\s+{foco}\s+{prospectivo}",
        rf"{inicio}quem\s+{perifrase}(?:\s+{palavra}){{0,18}}?\s+"
        rf"(?P<copula>é|e|foi|era)\s+{foco}(?=\s*(?:$|[.!?;:,]))",
    )
    intervalos = []
    tema_normalizado = _normalizar(tema)
    for forma in formas:
        for m in re.finditer(forma, frase, flags=re.IGNORECASE):
            foco_normalizado = _normalizar(m['foco'])
            if (tema_normalizado and re.search(
                r"(?<!\w)" + re.escape(tema_normalizado) + r"(?!\w)", foco_normalizado)):
                continue
            intervalos.append(m.span('copula'))
    for inicio_copula, fim_copula in sorted(set(intervalos), reverse=True):
        frase = frase[:inicio_copula] + ' ' * (fim_copula-inicio_copula) + frase[fim_copula:]
    return _normalizar(frase)


def _frase_especifica_sem_base(frase: str, tema: str = "") -> bool:
    t = _normalizar(frase)
    if len(t.split()) < 4:
        return False
    if _titulos_citados(frase) or re.search(r"\b(?:18|19|20)\d{2}\b", t):
        return True
    if any(_grupo_presente(set(t.split()), grupo) for grupo in _GRUPOS_ESPECIFICOS):
        return True
    tema_norm = _normalizar(tema)
    from mente_laylay.cognicao.normalizacao_linguagem import enunciacao_avaliativa_de_atividade
    subjetiva = bool(re.search(
        r"\b(?:acho|parece|soa|interessante|legal|curioso|curiosa|gosto|na minha opiniao)\b",
        t,
    ) or enunciacao_avaliativa_de_atividade(frase))
    if tema_norm and tema_norm in t and not subjetiva and re.search(
        r"\b(?:e|foi|era|tem|teve|possui|produz|fabrica|criou|fundou|desenvolveu|"
        r"publicou|lancou|participou|trabalhou|pertence|fica|funciona)\b",
        _predicados_sem_copula_de_foco_prospectivo(frase, tema),
    ):
        return True
    return bool(re.search(
        r"\b(?:e conhecido|é conhecido|foi conhecido|uma das|um dos|lancou|lançou|"
        r"criou|fundou|ganhou|mistura|combina elementos|participou|nasceu|morreu|"
        r"se passa em|foi desenvolvido|foi publicado)\b",
        str(frase or ""),
        flags=re.IGNORECASE,
    ))


def _grupo_presente(tokens: set[str], grupo: set[str]) -> bool:
    return any(
        token.strip(".-") == termo
        or (len(termo) >= 4 and token.strip(".-").startswith(termo))
        for token in tokens
        for termo in grupo
    )


def _fala_social_sem_alegacao_externa(frase: str) -> bool:
    """Distingue reação conversacional de uma afirmação factual pesquisável."""
    texto = _normalizar(frase)
    if not texto:
        return False
    if _titulos_citados(frase) or _MEDIDA_ESPECIFICA.search(frase):
        return False
    if re.search(r"\b(?:18|19|20)\d{2}\b", texto):
        return False
    if re.search(
        r"\b(?:nasceu|morreu|lancou|criou|fundou|ganhou|foi desenvolvido|"
        r"foi publicado|se passa em|e conhecido|pertence|possui|produz|"
        r"mistura|combina elementos)\b",
        texto,
    ):
        return False
    return bool(re.search(
        r"\b(?:entendi|legal|boa|interessante|curioso|curiosa|gosto|prefiro|"
        r"combina com voce|te pega|voce curte|me conta|qual|o que)\b",
        texto,
    ))


def _fallback_sem_inventar(tema: str, texto_usuario: str) -> str:
    nome = str(tema or "esse tema").strip()
    usuario = _normalizar(texto_usuario)
    if extrair_aprendizados_pessoais_explicitos(texto_usuario):
        return (
            f"{nome.capitalize()}, então. Boa, isso já me dá uma pista melhor do seu gosto. "
            "O que mais te pega nisso?"
        )
    if re.search(r"\b(?:gosto|curto|adoro|sou fa|tambem gosto)\b", usuario):
        return (
            f"Entendi o que você quis dizer sobre {nome}. Posso seguir por esse fio "
            "sem inventar detalhes que eu ainda não confirmei."
        )
    if re.search(r"\b(?:voce gosta|você gosta|voce curte|você curte|o que acha|qual sua opiniao)\b", str(texto_usuario or ""), flags=re.IGNORECASE):
        return (
            f"Eu ainda não conheço {nome} com segurança suficiente para dizer que gosto ou citar detalhes. "
            "Posso formar uma impressão pelo que eu encontrar de forma confiável, sem fingir repertório."
        )
    if "?" in str(texto_usuario or ""):
        return (
            f"Sobre {nome}, eu não encontrei uma base confiável o bastante para afirmar detalhes específicos. "
            "Prefiro assumir essa limitação a completar a resposta no chute."
        )
    return (
        f"Esse assunto sobre {nome} parece interessante, mas eu ainda não tenho informação verificada "
        "o bastante para acrescentar detalhes sem inventar."
    )


def texto_pede_recomendacao(texto: str) -> bool:
    """Reconhece o pedido factual; música e execução mantêm seus owners."""
    return bool(not texto_e_metalinguistico(texto) and re.search(
        r"\b(?:recomenda|recomende|recomendar|indica|indique|sugere|sugira)\b|"
        r"\b(?:quero|procuro|busco|preciso\s+de)\s+(?:um|uma)\s+"
        r"(?:modelo|op[cç][aã]o|alternativa)\b",
        str(texto or ""), flags=re.IGNORECASE,
    ))


def avaliar_candidatos_recomendacao(
    fundamentacao: Dict[str, Any] | None, *, agora: float | None = None,
) -> list[Dict[str, str]]:
    """Liga cada nome a um trecho da fonte, sem inferir atributos ou adequação.

    Uma lista de nomes não prova preço, especificação ou compatibilidade. O
    conteúdo vem da pesquisa compartilhada, nunca do rascunho da LLM.
    """
    base = dict(fundamentacao or {})
    if not classificar_proveniencia_informacao(
        base, contexto="fundamentacao_factual",
    ).get("pode_sustentar_fato_externo"):
        return []
    if base.get("evidencia_dentro_validade") is False:
        return []
    # Revalidar também fontes estáveis: a lista observada pode ter mudado.
    if "evidencia_expira_em" in base:
        try:
            instante = float(agora if agora is not None else time.time())
            obtida = float(base["evidencia_obtida_em"])
            expira = float(base["evidencia_expira_em"])
        except (KeyError, TypeError, ValueError, OverflowError):
            return []
        if not all(map(math.isfinite, (instante, obtida, expira))) or not obtida <= instante < expira:
            return []
    elif base.get("evidencia_dentro_validade") is not True:
        return []
    candidatos = base.get("candidatos")
    if not isinstance(candidatos, (list, tuple)):
        return []
    fontes = [item for item in (base.get("fontes") or []) if isinstance(item, dict)]
    if not fontes:
        fontes = [{"fonte": base.get("fonte"), "trecho": base.get("resumo")}]
    observados = []
    for candidato in candidatos[:12]:
        if not isinstance(candidato, str) or not candidato.strip():
            continue
        nome = re.sub(r"\s+", " ", candidato).strip()
        for fonte in fontes:
            origem = str(fonte.get("url") or fonte.get("fonte") or "").strip()
            trecho = str(fonte.get("trecho") or "").strip()
            if origem and re.search(
                r"(?<!\w)" + re.escape(_normalizar(nome)) + r"(?!\w)",
                _normalizar(trecho),
            ):
                observados.append({"nome": nome, "fonte": origem, "trecho": trecho})
                break
    return observados


def validar_resposta_recomendacao(
    fala: str, *, fundamentacao: Dict[str, Any] | None, texto_usuario: str = "",
    agora: float | None = None,
) -> Dict[str, Any]:
    """Projeta o rascunho no alcance comprovado; não pede outro reparo à LLM."""
    candidatos = avaliar_candidatos_recomendacao(fundamentacao, agora=agora)
    if not candidatos:
        segura = (
            "Ainda não tenho uma opção verificada para recomendar. "
            "Pode me passar uma opção ou uma fonte para comparar com o seu pedido?"
        )
        motivo = "recomendacao_sem_candidato_verificado"
    else:
        normalizada = _normalizar(fala)
        # Um nome curto não captura uma opção mais longa nomeada no rascunho.
        escolhido = next((item for item in sorted(
            candidatos, key=lambda item: len(item["nome"]), reverse=True,
        ) if re.search(r"(?<!\w)" + re.escape(_normalizar(item["nome"])) + r"(?!\w)", normalizada)), candidatos[0])
        segura = (
            f"Eu iria de {escolhido['nome']} como opção para avaliar. "
            f"A fonte {escolhido['fonte']} lista esse candidato. "
            "Não confirmei se atende a todos os requisitos do seu pedido."
        )
        motivo = "recomendacao_limitada_a_evidencia"
    return {
        "fala": segura, "acao": "ajustada" if fala != segura else "aceita",
        "problemas": ([motivo] + (["obra_sem_evidencia"] if not candidatos
            and extrair_titulos_citados(fala, texto_usuario=texto_usuario) else [])) if fala != segura else [],
        "candidatos_observados": candidatos, "autoriza_execucao": False,
        "comparacao": [{
            "pedido": texto_usuario, "candidato": item["nome"],
            "fonte": item["fonte"], "trecho": item["trecho"],
            "estado_requisitos": "nao_comprovado",
            "afirmacao_comprovada": "nome_presente_na_fonte",
        } for item in candidatos],
    }


def reparar_recomendacao_com_evidencia(
    fundamentacao: Dict[str, Any] | None,
    fala_candidata: str = "",
) -> str:
    """Materializa uma recomendação mínima somente de candidatos observados.

    Quando o modelo escolheu um item válido, a escolha é preservada. O renderer
    apenas remove alegações que a lista pesquisada não comprovou.
    """
    if not avaliar_candidatos_recomendacao(fundamentacao):
        return ""
    return str(validar_resposta_recomendacao(
        fala_candidata, fundamentacao=fundamentacao,
    )["fala"])


_NEGACAO_CAPACIDADE_COM_PESQUISA = re.compile(
    r"\b(?:n[aã]o\s+(?:posso|consigo)\s+(?:te\s+)?"
    r"(?:recomendar|sugerir|indicar)|"
    r"n[aã]o\s+tenho\s+acesso\s+(?:a|à)\s+(?:uma\s+)?"
    r"(?:base\s+de\s+dados|dados|informa[cç][oõ]es|cat[aá]logo))\b",
    re.IGNORECASE,
)

_DESCRICAO_OBRA_FORA_DA_LISTA = re.compile(
    r"\b(?:basead[oa]s?\s+em|hist[oó]ria\s+real|sinopse|enredo|trama|"
    r"protagonist[as]?|personage(?:m|ns)|se\s+passa|dirigid[oa]\s+por|"
    r"estrelad[oa]\s+por|conta\s+(?:a\s+)?hist[oó]ria|acompanha\s+|"
    r"jogador(?:a)?\s+de|se\s+apaixona|final|cl[aá]ssic[oa]s?|roteiro|"
    r"mistura|ritmo|clima|cenas?|explora|mostra|traz|porque|pois|tem)\b",
    re.IGNORECASE,
)
_EXPLICACAO_METALINGUISTICA = re.compile(
    r"\b(?:frase|palavra|pergunta|formula[cç][aã]o|exemplo|cita[cç][aã]o|"
    r"(?:perguntar|dizer|escrever|formular|interpretar|verificar)\w*|"
    r"conte[uú]do\s+real|estrutura\s+da\s+frase)\b",
    re.IGNORECASE,
)


from mente_laylay.cognicao.referencias_linguagem import PREDICADOS_PREFERENCIA as _PREDICADOS_PREFERENCIA
_INICIO_RELATO_PREFERENCIA = (
    r"(?:(?:l[aá]\s+)?no\s+(?:come[cç]o|in[ií]cio),?\s+)?"
    r"voc[eê]\s+"
)
_VERBO_RELATO_PREFERENCIA = r"(?:disse|falou|contou|mencionou|relatou)\s+"
_CABECALHO_RELATO_PREFERENCIA = (
    _INICIO_RELATO_PREFERENCIA + _VERBO_RELATO_PREFERENCIA +
    r"(?:(?:(?:l[aá]\s+)?no\s+(?:come[cç]o|in[ií]cio)|antes)\s+)?"
)


def _ler_preferencia_atribuida(texto: str, *, relato: bool) -> Dict[str, Any] | None:
    """Leitura integral de campos opacos; nenhum alinhamento é proposto pela IA."""
    normalizado = re.sub(r'\s+', ' ', str(texto or '')).strip()
    valor = r"(?P<valor>[\wÀ-ÿ '’&-]{1,100})"
    foco = r"(?:,\s*(?:principalmente|especialmente|sobretudo)\s+(?P<foco>[\wÀ-ÿ '’&-]{1,100}))?"
    argumentos = rf"\s+(?:de\s+)?{valor}{foco}[.!]?"
    negacao = r"(?P<negacao>n[aã]o\s+)?"
    formas = (
        ('relato_indicativo', _CABECALHO_RELATO_PREFERENCIA + r"que\s+" + negacao
            + r"(?P<predicado>gosta|gostava|prefere|preferia|curte|curtia|adora|adorava)" + argumentos),
        ('relato_infinitivo', _CABECALHO_RELATO_PREFERENCIA + negacao
            + r"(?P<predicado>gostar|preferir|curtir|adorar)" + argumentos),
    ) if relato else (
        ('declaracao_usuario', r"(?:(?:para|pra)\s+[\wÀ-ÿ]+r\s+)?(?:eu\s+)?" + negacao
            + r"(?P<predicado>gosto|prefiro|curto|adoro)" + argumentos),
    )
    for forma, padrao in formas:
        m = re.fullmatch(padrao, normalizado, re.I)
        if m is None:
            continue
        valores = {k:str(m.group(k) or '').strip().casefold() for k in ('valor','foco')}
        if any(re.search(r'\b(?:e|ou|se|quando|mas|porque|pois|apesar|embora|n[aã]o|que|sem)\b', v)
               for v in valores.values()):
            return None
        from mente_laylay.cognicao.referencias_linguagem import texto_tem_referencia_contextual
        if any(texto_tem_referencia_contextual(v) or re.search(
            r'\b(?:meu|minha|meus|minhas|seu|sua|seus|suas|teu|tua|teus|tuas|'
            r'nosso|nossa|nossos|nossas|vosso|vossa|eu|tu|voc[eê]|n[oó]s|'
            r'hoje|ontem|amanh[aã]|agora)\b',v) for v in valores.values() if v):
            # Um campo dependente do enunciador/momento não é identificador
            # opaco. Igualdade de palavras não confere a identidade referida.
            return None
        return {'forma':forma, 'texto_normalizado':normalizado,
            'papeis':{'predicado':_PREDICADOS_PREFERENCIA[m['predicado'].casefold()],
                'negada':bool(m['negacao']), **valores},
            'intervalos':{k:list(m.span(k)) for k in ('predicado','negacao','valor','foco')}}
    return None


def _texto_relato_usuario_qualificado(item: Any) -> str | None:
    """Validação comum da fonte pessoal; não decide apoio ou verdade."""
    if (not isinstance(item, dict) or item.get('autor') != 'usuario'
        or not (str(item.get('id') or '').startswith('alegacao:') or (
            str(item.get('id') or '').startswith('dialogo:usuario:') and item.get('origem') == 'historico_conversa') or (
            str(item.get('id') or '').startswith('entrada:usuario:') and item.get('origem') == 'fala_atual'))
        or not classificar_proveniencia_informacao(item).get('pode_sustentar_contexto_pessoal')):
        return None
    texto = item.get('texto')
    if type(texto) is not str or not texto or len(texto) >= 500:
        return None
    if str(item['id']).startswith('dialogo:usuario:') and not re.fullmatch(
        r'dialogo:usuario:\d+:' + hashlib.sha256(texto.encode('utf8')).hexdigest(), item['id']):
        return None
    if str(item['id']).startswith('entrada:usuario:') and not re.fullmatch(
        r'entrada:usuario:[^:\s]+:' + hashlib.sha256(texto.encode('utf8')).hexdigest(), item['id']):
        return None
    return texto


def avaliar_relato_preferencia_usuario(
    fala: str, relatos: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """Distingue fora do recorte, relato sem apoio e transformação conferida.

    Concordância de campos numa declaração pessoal não certifica verdade
    externa, preferência atual ou implicação livre. A fonte e o destino são
    lidos integralmente; a finalidade inicial da fonte permanece no snapshot.
    """
    normalizado = re.sub(r'\s+', ' ', str(fala or '')).strip()
    # Detectar o recorte não é conferir equivalência. Operadores sobre o
    # próprio relato permanecem visíveis e não passam à revisão factual
    # externa; somente a leitura integral abaixo pode conferir apoio.
    escopo = re.match(_INICIO_RELATO_PREFERENCIA + r"(?:[\wÀ-ÿ]+\s+){0,3}"
        + _VERBO_RELATO_PREFERENCIA + r"(?:[\wÀ-ÿ]+\s+){0,5}(?:"
        + '|'.join(_PREDICADOS_PREFERENCIA) + r")\b", normalizado, re.I)
    resultado = {'estado':'fora_do_recorte', 'texto':fala,
        'pode_confirmar_fato_externo':False, 'semantica_verificada':False,
        'prova_implicacao':False, 'autoriza_execucao':False}
    if escopo is None or normalizado.endswith('?'):
        return resultado
    destino = _ler_preferencia_atribuida(fala, relato=True)
    resultado['estado'] = 'sem_apoio' if destino is not None else 'cobertura_incompleta'
    if destino is None:
        return resultado
    for item in relatos:
        texto = _texto_relato_usuario_qualificado(item)
        if texto is None:
            continue
        origem = _ler_preferencia_atribuida(texto, relato=False)
        if origem is not None and origem['papeis'] == destino['papeis']:
            conferencia = {'fonte_id':item['id'], 'texto_fonte':texto, 'texto_destino':fala,
                'alcance':'relato_pessoal_atribuido',
                'pode_confirmar_fato_externo':False, 'semantica_verificada':False,
                'prova_implicacao':False, 'autoriza_execucao':False,
                'derivacao':{'regra':'preservacao_preferencia_atribuida_v1',
                    'fonte_sha256':hashlib.sha256(texto.encode('utf8')).hexdigest(),
                    'destino_sha256':hashlib.sha256(fala.encode('utf8')).hexdigest(),
                    'fonte':origem, 'destino':destino,
                    'alinhamento_estrutural_conferido':True, 'prova_semantica_livre':False}}
            return {**resultado, 'estado':'conferido', 'conferencia':conferencia}
    return resultado


LIMITE_CONFERENCIA_RELATO_USUARIO = "Não consegui conferir essa resposta com o que você contou."


def avaliar_nucleo_retomada_usuario(fala: str, *, plano: Dict[str, Any]) -> Dict[str, Any] | None:
    """Ato retrospectivo exigido não é satisfeito por ausência de conferência.

    Confere somente o núcleo: afirmações adicionais continuam nos respectivos
    revisores. A gramática existente sustenta paráfrases; citação integral
    preserva apenas o dizer. Nenhum desses passos certifica verdade externa.
    """
    from mente_laylay.cognicao.recordacao_atributo import avaliar_recordacao_atributo
    recordacao = avaliar_recordacao_atributo(fala, plano=plano)
    if recordacao is not None:
        return recordacao
    from mente_laylay.cognicao.referencias_linguagem import (
        PerspectivaEnunciador, pedido_consulta_fala_usuario, recorte_consulta_fala_usuario,
    )
    from mente_laylay.cognicao.categoria_preferencia import categoria_consulta_preferencia, conferir_categoria_da_fonte
    contrato = dict(plano.get('contrato_fala') or {})
    fonte = contrato.get('perspectiva_enunciador')
    pedido = str(plano.get('texto_usuario') or '')
    consulta_categoria = categoria_consulta_preferencia(pedido)
    if (type(fonte) is not PerspectivaEnunciador or not fonte.vigente(pedido, plano.get('id'))
        or str(contrato.get('turno_id')) != fonte.turno_id or contrato.get('origem') != 'mente_unica'
        or set(contrato.get('atos') or ()) != {'pergunta'}
        or plano.get('requer_execucao') or plano.get('comandos')
        or {'evidencia_fala_historica', 'explicacao_ocorrencia', 'revisao_alegacao',
            'explicacoes_historicas_por_ato'}.intersection(contrato)
        or not (pedido_consulta_fala_usuario(pedido) or consulta_categoria)):
        return None
    original = str(fala or '').strip()
    resultado = {'admissivel': False, 'estado': 'nucleo_nao_conferido',
        'semantica_verificada': False, 'prova_implicacao': False,
        'pode_confirmar_fato_externo': False, 'autoriza_execucao': False}
    recorte = recorte_consulta_fala_usuario(pedido)

    def vinculo_consulta(texto_fonte: str, fonte_pessoal: Dict[str, Any]) -> Dict[str, Any]:
        if consulta_categoria:
            return conferir_categoria_da_fonte(plano, fonte_pessoal)
        if recorte is None:
            return {'estado': 'fora_do_recorte_literal', 'conferido': None}
        # Preservar acentos dos nomes: normalização de busca não prova identidade.
        def literal(texto: str) -> str:
            return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', texto).casefold()).strip(' .!?')
        consulta, texto = literal(recorte['conteudo']), literal(texto_fonte)
        if recorte['tipo'] == 'proposicao_literal':
            # A polaridade da pergunta não é uma declaração. A citação pode
            # refutar sua premissa, mas deve conservar o mesmo núcleo literal.
            nucleo = lambda t: re.sub(r'^(?:eu\s+)?(?:n[aã]o\s+)?', '', t)
            conferido = bool(consulta and nucleo(consulta) == nucleo(texto))
        else:
            conferido = bool(consulta and re.search(r'(?<!\w)' + re.escape(consulta) + r'(?!\w)', texto))
        return {'estado': 'vinculo_literal_conferido' if conferido else 'fonte_fora_da_consulta',
                'conferido': conferido, 'recorte': dict(recorte)}

    if original == LIMITE_CONFERENCIA_RELATO_USUARIO:
        return {**resultado, 'admissivel': True, 'estado': 'limite_de_conferencia'}
    relatos = tuple(r for r in plano.get('relatos_usuario') or ()
                    if isinstance(r, dict) and r.get('origem') != 'fala_atual')
    citacao = re.match(r'Voc[eê]\s+(?:disse|contou):\s*«([^«»\r\n]+)»\.', original, re.I)
    if citacao is not None:
        for item in relatos:
            texto = _texto_relato_usuario_qualificado(item)
            if texto is not None and texto == citacao[1]:
                vinculo = vinculo_consulta(texto, item)
                if vinculo['conferido'] is False:
                    return {**resultado, 'vinculo_consulta': vinculo}
                return {**resultado, 'admissivel': True, 'estado': 'citacao_integral_atribuida',
                    'fonte_id': item['id'], 'texto_fonte': texto,
                    'fonte_sha256': hashlib.sha256(texto.encode('utf8')).hexdigest(),
                    'vinculo_consulta': vinculo}
    primeira = re.split(r'(?<=[.!?])\s+', original, maxsplit=1)[0]
    conferencia = avaliar_relato_preferencia_usuario(primeira, relatos)
    if conferencia['estado'] == 'conferido':
        fonte_pessoal = next((f for f in relatos if f.get('id') == conferencia['conferencia']['fonte_id']), {})
        vinculo = vinculo_consulta(conferencia['conferencia']['texto_fonte'], fonte_pessoal)
        if vinculo['conferido'] is False:
            return {**resultado, 'vinculo_consulta': vinculo}
        return {**resultado, 'admissivel': True, 'estado': 'parafrase_atribuida_conferida',
                'conferencia': conferencia['conferencia'], 'vinculo_consulta': vinculo}
    return {**resultado, 'revisao_nucleo': conferencia}


def realizacoes_retomada_usuario(*, plano: Dict[str, Any]) -> tuple[str, ...]:
    """Oferece dizeres literais conferíveis, sem decidir sua pertinência.

    A fonte histórica deve preservar a identidade integral do diálogo. Uma
    alegação normalizada não fornece essa identidade para uma citação literal.
    Não recorta, ranqueia nem transforma fontes; a revisão final permanece dona
    da conferência. A escolha do modelo não prova implicação ou verdade atual.
    """
    nucleo = avaliar_nucleo_retomada_usuario('', plano=plano)
    if nucleo is None:
        return ()
    if 'realizacoes' in nucleo:
        return tuple(nucleo['realizacoes'])
    opcoes: list[str] = []
    for item in plano.get('relatos_usuario') or ():
        if (not isinstance(item, dict) or item.get('origem') != 'historico_conversa'
            or not str(item.get('id') or '').startswith('dialogo:usuario:')):
            continue
        texto = _texto_relato_usuario_qualificado(item)
        if texto is None or any(c in texto for c in '«»\r\n'):
            continue
        fala = f'Você contou: «{texto}».'
        revisao = avaliar_nucleo_retomada_usuario(fala, plano=plano)
        if revisao and revisao['estado'] == 'citacao_integral_atribuida' and fala not in opcoes:
            opcoes.append(fala)
    return (*opcoes, LIMITE_CONFERENCIA_RELATO_USUARIO)


def conferir_relato_preferencia_usuario(
    fala: str, relatos: Iterable[Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Compatibilidade: ausência de conferência não equivale a aprovação."""
    return avaliar_relato_preferencia_usuario(fala, relatos).get('conferencia')


def validar_fala_com_fundamentacao(
    fala: str,
    *,
    fundamentacao: Dict[str, Any] | None,
    texto_usuario: str = "",
    agora: float | None = None,
    contexto_metalinguistico: bool = False,
    documentacao_capacidades: str = "",
    contexto_obra: bool = False,
    relatos_usuario: Iterable[Dict[str, Any]] = (),
    apenas_relatos_usuario: bool = False,
    plano: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    original = re.sub(r"\s+", " ", str(fala or "")).strip()
    from mente_laylay.cognicao.criacao_ficcional import criacao_ficcional_vigente, fala_ficcional_em_bloco
    criacao_vinculada = False
    if (plano and texto_usuario == plano.get('texto_usuario')
            and criacao_ficcional_vigente(plano) is not None):
        from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
        revisao = revisar_suporte_autoria(original, plano=plano, agora=agora)
        if (revisao is not None and not revisao.aplicar_limite
                and revisao.como_dict()['estado'] == 'criacao_ficcional_delimitada'):
            criacao_vinculada = True
        if criacao_vinculada and fala_ficcional_em_bloco(original):
            # O owner já conferiu contrato nativo, ocorrência, proposta inteira,
            # ausência de fontes e moldura integral. Datas e características
            # nesse conteúdo não são alegações do mundo. Não isentar o pedido
            # ou um prefixo isolado; os demais revisores continuam ativos.
            return {'fala': original, 'problemas': [], 'acao': 'aceita',
                'escopo': 'criacao_ficcional_delimitada', 'prova_factual': False,
                'prova_semantica_livre': False, 'autoriza_execucao': False,
                'relatos_usuario_conferidos': [], 'revisao_relatos_usuario': []}
    from mente_laylay.cognicao.opiniao_autoral import avaliar_opiniao_autoral
    opiniao = avaliar_opiniao_autoral(texto_usuario, original, plano=plano or {})
    if opiniao is not None and opiniao['aceita']:
        # Só a realização integral do ato autoral já conferido. Não isentar
        # primeira pessoa, nomes de gêneros, causas ou características livres.
        return {'fala': original, 'problemas': [], 'acao': 'aceita',
            'opiniao_autoral_conferida': True, 'prova_factual': False,
            'prova_semantica_livre': False, 'autoriza_execucao': False,
            'relatos_usuario_conferidos': [], 'revisao_relatos_usuario': []}
    if criacao_vinculada:
        # Sem bloco fechado, a finalidade não dispensa revisão das alegações,
        # inclusive na rota sem pesquisa que normalmente confere só relatos.
        apenas_relatos_usuario = False
    base = avaliar_validade_fundamentacao(fundamentacao, agora=agora)
    reparo_recomendacao = reparar_recomendacao_com_evidencia(base, original)
    if (
        reparo_recomendacao
        and base.get("confiavel")
        and base.get("evidencia_dentro_validade", True) is not False
        and _NEGACAO_CAPACIDADE_COM_PESQUISA.search(original)
    ):
        return {
            "fala": reparo_recomendacao,
            "problemas": ["negacao_capacidade_contradiz_pesquisa"],
            "acao": "recomendacao_reparada_por_evidencia",
            "trechos_rejeitados": [original],
        }
    tema = str(base.get("titulo") or base.get("tema") or "esse tema").strip()
    evidencia = " ".join((
        str(base.get("resumo") or ""),
        str(texto_usuario or ""),
    ))
    evidencia_norm = _normalizar(evidencia)
    preferencia_declarada = bool(
        base.get("declaracao_pessoal_explicita")
        or extrair_aprendizados_pessoais_explicitos(texto_usuario)
    )
    problemas: list[str] = []
    rejeitadas: list[str] = []
    relatos_conferidos: list[dict[str, Any]] = []
    revisoes_relatos: list[dict[str, Any]] = []
    relatos_usuario = tuple(relatos_usuario or ())
    evidencia_lista_candidatos = bool(
        base.get("confiavel")
        and base.get("candidatos")
        and str(base.get("titulo") or "").casefold().startswith("candidatos de ")
    )
    candidatos_normalizados = {
        _normalizar(item)
        for item in list(base.get("candidatos") or [])
        if _normalizar(item)
    }

    # O papel é resolvido no texto completo: separar frases não pode apagar a
    # relação entre uma orientação e seu exemplo na frase imediatamente seguinte.
    papeis_citados = _destaques_com_papel(
        original, texto_usuario=texto_usuario, contexto_obra=contexto_obra,
    )
    if _nomeacao_fora_do_escopo(texto_usuario, {papel for _, papel in papeis_citados}):
        # A proposta misturada a uma identificação precisa voltar à autoria.
        # Uma pesquisa pelo próprio título sugerido não resolveria a mistura.
        return {"fala": "", "problemas": ["nomeacao_sem_delimitacao"], "acao": "reparar",
                "trechos_rejeitados": [original], "autoriza_execucao": False,
                "requer_reparo": True}
    # Um exemplo ou título tipificado é indivisível. Demais citações conservam
    # a revisão por oração. O papel do título não se transfere para o entorno.
    frases = list(enunciados_discursivos(original, intervalos_protegidos=tuple(
        m.span() for m, papel in papeis_citados
        if papel in {"enunciado", "nome_proposto", "obra_identificada"}
    ), separar_ponto_e_virgula=False))
    posicoes_didaticas = {m.start() for m, papel in papeis_citados if papel == "enunciado"}
    recursos_locais = _recursos_locais_documentados(documentacao_capacidades)
    evidencia_obra = _normalizar(base.get("resumo")) if base.get("confiavel") else ""
    identificacao_sem_evidencia = False
    fim_frase = 0
    for frase_original in frases:
        inicio_frase = original.index(frase_original, fim_frase)
        fim_frase = inicio_frase + len(frase_original)
        revisao_relato = avaliar_relato_preferencia_usuario(frase_original, relatos_usuario)
        if revisao_relato['estado'] != 'fora_do_recorte':
            revisoes_relatos.append(revisao_relato)
            if revisao_relato['estado'] == 'conferido':
                relatos_conferidos.append(revisao_relato['conferencia'])
            else:
                problemas.append('relato_usuario_sem_apoio')
                rejeitadas.append(frase_original)
            # Pesquisa do assunto não pode suprir a declaração do usuário.
            continue
        destaques_frase = [(m, papel) for m, papel in papeis_citados
                           if inicio_frase <= m.start() < fim_frase]
        if any(papel == "nome_proposto" for _, papel in destaques_frase):
            continue
        obras_identificadas = [next(g for g in m.groups() if g is not None).strip()
                              for m, papel in destaques_frase if papel == "obra_identificada"]
        if apenas_relatos_usuario and not obras_identificadas:
            continue
        # Datas/medidas dentro de um exemplo de pedido também são conteúdo
        # citado, não afirmações factuais. O restante continua sendo validado.
        frase = _sem_enunciados_didaticos(frase_original, posicoes={
            p - inicio_frase for p in posicoes_didaticas if inicio_frase <= p < fim_frase
        })
        explicacao_metalinguistica = bool(
            contexto_metalinguistico
            and _EXPLICACAO_METALINGUISTICA.search(frase)
        )
        # Reusar o papel completo, inclusive 'Recomendo um filme. Exemplo: X'.
        # Reclassificar apenas a segunda frase perderia a relação comprovada.
        titulos = [next(g for g in m.groups() if g is not None).strip()
                   for m, papel in destaques_frase if papel == "obra_candidata"]
        identificacao_sem_fonte = any(
            not _normalizar(titulo) or not re.search(
                rf"(?<!\w){re.escape(_normalizar(titulo))}(?!\w)", evidencia_obra,
            )
            for titulo in obras_identificadas
        )
        identificacao_sem_evidencia |= identificacao_sem_fonte
        titulo_sem_evidencia = bool(
            identificacao_sem_fonte or (not explicacao_metalinguistica
            and any(_normalizar(titulo) not in evidencia_norm for titulo in titulos))
        )
        anos = set(re.findall(r"\b(?:18|19|20)\d{2}\b", _normalizar(frase)))
        ano_sem_evidencia = any(ano not in evidencia_norm for ano in anos)
        tokens = set(_normalizar(frase).split())
        tokens_evidencia = set(evidencia_norm.split())
        categoria_sem_evidencia = any(
            _grupo_presente(tokens, grupo) and not _grupo_presente(tokens_evidencia, grupo)
            for grupo in _GRUPOS_ESPECIFICOS
        )
        medida_sem_evidencia = bool(
            _MEDIDA_ESPECIFICA.search(frase)
            and _normalizar(_MEDIDA_ESPECIFICA.search(frase).group(0)) not in evidencia_norm
        )
        plataformas_frase = _plataformas_citadas(frase)
        descricao_local = _DESCRICAO_CONTROLE_LOCAL.fullmatch(_normalizar(frase))
        if descricao_local and descricao_local.group("recurso") in recursos_locais:
            # Só o papel de PC nessa descrição é resolvido pelo catálogo.
            # Não concatenar o catálogo à fonte factual nem isentar a frase
            # dos outros validadores (datas, medidas, estado e receipts).
            plataformas_frase.discard("pc")
        plataformas_evidencia = _plataformas_citadas(evidencia)
        plataforma_sem_evidencia = bool(plataformas_frase - plataformas_evidencia)
        familiaridade_inventada = bool(_FAMILIARIDADE_INVENTADA.search(frase))
        reacao_social_preferencia = bool(
            preferencia_declarada and _fala_social_sem_alegacao_externa(frase)
        )
        sem_base = bool(
            not base.get("confiavel")
            and _frase_especifica_sem_base(frase, tema)
            and not reacao_social_preferencia
            and not explicacao_metalinguistica
        )
        frase_normalizada = _normalizar(frase)
        frase_nomeia_candidato = any(
            candidato in frase_normalizada
            for candidato in candidatos_normalizados
        )
        declaracao_adicional_nao_comprovada = bool(
            not frase_nomeia_candidato
            and "?" not in frase
            and len(frase_normalizada.split()) >= 4
        )
        descricao_encontrada = _DESCRICAO_OBRA_FORA_DA_LISTA.search(frase)
        descricao_obra_sem_evidencia = bool(
            evidencia_lista_candidatos
            and (
                declaracao_adicional_nao_comprovada
                or (
                    descricao_encontrada
                    and _normalizar(descricao_encontrada.group(0)) not in evidencia_norm
                )
            )
        )
        if (
            titulo_sem_evidencia or ano_sem_evidencia or categoria_sem_evidencia
            or medida_sem_evidencia or plataforma_sem_evidencia
            or familiaridade_inventada or sem_base or descricao_obra_sem_evidencia
        ):
            rejeitadas.append(frase_original)
            if titulo_sem_evidencia:
                problemas.append("obra_sem_evidencia")
            if ano_sem_evidencia:
                problemas.append("data_sem_evidencia")
            if categoria_sem_evidencia:
                problemas.append("caracteristica_sem_evidencia")
            if medida_sem_evidencia:
                problemas.append("medida_sem_evidencia")
            if plataforma_sem_evidencia:
                problemas.append("plataforma_sem_evidencia")
            if familiaridade_inventada:
                problemas.append("familiaridade_inventada")
            if sem_base:
                problemas.append("alegacao_especifica_sem_fonte")
            if descricao_obra_sem_evidencia:
                problemas.append("descricao_obra_sem_evidencia")

    if not rejeitadas:
        return {"fala": original, "problemas": [], "acao": "aceita",
                "relatos_usuario_conferidos": relatos_conferidos,
                "revisao_relatos_usuario": revisoes_relatos}

    if criacao_vinculada:
        # Uma narrativa não é uma coleção de respostas independentes. Se a
        # moldura não fecha o corpo e há conteúdo não conferido, rejeitar a
        # unidade; não publicar o recorte restante como conclusão bem-sucedida.
        return {'fala': '', 'problemas': list(dict.fromkeys(problemas)),
            'acao': 'criacao_sem_delimitacao_integral',
            'trechos_rejeitados': rejeitadas, 'autoriza_execucao': False,
            'requer_reparo': True}

    if reparo_recomendacao and {
        "obra_sem_evidencia", "descricao_obra_sem_evidencia",
    }.intersection(problemas):
        # A pesquisa já materializou opções verificáveis. Se a LLM sair dessa
        # lista, não preservamos descrições anexadas ao título inventado: a
        # fala inteira volta para um candidato observado na mesma evidência.
        return {
            "fala": reparo_recomendacao,
            "problemas": list(dict.fromkeys(problemas)),
            "acao": "recomendacao_reparada_por_evidencia",
            "trechos_rejeitados": rejeitadas,
        }

    restantes = [frase for frase in frases if frase not in rejeitadas]
    fala_segura = " ".join(restantes).strip()
    # Saudações soltas como "isso é ótimo" não sustentam a resposta depois
    # que os detalhes inventados são removidos.
    possui_relato_conferido = any(r['texto_destino'] in restantes for r in relatos_conferidos)
    if identificacao_sem_evidencia or (
        len(_normalizar(fala_segura).split()) < 7 and not possui_relato_conferido
    ):
        fala_segura = ('Não consegui conferir essa preferência no que você contou.'
            if 'relato_usuario_sem_apoio' in problemas else _fallback_sem_inventar(tema, texto_usuario))
    return {
        "fala": fala_segura,
        "problemas": list(dict.fromkeys(problemas)),
        "acao": "ajustada",
        "trechos_rejeitados": rejeitadas,
        "relatos_usuario_conferidos": relatos_conferidos,
        "revisao_relatos_usuario": revisoes_relatos,
    }
