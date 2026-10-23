"""Referir uma fala para entendê-la não pede uma auditoria de execução."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada, formatar_evidencia_da_fala
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala


def contrato(texto: str, anterior: str, resultado: bool = False) -> dict:
    registro = registrar_fala_observada(None, ocorrencia_id="fala-observada", turno_id="anterior",
        fala=anterior, canal="texto_publicado", resultados=(ResultadoAcao(
            intent="IOT_CONTROL", alvo="lâmpada", status="confirmado", executou=True,
            confirmado=True, origem="executor", id_solicitacao="efeito-anterior"),) if resultado else ())
    mente = {"ultima_resposta": anterior, "continuidade_fala_ts": time.time(),
             "registro_semantico": registro}
    antes = deepcopy(mente)
    turno = classificar_modalidade_turno(texto)
    plano = {"id": turno["id"], "texto_usuario": texto, "comandos": [], "requer_execucao": False}
    c = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    assert mente == antes
    assert c["autoriza_execucao"] is False and turno["autoriza_execucao"] is False
    return c


@pytest.mark.parametrize("texto", [
    "como assim?", "O que você quis dizer?", "não entendi", "explica melhor",
    "explica isso de um jeito simples", "não ficou claro",
])
@pytest.mark.parametrize("anterior", [
    "Faltou uma peça aí. Me dá mais um detalhe pra eu não inventar moda?",
    "Podemos conversar sobre sua aula.", "Posso explicar as opções da lâmpada.",
])
@pytest.mark.parametrize("resultado", [False, True])
def test_esclarecimento_preserva_sentido_e_nao_impoe_auditoria(texto, anterior, resultado):
    c = contrato(texto, anterior, resultado)
    assert "esclarecimento" in c["atos"]
    assert c["fala_anterior_relevante"] == anterior
    assert "evidencia_fala_historica" not in c, "a fonte existe, mas o ato pede sentido, não prova de efeito"
    assert "explicacao_ocorrencia" not in c


@pytest.mark.parametrize("texto", [
    "Por que você disse isso?",
    "Por que você falou isso?",
    "Não entendi por que você disse isso?",
    'Qual o motivo de você dizer "Registrei o resultado do pedido."?',
])
def test_pedido_causal_preserva_auditoria_sem_inventar_justificativa(texto):
    c = contrato(texto, "Registrei o resultado do pedido.", True)
    assert "evidencia_fala_historica" in c


@pytest.mark.parametrize("texto", ["como assim?", "explica melhor", "o que você quis dizer?"])
@pytest.mark.parametrize("com_receipt", [False, True])
def test_projecao_de_esclarecimento_leva_texto_sem_impor_resultado_operacional(texto, com_receipt):
    anterior = "Falta uma leitura atual para conferir o estado do computador."
    resultados = (ResultadoAcao(intent="IOT_CONTROL", alvo="lâmpada", status="desligado",
        executou=True, confirmado=True, origem="executor", id_solicitacao="receipt-antigo"),) if com_receipt else ()
    registro = registrar_fala_observada(None, ocorrencia_id="entrega", turno_id="origem",
        fala=anterior, canal="texto_publicado", resultados=resultados)
    turno = classificar_modalidade_turno(texto)
    mente = {"ultima_resposta": anterior, "continuidade_fala_ts": time.time(),
             "registro_semantico": registro, "turno_atual": turno}
    mente["contrato_fala_atual"] = construir_contrato_semantico_fala(texto, turno=turno,
        plano={"id": turno["id"], "texto_usuario": texto}, mente=mente)
    antes = deepcopy(registro)
    prompt = formatar_evidencia_da_fala(texto, mente)
    assert "REFERENTE TEXTUAL DESTE ESCLARECIMENTO" in prompt
    assert anterior in prompt
    assert '"resultados"' not in prompt and "receipt-antigo" not in prompt
    assert registro == antes


@pytest.mark.parametrize("anterior", [
    "Ainda não tenho uma leitura atual desse estado para responder com segurança.",
    "A explicação usa primeiro o exemplo e depois mostra a conclusão.",
    "Podemos conversar sobre o que aconteceu na sua aula.",
])
def test_repeticao_literal_nao_satisfaz_a_obrigacao_de_esclarecer(anterior):
    c = contrato("como assim?", anterior)
    r = validar_aderencia_contrato_fala("como assim?", anterior, contrato_fala=c, turno_id=c["turno_id"])
    assert "esclarecimento_sem_explicacao" in r["problemas"]


@pytest.fixture(scope="module")
def conversa_instalada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("sentido_fala") / "coleta"
    codigo = (
        "from pathlib import Path; "
        "from scripts.analises.sonda_conversa_continua import coletar; "
        "coletar(Path(__import__('sys').argv[1]),modelo_real=False)"
    )
    p = subprocess.run([sys.executable, "-c", codigo, str(pasta)], cwd=Path(__file__).resolve().parents[2],
                       capture_output=True, text=True, encoding="utf-8", timeout=90)
    assert p.returncode == 0, p.stdout + p.stderr
    return json.loads((pasta / "conversa.json").read_text(encoding="utf-8"))


def test_conversa_continua_instalada_nao_substitui_esclarecimento_por_receipt(conversa_instalada):
    r = conversa_instalada["resultados"]
    assert len(r) == 6
    assert all(not t["executores_recusados"] for t in r)
    assert all(t["prioridades"] == [{"texto": t["texto"], "tratado": False}] for t in r)
    assert all(len(t["respostas"]) == 1 for t in r)
    assert len(r[-1]["historico_antes"]) > len(r[0]["historico_antes"])
    c = r[-1]["contrato"]
    assert "esclarecimento" in c["atos"]
    assert "evidencia_fala_historica" not in c, "primeira divergência: contrato escolheu auditoria"
    assert "resultado operacional" not in r[-1]["respostas"][0]
