"""Orquestra a fala final e sua continuidade na mente única."""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping

from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala


class OrquestradorFalaRuntime:
    def __init__(self, namespace_getter: Callable[[], Mapping[str, Any]]) -> None:
        self._namespace_getter = namespace_getter

    def _ns(self) -> Mapping[str, Any]:
        return self._namespace_getter()

    def registrar_fala_proativa_emitida(self, texto, itens) -> None:
        ns = self._ns()
        tipos = [
            str(item.get("tipo") or "").strip().lower()
            for item in list(itens or []) if isinstance(item, dict)
        ]
        habilidade = "+".join(dict.fromkeys(tipo for tipo in tipos if tipo)) or "proativa"
        ns["_registrar_mente_curta"](
            "", str(texto or ""), intencao="FALA_PROATIVA",
            alvo="inicialização" if "briefing" in tipos or "abertura" in tipos else habilidade,
            escopo="conversa", habilidade=f"proativa:{habilidade}",
        )

    def finalizar_encerramento_assunto(self) -> None:
        ns = self._ns()
        estado = ns["_estado_compartilhado_runtime"]
        mental = dict(estado.mental)
        if mental.get("encerramento_assunto_pendente") != "topico":
            return
        motivo = str(mental.get("encerramento_assunto_motivo") or "encerrado pelo usuário")
        nova_mente, nova_conversa = ns["_encerrar_topico_mente"](
            mental, dict(estado.conversacional), motivo=motivo,
        )
        estado.substituir("mental", nova_mente)
        estado.substituir("conversacional", nova_conversa)
        ns["salvar_memoria"]()
        ns["print"]("🧠 [CONTEXTO] assunto encerrado; fatos duráveis preservados")

    def falar(
        self,
        texto: str,
        emocao: str = "calma",
        nivel=None,
        wait: bool = False,
        _proativa: bool = False,
    ) -> bool:
        ns = self._ns()
        estado = ns["_estado_compartilhado_runtime"]
        mental_antes = dict(estado.mental)
        plano_antes = dict(mental_antes.get("plano_turno_atual") or {})
        fala = ns["_ajustar_autorreferencia_assistente_mente"](str(texto or ""))
        # Resultados operacionais são validados pelo executor. Nas conversas,
        # toda rota de fala passa por este guardião, inclusive atalhos locais.
        if not plano_antes.get("requer_execucao"):
            guardiao = validar_alegacoes_da_fala(
                fala, plano=plano_antes, origem="canal_voz",
            )
            fala = str(guardiao.get("fala") or fala)
            if guardiao.get("problemas"):
                ns["print"](
                    "🛡️ [GUARDIÃO:FALA] "
                    f"problemas={guardiao.get('problemas') or []}"
                )
        direcao = ns["_dirigir_fala_mente"](
            fala, texto_usuario=str(plano_antes.get("texto_usuario") or ""),
            estado_mental=mental_antes, emocao=emocao, nivel=nivel,
            proativa=_proativa,
        )
        fala = str(direcao.get("fala") or fala)
        emocao = str(direcao.get("emocao") or emocao or "calma")
        nivel = int(direcao.get("nivel") or nivel or 1)
        fala = ns["_sutilizar_referencia_memoria_mente"](fala)
        aceita = ns["_voz_runtime"].falar(
            fala, emocao, nivel, wait=wait, _proativa=_proativa,
        )
        if aceita is not False and not _proativa:
            mental = dict(estado.mental)
            plano = dict(mental.get("plano_turno_atual") or {})
            assunto = str(
                plano.get("dominio") or mental.get("ultimo_alvo")
                or mental.get("foco_conversacional_topico") or ""
            )
            mental["ultima_resposta"] = fala[:500]
            mental["ultima_fala_emitida_ts"] = time.time()
            mental["direcao_fala_atual"] = dict(direcao)
            historico = list(mental.get("historico_direcao_fala") or [])[-39:]
            historico.append(dict(direcao))
            mental["historico_direcao_fala"] = historico
            mental = ns["_registrar_continuidade_da_fala_mente"](
                mental, fala,
                texto_usuario=str(plano.get("texto_usuario") or mental.get("ultima_entrada") or ""),
                assunto=assunto, origem=str(plano.get("dominio") or "fala"),
                emocao=emocao,
            )
            estado.substituir("mental", mental)
            self.finalizar_encerramento_assunto()
        return bool(aceita)

    def entregar_fala_inicial_confirmada(
        self, tipo, texto, emocao="calma", nivel=1,
    ) -> bool:
        ns = self._ns()
        conclusao = ns["_threading"].Event()
        resultado = {"entregue": False, "motivo": "sem_retorno"}

        def ao_concluir(entregue, motivo):
            resultado["entregue"] = bool(entregue)
            resultado["motivo"] = str(motivo or "")
            conclusao.set()

        agendada = ns["_agendar_fala_proativa"](
            tipo, texto, emocao, nivel, ao_concluir=ao_concluir, forcar_inicio=True,
        )
        if not agendada:
            return False
        if not conclusao.wait(45.0):
            ns["print"](f"⚠️ [FALA INICIAL] entrega de {tipo} não foi confirmada em 45s")
            return False
        if not resultado["entregue"]:
            ns["print"](f"⚠️ [FALA INICIAL] {tipo} não entregue: {resultado['motivo']}")
        else:
            estado = ns["_estado_compartilhado_runtime"]
            mental = dict(estado.mental)
            mental["ultima_fala_emitida_ts"] = time.time()
            mental["ultima_resposta"] = str(texto or "").strip()[:500]
            estado.substituir("mental", mental)
        return bool(resultado["entregue"])


def criar_orquestrador_fala_runtime(
    namespace_getter: Callable[[], Mapping[str, Any]],
) -> OrquestradorFalaRuntime:
    return OrquestradorFalaRuntime(namespace_getter)
