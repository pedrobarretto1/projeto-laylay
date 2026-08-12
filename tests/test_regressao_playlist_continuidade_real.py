from __future__ import annotations

import pytest

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)


class _OperacoesMusicaisVivas:
    def __init__(self) -> None:
        self.faixa: dict[str, str] = {}
        self.adicoes: list[tuple[str, str, str, str]] = []
        self.ultima_playlist = ""
        self.aceitar_adicao = True

    def faixa_atual(self) -> dict[str, str]:
        return dict(self.faixa)

    def adicionar_faixa(
        self, nome: str, url: str, titulo: str, canal: str,
    ) -> bool:
        if not self.aceitar_adicao:
            return False
        self.adicoes.append((nome, url, titulo, canal))
        return True

    def definir_ultima_playlist(self, nome: str) -> None:
        self.ultima_playlist = nome


class _ComposicaoPlaylistReal:
    """Recorte da composição real com estado e executor canônicos.

    Somente a porta externa do player é falsa; executor, registro do resultado,
    continuidade e barreira pré-LLM são os mesmos usados pela aplicação.
    """

    def __init__(self) -> None:
        self.estado = EstadoCompartilhadoRuntime(mental=estado_mental_inicial())
        self.operacoes = _OperacoesMusicaisVivas()
        self.falas: list[str] = []
        self.namespace: dict = {}
        self.contexto = EstadoContextoRuntime(
            namespace_getter=lambda: self.namespace,
            estado_runtime_getter=lambda: self.estado,
        )
        self.namespace.update({
            "_estado_compartilhado_runtime": self.estado,
            "_normalizar_texto_com_apelidos": (
                lambda texto: str(texto or "").casefold().strip()
            ),
            "_atualizar_foco_vivo": self.contexto.atualizar_foco_vivo,
            "_resolver_repeticao_ultima_acao": (
                self.contexto.resolver_repeticao_ultima_acao
            ),
            "_registrar_resultado_execucao": (
                self.contexto.registrar_resultado_execucao
            ),
            "executar_intencao": self._executar_executor,
            "resolver_comando_natural": lambda *_args: (_ for _ in ()).throw(
                AssertionError("continuidade canônica não pode chegar à conversa")
            ),
        })
        self.ctx_executor = {
            "_target_from_params": lambda *_args: "pc_a",
            "_registrar_resultado_execucao": (
                self.contexto.registrar_resultado_execucao
            ),
            "_registro_musica_operacoes_runtime": self.operacoes,
            "falar_com_lipsync": (
                lambda fala, *_args: self.falas.append(str(fala))
            ),
            "_yt_clean_title": lambda titulo: titulo,
        }
        self.imediatos = ComandosImediatosRuntime(
            namespace_getter=lambda: self.namespace,
            loop_getter=lambda: None,
        )

    def _executar_executor(self, comando: dict, texto: str) -> bool:
        return executar_intencao(comando, texto, self.ctx_executor)

    def executar_turno(self, comando: dict, texto: str) -> bool:
        """Reproduz executor detalhado seguido do registro externo do turno."""
        executou = self._executar_executor(comando, texto)
        self.contexto.registrar_resultado_execucao(
            comando,
            texto,
            executou,
            origem="prioritario_linguagem_natural:deterministico-explicito",
        )
        return executou


@pytest.mark.parametrize(
    ("faixa", "status_esperado"),
    [
        ({}, "faixa_atual_indisponivel"),
        (
            {
                "url": "https://example.com/noticia",
                "title": "Página comum",
                "canal": "",
            },
            "fonte_musical_invalida",
        ),
    ],
)
def test_playlist_add_sem_musica_publica_falha_explicita_no_estado_canonico(
    faixa: dict[str, str], status_esperado: str,
) -> None:
    composicao = _ComposicaoPlaylistReal()
    composicao.operacoes.faixa = faixa
    comando = {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "vmz"},
    }

    executou = composicao.executar_turno(
        comando, "coloca essa musica na playlist vmz",
    )

    assert executou is False
    assert composicao.operacoes.adicoes == []
    assert composicao.estado.mental["ultima_acao_status"] == status_esperado
    assert composicao.estado.mental["ultima_acao_ok"] is False
    assert composicao.estado.mental["ultima_acao_confirmada"] is False
    contrato = dict(composicao.estado.mental["ultima_acao_contrato"])
    assert contrato["status"] == status_esperado
    assert contrato["executou"] is False
    assert contrato["confirmado"] is False
    continuidade = dict(
        composicao.estado.mental["continuidade_geral"]["dominios"]["musica"]
    )
    assert continuidade["status"] == status_esperado
    assert continuidade["reexecutavel"] is True


def test_tenta_de_novo_refaz_playlist_add_pela_composicao_canonica() -> None:
    composicao = _ComposicaoPlaylistReal()
    comando = {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "vmz"},
    }
    assert composicao.executar_turno(
        comando, "coloca essa musica na playlist vmz",
    ) is False
    composicao.operacoes.faixa = {
        "url": "https://www.youtube.com/watch?v=saturno",
        "title": "Saturno",
        "canal": "VMZ",
    }

    assert composicao.imediatos.processar_prioritarios("tenta de novo") is True

    assert composicao.operacoes.adicoes == [(
        "vmz",
        "https://www.youtube.com/watch?v=saturno",
        "Saturno",
        "VMZ",
    )]
    assert composicao.estado.mental["ultima_acao_status"] == (
        "playlist_musica_adicionada"
    )
    assert composicao.estado.mental["ultima_acao_ok"] is True
    assert composicao.operacoes.ultima_playlist == "vmz"


def test_essa_tambem_usa_nova_faixa_e_preserva_playlist_no_fluxo_real() -> None:
    composicao = _ComposicaoPlaylistReal()
    comando = {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "vmz"},
    }
    composicao.operacoes.faixa = {
        "url": "https://www.youtube.com/watch?v=saturno",
        "title": "Saturno",
        "canal": "VMZ",
    }
    assert composicao.executar_turno(
        comando, "coloca essa musica na playlist vmz",
    ) is True
    composicao.operacoes.faixa = {
        "url": "https://www.youtube.com/watch?v=rick",
        "title": "Tipo Rick e Morty",
        "canal": "VMZ",
    }

    assert composicao.imediatos.processar_prioritarios("essa tambem") is True

    assert composicao.operacoes.adicoes == [
        (
            "vmz",
            "https://www.youtube.com/watch?v=saturno",
            "Saturno",
            "VMZ",
        ),
        (
            "vmz",
            "https://www.youtube.com/watch?v=rick",
            "Tipo Rick e Morty",
            "VMZ",
        ),
    ]
    continuidade = dict(
        composicao.estado.mental["continuidade_geral"]["dominios"]["musica"]
    )
    assert continuidade["intent"] == "PLAYLIST_ADD"
    assert continuidade["params"]["nome_playlist"] == "vmz"
    assert continuidade["status"] == "playlist_musica_adicionada"


def test_essa_tambem_usa_contrato_confirmado_se_projecao_perder_o_destino() -> None:
    composicao = _ComposicaoPlaylistReal()
    comando = {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "vmz"},
    }
    composicao.operacoes.faixa = {
        "url": "https://www.youtube.com/watch?v=venus",
        "title": "Venus",
        "canal": "VMZ",
    }
    assert composicao.executar_turno(
        comando, "coloca essa musica na playlist vmz",
    ) is True

    # Reproduz a divergencia vista no terminal: a execucao deixou um contrato
    # atomico completo, mas a projecao por dominio perdeu os parametros.
    mental = dict(composicao.estado.mental)
    continuidade = dict(mental.get("continuidade_geral") or {})
    dominios = dict(continuidade.get("dominios") or {})
    musica = dict(dominios.get("musica") or {})
    musica["params"] = {}
    dominios["musica"] = musica
    continuidade["dominios"] = dominios
    mental["continuidade_geral"] = continuidade
    mental["ultima_acao_params"] = {}
    composicao.estado.substituir("mental", mental)
    composicao.operacoes.faixa = {
        "url": "https://www.youtube.com/watch?v=saturno",
        "title": "Saturno",
        "canal": "VMZ",
    }

    assert composicao.imediatos.processar_prioritarios("essa tambem") is True

    assert composicao.operacoes.adicoes[-1] == (
        "vmz",
        "https://www.youtube.com/watch?v=saturno",
        "Saturno",
        "VMZ",
    )
    assert composicao.estado.mental["ultima_acao_status"] == (
        "playlist_musica_adicionada"
    )
