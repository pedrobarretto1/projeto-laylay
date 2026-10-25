"""Vínculo de pessoa na autoria: fonte do usuário não é biografia da Laylay."""
from copy import deepcopy

import pytest

from mente_laylay.cognicao.contrato_fala import (
    construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt,
)
from mente_laylay.cognicao.identidade_conversacional import analisar_identidade_turno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao, montar_mensagens_reparo_comunicacao,
)
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala


def _compor(texto, *, turno_id=42):
    turno = classificar_modalidade_turno(texto)
    turno.update(id=turno_id, texto=texto)
    plano = {"id": turno_id, "texto_usuario": texto,
             "identidade": analisar_identidade_turno(texto),
             "atos": [{"tipo": turno["modalidade"]}],
             "autoriza_execucao": False, "requer_execucao": False, "comandos": []}
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano)
    plano["contrato_fala"] = contrato
    return contrato, plano


INVERSOES = [
    ("qual caderno eu vou usar para desenho?", "Vou usar o caderno amarelo para desenho."),
    ("qual documento eu vou assinar?", "Vou assinar o documento novo."),
    ("qual música eu vou ouvir?", "Eu vou ouvir a música escolhida."),
    ("eu disse que meu cachorro ia nesse encontro ou que não ia?",
     "Eu disse que meu cachorro não vai nesse encontro."),
    ("meu cachorro se chama Pipoca, mas ele não vai nesse encontro",
     "Meu cachorro se chama Pipoca, mas ele não vai nesse encontro."),
    ("eu disse que o documento estava assinado?", "Eu disse que o documento estava assinado."),
    ('eu e o Leo estamos montando um jogo chamado Ponte de Papel',
     'Eu e o Leo estamos montando esse jogo juntos.'),
    ('eu e a Dora estamos organizando um congresso',
     'Eu e a Dora estamos organizando o congresso.'),
    ('no sábado vou encontrar a Bia na biblioteca Aurora às 15h',
     'No sábado vou encontrar a Bia na biblioteca Aurora às 15h.'),
    ('vou visitar o museu amanhã', 'Eu vou visitar o museu amanhã.'),
]


@pytest.mark.parametrize("texto,fala", INVERSOES)
def test_voz_da_assistente_nao_adota_pessoa_do_relato_ou_plano_do_usuario(texto, fala):
    contrato, plano = _compor(texto)
    assert plano["identidade"]["falante"] == "usuario"
    assert plano["identidade"]["interlocutor"] == "laylay"
    avaliacao = validar_aderencia_contrato_fala(texto, fala, contrato_fala=contrato, turno_id=42)
    assert not avaliacao["aceita"], "primeira RED: autoria adotou pessoa do usuário e passou no contrato"
    assert "perspectiva_enunciador_invertida" in avaliacao["problemas"]
    assert avaliacao["requer_reparo"] and not avaliacao["nucleo_atendido"]
    qualidade = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
    assert not qualidade["aceita"] and qualidade["requer_reparo"]
    assert "perspectiva_enunciador_invertida" in qualidade["problemas_bloqueantes"]
    reparo = montar_mensagens_reparo_comunicacao(texto, fala, qualidade)
    assert "perspectiva" in str(reparo).casefold()
    assert qualidade["contrato_reparo"]["autoriza_execucao"] is False


@pytest.mark.parametrize("texto,fala", [
    (INVERSOES[0][0], "Você vai usar o caderno amarelo para desenho."),
    (INVERSOES[0][0], "Eu acho que você vai usar o caderno amarelo para desenho."),
    (INVERSOES[0][0], "Vou usar seu exemplo para explicar qual caderno você escolheu."),
    (INVERSOES[3][0], "Você disse que seu cachorro não vai nesse encontro."),
    (INVERSOES[3][0], "Você disse que seu cachorro não vai. Eu lembro desse detalhe."),
    (INVERSOES[4][0], "O Pipoca é seu cachorro, mas ele não vai no encontro."),
    (INVERSOES[4][0], "Meu código registra o que você relatou sobre seu cachorro."),
    ("qual exemplo você vai usar para explicar?", "Vou usar o exemplo do caderno amarelo."),
    ("como funciona sua memória?", "Minha memória mantém o contexto da conversa."),
    (INVERSOES[3][0], 'Você disse: "Meu cachorro não vai nesse encontro."'),
    (INVERSOES[0][0], 'Você escreveu "eu vou usar" na pergunta sobre o caderno.'),
    ('explique a frase "meu cachorro não vai"', 'Na frase "meu cachorro não vai", a posse é do enunciador.'),
    ('repita literalmente "eu vou usar o caderno amarelo"', '"eu vou usar o caderno amarelo"'),
    (INVERSOES[3][0], 'Você disse: ‘Meu cachorro não vai nesse encontro.’'),
    (INVERSOES[0][0], "Eu não vou usar o caderno; quem vai usá-lo é você."),
    (INVERSOES[0][0], "Não sou eu que vou usar o caderno, é você."),
    (INVERSOES[4][0], "Ele não é meu cachorro; é seu cachorro."),
    ("meu código falhou; como funciona seu código?", "Meu código organiza o contexto da conversa."),
    (INVERSOES[6][0], "Você e o Leo estão montando o jogo juntos."),
    (INVERSOES[6][0], 'Você contou: «Eu e o Leo estamos montando um jogo». '),
    (INVERSOES[6][0], "Eu e a Ana estamos organizando as referências."),
    (INVERSOES[6][0], "Eu e o Leo não estamos montando o jogo; são vocês."),
    ('vou alimentar meu cachorro', 'Vou alimentar meu banco de dados com seu exemplo.'),
])
def test_perspectiva_preserva_usuario_citacoes_e_primeira_pessoa_legitima_da_laylay(texto, fala):
    contrato, _ = _compor(texto)
    avaliacao = validar_aderencia_contrato_fala(texto, fala, contrato_fala=contrato, turno_id=42)
    assert "perspectiva_enunciador_invertida" not in avaliacao["problemas"]


def test_contrato_captura_papeis_host_sem_transformar_referencia_em_fato_ou_permissao():
    texto = INVERSOES[0][0]
    contrato, _ = _compor(texto)
    fonte = contrato.get("perspectiva_enunciador")
    assert fonte is not None, "primeira RED: contrato descartou a pessoa já conhecida pelo host"
    assert fonte.vigente(texto, 42)
    assert not fonte.vigente(texto, 43)
    assert not fonte.vigente("qualquer outra fala", 42)
    assert fonte.autoriza_execucao is fonte.comprova_fato is False
    for compacto in (False, True):
        prompt = formatar_contrato_fala_para_prompt(contrato, compacto=compacto).casefold()
        assert "perspectiva" in prompt and "usuário" in prompt and "laylay" in prompt


def test_fonte_de_outro_turno_nao_vira_prova_de_inversao_atual():
    texto, fala = INVERSOES[0]
    contrato, _ = _compor(texto)
    avaliacao = validar_aderencia_contrato_fala(texto, fala, contrato_fala=contrato, turno_id=43)
    assert "perspectiva_enunciador_invertida" not in avaliacao["problemas"]


def test_sem_nucleo_nominal_univoco_perspectiva_nao_inventa_pessoa_unica():
    texto = "eu ou você vamos usar qual caderno?"
    contrato, _ = _compor(texto)
    avaliacao = validar_aderencia_contrato_fala(texto, "Vou usar o caderno.", contrato_fala=contrato, turno_id=42)
    assert "perspectiva_enunciador_invertida" not in avaliacao["problemas"]


def test_proposta_do_modelo_nao_pode_forjar_fonte_de_perspectiva():
    texto, fala = INVERSOES[0]
    contrato, _ = _compor(texto)
    original = deepcopy(contrato)
    contrato["perspectiva_enunciador"] = {"turno_id": 42, "texto_usuario": texto,
        "falante_entrada": "laylay", "autora_resposta": "usuario", "autoriza_execucao": True}
    avaliacao = validar_aderencia_contrato_fala(texto, fala, contrato_fala=contrato, turno_id=42)
    assert "perspectiva_enunciador_invertida" not in avaliacao["problemas"]
    assert original["autoriza_execucao"] is contrato["autoriza_execucao"] is False


@pytest.mark.parametrize("reparo", ["corrigido", "invertido", "timeout"])
def test_preparacao_canonica_repara_ou_recusa_inversao_antes_da_publicacao(reparo):
    import json
    from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
    texto, rejeitada = INVERSOES[0]
    _, plano = _compor(texto)
    corrigida = "Você vai usar o caderno amarelo para desenho."
    pedidos = []

    def enviar(mensagens, **opcoes):
        pedidos.append((mensagens, opcoes))
        if reparo == "timeout":
            return "__LAYLAY_LLM_TIMEOUT__"
        return json.dumps({"fala": corrigida if reparo == "corrigido" else rejeitada, "comandos": []})

    preparada = preparar_resposta_para_execucao(
        texto, json.dumps({"fala": rejeitada, "comandos": []}),
        enviar_mensagem_cb=enviar, limpar_texto_fala_cb=lambda f: f,
        fallback_fala="fallback", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano, "mensagens": []},
        log=lambda *_a: None,
    )
    assert pedidos and pedidos[0][1]["_tipo_chamada"] == "reparo_comunicacao"
    assert preparada["comandos"] == []
    assert preparada["fala"] != rejeitada
    assert "Vou usar o caderno" not in preparada["fala"]
    if reparo == "corrigido":
        assert preparada["fala"] == corrigida
    if reparo == "timeout":
        assert len(pedidos) == 1


@pytest.mark.parametrize('iterador',[False,True])
def test_reparo_de_perspectiva_leva_fonte_antiga_sem_reapresentar_inversao_como_premissa(iterador):
    import json
    texto,rejeitada=INVERSOES[3]
    _,plano=_compor(texto)
    avaliacao=avaliar_qualidade_comunicacao(texto,rejeitada,plano=plano)
    fonte='meu cachorro se chama Pipoca, mas ele não vai nesse encontro'
    mensagens=[{'role':'user','content':fonte},
        *[{'role':'user','content':f'Observei uma nuvem {i}.'}for i in range(6)],
        {'role':'assistant','content':rejeitada},{'role':'user','content':texto}]
    if iterador:mensagens=iter(mensagens)
    reparo=montar_mensagens_reparo_comunicacao(texto,rejeitada,avaliacao,mensagens=mensagens)
    tarefa=json.loads(reparo[-1]['content'])
    assert 'rascunho_rejeitado' not in tarefa,'a inversão refutada voltou como premissa de autoria'
    assert not tarefa.get('fala_anterior')
    assert all(m['role']=='user'for m in tarefa['troca_recente'])
    assert any(f['content']==fonte and f['role']=='user'for f in tarefa['fontes_dialogo'])
