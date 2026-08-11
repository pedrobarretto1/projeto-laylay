"""Adaptadores pequenos que mantêm comportamento fora da raiz de composição."""

from __future__ import annotations

import os
import time
from typing import Any, Callable


def avaliar_evento_emocional_operacional(
    resultado: Any,
    *,
    avaliador: Any,
    definir_emocao: Callable[[str, int, str], Any],
    log: Callable[[str], Any] = print,
) -> dict[str, Any]:
    avaliacao = dict(avaliador.avaliar(resultado) or {})
    if avaliacao.get("permite_expressao"):
        definir_emocao(
            str(avaliacao.get("emocao") or "calma"),
            int(avaliacao.get("nivel") or 1),
            str(avaliacao.get("causa") or "evento operacional"),
        )
    log(
        "🎭 [EMOÇÃO:CAUSA] "
        f"responsabilidade={avaliacao.get('responsabilidade')} "
        f"confiança={float(avaliacao.get('confianca') or 0.0):.0%} "
        f"emoção={avaliacao.get('emocao')} nível={avaliacao.get('nivel')} "
        f"repetições={avaliacao.get('repeticoes')} "
        f"expressão={bool(avaliacao.get('permite_expressao'))} "
        f"motivo={avaliacao.get('motivo_expressao')}"
    )
    return avaliacao


def definir_atividade_visual(
    atividade: str,
    *,
    atualizar_estado: Callable[..., Any],
    clock: Callable[[], float] = time.time,
) -> None:
    atividade_segura = str(atividade or "idle")
    duracao = (
        0.0 if atividade_segura == "idle"
        else 12.0 if atividade_segura == "listening"
        else 15.0
    )
    atualizar_estado(
        visual_activity=atividade_segura,
        visual_activity_until=clock() + duracao,
    )


def publicar_curadoria_musical_cooperativa(
    resumo: dict[str, Any], *, publicar_getter: Callable[[], Any],
) -> bool:
    publicar = publicar_getter()
    if not callable(publicar):
        return False
    dados = dict(resumo or {})
    return bool(publicar(dados))


def descarregar_modelo_local(
    *, runtime_portatil: Any, modelo: str,
    descarregar_ollama: Callable[[str], bool],
) -> bool:
    if runtime_portatil.backend == "portatil":
        return bool(runtime_portatil.descarregar())
    return bool(descarregar_ollama(modelo))


def registrar_memoria_visual_integrada(
    imagem_b64: Any,
    descricao: Any,
    motivo: str = "captura manual",
    contexto: Any = "",
    emocao: str = "",
    intensidade: int = 1,
    tags: Any = None,
    origem: str = "pc_a",
    *,
    registrar_memoria: Callable[..., Any],
    registrar_evento_temporal: Callable[..., dict[str, Any]],
    estado_mental_getter: Callable[[], dict[str, Any]],
    atualizar_estado: Callable[..., Any],
    log: Callable[[str], Any] = print,
) -> Any:
    caminho = registrar_memoria(
        imagem_b64,
        descricao,
        motivo=motivo,
        contexto=contexto,
        emocao=emocao,
        intensidade=intensidade,
        tags=tags,
        origem=origem,
    )
    if caminho:
        try:
            temporal = registrar_evento_temporal(
                estado_mental_getter().get("consciencia_temporal"),
                str(descricao or ""),
                memoria_id=os.path.basename(str(caminho)),
                contexto=contexto if isinstance(contexto, dict) else {},
            )
            atualizar_estado(consciencia_temporal=temporal)
        except Exception as erro:
            log(
                "⚠️ [TEMPO:VISÃO] memória visual não entrou na linha do tempo: "
                f"{erro}"
            )
    return caminho


def salvar_identidade_usuario(
    nome: str,
    texto_original: str = "",
    *,
    persistir_nome: Callable[..., bool],
    atualizar_estado: Callable[..., Any],
    salvar_memoria: Callable[[], Any],
) -> bool:
    salvo = persistir_nome(nome, texto_original=texto_original)
    if salvo:
        atualizar_estado(nome_usuario=str(nome or "").strip())
        salvar_memoria()
    return bool(salvo)


def entregar_briefing_inicial(
    tipo: Any,
    texto: str,
    emocao: str = "calma",
    nivel: int = 1,
    *,
    entregar: Callable[..., Any],
    salvar_estado: Callable[..., Any],
) -> Any:
    return entregar(
        tipo, texto, emocao, nivel,
        adiar_se_interacao=True,
        ao_entrega_adiada=salvar_estado,
        detalhar=True,
    )


def observar_evento_pendencia_agenda(
    evento: str,
    pendencia: dict[str, Any],
    *,
    registrar_feedback: Callable[[str, dict[str, Any]], Any],
) -> None:
    if str((pendencia or {}).get("origem") or "") == "agenda" and str(evento or "") == "expirada":
        registrar_feedback("silencio_qualificado", {"intent": "AGENDAR_LEMBRETE"})


def agendar_entrada_canonica(
    texto: str,
    canal: str = "terminal",
    *,
    modo_jogo_ativo: Callable[[], bool],
    agendar: Callable[..., Any],
) -> Any:
    canal_normalizado = str(canal or "terminal").strip().casefold() or "terminal"
    # O Terminal 2 já possui contexto de jogo dentro da mente. Consultar o
    # lock do detector antes de sequer agendar a mensagem fazia a entrada do
    # desktop ficar presa enquanto uma transição de jogo descarregava a LLM.
    # A origem continua sendo desktop; o turno consulta o contexto atualizado
    # no lugar correto, sem bloquear a porta de entrada.
    origem = (
        "desktop"
        if canal_normalizado == "desktop"
        else "modo_jogo" if modo_jogo_ativo() else canal_normalizado
    )
    return agendar(texto, origem=origem)
