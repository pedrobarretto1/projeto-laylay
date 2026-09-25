"""A medição separa código sintático de exemplo factual comprovado."""

from scripts.analises.medir_cobertura_exemplos import extrair_tipos_de_pagina


def test_pagina_python_conta_bloco_sintatico_sem_saida_confirmada() -> None:
    html = (
        "<p>Este exemplo percorre uma sequência.</p>"
        '<pre><code class="language-python">for i in range(3):\n    print(i)</code></pre>'
    )
    tipos = extrair_tipos_de_pagina(html, "https://exemplo.org/python", "laço for em Python", "laço for")
    assert tipos["exemplos"] == []
    assert len(tipos["codigos"]) == 1
    assert tipos["codigos"][0]["tipo"] == "codigo_python"
    assert tipos["codigos"][0]["saida_confirmada"] is None


def test_transcricao_nao_conta_como_bloco_python_puro() -> None:
    html = '<pre><span>&gt;&gt;&gt; </span>print(2 + 2)\n4</pre>'
    tipos = extrair_tipos_de_pagina(html, "https://exemplo.org/python", "laço for em Python", "laço for")
    assert tipos["codigos"] == []


def test_codigo_python_de_outro_conceito_nao_ajuda_cobertura_do_for() -> None:
    html = '<pre><code class="language-python">print(2 + 2)</code></pre>'
    tipos = extrair_tipos_de_pagina(html, "https://exemplo.org/python", "laço for em Python", "laço for")
    assert tipos["codigos"] == []
