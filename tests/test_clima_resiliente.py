from __future__ import annotations

import requests

from mente_laylay.percepcao import ambiente_sistema
from mente_laylay.percepcao.ambiente_sistema import (
    obter_clima_localidade,
    obter_clima_open_meteo,
    obter_clima_wttr,
)


class _Resposta:
    def __init__(self, dados=None, *, texto="", status=200):
        self._dados = dados or {}
        self.text = texto
        self.status_code = status
        self.content = b"1" if dados else b""

    def json(self):
        return self._dados


def _limpar_cache():
    ambiente_sistema._COORDENADAS_CACHE.clear()
    ambiente_sistema._CLIMA_ATUAL_CACHE.clear()


def _get_com_reserva(url, **_kwargs):
    if "wttr.in" in url:
        raise requests.exceptions.ReadTimeout("lento")
    if "geocoding-api" in url:
        return _Resposta({
            "results": [{
                "name": "Boituva", "country_code": "BR",
                "latitude": -23.28, "longitude": -47.67,
                "timezone": "America/Sao_Paulo",
            }]
        })
    return _Resposta({
        "current": {
            "temperature_2m": 19.4,
            "apparent_temperature": 18.7,
            "relative_humidity_2m": 71,
            "weather_code": 2,
            "wind_speed_10m": 8.2,
            "wind_direction_10m": 140,
        }
    })


def test_briefing_recupera_clima_quando_wttr_expira():
    _limpar_cache()
    logs = []

    clima = obter_clima_wttr(
        "Boituva", requests_get=_get_com_reserva,
        print_fn=logs.append, timeout_s=0.5,
    )

    assert "19,4°C" in clima
    assert "umidade:71%" in clima
    assert "vento:8,2km/h" in clima
    assert any("fonte reserva" in item for item in logs)


def test_comando_weather_tambem_usa_reserva():
    _limpar_cache()
    dados = obter_clima_localidade(
        "Boituva", requests_get=_get_com_reserva, print_fn=lambda _msg: None,
    )

    assert dados["ok"] is True
    assert dados["fonte"] == "open_meteo"
    assert dados["descricao"] == "parcialmente nublado"
    assert dados["temperatura_c"] == "19,4"


def test_open_meteo_reutiliza_cache_por_cinco_minutos():
    _limpar_cache()
    chamadas = []

    def get(url, **kwargs):
        chamadas.append((url, kwargs))
        return _get_com_reserva(url, **kwargs)

    primeira = obter_clima_open_meteo("Boituva", requests_get=get, clock=lambda: 1000)
    segunda = obter_clima_open_meteo("Boituva", requests_get=get, clock=lambda: 1100)

    assert primeira["ok"] and segunda["ok"]
    assert segunda["cache"] is True
    assert len(chamadas) == 2


def test_wttr_expoe_probabilidade_de_chuva_do_dia() -> None:
    resposta = _Resposta({
        "current_condition": [{
            "temp_C": "21", "FeelsLikeC": "19", "humidity": "51",
            "weatherDesc": [{"value": "Smoky haze"}],
        }],
        "weather": [{
            "hourly": [
                {"time": "0", "chanceofrain": "10"},
                {"time": "1200", "chanceofrain": "65"},
                {"time": "1800", "chanceofrain": "30"},
            ],
        }],
    })

    dados = obter_clima_localidade(
        "Boituva", requests_get=lambda *_args, **_kwargs: resposta,
    )

    assert dados["ok"] is True
    assert dados["chance_chuva_pct"] == 65
    assert dados["previsao_chuva_disponivel"] is True
