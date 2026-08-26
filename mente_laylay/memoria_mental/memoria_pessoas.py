"""Memória estruturada de pessoas e relações integrada à mente única.

O runtime só promove a fato aquilo que o usuário afirmou explicitamente. Ele
mantém proveniência, corrige versões antigas, trata homônimos e usa a pendência
canônica para qualquer esquecimento. A LLM recebe apenas o recorte relevante ao
turno e nunca é usada como banco de dados desta habilidade.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import tempfile
import threading
import unicodedata
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping

from mente_laylay.memoria_mental.registro_semantico import registrar_entidade


RELACOES = (
    "mãe", "pai", "irmã", "irmão", "prima", "primo", "amiga", "amigo",
    "namorada", "namorado", "esposa", "marido", "colega", "chefe", "tia",
    "tio", "avó", "avô", "filha", "filho", "sobrinha", "sobrinho",
)
_RELACOES_NORMALIZADAS = {
    "mae": "mãe", "pai": "pai", "irma": "irmã", "irmao": "irmão",
    "prima": "prima", "primo": "primo", "amiga": "amiga", "amigo": "amigo",
    "namorada": "namorada", "namorado": "namorado", "esposa": "esposa",
    "marido": "marido", "colega": "colega", "chefe": "chefe", "tia": "tia",
    "tio": "tio", "avo": "avó", "filha": "filha", "filho": "filho",
    "sobrinha": "sobrinha", "sobrinho": "sobrinho",
}
_RELACOES_RE = "|".join(sorted(_RELACOES_NORMALIZADAS, key=len, reverse=True))
_PALAVRAS_NAO_NOME = {
    "ela", "ele", "isso", "alguem", "alguém", "pessoa", "minha", "meu",
    "outra", "outro", "quem", "qual", "lay", "laylay", "voce", "você",
    "eu", "mim", "comigo", "usuario", "usuário",
    "gosta", "trabalha", "mora", "estuda", "joga", "prefere", "odeia",
}

_GENEROS_MUSICAIS = {
    "blues", "classica", "country", "eletronica", "forro", "funk", "gospel",
    "heavy metal", "hip hop", "indie", "jazz", "k pop", "metal", "mpb",
    "pagode", "pop", "punk", "rap", "reggae", "rock", "samba", "sertanejo",
    "soul", "trap",
}
_ARTISTAS_CANONICOS = {
    "anitta": "Anitta",
    "guns n roses": "Guns N’ Roses",
    "guns n' roses": "Guns N’ Roses",
}
_CHAVES_MULTIVALORADAS = {"gosta_de", "joga"}

_CARGOS_OU_TITULOS_PUBLICOS_RE = (
    r"presidente|vice presidente|primeir[oa] ministr[oa]|governador(?:a)?|"
    r"prefeit[oa]|ministr[oa]|senador(?:a)?|deputad[oa]|chanceler|"
    r"rei|rainha|imperador(?:a)?|papa"
)


def _consulta_sobre_cargo_publico(texto_normalizado: str) -> bool:
    """Separa conhecimento factual público da memória pessoal do usuário."""
    t = str(texto_normalizado or "").strip()
    moldura = re.search(
        r"\b(?:quem (?:e|eh)|o que (?:voce )?(?:sabe|lembra) "
        r"(?:sobre|da|do)|me (?:fala|conte) (?:sobre|da|do))\s+"
        r"(?P<alvo>.+)$",
        t,
    )
    if not moldura:
        return False
    alvo = str(moldura.group("alvo") or "").strip()
    cargo = re.search(rf"\b(?:{_CARGOS_OU_TITULOS_PUBLICOS_RE})\b", alvo)
    if not cargo:
        return False
    # Um título isolado também pode ser nome ou apelido de alguém realmente
    # apresentado pelo usuário (por exemplo, ``Rei``). Artigo, complemento ou
    # nome depois do cargo dão a evidência factual necessária para desviar a
    # pergunta da memória pessoal.
    antes = alvo[:cargo.start()].strip()
    depois = alvo[cargo.end():].strip()
    return bool(
        antes in {"o", "a", "do", "da"}
        or depois
        or " " in str(cargo.group(0) or "").strip()
    )


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9' -]+", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def _nome_apresentacao(nome: str) -> str:
    partes = [parte for parte in re.split(r"\s+", str(nome or "").strip()) if parte]
    return " ".join(parte[:1].upper() + parte[1:].lower() for parte in partes[:4])


def _nome_valido(nome: str) -> bool:
    normalizado = _normalizar(nome)
    partes = normalizado.split()
    return bool(
        1 <= len(partes) <= 4
        and all(1 < len(parte) <= 35 for parte in partes)
        and not any(parte in _PALAVRAS_NAO_NOME for parte in partes)
    )


def _agora_iso(agora: Callable[[], dt.datetime]) -> str:
    valor = agora()
    if valor.tzinfo is None:
        valor = valor.astimezone()
    return valor.isoformat(timespec="seconds")


def _parece_segredo(texto: str) -> bool:
    valor = str(texto or "")
    return bool(
        re.search(r"\bsk-[A-Za-z0-9_-]{16,}\b", valor)
        or re.search(
            r"\b(?:senha|password|token|api[_ -]?key|secret)\s*[:=]\s*\S{4,}",
            valor,
            flags=re.IGNORECASE,
        )
        or re.search(r"\b(?:\d[ -]*?){13,19}\b", valor)
    )


class MemoriaPessoasRuntime:
    VERSAO = 1

    def __init__(
        self,
        *,
        caminho: str | os.PathLike[str],
        falar: Callable[[str, str, int], Any],
        pendencia_runtime: Any,
        classificar_confirmacao_contextual: Callable[[str, str], Any] | None = None,
        registrar_resultado: Callable[..., Any] | None = None,
        registrar_mente_curta: Callable[..., Any] | None = None,
        registrar_aprendizado: Callable[..., Any] | None = None,
        esquecer_aprendizado: Callable[[str], Any] | None = None,
        estado_getter: Callable[[], Mapping[str, Any]] | None = None,
        estado_atualizar: Callable[[Callable[[dict], dict]], Any] | None = None,
        agora: Callable[[], dt.datetime] = lambda: dt.datetime.now().astimezone(),
        log: Callable[[str], Any] = print,
    ) -> None:
        self.caminho = Path(caminho)
        self.falar = falar
        self.pendencia_runtime = pendencia_runtime
        self.classificar_confirmacao_contextual = classificar_confirmacao_contextual
        self.registrar_resultado = registrar_resultado
        self.registrar_mente_curta = registrar_mente_curta
        self.registrar_aprendizado = registrar_aprendizado
        self.esquecer_aprendizado = esquecer_aprendizado
        self.estado_getter = estado_getter
        self.estado_atualizar = estado_atualizar
        self.agora = agora
        self.log = log
        self._lock = threading.RLock()

    def _vazio(self) -> dict[str, Any]:
        return {
            "versao": self.VERSAO,
            "pessoas": [],
            "historico": [],
            "ultimo_id": "",
            "metricas": {
                "observacoes": 0, "consultas": 0, "correcoes": 0,
                "esquecimentos": 0, "ambiguidades": 0, "falhas": 0,
            },
        }

    def _carregar(self) -> dict[str, Any]:
        with self._lock:
            if not self.caminho.exists():
                return self._vazio()
            try:
                bruto = json.loads(self.caminho.read_text(encoding="utf-8"))
            except Exception as erro:
                self.log(f"⚠️ [MEMÓRIA:PESSOAS] leitura falhou: {type(erro).__name__}")
                dados = self._vazio()
                dados["metricas"]["falhas"] = 1
                return dados
            dados = self._vazio()
            if isinstance(bruto, dict):
                dados["pessoas"] = [dict(x) for x in bruto.get("pessoas") or [] if isinstance(x, dict)]
                dados["historico"] = [dict(x) for x in bruto.get("historico") or [] if isinstance(x, dict)][-500:]
                dados["ultimo_id"] = str(bruto.get("ultimo_id") or "")
                dados["metricas"].update(dict(bruto.get("metricas") or {}))
            return dados

    def _salvar(self, dados: dict[str, Any]) -> bool:
        with self._lock:
            try:
                self.caminho.parent.mkdir(parents=True, exist_ok=True)
                fd, temporario = tempfile.mkstemp(
                    prefix=f".{self.caminho.name}.", suffix=".tmp",
                    dir=str(self.caminho.parent),
                )
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
                        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
                        arquivo.flush()
                        os.fsync(arquivo.fileno())
                    os.replace(temporario, self.caminho)
                finally:
                    if os.path.exists(temporario):
                        os.unlink(temporario)
                return True
            except Exception as erro:
                self.log(f"⚠️ [MEMÓRIA:PESSOAS] persistência falhou: {type(erro).__name__}")
                return False

    @staticmethod
    def _ativas(dados: dict[str, Any]) -> list[dict[str, Any]]:
        return [p for p in dados.get("pessoas") or [] if p.get("status") == "ativa"]

    def _por_nome(self, dados: dict[str, Any], nome: str) -> list[dict[str, Any]]:
        chave = _normalizar(nome)
        return [
            p for p in self._ativas(dados)
            if chave == _normalizar(p.get("nome"))
            or chave in {_normalizar(x) for x in p.get("aliases") or []}
        ]

    def _por_id(self, dados: dict[str, Any], pessoa_id: str) -> dict[str, Any] | None:
        return next((p for p in dados.get("pessoas") or [] if p.get("id") == pessoa_id), None)

    def _ultima(self, dados: dict[str, Any]) -> dict[str, Any] | None:
        pessoa = self._por_id(dados, str(dados.get("ultimo_id") or ""))
        return pessoa if pessoa and pessoa.get("status") == "ativa" else None

    def _emitir(self, texto_usuario: str, fala: str, *, intent: str, alvo: str = "", status: str) -> None:
        self.falar(fala, "calma", 1)
        resultado = {
            "intent": intent,
            "params": {"alvo": alvo} if alvo else {},
            "status": status,
            "executou": status not in {"aguardando_confirmacao", "ambiguo", "nao_encontrado"},
            "confirmado": status not in {"aguardando_confirmacao", "ambiguo", "nao_encontrado"},
        }
        if callable(self.registrar_resultado):
            self.registrar_resultado(
                resultado, texto_usuario, resultado["executou"],
                origem="memoria_pessoas", status=status,
            )
        if callable(self.registrar_mente_curta):
            self.registrar_mente_curta(
                texto_usuario, fala, intent, alvo, "pessoas", "memoria_pessoas",
            )

    def _publicar_semantica(self, pessoa: dict[str, Any]) -> None:
        if not callable(self.estado_atualizar):
            return
        relacoes = [
            r.get("tipo") for r in pessoa.get("relacoes") or []
            if r.get("status") == "ativo" and r.get("tipo")
        ]

        def atualizar(estado: dict) -> dict:
            registro = registrar_entidade(
                estado.get("registro_semantico"),
                {
                    "nome": pessoa.get("nome"), "tipo": "pessoa",
                    "dados": {
                        "pessoa_memoria_id": pessoa.get("id"),
                        "relacoes_confirmadas": relacoes,
                        "fonte": "usuario_explicito",
                    },
                },
                fonte="memoria_pessoas",
            )
            estado["registro_semantico"] = registro
            estado["ultima_habilidade"] = "memoria_pessoas"
            estado["ultima_acao_alvo"] = str(pessoa.get("nome") or "")
            return estado

        self.estado_atualizar(atualizar)

    def _remover_semantica(self, pessoa_id: str, nome: str) -> None:
        """Apaga da mente curta as referências do perfil confirmado."""
        if not callable(self.estado_atualizar):
            return
        nome_norm = _normalizar(nome)

        def menciona_nome(valor: Any) -> bool:
            texto = _normalizar(valor)
            return bool(nome_norm and re.search(rf"\b{re.escape(nome_norm)}\b", texto))

        def atualizar(estado: dict) -> dict:
            registro = dict(estado.get("registro_semantico") or {})
            entidades = dict(registro.get("entidades") or {})
            ids_removidos = {
                chave for chave, item in entidades.items()
                if isinstance(item, dict) and (
                    str((item.get("dados") or {}).get("pessoa_memoria_id") or "") == pessoa_id
                    or _normalizar(item.get("nome")) == nome_norm
                )
            }
            registro["entidades"] = {
                chave: item for chave, item in entidades.items() if chave not in ids_removidos
            }
            alegacoes_removidas = {
                str(item.get("id") or "") for item in registro.get("alegacoes") or []
                if isinstance(item, dict) and (
                    menciona_nome(item.get("sujeito")) or menciona_nome(item.get("texto"))
                )
            }
            registro["alegacoes"] = [
                item for item in registro.get("alegacoes") or []
                if isinstance(item, dict) and str(item.get("id") or "") not in alegacoes_removidas
            ]
            registro["assuntos"] = [
                item for item in registro.get("assuntos") or []
                if isinstance(item, dict)
                and str(item.get("entidade_id") or "") not in ids_removidos
                and not menciona_nome(item.get("titulo"))
            ]
            registro["correcoes"] = [
                item for item in registro.get("correcoes") or []
                if isinstance(item, dict)
                and str(item.get("alegacao_corrigida_id") or "") not in alegacoes_removidas
                and str(item.get("entidade_resultante_id") or "") not in ids_removidos
                and not menciona_nome(item.get("texto"))
            ]
            if str(registro.get("entidade_ativa_id") or "") in ids_removidos:
                registro["entidade_ativa_id"] = ""
            assunto_ids = {str(item.get("id") or "") for item in registro.get("assuntos") or []}
            if str(registro.get("assunto_ativo_id") or "") not in assunto_ids:
                registro["assunto_ativo_id"] = ""
            estado["registro_semantico"] = registro
            if _normalizar(estado.get("ultima_acao_alvo")) == nome_norm:
                estado["ultima_acao_alvo"] = ""
            return estado

        self.estado_atualizar(atualizar)

    def _aprender(self, pessoa: dict[str, Any], evento: str, evidencia: str) -> None:
        if not callable(self.registrar_aprendizado):
            return
        relacao = next(
            (r.get("tipo") for r in reversed(pessoa.get("relacoes") or []) if r.get("status") == "ativo"),
            "pessoa conhecida",
        )
        try:
            self.registrar_aprendizado(
                chave=f"pessoa:{pessoa.get('id')}:{evento}",
                tipo="memoria_pessoa_confirmada",
                escopo="pessoas_relacoes",
                valor={"descricao_humana": f"{pessoa.get('nome')} é {relacao} do usuário"},
                sinal=1.0,
                origem="usuario_explicito",
                evidencia=str(evidencia or "")[:300],
                confirmado_usuario=True,
            )
        except Exception as erro:
            self.log(f"⚠️ [MEMÓRIA:PESSOAS] aprendizado isolado: {type(erro).__name__}")

    def _aprender_decisao(self, pessoa_id: str, decisao: str, evidencia: str) -> None:
        if not callable(self.registrar_aprendizado):
            return
        try:
            self.registrar_aprendizado(
                chave="memoria_pessoas:feedback_esquecimento",
                tipo="feedback_memoria_pessoa",
                escopo="pessoas_relacoes",
                valor={"descricao_humana": f"decisão sobre esquecer perfil: {decisao}"},
                sinal=1.0 if decisao == "aceito" else -1.0,
                origem="feedback_usuario_explicito",
                evidencia=str(evidencia or "")[:200],
                confirmado_usuario=True,
            )
        except Exception as erro:
            self.log(f"⚠️ [MEMÓRIA:PESSOAS] feedback isolado: {type(erro).__name__}")

    def _classificacao_afirmacao(self, texto: str) -> str:
        t = _normalizar(texto)
        if re.search(r"\b(?:k{2,}|rsrs+|brincando|brincadeira|zoeira|to zoando)\b", t):
            return "brincadeira"
        if re.search(r"\b(?:talvez|acho que|pode ser|provavelmente|possivelmente)\b", t):
            return "hipotese"
        return "fato_confirmado"

    @staticmethod
    def _classificar_gosto(valor: str, preposicao: str) -> tuple[str, str]:
        """Separa preferências musicais sem depender da LLM ou perder o valor."""
        normalizado = _normalizar(valor)
        genero = normalizado.replace("musica ", "", 1)
        if genero in _GENEROS_MUSICAIS:
            return "genero_musical", genero
        if normalizado in _ARTISTAS_CANONICOS:
            return "artista_musical", _ARTISTAS_CANONICOS[normalizado]
        # A contração isolada não prova que algo é artista: "gosta da praia" e
        # "gosta dos gatos" também são frases válidas. Sem evidência suficiente,
        # preservamos o fato como preferência geral em vez de fabricar semântica.
        return "preferencia_geral", normalizado

    @staticmethod
    def _marcador_correcao(texto: str) -> bool:
        return bool(re.search(
            r"\b(?:na verdade|corrigindo|me enganei|retificando|quer dizer)\b",
            _normalizar(texto),
        ))

    def _registrar_fatos(
        self,
        pessoa: dict[str, Any],
        fatos: list[dict[str, str]],
        *,
        bruto: str,
        instante: str,
    ) -> bool:
        """Registra fatos, mantendo preferências cumulativas e idempotentes."""
        corrigiu = False
        correcao_explicita = self._marcador_correcao(bruto)
        existentes = pessoa.setdefault("fatos", [])
        for fato in fatos:
            chave = fato["chave"]
            categoria = fato.get("categoria", "")
            valor_normalizado = _normalizar(fato["valor"])
            for antigo in existentes:
                mesma_chave = antigo.get("chave") == chave
                categoria_antiga = str(antigo.get("categoria") or "")
                if chave == "gosta_de" and not categoria_antiga:
                    categoria_antiga, _ = self._classificar_gosto(
                        str(antigo.get("valor") or ""), "de",
                    )
                mesma_categoria = categoria_antiga == categoria
                mesmo_valor = _normalizar(antigo.get("valor")) == valor_normalizado
                if (
                    mesma_chave and mesma_categoria and not mesmo_valor
                    and antigo.get("status") == "ativo"
                    and (chave not in _CHAVES_MULTIVALORADAS or correcao_explicita)
                ):
                    antigo.update(status="corrigido", corrigida_em=instante)
                    corrigiu = True
            if not any(
                x.get("chave") == chave
                and (
                    str(x.get("categoria") or "") == categoria
                    or (
                        chave == "gosta_de" and not x.get("categoria")
                        and self._classificar_gosto(
                            str(x.get("valor") or ""), "de",
                        )[0] == categoria
                    )
                )
                and _normalizar(x.get("valor")) == valor_normalizado
                and x.get("status") == "ativo"
                for x in existentes
            ):
                existentes.append({
                    **fato, "status": "ativo", "fonte": "usuario_explicito",
                    "confianca": 1.0, "evidencia": bruto[:300], "criada_em": instante,
                })
        return corrigiu

    def _extrair_relacao(self, texto: str) -> dict[str, str] | None:
        t = _normalizar(texto)
        padroes = (
            rf"\b(?:a |o |outra |outro )?(?P<nome>[a-z][a-z' -]{{1,80}}?) (?:e|eh) (?:a |o )?(?:minha|meu) (?P<rel>{_RELACOES_RE})\b",
            rf"\b(?:minha|meu) (?P<rel>{_RELACOES_RE}) (?:se chama|chama|e|eh) (?P<nome>[a-z][a-z' -]{{1,80}}?)(?:\s*(?:,| e | mas | que |$))",
            rf"\b(?:minha|meu) (?P<rel>{_RELACOES_RE}) "
            rf"(?P<nome>(?!(?:gosta|trabalha|mora|estuda|joga|prefere|odeia)\b)"
            rf"[a-z][a-z'-]{{1,35}})(?:\s|,|$)",
            rf"\b(?:tenho|conheco) (?:uma|um) (?P<rel>{_RELACOES_RE}) (?:chamada|chamado) (?P<nome>[a-z][a-z' -]{{1,80}}?)(?:\s*(?:,| e | mas | que |$))",
            # Forma conversacional comum: "tenho uma namorada e o nome dela é
            # Nanda". O vínculo e o nome estão explícitos; não é inferência da
            # LLM e pode entrar na mesma memória confiável das formas acima.
            rf"\b(?:eu )?(?:tenho|conheco) (?:uma|um) (?P<rel>{_RELACOES_RE}) "
            rf"(?:e )?(?:(?:o|a) nome (?:dela|dele) (?:e|eh)|que (?:se )?chama) "
            rf"(?P<nome>[a-z][a-z' -]{{1,80}}?)(?:\s*(?:,| e | mas | que |$))",
        )
        # Correções costumam trazer a relação nova depois de "na verdade".
        correcao = bool(re.search(r"\b(?:na verdade|corrigindo|me enganei|retificando)\b", t))
        encontrados: list[dict[str, str]] = []
        for padrao in padroes:
            for achado in re.finditer(padrao, t):
                nome = re.sub(r"\b(?:na verdade|corrigindo|me enganei|retificando)\b", "", achado.group("nome")).strip(" ,")
                relacao = _RELACOES_NORMALIZADAS.get(achado.group("rel"), achado.group("rel"))
                if _nome_valido(nome):
                    encontrados.append({
                        "nome": _nome_apresentacao(nome), "relacao": relacao,
                        "correcao": "sim" if correcao else "nao",
                    })
        return encontrados[-1] if encontrados else None

    def _extrair_fatos(self, texto: str, nome: str) -> list[dict[str, str]]:
        t = _normalizar(texto)
        nome_n = re.escape(_normalizar(nome))
        sujeito = rf"(?:{nome_n}|ela|ele|(?:minha|meu) (?:{_RELACOES_RE}))"
        fatos: list[dict[str, str]] = []
        padroes = (
            ("gosta_de", rf"\b{sujeito} gosta (?P<prep>de|do|da|dos|das) (?P<valor>[^,.!?]{{2,100}})"),
            ("trabalha_em", rf"\b{sujeito} trabalha (?:em|na|no) (?P<valor>[^,.!?]{{2,100}})"),
            ("mora_em", rf"\b{sujeito} mora (?:em|na|no) (?P<valor>[^,.!?]{{2,100}})"),
            ("estuda", rf"\b{sujeito} estuda (?P<valor>[^,.!?]{{2,100}})"),
            ("joga", rf"\b{sujeito} joga (?P<valor>[^,.!?]{{2,100}})"),
        )
        for chave, padrao in padroes:
            achado = re.search(padrao, t)
            if achado:
                valor = achado.group("valor").strip(" ,")
                if valor and len(valor.split()) <= 16:
                    fato = {"chave": chave, "valor": valor}
                    if chave == "gosta_de":
                        categoria, valor_apresentacao = self._classificar_gosto(
                            valor, achado.group("prep"),
                        )
                        fato.update(categoria=categoria, valor=valor_apresentacao)
                    fatos.append(fato)
        return fatos

    def _observar_fato_isolado(self, bruto: str) -> bool:
        """Anexa um fato posterior à pessoa ativa sem exigir repetir a relação."""
        dados = self._carregar()
        t = _normalizar(bruto)
        pessoa = None
        nome = ""
        relacao_mencionada = re.search(
            rf"\b(?:minha|meu) (?P<rel>{_RELACOES_RE}) (?="
            r"gosta (?:de|do|da|dos|das)|trabalha (?:em|na|no)|"
            r"mora (?:em|na|no)|estuda |joga )",
            t,
        )
        if relacao_mencionada:
            relacao = _RELACOES_NORMALIZADAS.get(
                relacao_mencionada.group("rel"), relacao_mencionada.group("rel")
            )
            candidatas_relacao = [
                item for item in self._ativas(dados)
                if any(
                    registro.get("tipo") == relacao
                    and registro.get("status") == "ativo"
                    for registro in item.get("relacoes") or []
                )
            ]
            if len(candidatas_relacao) == 1:
                pessoa = candidatas_relacao[0]
                nome = str(pessoa.get("nome") or "")
            elif len(candidatas_relacao) > 1:
                dados["metricas"]["ambiguidades"] += 1
                self._salvar(dados)
                return False
        achado = re.search(
            r"\b(?P<nome>[a-z][a-z'-]{1,35}) (?=gosta (?:de|do|da|dos|das)|trabalha (?:em|na|no)|"
            r"mora (?:em|na|no)|estuda |joga )",
            t,
        )
        if not pessoa and achado and achado.group("nome") not in {"ela", "ele"}:
            nome = _nome_apresentacao(achado.group("nome"))
            candidatas = self._por_nome(dados, nome)
            if len(candidatas) > 1:
                dados["metricas"]["ambiguidades"] += 1
                self._salvar(dados)
                self.falar(f"Eu lembro de mais de uma pessoa chamada {nome}. Qual delas você quis dizer?", "curiosa", 1)
                return True
            pessoa = candidatas[0] if candidatas else None
        elif not pessoa and re.search(r"\b(?:ela|ele) (?:gosta (?:de|do|da|dos|das)|trabalha |mora |estuda |joga )", t):
            pessoa = self._ultima(dados)
            nome = str((pessoa or {}).get("nome") or "")
        if not nome or not _nome_valido(nome):
            return False
        instante = _agora_iso(self.agora)
        if pessoa is None:
            pessoa = {
                "id": f"pessoa:{uuid.uuid4().hex[:12]}", "nome": nome,
                "aliases": [nome], "status": "ativa", "relacoes": [],
                "fatos": [], "observacoes": [], "criada_em": instante,
                "atualizada_em": instante,
            }
            dados["pessoas"].append(pessoa)
        classificacao = self._classificacao_afirmacao(bruto)
        fatos = self._extrair_fatos(bruto, nome)
        if not fatos:
            return False
        if classificacao != "fato_confirmado":
            pessoa["observacoes"].append({
                "tipo": classificacao, "texto": bruto[:300], "fonte": "usuario",
                "confianca": 0.25 if classificacao == "brincadeira" else 0.40,
                "status": "contextual", "criada_em": instante,
            })
        else:
            corrigiu = self._registrar_fatos(
                pessoa, fatos, bruto=bruto, instante=instante,
            )
            if corrigiu:
                dados["metricas"]["correcoes"] += 1
                dados["historico"].append({
                    "evento": "correcao_fato", "pessoa_id": pessoa["id"],
                    "evidencia": bruto[:300], "em": instante,
                })
        pessoa["atualizada_em"] = instante
        dados["ultimo_id"] = pessoa["id"]
        dados["metricas"]["observacoes"] += 1
        if not self._salvar(dados):
            return False
        if classificacao == "fato_confirmado":
            self._publicar_semantica(pessoa)
            self._aprender(pessoa, "fato", bruto)
        return False

    def observar(self, texto: str) -> bool:
        bruto = str(texto or "").strip()
        if not bruto or "?" in bruto or _parece_segredo(bruto):
            return False
        relacao = self._extrair_relacao(bruto)
        if not relacao:
            return self._observar_fato_isolado(bruto)
        classificacao = self._classificacao_afirmacao(bruto)
        dados = self._carregar()
        candidatas = self._por_nome(dados, relacao["nome"])
        outro = bool(re.search(rf"\b(?:outro|outra)\s+{re.escape(_normalizar(relacao['nome']))}\b", _normalizar(bruto)))
        if len(candidatas) > 1 and not outro:
            dados["metricas"]["ambiguidades"] += 1
            self._salvar(dados)
            self.falar(
                f"Eu lembro de mais de uma pessoa chamada {relacao['nome']}. Qual delas você quer atualizar?",
                "curiosa", 1,
            )
            return True
        pessoa = None if outro else (candidatas[0] if candidatas else None)
        instante = _agora_iso(self.agora)
        if pessoa is None:
            pessoa = {
                "id": f"pessoa:{uuid.uuid4().hex[:12]}", "nome": relacao["nome"],
                "aliases": [relacao["nome"]], "status": "ativa",
                "relacoes": [], "fatos": [], "observacoes": [],
                "criada_em": instante, "atualizada_em": instante,
            }
            dados["pessoas"].append(pessoa)
        if classificacao != "fato_confirmado":
            pessoa["observacoes"].append({
                "tipo": classificacao, "texto": bruto[:300], "fonte": "usuario",
                "confianca": 0.25 if classificacao == "brincadeira" else 0.40,
                "status": "contextual", "criada_em": instante,
            })
        else:
            ativas = [r for r in pessoa.get("relacoes") or [] if r.get("status") == "ativo"]
            mudou = any(r.get("tipo") != relacao["relacao"] for r in ativas)
            repetiu = any(r.get("tipo") == relacao["relacao"] for r in ativas)
            if mudou:
                for item in ativas:
                    item.update(status="corrigido", corrigida_em=instante)
                dados["metricas"]["correcoes"] += 1
                dados["historico"].append({
                    "evento": "correcao_relacao", "pessoa_id": pessoa["id"],
                    "anteriores": [r.get("tipo") for r in ativas],
                    "nova": relacao["relacao"], "evidencia": bruto[:300], "em": instante,
                })
            if not any(r.get("tipo") == relacao["relacao"] and r.get("status") == "ativo" for r in pessoa.get("relacoes") or []):
                pessoa["relacoes"].append({
                    "tipo": relacao["relacao"], "status": "ativo", "fonte": "usuario_explicito",
                    "confianca": 1.0, "evidencia": bruto[:300], "criada_em": instante,
                })
            corrigiu_fato = self._registrar_fatos(
                pessoa, self._extrair_fatos(bruto, relacao["nome"]),
                bruto=bruto, instante=instante,
            )
            if corrigiu_fato:
                dados["metricas"]["correcoes"] += 1
                dados["historico"].append({
                    "evento": "correcao_fato", "pessoa_id": pessoa["id"],
                    "evidencia": bruto[:300], "em": instante,
                })
        pessoa["atualizada_em"] = instante
        dados["ultimo_id"] = pessoa["id"]
        dados["metricas"]["observacoes"] += 1
        dados["historico"] = dados["historico"][-500:]
        if not self._salvar(dados):
            return False
        if classificacao == "fato_confirmado":
            self._publicar_semantica(pessoa)
            evento = "correcao" if mudou or relacao["correcao"] == "sim" else "repeticao" if repetiu else "relacao"
            self._aprender(pessoa, evento, bruto)
            if callable(self.registrar_resultado):
                resultado = {
                    "intent": "PEOPLE_REMEMBER",
                    "params": {"alvo": pessoa["nome"]},
                    "status": "pessoa_memorizada",
                    "executou": True,
                    "confirmado": True,
                }
                self.registrar_resultado(
                    resultado, bruto, True,
                    origem="memoria_pessoas", status="pessoa_memorizada",
                )
        self.log(
            f"🧠 [MEMÓRIA:PESSOAS] pessoa={pessoa['nome']} "
            f"tipo={classificacao} relação={relacao['relacao']}"
        )
        # A conversa continua pela LLM; observar uma afirmação não sequestra o turno.
        return False

    def _detectar_pedido(self, texto: str) -> dict[str, Any] | None:
        bruto = str(texto or "").strip()
        t = _normalizar(bruto)
        if not t:
            return None
        # Correções leves só dentro de construções inequívocas de consulta.
        # Elas não são um corretor global de conversa e, por isso, não mudam
        # nomes nem frases livres que a pessoa quis escrever de propósito.
        t = re.sub(r"\b(?:voce\s+)?abe\s+(?:sobre|da|do)\b", "voce sabe sobre", t)
        t = re.sub(r"\bqual\s+(?:a\s+)?relacao\s+da\b", "qual a relacao da", t)
        # "Mim" referencia o próprio usuário. Nunca deve virar uma entidade
        # da memória de terceiros; essa consulta pertence ao aprendizado pessoal.
        if re.search(
            r"\b(?:o que (?:voce )?(?:sabe|lembra)|me (?:fala|conte)) "
            r"(?:sobre|de) (?:mim|comigo)\b",
            t,
        ):
            return None
        # Cargos e títulos públicos pertencem à consulta factual (e podem
        # exigir pesquisa atual), não ao arquivo local de pessoas apresentadas
        # pelo usuário. A memória pessoal não deve sequestrar essa pergunta.
        if _consulta_sobre_cargo_publico(t):
            return None
        if re.search(r"\b(?:quais|quem sao as) pessoas (?:voce |a laylay )?(?:lembra|conhece|que eu te falei)", t) or re.search(r"\b(?:quem eu (?:ja )?te apresentei|de quem eu (?:ja )?te falei)\b", t):
            return {"intent": "PEOPLE_LIST"}
        substantivo_operacional = re.search(
            r"\b(?:arquivo|aquivo|pasta|documento|diretorio|atalho|programa|app|aplicativo)\b",
            t,
        )
        apagar = None if substantivo_operacional else re.search(
            r"\b(?:"
            r"(?:esquece|esqueca) (?:tudo )?(?:que sabe )?(?:sobre |da |do |a |o )?"
            r"|(?:apaga|remove) (?:(?:a |o )?memoria (?:sobre |da |do )?|o que sabe sobre )"
            r")(?P<nome>[a-z][a-z' -]{1,80})$",
            t,
        )
        if apagar and _nome_valido(apagar.group("nome")):
            return {"intent": "PEOPLE_FORGET", "nome": _nome_apresentacao(apagar.group("nome"))}
        reversa = re.search(rf"\bquem (?:e|eh) (?:a |o )?(?:minha|meu) (?P<rel>{_RELACOES_RE})\b", t)
        if reversa:
            return {"intent": "PEOPLE_QUERY", "relacao": _RELACOES_NORMALIZADAS.get(reversa.group("rel"), reversa.group("rel"))}
        consulta_relacao = re.search(
            rf"\b(?:o que (?:voce )?(?:sabe|lembra) (?:sobre|da|do)|"
            rf"me (?:fala|conte) (?:sobre|da|do)) "
            rf"(?:a |o )?(?:minha|meu) (?P<rel>{_RELACOES_RE})\b",
            t,
        )
        if consulta_relacao:
            relacao = consulta_relacao.group("rel")
            return {
                "intent": "PEOPLE_QUERY",
                "relacao": _RELACOES_NORMALIZADAS.get(relacao, relacao),
            }
        consulta = re.search(
            r"\b(?:quem (?:e|eh)|o que (?:voce )?(?:sabe|lembra) (?:sobre|da|do)|"
            r"me (?:fala|conte) (?:sobre|da|do)) (?:a |o )?(?P<nome>[a-z][a-z' -]{1,80})$",
            t,
        )
        if consulta and _nome_valido(consulta.group("nome")):
            return {"intent": "PEOPLE_QUERY", "nome": _nome_apresentacao(consulta.group("nome"))}
        # ``me lembra de X`` e ``lembra de X`` são pedidos de agenda, não
        # consultas sobre uma pessoa chamada ``X``. O padrão antigo buscava
        # ``lembra de`` em qualquer posição e, por isso, capturava frases como
        # ``me lembra de beber água`` antes que o coordenador da agenda pudesse
        # vê-las. Uma consulta de pessoa precisa estar dirigida à Laylay
        # (``você lembra...``) ou ser inequivocamente interrogativa.
        lembra = re.search(
            r"^(?:voce )?lembra (?:da|do|de) "
            r"(?P<nome>[a-z][a-z' -]{1,80})$",
            t,
        )
        consulta_lembranca = bool(
            lembra
            and (t.startswith("voce lembra ") or "?" in bruto)
        )
        if consulta_lembranca and _nome_valido(lembra.group("nome")):
            return {"intent": "PEOPLE_QUERY", "nome": _nome_apresentacao(lembra.group("nome"))}
        relacao_com = re.search(r"\bqual (?:e )?(?:a )?minha relacao com (?P<nome>[a-z][a-z' -]{1,80})$", t)
        if relacao_com and _nome_valido(relacao_com.group("nome")):
            return {"intent": "PEOPLE_QUERY", "nome": _nome_apresentacao(relacao_com.group("nome"))}
        relacao_invertida = re.search(
            r"\bqual (?:e )?(?:a )?relacao (?:da|do|de) (?P<nome>[a-z][a-z' -]{1,80}?)"
            r"(?:\s+(?:comigo|com a gente|pra mim|para mim))?$",
            t,
        )
        if relacao_invertida and _nome_valido(relacao_invertida.group("nome")):
            return {"intent": "PEOPLE_QUERY", "nome": _nome_apresentacao(relacao_invertida.group("nome"))}
        relacao_eliptica = re.search(
            r"\b(?P<nome>[a-z][a-z' -]{1,80}) (?:e|eh) (?:minha|meu) (?:o que|quem)$",
            t,
        )
        if relacao_eliptica and _nome_valido(relacao_eliptica.group("nome")):
            return {"intent": "PEOPLE_QUERY", "nome": _nome_apresentacao(relacao_eliptica.group("nome"))}
        gosto = re.search(r"\bo que (?P<nome>[a-z][a-z' -]{1,50}) gosta\b", t)
        if gosto and _nome_valido(gosto.group("nome")):
            return {"intent": "PEOPLE_QUERY", "nome": _nome_apresentacao(gosto.group("nome"))}
        if re.search(r"\bo que (?:ela|ele) gosta\b|\bo que voce sabe (?:dela|dele)\b", t):
            return {"intent": "PEOPLE_QUERY", "ultimo": True}
        return None

    def _descricao(self, pessoa: dict[str, Any]) -> str:
        relacoes = [r.get("tipo") for r in pessoa.get("relacoes") or [] if r.get("status") == "ativo"]
        fatos = [f for f in pessoa.get("fatos") or [] if f.get("status") == "ativo"]
        if not relacoes and not fatos:
            return f"Você mencionou {pessoa.get('nome')}, mas ainda não me deu um fato confirmado sobre essa pessoa."
        partes = []
        if relacoes:
            femininas = {"mãe", "irmã", "prima", "amiga", "namorada", "esposa", "colega", "chefe", "tia", "avó", "filha", "sobrinha"}
            possessivo = "sua" if relacoes[-1] in femininas else "seu"
            partes.append(f"{pessoa.get('nome')} é {possessivo} {relacoes[-1]}")
        nome = str(pessoa.get("nome") or "Essa pessoa")
        gostos = []
        gostos_vistos: set[str] = set()
        for fato in fatos:
            if fato.get("chave") != "gosta_de":
                continue
            valor = str(fato.get("valor") or "").strip()
            normalizado = _normalizar(valor)
            if valor and normalizado not in gostos_vistos:
                gostos.append(valor)
                gostos_vistos.add(normalizado)
        outros = [f for f in fatos if f.get("chave") != "gosta_de"]

        def juntar_natural(valores: list[str]) -> str:
            valores = [valor for valor in valores if valor]
            if len(valores) <= 1:
                return "".join(valores)
            return ", ".join(valores[:-1]) + f" e {valores[-1]}"

        detalhes = []
        if gostos:
            detalhes.append(f"gosta de {juntar_natural(gostos)}")
        rotulos = {
            "trabalha_em": "trabalha em", "mora_em": "mora em",
            "estuda": "estuda", "joga": "joga",
        }
        detalhes.extend(
            f"{rotulos.get(fato.get('chave'), fato.get('chave'))} {fato.get('valor')}"
            for fato in outros[:3]
        )
        resposta = ". ".join(partes)
        if detalhes:
            prefixo = "Ela" if relacoes and relacoes[-1] in {
                "mãe", "irmã", "prima", "amiga", "namorada", "esposa", "colega",
                "chefe", "tia", "avó", "filha", "sobrinha",
            } else "Ele" if relacoes else nome
            resposta += f". Você me contou que {prefixo.lower() if resposta else prefixo} {'; '.join(detalhes)}"
        return resposta.lstrip(". ") + "."

    def _consultar(self, texto: str, pedido: dict[str, Any]) -> bool:
        dados = self._carregar()
        dados["metricas"]["consultas"] += 1
        pessoas: list[dict[str, Any]]
        if pedido.get("ultimo"):
            ultima = self._ultima(dados)
            pessoas = [ultima] if ultima else []
        elif pedido.get("relacao"):
            pessoas = [
                p for p in self._ativas(dados)
                if any(r.get("tipo") == pedido["relacao"] and r.get("status") == "ativo" for r in p.get("relacoes") or [])
            ]
        else:
            pessoas = self._por_nome(dados, str(pedido.get("nome") or ""))
        if not pessoas:
            alvo = str(pedido.get("nome") or pedido.get("relacao") or "essa pessoa")
            fala, status = f"Você ainda não me contou nada confiável sobre {alvo}.", "nao_encontrado"
        elif len(pessoas) > 1:
            nomes = ", ".join(str(p.get("nome") or "") for p in pessoas[:4])
            fala, status = f"Encontrei mais de uma possibilidade: {nomes}. Qual delas você quis dizer?", "ambiguo"
            dados["metricas"]["ambiguidades"] += 1
        else:
            pessoa = pessoas[0]
            dados["ultimo_id"] = pessoa["id"]
            if pedido.get("modo") == "complemento":
                fala = (
                    f"Não tenho outro fato confirmado sobre {pessoa.get('nome')} "
                    "além do que já te contei."
                )
                status = "sem_outros_fatos"
            else:
                fala, status = self._descricao(pessoa), "pessoa_encontrada"
        self._salvar(dados)
        alvo = str(pessoas[0].get("nome") or "") if len(pessoas) == 1 else str(pedido.get("nome") or "")
        self._emitir(texto, fala, intent="PEOPLE_QUERY", alvo=alvo, status=status)
        return True

    def _listar(self, texto: str) -> bool:
        dados = self._carregar()
        pessoas = self._ativas(dados)
        dados["metricas"]["consultas"] += 1
        self._salvar(dados)
        if not pessoas:
            fala = "Você ainda não me apresentou ninguém de um jeito que eu pudesse guardar com segurança."
        else:
            itens = []
            for pessoa in pessoas[:8]:
                relacao = next((r.get("tipo") for r in reversed(pessoa.get("relacoes") or []) if r.get("status") == "ativo"), "pessoa conhecida")
                itens.append(f"{pessoa.get('nome')} ({relacao})")
            fala = "Eu lembro de " + ", ".join(itens) + "."
            if len(pessoas) > 8:
                fala += f" E de mais {len(pessoas) - 8}."
        self._emitir(texto, fala, intent="PEOPLE_LIST", status="pessoas_listadas")
        return True

    def _pedir_esquecimento(self, texto: str, nome: str) -> bool:
        dados = self._carregar()
        pessoas = self._por_nome(dados, nome)
        if not pessoas:
            self._emitir(texto, f"Não encontrei uma memória ativa sobre {nome}.", intent="PEOPLE_FORGET", alvo=nome, status="nao_encontrado")
            return True
        if len(pessoas) > 1:
            self._emitir(texto, f"Há mais de uma pessoa chamada {nome}. Preciso que você especifique qual delas.", intent="PEOPLE_FORGET", alvo=nome, status="ambiguo")
            return True
        pergunta = f"Confirma que quer que eu esqueça o que guardei sobre {pessoas[0]['nome']}?"
        pendencia = self.pendencia_runtime.registrar(
            origem="memoria_pessoas", acao="esquecer_pessoa", pergunta=pergunta,
            referencia=pessoas[0]["id"], metadados={"pessoa_id": pessoas[0]["id"]},
            ttl_s=300.0,
        )
        if not pendencia:
            self.falar("Já existe outra confirmação em andamento. Terminamos aquela primeiro.", "calma", 1)
            return True
        self._emitir(texto, pergunta, intent="PEOPLE_FORGET", alvo=nome, status="aguardando_confirmacao")
        return True

    def _resolver_pendencia(self, texto: str) -> bool:
        atual = self.pendencia_runtime.obter()
        if str((atual or {}).get("origem") or "") != "memoria_pessoas":
            return False
        resolucao = self.pendencia_runtime.resolver(
            texto, classificar_contextual=self.classificar_confirmacao_contextual,
        )
        if not resolucao.get("tratado"):
            return False
        status = str(resolucao.get("status") or "")
        pendencia = dict(resolucao.get("pendencia") or {})
        pendencia_id = str(pendencia.get("id") or "")
        if status in {"em_processamento", "concorrente"}:
            return True
        if status == "recusar":
            self.pendencia_runtime.concluir(pendencia_id, "recusada")
            pessoa_id = str((pendencia.get("metadados") or {}).get("pessoa_id") or pendencia.get("referencia") or "")
            self._aprender_decisao(pessoa_id, "recusado", texto)
            self._emitir(texto, "Tudo bem, mantive essa memória como estava.", intent="PEOPLE_FORGET", status="cancelado")
            return True
        pessoa_id = str((pendencia.get("metadados") or {}).get("pessoa_id") or pendencia.get("referencia") or "")
        dados = self._carregar()
        pessoa = self._por_id(dados, pessoa_id)
        if not pessoa or pessoa.get("status") != "ativa":
            self.pendencia_runtime.concluir(pendencia_id, "nao_encontrada")
            self._emitir(texto, "Essa memória já não estava mais ativa.", intent="PEOPLE_FORGET", status="nao_encontrado")
            return True
        instante = _agora_iso(self.agora)
        nome = str(pessoa.get("nome") or "essa pessoa")
        indice = dados["pessoas"].index(pessoa)
        # A lápide prova que a operação aconteceu, mas não conserva nenhum
        # nome, relação, fato, evidência ou alias pessoal.
        dados["pessoas"][indice] = {
            "id": pessoa_id, "status": "esquecida", "esquecida_em": instante,
        }
        dados["historico"] = [
            item for item in dados.get("historico") or []
            if str(item.get("pessoa_id") or "") != pessoa_id
        ]
        dados["historico"].append({"evento": "esquecimento", "pessoa_id": pessoa_id, "em": instante})
        dados["metricas"]["esquecimentos"] += 1
        if dados.get("ultimo_id") == pessoa_id:
            dados["ultimo_id"] = ""
        salvo = self._salvar(dados)
        self.pendencia_runtime.concluir(pendencia_id, "concluida" if salvo else "falha_persistencia")
        if salvo:
            self._remover_semantica(pessoa_id, nome)
            if callable(self.esquecer_aprendizado):
                try:
                    self.esquecer_aprendizado(f"pessoa:{pessoa_id}:")
                except Exception as erro:
                    self.log(f"⚠️ [MEMÓRIA:PESSOAS] revogação isolada: {type(erro).__name__}")
            self._aprender_decisao(pessoa_id, "aceito", texto)
            self._emitir(texto, f"Pronto. Esqueci o perfil de {nome}.", intent="PEOPLE_FORGET", alvo=nome, status="pessoa_esquecida")
        else:
            self._emitir(texto, "Não consegui confirmar a alteração, então não vou dizer que esqueci.", intent="PEOPLE_FORGET", status="falha_persistencia")
        return True

    def processar(self, texto: str) -> bool:
        if self._resolver_pendencia(texto):
            return True
        pedido = self._detectar_pedido(texto)
        if pedido:
            intent = pedido.get("intent")
            if intent == "PEOPLE_LIST":
                return self._listar(texto)
            if intent == "PEOPLE_QUERY":
                return self._consultar(texto, pedido)
            if intent == "PEOPLE_FORGET":
                return self._pedir_esquecimento(texto, str(pedido.get("nome") or ""))
        return self.observar(texto)

    def contexto_para_prompt(self, texto: str) -> str:
        dados = self._carregar()
        t = _normalizar(texto)
        relevantes = [
            p for p in self._ativas(dados)
            if _normalizar(p.get("nome")) and re.search(rf"\b{re.escape(_normalizar(p.get('nome')))}\b", t)
        ]
        if not relevantes and re.search(r"\b(?:ela|ele|dela|dele|essa pessoa|esse amigo|essa amiga)\b", t):
            ultima = self._ultima(dados)
            relevantes = [ultima] if ultima else []
        if not relevantes:
            pedido = self._detectar_pedido(texto)
            if pedido and pedido.get("intent") == "PEOPLE_QUERY":
                referente = str(
                    pedido.get("nome") or pedido.get("relacao") or "essa pessoa"
                ).strip()
                return (
                    "MEMÓRIA DE PESSOAS RELEVANTE: não há memória confirmada "
                    f"sobre {referente}. Declare a ausência com sinceridade e "
                    "não invente lembranças, fatos, relações ou experiências."
                )
            return ""
        linhas = [
            "MEMÓRIA DE PESSOAS RELEVANTE: use apenas como relato confirmado do usuário; "
            "não complete lacunas, não confunda pessoas homônimas e não invente uma "
            "experiência pessoal sua para reagir ao relato. Ao registrar uma relação, "
            "reconheça nome e relação de forma neutra, sem sexualizar, insinuar intimidade "
            "ou abrir uma pergunta nova. Responda de forma breve e natural."
        ]
        for pessoa in relevantes[:2]:
            linhas.append(f"- {self._descricao(pessoa)}")
        return "\n".join(linhas)

    def diagnostico(self) -> dict[str, Any]:
        dados = self._carregar()
        ativas = self._ativas(dados)
        return {
            "ativas": len(ativas),
            "relacoes_ativas": sum(
                1 for p in ativas for r in p.get("relacoes") or [] if r.get("status") == "ativo"
            ),
            "fatos_ativos": sum(
                1 for p in ativas for f in p.get("fatos") or [] if f.get("status") == "ativo"
            ),
            "correcoes": int(dados.get("metricas", {}).get("correcoes") or 0),
            "esquecimentos": int(dados.get("metricas", {}).get("esquecimentos") or 0),
            "ambiguidades": int(dados.get("metricas", {}).get("ambiguidades") or 0),
            "falhas": int(dados.get("metricas", {}).get("falhas") or 0),
            "persistencia_local": True,
            "envio_externo": False,
        }

    def retrato_para_mente(self, texto: str = "") -> dict[str, Any]:
        """Retrato sanitizado para o catálogo de recursos, nunca acesso bruto."""
        dados = self._carregar()
        t = _normalizar(texto)
        pessoas = self._ativas(dados)
        detalhe = {}
        for pessoa in pessoas:
            if _normalizar(pessoa.get("nome")) and re.search(
                rf"\b{re.escape(_normalizar(pessoa.get('nome')))}\b", t,
            ):
                detalhe = {
                    "nome": pessoa.get("nome"),
                    "relacoes": [
                        r.get("tipo") for r in pessoa.get("relacoes") or []
                        if r.get("status") == "ativo"
                    ],
                }
                break
        return {
            "pessoas": [
                {
                    "nome": pessoa.get("nome"),
                    "relacoes": [
                        r.get("tipo") for r in pessoa.get("relacoes") or []
                        if r.get("status") == "ativo"
                    ],
                }
                for pessoa in pessoas[:20]
            ],
            "total_ativos": len(pessoas),
            "detalhe": detalhe,
            "parametros_consulta": {"nome": str(detalhe.get("nome") or "")},
        }

    def reexecutar(self, resultado: dict[str, Any], texto: str) -> bool:
        intent = str(resultado.get("intent") or "").upper().strip()
        params: dict[str, Any] = (
            dict(resultado.get("params") or {})
            if isinstance(resultado.get("params"), dict) else {}
        )
        if intent == "PEOPLE_LIST":
            return self._listar(texto)
        if intent == "PEOPLE_QUERY":
            nome = str(params.get("nome") or params.get("alvo") or "").strip()
            pedido = {
                "intent": intent,
                "nome": nome,
                "modo": str(params.get("modo") or "").strip(),
            }
            return self._consultar(texto, pedido) if nome else False
        return False


def criar_memoria_pessoas_runtime(**kwargs: Any) -> MemoriaPessoasRuntime:
    return MemoriaPessoasRuntime(**kwargs)
