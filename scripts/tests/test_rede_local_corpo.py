"""Ciclo de vida do gerente existente; a fronteira Windows é substituída."""
import json
from types import SimpleNamespace
import pytest
import psutil
from mente_laylay.especialistas import corpo_wifi_transporte as modulo


def montar(tmp_path):
    (tmp_path / 'memoria').mkdir()
    (tmp_path / 'scripts').mkdir()
    pasta = tmp_path / 'artifacts' / 'rosto_oled' / 'wifi'
    pasta.mkdir(parents=True)
    script = tmp_path / 'scripts' / 'hotspot_corpo_windows.ps1'
    script.write_text('# fronteira de teste, nao executar')
    (tmp_path / 'memoria' / 'corpo_hotspot_windows.json').write_text(json.dumps(
        {'ssid': 'Laylay-Corpo-PC', 'modo': 'hosted_network_temporario'}))
    cfg = modulo.ConfiguracaoCorpoWifi('192.168.137.109', 8765, 'ab' * 32)
    return modulo.RedeLocalCorpoWindows(tmp_path), cfg, script, pasta / 'hotspot_windows.json'


def test_reutilizar_gerente_existente_nao_cria_nem_encerra_outro(tmp_path, monkeypatch):
    rede, cfg, script, recibo = montar(tmp_path)
    recibo.write_text(json.dumps({'pid': 123, 'estado': 'ativo', 'conexao_original_preservada': True}))
    monkeypatch.setattr(psutil, 'Process', lambda _: SimpleNamespace(
        name=lambda: 'powershell.exe', cmdline=lambda: ['powershell.exe', '-File', str(script)]))
    monkeypatch.setattr(modulo.subprocess, 'Popen', lambda *_a, **_k: pytest.fail('outro gerente'))
    rede.preparar(cfg)
    rede.encerrar()
    assert not (tmp_path / 'memoria' / 'corpo_hotspot_windows.parar').exists()


def test_gerente_criado_exige_receipt_proprio_e_encerra_pelo_protocolo_existente(tmp_path, monkeypatch):
    rede, cfg, script, recibo = montar(tmp_path)
    esperas = []
    processo = SimpleNamespace(pid=123, poll=lambda: None, wait=lambda **kw: esperas.append(kw))
    monkeypatch.setattr(psutil, 'Process', lambda _: SimpleNamespace(
        name=lambda: 'powershell.exe', cmdline=lambda: ['powershell.exe', '-File', str(script)]))
    def iniciar(args, **kwargs):
        assert args[-1] == str(script)
        assert kwargs['creationflags'] == modulo.subprocess.CREATE_NO_WINDOW
        recibo.write_text(json.dumps({'pid': 123, 'estado': 'ativo', 'conexao_original_preservada': True}))
        return processo
    monkeypatch.setattr(modulo.subprocess, 'Popen', iniciar)
    rede.preparar(cfg)
    rede.encerrar()
    assert (tmp_path / 'memoria' / 'corpo_hotspot_windows.parar').read_text() == 'parar'
    assert esperas == [{'timeout': 3}]


def test_configuracao_de_rede_externa_nao_ativa_hotspot(tmp_path, monkeypatch):
    rede, _, _, _ = montar(tmp_path)
    monkeypatch.setattr(modulo.subprocess, 'Popen', lambda *_a, **_k: pytest.fail('rede alheia'))
    rede.preparar(modulo.ConfiguracaoCorpoWifi('192.168.100.99', 8765, 'ab' * 32))
