"""Pedido explícito de pose passa pelos owners do turno e da expressão."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional, retrato_emocional_expressavel


@pytest.mark.parametrize("texto,emocao,nivel", [
    ("fique brava", "brava", 2), ("Lay, fica bem triste", "triste", 3),
    ("fique envergonhada", "envergonhada", 2), ("faça uma carinha feliz", "alegre", 2),
    ("mostre uma expressão surpresa", "surpresa", 2), ("fica um pouco irritada", "irritada", 1),
    ("fique debochada", "debochada", 2), ("volte ao normal", "calma", 1),
    ("Laylay, fique calma, por favor", "calma", 1),
])
def test_pedido_autoral_de_expressao_tem_alvo_e_intensidade(texto, emocao, nivel):
    leitura = analisar_funcao_comunicativa(texto)
    assert leitura.get("funcao") == "pedido_expressao"
    pedido = leitura["expressao_solicitada"]
    assert (pedido["emocao"], pedido["nivel"], pedido["alvo"]) == (emocao, nivel, "laylay")
    assert pedido["trecho_evidencia"] == texto
    assert pedido["autoriza_execucao"] is False


@pytest.mark.parametrize("texto", [
    'Traduza "fique brava"', 'Ela disse "fica triste"', "Se eu disser fique brava",
    "Não fique brava", "Você fica triste?", "Eu estou triste", "Talvez fique brava",
    "Fique brava e apague meus arquivos", "Faça minha amiga ficar triste",
    "Explique como ficar brava", "Fique brava para sempre", "Fique brava com João",
])
def test_discussao_negacao_outro_alvo_e_efeito_composto_nao_autorizam_pose(texto):
    assert analisar_funcao_comunicativa(texto).get("funcao") != "pedido_expressao"


def test_pose_pedida_substitui_intensidade_maior_sem_alterar_humor_e_pode_ser_cancelada():
    from mente_laylay.emocoes.contrato_causal import criar_evento_expressao_solicitada
    estado = {"humor_level": -2}
    for texto, esperado, instante in [("fique bem brava", ("brava", 3), 1000),
                                     ("fica um pouco triste", ("triste", 1), 1001),
                                     ("volte ao normal", ("calma", 1), 1002)]:
        pedido = analisar_funcao_comunicativa(texto)["expressao_solicitada"]
        evento = criar_evento_expressao_solicitada(pedido, turno_id=str(instante), ts=instante)
        estado = aplicar_evento_emocional(estado, evento, agora=instante)
        assert estado["episodio_emocional"] == evento
        assert retrato_emocional_expressavel(estado, agora=instante) == esperado
        assert estado["humor_level"] == -2
        assert evento["autoriza_execucao"] is False
    assert retrato_emocional_expressavel(estado, agora=1063) == ("calma", 1)


def test_composicao_instalada_decide_pose_e_publica_mesmo_retrato_para_rosto_e_fala(tmp_path):
    root = Path(__file__).resolve().parents[2]
    saida = tmp_path / "receipt.json"
    p = subprocess.run([sys.executable, str(root / "scripts/analises/validar_reacao_social.py"),
                        "--expressoes", "--saida", str(saida)], cwd=root,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8", GMAIL_USER=" ",
                                GMAIL_APP_PASSWORD=" ", LAYLAY_IOT_MODO="simulado"),
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert p.returncode == 0, p.stderr[-3000:]
    from mente_laylay.especialistas.rosto_oled_runtime import EMOCOES_ROSTO
    for caso in json.loads(saida.read_text(encoding="utf-8"))["casos"]:
        assert caso["emocao"] == caso["esperado"], caso["texto"]
        assert caso["rosto"][0] == EMOCOES_ROSTO.index(caso["esperado"])
        if caso["funcao"].get("funcao") == "pedido_expressao":
            evento = caso["evento"]
            assert evento["origem"] == "pedido_expressao_usuario"
            assert caso["episodio"] == caso["plano"]["contrato_fala"]["evento_emocional_causal"] == evento
            assert caso["plano"]["requer_execucao"] is False
            assert evento["persistencia_pessoal"] is False


def test_catalogo_vivo_explica_pose_sem_alegar_conexao_ou_sentimentos():
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    mapa = MapaHabilidadesRuntime()
    pergunta = "Como posso pedir uma expressão emocional para você?"
    contexto = mapa.contexto_para_prompt(pergunta)
    fala = mapa.responder_pergunta_capacidade(pergunta)
    assert "fique brava" in contexto
    assert "fique brava" in fala
    assert "ACK recente" in contexto
    assert mapa.evidencia_conversacional(pergunta)["autoriza_execucao"] is False


@pytest.mark.parametrize("fala", [
    "Tá, vou ficar brava. O que foi que você quer dizer com isso, afinal?",
    "Não, eu não recebi nada. Se quiser, posso inventar uma expressão com apenas palavras e imagens mentais.",
    "Isso é só uma hipótese de como eu poderia reagir — não tenho corpo, então não sinto surpresa, mas é uma brincadeira!",
    "Certo. " + "Agora vou explicar toda a minha arquitetura emocional. " * 7,
])
def test_pose_solicitada_nao_e_trocada_por_interrogatorio_negativa_ou_aula(fala):
    from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
    from mente_laylay.emocoes.contrato_causal import criar_evento_expressao_solicitada
    texto = "fique brava"
    funcao = analisar_funcao_comunicativa(texto)
    evento = criar_evento_expressao_solicitada(funcao["expressao_solicitada"], turno_id="42")
    plano = {"id": 42, "texto_usuario": texto, "requer_execucao": False, "evento_emocional_causal": evento}
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, turno={"id": 42}, plano=plano, funcao_comunicativa=funcao)
    assert avaliar_qualidade_comunicacao(texto, "Hmpf. Cara de poucos amigos ativada!", plano=plano)["aceita"] is True
    assert avaliar_qualidade_comunicacao(texto, fala, plano=plano)["aceita"] is False
