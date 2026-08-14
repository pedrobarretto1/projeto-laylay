from __future__ import annotations

import mente_laylay.integracao.cliente_llm_runtime as cliente_modulo
import mente_laylay.percepcao.ambiente_sistema as ambiente_modulo
from mente_laylay.cognicao.guardiao_realidade_pessoal import (
    detectar_experiencia_pessoal_inventada,
    remover_trechos_de_realidade_inventada,
)
from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
from mente_laylay.integracao.orcamento_llm_turno import OrcamentoLLMTurnoRuntime
from mente_laylay.integracao.registro_conversa_llm import RequisicaoTransporteLLM
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.percepcao.ambiente_sistema import montar_repeticao_briefing_local
from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_llm
from mente_laylay.personalidade.perfil_amizade import IDENTIDADE_VOZ_LAYLAY


class Relogio:
    def __init__(self) -> None:
        self.agora = 100.0

    def __call__(self) -> float:
        return self.agora

    def avancar(self, segundos: float) -> None:
        self.agora += segundos


def test_fala_exata_do_terminal_nao_atribui_fadiga_ou_respiracao_a_laylay() -> None:
    fala = (
        "Porque quando digo que rock é mais leve, estou falando da sensação de ouvir "
        "música que não sobrecarrega o corpo ou a mente. Metal, por outro lado, tem "
        "energia densa, sons fortes e ritmos que exigem mais atenção — e isso me deixa "
        "cansado. A diferença é física: rock me deixa mais tranquilo, com mais espaço "
        "para respirar."
    )

    assert "fadiga_ou_respiracao_inventada" in (
        detectar_experiencia_pessoal_inventada(fala)
    )
    fala_segura = remover_trechos_de_realidade_inventada(fala)
    assert "rock" in fala_segura.casefold()
    assert "metal" not in fala_segura.casefold()
    assert "cansado" not in fala_segura.casefold()
    assert "respirar" not in fala_segura.casefold()


def test_flexao_masculina_da_laylay_e_bloqueada_sem_bloquear_citacao() -> None:
    fala = "De nada, foi bom você ter me chamado. Obrigado por escutar."

    assert detectar_experiencia_pessoal_inventada(fala) == [
        "genero_autorreferente_incoerente",
    ]
    assert remover_trechos_de_realidade_inventada(fala) == (
        "De nada, foi bom você ter me chamado."
    )
    assert detectar_experiencia_pessoal_inventada(
        "Você disse obrigado e eu entendi o agradecimento."
    ) == []
    assert detectar_experiencia_pessoal_inventada(
        "Obrigado é a forma que você usou na mensagem."
    ) == []
    assert "sempre no feminino" in IDENTIDADE_VOZ_LAYLAY


def test_preferencia_musical_sem_corpo_continua_valida() -> None:
    fala = "Prefiro rock porque as guitarras deixam a faixa mais dinâmica."

    assert detectar_experiencia_pessoal_inventada(fala) == []


def test_repeticao_do_clima_nao_diz_boituva_continua_com_limpo(monkeypatch) -> None:
    monkeypatch.setattr(ambiente_modulo.random, "choice", lambda opcoes: opcoes[-1])

    fala = montar_repeticao_briefing_local(
        "Boituva",
        "Limpo +25°C umidade:52% vento:7km/h",
    )

    assert "Boituva continua com limpo" not in fala
    assert "Em Boituva, o tempo continua limpo, com 25 graus Celsius" in fala


def test_autoria_sem_fatia_minima_nao_inicia_http_nem_degrada_cliente(
    monkeypatch,
) -> None:
    relogio = Relogio()
    orcamento = OrcamentoLLMTurnoRuntime(monotonic=relogio)
    orcamento.iniciar_turno("turno-autoria", classe="rapida")
    relogio.avancar(6.2)  # restam 1,8 s: insuficiente para uma autoria secundária
    chamadas_http: list[bool] = []
    falhas: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        cliente_modulo,
        "executar_chat_llm",
        lambda *_args, **_kwargs: chamadas_http.append(True) or "não deveria chegar aqui",
    )
    cliente = ClienteLLMRuntime(
        endpoint_local_getter=lambda: True,
        post_chat=lambda *_args, **_kwargs: None,
        registrar_falha=lambda *args, **_kwargs: falhas.append(args),
        orcamento_turno=orcamento,
        log=lambda *_args: None,
    )

    resposta = cliente.executar(RequisicaoTransporteLLM(
        payload={"messages": [{"role": "user", "content": "contrato"}]},
        timeout=8,
        prioridade_interativa=True,
        permitir_durante_interacao=True,
        tipo_chamada="autoria_operacional",
        classe_timeout="rapida",
    ))

    assert resposta.rota == "orcamento_bloqueado"
    assert chamadas_http == []
    assert falhas == []
    assert cliente.diagnostico()["estado"] == "saudavel"
    assert cliente.diagnostico()["falhas"] == 0
    assert orcamento.diagnostico()["bloqueios_por_motivo"] == {
        "fatia_secundaria_insuficiente": 1,
    }


def test_confirmacao_preserva_fala_local_quando_autoria_deveria_ser_pulada(
    monkeypatch,
) -> None:
    relogio = Relogio()
    orcamento = OrcamentoLLMTurnoRuntime(monotonic=relogio)
    orcamento.iniciar_turno("turno-confirmacao", classe="rapida")
    relogio.avancar(6.5)
    chamadas_http: list[bool] = []
    monkeypatch.setattr(
        cliente_modulo,
        "executar_chat_llm",
        lambda *_args, **_kwargs: chamadas_http.append(True) or "não deveria chegar aqui",
    )
    cliente = ClienteLLMRuntime(
        endpoint_local_getter=lambda: True,
        post_chat=lambda *_args, **_kwargs: None,
        orcamento_turno=orcamento,
        log=lambda *_args: None,
    )

    def enviar(mensagens, **opcoes):
        return cliente.executar(RequisicaoTransporteLLM(
            payload={"messages": mensagens, "max_tokens": opcoes.get("max_tokens", 120)},
            timeout=opcoes.get("timeout"),
            prioridade_interativa=bool(opcoes.get("_prioridade_interativa")),
            permitir_durante_interacao=bool(opcoes.get("_permitir_durante_interacao")),
            tipo_chamada=str(opcoes.get("_tipo_chamada") or "principal"),
            classe_timeout=str(opcoes.get("_classe_timeout") or "normal"),
        )).texto

    fala_segura = "A lâmpada do quarto não respondeu agora."
    confirmacao = personalizar_confirmacao_llm(
        ResultadoAcao(
            intent="IOT_CONTROL",
            status="indisponivel",
            alvo="lampada_quarto",
            executou=False,
            confirmado=False,
        ),
        fala_segura,
        classe="falha",
        emocao="calma",
        nivel=1,
        enviar_mensagem=enviar,
    )

    assert confirmacao.fala == fala_segura
    assert confirmacao.usada_llm is False
    assert confirmacao.motivo_fallback == "resposta_tecnica_ou_json_invalido"
    assert chamadas_http == []
    assert cliente.diagnostico()["estado"] == "saudavel"
