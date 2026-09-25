"""Papel de pergunta/termo didático não é título de obra nem evidência factual."""
import pytest

from mente_laylay.cognicao.fundamentacao_factual import (
    extrair_titulos_citados, validar_fala_com_fundamentacao,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno


PEDIDO = "quero passo a passo usando metodos praticos"
FALA_HISTORICA = (
    'Claro! Vamos fazer divisão com um exemplo prático: 18 dividido por 6. '
    'Primeiro, pense: "6 cabe quantas vezes em 18?" - 6 cabe 3 vezes em 18, '
    'porque 6 × 3 = 18. Ou, se quiser, podemos usar o método da "divisão por '
    'agrupamento": - Agrupe 18 em blocos de 6: 6, 12, 18 → depois de 3 blocos, '
    'chega a 18. → Então, 18 ÷ 6 = 3. Quer tentar outro número? Ou quer que eu '
    'mostre com um exemplo mais difícil?'
)


@pytest.mark.parametrize("fala", [
    FALA_HISTORICA,
    'Pense: "quantos grupos consigo formar?"',
    'Pergunte a si mesmo: "qual é o próximo passo?"',
    'Considere a pergunta "qual peça cabe aqui?"',
    'Podemos usar o método de "subtrações sucessivas".',
    'O conceito de "variável" ajuda a nomear um valor.',
    "Não entendi o que você quis dizer com 'quero im'. Pode esclarecer?",
    "O que você quer dizer com 'isso aqui'?",
])
def test_papel_didatico_nao_dispara_pesquisa_de_obra(fala):
    assert extrair_titulos_citados(fala) == []
    validacao = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert validacao["fala"] == fala
    assert not validacao["problemas"]


def test_passos_historicos_sobrevivem_ao_verificador_completo():
    plano = planejar_turno(PEDIDO, turno=classificar_modalidade_turno(PEDIDO))
    resultado = verificar_fala_turno(FALA_HISTORICA, plano=plano, origem="ia_final")
    assert resultado["aceita"]
    for passo in ('6 cabe 3 vezes em 18', '6 × 3 = 18', 'Agrupe 18 em blocos de 6'):
        assert passo in resultado["fala"]
    assert not plano.get("comandos") and not plano["requer_execucao"]


@pytest.mark.parametrize("fala,titulo", [
    ('Recomendo o livro "Divisão por agrupamento".', 'Divisão por agrupamento'),
    ('Pense no filme "Quantos grupos?".', 'Quantos grupos?'),
    ('Pense: "qual é o resultado?". Recomendo "Lua Ausente".', 'Lua Ausente'),
    ('O conceito de "variável" ajuda. O filme "Lua Ausente" é bom.', 'Lua Ausente'),
    ("O que você quer dizer com o filme 'Lua Ausente'?", 'Lua Ausente'),
    ("O que você quer dizer com 'isso'? Recomendo 'Lua Ausente'.", 'Lua Ausente'),
])
def test_moldura_didatica_nao_isenta_obra_vizinha(fala, titulo):
    assert titulo in extrair_titulos_citados(fala)
    assert "obra_sem_evidencia" in validar_fala_com_fundamentacao(fala, fundamentacao=None)["problemas"]


@pytest.mark.parametrize("trecho", [
    'O método de "agrupamento" foi criado em 2025.',
    'O aparelho pesa 70 kg.',
])
def test_nome_de_conceito_nao_certifica_dados_externos(trecho):
    fala = 'Pense: "qual é o resultado?". ' + trecho
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert trecho in resultado["trechos_rejeitados"]
    assert any(p in resultado["problemas"] for p in ("data_sem_evidencia", "medida_sem_evidencia"))


def test_esclarecimento_citando_usuario_nao_vira_fallback_factual():
    fala = "Não entendi o que você quis dizer com 'quero im'. Pode esclarecer?"
    plano = planejar_turno("quero im", turno=classificar_modalidade_turno("quero im"))
    resultado = verificar_fala_turno(fala, plano=plano)
    assert resultado["fala"] == fala
    assert "alegacao_especifica_sem_fonte" not in resultado["problemas"]


def test_composicao_real_preserva_aula_sem_pesquisar_citacao(monkeypatch):
    import importlib
    root = importlib.import_module("laylay")
    plano = planejar_turno(PEDIDO, turno=classificar_modalidade_turno(PEDIDO))
    monkeypatch.setattr(root._estado_compartilhado_runtime, "mental", {"plano_turno_atual": plano})

    def pesquisa_proibida(*args, **kwargs):
        raise AssertionError("pergunta didática foi enviada à pesquisa de obras")

    monkeypatch.setattr(root._pesquisa_contextual_runtime, "pesquisar_contexto_tema", pesquisa_proibida)
    resultado = root._verificar_fala_do_turno(FALA_HISTORICA, origem="ia_final")
    assert resultado["aceita"]
    assert resultado["fala"] == FALA_HISTORICA
    assert not plano.get("comandos")


FALA_INVERSO_HISTORICA = (
    "Não, a divisão não é o contrário da multiplicação. É o inverso, mas não 'o contrário'. "
    "Por exemplo: 4 × 3 = 12, então 12 ÷ 4 = 3. "
    "A divisão pergunta: 'quantas vezes o número cabe?', enquanto a multiplicação é: "
    "'quanto dá se eu somar o número várias vezes?'"
)


@pytest.mark.parametrize("fala", [
    "A divisão 'desfaz' a multiplicação.",
    FALA_INVERSO_HISTORICA,
    "A soma é **repetida** em cada grupo.",
    "Aqui, 'delta' representa o valor que queremos encontrar.",
    "O resultado fica 'guardado' até o próximo cálculo.",
    "O filme é 'bom', mas essa é só minha impressão.",
    "Prefiro explicar isso 'aos poucos', com um exemplo de cada vez.",
])
def test_destaque_sem_indicio_de_obra_nao_vira_titulo(fala):
    # Preservar o texto não certifica a correção matemática da geração.
    assert extrair_titulos_citados(fala) == []
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert resultado["fala"] == fala
    assert not resultado["problemas"]


@pytest.mark.parametrize("fala,titulos", [
    ("Recomendo um filme. Por exemplo: 'Lua Ausente'.", ["Lua Ausente"]),
    ("'Lua Ausente' é um filme.", ["Lua Ausente"]),
    ('Sugiro estes livros: "Lua Ausente", "Mar de Vidro" e "Noite Vazia".',
     ["Lua Ausente", "Mar de Vidro", "Noite Vazia"]),
    ("Recomendo 'Lua Ausente'. A explicação 'desfaz' a dúvida.", ["Lua Ausente"]),
])
def test_indicio_positivo_de_obra_sobrevive_a_divisao_em_frases(fala, titulos):
    assert extrair_titulos_citados(fala) == titulos
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert "obra_sem_evidencia" in resultado["problemas"]
    assert all(t not in resultado["fala"] for t in titulos)


@pytest.mark.parametrize("fala,problema", [
    ("A data é '2025'.", "data_sem_evidencia"),
    ("O peso é '70 kg'.", "medida_sem_evidencia"),
    ("A soma é 'repetida'. O aparelho pesa 70 kg.", "medida_sem_evidencia"),
])
def test_destaque_indeterminado_nao_mascara_alegacao(fala, problema):
    assert extrair_titulos_citados(fala) == []
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None)
    assert problema in resultado["problemas"]


@pytest.mark.parametrize("pedido,fala,esperados", [
    ("me recomenda um filme", "'Lua Ausente'.", ["Lua Ausente"]),
    ("me indica livros", "'Lua Ausente' e 'Mar de Vidro'.", ["Lua Ausente", "Mar de Vidro"]),
    ("me explica divisão", "A divisão 'desfaz' a multiplicação.", []),
    ("me recomenda um filme", "Você prefere algo 'leve' ou 'intenso'?", []),
])
def test_contexto_so_tipifica_resposta_nominal_nao_toda_citacao(pedido, fala, esperados):
    assert extrair_titulos_citados(fala, texto_usuario=pedido) == esperados
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=None, texto_usuario=pedido)
    assert ("obra_sem_evidencia" in resultado["problemas"]) == bool(esperados)


@pytest.mark.parametrize("pedido,fala,titulos", [
    ("entao a divisao é o contrario da multiplicacao?", FALA_INVERSO_HISTORICA, []),
    ("me recomenda um filme", "'Lua Ausente'.", ["Lua Ausente"]),
])
def test_composicao_real_compartilha_papel_da_citacao(monkeypatch, pedido, fala, titulos):
    import importlib
    root = importlib.import_module("laylay")
    plano = planejar_turno(pedido, turno=classificar_modalidade_turno(pedido))
    monkeypatch.setattr(root._estado_compartilhado_runtime, "mental", {"plano_turno_atual": plano})
    pesquisas = []

    def pesquisar(tema):
        pesquisas.append(tema)
        return {}

    monkeypatch.setattr(root._pesquisa_contextual_runtime, "pesquisar_contexto_tema", pesquisar)
    resultado = root._verificar_fala_do_turno(fala, origem="ia_final")
    assert pesquisas == titulos
    assert not plano.get("comandos")
    if not titulos:
        assert resultado["fala"] == fala
    else:
        assert "obra_sem_evidencia" in resultado["problemas"]
