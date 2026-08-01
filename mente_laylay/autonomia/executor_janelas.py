"""Despacho das intencoes de abertura e organizacao de janelas.

Este modulo cuida apenas da orquestracao do dominio. A leitura e manipulacao
real das janelas continuam centralizadas em ``habilidade_janelas``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_comum import falar_ctx as _falar
from mente_laylay.autonomia.habilidade_janelas import executar_habilidade_janelas
from mente_laylay.personalidade.falas_variadas import escolher as escolher_fala_variada


INTENCOES_JANELAS = frozenset({
    "ORGANIZAR_DESKTOP",
    "MAXIMIZE_WINDOW",
    "APP_OPEN",
    "CLOSE_APP",
    "FECHAR_PROGRAMA",
})


@dataclass(frozen=True, slots=True)
class DependenciasExecutorJanelas:
    """Operacoes do roteador usadas para registrar e verbalizar o resultado."""

    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]
    falar_resultado_janela: Callable[[str, str], Any]
    alvo_preciso_para_aba: Callable[[str], str] | None = None
    esperar_aba_fechar: Callable[..., bool] | None = None
    esperar_programa_fechar: Callable[[str], bool] | None = None
    executar_recursivo: Callable[[dict, str, Dict[str, Any]], bool] | None = None


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _explicar_prioridade(item: Any) -> str:
    if not isinstance(item, dict):
        return ""
    motivos = [str(motivo or "").strip().casefold() for motivo in item.get("motivos") or []]
    traducoes = (
        ("janela em foco", "estava em foco"),
        ("reproduzindo áudio", "estava reproduzindo áudio"),
        ("uso recente", "foi usada recentemente"),
        ("uso recorrente", "vem sendo bastante usada"),
        ("aberto recentemente", "foi aberta recentemente"),
    )
    for motivo, fala in traducoes:
        if motivo.casefold() in motivos:
            return fala
    return ""


def _executar_organizar_desktop(
    params: Dict[str, Any],
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorJanelas,
) -> ResultadoDespacho:
    app_esquerda = str(params.get("left") or params.get("esquerda") or "").strip()
    app_direita = str(params.get("right") or params.get("direita") or "").strip()
    enviar_pc_b = _get(ctx, "_enviar_pc_b")
    organizar = _get(ctx, "organizar_janelas_robusto")
    try:
        if destino == "pc_b" and callable(enviar_pc_b):
            enviar_pc_b({"action": "organizar_desktop", "left": app_esquerda, "right": app_direita})
            deps.marcar_resultado("organizacao_solicitada", executou=True, confirmado=None)
            _falar(ctx, "Enviei a organização ao PC B, mas ele não confirmou o layout final.")
            return ResultadoDespacho.concluido()
        if not callable(organizar):
            deps.marcar_resultado("indisponivel", executou=False, confirmado=False)
            _falar(ctx, "Não consegui acessar o organizador de janelas agora.")
            return ResultadoDespacho.concluido()

        retorno = organizar(app_esquerda, app_direita)
        prioridades = []
        if isinstance(retorno, dict):
            status = str(retorno.get("status") or "falha_execucao").strip().lower()
            executou = bool(retorno.get("executou", retorno.get("ok")))
            confirmado = retorno.get("confirmado")
            confirmado = bool(confirmado) if confirmado is not None else None
            esquerda_real = str(retorno.get("nome_esquerda") or app_esquerda).strip()
            direita_real = str(retorno.get("nome_direita") or app_direita).strip()
            prioridades = list(
                retorno.get("prioridades")
                or params.get("prioridades_planejadas")
                or []
            )
        elif retorno is True:
            status, executou, confirmado = "layout_confirmado", True, True
            esquerda_real, direita_real = app_esquerda, app_direita
        elif retorno is False:
            status, executou, confirmado = "falha_execucao", False, False
            esquerda_real, direita_real = app_esquerda, app_direita
        else:
            status, executou, confirmado = "organizacao_nao_confirmada", True, None
            esquerda_real, direita_real = app_esquerda, app_direita

        modo_automatico = str(params.get("modo") or "").strip().casefold() in {
            "automatico", "automatico_cooperativo",
        }
        detalhe_prioridade = ""
        if modo_automatico and prioridades:
            detalhe_prioridade = "; ".join(
                f"{str(item.get('titulo') or '').strip()}: {_explicar_prioridade(item)}"
                for item in prioridades[:2]
                if isinstance(item, dict) and _explicar_prioridade(item)
            )
        kwargs_resultado = {"executou": executou, "confirmado": confirmado}
        if detalhe_prioridade:
            kwargs_resultado["detalhe"] = f"prioridade automática: {detalhe_prioridade}"
        deps.marcar_resultado(status, **kwargs_resultado)
        if confirmado is True:
            if esquerda_real and direita_real:
                if modo_automatico and len(prioridades) >= 2:
                    motivo_esq = _explicar_prioridade(prioridades[0])
                    motivo_dir = _explicar_prioridade(prioridades[1])
                    explicacao_esq = f", porque {motivo_esq}" if motivo_esq else ""
                    explicacao_dir = f", porque {motivo_dir}" if motivo_dir else ""
                    _falar(
                        ctx,
                        f"Organizei por prioridade: {esquerda_real} ficou na esquerda{explicacao_esq}, "
                        f"e {direita_real} na direita{explicacao_dir}.",
                        "feliz",
                        1,
                    )
                else:
                    _falar(
                        ctx,
                        f"Pronto: {esquerda_real} ficou na esquerda e {direita_real} na direita. Conferi o layout.",
                        "feliz",
                        1,
                    )
            elif esquerda_real:
                _falar(ctx, f"Pronto, deixei {esquerda_real} na esquerda e conferi a posição.", "feliz", 1)
            elif direita_real:
                _falar(ctx, f"Pronto, deixei {direita_real} na direita e conferi a posição.", "feliz", 1)
            else:
                _falar(ctx, "Organizei as janelas visíveis e conferi o layout.", "feliz", 1)
        elif not executou:
            ausentes = [nome for nome in (esquerda_real, direita_real) if nome]
            alvo = " e ".join(ausentes) or "janelas suficientes"
            _falar(ctx, f"Não consegui encontrar {alvo} para organizar a tela.")
        else:
            _falar(ctx, "Posicionei as janelas, mas o Windows não me deixou confirmar a geometria final.")
    except Exception as erro:
        deps.marcar_resultado("falha_execucao", executou=False, confirmado=False)
        registrar_falha = _get(ctx, "_registrar_falha_tecnica")
        if callable(registrar_falha):
            try:
                registrar_falha("organizar_desktop", "falha_execucao", erro=erro)
            except Exception:
                pass
        _falar(
            ctx,
            escolher_fala_variada([
                "Tentei organizar a área, mas o Windows resolveu fazer drama.",
                "A organização emperrou no humor do Windows.",
                "Quase arrumei tudo, mas o sistema fez cena.",
            ]),
            "irritada",
            2,
        )
    return ResultadoDespacho.concluido()


def _executar_maximizar(
    intent: str,
    params: Dict[str, Any],
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorJanelas,
) -> ResultadoDespacho:
    app = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
    enviar_pc_b = _get(ctx, "_enviar_pc_b")
    if destino == "pc_b" and callable(enviar_pc_b):
        enviar_pc_b({"action": "maximize_window", "app": app})
        deps.marcar_resultado("janela_maximizada_pc_b", executou=True)
        deps.falar_por_status(
            "janela_maximizada_pc_b",
            f"Maximizando {app or 'a janela'} no PC B.",
            alvo=app or "a janela",
        )
        return ResultadoDespacho.concluido()

    resultado = executar_habilidade_janelas(intent, params, ctx)
    if isinstance(resultado, dict) and resultado.get("handled"):
        app = str(resultado.get("nome_app") or params.get("nome_app") or "").strip()
        status = str(resultado.get("status") or "falha_execucao").strip().lower()
        if status == "alvo_ausente":
            _falar(ctx, escolher_fala_variada([
                "Qual janela você quer maximizar?",
                "Me fala qual janela eu devo trazer pra frente.",
                "Faltou dizer a janela.",
            ]))
            return ResultadoDespacho.concluido()
        deps.marcar_resultado(status, executou=bool(resultado.get("ok")))
        deps.falar_resultado_janela(app, status)
        return ResultadoDespacho.concluido()

    if not app:
        _falar(ctx, escolher_fala_variada([
            "Qual janela você quer maximizar?",
            "Me fala qual janela eu devo trazer pra frente.",
            "Faltou dizer a janela.",
        ]))
        return ResultadoDespacho.concluido()
    deps.marcar_resultado("falha_execucao", executou=False)
    deps.falar_por_status(
        "falha_execucao",
        f"Tentei maximizar {app}, mas não rolou de verdade.",
        alvo=app,
    )
    return ResultadoDespacho.concluido()


def _executar_abrir_app(
    intent: str,
    params: Dict[str, Any],
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorJanelas,
) -> ResultadoDespacho:
    nome = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
    if not nome:
        _falar(ctx, escolher_fala_variada([
            "Tá, mas abrir o quê? Fala o nome do app direito.",
            "Me diz qual app eu devo abrir.",
            "Faltou o nome do aplicativo.",
        ]), "debochada", 2)
        return ResultadoDespacho.concluido()

    enviar_pc_b = _get(ctx, "_enviar_pc_b")
    apps_map = _get(ctx, "APPS_MAP", {}) or {}
    if destino == "ambos" and callable(enviar_pc_b):
        mapped_remoto = apps_map.get(nome.lower().strip(), nome)
        enviar_pc_b({
            "action": "open_app",
            "app": mapped_remoto,
            "quantidade": int(params.get("quantidade") or 1),
        })

    if destino == "pc_b" and callable(enviar_pc_b):
        key = nome.lower().strip()
        mapped = apps_map.get(key, nome)
        sites_diretos = _get(ctx, "SITES_DIRECTOS", {}) or {}
        normalizar = _get(ctx, "_normalizar_texto_com_apelidos")
        eh_site = _get(ctx, "_eh_alvo_site_web")
        contexto_site = _get(ctx, "_contexto_aponta_site_web")
        url_site = ""
        if isinstance(mapped, str) and mapped.startswith(("http://", "https://")):
            url_site = mapped
        elif isinstance(mapped, str) and re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:$", mapped.strip()):
            url_site = mapped
        elif callable(eh_site) and callable(contexto_site) and (eh_site(nome) or contexto_site(nome)):
            nome_normalizado = normalizar(nome) if callable(normalizar) else nome
            url_site = sites_diretos.get(key) or sites_diretos.get(nome_normalizado) or ""
            if not url_site and "instagram" in key:
                url_site = "https://www.instagram.com"
        if url_site:
            enviar_pc_b({"action": "open_url", "url": url_site})
            deps.marcar_resultado("site_aberto", executou=True)
            deps.falar_por_status("site_aberto", f"Abrindo {nome} no PC B.", alvo=nome)
            return ResultadoDespacho.concluido()
        enviar_pc_b({"action": "open_app", "app": mapped, "quantidade": 1})
        deps.marcar_resultado("app_aberto_pc_b", executou=True)
        deps.falar_por_status("app_aberto_pc_b", f"Abrindo {nome} no PC B.", alvo=nome)
        return ResultadoDespacho.concluido()

    resultado = executar_habilidade_janelas(intent, params, ctx)
    if isinstance(resultado, dict) and resultado.get("handled"):
        nome = str(resultado.get("nome_app") or params.get("nome_app") or "").strip()
        status = str(resultado.get("status") or "falha_execucao").strip().lower()
        if status == "alvo_ausente":
            _falar(ctx, escolher_fala_variada([
                "Tá, mas abrir o quê? Fala o nome do app direito.",
                "Me diz qual app eu devo abrir.",
                "Faltou o nome do aplicativo.",
            ]), "debochada", 2)
            return ResultadoDespacho.concluido()
        deps.marcar_resultado(status, executou=bool(resultado.get("ok")))
        deps.falar_resultado_janela(nome, status)
        return ResultadoDespacho.concluido()

    deps.marcar_resultado("falha_execucao", executou=False)
    deps.falar_por_status(
        "falha_execucao",
        f"Tentei abrir {nome}, mas não consegui validar a abertura.",
        alvo=nome,
    )
    return ResultadoDespacho.concluido()


def _executar_fechar_app(
    params: Dict[str, Any],
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorJanelas,
) -> ResultadoDespacho:
    nome = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
    if not nome:
        _falar(ctx, escolher_fala_variada([
            "Fechar o quê? Me fala o nome do programa direito.",
            "Qual programa eu fecho?",
            "Faltou o nome do app.",
        ]), "debochada", 2)
        return ResultadoDespacho.concluido()

    enviar_pc_b = _get(ctx, "_enviar_pc_b")
    navegador_operacoes = _get(ctx, "_registro_navegador_operacoes_runtime")
    fechar_programa = _get(ctx, "fechar_programa")
    resolver_alvo = _get(ctx, "_resolver_alvo_ambiente")
    eh_site = _get(ctx, "_eh_alvo_site_web")
    contexto_site = _get(ctx, "_contexto_aponta_site_web")
    apps_map = _get(ctx, "APPS_MAP", {}) or {}

    if destino == "ambos" and callable(enviar_pc_b):
        mapped_remoto = apps_map.get(nome.lower(), nome)
        enviar_pc_b({"action": "close_app", "app": mapped_remoto})

    leitura = resolver_alvo(nome) if callable(resolver_alvo) else {}
    programa_aberto = bool((leitura or {}).get("programa_aberto"))
    alvo_preciso = deps.alvo_preciso_para_aba
    esperar_aba = deps.esperar_aba_fechar

    def _confirmar_aba_fechada(alvo_tab: str, estado_antes: Dict[str, Any]) -> bool:
        if not callable(esperar_aba):
            return False
        try:
            return bool(esperar_aba(alvo_tab, estado_antes))
        except TypeError:
            # Compatibilidade com adaptadores/testes antigos de um argumento.
            return bool(esperar_aba(alvo_tab))

    if bool((leitura or {}).get("aba_aberta")) and not programa_aberto:
        # A leitura já encontrou a aba correta. Prefira a URL observada em vez
        # de transformar um nome como "tuya" numa busca/host aproximado.
        referencia_aba = str((leitura or {}).get("url") or nome).strip()
        alvo_tab = alvo_preciso(referencia_aba) if callable(alvo_preciso) else referencia_aba
        if destino == "pc_b" and callable(enviar_pc_b):
            enviar_pc_b({"action": "close_specific_tab", "target": alvo_tab})
            ok_aba = True
        elif navegador_operacoes is not None:
            enviado = bool(navegador_operacoes.fechar_aba(alvo_tab))
            ok_aba = bool(enviado and _confirmar_aba_fechada(alvo_tab, leitura))
        else:
            ok_aba = False
        status = "aba_fechada_em_vez_de_app" if ok_aba else "falha_execucao"
        deps.marcar_resultado(status, executou=ok_aba)
        deps.falar_por_status(
            status,
            f"{nome} não estava aberto como programa. Fechei a aba."
            if ok_aba else f"Tentei fechar a aba de {nome}, mas ela resistiu.",
            alvo=nome,
        )
        return ResultadoDespacho.concluido()

    alvo_eh_site = (
        not programa_aberto
        and callable(eh_site)
        and callable(contexto_site)
        and (eh_site(nome) or contexto_site(nome))
    )
    if alvo_eh_site:
        referencia_aba = str((leitura or {}).get("url") or nome).strip()
        alvo_tab = alvo_preciso(referencia_aba) if callable(alvo_preciso) else referencia_aba
        if destino == "pc_b" and callable(enviar_pc_b):
            enviar_pc_b({"action": "close_specific_tab", "target": alvo_tab})
            ok_aba = True
        elif navegador_operacoes is not None:
            enviado = bool(navegador_operacoes.fechar_aba(alvo_tab))
            ok_aba = bool(enviado and _confirmar_aba_fechada(alvo_tab, leitura))
        else:
            ok_aba = False
        status = "aba_fechada" if ok_aba else "falha_execucao"
        deps.marcar_resultado(status, executou=ok_aba)
        deps.falar_por_status(
            status,
            f"Fechei a aba do {nome}."
            if ok_aba else f"Tentei fechar a aba do {nome}, mas não consegui confirmar.",
            alvo=nome,
        )
        return ResultadoDespacho.concluido()

    mapped = apps_map.get(nome.lower(), nome)
    if destino == "pc_b" and callable(enviar_pc_b):
        enviar_pc_b({"action": "close_app", "app": mapped})
        deps.marcar_resultado("app_fechado_pc_b", executou=True)
        deps.falar_por_status("app_fechado_pc_b", f"Fechando {nome} no PC B.", alvo=nome)
    elif callable(fechar_programa):
        try:
            fechar_programa(mapped)
        except Exception:
            pass
        esperar_programa = deps.esperar_programa_fechar
        ok = bool(esperar_programa(nome)) if callable(esperar_programa) else False
        status = "app_fechado" if ok else "falha_execucao"
        deps.marcar_resultado(status, executou=ok)
        deps.falar_por_status(
            status,
            f"Pronto, {nome} foi fechado."
            if ok else f"Tentei fechar {nome}, mas ele continuou por aí.",
            alvo=nome,
        )
    return ResultadoDespacho.concluido()


def _executar_alias_fechar_programa(
    params: Dict[str, Any],
    texto_original: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorJanelas,
) -> ResultadoDespacho:
    nome = str(
        params.get("nome") or params.get("app") or params.get("programa")
        or params.get("nome_busca") or ""
    ).strip()
    if not nome:
        _falar(ctx, escolher_fala_variada([
            "Fechar o quê? Me fala o nome do programa direito.",
            "Qual programa eu fecho?",
            "Faltou o nome do app.",
        ]), "debochada", 2)
        return ResultadoDespacho.concluido()
    if callable(deps.executar_recursivo):
        retorno = deps.executar_recursivo(
            {"intent": "CLOSE_APP", "params": {"nome_app": nome}},
            texto_original,
            ctx,
        )
        return ResultadoDespacho.concluido(retorno)
    return ResultadoDespacho.nao_tratado()


def executar_intencao_janelas(
    intent: str,
    params: Dict[str, Any],
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorJanelas,
    *,
    texto_original: str = "",
) -> ResultadoDespacho:
    """Executa uma intencao do dominio ou informa explicitamente que nao a trata."""

    intent = str(intent or "").upper().strip()
    if intent not in INTENCOES_JANELAS:
        return ResultadoDespacho.nao_tratado()
    if intent == "ORGANIZAR_DESKTOP":
        return _executar_organizar_desktop(params, destino, ctx, deps)
    if intent == "MAXIMIZE_WINDOW":
        return _executar_maximizar(intent, params, destino, ctx, deps)
    if intent == "APP_OPEN":
        return _executar_abrir_app(intent, params, destino, ctx, deps)
    if intent == "CLOSE_APP":
        return _executar_fechar_app(params, destino, ctx, deps)
    return _executar_alias_fechar_programa(params, texto_original, ctx, deps)
