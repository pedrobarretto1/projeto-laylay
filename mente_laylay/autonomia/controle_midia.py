"""Execucao de controle de midia da Laylay.

Este modulo nao guarda estado proprio. Ele recebe o contexto vivo do roteador
para continuar funcionando como parte da mesma mente.
"""

from __future__ import annotations

import ctypes
import re
import time
from typing import Any, Callable, Dict

from mente_laylay.personalidade.falas_variadas import (
    escolher as _escolher_fala_variada,
    fala_de_confirmacao as _fala_de_confirmacao_variada,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao
from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_llm
from mente_laylay.personalidade.higiene_fala import limpar_titulo_musical_para_fala


VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3


def _get(ctx: Dict[str, Any], nome: str, default=None):
    return ctx.get(nome, default)


def executar_controle_midia_nativo(
    command: str,
    *,
    ctypes_module: Any = ctypes,
    sleep_cb: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] = print,
) -> bool:
    """Envia teclas globais de mídia preservando a semântica legada."""
    cmd = str(command or "").strip().lower()
    try:
        if cmd == "pause_play":
            log("🎵 [MIDIA:NATIVO] tecla play/pause")
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
            return True
        if cmd == "next":
            log("🎵 [MIDIA:NATIVO] tecla next")
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)
            return True
        if cmd == "prev":
            log("🎵 [MIDIA:NATIVO] tecla previous x2")
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            sleep_cb(0.18)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            return True
        if cmd == "replay":
            log("🎵 [MIDIA:NATIVO] replay via previous")
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes_module.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            return True
    except Exception as erro:
        log(f"⚠️ [MIDIA NATIVA] falha ao executar '{cmd}': {erro}")
    return False


def executar_media_control(
    params: Dict[str, Any],
    texto_original: str,
    destino_val: str,
    ctx: Dict[str, Any],
    *,
    marcar_resultado: Callable[[str, bool | None], None],
    falar_por_status: Callable[..., None],
    ctx_fala: Callable[[], Dict[str, Any]],
) -> bool:
    """Executa MEDIA_CONTROL com validacao, logs e fala contextual."""
    falar = _get(ctx, "falar_com_lipsync")
    navegador_operacoes = _get(ctx, "_registro_navegador_operacoes_runtime")
    navegador_leitura = _get(ctx, "_registro_navegador_leitura_runtime")
    ajustar_volume = _get(ctx, "ajustar_volume_sistema")
    _enviar_pc_b = _get(ctx, "_enviar_pc_b")
    executar_controle_midia_nativo = _get(ctx, "_executar_controle_midia_nativo")
    musica_estado_get = _get(ctx, "_musica_estado_get")
    musica_estado_set = _get(ctx, "_musica_estado_set")

    acao = str(params.get("acao") or params.get("command") or "").strip().lower()
    platform = str(params.get("platform") or params.get("site") or "").strip().lower()
    nivel_bruto = params.get("nivel_volume")
    queue_item_id = str(params.get("queue_item_id") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", queue_item_id):
        queue_item_id = ""
    queue_index = params.get("queue_index")
    if isinstance(queue_index, bool):
        queue_index = None
    try:
        queue_index = int(queue_index) if queue_index is not None else None
    except (TypeError, ValueError):
        queue_index = None
    if queue_index is not None and not 0 <= queue_index <= 999:
        queue_index = None
    musica_operacoes = _get(ctx, "_registro_musica_operacoes_runtime")
    estado_reproducao = (
        musica_operacoes.estado() if musica_operacoes is not None else {}
    )
    alvo_musical = platform in {
        "music", "musica", "música", "youtube", "youtube_music",
    }
    playlist_ativa = bool(
        str((estado_reproducao or {}).get("playlist_ativa") or "").strip()
    )
    confirmado_execucao: bool | None = None
    detalhe_execucao = ""

    if acao in {"status", "now_playing", "qual_musica", "faixa_atual"}:
        # Esta rota é deliberadamente somente leitura. Em particular, ela não
        # chega a ``_executar_cmd_midia`` nem às teclas globais do Windows.
        musica_leitura = _get(ctx, "_registro_musica_leitura_runtime")
        try:
            estado_leitura = dict(
                musica_leitura.estado() if musica_leitura is not None else {}
            )
        except Exception:
            estado_leitura = {}
        titulo = limpar_titulo_musical_para_fala(
            str(estado_leitura.get("musica_atual_titulo") or "").strip()
        )
        status_player = str(
            estado_leitura.get("musica_atual_status") or ""
        ).strip().casefold()
        if not titulo:
            try:
                faixa = dict(
                    musica_operacoes.faixa_atual()
                    if musica_operacoes is not None else {}
                )
            except Exception:
                faixa = {}
            titulo = limpar_titulo_musical_para_fala(
                str(faixa.get("title") or "").strip()
            )

        if titulo:
            if status_player in {"pausada", "pausado", "paused", "pause"}:
                fala_status = f"A faixa atual é {titulo}, mas ela está pausada."
            elif status_player in {"tocando", "playing", "audivel", "audível"}:
                fala_status = f"Está tocando {titulo}."
            else:
                fala_status = f"A faixa atual registrada é {titulo}."
            try:
                marcar_resultado(
                    "midia_status_consultado",
                    executou=True,
                    confirmado=True,
                    alvo_resolvido=titulo,
                )
            except TypeError:
                marcar_resultado("midia_status_consultado", True)
            if callable(falar):
                falar(fala_status, "calma", 1)
            return True

        try:
            marcar_resultado(
                "faixa_atual_indisponivel", executou=True, confirmado=False,
            )
        except TypeError:
            marcar_resultado("faixa_atual_indisponivel", False)
        if callable(falar):
            falar(
                "Não consegui confirmar qual faixa está tocando agora.",
                "calma",
                1,
            )
        return False

    def _log_midia(etapa: str, msg: str) -> None:
        try:
            print(f"🎵 [MIDIA:{str(etapa or '').upper()}] {msg}")
        except Exception:
            pass

    def _aba_atual_midia() -> dict:
        try:
            return navegador_leitura.aba_ativa() if navegador_leitura is not None else {}
        except Exception as e:
            _log_midia("ABA", f"falha ao consultar aba: {e}")
            return {}

    def _aba_compativel_youtube(info_aba: dict) -> bool:
        if not isinstance(info_aba, dict):
            return False
        url = str(info_aba.get("url") or "").casefold()
        titulo = str(info_aba.get("title") or "").casefold()
        return bool(
            "youtube.com" in url
            or "youtu.be" in url
            or "youtube" in titulo
        )

    def _preferir_chrome_para_midia() -> bool:
        info_aba = _aba_atual_midia()
        url = str(info_aba.get("url") or "").lower() if isinstance(info_aba, dict) else ""
        preferir = bool(
            navegador_operacoes is not None
            and _aba_compativel_youtube(info_aba)
        )
        _log_midia("ROTA", f"acao={acao} platform={platform or '-'} playlist={playlist_ativa} url='{url[:80]}' preferir_chrome={preferir}")
        return preferir

    def _controlar_chrome_com_evidencia(cmd_exec: str) -> bool:
        nonlocal confirmado_execucao, detalhe_execucao
        if navegador_operacoes is None:
            confirmado_execucao = False
            detalhe_execucao = "navegador_indisponivel"
            return False
        tab_id = (estado_reproducao or {}).get("tab_id")
        if not isinstance(tab_id, int) or isinstance(tab_id, bool):
            aba = _aba_atual_midia()
            tab_id = (
                aba.get("tabId")
                if _aba_compativel_youtube(aba)
                else None
            )
            if not isinstance(tab_id, int) or isinstance(tab_id, bool):
                tab_id = None
        controlar_detalhado = getattr(
            navegador_operacoes, "controlar_youtube_detalhado", None,
        )
        if callable(controlar_detalhado):
            try:
                retorno = controlar_detalhado(
                    cmd_exec,
                    tab_id=tab_id if isinstance(tab_id, int) else None,
                    queue_item_id=(
                        queue_item_id if cmd_exec == "queue_select" else ""
                    ),
                    queue_index=(
                        queue_index if cmd_exec == "queue_select" else None
                    ),
                )
            except TypeError:
                if cmd_exec == "queue_select":
                    confirmado_execucao = False
                    detalhe_execucao = "queue_select_unsupported"
                    return False
                try:
                    retorno = controlar_detalhado(
                        cmd_exec,
                        tab_id=tab_id if isinstance(tab_id, int) else None,
                    )
                except TypeError:
                    retorno = controlar_detalhado(cmd_exec)
            dados = dict(retorno) if isinstance(retorno, dict) else {}
            ok = bool(dados.get("ok"))
            confirmado = dados.get("confirmado")
            confirmado_execucao = (
                bool(confirmado) if confirmado is not None else None
            )
            detalhe_execucao = str(
                dados.get("message") or dados.get("status") or ""
            ).strip()
            return ok
        try:
            ok = bool(navegador_operacoes.controlar_youtube(
                cmd_exec,
                tab_id=tab_id if isinstance(tab_id, int) else None,
            ))
        except TypeError:
            ok = bool(navegador_operacoes.controlar_youtube(cmd_exec))
        confirmado_execucao = ok
        detalhe_execucao = "confirmacao_legada" if ok else "falha_execucao"
        return ok

    def _executar_cmd_midia(cmd_exec: str) -> bool:
        nonlocal confirmado_execucao, detalhe_execucao
        _log_midia("ENVIO", f"cmd={cmd_exec} destino={destino_val or 'local'} playlist={playlist_ativa}")
        if cmd_exec == "queue_select":
            if (
                not queue_item_id or queue_index is None
                or not 0 <= queue_index <= 7
            ):
                confirmado_execucao = False
                return False
            return _controlar_chrome_com_evidencia(cmd_exec)
        if cmd_exec == "playlist_queue_select":
            if (
                not queue_item_id or queue_index is None
                or musica_operacoes is None
            ):
                confirmado_execucao = False
                detalhe_execucao = "fila_playlist_indisponivel"
                return False
            selecionar = getattr(
                musica_operacoes, "selecionar_faixa_fila", None,
            )
            if not callable(selecionar):
                confirmado_execucao = False
                detalhe_execucao = "queue_select_unavailable"
                return False
            try:
                resultado = dict(selecionar(queue_item_id, queue_index) or {})
            except Exception as erro:
                confirmado_execucao = False
                detalhe_execucao = f"falha_selecao_fila:{type(erro).__name__}"
                return False
            ok = bool(resultado.get("ok"))
            confirmado_execucao = (
                resultado.get("confirmed") is True if ok else False
            )
            detalhe_execucao = str(resultado.get("status") or "").strip()
            return ok
        if destino_val == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "youtube_control", "command": cmd_exec})
            confirmado_execucao = None
            return True
        if destino_val == "ambos":
            ok_local = False
            if cmd_exec == "skip_ad" and navegador_operacoes is not None:
                ok_local = _controlar_chrome_com_evidencia(cmd_exec)
            elif alvo_musical and navegador_operacoes is not None:
                ok_local = _controlar_chrome_com_evidencia(cmd_exec)
                confirmado_execucao = None
            elif _preferir_chrome_para_midia() and navegador_operacoes is not None:
                ok_local = _controlar_chrome_com_evidencia(cmd_exec)
                # O destino remoto continua sem confirmação conjunta; não
                # declaramos o comando inteiro confirmado só pelo PC local.
                confirmado_execucao = None
            elif callable(executar_controle_midia_nativo):
                native_cmd = "pause_play" if cmd_exec in {"pause", "play"} else cmd_exec
                ok_local = bool(executar_controle_midia_nativo(native_cmd))
                confirmado_execucao = None
            elif navegador_operacoes is not None:
                ok_local = _controlar_chrome_com_evidencia(cmd_exec)
                confirmado_execucao = None
            if callable(_enviar_pc_b):
                _enviar_pc_b({"action": "youtube_control", "command": cmd_exec})
            return ok_local
        if cmd_exec == "skip_ad" and navegador_operacoes is not None:
            return _controlar_chrome_com_evidencia(cmd_exec)
        if alvo_musical and navegador_operacoes is not None:
            # Um comando do painel musical pertence ao player musical
            # canônico, não à sessão de mídia que recebeu foco por último no
            # Windows. Se a extensão recusar o alvo, a falha é terminal: uma
            # tecla global poderia tocar Prime Video, Netflix ou outro player.
            return _controlar_chrome_com_evidencia(cmd_exec)
        if playlist_ativa and navegador_operacoes is not None:
            return _controlar_chrome_com_evidencia(cmd_exec)
        if _preferir_chrome_para_midia() and navegador_operacoes is not None:
            return _controlar_chrome_com_evidencia(cmd_exec)
        if callable(executar_controle_midia_nativo):
            native_cmd = "pause_play" if cmd_exec in {"pause", "play"} else cmd_exec
            confirmado_execucao = None
            return bool(executar_controle_midia_nativo(native_cmd))
        if navegador_operacoes is not None:
            return _controlar_chrome_com_evidencia(cmd_exec)
        return False

    _log_midia("ENTRADA", f"acao={acao or '-'} platform={platform or '-'} params={params}")
    cmd = ""
    if acao in {"resume", "retomar", "retoma", "continuar", "continua", "despausa", "despausar"}:
        cmd = "play"
    elif acao in {"pause", "pausa"}:
        cmd = "pause"
    elif acao in {"pause_play", "play_pause", "toggle", "tocar"}:
        cmd = "pause_play"
    elif acao in {"play"}:
        cmd = "play"
    elif acao in {"next", "proxima", "próxima"}:
        cmd = "next"
    elif acao in {"prev", "previous", "anterior"}:
        cmd = "prev"
    elif acao in {"replay", "voltar", "reiniciar"}:
        cmd = "replay"
    elif acao in {"repeat_toggle", "repetir", "repeticao", "repetição", "loop"}:
        cmd = "repeat_toggle"
    elif acao in {"skip_ad", "pular_anuncio", "pular_anúncio"}:
        cmd = "skip_ad"
    elif acao in {"queue_select", "selecionar_fila"}:
        cmd = "queue_select"
    elif acao in {"playlist_queue_select", "selecionar_fila_playlist"}:
        cmd = "playlist_queue_select"

    if nivel_bruto not in (None, ""):
        try:
            nivel = int(float(str(nivel_bruto).replace(",", ".")))
        except Exception:
            nivel = None
        if nivel is not None:
            nivel = max(0, min(100, nivel))
            ok_volume = False
            if destino_val == "pc_b" and callable(_enviar_pc_b):
                _enviar_pc_b({"action": "set_volume", "level": nivel})
                ok_volume = True
            elif callable(ajustar_volume):
                ajustar_volume(nivel)
                ok_volume = True
            else:
                if callable(falar):
                    falar(_escolher_fala_variada([
                        "Não consegui mexer no volume agora.",
                        "O volume escapou de mim desta vez.",
                        "Tentei ajustar o volume, mas não tive acesso ao controle.",
                    ]), "calma", 1)
                return False
            marcar_resultado("volume_ajustado" if ok_volume else "falha_execucao", ok_volume)
            falar_por_status(
                "volume_ajustado" if ok_volume else "falha_execucao",
                f"Volume em {nivel}%." if ok_volume else "Tentei ajustar o volume, mas o controle não respondeu.",
                alvo="volume",
            )
            return bool(ok_volume)

    if not cmd:
        if callable(falar):
            falar(_escolher_fala_variada(["Não entendi o controle de mídia. Fala de novo.", "Repete o comando de mídia.", "Esse controle de mídia escapou de mim."]), "calma", 1)
        return True

    if playlist_ativa and cmd == "next" and musica_operacoes is not None:
        _log_midia("PLAYLIST", "tentando avancar pela playlist interna")
        ok = bool(musica_operacoes.avancar_proxima())
        _log_midia("RESULTADO", f"playlist_next ok={ok}")
        if callable(falar):
            fala = _escolher_fala_variada([
                "Próxima faixa. Bora.",
                "Pulando pra seguinte.",
                "Trocando a música agora.",
            ]) if ok else _escolher_fala_variada([
                "Tentei puxar a próxima da playlist, mas ela não foi.",
                "A próxima faixa não respondeu agora.",
            ])
            falar(fala, "debochada" if ok else "irritada", 2)
        marcar_resultado("midia_next_playlist" if ok else "falha_execucao", ok)
        return bool(ok)

    if playlist_ativa and cmd == "prev" and musica_operacoes is not None:
        _log_midia("PLAYLIST", "tentando voltar pela playlist interna")
        ok = bool(musica_operacoes.voltar_anterior())
        _log_midia("RESULTADO", f"playlist_prev ok={ok}")
        if callable(falar):
            fala = _escolher_fala_variada([
                "Voltando uma faixa.",
                "Dei um passo atrás na playlist.",
                "Faixa anterior voltando agora.",
            ]) if ok else _escolher_fala_variada([
                "Tentei voltar a playlist, mas ela não cedeu.",
                "Não consegui confirmar a faixa anterior agora.",
            ])
            falar(fala, "debochada" if ok else "irritada", 2)
        marcar_resultado("midia_prev_playlist" if ok else "falha_execucao", ok)
        return bool(ok)

    url_antes_troca = ""
    if cmd in {"next", "prev"}:
        if callable(musica_estado_get):
            try:
                url_antes_troca = str(
                    musica_estado_get("musica_atual_url", "") or ""
                ).strip()
            except Exception:
                url_antes_troca = ""
        if not url_antes_troca and musica_operacoes is not None:
            try:
                faixa_antes = dict(musica_operacoes.faixa_atual() or {})
                url_antes_troca = str(faixa_antes.get("url") or "").strip()
            except Exception:
                url_antes_troca = ""

    ok_execucao = _executar_cmd_midia(cmd)
    _log_midia("RESULTADO", f"cmd={cmd} ok_envio={ok_execucao}")
    if (
        ok_execucao
        and callable(musica_estado_set)
        and cmd in {"next", "prev"}
    ):
        # A confirmação do controle prova que o player aceitou ``next`` ou
        # ``prev``; ela não prova que a identidade da nova faixa já chegou.
        # Guardamos a origem para que uma etapa dependente só aceite uma URL
        # diferente, mesmo quando o evento do player corre em paralelo.
        musica_estado_set("musica_troca_origem_url", url_antes_troca)
        musica_estado_set("musica_atual_status", "troca_nao_confirmada")
    if (
        ok_execucao
        and confirmado_execucao is True
        and callable(musica_estado_set)
        and cmd in {"pause", "play"}
    ):
        # A extensão já confirmou o estado final. Publique a observação na
        # mesma mente antes de liberar o próximo turno; sem isso, uma consulta
        # imediata ainda enxergava o snapshot anterior do player.
        musica_estado_set(
            "musica_atual_status",
            "pausada" if cmd == "pause" else "tocando",
        )
    if callable(falar):
        if cmd in {"pause", "play", "pause_play"}:
            chave_midia = "play" if cmd == "play" else ("pause" if cmd == "pause" else "pause")
        else:
            chave_midia = (
                "prev" if cmd == "prev"
                else "replay" if cmd in {"replay", "repeat_toggle"}
                else cmd
            )
        if ok_execucao:
            if confirmado_execucao is True:
                fala_midia = _fala_de_confirmacao_variada(
                    chave_midia,
                    fallback="Feito.",
                    contexto=ctx_fala(),
                    texto_usuario=texto_original,
                )
            else:
                falas_envio = {
                    "next": ["Mandei passar pra próxima.", "Pedi a próxima faixa.", "Comando de próxima faixa enviado."],
                    "prev": ["Mandei voltar pra anterior.", "Pedi a faixa anterior.", "Comando de faixa anterior enviado."],
                    "replay": ["Mandei recomeçar essa faixa.", "Pedi pra tocar essa desde o começo."],
                    "repeat_toggle": [
                        "Mandei alternar a repetição dessa faixa.",
                        "Pedi para mudar o modo de repetição.",
                    ],
                    "pause": ["Mandei pausar.", "Pedi uma pausa na música."],
                    "play": ["Mandei retomar.", "Pedi pra música continuar."],
                    "pause_play": ["Mandei alternar a reprodução.", "Enviei o comando de tocar ou pausar."],
                }
                fala_midia = _escolher_fala_variada(
                    falas_envio.get(cmd, ["Enviei o comando de mídia."])
                )
            contrato = ResultadoAcao(
                intent="MEDIA_CONTROL",
                status=f"midia_{cmd}",
                alvo="musica",
                params={"acao": cmd},
                executou=True,
                confirmado=confirmado_execucao,
                texto_usuario=texto_original,
                detalhe=detalhe_execucao,
            )
            plano = planejar_resposta_acao(
                contrato,
                fala_midia,
                emocao_preferida="debochada",
                nivel_preferido=2,
            )
            confirmacao = personalizar_confirmacao_llm(
                contrato,
                plano.fala,
                classe=plano.classe,
                emocao=plano.emocao,
                nivel=plano.nivel,
                enviar_mensagem=_get(ctx, "enviar_mensagem"),
                contexto=ctx_fala(),
            )
            falar(confirmacao.fala, confirmacao.emocao, confirmacao.nivel)
        else:
            contrato_falha = ResultadoAcao(
                    intent="MEDIA_CONTROL",
                    status="falha_execucao",
                    alvo="midia",
                    executou=False,
                    confirmado=False,
                    texto_usuario=texto_original,
                )
            plano = planejar_resposta_acao(
                contrato_falha,
                (
                    "O navegador não confirmou o controle de mídia; "
                    "não repeti o comando."
                    if detalhe_execucao
                    else "Tentei mexer na mídia, mas não consegui confirmar o caminho."
                ),
            )
            confirmacao = personalizar_confirmacao_llm(
                contrato_falha,
                plano.fala,
                classe=plano.classe,
                emocao=plano.emocao,
                nivel=plano.nivel,
                enviar_mensagem=_get(ctx, "enviar_mensagem"),
                contexto=ctx_fala(),
            )
            falar(confirmacao.fala, confirmacao.emocao, confirmacao.nivel)
    marcar_resultado(
        f"midia_{cmd}" if ok_execucao else "falha_execucao",
        ok_execucao,
        confirmado=confirmado_execucao if ok_execucao else False,
        detalhe=detalhe_execucao,
    )
    return bool(ok_execucao)
