#!/usr/bin/env python3
# P0_REVISAO_INTRA_TURNO_V1_1_20260816
from __future__ import annotations

import ast
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PATCH_ID = 'P0_REVISAO_INTRA_TURNO_V1_1_20260816'
BASELINE_HEAD = '6d8daa3dfe5a83b250154270a412285f88d42b96'

TARGETS = (
    Path("mente_laylay/cognicao/orquestrador_turno_runtime.py"),
    Path("mente_laylay/autonomia/comandos_imediatos.py"),
    Path("mente_laylay/autonomia/coordenador_intencao.py"),
    Path("mente_laylay/cognicao/revisao_turno.py"),
    Path("tests/test_revisao_intra_turno_v1.py"),
)

NEW_REVISOR = 'from __future__ import annotations\n\nimport re\nimport unicodedata\nfrom typing import Any, Dict\n\n_OPERACOES = (\n    ("retomar", r"(?:continua|continue|continuar|retoma|retome|retomar|volta\\s+a\\s+tocar)"),\n    ("maximizar", r"(?:maximiza|maximize|maximizar|tela\\s+cheia|fullscreen)"),\n    ("fechar", r"(?:fecha|feche|fechar|encerra|encerre|encerrar)"),\n    ("abrir", r"(?:abre|abra|abrir|acessa|acesse|acessar)"),\n    ("pausar", r"(?:pausa|pause|pausar)"),\n    ("criar", r"(?:cria|crie|criar)"),\n    ("apagar", r"(?:apaga|apague|apagar|deleta|delete|deletar|remove|remova|remover|exclui|exclua|excluir)"),\n    ("ligar", r"(?:liga|ligue|ligar|acende|acenda|acender)"),\n    ("desligar", r"(?:desliga|desligue|desligar)"),\n    ("pesquisar", r"(?:pesquisa|pesquise|pesquisar|busca|busque|buscar|procura|procure|procurar|encontra|encontre|encontrar)"),\n    ("tocar", r"(?:toca|toque|tocar|coloca|coloque|colocar|bota|bote|botar)"),\n)\n\n_VERBO_INICIO = re.compile(\n    r"^\\s*(?:me\\s+)?(?P<verbo>" + "|".join(f"(?:{p})" for _, p in _OPERACOES) + r")\\b(?:\\s+(?P<resto>.*))?$",\n    re.IGNORECASE,\n)\n_REVISAO = re.compile(\n    r"(?P<sep>\\.\\.\\.|…|;|,\\s*|\\bmas\\s+)"\n    r"(?P<espaco>\\s*)"\n    r"(?P<marker>não|nao|esquece|esqueça|quer\\s+dizer|na\\s+verdade|melhor)\\b",\n    re.IGNORECASE,\n)\n\ndef _norm(valor: str) -> str:\n    base = unicodedata.normalize("NFKD", str(valor or "").casefold())\n    return "".join(ch for ch in base if not unicodedata.combining(ch))\n\ndef _intervalos_aspas(texto: str) -> list[tuple[int,int]]:\n    pares = {\'"\':\'"\', \'“\':\'”\', "\'":"\'", \'‘\':\'’\'}\n    intervalos=[]\n    inicio=None\n    fecha=None\n    for i,ch in enumerate(texto):\n        if inicio is None:\n            if ch in pares:\n                # apóstrofo só abre se houver outro adiante\n                if ch == "\'" and "\'" not in texto[i+1:]:\n                    continue\n                inicio=i; fecha=pares[ch]\n        else:\n            if ch == fecha:\n                intervalos.append((inicio, i))\n                inicio=None; fecha=None\n    if inicio is not None:\n        intervalos.append((inicio, len(texto)-1))\n    return intervalos\n\ndef _dentro_aspas(pos:int, intervalos:list[tuple[int,int]]) -> bool:\n    return any(a <= pos <= b for a,b in intervalos)\n\ndef _operacao_inicio(texto: str) -> dict[str,str]:\n    bruto=str(texto or "").strip(" \\t\\r\\n,;:.!?…")\n    m=_VERBO_INICIO.match(bruto)\n    if not m:\n        return {}\n    verbo=m.group("verbo") or ""\n    resto=(m.group("resto") or "").strip(" \\t\\r\\n,;:.!?…")\n    verbo_n=_norm(verbo)\n    canon=""\n    for nome,padrao in _OPERACOES:\n        if re.fullmatch(padrao, verbo_n, re.I):\n            canon=nome; break\n    return {"canon":canon, "verbo":verbo, "resto":resto}\n\ndef _tem_operacao(texto:str)->bool:\n    return bool(_operacao_inicio(texto))\n\ndef _alvo_da_proposta(proposta:str, operacao:dict[str,str]) -> str:\n    canon=operacao.get("canon","")\n    if canon=="criar":\n        m=re.search(\n            r"\\b(?:arquivo|documento|pasta)\\b.*?\\b(?:chamad[oa]|com\\s+nome)\\s+(.+)$",\n            proposta, re.I,\n        )\n        if m:\n            return m.group(1).strip(" \\t\\r\\n,;:!?…")\n    resto=str(operacao.get("resto") or "").strip()\n    resto=re.sub(r"^(?:o|a|os|as|um|uma)\\s+", "", resto, flags=re.I)\n    resto=re.sub(r"\\s+\\bagora\\b$", "", resto, flags=re.I).strip()\n    return resto.strip(" \\t\\r\\n,;:.!?…")\n\ndef _resolver_pronome(texto:str, alvo:str) -> tuple[str,bool]:\n    if not re.search(r"\\b(?:ele|ela|isso|esse|essa|este|esta)\\b", texto, re.I):\n        return texto, True\n    if not alvo:\n        return texto, False\n    novo=re.sub(r"\\b(?:ele|ela|isso|esse|essa|este|esta)\\b", alvo, texto, count=1, flags=re.I)\n    return novo, True\n\ndef _nome_parametro(texto:str)->str:\n    t=str(texto or "").strip(" \\t\\r\\n,;:.!?…")\n    m=re.match(\n        r"^(?:chama|chame|chamar|nomeia|nomeie|nomear|renomeia|renomeie|renomear)"\n        r"(?:\\s+(?:de|para|pra))?\\s+(.+)$",\n        t, re.I,\n    )\n    if not m:\n        m=re.match(r"^(?:o\\s+)?nome\\s+(?:e|é)\\s+(.+)$", t, re.I)\n    return (m.group(1).strip(" \\t\\r\\n,;:!?…") if m else "")\n\ndef _substituir_nome_criacao(proposta:str, novo_nome:str)->str:\n    return re.sub(\n        r"(\\b(?:chamad[oa]|com\\s+nome)\\s+)(.+)$",\n        lambda m: m.group(1) + novo_nome,\n        proposta.strip(" \\t\\r\\n,;:.!?…"),\n        count=1,\n        flags=re.I,\n    )\n\ndef _limpar_inicio_correcao(texto:str)->str:\n    t=str(texto or "").strip(" \\t\\r\\n,;:-.…")\n    t=re.sub(r"^(?:entao|então|agora)\\s+", "", t, flags=re.I)\n    return t.strip()\n\ndef resolver_revisao_intra_turno(texto: str) -> Dict[str, Any]:\n    bruto=re.sub(r"\\s+", " ", str(texto or "")).strip()\n    base={\n        "detectada":False,\n        "resolvida":False,\n        "cancelada":False,\n        "tipo":"",\n        "texto_original":bruto[:500],\n        "texto_operacional_efetivo":"",\n        "proposta_anterior":"",\n        "correcao":"",\n        "alvo_herdado":"",\n        "motivo":"",\n    }\n    if not bruto:\n        return base\n    intervalos=_intervalos_aspas(bruto)\n    achado=None\n    for m in _REVISAO.finditer(bruto):\n        if _dentro_aspas(m.start("marker"), intervalos):\n            continue\n        proposta=bruto[:m.start()].strip(" \\t\\r\\n,;:.!?…")\n        if not _tem_operacao(proposta):\n            continue\n        achado=m\n        break\n    if achado is None:\n        return base\n    proposta=bruto[:achado.start()].strip(" \\t\\r\\n,;:.!?…")\n    marker=_norm(achado.group("marker"))\n    correcao=_limpar_inicio_correcao(bruto[achado.end():])\n    operacao_antiga=_operacao_inicio(proposta)\n    alvo_antigo=_alvo_da_proposta(proposta, operacao_antiga)\n    base.update(\n        detectada=True,\n        proposta_anterior=proposta[:300],\n        correcao=correcao[:300],\n        alvo_herdado=alvo_antigo[:160],\n    )\n    if marker in {"esquece","esqueca"} and not correcao:\n        base.update(resolvida=True,cancelada=True,tipo="cancelamento",motivo="revisao descartou a proposta anterior")\n        return base\n    if marker in {"nao"} and not correcao:\n        base.update(resolvida=True,cancelada=True,tipo="cancelamento",motivo="negação corretiva descartou a proposta anterior")\n        return base\n\n    # "não, melhor X" / "melhor X"\n    correcao_sem_melhor=re.sub(r"^melhor\\b[\\s,:-]*", "", correcao, flags=re.I).strip()\n    tinha_melhor=correcao_sem_melhor != correcao\n    if tinha_melhor:\n        correcao=correcao_sem_melhor\n\n    nova_op=_operacao_inicio(correcao)\n    if nova_op:\n        # Elipses como "continua tocando" carregam a nova operação, mas\n        # omitem o alvo que já estava explícito na proposta descartada.\n        # Herdamos somente quando o complemento é um marcador de continuidade\n        # sem alvo próprio; o executor recebe então uma fala autossuficiente.\n        resto_novo=_norm(str(nova_op.get("resto") or "")).strip()\n        if (\n            alvo_antigo\n            and nova_op.get("canon")=="retomar"\n            and resto_novo in {"", "tocando", "a tocar"}\n        ):\n            correcao=f"{nova_op.get(\'verbo\')} {alvo_antigo}".strip()\n            nova_op=_operacao_inicio(correcao)\n        # "apaga X... não apaga" = cancela, não é uma segunda exclusão sem alvo.\n        if marker=="nao" and nova_op.get("canon")==operacao_antiga.get("canon") and not nova_op.get("resto"):\n            base.update(resolvida=True,cancelada=True,tipo="cancelamento",motivo="negação repetiu a operação sem novo alvo")\n            return base\n        efetivo, ok=_resolver_pronome(correcao, alvo_antigo)\n        if not ok:\n            base.update(tipo="ambigua",motivo="correção usa referência sem alvo seguro da proposta anterior")\n            return base\n        base.update(\n            resolvida=True,\n            tipo="substituicao_acao" if nova_op.get("canon") != operacao_antiga.get("canon") else "substituicao_comando",\n            texto_operacional_efetivo=efetivo.strip(" \\t\\r\\n,;:.!?…")[:500],\n            motivo="última proposta operacional explícita substitui a anterior",\n        )\n        return base\n\n    novo_nome=_nome_parametro(correcao)\n    if novo_nome and operacao_antiga.get("canon")=="criar":\n        efetivo=_substituir_nome_criacao(proposta, novo_nome)\n        if efetivo != proposta:\n            base.update(\n                resolvida=True,tipo="substituicao_parametro",\n                texto_operacional_efetivo=efetivo[:500],\n                motivo="correção alterou parâmetro da criação antes da execução",\n            )\n            return base\n\n    # "abre X... não, melhor Y": mantém a operação, troca só o alvo.\n    if (tinha_melhor or marker in {"quer dizer","na verdade","nao","melhor"}) and correcao:\n        if operacao_antiga.get("canon") in {"abrir","fechar","maximizar","ligar","desligar","pesquisar","tocar"}:\n            if len(correcao.split()) <= 8 and not re.search(r"\\b(?:e depois|depois|entao|então)\\b", correcao, re.I):\n                efetivo=f"{operacao_antiga.get(\'verbo\')} {correcao}".strip()\n                base.update(\n                    resolvida=True,tipo="substituicao_alvo",\n                    texto_operacional_efetivo=efetivo[:500],\n                    motivo="correção substituiu somente o alvo da proposta anterior",\n                )\n                return base\n\n    if marker in {"esquece","esqueca"}:\n        base.update(tipo="ambigua",motivo="houve cancelamento, mas a continuação não formou um comando seguro")\n        return base\n\n    base.update(tipo="ambigua",motivo="revisão detectada sem forma operacional segura")\n    return base\n'
NEW_TESTS = 'from __future__ import annotations\n\nimport inspect\n\nimport pytest\n\nfrom mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito\nfrom mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno\nfrom mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno\n\n\n@pytest.mark.parametrize(\n    ("texto", "efetivo", "tipo"),\n    [\n        (\n            "Pausa a música... esquece, continua tocando.",\n            "continua música",\n            "substituicao_acao",\n        ),\n        (\n            "Cria um arquivo chamado erro.txt... não, chama correcao.txt.",\n            "Cria um arquivo chamado correcao.txt",\n            "substituicao_parametro",\n        ),\n        (\n            "Abre Wikipédia... não, melhor Prime Video.",\n            "Abre Prime Video",\n            "substituicao_alvo",\n        ),\n        (\n            "Fecha a Calculadora... quer dizer, maximiza ela.",\n            "maximiza Calculadora",\n            "substituicao_acao",\n        ),\n    ],\n)\ndef test_revisao_intra_turno_produz_uma_unica_fala_operacional(\n    texto: str, efetivo: str, tipo: str,\n) -> None:\n    revisao = resolver_revisao_intra_turno(texto)\n    assert revisao["detectada"] is True\n    assert revisao["resolvida"] is True\n    assert revisao["cancelada"] is False\n    assert revisao["tipo"] == tipo\n    assert revisao["texto_operacional_efetivo"] == efetivo\n\n    turno_final = classificar_modalidade_turno(\n        efetivo,\n        texto_tem_comando_explicito=texto_tem_comando_explicito,\n    )\n    assert turno_final["autoriza_execucao"] is True\n    assert turno_final["texto_operacional"]\n\n\ndef test_continuacao_eliptica_herda_alvo_da_proposta_descartada() -> None:\n    revisao = resolver_revisao_intra_turno(\n        "Pausa a música... esquece, continua tocando."\n    )\n    assert revisao["alvo_herdado"] == "música"\n    assert revisao["texto_operacional_efetivo"] == "continua música"\n\n\ndef test_negacao_corretiva_cancela_mutacao_em_vez_de_repetir() -> None:\n    revisao = resolver_revisao_intra_turno(\n        "Apaga o arquivo segredo.txt... não apaga."\n    )\n    assert revisao["detectada"] is True\n    assert revisao["resolvida"] is True\n    assert revisao["cancelada"] is True\n    assert revisao["texto_operacional_efetivo"] == ""\n\n\n@pytest.mark.parametrize(\n    "texto",\n    [\n        "Abre o Opera e depois abre a Calculadora.",\n        "Pausa a música e depois continua.",\n        \'Pesquisa por "não apaga".\',\n        "Abre o melhor resultado.",\n        "Cria um arquivo chamado não.txt.",\n    ],\n)\ndef test_falas_sem_revisao_preservam_fluxo_existente(texto: str) -> None:\n    revisao = resolver_revisao_intra_turno(texto)\n    assert revisao["detectada"] is False\n    assert revisao["resolvida"] is False\n    assert revisao["texto_operacional_efetivo"] == ""\n\n\ndef test_revisao_ambigua_fica_fail_closed() -> None:\n    revisao = resolver_revisao_intra_turno(\n        "Cria um arquivo chamado teste.txt... na verdade alguma outra coisa."\n    )\n    assert revisao["detectada"] is True\n    assert revisao["resolvida"] is False\n    assert revisao["tipo"] == "ambigua"\n    assert revisao["texto_operacional_efetivo"] == ""\n\n\ndef test_referencia_da_correcao_herda_alvo_da_proposta_descartada() -> None:\n    revisao = resolver_revisao_intra_turno(\n        "Fecha a Calculadora... quer dizer, maximiza ela."\n    )\n    assert revisao["alvo_herdado"] == "Calculadora"\n    assert revisao["texto_operacional_efetivo"] == "maximiza Calculadora"\n    assert "fecha" not in revisao["texto_operacional_efetivo"].casefold()\n\n\ndef test_revisao_esta_ligada_antes_dos_roteadores_operacionais() -> None:\n    from mente_laylay.cognicao import orquestrador_turno_runtime\n    from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime\n    from mente_laylay.autonomia import coordenador_intencao\n\n    fonte_turno = inspect.getsource(\n        orquestrador_turno_runtime._iniciar_planejamento_turno\n    )\n    assert "resolver_revisao_intra_turno(texto)" in fonte_turno\n    assert "texto_cognitivo" in fonte_turno\n    assert "revisão interna detectada sem resolução operacional segura" in fonte_turno\n\n    fonte_prioridade = inspect.getsource(\n        ComandosImediatosRuntime.processar_prioritarios\n    )\n    assert "texto_operacional_efetivo" in fonte_prioridade\n    assert "[REVISÃO:PRIORIDADE]" in fonte_prioridade\n\n    fonte_coordenador = inspect.getsource(coordenador_intencao.resolver_intencao)\n    assert "revisao_resolvida" in fonte_coordenador\n    assert "texto_operacional_efetivo" in fonte_coordenador\n'


class PatchError(RuntimeError):
    pass


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(args),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        raise PatchError(
            f"comando falhou ({result.returncode}): {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise PatchError(
            f"anchor {label!r} esperado 1x, encontrado {count}x; nada foi gravado"
        )
    return text.replace(old, new, 1)


def ensure_repo_root() -> None:
    raiz = run("git", "rev-parse", "--show-toplevel", check=False)
    if raiz.returncode != 0:
        raise PatchError(
            "execute este patcher dentro do repositório Laylay, na pasta que contém .git"
        )
    raiz_git = Path(raiz.stdout.strip()).resolve()
    if Path.cwd().resolve() != raiz_git:
        raise PatchError(
            f"execute na raiz do repositório: {raiz_git}"
        )
    head = run("git", "rev-parse", "HEAD").stdout.strip()
    if head != BASELINE_HEAD:
        raise PatchError(
            f"HEAD incompatível: esperado {BASELINE_HEAD}, encontrado {head}. "
            "O patch é travado no teste 2.6 e não vai adivinhar anchors."
        )


def ensure_clean_targets() -> None:
    existentes = [str(p) for p in TARGETS if p.exists()]
    if existentes:
        status = run("git", "status", "--porcelain", "--", *existentes).stdout
        if status.strip():
            raise PatchError(
                "há alterações locais em arquivos-alvo; commit/stash antes de aplicar:\n"
                + status
            )
    for novo in (Path("mente_laylay/cognicao/revisao_turno.py"), Path("tests/test_revisao_intra_turno_v1.py")):
        if novo.exists():
            conteudo = read_text(novo)
            if PATCH_ID in conteudo:
                raise PatchError("patch já parece aplicado; nenhum arquivo foi alterado")
            raise PatchError(f"arquivo novo já existe e não pertence a este patch: {novo}")


def build_changes() -> dict[Path, str]:
    changes: dict[Path, str] = {}

    orq_path = Path("mente_laylay/cognicao/orquestrador_turno_runtime.py")
    orq = read_text(orq_path)
    if PATCH_ID in orq:
        raise PatchError("marcador do patch já existe no orquestrador")

    import_anchor = """from mente_laylay.cognicao.intencao_visual_jogo import (
    aplicar_pedido_visual_ao_turno,
    detectar_pedido_visao_jogo,
)
"""
    import_new = import_anchor + """from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
"""
    orq = replace_once(orq, import_anchor, import_new, label="import revisao_turno")

    start_old = """    mente_antes_turno = dict(ns['_estado_compartilhado_runtime'].mental)
    pendencia_turno = ns['_pendencia_ativa_turno_mente'](mente_antes_turno) or {}
    confirmacao_contextual_valida = bool(pendencia_turno.get('intencao') and (str(pendencia_turno.get('resposta_esperada') or '') == 'sim_ou_nao' or str(pendencia_turno.get('tipo') or '') in {'confirmacao', 'escolha'}))
    turno = ns['_classificar_modalidade_turno_mente'](texto, normalizar_texto=ns['_normalizar_texto_com_apelidos'], texto_tem_comando_explicito=ns['_texto_tem_comando_explicito'], confirmacao_contextual_valida=confirmacao_contextual_valida)
    turno['origem_entrada'] = _normalizar_origem_entrada(origem)
    repeticao_operacional = resolver_repeticao_operacional_segura(ns, texto)
    turno = aplicar_repeticao_operacional_ao_turno(turno, repeticao_operacional)
"""
    start_new = """    mente_antes_turno = dict(ns['_estado_compartilhado_runtime'].mental)
    pendencia_turno = ns['_pendencia_ativa_turno_mente'](mente_antes_turno) or {}
    confirmacao_contextual_valida = bool(pendencia_turno.get('intencao') and (str(pendencia_turno.get('resposta_esperada') or '') == 'sim_ou_nao' or str(pendencia_turno.get('tipo') or '') in {'confirmacao', 'escolha'}))

    # P0_REVISAO_INTRA_TURNO_V1_1_20260816
    # Revisões dentro da própria fala são consolidadas antes do primeiro
    # detector operacional. O texto original continua auditável; apenas a
    # visão cognitiva/operacional recebe a última proposta válida.
    revisao_intra_turno = resolver_revisao_intra_turno(texto)
    revisao_detectada = bool(revisao_intra_turno.get('detectada'))
    revisao_resolvida = bool(revisao_intra_turno.get('resolvida'))
    revisao_cancelada = bool(revisao_intra_turno.get('cancelada'))
    texto_efetivo = str(
        revisao_intra_turno.get('texto_operacional_efetivo') or ''
    ).strip()
    texto_cognitivo = (
        texto_efetivo
        if revisao_detectada and revisao_resolvida and not revisao_cancelada and texto_efetivo
        else texto
    )

    turno = ns['_classificar_modalidade_turno_mente'](texto_cognitivo, normalizar_texto=ns['_normalizar_texto_com_apelidos'], texto_tem_comando_explicito=ns['_texto_tem_comando_explicito'], confirmacao_contextual_valida=confirmacao_contextual_valida)
    turno['origem_entrada'] = _normalizar_origem_entrada(origem)
    if revisao_detectada:
        turno['texto_original'] = str(texto or '')[:500]
        turno['texto'] = str(texto or '')[:500]
        turno['revisao_intra_turno'] = dict(revisao_intra_turno)
        turno['texto_operacional_efetivo'] = texto_efetivo
        if not revisao_resolvida:
            turno.update(
                modalidade='correcao',
                modalidade_geral='correcao',
                ato_principal='correcao',
                autoriza_execucao=False,
                requer_esclarecimento=True,
                acao_explicita=False,
                texto_operacional='',
                natureza_acao='revisao_ambigua',
                motivo='revisão interna detectada sem resolução operacional segura',
                motivo_decisao='revisão interna detectada sem resolução operacional segura',
            )
        elif revisao_cancelada:
            turno.update(
                modalidade='recusa',
                modalidade_geral='recusa',
                ato_principal='recusa',
                autoriza_execucao=False,
                requer_esclarecimento=False,
                acao_explicita=False,
                texto_operacional='',
                natureza_acao='cancelamento_revisao',
                motivo='usuário cancelou a proposta antes da execução',
                motivo_decisao='usuário cancelou a proposta antes da execução',
            )
        else:
            turno['texto_operacional'] = (
                texto_efetivo if bool(turno.get('autoriza_execucao')) else ''
            )
            ns['print'](
                '🧠 [REVISÃO:TURNO] '
                f"tipo={revisao_intra_turno.get('tipo')} | "
                f"efetivo={texto_efetivo!r}"
            )

    # Uma revisão atual não pode ser reinterpretada como repetição da ação
    # anterior só porque a proposta final contém "continua", "de novo" etc.
    repeticao_operacional = (
        None if revisao_detectada
        else resolver_repeticao_operacional_segura(ns, texto)
    )
    turno = aplicar_repeticao_operacional_ao_turno(turno, repeticao_operacional)
"""
    orq = replace_once(orq, start_old, start_new, label="pre-execucao revisao")

    replacements = [
        (
            "pedido_visao_jogo = detectar_pedido_visao_jogo(texto, jogo_contexto)",
            "pedido_visao_jogo = detectar_pedido_visao_jogo(texto_cognitivo, jogo_contexto)",
            "visao usa texto cognitivo",
        ),
        (
            "interpretador_semantico.observar(texto, turno_legado=dict(turno))",
            "interpretador_semantico.observar(texto_cognitivo, turno_legado=dict(turno))",
            "shadow semantico usa texto cognitivo",
        ),
        (
            "leitura_semantica = dict(interpretador_semantico.analisar(texto, turno_legado=turno) or {})",
            "leitura_semantica = dict(interpretador_semantico.analisar(texto_cognitivo, turno_legado=turno) or {})",
            "semantica usa texto cognitivo",
        ),
        (
            "funcao_comunicativa = ns['_analisar_funcao_comunicativa_mente'](texto)",
            "funcao_comunicativa = ns['_analisar_funcao_comunicativa_mente'](texto_cognitivo)",
            "funcao comunicativa efetiva",
        ),
        (
            "retrato_turno, entidades_recentes = ns['_construir_retrato_turno_mente'](texto, turno=turno, mente=mente_antes_turno, contexto_perceptivo=ns['_obter_contexto_perceptivo'](), playlist_state=ns['playlist_state'], jogo_contexto=jogo_contexto)",
            "retrato_turno, entidades_recentes = ns['_construir_retrato_turno_mente'](texto_cognitivo, turno=turno, mente=mente_antes_turno, contexto_perceptivo=ns['_obter_contexto_perceptivo'](), playlist_state=ns['playlist_state'], jogo_contexto=jogo_contexto)",
            "retrato efetivo",
        ),
        (
            "tema_factual = ns['_extrair_tema_fundamentacao_mente'](\n        texto, retrato=retrato_turno, registro_semantico=registro_semantico,\n    )",
            "tema_factual = ns['_extrair_tema_fundamentacao_mente'](\n        texto_cognitivo, retrato=retrato_turno, registro_semantico=registro_semantico,\n    )",
            "tema factual efetivo",
        ),
        (
            "especialistas = ns['_construir_parecer_especialistas_mente'](texto, turno=turno, funcao_comunicativa=funcao_comunicativa, retrato=retrato_turno, saude=ns['_saude_mente_runtime'].snapshot())",
            "especialistas = ns['_construir_parecer_especialistas_mente'](texto_cognitivo, turno=turno, funcao_comunicativa=funcao_comunicativa, retrato=retrato_turno, saude=ns['_saude_mente_runtime'].snapshot())",
            "especialistas efetivos",
        ),
        (
            "plano = ns['_planejar_turno_mente'](texto, turno=turno, mente=mente_antes_turno, periodo=ns['_contexto_horario_atual']())",
            "plano = ns['_planejar_turno_mente'](texto_cognitivo, turno=turno, mente=mente_antes_turno, periodo=ns['_contexto_horario_atual']())",
            "plano efetivo",
        ),
        (
            "evidencia_habilidades = evidencia_habilidades_getter(texto, turno=turno)",
            "evidencia_habilidades = evidencia_habilidades_getter(texto_cognitivo, turno=turno)",
            "evidencia habilidades efetiva",
        ),
    ]
    for old, new, label in replacements:
        orq = replace_once(orq, old, new, label=label)
    ast.parse(orq, filename=str(orq_path))
    changes[orq_path] = orq

    pri_path = Path("mente_laylay/autonomia/comandos_imediatos.py")
    pri = read_text(pri_path)
    if PATCH_ID in pri:
        raise PatchError("marcador do patch já existe em comandos_imediatos")
    pri_old = """        ns = self.namespace_getter() or {}
        estado_runtime = ns.get("_estado_compartilhado_runtime")
        contexto_prioritario = dict(ns)
"""
    pri_new = """        ns = self.namespace_getter() or {}
        estado_runtime = ns.get("_estado_compartilhado_runtime")

        # P0_REVISAO_INTRA_TURNO_V1_1_20260816
        # Todo detector prioritário recebe a mesma proposta final que planejou
        # o turno. A fala original permanece na memória e nos logs do turno.
        mente_prioritaria = getattr(estado_runtime, "mental", {})
        turno_prioritario = (
            dict(mente_prioritaria.get("turno_atual") or {})
            if isinstance(mente_prioritaria, dict)
            else {}
        )
        revisao_prioritaria = (
            dict(turno_prioritario.get("revisao_intra_turno") or {})
            if isinstance(turno_prioritario.get("revisao_intra_turno"), dict)
            else {}
        )
        if (
            revisao_prioritaria.get("detectada") is True
            and revisao_prioritaria.get("resolvida") is True
            and revisao_prioritaria.get("cancelada") is not True
        ):
            texto_final = str(
                turno_prioritario.get("texto_operacional_efetivo")
                or revisao_prioritaria.get("texto_operacional_efetivo")
                or ""
            ).strip()
            if texto_final:
                print(
                    "🧠 [REVISÃO:PRIORIDADE] usando proposta final -> "
                    f"{texto_final!r}"
                )
                texto = texto_final

        contexto_prioritario = dict(ns)
"""
    pri = replace_once(pri, pri_old, pri_new, label="prioritarios usam texto efetivo")
    ast.parse(pri, filename=str(pri_path))
    changes[pri_path] = pri

    coord_path = Path("mente_laylay/autonomia/coordenador_intencao.py")
    coord = read_text(coord_path)
    if PATCH_ID in coord:
        raise PatchError("marcador do patch já existe no coordenador")
    coord_old = """    retrato_atual = dict(ctx.get("retrato_turno_atual") or {})
    turno_congelado = dict(ctx.get("turno_atual") or {})
    trecho_operacional = str(turno_congelado.get("texto_operacional") or "").strip()
    moldura_nao_autoriza_recorte = bool(
"""
    coord_new = """    retrato_atual = dict(ctx.get("retrato_turno_atual") or {})
    turno_congelado = dict(ctx.get("turno_atual") or {})
    # P0_REVISAO_INTRA_TURNO_V1_1_20260816
    revisao_turno = (
        dict(turno_congelado.get("revisao_intra_turno") or {})
        if isinstance(turno_congelado.get("revisao_intra_turno"), dict)
        else {}
    )
    revisao_resolvida = bool(
        revisao_turno.get("detectada")
        and revisao_turno.get("resolvida")
        and not revisao_turno.get("cancelada")
    )
    trecho_operacional = str(
        turno_congelado.get("texto_operacional_efetivo")
        or turno_congelado.get("texto_operacional")
        or ""
    ).strip()
    moldura_nao_autoriza_recorte = bool(
"""
    coord = replace_once(coord, coord_old, coord_new, label="coordenador le revisao")
    cond_old = """        if trecho_operacional
        and str(turno_congelado.get("modalidade_geral") or "") == "misto"
        and bool(turno_congelado.get("autoriza_execucao"))
        and not moldura_nao_autoriza_recorte
"""
    cond_new = """        if trecho_operacional
        and (
            revisao_resolvida
            or str(turno_congelado.get("modalidade_geral") or "") == "misto"
        )
        and bool(turno_congelado.get("autoriza_execucao"))
        and not moldura_nao_autoriza_recorte
"""
    coord = replace_once(coord, cond_old, cond_new, label="coordenador prefere proposta final")
    ast.parse(coord, filename=str(coord_path))
    changes[coord_path] = coord

    changes[Path("mente_laylay/cognicao/revisao_turno.py")] = (
        "# P0_REVISAO_INTRA_TURNO_V1_1_20260816\n" + NEW_REVISOR
    )
    changes[Path("tests/test_revisao_intra_turno_v1.py")] = (
        "# P0_REVISAO_INTRA_TURNO_V1_1_20260816\n" + NEW_TESTS
    )
    for path, content in changes.items():
        if path.suffix == ".py":
            ast.parse(content, filename=str(path))
    return changes


def backup_and_write(changes: dict[Path, str]) -> tuple[Path, dict[str, str | None]]:
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = Path(".laylay_patch_backups") / PATCH_ID / stamp
    backup_root.mkdir(parents=True, exist_ok=False)
    before_hashes: dict[str, str | None] = {}
    for path, content in changes.items():
        before_hashes[str(path)] = sha256_text(read_text(path)) if path.exists() else None
        if path.exists():
            backup_path = backup_root / path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    return backup_root, before_hashes


def rollback(changes: dict[Path, str], backup_root: Path) -> None:
    for path in changes:
        backup = backup_root / path
        if backup.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, path)
        elif path.exists():
            path.unlink()


def main() -> int:
    ensure_repo_root()
    ensure_clean_targets()
    changes = build_changes()

    backup_root: Path | None = None
    before_hashes: dict[str, str | None] = {}
    try:
        backup_root, before_hashes = backup_and_write(changes)

        compile_result = run(
            sys.executable, "-m", "py_compile",
            *[str(p) for p in changes if p.suffix == ".py"],
            check=False,
        )
        if compile_result.returncode != 0:
            raise PatchError("py_compile falhou:\n" + compile_result.stderr)

        diffcheck = run("git", "diff", "--check", check=False)
        if diffcheck.returncode != 0:
            raise PatchError("git diff --check falhou:\n" + diffcheck.stdout + diffcheck.stderr)

        pytest_result = run(
            sys.executable, "-m", "pytest", "-q",
            "tests/test_revisao_intra_turno_v1.py",
            "tests/test_autorizacao_ato_fala_v2.py",
            "tests/test_arbitro_modalidade_inteligente.py",
            "tests/test_cadeia_contexto_vivo_v2.py",
            check=False,
        )
        if pytest_result.returncode != 0:
            raise PatchError(
                "pytest focado falhou:\n"
                + pytest_result.stdout
                + "\n"
                + pytest_result.stderr
            )

        diff_text = run("git", "diff", "--", *[str(p) for p in changes]).stdout
        (backup_root / "patch.diff").write_text(diff_text, encoding="utf-8")

        after_hashes = {
            str(path): sha256_text(read_text(path))
            for path in changes
        }
        manifest = {
            "patch_id": PATCH_ID,
            "baseline_head": BASELINE_HEAD,
            "status": "applied",
            "applied_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "files": [
                {
                    "path": str(path),
                    "sha256_before": before_hashes.get(str(path)),
                    "sha256_after": after_hashes[str(path)],
                }
                for path in changes
            ],
            "tests": {
                "py_compile_returncode": compile_result.returncode,
                "git_diff_check_returncode": diffcheck.returncode,
                "pytest_returncode": pytest_result.returncode,
                "pytest_output": pytest_result.stdout[-6000:],
            },
            "backup_dir": str(backup_root),
        }
        (backup_root / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(f"✅ {PATCH_ID} aplicado com sucesso.")
        print(f"🔒 baseline: {BASELINE_HEAD}")
        print(f"🧪 {pytest_result.stdout.strip()}")
        print(f"🗂️ backup/manifest: {backup_root}")
        print("ℹ️ Nenhum commit, push ou git add foi executado.")
        return 0
    except Exception:
        if backup_root is not None:
            rollback(changes, backup_root)
            try:
                (backup_root / "ROLLBACK.txt").write_text(
                    "Patch revertido automaticamente após falha.\n",
                    encoding="utf-8",
                )
            except Exception:
                pass
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PatchError as exc:
        print(f"❌ {PATCH_ID} não foi aplicado: {exc}", file=sys.stderr)
        raise SystemExit(2)
