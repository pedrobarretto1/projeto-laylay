"""Detecção e resposta local para conversas sobre capacidades da Laylay.

Este módulo não executa ações. Ele separa propostas, planos e comentários
sobre habilidades futuras de comandos que devem ser executados agora.
"""

from __future__ import annotations

import re

from .normalizacao_linguagem import normalizar_texto_basico as _normalizar


def texto_discute_capacidade_futura(texto: str) -> bool:
    """Indica conversa meta/futura, sem confundir com um comando presente."""
    t = _normalizar(texto)
    if not t:
        return False

    marcadores_capacidade = (
        "habilidade", "capacidade", "funcao", "funcionalidade", "recurso",
        "integracao", "automacao", "modo", "poder controlar", "conseguir controlar",
        "poder abrir", "conseguir abrir", "poder fazer", "conseguir fazer",
    )
    marcadores_futuro = (
        "vou te dar", "vou adicionar", "vou colocar", "vou implementar",
        "quero te dar", "quero adicionar", "quero criar", "pretendo adicionar",
        "estou pensando em", "to pensando em", "pensei em adicionar",
        "voce vai poder", "voce podera", "voce vai conseguir",
        "quando voce puder", "no futuro", "nova habilidade", "nova capacidade",
        "essa habilidade", "essa capacidade", "essa funcao", "esse recurso",
    )
    pede_opiniao_meta = any(p in t for p in (
        "o que acha dessa", "o que voce acha dessa", "acha legal",
        "seria legal", "isso seria util", "gostou da ideia",
    ))
    tem_capacidade = any(p in t for p in marcadores_capacidade)
    tem_futuro = any(p in t for p in marcadores_futuro)
    return bool((tem_capacidade and tem_futuro) or (pede_opiniao_meta and tem_capacidade))


def resposta_conversa_sobre_capacidade(texto: str) -> str:
    """Produz uma reação contextual curta, sem prometer que a ação já existe."""
    if not texto_discute_capacidade_futura(texto):
        return ""
    t = _normalizar(texto)

    correcao_indisponivel = any(p in t for p in (
        "voce nao tem", "ainda nao tem", "nao tem essa", "nao possui",
        "ainda nao possui", "ja falei", "nao consegue ainda", "nao pode ainda",
    ))
    if correcao_indisponivel:
        return (
            "Você tem razão. Eu ainda não tenho essa capacidade e vou tratá-la como "
            "indisponível até você implementar e confirmar que está funcionando."
        )

    if any(p in t for p in ("depende de voce", "depende de você")):
        return (
            "Sim. Essa capacidade depende de você implementar e conectar tudo. "
            "Até lá, eu não vou dizer que consigo usá-la nem oferecer essa ação."
        )

    if any(p in t for p in ("luz", "lampada", "iluminacao")):
        detalhe = "controlar a iluminação"
        extensao = "Depois dá até para criar cenas e rotinas por horário."
    elif any(p in t for p in ("iot", "casa", "tomada", "ventilador", "dispositivo")):
        detalhe = "controlar os dispositivos da casa"
        extensao = "Eu começaria com comandos explícitos e confirmação para evitar acionamentos acidentais."
    elif any(p in t for p in ("musica", "playlist", "spotify", "youtube")):
        detalhe = "entender e controlar melhor a música"
        extensao = "O mais importante seria preservar o estilo pedido e confirmar antes de tocar."
    elif any(p in t for p in ("navegador", "chrome", "site", "aba")):
        detalhe = "trabalhar melhor com o navegador"
        extensao = "Dá para começar com leitura de contexto e deixar ações destrutivas sempre sob confirmação."
    else:
        detalhe = "ganhar essa capacidade nova"
        extensao = "Eu só separaria bem conversa, sugestão e execução para não agir antes da hora."

    if any(p in t for p in ("legal", "o que acha", "gostou", "util")):
        inicio = f"Acho uma ideia bem legal. {detalhe.capitalize()} deixaria nossa interação bem mais natural."
    else:
        inicio = f"Gostei da direção. {detalhe.capitalize()} pode ser uma habilidade bem útil."
    return f"{inicio} {extensao}"


def extrair_registro_capacidade_futura(texto: str) -> dict:
    """Cria um registro curto para continuações como 'ela' e 'isso'."""
    if not texto_discute_capacidade_futura(texto):
        return {}
    t = _normalizar(texto)
    if any(p in t for p in ("luz", "lampada", "iluminacao")):
        alvo = "controlar a luz"
    elif any(p in t for p in ("iot", "tomada", "ventilador", "dispositivo", "casa")):
        alvo = "controlar dispositivos IoT"
    elif any(p in t for p in ("musica", "playlist", "spotify", "youtube")):
        alvo = "controlar música"
    elif any(p in t for p in ("navegador", "chrome", "site", "aba")):
        alvo = "trabalhar com o navegador"
    else:
        alvo = "a capacidade mencionada"
    return {
        "alvo": alvo,
        "status": "indisponivel",
        "confirmada_disponivel": False,
        "evidencia": str(texto or "").strip()[:240],
    }


def texto_continua_capacidade_futura(texto: str) -> bool:
    """Reconhece continuação curta quando já existe um registro na memória."""
    t = _normalizar(texto)
    if not t or len(t.split()) > 14:
        return False
    return any(p in t for p in (
        "isso depende", "depende de voce", "depende de você", "nao tem ela",
        "não tem ela", "nao tem isso", "não tem isso", "ainda nao tem",
        "ainda não tem", "essa habilidade", "essa capacidade", "ela ainda",
        "isso ainda", "quando tiver", "quando voce tiver", "quando você tiver",
    ))


def resposta_continuacao_capacidade_futura(texto: str, registro: dict | None) -> str:
    registro = dict(registro or {})
    if not registro or not texto_continua_capacidade_futura(texto):
        return ""
    t = _normalizar(texto)
    alvo = str(registro.get("alvo") or "essa capacidade").strip()
    if any(p in t for p in ("nao tem", "ainda nao", "ela ainda", "isso ainda")):
        return (
            f"Você tem razão: eu ainda não consigo {alvo}. "
            "Vou manter isso como indisponível até você confirmar a implementação."
        )
    return (
        f"Sim. Conseguir {alvo} depende de você implementar e conectar essa habilidade. "
        "Até lá, eu não vou agir como se ela já existisse."
    )
