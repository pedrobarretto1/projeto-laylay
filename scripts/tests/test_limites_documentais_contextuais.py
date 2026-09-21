"""Limite de rota não é requisito global; verificação não é tarefa do usuário."""
import json

import pytest

from mente_laylay.especialistas.capacidades import consultar_capacidade
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao, montar_mensagens_reparo_comunicacao
from tests.test_explicacao_capacidades_sem_execucao import preparar
from tests.test_reparo_preserva_objetivo_turno import plano_explicacao


@pytest.mark.parametrize("intent", ["VOLUME", "APP_OPEN", "MAXIMIZE_WINDOW"])
def test_catalogo_distingue_limite_remoto_de_controle_local(intent):
    capacidade = consultar_capacidade(intent)
    regras = capacidade.get("limites_contextuais", [])
    assert {r["escopo"] for r in regras} == {"controle_local", "envio_pc_remoto"}
    local, remoto = regras
    assert local["responsavel"] == remoto["responsavel"] == "Laylay"
    assert "não exige conexão com outro PC" in local["regra"]
    assert "outro PC" in remoto["quando"]
    assert "compatíveis" in remoto["regra"]
    # Consumidores antigos continuam recebendo limites, agora com escopo.
    assert remoto["quando"] in capacidade["limites"]


def test_releitura_iot_e_responsabilidade_da_laylay_apos_controle():
    capacidade = consultar_capacidade("IOT_CONTROL")
    regras = capacidade.get("limites_contextuais", [])
    assert len(regras) == 1
    assert regras[0]["escopo"] == "confirmacao_controle"
    assert regras[0]["responsavel"] == "Laylay"
    assert "após um comando autorizado" in regras[0]["quando"]
    assert "reler o dispositivo" in regras[0]["regra"]
    assert capacidade["autorizacao"] == "pedido_atual_autorizado"


@pytest.mark.parametrize("texto,intent", [
    ("como eu poderia aumentar o volume?", "VOLUME"),
    ("como eu poderia abrir a calculadora?", "APP_OPEN"),
    ("como eu poderia ligar a lâmpada?", "IOT_CONTROL"),
])
def test_composicao_transporta_escopo_e_responsavel_ate_autoria_e_reparo(texto, intent):
    estado, runtime, mensagens = preparar(texto)
    contrato = estado["contrato_fala_atual"]
    documento = json.loads(contrato["documentacao_capacidades"])[0]
    regras = consultar_capacidade(intent).get("limites_contextuais")
    assert regras
    assert documento["limites_contextuais"] == list(regras)
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=81)
    assert contrato["documentacao_capacidades"] in pacote.mensagens[0]["content"]
    assert "responsavel" in pacote.mensagens[0]["content"]
    assert not estado["turno_atual"]["autoriza_execucao"]
    avaliacao = avaliar_qualidade_comunicacao(texto, "O arquivo foi salvo.", plano=plano_explicacao(texto))
    assert not avaliacao["aceita"]
    reparo = montar_mensagens_reparo_comunicacao(texto, "O arquivo foi salvo.", avaliacao)
    doc_reparo = json.loads(json.loads(reparo[1]["content"])["contrato_de_reparo"]["documentacao_capacidades"])[0]
    assert doc_reparo["limites_contextuais"] == list(regras)


def test_regras_documentais_nao_tornam_capacidade_indisponivel_em_disponivel():
    mapa = MapaHabilidadesRuntime(operacional_getter=lambda: {
        "dominios": {"sistema": {"estado": "indisponivel", "motivo": "backend_ausente"}},
    })
    estado, _, _ = preparar("como eu poderia aumentar o volume?", mapa)
    documento = json.loads(estado["contrato_fala_atual"]["documentacao_capacidades"])[0]
    assert documento["estado"] == "indisponivel"
    assert documento["exemplos"] == []
    assert documento["motivo"] == "backend_ausente"
    assert not estado["turno_atual"]["autoriza_execucao"]


def test_limite_de_dominio_vizinho_e_preservado_sem_inventar_escopo():
    estado, _, _ = preparar("como eu poderia pausar a música?")
    documento = json.loads(estado["contrato_fala_atual"]["documentacao_capacidades"])[0]
    assert documento["limites"] == consultar_capacidade("MEDIA_CONTROL")["limites"]
    assert not documento.get("limites_contextuais")
