"""Políticas de domínio usadas pela composição sem depender do processo raiz."""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Mapping, Sequence


def construir_estado_visual(
    *,
    conversa_get: Callable[[str, Any], Any],
    plano_get: Callable[[], Mapping[str, Any]],
    time_fn: Callable[[], float] = time.time,
) -> dict[str, Any]:
    """Traduz estado mental e plano recente para o contrato visual do avatar."""
    agora = time_fn()
    falando = bool(conversa_get("audio_playing", False))
    preparando_fala = bool(conversa_get("is_speaking", False)) and not falando
    atividade = str(conversa_get("visual_activity", "idle") or "idle")
    if agora > float(conversa_get("visual_activity_until", 0.0) or 0.0):
        atividade = "idle"
    reaction_id = ""
    plano = dict(plano_get() or {})
    atualizado = float(plano.get("atualizado_ts") or plano.get("ts") or 0.0)
    idade_plano = agora - atualizado if atualizado else 999.0
    fase = str(plano.get("fase") or "").strip().lower()
    comandos = [item for item in list(plano.get("comandos") or []) if isinstance(item, dict)]
    erros = list(plano.get("erros") or [])
    falhou = bool(erros) or any(
        item.get("confirmado") is False
        or str(item.get("status") or "").lower() in {
            "erro", "falha", "indisponivel", "não_confirmado", "nao_confirmado",
        }
        for item in comandos
    )
    if falando:
        atividade = "speaking"
    elif preparando_fala:
        atividade = "thinking"
    elif idade_plano <= 2.8 and falhou:
        atividade = "error"
        reaction_id = f"erro:{plano.get('id') or atualizado}"
    elif idade_plano <= 2.2 and comandos and fase in {"executado", "tratado_pre_fluxo"}:
        atividade = "success"
        reaction_id = f"sucesso:{plano.get('id') or atualizado}"
    elif idade_plano <= 8.0 and comandos and fase not in {"executado", "tratado_pre_fluxo"}:
        atividade = "executing"
    elif idade_plano <= 8.0 and fase in {"planejado", "resposta_planejada", "fala_verificada"}:
        atividade = "thinking"
    nivel = int(conversa_get("emotion_level", 1) or 1)
    return {
        "emotion": conversa_get("current_emotion", "calma"),
        "level": nivel,
        "speaking": falando,
        "activity": atividade,
        "intensity": max(0.25, min(1.0, float(nivel) / 3.0)),
        "reaction_id": reaction_id,
    }


def recomendar_playlist_real_para_presenca(
    clima: str,
    *,
    carregar_playlists: Callable[[], Mapping[str, Any]],
    registrar_falha: Callable[..., Any] | None = None,
    log: Callable[[str], Any] = print,
) -> str:
    """Escolhe somente entre playlists existentes; nunca inventa nem dá play."""
    try:
        nomes = [
            str(nome).strip() for nome in dict(carregar_playlists() or {}).keys()
            if str(nome).strip()
        ]
    except Exception as erro:
        log(
            "⚠️ [PRESENÇA:MÚSICA] playlists reais indisponíveis: "
            f"{type(erro).__name__}: {erro}"
        )
        if callable(registrar_falha):
            registrar_falha("presenca_musical", "falha_carregar_playlists", erro=erro)
        nomes = []
    if not nomes:
        return ""
    preferencias = {
        "foco": ("synthwave", "devaneios", "vibes", "alternativo", "brisa"),
        "intenso": ("rock", "alternativo", "anime", "trap"),
        "calmo": ("brisa", "vibes", "devaneios", "musica brasileira"),
        "sombrio": ("alternativo", "synthwave", "rock"),
    }
    tokens = preferencias.get(str(clima or "").casefold(), preferencias["foco"])
    escolhida = next((
        nome for token in tokens for nome in nomes if token in nome.casefold()
    ), "")
    if not escolhida:
        return ""
    return (
        f"Você tá num foco bonito faz um tempo. A sua playlist {escolhida} "
        "combina com esse ritmo, se quiser manter a cabeça embalada."
    )


def aprender_pesquisa_semantica_arquivos(
    consulta: str,
    resultados: Sequence[Mapping[str, Any]],
    *,
    normalizar: Callable[[str], str],
    registrar_evidencia: Callable[..., Any],
) -> bool:
    """Aprende apenas o assunto agregado de buscas locais úteis."""
    normalizada = normalizar(str(consulta or ""))
    bloqueados = {
        "arquivo", "arquivos", "documento", "documentos", "encontra", "procura",
        "busca", "pesquisa", "sobre", "meu", "minha", "meus", "minhas",
    }
    termos = [
        termo for termo in re.findall(r"[a-z0-9_]{3,}", normalizada)
        if termo not in bloqueados and not termo.isdigit()
    ][:3]
    if not termos or not resultados:
        return False
    assunto = " ".join(dict.fromkeys(termos))[:80]
    return bool(registrar_evidencia(
        chave=f"arquivos:assunto_busca:{'-'.join(assunto.split())}",
        tipo="assunto_recorrente_pesquisa_arquivos",
        escopo="arquivos",
        valor={"descricao_humana": f"costuma procurar arquivos sobre {assunto}"},
        sinal=0.3,
        origem="pesquisa_semantica_arquivos",
        evidencia="busca explícita com resultado local confirmado",
        confirmado_usuario=False,
    ))


def aprender_conteudo_area_transferencia(
    conteudo: str,
    pedido: str,
    *,
    salvar_aprendizado: Callable[..., Any],
) -> bool:
    """Persiste somente conteúdo que o usuário mandou explicitamente aprender."""
    fato = re.sub(r"\s+", " ", str(conteudo or "")).strip()[:4000]
    if not fato:
        return False
    return bool(salvar_aprendizado(
        tipo="fato_usuario",
        gatilho=fato[:240],
        valor=fato,
        regra=f"O usuário ensinou explicitamente pela área de transferência: {fato}",
        texto_original=str(pedido or "")[:500],
        confianca=0.98,
        origem="area_transferencia_explicita",
        evidencia="pedido explícito do usuário para aprender conteúdo copiado",
        status="ativo",
        confirmado_usuario=True,
    ))


def observar_conteudo_area_transferencia(
    classificacao: Mapping[str, Any],
    *,
    registrar_evidencia: Callable[..., Any],
) -> bool:
    """Entrega evidências classificadas ao aprendizado gradual."""
    chave = str(classificacao.get("chave") or "").strip()
    descricao = str(classificacao.get("descricao") or "").strip()[:500]
    if not chave or not descricao:
        return False
    return bool(registrar_evidencia(
        chave=chave,
        tipo=str(classificacao.get("tipo") or "padrao_clipboard"),
        escopo=str(classificacao.get("escopo") or "area_transferencia"),
        valor={"descricao_humana": descricao, "origem": "area_transferencia"},
        sinal=float(classificacao.get("sinal") or 0.0),
        origem="observacao_area_transferencia",
        evidencia=str(classificacao.get("motivo") or "conteúdo classificado localmente"),
        confirmado_usuario=False,
    ))


def observar_item_caixa_entrada(
    item: Mapping[str, Any],
    *,
    registrar_evidencia: Callable[..., Any],
) -> None:
    """Aprende padrões agregados das notas, nunca o texto integral como fato."""
    for assunto in list(item.get("assuntos") or [])[:3]:
        assunto_limpo = str(assunto or "").strip().casefold()[:80]
        if not assunto_limpo:
            continue
        registrar_evidencia(
            chave=f"caixa_entrada:assunto:{assunto_limpo}",
            tipo="assunto_recorrente_caixa_entrada",
            escopo="caixa_entrada",
            valor={"descricao_humana": f"costuma anotar coisas sobre {assunto_limpo}"},
            sinal=0.4,
            origem="caixa_entrada_pessoal",
            evidencia=f"nova {str(item.get('tipo') or 'nota')} classificada nesse assunto",
            confirmado_usuario=False,
        )


def registrar_feedback_agenda(
    evento: str,
    dados: Mapping[str, Any] | None,
    *,
    registrar_evidencia: Callable[..., Any],
) -> None:
    """Converte o fluxo da agenda em sinais agregados, sem guardar lembretes."""
    evento_norm = str(evento or "").casefold().strip()
    sinais = {
        "aceitacao": 0.55,
        "correcao": 0.35,
        "repeticao": -0.15,
        "recusa": -0.55,
        "silencio_qualificado": -0.10,
        "correcao_necessaria": -0.20,
        "falha": -0.30,
    }
    if evento_norm not in sinais:
        return
    registrar_evidencia(
        chave=f"agenda:fluxo:{evento_norm}",
        tipo="feedback_habilidade_agenda",
        escopo="agenda",
        valor={
            "descricao_humana": f"feedback agregado da agenda: {evento_norm}",
            "intent": str((dados or {}).get("intent") or "AGENDAR_LEMBRETE")[:48],
        },
        sinal=sinais[evento_norm],
        origem="interacao_usuario_agenda",
        evidencia="resultado do fluxo canônico da agenda",
        confirmado_usuario=evento_norm in {"aceitacao", "recusa", "correcao"},
    )
