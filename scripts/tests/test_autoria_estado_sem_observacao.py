"""Sem observação, a autoria não pode fabricar estado ou incapacidade."""
from copy import deepcopy
import json
import time

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada


def preparar(texto, *, fundamentacao=None, turno_id=None, anterior="", entregue=True):
    turno = classificar_modalidade_turno(texto)
    plano = {"id": turno["id"], "texto_usuario": texto, "comandos": [],
             "requer_execucao": False, "atualidade_factual": classificar_atualidade_factual(texto, turno=turno),
             "fundamentacao_factual": fundamentacao or {}}
    mente = {"ultima_resposta": anterior, "continuidade_fala_ts": time.time()}
    if anterior and entregue:
        mente["registro_semantico"] = registrar_fala_observada(None, ocorrencia_id="entrega-anterior",
            turno_id="turno-anterior", fala=anterior, resultados=(), canal="texto_publicado")
    c = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    plano["contrato_fala"] = c
    estado = {**mente, "turno_atual": turno, "contrato_fala_atual": c, "plano_turno_atual": plano}
    antes = deepcopy(estado)
    runtime = ContextoPromptRuntime(memoria_sqlite=None, resumo_mente_integrada=lambda _: "",
        formatar_playlists=lambda: "", get_status_humor_prompt=lambda: "", base_system_prompt="identidade",
        estado_getter=lambda: estado)
    mensagens = [{"role": "system", "content": "contexto anterior não pode decidir estado"},
                 {"role": "user", "content": texto}]
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=turno_id or turno["id"])
    assert estado == antes
    return pacote


@pytest.mark.parametrize("texto", [
    "e como estao as coisas no computador?", "como está o arquivo?",
    "como está a playlist?", "como está o sensor?",
])
def test_limite_de_observacao_e_fonte_compartilhada_sem_redacao_factual_livre(texto):
    p = preparar(texto)
    assert p.contexto_fechado is True, "primeira divergência: ausência de observação foi entregue à autoria factual livre"
    assert len(p.mensagens) == 2 and p.mensagens[-1]["content"] == texto
    assert p.contrato_saida is not None
    permitido = "Ainda não tenho uma leitura atual desse estado para responder com segurança."
    dados = p.contrato_saida.decodificar_json(json.dumps({"comandos": [],
        "suporte_proposicoes": [{"texto": permitido, "fontes": []}]}))
    assert dados["fala"] == permitido and dados["comandos"] == []
    for inventada in ("Tudo está funcionando normalmente.", "Estou sem acesso direto ao sistema.", "O sensor quebrou."):
        with pytest.raises(ValueError):
            p.contrato_saida.decodificar_json(json.dumps({"comandos": [],
                "suporte_proposicoes": [{"texto": inventada, "fontes": []}]}))


@pytest.mark.parametrize("texto", ["como você está?", "como assim?", "estou bem; como está o arquivo?",
    "Como está o sistema solar organizado?", "Como está o corpo humano dividido?",
    "Qual é o estado da música brasileira no século XIX?"])
def test_outros_atos_nao_sao_substituidos_pelo_limite_de_observacao(texto):
    assert preparar(texto).contexto_fechado is False


def test_pacote_de_outro_turno_nao_recebe_fonte_do_estado_atual():
    assert preparar("como está o arquivo?", turno_id="outro").contexto_fechado is False


@pytest.mark.parametrize("anterior", [
    "Ainda não tenho uma leitura atual desse estado para responder com segurança.",
    "Preciso de uma observação atual desse estado para responder com segurança.",
])
@pytest.mark.parametrize("texto", ["como assim?", "explica melhor", "o que você quis dizer?"])
def test_sentido_do_limite_entregue_tem_realizacao_propria_sem_repetir_o_original(anterior, texto):
    p = preparar(texto, anterior=anterior)
    assert p.contexto_fechado is True
    assert p.mensagens[-1]["content"] == texto
    resposta = ("Quis dizer que é preciso observar o estado antes de descrevê-lo. "
                "Minha frase não afirma que o recurso esteja com defeito nem que eu tenha perdido acesso a ele.")
    dados = p.contrato_saida.decodificar_json(json.dumps({"comandos": [],
        "suporte_proposicoes": [{"texto": resposta, "fontes": []}]}))
    assert dados["fala"] == resposta and dados["fala"] != anterior
    turno = classificar_modalidade_turno(texto)
    plano = {"id": turno["id"], "texto_usuario": texto, "comandos": [], "requer_execucao": False}
    plano["contrato_fala"] = construir_contrato_semantico_fala(
        texto, turno=turno, plano=plano, mente={"ultima_resposta": anterior})
    revisao = verificar_fala_turno(dados["fala"], plano=plano, ultima_resposta=anterior)
    assert revisao["aceita"] is True, revisao["problemas"]
    with pytest.raises(ValueError):
        p.contrato_saida.decodificar_json(json.dumps({"comandos": [],
            "suporte_proposicoes": [{"texto": anterior, "fontes": []}]}))


def test_fala_sem_entrega_observada_nao_recebe_semantica_controlada_por_recencia():
    p = preparar("como assim?", anterior="Ainda não tenho uma leitura atual desse estado para responder com segurança.",
                 entregue=False)
    assert p.contexto_fechado is False
