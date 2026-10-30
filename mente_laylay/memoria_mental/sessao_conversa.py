"""Limites de sessão para impedir que contexto encerrado volte como conversa atual."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from mente_laylay.cognicao.contratos_turno import ContratoOcorrenciaTurno

from mente_laylay.memoria_mental.registro_semantico import renovar_registro_semantico_sessao
from mente_laylay.memoria_mental.pendencia_acao import CHAVE_PENDENCIA_ACAO
from mente_laylay.memoria_mental.continuidade_geral import estado_continuidade_geral_inicial
from mente_laylay.cognicao.normalizacao_linguagem import separar_saudacao_inicial


def texto_encerra_conversa(texto: str) -> bool:
    # Cortesia não concede autoridade para descartar a sessão. Confere o
    # núcleo restante INTEGRAL, sem extrair fechamento de outro pedido.
    _, t = separar_saudacao_inicial(texto)
    if '?' in t:
        return False
    t = t.strip(" .!")
    if not t:
        return False
    # A mesma moldura pode vir ao final, delimitada por pontuação. Não
    # remover conteúdo livre ou comandos após o cumprimento.
    partes = re.split(r"[,;.!]", t)
    if len(partes) > 1:
        saudacao, restante = separar_saudacao_inicial(partes[-1].strip())
        if saudacao and not restante:
            t = t[:t.rfind(partes[-1])].rstrip(" ,;.!")
    padroes = (
        r"(?:tchau|ate mais|falou|fui),?(?: lay| laylay)?",
        r"(?:por hoje|por agora) e so",
        r"(?:era|e) so isso(?: mesmo)?",
        r"(?:obrigado|obrigada|valeu),? (?:era|e) so isso",
        r"(?:vamos|a gente) (?:parar|encerra|encerrar) por aqui",
        r"(?:encerra|encerre|finaliza|finalize) (?:a )?conversa",
        r"depois (?:a gente|nos) conversa",
        r"vou (?:sair|dormir|embora),?(?: ate mais)?",
    )
    return any(re.fullmatch(padrao, t, flags=re.IGNORECASE) for padrao in padroes)


def _limpar_campos(estado: Dict[str, Any], campos: Iterable[str], prefixos: Iterable[str] = ()) -> Dict[str, Any]:
    novo = dict(estado or {})
    alvos = set(campos)
    prefixos = tuple(prefixos)
    alvos.update(chave for chave in novo if any(chave.startswith(prefixo) for prefixo in prefixos))
    for chave in alvos:
        valor = novo.get(chave)
        if chave.endswith("_ts") or chave.endswith("_at"):
            novo[chave] = 0.0
        elif isinstance(valor, list):
            novo[chave] = []
        elif isinstance(valor, dict):
            novo[chave] = {}
        elif isinstance(valor, bool):
            novo[chave] = False
        else:
            novo[chave] = ""
    return novo


def _ocorrencia_em_conclusao(
    mental: Dict[str, Any], ocorrencia: ContratoOcorrenciaTurno | None,
) -> Dict[str, Any]:
    """Preserva o frame original conferido, sem ressuscitar contexto ou ação."""
    from mente_laylay.cognicao.contratos_turno import ContratoOcorrenciaTurno
    from mente_laylay.cognicao.decisao_turno import motivo_divergencia_ocorrencia_turno
    if type(ocorrencia) is not ContratoOcorrenciaTurno:
        return {}
    turno = mental.get('turno_atual')
    plano = mental.get('plano_turno_atual')
    contrato = mental.get('contrato_fala_atual')
    retrato = mental.get('retrato_turno_atual')
    if (not all(isinstance(c, dict) for c in (turno, plano, contrato, retrato))
        or turno.get('encerramento_assunto') != 'sessao'
        or turno.get('natureza_entrada') == 'evento' or plano.get('natureza_entrada') == 'evento'
        or turno.get('autoriza_execucao') is not False or plano.get('autoriza_execucao') is not False
        or not isinstance(plano.get('decisao_turno'), dict)
        or plano['decisao_turno'].get('permite_acao') is not False
        or plano.get('requer_execucao') or plano.get('comandos') or plano.get('fase') != 'planejado'
        or mental.get('ultima_entrada') != ocorrencia.texto_usuario
        or str(contrato.get('turno_id')) != ocorrencia.turno_id
        or contrato.get('autoriza_execucao') is not False or contrato.get('origem') != 'mente_unica'
        or turno.get('contrato_fala') != contrato or plano.get('contrato_fala') != contrato
        or motivo_divergencia_ocorrencia_turno(ocorrencia, turno=turno, plano=plano, retrato=retrato)):
        return {}
    # Nenhuma reconstrução de turno ou cópia de oferta/receipt antigo. Os
    # snapshots nativos continuam vinculados; a sessão anterior é descartada.
    campos = ('ultima_entrada', 'ultima_entrada_ts', 'turno_atual', 'plano_turno_atual',
        'contrato_fala_atual', 'retrato_turno_atual', 'identidade_turno_atual',
        'identidade_turno_resumo', 'funcao_comunicativa_atual', 'especialistas_turno_atual')
    return {c: mental[c] for c in campos if c in mental}


def renovar_contexto_sessao(
    mental: Dict[str, Any] | None,
    conversacional: Dict[str, Any] | None,
    mensagens: list | None,
    *,
    motivo: str,
    ativa: bool,
    agora: float | None = None,
    ocorrencia_em_conclusao: ContratoOcorrenciaTurno | None = None,
) -> tuple[Dict[str, Any], Dict[str, Any], list]:
    """Renova a sessão; conclusão explícita pode manter seu frame sem autoridade."""
    instante = float(agora if agora is not None else time.time())
    conclusao = (_ocorrencia_em_conclusao(dict(mental or {}), ocorrencia_em_conclusao)
                 if motivo == 'despedida_usuario' and ativa is False else {})
    mental_novo = _limpar_campos(
        dict(mental or {}),
        (
            "ultima_entrada", "ultimas_entradas", "ultima_entrada_ts", "ultima_resposta",
            "direcao_fala_atual", "historico_direcao_fala",
            "ultima_intencao", "ultimo_alvo", "ultimo_escopo", "ultima_habilidade",
            "ultimo_app_janela", "ultimo_site_aba", "ultimo_layout_janelas",
            "continuidade_geral",
            "pendencia_atual", "ultima_pendencia_encerrada", "oferta_pendente",
            CHAVE_PENDENCIA_ACAO,
            "ultimo_resumo_pagina", "capacidade_futura", "foco_vivo", "focos_por_dominio",
            "email_contexto", "rascunho_email_atual",
            "conteudo_atual", "turno_atual", "plano_turno_atual", "ultima_decisao_semantica",
            "contrato_fala_atual",
            "cenario_didatico_inventario", "cenario_didatico_sombra",
            "auditoria_alegacoes_didaticas_sombra",
            "retrato_turno_atual", "especialistas_turno_atual", "assunto_estruturado_atual",
            "identidade_turno_atual", "identidade_turno_resumo", "funcao_comunicativa_atual",
            "ultima_correcao_conversacional", "ultima_correcao_conversacional_ts",
        ),
        prefixos=(
            "pergunta_aberta_", "ultima_promessa_", "foco_conversacional_",
            "foco_operacional_", "topico_explicito_", "ultima_acao_",
            "ultima_estrutura_arquivo_",
        ),
    )
    mental_novo.update({
        "continuidade_geral": estado_continuidade_geral_inicial(),
        "registro_semantico": renovar_registro_semantico_sessao(
            (mental or {}).get("registro_semantico") if isinstance(mental, dict) else {},
            motivo=motivo,
            agora=instante,
        ),
        "sessao_conversa_ativa": bool(ativa),
        "sessao_conversa_motivo": str(motivo or "renovacao"),
        "sessao_conversa_ts": instante,
    })
    mental_novo.update(conclusao)

    conversa_nova = dict(conversacional or {})
    conversa_nova.update({
        "current_emotion": "calma",
        "emotion_level": 1,
        "emotion_cause": "nova sessão de conversa",
        "emotion_started_at": instante,
        "emotion_duration_s": 0.0,
        "emotion_interactions_total": 0,
        "emotion_interactions_left": 0,
        "ultimo_topico_conversa": "",
        "ultimo_topico_ts": 0.0,
        "topicos_conversa_recente": [],
        "sessao_conversa_ativa": bool(ativa),
        "sessao_conversa_motivo": str(motivo or "renovacao"),
        "sessao_conversa_ts": instante,
    })

    sistemas = [
        dict(mensagem) for mensagem in list(mensagens or [])
        if isinstance(mensagem, dict) and str(mensagem.get("role") or "").casefold() == "system"
    ]
    return mental_novo, conversa_nova, sistemas[:1]
