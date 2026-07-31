from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch
import json
import os

from mente_laylay.autonomia.agendamento_mental import extrair_acao_agendada_local
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.orquestrador_deterministico import (
    DeteccaoDeterministicaRuntime,
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.porteiro_acoes import (
    texto_conversa_casual_sem_acao,
    texto_social_curto,
    texto_tem_comando_explicito,
)
from mente_laylay.cognicao.evidencia_operacional import (
    autoriza_candidato_iot_direto,
    detectar_consulta_lista_iot,
    texto_tem_evidencia_iot_parametro,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.iot.controlador import ControladorIoT
from mente_laylay.iot.configuracao import carregar_dispositivo_snapshot
from mente_laylay.iot.contratos import ResultadoProtocolo
from mente_laylay.iot.protocolos.simulado import ProtocoloSimulado
from mente_laylay.iot.protocolos.tuya import ProtocoloTuya
from mente_laylay.iot.registro import (
    RegistroDispositivos,
    criar_dispositivo_lampada,
    criar_dispositivo_ventilador,
)
from mente_laylay.iot.runtime import RuntimeIoT
from mente_laylay.memoria_mental.contexto_imediato import ContextoImediatoRuntime


class MemoriaIoTFalsa:
    def __init__(self) -> None:
        self.dispositivos = {}
        self.historico = []

    def salvar_dispositivo_iot(self, dados):
        self.dispositivos[dados["nome"]] = dict(dados)
        return dict(dados)

    def listar_dispositivos_iot(self, ambiente="", *, somente_ativos=True):
        return [
            dict(item) for item in self.dispositivos.values()
            if (not ambiente or item["ambiente"] == ambiente)
            and (not somente_ativos or item.get("ativo", True))
        ]

    def atualizar_estado_iot(self, nome, estado, **kwargs):
        self.dispositivos[nome]["estado"] = dict(estado)
        return dict(estado)

    def registrar_historico_iot(self, nome, **dados):
        self.historico.append({"nome": nome, **dados})
        return self.historico[-1]


class ClienteBulbFalso:
    def __init__(self) -> None:
        self.ligado = False
        self.chamadas = []

    def status(self):
        return {"dps": {"20": self.ligado}}

    def turn_on(self):
        self.ligado = True
        self.chamadas.append(("turn_on",))
        return {"dps": {"20": True}}

    def turn_off(self):
        self.ligado = False
        self.chamadas.append(("turn_off",))
        return {"dps": {"20": False}}

    def set_brightness_percentage(self, valor):
        self.chamadas.append(("brilho", valor))
        return {"dps": {"22": valor}}

    def set_colour(self, r, g, b):
        self.chamadas.append(("cor", r, g, b))
        return {"dps": {"24": "ok"}}

    def set_white_percentage(self, *, brightness, colourtemp):
        self.chamadas.append(("branco", brightness, colourtemp))
        return {"dps": {"22": brightness, "23": colourtemp}}


def test_registro_da_lampada_tem_controles_completos():
    lampada = criar_dispositivo_lampada()
    registro = RegistroDispositivos([lampada])

    assert registro.resolver("luz") == lampada
    assert lampada.configuracao["classe_tuya"] == "bulb"
    assert lampada.configuracao["dps_estado"] == "20"
    assert lampada.configuracao["snapshot_path"] == "dados/voz_pessoal/snapshot.json"
    assert lampada.configuracao["snapshot_fallback_paths"] == (
        "snapshot.json", "dados/voz_pessoal/devices.json", "devices.json",
    )
    assert {"ligar", "desligar", "ajustar_brilho", "ajustar_cor", "ajustar_branco"} <= lampada.capacidades


def test_configuracao_tuya_le_arquivo_devices_em_formato_de_lista(tmp_path):
    arquivo = tmp_path / "devices.json"
    arquivo.write_text(json.dumps([{
        "name": "LED BULB W5K",
        "id": "lampada-id",
        "key": "chave-local",
        "ip": "192.168.100.57",
        "ver": "3.5",
    }]), encoding="utf-8")

    dados = carregar_dispositivo_snapshot(str(arquivo), nome="LED BULB W5K")

    assert dados == {
        "device_id": "lampada-id",
        "local_key": "chave-local",
        "ip": "192.168.100.57",
        "version": "3.5",
    }


def test_tuya_escolhe_snapshot_mais_recente_sem_sobrepor_ambiente(tmp_path):
    antigo = tmp_path / "antigo.json"
    novo = tmp_path / "novo.json"
    base = {
        "name": "LED BULB W5K",
        "id": "lampada-id",
        "ip": "192.168.100.57",
        "ver": "3.5",
    }
    antigo.write_text(json.dumps([{**base, "key": "chave-antiga-000"}]), encoding="utf-8")
    novo.write_text(json.dumps([{**base, "key": "chave-nova-00000"}]), encoding="utf-8")
    os.utime(antigo, (1000, 1000))
    os.utime(novo, (2000, 2000))

    lampada = criar_dispositivo_lampada(protocolo="tuya")
    configuracao = dict(lampada.configuracao)
    configuracao["snapshot_path"] = str(antigo)
    configuracao["snapshot_fallback_paths"] = (str(novo),)
    lampada = replace(lampada, configuracao=configuracao)
    referencias = lampada.configuracao["variaveis"]
    ambiente_vazio = {nome: "" for nome in referencias.values()}

    with patch.dict("os.environ", ambiente_vazio, clear=False):
        dados, erro = ProtocoloTuya()._configuracao(lampada)

    assert erro == ""
    assert dados["local_key"] == "chave-nova-00000"


def test_controlador_simulado_ajusta_brilho_e_cor_sem_afetar_ventilador():
    lampada = criar_dispositivo_lampada()
    ventilador = criar_dispositivo_ventilador()
    protocolo = ProtocoloSimulado()
    protocolo.configurar(lampada.nome)
    protocolo.configurar(ventilador.nome)
    controlador = ControladorIoT(RegistroDispositivos([lampada, ventilador]), [protocolo])

    brilho = controlador.executar("ajustar_brilho", "luz", parametros={"valor": 45})
    cor = controlador.executar(
        "ajustar_cor", "lâmpada", parametros={"cor": "azul", "rgb": (0, 0, 255)}
    )
    fan = controlador.executar("ligar", "ventilador")

    assert (brilho.ok, brilho.status, brilho.detalhes["brilho"]) == (True, "brilho_ajustado", 45)
    assert (cor.ok, cor.status, cor.detalhes["rgb"]) == (True, "cor_ajustada", (0, 0, 255))
    assert (fan.ok, fan.status) == (True, "ligado")


def test_protocolo_tuya_usa_operacoes_de_bulb_sem_rede():
    lampada = criar_dispositivo_lampada(protocolo="tuya")
    referencias = lampada.configuracao["variaveis"]
    ambiente = {
        referencias["device_id"]: "id-de-teste",
        referencias["local_key"]: "chave-de-teste",
        referencias["ip"]: "192.0.2.10",
        referencias["version"]: "3.5",
    }
    cliente = ClienteBulbFalso()
    configuracoes = []

    def factory(**dados):
        configuracoes.append(dados)
        return cliente

    protocolo = ProtocoloTuya(cliente_factory=factory)
    with patch.dict("os.environ", ambiente, clear=False):
        ligado = protocolo.definir_estado(lampada, True)
        cor = protocolo.definir_parametros(
            lampada, "ajustar_cor", {"cor": "azul", "rgb": (0, 0, 255)}
        )
        branco = protocolo.definir_parametros(
            lampada, "ajustar_branco", {"cor": "branco quente", "brilho": 70, "temperatura": 10}
        )

    assert ligado.ok and cor.ok and branco.ok
    assert configuracoes and all(item["classe_tuya"] == "bulb" for item in configuracoes)
    assert all(item["tentativas"] == 2 for item in configuracoes)
    assert ("turn_on",) in cliente.chamadas
    assert ("cor", 0, 0, 255) in cliente.chamadas
    assert ("branco", 70, 10) in cliente.chamadas


def test_comando_explicito_prossegue_quando_apenas_consulta_previa_oscila():
    class ProtocoloOscilante:
        nome = "tuya"

        def __init__(self):
            self.consultas = 0
            self.definicoes = []

        def consultar_estado(self, _dispositivo):
            self.consultas += 1
            if self.consultas == 1:
                return ResultadoProtocolo(False, None, False, "timeout transitório")
            return ResultadoProtocolo(True, True, True)

        def definir_estado(self, _dispositivo, ligado):
            self.definicoes.append(ligado)
            return ResultadoProtocolo(True, ligado, True)

    lampada = criar_dispositivo_lampada(protocolo="tuya")
    protocolo = ProtocoloOscilante()
    controlador = ControladorIoT(RegistroDispositivos([lampada]), [protocolo])

    resultado = controlador.executar("ligar", "luz")

    assert resultado.ok is True
    assert resultado.status == "ligado"
    assert resultado.confirmado is True
    assert protocolo.definicoes == [True]


def test_runtime_entende_energia_brilho_cor_e_branco():
    estado = {}
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: estado,
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )

    ligar = runtime.detectar("liga a lâmpada")
    brilho = runtime.detectar("deixa o brilho da luz em 45%")
    cor = runtime.detectar("coloca a lâmpada azul")
    branco = runtime.detectar("deixa a luz em branco quente")
    feminina = runtime.detectar("deixa a lâmpada vermelha")
    azul_claro = runtime.detectar("deixa a luz do quarto azul claro")
    roxo_escuro = runtime.detectar("deixa a lâmpada roxo escuro")
    azul_pastel = runtime.detectar("coloca a luz azul pastel")
    comentario = runtime.detectar("acho a lâmpada azul bonita")
    dispositivos = runtime.detectar("quais dispositivos estão disponíveis?")
    retrato_quarto = runtime.retrato_para_mente("quais dispositivos tem no quarto?")

    assert ligar == {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}}
    assert brilho["params"] == {"acao": "ajustar_brilho", "alvo": "lampada_quarto", "valor": 45}
    assert cor["params"]["acao"] == "ajustar_cor" and cor["params"]["rgb"] == (0, 0, 255)
    assert branco["params"]["acao"] == "ajustar_branco" and branco["params"]["temperatura"] == 10
    assert feminina["params"]["cor"] == "vermelho" and feminina["params"]["rgb"] == (255, 0, 0)
    assert azul_claro["params"]["cor"] == "azul claro"
    assert azul_claro["params"]["rgb"] == (64, 64, 255)
    assert roxo_escuro["params"]["cor"] == "roxo escuro"
    assert roxo_escuro["params"]["rgb"] == (54, 0, 107)
    assert azul_pastel["params"]["cor"] == "azul pastel"
    assert azul_pastel["params"]["rgb"] == (166, 166, 255)
    assert comentario is None
    assert dispositivos == {"intent": "IOT_LIST", "params": {"ambiente": ""}}
    assert retrato_quarto["total_dispositivos"] == 2
    assert {
        item["nome"] for item in retrato_quarto["dispositivos"]
    } == {"lampada_quarto", "tomada_ventilador"}
    azul_ciano = runtime.detectar("deixa a luz do quarto azul ciano")
    assert azul_ciano["params"]["cor"] == "azul ciano"
    assert azul_ciano["params"]["rgb"] == (0, 128, 255)
    assert azul_ciano["params"]["cor_composta"] is True

    resultado_ligar = runtime.executar(ligar, "liga a lâmpada")
    estado.update({
        "ultima_acao_intent": "IOT_CONTROL",
        "ultima_acao_params": {"acao": "ligar", "alvo": "lampada_quarto"},
        "ultima_habilidade": "iot",
    })
    continuidade = runtime.detectar("deixa ela rosa")
    preto = runtime.detectar("coloca um preto")
    lilas = runtime.detectar("coloca um lilás")
    resultado_cor = runtime.executar(continuidade, "deixa ela rosa")
    resultado_vermelho = runtime.executar(feminina, "deixa a lâmpada vermelha")
    resultado_roxo_escuro = runtime.executar(roxo_escuro, "deixa a lâmpada roxo escuro")
    mais_clara = runtime.detectar("deixa ela mais clara")
    executado = runtime.executar(brilho, "deixa o brilho da luz em 45%")
    assert continuidade["params"]["acao"] == "ajustar_cor"
    assert continuidade["params"]["alvo"] == "lampada_quarto"
    assert continuidade["params"]["cor"] == "rosa"
    assert resultado_cor["status"] == "cor_ajustada"
    assert "a lâmpada do quarto rosa" in resultado_cor["plano_resposta"]["fala"]
    assert preto["intent"] == "SUGGEST_ACTION"
    assert preto["params"]["acao_sugerida"]["params"]["acao"] == "desligar"
    assert "não consegue emitir preto" in preto["params"]["fala"]
    assert lilas["params"]["acao"] == "ajustar_cor"
    assert lilas["params"]["cor"] == "lilás"
    assert "a lâmpada do quarto vermelha" in resultado_vermelho["plano_resposta"]["fala"]
    assert "a lâmpada do quarto roxa escura" in resultado_roxo_escuro["plano_resposta"]["fala"]
    assert mais_clara["params"]["acao"] == "ajustar_cor"
    assert mais_clara["params"]["cor"] == "roxo claro"
    assert mais_clara["params"]["rgb"] == (104, 64, 144)
    assert "a lâmpada do quarto" in resultado_ligar["plano_resposta"]["fala"]
    assert executado["ok"] is True
    assert executado["status"] == "brilho_ajustado"
    assert "45 por cento" in executado["plano_resposta"]["fala"]

    roteado = detectar_intencao_deterministica_mente(
        "coloca um preto",
        {
            "normalizar_texto": normalizar_texto,
            "detectar_intencao_iot": runtime.detectar,
            "mente_integrada_estado": estado,
            "limpar_destino_pc_b": lambda texto: texto,
            "target_from_params": lambda *_: "pc_a",
        },
    )
    assert roteado["intent"] == "SUGGEST_ACTION"
    assert roteado["params"]["origem"] == "cor_iot_sem_emissao"


def test_consulta_lista_iot_pura_identifica_ambiente_sem_runtime() -> None:
    assert detectar_consulta_lista_iot("quais dispositivos tem no quarto?") == {
        "intent": "IOT_LIST", "params": {"ambiente": "quarto"},
    }
    assert detectar_consulta_lista_iot("quais dispositivos estão disponíveis?") == {
        "intent": "IOT_LIST", "params": {"ambiente": ""},
    }
    assert detectar_consulta_lista_iot("como liga a luz?") is None


def test_parafrases_de_cor_iot_atravessam_o_porteiro_conversacional_completo():
    estado = {}
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: estado,
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )
    contexto = {
        "normalizar_texto": normalizar_texto,
        "detectar_intencao_iot": runtime.detectar,
        "mente_integrada_estado": estado,
        "texto_conversa_casual_sem_acao": texto_conversa_casual_sem_acao,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": texto_social_curto,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "texto_expresso_melhor_no_deterministico": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda *_: "pc_a",
    }

    frases = (
        "deixa a luz roxa",
        "deixa a lâmpada roxa",
        "pode deixar a luz roxa?",
        "muda a cor da luz para roxo",
        "ajusta a lâmpada para roxo",
        "define a luz como roxa",
        "torna a luz roxa",
        "quero a luz roxa",
    )
    for frase in frases:
        resultado = detectar_intencao_deterministica_mente(frase, contexto)
        assert resultado is not None, frase
        assert resultado["intent"] == "IOT_CONTROL", frase
        assert resultado["params"]["acao"] == "ajustar_cor", frase
        assert resultado["params"]["alvo"] == "lampada_quarto", frase
        assert resultado["params"]["cor"] == "roxo", frase


def test_mencoes_negacoes_e_hipoteses_de_cor_nao_executam_iot():
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: {},
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )
    contexto = {
        "normalizar_texto": normalizar_texto,
        "detectar_intencao_iot": runtime.detectar,
        "mente_integrada_estado": {},
        "texto_conversa_casual_sem_acao": texto_conversa_casual_sem_acao,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": texto_social_curto,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "texto_expresso_melhor_no_deterministico": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda *_: "pc_a",
    }

    frases = (
        "não deixa a luz roxa",
        "seria legal deixar a luz roxa",
        "acho que eu vou deixar a luz roxa",
        "se eu deixar a luz roxa",
        "você acha legal deixar a luz roxa?",
        "eu gosto de deixar a luz roxa",
        "a lâmpada roxa é bonita",
        "deixa quieto",
    )
    for frase in frases:
        assert detectar_intencao_deterministica_mente(frase, contexto) is None, frase


def test_vocativo_final_nao_vira_cor_e_desligar_tem_precedencia():
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: {},
        emitir_fala=False,
        modo="simulado",
        resolver_cor=lambda _nome: {"rgb": (0, 0, 0)},
        log=lambda *_: None,
    )

    assert runtime.detectar("desliga a luz lay") == {
        "intent": "IOT_CONTROL",
        "params": {"acao": "desligar", "alvo": "lampada_quarto"},
    }
    assert runtime.detectar("Laylay, desliga a lâmpada, por favor") == {
        "intent": "IOT_CONTROL",
        "params": {"acao": "desligar", "alvo": "lampada_quarto"},
    }


def test_runtime_iot_bloqueia_instrucao_negacao_e_sugestao() -> None:
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: {},
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )

    assert runtime.detectar("como eu faria para desligar a luz?") is None
    assert runtime.detectar("não desliga a luz") is None
    assert runtime.detectar("talvez fosse legal apagar a lâmpada") is None
    assert runtime.detectar("desliga a luz")["intent"] == "IOT_CONTROL"


def test_guarda_operacional_distingue_pedido_de_comentario():
    assert autoriza_candidato_iot_direto("deixa a luz roxa", modalidade="direto")
    assert autoriza_candidato_iot_direto("deixa a luz roxa", modalidade="pedido")
    assert not autoriza_candidato_iot_direto("deixa a luz roxa", modalidade="deliberativo")
    assert not autoriza_candidato_iot_direto("não deixa a luz roxa", modalidade="direto")
    assert not autoriza_candidato_iot_direto("eu gosto de deixar a luz roxa", modalidade="direto")
    assert texto_tem_evidencia_iot_parametro("deixa a luz roxa")
    assert texto_tem_evidencia_iot_parametro("pode deixar a lâmpada roxa?")
    assert not texto_tem_evidencia_iot_parametro("deixa quieto")
    assert not texto_tem_evidencia_iot_parametro("seria legal deixar a luz roxa")


def test_turno_real_autoriza_ajuste_iot_sem_autorizar_hipotese():
    comando = classificar_modalidade_turno(
        "deixa a luz roxa",
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    hipotese = classificar_modalidade_turno(
        "seria legal deixar a luz roxa",
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )

    assert comando["modalidade_geral"] == "comando"
    assert comando["autoriza_execucao"] is True
    assert hipotese["autoriza_execucao"] is False


def test_runtime_pesquisa_cor_livre_valida_e_usa_cache():
    consultas = []
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: {},
        emitir_fala=False,
        modo="simulado",
        resolver_cor=lambda nome: consultas.append(nome) or {"rgb": (0, 95, 106)},
        log=lambda *_: None,
    )

    primeira = runtime.detectar("deixa a luz do quarto azul petróleo")
    segunda = runtime.detectar("coloca a lâmpada azul petróleo")

    assert primeira["params"]["cor"] == "azul petroleo"
    assert primeira["params"]["rgb"] == (0, 95, 106)
    assert primeira["params"]["cor_pesquisada"] is True
    assert segunda["params"]["rgb"] == (0, 95, 106)
    assert consultas == ["azul petroleo"]


def test_horario_da_acao_iot_nao_vira_brilho_e_e_agendado():
    estado = {}
    runtime_iot = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: estado,
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )
    namespace = {
        "_normalizar_texto_com_apelidos": normalizar_texto,
        "_extrair_acao_agendada_local": lambda texto: extrair_acao_agendada_local(
            texto, normalizar_texto
        ),
    }
    detector = DeteccaoDeterministicaRuntime(
        namespace_getter=lambda: namespace,
        estado_getter=lambda: estado,
        sites_diretos={},
        apps_map={},
        iot=runtime_iot,
    )

    assert runtime_iot.detectar("desliga a luz às 23:27") is None
    resultado = detector.detectar("desliga a luz às 23:27")

    assert resultado["intent"] == "AGENDAR_ACAO"
    assert resultado["params"]["hora_alvo"] == "23:27"
    assert resultado["params"]["texto_acao"] == "desliga a luz"
    assert resultado["params"]["acao_agendada"] == {
        "intent": "IOT_CONTROL",
        "params": {"acao": "desligar", "alvo": "lampada_quarto"},
    }


def test_apagar_luz_vai_para_iot_e_nao_para_exclusao_de_arquivo():
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: {},
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )
    texto = "está bem lay, pode apagar a luz para mim"

    iot = runtime.detectar(texto)
    alvo_desconhecido_ambiguo = runtime.detectar("apaga o antonio")
    arquivo = detectar_intencao_arquivos(
        texto,
        params_cb=lambda **params: params,
        estado_mental={},
        normalizar_texto=normalizar_texto,
    )
    arquivo_explicito = detectar_intencao_arquivos(
        "apagar o arquivo luz.txt",
        params_cb=lambda **params: params,
        estado_mental={},
        normalizar_texto=normalizar_texto,
    )

    assert iot == {
        "intent": "IOT_CONTROL",
        "params": {"acao": "desligar", "alvo": "lampada_quarto"},
    }
    assert arquivo is None
    assert alvo_desconhecido_ambiguo is None
    assert arquivo_explicito["intent"] == "DELETE_ITEM"


def test_cadeia_completa_separa_arquivo_iot_e_musica() -> None:
    estado = {
        "ultima_acao_intent": "CREATE_FOLDER",
        "ultima_acao_params": {"nome": "antonio"},
    }
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: estado,
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )
    contexto = {
        "normalizar_texto": normalizar_texto,
        "detectar_intencao_iot": runtime.detectar,
        "mente_integrada_estado": estado,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda *_: "pc_a",
        "sites_diretos": {},
        "apps_map": {},
    }

    assert detectar_intencao_deterministica_mente(
        "cria uma pasta chamada antonio", contexto,
    ) == {"intent": "CREATE_FOLDER", "params": {"nome": "antonio"}}
    assert detectar_intencao_deterministica_mente(
        "coloca um arquivo de texto chamado carlos dentro de antonio", contexto,
    ) == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": "carlos",
            "pasta": "antonio",
            "tipo_arquivo": "texto",
        },
    }
    assert detectar_intencao_deterministica_mente(
        "apaga o antonio", contexto,
    ) == {"intent": "DELETE_ITEM", "params": {"alvo": "antonio"}}
    assert detectar_intencao_deterministica_mente(
        "apaga a pasta antonio", contexto,
    ) == {
        "intent": "DELETE_ITEM",
        "params": {"alvo": "antonio", "tipo": "pasta"},
    }
    assert detectar_intencao_deterministica_mente(
        "apaga a luz", contexto,
    ) == {
        "intent": "IOT_CONTROL",
        "params": {"acao": "desligar", "alvo": "lampada_quarto"},
    }


def test_contexto_iot_com_cor_vence_reutilizacao_semantica_de_energia():
    class Estado:
        mental = {"ultima_acao_intent": "IOT_CONTROL"}

    contexto = ContextoImediatoRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_com_apelidos": lambda texto: texto.lower(),
            "_estrutura_arquivo_recente": lambda *_: {},
        },
        estado_runtime_getter=lambda: Estado(),
    )
    contexto.resolver_iot = lambda *_: {
        "intent": "IOT_CONTROL",
        "params": {"acao": "ajustar_cor", "alvo": "lampada_quarto", "cor": "rosa"},
    }
    contexto.resolver_semantico = lambda *_: {
        "intent": "IOT_CONTROL",
        "params": {"acao": "desligar", "alvo": "lampada_quarto"},
    }

    resultado = contexto.resolver("deixa ela rosa")

    assert resultado["params"]["acao"] == "ajustar_cor"
    assert resultado["params"]["cor"] == "rosa"
    assert resultado["_rota_contextual"] == "IOT"


def test_clara_e_escura_sem_cor_ajustam_brilho_e_aceitam_erro_de_digitacao():
    estado = {}
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: estado,
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )

    escura = runtime.detectar("deixa a luz mais escura")
    escura_com_typo = runtime.detectar("deixa a luz maus escura")

    assert escura["params"]["acao"] == "ajustar_brilho"
    assert escura["params"]["valor"] == 50
    assert escura_com_typo["params"]["acao"] == "ajustar_brilho"
    assert escura_com_typo["params"]["valor"] == 50

    for frase in ("deixa a luz mais escura", "deixa a luz maus escura", "deixa a luz mais clara"):
        roteado = detectar_intencao_deterministica_mente(
            frase,
            {
                "normalizar_texto": normalizar_texto,
                "detectar_intencao_iot": runtime.detectar,
                "mente_integrada_estado": estado,
                "limpar_destino_pc_b": lambda texto: texto,
                "target_from_params": lambda *_: "pc_a",
            },
        )
        assert roteado["intent"] == "IOT_CONTROL"
        assert roteado["params"]["acao"] == "ajustar_brilho"

    primeira = runtime.executar(escura, "deixa a luz mais escura")
    mais_escura = runtime.detectar("deixa a luz mais escura")
    mais_clara = runtime.detectar("deixa a luz mais clara")

    assert primeira["status"] == "brilho_ajustado"
    assert mais_escura["params"]["valor"] == 30
    assert mais_clara["params"]["valor"] == 70


def test_aumentar_brilho_dela_preserva_contexto_e_parte_da_cor_atual():
    estado = {}
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: estado,
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )
    verde_escuro = runtime.detectar("deixa a luz verde escuro")
    runtime.executar(verde_escuro, "deixa a luz verde escuro")

    aumenta = runtime.detectar("aumenta o brilho dela")
    roteado = detectar_intencao_deterministica_mente(
        "aumenta o brilho dela",
        {
            "normalizar_texto": normalizar_texto,
            "detectar_intencao_iot": runtime.detectar,
            "mente_integrada_estado": estado,
            "limpar_destino_pc_b": lambda texto: texto,
            "target_from_params": lambda *_: "pc_a",
        },
    )

    assert estado["ultimos_parametros_iot"]["brilho"] == 42
    assert aumenta["intent"] == "IOT_CONTROL"
    assert aumenta["params"]["acao"] == "ajustar_brilho"
    assert aumenta["params"]["alvo"] == "lampada_quarto"
    assert aumenta["params"]["valor"] == 62
    assert roteado["params"]["acao"] == "ajustar_brilho"
    assert roteado["params"]["valor"] == 62

    resultado = runtime.executar(aumenta, "aumenta o brilho dela")
    diminui = runtime.detectar("diminui bastante o brilho dela")
    assert resultado["status"] == "brilho_ajustado"
    assert diminui["params"]["valor"] == 32


def test_valor_final_e_elipse_numerica_preservam_contexto_do_brilho():
    estado = {}
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: estado,
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )

    cor = runtime.detectar("coloca a luz rosa escuro")
    runtime.executar(cor, "coloca a luz rosa escuro")

    absoluto = runtime.detectar("aumenta o brilho para 100")
    assert absoluto["params"]["acao"] == "ajustar_brilho"
    assert absoluto["params"]["valor"] == 100
    assert "ajuste_relativo" not in absoluto["params"]

    noventa = runtime.detectar("coloca o brilho em 90")
    runtime.executar(noventa, "coloca o brilho em 90")
    eliptico = runtime.detectar("coloca em 100")
    assert eliptico == {
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "ajustar_brilho",
            "alvo": "lampada_quarto",
            "valor": 100,
            "referencia_contextual": True,
        },
    }

    roteado = detectar_intencao_deterministica_mente(
        "coloca em 100",
        {
            "normalizar_texto": normalizar_texto,
            "detectar_intencao_iot": runtime.detectar,
            "mente_integrada_estado": estado,
            "limpar_destino_pc_b": lambda texto: texto,
            "target_from_params": lambda *_: "pc_a",
        },
    )
    assert roteado["intent"] == "IOT_CONTROL"
    assert roteado["params"]["valor"] == 100
