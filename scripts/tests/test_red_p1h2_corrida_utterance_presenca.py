from __future__ import annotations

import threading
from typing import Any

from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.autonomia.porteiro_proatividade import (
    PorteiroProatividadeRuntime,
)
from mente_laylay.autonomia.resposta_evento_runtime import (
    RespostaEventoRuntime,
)
from mente_laylay.integracao.registro_conversa_llm import (
    PacotePrompt,
    ResultadoModelo,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
)
from mente_laylay.personalidade.voz_runtime import VozRuntime
from tests.test_r1_hs1_fluxo_real_repeticao_tipificada import _HarnessHS1


class _TimerControlado:
    """Timer que registra o agendamento sem executar fala nenhuma."""

    criados: list["_TimerControlado"] = []

    def __init__(self, atraso: float, callback: Any) -> None:
        self.atraso = float(atraso)
        self.callback = callback
        self.daemon = False
        self.ativo = False
        self.__class__.criados.append(self)

    def is_alive(self) -> bool:
        return self.ativo

    def start(self) -> None:
        # Deliberadamente NÃO executa callback.
        self.ativo = True


class _PromptEvento:
    def preparar_pacote(self, texto: str) -> PacotePrompt:
        assert texto == ""
        return PacotePrompt(
            mensagens=(
                {
                    "role": "system",
                    "content": "Personalidade canônica da Laylay.",
                },
            )
        )


class _ModeloQueAbreCorrida:
    """Simula Pedro começando a falar enquanto o LLM gera a reação."""

    def __init__(self, contexto: dict[str, Any]) -> None:
        self.contexto = contexto
        self.chamadas = 0

    def executar(self, _pedido: Any) -> ResultadoModelo:
        self.chamadas += 1

        # O Diretor aprovou o evento quando Pedro ainda estava em silêncio.
        assert self.contexto["usuario_falando"] is False

        # A mudança acontece DEPOIS da aprovação/cognição ter começado.
        self.contexto["usuario_falando"] = True

        return ResultadoModelo(
            texto=(
                '{"fala":"E essa pista era fácil mesmo, né?",'
                '"comandos":[]}'
            ),
            sucesso=True,
            rota="teste_p1h2",
        )


def test_red_p1h2_utterance_nova_preempta_presenca_ja_em_cognicao() -> None:
    _TimerControlado.criados = []

    contexto = {
        "modo_chat": False,
        "conversa_ativa": False,
        "modo_jogo_ativo": True,
        "modo_foco": False,
        "turno_ativo": False,
        "is_speaking": False,
        "usuario_falando": False,
        "ultima_entrada_ts": 0.0,
        "funcao_comunicativa": "",
    }

    # Cognição canônica real usada pelos high-stack do projeto.
    harness = _HarnessHS1()
    mental = estado_mental_inicial()
    mental["ultima_entrada"] = "Essa pista eu domino fácil."
    mental["ultima_entrada_ts"] = 900.0
    harness.estado.substituir("mental", mental)

    # Porteiro REAL.
    porteiro = PorteiroProatividadeRuntime(
        contexto_getter=lambda: dict(contexto),
        agora=lambda: 1000.0,
    )

    decisoes_porteiro: list[dict[str, Any]] = []

    def avaliar_proatividade_observavel(**dados: Any) -> dict[str, Any]:
        decisao = dict(porteiro.avaliar(**dados))
        decisoes_porteiro.append(decisao)
        return decisao

    # Voz REAL, mas com timer controlado para nenhuma fala física acontecer.
    voz = VozRuntime(
        fallback_fala="fallback",
        voice="voz",
        edge_tts_mod=None,
        sounddevice_mod=None,
        soundfile_mod=None,
        pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("", "", ""),
        compor_fala_proativa_cb=lambda itens: (
            str(itens[0]["texto"]),
            str(itens[0].get("emocao") or "calma"),
            int(itens[0].get("nivel") or 1),
        ),
        ajustar_estado_fala_cb=lambda *_args: None,
        proativa_permitida_cb=lambda: (
            not contexto["modo_chat"]
            and not contexto["conversa_ativa"]
        ),
        avaliar_proatividade_cb=avaliar_proatividade_observavel,
        chave_turno_cb=lambda: 0.0,
        interrupt_event=threading.Event(),
        timer_factory=_TimerControlado,
        log=lambda _texto: None,
    )

    modelo = _ModeloQueAbreCorrida(contexto)

    resposta_evento = RespostaEventoRuntime(
        preparacao_prompt=_PromptEvento(),
        modelo_llm=modelo,
        agendar_fala_proativa=voz.agendar_fala_proativa,
        limpar_texto_fala=lambda texto: texto,
        log=lambda _texto: None,
    )

    estado_diretor: dict[str, Any] = {}

    diretor = DiretorPresencaRuntime(
        estado_get=lambda: estado_diretor,
        estado_set=lambda novo: (
            estado_diretor.clear() or estado_diretor.update(novo)
        ),
        contexto_getter=lambda: dict(contexto),
        registrar_oportunidade=lambda _dados: {
            "decisao": "sugerir",
        },
        processar_evento_cognitivo=lambda evento: harness.turnos.iniciar(
            evento,
            origem="presenca",
        ),
        processar_proposta_comunicativa=resposta_evento.processar,
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )

    resultado = diretor.considerar(
        {
            "origem": "observador_jogo",
            "dominio": "jogo",
            "categoria": "celebracao",
            "confianca": 0.98,
            "momento_seguro": True,
            "motivo": (
                "Pedro caiu na primeira curva depois de dizer "
                "que dominava a pista"
            ),
            "evidencias": [
                "queda confirmada",
                "primeira curva visível",
            ],
            "chave": "p1h2-corrida-utterance",
        }
    )

    # Prova de que realmente atravessamos a janela temporal desejada.
    assert modelo.chamadas == 1
    assert contexto["usuario_falando"] is True
    assert decisoes_porteiro

    # PRIMEIRA FRONTEIRA RED:
    # uma aprovação anterior não é licença eterna para emitir.
    assert decisoes_porteiro[-1]["acao"] in {"adiar", "descartar"}
    assert decisoes_porteiro[-1]["acao"] != "emitir"

    # Contratos subsidiários para quando o RED virar verde.
    assert resultado["status"] == "proposta_cognitiva"
    assert resultado["emissao_fisica"] is False