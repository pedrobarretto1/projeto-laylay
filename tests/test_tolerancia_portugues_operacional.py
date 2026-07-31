from __future__ import annotations

from mente_laylay.autonomia.roteador_deterministico import (
    corrigir_verbo_operacional_digitado,
    detectar_organizacao_desktop,
)
from mente_laylay.cognicao.linguagem_aprendida import LinguagemAprendidaRuntime
from mente_laylay.cognicao.normalizacao_linguagem import (
    corrigir_erros_portugues_operacionais,
    normalizar_texto,
)


def _runtime() -> LinguagemAprendidaRuntime:
    return LinguagemAprendidaRuntime(
        memoria_sqlite=None,
        normalizar_texto=normalizar_texto,
        texto_social_curto=lambda _texto: False,
        falar=lambda *_args: None,
        log=lambda *_args: None,
    )


def test_corrige_verbos_em_dominios_diferentes_sem_fuzzy_sobre_alvos() -> None:
    runtime = _runtime()

    assert runtime.normalizar_com_apelidos("colcoa uma música") == "coloca uma musica"
    assert runtime.normalizar_com_apelidos(
        "orgniza minha área de trabalho"
    ) == "organiza minha area de trabalho"
    assert runtime.normalizar_com_apelidos("pesqisa esse erro") == "pesquisa esse erro"
    assert runtime.normalizar_com_apelidos("liag o ventilador") == "liga o ventilador"
    assert runtime.normalizar_com_apelidos("adciona essa também") == "adiciona essa tambem"
    assert runtime.normalizar_com_apelidos("colcoa isso") == "coloca isso"


def test_fluxo_real_do_detector_recebe_comando_corrigido() -> None:
    runtime = _runtime()
    texto = runtime.normalizar_com_apelidos("orgniza minha área de trabalho")

    assert detectar_organizacao_desktop(
        texto,
        params_cb=lambda **kwargs: kwargs,
    ) == {
        "intent": "ORGANIZAR_DESKTOP",
        "params": {"modo": "automatico"},
    }


def test_nome_de_arquivo_e_pasta_permanece_opaco() -> None:
    runtime = _runtime()

    assert runtime.normalizar_com_apelidos(
        "abre o arquivo Orgniza.txt"
    ) == "abre o arquivo orgniza txt"
    assert runtime.normalizar_com_apelidos(
        "cria um arquivo chamado muscia"
    ) == "cria um arquivo chamado muscia"
    assert runtime.normalizar_com_apelidos(
        "cria uma pasta playlit"
    ) == "cria uma pasta playlit"


def test_erro_de_termo_e_corrigido_quando_a_gramatica_prova_o_dominio() -> None:
    runtime = _runtime()

    assert runtime.normalizar_com_apelidos(
        "quais sao minha playlit"
    ) == "quais sao minha playlist"
    assert runtime.normalizar_com_apelidos(
        "colcoa uma muscia"
    ) == "coloca uma musica"


def test_negacao_hipotese_e_conversa_nao_ganham_verbo_executavel() -> None:
    assert corrigir_verbo_operacional_digitado("liag uma conversa") == "liag uma conversa"
    assert corrigir_erros_portugues_operacionais("nao deslga a luz")[0] == "nao deslga a luz"
    assert corrigir_erros_portugues_operacionais(
        "como eu faria para deslga a luz"
    )[0] == "como eu faria para deslga a luz"
    assert corrigir_erros_portugues_operacionais(
        "eu gosto de organizacao e musica"
    )[0] == "eu gosto de organizacao e musica"


def test_diagnostico_audita_correcao_sem_autorizar_execucao() -> None:
    runtime = _runtime()
    runtime.normalizar_com_apelidos("colcoa uma música")
    diagnostico = runtime.diagnostico_tolerancia_portugues()

    assert diagnostico["modo"] == "operacional_conservador"
    assert diagnostico["entradas_corrigidas"] == 1
    assert diagnostico["substituicoes"] == 1
    assert diagnostico["ultima"]["texto_normalizado"] == "coloca uma musica"
    assert diagnostico["aproximacao_altera_argumentos"] is False
    assert diagnostico["autoriza_execucao"] is False
