"""Pós-processamento da resposta da IA na Laylay."""

from __future__ import annotations

import ast
import json
import re
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from mente_laylay.memoria_mental.memoria_confiavel import (
    extrair_aprendizados_pessoais_explicitos,
    normalizar_texto as normalizar_texto_memoria,
    preparar_aprendizados_confirmados,
)
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.leitura_semantica_turno import normalizar_leitura_semantica
from mente_laylay.cognicao.guardiao_alegacoes import fala_adia_resposta_sem_continuacao
from mente_laylay.cognicao.guardiao_realidade_pessoal import (
    detectar_experiencia_pessoal_inventada,
    remover_trechos_de_realidade_inventada,
)
from mente_laylay.personalidade.higiene_fala import remover_residuos_operacionais
from mente_laylay.personalidade.proporcao_resposta import parece_problema_matematico
from mente_laylay.personalidade.contingencia_natural import fala_contingencia_natural
from mente_laylay.personalidade.autoria_conversacional import criar_fala_autoral
from mente_laylay.cognicao.contratos_turno import ContratoRespostaTurno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao,
    contingencia_comunicacao,
    montar_mensagens_reparo_comunicacao,
)
from mente_laylay.integracao.registro_conversa_llm import resolver_enviador_modelo
from mente_laylay.autonomia.higiene_resposta_ia import (
    _fala_contingencia_sem_llm,
    _fala_entregavel,
    _fala_representa_falha_tecnica_llm,
    _normalizar_envelope_contrato_escapado,
    _recuperar_fala_no_mesmo_turno,
    _saida_conversacional_recuperavel_localmente,
    corrigir_saida_malformada_da_ia,
    limpar_resposta_da_ia,
)


_ACOES_QUE_EXIGEM_PEDIDO_ATUAL = {
    "open_url", "open_app", "close_app", "close_tab", "close_specific_tab",
    "youtube_search", "youtube_play", "youtube_control",
    "capturar_tela", "organizar_desktop", "maximize_window",
    "criar_pasta", "criar_arquivo", "deletar_item", "delete_item",
    "ligar", "desligar", "alternar", "agendar_lembrete",
    "ler_emails", "ler_emails_urgentes", "sincronizar_emails",
    "ler_notificacoes", "silenciar_notificacoes", "ativar_notificacoes",
    "fechar_abas_paradas", "lock_pc", "tocar_playlist",
    "adicionar_playlist", "adicionar_a_playlist",
    "listar_agendamentos", "cancelar_agendamento",
}

_EMOCOES_RESPOSTA_IA = {
    "calma": "calma",
    "neutra": "calma",
    "alegre": "alegre",
    "feliz": "alegre",
    "animada": "alegre",
    "debochada": "debochada",
    "envergonhada": "envergonhada",
    "surpresa": "surpresa",
    "triste": "triste",
    "decepcionada": "triste",
    "irritada": "irritada",
    "nervosa": "irritada",
    "brava": "brava",
    "acalmando-se": "acalmando-se",
}


def filtrar_comandos_sem_pedido_atual(
    texto_usuario: str,
    comandos: List[dict],
    *,
    tipo_interacao: str = "",
) -> Tuple[List[dict], List[str]]:
    """Impede que conversa seja convertida em ação prática pela saída da IA."""
    lista = [comando for comando in (comandos or []) if isinstance(comando, dict)]
    if not lista:
        return lista, []
    decisao = classificar_modalidade_turno(
        texto_usuario,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    if bool(decisao.get("autoriza_execucao")):
        return lista, []

    permitidos: List[dict] = []
    bloqueados: List[str] = []
    for comando in lista:
        acao = str(comando.get("acao") or comando.get("action") or "").strip().casefold()
        if acao in _ACOES_QUE_EXIGEM_PEDIDO_ATUAL:
            bloqueados.append(acao)
        else:
            permitidos.append(comando)
    return permitidos, bloqueados


_PROMESSA_ENTREGA_NO_PROXIMO_PASSO = re.compile(
    r"\b(?:vou|vamos)\s+(?:fazer|resolver|calcular|mostrar|explicar|desenvolver|"
    r"come[cç]ar|expandir|simplificar)\b|"
    r"\b(?:vou|vamos)\s+(?:fazer|come[cç]ar)\s+(?:o|a|os|as)\s+"
    r"(?:c[aá]lculo|conta|passos?|resolu[cç][aã]o)\b|"
    r"\bquer\s+que\s+eu\s+(?:mostre|resolva|calcule|continue|explique)\b|"
    r"\bquer\s+(?:ver|os\s+passos?|a\s+resolu[cç][aã]o)\b",
    re.IGNORECASE,
)
_CONCLUSAO_MATEMATICA = re.compile(
    r"\b(?:portanto|logo|conclu[ií]mos|solu[cç][aã]o|resultado(?:\s+final)?|"
    r"sem\s+solu[cç][aã]o|n[aã]o\s+(?:tem|possui)\s+solu[cç][aã]o|"
    r"infinitas?\s+solu[cç][oõ]es)\b|"
    r"\b[xyz]\s*(?:=|[ée]\s+igual\s+a)\s*-?\s*\d",
    re.IGNORECASE,
)


def resposta_precisa_continuacao_autonoma(
    texto_usuario: str,
    fala: str,
    comandos: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """Detecta tarefa prometida, mas ainda não entregue no turno atual.

    A continuação é restrita a respostas conceituais: nunca autoriza comando,
    clique ou outra ação prática. Em matemática, uma introdução sem resultado
    é incompleta mesmo que o modelo não diga literalmente que responderá depois.
    """
    if comandos:
        return False
    pedido = str(texto_usuario or "").strip()
    resposta = re.sub(r"\s+", " ", str(fala or "")).strip()
    if not pedido or not resposta:
        return False
    if fala_adia_resposta_sem_continuacao(resposta):
        return True
    if parece_problema_matematico(pedido):
        return not bool(_CONCLUSAO_MATEMATICA.search(resposta))
    pedido_explicito = bool(re.search(
        r"\b(?:resolv[ae]|calcule|explique|analise|demonstre|mostre\s+os\s+passos)\b",
        pedido,
        flags=re.IGNORECASE,
    ))
    return bool(pedido_explicito and _PROMESSA_ENTREGA_NO_PROXIMO_PASSO.search(resposta))


def extrair_aprendizados_da_ia(resposta_bruta: Any) -> List[Any]:
    original = str(resposta_bruta or "").strip()
    if not original:
        return []

    texto_pre = re.sub(r"^```(?:json)?\s*", "", original, flags=re.IGNORECASE)
    texto_pre = re.sub(r"\s*```$", "", texto_pre, flags=re.IGNORECASE).strip()

    candidatos: Any = []
    try:
        dados = json.loads(texto_pre)
        if isinstance(dados, dict):
            candidatos = dados.get("aprendizados") or dados.get("aprendizado") or []
    except Exception:
        try:
            match = re.search(r'["\']?aprendizados?["\']?\s*:\s*(\[[\s\S]*?\]|["\'][\s\S]*?["\'])', texto_pre, re.IGNORECASE)
            if match:
                raw = match.group(1).strip()
                try:
                    candidatos = json.loads(raw)
                except Exception:
                    candidatos = ast.literal_eval(raw)
        except Exception:
            candidatos = []

    if isinstance(candidatos, str):
        candidatos = [candidatos]
    if not isinstance(candidatos, list):
        return []

    aprendizados: List[Any] = []
    for item in candidatos:
        if isinstance(item, dict):
            if any(str(item.get(k) or "").strip() for k in ("gatilho", "valor", "regra", "texto")):
                aprendizados.append(item)
            continue
        txt = str(item or "").strip()
        if len(txt) >= 8 and txt.lower() not in {"none", "nenhum", "n/a", "null"}:
            aprendizados.append(txt)
    return aprendizados


def salvar_aprendizados_da_ia(
    resposta_bruta: Any,
    memoria_sqlite: Any,
    texto_usuario: str = "",
) -> List[Any]:
    aprendizados_ia = extrair_aprendizados_da_ia(resposta_bruta)
    explicitos = extrair_aprendizados_pessoais_explicitos(texto_usuario)
    # O extrator determinístico preserva literalmente o que a pessoa disse e
    # tem precedência sobre interpretações criativas do modelo. Quando ele já
    # confirmou uma preferência, identidade ou regra, outra versão do mesmo
    # tipo gerada pela LLM não pode transformá-la em instruções inventadas.
    tipos_explicitos = {
        normalizar_texto_memoria(item.get("tipo"))
        for item in explicitos if isinstance(item, dict)
    }
    aprendizados: List[Any] = list(explicitos)
    for item in aprendizados_ia:
        if explicitos and not isinstance(item, dict):
            continue
        tipo = (
            normalizar_texto_memoria(item.get("tipo"))
            if isinstance(item, dict) else ""
        )
        if tipo and tipo in tipos_explicitos:
            continue
        aprendizados.append(item)
    unicos: List[Any] = []
    assinaturas = set()
    for item in aprendizados:
        assinatura = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, dict) else str(item)
        if assinatura.casefold() in assinaturas:
            continue
        assinaturas.add(assinatura.casefold())
        unicos.append(item)
    aprendizados = unicos
    if not aprendizados:
        return []
    confirmados = preparar_aprendizados_confirmados(aprendizados, texto_usuario)
    rejeitados = len(aprendizados) - len(confirmados)
    if rejeitados:
        print(
            f"🧠 [MEMÓRIA:FILTRO] {rejeitados} aprendizado(s) sem evidência do usuário foram descartados."
        )
    if not confirmados:
        return []
    try:
        salvos_semanticos = memoria_sqlite.salvar_aprendizados_semanticos(confirmados)
        print(
            f"🧠 [MEMÓRIA] {len(salvos_semanticos)} aprendizado(s) confirmado(s) salvo(s): "
            f"{confirmados[:2]}"
        )
    except Exception as e:
        print(f"⚠️ [MEMÓRIA] Falha ao salvar aprendizados da IA: {e}")
        return []
    return confirmados


def extrair_tipo_interacao_da_ia(resposta_bruta: Any) -> str:
    original = str(resposta_bruta or "").strip()
    if not original:
        return ""
    texto_pre = re.sub(r"^```(?:json)?\s*", "", original, flags=re.IGNORECASE)
    texto_pre = re.sub(r"\s*```$", "", texto_pre, flags=re.IGNORECASE).strip()
    try:
        dados = json.loads(texto_pre)
        if isinstance(dados, dict):
            tipo = str(dados.get("tipo_interacao") or dados.get("tipo") or "").strip().lower()
            if tipo in {"acao", "conversa", "aprendizado", "confirmacao"}:
                return tipo
    except Exception:
        pass
    try:
        match = re.search(r'["\']?tipo_interacao["\']?\s*:\s*["\']([^"\']+)["\']', texto_pre, re.IGNORECASE)
        if match:
            tipo = match.group(1).strip().lower()
            if tipo in {"acao", "conversa", "aprendizado", "confirmacao"}:
                return tipo
    except Exception:
        pass
    return ""


def extrair_emocao_da_ia(resposta_bruta: Any) -> Tuple[str, int]:
    """Lê a decisão emocional da LLM sem aceitar estados fora do avatar."""
    if isinstance(resposta_bruta, dict):
        dados = resposta_bruta
    else:
        bruto = str(resposta_bruta or "").strip()
        bruto = re.sub(r"^```(?:json)?\s*", "", bruto, flags=re.IGNORECASE)
        bruto = re.sub(r"\s*```$", "", bruto, flags=re.IGNORECASE).strip()
        bruto = _normalizar_envelope_contrato_escapado(bruto)
        try:
            dados = json.loads(bruto)
        except Exception:
            dados = {}
            emocao_match = re.search(
                r'["\']?(?:emocao|emoção|emotion)["\']?\s*:\s*["\']([^"\']+)["\']',
                bruto,
                flags=re.IGNORECASE,
            )
            nivel_match = re.search(
                r'["\']?(?:nivel_emocao|nível_emoção|emotion_level)["\']?\s*:\s*(\d+)',
                bruto,
                flags=re.IGNORECASE,
            )
            if emocao_match:
                dados["emocao"] = emocao_match.group(1)
            if nivel_match:
                dados["nivel_emocao"] = nivel_match.group(1)
    if not isinstance(dados, dict):
        return "", 0
    bruta = str(dados.get("emocao") or dados.get("emotion") or "").strip().casefold()
    emocao = _EMOCOES_RESPOSTA_IA.get(bruta, "")
    if not emocao:
        return "", 0
    try:
        nivel = int(dados.get("nivel_emocao") or dados.get("emotion_level") or 1)
    except (TypeError, ValueError):
        nivel = 1
    return emocao, max(1, min(3, nivel))


def extrair_leitura_semantica_da_ia(resposta_bruta: Any, texto_usuario: str) -> Dict[str, Any]:
    """Extrai a compreensão produzida junto da fala, sem interpretar comandos."""
    if isinstance(resposta_bruta, dict):
        dados = resposta_bruta
    else:
        bruto = str(resposta_bruta or "").strip()
        bruto = re.sub(r"^```(?:json)?\s*", "", bruto, flags=re.IGNORECASE)
        bruto = re.sub(r"\s*```$", "", bruto, flags=re.IGNORECASE).strip()
        try:
            dados = json.loads(bruto)
        except Exception:
            return {}
    if not isinstance(dados, dict):
        return {}
    valor = dados.get("leitura_turno")
    if isinstance(valor, list):
        tipos = [str(item or "").strip().lower() for item in valor if str(item or "").strip()]
        if not tipos:
            return {}
        tipos_pergunta = {"pergunta", "pergunta_opiniao", "pergunta_capacidade"}
        if len(tipos) > 1:
            modalidade = "misto"
        elif tipos[0] == "pedido_acao":
            modalidade = "comando"
        elif tipos[0] in tipos_pergunta:
            modalidade = "pergunta"
        elif tipos[0] in {"correcao", "recusa", "confirmacao", "reacao", "deliberacao"}:
            modalidade = tipos[0]
        else:
            modalidade = "conversa"
        valor = {
            "atos": [
                {"tipo": tipo, "falante": "pedro", "confianca": 0.82}
                for tipo in tipos
            ],
            "modalidade_geral": modalidade,
            "ato_principal": tipos[-1],
            "operacional": {"pedido_real": "pedido_acao" in tipos},
            "confianca": 0.82,
        }
    if not isinstance(valor, dict):
        return {}
    return normalizar_leitura_semantica(
        valor,
        texto=texto_usuario,
        origem="llm_principal",
    )


def preparar_resposta_para_execucao(
    texto_usuario: str,
    resposta_bruta: Any,
    *,
    enviar_mensagem_cb: Optional[Callable[..., Any]] = None,
    modelo_llm: Any = None,
    limpar_texto_fala_cb: Optional[Callable[[str], str]],
    fallback_fala: str,
    memoria_sqlite: Any,
    registrar_autocorrecao_cb: Optional[Callable[..., Any]] = None,
    registrar_falha_cb: Optional[Callable[..., Any]] = None,
    contexto_contingencia: Mapping[str, Any] | None = None,
    contexto_comunicacao: Mapping[str, Any] | None = None,
    log: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Prepara a resposta da IA antes do dispatcher executar qualquer acao."""
    enviar_mensagem_cb = resolver_enviador_modelo(
        modelo_llm=modelo_llm,
        enviar_mensagem=enviar_mensagem_cb,
    )
    registrar_log = log or print
    texto = str(texto_usuario or "").strip()
    bot_raw = resposta_bruta
    falha_tecnica_llm = _fala_representa_falha_tecnica_llm(bot_raw)
    comunicacao_autocorrigida = False

    def registrar_falha_contingencia(codigo: str) -> None:
        if not callable(registrar_falha_cb):
            return
        try:
            registrar_falha_cb(
                "resposta_llm",
                codigo,
                classe="degradacao",
                impacto="turno",
                fallback="contingencia_conversacional",
            )
        except Exception:
            # Telemetria nunca substitui a contingência que está protegendo.
            return

    recuperavel_localmente = _saida_conversacional_recuperavel_localmente(bot_raw)
    corrigida = None
    if not recuperavel_localmente and not falha_tecnica_llm:
        corrigida = corrigir_saida_malformada_da_ia(
            texto,
            bot_raw,
            enviar_mensagem_cb,
        )
    else:
        registrar_log("🧹 [IA] Metadados removidos localmente sem uma segunda chamada ao modelo.")
    if corrigida:
        try:
            if callable(registrar_autocorrecao_cb):
                registrar_autocorrecao_cb(
                    "ia",
                    "saida malformada",
                    "saida reformatada para json valido",
                    "segunda passada de autocorreção da resposta da IA",
                )
        except Exception as erro_registro:
            registrar_log(
                f"⚠️ [AUTOCORREÇÃO] falha ao registrar correção da saída: {erro_registro}"
            )
        bot_raw = corrigida
        registrar_log("🍪 [AUTOCORREÇÃO] Saída da IA refeita em JSON válido antes de executar.")

    fala_limpa, comandos = limpar_resposta_da_ia(
        bot_raw,
        limpar_texto_fala_cb=limpar_texto_fala_cb,
        fallback_fala=fallback_fala,
    )
    realidade_bloqueada = False
    problemas_realidade = (
        detectar_experiencia_pessoal_inventada(fala_limpa)
        if not comandos else []
    )
    if problemas_realidade and callable(enviar_mensagem_cb):
        registrar_log(
            "🧷 [IA:REALIDADE] pedindo reescrita à LLM | "
            + ",".join(problemas_realidade)
        )
        try:
            reparada_raw = enviar_mensagem_cb(
                [
                    {
                        "role": "system",
                        "content": (
                            "Reescreva a resposta mantendo a personalidade natural da Laylay, mas "
                            "remova experiências físicas, sentidos corporais, promessas de cozinhar "
                            "ou entregar objetos e acontecimentos compartilhados que não foram "
                            "afirmados pelo usuário. Laylay não tem corpo físico. Imaginação e humor "
                            "podem continuar, mas devem ser apresentados claramente como hipótese ou "
                            "brincadeira atual, nunca como lembrança real. Se o usuário estiver corrigindo um erro, reconheça a "
                            "correção uma vez e abandone a história inventada. Não crie outra "
                            "explicação fictícia. Retorne apenas JSON válido com fala e comandos."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "mensagem_atual": texto[:800],
                                "resposta_a_corrigir": fala_limpa[:1200],
                                "problemas": problemas_realidade,
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                _com_tools=False,
                max_tokens=260,
                modo_rapido=True,
                _prioridade_interativa=True,
            )
            fala_reparada, comandos_reparados = limpar_resposta_da_ia(
                reparada_raw,
                limpar_texto_fala_cb=limpar_texto_fala_cb,
                fallback_fala=fallback_fala,
            )
            ainda_invalida = detectar_experiencia_pessoal_inventada(fala_reparada)
            if fala_reparada and not comandos_reparados and not ainda_invalida:
                fala_limpa = fala_reparada
                bot_raw = json.dumps(
                    {"fala": fala_reparada, "comandos": []}, ensure_ascii=False,
                )
                registrar_log("🧷 [IA:REALIDADE] reescrita factual aceita.")
            else:
                fala_segura = remover_trechos_de_realidade_inventada(fala_limpa)
                if fala_segura:
                    fala_limpa = fala_segura
                    bot_raw = json.dumps(
                        {"fala": fala_segura, "comandos": []}, ensure_ascii=False,
                    )
                    registrar_log("🧷 [IA:REALIDADE] trechos inventados removidos localmente.")
                else:
                    realidade_bloqueada = True
        except Exception as erro:
            fala_segura = remover_trechos_de_realidade_inventada(fala_limpa)
            if fala_segura:
                fala_limpa = fala_segura
                bot_raw = json.dumps(
                    {"fala": fala_segura, "comandos": []}, ensure_ascii=False,
                )
            else:
                realidade_bloqueada = True
            registrar_log(
                "⚠️ [IA:REALIDADE] reescrita falhou: "
                f"{type(erro).__name__}"
            )
    elif problemas_realidade:
        realidade_bloqueada = True
    # Prometer que vai pensar, calcular ou mostrar os passos ainda não conclui
    # a tarefa. A mente faz uma continuação interna, no mesmo turno, antes de
    # entregar a fala; nenhuma nova entrada do usuário é necessária.
    precisa_continuar = resposta_precisa_continuacao_autonoma(
        texto,
        fala_limpa,
        comandos,
    )
    if precisa_continuar and callable(enviar_mensagem_cb):
        try:
            tarefa_matematica = parece_problema_matematico(texto)
            resposta_imediata = enviar_mensagem_cb(
                [
                    {
                        "role": "system",
                        "content": (
                            "Conclua agora a tarefa original do usuário neste mesmo turno. A resposta "
                            "anterior foi apenas uma introdução ou promessa. Não peça permissão para "
                            "continuar, não diga que vai calcular, começar ou mostrar depois. Entregue "
                            + (
                                "o desenvolvimento necessário e o resultado final da matemática. "
                                if tarefa_matematica else
                                "a explicação ou conclusão que foi pedida. "
                            )
                            + "Se houver inconsistência, explique-a e ainda assim conclua. "
                            "Retorne apenas JSON válido no formato "
                            '{"fala":"...","comandos":[]}.'
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {"pergunta": texto[:1200], "resposta_incompleta": fala_limpa[:1200]},
                            ensure_ascii=False,
                        ),
                    },
                ],
                _com_tools=False,
                max_tokens=800 if tarefa_matematica else 420,
                modo_rapido=False,
                _prioridade_interativa=True,
            )
            fala_corrigida, comandos_corrigidos = limpar_resposta_da_ia(
                resposta_imediata,
                limpar_texto_fala_cb=limpar_texto_fala_cb,
                fallback_fala=fallback_fala,
            )
            ainda_incompleta = resposta_precisa_continuacao_autonoma(
                texto,
                fala_corrigida,
                comandos_corrigidos,
            )
            if fala_corrigida and not ainda_incompleta:
                bot_raw = resposta_imediata
                fala_limpa = fala_corrigida
                comandos = comandos_corrigidos
                registrar_log("🧠 [IA] Continuação autônoma concluiu a tarefa no mesmo turno.")
            else:
                registrar_log("⚠️ [IA] Continuação autônoma ainda veio incompleta; mantive a resposta segura.")
        except Exception as erro:
            registrar_log(f"⚠️ [IA] não consegui concluir a resposta autonomamente: {type(erro).__name__}")

    # O verificador estrutural acima protege formato e realidade. Esta etapa
    # observa o significado do turno: se a fala ficou pela metade, não entregou
    # o que prometeu ou abandonou o domínio confirmado, fazemos exatamente uma
    # nova tentativa com contexto curto. O rascunho rejeitado nunca vai para a
    # memória nem para o TTS.
    contexto_com = dict(contexto_comunicacao or {})
    plano_comunicacao = dict(contexto_com.get("plano_turno") or {})
    mensagens_comunicacao = list(contexto_com.get("mensagens") or [])
    ultima_resposta_comunicacao = next(
        (
            str(item.get("content") or "").strip()
            for item in reversed(mensagens_comunicacao)
            if isinstance(item, Mapping)
            and str(item.get("role") or "").strip().casefold() == "assistant"
            and str(item.get("content") or "").strip()
        ),
        "",
    )
    falas_recentes_comunicacao = [
        str(item.get("content") or "").strip()
        for item in mensagens_comunicacao
        if isinstance(item, Mapping)
        and str(item.get("role") or "").strip().casefold() == "assistant"
        and str(item.get("content") or "").strip()
    ][-5:]
    avaliacao_comunicacao = (
        avaliar_qualidade_comunicacao(
            texto,
            fala_limpa,
            plano=plano_comunicacao,
            ultima_resposta=ultima_resposta_comunicacao,
        )
        if not comandos and not falha_tecnica_llm and not realidade_bloqueada
        else {"aceita": True, "problemas": [], "foco": {}}
    )
    if avaliacao_comunicacao.get("requer_reparo"):
        problemas = list(avaliacao_comunicacao.get("problemas") or [])
        somente_consultiva = bool(avaliacao_comunicacao.get("somente_consultiva"))
        registrar_log(
            "🧭 [COMUNICAÇÃO] "
            + ("observação consultiva | " if somente_consultiva else "reparo semântico solicitado | ")
            + ",".join(problemas)
        )
        if somente_consultiva:
            # Uma preferência estilística não pode apagar uma fala completa da
            # LLM. Ela fica disponível para diagnóstico e melhoria futura, mas
            # não adiciona latência, não chama reparo e não produz fallback.
            avaliacao_comunicacao = {**avaliacao_comunicacao, "requer_reparo": False}
        fala_reparada = ""
        reparo_modelo_indisponivel = False
        if not somente_consultiva and callable(enviar_mensagem_cb):
            try:
                reparada_raw = enviar_mensagem_cb(
                    montar_mensagens_reparo_comunicacao(
                        texto,
                        fala_limpa,
                        avaliacao_comunicacao,
                        mensagens=mensagens_comunicacao,
                    ),
                    _com_tools=False,
                    max_tokens=360,
                    modo_rapido=True,
                    timeout=12,
                    _prioridade_interativa=True,
                )
                reparo_modelo_indisponivel = _fala_representa_falha_tecnica_llm(
                    reparada_raw
                )
                candidata, comandos_reparo = limpar_resposta_da_ia(
                    reparada_raw,
                    limpar_texto_fala_cb=limpar_texto_fala_cb,
                    fallback_fala=fallback_fala,
                )
                segunda_avaliacao = avaliar_qualidade_comunicacao(
                    texto,
                    candidata,
                    plano=plano_comunicacao,
                    ultima_resposta=ultima_resposta_comunicacao,
                )
                if candidata and not comandos_reparo and segunda_avaliacao.get("aceita"):
                    fala_reparada = candidata
                elif candidata:
                    registrar_log(
                        "🧭 [COMUNICAÇÃO] reparo rejeitado | "
                        + ",".join(segunda_avaliacao.get("problemas") or ["motivo_desconhecido"])
                    )
            except Exception as erro:
                registrar_log(
                    "⚠️ [COMUNICAÇÃO] tentativa de reparo falhou: "
                    f"{type(erro).__name__}"
                )
        if somente_consultiva:
            pass
        elif fala_reparada:
            fala_limpa = fala_reparada
            bot_raw = json.dumps(
                {"fala": fala_reparada, "comandos": []},
                ensure_ascii=False,
            )
            comunicacao_autocorrigida = True
            registrar_log("🧭 [COMUNICAÇÃO] resposta reparada antes da fala e da memória.")
        else:
            fala_segura = contingencia_comunicacao(
                texto,
                foco=avaliacao_comunicacao.get("foco"),
                contrato_reparo=avaliacao_comunicacao.get("contrato_reparo"),
                falas_evitar=falas_recentes_comunicacao,
            )
            autoria = criar_fala_autoral(
                texto,
                fala_segura,
                enviar_mensagem=None if reparo_modelo_indisponivel else enviar_mensagem_cb,
                mensagens=mensagens_comunicacao,
                foco=avaliacao_comunicacao.get("foco"),
                contrato_reparo=avaliacao_comunicacao.get("contrato_reparo"),
            )
            fala_limpa = fala_segura
            if autoria.usada_llm:
                avaliacao_autoral = avaliar_qualidade_comunicacao(
                    texto,
                    autoria.fala,
                    plano=plano_comunicacao,
                    ultima_resposta=ultima_resposta_comunicacao,
                )
                if avaliacao_autoral.get("aceita"):
                    fala_limpa = autoria.fala
                    comunicacao_autocorrigida = True
                    registrar_log(
                        "✍️ [COMUNICAÇÃO] Laylay criou a contingência final com voz própria."
                    )
                else:
                    registrar_log(
                        "⚠️ [COMUNICAÇÃO] autoria final rejeitada | "
                        + ",".join(
                            avaliacao_autoral.get("problemas")
                            or ["contrato_nao_preservado"]
                        )
                    )
            else:
                registrar_log(
                    "⚠️ [COMUNICAÇÃO] autoria final indisponível | "
                    f"motivo={autoria.motivo_fallback or 'desconhecido'}"
                )
            bot_raw = json.dumps(
                {"fala": fala_limpa, "comandos": []},
                ensure_ascii=False,
            )
            estrategia_reparo = str(
                dict(avaliacao_comunicacao.get("contrato_reparo") or {}).get("estrategia") or ""
            )
            if autoria.usada_llm and fala_limpa == autoria.fala:
                registrar_log(
                    "🧭 [COMUNICAÇÃO] turno recuperado pela autoria conversacional."
                )
            elif estrategia_reparo == "reacao_social_curta":
                comunicacao_autocorrigida = True
                registrar_log(
                    "🧭 [COMUNICAÇÃO] reação social recuperada sem expor o reparo."
                )
            else:
                registrar_falha_contingencia("qualidade_comunicacao_nao_reparada")
                registrar_log(
                    "🧭 [COMUNICAÇÃO] reparo indisponível; usei contingência contextual."
                )
    tipo_interacao = extrair_tipo_interacao_da_ia(bot_raw)
    emocao_resposta, nivel_emocao_resposta = extrair_emocao_da_ia(bot_raw)
    leitura_semantica = extrair_leitura_semantica_da_ia(bot_raw, texto)
    suprimir_fala = False
    if realidade_bloqueada:
        fala_limpa = contingencia_comunicacao(
            texto,
            falas_evitar=falas_recentes_comunicacao,
        )
        bot_raw = json.dumps({"fala": fala_limpa, "comandos": []}, ensure_ascii=False)
        registrar_log(
            "⚠️ [IA:REALIDADE] invenção pessoal substituída por contingência contextual."
        )
    elif not comandos and falha_tecnica_llm:
        fala_limpa = _fala_contingencia_sem_llm(texto, contexto_contingencia)
        registrar_log("🛟 [IA] Contingência conversacional manteve o turno aberto.")
    elif not comandos and not _fala_entregavel(fala_limpa, fallback_fala):
        fala_reparada = _recuperar_fala_no_mesmo_turno(
            texto,
            bot_raw,
            enviar_mensagem_cb=enviar_mensagem_cb,
            limpar_texto_fala_cb=limpar_texto_fala_cb,
            fallback_fala=fallback_fala,
        )
        if fala_reparada:
            fala_limpa = fala_reparada
            registrar_log("🛟 [IA] Resposta refeita e concluída no mesmo turno.")
        else:
            fala_limpa = _fala_contingencia_sem_llm(texto, contexto_contingencia)
            registrar_falha_contingencia("saida_nao_entregavel")
            registrar_log("🛟 [IA] Saída vazia; contingência manteve o turno aberto.")
    registrar_log(
        f"✨ [IA] Fala limpa: '{fala_limpa}' | "
        f"Tipo: {tipo_interacao or 'legado'} | Comandos: {len(comandos)}"
    )
    aprendizados = salvar_aprendizados_da_ia(bot_raw, memoria_sqlite, texto)

    if tipo_interacao in {"aprendizado", "conversa"} and comandos:
        acoes_bloqueadas = [
            str(comando.get("acao", ""))
            for comando in comandos
            if isinstance(comando, dict)
        ]
        registrar_log(
            f"🧠 [INTENÇÃO] tipo={tipo_interacao}; bloqueando "
            f"{len(comandos)} comando(s): {acoes_bloqueadas}"
        )
        comandos = []

    comandos, bloqueados_sem_pedido = filtrar_comandos_sem_pedido_atual(
        texto,
        comandos,
        tipo_interacao=tipo_interacao,
    )
    if bloqueados_sem_pedido:
        registrar_log(
            "🛡️ [AUTORIZAÇÃO] conversa sem pedido prático; bloqueando ações da IA: "
            f"{bloqueados_sem_pedido}"
        )

    return ContratoRespostaTurno(
        resposta_bruta=bot_raw,
        fala=fala_limpa,
        comandos=tuple(comandos),
        tipo_interacao=tipo_interacao,
        aprendizados=tuple(aprendizados),
        leitura_semantica=leitura_semantica,
        autocorrigida=bool(corrigida or comunicacao_autocorrigida),
        suprimir_fala=suprimir_fala,
        emocao=emocao_resposta,
        nivel_emocao=nivel_emocao_resposta,
    ).como_dict()
