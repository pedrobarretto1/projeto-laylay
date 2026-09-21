"""Informação solicitada não é estado observado nem prova de outro efeito."""

import json

import pytest

from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.guardiao_alegacoes import detectar_resultados_operacionais_sem_evidencia, validar_alegacoes_da_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao


ENTRADA = "como eu poderia pausar a música?"
FALA_CAPTURADA = (
    "Pausa a música com o botão de pausa no player — só clica no ícone de pausa, "
    "não preciso fazer nada por você. Se não estiver vendo, me diga o nome da música "
    "ou o app que tá rodando, para eu te ajudar a localizar."
)


def _plano():
    turno = classificar_modalidade_turno(ENTRADA)
    assert turno["autoriza_execucao"] is False
    plano = planejar_turno(ENTRADA, turno=turno, mente={})
    plano["contrato_fala"] = construir_contrato_semantico_fala(ENTRADA, turno=turno, plano=plano, mente={})
    return plano


PEDIDOS = (
    FALA_CAPTURADA,
    "Me diga o app que está rodando.",
    "Me diga o nome da música ou o app que tá rodando.",
    "Me diga o nome da música e o aplicativo que está aberto.",
    "Por favor me informe a janela que está aberta.",
    "Pode me informar o documento que está aberto.",
    "Você poderia me dizer o processo que continua rodando.",
    "Se puder me mostrar o navegador que está aberto, consigo te orientar.",
    "Me diga qual arquivo ou pasta está aberto.",
    "Me diga se a janela está aberta.",
)


@pytest.mark.parametrize("fala", PEDIDOS)
def test_pedido_informacao_preserva_fala_nos_dois_validadores(fala):
    assert detectar_resultados_operacionais_sem_evidencia(fala, plano=_plano()) == []
    # A outra porta usa o mesmo reconhecedor, inclusive em consulta de estado.
    resultado = validar_alegacoes_da_fala(fala, plano={"texto_usuario": "A janela está aberta?", "comandos": []})
    assert resultado["problemas"] == []
    assert resultado["fala"] == fala
    qualidade = avaliar_qualidade_comunicacao(ENTRADA, fala, plano=_plano())
    assert qualidade["aceita"], qualidade["problemas"]


@pytest.mark.parametrize("separador", [", mas ", "; ", ". ", " e ", " ou ", " porque ", " pois ", " então ", " logo ", " — "])
@pytest.mark.parametrize("pedido", ["Me diga qual aplicativo está rodando", "Me diga o aplicativo que está rodando"])
def test_pedido_nao_empresta_escopo_a_afirmacao_posterior(pedido, separador):
    fala = pedido + separador + "o navegador está aberto."
    assert detectar_resultados_operacionais_sem_evidencia(fala, plano=_plano())
    resultado = validar_alegacoes_da_fala(fala, plano={"texto_usuario": "A janela está aberta?", "comandos": []})
    assert "estado_atual_sem_evidencia" in resultado["problemas"]


@pytest.mark.parametrize("fala", [
    "O app está rodando; me diga o nome.",
    "Posso informar que o app está rodando.",
    "Me diga que o app está rodando.",
    "Você pode me dizer o nome, o app está rodando.",
    "Me diga o app que está rodando. O arquivo foi salvo.",
    "Me diga qual app está rodando e o arquivo foi salvo.",
    "Me diga o arquivo que foi salvo, mas o e-mail foi enviado.",
    "Me diga qual app está rodando porque não consegui abrir o navegador.",
])
def test_alegacao_independente_e_efeito_inventado_continuam_bloqueados(fala):
    assert detectar_resultados_operacionais_sem_evidencia(fala, plano=_plano())
    assert not avaliar_qualidade_comunicacao(ENTRADA, fala, plano=_plano())["aceita"]


@pytest.mark.parametrize("fala", [
    "Me diga se o app está aberto e a lâmpada está ligada.",
    "Me diga se a lâmpada está ligada e o app está aberto.",
    "Me diga se o arquivo foi salvo e a lâmpada está ligada.",
    "Me diga se a lâmpada está ligada e o arquivo foi salvo.",
])
def test_pedido_nao_vaza_entre_diferentes_tipos_de_alegacao(fala):
    # Estados fortes passam também pelo guardião final. Ele pode aceitar sua
    # própria fala ajustada, mas não pode entregar a afirmação original.
    resultado = verificar_fala_turno(fala, plano=_plano(), origem="ia_final")
    assert resultado["problemas"]
    assert not resultado["aceita"] or resultado["fala"] != fala


@pytest.mark.parametrize("comandos", [[], [{"acao": "pause", "alvo": "música"}]])
def test_resposta_historica_atravessa_preparacao_e_verificacao_sem_reparo(comandos):
    def nao_reparar(*args, **kwargs):
        pytest.fail("pedido de informação válido não deve pedir reparo à LLM")

    plano = _plano()
    resultado = preparar_resposta_para_execucao(
        ENTRADA, json.dumps({"fala": FALA_CAPTURADA, "comandos": comandos}, ensure_ascii=False),
        enviar_mensagem_cb=nao_reparar, limpar_texto_fala_cb=lambda t: t,
        fallback_fala="Contingência", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano}, log=lambda _: None,
    )
    assert resultado["comandos"] == []  # explicar nunca autoriza pausar
    assert resultado["fala"] == FALA_CAPTURADA
    final = verificar_fala_turno(FALA_CAPTURADA, plano=plano, origem="ia_final")
    assert final["aceita"], final
    assert final["fala"] == FALA_CAPTURADA
