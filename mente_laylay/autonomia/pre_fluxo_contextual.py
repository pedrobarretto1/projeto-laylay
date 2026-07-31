"""Helpers compartilhados para o pre-fluxo conversacional da Laylay."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Iterable, Tuple

from mente_laylay.arquivos.lixeira_laylay import existe_exclusao_pendente
from mente_laylay.cognicao.conversa_sobre_capacidades import texto_discute_capacidade_futura
from mente_laylay.cognicao.modalidade_turno import texto_tem_pergunta_reciproca_apos_resposta
from mente_laylay.memoria_mental.sessao_conversa import texto_encerra_conversa
from mente_laylay.memoria_mental.continuidade_conversa import (
    detectar_comentario_resultado_operacional,
)
from mente_laylay.personalidade.conversa_natural import (
    texto_parece_correcao_conversacional,
    tipo_reconhecimento_afetivo,
)
from mente_laylay.personalidade.proporcao_resposta import parece_problema_matematico
from mente_laylay.memoria_mental.identidade_usuario import normalizar_nome_usuario
from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_local,
)


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def _modalidade_turno(ctx: Dict[str, Any]) -> str:
    mente = _get(ctx, "mente_integrada_estado", {})
    turno = mente.get("turno_atual") if isinstance(mente, dict) else {}
    return str((turno or {}).get("modalidade") or "").strip().lower()


def _decisao_turno(ctx: Dict[str, Any]) -> Dict[str, Any]:
    mente = _get(ctx, "mente_integrada_estado", {})
    turno = mente.get("turno_atual") if isinstance(mente, dict) else {}
    return dict(turno or {}) if isinstance(turno, dict) else {}


def turno_tem_pergunta_nova_apos_trecho_social(ctx: Dict[str, Any], texto: str) -> bool:
    """Detecta turno composto mesmo se um retrato transitório estiver atrasado."""
    decisao = _decisao_turno(ctx)
    segmentos = [
        item for item in list(decisao.get("segmentos") or [])
        if isinstance(item, dict)
    ]
    modalidades = {str(item.get("modalidade") or "") for item in segmentos}
    if len(segmentos) > 1 and "pergunta" in modalidades and len(modalidades) > 1:
        return True

    # Perguntas recíprocas omitem o substantivo já mencionado: "e o seu?"
    # significa "e o seu dia?". Essa estrutura precisa funcionar mesmo quando
    # o retrato do turno ainda é o anterior.
    if texto_tem_pergunta_reciproca_apos_resposta(texto):
        return True

    bruto = re.sub(r"\s+", " ", str(texto or "").strip().casefold())
    # O retrato mental pode ainda representar o turno anterior. Nesse caso,
    # detectamos a pergunta nova diretamente no texto. Além de vírgula e
    # ponto e vírgula, frases naturais costumam separar os atos com ponto ou
    # exclamação: "estou bem também. Você gosta de Slipknot?".
    partes = [
        parte.strip()
        for parte in re.split(r"[,;]|[.!](?=\s)", bruto)
        if parte.strip()
    ]
    if len(partes) < 2 or not partes[-1].endswith("?"):
        return False
    sufixo = partes[-1]
    sufixo = re.sub(r"^(?:lay|laylay)\s*[,;:]?\s*", "", sufixo)
    return bool(re.match(
        r"^(?:(?:e|mas)\s+)?(?:voc[eê]|tu|quem|qual|quais|o\s+que|como|"
        r"quando|onde|por\s+que)\b",
        sufixo,
    ))


def texto_eh_conversa_social_sem_comando(ctx: Dict[str, Any], texto: str) -> bool:
    texto_social_curto = _get(ctx, "_texto_social_curto")
    texto_conversa_casual_sem_acao = _get(ctx, "_texto_conversa_casual_sem_acao")
    texto_tem_comando_explicito = _get(ctx, "_texto_tem_comando_explicito")
    t = str(texto or "").strip()
    if not t:
        return False
    # Uma correção não pode ser encerrada pelo atalho de conversa casual. Ela
    # precisa seguir para o contexto completo, ainda que algum classificador
    # anterior tenha marcado o turno como agradecimento ou reação social.
    if _modalidade_turno(ctx) == "correcao" or texto_parece_correcao_conversacional(t):
        return False
    eh_social = (
        (callable(texto_social_curto) and texto_social_curto(t))
        or (callable(texto_conversa_casual_sem_acao) and texto_conversa_casual_sem_acao(t))
    )
    if not eh_social:
        return False
    if callable(texto_tem_comando_explicito) and texto_tem_comando_explicito(t):
        if texto_discute_capacidade_futura(t):
            return True
        return False
    if texto_discute_capacidade_futura(t):
        return True
    return True


def texto_deve_evitar_llm_de_comando(ctx: Dict[str, Any], texto: str) -> bool:
    """Evita mandar conversa casual para o analisador de comando."""
    texto_tem_comando_explicito = _get(ctx, "_texto_tem_comando_explicito")
    texto_conversa_contextual_sem_comando = _get(ctx, "_texto_conversa_contextual_sem_comando")
    t = str(texto or "").strip()
    if not t:
        return True
    decisao = _decisao_turno(ctx)
    modalidade = str(decisao.get("modalidade_geral") or decisao.get("modalidade") or "").lower()
    if decisao and (
        decisao.get("requer_esclarecimento")
        or (
            modalidade in {"conversa", "pergunta", "deliberacao", "correcao", "reacao"}
            and not decisao.get("autoriza_execucao")
        )
    ):
        return True
    if texto_discute_capacidade_futura(t):
        return True
    if callable(texto_tem_comando_explicito) and texto_tem_comando_explicito(t):
        return False
    if texto_eh_conversa_social_sem_comando(ctx, t):
        return True
    if callable(texto_conversa_contextual_sem_comando) and texto_conversa_contextual_sem_comando(t):
        return True
    return False


def analisar_intencao_com_porteiro(
    ctx: Dict[str, Any],
    texto: str,
) -> Tuple[str, Dict[str, Any] | None]:
    """Chama o analisador IA-first somente quando o porteiro permitir."""
    t = str(texto or "").strip()
    if not t:
        return "vazio", None
    if texto_deve_evitar_llm_de_comando(ctx, t):
        return "evitar", None

    analisar_intencao = _get(ctx, "analisar_intencao")
    if not callable(analisar_intencao):
        return "sem_analisador", None

    try:
        resultado = analisar_intencao(t)
    except Exception:
        return "falha", None

    if resultado is None:
        return "sem_intencao", None
    if not isinstance(resultado, dict):
        return "falha", None

    intent = str(resultado.get("intent") or "").upper().strip()
    if intent in {"", "NONE", "NENHUM"}:
        return "sem_intencao", None

    decisao = _decisao_turno(ctx)
    if "autoriza_execucao" in decisao and not bool(decisao.get("autoriza_execucao")):
        return "evitar", None

    # Uma classificação da IA não cria autorização prática. Intenções que
    # podem fechar, apagar ou inspecionar conteúdo exigem sinal operacional
    # explícito na fala atual; memória e contexto não bastam.
    exigem_sinal_atual = {
        "CLOSE_APP", "CLOSE_TAB", "DELETE_ITEM", "RESUMIR_PAGINA",
        "APP_OPEN", "OPEN_URL", "MAXIMIZE_WINDOW",
    }
    texto_tem_comando_explicito = _get(ctx, "_texto_tem_comando_explicito")
    if (
        intent in exigem_sinal_atual
        and (not callable(texto_tem_comando_explicito) or not texto_tem_comando_explicito(t))
    ):
        return "evitar", None

    return "ok", resultado


def emitir_conversa_curta(
    ctx: Dict[str, Any],
    texto_usuario: str,
    fala: str,
    *,
    emocao: str,
    nivel: int,
) -> bool:
    fala = str(fala or "").strip()
    if not fala:
        return False

    emitir_resposta_curta = _get(ctx, "_emitir_resposta_curta")
    if callable(emitir_resposta_curta):
        emitir_resposta_curta(
            texto_usuario,
            fala,
            emocao=emocao or "calma",
            nivel=nivel or 1,
            habilidade="conversa",
        )
        return True

    mensagens_append = _get(ctx, "mensagens_append")
    falar_com_lipsync = _get(ctx, "falar_com_lipsync")
    registrar_mente_curta = _get(ctx, "_registrar_mente_curta")
    salvar_memoria = _get(ctx, "salvar_memoria")

    if callable(mensagens_append):
        mensagens_append({"role": "user", "content": str(texto_usuario or "")})
        mensagens_append({"role": "assistant", "content": fala})
    if callable(falar_com_lipsync):
        falar_com_lipsync(fala, emocao or "calma", nivel or 1)
    if callable(registrar_mente_curta):
        registrar_mente_curta(str(texto_usuario or ""), fala, habilidade="conversa")
    if callable(salvar_memoria):
        salvar_memoria()
    return True


def processar_encerramento_conversa(
    ctx: Dict[str, Any], texto_usuario: str, *, emitir_fala: bool = True,
) -> Tuple[bool, str]:
    """Encerra o fio atual sem apagar fatos e aprendizados duradouros."""
    texto = str(texto_usuario or "").strip()
    if not texto_encerra_conversa(texto):
        return False, ""
    renovar = _get(ctx, "_renovar_sessao_conversa")
    if callable(renovar):
        renovar("despedida_usuario", False)
    falar = _get(ctx, "falar_com_lipsync")
    if emitir_fala and callable(falar):
        falar("Fechado. Encerramos por aqui; quando você voltar, começo por um contexto novo.", "calma", 1)
    salvar = _get(ctx, "salvar_memoria")
    if callable(salvar):
        salvar()
    # Na voz única, a limpeza da sessão acontece sem ocupar a autoria da
    # resposta. O chamador recebe a etapa, mas deixa o turno seguir à LLM.
    return bool(emitir_fala), "encerramento_conversa"


def processar_identidade_usuario(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    """Resolve correções explícitas do nome sem pedir interpretação à IA."""
    t = str(texto_usuario or "").strip()
    normalizar = _get(ctx, "_normalizar_texto_com_apelidos")
    norm = str(normalizar(t) if callable(normalizar) else t.casefold()).strip()
    mente = _get(ctx, "mente_integrada_estado", {})
    mente = mente if isinstance(mente, dict) else {}
    conhecido = normalizar_nome_usuario(mente.get("nome_usuario"))

    negacao = re.fullmatch(r"meu nome (?:nao|não) (?:e|é)\s+([a-zà-ÿ][a-zà-ÿ' -]{0,50})", norm, re.IGNORECASE)
    if negacao:
        nome_errado = str(negacao.group(1) or "").strip().title()
        if conhecido and conhecido.casefold() != nome_errado.casefold():
            fala = f"Você tem razão: seu nome é {conhecido}, não {nome_errado}. Eu puxei esse nome do contexto errado."
        else:
            fala = f"Certo, não vou te chamar de {nome_errado}. Você ainda não me ensinou qual nome prefere."
        return emitir_conversa_curta(ctx, t, fala, emocao="calma", nivel=1), "correcao_nome_usuario"

    afirmacao = re.fullmatch(
        r"(?:meu nome (?:e|é)|eu me chamo|me chamo|pode me chamar de|me chama de)\s+"
        r"([a-zà-ÿ][a-zà-ÿ' -]{0,50})",
        norm,
        re.IGNORECASE,
    )
    if not afirmacao:
        return False, ""
    nome = normalizar_nome_usuario(afirmacao.group(1))
    if not nome:
        return False, ""
    salvar_identidade = _get(ctx, "_salvar_identidade_usuario")
    if callable(salvar_identidade) and not bool(salvar_identidade(nome, t)):
        return emitir_conversa_curta(
            ctx, t,
            "Eu entendi o nome, mas não consegui guardá-lo com segurança agora.",
            emocao="calma", nivel=1,
        ), "identidade_usuario_falha_persistencia"
    mente["nome_usuario"] = nome
    fala = f"Prazer, {nome}. Agora sim: guardei seu nome do jeito certo."
    return emitir_conversa_curta(ctx, t, fala, emocao="calma", nivel=1), "identidade_usuario"


def processar_correcao_temporal(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    responder = _get(ctx, "_responder_correcao_temporal")
    if not callable(responder):
        return False, ""
    try:
        fala = str(responder(texto_usuario) or "").strip()
    except Exception:
        return False, ""
    if not fala:
        return False, ""
    return emitir_conversa_curta(
        ctx, texto_usuario, fala, emocao="calma", nivel=1
    ), "correcao_temporal"


def responder_conversa_social_curta(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    emocao: str,
    nivel: int,
) -> Tuple[bool, str]:
    t = str(texto_usuario or "").strip()
    resposta_conversa_rapida_local = _get(ctx, "_resposta_conversa_rapida_local")
    # A matemática local não é conversa social, portanto precisa ser tentada
    # antes do porteiro social que corretamente rejeita fórmulas.
    if parece_problema_matematico(t) and callable(resposta_conversa_rapida_local):
        fala_matematica = str(resposta_conversa_rapida_local(t) or "").strip()
        if fala_matematica and re.search(
            r"\bx\s+(?:é\s+igual|igual)\s+a\b|infinitas\s+solu[cç][oõ]es|"
            r"n[aã]o\s+tem\s+solu[cç][aã]o",
            fala_matematica, flags=re.IGNORECASE,
        ):
            return emitir_conversa_curta(
                ctx, t, fala_matematica, emocao="curiosa", nivel=1,
            ), "matematica_linear_local"
    if not texto_eh_conversa_social_sem_comando(ctx, t):
        return False, ""

    # Uma resposta social seguida de uma pergunta nova é um turno composto.
    # O atalho curto não pode consumir só a primeira metade e esconder a outra.
    if turno_tem_pergunta_nova_apos_trecho_social(ctx, t):
        return False, ""

    texto_social_curto = _get(ctx, "_texto_social_curto")
    texto_conversa_casual_sem_acao = _get(ctx, "_texto_conversa_casual_sem_acao")
    if not callable(resposta_conversa_rapida_local):
        return False, ""

    fala = resposta_conversa_rapida_local(t)
    if not str(fala or "").strip():
        return False, ""
    if callable(texto_social_curto) and texto_social_curto(t):
        return emitir_conversa_curta(ctx, t, fala, emocao=emocao, nivel=nivel), "conversa_social_curta"
    if callable(texto_conversa_casual_sem_acao) and texto_conversa_casual_sem_acao(t):
        return emitir_conversa_curta(ctx, t, fala, emocao=emocao, nivel=nivel), "conversa_casual_sem_acao"
    return False, ""


def processar_pergunta_curta_contextual(
    ctx: Dict[str, Any],
    texto_usuario: str,
) -> Tuple[bool, str]:
    resolver_pergunta_curta_contextual_intencao = _get(ctx, "_resolver_pergunta_curta_contextual_intencao")
    executar_intencao_curta_contextual = _get(ctx, "_executar_intencao_curta_contextual")
    executar_intencao = _get(ctx, "executar_intencao")

    t = str(texto_usuario or "").strip()
    if not callable(resolver_pergunta_curta_contextual_intencao):
        return False, ""

    intencao_curta = resolver_pergunta_curta_contextual_intencao(t)
    if not isinstance(intencao_curta, dict) or not str(intencao_curta.get("intent") or "").strip():
        return False, ""

    if callable(executar_intencao_curta_contextual):
        ok = bool(executar_intencao_curta_contextual(
            intencao_curta,
            t,
            origem="pre-ia",
            contexto_autoaprimoramento="pergunta curta dependente do topico",
        ))
        return ok, "pergunta_curta_contextual" if ok else ""

    ok = bool(executar_intencao(intencao_curta, t)) if callable(executar_intencao) else False
    return ok, "pergunta_curta_contextual_fallback" if ok else ""


def processar_resposta_pendencia_prioritaria(
    ctx: Dict[str, Any],
    texto_usuario: str,
) -> Tuple[bool, str]:
    """Resolve uma pendência realmente falada antes de herdar ação antiga."""
    if turno_tem_pergunta_nova_apos_trecho_social(ctx, texto_usuario):
        return False, ""
    mente = _get(ctx, "mente_integrada_estado", {})
    pendencia = mente.get("pendencia_atual") if isinstance(mente, dict) else {}
    resposta = re.sub(
        r"\s+", " ", str(texto_usuario or "").strip().casefold(),
    ).strip(" .,!?:;")
    pendencia_exclusao = bool(
        existe_exclusao_pendente()
        or (
            isinstance(pendencia, dict)
            and pendencia.get("status") == "ativa"
            and str(pendencia.get("origem") or "") == "lixeira_laylay"
        )
    )
    confirmar = resposta in {
        "sim", "pode", "pode apagar", "confirma", "confirmo",
        "manda pra lixeira", "manda para a lixeira",
    }
    cancelar = resposta in {
        "nao", "não", "cancela", "cancelar", "deixa", "deixa quieto",
    } or classificar_confirmacao_local(texto_usuario) is False
    confirmar_oferta = confirmar or resposta in {
        "quero", "quero sim", "claro", "bora", "manda", "pode ser",
    }
    oferta_musical = mente.get("oferta_pendente") if isinstance(mente, dict) else {}
    if (
        confirmar_oferta
        and isinstance(oferta_musical, dict)
        and oferta_musical.get("modo") == "recomendar_artista"
    ):
        recomendar = _get(ctx, "_recomendar_musica_verificada")
        artista = str(oferta_musical.get("contexto") or "").strip()
        if callable(recomendar) and artista:
            ok = bool(recomendar(artista, str(texto_usuario or "").strip()))
            return ok, "recomendacao_musical_verificada" if ok else ""
    if pendencia_exclusao and (confirmar or cancelar):
        executar = _get(ctx, "_executar_intencao_curta_contextual")
        if not callable(executar):
            return False, ""
        intencao = {
            "intent": "CONFIRM_DELETE_ITEM" if confirmar else "CANCEL_DELETE_ITEM",
            "params": {},
        }
        ok = bool(executar(
            intencao,
            str(texto_usuario or "").strip(),
            origem="confirmacao-exclusao",
            contexto_autoaprimoramento="resposta à confirmação da lixeira",
        ))
        return ok, "confirmacao_exclusao" if confirmar else "cancelamento_exclusao"
    if not isinstance(pendencia, dict) or pendencia.get("status") != "ativa" or not pendencia.get("foi_falada"):
        return False, ""
    if _modalidade_turno(ctx) in {"comando", "pergunta", "correcao", "deliberacao"}:
        return False, ""
    ok, nome = processar_pergunta_curta_contextual(ctx, texto_usuario)
    return ok, "pendencia_unificada" if ok else nome


def processar_continuacao_visao_jogo(
    ctx: Dict[str, Any], texto_usuario: str,
) -> Tuple[bool, str]:
    """Entrega um complemento à análise visual que realmente o solicitou."""
    decisao = _decisao_turno(ctx)
    modalidade = str(
        decisao.get("modalidade_geral") or decisao.get("modalidade") or ""
    ).casefold()
    # Uma pendência nunca pode sequestrar um pedido operacional novo. O
    # executor adequado terá a oportunidade de tratá-lo logo depois.
    if bool(decisao.get("autoriza_execucao")) or modalidade == "comando":
        return False, ""
    continuar = _get(ctx, "_continuar_visao_jogo_pendente")
    if not callable(continuar):
        return False, ""
    try:
        tratado = bool(continuar(str(texto_usuario or "").strip()))
    except Exception:
        tratado = False
    return tratado, "continuacao_visao_jogo" if tratado else ""


def processar_consulta_sistema_local(
    ctx: Dict[str, Any], texto_usuario: str,
) -> Tuple[bool, str]:
    """Responde inventários locais sem pedir ao modelo que os adivinhe."""
    t = re.sub(r"\s+", " ", str(texto_usuario or "").strip().casefold())
    if not re.search(
        r"\b(?:quais|que|lista|listar|mostra|mostrar)\b.*"
        r"\b(?:programas|aplicativos|apps|janelas)\b.*"
        r"\b(?:abert[oa]s?|rodando|execucao|execução)\b",
        t,
    ):
        return False, ""
    listar = _get(ctx, "listar_programas_abertos")
    if not callable(listar):
        return False, ""
    try:
        programas = [str(item).strip() for item in list(listar() or []) if str(item).strip()]
    except Exception:
        programas = []
    if programas:
        nomes = ", ".join(programas[:12])
        fala = f"Estão abertos agora: {nomes}."
    else:
        fala = "Não encontrei nenhum programa com janela visível agora."
    return emitir_conversa_curta(
        ctx, texto_usuario, fala, emocao="calma", nivel=1,
    ), "consulta_programas_abertos"


def processar_pergunta_aberta(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    emocao: str,
    nivel: int,
) -> Tuple[bool, str]:
    if turno_tem_pergunta_nova_apos_trecho_social(ctx, texto_usuario):
        return False, ""
    if _modalidade_turno(ctx) in {"pergunta", "comando", "correcao", "deliberacao"}:
        return False, ""
    texto_responde_pergunta_aberta = _get(ctx, "_texto_responde_pergunta_aberta")
    responder_pergunta_aberta = _get(ctx, "_responder_pergunta_aberta")

    t = str(texto_usuario or "").strip()
    if not callable(texto_responde_pergunta_aberta) or not texto_responde_pergunta_aberta(t):
        return False, ""
    fala = responder_pergunta_aberta(t) if callable(responder_pergunta_aberta) else ""
    return emitir_conversa_curta(ctx, t, fala, emocao=emocao, nivel=nivel), "pergunta_aberta"


def processar_elogio_ou_agradecimento(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    emocao: str,
    nivel: int,
) -> Tuple[bool, str]:
    parece_elogio_ou_agradecimento_curto = _get(ctx, "_parece_elogio_ou_agradecimento_curto")
    responder_agradecimento_ou_elogio = _get(ctx, "_responder_agradecimento_ou_elogio")
    t = str(texto_usuario or "").strip()
    if not callable(parece_elogio_ou_agradecimento_curto) or not parece_elogio_ou_agradecimento_curto(t):
        return False, ""
    fala = responder_agradecimento_ou_elogio(t) if callable(responder_agradecimento_ou_elogio) else ""
    # Gratidão pela ajuda é uma reação tímida leve; elogio dirigido à Laylay
    # mantém uma vergonha mais perceptível.
    nivel_reacao = 1 if tipo_reconhecimento_afetivo(t) == "agradecimento" else max(2, nivel)
    return emitir_conversa_curta(ctx, t, fala, emocao="envergonhada", nivel=nivel_reacao), "elogio_ou_agradecimento"


def processar_bloqueio_playlist_temporario(
    ctx: Dict[str, Any],
    texto_usuario: str,
) -> Tuple[bool, str]:
    texto_bloqueia_playlist_agora = _get(ctx, "_texto_bloqueia_playlist_agora")
    bloquear_playlist_temporariamente = _get(ctx, "_bloquear_playlist_temporariamente")
    t = str(texto_usuario or "").strip()
    if not callable(texto_bloqueia_playlist_agora) or not texto_bloqueia_playlist_agora(t):
        return False, ""
    if callable(bloquear_playlist_temporariamente):
        try:
            bloquear_playlist_temporariamente()
        except Exception:
            pass
    ok = emitir_conversa_curta(
        ctx,
        t,
        "Fechado, sem playlist agora. Guardei a caixinha de som.",
        emocao="calma",
        nivel=1,
    )
    return ok, "bloqueio_playlist" if ok else ""


def processar_feedback_pendente(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    texto_norm = re.sub(r"\s+", " ", str(texto_usuario or "").strip().casefold())
    contraproposta = bool(re.search(
        r"\b(?:melhor|prefiro|preferia|em vez|ao inves|ao invés|apenas|somente|só|so)\b",
        texto_norm,
    ))
    if _modalidade_turno(ctx) not in {"confirmacao", "recusa", "reacao"} and not contraproposta:
        return False, ""
    handle_feedback_pendente_misto = _get(ctx, "_handle_feedback_pendente_misto")
    handle_feedback_pendente = _get(ctx, "_handle_feedback_pendente")
    t = str(texto_usuario or "").strip()
    if callable(handle_feedback_pendente_misto) and handle_feedback_pendente_misto(t):
        return True, "feedback_pendente_misto"
    if callable(handle_feedback_pendente) and handle_feedback_pendente(t):
        return True, "feedback_pendente"
    return False, ""


def processar_sugestao_indireta(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    detectar = _get(ctx, "_detectar_sugestao_indireta")
    registrar = _get(ctx, "_registrar_sugestao_indireta")
    mente = _get(ctx, "mente_integrada_estado", {})
    if not callable(detectar) or not callable(registrar):
        return False, ""
    try:
        sugestao = detectar(str(texto_usuario or "").strip(), mente)
    except Exception:
        return False, ""
    if not isinstance(sugestao, dict):
        return False, ""
    ok = bool(registrar(sugestao, texto_usuario))
    return ok, "sugestao_indireta" if ok else ""


def processar_reparacao_conversacional(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    texto_norm = str(texto_usuario or "").casefold()
    # "não, Lay, faça X" é uma correção que já contém um novo comando
    # completo. O executor determinístico deve resolvê-lo e produzir apenas a
    # confirmação final, sem uma fala intermediária de reparação.
    comando_corrigido_explicito = bool(
        re.match(r"^\s*(?:nao|não|na verdade|eu quis dizer)\b", texto_norm)
        and (
            (re.search(r"\b(?:volume|som)\b", texto_norm) and re.search(r"\b(?:\d{1,3}|maximo|máximo|minimo|mínimo|mudo)\b", texto_norm))
            or (re.search(r"\b(?:email|emails|e-mail)\b", texto_norm) and re.search(r"\b(?:le|lê|leia|ler|mostra|verifica|resuma)\b", texto_norm))
            or bool(re.search(r"\b(?:cria|apaga|abre|fecha|liga|desliga|maximiza)\b", texto_norm))
        )
    )
    if comando_corrigido_explicito:
        return False, ""
    resolver = _get(ctx, "_resolver_reparacao_conversacional")
    if not callable(resolver):
        return False, ""
    try:
        reparacao = resolver(texto_usuario)
    except Exception as erro:
        print(f"⚠️ [REPARAÇÃO] falha ao analisar correção: {erro}")
        return False, ""
    if not isinstance(reparacao, dict):
        return False, ""

    alvo_anterior = str(reparacao.get("alvo_anterior") or "isso").strip()
    alvo_novo = str(reparacao.get("alvo_novo") or "").strip()
    falar = _get(ctx, "falar_com_lipsync")
    if reparacao.get("tipo") == "nao_suportada":
        if callable(falar):
            falar(
                f"Entendi a correção para {alvo_novo}, mas essa ação ainda não tem executor seguro. Não mexi em nada.",
                "calma",
                1,
            )
        return True, "reparacao_nao_suportada"
    if reparacao.get("tipo") != "operacional" or not isinstance(reparacao.get("intencao"), dict):
        if callable(falar):
            fala = (
                f"Ah, agora entendi: você está falando de {alvo_novo}."
                if alvo_novo
                else "Foi mal, eu puxei o contexto errado. Corrigi o rumo; pode continuar."
            )
            falar(fala, "calma", 1)
        return True, "reparacao_conversacional"

    if callable(falar):
        resumo = str(reparacao.get("resumo_correcao") or alvo_novo).strip()
        falar(f"Foi mal, corrigi: agora é {resumo}.", "calma", 1)
    ok = executar_resultado_contextual(
        ctx,
        reparacao["intencao"],
        texto_usuario,
        origem_resultado="reparacao_conversacional",
        contexto_autoaprimoramento="correcao imediata de alvo",
        log_rota="ROTEADOR REPARAÇÃO [pre-ia]",
    )
    return ok, "reparacao_operacional" if ok else ""


def processar_comentario_resultado_operacional(
    ctx: Dict[str, Any],
    texto_usuario: str,
) -> Tuple[bool, str]:
    """Responde à reação sobre a última ação sem reabrir conversa antiga."""
    mente = _get(ctx, "mente_integrada_estado", {})
    comentario = detectar_comentario_resultado_operacional(texto_usuario, mente)
    if not comentario:
        return False, ""

    suspender = _get(ctx, "_suspender_topico_conversacional")
    if callable(suspender):
        try:
            suspender("comentario_resultado_operacional")
        except Exception:
            pass

    tipo = str(comentario.get("tipo") or "")
    alvo = str(comentario.get("alvo") or "o resultado").strip()
    fala = ""
    if tipo == "aparencia_cor":
        pedida = str(comentario.get("cor_pedida") or "a cor pedida").strip()
        percebida = str(comentario.get("cor_percebida") or "outro tom").strip()
        fala = (
            f"Entendi — {alvo} puxou mais para {percebida} do que para {pedida}. "
            "No próximo ajuste eu uso um tom mais fechado para corrigir isso."
        )
    elif re.search(r"\b(?:não|nao)\s+(?:funcionou|deu)|\b(?:errado|estranho|pior)\b", str(texto_usuario), re.I):
        fala = f"Entendi — {alvo} não ficou como você esperava. Vou considerar esse resultado, não o assunto anterior."
    else:
        fala = f"Entendi o que você percebeu em {alvo}. Vou continuar a partir desse resultado."

    emitir = _get(ctx, "_emitir_resposta_curta")
    if callable(emitir):
        return bool(emitir(texto_usuario, fala, habilidade="continuidade_operacional")), "comentario_resultado_operacional"
    falar = _get(ctx, "falar_com_lipsync")
    if callable(falar):
        falar(fala, "calma", 1)
        return True, "comentario_resultado_operacional"
    return False, ""


def processar_fluxo_musical_generico(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    texto_pede_direcao_musical_generica = _get(ctx, "_texto_pede_direcao_musical_generica")
    responder_pedido_direcao_musical_generica = _get(ctx, "_responder_pedido_direcao_musical_generica")
    processar_confirmacao_sugestao_musical = _get(ctx, "_processar_confirmacao_sugestao_musical")
    t = str(texto_usuario or "").strip()

    if callable(processar_confirmacao_sugestao_musical) and processar_confirmacao_sugestao_musical(t):
        return True, "confirmacao_sugestao_musical"

    if callable(texto_pede_direcao_musical_generica) and texto_pede_direcao_musical_generica(t):
        if callable(responder_pedido_direcao_musical_generica):
            ok = bool(responder_pedido_direcao_musical_generica(t))
            return ok, "direcao_musical_generica" if ok else ""
        return True, "direcao_musical_generica"

    return False, ""


def processar_opiniao_musica_atual(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    detectar = _get(ctx, "_texto_pede_opiniao_musica_atual")
    responder = _get(ctx, "_responder_opiniao_musica_atual")
    if not callable(detectar) or not callable(responder):
        return False, ""
    try:
        if not detectar(texto_usuario):
            return False, ""
        return bool(responder(texto_usuario)), "opiniao_musica_atual"
    except Exception as erro:
        print(f"⚠️ [MÚSICA:OPINIÃO] falha no fluxo conversacional: {erro}")
        return False, ""


def resolver_contexto_unificado(ctx: Dict[str, Any], texto: str) -> Tuple[Dict[str, Any] | None, str]:
    resolver_comando_contextual_forcado = _get(ctx, "_resolver_comando_contextual_forcado")
    if not callable(resolver_comando_contextual_forcado):
        return None, ""
    try:
        comando_contextual = resolver_comando_contextual_forcado(str(texto or "").strip())
    except Exception:
        return None, ""
    if not isinstance(comando_contextual, dict):
        return None, ""
    rota = str(comando_contextual.get("_rota_contextual") or "GERAL").upper()
    intent_limpo = dict(comando_contextual)
    intent_limpo.pop("_rota_contextual", None)
    if not str(intent_limpo.get("intent") or "").strip():
        return None, ""
    return intent_limpo, rota


def processar_contexto_unificado_precoce(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    origem: str = "pre-ia",
) -> Tuple[bool, str]:
    try:
        comando_contextual, rota = resolver_contexto_unificado(ctx, texto_usuario)
        if comando_contextual:
            ok = executar_resultado_contextual(
                ctx,
                comando_contextual,
                texto_usuario,
                log_rota=f"ROTEADOR CONTEXTO-{rota} [{origem}]",
                origem_resultado=f"contexto_{rota.lower()}_{str(origem).replace('-', '_')}",
                contexto_autoaprimoramento=f"continuidade contextual de {rota.lower()}",
            )
            return ok, f"continuidade_{rota.lower()}" if ok else ""
    except Exception as e:
        print(f"⚠️ [CONTEXTO-UNIFICADO] falha no fluxo {origem}: {e}")
    return False, ""


def processar_repeticao_operacional_precoce(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    origem: str = "pre-ia",
) -> Tuple[bool, str]:
    """Reexecuta o contrato anterior antes de qualquer interpretação por IA."""
    resolver = _get(ctx, "_resolver_repeticao_ultima_acao")
    if not callable(resolver):
        return False, ""
    try:
        repeticao = resolver(str(texto_usuario or "").strip())
    except Exception:
        return False, ""
    if not isinstance(repeticao, dict) or not str(repeticao.get("intent") or "").strip():
        return False, ""
    ok = executar_resultado_contextual(
        ctx,
        repeticao,
        texto_usuario,
        origem_resultado=f"repeticao_{str(origem).replace('-', '_')}",
        contexto_autoaprimoramento="repetição explícita da última ação",
        log_rota=f"ROTEADOR REPETIÇÃO [{origem}]",
    )
    return ok, "repeticao_operacional" if ok else ""


def processar_janela_indisponivel(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    responder_contexto_janela_indisponivel = _get(ctx, "_responder_contexto_janela_indisponivel")
    t = str(texto_usuario or "").strip()
    if callable(responder_contexto_janela_indisponivel) and responder_contexto_janela_indisponivel(t):
        return True, "janela_indisponivel"
    return False, ""


def processar_aprendizado_apelido(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    processar_aprendizado_apelido_imediato = _get(ctx, "_processar_aprendizado_apelido_imediato")
    t = str(texto_usuario or "").strip()
    if callable(processar_aprendizado_apelido_imediato) and processar_aprendizado_apelido_imediato(t):
        return True, "aprendizado_apelido"
    return False, ""


def processar_comando_deterministico_precoce(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    origem: str = "pre-ia",
) -> Tuple[bool, str]:
    processar_comando_deterministico = _get(ctx, "processar_comando_deterministico")
    t = str(texto_usuario or "").strip()
    mente = _get(ctx, "mente_integrada_estado", {})
    turno = mente.get("turno_atual") if isinstance(mente, dict) else {}
    if isinstance(turno, dict) and "autoriza_execucao" in turno and not bool(turno.get("autoriza_execucao")):
        return False, ""
    operacional = str((turno or {}).get("texto_operacional") or "").strip()
    deteccao = operacional if str((turno or {}).get("ato_principal") or "") == "comando" and operacional else t
    executou = False
    if callable(processar_comando_deterministico):
        try:
            executou = bool(processar_comando_deterministico(deteccao, origem, t))
        except TypeError:
            executou = bool(processar_comando_deterministico(deteccao, origem))
    if executou:
        return True, f"comando_deterministico_{str(origem).replace('-', '_')}"
    return False, ""


def executar_resultado_contextual(
    ctx: Dict[str, Any],
    resultado: Dict[str, Any] | None,
    texto_usuario: str,
    *,
    origem_resultado: str,
    contexto_autoaprimoramento: str,
    log_rota: str,
) -> bool:
    if not isinstance(resultado, dict) or not str(resultado.get("intent") or "").strip():
        return False

    executar_intencao = _get(ctx, "executar_intencao")
    registrar_resultado_execucao = _get(ctx, "_registrar_resultado_execucao")
    registrar_autoaprimoramento = _get(ctx, "_registrar_autoaprimoramento")

    print(f"⚡ [{log_rota}] {resultado}")
    executou = bool(executar_intencao(resultado, texto_usuario)) if callable(executar_intencao) else False
    if callable(registrar_resultado_execucao):
        registrar_resultado_execucao(resultado, texto_usuario, executou, origem=origem_resultado)
    if executou and callable(registrar_autoaprimoramento):
        registrar_autoaprimoramento(
            resultado,
            texto_usuario,
            True,
            contexto=contexto_autoaprimoramento,
            origem=origem_resultado,
        )
    return True


def executar_comando_local_rapido(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, Dict[str, Any] | None]:
    interpretar_comando_local_rapido = _get(ctx, "interpretar_comando_local_rapido")
    executar_intencao = _get(ctx, "executar_intencao")
    registrar_resultado_execucao = _get(ctx, "_registrar_resultado_execucao")
    registrar_autoaprimoramento = _get(ctx, "_registrar_autoaprimoramento")

    decisao = _decisao_turno(ctx)
    if "autoriza_execucao" in decisao and not bool(decisao.get("autoriza_execucao")):
        return False, None

    comando_local = interpretar_comando_local_rapido(str(texto_usuario or "").strip()) if callable(interpretar_comando_local_rapido) else None
    if not isinstance(comando_local, dict) or not str(comando_local.get("intent") or "").strip():
        return False, None

    executou = bool(executar_intencao(comando_local, texto_usuario)) if callable(executar_intencao) else False
    if callable(registrar_resultado_execucao):
        registrar_resultado_execucao(comando_local, texto_usuario, executou, origem="comando_local_rapido")
    if executou and callable(registrar_autoaprimoramento):
        registrar_autoaprimoramento(
            comando_local,
            texto_usuario,
            True,
            contexto="comando local rapido",
            origem="comando_local_rapido",
        )
    return True, comando_local


def processar_comando_local_rapido_precoce(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    try:
        houve_comando_local, comando_local = executar_comando_local_rapido(ctx, texto_usuario)
    except Exception as e:
        print(f"⚠️ [FOCO LOCAL] falha ao executar comando local: {e}")
        return False, ""
    if houve_comando_local and isinstance(comando_local, dict):
        return True, "comando_local_rapido"
    return False, ""


def processar_execucao_pratica_precoce(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    origem: str = "pre-ia",
) -> Tuple[bool, str]:
    """Agrupa rotas praticas para diminuir competicao entre roteadores."""
    mente = _get(ctx, "mente_integrada_estado", {})
    turno = mente.get("turno_atual") if isinstance(mente, dict) else {}
    if isinstance(turno, dict) and "autoriza_execucao" in turno and not bool(turno.get("autoriza_execucao")):
        return False, ""
    if (
        str((turno or {}).get("modalidade_geral") or "") == "misto"
        and str((turno or {}).get("ato_principal") or "") == "comando"
        and str((turno or {}).get("texto_operacional") or "").strip()
    ):
        # O comando explícito do turno misto vence referências operacionais
        # antigas; o texto integral segue junto para a resposta final.
        return processar_comando_deterministico_precoce(ctx, texto_usuario, origem=origem)
    texto_norm = str(texto_usuario or "").casefold()
    if re.search(
        r"\b(?:daqui|em)\s+\d{1,4}\s*(?:segundos?|seg|minutos?|min|horas?)\b",
        texto_norm,
    ) or re.search(r"\b(?:as|às)\s+\d{1,2}:\d{2}\b", texto_norm):
        return processar_comando_deterministico_precoce(ctx, texto_usuario, origem=origem)

    # Leituras locais explícitas (saúde, briefing etc.) não podem herdar o
    # último dispositivo IoT só porque a frase contém "dele".
    houve_local, nome_local = processar_comando_local_rapido_precoce(ctx, texto_usuario)
    if houve_local:
        return True, nome_local or "comando_local_rapido"
    etapas = [
        lambda: processar_repeticao_operacional_precoce(ctx, texto_usuario, origem=origem),
        lambda: processar_contexto_unificado_precoce(ctx, texto_usuario, origem=origem),
        lambda: processar_janela_indisponivel(ctx, texto_usuario),
        lambda: processar_comando_deterministico_precoce(ctx, texto_usuario, origem=origem),
    ]
    for etapa in etapas:
        ok, nome = etapa()
        if ok:
            return True, nome or "execucao_pratica"
    return False, ""


def executar_pipeline_pre_fluxo(
    ctx: Dict[str, Any],
    texto_usuario: str,
    etapas: Iterable[Callable[[], Tuple[bool, str]]],
    *,
    log_cb: Callable[[str, str], None] | None = None,
) -> bool:
    for etapa in etapas:
        try:
            ok, nome = etapa()
        except Exception as e:
            print(f"⚠️ [PRE-FLUXO] falha em etapa compartilhada: {e}")
            continue
        if ok:
            if callable(log_cb):
                log_cb(nome or "etapa_sem_nome", "")
            return True
    return False
