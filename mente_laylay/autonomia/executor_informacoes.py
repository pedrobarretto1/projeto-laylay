"""Consultas informativas de e-mail, clima e briefing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_comum import falar_ctx as _falar
from mente_laylay.memoria_mental.memoria_confiavel import normalizar_texto
from mente_laylay.memoria_mental.identidade_usuario import normalizar_nome_usuario
from mente_laylay.personalidade.falas_variadas import escolher as escolher_fala_variada
from mente_laylay.personalidade.fala_memoria import (
    falar_lembrancas,
    falar_nome_lembrado,
)


INTENCOES_INFORMACOES = frozenset({
    "EMAIL_READ", "EMAIL_SYNC", "BRIEFING_REPEAT", "WEATHER", "LEARNING_QUERY",
})


@dataclass(frozen=True, slots=True)
class DependenciasExecutorInformacoes:
    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]
    registrar_mente: Callable[..., Any]


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _humanizar_aprendizado(item: Dict[str, Any]) -> str:
    """Converte o registro interno em uma lembrança dirigida à pessoa."""
    humanizado = str(item.get("_texto_humanizado") or "").strip()
    if humanizado:
        return humanizado
    texto = str(item.get("texto") or item.get("regra") or "").strip()
    valor = str(item.get("valor") or "").strip()
    chave = str(item.get("chave") or "").casefold()
    if chave.startswith("preferencia:afinidade:") and valor:
        regra = str(item.get("regra") or texto).casefold()
        if any(sinal in regra for sinal in (
            "não gosta", "nao gosta", "não curte", "nao curte",
            "odeia", "detesta",
        )):
            return f"você não gosta de {valor}"
        if "prefere" in regra:
            return f"você prefere {valor}"
        if "adora" in regra:
            return f"você adora {valor}"
        if " ama " in f" {regra} ":
            return f"você ama {valor}"
        if "curte" in regra:
            return f"você curte {valor}"
        return f"você gosta de {valor}"
    substituicoes = (
        (r"^o usuário\s+gosto\s+de\s+", "você gosta de "),
        (r"^o usuário\s+curto\s+", "você curte "),
        (r"^o usuário\s+adoro\s+", "você adora "),
        (r"^o usuário\s+amo\s+", "você ama "),
        (r"^o usuário\s+", "você "),
    )
    for padrao, troca in substituicoes:
        texto = re.sub(padrao, troca, texto, flags=re.IGNORECASE)
    return texto


_AFINIDADE_HUMANIZADA = re.compile(
    r"^você\s+(?P<verbo>não\s+gosta\s+de|não\s+curte|odeia|detesta|"
    r"gosta\s+de|prefere|adora|ama|curte)\s+"
    r"(?P<valor>.+)$",
    re.IGNORECASE,
)


def _partes_afinidade(valor: str) -> list[str]:
    """Separa listas naturais usadas como um único valor de preferência."""
    partes = [
        parte.strip(" ,.;:-")
        for parte in re.split(r"\s*(?:[,;]|\be\b)\s*", str(valor or ""), flags=re.I)
        if parte.strip(" ,.;:-")
    ]
    return partes or [str(valor or "").strip()]


def _deduplicar_aprendizados_para_fala(
    aprendizados: list[Dict[str, Any]],
) -> list[Dict[str, Any]]:
    """Expande afinidades compostas e remove duplicatas sem misturar polaridade.

    Registros antigos podem conter ``rock e programação`` como um único valor
    e, ao mesmo tempo, um registro atômico de ``rock``. A chave inclui a
    polaridade para que ``gosta de X`` nunca apague ``não gosta de X``.
    Outros aprendizados preservam a ordem e a proveniência originais.
    """
    vistos_preferencia: set[tuple[str, str]] = set()
    vistos_outros: set[str] = set()
    resultado: list[Dict[str, Any]] = []
    for item in aprendizados:
        fala = _humanizar_aprendizado(item).strip().rstrip(".!?;: ")
        afinidade = _AFINIDADE_HUMANIZADA.fullmatch(fala)
        if afinidade:
            verbo = re.sub(r"\s+", " ", afinidade.group("verbo").casefold()).strip()
            polaridade = (
                "negativa"
                if verbo.startswith("não ") or verbo in {"odeia", "detesta"}
                else "positiva"
            )
            for valor in _partes_afinidade(afinidade.group("valor")):
                assinatura = normalizar_texto(valor)
                chave = (polaridade, assinatura)
                if not assinatura or chave in vistos_preferencia:
                    continue
                vistos_preferencia.add(chave)
                atomico = dict(item)
                atomico["valor"] = valor
                atomico["_texto_humanizado"] = f"você {verbo} {valor}"
                resultado.append(atomico)
            continue

        assinatura = normalizar_texto(fala)
        if assinatura and assinatura not in vistos_outros:
            vistos_outros.add(assinatura)
            resultado.append(dict(item))
    return resultado


def _filtrar_polaridade_preferencia(
    aprendizados: list[Dict[str, Any]],
    polaridade: str,
) -> list[Dict[str, Any]]:
    """Aplica a polaridade pedida sem inferir gosto a partir de outro fato."""
    polaridade_norm = normalizar_texto(polaridade)
    if polaridade_norm not in {"positiva", "negativa"}:
        return aprendizados
    filtrados: list[Dict[str, Any]] = []
    for item in aprendizados:
        fala = _humanizar_aprendizado(item).strip().rstrip(".!?;: ")
        afinidade = _AFINIDADE_HUMANIZADA.fullmatch(fala)
        if not afinidade:
            continue
        verbo = normalizar_texto(afinidade.group("verbo"))
        negativa = verbo.startswith("nao ") or verbo in {"odeia", "detesta"}
        if negativa == (polaridade_norm == "negativa"):
            filtrados.append(item)
    return filtrados


def _ler_emails(
    params: Dict[str, Any],
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    configurado = _get(ctx, "_gmail_configurado")
    if callable(configurado) and not configurado():
        _falar(
            ctx,
            "Meu acesso ao Gmail não está configurado neste PC. Configure as variáveis do email e me reinicie para eu voltar a acompanhar a caixa.",
        )
        deps.marcar_resultado("falha_execucao", executou=False)
        return ResultadoDespacho.concluido()
    somente = bool(params.get("urgentes") or params.get("prioritarios"))
    remetente = str(
        params.get("remetente") or params.get("alvo") or params.get("query") or ""
    ).strip().lower()
    buscar = _get(ctx, "_gmail_buscar_nao_lidos")
    emails = _get(ctx, "_gmail_nao_lidos_cache", []) or (buscar() if callable(buscar) else [])
    if somente:
        emails = [email for email in emails if email.get("prioritario")]
    if remetente:
        filtrados = []
        for email in emails if isinstance(emails, list) else []:
            origem = str((email or {}).get("remetente") or "").strip().lower()
            if origem and (remetente == origem or remetente in origem or origem in remetente):
                filtrados.append(email)
        emails = filtrados or emails

    resumir = _get(ctx, "_gmail_falar_resumo_estiloso")
    fala = ""
    if callable(resumir):
        try:
            fala = str(resumir(
                emails,
                somente_prioritarios=somente,
                emitir_proativa=False,
            ) or "").strip()
        except TypeError:
            fala = str(resumir(emails, somente_prioritarios=somente) or "").strip()
    if fala:
        _falar(ctx, fala)
    deps.marcar_resultado(
        "emails_lidos",
        executou=True,
        confirmado=True,
    )
    return ResultadoDespacho.concluido()


def _sincronizar_emails(
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    configurado = _get(ctx, "_gmail_configurado")
    if callable(configurado) and not configurado():
        deps.marcar_resultado("falha_execucao", executou=False)
        _falar(
            ctx,
            "Ainda não tenho acesso configurado ao Gmail neste PC. Depois de configurar as variáveis, preciso ser reiniciada.",
        )
        return ResultadoDespacho.concluido()
    buscar = _get(ctx, "_gmail_buscar_nao_lidos")
    ok = False
    if callable(buscar):
        try:
            ok = isinstance(buscar(), list)
        except Exception:
            ok = False
    status = "emails_sincronizados" if ok else "falha_execucao"
    deps.marcar_resultado(status, executou=ok)
    deps.falar_por_status(
        status,
        "Atualizando a caixa de entrada."
        if ok else "Tentei atualizar teus emails, mas a caixa não respondeu direito.",
        alvo="emails",
    )
    return ResultadoDespacho.concluido()


def _repetir_briefing(
    texto_original: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    repetir = _get(ctx, "repetir_briefing")
    fala = ""
    retorno: Any = None
    if callable(repetir):
        try:
            retorno = repetir()
        except Exception:
            retorno = None
        if isinstance(retorno, str):
            fala = retorno.strip()
    if fala:
        deps.registrar_mente(
            texto_original,
            fala,
            "BRIEFING_REPEAT",
            "briefing do clima",
            "conversa",
            "briefing",
        )
    sucesso = bool(fala or retorno is True)
    if sucesso:
        deps.marcar_resultado(
            "briefing_repetido",
            executou=True,
            confirmado=True,
        )
        return ResultadoDespacho.concluido(True)

    _falar(
        ctx,
        "Ainda não tenho um briefing pronto para repetir. Posso montar um novo quando você quiser.",
    )
    deps.marcar_resultado(
        "briefing_indisponivel",
        executou=False,
        confirmado=False,
    )
    return ResultadoDespacho.concluido(False)


def _consultar_clima(
    params: Dict[str, Any],
    texto_original: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    local = str(
        params.get("local") or params.get("cidade") or params.get("bairro")
        or params.get("query") or _get(ctx, "cidade_padrao_clima", "Boituva")
    ).strip()
    try:
        day_offset = max(0, min(6, int(params.get("day_offset") or 0)))
    except (TypeError, ValueError):
        day_offset = 0
    obter = _get(ctx, "obter_clima_localidade")
    try:
        if callable(obter):
            try:
                info = obter(local, day_offset=day_offset)
            except TypeError:
                # Adaptadores antigos só são seguros para o tempo atual. Não
                # rotulamos dados de hoje como previsão de amanhã.
                info = (
                    obter(local)
                    if day_offset == 0
                    else {
                        "ok": False,
                        "localidade": local,
                        "erro": "horizonte_nao_suportado",
                    }
                )
        else:
            info = {"ok": False, "localidade": local}
    except Exception:
        info = {"ok": False, "localidade": local}
    if not isinstance(info, dict):
        info = {"ok": False, "localidade": local}
    if not info.get("ok"):
        _falar(ctx, escolher_fala_variada([
            f"Tentei sentir o clima de {local}, mas minha antena do tempo falhou agora.",
            f"Fui olhar o tempo em {local}, mas não consegui puxar essa informação agora.",
            f"O clima de {local} escapou de mim por enquanto. Se quiser, tenta de novo em instantes.",
        ]))
        deps.marcar_resultado(
            "clima_indisponivel",
            executou=False,
            confirmado=False,
        )
        return ResultadoDespacho.concluido()

    cidade = str(info.get("localidade") or local).strip()
    cidade_fala = cidade.title() if cidade.islower() else cidade
    temperatura = str(info.get("temperatura_c") or "").strip()
    sensacao = str(info.get("sensacao_c") or "").strip()
    descricao = str(info.get("descricao") or "").strip()
    umidade = str(info.get("umidade") or "").strip()
    if day_offset:
        rotulo_dia = "Amanhã" if day_offset == 1 else "Depois de amanhã"
        maxima = str(info.get("temperatura_max_c") or "").strip()
        minima = str(info.get("temperatura_min_c") or "").strip()
        chance_bruta = info.get("chance_chuva_pct")
        try:
            chance = max(0, min(100, int(float(chance_bruta))))
        except (TypeError, ValueError):
            chance = None
        partes = [f"{rotulo_dia} em {cidade_fala}"]
        if descricao:
            partes.append(f"o tempo fica {descricao.casefold()}")
        if maxima and minima:
            partes.append(f"com mínima de {minima} e máxima de {maxima} graus")
        elif maxima:
            partes.append(f"com máxima de {maxima} graus")
        elif minima:
            partes.append(f"com mínima de {minima} graus")
        elif temperatura:
            partes.append(f"com temperatura média perto de {temperatura} graus")
        if chance is not None:
            partes.append(f"e chance de chuva de até {chance}%")
        if len(partes) == 1:
            _falar(
                ctx,
                f"O provedor respondeu para {cidade_fala}, mas não trouxe dados suficientes para {rotulo_dia.casefold()}.",
            )
            deps.marcar_resultado(
                "previsao_indisponivel", executou=False, confirmado=False,
            )
            return ResultadoDespacho.concluido(False)
        fala_previsao = ", ".join(partes).rstrip(", ") + "."
        _falar(ctx, fala_previsao)
        deps.marcar_resultado(
            "previsao_consultada",
            executou=True,
            confirmado=True,
            detalhe=str(info.get("fonte") or "fonte_meteorologica"),
        )
        return ResultadoDespacho.concluido(True)

    base = f"Agora em {cidade_fala} está {temperatura} graus"
    if descricao:
        base += f", e o tempo está {descricao.casefold()}"
    if sensacao:
        base += f". Sensação de {sensacao} graus"
    if umidade:
        base += f" e umidade em {umidade}%"
    base += "."
    pergunta_chuva = "chov" in str(texto_original or "").casefold()
    pergunta_maxima = bool(re.search(
        r"\b(?:temperatura\s+)?maxima\b|\bmaximo\b",
        normalizar_texto(texto_original),
    ))
    pergunta_minima = bool(re.search(
        r"\b(?:temperatura\s+)?minima\b|\bminimo\b",
        normalizar_texto(texto_original),
    ))
    if pergunta_maxima or pergunta_minima:
        chave = "temperatura_max_c" if pergunta_maxima else "temperatura_min_c"
        rotulo = "máxima" if pergunta_maxima else "mínima"
        valor = str(info.get(chave) or "").strip()
        if valor:
            _falar(ctx, f"A temperatura {rotulo} prevista hoje em {cidade_fala} é de {valor} graus.")
        else:
            _falar(
                ctx,
                f"Consegui ver o tempo atual, mas o provedor não informou a temperatura {rotulo} de hoje.",
            )
    elif pergunta_chuva:
        chance_bruta = info.get("chance_chuva_pct")
        try:
            chance = max(0, min(100, int(float(chance_bruta))))
        except (TypeError, ValueError):
            chance = None
        descricao_norm = descricao.casefold()
        chuva_agora = any(
            termo in descricao_norm
            for termo in ("chuva", "chuvoso", "garoa", "rain", "drizzle", "tempestade")
        )
        if chuva_agora:
            resposta_chuva = "Sim, está chovendo ou há chuva indicada agora."
        elif chance is None:
            resposta_chuva = "Não consegui confirmar a chance de chuva para hoje."
        elif chance >= 60:
            resposta_chuva = f"Sim, há uma chance alta de chuva hoje: até {chance}%."
        elif chance >= 30:
            resposta_chuva = f"Pode chover hoje; a chance chega a {chance}%."
        else:
            resposta_chuva = (
                f"A previsão não indica chuva significativa hoje; "
                f"a chance máxima é de {chance}%."
            )
        _falar(ctx, f"{resposta_chuva} {base}")
    else:
        _falar(ctx, escolher_fala_variada([
            base,
            f"Dei uma espiada no tempo: {base}",
            f"Clima na mesa. {base}",
        ]))
    deps.marcar_resultado("clima_consultado", executou=True, confirmado=True)
    return ResultadoDespacho.concluido()


def _consultar_aprendizados(
    params: Dict[str, Any],
    texto_original: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    recuperar = _get(ctx, "_recuperar_aprendizados")
    try:
        limite = max(1, min(5, int(params.get("limit") or 3)))
    except (TypeError, ValueError):
        limite = 3
    try:
        offset = max(0, int(params.get("offset") or 0))
    except (TypeError, ValueError):
        offset = 0
    consulta = str(params.get("query") or params.get("consulta") or "").strip()
    modo = str(params.get("modo") or "listar").strip().casefold()
    polaridade = str(params.get("polaridade") or "").strip().casefold()
    if modo == "identidade":
        mente = _get(ctx, "mente_integrada_estado", {})
        nome = normalizar_nome_usuario(
            mente.get("nome_usuario") if isinstance(mente, dict) else ""
        )
        if nome:
            deps.marcar_resultado(
                "aprendizados_consultados", executou=True, confirmado=True,
            )
            _falar(ctx, falar_nome_lembrado(nome))
            return ResultadoDespacho.concluido(True)
    if not callable(recuperar):
        deps.marcar_resultado("habilidade_indisponivel", executou=False)
        _falar(ctx, "Minha memória de aprendizados não está disponível agora.")
        return ResultadoDespacho.concluido(False)
    try:
        try:
            limite_busca = 20 if polaridade in {"positiva", "negativa"} else limite
            brutos = recuperar(
                consulta=consulta,
                limit=limite_busca,
                offset=offset,
            ) or []
        except TypeError:
            # Compatibilidade temporária com adaptadores anteriores à visão
            # unificada. A origem continua marcada como legado, nunca como
            # confirmação direta do usuário.
            brutos = recuperar(limit=limite) or []
    except Exception:
        deps.marcar_resultado("falha_execucao", executou=False)
        _falar(ctx, "Tentei puxar o que aprendi, mas minha memória não respondeu direito.")
        return ResultadoDespacho.concluido(False)

    aprendizados: list[Dict[str, Any]] = []
    for item in brutos if isinstance(brutos, (list, tuple)) else []:
        if isinstance(item, dict):
            registro = dict(item)
            texto = str(registro.get("texto") or "").strip()
        else:
            texto = str(item or "").strip()
            registro = {
                "texto": texto,
                "fonte": "fato_legado",
                "natureza": "registro_antigo",
                "confirmado_usuario": False,
            }
        if texto:
            registro["texto"] = texto
            aprendizados.append(registro)

    if modo == "identidade":
        nome = ""
        for item in aprendizados:
            if str(item.get("chave") or "") == "identidade:nome_usuario":
                nome = normalizar_nome_usuario(item.get("valor"))
            if not nome:
                achado = re.search(
                    r"\bnome (?:confirmado )?do usu[aá]rio (?:e|é|eh|è)\s+"
                    r"([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ' -]{0,59})",
                    str(item.get("texto") or ""),
                    flags=re.IGNORECASE,
                )
                nome = normalizar_nome_usuario(achado.group(1)) if achado else ""
            if nome:
                break
        deps.marcar_resultado(
            "aprendizados_consultados", executou=True, confirmado=True,
        )
        if nome:
            _falar(ctx, falar_nome_lembrado(nome))
        else:
            _falar(
                ctx,
                "Ainda não tenho seu nome confirmado na memória. Se quiser, diga “meu nome é...” e eu guardo.",
            )
        return ResultadoDespacho.concluido(True)

    aprendizados = _deduplicar_aprendizados_para_fala(aprendizados)
    aprendizados = _filtrar_polaridade_preferencia(
        aprendizados,
        polaridade,
    )[:limite]
    deps.marcar_resultado("aprendizados_consultados", executou=True, confirmado=True)
    if not aprendizados:
        if modo == "verificar" and consulta:
            fala = (
                "Não encontrei isso entre os aprendizados confiáveis que tenho sobre você. "
                "Prefiro admitir a lacuna a completar no chute."
            )
        elif polaridade == "negativa":
            fala = (
                "Ainda não tenho nada confirmado sobre o que você não gosta. "
                "Prefiro deixar o espaço vazio a inventar uma implicância sua."
            )
        elif offset:
            fala = "Não achei outros aprendizados confiáveis além daqueles."
        else:
            fala = "Ainda não tenho nenhum aprendizado confiável seu guardado por aqui."
        _falar(ctx, fala)
        return ResultadoDespacho.concluido(True)

    def descrever(item: Dict[str, Any]) -> str:
        texto = _humanizar_aprendizado(item)
        recorte = texto if len(texto) <= 160 else texto[:157] + "..."
        natureza = str(item.get("natureza") or "").casefold()
        if item.get("confirmado_usuario") or natureza == "confirmado":
            return recorte
        if natureza == "padrao_percebido" or item.get("fonte") == "hipotese_madura":
            return f"percebi com boa confiança o padrão: {recorte}"
        if natureza == "observado_confiavel":
            return f"observei com boa confiança que {recorte}"
        return f"tenho este registro antigo, ainda sem confirmação direta: {recorte}"

    recortes = [descrever(item) for item in aprendizados]
    if modo == "verificar" and consulta:
        consulta_norm = normalizar_texto(consulta)
        registro_norm = normalizar_texto(recortes[0])
        consulta_negada = bool(re.search(r"\bnao\b", consulta_norm))
        registro_negado = bool(re.search(r"\b(?:voce\s+)?nao\b", registro_norm))
        prefixo = "Sim" if consulta_negada == registro_negado else "Não"
        fala = f"{prefixo}. {recortes[0].capitalize()}."
    elif modo == "origem":
        fala = f"Minha base para isso é o que você me contou diretamente: {recortes[0]}."
    else:
        todos_confirmados = all(
            bool(item.get("confirmado_usuario"))
            or str(item.get("natureza") or "").casefold() == "confirmado"
            for item in aprendizados
        )
        fala = falar_lembrancas(
            recortes,
            todos_confirmados=todos_confirmados,
        )
    _falar(ctx, fala)
    return ResultadoDespacho.concluido(True)


def executar_intencao_informacoes(
    intent: str,
    params: Dict[str, Any],
    texto_original: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    intent = str(intent or "").upper().strip()
    if intent not in INTENCOES_INFORMACOES:
        return ResultadoDespacho.nao_tratado()
    if intent == "EMAIL_READ":
        return _ler_emails(params, ctx, deps)
    if intent == "EMAIL_SYNC":
        return _sincronizar_emails(ctx, deps)
    if intent == "BRIEFING_REPEAT":
        return _repetir_briefing(texto_original, ctx, deps)
    if intent == "LEARNING_QUERY":
        return _consultar_aprendizados(params, texto_original, ctx, deps)
    return _consultar_clima(params, texto_original, ctx, deps)
