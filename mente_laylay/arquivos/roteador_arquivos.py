"""Roteamento de comandos de arquivos da Laylay."""

from __future__ import annotations

import ast
import re
from typing import Any, Mapping


def _get(ctx: Mapping[str, Any], key: str):
    return ctx.get(key)


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

