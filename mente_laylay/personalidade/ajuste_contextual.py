"""Ajustes leves de fala a partir do contexto vivo da Laylay."""

from __future__ import annotations

from collections.abc import Callable

from mente_laylay.cognicao.coerencia_temporal import ajustar_fala_ao_periodo
from mente_laylay.percepcao.ritmo_circadiano import adaptar_fala_ao_ritmo


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
    periodo = ctx["periodo"]
    texto_lower = str(texto_usuario or "").strip().lower()
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

    # Fora de saudações, não inventa observações sobre o relógio, mas corrige
    # contradições temporais objetivas em respostas prontas.
    fala = ajustar_fala_ao_periodo(fala, periodo)
    return adaptar_fala_ao_ritmo(fala, ctx.get("ritmo_temporal"))
