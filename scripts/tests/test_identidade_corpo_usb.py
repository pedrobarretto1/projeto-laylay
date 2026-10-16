"""Pareamento escolhe o dispositivo observado, nunca a primeira porta ou o nome."""
from hashlib import sha256

import pytest
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime

from scripts.tests.test_recuperacao_corpo_usb import EspSaude
from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
from mente_laylay.integracao.configuracao_aplicacao import ConfiguracaoAplicacaoRuntime


UID = "112233445566"
ID = sha256(UID.encode()).hexdigest()[:16]
PAREAMENTO = {"dispositivo": ID, "nome": "Corpo da Laylay"}


def placa(uid=UID):
    esp = EspSaude()
    esp.uid = uid
    return esp


def runtime(portas, **kwargs):
    r = RostoOledRuntime(estado_getter=lambda: {}, autodetectar=True,
        listar_portas=lambda: tuple(portas), abrir_serial=portas.__getitem__, **kwargs)
    r.identidade_usb_getter = lambda: dict(PAREAMENTO)
    return r


def test_identidade_escolhe_corpo_entre_varias_portas_sem_acordar_outro_esp():
    outro, corpo = placa("aabbccddeeff"), placa()
    r = runtime({"COM4": outro, "COM8": corpo})
    try:
        assert r.sincronizar(), r.diagnostico()
        assert r.diagnostico()["porta_ativa"] == "COM8"
        assert r.diagnostico()["identidade_usb"]["verificada"]
        assert outro.fechado and all(x.startswith("HEALTH ") for x in outro.enviados)
        assert not any(x.startswith(("MOTOR ", "TURN ")) for x in corpo.enviados)
    finally:
        r.encerrar()


def test_corpo_pareado_ausente_nao_adota_outro_mesmo_com_porta_unica():
    outro = placa("aabbccddeeff")
    r = runtime({"COM4": outro})
    assert not r.sincronizar()
    assert not r.diagnostico()["aplicacao_confirmada"]
    assert outro.fechado and all(x.startswith("HEALTH ") for x in outro.enviados)


def test_configuracao_corporal_persiste_identidade_e_nome_sem_alterar_outros_campos(tmp_path):
    cfg = ConfiguracaoAplicacaoRuntime(raiz=tmp_path)
    cfg.arquivo_env.write_text("# pessoal\nOUTRA_CHAVE=preservar\n", encoding="utf8")
    assert cfg.definir_identidade_corpo_usb(**PAREAMENTO)["saved"]
    assert ConfiguracaoAplicacaoRuntime(raiz=tmp_path).identidade_corpo_usb() == PAREAMENTO
    assert "OUTRA_CHAVE=preservar" in cfg.arquivo_env.read_text(encoding="utf8")


def test_identidade_invalida_falha_antes_de_abrir_porta():
    abertas = []
    r = RostoOledRuntime(estado_getter=lambda: {}, autodetectar=True,
        listar_portas=lambda: ("COM4",), abrir_serial=lambda p: abertas.append(p))
    r.identidade_usb_getter = lambda: {"dispositivo": "invalido", "nome": "Corpo"}
    assert not r.sincronizar()
    assert not abertas


def test_duas_portas_anunciando_mesma_identidade_falham_fechadas():
    placas = {"COM4": placa(), "COM7": placa()}
    r = runtime(placas)
    assert not r.sincronizar()
    assert "identidade_usb_ambigua" in r.diagnostico()["motivo"]
    assert all(e.fechado and all(l.startswith("HEALTH ") for l in e.enviados) for e in placas.values())


def test_porta_muda_mas_identidade_pareada_continua_a_mesma():
    esp = placa();portas = {"COM4": esp}
    r = runtime(portas)
    assert r.sincronizar()
    esp.borda = 100
    r._fechar()  # Perda do fluxo, sem repetir ação.
    outro, novo = placa("aabbccddeeff"), placa()
    portas.clear();portas.update({"COM4": outro, "COM19": novo})
    try:
        assert r.sincronizar()
        assert r.diagnostico()["porta_ativa"] == "COM19"
        assert all(l.startswith("HEALTH ") for l in outro.enviados)
        assert not any(l.startswith(("MOTOR ", "TURN ")) for l in novo.enviados)
    finally:r.encerrar()


def test_porta_manual_tambem_exige_identidade_sem_procurar_substituto():
    esp = placa("aabbccddeeff")
    r = RostoOledRuntime(estado_getter=lambda:{}, porta="COM4", abrir_serial=lambda _:esp,
        listar_portas=lambda:pytest.fail("porta manual não enumera outras"),
        identidade_usb_getter=lambda:PAREAMENTO)
    assert not r.sincronizar()
    assert all(l.startswith("HEALTH ") for l in esp.enviados)


def test_firmware_sem_health_nao_e_adotado_pelo_nome_ou_porta():
    from scripts.tests.test_rosto_oled import EspSerial
    esp = EspSerial()
    r = runtime({"COM4":esp})
    assert not r.sincronizar()
    assert not r.diagnostico()["identidade_usb"]["verificada"]
    assert esp.fechado and all(l.startswith("HEALTH ") for l in esp.enviados)


def test_identidade_mudando_apos_hello_nao_recebe_face():
    class Troca(EspSaude):
        def write(self,dados):
            if dados.startswith(b"HELLO "):self.uid="aabbccddeeff"
            return super().write(dados)
    esp = Troca();r=runtime({"COM4":esp})
    assert not r.sincronizar()
    assert not any(l.startswith(("FACE ","MOTOR ","TURN ","SENTRY ")) for l in esp.enviados)


def test_encerramento_interrompe_sondagem_sem_abrir_mais_portas():
    esp=placa();r=runtime({"COM4":esp})
    r._deve_parar=lambda:True
    assert not r.sincronizar()
    assert not esp.enviados and not r.diagnostico()["conectado"]


def test_porta_alheia_ocupada_nao_impede_corpo_identificado_em_outra_porta():
    esp=placa()
    def abrir(porta):
        if porta=="COM4":raise PermissionError("ocupada")
        return esp
    r=RostoOledRuntime(estado_getter=lambda:{},autodetectar=True,
        listar_portas=lambda:("COM4","COM8"),abrir_serial=abrir,
        identidade_usb_getter=lambda:PAREAMENTO)
    try:
        assert r.sincronizar() and r.diagnostico()["porta_ativa"]=="COM8"
    finally:r.encerrar()


@pytest.mark.parametrize("nome",["a\nOUTRA=1", "a$VAR", "#comentario", " nome ", "x"*65])
def test_nome_invalido_nao_altera_configuracao(tmp_path,nome):
    cfg=ConfiguracaoAplicacaoRuntime(raiz=tmp_path)
    cfg.arquivo_env.write_text("OUTRA=preservar\n",encoding="utf8")
    with pytest.raises(ValueError):cfg.definir_identidade_corpo_usb(dispositivo=ID,nome=nome)
    assert cfg.arquivo_env.read_text(encoding="utf8")=="OUTRA=preservar\n"


@pytest.mark.parametrize("pergunta",[
    "Você reconhece seu corpo em outro PC?",
    "Você consegue reconhecer o ESP32 quando mudar a porta USB?",
    "Você sabe a identidade do corpo?",
])
def test_composicao_catalogo_dev_e_perguntas_descrevem_so_identidade_verificada(tmp_path,pergunta):
    from mente_laylay.integracao.composicao_rosto_oled import criar_composicao_rosto_oled_runtime
    from mente_laylay.integracao.dev_console_runtime import DevConsoleRuntime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
    from mente_laylay.especialistas.capacidades import consultar_capacidade
    cfg=ConfiguracaoAplicacaoRuntime(raiz=tmp_path)
    cfg.definir_identidade_corpo_usb(**PAREAMENTO)
    estado=criar_estado_compartilhado_runtime();esp=placa()
    class Observabilidade:
        def relatar_falha(self,*a,**k):pass
    r=criar_composicao_rosto_oled_runtime(estado=estado,observabilidade=Observabilidade(),
        porta="COM19",abrir_serial=lambda _:esp,identidade_usb_getter=cfg.identidade_corpo_usb)
    mapa=MapaHabilidadesRuntime(operacional_getter=DisponibilidadeOperacionalRuntime(rosto_oled_getter=r.diagnostico).snapshot)
    try:
        assert r.sincronizar()
        assert estado.obter_copia("mental","rosto_oled",{})["identidade_usb"]["verificada"]
        dev=DevConsoleRuntime();dev.configurar_corpo_getter(lambda:{"transporte":r.diagnostico()})
        assert dev.snapshot()["body"]["nome_corpo"]==PAREAMENTO["nome"]
        assert "verificada" in mapa.responder_pergunta_capacidade(pergunta)
        assert "HEALTH" in consultar_capacidade("CORPO_COMPANHIA")["identificacao_usb_condicional"]
    finally:r.encerrar()
    assert "não está confirmado" in mapa.responder_pergunta_capacidade(pergunta)


def test_raiz_real_injeta_pareamento_sem_abrir_serial_ao_importar():
    import laylay
    r=laylay._rosto_oled_runtime
    assert r.identidade_usb_getter.__self__ is laylay._configuracao_aplicacao_runtime
    assert r.identidade_usb_getter.__name__ == "identidade_corpo_usb"
    assert r._serial is None
