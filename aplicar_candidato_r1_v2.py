#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APLICADOR — CANDIDATO R1-V2 / FAIL-CLOSED MONOTÔNICO DA REPETIÇÃO TIPADA

Produção alterada:
    mente_laylay/cognicao/orquestrador_turno_runtime.py

Teste novo:
    tests/test_r1_v2_fail_closed_repeticao_tipificada.py

Uso:
    python .\\aplicar_candidato_r1_v2.py
    python .\\aplicar_candidato_r1_v2.py --reverter
"""

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
from pathlib import Path

HEAD_ESPERADO = "dc72f429088949211b86bf0160de518bfd1bbccc"
MARCADOR = 'ROOT_R1_V2_FAIL_CLOSED_TIPADO_20260826'

ARQ_ORQ = Path("mente_laylay/cognicao/orquestrador_turno_runtime.py")
ARQ_COMPAT = Path("mente_laylay/memoria_mental/compatibilidade_contexto.py")
ARQ_POLITICA = Path("mente_laylay/memoria_mental/politica_reexecucao.py")
ARQ_MODALIDADE = Path("mente_laylay/cognicao/modalidade_turno.py")
ARQ_TESTE = Path("tests/test_r1_v2_fail_closed_repeticao_tipificada.py")

BLOBS_ESPERADOS = {
    ARQ_ORQ: "6105e8307e863f1a52a247e252cbbab130e7a3bd",
    ARQ_COMPAT: "95f93c29df0c91bf3f55a8b10236a06f8d0be3db",
    ARQ_POLITICA: "ee427daf06b0e579a2a402d1a1113db4a3cb978e",
    ARQ_MODALIDADE: "685e6728fa793ba52f390a9b68f467ac9d5fdb8a",
}

BACKUP_DIR = Path(".r1_v2_backup_pre_candidato_dc72f429")
BACKUP_ORQ = BACKUP_DIR / ARQ_ORQ

IMPORT_ANCHOR = 'from mente_laylay.memoria_mental.contexto_imediato import (\n    referencia_app_quarentenavel_c1d,\n)\n'
IMPORT_NEW = 'from mente_laylay.memoria_mental.contexto_imediato import (\n    referencia_app_quarentenavel_c1d,\n)\nfrom mente_laylay.memoria_mental.compatibilidade_contexto import (\n    classificar_repeticao_curta,\n)\nfrom mente_laylay.memoria_mental.politica_reexecucao import (\n    intents_compativeis_repeticao,\n)\n\n# ROOT_R1_V2_FAIL_CLOSED_TIPADO_20260826\n'
RESOLVER_OLD = 'def resolver_repeticao_operacional_segura(ns: dict, texto: str) -> dict | None:\n    """Consulta a continuidade; em falha, deixa um diagnóstico acionável."""\n    resolver = ns.get(\'_resolver_repeticao_ultima_acao\')\n    if not callable(resolver):\n        return None\n    try:\n        repeticao = resolver(texto)\n        return repeticao if isinstance(repeticao, dict) else None\n    except Exception as erro:\n        registrar_falha_opcional(\n            ns,\n            \'continuidade_turno\',\n            \'falha_resolver_repeticao\',\n            erro,\n            classe=\'defeito\',\n            impacto=\'turno\',\n            fallback=\'conversa_sem_repeticao\',\n        )\n        return None\n'
RESOLVER_NEW = 'def consultar_repeticao_operacional_classificada_segura(\n    ns: dict,\n    texto: str,\n) -> dict:\n    """Preserva classificação, resultado e saúde da consulta separadamente.\n\n    ``None`` não volta a carregar dois significados arquiteturais. O turno pode\n    distinguir "não houve operação compatível" de "o resolvedor não respondeu"\n    sem criar uma segunda gramática de repetição.\n    """\n    classificacao: dict = {}\n    normalizar = ns.get(\'_normalizar_texto_com_apelidos\')\n    estado_classificacao = \'indisponivel\'\n\n    if callable(normalizar):\n        try:\n            classificacao = dict(\n                classificar_repeticao_curta(texto, normalizar) or {}\n            )\n            estado_classificacao = \'ok\'\n        except Exception as erro:\n            estado_classificacao = \'erro\'\n            registrar_falha_opcional(\n                ns,\n                \'continuidade_turno\',\n                \'falha_classificar_repeticao\',\n                erro,\n                classe=\'defeito\',\n                impacto=\'turno\',\n                fallback=\'classificacao_repeticao_indisponivel\',\n            )\n\n    resolver = ns.get(\'_resolver_repeticao_ultima_acao\')\n    if not callable(resolver):\n        return {\n            \'estado\': \'resolver_indisponivel\',\n            \'estado_classificacao\': estado_classificacao,\n            \'classificacao\': classificacao,\n            \'repeticao\': None,\n        }\n\n    try:\n        repeticao_bruta = resolver(texto)\n    except Exception as erro:\n        registrar_falha_opcional(\n            ns,\n            \'continuidade_turno\',\n            \'falha_resolver_repeticao\',\n            erro,\n            classe=\'defeito\',\n            impacto=\'turno\',\n            fallback=\'conversa_sem_repeticao\',\n        )\n        return {\n            \'estado\': \'resolver_erro\',\n            \'estado_classificacao\': estado_classificacao,\n            \'classificacao\': classificacao,\n            \'repeticao\': None,\n        }\n\n    return {\n        \'estado\': \'ok\',\n        \'estado_classificacao\': estado_classificacao,\n        \'classificacao\': classificacao,\n        \'repeticao\': (\n            dict(repeticao_bruta)\n            if isinstance(repeticao_bruta, dict)\n            else None\n        ),\n    }\n\n\ndef resolver_repeticao_operacional_segura(ns: dict, texto: str) -> dict | None:\n    """Compatibilidade pública: devolve só a operação recuperada."""\n    consulta = consultar_repeticao_operacional_classificada_segura(ns, texto)\n    repeticao = consulta.get(\'repeticao\')\n    return dict(repeticao) if isinstance(repeticao, dict) else None\n'
APPLY_ANCHOR = 'def _catalogo_apps_retarget_c1d(apps_map: object) -> dict[str, tuple[str, object]]:\n'
APPLY_HELPER = 'def aplicar_contrato_repeticao_classificada_ao_turno(\n    turno: dict,\n    *,\n    texto: str,\n    consulta: object,\n) -> dict:\n    """Congela a restrição lexical antes que contexto posterior a amplie.\n\n    Repetições genéricas mantêm o comportamento legado. Uma repetição tipada\n    só autoriza intents declaradas pela política semântica canônica. Quando a\n    fala foi tipada mas nenhum resultado autorizável existe, o turno ganha um\n    veto operacional sticky: contexto continua útil para conversa, nunca para\n    trocar LER por outro domínio.\n    """\n    resultado = dict(turno or {})\n    if turno_tem_veto_execucao(resultado):\n        return resultado\n\n    dados = dict(consulta or {}) if isinstance(consulta, dict) else {}\n    classificacao = dict(dados.get(\'classificacao\') or {})\n    repeticao = (\n        dict(dados.get(\'repeticao\') or {})\n        if isinstance(dados.get(\'repeticao\'), dict)\n        else None\n    )\n\n    if str(classificacao.get(\'tipo\') or \'\') != \'tipada\':\n        return aplicar_repeticao_operacional_ao_turno(resultado, repeticao)\n\n    acao_semantica = str(\n        classificacao.get(\'acao_semantica\') or \'\'\n    ).strip().upper()\n    permitidos = intents_compativeis_repeticao(acao_semantica)\n    intent = str(\n        (repeticao or {}).get(\'intent\') or \'\'\n    ).strip().upper()\n    params = (repeticao or {}).get(\'params\')\n\n    if (\n        bool(permitidos)\n        and intent in permitidos\n        and isinstance(params, dict)\n    ):\n        return aplicar_repeticao_operacional_ao_turno(\n            resultado,\n            {\'intent\': intent, \'params\': dict(params)},\n        )\n\n    estado_consulta = str(dados.get(\'estado\') or \'\').strip().casefold()\n    if estado_consulta == \'resolver_erro\':\n        motivo = (\n            \'repetição tipada reconhecida, mas o resolvedor falhou antes de \'\n            \'produzir operação semanticamente compatível\'\n        )\n    elif estado_consulta == \'resolver_indisponivel\':\n        motivo = (\n            \'repetição tipada reconhecida, mas o resolvedor de continuidade \'\n            \'está indisponível\'\n        )\n    elif not permitidos:\n        motivo = (\n            \'repetição tipada reconhecida sem política semântica de intents \'\n            \'compatíveis\'\n        )\n    elif repeticao:\n        motivo = (\n            \'repetição tipada produziu operação incompatível com a restrição \'\n            f\'{acao_semantica or "tipada"}\'\n        )\n    else:\n        motivo = (\n            \'repetição tipada sem operação reexecutável semanticamente \'\n            \'compatível\'\n        )\n\n    return aplicar_veto_canonico(\n        resultado,\n        texto=texto,\n        modalidade=\'comando\',\n        natureza=\'repeticao_tipificada_sem_operacao_compativel\',\n        motivo=motivo,\n        requer_esclarecimento=False,\n        origem_veto=\'repeticao_tipificada_fail_closed\',\n    )\n\n\n'
FLOW_OLD = '    # Uma revisão atual não pode ser reinterpretada como repetição da ação\n    # anterior só porque a proposta final contém "continua", "de novo" etc.\n    repeticao_operacional = (\n        None if revisao_detectada\n        else resolver_repeticao_operacional_segura(ns, texto)\n    )\n    if not turno_tem_veto_execucao(turno):\n        turno = aplicar_repeticao_operacional_ao_turno(turno, repeticao_operacional)\n    if repeticao_operacional:\n        ns[\'print\'](\n            f"🔁 [TURNO] repetição operacional autorizada | "\n            f"intent={str(repeticao_operacional.get(\'intent\') or \'-\')}"\n        )\n'
FLOW_NEW = '    # Uma revisão atual não pode ser reinterpretada como repetição da ação\n    # anterior só porque a proposta final contém "continua", "de novo" etc.\n    consulta_repeticao = (\n        {\n            \'estado\': \'suprimida_revisao\',\n            \'estado_classificacao\': \'suprimida_revisao\',\n            \'classificacao\': {},\n            \'repeticao\': None,\n        }\n        if revisao_detectada\n        else consultar_repeticao_operacional_classificada_segura(ns, texto)\n    )\n    repeticao_operacional = consulta_repeticao.get(\'repeticao\')\n    if not turno_tem_veto_execucao(turno):\n        turno = aplicar_contrato_repeticao_classificada_ao_turno(\n            turno,\n            texto=texto,\n            consulta=consulta_repeticao,\n        )\n    if repeticao_operacional and not turno_tem_veto_execucao(turno):\n        ns[\'print\'](\n            f"🔁 [TURNO] repetição operacional autorizada | "\n            f"intent={str(repeticao_operacional.get(\'intent\') or \'-\')}"\n        )\n    elif (\n        str(dict(consulta_repeticao.get(\'classificacao\') or {}).get(\'tipo\') or \'\')\n        == \'tipada\'\n        and turno_tem_veto_execucao(turno)\n        and str(turno.get(\'origem_veto_execucao_operacional\') or \'\')\n        == \'repeticao_tipificada_fail_closed\'\n    ):\n        ns[\'print\'](\n            "🛡️ [TURNO] repetição tipada sem operação compatível | "\n            f"estado={consulta_repeticao.get(\'estado\') or \'-\'}"\n        )\n'
TESTE = 'from __future__ import annotations\n\nimport inspect\n\nimport mente_laylay.cognicao.orquestrador_turno_runtime as orq\nfrom mente_laylay.cognicao.modalidade_turno import (\n    autoriza_execucao_efetiva,\n    turno_tem_veto_execucao,\n)\nfrom mente_laylay.memoria_mental.compatibilidade_contexto import (\n    resolver_repeticao_ultima_acao,\n)\nfrom mente_laylay.memoria_mental.contexto_compartilhado import (\n    estado_mental_inicial,\n    registrar_resultado_execucao,\n)\n\nMARCADOR = "ROOT_R1_V2_FAIL_CLOSED_TIPADO_20260826"\n# ROOT_R1_V2_FAIL_CLOSED_TIPADO_20260826\n\n\ndef _normalizar(texto: str) -> str:\n    return str(texto or "").casefold().strip(" .,!?:;")\n\n\ndef _registrar(\n    estado: dict,\n    *,\n    intent: str,\n    params: dict,\n    status: str,\n    executou: bool,\n    confirmado: bool,\n    texto: str,\n) -> dict:\n    return registrar_resultado_execucao(\n        estado,\n        {\n            "intent": intent,\n            "params": dict(params),\n            "alvo": (\n                params.get("alvo")\n                or params.get("caminho")\n                or ""\n            ),\n            "status": status,\n            "executou": executou,\n            "confirmado": confirmado,\n            "origem": "test_r1_v2",\n        },\n        texto,\n        executou,\n        origem="test_r1_v2",\n        status=status,\n    )\n\n\ndef _estado_iot() -> dict:\n    return _registrar(\n        estado_mental_inicial(),\n        intent="IOT_CONTROL",\n        params={"acao": "ligar", "alvo": "lampada_quarto"},\n        status="ligado",\n        executou=True,\n        confirmado=True,\n        texto="Liga a lâmpada.",\n    )\n\n\ndef _estado_leitura_depois_iot() -> dict:\n    estado = _registrar(\n        estado_mental_inicial(),\n        intent="FILE_READ",\n        params={\n            "caminho": r"C:\\tmp\\r1_v2_alfa.txt",\n            "alvo": "r1_v2_alfa.txt",\n        },\n        status="conteudo_lido",\n        executou=True,\n        confirmado=True,\n        texto="Leia r1_v2_alfa.txt.",\n    )\n    return _registrar(\n        estado,\n        intent="IOT_CONTROL",\n        params={"acao": "ligar", "alvo": "lampada_quarto"},\n        status="ligado",\n        executou=True,\n        confirmado=True,\n        texto="Liga a lâmpada.",\n    )\n\n\ndef _estado_delete_falho() -> dict:\n    return _registrar(\n        estado_mental_inicial(),\n        intent="DELETE_ITEM",\n        params={"alvo": r"C:\\tmp\\r1_v2_inexistente.txt"},\n        status="nao_encontrado",\n        executou=False,\n        confirmado=False,\n        texto="Apaga r1_v2_inexistente.txt.",\n    )\n\n\ndef _turno_stale(texto: str) -> dict:\n    return {\n        "id": "r1-v2-turno",\n        "texto": texto,\n        "normalizado": _normalizar(texto),\n        "modalidade": "comando",\n        "modalidade_geral": "comando",\n        "ato_principal": "comando",\n        "acao_explicita": True,\n        "autoriza_execucao": True,\n        "requer_esclarecimento": False,\n        "depende_contexto": True,\n        "natureza_acao": "pedido_direto",\n        "confianca": 0.95,\n    }\n\n\ndef _ns(estado: dict, resolver=None) -> dict:\n    if resolver is None:\n        resolver = lambda texto: resolver_repeticao_ultima_acao(\n            texto,\n            estado,\n            _normalizar,\n        )\n    return {\n        "_normalizar_texto_com_apelidos": _normalizar,\n        "_resolver_repeticao_ultima_acao": resolver,\n    }\n\n\ndef _aplicar(estado: dict, texto: str, resolver=None) -> tuple[dict, dict]:\n    consulta = orq.consultar_repeticao_operacional_classificada_segura(\n        _ns(estado, resolver=resolver),\n        texto,\n    )\n    turno = orq.aplicar_contrato_repeticao_classificada_ao_turno(\n        _turno_stale(texto),\n        texto=texto,\n        consulta=consulta,\n    )\n    return turno, consulta\n\n\ndef test_a_leia_de_novo_com_file_read_compativel_preserva_execucao() -> None:\n    turno, consulta = _aplicar(\n        _estado_leitura_depois_iot(),\n        "Leia de novo.",\n    )\n    assert consulta["classificacao"]["tipo"] == "tipada"\n    assert consulta["classificacao"]["acao_semantica"] == "LER"\n    assert consulta["repeticao"]["intent"] == "FILE_READ"\n    assert turno_tem_veto_execucao(turno) is False\n    assert autoriza_execucao_efetiva(turno) is True\n    assert turno["repeticao_operacional"]["intent"] == "FILE_READ"\n\n\ndef test_d_de_novo_generico_preserva_retry_iot() -> None:\n    turno, consulta = _aplicar(_estado_iot(), "de novo")\n    assert consulta["classificacao"]["tipo"] == "generica"\n    assert consulta["repeticao"]["intent"] == "IOT_CONTROL"\n    assert turno_tem_veto_execucao(turno) is False\n    assert autoriza_execucao_efetiva(turno) is True\n    assert turno["repeticao_operacional"]["intent"] == "IOT_CONTROL"\n\n\ndef test_e_leia_de_novo_so_com_iot_publica_veto_sticky() -> None:\n    turno, consulta = _aplicar(_estado_iot(), "Leia de novo.")\n    assert consulta["estado"] == "ok"\n    assert consulta["classificacao"]["tipo"] == "tipada"\n    assert consulta["classificacao"]["acao_semantica"] == "LER"\n    assert consulta["repeticao"] is None\n    assert turno_tem_veto_execucao(turno) is True\n    assert autoriza_execucao_efetiva(turno) is False\n    assert turno["origem_veto_execucao_operacional"] == (\n        "repeticao_tipificada_fail_closed"\n    )\n    assert turno["natureza_acao"] == (\n        "repeticao_tipificada_sem_operacao_compativel"\n    )\n\n\ndef test_f1_leia_de_novo_nao_pode_refazer_delete_falho() -> None:\n    turno, consulta = _aplicar(\n        _estado_delete_falho(),\n        "Leia de novo.",\n    )\n    assert consulta["classificacao"]["tipo"] == "tipada"\n    assert consulta["repeticao"] is None\n    assert turno_tem_veto_execucao(turno) is True\n    assert autoriza_execucao_efetiva(turno) is False\n\n\ndef test_f2_tenta_de_novo_preserva_retry_delete_falho() -> None:\n    turno, consulta = _aplicar(\n        _estado_delete_falho(),\n        "tenta de novo",\n    )\n    assert consulta["classificacao"]["tipo"] == "generica"\n    assert consulta["repeticao"]["intent"] == "DELETE_ITEM"\n    assert turno_tem_veto_execucao(turno) is False\n    assert autoriza_execucao_efetiva(turno) is True\n    assert turno["repeticao_operacional"]["intent"] == "DELETE_ITEM"\n\n\ndef test_killer_resolvedor_incompativel_nao_pode_dar_iot_a_ler() -> None:\n    def resolver_defeituoso(_texto: str) -> dict:\n        return {\n            "intent": "IOT_CONTROL",\n            "params": {"acao": "ligar", "alvo": "lampada_quarto"},\n        }\n\n    turno, consulta = _aplicar(\n        _estado_iot(),\n        "Leia de novo.",\n        resolver=resolver_defeituoso,\n    )\n    assert consulta["classificacao"]["tipo"] == "tipada"\n    assert consulta["repeticao"]["intent"] == "IOT_CONTROL"\n    assert turno_tem_veto_execucao(turno) is True\n    assert autoriza_execucao_efetiva(turno) is False\n    assert "incompatível" in turno["motivo"]\n\n\ndef test_killer_erro_do_resolvedor_nao_reabre_turno_tipado() -> None:\n    def resolver_quebrado(_texto: str):\n        raise RuntimeError("falha sintética R1-V2")\n\n    turno, consulta = _aplicar(\n        _estado_iot(),\n        "Leia de novo.",\n        resolver=resolver_quebrado,\n    )\n    assert consulta["estado"] == "resolver_erro"\n    assert consulta["classificacao"]["tipo"] == "tipada"\n    assert consulta["repeticao"] is None\n    assert turno_tem_veto_execucao(turno) is True\n    assert autoriza_execucao_efetiva(turno) is False\n    assert "resolvedor falhou" in turno["motivo"]\n\n\ndef test_killer_resolvedor_ausente_nao_reabre_turno_tipado() -> None:\n    ns = {\n        "_normalizar_texto_com_apelidos": _normalizar,\n        "_resolver_repeticao_ultima_acao": None,\n    }\n    consulta = orq.consultar_repeticao_operacional_classificada_segura(\n        ns,\n        "Leia de novo.",\n    )\n    turno = orq.aplicar_contrato_repeticao_classificada_ao_turno(\n        _turno_stale("Leia de novo."),\n        texto="Leia de novo.",\n        consulta=consulta,\n    )\n    assert consulta["estado"] == "resolver_indisponivel"\n    assert consulta["classificacao"]["tipo"] == "tipada"\n    assert turno_tem_veto_execucao(turno) is True\n    assert autoriza_execucao_efetiva(turno) is False\n\n\ndef test_killer_veto_tipado_sobrevive_reautorizacao_stale() -> None:\n    turno, _consulta = _aplicar(_estado_iot(), "Leia de novo.")\n    reautorizado = orq.aplicar_repeticao_operacional_ao_turno(\n        turno,\n        {\n            "intent": "IOT_CONTROL",\n            "params": {"acao": "ligar", "alvo": "lampada_quarto"},\n        },\n    )\n    assert reautorizado["autoriza_execucao"] is True\n    assert turno_tem_veto_execucao(reautorizado) is True\n    assert autoriza_execucao_efetiva(reautorizado) is False\n\n\ndef test_wiring_orquestrador_usa_consulta_e_contrato_classificados() -> None:\n    fonte = inspect.getsource(orq)\n    assert MARCADOR in fonte\n    assert "consultar_repeticao_operacional_classificada_segura(ns, texto)" in fonte\n    assert "aplicar_contrato_repeticao_classificada_ao_turno(" in fonte\n    assert "origem_veto=\'repeticao_tipificada_fail_closed\'" in fonte\n'


class PatchError(RuntimeError):
    pass


def _git(repo: Path, *args: str, check: bool = True) -> str:
    p = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and p.returncode != 0:
        raise PatchError(
            f"git {' '.join(args)} falhou ({p.returncode}): "
            f"{p.stderr.strip() or p.stdout.strip()}"
        )
    return p.stdout.strip()


def localizar_repo() -> Path:
    candidatos = [Path.cwd().resolve(), Path(__file__).resolve().parent]
    vistos = set()
    for origem in candidatos:
        for pasta in (origem, *origem.parents):
            if pasta in vistos:
                continue
            vistos.add(pasta)
            if (pasta / ".git").exists() and (pasta / "laylay.py").is_file():
                return pasta
    raise PatchError(
        "Não encontrei a raiz da Laylay. Execute o aplicador dentro do repositório."
    )


def _validar_python(path: Path) -> None:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _preflight(repo: Path) -> None:
    head = _git(repo, "rev-parse", "HEAD")
    if head != HEAD_ESPERADO:
        raise PatchError(
            "HEAD divergente; não atualizar lock cegamente.\n"
            f"esperado={HEAD_ESPERADO}\natual   ={head}"
        )

    for rel, esperado in BLOBS_ESPERADOS.items():
        path = repo / rel
        if not path.is_file():
            raise PatchError(f"arquivo causal ausente: {rel}")
        atual = _git(repo, "rev-parse", f"HEAD:{rel.as_posix()}")
        if atual != esperado:
            raise PatchError(
                f"blob divergente: {rel}\n"
                f"esperado={esperado}\natual   ={atual}"
            )

    status_alvo = _git(
        repo, "status", "--porcelain", "--", ARQ_ORQ.as_posix(), check=False
    )
    if status_alvo.strip():
        raise PatchError(
            "orquestrador possui alteração local; candidato NÃO será aplicado:\n"
            + status_alvo
        )

    texto = (repo / ARQ_ORQ).read_text(encoding="utf-8")
    if MARCADOR in texto:
        raise PatchError("o candidato R1-V2 já parece aplicado")
    if (repo / ARQ_TESTE).exists():
        raise PatchError(f"{ARQ_TESTE} já existe; preserve e revise antes")
    if (repo / BACKUP_DIR).exists():
        raise PatchError(
            f"backup {BACKUP_DIR} já existe; não vou sobrescrever evidência"
        )


def _patch_orquestrador(texto: str) -> str:
    if texto.count(IMPORT_ANCHOR) != 1:
        raise PatchError("âncora de import não é única")
    texto = texto.replace(IMPORT_ANCHOR, IMPORT_NEW, 1)

    if texto.count(RESOLVER_OLD) != 1:
        raise PatchError("bloco do resolvedor seguro não é único")
    texto = texto.replace(RESOLVER_OLD, RESOLVER_NEW, 1)

    if texto.count(APPLY_ANCHOR) != 1:
        raise PatchError("âncora do helper de repetição não é única")
    texto = texto.replace(
        APPLY_ANCHOR,
        APPLY_HELPER + APPLY_ANCHOR,
        1,
    )

    if texto.count(FLOW_OLD) != 1:
        raise PatchError("bloco de integração da repetição não é único")
    texto = texto.replace(FLOW_OLD, FLOW_NEW, 1)

    if texto.count(MARCADOR) != 1:
        raise PatchError("marcador R1-V2 não ficou único na produção")
    return texto


def aplicar(repo: Path) -> None:
    _preflight(repo)

    alvo = repo / ARQ_ORQ
    teste = repo / ARQ_TESTE
    backup = repo / BACKUP_ORQ

    original = alvo.read_text(encoding="utf-8")
    novo = _patch_orquestrador(original)

    backup.parent.mkdir(parents=True, exist_ok=False)
    shutil.copy2(alvo, backup)

    try:
        alvo.write_text(novo, encoding="utf-8")
        teste.parent.mkdir(parents=True, exist_ok=True)
        teste.write_text(TESTE, encoding="utf-8")

        _validar_python(alvo)
        _validar_python(teste)

        diff_check = subprocess.run(
            [
                "git", "diff", "--check", "--",
                ARQ_ORQ.as_posix(), ARQ_TESTE.as_posix(),
            ],
            cwd=str(repo),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if diff_check.returncode != 0:
            raise PatchError(
                "git diff --check falhou:\n"
                + (diff_check.stdout.strip() or diff_check.stderr.strip())
            )
    except Exception:
        shutil.copy2(backup, alvo)
        if teste.exists():
            teste.unlink()
        raise

    print("\n✅ CANDIDATO R1-V2 APLICADO")
    print(f"produção : {ARQ_ORQ}")
    print(f"teste    : {ARQ_TESTE}")
    print(f"backup   : {BACKUP_ORQ}")
    print("\nNenhum commit/pull/reset/checkout foi executado.")
    print("\nPróximo comando focado:")
    print(
        r"python -m pytest tests\test_r1_v2_fail_closed_repeticao_tipificada.py -vv"
    )


def reverter(repo: Path) -> None:
    backup = repo / BACKUP_ORQ
    alvo = repo / ARQ_ORQ
    teste = repo / ARQ_TESTE

    if not backup.is_file():
        raise PatchError(f"backup ausente: {BACKUP_ORQ}")

    atual = alvo.read_text(encoding="utf-8") if alvo.is_file() else ""
    if MARCADOR not in atual:
        raise PatchError(
            "arquivo atual não contém marcador R1-V2; "
            "não vou sobrescrevê-lo automaticamente"
        )

    if teste.exists():
        texto_teste = teste.read_text(encoding="utf-8")
        if MARCADOR not in texto_teste:
            raise PatchError(
                f"{ARQ_TESTE} existe sem marcador do candidato; preservei"
            )

    shutil.copy2(backup, alvo)
    if teste.exists():
        teste.unlink()

    _validar_python(alvo)
    print("\n✅ CANDIDATO R1-V2 REVERTIDO PELO BACKUP")
    print(f"restaurado: {ARQ_ORQ}")
    print(f"removido : {ARQ_TESTE}")
    print(f"backup preservado em: {BACKUP_DIR}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reverter",
        action="store_true",
        help="restaura apenas o backup criado por este aplicador",
    )
    args = parser.parse_args()

    try:
        repo = localizar_repo()
        print("R1-V2 — CANDIDATO FAIL-CLOSED TIPADO")
        print("=" * 78)
        print(f"repo: {repo}")
        print(f"HEAD esperado: {HEAD_ESPERADO}")

        if args.reverter:
            reverter(repo)
        else:
            aplicar(repo)
        return 0
    except PatchError as exc:
        print("\n🟠 CANDIDATO NÃO APLICADO")
        print(exc)
        return 1
    except Exception as exc:
        print("\n🔴 FALHA INESPERADA DO APLICADOR")
        print(f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
