"""Classificação única da natureza de cada turno da Laylay."""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_local,
)
from mente_laylay.cognicao.referencias_linguagem import (
    texto_pede_aba_anterior,
)
from mente_laylay.cognicao.gramatica_operacional import (
    texto_pede_avanco_midia_via_vai,
    texto_pede_restauracao_contextual,
)
from mente_laylay.arquivos.nome_natural import (
    aspas_globalmente_coerentes,
    marcador_negacao_em_filename_literal,
)

from mente_laylay.cognicao.normalizacao_linguagem import (
    corrigir_erros_portugues_operacionais,
)
from mente_laylay.cognicao.gramatica_musical import (
    analisar_gramatica_musical,
    texto_tem_relevancia_musical,
)


def analisar_protecao_operacional(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
) -> Dict[str, Any]:
    """Lê negação, hipótese e pergunta antes de qualquer intenção prática."""
    normalizar = normalizar_texto if callable(normalizar_texto) else (
        lambda valor: str(valor or "").casefold().strip()
    )
    t = re.sub(r"\s+", " ", str(normalizar(texto) or "")).strip()
    neutra = {
        "bloqueia_execucao": False,
        "modalidade": "",
        "natureza_acao": "nenhuma",
        "motivo": "",
    }
    if not t:
        return neutra
    if re.search(r"^(?:nao|não)\s+\w+.*\b(?:qu[eê]|qual|porque|por que)\b", t):
        return {
            "bloqueia_execucao": True,
            "modalidade": "pergunta",
            "natureza_acao": "instrucao_ou_explicacao",
            "motivo": "pergunta negativa sobre ação",
        }
    if re.search(
        r"\b(?:acho que (?:eu )?vou|talvez|estou pensando em|to pensando em|"
        r"seria bom|seria legal|quem sabe|tenho vontade de|estou com vontade de|"
        r"to com vontade de|queria saber|se eu (?:pedir|quiser|mandar|falar|disser)|"
        r"quando (?:voce|você|eu|a gente)|caso (?:eu|voce|você|a gente))\b",
        t,
    ):
        return {
            "bloqueia_execucao": True,
            "modalidade": "deliberacao",
            "natureza_acao": "hipotetica",
            "motivo": "intenção hipotética ou reflexão",
        }
    if (
        re.search(
            r"^(?:voce|você|tu)\s+(?:pode|poderia|consegue|conseguiria|sabe)\s+(?:me\s+)?"
            r"(?:ver|olhar|olha|resume|resuma|resumir|mostrar|passar|criar|abrir|"
            r"fechar|apagar|tocar|ligar|desligar|mexer|organizar|procurar|"
            r"adicionar|acrescentar)\b",
            t,
        )
        and not re.search(r"\b(?:pra|para)\s+mim\b", t)
    ):
        return {
            "bloqueia_execucao": True,
            "modalidade": "pergunta",
            "natureza_acao": "capacidade",
            "motivo": "pergunta sobre capacidade; não é autorização",
        }
    if re.search(
        r"^(?:nao|não|nunca|jamais)\s+(?:(?:pode|deve|vai)\s+)?(?:me\s+)?"
        r"(?:abre|abra|fecha|feche|liga|ligue|acende|desliga|desligue|toca|"
        r"toque|coloca|coloque|cria|crie|apaga|apague|remove|remova|deleta|"
        r"delete|move|mova|renomeia|renomeie|escreve|escreva|grava|grave|"
        r"adiciona|adicione|acrescenta|acrescente|"
        r"muda|ajusta|deixa|olha|olhe|veja|ver|captura|capture|mostra|"
        r"mostre|passa|passe|resume|resuma|explique|maximiza|maximize|"
        r"organiza|organize|pesquisa|pesquise|busca|busque|encontra|encontre)\b",
        t,
    ):
        return {
            "bloqueia_execucao": True,
            "modalidade": "recusa",
            "natureza_acao": "cancelamento",
            "motivo": "negação operacional",
        }
    if re.search(
        r"^(?:como(?:\s+(?:eu\s+)?)?(?:faria|fa[cç]o|posso|poderia)?|"
        r"onde|quando|por\s+que|porque|qual\s+(?:a\s+)?forma\s+de|"
        r"o\s+que\s+(?:eu\s+)?(?:faria|fa[cç]o)|o\s+que\s+acontece\s+se)\b"
        r".*\b(?:abrir|fechar|ligar|desligar|tocar|colocar|criar|apagar|"
        r"remover|usar|fazer|resumir|explicar|ver|olhar|mostrar|passar|"
        r"adicionar|acrescentar)\b",
        t,
    ) or re.search(r"\b(?:queria|gostaria)\s+de\s+saber\s+como\b", t) or re.search(
        r"^como\s+(?:eu\s+)?(?:abriria|fecharia|criaria|apagaria|removeria|"
        r"tocaria|ligaria|desligaria|maximizaria|organizaria|usaria|faria|"
        r"adicionaria|acrescentaria)\b",
        t,
    ):
        return {
            "bloqueia_execucao": True,
            "modalidade": "pergunta",
            "natureza_acao": "instrucao_ou_explicacao",
            "motivo": "pergunta informativa sobre uma ação",
        }
    return neutra


def _eh_politica_condicional_abertura_observavel(
    texto: str,
    normalizar_texto: Callable[[str], str] | None = None,
) -> bool:
    """Reconhece a política atômica abrir-se-fechado/avisar-se-aberto.

    A condição negativa descreve o estado observado, não uma revogação da
    ordem. A moldura é deliberadamente estrita: exige as duas consequências,
    rejeita perguntas e não interpreta condicionais genéricos como autoridade.
    """
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not bruto or "?" in bruto:
        return False
    normalizar = normalizar_texto if callable(normalizar_texto) else (
        lambda valor: str(valor or "").casefold().strip()
    )
    t = re.sub(r"\s+", " ", str(normalizar(bruto) or "")).strip()
    return bool(re.fullmatch(
        r"se\s+(?:(?:o|a)\s+)?(?P<alvo>.+?)\s+(?:nao|não)\s+"
        r"estiver\s+abert[oa]\s*,?\s*(?:abre|abra)"
        r"(?:\s+(?:ele|ela|o\s+app|a\s+janela))?\s*"
        r"(?:[;,]\s*)?se\s+(?:ja|já)\s+estiver\s*,?\s*"
        r"(?:(?:so|só)\s+)?me\s+avisa[.!]*",
        t,
        flags=re.IGNORECASE,
    ))


def _classificar_modalidade_base(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
    texto_tem_comando_explicito: Callable[[str], bool] | None = None,
    confirmacao_contextual_valida: bool = False,
) -> Dict[str, Any]:
    bruto = str(texto or "").strip()
    normalizar = normalizar_texto if callable(normalizar_texto) else (lambda valor: str(valor or "").casefold().strip())
    t = re.sub(r"\s+", " ", str(normalizar(bruto) or "")).strip()
    resultado = {
        "id": time.time_ns(), "texto": bruto[:500], "normalizado": t[:500],
        "modalidade": "conversa", "confianca": 0.60,
        "motivo": "fala sem marcador operacional dominante", "ts": time.time(),
        "acao_explicita": False,
        "autoriza_execucao": False,
        "requer_esclarecimento": False,
        "depende_contexto": False,
        "natureza_acao": "nenhuma",
        "confirmacao_contextual_valida": bool(confirmacao_contextual_valida),
    }
    if not t:
        resultado.update(modalidade="vazio", confianca=1.0, motivo="entrada vazia")
        return resultado

    if _eh_politica_condicional_abertura_observavel(
        bruto,
        normalizar_texto=normalizar_texto,
    ):
        resultado.update(
            modalidade="comando",
            confianca=0.99,
            motivo="política condicional explícita de abertura e observação",
            acao_explicita=True,
            autoriza_execucao=True,
            natureza_acao="pedido_condicional",
        )
        return resultado

    # Adiamentos curtos encerram ou pausam a ação anterior. Embora comecem
    # por verbos no imperativo ("deixa", "vemos", "fazemos"), não autorizam
    # uma nova execução. Esta leitura precisa vir antes do detector geral de
    # imperativos para que "deixa para depois" não vire um comando sem alvo.
    if re.fullmatch(
        r"(?:melhor\s+)?(?:deixa|deixar|deixe|deixamos|vamos\s+deixar)"
        r"(?:\s+(?:isso|essa|esse|ela|ele))?\s+(?:pra|para)\s+depois|"
        r"(?:isso\s+)?(?:fica|pode\s+ficar)\s+(?:pra|para)\s+depois|"
        r"(?:a\s+gente\s+)?(?:ve|v[eê]|vemos|faz|fazemos)"
        r"(?:\s+isso)?\s+depois",
        t,
    ):
        resultado.update(
            modalidade="recusa",
            confianca=0.99,
            motivo="adiamento explícito sem autorização",
            natureza_acao="adiamento",
            depende_contexto=True,
            autoriza_execucao=False,
        )
        return resultado
    protecao = analisar_protecao_operacional(
        t,
        normalizar_texto=lambda valor: str(valor or "").strip(),
    )
    if protecao["bloqueia_execucao"] and protecao["motivo"] == "pergunta negativa sobre ação":
        resultado.update(
            modalidade=protecao["modalidade"], confianca=0.99,
            motivo=protecao["motivo"], natureza_acao=protecao["natureza_acao"],
        )
        return resultado
    if re.search(
        r"^(?:na verdade|eu quis dizer|quis dizer|nao lay|não lay|to falando de|estou falando de|"
        r"eu (?:nao|não) pedi|(?:nao|não) te pedi|eu te perguntei|eu perguntei|como assim.+eu .*perguntei)\b",
        t,
    ):
        resultado.update(modalidade="correcao", confianca=0.99, motivo="reparação explícita", natureza_acao="correcao")
        return resultado
    if re.search(
        r"^(?:voce|você|tu)\s+(?:nao|não)\s+"
        r"(?:conseguiu|conseguil|consegue|conseguiu|pode|pôde)\b|"
        r"^(?:voce|você|tu)\s+(?:falhou|errou)\b",
        t,
    ):
        resultado.update(
            modalidade="reacao",
            confianca=0.99,
            motivo="observação sobre resultado anterior; não autoriza nova execução",
            natureza_acao="feedback_resultado",
            depende_contexto=True,
            autoriza_execucao=False,
        )
        return resultado
    if protecao["bloqueia_execucao"]:
        resultado.update(
            modalidade=protecao["modalidade"],
            confianca=0.98 if protecao["modalidade"] != "deliberacao" else 0.97,
            motivo=protecao["motivo"],
            natureza_acao=protecao["natureza_acao"],
            depende_contexto=protecao["modalidade"] == "recusa",
            requer_esclarecimento=protecao["natureza_acao"] == "capacidade",
        )
        return resultado

    # ROOT_AUTORIDADE_RESTAURACAO_V1_20260823
    # A fala atual fornece autoridade. O alvo continua dependendo de contexto
    # operacional válido no domínio proprietário; este classificador não
    # inventa alvo, não consulta lixeira e não contorna a P0.
    if texto_pede_restauracao_contextual(t):
        resultado.update(
            modalidade="comando",
            confianca=0.99,
            motivo="pedido explícito de restauração contextual",
            acao_explicita=True,
            autoriza_execucao=True,
            depende_contexto=True,
            natureza_acao="pedido_direto",
        )
        return resultado

    if re.match(
        r"^(?:eu\s+)?(?:achei|pensei|entendi)\s+que\s+(?:voc[eê]|tu)\s+ia\s+"
        r"(?:colocar|tocar|abrir|fechar|ligar|desligar|fazer|executar)\b",
        t,
    ):
        resultado.update(
            modalidade="reacao", confianca=0.99,
            motivo="expectativa sobre ação passada; não autoriza execução",
            natureza_acao="decepcao",
        )
        return resultado

    decisao_curta = classificar_confirmacao_local(t)
    # Verbos curtos podem confirmar uma pendência ("abre") ou iniciar um
    # comando que ainda carece de alvo. Sem pendência válida, deixamos o
    # classificador operacional decidir e pedir o alvo, em vez de convertê-los
    # em confirmação social.
    verbo_operacional_sem_contexto = bool(re.fullmatch(
        r"(?:abre|coloca|toca|play|da play|fecha|liga|desliga|apaga|remove)",
        t,
    ))
    if decisao_curta is True and (
        confirmacao_contextual_valida or not verbo_operacional_sem_contexto
    ):
        resultado.update(
            modalidade="confirmacao", confianca=0.98,
            motivo=("confirmação ligada a pendência ativa" if confirmacao_contextual_valida else "confirmação social sem pendência acionável"),
            natureza_acao="confirmacao_contextual",
            depende_contexto=True,
            autoriza_execucao=bool(confirmacao_contextual_valida),
        )
        return resultado
    if decisao_curta is False:
        resultado.update(modalidade="recusa", confianca=0.98, motivo="recusa curta explícita")
        return resultado
    if re.fullmatch(
        r"(?:h+m+|hum+|entendi|tendi|ta bom|tá bom|ah ta|ah tá|ata|nossa|"
        r"caramba|pois e|pois é|e ne|e né|ne|né)(?: entao| então)?",
        t,
    ):
        resultado.update(modalidade="reacao", confianca=0.92, motivo="reação curta à fala anterior")
        return resultado
    # Repetição curta no imperativo é uma ordem contextual completa. A camada
    # de continuidade ainda decide se o recibo anterior é reexecutável; esta
    # classificação fornece apenas a autoridade da fala atual. Expressões como
    # "obrigado de novo" não casam e continuam conversacionais.
    if re.fullmatch(
        r"(?:tenta|tente|repete|repita|faz|fa[cç]a)\s+"
        r"(?:de\s+novo|novamente|outra\s+vez)",
        t,
    ):
        resultado.update(
            modalidade="comando",
            confianca=0.99,
            motivo="pedido explícito de repetição contextual",
            acao_explicita=True,
            autoriza_execucao=True,
            depende_contexto=True,
            natureza_acao="pedido_direto",
        )
        return resultado
    if re.fullmatch(
        r"(?:essa|esse|esta|este|isso)\s+(?:tambem|também)",
        t,
    ):
        resultado.update(
            modalidade="comando",
            confianca=0.97,
            motivo="continuação aditiva contextual explícita",
            acao_explicita=True,
            autoriza_execucao=True,
            depende_contexto=True,
            natureza_acao="pedido_direto",
        )
        return resultado
    # O usuário pode mencionar o nome da playlist sem repetir a palavra
    # "playlist": "quais músicas eu tenho em Kamaitachi" ainda é uma
    # consulta ao catálogo local, não uma pergunta factual para a conversa.
    if re.search(r"\b(?:quais|quantas|lista|listar|liste|mostra|mostrar|mostre)\b", t) and re.search(
        r"\b(?:musicas|músicas|faixas)\b", t
    ) and re.search(
        r"\b(?:eu\s+tenho|tenho|tem|salvas?|guardadas?|em|na|no|da|do)\b", t
    ):
        resultado.update(
            modalidade="comando", confianca=0.98,
            motivo="consulta explícita às faixas de uma playlist local",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado

    # Inventários locais são consultas operacionais, mesmo quando formulados
    # como pergunta. Sem esta distinção, "quais minhas playlists" cai na
    # conversa generativa e a LLM pode inventar nomes em vez de ler o arquivo.
    if re.search(r"\bplaylists?\b", t) and re.search(
        r"\b(?:que|quais|quantas|lista|listar|liste|mostra|mostrar|mostre|"
        r"fale|fala|diga|diz)\b",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.99,
            motivo="consulta explícita ao inventário local de playlists",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado
    if re.search(r"\b(?:e-?mail|emails?)\b", t) and re.search(
        r"\b(?:que|quais|quantos|lista|listar|mostra|mostrar|mostre|fale|fala|"
        r"diga|diz|leia|ler|resuma|resumo)\b",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.99,
            motivo="consulta explícita à caixa de e-mail",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado
    # Consultas a estado local são operações de leitura. Elas precisam chegar
    # ao especialista determinístico em vez de cair na conversa generativa.
    if (
        re.search(
            r"\b(?:como\s+(?:esta|está|ta|tá|ficou|se\s+encontra)|"
            r"qual\s+(?:e|é)\s+(?:o\s+)?(?:status|estado)|"
            r"mostra|mostrar|consulta|consultar|status|estado)\b",
            t,
        )
        and re.search(r"\b(?:lampada|lâmpada|luz|tomada|ventilador|dispositivo|aparelho|iot)\b", t)
    ) or re.search(
        r"\b(?:quais|que|lista|listar|mostra|mostrar)\b.*\b(?:programas|aplicativos|apps|janelas)\b.*\b(?:abert[oa]s?|rodando|execucao|execução)\b",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.99,
            motivo="consulta explícita a estado local",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado
    if texto_pede_aba_anterior(t, permitir_cadeia=True):
        resultado.update(
            modalidade="comando",
            confianca=0.99,
            motivo="navegação explícita para a aba anterior",
            acao_explicita=True,
            autoriza_execucao=True,
            natureza_acao="pedido_direto",
        )
        return resultado
    if texto_pede_avanco_midia_via_vai(t, permitir_cadeia=True):
        resultado.update(
            modalidade="comando", confianca=0.99,
            motivo="controle explícito da mídia atual",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="pedido_direto",
        )
        return resultado
    if re.fullmatch(
        r"(?:(?:para|pare|pausa|pause)\s+(?:a\s+)?m[uú]sica|"
        r"(?:volta|retoma|continua)\s+(?:a\s+)?(?:tocar|m[uú]sica)|"
        r"(?:pr[oó]xima)(?:\s+(?:m[uú]sica|faixa))?|"
        r"volta\s+(?:para|pra)\s+(?:a\s+)?anterior|"
        r"(?:m[uú]sica|faixa)\s+anterior)"
        r"[.!?]*",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.99,
            motivo="controle explícito da mídia atual",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="pedido_direto",
        )
        return resultado
    if re.search(
        r"^(?:(?:lay|laylay)[, ]+)?(?:por\s+favor\s+)?(?:"
        r"me\s+lembra(?:\s+(?:de|pra|para))?|"
        r"lembra(?:-me)?\s+(?:de|pra|para)|me\s+avisa|"
        r"cria\s+(?:um\s+)?lembrete|agende|agendar)\b",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.99, motivo="pedido explícito de agendamento",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="pedido_direto",
        )
        return resultado
    if re.search(
        r"^(?:o\s+que\s+(?:essa|esta)\s+(?:pagina|página|site|video|vídeo|aba)\b|"
        r"(?:(?:me|pra\s+mim|para\s+mim)\s+)?"
        r"(?:resume|resuma|resumir|leia|ler|verifique|explica|explique)\b.*"
        r"\b(?:pagina|página|site|video|vídeo|aba)\b)",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.97,
            motivo="consulta explícita de conteúdo atual",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado
    if re.search(
        r"^(?:o\s+que\s+(?:tem|ha|há|aparece)\s+(?:na|em)\s+(?:minha\s+)?tela\b|"
        r"(?:olha|olhe|veja|ver|captura|capture)\b.*\b(?:minha\s+)?tela\b|"
        r"tira\s+(?:um\s+)?print\b)",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.99,
            motivo="consulta visual explícita da tela atual",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado
    if re.search(
        r"^(?:(?:me\s+)?(?:passa|passe|mostra|mostre|fala|fale|diz|diga|"
        r"repete|repita)\b.*\bbriefing\b|"
        r"qual\s+(?:(?:e|é)\s+)?(?:o\s+)?briefing\b)",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.99,
            motivo="consulta explícita ao briefing observado",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado
    if re.search(
        r"^(?:pesquisa|pesquisar|busca|buscar|procura|procurar|encontra|encontre|"
        r"acha|ache|localiza|localize)\b\s+.+|"
        r"^(?:pula|pule|passa|tira|remove)\b.*\b(?:anuncio|anúncio|propaganda)\b|"
        r"^(?:proxima|próxima)\s+(?:musica|música|faixa)|^(?:musica|música)\s+anterior|"
        r"^(?:olha|veja|ver|captura|capture)\b.*\b(?:minha\s+)?tela\b|^tira\s+(?:um\s+)?print\b|"
        r"^(?:trava|bloqueia)\b.*\b(?:pc|computador|tela)\b|"
        r"^(?:volume\s+(?:maximo|máximo|minimo|mínimo|mudo|\d{1,3})|mute|mudo|desmuta)\b",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.98,
            motivo="comando determinístico explícito",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="pedido_direto",
        )
        return resultado

    # Um desejo formulado como estado imediato continua sendo um pedido
    # direto quando o usuário explicita que quer o alvo aberto ``agora``.
    # Sem esse marcador temporal, frases como "seria legal ter..." continuam
    # deliberativas e não concedem autorização.
    if re.fullmatch(
        r"(?:eu\s+)?(?:queria|gostaria)\s+que\s+(?:(?:o|a)\s+)?"
        r".+?\s+estivesse\s+abert[oa]\s+agora[.!?]*",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.96,
            motivo="estado operacional imediato pedido explicitamente",
            acao_explicita=True, autoriza_execucao=True,
            natureza_acao="pedido_direto",
        )
        return resultado
    if re.match(
        r"^(?:troca|troque|muda|mude|altera|altere|remarca|remarque)\b"
        r".*\b(?:amanh[ãa]|hoje|\d{1,2}(?::\d{2}|\s+horas?))\b",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.96,
            motivo="reagendamento contextual com novo horário explícito",
            acao_explicita=True, autoriza_execucao=True,
            depende_contexto=True, natureza_acao="pedido_direto",
        )
        return resultado

    # Perguntas de conhecimento ou capacidade são respondidas; não executadas.
    if re.search(
        r"\b(?:voce|você)\s+(?:viu|conhece|soube|sabe\s+(?:o\s+que|quem|como)|"
        r"tem\s+capacidade|e\s+capaz|é\s+capaz)|\b(?:ja|já)\s+ouviu\s+falar\b",
        t,
    ):
        resultado.update(modalidade="pergunta", confianca=0.98, motivo="pergunta sobre conhecimento ou capacidade", natureza_acao="capacidade")
        return resultado
    pedido_polido = bool(re.search(
        r"^(?:por favor\s+)?(?:pode|poderia|consegue|conseguiria)\s+(?:me\s+)?"
        r"(?:abrir|abre|fechar|fecha|ligar|liga|desligar|desliga|tocar|toca|colocar|"
        r"coloca|criar|apagar|ler|leia|ver|olhar|mostrar|passar|verificar|verifique|resumir|resuma|resume|"
        r"encontrar|encontra|achar|acha|localizar|localiza)\b",
        t,
    ))
    pedido_para_mim = bool(re.search(
        r"^(?:voce|você)\s+(?:pode|poderia|consegue|conseguiria)\s+.*\b(?:pra|para)\s+mim\b",
        t,
    ))
    imperativo_direto = bool(re.search(
        r"^(?:por favor\s+)?(?:abre|abra|fecha|feche|liga|ligue|desliga|desligue|"
        r"toca|toque|coloca|coloque|deixa|deixe|bota|põe|poe|cria|crie|apaga|remove|deleta|"
        r"restaura|restaure|recupera|recupere|"
        r"maximiza|organiza|pausa|retoma|aumenta|abaixa|diminui|resume|resuma|"
        r"leia|verifique|encontra|encontre|acha|ache|localiza|localize|"
        r"escreve|escreva|grava|grave|adiciona|adicione|"
        r"acrescenta|acrescente)\b",
        t,
    ))
    comando_detectado = False
    if callable(texto_tem_comando_explicito):
        try:
            comando_detectado = bool(texto_tem_comando_explicito(t))
        except Exception:
            comando_detectado = False
    capacidade_ambigua = bool(re.search(
        r"^(?:voce|você)\s+(?:pode|poderia|consegue|conseguiria)\s+(?:me\s+)?"
        r"(?:abrir|fechar|ligar|desligar|tocar|colocar|criar|apagar|ler|ver|olhar|mostrar|passar|verificar|resumir|"
        r"encontrar|achar|localizar)\b",
        t,
    )) and not pedido_para_mim
    if capacidade_ambigua:
        resultado.update(
            modalidade="pergunta", confianca=0.88,
            motivo="pedido de capacidade ambíguo; execução não presumida",
            natureza_acao="capacidade", requer_esclarecimento=True,
        )
        return resultado
    if imperativo_direto or pedido_polido or pedido_para_mim or comando_detectado:
        palavras = t.split()
        alvo_pronominal = bool(re.search(r"\b(?:ele|ela|isso|essa|esse|aquela|aquele)\b", t))
        alvo_ausente = len(palavras) <= 1
        # C1-B: em ``maximiza`` a ação mutante está explícita no turno atual.
        # O alvo continua pendente e só pode ser fornecido pelo contexto tipado;
        # esta exceção não transforma outros verbos sem alvo em autorização.
        acao_eliptica_contextual_autorizada = bool(
            alvo_ausente
            and t == "maximiza"
        )
        resultado.update(
            modalidade="comando",
            confianca=0.98 if (imperativo_direto or pedido_para_mim) and not alvo_ausente else 0.82,
            motivo="pedido prático explícito" if not alvo_ausente else "verbo operacional sem alvo",
            acao_explicita=True,
            autoriza_execucao=(
                not alvo_ausente
                or acao_eliptica_contextual_autorizada
            ),
            requer_esclarecimento=alvo_ausente,
            depende_contexto=alvo_pronominal or alvo_ausente,
            natureza_acao="pedido_direto",
        )
        return resultado

    # "Você consegue abrir X?" sem "para mim" é ambíguo: pode ser teste de
    # capacidade. A Laylay responde ou esclarece, mas não age por suposição.
    interrogativos = r"(?:como|qual|quais|quem|quando|onde|porque|por que|o que|que tal|vamos fazer o que)"
    if "?" in bruto or re.search(rf"^(?:e\s+|mas\s+|entao\s+)?{interrogativos}\b", t):
        resultado.update(modalidade="pergunta", confianca=0.94, motivo="pergunta nova")
        return resultado
    if re.search(r"\b(?:obrigado|obrigada|valeu|gostei|adorei|odeio|nao gosto|não gosto)\b", t):
        resultado.update(modalidade="reacao", confianca=0.88, motivo="reação ou preferência")
    return resultado


_VERBOS_COMANDO = re.compile(
    r"\b(?:abre|abrir|abra|fecha|fechar|feche|liga|ligar|ligue|desliga|desligar|"
    r"desligue|toca|tocar|toque|coloca|colocar|coloque|deixa|deixar|deixe|bota|põe|poe|cria|criar|"
    r"crie|apaga|apagar|remove|remover|deleta|deletar|maximiza|maximizar|pausa|"
    r"pausar|retoma|aumenta|abaixa|diminui|organiza|agende|agendar|me lembra|me avisa|"
    r"leia|ler|lê|le|pesquisa|pesquisar|busca|buscar|procura|procurar|"
    r"encontra|encontre|achar|acha|ache|localiza|localize|pula|pule|"
    r"captura|capture|trava|bloqueia|escreve|escrever|escreva|grava|gravar|grave|"
    r"adiciona|adicionar|adicione|acrescenta|acrescentar|acrescente|"
    r"restaura|restaurar|restaure|recupera|recuperar|recupere)\b",
    re.IGNORECASE,
)


_PERGUNTA_RECIPROCA_FINAL = re.compile(
    r"(?:[,;]\s*|\s+)"
    r"(?P<sufixo>(?:(?:mas\s+)?e\s+)?(?:"
    r"(?:o|a)\s+(?:seu|sua|teu|tua)|"
    r"(?:voc[eê]|tu)|"
    r"(?:do|da)\s+(?:seu|teu)\s+lado|"
    r"por\s+a[ií]|"
    r"como\s+(?:foi|est[aá]|t[aá])\s+(?:(?:o|a)\s+)?(?:seu|sua|teu|tua)"
    r"))\?\s*$",
    flags=re.IGNORECASE,
)


def texto_tem_pergunta_reciproca_apos_resposta(texto: str) -> bool:
    """Reconhece respostas seguidas de pergunta elíptica: ``estou bem, e o seu?``."""
    t = re.sub(r"\s+", " ", str(texto or "").strip().casefold())
    if not t.endswith("?"):
        return False
    reciproca = _PERGUNTA_RECIPROCA_FINAL.search(t)
    if not reciproca:
        return False
    prefixo = t[:reciproca.start()].strip(" ,;")
    return len(prefixo.split()) >= 2


_CLASSES_MUSICA_OWNED = frozenset({
    "pedido_direto",
    "consulta_estado",
    "referencia_ambigua",
})

def _normalizar_operacional_ato(
    texto: str,
    normalizar_texto: Callable[[str], str] | None,
) -> str:
    normalizar = normalizar_texto if callable(normalizar_texto) else (
        lambda valor: str(valor or "").casefold().strip()
    )
    return re.sub(r"\s+", " ", str(normalizar(texto) or "")).strip()

def _detector_lexical_ancorado(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None,
    texto_tem_comando_explicito: Callable[[str], bool] | None,
) -> bool:
    """
    R9b: o detector amplo só complementa a gramática quando o verbo
    operacional está ancorado no começo do ATO atual.
    """
    if not callable(texto_tem_comando_explicito):
        return False

    t = _normalizar_operacional_ato(texto, normalizar_texto)
    t = re.sub(r"^(?:agora|entao)\s+", "", t).strip()
    if not t:
        return False

    try:
        if not bool(texto_tem_comando_explicito(t)):
            return False
    except Exception:
        return False

    return bool(_VERBOS_COMANDO.match(t))

def _compor_atomo_base(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None,
    texto_tem_comando_explicito: Callable[[str], bool] | None,
    confirmacao_contextual_valida: bool,
) -> Dict[str, Any]:
    """
    R9a: produz contrato atômico SEM reentrar na composição.
    """
    def detector_local(valor: str) -> bool:
        return _detector_lexical_ancorado(
            valor,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )

    base = dict(
        _classificar_modalidade_base(
            texto,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=detector_local,
            confirmacao_contextual_valida=confirmacao_contextual_valida,
        )
        or {}
    )

    modal = str(base.get("modalidade") or "conversa")
    normalizado = str(
        base.get("normalizado")
        or _normalizar_operacional_ato(texto, normalizar_texto)
        or ""
    ).strip()

    segmento = {
        "indice": 0,
        "texto": normalizado[:300],
        "modalidade": modal,
        "confianca": float(base.get("confianca") or 0.0),
        "motivo": str(base.get("motivo") or ""),
        "autoriza_execucao": bool(base.get("autoriza_execucao")),
        "acao_explicita": bool(base.get("acao_explicita")),
        "requer_esclarecimento": bool(
            base.get("requer_esclarecimento")
        ),
        "depende_contexto": bool(base.get("depende_contexto")),
        "natureza_acao": str(base.get("natureza_acao") or "nenhuma"),
    }

    base.update(
        modalidade=modal,
        modalidade_geral=modal,
        ato_principal=modal,
        atos=[modal],
        segmentos=[segmento],
        texto_operacional=normalizado[:500] if modal == "comando" else "",
        texto_conversacional="" if modal == "comando" else normalizado[:500],
        origem_modalidade="atomico_base",
    )
    return base

def _aplicar_p0_atomico(
    texto: str,
    resultado: Dict[str, Any],
    *,
    normalizar_texto: Callable[[str], str] | None,
    texto_tem_comando_explicito: Callable[[str], bool] | None,
) -> Dict[str, Any]:
    """
    Mantém a proteção soberana, mas no nível do ato.
    """
    resultado = dict(resultado or {})
    # Esta é a única condição negativa hoje representada como contrato
    # operacional próprio. ``não estiver aberta`` descreve a observação que
    # habilita ``abre``; não revoga a ordem. A gramática estrita já rejeitou
    # perguntas, hipóteses pessoais e qualquer consequência diferente.
    if (
        resultado.get("autoriza_execucao") is True
        and str(resultado.get("modalidade") or "").casefold() == "comando"
        and _eh_politica_condicional_abertura_observavel(
            texto,
            normalizar_texto=normalizar_texto,
        )
    ):
        return resultado
    protecao = _protecao_p0_ato_fala(
        texto,
        normalizar_texto=normalizar_texto,
    )
    if protecao:
        normalizado = _normalizar_p0_ato_fala(texto, normalizar_texto)
        modalidade = str(protecao.get("modalidade") or "conversa")
        natureza = str(protecao.get("natureza_acao") or "nenhuma")
        motivo = str(
            protecao.get("motivo")
            or "ato de fala sem autorização"
        )
        requer = bool(protecao.get("requer_esclarecimento"))

        resultado.update(
            modalidade=modalidade,
            modalidade_geral=modalidade,
            ato_principal=modalidade,
            atos=[modalidade],
            segmentos=[{
                "indice": 0,
                "texto": normalizado[:300],
                "modalidade": modalidade,
                "confianca": 0.99,
                "motivo": motivo,
                "autoriza_execucao": False,
                "acao_explicita": False,
                "requer_esclarecimento": requer,
                "depende_contexto": modalidade == "recusa",
                "natureza_acao": natureza,
            }],
            texto_operacional="",
            texto_conversacional=normalizado[:500],
            acao_explicita=False,
            autoriza_execucao=False,
            requer_esclarecimento=requer,
            depende_contexto=(
                bool(resultado.get("depende_contexto"))
                or modalidade == "recusa"
            ),
            natureza_acao=natureza,
            motivo=motivo,
            motivo_decisao=motivo,
            confianca=max(
                float(resultado.get("confianca") or 0.0), 0.99
            ),
        )

        if natureza.casefold() in _NATUREZAS_VETO_MONOTONICO:
            return aplicar_veto_canonico(
                resultado,
                texto=texto,
                modalidade=modalidade,
                natureza=natureza,
                motivo=motivo,
                requer_esclarecimento=requer,
                origem_veto="p0_ato_fala_atomico",
            )
        return resultado

    detector_ancorado = _detector_lexical_ancorado(
        texto,
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    if (
        resultado.get("autoriza_execucao") is not True
        and str(resultado.get("modalidade") or "").casefold() == "recusa"
        and detector_ancorado
    ):
        return aplicar_veto_canonico(
            resultado,
            texto=texto,
            modalidade="recusa",
            natureza=str(
                resultado.get("natureza_acao") or "cancelamento"
            ),
            motivo=str(
                resultado.get("motivo") or "recusa operacional"
            ),
            requer_esclarecimento=bool(
                resultado.get("requer_esclarecimento")
            ),
            origem_veto="recusa_operacional_historica_atomica",
        )

    if resultado.get("autoriza_execucao") is True:
        negacao = analisar_negacao_interna_conservadora(texto)
        if negacao.get("bloqueia"):
            return aplicar_veto_canonico(
                resultado,
                texto=texto,
                modalidade="recusa",
                natureza="ambiguidade_polaridade_interna",
                motivo=(
                    "negação interna sem decomposição operacional segura; "
                    "execução não presumida"
                ),
                requer_esclarecimento=True,
                origem_veto="negacao_interna_stt_atomica",
            )

    return resultado

def _classificar_atomo_geral(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None,
    texto_tem_comando_explicito: Callable[[str], bool] | None,
    confirmacao_contextual_valida: bool,
) -> Dict[str, Any]:
    base = _compor_atomo_base(
        texto,
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
        confirmacao_contextual_valida=confirmacao_contextual_valida,
    )
    return _aplicar_p0_atomico(
        texto,
        base,
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )

def _contrato_musical_direto(
    texto_estrutural: str,
    cand: Any,
) -> Dict[str, Any]:
    classe = str(getattr(cand, "classe", "") or "")
    operacao = str(getattr(cand, "operacao", "") or "")
    regra = str(getattr(cand, "regra", "") or "")
    motivo = str(getattr(cand, "motivo", "") or regra)

    if classe == "pedido_direto":
        modalidade = "comando"
        auth = bool(getattr(cand, "evidencia_diretiva", False))
        acao = auth
        natureza = "pedido_direto"
    elif classe == "consulta_estado":
        modalidade = "pergunta"
        auth = False
        acao = False
        natureza = "consulta_estado"
    elif classe == "referencia_ambigua":
        modalidade = "conversa"
        auth = False
        acao = False
        natureza = "nenhuma"
    else:
        raise ValueError(
            f"classe musical não-owned no contrato direto: {classe!r}"
        )

    depende = bool(getattr(cand, "depende_contexto", False))
    return {
        "texto": texto_estrutural[:500],
        "normalizado": str(
            getattr(cand, "normalizado", "")
            or texto_estrutural
        )[:500],
        "modalidade": modalidade,
        "modalidade_geral": modalidade,
        "ato_principal": modalidade,
        "atos": [modalidade],
        "confianca": 0.99,
        "motivo": f"gramatica_musical:{regra}:{motivo}",
        "motivo_decisao": f"gramatica_musical:{regra}:{motivo}",
        "acao_explicita": acao,
        "autoriza_execucao": auth,
        "requer_esclarecimento": False,
        "depende_contexto": depende,
        "natureza_acao": natureza,
        "operacao_candidata": operacao,
        "somente_leitura": bool(
            getattr(cand, "somente_leitura", False)
        ),
        "segmentos": [{
            "indice": 0,
            "texto": texto_estrutural[:300],
            "modalidade": modalidade,
            "confianca": 0.99,
            "motivo": f"gramatica_musical:{regra}",
            "autoriza_execucao": auth,
            "acao_explicita": acao,
            "requer_esclarecimento": False,
            "depende_contexto": depende,
            "natureza_acao": natureza,
        }],
        "texto_operacional": (
            texto_estrutural[:500] if modalidade == "comando" else ""
        ),
        "texto_conversacional": (
            "" if modalidade == "comando" else texto_estrutural[:500]
        ),
        "origem_modalidade": "gramatica_musical_estrutural",
    }

def _fallback_musical_protegido(
    texto_estrutural: str,
    cand: Any,
    *,
    normalizar_texto: Callable[[str], str] | None,
) -> Dict[str, Any]:
    regra = str(getattr(cand, "regra", "") or "")
    t = str(texto_estrutural or "").strip().casefold()

    if regra == "negacao_inicial" or t.startswith(
        ("nao ", "não ", "nunca ", "jamais ", "nem ")
    ):
        modalidade = "recusa"
    elif regra == "pergunta" or t.endswith("?"):
        modalidade = "pergunta"
    else:
        modalidade = "conversa"

    natureza = "protegida"
    motivo = str(
        getattr(cand, "motivo", "")
        or "proteção musical fail-closed"
    )
    normalizado = _normalizar_operacional_ato(
        texto_estrutural, normalizar_texto
    )
    depende = modalidade == "recusa"

    return {
        "texto": texto_estrutural[:500],
        "normalizado": normalizado[:500],
        "modalidade": modalidade,
        "modalidade_geral": modalidade,
        "ato_principal": modalidade,
        "atos": [modalidade],
        "segmentos": [{
            "indice": 0,
            "texto": texto_estrutural[:300],
            "modalidade": modalidade,
            "confianca": 0.99,
            "motivo": motivo,
            "autoriza_execucao": False,
            "acao_explicita": False,
            "requer_esclarecimento": False,
            "depende_contexto": depende,
            "natureza_acao": natureza,
            "veto_execucao_operacional": True,
        }],
        "texto_operacional": "",
        "texto_conversacional": texto_estrutural[:500],
        "acao_explicita": False,
        "autoriza_execucao": False,
        "requer_esclarecimento": False,
        "depende_contexto": depende,
        "natureza_acao": natureza,
        "motivo": motivo,
        "motivo_decisao": motivo,
        "origem_modalidade": "gramatica_musical_guard",
        "veto_execucao_operacional": True,
        "origem_veto_execucao_operacional": "gramatica_musical_guard",
    }

def _classificar_ato_estrutural(
    texto_estrutural: str,
    *,
    normalizar_texto: Callable[[str], str] | None,
    texto_tem_comando_explicito: Callable[[str], bool] | None,
    confirmacao_contextual_valida: bool,
) -> Dict[str, Any]:
    """
    B/B2/C: ownership na representação estrutural.
    Relevância nunca vira autoridade.
    """
    cand = analisar_gramatica_musical(texto_estrutural)
    classe = str(getattr(cand, "classe", "") or "")

    if classe in _CLASSES_MUSICA_OWNED:
        return _contrato_musical_direto(
            texto_estrutural, cand
        )

    if classe == "protegida":
        protecao_real = dict(
            analisar_protecao_operacional(
                texto_estrutural,
                normalizar_texto=normalizar_texto,
            )
            or {}
        )
        protecao_p0 = dict(
            _protecao_p0_ato_fala(
                texto_estrutural,
                normalizar_texto=normalizar_texto,
            )
            or {}
        )
        if (
            bool(protecao_real.get("bloqueia_execucao"))
            or bool(protecao_p0)
        ):
            return _classificar_atomo_geral(
                texto_estrutural,
                normalizar_texto=normalizar_texto,
                texto_tem_comando_explicito=texto_tem_comando_explicito,
                confirmacao_contextual_valida=(
                    confirmacao_contextual_valida
                ),
            )

        if texto_tem_relevancia_musical(texto_estrutural):
            return _fallback_musical_protegido(
                texto_estrutural,
                cand,
                normalizar_texto=normalizar_texto,
            )

        # B2: guard especializado não sequestra outro domínio.
        return _classificar_atomo_geral(
            texto_estrutural,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
            confirmacao_contextual_valida=confirmacao_contextual_valida,
        )

    # classe=nenhuma, com ou sem relevância, delega ao owner geral.
    return _classificar_atomo_geral(
        texto_estrutural,
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
        confirmacao_contextual_valida=confirmacao_contextual_valida,
    )

def _limpar_ato_semantico(texto: str) -> str:
    """
    A3: remove apenas resíduos de boundary; preserva .?!
    que ainda pertencem ao ato.
    """
    return re.sub(r"\s+", " ", str(texto or "")).strip(" ,;")

def _evidencia_ato_operacional(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None,
) -> tuple[bool, str]:
    """
    A2: evidência de fronteira pela cláusula inteira, nunca por verbo interno.
    """
    t = _limpar_ato_semantico(texto)
    if not t:
        return False, "vazio"

    cand = analisar_gramatica_musical(t)
    if (
        str(getattr(cand, "classe", "") or "") == "pedido_direto"
        and bool(getattr(cand, "evidencia_diretiva", False))
    ):
        return True, "GRAMATICA_MUSICAL"

    base = dict(
        _classificar_modalidade_base(
            t,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=lambda _texto: False,
            confirmacao_contextual_valida=False,
        )
        or {}
    )
    if (
        str(base.get("modalidade") or "") == "comando"
        and bool(base.get("acao_explicita"))
    ):
        return True, "BASE_ANCORADA"

    return False, "BASE:" + str(
        base.get("modalidade") or "conversa"
    )


def _evidencia_pergunta_independente(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None,
) -> bool:
    """Reconhece uma pergunta como novo ato sem lhe conceder autoridade."""
    t = _limpar_ato_semantico(texto)
    if not t or "?" not in t:
        return False
    base = dict(
        _classificar_modalidade_base(
            t,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=lambda _texto: False,
            confirmacao_contextual_valida=False,
        )
        or {}
    )
    return str(base.get("modalidade") or "") == "pergunta"

def _separar_primeira_fronteira_forte(
    bloco: str,
    *,
    normalizar_texto: Callable[[str], str] | None,
):
    for m in re.finditer(
        r"(?P<sep>[,;.!])\s*(?P<conj>(?:mas|e|entao)\s+)?",
        bloco,
        flags=re.IGNORECASE,
    ):
        direita = _limpar_ato_semantico(bloco[m.end():])
        if not direita:
            continue

        inicia, origem = _evidencia_ato_operacional(
            direita,
            normalizar_texto=normalizar_texto,
        )
        if not inicia and _evidencia_pergunta_independente(
            direita,
            normalizar_texto=normalizar_texto,
        ):
            inicia, origem = True, "PERGUNTA_INDEPENDENTE"
        if not inicia:
            continue

        esquerda = _limpar_ato_semantico(
            bloco[:m.start()]
        )
        if esquerda:
            return m, esquerda, direita, origem

    return None

def _segmento_estrutural(
    texto_estrutural: str,
    resultado: Dict[str, Any],
    indice: int,
) -> Dict[str, Any]:
    return {
        "indice": indice,
        "texto": texto_estrutural[:300],
        "texto_estrutural": texto_estrutural[:300],
        "modalidade": str(
            resultado.get("ato_principal")
            or resultado.get("modalidade")
            or "conversa"
        ),
        "confianca": float(resultado.get("confianca") or 0.0),
        "motivo": str(
            resultado.get("motivo_decisao")
            or resultado.get("motivo")
            or ""
        ),
        "autoriza_execucao": bool(
            autoriza_execucao_efetiva(resultado)
        ),
        "acao_explicita": bool(resultado.get("acao_explicita")),
        "requer_esclarecimento": bool(
            resultado.get("requer_esclarecimento")
        ),
        "depende_contexto": bool(resultado.get("depende_contexto")),
        "natureza_acao": str(
            resultado.get("natureza_acao") or "nenhuma"
        ),
        "veto_execucao_operacional": bool(
            resultado.get("veto_execucao_operacional")
        ),
    }

def _fontes_autoridade_turno(turno: Dict[str, Any]) -> list[str]:
    leitura = dict(turno or {})
    fontes = []
    for s in list(leitura.get("segmentos") or []):
        if not isinstance(s, dict):
            continue
        modalidade = str(s.get("modalidade") or "")
        auth = bool(s.get("autoriza_execucao"))
        if modalidade == "comando" and auth:
            fontes.append("comando")
        elif (
            modalidade == "confirmacao"
            and auth
            and str(
                leitura.get("ato_principal")
                or leitura.get("modalidade")
                or ""
            ) == "confirmacao"
            and str(
                leitura.get("natureza_acao") or ""
            ) == "confirmacao_contextual"
            and bool(leitura.get("depende_contexto"))
            and bool(leitura.get("confirmacao_contextual_valida"))
        ):
            fontes.append("confirmacao_contextual")
    return fontes

def _segmentar_turno_misto(
    texto_estrutural: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
) -> list[str]:
    """
    A2+A3: boundary estrutural + pontuação semântica preservada.
    """
    t = re.sub(r"\s+", " ", str(texto_estrutural or "")).strip()
    if not t:
        return []

    # As duas cláusulas formam uma única política: a segunda não é um novo
    # comando independente, e a primeira contém o alvo da execução. Separá-las
    # faria o detector receber apenas ``abre; se já estiver...``.
    if _eh_politica_condicional_abertura_observavel(
        t,
        normalizar_texto=normalizar_texto,
    ):
        return [t]

    segmentos = [t]

    for _ in range(8):
        mudou = False
        novos = []

        for bloco in segmentos:
            corte = _separar_primeira_fronteira_forte(
                bloco,
                normalizar_texto=normalizar_texto,
            )
            if corte is None:
                limpo = _limpar_ato_semantico(bloco)
                if limpo:
                    novos.append(limpo)
                continue

            _m, esquerda, direita, _origem = corte
            novos.extend([esquerda, direita])
            mudou = True

        segmentos = [s for s in novos if s]
        if not mudou:
            break

    finais = []
    for bloco in segmentos:
        atual = bloco

        while True:
            corte = None
            for m in re.finditer(
                r"\s+(?P<conj>e|mas|entao)\s+",
                atual,
                flags=re.IGNORECASE,
            ):
                esquerda = _limpar_ato_semantico(
                    atual[:m.start()]
                )
                direita = _limpar_ato_semantico(
                    atual[m.end():]
                )
                if not esquerda or not direita:
                    continue

                esq_ok, _ = _evidencia_ato_operacional(
                    esquerda,
                    normalizar_texto=normalizar_texto,
                )
                dir_ok, _ = _evidencia_ato_operacional(
                    direita,
                    normalizar_texto=normalizar_texto,
                )
                direita_pergunta = _evidencia_pergunta_independente(
                    direita,
                    normalizar_texto=normalizar_texto,
                )
                if (esq_ok and dir_ok) or direita_pergunta:
                    corte = (esquerda, direita)
                    break

            if corte is None:
                limpo = _limpar_ato_semantico(atual)
                if limpo:
                    finais.append(limpo)
                break

            esquerda, direita = corte
            finais.append(esquerda)
            atual = direita

    return [s for s in finais if s]



def _classificar_modalidade_turno_composta_base(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
    texto_tem_comando_explicito: Callable[[str], bool] | None = None,
    confirmacao_contextual_valida: bool = False,
) -> Dict[str, Any]:
    """
    C REV2: fronteira e ownership antes da normalização operacional.
    """
    bruto = str(texto or "").strip()
    # A coerência das aspas é uma propriedade do turno inteiro. Verificá-la
    # somente depois da segmentação permite que um primeiro literal válido e
    # uma aspa órfã em outro ato pareçam seguros quando observados isoladamente.
    # Em entrada operacional malformada, falhamos fechados antes de qualquer
    # decomposição ou fonte positiva de autoridade.
    normalizado_p0 = _normalizar_p0_ato_fala(bruto, normalizar_texto)
    if (
        bruto
        and not aspas_globalmente_coerentes(bruto)
        and bool(_P0_GATILHOS_OPERACIONAIS.search(normalizado_p0))
    ):
        return aplicar_veto_canonico(
            {},
            texto=bruto,
            modalidade="recusa",
            natureza="entrada_operacional_malformada",
            motivo=(
                "aspas incoerentes em entrada operacional; execução não "
                "presumida"
            ),
            requer_esclarecimento=True,
            origem_veto="aspas_globais_operacionais",
        )
    # O retrato estrutural precisa conservar a grafia do usuário; remover
    # acentos aqui corrompe o texto que será entregue à conversa e aos
    # especialistas. Corrigimos somente deslizes operacionais auditáveis.
    estrutural, _correcoes_estruturais = corrigir_erros_portugues_operacionais(
        bruto.casefold()
    )
    estrutural = re.sub(r"\s+", " ", str(estrutural or "")).strip()

    segmentos_texto = _segmentar_turno_misto(
        estrutural,
        normalizar_texto=normalizar_texto,
    )

    segmentos = []
    resultados = []
    for indice, trecho in enumerate(segmentos_texto):
        res = _classificar_ato_estrutural(
            trecho,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
            confirmacao_contextual_valida=(
                confirmacao_contextual_valida
            ),
        )
        resultados.append(res)
        segmentos.append(
            _segmento_estrutural(trecho, res, indice)
        )

    normalizado_operacional = _normalizar_operacional_ato(
        bruto, normalizar_texto
    )

    if not segmentos:
        return {
            "id": time.time_ns(),
            "texto": bruto[:500],
            "normalizado": normalizado_operacional[:500],
            "modalidade": "vazio",
            "modalidade_geral": "vazio",
            "ato_principal": "vazio",
            "atos": [],
            "segmentos": [],
            "texto_operacional": "",
            "texto_conversacional": "",
            "acao_explicita": False,
            "autoriza_execucao": False,
            "requer_esclarecimento": False,
            "depende_contexto": False,
            "natureza_acao": "nenhuma",
            "confirmacao_contextual_valida": bool(
                confirmacao_contextual_valida
            ),
            "confianca": 1.0,
            "motivo": "entrada vazia",
            "motivo_decisao": "entrada vazia",
            "ts": time.time(),
        }

    modalidades = {
        str(s.get("modalidade") or "")
        for s in segmentos
        if str(s.get("modalidade") or "") != "vazio"
    }
    comandos = [
        s for s in segmentos
        if str(s.get("modalidade") or "") == "comando"
    ]

    prioridade = (
        "correcao", "comando", "pergunta", "confirmacao",
        "recusa", "deliberacao", "reacao", "conversa",
    )
    ato = next(
        (m for m in prioridade if m in modalidades),
        str(segmentos[0].get("modalidade") or "conversa"),
    )
    if comandos:
        ato = "comando"

    geral = (
        "misto"
        if len(segmentos) > 1 and len(modalidades) > 1
        else ato
    )

    auth = any(
        bool(s.get("autoriza_execucao")) for s in comandos
    )
    if ato == "confirmacao":
        auth = bool(confirmacao_contextual_valida)

    # H3: o veto sticky existe por ato/segmento. Ele sobe ao contrato do
    # turno apenas quando NÃO existe outra fonte independente de autoridade.
    # Como segmentos vetados usam autoriza_execucao_efetiva, um auth=True
    # agregado necessariamente veio de outro segmento não vetado.
    veto_execucao_operacional = (
        any(
            bool(s.get("veto_execucao_operacional"))
            for s in segmentos
        )
        and not auth
    )

    principal_seg = comandos[0] if comandos else segmentos[0]
    principal_res = None
    for seg, res in zip(segmentos, resultados):
        if seg is principal_seg:
            principal_res = res
            break
    if principal_res is None:
        principal_res = resultados[0]

    return {
        "id": time.time_ns(),
        "texto": bruto[:500],
        "normalizado": normalizado_operacional[:500],
        "normalizado_estrutural": estrutural[:500],
        "modalidade": ato,
        "modalidade_geral": geral,
        "ato_principal": ato,
        "atos": [str(s.get("modalidade") or "") for s in segmentos],
        "segmentos": segmentos,
        "texto_operacional": " ".join(
            str(s.get("texto") or "")
            for s in comandos
        ).strip()[:500],
        "texto_conversacional": " ".join(
            str(s.get("texto") or "")
            for s in segmentos
            if str(s.get("modalidade") or "") != "comando"
        ).strip()[:500],
        "acao_explicita": any(
            bool(s.get("acao_explicita")) for s in segmentos
        ),
        "autoriza_execucao": auth,
        "veto_execucao_operacional": bool(
            veto_execucao_operacional
        ),
        "requer_esclarecimento": any(
            bool(s.get("requer_esclarecimento"))
            for s in segmentos
        ),
        "depende_contexto": (
            any(bool(s.get("depende_contexto")) for s in segmentos)
            or ato in {"confirmacao", "recusa"}
        ),
        "natureza_acao": str(
            principal_seg.get("natureza_acao") or "nenhuma"
        ),
        "confirmacao_contextual_valida": bool(
            confirmacao_contextual_valida
        ),
        "confianca": max(
            float(r.get("confianca") or 0.0) for r in resultados
        ),
        "motivo": (
            "turno com múltiplos atos compatíveis"
            if geral == "misto"
            else str(
                principal_res.get("motivo_decisao")
                or principal_res.get("motivo")
                or ""
            )
        ),
        "motivo_decisao": str(
            principal_res.get("motivo_decisao")
            or principal_res.get("motivo")
            or ""
        ),
        "ts": time.time(),
    }

# P0_AUTORIZACAO_MODALIDADE_20260814
# A classificação composta histórica continua como fonte de contexto, mas o
# ato de fala INTEIRO ganha a palavra final sobre autorização. Assim uma
# citação/pergunta não recupera permissão por causa da segmentação interna.
_P0_GATILHOS_OPERACIONAIS = re.compile(
    r"\b(?:"
    r"abre|abrir|abra|abriria|"
    r"fecha|fechar|feche|fecharia|"
    r"liga|ligar|ligue|ligaria|"
    r"desliga|desligar|desligue|desligaria|"
    r"toca|tocar|toque|tocaria|"
    r"coloca|colocar|coloque|colocaria|"
    r"cria|criar|crie|criaria|"
    r"apaga|apagar|apague|apagaria|"
    r"remove|remover|remova|removeria|"
    r"deleta|deletar|delete|deletaria|"
    r"move|mover|mova|moveria|"
    r"renomeia|renomear|renomeie|renomearia|"
    r"maximiza|maximizar|maximize|maximizaria|"
    r"minimiza|minimizar|minimize|minimizaria|"
    r"pausa|pausar|pause|pausaria|"
    r"retoma|retomar|continue|continua|continuar|"
    r"organiza|organizar|organize|organizaria|"
    r"pesquisa|pesquisar|pesquise|"
    r"busca|buscar|busque|procura|procurar|procure|"
    r"encontra|encontrar|encontre|"
    r"escreve|escrever|escreva|escreveria|"
    r"grava|gravar|grave|gravaria|"
    r"adiciona|adicionar|adicione|adicionaria|"
    r"acrescenta|acrescentar|acrescente|acrescentaria|"
    r"restaura|restaurar|restaure|restauraria|"
    r"recupera|recuperar|recupere|recuperaria|"
    r"executa|executar|execute|executaria|"
    r"repete|repetir|repita|refaz|refazer|refaca|"
    r"tenta|tentar|tente"
    r")\b",
    re.IGNORECASE,
)


def _normalizar_p0_ato_fala(
    texto: str,
    normalizar_texto: Callable[[str], str] | None = None,
) -> str:
    normalizar = normalizar_texto if callable(normalizar_texto) else (
        lambda valor: str(valor or "").casefold().strip()
    )
    bruto = str(normalizar(texto) or "").casefold()
    base = unicodedata.normalize("NFKD", bruto)
    sem_acentos = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", sem_acentos).strip()



# P0_AUTORIZACAO_ATO_FALA_V2_20260815
# Um gatilho lexical prova apenas que uma acao foi mencionada. Ele NAO prova
# que o usuario autorizou a Laylay a executa-la.
_P0_VERBOS_PEDIDO_DIRETO = (
    r"(?:"
    r"abre|abra|fecha|feche|liga|ligue|desliga|desligue|"
    r"toca|toque|coloca|coloque|bota|poe|cria|crie|"
    r"apaga|apague|remove|remova|deleta|delete|move|mova|"
    r"renomeia|renomeie|maximiza|maximize|minimiza|minimize|"
    r"pausa|pause|retoma|continue|continua|organiza|organize|"
    r"pesquisa|pesquise|busca|busque|procura|procure|"
    r"encontra|encontre|escreve|escreva|grava|grave|"
    r"adiciona|adicione|acrescenta|acrescente|"
    r"restaura|restaure|recupera|recupere|"
    r"executa|execute|repete|repita|refaz|refaca|tenta|tente"
    r")"
)

_P0_VERBOS_INFINITIVO_OPERACIONAL = (
    r"(?:"
    r"abrir|fechar|ligar|desligar|tocar|colocar|criar|apagar|"
    r"remover|deletar|mover|renomear|maximizar|minimizar|"
    r"pausar|retomar|continuar|organizar|pesquisar|buscar|"
    r"procurar|encontrar|escrever|gravar|adicionar|acrescentar|"
    r"restaurar|recuperar|"
    r"executar|repetir|refazer|tentar"
    r")"
)

_P0_PEDIDO_DIRETO_INICIAL = re.compile(
    rf"^(?:por\s+favor\s+)?{_P0_VERBOS_PEDIDO_DIRETO}\b",
    re.IGNORECASE,
)
_P0_PEDIDO_POLIDO_SEM_SUJEITO = re.compile(
    rf"^(?:por\s+favor\s+)?"
    rf"(?:pode|poderia|consegue|conseguiria)\s+(?:me\s+)?"
    rf"(?:{_P0_VERBOS_INFINITIVO_OPERACIONAL}|{_P0_VERBOS_PEDIDO_DIRETO})\b",
    re.IGNORECASE,
)
_P0_PRIMEIRA_PESSOA_NAO_AUTORIZA = re.compile(
    rf"^(?:"
    rf"eu\s+(?:posso|poderia|devo|deveria|consigo|conseguiria|iria|"
    rf"tentaria|pretendo|vou)|"
    rf"(?:posso|devo|deveria|consigo|iria|tentaria|pretendo|vou)"
    rf")\s+{_P0_VERBOS_INFINITIVO_OPERACIONAL}\b",
    re.IGNORECASE,
)
_P0_HIPOTESE_PRIMEIRA_PESSOA = re.compile(
    rf"^(?:e\s+)?(?:se|caso)\s+eu\s+"
    rf"(?:quisesse|quiser|tentasse|decidisse|pensasse|pretendesse|fosse)\b"
    rf".*\b(?:{_P0_VERBOS_INFINITIVO_OPERACIONAL}|{_P0_VERBOS_PEDIDO_DIRETO})\b",
    re.IGNORECASE,
)
_P0_NEGACAO_OPERACIONAL_INTERNA = re.compile(
    rf"(?:^|[,;]\s*|\b(?:mas|e)\s+)"
    rf"(?:nao|nunca|jamais)\s+"
    rf"(?:(?:pode|deve|vai)\s+)?(?:me\s+)?"
    rf"(?:{_P0_VERBOS_PEDIDO_DIRETO}|{_P0_VERBOS_INFINITIVO_OPERACIONAL})\b",
    re.IGNORECASE,
)


def _p0_pergunta_operacional_tem_pedido_explicito(texto_normalizado: str) -> bool:
    """Distingue pergunta-pedido de pergunta SOBRE uma acao."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return False
    if _P0_PEDIDO_DIRETO_INICIAL.search(t):
        return True
    if _P0_PEDIDO_POLIDO_SEM_SUJEITO.search(t):
        return True
    if (
        re.match(
            r"^(?:voce|tu)\s+(?:pode|poderia|consegue|conseguiria)\b",
            t, flags=re.IGNORECASE,
        )
        and re.search(r"\b(?:pra|para)\s+mim\b", t, flags=re.IGNORECASE)
        and _P0_GATILHOS_OPERACIONAIS.search(t)
    ):
        return True
    return False


_NEGACAO_INTERNA_CONSERVADORA = re.compile(
    r"(?<![\wÀ-ÿ])(?P<neg>nao|não|nunca|jamais)(?![\wÀ-ÿ])",
    re.IGNORECASE,
)

_NATUREZAS_VETO_MONOTONICO = frozenset({
    "cancelamento",
    "capacidade",
    "hipotetica",
    "mencao_operacional",
    "instrucao_ou_explicacao",
    "decepcao",
})


def turno_tem_veto_execucao(turno: Dict[str, Any] | None) -> bool:
    """Consulta o receipt soberano que nenhuma camada posterior pode revogar."""
    return bool(dict(turno or {}).get("veto_execucao_operacional"))


def autoriza_execucao_efetiva(turno: Dict[str, Any] | None) -> bool:
    """Autoridade efetiva exige autorização positiva e ausência de veto sticky."""
    leitura = dict(turno or {})
    return bool(leitura.get("autoriza_execucao") and not turno_tem_veto_execucao(leitura))


def analisar_negacao_interna_conservadora(texto: str) -> Dict[str, Any]:
    """Falha fechada para negação interna, salvo filename literal comprovado."""
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    marcadores: list[Dict[str, Any]] = []
    for encontrado in _NEGACAO_INTERNA_CONSERVADORA.finditer(bruto):
        inicio, fim = encontrado.span("neg")
        prefixo = bruto[:inicio].strip()
        atomo, valor = marcador_negacao_em_filename_literal(bruto, inicio, fim)
        marcadores.append({
            "marcador": encontrado.group("neg"),
            "inicio": inicio,
            "fim": fim,
            "prefixo": prefixo,
            "cauda": bruto[fim:].strip(),
            "interno": bool(prefixo),
            "atomo_arquivo": bool(atomo),
            "atomo_valor": valor,
        })
    bloqueantes = [
        item for item in marcadores
        if item["interno"] and not item["atomo_arquivo"]
    ]
    return {
        "texto": bruto,
        "marcadores": marcadores,
        "bloqueia": bool(bloqueantes),
        "primeiro": dict(bloqueantes[0]) if bloqueantes else {},
        "atomos_liberados": [
            dict(item) for item in marcadores if item["atomo_arquivo"]
        ],
    }


def aplicar_veto_canonico(
    turno: Dict[str, Any] | None,
    *,
    texto: str,
    modalidade: str,
    natureza: str,
    motivo: str,
    requer_esclarecimento: bool,
    origem_veto: str,
) -> Dict[str, Any]:
    """Reescreve todo o contrato e elimina qualquer autorização stale."""
    novo = dict(turno or {})
    modal = str(modalidade or "recusa").strip().casefold() or "recusa"
    normalizado = re.sub(r"\s+", " ", str(texto or "")).strip()
    confianca = max(0.99, float(novo.get("confianca") or 0.0))
    segmento = {
        "indice": 0,
        "texto": normalizado[:300],
        "modalidade": modal,
        "confianca": confianca,
        "motivo": str(motivo or "veto operacional soberano"),
        "autoriza_execucao": False,
        "acao_explicita": False,
        "requer_esclarecimento": bool(requer_esclarecimento),
        "natureza_acao": str(natureza or "nenhuma"),
        "veto_execucao_operacional": True,
    }
    novo.update(
        modalidade=modal,
        modalidade_geral=modal,
        ato_principal=modal,
        atos=[modal],
        segmentos=[segmento],
        texto_operacional="",
        texto_conversacional=normalizado[:500],
        acao_explicita=False,
        autoriza_execucao=False,
        requer_esclarecimento=bool(requer_esclarecimento),
        natureza_acao=str(natureza or "nenhuma"),
        motivo=str(motivo or "veto operacional soberano"),
        motivo_decisao=str(motivo or "veto operacional soberano"),
        veto_execucao_operacional=True,
        origem_veto_execucao_operacional=str(origem_veto or "protecao_operacional"),
        motivo_veto_execucao_operacional=str(motivo or "veto operacional soberano"),
        confianca=confianca,
    )
    return novo


def _protecao_p0_ato_fala(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
) -> Dict[str, Any] | None:
    """Lê quando a frase fala SOBRE uma ação sem autorizá-la."""
    t = _normalizar_p0_ato_fala(texto, normalizar_texto)
    if not t:
        return None

    existente = analisar_protecao_operacional(
        t,
        normalizar_texto=lambda valor: _normalizar_p0_ato_fala(valor),
    )
    if bool(existente.get("bloqueia_execucao")):
        return {
            "modalidade": str(existente.get("modalidade") or "conversa"),
            "natureza_acao": str(existente.get("natureza_acao") or "nenhuma"),
            "motivo": str(existente.get("motivo") or "proteção operacional"),
            "requer_esclarecimento": (
                str(existente.get("natureza_acao") or "") == "capacidade"
            ),
        }

    tem_gatilho = bool(_P0_GATILHOS_OPERACIONAIS.search(t))
    if not tem_gatilho:
        return None

    # Primeira pessoa descreve possibilidade, conselho ou hipotese; isso nao
    # autoriza a Laylay a agir por conta propria.
    if (
        _P0_PRIMEIRA_PESSOA_NAO_AUTORIZA.search(t)
        or _P0_HIPOTESE_PRIMEIRA_PESSOA.search(t)
    ):
        return {
            "modalidade": "pergunta" if "?" in str(texto or "") else "deliberacao",
            "natureza_acao": "hipotetica",
            "motivo": "possibilidade ou hipotese sobre acao; nao e pedido",
            "requer_esclarecimento": False,
        }

    # Interrogacao + verbo operacional nao basta. So liberamos quando a
    # propria moldura e um pedido reconhecivel.
    if (
        "?" in str(texto or "")
        and not _p0_pergunta_operacional_tem_pedido_explicito(t)
    ):
        return {
            "modalidade": "pergunta",
            "natureza_acao": "informativa_sobre_acao",
            "motivo": "pergunta sobre acao sem pedido explicito",
            "requer_esclarecimento": False,
        }

    # Metalinguagem/citação: o verbo é conteúdo da frase, não uma ordem.
    if (
        re.search(
            r"^(?:(?:eu\s+)?(?:estou|to)\s+)?(?:so\s+|apenas\s+|somente\s+)?"
            r"(?:estou\s+)?(?:escrevendo|digitando|citando|mencionando|"
            r"falando\s+a\s+frase|dizendo)\b",
            t,
        )
        or re.search(r"^(?:a\s+)?(?:palavra|frase|expressao|texto|termo)\b", t)
        # P0_METALINGUAGEM_IGNORE_20260814
        # "ignore/desconsidere a palavra X" fala SOBRE o token X; o verbo
        # citado depois não ganha autorização operacional.
        or re.search(
            r"^(?:por\s+favor\s+)?"
            r"(?:ignore|ignora|ignorar|desconsidere|desconsidera|desconsiderar)\s+"
            r"(?:a\s+|o\s+)?(?:palavra|frase|expressao|texto|termo)\b",
            t,
        )
        or re.search(r"\bnao\s+(?:e|eh)\s+(?:um\s+)?(?:pedido|comando|ordem)\b", t)
        or re.search(
            r"\b(?:so|apenas|somente)\s+(?:um\s+)?"
            r"(?:exemplo|teste|texto|citacao|mencao)\b",
            t,
        )
        or re.search(
            r"^(?:quando|se)\s+eu\s+(?:digo|disser|escrevo|escrever|falo|falar)\b",
            t,
        )
    ):
        return {
            "modalidade": "conversa",
            "natureza_acao": "mencao_operacional",
            "motivo": "menção/citação de comando sem autorização",
            "requer_esclarecimento": False,
        }

    # Explicação/instrução sobre COMO fazer algo.
    if (
        re.search(
            r"^(?:(?:so|apenas|somente)\s+)?" r"(?:(?:me|pra\s+mim|para\s+mim)\s+)?"
            r"(?:explica|explique|ensina|ensine|mostra|mostre)\s+como\b",
            t,
        )
        or re.search(
            r"^(?:eu\s+)?(?:quero|queria|gostaria)\s+(?:de\s+)?saber\s+como\b",
            t,
        )
    ):
        return {
            "modalidade": "pergunta",
            "natureza_acao": "instrucao_ou_explicacao",
            "motivo": "pedido de explicação sobre ação; não é execução",
            "requer_esclarecimento": False,
        }

    # Ate existir representacao propria para condicionais/mistos, uma clausula
    # operacional negada torna o turno fail-closed. Evita transformar
    # "A, mas nao B" em uma ordem positiva contaminada.
    if _P0_NEGACAO_OPERACIONAL_INTERNA.search(t):
        return {
            "modalidade": "recusa",
            "natureza_acao": "cancelamento",
            "motivo": "negacao operacional interna; execucao nao presumida",
            "requer_esclarecimento": False,
        }

    # Perguntas informativas que começam pelo infinitivo da ação. Antes da P0
    # elas venciam a pergunta genérica e podiam ser classificadas como ordem.
    if "?" in str(texto or "") and (
        re.search(
            r"^(?:abrir|fechar|ligar|desligar|tocar|colocar|criar|apagar|"
            r"remover|deletar|mover|renomear|maximizar|minimizar|pausar|"
            r"organizar|executar)\b.*\b(?:e|eh)\s+"
            r"(?:(?:uma|a)\s+)?(?:boa|ma)\s+ideia\b",
            t,
        )
        or re.search(
            r"^(?:abrir|fechar|ligar|desligar|tocar|colocar|criar|apagar|"
            r"remover|deletar|mover|renomear|maximizar|minimizar|pausar|"
            r"organizar|executar)\b.*\b"
            r"(?:muda|altera|afeta|causa|serve|significa|acontece|funciona|"
            r"pode\s+causar|vai\s+causar)\b",
            t,
        )
    ):
        return {
            "modalidade": "pergunta",
            "natureza_acao": "informativa_sobre_acao",
            "motivo": "pergunta informativa sobre uma ação; não é pedido",
            "requer_esclarecimento": False,
        }

    return None


def classificar_modalidade_turno(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
    texto_tem_comando_explicito: Callable[[str], bool] | None = None,
    confirmacao_contextual_valida: bool = False,
) -> Dict[str, Any]:
    """
    API pública preservada. P0 já foi aplicado por ato.
    """
    return _classificar_modalidade_turno_composta_base(
        texto,
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
        confirmacao_contextual_valida=confirmacao_contextual_valida,
    )



def bloqueia_execucao_operacional_prioritaria(
    texto: str,
    *,
    classificacao: Dict[str, Any] | None = None,
    normalizar_texto: Callable[[str], str] | None = None,
    texto_tem_comando_explicito: Callable[[str], bool] | None = None,
    confirmacao_contextual_valida: bool = False,
) -> bool:
    """
    Barreira continua fail-closed, mas não reaplica P0 global sobre um
    contrato composto que já provou autoridade por ato.
    """
    analise = dict(classificacao or {})
    if not analise:
        analise = classificar_modalidade_turno(
            texto,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
            confirmacao_contextual_valida=confirmacao_contextual_valida,
        )

    if turno_tem_veto_execucao(analise):
        return True

    if (
        autoriza_execucao_efetiva(analise)
        and _fontes_autoridade_turno(analise)
    ):
        return False

    # Sem fonte legítima, preservamos o comportamento conservador histórico.
    if analisar_negacao_interna_conservadora(texto).get("bloqueia"):
        return True
    if _protecao_p0_ato_fala(
        texto,
        normalizar_texto=normalizar_texto,
    ):
        return True

    natureza = str(analise.get("natureza_acao") or "").casefold()
    if natureza in {
        "capacidade",
        "instrucao_ou_explicacao",
        "informativa_sobre_acao",
        "hipotetica",
        "cancelamento",
        "mencao_operacional",
        "decepcao",
        "protegida",
    }:
        return True

    if texto_pede_aba_anterior(texto, permitir_cadeia=True):
        return True

    normalizado = _normalizar_p0_ato_fala(
        texto, normalizar_texto
    )
    return bool(_P0_GATILHOS_OPERACIONAIS.search(normalizado))
