"""Grade fatorial de escopo, com reservas separadas antes de qualquer fit.

Nomes são alvos sintéticos, não uma declaração de aplicativos/faixas existentes.
Somente a negação é rotulada para treino; catálogo e executor não mudam.
"""

from __future__ import annotations


PARES = (
    ("Cedrion", "Belmora", 14, 28),
    ("Nuvarel", "Dorvila", 19, 37),
    ("Solmira", "Ferlume", 26, 44),
    ("Brisalto", "Lunvero", 32, 58),
    ("Veldora", "Calmire", 41, 63),
    ("Orvante", "Melquira", 47, 72),
    # Estes dois pares nunca entram em treino, em nenhum domínio.
    ("Zelvoria", "Tarselio", 83, 96),
    ("Quirvante", "Nelmoria", 89, 98),
)

FORMAS = (
    ((False, "{pedido}, não {alternativa}"), (True, "não {pedido}, por gentileza")),
    ((False, "{pedido} e não {alternativa}"), (True, "por gentileza, não {pedido}")),
    ((False, "por favor, {pedido}; a alternativa não é {alternativa}"),
     (True, "por favor, não {pedido}; esse pedido está cancelado")),
    ((False, "quero que você {pedido}, não {alternativa}"),
     (True, "não quero que você {pedido}")),
    # Construções reservadas: não usadas na grade de treino.
    ((False, "o que peço é: {pedido}; não estou pedindo {alternativa}"),
     (True, "o que peço é: não {pedido}; mantenha tudo como está")),
    ((False, "{pedido}; ignore a opção {alternativa}"),
     (True, "{pedido}? Não, cancele esse pedido.")),
)


def gerar_grade() -> list[dict]:
    itens = []
    for entidade, (a, b, valor, outro) in enumerate(PARES):
        dominios = (
            ("audio", "VOLUME", "set", f"ajuste o áudio para {valor}", f"para {outro}", [str(valor), str(outro)]),
            ("apps", "APP_OPEN", "open", f"inicie o {a}", f"o {b}", [a, b]),
            ("musica", "MUSIC_SEARCH", "search", f'reproduza a canção "Rota {a}"', f'a canção "Rota {b}"', [a, b]),
            ("arquivos", "FILE_READ", "read", f"leia inventario_{a}.txt", f"inventario_{b}.txt", [a, b]),
            ("musica_literal", "MUSIC_SEARCH", "search", f'reproduza a faixa "Não Volte {a}"', f'a faixa "Nunca Pare {b}"', [a, b]),
            ("arquivo_literal", "FILE_READ", "read", f'leia o arquivo "não executar {a}.txt"', f'o arquivo "não executar {b}.txt"', [a, b]),
        )
        for construcao, formas in enumerate(FORMAS):
            particao = (
                "treino" if entidade < 6 and construcao < 4 else
                "entidade" if entidade >= 6 and construcao < 4 else
                "construcao" if entidade < 6 else "ambas"
            )
            for dominio, intent, acao, pedido, alternativa, entidades in dominios:
                for negada, forma in formas:
                    itens.append({
                        "text": forma.format(pedido=pedido, alternativa=alternativa),
                        "intent": intent, "action": acao, "negated": negada,
                        "is_command": not negada, "domain": dominio,
                        "family": f"escopo_v2_c{construcao}_{dominio}_e{entidade}",
                        "validation_group": f"escopo_v2_c{construcao}",
                        "validation_entity_group": f"escopo_v2_e{entidade}",
                        "training_heads": ["negation"], "source": "MANUAL_PARAPHRASE",
                        "particao": particao, "entidades": entidades,
                    })
    return itens
