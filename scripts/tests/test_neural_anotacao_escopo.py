from copy import deepcopy
import json
from pathlib import Path

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.neural.anotacao_escopo import referencia_canonica, validar_anotacao_escopo
from mente_laylay.neural.auditar_escopo_manual import auditar_piloto
from mente_laylay.neural.dataset import validar_exemplo
from mente_laylay.especialistas.capacidades import intents_registradas

PILOTO = Path(__file__).parents[2] / "mente_laylay/neural/datasets/escopo_relacional_piloto_v1.json"
CASOS = json.loads(PILOTO.read_text(encoding="utf-8"))["casos"]


def preparar(caso):
    turno = classificar_modalidade_turno(
        caso["texto_entrada"], texto_tem_comando_explicito=texto_tem_comando_explicito,
        confirmacao_contextual_valida=False,
    )
    anotacao = {"versao": 1, "origem": "anotacao_manual",
                "referencia_sha256": referencia_canonica(turno)["sha256"],
                "segmentos": deepcopy(caso["segmentos"])}
    return turno, anotacao


def validar(turno, anotacao):
    return validar_anotacao_escopo(anotacao, turno=turno, variantes_permitidas={
        ("MUSIC_SEARCH", "search"), ("APP_OPEN", "open"), ("CLOSE_APP", "close"),
        ("FILE_READ", "read"), ("CLOSE_TAB", "close"),
    })


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
def test_rotulo_manual_alinha_com_componente_canonico_sem_muta_lo(caso):
    turno, anotacao = preparar(caso)
    antes = deepcopy((turno, anotacao))
    r = validar(turno, anotacao)
    assert (turno, anotacao) == antes
    assert r["anotacao"] == anotacao
    assert r["somente_observacao"]
    assert r["autoriza_execucao"] is r["treino_permitido"] is r["autoriza_promocao"] is False
    # Sidecar não se disfarça de exemplo de treino do schema booleano.
    with pytest.raises(ValueError, match="sem text"):
        validar_exemplo(r, intents_permitidas=intents_registradas())
    r["anotacao"]["segmentos"].clear()
    assert anotacao["segmentos"]


def test_auditoria_usa_catalogo_real_e_nao_apresenta_alinhamento_como_acuracia():
    r = auditar_piloto(PILOTO)
    assert r["total"] == 16
    assert not r["modelo_avaliado"] and not r["runtime_completo"]
    assert "acuracia" not in r
    casos = {c["id"]: c for c in r["casos"]}
    # A expectativa positiva independente NÃO elimina o veto real.
    c = casos["apps_correcao"]
    assert c["anotacao"]["segmentos"][0]["acoes"][0]["ato"] == "pedido"
    assert c["referencia"]["leitura_observada"]["veto_execucao_operacional"] is True
    assert c["autoriza_execucao"] is False


@pytest.mark.parametrize("mudanca", ["texto", "veto", "indice"])
def test_referencia_obsoleta_aborta_sem_remapear(mudanca):
    turno, anotacao = preparar(CASOS[0])
    if mudanca == "texto":
        turno["segmentos"][0]["texto"] += " agora"
    elif mudanca == "veto":
        turno["veto_execucao_operacional"] = not turno.get("veto_execucao_operacional")
    else:
        turno["segmentos"][0]["indice"] = 3
    with pytest.raises(ValueError, match="referência canônica mudou"):
        validar(turno, anotacao)


@pytest.mark.parametrize("mudanca", [
    "span", "bool_offset", "texto", "duplicata", "sem_segmento", "campo_autoridade",
    "acao_desconhecida", "pedido_sem_alvo", "sobreposicao", "recusa_com_pedido",
    "relato_com_exclusao", "alternativa_com_alvo", "origem_modelo", "acao_duplicada",
])
def test_anotacao_incoerente_nao_e_reparada_silenciosamente(mudanca):
    turno, anotacao = preparar(CASOS[0])
    seg = anotacao["segmentos"][0]
    acao = seg["acoes"][0]
    if mudanca == "span":
        acao["alvos_solicitados"][0]["inicio"] += 1
    elif mudanca == "bool_offset":
        acao["alvos_solicitados"][0]["inicio"] = True
    elif mudanca == "texto":
        seg["texto"] += " agora"
    elif mudanca == "duplicata":
        anotacao["segmentos"].append(deepcopy(seg))
    elif mudanca == "sem_segmento":
        anotacao["segmentos"].clear()
    elif mudanca == "campo_autoridade":
        acao["autoriza_execucao"] = True
    elif mudanca == "acao_desconhecida":
        acao["action"] = "delete"
    elif mudanca == "pedido_sem_alvo":
        acao["alvos_solicitados"] = []
    elif mudanca == "sobreposicao":
        acao["alvos_excluidos"] = deepcopy(acao["alvos_solicitados"])
    elif mudanca == "recusa_com_pedido":
        acao["ato"] = "recusa"
    elif mudanca == "relato_com_exclusao":
        acao.update(ato="relato", resolucao_alvo="nao_aplicavel", alvos_solicitados=[])
    elif mudanca == "alternativa_com_alvo":
        acao["resolucao_alvo"] = "alternativa"
    elif mudanca == "acao_duplicada":
        seg["acoes"].append(deepcopy(acao))
    else:
        anotacao["origem"] = "previsao_neural"
    with pytest.raises(ValueError):
        validar(turno, anotacao)


def test_timestamp_nao_muda_referencia_mas_texto_e_veto_mudam():
    turno, _ = preparar(CASOS[0])
    antes = referencia_canonica(turno)
    turno["ts"] = -1
    assert referencia_canonica(turno) == antes


def test_alvo_excluido_de_uma_acao_nao_contamina_outra():
    caso = deepcopy(next(c for c in CASOS if c["id"] == "acoes_distintas"))
    # O MESMO alvo pode ser solicitado para abrir e excluído para fechar.
    caso["texto_entrada"] = "abra o opera e não feche o opera"
    seg = caso["segmentos"][0]
    seg["texto"] = caso["texto_entrada"]
    m = seg["acoes"][1]["alvos_excluidos"][0]
    m.update(inicio=seg["texto"].rindex("opera"), fim=len(seg["texto"]), texto="opera")
    turno, anotacao = preparar(caso)
    r = validar(turno, anotacao)
    assert len(r["anotacao"]["segmentos"][0]["acoes"]) == 2
    assert not r["autoriza_execucao"]


def test_segmentacao_real_nao_e_refeita_e_cobertura_parcial_aborta():
    entrada = "abra o opera e feche o firefox"
    turno = classificar_modalidade_turno(entrada, texto_tem_comando_explicito=texto_tem_comando_explicito)
    assert [s["texto"] for s in turno["segmentos"]] == ["abra o opera", "feche o firefox"]
    segmentos = []
    for s, intent, action, alvo in zip(turno["segmentos"], ("APP_OPEN", "CLOSE_APP"),
                                       ("open", "close"), ("opera", "firefox"), strict=True):
        inicio = s["texto"].index(alvo)
        segmentos.append({"indice": s["indice"], "texto": s["texto"], "acoes": [{
            "intent": intent, "action": action, "ato": "pedido", "resolucao_alvo": "explicito",
            "alvos_solicitados": [{"inicio": inicio, "fim": inicio + len(alvo), "texto": alvo}],
            "alvos_excluidos": [], "alvos_mencionados": [],
        }]})
    anotacao = {"versao": 1, "origem": "anotacao_manual", "segmentos": segmentos,
                "referencia_sha256": referencia_canonica(turno)["sha256"]}
    assert len(validar(turno, anotacao)["anotacao"]["segmentos"]) == 2
    anotacao["segmentos"].pop()
    with pytest.raises(ValueError, match="sem cobertura"):
        validar(turno, anotacao)
