"""Ajustes leves de fala a partir do contexto vivo da Laylay."""

from __future__ import annotations

from collections.abc import Callable


def ajustar_fala_por_horario(
    fala: str,
    texto_usuario: str = "",
    *,
    obter_contexto_perceptivo: Callable[[], dict],
    interpretar_contexto_vivo: Callable[[dict, str], dict],
    escolher_fala: Callable[[list[str]], str],
) -> str:
    """Ajusta saudações e observações leves para combinar com o contexto atual."""
    fala = str(fala or "").strip()
    if not fala:
        return fala

    ctx = obter_contexto_perceptivo()
    percepcao = interpretar_contexto_vivo(ctx, texto_usuario)
    periodo = ctx["periodo"]
    texto_lower = str(texto_usuario or "").strip().lower()
    fala_lower = fala.lower()
    contexto_gatilho = " ".join(
        [
            ctx["assunto"],
            ctx["title"],
            " ".join(ctx["logs_recentes"]),
            ctx["topico_ativo"],
            " ".join(ctx["topicos_recentes"]),
        ]
    ).lower()
    contexto_descanso = any(k in contexto_gatilho for k in ["sono", "cansad", "dorm", "descans", "noite", "madrugada", "sleep"])
    contexto_foco = any(k in contexto_gatilho for k in ["codigo", "código", "program", "vs code", "vscode", "debug", "estudo", "trabalho", "foco"])
    contexto_musica = any(k in contexto_gatilho for k in ["musica", "música", "spotify", "youtube", "playlist", "som"])
    contexto_inicio_dia = any(k in contexto_gatilho for k in ["acord", "manh", "bom dia", "começando", "inicio do dia", "iniciando"])

    if "bom dia" in texto_lower:
        if contexto_descanso and periodo in {"madrugada", "noite"}:
            return escolher_fala([
                "Bom dia, Pedro. Mas esse corpo aí tá pedindo descanso, não cumprimento.",
                "Bom dia meio torto, Pedro. Parece que teu corpo ainda tá em modo descanso.",
                "Bom dia, mas teu contexto tá pedindo cama, não café.",
            ])
        if contexto_inicio_dia or periodo == "manha":
            return escolher_fala([
                "Bom dia, Pedro. Bora aproveitar a manhã.",
                "Bom dia, Pedro. Hora de fazer o dia acontecer.",
                "Bom dia. Vamos começar essa manhã direito.",
            ])
        if periodo == "madrugada":
            return escolher_fala([
                "Boa madrugada, Pedro. Ainda tá cedo demais até pra fingir que é dia.",
                "Boa madrugada. O relógio tá claramente fora de hora pra bom dia.",
                "Madrugada, Pedro. Isso aí ainda não virou manhã.",
            ])
        if periodo == "tarde":
            return escolher_fala([
                "Boa tarde, Pedro. Meio atrasado, mas valeu a intenção.",
                "Boa tarde. Chegou com um pequeno atraso, mas chegou.",
                "Boa tarde, Pedro. Essa saudação veio no timing caprichado demais.",
            ])
        return escolher_fala([
            "Boa noite, Pedro. Esse bom dia veio meio perdido, mas eu aceito.",
            "Boa noite, Pedro. Esse bom dia tropeçou no relógio.",
            "Boa noite. Esse cumprimento veio atravessado, mas tudo bem.",
        ])

    if "boa tarde" in texto_lower:
        if contexto_descanso and periodo == "madrugada":
            return escolher_fala([
                "Boa madrugada, Pedro. Essa tarde aí tá sonhando alto.",
                "Madrugada, Pedro. Essa tarde ainda não foi autorizada.",
                "Tá de madrugada, mas a saudação veio de tarde.",
            ])
        if periodo == "manha":
            return escolher_fala([
                "Bom dia ainda, Pedro. A tarde tá adiantada demais.",
                "Ainda é manhã, Pedro. Essa tarde chegou cedo demais.",
                "Bom dia, porque a tarde ainda nem acordou.",
            ])
        if contexto_inicio_dia:
            return escolher_fala([
                "Ainda tá com cara de começo de dia, Pedro. Tarde nenhuma decidiu chegar de verdade.",
                "O dia ainda tá começando, então essa tarde tá meio fictícia.",
                "Isso aí ainda tá com energia de manhã, não de tarde.",
            ])
        if periodo == "noite":
            return escolher_fala([
                "Boa noite, Pedro. Essa tarde já foi embora faz tempo.",
                "Boa noite. A tarde já encerrou o expediente.",
                "Noite, Pedro. A tarde já foi dormir.",
            ])
        return escolher_fala([
            "Boa tarde, Pedro.",
            "Boa tarde. Tô por aqui.",
            "Boa tarde, Pedro. Pode falar.",
        ])

    if "boa noite" in texto_lower:
        if contexto_descanso:
            return escolher_fala([
                "Boa noite, Pedro. Acho que o contexto já tá me dizendo pra baixar o ritmo.",
                "Boa noite. O contexto já pediu modo baixo.",
                "Noite, Pedro. Vou reduzir o volume do papo.",
            ])
        if periodo == "manha":
            return escolher_fala([
                "Bom dia, Pedro. Essa boa noite tá bem adiantada.",
                "Bom dia. A boa noite veio cedo demais.",
                "Pedro, isso ainda é manhã. A noite tá chutando a porta cedo.",
            ])
        if periodo == "tarde":
            return escolher_fala([
                "Ainda é tarde, Pedro. A noite tá chegando, mas não chegou.",
                "Tarde ainda, Pedro. A noite tá só ensaiando.",
                "A noite tá vindo, mas ainda não estacionou.",
            ])
        if periodo == "madrugada":
            return escolher_fala([
                "Boa madrugada, Pedro. Esse boa noite já virou plantão.",
                "Boa madrugada. O boa noite já entrou em turno extra.",
                "Madrugada, Pedro. Esse cumprimento já tá fazendo hora extra.",
            ])
        return escolher_fala([
            "Boa noite, Pedro.",
            "Boa noite. Tô por aqui.",
            "Boa noite, Pedro. Pode falar.",
        ])

    if periodo == "madrugada" and any(k in fala_lower for k in ["bom dia", "boa tarde", "horario de dia", "dia lindo"]):
        return "Pedro, isso aí tá com energia de madrugada. Melhor falar de café do que de bom dia."

    if periodo == "madrugada" and len(texto_lower.split()) <= 5 and any(k in texto_lower for k in ["vamos", "abrir", "começar", "fazer"]):
        return fala + " E no relógio? Já é madrugada, então vou ser objetiva."

    if contexto_descanso and "?" in fala and len(fala) < 90:
        return fala.rstrip(" .") + " E, sinceramente, esse contexto tá com cara de pausa."

    if contexto_foco and len(fala) < 90 and any(k in fala_lower for k in ["vamos", "começar", "seguir", "fazer", "continuar", "partir"]):
        return fala.rstrip(" .") + " Vamos no ritmo certo e sem meias distrações."

    fala_ou_texto_musical = any(
        k in (fala_lower + " " + texto_lower)
        for k in ["musica", "música", "playlist", "faixa", "som", "trilha", "youtube"]
    )
    if contexto_musica and fala_ou_texto_musical and len(fala) < 90 and any(k in fala_lower for k in ["tranquilo", "calma", "boa", "certo", "presente"]):
        return fala.rstrip(" .") + " Deixo isso no tom da trilha que você tá vivendo."

    if percepcao.get("conclusao") == "foco" and "?" not in fala and len(fala) < 100:
        if any(k in fala_lower for k in ["calma", "descansa", "devagar", "sem pressa"]):
            return fala.rstrip(" .") + " O contexto tá puxando mais pra foco do que pra pausa."
    if percepcao.get("conclusao") == "musica" and len(fala) < 100:
        if any(k in fala_lower for k in ["abrindo", "pronto", "beleza", "certo"]):
            return fala.rstrip(" .") + " Seu contexto musical tá bem claro pra mim agora."

    return fala
