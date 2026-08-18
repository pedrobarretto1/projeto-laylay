#!/usr/bin/env python3
"""PATCH REAL C1-C — turno 156 `esquerda` / teste 3.8.

Self-contained e fail-closed.

Por padrão roda SOMENTE CHECK-ONLY.
Use --apply explicitamente para modificar os quatro arquivos de produção.

Não executa a Laylay e não toca em arquivos fora dos quatro alvos.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HEAD_TRAVADO = 'de749453599db0201f9f4cac20e2dc664d4a7b4a'
DIFF_SHA_TRAVADO = '88e0cd1e3ba52fb750fd90a332b8dad53ad3f6de51d5294b90841bb840e80e05'
MANIFEST_SHA256 = '562dc02c4e5d7fb03b63a062ebc51699282fa019dcda8a4f50b0e003729acf6d'

ALVOS = ('mente_laylay/cognicao/orquestrador_turno_runtime.py', 'mente_laylay/autonomia/orquestrador_deterministico.py', 'mente_laylay/autonomia/coordenador_intencao.py', 'mente_laylay/memoria_mental/continuidade_contexto.py')
BLOBS_HEAD = {'mente_laylay/cognicao/orquestrador_turno_runtime.py': '1c5497369afde2992d282124b6cc3f28c2659643', 'mente_laylay/autonomia/orquestrador_deterministico.py': '1ace7364d3ac9ef3530e7cd22607d6573f1c5b86', 'mente_laylay/autonomia/coordenador_intencao.py': '09431feecd3d083afc509770a4918e59d2111add', 'mente_laylay/memoria_mental/continuidade_contexto.py': '5fd03c85e9b53e2f72192bdde0bda6bd4c447a34'}
TRANSFORMACOES = {'mente_laylay/cognicao/orquestrador_turno_runtime.py': [('    return resultado\n\ndef reconciliar_alvo_eliptico_janela_confirmado(texto: str, *, turno: dict, retrato: dict, mente: dict) -> tuple[dict, dict]:\n', '    return resultado\n\n\ndef _forma_elipse_espacial_exata(texto: str) -> str:\n    """Retorna somente a direção espacial curta explicitamente coberta por C1-C."""\n    bruto = str(texto or "").casefold().strip()\n    return "left" if bruto == "esquerda" else ""\n\n\ndef _pendencia_conversacional_veta_elipse_espacial(pendencia: object) -> bool:\n    """Contexto conversacional pode reduzir autoridade; nunca criá-la."""\n    p = dict(pendencia or {}) if isinstance(pendencia, dict) else {}\n    dominio = str(p.get("dominio") or "").casefold()\n    origem = str(p.get("origem") or "").casefold()\n    tipo = str(p.get("tipo") or p.get("proposito") or "").casefold()\n    esperado = str(p.get("resposta_esperada") or "").casefold()\n    return bool(\n        dominio == "conversa"\n        and origem == "pergunta_aberta"\n        and (tipo in {"escolha", "escolha_atividade"} or esperado == "opcao")\n    )\n\n\ndef aplicar_elipse_espacial_autorizada_ao_turno(\n    texto: str,\n    *,\n    turno: dict,\n    pendencia_turno: object = None,\n) -> dict:\n    """Autoriza só a ação espacial dita agora; o alvo continua pendente."""\n    leitura = dict(turno or {})\n    direcao = _forma_elipse_espacial_exata(texto)\n    if not direcao:\n        return leitura\n    if _pendencia_conversacional_veta_elipse_espacial(pendencia_turno):\n        return leitura\n    leitura.update(\n        modalidade="comando",\n        modalidade_geral="comando",\n        ato_principal="comando",\n        texto_operacional="esquerda",\n        confianca=max(0.98, float(leitura.get("confianca") or 0.0)),\n        motivo="direção espacial elíptica explicitamente pedida",\n        motivo_decisao="direção espacial elíptica explicitamente pedida",\n        acao_explicita=True,\n        autoriza_execucao=True,\n        requer_esclarecimento=True,\n        depende_contexto=True,\n        natureza_acao="pedido_direto",\n        elipse_operacional={\n            "tipo": "posicionamento_janela",\n            "direcao": direcao,\n            "alvo_requerido": "app",\n        },\n    )\n    return leitura\n\n\ndef reconciliar_alvo_eliptico_janela_confirmado(texto: str, *, turno: dict, retrato: dict, mente: dict) -> tuple[dict, dict]:\n', 'v1/runtime/helpers'), ('def reconciliar_alvo_eliptico_janela_confirmado(texto: str, *, turno: dict, retrato: dict, mente: dict) -> tuple[dict, dict]:\n    """Resolve somente o alvo contextual comprovado do `maximiza` exato.\n\n    Não cria autoridade. A ação precisa já estar autorizada e o mesmo app\n    precisa existir simultaneamente em `ultimo_app_janela` e na entidade app\n    congelada do retrato.\n    """\n    leitura = dict(turno or {})\n    snapshot = dict(retrato or {})\n    forma = str(texto or "").casefold().strip(" \\t\\r\\n.,!?;:")\n    if forma != "maximiza":\n        return leitura, snapshot\n    if not bool(leitura.get("autoriza_execucao")):\n        return leitura, snapshot\n    if not bool(leitura.get("requer_esclarecimento")):\n        return leitura, snapshot\n    ultimo_app = str(dict(mente or {}).get("ultimo_app_janela") or "").strip()\n    entidade_app = dict(dict(snapshot.get("entidades") or {}).get("app") or {})\n    nome_app = str(entidade_app.get("nome") or "").strip()\n    if not ultimo_app or not nome_app:\n        return leitura, snapshot\n    if ultimo_app.casefold() != nome_app.casefold():\n        return leitura, snapshot\n    referencia = dict(entidade_app)\n    snapshot["referencia_tipo"] = "app"\n    snapshot["referencia_resolvida"] = referencia\n    leitura["requer_esclarecimento"] = False\n    leitura["depende_contexto"] = True\n    leitura["referencia_resolvida"] = referencia\n    leitura["alvo_contextual_resolvido"] = {\n        "tipo": "app", "nome": nome_app,\n        "origem": "elipse_operacional_maximiza_confirmada",\n    }\n    return leitura, snapshot\n', 'def reconciliar_alvo_eliptico_janela_confirmado(texto: str, *, turno: dict, retrato: dict, mente: dict) -> tuple[dict, dict]:\n    """Resolve alvo de janela já autorizado sem transformar contexto em autoridade."""\n    leitura = dict(turno or {})\n    snapshot = dict(retrato or {})\n    forma_max = str(texto or "").casefold().strip(" \\t\\r\\n.,!?;:")\n    forma_espacial = _forma_elipse_espacial_exata(texto)\n    elipse = dict(leitura.get("elipse_operacional") or {})\n\n    eh_maximiza = forma_max == "maximiza"\n    eh_espacial = bool(\n        forma_espacial\n        and str(elipse.get("tipo") or "") == "posicionamento_janela"\n        and str(elipse.get("direcao") or "") == forma_espacial\n        and str(elipse.get("alvo_requerido") or "") == "app"\n    )\n    if not (eh_maximiza or eh_espacial):\n        return leitura, snapshot\n    if not bool(leitura.get("autoriza_execucao")):\n        return leitura, snapshot\n    if not bool(leitura.get("requer_esclarecimento")):\n        return leitura, snapshot\n\n    ultimo_app = str(dict(mente or {}).get("ultimo_app_janela") or "").strip()\n    entidade_app = dict(dict(snapshot.get("entidades") or {}).get("app") or {})\n    nome_app = str(entidade_app.get("nome") or "").strip()\n    if not ultimo_app or not nome_app:\n        return leitura, snapshot\n    if ultimo_app.casefold() != nome_app.casefold():\n        return leitura, snapshot\n\n    referencia = dict(entidade_app)\n    snapshot["referencia_tipo"] = "app"\n    snapshot["referencia_resolvida"] = referencia\n    leitura["requer_esclarecimento"] = False\n    leitura["depende_contexto"] = True\n    leitura["referencia_resolvida"] = referencia\n    leitura["alvo_contextual_resolvido"] = {\n        "tipo": "app",\n        "nome": nome_app,\n        "origem": (\n            "elipse_operacional_maximiza_confirmada"\n            if eh_maximiza\n            else "elipse_operacional_espacial_confirmada"\n        ),\n    }\n    return leitura, snapshot\n', 'v1/runtime/reconcile'), ('    # Uma revisão atual não pode ser reinterpretada como repetição da ação\n    # anterior só porque a proposta final contém "continua", "de novo" etc.\n    repeticao_operacional = (\n', '    # C1-C: a direção atual pode conceder autoridade estreita por si.\n    # Uma escolha conversacional pendente só pode vetar essa autoridade.\n    turno = aplicar_elipse_espacial_autorizada_ao_turno(\n        texto,\n        turno=turno,\n        pendencia_turno=pendencia_turno,\n    )\n\n    # Uma revisão atual não pode ser reinterpretada como repetição da ação\n    # anterior só porque a proposta final contém "continua", "de novo" etc.\n    repeticao_operacional = (\n', 'v1/runtime/call'), ('def _pendencia_conversacional_veta_elipse_espacial(pendencia: object) -> bool:\n    """Contexto conversacional pode reduzir autoridade; nunca criá-la."""\n    p = dict(pendencia or {}) if isinstance(pendencia, dict) else {}\n    dominio = str(p.get("dominio") or "").casefold()\n    origem = str(p.get("origem") or "").casefold()\n    tipo = str(p.get("tipo") or p.get("proposito") or "").casefold()\n    esperado = str(p.get("resposta_esperada") or "").casefold()\n    return bool(\n        dominio == "conversa"\n        and origem == "pergunta_aberta"\n        and (tipo in {"escolha", "escolha_atividade"} or esperado == "opcao")\n    )\n', 'def _pendencia_veta_elipse_espacial(pendencia: object) -> bool:\n    """Uma fala curta ambígua nunca fura uma pendência ativa já falada."""\n    p = dict(pendencia or {}) if isinstance(pendencia, dict) else {}\n    if not p:\n        return False\n    status = str(p.get("status") or "").casefold()\n    foi_falada = p.get("foi_falada")\n    # No ciclo real `pendencia_turno` já veio de `pendencia_ativa`, mas esta\n    # guarda local mantém o helper fail-closed quando chamado isoladamente.\n    return bool(\n        status in {"", "ativa"}\n        and foi_falada is not False\n        and (p.get("id") or p.get("tipo") or p.get("origem"))\n    )\n', 'v3/runtime/veto'), ('    if _pendencia_conversacional_veta_elipse_espacial(pendencia_turno):\n        return leitura\n', '    if _pendencia_veta_elipse_espacial(pendencia_turno):\n        return leitura\n', 'v3/runtime/veto-call'), ('    # C1-C: a direção atual pode conceder autoridade estreita por si.\n    # Uma escolha conversacional pendente só pode vetar essa autoridade.\n', '    # C1-C: a direção atual pode conceder autoridade estreita por si.\n    # Qualquer pendência ativa já falada veta esta elipse ambígua; contexto só\n    # reduz autoridade e nunca fornece a permissão operacional da fala atual.\n', 'v4/runtime/comentario')], 'mente_laylay/autonomia/orquestrador_deterministico.py': [('def _call(ctx: Mapping[str, Any], nome: str, *args: Any, default: Any = None, **kwargs: Any) -> Any:\n    fn = _get(ctx, nome)\n    if callable(fn):\n        return fn(*args, **kwargs)\n    return default\n\n\ndef detectar_intencao_deterministica_mente(texto: str, ctx: Mapping[str, Any]) -> Dict[str, Any] | None:\n', 'def _call(ctx: Mapping[str, Any], nome: str, *args: Any, default: Any = None, **kwargs: Any) -> Any:\n    fn = _get(ctx, nome)\n    if callable(fn):\n        return fn(*args, **kwargs)\n    return default\n\n\ndef _detectar_elipse_espacial_confirmada(\n    texto: str,\n    mente: Mapping[str, Any] | None,\n) -> Dict[str, Any] | None:\n    """Materializa somente a elipse que o planejamento atual já autorizou."""\n    if str(texto or "").casefold().strip() != "esquerda":\n        return None\n    estado = dict(mente or {}) if isinstance(mente, Mapping) else {}\n    turno = dict(estado.get("turno_atual") or {})\n    if str(turno.get("texto") or "").casefold().strip() != "esquerda":\n        return None\n    if not bool(turno.get("autoriza_execucao")):\n        return None\n    if bool(turno.get("requer_esclarecimento")):\n        return None\n\n    elipse = dict(turno.get("elipse_operacional") or {})\n    if (\n        str(elipse.get("tipo") or "") != "posicionamento_janela"\n        or str(elipse.get("direcao") or "") != "left"\n        or str(elipse.get("alvo_requerido") or "") != "app"\n    ):\n        return None\n\n    referencia = dict(turno.get("referencia_resolvida") or {})\n    tipo = str(referencia.get("tipo") or "").casefold()\n    nome = str(referencia.get("nome") or "").strip()\n    if tipo not in {"app", "janela"} or not nome:\n        return None\n\n    return {\n        "intent": "ORGANIZAR_DESKTOP",\n        "params": {\n            "left": nome,\n            "modo": "posicionar",\n            "referencia_contextual": True,\n            "referencia_contextual_fonte": "turno_atual.referencia_resolvida",\n            "direcao_original": "esquerda",\n        },\n    }\n\n\ndef detectar_intencao_deterministica_mente(texto: str, ctx: Mapping[str, Any]) -> Dict[str, Any] | None:\n', 'v1/det/helper'), ('    mente_previa = _get(ctx, "mente_integrada_estado", {})\n    ultimo_intent_previo = str(\n', '    mente_previa = _get(ctx, "mente_integrada_estado", {})\n    elipse_espacial = _detectar_elipse_espacial_confirmada(texto, mente_previa)\n    if elipse_espacial:\n        return elipse_espacial\n\n    ultimo_intent_previo = str(\n', 'v1/det/call'), ('    if tipo not in {"app", "janela"} or not nome:\n        return None\n', '    if tipo != "app" or not nome:\n        return None\n', 'v3/det/app-only')], 'mente_laylay/autonomia/coordenador_intencao.py': [('    if intent == "ORGANIZAR_DESKTOP":\n        if str(params.get("modo") or "").casefold() == "automatico":\n            return True\n        lados = [\n            str(params.get(chave) or "").strip()\n            for chave in ("left", "right", "esquerda", "direita")\n            if str(params.get(chave) or "").strip()\n        ]\n        return bool(lados) and all(not valor_e_referencia_contextual(valor) for valor in lados)\n', '    if intent == "ORGANIZAR_DESKTOP":\n        if params.get("referencia_contextual") is True:\n            return False\n        if str(params.get("modo") or "").casefold() == "automatico":\n            return True\n        lados = [\n            str(params.get(chave) or "").strip()\n            for chave in ("left", "right", "esquerda", "direita")\n            if str(params.get(chave) or "").strip()\n        ]\n        return bool(lados) and all(not valor_e_referencia_contextual(valor) for valor in lados)\n', 'v1/coord/proveniencia'), ('    return False\n\n\ndef resolver_referencias_da_intencao(\n', '    return False\n\n\ndef _intencao_deterministica_depende_contexto_operacional(resultado: Any) -> bool:\n    """Separa herança operacional de referência linguística global."""\n    if not isinstance(resultado, dict):\n        return False\n    if _normalizar_intent(resultado) != "ORGANIZAR_DESKTOP":\n        return False\n    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}\n    return params.get("referencia_contextual") is True\n\n\ndef resolver_referencias_da_intencao(\n', 'v1/coord/helper'), ('    candidatos: list[CandidatoDecisao] = []\n    det_explicito = _intencao_deterministica_tem_alvo_explicito(intent_deterministica, texto_deteccao)\n    if isinstance(continuidade_aditiva, dict) and continuidade_aditiva:\n        candidatos.append(CandidatoDecisao(\n            tipo="comando_contextual",\n            valor=continuidade_aditiva,\n            origem="continuidade-aditiva",\n            confianca=0.97,\n            evidencia=("continuidade oficial compatível", "operação aditiva segura"),\n        ))\n    elif isinstance(intent_deterministica, dict) and (not depende_contexto or det_explicito):\n        candidatos.append(CandidatoDecisao(\n            tipo="comando_explicito",\n            valor=intent_deterministica,\n            origem="deterministico-explicito" if det_explicito else "deterministico",\n            confianca=0.98 if det_explicito else 0.90,\n            evidencia=("verbo operacional detectado", "alvo explicito" if det_explicito else "frase independente"),\n        ))\n', '    candidatos: list[CandidatoDecisao] = []\n    det_explicito = _intencao_deterministica_tem_alvo_explicito(intent_deterministica, texto_deteccao)\n    det_contexto_operacional = _intencao_deterministica_depende_contexto_operacional(\n        intent_deterministica\n    )\n    depende_contexto_deterministico = bool(\n        depende_contexto or det_contexto_operacional\n    )\n    if isinstance(continuidade_aditiva, dict) and continuidade_aditiva:\n        candidatos.append(CandidatoDecisao(\n            tipo="comando_contextual",\n            valor=continuidade_aditiva,\n            origem="continuidade-aditiva",\n            confianca=0.97,\n            evidencia=("continuidade oficial compatível", "operação aditiva segura"),\n        ))\n    elif isinstance(intent_deterministica, dict) and (\n        not depende_contexto_deterministico or det_explicito\n    ):\n        candidatos.append(CandidatoDecisao(\n            tipo="comando_explicito",\n            valor=intent_deterministica,\n            origem="deterministico-explicito" if det_explicito else "deterministico",\n            confianca=0.98 if det_explicito else 0.90,\n            evidencia=("verbo operacional detectado", "alvo explicito" if det_explicito else "frase independente"),\n        ))\n', 'v1/coord/flow'), ('    if depende_contexto and not continuidade_aditiva:\n        if isinstance(intent_deterministica, dict) and not det_explicito:\n            candidatos.append(CandidatoDecisao(\n                tipo="comando_contextual",\n                valor=intent_deterministica,\n                origem="deterministico-contextual",\n                confianca=0.62,\n                evidencia=("deteccao deterministica dependente de contexto",),\n            ))\n', '    if depende_contexto_deterministico and not continuidade_aditiva:\n        if isinstance(intent_deterministica, dict) and not det_explicito:\n            candidatos.append(CandidatoDecisao(\n                tipo="comando_contextual",\n                valor=intent_deterministica,\n                origem="deterministico-contextual",\n                confianca=0.62,\n                evidencia=(\n                    "deteccao deterministica dependente de contexto operacional"\n                    if det_contexto_operacional\n                    else "deteccao deterministica dependente de contexto",\n                ),\n            ))\n', 'v1/coord/contextual'), ('    if intent == "ORGANIZAR_DESKTOP":\n        if params.get("referencia_contextual") is True:\n            return False\n        if str(params.get("modo") or "").casefold() == "automatico":\n            return True\n        lados = [\n            str(params.get(chave) or "").strip()\n            for chave in ("left", "right", "esquerda", "direita")\n            if str(params.get(chave) or "").strip()\n        ]\n        return bool(lados) and all(not valor_e_referencia_contextual(valor) for valor in lados)\n', '    if intent == "ORGANIZAR_DESKTOP":\n        if _eh_elipse_espacial_c1c_contextual(resultado):\n            return False\n        if str(params.get("modo") or "").casefold() == "automatico":\n            return True\n        lados = [\n            str(params.get(chave) or "").strip()\n            for chave in ("left", "right", "esquerda", "direita")\n            if str(params.get(chave) or "").strip()\n        ]\n        return bool(lados) and all(not valor_e_referencia_contextual(valor) for valor in lados)\n', 'v2/coord/proveniencia'), ('    return False\n\n\ndef _intencao_deterministica_depende_contexto_operacional(resultado: Any) -> bool:\n    """Separa herança operacional de referência linguística global."""\n    if not isinstance(resultado, dict):\n        return False\n    if _normalizar_intent(resultado) != "ORGANIZAR_DESKTOP":\n        return False\n    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}\n    return params.get("referencia_contextual") is True\n\n\ndef resolver_referencias_da_intencao(\n', '    return False\n\n\ndef _eh_elipse_espacial_c1c_contextual(resultado: Any) -> bool:\n    if not isinstance(resultado, dict):\n        return False\n    if _normalizar_intent(resultado) != "ORGANIZAR_DESKTOP":\n        return False\n    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}\n    return bool(\n        params.get("referencia_contextual") is True\n        and str(params.get("referencia_contextual_fonte") or "")\n        == "turno_atual.referencia_resolvida"\n        and str(params.get("direcao_original") or "").casefold() == "esquerda"\n        and str(params.get("left") or "").strip()\n    )\n\n\ndef _intencao_deterministica_depende_contexto_operacional(resultado: Any) -> bool:\n    return _eh_elipse_espacial_c1c_contextual(resultado)\n\n\ndef resolver_referencias_da_intencao(\n', 'v2/coord/contexto'), ('    return False\n\n\ndef _eh_elipse_espacial_c1c_contextual(resultado: Any) -> bool:\n    if not isinstance(resultado, dict):\n        return False\n    if _normalizar_intent(resultado) != "ORGANIZAR_DESKTOP":\n        return False\n    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}\n    return bool(\n        params.get("referencia_contextual") is True\n        and str(params.get("referencia_contextual_fonte") or "")\n        == "turno_atual.referencia_resolvida"\n        and str(params.get("direcao_original") or "").casefold() == "esquerda"\n        and str(params.get("left") or "").strip()\n    )\n\n\ndef _intencao_deterministica_depende_contexto_operacional(resultado: Any) -> bool:\n    return _eh_elipse_espacial_c1c_contextual(resultado)\n\n\ndef resolver_referencias_da_intencao(\n', '    return False\n\n\ndef _eh_elipse_espacial_c1c_contextual(resultado: Any) -> bool:\n    """Reconhece somente o shape executável publicado pela elipse C1-C."""\n    if not isinstance(resultado, dict):\n        return False\n    if _normalizar_intent(resultado) != "ORGANIZAR_DESKTOP":\n        return False\n    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}\n    lados_extras = any(\n        str(params.get(chave) or "").strip()\n        for chave in ("right", "esquerda", "direita")\n    )\n    return bool(\n        str(params.get("modo") or "").casefold() == "posicionar"\n        and params.get("referencia_contextual") is True\n        and str(params.get("referencia_contextual_fonte") or "")\n        == "turno_atual.referencia_resolvida"\n        and str(params.get("direcao_original") or "").casefold() == "esquerda"\n        and str(params.get("left") or "").strip()\n        and not lados_extras\n    )\n\n\ndef _intencao_deterministica_depende_contexto_operacional(resultado: Any) -> bool:\n    return _eh_elipse_espacial_c1c_contextual(resultado)\n\n\ndef resolver_referencias_da_intencao(\n', 'v3/coord/shape'), ('    return False\n\n\ndef _eh_elipse_espacial_c1c_contextual(resultado: Any) -> bool:\n    """Reconhece somente o shape executável publicado pela elipse C1-C."""\n    if not isinstance(resultado, dict):\n        return False\n    if _normalizar_intent(resultado) != "ORGANIZAR_DESKTOP":\n        return False\n    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}\n    lados_extras = any(\n        str(params.get(chave) or "").strip()\n        for chave in ("right", "esquerda", "direita")\n    )\n    return bool(\n        str(params.get("modo") or "").casefold() == "posicionar"\n        and params.get("referencia_contextual") is True\n        and str(params.get("referencia_contextual_fonte") or "")\n        == "turno_atual.referencia_resolvida"\n        and str(params.get("direcao_original") or "").casefold() == "esquerda"\n        and str(params.get("left") or "").strip()\n        and not lados_extras\n    )\n\n\ndef _intencao_deterministica_depende_contexto_operacional(resultado: Any) -> bool:\n    return _eh_elipse_espacial_c1c_contextual(resultado)\n\n\ndef resolver_referencias_da_intencao(\n', '    return False\n\n\ndef _eh_elipse_espacial_c1c_contextual(resultado: Any) -> bool:\n    """Reconhece somente o shape exato publicado pela elipse C1-C."""\n    if not isinstance(resultado, dict):\n        return False\n    if _normalizar_intent(resultado) != "ORGANIZAR_DESKTOP":\n        return False\n    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}\n    chaves_esperadas = {\n        "left",\n        "modo",\n        "referencia_contextual",\n        "referencia_contextual_fonte",\n        "direcao_original",\n    }\n    if set(params) != chaves_esperadas:\n        return False\n    return bool(\n        str(params.get("modo") or "").casefold() == "posicionar"\n        and params.get("referencia_contextual") is True\n        and str(params.get("referencia_contextual_fonte") or "")\n        == "turno_atual.referencia_resolvida"\n        and str(params.get("direcao_original") or "").casefold() == "esquerda"\n        and str(params.get("left") or "").strip()\n    )\n\n\ndef _intencao_deterministica_depende_contexto_operacional(resultado: Any) -> bool:\n    return _eh_elipse_espacial_c1c_contextual(resultado)\n\n\ndef resolver_referencias_da_intencao(\n', 'v4/coord/chaves-exatas')], 'mente_laylay/memoria_mental/continuidade_contexto.py': [('    if any(s in base for s in ("qual voce prefere", "qual você prefere", "qual prefere", "qual deles", "qual delas", "uma ou outra", "ou prefere")):\n        return {"pergunta": pergunta, "proposito": "escolha", "resposta_esperada": "opcao"}\n    if any(s in base for s in ("quer que eu explique", "quer que eu detalhe", "posso explicar", "posso detalhar", "quer aprofundar", "quer ir mais fundo")):\n', '    if any(s in base for s in ("qual voce prefere", "qual você prefere", "qual prefere", "qual deles", "qual delas", "uma ou outra", "ou prefere")):\n        return {"pergunta": pergunta, "proposito": "escolha", "resposta_esperada": "opcao"}\n    if re.search(\n        r"\\b(?:voce|você|tu)\\s+prefere\\b[^?]{1,120}\\bou\\b[^?]{1,120}\\?\\s*$",\n        base,\n    ):\n        return {"pergunta": pergunta, "proposito": "escolha", "resposta_esperada": "opcao"}\n    if any(s in base for s in ("quer que eu explique", "quer que eu detalhe", "posso explicar", "posso detalhar", "quer aprofundar", "quer ir mais fundo")):\n', 'v1/conversa/escolha'), ('    if any(s in base for s in ("qual voce prefere", "qual você prefere", "qual prefere", "qual deles", "qual delas", "uma ou outra", "ou prefere")):\n        return {"pergunta": pergunta, "proposito": "escolha", "resposta_esperada": "opcao"}\n    if re.search(\n        r"\\b(?:voce|você|tu)\\s+prefere\\b[^?]{1,120}\\bou\\b[^?]{1,120}\\?\\s*$",\n        base,\n    ):\n        return {"pergunta": pergunta, "proposito": "escolha", "resposta_esperada": "opcao"}\n    if any(s in base for s in ("quer que eu explique", "quer que eu detalhe", "posso explicar", "posso detalhar", "quer aprofundar", "quer ir mais fundo")):\n', '    if any(s in base for s in ("qual voce prefere", "qual você prefere", "qual prefere", "qual deles", "qual delas", "uma ou outra", "ou prefere")):\n        return {"pergunta": pergunta, "proposito": "escolha", "resposta_esperada": "opcao"}\n    if re.search(\n        r"\\b(?:voce|você|tu)\\s+prefere\\b[^?]{0,120}\\b"\n        r"(?:esquerda\\b[^?]{0,60}\\bou\\b[^?]{0,60}\\bdireita|"\n        r"direita\\b[^?]{0,60}\\bou\\b[^?]{0,60}\\besquerda)\\b[^?]*\\?\\s*$",\n        base,\n    ):\n        return {"pergunta": pergunta, "proposito": "escolha", "resposta_esperada": "opcao"}\n    if any(s in base for s in ("quer que eu explique", "quer que eu detalhe", "posso explicar", "posso detalhar", "quer aprofundar", "quer ir mais fundo")):\n', 'v2/conversa/escolha-espacial')]}


class FalhaPrecondicao(RuntimeError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repo: Path, *args: str) -> str:
    p = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if p.returncode != 0:
        raise FalhaPrecondicao(
            f"git {' '.join(args)} falhou: {p.stderr.strip() or p.stdout.strip()}"
        )
    return p.stdout.strip()


def _git_blob_sha(data: bytes) -> str:
    cabecalho = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(cabecalho + data).hexdigest()


def _replace_once(src: str, old: str, new: str, label: str) -> str:
    n = src.count(old)
    if n != 1:
        raise FalhaPrecondicao(
            f"âncora {label} encontrada {n} vezes; esperado=1"
        )
    return src.replace(old, new, 1)


def _gerar_candidatos(repo: Path):
    originais = {}
    finais = {}
    for rel in ALVOS:
        path = repo / rel
        if not path.is_file():
            raise FalhaPrecondicao(f"arquivo alvo ausente: {rel}")
        bruto = path.read_bytes()
        originais[rel] = bruto

        blob_worktree = _git_blob_sha(bruto)
        if blob_worktree != BLOBS_HEAD[rel]:
            raise FalhaPrecondicao(
                f"arquivo alvo não está byte-a-byte no baseline HEAD: {rel} "
                f"esperado={BLOBS_HEAD[rel]} observado={blob_worktree}"
            )

        texto = bruto.decode("utf-8")
        for old, new, label in TRANSFORMACOES[rel]:
            texto = _replace_once(texto, old, new, label)
        ast.parse(texto, filename=rel)
        finais[rel] = texto.encode("utf-8")
    return originais, finais


def _udiff(rel: str, old: bytes, new: bytes) -> str:
    a = old.decode("utf-8").splitlines(keepends=True)
    b = new.decode("utf-8").splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            a, b,
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
            n=5,
        )
    )


def _diff_congelado(originais, finais):
    blocos = [_udiff(rel, originais[rel], finais[rel]) for rel in sorted(ALVOS)]
    diff = "\n".join(blocos)
    return _sha256(diff.encode("utf-8")), diff


def _verificar_repo(repo: Path):
    if not (repo / ".git").exists():
        raise FalhaPrecondicao("a pasta informada não é a raiz de um clone Git")

    head = _git(repo, "rev-parse", "HEAD")
    if head != HEAD_TRAVADO:
        raise FalhaPrecondicao(
            f"HEAD divergente: esperado={HEAD_TRAVADO} observado={head}"
        )

    for rel, esperado in BLOBS_HEAD.items():
        observado = _git(repo, "rev-parse", f"HEAD:{rel}")
        if observado != esperado:
            raise FalhaPrecondicao(
                f"blob HEAD divergente em {rel}: esperado={esperado} observado={observado}"
            )

    staged_alvos = _git(repo, "diff", "--cached", "--name-only", "--", *ALVOS)
    if staged_alvos.strip():
        raise FalhaPrecondicao(
            "há alterações staged em arquivos C1-C; não vou sobrepor:\n" + staged_alvos
        )

    cached_antes = _git(repo, "diff", "--cached", "--binary")
    return cached_antes


def _aplicar_com_rollback(repo: Path, finais, originais):
    temporarios = []
    substituidos = []
    try:
        for rel in ALVOS:
            destino = repo / rel
            fd, nome = tempfile.mkstemp(
                prefix=f".{destino.name}.c1c_",
                suffix=".tmp",
                dir=str(destino.parent),
            )
            os.close(fd)
            tmp = Path(nome)
            tmp.write_bytes(finais[rel])
            ast.parse(tmp.read_text(encoding="utf-8"), filename=rel)
            temporarios.append((tmp, destino))

        for tmp, destino in temporarios:
            rel = destino.relative_to(repo).as_posix()
            os.replace(tmp, destino)
            substituidos.append(rel)

    except Exception:
        for rel in substituidos:
            (repo / rel).write_bytes(originais[rel])
        for tmp, _destino in temporarios:
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass
        raise


def executar(repo: Path, aplicar: bool) -> int:
    try:
        print("C1-C PATCH REAL — TESTE 3.8")
        print(f"repo: {repo}")
        print(f"HEAD travado: {HEAD_TRAVADO}")
        print(f"diff travado: {DIFF_SHA_TRAVADO}")
        print(f"modo: {'APPLY' if aplicar else 'CHECK-ONLY'}\n")

        cached_antes = _verificar_repo(repo)
        print("A HEAD + 4 blobs travados............................... PASS")
        print("B staged nos 4 alvos.................................... NÃO")

        if _sha256(repr(TRANSFORMACOES).encode("utf-8")) != MANIFEST_SHA256:
            raise FalhaPrecondicao("manifesto interno de transformações foi alterado")
        print("C manifesto interno travado por SHA..................... PASS")

        originais, finais = _gerar_candidatos(repo)
        print("D âncoras únicas + AST final............................ PASS")

        if set(originais) != set(ALVOS) or set(finais) != set(ALVOS):
            raise FalhaPrecondicao("changed-set interno não é exatamente os 4 alvos")
        if any(originais[r] == finais[r] for r in ALVOS):
            raise FalhaPrecondicao("um dos quatro arquivos não teria mudança")
        print("E changed-set candidato................................. PASS | 4 arquivos")

        diff_sha, _diff = _diff_congelado(originais, finais)
        if diff_sha != DIFF_SHA_TRAVADO:
            raise FalhaPrecondicao(
                f"SHA do diff divergente: esperado={DIFF_SHA_TRAVADO} observado={diff_sha}"
            )
        print("F SHA do diff congelado................................. PASS")
        print(f"  {diff_sha}")

        if not aplicar:
            print("\n✅ CHECK-ONLY VERDE — produção NÃO alterada")
            print("   Para aplicar: execute o mesmo arquivo com --apply")
            return 0

        _aplicar_com_rollback(repo, finais, originais)

        for rel in ALVOS:
            observado = (repo / rel).read_bytes()
            if observado != finais[rel]:
                raise FalhaPrecondicao(f"pós-condição falhou em {rel}")
            ast.parse(observado.decode("utf-8"), filename=rel)

        cached_depois = _git(repo, "diff", "--cached", "--binary")
        if cached_depois != cached_antes:
            raise FalhaPrecondicao("index/staging mudou durante o patch")

        finais_pos = {rel: (repo / rel).read_bytes() for rel in ALVOS}
        diff_pos_sha, _ = _diff_congelado(originais, finais_pos)
        if diff_pos_sha != DIFF_SHA_TRAVADO:
            raise FalhaPrecondicao("arquivos aplicados não reproduzem o diff congelado")

        print("G aplicação nos 4 arquivos.............................. PASS")
        print("H AST pós-aplicação...................................... PASS")
        print("I index/staging preservado............................... PASS")
        print("J diff pós-aplicação = SHA soberano..................... PASS")
        print()
        print("✅ C1-C PATCH V4 APLICADO À PRODUÇÃO")
        print("   arquivos modificados: EXATAMENTE 4")
        print("   Git mutante: NÃO")
        print("   C1-C fechada: NÃO")
        print("   próximo: regressivos focados + runtime canônico + chaos")
        return 0

    except FalhaPrecondicao as exc:
        print(f"\n❌ PATCH RECUSADO / PROVA INCONCLUSIVA — {exc}")
        return 1
    except Exception as exc:
        print(f"\n❌ PATCH RECUSADO / PROVA INCONCLUSIVA — {type(exc).__name__}: {exc}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Patcher real e travado do C1-C v4.")
    parser.add_argument("--repo", default=".", help="raiz do clone Git")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="aplica os quatro arquivos; sem esta flag roda somente CHECK-ONLY",
    )
    args = parser.parse_args()
    return executar(Path(args.repo).expanduser().resolve(), bool(args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
