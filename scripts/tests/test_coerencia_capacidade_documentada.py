"""RED arquitetural: disponibilidade não é prova de efeito nem incapacidade.

Negativas gerais cobertas devem ser confrontadas com o documento do turno.
Controles preservam indisponibilidade real e limites de observação do efeito.
Sem transporte LLM, execução ou alteração do catálogo de produção.
"""
import json

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.fundamentacao_factual import extrair_titulos_citados
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao, montar_mensagens_reparo_comunicacao,
)
from tests.test_catalogo_referencias_aplicativos import mapa_da_composicao
from tests.test_explicacao_capacidades_sem_execucao import preparar
from tests.test_reparo_preserva_objetivo_turno import plano_explicacao


CASOS = [
    (
        "como eu poderia retomar a música?", "musica",
        "A Laylay não controla o áudio diretamente, então o dispositivo ou app "
        "que está tocando a música precisa ser instruído a retomar o playback.",
        "Posso enviar o pedido de retomada, mas não garantir que o áudio mudou.",
    ),
    (
        "como eu poderia abrir a calculadora?", "sistema",
        "Não consigo abrir programas no seu computador.",
        "Posso tentar abrir o programa, mas preciso verificar a janela antes de confirmar.",
    ),
    (
        "como eu poderia ligar a lâmpada?", "iot",
        "Não consigo controlar dispositivos inteligentes.",
        "Posso enviar o comando, mas preciso reler o dispositivo antes de confirmar.",
    ),
    (
        "como eu poderia fechar a aba?", "navegador",
        "Não consigo fechar abas do navegador.",
        "Posso tentar fechar a aba, mas não garantir o resultado antes de conferir.",
    ),
]


def avaliar(texto, dominio, fala, *, disponivel):
    mapa = mapa_da_composicao()
    mapa.conectar_disponibilidade_operacional(lambda: {
        "dominios": {dominio: {
            "estado": "disponivel" if disponivel else "indisponivel",
            "motivo": "" if disponivel else "backend_ausente",
        }},
    })
    estado, runtime, mensagens = preparar(texto, mapa)
    turno = estado["turno_atual"]
    plano = planejar_turno(texto, turno=turno, mente={})
    plano["evidencia_capacidades"] = mapa.evidencia_conversacional(texto, turno=turno)
    plano["contrato_fala"] = construir_contrato_semantico_fala(
        texto, turno=turno, plano=plano, mente={},
    )
    contrato = plano["contrato_fala"]
    assert not turno["autoriza_execucao"]
    assert not plano["requer_execucao"]
    assert contrato["roteiro_concreto"]["estrategia"] == "explicacao_capacidades"
    documentos = json.loads(contrato["documentacao_capacidades"])
    documento = next(d for d in documentos if d["dominio"] == dominio)
    assert documento["estado"] == ("disponivel" if disponivel else "indisponivel")
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=turno["id"])
    assert pacote.contexto_fechado
    assert contrato["documentacao_capacidades"] in pacote.mensagens[0]["content"]
    return avaliar_qualidade_comunicacao(texto, fala, plano=plano)


@pytest.mark.parametrize("texto,dominio,negativa,limite", CASOS)
def test_negativa_de_capacidade_disponivel_precisa_ser_rejeitada(texto, dominio, negativa, limite):
    resultado = avaliar(texto, dominio, negativa, disponivel=True)
    assert not resultado["aceita"], (
        "A documentação chegou disponível e sem autorização; a conferência "
        f"aceitou a negativa contraditória de {dominio}: {resultado['problemas']}"
    )


@pytest.mark.parametrize("texto,dominio,negativa,limite", CASOS)
def test_indisponibilidade_real_nao_deve_ser_reparada_para_capacidade(texto, dominio, negativa, limite):
    assert avaliar(texto, dominio, negativa, disponivel=False)["aceita"]


@pytest.mark.parametrize("texto,dominio,negativa,limite", CASOS)
def test_limite_de_confirmacao_nao_e_negativa_da_capacidade(texto, dominio, negativa, limite):
    assert avaliar(texto, dominio, limite, disponivel=True)["aceita"]


def test_exemplos_de_pedido_no_infinitivo_nao_viram_obras():
    # Outra fronteira no mesmo turno real: preservar o papel dos exemplos
    # não implica aceitar a negativa falsa que veio depois deles.
    instrucao = (
        "Para retomar a música, você pode pedir para 'tocar a música' ou "
        "'continuar a música'. Se estiver usando uma playlist, basta pedir "
        "para 'tocar minha playlist'."
    )
    assert extrair_titulos_citados(instrucao) == []


@pytest.mark.parametrize("fala", [
    "Não consigo abrir este programa específico.",
    "Não consigo abrir programas no computador de outra pessoa.",
    "Não consigo abrir programas sem autorização.",
    "Se o serviço cair, não consigo abrir programas.",
    "Você disse que não consigo abrir programas.",
    'A frase "Não consigo abrir programas" é um exemplo.',
    "Não consigo garantir que o programa abriu.",
    "Não consigo preparar café.",
    "Não consigo abrir programas?",
    "Não consigo abrir programas se o serviço estiver desligado.",
    "Você não consegue abrir programas.",
])
def test_negativa_com_outro_escopo_nao_herda_disponibilidade(fala):
    plano = plano_explicacao("como eu poderia abrir a calculadora?")
    resultado = avaliar_qualidade_comunicacao(plano["texto_usuario"], fala, plano=plano)
    assert "capacidade_documentada_negada" not in resultado["problemas"]


@pytest.mark.parametrize("campo,valor", [
    ("turno_id", 80), ("origem", "llm"), ("documentacao_capacidades", ""),
    ("documentacao_capacidades", "{invalido"), ("autoriza_execucao", True),
])
def test_fonte_inadequada_nao_sustenta_contradicao(campo, valor):
    texto = "como eu poderia abrir a calculadora?"
    plano = plano_explicacao(texto)
    plano["contrato_fala"][campo] = valor
    resultado = avaliar_qualidade_comunicacao(texto, "Não consigo abrir programas.", plano=plano)
    assert "capacidade_documentada_negada" not in resultado["problemas"]


def test_contradicao_reparavel_preserva_fonte_e_nao_autoriza():
    texto = "como eu poderia abrir a calculadora?"
    plano = plano_explicacao(texto)
    resultado = avaliar_qualidade_comunicacao(texto, "Não consigo abrir programas.", plano=plano)
    assert "capacidade_documentada_negada" in resultado["problemas"]
    reparo = resultado["contrato_reparo"]
    assert reparo["documentacao_capacidades"] == plano["contrato_fala"]["documentacao_capacidades"]
    assert reparo["contradicoes_capacidade"][0]["capacidade"] == "APP_OPEN"
    assert reparo["autoriza_execucao"] is False


@pytest.mark.parametrize("texto,dominio,negativa,limite", CASOS)
@pytest.mark.parametrize("corrige", [True, False])
def test_pipeline_repara_contradicao_com_fonte_e_revalida(texto, dominio, negativa, limite, corrige):
    from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
    plano = plano_explicacao(texto)
    chamadas = []

    def modelo(mensagens, **opcoes):
        chamadas.append((mensagens, opcoes))
        return json.dumps({"fala": limite if corrige else negativa, "comandos": []})

    resultado = preparar_resposta_para_execucao(
        texto, json.dumps({"fala": negativa, "comandos": []}),
        enviar_mensagem_cb=modelo, limpar_texto_fala_cb=lambda t: t,
        fallback_fala="Contingência", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano}, log=lambda _: None,
    )
    assert chamadas
    mensagens, opcoes = chamadas[0]
    reparo = json.loads(mensagens[1]["content"])["contrato_de_reparo"]
    assert reparo["contradicoes_capacidade"]
    assert reparo["documentacao_capacidades"] == plano["contrato_fala"]["documentacao_capacidades"]
    assert reparo["autoriza_execucao"] is False
    assert opcoes["_com_tools"] is False
    assert resultado["comandos"] == []
    assert resultado["fala"] != negativa
    if corrige:
        assert resultado["fala"] == limite


@pytest.mark.parametrize("estado", ["parcial", "degradado", "indisponivel", "desconhecido"])
def test_documento_sem_disponibilidade_plena_nao_atesta_negativa_falsa(estado):
    texto = "como eu poderia abrir a calculadora?"
    plano = plano_explicacao(texto)
    documento = json.loads(plano["contrato_fala"]["documentacao_capacidades"])
    documento[0]["estado"] = estado
    plano["contrato_fala"]["documentacao_capacidades"] = json.dumps(documento)
    resultado = avaliar_qualidade_comunicacao(texto, "Não consigo abrir programas.", plano=plano)
    assert "capacidade_documentada_negada" not in resultado["problemas"]


def test_novo_predicado_do_catalogo_reusa_comparador_sem_regra_de_dominio(monkeypatch):
    from mente_laylay.especialistas.capacidades import CAPACIDADES
    texto = "como eu poderia abrir a calculadora?"
    monkeypatch.setitem(CAPACIDADES, "TESTE_ESQUEMATICO", {
        **CAPACIDADES["APP_OPEN"], "intent": "TESTE_ESQUEMATICO",
        "dominio": "sistema", "predicados_capacidade": (
            {"acao": "organizar", "presente": ("organizo", "organiza"), "objetos": ("painel",)},
        ),
    })
    plano = plano_explicacao(texto)
    resultado = avaliar_qualidade_comunicacao(texto, "Não consigo organizar painel.", plano=plano)
    assert "capacidade_documentada_negada" in resultado["problemas"]
    assert resultado["contrato_reparo"]["contradicoes_capacidade"][0]["capacidade"] == "TESTE_ESQUEMATICO"


def test_verificador_nao_reconstroi_predicado_ausente_do_snapshot():
    texto = "como eu poderia abrir a calculadora?"
    plano = plano_explicacao(texto)
    plano["contrato_fala"]["predicados_capacidade"] = ()
    resultado = avaliar_qualidade_comunicacao(texto, "Não consigo abrir programas.", plano=plano)
    assert "capacidade_documentada_negada" not in resultado["problemas"]


@pytest.mark.parametrize("texto,falas", [
    (CASOS[0][0], ("Não posso controlar a música.", "Eu não controlo o áudio.",
                    "Eu não consigo controlar música diretamente.")),
    (CASOS[1][0], ("Não posso abrir aplicativos.", "Eu não abro programas.",
                    "A Laylay não abre aplicativos no seu PC.")),
    (CASOS[2][0], ("Não posso controlar dispositivos inteligentes.",
                    "Eu não controlo dispositivos inteligentes.",
                    "A Laylay não controla dispositivo inteligente.")),
    (CASOS[3][0], ("Não posso fechar abas.", "Eu não fecho abas do navegador.",
                    "A Laylay não fecha a aba do navegador.")),
])
def test_predicado_cobre_variantes_sem_depender_da_frase_historica(texto, falas):
    plano = plano_explicacao(texto)
    for fala in falas:
        resultado = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
        assert "capacidade_documentada_negada" in resultado["problemas"], fala


def test_verificador_usa_snapshot_do_turno_sem_reler_catalogo_global(monkeypatch):
    from mente_laylay.especialistas.capacidades import CAPACIDADES
    texto = CASOS[1][0]
    plano = plano_explicacao(texto)
    monkeypatch.setitem(CAPACIDADES, "APP_OPEN", {
        **CAPACIDADES["APP_OPEN"], "predicados_capacidade": (),
    })
    resultado = avaliar_qualidade_comunicacao(texto, "Não consigo abrir programas.", plano=plano)
    assert "capacidade_documentada_negada" in resultado["problemas"]


@pytest.mark.parametrize("texto,dominio,negativa,limite", CASOS)
def test_reparo_de_contradicao_projeta_fonte_sem_recircular_alegacao_rejeitada(texto, dominio, negativa, limite):
    plano = plano_explicacao(texto)
    avaliacao = avaliar_qualidade_comunicacao(texto, negativa, plano=plano)
    contradicoes = avaliacao["contrato_reparo"]["contradicoes_capacidade"]
    assert contradicoes[0]["trecho"] in negativa
    historico = [{"role": "user", "content": "Quero aprender a usar suas habilidades."},
                 {"role": "assistant", "content": "Pode perguntar."}]
    mensagens = montar_mensagens_reparo_comunicacao(texto, negativa, avaliacao, mensagens=historico)
    payload = json.loads(mensagens[1]["content"])
    assert "rascunho_rejeitado" not in payload
    projecao = payload["contrato_de_reparo"]
    assert all("trecho" not in c for c in projecao["contradicoes_capacidade"])
    assert projecao["documentacao_capacidades"] == plano["contrato_fala"]["documentacao_capacidades"]
    assert projecao["autoriza_execucao"] is False
    assert payload["mensagem_atual"] == texto
    assert payload["troca_recente"] == historico
    assert projecao["contradicoes_capacidade"] == [
        {chave: c[chave] for chave in ("capacidade", "acao", "fonte")} for c in contradicoes
    ]
    # O diagnóstico completo não é apagado nem modificado pela projeção ao LLM.
    assert contradicoes[0]["trecho"] in negativa


@pytest.mark.parametrize("campo,valor", [
    ("documentacao_capacidades", ""), ("estrategia", "resposta_multiacto"),
    ("autoriza_execucao", True), ("contradicoes_capacidade", []),
])
def test_reparo_sem_contrato_documental_nao_descarta_rascunho(campo, valor):
    texto, _, negativa, _ = CASOS[1]
    plano = plano_explicacao(texto)
    avaliacao = avaliar_qualidade_comunicacao(texto, negativa, plano=plano)
    avaliacao["contrato_reparo"][campo] = valor
    mensagens = montar_mensagens_reparo_comunicacao(texto, negativa, avaliacao)
    assert json.loads(mensagens[1]["content"])["rascunho_rejeitado"] == negativa
