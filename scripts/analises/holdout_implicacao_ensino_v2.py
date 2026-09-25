"""Gabarito P01 congelado antes de testar candidatas neste conjunto.

Cada rótulo diz somente o que o excerto permite concluir, não se a página
inteira ou o mundo confirma a alegação. Sem ajuste pós-medição para elevar nota.
"""

FONTES = {
    "range": {
        "url": "https://docs.python.org/pt-br/3.11/tutorial/controlflow.html",
        "texto": (
            "O ponto de parada fornecido nunca é incluído na lista; "
            "range(10) gera uma lista com 10 valores."
        ),
    },
    "luz": {
        "url": "https://science.nasa.gov/earth/earth-observatory/what-are-phytoplankton/",
        "texto": (
            "Like land plants, phytoplankton have chlorophyll to capture sunlight, "
            "and they use photosynthesis to turn it into chemical energy."
        ),
    },
    "anual": {
        "url": "https://www.rhs.org.uk/advice/beginners-guide/glossary",
        "texto": (
            "Annual - a plant that completes its life cycle "
            "(germination, flowering, seeding, dying) in one growing season."
        ),
    },
    "lua": {
        "url": "https://science.nasa.gov/moon/moon-phases/",
        "texto": (
            "The Sun always illuminates half of the Moon while the other half "
            "remains dark."
        ),
    },
}

# id, fonte, papel, alegação, relação lógica com o excerto.
CASOS = (
    ("R-D1", "range", "definicao", "O ponto de parada do range não integra a sequência gerada.", "sustentada"),
    ("R-D2", "range", "definicao", "O ponto de parada do range sempre integra a sequência gerada.", "contradita"),
    ("R-D3", "range", "definicao", "Todo objeto range ocupa exatamente vinte bytes de memória.", "sem_prova"),
    ("R-E1", "range", "exemplo", "range(10) gera dez valores.", "sustentada"),
    ("R-E2", "range", "exemplo", "range(10) gera onze valores.", "contradita"),
    ("R-E3", "range", "exemplo", "range(10) gera dez valores e imprime todos automaticamente.", "sem_prova"),
    ("L-D1", "luz", "definicao", "Fitoplâncton capta luz com clorofila e usa fotossíntese para transformá-la em energia química.", "sustentada"),
    ("L-D2", "luz", "definicao", "Na fotossíntese do fitoplâncton, energia química vira luz solar em vez do processo descrito.", "contradita"),
    ("L-D3", "luz", "definicao", "A fotossíntese do fitoplâncton leva exatamente sete segundos.", "sem_prova"),
    ("L-E1", "luz", "exemplo", "Num fitoplâncton que faz fotossíntese, a luz captada é transformada em energia química.", "sustentada"),
    ("L-E2", "luz", "exemplo", "Num fitoplâncton que faz fotossíntese, energia química se torna luz solar no lugar do processo descrito.", "contradita"),
    ("L-E3", "luz", "exemplo", "Fitoplâncton capta luz e libera exatamente dez mililitros de oxigênio por hora.", "sem_prova"),
    ("A-D1", "anual", "definicao", "Uma planta anual completa germinação, floração, produção de sementes e morte em uma estação de crescimento.", "sustentada"),
    ("A-D2", "anual", "definicao", "Uma planta anual só completa seu ciclo após três estações de crescimento, nunca em uma.", "contradita"),
    ("A-D3", "anual", "definicao", "Todas as plantas anuais florescem em outubro.", "sem_prova"),
    ("A-E1", "anual", "exemplo", "No caso de uma anual, germinação, floração, sementes e morte ocorrem no mesmo período de crescimento.", "sustentada"),
    ("A-E2", "anual", "exemplo", "Uma planta classificada como anual só morre depois de três estações de crescimento.", "contradita"),
    ("A-E3", "anual", "exemplo", "Uma petúnia anual floresce em outubro e morre em novembro.", "sem_prova"),
    ("M-D1", "lua", "definicao", "O Sol ilumina sempre metade da Lua, enquanto a outra metade permanece escura.", "sustentada"),
    ("M-D2", "lua", "definicao", "O Sol ilumina sempre a Lua inteira e nenhuma parte permanece escura.", "contradita"),
    ("M-D3", "lua", "definicao", "A metade iluminada da Lua está sempre a cem graus Celsius.", "sem_prova"),
    ("M-E1", "lua", "exemplo", "Num instante da órbita lunar, metade da Lua recebe luz do Sol e a outra metade fica escura.", "sustentada"),
    ("M-E2", "lua", "exemplo", "Num instante da órbita lunar, toda a Lua recebe luz do Sol e nenhuma metade fica escura.", "contradita"),
    ("M-E3", "lua", "exemplo", "A metade iluminada da Lua em setembro está a cem graus Celsius.", "sem_prova"),
)
