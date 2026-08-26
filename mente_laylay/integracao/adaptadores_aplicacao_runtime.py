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
from mente_laylay.memoria_mental.resultado_acao import (
    CHAVE_RESULTADO_OPERACIONAL_PUBLICADO,
    normalizar_resultado_acao,
)


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
        # P0_PUBLICACAO_RESULTADO_PRIORITARIO_V1_20260815
        # Vários atalhos prioritários seguem o contrato legado
        # ``executar_intencao(...) -> registrar(dict original)``. Quando o
        # executor moderno já publicou ResultadoAcao, o adaptador marca esse
        # mesmo dict. Nesse caso a segunda chamada é somente fallback e deve
        # ser descartada ANTES de alimentar base, aprendizado, mapa e plano.
        #
        # Um status explícito continua sendo aceito como atualização deliberada;
        # caminhos sem publicação oficial também continuam usando o fallback.
        if (
            isinstance(resultado, dict)
            and resultado.get(CHAVE_RESULTADO_OPERACIONAL_PUBLICADO)
            and not str(status or resultado.get("status") or "").strip()
            and str(origem or "").strip().casefold() != "executor"
        ):
            return
        # A base mental já normaliza o retorno legado, mas o plano do turno
        # era montado abaixo diretamente do dict bruto. Isso criava dois
        # recibos para o mesmo fato: ``resumo_concluido`` ficava confirmado
        # na memória e indeterminado no plano observado pelo caos. Normalize
        # uma vez também para os consumidores do adaptador; a inferência
        # continua restrita à tabela oficial de estados confirmáveis.
        contrato_plano = normalizar_resultado_acao(
            resultado,
            texto=texto,
            executou=executou,
            origem=origem,
            status=status,
        )
        # A identidade pertence ao turno que disparou a ação. Capture-a antes
        # de notificar base, aprendizado e limpadores de contexto: esses
        # consumidores também atualizam a mente compartilhada e não podem
        # trocar o RG do recibo pela proposta operacional já reduzida.
        estado = ns["_estado_compartilhado_runtime"]
        plano = dict(estado.mental.get("plano_turno_atual") or {})
        texto_turno = " ".join(str(texto or "").split()).casefold()
        texto_plano = " ".join(
            str(plano.get("texto_usuario") or "").split()
        ).casefold()
        texto_operacional_plano = " ".join(
            str(plano.get("texto_operacional_efetivo") or "").split()
        ).casefold()
        entrada_atual = str(
            estado.mental.get("ultima_entrada") or ""
        ).strip()
        texto_entrada_atual = " ".join(
            entrada_atual.split()
        ).casefold()
        subetapa_do_plano_atual = bool(
            texto_plano
            and texto_turno
            and (
                texto_turno == texto_plano
                or texto_turno in texto_plano
                or texto_turno == texto_operacional_plano
            )
        )
        subetapa_da_entrada_atual = bool(
            texto_entrada_atual
            and texto_turno
            and (
                texto_turno == texto_entrada_atual
                or texto_turno in texto_entrada_atual
            )
        )
        texto_identidade = (
            str(plano.get("texto_usuario") or "").strip()
            if subetapa_do_plano_atual
            else entrada_atual
            if subetapa_da_entrada_atual
            else str(texto or "").strip()
        )
        texto_identidade_normalizado = (
            texto_plano
            if subetapa_do_plano_atual
            else texto_entrada_atual
            if subetapa_da_entrada_atual
            else texto_turno
        )
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
            intent = contrato_plano.intent
            params = dict(contrato_plano.params)
            status_resultado = contrato_plano.status
            confirmado = contrato_plano.confirmado
            confirmacao_oferecida = contrato_plano.confirmacao_oferecida
            evidencia_confirmacao = contrato_plano.evidencia_confirmacao
            id_solicitacao = contrato_plano.id_solicitacao
            origem_resultado = contrato_plano.origem
            detalhe_resultado = contrato_plano.detalhe
            alvo_objeto = contrato_plano.alvo
            if not intent:
                return
            # Uma acao operacional observada encerra qualquer pergunta casual
            # anterior. Sem esta limpeza, um ``Sim`` enviado depois de apagar
            # uma playlist podia responder a uma pergunta musical de varios
            # turnos atras e reabrir um contexto que ja havia sido superado.
            limpar_pergunta = ns.get("_limpar_pergunta_aberta")
            if callable(limpar_pergunta):
                try:
                    limpar_pergunta()
                except Exception as erro:
                    ns["print"](
                        "⚠️ [CONTEXTO] pergunta anterior não foi limpa: "
                        f"{type(erro).__name__}"
                    )
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
            plano_sem_identidade = bool(
                not plano.get("id")
                and not texto_plano
                and not list(plano.get("comandos") or [])
            )
            plano_obsoleto_com_entrada_comprovada = bool(
                not subetapa_do_plano_atual
                and subetapa_da_entrada_atual
                and texto_plano != texto_identidade_normalizado
            )
            if texto_identidade_normalizado and (
                plano_sem_identidade
                or plano_obsoleto_com_entrada_comprovada
            ):
                # Atalhos prioritários podem executar antes da composição
                # cognitiva criar o plano do novo turno. Anexar o recibo a
                # ``{}`` (ou ao turno anterior) produz uma ação real sem
                # autoria observável e faz a barreira do roteiro esperar até
                # o timeout. O próprio texto recebido pelo executor é a
                # identidade mínima e auditável desse turno; um plano antigo
                # nunca pode absorver a nova ocorrência.
                plano = {
                    "id": time.time_ns(),
                    "origem_entrada": str(origem or "prioritario"),
                    "texto_usuario": texto_identidade[:500],
                    "modalidade": "comando",
                    "ato_principal": "comando",
                    "requer_execucao": True,
                    "autoriza_execucao": True,
                    "fase": "executado",
                    "comandos": [],
                    "erros": [],
                }
            comandos = list(plano.get("comandos") or [])
            # P0_BUG_B_OBSERVABILIDADE_EXECUCOES_V1_20260815
            # Resultado identificado: consolida somente a MESMA ocorrência.
            # Resultado legado sem ID: mantém a deduplicação antiga por intent.
            indice_anterior = None
            if id_solicitacao:
                indice_anterior = next(
                    (
                        indice
                        for indice, item in enumerate(comandos)
                        if str(item.get("id_solicitacao") or "").strip()
                        == id_solicitacao
                    ),
                    None,
                )
                anterior = (
                    dict(comandos[indice_anterior])
                    if indice_anterior is not None
                    else {}
                )
            else:
                anterior = next(
                    (
                        item
                        for item in comandos
                        if not str(item.get("id_solicitacao") or "").strip()
                        and str(item.get("intent") or "").upper()
                        == intent.upper()
                    ),
                    {},
                )
            preservar_resultado_detalhado = bool(
                anterior.get("status") and not status_resultado
            )
            params_anteriores = (
                dict(anterior.get("params") or {})
                if isinstance(anterior.get("params"), dict)
                else {}
            )
            params_registro = dict(params_anteriores)
            params_registro.update(params)
            registro = {
                "id_solicitacao": id_solicitacao,
                "intent": intent.upper(),
                "alvo": alvo or str(anterior.get("alvo") or ""),
                "status": status_resultado or str(anterior.get("status") or ""),
                "params": params_registro,
                "origem": origem_resultado or str(anterior.get("origem") or ""),
                "detalhe": detalhe_resultado or str(anterior.get("detalhe") or ""),
                "executou": (
                    anterior.get("executou") if preservar_resultado_detalhado
                    else executou if executou is not None else anterior.get("executou")
                ),
                "confirmado": (
                    anterior.get("confirmado") if preservar_resultado_detalhado
                    else confirmado if confirmado is not None else anterior.get("confirmado")
                ),
                "confirmacao_oferecida": (
                    confirmacao_oferecida
                    if confirmacao_oferecida not in (None, "")
                    else anterior.get("confirmacao_oferecida")
                ),
                "evidencia_confirmacao": (
                    evidencia_confirmacao
                    if evidencia_confirmacao not in (None, "")
                    else anterior.get("evidencia_confirmacao")
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
            if id_solicitacao:
                if indice_anterior is None:
                    comandos.append(registro)
                else:
                    # Atualiza a mesma execução na posição original.
                    comandos[indice_anterior] = registro
            else:
                # Compatibilidade legada: sem identidade confiável, preserva
                # o comportamento anterior apenas entre registros também sem ID.
                comandos = [
                    item
                    for item in comandos
                    if str(item.get("id_solicitacao") or "").strip()
                    or str(item.get("intent") or "").upper()
                    != intent.upper()
                ]
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
        from mente_laylay.memoria_mental.contexto_integrado import (
            compactar_contexto_integrado_para_prompt,
        )

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
        if motor is not None:
            aprendido = str(motor.resumo_para_prompt() or "").strip()
            if aprendido:
                resumo = f"{resumo}\n{aprendido}" if resumo else aprendido
        return compactar_contexto_integrado_para_prompt(
            resumo,
            texto_usuario=texto_usuario,
            limite_chars=2400,
        )

    def registrar_feedback_rotina(self, aceito: bool) -> None:
        ns = self._ns()
        pendente = ns["_continuidades_get"]("rotina_sugestao_pendente")
        ns["_aprendizado_runtime"].registrar_feedback_rotina(
            aceito,
            cooldown_min=ns["ROTINA_BLOQUEIO_REJEICAO_MIN"],
            limite_rejeicao=ns["ROTINA_BLOQUEIO_REJEICAO_VEZES"],
        )
        ns["_motor_aprendizado_runtime"].registrar_feedback_rotina(pendente, bool(aceito))

    def registrar_feedback_contextual(self, **dados: Any) -> Any:
        motor = self._ns().get("_motor_aprendizado_runtime")
        metodo = getattr(motor, "registrar_feedback_contextual", None)
        if not callable(metodo):
            return None
        return metodo(**dados)

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
        estrutura = estado.validar_estrutura(conexoes={
            "estado_compartilhado": estado,
            "pendencia_runtime": ns.get("_pendencia_acao_runtime"),
            "classificador_confirmacao": ns.get("_classificar_confirmacao_local"),
            "motor_aprendizado": ns.get("_motor_aprendizado_runtime"),
            "aprendizado_runtime": ns.get("_aprendizado_runtime"),
        })
        saude.registrar(
            "estado_compartilhado", "saudavel" if estrutura.get("ok") else "degradado",
            detalhes="dominios conectados" if estrutura.get("ok") else "estrutura incompleta",
            ausentes=[*(estrutura.get("ausentes") or []), *(estrutura.get("invalidos") or [])],
        )
        ns["_chrome_ws_contexto_runtime"].validar_conexoes()
        ns["_contexto_intencao_runtime"].validar_conexoes()
        ns["_ciclo_comandos_runtime"].validar_conexoes()
        servicos = {
            "voz": ("falar_com_lipsync",),
            "memoria": ("carregar_memoria", "salvar_memoria"),
            "gmail": ("_gmail_buscar_nao_lidos", "gmail_daemon"),
            "navegador": ("run_ws_server_in_thread",),
        }
        for modulo, dependencias in servicos.items():
            saude.validar_dependencias(modulo, ns, dependencias, callables=dependencias)
        modelo_llm = ns.get("_registro_modelo_llm_runtime")
        diagnostico_llm = {}
        try:
            diagnostico_llm = dict(modelo_llm.diagnostico() or {})
        except Exception:
            diagnostico_llm = {}
        llm_disponivel = bool(
            callable(getattr(modelo_llm, "enviar", None))
            and diagnostico_llm.get("disponivel")
        )
        saude.registrar(
            "llm",
            "saudavel" if llm_disponivel else "degradado",
            detalhes=(
                "contrato tipado conectado"
                if llm_disponivel else "contrato tipado indisponível"
            ),
            ausentes=[] if llm_disponivel else ["modelo_llm"],
        )
        navegador_leitura = ns.get("_registro_navegador_leitura_runtime")
        navegador_operacoes = ns.get("_registro_navegador_operacoes_runtime")
        try:
            diag_navegador_leitura = dict(navegador_leitura.diagnostico() or {})
            diag_navegador_operacoes = dict(navegador_operacoes.diagnostico() or {})
        except Exception:
            diag_navegador_leitura = {}
            diag_navegador_operacoes = {}
        navegador_contrato = bool(
            diag_navegador_leitura.get("leitura_aba_disponivel")
            and diag_navegador_leitura.get("listagem_disponivel")
            and diag_navegador_operacoes.get("comandos_disponiveis")
            and diag_navegador_operacoes.get("navegacao_disponivel")
        )
        navegador_conectado = bool(diag_navegador_leitura.get("conectado"))
        navegador_disponivel = navegador_contrato and navegador_conectado
        navegador_status = (
            "saudavel" if navegador_disponivel
            else "degradado" if navegador_contrato
            else "indisponivel"
        )
        navegador_ausentes = []
        if not navegador_contrato:
            navegador_ausentes.append("contrato_navegador")
        if navegador_contrato and not navegador_conectado:
            navegador_ausentes.append("chrome_ws_conectado")
        saude.registrar(
            "navegador",
            navegador_status,
            detalhes=(
                "contrato e conexão observados"
                if navegador_disponivel else "disponibilidade operacional limitada"
            ),
            ausentes=navegador_ausentes,
        )
        # Nome legado preservado como espelho, sempre vindo da mesma fonte viva.
        saude.registrar(
            "navegador_tipado", navegador_status,
            detalhes="espelho da saúde operacional do navegador",
            ausentes=navegador_ausentes,
        )

        iot = ns.get("_registro_iot_runtime") or self._iot
        try:
            diagnostico_iot = dict(iot.diagnostico() or {})
        except Exception:
            diagnostico_iot = {}
        iot_disponivel = bool(
            diagnostico_iot.get("configurado")
            and diagnostico_iot.get("provedor_disponivel")
            and int(diagnostico_iot.get("total_dispositivos") or 0) > 0
        )
        saude.registrar(
            "iot", "saudavel" if iot_disponivel else "indisponivel",
            detalhes=(
                "configuração, provedor e dispositivos observados"
                if iot_disponivel else "pré-condições IoT incompletas"
            ),
            ausentes=[] if iot_disponivel else ["configuracao_ou_provedor_iot"],
        )

        diagnosticos_simples = {
            "area_transferencia": (
                ns.get("_area_transferencia_runtime"), "leitura_disponivel",
                "leitor_clipboard",
            ),
            "caixa_entrada": (
                ns.get("_caixa_entrada_pessoal_runtime"),
                "persistencia_disponivel", "persistencia_caixa",
            ),
            "central_notificacoes": (
                ns.get("_central_notificacoes_runtime"),
                "persistencia_disponivel", "persistencia_notificacoes",
            ),
        }
        for modulo, (runtime, chave, ausente) in diagnosticos_simples.items():
            try:
                retrato = dict(runtime.diagnostico() or {})
            except Exception:
                retrato = {}
            disponivel = bool(retrato.get(chave))
            saude.registrar(
                modulo, "saudavel" if disponivel else "degradado",
                detalhes="pré-condições observadas" if disponivel else "retrato operacional incompleto",
                ausentes=[] if disponivel else [ausente],
            )

        avatar = ns.get("_avatar_runtime")
        try:
            diagnostico_avatar = dict(avatar.diagnostico() or {})
        except Exception:
            diagnostico_avatar = {}
        avatar_preferido = bool(diagnostico_avatar.get("preferencia_ativa"))
        avatar_pronto = bool(
            avatar_preferido
            and diagnostico_avatar.get("assets_disponiveis")
            and (
                diagnostico_avatar.get("processo_ativo")
                or diagnostico_avatar.get("visual_externo_ativo")
            )
        )
        saude.registrar(
            "avatar",
            "saudavel" if avatar_pronto else "degradado" if avatar_preferido else "indisponivel",
            detalhes=(
                "visual observado" if avatar_pronto
                else "preferência desativada" if not avatar_preferido
                else "visual configurado sem processo ativo"
            ),
            ausentes=(
                [] if avatar_pronto
                else ["preferencia_avatar_ativa"] if not avatar_preferido
                else ["processo_ou_widget_avatar"]
            ),
        )
        agenda = ns.get("_agenda_runtime")
        diagnostico_agenda = {}
        try:
            diagnostico_agenda = dict(agenda.diagnostico() or {}) if agenda is not None else {}
        except Exception:
            diagnostico_agenda = {"disponivel": False, "falhas_persistencia": 1}
        agenda_disponivel = bool(diagnostico_agenda.get("disponivel"))
        saude.registrar(
            "agenda",
            "saudavel" if agenda_disponivel else "degradado",
            detalhes=(
                "persistência e daemon da agenda observáveis"
                if agenda_disponivel else "persistência da agenda sem confirmação"
            ),
            ausentes=[] if agenda_disponivel else ["persistencia_agenda"],
        )
        ns["print"](saude.resumo_terminal())


def criar_adaptadores_aplicacao_runtime(
    namespace_getter: Callable[[], Mapping[str, Any]],
) -> AdaptadoresAplicacaoRuntime:
    return AdaptadoresAplicacaoRuntime(namespace_getter)
