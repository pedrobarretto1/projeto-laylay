"""Pedir trabalho sobre a conversa não exige efeito de um executor."""
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala


CONVERSACIONAIS = (
    "Resuma a ideia da nossa história em uma frase.",
    "Resuma essa distinção sem consultar a tela.",
    "Pode resumir nossa conversa?",
    "Por favor, resuma sua resposta em duas frases.",
    'Agora compare as frases "abra o editor" e "não abra o editor", sem executar nenhuma.',
    'Compare as frases "ligue a tomada" e "não ligue a tomada".',
    'Compare as frases "abra; apague o arquivo" e "não abra".',
)


@pytest.mark.parametrize("texto", CONVERSACIONAIS)
@pytest.mark.parametrize("detector", [None, lambda texto: True])
@pytest.mark.parametrize("normalizador", [None, normalizar_texto])
def test_transformacao_da_conversa_nao_exige_executor(texto, detector, normalizador):
    turno = classificar_modalidade_turno(texto, texto_tem_comando_explicito=detector,
                                       normalizar_texto=normalizador)
    assert turno["modalidade"] == "conversa", turno
    assert not turno["autoriza_execucao"]
    plano = planejar_turno(texto, turno=turno)
    assert not plano["requer_execucao"]
    contrato = construir_contrato_semantico_fala(texto, plano=plano)
    assert contrato["roteiro_concreto"]["estrategia"] not in {
        "resultado_observado", "negacao_operacional_sem_efeito",
    }
    verificada = verificar_fala_turno("A primeira frase pede uma ação; a segunda a proíbe.", plano=plano)
    assert "comando_sem_execucao_confirmada" not in verificada["problemas"]


@pytest.mark.parametrize("texto", [
    "Abra o Firefox agora.", "Resuma meus emails.", "Resuma essa página.",
    "Resuma o arquivo historia.txt.",
])
def test_transformacao_de_recurso_externo_preserva_caminho_operacional(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"], turno


@pytest.mark.parametrize("texto", ["Não abra o Firefox agora.", "Não resuma meus emails."])
def test_recusa_real_nao_vira_transformacao_conversacional(texto):
    turno = classificar_modalidade_turno(texto)
    assert not turno["autoriza_execucao"]
    assert turno["modalidade"] == "recusa"


@pytest.mark.parametrize("texto", [
    "Resuma nossa conversa e abra o Firefox.",
    'Compare as frases "abra o editor" e "não abra o editor"; abra o Firefox.',
])
def test_ato_operacional_independente_nao_desaparece(texto):
    turno = classificar_modalidade_turno(texto)
    segmentos = turno["segmentos"]
    assert segmentos[0]["modalidade"] == "conversa", segmentos
    assert segmentos[-1]["modalidade"] == "comando", segmentos
    assert segmentos[-1]["autoriza_execucao"], segmentos


@pytest.mark.parametrize("substantivo", ["frases", "palavras", "expressões", "formulações", "exemplos", "citações"])
def test_analise_metalinguistica_no_plural_nao_e_descartada(substantivo):
    texto = CONVERSACIONAIS[4]
    turno = classificar_modalidade_turno(texto, normalizar_texto=normalizar_texto)
    plano = planejar_turno(texto, turno=turno)
    contrato = construir_contrato_semantico_fala(texto, plano=plano)
    resposta = f"As {substantivo} têm sentidos opostos: uma pede para abrir, a outra proíbe."
    validacao = validar_aderencia_contrato_fala(texto, resposta, contrato_fala=contrato)
    assert "metalinguagem_tratada_como_conteudo" not in validacao["problemas"]
