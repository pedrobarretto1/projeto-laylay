"""Descoberta de dois canais conserva alvo único, sessão e ausência de replay."""
import json
import pytest
from types import SimpleNamespace
from scripts.tests.test_identidade_corpo_usb import placa, PAREAMENTO
from mente_laylay.especialistas.rosto_oled_runtime import criar_rosto_oled_runtime
from mente_laylay.especialistas.corpo_wifi_transporte import ConexaoCorpoIndisponivel


def montar(tmp_path, portas, rede, *, preferir_usb=True):
    cfg = tmp_path / 'wifi.json'
    cfg.write_text(json.dumps({'version': 1, 'ativo': True, 'host': '127.0.0.1',
        'hostname': 'laylay-corpo.local', 'porta': 8765, 'token': 'ab' * 32}))
    return criar_rosto_oled_runtime(porta='AUTO', preferir_usb=preferir_usb,
        config_wifi_path=cfg, estado_getter=lambda: {}, listar_portas=lambda: tuple(portas),
        abrir_serial=portas.__getitem__, abrir_tcp=lambda _: rede,
        identidade_usb_getter=lambda: PAREAMENTO)


@pytest.mark.parametrize('preferir_usb', [True, False])
def test_auto_usa_usb_pareado_e_nao_abre_rede(tmp_path, preferir_usb):
    usb = placa()
    r = montar(tmp_path, {'COM8': usb}, None, preferir_usb=preferir_usb)
    try:
        assert r.sincronizar()
        assert r.diagnostico()['transporte'] == 'serial'
        assert r.diagnostico()['porta_ativa'] == 'COM8'
    finally:
        r.encerrar()


def test_auto_sem_usb_usa_mesmo_corpo_na_rede(tmp_path):
    r = montar(tmp_path, {}, placa())
    try:
        assert r.sincronizar(), r.diagnostico()
        assert r.diagnostico()['transporte'] == 'tcp'
        assert r.diagnostico()['canal_autenticado']
    finally:
        r.encerrar()


def test_auto_nao_adota_usb_alheio_e_confere_identidade_tcp(tmp_path):
    outro = placa('aabbccddeeff')
    r = montar(tmp_path, {'COM7': outro}, placa('ffeeddccbbaa'))
    assert not r.sincronizar()
    assert not r.diagnostico()['aplicacao_confirmada']
    assert 'identidade_tcp_divergente' in r.diagnostico()['motivo']
    assert all(x.startswith('HEALTH ') for x in outro.enviados)


def test_reconexao_muda_canal_sem_reutilizar_sessao_ou_reenviar_movimento(tmp_path):
    portas = {}
    rede = placa()
    r = montar(tmp_path, portas, rede)
    try:
        assert r.sincronizar()
        sessao_rede = r.diagnostico()['sessao']
        r._fechar()
        portas['COM9'] = placa()
        assert r.sincronizar()
        assert r.diagnostico()['transporte'] == 'serial'
        assert r.diagnostico()['sessao'] != sessao_rede
        assert rede.fechado
        assert not any(l.startswith(('MOTOR ', 'TURN ')) for l in portas['COM9'].enviados)
    finally:
        r.encerrar()


def test_ambiguidade_usb_nao_escapa_pela_rede(tmp_path):
    rede = placa()
    r = montar(tmp_path, {'COM4': placa(), 'COM7': placa()}, rede)
    assert not r.sincronizar()
    assert 'identidade_usb_ambigua' in r.diagnostico()['motivo']
    assert not rede.enviados


@pytest.mark.parametrize('falha', [None, 'indisponivel', 'autenticacao'])
def test_preparar_rede_so_apos_falha_de_conexao_antes_da_autenticacao(tmp_path, falha):
    r = montar(tmp_path, {}, placa())
    chamadas = []
    preparar = []
    abrir = r.abrir_tcp
    def conectar(config):
        chamadas.append(1)
        if len(chamadas) == 1 and falha:
            if falha == 'indisponivel':
                raise ConexaoCorpoIndisponivel('sem_rede')
            raise ConnectionError('autenticacao_corpo_rejeitada')
        return abrir(config)
    r.abrir_tcp = conectar
    r.rede_local = SimpleNamespace(preparar=lambda _: preparar.append(1), encerrar=lambda: None)
    try:
        assert r.sincronizar() is (falha != 'autenticacao')
        assert bool(preparar) is (falha == 'indisponivel')
    finally:
        r.encerrar()
