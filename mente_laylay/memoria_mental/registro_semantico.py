"""Memória semântica curta: entidades, alegações, assuntos e correções.

O registro não substitui o histórico textual. Ele oferece uma camada confiável
para decidir a que um pronome se refere e impede que respostas anteriores da
própria assistente sejam promovidas automaticamente a fatos.
"""

from __future__ import annotations

import math
import re
import time
import unicodedata
from typing import Any, Dict

from mente_laylay.cognicao.proveniencia_informacao import classificar_proveniencia_informacao


VERSAO_REGISTRO = 1


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9_\s.-]", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def _id_entidade(tipo: str, nome: str) -> str:
    chave = re.sub(r"[^a-z0-9]+", "_", _normalizar(nome)).strip("_")
    return f"{_normalizar(tipo) or 'entidade'}:{chave}"[:160]


def estado_registro_semantico_inicial() -> Dict[str, Any]:
    return {
        "versao": VERSAO_REGISTRO,
        "entidades": {},
        "alegacoes": [],
        "assuntos": [],
        "correcoes": [],
        "entidade_ativa_id": "",
        "assunto_ativo_id": "",
        "atualizado_ts": 0.0,
    }


def _registro(dados: Dict[str, Any] | None) -> Dict[str, Any]:
    base = estado_registro_semantico_inicial()
    if isinstance(dados, dict):
        base.update(dados)
    base["entidades"] = dict(base.get("entidades") or {})
    base["alegacoes"] = list(base.get("alegacoes") or [])
    base["assuntos"] = list(base.get("assuntos") or [])
    base["correcoes"] = list(base.get("correcoes") or [])
    return base


def registrar_entidade(
    registro: Dict[str, Any] | None,
    entidade: Dict[str, Any] | None,
    *,
    fonte: str = "usuario",
    agora: float | None = None,
) -> Dict[str, Any]:
    estado = _registro(registro)
    dados = dict(entidade or {})
    nome = str(dados.get("nome") or "").strip()
    tipo = str(dados.get("tipo") or "referencia_nomeada").strip().casefold()
    if not nome:
        return estado
    instante = float(agora if agora is not None else time.time())

    # Se o mesmo nome reaparece com um tipo mais específico, reaproveita o
    # registro anterior em vez de criar duas pessoas diferentes.
    nome_norm = _normalizar(nome)
    entidades = dict(estado.get("entidades") or {})
    existente_id = next(
        (
            chave for chave, item in entidades.items()
            if isinstance(item, dict) and _normalizar(item.get("nome")) == nome_norm
        ),
        "",
    )
    entidade_id = existente_id or _id_entidade(tipo, nome)
    anterior = dict(entidades.get(entidade_id) or {})
    tipo_anterior = str(anterior.get("tipo") or "")
    if tipo_anterior not in {"", "referencia_nomeada"} and tipo == "referencia_nomeada":
        tipo = tipo_anterior
    aliases = set(str(x).strip() for x in anterior.get("aliases") or [] if str(x).strip())
    aliases.add(nome)
    entidades[entidade_id] = {
        "id": entidade_id,
        "tipo": tipo,
        "nome": nome,
        "aliases": sorted(aliases)[:12],
        "fonte": str(fonte or dados.get("origem") or "usuario")[:60],
        "primeira_mencao_ts": float(anterior.get("primeira_mencao_ts") or instante),
        "ultima_mencao_ts": instante,
        "mencoes": min(999, int(anterior.get("mencoes") or 0) + 1),
        "confianca_identidade": max(float(anterior.get("confianca_identidade") or 0.0), 0.92),
        "dados": dict(dados.get("dados") or anterior.get("dados") or {}),
    }
    estado["entidades"] = entidades
    estado["entidade_ativa_id"] = entidade_id
    estado["atualizado_ts"] = instante
    return estado


def atualizar_assunto_semantico(
    registro: Dict[str, Any] | None,
    *,
    titulo: str = "",
    entidade_id: str = "",
    encerrar: bool = False,
    agora: float | None = None,
) -> Dict[str, Any]:
    estado = _registro(registro)
    instante = float(agora if agora is not None else time.time())
    assuntos = [dict(item) for item in estado.get("assuntos") or [] if isinstance(item, dict)]
    ativo_id = str(estado.get("assunto_ativo_id") or "")
    if encerrar:
        for item in assuntos:
            if item.get("id") == ativo_id and item.get("status") == "ativo":
                item.update(status="encerrado", encerrado_ts=instante, atualizado_ts=instante)
        estado.update(assuntos=assuntos[-20:], assunto_ativo_id="", atualizado_ts=instante)
        return estado
    nome = str(titulo or "").strip()
    if not nome:
        return estado
    chave_nome = _normalizar(nome)
    existente = next((item for item in reversed(assuntos) if _normalizar(item.get("titulo")) == chave_nome), None)
    if existente and existente.get("status") != "encerrado":
        for item in assuntos:
            if item.get("status") == "ativo" and item is not existente:
                item.update(status="pausado", atualizado_ts=instante)
        existente.update(status="ativo", atualizado_ts=instante, entidade_id=entidade_id or existente.get("entidade_id", ""))
        assunto_id = str(existente.get("id") or "")
    else:
        for item in assuntos:
            if item.get("status") == "ativo":
                item.update(status="pausado", atualizado_ts=instante)
        assunto_id = f"assunto:{int(instante * 1000)}"
        assuntos.append({
            "id": assunto_id,
            "titulo": nome[:160],
            "entidade_id": entidade_id,
            "status": "ativo",
            "iniciado_ts": instante,
            "atualizado_ts": instante,
        })
    estado.update(assuntos=assuntos[-20:], assunto_ativo_id=assunto_id, atualizado_ts=instante)
    return estado


def _eh_contestacao(texto: str) -> bool:
    return bool(re.search(
        r"\b(?:que\s+papo\s+(?:e|é)\s+esse|de\s+onde\s+(?:voce|você)\s+tirou|"
        r"isso\s+(?:e|é)\s+verdade|viajou|nada\s+a\s+ver|tem\s+certeza\s+disso)\b",
        str(texto or "").casefold(),
    ))


def _tipo_alegacao(texto: str) -> str:
    t = _normalizar(texto)
    if re.search(r"\b(?:acho|gosto|curto|prefiro|parece|na minha opiniao|minha impressao)\b", t):
        return "opiniao"
    if re.search(r"\b(?:talvez|pode ser|provavelmente|possivelmente)\b", t):
        return "hipotese"
    if re.search(
        r"\b(?:e|sou|estou|foi|era|teve|tenho|tem|nasceu|morreu|participo|participou|"
        r"vou participar|trabalho|trabalhou|criei|criou|ganhei|ganhou|chegou|tirei|fiz)\b",
        t,
    ):
        return "fato_candidato"
    return "comentario"


def registrar_alegacao(
    registro: Dict[str, Any] | None,
    texto: str,
    *,
    autor: str,
    sujeito: str = "",
    fonte: str = "",
    confianca: float | None = None,
    agora: float | None = None,
) -> Dict[str, Any]:
    estado = _registro(registro)
    conteudo = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not conteudo or len(conteudo) < 8:
        return estado
    if "?" in conteudo or re.match(
        r"^\s*(?:coloca|coloque|bota|toque|toca|abre|fecha|liga|desliga|apaga|remove|"
        r"cria|faz|me\s+lembra|me\s+avisa)\b",
        conteudo,
        flags=re.IGNORECASE,
    ):
        return estado
    tipo = _tipo_alegacao(conteudo)
    if tipo == "comentario":
        return estado
    instante = float(agora if agora is not None else time.time())
    autor_norm = str(autor or "desconhecido").casefold()
    if confianca is None:
        if tipo == "opiniao":
            nivel = 0.90
        elif autor_norm == "usuario":
            nivel = 0.65
        elif fonte:
            nivel = 0.82
        else:
            nivel = 0.35
    else:
        nivel = float(confianca)
    status = "opiniao" if tipo == "opiniao" else (
        "relatado_pelo_usuario" if autor_norm == "usuario" else (
            "confirmado_por_fonte" if fonte else "incerto"
        )
    )
    chave = f"{autor_norm}|{_normalizar(sujeito)}|{_normalizar(conteudo)}"
    alegacoes = [dict(item) for item in estado.get("alegacoes") or [] if isinstance(item, dict)]
    if any(str(item.get("chave") or "") == chave and instante - float(item.get("ts") or 0.0) < 120.0 for item in alegacoes):
        return estado
    alegacoes.append({
        "id": f"alegacao:{int(instante * 1000000)}",
        "chave": chave[:500],
        "sujeito": str(sujeito or "")[:160],
        "texto": conteudo[:500],
        "tipo": tipo,
        "autor": autor_norm,
        "fonte": str(fonte or "")[:200],
        "confianca": round(max(0.0, min(1.0, nivel)), 3),
        "status": status,
        "ts": instante,
    })
    estado.update(alegacoes=alegacoes[-60:], atualizado_ts=instante)
    return estado


def contestar_alegacao_recente(
    registro: Dict[str, Any] | None,
    contestacao: str,
    *,
    agora: float | None = None,
) -> Dict[str, Any]:
    estado = _registro(registro)
    if not _eh_contestacao(contestacao):
        return estado
    instante = float(agora if agora is not None else time.time())
    alegacoes = [dict(item) for item in estado.get("alegacoes") or [] if isinstance(item, dict)]
    for item in reversed(alegacoes):
        if item.get("autor") == "laylay" and item.get("status") not in {"contestado", "corrigido"}:
            item.update(
                status="contestado",
                confianca=min(0.10, float(item.get("confianca") or 0.0)),
                contestacao=str(contestacao or "")[:300],
                contestado_ts=instante,
            )
            break
    estado.update(alegacoes=alegacoes[-60:], atualizado_ts=instante)
    return estado


def corrigir_alegacao_recente(
    registro: Dict[str, Any] | None,
    correcao: str,
    *,
    agora: float | None = None,
) -> Dict[str, Any]:
    estado = _registro(registro)
    instante = float(agora if agora is not None else time.time())
    alegacoes = [dict(item) for item in estado.get("alegacoes") or [] if isinstance(item, dict)]
    corrigida_id = ""
    for item in reversed(alegacoes):
        if item.get("autor") == "laylay" and item.get("status") not in {"contestado", "corrigido"}:
            item.update(
                status="corrigido",
                confianca=min(0.05, float(item.get("confianca") or 0.0)),
                correcao=str(correcao or "")[:300],
                corrigido_ts=instante,
            )
            corrigida_id = str(item.get("id") or "")
            break
    estado["alegacoes"] = alegacoes[-60:]
    if corrigida_id:
        correcoes = list(estado.get("correcoes") or [])
        correcoes.append({
            "id": f"correcao:{int(instante * 1000000)}",
            "texto": str(correcao or "")[:500],
            "alegacao_corrigida_id": corrigida_id,
            "ts": instante,
        })
        estado["correcoes"] = correcoes[-30:]
    estado["atualizado_ts"] = instante
    return estado


def atualizar_registro_turno(
    registro: Dict[str, Any] | None,
    texto: str,
    *,
    retrato: Dict[str, Any] | None,
    funcao: str = "",
    encerramento: str = "",
    agora: float | None = None,
) -> Dict[str, Any]:
    instante = float(agora if agora is not None else time.time())
    estado = _registro(registro)
    snapshot = dict(retrato or {})
    explicita = dict(snapshot.get("entidade_explicita") or {})
    if explicita:
        estado = registrar_entidade(estado, explicita, fonte="usuario", agora=instante)
        entidade_id = str(estado.get("entidade_ativa_id") or "")
        estado = atualizar_assunto_semantico(
            estado, titulo=str(explicita.get("nome") or ""), entidade_id=entidade_id, agora=instante,
        )
    elif str(encerramento or "") == "topico":
        estado = atualizar_assunto_semantico(estado, encerrar=True, agora=instante)

    if str(funcao or "") == "correcao":
        estado = corrigir_alegacao_recente(estado, texto, agora=instante)
        correcoes = list(estado.get("correcoes") or [])
        correcoes.append({
            "id": f"correcao:{int(instante * 1000000)}",
            "texto": str(texto or "")[:500],
            "entidade_resultante_id": str(estado.get("entidade_ativa_id") or ""),
            "ts": instante,
        })
        estado["correcoes"] = correcoes[-30:]
    estado = contestar_alegacao_recente(estado, texto, agora=instante)
    estado["atualizado_ts"] = instante
    return estado


def renovar_registro_semantico_sessao(
    registro: Dict[str, Any] | None,
    *,
    motivo: str = "nova_sessao",
    agora: float | None = None,
) -> Dict[str, Any]:
    """Encerra o assunto transitório sem apagar fatos e correções duráveis."""
    estado = _registro(registro)
    instante = float(agora if agora is not None else time.time())
    assuntos = [dict(item) for item in estado.get("assuntos") or [] if isinstance(item, dict)]
    for item in assuntos:
        if item.get("status") in {"ativo", "pausado"}:
            item.update(status="encerrado", encerrado_ts=instante, atualizado_ts=instante)
    # Afirmações incertas produzidas pela própria Laylay não atravessam uma
    # reinicialização. Relatos do usuário, fontes, correções e contestações sim.
    alegacoes = [
        dict(item) for item in estado.get("alegacoes") or []
        if isinstance(item, dict)
        and not (item.get("autor") == "laylay" and item.get("status") == "incerto")
    ]
    estado.update(
        assuntos=assuntos[-20:],
        alegacoes=alegacoes[-60:],
        entidade_ativa_id="",
        assunto_ativo_id="",
        ultima_renovacao_motivo=str(motivo or "nova_sessao")[:80],
        atualizado_ts=instante,
    )
    return estado


def registrar_interacao_semantica(
    registro: Dict[str, Any] | None,
    *,
    texto_usuario: str = "",
    resposta_laylay: str = "",
    assunto: str = "",
    fonte_resposta: str = "",
    agora: float | None = None,
) -> Dict[str, Any]:
    instante = float(agora if agora is not None else time.time())
    estado = contestar_alegacao_recente(registro, texto_usuario, agora=instante)
    frases_usuario: list[str] = []
    if texto_usuario and not _eh_contestacao(texto_usuario):
        frases_usuario = [
            parte.strip() for parte in re.split(r"(?<=[.!?])\s+", texto_usuario) if parte.strip()
        ] or [texto_usuario]
        for indice, frase in enumerate(frases_usuario):
            estado = registrar_alegacao(
                estado, frase, autor="usuario", sujeito=assunto, agora=instante + indice / 1000000.0,
            )
    if resposta_laylay:
        frases_laylay = [
            parte.strip() for parte in re.split(r"(?<=[.!?])\s+", resposta_laylay) if parte.strip()
        ] or [resposta_laylay]
        for indice, frase in enumerate(frases_laylay):
            estado = registrar_alegacao(
                estado,
                frase,
                autor="laylay",
                sujeito=assunto,
                fonte=fonte_resposta,
                agora=instante + (len(frases_usuario) + indice + 1) / 1000000.0,
            )
    return estado


_TTL_TIPO = {
    "janela": 45.0,
    "app": 300.0,
    "site": 300.0,
    "iot": 600.0,
    "playlist": 600.0,
    "musica": 600.0,
    "jogo": 900.0,
    "artista": 1800.0,
    "cantor": 1800.0,
    "cantora": 1800.0,
    "banda": 1800.0,
    "referencia_nomeada": 1800.0,
}


# P0_ISOLAMENTO_CONTEXTO_20260814
def resolver_referencia_pontuada(
    texto: str,
    *,
    entidades_recentes: Dict[str, Any] | None,
    registro: Dict[str, Any] | None = None,
    operacao: str = "",
    agora: float | None = None,
) -> Dict[str, Any]:
    """P0.2A: domínio explícito restringe candidatos antes da recência."""
    instante = float(agora if agora is not None else time.time())
    recentes = {
        str(chave): dict(item)
        for chave, item in dict(entidades_recentes or {}).items()
        if isinstance(item, dict) and str(item.get("nome") or "").strip()
    }
    estado = _registro(registro)
    for entidade_id, item in dict(estado.get("entidades") or {}).items():
        if not isinstance(item, dict):
            continue
        tipo = str(item.get("tipo") or "referencia_nomeada")
        nome_item = str(item.get("nome") or "")
        if any(
            _normalizar(recente.get("nome")) == _normalizar(nome_item)
            for recente in recentes.values()
        ):
            continue
        chave = tipo if tipo not in recentes else f"{tipo}:{entidade_id}"
        recentes.setdefault(chave, {
            "tipo": tipo,
            "nome": nome_item,
            "origem": "registro_semantico",
            "ts": float(item.get("ultima_mencao_ts") or 0.0),
            "entidade_id": entidade_id,
        })

    t = _normalizar(texto)
    op = _normalizar(operacao)
    dominio = ""
    if op.startswith("playlist") or op == "musica_do_referente":
        dominio = "musica"
    elif op == "iot":
        dominio = "iot"
    elif op == "arquivo":
        dominio = "arquivo"
    elif re.search(r"\b(?:musica|som|faixa|cancao|playlist)\b", t):
        dominio = "musica"
    elif re.search(r"\b(?:luz|lampada|ventilador|tomada|dispositivo|aparelho)\b", t):
        dominio = "iot"
    elif re.search(
        r"\b(?:arquivo|pasta|documento|diretorio|markdown|extensao|formato)\b|"
        r"\.(?:txt|md)\b", t,
    ):
        dominio = "arquivo"
    elif re.search(r"\b(?:aba|guia|site|pagina)\b", t):
        dominio = "site"
    elif re.search(
        r"\b(?:app|aplicativo|programa|janela|opera|chrome|steam|vscode|"
        r"firefox|brave|calculadora)\b", t,
    ):
        dominio = "app"

    tipos = {
        "musica": {
            "artista", "cantor", "cantora", "banda", "referencia_nomeada",
            "musica", "playlist", "midia",
        },
        "iot": {"iot", "dispositivo"},
        "arquivo": {"arquivo", "pasta"},
        "app": {"app", "janela"},
        "site": {"site", "janela"},
    }
    permitidos = tipos.get(dominio, set())
    ativo_id = str(estado.get("entidade_ativa_id") or "")
    candidatos = []

    for chave, entidade in recentes.items():
        tipo = str(entidade.get("tipo") or chave).casefold()
        idade = max(0.0, instante - float(entidade.get("ts") or 0.0))
        ttl = float(_TTL_TIPO.get(tipo, 900.0))
        if idade > ttl:
            continue

        compativel = not dominio or tipo in permitidos
        score = 0.15 + (0.35 * math.exp(-3.0 * idade / max(ttl, 1.0)))
        origem = str(entidade.get("origem") or "")
        if origem == "nome_explicito":
            score += 0.30
        elif origem == "registro_semantico":
            score += 0.12
        if ativo_id and str(entidade.get("entidade_id") or "") == ativo_id:
            score += 0.25

        entidade_ativa = dict((estado.get("entidades") or {}).get(ativo_id) or {})
        if (
            ativo_id
            and _normalizar(entidade.get("nome"))
            == _normalizar(entidade_ativa.get("nome"))
        ):
            score += 0.25

        if dominio == "musica":
            score += 0.30 if tipo in tipos["musica"] else -0.25
        elif dominio == "iot":
            score += 0.35 if tipo in tipos["iot"] else -0.25
        elif dominio == "arquivo":
            score += 0.35 if tipo in tipos["arquivo"] else -0.25
        elif dominio == "site":
            score += 0.30 if tipo in tipos["site"] else -0.25
        elif dominio == "app":
            score += 0.30 if tipo in tipos["app"] else -0.20
        elif re.search(r"\b(?:abre|fecha|foco|maximiza)\b", t):
            score += 0.25 if tipo in tipos["app"] else -0.15

        if dominio and not compativel:
            score = 0.0
        score = max(0.0, min(1.0, score))
        candidatos.append({
            "chave": chave,
            "nome": str(entidade.get("nome") or ""),
            "tipo": tipo,
            "pontuacao": round(score, 3),
            "idade_s": round(idade, 1),
            "origem": origem,
            "dominio_restrito": dominio,
            "compativel_dominio": compativel,
            "entidade": dict(entidade),
        })

    candidatos.sort(
        key=lambda item: float(item.get("pontuacao") or 0.0),
        reverse=True,
    )
    elegiveis = [x for x in candidatos if x.get("compativel_dominio") is not False]
    melhor = (
        elegiveis[0]
        if elegiveis and float(elegiveis[0].get("pontuacao") or 0.0) >= 0.45
        else {}
    )
    return {
        "resolvida": dict(melhor.get("entidade") or {}),
        "chave": str(melhor.get("chave") or ""),
        "pontuacao": float(melhor.get("pontuacao") or 0.0),
        "dominio_restrito": dominio,
        "candidatos": [
            {k: v for k, v in item.items() if k != "entidade"}
            for item in candidatos[:5]
        ],
    }


def resumo_registro_semantico_para_prompt(
    registro: Dict[str, Any] | None,
    *,
    agora: float | None = None,
) -> str:
    estado = _registro(registro)
    instante = float(agora if agora is not None else time.time())
    entidades = dict(estado.get("entidades") or {})
    ativa = dict(entidades.get(str(estado.get("entidade_ativa_id") or "")) or {})
    assuntos = [item for item in estado.get("assuntos") or [] if isinstance(item, dict)]
    assunto_ativo = next((item for item in reversed(assuntos) if item.get("status") == "ativo"), {})
    alegacoes_confiaveis = []
    alegacoes_bloqueadas = []
    meias_vidas = {
        "confirmado_por_fonte": 30.0 * 86400.0,
        "relatado_pelo_usuario": 7.0 * 86400.0,
        "opiniao": 1.0 * 86400.0,
        "contestado": 30.0 * 86400.0,
        "corrigido": 30.0 * 86400.0,
    }
    for item in reversed(estado.get("alegacoes") or []):
        if not isinstance(item, dict):
            continue
        idade = max(0.0, instante - float(item.get("ts") or 0.0))
        status = str(item.get("status") or "incerto")
        meia_vida = float(meias_vidas.get(status, 3600.0))
        confianca_efetiva = float(item.get("confianca") or 0.0) * (0.5 ** (idade / meia_vida))
        autor = str(item.get("autor") or "")
        proveniencia = classificar_proveniencia_informacao(item, contexto="registro_semantico")
        tipo_proveniencia = str(proveniencia.get("tipo") or "sem_evidencia")
        rotulo = (
            "memória do usuário; apenas contexto pessoal"
            if tipo_proveniencia == "memoria_usuario"
            else "opinião do usuário; não é fato externo"
            if proveniencia.get("subtipo") == "opiniao_usuario"
            else "opinião da Laylay; não é fato"
            if tipo_proveniencia == "opiniao"
            else f"informação externa; fonte {item.get('fonte')}"
            if tipo_proveniencia == "informacao_externa"
            else status
        )
        resumo = (
            f"[{rotulo}; confiança_atual={confianca_efetiva:.2f}] "
            f"{item.get('sujeito') or 'assunto'}: {item.get('texto') or ''}"
        )
        if item.get("status") in {"contestado", "corrigido"}:
            alegacoes_bloqueadas.append(resumo)
        elif status in {"confirmado_por_fonte", "relatado_pelo_usuario", "opiniao"} and confianca_efetiva >= 0.25:
            alegacoes_confiaveis.append(resumo)
    partes = [
        "REGISTRO SEMÂNTICO CONFIÁVEL:",
        f"entidade_ativa={ativa.get('tipo') or '-'}:{ativa.get('nome') or '-'}",
        f"assunto_ativo={assunto_ativo.get('titulo') or '-'}",
    ]
    if alegacoes_confiaveis:
        partes.append("informações_utilizáveis=" + " | ".join(alegacoes_confiaveis[:4]))
    if alegacoes_bloqueadas:
        partes.append("alegações_bloqueadas=" + " | ".join(alegacoes_bloqueadas[:3]))
    partes.append(
        "Relatos e memórias do usuário valem para preferências, identidade e experiências dele, não como prova "
        "sobre o mundo. Opiniões continuam subjetivas. Respostas da Laylay com estado incerto não são fatos. "
        "Alegações contestadas ou corrigidas não podem ser reutilizadas."
    )
    return " ".join(partes)
