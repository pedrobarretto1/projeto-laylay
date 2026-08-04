"""Avaliação emocional causal de resultados operacionais confirmados.

O avaliador não executa comandos e não cria fatos. Ele mantém somente um histórico
curto da sessão para distinguir uma falha isolada de uma repetição e atribui a
responsabilidade apenas quando o contrato do executor oferece evidência suficiente.
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import (
    normalizar_texto_basico as _normalizar,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


_STATUS_FALHA_SISTEMA = frozenset({
    "falha_execucao", "indisponivel", "protocolo_indisponivel",
    "app_aberto_sem_foco", "falha_consulta", "erro_conexao", "timeout",
})
_STATUS_REDUNDANCIA_VISIVEL = frozenset({
    "ja_aberto_focado", "site_ja_aberto_focado",
    "ja_estava_ligado", "ja_estava_desligado",
})
_STATUS_FALHA_LAYLAY = frozenset({
    "alvo_ausente", "acao_invalida", "falha_validacao",
})
_INTENTS_SENSIVEIS = frozenset({
    "DELETE_ITEM", "CONFIRM_DELETE_ITEM", "LOCK_PC", "SEND_EMAIL",
    "CANCELAR_AGENDAMENTO",
})
_SINAIS_VULNERABILIDADE = re.compile(
    r"\b(?:triste|mal|ansios[oa]|nervos[oa]|com medo|desabaf|cansad[oa]|"
    r"deprimid[oa]|chorando|n[aã]o aguento|me ajuda)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class AvaliacaoEventoEmocional:
    emocao: str = "calma"
    nivel: int = 1
    causa: str = "resultado operacional observado"
    responsabilidade: str = "ambigua"
    confianca: float = 0.0
    repeticoes: int = 1
    provocacao_usuario: int = 0
    permite_expressao: bool = False
    motivo_expressao: str = "evento_neutro_sem_expressao"
    arco: str = "neutro"
    ts: float = 0.0

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


class AvaliadorEventosEmocionaisRuntime:
    """Mantém avaliação e histórico efêmeros, isolados por intenção e alvo."""

    def __init__(
        self,
        *,
        time_cb: Callable[[], float] = time.time,
        janela_s: float = 300.0,
        log: Callable[..., Any] = print,
    ) -> None:
        self.time_cb = time_cb
        self.janela_s = max(30.0, float(janela_s or 300.0))
        self.log = log
        self._lock = threading.RLock()
        self._historico: list[dict[str, Any]] = []
        self._metricas: dict[str, Any] = {
            "avaliados": 0,
            "expressoes": 0,
            "contencoes": 0,
            "contencoes_por_motivo": {},
            "responsabilidade_usuario": 0,
            "responsabilidade_laylay": 0,
            "responsabilidade_sistema": 0,
            "ambiguos": 0,
            "recuperacoes": 0,
        }
        self._ultima: dict[str, Any] = {}

    @staticmethod
    def _assinatura(resultado: ResultadoAcao) -> str:
        return f"{_normalizar(resultado.intent)}::{_normalizar(resultado.alvo)}"

    @staticmethod
    def _classe(resultado: ResultadoAcao) -> str:
        status = _normalizar(resultado.status).replace(" ", "_")
        # Um estado já satisfeito é uma não-ação confirmada, não uma falha.
        if status in _STATUS_REDUNDANCIA_VISIVEL and resultado.confirmado is True:
            return "redundancia_visivel"
        if (
            resultado.executou is False
            or resultado.confirmado is False
            or status in _STATUS_FALHA_SISTEMA
            or status in _STATUS_FALHA_LAYLAY
            or any(sinal in status for sinal in ("falha", "erro", "indisponivel", "timeout"))
        ):
            return "falha"
        if resultado.executou is True and resultado.confirmado is True:
            return "sucesso"
        return "incerto"

    @staticmethod
    def _confianca_entrada(resultado: ResultadoAcao) -> float:
        for fonte in (resultado.contexto, resultado.params):
            for chave in ("confianca", "confidence", "confianca_interpretacao"):
                if chave not in fonte:
                    continue
                try:
                    valor = float(fonte.get(chave))
                    return valor / 100.0 if valor > 1.0 else valor
                except (TypeError, ValueError):
                    pass
        return 1.0

    @staticmethod
    def _responsabilidade_explicita(resultado: ResultadoAcao) -> tuple[str, float]:
        contexto = dict(resultado.contexto or {})
        responsabilidade = _normalizar(
            contexto.get("responsabilidade") or contexto.get("origem_falha")
        )
        aliases = {
            "usuario": "usuario", "pessoa": "usuario",
            "laylay": "laylay", "assistente": "laylay", "interpretacao": "laylay",
            "sistema": "sistema", "executor": "sistema", "dispositivo": "sistema",
        }
        resolvida = aliases.get(responsabilidade, "")
        if not resolvida:
            return "", 0.0
        try:
            confianca = float(contexto.get("confianca_responsabilidade") or 0.98)
        except (TypeError, ValueError):
            confianca = 0.98
        return resolvida, max(0.0, min(1.0, confianca))

    def _recentes(self, assinatura: str, agora: float) -> list[dict[str, Any]]:
        limite = agora - self.janela_s
        self._historico = [
            item for item in self._historico
            if float(item.get("ts") or 0.0) >= limite
        ][-79:]
        return [item for item in self._historico if item.get("assinatura") == assinatura]

    @staticmethod
    def _contar_finais(recentes: list[dict[str, Any]], classe: str) -> int:
        total = 0
        for item in reversed(recentes):
            if item.get("classe") != classe:
                break
            total += 1
        return total

    def avaliar(self, resultado: ResultadoAcao) -> dict[str, Any]:
        agora = float(self.time_cb())
        assinatura = self._assinatura(resultado)
        classe = self._classe(resultado)
        status = _normalizar(resultado.status).replace(" ", "_")
        intent = str(resultado.intent or "").strip().upper()
        entrada_confiavel = self._confianca_entrada(resultado) >= 0.90
        sensivel = intent in _INTENTS_SENSIVEIS or bool(
            _SINAIS_VULNERABILIDADE.search(str(resultado.texto_usuario or ""))
        )

        with self._lock:
            recentes = self._recentes(assinatura, agora)
            falhas_anteriores = self._contar_finais(recentes, "falha")
            redundancias_anteriores = self._contar_finais(
                recentes, "redundancia_visivel"
            )
            responsabilidade, confianca = self._responsabilidade_explicita(resultado)
            emocao, nivel, provocacao = "calma", 1, 0
            permite, arco = False, "neutro"
            motivo_expressao = "evento_neutro_sem_expressao"
            repeticoes = 1
            causa = f"resultado {status or classe} observado"

            if classe == "sucesso" and falhas_anteriores >= 2:
                responsabilidade = str(recentes[-1].get("responsabilidade") or "sistema")
                confianca = max(confianca, 0.95)
                emocao, nivel, permite, arco = "acalmando-se", 1, True, "alivio"
                repeticoes = falhas_anteriores + 1
                causa = f"sucesso após {falhas_anteriores} falhas consecutivas"
                self._metricas["recuperacoes"] += 1
                motivo_expressao = "alivio_causal_confirmado"
            elif classe == "redundancia_visivel":
                responsabilidade = responsabilidade or "usuario"
                confianca = max(confianca, 0.94 if entrada_confiavel else 0.70)
                repeticoes = redundancias_anteriores + 1
                permite = bool(confianca >= 0.90 and entrada_confiavel and not sensivel)
                provocacao = min(3, repeticoes) if permite else 0
                if not permite:
                    emocao, nivel, arco = "calma", 1, "observacao"
                    motivo_expressao = (
                        "contexto_sensivel"
                        if sensivel
                        else "entrada_ou_responsabilidade_sem_confianca"
                    )
                elif repeticoes == 1:
                    emocao, nivel, arco = "debochada", 1, "provocacao_afetuosa"
                    motivo_expressao = "redundancia_confirmada"
                elif repeticoes == 2:
                    emocao, nivel, arco = "debochada", 2, "provocacao_afetuosa"
                    motivo_expressao = "redundancia_confirmada_repetida"
                elif repeticoes == 3:
                    emocao, nivel, arco = "irritada", 2, "bronca_brincalhona"
                    motivo_expressao = "redundancia_confirmada_repetida"
                else:
                    emocao, nivel, arco = "brava", 3, "bronca_brincalhona"
                    motivo_expressao = "redundancia_confirmada_repetida"
                causa = (
                    f"{repeticoes} pedidos redundantes consecutivos do usuário "
                    "com estado já confirmado"
                )
            elif classe == "falha":
                repeticoes = falhas_anteriores + 1
                if not responsabilidade:
                    if status in _STATUS_FALHA_SISTEMA:
                        responsabilidade, confianca = "sistema", 0.96
                    elif status in _STATUS_FALHA_LAYLAY:
                        responsabilidade, confianca = "laylay", 0.82
                    else:
                        responsabilidade, confianca = "ambigua", 0.55

                if responsabilidade == "sistema" and repeticoes >= 2:
                    emocao = "irritada" if repeticoes < 4 else "brava"
                    nivel = 1 if repeticoes == 2 else 2
                    permite = not sensivel
                    arco = "irritacao_compartilhada"
                    causa = f"{repeticoes} falhas consecutivas do sistema em {resultado.alvo or intent}"
                    motivo_expressao = (
                        "contexto_sensivel"
                        if sensivel
                        else "falha_sistema_repetida"
                    )
                elif responsabilidade == "laylay" and confianca >= 0.90:
                    emocao, nivel, permite = "envergonhada", 1, True
                    arco = "autorreparo"
                    causa = "falha atribuída à própria interpretação da Laylay"
                    motivo_expressao = "autoria_da_falha_confirmada"
                elif responsabilidade == "usuario" and confianca >= 0.90 and not sensivel:
                    emocao, nivel, permite = "debochada", 1, True
                    provocacao, arco = 1, "provocacao_afetuosa"
                    causa = "engano do usuário confirmado pelo executor"
                    motivo_expressao = "engano_usuario_confirmado"
                elif sensivel:
                    motivo_expressao = "contexto_sensivel"
                elif repeticoes < 2 and responsabilidade == "sistema":
                    motivo_expressao = "falha_sistema_isolada"
                elif responsabilidade == "laylay":
                    motivo_expressao = "autoria_da_falha_incerta"
                else:
                    motivo_expressao = "responsabilidade_ambigua"
            elif classe == "sucesso":
                motivo_expressao = "sucesso_rotineiro_sem_reacao_causal"
            elif classe == "incerto":
                motivo_expressao = "resultado_incerto"

            avaliacao = AvaliacaoEventoEmocional(
                emocao=emocao,
                nivel=nivel,
                causa=causa,
                responsabilidade=responsabilidade or "ambigua",
                confianca=round(max(0.0, min(1.0, confianca)), 3),
                repeticoes=repeticoes,
                provocacao_usuario=provocacao,
                permite_expressao=permite,
                motivo_expressao=motivo_expressao,
                arco=arco,
                ts=agora,
            ).como_dict()
            self._historico.append({
                "assinatura": assinatura,
                "classe": classe,
                "status": status,
                "responsabilidade": avaliacao["responsabilidade"],
                "ts": agora,
            })
            self._historico = self._historico[-80:]
            self._metricas["avaliados"] += 1
            chave_metrica = f"responsabilidade_{avaliacao['responsabilidade']}"
            if chave_metrica in self._metricas:
                self._metricas[chave_metrica] += 1
            else:
                self._metricas["ambiguos"] += 1
            if permite:
                self._metricas["expressoes"] += 1
            else:
                self._metricas["contencoes"] += 1
                motivos = self._metricas["contencoes_por_motivo"]
                motivos[motivo_expressao] = int(motivos.get(motivo_expressao) or 0) + 1
            self._ultima = dict(avaliacao)
            return avaliacao

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            avaliados = int(self._metricas.get("avaliados") or 0)
            expressoes = int(self._metricas.get("expressoes") or 0)
            return {
                **dict(self._metricas),
                "taxa_expressao": round(expressoes / avaliados, 3) if avaliados else 0.0,
                "ultima_decisao_expressao": (
                    "expressar"
                    if self._ultima.get("permite_expressao")
                    else "conter"
                ) if self._ultima else "sem_amostras",
                "historico_efemero": len(self._historico),
                "ultima": dict(self._ultima),
                "autoriza_execucao": False,
                "persistencia_pessoal": False,
            }


def contextualizar_fala_evento(
    fala: str,
    avaliacao: Mapping[str, Any] | None,
) -> str:
    """Acrescenta uma reação curta sem alterar o resultado operacional."""
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    evento = dict(avaliacao or {})
    if not texto or not evento.get("permite_expressao") or len(texto) > 210:
        return texto

    arco = str(evento.get("arco") or "")
    repeticoes = max(1, int(evento.get("repeticoes") or 1))
    provocacao = max(0, int(evento.get("provocacao_usuario") or 0))
    complemento = ""
    if arco in {"provocacao_afetuosa", "bronca_brincalhona"} and re.search(
        r"\b(?:na tua cara|mais exposto que|seus olhos|criatura)\b",
        _normalizar(texto),
    ):
        return texto
    if arco in {"provocacao_afetuosa", "bronca_brincalhona"}:
        frases = [parte.strip() for parte in re.split(r"(?<=[.!])\s+", texto) if parte.strip()]
        if len(frases) > 1:
            # Conserva a confirmação factual e substitui uma decoração genérica
            # pela reação causal, evitando duas piadas na mesma resposta.
            texto = frases[0]
    if arco == "provocacao_afetuosa" and provocacao == 1:
        complemento = "Seus olhos tiraram uma folguinha agora."
    elif arco == "provocacao_afetuosa" and provocacao >= 2:
        complemento = "Criatura, agora eu já tenho evidência contra a sua atenção."
    elif arco == "bronca_brincalhona" and repeticoes == 3:
        complemento = "Você está me testando, né? Eu já conferi isso três vezes."
    elif arco == "bronca_brincalhona" and repeticoes >= 4:
        complemento = "Chega, criatura. Continua igual e eu não vou fingir que a quarta vez mudou alguma coisa."
    elif arco == "irritacao_compartilhada" and repeticoes == 2:
        complemento = "É a segunda falha seguida; isso está começando a testar minha paciência."
    elif arco == "irritacao_compartilhada" and repeticoes == 3:
        complemento = "De novo. Agora isso está oficialmente me irritando."
    elif arco == "irritacao_compartilhada" and repeticoes >= 4:
        complemento = "Esse sistema acordou decidido a me desafiar hoje."
    elif arco == "autorreparo":
        complemento = "Essa foi minha; não vou jogar a culpa em você."
    elif arco == "alivio":
        complemento = "Finalmente. O sistema desistiu de bancar o rebelde."

    if not complemento or _normalizar(complemento) in _normalizar(texto):
        return texto
    return f"{texto} {complemento}"


def criar_avaliador_eventos_emocionais_runtime(
    **kwargs: Any,
) -> AvaliadorEventosEmocionaisRuntime:
    return AvaliadorEventosEmocionaisRuntime(**kwargs)
