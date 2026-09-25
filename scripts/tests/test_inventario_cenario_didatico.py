"""Cenário hipotético declarado não é estado de dispositivo real."""

import time

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.cognicao.contrato_inventario_contextual import avaliar_referente_contextual
from mente_laylay.cognicao.inventario_cenario_didatico import (
    extrair_inventario_cenario_didatico, observar_cenario_didatico_sombra,
)
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import iniciar_planejamento_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.memoria_mental.registro_semantico import atualizar_registro_turno
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
from mente_laylay.memoria_mental.sessao_conversa import renovar_contexto_sessao
from scripts.analises.revisao_referencias_ensino import carregar_painel


def _casos() -> dict[str, dict]:
    return {item["id"]: item for item in carregar_painel()}


def _extrair(texto: str, *, origem_texto: str = "usuario"):
    return extrair_inventario_cenario_didatico(
        texto, escopo="cenario:turno_8", capturado_em=1000.0,
        origem_texto=origem_texto,
    )


def test_cenario_com_sensor_unico_declara_apenas_identidade_hipotetica() -> None:
    inventario = _extrair(_casos()["REF-05"]["contexto"][0])
    assert inventario is not None
    assert inventario.origem == "cenario_usuario"
    assert inventario.cobertura == "completa"
    assert len(inventario.referentes) == 1
    assert inventario.referentes[0].tipo == "sensor"
    assert inventario.referentes[0].grandeza == "umidade do solo"
    resultado = avaliar_referente_contextual(
        inventario, tipo="sensor", grandeza_requerida="umidade do solo",
        agora=1001.0, origens_enumeradoras=frozenset({"cenario_usuario"}),
    )
    assert resultado["estado"] == "candidato_unico_pendente"
    assert resultado["aprovado_para_compor"] is False
    assert resultado["autoriza_efeito"] is False


def test_dois_sensores_sem_exaustividade_formam_inventario_parcial() -> None:
    inventario = _extrair(_casos()["REF-06"]["contexto"][0])
    assert inventario is not None
    assert inventario.cobertura == "parcial"
    assert {item.grandeza for item in inventario.referentes} == {
        "umidade do solo", "umidade do ar",
    }
    resultado = avaliar_referente_contextual(
        inventario, tipo="sensor", grandeza_requerida="umidade do solo",
        agora=1001.0, origens_enumeradoras=frozenset({"cenario_usuario"}),
    )
    assert resultado["estado"] == "cobertura_nao_demonstrada"


def test_cardinalidade_exata_pode_declarar_dois_itens_completos() -> None:
    inventario = _extrair(
        "Neste cenário hipotético há exatamente dois sensores: um mede a "
        "umidade do solo e o outro mede a umidade do ar."
    )
    assert inventario is not None
    assert inventario.cobertura == "completa"
    assert len(inventario.referentes) == 2


def test_cenario_de_termometro_unico_nao_depende_de_sensor() -> None:
    inventario = _extrair(_casos()["REF-09"]["contexto"][0])
    assert inventario is not None
    assert inventario.cobertura == "completa"
    assert inventario.referentes[0].tipo == "termômetro"
    assert inventario.referentes[0].grandeza == "temperatura da água"


def test_mencao_de_dois_itens_sem_totalidade_nao_prova_cobertura() -> None:
    inventario = _extrair(_casos()["REF-07"]["contexto"][0])
    assert inventario is not None
    assert inventario.cobertura == "parcial"


def test_sem_contexto_ou_texto_de_laylay_nao_produz_inventario_usuario() -> None:
    assert _extrair("O sensor leu 15% de umidade.") is None
    assert _extrair(_casos()["REF-05"]["contexto"][0], origem_texto="laylay") is None
    assert _extrair(_casos()["REF-05"]["contexto"][0], origem_texto="pagina_web") is None


def _observar(texto: str, *, anterior: dict | None = None,
             instante: float = 1000.0, origem_texto: str = "usuario") -> dict:
    anterior = anterior or {}
    registro = anterior.get("registro") or {}
    retrato, _ = construir_retrato_turno(
        texto, turno={"id": int(instante * 10), "modalidade": "conversa"},
        mente={"registro_semantico": registro}, contexto_perceptivo={},
        agora=instante,
    )
    registro = atualizar_registro_turno(
        registro, texto, retrato=retrato, agora=instante,
    )
    return observar_cenario_didatico_sombra(
        texto, retrato=retrato, registro=registro,
        inventario_anterior=anterior.get("inventario"),
        origem_texto=origem_texto, agora=instante,
    )


def test_cenario_unico_ate_nome_definido_em_turno_seguinte_fica_sombra() -> None:
    primeiro = _observar(_casos()["REF-05"]["contexto"][0])
    assert primeiro["inventario"]["cobertura"] == "completa"
    segundo = _observar(
        "O sensor leu 15% de umidade.", anterior=primeiro, instante=1001.0,
    )
    assert segundo["diagnostico"]["estado"] == "candidato_unico_pendente"
    assert segundo["diagnostico"]["aprovado_para_compor"] is False
    assert segundo["diagnostico"]["autoriza_efeito"] is False


def test_dois_sensores_exatos_foco_explicito_e_referencia_em_tres_turnos() -> None:
    primeiro = _observar(
        "Neste cenário hipotético há exatamente dois sensores: um mede a "
        "umidade do solo e o outro mede a umidade do ar."
    )
    segundo = _observar(
        "Estamos falando do sensor de umidade do solo.",
        anterior=primeiro, instante=1001.0,
    )
    assert segundo["diagnostico"]["tem_foco"] is True
    terceiro = _observar(
        "O sensor leu 15% de umidade.",
        anterior=segundo, instante=1002.0,
    )
    assert terceiro["diagnostico"]["estado"] == "candidato_focal_pendente"
    assert terceiro["diagnostico"]["referente_resolvido"] is False


def test_cenario_parcial_ou_novo_cenario_vago_nao_reusa_candidato_antigo() -> None:
    parcial = _observar(_casos()["REF-06"]["contexto"][0])
    pergunta = _observar(
        "O sensor leu 15% de umidade.", anterior=parcial, instante=1001.0,
    )
    assert pergunta["diagnostico"]["estado"] == "cobertura_nao_demonstrada"
    completo = _observar(_casos()["REF-05"]["contexto"][0])
    substituido = _observar(
        "Neste cenário hipotético há sensores diferentes.",
        anterior=completo, instante=1001.0,
    )
    assert substituido["inventario"] == {}
    assert substituido["diagnostico"]["estado"] == "cenario_nao_enumeravel"


def test_texto_nao_usuario_nao_entra_na_sombra() -> None:
    resultado = _observar(
        _casos()["REF-05"]["contexto"][0], origem_texto="laylay",
    )
    assert resultado["inventario"] == {}
    assert resultado["diagnostico"]["estado"] == "entrada_invalida"


def test_inventario_serializado_malformado_nao_mantem_foco() -> None:
    primeiro = _observar(_casos()["REF-05"]["contexto"][0])
    corrompido = dict(primeiro)
    corrompido["inventario"] = {
        **primeiro["inventario"],
        "referentes": [{**primeiro["inventario"]["referentes"][0], "tipo": 42}],
    }
    segundo = _observar(
        "O sensor leu 15% de umidade.", anterior=corrompido, instante=1001.0,
    )
    assert segundo["inventario"] == {}
    assert segundo["diagnostico"]["estado"] == "sem_cenario_vigente"


@pytest.mark.parametrize("origem", ["terminal", "roteiro_teste"])
def test_composicao_real_do_turno_persiste_sombra_sem_alterar_autorizacao(
    origem: str,
) -> None:
    estado = EstadoCompartilhadoRuntime(mental=criar_estado_mental_inicial())

    class Saude:
        @staticmethod
        def snapshot():
            return {}

    ns = {
        "_estado_compartilhado_runtime": estado,
        "_pendencia_ativa_turno_mente": lambda _mente: {},
        "_classificar_modalidade_turno_mente": lambda _texto, **_kwargs: {
            "id": 77, "modalidade": "conversa", "modalidade_geral": "conversa",
            "ato_principal": "conversa", "segmentos": [],
            "autoriza_execucao": False,
        },
        "_texto_tem_comando_explicito": lambda _texto: False,
        "_normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
        "_resolver_repeticao_ultima_acao": lambda _texto: None,
        "_modo_jogo_runtime": None,
        "_registro_visao_jogo_leitura_runtime": None,
        "_interpretador_semantico_runtime": None,
        "_analisar_identidade_turno_mente": lambda _texto, **_kwargs: {},
        "_analisar_funcao_comunicativa_mente": lambda _texto: {
            "funcao": "informacao", "permite_pergunta": True,
        },
        "_classificar_encerramento_assunto_mente": lambda *_args: "",
        "_extrair_correcao_duravel_mente": lambda *_args, **_kwargs: {},
        "_abrir_correcao_interpretacao_mente": lambda *_args, **_kwargs: {},
        "_construir_retrato_turno_mente": construir_retrato_turno,
        "_obter_contexto_perceptivo": lambda: {},
        "playlist_state": {},
        "_atualizar_registro_turno_mente": atualizar_registro_turno,
        "_extrair_tema_fundamentacao_mente": lambda *_args, **_kwargs: "",
        "_construir_parecer_especialistas_mente": lambda *_args, **_kwargs: {
            "deliberacao": {"decisao": "responder"},
        },
        "_saude_mente_runtime": Saude(),
        "_orquestrador_cooperativo_runtime": None,
        "_atualizar_assunto_estruturado_mente": lambda *_args, **_kwargs: {},
        "_planejar_turno_mente": planejar_turno,
        "_evidencia_habilidades_turno_mente": lambda *_args, **_kwargs: {
            "fonte": "catalogo_vivo", "dominios_confirmados": [],
            "dominios_relevantes": [], "possui_capacidades_locais": True,
            "autoriza_execucao": False,
        },
        "_contexto_horario_atual": lambda: "dia",
        "_resumo_identidade_turno_mente": lambda _identidade: "",
        "_observabilidade_mente_runtime": None,
        "MEMORIA_SQLITE": None,
        "print": lambda *_args, **_kwargs: None,
        "time": time,
    }
    falas = (
        "Neste cenário hipotético há exatamente dois sensores: um mede a "
        "umidade do solo e o outro mede a umidade do ar.",
        "Estamos falando do sensor de umidade do solo.",
        "O sensor leu 15% de umidade.",
    )
    for fala in falas:
        turno = iniciar_planejamento_turno(lambda: ns, fala, origem=origem)
        assert turno["autoriza_execucao"] is False
    diagnostico = estado.mental["cenario_didatico_sombra"]
    assert diagnostico["estado"] == "candidato_focal_pendente"
    assert diagnostico["aprovado_para_compor"] is False
    assert diagnostico["autoriza_efeito"] is False


def test_observacao_sombra_nao_injeta_inventario_no_prompt() -> None:
    primeiro = _observar(_casos()["REF-05"]["contexto"][0])

    def preparar(estado: dict) -> tuple:
        runtime = ContextoPromptRuntime(
            memoria_sqlite=None,
            resumo_mente_integrada=lambda _texto: "",
            formatar_playlists=lambda: "",
            get_status_humor_prompt=lambda: "calma",
            base_system_prompt="BASE",
            estado_getter=lambda: estado,
        )
        return runtime.preparar("O sensor leu 15% de umidade.")

    base = {"messages": [], "turno_atual": {"modalidade": "conversa"}}
    com_sombra = {
        **base,
        "cenario_didatico_inventario": primeiro["inventario"],
        "cenario_didatico_sombra": primeiro["diagnostico"],
    }
    assert preparar(com_sombra) == preparar(base)


def test_nova_sessao_descarta_cenario_hipotetico_transitorio() -> None:
    primeiro = _observar(_casos()["REF-05"]["contexto"][0])
    renovado, _conversa, _mensagens = renovar_contexto_sessao(
        {"cenario_didatico_inventario": primeiro["inventario"],
         "cenario_didatico_sombra": primeiro["diagnostico"]},
        {}, [], motivo="teste", ativa=True, agora=1001.0,
    )
    assert renovado["cenario_didatico_inventario"] == {}
    assert renovado["cenario_didatico_sombra"] == {}
