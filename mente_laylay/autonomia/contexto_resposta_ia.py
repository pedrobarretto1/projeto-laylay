"""Montagem de contexto e prompt para a resposta da IA da Laylay."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def montar_prompt_contextual_legado(
    base_system_prompt: str,
    contexto: Dict[str, Any] | None,
    resumo_conversa: str = "",
    historico_long_term: str = "",
) -> str:
    """Preserva o montador antigo sem competir com o fluxo ativo de prompt."""
    ctx = contexto if isinstance(contexto, dict) else {}
    base = [str(base_system_prompt or "")]
    base.append(
        "ESTADO MENTAL COMPARTILHADO: "
        f"periodo={ctx.get('periodo') or 'indefinido'} | "
        f"emocao={ctx.get('emocao') or 'calma'}({ctx.get('nivel_emocao') or 1}) | "
        f"humor={ctx.get('humor', 0)} | "
        f"topico={ctx.get('topico_ativo') or 'nenhum'}"
    )
    if ctx.get("exe") or ctx.get("title") or ctx.get("assunto"):
        base.append(
            "CONTEXTO VIVO: "
            f"app={ctx.get('exe') or 'desconhecido'} | "
            f"janela={ctx.get('title') or 'indefinida'} | "
            f"assunto={ctx.get('assunto') or 'indefinido'}"
        )
    logs_recentes = ctx.get("logs_recentes")
    if isinstance(logs_recentes, list) and logs_recentes:
        base.append("SINAIS RECENTES: " + " | ".join(map(str, logs_recentes[-3:])))
    rotina_atual = ctx.get("rotina_atual")
    if isinstance(rotina_atual, dict) and rotina_atual:
        janelas = rotina_atual.get("janelas") or []
        assuntos = rotina_atual.get("assuntos") or []
        partes = []
        if janelas:
            partes.append("janelas=" + ", ".join(map(str, janelas[-3:])))
        if assuntos:
            partes.append("assuntos=" + ", ".join(map(str, assuntos[-3:])))
        if partes:
            base.append("ROTINA DO HORARIO: " + " | ".join(partes))
    if resumo_conversa:
        base.append(f"RESUMO CURTO: {resumo_conversa}")
    if historico_long_term:
        base.append(f"HISTORICO LONGO: {historico_long_term}")
    return "\n".join(base)


def preparar_contexto_resposta_ia(
    ctx: Dict[str, Any],
    texto: str,
    mensagens: List[Dict[str, Any]],
    humor_level: int,
    base_system_prompt: str,
) -> Tuple[List[Dict[str, Any]], str]:
    t = str(texto or "").strip()
    mensagens = list(mensagens or [])

    memoria_sqlite = _get(ctx, "memoria_sqlite")
    aba_titulo_atual = str(_get(ctx, "aba_titulo_atual", "") or "")
    aba_url_atual = str(_get(ctx, "aba_url_atual", "") or "")
    current_emotion = str(_get(ctx, "current_emotion", "calma") or "")
    get_status_humor_prompt = _get(ctx, "get_status_humor_prompt")
    resumo_mente_integrada_para_prompt = _get(ctx, "_resumo_mente_integrada_para_prompt")
    retrato_mente_integrada = str(_get(ctx, "retrato_mente_integrada", "") or "").strip()
    formatar_playlists_para_prompt = _get(ctx, "_formatar_playlists_para_prompt")

    contaminantes = ["adicionar_a_playlist", "editar_playlist", "tocar_playlist", "organizar_desktop", "maximize_window", "persona"]

    def _contaminada(msg: dict) -> bool:
        if msg.get("role") not in ("assistant", "user"):
            return False
        c = str(msg.get("content", ""))
        if msg.get("role") == "user" and not c.startswith("System:"):
            return False
        return any(tok in c for tok in contaminantes)

    mensagens = [m for m in mensagens if not _contaminada(m)]

    contexto_extra = (
        f"\n\n--- CONTEXTO ATUAL ---\n"
        f"Aba Atual: {aba_titulo_atual}\n"
        f"URL Atual: {aba_url_atual}\n"
    )

    try:
        if callable(formatar_playlists_para_prompt):
            playlists_txt = formatar_playlists_para_prompt()
            if playlists_txt:
                contexto_extra += f"Playlists Disponíveis: {playlists_txt}\n"
    except Exception:
        pass

    try:
        if memoria_sqlite is not None:
            memorias_relevantes = memoria_sqlite.formatar_aprendizados_relevantes_para_prompt(t, limit=5)
            if memorias_relevantes:
                contexto_extra += "\n" + memorias_relevantes + "\n"
    except Exception:
        pass

    try:
        if memoria_sqlite is not None:
            memoria_quente = memoria_sqlite.formatar_memoria_quente_para_prompt(limit=6, max_chars=1200)
            if memoria_quente:
                contexto_extra += "\n" + memoria_quente + "\n"
    except Exception:
        pass

    try:
        if memoria_sqlite is not None:
            topicos_prompt = memoria_sqlite.formatar_topicos_conversa_para_prompt(limit=5)
            if topicos_prompt:
                contexto_extra += "\n" + topicos_prompt + "\n"
    except Exception:
        pass

    if retrato_mente_integrada:
        contexto_extra += "\n" + retrato_mente_integrada + "\n"
    else:
        try:
            if callable(resumo_mente_integrada_para_prompt):
                mente_unica = resumo_mente_integrada_para_prompt(t)
                if mente_unica:
                    contexto_extra += "\n" + mente_unica + "\n"
        except Exception:
            pass

    liberdade_conversacional = (
        "\n\n--- LIBERDADE CONVERSACIONAL ---\n"
        "Quando o usuário estiver conversando, responda como Laylay de forma viva, espontânea e contextual. "
        "Você pode opinar, brincar, discordar de leve, fazer uma leitura pessoal e puxar assunto sem pedir confirmação a cada frase. "
        "Peça mais contexto apenas quando a resposta depender de uma informação essencial; se der para responder com uma hipótese honesta, responda. "
        "Não trate opinião, brincadeira, gosto, recomendação conceitual ou papo aberto como comando técnico. "
        "Use frases como 'eu acho', 'eu iria por esse caminho', 'isso me soa como...' quando couber. "
        "A validação rígida vale para executar ações no PC; a conversa pode respirar e ter iniciativa.\n"
    )

    prompt_com_contexto = base_system_prompt + liberdade_conversacional + contexto_extra

    try:
        if memoria_sqlite is not None:
            memoria_resumida = memoria_sqlite.formatar_memoria_para_prompt()
            if memoria_resumida:
                prompt_com_contexto = prompt_com_contexto + "\n\n" + memoria_resumida
    except Exception:
        pass

    try:
        if callable(get_status_humor_prompt):
            status_humor = get_status_humor_prompt()
            prompt_com_humor = prompt_com_contexto.replace("{status_humor}", status_humor).replace("{humor_level}", str(humor_level))
        else:
            prompt_com_humor = prompt_com_contexto
    except Exception:
        prompt_com_humor = prompt_com_contexto

    if not mensagens:
        mensagens.append({"role": "system", "content": prompt_com_humor})
    else:
        if mensagens[0].get("role") == "system":
            mensagens[0]["content"] = prompt_com_humor
        else:
            mensagens.insert(0, {"role": "system", "content": prompt_com_humor})

    return mensagens, prompt_com_humor


class ContextoPromptRuntime:
    """Prepara o prompt ativo usando o retrato vivo da mesma mente."""

    def __init__(
        self,
        *,
        memoria_sqlite: Any,
        resumo_mente_integrada: Callable[[str], str],
        formatar_playlists: Callable[[], str],
        get_status_humor_prompt: Callable[[], str],
        base_system_prompt: str,
        estado_getter: Callable[[], Dict[str, Any]],
    ) -> None:
        self.memoria_sqlite = memoria_sqlite
        self.resumo_mente_integrada = resumo_mente_integrada
        self.formatar_playlists = formatar_playlists
        self.get_status_humor_prompt = get_status_humor_prompt
        self.base_system_prompt = str(base_system_prompt or "")
        self.estado_getter = estado_getter

    def preparar(self, texto: str) -> Tuple[List[Dict[str, Any]], str]:
        try:
            estado = self.estado_getter() or {}
        except Exception:
            estado = {}
        estado = estado if isinstance(estado, dict) else {}
        t = str(texto or "").strip()
        retrato = self.resumo_mente_integrada(t)
        contexto = {
            "memoria_sqlite": self.memoria_sqlite,
            "retrato_mente_integrada": retrato,
            "_resumo_mente_integrada_para_prompt": self.resumo_mente_integrada,
            "aba_titulo_atual": estado.get("aba_titulo_atual", ""),
            "aba_url_atual": estado.get("aba_url_atual", ""),
            "_formatar_playlists_para_prompt": self.formatar_playlists,
            "get_status_humor_prompt": self.get_status_humor_prompt,
        }
        return preparar_contexto_resposta_ia(
            contexto,
            t,
            estado.get("messages") or [],
            estado.get("humor_level", 0),
            self.base_system_prompt,
        )


def criar_contexto_prompt_runtime(**kwargs: Any) -> ContextoPromptRuntime:
    return ContextoPromptRuntime(**kwargs)
