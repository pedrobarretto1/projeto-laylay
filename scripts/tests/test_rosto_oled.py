"""Contratos da projeção periférica: causa, transporte, receipt e composição."""
from copy import deepcopy
import time
from types import SimpleNamespace

import pytest

from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional
from mente_laylay.especialistas.rosto_oled_runtime import (
    EMOCOES_ROSTO, RostoOledRuntime, projetar_rosto, criar_rosto_oled_runtime,
)
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.integracao.composicao_rosto_oled import criar_composicao_rosto_oled_runtime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
from mente_laylay.memoria_mental.atividade_operacional_runtime import criar_atividade_operacional_runtime


@pytest.fixture(autouse=True)
def isolar_pareamento_pessoal_do_pc(monkeypatch, tmp_path):
    # Estes contratos cobrem USB; o pareamento real do usuario nunca e fixture.
    # Os contratos TCP configuram seu proprio endpoint em test_corpo_wifi_transporte.
    monkeypatch.setenv("LAYLAY_CORPO_WIFI_CONFIG", str(tmp_path / "sem_pareamento_wifi.json"))


def estado_emocional(emocao="alegre", permitido=True, idade=0):
    agora = time.time() - idade
    evento = criar_evento_emocional_causal(
        origem="controle_rosto", causa="causa pessoal não transmitida",
        evidencia_ref="teste:rosto", natureza_evidencia="fato_observado",
        responsabilidade="usuario", confianca=.97, relevancia=.95,
        intensidade=2, permite_expressao=permitido, emocao=emocao, nivel=2,
        ts=agora, validade_s=120,
    )
    return aplicar_evento_emocional({}, evento, agora=agora)


class EspSerial:
    """Dublê somente da porta física; mente e contrato emocional são reais."""
    def __init__(self, *, ack=True, incorreto=False, pronto=True, fragmentar=False,
                 hack=False, ack_atividade=True):
        self.ack, self.incorreto, self.pronto = ack, incorreto, pronto
        self.fragmentar = fragmentar
        self.hack, self.ack_atividade = hack, ack_atividade
        self.enviados = []
        self.rx = bytearray()
        self.fechado = False

    def write(self, dados):
        texto = dados.decode().strip()
        self.enviados.append(texto)
        partes = texto.split()
        if partes[0] == "HELLO" and self.pronto:
            self.rx.extend(f"READY 1 {partes[2]} SSD1306 128 64\n".encode())
        elif partes[0] == "CAPS":
            resposta = f"CAPS 1 {partes[2]} HACK1" if self.hack else "ERROR 1 PACOTE_INVALIDO"
            self.rx.extend((resposta + "\n").encode())
        elif partes[0] in {"GCAPS", "MCAPS", "SCAPS", "LCAPS", "ECAPS", "RCAPS", "DCAPS"}:
            # Firmware anterior rejeita extensões desconhecidas. Isto mantém
            # os testes com clock congelado fiéis ao parser antigo real.
            self.rx.extend(b"ERROR 1 PACOTE_INVALIDO\n")
        elif partes[0] == "ACTIVITY" and self.hack and self.ack_atividade:
            self.rx.extend(("AACK " + " ".join(partes[1:-1]) + "\n").encode())
        elif partes[0] == "FACE" and self.ack:
            if self.incorreto:
                partes[3] = "0"  # Receipt de outra sequência nunca confirma esta.
            self.rx.extend(("ACK " + " ".join(partes[1:-1]) + "\n").encode())
        return len(dados)

    def read(self, quantidade):
        tamanho = 3 if self.fragmentar else quantidade
        dados = bytes(self.rx[:tamanho])
        del self.rx[:tamanho]
        return dados

    def close(self):
        self.fechado = True


class Relogio:
    def __init__(self):
        self.agora = 0.
    def __call__(self):
        self.agora += .02
        return self.agora


@pytest.mark.parametrize("emocao", EMOCOES_ROSTO[1:])
def test_rosto_reutiliza_emocao_causal_vigente_sem_reinterpretar(emocao):
    estado = estado_emocional(emocao)
    antes = deepcopy(estado)
    assert projetar_rosto(estado) == (EMOCOES_ROSTO.index(emocao), 2, 0)
    assert estado == antes


@pytest.mark.parametrize("estado", [
    {"current_emotion": "brava", "emotion_level": 3},
    estado_emocional(permitido=False), estado_emocional(idade=150),
])
def test_emocao_sem_causa_permitida_ou_vigente_nao_chega_ao_rosto(estado):
    assert projetar_rosto(estado) == (0, 1, 0)


def test_envio_conta_como_confirmado_so_apos_ack_da_mesma_sessao_sequencia_e_pose():
    esp = EspSerial(fragmentar=True)
    estado = estado_emocional()
    estado["is_speaking"] = True
    runtime = RostoOledRuntime(estado_getter=lambda: estado, porta="TESTE", abrir_serial=lambda _: esp)
    assert not runtime.diagnostico()["aplicacao_confirmada"]
    assert runtime.sincronizar()
    assert esp.enviados[0].startswith("HELLO 1")
    assert runtime.diagnostico()["confirmado"] == [1, 2, 0]
    assert not runtime.diagnostico()["prova_optica"]
    assert "causa pessoal" not in str(esp.enviados)


@pytest.mark.parametrize("opcoes", [{"ack": False}, {"incorreto": True}, {"pronto": False}])
def test_falha_parcial_nunca_vira_sucesso_do_corpo(opcoes):
    esp = EspSerial(**opcoes)
    runtime = RostoOledRuntime(estado_getter=lambda: estado_emocional(), porta="TESTE",
                              abrir_serial=lambda _: esp, monotonic=Relogio())
    assert not runtime.sincronizar()
    assert not runtime.diagnostico()["aplicacao_confirmada"]
    assert esp.fechado
    if not opcoes.get("pronto", True):
        assert not any(linha.startswith("FACE") for linha in esp.enviados)


def test_receipt_expira_sem_promover_conexao_a_confirmacao():
    relogio = Relogio()
    esp = EspSerial()
    runtime = RostoOledRuntime(estado_getter=lambda: {}, porta="TESTE",
                              abrir_serial=lambda _: esp, monotonic=relogio)
    assert runtime.sincronizar()
    relogio.agora += 4
    assert runtime.diagnostico()["conectado"]
    assert not runtime.diagnostico()["aplicacao_confirmada"]


def test_reconexao_le_estado_atual_em_vez_de_reexecutar_uma_emocao_antiga():
    estado = estado_emocional("brava")
    primeiro, segundo = EspSerial(ack=False), EspSerial()
    portas = iter([primeiro, segundo])
    runtime = RostoOledRuntime(estado_getter=lambda: estado, porta="TESTE",
                              abrir_serial=lambda _: next(portas), monotonic=Relogio())
    assert not runtime.sincronizar()
    estado = {"current_emotion": "calma"}
    assert runtime.sincronizar()
    assert runtime.diagnostico()["confirmado"] == [0, 1, 0]
    assert primeiro.enviados[0] != segundo.enviados[0]


def test_sem_porta_explicitamente_configurada_nao_abre_dispositivo():
    def proibido(_):
        pytest.fail("configuração ausente não autoriza abrir porta")
    runtime = RostoOledRuntime(estado_getter=lambda: {}, abrir_serial=proibido)
    assert not runtime.sincronizar()


def test_composicao_compartilha_owner_da_mente_e_publica_diagnostico_sem_escrever_emocao():
    mente = criar_estado_compartilhado_runtime(conversacional=estado_emocional("surpresa"))
    esp = EspSerial()
    class Observabilidade:
        def relatar_falha(self, *args, **kwargs):
            pytest.fail("caminho de sucesso")
    runtime = criar_composicao_rosto_oled_runtime(
        estado=mente, observabilidade=Observabilidade(), porta="TESTE", abrir_serial=lambda _: esp,
    )
    antes = mente.retrato_dominio("conversacional")
    assert runtime.sincronizar()
    assert mente.mental["rosto_oled"]["aplicacao_confirmada"]
    assert mente.retrato_dominio("conversacional") == antes
    mente.atualizar_campos("conversacional", is_speaking=True)
    assert runtime.sincronizar()
    assert runtime.diagnostico()["confirmado"] == [5, 2, 0]
    runtime.encerrar()
    assert esp.fechado and not mente.mental["rosto_oled"]["aplicacao_confirmada"]


@pytest.mark.parametrize("pergunta", [
    "Você consegue mostrar suas emoções no OLED?", "Você pode ter um rostinho no ESP32?",
    "Você consegue mostrar uma animação de hack no OLED?",
])
def test_catalogo_e_perguntas_naturais_exigem_confirmacao_viva_do_rosto(pergunta):
    esp = EspSerial()
    runtime = RostoOledRuntime(estado_getter=lambda: {}, porta="TESTE", abrir_serial=lambda _: esp)
    disponibilidade = DisponibilidadeOperacionalRuntime(rosto_oled_getter=runtime.diagnostico)
    mapa = MapaHabilidadesRuntime()
    mapa.conectar_disponibilidade_operacional(disponibilidade.snapshot)
    assert "indisponível" in mapa.responder_pergunta_capacidade(pergunta)
    assert runtime.sincronizar()
    assert "rosto_oled [disponivel]" in mapa.contexto_para_prompt(pergunta)
    assert "ACK" in mapa.responder_pergunta_capacidade(pergunta)
    assert "HACK1" in mapa.responder_pergunta_capacidade(pergunta)
    assert "não confirmam sucesso" in mapa.responder_pergunta_capacidade(pergunta)
    assert mapa.evidencia_conversacional(pergunta)["autoriza_execucao"] is False


def test_retrato_de_dominio_nao_permite_mutacao_da_mente_pelo_consumidor():
    mente = criar_estado_compartilhado_runtime(conversacional=estado_emocional())
    copia = mente.retrato_dominio("conversacional")
    copia["episodio_emocional"]["emocao"] = "triste"
    assert mente.retrato_dominio("conversacional")["episodio_emocional"]["emocao"] == "alegre"


def test_raiz_real_registra_rosto_e_supervisor_sem_abrir_porta_ao_importar(monkeypatch, tmp_path):
    import importlib
    # Isola somente a identidade da trava, sem iniciar outro main ou disputar USB.
    from mente_laylay.integracao import instancia_unica
    adquirir = instancia_unica.adquirir_instancia_unica
    monkeypatch.setattr(instancia_unica, "adquirir_instancia_unica",
                        lambda _: adquirir(tmp_path / "composicao_rosto"))
    root = importlib.import_module("laylay")
    runtime = root._rosto_oled_runtime
    assert root._registro_servicos_aplicacao_runtime.snapshot()["_rosto_oled_runtime"] is runtime
    target = root._composicao_servicos_runtime.catalogo_threads()["Laylay-Rosto-OLED"]
    assert target.func.__self__ is runtime
    assert runtime._serial is None
    assert runtime.autodetectar is True
    assert runtime.estado_getter() == root._estado_compartilhado_runtime.retrato_dominio("conversacional")


def test_supervisor_interrompe_espera_de_hardware_e_fecha_porta():
    esp = EspSerial(pronto=False)
    chamadas = []
    falhas = []
    def deve_parar():
        chamadas.append(True)
        return len(chamadas) >= 3
    runtime = RostoOledRuntime(estado_getter=lambda: {}, porta="TESTE", abrir_serial=lambda _: esp,
                              relatar_falha=lambda *args, **kwargs: falhas.append(args))
    runtime.executar(deve_parar=deve_parar, aguardar_fn=lambda _: True)
    assert esp.fechado and not falhas
    assert runtime.diagnostico()["motivo"] == "encerrado"


def inventario_usb(monkeypatch, portas):
    from serial.tools import list_ports
    monkeypatch.delenv("LAYLAY_ROSTO_PORTA", raising=False)
    monkeypatch.setattr(list_ports, "comports", lambda: portas)


def usb(porta="COM4", vid=0x303A, pid=0x1001):
    return SimpleNamespace(device=porta, vid=vid, pid=pid)


def test_inicializacao_sem_porta_configurada_detecta_esp_e_sincroniza(monkeypatch):
    inventario_usb(monkeypatch, [usb("COM1", vid=None, pid=None), usb()])
    abertas = []
    esp = EspSerial()
    runtime = criar_rosto_oled_runtime(
        estado_getter=lambda: estado_emocional("alegre"),
        abrir_serial=lambda porta: abertas.append(porta) or esp,
    )
    assert runtime.sincronizar(), "primeira fronteira: ESP presente, mas a fábrica ainda exige COM manual"
    assert abertas == ["COM4"]
    assert runtime.diagnostico()["confirmado"] == [1, 2, 0]


def test_supervisor_continua_procurando_quando_esp_chega_depois_da_abertura(monkeypatch):
    portas = []
    inventario_usb(monkeypatch, portas)
    esp = EspSerial()
    abertas, esperas = [], []
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {},
                                     abrir_serial=lambda p: abertas.append(p) or esp)
    def aguardar(segundos):
        esperas.append(segundos)
        if len(esperas) == 1:
            assert not abertas, "ausência de ESP não pode abrir COM1"
            portas.append(usb("COM7"))
            return False
        assert runtime.diagnostico()["aplicacao_confirmada"]
        return True
    runtime.executar(deve_parar=lambda: False, aguardar_fn=aguardar)
    assert abertas == ["COM7"] and len(esperas) == 2
    assert esp.fechado


@pytest.mark.parametrize("portas", [[], [usb("COM1", None, None)], [usb(), usb("COM7")]])
def test_autodeteccao_nao_abre_usb_alheio_ou_escolhe_entre_placas_ambiguas(monkeypatch, portas):
    inventario_usb(monkeypatch, portas)
    def proibido(_):
        pytest.fail("sem candidato único não pode abrir serial")
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=proibido)
    assert not runtime.sincronizar()
    assert not runtime.diagnostico()["aplicacao_confirmada"]


def test_esp_com_firmware_alheio_nao_recebe_expressao(monkeypatch):
    inventario_usb(monkeypatch, [usb()])
    esp = EspSerial(pronto=False)
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=lambda _: esp,
                                     monotonic=Relogio())
    assert not runtime.sincronizar()
    assert esp.enviados and all(linha.startswith("HELLO 1 ") for linha in esp.enviados)
    assert esp.fechado


def test_reconexao_automatica_redescobre_porta_e_usa_emocao_atual(monkeypatch):
    portas = [usb("COM4")]
    inventario_usb(monkeypatch, portas)
    esp1, esp2 = EspSerial(), EspSerial()
    abertas = []
    estado = estado_emocional("brava")
    def abrir(porta):
        abertas.append(porta)
        return esp1 if porta == "COM4" else esp2
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: estado, abrir_serial=abrir,
                                     monotonic=Relogio())
    assert runtime.sincronizar()
    esp1.ack = False
    assert not runtime.sincronizar()
    portas[:] = [usb("COM7")]
    estado = {"current_emotion": "calma"}
    assert runtime.sincronizar()
    assert abertas == ["COM4", "COM7"]
    assert runtime.diagnostico()["confirmado"] == [0, 1, 0]


def test_configuracao_manual_preserva_alvo_e_dispensa_autodeteccao(monkeypatch):
    inventario_usb(monkeypatch, [usb(), usb("COM7")])
    monkeypatch.setenv("LAYLAY_ROSTO_PORTA", "COM8")
    esp = EspSerial()
    abertas = []
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {},
                                     abrir_serial=lambda p: abertas.append(p) or esp)
    assert runtime.sincronizar() and abertas == ["COM8"]


def test_autodeteccao_pode_ser_desligada_explicitamente(monkeypatch):
    inventario_usb(monkeypatch, [usb()])
    monkeypatch.setenv("LAYLAY_ROSTO_PORTA", "off")
    def proibido(_):
        pytest.fail("off não permite abrir serial")
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=proibido)
    assert not runtime.sincronizar()


def test_porta_ocupada_aguarda_liberacao_sem_anunciar_conexao(monkeypatch):
    inventario_usb(monkeypatch, [usb()])
    esp = EspSerial()
    tentativas = []
    falhas = []
    def abrir(porta):
        tentativas.append(porta)
        if len(tentativas) < 3:
            raise PermissionError("porta_ocupada")
        return esp
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=abrir,
                                     relatar_falha=lambda *args, **kwargs: falhas.append(args))
    assert not runtime.sincronizar()
    assert not runtime.diagnostico()["conectado"]
    assert not runtime.sincronizar()
    assert len(falhas) == 1, "espera por porta ocupada não deve gerar log idêntico repetido"
    assert runtime.sincronizar()
    assert runtime.diagnostico()["aplicacao_confirmada"]


def test_intervalo_sem_heartbeats_renova_sessao_antes_de_acordar_com_pose_atual():
    esp = EspSerial()
    relogio = Relogio()
    estado = estado_emocional("brava")
    runtime = RostoOledRuntime(porta="COM4", estado_getter=lambda: estado,
                               abrir_serial=lambda _: esp, monotonic=relogio)
    assert runtime.sincronizar()
    sessao_anterior = esp.enviados[0]
    relogio.agora += 4
    estado = estado_emocional("envergonhada")
    assert runtime.sincronizar()
    # Cada extensão negocia entre HELLO e FACE; renovação continua canônica.
    hello_atual = next(p for p in reversed(esp.enviados) if p.startswith("HELLO 1 "))
    assert hello_atual != sessao_anterior
    negociacao = esp.enviados[esp.enviados.index(hello_atual):]
    assert [p.split()[0] for p in negociacao] == ["HELLO", "CAPS", "GCAPS", "MCAPS", "LCAPS", "SCAPS", "ECAPS", "RCAPS", "DCAPS", "FACE"]
    assert " 1 6 2 0 3500" in esp.enviados[-1]


def test_hack_negociado_reutiliza_atividade_observada_sem_transmitir_dados_da_acao():
    mente = criar_estado_compartilhado_runtime(
        conversacional=estado_emocional("envergonhada"),
        mental={"atividade_operacional": {"origem": "atividade_operacional_observada", "ativos": 1, "ultimo_inicio_monotonic": time.monotonic()},
                "plano_turno_atual": {"comandos": [{"intent": "DELETE_ITEM", "alvo": "privado.txt"}]}},
    )
    esp = EspSerial(hack=True)
    runtime = criar_composicao_rosto_oled_runtime(
        estado=mente, observabilidade=SimpleNamespace(relatar_falha=lambda *a, **k: None),
        porta="TESTE", abrir_serial=lambda _: esp,
    )
    antes = mente.snapshot()
    assert runtime.sincronizar()
    assert any(p.startswith("CAPS 1 ") for p in esp.enviados), "primeira fronteira: negociar efeito com firmware"
    atividade = [p.split() for p in esp.enviados if p.startswith("ACTIVITY 1 ")]
    assert atividade and atividade[-1][4:] == ["1", "1200"]
    assert runtime.diagnostico()["hack"]["aplicacao_confirmada"]
    assert runtime.diagnostico()["confirmado"] == [6, 2, 0]
    assert mente.retrato_dominio("conversacional") == antes["conversacional"]
    assert not any("privado" in p or "DELETE" in p or p.startswith("MOTOR") for p in esp.enviados)


def test_atividade_do_owner_chega_ao_oled_e_termina_sem_substituir_emocao():
    instante = [20.0]
    mente = criar_estado_compartilhado_runtime(conversacional=estado_emocional("triste"))
    owner = criar_atividade_operacional_runtime(estado=mente, monotonic=lambda: instante[0])
    esp = EspSerial(hack=True)
    runtime = criar_composicao_rosto_oled_runtime(
        estado=mente, observabilidade=SimpleNamespace(relatar_falha=lambda *a, **k: None),
        porta="TESTE", abrir_serial=lambda _: esp, monotonic=lambda: instante[0],
    )
    with owner.escopo():
        assert runtime.sincronizar()
        assert runtime.diagnostico()["hack"]["ativo"]
        instante[0] += 1.0
        assert runtime.sincronizar()
        assert runtime.diagnostico()["hack"]["ativo"], "ação longa permanece visível"
    assert runtime.sincronizar()
    assert not runtime.diagnostico()["hack"]["ativo"]
    assert runtime.diagnostico()["confirmado"] == [2, 2, 0]
    assert mente.mental["atividade_operacional"]["ativos"] == 0


def test_firmware_anterior_continua_expressando_sem_receber_extensao_nao_negociada():
    esp = EspSerial()
    runtime = RostoOledRuntime(estado_getter=lambda: estado_emocional("brava"),
                              atividade_getter=lambda: {"origem": "atividade_operacional_observada", "ativos": 1},
                              porta="TESTE", abrir_serial=lambda _: esp)
    assert runtime.sincronizar()
    assert runtime.diagnostico()["confirmado"] == [3, 2, 0]
    assert not runtime.diagnostico()["hack"]["suportado"]
    assert not any(p.startswith("ACTIVITY") for p in esp.enviados)


@pytest.mark.parametrize("incorreto", [False, True])
def test_falha_de_ack_do_overlay_nao_falsifica_confirmacao_nem_perde_face(incorreto):
    class SemConfirmacao(EspSerial):
        def write(self, dados):
            tamanho = super().write(dados)
            if incorreto and dados.startswith(b"ACTIVITY"):
                self.rx.extend(b"AACK 1 sessao_antiga 1 1\n")
            return tamanho
    esp = SemConfirmacao(hack=True, ack_atividade=False)
    runtime = RostoOledRuntime(estado_getter=lambda: {}, porta="TESTE", abrir_serial=lambda _: esp,
                              monotonic=Relogio())
    assert runtime.sincronizar()
    assert runtime.diagnostico()["aplicacao_confirmada"]
    assert runtime.diagnostico()["hack"]["suportado"]
    assert not runtime.diagnostico()["hack"]["aplicacao_confirmada"]
    assert not esp.fechado


def test_plano_e_atividade_visual_antiga_nao_disparam_hack():
    mente = criar_estado_compartilhado_runtime(
        mental={"plano_turno_atual": {"comandos": [{"intent": "OPEN_APP"}]},
                "atividade_visual": {"estado": "executing"},
                "atividade_operacional": {"ativos": 1}},
    )
    esp = EspSerial(hack=True)
    runtime = criar_composicao_rosto_oled_runtime(
        estado=mente, observabilidade=SimpleNamespace(relatar_falha=lambda *a, **k: None),
        porta="TESTE", abrir_serial=lambda _: esp,
    )
    assert runtime.sincronizar()
    assert [p for p in esp.enviados if p.startswith("ACTIVITY")][-1].endswith(" 0 1200")
    assert not runtime.diagnostico()["hack"]["ativo"]


def test_reconexao_de_hack_negocia_novamente_e_nao_restaura_atividade_terminada():
    atividade = {"origem": "atividade_operacional_observada", "ativos": 1}
    esp1, esp2 = EspSerial(hack=True), EspSerial(hack=True)
    portas = iter([esp1, esp2])
    runtime = RostoOledRuntime(
        estado_getter=lambda: {}, atividade_getter=lambda: atividade,
        porta="TESTE", abrir_serial=lambda _: next(portas), monotonic=Relogio(),
    )
    assert runtime.sincronizar()
    assert runtime.diagnostico()["hack"]["ativo"]
    esp1.ack = False
    assert not runtime.sincronizar()
    assert not runtime.diagnostico()["hack"]["aplicacao_confirmada"]
    atividade["ativos"] = 0
    assert runtime.sincronizar()
    assert esp1.enviados[0] != esp2.enviados[0]
    assert any(p.startswith("CAPS") for p in esp2.enviados)
    assert not runtime.diagnostico()["hack"]["ativo"]
