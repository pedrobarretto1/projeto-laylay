# P0_REVISAO_INTRA_TURNO_V1_1_20260816
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict

_OPERACOES = (
    ("retomar", r"(?:continua|continue|continuar|retoma|retome|retomar|volta\s+a\s+tocar)"),
    ("maximizar", r"(?:maximiza|maximize|maximizar|tela\s+cheia|fullscreen)"),
    ("fechar", r"(?:fecha|feche|fechar|encerra|encerre|encerrar)"),
    ("abrir", r"(?:abre|abra|abrir|acessa|acesse|acessar)"),
    ("pausar", r"(?:pausa|pause|pausar)"),
    ("criar", r"(?:cria|crie|criar)"),
    ("apagar", r"(?:apaga|apague|apagar|deleta|delete|deletar|remove|remova|remover|exclui|exclua|excluir)"),
    ("ligar", r"(?:liga|ligue|ligar|acende|acenda|acender)"),
    ("desligar", r"(?:desliga|desligue|desligar)"),
    ("pesquisar", r"(?:pesquisa|pesquise|pesquisar|busca|busque|buscar|procura|procure|procurar|encontra|encontre|encontrar)"),
    ("tocar", r"(?:toca|toque|tocar|coloca|coloque|colocar|bota|bote|botar)"),
)

_VERBO_INICIO = re.compile(
    r"^\s*(?:me\s+)?(?P<verbo>" + "|".join(f"(?:{p})" for _, p in _OPERACOES) + r")\b(?:\s+(?P<resto>.*))?$",
    re.IGNORECASE,
)
_REVISAO = re.compile(
    r"(?P<sep>\.\.\.|…|;|,\s*|\bmas\s+)"
    r"(?P<espaco>\s*)"
    r"(?P<marker>não|nao|esquece|esqueça|quer\s+dizer|na\s+verdade|melhor)\b",
    re.IGNORECASE,
)

def _norm(valor: str) -> str:
    base = unicodedata.normalize("NFKD", str(valor or "").casefold())
    return "".join(ch for ch in base if not unicodedata.combining(ch))

def _intervalos_aspas(texto: str) -> list[tuple[int,int]]:
    pares = {'"':'"', '“':'”', "'":"'", '‘':'’'}
    intervalos=[]
    inicio=None
    fecha=None
    for i,ch in enumerate(texto):
        if inicio is None:
            if ch in pares:
                # apóstrofo só abre se houver outro adiante
                if ch == "'" and "'" not in texto[i+1:]:
                    continue
                inicio=i; fecha=pares[ch]
        else:
            if ch == fecha:
                intervalos.append((inicio, i))
                inicio=None; fecha=None
    if inicio is not None:
        intervalos.append((inicio, len(texto)-1))
    return intervalos

def _dentro_aspas(pos:int, intervalos:list[tuple[int,int]]) -> bool:
    return any(a <= pos <= b for a,b in intervalos)

def _operacao_inicio(texto: str) -> dict[str,str]:
    bruto=str(texto or "").strip(" \t\r\n,;:.!?…")
    m=_VERBO_INICIO.match(bruto)
    if not m:
        return {}
    verbo=m.group("verbo") or ""
    resto=(m.group("resto") or "").strip(" \t\r\n,;:.!?…")
    verbo_n=_norm(verbo)
    canon=""
    for nome,padrao in _OPERACOES:
        if re.fullmatch(padrao, verbo_n, re.I):
            canon=nome; break
    return {"canon":canon, "verbo":verbo, "resto":resto}

def _tem_operacao(texto:str)->bool:
    return bool(_operacao_inicio(texto))

def _alvo_da_proposta(proposta:str, operacao:dict[str,str]) -> str:
    canon=operacao.get("canon","")
    if canon=="criar":
        m=re.search(
            r"\b(?:arquivo|documento|pasta)\b.*?\b(?:chamad[oa]|com\s+nome)\s+(.+)$",
            proposta, re.I,
        )
        if m:
            return m.group(1).strip(" \t\r\n,;:!?…")
    resto=str(operacao.get("resto") or "").strip()
    resto=re.sub(r"^(?:o|a|os|as|um|uma)\s+", "", resto, flags=re.I)
    resto=re.sub(r"\s+\bagora\b$", "", resto, flags=re.I).strip()
    return resto.strip(" \t\r\n,;:.!?…")

def _resolver_pronome(texto:str, alvo:str) -> tuple[str,bool]:
    if not re.search(r"\b(?:ele|ela|isso|esse|essa|este|esta)\b", texto, re.I):
        return texto, True
    if not alvo:
        return texto, False
    novo=re.sub(r"\b(?:ele|ela|isso|esse|essa|este|esta)\b", alvo, texto, count=1, flags=re.I)
    return novo, True

def _nome_parametro(texto:str)->str:
    t=str(texto or "").strip(" \t\r\n,;:.!?…")
    m=re.match(
        r"^(?:chama|chame|chamar|nomeia|nomeie|nomear|renomeia|renomeie|renomear)"
        r"(?:\s+(?:de|para|pra))?\s+(.+)$",
        t, re.I,
    )
    if not m:
        m=re.match(r"^(?:o\s+)?nome\s+(?:e|é)\s+(.+)$", t, re.I)
    return (m.group(1).strip(" \t\r\n,;:!?…") if m else "")

def _substituir_nome_criacao(proposta:str, novo_nome:str)->str:
    return re.sub(
        r"(\b(?:chamad[oa]|com\s+nome)\s+)(.+)$",
        lambda m: m.group(1) + novo_nome,
        proposta.strip(" \t\r\n,;:.!?…"),
        count=1,
        flags=re.I,
    )

def _limpar_inicio_correcao(texto:str)->str:
    t=str(texto or "").strip(" \t\r\n,;:-.…")
    t=re.sub(r"^(?:entao|então|agora)\s+", "", t, flags=re.I)
    return t.strip()

def resolver_revisao_intra_turno(texto: str) -> Dict[str, Any]:
    bruto=re.sub(r"\s+", " ", str(texto or "")).strip()
    base={
        "detectada":False,
        "resolvida":False,
        "cancelada":False,
        "tipo":"",
        "texto_original":bruto[:500],
        "texto_operacional_efetivo":"",
        "proposta_anterior":"",
        "correcao":"",
        "alvo_herdado":"",
        "motivo":"",
    }
    if not bruto:
        return base
    intervalos=_intervalos_aspas(bruto)
    achado=None
    for m in _REVISAO.finditer(bruto):
        if _dentro_aspas(m.start("marker"), intervalos):
            continue
        proposta=bruto[:m.start()].strip(" \t\r\n,;:.!?…")
        if not _tem_operacao(proposta):
            continue
        achado=m
        break
    if achado is None:
        return base
    proposta=bruto[:achado.start()].strip(" \t\r\n,;:.!?…")
    marker=_norm(achado.group("marker"))
    correcao=_limpar_inicio_correcao(bruto[achado.end():])
    operacao_antiga=_operacao_inicio(proposta)
    alvo_antigo=_alvo_da_proposta(proposta, operacao_antiga)
    base.update(
        detectada=True,
        proposta_anterior=proposta[:300],
        correcao=correcao[:300],
        alvo_herdado=alvo_antigo[:160],
    )
    if marker in {"esquece","esqueca"} and not correcao:
        base.update(resolvida=True,cancelada=True,tipo="cancelamento",motivo="revisao descartou a proposta anterior")
        return base
    if marker in {"nao"} and not correcao:
        base.update(resolvida=True,cancelada=True,tipo="cancelamento",motivo="negação corretiva descartou a proposta anterior")
        return base

    # "não, melhor X" / "melhor X"
    correcao_sem_melhor=re.sub(r"^melhor\b[\s,:-]*", "", correcao, flags=re.I).strip()
    tinha_melhor=correcao_sem_melhor != correcao
    if tinha_melhor:
        correcao=correcao_sem_melhor

    nova_op=_operacao_inicio(correcao)
    if nova_op:
        # Elipses como "continua tocando" carregam a nova operação, mas
        # omitem o alvo que já estava explícito na proposta descartada.
        # Herdamos somente quando o complemento é um marcador de continuidade
        # sem alvo próprio; o executor recebe então uma fala autossuficiente.
        resto_novo=_norm(str(nova_op.get("resto") or "")).strip()
        if (
            alvo_antigo
            and nova_op.get("canon")=="retomar"
            and resto_novo in {"", "tocando", "a tocar"}
        ):
            correcao=f"{nova_op.get('verbo')} {alvo_antigo}".strip()
            nova_op=_operacao_inicio(correcao)
        # "apaga X... não apaga" = cancela, não é uma segunda exclusão sem alvo.
        if marker=="nao" and nova_op.get("canon")==operacao_antiga.get("canon") and not nova_op.get("resto"):
            base.update(resolvida=True,cancelada=True,tipo="cancelamento",motivo="negação repetiu a operação sem novo alvo")
            return base
        efetivo, ok=_resolver_pronome(correcao, alvo_antigo)
        if not ok:
            base.update(tipo="ambigua",motivo="correção usa referência sem alvo seguro da proposta anterior")
            return base
        base.update(
            resolvida=True,
            tipo="substituicao_acao" if nova_op.get("canon") != operacao_antiga.get("canon") else "substituicao_comando",
            texto_operacional_efetivo=efetivo.strip(" \t\r\n,;:.!?…")[:500],
            motivo="última proposta operacional explícita substitui a anterior",
        )
        return base

    novo_nome=_nome_parametro(correcao)
    if novo_nome and operacao_antiga.get("canon")=="criar":
        efetivo=_substituir_nome_criacao(proposta, novo_nome)
        if efetivo != proposta:
            base.update(
                resolvida=True,tipo="substituicao_parametro",
                texto_operacional_efetivo=efetivo[:500],
                motivo="correção alterou parâmetro da criação antes da execução",
            )
            return base

    # "abre X... não, melhor Y": mantém a operação, troca só o alvo.
    if (tinha_melhor or marker in {"quer dizer","na verdade","nao","melhor"}) and correcao:
        if operacao_antiga.get("canon") in {"abrir","fechar","maximizar","ligar","desligar","pesquisar","tocar"}:
            if len(correcao.split()) <= 8 and not re.search(r"\b(?:e depois|depois|entao|então)\b", correcao, re.I):
                efetivo=f"{operacao_antiga.get('verbo')} {correcao}".strip()
                base.update(
                    resolvida=True,tipo="substituicao_alvo",
                    texto_operacional_efetivo=efetivo[:500],
                    motivo="correção substituiu somente o alvo da proposta anterior",
                )
                return base

    if marker in {"esquece","esqueca"}:
        base.update(tipo="ambigua",motivo="houve cancelamento, mas a continuação não formou um comando seguro")
        return base

    base.update(tipo="ambigua",motivo="revisão detectada sem forma operacional segura")
    return base
