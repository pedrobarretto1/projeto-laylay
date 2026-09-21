"""Alteração negada preserva o ato, independentemente da habilidade."""
import pytest

from mente_laylay.cognicao.modalidade_turno import (
    analisar_protecao_operacional, classificar_modalidade_turno,
    autoriza_execucao_efetiva, extrair_nucleo_pedido_operacional,
)
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime


@pytest.mark.parametrize("alvo", ["o volume", "o arquivo notas.txt", "o brilho da lâmpada"])
@pytest.mark.parametrize("verbo", ["altere", "mude", "ajuste"])
@pytest.mark.parametrize("moldura", ["não {} {}", "preciso que você não {} {}"])
def test_recusa_de_alteracao_chega_inteira_ao_contrato_e_geracao(alvo, verbo, moldura):
    texto = moldura.format(verbo, alvo)
    protecao = analisar_protecao_operacional(texto)
    assert protecao["modalidade"] == "recusa", protecao
    assert protecao["bloqueia_execucao"]
    turno = classificar_modalidade_turno(texto)
    assert turno["modalidade"] == "recusa", turno
    assert not autoriza_execucao_efetiva(turno)
    assert extrair_nucleo_pedido_operacional(texto) is None
    plano = planejar_turno(texto, turno=turno, mente={})
    assert not plano.get("comandos")
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={})
    assert contrato["roteiro_concreto"]["estrategia"] == "negacao_operacional_sem_efeito"
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None, resumo_mente_integrada=lambda _: "", formatar_playlists=lambda: "",
        get_status_humor_prompt=lambda: "", base_system_prompt="BASE",
        estado_getter=lambda: {"turno_atual": turno, "contrato_fala_atual": contrato},
    )
    pacote = runtime.preparar_envio_modelo([{"role": "user", "content": texto}], turno_id=turno["id"])
    assert pacote.contexto_fechado
    assert pacote.mensagens[-1]["content"] == texto


@pytest.mark.parametrize("verbo", ["alterar", "mudar", "ajustar"])
@pytest.mark.parametrize("pontuacao", ["", "?"])
def test_pergunta_de_capacidade_nao_vira_autorizacao(verbo, pontuacao):
    texto = f"você pode {verbo} o volume{pontuacao}"
    turno = classificar_modalidade_turno(texto)
    assert turno["modalidade"] == "pergunta"
    assert not autoriza_execucao_efetiva(turno)


@pytest.mark.parametrize("texto", [
    "eu alterei o volume", "eu vou alterar o volume", "posso alterar o volume?",
    "como posso alterar o volume", "pode alterar o volume causar problemas?",
    "ele pode alterar o volume", "se eu disser pode alterar o volume",
    'a frase "não altere o volume" é um exemplo',
    "não preciso que você altere o volume", "preciso que você explique como alterar o volume",
])
def test_mencoes_e_relato_nao_adquirem_permissao(texto):
    turno = classificar_modalidade_turno(texto)
    assert not autoriza_execucao_efetiva(turno), turno


@pytest.mark.parametrize("verbo", ["alterar", "mudar", "ajustar"])
def test_pedido_positivo_continua_diferente_da_recusa(verbo):
    texto = f"pode {verbo} o volume para 20"
    turno = classificar_modalidade_turno(texto)
    assert turno["modalidade"] == "comando", turno
    assert autoriza_execucao_efetiva(turno)
    assert extrair_nucleo_pedido_operacional(texto) == f"{verbo} o volume para 20"


@pytest.mark.parametrize("texto", [
    "preciso que você não altere o volume", "não ajuste o volume",
    "você pode alterar o volume", "eu alterei o volume",
])
def test_barreira_real_bloqueia_candidato_de_acao_sem_autorizacao(texto):
    from tests.test_p0_autorizacao_modalidade import _runtime_para
    runtime, enviados, _, _ = _runtime_para(
        texto, detector=lambda _: {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}},
    )
    assert runtime.processar_prioritarios(texto) is False
    assert enviados == []
