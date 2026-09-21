"""O reparo de um ato não pode apagar os demais atos já produzidos."""
import json
import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao, compor_reparo_comunicacao
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.validacao_contrato_fala import reconhecimento_estado_pessoal_valido


def plano_para(texto):
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, plano=plano)
    return plano


@pytest.mark.parametrize("texto,conteudo", [
    ("estou bem, existe painel solar para arduino?", "Sim, é possível usar energia solar com alimentação regulada adequada à placa."),
    ("estou bem, qual a diferença entre lista e tupla?", "Uma lista é mutável; uma tupla é imutável."),
])
def test_reparo_social_preserva_resposta_tematica_literal(texto, conteudo):
    plano = plano_para(texto)
    chamadas = []
    def modelo(mensagens, **kwargs):
        chamadas.append(mensagens)
        return json.dumps({"fala": "Que bom saber!", "comandos": []})
    resultado = preparar_resposta_para_execucao(texto,
        json.dumps({"fala": conteudo, "comandos": []}), enviar_mensagem_cb=modelo,
        limpar_texto_fala_cb=lambda x: x, fallback_fala="fallback", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano, "mensagens": []}, log=lambda x: None)
    assert len(chamadas) == 1
    assert resultado["fala"] == "Que bom saber! " + conteudo
    assert resultado["comandos"] == []
    payload = json.loads(chamadas[0][-1]["content"])
    assert payload["escopo"] == "reconhecimento_estado_pessoal"
    assert conteudo not in json.dumps(payload, ensure_ascii=False)


def test_falha_operacional_nao_e_elegivel_para_reparo_parcial():
    texto = "estou bem, existe painel solar para arduino?"
    fala = "Abri o navegador para você."
    avaliacao = avaliar_qualidade_comunicacao(texto, fala, plano=plano_para(texto))
    assert "execucao_alegada_sem_resultado" in validar_alegacoes_da_fala(fala, plano=plano_para(texto))["problemas"]
    assert avaliacao["contrato_reparo"].get("escopo") != "reconhecimento_estado_pessoal"


def test_pergunta_sobre_assistente_nao_usa_reparo_do_estado_do_usuario():
    texto = "como você está?"
    avaliacao = avaliar_qualidade_comunicacao(texto, "Uma lista é mutável.", plano=plano_para(texto))
    assert avaliacao["contrato_reparo"].get("escopo") != "reconhecimento_estado_pessoal"


@pytest.mark.parametrize("prefixo", ["Estou bem, obrigada!", "Que bom, abri o navegador!", "Que bom! Quer ajuda?", ""])
def test_fragmento_invalido_nao_se_incorpora_ao_rascunho(prefixo):
    texto = "estou bem, qual a diferença entre lista e tupla?"
    original = "Uma lista é mutável; uma tupla é imutável."
    plano = plano_para(texto)
    avaliacao = avaliar_qualidade_comunicacao(texto, original, plano=plano)
    assert avaliacao["contrato_reparo"]["escopo"] == "reconhecimento_estado_pessoal"
    assert compor_reparo_comunicacao(original, prefixo, avaliacao, plano=plano) == ""


def test_reparo_nao_pode_ser_aplicado_sobre_outro_rascunho():
    texto = "estou bem, existe painel solar para arduino?"
    original = "Sim, é possível usar energia solar com alimentação regulada adequada à placa."
    plano = plano_para(texto)
    avaliacao = avaliar_qualidade_comunicacao(texto, original, plano=plano)
    assert compor_reparo_comunicacao("Outro conteúdo.", "Que bom saber!", avaliacao, plano=plano) == ""


@pytest.mark.parametrize("fala", [
    "Ah, bom que você está bem.",
    "Fico contente que você está bem!",
])
def test_reconhecimento_explicito_do_usuario_nao_exige_bordao(fala):
    assert reconhecimento_estado_pessoal_valido(fala, "bem")


@pytest.mark.parametrize("fala", [
    "Você não está bem.",
    "Não acredito que você está bem.",
    "Estou bem.",
])
def test_negacao_e_estado_da_assistente_nao_reconhecem_estado_do_usuario(fala):
    assert not reconhecimento_estado_pessoal_valido(fala, "bem")


def test_reparo_nao_introduz_comandos_na_resposta_composta():
    texto = "estou bem, qual a diferença entre lista e tupla?"
    resultado = preparar_resposta_para_execucao(
        texto, json.dumps({"fala": "Uma lista é mutável; uma tupla é imutável.", "comandos": []}),
        enviar_mensagem_cb=lambda *args, **kwargs: json.dumps({
            "fala": "Que bom saber!", "comandos": [{"acao": "OPEN_URL", "alvo": "https://example.com"}],
        }),
        limpar_texto_fala_cb=lambda x: x, fallback_fala="fallback", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano_para(texto), "mensagens": []}, log=lambda x: None,
    )
    assert resultado["comandos"] == []
    assert resultado["fala"] != "Que bom saber! Uma lista é mutável; uma tupla é imutável."


@pytest.mark.parametrize("texto,prefixo", [
    ("estou bem, qual a diferença entre lista e tupla?", "Que bom saber! "),
    ("qual a diferença entre lista e tupla?", ""),
])
def test_verificacao_final_nao_apaga_conteudo_por_proporcao(texto, prefixo):
    fala = prefixo + (
        "Uma lista é mutável. Você pode adicionar itens. Uma tupla é imutável. "
        "Atenção: objetos mutáveis contidos numa tupla ainda podem mudar."
    )
    resultado = verificar_fala_turno(fala, plano=plano_para(texto))
    assert resultado["aceita"]
    assert resultado["fala"] == fala
