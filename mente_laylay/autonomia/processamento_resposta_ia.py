"""Pós-processamento da resposta da IA na Laylay."""

from __future__ import annotations

import ast
import json
import re
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from mente_laylay.memoria_mental.memoria_confiavel import (
    extrair_aprendizados_pessoais_explicitos,
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
from mente_laylay.cognicao.contratos_turno import ContratoRespostaTurno


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


_PREFIXO_CAMPO_FALA = re.compile(
    r'^\s*(?:laylay\s*:\s*)?(?:\[\s*fala\s*\]|["\']?fala["\']?)\s*:\s*',
    re.IGNORECASE,
)


def _normalizar_envelope_contrato_escapado(texto: str) -> str:
    """Abre uma camada textual de JSON sem alterar fala livre comum.

    Alguns modelos devolvem o objeto inteiro como string (``{\"fala\":...}``),
    às vezes já truncada. Nesse caso a fala ainda é utilizável, embora o
    envelope não seja JSON válido. Comandos continuam sujeitos aos validadores
    normais depois da recuperação.
    """
    bruto = str(texto or "").strip()
    if not bruto:
        return ""
    try:
        decodificado = json.loads(bruto)
        if isinstance(decodificado, str) and _tem_indicio_contrato_ia(decodificado):
            return decodificado.strip()
    except Exception:
        pass

    candidato = bruto[1:].lstrip() if bruto.startswith(('"{\\"', "'{\\'")) else bruto
    if not re.match(r'^\s*\{\s*\\["\'](?:fala|tipo_interacao|comandos)\\["\']\s*:', candidato, re.IGNORECASE):
        return bruto
    candidato = candidato.replace(r'\"', '"').replace(r"\'", "'")
    if bruto.startswith(('"{\\"', "'{\\'")) and candidato.endswith(bruto[0]):
        candidato = candidato[:-1].rstrip()
    return candidato


def _remover_prefixos_campo_fala(texto: str) -> str:
    resultado = str(texto or "")
    for _ in range(3):
        limpo = _PREFIXO_CAMPO_FALA.sub("", resultado, count=1)
        if limpo == resultado:
            break
        resultado = limpo
    return resultado.strip()


def _normalizar_fala_cb(
    texto: str,
    limpar_texto_fala_cb: Optional[Callable[[str], str]] = None,
    fallback_fala: str = "Não consegui encaixar isso direito. Me fala de outro jeito?",
) -> str:
    # Alguns modelos locais deixam o nome do campo do contrato na frente da
    # resposta (``fala: ...``). Remova-o antes da higiene geral, pois nela
    # ``fala:`` também funciona como início de metadados e apagaria a frase.
    texto = _remover_prefixos_campo_fala(texto)
    if len(texto) >= 2 and texto[0] == texto[-1] and texto[0] in {'"', "'"}:
        texto = texto[1:-1].strip()
    if callable(limpar_texto_fala_cb):
        try:
            texto = limpar_texto_fala_cb(texto)
        except Exception:
            pass
    texto = remover_residuos_operacionais(texto)
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    return texto or fallback_fala


def _remover_loop_textual_malformado(texto: str) -> str:
    """Remove uma volta de geração repetida, preservando a versão mais completa.

    Só é chamada em saídas que já contêm evidência de contrato quebrado. Uma
    janela longa de palavras evita confundir repetição retórica normal com um
    loop de decodificação do modelo.
    """
    bruto = str(texto or "")
    palavras = list(re.finditer(r"[\wÀ-ÿ]+", bruto, flags=re.UNICODE))
    normalizadas = [item.group(0).casefold() for item in palavras]
    if len(normalizadas) < 16:
        return bruto
    limite = min(16, len(normalizadas) // 2)
    for tamanho in range(limite, 7, -1):
        vistas: Dict[Tuple[str, ...], int] = {}
        for indice in range(0, len(normalizadas) - tamanho + 1):
            chave = tuple(normalizadas[indice:indice + tamanho])
            anterior = vistas.get(chave)
            if anterior is not None and indice - anterior >= tamanho:
                inicio = palavras[anterior].start()
                reinicio = palavras[indice].start()
                reparada = bruto[:inicio].rstrip() + " " + bruto[reinicio:].lstrip()
                reparada = re.sub(r"\s+([,.;:!?])", r"\1", reparada)
                return re.sub(r"\s+", " ", reparada).strip()
            vistas.setdefault(chave, indice)
    return bruto


_CHAVES_CONTRATO_IA = {
    "fala", "comandos", "comando", "acao", "action", "alvo", "intent",
    "params", "aprendizado", "aprendizados", "tipo_interacao",
    "leitura_turno", "humor",
}

_PADRAO_CAMPO_CONTRATO = re.compile(
    r'(?i)(?:\[\s*)?["\']?(?:fala|tipo_interacao|leitura_turno|comandos|'
    r'aprendizados?|humor|acao|action|alvo|intent|params)["\']?(?:\s*\])?\s*:'
)


def _tem_indicio_contrato_ia(texto: str) -> bool:
    return bool(_PADRAO_CAMPO_CONTRATO.search(str(texto or "")))


def _remover_blocos_json_estruturais(texto: str) -> str:
    r"""Remove apenas objetos do contrato da IA, preservando chaves matemáticas.

    A antiga expressão ``\{.*\}`` era gulosa e confundia LaTeX, conjuntos e
    fórmulas com JSON. Aqui um bloco só é retirado quando é balanceado, pode
    ser realmente interpretado como dicionário e contém uma chave do contrato.
    """
    bruto = str(texto or "")
    if "{" not in bruto:
        return bruto.strip()

    saida: List[str] = []
    inicio_trecho = 0
    i = 0
    while i < len(bruto):
        if bruto[i] != "{":
            i += 1
            continue

        inicio = i
        profundidade = 0
        aspas = ""
        escape = False
        fim = -1
        while i < len(bruto):
            ch = bruto[i]
            if aspas:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == aspas:
                    aspas = ""
            elif ch in {'"', "'"}:
                aspas = ch
            elif ch == "{":
                profundidade += 1
            elif ch == "}":
                profundidade -= 1
                if profundidade == 0:
                    fim = i + 1
                    break
            i += 1

        if fim < 0:
            break

        bloco = bruto[inicio:fim]
        objeto: Any = None
        for parser in (json.loads, ast.literal_eval):
            try:
                objeto = parser(bloco)
                break
            except Exception:
                continue
        estrutural = isinstance(objeto, dict) and bool(
            {str(chave).strip().casefold() for chave in objeto} & _CHAVES_CONTRATO_IA
        )
        if estrutural:
            saida.append(bruto[inicio_trecho:inicio])
            saida.append(" ")
            inicio_trecho = fim
        i = fim

    saida.append(bruto[inicio_trecho:])
    return re.sub(r"\s+", " ", "".join(saida)).strip()


def _extrair_campo_textual_json_like(texto: str, campo: str) -> str:
    bruto = str(texto or "")
    if not bruto or not campo:
        return ""

    m = re.search(
        rf'(?:\[\s*)?["\']?{re.escape(campo)}["\']?(?:\s*\])?\s*:\s*',
        bruto,
        re.IGNORECASE,
    )
    if not m:
        return ""

    i = m.end()
    while i < len(bruto) and bruto[i].isspace():
        i += 1
    if i >= len(bruto):
        return ""

    quote = bruto[i]
    if quote not in {'"', "'"}:
        return ""
    i += 1

    resultado: List[str] = []
    escape = False
    while i < len(bruto):
        ch = bruto[i]
        if escape:
            resultado.append(ch)
            escape = False
        elif ch == "\\":
            escape = True
        elif ch == quote:
            break
        else:
            resultado.append(ch)
        i += 1

    return "".join(resultado).strip()


def _fala_antes_de_metadados(texto: str) -> str:
    """Recupera a fala livre que veio antes de um contrato interno vazado."""
    marcador = re.search(
        r'(?:\[\s*(?:fala|tipo_interacao|leitura_turno|comandos|aprendizados?|humor)\s*\]\s*:|'
        r'(?<!\w)(?:tipo_interacao|leitura_turno|comandos|aprendizados?|humor)\s*:)',
        str(texto or ""),
        flags=re.IGNORECASE,
    )
    if not marcador:
        return ""
    prefixo = str(texto or "")[:marcador.start()].strip(" \t\r\n,;:-")
    return prefixo if len(prefixo) >= 2 else ""


def limpar_resposta_da_ia(
    resposta_bruta: Any,
    limpar_texto_fala_cb: Optional[Callable[[str], str]] = None,
    fallback_fala: str = "Não consegui encaixar isso direito. Me fala de outro jeito?",
) -> Tuple[str, List[Dict[str, Any]]]:
    """Separa fala e comandos, mesmo quando a saída da IA vem malformada."""
    if isinstance(resposta_bruta, tuple) and len(resposta_bruta) == 2:
        fala, comandos = resposta_bruta
        return _normalizar_fala_cb(str(fala or ""), limpar_texto_fala_cb, fallback_fala), list(comandos or [])

    original = str(resposta_bruta or "").strip()
    fala_final = ""
    comandos_finais: List[Dict[str, Any]] = []

    texto_pre = re.sub(r"^```(?:json)?\s*", "", original, flags=re.IGNORECASE)
    texto_pre = re.sub(r"\s*```$", "", texto_pre, flags=re.IGNORECASE).strip()
    texto_pre = _normalizar_envelope_contrato_escapado(texto_pre)
    json_invalido = False

    try:
        dados = json.loads(texto_pre)
        if isinstance(dados, dict):
            fala_final = str(dados.get("fala", "")).strip()
            comandos = dados.get("comandos", [])
            if isinstance(comandos, list):
                comandos_finais = [c for c in comandos if isinstance(c, dict)]
                return _normalizar_fala_cb(
                    fala_final,
                    limpar_texto_fala_cb,
                    fallback_fala,
                ), comandos_finais
    except Exception:
        json_invalido = bool(
            texto_pre.startswith(("{", "["))
            or re.search(r'(?i)(?:\[\s*)?["\']?(?:fala|tipo_interacao|leitura_turno|comandos|aprendizados?|humor)["\']?(?:\s*\])?\s*:', texto_pre)
        )

    try:
        match_cmds = re.search(r'["\']?comandos["\']?\s*:\s*(\[.*?\])', texto_pre, re.IGNORECASE | re.DOTALL)
        if match_cmds:
            cmd_txt = match_cmds.group(1).strip()
            try:
                parsed = json.loads(cmd_txt)
            except Exception:
                parsed = ast.literal_eval(cmd_txt)
            if isinstance(parsed, list):
                comandos_finais = [c for c in parsed if isinstance(c, dict)]
    except Exception:
        pass

    try:
        fala_final = _extrair_campo_textual_json_like(texto_pre, "fala") or fala_final
    except Exception:
        pass
    if not fala_final and _PREFIXO_CAMPO_FALA.match(texto_pre):
        fala_final = _remover_prefixos_campo_fala(texto_pre)
    # Se o modelo já produziu uma frase natural antes de despejar o esquema,
    # essa frase é mais confiável que um campo duplicado e possivelmente
    # truncado no fim da saída.
    fala_prefixo = _fala_antes_de_metadados(texto_pre)
    if fala_prefixo:
        fala_final = fala_prefixo

    if not comandos_finais:
        def _limpar_alvo_bruto(valor: str) -> str:
            v = str(valor or "").strip()
            v = v.strip(" '\"\t\r\n")
            v = v.rstrip(".,;:!?)]}>'\"")
            return v.strip()

        texto_busca = texto_pre
        padroes_soltos = [
            ("open_url", r'(?i)\bopen_url\b\s*["\':=]*\s*(?P<alvo>(?:https?://|www\.)[^\s"\']+|[^\s"\']+\.[^\s"\']+)(?:\b|$)'),
            ("youtube_search", r'(?i)\byoutube_search\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
            ("youtube_play", r'(?i)\byoutube_play\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
            ("close_tab", r'(?i)\bclose_tab\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
            ("close_specific_tab", r'(?i)\bclose_specific_tab\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
            ("open_app", r'(?i)\bopen_app\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
            ("close_app", r'(?i)\bclose_app\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
        ]
        for acao_solta, padrao_solto in padroes_soltos:
            m_solto = re.search(padrao_solto, texto_busca, flags=re.IGNORECASE | re.DOTALL)
            if not m_solto:
                continue
            alvo_solto = _limpar_alvo_bruto(m_solto.group("alvo") or "")
            if not alvo_solto:
                continue
            if acao_solta == "open_url":
                if not re.match(r"^(?:https?://|www\.)", alvo_solto, flags=re.IGNORECASE):
                    continue
            elif acao_solta in {"youtube_search", "youtube_play"}:
                alvo_solto = alvo_solto.strip(" '\"")
            comando = {"acao": acao_solta, "alvo": alvo_solto}
            if acao_solta == "open_url":
                comando["url"] = alvo_solto
            elif acao_solta in {"youtube_search", "youtube_play"}:
                comando["query"] = alvo_solto
            elif acao_solta in {"close_tab", "close_specific_tab"}:
                comando["target"] = alvo_solto
            elif acao_solta in {"open_app", "close_app"}:
                comando["app"] = alvo_solto
            comandos_finais = [comando]
            break

    if comandos_finais and not fala_final:
        txt_limpo_de_json = _remover_blocos_json_estruturais(texto_pre)
        if txt_limpo_de_json and len(txt_limpo_de_json) > 1:
            fala_final = txt_limpo_de_json

    if not comandos_finais:
        if json_invalido and not fala_final:
            print("⚠️ [IA] JSON inválido bloqueado antes da fala.")
            return _normalizar_fala_cb("", limpar_texto_fala_cb, fallback_fala), []
        if fala_final:
            if _tem_indicio_contrato_ia(original):
                fala_final = _remover_loop_textual_malformado(fala_final)
                print(f"🧹 [IA] Estrutura conversacional recuperada: {fala_final[:60]}...")
            return _normalizar_fala_cb(fala_final, limpar_texto_fala_cb, fallback_fala), []
        texto_fala_pura = _remover_blocos_json_estruturais(texto_pre)
        if not texto_fala_pura:
            texto_fala_pura = texto_pre
        texto_fala_pura = re.sub(r"\[EXEC:.*?\]", "", texto_fala_pura, flags=re.IGNORECASE | re.DOTALL)
        texto_fala_pura = texto_fala_pura.strip()
        if len(texto_fala_pura) < 2:
            texto_fala_pura = fallback_fala
        if _tem_indicio_contrato_ia(original):
            texto_fala_pura = _remover_loop_textual_malformado(texto_fala_pura)
            print(f"🧹 [IA] Estrutura conversacional recuperada: {texto_fala_pura[:60]}...")
        return _normalizar_fala_cb(texto_fala_pura, limpar_texto_fala_cb, fallback_fala), []

    return _normalizar_fala_cb(fala_final, limpar_texto_fala_cb, fallback_fala), comandos_finais


def _saida_ia_parece_malformada(texto: str) -> bool:
    s = str(texto or "").strip()
    if not s:
        return False
    texto_json = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    texto_json = re.sub(r"\s*```$", "", texto_json, flags=re.IGNORECASE).strip()
    texto_json = _normalizar_envelope_contrato_escapado(texto_json)
    parseou_json = False
    try:
        dados = json.loads(texto_json)
        parseou_json = True
        if (
            isinstance(dados, dict)
            and isinstance(dados.get("fala", ""), str)
            and isinstance(dados.get("comandos", []), list)
        ):
            return False
    except Exception:
        pass
    parece_objeto = bool(re.match(
        r'^\{\s*["\']?[A-Za-z_À-ÿ][\wÀ-ÿ-]*["\']?\s*:',
        texto_json,
    ))
    if not parseou_json and (parece_objeto or _tem_indicio_contrato_ia(texto_json)):
        return True
    if re.search(r"(?i)\[EXEC:.*?\]", s):
        return True
    if re.search(r"(?i)\b(open_url|youtube_search|youtube_play|close_tab|close_specific_tab|open_app|close_app)\b", s):
        return True
    return False


def corrigir_saida_malformada_da_ia(
    texto_usuario: str,
    resposta_bruta: Any,
    enviar_mensagem_cb: Optional[Callable[..., Any]] = None,
) -> Optional[Any]:
    bruto = str(resposta_bruta or "").strip()
    if not bruto or not _saida_ia_parece_malformada(bruto):
        return None
    if not callable(enviar_mensagem_cb):
        return None

    prompt = (
        "Você é um corretor de saída. Reescreva a resposta abaixo em JSON válido e APENAS JSON.\n"
        "Formato obrigatório:\n"
        "{\"fala\":\"...\",\"comandos\":[{\"acao\":\"...\",\"alvo\":\"...\"}]}\n"
        "Regras:\n"
        "- Não use markdown.\n"
        "- Não use aspas soltas fora do JSON.\n"
        "- Se houver comando de abrir URL, use acao=open_url e coloque a URL em alvo.\n"
        "- Se a resposta anterior já tinha um comando implícito, preserve a intenção.\n"
        "- Se não houver comando, retorne comandos vazios.\n"
    )
    payload = {
        "texto_usuario": str(texto_usuario or "")[:1200],
        "resposta_bruta": bruto[:1800],
    }
    try:
        corrigida = enviar_mensagem_cb(
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            _com_tools=False,
            max_tokens=240,
            modo_rapido=True,
        )
        if corrigida and str(corrigida).strip():
            candidata = re.sub(r"^```(?:json)?\s*", "", str(corrigida).strip(), flags=re.IGNORECASE)
            candidata = re.sub(r"\s*```$", "", candidata, flags=re.IGNORECASE).strip()
            try:
                dados = json.loads(candidata)
            except Exception:
                dados = None
            # Uma segunda resposta ocupada, vazia ou novamente malformada não
            # pode substituir a fala original que ainda é recuperável.
            if isinstance(dados, dict) and isinstance(dados.get("fala"), str) and isinstance(dados.get("comandos", []), list):
                return candidata
    except Exception as e:
        print(f"⚠️ [AUTOCORREÇÃO] falha ao pedir correção da saída: {e}")
    return None


def _saida_conversacional_recuperavel_localmente(resposta_bruta: Any) -> bool:
    """Reconhece quando o vazamento é só estrutural e dispensa outra LLM."""
    bruto = str(resposta_bruta or "").strip()
    if not bruto or not _saida_ia_parece_malformada(bruto):
        return False
    # Ações ambíguas continuam usando a correção completa, pois perder um
    # alvo ou interpretar um comando pela metade seria pior que esperar.
    if re.search(
        r"(?i)\b(open_url|youtube_search|youtube_play|close_tab|close_specific_tab|open_app|close_app)\b",
        bruto,
    ):
        return False
    normalizado = _normalizar_envelope_contrato_escapado(bruto)
    fala = _fala_antes_de_metadados(normalizado) or _extrair_campo_textual_json_like(normalizado, "fala")
    return len(str(fala or "").strip()) >= 2


def _fala_entregavel(texto: Any, fallback_fala: str) -> bool:
    """Distingue conteúdo real de sentinelas internas e contratos vazados."""
    fala = re.sub(r"\s+", " ", str(texto or "")).strip()
    fallback = re.sub(r"\s+", " ", str(fallback_fala or "")).strip()
    if len(fala) < 2 or fala.casefold() == fallback.casefold():
        return False
    if _fala_representa_falha_tecnica_llm(fala):
        return False
    if _tem_indicio_contrato_ia(fala) or re.search(r"(?i)\[EXEC:.*?\]", fala):
        return False
    return True


def _fala_representa_falha_tecnica_llm(texto: Any) -> bool:
    """Reconhece sentinelas novas e mensagens legadas que jamais são diálogo."""
    fala = re.sub(r"\s+", " ", str(texto or "")).strip()
    if re.fullmatch(r"__LAYLAY_LLM_[A-Z_]+__", fala):
        return True
    return bool(re.search(
        r"(?i)(?:essa resposta demorou mais do que devia|"
        r"minha resposta (?:não ficou pronta a tempo|falhou antes de ficar pronta)|"
        r"meu modelo local (?:está|esta|continuou) ocupado|"
        r"t[oô] poupando a placa enquanto voc[eê] joga)",
        fala,
    ))


def _fala_contingencia_sem_llm(
    texto_usuario: str,
    contexto: Mapping[str, Any] | None = None,
) -> str:
    """Mantém o vínculo do turno sem simular uma resposta ou uma execução."""
    return fala_contingencia_natural(texto_usuario, contexto=contexto)


def _recuperar_fala_no_mesmo_turno(
    texto_usuario: str,
    resposta_anterior: Any,
    *,
    enviar_mensagem_cb: Optional[Callable[..., Any]],
    limpar_texto_fala_cb: Optional[Callable[[str], str]],
    fallback_fala: str,
) -> str:
    """Faz uma única nova tentativa, sem permitir ações na resposta reparada."""
    if (
        not callable(enviar_mensagem_cb)
        or not str(texto_usuario or "").strip()
        or _fala_representa_falha_tecnica_llm(resposta_anterior)
    ):
        return ""
    try:
        reparada = enviar_mensagem_cb(
            [
                {
                    "role": "system",
                    "content": (
                        "A resposta anterior falhou no formato. Responda agora ao texto do usuário "
                        "de maneira direta, natural e completa, mantendo o assunto atual. Não peça "
                        "para ele repetir, não mencione erro técnico e não execute ações. Retorne "
                        "somente JSON válido no formato {\"fala\":\"...\",\"comandos\":[]}."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "texto_usuario": str(texto_usuario or "")[:800],
                            "resposta_anterior": str(resposta_anterior or "")[:1000],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            _com_tools=False,
            max_tokens=320,
            modo_rapido=True,
            _prioridade_interativa=True,
        )
        fala, _comandos_descartados = limpar_resposta_da_ia(
            reparada,
            limpar_texto_fala_cb=limpar_texto_fala_cb,
            fallback_fala=fallback_fala,
        )
        return fala if _fala_entregavel(fala, fallback_fala) else ""
    except Exception:
        return ""


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
    aprendizados = extrair_aprendizados_da_ia(resposta_bruta)
    aprendizados.extend(extrair_aprendizados_pessoais_explicitos(texto_usuario))
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
    enviar_mensagem_cb: Optional[Callable[..., Any]],
    limpar_texto_fala_cb: Optional[Callable[[str], str]],
    fallback_fala: str,
    memoria_sqlite: Any,
    registrar_autocorrecao_cb: Optional[Callable[..., Any]] = None,
    registrar_falha_cb: Optional[Callable[..., Any]] = None,
    contexto_contingencia: Mapping[str, Any] | None = None,
    log: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Prepara a resposta da IA antes do dispatcher executar qualquer acao."""
    registrar_log = log or print
    texto = str(texto_usuario or "").strip()
    bot_raw = resposta_bruta
    falha_tecnica_llm = _fala_representa_falha_tecnica_llm(bot_raw)

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
    if not recuperavel_localmente:
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
    tipo_interacao = extrair_tipo_interacao_da_ia(bot_raw)
    emocao_resposta, nivel_emocao_resposta = extrair_emocao_da_ia(bot_raw)
    leitura_semantica = extrair_leitura_semantica_da_ia(bot_raw, texto)
    suprimir_fala = False
    if realidade_bloqueada:
        fala_limpa = ""
        suprimir_fala = True
        registrar_log("⚠️ [IA:REALIDADE] invenção pessoal bloqueada antes da fala.")
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
        autocorrigida=bool(corrigida),
        suprimir_fala=suprimir_fala,
        emocao=emocao_resposta,
        nivel_emocao=nivel_emocao_resposta,
    ).como_dict()
