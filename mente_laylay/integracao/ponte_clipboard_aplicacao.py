"""Ponte tipada entre o observador de clipboard e a mente compartilhada."""

from __future__ import annotations

import time
from typing import Any, Callable


class PonteClipboardAplicacaoRuntime:
    """Coordena ofertas do clipboard sem conhecer a raiz da aplicação."""

    def __init__(
        self,
        *,
        pendencias: Any,
        estado_mental_getter: Callable[[], dict[str, Any]],
        estado_mental_atualizar: Callable[..., Any],
        memoria_conversa_getter: Callable[[], list[dict[str, Any]]],
        memoria_conversa_setter: Callable[[list[dict[str, Any]]], Any],
        pendencia_protegida_getter: Callable[[dict[str, Any]], dict[str, Any] | None],
        oferta_deve_ceder: Callable[..., bool],
        texto_tem_comando_explicito: Callable[[str], bool],
        classificar_resposta: Callable[[str], Any],
        classificar_confirmacao: Callable[..., Any],
        area_transferencia: Any,
        caixa_entrada_getter: Callable[[], Any | None],
        falar: Callable[[str, str, int], Any],
        agendar_fala: Callable[..., Any],
        clock: Callable[[], float] = time.time,
        log: Callable[[str], Any] = print,
    ) -> None:
        self._pendencias = pendencias
        self._estado_mental_getter = estado_mental_getter
        self._estado_mental_atualizar = estado_mental_atualizar
        self._memoria_conversa_getter = memoria_conversa_getter
        self._memoria_conversa_setter = memoria_conversa_setter
        self._pendencia_protegida_getter = pendencia_protegida_getter
        self._oferta_deve_ceder = oferta_deve_ceder
        self._texto_tem_comando_explicito = texto_tem_comando_explicito
        self._classificar_resposta = classificar_resposta
        self._classificar_confirmacao = classificar_confirmacao
        self._area_transferencia = area_transferencia
        self._caixa_entrada_getter = caixa_entrada_getter
        self._falar = falar
        self._agendar_fala = agendar_fala
        self._clock = clock
        self._log = log

    def registrar_oferta_entregue(self, oferta: dict[str, Any]) -> None:
        acao = str((oferta or {}).get("acao_sugerida") or "").strip()
        if not acao:
            return
        fala = str((oferta or {}).get("fala") or "").strip()
        if bool((oferta or {}).get("cancelada")):
            atual = self._pendencias.obter()
            if (
                atual
                and atual.get("origem") == "observador_area_transferencia"
                and atual.get("acao") == acao
            ):
                self._pendencias.concluir(
                    str(atual.get("id") or ""), "fala_nao_entregue"
                )
            return
        if not fala:
            return
        pendencia_geral = self._pendencia_protegida_getter(
            self._estado_mental_getter()
        )
        if str((pendencia_geral or {}).get("origem") or "") in {
            "lixeira_laylay", "caixa_entrada_pessoal", "confirmacao_operacional",
        }:
            self._log(
                "📋 [CLIPBOARD:CONTEXTO] oferta bloqueada por confirmação "
                f"protegida | origem={pendencia_geral.get('origem')}"
            )
            return
        pendencia = self._pendencias.registrar(
            origem="observador_area_transferencia",
            acao=acao,
            pergunta=fala,
            referencia=str((oferta or {}).get("assinatura") or ""),
            metadados={
                "tipo": str((oferta or {}).get("tipo") or ""),
                "assinatura_clipboard": str((oferta or {}).get("assinatura") or ""),
            },
            ttl_s=300.0,
        )
        if not pendencia:
            return
        self._estado_mental_atualizar(
            ultima_resposta=fala[:180], ultima_fala_emitida_ts=self._clock(),
        )
        self._log(
            "📋 [CLIPBOARD:CONTEXTO] pendência canônica ativa "
            f"| id={pendencia.get('id')} ação={acao}"
        )
        mensagens = list(self._memoria_conversa_getter() or [])
        ultima = mensagens[-1] if mensagens else {}
        if not (
            isinstance(ultima, dict)
            and str(ultima.get("role") or "") == "assistant"
            and str(ultima.get("content") or "").strip() == fala
        ):
            mensagens.append({"role": "assistant", "content": fala})
            self._memoria_conversa_setter(mensagens)

    def processar_oferta_pendente(self, texto: str) -> bool:
        atual = self._pendencias.obter()
        if str((atual or {}).get("origem") or "") != "observador_area_transferencia":
            return False
        acao_atual = str((atual or {}).get("acao") or "")
        if self._oferta_deve_ceder(
            texto,
            acao_atual,
            texto_tem_comando_explicito=self._texto_tem_comando_explicito,
        ):
            self._pendencias.concluir(
                str((atual or {}).get("id") or ""), "substituida_por_novo_comando"
            )
            self._log(
                "📋 [CLIPBOARD:CONTEXTO] oferta opcional encerrada; "
                "novo comando manteve a prioridade"
            )
            return False
        resolucao = self._pendencias.resolver(
            texto,
            classificar_dominio=self._classificar_resposta,
            classificar_contextual=self._classificar_confirmacao,
        )
        if not resolucao.get("tratado"):
            return False
        status = str(resolucao.get("status") or "")
        pendencia = dict(resolucao.get("pendencia") or {})
        pendencia_id = str(pendencia.get("id") or "")
        if status in {"em_processamento", "concorrente"}:
            self._log(
                f"📋 [CLIPBOARD:CONTEXTO] ação já em processamento | id={pendencia_id}"
            )
            return True
        acao = str(pendencia.get("acao") or "")
        self._log(
            "📋 [CLIPBOARD:CONTEXTO] resposta vinculada "
            f"| id={pendencia_id} ação={acao} | resposta={status}"
        )
        if status == "recusar":
            self._pendencias.concluir(pendencia_id, "recusada")
            estado = dict(self._estado_mental_getter() or {})
            silenciadas = dict(
                estado.get("clipboard_ofertas_silenciadas") or {}
            )
            # Recusar uma oferta é feedback contextual, não uma proibição
            # permanente. Evitamos repetir a mesma categoria por dez minutos,
            # mesmo que outro aplicativo publique uma nova assinatura.
            silenciadas[acao] = float(self._clock()) + 600.0
            self._estado_mental_atualizar(
                clipboard_ofertas_silenciadas=silenciadas,
            )
            self._falar("Tudo bem, deixo quieto.", "calma", 1)
            return True

        esperada = str(
            (pendencia.get("metadados") or {}).get("assinatura_clipboard") or ""
        )
        snapshot = dict(self._area_transferencia.snapshot_passivo() or {})
        if esperada and str(snapshot.get("assinatura") or "") != esperada:
            self._pendencias.concluir(pendencia_id, "conteudo_alterado")
            self._falar(
                "Você copiou outra coisa depois da minha pergunta. Não vou "
                "investigar o conteúdo novo sem te avisar.",
                "calma", 1,
            )
            return True

        pedidos = {
            "investigar_erro": "pesquisa o erro que eu copiei",
            "abrir_link": "abre o link que eu copiei",
            "explicar_codigo": "explica o que eu copiei",
            "resumir_texto": "resume o que eu copiei",
        }
        pedido = pedidos.get(acao)
        if pedido:
            executou = bool(self._area_transferencia.processar(pedido))
        elif acao == "guardar_ideia":
            caixa = self._caixa_entrada_getter()
            processar = getattr(caixa, "processar", None)
            executou = bool(processar("anota a ideia que eu copiei")) if callable(processar) else False
        else:
            executou = False
        self._pendencias.concluir(
            pendencia_id, "concluida" if executou else "falha_execucao"
        )
        if not executou:
            self._falar(
                "Eu entendi que você quis continuar, mas essa ação não ficou "
                "disponível agora.",
                "calma", 1,
            )
        return True

    def encaminhar_oferta(self, evento: dict[str, Any]) -> dict[str, Any]:
        dados = dict(evento or {})
        agendada = bool(self._agendar_fala(
            "assistencia_clipboard",
            str(dados.get("fala") or ""),
            str(dados.get("emocao") or "calma"),
            int(dados.get("nivel") or 1),
            ao_iniciar=dados.get("ao_iniciar"),
            ao_concluir=dados.get("ao_concluir"),
            preservar_ate_entrega=True,
            mesclar_turno=False,
        ))
        return {
            "status": "emitida" if agendada else "nao_emitida",
            "motivo": "fila_assistencia_clipboard" if agendada else "fila_recusou",
            "categoria": str(dados.get("categoria") or "curiosidade"),
            "dominio": str(dados.get("dominio") or "rotina"),
            "ts": self._clock(),
        }


def criar_ponte_clipboard_aplicacao_runtime(
    **kwargs: Any,
) -> PonteClipboardAplicacaoRuntime:
    return PonteClipboardAplicacaoRuntime(**kwargs)
