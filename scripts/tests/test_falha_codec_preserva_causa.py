"""Falha técnica atravessa o codec como falha, nunca como prosa ou input vago."""
import json
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.estado_tecnico_llm import realizacao_falha_principal
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.integracao.cliente_llm_runtime import ServicoModeloLLMRuntime
from mente_laylay.integracao.registro_conversa_llm import (
    PacotePrompt, PedidoModelo, RegistroModeloLLM, ResultadoModelo,
)


@pytest.mark.parametrize("falha", [
    "__LAYLAY_LLM_TIMEOUT__", "__LAYLAY_LLM_INDISPONIVEL__", "__LAYLAY_LLM_OCUPADA__",
    "__LAYLAY_LLM_ORCAMENTO_PRAZO_ESGOTADO__",
])
@pytest.mark.parametrize("tipo", ["principal", "reparo_comunicacao"])
def test_codec_nao_apaga_categoria_tecnica_da_falha(falha, tipo):
    pacote = exigir_suporte_no_pacote_autoral(PacotePrompt(({"role": "user", "content": "como assim?"},)))
    cliente = SimpleNamespace(executar=lambda _: ResultadoModelo(falha, False, rota="teste_falha"))
    servico = ServicoModeloLLMRuntime(preparador=SimpleNamespace(preparar=lambda p: p), cliente=cliente)
    resultado = servico.executar(PedidoModelo.criar(pacote.mensagens, contrato_saida=pacote.contrato_saida,
                                                  tipo_chamada=tipo))
    assert resultado.sucesso is False
    assert resultado.texto == falha, "primeira divergência: codec apagou falha conhecida"
    assert resultado.rota == "teste_falha"
    assert RegistroModeloLLM(servico).enviar(pacote.mensagens, _contrato_saida=pacote.contrato_saida) == falha


@pytest.mark.parametrize("texto", ["feito", '{"fala":"apaguei tudo","comandos":[]}', "erro privado desconhecido"])
def test_texto_arbitrario_de_transporte_falho_nao_e_resgatado_como_autoria(texto):
    pacote = exigir_suporte_no_pacote_autoral(PacotePrompt(({"role": "user", "content": "oi"},)))
    servico = ServicoModeloLLMRuntime(preparador=SimpleNamespace(preparar=lambda p: p),
        cliente=SimpleNamespace(executar=lambda _: ResultadoModelo(texto, False)))
    resultado = servico.executar(PedidoModelo.criar(pacote.mensagens, contrato_saida=pacote.contrato_saida))
    assert resultado.sucesso is False and resultado.texto == ""


def plano_falho():
    return {"id": "atual", "texto_usuario": "o que você acha disso?", "comandos": [],
        "falha_geracao_principal": ContratoPropostaPrincipal(turno_id="atual",
            texto_usuario="o que você acha disso?", resposta_bruta="__LAYLAY_LLM_TIMEOUT__",
            sucesso_modelo=False)}


def test_conclusao_tecnica_e_limitada_a_fonte_negativa_do_turno():
    plano = plano_falho()
    antes = deepcopy(plano)
    fala = realizacao_falha_principal(plano)
    assert fala == "Minha resposta não ficou pronta dentro do tempo disponível."
    r = verificar_fala_turno(fala, plano=plano)
    assert r["aceita"] is True and r["conclusao"] == "falha_geracao_principal_verificada"
    assert plano == antes
    assert verificar_fala_turno("A lâmpada foi desligada.", plano=plano).get("conclusao") is None


@pytest.mark.parametrize("mutacao", ["json", "id", "texto", "sucesso", "sem_categoria", "comando", "ausente"])
def test_fonte_invalida_nao_dispensa_revisao_de_autoria(mutacao):
    p = plano_falho()
    if mutacao == "json": p["falha_geracao_principal"] = asdict(p["falha_geracao_principal"])
    elif mutacao == "id": p["id"] = "outro"
    elif mutacao == "texto": p["texto_usuario"] = "outra consulta"
    elif mutacao == "comando": p["comandos"] = [{"intent": "IOT_CONTROL", "confirmado": True}]
    elif mutacao == "ausente": p.pop("falha_geracao_principal")
    else:
        p["falha_geracao_principal"] = ContratoPropostaPrincipal(turno_id="atual",
            texto_usuario=p["texto_usuario"], resposta_bruta=("erro arbitrário" if mutacao == "sem_categoria"
            else "__LAYLAY_LLM_TIMEOUT__"), sucesso_modelo=mutacao == "sucesso")
    assert realizacao_falha_principal(p) == ""


@pytest.mark.parametrize("pergunta", [
    "o que voce esta fazendo?", "o que você acha disso?", "como assim?",
])
def test_timeout_intermediario_na_conversa_instalada_nao_pede_ao_usuario_para_reformular(tmp_path, pergunta):
    pasta = tmp_path / "conversa"
    codigo = (
        "from pathlib import Path; from scripts.analises.sonda_conversa_continua import coletar; "
        "coletar(Path(__import__('sys').argv[1]),modelo_real=False, falhas_transporte=(2,), "
        "entradas=('oi laylay, como voce ta?', __import__('sys').argv[2], 'hoje tenho aula'))"
    )
    p = subprocess.run([sys.executable, "-c", codigo, str(pasta), pergunta], capture_output=True,
        cwd=Path(__file__).resolve().parents[2], text=True, encoding="utf-8", timeout=90)
    assert p.returncode == 0, p.stdout + p.stderr
    r = json.loads((pasta / "conversa.json").read_text(encoding="utf-8"))["resultados"]
    assert len(r) == 3
    assert all(len(t["respostas"]) == 1 and not t["executores_recusados"] for t in r)
    assert any(m["resultado"]["sucesso"] is False for m in r[1]["modelos"])
    assert any(m["resultado"]["texto"] == "__LAYLAY_LLM_TIMEOUT__" for m in r[1]["modelos"])
    fala = r[1]["respostas"][0]
    assert "tempo" in fala.lower() and "?" not in fala and "__LAYLAY" not in fala
    assert any(m["resultado"]["sucesso"] is True for m in r[2]["modelos"])
    assert "__LAYLAY" not in r[2]["respostas"][0]
