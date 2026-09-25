from __future__ import annotations

import time

from mente_laylay.autonomia.roteador_intencao import bloquear_por_emocao
from mente_laylay.emocoes.contrato_causal import (
    criar_evento_emocional_causal,
    evento_pode_alterar_estado,
)
from mente_laylay.personalidade.contingencia_natural import fala_contingencia_natural
from mente_laylay.personalidade.resposta_conversacional_runtime import (
    RespostaConversacionalRuntime,
)
from mente_laylay.memoria_mental.diagnostico_mente import (
    construir_diagnostico_mente,
    formatar_diagnostico_terminal,
)
from mente_laylay.integracao.politicas_composicao import construir_estado_visual
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.emocoes.estado_emocional import (
    aplicar_evento_emocional,
    decair_estado_emocional,
)
from mente_laylay.emocoes.avaliador_eventos import contextualizar_fala_evento
from mente_laylay.memoria_mental.persistencia_memoria import registrar_autocorrecao_virtual


def _evento(*, inicio: float, validade_s: float = 120.0) -> dict:
    return criar_evento_emocional_causal(
        origem="resultado_operacional",
        causa="quatro pedidos redundantes com estado confirmado",
        evidencia_ref="resultado:music_search:4",
        natureza_evidencia="fato_observado",
        responsabilidade="usuario",
        confianca=0.96,
        relevancia=0.95,
        novidade=0.25,
        intensidade=3,
        sensibilidade="normal",
        alvo="Duality",
        validade_s=validade_s,
        permite_expressao=True,
        emocao="brava",
        nivel=3,
        arco="bronca_brincalhona",
        ts=inicio,
    )


def test_evento_expirado_nao_pode_alterar_estado() -> None:
    evento = _evento(inicio=time.time() - 300.0)

    assert evento_pode_alterar_estado(evento) is False


def test_emocao_brava_sem_evento_causal_nao_bloqueia_comando() -> None:
    falas: list[str] = []

    bloqueou = bloquear_por_emocao(
        "MUSIC_SEARCH",
        "toca Duality",
        {
            "current_emotion": "brava",
            "emotion_level": 3,
            "falar_com_lipsync": lambda fala, *_: falas.append(fala),
        },
    )

    assert bloqueou is False
    assert falas == []


def test_evento_de_outro_alvo_nao_bloqueia_comando_novo() -> None:
    falas: list[str] = []

    bloqueou = bloquear_por_emocao(
        "MUSIC_SEARCH",
        "toca outra música",
        {
            "current_emotion": "brava",
            "emotion_level": 3,
            "evento_emocional_causal": _evento(inicio=time.time()),
            "falar_com_lipsync": lambda fala, *_: falas.append(fala),
        },
    )

    assert bloqueou is False
    assert falas == []


def test_leitura_social_expirada_nao_e_expressa_em_turno_posterior() -> None:
    evento = criar_evento_emocional_causal(
        origem="contingencia_lexical_usuario",
        causa="tristeza relatada no turno original",
        evidencia_ref="turno:anterior:texto_usuario",
        natureza_evidencia="leitura_social",
        responsabilidade="ambigua",
        confianca=0.96,
        relevancia=0.9,
        novidade=0.8,
        intensidade=2,
        sensibilidade="vulneravel",
        alvo="estado_emocional_usuario",
        validade_s=120,
        permite_expressao=False,
        ts=time.time() - 300,
    )

    resposta = fala_contingencia_natural(
        "estou triste hoje",
        contexto={"plano_turno_atual": {
            "texto_usuario": "estou triste hoje",
            "evento_emocional_causal": evento,
        }},
    ).casefold()

    assert not any(marcador in resposta for marcador in ("trist", "ouvi", "entendo"))


def test_resultado_causal_abre_episodio_na_mesma_conversa_da_voz() -> None:
    evento = _evento(inicio=time.time())

    class Estado:
        def __init__(self) -> None:
            self.mental = {"eventos_emocionais_causais": {"atual": evento}}
            self.conversacional = {"current_emotion": "calma", "emotion_level": 1}

        def substituir(self, dominio: str, valor: dict) -> None:
            setattr(self, dominio, dict(valor))

    estado = Estado()
    runtime = RespostaConversacionalRuntime(
        namespace_getter=lambda: {},
        estado_runtime_getter=lambda: estado,
        fallback_fala="",
        log=lambda *_: None,
    )

    runtime.definir_emocao("brava", 3, evento["causa"])

    assert estado.conversacional["current_emotion"] == "brava"
    assert estado.conversacional["episodio_emocional"]["evidencia_ref"] == (
        evento["evidencia_ref"]
    )
    assert estado.conversacional["episodio_emocional"]["autoriza_execucao"] is False


def test_setter_conversacional_nao_cria_emocao_sem_evento_publicado() -> None:
    class Estado:
        def __init__(self) -> None:
            self.mental = {"eventos_emocionais_causais": {}}
            self.conversacional = {"current_emotion": "calma", "emotion_level": 1}

        def substituir(self, dominio: str, valor: dict) -> None:
            setattr(self, dominio, dict(valor))

    estado = Estado()
    runtime = RespostaConversacionalRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
        fallback_fala="", log=lambda *_: None,
    )

    runtime.definir_emocao("brava", 3, "tom usado na fala")

    assert estado.conversacional["current_emotion"] == "calma"
    assert estado.conversacional["emotion_level"] == 1
    assert not estado.conversacional.get("episodio_emocional")


def test_pedido_para_acalmar_encerra_episodio_sem_criar_outro_sem_causa() -> None:
    evento = _evento(inicio=time.time())

    class Estado:
        def __init__(self) -> None:
            self.conversacional = aplicar_evento_emocional({}, evento)

        def substituir(self, dominio: str, valor: dict) -> None:
            setattr(self, dominio, dict(valor))

    estado = Estado()
    runtime = RespostaConversacionalRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
        fallback_fala="", log=lambda *_: None,
    )

    runtime.acalmar_emocao("pedido para acalmar")

    assert estado.conversacional["current_emotion"] == "calma"
    assert estado.conversacional["emotion_level"] == 1
    assert estado.conversacional["episodio_emocional"] == {}
    assert estado.conversacional["transicao_emocional"]["para"] == "calma"


def test_tom_da_voz_nao_grava_episodio_emocional_sem_evento() -> None:
    class Estado:
        def __init__(self) -> None:
            self.conversacional = {"current_emotion": "calma", "emotion_level": 1}

        def atualizar_campos(self, dominio: str, **campos) -> None:
            assert dominio == "conversacional"
            self.conversacional.update(campos)

    estado = Estado()
    runtime = EstadoContextoRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
    )

    runtime.ajustar_estado_voz("current_emotion", "brava")
    runtime.ajustar_estado_voz("emotion_level", 3)

    assert estado.conversacional["current_emotion"] == "calma"
    assert estado.conversacional["emotion_level"] == 1


def test_autocorrecao_registrada_nao_muda_humor_sem_receipt_do_turno() -> None:
    class Memoria:
        def __getattr__(self, _nome):
            return lambda *args, **kwargs: None

    ajustes: list[tuple[int, str]] = []
    estado = registrar_autocorrecao_virtual(
        Memoria(), {}, "ia", "saida malformada", "json valido",
        ajustar_humor_cb=lambda delta, motivo: ajustes.append((delta, motivo)),
    )

    assert estado["_cookie_virtual_total"] == 1
    assert ajustes == []


def test_episodio_causal_expira_mesmo_sem_consumir_interacao() -> None:
    evento = _evento(inicio=time.time())
    estado = {
        "current_emotion": "brava",
        "emotion_level": 3,
        "emotion_started_at": evento["ts"],
        "emotion_duration_s": 210.0,
        "emotion_interactions_total": 5,
        "emotion_interactions_left": 5,
        "episodio_emocional": evento,
    }

    novo, alterou = decair_estado_emocional(
        estado,
        agora=evento["validade"]["expira_ts"] + 1,
        consumir_interacao=False,
    )

    assert alterou is True
    assert novo["current_emotion"] == "calma"
    assert novo["episodio_emocional"] == {}


def test_humor_de_fundo_muda_uma_vez_por_evidencia_e_recupera_devagar() -> None:
    agora = time.time()
    evento = _evento(inicio=agora, validade_s=600.0)
    inicial = {"humor_level": 0}

    primeiro = aplicar_evento_emocional(inicial, evento, agora=agora)
    repetido = aplicar_evento_emocional(primeiro, evento, agora=agora + 1.0)
    recuperado, _ = decair_estado_emocional(
        repetido, agora=agora + 301.0, consumir_interacao=False,
    )

    assert primeiro["humor_level"] == -1
    assert repetido["humor_level"] == -1
    assert repetido["emotion_started_at"] == primeiro["emotion_started_at"]
    assert recuperado["humor_level"] == 0


def test_correcao_de_fala_interrompe_episodio_de_braveza() -> None:
    agora = time.time()
    evento = _evento(inicio=agora)
    estado = aplicar_evento_emocional({}, evento, agora=agora)

    corrigido, _ = decair_estado_emocional(
        estado, agora=agora + 2,
        contexto="correcao",
    )

    assert corrigido["current_emotion"] == "calma"
    assert corrigido["episodio_emocional"] == {}


def test_jogo_nao_reaproveita_bronca_de_evento_expirado() -> None:
    evento = _evento(inicio=time.time() - 300.0)
    evento.update({"repeticoes": 4, "provocacao_usuario": 3})
    fala = "Duality já estava tocando; não repeti a ação."

    assert contextualizar_fala_evento(fala, evento, alvo="Duality") == fala


def test_diagnostico_mostra_causa_e_transicao_sem_texto_pessoal() -> None:
    evento = _evento(inicio=time.time())
    evento["causa"] = "Pedro ficou irritado com um segredo pessoal"
    evento["motivo_expressao"] = "redundancia_confirmada_repetida"
    conversa = aplicar_evento_emocional({}, evento)
    diagnostico = construir_diagnostico_mente(
        {"mental": {"eventos_emocionais_causais": {"atual": evento}},
         "conversacional": conversa},
        {},
    )
    texto = formatar_diagnostico_terminal(diagnostico)

    causal = diagnostico["estado_emocional_causal"]
    assert causal["causa"] == "redundancia_confirmada_repetida"
    assert causal["responsabilidade"] == "usuario"
    assert causal["confianca"] >= 0.9
    assert causal["validade"] is True
    assert causal["transicao"]["para"] == "brava"
    assert "redundancia_confirmada_repetida" in texto
    assert "segredo pessoal" not in texto


def test_avatar_nao_exibe_episodio_expirado() -> None:
    evento = _evento(inicio=100.0, validade_s=120.0)
    conversa = {
        "current_emotion": "brava", "emotion_level": 3,
        "episodio_emocional": evento,
    }

    visual = construir_estado_visual(
        conversa_get=lambda chave, padrao=None: conversa.get(chave, padrao),
        plano_get=lambda: {},
        time_fn=lambda: 221.0,
    )

    assert visual["emotion"] == "calma"
    assert visual["level"] == 1


def test_avatar_nao_exibe_emocao_sem_episodio_causal_expressavel() -> None:
    evento_contido = _evento(inicio=100.0)
    evento_contido["permite_expressao"] = False
    for episodio in ({}, evento_contido):
        conversa = {
            "current_emotion": "brava", "emotion_level": 3,
            "episodio_emocional": episodio,
        }
        visual = construir_estado_visual(
            conversa_get=lambda chave, padrao=None: conversa.get(chave, padrao),
            plano_get=lambda: {},
            time_fn=lambda: 101.0,
        )
        assert visual["emotion"] == "calma"
        assert visual["level"] == 1


def test_avatar_nao_exibe_emocao_divergente_do_episodio() -> None:
    conversa = {
        "current_emotion": "debochada", "emotion_level": 3,
        "episodio_emocional": _evento(inicio=100.0),
    }
    visual = construir_estado_visual(
        conversa_get=lambda chave, padrao=None: conversa.get(chave, padrao),
        plano_get=lambda: {},
        time_fn=lambda: 101.0,
    )
    assert visual["emotion"] == "calma"
    assert visual["level"] == 1


def test_avatar_falha_fechada_com_nivel_de_episodio_malformado() -> None:
    evento = _evento(inicio=100.0)
    evento["nivel"] = "invalido"
    conversa = {
        "current_emotion": "brava", "emotion_level": 3,
        "episodio_emocional": evento,
    }

    visual = construir_estado_visual(
        conversa_get=lambda chave, padrao=None: conversa.get(chave, padrao),
        plano_get=lambda: {},
        time_fn=lambda: 101.0,
    )

    assert visual["emotion"] == "calma"
    assert visual["level"] == 1


def test_avatar_calma_nao_preserva_intensidade_legada() -> None:
    conversa = {"current_emotion": "calma", "emotion_level": 3}
    visual = construir_estado_visual(
        conversa_get=lambda chave, padrao=None: conversa.get(chave, padrao),
        plano_get=lambda: {},
        time_fn=lambda: 101.0,
    )

    assert visual["emotion"] == "calma"
    assert visual["level"] == 1
