from __future__ import annotations

import threading
import time

import mente_laylay.autonomia.coordenador_intencao as coordenador_mod
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.cognicao.linguagem_aprendida import LinguagemAprendidaRuntime
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from mente_laylay.memoria_mental.diagnostico_mente import (
    DiagnosticoMenteRuntime,
    construir_diagnostico_mente,
    formatar_diagnostico_terminal,
)
from mente_laylay.memoria_mental.observabilidade import ObservabilidadeMenteRuntime
from mente_laylay.personalidade.voz_runtime import VozRuntime


def _estado_base(mental=None, continuidades=None):
    return {
        "mental": dict(mental or {}),
        "conversacional": {},
        "percepcao": {},
        "continuidades": dict(continuidades or {}),
    }


def test_saude_llm_contadores_e_falha_recente_concordam() -> None:
    runtime = DiagnosticoMenteRuntime(
        estado_getter=lambda: _estado_base(),
        saude_getter=lambda: {"llm": {"status": "saudavel"}},
        conversa_llm_getter=lambda: {
            "modelo_disponivel": True,
            "estado": "degradado",
            "falhas": 2,
            "falhas_consecutivas": 2,
            "ultima_falha_codigo": "timeout_resposta",
        },
        falar=lambda *_args: None,
    )

    diagnostico = runtime.snapshot()

    assert diagnostico["saude"]["degradado"] == 1
    assert diagnostico["saude"]["saudavel"] == 0
    assert diagnostico["falhas_recentes"][-1]["codigo"] == "timeout_resposta"
    assert "falhas técnicas recentes: 1" in formatar_diagnostico_terminal(diagnostico)


def test_pendencia_expoe_origem_acao_idade_prazo_e_motivo_sem_conteudo() -> None:
    agora = time.time()
    diagnostico = construir_diagnostico_mente(
        _estado_base(mental={
            "pendencia_acao_canonica": {
                "status": "ativa",
                "origem": "clipboard",
                "acao": "resumir_texto",
                "criada_em": agora - 12,
                "expira_em": agora + 48,
                "motivo": "aguardando_resposta",
                "metadados": {"conteudo": "segredo absoluto"},
            },
        }),
        {},
    )

    item = diagnostico["pendencias_detalhadas"][0]
    assert item["origem"] == "clipboard"
    assert item["acao"] == "resumir_texto"
    assert 11 <= item["idade_s"] <= 13
    assert 47 <= item["prazo_s"] <= 49
    assert item["motivo"] == "aguardando_resposta"
    assert "segredo absoluto" not in repr(diagnostico)


def test_servicos_distinguem_ativo_desativado_encerrado_e_degradado() -> None:
    diagnostico = construir_diagnostico_mente(
        _estado_base(mental={
            "diagnostico_servicos": {
                "agenda": {"estado": "ativo"},
                "ouvido": {"estado": "desativado"},
                "worker": {"estado": "encerrado"},
                "llm": {"estado": "queda"},
            },
        }),
        {},
    )
    classes = {
        item["nome"]: item["classe_estado"]
        for item in diagnostico["servicos_background"]
    }

    assert classes == {
        "agenda": "ativos",
        "llm": "degradados",
        "ouvido": "desativados",
        "worker": "encerrados",
    }
    texto = formatar_diagnostico_terminal(diagnostico)
    assert "ativos=1 degradados=1" in texto
    assert "desativados=1 encerrados=1" in texto


def test_ultima_acao_usa_um_unico_contrato_atomico() -> None:
    diagnostico = construir_diagnostico_mente(
        _estado_base(mental={
            "ultima_acao_intent": "IOT_CONTROL",
            "ultima_acao_alvo": "lampada_quarto",
            "ultima_acao_status": "ligado",
            "ultima_acao_contrato": {
                "id_solicitacao": "evt-42",
                "intent": "APP_OPEN",
                "alvo": "opera",
                "status": "ja_aberto_focado",
                "dominio": "app",
                "confirmado": True,
            },
        }),
        {},
    )

    assert diagnostico["ultima_acao"] == {
        "intent": "APP_OPEN",
        "alvo": "opera",
        "status": "ja_aberto_focado",
        "confirmado": True,
    }
    assert diagnostico["ultima_acao_auditoria"] == {
        "id_evento": "evt-42",
        "dominio": "app",
        "fonte": "contrato_atomico",
        "coerente": True,
    }


def test_orcamento_prompt_fecha_preparacao_e_transporte() -> None:
    estado = {}
    observabilidade = ObservabilidadeMenteRuntime(
        estado_getter=lambda chave, padrao=None: estado.get(chave, padrao),
        estado_setter=lambda **campos: estado.update(campos),
    )
    mensagens = [
        {"role": "system", "content": "s" * 100},
        *({"role": "user", "content": str(indice) * 80} for indice in range(14)),
    ]

    preparar_payload_llm(
        mensagens,
        model="teste",
        registrar_orcamento_prompt=observabilidade.registrar_orcamento_prompt,
    )
    observabilidade.registrar_orcamento_prompt(
        etapa="transporte",
        brutos=500,
        selecionados=320,
        truncados=180,
        injetados=0,
        enviados=320,
    )

    etapas = estado["diagnostico_orcamento_prompt"]["etapas"]
    assert etapas["preparacao"]["fecha_selecao"] is True
    assert etapas["preparacao"]["fecha_envio"] is True
    assert etapas["preparacao"]["truncados"] > 0
    assert etapas["transporte"]["fecha_selecao"] is True
    assert etapas["transporte"]["fecha_envio"] is True


class _MemoriaVazia:
    def listar_aprendizados_semanticos(self, **_kwargs):
        return []


def test_normalizacao_identica_e_reutilizada_uma_vez_por_turno() -> None:
    turno = ["turno-1"]
    runtime = LinguagemAprendidaRuntime(
        memoria_sqlite=_MemoriaVazia(),
        normalizar_texto=lambda texto: str(texto).casefold(),
        texto_social_curto=lambda _texto: False,
        falar=lambda *_args: None,
        turno_id_getter=lambda: turno[0],
    )

    assert runtime.normalizar_com_apelidos("Colcoa a música") == "coloca a música"
    assert runtime.normalizar_com_apelidos("Colcoa a música") == "coloca a música"
    diagnostico = runtime.diagnostico_tolerancia_portugues()
    assert diagnostico["normalizacoes"] == 2
    assert diagnostico["normalizacoes_unicas_turno"] == 1
    assert diagnostico["reaplicacoes_identicas"] == 1


class _ContextoNatural:
    def montar(self):
        return {
            "turno_atual": {"id": "turno-1"},
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "texto_parece_consulta_operacional": lambda _texto: True,
        }


def test_intencao_nao_resolvida_registra_motivo_sem_texto_privado(monkeypatch) -> None:
    monkeypatch.setattr(
        coordenador_mod,
        "resolver_intencao",
        lambda _texto, _origem, _contexto: (None, "catalogo_sem_match"),
    )
    runtime = CicloComandosRuntime(
        namespace_getter=lambda: {
            "_texto_parece_consulta_operacional": lambda _texto: True,
            "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        },
        contexto_intencao_runtime=_ContextoNatural(),
        log=lambda *_args: None,
    )

    runtime.resolver_comando_natural("abra o segredo privado", "chat")
    diagnostico = runtime.diagnostico_linguagem_natural()

    assert diagnostico["ultima_nao_resolvida"] == {
        "motivo": "nenhuma_habilidade_atingiu_confianca",
        "moldura": "fala_natural",
        "rota": "catalogo_sem_match",
        "parecia_operacional": True,
    }
    assert "segredo privado" not in repr(diagnostico)


class _Stream:
    active = False


class _Som:
    def play(self, *_args, **_kwargs):
        return None

    def get_stream(self):
        return _Stream()

    def stop(self):
        return None


class _ArquivoSom:
    def read(self, _caminho):
        return [0.0], 16000


def test_voz_separa_fila_sintese_reproducao_e_bloqueio_externo() -> None:
    metricas = []
    runtime = VozRuntime(
        fallback_fala="fallback",
        voice="voz",
        edge_tts_mod=None,
        sounddevice_mod=_Som(),
        soundfile_mod=_ArquivoSom(),
        pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("", "", ""),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        interrupt_event=threading.Event(),
        registrar_metrica_cb=lambda *args: metricas.append(args),
        log=lambda *_args: None,
    )
    runtime._sintetizar_edge = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    runtime._selecionar_saida_audio = lambda: None  # type: ignore[method-assign]

    runtime.reproduzir_fala("teste", "calma", 1)

    runtime.fila.put({
        "texto": "na fila",
        "emocao": "calma",
        "nivel": 1,
        "dinamizar": False,
        "enfileirado_monotonic": time.monotonic() - 0.01,
    })

    def _reproduzir_da_fila(*_args):
        runtime.stop_event.set()

    runtime.reproduzir_fala = _reproduzir_da_fila  # type: ignore[method-assign]
    runtime.worker_de_falas()

    nomes = {item[0] for item in metricas}
    assert {
        "tts_fila", "tts_sintese", "tts_bloqueio_externo",
        "tts_reproducao", "tts_total",
    } <= nomes
