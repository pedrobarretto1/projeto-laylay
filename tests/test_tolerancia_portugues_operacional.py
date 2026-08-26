from __future__ import annotations

from mente_laylay.autonomia.roteador_deterministico import (
    corrigir_verbo_operacional_digitado,
    detectar_fechar_alvo,
    detectar_playlist_contextual_musica_atual,
    detectar_organizacao_desktop,
    detectar_web_e_youtube,
    extrair_intencao_abrir_app,
)
from mente_laylay.cognicao.linguagem_aprendida import LinguagemAprendidaRuntime
from mente_laylay.cognicao.normalizacao_linguagem import (
    corrigir_erros_portugues_operacionais,
    normalizar_texto,
    normalizar_texto_basico,
)


def _runtime() -> LinguagemAprendidaRuntime:
    return LinguagemAprendidaRuntime(
        memoria_sqlite=None,
        normalizar_texto=normalizar_texto,
        texto_social_curto=lambda _texto: False,
        falar=lambda *_args: None,
        log=lambda *_args: None,
    )


def test_normalizacao_basica_compartilhada_preserva_pontuacao_contextual() -> None:
    assert normalizar_texto_basico("  VOCÊ  está BEM?  ") == "voce esta bem?"
    assert normalizar_texto_basico("Straße") == "strasse"


def test_corrige_verbos_em_dominios_diferentes_sem_fuzzy_sobre_alvos() -> None:
    runtime = _runtime()

    assert runtime.normalizar_com_apelidos("colcoa uma música") == "coloca uma musica"
    assert runtime.normalizar_com_apelidos(
        "orgniza minha área de trabalho"
    ) == "organiza minha area de trabalho"
    assert runtime.normalizar_com_apelidos("pesqisa esse erro") == "pesquisa esse erro"
    assert runtime.normalizar_com_apelidos(
        "pequisa sobre o presidente da china"
    ) == "pesquisa sobre o presidente da china"
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


def test_turno_35_corrige_calcuradora_so_como_app_canonico_explicito() -> None:
    runtime = _runtime()
    texto = runtime.normalizar_com_apelidos("abre a calcuradora")

    assert texto == "abre a calculadora"
    assert extrair_intencao_abrir_app(
        texto,
        normalizar_texto=lambda valor: str(valor).casefold(),
        limpar_destino=lambda valor: str(valor).strip(),
        apps_map={"calculadora": "calc"},
        sites_diretos={},
    ) == {
        "intent": "APP_OPEN",
        "params": {"nome_app": "calculadora"},
    }
    assert runtime.normalizar_com_apelidos(
        "abre o app chamado calcuradora"
    ) == "abre o app chamado calcuradora"


def test_red_turno_36_corrige_fexa_sem_entregar_o_comando_a_ia() -> None:
    corrigido = corrigir_verbo_operacional_digitado(
        "fexa a microsoft store"
    )

    assert corrigido == "fecha a microsoft store"
    assert detectar_fechar_alvo(
        corrigido,
        params_cb=lambda **kwargs: kwargs,
        sites_diretos=set(),
        apps_map={"microsoft store": "ms-windows-store:"},
    ) == {
        "intent": "CLOSE_APP",
        "params": {"nome_app": "microsoft store"},
    }


def test_pequisa_corrigida_chega_ao_detector_de_busca_sem_alterar_o_tema() -> None:
    runtime = _runtime()
    texto = runtime.normalizar_com_apelidos(
        "pequisa sobre o presidente da China"
    )

    assert detectar_web_e_youtube(
        texto,
        params_cb=lambda **kwargs: kwargs,
        sites_diretos=set(),
    ) == {
        "intent": "SEARCH",
        "params": {
            "query": "o presidente da china",
            "engine": "google",
        },
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
    assert runtime.normalizar_com_apelidos(
        "cria um arquivo chamado pequisa"
    ) == "cria um arquivo chamado pequisa"
    assert runtime.normalizar_com_apelidos(
        "abre o arquivo pequisa.txt"
    ) == "abre o arquivo pequisa txt"
    assert runtime.normalizar_com_apelidos(
        "Pequisa é minha amiga"
    ) == "pequisa e minha amiga"


def test_erro_de_termo_e_corrigido_quando_a_gramatica_prova_o_dominio() -> None:
    runtime = _runtime()

    assert runtime.normalizar_com_apelidos(
        "quais sao minha playlit"
    ) == "quais sao minha playlist"
    assert runtime.normalizar_com_apelidos(
        "colcoa uma muscia"
    ) == "coloca uma musica"


def test_corrige_alias_conhecido_e_termo_de_janela_sem_aproximar_nomes_livres() -> None:
    runtime = _runtime()

    assert runtime.normalizar_com_apelidos(
        "abre o operra e maximiza a janlea"
    ) == "abre o opera e maximiza a janela"
    assert runtime.normalizar_com_apelidos(
        "cria um arquivo chamado operra"
    ) == "cria um arquivo chamado operra"


def test_erro_inequivoco_em_termo_operacional_usa_aproximacao_compartilhada() -> None:
    runtime = _runtime()

    corrigido = runtime.normalizar_com_apelidos(
        "eu gosto de programacao, encontra o codgio que controla a lampada"
    )

    assert corrigido == (
        "eu gosto de programacao encontra o codigo que controla a lampada"
    )
    diagnostico = runtime.diagnostico_tolerancia_portugues()
    assert diagnostico["ultima"]["correcoes"] == [{
        "de": "codgio",
        "para": "codigo",
        "tipo": "termo_operacional_aproximado",
    }]


def test_aproximacao_de_termo_nao_altera_conversa_nem_nome_de_entidade() -> None:
    runtime = _runtime()

    assert runtime.normalizar_com_apelidos("eu gosto de codgio") == "eu gosto de codgio"
    assert runtime.normalizar_com_apelidos(
        "cria um arquivo chamado Codgio"
    ) == "cria um arquivo chamado codgio"


def test_vom_e_recuperado_so_como_avaliacao_contextual_final() -> None:
    runtime = _runtime()

    assert runtime.normalizar_com_apelidos(
        "o comunismo è vom?"
    ) == "o comunismo e bom"
    assert runtime.normalizar_com_apelidos("vom é minha amiga") == "vom e minha amiga"
    assert runtime.normalizar_com_apelidos(
        "cria um arquivo chamado vom"
    ) == "cria um arquivo chamado vom"
    assert runtime.normalizar_com_apelidos(
        "abre o arquivo vom.txt"
    ) == "abre o arquivo vom txt"


def test_preposicao_oral_de_playlist_preserva_faixa_atual_e_destino() -> None:
    runtime = _runtime()

    texto = runtime.normalizar_com_apelidos(
        "coloca essa musica a playlist rei do pop"
    )

    assert texto == "coloca essa musica na playlist rei do pop"
    assert detectar_playlist_contextual_musica_atual(
        texto,
        params_cb=lambda **kwargs: kwargs,
        limpar_nome_playlist=lambda valor: str(valor).strip(),
    ) == {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "rei do pop"},
    }


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
