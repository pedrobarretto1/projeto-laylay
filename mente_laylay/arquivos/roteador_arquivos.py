"""Roteamento de comandos de arquivos da Laylay."""

from __future__ import annotations

import os
import re
from typing import Any, Callable, Mapping

from mente_laylay.arquivos.lixeira_laylay import existe_exclusao_pendente
from mente_laylay.arquivos.nome_natural import limpar_nome_arquivo_natural
from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_local,
)
from mente_laylay.cognicao.referencias_linguagem import (
    extrair_indice_referencia_ordinal,
)
from mente_laylay.cognicao.normalizacao_linguagem import texto_pede_opiniao


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


def extrair_criacao_arquivo(
    frase: str,
    *,
    estado_mental: Mapping[str, Any] | None = None,
) -> dict:
    """Extrai criação de arquivo independente, inclusive dentro de uma pasta.

    O contrato retornado é canônico para o executor: ``alvo`` contém somente
    o nome do arquivo e ``pasta`` contém o diretório opcional.
    """
    texto_local = re.sub(r"\s+", " ", str(frase or "").strip())
    if not texto_local:
        return {}
    estado = dict(estado_mental or {})
    ultima_intencao = str(
        estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or ""
    ).strip().upper()
    ultimo_status = str(estado.get("ultima_acao_status") or "").strip().casefold()
    ultimo_params = estado.get("ultima_acao_params")
    faltou_alvo = ultimo_status == "alvo_ausente" or (
        ultima_intencao == "CREATE_FILE"
        and isinstance(ultimo_params, Mapping)
        and not any(str(valor or "").strip() for valor in ultimo_params.values())
    )
    inicio = r"(?:coloca|coloque|cria|criar|crie)\s+(?:um\s+|uma\s+)?"
    # Uma continuação como "um de texto chamado Carlos..." só é operacional
    # quando a mente acabou de pedir o nome de um CREATE_FILE incompleto.
    if ultima_intencao == "CREATE_FILE" and faltou_alvo:
        inicio = rf"(?:{inicio}|(?:um\s+|uma\s+)?)"
    padrao = re.compile(
        rf"^\s*{inicio}"
        r"(?:(?:arquivo|documento)(?:\s+de\s+(?:texto|txt))?|de\s+(?:texto|txt))\s*"
        r"(?:chamado|chamada|com\s+nome|de\s+nome)?\s*"
        r"(?P<nome>.+?)"
        r"(?:\s+dentro\s+(?:da\s+pasta\s+|do\s+diretorio\s+|do\s+diretório\s+|de\s+)?(?P<pasta>.+?))?\s*$",
        flags=re.IGNORECASE,
    )
    encontrado = padrao.match(texto_local)
    if not encontrado:
        return {}
    nome = str(encontrado.group("nome") or "").strip(" .,!?:;\"'")
    pasta = str(encontrado.group("pasta") or "").strip(" .,!?:;\"'")
    pasta_norm = pasta.casefold()
    if pasta_norm in {
        "dela", "dele", "nela", "nele", "essa", "esse",
        "essa pasta", "aquela pasta", "a pasta",
    }:
        pasta = ""
        if ultima_intencao == "CREATE_FOLDER" and isinstance(ultimo_params, Mapping):
            pasta = str(
                ultimo_params.get("nome")
                or ultimo_params.get("alvo")
                or ultimo_params.get("pasta")
                or ""
            ).strip()
        if not pasta:
            return {}
    tipo_texto = bool(re.search(r"\b(?:de\s+texto|txt)\b", texto_local, re.IGNORECASE))
    if not nome or nome.casefold() in {"arquivo", "documento", "texto", "txt"}:
        return {}
    resultado = {"alvo": nome}
    if pasta:
        resultado["pasta"] = pasta
    if tipo_texto:
        resultado["tipo_arquivo"] = "texto"
    return resultado


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
        nome = limpar_nome_arquivo_natural(m_arquivo.group("nome") or "")
        if nome and not os.path.splitext(nome)[1]:
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
        nome = limpar_nome_arquivo_natural(m_generico.group("nome") or "")
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
        if (
            texto_confirmacao in {"nao", "não", "cancela", "cancelar", "deixa", "deixa quieto"}
            or classificar_confirmacao_local(t) is False
        ):
            return {"intent": "CANCEL_DELETE_ITEM", "params": params()}

    if re.fullmatch(
        r"(?:desfaz(?:er)?(?:\s+isso)?|restaura(?:r)?(?:\s+o)?\s+(?:ultimo|último)?\s*(?:arquivo|item|pasta)?|recupera(?:r)?(?:\s+o)?\s+(?:ultimo|último)?\s*(?:arquivo|item|pasta)?)",
        texto_confirmacao,
    ):
        return {"intent": "RESTORE_DELETED_ITEM", "params": params()}

    estrutura_recente = (
        dict(estado.get("ultima_estrutura_arquivo_params") or {})
        if isinstance(estado.get("ultima_estrutura_arquivo_params"), dict)
        else {}
    )
    pesquisa_recente = (
        estrutura_recente
        if str(estrutura_recente.get("tipo") or "") == "pesquisa_semantica"
        else {}
    )
    resultados_recentes = [
        str(item or "").strip()
        for item in list(pesquisa_recente.get("resultados") or [])
        if str(item or "").strip()
    ]
    nomes_recentes = [
        str(item or "").strip()
        for item in list(pesquisa_recente.get("nomes") or [])
    ]
    consulta_recente = str(pesquisa_recente.get("consulta") or "").strip()

    # Continuidade direta da última busca, sem depender de uma lista paralela.
    bloqueia_selecao = bool(re.search(
        r"^(?:voce|você|lay|laylay)\s+(?:consegue|sabe|e capaz|é capaz)\b|"
        r"^se eu (?:pedir|mandar)\b|^(?:nao|não)\s+",
        texto_confirmacao,
    ))
    indice = extrair_indice_referencia_ordinal(texto_confirmacao)
    # Depois de uma busca que acabou de listar opções, uma resposta curta como
    # "o primeiro" já é uma seleção inequívoca. Fora desse contexto o ordinal
    # solto continua não operacional, evitando transformar relatos como "foi o
    # primeiro jogo" em abertura de arquivo.
    if indice is None and resultados_recentes and re.fullmatch(
        r"(?:(?:o|a)\s+)?(?:primeir[oa]|segund[oa]|terceir[oa]|quart[oa]|"
        r"quint[oa]|sext[oa]|s[eé]tim[oa]|oitav[oa]|non[oa]|d[eé]cim[oa]|"
        r"\d{1,2}(?:\s*[ºª])?)",
        texto_confirmacao,
    ):
        indice = extrair_indice_referencia_ordinal(f"abre {texto_confirmacao}")
    if indice is not None and resultados_recentes and not bloqueia_selecao:
        if 0 <= indice < len(resultados_recentes):
            nome = nomes_recentes[indice] if indice < len(nomes_recentes) else os.path.basename(resultados_recentes[indice])
            return {
                "intent": "FILE_OPEN_RESULT",
                "params": params(caminho=resultados_recentes[indice], alvo=nome, indice=indice + 1),
            }

    if resultados_recentes and re.fullmatch(
        r"(?:onde\s+(?:ele|ela|esse|essa|o\s+arquivo)\s+(?:fica|esta|está)|"
        r"qual\s+(?:e|é)\s+o\s+caminho(?:\s+dele|\s+dela)?|mostra\s+o\s+caminho)",
        texto_confirmacao,
    ):
        return {
            "intent": "FILE_SEARCH",
            "params": params(
                query=consulta_recente,
                referencia_caminho=resultados_recentes[0],
                alvo=nomes_recentes[0] if nomes_recentes else os.path.basename(resultados_recentes[0]),
            ),
        }

    if consulta_recente and re.search(
        r"\b(?:tenta|procura|busca|pesquisa)\b.*\b(?:de novo|novamente)\b",
        texto_confirmacao,
    ):
        return {
            "intent": "FILE_SEARCH",
            "params": params(
                query=consulta_recente,
                forcar_indice=True,
                somente_projeto=bool(re.search(r"\bprojeto(?:\s+da\s+laylay)?\b", texto_confirmacao)),
            ),
        }

    # Perguntas hipotéticas, negativas e sobre capacidade não autorizam nem
    # mesmo uma consulta de leitura; o mapa vivo responde sobre a habilidade.
    bloqueia_pesquisa = bool(
        texto_pede_opiniao(texto_confirmacao)
        or re.search(
            r"\b(?:voce|você|lay|laylay)\s+(?:consegue|pode|sabe|é capaz|e capaz)\b|"
            r"\b(?:como eu faria|se eu pedir|nao procura|não procura|nao busque|não busque)\b",
            texto_confirmacao,
        )
    )
    padroes_pesquisa = (
        r"^(?:encontra|encontre|achar|ache|acha|procura|procure|buscar|busca|pesquisa|pesquise|localiza|localize)\b",
        r"^onde\s+(?:esta|está|fica)\b.*\b(?:arquivo|documento|codigo|código|imagem|foto|script)\b",
        r"^(?:quais?|mostra|mostre|lista|liste)\s+(?:os\s+|meus\s+|as\s+|minhas\s+)?"
        r"(?:arquivos|documentos|imagens|fotos|scripts)\b.*\b(?:fala|falam|sobre|com|relacionad)\w*",
    )
    if not bloqueia_pesquisa and any(re.search(padrao, texto_confirmacao) for padrao in padroes_pesquisa):
        consulta = texto_confirmacao
        consulta = re.sub(
            r"^(?:encontra|encontre|achar|ache|acha|procura|procure|buscar|busca|pesquisa|pesquise|localiza|localize)\s+",
            "", consulta,
        )
        consulta = re.sub(r"^onde\s+(?:esta|está|fica)\s+", "", consulta)
        consulta = re.sub(
            r"^(?:quais?|mostra|mostre|lista|liste)\s+(?:os\s+|meus\s+|as\s+|minhas\s+)?",
            "", consulta,
        )
        consulta = re.sub(r"\b(?:nos?|dentro\s+dos?)\s+meus\s+arquivos\b", " ", consulta)
        consulta = re.sub(r"^(?:o|a|os|as|um|uma)\s+", "", consulta)
        consulta = re.sub(r"^(?:arquivo|arquivos|documento|documentos)\s+", "", consulta)
        consulta = re.sub(r"\b(?:que\s+fala|que\s+falam|falando|relacionados?)\s+(?:do|da|de|sobre)\s+", " ", consulta)
        consulta = re.sub(r"\b(?:algo\s+)?sobre\s+", " ", consulta)
        consulta = re.sub(r"\s+", " ", consulta).strip(" .,!?:;\"'")
        if consulta:
            return {
                "intent": "FILE_SEARCH",
                "params": params(
                    query=consulta,
                    somente_projeto=bool(re.search(r"\bprojeto(?:\s+da\s+laylay)?\b", texto_confirmacao)),
                ),
            }

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

    arquivo_info = extrair_criacao_arquivo(t, estado_mental=estado)
    if arquivo_info:
        return {"intent": "CREATE_FILE", "params": params(**arquivo_info)}

    pasta_info = extrair_criacao_pasta_arquivo(t)
    if pasta_info:
        return {"intent": "CREATE_FOLDER", "params": params(**pasta_info)}

    return None
