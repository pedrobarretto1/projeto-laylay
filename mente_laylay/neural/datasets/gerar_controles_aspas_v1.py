"""Contrastes de avaliação, não lote de treino: aspas não mudam a intenção."""

from __future__ import annotations


def gerar_controles() -> list[dict]:
    itens = []
    for entidade, (a, b) in enumerate((("Nimbora", "Seldrin"), ("Tervana", "Orlume"))):
        for dominio, intent, acao, verbo, classe, alvo, alternativa in (
            ("apps", "APP_OPEN", "open", "abra", "aplicativo chamado", a, b),
            ("musica", "MUSIC_SEARCH", "search", "toque", "faixa chamada", f"Não Volte {a}", f"Outra Rota {b}"),
            ("arquivos", "FILE_READ", "read", "leia", "arquivo chamado", f"não apagar {a}.txt", f"rascunho {b}.txt"),
        ):
            for forma in range(2):
                grupo = f"controle_aspas_v1_f{forma}"
                for aspas in (False, True):
                    nome = f'"{alvo}"' if aspas else alvo
                    outro = f'"{alternativa}"' if aspas else alternativa
                    pedido = f"{verbo} o {classe} {nome}" if dominio != "musica" else f"{verbo} a {classe} {nome}"
                    if forma == 0:
                        textos = {"pedido": f"por gentileza, {pedido}",
                                  "correcao": f"{pedido}; eu escolhi {nome}, não {outro}",
                                  "recusa": f"não quero que você {pedido}",
                                  "relato": f"ontem ela disse para não {pedido}"}
                    else:
                        textos = {"pedido": f"agora, {pedido}, por favor",
                                  "correcao": f"{pedido}; minha escolha é {nome}, e não {outro}",
                                  "recusa": f"por favor, não {pedido}; retire esse pedido",
                                  "relato": f"ele contou que ontem pediu para não {pedido}"}
                    for ato, texto in textos.items():
                        relato = ato == "relato"
                        itens.append({
                            "text": texto, "intent": "NONE" if relato else intent,
                            "action": "none" if relato else acao,
                            "is_command": ato in {"pedido", "correcao"},
                            "negated": ato == "recusa",  # No relato não é alvo supervisionado.
                            "training_heads": ["command"] if relato else ["negation"],
                            "source": "COUNTERFACTUAL", "domain": dominio,
                            "family": f"{grupo}_{dominio}_e{entidade}", "validation_group": grupo,
                            "pair_id": f"{grupo}_{dominio}_e{entidade}_{ato}",
                            "com_aspas": aspas, "ato": ato,
                            "particao": "avaliacao_somente", "entidades": [alvo, alternativa],
                        })
    return itens
