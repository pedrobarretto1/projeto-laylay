"""Avaliação central de oportunidades autônomas da mente única.

O motor não executa integrações. Ele decide o que seria apropriado fazer e
registra uma trilha curta. No modo sombra, usado por padrão, nenhuma decisão
dele muda o comportamento externo da Laylay.
"""

from __future__ import annotations

import re
import threading
import time
from typing import Any, Callable, Mapping

from .governanca_iniciativa import (
    DOMINIOS_PERFIL_SEGURO,
    PERMISSOES_INICIATIVA,
    normalizar_dominio_iniciativa,
)


MODOS_INICIATIVA = frozenset({"desligado", "sombra", "sugestao", "autorizado"})
RISCOS = frozenset({"baixo", "medio", "alto"})
TIPOS_URGENTES = frozenset({"alarme", "seguranca", "erro_critico"})
FALHAS_ATE_ABRIR_CIRCUITO = 3
CIRCUITO_ABERTO_S = 900.0
CONFIANCA_MINIMA_EXECUCAO = 0.90
JANELA_ORCAMENTO_S = 600.0
MAX_SUGESTOES_JANELA = 3
MAX_EXECUCOES_JANELA = 3

# Nunca são ações autônomas. Podem, no máximo, virar uma sugestão que exija
# uma ordem explícita posterior do usuário pelo fluxo operacional normal.
INTENTS_COM_CONFIRMACAO_HUMANA = frozenset({
    "DELETE_ITEM", "CONFIRM_DELETE_ITEM", "RESTORE_DELETED_ITEM",
    "LOCK_PC", "CLOSE_APP", "FECHAR_PROGRAMA", "CLOSE_TAB",
    "CLOSE_IDLE_TABS", "PLAYLIST_DELETE", "CANCELAR_AGENDAMENTO",
    "FILE_TRANSACTION", "CREATE_FILE", "CREATE_FOLDER",
    "SEND_EMAIL", "SEND_MESSAGE", "PURCHASE", "PAYMENT",
})

_ALIASES_CAPACIDADE = {
    "TIME_LIGHT_ON": "IOT_CONTROL",
    "VOLUME_RELATIVE": "VOLUME",
}

_UTILIDADE_PADRAO = {
    "alarme": 100,
    "seguranca": 95,
    "erro_critico": 90,
    "lembrete": 84,
    "ritmo_temporal": 58,
    "rotina": 52,
    "contexto_janela": 44,
    "observacao": 38,
}
_PENALIDADE_RISCO = {"baixo": 0, "medio": 24, "alto": 60}


def _codigo(valor: Any, limite: int = 80) -> str:
    texto = str(valor or "").strip().casefold()
    texto = re.sub(r"https?://\S+|[a-z]:\\\S+|[/\\][^\s]+", "", texto)
    texto = re.sub(r"[^a-z0-9áàâãéêíóôõúç_.: -]+", "", texto)
    return re.sub(r"\s+", "_", texto).strip("_.:-")[:limite]


def _numero(valor: Any, padrao: float, minimo: float, maximo: float) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = float(padrao)
    return max(float(minimo), min(float(maximo), numero))


def estado_iniciativa_inicial(modo: str = "sombra") -> dict[str, Any]:
    modo_norm = str(modo or "sombra").strip().casefold()
    if modo_norm not in MODOS_INICIATIVA:
        modo_norm = "sombra"
    return {
        "versao": 2,
        "modo": modo_norm,
        "niveis": {},
        "permissoes": {},
        "historico": [],
        "contadores": {
            "avaliadas": 0,
            "ignoradas": 0,
            "aguardariam": 0,
            "sugeririam": 0,
            "executariam": 0,
            "duplicadas": 0,
        },
        "ultima_decisao": {},
        "execucao": {
            "falhas_consecutivas": {},
            "circuitos_ate": {},
            "ultimo_desfazer": {},
            "ultima_execucao": {},
        },
        "seguranca": {
            "modo": "vontade_segura",
            "autoriza_execucao": False,
            "eventos_orcamento": [],
            "bloqueios_capacidade": 0,
            "bloqueios_confirmacao": 0,
            "bloqueios_orcamento": 0,
            "simulacoes_orcamento": 0,
        },
        "auditoria": {
            "status": "sem_amostras",
            "autoriza_execucao": False,
            "amostras": 0,
            "taxa_duplicacao": 0.0,
            "dominios": {},
        },
    }


class MotorIniciativaRuntime:
    """Pontua oportunidades e aprende em segurança antes de ganhar autoridade."""

    def __init__(
        self,
        *,
        estado_get: Callable[[], Mapping[str, Any]],
        estado_set: Callable[[dict[str, Any]], Any],
        contexto_getter: Callable[[], Mapping[str, Any]],
        modo: str = "sombra",
        registrar_decisao_cb: Callable[..., Any] | None = None,
        capacidade_getter: Callable[[str], Mapping[str, Any]] | None = None,
        executor_acao_cb: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        desfazer_acao_cb: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        clock: Callable[[], float] = time.time,
        limite_historico: int = 30,
        janela_repeticao_s: float = 600.0,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.estado_get = estado_get
        self.estado_set = estado_set
        self.contexto_getter = contexto_getter
        self.modo_padrao = modo if modo in MODOS_INICIATIVA else "sombra"
        self.registrar_decisao_cb = registrar_decisao_cb
        self.capacidade_getter = capacidade_getter
        self.executor_acao_cb = executor_acao_cb
        self.desfazer_acao_cb = desfazer_acao_cb
        self.clock = clock
        self.limite_historico = max(5, min(100, int(limite_historico)))
        self.janela_repeticao_s = max(30.0, float(janela_repeticao_s))
        self.log = log
        self._lock = threading.RLock()

    def _estado(self) -> dict[str, Any]:
        try:
            recebido = dict(self.estado_get() or {})
        except Exception:
            recebido = {}
        base = estado_iniciativa_inicial(self.modo_padrao)
        base.update(recebido)
        modo = str(base.get("modo") or self.modo_padrao).casefold()
        base["modo"] = modo if modo in MODOS_INICIATIVA else self.modo_padrao
        base["historico"] = [
            dict(item) for item in list(base.get("historico") or [])
            if isinstance(item, Mapping)
        ][-self.limite_historico:]
        base["contadores"] = {
            **estado_iniciativa_inicial()["contadores"],
            **dict(base.get("contadores") or {}),
        }
        base["execucao"] = {
            **estado_iniciativa_inicial()["execucao"],
            **dict(base.get("execucao") or {}),
        }
        base["seguranca"] = {
            **estado_iniciativa_inicial()["seguranca"],
            **dict(base.get("seguranca") or {}),
        }
        return base

    @staticmethod
    def _intent_capacidade(proposta: Any) -> str:
        if isinstance(proposta, Mapping):
            intent = str(proposta.get("intent") or "").strip().upper()
            params = dict(proposta.get("params") or {}) if isinstance(proposta.get("params"), Mapping) else {}
        else:
            intent = str(proposta or "").strip().upper()
            params = {}
        if intent == "EXECUTE_INTENT":
            interna = params.get("intent") if isinstance(params.get("intent"), Mapping) else {}
            intent = str(interna.get("intent") or "").strip().upper()
        return _ALIASES_CAPACIDADE.get(intent, intent)

    def _capacidade_disponivel(self, intent: str) -> tuple[bool | None, str]:
        """Retorna ``None`` para ações internas fora do catálogo público."""
        if not intent or not callable(self.capacidade_getter):
            return None, ""
        try:
            registro = dict(self.capacidade_getter(intent) or {})
        except Exception:
            return None, ""
        if str(registro.get("motivo") or "") == "capacidade_nao_registrada":
            return None, ""
        return bool(registro.get("disponivel")), _codigo(
            registro.get("motivo") or registro.get("estado"), 64,
        )

    @staticmethod
    def _aplicar_orcamento(
        estado: dict[str, Any], decisao: str, agora: float, *, simular: bool,
    ) -> tuple[bool, dict[str, Any]]:
        seguranca = {
            **estado_iniciativa_inicial()["seguranca"],
            **dict(estado.get("seguranca") or {}),
        }
        eventos = [
            dict(item) for item in list(seguranca.get("eventos_orcamento") or [])
            if isinstance(item, Mapping)
            and agora - float(item.get("ts") or 0.0) < JANELA_ORCAMENTO_S
        ]
        limite = MAX_EXECUCOES_JANELA if decisao == "executar" else MAX_SUGESTOES_JANELA
        usados = sum(str(item.get("tipo") or "") == decisao for item in eventos)
        permitido = usados < limite
        if simular:
            seguranca["simulacoes_orcamento"] = int(seguranca.get("simulacoes_orcamento") or 0) + 1
        elif permitido:
            eventos.append({"tipo": decisao, "ts": agora})
        else:
            seguranca["bloqueios_orcamento"] = int(seguranca.get("bloqueios_orcamento") or 0) + 1
        seguranca["eventos_orcamento"] = eventos[-12:]
        estado["seguranca"] = seguranca
        return permitido, seguranca

    def definir_executor(
        self,
        executor: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None,
        *,
        desfazer: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    ) -> None:
        """Conecta integrações somente depois que toda a aplicação está pronta."""
        with self._lock:
            self.executor_acao_cb = executor
            self.desfazer_acao_cb = desfazer

    @staticmethod
    def _acao_reversivel_elegivel(proposta: Any) -> tuple[dict[str, Any] | None, str]:
        """Traduz apenas ações explicitamente auditadas para execução autônoma."""
        if isinstance(proposta, Mapping):
            intent = str(proposta.get("intent") or "").strip().upper()
            params = dict(proposta.get("params") or {}) if isinstance(proposta.get("params"), Mapping) else {}
        else:
            intent = str(proposta or "").strip().upper()
            params = {}

        if intent == "TIME_LIGHT_ON":
            return {
                "intent": "IOT_CONTROL",
                "params": {
                    "acao": "ligar", "alvo": "lampada_quarto",
                    "origem": "autonomia", "confirmado": True,
                },
            }, ""
        if intent == "EXECUTE_INTENT":
            interna = params.get("intent") if isinstance(params.get("intent"), Mapping) else {}
            intent = str(interna.get("intent") or "").strip().upper()
            params = dict(interna.get("params") or {}) if isinstance(interna.get("params"), Mapping) else {}

        if intent == "IOT_CONTROL":
            acao = str(params.get("acao") or "").strip().lower()
            alvo = str(params.get("alvo") or "").strip()
            permitidas_iot = {
                "lampada_quarto": {"ligar", "ajustar_brilho", "ajustar_cor"},
                "tomada_ventilador": {"ligar", "desligar"},
            }
            if acao not in permitidas_iot.get(alvo, set()):
                return None, "acao_iot_fora_da_allowlist"
            normalizada = {
                "acao": acao, "alvo": alvo,
                "origem": "autonomia", "confirmado": True,
            }
            if acao == "ajustar_brilho":
                try:
                    valor = int(params.get("valor"))
                except (TypeError, ValueError):
                    return None, "brilho_invalido"
                if not 10 <= valor <= 80:
                    return None, "brilho_fora_do_limite_autonomo"
                normalizada["valor"] = valor
            elif acao == "ajustar_cor":
                cor = _codigo(params.get("cor"), 24)
                rgb_bruto = params.get("rgb")
                try:
                    rgb = tuple(int(item) for item in rgb_bruto)
                except (TypeError, ValueError):
                    return None, "cor_invalida"
                if not cor or len(rgb) != 3 or any(item < 0 or item > 255 for item in rgb):
                    return None, "cor_invalida"
                normalizada.update(cor=cor, rgb=rgb)
            return {"intent": intent, "params": normalizada}, ""

        if intent == "VOLUME_RELATIVE":
            try:
                delta = int(params.get("delta"))
            except (TypeError, ValueError):
                return None, "volume_relativo_invalido"
            if delta == 0 or not -15 <= delta <= 15:
                return None, "volume_relativo_fora_do_limite_autonomo"
            return {
                "intent": "VOLUME_RELATIVE",
                "params": {"delta": delta, "origem": "autonomia"},
            }, ""

        if intent == "MEDIA_CONTROL":
            acao = str(params.get("acao") or "").strip().lower()
            if acao not in {"pause", "play", "next", "prev"}:
                return None, "controle_midia_fora_da_allowlist"
            return {
                "intent": "MEDIA_CONTROL",
                "params": {
                    "acao": acao, "platform": "music", "origem": "autonomia",
                },
            }, ""

        if intent == "MUSIC_SEARCH":
            query = re.sub(r"\s+", " ", str(params.get("query") or "")).strip()
            if not query or len(query) > 80 or any(ch in query for ch in "\r\n\t"):
                return None, "busca_musical_invalida"
            return {
                "intent": "MUSIC_SEARCH",
                "params": {"query": query, "origem": "autonomia"},
            }, ""

        if intent == "VOLUME":
            acao = str(params.get("acao") or "set").strip().lower()
            if acao not in {"set", "definir", "ajustar", ""}:
                return None, "volume_relativo_ou_mudo_nao_elegivel"
            try:
                nivel = int(params.get("nivel_volume", params.get("value")))
            except (TypeError, ValueError):
                return None, "volume_invalido"
            if not 10 <= nivel <= 60:
                return None, "volume_fora_do_limite_autonomo"
            return {
                "intent": "VOLUME",
                "params": {"acao": "set", "nivel_volume": nivel, "origem": "autonomia"},
            }, ""
        return None, "intent_nao_elegivel"

    @staticmethod
    def _token_desfazer_seguro(valor: Any) -> dict[str, Any]:
        if not isinstance(valor, Mapping):
            return {}
        intent = str(valor.get("intent") or "").strip().upper()
        params = dict(valor.get("params") or {}) if isinstance(valor.get("params"), Mapping) else {}
        if intent == "IOT_CONTROL":
            acao = str(params.get("acao") or "").strip().lower()
            alvo = str(params.get("alvo") or "").strip()
            alvos_acoes = {
                "lampada_quarto": {
                    "ligar", "desligar", "ajustar_brilho", "ajustar_cor", "ajustar_branco",
                },
                "tomada_ventilador": {"ligar", "desligar"},
            }
            if acao in alvos_acoes.get(alvo, set()):
                seguro = {"acao": acao, "alvo": alvo, "origem": "autonomia", "confirmado": True}
                if acao == "ajustar_brilho":
                    try:
                        seguro["valor"] = max(1, min(100, int(params.get("valor"))))
                    except (TypeError, ValueError):
                        return {}
                elif acao == "ajustar_cor":
                    cor = _codigo(params.get("cor"), 24)
                    try:
                        rgb = tuple(int(item) for item in params.get("rgb"))
                    except (TypeError, ValueError):
                        return {}
                    if not cor or len(rgb) != 3 or any(item < 0 or item > 255 for item in rgb):
                        return {}
                    seguro.update(cor=cor, rgb=rgb)
                elif acao == "ajustar_branco":
                    try:
                        seguro["temperatura"] = max(0, min(100, int(params.get("temperatura", 50))))
                        seguro["brilho"] = max(1, min(100, int(params.get("brilho", 70))))
                    except (TypeError, ValueError):
                        return {}
                return {"intent": intent, "params": seguro}
        if intent == "VOLUME":
            try:
                nivel = max(0, min(100, int(params.get("nivel_volume"))))
            except (TypeError, ValueError):
                return {}
            return {"intent": intent, "params": {"acao": "set", "nivel_volume": nivel, "origem": "autonomia"}}
        if intent == "MEDIA_CONTROL":
            acao = str(params.get("acao") or "").strip().lower()
            if acao in {"pause", "play", "next", "prev"}:
                return {
                    "intent": intent,
                    "params": {"acao": acao, "platform": "music", "origem": "autonomia"},
                }
        return {}

    def _contexto(self) -> dict[str, Any]:
        try:
            valor = self.contexto_getter() or {}
            return dict(valor) if isinstance(valor, Mapping) else {}
        except Exception:
            return {}

    @staticmethod
    def _assinatura(dados: Mapping[str, Any]) -> str:
        chave = _codigo(dados.get("chave"), 72)
        if chave:
            return chave
        acao = dados.get("acao_proposta")
        if isinstance(acao, Mapping):
            intent = acao.get("intent")
        else:
            intent = acao
        return ":".join(filter(None, (
            _codigo(dados.get("origem"), 32),
            _codigo(dados.get("tipo"), 32),
            _codigo(intent, 40),
        ))) or "oportunidade"

    @staticmethod
    def _nivel_dominio(estado: Mapping[str, Any], dominio: str) -> int:
        try:
            return max(0, min(3, int(dict(estado.get("niveis") or {}).get(dominio, 1))))
        except (TypeError, ValueError):
            return 1

    @staticmethod
    def _permissao_dominio(estado: Mapping[str, Any], dominio: str) -> str:
        registro = dict(estado.get("permissoes") or {}).get(dominio, {})
        if isinstance(registro, Mapping):
            permissao = str(registro.get("nivel") or "bloqueado")
        else:
            permissao = str(registro or "bloqueado")
        return permissao if permissao in PERMISSOES_INICIATIVA else "bloqueado"

    def _pontuar(
        self,
        dados: Mapping[str, Any],
        contexto: Mapping[str, Any],
        estado: Mapping[str, Any],
    ) -> tuple[int, str, list[str]]:
        tipo = _codigo(dados.get("tipo"), 40) or "observacao"
        dominio = _codigo(dados.get("dominio"), 40) or tipo
        risco = _codigo(dados.get("risco"), 16)
        risco = risco if risco in RISCOS else "medio"
        try:
            pontos = int(dados.get("utilidade", _UTILIDADE_PADRAO.get(tipo, 40)))
        except (TypeError, ValueError):
            pontos = int(_UTILIDADE_PADRAO.get(tipo, 40))
        pontos = max(0, min(100, pontos))
        motivos = [f"utilidade_{pontos}", f"risco_{risco}"]
        pontos -= _PENALIDADE_RISCO[risco]

        confianca = _numero(
            dados.get("confianca"), 0.0, 0.0, 1.0,
        )
        origem = _codigo(dados.get("origem"), 48)
        fala_indireta_confiavel = (
            origem == "fala_indireta_confiavel"
            and confianca >= CONFIANCA_MINIMA_EXECUCAO
        )
        motivos.append(f"confianca_{int(round(confianca * 100))}")
        if fala_indireta_confiavel:
            motivos.append("pedido_indireto_usuario")

        urgente = tipo in TIPOS_URGENTES
        momento_seguro_jogo = bool(dados.get("momento_seguro")) and dominio == "jogo"
        if bool(contexto.get("turno_ativo")) and not urgente and not fala_indireta_confiavel:
            pontos -= 45
            motivos.append("turno_ativo")
        if (
            bool(contexto.get("modo_chat") or contexto.get("conversa_ativa"))
            and not urgente and not momento_seguro_jogo and not fala_indireta_confiavel
        ):
            pontos -= 34
            motivos.append("conversa_ativa")
        if (
            bool(contexto.get("modo_jogo") or contexto.get("modo_jogo_ativo"))
            and not urgente and not momento_seguro_jogo and not fala_indireta_confiavel
        ):
            pontos -= 32
            motivos.append("modo_jogo")
        elif momento_seguro_jogo:
            motivos.append("momento_seguro_jogo")
        if (
            bool(contexto.get("modo_foco") or contexto.get("foco_ativo"))
            and not urgente and not fala_indireta_confiavel
        ):
            pontos -= 24
            motivos.append("modo_foco")
        try:
            ultima_entrada = float(contexto.get("ultima_entrada_ts") or 0.0)
        except (TypeError, ValueError):
            ultima_entrada = 0.0
        if (
            ultima_entrada and self.clock() - ultima_entrada < 30.0
            and not urgente and not fala_indireta_confiavel
        ):
            pontos -= 20
            motivos.append("entrada_recente")
        if bool(dados.get("reversivel")):
            pontos += 5
            motivos.append("acao_reversivel")
        dominio = _codigo(dados.get("dominio"), 40) or tipo
        if (
            bool(dados.get("reversivel"))
            and self._permissao_dominio(estado, dominio) == "acao_reversivel"
        ):
            pontos += 25
            motivos.append("autorizacao_explicita_dominio")

        pontos = max(0, min(100, pontos))
        nivel = self._nivel_dominio(estado, dominio)
        executavel = bool(dados.get("executavel"))
        if (
            pontos >= 85 and executavel and risco == "baixo" and nivel >= 2
            and confianca >= CONFIANCA_MINIMA_EXECUCAO
        ):
            decisao = "executar"
        elif pontos >= 55 and nivel >= 1:
            decisao = "sugerir"
        elif pontos >= 28 and any(m in motivos for m in (
            "turno_ativo", "conversa_ativa", "modo_jogo", "modo_foco", "entrada_recente",
        )):
            decisao = "aguardar"
        else:
            decisao = "ignorar"
        return pontos, decisao, motivos

    @staticmethod
    def _decisao_ideal(evento: Mapping[str, Any]) -> str:
        decisao = str(evento.get("acao_simulada") or evento.get("decisao") or "").casefold()
        return decisao.removeprefix("sombra_")

    def _avaliar_estado(self, estado: Mapping[str, Any]) -> dict[str, Any]:
        """Resume evidência do modo sombra sem transformar evidência em autoridade."""
        historico = [
            dict(item) for item in list(estado.get("historico") or [])
            if isinstance(item, Mapping)
        ]
        contadores = dict(estado.get("contadores") or {})
        avaliadas = max(0, int(contadores.get("avaliadas") or 0))
        duplicadas = max(0, int(contadores.get("duplicadas") or 0))
        total_recebidas = avaliadas + duplicadas
        taxa_duplicacao = round(duplicadas / total_recebidas, 3) if total_recebidas else 0.0
        por_dominio: dict[str, list[dict[str, Any]]] = {}
        for evento in historico:
            dominio = _codigo(evento.get("dominio"), 40) or "geral"
            por_dominio.setdefault(dominio, []).append(evento)

        dominios: dict[str, dict[str, Any]] = {}
        candidatos = 0
        for dominio, eventos in sorted(por_dominio.items()):
            decisoes = [self._decisao_ideal(item) for item in eventos]
            acionaveis = sum(item in {"sugerir", "executar"} for item in decisoes)
            alto_risco_acionavel = sum(
                self._decisao_ideal(item) in {"sugerir", "executar"}
                and str(item.get("risco") or "") == "alto"
                for item in eventos
            )
            motivos = []
            if len(eventos) < 6:
                motivos.append("amostra_insuficiente")
            if acionaveis < 2:
                motivos.append("poucas_oportunidades_uteis")
            if alto_risco_acionavel:
                motivos.append("risco_incompativel")
            if taxa_duplicacao > 0.50:
                motivos.append("fonte_muito_repetitiva")
            pronto = not motivos
            if pronto:
                candidatos += 1
            dominios[dominio] = {
                "status": "candidato_sugestao" if pronto else "observando",
                "amostras": len(eventos),
                "acionaveis": acionaveis,
                "alto_risco_acionavel": alto_risco_acionavel,
                "motivos": motivos,
            }

        return {
            "status": (
                "sem_amostras" if not historico
                else "candidato_sugestao" if candidatos
                else "observando"
            ),
            # Uma auditoria favorável só permite a próxima etapa de teste.
            # Autoridade operacional continua dependendo de escolha explícita.
            "autoriza_execucao": False,
            "amostras": len(historico),
            "taxa_duplicacao": taxa_duplicacao,
            "dominios_candidatos": candidatos,
            "dominios": dominios,
        }

    def avaliar_prontidao(self) -> dict[str, Any]:
        """Atualiza e devolve a auditoria sanitizada do histórico real."""
        with self._lock:
            estado = self._estado()
            auditoria = self._avaliar_estado(estado)
            estado["auditoria"] = auditoria
            self.estado_set(estado)
            return dict(auditoria)

    def configurar_dominio(
        self,
        dominio: str,
        permissao: str,
        *,
        confirmacao_explicita: bool = False,
        origem: str = "usuario_explicito",
    ) -> dict[str, Any]:
        dominio_norm = normalizar_dominio_iniciativa(dominio)
        permissao_norm = str(permissao or "").strip().casefold()
        if not confirmacao_explicita:
            return {"ok": False, "motivo": "confirmacao_explicita_necessaria"}
        if not dominio_norm or permissao_norm not in PERMISSOES_INICIATIVA:
            return {"ok": False, "motivo": "dominio_ou_permissao_invalida"}
        with self._lock:
            estado = self._estado()
            permissoes = dict(estado.get("permissoes") or {})
            permissoes[dominio_norm] = {
                "nivel": permissao_norm,
                "confirmado_em": float(self.clock()),
                "origem": _codigo(origem, 32) or "usuario_explicito",
            }
            estado["permissoes"] = permissoes
            niveis = dict(estado.get("niveis") or {})
            niveis[dominio_norm] = {
                "bloqueado": 0,
                "sugestao": 1,
                "acao_reversivel": 2,
            }[permissao_norm]
            estado["niveis"] = niveis
            niveis_ativos = {
                str(dict(valor or {}).get("nivel") or "bloqueado")
                for valor in permissoes.values() if isinstance(valor, Mapping)
            }
            estado["modo"] = (
                "autorizado" if "acao_reversivel" in niveis_ativos
                else "sugestao" if "sugestao" in niveis_ativos
                else "sombra"
            )
            self.estado_set(estado)
        return {
            "ok": True, "dominio": dominio_norm, "permissao": permissao_norm,
            "modo": estado["modo"],
        }

    def permissoes_atuais(self) -> dict[str, Any]:
        with self._lock:
            estado = self._estado()
            return {
                "modo": str(estado.get("modo") or "sombra"),
                "dominios": {
                    dominio: self._permissao_dominio(estado, dominio)
                    for dominio in sorted(dict(estado.get("permissoes") or {}))
                },
            }

    def configurar_perfil_seguro(
        self,
        permissao: str = "acao_reversivel",
        *,
        confirmacao_explicita: bool = False,
    ) -> dict[str, Any]:
        """Agrupa somente domínios com execução autônoma auditada e reversível."""
        permissao_norm = str(permissao or "").strip().casefold()
        if not confirmacao_explicita:
            return {"ok": False, "motivo": "confirmacao_explicita_necessaria"}
        if permissao_norm not in {"acao_reversivel", "bloqueado"}:
            return {"ok": False, "motivo": "permissao_invalida_para_perfil_seguro"}
        resultados = [
            self.configurar_dominio(
                dominio,
                permissao_norm,
                confirmacao_explicita=True,
            )
            for dominio in DOMINIOS_PERFIL_SEGURO
        ]
        if not all(item.get("ok") for item in resultados):
            return {"ok": False, "motivo": "falha_ao_configurar_perfil_seguro"}
        return {
            "ok": True,
            "perfil": "seguro",
            "permissao": permissao_norm,
            "dominios": list(DOMINIOS_PERFIL_SEGURO),
            "modo": self.permissoes_atuais()["modo"],
        }

    def ativar_perfil_seguro_padrao(self) -> dict[str, Any]:
        """Ativa o perfil natural sem reverter escolhas já feitas pelo usuário."""
        with self._lock:
            estado = self._estado()
            existentes = set(dict(estado.get("permissoes") or {}))
        faltantes = [
            dominio for dominio in DOMINIOS_PERFIL_SEGURO
            if dominio not in existentes
        ]
        resultados = [
            self.configurar_dominio(
                dominio,
                "acao_reversivel",
                confirmacao_explicita=True,
                origem="padrao_seguro",
            )
            for dominio in faltantes
        ]
        return {
            "ok": all(item.get("ok") for item in resultados),
            "perfil": "seguro",
            "ativados": faltantes,
            "preservados": sorted(existentes & set(DOMINIOS_PERFIL_SEGURO)),
            "modo": self.permissoes_atuais()["modo"],
        }

    def _registrar_resultado_execucao(
        self,
        evento_id: str,
        dominio: str,
        resultado: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        dados = dict(resultado or {})
        ok = bool(dados.get("ok")) and bool(dados.get("confirmado"))
        status = _codigo(dados.get("status"), 64) or ("confirmado" if ok else "falha_execucao")
        agora = float(self.clock())
        with self._lock:
            estado = self._estado()
            execucao = dict(estado.get("execucao") or {})
            falhas = dict(execucao.get("falhas_consecutivas") or {})
            circuitos = dict(execucao.get("circuitos_ate") or {})
            if ok:
                falhas[dominio] = 0
                circuitos.pop(dominio, None)
            else:
                falhas[dominio] = int(falhas.get(dominio) or 0) + 1
                if falhas[dominio] >= FALHAS_ATE_ABRIR_CIRCUITO:
                    circuitos[dominio] = agora + CIRCUITO_ABERTO_S
            token = self._token_desfazer_seguro(dados.get("desfazer")) if ok else {}
            if token:
                execucao["ultimo_desfazer"] = {
                    "acao": token, "dominio": dominio, "criado_em": agora,
                    "expira_em": agora + 1800.0,
                }
            execucao.update(
                falhas_consecutivas=falhas,
                circuitos_ate=circuitos,
                ultima_execucao={
                    "evento_id": evento_id, "dominio": dominio,
                    "ok": ok, "confirmado": bool(dados.get("confirmado")),
                    "status": status, "ts": agora,
                },
            )
            historico = list(estado.get("historico") or [])
            for indice in range(len(historico) - 1, -1, -1):
                if str(historico[indice].get("id") or "") == evento_id:
                    historico[indice] = {
                        **dict(historico[indice]),
                        "execucao": {
                            "ok": ok,
                            "confirmado": bool(dados.get("confirmado")),
                            "status": status,
                        },
                        "decisao": "executado" if ok else "execucao_falhou",
                    }
                    break
            estado["historico"] = historico[-self.limite_historico:]
            estado["execucao"] = execucao
            estado["ultima_decisao"] = next(
                (dict(item) for item in reversed(historico) if item.get("id") == evento_id),
                dict(estado.get("ultima_decisao") or {}),
            )
            self.estado_set(estado)
            return dict(estado["ultima_decisao"])

    def desfazer_ultima(self, *, confirmacao_explicita: bool = False) -> dict[str, Any]:
        if not confirmacao_explicita:
            return {"ok": False, "motivo": "confirmacao_explicita_necessaria"}
        with self._lock:
            estado = self._estado()
            execucao = dict(estado.get("execucao") or {})
            registro = dict(execucao.get("ultimo_desfazer") or {})
        if not registro or not callable(self.desfazer_acao_cb):
            return {"ok": False, "motivo": "nenhuma_acao_autonoma_reversivel"}
        try:
            if float(self.clock()) >= float(registro.get("expira_em") or 0.0):
                return {"ok": False, "motivo": "prazo_para_desfazer_expirou"}
        except (TypeError, ValueError):
            return {"ok": False, "motivo": "token_de_desfazer_invalido"}
        try:
            resultado = dict(self.desfazer_acao_cb(dict(registro.get("acao") or {})) or {})
        except Exception as exc:
            self.log(f"⚠️ [INICIATIVA] falha ao desfazer ação: {exc}")
            resultado = {"ok": False, "confirmado": False, "status": "erro_ao_desfazer"}
        ok = bool(resultado.get("ok")) and bool(resultado.get("confirmado"))
        with self._lock:
            estado = self._estado()
            execucao = dict(estado.get("execucao") or {})
            execucao["ultima_reversao"] = {
                "ok": ok,
                "status": _codigo(resultado.get("status"), 64),
                "ts": float(self.clock()),
            }
            if ok:
                execucao["ultimo_desfazer"] = {}
            estado["execucao"] = execucao
            self.estado_set(estado)
        return {
            "ok": ok,
            "confirmado": bool(resultado.get("confirmado")),
            "status": str(resultado.get("status") or ""),
        }

    def registrar(self, oportunidade: Mapping[str, Any] | None) -> dict[str, Any]:
        dados = dict(oportunidade or {})
        agora = float(self.clock())
        assinatura = self._assinatura(dados)
        acao_normalizada: dict[str, Any] | None = None
        with self._lock:
            estado = self._estado()
            historico = list(estado.get("historico") or [])
            try:
                confianca_entrada = float(dados.get("confianca") or 0.0)
            except (TypeError, ValueError):
                confianca_entrada = 0.0
            pedido_indireto_confiavel = (
                _codigo(dados.get("origem"), 48) == "fala_indireta_confiavel"
                and confianca_entrada >= CONFIANCA_MINIMA_EXECUCAO
            )
            repetida = next((
                item for item in reversed(historico)
                if item.get("assinatura") == assinatura
                and agora - float(item.get("ts") or 0.0) < self.janela_repeticao_s
            ), None)
            if repetida is not None and not pedido_indireto_confiavel:
                contadores = dict(estado.get("contadores") or {})
                contadores["duplicadas"] = int(contadores.get("duplicadas") or 0) + 1
                estado["contadores"] = contadores
                estado["auditoria"] = self._avaliar_estado(estado)
                self.estado_set(estado)
                return {**dict(repetida), "duplicada": True}

            contexto = self._contexto()
            pontos, ideal, motivos = self._pontuar(dados, contexto, estado)
            modo = str(estado.get("modo") or self.modo_padrao)
            risco = _codigo(dados.get("risco"), 16)
            risco = risco if risco in RISCOS else "medio"
            dominio = _codigo(dados.get("dominio"), 40)
            permissao = self._permissao_dominio(estado, dominio)
            acao_proposta = dados.get("acao_proposta")
            intent_capacidade = self._intent_capacidade(acao_proposta)
            disponivel, motivo_capacidade = self._capacidade_disponivel(intent_capacidade)
            seguranca = dict(estado.get("seguranca") or {})
            if disponivel is False and ideal in {"sugerir", "executar"}:
                ideal = "aguardar"
                motivos.extend(("capacidade_indisponivel", motivo_capacidade or "estado_indisponivel"))
                seguranca["bloqueios_capacidade"] = int(seguranca.get("bloqueios_capacidade") or 0) + 1
            if intent_capacidade in INTENTS_COM_CONFIRMACAO_HUMANA and ideal == "executar":
                ideal = "sugerir"
                motivos.append("confirmacao_humana_obrigatoria")
                seguranca["bloqueios_confirmacao"] = int(seguranca.get("bloqueios_confirmacao") or 0) + 1
            estado["seguranca"] = seguranca

            if modo == "sombra" and ideal in {"sugerir", "executar"}:
                self._aplicar_orcamento(estado, ideal, agora, simular=True)
            if modo == "desligado":
                acao_real = "ignorar"
            elif modo == "sombra":
                acao_real = f"sombra_{ideal}"
            elif ideal == "executar":
                if (
                    modo == "autorizado" and permissao == "acao_reversivel"
                    and risco == "baixo" and bool(dados.get("reversivel"))
                ):
                    acao_normalizada, motivo_inelegivel = self._acao_reversivel_elegivel(acao_proposta)
                    execucao = dict(estado.get("execucao") or {})
                    circuito_ate = float(dict(execucao.get("circuitos_ate") or {}).get(dominio) or 0.0)
                    if circuito_ate > agora:
                        acao_real = "bloqueado_circuito"
                        motivos.append("circuito_aberto")
                    elif acao_normalizada is None:
                        acao_real = "sugerir"
                        motivos.append(motivo_inelegivel)
                    elif not callable(self.executor_acao_cb):
                        acao_real = "sugerir"
                        motivos.append("executor_nao_conectado")
                    else:
                        acao_real = "executar"
                elif permissao in {"sugestao", "acao_reversivel"}:
                    acao_real = "sugerir"
                else:
                    acao_real = "bloqueado_permissao"
            elif ideal == "sugerir":
                acao_real = (
                    "sugerir" if permissao in {"sugestao", "acao_reversivel"}
                    else "bloqueado_permissao"
                )
            else:
                acao_real = ideal
            if modo != "sombra" and acao_real in {"sugerir", "executar"}:
                permitido_orcamento, _ = self._aplicar_orcamento(
                    estado, acao_real, agora, simular=False,
                )
                if not permitido_orcamento:
                    acao_real = "aguardar"
                    motivos.append("orcamento_de_iniciativas_esgotado")
            intent = acao_proposta.get("intent") if isinstance(acao_proposta, Mapping) else acao_proposta
            evento = {
                "id": f"ini-{int(agora * 1000)}",
                "assinatura": assinatura,
                "tipo": _codigo(dados.get("tipo"), 40) or "observacao",
                "origem": _codigo(dados.get("origem"), 40) or "desconhecida",
                "dominio": dominio,
                "intent": _codigo(intent, 48),
                "intent_capacidade": _codigo(intent_capacidade, 48),
                "risco": risco,
                "permissao": permissao,
                "pontuacao": pontos,
                "confianca": round(float(dados.get("confianca") or 0.0), 3),
                "decisao": acao_real,
                "acao_simulada": ideal if modo == "sombra" else "",
                "motivos": [_codigo(item, 64) for item in motivos[:6]],
                "ts": agora,
                "validade_ate": agora + max(1.0, float(dados.get("validade_s") or 180.0)),
                "contexto": {
                    "jogo": bool(contexto.get("modo_jogo") or contexto.get("modo_jogo_ativo")),
                    "conversa": bool(contexto.get("modo_chat") or contexto.get("conversa_ativa")),
                    "foco": bool(contexto.get("modo_foco") or contexto.get("foco_ativo")),
                },
                "seguranca": {
                    "modo": "vontade_segura",
                    "capacidade_disponivel": disponivel,
                    "confirmacao_humana": intent_capacidade in INTENTS_COM_CONFIRMACAO_HUMANA,
                    "orcamento_simulado": modo == "sombra" and ideal in {"sugerir", "executar"},
                },
            }
            historico.append(evento)
            contadores = dict(estado.get("contadores") or {})
            contadores["avaliadas"] = int(contadores.get("avaliadas") or 0) + 1
            chave_contador = {
                "ignorar": "ignoradas",
                "aguardar": "aguardariam",
                "sugerir": "sugeririam",
                "executar": "executariam",
            }[ideal]
            contadores[chave_contador] = int(contadores.get(chave_contador) or 0) + 1
            estado.update(
                historico=historico[-self.limite_historico:],
                contadores=contadores,
                ultima_decisao=evento,
            )
            estado["auditoria"] = self._avaliar_estado(estado)
            self.estado_set(estado)

        if acao_real == "executar" and acao_normalizada is not None:
            try:
                resultado_execucao = dict(self.executor_acao_cb(acao_normalizada) or {})
            except Exception as exc:
                self.log(f"⚠️ [INICIATIVA] executor autônomo falhou: {exc}")
                resultado_execucao = {
                    "ok": False, "confirmado": False, "status": "erro_executor",
                }
            evento = self._registrar_resultado_execucao(
                evento["id"], evento["dominio"], resultado_execucao,
            )

        if callable(self.registrar_decisao_cb):
            try:
                self.registrar_decisao_cb(
                    "iniciativa", acao_real, motivos, categoria=evento["tipo"],
                )
            except Exception:
                pass
        if modo == "sombra":
            self.log(
                f"🧭 [INICIATIVA:SOMBRA] {ideal} | "
                f"tipo={evento['tipo']} pontuação={pontos} risco={risco}"
            )
        elif acao_real == "executar":
            execucao_evento = dict(evento.get("execucao") or {})
            self.log(
                f"🧭 [INICIATIVA:EXECUÇÃO] status={execucao_evento.get('status', '')} "
                f"confirmado={bool(execucao_evento.get('confirmado'))} domínio={evento['dominio']}"
            )
        return dict(evento)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._estado()


def criar_motor_iniciativa_runtime(**kwargs: Any) -> MotorIniciativaRuntime:
    return MotorIniciativaRuntime(**kwargs)
