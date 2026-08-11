"""Triagem unificada e persistente das notificacoes da Laylay.

A central nao captura notificacoes do Windows por conta propria. Ela recebe
eventos das integracoes confiaveis (Gmail, agenda e futuros coletores locais),
remove repeticoes e decide se deve avisar agora, resumir ou apenas guardar.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import unicodedata
from collections import Counter
from typing import Any, Callable, Iterable, Mapping


_MODOS = frozenset({"interromper", "resumir", "silenciar"})
_CATEGORIAS = {
    "promocao": ("promocao", "promocoes", "oferta", "ofertas", "marketing", "propaganda"),
    "seguranca": ("seguranca", "login", "senha", "golpe", "acesso"),
    "financeiro": ("financeiro", "banco", "fatura", "boleto", "pagamento", "pix"),
    "compras": ("compras", "pedido", "entrega", "rastreio"),
    "estudo": ("estudo", "curso", "prova", "atividade"),
    "agenda": ("agenda", "lembrete", "compromisso", "reuniao"),
    "sistema": ("sistema", "computador", "windows", "programa"),
    "geral": ("geral", "outros avisos"),
}
_TERMOS_PROMO = (
    "oferta", "desconto", "cupom", "promocao", "imperdivel", "liquidacao",
    "frete gratis", "ultima chance", "mais vendidos", "selecionamos para voce",
)
_TERMOS_URGENTES = (
    "urgente", "vence hoje", "vencimento hoje", "prazo hoje", "bloqueado",
    "tentativa de login", "novo acesso", "senha alterada", "codigo de verificacao",
    "cobranca recusada", "pagamento recusado", "compromisso agora",
)


def _normalizar(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or "").casefold())
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", texto).strip()


def _curto(valor: Any, limite: int = 120) -> str:
    texto = re.sub(r"\s+", " ", str(valor or "").strip())
    return texto if len(texto) <= limite else texto[: limite - 3].rstrip() + "..."


class CentralNotificacoesRuntime:
    """Centraliza prioridade, preferencias, deduplicacao e resumo."""

    def __init__(
        self,
        arquivo_estado: str,
        *,
        falar_cb: Callable[[str, str, int], Any] | None = None,
        agendar_fala_cb: Callable[[str, str, str, int], Any] | None = None,
        agenda_getter: Callable[[], list] | None = None,
        modo_jogo_getter: Callable[[], bool] | None = None,
        conversa_ativa_getter: Callable[[], bool] | None = None,
        is_speaking_getter: Callable[[], bool] | None = None,
        contexto_atualizar_cb: Callable[..., Any] | None = None,
        registrar_aprendizado_cb: Callable[..., Any] | None = None,
        time_cb: Callable[[], float] = time.time,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.arquivo_estado = arquivo_estado
        self.falar_cb = falar_cb
        self.agendar_fala_cb = agendar_fala_cb
        self.agenda_getter = agenda_getter
        self.modo_jogo_getter = modo_jogo_getter
        self.conversa_ativa_getter = conversa_ativa_getter
        self.is_speaking_getter = is_speaking_getter
        self.contexto_atualizar_cb = contexto_atualizar_cb
        self.registrar_aprendizado_cb = registrar_aprendizado_cb
        self.time_cb = time_cb
        self.log = log
        self._lock = threading.RLock()
        self._estado = self._carregar()
        self._publicar_preferencias("persistencia_local")

    @staticmethod
    def _estado_padrao() -> dict[str, Any]:
        return {
            "versao": 1,
            "ativa": True,
            "preferencias": {
                "promocao": "silenciar",
                "seguranca": "interromper",
            },
            "eventos": [],
            "vistos": {},
            "ultima_categoria": "",
        }

    def _carregar(self) -> dict[str, Any]:
        padrao = self._estado_padrao()
        try:
            if os.path.exists(self.arquivo_estado):
                with open(self.arquivo_estado, "r", encoding="utf-8") as arquivo:
                    dados = json.load(arquivo)
                if isinstance(dados, dict):
                    padrao.update(dados)
                    prefs = dados.get("preferencias")
                    if isinstance(prefs, dict):
                        padrao["preferencias"] = {
                            _normalizar(k): str(v)
                            for k, v in prefs.items()
                            if str(v) in _MODOS
                        }
        except Exception as erro:
            self.log(f"⚠️ [NOTIFICAÇÕES] estado ignorado: {type(erro).__name__}")
        return padrao

    def _salvar(self) -> None:
        pasta = os.path.dirname(self.arquivo_estado) or "."
        temporario = f"{self.arquivo_estado}.tmp"
        os.makedirs(pasta, exist_ok=True)
        with open(temporario, "w", encoding="utf-8") as arquivo:
            json.dump(self._estado, arquivo, ensure_ascii=False, indent=2)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, self.arquivo_estado)

    def _publicar_preferencias(
        self,
        proveniencia: str,
        *,
        categoria: str = "",
        modo: str = "",
    ) -> None:
        """Publica somente preferências sanitizadas na mente compartilhada."""
        if not callable(self.contexto_atualizar_cb):
            return
        with self._lock:
            retrato = {
                "ativa": bool(self._estado.get("ativa", True)),
                "valores": dict(self._estado.get("preferencias") or {}),
                "ultima_categoria": categoria or str(
                    self._estado.get("ultima_categoria") or ""
                ),
                "ultimo_modo": modo,
                "proveniencia": str(proveniencia or "runtime"),
                "confianca": 1.0,
                "ts": float(self.time_cb()),
            }
        try:
            self.contexto_atualizar_cb(preferencias_notificacoes=retrato)
        except Exception as erro:
            self.log(
                "⚠️ [NOTIFICAÇÕES] preferências não publicadas no contexto: "
                f"{type(erro).__name__}"
            )

    def _aprender_preferencia(self, categoria: str, modo: str) -> None:
        if not callable(self.registrar_aprendizado_cb):
            return
        descricao = {
            "silenciar": f"prefere guardar avisos de {categoria} em silêncio",
            "interromper": f"aceita interrupções para avisos de {categoria}",
            "resumir": f"prefere receber avisos de {categoria} em resumo",
        }.get(modo, f"prefere o modo {modo} para avisos de {categoria}")
        try:
            self.registrar_aprendizado_cb(
                chave=f"notificacoes:{categoria}",
                tipo="preferencia_notificacao",
                escopo="notificacoes",
                valor={
                    "categoria": categoria,
                    "modo": modo,
                    "descricao_humana": descricao,
                },
                sinal=1.0,
                origem="preferencia_notificacao_explicita",
                evidencia=f"usuário definiu {categoria} como {modo}",
                confirmado_usuario=True,
            )
        except Exception as erro:
            self.log(
                "⚠️ [NOTIFICAÇÕES] preferência não enviada ao aprendizado: "
                f"{type(erro).__name__}"
            )

    def _categoria(self, evento: Mapping[str, Any]) -> str:
        if bool(evento.get("possivel_golpe")):
            return "seguranca"
        categoria = _normalizar(evento.get("categoria") or "")
        texto = _normalizar(
            f"{evento.get('titulo', '')} {evento.get('assunto', '')} "
            f"{evento.get('remetente', '')}"
        )
        if any(termo in texto for termo in _TERMOS_PROMO):
            return "promocao"
        if categoria in _CATEGORIAS:
            return categoria
        return "geral"

    def _prioridade(self, evento: Mapping[str, Any], categoria: str) -> str:
        texto = _normalizar(
            f"{evento.get('titulo', '')} {evento.get('assunto', '')} {evento.get('descricao', '')}"
        )
        if bool(evento.get("possivel_golpe")) or categoria == "seguranca":
            return "critica"
        if str(evento.get("prioridade") or "") in {"critica", "alta"}:
            return str(evento.get("prioridade"))
        if bool(evento.get("prioritario")) or any(x in texto for x in _TERMOS_URGENTES):
            return "alta"
        if categoria == "promocao":
            return "baixa"
        return "normal"

    def _fingerprint(self, evento: Mapping[str, Any], categoria: str) -> str:
        origem = _normalizar(evento.get("origem") or "sistema")
        identificador = _normalizar(evento.get("id") or evento.get("uid") or "")
        if identificador:
            base = f"{origem}|{identificador}"
        else:
            assunto = _normalizar(evento.get("assunto") or evento.get("titulo") or evento.get("descricao"))
            assunto = re.sub(r"\b\d{2,}\b", "#", assunto)
            remetente = _normalizar(evento.get("dominio") or evento.get("remetente") or "")
            base = f"{origem}|{categoria}|{remetente}|{assunto}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]

    def _sanitizar(self, evento: Mapping[str, Any]) -> dict[str, Any]:
        origem = _normalizar(evento.get("origem") or "sistema") or "sistema"
        categoria = self._categoria(evento)
        prioridade = self._prioridade(evento, categoria)
        titulo = _curto(
            evento.get("titulo") or evento.get("assunto") or evento.get("descricao") or "Aviso",
            140,
        )
        remetente = _curto(evento.get("remetente") or evento.get("aplicativo") or "", 60)
        return {
            "id": self._fingerprint(evento, categoria),
            "origem": origem,
            "categoria": categoria,
            "prioridade": prioridade,
            "titulo": titulo,
            "remetente": remetente,
            "ts": float(evento.get("ts") or self.time_cb()),
            "anunciado": False,
            "quantidade": 1,
        }

    def _modo_evento(self, evento: Mapping[str, Any]) -> str:
        categoria = str(evento.get("categoria") or "geral")
        prioridade = str(evento.get("prioridade") or "normal")
        preferencias = self._estado.get("preferencias") or {}
        modo = str(preferencias.get(categoria) or "")
        if modo in _MODOS:
            return modo
        if prioridade == "critica":
            return "interromper"
        if prioridade == "alta":
            return "resumir"
        if categoria == "promocao":
            return "silenciar"
        return "resumir"

    def _contexto_ocupado(self) -> bool:
        getters = (self.modo_jogo_getter, self.conversa_ativa_getter, self.is_speaking_getter)
        for getter in getters:
            try:
                if callable(getter) and getter():
                    return True
            except Exception:
                continue
        return False

    def _texto_evento(self, evento: Mapping[str, Any]) -> str:
        categoria = str(evento.get("categoria") or "geral")
        titulo = str(evento.get("titulo") or "um aviso")
        remetente = str(evento.get("remetente") or "").strip()
        if categoria == "seguranca":
            origem = f" de {remetente}" if remetente else ""
            return f"Atenção: apareceu um aviso de segurança{origem}: {titulo}. Vale conferir antes de abrir links."
        if evento.get("origem") == "agenda":
            return f"Lembrete chegando: {titulo}."
        origem = f" de {remetente}" if remetente else ""
        return f"Chegou um aviso importante{origem}: {titulo}."

    def ingerir(self, eventos: Iterable[Mapping[str, Any]]) -> set[str]:
        """Guarda uma leva e devolve os IDs externos aceitos pela central."""
        aceitos: set[str] = set()
        novos: list[dict[str, Any]] = []
        agora = self.time_cb()
        with self._lock:
            vistos = self._estado.setdefault("vistos", {})
            armazenados = self._estado.setdefault("eventos", [])
            for bruto in eventos or ():
                if not isinstance(bruto, Mapping):
                    continue
                externo = str(bruto.get("uid") or bruto.get("id") or "").strip()
                evento = self._sanitizar(bruto)
                chave = evento["id"]
                anterior = float(vistos.get(chave) or 0.0)
                if anterior and agora - anterior < 7 * 86400:
                    if externo:
                        aceitos.add(externo)
                    continue
                vistos[chave] = agora
                armazenados.append(evento)
                novos.append(evento)
                if externo:
                    aceitos.add(externo)
            self._estado["eventos"] = armazenados[-120:]
            self._estado["vistos"] = {
                k: v for k, v in list(vistos.items())[-400:]
                if agora - float(v or 0.0) < 30 * 86400
            }
            if novos:
                self._estado["ultima_categoria"] = novos[-1]["categoria"]
                self._salvar()

        if not novos or not bool(self._estado.get("ativa", True)):
            return aceitos

        candidatos = [e for e in novos if self._modo_evento(e) != "silenciar"]
        criticos = [e for e in candidatos if self._modo_evento(e) == "interromper"]
        escolhidos = criticos[:1] if criticos else ([] if self._contexto_ocupado() else candidatos[:1])
        if escolhidos and callable(self.agendar_fala_cb):
            evento = escolhidos[0]
            texto = self._texto_evento(evento)
            try:
                agendou = bool(self.agendar_fala_cb(
                    "seguranca" if evento["categoria"] == "seguranca" else "notificacoes",
                    texto,
                    "irritada" if evento["categoria"] == "seguranca" else "calma",
                    2 if evento["prioridade"] == "critica" else 1,
                ))
            except Exception as erro:
                self.log(f"⚠️ [NOTIFICAÇÕES] fala não entrou na fila: {type(erro).__name__}")
                agendou = False
            if agendou:
                with self._lock:
                    evento["anunciado"] = True
                    self._salvar()
        return aceitos

    def ingerir_emails(self, emails: Iterable[Mapping[str, Any]]) -> set[str]:
        preparados = []
        for email in emails or ():
            if not isinstance(email, Mapping) or email.get("silenciado"):
                continue
            preparados.append({**dict(email), "origem": "email"})
        return self.ingerir(preparados)

    def ingerir_agendamento(self, agendamento: Mapping[str, Any], descricao: str = "") -> bool:
        identificador = str(agendamento.get("id") or agendamento.get("nome") or descricao)
        aceitos = self.ingerir([{
            "id": f"agenda:{identificador}:{int(self.time_cb() // 60)}",
            "origem": "agenda",
            "categoria": "agenda",
            "prioridade": "alta",
            "titulo": descricao or agendamento.get("descricao") or agendamento.get("nome") or "Lembrete",
        }])
        return bool(aceitos)

    def ingerir_alerta_sistema(
        self, titulo: str, *, aplicativo: str = "", prioridade: str = "normal",
    ) -> bool:
        identificador = f"{aplicativo}:{titulo}:{int(self.time_cb() // 60)}"
        return bool(self.ingerir([{
            "id": identificador,
            "origem": "sistema",
            "categoria": "sistema",
            "prioridade": prioridade,
            "titulo": titulo,
            "aplicativo": aplicativo,
        }]))

    def _agenda_ativa(self) -> list[dict[str, Any]]:
        try:
            itens = self.agenda_getter() if callable(self.agenda_getter) else []
        except Exception:
            return []
        return [dict(item) for item in (itens or []) if isinstance(item, Mapping) and item.get("ativo", True)]

    def resumo(self, *, somente_importantes: bool = False) -> str:
        with self._lock:
            eventos = [dict(e) for e in self._estado.get("eventos", []) if isinstance(e, dict)]
        if somente_importantes:
            eventos = [e for e in eventos if e.get("prioridade") in {"alta", "critica"}]
        eventos = eventos[-12:]
        agenda = self._agenda_ativa()
        if not eventos and not agenda:
            return "Sua central está quietinha: nenhum aviso guardado e nada ativo na agenda."

        partes: list[str] = []
        if eventos:
            contagem = Counter(str(e.get("categoria") or "geral") for e in eventos)
            importantes = [e for e in eventos if e.get("prioridade") in {"alta", "critica"}]
            partes.append(
                f"Tenho {len(eventos)} aviso{'s' if len(eventos) != 1 else ''} guardado{'s' if len(eventos) != 1 else ''}"
                + (f", {len(importantes)} pedindo mais atenção" if importantes else "")
                + "."
            )
            destaques = importantes[-3:] or eventos[-3:]
            partes.append("Destaques: " + "; ".join(
                f"{e.get('remetente') + ': ' if e.get('remetente') else ''}{e.get('titulo')}"
                for e in reversed(destaques)
            ) + ".")
            silenciosas = contagem.get("promocao", 0)
            if silenciosas:
                partes.append(f"Agrupei {silenciosas} promoção{'ões' if silenciosas != 1 else ''} sem ficar tagarelando.")
        if agenda:
            nomes = [_curto(x.get("nome") or x.get("descricao") or "compromisso", 55) for x in agenda[:3]]
            partes.append(
                f"Na agenda, há {len(agenda)} item{'s' if len(agenda) != 1 else ''} ativo{'s' if len(agenda) != 1 else ''}: "
                + ", ".join(nomes) + "."
            )
        return " ".join(partes)

    def definir_preferencia(self, categoria: str, modo: str) -> tuple[bool, str]:
        categoria = _normalizar(categoria)
        modo = _normalizar(modo)
        if categoria not in _CATEGORIAS or modo not in _MODOS:
            return False, "Não identifiquei qual categoria de aviso você quis ajustar."
        with self._lock:
            self._estado.setdefault("preferencias", {})[categoria] = modo
            self._estado["ultima_categoria"] = categoria
            self._salvar()
        self._publicar_preferencias(
            "preferencia_explicita_usuario",
            categoria=categoria,
            modo=modo,
        )
        self._aprender_preferencia(categoria, modo)
        if modo == "silenciar":
            return True, f"Fechado. Vou guardar avisos de {categoria} em silêncio."
        if modo == "interromper":
            return True, f"Entendi. Avisos de {categoria} podem chamar sua atenção na hora."
        return True, f"Certo. Vou juntar avisos de {categoria} no resumo, sem interromper à toa."

    def executar(self, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        params = dict(params or {})
        acao = _normalizar(params.get("acao") or "ler")
        categoria = _normalizar(params.get("categoria") or params.get("alvo") or "")
        if acao in {"ler", "resumir", "listar", "importantes"}:
            return {"ok": True, "status": "notificacoes_lidas", "fala": self.resumo(
                somente_importantes=acao == "importantes",
            )}
        if acao in {"silenciar", "desativar", "mute"} and not categoria:
            with self._lock:
                self._estado["ativa"] = False
                self._salvar()
            self._publicar_preferencias("preferencia_explicita_usuario", modo="silenciar")
            return {"ok": True, "status": "notificacoes_silenciadas", "fala": "Tudo bem. A central fica em silêncio e continua guardando os avisos para quando você pedir."}
        if acao in {"ativar", "reativar"} and not categoria:
            with self._lock:
                self._estado["ativa"] = True
                self._salvar()
            self._publicar_preferencias("preferencia_explicita_usuario", modo="ativar")
            return {"ok": True, "status": "notificacoes_ativadas", "fala": "Central acordada de novo. Vou avisar com critério, sem virar uma sirene com ansiedade."}
        modo = "silenciar" if acao in {"silenciar", "dispensar", "ignorar"} else "interromper" if acao in {"interromper", "priorizar", "importante"} else "resumir"
        ok, fala = self.definir_preferencia(categoria, modo)
        return {"ok": ok, "status": "preferencia_notificacao_atualizada" if ok else "categoria_ausente", "fala": fala}

    def _extrair_categoria(self, texto: str) -> str:
        t = _normalizar(texto)
        for categoria, termos in _CATEGORIAS.items():
            if any(re.search(rf"\b{re.escape(termo)}\b", t) for termo in termos):
                return categoria
        if re.search(r"\b(?:esse|essa|desse|dessa)\s+tipo\b", t):
            return str(self._estado.get("ultima_categoria") or "")
        return ""

    def detectar(self, texto: str) -> dict[str, Any] | None:
        t = _normalizar(texto)
        if not t:
            return None
        assunto = bool(re.search(r"\b(?:notificacoes?|avisos?|alertas?)\b", t))
        consulta_ampla = bool(re.search(
            r"\b(?:tem|ha|quais|mostra|resume|resuma|me fala|me diga)\b.*"
            r"\b(?:importante|precisa (?:da )?minha atencao|pendente)\b",
            t,
        ))
        categoria = self._extrair_categoria(t)
        if re.search(r"\b(?:nao me avis[ae]|nao quero aviso|silencia|silenciar|dispensa|ignora)\b", t) and (assunto or categoria):
            return {"intent": "NOTIFICATIONS", "params": {"acao": "silenciar", "categoria": categoria}}
        if re.search(r"\b(?:me avis[ae] na hora|podem? me interromper|me interrompa|e importante)\b", t) and (assunto or categoria):
            return {"intent": "NOTIFICATIONS", "params": {"acao": "interromper", "categoria": categoria}}
        if re.search(r"\b(?:junta|agrupa|coloca)\b.*\b(?:resumo|avisos?|notificacoes?)\b", t) and categoria:
            return {"intent": "NOTIFICATIONS", "params": {"acao": "resumir_categoria", "categoria": categoria}}
        if assunto and re.search(r"\b(?:ativa|reativa|volta)\b", t):
            return {"intent": "NOTIFICATIONS", "params": {"acao": "ativar"}}
        if assunto and re.search(r"\b(?:silencia tudo|desativa|fica em silencio)\b", t):
            return {"intent": "NOTIFICATIONS", "params": {"acao": "silenciar"}}
        if assunto or consulta_ampla:
            importantes = bool(re.search(r"\b(?:importantes?|urgentes?|prioritarios?)\b", t))
            return {"intent": "NOTIFICATIONS", "params": {"acao": "importantes" if importantes else "ler"}}
        return None

    def processar(self, texto: str) -> bool:
        comando = self.detectar(texto)
        if not comando:
            return False
        resultado = self.executar(comando.get("params"))
        if callable(self.falar_cb):
            self.falar_cb(str(resultado.get("fala") or ""), "calma", 1)
        return True

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            eventos = list(self._estado.get("eventos") or [])
            pasta = os.path.dirname(self.arquivo_estado) or "."
            return {
                "ativa": bool(self._estado.get("ativa", True)),
                "eventos": len(eventos),
                "importantes": sum(e.get("prioridade") in {"alta", "critica"} for e in eventos if isinstance(e, dict)),
                "preferencias": dict(self._estado.get("preferencias") or {}),
                "persistencia_disponivel": bool(
                    os.path.exists(self.arquivo_estado)
                    or (os.path.isdir(pasta) and os.access(pasta, os.W_OK))
                ),
                "conteudo_exposto": False,
                "autoriza_execucao": False,
            }


def criar_central_notificacoes_runtime(*args: Any, **kwargs: Any) -> CentralNotificacoesRuntime:
    return CentralNotificacoesRuntime(*args, **kwargs)
