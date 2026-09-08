"""Contrastes de desenvolvimento: negar pedido versus negar alternativa.

Templates irmãos de todos os domínios ficam no MESMO grupo de validação.
Somente o head de negação pode consumir estes rótulos. Não são reserva inédita.
"""

from __future__ import annotations


def gerar_exemplos() -> list[dict]:
    dominios = (
        ("audio", "VOLUME", "set", "ajuste o áudio para 23", "para 67"),
        ("apps", "APP_OPEN", "open", "inicie o Krita", "o Inkscape"),
        ("musica", "MUSIC_SEARCH", "search", "reproduza a canção Horizonte Azul", "a canção Caminho Lunar"),
        ("arquivos", "FILE_READ", "read", "leia inventario_setembro.txt", "balanco_janeiro.txt"),
    )
    # Cada mecanismo inclui oposição verdadeira. A frase negativa é um veto
    # ao pedido inteiro, não dois comandos com autorizações diferentes.
    formas = {
        "virgula_alternativa": (
            (False, "{pedido}, não {alternativa}"),
            (True, "não {pedido}, por gentileza"),
        ),
        "conjuncao_alternativa": (
            (False, "{pedido} e não {alternativa}"),
            (True, "por gentileza, não {pedido}"),
        ),
        "em_vez": (
            (False, "{pedido} em vez de usar {alternativa}"),
            (True, "de jeito nenhum {pedido}"),
        ),
        "preferencia_explicita": (
            (False, "quero que você {pedido}, não {alternativa}"),
            (True, "não quero que você {pedido}"),
        ),
        "restricao_alternativa": (
            (False, "por favor, {pedido}; a alternativa não é {alternativa}"),
            (True, "por favor, não {pedido}; esse pedido está cancelado"),
        ),
        "cancelamento_tardio": (
            (False, "{pedido}; confirme somente depois"),
            (True, "{pedido}; quer dizer, não faça isso"),
        ),
    }
    exemplos = []
    for mecanismo, formas_rotuladas in formas.items():
        for dominio, intent, acao, pedido, alternativa in dominios:
            for negada, forma in formas_rotuladas:
                exemplos.append({
                    "text": forma.format(pedido=pedido, alternativa=alternativa),
                    "intent": intent, "action": acao, "is_command": not negada,
                    "negated": negada, "domain": dominio,
                    "family": f"escopo_negacao_v1_{mecanismo}_{dominio}",
                    "validation_group": f"escopo_negacao_v1_{mecanismo}",
                    "source": "MANUAL_PARAPHRASE", "training_heads": ["negation"],
                })
    # Nomes são literais sintéticos, sem afirmação de existência.
    for dominio, intent, acao, verbo, nome in (
        ("arquivos", "FILE_READ", "read", "leia o arquivo", "não executar.txt"),
        ("musica", "MUSIC_SEARCH", "search", "reproduza a faixa", "Não Vá Embora"),
    ):
        for negada in (False, True):
            exemplos.append({
                "text": f'{"não " if negada else ""}{verbo} "{nome}"',
                "intent": intent, "action": acao, "is_command": not negada,
                "negated": negada, "domain": dominio,
                "family": f"escopo_negacao_v1_literal_{dominio}",
                "validation_group": "escopo_negacao_v1_literal",
                "source": "MANUAL_PARAPHRASE", "training_heads": ["negation"],
            })
    return exemplos
