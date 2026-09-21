from types import SimpleNamespace
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime


def executar_caminho(texto, candidato, *, via_iot=False):
    turno = classificar_modalidade_turno(texto)
    chamadas = []
    estado = SimpleNamespace(mental={"turno_atual": turno})
    ns = {
        "_estado_compartilhado_runtime": estado,
        "resolver_comando_natural": lambda *a: (candidato, "sonda_inerte"),
        "executar_intencao": lambda *a: chamadas.append(a) or True,
    }
    runtime = ComandosImediatosRuntime(namespace_getter=lambda: ns, loop_getter=lambda: None,
        iot=SimpleNamespace(detectar=lambda *a: candidato) if via_iot else None)
    tratado = runtime.processar_prioritarios(texto)
    return turno, chamadas, tratado


@pytest.mark.parametrize("texto", [
    "Não leia meus e-mails.", "Não leia o relatório.", "Não consulte meus e-mails.",
    "Não verifique a lâmpada.",
])
def test_negacao_de_leitura_publica_veto_canonico(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno["veto_execucao_operacional"] is True
    assert turno["autoriza_execucao"] is False


@pytest.mark.parametrize("texto, candidato, via_iot", [
    ("Não leia meus e-mails.", {"intent": "EMAIL_READ", "params": {}}, False),
    ("Esse relato informa se a lâmpada está ligada neste momento?", {"intent": "IOT_STATUS", "params": {"alvo": "lampada_quarto"}}, True),
    ("Esse pedido prova que o arquivo foi lido?", {"intent": "FILE_READ", "params": {"arquivo": "notas.txt"}}, False),
    ("Esse relato confirma que meus e-mails foram lidos?", {"intent": "EMAIL_READ", "params": {}}, False),
])
def test_consulta_nao_autorizada_nao_chega_ao_executor(texto, candidato, via_iot):
    turno, chamadas, tratado = executar_caminho(texto, candidato, via_iot=via_iot)
    assert not turno["autoriza_execucao"]
    assert chamadas == []
    assert tratado is False  # segue para conclusão conversacional, sem receipt falso


@pytest.mark.parametrize("texto, candidato, via_iot", [
    ("Leia meus e-mails.", {"intent": "EMAIL_READ", "params": {}}, False),
    ("A lâmpada está ligada?", {"intent": "IOT_STATUS", "params": {"alvo": "lampada_quarto"}}, True),
])
def test_consulta_legitima_chega_ao_executor_inerte(texto, candidato, via_iot):
    _, chamadas, tratado = executar_caminho(texto, candidato, via_iot=via_iot)
    assert tratado and len(chamadas) == 1


@pytest.mark.parametrize("texto,intent", [
    ("Não leia meus e-mails.", "EMAIL_READ"),
    ("Esse relato informa se a lâmpada está ligada neste momento?", "IOT_STATUS"),
])
def test_composicao_publica_veto_consumido_antes_do_executor(texto, intent):
    from tests.test_r1_hs1_fluxo_real_repeticao_tipificada import _HarnessHS1
    h = _HarnessHS1()
    turno = h.turnos.iniciar(texto, origem="roteiro_teste")
    assert turno["veto_execucao_operacional"]
    assert h.estado.mental["turno_atual"]["veto_execucao_operacional"]
    efeitos = []
    candidato = {"intent": intent, "params": {}}
    ns = {"_estado_compartilhado_runtime": h.estado,
          "resolver_comando_natural": lambda *a: (candidato, "inerte"),
          "executar_intencao": lambda *a: efeitos.append(a) or True}
    runtime = ComandosImediatosRuntime(namespace_getter=lambda: ns, loop_getter=lambda: None,
        iot=SimpleNamespace(detectar=lambda *a: candidato))
    assert runtime.processar_prioritarios(texto) is False
    assert efeitos == []


@pytest.mark.parametrize("texto", [
    'Leia o arquivo "nao.txt".', "Leia o relatório.", "Consulte meus e-mails.",
    "Esse relato é interessante.",
])
def test_controles_sem_veto_nao_sao_transformados_em_recusa(texto):
    assert not classificar_modalidade_turno(texto)["veto_execucao_operacional"]
