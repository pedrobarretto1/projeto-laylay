"""A explicação preserva a relação do ato; não classifica nem autoriza de novo."""
from copy import deepcopy

import pytest

from mente_laylay.cognicao.contratos_turno import ComplementoConversacionalTurno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito


def _turno(restante):
    texto = f"Abre a calculadora; {restante}"
    turno = classificar_modalidade_turno(
        texto, normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    turno["id"] = "explicacao-1"
    assert len(turno["segmentos"]) == 2
    assert turno["segmentos"][0]["autoriza_execucao"] is True
    assert turno["segmentos"][1]["autoriza_execucao"] is False
    return turno, texto


@pytest.mark.parametrize("expressao", [
    "pode abrir a calculadora", "pode pausar a música",
    "pode ligar a luz", "pode apagar o arquivo notas.txt",
    'pode abrir o arquivo "isso significa o quê.txt"',
])
@pytest.mark.parametrize("predicado", ["significa o quê?", "quer dizer o que"])
def test_owner_preserva_objeto_estrutural_separado_da_pergunta(expressao, predicado):
    turno, texto = _turno(f"{expressao} {predicado}")
    segmento = turno["segmentos"][1]
    contrato = segmento.get("contrato_explicativo", {})
    assert contrato.get("relacao") == "consulta_significado"
    inicio, fim = contrato["intervalo_objeto"]
    assert segmento["texto_estrutural"][inicio:fim] == contrato["objeto_textual"]
    assert contrato["objeto_textual"] == expressao
    assert contrato["objeto_textual"] != segmento["texto_estrutural"]
    complemento = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert complemento is not None
    atos = getattr(complemento, "atos_explicativos", ())
    assert len(atos) == 1
    assert atos[0].indice == 1
    dados = atos[0].como_dict()
    assert dados["objeto_textual"] == expressao
    assert dados["autoriza_execucao"] is False
    assert set(dados["nao_comprova"]) == {
        "efeito", "pendencia", "capacidade", "acesso_ao_alvo",
    }


@pytest.mark.parametrize("restante", [
    "quando eu confirmar, retoma a música",
    "caso eu peça, fecha o navegador",
])
def test_condicao_declarada_nao_se_converte_em_pendencia_comprovada(restante):
    turno, texto = _turno(restante)
    complemento = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert complemento is not None
    atos = getattr(complemento, "atos_explicativos", ())
    assert len(atos) == 1
    dados = atos[0].como_dict()
    assert dados["relacao"] == "condicao_nao_verificada"
    assert dados["objeto_textual"] == ""
    assert dados["intervalo_objeto"] is None
    assert dados["autoriza_execucao"] is False
    assert "pendencia" in dados["nao_comprova"]
    assert "pendencia_ativa" not in dados


@pytest.mark.parametrize("campo,valor", [
    ("fonte", "llm"), ("relacao", "efeito_executado"),
    ("objeto_textual", "outro objeto"), ("intervalo_objeto", [True, 20]),
    ("intervalo_objeto", [0, 999]), ("autoriza_execucao", True),
])
def test_projecao_recusa_contrato_explicativo_incoerente(campo, valor):
    turno, texto = _turno("pode abrir a calculadora significa o quê?")
    segmento = turno["segmentos"][1]
    segmento.setdefault("contrato_explicativo", {})[campo] = valor
    assert ComplementoConversacionalTurno.da_prioridade(turno, texto) is None


def test_snapshot_explicativo_detecta_mudanca_sem_novo_texto_ou_turno():
    turno, texto = _turno("pode abrir a calculadora significa o quê?")
    antes = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert antes is not None
    alterado = deepcopy(turno)
    alterado["segmentos"][1]["natureza_acao"] = "condicao_nao_verificada"
    depois = ComplementoConversacionalTurno.da_prioridade(alterado, texto)
    assert antes != depois


def test_literal_com_marcador_interno_continua_pedido_sem_contrato_de_consulta():
    turno = classificar_modalidade_turno(
        'Pode abrir o arquivo "isso significa o quê.txt"?',
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    assert turno["autoriza_execucao"] is True
    assert "contrato_explicativo" not in turno["segmentos"][0]


def test_coordenadas_explicativas_nao_apontam_para_fonte_truncada():
    expressao = 'pode abrir o arquivo "' + "a" * 320 + '.txt"'
    turno, texto = _turno(expressao + " significa o quê?")
    segmento = turno["segmentos"][1]
    assert len(segmento["texto_estrutural"]) == 300
    complemento = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert complemento is not None
    ato = complemento.atos_explicativos[0]
    inicio, fim = ato.intervalo_objeto
    assert ato.texto[inicio:fim] == expressao
    assert fim > 300


def test_serializacao_nao_altera_snapshot_ou_prova_estado_de_outro_owner():
    turno, texto = _turno("quando eu confirmar, retoma a música")
    # Pode existir uma oferta legítima em outro fluxo: este contrato não a
    # invalida nem a usa para converter a condição em confirmação.
    turno["pendencia_de_outro_owner"] = {"ativa": True, "alvo": "playlist"}
    complemento = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert complemento is not None
    ato = complemento.atos_explicativos[0]
    dados = ato.como_dict()
    dados["nao_comprova"].clear()
    dados["relacao"] = "confirmacao"
    assert ato.como_dict()["relacao"] == "condicao_nao_verificada"
    assert "pendencia" in ato.como_dict()["nao_comprova"]
    assert turno["pendencia_de_outro_owner"]["ativa"] is True


@pytest.mark.parametrize("sujeito,pessoa", [
    ("eu", "enunciador"), ("você", "destinatario"),
    ("a gente", "grupo"), ("nós", "grupo"),
])
@pytest.mark.parametrize("acao", ["retoma a música", "liga a luz", "abre o arquivo notas.txt"])
def test_pessoa_da_condicao_vem_do_owner_e_preserva_coordenadas(sujeito, pessoa, acao):
    verbo = "confirmarmos" if sujeito == "nós" else "confirmar"
    turno, texto = _turno(f"quando {sujeito} {verbo}, {acao}")
    contrato = turno["segmentos"][1]["contrato_explicativo"]
    assert contrato.get("pessoa_condicao") == pessoa
    inicio, fim = contrato["intervalo_pessoa_condicao"]
    assert contrato["texto_ato"][inicio:fim] == sujeito
    complemento = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert complemento is not None
    ato = complemento.atos_explicativos[0].como_dict()
    assert ato["pessoa_condicao"] == pessoa
    assert ato["intervalo_pessoa_condicao"] == [inicio, fim]


def test_condicao_sem_sujeito_explicito_nao_inventa_pessoa():
    turno, texto = _turno("retoma a música só se houver autorização")
    complemento = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert complemento is not None
    ato = complemento.atos_explicativos[0].como_dict()
    assert ato.get("pessoa_condicao") == "indeterminada"
    assert ato["intervalo_pessoa_condicao"] is None


@pytest.mark.parametrize("campo,valor", [
    ("pessoa_condicao", "destinatario"), ("pessoa_condicao", "llm"),
    ("intervalo_pessoa_condicao", [True, 8]),
    ("intervalo_pessoa_condicao", [0, 999]),
])
def test_pessoa_condicao_precisa_de_vinculo_literal_coerente(campo, valor):
    turno, texto = _turno("quando eu confirmar, retoma a música")
    turno["segmentos"][1]["contrato_explicativo"][campo] = valor
    assert ComplementoConversacionalTurno.da_prioridade(turno, texto) is None


def test_condicoes_com_pessoas_concorrentes_nao_sao_reduzidas_a_primeira():
    turno, texto = _turno("quando eu confirmar e quando você autorizar, retoma a música")
    c = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert c is not None
    assert c.atos_explicativos[0].pessoa_condicao == "indeterminada"
    assert c.atos_explicativos[0].intervalo_pessoa_condicao is None
