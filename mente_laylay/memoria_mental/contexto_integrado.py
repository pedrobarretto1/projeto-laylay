"""Leitura e resumo do contexto integrado da Laylay."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, Optional


def montar_contexto_perceptivo(
    *,
    periodo: str,
    agora: datetime,
    contexto_sistema: Dict[str, Any] | None = None,
    logs_navegador: list | None = None,
    current_emotion: str = "calma",
    emotion_level: int = 1,
    humor_level: int = 0,
    ultimo_topico_conversa: str = "",
    topicos_conversa_recente: list | None = None,
    rotina_atual: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    sistema = dict(contexto_sistema or {})
    logs = [str(x).strip() for x in (logs_navegador or [])[-5:] if str(x).strip()]
    return {
        "periodo": str(periodo or "").strip(),
        "hora_chave": agora.strftime("%H:00"),
        "exe": str(sistema.get("exe") or "").strip(),
        "title": str(sistema.get("title") or "").strip(),
        "assunto": str(sistema.get("assunto") or "").strip(),
        "logs_recentes": logs,
        "emocao": str(current_emotion or "calma").strip(),
        "nivel_emocao": int(emotion_level or 1),
        "humor": int(humor_level or 0),
        "topico_ativo": str(ultimo_topico_conversa or "").strip(),
        "topicos_recentes": list((topicos_conversa_recente or [])[-5:]),
        "rotina_atual": dict(rotina_atual or {}),
    }


def resumo_contexto_perceptivo_para_prompt(ctx: Dict[str, Any], percepcao: Dict[str, Any] | None = None) -> str:
    ctx = dict(ctx or {})
    percepcao = dict(percepcao or {})
    linhas = [
        "--- CONTEXTO PERCEPTIVO ---",
        f"Periodo atual: {ctx.get('periodo') or ''} ({ctx.get('hora_chave') or ''})",
    ]
    if ctx.get("exe") or ctx.get("title") or ctx.get("assunto"):
        linhas.append(
            "Sistema ativo: "
            f"exe={ctx.get('exe') or 'desconhecido'} | "
            f"janela={ctx.get('title') or 'indefinida'} | "
            f"assunto={ctx.get('assunto') or 'indefinido'}"
        )
    logs_recentes = ctx.get("logs_recentes") or []
    if logs_recentes:
        linhas.append("Sinais recentes: " + " | ".join(map(str, logs_recentes[-3:])))
    if ctx.get("topico_ativo"):
        linhas.append(f"Topico ativo: {ctx.get('topico_ativo')}")
    topicos = ctx.get("topicos_recentes") or []
    if topicos:
        linhas.append("Topicos recentes: " + "; ".join(map(str, topicos)))
    rotina = ctx.get("rotina_atual") or {}
    if isinstance(rotina, dict) and rotina:
        partes = []
        janelas = rotina.get("janelas") or []
        assuntos = rotina.get("assuntos") or []
        if janelas:
            partes.append("janelas=" + ", ".join(map(str, janelas[-3:])))
        if assuntos:
            partes.append("assuntos=" + ", ".join(map(str, assuntos[-3:])))
        if partes:
            linhas.append("Rotina aprendida neste horario: " + " | ".join(partes))
    if percepcao:
        linhas.append(
            "Leitura contextual: "
            f"conclusao={percepcao.get('conclusao')} | confianca={percepcao.get('confianca')} | "
            f"sinais={', '.join((percepcao.get('observacoes') or [])[:4])}"
        )
        linhas.append("Interpretacao: " + str(percepcao.get("interpretacao") or ""))
    linhas.append(
        f"Estado interno: emocao={ctx.get('emocao')} nivel={ctx.get('nivel_emocao')} humor={ctx.get('humor')}"
    )
    return "\n".join(linhas)


def resumo_mente_integrada_para_prompt(
    *,
    ctx: Dict[str, Any],
    percepcao: Dict[str, Any] | None,
    mente: Dict[str, Any] | None,
    auto_resumo: str = "",
    aprendizados: str = "",
    memoria_quente: str = "",
    topicos_prompt: str = "",
) -> str:
    ctx = dict(ctx or {})
    mente = dict(mente or {})
    percepcao = dict(percepcao or {})
    blocos = ["--- MENTE INTEGRADA ---"]

    blocos.append(
        "Estado atual: "
        f"periodo={ctx.get('periodo')} | "
        f"emocao={ctx.get('emocao')}({ctx.get('nivel_emocao')}) | "
        f"humor={ctx.get('humor')}"
    )
    if ctx.get("exe") or ctx.get("title") or ctx.get("assunto"):
        blocos.append(
            "Contexto vivo: "
            f"app={ctx.get('exe') or 'desconhecido'} | "
            f"janela={ctx.get('title') or 'indefinida'} | "
            f"assunto={ctx.get('assunto') or 'indefinido'}"
        )
    logs_recentes = ctx.get("logs_recentes") or []
    if logs_recentes:
        blocos.append("Sinais recentes: " + " | ".join(map(str, logs_recentes[-3:])))
    if ctx.get("topico_ativo"):
        blocos.append(f"Topico ativo: {ctx.get('topico_ativo')}")
    rotina = ctx.get("rotina_atual") or {}
    if isinstance(rotina, dict) and rotina:
        partes = []
        janelas = rotina.get("janelas") or []
        assuntos = rotina.get("assuntos") or []
        if janelas:
            partes.append("janelas=" + ", ".join(map(str, janelas[-3:])))
        if assuntos:
            partes.append("assuntos=" + ", ".join(map(str, assuntos[-3:])))
        if partes:
            blocos.append("Rotina aprendida: " + " | ".join(partes))
    if percepcao:
        blocos.append(
            "Percepcao contextual: "
            f"conclusao={percepcao.get('conclusao')} | confianca={percepcao.get('confianca')} | "
            f"observacoes={'; '.join((percepcao.get('observacoes') or [])[:4])}"
        )
        blocos.append("Leitura da mente: " + str(percepcao.get("interpretacao") or ""))

    if mente.get("ultima_intencao") or mente.get("ultimo_alvo") or mente.get("ultima_habilidade"):
        partes = []
        if mente.get("ultima_habilidade"):
            partes.append(f"habilidade={mente.get('ultima_habilidade')}")
        if mente.get("ultima_intencao"):
            partes.append(f"intencao={mente.get('ultima_intencao')}")
        if mente.get("ultimo_alvo"):
            partes.append(f"alvo={mente.get('ultimo_alvo')}")
        if mente.get("ultimo_escopo"):
            partes.append(f"escopo={mente.get('ultimo_escopo')}")
        if partes:
            blocos.append("Memoria curta da mente: " + " | ".join(partes))

    if mente.get("ultimas_entradas"):
        blocos.append("Entradas recentes: " + " || ".join(map(str, mente.get("ultimas_entradas")[-3:])))
    if mente.get("pergunta_aberta_texto"):
        partes_pergunta = [f"pergunta={mente.get('pergunta_aberta_texto')}"]
        if mente.get("pergunta_aberta_topico"):
            partes_pergunta.append(f"topico={mente.get('pergunta_aberta_topico')}")
        if mente.get("pergunta_aberta_origem"):
            partes_pergunta.append(f"origem={mente.get('pergunta_aberta_origem')}")
        blocos.append("Pergunta aberta pendente: " + " | ".join(map(str, partes_pergunta)))
    if mente.get("ultima_acao_intent"):
        blocos.append(
            "Ultima acao real: "
            f"intent={mente.get('ultima_acao_intent')} | "
            f"status={mente.get('ultima_acao_status') or 'desconhecido'} | "
            f"reexecutavel={bool(mente.get('ultima_acao_reexecutavel'))}"
        )

    for extra in [auto_resumo, aprendizados, memoria_quente, topicos_prompt]:
        extra = str(extra or "").strip()
        if extra:
            blocos.append(extra)

    blocos.append(
        "Regra interna: nenhuma peça isolada deve decidir sozinha quando houver "
        "mais sinais disponíveis. Cruzar memoria, contexto, emocao, rotina, percepcao contextual e memoria curta da mente antes de responder."
    )
    return "\n".join(blocos)


def contexto_aponta_descanso(ctx: Dict[str, Any], percepcao: Dict[str, Any] | None = None, texto_extra: str = "") -> bool:
    """Decide se o contexto atual pede modo descanso em vez de iniciativa."""
    ctx = dict(ctx or {})
    percepcao = dict(percepcao or {})
    texto_extra = str(texto_extra or "").strip().lower()
    amostra = " ".join([
        str(ctx.get("assunto") or ""),
        str(ctx.get("title") or ""),
        " ".join(ctx.get("logs_recentes") or []),
        str(ctx.get("topico_ativo") or ""),
        texto_extra,
    ]).lower()
    sinais_descanso = ["sono", "cansad", "dorm", "descans", "boa noite", "madrugada", "sleep", "apagar"]
    sinais_foco = ["codigo", "código", "program", "vs code", "vscode", "debug", "trabalho", "estudo", "foco"]

    if percepcao.get("conclusao") == "descanso" and int(percepcao.get("confianca") or 0) >= 1:
        return True
    if percepcao.get("conclusao") in {"foco", "musica", "pesquisa", "organizacao", "inicio_dia"}:
        return False
    if any(s in amostra for s in sinais_descanso):
        return True
    if ctx.get("periodo") in {"madrugada", "noite"} and not any(s in amostra for s in sinais_foco):
        return True
    return False


def montar_resumo_mente_integrada_com_extras(
    *,
    texto_usuario: str = "",
    ctx: Dict[str, Any],
    percepcao: Dict[str, Any] | None,
    mente: Dict[str, Any] | None,
    resumo_autoaprimoramento_cb: Callable[..., str] | None = None,
    memoria_sqlite: Any = None,
) -> str:
    """Agrupa memoria, percepcao, emocao, humor e rotina num unico retrato."""
    texto_base = str(texto_usuario or "").strip()
    auto_resumo = ""
    aprendizados = ""
    memoria_quente = ""
    topicos_prompt = ""
    try:
        if callable(resumo_autoaprimoramento_cb):
            auto_resumo = resumo_autoaprimoramento_cb(limit=4)
    except Exception:
        pass

    try:
        if texto_base and memoria_sqlite is not None:
            aprendizados = memoria_sqlite.formatar_aprendizados_relevantes_para_prompt(texto_base, limit=4)
    except Exception:
        pass

    try:
        if memoria_sqlite is not None:
            memoria_quente = memoria_sqlite.formatar_memoria_quente_para_prompt(limit=4, max_chars=800)
    except Exception:
        pass

    try:
        if memoria_sqlite is not None:
            topicos_prompt = memoria_sqlite.formatar_topicos_conversa_para_prompt(limit=4)
    except Exception:
        pass

    return resumo_mente_integrada_para_prompt(
        ctx=ctx,
        percepcao=percepcao,
        mente=mente,
        auto_resumo=auto_resumo,
        aprendizados=aprendizados,
        memoria_quente=memoria_quente,
        topicos_prompt=topicos_prompt,
    )


def interpretar_contexto_vivo(
    ctx: Optional[Dict[str, Any]] = None,
    texto_extra: str = "",
    normalizar_cb: Optional[Callable[[str], str]] = None,
) -> Dict[str, Any]:
    ctx = ctx if isinstance(ctx, dict) else {}
    texto_extra = str(texto_extra or "").strip()
    normalizar = normalizar_cb or (lambda s: str(s or "").lower())

    partes = [
        str(ctx.get("exe") or ""),
        str(ctx.get("title") or ""),
        str(ctx.get("assunto") or ""),
        " ".join(ctx.get("logs_recentes") or []),
        str(ctx.get("topico_ativo") or ""),
        " ".join(ctx.get("topicos_recentes") or []),
        texto_extra,
    ]
    base = normalizar(" ".join(partes))
    periodo = str(ctx.get("periodo") or "").strip()
    emocao = str(ctx.get("emocao") or "").strip()
    humor = int(ctx.get("humor") or 0)

    sinais = {
        "descanso": 0,
        "foco": 0,
        "musica": 0,
        "inicio_dia": 0,
        "conversa": 0,
        "pesquisa": 0,
        "organizacao": 0,
    }
    evidencias = {k: [] for k in sinais}

    def marcar(chave: str, peso: int, motivo: str) -> None:
        if chave not in sinais or peso == 0:
            return
        sinais[chave] += int(peso)
        evidencias[chave].append(str(motivo))

    def texto_tem(*fragmentos: str) -> bool:
        return any(f and f in base for f in fragmentos)

    if periodo in {"noite", "madrugada"}:
        marcar("descanso", 1, f"periodo={periodo}")
    if periodo == "manha":
        marcar("inicio_dia", 1, "periodo=manha")
    if periodo == "tarde":
        marcar("conversa", 1, "periodo=tarde")

    if texto_tem("sono", "cansad", "dorm", "descans", "boa noite", "sleep", "apagar"):
        marcar("descanso", 4, "texto sugere cansaço ou pausa")
    if texto_tem("codigo", "código", "program", "vscode", "vs code", "debug", "compilar", "editar", "terminal"):
        marcar("foco", 4, "texto sugere trabalho focado")
    if texto_tem("playlist", "musica", "música", "spotify", "youtube music", "som", "toca", "play"):
        marcar("musica", 4, "texto sugere atividade musical")
    if texto_tem("acord", "bom dia", "acordei", "começando", "iniciando", "manh"):
        marcar("inicio_dia", 4, "texto sugere começo do dia")
    if texto_tem("organiza", "arruma", "fechar programa", "fechar app", "limpar", "bloquear", "desligar"):
        marcar("organizacao", 3, "texto sugere organização do ambiente")
    if "?" in texto_extra or texto_tem("como", "por que", "porque", "o que", "qual", "me fala", "me diz"):
        marcar("conversa", 2, "texto pede explicação ou conversa")
    if texto_tem("pesquis", "buscar", "procur", "google", "internet", "resultado"):
        marcar("pesquisa", 3, "texto sugere busca")

    exe = str(ctx.get("exe") or "").lower()
    title = str(ctx.get("title") or "").lower()
    assunto = str(ctx.get("assunto") or "").lower()

    if any(x in exe or x in title or x in assunto for x in ["code", "vscode", "pycharm", "sublime", "terminal"]):
        marcar("foco", 3, "janela ativa sugere estudo ou programação")
    if any(x in exe or x in title or x in assunto for x in ["youtube", "music", "spotify", "player", "playlist", "audio"]):
        marcar("musica", 3, "janela ativa sugere mídia ou música")
    if any(x in exe or x in title or x in assunto for x in ["chrome", "google", "search", "pesquisa"]):
        marcar("pesquisa", 2, "janela ativa sugere navegação ou busca")

    rotina_atual = ctx.get("rotina_atual") or {}
    if isinstance(rotina_atual, dict) and rotina_atual:
        janelas = [str(x).lower() for x in (rotina_atual.get("janelas") or []) if str(x).strip()]
        assuntos = [str(x).lower() for x in (rotina_atual.get("assuntos") or []) if str(x).strip()]
        rotina_txt = " ".join(janelas + assuntos)
        if any(x in rotina_txt for x in ["sleep", "sono", "dorm", "descans", "noite"]):
            marcar("descanso", 2, "rotina aprendida aponta descanso")
        if any(x in rotina_txt for x in ["code", "vscode", "program", "terminal", "debug"]):
            marcar("foco", 2, "rotina aprendida aponta foco")
        if any(x in rotina_txt for x in ["youtube", "spotify", "playlist", "music", "música"]):
            marcar("musica", 2, "rotina aprendida aponta música")

    if emocao in {"cansada", "triste"}:
        marcar("descanso", 2, f"emocao={emocao}")
    if emocao in {"alegre", "envergonhada"}:
        marcar("conversa", 1, f"emocao={emocao}")
    if emocao == "brava":
        marcar("organizacao", 1, "emocao=brava pede objetividade")

    if humor <= -3:
        marcar("descanso", 1, f"humor={humor}")
    elif humor >= 3:
        marcar("conversa", 1, f"humor={humor}")

    ordem = ["descanso", "foco", "musica", "inicio_dia", "conversa", "pesquisa", "organizacao"]
    lider = max(ordem, key=lambda k: (sinais.get(k, 0), -ordem.index(k)))
    valor_lider = int(sinais.get(lider, 0))
    segundo = sorted(sinais.values(), reverse=True)[1] if len(sinais) > 1 else 0
    confianca = max(0, valor_lider - int(segundo))

    if valor_lider <= 0:
        lider = "neutro"
        interpretacao = "A percepção ainda está ambígua; a hora existe, mas não domina o cenário."
    else:
        evid = evidencias.get(lider) or []
        evid_txt = "; ".join(evid[:3]) if evid else "sem evidências fortes"
        interpretacao = f"A leitura favorece {lider} porque {evid_txt}."

    observacoes = [f"{chave}={sinais[chave]}" for chave in ordem if sinais.get(chave, 0) > 0]
    if not observacoes:
        observacoes.append("sinais insuficientes")

    return {
        "sinais": sinais,
        "evidencias": evidencias,
        "lider": lider,
        "confianca": confianca,
        "observacoes": observacoes,
        "interpretacao": interpretacao,
        "conclusao": lider,
    }
