from __future__ import annotations

import pytest

from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.especialistas.capacidades import consultar_capacidade, intents_registradas
from mente_laylay.especialistas.operacional import anexar_resultados_operacionais
from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao
from mente_laylay.personalidade.confirmacao_llm import (
    _motivo_contrato_invalido,
    personalizar_confirmacao_llm,
)


@pytest.mark.parametrize("fala", [
    "A repetição da música foi ativada. Tá na hora de escutar de novo, sem parar!",
    "Desativei a repetição da música.",
    "A repetição da música foi alternada e ficou ligada.",
    "A repetição da música foi alternada e ficou desativada.",
])
def test_receipt_de_alternancia_nao_prova_direcao_do_estado(fala: str) -> None:
    resultado = normalizar_resultado_acao({
        "intent": "MEDIA_CONTROL", "status": "midia_repeat_toggle",
        "alvo": "musica", "params": {"acao": "repeat_toggle"},
        "executou": True, "confirmado": True, "origem": "executor",
    })
    assert _motivo_contrato_invalido(
        fala, resultado=resultado, classe="sucesso",
        status_declarado=resultado.status, alvo_declarado=resultado.alvo,
    ) == "estado_final_do_toggle_nao_evidenciado"


def test_confirmacao_de_alternancia_preserva_operacao_sem_inventar_estado() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "MEDIA_CONTROL", "status": "midia_repeat_toggle",
        "alvo": "musica", "params": {"acao": "repeat_toggle"},
        "executou": True, "confirmado": True,
    })
    assert _motivo_contrato_invalido(
        "A repetição da música foi alternada.", resultado=resultado,
        classe="sucesso", status_declarado=resultado.status,
        alvo_declarado=resultado.alvo,
    ) == ""


def test_autoria_e_reparo_sem_estado_observado_preservam_fala_segura_do_toggle() -> None:
    chamadas = []

    def modelo(mensagens, **opcoes):
        chamadas.append((mensagens, opcoes))
        return "A repetição da música foi ativada."

    resultado = normalizar_resultado_acao({
        "intent": "MEDIA_CONTROL", "status": "midia_repeat_toggle",
        "alvo": "musica", "params": {"acao": "repeat_toggle"},
        "executou": True, "confirmado": True,
    })
    fala_segura = "A repetição da música foi alternada."
    confirmacao = personalizar_confirmacao_llm(
        resultado, fala_segura, classe="sucesso", emocao="calma", nivel=1,
        enviar_mensagem=modelo,
    )
    assert len(chamadas) == 2
    assert "não confirma ativação" in chamadas[0][0][0]["content"]
    assert confirmacao.usada_llm is False
    assert confirmacao.fala == fala_segura
    assert confirmacao.motivo_fallback == "contrato_nao_preservado:estado_final_do_toggle_nao_evidenciado"


def test_todo_intent_documenta_como_confirma_resultado() -> None:
    assert intents_registradas()
    for intent in intents_registradas():
        capacidade = consultar_capacidade(intent)
        assert capacidade["confirmacao_oferecida"] in {
            "estado_observado", "persistencia_local", "retorno_dados",
            "estado_local", "variavel", "indisponivel",
        }
        assert capacidade["evidencia_confirmacao"]
        assert capacidade["estado_sem_confirmacao"] == "nao_confirmado"


@pytest.mark.parametrize(
    ("intent", "status"),
    [
        ("APP_OPEN", "app_aberto_pc_b"),
        ("OPEN_URL", "protocolo_aberto"),
        ("MEDIA_CONTROL", "midia_next"),
        ("CREATE_FOLDER", "pasta_criada_pc_b"),
        ("IOT_CONTROL", "ligado"),
    ],
)
def test_execucao_sem_evidencia_fica_nao_confirmada_por_dominio(intent: str, status: str) -> None:
    resultado = normalizar_resultado_acao({
        "intent": intent,
        "status": status,
        "executou": True,
    })

    assert resultado.confirmado is None
    assert resultado.como_dict()["estado_confirmacao"] == "nao_confirmado"
    assert planejar_resposta_acao(resultado, "Pronto, concluí.").classe == "incerto"
    assert "não consegui confirmar" in planejar_resposta_acao(resultado, "Pronto, concluí.").fala


@pytest.mark.parametrize(
    ("intent", "status"),
    [
        ("CLOSE_APP", "app_fechado"),
        ("OPEN_URL", "url_aberta"),
        ("CREATE_FILE", "arquivo_criado"),
        ("FILE_SEARCH", "arquivos_encontrados"),
        ("FILE_OPEN_RESULT", "arquivo_aberto"),
    ],
)
def test_estado_local_realmente_observado_pode_ser_confirmado(intent: str, status: str) -> None:
    resultado = normalizar_resultado_acao({
        "intent": intent,
        "status": status,
        "executou": True,
    })

    assert resultado.confirmado is True
    assert resultado.como_dict()["estado_confirmacao"] == "confirmado"


def test_iot_exige_confirmacao_explicita_da_releitura() -> None:
    sem_releitura = normalizar_resultado_acao({
        "intent": "IOT_CONTROL", "status": "desligado", "executou": True,
    })
    com_releitura = normalizar_resultado_acao({
        "intent": "IOT_CONTROL", "status": "desligado", "executou": True,
        "confirmado": True,
    })

    assert sem_releitura.confirmado is None
    assert com_releitura.confirmado is True


def test_resultado_legado_aceita_params_e_contexto_nulos() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "OPEN_URL",
        "params": None,
        "contexto": None,
        "executou": False,
    })

    assert resultado.alvo == ""
    assert resultado.params == {}
    assert resultado.contexto == {}
    assert resultado.confirmado is False


def test_intent_sem_confirmacao_possivel_nao_aceita_sucesso_forcado() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "LOCK_PC", "status": "bloqueio_solicitado",
        "executou": True, "confirmado": True,
    })

    assert resultado.confirmacao_oferecida == "indisponivel"
    assert resultado.confirmado is None
    assert resultado.como_dict()["estado_confirmacao"] == "nao_confirmado"


def test_guardiao_nao_confunde_envio_com_conclusao() -> None:
    validacao = validar_alegacoes_da_fala(
        "Pronto, desliguei a lâmpada.",
        plano={"comandos": [{
            "intent": "IOT_CONTROL", "status": "desligado",
            "executou": True, "confirmado": None,
        }]},
        origem="resposta_ia",
    )

    assert "execucao_alegada_sem_resultado" in validacao["problemas"]
    assert "comando foi enviado" in validacao["fala"]
    assert "não consegui confirmar" in validacao["fala"]


def test_parecer_operacional_so_libera_conclusao_quando_todos_confirmam() -> None:
    parcial, _ = anexar_resultados_operacionais({}, [
        {"intent": "OPEN_URL", "status": "url_aberta", "executou": True},
        {"intent": "MEDIA_CONTROL", "status": "midia_next", "executou": True},
    ])
    completo, _ = anexar_resultados_operacionais({}, [
        {"intent": "OPEN_URL", "status": "url_aberta", "executou": True},
        {"intent": "MEDIA_CONTROL", "status": "midia_next", "executou": True, "confirmado": True},
    ])

    assert parcial["pode_afirmar_conclusao"] is False
    assert parcial["sem_confirmacao"]
    assert completo["pode_afirmar_conclusao"] is True


def test_autoria_nao_pode_trocar_identificador_alfanumerico_da_musica() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "MUSIC_SEARCH",
        "params": {"query": "C418 - Sweden Minecraft Volume Alpha"},
        "alvo": "C418 - Sweden Minecraft Volume Alpha",
        "status": "musica_nao_resolvida",
        "executou": False,
        "confirmado": False,
    })

    motivo = _motivo_contrato_invalido(
        "Não encontrei C410 - Sweden Minecraft Volume Alpha.",
        resultado=resultado,
        classe="falha",
        status_declarado="musica_nao_resolvida",
        alvo_declarado="C418 - Sweden Minecraft Volume Alpha",
    )

    assert motivo == "identificador_concreto_divergente"


def test_autoria_nao_inventa_que_playlist_confirmada_esta_vazia() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "PLAYLIST_ADD",
        "alvo": "vmz",
        "status": "playlist_musica_adicionada",
        "executou": True,
        "confirmado": True,
        "params": {"nome_playlist": "vmz", "titulo": "Bad Girl"},
    })

    motivo = _motivo_contrato_invalido(
        "Salvei Bad Girl na playlist vmz. A playlist está vazia.",
        resultado=resultado,
        classe="sucesso",
        status_declarado="playlist_musica_adicionada",
        alvo_declarado="vmz",
    )

    assert motivo == "estado_operacional_nao_evidenciado"


def test_autoria_operacional_rejeita_metafora_sem_evidencia() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "PLAYLIST_ADD",
        "alvo": "vmz",
        "status": "playlist_musica_adicionada",
        "executou": True,
        "confirmado": True,
        "params": {"nome_playlist": "vmz", "titulo": "Amanhecer"},
    })

    motivo = _motivo_contrato_invalido(
        "Salvei Amanhecer na playlist vmz. Como se o celular tivesse coração.",
        resultado=resultado,
        classe="sucesso",
        status_declarado="playlist_musica_adicionada",
        alvo_declarado="vmz",
    )

    assert motivo == "metafora_operacional_nao_ancorada"


def test_autoria_pode_personalizar_execucao_parcial_sem_pedir_permissao() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "MUSIC_SEARCH",
        "params": {"query": "C418 - Sweden"},
        "alvo": "C418 - Sweden",
        "status": "musica_enviada_sem_confirmacao",
        "executou": True,
        "confirmado": None,
    })

    confirmacao = personalizar_confirmacao_llm(
        resultado,
        "Abri C418 - Sweden, mas o player não confirmou a reprodução.",
        classe="incerto",
        emocao="calma",
        nivel=1,
        enviar_mensagem=lambda *_args, **_kwargs: (
            '{"fala":"Abri C418 - Sweden, mas o player não confirmou o áudio.",'
            '"emocao":"calma","nivel":1,'
            '"status":"musica_enviada_sem_confirmacao",'
            '"alvo":"C418 - Sweden"}'
        ),
        contexto={},
    )

    assert confirmacao.usada_llm is True
    assert "não confirmou" in confirmacao.fala.casefold()
    assert "confirma antes" not in confirmacao.fala.casefold()


def test_fala_de_musica_tocando_ja_confirma_o_resultado_sem_repetir_titulo() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "MUSIC_SEARCH",
        "params": {
            "query": "Shiny - Vazio Constante | Bojack, Rick & Clancy",
        },
        "alvo": "Shiny - Vazio Constante",
        "status": "musica_reproduzindo",
        "executou": True,
        "confirmado": True,
        "texto_usuario": "coloca vazio constante shiny_sz",
    })

    plano = planejar_resposta_acao(
        resultado,
        "Shiny - Vazio Constante está tocando agora.",
    )

    assert plano.fala == "Shiny - Vazio Constante está tocando agora."
    assert plano.fala.count("Shiny - Vazio Constante") == 1


def test_autoria_rejeita_parcial_que_finge_confirmacao_total() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "MUSIC_SEARCH",
        "params": {"query": "C418 - Sweden"},
        "alvo": "C418 - Sweden",
        "status": "musica_enviada_sem_confirmacao",
        "executou": True,
        "confirmado": None,
    })

    motivo = _motivo_contrato_invalido(
        "Pronto, C418 - Sweden está tocando.",
        resultado=resultado,
        classe="incerto",
        status_declarado="musica_enviada_sem_confirmacao",
        alvo_declarado="C418 - Sweden",
    )

    assert motivo == "incerteza_ocultada"


def test_autoria_operacional_se_corrige_antes_de_usar_fala_local() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "APP_OPEN",
        "params": {"nome_app": "Opera"},
        "alvo": "Opera",
        "status": "ja_aberto_focado",
        "executou": False,
        "confirmado": True,
    })
    chamadas = []

    def modelo(*_args, **_kwargs):
        chamadas.append(1)
        if len(chamadas) == 1:
            return (
                '{"fala":"Abri o Opera de novo.","emocao":"calma","nivel":1,'
                '"status":"ja_aberto_focado","alvo":"Opera"}'
            )
        return (
            '{"fala":"O Opera já estava aberto e em foco; não repeti a abertura.",'
            '"emocao":"debochada","nivel":1,'
            '"status":"ja_aberto_focado","alvo":"Opera"}'
        )

    confirmacao = personalizar_confirmacao_llm(
        resultado,
        "Opera já estava aberto e em foco; não repeti a abertura.",
        classe="sem_acao",
        emocao="calma",
        nivel=1,
        enviar_mensagem=modelo,
        contexto={},
    )

    assert len(chamadas) == 2
    assert confirmacao.usada_llm is True
    assert "não repeti" in confirmacao.fala.casefold()


def test_autoria_operacional_aceita_fala_pura_sem_redeclarar_receipt_em_json() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "APP_OPEN",
        "params": {"nome_app": "calculadora"},
        "alvo": "calculadora",
        "status": "app_iniciado_focado",
        "executou": True,
        "confirmado": True,
    })

    confirmacao = personalizar_confirmacao_llm(
        resultado,
        "Iniciei calculadora e trouxe a nova janela pra frente.",
        classe="sucesso",
        emocao="calma",
        nivel=1,
        enviar_mensagem=lambda *_args, **_kwargs: (
            "Iniciei a calculadora e trouxe a janela pra frente."
        ),
        contexto={},
    )

    assert confirmacao.usada_llm is True
    assert confirmacao.motivo_fallback == ""
    assert "calculadora" in confirmacao.fala.casefold()


def test_autoria_operacional_remove_enxerto_literal_de_contexto_antigo() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "AGENDAR_LEMBRETE",
        "alvo": "revisar o código",
        "status": "lembrete_agendado",
        "executou": True,
        "confirmado": True,
    })
    chamadas = []

    def modelo(*_args, **_kwargs):
        chamadas.append(1)
        if len(chamadas) == 1:
            return (
                '{"fala":"Agendei revisar o código. Você ainda não me contou nada '
                'confiável sobre Beber Água.","emocao":"calma","nivel":1,'
                '"status":"lembrete_agendado","alvo":"revisar o código"}'
            )
        return (
            '{"fala":"Agendei o lembrete de revisar o código.",'
            '"emocao":"calma","nivel":1,'
            '"status":"lembrete_agendado","alvo":"revisar o código"}'
        )

    confirmacao = personalizar_confirmacao_llm(
        resultado,
        "Agendei o lembrete de revisar o código.",
        classe="sucesso",
        emocao="calma",
        nivel=1,
        enviar_mensagem=modelo,
        contexto={
            "ultima_resposta": (
                "Você ainda não me contou nada confiável sobre Beber Água."
            ),
        },
    )

    assert len(chamadas) == 2
    assert confirmacao.usada_llm is True
    assert "Beber Água" not in confirmacao.fala


def test_listagem_antiga_nao_pode_confirmar_exclusao_de_playlist() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "PLAYLIST_DELETE",
        "alvo": "roteiro teste",
        "status": "playlist_deletada",
        "executou": True,
        "confirmado": True,
    })

    motivo = _motivo_contrato_invalido(
        "A playlist Roteiro Teste é curtinha: 1 música.",
        resultado=resultado,
        classe="sucesso",
        status_declarado="playlist_deletada",
        alvo_declarado="roteiro teste",
    )

    assert motivo == "estado_observado_ausente"


def test_append_confirmado_nao_pode_ser_reescrito_como_criacao() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "CREATE_FILE",
        "alvo": "teste completo.txt",
        "status": "conteudo_acrescentado",
        "executou": True,
    })

    assert resultado.confirmado is True
    assert _motivo_contrato_invalido(
        "Criei o arquivo teste completo.txt.",
        resultado=resultado,
        classe="sucesso",
        status_declarado="conteudo_acrescentado",
        alvo_declarado="teste completo.txt",
    ) == "estado_observado_ausente"
    assert _motivo_contrato_invalido(
        "Acrescentei a nova linha no arquivo teste completo.txt.",
        resultado=resultado,
        classe="sucesso",
        status_declarado="conteudo_acrescentado",
        alvo_declarado="teste completo.txt",
    ) == ""


def test_listagem_antiga_nao_pode_confirmar_adicao_em_playlist() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "PLAYLIST_ADD",
        "alvo": "rock",
        "status": "playlist_musica_adicionada",
        "executou": True,
        "confirmado": True,
    })

    motivo = _motivo_contrato_invalido(
        "A playlist rock tá pronta com 20 músicas — e já escolhi três.",
        resultado=resultado,
        classe="sucesso",
        status_declarado="playlist_musica_adicionada",
        alvo_declarado="rock",
    )

    assert motivo == "estado_observado_ausente"


def test_cancelamento_nao_pode_reintroduzir_lembrete_ou_cobranca() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "CANCELAR_AGENDAMENTO",
        "alvo": "beber água",
        "status": "agendamento_cancelado",
        "executou": True,
        "confirmado": True,
    })

    motivo = _motivo_contrato_invalido(
        (
            "Beber água foi cancelado. Só não esqueça de beber, "
            "a gente está no aguardo."
        ),
        resultado=resultado,
        classe="sucesso",
        status_declarado="agendamento_cancelado",
        alvo_declarado="beber água",
    )

    assert motivo == "cancelamento_reintroduziu_obrigacao"
    assert _motivo_contrato_invalido(
        "Cancelei beber água. Esse compromisso saiu da agenda.",
        resultado=resultado,
        classe="sucesso",
        status_declarado="agendamento_cancelado",
        alvo_declarado="beber água",
    ) == ""


def test_consulta_de_caminho_preserva_dado_literal_sem_autoria_operacional() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "FILE_SEARCH",
        "alvo": "roteiro correcao.txt",
        "status": "caminho_encontrado",
        "executou": True,
        "confirmado": True,
    })
    chamadas: list[bool] = []
    fala = (
        r"O arquivo fica em C:\Users\pbarr\Downloads\carlos\roteiro correcao.txt."
    )

    confirmacao = personalizar_confirmacao_llm(
        resultado,
        fala,
        classe="sucesso",
        emocao="calma",
        nivel=1,
        enviar_mensagem=lambda *_args, **_kwargs: chamadas.append(True),
        contexto={},
    )

    assert confirmacao.fala == fala
    assert confirmacao.usada_llm is False
    assert chamadas == []



def test_fala_incerta_sem_evidencia_de_execucao_nao_afirma_que_enviou_comando() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "APP_OPEN",
        "alvo": "Chrome",
        "status": "tratado_sem_receipt",
        "executou": None,
        "confirmado": None,
    })

    plano = planejar_resposta_acao(
        resultado,
        "Pronto, abri o Chrome.",
    )

    assert plano.classe == "incerto"
    assert "não tenho confirmação" in plano.fala.casefold()
    assert "enviei o comando" not in plano.fala.casefold()
    assert "abri o chrome" not in plano.fala.casefold()


def test_bloqueio_por_politica_nao_e_descrito_como_tentativa_falha() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "IOT_CONTROL",
        "alvo": "luz",
        "status": "nao_executado_por_politica",
        "executou": False,
        "confirmado": False,
    })

    plano = planejar_resposta_acao(
        resultado,
        "Não consegui ligar a luz.",
    )

    assert plano.classe == "nao_executado"
    assert "não executei" in plano.fala.casefold()
    assert "não consegui" not in plano.fala.casefold()
    assert "tentei" not in plano.fala.casefold()


@pytest.mark.parametrize("intent, status, alvo, segura, contaminada", [
    (
        "APP_OPEN", "ja_aberto_focado", "calculadora",
        "calculadora já está aberto e em foco; não repeti a abertura.",
        "calculadora já está aberto e em foco; não repeti a abertura, e o erro de "
        "tamanho_invalido não se aplica aqui — você me deu um problema que não existe no cenário real.",
    ),
    (
        "IOT_CONTROL", "ja_estava_ligado", "abajur",
        "O abajur já está ligado; não repeti o comando.",
        "O abajur já está ligado; não repeti o comando, e o erro de "
        "tamanho_invalido não se aplica aqui — você me deu um problema que não existe no cenário real.",
    ),
])
def test_retry_nao_transforma_diagnostico_da_redacao_em_fato_do_receipt(
    intent: str, status: str, alvo: str, segura: str, contaminada: str,
) -> None:
    resultado = normalizar_resultado_acao({
        "intent": intent, "status": status, "alvo": alvo,
        "executou": False, "confirmado": True, "origem": "executor",
    })
    chamadas: list[list[dict]] = []

    def transporte_local(mensagens, **_opcoes):
        chamadas.append(mensagens)
        return "x" * 261 if len(chamadas) == 1 else contaminada

    confirmacao = personalizar_confirmacao_llm(
        resultado, segura, classe="sem_acao", emocao="calma", nivel=1,
        enviar_mensagem=transporte_local, contexto={},
    )

    assert len(chamadas) == 2
    assert "tamanho_invalido" not in chamadas[1][-1]["content"]
    assert confirmacao.usada_llm is False
    assert confirmacao.fala == segura
    assert confirmacao.motivo_fallback == "contrato_nao_preservado:tamanho_invalido"


@pytest.mark.parametrize("proposta_rejeitada, motivo", [
    ("x" * 261, "tamanho_invalido"),
    ("{", "json_invalido"),
    ("Calculadora já está aberta como se fosse uma rainha; não repeti a abertura.",
     "metafora_operacional_nao_ancorada"),
])
def test_retry_preserva_diagnostico_local_sem_projeta_lo_como_fonte_da_autoria(
    proposta_rejeitada: str, motivo: str,
) -> None:
    resultado = normalizar_resultado_acao({
        "intent": "APP_OPEN", "status": "ja_aberto_focado", "alvo": "calculadora",
        "executou": False, "confirmado": True, "origem": "executor",
    })
    segura = "Calculadora já está aberto e em foco; não repeti a abertura."
    chamadas: list[list[dict]] = []

    def transporte_local(mensagens, **_opcoes):
        chamadas.append(mensagens)
        return proposta_rejeitada if len(chamadas) == 1 else segura

    confirmacao = personalizar_confirmacao_llm(
        resultado, segura, classe="sem_acao", emocao="calma", nivel=1,
        enviar_mensagem=transporte_local, contexto={},
    )

    assert len(chamadas) == 2
    assert motivo not in chamadas[1][-1]["content"]
    assert "somente os fatos" in chamadas[1][-1]["content"]
    assert confirmacao.usada_llm is True
    assert confirmacao.fala == segura


@pytest.mark.parametrize("identificador", ["tamanho_invalido", "analise_nao_ancorada", "falha_de_verificacao"])
def test_identificador_tecnico_sem_fonte_nao_compoe_confirmacao(identificador: str) -> None:
    resultado = normalizar_resultado_acao({
        "intent": "APP_OPEN", "status": "ja_aberto_focado", "alvo": "calculadora",
        "executou": False, "confirmado": True, "origem": "executor",
        "params": {"responsabilidade": identificador},
        "contexto": {"diagnostico": identificador},
    })
    motivo = _motivo_contrato_invalido(
        f"Calculadora já está aberta e em foco; não repeti a abertura por {identificador}.",
        resultado=resultado, classe="sem_acao", status_declarado=resultado.status,
        alvo_declarado=resultado.alvo,
    )

    assert motivo == "diagnostico_sem_evidencia"


@pytest.mark.parametrize("nome", ["tamanho_invalido.txt", "analise_nao_ancorada.txt"])
def test_nome_factual_com_underscore_permanece_na_confirmacao(nome: str) -> None:
    resultado = normalizar_resultado_acao({
        "intent": "CREATE_FILE", "status": "arquivo_criado", "alvo": nome,
        "params": {"nome_arquivo": nome}, "executou": True, "confirmado": True,
        "origem": "executor",
    })
    segura = f"Criei o arquivo {nome}."
    chamadas: list[bool] = []

    def transporte_local(*_argumentos, **_opcoes):
        chamadas.append(True)
        return segura

    confirmacao = personalizar_confirmacao_llm(
        resultado, segura, classe="sucesso", emocao="calma", nivel=1,
        enviar_mensagem=transporte_local, contexto={},
    )

    assert chamadas == [True]
    assert confirmacao.usada_llm is True
    assert confirmacao.fala == segura


def test_diagnostico_real_do_executor_pode_compor_fala_de_falha() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "APP_OPEN", "status": "falha_execucao", "alvo": "Opera",
        "executou": False, "confirmado": False, "origem": "executor",
        "detalhe": "tamanho_invalido",
    })

    assert _motivo_contrato_invalido(
        "Não consegui abrir o Opera: o executor informou tamanho_invalido.",
        resultado=resultado, classe="falha", status_declarado=resultado.status,
        alvo_declarado=resultado.alvo,
    ) == ""


def test_transformacao_de_abertura_nao_aprova_saida_que_viola_contrato() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "APP_OPEN", "status": "ja_aberto_focado", "alvo": "calculadora",
        "executou": False, "confirmado": True, "origem": "executor",
    })
    segura = "Calculadora já está aberto e em foco; não repeti a abertura."
    proposta = (
        "Calculadora já está aberto e em foco, não repeti a abertura, "
        "a janela continua pronta, o pedido encontrou o destino, deixei tudo como estava."
    )
    assert _motivo_contrato_invalido(
        proposta, resultado=resultado, classe="sem_acao", status_declarado=resultado.status,
        alvo_declarado=resultado.alvo,
    ) == ""
    chamadas: list[bool] = []

    def transporte_local(*_argumentos, **_opcoes):
        chamadas.append(True)
        return proposta

    confirmacao = personalizar_confirmacao_llm(
        resultado, segura, classe="sem_acao", emocao="calma", nivel=1,
        enviar_mensagem=transporte_local, contexto={"falas_recentes": [segura]},
    )

    assert chamadas == [True]
    assert confirmacao.usada_llm is False
    assert confirmacao.fala == segura
    assert confirmacao.motivo_fallback == "contrato_nao_preservado:fala_operacional_prolixa"


def test_transformacao_de_abertura_preserva_variacao_validada() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "APP_OPEN", "status": "ja_aberto_focado", "alvo": "calculadora",
        "executou": False, "confirmado": True, "origem": "executor",
    })
    proposta = (
        "Calculadora já está aberta e em foco; não repeti o comando porque a Calculadora está em foco."
    )
    segura = "Calculadora já está aberta e em foco; não repeti a abertura."
    confirmacao = personalizar_confirmacao_llm(
        resultado, segura, classe="sem_acao", emocao="calma", nivel=1,
        enviar_mensagem=lambda *_argumentos, **_opcoes: proposta,
        contexto={"falas_recentes": [segura]},
    )

    assert confirmacao.usada_llm is True
    assert confirmacao.fala.startswith("Não repeti o comando porque a Calculadora está em foco.")
    assert _motivo_contrato_invalido(
        confirmacao.fala, resultado=resultado, classe="sem_acao", status_declarado=resultado.status,
        alvo_declarado=resultado.alvo,
    ) == ""



def test_confirmacao_none_explicita_nao_e_promovida_por_status_otimista() -> None:
    explicito = normalizar_resultado_acao({
        "intent": "APP_OPEN",
        "status": "app_aberto",
        "executou": True,
        "confirmado": None,
    })
    legado_sem_campo = normalizar_resultado_acao({
        "intent": "APP_OPEN",
        "status": "app_aberto",
        "executou": True,
    })

    assert explicito.confirmado is None
    assert explicito.como_dict()["estado_confirmacao"] == "nao_confirmado"
    assert legado_sem_campo.confirmado is True
