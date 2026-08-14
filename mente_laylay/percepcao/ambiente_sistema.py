"""Percepcao de ambiente: briefing, clima e saude do PC."""

from __future__ import annotations

import json
import os
import random
import re
import threading
import time
import unicodedata
import urllib.parse
from datetime import datetime
from typing import Any, Callable

from mente_laylay.personalidade.ritmo_natural import escolher_sem_repeticao
from mente_laylay.integracao.llm_http import eh_estado_tecnico_llm


_MARCADORES_CLIMA_INDISPONIVEL = (
    "não consegui pegar o clima",
    "nao consegui pegar o clima",
    "clima não disponível",
    "clima nao disponivel",
    "clima indisponível",
    "clima indisponivel",
)

_CLIMA_CACHE_LOCK = threading.RLock()
_COORDENADAS_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CLIMA_ATUAL_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}

_DESCRICOES_WMO = {
    0: "céu limpo", 1: "predominantemente limpo", 2: "parcialmente nublado",
    3: "nublado", 45: "neblina", 48: "neblina com geada",
    51: "garoa fraca", 53: "garoa moderada", 55: "garoa forte",
    56: "garoa congelante fraca", 57: "garoa congelante forte",
    61: "chuva fraca", 63: "chuva moderada", 65: "chuva forte",
    66: "chuva congelante fraca", 67: "chuva congelante forte",
    71: "neve fraca", 73: "neve moderada", 75: "neve forte",
    77: "grãos de neve", 80: "pancadas de chuva fracas",
    81: "pancadas de chuva moderadas", 82: "pancadas de chuva fortes",
    85: "pancadas de neve fracas", 86: "pancadas de neve fortes",
    95: "trovoadas", 96: "trovoadas com granizo fraco",
    99: "trovoadas com granizo forte",
}


def _valor_clima(valor: Any) -> str:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return ""
    if numero.is_integer():
        return str(int(numero))
    return f"{numero:.1f}".replace(".", ",")


def _descricao_wmo(codigo: Any) -> str:
    try:
        return _DESCRICOES_WMO.get(int(codigo), "condições variáveis")
    except (TypeError, ValueError):
        return "condições variáveis"


def obter_clima_open_meteo(
    localidade: str,
    *,
    requests_get: Callable[..., Any],
    print_fn: Callable[..., Any] = print,
    timeout_s: float = 2.5,
    clock: Callable[[], float] = time.time,
    day_offset: int = 0,
) -> dict:
    """Consulta reserva sem chave, com geocodificação e cache conservador."""
    cidade = re.sub(r"\s+", " ", str(localidade or "Boituva")).strip() or "Boituva"
    try:
        deslocamento = max(0, min(6, int(day_offset or 0)))
    except (TypeError, ValueError):
        deslocamento = 0
    chave_cidade = cidade.casefold()
    chave = f"{chave_cidade}:{deslocamento}"
    agora = float(clock())
    with _CLIMA_CACHE_LOCK:
        item_clima = _CLIMA_ATUAL_CACHE.get(chave)
        if item_clima and agora - item_clima[0] < 300.0:
            retorno = dict(item_clima[1])
            retorno["cache"] = True
            return retorno
        item_coordenadas = _COORDENADAS_CACHE.get(chave_cidade)
        coordenadas = (
            dict(item_coordenadas[1])
            if item_coordenadas and agora - item_coordenadas[0] < 86400.0
            else {}
        )

    limite = max(0.5, float(timeout_s))
    try:
        if not coordenadas:
            resposta_geo = requests_get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": cidade, "count": 5, "language": "pt",
                    "format": "json",
                },
                timeout=limite,
            )
            if int(getattr(resposta_geo, "status_code", 0) or 0) != 200:
                return {"ok": False, "localidade": cidade, "erro": "geocodificacao"}
            resultados = list((resposta_geo.json() or {}).get("results") or [])
            if not resultados:
                return {"ok": False, "localidade": cidade, "erro": "local_nao_encontrado"}
            escolhido = next(
                (item for item in resultados if str(item.get("country_code") or "").upper() == "BR"),
                resultados[0],
            )
            coordenadas = {
                "latitude": float(escolhido["latitude"]),
                "longitude": float(escolhido["longitude"]),
                "localidade": str(escolhido.get("name") or cidade).strip() or cidade,
                "timezone": str(escolhido.get("timezone") or "auto").strip() or "auto",
            }
            with _CLIMA_CACHE_LOCK:
                _COORDENADAS_CACHE[chave_cidade] = (agora, dict(coordenadas))

        resposta = requests_get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": coordenadas["latitude"],
                "longitude": coordenadas["longitude"],
                "current": (
                    "temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "weather_code,wind_speed_10m,wind_direction_10m"
                ),
                "hourly": "precipitation_probability,precipitation",
                "daily": (
                    "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
                    "weather_code,precipitation_probability_max"
                ),
                "timezone": coordenadas.get("timezone") or "auto",
                "forecast_days": max(1, deslocamento + 1),
            },
            timeout=limite,
        )
        if int(getattr(resposta, "status_code", 0) or 0) != 200:
            return {"ok": False, "localidade": cidade, "erro": "previsao"}
        dados_previsao = resposta.json() or {}
        atual = dict(dados_previsao.get("current") or {})
        horario = dict(dados_previsao.get("hourly") or {})
        diario = dict(dados_previsao.get("daily") or {})
        chances_chuva = []
        for valor in horario.get("precipitation_probability") or ():
            try:
                chances_chuva.append(max(0, min(100, int(float(valor)))))
            except (TypeError, ValueError):
                continue
        precipitacoes = []
        for valor in horario.get("precipitation") or ():
            try:
                precipitacoes.append(max(0.0, float(valor)))
            except (TypeError, ValueError):
                continue
        def _diario_no_dia(chave_diaria: str) -> Any:
            valores = list(diario.get(chave_diaria) or [])
            return valores[deslocamento] if deslocamento < len(valores) else None

        temperatura = _valor_clima(
            atual.get("temperature_2m")
            if deslocamento == 0 else _diario_no_dia("temperature_2m_mean")
        )
        if deslocamento and not (
            _valor_clima(_diario_no_dia("temperature_2m_max"))
            or _valor_clima(_diario_no_dia("temperature_2m_min"))
        ):
            return {
                "ok": False,
                "localidade": cidade,
                "erro": "previsao_dia_ausente",
                "day_offset": deslocamento,
            }
        if not temperatura and deslocamento == 0:
            return {"ok": False, "localidade": cidade, "erro": "dados_ausentes"}
        chance_diaria = _diario_no_dia("precipitation_probability_max")
        try:
            chance_diaria = max(0, min(100, int(float(chance_diaria))))
        except (TypeError, ValueError):
            chance_diaria = None
        resultado = {
            "ok": True,
            "localidade": coordenadas.get("localidade") or cidade,
            "temperatura_c": temperatura,
            "sensacao_c": _valor_clima(
                atual.get("apparent_temperature") if deslocamento == 0 else None
            ),
            "umidade": _valor_clima(
                atual.get("relative_humidity_2m") if deslocamento == 0 else None
            ),
            "vento_kmph": _valor_clima(
                atual.get("wind_speed_10m") if deslocamento == 0 else None
            ),
            "direcao_vento": _valor_clima(
                atual.get("wind_direction_10m") if deslocamento == 0 else None
            ),
            "descricao": _descricao_wmo(
                atual.get("weather_code")
                if deslocamento == 0 else _diario_no_dia("weather_code")
            ),
            "chance_chuva_pct": (
                chance_diaria
                if chance_diaria is not None
                else max(chances_chuva) if deslocamento == 0 and chances_chuva else None
            ),
            "temperatura_max_c": _valor_clima(
                _diario_no_dia("temperature_2m_max")
            ),
            "temperatura_min_c": _valor_clima(
                _diario_no_dia("temperature_2m_min")
            ),
            "precipitacao_max_mm": max(precipitacoes) if precipitacoes else None,
            "previsao_chuva_disponivel": bool(
                chance_diaria is not None
                or (deslocamento == 0 and (chances_chuva or precipitacoes))
            ),
            "fonte": "open_meteo",
            "cache": False,
            "day_offset": deslocamento,
        }
        with _CLIMA_CACHE_LOCK:
            _CLIMA_ATUAL_CACHE[chave] = (agora, dict(resultado))
        return resultado
    except Exception as erro:
        print_fn(f"⚠️ [CLIMA] fonte reserva não respondeu: {type(erro).__name__}")
        return {"ok": False, "localidade": cidade, "erro": "fonte_reserva"}


def _clima_compacto(dados: dict) -> str:
    descricao = str(dados.get("descricao") or "condições variáveis").strip()
    temperatura = str(dados.get("temperatura_c") or "").strip()
    umidade = str(dados.get("umidade") or "").strip()
    vento = str(dados.get("vento_kmph") or "").strip()
    partes = [descricao, f"{temperatura}°C" if temperatura else ""]
    if umidade:
        partes.append(f"umidade:{umidade}%")
    if vento:
        partes.append(f"vento:{vento}km/h")
    return " ".join(item for item in partes if item)


def clima_esta_disponivel(clima: str) -> bool:
    """Distingue uma observação meteorológica de uma mensagem de erro."""
    texto = re.sub(r"\s+", " ", str(clima or "")).strip().casefold()
    return bool(texto) and not any(marcador in texto for marcador in _MARCADORES_CLIMA_INDISPONIVEL)


def naturalizar_clima_resumido(clima: str) -> str:
    """Converte o formato compacto do wttr.in em uma frase pronunciável."""
    texto = re.sub(r"\s+", " ", str(clima or "")).strip()
    texto = re.sub(r"[↑↗→↘↓↙←↖]", "", texto)
    texto = re.sub(r"(?<!\w)\+(?=\d)", "", texto)
    texto = re.sub(r"(?<=\d)\s*°\s*C\b", " graus Celsius", texto, flags=re.IGNORECASE)
    texto = re.sub(r"(?<=\d)\s*km\s*/\s*h\b", " quilômetros por hora", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bumidade\s*:\s*(\d+)\s*%", r"umidade em \1 por cento", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bvento\s*:\s*", "vento de ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"^([^\d,]+?)\s+(-?\d+\s+graus\b)", r"\1, com \2", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s+(?=umidade\s+em\b)", ", ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[, ]+vento\s+de\b", " e vento de", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s+", " ", texto).strip(" ,.;")
    if texto and texto[0].isupper():
        texto = texto[0].lower() + texto[1:]
    return texto


def montar_briefing_sem_clima(cidade: str, *, repeticao: bool = False) -> str:
    """Mantém o briefing útil quando o provedor meteorológico não responde."""
    local = re.sub(r"\s+", " ", str(cidade or "Boituva")).strip() or "Boituva"
    if repeticao:
        return (
            f"O briefing é este: o clima de {local} não respondeu agora, então eu não vou "
            "inventar previsão. O restante continua funcionando normalmente."
        )
    return (
        f"O clima de {local} não respondeu agora, então hoje eu não vou inventar previsão. "
        "O resto do sistema já acordou, e eu também. Qual projeto vai perder a paz primeiro hoje?"
    )


def fala_briefing_ancorada(fala: str, *, cidade: str) -> bool:
    """Aceita autoria criativa somente quando ela continua falando do clima observado."""
    bruto = unicodedata.normalize("NFKD", str(fala or "").casefold())
    texto = "".join(ch for ch in bruto if not unicodedata.combining(ch))
    cidade_bruta = unicodedata.normalize("NFKD", str(cidade or "").casefold())
    cidade_normalizada = "".join(
        ch for ch in cidade_bruta if not unicodedata.combining(ch)
    ).strip()
    menciona_cidade = bool(cidade_normalizada and cidade_normalizada in texto)
    menciona_clima = bool(re.search(
        r"\b(?:clima|tempo|sol|ensolarad[oa]|chuva|chuvoso|nublad[oa]|nuvens?|"
        r"vento|umidade|garoa|neve|neblina|temperatura|calor|frio|graus?)\b|"
        r"-?\d+(?:[.,]\d+)?\s*(?:°|graus?\b)",
        texto,
    ))
    return menciona_cidade and menciona_clima


def fala_repeticao_briefing_adequada(fala: str, *, cidade: str) -> bool:
    """Exige conteúdo e presença equivalentes ao briefing inicial.

    A repetição pode mudar as palavras, mas não pode degradar para uma linha
    mecânica de telemetria nem para uma resposta curta sem personalidade.
    """
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    palavras = re.findall(r"[\wÀ-ÿ]+", texto)
    return (
        fala_briefing_ancorada(texto, cidade=cidade)
        and 18 <= len(palavras) <= 85
        and len(re.findall(r"[.!?]", texto)) >= 2
    )


def montar_repeticao_briefing_local(cidade: str, clima: str) -> str:
    """Produz uma repetição rica e variável quando a LLM não responde bem."""
    local = re.sub(r"\s+", " ", str(cidade or "Boituva")).strip() or "Boituva"
    clima_fala = naturalizar_clima_resumido(clima)
    opcoes = (
        (
            f"Em {local}, o tempo continua {clima_fala}. O céu não mudou o roteiro, "
            "só trouxe o relatório de volta. Agora diz: qual projeto vai perder a paz primeiro?"
        ),
        (
            f"Resumo da rodada: em {local}, o dia segue {clima_fala}. Nada de suspense "
            "meteorológico por enquanto. A pergunta importante continua: qual projeto você vai tirar do sossego primeiro?"
        ),
        (
            f"Em {local}, o tempo continua {clima_fala}. O clima fez a parte dele sem drama; "
            "agora falta você decidir onde começa a bagunça produtiva de hoje. Qual é o primeiro alvo?"
        ),
    )
    return escolher_sem_repeticao(
        opcoes,
        fallback=opcoes[0],
        escolha_aleatoria=random.choice,
    )


def selecionar_fala_inicial(
    *,
    usuario_iniciou: bool,
    briefing_pendente: bool,
    briefing_ativo: bool,
    abertura_ativa: bool,
) -> str:
    """Separa o briefing útil da saudação decorativa de inicialização."""
    if usuario_iniciou:
        return ""
    if briefing_ativo and briefing_pendente:
        return "briefing"
    if abertura_ativa:
        return "abertura"
    return ""


def lapidar_fala_briefing(fala: str, *, cidade: str, clima: str) -> str:
    """Corrige artificialidades do modelo sem alterar os dados meteorológicos."""
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    if not texto:
        texto = (
            f"Em {cidade}, o dia amanheceu {naturalizar_clima_resumido(clima)}. "
            "Qual projeto vai perder a paz primeiro hoje?"
        )

    texto = re.sub(r"\bBoa manhã\b", "Bom dia", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bvocês\b", "você", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bplanejam\b", "planeja", texto, flags=re.IGNORECASE)
    texto = re.sub(r"(['\"`])destruir\1", "destruir", texto, flags=re.IGNORECASE)
    texto = re.sub(
        rf"\bEm\s+{re.escape(str(cidade or '').strip())}\s+é\s+([^.!?]+)",
        rf"Em {str(cidade or '').strip()}, o tempo está \1",
        texto,
        flags=re.IGNORECASE,
    )

    pergunta_seca = re.compile(
        r"(?:E aí[, ]*)?(?:o que|qual coisa)\s+(?:você\s+)?(?:planeja|vai|pretende)\s+"
        r"(?:fazer|destruir|aprontar)(?:\s+hoje)?(?:\s+(?:no|nesse)\s+PC)?\s*\?",
        flags=re.IGNORECASE,
    )
    texto = pergunta_seca.sub(
        "Agora me conta. Qual projeto vai perder a paz primeiro hoje?",
        texto,
    )
    texto = re.sub(r"([.!?])\1+", r"\1", texto)
    texto = re.sub(r"\?\s*\.", "?", texto)
    texto = re.sub(r"\s+([,.!?;:])", r"\1", texto)
    return re.sub(r"\s+", " ", texto).strip()


class AmbienteSistemaRuntime:
    """Mantém travas e estado transitório de briefing e saúde do computador."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._briefing_executado = False
        self._briefing_repeticao_em_andamento = False
        self.saude = {"cpu_alta_desde": 0.0, "ultimo_aviso": 0.0}

    def executar_briefing(self, **kwargs: Any) -> bool:
        with self._lock:
            ja_executado = self._briefing_executado
        resultado = executar_briefing_matinal(ja_executado=ja_executado, **kwargs)
        with self._lock:
            self._briefing_executado = bool(resultado)
            return self._briefing_executado

    def iniciar_repeticao_briefing(self) -> bool:
        with self._lock:
            if self._briefing_repeticao_em_andamento:
                return False
            self._briefing_repeticao_em_andamento = True
            return True

    def finalizar_repeticao_briefing(self) -> None:
        with self._lock:
            self._briefing_repeticao_em_andamento = False

    def repetir_briefing_atual(
        self,
        *,
        cidade: str,
        obter_clima: Callable[[], str],
        enviar_mensagem: Callable[..., Any],
        limpar_resposta: Callable[[str], str],
        remover_prefixo_exec: Callable[[str], str],
        falar: Callable[[str, str, int], Any],
        print_fn: Callable[..., Any] = print,
    ) -> bool | str:
        if not self.iniciar_repeticao_briefing():
            print_fn("⚠️ [BRIEFING] repetição duplicada ignorada enquanto a anterior ainda está em andamento")
            return False

        try:
            clima = obter_clima()
            if not clima_esta_disponivel(clima):
                fala = montar_briefing_sem_clima(cidade, repeticao=True)
                falar(fala, "calma", 1)
                return fala

            def gerar_somente_fala(prompt: str) -> str:
                mensagens = [
                    {
                        "role": "system",
                        "content": (
                            "Você está repetindo o briefing diário da Laylay. Mude a formulação, mas mantenha "
                            "a mesma energia e riqueza da abertura: duas ou três frases, de 25 a 65 palavras, "
                            "voz espontânea, cúmplice e levemente debochada. Informe cidade e clima com clareza, "
                            "sem soar como painel de telemetria ou locutora. Termine com uma pergunta ou provocação "
                            "simpática ligada ao dia do usuário. Não crie nem execute comandos. Retorne apenas a fala."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
                resposta_raw = enviar_mensagem(
                    mensagens,
                    _com_tools=False,
                    max_tokens=160,
                    modo_rapido=True,
                    timeout=4,
                )
                fala = "" if eh_estado_tecnico_llm(resposta_raw) else remover_prefixo_exec(
                    limpar_resposta(resposta_raw)
                ).strip()
                falha_ia = any(
                    trecho in fala.lower()
                    for trecho in (
                        "demorou demais", "conexão com a parte da ia falhou",
                        "conexao com a parte da ia falhou", "cheque sua chave",
                    )
                )
                if (
                    not fala
                    or falha_ia
                    or not fala_repeticao_briefing_adequada(fala, cidade=cidade)
                ):
                    fala = montar_repeticao_briefing_local(cidade, clima)
                fala = lapidar_fala_briefing(fala, cidade=cidade, clima=clima)
                falar(fala, "calma", 1)
                return fala

            fala_gerada = repetir_briefing(
                cidade=cidade,
                clima=clima,
                gerar_resposta_exec_sync_cb=gerar_somente_fala,
            )
            return str(fala_gerada or "").strip() or True
        finally:
            self.finalizar_repeticao_briefing()

    def monitorar_saude(self, **kwargs: Any) -> None:
        monitor_saude_daemon(estado=self.saude, **kwargs)

    @staticmethod
    def falar_status_saude(*, psutil_mod: Any, falar: Callable[..., Any], print_fn=print) -> str:
        mensagem = montar_status_saude(psutil_mod)
        falar(mensagem, "calma", 1)
        print_fn(f"[SAUDE] {mensagem}")
        return mensagem


def criar_ambiente_sistema_runtime() -> AmbienteSistemaRuntime:
    return AmbienteSistemaRuntime()


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
    timeout_s: float = 6.0,
) -> str:
    cidade = str(cidade or "Boituva").strip() or "Boituva"
    try:
        cidade_url = urllib.parse.quote(cidade)
        url = f"https://wttr.in/{cidade_url}?format=%C+%t+umidade:%h+vento:%w&lang=pt"
        res = requests_get(url, timeout=max(0.5, float(timeout_s)))
        if res.status_code == 200:
            clima_raw = str(res.text or "").strip()
            umidade_match = re.search(r"umidade:(\d+)%", clima_raw)
            if umidade_match and int(umidade_match.group(1)) > 80:
                clima_raw += " — alta umidade, chance de chuva nas próximas horas!"
            return clima_raw
    except Exception:
        print_fn("⚠️ [BRIEFING] wttr.in não respondeu; usando fonte reserva.")
    reserva = obter_clima_open_meteo(
        cidade,
        requests_get=requests_get,
        print_fn=print_fn,
        timeout_s=min(3.0, max(1.0, float(timeout_s))),
    )
    if reserva.get("ok"):
        print_fn("🌦️ [BRIEFING] clima recuperado pela fonte reserva.")
        return _clima_compacto(reserva)
    return "Não consegui pegar o clima agora."


def obter_clima_localidade(
    localidade: str = "",
    *,
    cidade_padrao: str = "Boituva",
    requests_get: Callable[..., Any],
    print_fn: Callable[..., Any] = print,
    day_offset: int = 0,
) -> dict:
    cidade = str(localidade or cidade_padrao or "").strip() or "Boituva"
    try:
        deslocamento = max(0, min(6, int(day_offset or 0)))
    except (TypeError, ValueError):
        deslocamento = 0
    try:
        cidade_url = urllib.parse.quote(cidade)
        url = f"https://wttr.in/{cidade_url}?format=j1&lang=pt"
        res = requests_get(url, timeout=6)
        if res.status_code != 200:
            raise RuntimeError("status_wttr")
        data = res.json() if res.content else {}
        atual = ((data or {}).get("current_condition") or [{}])[0] or {}
        dias = list((data or {}).get("weather") or [])
        if deslocamento >= len(dias):
            raise RuntimeError("previsao_dia_ausente")
        dia = dict(dias[deslocamento] or {})
        horas = list(dia.get("hourly") or [])
        chances_chuva = []
        for hora in horas:
            if not isinstance(hora, dict):
                continue
            try:
                chances_chuva.append(max(0, min(100, int(float(
                    hora.get("chanceofrain") or 0
                )))))
            except (TypeError, ValueError):
                continue
        descricao = ""
        fonte_descricao = atual if deslocamento == 0 else next(
            (
                hora for hora in horas
                if str((hora or {}).get("time") or "") in {"1200", "12:00"}
            ),
            horas[len(horas) // 2] if horas else {},
        )
        try:
            descricao = str((((fonte_descricao.get("lang_pt") or fonte_descricao.get("weatherDesc")) or [{}])[0] or {}).get("value") or "").strip()
        except Exception:
            descricao = ""
        if not descricao:
            try:
                descricao = str(((fonte_descricao.get("weatherDesc") or [{}])[0] or {}).get("value") or "").strip()
            except Exception:
                descricao = ""
        return {
            "ok": True,
            "localidade": cidade,
            "temperatura_c": str(
                atual.get("temp_C") if deslocamento == 0 else dia.get("avgtempC") or ""
            ).strip(),
            "sensacao_c": str(atual.get("FeelsLikeC") or "").strip() if deslocamento == 0 else "",
            "umidade": str(atual.get("humidity") or "").strip() if deslocamento == 0 else "",
            "vento_kmph": str(atual.get("windspeedKmph") or "").strip() if deslocamento == 0 else "",
            "descricao": descricao,
            "chance_chuva_pct": max(chances_chuva) if chances_chuva else None,
            "temperatura_max_c": str(dia.get("maxtempC") or "").strip(),
            "temperatura_min_c": str(dia.get("mintempC") or "").strip(),
            "precipitacao_max_mm": None,
            "previsao_chuva_disponivel": bool(chances_chuva),
            "fonte": "wttr",
            "day_offset": deslocamento,
        }
    except Exception:
        print_fn(f"⚠️ [CLIMA] wttr.in não respondeu para {cidade}; usando fonte reserva.")
        return obter_clima_open_meteo(
            cidade,
            requests_get=requests_get,
            print_fn=print_fn,
            timeout_s=3.0,
            day_offset=deslocamento,
        )


def montar_briefing_matinal(
    *,
    cidade: str,
    clima: str,
    enviar_mensagem_cb: Callable[..., Any],
    limpar_resposta_cb: Callable[[str], str],
    remover_prefixo_exec_cb: Callable[[str], str],
) -> str:
    if not clima_esta_disponivel(clima):
        return montar_briefing_sem_clima(cidade)

    clima_fala = naturalizar_clima_resumido(clima)
    prompt_briefing = (
        f"É de manhã e você acabou de acordar junto com o sistema. "
        f"Faça um briefing matinal curto na voz da Laylay: observadora, cúmplice, espontânea e "
        f"levemente debochada, sem parecer locutora de previsão do tempo. "
        f"Informe que em {cidade} o clima hoje é: {clima_fala}. "
        f"Fale diretamente com o usuário no singular e termine com uma provocação simpática sobre qual "
        f"projeto vai perder a paz primeiro hoje. "
        f"Use no máximo 65 palavras e duas ou três frases. Não use metáforas sensuais, românticas ou corporais. "
        f"Não diga 'Boa manhã', não use 'vocês', não coloque destruir entre aspas e não soe institucional. "
        f"Retorne somente a frase que será falada, sem JSON, rótulos ou comandos."
    )
    mensagens = [
        {"role": "system", "content": prompt_briefing},
        {"role": "user", "content": "Gere o briefing agora."},
    ]
    bot_raw = enviar_mensagem_cb(
        mensagens,
        _com_tools=False,
        max_tokens=160,
        modo_rapido=True,
        timeout=4,
    )
    bot = "" if eh_estado_tecnico_llm(bot_raw) else remover_prefixo_exec_cb(
        limpar_resposta_cb(bot_raw)
    ).strip()
    falha_ia = any(
        trecho in bot.lower()
        for trecho in (
            "demorou demais", "conexão com a parte da ia falhou",
            "conexao com a parte da ia falhou", "cheque sua chave",
        )
    )
    tom_inadequado = any(
        trecho in bot.casefold()
        for trecho in (
            "desejo", "sensual", "sedutor", "coração úmido", "coracao umido",
            "riso malicioso", "mundo inteiro começa a tremer", "mundo inteiro comeca a tremer",
        )
    )
    palavras = bot.split()
    if (
        falha_ia
        or tom_inadequado
        or len(palavras) > 85
        or not fala_briefing_ancorada(bot, cidade=cidade)
    ):
        bot = ""
    fallback = (
        f"Em {cidade}, o dia amanheceu {clima_fala}. O céu já entregou o relatório. "
        "Agora me conta. Qual projeto vai perder a paz primeiro hoje?"
    )
    return lapidar_fala_briefing(bot or fallback, cidade=cidade, clima=clima_fala)


def executar_briefing_matinal(
    *,
    ja_executado: bool,
    cidade: str,
    carregar_estado: Callable[[], str],
    salvar_estado: Callable[[], Any],
    obter_clima: Callable[[], str],
    montar_fala: Callable[[str], str],
    agendar_fala: Callable[[str, str, str, int], Any],
    agora: Callable[[], datetime] = datetime.now,
    sleep_fn: Callable[[float], Any] = time.sleep,
    print_fn: Callable[..., Any] = print,
    atraso_startup_s: float = 0.25,
) -> bool:
    """Executa no máximo um briefing por dia e devolve o estado da trava."""
    if ja_executado:
        return True
    hoje = agora().strftime("%Y-%m-%d")
    if carregar_estado() == hoje:
        print_fn("📅 [BRIEFING] Já foi executado hoje.")
        return True
    sleep_fn(max(0.0, float(atraso_startup_s)))
    clima = obter_clima()
    entregue = False
    pendente = False
    try:
        fala = montar_fala(clima)
        resultado_entrega = agendar_fala("briefing", fala, "calma", 1)
        if isinstance(resultado_entrega, dict):
            entregue = bool(resultado_entrega.get("entregue"))
            pendente = bool(resultado_entrega.get("pendente"))
        else:
            entregue = bool(resultado_entrega)
    except Exception as erro:
        print_fn(f"⚠️ [BRIEFING] Falha ao montar fala: {erro}")
        fallback = (
            f"Hoje em {cidade} o clima está {clima}. E aí, qual vai ser a bagunça de hoje?"
            if clima_esta_disponivel(clima)
            else montar_briefing_sem_clima(cidade)
        )
        try:
            resultado_entrega = agendar_fala("briefing", fallback, "calma", 1)
            if isinstance(resultado_entrega, dict):
                entregue = bool(resultado_entrega.get("entregue"))
                pendente = bool(resultado_entrega.get("pendente"))
            else:
                entregue = bool(resultado_entrega)
        except Exception as erro_fala:
            print_fn(f"⚠️ [BRIEFING] Falha ao entregar fallback: {erro_fala}")
            entregue = False
    if not entregue:
        if pendente:
            print_fn("📅 [BRIEFING] Fala preservada para depois do turno; estado será salvo após a entrega.")
            return True
        print_fn("⚠️ [BRIEFING] Fala não foi entregue; estado diário não será salvo.")
        return False
    salvar_estado()
    print_fn("✅ [BRIEFING MATINAL] Fala entregue e estado salvo.")
    return True


def repetir_briefing(
    *,
    cidade: str,
    clima: str,
    gerar_resposta_exec_sync_cb: Callable[[str], Any],
) -> Any:
    if not clima_esta_disponivel(clima):
        return montar_briefing_sem_clima(cidade, repeticao=True)
    clima_fala = naturalizar_clima_resumido(clima)
    prompt_repetir = (
        "O usuário pediu o briefing novamente. Reconte-o com palavras novas, mas preserve a mesma "
        "intensidade da abertura da Laylay: espontânea, cúmplice, clara e levemente debochada. "
        f"Diga que em {cidade} o clima está {clima_fala}. Use duas ou três frases, entre 25 e 65 "
        "palavras, e termine com uma pergunta ou provocação simpática sobre o dia. Não pareça uma "
        "locutora nem uma tela de telemetria. Retorne somente a fala, sem JSON, rótulos ou comandos."
    )
    return gerar_resposta_exec_sync_cb(prompt_repetir)


def detectar_repetir_briefing(texto: str) -> bool:
    t = str(texto or "").lower().strip()
    triggers = [
        "repete o briefing", "repetir briefing", "briefing de novo",
        "fala o briefing de novo", "repete o clima", "qual o briefing",
        "qual é o briefing", "qual e o briefing", "briefing de hoje",
        "me passa o briefing", "me mostra o briefing",
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


def identificar_processo_culpado(psutil_mod: Any, metrica: str = "cpu") -> str:
    try:
        processos = []
        campo = "memory_percent" if metrica == "memoria" else "cpu_percent"
        for proc in psutil_mod.process_iter(["name", campo]):
            try:
                nome = str(proc.info.get("name") or "").strip()
                if nome.lower() in {"system idle process", "idle", "system idle process.exe"}:
                    continue
                valor = proc.info.get(campo)
                if valor is not None:
                    processos.append((nome, float(valor)))
            except Exception:
                pass
        if processos:
            culpado = max(processos, key=lambda item: item[1])
            limite = 10 if metrica == "memoria" else 15
            return culpado[0] if culpado[1] > limite else "nenhum em destaque"
    except Exception:
        pass
    return "nenhum processo detectado"


def montar_status_saude(psutil_mod: Any) -> str:
    cpu = psutil_mod.cpu_percent(interval=1)
    ram = psutil_mod.virtual_memory().percent
    temp = obter_temperatura_cpu()

    if cpu < 60 and ram < 70:
        nivel = "normal"
        vereditos = [
            "Tá tudo respirando bem por aqui.",
            "O PC está trabalhando sem aperto.",
            "Nada preocupante no momento.",
            "Está tudo bem comportado por aqui.",
        ]
    elif cpu < 80 and ram < 85:
        nivel = "atencao"
        vereditos = [
            "Ele está um pouco ocupado, mas ainda está dando conta.",
            "A carga subiu; vale ficar de olho.",
            "Está trabalhando mais do que o normal agora.",
            "Tem bastante coisa acontecendo, mas ainda não virou sufoco.",
        ]
    else:
        nivel = "critico"
        vereditos = [
            "O PC está bem sobrecarregado agora.",
            "A carga está alta e já pode causar lentidão.",
            "Ele está no limite; alguma coisa está puxando bastante recurso.",
            "Está pesado de verdade. Melhor descobrir quem está causando isso.",
        ]

    aberturas = [
        f"CPU em {cpu:.0f}% e memória em {ram:.0f}%",
        f"Agora a CPU está em {cpu:.0f}% e a RAM em {ram:.0f}%",
        f"Dei uma olhada: CPU {cpu:.0f}%, RAM {ram:.0f}%",
        f"O retrato agora é CPU {cpu:.0f}% e memória {ram:.0f}%",
    ]
    msg = escolher_sem_repeticao(
        aberturas,
        fallback=aberturas[0],
        escolha_aleatoria=random.choice,
    )
    if temp is not None:
        msg += f", temperatura {temp}°C"
    veredito = escolher_sem_repeticao(
        vereditos,
        fallback=vereditos[0],
        escolha_aleatoria=random.choice,
    )
    msg += f". {veredito}"

    metrica = "cpu" if cpu >= 60 else ("memoria" if ram >= 70 else "")
    culpado = identificar_processo_culpado(psutil_mod, metrica) if metrica else "nenhum em destaque"
    if culpado not in {"nenhum em destaque", "nenhum processo detectado"}:
        motivo = "memória" if metrica == "memoria" else "CPU"
        complementos = [
            f"Quem mais está usando {motivo} é {culpado}.",
            f"O processo que mais aparece nessa conta é {culpado}.",
            f"Neste momento, {culpado} é quem mais está puxando {motivo}.",
        ]
        msg += " " + escolher_sem_repeticao(
            complementos,
            fallback=complementos[0],
            escolha_aleatoria=random.choice,
        )
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
    deve_parar: Callable[[], bool] | None = None,
    aguardar_fn: Callable[[float], bool] | None = None,
) -> None:
    print_fn("🩺 [SAÚDE] Monitor de saúde iniciado (CPU/RAM/Temp + anti-falso-positivo)")
    estado.setdefault("cpu_alta_desde", 0.0)
    estado.setdefault("ultimo_aviso", 0.0)

    while not (callable(deve_parar) and deve_parar()):
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

            if ram >= ram_threshold and (agora - float(estado.get("ultimo_aviso") or 0.0)) > 900:
                estado["ultimo_aviso"] = agora
                falar_status_cb()
        except Exception as e:
            print_fn(f"⚠️ [SAÚDE] Erro no daemon: {e}")

        if callable(aguardar_fn):
            if aguardar_fn(5):
                break
        else:
            sleep_fn(5)


def detectar_comando_saude(texto: str) -> bool:
    t = str(texto or "").lower().strip()
    triggers = [
        "como tá o pc", "como ta o pc", "como está o pc",
        "tá pesado", "ta pesado", "status do pc",
        "saúde do pc", "como anda o pc", "tá quente o pc",
        "como está a saúde do computador", "como esta a saude do computador",
        "saúde do computador", "saude do computador",
        "status do computador", "como está o computador", "como esta o computador",
        "como esta o meu pc", "como está o meu pc", "como esta meu pc", "como está meu pc",
        "qual a saude dele", "qual a saúde dele",
    ]
    return any(trig in t for trig in triggers)
