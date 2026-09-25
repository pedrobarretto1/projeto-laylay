"""Citação de como falar não é nome de obra; alegações vizinhas não herdam isso."""
import pytest

from mente_laylay.cognicao.fundamentacao_factual import extrair_titulos_citados, validar_fala_com_fundamentacao
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno


FALA_ACOLHIMENTO_CITADA = (
    'Tudo bem, obrigada por perguntar. Estou aqui pra escutar o que você tá '
    'pensando — mesmo que seja só um "estou triste" ou um "cansado". 😊'
)


@pytest.mark.parametrize("fala", [
    FALA_ACOLHIMENTO_CITADA,
    'Quero entender o que você quer dizer, mesmo que seja apenas um "não entendi a conta".',
    'Estou aqui para ouvir o que você está sentindo — ainda que seja um "aliviado".',
    'Posso ler o que você pensa, mesmo que seja só um "quero calibrar o sensor".',
    'Quero escutar o que você está pensando — mesmo que seja um "criar o arquivo em 2030".',
])
def test_exemplo_de_conteudo_discursivo_nao_e_obra_nem_fato(fala):
    assert extrair_titulos_citados(fala) == []
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert not resultado["problemas"]
    assert resultado["fala"] == fala


@pytest.mark.parametrize("fala,titulos", [
    ('Recomendo o filme "estou triste" ou um "cansado".', ["estou triste", "cansado"]),
    ('Quero ouvir uma música — mesmo que seja só um "estou triste".', ["estou triste"]),
    ('Quero entender o que você quer dizer. Recomendo "estou triste".', ["estou triste"]),
    ('Quero escutar o que você está pensando — mesmo que seja só um filme "estou triste".', ["estou triste"]),
    ('Quero escutar o que você está pensando — mesmo que seja um "aliviado". Recomendo "Noite Inventada".', ["Noite Inventada"]),
    ('Diga "aliviado" ou um filme chamado "Noite Inventada".', ["Noite Inventada"]),
])
def test_moldura_discursiva_nao_isenta_obra_ou_oracao_seguinte(fala, titulos):
    assert extrair_titulos_citados(fala) == titulos
    assert "obra_sem_evidencia" in validar_fala_com_fundamentacao(fala, fundamentacao=None)["problemas"]


def test_exemplo_discursivo_nao_libera_data_vizinha():
    fala = 'Quero entender o que você quer dizer, mesmo que seja um "em 2030". O filme foi lançado em 2025.'
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert resultado["trechos_rejeitados"] == ["O filme foi lançado em 2025."]


def test_acolhimento_citado_chega_inteiro_ao_verificador_sem_autoridade():
    texto = "como você está?"
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    resultado = verificar_fala_turno(FALA_ACOLHIMENTO_CITADA, plano=plano)
    assert resultado["fala"] == FALA_ACOLHIMENTO_CITADA
    assert not plano["requer_execucao"]
    assert not plano.get("comandos")


@pytest.mark.parametrize("fala", [
    "Para pausar a música, basta dizer 'pausa a música'.",
    'Você pode pedir "abre a calculadora".',
    'Diga: “liga a lâmpada”.',
    "Você pode escrever, por exemplo: 'cria o arquivo notas.txt'.",
    "Peça algo como 'lista meus lembretes'.",
    "Digite **fecha a aba**.",
    "É só falar 'abaixa o volume'.",
    "Use o comando 'pausa a música'.",
    "Você pode dizer ‘coloca o volume em 30%’.",
    "Diga 'me lembre em 2030'.",
    'Para retomar a música, basta pedir para tocar novamente, por exemplo: "toca a música novamente".',
    "Para retomar a música, basta pedir para tocar novamente, como 'toca a música' ou 'continua a música'. Se a música estiver pausada, o comando 'retoma' ou 'continua' fará o mesmo.",
    "Diga 'abre o aplicativo' e 'maximiza a janela'.",
    "Para retomar a música, você pode pedir para 'tocar a música' ou 'continuar a música'. Se estiver usando uma playlist, basta pedir para 'tocar minha playlist'.",
    "Para abrir um aplicativo, basta pedir para 'abrir a calculadora'.",
    "Você pode pedir pra 'ligar a lâmpada'.",
    "Peça para 'listar os lembretes'.",
    "Você pode pedir para 'calibrar o espectrômetro'.",
    "Peça pra 'teletransportar a estação'.",
])
def test_exemplo_de_enunciado_nao_e_candidato_a_pesquisa_de_obra(fala):
    assert extrair_titulos_citados(fala) == []
    validacao = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert validacao["problemas"] == []
    assert validacao["fala"] == fala


@pytest.mark.parametrize("fala,titulo", [
    ('Recomendo o filme "Estrelas que Não Existem".', "Estrelas que Não Existem"),
    ("Peça a música 'Noite Inventada'.", "Noite Inventada"),
    ("Você pode dizer o título 'Filme Inventado'.", "Filme Inventado"),
    ("O filme se chama 'Diga alguma coisa'.", "Diga alguma coisa"),
    ("Diga 'pausa a música'; recomendo 'Planeta Impossível'.", "Planeta Impossível"),
    ("Você pode dizer 'pausa a música', mas o filme 'Lua Ausente' é de 2025.", "Lua Ausente"),
    ("Recomendo ‘Estrelas Vazias’.", "Estrelas Vazias"),
    ("Você pode pedir para tocar algo, por exemplo: 'Noite Inventada'.", "Noite Inventada"),
    ("Diga 'pausa a música' e recomende 'Noite Inventada'.", "Noite Inventada"),
    ("Recomendo 'Noite Inventada' ou 'Lua de Cristal'.", "Lua de Cristal"),
    ("Você pode pedir para tocar 'Noite Inventada'.", "Noite Inventada"),
    ("Você pode pedir para assistir ao filme 'Continuar a Música'.", "Continuar a Música"),
    ("Peça o livro 'Abrir a Calculadora'.", "Abrir a Calculadora"),
    ("Você pode pedir para 'tocar a música', mas recomendo 'Noite Inventada'.", "Noite Inventada"),
])
def test_nome_de_obra_nao_herda_escopo_de_instrucao(fala, titulo):
    assert titulo in extrair_titulos_citados(fala)
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert "obra_sem_evidencia" in resultado["problemas"]


def test_composicao_verifica_fala_inteira_sem_cortar_a_instrucao():
    texto = "como eu poderia pausar a música?"
    fala = "Para pausar a música, basta dizer 'pausa a música'. A habilidade de controle de música já está disponível e pode ser usada assim."
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto), mente={})
    resultado = verificar_fala_turno(fala, plano=plano, origem="ia_final")
    assert resultado["aceita"], resultado["problemas"]
    assert resultado["fala"] == fala
    assert not resultado["problemas"]


def test_exemplo_nao_libera_estado_independente_inventado():
    texto = "como eu poderia pausar a música?"
    fala = "Você pode dizer 'pausa a música'. O navegador está aberto."
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto), mente={})
    resultado = verificar_fala_turno(fala, plano=plano, origem="ia_final")
    assert resultado["problemas"]
    assert not resultado["aceita"] or resultado["fala"] != fala


@pytest.mark.parametrize("sufixo", [" O filme foi lançado em 2025.", " O aparelho pesa 70 kg."])
def test_data_e_medida_fora_da_citacao_continuam_exigindo_fonte(sufixo):
    fala = "Diga 'me lembre em 2030'." + sufixo
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert resultado["problemas"]
    assert resultado["trechos_rejeitados"] == [sufixo.strip()]
    composto = verificar_fala_turno(fala, plano={"dominio": "conversa", "texto_usuario": "como pedir ajuda?"})
    assert any(p in composto["problemas"] for p in ("data_sem_evidencia", "medida_sem_evidencia"))


@pytest.mark.parametrize("nome", ["Calculadora", "Krita", "Editor Aurora"])
def test_nome_de_recurso_e_exemplo_em_frase_separada_preservam_explicacao(nome):
    fala = (f"Para abrir o aplicativo, você pode pedir para o sistema abrir o programa '{nome}'. "
            f"Por exemplo: 'abre {nome}'.")
    assert extrair_titulos_citados(fala) == []
    assert validar_fala_com_fundamentacao(fala, fundamentacao=None)["problemas"] == []
    plano = planejar_turno("como abrir um programa?", turno=classificar_modalidade_turno("como abrir um programa?"))
    verificado = verificar_fala_turno(fala, plano=plano, origem="ia_final")
    assert verificado["aceita"] and verificado["fala"] == fala


@pytest.mark.parametrize("tipo,nome", [
    ("aplicativo", "Aurora"), ("arquivo", "notas.txt"), ("pasta", "Projeto"),
    ("dispositivo", "lâmpada do quarto"), ("playlist", "Favoritas"),
])
def test_referencia_tipificada_nao_e_obra(tipo, nome):
    assert extrair_titulos_citados(f"Você pode escolher o {tipo} '{nome}'.") == []


@pytest.mark.parametrize("fala,titulo", [
    ("Recomendo o filme 'Calculadora'.", "Calculadora"),
    ("Recomendo um filme. Por exemplo: 'Abra os Olhos'.", "Abra os Olhos"),
    ("Você pode pedir para tocar uma música. Por exemplo: 'Noite Inventada'.", "Noite Inventada"),
    ("Use o aplicativo 'Aurora'. Recomendo 'Lua Inventada'.", "Lua Inventada"),
    ("Assista ao programa 'Noite Inventada'.", "Noite Inventada"),
    ("O programa 'Noite Inventada' foi premiado.", "Noite Inventada"),
])
def test_tipo_e_exemplo_nao_liberam_outra_obra(fala, titulo):
    assert titulo in extrair_titulos_citados(fala)
    assert "obra_sem_evidencia" in validar_fala_com_fundamentacao(fala, fundamentacao=None)["problemas"]


@pytest.mark.parametrize("fala,problema", [
    ("O aplicativo 'Aurora' foi lançado em 2025.", "data_sem_evidencia"),
    ("O dispositivo 'Aurora' pesa 70 kg.", "medida_sem_evidencia"),
])
def test_referencia_nao_isenta_fatos_associados(fala, problema):
    assert problema in validar_fala_com_fundamentacao(fala, fundamentacao=None)["problemas"]


def test_nome_de_app_nao_comprova_instalacao_ou_abertura():
    fala = "O aplicativo 'Aurora' está aberto."
    plano = planejar_turno("como abrir um aplicativo?", turno=classificar_modalidade_turno("como abrir um aplicativo?"))
    resultado = verificar_fala_turno(fala, plano=plano, origem="ia_final")
    assert not resultado["aceita"] or resultado["fala"] != fala


def test_fala_historica_da_calculadora_chega_inteira_ao_verificador():
    texto = "como eu poderia abrir a calculadora?"
    fala = "Para abrir a calculadora, você pode pedir para o sistema abrir o programa 'Calculadora'. Por exemplo: 'abre a calculadora'."
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    assert extrair_titulos_citados(fala) == []
    resultado = verificar_fala_turno(fala, plano=plano, origem="ia_final")
    assert resultado["aceita"] and resultado["fala"] == fala


@pytest.mark.parametrize("fala", [
    "Você pode pedir para abrir um programa. Recomendo um filme. Por exemplo: 'Abra os Olhos'.",
])
def test_exemplo_sem_pedido_ou_fora_da_frase_seguinte_nao_herda_escopo(fala):
    assert extrair_titulos_citados(fala)
    assert "obra_sem_evidencia" in validar_fala_com_fundamentacao(fala, fundamentacao=None)["problemas"]


def test_exemplo_ambiguo_nao_e_obra_nem_enunciado_isento():
    # Expectativa antiga confundia falta de classificação com prova de obra.
    # Não há relação musical/editorial aqui; também não há pedido citado que
    # permita mascarar os fatos do trecho desconhecido.
    fala = "Você pode pedir para abrir o programa 'Aurora'. Por exemplo: 'Noite Inventada em 2030'."
    assert extrair_titulos_citados(fala) == []
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert "data_sem_evidencia" in resultado["problemas"]
    assert "obra_sem_evidencia" not in resultado["problemas"]


def test_exemplo_em_frase_separada_nao_isenta_data_posterior():
    fala = "Você pode pedir para abrir o programa 'Aurora'. Por exemplo: 'abre Aurora'. Foi lançado em 2025."
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert "data_sem_evidencia" in resultado["problemas"]
    assert resultado["trechos_rejeitados"] == ["Foi lançado em 2025."]


@pytest.mark.parametrize("fala", [
    "Para abrir a calculadora, basta pedir para eu abrir o programa 'Calculadora' — como em 'abre a calculadora'.",
    "Para ligar a lâmpada, basta pedir para mim: 'ligue a lâmpada'.",
    "Para desligar o ventilador, você pode pedir para Laylay desligar o ventilador diretamente. Exemplo: 'Laylay, desligue o ventilador'.",
    "Para aumentar o volume, basta pedir para mim abrir o controle de volume do seu computador. Por exemplo: 'Laylay, aumente o volume'.",
    "Você pode pedir para abrir o aplicativo 'Aurora', como em 'abre Aurora'.",
    "Você pode pedir para criar o arquivo 'notas.txt' — como em 'cria o arquivo notas.txt'.",
    "Peça a mim: 'mostre meus lembretes'.",
    "Você pode pedir para ajustar algo. Exemplo: 'Ei, Laylay, calibre o sensor'.",
])
def test_exemplo_com_destinatario_referencia_intermediaria_ou_vocativo_e_enunciado(fala):
    assert extrair_titulos_citados(fala) == []
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert resultado["fala"] == fala
    assert not resultado["problemas"]


@pytest.mark.parametrize("fala,titulo", [
    ("Você pode pedir um filme. Exemplo: 'Abra os Olhos'.", "Abra os Olhos"),
    ("Você pode pedir uma música. Por exemplo: 'Laylay, volte'.", "Laylay, volte"),
    ("Recomendo uma música. Exemplo: 'Laylay, aumente o volume'.", "Laylay, aumente o volume"),
    ("Você pode pedir para tocar algo. Exemplo: 'Noite Inventada'.", "Noite Inventada"),
    ("Você pode pedir para abrir o programa 'Aurora'. Recomendo 'Abra os Olhos'.", "Abra os Olhos"),
    ("Diga 'pausa a música'. O filme se chama 'Laylay, volte'.", "Laylay, volte"),
])
def test_vocativo_ou_morfologia_de_comando_nao_isentam_obra(fala, titulo):
    assert titulo in extrair_titulos_citados(fala)
    assert "obra_sem_evidencia" in validar_fala_com_fundamentacao(fala, fundamentacao=None)["problemas"]


@pytest.mark.parametrize("sufixo", [" O aparelho pesa 70 kg.", " O filme foi lançado em 2025."])
def test_destinatario_no_exemplo_nao_isenta_fato_vizinho(sufixo):
    fala = "Você pode pedir para ajustar algo. Exemplo: 'Laylay, aumente o volume'." + sufixo
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert resultado["trechos_rejeitados"] == [sufixo.strip()]


def test_exemplo_nao_promove_citacao_a_utterance_autorizante():
    texto = "como eu poderia desligar o ventilador?"
    fala = "Você pode pedir para desligar o ventilador. Exemplo: 'Laylay, desligue o ventilador'."
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    resultado = verificar_fala_turno(fala, plano=plano, origem="ia_final")
    assert resultado["fala"] == fala
    assert not plano["requer_execucao"]
    assert not plano.get("comandos")


def test_moldura_de_enunciado_nao_depende_de_verbo_executavel(monkeypatch):
    import mente_laylay.cognicao.modalidade_turno as modalidade
    def nao_classificar(*args, **kwargs):
        raise AssertionError("Papel citado não é autorização nem classificação operacional")
    monkeypatch.setattr(modalidade, "classificar_modalidade_turno", nao_classificar)
    assert extrair_titulos_citados("Peça para 'calibrar o espectrômetro'.") == []


def test_infinitivo_citado_nao_certifica_alegacao_factual_vizinha():
    fala = "Peça para 'criar o arquivo em 2030'. O filme foi lançado em 2025."
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert resultado["trechos_rejeitados"] == ["O filme foi lançado em 2025."]
    assert "data_sem_evidencia" in resultado["problemas"]


def test_infinitivo_citado_preserva_ausencia_de_autorizacao():
    texto = "como eu poderia desligar o ventilador?"
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    fala = "Você pode pedir para 'desligar o ventilador'."
    assert verificar_fala_turno(fala, plano=plano)["fala"] == fala
    assert not plano["requer_execucao"]
    assert not plano.get("comandos")


@pytest.mark.parametrize("fala,titulos", [
    ("Você pode pedir para ajustar algo. Exemplo: 'Laylay, aumente o volume'.", []),
    ("Para abrir a calculadora, basta pedir para eu abrir o programa 'Calculadora' — como em 'abre a calculadora'.", []),
    ("Recomendo o filme 'Abra os Olhos'.", ["Abra os Olhos"]),
    ("Você pode pedir para 'tocar a música' ou 'continuar a música'.", []),
    ("Peça para 'abrir a calculadora'.", []),
    ("Peça para 'ligar a lâmpada'.", []),
    ("Você pode pedir para tocar 'Noite Inventada'.", ["Noite Inventada"]),
    (FALA_ACOLHIMENTO_CITADA, []),
    ('Quero entender o que você quer dizer, mesmo que seja um "não entendi a conta".', []),
    ('Quero ouvir uma música — mesmo que seja só um "estou triste".', ["estou triste"]),
])
def test_composicao_so_pesquisa_titulo_e_nao_exemplo(fala, titulos):
    import time
    from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime

    pesquisas = []

    class PesquisaObservada:
        def pesquisar_contexto_tema(self, tema):
            pesquisas.append(tema)
            return {}  # Transporte sem evidência; nunca certifica o título.

    texto = "como eu poderia aumentar o volume?"
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    estado = EstadoCompartilhadoRuntime(mental={"plano_turno_atual": plano})
    runtime = ComposicaoTurnoRuntime(servicos={
        "_estado_compartilhado_runtime": estado,
        "_contexto_horario_atual": lambda: "manha",
        "_verificar_fala_turno_mente": verificar_fala_turno,
        "_pesquisa_contextual_runtime": PesquisaObservada(),
        "_montar_fundamentacao_mente": montar_fundamentacao,
        "time": time, "print": lambda *args: None,
    })
    resultado = runtime.verificar_fala(fala, origem="ia_final")
    assert pesquisas == titulos
    assert not estado.mental["plano_turno_atual"].get("comandos")
    if not titulos:
        assert resultado["fala"] == fala
        assert not resultado["problemas"]
    else:
        assert "obra_sem_evidencia" in resultado["problemas"]
