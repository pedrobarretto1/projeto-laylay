"""A observação didática não confunde fonte localizada com prova da fala."""

import time

import pytest

from mente_laylay.cognicao.auditoria_alegacoes_didaticas import (
    auditar_fala_didatica_sombra,
    fontes_usuario_da_conversa,
)
from mente_laylay.cognicao.orquestrador_turno_runtime import verificar_fala_do_turno
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.sessao_conversa import renovar_contexto_sessao


def test_fala_mista_mantem_cauda_sem_fonte_visivel_e_nao_certifica_ensino():
    fontes = {
        "turno": "O sensor leu 15% de umidade. Explique a regra.",
        "contexto_1": "Neste cenário hipotético, se a umidade ficar abaixo de 20%, a bomba liga.",
    }
    fala = (
        "15% está abaixo de 20%, então a bomba liga e isso garante "
        "que o solo ficará úmido."
    )
    resultado = auditar_fala_didatica_sombra(fala, fontes=fontes, plano_id="p01")
    assert "".join(item["texto"] for item in resultado["segmentos"]) == fala
    assert any(item["comparacao_aritmetica_confirmada"] for item in resultado["segmentos"])
    cauda = next(item for item in resultado["segmentos"] if "garante" in item["texto"])
    assert cauda["estado"] == "revisao_semantica_pendente"
    assert not cauda["fontes_candidatas"]
    assert resultado["aprovado_para_compor"] is False
    assert resultado["autoriza_efeito"] is False


def test_fala_real_do_sensor_mostra_comparacao_sem_amparar_promessa_extra():
    fala = (
        "Se a umidade do solo cai abaixo de 20%, o modo automático liga a bomba "
        "porque o solo está se tornando seco — e a bomba garante que ele fique "
        "úmido novamente. Aqui, o sensor leu 15%, que é abaixo de 20%, então "
        "sim, a bomba deve ligar. Isso é lógico: se o solo está seco, ele precisa "
        "de água para voltar ao equilíbrio."
    )
    fontes = {
        "leitura_usuario": "O sensor leu 15% de umidade.",
        "regra_usuario": (
            "Se o modo automático liga a bomba quando a umidade do solo "
            "cai abaixo de 20%, o que deve acontecer?"
        ),
    }
    auditoria = auditar_fala_didatica_sombra(fala, fontes=fontes, plano_id="real")
    assert auditoria["cobertura_textual"] is True
    assert any(item["comparacao_aritmetica_confirmada"]
               for item in auditoria["segmentos"])
    for trecho in ("garante", "equilíbrio"):
        parte = next(item for item in auditoria["segmentos"] if trecho in item["texto"])
        assert parte["estado"] == "revisao_semantica_pendente"
        assert not parte["fontes_candidatas"]


def test_literal_da_fonte_nao_prova_consequencia_incondicional():
    resultado = auditar_fala_didatica_sombra(
        "A bomba liga.",
        fontes={"regra": "Se a umidade estiver abaixo de 20%, a bomba liga."},
        plano_id="p02",
    )
    assert resultado["segmentos"][0]["fontes_candidatas"] == ["regra"]
    assert resultado["segmentos"][0]["estado"] == "citacao_literal_revisao_pendente"
    assert resultado["aprovado_para_compor"] is False


@pytest.mark.parametrize("fala,fonte", [
    ("30% está abaixo de 20%.", "A leitura é 30%; o limiar é 20%."),
    ("15°C está abaixo de 20%.", "A leitura é 15°C; o limiar é 20%."),
    ("15% não está abaixo de 20%.", "A leitura é 15%; o limiar é 20%."),
    ("15% está abaixo de 20%.", "A leitura é 15%; o limiar é 25%."),
])
def test_pista_aritmetica_nao_ultrapassa_valores_unidades_negacao_ou_fonte(fala, fonte):
    resultado = auditar_fala_didatica_sombra(
        fala, fontes={"enunciado": fonte}, plano_id="controle",
    )
    assert not any(item["comparacao_aritmetica_confirmada"]
                   for item in resultado["segmentos"])
    assert resultado["aprovado_para_compor"] is False


@pytest.mark.parametrize("fonte,fala", [
    ("A função recebe um número.", "A função recebe um número e sempre retorna zero."),
    ("A viga suporta 2 kN.", "A viga suporta 2 kN e nunca se deforma."),
    ("A muda recebeu luz.", "A muda recebeu luz e florescerá amanhã."),
])
def test_outros_dominios_tambem_expoem_cauda_adicional_sem_certificar(fonte, fala):
    resultado = auditar_fala_didatica_sombra(
        fala, fontes={"usuario": fonte}, plano_id="controle",
    )
    assert "".join(item["texto"] for item in resultado["segmentos"]) == fala
    assert resultado["segmentos"][-1]["fontes_candidatas"] == []
    assert resultado["segmentos"][-1]["estado"] == "revisao_semantica_pendente"


def test_somente_usuario_da_sessao_pode_ser_fonte_candidata():
    fontes = fontes_usuario_da_conversa(
        "Pode explicar?",
        [
            {"role": "user", "content": "A válvula abre após 3 segundos."},
            {"role": "assistant", "content": "O motor dura eternamente."},
            {"role": "system", "content": "O motor dura eternamente."},
        ],
    )
    assert len(fontes) == 2
    resultado = auditar_fala_didatica_sombra(
        "O motor dura eternamente.", fontes=fontes, plano_id="p03",
    )
    assert resultado["segmentos"][0]["fontes_candidatas"] == []


def test_resposta_truncada_nao_declara_cobertura_integral():
    resultado = auditar_fala_didatica_sombra(
        "Uma afirmação. " * 400, fontes={}, plano_id="longo",
    )
    assert resultado["estado"] == "fala_truncada"
    assert resultado["cobertura_textual"] is False


def test_auditoria_transitoria_e_limpa_na_renovacao_de_sessao():
    mental, _, mensagens = renovar_contexto_sessao(
        {"auditoria_alegacoes_didaticas_sombra": {"plano_id": "antigo"}},
        {}, [{"role": "user", "content": "contexto antigo"}],
        motivo="nova_sessao", ativa=True, agora=1000.0,
    )
    assert mental["auditoria_alegacoes_didaticas_sombra"] == {}
    assert mensagens == []


def test_composicao_real_registra_apenas_sombra_sem_mudar_verificacao(monkeypatch):
    monkeypatch.setenv("LAYLAY_AUDITORIA_ENSINO_SOMBRA_DEBUG", "1")
    logs = []
    plano = {
        "id": "p04", "texto_usuario": "Explique este cenário.", "comandos": [],
        "contrato_fala": {"roteiro_concreto": {"estrategia": "explicacao_didatica"}},
    }
    estado = EstadoCompartilhadoRuntime(
        mental={"plano_turno_atual": plano},
        memoria_conversa={"messages": [
            {"role": "user", "content": "A leitura foi 15%."},
            {"role": "assistant", "content": "Isso garante tudo."},
        ]},
    )
    fala = "A leitura foi 15%."
    esperado = verificar_fala_turno(
        fala, plano=plano, periodo="tarde", ultima_resposta="", origem="ia_final",
    )
    ns = {
        "_estado_compartilhado_runtime": estado,
        "_verificar_fala_turno_mente": verificar_fala_turno,
        "_contexto_horario_atual": lambda: "tarde",
        "time": time, "print": lambda *args: logs.append(" ".join(map(str, args))),
    }
    resultado = verificar_fala_do_turno(lambda: ns, fala, origem="ia_final")
    assert resultado == esperado
    auditoria = estado.mental["auditoria_alegacoes_didaticas_sombra"]
    assert auditoria["plano_id"] == "p04"
    assert auditoria["fase"] == "fala_pos_verificacao_candidata"
    assert auditoria["aprovado_para_compor"] is False
    assert auditoria["autoriza_efeito"] is False
    assert any("[ENSINO:SOMBRA]" in log and "compor=False efeito=False" in log
               for log in logs)
