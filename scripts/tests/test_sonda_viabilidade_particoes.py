"""Os dois juizos de viabilidade sao isolados e nunca sao autoridade."""

from scripts.analises import sonda_viabilidade_particoes as sonda
from scripts.analises.sonda_avaliador_fronteira_independente import (
    carregar_painel_fronteira,
)


CASOS, _ = carregar_painel_fronteira(25)
POR_ID = {caso["id"]: caso for caso in CASOS}


def test_objeto_claro_pede_duas_leituras_isoladas_e_conclui_so_proposta():
    caso = POR_ID["FERREIRO_MARTELO_ALICATE_APRENDIZ"]
    entradas = []

    def consultar(_sistema, entrada, _formato):
        entradas.append(entrada)
        if len(entradas) == 1:
            return {"viabilidade": "viavel", "motivo": "nenhum",
                    "citacao": ""}
        return {"viabilidade": "inviavel", "motivo": "concordancia",
                "citacao": "o alicate e a aprendiz chegar"}

    resultado = sonda.propor_viabilidade(caso, consultar)
    assert len(entradas) == 2
    assert [entrada["trechos_condicoes"] for entrada in entradas] == [
        [
            "o ferreiro polir o martelo e o alicate", "a aprendiz chegar",
        ],
        [
            "o ferreiro polir o martelo", "o alicate e a aprendiz chegar",
        ],
    ]
    assert resultado["estado"] == "relacao_proposta_revisao_pendente"
    assert resultado["relacao_proposta"] == "objeto_anterior"
    assert resultado["aprovado_para_producao"] is False
    assert resultado["autoriza_efeito"] is False
    assert "gabarito" not in str(entradas)


def test_cada_leitura_preserva_se_e_efeito_sem_mostrar_alternativa():
    caso = POR_ID["FERREIRO_MARTELO_ALICATE_APRENDIZ"]
    entradas = []

    def consultar(_sistema, entrada, _formato):
        entradas.append(entrada)
        return {"viabilidade": "incerta", "motivo": "incerteza",
                "citacao": ""}

    sonda.propor_viabilidade(caso, consultar)
    assert entradas[0]["frase_com_leitura"] == (
        "Se (o ferreiro polir o martelo e o alicate) e "
        "(a aprendiz chegar), a oficina abre."
    )
    assert entradas[1]["frase_com_leitura"] == (
        "Se (o ferreiro polir o martelo) e "
        "(o alicate e a aprendiz chegar), a oficina abre."
    )
    assert "gabarito" not in str(entradas)


def test_duas_leituras_viaveis_propoem_ambiguidade_sem_efeito():
    caso = POR_ID["PESCADOR_SALMAO_TRUTA_GOLFINHOS"]
    resultado = sonda.propor_viabilidade(
        caso, lambda *_: {"viabilidade": "viavel", "motivo": "nenhum",
                          "citacao": ""},
    )
    assert resultado["estado"] == "ambiguidade_proposta_revisao_pendente"
    assert resultado["relacao_proposta"] == "indeterminado"
    assert resultado["autoriza_efeito"] is False


def test_inviabilidade_precisa_de_motivo_e_condicao_literal_inteira():
    trechos = ["o ferreiro polir o martelo", "o alicate e a aprendiz chegar"]
    for bruto in (
        {"viabilidade": "inviavel", "motivo": "concordancia",
         "citacao": "a aprendiz chegar"},
        {"viabilidade": "inviavel", "motivo": "nenhum",
         "citacao": trechos[1]},
        {"viabilidade": "viavel", "motivo": "concordancia",
         "citacao": ""},
        {"viabilidade": "inviavel", "motivo": "concordancia",
         "citacao": trechos[1], "executar": True},
    ):
        resultado = sonda.validar_parecer(trechos, bruto)
        assert resultado["estado"] == "parecer_invalido"
        assert resultado["autoriza_efeito"] is False


def test_parenteses_adicionados_pela_sonda_podem_ser_removidos_da_citacao():
    trechos = ["o ferreiro polir o martelo", "o alicate e a aprendiz chegar"]
    resultado = sonda.validar_parecer(trechos, {
        "viabilidade": "inviavel", "motivo": "concordancia",
        "citacao": "(o alicate e a aprendiz chegar)",
    })
    assert resultado["estado"] == "inviabilidade_alegada_revisao_pendente"
    assert resultado["citacao"] == trechos[1]
    assert resultado["normalizacao"] == "parenteses_da_sonda"
    assert sonda.validar_parecer(trechos, {
        "viabilidade": "inviavel", "motivo": "concordancia",
        "citacao": "((o alicate e a aprendiz chegar))",
    })["estado"] == "parecer_invalido"


def test_parecer_invalido_ou_duas_inviaveis_nao_viram_relacao():
    caso = POR_ID["FERREIRO_MARTELO_ALICATE_APRENDIZ"]
    respostas = iter((
        {"viabilidade": "viavel", "motivo": "nenhum", "citacao": ""},
        {"viabilidade": "inviavel", "motivo": "concordancia",
         "citacao": "inventado"},
    ))
    resultado = sonda.propor_viabilidade(caso, lambda *_: next(respostas))
    assert resultado["estado"] == "abstencao_pareceres_invalidos"
    assert "relacao_proposta" not in resultado

    pareceres = {
        "objeto_anterior": sonda.validar_parecer(
            ["o ferreiro polir o martelo e o alicate", "a aprendiz chegar"],
            {"viabilidade": "inviavel", "motivo": "semantica",
             "citacao": "a aprendiz chegar"},
        ),
        "sujeito_seguinte": sonda.validar_parecer(
            ["o ferreiro polir o martelo", "o alicate e a aprendiz chegar"],
            {"viabilidade": "inviavel", "motivo": "concordancia",
             "citacao": "o alicate e a aprendiz chegar"},
        ),
    }
    assert sonda.concluir_pareceres(pareceres)["estado"] \
        == "abstencao_pareceres_invalidos"


def test_conclusao_nao_aceita_viabilidade_sem_parecer_validado():
    forjado = {
        "objeto_anterior": {"viabilidade": "viavel"},
        "sujeito_seguinte": {"viabilidade": "inviavel"},
    }
    resultado = sonda.concluir_pareceres(forjado)
    assert resultado["estado"] == "abstencao_pareceres_invalidos"
    assert "relacao_proposta" not in resultado


def test_regra_mista_nao_consulta_nenhum_modelo():
    caso = {"id": "MISTO", "fonte": (
        "Se a chuva cair e o vento soprar ou a bateria acabar, o aviso toca."
    )}

    def proibido(*_args):
        raise AssertionError("regra mista nao deve consultar modelo plano")

    resultado = sonda.propor_viabilidade(caso, proibido)
    assert resultado["estado"] == "abstencao_estrutura_lexical"
    assert resultado["autoriza_efeito"] is False


def test_painel_v26_congelado_prepara_nove_leituras_com_dupla_ambiguidade():
    from scripts.analises.sonda_avaliador_fronteira_independente import (
        carregar_painel_fronteira,
        preparar_entrada,
        preparar_pares,
    )

    casos, revisao = carregar_painel_fronteira(26)
    assert len(casos) == len(revisao) == 9
    assert all([item["relacao"] for item in revisao.values()].count(rotulo)
               == 3 for rotulo in ("sujeito_seguinte", "objeto_anterior",
                                  "indeterminado"))
    for caso in casos:
        assert preparar_entrada(caso)["estado"] == "entrada_literal_preparada"
        anotacao = revisao[caso["id"]]
        if anotacao["relacao"] == "indeterminado":
            leituras = {
                item["relacao"]: item["trechos_condicoes"]
                for item in preparar_pares(caso)["entrada"]["leituras"]
            }
            assert leituras == anotacao["leituras_plausiveis"]


def test_painel_v27_novo_prepara_nove_leituras_e_tres_controles_por_classe():
    from scripts.analises.sonda_avaliador_fronteira_independente import (
        preparar_entrada,
        preparar_pares,
    )

    casos, revisao = carregar_painel_fronteira(27)
    assert len(casos) == len(revisao) == 9
    assert all([item["relacao"] for item in revisao.values()].count(rotulo)
               == 3 for rotulo in ("sujeito_seguinte", "objeto_anterior",
                                  "indeterminado"))
    for caso in casos:
        assert preparar_entrada(caso)["estado"] == "entrada_literal_preparada"
        leituras = {
            item["relacao"]: item["trechos_condicoes"]
            for item in preparar_pares(caso)["entrada"]["leituras"]
        }
        if revisao[caso["id"]]["relacao"] == "indeterminado":
            assert leituras == revisao[caso["id"]]["leituras_plausiveis"]


def test_painel_v28_congelado_prepara_doze_leituras_quatro_por_classe():
    from scripts.analises.sonda_avaliador_fronteira_independente import (
        preparar_pares,
    )

    casos, revisao = carregar_painel_fronteira(28)
    assert len(casos) == len(revisao) == 12
    assert all([item["relacao"] for item in revisao.values()].count(rotulo)
               == 4 for rotulo in ("sujeito_seguinte", "objeto_anterior",
                                  "indeterminado"))
    for caso in casos:
        preparada = preparar_pares(caso)
        assert preparada["estado"] == "pares_literais_preparados"
        if revisao[caso["id"]]["relacao"] == "indeterminado":
            leituras = {
                item["relacao"]: item["trechos_condicoes"]
                for item in preparada["entrada"]["leituras"]
            }
            assert leituras == revisao[caso["id"]]["leituras_plausiveis"]


def test_concordancia_alegada_errada_em_sujeito_composto_plural_nao_decide_objeto():
    casos, _ = carregar_painel_fronteira(26)
    caso = next(item for item in casos if item["id"] ==
                "PORTEIRO_SALA_TECNICO_COORDENADORA")
    respostas = iter((
        {"viabilidade": "viavel", "motivo": "nenhum", "citacao": ""},
        {"viabilidade": "inviavel", "motivo": "concordancia",
         "citacao": "o técnico e a coordenadora entrarem"},
    ))
    resultado = sonda.propor_viabilidade(caso, lambda *_: next(respostas))
    assert resultado["estado"] == "abstencao_pareceres_invalidos"
    assert resultado["pareceres"]["sujeito_seguinte"]["estado"] \
        == "conflito_concordancia_superficial"
    assert "relacao_proposta" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_concordancia_singular_sem_sinal_plural_preserva_controle_de_objeto():
    caso = POR_ID["FERREIRO_MARTELO_ALICATE_APRENDIZ"]
    respostas = iter((
        {"viabilidade": "viavel", "motivo": "nenhum", "citacao": ""},
        {"viabilidade": "inviavel", "motivo": "concordancia",
         "citacao": "o alicate e a aprendiz chegar"},
    ))
    resultado = sonda.propor_viabilidade(caso, lambda *_: next(respostas))
    assert resultado["estado"] == "relacao_proposta_revisao_pendente"
    assert resultado["relacao_proposta"] == "objeto_anterior"


def test_sinal_plural_nao_valida_semantica():
    trechos = ["o porteiro destrancar a sala",
               "o técnico e a coordenadora entrarem"]
    semantica = sonda.validar_parecer(trechos, {
        "viabilidade": "inviavel", "motivo": "semantica",
        "citacao": trechos[1],
    })
    assert semantica["estado"] == "semantica_nao_corroborada"
    assert "viabilidade" not in semantica

    concordancia = sonda.validar_parecer(trechos, {
        "viabilidade": "inviavel", "motivo": "concordancia",
        "citacao": f"({trechos[1]})",
    })
    assert concordancia["estado"] == "conflito_concordancia_superficial"
    assert "viabilidade" not in concordancia
    assert concordancia["sinal_independente"]["estado"] \
        == "numero_convergente"
    assert concordancia["aprovado_para_producao"] is False


def test_alegacao_semantica_literal_nao_exclui_leitura():
    caso = POR_ID["FERREIRO_MARTELO_ALICATE_APRENDIZ"]
    respostas = iter((
        {"viabilidade": "viavel", "motivo": "nenhum", "citacao": ""},
        {"viabilidade": "inviavel", "motivo": "semantica",
         "citacao": "o alicate e a aprendiz chegar"},
    ))
    resultado = sonda.propor_viabilidade(caso, lambda *_: next(respostas))
    parecer = resultado["pareceres"]["sujeito_seguinte"]
    assert parecer["estado"] == "semantica_nao_corroborada"
    assert parecer["citacao"] == "o alicate e a aprendiz chegar"
    assert "viabilidade" not in parecer
    assert resultado["estado"] == "abstencao_pareceres_invalidos"
    assert "relacao_proposta" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_alegacao_semantica_na_primeira_leitura_tambem_nao_decide():
    caso = POR_ID["FERREIRO_MARTELO_ALICATE_APRENDIZ"]
    respostas = iter((
        {"viabilidade": "inviavel", "motivo": "semantica",
         "citacao": "a aprendiz chegar"},
        {"viabilidade": "viavel", "motivo": "nenhum", "citacao": ""},
    ))
    resultado = sonda.propor_viabilidade(caso, lambda *_: next(respostas))
    assert resultado["pareceres"]["objeto_anterior"]["estado"] \
        == "semantica_nao_corroborada"
    assert resultado["estado"] == "abstencao_pareceres_invalidos"
    assert "relacao_proposta" not in resultado


def test_viabilidade_alegada_nao_supera_numero_divergente_na_condicao_curta():
    caso = {"id": "CONTROLE_DIVERGENCIA", "fonte": (
        "Se o jardineiro regar a roseira e a samambaia e o vizinho "
        "aparecer, o jardim abre."
    )}
    resultado = sonda.propor_viabilidade(
        caso, lambda *_: {"viabilidade": "viavel", "motivo": "nenhum",
                          "citacao": ""},
    )
    parecer = resultado["pareceres"]["sujeito_seguinte"]
    assert parecer["estado"] == "conflito_viabilidade_superficial"
    assert parecer["citacao"] == "a samambaia e o vizinho aparecer"
    assert parecer["sinal_independente"]["estado"] == "numero_divergente"
    assert "viabilidade" not in parecer
    assert resultado["estado"] == "abstencao_pareceres_invalidos"
    assert "relacao_proposta" not in resultado


def test_alegacao_concordancia_sem_forma_lexical_nao_exclui_leitura():
    trechos = ["o porteiro destrancar a sala",
               "o técnico e a coordenadora trubarem"]
    parecer = sonda.validar_parecer(trechos, {
        "viabilidade": "inviavel", "motivo": "concordancia",
        "citacao": trechos[1],
    })
    assert parecer["estado"] == "concordancia_nao_corroborada"
    assert "viabilidade" not in parecer
    assert parecer["autoriza_efeito"] is False


def test_alegacao_concordancia_em_numero_divergente_permanece_provisoria():
    trechos = ["o ferreiro polir o martelo",
               "o alicate e a aprendiz chegar"]
    parecer = sonda.validar_parecer(trechos, {
        "viabilidade": "inviavel", "motivo": "concordancia",
        "citacao": trechos[1],
    })
    assert parecer["estado"] == "inviabilidade_alegada_revisao_pendente"
    assert parecer["sinal_independente"]["estado"] == "numero_divergente"
    assert parecer["aprovado_para_producao"] is False


def test_indice_morfologico_indisponivel_impede_exclusao_por_concordancia(
    monkeypatch, tmp_path,
):
    from scripts.analises import veto_superficie_sujeito_composto as superficie

    monkeypatch.setattr(superficie, "_CAMINHO_INDICE_MORFOLOGICO",
                        tmp_path / "ausente.tsv")
    trechos = ["o ferreiro polir o martelo",
               "o alicate e a aprendiz chegar"]
    parecer = sonda.validar_parecer(trechos, {
        "viabilidade": "inviavel", "motivo": "concordancia",
        "citacao": trechos[1],
    })
    assert parecer["estado"] == "concordancia_nao_corroborada"
    assert parecer["sinal_independente"]["estado"] \
        == "recurso_morfologico_indisponivel"
    assert "viabilidade" not in parecer


def test_forma_nao_atestada_nao_produz_relacao_no_caminho_composto():
    caso = {"id": "FORMA_NAO_ATESTADA", "fonte": (
        "Se a jardineira observar a horta e o cuidador e a vizinha "
        "trubarem, o portão abre."
    )}
    respostas = iter((
        {"viabilidade": "viavel", "motivo": "nenhum", "citacao": ""},
        {"viabilidade": "inviavel", "motivo": "concordancia",
         "citacao": "o cuidador e a vizinha trubarem"},
    ))
    resultado = sonda.propor_viabilidade(caso, lambda *_: next(respostas))
    assert resultado["estado"] == "abstencao_pareceres_invalidos"
    assert resultado["pareceres"]["sujeito_seguinte"]["estado"] \
        == "concordancia_nao_corroborada"
    assert "relacao_proposta" not in resultado
    assert resultado["aprovado_para_producao"] is False
