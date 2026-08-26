"""Avalia quando uma hipótese pode influenciar o comportamento da Laylay."""

from __future__ import annotations

from datetime import datetime
import math
from typing import Any, Callable, Dict


_MEIA_VIDA_DIAS = {
    "rotina_observada": 30.0,
    "rotina": 60.0,
    "preferencia_contextual": 180.0,
    "preferencia_musical": 120.0,
    "resultado_habilidade": 45.0,
}


class MaturidadeAprendizadoRuntime:
    def __init__(
        self,
        *,
        memoria_sqlite: Any,
        contexto_getter: Callable[[], Dict[str, Any]],
        agora: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.memoria = memoria_sqlite
        self.contexto_getter = contexto_getter
        self.agora = agora

    def _contexto(self) -> Dict[str, Any]:
        try:
            contexto = self.contexto_getter() or {}
            return contexto if isinstance(contexto, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _contexto_compativel(
        atual: Dict[str, Any], evidencia: Dict[str, Any], *, global_: bool,
    ) -> tuple[bool, list[str]]:
        if global_:
            return True, []
        divergencias = []
        aliases = {
            "periodo": ("periodo",),
            "fase": ("fase",),
            "aplicativo": ("aplicativo", "exe"),
            "atividade": ("atividade", "tipo_atividade", "assunto"),
        }
        for rotulo, chaves in aliases.items():
            esperado = next((str(evidencia.get(chave) or "").strip().casefold() for chave in chaves if evidencia.get(chave)), "")
            presente = next((str(atual.get(chave) or "").strip().casefold() for chave in chaves if atual.get(chave)), "")
            if esperado and presente and esperado != presente:
                divergencias.append(rotulo)
        return not divergencias, divergencias

    def avaliar(
        self, chave: str, *, contexto: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        hipotese = self.memoria.obter_hipotese_aprendizado(chave)
        if not isinstance(hipotese, dict):
            return {
                "chave": chave, "nivel": "ausente", "aplicavel": False,
                "confianca_efetiva": 0.0, "motivos": ["hipótese inexistente"],
            }
        eventos = self.memoria.listar_eventos_aprendizado(chave, limit=100)
        positivos = [item for item in eventos if float(item.get("sinal") or 0.0) > 0]
        negativos = [item for item in eventos if float(item.get("sinal") or 0.0) < 0]
        confirmacoes = sum(bool(item.get("confirmado_usuario")) for item in positivos)
        dias_distintos = {
            str(item.get("criado_em") or "")[:10] for item in positivos
            if str(item.get("criado_em") or "")
        }
        try:
            ultima = datetime.fromisoformat(str(hipotese.get("ultima_evidencia_em") or ""))
            idade_dias = max(0.0, (self.agora() - ultima).total_seconds() / 86400.0)
        except Exception:
            idade_dias = 0.0
        tipo = str(hipotese.get("tipo") or "padrao")
        meia_vida_base = float(_MEIA_VIDA_DIAS.get(tipo, 90.0))
        # Repetições independentes tornam o padrão mais durável, mas nunca
        # imortal. Sem novos reforços, até uma preferência confirmada decai.
        reforcos_ponderados = len(dias_distintos) + (confirmacoes * 1.5)
        fator_reforco = 1.0 + min(2.5, math.log2(1.0 + reforcos_ponderados) * 0.55)
        meia_vida = meia_vida_base * fator_reforco
        confianca = float(hipotese.get("confianca") or 0.0)
        confianca_efetiva = confianca * (0.5 ** (idade_dias / meia_vida))
        confianca_efetiva = max(0.0, min(0.99, confianca_efetiva))

        status = str(hipotese.get("status") or "candidata")
        if status in {"enfraquecida", "resolvida"} or confianca_efetiva < 0.30:
            nivel = "enfraquecida"
        elif confirmacoes and confianca_efetiva >= 0.72:
            nivel = "confirmada"
        elif len(positivos) >= 2 and len(dias_distintos) >= 2 and confianca_efetiva >= 0.68:
            nivel = "provavel"
        elif positivos:
            nivel = "hipotese"
        else:
            nivel = "observacao"

        evidencia_recente = positivos[0] if positivos else {}
        contexto_evidencia = (
            evidencia_recente.get("contexto")
            if isinstance(evidencia_recente.get("contexto"), dict) else {}
        )
        global_ = bool(contexto_evidencia.get("global"))
        compativel, divergencias = self._contexto_compativel(
            dict(contexto or self._contexto()), contexto_evidencia, global_=global_,
        )
        aplicavel = bool(
            nivel in {"confirmada", "provavel"}
            and compativel
            and len(negativos) <= len(positivos) + confirmacoes
        )
        motivos = []
        if divergencias:
            motivos.append(f"contexto divergente: {', '.join(divergencias)}")
        if nivel not in {"confirmada", "provavel"}:
            motivos.append(f"maturidade insuficiente: {nivel}")
        if len(negativos) > len(positivos) + confirmacoes:
            motivos.append("evidências negativas predominam")

        excecao_ativa: Dict[str, Any] = {}
        if tipo in {"preferencia_contextual", "preferencia_musical"}:
            contexto_atual = dict(contexto or self._contexto())
            try:
                candidatas_excecao = self.memoria.listar_hipoteses_aprendizado(limit=500)
            except Exception:
                candidatas_excecao = []
            for candidata in candidatas_excecao:
                if str(candidata.get("tipo") or "") != "excecao_preferencia":
                    continue
                valor_excecao = candidata.get("valor") if isinstance(candidata.get("valor"), dict) else {}
                if str(valor_excecao.get("preferencia_base") or "") != chave:
                    continue
                eventos_excecao = self.memoria.listar_eventos_aprendizado(
                    str(candidata.get("chave") or ""), limit=20,
                )
                positiva = next(
                    (item for item in eventos_excecao if float(item.get("sinal") or 0.0) > 0),
                    {},
                )
                contexto_excecao = (
                    positiva.get("contexto")
                    if isinstance(positiva.get("contexto"), dict) else {}
                )
                compativel_excecao, _ = self._contexto_compativel(
                    contexto_atual, contexto_excecao, global_=False,
                )
                if (
                    compativel_excecao
                    and str(candidata.get("status") or "") == "ativa"
                    and float(candidata.get("confianca") or 0.0) >= 0.68
                ):
                    excecao_ativa = candidata
                    aplicavel = False
                    motivos.append("exceção confirmada para o contexto atual")
                    break
        return {
            "chave": chave,
            "nivel": nivel,
            "aplicavel": aplicavel,
            "confianca": round(confianca, 3),
            "confianca_efetiva": round(confianca_efetiva, 3),
            "idade_sem_reforco_dias": round(idade_dias, 2),
            "meia_vida_base_dias": round(meia_vida_base, 2),
            "meia_vida_ajustada_dias": round(meia_vida, 2),
            "fator_reforco": round(fator_reforco, 3),
            "evidencias_positivas": len(positivos),
            "evidencias_negativas": len(negativos),
            "dias_com_evidencia": len(dias_distintos),
            "confirmacoes_usuario": confirmacoes,
            "contexto_compativel": compativel,
            "contexto_evidencia": contexto_evidencia,
            "global": global_,
            "motivos": motivos,
            "excecao_ativa": excecao_ativa,
            "hipotese": hipotese,
        }
