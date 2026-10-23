"""Opinião preserva o tema; rejeição de rascunho não acusa lacuna do usuário."""
import json

import pytest

from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.qualidade_comunicacao import contingencia_comunicacao
from mente_laylay.personalidade.contingencia_natural import fala_falha_geracao


@pytest.mark.parametrize("compacto", [True, False])
@pytest.mark.parametrize("texto", ["o que você acha disso?", "você prefere rock ou jazz?"])
def test_opiniao_nao_recebe_ordem_de_explicar_fala_anterior(compacto, texto):
    turno = classificar_modalidade_turno(texto)
    plano = {"id": turno["id"], "texto_usuario": texto, "comandos": [], "requer_execucao": False}
    anterior = "Eu prefiro jazz, porque gosto da improvisação."
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano,
                                               mente={"ultima_resposta": anterior})
    assert "opiniao" in contrato["atos"]
    prompt = formatar_contrato_fala_para_prompt(contrato, compacto=compacto)
    assert anterior in prompt, "posição anterior permanece contexto de consistência"
    assert "Explique esta fala anterior:" not in prompt
    assert "Fala anterior que precisa ser explicada:" not in prompt


@pytest.mark.parametrize("compacto", [True, False])
def test_esclarecimento_continua_recebendo_a_fala_cujo_sentido_foi_pedido(compacto):
    texto = "como assim?"
    turno = classificar_modalidade_turno(texto)
    anterior = "Precisamos observar esse estado antes de descrevê-lo."
    contrato = construir_contrato_semantico_fala(texto, turno=turno,
        plano={"id": turno["id"], "texto_usuario": texto, "comandos": []}, mente={"ultima_resposta": anterior})
    prompt = formatar_contrato_fala_para_prompt(contrato, compacto=compacto)
    assert anterior in prompt
    assert "Explique esta fala anterior:" in prompt or "Fala anterior que precisa ser explicada:" in prompt


@pytest.mark.parametrize("alvo", ["os exercícios", "as notas", "a playlist", "o código"])
def test_realizacao_local_ausente_nao_desativa_o_reparo_do_rascunho(alvo):
    texto = "mas consegui terminar " + alvo
    turno = classificar_modalidade_turno(texto)
    plano = {"id": turno["id"], "texto_usuario": texto, "comandos": [], "requer_execucao": False}
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano,
        funcao_comunicativa={"funcao": "conquista"})
    reparada = "Você contou que conseguiu terminar " + alvo + ". Que bom!"
    def gerar(*_args, **_kwargs):
        return json.dumps({"fala": reparada, "comandos": []}, ensure_ascii=False)
    resposta = preparar_resposta_para_execucao(texto,
        json.dumps({"fala": "Isso é só um passo, mas é uma conquista.", "comandos": []}, ensure_ascii=False),
        enviar_mensagem_cb=gerar, limpar_texto_fala_cb=lambda v: v, fallback_fala="fallback",
        memoria_sqlite=None, contexto_contingencia={"plano_turno_atual": plano},
        contexto_comunicacao={"plano_turno": plano, "mensagens": []}, log=lambda *_a: None)
    assert resposta["fala"] == reparada
    assert resposta["comandos"] == []


@pytest.mark.parametrize("texto", ["mas consegui terminar os exercícios", "o que você acha disso?"])
def test_causa_explicita_de_rejeicao_nao_vira_falta_de_contexto_do_usuario(texto):
    fala = contingencia_comunicacao(texto, motivo_falha="conquista_minimizada_sem_base")
    assert fala == fala_falha_geracao("reparo_rejeitado")
