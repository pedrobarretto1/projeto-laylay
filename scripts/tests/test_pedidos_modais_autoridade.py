"""A moldura do pedido não depende do domínio nem concede efeito por si só."""

import pytest

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import (
    autoriza_execucao_efetiva,
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)


PEDIDOS = (
    "pode abri a steam para mim",
    "preciso que voce pause a musica",
    "pode pausar a musica",
    "pode pausa a musica",
    "pode despausar a musica",
    "Pode pausar a música?",
    "Poderia despausar a música?",
    "Preciso que você pause a música?",
    "preciso que você abra a calculadora",
    "eu preciso que você feche a janela",
    "por favor, pode ler o arquivo notas.txt?",
    "preciso que você apague o arquivo antonio.txt",
    "poderia maximizar a calculadora?",
    "pode pesquisar sobre astronomia?",
)


@pytest.mark.parametrize("pontuacao", ("", "?"))
@pytest.mark.parametrize("texto", PEDIDOS)
def test_moldura_diretiva_reconhece_operacao_sem_executar(texto, pontuacao):
    texto = texto.rstrip("?") + pontuacao
    turno = classificar_modalidade_turno(
        texto, texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    assert turno["modalidade"] == "comando", turno
    assert autoriza_execucao_efetiva(turno), turno
    assert not bloqueia_execucao_operacional_prioritaria(texto, classificacao=turno)


@pytest.mark.parametrize("pontuacao", ("", "?"))
@pytest.mark.parametrize("texto", (
    "preciso que voce nao apague o arquivo antonio.txt",
    "preciso que você não pause a música",
    "pode não abrir a calculadora",
    "poderia não despausar a música?",
))
def test_negacao_na_oracao_pedida_continua_recusa(texto, pontuacao):
    texto = texto.rstrip("?") + pontuacao
    turno = classificar_modalidade_turno(texto)
    # Mesmo em turno composto, a oração negada precisa permanecer uma recusa.
    # A integridade do nome com extensão é coberta separadamente abaixo.
    assert "recusa" in turno["atos"], turno
    assert not autoriza_execucao_efetiva(turno)


@pytest.mark.xfail(strict=True, reason="Raiz separada: segmentador corta antonio.txt? no ponto da extensão")
def test_negacao_preserva_nome_com_extensao_e_interrogacao_em_um_ato():
    turno = classificar_modalidade_turno("preciso que voce nao apague o arquivo antonio.txt?")
    assert len(turno["segmentos"]) == 1, turno
    assert turno["modalidade"] == "recusa"


@pytest.mark.parametrize("texto", (
    "abri a calculadora do windowns",
    "eu abri a calculadora",
    "ontem precisei que você pausasse a música",
    "ele pode pausar a música",
    "se eu disser pode pausar a música",
    "talvez precise que você pause a música",
    "não preciso que você pause a música",
    "você pode pausar a música?",
    "você consegue despausar a música?",
    "pode pausar a música causar problemas?",
    "pode me explicar como pausar a música?",
    "estou apenas escrevendo: pode pausar a música",
    "a frase preciso que você pause a música é um exemplo",
    "preciso que você saiba como pausar a música",
    "preciso que você não diga que abriu a calculadora",
))
def test_mencao_capacidade_relato_ou_recusa_nao_vira_pedido(texto):
    turno = classificar_modalidade_turno(texto)
    assert not autoriza_execucao_efetiva(turno), turno
    # Esta barreira complementar usa gatilhos lexicais: False não concede
    # autoridade. Relatos com "abri" não têm esse gatilho; o contrato acima
    # é a prova canônica de que não foram promovidos a pedidos.
    if texto not in {"abri a calculadora do windowns", "eu abri a calculadora"}:
        assert bloqueia_execucao_operacional_prioritaria(texto, classificacao=turno)


@pytest.mark.parametrize("pontuacao", ("", "?"))
@pytest.mark.parametrize("texto", (
    "como funciona a pausa",
    "como eu poderia pausar a música",
    "você pode pausar a música",
    "você consegue despausar a música",
    "pode pausar a música causar problemas",
    "pode me explicar como pausar a música",
))
def test_pergunta_pelo_sentido_independe_da_interrogacao(texto, pontuacao):
    turno = classificar_modalidade_turno(texto + pontuacao)
    assert not autoriza_execucao_efetiva(turno), turno


@pytest.mark.parametrize("texto,acao", (
    ("pode pausar a musica", "pause"),
    ("pode pausa a musica", "pause"),
    ("preciso que voce pause a musica", "pause"),
    ("pode despausar a musica", "play"),
))
@pytest.mark.parametrize("pontuacao", ("", "?"))
def test_composicao_publica_e_detector_real_entregam_pedido_ao_dispatch(texto, acao, pontuacao):
    from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
    from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
    from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
    from tests.test_r1_hs1_fluxo_real_repeticao_tipificada import _HarnessHS1

    h = _HarnessHS1()
    servicos = h.turnos._snapshot()
    servicos.update(
        _classificar_modalidade_turno_mente=classificar_modalidade_turno,
        _texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    texto += pontuacao
    turno = ComposicaoTurnoRuntime(servicos=servicos).iniciar(texto, origem="roteiro_teste")
    assert autoriza_execucao_efetiva(turno), turno
    assert h.estado.mental["turno_atual"]["id"] == turno["id"]
    assert h.estado.mental["turno_atual"]["autoriza_execucao"] is True
    candidato = detectar_volume_ou_midia(texto, params_cb=lambda **kw: kw)
    assert candidato["intent"] == "MEDIA_CONTROL"
    assert candidato["params"]["acao"] == acao

    # Intercepta somente o efeito externo; classificador, composição, estado,
    # detector e barreira são reais. Isto não prova estado físico do player.
    enviados = []
    runtime = ComandosImediatosRuntime(namespace_getter=lambda: {
        "_estado_compartilhado_runtime": h.estado,
        "detectar_intencao_deterministica": lambda t: detectar_volume_ou_midia(
            t, params_cb=lambda **kw: kw,
        ),
        "executar_intencao": lambda c, _t: enviados.append(c) or True,
        "_registrar_resultado_execucao": lambda *a, **kw: None,
        "_emitir_resposta_curta": lambda *a, **kw: None,
    }, loop_getter=lambda: None)
    assert runtime.processar_prioritarios(texto) is True
    assert len(enviados) == 1
    assert enviados[0]["params"]["acao"] == acao


@pytest.mark.parametrize("texto", (
    "você pode pausar a música",
    "você pode pausar a música?",
    "como eu poderia pausar a música",
    "preciso que você não pause a música",
    "eu pausei a música",
    "estou apenas escrevendo: pode pausar a música",
))
def test_detector_real_nao_concede_autoridade_ao_reconhecer_verbo(texto):
    from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
    from tests.test_p0_autorizacao_modalidade import _runtime_para

    detector = lambda t: detectar_volume_ou_midia(t, params_cb=lambda **kw: kw)
    # Controle adversarial: o detector lexical acha mídia mesmo sem pedido.
    assert detector(texto)["intent"] == "MEDIA_CONTROL"
    runtime, enviados, _registros, _falas = _runtime_para(texto, detector=detector)
    assert runtime.processar_prioritarios(texto) is False
    assert enviados == []


@pytest.mark.parametrize("texto,esperado", (
    ("pode abri a calculadora para mim", "abrir a calculadora para mim"),
    ("preciso que você abra a calculadora", "abra a calculadora"),
    ("preciso que voce leia o arquivo notas.txt", "leia o arquivo notas.txt"),
    ("preciso que você pause a música", "pause a música"),
    ("pode abri um arquivo chamado abri.txt", "abrir um arquivo chamado abri.txt"),
))
def test_nucleo_do_pedido_chega_ao_roteador_sem_reescrever_entidade(texto, esperado):
    from mente_laylay.autonomia.roteador_deterministico import normalizar_pedido_natural

    assert autoriza_execucao_efetiva(classificar_modalidade_turno(texto))
    assert normalizar_pedido_natural(texto) == (esperado, "pedido")


@pytest.mark.parametrize("texto", (
    "pode abri a calculadora para mim",
    "preciso que você abra a calculadora",
    "pode abrir a calculadora?",
))
def test_orquestrador_deterministico_resolve_mesmo_app_apos_moldura(texto):
    from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente
    from mente_laylay.autonomia.porteiro_acoes import texto_conversa_casual_sem_acao
    from mente_laylay.autonomia.roteador_deterministico import extrair_intencao_abrir_app
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto

    contexto = {
        "normalizar_texto": normalizar_texto,
        "texto_conversa_casual_sem_acao": texto_conversa_casual_sem_acao,
        "extrair_intencao_abrir_app": lambda t: extrair_intencao_abrir_app(
            t, normalizar_texto=normalizar_texto, limpar_destino=lambda t: t,
            apps_map={"calculadora": "calc"}, sites_diretos={},
        ),
    }
    candidato = detectar_intencao_deterministica_mente(texto, contexto)
    assert candidato is not None, "pedido se perdeu antes do extrator/executor"
    assert candidato["intent"] == "APP_OPEN", candidato
    assert candidato["params"]["nome_app"] == "calculadora", candidato


@pytest.mark.parametrize("texto", (
    "abri a calculadora do windowns",
    "eu abri a calculadora",
    "preciso que você não abra a calculadora",
    "você pode abrir a calculadora",
    "pode abrir a calculadora causar problemas?",
    "como eu poderia abrir a calculadora",
    "estou apenas escrevendo: pode abri a calculadora",
    "pode abrir a calculadora é apenas um exemplo de frase, não um pedido",
))
def test_extracao_do_nucleo_nao_remove_protecao_da_fala(texto):
    from mente_laylay.cognicao.modalidade_turno import extrair_nucleo_pedido_operacional

    assert extrair_nucleo_pedido_operacional(texto) is None
