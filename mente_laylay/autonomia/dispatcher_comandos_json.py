"""Dispatcher dos comandos JSON executados pela resposta da IA."""

from __future__ import annotations

import re
from typing import Any, Dict, List

def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def adaptar_acao_json_para_intencao(cmd: Dict[str, Any], alvo: str = "") -> Dict[str, Any] | None:
    """Converte o contrato JSON antigo para a intenção canônica da Laylay."""
    if not isinstance(cmd, dict):
        return None
    acao = str(cmd.get("acao") or cmd.get("intent") or "").strip().casefold()
    destino = str(cmd.get("target") or "pc_a").strip().casefold()
    alvo = str(alvo or cmd.get("alvo") or cmd.get("url") or cmd.get("app") or cmd.get("query") or cmd.get("nome") or "").strip()

    simples = {
        "open_url": ("OPEN_URL", "url"),
        "open_app": ("APP_OPEN", "nome_app"),
        "close_app": ("CLOSE_APP", "nome_app"),
        "maximize_window": ("MAXIMIZE_WINDOW", "nome_app"),
        "capturar_tela": ("SCREEN_CAPTURE", "alvo"),
        "fechar_abas_paradas": ("CLOSE_IDLE_TABS", "alvo"),
        "criar_pasta": ("CREATE_FOLDER", "alvo"),
        "criar_arquivo": ("CREATE_FILE", "alvo"),
        "deletar_item": ("DELETE_ITEM", "alvo"),
        "agendar_lembrete": ("AGENDAR_LEMBRETE", "descricao"),
        "listar_agendamentos": ("LISTAR_AGENDAMENTOS", "alvo"),
        "cancelar_agendamento": ("CANCELAR_AGENDAMENTO", "alvo"),
    }
    if acao in simples:
        intent, chave_alvo = simples[acao]
        params = {k: v for k, v in cmd.items() if k not in {"acao", "intent"}}
        if alvo and not params.get(chave_alvo):
            params[chave_alvo] = alvo
        params.setdefault("target", destino)
        return {"intent": intent, "params": params}

    if acao == "organizar_desktop":
        return {
            "intent": "ORGANIZAR_DESKTOP",
            "params": {
                "left": str(cmd.get("left") or cmd.get("esquerda") or "vscode"),
                "right": str(cmd.get("right") or cmd.get("direita") or "opera"),
                "target": destino,
            },
        }
    if acao in {"ligar", "desligar", "alternar"}:
        return {
            "intent": "IOT_CONTROL",
            "params": {"acao": acao, "alvo": alvo or str(cmd.get("dispositivo") or "")},
        }
    if acao in {"ler_emails", "ler_emails_urgentes"}:
        return {
            "intent": "EMAIL_READ",
            "params": {"urgentes": acao == "ler_emails_urgentes"},
        }
    if acao == "sincronizar_emails":
        return {"intent": "EMAIL_SYNC", "params": {}}
    if acao == "lock_pc":
        return {"intent": "LOCK_PC", "params": {"target": destino}}
    if acao in {"ler_notificacoes", "silenciar_notificacoes", "ativar_notificacoes"}:
        modo = {
            "ler_notificacoes": "ler",
            "silenciar_notificacoes": "silenciar",
            "ativar_notificacoes": "ativar",
        }[acao]
        return {"intent": "NOTIFICATIONS", "params": {"acao": modo}}
    if acao == "youtube_search":
        return {
            "intent": "MUSIC_SEARCH",
            "params": {"query": alvo, "target": destino, "origem": "json_canonico"},
        }
    if acao == "youtube_control":
        return {
            "intent": "MEDIA_CONTROL",
            "params": {"acao": alvo or str(cmd.get("command") or ""), "target": destino},
        }
    if acao == "youtube_play":
        return {"intent": "OPEN_URL", "params": {"url": alvo, "target": destino}}
    if acao == "tocar_playlist":
        return {
            "intent": "PLAYLIST_PLAY",
            "params": {"nome_playlist": alvo, "target": destino},
        }
    if acao in {"adicionar_playlist", "adicionar_a_playlist"}:
        return {
            "intent": "PLAYLIST_ADD",
            "params": {
                "nome_playlist": str(cmd.get("playlist") or cmd.get("alvo") or alvo),
                "target": destino,
            },
        }
    if acao in {"close_tab", "close_specific_tab"}:
        return {
            "intent": "CLOSE_TAB",
            "params": {"alvo": alvo, "target": destino},
        }
    if acao in {"volume_up", "volume_down", "volume_set", "set_volume", "volume_mute", "mute"}:
        modo = {
            "volume_up": "up", "volume_down": "down", "volume_set": "set",
            "set_volume": "set", "volume_mute": "mute", "mute": "mute",
        }[acao]
        return {
            "intent": "VOLUME",
            "params": {
                "acao": modo,
                "nivel_volume": cmd.get("nivel", cmd.get("level", cmd.get("value", alvo))),
                "target": destino,
            },
        }
    return None


def executar_comandos_json(
    ctx: Dict[str, Any],
    texto: str,
    comandos: List[Dict[str, Any]],
    fala_limpa_original: str,
    tipo_interacao: str,
    fala_ja_emitida: bool,
    fala_emitida_por_acao: bool,
    fala_salva_no_inicio: bool,
) -> Dict[str, Any]:
    """Executa ações JSON usando o contexto compartilhado da Laylay."""
    mensagens = _get(ctx, "messages")
    salvar_memoria = _get(ctx, "salvar_memoria")
    listar_abas_chrome = _get(ctx, "listar_abas_chrome")
    listar_programas_abertos = _get(ctx, "listar_programas_abertos")
    executar_intencao = _get(ctx, "executar_intencao")
    _executar_exec = _get(ctx, "_executar_exec")
    processar_comando_deterministico = _get(ctx, "processar_comando_deterministico")
    _autorizar_acao_pratica = _get(ctx, "_autorizar_acao_pratica")

    erros_execucao: List[str] = []
    if not isinstance(comandos, list):
        comandos = []

    def _extrair_alvo(cmd: dict) -> str:
        for k in ("alvo", "url", "app", "query", "nome"):
            v = cmd.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
        return ""

    _MENCOES_PC_B = ["pc b", "pc_b", "computador b", "no b", "pro b", "pra b"]
    _usuario_pediu_pc_b = any(m in texto.lower() for m in _MENCOES_PC_B)

    if _usuario_pediu_pc_b:
        for _cmd in comandos:
            if isinstance(_cmd, dict) and not _cmd.get("target"):
                if str(_cmd.get("acao", "")).strip() in {"open_url", "youtube_search", "youtube_control", "open_app", "close_app", "organizar_desktop", "capturar_tela", "volume_up", "volume_down", "volume_set", "volume_mute", "parar_midia", "tocar_playlist", "close_tab", "close_specific_tab", "notificar", "criar_pasta", "criar_arquivo", "deletar_item"}:
                    _cmd["target"] = "pc_b"
        print(f"🎯 [PC B] Target injetado em {len(comandos)} comando(s) — usuário pediu PC B.")

    if not comandos and processar_comando_deterministico and processar_comando_deterministico(texto, "pos-ia-0-comandos"):
        return {"erros": [], "fala_emitida_por_acao": False, "fala_ja_emitida": fala_ja_emitida, "fala_salva_no_inicio": fala_salva_no_inicio}

    for cmd in comandos:
        if not isinstance(cmd, dict):
            continue
        # Alguns modelos usam ``intent`` dentro da lista de comandos, apesar
        # do contrato histórico chamar o campo de ``acao``. Ambos precisam
        # chegar ao mesmo executor; ignorar ``intent`` marcava sucesso vazio.
        acao = str(cmd.get("acao") or cmd.get("intent") or "").strip().lower()
        if not acao or acao.upper() in {"", "NENHUM", "NONE"}:
            continue
        alvo_raw = _extrair_alvo(cmd)
        alvo = re.sub(r'\[.*?\]\((.*?)\)', r'\1', str(alvo_raw or "")).replace("[", "").replace("]", "").strip('"\' ')

        intencao_canonica = adaptar_acao_json_para_intencao(cmd, alvo)
        if intencao_canonica is not None:
            if not callable(executar_intencao):
                erros_execucao.append(f"executor canônico indisponível para a ação '{acao}'.")
                continue
            try:
                if executar_intencao(intencao_canonica, texto):
                    fala_emitida_por_acao = True
                else:
                    erros_execucao.append(f"intenção canônica não executada: {intencao_canonica.get('intent')}")
            except Exception as erro_intencao:
                erros_execucao.append(
                    f"intenção {intencao_canonica.get('intent')}: {type(erro_intencao).__name__} — {erro_intencao}"
                )
            continue

        if acao == "verificar_programas" and callable(listar_programas_abertos):
            lista = listar_programas_abertos()
            info_txt = "System: Programas/janelas abertas no momento: " + ", ".join(lista[:25]) if lista else "System: Nenhum programa com janela visível encontrado no momento."
            if isinstance(mensagens, list):
                mensagens.append({"role": "user", "content": info_txt + "\n\n[RESPOSTA OBRIGATÓRIA EM JSON: {\"fala\": \"...\", \"comandos\": [...]}]"})

        elif acao == "verificar_abas" and callable(listar_abas_chrome):
            abas = listar_abas_chrome(timeout_s=5.0)
            info_txt = "System: Abas abertas no Chrome:\n" + "\n".join([f"{i}. {str(a.get('titulo') or '')[:60]} | {str(a.get('url') or '')[:80]}" for i, a in enumerate(abas[:20], 1)]) if abas else "System: Nenhuma aba encontrada no Chrome (extensão pode estar desconectada)."
            if isinstance(mensagens, list):
                mensagens.append({"role": "user", "content": info_txt + "\n\n[RESPOSTA OBRIGATÓRIA EM JSON: {\"fala\": \"...\", \"comandos\": [...]}]"})

        else:
            try:
                if callable(_executar_exec):
                    if acao.lower() in {"youtube", "youtube_search", "tocar_playlist", "youtube_play"} and callable(_autorizar_acao_pratica):
                        decisao = _autorizar_acao_pratica(acao, texto, origem="json_legacy")
                        if not bool(decisao.get("permitido")):
                            print(f"🎵 [AUTONOMIA] ação legada bloqueada: {acao} ({decisao.get('motivo')}).")
                            continue
                    executou_legado = bool(_executar_exec(acao.upper(), alvo))
                    if not executou_legado:
                        erros_execucao.append(
                            f"ação não reconhecida ou não executada: '{acao}' (alvo='{alvo}')"
                        )
                else:
                    erros_execucao.append(f"executor indisponível para a ação '{acao}'.")
            except Exception as ef:
                erros_execucao.append(f"ação '{acao}' (alvo='{alvo}'): {type(ef).__name__} — {ef}")

    if callable(salvar_memoria):
        salvar_memoria()

    return {
        "erros": erros_execucao,
        "fala_emitida_por_acao": fala_emitida_por_acao,
        "fala_ja_emitida": fala_ja_emitida,
        "fala_salva_no_inicio": fala_salva_no_inicio,
    }
