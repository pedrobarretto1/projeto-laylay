"""A paleta refinada deve chegar às superfícies renderizadas pela interface real."""
from __future__ import annotations

import json

import pytest

from scripts.tests.test_terminal_web_v1_estabilidade import conversa_web


def test_paleta_plum_nocturne_no_runtime_preserva_acento_ciano_e_estados(conversa_web):
    _janela, _ponte, _entradas, js, aguardar = conversa_web

    js("LaylayInterface.goMode('full');LaylayInterface.goPage('home')")
    aguardar(lambda: js("!!document.querySelector('.presence .avatar-body')"))

    def capturar():
        return json.loads(js("""JSON.stringify((()=>{
          const estilo=seletor=>getComputedStyle(document.querySelector(seletor));
          const body=getComputedStyle(document.body);
          return {
            bodyBackground:body.backgroundColor,
            windowBackground:estilo('.window').backgroundColor,
            sidebarBackground:estilo('.sidebar').backgroundColor,
            activeColor:estilo('.nav button.active').color,
            activeBackground:estilo('.nav button.active').backgroundColor,
            accent:body.getPropertyValue('--accent').trim(),
            statusDot:estilo('.status i').backgroundColor,
            mascot:estilo('.presence .avatar-body').backgroundImage,
            dialogBackground:estilo('dialog').backgroundColor,
            dialogColor:estilo('dialog').color,
            dialogBorder:estilo('dialog').borderTopColor
          };
        })())"""))

    paleta = capturar()
    assert paleta["bodyBackground"] == "rgb(16, 13, 21)", paleta
    assert paleta["windowBackground"] == "rgb(23, 19, 30)", paleta
    assert paleta["sidebarBackground"] == "rgb(27, 23, 33)", paleta
    assert paleta["activeColor"] == "rgb(182, 154, 221)", paleta
    assert paleta["accent"] == "#b69add", paleta
    assert paleta["statusDot"] == "rgb(138, 203, 176)", paleta
    assert "rgb(217, 182, 255)" in paleta["mascot"], paleta
    assert paleta["dialogBackground"] == "rgb(33, 27, 42)", paleta
    assert paleta["dialogColor"] == "rgb(242, 237, 247)", paleta
    assert paleta["dialogBorder"] == "rgb(57, 48, 68)", paleta

    js("LaylayInterface.request('preferencia',{name:'cor',value:'cyan'})")
    aguardar(lambda: js("document.body.classList.contains('cyan')"))
    aguardar(lambda: js("getComputedStyle(document.querySelector('.nav button.active')).color==='rgb(145, 203, 215)'"))
    ciano = capturar()
    assert ciano["bodyBackground"] == paleta["bodyBackground"], ciano
    assert ciano["windowBackground"] == paleta["windowBackground"], ciano
    assert ciano["accent"] == "#91cbd7", ciano
    assert ciano["activeColor"] == "rgb(145, 203, 215)", ciano
    assert ciano["activeBackground"] == "rgba(145, 203, 215, 0.12)", ciano
    assert ciano["statusDot"] == paleta["statusDot"], ciano

    js("LaylayInterface.goPage('settings')")
    aguardar(lambda: js("!!document.querySelector('.pr-settings .tp-provider')"))
    controles = json.loads(js("""JSON.stringify((()=>{
      const estilo=seletor=>getComputedStyle(document.querySelector(seletor));
      return {
        provider:estilo('.pr-settings .tp-provider:not(.active)').backgroundColor,
        selectedProvider:estilo('.pr-settings .tp-provider.active').backgroundColor,
        field:estilo('.pr-settings .tp-formfield input').backgroundColor,
        selected:estilo('.pr-settings-link.active').backgroundColor
      };
    })())"""))
    assert controles["provider"] == "rgb(33, 27, 42)", controles
    assert controles["selectedProvider"] == "rgba(145, 203, 215, 0.12)", controles
    assert controles["field"] == "rgb(33, 27, 42)", controles
    assert controles["selected"] == "rgba(145, 203, 215, 0.12)", controles


@pytest.mark.parametrize(
    ("pagina", "seletor", "estrutura"),
    [
        ("home", ".home-inteligente", ".home-layout"),
        ("chat", ".chat-view", ".chat-history"),
        ("music", ".pr-music", ".tp-player"),
        ("system", ".pr-system", ".tp-chart-grid"),
        ("settings", ".pr-settings", ".pr-settings-nav"),
        ("memory", ".pr-memory", ".pr-memory-filters"),
        ("lamp", ".pr-lamp", ".pr-device-grid"),
        ("dev", ".pr-dev", ".tp-terminal"),
        ("streaming", ".pr-streaming", "#streaming-viewport"),
    ],
)
def test_acabamento_plum_cobre_todas_as_paginas_sem_remover_estrutura(
    conversa_web, pagina, seletor, estrutura
):
    _janela, _ponte, _entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('full')")
    js(f"LaylayInterface.goPage('{pagina}')")
    aguardar(lambda: js(f"!!document.querySelector('{seletor} {estrutura}')"))

    estilo = json.loads(
        js(
            f"""JSON.stringify((()=>{{
              const raiz=document.querySelector('{seletor}');
              const estilo=getComputedStyle(raiz);
              return {{
                page:!!raiz,
                structure:!!raiz.querySelector('{estrutura}'),
                background:estilo.backgroundImage,
                accent:estilo.getPropertyValue('--pr-lavender').trim()
              }};
            }})())"""
        )
    )
    assert estilo["page"] and estilo["structure"], estilo
    assert "radial-gradient" in estilo["background"], estilo
    assert estilo["accent"], estilo
