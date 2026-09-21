"""A barreira impede efeito; a autoria compartilhada responde ao ato original."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.autonomia.higiene_resposta_ia import limpar_resposta_da_ia
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from tests.test_explicacao_capacidades_sem_execucao import preparar


@pytest.mark.parametrize("texto", [
    "como eu poderia ligar a lâmpada?", "como eu poderia desligar o ventilador?",
    "como eu faria para desligar a luz?", "me ensina como ligar a tomada",
    "como diminuir o brilho da lâmpada?", "não desliga o ventilador",
    "talvez fosse legal ligar a tomada", "não desliga a luz",
])
def test_iot_protegida_delega_autoria_sem_consumir_turno_ou_chamar_executor(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is False
    antes = deepcopy(turno)
    falas = []
    def proibido(*args, **kwargs):
        pytest.fail("pergunta/recusa/hipótese alcançou rota operacional")
    runtime = ComandosImediatosRuntime(namespace_getter=lambda: {
        "_estado_compartilhado_runtime": SimpleNamespace(mental={"turno_atual": turno}),
        "falar_com_lipsync": lambda fala, *_: falas.append(fala),
        "executar_intencao": proibido,
        "detectar_intencao_deterministica": proibido,
    }, loop_getter=lambda: None)
    assert runtime.processar_prioritarios(texto) is False
    assert falas == []
    assert turno == antes


@pytest.mark.parametrize("texto,fala", [
    ("como eu poderia ligar a lâmpada?", "Para ligar a lâmpada, diga 'liga a lâmpada'."),
    ("como eu poderia desligar o ventilador?", "Para desligar o ventilador, diga 'desliga o ventilador'."),
])
@pytest.mark.parametrize("disponivel", [True, False])
def test_documentacao_e_autoria_preservam_pergunta_e_rejeitam_efeito_proposto(texto, fala, disponivel):
    mapa = MapaHabilidadesRuntime(operacional_getter=lambda: {
        "dominios": {"iot": {"estado": "disponivel" if disponivel else "indisponivel"}}
    })
    estado, prompt, mensagens = preparar(texto, mapa)
    pacote = prompt.preparar_envio_modelo(mensagens, turno_id=81)
    assert pacote.contexto_fechado
    assert pacote.mensagens[-1]["content"] == texto
    doc = json.loads(estado["contrato_fala_atual"]["documentacao_capacidades"])
    assert doc[0]["estado"] == ("disponivel" if disponivel else "indisponivel")
    if not disponivel:
        assert doc[0]["exemplos"] == []
        fala = "O controle de dispositivos está indisponível agora."
    plano = planejar_turno(texto, turno=estado["turno_atual"], mente={})
    plano["contrato_fala"] = estado["contrato_fala_atual"]
    proposta = {"acao": "ligar", "alvo": "lampada_quarto"}
    bruto = json.dumps({"fala": fala, "comandos": [proposta]})
    # Não obter verde porque a proposta foi perdida na leitura do envelope.
    assert limpar_resposta_da_ia(bruto)[1] == [proposta]
    resposta = preparar_resposta_para_execucao(
        texto, bruto,
        enviar_mensagem_cb=lambda *a, **k: pytest.fail("fala válida não precisa de reparo"),
        limpar_texto_fala_cb=lambda t: t, fallback_fala="Contingência", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano}, log=lambda _: None,
    )
    assert resposta["comandos"] == []
    assert resposta["fala"] == fala
    verificado = verificar_fala_turno(fala, plano=plano, origem="ia_final")
    assert verificado["aceita"] and verificado["fala"] == fala
