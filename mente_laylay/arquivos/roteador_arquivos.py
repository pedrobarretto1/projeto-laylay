"""Roteamento de comandos de arquivos da Laylay."""

from __future__ import annotations

import os
import re
import time
from typing import Any, Callable, Mapping

from mente_laylay.arquivos.lixeira_laylay import existe_exclusao_pendente
from mente_laylay.arquivos.nome_natural import limpar_nome_arquivo_natural
from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_local,
)
from mente_laylay.cognicao.referencias_linguagem import (
    extrair_indice_referencia_ordinal,
    separar_alvo_e_complemento_foco,
    valor_e_referencia_contextual,
)
from mente_laylay.cognicao.normalizacao_linguagem import texto_pede_opiniao
from mente_laylay.memoria_mental.continuidade_contexto import (
    estrutura_arquivo_recente,
)


def _get(ctx: Mapping[str, Any], key: str):
    return ctx.get(key)


def _arquivo_recente(estado: Mapping[str, Any]) -> tuple[str, str]:
    """Retorna o ultimo arquivo concreto publicado pela mente unica.

    A estrutura recente e a fonte canonica para pronomes de arquivo.  Nao
    usamos ``ultimo_alvo`` aqui porque ele pode pertencer a conversa, pessoa,
    aplicativo ou qualquer outro dominio.
    """
    estrutura = dict(estrutura_arquivo_recente(dict(estado or {})) or {})
    tipo = str(estrutura.get("tipo") or "").strip().casefold()
    if tipo == "arquivo":
        caminho = str(estrutura.get("caminho") or "").strip()
        nome_publicado = str(
            estrutura.get("arquivo_nome")
            or estrutura.get("nome_arquivo")
            or estrutura.get("arquivo")
            or (os.path.basename(caminho) if caminho else "")
        ).strip()
        nome = os.path.basename(nome_publicado) or os.path.basename(caminho)
        return caminho, nome
    return "", ""


def _pasta_recente(estado: Mapping[str, Any]) -> tuple[str, str]:
    estrutura = dict(estrutura_arquivo_recente(dict(estado or {})) or {})
    if str(estrutura.get("tipo") or "").strip().casefold() == "pasta":
        caminho = str(estrutura.get("caminho") or "").strip()
        nome = str(
            estrutura.get("nome")
            or estrutura.get("pasta")
            or (os.path.basename(caminho) if caminho else "")
        ).strip()
        if caminho or nome:
            return caminho, nome
    caminho = str(estado.get("ultima_pasta") or "").strip()
    return caminho, os.path.basename(caminho) if caminho else ""


def _limpar_item_movimentacao(valor: str, *, destino: bool = False) -> str:
    texto = str(valor or "").strip(" .,!?:;\"'")
    if destino:
        texto = re.sub(
            r"^(?:a|o|uma|um)?\s*(?:pasta|diretorio|diretório)\s+",
            "",
            texto,
            flags=re.IGNORECASE,
        )
        texto = re.sub(r"^(?:a|o|uma|um)\s+", "", texto, flags=re.IGNORECASE)
    else:
        moldura_removida = bool(re.match(
            r"^(?:o|a|um|uma)?\s*(?:arquivo|documento|item)\s+",
            texto,
            flags=re.IGNORECASE,
        ))
        texto = re.sub(
            r"^(?:o|a|um|uma)?\s*(?:arquivo|documento|item)\s+",
            "",
            texto,
            flags=re.IGNORECASE,
        )
        texto = limpar_nome_arquivo_natural(texto)
        if not moldura_removida and re.search(
            r"\.[a-z0-9]{1,10}$", texto, flags=re.IGNORECASE,
        ):
            texto = re.sub(r"^(?:o|a|um|uma)\s+", "", texto, flags=re.IGNORECASE)
    return texto.strip(" .,!?:;\"'")


def _nomes_arquivo_equivalentes(declarado: str, conhecido: str) -> bool:
    """Compara um nome falado com um basename concreto sem adivinhar caminhos."""
    nome_declarado = os.path.basename(
        limpar_nome_arquivo_natural(declarado).replace("/", os.sep)
    ).casefold()
    nome_conhecido = os.path.basename(str(conhecido or "").replace("/", os.sep)).casefold()
    if not nome_declarado or not nome_conhecido:
        return False
    if nome_declarado == nome_conhecido:
        return True
    raiz_declarada, extensao_declarada = os.path.splitext(nome_declarado)
    raiz_conhecida, extensao_conhecida = os.path.splitext(nome_conhecido)
    return bool(
        raiz_declarada == raiz_conhecida
        and {extensao_declarada, extensao_conhecida} == {"", ".txt"}
    )


def _exclusao_confirmada_recente(
    estado: Mapping[str, Any], *, ttl_s: float = 300.0,
) -> str:
    """Retorna somente o caminho ligado ao último descarte confirmado."""
    contrato = (
        dict(estado.get("ultima_acao_contrato") or {})
        if isinstance(estado.get("ultima_acao_contrato"), Mapping)
        else {}
    )
    intent = str(contrato.get("intent") or "").strip().upper()
    status = str(contrato.get("status") or "").strip().casefold()
    if (
        intent not in {"CONFIRM_DELETE_ITEM", "DELETE_ITEM"}
        or contrato.get("executou") is not True
        or contrato.get("confirmado") is not True
        or status != "movido_para_lixeira"
    ):
        return ""
    try:
        idade = time.time() - float(estado.get("ultima_acao_ts") or 0.0)
    except (TypeError, ValueError):
        return ""
    if idade < 0.0 or idade > max(1.0, float(ttl_s)):
        return ""
    return str(contrato.get("alvo") or estado.get("ultima_acao_alvo") or "").strip()


def _remover_aspas_pareadas(valor: str) -> str:
    texto = str(valor or "").strip()
    if len(texto) >= 2 and texto[0] == texto[-1] and texto[0] in {'"', "'"}:
        return texto[1:-1].strip()
    return texto


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

    # Um pedido composto como "cria um arquivo chamado notas e dentro dele
    # escreva ..." continua sendo uma unica mutacao de arquivo.  Esta leitura
    # precisa vir antes da regra generica de ``dentro de <pasta>``; caso
    # contrario, o "e" entra no nome e "dele escreva ..." vira um diretorio.
    # O conteudo e preservado como foi dito, removendo apenas aspas externas
    # pareadas.  Nome, conteudo e referencia permanecem no contrato canonico
    # de CREATE_FILE, sem introduzir um executor paralelo.
    prefixo_arquivo = (
        rf"^\s*{inicio}"
        r"(?:(?:arquivo|documento)(?:\s+de\s+(?:texto|txt))?|de\s+(?:texto|txt))\s*"
        r"(?:chamado|chamada|com\s+nome|de\s+nome)?\s*"
        r"(?P<nome>.+?)\s+"
    )
    referencia_interna = r"(?:dentro\s+del[ae]|nel[ae]|ness[ae])"
    verbo_escrita = (
        r"(?:escreva|escreve|escrever|grave|grava|gravar|coloque|coloca|"
        r"insira|insere|inserir|adicione|adiciona|adicionar)"
    )
    marcadores_conteudo = (
        rf"(?:e\s+)?(?:{referencia_interna}\s+{verbo_escrita}|"
        rf"{verbo_escrita}\s+{referencia_interna})"
        r"|(?:com\s+(?:o\s+)?texto|com\s+conte[uú]do|contendo|que\s+diga)"
    )
    composto = re.match(
        prefixo_arquivo
        + rf"(?:{marcadores_conteudo})\s+(?P<conteudo>.+?)\s*$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if not composto:
        # Variação igualmente natural: "crie notas e escreva o texto nele".
        composto = re.match(
            prefixo_arquivo
            + rf"(?:e\s+)?{verbo_escrita}\s+(?P<conteudo>.+?)\s+"
              rf"(?:{referencia_interna})\s*$",
            texto_local,
            flags=re.IGNORECASE,
        )
    if composto:
        nome_composto = limpar_nome_arquivo_natural(composto.group("nome") or "")
        conteudo_composto = _remover_aspas_pareadas(composto.group("conteudo") or "")
        if (
            nome_composto
            and conteudo_composto
            and nome_composto.casefold() not in {"arquivo", "documento", "texto", "txt"}
        ):
            resultado_composto = {
                "alvo": nome_composto,
                "conteudo": conteudo_composto,
            }
            if re.search(r"\b(?:de\s+texto|txt)\b", texto_local, re.IGNORECASE):
                resultado_composto["tipo_arquivo"] = "texto"
            return resultado_composto

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

    if not re.search(
        r"\b(?:apaga|apague|apagar|delete|deleta|deletar|remove|remova|"
        r"remover|exclui|exclua|excluir)\b",
        texto_local,
        flags=re.IGNORECASE,
    ):
        return {}

    # Marcadores de repetição qualificam a ação, não fazem parte do nome do
    # arquivo. Sem essa limpeza, ``apaga novamente o arquivo X`` procurava um
    # arquivo literalmente chamado ``novamente o arquivo X``.
    texto_local = re.sub(
        r"\b(apaga|apague|apagar|delete|deleta|deletar|remove|remova|"
        r"remover|exclui|exclua|excluir)\s+(?:novamente|de\s+novo|outra\s+vez)\s+",
        r"\1 ",
        texto_local,
        count=1,
        flags=re.IGNORECASE,
    )

    m_ref = re.search(
        r"\b(?:apaga|apague|apagar|delete|deleta|deletar|remove|remova|remover|exclui|exclua|excluir)\s+"
        r"(?P<ref>ela|ele|isso|essa|esse|essa\s+pasta|esse\s+arquivo)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_ref:
        ref = str(m_ref.group("ref") or "").strip()
        return {"alvo": ref}

    m_pasta = re.search(
        r"\b(?:apaga|apague|apagar|delete|deleta|deletar|remove|remova|remover|exclui|exclua|excluir)\s+"
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
        r"\b(?:apaga|apague|apagar|delete|deleta|deletar|remove|remova|remover|exclui|exclua|excluir)\s+"
        r"(?:o|a|um|uma)?\s*(?:arquivo(?:\s+de\s+texto)?|txt)\s+"
        r"(?:chamado|chamada|com\s+nome|de\s+nome)?\s*(?P<nome>.+)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_arquivo:
        nome = limpar_nome_arquivo_natural(
            str(m_arquivo.group("nome") or "").strip(" .,!?:;\"'")
        )
        if nome and not os.path.splitext(nome)[1]:
            nome = f"{nome}.txt"
        if nome:
            return {"alvo": nome, "tipo": "arquivo"}

    m_generico = re.search(
        r"\b(?:apaga|apague|apagar|delete|deleta|deletar|remove|remova|remover|exclui|exclua|excluir)\s+"
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
        r"(?:desfaz(?:er)?(?:\s+isso)?|"
        r"restaura(?:r)?(?:\s+o)?\s+(?:ultimo|último)?\s*(?:arquivo|item|pasta)?|"
        r"recupera(?:r)?(?:\s+o)?\s+(?:ultimo|último)?\s*(?:arquivo|item|pasta)?|"
        r"(?:eu\s+)?quero\s+(?:ele|ela|isso|o\s+arquivo|a\s+pasta)\s+de\s+volta|"
        r"traz\s+(?:ele|ela|isso|o\s+arquivo|a\s+pasta)\s+de\s+volta)",
        texto_confirmacao,
    ):
        alvo_exclusao = _exclusao_confirmada_recente(estado)
        if alvo_exclusao:
            return {
                "intent": "RESTORE_DELETED_ITEM",
                "params": params(
                    alvo=alvo_exclusao,
                    referencia_exclusao_confirmada=True,
                ),
            }
        return None

    estrutura_recente = dict(estrutura_arquivo_recente(estado) or {})
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
    arquivo_recente_caminho, arquivo_recente_nome = _arquivo_recente(estado)
    pasta_recente_caminho, _pasta_recente_nome = _pasta_recente(estado)

    movimentacao = re.fullmatch(
        r"(?:coloca|coloque|bota|ponha|poe|põe|move|mova|transfere|transfira)\s+"
        r"(?P<origem>.+?)\s+(?:dentro|para|pra)\s+"
        r"(?:(?:de|do|da)\s+)?(?P<destino>.+)",
        t.rstrip(" .,!?:;"),
        flags=re.IGNORECASE,
    )
    if movimentacao:
        origem_bruta = str(movimentacao.group("origem") or "").strip()
        destino_bruto = str(movimentacao.group("destino") or "").strip()
        origem = _limpar_item_movimentacao(origem_bruta)
        destino = _limpar_item_movimentacao(destino_bruto, destino=True)
        if valor_e_referencia_contextual(origem):
            origem = str(
                estado.get("ultimo_caminho_arquivo")
                or arquivo_recente_caminho
                or ""
            ).strip()
        if destino.casefold() in {
            "ele", "ela", "dele", "dela", "nele", "nela", "isso",
            "essa", "esse", "esta", "este", "essa pasta", "a pasta",
        }:
            destino = pasta_recente_caminho
        fonte_generica_sem_referencia = bool(re.fullmatch(
            r"(?:um|uma|o|a)?\s*(?:arquivo|documento|item)",
            origem_bruta,
            re.IGNORECASE,
        )) or bool(re.match(
            r"^(?:um|uma|o|a)?\s*(?:arquivo|documento)\s+"
            r"(?:de\s+texto\s+)?(?:chamado|chamada|com\s+nome)\b",
            origem_bruta,
            re.IGNORECASE,
        ))
        if origem and destino and not fonte_generica_sem_referencia:
            return {
                "intent": "FILE_TRANSACTION",
                "params": params(
                    operacao="mover",
                    origem=origem,
                    destino=destino,
                    referencia_contextual=bool(
                        valor_e_referencia_contextual(origem_bruta)
                        or destino_bruto.casefold() in {
                            "ele", "ela", "dele", "dela", "nele", "nela",
                            "isso", "essa", "esse", "esta", "este",
                            "essa pasta", "a pasta",
                        }
                    ),
                ),
            }

    pergunta_caminho_arquivo = bool(re.fullmatch(
        r"(?:onde\s+(?:(?:ele|ela|esse|essa|este|esta|o\s+arquivo|esse\s+arquivo)\s+)?"
        r"(?:fica|esta|está)(?:\s+agora)?|onde\s+(?:fica|esta|está)\s+"
        r"(?:ele|ela|esse|essa|este|esta|o\s+arquivo|esse\s+arquivo)(?:\s+agora)?|"
        r"qual\s+(?:e|é)\s+o\s+caminho(?:\s+completo)?(?:\s+(?:dele|dela|desse\s+arquivo))?|"
        r"mostra\s+o\s+caminho(?:\s+completo)?(?:\s+(?:dele|dela|desse\s+arquivo))?)",
        texto_confirmacao,
    ))
    if pergunta_caminho_arquivo and arquivo_recente_caminho:
        return {
            "intent": "FILE_SEARCH",
            "params": params(
                query=arquivo_recente_nome or os.path.basename(arquivo_recente_caminho),
                referencia_caminho=arquivo_recente_caminho,
                alvo=arquivo_recente_nome or os.path.basename(arquivo_recente_caminho),
            ),
        }

    leitura_referenciada = re.fullmatch(
        r"(?:leia|ler|l[eê]|mostra|mostre|diz|fale)\s+"
        r"(?:(?:o\s+)?conte[uú]do\s+(?:(?:de|do|da)\s+)?)?"
        r"(?P<referencia>ele|ela|dele|dela|isso|esse\s+arquivo|"
        r"este\s+arquivo|o\s+arquivo|esse|este)"
        r"(?:\s+(?:novamente|de\s+novo|outra\s+vez))?",
        texto_confirmacao,
    )
    if arquivo_recente_caminho and leitura_referenciada:
        return {
            "intent": "FILE_READ",
            "params": params(
                caminho=arquivo_recente_caminho,
                alvo=arquivo_recente_nome or os.path.basename(arquivo_recente_caminho),
                referencia_contextual=True,
            ),
        }

    # Consulta nomeada em ordem natural: "Onde o relatorio.txt fica?". A
    # gramática anterior só reconhecia "Onde fica o arquivo..." ou pronomes,
    # fazendo a forma mais comum escapar para a conversa livre.
    caminho_nomeado = re.fullmatch(
        r"onde\s+(?:(?:o|a)\s+)?(?:(?:arquivo|documento)\s+)?"
        r"(?P<nome>.+?)\s+(?:fica|esta|está)(?:\s+agora)?",
        texto_confirmacao,
    )
    if caminho_nomeado:
        nome_bruto = str(caminho_nomeado.group("nome") or "").strip()
        moldura_arquivo = bool(re.match(
            r"^onde\s+(?:(?:o|a)\s+)?(?:arquivo|documento)\b",
            texto_confirmacao,
        ))
        nome = limpar_nome_arquivo_natural(nome_bruto)
        if (
            nome
            and nome.casefold() not in {
                "ele", "ela", "esse", "essa", "este", "esta", "arquivo",
            }
            and (moldura_arquivo or bool(os.path.splitext(nome)[1]))
        ):
            nome_recente = str(
                arquivo_recente_nome
                or (os.path.basename(arquivo_recente_caminho) if arquivo_recente_caminho else "")
            ).strip()
            if (
                arquivo_recente_caminho
                and nome_recente
                and nome.casefold() == nome_recente.casefold()
            ):
                return {
                    "intent": "FILE_SEARCH",
                    "params": params(
                        query=nome,
                        referencia_caminho=arquivo_recente_caminho,
                        alvo=nome_recente,
                    ),
                }
            return {
                "intent": "FILE_SEARCH",
                "params": params(query=nome, alvo=nome),
            }

    abertura_referenciada = re.fullmatch(
        r"(?:tenta\s+(?:abrir|abre)|abre|abra|abrir|mostra|mostre)\s+"
        r"(?P<referencia>.+)",
        texto_confirmacao,
    )
    if arquivo_recente_caminho and abertura_referenciada:
        referencia_bruta = str(abertura_referenciada.group("referencia") or "")
        referencia_limpa, pediu_foco = separar_alvo_e_complemento_foco(
            referencia_bruta
        )
        if valor_e_referencia_contextual(referencia_limpa):
            params_abertura = {
                "caminho": arquivo_recente_caminho,
                "alvo": arquivo_recente_nome or os.path.basename(arquivo_recente_caminho),
            }
            if pediu_foco:
                params_abertura["modo"] = "focus"
                params_abertura["referencia_contextual"] = True
            return {"intent": "FILE_OPEN_RESULT", "params": params(**params_abertura)}

    # Um nome explícito de arquivo não é nome de aplicativo. A abertura direta
    # só nasce quando o nome pode ser ligado a um caminho concreto publicado
    # pela própria habilidade (arquivo recente ou resultado de busca local).
    if abertura_referenciada:
        referencia_bruta = str(abertura_referenciada.group("referencia") or "")
        referencia_limpa, pediu_foco = separar_alvo_e_complemento_foco(
            referencia_bruta
        )
        referencia_limpa = re.sub(
            r"^(?:(?:o|a|um|uma)\s+)?(?:arquivo|documento)\s+",
            "",
            referencia_limpa,
            count=1,
            flags=re.IGNORECASE,
        ).strip()
        referencia_limpa = re.sub(
            r"^(?:o|a|um|uma)\s+",
            "",
            referencia_limpa,
            count=1,
            flags=re.IGNORECASE,
        ).strip()
        nome_declarado = limpar_nome_arquivo_natural(referencia_limpa)
        candidatos: list[tuple[str, str]] = []
        if arquivo_recente_caminho:
            candidatos.append((
                arquivo_recente_caminho,
                arquivo_recente_nome or os.path.basename(arquivo_recente_caminho),
            ))
        candidatos.extend(
            (
                caminho,
                nomes_recentes[indice]
                if indice < len(nomes_recentes)
                else os.path.basename(caminho),
            )
            for indice, caminho in enumerate(resultados_recentes)
        )
        caminho_resolvido = ""
        nome_resolvido = ""
        for caminho_candidato, nome_candidato in candidatos:
            if _nomes_arquivo_equivalentes(nome_declarado, nome_candidato):
                caminho_resolvido = caminho_candidato
                nome_resolvido = (
                    os.path.basename(caminho_candidato)
                    or os.path.basename(nome_candidato)
                )
                break
        if caminho_resolvido:
            params_abertura = {
                "caminho": caminho_resolvido,
                "alvo": nome_resolvido,
            }
            if pediu_foco:
                params_abertura["modo"] = "focus"
                params_abertura["referencia_contextual"] = True
            return {"intent": "FILE_OPEN_RESULT", "params": params(**params_abertura)}

        # Um nome de arquivo explícito continua pertencendo ao domínio de
        # arquivos mesmo quando o foco recente aponta para outra pasta. A
        # pesquisa local só abre se encontrar um basename equivalente; nunca
        # promove o primeiro resultado aproximado nem entrega ``.txt`` ao
        # resolvedor de aplicativos.
        moldura_arquivo = bool(re.match(
            r"^(?:(?:o|a|um|uma)\s+)?(?:arquivo|documento)\b",
            referencia_bruta,
            flags=re.IGNORECASE,
        ))
        if nome_declarado and (
            moldura_arquivo or bool(os.path.splitext(nome_declarado)[1])
        ):
            dados_busca = {
                "query": nome_declarado,
                "alvo": nome_declarado,
                "abrir_resultado_exato": True,
            }
            if pediu_foco:
                dados_busca["modo"] = "focus"
            return {"intent": "FILE_SEARCH", "params": params(**dados_busca)}

    # Exclusão por pronome só pode herdar um artefato de arquivo tipado. Isso
    # impede que um referente recente de outro domínio (pessoa, conversa,
    # aplicativo) seja promovido a alvo destrutivo por engano.
    if arquivo_recente_caminho and re.fullmatch(
        r"(?:apaga|apague|exclui|exclua|deleta|delete|remove|remova)\s+"
        r"(?:ele|isso|esse|este|o\s+arquivo|esse\s+arquivo|este\s+arquivo)",
        texto_confirmacao,
    ):
        return {
            "intent": "DELETE_ITEM",
            "params": params(
                alvo=arquivo_recente_caminho,
                tipo="arquivo",
            ),
        }

    # Edicao explicita de um arquivo existente. O conteudo e o alvo ficam
    # separados antes de qualquer normalizacao que possa destruir aspas ou a
    # extensao. Pronomes so sao aceitos quando a mente publicou um caminho de
    # arquivo concreto no turno anterior.
    escrita = re.fullmatch(
        r"(?P<verbo>escreve|escreva|grava|grave|adiciona|adicione|acrescenta|acrescente)\s+"
        r"(?P<conteudo>.+?)\s+"
        r"(?:(?P<pronome>nele|nela|dentro\s+dele|dentro\s+dela|nesse\s+arquivo|"
        r"neste\s+arquivo)|dentro\s+(?:do|da)\s+(?:arquivo\s+)?(?P<alvo>.+))",
        t.rstrip(" .,!?:;"),
        flags=re.IGNORECASE,
    )
    if escrita:
        conteudo = _remover_aspas_pareadas(escrita.group("conteudo") or "")
        # Em "acrescente a frase X nele", artigo e substantivo apenas
        # apresentam o conteúdo; não fazem parte do texto solicitado. Formas
        # sem essa moldura ("acrescente X nele") permanecem literais.
        if str(escrita.group("verbo") or "").casefold() in {
            "adiciona", "adicione", "acrescenta", "acrescente",
        }:
            conteudo = re.sub(
                r"^(?:a\s+)?(?:frase|linha|texto|trecho)\s+",
                "",
                conteudo,
                count=1,
                flags=re.IGNORECASE,
            ).strip()
        alvo_declarado = str(escrita.group("alvo") or "").strip(" .,!?:;\"'")
        alvo = alvo_declarado
        if escrita.group("pronome"):
            alvo = arquivo_recente_caminho
        elif arquivo_recente_caminho and alvo_declarado:
            nome_declarado = limpar_nome_arquivo_natural(alvo_declarado).casefold()
            nomes_equivalentes = {
                arquivo_recente_nome.casefold(),
                os.path.basename(arquivo_recente_caminho).casefold(),
            }
            if nome_declarado in nomes_equivalentes:
                alvo = arquivo_recente_caminho
        if conteudo and alvo:
            verbo = str(escrita.group("verbo") or "").casefold()
            modo_escrita = "append" if (
                verbo in {"adiciona", "adicione", "acrescenta", "acrescente"}
                or re.search(
                    r"\b(?:segunda|outra|nova|mais\s+uma)\s+linha\b",
                    conteudo,
                    flags=re.IGNORECASE,
                )
            ) else "overwrite"
            return {
                "intent": "CREATE_FILE",
                "params": params(
                    alvo=alvo,
                    conteudo=conteudo,
                    editar_existente=True,
                    **({"modo_escrita": modo_escrita} if modo_escrita == "append" else {}),
                ),
            }

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
        r"qual\s+(?:e|é)\s+o\s+caminho(?:\s+completo)?(?:\s+dele|\s+dela)?|"
        r"mostra\s+o\s+caminho(?:\s+completo)?)",
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
    iniciou_com_verbo_generico = bool(re.search(padroes_pesquisa[0], texto_confirmacao))
    marcador_local = bool(
        re.search(
            r"\b(?:arquivo|arquivos|pasta|pastas|documento|documentos|diretorio|"
            r"diretório|diretorios|diretórios|codigo|código|script|scripts|imagem|"
            r"imagens|foto|fotos|planilha|planilhas|pdf|txt|caminho|caminhos|atalho|"
            r"atalhos|projeto|computador|pc|disco|downloads|desktop)\b|"
            r"\.[a-z0-9]{1,8}\b|\b(?:nos?|dentro\s+dos?)\s+meus\s+arquivos\b|"
            r"\b(?:neste|nesse|no)\s+computador\b",
            texto_confirmacao,
        )
    )
    corresponde_pesquisa = any(
        re.search(padrao, texto_confirmacao) for padrao in padroes_pesquisa
    )
    # Verbos como "pesquisa", "busca" e "procura" também descrevem uma
    # pesquisa web. Sem evidência explícita de arquivo ou armazenamento local,
    # este especialista deve ceder ao roteador do navegador.
    if iniciou_com_verbo_generico and not marcador_local:
        corresponde_pesquisa = False
    if not bloqueia_pesquisa and corresponde_pesquisa:
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
        alvo_declarado = str(delete_info.get("alvo") or "").strip()
        if (
            arquivo_recente_caminho
            and str(delete_info.get("tipo") or "").casefold() == "arquivo"
            and _nomes_arquivo_equivalentes(
                alvo_declarado,
                arquivo_recente_nome or os.path.basename(arquivo_recente_caminho),
            )
        ):
            delete_info["alvo"] = arquivo_recente_caminho
        return {"intent": "DELETE_ITEM", "params": params(**delete_info)}

    arquivo_info = extrair_criacao_arquivo(t, estado_mental=estado)
    if arquivo_info:
        return {"intent": "CREATE_FILE", "params": params(**arquivo_info)}

    pasta_info = extrair_criacao_pasta_arquivo(t)
    if pasta_info:
        return {"intent": "CREATE_FOLDER", "params": params(**pasta_info)}

    return None
