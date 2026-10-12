"""A configuração local não promove envio USB a conexão confirmada."""
import json
from pathlib import Path

import pytest

from scripts.configurar_corpo_wifi import preparar_pacote_wifi, salvar_conexao_wifi, aguardar_linha


def test_configuracao_preserva_utf8_sem_injetar_linhas_no_protocolo():
    token = "a" * 64
    pacote = preparar_pacote_wifi("Rede da família", "senha\n1234", token)
    assert pacote.count(b"\n") == 1
    campos = pacote.decode("ascii").split()
    assert bytes.fromhex(campos[2]).decode("utf-8") == "Rede da família"
    assert bytes.fromhex(campos[3]).decode("utf-8") == "senha\n1234"
    assert "senha" not in pacote.decode("ascii")


@pytest.mark.parametrize("ssid,senha,token", [
    ("", "12345678", "a" * 64), ("é" * 17, "12345678", "a" * 64),
    ("rede", "curta", "a" * 64), ("rede", "x" * 64, "a" * 64),
    ("rede", "12345678", "A" * 64), ("rede", "12345678", "abc"),
    ("rede\0outra", "12345678", "a" * 64), ("rede", "123456\00078", "a" * 64),
])
def test_parametros_invalidos_nao_chegam_a_usb_e_erro_nao_contem_credenciais(ssid, senha, token):
    with pytest.raises(ValueError) as erro:
        preparar_pacote_wifi(ssid, senha, token)
    assert senha not in str(erro.value) and token not in str(erro.value)


def test_rede_aberta_tem_campo_explicito_sem_omitir_pareamento():
    assert preparar_pacote_wifi("rede", "", "a" * 64).split()[3] == b"-"


def test_json_do_pc_guarda_pareamento_sem_senha_do_roteador(tmp_path):
    destino = tmp_path / "memoria" / "corpo_wifi.json"
    salvar_conexao_wifi(destino, "192.168.0.21", "a" * 64)
    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["host"] == "192.168.0.21" and dados["ativo"] is True
    assert dados["version"] == 1 and dados["token"] == "a" * 64
    assert not {"senha", "password", "ssid"}.intersection(dados)
    assert not destino.with_name(destino.name + ".tmp").exists()


def test_erro_usb_nao_divulga_resposta_que_poderia_conter_segredo():
    class Porta:
        def read(self, _n):
            return b"ERROR 1 minha_senha_secreta\n"
    import time
    with pytest.raises(ConnectionError) as erro:
        aguardar_linha(Porta(), lambda _s: False, time.monotonic() + 1)
    assert "minha_senha_secreta" not in str(erro.value)


def test_associacao_alternativa_nao_ativa_tcp_nem_salva_permissao(tmp_path, monkeypatch):
    import serial
    from scripts.configurar_corpo_wifi import configurar_rede
    from mente_laylay.especialistas import corpo_wifi_transporte
    class Usb:
        resposta = b""
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        def write(self, dados):
            self.resposta = (b"STOPPED 1\n" if dados == b"STOP\n" else
                             b"WIFI_CONFIGURED 1\n" if dados.startswith(b"WIFI_CONFIG ") else
                             b"WIFI_STATUS 1 CONNECTED 192.168.43.2 8765\n")
            return len(dados)
        def read(self, _n):
            dados, self.resposta = self.resposta, b""
            return dados
    monkeypatch.setattr(serial, "Serial", lambda *_a, **_k: Usb())
    monkeypatch.setattr(corpo_wifi_transporte, "abrir_corpo_tcp",
                        lambda *_a: pytest.fail("teste de associação não concede conexão TCP"))
    arquivo = tmp_path / "corpo_wifi.json"
    resultado = configurar_rede(ssid="teste", senha="12345678", porta="TESTE",
                                arquivo=arquivo, somente_associacao=True)
    assert resultado["somente_associacao"] is True and not resultado["rosto_confirmado"]
    assert not resultado["parada_confirmada"] and not arquivo.exists()


@pytest.mark.parametrize("indisponivel,sack,sucesso", [(2, True, True), (3, True, False), (0, False, False)])
def test_servidor_recente_so_ativa_apos_receipts_sem_repetir_motor(tmp_path, monkeypatch, indisponivel, sack, sucesso):
    import serial
    from scripts import configurar_corpo_wifi as configurador
    from scripts.tests.test_corpo_wifi_transporte import ServidorCorpo, TOKEN_TESTE
    from mente_laylay.especialistas import corpo_wifi_transporte as transporte
    class Usb:
        resposta = b""
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        def write(self, dados):
            self.resposta = (b"STOPPED 1\n" if dados == b"STOP\n" else
                             b"WIFI_CONFIGURED 1\n" if dados.startswith(b"WIFI_CONFIG ") else
                             b"WIFI_STATUS 1 CONNECTED 127.0.0.1 8765\n")
            return len(dados)
        def read(self, _n):
            dados, self.resposta = self.resposta, b""
            return dados
    monkeypatch.setattr(serial, "Serial", lambda *_a, **_k: Usb())
    monkeypatch.setattr(configurador.secrets, "token_hex", lambda _n: TOKEN_TESTE)
    monkeypatch.setattr(configurador.time, "sleep", lambda _s: None)
    arquivo = tmp_path / "corpo_wifi.json"
    esp = ServidorCorpo(sack=sack)
    abrir_real = transporte.abrir_corpo_tcp
    tentativas = []
    def abrir(config):
        tentativas.append(config)
        assert not arquivo.exists(), "pareamento nao pode ser ativado durante a tentativa"
        if len(tentativas) <= indisponivel:
            raise TimeoutError("servidor_recente_indisponivel")
        return abrir_real(transporte.ConfiguracaoCorpoWifi(host=config.host, porta=esp.porta, token=config.token))
    monkeypatch.setattr(transporte, "abrir_corpo_tcp", abrir)
    try:
        if sucesso:
            resultado = configurador.configurar_rede(ssid="rede", senha="12345678", porta="TESTE", arquivo=arquivo)
            assert resultado["rosto_confirmado"] and resultado["parada_confirmada"]
            assert arquivo.exists() and len(tentativas) == 3
        else:
            with pytest.raises(ConnectionError):
                configurador.configurar_rede(ssid="rede", senha="12345678", porta="TESTE", arquivo=arquivo)
            assert not arquivo.exists()
        assert not any(linha.startswith("MOTOR ") for linha in esp.enviados)
    finally:
        esp.close()
