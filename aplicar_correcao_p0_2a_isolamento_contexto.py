#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# P0.2A — isolamento tipado de contexto operacional da Laylay.
# Não altera confirmação pendente; isso fica para P0.2B.
# Faz backup, aplica apenas em fontes compatíveis, reabre o conteúdo gravado,
# valida AST/testes e restaura tudo se houver falha.

from __future__ import annotations

import argparse
import ast
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

MARCADOR = "P0_ISOLAMENTO_CONTEXTO_20260814"
REGISTRO_REL = Path("mente_laylay/memoria_mental/registro_semantico.py")
SELETOR_REL = Path("mente_laylay/cognicao/seletor_contexto.py")
CONTEXTO_REL = Path("mente_laylay/memoria_mental/contexto_imediato.py")
TESTE_REL = Path("tests/test_p0_isolamento_contexto.py")

NEW_REF = '# P0_ISOLAMENTO_CONTEXTO_20260814\ndef resolver_referencia_pontuada(\n    texto: str,\n    *,\n    entidades_recentes: Dict[str, Any] | None,\n    registro: Dict[str, Any] | None = None,\n    operacao: str = "",\n    agora: float | None = None,\n) -> Dict[str, Any]:\n    """P0.2A: domínio explícito restringe candidatos antes da recência."""\n    instante = float(agora if agora is not None else time.time())\n    recentes = {\n        str(chave): dict(item)\n        for chave, item in dict(entidades_recentes or {}).items()\n        if isinstance(item, dict) and str(item.get("nome") or "").strip()\n    }\n    estado = _registro(registro)\n    for entidade_id, item in dict(estado.get("entidades") or {}).items():\n        if not isinstance(item, dict):\n            continue\n        tipo = str(item.get("tipo") or "referencia_nomeada")\n        nome_item = str(item.get("nome") or "")\n        if any(\n            _normalizar(recente.get("nome")) == _normalizar(nome_item)\n            for recente in recentes.values()\n        ):\n            continue\n        chave = tipo if tipo not in recentes else f"{tipo}:{entidade_id}"\n        recentes.setdefault(chave, {\n            "tipo": tipo,\n            "nome": nome_item,\n            "origem": "registro_semantico",\n            "ts": float(item.get("ultima_mencao_ts") or 0.0),\n            "entidade_id": entidade_id,\n        })\n\n    t = _normalizar(texto)\n    op = _normalizar(operacao)\n    dominio = ""\n    if op.startswith("playlist") or op == "musica_do_referente":\n        dominio = "musica"\n    elif op == "iot":\n        dominio = "iot"\n    elif op == "arquivo":\n        dominio = "arquivo"\n    elif re.search(r"\\b(?:musica|som|faixa|cancao|playlist)\\b", t):\n        dominio = "musica"\n    elif re.search(r"\\b(?:luz|lampada|ventilador|tomada|dispositivo|aparelho)\\b", t):\n        dominio = "iot"\n    elif re.search(\n        r"\\b(?:arquivo|pasta|documento|diretorio|markdown|extensao|formato)\\b|"\n        r"\\.(?:txt|md)\\b", t,\n    ):\n        dominio = "arquivo"\n    elif re.search(r"\\b(?:aba|guia|site|pagina)\\b", t):\n        dominio = "site"\n    elif re.search(\n        r"\\b(?:app|aplicativo|programa|janela|opera|chrome|steam|vscode|"\n        r"firefox|brave|calculadora)\\b", t,\n    ):\n        dominio = "app"\n\n    tipos = {\n        "musica": {\n            "artista", "cantor", "cantora", "banda", "referencia_nomeada",\n            "musica", "playlist", "midia",\n        },\n        "iot": {"iot", "dispositivo"},\n        "arquivo": {"arquivo", "pasta"},\n        "app": {"app", "janela"},\n        "site": {"site", "janela"},\n    }\n    permitidos = tipos.get(dominio, set())\n    ativo_id = str(estado.get("entidade_ativa_id") or "")\n    candidatos = []\n\n    for chave, entidade in recentes.items():\n        tipo = str(entidade.get("tipo") or chave).casefold()\n        idade = max(0.0, instante - float(entidade.get("ts") or 0.0))\n        ttl = float(_TTL_TIPO.get(tipo, 900.0))\n        if idade > ttl:\n            continue\n\n        compativel = not dominio or tipo in permitidos\n        score = 0.15 + (0.35 * math.exp(-3.0 * idade / max(ttl, 1.0)))\n        origem = str(entidade.get("origem") or "")\n        if origem == "nome_explicito":\n            score += 0.30\n        elif origem == "registro_semantico":\n            score += 0.12\n        if ativo_id and str(entidade.get("entidade_id") or "") == ativo_id:\n            score += 0.25\n\n        entidade_ativa = dict((estado.get("entidades") or {}).get(ativo_id) or {})\n        if (\n            ativo_id\n            and _normalizar(entidade.get("nome"))\n            == _normalizar(entidade_ativa.get("nome"))\n        ):\n            score += 0.25\n\n        if dominio == "musica":\n            score += 0.30 if tipo in tipos["musica"] else -0.25\n        elif dominio == "iot":\n            score += 0.35 if tipo in tipos["iot"] else -0.25\n        elif dominio == "arquivo":\n            score += 0.35 if tipo in tipos["arquivo"] else -0.25\n        elif dominio == "site":\n            score += 0.30 if tipo in tipos["site"] else -0.25\n        elif dominio == "app":\n            score += 0.30 if tipo in tipos["app"] else -0.20\n        elif re.search(r"\\b(?:abre|fecha|foco|maximiza)\\b", t):\n            score += 0.25 if tipo in tipos["app"] else -0.15\n\n        if dominio and not compativel:\n            score = 0.0\n        score = max(0.0, min(1.0, score))\n        candidatos.append({\n            "chave": chave,\n            "nome": str(entidade.get("nome") or ""),\n            "tipo": tipo,\n            "pontuacao": round(score, 3),\n            "idade_s": round(idade, 1),\n            "origem": origem,\n            "dominio_restrito": dominio,\n            "compativel_dominio": compativel,\n            "entidade": dict(entidade),\n        })\n\n    candidatos.sort(\n        key=lambda item: float(item.get("pontuacao") or 0.0),\n        reverse=True,\n    )\n    elegiveis = [x for x in candidatos if x.get("compativel_dominio") is not False]\n    melhor = (\n        elegiveis[0]\n        if elegiveis and float(elegiveis[0].get("pontuacao") or 0.0) >= 0.45\n        else {}\n    )\n    return {\n        "resolvida": dict(melhor.get("entidade") or {}),\n        "chave": str(melhor.get("chave") or ""),\n        "pontuacao": float(melhor.get("pontuacao") or 0.0),\n        "dominio_restrito": dominio,\n        "candidatos": [\n            {k: v for k, v in item.items() if k != "entidade"}\n            for item in candidatos[:5]\n        ],\n    }\n'
HELPERS = '# P0_ISOLAMENTO_CONTEXTO_20260814\n_DOMINIOS_INTENT_CONTEXTO = {\n    "app": {\n        "APP_OPEN", "CLOSE_APP", "FECHAR_PROGRAMA", "MAXIMIZE_WINDOW",\n        "ORGANIZAR_DESKTOP", "LIST_WINDOWS",\n    },\n    "site": {\n        "OPEN_URL", "CLOSE_TAB", "SITE_ENTER", "SEARCH", "LIST_TABS",\n        "SWITCH_PREVIOUS_TAB", "CLOSE_IDLE_TABS", "RESUMIR_PAGINA",\n    },\n    "musica": {\n        "MUSIC_SEARCH", "MEDIA_CONTROL", "MUSIC_STATUS",\n        "PLAYLIST_CREATE", "PLAYLIST_DELETE", "PLAYLIST_ADD", "PLAYLIST_LIST",\n        "PLAYLIST_PLAY", "PLAYLIST_MOVE", "TOCAR_PLAYLIST",\n        "TOCAR_PLAYLIST_SHUFFLE", "LISTAR_PLAYLISTS",\n        "LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_PLAY", "LAYLAY_PLAYLIST_COPY",\n    },\n    "iot": {"IOT_CONTROL", "IOT_STATUS", "IOT_LIST"},\n    "arquivo": {\n        "CREATE_FOLDER", "CREATE_FILE", "DELETE_ITEM", "MOVE_ITEM",\n        "FILE_TRANSACTION", "FILE_SEARCH", "FILE_READ", "FILE_OPEN_RESULT",\n        "RESTORE_DELETED_ITEM", "CONFIRM_DELETE_ITEM", "CANCEL_DELETE_ITEM",\n    },\n}\n\n\ndef _normalizar_dominio_referencia(dominio: str) -> str:\n    valor = str(dominio or "").strip().casefold()\n    return {\n        "arquivos": "arquivo", "arquivo": "arquivo", "pasta": "arquivo",\n        "musica": "musica", "música": "musica", "playlist": "musica",\n        "midia": "musica", "playlist_laylay": "musica",\n        "iot": "iot", "dispositivo": "iot",\n        "janela": "app", "app": "app", "site": "site", "navegador": "site",\n    }.get(valor, valor)\n\n\ndef _dominio_explicito_referencia(texto: str) -> str:\n    t = str(texto or "").casefold()\n    if re.search(r"\\b(?:musica|música|som|faixa|canção|cancao|playlist)\\b", t):\n        return "musica"\n    if re.search(r"\\b(?:luz|lampada|lâmpada|ventilador|tomada|dispositivo|aparelho)\\b", t):\n        return "iot"\n    if re.search(\n        r"\\b(?:arquivo|pasta|documento|diretorio|diretório|markdown|"\n        r"extensao|extensão|formato)\\b|\\.(?:txt|md)\\b", t,\n    ):\n        return "arquivo"\n    if re.search(r"\\b(?:aba|guia|site|pagina|página)\\b", t):\n        return "site"\n    if re.search(\n        r"\\b(?:app|aplicativo|programa|janela|opera|ópera|chrome|steam|"\n        r"vscode|firefox|brave|calculadora)\\b", t,\n    ):\n        return "app"\n    return ""\n\n\ndef _dominio_ativo_referencia(\n    estado: Dict[str, Any] | None,\n    *,\n    ttl_s: float = 300.0,\n) -> str:\n    mente = dict(estado or {})\n    continuidade = dict(mente.get("continuidade_geral") or {})\n    bruto = str(continuidade.get("dominio_ativo") or "").strip()\n    if not bruto:\n        return ""\n    registro = dict(dict(continuidade.get("dominios") or {}).get(bruto) or {})\n    if not registro or registro.get("ativa", True) is False:\n        return ""\n    agora = time.time()\n    try:\n        ts = float(registro.get("ts") or 0.0)\n        expira_em = float(registro.get("expira_em") or 0.0)\n    except (TypeError, ValueError):\n        return ""\n    if not ts or agora - ts > ttl_s or (expira_em and agora >= expira_em):\n        return ""\n    return _normalizar_dominio_referencia(bruto)\n\n\ndef _texto_referencia_curta_operacional(texto: str) -> bool:\n    t = str(texto or "").casefold().strip()\n    pronome = bool(re.search(\n        r"\\b(?:ele|ela|isso|esse|essa|este|esta|dele|dela|desse|dessa)\\b", t\n    ))\n    operacao = bool(re.search(\n        r"\\b(?:abre|abra|abrir|fecha|feche|fechar|encerra|encerrar|"\n        r"maximiza|maximizar|coloca|coloque|deixa|muda|ajusta|liga|"\n        r"desliga|apaga|apagar|remove|remover|exclui|excluir|deleta|"\n        r"deletar|move|mover|renomeia|renomear|toca|toque|pausa|"\n        r"continue|continua|retoma|volta)\\b", t\n    ))\n    return pronome and operacao\n\n\ndef _dominio_restrito_referencia(\n    texto: str,\n    estado: Dict[str, Any] | None,\n    *,\n    ttl_s: float = 300.0,\n) -> str:\n    explicito = _dominio_explicito_referencia(texto)\n    if explicito:\n        return explicito\n    if not _texto_referencia_curta_operacional(texto):\n        return ""\n    return _dominio_ativo_referencia(estado, ttl_s=ttl_s)\n\n\ndef _dominio_intent_contextual(intent: str) -> str:\n    nome = str(intent or "").upper().strip()\n    for dominio, intents in _DOMINIOS_INTENT_CONTEXTO.items():\n        if nome in intents:\n            return dominio\n    return ""\n\n\ndef _resultado_compativel_com_dominio(\n    resultado: Dict[str, Any] | None,\n    dominio: str,\n) -> bool:\n    if not isinstance(resultado, dict):\n        return False\n    restrito = _normalizar_dominio_referencia(dominio)\n    if not restrito:\n        return True\n    return _dominio_intent_contextual(str(resultado.get("intent") or "")) == restrito\n'
NEW_CONTEXTUAL = 'def resolver_comando_contextual(\n    texto: str,\n    candidatos: Iterable[Tuple[str, Callable[[str], Dict[str, Any] | None]]],\n    *,\n    dominio_restrito: str = "",\n) -> Dict[str, Any] | None:\n    """Filtra resultados contextuais por domínio antes de materializar ação."""\n    for rota, resolver in candidatos:\n        rota_txt = str(rota or "GERAL").upper()\n        try:\n            resultado = resolver(texto)\n        except Exception as erro:\n            print(f"⚠️ [CONTEXTO-{rota_txt}] falha ao resolver: {erro}")\n            continue\n        if not isinstance(resultado, dict) or not str(resultado.get("intent") or "").strip():\n            continue\n        if dominio_restrito and not _resultado_compativel_com_dominio(\n            resultado, dominio_restrito\n        ):\n            print(\n                "🛡️ [P0:CONTEXTO] intenção contextual descartada por domínio | "\n                f"rota={rota_txt} dominio={dominio_restrito} "\n                f"intent={resultado.get(\'intent\')}"\n            )\n            continue\n        saida = dict(resultado)\n        saida["_rota_contextual"] = rota_txt\n        if dominio_restrito:\n            saida["_dominio_contextual"] = _normalizar_dominio_referencia(\n                dominio_restrito\n            )\n        return saida\n    return None\n'
NEW_RUNTIME_METHOD = 'def resolver(self, texto: str) -> Dict[str, Any] | None:\n    ns = self._namespace()\n    t = ns["_normalizar_texto_com_apelidos"](texto)\n    if re.search(\n        r"\\b(?:daqui|em)\\s+\\d{1,4}\\s*(?:segundos?|seg|minutos?|min|horas?)\\b", t\n    ) or re.search(r"\\b(?:as|às)\\s+\\d{1,2}:\\d{2}\\b", t):\n        return None\n\n    estrutura = ns["_estrutura_arquivo_recente"](900.0)\n    mente = self._estado().mental\n    dominio_restrito = _dominio_restrito_referencia(t, mente, ttl_s=300.0)\n    referencia_operacional = _texto_referencia_curta_operacional(t)\n\n    if referencia_operacional and not dominio_restrito:\n        print(\n            "🛡️ [P0:CONTEXTO] referência operacional ambígua; "\n            "nenhuma mutação contextual foi materializada."\n        )\n        return None\n\n    verbo_mutacao_arquivo = bool(re.search(\n        r"\\b(apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir|"\n        r"cria|criar|move|mover|renomeia|renomear|muda|mudar|troca|trocar|"\n        r"altera|alterar)\\b", t\n    ))\n    verbo_abertura = bool(re.search(r"\\b(?:abre|abra|abrir|mostra|mostre)\\b", t))\n    verbo_fechamento = bool(re.search(\n        r"\\b(?:fecha|feche|fechar|encerra|encerre|encerrar)\\b", t\n    ))\n    ultima_intencao = str(\n        mente.get("ultima_acao_intent") or mente.get("ultima_intencao") or ""\n    ).upper()\n    ultima_habilidade = str(mente.get("ultima_habilidade") or "").lower()\n    arquivo_mais_recente = bool(\n        estrutura\n        and (\n            ultima_intencao in {\n                "CREATE_FOLDER", "CREATE_FILE", "DELETE_ITEM", "MOVE_ITEM",\n                "FILE_TRANSACTION", "FILE_READ", "FILE_OPEN_RESULT", "FILE_SEARCH",\n            }\n            or ultima_habilidade in {"arquivo", "arquivos"}\n        )\n    )\n    sinal_arquivo_explicito = bool(re.search(\n        r"\\b(pasta|arquivo|documento|txt|md|markdown|extensao|extensão|formato|"\n        r"diretorio|diretório)\\b|\\.(?:txt|md)\\b", t\n    ))\n    contexto_arquivo = bool(\n        sinal_arquivo_explicito\n        or dominio_restrito == "arquivo"\n        or (\n            not referencia_operacional\n            and (\n                ultima_habilidade in {"arquivo", "arquivos"}\n                or ultima_intencao in {\n                    "CREATE_FOLDER", "CREATE_FILE", "DELETE_ITEM",\n                    "MOVE_ITEM", "FILE_TRANSACTION",\n                }\n            )\n        )\n    )\n\n    if dominio_restrito == "musica":\n        resolvedores = [\n            ("MIDIA", self.resolver_midia),\n            ("GERAL", self.resolver_acao_geral),\n            ("SEMANTICA", self.resolver_semantico),\n        ]\n    elif dominio_restrito == "iot":\n        resolvedores = [\n            ("IOT", self.resolver_iot),\n            ("GERAL", self.resolver_acao_geral),\n            ("SEMANTICA", self.resolver_semantico),\n        ]\n    elif dominio_restrito == "arquivo":\n        resolvedores = [\n            ("ARQUIVO", self.resolver_arquivo),\n            ("GERAL", self.resolver_acao_geral),\n            ("SEMANTICA", self.resolver_semantico),\n        ]\n    elif dominio_restrito in {"app", "site"}:\n        resolvedores = [\n            ("JANELA", self.resolver_janela),\n            ("GERAL", self.resolver_acao_geral),\n            ("SEMANTICA", self.resolver_semantico),\n        ]\n    elif verbo_fechamento and arquivo_mais_recente:\n        resolvedores = [\n            ("GERAL", self.resolver_acao_geral),\n            ("ARQUIVO", self.resolver_arquivo),\n            ("SEMANTICA", self.resolver_semantico),\n            ("JANELA", self.resolver_janela),\n            ("IOT", self.resolver_iot),\n            ("MIDIA", self.resolver_midia),\n        ]\n    elif verbo_abertura and arquivo_mais_recente:\n        resolvedores = [\n            ("ARQUIVO", self.resolver_arquivo),\n            ("SEMANTICA", self.resolver_semantico),\n            ("IOT", self.resolver_iot),\n            ("JANELA", self.resolver_janela),\n            ("MIDIA", self.resolver_midia),\n            ("GERAL", self.resolver_acao_geral),\n        ]\n    elif verbo_mutacao_arquivo and contexto_arquivo:\n        resolvedores = [\n            ("SEMANTICA", self.resolver_semantico),\n            ("ARQUIVO", self.resolver_arquivo),\n            ("IOT", self.resolver_iot),\n            ("JANELA", self.resolver_janela),\n            ("MIDIA", self.resolver_midia),\n            ("GERAL", self.resolver_acao_geral),\n        ]\n    else:\n        resolvedores = [\n            ("IOT", self.resolver_iot),\n            ("SEMANTICA", self.resolver_semantico),\n            ("JANELA", self.resolver_janela),\n            ("MIDIA", self.resolver_midia),\n            ("ARQUIVO", self.resolver_arquivo),\n            ("GERAL", self.resolver_acao_geral),\n        ]\n\n    return resolver_comando_contextual(\n        texto, resolvedores, dominio_restrito=dominio_restrito\n    )\n'
TESTS = 'from __future__ import annotations\n\nimport time\n\nfrom mente_laylay.cognicao.seletor_contexto import selecionar_contexto_turno\nfrom mente_laylay.memoria_mental.contexto_imediato import (\n    ContextoImediatoRuntime,\n    _dominio_restrito_referencia,\n    _resultado_compativel_com_dominio,\n    referencia_contextual_imediata,\n    resolver_comando_acao_geral_contextual,\n)\nfrom mente_laylay.memoria_mental.registro_semantico import resolver_referencia_pontuada\n\n\ndef _continuidade(dominio, intent, alvo, params=None):\n    agora = time.time()\n    return {\n        "versao": 1,\n        "dominio_ativo": dominio,\n        "dominios": {\n            dominio: {\n                "dominio": dominio, "intent": intent, "alvo": alvo,\n                "params": dict(params or {}), "status": "executado",\n                "ativa": True, "ts": agora, "expira_em": agora + 600.0,\n            }\n        },\n        "historico": [], "ts": agora,\n    }\n\n\ndef test_playlist_explicita_elimina_arquivo_antigo():\n    agora = time.time()\n    r = resolver_referencia_pontuada(\n        "Mostra a playlist caos sonora e depois apaga ela.",\n        entidades_recentes={\n            "arquivo": {\n                "tipo": "arquivo", "nome": "correcao.txt",\n                "origem": "nome_explicito", "ts": agora - 1.0,\n            },\n            "playlist": {\n                "tipo": "playlist", "nome": "caos sonora",\n                "origem": "foco_mental", "ts": agora - 8.0,\n            },\n        },\n        registro={}, agora=agora,\n    )\n    assert r["dominio_restrito"] == "musica"\n    assert r["resolvida"]["tipo"] == "playlist"\n    arquivo = next(x for x in r["candidatos"] if x["tipo"] == "arquivo")\n    assert arquivo["compativel_dominio"] is False\n    assert arquivo["pontuacao"] == 0.0\n\n\ndef test_apaga_pronome_mantem_playlist_ativa():\n    estado = {\n        "ts": time.time(),\n        "continuidade_geral": _continuidade(\n            "musica", "PLAYLIST_LIST", "caos sonora",\n            {"nome_playlist": "caos sonora"},\n        ),\n        "ultima_acao_intent": "PLAYLIST_LIST",\n        "ultima_acao_params": {"nome_playlist": "caos sonora"},\n        "ultima_acao_promovivel": True,\n    }\n    ref = referencia_contextual_imediata(\n        mente_integrada_estado=estado, foco_vivo={},\n        texto_atual="apaga ela", ultima_playlist="caos sonora",\n        normalizar_texto=lambda x: str(x).casefold(), ttl_s=300.0,\n    )\n    assert ref["tipo"] == "playlist"\n    assert ref["alvo"] == "caos sonora"\n\n\ndef test_playlist_contextual_materializa_playlist_delete():\n    r = resolver_comando_acao_geral_contextual(\n        "apaga ela",\n        {\n            "tipo": "playlist", "alvo": "caos sonora",\n            "intencao": "PLAYLIST_LIST",\n            "params": {"nome_playlist": "caos sonora"},\n        },\n        ultima_playlist="caos sonora",\n    )\n    assert r["intent"] == "PLAYLIST_DELETE"\n    assert r["params"]["nome_playlist"] == "caos sonora"\n\n\ndef test_dominio_musica_rejeita_delete_item():\n    assert not _resultado_compativel_com_dominio(\n        {"intent": "DELETE_ITEM", "params": {"alvo": "correcao.txt"}}, "musica"\n    )\n    assert _resultado_compativel_com_dominio(\n        {"intent": "PLAYLIST_DELETE", "params": {"nome_playlist": "caos sonora"}},\n        "musica",\n    )\n\n\ndef test_pronome_mutante_usa_dominio_ativo():\n    estado = {"continuidade_geral": _continuidade(\n        "musica", "PLAYLIST_LIST", "caos sonora"\n    )}\n    assert _dominio_restrito_referencia("apaga ela", estado) == "musica"\n\n\ndef test_pronome_mutante_sem_dominio_falha_fechado():\n    estado = {"continuidade_geral": {\n        "dominio_ativo": "", "dominios": {}, "historico": [], "ts": time.time()\n    }}\n    assert _dominio_restrito_referencia("apaga ela", estado) == ""\n\n\ndef test_seletor_pronome_rejeita_foco_de_outro_dominio():\n    agora = time.time()\n    mente = {\n        "continuidade_geral": _continuidade(\n            "musica", "PLAYLIST_LIST", "caos sonora"\n        ),\n        "focos_por_dominio": {\n            "arquivo": {"alvo": "correcao.txt", "topico": "correcao.txt", "ts": agora - 1},\n            "musica": {"alvo": "caos sonora", "topico": "caos sonora", "ts": agora - 5},\n        },\n        "continuidade_fala_ts": agora,\n    }\n    r = selecionar_contexto_turno(\n        "apaga ela",\n        turno={"modalidade": "comando", "texto": "apaga ela", "texto_operacional": "apaga ela"},\n        mente=mente, contexto_perceptivo={},\n    )\n    assert any(x["dominio"] == "musica" for x in r["selecionados"])\n    assert not any(x["dominio"] == "arquivo" for x in r["selecionados"])\n\n\nclass EstadoFalso:\n    def __init__(self, mental, ultima_playlist=""):\n        self.mental = mental\n        self._ultima_playlist = ultima_playlist\n\n    def musica_get(self, chave):\n        return self._ultima_playlist if chave == "ultima_playlist" else ""\n\n\nclass IoTAgressivo:\n    def detectar(self, _texto, _mente):\n        return {"intent": "IOT_CONTROL", "params": {"alvo": "lampada_quarto", "acao": "off"}}\n\n\ndef _runtime(mental, estrutura, ultima_playlist=""):\n    estado = EstadoFalso(mental, ultima_playlist)\n    servicos = {\n        "_normalizar_texto_com_apelidos": lambda x: str(x).casefold().strip(),\n        "_alvo_corrigido_atual": lambda: "",\n        "_registrar_alvo_corrigido": lambda _x: None,\n        "falar_com_lipsync": lambda *_a, **_k: None,\n        "_contexto_musical_ativo": lambda: True,\n        "_estrutura_arquivo_recente": lambda _ttl: dict(estrutura or {}),\n        "_foco_vivo_atual": lambda **_k: {},\n        "enviar_mensagem": None,\n    }\n    return ContextoImediatoRuntime(\n        estado_runtime_getter=lambda: estado,\n        servicos_iniciais=servicos, iot=IoTAgressivo(),\n    )\n\n\ndef test_runtime_playlist_nao_cai_em_arquivo_nem_iot():\n    mental = {\n        "ts": time.time(), "ultima_acao_intent": "PLAYLIST_LIST",\n        "ultima_intencao": "PLAYLIST_LIST", "ultima_habilidade": "playlist",\n        "ultima_acao_params": {"nome_playlist": "caos sonora"},\n        "ultima_acao_promovivel": True,\n        "continuidade_geral": _continuidade(\n            "musica", "PLAYLIST_LIST", "caos sonora",\n            {"nome_playlist": "caos sonora"},\n        ),\n    }\n    r = _runtime(\n        mental,\n        {"tipo": "arquivo", "caminho": r"C:\\temp\\correcao.txt", "arquivo_nome": "correcao.txt"},\n        "caos sonora",\n    ).resolver("apaga ela")\n    assert r["intent"] == "PLAYLIST_DELETE"\n    assert r["params"]["nome_playlist"] == "caos sonora"\n\n\ndef test_runtime_ambiguo_com_arquivo_antigo_nao_muta():\n    mental = {\n        "ts": time.time(), "ultima_acao_intent": "", "ultima_intencao": "",\n        "ultima_habilidade": "", "ultima_acao_params": {},\n        "continuidade_geral": {\n            "dominio_ativo": "", "dominios": {}, "historico": [], "ts": time.time()\n        },\n    }\n    r = _runtime(\n        mental,\n        {"tipo": "arquivo", "caminho": r"C:\\temp\\correcao.txt", "arquivo_nome": "correcao.txt"},\n    ).resolver("apaga ela")\n    assert r is None\n\n\ndef test_app_valido_continua_resolvendo_fecha_ele():\n    mental = {\n        "ts": time.time(), "ultima_acao_intent": "APP_OPEN",\n        "ultima_intencao": "APP_OPEN", "ultima_habilidade": "janela",\n        "ultima_acao_params": {"nome_app": "opera"},\n        "ultima_acao_promovivel": True, "ultimo_app_janela": "opera",\n        "ultima_acao_contrato": {\n            "intent": "APP_OPEN", "alvo": "opera",\n            "executou": True, "confirmado": True,\n        },\n        "continuidade_geral": _continuidade(\n            "app", "APP_OPEN", "opera", {"nome_app": "opera"}\n        ),\n    }\n    r = _runtime(mental, {}).resolver("fecha ele")\n    assert r["intent"] == "CLOSE_APP"\n    assert r["params"]["nome_app"] == "opera"\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def achar_raiz(inicio: Path) -> Path:
    inicio = inicio.resolve()
    for pasta in (inicio, *inicio.parents):
        if (
            (pasta / "laylay.py").is_file()
            and (pasta / REGISTRO_REL).is_file()
            and (pasta / SELETOR_REL).is_file()
            and (pasta / CONTEXTO_REL).is_file()
        ):
            return pasta
    raise FileNotFoundError(
        "Não encontrei a raiz da Laylay. Coloque o patcher no projeto ou use --root."
    )


def raiz_padrao() -> Path:
    erros = []
    for inicio in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        try:
            return achar_raiz(inicio)
        except FileNotFoundError as erro:
            erros.append(erro)
    raise erros[-1] if erros else FileNotFoundError("Raiz não encontrada.")


def substituir_funcao_ast(
    fonte: str,
    nome: str,
    bloco: str,
    *,
    classe: str | None = None,
) -> str:
    arvore = ast.parse(fonte)
    if classe:
        classes = [
            n for n in arvore.body
            if isinstance(n, ast.ClassDef) and n.name == classe
        ]
        if len(classes) != 1:
            raise RuntimeError(f"Classe {classe!r} não encontrada de forma única.")
        candidatos = [
            n for n in classes[0].body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == nome
        ]
    else:
        candidatos = [
            n for n in arvore.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == nome
        ]
    if len(candidatos) != 1:
        alvo = f"{classe}.{nome}" if classe else nome
        raise RuntimeError(f"Função {alvo!r} não encontrada de forma única.")
    no = candidatos[0]
    if no.end_lineno is None:
        raise RuntimeError("AST sem end_lineno.")
    linhas = fonte.splitlines(keepends=True)
    novo = bloco.strip("\n") + "\n"
    if classe:
        novo = "\n".join(
            ("    " + linha if linha else "")
            for linha in novo.splitlines()
        ) + "\n"
    return "".join(linhas[: no.lineno - 1]) + novo + "".join(linhas[no.end_lineno :])


def inserir_apos_funcao(fonte: str, nome: str, bloco: str) -> str:
    arvore = ast.parse(fonte)
    candidatos = [
        n for n in arvore.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nome
    ]
    if len(candidatos) != 1 or candidatos[0].end_lineno is None:
        raise RuntimeError(f"Âncora {nome!r} não encontrada.")
    linhas = fonte.splitlines(keepends=True)
    fim = candidatos[0].end_lineno
    return (
        "".join(linhas[:fim])
        + "\n\n"
        + bloco.strip("\n")
        + "\n\n"
        + "".join(linhas[fim:])
    )


def patch_registro(fonte: str) -> str:
    if MARCADOR in fonte:
        return fonte
    if "def resolver_referencia_pontuada(" not in fonte:
        raise RuntimeError("resolver_referencia_pontuada ausente.")
    return substituir_funcao_ast(fonte, "resolver_referencia_pontuada", NEW_REF)


def patch_seletor(fonte: str) -> str:
    if MARCADOR in fonte:
        return fonte

    a1 = '''    novo_assunto = modalidade in {"conversa", "pergunta"} and not referencia and len(_tokens(texto)) >= 2
    associacoes = [
'''
    b1 = '''    novo_assunto = modalidade in {"conversa", "pergunta"} and not referencia and len(_tokens(texto)) >= 2

    # P0_ISOLAMENTO_CONTEXTO_20260814
    dominio_referencia = dominio_atual
    if referencia and dominio_atual == "conversa":
        continuidade = dict(mente.get("continuidade_geral") or {})
        ativo = str(continuidade.get("dominio_ativo") or "").strip().casefold()
        registro_ativo = dict(dict(continuidade.get("dominios") or {}).get(ativo) or {})
        try:
            idade_ativo = time.time() - float(registro_ativo.get("ts") or 0.0)
            expira_ativo = float(registro_ativo.get("expira_em") or 0.0)
        except (TypeError, ValueError):
            idade_ativo, expira_ativo = 999999.0, 0.0
        if (
            ativo
            and registro_ativo.get("ativa", True) is not False
            and idade_ativo <= 300.0
            and (not expira_ativo or time.time() < expira_ativo)
        ):
            dominio_referencia = {
                "arquivos": "arquivo",
                "playlist_laylay": "musica",
            }.get(ativo, ativo)

    associacoes = [
'''
    if a1 not in fonte:
        raise RuntimeError("Âncora de domínio do seletor mudou.")
    fonte = fonte.replace(a1, b1, 1)

    a2 = '        dominio_ok = dominio in {"conversa", dominio_atual} or dominio_atual == "conversa"\n'
    b2 = '''        if referencia:
            dominio_ok = (
                dominio == "conversa"
                or (dominio_referencia != "conversa" and dominio == dominio_referencia)
            )
        else:
            dominio_ok = (
                dominio in {"conversa", dominio_referencia}
                or dominio_referencia == "conversa"
            )
'''
    if a2 not in fonte:
        raise RuntimeError("Regra dominio_ok antiga não encontrada.")
    fonte = fonte.replace(a2, b2, 1)

    a_ref = '        if referencia and origem in {"ultima_fala", "pergunta_aberta", "promessa"}:\n            score += 0.22\n'
    b_ref = '        if referencia and dominio_ok and dominio != "conversa":\n            # O domínio ativo tipado é evidência positiva para a referência.\n            score += 0.12\n        if referencia and origem in {"ultima_fala", "pergunta_aberta", "promessa"}:\n            score += 0.22\n'
    if a_ref not in fonte:
        raise RuntimeError("Âncora de reforço de referência mudou.")
    fonte = fonte.replace(a_ref, b_ref, 1)

    a_penalidade = '        if modalidade == "comando" and dominio != dominio_atual and dominio != "conversa":\n            score -= 0.35\n'
    b_penalidade = '        if modalidade == "comando" and dominio != dominio_referencia and dominio != "conversa":\n            score -= 0.35\n'
    if a_penalidade not in fonte:
        raise RuntimeError("Âncora de penalidade de domínio mudou.")
    fonte = fonte.replace(a_penalidade, b_penalidade, 1)

    a3 = "        aceito = score >= limiar\n"
    b3 = "        aceito = score >= limiar and dominio_ok\n"
    if a3 not in fonte:
        raise RuntimeError("Regra aceito do seletor mudou.")
    return fonte.replace(a3, b3, 1)


def patch_contexto(fonte: str) -> str:
    if MARCADOR in fonte:
        return fonte

    fonte = inserir_apos_funcao(fonte, "_normalizar_com_callback", HELPERS)
    fonte = substituir_funcao_ast(
        fonte, "resolver_comando_contextual", NEW_CONTEXTUAL
    )
    fonte = substituir_funcao_ast(
        fonte,
        "resolver",
        NEW_RUNTIME_METHOD,
        classe="ContextoImediatoRuntime",
    )

    antigo_iot = '''        and re.search(
            r"\\b(ele|ela|isso|dispositivo|aparelho|tomada|ventilador|luz|lampada|lâmpada)\\b",
            texto_norm,
        )
'''
    novo_iot = '''        and re.search(
            r"\\b(dispositivo|aparelho|tomada|ventilador|luz|lampada|lâmpada)\\b",
            texto_norm,
        )
'''
    if antigo_iot not in fonte:
        raise RuntimeError("Âncora da inferência IoT ambígua mudou.")
    fonte = fonte.replace(antigo_iot, novo_iot, 1)

    ancora = '''    ultima_playlist = str(ultima_playlist or "").strip()

    if tipo_ref == "pessoas" and alvo_ref and re.fullmatch(
'''
    insercao = '''    ultima_playlist = str(ultima_playlist or "").strip()

    if (
        tipo_ref == "playlist"
        and alvo_ref
        and re.fullmatch(
            r"(?:apaga|apagar|deleta|deletar|remove|remover|exclui|excluir)\\s+"
            r"(?:ela|ele|isso|essa|esse|esta|este)[?.!]*",
            t,
            flags=re.IGNORECASE,
        )
    ):
        return {
            "intent": "PLAYLIST_DELETE",
            "params": {
                "nome_playlist": alvo_ref,
                "referencia_contextual": True,
            },
        }

    if tipo_ref == "pessoas" and alvo_ref and re.fullmatch(
'''
    if ancora not in fonte:
        raise RuntimeError("Âncora da ação geral contextual mudou.")
    return fonte.replace(ancora, insercao, 1)


def validar(registro: str, seletor: str, contexto: str, testes: str) -> None:
    for nome, fonte in (
        ("registro_semantico.py", registro),
        ("seletor_contexto.py", seletor),
        ("contexto_imediato.py", contexto),
        ("test_p0_isolamento_contexto.py", testes),
    ):
        try:
            ast.parse(fonte)
        except SyntaxError as erro:
            raise RuntimeError(f"Sintaxe inválida em {nome}: {erro}") from erro

    checks = {
        "registro": (
            MARCADOR, "compativel_dominio", "dominio_restrito", "score = 0.0",
        ),
        "seletor": (
            MARCADOR, "dominio_referencia",
            "aceito = score >= limiar and dominio_ok",
            'dominio != dominio_referencia',
            "score += 0.12",
        ),
        "contexto": (
            MARCADOR, "_dominio_restrito_referencia",
            "_resultado_compativel_com_dominio",
            '"intent": "PLAYLIST_DELETE"',
            "referência operacional ambígua",
            "dominio_restrito=dominio_restrito",
            r"\b(dispositivo|aparelho|tomada|ventilador|luz|lampada|lâmpada)\b",
        ),
    }
    fontes = {"registro": registro, "seletor": seletor, "contexto": contexto}
    for nome, itens in checks.items():
        faltando = [x for x in itens if x not in fontes[nome]]
        if faltando:
            raise RuntimeError(f"Validação {nome}: itens ausentes {faltando}")

    if (
        'dominio_ok = dominio in {"conversa", dominio_atual} '
        'or dominio_atual == "conversa"'
    ) in seletor:
        raise RuntimeError("Regra antiga de domínio do seletor sobreviveu.")


def copiar_backup(origem: Path, destino: Path) -> None:
    if origem.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, destino)


def restaurar(pares) -> None:
    for destino, backup, existia in pares:
        if existia and backup.exists():
            shutil.copy2(backup, destino)
        elif not existia and destino.exists():
            destino.unlink()


def executar_validacoes(raiz: Path, sem_testes: bool) -> None:
    arquivos = [REGISTRO_REL, SELETOR_REL, CONTEXTO_REL, TESTE_REL]
    subprocess.run(
        [sys.executable, "-m", "py_compile", *map(str, arquivos)],
        cwd=raiz,
        check=True,
    )
    if sem_testes:
        return
    try:
        import pytest  # noqa: F401
    except Exception:
        print("ℹ️ pytest indisponível; py_compile passou.")
        return

    suite = [str(TESTE_REL)]
    for opcional in (
        Path("tests/test_p0_autorizacao_modalidade.py"),
        Path("tests/test_p0_autopreservacao_executor.py"),
        Path("tests/test_regressoes_roteiro_118.py"),
    ):
        if (raiz / opcional).is_file():
            suite.append(str(opcional))

    subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *suite],
        cwd=raiz,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Aplica P0.2A da Laylay.")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--sem-testes", action="store_true")
    args = parser.parse_args()

    raiz = achar_raiz(args.root.expanduser()) if args.root else raiz_padrao()
    caminhos = {
        REGISTRO_REL: raiz / REGISTRO_REL,
        SELETOR_REL: raiz / SELETOR_REL,
        CONTEXTO_REL: raiz / CONTEXTO_REL,
        TESTE_REL: raiz / TESTE_REL,
    }
    originais = {
        rel: path.read_text(encoding="utf-8")
        for rel, path in caminhos.items()
        if rel != TESTE_REL
    }

    registro = patch_registro(originais[REGISTRO_REL])
    seletor = patch_seletor(originais[SELETOR_REL])
    contexto = patch_contexto(originais[CONTEXTO_REL])
    validar(registro, seletor, contexto, TESTS)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_raiz = raiz / "_backup_correcao_p0_contexto" / timestamp
    pares = []
    for rel, destino in caminhos.items():
        existia = destino.exists()
        backup = backup_raiz / rel
        copiar_backup(destino, backup)
        pares.append((destino, backup, existia))

    try:
        caminhos[REGISTRO_REL].write_text(registro, encoding="utf-8")
        caminhos[SELETOR_REL].write_text(seletor, encoding="utf-8")
        caminhos[CONTEXTO_REL].write_text(contexto, encoding="utf-8")
        caminhos[TESTE_REL].parent.mkdir(parents=True, exist_ok=True)
        caminhos[TESTE_REL].write_text(TESTS, encoding="utf-8")

        # Reabre exatamente o conteúdo gravado antes de qualquer teste.
        validar(
            caminhos[REGISTRO_REL].read_text(encoding="utf-8"),
            caminhos[SELETOR_REL].read_text(encoding="utf-8"),
            caminhos[CONTEXTO_REL].read_text(encoding="utf-8"),
            caminhos[TESTE_REL].read_text(encoding="utf-8"),
        )
        executar_validacoes(raiz, args.sem_testes)
    except Exception as erro:
        print(f"\nERRO: {type(erro).__name__}: {erro}")
        print("Restaurando estado anterior...")
        restaurar(pares)
        print("✓ Restauração concluída.")
        return 1

    print("\n✓ P0.2A aplicada com sucesso.")
    print(f"Backup: {backup_raiz}")
    for rel, path in caminhos.items():
        print(f"SHA {rel}: {sha256(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
