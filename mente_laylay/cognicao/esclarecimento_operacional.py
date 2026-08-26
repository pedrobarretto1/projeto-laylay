"""Contrato único para pedidos operacionais que ainda não têm dados suficientes.

Uma frase pode deixar clara a *vontade* do usuário sem conter o alvo que uma
habilidade precisa para agir. Em vez de entregar esse vazio à LLM (que pode
inventar um alvo) cada regra deste módulo produz uma pergunta objetiva e uma
pendência canônica. A resposta seguinte volta como uma intenção normal.

O registro é deliberadamente pequeno e declarativo: acrescentar uma nova
habilidade significa informar o intent, o campo obrigatório e seus padrões,
sem criar mais um atalho isolado no pré-fluxo.
"""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any, Callable, Dict, Iterable, Mapping

from mente_laylay.arquivos.nome_natural import (
    limpar_nome_arquivo_natural,
    tipo_arquivo_pelo_nome,
)
from mente_laylay.memoria_mental.pendencia import (
    criar_pendencia,
    limpar_pendencia,
    pendencia_ativa,
    registrar_pendencia,
)
from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_local,
)


ORIGEM_ESCLARECIMENTO_OPERACIONAL = "esclarecimento_operacional"
CHAVE_ESCLARECIMENTO_OPERACIONAL = "esclarecimento_operacional_ativo"


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    sem_acentos = "".join(char for char in base if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", sem_acentos).strip(" .,!?:;")


# Cada regra só aceita frases sem alvo. Isso é a fronteira importante: uma
# frase que já possui um nome, uma URL ou outro dado concreto continua no
# roteador canônico e jamais é "simplificada" por esta camada.
_REGRAS: tuple[Dict[str, Any], ...] = (
    {
        "intent": "MUSIC_SEARCH",
        "dominio": "musica",
        "campo": "query",
        "resposta_esperada": "nome da música, artista ou clima",
        "fala": "Eu topo. Qual faixa ou clima você quer?",
        "padroes": (
            r"(?:(?:eu )?(?:queria|gostaria de|estou a fim de|to a fim de|estou com vontade de|to com vontade de) (?:ouvir|escutar|colocar)|(?:coloca|coloque|toca|toque|bota|bote|poe|manda)) (?:uma |alguma |qualquer )?(?:musica|faixa|som)(?: (?:agora|mesmo|na verdade|so))?",
        ),
    },
    {
        "intent": "PLAYLIST_PLAY",
        "dominio": "musica",
        "campo": "nome_playlist",
        "resposta_esperada": "nome da playlist",
        "fala": "Qual playlist você quer ouvir?",
        "padroes": (
            r"(?:(?:eu )?(?:queria|gostaria de|quero) (?:ouvir|colocar)|(?:coloca|coloque|toca|toque|bota|bote|poe|manda)) (?:uma |alguma |qualquer )?playlist(?: agora| mesmo)?",
        ),
    },
    {
        "intent": "APP_OPEN",
        "dominio": "app",
        "campo": "nome_app",
        "resposta_esperada": "nome do programa",
        "fala": "Qual programa você quer abrir?",
        "padroes": (
            r"(?:(?:eu )?(?:queria|gostaria de|quero) abrir|(?:abre|abra|abre ai|abre pra mim)) (?:um |algum )?(?:programa|aplicativo|app)",
        ),
    },
    {
        "intent": "CREATE_FOLDER",
        "dominio": "arquivos",
        "campo": "nome",
        "resposta_esperada": "nome da pasta",
        "fala": "Qual nome você quer dar à pasta?",
        "padroes": (
            r"(?:cria|criar|crie|faz|fazer|faça) (?:uma |alguma )?pasta",
        ),
    },
    {
        "intent": "CREATE_FILE",
        "dominio": "arquivos",
        "campo": "alvo",
        "resposta_esperada": "nome do arquivo",
        "fala": "Qual nome você quer dar ao arquivo? Se não disser o tipo, faço um .txt.",
        "padroes": (
            r"(?:cria|criar|crie|faz|fazer|faça) (?:um |algum )?(?:arquivo|documento)(?: de (?:texto|txt))?",
        ),
        "params_base": {"tipo_arquivo": "texto"},
    },
    {
        "intent": "FILE_SEARCH",
        "dominio": "arquivos",
        "campo": "query",
        "resposta_esperada": "o que procurar nos arquivos",
        "fala": "O que você quer que eu procure nos seus arquivos?",
        "padroes": (
            r"(?:encontra|encontre|acha|ache|procura|procure|busca|busque|localiza|localize) (?:um |algum )?(?:arquivo|documento|codigo|script)",
        ),
    },
    {
        "intent": "SEARCH",
        "dominio": "pesquisa",
        "campo": "query",
        "resposta_esperada": "assunto da pesquisa",
        "fala": "O que você quer que eu pesquise?",
        "padroes": (
            r"(?:pesquisa|pesquise|procura|procure|busca|busque) (?:algo|alguma coisa|uma coisa|qualquer coisa)",
        ),
    },
)


def detectar_esclarecimento_operacional(texto: str) -> Dict[str, Any] | None:
    """Retorna o contrato de esclarecimento apenas quando falta um campo.

    Não infere alvo, não consulta a LLM e não executa nada.
    """
    normalizado = _normalizar(texto)
    if not normalizado or "?" in str(texto or ""):
        return None
    for regra_origem in _REGRAS:
        regra = dict(regra_origem)
        for padrao in tuple(regra.get("padroes") or ()):
            if re.fullmatch(str(padrao), normalizado):
                return {
                    "intent": str(regra["intent"]),
                    "dominio": str(regra["dominio"]),
                    "campo": str(regra["campo"]),
                    "resposta_esperada": str(regra["resposta_esperada"]),
                    "fala": str(regra["fala"]),
                    "params_base": dict(regra.get("params_base") or {}),
                    "origem": ORIGEM_ESCLARECIMENTO_OPERACIONAL,
                    "ttl_s": 180.0,
                }
    return None


def registrar_esclarecimento_operacional(
    estado_atual: Mapping[str, Any] | None,
    contrato: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Persiste a pergunta já falada na mente única, sem estado paralelo."""
    estado = dict(estado_atual or {})
    dados = dict(contrato or {})
    if not dados.get("intent") or not dados.get("campo") or not dados.get("fala"):
        return estado
    pendencia = criar_pendencia(
        origem=ORIGEM_ESCLARECIMENTO_OPERACIONAL,
        tipo="esclarecimento",
        dominio=str(dados.get("dominio") or "conversa"),
        conteudo=str(dados.get("fala") or ""),
        resposta_esperada=str(dados.get("resposta_esperada") or ""),
        intencao=str(dados.get("intent") or ""),
        ttl_s=float(dados.get("ttl_s") or 180.0),
        foi_falada=True,
    )
    estado = registrar_pendencia(estado, pendencia)
    ativa = dict(estado.get("pendencia_atual") or {})
    if (
        ativa.get("status") == "ativa"
        and str(ativa.get("origem") or "") == ORIGEM_ESCLARECIMENTO_OPERACIONAL
    ):
        estado[CHAVE_ESCLARECIMENTO_OPERACIONAL] = {
            "intent": str(dados.get("intent") or ""),
            "dominio": str(dados.get("dominio") or ""),
            "campo": str(dados.get("campo") or ""),
            "params_base": dict(dados.get("params_base") or {}),
            "pendencia_id": str(ativa.get("id") or ""),
            "criada_em": time.time(),
        }
    return estado


def limpar_esclarecimento_operacional(
    estado_atual: Mapping[str, Any] | None,
    *,
    motivo: str,
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    pendencia = dict(estado.get("pendencia_atual") or {})
    if str(pendencia.get("origem") or "") == ORIGEM_ESCLARECIMENTO_OPERACIONAL:
        estado = limpar_pendencia(estado, motivo=motivo)
    estado.pop(CHAVE_ESCLARECIMENTO_OPERACIONAL, None)
    return estado


def _texto_e_cancelamento(texto: str) -> bool:
    return classificar_confirmacao_local(texto) is False


def _valor_de_resposta(texto: str) -> str:
    valor = re.sub(r"\s+", " ", str(texto or "").strip()).strip(" .,!?:;")
    valor = re.sub(
        r"^(?:e |entao |então |seria |o nome (?:e|é) |chama(?:do|da)? |"
        r"pode ser |quero )+",
        "",
        valor,
        flags=re.IGNORECASE,
    ).strip(" .,!?:;")
    return valor


def resolver_esclarecimento_operacional(
    texto: str,
    estado_atual: Mapping[str, Any] | None,
    *,
    texto_tem_comando_explicito: Callable[[str], bool] | None = None,
) -> Dict[str, Any]:
    """Converte a resposta curta à pergunta pendente em intenção canônica.

    Um novo comando explícito não é usado como resposta: a pendência é
    substituída e o roteador normal pode cuidar da nova fala.
    """
    estado = dict(estado_atual or {})
    pendencia = pendencia_ativa(estado)
    ativo = dict(estado.get(CHAVE_ESCLARECIMENTO_OPERACIONAL) or {})
    if (
        not pendencia
        or str(pendencia.get("origem") or "") != ORIGEM_ESCLARECIMENTO_OPERACIONAL
        or not ativo
        or str(ativo.get("pendencia_id") or "") != str(pendencia.get("id") or "")
    ):
        return {"tipo": "nao_tratada"}

    if _texto_e_cancelamento(texto):
        return {"tipo": "cancelar"}
    if callable(texto_tem_comando_explicito) and texto_tem_comando_explicito(texto):
        return {"tipo": "substituir"}

    valor = _valor_de_resposta(texto)
    valor_norm = _normalizar(valor)
    genericos = {
        "uma musica", "alguma musica", "musica", "som", "faixa", "playlist",
        "um programa", "programa", "app", "aplicativo", "um arquivo", "arquivo",
        "uma pasta", "pasta", "algo", "alguma coisa", "uma coisa",
    }
    if not valor or valor_norm in genericos or len(valor) > 180:
        return {"tipo": "aguardar"}

    intent = str(ativo.get("intent") or "").upper().strip()
    campo = str(ativo.get("campo") or "").strip()
    if not intent or not campo:
        return {"tipo": "nao_tratada"}
    params = dict(ativo.get("params_base") or {})
    if intent == "CREATE_FILE" and campo == "alvo":
        valor = limpar_nome_arquivo_natural(valor)
        if not valor:
            return {"tipo": "aguardar"}
        params["tipo_arquivo"] = tipo_arquivo_pelo_nome(
            valor,
            str(params.get("tipo_arquivo") or ""),
        )
    params[campo] = valor
    params["origem"] = ORIGEM_ESCLARECIMENTO_OPERACIONAL
    return {
        "tipo": "executar",
        "intencao": {"intent": intent, "params": params},
    }


def regras_esclarecimento_operacional() -> Iterable[Dict[str, Any]]:
    """Exposição somente-leitura para diagnóstico e testes."""
    return tuple(dict(regra) for regra in _REGRAS)
