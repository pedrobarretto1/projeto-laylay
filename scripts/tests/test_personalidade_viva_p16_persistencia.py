from __future__ import annotations

import time

import pytest

from memoria_sqlite import MemoriaSQLite
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.avaliador_eventos import AvaliadorEventosEmocionaisRuntime
from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa
from mente_laylay.emocoes.estado_emocional import (
    aplicar_evento_emocional,
    decair_estado_emocional,
    retrato_emocional_expressavel,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.persistencia_memoria import PersistenciaMemoriaRuntime
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.memoria_mental.encerramento_assunto import classificar_encerramento_assunto
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.integracao.adaptadores_composicao import avaliar_evento_emocional_operacional
from mente_laylay.personalidade.resposta_conversacional_runtime import RespostaConversacionalRuntime
from mente_laylay.integracao.politicas_composicao import construir_estado_visual


class _MemoriaSalva:
    def __init__(self, dados: dict) -> None:
        self.dados = dados

    def carregar_estado(self) -> dict:
        return dict(self.dados)

    def listar_aprendizados_semanticos(self, **_kwargs) -> list:
        return []


def _evento(ts: float, *, validade_s: float = 210.0) -> dict:
    return criar_evento_emocional_causal(
        origem="resultado_operacional",
        causa="quatro pedidos redundantes confirmados",
        evidencia_ref="resultado:musica:4",
        natureza_evidencia="fato_observado",
        responsabilidade="usuario",
        confianca=0.96,
        relevancia=0.9,
        novidade=0.25,
        intensidade=3,
        sensibilidade="normal",
        alvo="música",
        validade_s=validade_s,
        permite_expressao=True,
        emocao="brava",
        nivel=3,
        arco="bronca_brincalhona",
        ts=ts,
    )


def _carregar(dados: dict) -> tuple[EstadoCompartilhadoRuntime, PersistenciaMemoriaRuntime]:
    estado = EstadoCompartilhadoRuntime(conversacional={"current_emotion": "calma"})
    runtime = PersistenciaMemoriaRuntime(
        memoria_sqlite=_MemoriaSalva(dados),
        base_system_prompt="identidade atual",
        estado_obter=estado.obter,
        estado_atualizar=estado.atualizar_campos,
        log=lambda *_args: None,
    )
    runtime.carregar()
    return estado, runtime


@pytest.mark.parametrize("com_evento", [False, True])
def test_reinicio_so_restaura_emocao_com_episodio_causal_vigente(com_evento: bool) -> None:
    dados = {
        "current_emotion": "brava",
        "emotion_level": 3,
        "emotion_cause": "quatro pedidos redundantes confirmados",
        "emotion_started_at": time.time(),
        "emotion_duration_s": 210.0,
        "emotion_interactions_total": 5,
        "emotion_interactions_left": 5,
    }
    if com_evento:
        dados["episodio_emocional"] = _evento(dados["emotion_started_at"])

    estado, _runtime = _carregar(dados)
    esperado = "brava" if com_evento else "calma"

    assert estado.conversacional["current_emotion"] == esperado
    assert retrato_emocional_expressavel(estado.conversacional)[0] == esperado


def test_reinicio_nao_restaura_episodio_causal_expirado() -> None:
    evento = _evento(time.time() - 300.0)
    estado, _runtime = _carregar({
        "current_emotion": "brava", "emotion_level": 3,
        "episodio_emocional": evento,
    })

    assert estado.conversacional["current_emotion"] == "calma"
    assert retrato_emocional_expressavel(estado.conversacional) == ("calma", 1)


def test_snapshot_preserva_referencia_causal_do_episodio_vigente() -> None:
    evento = _evento(time.time())
    estado = EstadoCompartilhadoRuntime(conversacional=aplicar_evento_emocional(
        {}, evento,
    ))
    runtime = PersistenciaMemoriaRuntime(
        memoria_sqlite=_MemoriaSalva({}),
        base_system_prompt="identidade atual",
        estado_obter=estado.obter,
        estado_atualizar=estado.atualizar_campos,
        log=lambda *_args: None,
    )

    assert runtime.snapshot()["episodio_emocional"]["evidencia_ref"] == "resultado:musica:4"


def test_episodio_vigente_sobrevive_ao_ciclo_real_de_sqlite(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "laylay_memoria.sqlite"))
    evento = _evento(time.time())
    origem = EstadoCompartilhadoRuntime(conversacional={
        "current_emotion": "brava", "emotion_level": 3,
        "emotion_cause": evento["causa"],
        "emotion_started_at": evento["ts"],
        "emotion_duration_s": 210.0,
        "emotion_interactions_total": 5,
        "emotion_interactions_left": 5,
        "episodio_emocional": evento,
        "humor_level": -2,
        "humor_last_update": time.time(),
    })
    escritor = PersistenciaMemoriaRuntime(
        memoria_sqlite=memoria, base_system_prompt="identidade atual",
        estado_obter=origem.obter, estado_atualizar=origem.atualizar_campos,
        log=lambda *_args: None,
    )
    assert escritor.salvar() is True

    destino = EstadoCompartilhadoRuntime(conversacional={"current_emotion": "calma"})
    leitor = PersistenciaMemoriaRuntime(
        memoria_sqlite=memoria, base_system_prompt="identidade atual",
        estado_obter=destino.obter, estado_atualizar=destino.atualizar_campos,
        log=lambda *_args: None,
    )
    leitor.carregar()

    assert retrato_emocional_expressavel(destino.conversacional) == ("brava", 3)
    assert destino.conversacional["episodio_emocional"]["evidencia_ref"] == evento["evidencia_ref"]
    assert destino.conversacional["humor_level"] == -2


@pytest.mark.parametrize(
    ("idade_s", "esperado"),
    [(30.0, -2), (900.0, 0), (None, 0)],
)
def test_humor_de_fundo_reidrata_com_decaimento_ou_volta_ao_neutro(
    idade_s: float | None, esperado: int,
) -> None:
    dados = {"current_emotion": "calma", "humor_level": -2}
    if idade_s is not None:
        dados["humor_last_update"] = time.time() - idade_s

    estado, _runtime = _carregar(dados)

    assert estado.conversacional.get("humor_level", 0) == esperado


def test_retrato_de_voz_respeita_duracao_do_episodio_sem_novo_turno() -> None:
    evento = _evento(100.0, validade_s=300.0)
    estado = aplicar_evento_emocional({}, evento, agora=100.0)

    assert retrato_emocional_expressavel(estado, agora=150.0) == ("brava", 3)
    assert retrato_emocional_expressavel(estado, agora=311.0) == ("calma", 1)


def test_avatar_e_voz_leem_o_mesmo_episodio_antes_e_depois_do_prazo() -> None:
    evento = _evento(100.0, validade_s=300.0)
    estado = aplicar_evento_emocional({}, evento, agora=100.0)

    for instante in (150.0, 311.0):
        visual = construir_estado_visual(
            conversa_get=lambda chave, padrao=None: estado.get(chave, padrao),
            plano_get=lambda: {}, time_fn=lambda: instante,
        )
        assert (visual["emotion"], visual["level"]) == retrato_emocional_expressavel(
            estado, agora=instante,
        )


def test_episodio_forte_resiste_evento_fraco_sem_bloquear_recuperacao() -> None:
    forte = _evento(100.0, validade_s=300.0)
    fraco = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="sucesso rotineiro confirmado",
        evidencia_ref="resultado:musica:5", natureza_evidencia="fato_observado",
        responsabilidade="sistema", confianca=0.96, relevancia=0.9,
        novidade=0.4, intensidade=1, sensibilidade="normal", alvo="música",
        validade_s=120.0, permite_expressao=True, emocao="alegre", nivel=1,
        arco="rotina", ts=110.0,
    )
    recuperacao = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="sucesso após falhas confirmadas",
        evidencia_ref="resultado:musica:6", natureza_evidencia="fato_observado",
        responsabilidade="sistema", confianca=0.96, relevancia=0.95,
        novidade=0.8, intensidade=1, sensibilidade="normal", alvo="música",
        validade_s=120.0, permite_expressao=True, emocao="acalmando-se", nivel=1,
        arco="alivio", ts=120.0,
    )

    estado = aplicar_evento_emocional({}, forte, agora=100.0)
    depois_rotina = aplicar_evento_emocional(estado, fraco, agora=110.0)
    recuperacao_outro_alvo = {
        **recuperacao,
        "alvo": "lâmpada",
        "evidencia_ref": "resultado:lampada:1",
    }
    depois_outro_alvo = aplicar_evento_emocional(
        estado, recuperacao_outro_alvo, agora=120.0,
    )
    depois_recuperacao = aplicar_evento_emocional(depois_rotina, recuperacao, agora=120.0)

    assert depois_rotina["current_emotion"] == "brava"
    assert depois_rotina["episodio_emocional"]["evidencia_ref"] == forte["evidencia_ref"]
    assert depois_rotina["humor_level"] == 0
    assert depois_outro_alvo["current_emotion"] == "brava"
    assert depois_recuperacao["current_emotion"] == "acalmando-se"
    assert depois_recuperacao["episodio_emocional"]["evidencia_ref"] == recuperacao["evidencia_ref"]


def test_recuperacao_real_do_avaliador_substitui_falha_do_mesmo_alvo() -> None:
    instante = [100.0]
    avaliador = AvaliadorEventosEmocionaisRuntime(
        time_cb=lambda: instante[0], log=lambda *_args: None,
    )
    estado: dict = {}
    for indice in (1, 2):
        instante[0] = 100.0 + indice * 10.0
        falha = avaliador.avaliar(ResultadoAcao(
            intent="IOT_CONTROL", status="timeout", alvo="lâmpada",
            executou=False, confirmado=False, texto_usuario="liga a lâmpada",
            id_solicitacao=f"falha:{indice}",
        ))
        estado = aplicar_evento_emocional(estado, falha, agora=instante[0])
    assert estado["current_emotion"] == "irritada"

    instante[0] = 130.0
    recuperacao = avaliador.avaliar(ResultadoAcao(
        intent="IOT_CONTROL", status="sucesso", alvo="lâmpada",
        executou=True, confirmado=True, texto_usuario="liga a lâmpada",
        id_solicitacao="sucesso:3",
    ))
    estado = aplicar_evento_emocional(estado, recuperacao, agora=instante[0])

    assert recuperacao["arco"] == "alivio"
    assert estado["current_emotion"] == "acalmando-se"
    assert estado["episodio_emocional"]["evidencia_ref"] == "sucesso:3"


def test_publicador_e_setter_compartilhados_preservam_prioridade_do_episodio() -> None:
    instante = time.time()
    forte = _evento(instante)
    estado = EstadoCompartilhadoRuntime(conversacional={"current_emotion": "calma"})
    publicador = EstadoContextoRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
    )
    conversa = RespostaConversacionalRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
        fallback_fala="", log=lambda *_args: None,
    )

    def publicar_e_aplicar(evento: dict) -> None:
        assert publicador.publicar_evento_emocional_causal(evento) is True
        assert estado.mental["eventos_emocionais_causais"]["atual"] == evento
        conversa.definir_emocao(evento["emocao"], evento["nivel"], evento["causa"])

    publicar_e_aplicar(forte)
    fraco = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="resultado menor confirmado",
        evidencia_ref="resultado:musica:5", natureza_evidencia="fato_observado",
        responsabilidade="sistema", confianca=0.96, relevancia=0.9,
        alvo="música", validade_s=120.0, permite_expressao=True,
        emocao="alegre", nivel=1, ts=instante,
    )
    publicar_e_aplicar(fraco)
    assert estado.conversacional["current_emotion"] == "brava"
    assert estado.conversacional["episodio_emocional"]["evidencia_ref"] == forte["evidencia_ref"]

    recuperacao = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="sucesso após falhas confirmadas",
        evidencia_ref="resultado:musica:6", natureza_evidencia="fato_observado",
        responsabilidade="sistema", confianca=0.96, relevancia=0.95,
        alvo="música", validade_s=120.0, permite_expressao=True,
        emocao="acalmando-se", nivel=1, arco="alivio", ts=instante,
    )
    publicar_e_aplicar(recuperacao)
    assert estado.conversacional["current_emotion"] == "acalmando-se"


def test_adaptador_nao_colore_fala_com_evento_publicado_mas_sem_prioridade() -> None:
    instante = time.time()
    forte = _evento(instante)
    fraco = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="resultado menor confirmado",
        evidencia_ref="resultado:musica:5", natureza_evidencia="fato_observado",
        responsabilidade="sistema", confianca=0.96, relevancia=0.9,
        alvo="música", validade_s=120.0, permite_expressao=True,
        emocao="alegre", nivel=1, ts=instante,
    )
    estado = EstadoCompartilhadoRuntime(conversacional={"current_emotion": "calma"})
    publicador = EstadoContextoRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
    )
    conversa = RespostaConversacionalRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
        fallback_fala="", log=lambda *_args: None,
    )
    assert publicador.publicar_evento_emocional_causal(forte) is True
    assert conversa.definir_emocao(forte["emocao"], forte["nivel"], forte["causa"]) is True

    class Avaliador:
        def avaliar(self, _resultado):
            return fraco

    avaliacao = avaliar_evento_emocional_operacional(
        object(), avaliador=Avaliador(),
        publicar_evento=publicador.publicar_evento_emocional_causal,
        definir_emocao=conversa.definir_emocao, log=lambda *_args: None,
    )

    assert estado.conversacional["current_emotion"] == "brava"
    assert avaliacao["permite_expressao"] is False
    assert avaliacao["motivo_expressao"] == "aplicacao_no_estado_nao_confirmada"


def test_setter_nao_confirma_evento_ausente_ou_diferente_do_publicado() -> None:
    instante = time.time()
    evento = _evento(instante)
    estado = EstadoCompartilhadoRuntime(conversacional={"current_emotion": "calma"})
    publicador = EstadoContextoRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
    )
    conversa = RespostaConversacionalRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
        fallback_fala="", log=lambda *_args: None,
    )

    assert conversa.definir_emocao(evento["emocao"], evento["nivel"], evento["causa"]) is False
    assert publicador.publicar_evento_emocional_causal(evento) is True
    assert conversa.definir_emocao(evento["emocao"], evento["nivel"], "outra causa") is False
    assert estado.conversacional["current_emotion"] == "calma"


@pytest.mark.parametrize("texto", [
    "Desculpa, repeti o pedido mesmo depois de você confirmar.",
    "Foi mal, pedi de novo sem necessidade.",
    "Me perdoa, eu insisti à toa.",
])
def test_desculpa_direta_por_repeticao_tem_funcao_compartilhada(texto: str) -> None:
    assert analisar_funcao_comunicativa(texto)["funcao"] == "pedido_desculpas"


def test_desculpa_pelo_proprio_excesso_reduz_episodio_de_repeticao() -> None:
    instante = time.time()
    evento = _evento(instante)
    estado = aplicar_evento_emocional({}, evento, agora=instante)
    funcao = analisar_funcao_comunicativa(
        "Desculpa, repeti o pedido mesmo depois de você confirmar.",
    )["funcao"]

    depois, alterou = decair_estado_emocional(
        estado, agora=instante + 1, contexto=funcao,
    )

    assert alterou is True
    assert depois["current_emotion"] == "brava"
    assert depois["emotion_level"] == 2
    assert depois["episodio_emocional"] == evento
    assert depois["emotion_interactions_left"] == 4


def test_desculpa_que_nao_reconhece_excesso_nao_atenua_causa_alheia() -> None:
    instante = time.time()
    evento = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="falha do sistema confirmada",
        evidencia_ref="resultado:iot:2", natureza_evidencia="fato_observado",
        responsabilidade="sistema", confianca=0.96, relevancia=0.95,
        alvo="lâmpada", validade_s=150.0, permite_expressao=True,
        emocao="irritada", nivel=2, arco="irritacao_compartilhada", ts=instante,
    )
    estado = aplicar_evento_emocional({}, evento, agora=instante)
    funcao = analisar_funcao_comunicativa("Desculpa, repeti o pedido.")["funcao"]
    depois, _ = decair_estado_emocional(
        estado, agora=instante + 1, contexto=funcao,
    )

    assert depois["current_emotion"] == "irritada"
    assert depois["emotion_level"] == 2


def test_desculpa_citada_por_terceiro_nao_muda_funcao_do_turno() -> None:
    assert analisar_funcao_comunicativa(
        'Ele disse "desculpa, repeti o pedido" ontem.'
    )["funcao"] != "pedido_desculpas"


def test_quatro_receipts_redundantes_e_desculpa_usam_estado_compartilhado() -> None:
    estado = EstadoCompartilhadoRuntime(conversacional={"current_emotion": "calma"})
    publicador = EstadoContextoRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
    )
    conversa = RespostaConversacionalRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
        fallback_fala="", log=lambda *_args: None,
    )
    avaliador = AvaliadorEventosEmocionaisRuntime(log=lambda *_args: None)

    for indice in range(4):
        resultado = ResultadoAcao(
            intent="APP_OPEN", status="ja_aberto_focado", alvo="Opera",
            executou=False, confirmado=True, texto_usuario="abre o Opera",
            id_solicitacao=f"opera:redundante:{indice}",
        )
        avaliacao = avaliar_evento_emocional_operacional(
            resultado, avaliador=avaliador,
            publicar_evento=publicador.publicar_evento_emocional_causal,
            definir_emocao=conversa.definir_emocao, log=lambda *_args: None,
        )
        assert avaliacao["repeticoes"] == indice + 1
        assert avaliacao["permite_expressao"] is True

    assert estado.conversacional["current_emotion"] == "brava"
    assert estado.conversacional["emotion_level"] == 3
    assert estado.conversacional["episodio_emocional"]["responsabilidade"] == "usuario"

    conversa.avancar_emocao(
        contexto=analisar_funcao_comunicativa("mostra outra coisa")["funcao"],
        interaction_key="turno:41", por_turno=True,
    )
    assert estado.conversacional["emotion_level"] == 3
    conversa.avancar_emocao(
        contexto=analisar_funcao_comunicativa("Desculpa, repeti o pedido.")["funcao"],
        interaction_key="turno:42", por_turno=True,
    )
    assert estado.conversacional["emotion_level"] == 2
    assert estado.conversacional["episodio_emocional"]["arco"] == "bronca_brincalhona"


@pytest.mark.parametrize("texto", [
    "Estou triste hoje.",
    "Estou um pouco triste hoje.",
    "Eu estou muito triste com isso.",
])
def test_tristeza_declarada_em_primeira_pessoa_pede_escuta(texto: str) -> None:
    assert analisar_funcao_comunicativa(texto)["funcao"] == "desabafo"


@pytest.mark.parametrize("texto", [
    "Ela está triste hoje.",
    "Você está triste hoje?",
    'Ele escreveu "estou triste hoje".',
])
def test_tristeza_de_terceiro_ou_citacao_nao_e_desabafo_proprio(texto: str) -> None:
    assert analisar_funcao_comunicativa(texto)["funcao"] != "desabafo"


def test_vulnerabilidade_do_usuario_interrompe_bronca_no_estado_compartilhado() -> None:
    instante = time.time()
    evento = _evento(instante)
    estado = EstadoCompartilhadoRuntime(conversacional={"current_emotion": "calma"})
    publicador = EstadoContextoRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
    )
    conversa = RespostaConversacionalRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
        fallback_fala="", log=lambda *_args: None,
    )
    assert publicador.publicar_evento_emocional_causal(evento) is True
    assert conversa.definir_emocao(evento["emocao"], evento["nivel"], evento["causa"]) is True
    conversa.avancar_emocao(
        contexto=analisar_funcao_comunicativa("Estou um pouco triste hoje.")["funcao"],
        interaction_key="turno:triste", por_turno=True,
    )

    assert estado.conversacional["current_emotion"] == "calma"
    assert estado.conversacional["episodio_emocional"] == {}


def test_refino_mental_entrega_mudanca_explicita_de_assunto_ao_decaimento() -> None:
    estado = EstadoCompartilhadoRuntime()
    contextos: list[str] = []
    contexto = EstadoContextoRuntime(
        namespace_getter=lambda: {
            "_avancar_emocao_conversacional": lambda **dados: contextos.append(
                str(dados.get("contexto") or "")
            ),
        },
        estado_runtime_getter=lambda: estado,
    )
    contexto.registrar_mente_curta = lambda *_args: None

    assert classificar_encerramento_assunto("Mudando de assunto: como está o tempo?") == "topico"
    assert classificar_encerramento_assunto("Como está o tempo?") == ""
    contexto.refinar_contexto_mental("Mudando de assunto: como está o tempo?")
    contexto.refinar_contexto_mental("Como está o tempo?")

    assert contextos == ["mudanca_assunto", "informacao"]


def test_mudanca_explicita_fecha_episodio_sem_apagar_humor_de_fundo() -> None:
    instante = time.time()
    evento = _evento(instante)
    estado = aplicar_evento_emocional({}, evento, agora=instante)

    ordinario, _ = decair_estado_emocional(
        estado, agora=instante + 1, contexto="informacao",
    )
    mudou, alterou = decair_estado_emocional(
        estado, agora=instante + 1, contexto="mudanca_assunto",
    )

    assert ordinario["current_emotion"] == "brava"
    assert mudou["current_emotion"] == "calma"
    assert mudou["episodio_emocional"] == {}
    assert mudou["humor_level"] == estado["humor_level"]
    assert alterou is True


def test_refino_com_estado_compartilhado_fecha_episodio_ao_mudar_assunto() -> None:
    instante = time.time()
    evento = _evento(instante)
    estado = EstadoCompartilhadoRuntime(conversacional={"current_emotion": "calma"})
    conversa = RespostaConversacionalRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
        fallback_fala="", log=lambda *_args: None,
    )
    contexto = EstadoContextoRuntime(
        namespace_getter=lambda: {
            "_avancar_emocao_conversacional": conversa.avancar_emocao,
        },
        estado_runtime_getter=lambda: estado,
    )
    contexto.registrar_mente_curta = lambda *_args: None
    assert contexto.publicar_evento_emocional_causal(evento) is True
    assert conversa.definir_emocao(evento["emocao"], evento["nivel"], evento["causa"]) is True

    contexto.refinar_contexto_mental("Mudando de assunto: como está o tempo?")

    assert estado.conversacional["current_emotion"] == "calma"
    assert estado.conversacional["episodio_emocional"] == {}
