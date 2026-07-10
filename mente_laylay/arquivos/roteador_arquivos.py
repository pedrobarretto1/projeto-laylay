"""Roteamento de comandos de arquivos da Laylay."""

from __future__ import annotations

import ast
import re
from typing import Any, Callable, Mapping


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
        r"(?:um\s+|uma\s+)?arquivo(?:\s+de\s+texto)?\s+"
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

    combo = re.search(
        r"\b(?:cria|criar|crie)\b.*?\bpasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<pasta>.+?)\s+"
        r"(?:e\s+)?(?:dentro(?:\s+del[ae]|\s+dess[ae]|\s+da\s+pasta|\s+do\s+diretorio|\s+do\s+diretório)?\s*)?(?:coloca|cria|criar|crie)?\s*"
        r"(?:um\s+|uma\s+)?arquivo(?:\s+de\s+texto)?\s+"
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


def executar_comando_arquivos(c_nome: str, c_args: str, comando: str, c_upper: str, ctx: Mapping[str, Any]) -> bool:
    c = str(c_nome or "").upper()
    a = "" if c_args is None else str(c_args).strip()

    criar_pasta = _get(ctx, "criar_pasta")
    criar_ou_editar_arquivo = _get(ctx, "criar_ou_editar_arquivo")
    mover_arquivo = _get(ctx, "mover_arquivo")
    renomear_arquivo = _get(ctx, "renomear_arquivo")
    deletar_item = _get(ctx, "deletar_item")
    buscar_arquivo_no_pc = _get(ctx, "buscar_arquivo_no_pc")
    falar = _get(ctx, "falar_com_lipsync")
    organizar_janelas_robusto = _get(ctx, "organizar_janelas_robusto")

    if c == "CRIAR_PASTA" and callable(criar_pasta):
        nome = a.strip(' "\'')
        if nome:
            criar_pasta(nome)
        return True

    if c == "ESCREVER_ARQUIVO" and callable(criar_ou_editar_arquivo):
        try:
            test_str = a.strip()
            if not test_str.startswith("("):
                test_str = f"({test_str})"
            args = ast.literal_eval(test_str)
            if isinstance(args, tuple) and len(args) >= 2:
                caminho = str(args[0])
                conteudo = str(args[1])
                modo = str(args[2]) if len(args) > 2 else "w"
                criar_ou_editar_arquivo(caminho, conteudo, modo)
                return True
        except Exception:
            pass

        pattern = r"'(.*?)'|\"(.*?)\""
        matches = re.findall(pattern, a, re.DOTALL)
        args = [m[0] if m[0] else m[1] for m in matches]
        if len(args) >= 2:
            caminho = args[0]
            conteudo = args[1]
            modo = args[2] if len(args) > 2 else "w"
            criar_ou_editar_arquivo(caminho, conteudo, modo)
            return True
        parts = a.split(",")
        if len(parts) >= 2:
            caminho = parts[0].strip(' "\'')
            conteudo = parts[1].strip(' "\'')
            modo = parts[2].strip(' "\'') if len(parts) > 2 else "w"
            criar_ou_editar_arquivo(caminho, conteudo, modo)
            return True
        return True

    if c == "MOVER" and callable(mover_arquivo):
        parts = a.split(",")
        if len(parts) >= 2:
            mover_arquivo(parts[0].strip(' "\''), parts[1].strip(' "\''))
        return True

    if c == "RENOMEAR" and callable(renomear_arquivo):
        parts = a.split(",")
        if len(parts) >= 2:
            renomear_arquivo(parts[0].strip(' "\''), parts[1].strip(' "\''))
        return True

    if c == "DELETAR" and callable(deletar_item):
        deletar_item(a.strip(' "\''))
        return True

    if c == "BUSCAR_ARQUIVO" and callable(buscar_arquivo_no_pc):
        buscar_arquivo_no_pc(a.strip(' "\''))
        return True

    if c == "ORGANIZE_WORKSPACE" and callable(organizar_janelas_robusto):
        try:
            match = re.search(r"ORGANIZE_WORKSPACE\((.*?)\)", comando)
            if match:
                argumentos = match.group(1)
                apps = [app.strip(" '\"") for app in argumentos.split(',')]
                app1 = apps[0] if len(apps) > 0 else "vscode"
                app2 = apps[1] if len(apps) > 1 else "whatsapp"
                organizar_janelas_robusto(app1, app2)
            else:
                organizar_janelas_robusto("vscode", "whatsapp")
        except Exception as e:
            print(f"❌ Falha ao entender os apps para organizar: {e}")
            organizar_janelas_robusto("vscode", "whatsapp")
        return True

    return False
