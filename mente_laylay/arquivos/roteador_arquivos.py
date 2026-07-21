"""Roteamento de comandos de arquivos da Laylay."""

from __future__ import annotations

import re
from typing import Any, Callable, Mapping

from mente_laylay.arquivos.lixeira_laylay import existe_exclusao_pendente


def _get(ctx: Mapping[str, Any], key: str):
    return ctx.get(key)


def extrair_criacao_pasta_arquivo(frase: str) -> dict:
    """Extrai pasta, arquivo e conteudo de pedidos naturais de criacao."""
    texto_local = re.sub(r"\s+", " ", str(frase or "").strip())
    if not texto_local:
        return {}

    combo_escreve = re.search(
        r"\b(?:cria|criar|crie)\b.*?\bpasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<pasta>.+?)\s+"
        r"(?:e\s+)?dentro(?:\s+del[ae]|\s+dess[ae]|\s+da\s+pasta|\s+do\s+diretorio|\s+do\s+diretório)?\s+"
        r"(?:um\s+|uma\s+)?arquivo(?:\s+de\s+te(?:x|s)to)?\s+"
        r"(?:chamado|chamada|chamadda|com nome)?\s*(?P<arquivo>.+?)\s+"
        r"escreve\s+(?P<conteudo>.+)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if combo_escreve:
        pasta = str(combo_escreve.group("pasta") or "").strip(" .,!?:;\"'")
        arquivo = str(combo_escreve.group("arquivo") or "").strip(" .,!?:;\"'")
        conteudo = str(combo_escreve.group("conteudo") or "").strip(" .,!?:;\"'")
        if pasta and arquivo:
            return {"nome": pasta, "arquivo_nome": arquivo, "arquivo_conteudo": conteudo}

    combo_escrito = re.search(
        r"\b(?:cria|criar|crie)\b.*?\bpasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<pasta>.+?)\s+"
        r"(?:e\s+)?dentro(?:\s+del[ae]|\s+dess[ae]|\s+da\s+pasta)?\s+"
        r"(?:um\s+|uma\s+)?arquivo(?:\s+de\s+te(?:x|s)to)?\s+"
        r"(?:chamado|chamada|chamadda|com nome)?\s*(?P<arquivo>.+?)\s+"
        r"escrito(?:\s+nele)?\s+(?P<conteudo>.+)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if combo_escrito:
        pasta = str(combo_escrito.group("pasta") or "").strip(" .,!?:;\"'")
        arquivo = str(combo_escrito.group("arquivo") or "").strip(" .,!?:;\"'")
        conteudo = str(combo_escrito.group("conteudo") or "").strip(" .,!?:;\"'")
        if pasta and arquivo:
            return {"nome": pasta, "arquivo_nome": arquivo, "arquivo_conteudo": conteudo}

    mover_para_dentro = re.search(
        r"\b(?:cria|criar|crie)\b.*?\bpasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<pasta>.+?)\s+"
        r"(?:e\s+)?(?:dentro\s+del[ae]\s+|dentro\s+dess[ae]\s+)?(?:coloca|mova|move|mover)\s+"
        r"(?:a|uma)?\s*pasta\s+(?P<mover>.+?)(?:\s+dentro(?:\s+dela|\s+da\s+pasta)?)?$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if mover_para_dentro:
        pasta = str(mover_para_dentro.group("pasta") or "").strip(" .,!?:;\"'")
        mover = str(mover_para_dentro.group("mover") or "").strip(" .,!?:;\"'")
        if pasta and mover:
            return {"nome": pasta, "mover_item": mover}

    nested_folder = re.search(
        r"\b(?:cria|criar|crie)\b.*?\bpasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<pasta>.+?)\s+"
        r"(?:e\s+)?dentro(?:\s+del[ae]|\s+dess[ae]|\s+da\s+pasta|\s+do\s+diretorio|\s+do\s+diretório)?\s*(?:coloca|cria|criar|crie)\s+"
        r"(?:a|uma)?\s*pasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<interna>.+?)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if nested_folder:
        pasta = str(nested_folder.group("pasta") or "").strip(" .,!?:;\"'")
        interna = str(nested_folder.group("interna") or "").strip(" .,!?:;\"'")
        if pasta and interna:
            return {"nome": pasta, "pasta_interna": interna}

    pasta_dentro_de_outra = re.search(
        r"\b(?:cria|criar|crie)\s+(?:uma\s+)?pasta\s+"
        r"(?:chamada|chamado|chamadda|com nome)?\s*(?P<nome>.+?)\s+"
        r"dentro\s+(?!del[ae]\b|dess[ae]\b)(?:da\s+pasta\s+|do\s+diretorio\s+|do\s+diretório\s+|de\s+)?(?P<pai>.+?)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if pasta_dentro_de_outra:
        nome = str(pasta_dentro_de_outra.group("nome") or "").strip(" .,!?:;\"'")
        pasta_pai = str(pasta_dentro_de_outra.group("pai") or "").strip(" .,!?:;\"'")
        if nome and pasta_pai:
            return {"nome": nome, "pasta_pai": pasta_pai}

    combo = re.search(
        r"\b(?:cria|criar|crie)\b.*?\bpasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<pasta>.+?)\s+"
        r"(?:e\s+)?(?:dentro(?:\s+del[ae]|\s+dess[ae]|\s+da\s+pasta|\s+do\s+diretorio|\s+do\s+diretório)?\s*)?(?:coloca|cria|criar|crie)?\s*"
        r"(?:um\s+|uma\s+)?arquivo(?:\s+de\s+te(?:x|s)to)?\s+"
        r"(?:chamado|chamada|chamadda|com nome)?\s*(?P<arquivo>.+?)"
        r"(?:\s+(?:escrito(?:\s+nele)?|com\s+o\s+texto|com\s+texto|contendo|que\s+diga)\s+(?P<conteudo>.+))?$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if combo:
        pasta = str(combo.group("pasta") or "").strip(" .,!?:;\"'")
        arquivo = str(combo.group("arquivo") or "").strip(" .,!?:;\"'")
        conteudo = str(combo.group("conteudo") or "").strip(" .,!?:;\"'")
        if pasta:
            return {"nome": pasta, "arquivo_nome": arquivo, "arquivo_conteudo": conteudo}

    m_folder = re.search(
        r"\b(?:cria|criar|crie)\s+(?:uma\s+)?pasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(.+?)(?=\s+(?:e\s+dentro|dentro\s+del[ae]|dentro\s+dess[ae]|dentro|e\s+coloca|e\s+cria|e\s+arquivo|arquivo|com\s+um\s+arquivo|com\s+arquivo|,|;|\.)|$)",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_folder:
        nome = str(m_folder.group(1) or "").strip(" .,!?:;\"'")
        if nome:
            return {"nome": nome}
    return {}


def extrair_delete_pasta_arquivo(
    frase: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
) -> dict:
    """Extrai alvo/tipo de pedidos naturais de apagar/remover."""
    texto_local = re.sub(r"\s+", " ", str(frase or "").strip())
    if not texto_local:
        return {}

    if not re.search(r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\b", texto_local):
        return {}

    m_ref = re.search(
        r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\s+"
        r"(?P<ref>ela|ele|isso|essa|esse|essa\s+pasta|esse\s+arquivo)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_ref:
        ref = str(m_ref.group("ref") or "").strip()
        return {"alvo": ref}

    m_pasta = re.search(
        r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\s+"
        r"(?:a|o|uma|um)?\s*pasta\s+(?:chamada|chamado|com\s+nome|de\s+nome)?\s*"
        r"(?P<nome>.+?)(?=\s+(?:e\s+dentro|dentro\s+dela|com\s+arquivo|arquivo|que\s+tem|contendo)|$)",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_pasta:
        nome = str(m_pasta.group("nome") or "").strip(" .,!?:;\"'")
        if nome:
            return {"alvo": nome, "tipo": "pasta"}

    m_arquivo = re.search(
        r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\s+"
        r"(?:o|a|um|uma)?\s*(?:arquivo(?:\s+de\s+texto)?|txt)\s+"
        r"(?:chamado|chamada|com\s+nome|de\s+nome)?\s*(?P<nome>.+)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_arquivo:
        nome = str(m_arquivo.group("nome") or "").strip(" .,!?:;\"'")
        if nome and not nome.lower().endswith(".txt"):
            nome = f"{nome}.txt"
        if nome:
            return {"alvo": nome, "tipo": "arquivo"}

    m_generico = re.search(
        r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\s+"
        r"(?:o|a|os|as|um|uma)?\s*(?P<nome>[a-zA-Z0-9_\-.][a-zA-Z0-9_\-.\s]{0,40})$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_generico:
        nome = str(m_generico.group("nome") or "").strip(" .,!?:;\"'")
        normalizar = normalizar_texto if callable(normalizar_texto) else (lambda valor: str(valor or "").strip().lower())
        nome_norm = normalizar(nome)
        if nome and nome_norm not in {
            "arquivo",
            "pasta",
            "item",
            "negocio",
            "negócio",
            "isso",
            "essa",
            "esse",
            "ela",
            "ele",
        }:
            return {"alvo": nome}

    return {}


def detectar_intencao_arquivos(
    texto_sem_destino: str,
    *,
    params_cb: Callable[..., dict],
    estado_mental: Mapping[str, Any] | None = None,
    normalizar_texto: Callable[[str], str] | None = None,
) -> dict | None:
    """Roteia criacao/delecao de arquivos usando texto e contexto imediato."""
    t = str(texto_sem_destino or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    estado = dict(estado_mental or {})

    texto_confirmacao = t.casefold().strip(" .,!?:;")
    if existe_exclusao_pendente():
        if texto_confirmacao in {"sim", "pode", "pode apagar", "confirma", "confirmo", "apaga"}:
            return {"intent": "CONFIRM_DELETE_ITEM", "params": params()}
        if texto_confirmacao in {"nao", "não", "cancela", "cancelar", "deixa", "deixa quieto"}:
            return {"intent": "CANCEL_DELETE_ITEM", "params": params()}

    if re.fullmatch(
        r"(?:desfaz(?:er)?(?:\s+isso)?|restaura(?:r)?(?:\s+o)?\s+(?:ultimo|último)?\s*(?:arquivo|item|pasta)?|recupera(?:r)?(?:\s+o)?\s+(?:ultimo|último)?\s*(?:arquivo|item|pasta)?)",
        texto_confirmacao,
    ):
        return {"intent": "RESTORE_DELETED_ITEM", "params": params()}

    # "Apagar" também é uma forma natural de desligar dispositivos. Quando a
    # frase nomeia um alvo IoT e não declara arquivo/pasta, o roteador de
    # arquivos deve ceder ao domínio físico em vez de inventar um caminho.
    alvo_iot_explicito = bool(re.search(
        r"\b(?:luz|lampada|lâmpada|ventilador|tomada|dispositivo)\b",
        t,
        flags=re.IGNORECASE,
    ))
    alvo_arquivo_explicito = bool(re.search(
        r"\b(?:arquivo|pasta|diretorio|diretório|documento|txt|pdf)\b",
        t,
        flags=re.IGNORECASE,
    ))
    if alvo_iot_explicito and not alvo_arquivo_explicito and re.search(
        r"\b(?:apaga|apagar|desliga|desligar)\b", t, flags=re.IGNORECASE
    ):
        return None

    m_pasta_contextual = re.search(
        r"\bdentro\s+dela\b.*?\b(?:coloca|cria|criar|crie)\b\s+(?:a|uma)?\s*pasta\s+(?:chamada|com nome)?\s*(?P<nome>.+)$",
        t,
        flags=re.IGNORECASE,
    )
    if m_pasta_contextual:
        ultima_intencao = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
        ultimo_params = estado.get("ultima_acao_params") if isinstance(estado.get("ultima_acao_params"), dict) else {}
        pasta_pai = str(ultimo_params.get("nome") or ultimo_params.get("pasta") or ultimo_params.get("alvo") or "").strip()
        nome_contextual = str(m_pasta_contextual.group("nome") or "").strip(" .,!?:;\"'")
        if ultima_intencao == "CREATE_FOLDER" and pasta_pai and nome_contextual:
            return {"intent": "CREATE_FOLDER", "params": params(nome=nome_contextual, pasta_pai=pasta_pai)}

    delete_info = extrair_delete_pasta_arquivo(t, normalizar_texto=normalizar_texto)
    if delete_info:
        return {"intent": "DELETE_ITEM", "params": params(**delete_info)}

    pasta_info = extrair_criacao_pasta_arquivo(t)
    if pasta_info:
        return {"intent": "CREATE_FOLDER", "params": params(**pasta_info)}

    return None
