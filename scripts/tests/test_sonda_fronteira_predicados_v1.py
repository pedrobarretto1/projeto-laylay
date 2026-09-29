"""Predicados em fragmentos evidenciam fronteiras, não autorizam ensino."""

from scripts.analises import sonda_fronteira_predicados_v1 as sonda
from scripts.analises.sonda_produtor_condicoes_v2 import carregar_painel


CASOS, OURO = carregar_painel(6)
POR_ID = {caso["id"]: caso for caso in CASOS}


def _proposta(*pares):
    return {"segmentos": [
        {"id": f"c{indice}", "tem_predicado": bool(ancora), "ancora": ancora}
        for indice, ancora in enumerate(pares)
    ]}


def test_sujeito_composto_junta_fragmentos_ate_o_predicado():
    caso = POR_ID["VALVULAS_SUJEITO_E"]
    resultado = sonda.reconstruir_condicoes(caso, _proposta("", "estiverem"))
    assert resultado["estado"] == "segmentos_ancorados_revisao_pendente"
    assert resultado["trechos"]["trechos_condicoes"] == [
        "as válvulas A e B estiverem fechadas",
    ]
    assert resultado["trechos"]["conectivo_condicoes"] == "unico"
    assert resultado["autoriza_efeito"] is False


def test_predicados_independentes_viram_duas_condicoes():
    caso = POR_ID["ESTUFA_PREDICADOS_E"]
    resultado = sonda.reconstruir_condicoes(caso, _proposta("estiver", "estiver"))
    assert resultado["estado"] == "segmentos_ancorados_revisao_pendente"
    assert resultado["trechos"]["trechos_condicoes"] == [
        "a janela estiver fechada", "o exaustor estiver ligado",
    ]
    assert resultado["trechos"]["conectivo_condicoes"] == "e"


def test_sujeito_composto_mais_segunda_oracao_gera_particao_intermediaria():
    caso = {"fonte": (
        "Se os sensores A e B detectarem fumaça e a bateria estiver carregada, "
        "o alarme toca."
    )}
    resultado = sonda.reconstruir_condicoes(
        caso, _proposta("", "detectarem", "estiver"),
    )
    assert resultado["trechos"]["trechos_condicoes"] == [
        "os sensores A e B detectarem fumaça", "a bateria estiver carregada",
    ]
    assert resultado["trechos"]["conectivo_condicoes"] == "e"


def test_fragmento_sem_predicado_entre_condicoes_nao_e_unido_em_silencio():
    caso = {"fonte": (
        "Se o sino tocar ou a sirene soar ou a porta abrir, o alerta acende."
    )}
    resultado = sonda.reconstruir_condicoes(
        caso, _proposta("tocar", "", "abrir"),
    )
    assert resultado["estado"] == "fronteira_interna_sem_predicado_ambigua"
    assert "trechos" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_prefixo_da_segunda_condicao_sem_predicado_tambem_se_abstem():
    caso = {"fonte": (
        "Se o servidor responder e os sensores A e B gravarem, "
        "o aviso aparece."
    )}
    resultado = sonda.reconstruir_condicoes(
        caso, _proposta("responder", "", "gravarem"),
    )
    assert resultado["estado"] == "fronteira_interna_sem_predicado_ambigua"
    assert "trechos" not in resultado


def test_prefixos_sem_predicado_antes_da_primeira_condicao_continuam_validos():
    casos, _ = carregar_painel(13)
    caso = next(item for item in casos
                if item["id"] == "CRIANCAS_TRES_ADJETIVOS")
    resultado = sonda.reconstruir_condicoes(
        caso, _proposta("", "", "chegarem"),
    )
    assert resultado["estado"] == "segmentos_ancorados_revisao_pendente"
    assert len(resultado["trechos"]["trechos_condicoes"]) == 1


def test_ancora_inventada_nao_passa_e_ids_validos_podem_vir_permutados():
    caso = POR_ID["VALVULAS_SUJEITO_E"]
    assert sonda.reconstruir_condicoes(
        caso, _proposta("", "desligaram"),
    )["estado"] == "ancora_invalida"
    trocado = {"segmentos": [
        {"id": "c1", "tem_predicado": True, "ancora": "estiverem"},
        {"id": "c0", "tem_predicado": False, "ancora": ""},
    ]}
    assert sonda.reconstruir_condicoes(caso, trocado)["estado"] \
        == "segmentos_ancorados_revisao_pendente"
    trocado["segmentos"][1]["id"] = "c1"
    assert sonda.reconstruir_condicoes(caso, trocado)["estado"] == "entrada_invalida"


def test_misto_recusa_antes_do_modelo(monkeypatch):
    caso = POR_ID["TRAVA_MISTA_V6"]

    def proibida(*args, **kwargs):
        raise AssertionError("nao chamar modelo para arvore mista")

    monkeypatch.setattr(sonda, "_consultar_modelo", proibida)
    resultado = sonda.medir_caso(caso, OURO[caso["id"]])
    assert resultado["escolha"] == "recusa_estrutura_plana"


def test_modelo_recebe_fragmentos_sem_gabarito(monkeypatch):
    caso = POR_ID["VALVULAS_SUJEITO_E"]
    entradas = []

    def consulta(_sistema, entrada, _formato, *, url, modelo):
        entradas.append(entrada)
        return _proposta("", "estiverem")

    monkeypatch.setattr(sonda, "_consultar_modelo", consulta)
    resultado = sonda.medir_caso(caso, OURO[caso["id"]])
    assert len(entradas) == 1
    assert "condicoes" not in entradas[0]
    assert "gabarito" not in entradas[0]
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"
    assert resultado["aprovado_para_producao"] is False


def test_painel_v7_congelado_cobre_sujeitos_predicados_e_particao_parcial():
    casos, ouro = carregar_painel(7)
    assert len(casos) == len(ouro) == 8
    assert set(caso["id"] for caso in casos) == set(ouro)
    por_id = {caso["id"]: caso for caso in casos}
    assert sonda.reconstruir_condicoes(
        por_id["SENSORES_E_BATERIA"],
        _proposta("", "detectarem", "estiver"),
    )["trechos"]["trechos_condicoes"] == [
        "os sensores A e B detectarem fumaça", "a bateria estiver carregada",
    ]
    assert sonda.reconstruir_condicoes(
        por_id["PROTOCOLO_MISTO_V7"],
        _proposta("travar", "avisar", "confirmar"),
    )["estado"] == "recusa_estrutura_plana"
