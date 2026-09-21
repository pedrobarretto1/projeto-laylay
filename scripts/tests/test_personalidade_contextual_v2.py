from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.emocoes.avaliador_eventos import contextualizar_fala_evento
from mente_laylay.personalidade.antirrepeticao import (
    assinatura_fala,
    repeticao_estrutural,
)
from mente_laylay.personalidade.contingencia_natural import fala_contingencia_natural
from mente_laylay.personalidade.perfil_amizade import (
    CONTRATO_AMIZADE_COMPACTO,
    VERSAO_PERFIL_PERSONALIDADE,
)
from mente_laylay.personalidade.prompt_voz_unica import (
    BASE_SYSTEM_PROMPT,
    BASE_SYSTEM_PROMPT_RAPIDO,
)
from mente_laylay.personalidade.retrato_expressivo import (
    construir_retrato_expressivo,
)
from mente_laylay.personalidade.variacao_fala import resetar_variacoes_para_testes


def _estado(
    funcao: str = "informacao",
    *,
    mensagens: list[dict] | None = None,
    operacional: bool = False,
) -> dict:
    return {
        "messages": list(mensagens or []),
        "especialistas_turno_atual": {
            "social": {"funcao": funcao, "permite_pergunta": True},
            "operacional": {"ativo": operacional},
        },
    }


def test_prompt_rapido_e_completo_compartilham_invariantes_sociais() -> None:
    for regra in (
        "detalhe literal",
        "Humor é opcional",
        "Vulnerabilidade",
        "cria, autoriza, executa ou confirma ações",
    ):
        assert regra.casefold() in CONTRATO_AMIZADE_COMPACTO.casefold()
        assert regra.casefold() in BASE_SYSTEM_PROMPT_RAPIDO.casefold()
    assert VERSAO_PERFIL_PERSONALIDADE
    assert VERSAO_PERFIL_PERSONALIDADE in BASE_SYSTEM_PROMPT
    assert VERSAO_PERFIL_PERSONALIDADE in BASE_SYSTEM_PROMPT_RAPIDO
    assert "amiga" in BASE_SYSTEM_PROMPT.casefold()


def test_instrucao_rapida_recebe_postura_timing_e_moldes_recentes() -> None:
    estado = _estado(
        "informacao",
        mensagens=[
            {"role": "assistant", "content": "Que bom. E você, como está?"},
            {"role": "user", "content": "Você prefere rock ou metal?"},
        ],
    )
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _texto: "MEMÓRIA PRIVADA",
        formatar_playlists=lambda: "playlist privada",
        get_status_humor_prompt=lambda: "calma",
        base_system_prompt="BASE",
        estado_getter=lambda: estado,
    )

    instrucao = runtime.preparar_instrucao_rapida("Você prefere rock ou metal?")

    assert "RETRATO EXPRESSIVO EFÊMERO" in instrucao
    assert f"Perfil={VERSAO_PERFIL_PERSONALIDADE}" in instrucao
    assert "validacao_positiva" in instrucao
    assert "não cria fatos, comandos, autorização ou confirmação" in instrucao
    assert "MEMÓRIA PRIVADA" not in instrucao
    assert "playlist privada" not in instrucao


def test_antirrepeticao_reconhece_molde_sem_bloquear_resposta_diferente() -> None:
    anterior = "Que bom. E você, como está?"
    parecida = "Bom saber. E você?"
    diferente = "Prefiro rock porque ele tem mais variedade."

    assert assinatura_fala(anterior).abertura == "validacao_positiva"
    assert repeticao_estrutural(parecida, [anterior]) is True
    assert repeticao_estrutural(diferente, [anterior]) is False


def test_vulnerabilidade_suspende_deboche_no_retrato() -> None:
    retrato = construir_retrato_expressivo(
        "Hoje eu tô cansado",
        estado_mental=_estado("desabafo"),
    )

    assert retrato.sensivel is True
    assert retrato.orcamento_humor == 0
    assert retrato.estrategia_humor == "nenhum"
    assert retrato.autoriza_execucao is False


def test_brincadeira_mantem_arco_mas_turno_neutro_respeita_intervalo() -> None:
    mensagens = [
        {"role": "assistant", "content": "Minha pose sofreu um dano leve kkk."},
    ]
    brincadeira = construir_retrato_expressivo(
        "kkkk, essa foi boa",
        estado_mental=_estado("brincadeira", mensagens=mensagens),
    )
    neutro = construir_retrato_expressivo(
        "Você prefere rock ou metal?",
        estado_mental=_estado("informacao", mensagens=mensagens),
    )

    assert brincadeira.orcamento_humor == 1
    assert brincadeira.estrategia_humor == "acompanhar_brincadeira"
    assert neutro.orcamento_humor == 0
    assert "intervalo" in neutro.motivo


def test_reacao_causal_varia_sem_apagar_resultado_ou_alvo() -> None:
    resetar_variacoes_para_testes()
    evento = {
        "permite_expressao": True,
        "arco": "provocacao_afetuosa",
        "repeticoes": 1,
        "provocacao_usuario": 1,
    }
    falas = {
        contextualizar_fala_evento(
            "Opera já estava aberto e em foco.",
            evento,
            alvo="Opera",
        )
        for _ in range(3)
    }

    assert len(falas) == 3
    assert all(fala.startswith("Opera já estava aberto e em foco.") for fala in falas)
    assert all(fala.casefold().count("opera") >= 2 for fala in falas)
    assert all(len(fala.split(". ")) <= 2 for fala in falas)


def test_contingencia_social_nao_vira_bordao_em_sequencia() -> None:
    resetar_variacoes_para_testes()
    falas = {fala_contingencia_natural("obrigado lay") for _ in range(3)}

    assert len(falas) == 3
    assert all("resposta" not in fala.casefold() for fala in falas)
