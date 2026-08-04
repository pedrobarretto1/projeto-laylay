from __future__ import annotations

import threading

from mente_laylay.memoria_mental.contexto_compartilhado import (
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.diagnostico_mente import construir_diagnostico_mente
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.percepcao.observador_area_transferencia import (
    oferta_deve_ceder_a_novo_comando,
)
from mente_laylay.personalidade.orquestrador_fala_runtime import (
    OrquestradorFalaRuntime,
)
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao


def test_resultado_atomico_nao_herda_alvo_de_outro_dominio() -> None:
    mente = registrar_resultado_execucao(
        {},
        ResultadoAcao(
            intent="CANCELAR_AGENDAMENTO",
            alvo="beber agua",
            status="agendamento_cancelado",
            executou=True,
            confirmado=True,
        ),
        "cancela o lembrete de beber agua",
        True,
    )
    mente = registrar_resultado_execucao(
        mente,
        ResultadoAcao(
            intent="EMAIL_READ",
            alvo="",
            status="emails_lidos",
            executou=True,
            confirmado=True,
        ),
        "quais emails novos eu tenho",
        True,
    )

    contrato = mente["ultima_acao_contrato"]
    diagnostico = construir_diagnostico_mente(
        {
            "mental": mente,
            "conversacional": {},
            "percepcao": {},
            "continuidades": {},
        },
        {},
    )

    assert contrato == {
        "id_solicitacao": "",
        "intent": "EMAIL_READ",
        "alvo": "",
        "status": "emails_lidos",
        "dominio": "email",
        "executou": True,
        "confirmado": True,
        "origem": "",
        "evidencia_confirmacao": "as mensagens são recuperadas do serviço",
    }
    assert diagnostico["ultima_acao"] == {
        "intent": "EMAIL_READ",
        "alvo": "",
        "status": "emails_lidos",
        "confirmado": True,
    }


def test_cancelamento_confirmado_e_desfecho_valido_sem_prefixo_de_falha() -> None:
    plano = planejar_resposta_acao(
        ResultadoAcao(
            intent="CANCEL_DELETE_ITEM",
            alvo="teste governanca.txt",
            status="exclusao_cancelada",
            executou=False,
            confirmado=False,
            texto_usuario="não, deixa como está",
        ),
        "Certo, cancelei. Não mexi no arquivo.",
    )

    assert plano.classe == "cancelado"
    assert "cancelei" in plano.fala.casefold()
    assert "não consegui" not in plano.fala.casefold()


def test_oferta_opcional_cede_a_pergunta_nova_sem_consumir_o_turno() -> None:
    assert oferta_deve_ceder_a_novo_comando(
        "o que voce sabe sobre mim?",
        "resumir_texto",
        texto_tem_comando_explicito=lambda _texto: False,
    ) is True
    assert oferta_deve_ceder_a_novo_comando(
        "quem é Nanda?",
        "explicar_codigo",
        texto_tem_comando_explicito=lambda _texto: False,
    ) is True
    assert oferta_deve_ceder_a_novo_comando(
        "seria ótimo",
        "investigar_erro",
        texto_tem_comando_explicito=lambda _texto: False,
    ) is False


class _Estado:
    def __init__(self) -> None:
        self.mental = {
            "turno_atual": {"id": "p14"},
            "plano_turno_atual": {
                "id": "p14",
                "fase": "planejado",
                "requer_execucao": True,
                "texto_usuario": "liga a luz",
            },
        }

    def substituir(self, dominio: str, valor: dict) -> None:
        assert dominio == "mental"
        self.mental = dict(valor)


class _Voz:
    def __init__(self) -> None:
        self.falas: list[str] = []

    def falar(self, fala: str, *_args, **_kwargs) -> bool:
        self.falas.append(fala)
        return True


def test_sentinela_tecnica_e_absorvida_na_fronteira_final_de_fala() -> None:
    estado = _Estado()
    voz = _Voz()
    runtime = OrquestradorFalaRuntime(servicos_iniciais={
        "_registrar_mente_curta": lambda *_args, **_kwargs: None,
        "_estado_compartilhado_runtime": estado,
        "_encerrar_topico_mente": lambda mental, conversa, **_kwargs: (mental, conversa),
        "salvar_memoria": lambda: None,
        "print": lambda *_args: None,
        "_dirigir_fala_mente": lambda fala, **kwargs: {
            "fala": fala,
            "emocao": kwargs.get("emocao") or "calma",
            "nivel": kwargs.get("nivel") or 1,
        },
        "_voz_runtime": voz,
        "_registrar_continuidade_da_fala_mente": lambda mental, *_args, **_kwargs: mental,
        "_threading": threading,
        "_agendar_fala_proativa": lambda *_args, **_kwargs: False,
    })

    assert runtime.falar("LAYLAYLLMINDISPONIVEL") is True
    assert len(voz.falas) == 1
    assert "LAYLAYLLM" not in voz.falas[0].upper()
    assert "erro técnico" not in voz.falas[0].casefold()
