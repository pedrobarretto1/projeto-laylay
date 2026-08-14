from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.memoria_mental.continuidade_geral import (
    normalizar_dominio_continuidade,
)


def _passar_pela_porta_prioritaria(
    texto: str,
    *,
    mapa: MapaHabilidadesRuntime,
    contexto: dict | None = None,
) -> tuple[list[str], list[dict]]:
    falas: list[str] = []
    execucoes: list[dict] = []
    turno = classificar_modalidade_turno(texto)
    estado = SimpleNamespace(mental={"turno_atual": turno})
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_responder_pergunta_capacidade_local": lambda entrada: (
                mapa.responder_pergunta_capacidade(
                    entrada,
                    turno=turno,
                    contexto=contexto,
                )
            ),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "executar_intencao": lambda comando, _entrada: (
                execucoes.append(comando) or True
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(texto) is True
    return falas, execucoes


@pytest.mark.parametrize(
    ("texto", "pistas"),
    (
        (
            "Como eu faria para criar um arquivo?",
            (
                "arquivo", "pedido", "não criou", "não acontece",
                "só acontece", "só executo depois",
            ),
        ),
        (
            "Como eu faria para apagar um arquivo?",
            ("arquivo", "lixeira", "confirma", "confirmo"),
        ),
        (
            "Como eu faria para apagar o teste natural.txt?",
            ("teste natural.txt", "lixeira", "confirma", "confirmo"),
        ),
        (
            "Como eu abriria o Spotify?",
            ("spotify", "janela", "não abriu", "sem executar", "apenas expliquei", "ficou como estava"),
        ),
    ),
)
def test_pergunta_procedural_recebe_instrucao_local_sem_executar(
    texto: str,
    pistas: tuple[str, ...],
) -> None:
    mapa = MapaHabilidadesRuntime()
    turno = classificar_modalidade_turno(texto)

    falas, execucoes = _passar_pela_porta_prioritaria(texto, mapa=mapa)

    assert turno["natureza_acao"] == "instrucao_ou_explicacao"
    assert turno["autoriza_execucao"] is False
    assert execucoes == []
    assert len(falas) == 1
    resposta = falas[0].casefold()
    assert pistas[0] in resposta
    assert pistas[1] in resposta
    assert any(pista in resposta for pista in pistas[2:])
    assert "não posso ajudar" not in resposta
    assert "não tenho acesso" not in resposta


def test_instrucao_procedural_respeita_disponibilidade_do_catalogo_vivo() -> None:
    mapa = MapaHabilidadesRuntime(
        operacional_getter=lambda: {
            "capacidades": {
                "CREATE_FILE": {
                    "estado": "indisponivel",
                    "motivo": "precondicao_operacional_ausente",
                },
            },
        },
    )
    texto = "Como eu faria para criar um arquivo?"

    resposta = mapa.responder_pergunta_capacidade(
        texto,
        turno=classificar_modalidade_turno(texto),
    )

    assert "indisponível" in resposta.casefold()
    assert "não executou" in resposta.casefold()


@pytest.mark.parametrize(
    "texto",
    (
        "Você é só um chatbot?",
        "Você está no meu computador?",
        "Você só consegue conversar?",
        "Você consegue abrir apps?",
    ),
)
def test_identidade_e_capacidade_reais_nao_negam_acesso_nem_executam(
    texto: str,
) -> None:
    mapa = MapaHabilidadesRuntime()

    falas, execucoes = _passar_pela_porta_prioritaria(texto, mapa=mapa)

    assert execucoes == []
    assert len(falas) == 1
    resposta = falas[0].casefold()
    assert "abrir" in resposta or "abro" in resposta or "arquivos" in resposta
    for negacao_falsa in (
        "não tenho acesso",
        "não posso abrir apps",
        "não posso abrir aplicativos",
        "só consigo conversar",
        "só converso",
        "não tô no seu computador",
    ):
        assert negacao_falsa not in resposta


def test_respostas_locais_equivalentes_variam_sem_mudar_os_fatos() -> None:
    mapa = MapaHabilidadesRuntime()
    texto = "Como eu abriria o Spotify?"
    turno = classificar_modalidade_turno(texto)

    primeira = mapa.responder_pergunta_capacidade(texto, turno=turno)
    segunda = mapa.responder_pergunta_capacidade(
        texto,
        turno=turno,
        contexto={"ultima_resposta": primeira},
    )

    assert primeira != segunda
    for resposta in (primeira, segunda):
        normalizada = resposta.casefold()
        assert "spotify" in normalizada
        assert "não tenho acesso" not in normalizada
        assert any(
            limite in normalizada
            for limite in (
                "não abriu", "sem executar", "apenas expliquei",
                "ficou como estava",
            )
        )


def test_pergunta_repetida_sobre_abrir_apps_varia_sem_executar() -> None:
    mapa = MapaHabilidadesRuntime()
    texto = "Você consegue abrir apps?"
    turno = classificar_modalidade_turno(texto)

    primeira = mapa.responder_pergunta_capacidade(texto, turno=turno)
    segunda = mapa.responder_pergunta_capacidade(
        texto,
        turno=turno,
        contexto={"ultima_resposta": primeira},
    )

    assert primeira != segunda
    for resposta in (primeira, segunda):
        normalizada = resposta.casefold()
        assert "abr" in normalizada
        assert "não tenho acesso" not in normalizada
        assert any(
            limite in normalizada
            for limite in (
                "não acionei", "não executa", "nenhum aplicativo foi aberto",
            )
        )


@pytest.mark.parametrize(
    ("texto", "pistas"),
    (
        (
            "Você consegue abrir e organizar programas?",
            ("abr", "programas", "organiz", "janelas"),
        ),
        (
            "Você consegue criar e procurar arquivos?",
            ("criar", "arquivos", "pesquisar localmente"),
        ),
    ),
)
def test_pergunta_composta_preserva_as_duas_capacidades_sem_executar(
    texto: str,
    pistas: tuple[str, ...],
) -> None:
    mapa = MapaHabilidadesRuntime()
    turno = classificar_modalidade_turno(texto)

    primeira = mapa.responder_pergunta_capacidade(texto, turno=turno)
    segunda = mapa.responder_pergunta_capacidade(
        texto,
        turno=turno,
        contexto={"ultima_resposta": primeira},
    )
    falas, execucoes = _passar_pela_porta_prioritaria(texto, mapa=mapa)

    assert turno["autoriza_execucao"] is False
    assert execucoes == []
    assert falas
    assert primeira != segunda
    for resposta in (primeira, segunda, falas[0]):
        normalizada = resposta.casefold()
        assert all(pista in normalizada for pista in pistas)


def test_pergunta_composta_respeita_indisponibilidade_granular_do_catalogo() -> None:
    mapa = MapaHabilidadesRuntime(
        operacional_getter=lambda: {
            "capacidades": {
                "ORGANIZAR_DESKTOP": {
                    "estado": "indisponivel",
                    "motivo": "precondicao_operacional_ausente",
                },
            },
        },
    )

    resposta = mapa.responder_pergunta_capacidade(
        "Você consegue abrir e organizar programas?",
    ).casefold()

    assert "consigo abrir programas" in resposta
    assert "organizar janelas está indisponível" in resposta
    assert "não abriu nada" in resposta


def test_continuidade_catalogada_inclui_status_musical_e_consulta_visual() -> None:
    assert normalizar_dominio_continuidade(intent="MUSIC_STATUS") == "musica"
    assert normalizar_dominio_continuidade(intent="VISION_QUERY") == "jogo"


def test_por_que_nao_explica_alvo_inexistente_sem_negar_capacidade_real() -> None:
    agora = time.time()
    mapa = MapaHabilidadesRuntime(relogio=lambda: agora)
    contexto = {
        "ultima_acao_intent": "APP_OPEN",
        "ultima_acao_status": "nao_encontrado",
        "ultima_acao_ok": False,
        "ultima_acao_alvo": "aplicativo que não existe",
        "ultima_acao_params": {"nome_app": "aplicativo que não existe"},
        "ultima_acao_ts": agora - 2.0,
    }

    falas, execucoes = _passar_pela_porta_prioritaria(
        "Por que não?",
        mapa=mapa,
        contexto=contexto,
    )

    assert execucoes == []
    assert len(falas) == 1
    resposta = falas[0].casefold()
    assert "aplicativo que não existe" in resposta
    assert any(
        trecho in resposta
        for trecho in ("não encontr", "não reconheceu", "não apareceu")
    )
    assert any(
        trecho in resposta
        for trecho in (
            "consigo abrir", "conseguindo abrir",
            "capacidade de abrir apps continua",
        )
    )
    assert "não tenho acesso" not in resposta


def test_por_que_nao_nao_reaproveita_falha_operacional_antiga() -> None:
    agora = time.time()
    mapa = MapaHabilidadesRuntime(relogio=lambda: agora)

    resposta = mapa.responder_pergunta_capacidade(
        "Por que não?",
        turno=classificar_modalidade_turno("Por que não?"),
        contexto={
            "ultima_acao_intent": "APP_OPEN",
            "ultima_acao_status": "nao_encontrado",
            "ultima_acao_ok": False,
            "ultima_acao_alvo": "app antigo",
            "ultima_acao_ts": agora - 301.0,
        },
    )

    assert resposta == ""
