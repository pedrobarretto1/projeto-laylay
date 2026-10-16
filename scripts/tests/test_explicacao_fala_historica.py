"""Resultado, causa e estágio são dimensões independentes em qualquer domínio."""
from copy import deepcopy
import json
import time

import pytest

from mente_laylay.cognicao.contrato_fala import (
    construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt,
)
from mente_laylay.cognicao.explicacao_fala_historica import (
    avaliar_fala_historica, realizacoes_fala_historica,
)
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
from mente_laylay.memoria_mental.registro_semantico import (
    registrar_fala_observada, recuperar_evidencia_da_fala,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


def plano_historico(intent="IOT_CONTROL", alvo="lâmpada", executou=True, confirmado=True):
    fonte = registrar_fala_observada(None, ocorrencia_id="fala-1", turno_id="origem-1",
        fala="Registrei o resultado do pedido.", canal="texto_publicado", resultados=(
            ResultadoAcao(intent=intent, alvo=alvo, status="resultado", executou=executou,
                confirmado=confirmado, origem="executor", id_solicitacao="resultado-1",
                evidencia_confirmacao="critério de confirmação disponível"),))
    texto = 'Quando disse "Registrei o resultado do pedido.", por que aconteceu?'
    plano = {"id": "consulta-1", "texto_usuario": texto, "autoriza_execucao": False,
             "requer_execucao": False, "comandos": []}
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto,
        turno={"id": "consulta-1", "modalidade": "deliberacao", "autoriza_execucao": False},
        plano=plano, mente={"registro_semantico": fonte})
    return plano


@pytest.mark.parametrize("intent,alvo", [
    ("IOT_CONTROL", "lâmpada"), ("PLAYLIST_PLAY", "jazz"),
    ("CREATE_FILE", "relatorio.txt"), ("EMAIL_READ", "mensagem"),
])
def test_contrato_de_resultados_e_compartilhado_e_nao_inventa_causa(intent, alvo):
    plano = plano_historico(intent, alvo)
    evidencia = plano["contrato_fala"]["evidencia_fala_historica"]
    assert evidencia["falas"][0]["resultados"][0]["intent"] == intent
    for fala in realizacoes_fala_historica(evidencia):
        assert alvo in fala and "execução registrada, efeito confirmado" in fala
        assert "não informa a causa nem a etapa de processamento" in fala
        assert "critério de confirmação disponível" not in fala
        assert "não comprova o estado atual" in fala
        assert not validar_alegacoes_da_fala(fala, plano=plano)["problemas"]
        assert avaliar_qualidade_comunicacao(plano["texto_usuario"], fala, plano=plano)["aceita"]
        assert validar_aderencia_contrato_fala(plano["texto_usuario"], fala,
            contrato_fala=plano["contrato_fala"], turno_id=plano["id"])["aceita"]
    assert not plano["comandos"] and plano["autoriza_execucao"] is False


@pytest.mark.parametrize("fala", [
    "A ação falhou porque o comando não foi processado.",
    "O provedor estava fora do ar.",
    "O arquivo estava protegido por outro processo.",
    "Eu não executei nada.",
    "A lâmpada acendeu e continua ligada agora.",
])
def test_prosa_livre_sem_cobertura_nao_se_autovalida_nem_vira_negacao(fala):
    plano = plano_historico()
    antes = deepcopy(plano)
    resultado = avaliar_fala_historica(fala, plano=plano)
    assert resultado["problemas"] == ["explicacao_historica_sem_cobertura"]
    assert resultado["prova_semantica_livre"] is False
    assert "efeito confirmado" in resultado["fala"]
    assert not avaliar_qualidade_comunicacao(plano["texto_usuario"], fala, plano=plano)["aceita"]
    assert not validar_aderencia_contrato_fala(plano["texto_usuario"], fala,
        contrato_fala=plano["contrato_fala"], turno_id=plano["id"])["aceita"]
    assert plano == antes


def test_confirmacao_desconhecida_nao_vira_falha_ou_ausencia_de_execucao():
    plano = plano_historico(executou=True, confirmado=None)
    resultado = avaliar_fala_historica("Foi um erro de conexão.", plano=plano)
    assert "execução registrada, confirmação desconhecida" in resultado["fala"]
    assert "execução não concluída" not in resultado["fala"]


def test_estado_ja_satisfeito_confirmado_nao_exige_nova_execucao():
    plano = plano_historico(executou=False, confirmado=True)
    resultado = avaliar_fala_historica("Não foi feito nada.", plano=plano)
    assert resultado["fonte_valida"] is True
    assert "sem nova execução registrada, efeito confirmado" in resultado["fala"]


def test_receipt_idempotente_nao_apaga_confirmacao_de_outra_etapa():
    plano = plano_historico()
    resultados = plano["contrato_fala"]["evidencia_fala_historica"]["falas"][0]["resultados"]
    idempotente = {**resultados[0], "id_solicitacao": "ja-satisfeito", "alvo": "segunda lâmpada",
                  "executou": False, "confirmado": True, "status": "ja_satisfeito"}
    resultados.append(idempotente)
    resultado = avaliar_fala_historica("Tudo falhou.", plano=plano)
    assert resultado["fonte_valida"] is True
    assert 'alvo "lâmpada": execução registrada, efeito confirmado' in resultado["fala"]
    assert 'alvo "segunda lâmpada": sem nova execução registrada, efeito confirmado' in resultado["fala"]


@pytest.mark.parametrize("mudanca", ["expirou", "futuro", "turno", "texto", "comando", "autoridade", "fonte", "booleano", "duplicado"])
def test_fonte_ou_escopo_invalidos_falham_fechado_sem_negar_efeitos(mudanca):
    plano = plano_historico()
    fonte = plano["contrato_fala"]["evidencia_fala_historica"]["falas"][0]
    if mudanca == "expirou": fonte["ts"] = time.time() - 901
    elif mudanca == "futuro": fonte["ts"] = time.time() + 100
    elif mudanca == "turno": plano["id"] = "outro-turno"
    elif mudanca == "texto": plano["texto_usuario"] = "outro pedido"
    elif mudanca == "comando": plano["comandos"] = [{"intent": "IOT_CONTROL"}]
    elif mudanca == "autoridade": plano["autoriza_execucao"] = True
    elif mudanca == "fonte": fonte["resultados"][0]["origem"] = "llm"
    elif mudanca == "booleano": fonte["resultados"][0]["confirmado"] = "true"
    elif mudanca == "duplicado": fonte["resultados"].append(deepcopy(fonte["resultados"][0]))
    resultado = avaliar_fala_historica("Tudo confirmado.", plano=plano)
    assert resultado["problemas"] == ["evidencia_historica_invalida"]
    assert "Não tenho evidência histórica válida" in resultado["fala"]
    assert resultado["autoriza_execucao"] is False
    assert not avaliar_fala_historica(resultado["fala"], plano=plano)["problemas"]


def test_ambiguidade_e_receipt_ausente_nao_emprestam_o_ultimo_efeito():
    plano = plano_historico()
    evidencia = plano["contrato_fala"]["evidencia_fala_historica"]
    outra = deepcopy(evidencia["falas"][0])
    outra["id"], outra["turno_id"] = "fala-2", "origem-2"
    evidencia["falas"].append(outra)
    evidencia["referencia_ambigua"] = True
    assert "qual delas" in avaliar_fala_historica("A luz foi ligada.", plano=plano)["fala"]
    evidencia["falas"].pop()
    evidencia["referencia_ambigua"] = False
    evidencia["falas"][0]["resultados"] = []
    fala = avaliar_fala_historica("Não executei nada.", plano=plano)["fala"]
    assert "não prova que uma ação aconteceu nem que deixou de acontecer" in fala


def test_roteiros_normal_e_rapido_apresentam_as_mesmas_realizacoes():
    contrato = plano_historico()["contrato_fala"]
    assert formatar_contrato_fala_para_prompt(contrato) == formatar_contrato_fala_para_prompt(contrato, compacto=True)
    for fala in realizacoes_fala_historica(contrato["evidencia_fala_historica"]):
        assert json.dumps(fala, ensure_ascii=False) in formatar_contrato_fala_para_prompt(contrato)


def test_outro_assunto_ou_comando_atual_nao_entra_no_escopo_historico():
    base = plano_historico()
    evidencia = base["contrato_fala"]["evidencia_fala_historica"]
    registro = {"falas_observadas": evidencia["falas"]}
    assert not recuperar_evidencia_da_fala("Qual sua cor preferida?", {"registro_semantico": registro})
    contrato = construir_contrato_semantico_fala(base["texto_usuario"],
        turno={"id": "atual", "modalidade": "imperativo", "autoriza_execucao": True},
        plano={"id": "atual", "requer_execucao": True}, mente={"registro_semantico": registro})
    assert "evidencia_fala_historica" not in contrato


def test_preparacao_registra_autocorrecao_sem_tentar_provar_causa_por_outra_geracao():
    from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
    plano = plano_historico()
    logs = []
    def modelo_nao_deve_ser_chamado(*args, **kwargs):
        pytest.fail("Uma nova proposta da LLM não prova a causa ausente.")
    resposta = preparar_resposta_para_execucao(plano["texto_usuario"],
        json.dumps({"fala": "A conexão caiu e o serviço parou.", "comandos": []}),
        enviar_mensagem_cb=modelo_nao_deve_ser_chamado,
        limpar_texto_fala_cb=lambda fala: fala, fallback_fala="", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano}, log=logs.append)
    assert resposta["autocorrigida"] is True
    assert not resposta["comandos"]
    assert "execução registrada, efeito confirmado" in resposta["fala"]
    assert any("explicacao_historica_sem_cobertura" in log for log in logs)
