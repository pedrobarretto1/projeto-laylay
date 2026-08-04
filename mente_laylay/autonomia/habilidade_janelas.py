"""Habilidade enxuta para abrir, focar e maximizar janelas/apps.

Objetivo:
- ter um unico caminho para acoes de janela;
- responder com base no estado real;
- integrar com a mente unica sem depender de varios atalhos conflitantes.
"""

from __future__ import annotations

import time
from typing import Any, Dict


APPS_SEM_JANELA_CONTEXTUAL = {
    "microsoft store",
    "store",
    "ms store",
    "loja microsoft",
    "loja",
}


def _get(ctx: Dict[str, Any], nome: str, default=None):
    return ctx.get(nome, default)


def _log(etapa: str, mensagem: str) -> None:
    try:
        print(f"🪟 [JANELA:{str(etapa or '').upper()}] {mensagem}")
    except Exception:
        pass


def _normalizar(nome: str, ctx: Dict[str, Any]) -> str:
    fn = _get(ctx, "_normalizar_texto_com_apelidos")
    if callable(fn):
        try:
            return str(fn(nome or "")).strip().lower()
        except Exception:
            pass
    return str(nome or "").strip().lower()


def _eh_app_sem_janela(nome: str, ctx: Dict[str, Any]) -> bool:
    return _normalizar(nome, ctx) in APPS_SEM_JANELA_CONTEXTUAL


def _eh_url(valor: Any) -> bool:
    texto = str(valor or "").strip().lower()
    return texto.startswith(("http://", "https://", "www."))


def _resolver_url_site(nome: str, mapped: Any, ctx: Dict[str, Any]) -> str:
    if _eh_url(mapped):
        return str(mapped or "").strip()

    sites = _get(ctx, "SITES_DIRECTOS", {}) or {}
    nome_norm = _normalizar(nome, ctx)
    mapped_norm = _normalizar(str(mapped or ""), ctx)
    for chave in (nome_norm, mapped_norm):
        if chave and chave in sites:
            return str(sites.get(chave) or "").strip()

    montar_url = _get(ctx, "_montar_url_site_ou_busca")
    if callable(montar_url):
        try:
            if "." in nome_norm and " " not in nome_norm:
                return str(montar_url(nome_norm) or "").strip()
        except Exception:
            pass
    return ""


def _abrir_url_mapeada(
    nome: str,
    url: str,
    ctx: Dict[str, Any],
    *,
    permitir_foco: bool = False,
) -> bool:
    navegador_operacoes = _get(ctx, "_registro_navegador_operacoes_runtime")
    url = str(url or "").strip()
    if not url:
        return False
    if url.lower().startswith("www."):
        url = "https://" + url
    _log("acao", f"{nome} mapeado como site -> abrir_url {url}")
    try:
        if navegador_operacoes is not None:
            return bool(navegador_operacoes.abrir_url(
                url, permitir_foco=permitir_foco,
            ))
    except Exception as e:
        _log("acao", f"{nome} falha ao abrir site mapeado: {e}")
        return False
    return False


def _ler_estado_alvo(nome: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    resolver = _get(ctx, "_resolver_alvo_ambiente")
    if callable(resolver):
        try:
            estado = dict(resolver(nome) or {})
            _log("estado", f"{nome} -> aberto={bool(estado.get('programa_aberto'))} foco={bool(estado.get('programa_em_foco'))} aba={bool(estado.get('aba_aberta'))} preferido={estado.get('preferido') or 'desconhecido'}")
            return estado
        except Exception:
            _log("estado", f"{nome} -> falha ao ler estado")
            return {}
    return {}


def _aguardar_estado(nome: str, ctx: Dict[str, Any], tentativas: int = 6, pausa: float = 0.35) -> Dict[str, Any]:
    ultimo = {}
    for _ in range(max(1, tentativas)):
        ultimo = _ler_estado_alvo(nome, ctx)
        if ultimo.get("programa_aberto"):
            return ultimo
        time.sleep(max(0.05, pausa))
    return ultimo


def _tentar_foco(nome: str, mapped: Any, ctx: Dict[str, Any], focar_app: Any) -> bool:
    if not callable(focar_app):
        return False
    try:
        foco_ok = bool(focar_app(mapped))
    except Exception:
        foco_ok = False
    estado_pos = _aguardar_estado(nome, ctx, tentativas=4, pausa=0.2)
    return bool(estado_pos.get("programa_em_foco")) or foco_ok


def _reativar_app_sem_janela_principal(nome: str, mapped: Any, ctx: Dict[str, Any], abrir_programa: Any) -> bool:
    """Chama o app de novo para restaurar janela principal quando o processo ja existe."""
    if not callable(abrir_programa):
        return False
    _log("acao", f"{nome} aberto sem foco -> tentar reativar interface")
    try:
        reativou = bool(abrir_programa(mapped))
    except Exception as e:
        _log("acao", f"{nome} reativacao falhou: {e}")
        return False

    for _ in range(8):
        estado = _ler_estado_alvo(nome, ctx)
        if estado.get("programa_em_foco"):
            return True
        time.sleep(0.35)
    return reativou


def _tentar_foco_com_reativacao(
    nome: str,
    mapped: Any,
    ctx: Dict[str, Any],
    focar_app: Any,
    abrir_programa: Any,
) -> bool:
    if _tentar_foco(nome, mapped, ctx, focar_app):
        return True
    if _reativar_app_sem_janela_principal(nome, mapped, ctx, abrir_programa):
        if _tentar_foco(nome, mapped, ctx, focar_app):
            return True
        estado_pos = _aguardar_estado(nome, ctx, tentativas=4, pausa=0.2)
        return bool(estado_pos.get("programa_em_foco"))
    return False


def executar_habilidade_janelas(intent: str, params: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any] | None:
    intent = str(intent or "").strip().upper()
    if intent not in {"APP_OPEN", "MAXIMIZE_WINDOW"}:
        return None

    nome = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
    if not nome:
        _log("entrada", f"{intent} sem alvo")
        return {"ok": False, "status": "alvo_ausente", "nome_app": "", "handled": True}

    apps_map = _get(ctx, "APPS_MAP", {}) or {}
    abrir_programa = _get(ctx, "abrir_programa")
    focar_app = _get(ctx, "focar_janela_app")
    ativar_full = _get(ctx, "ativar_tela_cheia_robusta")

    key = nome.lower().strip()
    mapped = apps_map.get(key, nome)
    modo = str(params.get("modo") or "").strip().lower()
    quer_maximizar = intent == "MAXIMIZE_WINDOW" or modo in {"fullscreen", "tela_cheia"}
    modo_jogo_ativo = _get(ctx, "modo_jogo_ativo")
    jogo_ativo = bool(modo_jogo_ativo()) if callable(modo_jogo_ativo) else False
    permitir_foco = bool(params.get("permitir_foco")) or quer_maximizar
    preservar_jogo = jogo_ativo and not permitir_foco
    sem_janela = _eh_app_sem_janela(nome, ctx) or (
        isinstance(mapped, str) and mapped.strip().endswith(":")
    )
    _log("entrada", f"intent={intent} nome={nome} mapped={mapped} maximizar={quer_maximizar} sem_janela={sem_janela}")

    url_site = _resolver_url_site(nome, mapped, ctx)
    if url_site:
        estado_site = _ler_estado_alvo(nome, ctx)
        aba_ja_aberta = bool(estado_site.get("aba_aberta"))
        ok = _abrir_url_mapeada(nome, url_site, ctx, permitir_foco=permitir_foco)
        status_site = (
            "site_aberto_segundo_plano"
            if ok and preservar_jogo
            else "site_ja_aberto_focado"
            if ok and aba_ja_aberta
            else "site_aberto"
            if ok
            else "falha_execucao"
        )
        _log("resultado", f"{nome} -> {status_site}")
        return {
            "ok": ok,
            "status": status_site,
            "nome_app": nome,
            "url": url_site,
            "handled": True,
        }

    estado_inicial = _ler_estado_alvo(nome, ctx)
    programa_aberto = bool(estado_inicial.get("programa_aberto"))
    programa_em_foco = bool(estado_inicial.get("programa_em_foco"))

    if programa_aberto:
        if preservar_jogo:
            _log("resultado", f"{nome} -> app_aberto_segundo_plano (modo jogo)")
            return {"ok": True, "status": "app_aberto_segundo_plano", "nome_app": nome, "handled": True}
        if quer_maximizar:
            _log("acao", f"{nome} já aberto -> tentar maximizar")
            foco_ok = False
            if callable(ativar_full):
                try:
                    foco_ok = bool(ativar_full(mapped))
                except Exception:
                    foco_ok = False
            estado_pos = _aguardar_estado(nome, ctx, tentativas=4, pausa=0.2)
            foco_ok = bool(estado_pos.get("programa_em_foco")) or foco_ok
            if not foco_ok:
                foco_ok = _tentar_foco_com_reativacao(nome, mapped, ctx, focar_app, abrir_programa)
                if foco_ok and callable(ativar_full):
                    try:
                        foco_ok = bool(ativar_full(mapped)) or foco_ok
                    except Exception:
                        pass
            _log("resultado", f"{nome} -> {'janela_maximizada' if foco_ok else 'falha_execucao'}")
            return {
                "ok": foco_ok,
                "status": "janela_maximizada" if foco_ok else "falha_execucao",
                "nome_app": nome,
                "handled": True,
            }

        if programa_em_foco:
            _log("resultado", f"{nome} -> ja_aberto_focado")
            return {"ok": True, "status": "ja_aberto_focado", "nome_app": nome, "handled": True}

        _log("acao", f"{nome} já aberto -> tentar foco")
        foco_ok = _tentar_foco_com_reativacao(nome, mapped, ctx, focar_app, abrir_programa)
        _log("resultado", f"{nome} -> {'app_focado' if foco_ok else 'app_aberto_sem_foco'}")
        return {
            "ok": foco_ok,
            "status": "app_focado" if foco_ok else "app_aberto_sem_foco",
            "nome_app": nome,
            "handled": True,
        }

    abriu = False
    erro = ""
    _log("acao", f"{nome} fechado -> tentar abrir")
    if callable(abrir_programa):
        try:
            abriu = bool(abrir_programa(mapped))
        except Exception as e:
            erro = str(e or "").strip()
            abriu = False
    _log("acao", f"{nome} abrir retornou={abriu} erro={erro or '-'}")

    if sem_janela:
        _log("resultado", f"{nome} -> {'protocolo_aberto' if abriu else 'falha_execucao'}")
        return {
            "ok": abriu,
            "status": "protocolo_aberto" if abriu else "falha_execucao",
            "nome_app": nome,
            "erro": erro,
            "handled": True,
        }

    estado_pos_abertura = _aguardar_estado(nome, ctx, tentativas=7, pausa=0.35)
    if abriu and not bool(estado_pos_abertura.get("programa_aberto")):
        # Jogos e launchers podem aceitar a abertura antes de criarem a janela
        # principal. A segunda espera evita um falso negativo imediato.
        _log("acao", f"{nome} aceitou abertura; aguardando inicialização lenta")
        estado_pos_abertura = _aguardar_estado(nome, ctx, tentativas=12, pausa=0.5)
    if not bool(estado_pos_abertura.get("programa_aberto")):
        status_sem_confirmacao = "nao_encontrado" if erro else "abertura_solicitada" if abriu else "falha_execucao"
        _log("resultado", f"{nome} -> {status_sem_confirmacao}")
        return {
            "ok": bool(abriu),
            "status": status_sem_confirmacao,
            "nome_app": nome,
            "erro": erro,
            "handled": True,
        }

    if preservar_jogo:
        _log("resultado", f"{nome} -> app_aberto_segundo_plano (foco preservado pelo modo jogo)")
        return {
            "ok": True,
            "status": "app_aberto_segundo_plano",
            "nome_app": nome,
            "handled": True,
        }

    if quer_maximizar:
        _log("acao", f"{nome} abriu -> tentar maximizar")
        foco_ok = False
        if callable(ativar_full):
            try:
                foco_ok = bool(ativar_full(mapped))
            except Exception:
                foco_ok = False
        estado_pos = _aguardar_estado(nome, ctx, tentativas=4, pausa=0.2)
        foco_ok = bool(estado_pos.get("programa_em_foco")) or foco_ok
        _log("resultado", f"{nome} -> {'janela_maximizada' if foco_ok else 'app_aberto_sem_foco'}")
        return {
            "ok": foco_ok,
            "status": "janela_maximizada" if foco_ok else "app_aberto_sem_foco",
            "nome_app": nome,
            "handled": True,
        }

    _log("acao", f"{nome} abriu -> tentar foco")
    foco_ok = _tentar_foco_com_reativacao(nome, mapped, ctx, focar_app, abrir_programa)
    status_final = "app_iniciado_focado" if foco_ok else "app_aberto"
    _log("resultado", f"{nome} -> {status_final}")
    return {
        "ok": True,
        "status": status_final,
        "nome_app": nome,
        "estado_anterior": {
            "programa_aberto": programa_aberto,
            "programa_em_foco": programa_em_foco,
        },
        "estado_posterior": {
            "programa_aberto": True,
            "programa_em_foco": bool(foco_ok),
        },
        "handled": True,
    }
