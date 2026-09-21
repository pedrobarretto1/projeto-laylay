from collections import Counter, defaultdict

import pytest

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.neural.anotacao_escopo import referencia_canonica, validar_anotacao_escopo
from mente_laylay.neural.datasets.gerar_escopo_relacional_v2 import gerar_grade_relacional
from mente_laylay.neural.qualidade import _normalizar_texto


def test_grade_fatorial_reserva_eixos_antes_de_modelo():
    casos = gerar_grade_relacional()
    assert len(casos) == len({c["id"] for c in casos}) == 216
    assert Counter(c["particao"] for c in casos) == {
        "desenvolvimento": 96, "reserva_entidades": 48,
        "reserva_construcoes": 48, "reserva_ambas": 24,
    }
    dev = [c for c in casos if c["particao"] == "desenvolvimento"]
    for particao, eixo in (("reserva_entidades", "grupo_entidades"), ("reserva_construcoes", "grupo_construcao")):
        assert not {c[eixo] for c in dev} & {c[eixo] for c in casos if c["particao"] == particao}
    assert {c["grupo_entidades"] for c in dev}.isdisjoint(
        c["grupo_entidades"] for c in casos if c["particao"] == "reserva_ambas")
    assert {c["grupo_construcao"] for c in dev}.isdisjoint(
        c["grupo_construcao"] for c in casos if c["particao"] == "reserva_ambas")


def test_irmaos_de_aspas_ficam_juntos_sem_mudar_rotulos():
    grupos = defaultdict(list)
    for c in gerar_grade_relacional():
        grupos[c["grupo_contraste"]].append(c)
    assert len(grupos) == 108
    for a, b in grupos.values():
        assert a["particao"] == b["particao"]
        assert a["texto_entrada"] == b["texto_entrada"].replace('"', '')
        aa, bb = (c["segmentos"][0]["acoes"][0] for c in (a, b))
        for k in ("ato", "intent", "action", "resolucao_alvo"):
            assert aa[k] == bb[k]
        for k in ("alvos_solicitados", "alvos_excluidos", "alvos_mencionados"):
            assert [m["texto"] for m in aa[k]] == [m["texto"] for m in bb[k]]


def test_spans_manuais_validos_sem_fingir_classificacao_real_das_reservas():
    for c in gerar_grade_relacional():
        # Apenas contrato sintético de offsets; não chamamos um classificador.
        turno = {"segmentos": [{"indice": 0, "texto": c["texto_entrada"]}]}
        a = {"versao": 1, "origem": "anotacao_manual", "segmentos": c["segmentos"],
             "referencia_sha256": referencia_canonica(turno)["sha256"]}
        r = validar_anotacao_escopo(a, turno=turno, variantes_permitidas={
            ("APP_OPEN", "open"), ("MUSIC_SEARCH", "search"), ("FILE_READ", "read")})
        assert not r["treino_permitido"]


def test_nao_ha_texto_normalizado_exato_cruzando_particoes():
    particoes = defaultdict(set)
    for c in gerar_grade_relacional():
        particoes[_normalizar_texto(c["texto_entrada"])].add(c["particao"])
    assert all(len(p) == 1 for p in particoes.values())


@pytest.mark.parametrize("dominio", ["apps", "musica", "arquivos"])
@pytest.mark.parametrize("aspas", [False, True])
def test_restricao_anteposta_nao_pode_ser_silenciosamente_colada_ao_segundo_segmento(dominio, aspas):
    c = next(c for c in gerar_grade_relacional() if c["grupo_entidades"] == "rel_v2_e0"
             and c["grupo_construcao"] == "rel_v2_f1" and c["mecanismo"] == "pedido"
             and c["dominio"] == dominio and c["com_aspas"] == aspas)
    turno = classificar_modalidade_turno(c["texto_entrada"],
                                         texto_tem_comando_explicito=texto_tem_comando_explicito)
    # Fronteira alcançada com componentes reais: texto inteiro não sumiu;
    # foi dividido. O contrato v1 não representa a aresta entre esses atos.
    assert len(turno["segmentos"]) == 2
    assert ", ".join(s["texto"] for s in turno["segmentos"]) == c["texto_entrada"]
    acao = c["segmentos"][0]["acoes"][0]
    assert acao["alvos_excluidos"][0]["texto"] in turno["segmentos"][0]["texto"]
    assert acao["alvos_solicitados"][0]["texto"] in turno["segmentos"][1]["texto"]
    anotacao = {"versao": 1, "origem": "anotacao_manual", "segmentos": c["segmentos"],
                "referencia_sha256": referencia_canonica(turno)["sha256"]}
    with pytest.raises(ValueError, match="texto anotado divergiu"):
        validar_anotacao_escopo(anotacao, turno=turno,
                               variantes_permitidas={(acao["intent"], acao["action"])})
