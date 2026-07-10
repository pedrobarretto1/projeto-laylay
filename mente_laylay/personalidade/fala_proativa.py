"""Composição de falas proativas a partir de sinais da mente integrada."""

from __future__ import annotations

import re
import threading
import time
from collections.abc import Callable


class FilaFalaProativa:
    """Une falas proativas próximas para evitar alertas fragmentados."""

    def __init__(self, *, delay: float = 1.0, janela_startup: float = 18.0):
        self.lock = threading.Lock()
        self.buffer = []
        self.timer = None
        self.delay = delay
        self.inicio_sistema = time.time()
        self.janela_startup = janela_startup

    def flush(
        self,
        *,
        compor_fala: Callable[[list], tuple[str, str, int]],
        falar: Callable[[str, str, int], None],
    ) -> None:
        with self.lock:
            itens = list(self.buffer)
            self.buffer = []
            self.timer = None

        if not itens:
            return

        texto, emocao, nivel = compor_fala(itens)
        falar(texto, emocao, nivel)

    def agendar(
        self,
        tipo: str,
        texto: str,
        emocao: str = "calma",
        nivel: int = 1,
        *,
        flush_callback: Callable[[], None],
        log: Callable[[str], None] = print,
    ) -> None:
        tipo_norm = str(tipo or "").strip().lower()
        item = {
            "tipo": tipo_norm,
            "texto": str(texto or "").strip(),
            "emocao": emocao,
            "nivel": nivel,
            "ts": time.time(),
        }
        with self.lock:
            self.buffer.append(item)
            if self.timer and self.timer.is_alive():
                return
            atraso = self.delay
            idade_sistema = time.time() - self.inicio_sistema
            if tipo_norm in {"briefing", "emails", "rotina", "musica"} and idade_sistema < self.janela_startup:
                atraso = max(self.delay, self.janela_startup - idade_sistema)
                log(f"🧠 [FALA PROATIVA] aguardando {atraso:.1f}s para unificar falas iniciais")
            self.timer = threading.Timer(atraso, flush_callback)
            self.timer.daemon = True
            self.timer.start()


def compor_fala_proativa(
    itens: list,
    *,
    obter_contexto_perceptivo: Callable[[], dict],
    normalizar_segmento_fala: Callable[[str], str],
    normalizar_texto_com_apelidos: Callable[[str], str],
    ajustar_tom_por_emocao: Callable[[str, str, str], str],
    fallback_fala_neutra: str,
) -> tuple[str, str, int]:
    if not itens:
        return fallback_fala_neutra, "calma", 1

    ctx = obter_contexto_perceptivo()
    ordem = {"briefing": 0, "emails": 1, "rotina": 2, "musica": 3}
    itens_validos = sorted(
        [i for i in itens if isinstance(i, dict) and str(i.get("texto") or "").strip()],
        key=lambda i: (
            ordem.get(str(i.get("tipo") or "").lower(), 9),
            float(i.get("ts") or 0.0),
        ),
    )

    agrupados = {}
    for item in itens_validos:
        tipo_item = str(item.get("tipo") or "").lower().strip() or "geral"
        agrupados.setdefault(tipo_item, []).append(item)

    itens = []
    for tipo_item, grupo in sorted(agrupados.items(), key=lambda kv: ordem.get(kv[0], 9)):
        if tipo_item == "emails" and len(grupo) > 1:
            textos_email = []
            for item in grupo[:4]:
                texto_email = normalizar_segmento_fala(item.get("texto") or "")
                texto_email = re.sub(r"^(Teus emails estão querendo atenção:\s*)", "", texto_email, flags=re.IGNORECASE).strip()
                if texto_email:
                    textos_email.append(texto_email)
            total = len(grupo)
            resumo = f"Tem {total} avisos de email no radar."
            if textos_email:
                resumo += " " + " ".join(textos_email)
            if total > len(textos_email):
                resumo += f" E ainda tem mais {total - len(textos_email)} sem eu tagarelar tudo agora."
            base = dict(grupo[0])
            base["texto"] = resumo
            base["ts"] = max(float(g.get("ts") or 0.0) for g in grupo)
            itens.append(base)
            continue

        if len(grupo) > 1:
            # Para rotina/música/briefing, evita eco repetido e fica com o sinal mais recente.
            itens.append(max(grupo, key=lambda g: float(g.get("ts") or 0.0)))
        else:
            itens.append(grupo[0])

    partes = []
    emocao = "calma"
    nivel = 1
    tipos = [str(i.get("tipo") or "").lower().strip() for i in itens]
    tem_briefing = "briefing" in tipos
    tem_emails = "emails" in tipos
    tem_musica = "musica" in tipos

    def turbinhar(texto: str) -> str:
        texto = re.sub(r"\s+", " ", str(texto or "")).strip()
        if not texto:
            return ""
        if texto[-1] not in ".!?…":
            texto += "."
        return texto

    for idx, item in enumerate(itens):
        tipo = str(item.get("tipo") or "").lower().strip()
        texto = normalizar_segmento_fala(item.get("texto") or "")
        if not texto:
            continue

        if idx == 0:
            emocao = str(item.get("emocao") or emocao)
            try:
                nivel = int(item.get("nivel") or nivel)
            except Exception:
                nivel = 1

        if tipo == "briefing":
            texto = turbinhar(texto)
            texto = re.sub(r"^(Hoje|Agora|E aí|Bom dia)[, ]+", "", texto, flags=re.IGNORECASE)
            texto = texto[:1].upper() + texto[1:] if texto else texto
            texto = f"Olha só: {texto}"
        elif tipo == "emails":
            texto = turbinhar(texto)
            texto = texto[:1].lower() + texto[1:] if texto else texto
            texto = f"Teus emails estão querendo atenção: {texto}"
        elif tipo == "rotina":
            texto = turbinhar(texto)
            texto = f"Seu horário tá puxando isso aqui: {texto}"
        elif tipo == "musica":
            texto = turbinhar(texto)
            texto = f"Tem um padrão musical querendo aparecer no contexto: {texto}"
        else:
            texto = turbinhar(texto)

        texto_lower = normalizar_texto_com_apelidos(texto)
        if ctx["periodo"] in {"madrugada", "noite"} and tipo in {"emails", "rotina", "musica"}:
            texto = texto.replace("querendo atenção", "pedindo um ritmo mais leve")
            if tipo == "musica" and "trilha sonora" not in texto_lower:
                texto += " Talvez hoje o melhor seja algo mais calmo."
        if ctx["topico_ativo"] and tipo in {"briefing", "rotina"} and len(texto) < 180:
            texto += f" Isso conversa com o que a gente vinha vendo sobre {ctx['topico_ativo']}."
        if ctx["humor"] <= -4 and tipo in {"emails", "rotina"}:
            texto = texto.replace("querendo atenção", "sem pressa para te encher")
        if ctx["emocao"] in {"triste", "decepcionada", "cansada"} and tipo == "briefing":
            texto += " Vou falar sem exagero pra não pesar mais o clima."

        texto = ajustar_tom_por_emocao(texto, emocao, ctx.get("topico_ativo", ""))
        partes.append(texto)

    if not partes:
        return fallback_fala_neutra, emocao, nivel

    if len(partes) == 1:
        texto_final = partes[0]
    elif len(partes) == 2:
        texto_final = f"{partes[0]} E {partes[1][0].lower() + partes[1][1:]}"
    else:
        texto_final = f"{partes[0]} Além disso, {partes[1][0].lower() + partes[1][1:]}"
        for parte in partes[2:]:
            texto_final += f" E {parte[0].lower() + parte[1:]}"

    if len(partes) > 1:
        texto_final = "Hmmm, " + texto_final[0].lower() + texto_final[1:]

    if tem_briefing and tem_musica:
        texto_final = texto_final.replace("E o padrão musical", "e o padrão musical", 1)
    if tem_emails and tem_musica and "padrão musical" not in texto_final.lower():
        texto_final += " E esse hábito musical também entra na conta."

    if ctx["periodo"] in {"madrugada", "noite"} and not tem_briefing:
        texto_final = texto_final.replace("Olha só:", "Olha só, baixando um pouco o ritmo:")
    if ctx["topico_ativo"] and ctx["topico_ativo"].lower() in texto_final.lower():
        texto_final = texto_final.replace("Seu horário tá puxando isso aqui:", "Seu cérebro tá puxando isso aqui junto com o contexto:")

    texto_final = re.sub(r"\s+", " ", texto_final).strip()

    return texto_final, emocao, nivel
