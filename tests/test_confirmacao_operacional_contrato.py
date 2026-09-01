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
