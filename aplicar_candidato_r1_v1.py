from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path.cwd()
POLITICA = ROOT / "mente_laylay" / "memoria_mental" / "politica_reexecucao.py"
COMPAT = ROOT / "mente_laylay" / "memoria_mental" / "compatibilidade_contexto.py"
CONT = ROOT / "mente_laylay" / "memoria_mental" / "continuidade_geral.py"
CTX = ROOT / "mente_laylay" / "memoria_mental" / "contexto_compartilhado.py"
BACKUP = ROOT / ".r1_v1_backup_pre_candidato"


def falhar(msg: str) -> None:
    raise SystemExit(f"\n❌ R1-V1 abortado: {msg}\n")


def ler(path: Path) -> str:
    if not path.is_file():
        falhar(f"arquivo não encontrado: {path}")
    return path.read_text(encoding="utf-8")


def trocar_unico(texto: str, antigo: str, novo: str, rotulo: str) -> str:
    qtd = texto.count(antigo)
    if qtd != 1:
        falhar(
            f"{rotulo}: esperado exatamente 1 trecho da baseline, encontrado {qtd}. "
            "Nenhuma alteração foi aplicada."
        )
    return texto.replace(antigo, novo, 1)


def gravar_atomico(path: Path, texto: str) -> None:
    tmp = path.with_suffix(path.suffix + ".r1v1.tmp")
    tmp.write_text(texto, encoding="utf-8")
    tmp.replace(path)


compat = ler(COMPAT)
cont = ler(CONT)
ctx = ler(CTX)

if POLITICA.exists():
    falhar(
        f"{POLITICA} já existe. O candidato parece já ter sido aplicado "
        "ou há um arquivo local que precisa ser revisado."
    )

# 1) Política neutra
politica = '''"""Política neutra de reexecução da Laylay.

A ocorrência concreta continua decidindo se uma tentativa é reexecutável.
Este módulo declara apenas compatibilidade semântica e params extras de retry.
"""

from __future__ import annotations


_INTENTS_REEXECUTAVEIS_PADRAO = frozenset({
    "APP_OPEN", "CLOSE_APP", "OPEN_URL", "CLOSE_TAB", "PLAYLIST_PLAY",
    "PLAYLIST_ADD", "MUSIC_SEARCH", "VOLUME", "MEDIA_CONTROL", "WEATHER",
    "EMAIL_READ", "EMAIL_SYNC", "NOTIFICATIONS", "BRIEFING_REPEAT",
    "SITE_ENTER", "LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_PLAY",
    "PLAYLIST_LIST", "IOT_CONTROL", "IOT_STATUS", "IOT_LIST",
    "INBOX_LIST", "ORGANIZAR_DESKTOP", "FILE_READ",
})

_INTENTS_POR_ACAO_SEMANTICA = {
    "LER": frozenset({"FILE_READ", "EMAIL_READ"}),
}

_PARAMS_EXTRAS_REEXECUCAO = {
    "EMAIL_READ": frozenset({"urgentes"}),
}


def intencao_reexecutavel_padrao(intent: str) -> bool:
    return str(intent or "").strip().upper() in _INTENTS_REEXECUTAVEIS_PADRAO


def intents_compativeis_repeticao(acao_semantica: str) -> frozenset[str]:
    return _INTENTS_POR_ACAO_SEMANTICA.get(
        str(acao_semantica or "").strip().upper(),
        frozenset(),
    )


def params_extras_reexecucao(intent: str) -> frozenset[str]:
    return _PARAMS_EXTRAS_REEXECUCAO.get(
        str(intent or "").strip().upper(),
        frozenset(),
    )
'''

# 2) compatibilidade_contexto.py
compat = trocar_unico(
    compat,
    """from mente_laylay.memoria_mental.continuidade_geral import (\n    selecionar_continuidade_reexecutavel,\n)\n""",
    """from mente_laylay.memoria_mental.continuidade_geral import (\n    selecionar_continuidade_reexecutavel,\n    selecionar_operacao_reexecutavel_compativel,\n)\nfrom mente_laylay.memoria_mental.politica_reexecucao import (\n    intents_compativeis_repeticao,\n)\n""",
    "compat/imports",
)

inicio = compat.index("def texto_pede_repeticao_curta(")
fim = compat.index("\n\ndef contexto_musical_ativo(", inicio)
novo_bloco_compat = '''_PADRAO_REPETICAO_CURTA = re.compile(
    r"(?:(?P<verbo>tenta|tente|faz|fa[cç]a|vai|leia|l[eê]|ler)\\s+)?"
    r"(?:de\\s+novo|novamente|outra\\s+vez|mais\\s+uma\\s+vez)|"
    r"tenta\\s+outra\\s+vez"
)


def classificar_repeticao_curta(texto: str, normalizar_texto_cb) -> Dict[str, str]:
    """Preserva a restrição lexical antes de selecionar a operação."""
    t = str(normalizar_texto_cb(str(texto or "")) or "").strip(" .,!?:;")
    if not t or len(t.split()) > 8:
        return {}
    achado = _PADRAO_REPETICAO_CURTA.fullmatch(t)
    if not achado:
        return {}

    verbo = str(achado.groupdict().get("verbo") or "").strip().casefold()
    if verbo in {"leia", "le", "lê", "ler"}:
        return {"tipo": "tipada", "acao_semantica": "LER", "verbo": verbo}
    return {"tipo": "generica", "acao_semantica": "", "verbo": verbo}


def texto_pede_repeticao_curta(texto: str, normalizar_texto_cb) -> bool:
    return bool(classificar_repeticao_curta(texto, normalizar_texto_cb))


def resolver_repeticao_ultima_acao(
    texto: str,
    estado_atual: Dict[str, Any] | None,
    normalizar_texto_cb,
):
    repeticao = classificar_repeticao_curta(texto, normalizar_texto_cb)
    if not repeticao:
        return None
    estado = dict(estado_atual or {})

    # ROOT R1: repetição tipada nunca cai no fluxo genérico.
    if repeticao.get("tipo") == "tipada":
        permitidos = intents_compativeis_repeticao(
            repeticao.get("acao_semantica", "")
        )
        if not permitidos:
            return None
        oficial_tipado = selecionar_operacao_reexecutavel_compativel(
            estado,
            intents_permitidos=permitidos,
            ttl_s=900.0,
        )
        if oficial_tipado:
            intent_tipado = str(oficial_tipado.get("intent") or "").strip().upper()
            params_tipados = oficial_tipado.get("params")
            if intent_tipado and isinstance(params_tipados, dict):
                return {"intent": intent_tipado, "params": dict(params_tipados)}

        # Compatibilidade V1: só a última ação atômica ainda disponível.
        intent_legado = str(estado.get("ultima_acao_intent") or "").strip().upper()
        params_legados = estado.get("ultima_acao_params")
        if (
            intent_legado in permitidos
            and bool(estado.get("ultima_acao_reexecutavel"))
            and isinstance(params_legados, dict)
        ):
            return {"intent": intent_legado, "params": dict(params_legados)}
        return None

    # Somente repetição genérica entra nos atalhos de mutação falha.
    intent_recente = str(estado.get("ultima_acao_intent") or "").strip().upper()
    status_recente = str(estado.get("ultima_acao_status") or "").strip().casefold()
    params_recentes = estado.get("ultima_acao_params")

    falhas_retentaveis_exclusao = {
        "falha_execucao", "nao_encontrado", "alvo_ambiguo",
        "referencia_nao_resolvida", "falhou",
    }
    if (
        intent_recente == "DELETE_ITEM"
        and status_recente in falhas_retentaveis_exclusao
        and estado.get("ultima_acao_ok") is not True
        and estado.get("ultima_acao_confirmada") is not True
        and isinstance(params_recentes, dict)
        and str(params_recentes.get("alvo") or "").strip()
    ):
        return {"intent": "DELETE_ITEM", "params": dict(params_recentes)}

    falhas_retentaveis_transacao = {
        "falha_execucao", "origem_nao_encontrada", "destino_nao_encontrado",
        "destino_bloqueado", "validacao_falhou", "falhou",
    }
    if (
        intent_recente == "FILE_TRANSACTION"
        and status_recente in falhas_retentaveis_transacao
        and estado.get("ultima_acao_ok") is not True
        and estado.get("ultima_acao_confirmada") is not True
        and isinstance(params_recentes, dict)
        and str(params_recentes.get("operacao") or "").strip().casefold()
        in {"mover", "renomear"}
        and str(params_recentes.get("origem") or "").strip()
        and str(params_recentes.get("destino") or "").strip()
    ):
        return {"intent": "FILE_TRANSACTION", "params": dict(params_recentes)}

    oficial = selecionar_continuidade_reexecutavel(
        estado,
        classe="operacional",
        ttl_s=900.0,
    )
    if oficial:
        if not bool(oficial.get("reexecutavel")):
            return None
        intent = str(oficial.get("intent") or "").strip().upper()
        params = oficial.get("params")
    else:
        if not bool(estado.get("ultima_acao_reexecutavel")):
            return None
        intent = str(estado.get("ultima_acao_intent") or "").strip().upper()
        params = estado.get("ultima_acao_params")
    if not intent or not isinstance(params, dict):
        return None
    return {"intent": intent, "params": dict(params)}
'''
compat = compat[:inicio] + novo_bloco_compat + compat[fim:]

# 3) continuidade_geral.py
cont = trocar_unico(
    cont,
    """from mente_laylay.cognicao.referencias_linguagem import (\n    extrair_indice_fechamento_ordinal_aba,\n)\n\n\nVERSAO_CONTINUIDADE_GERAL = 1\n""",
    """from mente_laylay.cognicao.referencias_linguagem import (\n    extrair_indice_fechamento_ordinal_aba,\n)\nfrom mente_laylay.memoria_mental.politica_reexecucao import (\n    params_extras_reexecucao,\n)\n\n\nVERSAO_CONTINUIDADE_GERAL = 2\n""",
    "continuidade/import+versao",
)
cont = trocar_unico(
    cont,
    '        "dominios": {},\n        "operacoes_referenciaveis": {},\n        "historico": [],\n',
    '        "dominios": {},\n        "operacoes_referenciaveis": {},\n        "operacoes_reexecutaveis": {},\n        "historico": [],\n',
    "continuidade/estado-v2",
)

marcador = "\n\ndef registrar_evento_continuidade(\n"
pos = cont.find(marcador)
if pos < 0:
    falhar("continuidade: não achei registrar_evento_continuidade")
helpers = '''

def _valor_param_reexecucao_seguro(chave: str, valor: Any) -> tuple[bool, Any]:
    if isinstance(valor, (dict, set)):
        return False, None
    if isinstance(valor, (list, tuple)):
        itens: list[Any] = []
        for item in list(valor)[:8]:
            if isinstance(item, (bool, int, float)):
                itens.append(item)
            elif isinstance(item, str):
                itens.append(_texto_seguro(item, 80))
        return True, tuple(itens) if isinstance(valor, tuple) else itens
    if isinstance(valor, (bool, int, float)):
        return True, valor
    return True, _texto_seguro(valor, 160)


def _params_reexecucao_seguros(
    intent: str,
    params: Dict[str, Any] | None,
) -> Dict[str, Any]:
    bruto = dict(params or {})
    seguro = _params_seguros(bruto)
    for chave in params_extras_reexecucao(intent):
        if chave not in bruto or chave in seguro:
            continue
        aceito, valor = _valor_param_reexecucao_seguro(chave, bruto[chave])
        if aceito:
            seguro[chave] = valor
    return seguro


def _mesma_ocorrencia_reexecutavel(
    item: Dict[str, Any],
    recibo: Dict[str, Any],
) -> bool:
    if str(item.get("intent") or "").strip().upper() != str(recibo.get("intent") or "").strip().upper():
        return False
    id_item = str(item.get("id_solicitacao") or "").strip()
    id_recibo = str(recibo.get("id_solicitacao") or "").strip()
    if id_item or id_recibo:
        return bool(id_item and id_recibo and id_item == id_recibo)
    try:
        return abs(float(item.get("ts") or 0.0) - float(recibo.get("ts") or 0.0)) <= 1e-9
    except (TypeError, ValueError):
        return False
'''
cont = cont[:pos] + helpers + cont[pos:]

cont = trocar_unico(
    cont,
    '    status: str = "",\n    origem: str = "",\n    ttl_s: float = 900.0,\n',
    '    status: str = "",\n    origem: str = "",\n    id_solicitacao: str = "",\n    ttl_s: float = 900.0,\n',
    "continuidade/signature-id",
)
cont = trocar_unico(
    cont,
    '        "status": _texto_seguro(status, 60),\n        "origem": _texto_seguro(origem, 60),\n        "ativa": bool(ativa),\n',
    '        "status": _texto_seguro(status, 60),\n        "origem": _texto_seguro(origem, 60),\n        "id_solicitacao": _texto_seguro(id_solicitacao, 120),\n        "ativa": bool(ativa),\n',
    "continuidade/item-id",
)

antigo = '''    operacoes_referenciaveis = dict(
        continuidade.get("operacoes_referenciaveis") or {}
    )
    intent_item = str(item.get("intent") or "").upper().strip()
    if (
        str(item.get("evento") or "") == "acao"
        and intent_item in _POLITICAS_CONTINUACAO_ADITIVA
    ):
        operacoes_referenciaveis[intent_item] = {
            "intent": intent_item,
            "alvo": item.get("alvo"),
            "params": dict(item.get("params") or {}),
            "status": item.get("status"),
            "ativa": bool(item.get("ativa", True)),
            "ts": item.get("ts"),
            "expira_em": item.get("expira_em"),
        }
    historico = list(continuidade.get("historico") or [])
    resumo_historico_referenciavel = {
        chave: item.get(chave)
        for chave in ("evento", "dominio", "intent", "alvo", "status", "ts")
    }
    # Params só entram no histórico para operações que declararam política
    # aditiva; os valores já passaram por _params_seguros.
    # REGRESSAO_118_V1_20260814 | resumo_historico_referenciavel
    if str(item.get("intent") or "").upper() in _POLITICAS_CONTINUACAO_ADITIVA:
        resumo_historico_referenciavel["params"] = dict(item.get("params") or {})
    historico.append(resumo_historico_referenciavel)
'''
novo = '''    operacoes_referenciaveis = dict(
        continuidade.get("operacoes_referenciaveis") or {}
    )
    operacoes_reexecutaveis = dict(
        continuidade.get("operacoes_reexecutaveis") or {}
    )
    intent_item = str(item.get("intent") or "").upper().strip()
    if (
        str(item.get("evento") or "") == "acao"
        and intent_item in _POLITICAS_CONTINUACAO_ADITIVA
    ):
        operacoes_referenciaveis[intent_item] = {
            "intent": intent_item,
            "alvo": item.get("alvo"),
            "params": dict(item.get("params") or {}),
            "status": item.get("status"),
            "ativa": bool(item.get("ativa", True)),
            "ts": item.get("ts"),
            "expira_em": item.get("expira_em"),
        }

    params_reexecucao = _params_reexecucao_seguros(intent_item, params)
    if str(item.get("evento") or "") == "acao" and intent_item:
        if bool(item.get("reexecutavel")):
            operacoes_reexecutaveis[intent_item] = {
                "intent": intent_item,
                "dominio": dominio_norm,
                "alvo": item.get("alvo"),
                "params": params_reexecucao,
                "status": item.get("status"),
                "origem": item.get("origem"),
                "id_solicitacao": item.get("id_solicitacao"),
                "ativa": bool(item.get("ativa", True)),
                "reexecutavel": True,
                "ts": item.get("ts"),
                "expira_em": item.get("expira_em"),
            }
        else:
            operacoes_reexecutaveis.pop(intent_item, None)

    historico = list(continuidade.get("historico") or [])
    resumo_historico_referenciavel = {
        chave: item.get(chave)
        for chave in ("evento", "dominio", "intent", "alvo", "status", "id_solicitacao", "ts")
    }
    if intent_item in _POLITICAS_CONTINUACAO_ADITIVA:
        resumo_historico_referenciavel["params"] = dict(item.get("params") or {})
    elif bool(item.get("reexecutavel")):
        resumo_historico_referenciavel["params"] = dict(params_reexecucao)
    historico.append(resumo_historico_referenciavel)
'''
cont = trocar_unico(cont, antigo, novo, "continuidade/recibos-v2")
cont = trocar_unico(
    cont,
    '        "dominios": dominios,\n        "operacoes_referenciaveis": operacoes_referenciaveis,\n        "historico": historico[-24:],\n',
    '        "dominios": dominios,\n        "operacoes_referenciaveis": operacoes_referenciaveis,\n        "operacoes_reexecutaveis": operacoes_reexecutaveis,\n        "historico": historico[-24:],\n',
    "continuidade/update-v2",
)

inicio_sel = cont.index("def selecionar_continuidade_reexecutavel(")
fim_sel = cont.index("\n\ndef resumo_continuidade_para_prompt(", inicio_sel)
novo_sel = '''def selecionar_operacao_reexecutavel_compativel(
    estado_atual: Dict[str, Any] | None,
    *,
    intents_permitidos,
    ttl_s: float = 900.0,
) -> Dict[str, Any]:
    """Escolhe a última ocorrência reexecutável compatível com a fala tipada."""
    permitidos = {
        str(intent or "").strip().upper()
        for intent in (intents_permitidos or ())
        if str(intent or "").strip()
    }
    if not permitidos:
        return {}
    continuidade = dict((estado_atual or {}).get("continuidade_geral") or {})
    recibos = dict(continuidade.get("operacoes_reexecutaveis") or {})
    dominios = dict(continuidade.get("dominios") or {})
    agora = time.time()
    candidatos: list[Dict[str, Any]] = []

    for intent in permitidos:
        item = dict(recibos.get(intent) or {})
        if not item:
            continue
        try:
            idade = agora - float(item.get("ts") or 0.0)
            expira_em = float(item.get("expira_em") or 0.0)
        except (TypeError, ValueError):
            continue
        if (
            not item.get("ativa", True)
            or not bool(item.get("reexecutavel"))
            or idade > ttl_s
            or (expira_em and agora >= expira_em)
            or not isinstance(item.get("params"), dict)
        ):
            continue
        item["idade_s"] = max(0.0, idade)
        item["fonte"] = "operacao_reexecutavel"
        candidatos.append(item)

    # V1: somente slot oficial ainda existente; nada é reconstruído.
    for dominio, bruto in dominios.items():
        item = dict(bruto or {})
        intent = str(item.get("intent") or "").strip().upper()
        if intent not in permitidos or intent in recibos:
            continue
        try:
            idade = agora - float(item.get("ts") or 0.0)
            expira_em = float(item.get("expira_em") or 0.0)
        except (TypeError, ValueError):
            continue
        if (
            not item.get("ativa", True)
            or not bool(item.get("reexecutavel"))
            or idade > ttl_s
            or (expira_em and agora >= expira_em)
            or not isinstance(item.get("params"), dict)
        ):
            continue
        item["dominio"] = dominio
        item["idade_s"] = max(0.0, idade)
        item["fonte"] = "continuidade_v1"
        candidatos.append(item)

    if not candidatos:
        return {}
    return max(candidatos, key=lambda item: float(item.get("ts") or 0.0))


def selecionar_continuidade_reexecutavel(
    estado_atual: Dict[str, Any] | None,
    *,
    classe: str = "operacional",
    ttl_s: float = 900.0,
) -> Dict[str, Any]:
    """Mantém a escolha genérica atual e hidrata params da mesma ocorrência."""
    continuidade = dict((estado_atual or {}).get("continuidade_geral") or {})
    dominios = dict(continuidade.get("dominios") or {})
    classe_norm = str(classe or "operacional").strip().casefold()
    candidatos: list[Dict[str, Any]] = []
    agora = time.time()
    for dominio, bruto in dominios.items():
        item = dict(bruto or {})
        try:
            idade = agora - float(item.get("ts") or 0.0)
            expira_em = float(item.get("expira_em") or 0.0)
        except (TypeError, ValueError):
            continue
        if (
            not item
            or not item.get("ativa", True)
            or not bool(item.get("reexecutavel"))
            or idade > ttl_s
            or (expira_em and agora >= expira_em)
        ):
            continue
        if classe_norm in {"conversa", "conversacional"} and dominio != "conversa":
            continue
        if classe_norm in {"operacao", "operação", "operacional"} and dominio == "conversa":
            continue
        intent = str(item.get("intent") or "").strip().upper()
        if not intent or not isinstance(item.get("params"), dict):
            continue
        item["dominio"] = dominio
        item["idade_s"] = max(0.0, idade)
        candidatos.append(item)
    if not candidatos:
        return {}
    ativo = str(continuidade.get("dominio_ativo") or "")
    selecionado = max(
        candidatos,
        key=lambda item: (item.get("dominio") == ativo, float(item.get("ts") or 0.0)),
    )

    recibos = dict(continuidade.get("operacoes_reexecutaveis") or {})
    intent_selecionado = str(selecionado.get("intent") or "").strip().upper()
    recibo = dict(recibos.get(intent_selecionado) or {})
    if recibo and _mesma_ocorrencia_reexecutavel(selecionado, recibo):
        selecionado = dict(selecionado)
        selecionado["params"] = dict(recibo.get("params") or {})
        selecionado["fonte_params"] = "recibo_reexecucao_v2"
    return selecionado
'''
cont = cont[:inicio_sel] + novo_sel + cont[fim_sel:]

# 4) contexto_compartilhado.py
ctx = trocar_unico(
    ctx,
    """from mente_laylay.memoria_mental.efeitos_reversiveis import (\n    registrar_resultado_efeito_reversivel,\n)\n""",
    """from mente_laylay.memoria_mental.efeitos_reversiveis import (\n    registrar_resultado_efeito_reversivel,\n)\nfrom mente_laylay.memoria_mental.politica_reexecucao import (\n    intencao_reexecutavel_padrao,\n)\n""",
    "contexto/import-policy",
)
inicio_int = ctx.index("def intencao_reexecutavel(")
fim_int = ctx.index("\n\n_RESULTADOS_JA_SATISFEITOS_REFERENCIAVEIS", inicio_int)
ctx = ctx[:inicio_int] + '''def intencao_reexecutavel(intent: str) -> bool:
    return intencao_reexecutavel_padrao(intent)
''' + ctx[fim_int:]
ctx = trocar_unico(
    ctx,
    '            status=status_final,\n            origem=contrato.origem,\n            ttl_s=900.0,\n            reexecutavel=reexecutavel,\n',
    '            status=status_final,\n            origem=contrato.origem,\n            id_solicitacao=contrato.id_solicitacao,\n            ttl_s=900.0,\n            reexecutavel=reexecutavel,\n',
    "contexto/publica-id",
)

# Só escreve depois de validar tudo. Salva a baseline local antes do candidato.
if BACKUP.exists():
    falhar(f"backup anterior já existe: {BACKUP}")
BACKUP.mkdir(parents=True)
for original in (COMPAT, CONT, CTX):
    shutil.copy2(original, BACKUP / original.name)

POLITICA.parent.mkdir(parents=True, exist_ok=True)
gravar_atomico(POLITICA, politica)
gravar_atomico(COMPAT, compat)
gravar_atomico(CONT, cont)
gravar_atomico(CTX, ctx)

print("✅ Candidato R1-V1 aplicado com sucesso.")
print(f"  + {POLITICA}")
print(f"  * {COMPAT}")
print(f"  * {CONT}")
print(f"  * {CTX}")
print(f"Backup da baseline local: {BACKUP}")
print("Nenhum árbitro, coordenador, executor ou continuidade_semantica foi alterado.")
