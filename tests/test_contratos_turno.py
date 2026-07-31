from __future__ import annotations

from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.contratos_turno import (
    ContratoDecisaoTurno,
    ContratoRespostaTurno,
    normalizar_resposta_preparada,
)
from mente_laylay.cognicao.decisao_turno import consolidar_arbitragem


class _MemoriaFalsa:
    def salvar_aprendizados_semanticos(self, itens):
        return list(itens or [])


def test_decisao_preserva_campos_legados_adicionais() -> None:
    contrato = ContratoDecisaoTurno.de_mapping({
        "turno_id": 42,
        "modalidade": "COMANDO",
        "proprietario": "OPERACIONAL",
        "permite_acao": True,
        "confianca": "0.8764",
        "campo_legado": {"preservar": True},
    })

    dados = contrato.como_dict()

    assert dados["modalidade"] == "comando"
    assert dados["proprietario"] == "operacional"
    assert dados["confianca"] == 0.876
    assert dados["campo_legado"] == {"preservar": True}


def test_arbitragem_continua_retornando_dicionario_compativel() -> None:
    base = ContratoDecisaoTurno(
        turno_id=7,
        modalidade="comando",
        proprietario="operacional",
        permite_acao=True,
    ).como_dict()

    consolidado = consolidar_arbitragem(base, {
        "decisao": {"intent": "open_url"},
        "origem": "deterministico",
        "confianca": 0.91,
    })

    assert isinstance(consolidado, dict)
    assert consolidado["intencao"] == "OPEN_URL"
    assert consolidado["status"] == "decidida"
    assert consolidado["permite_acao"] is True


def test_resposta_tipificada_faz_copias_defensivas() -> None:
    comando = {"intent": "TESTE", "params": {"valor": 1}}
    leitura = {"relacao": "independente"}
    contrato = ContratoRespostaTurno(
        fala="  resposta completa  ",
        comandos=(comando,),
        leitura_semantica=leitura,
    )
    comando["intent"] = "ALTERADO"
    leitura["relacao"] = "alterada"

    dados = contrato.como_dict()

    assert dados["fala"] == "resposta completa"
    assert dados["comandos"][0]["intent"] == "TESTE"
    assert dados["leitura_semantica"]["relacao"] == "independente"


def test_normalizador_de_resposta_descarta_comandos_malformados() -> None:
    contrato = normalizar_resposta_preparada({
        "fala": "Oi",
        "comandos": [{"intent": "OK"}, "invalido", None],
        "aprendizados": ["um"],
    })

    assert contrato.como_dict()["comandos"] == [{"intent": "OK"}]


def test_contrato_normaliza_emocao_sem_quebrar_resposta_legada() -> None:
    contrato = normalizar_resposta_preparada({
        "fala": "Consegui!",
        "emocao": "ALEGRE",
        "nivel_emocao": 8,
    })

    assert contrato.como_dict()["emocao"] == "alegre"
    assert contrato.como_dict()["nivel_emocao"] == 3


def test_preparador_real_mantem_formato_legado_na_fronteira() -> None:
    resposta = preparar_resposta_para_execucao(
        "oi",
        '{"fala":"Oi, Pedro.","comandos":[]}',
        enviar_mensagem_cb=lambda *_args, **_kwargs: "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Tô por aqui.",
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert resposta == {
        "resposta_bruta": '{"fala":"Oi, Pedro.","comandos":[]}',
        "fala": "Oi, Pedro.",
        "comandos": [],
        "tipo_interacao": "",
        "aprendizados": [],
        "leitura_semantica": resposta["leitura_semantica"],
        "autocorrigida": False,
        "suprimir_fala": False,
    }
