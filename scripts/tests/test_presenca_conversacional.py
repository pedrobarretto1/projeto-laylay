"""Presença discursiva atual não prova saúde do corpo nem atividade externa."""
import json

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime


def preparar(texto, *, outro_turno=False, companhia=False, companhia_envio=None):
    turno = classificar_modalidade_turno(texto)
    plano = {"id": turno["id"], "texto_usuario": texto, "comandos": [],
             "requer_execucao": turno["autoriza_execucao"], "atos": turno.get("segmentos", [])}
    corpo = {"companhia_ativa": companhia, "estado": "desconectado"}
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano,
                                               mente={"modelo_corporal": corpo})
    plano["contrato_fala"] = contrato
    if companhia_envio is not None:
        corpo = {"companhia_ativa": companhia_envio, "turno_id": turno["id"]}
        plano["retrato_corporal"] = corpo
    estado = {"turno_atual": turno, "contrato_fala_atual": contrato,
              "plano_turno_atual": plano, "modelo_corporal": corpo}
    runtime = ContextoPromptRuntime(memoria_sqlite=None, resumo_mente_integrada=lambda _: "",
        formatar_playlists=lambda: "", get_status_humor_prompt=lambda: "", base_system_prompt="identidade",
        estado_getter=lambda: estado)
    pacote = runtime.preparar_envio_modelo([
        {"role": "system", "content": "Corpo desconectado; isso não descreve a conversa."},
        {"role": "user", "content": texto}], turno_id="outro" if outro_turno else turno["id"])
    return pacote, plano


@pytest.mark.parametrize("texto", [
    "oi laylay, como voce ta?", "como você está?", "como tu vai?",
    "e o que voce esta fazendo?", "o que voce ta fazendo?",
    "o que você está fazendo agora?", "Laylay, o que você está fazendo?",
])
def test_presenca_tem_realizacao_sem_inferir_estado_externo(texto):
    p, plano = preparar(texto)
    assert p.contexto_fechado is True, "presença atual ainda entregue à autoria de estado sem fonte"
    assert p.mensagens[-1]["content"] == texto
    fala = "Oi! Estou aqui conversando com você." if texto.startswith("oi") else "Estou aqui conversando com você."
    dados = p.contrato_saida.decodificar_json(json.dumps({"comandos": [],
        "suporte_proposicoes": [{"texto": fala, "fontes": []}]}))
    assert dados["fala"] == fala
    revisao = verificar_fala_turno(fala, plano=plano)
    assert revisao["aceita"] is True, revisao
    for falsa in ["Estou desligada.", "Não consigo ver, ouvir nem interagir com nada.",
                  "Estou aqui conversando com você e monitorando o computador."]:
        with pytest.raises(ValueError):
            p.contrato_saida.decodificar_json(json.dumps({"comandos": [],
                "suporte_proposicoes": [{"texto": falsa, "fontes": []}]}))


@pytest.mark.parametrize("fala", [
    "Estou desligada, só existo aqui no texto, como um eco.",
    "Oi! Estou desconectada, então não consigo ver nada nem ouvir nada.",
    "Estou aqui conversando com você. Estou vigiando o computador.",
])
def test_revisao_nao_aceita_extrapolacao_da_presenca(fala):
    _, plano = preparar("oi laylay, como voce ta?")
    r = verificar_fala_turno(fala, plano=plano)
    assert r["aceita"] is False, "revisão aceitou autodescrição sem fonte"


@pytest.mark.parametrize("texto", [
    'repita "o que você está fazendo?"', "o que ela está fazendo?",
    "o que você estava fazendo ontem?", "como está o computador?",
    "oi, como você está? e como está o tempo?", "o que você está fazendo e abra o Opera",
    "como você está programada?", "o que você está fazendo com meus arquivos?",
    "estou cansado, como você está?", "como você está? estou triste",
])
def test_outros_atos_nao_sao_consumidos_como_presenca_pura(texto):
    _, plano = preparar(texto)
    assert plano["contrato_fala"].get("fonte_presenca_conversacional") is None


def test_ocorrencia_antiga_e_companhia_ativa_preservam_seu_caminho():
    assert preparar("como você está?", outro_turno=True)[0].contexto_fechado is False
    assert preparar("como você está?", companhia=True)[0].contexto_fechado is False


def test_companhia_ativada_entre_contrato_e_envio_preserva_prompt_e_revisao():
    p, plano = preparar("como você está?", companhia=False, companhia_envio=True)
    assert plano["contrato_fala"].get("fonte_presenca_conversacional") is not None
    assert p.contexto_fechado is False, "fonte anterior suprimiu o caminho corporal vivo"
    revisao = verificar_fala_turno("Estou bem, acompanhando você.", plano=plano)
    assert "presenca_conversacional_sem_suporte" not in revisao["problemas"]


@pytest.mark.parametrize("mutacao", ["id", "texto", "fonte", "ancora"])
def test_fonte_atual_nao_pode_ser_emprestada_para_outra_ocorrencia(mutacao):
    from copy import deepcopy
    from mente_laylay.cognicao.presenca_conversacional import realizacoes_presenca
    _, plano = preparar("como você está?")
    c = deepcopy(plano["contrato_fala"])
    texto, tid = plano["texto_usuario"], plano["id"]
    if mutacao == "id": tid = "outro"
    elif mutacao == "texto": texto = "o que você está fazendo?"
    elif mutacao == "fonte": c["fonte_presenca_conversacional"]["texto_sha256"] = "inventado"
    else: c["roteiro_concreto"]["ancora_literal"] = "outro"
    assert realizacoes_presenca(texto, contrato=c, turno_id=tid) == ()


@pytest.mark.parametrize("anterior", ["Estou acompanhando nossa conversa.",
    "Agora estou respondendo à sua mensagem.", "Oi! Estou aqui conversando com você."])
def test_esclarecimento_da_presenca_nao_inventa_exclusividade_de_atividade(anterior):
    from scripts.tests.test_autoria_estado_sem_observacao import preparar as preparar_esclarecimento
    p = preparar_esclarecimento("como assim?", anterior=anterior)
    assert p.contexto_fechado is True, "sentido do ato conhecido voltou à autoria factual livre"
    explicacao = ("Minha frase se refere à participação nesta conversa. "
                  "Ela não informa outras atividades no computador nem o estado do corpo físico.")
    dados = p.contrato_saida.decodificar_json(json.dumps({"comandos": [],
        "suporte_proposicoes": [{"texto": explicacao, "fontes": []}]}))
    assert dados["fala"] == explicacao
    with pytest.raises(ValueError):
        p.contrato_saida.decodificar_json(json.dumps({"comandos": [],
            "suporte_proposicoes": [{"texto": "Não estou fazendo nada além disso.", "fontes": []}]}))


@pytest.mark.parametrize("anterior,entregue", [
    ("Estou acompanhando nossa conversa. Não faço mais nada.", True),
    ("Estou acompanhando nossa conversa.", False),
])
def test_significado_controlado_precisa_da_fala_integral_observada(anterior, entregue):
    from scripts.tests.test_autoria_estado_sem_observacao import preparar as preparar_esclarecimento
    assert preparar_esclarecimento("como assim?", anterior=anterior, entregue=entregue).contexto_fechado is False


@pytest.mark.parametrize("fala", ["Não estou fazendo nada além disso.",
    "Minha frase significa que estou monitorando o computador.",
    "Minha frase se refere à participação nesta conversa. Não consigo mais fazer nada."])
def test_revisao_do_esclarecimento_preserva_significado_e_escopo(fala):
    import time
    from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada
    texto, anterior = "como assim?", "Estou acompanhando nossa conversa."
    turno = classificar_modalidade_turno(texto)
    plano = {"id": turno["id"], "texto_usuario": texto, "comandos": [], "requer_execucao": False}
    mente = {"ultima_resposta": anterior, "continuidade_fala_ts": time.time(),
        "registro_semantico": registrar_fala_observada(None, ocorrencia_id="fala-entregue",
            turno_id="turno-anterior", fala=anterior, resultados=(), canal="texto_publicado")}
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    assert plano["contrato_fala"].get("fonte_presenca_conversacional") is not None
    assert verificar_fala_turno(fala, plano=plano)["aceita"] is False
