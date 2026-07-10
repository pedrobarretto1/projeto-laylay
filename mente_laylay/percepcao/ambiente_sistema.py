"""Percepcao de ambiente: briefing, clima e saude do PC."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
from datetime import datetime
from typing import Any, Callable


def carregar_estado_briefing(arquivo: str) -> str:
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                data = json.load(f)
                return str(data.get("data_ultimo") or "")
        except Exception:
            pass
    return ""


def salvar_estado_briefing(arquivo: str, *, print_fn: Callable[..., Any] = print) -> None:
    try:
        data = {"data_ultimo": datetime.now().strftime("%Y-%m-%d")}
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print_fn(f"💾 [BRIEFING] Estado salvo para {data['data_ultimo']}")
    except Exception as e:
        print_fn(f"⚠️ [BRIEFING] Erro ao salvar estado: {e}")


def obter_clima_wttr(
    cidade: str,
    *,
    requests_get: Callable[..., Any],
    print_fn: Callable[..., Any] = print,
) -> str:
    try:
        cidade = str(cidade or "Boituva").strip() or "Boituva"
        url = f"https://wttr.in/{cidade}?format=%C+%t+umidade:%h+vento:%w&lang=pt"
        res = requests_get(url, timeout=6)
        if res.status_code == 200:
            clima_raw = str(res.text or "").strip()
            umidade_match = re.search(r"umidade:(\d+)%", clima_raw)
            if umidade_match and int(umidade_match.group(1)) > 80:
                clima_raw += " — alta umidade, chance de chuva nas próximas horas!"
            return clima_raw
        return "Clima não disponível no momento."
    except Exception as e:
        print_fn(f"⚠️ [BRIEFING] wttr.in falhou: {e}")
        return "Não consegui pegar o clima agora."


def obter_clima_localidade(
    localidade: str = "",
    *,
    cidade_padrao: str = "Boituva",
    requests_get: Callable[..., Any],
    print_fn: Callable[..., Any] = print,
) -> dict:
    cidade = str(localidade or cidade_padrao or "").strip() or "Boituva"
    try:
        cidade_url = urllib.parse.quote(cidade)
        url = f"https://wttr.in/{cidade_url}?format=j1&lang=pt"
        res = requests_get(url, timeout=6)
        if res.status_code != 200:
            return {"ok": False, "localidade": cidade, "erro": "status"}
        data = res.json() if res.content else {}
        atual = ((data or {}).get("current_condition") or [{}])[0] or {}
        descricao = ""
        try:
            descricao = str((((atual.get("lang_pt") or atual.get("weatherDesc")) or [{}])[0] or {}).get("value") or "").strip()
        except Exception:
            descricao = ""
        if not descricao:
            try:
                descricao = str(((atual.get("weatherDesc") or [{}])[0] or {}).get("value") or "").strip()
            except Exception:
                descricao = ""
        return {
            "ok": True,
            "localidade": cidade,
            "temperatura_c": str(atual.get("temp_C") or "").strip(),
            "sensacao_c": str(atual.get("FeelsLikeC") or "").strip(),
            "umidade": str(atual.get("humidity") or "").strip(),
            "vento_kmph": str(atual.get("windspeedKmph") or "").strip(),
            "descricao": descricao,
        }
    except Exception as e:
        print_fn(f"⚠️ [CLIMA] falha ao consultar clima de {cidade}: {e}")
        return {"ok": False, "localidade": cidade, "erro": str(e)}


def montar_briefing_matinal(
    *,
    cidade: str,
    clima: str,
    enviar_mensagem_cb: Callable[..., Any],
    limpar_resposta_cb: Callable[[str], str],
    remover_prefixo_exec_cb: Callable[[str], str],
) -> str:
    prompt_briefing = (
        f"System: É de manhã e você acabou de acordar o sistema do Pedro. "
        f"Faça o seu briefing matinal para ele do seu jeito debochado, inteligente, observador e um pouco sedutor na confiança. "
        f"Informe que em {cidade} o clima hoje é: {clima}. "
        f"Pergunte o que ele vai fazer ou 'destruir' no PC hoje. "
        f"Se soar natural, conecte clima, humor e convite em uma única fala charmosa. "
        f"Use APENAS o JSON obrigatório com a chave 'fala' (sem comandos)."
    )
    mensagens = [
        {"role": "system", "content": prompt_briefing},
        {"role": "user", "content": "Gere o briefing agora."},
    ]
    bot_raw = enviar_mensagem_cb(mensagens, _com_tools=False)
    bot = remover_prefixo_exec_cb(limpar_resposta_cb(bot_raw)).strip()
    return bot or f"Hoje em {cidade} o clima está {clima}. E aí, qual vai ser a bagunça de hoje, Pedro?"


def repetir_briefing(
    *,
    cidade: str,
    clima: str,
    gerar_resposta_exec_sync_cb: Callable[[str], Any],
) -> None:
    prompt_repetir = (
        f"System: O Pedro acabou de pedir para você repetir o briefing do clima. "
        f"Fale do seu jeito debochado (talvez zoando a memória dele). "
        f"A informação é: em {cidade} o clima está {clima}. "
        f"Use APENAS o JSON obrigatório com a chave 'fala' (sem comandos)."
    )
    gerar_resposta_exec_sync_cb(prompt_repetir)


def detectar_repetir_briefing(texto: str) -> bool:
    t = str(texto or "").lower().strip()
    triggers = [
        "repete o briefing", "repetir briefing", "briefing de novo",
        "fala o briefing de novo", "repete o clima",
    ]
    return any(trig in t for trig in triggers)


def obter_temperatura_cpu() -> float | None:
    try:
        import wmi
        c = wmi.WMI(namespace="root\\OpenHardwareMonitor")
        sensors = c.Sensor()
        for sensor in sensors:
            if sensor.SensorType == "Temperature" and ("CPU" in sensor.Name or "Package" in sensor.Name):
                return round(float(sensor.Value), 1)
    except Exception:
        pass

    try:
        import wmi
        c = wmi.WMI(namespace="root\\wmi")
        temps = c.MSAcpi_ThermalZoneTemperature()
        for temp in temps:
            return round((temp.CurrentTemperature / 10.0) - 273.15, 1)
    except Exception:
        pass

    return None


def identificar_processo_culpado(psutil_mod: Any) -> str:
    try:
        processos = []
        for proc in psutil_mod.process_iter(["name", "cpu_percent"]):
            try:
                if proc.info["cpu_percent"] is not None:
                    processos.append((proc.info["name"], proc.info["cpu_percent"]))
            except Exception:
                pass
        if processos:
            culpado = max(processos, key=lambda item: item[1])
            return culpado[0] if culpado[1] > 15 else "nenhum em destaque"
    except Exception:
        pass
    return "nenhum processo detectado"


def montar_status_saude(psutil_mod: Any) -> str:
    cpu = psutil_mod.cpu_percent(interval=1)
    ram = psutil_mod.virtual_memory().percent
    temp = obter_temperatura_cpu()

    if cpu < 60 and ram < 70:
        veredito = "tá tranquilo"
    elif cpu < 80 and ram < 85:
        veredito = "tá esquentando"
    else:
        veredito = "tá pesado pra caralho"

    msg = f"CPU {cpu:.0f}%, RAM {ram:.0f}%"
    if temp is not None:
        msg += f", temperatura {temp}°C"
    msg += f". {veredito}, Pedro."

    culpado = identificar_processo_culpado(psutil_mod)
    if culpado not in {"nenhum em destaque", "nenhum processo detectado"}:
        msg += f" O culpado é {culpado}."
    return msg


def monitor_saude_daemon(
    *,
    psutil_mod: Any,
    falar_status_cb: Callable[[], Any],
    estado: dict,
    cpu_threshold: float,
    ram_threshold: float,
    cpu_sustentado_segundos: float,
    print_fn: Callable[..., Any] = print,
    sleep_fn: Callable[[float], Any] = time.sleep,
) -> None:
    print_fn("🩺 [SAÚDE] Monitor de saúde iniciado (CPU/RAM/Temp + anti-falso-positivo)")
    estado.setdefault("cpu_alta_desde", 0.0)
    estado.setdefault("ultimo_aviso", 0.0)

    while True:
        try:
            agora = time.time()
            cpu = psutil_mod.cpu_percent(interval=1)
            ram = psutil_mod.virtual_memory().percent

            if cpu >= cpu_threshold:
                if float(estado.get("cpu_alta_desde") or 0.0) == 0.0:
                    estado["cpu_alta_desde"] = agora
                elif (agora - float(estado.get("cpu_alta_desde") or 0.0)) >= cpu_sustentado_segundos:
                    if (agora - float(estado.get("ultimo_aviso") or 0.0)) > 300:
                        estado["ultimo_aviso"] = agora
                        falar_status_cb()
            else:
                estado["cpu_alta_desde"] = 0.0

            if ram >= ram_threshold and (agora - float(estado.get("ultimo_aviso") or 0.0)) > 180:
                estado["ultimo_aviso"] = agora
                falar_status_cb()
        except Exception as e:
            print_fn(f"⚠️ [SAÚDE] Erro no daemon: {e}")

        sleep_fn(5)


def detectar_comando_saude(texto: str) -> bool:
    t = str(texto or "").lower().strip()
    triggers = [
        "como tá o pc", "como ta o pc", "como está o pc",
        "tá pesado", "ta pesado", "status do pc",
        "saúde do pc", "como anda o pc", "tá quente o pc",
    ]
    return any(trig in t for trig in triggers)
