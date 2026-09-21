from __future__ import annotations

from mente_laylay.autonomia.analise_comandos import (
    LIMITE_ETAPAS_CADEIA,
    processar_comandos_em_cadeia,
    segmentar_comandos_em_cadeia,
)
from mente_laylay.iot.runtime import RuntimeIoT


class MemoriaIoTFalsa:
    def __init__(self) -> None:
        self.dispositivos = {}
        self.historico = []

    def salvar_dispositivo_iot(self, dados):
        self.dispositivos[dados["nome"]] = dict(dados)
        return dict(dados)

    def listar_dispositivos_iot(self, ambiente="", *, somente_ativos=True):
        return [
            dict(item)
            for item in self.dispositivos.values()
            if (not ambiente or item["ambiente"] == ambiente)
            and (not somente_ativos or item.get("ativo", True))
        ]

    def atualizar_estado_iot(self, nome, estado, **kwargs):
        self.dispositivos[nome]["estado"] = dict(estado)
        return dict(estado)

    def registrar_historico_iot(self, nome, **dados):
        self.historico.append({"nome": nome, **dados})
        return self.historico[-1]


def test_turno_152_segmenta_em_tres_etapas_reais() -> None:
    texto = (
        "Liga a lâmpada do quarto, deixa azul e depois "
        "me diz como ela ficou."
    )

    assert segmentar_comandos_em_cadeia(texto) == [
        "Liga a lâmpada do quarto",
        "deixa azul",
        "me diz como ela ficou",
    ]


def test_variantes_reais_do_bloco_h_continuam_segmentadas() -> None:
    casos = (
        (
            "Mostra a playlist caos sonora e depois apaga ela.",
            ["Mostra a playlist caos sonora", "apaga ela"],
        ),
        (
            "Desliga a lâmpada e confirma o estado.",
            ["Desliga a lâmpada", "confirma o estado"],
        ),
        (
            "Volta para a aba anterior e depois me diz qual aba está aberta.",
            ["Volta para a aba anterior", "me diz qual aba está aberta"],
        ),
        (
            "Continua a música, passa para a próxima faixa e me diz qual está tocando.",
            [
                "Continua a música",
                "passa para a próxima faixa",
                "me diz qual está tocando",
            ],
        ),
        (
            "Abre a Wikipédia, pesquisa documentação oficial do Python "
            "e abre o primeiro resultado.",
            [
                "Abre a Wikipédia",
                "pesquisa documentação oficial do Python",
                "abre o primeiro resultado",
            ],
        ),
    )

    for texto, esperado in casos:
        assert segmentar_comandos_em_cadeia(texto) == esperado, texto


def test_conjuncoes_e_enumeracoes_nao_viram_execucao_multipla() -> None:
    frases = (
        "Liga a luz e o ventilador.",
        "Você prefere rock e metal?",
        "Talvez eu apague X depois.",
        "deixa para depois",
        "coloca vermelho, azul e verde",
        "me fala de rock e metal",
    )

    for texto in frases:
        assert len(segmentar_comandos_em_cadeia(texto)) == 1, texto


def test_cadeia_acima_do_limite_nao_e_executada_parcialmente() -> None:
    texto = ", ".join(
        f"abre o aplicativo {indice}"
        for indice in range(1, LIMITE_ETAPAS_CADEIA + 2)
    )

    assert len(segmentar_comandos_em_cadeia(texto)) == 1


def test_processador_executa_as_tres_etapas_na_ordem() -> None:
    texto = (
        "Liga a lâmpada do quarto, deixa azul e depois "
        "me diz como ela ficou."
    )
    chamadas = []

    def executar(trecho: str, origem: str) -> bool:
        chamadas.append((trecho, origem))
        return True

    assert processar_comandos_em_cadeia(
        texto,
        "regressao-152",
        executar_trecho=executar,
    ) is True
    assert chamadas == [
        ("Liga a lâmpada do quarto", "regressao-152-1"),
        ("deixa azul", "regressao-152-2"),
        ("me diz como ela ficou", "regressao-152-3"),
    ]


def test_processador_para_na_primeira_falha_sem_executar_dependentes() -> None:
    texto = "abre a Calculadora, maximiza ela e depois fecha ela"
    chamadas = []

    def executar(trecho: str, origem: str) -> bool:
        chamadas.append((trecho, origem))
        return len(chamadas) < 2

    assert processar_comandos_em_cadeia(
        texto,
        "falha-parcial",
        executar_trecho=executar,
    ) is True
    assert [item[0] for item in chamadas] == [
        "abre a Calculadora",
        "maximiza ela",
    ]


def test_turno_152_percorre_iot_simulado_ligar_cor_status() -> None:
    estado = {}
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: estado,
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )
    texto = (
        "Liga a lâmpada do quarto, deixa azul e depois "
        "me diz como ela ficou."
    )
    observadas = []

    for trecho in segmentar_comandos_em_cadeia(texto):
        candidato = runtime.detectar(trecho, estado)
        assert candidato is not None, trecho
        observadas.append((
            candidato["intent"],
            candidato["params"]["acao"],
            candidato["params"]["alvo"],
        ))
        retorno = runtime.executar(candidato, trecho)
        assert retorno["handled"] is True
        assert retorno["ok"] is True
        assert retorno["confirmado"] is True

    assert observadas == [
        ("IOT_CONTROL", "ligar", "lampada_quarto"),
        ("IOT_CONTROL", "ajustar_cor", "lampada_quarto"),
        ("IOT_STATUS", "status", "lampada_quarto"),
    ]
    assert estado["ultimo_dispositivo_iot"] == "lampada_quarto"
    assert estado["ultima_habilidade"] == "iot"
