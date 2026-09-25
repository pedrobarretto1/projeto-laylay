"""Anotações artificiais testam contratos; não são avaliação inédita ou treino."""
from copy import deepcopy

import pytest

from mente_laylay.neural.supervisao_operacional_v1 import (
    PERFIL, ROTULOS, VARIANTES, preparar_exemplo_operacional,
)
from mente_laylay.neural.supervisao_relacoes_v4 import FLAGS
from mente_laylay.neural.comparar_ocorrencias_v4 import (
    ROTULOS as ROTULOS_HISTORICOS, rotular_ocorrencias,
)
from mente_laylay.neural.protocolo_ajuste_supervisionado import validar_caso
from tests.test_neural_protocolo_ajuste_supervisionado import caso


def exemplo(texto="coloca o volume em 50", *, intent="VOLUME", action="set",
            ancora="coloca", alvo="volume", ato="pedido", valor=50):
    c = caso(texto, intent=intent, action=action, ancora=ancora, alvo=alvo, ato=ato)
    parametros = []
    if intent == "VOLUME":
        literal = str(valor)
        inicio = texto.index(literal)
        parametros = [{"ocorrencia": "n0", "nome": "nivel_volume", "valor": valor,
                       "unidade": "percentual", "evidencia": {
                           "inicio": inicio, "fim": inicio + len(literal), "texto": literal}}]
    return {"versao": 1, "perfil": PERFIL, "escopo": "literal_imediato",
            "origem_rotulo": "curadoria_ia", "referencia_rotulo": "fixture/sintetica",
            "fonte_v4": c["fonte_v4"], "parametros": parametros, **FLAGS}


VARIANTES_TEXTO = [
    ("APP_OPEN", "open", "abre", "editor"),
    ("MUSIC_SEARCH", "search", "toca", "Aurora"),
    ("FILE_READ", "read", "leia", "notas.txt"),
    ("IOT_CONTROL", "on", "liga", "luz"),
    ("IOT_CONTROL", "off", "desliga", "ventilador"),
    ("MEDIA_CONTROL", "pause", "pausa", "musica"),
    ("MEDIA_CONTROL", "play", "despausa", "musica"),
    ("MEDIA_CONTROL", "next", "pula", "musica"),
    ("VOLUME", "set", "coloca", "volume"),
]


@pytest.mark.parametrize("ato,prefixo", [
    ("pedido", ""), ("recusa", "nao "), ("relato", "ontem eu disse: "),
])
@pytest.mark.parametrize("intent,action,ancora,alvo", VARIANTES_TEXTO)
def test_perfil_ampliado_separa_ato_acao_alvo_e_valor(ato, prefixo, intent, action, ancora, alvo):
    texto = prefixo + ancora + " " + alvo + (" em 50" if intent == "VOLUME" else "")
    anotacao = exemplo(texto, intent=intent, action=action, ancora=ancora, alvo=alvo, ato=ato)
    antes = deepcopy(anotacao)
    r = preparar_exemplo_operacional(anotacao)
    assert anotacao == antes
    assert r["entrada"] == {"texto": texto}
    assert r["supervisao"]["rotulos"].count(f"{intent}|{action}|{ato}") == 1
    assert r["supervisao"]["fonte_v4"]["nos"][0]["alvos"][0]["texto"] == alvo
    assert r["supervisao"]["parametros"] == anotacao["parametros"]
    assert all(r[k] is False for k in FLAGS)
    assert r["dados_prontos_para_treino"] is False


@pytest.mark.parametrize("texto,intent,action,ancora,alvo", [
    ("liga o ventildor", "IOT_CONTROL", "on", "liga", "ventildor"),
    ("pausa a muica", "MEDIA_CONTROL", "pause", "pausa", "muica"),
    ("pode despausar a musica", "MEDIA_CONTROL", "play", "despausar", "musica"),
    ("coloca o volume em 100", "VOLUME", "set", "coloca", "volume"),
])
def test_grafia_real_preservada_sem_parser_escolher_rotulo(texto, intent, action, ancora, alvo):
    r = preparar_exemplo_operacional(exemplo(
        texto, intent=intent, action=action, ancora=ancora, alvo=alvo, valor=100,
    ))
    assert r["entrada"]["texto"] == texto
    assert r["revisao_semantica_certificada"] is False


@pytest.mark.parametrize("valor", [0, 1, 50, 100])
def test_percentual_nao_e_reinterpretado_como_fracao(valor):
    r = preparar_exemplo_operacional(exemplo(f"coloca o volume em {valor}", valor=valor))
    assert r["supervisao"]["parametros"][0]["valor"] == valor


@pytest.mark.parametrize("campo,valor", [
    ("valor", True), ("valor", 50.0), ("valor", -1), ("valor", 101), ("valor", 51),
    ("unidade", "fracao"), ("nome", "device_id"), ("ocorrencia", "inexistente"),
])
def test_parametros_invalidos_nao_entram_no_diagnostico(campo, valor):
    a = exemplo(); a["parametros"][0][campo] = valor
    with pytest.raises(ValueError):
        preparar_exemplo_operacional(a)


@pytest.mark.parametrize("modo", ["ausente", "duplicado", "span_falso", "valor_como_alvo"])
def test_evidencia_numerica_tem_dono_e_nao_substitui_alvo(modo):
    a = exemplo()
    if modo == "ausente": a["parametros"] = []
    elif modo == "duplicado": a["parametros"] *= 2
    elif modo == "span_falso": a["parametros"][0]["evidencia"]["inicio"] = 0
    else: a["fonte_v4"]["nos"][0]["alvos"] = [deepcopy(a["parametros"][0]["evidencia"])]
    with pytest.raises(ValueError):
        preparar_exemplo_operacional(a)


@pytest.mark.parametrize("escopo", ["contextual", "agendado", "correcao_temporal", "implicito"])
def test_escopo_nao_suportado_nao_vira_comando_imediato(escopo):
    a = exemplo(); a["escopo"] = escopo
    with pytest.raises(ValueError, match="exige outro perfil"):
        preparar_exemplo_operacional(a)


@pytest.mark.parametrize("flag", FLAGS)
@pytest.mark.parametrize("lugar", ["envelope", "fonte"])
def test_supervisao_nao_concede_autoridade(flag, lugar):
    a = exemplo(); (a if lugar == "envelope" else a["fonte_v4"])[flag] = True
    with pytest.raises(ValueError):
        preparar_exemplo_operacional(a)


def test_perfil_historico_nao_e_mutado_ou_liberado_por_importar_extensao():
    assert len(VARIANTES) == 9 and len(ROTULOS) == 28
    assert len(ROTULOS_HISTORICOS) == 10
    c = caso("liga a luz", intent="IOT_CONTROL", action="on", ancora="liga", alvo="luz")
    with pytest.raises(ValueError, match="catálogo"):
        validar_caso(c)
    n = c["fonte_v4"]["nos"][0]
    projecao = {"alinhado": {"entrada": {"texto_entrada": c["texto"], "segmentos": [{"indice": 0, "texto": c["texto"]}]},
        "supervisao": {"nos": [{**n, "ancora": {**n["ancora"], "segmento": 0}}]}}}
    with pytest.raises(ValueError, match="fora do perfil"):
        rotular_ocorrencias(projecao)
    assert "IOT_CONTROL|on|pedido" in rotular_ocorrencias(projecao, rotulos_permitidos=ROTULOS)
    assert len(ROTULOS_HISTORICOS) == 10
