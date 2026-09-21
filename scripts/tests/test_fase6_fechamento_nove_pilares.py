from __future__ import annotations

import pytest

from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


def _pendencia(
    estado: EstadoCompartilhadoRuntime,
) -> PendenciaAcaoRuntime:
    return PendenciaAcaoRuntime(
        estado_getter=lambda: estado.mental,
        estado_atualizar=lambda atualizar: estado.atualizar(
            "mental", atualizar,
        ),
        agora=lambda: 100.0,
        log=lambda *_args: None,
    )


def test_pendencia_oficial_sobrevive_a_recriacao_do_runtime_de_conversa() -> None:
    estado = EstadoCompartilhadoRuntime(mental={})
    conversa_anterior = _pendencia(estado)
    criada = conversa_anterior.registrar(
        origem="lixeira_laylay",
        acao="confirmar_exclusao",
        pergunta="Confirma que quer enviar o arquivo para a lixeira?",
        referencia="arquivo-teste",
        dominio="arquivos",
    )

    conversa_reaberta = _pendencia(estado)
    resposta = conversa_reaberta.resolver("sim")

    assert criada is not None
    assert resposta["tratado"] is True
    assert resposta["status"] == "aceitar"
    assert resposta["pendencia"]["id"] == criada["id"]
    assert resposta["pendencia"]["acao"] == "confirmar_exclusao"


@pytest.mark.parametrize(
    ("pergunta", "trecho_esperado"),
    (
        ("você consegue tocar músicas e playlists?", "músicas"),
        ("você consegue abrir e organizar programas?", "janelas"),
        ("você consegue consultar e controlar o navegador?", "aba ativa"),
        ("você consegue analisar o que aparece no jogo?", "item visível"),
        ("você consegue criar lembretes?", "persistência local"),
        ("você consegue criar e procurar arquivos?", "pesquisar localmente"),
        ("você consegue ler meus emails?", "emails"),
        ("você consegue controlar a lâmpada?", "dispositivos inteligentes"),
        ("você consegue conversar e explicar coisas?", "modelo de linguagem"),
        ("você consegue guardar minhas ideias?", "caixa de entrada"),
        ("você consegue investigar um erro copiado?", "sem abrir uma aba"),
    ),
)
def test_perguntas_naturais_explicam_capacidade_sem_executar(
    pergunta: str,
    trecho_esperado: str,
) -> None:
    mapa = MapaHabilidadesRuntime()

    resposta = mapa.responder_pergunta_capacidade(pergunta)

    assert trecho_esperado.casefold() in resposta.casefold()
    assert mapa.parece_consulta_operacional(pergunta) is False
    assert mapa.diagnostico()["autoriza_execucao"] is False
