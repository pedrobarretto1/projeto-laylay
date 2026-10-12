"""Avaliação social dirigida, expressão causal e identidade emocional."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa
from mente_laylay.personalidade.leitura_social_conversa import elogio_pessoal_direto
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt
from mente_laylay.emocoes.contrato_causal import criar_evento_reconhecimento_social_usuario
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.personalidade.autoria_conversacional import criar_fala_autoral
from mente_laylay.memoria_mental.memoria_confiavel import extrair_aprendizados_pessoais_explicitos
from mente_laylay.cognicao.fundamentacao_factual import extrair_tema_fundamentacao


@pytest.mark.parametrize("texto", [
    "gosto muito de voce", "eu te amo", "mas voce è muito legal",
    "voce è legal lay", "Eu gosto bastante de você", "Lay, tu é incrível",
])
def test_elogio_atual_tem_uma_leitura_social_compartilhada(texto):
    assert elogio_pessoal_direto(texto)
    assert analisar_funcao_comunicativa(texto)["funcao"] == "elogio"


@pytest.mark.parametrize("fala", [
    "Gosto de você também, mesmo que eu não tenha corações para sentir isso.",
    "Isso aqui é um espaço de conversa, não de sentimentos. Não posso sentir ou responder com isso.",
    "Não sou legal — sou só um código que tenta ser útil.",
    "Eu não consigo sentir nada, sou apenas um programa.",
    "Você tá dizendo coisas que não cabem no meu código, e eu não tenho corpo pra sentir isso.",
    "Gosto de você, mesmo que eu não tenha corpos para sentir isso.",
])
def test_identidade_nao_apaga_expressao_emocional_na_conversa(fala):
    resultado = validar_alegacoes_da_fala(fala, plano={"texto_usuario": "eu te amo"})
    assert "capacidade_emocional_negada" in resultado["problemas"]


@pytest.mark.parametrize("fala", [
    "Não tenho emoções humanas, mas posso expressar reações causais.",
    "Não tenho corpo físico e não sinto toque.",
    "Não posso sentir o cheiro dessa comida.",
    "Não estou triste agora, não houve causa para isso.",
    "Você escreveu ‘sou só um código’ como exemplo.",
    "A frase 'sou só um código' é uma redução inadequada da minha personalidade.",
    "Experiência subjetiva não foi demonstrada pelo meu estado emocional.",
])
def test_limite_fisico_citacao_e_incerteza_subjetiva_continuam_validos(fala):
    resultado = validar_alegacoes_da_fala(fala, plano={"texto_usuario": "Como você funciona?"})
    assert "capacidade_emocional_negada" not in resultado["problemas"]


@pytest.mark.parametrize("texto", [
    'Traduza "eu te amo"', "Talvez você seja legal", "Você é legal?",
    "Não acho que você é legal", "Minha amiga é legal", "Você é legal, abra o navegador",
    "Eu te amo, mas não gosto de você", "Ela falou que você é legal",
])
def test_mencao_hipotese_negacao_e_ato_composto_nao_criam_elogio_certo(texto):
    assert not elogio_pessoal_direto(texto)
    assert analisar_funcao_comunicativa(texto)["funcao"] != "elogio"


def _plano_elogio():
    texto = "eu te amo"
    funcao = analisar_funcao_comunicativa(texto)
    evento = criar_evento_reconhecimento_social_usuario(
        turno_id=42, confianca=funcao["confianca"], tipo="elogio_pessoal")
    plano = {"id": 42, "texto_usuario": texto, "autoriza_execucao": False,
             "requer_execucao": False, "evento_emocional_causal": evento}
    plano["contrato_fala"] = construir_contrato_semantico_fala(
        texto, turno={"id": 42}, plano=plano, funcao_comunicativa=funcao)
    return plano


def test_negativa_de_identidade_exige_reparo_natural_sem_virar_aula_tecnica():
    plano = _plano_elogio()
    fala = "Sou só um código e não posso sentir nada."
    validacao = verificar_fala_turno(fala, plano=plano, origem="ia_final")
    assert validacao["aceita"] is False
    assert validacao["acao"] == "reparar"
    assert validacao["contrato_reparo"]["preservar_identidade_emocional"] is True
    assert "carinho" in validacao["fala_contingencia"].casefold()
    assert "causa e evidência" not in validacao["fala_contingencia"].casefold()


@pytest.mark.parametrize("fala", [
    "Ei, não sei se é verdade, mas se é, eu tô aqui pra te escutar.",
    "Obrigada por dizer que sou legal. Mas é só uma brincadeira, eu não tenho corpo.",
    "Agradeço, mas não é nada especial.",
    "Ah, tá bom, mas você tá me elogiando por não ter coragem de dizer não.",
])
def test_ato_afetivo_nao_pode_ser_anulado_ou_virar_acusacao_sem_causa(fala):
    qualidade = avaliar_qualidade_comunicacao("eu te amo", fala, plano=_plano_elogio())
    assert qualidade["aceita"] is False


def test_reacao_afetiva_breve_nao_precisa_copiar_frase_do_usuario():
    qualidade = avaliar_qualidade_comunicacao("eu te amo", "Obrigada pelo carinho. Você me deixou sem jeito.", plano=_plano_elogio())
    assert qualidade["aceita"] is True


def test_critica_nao_pode_ser_reclassificada_como_elogio_pela_autoria():
    texto = "tu è mo chata"
    funcao = analisar_funcao_comunicativa(texto)
    plano = {"id": 43, "texto_usuario": texto, "requer_execucao": False}
    plano["contrato_fala"] = construir_contrato_semantico_fala(
        texto, turno={"id": 43}, plano=plano, funcao_comunicativa=funcao)
    qualidade = avaliar_qualidade_comunicacao(texto,
        "Entendo o que disse. Não é uma crítica, é só um detalhe.", plano=plano)
    assert qualidade["aceita"] is False
    assert "avaliacao_social_anulada" in qualidade["problemas_bloqueantes"]


@pytest.mark.parametrize("texto,fala,problema", [
    ("voce è muito legal", "Obrigada, mas eu não sou nem um pouco legal.", "avaliacao_social_anulada"),
    ("tu è mo chata", "Tu é mo chata, eu entendo. Obrigada por dizer.", "avaliacao_social_alvo_invertido"),
])
def test_atributo_recebido_nao_pode_ser_negado_ou_devolvido_ao_usuario(texto, fala, problema):
    funcao = analisar_funcao_comunicativa(texto)
    plano = {"id": 43, "texto_usuario": texto, "requer_execucao": False}
    plano["contrato_fala"] = construir_contrato_semantico_fala(
        texto, turno={"id": 43}, plano=plano, funcao_comunicativa=funcao)
    qualidade = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
    assert qualidade["aceita"] is False
    assert problema in qualidade["problemas_bloqueantes"]


@pytest.mark.parametrize("texto", ["gosto muito de voce", "Não gosto de você", "amo a Laylay"])
def test_destinataria_do_afeto_nao_vira_preferencia_duravel_ou_tema_externo(texto):
    assert extrair_aprendizados_pessoais_explicitos(texto) == []
    assert extrair_tema_fundamentacao(texto) == ""


def test_gosto_por_musica_continua_sendo_preferencia_e_tema_externo():
    assert extrair_aprendizados_pessoais_explicitos("Gosto muito de rock")
    assert extrair_tema_fundamentacao("Gosto muito de rock") == "rock"


@pytest.mark.parametrize("retorno", [
    '{"fala":"Obrigada pelo carinho. Você me deixou sem jeito.","comandos":[]}',
    '{"fala":"Sou apenas um programa e não sinto nada.","comandos":[]}',
])
def test_principal_reparo_e_autoria_preservam_identidade_sem_criar_comando(retorno):
    plano = _plano_elogio()
    preparada = preparar_resposta_para_execucao(
        "eu te amo", '{"fala":"Não tenho corpo pra sentir isso.","comandos":[]}',
        enviar_mensagem_cb=lambda *_a, **_k: retorno,
        limpar_texto_fala_cb=lambda f: f, fallback_fala="fallback", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano}, log=lambda *_: None)
    assert preparada["comandos"] == []
    assert not validar_alegacoes_da_fala(preparada["fala"], plano=plano)["problemas"]
    assert avaliar_qualidade_comunicacao("eu te amo", preparada["fala"], plano=plano)["aceita"]
    assert "carinho" in preparada["fala"].casefold()


def test_autoria_final_nao_reintroduz_negativa_rejeitada():
    autoria = criar_fala_autoral("eu te amo", "Obrigada pelo carinho.",
        enviar_mensagem=lambda *_a, **_k: "Sou só um código, não posso sentir nada.")
    assert autoria.usada_llm is False
    assert autoria.motivo_fallback == "capacidade_emocional_negada"


@pytest.mark.parametrize("compacto", [True, False])
def test_prompt_publica_somente_expressao_causal_vigente(compacto):
    plano = _plano_elogio()
    contrato = plano["contrato_fala"]
    assert "envergonhada" in formatar_contrato_fala_para_prompt(contrato, compacto=compacto)
    contrato["evento_emocional_causal"]["validade"]["expira_ts"] = 1
    assert "Expressão emocional vigente" not in formatar_contrato_fala_para_prompt(contrato, compacto=compacto)


def test_composicao_instalada_publica_causa_antes_da_expressao_e_rosto(tmp_path):
    root = Path(__file__).resolve().parents[2]
    saida = tmp_path / "receipt.json"
    processo = subprocess.run([
        sys.executable, str(root / "scripts/analises/validar_reacao_social.py"),
        "--saida", str(saida),
    ], cwd=root, env=dict(os.environ, PYTHONIOENCODING="utf-8", GMAIL_USER=" ",
        GMAIL_APP_PASSWORD=" ", LAYLAY_IOT_MODO="simulado"),
        capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert processo.returncode == 0, processo.stderr[-3500:]
    dados = json.loads(saida.read_text(encoding="utf-8"))
    for caso in dados["casos"]:
        assert caso["emocao"] == caso["esperado"], caso["texto"]
        if caso["esperado"] != "calma":
            evento = caso["evento"]
            assert evento["autoriza_execucao"] is False
            assert caso["episodio"] == evento
            assert caso["plano"]["evento_emocional_causal"] == evento
            assert caso["plano"]["contrato_fala"]["evento_emocional_causal"] == evento
            assert caso["plano"]["fundamentacao_factual"] == {}
            assert caso["rosto"][0] == (6 if caso["esperado"] == "envergonhada" else 2)
