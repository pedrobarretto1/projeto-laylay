"""Orquestracao de criacao e administracao da agenda da Laylay."""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.autonomia.agendamento_mental import (
    descrever_intencao_agendada,
    resolver_instante_lembrete,
    resolver_referencia_contextual_lembrete,
)
from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_comum import falar_ctx as _falar
from mente_laylay.personalidade.falas_variadas import escolher as escolher_fala_variada


INTENCOES_AGENDA = frozenset({
    "AGENDAR_ACAO", "AGENDAR_LEMBRETE", "LISTAR_AGENDAMENTOS", "CANCELAR_AGENDAMENTO",
})


@dataclass(frozen=True, slots=True)
class DependenciasExecutorAgenda:
    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _transacionar(ctx: Dict[str, Any], mutador: Callable[[list], Any]) -> bool:
    transacionar = _get(ctx, "_agendamentos_transacionar")
    if callable(transacionar):
        return bool(transacionar(mutador))
    carregar = _get(ctx, "_agendamentos_load")
    salvar = _get(ctx, "_agendamentos_save")
    lista = carregar() if callable(carregar) else []
    mutador(lista)
    return bool(salvar(lista)) if callable(salvar) else False


def _registrar_mente(ctx: Dict[str, Any], texto: str, resposta: str, intent: str, alvo: str, escopo: str) -> None:
    registrar = _get(ctx, "_registrar_mente_curta")
    if callable(registrar):
        registrar(texto, resposta, intent, alvo, escopo, "agenda")


def _registrar_feedback(ctx: Dict[str, Any], evento: str, **dados: Any) -> None:
    callback = _get(ctx, "_registrar_feedback_agenda")
    if callable(callback):
        callback(evento, dados)


def _publicar_cooperacao(ctx: Dict[str, Any], operacao: str, *, alvo: str, confirmado: bool) -> None:
    callback = _get(ctx, "_publicar_evento_agenda_cooperativo")
    if callable(callback):
        callback(operacao, alvo=alvo, confirmado=bool(confirmado))


def _agendar_acao(
    params: Dict[str, Any], texto: str, ctx: Dict[str, Any], deps: DependenciasExecutorAgenda,
) -> ResultadoDespacho:
    acao = params.get("acao_agendada")
    if not isinstance(acao, dict) or not str(acao.get("intent") or "").strip():
        _falar(ctx, "Eu peguei o horário, mas não consegui separar qual ação deveria executar.")
        return ResultadoDespacho.concluido()

    agora = dt.datetime.now()
    atraso = params.get("atraso_segundos")
    segundos = params.get("segundos")
    if atraso is None and segundos is not None:
        atraso = segundos
    hora_alvo = str(params.get("hora_alvo") or "").strip()
    try:
        minutos = params.get("minutos")
        horas = params.get("horas")
        if atraso is None and minutos is not None:
            atraso = int(minutos) * 60
        if atraso is None and horas is not None:
            atraso = int(horas) * 3600
        if atraso is not None:
            atraso_int = max(1, int(atraso))
            ts_exec = agora.timestamp() + atraso_int
            if atraso_int % 3600 == 0:
                tempo_txt = f"daqui {atraso_int // 3600} hora(s)"
            elif atraso_int % 60 == 0:
                tempo_txt = f"daqui {atraso_int // 60} minuto(s)"
            else:
                tempo_txt = f"daqui {atraso_int} segundo(s)"
        elif hora_alvo:
            hora, minuto = map(int, hora_alvo.split(":"))
            instante = agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
            if instante <= agora:
                instante += dt.timedelta(days=1)
            ts_exec = instante.timestamp()
            tempo_txt = f"às {hora_alvo}"
        else:
            raise ValueError("prazo ausente")
    except Exception:
        _falar(ctx, "Não consegui entender quando essa ação deve acontecer.")
        return ResultadoDespacho.concluido()

    intent_real = str(acao.get("intent") or "").upper().strip()
    params_reais = dict(acao.get("params") or {})
    alvo = str(
        params_reais.get("alvo") or params_reais.get("nome_app")
        or params_reais.get("nome_playlist") or params_reais.get("query") or "a ação"
    ).strip()
    descricao = descrever_intencao_agendada({"intent": intent_real, "params": params_reais})
    novo: Dict[str, Any] = {
        "id": str(uuid.uuid4())[:8], "tipo": "once", "ts_execucao": ts_exec,
        "descricao": descricao, "nome": f"ação: {alvo}"[:30], "ativo": True,
        "criado_em": agora.isoformat(), "texto_original": texto,
        "intencao_no_disparo": {"intent": intent_real, "params": params_reais},
        "comandos_no_disparo": [],
    }

    def _adicionar(lista: list) -> None:
        if not params.get("substituir_agendamento_anterior"):
            lista.append(novo)
            return

        def _mesma(item: Any) -> bool:
            if not isinstance(item, dict) or not item.get("ativo", True):
                return False
            anterior = item.get("intencao_no_disparo")
            if not isinstance(anterior, dict):
                return False
            antigos = dict(anterior.get("params") or {})
            alvo_antigo = str(
                antigos.get("alvo") or antigos.get("nome_app")
                or antigos.get("nome_playlist") or antigos.get("query") or ""
            ).casefold()
            return str(anterior.get("intent") or "").upper() == intent_real and alvo_antigo == alvo.casefold()

        candidatos = [i for i, item in enumerate(lista) if _mesma(item)]
        if candidatos:
            lista.pop(candidatos[-1])
        lista.append(novo)

    salvo = _transacionar(ctx, _adicionar)
    status = "acao_agendada" if salvo else "falha_execucao"
    deps.marcar_resultado(status, executou=salvo)
    deps.falar_por_status(status, escolher_fala_variada([
        f"Combinado. Vou executar isso {tempo_txt}.",
        f"Ação guardada. Quando chegar {tempo_txt}, eu faço e confiro o resultado.",
        f"Fechado. Deixei essa ação marcada para {tempo_txt}.",
    ] if salvo else [
        "Entendi a ação e o horário, mas não consegui salvar o agendamento.",
        "A agenda não confirmou a gravação, então não vou prometer que isso ficou marcado.",
    ]), alvo=alvo)
    _publicar_cooperacao(ctx, "agendar_acao", alvo=alvo, confirmado=salvo)
    _registrar_feedback(ctx, "aceitacao" if salvo else "falha", intent="AGENDAR_ACAO")
    _registrar_mente(ctx, texto, descricao, "AGENDAR_ACAO", alvo, hora_alvo or str(atraso or ""))
    return ResultadoDespacho.concluido()


def _agendar_lembrete(
    params: Dict[str, Any], texto: str, ctx: Dict[str, Any], deps: DependenciasExecutorAgenda,
) -> ResultadoDespacho:
    pendencia_runtime = _get(ctx, "_pendencia_acao_runtime")
    try:
        pendencia_canonica = dict(pendencia_runtime.obter() or {}) if pendencia_runtime is not None else {}
    except Exception:
        pendencia_canonica = {}
    if str(pendencia_canonica.get("origem") or "") != "agenda":
        pendencia_canonica = {}
    if params.get("cancelar_pendente"):
        pendencia_id = str(pendencia_canonica.get("id") or params.get("pendencia_id") or "")
        if pendencia_id and pendencia_runtime is not None:
            pendencia_runtime.concluir(pendencia_id, "recusada")
        deps.marcar_resultado("lembrete_pendente_cancelado", executou=False, confirmado=True)
        _registrar_feedback(ctx, "recusa", intent="AGENDAR_LEMBRETE")
        _falar(ctx, "Tudo bem. Não vou criar esse lembrete.")
        return ResultadoDespacho.concluido()

    pendente_legado = (
        str(_get(ctx, "ultima_intencao", "") or "").upper() == "AGENDAR_LEMBRETE"
        and str(_get(ctx, "ultima_habilidade", "") or "").casefold() == "agenda"
    )
    pendente = bool(pendencia_canonica) or pendente_legado
    metadados_pendentes = dict(pendencia_canonica.get("metadados") or {})
    descricao = str(
        params.get("descricao") or params.get("evento") or params.get("alvo") or params.get("texto") or ""
    ).strip()
    if descricao.casefold() in {"", "lembrete", "isso", "disso", "desse evento", "do evento"} and pendente:
        descricao = str(
            metadados_pendentes.get("descricao")
            or _get(ctx, "ultimo_alvo", "")
            or ""
        ).strip()
    descricao = descricao or "Lembrete"
    minutos = params.get("minutos")
    hora_alvo = str(params.get("hora_alvo") or params.get("hora") or "").strip()
    referencia = str(params.get("data_hora") or params.get("data") or params.get("dia") or "").strip()
    if not referencia and pendente:
        referencia = str(
            metadados_pendentes.get("referencia_data")
            or _get(ctx, "ultimo_escopo", "")
            or ""
        ).strip()
    descricao, referencia = resolver_referencia_contextual_lembrete(
        descricao, referencia, _get(ctx, "ultimas_entradas", []),
    )
    descricao = descricao or "Lembrete"
    try:
        if minutos is not None:
            ts_exec = dt.datetime.now().timestamp() + int(minutos) * 60
            tempo_txt = f"em {int(minutos)} minutos"
        elif hora_alvo:
            instante, tempo_txt = resolver_instante_lembrete(hora_alvo, referencia)
            ts_exec = instante.timestamp()
        else:
            _registrar_mente(ctx, texto, "", "AGENDAR_LEMBRETE", descricao, referencia)
            pergunta = escolher_fala_variada([
                "Me diz o horário ou em quantos minutos eu te lembro disso.",
                "Fala o horário ou os minutos do lembrete.",
                "Preciso do tempo pra guardar esse lembrete.",
            ])
            nova_pendencia = None
            if pendencia_runtime is not None:
                nova_pendencia = pendencia_runtime.registrar(
                    origem="agenda",
                    acao="completar_lembrete",
                    pergunta=pergunta,
                    referencia=descricao,
                    metadados={
                        "descricao": descricao[:160],
                        "referencia_data": referencia[:80],
                    },
                    ttl_s=600.0,
                )
            deps.marcar_resultado(
                "aguardando_complemento",
                executou=False,
                confirmado=False,
                detalhe=(
                    "pendencia=" + str((nova_pendencia or {}).get("id") or "")
                    if nova_pendencia else "pendencia_nao_registrada"
                ),
            )
            if pendencia_canonica:
                _registrar_feedback(ctx, "repeticao", intent="AGENDAR_LEMBRETE")
            _falar(ctx, pergunta)
            return ResultadoDespacho.concluido()
    except Exception:
        deps.marcar_resultado("horario_invalido", executou=False, confirmado=False)
        _registrar_feedback(ctx, "correcao_necessaria", intent="AGENDAR_LEMBRETE")
        _falar(ctx, escolher_fala_variada([
            "Não consegui entender o horário do lembrete. Fala no formato 12:30 ou em 15 minutos.",
            "Esse horário não bateu. Tenta 12:30 ou 15 minutos.",
            "Me passa a hora num formato mais certinho.",
        ]))
        return ResultadoDespacho.concluido()

    novo: Dict[str, Any] = {
        "id": str(uuid.uuid4())[:8], "tipo": "once", "ts_execucao": ts_exec,
        "descricao": descricao, "comandos_no_disparo": [], "nome": descricao[:30],
        "ativo": True, "criado_em": dt.datetime.now().isoformat(),
        "origem": "pedido_usuario", "evidencia": "persistencia_local",
    }
    salvo = _transacionar(ctx, lambda lista: lista.append(novo))
    status = "lembrete_agendado" if salvo else "falha_execucao"
    deps.marcar_resultado(status, executou=salvo)
    deps.falar_por_status(status, escolher_fala_variada([
        f"Feito. Vou te lembrar {tempo_txt} de {descricao}.",
        f"Pronto, lembrete de {descricao} salvo para {tempo_txt}.",
        f"Anotado. Vou te lembrar de {descricao} {tempo_txt}.",
    ] if salvo else [
        "Entendi o lembrete, mas não consegui salvar ele na agenda.",
        "A agenda falhou ao gravar isso, então o lembrete não ficou confirmado.",
    ]), alvo=descricao)
    pendencia_id = str(params.get("pendencia_id") or pendencia_canonica.get("id") or "")
    if salvo and pendencia_id and pendencia_runtime is not None:
        pendencia_runtime.concluir(pendencia_id, "concluida")
    if salvo:
        _registrar_feedback(
            ctx,
            "correcao" if params.get("complemento_pendente") else "aceitacao",
            intent="AGENDAR_LEMBRETE",
        )
    else:
        _registrar_feedback(ctx, "falha", intent="AGENDAR_LEMBRETE")
    _publicar_cooperacao(ctx, "agendar_lembrete", alvo=descricao, confirmado=salvo)
    _registrar_mente(ctx, texto, descricao, "AGENDAR_LEMBRETE", descricao, hora_alvo or str(minutos or ""))
    return ResultadoDespacho.concluido()


def _listar(ctx: Dict[str, Any]) -> ResultadoDespacho:
    carregar = _get(ctx, "_agendamentos_load")
    lista = carregar() if callable(carregar) else []
    ativos = [item for item in lista if item.get("ativo", True)]
    estilizar = _get(ctx, "_fala_agendamentos_estilosa")
    resumo = estilizar(ativos) if callable(estilizar) else "Agendamentos."
    _falar(ctx, resumo, "debochada", 1)
    return ResultadoDespacho.concluido()


def _cancelar(params: Dict[str, Any], ctx: Dict[str, Any], deps: DependenciasExecutorAgenda) -> ResultadoDespacho:
    alvo = str(params.get("alvo") or params.get("nome") or params.get("query") or "").strip().lower()
    if not alvo:
        _falar(ctx, escolher_fala_variada([
            "Cancelo o quê? Me fala qual lembrete ou compromisso você quer apagar.",
            "Qual compromisso eu corto?",
            "Faltou dizer qual agendamento eu devo apagar.",
        ]), "debochada", 2)
        return ResultadoDespacho.concluido()
    alteracao = {"cancelados": 0}

    def _aplicar(lista: list) -> None:
        for item in lista:
            nome = str(item.get("nome") or item.get("descricao") or item.get("id") or "").lower()
            item_id = str(item.get("id") or "").lower()
            if alvo in nome or alvo == item_id:
                item["ativo"] = False
                alteracao["cancelados"] += 1

    salvo = _transacionar(ctx, _aplicar)
    total = alteracao["cancelados"]
    ok = total > 0 and salvo
    status = "agendamento_cancelado" if ok else "falha_execucao"
    deps.marcar_resultado(status, executou=ok)
    mensagem = escolher_fala_variada([
        f"{total} agendamento(s) cancelado(s)." if ok else "Não consegui confirmar o cancelamento desse agendamento.",
        f"Apaguei {total} agendamento(s)." if ok else "Esse agendamento não foi encontrado ou a agenda não salvou a mudança.",
        f"Feito, {total} compromisso(s) saíram da lista." if ok else "Nada foi cancelado de verdade com esse nome.",
    ])
    deps.falar_por_status(status, mensagem, alvo=alvo)
    return ResultadoDespacho.concluido()


def executar_intencao_agenda(
    intent: str, params: Dict[str, Any], texto: str, ctx: Dict[str, Any], deps: DependenciasExecutorAgenda,
) -> ResultadoDespacho:
    intent = str(intent or "").upper().strip()
    if intent not in INTENCOES_AGENDA:
        return ResultadoDespacho.nao_tratado()
    if intent == "AGENDAR_ACAO":
        return _agendar_acao(params, texto, ctx, deps)
    if intent == "AGENDAR_LEMBRETE":
        return _agendar_lembrete(params, texto, ctx, deps)
    if intent == "LISTAR_AGENDAMENTOS":
        return _listar(ctx)
    return _cancelar(params, ctx, deps)
