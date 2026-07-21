"""Aprendizado de rotina, musica e feedback contextual da Laylay."""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple


def carregar_rotinas_aprendidas(arquivo: str) -> Dict[str, Any]:
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                data = json.load(f)
                dados = data.get("dados", {})
                if isinstance(dados, dict):
                    return dados
        except Exception:
            pass
    return {}


def salvar_rotinas_aprendidas(arquivo: str, dados_diarios: Dict[str, Any]) -> None:
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "dados": dados_diarios,
                    "ultima_atualizacao": datetime.now().isoformat(),
                },
                f,
                ensure_ascii=False,
            )
    except Exception:
        pass


def logar_atividade_atual(
    arquivo_rotinas: str,
    dados_diarios: Dict[str, Any],
    ultimo_log: float,
    contexto_sistema: Dict[str, Any],
    obter_janela_ativa: Callable[[], Any],
    salvar_cb: Optional[Callable[[], None]] = None,
    registrar_observacao_cb: Optional[Callable[[str, str, str], Any]] = None,
    intervalo_s: int = 300,
    limite_por_bloco: int = 20,
) -> float:
    agora = time.time()
    if agora - float(ultimo_log or 0.0) < intervalo_s:
        return ultimo_log

    try:
        win = obter_janela_ativa()
        title = (win.title if win else "").strip()[:80]
        assunto = str(contexto_sistema.get("assunto") or "").strip()
        hora = datetime.now().strftime("%H:00")
        if callable(registrar_observacao_cb) and (title or assunto):
            try:
                registrar_observacao_cb(title, assunto, hora)
            except Exception:
                pass

        bloco = dados_diarios.setdefault(hora, {"janelas": [], "assuntos": []})
        if title:
            bloco["janelas"].append(title)
        if assunto:
            bloco["assuntos"].append(assunto)

        bloco["janelas"] = bloco["janelas"][-limite_por_bloco:]
        bloco["assuntos"] = bloco["assuntos"][-limite_por_bloco:]

        if len(bloco["janelas"]) % 6 == 0:
            if callable(salvar_cb):
                salvar_cb()
            else:
                salvar_rotinas_aprendidas(arquivo_rotinas, dados_diarios)
    except Exception:
        pass

    return agora


def carregar_feedback_pesos(arquivo: str) -> Dict[str, int]:
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, dict):
                    return {str(k): int(v) for k, v in dados.items()}
        except Exception:
            pass
    return {}


def salvar_feedback_pesos(arquivo: str, pesos: Dict[str, int]) -> None:
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(pesos, f, ensure_ascii=False)
    except Exception:
        pass


def rotina_chave_feedback(hora: str, app: str) -> str:
    return f"{hora}:{app[:40].lower().strip()}"


def rotina_app_bloqueado(pesos: Dict[str, int], hora: str, app: str, limite_rejeicao: int) -> bool:
    return int(pesos.get(rotina_chave_feedback(hora, app), 0)) <= -int(limite_rejeicao)


def registrar_feedback_rotina(
    pendente: Optional[Dict[str, Any]],
    pesos: Dict[str, int],
    aceito: bool,
    falar_cb: Optional[Callable[[str, str, int], None]] = None,
    abrir_programa_cb: Optional[Callable[[str], Any]] = None,
    salvar_cb: Optional[Callable[[Dict[str, int]], None]] = None,
    cooldown_min: int = 60,
    limite_rejeicao: int = 3,
) -> Tuple[Dict[str, int], Optional[Dict[str, Any]], float]:
    if not pendente:
        return pesos, None, 0.0

    app = str(pendente.get("app") or "").strip()
    hora = str(pendente.get("hora") or "").strip()
    chave = rotina_chave_feedback(hora, app)
    nome_amigavel = app.split(" - ")[0].strip().title() or app.title()
    pesos = dict(pesos or {})
    cooldown_ate = 0.0

    if aceito:
        pesos[chave] = int(pesos.get(chave, 0)) + 1
        if callable(falar_cb):
            falar_cb(f"Abrindo {nome_amigavel} pra voce.", "calma", 1)
        if callable(abrir_programa_cb):
            try:
                abrir_programa_cb(app)
            except Exception:
                pass
    else:
        pesos[chave] = int(pesos.get(chave, 0)) - 1
        cooldown_ate = time.time() + (int(cooldown_min) * 60)
        if int(pesos[chave]) <= -int(limite_rejeicao):
            if callable(falar_cb):
                falar_cb(f"Ok, aprendi. Nao vou mais sugerir {nome_amigavel} neste horario.", "calma", 1)
        elif callable(falar_cb):
            falar_cb("Ok, nao abro.", "calma", 1)

    if callable(salvar_cb):
        salvar_cb(pesos)
    return pesos, None, cooldown_ate


def carregar_musica_dados(arquivo: str) -> Dict[str, Any]:
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if not isinstance(raw, dict):
                    return {}
                normalizado: Dict[str, Any] = {}
                for hora, valor in raw.items():
                    chave = str(hora or "").strip()
                    if not chave:
                        continue
                    if isinstance(valor, dict):
                        musicas = valor.get("musicas") or valor.get("tracks") or []
                        dias = valor.get("dias") or valor.get("dates") or []
                        if not isinstance(musicas, list):
                            musicas = []
                        if not isinstance(dias, list):
                            dias = []
                        normalizado[chave] = {
                            "musicas": [str(m).strip() for m in musicas if str(m).strip()],
                            "dias": [str(d).strip() for d in dias if str(d).strip()],
                        }
                    elif isinstance(valor, list):
                        normalizado[chave] = {
                            "musicas": [str(m).strip() for m in valor if str(m).strip()],
                            "dias": [],
                        }
                return normalizado
        except Exception:
            pass
    return {}


def salvar_musica_dados(arquivo: str, dados_diarios: Dict[str, Any]) -> None:
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados_diarios, f, ensure_ascii=False)
    except Exception:
        pass


def carregar_musica_feedback_pesos(arquivo: str) -> Dict[str, int]:
    return carregar_feedback_pesos(arquivo)


def salvar_musica_feedback_pesos(arquivo: str, pesos: Dict[str, int]) -> None:
    salvar_feedback_pesos(arquivo, pesos)


def musica_chave_feedback(hora: str, musica: str) -> str:
    return f"{hora}:{musica[:40].lower().strip()}"


def musica_bloqueada(pesos: Dict[str, int], hora: str, musica: str, limite_rejeicao: int) -> bool:
    return int(pesos.get(musica_chave_feedback(hora, musica), 0)) <= -int(limite_rejeicao)


def registrar_historico_musica(
    dados_diarios: Dict[str, Any],
    musica: str,
    salvar_cb: Optional[Callable[[], None]] = None,
    limite_por_hora: int = 100,
) -> None:
    if not musica or len(str(musica)) < 3:
        return

    hora_atual = datetime.now().strftime("%H:00")
    dia_atual = datetime.now().date().isoformat()
    if hora_atual not in dados_diarios or not isinstance(dados_diarios.get(hora_atual), dict):
        dados_diarios[hora_atual] = {"musicas": [], "dias": []}

    musica = str(musica).replace("- YouTube", "").strip()
    bloco = dados_diarios[hora_atual]
    bloco["musicas"].append(musica)
    if dia_atual not in bloco["dias"]:
        bloco["dias"].append(dia_atual)

    if len(bloco["musicas"]) > limite_por_hora:
        bloco["musicas"] = bloco["musicas"][-limite_por_hora:]

    if callable(salvar_cb):
        salvar_cb()


def normalizar_confirmacao_texto(texto: str) -> str:
    bruto = str(texto or "").strip().lower()
    sem_acento = unicodedata.normalize("NFKD", bruto)
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    sem_acento = re.sub(r"[^\w\s]", " ", sem_acento)
    return re.sub(r"\s+", " ", sem_acento).strip()


def classificar_confirmacao_local(texto: str) -> Optional[bool]:
    t = normalizar_confirmacao_texto(texto)
    if not t:
        return None
    if any(p in t for p in [
        "estilo diferente", "outro estilo", "outra vibe", "outra pegada",
        "uma diferente", "outra musica", "outra música",
        "tem outra", "manda outra", "quero outra",
        "nao essa", "não essa", "essa nao", "essa não", "diferente dessa",
    ]):
        return None
    sim_frases = {
        "sim", "sim pode", "pode", "pode sim", "quero", "quero sim", "eu quero",
        "eu quero sim", "quero ouvir", "quero ver", "quero essa", "quero ele",
        "claro", "bora", "vai", "vai la", "manda", "manda ver",
        "ok", "beleza", "blz", "coloca", "toca", "da play", "play",
        "abre", "abre sim", "pode abrir", "pode colocar",
        "pode falar", "pode fala", "pode me falar", "pode me fala",
        "fala", "fala sim", "me fala", "me fala sim",
    }
    nao_frases = {
        "nao", "nao precisa", "nao agora", "agora nao", "deixa",
        "deixa quieto", "esquece", "para", "cancela", "pode nao",
        "melhor nao", "nem", "nope", "precisa nao", "precisa não",
        "não precisa", "agora não", "pode não",
    }
    if t in sim_frases:
        return True
    if t in nao_frases:
        return False
    tokens = set(t.split())
    if {"quero", "sim"} <= tokens or {"pode", "sim"} <= tokens:
        return True
    if "nao" in tokens and ("agora" in tokens or "precisa" in tokens or "quero" in tokens):
        return False
    return None


def classificar_confirmacao_contextual(
    texto: str,
    sugestao: str,
    interpretar_confirmacao_llm: Optional[Callable[[str, str], Any]] = None,
) -> Optional[bool]:
    local = classificar_confirmacao_local(texto)
    if local is not None:
        return local
    if len(str(texto or "").strip()) <= 90 and callable(interpretar_confirmacao_llm):
        try:
            return interpretar_confirmacao_llm(texto, sugestao)
        except Exception:
            return None
    return None


def analisar_e_sugerir_rotina(
    dados_diarios: Dict[str, Any],
    pesos: Dict[str, int],
    ultima_sugestao: float,
    sugestao_pendente: Optional[Dict[str, Any]],
    contexto_aponta_descanso: Callable[[], bool],
    agendar_fala_proativa: Callable[[str, str, str, int], Any],
    rotinas_aprendidas_min_dias: int,
    bloqueio_rejeicao_vezes: int,
) -> Tuple[float, Optional[Dict[str, Any]]]:
    agora = time.time()
    if agora - float(ultima_sugestao or 0.0) < 600:
        return ultima_sugestao, sugestao_pendente
    if contexto_aponta_descanso():
        return ultima_sugestao, sugestao_pendente
    if sugestao_pendente is not None:
        return ultima_sugestao, sugestao_pendente

    dias_com_dados = len(set(k.split(" ")[0] for k in dados_diarios.keys())) if dados_diarios else 0
    if dias_com_dados < rotinas_aprendidas_min_dias:
        return ultima_sugestao, sugestao_pendente

    hora_atual = datetime.now().strftime("%H:00")
    if hora_atual not in dados_diarios:
        return ultima_sugestao, sugestao_pendente

    dados = dados_diarios[hora_atual]
    janelas_comuns: Dict[str, int] = {}
    for j in dados.get("janelas", []):
        j_clean = str(j).lower().strip()
        janelas_comuns[j_clean] = janelas_comuns.get(j_clean, 0) + 1

    if not janelas_comuns:
        return ultima_sugestao, sugestao_pendente

    total_registros = len(dados.get("janelas", []))
    candidatos = sorted(janelas_comuns.items(), key=lambda x: x[1], reverse=True)
    for nome_janela, ocorrencias in candidatos:
        if ocorrencias < total_registros * 0.7:
            break
        if rotina_app_bloqueado(pesos, hora_atual, nome_janela, bloqueio_rejeicao_vezes):
            continue

        nome_amigavel = nome_janela.split(" - ")[0].strip().title()
        nova_pendente = {"app": nome_janela, "hora": hora_atual, "ts": agora}
        agendada = agendar_fala_proativa(
            "rotina",
            f"Voce costuma usar {nome_amigavel} agora. Quer que eu abra isso com aquele jeitinho de quem ja sabe o que voce vai fazer?",
            "calma",
            1,
        )
        if agendada is False:
            return ultima_sugestao, sugestao_pendente
        return agora, nova_pendente

    return ultima_sugestao, sugestao_pendente
