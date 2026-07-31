"""Entrada única e contextual para oportunidades da mente da Laylay.

O coordenador não concede autoridade e não executa ações. Ele qualifica os
eventos dos sensores antes de entregá-los ao MotorIniciativaRuntime, que
continua sendo a única fonte de decisão, governança e execução autônoma.
"""

from __future__ import annotations

import re
import threading
import time
import unicodedata
from typing import Any, Callable, Mapping


def _codigo(valor: Any, limite: int = 72) -> str:
    base = unicodedata.normalize("NFKD", str(valor or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"https?://\S+|[a-z]:\\\S+|[/\\][^\s]+", "", base)
    base = re.sub(r"[^a-z0-9_.: -]+", "", base)
    return re.sub(r"\s+", "_", base).strip("_.:-")[:limite]


def _numero(valor: Any, padrao: float, minimo: float, maximo: float) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = padrao
    return max(minimo, min(maximo, numero))


def estado_coordenador_inicial() -> dict[str, Any]:
    return {
        "versao": 1,
        "recentes": [],
        "objetivos": [],
        "aprendizado": {},
        "contadores": {
            "recebidas": 0,
            "encaminhadas": 0,
            "duplicadas_semanticas": 0,
            "baixa_confianca": 0,
            "expiradas": 0,
            "alinhadas_objetivo": 0,
            "feedbacks": 0,
            "aceitas": 0,
            "recusadas": 0,
            "silencios": 0,
            "correcoes": 0,
        },
        "ultima": {},
    }


class CoordenadorOportunidadesRuntime:
    """Normaliza, contextualiza e agrupa oportunidades antes da decisão."""

    def __init__(
        self,
        *,
        encaminhar: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        estado_get: Callable[[], Mapping[str, Any]] = lambda: {},
        estado_set: Callable[[dict[str, Any]], Any] = lambda _estado: None,
        contexto_getter: Callable[[], Mapping[str, Any]] = lambda: {},
        objetivos_getter: Callable[[], Any] | None = None,
        clock: Callable[[], float] = time.time,
        janela_semantica_s: float = 300.0,
        confianca_minima: float = 0.45,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.encaminhar = encaminhar
        self.estado_get = estado_get
        self.estado_set = estado_set
        self.contexto_getter = contexto_getter
        self.objetivos_getter = objetivos_getter
        self.clock = clock
        self.janela_semantica_s = max(15.0, float(janela_semantica_s))
        self.confianca_minima = max(0.0, min(1.0, float(confianca_minima)))
        self.log = log
        self._lock = threading.RLock()

    def _estado(self) -> dict[str, Any]:
        try:
            recebido = dict(self.estado_get() or {})
        except Exception:
            recebido = {}
        base = estado_coordenador_inicial()
        base.update(recebido)
        base["contadores"] = {
            **estado_coordenador_inicial()["contadores"],
            **dict(base.get("contadores") or {}),
        }
        base["recentes"] = [
            dict(item) for item in list(base.get("recentes") or [])[-40:]
            if isinstance(item, Mapping)
        ]
        base["objetivos"] = [
            dict(item) for item in list(base.get("objetivos") or [])[-12:]
            if isinstance(item, Mapping)
        ]
        base["aprendizado"] = {
            _codigo(chave, 120): dict(valor)
            for chave, valor in list(dict(base.get("aprendizado") or {}).items())[-40:]
            if _codigo(chave, 120) and isinstance(valor, Mapping)
        }
        return base

    def _contexto(self) -> dict[str, Any]:
        try:
            valor = self.contexto_getter() or {}
            return dict(valor) if isinstance(valor, Mapping) else {}
        except Exception:
            return {}

    @staticmethod
    def _tags(valor: Any) -> set[str]:
        if isinstance(valor, str):
            itens = re.split(r"[,;/|]", valor)
        elif isinstance(valor, (list, tuple, set, frozenset)):
            itens = list(valor)
        else:
            itens = []
        return {_codigo(item, 48) for item in itens if _codigo(item, 48)}

    def _objetivos_ativos(self, estado: Mapping[str, Any], agora: float) -> list[dict[str, Any]]:
        objetivos = list(estado.get("objetivos") or [])
        if callable(self.objetivos_getter):
            try:
                externos = self.objetivos_getter() or []
                if isinstance(externos, Mapping):
                    externos = [externos]
                objetivos.extend(item for item in externos if isinstance(item, Mapping))
            except Exception:
                pass
        ativos = []
        for bruto in objetivos:
            item = dict(bruto or {})
            expira = _numero(item.get("expira_em"), agora + 1.0, 0.0, agora + 365 * 86400.0)
            if expira <= agora:
                continue
            tags = self._tags(item.get("tags"))
            nome = _codigo(item.get("nome") or item.get("objetivo"), 72)
            if nome:
                tags.add(nome)
            if tags:
                ativos.append({
                    "nome": nome or "objetivo",
                    "tags": sorted(tags),
                    "prioridade": int(_numero(item.get("prioridade"), 5, 1, 10)),
                    "expira_em": expira,
                })
        return ativos[-12:]

    @staticmethod
    def _assinatura_semantica(dados: Mapping[str, Any]) -> str:
        acao = dados.get("acao_proposta")
        if isinstance(acao, Mapping):
            intent = _codigo(acao.get("intent"), 48)
            params = dict(acao.get("params") or {}) if isinstance(acao.get("params"), Mapping) else {}
        else:
            intent = _codigo(acao, 48)
            params = {}
        alvo = next((
            _codigo(params.get(chave), 64)
            for chave in ("alvo", "slot", "item", "nome_app", "nome_playlist", "acao")
            if _codigo(params.get(chave), 64)
        ), "")
        if not alvo:
            alvo = next((
                _codigo(dados.get(chave), 64)
                for chave in ("alvo", "slot", "item", "entidade", "assunto")
                if _codigo(dados.get(chave), 64)
            ), "")
        partes = (
            _codigo(dados.get("dominio"), 32),
            _codigo(dados.get("tipo"), 40),
            intent,
            alvo,
            _codigo(dados.get("objetivo"), 48),
        )
        return ":".join(parte for parte in partes if parte) or _codigo(dados.get("chave")) or "oportunidade"

    @staticmethod
    def _perfil_contextual(dados: Mapping[str, Any], contexto: Mapping[str, Any]) -> str:
        dominio = _codigo(dados.get("dominio"), 32) or "geral"
        tipo = _codigo(dados.get("tipo"), 40) or "observacao"
        ambiente = "jogo" if bool(
            contexto.get("modo_jogo") or contexto.get("modo_jogo_ativo")
        ) else "cotidiano"
        foco = "foco" if bool(
            contexto.get("modo_foco") or contexto.get("foco_ativo")
        ) else "livre"
        return f"{dominio}:{tipo}:{ambiente}:{foco}"

    @staticmethod
    def _recalcular_aprendizado(registro: Mapping[str, Any]) -> dict[str, Any]:
        dados = dict(registro or {})
        aceitas = max(0, int(dados.get("aceitas") or 0))
        recusadas = max(0, int(dados.get("recusadas") or 0))
        silencios = max(0, int(dados.get("silencios") or 0))
        correcoes = max(0, int(dados.get("correcoes") or 0))
        amostras = aceitas + recusadas + silencios + correcoes
        grupos = [aceitas, recusadas, silencios, correcoes]
        dominancia = max(grupos, default=0) / amostras if amostras else 0.0
        sinal = (
            aceitas - recusadas - 1.25 * correcoes - 0.35 * silencios
        ) / amostras if amostras else 0.0
        ajuste = 0
        status = "observando"
        if amostras >= 3 and dominancia >= 0.67 and abs(sinal) >= 0.30:
            maturidade = min(1.0, amostras / 6.0)
            escala = 12 if sinal > 0 else 16
            ajuste = round(sinal * escala * maturidade)
            ajuste = max(-18, min(12, ajuste))
            status = "preferencia_emergente"
        elif amostras >= 3 and dominancia < 0.67:
            status = "sinais_conflitantes"
        dados.update(
            amostras=amostras,
            dominancia=round(dominancia, 3),
            sinal=round(sinal, 3),
            ajuste_utilidade=ajuste,
            status=status,
        )
        return dados

    def registrar_feedback(
        self,
        tipo: str = "",
        aceito: bool | None = None,
        *,
        resultado: str = "",
        comando: str = "",
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Aprende com a última oportunidade, exigindo evidência repetida."""
        agora = float(self.clock())
        resultado_norm = _codigo(resultado, 32)
        if resultado_norm not in {"aceita", "recusa", "silencio", "correcao"}:
            resultado_norm = "aceita" if aceito is True else "recusa" if aceito is False else ""
        if not resultado_norm:
            return {}
        with self._lock:
            estado = self._estado()
            ultima = dict(estado.get("ultima") or {})
            if not ultima or agora - float(ultima.get("ts") or 0.0) > 600.0:
                return {}
            if ultima.get("feedback_registrado"):
                return {}
            categoria = _codigo(tipo, 40)
            origem_feedback = " ".join((
                _codigo(ultima.get("dominio"), 32),
                _codigo(ultima.get("tipo"), 40),
            ))
            aliases = {
                "musica": ("musica", "playlist", "media"),
                "emails": ("email", "emails"),
                "contexto_janela": ("contexto_janela", "navegador", "janelas"),
                "horario": ("ritmo_temporal", "conforto", "iot", "agenda"),
                "rotina": ("rotina", "janelas", "iot", "conforto"),
                "jogo": ("jogo", "observacao"),
                "observacao": ("observacao", "jogo"),
            }
            termos = aliases.get(categoria, (categoria,) if categoria else ())
            if termos and not any(termo in origem_feedback for termo in termos):
                return {}
            perfil = _codigo(ultima.get("perfil_contextual"), 120)
            if not perfil:
                return {}
            aprendizado = dict(estado.get("aprendizado") or {})
            registro = dict(aprendizado.get(perfil) or {})
            campo = {
                "aceita": "aceitas", "recusa": "recusadas",
                "silencio": "silencios", "correcao": "correcoes",
            }[resultado_norm]
            registro[campo] = int(registro.get(campo) or 0) + 1
            registro.update(
                perfil=perfil,
                ultima_resposta=resultado_norm,
                ultima_resposta_ts=agora,
                tipo=_codigo(tipo or ultima.get("tipo"), 40),
                comando=_codigo(comando, 48),
            )
            registro = self._recalcular_aprendizado(registro)
            aprendizado[perfil] = registro
            contadores = dict(estado.get("contadores") or {})
            contadores["feedbacks"] = int(contadores.get("feedbacks") or 0) + 1
            contadores[campo] = int(contadores.get(campo) or 0) + 1
            estado.update(
                aprendizado=dict(list(aprendizado.items())[-40:]),
                contadores=contadores,
                ultima={
                    **ultima,
                    "feedback_registrado": True,
                    "feedback_resultado": resultado_norm,
                },
            )
            self.estado_set(estado)
        if registro.get("ajuste_utilidade"):
            self.log(
                f"🧭 [OPORTUNIDADE:APRENDIZADO] perfil={perfil} "
                f"amostras={registro['amostras']} ajuste={registro['ajuste_utilidade']:+d}"
            )
        return dict(registro)

    def definir_objetivo(
        self, nome: str, *, tags: Any = (), prioridade: int = 5, validade_s: float = 3600.0,
    ) -> bool:
        nome_seguro = _codigo(nome, 72)
        if not nome_seguro:
            return False
        agora = float(self.clock())
        with self._lock:
            estado = self._estado()
            objetivos = [
                dict(item) for item in list(estado.get("objetivos") or [])
                if _codigo(dict(item).get("nome"), 72) != nome_seguro
            ]
            objetivos.append({
                "nome": nome_seguro,
                "tags": sorted(self._tags(tags) | {nome_seguro}),
                "prioridade": int(_numero(prioridade, 5, 1, 10)),
                "expira_em": agora + max(60.0, float(validade_s)),
            })
            estado["objetivos"] = objetivos[-12:]
            self.estado_set(estado)
        return True

    def registrar(self, oportunidade: Mapping[str, Any] | None) -> dict[str, Any]:
        dados = dict(oportunidade or {})
        agora = float(self.clock())
        with self._lock:
            estado = self._estado()
            contadores = dict(estado.get("contadores") or {})
            contadores["recebidas"] = int(contadores.get("recebidas") or 0) + 1
            validade_s = _numero(dados.get("validade_s"), 180.0, 0.0, 86400.0)
            if validade_s <= 0.0:
                contadores["expiradas"] = int(contadores.get("expiradas") or 0) + 1
                resultado = {"decisao": "ignorar_expirada", "motivos": ["oportunidade_expirada"]}
                estado.update(contadores=contadores, ultima=resultado)
                self.estado_set(estado)
                return resultado

            confianca = _numero(dados.get("confianca"), 1.0, 0.0, 1.0)
            pedido_indireto_confiavel = (
                _codigo(dados.get("origem"), 48) == "fala_indireta_confiavel"
                and confianca >= 0.90
            )
            urgente = _codigo(dados.get("tipo"), 32) in {"alarme", "seguranca", "erro_critico"}
            if confianca < self.confianca_minima and not urgente:
                contadores["baixa_confianca"] = int(contadores.get("baixa_confianca") or 0) + 1
                resultado = {
                    "decisao": "ignorar_baixa_confianca",
                    "confianca": confianca,
                    "motivos": ["confianca_insuficiente"],
                }
                estado.update(contadores=contadores, ultima=resultado)
                self.estado_set(estado)
                return resultado

            assinatura = self._assinatura_semantica(dados)
            recentes = [
                dict(item) for item in list(estado.get("recentes") or [])
                if agora - float(dict(item).get("ts") or 0.0) <= self.janela_semantica_s
            ]
            if (
                not pedido_indireto_confiavel
                and any(item.get("assinatura") == assinatura for item in recentes)
            ):
                contadores["duplicadas_semanticas"] = int(contadores.get("duplicadas_semanticas") or 0) + 1
                resultado = {
                    "decisao": "ignorar_duplicada_semantica",
                    "duplicada": True,
                    "assinatura_semantica": assinatura,
                    "motivos": ["oportunidade_equivalente_recente"],
                }
                estado.update(recentes=recentes[-40:], contadores=contadores, ultima=resultado)
                self.estado_set(estado)
                return resultado

            tags = self._tags(dados.get("tags") or dados.get("objetivos_relacionados"))
            tags.update(filter(None, (
                _codigo(dados.get("dominio"), 32),
                _codigo(dados.get("tipo"), 40),
            )))
            objetivos_locais = list(estado.get("objetivos") or [])
            objetivos = self._objetivos_ativos(estado, agora)
            alinhados = [obj for obj in objetivos if tags & set(obj.get("tags") or [])]
            utilidade_base = int(_numero(dados.get("utilidade"), 40, 0, 100))
            utilidade = round(utilidade_base * (0.55 + 0.45 * confianca))
            if alinhados:
                utilidade += min(12, max(int(obj.get("prioridade") or 1) for obj in alinhados) + 2)
                contadores["alinhadas_objetivo"] = int(contadores.get("alinhadas_objetivo") or 0) + 1
            utilidade = max(0, min(100, utilidade))
            contexto = self._contexto()
            perfil_contextual = self._perfil_contextual(dados, contexto)
            aprendizado = dict(estado.get("aprendizado") or {})
            perfil_aprendido = dict(aprendizado.get(perfil_contextual) or {})
            ajuste_aprendido = int(perfil_aprendido.get("ajuste_utilidade") or 0)
            utilidade = max(0, min(100, utilidade + ajuste_aprendido))
            dados_qualificados = {
                **dados,
                "chave": _codigo(dados.get("chave"), 72) or assinatura,
                "utilidade": utilidade,
                "confianca": confianca,
                "validade_s": validade_s,
                "tags_contextuais": sorted(tags)[:10],
                "objetivos_ativos": [obj["nome"] for obj in alinhados[:3]],
                "ajuste_aprendido": ajuste_aprendido,
                "contexto_oportunidade": {
                    "jogo": bool(contexto.get("modo_jogo") or contexto.get("modo_jogo_ativo")),
                    "conversa": bool(contexto.get("modo_chat") or contexto.get("conversa_ativa")),
                    "foco": bool(contexto.get("modo_foco") or contexto.get("foco_ativo")),
                },
            }
            resultado = dict(self.encaminhar(dados_qualificados) or {})
            contadores["encaminhadas"] = int(contadores.get("encaminhadas") or 0) + 1
            recentes.append({
                "assinatura": assinatura,
                "dominio": _codigo(dados.get("dominio"), 32),
                "tipo": _codigo(dados.get("tipo"), 40),
                "ts": agora,
                "validade_ate": agora + validade_s,
            })
            ultima = {
                "assinatura": assinatura,
                "dominio": _codigo(dados.get("dominio"), 32),
                "tipo": _codigo(dados.get("tipo"), 40),
                "confianca": round(confianca, 3),
                "utilidade": utilidade,
                "objetivos": [obj["nome"] for obj in alinhados[:3]],
                "perfil_contextual": perfil_contextual,
                "ajuste_aprendido": ajuste_aprendido,
                "decisao": _codigo(resultado.get("decisao"), 48),
                "ts": agora,
            }
            estado.update(
                recentes=recentes[-40:], objetivos=objetivos_locais[-12:],
                contadores=contadores, ultima=ultima,
            )
            self.estado_set(estado)
        if alinhados:
            self.log(
                f"🧭 [OPORTUNIDADE] alinhada={','.join(obj['nome'] for obj in alinhados[:3])} "
                f"utilidade={utilidade} domínio={dados.get('dominio') or dados.get('tipo')}"
            )
        return resultado

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._estado()


def criar_coordenador_oportunidades_runtime(**kwargs: Any) -> CoordenadorOportunidadesRuntime:
    return CoordenadorOportunidadesRuntime(**kwargs)
