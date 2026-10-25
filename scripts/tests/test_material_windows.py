"""Contratos para o material Fluent local da ilha (sem alterar o sistema)."""
from __future__ import annotations

from types import SimpleNamespace

from cliente.terminal_2 import material_windows as material


def test_desliga_material_sem_tocar_no_dwm(monkeypatch):
    chamadas = []
    monkeypatch.setattr(material, '_dwm_set', lambda *args: chamadas.append(args) or True)
    assert material.aplicar_material_windows(123, 'off') == 'fallback'
    assert material.aplicar_material_windows(0, 'acrylic') == 'fallback'
    assert chamadas == []


def test_win11_usa_atributo_documentado_e_pode_restaurar(monkeypatch):
    chamadas = []
    monkeypatch.setattr(material, 'sys', SimpleNamespace(
        platform='win32', getwindowsversion=lambda: SimpleNamespace(build=26300)))
    monkeypatch.setattr(material, '_dwm_set', lambda *args: chamadas.append(args) or True)
    assert material.aplicar_material_windows(123, 'acrylic') == 'acrylic'
    assert chamadas == [(123,38,3),(123,20,1),(123,33,2)]
    chamadas.clear()
    assert material.aplicar_material_windows(123, 'mica') == 'mica'
    assert chamadas == [(123,38,2),(123,20,1),(123,33,2)]
    chamadas.clear()
    material.restaurar_material_windows(123)
    assert chamadas == [(123,38,0),(123,33,0)]


def test_versao_incompatibilidade_ou_falha_dwm_usam_fallback(monkeypatch):
    chamadas = []
    monkeypatch.setattr(material, 'sys', SimpleNamespace(
        platform='win32', getwindowsversion=lambda: SimpleNamespace(build=22000)))
    monkeypatch.setattr(material, '_dwm_set', lambda *args: chamadas.append(args) or True)
    assert material.aplicar_material_windows(123, 'acrylic') == 'fallback'
    assert chamadas == []
    monkeypatch.setattr(material, 'sys', SimpleNamespace(
        platform='win32', getwindowsversion=lambda: SimpleNamespace(build=26300)))
    monkeypatch.setattr(material, '_dwm_set', lambda *args: chamadas.append(args) or False)
    assert material.aplicar_material_windows(123, 'acrylic') == 'fallback'
    assert chamadas == [(123,38,3)]


def test_linux_e_preferencia_desconhecida_nao_aplicam(monkeypatch):
    chamadas = []
    monkeypatch.setattr(material, 'sys', SimpleNamespace(platform='linux'))
    monkeypatch.setattr(material, '_dwm_set', lambda *args: chamadas.append(args) or True)
    assert material.aplicar_material_windows(123, 'acrylic') == 'fallback'
    assert material.aplicar_material_windows(123, 'blur_legacy') == 'fallback'
    assert chamadas == []

def test_default_fluent_nao_ativa_backdrop_retangular(monkeypatch):
    """Acrílico retangular vazava para fora da máscara Qt arredondada."""
    monkeypatch.delenv('LAYLAY_WINDOWS_BACKDROP', raising=False)
    chamadas = []
    monkeypatch.setattr(material, '_dwm_set', lambda *args: chamadas.append(args) or True)
    assert material.aplicar_material_windows(123) == 'fallback'
    assert chamadas == []
    monkeypatch.setenv('LAYLAY_WINDOWS_BACKDROP', 'acrylic')
    monkeypatch.setattr(material, 'sys', SimpleNamespace(
        platform='win32', getwindowsversion=lambda: SimpleNamespace(build=26300)))
    assert material.aplicar_material_windows(123) == 'acrylic'
    assert chamadas[0] == (123, 38, 3)
