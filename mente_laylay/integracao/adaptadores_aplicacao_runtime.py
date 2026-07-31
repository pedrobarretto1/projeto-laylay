"""Adaptadores entre a composição da aplicação e os subsistemas da mente.

Este módulo concentra integrações que antes viviam como funções globais em
``laylay.py``. O namespace é consultado somente no momento da chamada para
preservar a inicialização tardia dos runtimes sem criar imports circulares.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping

from mente_laylay.integracao.registro_memoria_pessoas import PortaMemoriaPessoas
from mente_laylay.integracao.registro_iot import PortaIoT


class AdaptadoresAplicacaoRuntime:
    def __init__(self, namespace_getter: Callable[[], Mapping[str, Any]]) -> None:
        self._namespace_getter = namespace_getter
        self._memoria_pessoas: PortaMemoriaPessoas | None = None
        self._iot: PortaIoT | None = None

    def conectar_memoria_pessoas(
        self, memoria_pessoas: PortaMemoriaPessoas,
    ) -> None:
        """Recebe a dependência tipada depois da inicialização tardia."""
        self._memoria_pessoas = memoria_pessoas

    def conectar_iot(self, iot: PortaIoT) -> None:
        self._iot = iot

    def _ns(self) -> Mapping[str, Any]:
        return self._namespace_getter()

    def registrar_mente_curta(
        self,
        texto_usuario: str = "",
        resposta_ia: str = "",
        intencao: str = "",
        alvo: str = "",
        escopo: str = "",
        habilidade: str = "",
    ) -> None:
        ns = self._ns()
        ns["_registrar_mente_curta_base"](
            texto_usuario, resposta_ia, intencao, alvo, escopo, habilidade,
        )
        motor = ns.get("_motor_aprendizado_runtime")
        if motor is not None and texto_usuario:
            try:
                motor.observar_interacao(
                    texto_usuario, resposta_ia, habilidade=habilidade, alvo=alvo,
                )
            except Exception as erro:
                ns["print"](f"⚠️ [APRENDIZADO] observação textual ignorada: {erro}")
        rede = ns.get("_rede_associativa_runtime")
        if rede is not None:
            try:
                rede.observar_interacao(
                    intencao=intencao,
                    alvo=alvo,
                    escopo=escopo,
                    habilidade=habilidade,
                )
            except Exception as erro:
                # A rede é complementar: uma falha nunca interrompe conversa.
                ns["print"](
                    f"⚠️ [REDE ASSOCIATIVA] observação isolada: {type(erro).__name__}"
                )

    def registrar_resultado_execucao(
        self,
        resultado=None,
        texto: str = "",
        executou=None,
        *,
        origem: str = "",
        status: str = "",
    ) -> None:
        ns = self._ns()
        ns["_registrar_resultado_execucao_base"](
            resultado, texto, executou, origem=origem, status=status,
        )
        motor = ns.get("_motor_aprendizado_runtime")
        if motor is not None:
            try:
                motor.observar_resultado(resultado, texto, executou, origem=origem, status=status)
            except Exception as erro:
                ns["print"](f"⚠️ [APRENDIZADO] resultado não observado: {erro}")
        mapa_habilidades = ns.get("_mapa_habilidades_runtime")
        if mapa_habilidades is not None:
            try:
                mapa_habilidades.registrar_resultado(
                    resultado,
                    status=status,
                    executou=executou,
                )
            except Exception as erro:
                ns["print"](
                    f"⚠️ [HABILIDADES] resultado não refletido no mapa: {type(erro).__name__}"
                )
        try:
            if isinstance(resultado, dict):
                intent = str(resultado.get("intent") or resultado.get("acao") or "").strip()
                params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
                status_resultado = str(status or resultado.get("status") or "").strip()
                confirmado = resultado.get("confirmado")
                alvo_objeto = ""
            else:
                intent = str(getattr(resultado, "intent", "") or getattr(resultado, "acao", "")).strip()
                params = dict(getattr(resultado, "params", {}) or {})
                status_resultado = str(status or getattr(resultado, "status", "") or "").strip()
                confirmado = getattr(resultado, "confirmado", None)
                alvo_objeto = str(getattr(resultado, "alvo", "") or "")
            if not intent:
                return
            suspender_topico = ns.get("_suspender_topico_conversacional")
            if callable(suspender_topico):
                try:
                    suspender_topico("acao_operacional_executada")
                except Exception as erro:
                    ns["print"](
                        f"⚠️ [CONTEXTO] não consegui suspender o assunto anterior: {type(erro).__name__}"
                    )
            alvo = str(
                alvo_objeto
                or params.get("alvo")
                or params.get("nome_app")
                or params.get("nome_playlist")
                or params.get("local")
                or params.get("query")
                or ""
            ).strip()
            estado = ns["_estado_compartilhado_runtime"]
            plano = dict(estado.mental.get("plano_turno_atual") or {})
            comandos = list(plano.get("comandos") or [])
            anterior = next(
                (item for item in comandos if str(item.get("intent") or "").upper() == intent.upper()),
                {},
            )
            preservar_resultado_detalhado = bool(
                anterior.get("status") and not status_resultado
            )
            registro = {
                "intent": intent.upper(),
                "alvo": alvo or str(anterior.get("alvo") or ""),
                "status": status_resultado or str(anterior.get("status") or ""),
                "executou": (
                    anterior.get("executou") if preservar_resultado_detalhado
                    else executou if executou is not None else anterior.get("executou")
                ),
                "confirmado": (
                    anterior.get("confirmado") if preservar_resultado_detalhado
                    else confirmado if confirmado is not None else anterior.get("confirmado")
                ),
            }
            rede = ns.get("_rede_associativa_runtime")
            if rede is not None:
                try:
                    rede.observar_resultado(
                        intencao=intent,
                        alvo=registro["alvo"],
                        status=registro["status"],
                        executou=registro["executou"],
                        confirmado=registro["confirmado"],
                    )
                except Exception as erro_rede:
                    ns["print"](
                        "⚠️ [REDE ASSOCIATIVA] resultado isolado: "
                        f"{type(erro_rede).__name__}"
                    )
            comandos = [item for item in comandos if str(item.get("intent") or "").upper() != intent.upper()]
            comandos.append(registro)
            novo = ns["_atualizar_plano_turno_mente"](
                plano,
                fase=str(plano.get("fase") or "executado"),
                comandos=comandos,
                erros=plano.get("erros") or (),
                fala=str(plano.get("fala_planejada") or ""),
            )
            estado.atualizar_campos("mental", plano_turno_atual=novo)
            mente_atual = dict(estado.mental)
            correcao = ns["_concluir_correcao_interpretacao_mente"](
                mente_atual.get("correcao_interpretacao_pendente")
                if isinstance(mente_atual.get("correcao_interpretacao_pendente"), dict)
                else {},
                intent_correta=intent,
                alvo_correto=alvo,
                texto_execucao=texto,
            )
            if correcao.get("status") == "confirmada_por_execucao":
                historico = list(mente_atual.get("historico_correcoes_interpretacao") or [])[-29:]
                historico.append(correcao)
                estado.atualizar_campos(
                    "mental",
                    correcao_interpretacao_pendente={},
                    historico_correcoes_interpretacao=historico,
                )
        except Exception as erro:
            ns["print"](f"⚠️ [PLANO] não consegui anexar resultado real: {erro}")

    def resumo_mente_integrada_para_prompt(self, texto_usuario: str = "") -> str:
        ns = self._ns()
        resumo = ns["_resumo_mente_integrada_para_prompt_base"](texto_usuario)
        memoria_pessoas = self._memoria_pessoas
        pessoas = ""
        if callable(getattr(memoria_pessoas, "contexto_para_prompt", None)):
            try:
                pessoas = str(memoria_pessoas.contexto_para_prompt(texto_usuario) or "").strip()
            except Exception as erro:
                ns["print"](
                    f"⚠️ [MEMÓRIA:PESSOAS] contexto isolado: {type(erro).__name__}"
                )
        if pessoas:
            resumo = f"{resumo}\n{pessoas}" if resumo else pessoas
        motor = ns.get("_motor_aprendizado_runtime")
        if motor is None:
            return resumo
        aprendido = str(motor.resumo_para_prompt() or "").strip()
        return f"{resumo}\n{aprendido}" if aprendido else resumo

    def registrar_feedback_rotina(self, aceito: bool) -> None:
        ns = self._ns()
        pendente = ns["_continuidades_get"]("rotina_sugestao_pendente")
        ns["_aprendizado_runtime"].registrar_feedback_rotina(
            aceito,
            cooldown_min=ns["ROTINA_BLOQUEIO_REJEICAO_MIN"],
            limite_rejeicao=ns["ROTINA_BLOQUEIO_REJEICAO_VEZES"],
        )
        ns["_motor_aprendizado_runtime"].registrar_feedback_rotina(pendente, bool(aceito))

    def registrar_contexto_resumo_pagina(self, registro) -> None:
        ns = self._ns()
        dados = dict(registro or {})
        if not dados:
            return
        dados["ts"] = time.time()
        estado = ns["_estado_compartilhado_runtime"]
        estado.atualizar_campos("mental", ultimo_resumo_pagina=dados)
        referente = str(dados.get("referente") or dados.get("titulo") or "página atual").strip()
        resumo = str(dados.get("resumo") or "").strip()
        if resumo:
            ns["_registrar_mente_curta"](
                "resuma a página atual", resumo,
                intencao="RESUMIR_PAGINA", alvo=referente,
                escopo="pagina", habilidade="resumo_pagina",
            )
            mensagens = list(estado.memoria_conversa.get("messages", []) or [])
            mensagens.extend([
                {"role": "user", "content": "Resuma a página atual."},
                {"role": "assistant", "content": resumo},
            ])
            estado.atualizar_campos("memoria_conversa", messages=mensagens[-30:])
            conversa = dict(estado.conversacional)
            topicos = [
                item for item in list(conversa.get("topicos_conversa_recente") or [])
                if str(item).strip().casefold() != referente.casefold()
            ]
            topicos.append(referente)
            estado.atualizar_campos(
                "conversacional", ultimo_topico_conversa=referente,
                ultimo_topico_ts=time.time(), topicos_conversa_recente=topicos[-8:],
            )
        ns["salvar_memoria"]()

    def pronuncias_aprendidas_voz(self) -> dict[str, str]:
        ns = self._ns()
        mapa: dict[str, str] = {}
        try:
            for item in ns["MEMORIA_SQLITE"].listar_aprendizados_semanticos(limit=300):
                if (
                    str(item.get("tipo") or "").casefold() == "pronuncia"
                    and str(item.get("status") or "") == "ativo"
                    and bool(item.get("confirmado_usuario"))
                ):
                    ouvido = str(item.get("gatilho") or "").strip()
                    correto = str(item.get("valor") or "").strip()
                    if ouvido and correto:
                        mapa[ouvido] = correto
        except Exception as erro:
            ns["print"](f"⚠️ [OUVIDO] Não consegui carregar pronúncias: {erro}")
        return mapa

    def salvar_pronuncia_voz(self, ouvido: str, correto: str) -> bool:
        ns = self._ns()
        try:
            salvo = ns["MEMORIA_SQLITE"].salvar_aprendizado_semantico(
                tipo="pronuncia", gatilho=str(ouvido or "").strip(),
                valor=str(correto or "").strip(),
                regra=f"Na voz do usuário, {ouvido} significa {correto}.",
                texto_original=f"quando eu falar {ouvido}, quero dizer {correto}",
                confianca=0.99, origem="usuario_voz",
                evidencia="ensino explícito de pronúncia", status="ativo",
                confirmado_usuario=True,
            )
            return bool(salvo)
        except Exception as erro:
            ns["print"](f"⚠️ [OUVIDO] Não consegui persistir pronúncia: {erro}")
            return False

    def vocabulario_dinamico_voz(self) -> list[str]:
        ns = self._ns()
        itens = {
            "Laylay", "lâmpada do quarto", "tomada do ventilador", "YouTube",
            "WhatsApp", "FragPunk", "Soulframe", "VS Code", "PyCharm",
            "azul ciano", "roxo pastel", "vermelho", "verde", "brilho",
        }
        itens.update(str(nome).strip() for nome in ns["APPS_MAP"] if str(nome).strip())
        try:
            itens.update(str(nome).strip() for nome in dict(ns["_playlist_runtime"].cache or {}) if str(nome).strip())
        except Exception:
            pass
        try:
            for dispositivo in ns["MEMORIA_SQLITE"].listar_dispositivos_iot(somente_ativos=True):
                for campo in ("nome", "nome_amigavel", "ambiente"):
                    valor = str(dispositivo.get(campo) or "").strip()
                    if valor:
                        itens.add(valor)
        except Exception:
            pass
        itens.update(self.pronuncias_aprendidas_voz().values())
        return sorted(itens, key=lambda valor: (len(valor), valor.casefold()))

    def auditar_saude_mente(self) -> None:
        ns = self._ns()
        estado = ns["_estado_compartilhado_runtime"]
        saude = ns["_saude_mente_runtime"]
        estrutura = estado.validar_estrutura()
        saude.registrar(
            "estado_compartilhado", "saudavel" if estrutura.get("ok") else "degradado",
            detalhes="dominios conectados" if estrutura.get("ok") else "estrutura incompleta",
            ausentes=[*(estrutura.get("ausentes") or []), *(estrutura.get("invalidos") or [])],
        )
        ns["_chrome_ws_contexto_runtime"].validar_conexoes()
        ns["_contexto_intencao_runtime"].validar_conexoes()
        ns["_ciclo_comandos_runtime"].validar_conexoes()
        servicos = {
            "voz": ("falar_com_lipsync",), "llm": ("enviar_mensagem",),
            "memoria": ("carregar_memoria", "salvar_memoria"),
            "gmail": ("_gmail_buscar_nao_lidos", "gmail_daemon"),
            "navegador": ("run_ws_server_in_thread", "enviar_comando_chrome"),
        }
        for modulo, dependencias in servicos.items():
            saude.validar_dependencias(modulo, ns, dependencias, callables=dependencias)
        iot_disponivel = callable(getattr(self._iot, "executar", None))
        saude.registrar(
            "iot", "saudavel" if iot_disponivel else "indisponivel",
            detalhes="contrato tipado conectado" if iot_disponivel else "contrato ausente",
            ausentes=[] if iot_disponivel else ["servico_iot"],
        )
        ns["print"](saude.resumo_terminal())


def criar_adaptadores_aplicacao_runtime(
    namespace_getter: Callable[[], Mapping[str, Any]],
) -> AdaptadoresAplicacaoRuntime:
    return AdaptadoresAplicacaoRuntime(namespace_getter)
