"""Caixa de entrada pessoal persistente integrada à mente única."""

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
from typing import Any, Callable
from urllib.parse import urlsplit

from mente_laylay.personalidade.confirmacao_llm import personalizar_informacao_llm


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base).strip()


def _parece_segredo(texto: str) -> bool:
    valor = str(texto or "")
    return bool(
        re.search(r"\bsk-[A-Za-z0-9_-]{16,}\b", valor)
        or re.search(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}\b", valor)
        or re.search(
            r"\b(?:senha|password|token|api[_ -]?key|secret)\s*[:=]\s*\S{4,}",
            valor,
            flags=re.IGNORECASE,
        )
        or re.search(r"\b(?:\d[ -]*?){13,19}\b", valor)
    )


def _classificar_tipo(texto: str, pedido: str = "") -> str:
    base = _normalizar(f"{pedido} {texto}")
    try:
        url = urlsplit(str(texto or "").strip())
    except Exception:
        url = None
    if url is not None and url.scheme in {"http", "https"} and url.netloc:
        return "link"
    if re.search(r"\b(?:tarefa|preciso|tenho que|fazer|resolver|comprar|entregar)\b", base):
        return "tarefa"
    if re.search(r"\b(?:ideia|poderia|seria legal|projeto)\b", base):
        return "ideia"
    if re.search(r"\b(?:pensamento|pensei|reflexao|reflexão)\b", base):
        return "pensamento"
    return "nota"


def _assuntos(texto: str, limite: int = 3) -> list[str]:
    ignorar = {
        "para", "como", "isso", "essa", "esse", "uma", "umas", "com", "que",
        "dos", "das", "por", "mais", "muito", "minha", "meu", "sobre", "quando",
        "onde", "depois", "antes", "tambem", "também", "porque", "fazer", "ideia",
    }
    vistos: list[str] = []
    for token in re.findall(r"[A-Za-zÀ-ÿ0-9_-]{3,}", str(texto or "").casefold()):
        if token in ignorar or token.isdigit() or token in vistos:
            continue
        vistos.append(token)
        if len(vistos) >= limite:
            break
    return vistos


def _extrair_json_objeto(resposta: Any) -> dict[str, Any]:
    texto = str(resposta or "").strip()
    if not texto:
        return {}
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.IGNORECASE)
    candidatos = [texto]
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio >= 0 and fim > inicio:
        candidatos.append(texto[inicio : fim + 1])
    for candidato in candidatos:
        try:
            dados = json.loads(candidato)
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        if isinstance(dados, dict):
            return dados
    return {}


def _tokens_conteudo(texto: Any) -> set[str]:
    ignorar = {
        "para", "como", "isso", "essa", "esse", "uma", "com", "que", "dos",
        "das", "por", "mais", "muito", "sobre", "tambem", "depois", "antes",
        "ideia", "laylay", "voce", "você", "minha", "nossa", "suas", "seus",
    }
    return {
        token for token in re.findall(r"[a-z0-9_-]{3,}", _normalizar(texto))
        if token not in ignorar
    }


class CaixaEntradaPessoalRuntime:
    VERSAO = 1

    def __init__(
        self,
        *,
        caminho: str | os.PathLike[str],
        falar: Callable[[str, str, int], Any],
        registrar_resultado: Callable[..., Any] | None = None,
        executar_intencao: Callable[[dict, str], bool] | None = None,
        contexto_getter: Callable[[], Any] | None = None,
        clipboard_getter: Callable[[], str] | None = None,
        observar_item: Callable[[dict[str, Any]], Any] | None = None,
        enviar_mensagem: Callable[..., Any] | None = None,
        agora: Callable[[], dt.datetime] = dt.datetime.now,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.caminho = Path(caminho)
        self.falar = falar
        self.registrar_resultado = registrar_resultado
        self.executar_intencao = executar_intencao
        self.contexto_getter = contexto_getter
        self.clipboard_getter = clipboard_getter
        self.observar_item = observar_item
        self.enviar_mensagem = enviar_mensagem
        self.agora = agora
        self.log = log
        self._lock = threading.RLock()
        self._pendencia: dict[str, Any] = {}
        self._ultimo_id = ""

    def _carregar(self) -> dict[str, Any]:
        with self._lock:
            if not self.caminho.exists():
                return {"versao": self.VERSAO, "itens": []}
            try:
                dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            except Exception as erro:
                self.log(f"⚠️ [CAIXA DE ENTRADA] leitura falhou: {type(erro).__name__}")
                return {"versao": self.VERSAO, "itens": []}
            itens = dados.get("itens") if isinstance(dados, dict) else []
            return {
                "versao": self.VERSAO,
                "itens": [dict(item) for item in itens if isinstance(item, dict)],
            }

    def _salvar(self, dados: dict[str, Any]) -> bool:
        with self._lock:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            temporario = ""
            try:
                fd, temporario = tempfile.mkstemp(
                    prefix="caixa_entrada_", suffix=".tmp", dir=str(self.caminho.parent)
                )
                with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
                    json.dump(dados, arquivo, ensure_ascii=False, indent=2)
                    arquivo.flush()
                    os.fsync(arquivo.fileno())
                os.replace(temporario, self.caminho)
                return True
            except Exception as erro:
                self.log(f"⚠️ [CAIXA DE ENTRADA] gravação falhou: {type(erro).__name__}")
                if temporario:
                    try:
                        os.unlink(temporario)
                    except OSError:
                        pass
                return False

    def detectar(self, texto: str) -> str:
        t = _normalizar(texto)
        if not t:
            return ""
        if self._pendencia and t in {"sim", "confirmo", "pode", "pode sim", "isso", "manda"}:
            return "confirmar"
        if self._pendencia and t in {"nao", "não", "cancela", "deixa", "melhor nao", "melhor não"}:
            return "cancelar"
        if re.search(r"\b(?:transforma|transforme|converte|converta)\b", t) and re.search(
            r"\b(?:nota|ideia|tarefa|isso|ela)\b", t
        ) and "lembrete" in t:
            return "converter_lembrete"
        pede_registro = bool(re.search(
            r"\b(?:anota|anote|guarda|guarde|salva|salve|registra|registre|resume|resuma)\b",
            t,
        ))
        refere_discussao = bool(re.search(
            r"\b(?:nossa (?:ideia|conversa|discussao)|essa (?:conversa|discussao)|"
            r"o que (?:discutimos|conversamos)|discussao inteira|conversa inteira|"
            r"minha ideia .{0,30}(?:sua ideia|suas sugestoes|sugestoes da laylay)|"
            r"ideia e .{0,20}(?:sugestoes|ideia da laylay)|resumo .{0,20}conversa)\b",
            t,
        ))
        if pede_registro and refere_discussao:
            return "adicionar_discussao"
        if re.search(r"\b(?:apaga|apague|exclui|exclua|remove|remova)\b", t) and re.search(
            r"\b(?:nota|ideia|tarefa|pensamento|item|anotacao|anotação)\b", t
        ):
            return "excluir"
        if re.search(r"\b(?:quais|mostra|mostre|lista|liste|o que tem|o que guardei|o que anotei)\b", t) and re.search(
            r"\b(?:caixa de entrada|nota|notas|ideia|ideias|tarefa|tarefas|anotei|guardei)\b", t
        ):
            return "listar"
        if (
            re.match(r"^(?:anota|anote|guarda|guarde|salva|salve|registra|registre)\b", t)
            or re.search(r"\b(?:coloca|coloque)\b.*\b(?:caixa de entrada|anotacoes|anotações)\b", t)
        ):
            return "adicionar"
        return ""

    def _ultima_fala_usuario(self, atual: str) -> str:
        if not callable(self.contexto_getter):
            return ""
        try:
            contexto = self.contexto_getter()
        except Exception:
            return ""
        mensagens = contexto.get("messages", []) if isinstance(contexto, dict) else contexto
        for item in reversed(list(mensagens or [])):
            if not isinstance(item, dict) or str(item.get("role") or "") != "user":
                continue
            conteudo = re.sub(r"\s+", " ", str(item.get("content") or "")).strip()
            if conteudo and _normalizar(conteudo) != _normalizar(atual):
                return conteudo[:4000]
        return ""

    def _mensagens_conversa(self, atual: str) -> list[dict[str, str]]:
        if not callable(self.contexto_getter):
            return []
        try:
            contexto = self.contexto_getter()
        except Exception:
            return []
        mensagens = contexto.get("messages", []) if isinstance(contexto, dict) else contexto
        limpas: list[dict[str, str]] = []
        ignorar_resposta_do_comando = False
        for item in list(mensagens or [])[-30:]:
            if not isinstance(item, dict):
                continue
            papel = str(item.get("role") or "").strip().lower()
            conteudo = re.sub(r"\s+", " ", str(item.get("content") or "")).strip()
            if papel not in {"user", "assistant"} or not conteudo:
                continue
            if papel == "user" and _normalizar(conteudo) == _normalizar(atual):
                # Uma tentativa anterior do mesmo pedido e a resposta que ela
                # produziu não fazem parte da ideia discutida.
                ignorar_resposta_do_comando = True
                continue
            if papel == "assistant" and ignorar_resposta_do_comando:
                ignorar_resposta_do_comando = False
                continue
            if papel == "user":
                ignorar_resposta_do_comando = False
            limpas.append({"role": papel, "content": conteudo[:2000]})
        return limpas

    @staticmethod
    def _parece_proposta_usuario(conteudo: str) -> bool:
        base = _normalizar(conteudo)
        if not base:
            return False
        pergunta_operacional = re.match(
            r"^(?:quais?|como|onde|quando|pode me|me manda|me da|o que|por que|porque)\b",
            base,
        )
        proposta = re.search(
            r"\b(?:tive uma ideia|ideia de|seria legal|ficaria (?:muito )?legal|"
            r"acho que|poderia|de fazer|vamos criar|quero (?:criar|fazer|melhorar)|"
            r"melhorar|criar)\b",
            base,
        )
        return bool(proposta and not pergunta_operacional)

    @staticmethod
    def _topico_pedido(texto: str) -> str:
        original = re.sub(r"\s+", " ", str(texto or "")).strip()
        encontrado = re.search(
            r"\b(?:sobre|a respeito d[aeo])\s+(.+?)(?:\s+(?:em|numa|em uma)\s+"
            r"(?:unica|única)\s+nota)?[.!?]*$",
            original,
            flags=re.IGNORECASE,
        )
        return encontrado.group(1).strip(" ,.!?")[:120] if encontrado else ""

    def _recortar_discussao(self, texto: str) -> tuple[list[dict[str, str]], str]:
        mensagens = self._mensagens_conversa(texto)
        if not mensagens:
            return [], ""
        topico = self._topico_pedido(texto)
        inicio = -1
        if topico:
            tokens_topico = _tokens_conteudo(topico)
            indices = [
                indice for indice, item in enumerate(mensagens)
                if tokens_topico and tokens_topico.intersection(_tokens_conteudo(item["content"]))
            ]
            if indices:
                inicio = min(indices[-4:])
                if inicio > 0 and mensagens[inicio]["role"] == "assistant":
                    inicio -= 1
        if inicio < 0:
            for indice in range(len(mensagens) - 1, -1, -1):
                item = mensagens[indice]
                if item["role"] != "user":
                    continue
                if self._parece_proposta_usuario(item["content"]):
                    # Até duas falas anteriores ajudam a resolver pronomes
                    # como "ela" sem trocar a ideia principal escolhida.
                    inicio = max(0, indice - 2)
                    break
        if inicio < 0:
            inicio = max(0, len(mensagens) - 6)
        trecho = mensagens[inicio:][-10:]
        if not any(item["role"] == "user" for item in trecho):
            return [], topico
        return trecho, topico

    @staticmethod
    def _titulo_discussao(topico: str, ideia: str) -> str:
        ideia_norm = _normalizar(ideia)
        if re.search(r"\bskins?\b", ideia_norm):
            estilos = [
                nome for nome in ("medieval", "futurista", "cyberpunk")
                if nome in ideia_norm
            ]
            if estilos:
                if len(estilos) == 1:
                    lista = estilos[0]
                else:
                    lista = ", ".join(estilos[:-1]) + " e " + estilos[-1]
                return f"Skins {lista} para o avatar"[:100]
        base = re.sub(r"\s+", " ", str(topico or ideia or "Ideia discutida")).strip(" .,:;!?")
        base = re.sub(
            r"^(?:lay[, ]+)?(?:eu )?(?:tive uma ideia (?:de|para)|acho que (?:seria legal )?|"
            r"seria legal|uma ideia (?:de|para)|de fazer)\s+",
            "",
            base,
            flags=re.IGNORECASE,
        ).strip()
        palavras = base.split()
        if len(palavras) > 9:
            base = " ".join(palavras[:9])
        return base[:100].capitalize()

    def _ideia_principal(self, trecho: list[dict[str, str]]) -> str:
        usuarios = [item["content"] for item in trecho if item["role"] == "user"]
        for fala in reversed(usuarios):
            if self._parece_proposta_usuario(fala):
                return fala
        return usuarios[0] if usuarios else ""

    @staticmethod
    def _sugestoes_uteis(trecho: list[dict[str, str]]) -> list[str]:
        sugestoes: list[str] = []
        for item in trecho:
            if item["role"] != "assistant":
                continue
            fala = re.sub(r"\s+", " ", item["content"]).strip()
            base = _normalizar(fala)
            if len(fala.split()) < 3 or re.search(
                r"\b(?:resposta escapou|nao consegui guardar|notebook aberto|"
                r"ideias vao girando|me fala de outro jeito|modelo local)\b",
                base,
            ):
                continue
            partes = re.split(r"(?<=[.!?])\s+|\s+[—-]\s+", fala)
            candidatas = [
                parte.strip(" -") for parte in partes
                if re.search(
                    r"\b(?:podemos|posso|sugiro|adicionar|criar|fazer|usar|"
                    r"uma (?:skin|versao|versão|com)|descri(?:cao|ção))\b",
                    _normalizar(parte),
                )
                and not parte.strip().endswith("?")
            ]
            if candidatas:
                sugestao = " ".join(candidatas)[:360]
                if _normalizar(sugestao) not in {_normalizar(valor) for valor in sugestoes}:
                    sugestoes.append(sugestao)
        return sugestoes[-4:]

    @staticmethod
    def _resumir_ideia_literal(ideia: str, trecho: list[dict[str, str]]) -> str:
        resumo = re.sub(r"\s+", " ", str(ideia or "")).strip(" .")
        resumo = re.sub(
            r"^(?:lay[, ]+)?(?:eu )?(?:tive uma ideia (?:de|para)|acho que (?:seria legal )?|"
            r"seria legal|uma ideia (?:de|para)|de fazer)\s+",
            lambda m: "Fazer " if "de fazer" in _normalizar(m.group(0)) else "",
            resumo,
            flags=re.IGNORECASE,
        ).strip()
        resumo = re.sub(r",?\s+ficaria (?:muito )?legal(?:,?\s*n[éèe])?\??$", "", resumo, flags=re.IGNORECASE)
        resumo = re.sub(r"\bvarias?\s+skin\b", "várias skins", resumo, flags=re.IGNORECASE)
        contexto = _normalizar(" ".join(item["content"] for item in trecho))
        if "avatar" in contexto and re.search(r"\bpara ela\b", resumo, flags=re.IGNORECASE):
            resumo = re.sub(r"\bpara ela\b", "para o avatar da Laylay", resumo, flags=re.IGNORECASE)
        if resumo:
            resumo = resumo[0].upper() + resumo[1:]
        return resumo.rstrip(" ,;:.!?") + "."

    def _resumo_deterministico(
        self,
        trecho: list[dict[str, str]],
        topico: str,
    ) -> dict[str, Any]:
        falas_usuario = [item["content"] for item in trecho if item["role"] == "user"]
        falas_laylay = [item["content"] for item in trecho if item["role"] == "assistant"]
        ideia = self._ideia_principal(trecho)
        sugestoes = self._sugestoes_uteis(trecho)
        decisoes = [
            fala[:240] for fala in falas_usuario[1:]
            if re.search(r"\b(?:vamos|fechado|decid|pode fazer|gostei|prefiro)\b", _normalizar(fala))
        ][-3:]
        proximos = [
            fala[:240] for fala in falas_laylay
            if re.search(r"\b(?:proximo|depois|implementar|comecar|primeiro passo)\b", _normalizar(fala))
        ][-3:]
        resumo = self._resumir_ideia_literal(ideia, trecho)
        return {
            "titulo": self._titulo_discussao(topico, ideia),
            "ideia_original": ideia,
            "resumo": resumo[:1800],
            "sugestoes_laylay": sugestoes,
            "decisoes": decisoes,
            "proximos_passos": proximos,
        }

    def _resumir_discussao_llm(
        self,
        trecho: list[dict[str, str]],
        topico: str,
    ) -> dict[str, Any]:
        fallback = self._resumo_deterministico(trecho, topico)
        if not callable(self.enviar_mensagem):
            return fallback
        transcricao = "\n".join(
            f"{'USUÁRIO' if item['role'] == 'user' else 'LAYLAY'}: {item['content']}"
            for item in trecho
        )
        sistema = (
            "Organize uma discussão já ocorrida sem acrescentar informação. Separe autoria: "
            "ideia_original deve ser uma fala literal do USUÁRIO; cada sugestão da Laylay, "
            "decisão e próximo passo deve ser um trecho literal da transcrição. O resumo pode "
            "ligar essas evidências em linguagem curta, mas não pode criar proposta nova. "
            "Retorne apenas JSON com titulo, ideia_original, resumo, sugestoes_laylay, decisoes "
            "e proximos_passos. Os quatro últimos campos de coleção são listas de strings."
        )
        try:
            resposta = self.enviar_mensagem(
                [
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": f"Tópico indicado: {topico or 'não indicado'}\n\n{transcricao}"},
                ],
                _com_tools=False,
                max_tokens=520,
                modo_rapido=True,
                timeout=3,
                _prioridade_interativa=False,
            )
        except Exception:
            return fallback
        dados = _extrair_json_objeto(resposta)
        usuarios = _normalizar(" ".join(item["content"] for item in trecho if item["role"] == "user"))
        assistente = _normalizar(" ".join(item["content"] for item in trecho if item["role"] == "assistant"))
        todos = _normalizar(" ".join(item["content"] for item in trecho))
        ideia = re.sub(r"\s+", " ", str(dados.get("ideia_original") or "")).strip()
        resumo = re.sub(r"\s+", " ", str(dados.get("resumo") or "")).strip()
        colecoes: dict[str, list[str]] = {}
        fontes = {
            "sugestoes_laylay": assistente,
            "decisoes": todos,
            "proximos_passos": todos,
        }
        for chave, fonte in fontes.items():
            valores = dados.get(chave)
            if not isinstance(valores, list):
                return fallback
            limpos = [re.sub(r"\s+", " ", str(valor or "")).strip() for valor in valores[:5]]
            if any(valor and _normalizar(valor) not in fonte for valor in limpos):
                return fallback
            colecoes[chave] = [valor[:360] for valor in limpos if valor]
        if (
            not ideia
            or _normalizar(ideia) != _normalizar(fallback["ideia_original"])
            or _normalizar(ideia) not in usuarios
            or not resumo
        ):
            return fallback
        tokens_resumo = _tokens_conteudo(resumo)
        tokens_fonte = _tokens_conteudo(todos)
        if tokens_resumo and len(tokens_resumo & tokens_fonte) / len(tokens_resumo) < 0.65:
            return fallback
        titulo = re.sub(r"\s+", " ", str(dados.get("titulo") or "")).strip()
        if not titulo or not _tokens_conteudo(titulo).intersection(tokens_fonte | _tokens_conteudo(topico)):
            titulo = self._titulo_discussao(topico, ideia)
        return {
            "titulo": titulo[:100],
            "ideia_original": ideia[:1000],
            "resumo": resumo[:1800],
            **colecoes,
        }

    def _extrair_conteudo(self, texto: str) -> tuple[str, str]:
        t = str(texto or "").strip()
        normalizado = _normalizar(t)
        refere_clipboard = bool(re.search(r"\b(?:link|texto|conteudo)\s+copiad[oa]|o que eu copiei\b", normalizado))
        if refere_clipboard and callable(self.clipboard_getter):
            try:
                copiado = str(self.clipboard_getter() or "").strip()
            except Exception:
                copiado = ""
            if copiado:
                return copiado[:4000], "clipboard"

        conteudo = re.sub(
            r"^(?:anota|anote|guarda|guarde|salva|salve|registra|registre)\b",
            "", t, flags=re.IGNORECASE,
        ).strip(" ,:-")
        conteudo = re.sub(
            r"^(?:(?:essa|esta|uma|a|esse|este|um|o|minha|meu)\s+)?"
            r"(?:ideia|nota|tarefa|pensamento|link)?\s*",
            "", conteudo, flags=re.IGNORECASE,
        ).strip(" ,:-")
        conteudo = re.sub(
            r"\s+(?:na|no|para a|em)\s+(?:minha\s+)?(?:caixa de entrada|anotacoes|anotações|notas)\s*$",
            "", conteudo, flags=re.IGNORECASE,
        ).strip(" ,:-")
        generico = not conteudo or _normalizar(conteudo) in {
            "isso", "essa", "ela", "essa ideia", "essa nota", "esse pensamento",
        } or bool(re.match(r"^(?:isso|essa ideia|essa nota)\s+para\s+eu\s+ver\b", _normalizar(conteudo)))
        if generico:
            anterior = self._ultima_fala_usuario(t)
            if anterior:
                return anterior, "conversa"
        return conteudo[:4000], "pedido"

    def _registrar(self, resultado: dict, texto: str, executou: bool, *, status: str) -> None:
        if callable(self.registrar_resultado):
            self.registrar_resultado(
                resultado, texto, executou, origem="caixa_entrada_pessoal", status=status,
            )

    def _adicionar(self, texto: str) -> bool:
        conteudo, origem = self._extrair_conteudo(texto)
        if not conteudo:
            self.falar("O que você quer que eu anote?", "calma", 1)
            return True
        if _parece_segredo(conteudo):
            self.falar("Isso parece conter um segredo ou dado sensível. Não vou colocar na caixa.", "preocupada", 2)
            return True
        agora = self.agora()
        tipo = _classificar_tipo(conteudo, texto)
        item = {
            "id": uuid.uuid4().hex[:10],
            "tipo": tipo,
            "conteudo": conteudo,
            "assuntos": _assuntos(conteudo),
            "status": "ativo",
            "origem": origem,
            "criado_em": agora.isoformat(),
            "atualizado_em": agora.isoformat(),
        }
        if re.search(r"\bamanha\b", _normalizar(texto)):
            item["revisar_em"] = (agora + dt.timedelta(days=1)).date().isoformat()
        dados = self._carregar()
        dados["itens"].append(item)
        ok = self._salvar(dados)
        resultado = {
            "intent": "INBOX_ADD",
            "params": {"nota_id": item["id"], "tipo_nota": tipo, "alvo": conteudo[:180]},
        }
        self._registrar(resultado, texto, ok, status="nota_guardada" if ok else "falha_execucao")
        if ok:
            self._ultimo_id = item["id"]
            if callable(self.observar_item):
                try:
                    self.observar_item(dict(item))
                except Exception as erro:
                    self.log(f"⚠️ [CAIXA DE ENTRADA] aprendizado isolado: {type(erro).__name__}")
            complemento = " e marquei para você rever amanhã" if item.get("revisar_em") else ""
            self.falar(f"Guardei como {tipo}{complemento}.", "feliz", 1)
        else:
            self.falar("Entendi a nota, mas o arquivo não confirmou a gravação.", "calma", 1)
        return True

    def _adicionar_discussao(self, texto: str) -> bool:
        trecho, topico = self._recortar_discussao(texto)
        if not trecho:
            self.falar(
                "Não achei uma discussão recente para resumir. Me diz qual ideia você quer guardar.",
                "calma",
                1,
            )
            return True
        conteudo_bruto = " ".join(item["content"] for item in trecho)
        if _parece_segredo(conteudo_bruto):
            self.falar(
                "Essa conversa parece conter um segredo ou dado sensível. Não vou salvar o resumo.",
                "preocupada",
                2,
            )
            return True

        try:
            estrutura = self._resumir_discussao_llm(trecho, topico)
        except Exception as erro:
            # A indisponibilidade da LLM nunca pode derrubar uma habilidade de
            # persistência. A síntese literal é suficiente para concluir.
            self.log(f"⚠️ [CAIXA DE ENTRADA] resumo avançado ignorado: {type(erro).__name__}")
            estrutura = self._resumo_deterministico(trecho, topico)
        agora = self.agora()
        item = {
            "id": uuid.uuid4().hex[:10],
            "tipo": "ideia_discutida",
            "titulo": estrutura["titulo"],
            "conteudo": estrutura["resumo"],
            "resumo": estrutura["resumo"],
            "ideia_original": estrutura["ideia_original"],
            "sugestoes_laylay": list(estrutura.get("sugestoes_laylay") or []),
            "decisoes": list(estrutura.get("decisoes") or []),
            "proximos_passos": list(estrutura.get("proximos_passos") or []),
            "assuntos": _assuntos(f"{estrutura['titulo']} {estrutura['ideia_original']}"),
            "status": "ativo",
            "origem": "conversa_resumida",
            "mensagens_consideradas": len(trecho),
            "criado_em": agora.isoformat(),
            "atualizado_em": agora.isoformat(),
        }
        dados = self._carregar()
        duplicada = next((
            existente for existente in reversed(dados["itens"])
            if existente.get("status") == "ativo"
            and existente.get("tipo") == "ideia_discutida"
            and _normalizar(existente.get("ideia_original")) == _normalizar(estrutura["ideia_original"])
        ), None)
        if duplicada:
            self._ultimo_id = str(duplicada.get("id") or "")
            self._registrar(
                {
                    "intent": "INBOX_ADD_DISCUSSION",
                    "params": {"nota_id": self._ultimo_id, "alvo": str(duplicada.get("titulo") or "")},
                },
                texto,
                True,
                status="discussao_ja_guardada",
            )
            self.falar(
                f"Essa discussão já está guardada como “{duplicada.get('titulo') or 'ideia discutida'}”. Não dupliquei a nota.",
                "debochada",
                1,
            )
            return True
        dados["itens"].append(item)
        ok = self._salvar(dados)
        resultado = {
            "intent": "INBOX_ADD_DISCUSSION",
            "params": {
                "nota_id": item["id"],
                "tipo_nota": item["tipo"],
                "alvo": item["titulo"],
                "sugestoes": len(item["sugestoes_laylay"]),
                "decisoes": len(item["decisoes"]),
                "proximos_passos": len(item["proximos_passos"]),
            },
        }
        self._registrar(
            resultado,
            texto,
            ok,
            status="discussao_guardada" if ok else "falha_execucao",
        )
        if not ok:
            self.falar("Montei o resumo, mas o arquivo não confirmou a gravação.", "calma", 1)
            return True

        self._ultimo_id = item["id"]
        if callable(self.observar_item):
            try:
                self.observar_item(dict(item))
            except Exception as erro:
                self.log(f"⚠️ [CAIXA DE ENTRADA] aprendizado isolado: {type(erro).__name__}")
        detalhes = []
        if item["sugestoes_laylay"]:
            total_sugestoes = len(item["sugestoes_laylay"])
            detalhes.append("1 sugestão" if total_sugestoes == 1 else f"{total_sugestoes} sugestões")
        if item["proximos_passos"]:
            detalhes.append(f"{len(item['proximos_passos'])} próximo" + ("s passos" if len(item["proximos_passos"]) != 1 else " passo"))
        complemento = " com " + " e ".join(detalhes) if detalhes else ""
        fala = (
            f"Guardei nossa discussão como “{item['titulo']}”{complemento}. "
            "Separei sua ideia das minhas sugestões, bonitinho e sem deixar nada fugir pro limbo."
        )
        personalizada = personalizar_informacao_llm(
            fala,
            fatos_obrigatorios=[str(item["titulo"]), *detalhes],
            enviar_mensagem=self.enviar_mensagem,
            emocao="feliz",
            nivel=1,
        )
        self.falar(personalizada.fala, personalizada.emocao, personalizada.nivel)
        return True

    def _filtrar(self, texto: str) -> list[dict[str, Any]]:
        itens = [item for item in self._carregar()["itens"] if item.get("status") == "ativo"]
        t = _normalizar(texto)
        tipo = next((nome for nome in ("ideia", "tarefa", "link", "pensamento", "nota") if nome in t), "")
        if tipo:
            tipos_aceitos = {tipo, "ideia_discutida"} if tipo == "ideia" else {tipo}
            itens = [item for item in itens if str(item.get("tipo")) in tipos_aceitos]
        if "esta semana" in t:
            limite = self.agora() - dt.timedelta(days=7)
            filtrados = []
            for item in itens:
                try:
                    if dt.datetime.fromisoformat(str(item.get("criado_em"))) >= limite:
                        filtrados.append(item)
                except Exception:
                    pass
            itens = filtrados
        return sorted(itens, key=lambda item: str(item.get("criado_em") or ""), reverse=True)

    def _listar(self, texto: str) -> bool:
        itens = self._filtrar(texto)
        resultado = {"intent": "INBOX_LIST", "params": {"filtro": _normalizar(texto)[:120]}}
        self._registrar(resultado, texto, True, status="notas_listadas")
        if not itens:
            self.falar("Sua caixa de entrada não tem nada com esse filtro.", "calma", 1)
            return True
        partes = []
        fatos = []
        for indice, item in enumerate(itens[:5], 1):
            conteudo = re.sub(r"\s+", " ", str(item.get("conteudo") or ""))
            tipo_fala = str(item.get("tipo") or "nota").replace("_", " ")
            fato = f"{indice}: {tipo_fala} — {conteudo[:140]}"
            partes.append(fato)
            fatos.append(fato)
        restante = len(itens) - len(partes)
        fala = "Na sua caixa: " + "; ".join(partes)
        if restante > 0:
            fala += f". E ainda tem mais {restante}."
        self._ultimo_id = str(itens[0].get("id") or self._ultimo_id)
        personalizada = personalizar_informacao_llm(
            fala,
            fatos_obrigatorios=fatos,
            enviar_mensagem=self.enviar_mensagem,
            emocao="calma",
            nivel=1,
        )
        self.falar(personalizada.fala, personalizada.emocao, personalizada.nivel)
        return True

    def _item_referenciado(self, texto: str) -> dict[str, Any]:
        ativos = [item for item in self._carregar()["itens"] if item.get("status") == "ativo"]
        if self._ultimo_id:
            atual = next((item for item in ativos if item.get("id") == self._ultimo_id), None)
            if atual:
                return atual
        t = _normalizar(texto)
        termos = [p for p in _assuntos(t, 5) if p not in {"apaga", "exclui", "remove", "nota", "ideia", "tarefa"}]
        for item in reversed(ativos):
            alvo = _normalizar(item.get("conteudo"))
            if termos and all(termo in alvo for termo in termos):
                return item
        return ativos[-1] if ativos else {}

    def _pedir_confirmacao(self, texto: str, acao: str) -> bool:
        item = self._item_referenciado(texto)
        if not item:
            self.falar("Não encontrei uma nota ativa para fazer isso.", "calma", 1)
            return True
        self._pendencia = {"acao": acao, "item_id": item["id"], "texto": texto}
        intent = "INBOX_DELETE" if acao == "excluir" else "INBOX_CONVERT_REMINDER"
        self._registrar(
            {
                "intent": intent,
                "params": {"nota_id": item["id"], "alvo": str(item.get("conteudo"))[:180]},
            },
            texto,
            False,
            status="aguardando_confirmacao",
        )
        verbo = "enviar essa nota para os itens excluídos" if acao == "excluir" else "transformar essa nota em lembrete"
        self.falar(f"Confirma que quer {verbo}?", "calma", 1)
        return True

    def _confirmar(self, texto: str) -> bool:
        pendencia = dict(self._pendencia)
        self._pendencia = {}
        if not pendencia:
            return False
        dados = self._carregar()
        item = next((i for i in dados["itens"] if i.get("id") == pendencia.get("item_id")), None)
        if not item:
            self.falar("A nota pendente não está mais disponível.", "calma", 1)
            return True
        if pendencia.get("acao") == "excluir":
            item["status"] = "excluido"
            item["atualizado_em"] = self.agora().isoformat()
            ok = self._salvar(dados)
            resultado = {"intent": "INBOX_DELETE", "params": {"nota_id": item["id"], "alvo": str(item.get("conteudo"))[:180]}}
            self._registrar(resultado, texto, ok, status="nota_excluida" if ok else "falha_execucao")
            self.falar("Enviei a nota para os itens excluídos." if ok else "Não consegui confirmar a exclusão.", "calma", 1)
            return True

        resultado_agenda = {
            "intent": "AGENDAR_LEMBRETE",
            "params": {"descricao": str(item.get("conteudo") or "")[:500]},
        }
        ok = bool(self.executar_intencao(resultado_agenda, pendencia.get("texto", ""))) if callable(self.executar_intencao) else False
        self._registrar(resultado_agenda, pendencia.get("texto", ""), ok, status="conversao_iniciada" if ok else "falha_execucao")
        if not ok:
            self.falar("Não consegui encaminhar essa nota para a agenda.", "calma", 1)
        return True

    def processar(self, texto: str) -> bool:
        operacao = self.detectar(texto)
        if not operacao:
            return False
        if operacao == "adicionar_discussao":
            return self._adicionar_discussao(texto)
        if operacao == "adicionar":
            return self._adicionar(texto)
        if operacao == "listar":
            return self._listar(texto)
        if operacao in {"excluir", "converter_lembrete"}:
            return self._pedir_confirmacao(texto, "excluir" if operacao == "excluir" else "converter")
        if operacao == "confirmar":
            return self._confirmar(texto)
        if operacao == "cancelar":
            self._pendencia = {}
            self._registrar(
                {"intent": "CANCEL_INBOX_ACTION", "params": {}},
                texto,
                True,
                status="cancelado",
            )
            self.falar("Certo, não alterei a nota.", "calma", 1)
            return True
        return False

    def reexecutar(self, resultado: dict[str, Any], texto: str) -> bool:
        """Executa novamente apenas consultas consideradas seguras pela mente."""
        intent = str(resultado.get("intent") or "").upper().strip()
        params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
        if intent != "INBOX_LIST":
            return False
        return self._listar(str(params.get("filtro") or texto))

    def retrato_para_mente(self, texto: str = "") -> dict[str, Any]:
        """Expõe somente notas ativas e sanitizadas ao catálogo da mente."""
        itens = self._filtrar(texto)
        return {
            "notas": [
                {
                    "tipo": str(item.get("tipo") or "nota")[:40],
                    "conteudo": re.sub(
                        r"\s+", " ", str(item.get("conteudo") or "")
                    ).strip()[:500],
                }
                for item in itens[:20]
                if str(item.get("conteudo") or "").strip()
            ],
            "total_ativos": len(itens),
            "parametros_consulta": {"filtro": _normalizar(texto)[:120]},
        }

    def snapshot(self) -> dict[str, Any]:
        itens = self._carregar()["itens"]
        ativos = [item for item in itens if item.get("status") == "ativo"]
        return {
            "total": len(itens),
            "ativos": len(ativos),
            "tipos": {
                tipo: sum(1 for item in ativos if item.get("tipo") == tipo)
                for tipo in ("nota", "ideia", "ideia_discutida", "tarefa", "link", "pensamento")
            },
            "ultimo_id": self._ultimo_id,
            "pendencia": bool(self._pendencia),
        }


def criar_caixa_entrada_pessoal_runtime(**kwargs: Any) -> CaixaEntradaPessoalRuntime:
    return CaixaEntradaPessoalRuntime(**kwargs)
