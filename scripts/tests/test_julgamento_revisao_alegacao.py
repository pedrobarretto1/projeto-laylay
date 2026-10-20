"""Resposta posterior deve consumir a mesma revisão, não só seu prompt."""
import os

from scripts.tests.test_revisao_dirigida_alegacao import revisao_instalada
import pytest
from copy import deepcopy

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.registro_semantico import (
    registrar_alegacao, contestar_alegacao_recente, corrigir_alegacao_recente,
)


def _plano(afirmacao="O arquivo beta tem uma cópia externa.", *, status="contestado", autor="laylay", texto=None):
    registro = registrar_alegacao(None, afirmacao, autor=autor, agora=100)
    if status == "contestado":
        registro = contestar_alegacao_recente(registro, f'De onde você tirou "{afirmacao}"?', agora=101)
    elif status == "corrigido":
        registro = corrigir_alegacao_recente(registro, f'A afirmação "{afirmacao}" está errada.', agora=101)
    texto = texto or 'Você mantém a alegação ' + registro["alegacoes"][0]["id"] + '?'
    turno = {**classificar_modalidade_turno(texto), "id": "consulta"}
    plano = {"id": "consulta", "texto_usuario": texto, "autoriza_execucao": False, "comandos": []}
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano,
        mente={"registro_semantico": registro})
    return plano


@pytest.mark.parametrize("afirmacao", ["O arquivo beta tem uma cópia externa.", "A tomada do quarto tem proteção elétrica."])
def test_revisao_pertence_ao_julgamento_compartilhado_e_nao_so_a_projecao(afirmacao):
    plano = _plano(afirmacao)
    texto = plano["texto_usuario"]
    assert "revisao_alegacao" in plano["contrato_fala"]
    for avaliacao in (validar_alegacoes_da_fala(afirmacao, plano=plano),
                     avaliar_qualidade_comunicacao(texto, afirmacao, plano=plano),
                     validar_aderencia_contrato_fala(texto, afirmacao,
                         contrato_fala=plano["contrato_fala"], turno_id="consulta")):
        assert avaliacao["problemas"]
    segura = validar_alegacoes_da_fala(afirmacao, plano=plano)["fala"]
    assert "contestad" in segura
    assert not validar_alegacoes_da_fala(segura, plano=plano)["problemas"]
    adulterado = deepcopy(plano)
    adulterado["id"] = "outro_turno"
    assert validar_alegacoes_da_fala(segura, plano=adulterado)["problemas"]


@pytest.mark.parametrize("fala", ["O arquivo beta tem uma cópia externa.",
    "Há um backup externo do arquivo beta.", "Não existe cópia externa do arquivo beta.",
    "Você contestou, então a afirmação é falsa.", "Sua alternativa é a correta.",
    "Essa prova garante que posso apagar o arquivo."])
def test_revisao_nao_se_converte_em_afirmacao_negacao_alternativa_ou_autoridade(fala):
    plano = _plano()
    avaliacao = validar_alegacoes_da_fala(fala, plano=plano)
    assert avaliacao["problemas"] == ["revisao_alegacao_sem_cobertura"]
    assert avaliacao["prova_semantica_livre"] is False
    assert avaliacao["autoriza_execucao"] is False
    assert not validar_alegacoes_da_fala(avaliacao["fala"], plano=plano)["problemas"]


@pytest.mark.parametrize("adulteracao", ["json", "ausente", "turno", "consulta", "comandos"])
def test_fonte_invalida_nao_desliga_protecao_e_limite_pode_ser_publicado(adulteracao):
    from dataclasses import asdict
    plano = _plano()
    if adulteracao == "json":
        plano["contrato_fala"]["revisao_alegacao"] = asdict(plano["contrato_fala"]["revisao_alegacao"])
    elif adulteracao == "ausente":
        plano["contrato_fala"]["revisao_alegacao"] = None
    elif adulteracao == "turno":
        plano["id"] = "outro"
    elif adulteracao == "consulta":
        plano["texto_usuario"] = "Outra consulta?"
    else:
        plano["comandos"] = [{"intent": "DELETE_FILE"}]
    avaliacao = validar_alegacoes_da_fala("A afirmação está confirmada.", plano=plano)
    assert avaliacao["problemas"] == ["revisao_alegacao_invalida"]
    assert avaliacao["fonte_valida"] is False
    assert not validar_alegacoes_da_fala(avaliacao["fala"], plano=plano)["problemas"]


def test_correcao_nao_ganha_prova_de_versao_substituta():
    plano = _plano(status="corrigido")
    a = validar_alegacoes_da_fala("A versão nova está confirmada.", plano=plano)
    assert a["problemas"] and "corrigida" in a["fala"]
    assert "nem confirma uma alternativa" in a["fala"]


@pytest.mark.parametrize("texto", ["Qual música você prefere?", "Você mantém a alegação alegacao:999?",
    'Traduza "O arquivo beta tem uma cópia externa." para inglês.',
    'Como eu perguntaria "O arquivo beta tem uma cópia externa."?'])
def test_outro_assunto_referencia_desconhecida_e_metalinguagem_nao_herdam_revisao(texto):
    plano = _plano(texto=texto)
    assert "revisao_alegacao" not in plano["contrato_fala"]


@pytest.mark.parametrize("autor,status", [("usuario", "contestado"), ("laylay", "incerto")])
def test_fonte_nao_revisada_ou_de_outro_autor_nao_vira_revisao_propria(autor, status):
    assert "revisao_alegacao" not in _plano(autor=autor, status=status)["contrato_fala"]


@pytest.fixture(scope="module", autouse=True)
def coletar_julgamento():
    anterior = os.environ.get("LAYLAY_COLETAR_JULGAMENTO_REVISAO")
    os.environ["LAYLAY_COLETAR_JULGAMENTO_REVISAO"] = "1"
    yield
    if anterior is None:
        os.environ.pop("LAYLAY_COLETAR_JULGAMENTO_REVISAO", None)
    else:
        os.environ["LAYLAY_COLETAR_JULGAMENTO_REVISAO"] = anterior


@pytest.mark.parametrize("indice", [0, 1])
@pytest.mark.parametrize("consulta", [0, 1])
def test_composicao_vincula_revisao_ao_julgamento_e_nao_reafirma_a_alegacao(revisao_instalada, indice, consulta):
    caso = revisao_instalada[indice]
    posterior = caso["posteriores"][consulta]
    contrato = posterior["plano"]["contrato_fala"]
    assert "revisao_alegacao" in contrato
    assert posterior["guarda"]["problemas"]
    assert posterior["guarda"]["fala"] != caso["alvo"]
    assert "contestad" in posterior["guarda"]["fala"]
    assert posterior["preparada"]["fala"] == posterior["guarda"]["fala"]
    assert not posterior["preparada"].get("comandos")


@pytest.mark.parametrize("indice", [0, 1])
@pytest.mark.parametrize("modo", ["normal", "rapido"])
def test_ciclo_instalado_publica_uma_conclusao_com_revisao_sem_efeito(revisao_instalada, indice, modo):
    caso = revisao_instalada[indice]
    ciclo = next(c for c in caso["ciclos_revisao"] if c["modo"] == modo)
    assert ciclo["modelos"]
    assert len(ciclo["textos"]) == 1
    assert ciclo["textos"][0] != caso["alvo"] and "contestad" in ciclo["textos"][0]
    assert "nem confirma uma alternativa" in ciclo["textos"][0]
    assert not ciclo["efeitos"] and not ciclo["plano"].get("comandos")


@pytest.mark.skipif(os.environ.get("LAYLAY_REVISAO_QWEN_REAL") != "1", reason="Inferência local real opcional.")
@pytest.mark.parametrize("indice", [0, 1])
def test_qwen_real_preserva_revisao_na_publicacao_instalada(revisao_instalada, indice):
    geracao = revisao_instalada[indice]["geracoes_reais"][0]
    assert geracao["modelos"] and geracao["transportes"]
    assert all(t["status"] == 200 for t in geracao["transportes"])
    assert len(geracao["textos"]) == 1 and "contestad" in geracao["textos"][0]
    assert "nem confirma uma alternativa" in geracao["textos"][0]
    assert not geracao["plano"].get("comandos")
