from __future__ import annotations

import os
import time
from pathlib import Path

from mente_laylay.arquivos.execucao_arquivos import executar_intencao_arquivos
from mente_laylay.arquivos.pesquisa_semantica import PesquisaSemanticaArquivosRuntime
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.integracao.registro_arquivos import registrar_arquivos_leitura
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.roteador_deterministico import (
    extrair_intencao_abrir_app,
    texto_expresso_melhor_no_deterministico,
)
from mente_laylay.autonomia.porteiro_acoes import (
    texto_conversa_casual_sem_acao,
    texto_tem_comando_explicito,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao


def _params(**kwargs):
    return kwargs


def test_pesquisa_encontra_por_nome_conteudo_e_significado(tmp_path: Path) -> None:
    projeto = tmp_path / "laylay"
    projeto.mkdir()
    (projeto / "avatar_laylay.py").write_text("animacao emocao sprite gamebar", encoding="utf-8")
    iot = projeto / "runtime.py"
    iot.write_text("controle tuya de brilho cor e dispositivos iot", encoding="utf-8")
    (projeto / "test_iot_lampada.py").write_text("teste do controle tuya da lâmpada", encoding="utf-8")
    (projeto / "aleatorio.py").write_text("calculo sem relação", encoding="utf-8")
    runtime = PesquisaSemanticaArquivosRuntime(
        raizes=[], projeto_raiz=projeto, log=lambda *_args: None,
    )

    avatar = runtime.pesquisar("documento sobre avatar")
    lampada = runtime.pesquisar("código que controla a lâmpada")

    assert avatar["resultados"][0]["nome"] == "avatar_laylay.py"
    assert lampada["resultados"][0]["caminho"] == str(iot.resolve())
    assert all(item["nome"] != "aleatorio.py" for item in lampada["resultados"])
    assert "significado relacionado" in lampada["resultados"][0]["motivos"]


def test_pesquisa_por_imagem_modificada_ontem(tmp_path: Path) -> None:
    antiga = tmp_path / "antiga.png"
    ontem = tmp_path / "avatar_nebulosa.png"
    antiga.write_bytes(b"png")
    ontem.write_bytes(b"png")
    agora = time.time()
    os.utime(antiga, (agora - 10 * 86400, agora - 10 * 86400))
    os.utime(ontem, (agora - 86400, agora - 86400))
    runtime = PesquisaSemanticaArquivosRuntime(
        raizes=[tmp_path], cache_ttl_s=60, log=lambda *_args: None,
    )

    resultado = runtime.pesquisar("ache a imagem que usei ontem")

    assert resultado["resultados"][0]["nome"] == "avatar_nebulosa.png"
    assert "modificado ontem" in resultado["resultados"][0]["motivos"]


def test_arquivo_sensivel_pode_ser_localizado_sem_indexar_conteudo(tmp_path: Path) -> None:
    segredo = tmp_path / "credentials.json"
    segredo.write_text('{"password":"NAO_DEVE_APARECER"}', encoding="utf-8")
    runtime = PesquisaSemanticaArquivosRuntime(
        raizes=[tmp_path], log=lambda *_args: None,
    )

    resultado_nome = runtime.pesquisar("credentials")
    resultado_segredo = runtime.pesquisar("NAO_DEVE_APARECER")

    assert resultado_nome["resultados"][0]["sensivel"] is True
    assert resultado_nome["resultados"][0]["trecho"] == ""
    assert resultado_segredo["resultados"] == []


def test_indice_e_local_efemero_e_reutiliza_cache(tmp_path: Path) -> None:
    (tmp_path / "modo_jogo.md").write_text("visão durante partidas", encoding="utf-8")
    runtime = PesquisaSemanticaArquivosRuntime(
        raizes=[tmp_path], cache_ttl_s=60, log=lambda *_args: None,
    )

    runtime.pesquisar("modo jogo")
    runtime.pesquisar("visão partidas")
    diagnostico = runtime.diagnostico()

    assert diagnostico["indexacoes"] == 1
    assert diagnostico["cache_hits"] == 1
    assert diagnostico["somente_leitura"] is True
    assert diagnostico["envia_conteudo_externo"] is False


def test_roteador_entende_busca_natural_e_bloqueia_hipotese() -> None:
    exemplos = {
        "encontra o documento sobre o avatar": "avatar",
        "onde está o código que controla a lâmpada?": "código que controla a lâmpada",
        "quais arquivos falam do modo jogo?": "modo jogo",
        "ache a imagem que usei ontem": "imagem que usei ontem",
    }
    for texto, trecho in exemplos.items():
        resultado = detectar_intencao_arquivos(texto, params_cb=_params)
        assert resultado and resultado["intent"] == "FILE_SEARCH"
        assert trecho.casefold() in resultado["params"]["query"].casefold()

    assert detectar_intencao_arquivos(
        "você consegue encontrar um arquivo para mim?", params_cb=_params,
    ) is None
    assert detectar_intencao_arquivos(
        "não procure esse arquivo", params_cb=_params,
    ) is None


def test_acha_com_moldura_de_opiniao_nao_vira_pesquisa_de_arquivo() -> None:
    for frase in (
        "o que você acha de rock?",
        "o que acha do gênero rock?",
        "acha do gênero rock?",
        "acha que rock é bom?",
        "qual sua opinião sobre rock?",
    ):
        assert detectar_intencao_arquivos(frase, params_cb=_params) is None

    comando = detectar_intencao_arquivos(
        "acha o arquivo do gênero rock", params_cb=_params,
    )
    assert comando is not None
    assert comando["intent"] == "FILE_SEARCH"
    assert "gênero rock" in comando["params"]["query"]


def test_selecao_natural_abre_resultado_recente_em_vez_de_app() -> None:
    estado = {
        "ultima_estrutura_arquivo_params": {
            "tipo": "pesquisa_semantica",
            "consulta": "código que controla a lâmpada",
            "resultados": [r"C:\projeto\controlador.py", r"C:\projeto\tuya.py"],
            "nomes": ["controlador.py", "tuya.py"],
        },
    }
    for frase, esperado in (
        ("pode abrir o primeiro", "controlador.py"),
        ("abra o segundo resultado", "tuya.py"),
        ("mostra a opção 2", "tuya.py"),
    ):
        resultado = detectar_intencao_arquivos(
            frase, params_cb=_params, estado_mental=estado,
        )
        assert resultado and resultado["intent"] == "FILE_OPEN_RESULT"
        assert resultado["params"]["alvo"] == esperado

    assert detectar_intencao_arquivos(
        "você consegue abrir o primeiro?", params_cb=_params, estado_mental=estado,
    ) is None

    # Sem uma lista válida, o ordinal também não pode virar o nome literal de
    # um programa. Outro resolvedor contextual poderá tratá-lo ou esclarecer.
    assert extrair_intencao_abrir_app(
        "pode abrir o primeiro",
        normalizar_texto=lambda texto: str(texto or "").casefold().strip(),
        limpar_destino=lambda texto: texto,
        apps_map={},
        sites_diretos={},
    ) is None

    normalizar = lambda texto: str(texto or "").casefold().strip()
    ctx = {
        "normalizar_texto": normalizar,
        "texto_conversa_casual_sem_acao": texto_conversa_casual_sem_acao,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "texto_expresso_melhor_no_deterministico": lambda texto: (
            texto_expresso_melhor_no_deterministico(texto, normalizar_texto=normalizar)
        ),
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda *_args: "pc_a",
        "mente_integrada_estado": estado,
        "sites_diretos": {},
        "apps_map": {},
    }
    resultado_fluxo = detectar_intencao_deterministica_mente(
        "pode abrir o primeiro", ctx,
    )
    assert resultado_fluxo and resultado_fluxo["intent"] == "FILE_OPEN_RESULT"
    assert resultado_fluxo["params"]["alvo"] == "controlador.py"


def test_busca_atravessa_orquestrador_deterministico_real() -> None:
    normalizar = lambda texto: str(texto or "").casefold().strip()
    ctx = {
        "normalizar_texto": normalizar,
        "texto_conversa_casual_sem_acao": lambda _texto: False,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "texto_expresso_melhor_no_deterministico": lambda texto: (
            texto_expresso_melhor_no_deterministico(texto, normalizar_texto=normalizar)
        ),
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda *_args: "pc_a",
        "mente_integrada_estado": {},
        "sites_diretos": {},
        "apps_map": {},
    }

    resultado = detectar_intencao_deterministica_mente(
        "ache a imagem que usei ontem", ctx,
    )

    assert resultado and resultado["intent"] == "FILE_SEARCH"
    assert "imagem" in resultado["params"]["query"]


def test_busca_codigo_lampada_atravessa_portas_reais_da_entrada() -> None:
    frase = "encontra o código que controla a lâmpada"
    normalizar = lambda texto: str(texto or "").casefold().strip()

    assert texto_tem_comando_explicito(frase) is True
    assert texto_conversa_casual_sem_acao(frase) is False

    turno = classificar_modalidade_turno(
        frase,
        normalizar_texto=normalizar,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    assert turno["modalidade"] == "comando"
    assert turno["autoriza_execucao"] is True

    mapa = MapaHabilidadesRuntime()
    assert mapa.parece_consulta_operacional(frase) is True

    ctx = {
        "normalizar_texto": normalizar,
        "texto_conversa_casual_sem_acao": texto_conversa_casual_sem_acao,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "texto_expresso_melhor_no_deterministico": lambda texto: (
            texto_expresso_melhor_no_deterministico(texto, normalizar_texto=normalizar)
        ),
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda *_args: "pc_a",
        "mente_integrada_estado": {"turno_atual": turno},
        "sites_diretos": {},
        "apps_map": {},
    }
    resultado = detectar_intencao_deterministica_mente(frase, ctx)

    assert resultado == {
        "intent": "FILE_SEARCH",
        "params": {"query": "código que controla a lâmpada", "somente_projeto": False},
    }


def test_fluxo_real_publica_resultados_e_continua_por_referencia(tmp_path: Path) -> None:
    arquivo = tmp_path / "controle_lampada.py"
    arquivo.write_text("integração iot tuya", encoding="utf-8")
    abertos = []
    estruturas = []
    falas = []
    resultados_execucao = []
    aprendizados = []
    runtime = PesquisaSemanticaArquivosRuntime(
        raizes=[tmp_path],
        abrir_caminho=lambda caminho: abertos.append(caminho) or True,
        log=lambda *_args: None,
    )
    resultado = detectar_intencao_arquivos(
        "onde está o código que controla a lâmpada?", params_cb=_params,
    )
    assert resultado is not None
    ctx = {
        "_registrar_estrutura_arquivo_recente": estruturas.append,
        "_aprender_pesquisa_semantica_arquivos": lambda consulta, itens: aprendizados.append((consulta, itens)),
        "falar_com_lipsync": lambda texto, *_args: falas.append(texto),
    }

    tratado = executar_intencao_arquivos(
        resultado["intent"], resultado["params"], "pc_a", ctx,
        texto_original="onde está o código que controla a lâmpada?",
        marcar_resultado=lambda status, executou: resultados_execucao.append((status, executou)),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda caminho, tipo: Path(caminho).is_file() if tipo == "arquivo" else Path(caminho).exists(),
        resolver_caminho_local=lambda caminho: caminho,
        resolver_referencia_arquivo_contextual=lambda alvo, _tipo: alvo,
        arquivos_leitura=registrar_arquivos_leitura(runtime),
    )

    assert tratado is True
    assert resultados_execucao[-1] == ("arquivos_encontrados", True)
    assert falas and falas[-1].startswith("Encontrei controle_lampada.py")
    assert "não consegui confirmar" not in falas[-1].casefold()
    assert estruturas[-1]["tipo"] == "pesquisa_semantica"
    assert estruturas[-1]["resultados"] == [str(arquivo.resolve())]
    assert aprendizados and "lâmpada" in aprendizados[-1][0]

    estado = {"ultima_estrutura_arquivo_params": estruturas[-1]}
    caminho = detectar_intencao_arquivos("onde ele fica?", params_cb=_params, estado_mental=estado)
    abrir = detectar_intencao_arquivos("abre o primeiro", params_cb=_params, estado_mental=estado)

    assert caminho and caminho["intent"] == "FILE_SEARCH"
    assert caminho["params"]["referencia_caminho"] == str(arquivo.resolve())
    assert abrir and abrir["intent"] == "FILE_OPEN_RESULT"

    executar_intencao_arquivos(
        abrir["intent"], abrir["params"], "pc_a", ctx,
        texto_original="abre o primeiro",
        marcar_resultado=lambda status, executou: resultados_execucao.append((status, executou)),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda *_args: True,
        resolver_caminho_local=lambda caminho: caminho,
        resolver_referencia_arquivo_contextual=lambda alvo, _tipo: alvo,
        arquivos_leitura=registrar_arquivos_leitura(runtime),
    )
    assert abertos == [str(arquivo.resolve())]
    assert resultados_execucao[-1] == ("arquivo_aberto", True)
    assert falas[-1] == "Abri controle_lampada.py para você."


def test_resultados_da_busca_local_sao_confirmados_pelo_contrato_central() -> None:
    for intent, status in (
        ("FILE_SEARCH", "arquivos_encontrados"),
        ("FILE_SEARCH", "sem_resultados"),
        ("FILE_SEARCH", "caminho_encontrado"),
        ("FILE_OPEN_RESULT", "arquivo_aberto"),
    ):
        resultado = normalizar_resultado_acao({
            "intent": intent,
            "status": status,
            "executou": True,
        })
        assert resultado.confirmado is True
        assert planejar_resposta_acao(resultado, "Resultado local conferido.").classe == "sucesso"


def test_llm_tem_consciencia_real_da_pesquisa_semantica() -> None:
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt("encontra o código que controla a lâmpada")
    resposta = mapa.responder_pergunta_capacidade(
        "Lay, você consegue procurar arquivos pelo conteúdo?"
    )

    assert "FILE_SEARCH" in mapa.snapshot()["dominios"]["arquivos"]["intents"]
    assert "significado" in contexto.casefold()
    assert "índice fica só na memória" in resposta.casefold()
    assert "não envia seus arquivos" in resposta.casefold()
