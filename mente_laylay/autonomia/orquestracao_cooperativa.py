"""Coordenação segura entre habilidades da mente única.

Habilidades publicam evidências e contribuições; somente este coordenador cria
um plano. Percepções não viram ordens, referências sensíveis ficam apenas em
RAM e a execução continua passando pelos porteiros e executores canônicos.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


from mente_laylay.autonomia.quadro_cooperacao import (
    ESTADOS_FINAIS,
    QuadroCooperacaoRuntime,
    _hash_texto,
    _normalizar,
)


from mente_laylay.autonomia.governanca_cooperacao import GovernancaPlanoCooperativoRuntime


from mente_laylay.autonomia.executor_cooperacao import ExecutorPlanoCooperativoRuntime


class OrquestradorCooperativoRuntime:
    """Planeja relações entre habilidades e ativa somente fluxos permitidos."""

    ORIGEM_PENDENCIA = "orquestracao_cooperativa"
    ACAO_SOBRESCREVER = "sobrescrever_arquivo_com_clipboard"

    def __init__(
        self,
        *,
        quadro: QuadroCooperacaoRuntime,
        clipboard_snapshot: Callable[[], Mapping[str, Any]],
        clipboard_getter: Callable[[], str],
        executar_intencao: Callable[[dict[str, Any], str], bool],
        resolver_caminho: Callable[[str], str],
        falar: Callable[[str, str, int], Any],
        marcar_clipboard_consumido: Callable[[Mapping[str, Any]], Any] | None = None,
        planejar_layout: Callable[[], Mapping[str, Any]] | None = None,
        detectar_visao_jogo: Callable[[str], Mapping[str, Any] | None] | None = None,
        estado_getter: Callable[[], Mapping[str, Any]] = lambda: {},
        pendencia_runtime: Any = None,
        classificar_confirmacao_contextual: Callable[[str, str], Any] | None = None,
        registrar_aprendizado: Callable[[Mapping[str, Any], str], Any] | None = None,
        registrar_decisao: Callable[..., Any] | None = None,
        registrar_continuidade: Callable[[Mapping[str, Any], str], Any] | None = None,
        autorizar_acao: Callable[..., Mapping[str, Any]] | None = None,
        executor_plano: ExecutorPlanoCooperativoRuntime | None = None,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.quadro = quadro
        self.clipboard_snapshot = clipboard_snapshot
        self.clipboard_getter = clipboard_getter
        self.marcar_clipboard_consumido = marcar_clipboard_consumido
        self.executar_intencao = executar_intencao
        self.resolver_caminho = resolver_caminho
        self.falar = falar
        self.planejar_layout = planejar_layout
        self.detectar_visao_jogo = detectar_visao_jogo
        self.estado_getter = estado_getter
        self.pendencia_runtime = pendencia_runtime
        self.classificar_confirmacao_contextual = classificar_confirmacao_contextual
        self.registrar_aprendizado = registrar_aprendizado
        self.registrar_decisao = registrar_decisao
        self.log = log
        self.governanca = GovernancaPlanoCooperativoRuntime(
            quadro=quadro,
            autorizar_acao=autorizar_acao,
            registrar_continuidade=registrar_continuidade,
            registrar_aprendizado=registrar_aprendizado,
            registrar_decisao=registrar_decisao,
            log=log,
        )
        self.executor_plano = executor_plano or ExecutorPlanoCooperativoRuntime(
            quadro=quadro, governanca=self.governanca, log=log,
        )

    def registrar_deliberacao_turno(
        self,
        deliberacao: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Publica no quadro a coalizão cognitiva, sem transformar fala em ação.

        O quadro recebe somente metadados e evidências sanitizadas. A presença
        de uma habilidade executora não autoriza execução; os porteiros
        canônicos continuam sendo a única fronteira de efeitos externos.
        """
        dados = dict(deliberacao or {})
        participantes = [
            str(item)[:80] for item in list(dados.get("participantes") or [])
            if str(item).strip()
        ][:8]
        # Conversa + personalidade é o caminho básico de uma única resposta,
        # não uma cooperação que mereça poluir quadro e terminal. Publicamos
        # apenas quando outra habilidade realmente contribuiu para o consenso.
        contribuintes_especializados = set(participantes).difference({
            "conversa", "personalidade",
        })
        if len(participantes) < 2 or not contribuintes_especializados:
            return {}
        evidencias = [
            str(item)[:160]
            for item in list(dados.get("evidencias_compartilhadas") or [])
            if str(item).strip()
        ][:8]
        assinatura = _hash_texto("|".join(sorted(participantes)))[:24]
        evento = self.quadro.publicar_evento(
            origem="deliberador_habilidades",
            tipo="coalizao_cognitiva_formada",
            resumo=f"{len(participantes)} habilidades chegaram a uma conclusão conjunta",
            confianca=max(
                (float(item.get("ativacao") or 0.0) for item in list(dados.get("pareceres") or []) if isinstance(item, Mapping)),
                default=0.0,
            ),
            relevancia=1.0,
            sensibilidade="metadados_locais",
            validade_s=120.0,
            habilidades=participantes,
            evidencias=evidencias,
            chave_deduplicacao=f"coalizao_turno:{assinatura}",
        )
        self.log(
            "🤝 [COOPERAÇÃO:CONSENSO] "
            f"habilidades={','.join(participantes)} | sem_vencedor=True"
        )
        return {
            "evento_id": str(evento.get("id") or ""),
            "participantes": participantes,
            "publicado": True,
            "autoriza_execucao": False,
        }

    def _processar_analise_item_jogo(
        self, pedido: Mapping[str, Any], texto: str,
    ) -> bool:
        params = dict(pedido.get("params") or {})
        jogo = str(params.get("jogo") or "jogo em execução").strip()
        evento = self.quadro.publicar_evento(
            origem="linguagem_natural_jogo",
            tipo="avaliacao_item_solicitada",
            resumo=f"avaliação de item solicitada em {jogo}",
            confianca=0.99,
            relevancia=0.99,
            sensibilidade="local_temporaria",
            validade_s=180.0,
            habilidades=("visao_jogo", "pesquisa_jogos", "memoria_jogos"),
            evidencias=("pedido explícito", "modo jogo ativo"),
            chave_deduplicacao="",
        )
        plano = self.quadro.criar_plano(
            objetivo="identificar e avaliar um item no jogo atual",
            evento_ids=(str(evento.get("id") or ""),),
            etapas=(
                {
                    "id": "ler_item", "ordem": 1,
                    "habilidade": "visao_jogo", "acao": "capturar_e_ler_item",
                    "intent": "GAME_VISION", "estado": "proposto",
                    "orcamento_ms": 60_000, "idempotente": True,
                    "evidencia_esperada": "quadro_atual_lido_sem_inventar_item",
                },
                {
                    "id": "pesquisar_item", "ordem": 2,
                    "habilidade": "pesquisa_jogos", "acao": "enriquecer_item",
                    "depende_de": ["ler_item"], "estado": "proposto",
                    "orcamento_ms": 30_000, "idempotente": True,
                    "politica_falha": "continuar",
                    "evidencia_esperada": "pesquisa_tentada_com_fontes_ou_limite_explicito",
                },
                {
                    "id": "avaliar_build", "ordem": 3,
                    "habilidade": "memoria_jogos", "acao": "cruzar_item_com_perfil",
                    "depende_de": ["pesquisar_item"], "estado": "proposto",
                    "orcamento_ms": 30_000, "idempotente": True,
                    "evidencia_esperada": "parecer_final_contextualizado",
                },
            ),
            confianca=0.99,
            risco="baixo",
            autorizacao="explicita_no_pedido",
            validade_s=180.0,
            orcamento_total_ms=120_000,
            politica_falha_parcial="continuar_independentes",
            metadados={"fluxo": "analise_item_jogo", "jogo": jogo},
        )
        plano_id = str(plano.get("id") or "")
        etapa = next(iter(plano.get("etapas") or []), {})
        autorizacao = self.governanca.avaliar_autorizacao(
            plano, etapa, {"texto": texto, "confirmado": True},
        )
        if not autorizacao.get("permitido"):
            final = self.quadro.atualizar_plano(
                plano_id, "falhou",
                resultado={"status": "autorizacao_negada", "confirmado": False},
            ) or plano
            self.governanca.finalizar(
                final, decisao="falhou", motivo=str(autorizacao.get("motivo") or "autorizacao_negada"),
            )
            self.falar("Não consegui autorizar a leitura do jogo agora.", "calma", 1)
            return True

        self.quadro.atualizar_plano(plano_id, "executando")
        self.quadro.atualizar_etapa(
            plano_id, "ler_item", "executando",
            resultado={"status": "analise_visual_solicitada"},
        )
        self.governanca.registrar_ciclo(plano, "iniciado")
        params["_plano_cooperativo_id"] = plano_id
        tratado = bool(self.executar_intencao({"intent": "GAME_VISION", "params": params}, texto))
        if tratado:
            self.log(
                "🤝 [COOPERAÇÃO] análise de item iniciada | "
                f"id={plano_id} jogo={jogo}"
            )
            return True
        self.registrar_progresso_visao_jogo({
            "plano_id": plano_id, "fase": "falha", "status": "visao_nao_iniciada",
        })
        self.falar("Não consegui iniciar a análise desse item agora.", "calma", 1)
        return True

    def registrar_progresso_visao_jogo(self, evento: Mapping[str, Any]) -> bool:
        """Fecha o plano assíncrono usando apenas evidências sanitizadas da visão."""
        dados = dict(evento or {})
        plano_id = str(dados.get("plano_id") or "")
        fase = str(dados.get("fase") or "").strip().casefold()
        plano = self.quadro.obter_plano(plano_id)
        if not plano or str((plano.get("metadados") or {}).get("fluxo") or "") != "analise_item_jogo":
            return False
        if str(plano.get("estado") or "") in ESTADOS_FINAIS:
            return True
        duracao_ms = max(0, int(dados.get("duracao_ms") or 0))
        status = str(dados.get("status") or fase or "progresso")[:120]
        if fase == "leitura_visual":
            self.quadro.atualizar_etapa(
                plano_id, "ler_item", "confirmado", duracao_ms=duracao_ms,
                resultado={
                    "status": status, "confirmado": True,
                    "evidencia": "quadro_atual_lido_sem_inventar_item",
                },
            )
            self.quadro.atualizar_etapa(
                plano_id, "pesquisar_item", "executando",
                resultado={"status": "enriquecimento_iniciado"},
            )
            return True
        if fase == "pesquisa":
            leitura = next((
                item for item in plano.get("etapas") or []
                if str(item.get("id") or "") == "ler_item"
            ), {})
            if str(leitura.get("estado") or "") != "confirmado":
                return False
            self.quadro.atualizar_etapa(
                plano_id, "pesquisar_item", "confirmado", duracao_ms=duracao_ms,
                resultado={
                    "status": status, "confirmado": True,
                    "evidencia": "pesquisa_tentada_com_fontes_ou_limite_explicito",
                },
            )
            self.quadro.atualizar_etapa(
                plano_id, "avaliar_build", "executando",
                resultado={"status": "contextualizacao_iniciada"},
            )
            return True
        if fase == "parecer_final":
            atual = self.quadro.obter_plano(plano_id) or plano
            pesquisa = next((
                item for item in atual.get("etapas") or []
                if str(item.get("id") or "") == "pesquisar_item"
            ), {})
            if str(pesquisa.get("estado") or "") != "confirmado":
                return False
            self.quadro.atualizar_etapa(
                plano_id, "avaliar_build", "confirmado", duracao_ms=duracao_ms,
                resultado={
                    "status": status, "confirmado": True,
                    "evidencia": "parecer_final_contextualizado",
                },
            )
            final = self.quadro.atualizar_plano(
                plano_id, "confirmado",
                resultado={"status": "parecer_pronto", "confirmado": True},
            ) or atual
            self.governanca.finalizar(final, decisao="aceito", motivo="parecer_pronto")
            self.log(f"🤝 [COOPERAÇÃO] análise de item confirmada | id={plano_id}")
            return True
        if fase == "falha":
            atual = self.quadro.obter_plano(plano_id) or plano
            etapa_atual = next((
                item for item in atual.get("etapas") or []
                if str(item.get("estado") or "") in {"executando", "proposto"}
            ), {})
            if etapa_atual:
                self.quadro.atualizar_etapa(
                    plano_id, str(etapa_atual.get("id") or ""), "falhou",
                    duracao_ms=duracao_ms,
                    resultado={"status": status, "confirmado": False, "motivo": status},
                )
            final = self.quadro.atualizar_plano(
                plano_id, "falhou",
                resultado={"status": status, "confirmado": False},
            ) or atual
            self.governanca.finalizar(final, decisao="falhou", motivo=status)
            return True
        return False

    @staticmethod
    def detectar(texto: str) -> dict[str, Any] | None:
        original = re.sub(r"\s+", " ", str(texto or "")).strip()
        t = _normalizar(original)
        if not t:
            return None
        if re.search(r"^(?:nao|não)\b|\b(?:nao|não)\s+(?:coloca|salva|grava|cria)\b", t):
            return None
        if re.search(
            r"\b(?:como eu faria|talvez|seria legal|seria possivel|se eu pedir|"
            r"voce (?:consegue|pode|sabe))\b",
            t,
        ):
            return None
        organiza_desktop = bool(re.search(
            r"\b(?:organiza|organize|organizar|arruma|arrume|ajeita|ajeite)\b"
            r"[^.!?]{0,60}\b(?:area de trabalho|desktop|janelas|tela)\b",
            t,
        ))
        posicionamento_explicito = bool(re.search(
            r"\b(?:esquerda|direita|lado esquerdo|lado direito)\b",
            t,
        ))
        if organiza_desktop and not posicionamento_explicito:
            return {
                "tipo": "organizacao_desktop_inteligente",
                "confianca": 0.99,
            }
        tem_clipboard = bool(re.search(
            r"\b(?:o que (?:eu )?copiei|texto copiado|conteudo copiado|"
            r"area de transferencia|clipboard)\b",
            t,
        ))
        tem_arquivo = bool(re.search(r"\b(?:arquivo(?: de texto)?|txt|documento de texto)\b", t))
        tem_acao = bool(re.search(
            r"\b(?:coloca|coloque|colocar|salva|salve|salvar|grava|grave|gravar|"
            r"cria|crie|criar|transforma|transforme|transformar)\b",
            t,
        ))
        if not (tem_clipboard and tem_arquivo and tem_acao):
            return None

        pasta = ""
        trecho_nome = ""
        encontrado = re.search(
            r"\b(?:chamado|chamada|com (?:o )?nome|de nome)\s+"
            r"(?P<nome>.+?)(?:\s+dentro\s+(?:da pasta\s+|do diretorio\s+|de\s+)?(?P<pasta>.+))?$",
            original,
            flags=re.IGNORECASE,
        )
        if encontrado:
            trecho_nome = str(encontrado.group("nome") or "")
            pasta = str(encontrado.group("pasta") or "")
        else:
            encontrado = re.search(
                r"\b(?:arquivo(?: de texto)?|txt)\s+(?P<nome>[\w .-]+?)"
                r"(?:\s+(?:com|usando|contendo)\s+(?:o )?(?:texto |conteudo )?(?:que )?(?:eu )?copiei)\b",
                original,
                flags=re.IGNORECASE,
            )
            if encontrado:
                trecho_nome = str(encontrado.group("nome") or "")
        nome = trecho_nome.strip(" .,!?:;\"'")
        pasta = pasta.strip(" .,!?:;\"'")
        if not nome or nome.casefold() in {"arquivo", "texto", "txt", "documento"}:
            return None
        if any(separador in nome for separador in ("/", "\\", ":")) or len(nome) > 120:
            return None
        if not nome.casefold().endswith(".txt"):
            nome = f"{nome}.txt"
        return {
            "tipo": "clipboard_para_arquivo",
            "nome": nome,
            "pasta": pasta,
            "confianca": 0.98,
        }

    def _processar_organizacao_desktop(
        self, intencao: Mapping[str, Any], texto: str,
    ) -> bool:
        if not callable(self.planejar_layout):
            self.falar(
                "Não consegui observar as janelas abertas para montar um layout seguro agora.",
                "calma", 1,
            )
            return True
        try:
            analise = dict(self.planejar_layout() or {})
        except Exception as erro:
            self.log(
                "⚠️ [COOPERAÇÃO:JANELAS] percepção falhou | "
                f"erro={type(erro).__name__}"
            )
            analise = {"ok": False, "status": "falha_percepcao", "prioridades": []}

        prioridades = [
            {
                "titulo": str(item.get("titulo") or "")[:180],
                "pontuacao": float(item.get("pontuacao") or 0.0),
                "motivos": [str(motivo)[:80] for motivo in list(item.get("motivos") or [])[:5]],
            }
            for item in list(analise.get("prioridades") or [])[:5]
            if isinstance(item, Mapping) and str(item.get("titulo") or "").strip()
        ]
        quantidade = max(0, int(analise.get("quantidade") or len(prioridades)))
        assinatura = _hash_texto("|".join(
            str(item.get("titulo") or "") for item in prioridades
        ))
        evento = self.quadro.publicar_evento(
            origem="percepcao_janelas",
            tipo="ambiente_de_trabalho_observado",
            resumo=f"{quantidade} janela(s) organizável(is) observada(s)",
            confianca=float(intencao.get("confianca") or 0.0),
            relevancia=0.97,
            sensibilidade="local_temporaria",
            validade_s=60.0,
            habilidades=("percepcao_janelas", "priorizacao_janelas", "sistema_janelas"),
            evidencias=("janelas visíveis", "foco local", "áudio ativo", "uso recente"),
            chave_deduplicacao=f"layout_janelas:{assinatura}",
        )
        if not analise.get("ok") or not prioridades:
            self._registrar_decisao(
                "falhou", str(analise.get("status") or "sem_janelas_organizaveis"),
                categoria="organizacao_desktop_inteligente",
            )
            self.falar(
                "Não encontrei janelas visíveis suficientes para organizar sem adivinhar.",
                "calma", 1,
            )
            return True

        esquerda = str(analise.get("nome_esquerda") or prioridades[0]["titulo"]).strip()
        direita = str(
            analise.get("nome_direita")
            or (prioridades[1]["titulo"] if len(prioridades) > 1 else "")
        ).strip()
        plano = self.quadro.criar_plano(
            objetivo="organizar a área de trabalho pelas janelas prioritárias",
            evento_ids=(str(evento.get("id") or ""),),
            etapas=(
                {
                    "id": "perceber_janelas", "ordem": 1,
                    "habilidade": "percepcao_janelas", "acao": "observar_janelas_visiveis",
                    "estado": "confirmado", "orcamento_ms": 1_000,
                    "idempotente": True,
                    "evidencia_esperada": "inventario_local_de_janelas_visiveis",
                },
                {
                    "id": "priorizar_janelas", "ordem": 2,
                    "habilidade": "priorizacao_janelas", "acao": "classificar_prioridade",
                    "depende_de": ["perceber_janelas"], "estado": "confirmado",
                    "orcamento_ms": 1_000, "idempotente": True,
                    "evidencia_esperada": "ranking_por_foco_audio_recencia_e_tempo",
                },
                {
                    "id": "aplicar_layout", "ordem": 3,
                    "habilidade": "sistema_janelas", "acao": "aplicar_layout",
                    "intent": "ORGANIZAR_DESKTOP", "depende_de": ["priorizar_janelas"],
                    "estado": "proposto", "orcamento_ms": 5_000,
                    "idempotente": True, "politica_falha": "interromper",
                    "evidencia_esperada": "geometria_final_confirmada",
                },
            ),
            confianca=float(intencao.get("confianca") or 0.0),
            risco="baixo",
            autorizacao="explicita_no_pedido",
            validade_s=60.0,
            orcamento_total_ms=8_000,
            politica_falha_parcial="interromper",
            metadados={
                "fluxo": "organizacao_desktop_inteligente",
                "quantidade_janelas": quantidade,
            },
        )
        plano_id = str(plano.get("id") or "")
        self.log(
            "🤝 [COOPERAÇÃO] plano criado | "
            f"fluxo=organizacao_desktop_inteligente id={plano_id} janelas={quantidade}"
        )

        def aplicar_layout(
            _etapa: Mapping[str, Any], _plano_atual: Mapping[str, Any],
        ) -> Mapping[str, Any]:
            resultado = {
                "intent": "ORGANIZAR_DESKTOP",
                "params": {
                    "left": esquerda,
                    "right": direita,
                    "modo": "automatico_cooperativo",
                    "prioridades_planejadas": prioridades[:2],
                    "plano_cooperativo_id": plano_id,
                },
            }
            tratado = bool(self.executar_intencao(resultado, texto))
            estado = dict(self.estado_getter() or {})
            status = str(estado.get("ultima_acao_status") or "").strip().casefold()
            confirmou = bool(
                tratado
                and str(estado.get("ultima_acao_intent") or "").upper()
                == "ORGANIZAR_DESKTOP"
                and estado.get("ultima_acao_confirmada") is True
                and status == "layout_confirmado"
            )
            return {
                "ok": confirmou,
                "confirmado": confirmou,
                "status": status or "layout_nao_confirmado",
                "evidencia": "geometria_final_confirmada" if confirmou else "",
            }

        self.quadro.atualizar_plano(plano_id, "autorizado")
        resumo = self.executor_plano.executar(
            plano_id,
            {"aplicar_layout": aplicar_layout},
            contexto_execucao={"texto": texto, "confirmado": True},
        )
        if not resumo.get("ok") and str(resumo.get("status") or "") in {
            "autorizacao_negada", "executor_indisponivel", "plano_indisponivel",
        }:
            self.falar(
                "Eu montei o layout, mas a execução segura não foi autorizada.",
                "calma", 1,
            )
        return True

    def _caminho(self, nome: str, pasta: str) -> str:
        if pasta:
            return os.path.join(self.resolver_caminho(pasta), nome)
        return self.resolver_caminho(nome)

    @staticmethod
    def _hash_arquivo(caminho: str) -> str:
        try:
            texto = Path(caminho).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return ""
        return _hash_texto(texto)

    def _aprender(self, plano: Mapping[str, Any], decisao: str) -> None:
        if callable(self.registrar_aprendizado):
            try:
                self.registrar_aprendizado(self.quadro.plano_publico(plano), decisao)
            except Exception:
                pass

    def _registrar_decisao(
        self, decisao: str, motivo: str, *, categoria: str = "clipboard_para_arquivo",
    ) -> None:
        if callable(self.registrar_decisao):
            try:
                self.registrar_decisao(
                    "orquestracao_cooperativa", decisao, (motivo,),
                    categoria=str(categoria or "plano_cooperativo")[:80],
                )
            except Exception:
                pass

    def _consumir_referencia_plano(self, plano: Mapping[str, Any]) -> None:
        metadados = dict(plano.get("metadados") or {})
        self.quadro.consumir_referencia(str(metadados.get("referencia_conteudo") or ""))

    def _executar_plano(self, plano: Mapping[str, Any], texto: str, *, sobrescrever: bool) -> bool:
        plano_id = str(plano.get("id") or "")
        metadados = dict(plano.get("metadados") or {})
        referencia = str(metadados.get("referencia_conteudo") or "")
        hash_conteudo = str(metadados.get("hash_conteudo") or "")
        nome = str(metadados.get("nome") or "")
        pasta = str(metadados.get("pasta") or "")
        def executar_arquivo(
            _etapa: Mapping[str, Any], _plano_atual: Mapping[str, Any],
        ) -> Mapping[str, Any]:
            resolvida = self.quadro.resolver_referencia(
                referencia, hash_esperado=hash_conteudo,
            )
            if not resolvida.get("ok"):
                return {
                    "ok": False,
                    "confirmado": False,
                    "status": str(resolvida.get("status") or "referencia_expirada"),
                    "estado_plano": "expirado",
                }
            resultado = {
                "intent": "CREATE_FILE",
                "params": {
                    "alvo": nome,
                    "pasta": pasta,
                    "tipo_arquivo": "texto",
                    "conteudo_ref": referencia,
                    "conteudo_hash": hash_conteudo,
                    "sobrescrever_confirmado": bool(sobrescrever),
                    "plano_cooperativo_id": plano_id,
                },
            }
            tratado = bool(self.executar_intencao(resultado, texto))
            estado = dict(self.estado_getter() or {})
            status = str(estado.get("ultima_acao_status") or "").strip().casefold()
            confirmou = bool(
                tratado
                and str(estado.get("ultima_acao_intent") or "").upper() == "CREATE_FILE"
                and estado.get("ultima_acao_confirmada") is True
                and status == "arquivo_criado"
            )
            return {
                "ok": confirmou,
                "confirmado": confirmou,
                "status": status or "nao_confirmado",
                "evidencia": "arquivo_existente_e_hash_confirmado" if confirmou else "",
            }

        resumo = self.executor_plano.executar(
            plano_id,
            {"criar_arquivo": executar_arquivo},
            contexto_execucao={"texto": texto, "confirmado": bool(sobrescrever)},
        )
        plano_final = self.quadro.obter_plano(plano_id) or plano
        if resumo.get("ok"):
            self._consumir_referencia_plano(plano_final)
        else:
            status = str(resumo.get("status") or "nao_confirmado")
            if resumo.get("estado") == "expirado":
                self._consumir_referencia_plano(plano_final)
                self.falar(
                    "A referência temporária ao texto expirou. Copie novamente antes de eu criar o arquivo.",
                    "calma", 1,
                )
        return True

    def _processar_pendencia(self, texto: str) -> bool:
        runtime = self.pendencia_runtime
        obter = getattr(runtime, "obter", None)
        resolver = getattr(runtime, "resolver", None)
        concluir = getattr(runtime, "concluir", None)
        pendencia = dict(obter() or {}) if callable(obter) else {}
        if str(pendencia.get("origem") or "") != self.ORIGEM_PENDENCIA:
            return False
        resolucao = dict(resolver(
            texto,
            classificar_contextual=self.classificar_confirmacao_contextual,
        ) or {}) if callable(resolver) else {}
        if not resolucao.get("tratado"):
            return False
        status = str(resolucao.get("status") or "")
        if status in {"em_processamento", "concorrente"}:
            return True
        pendencia = dict(resolucao.get("pendencia") or pendencia)
        pendencia_id = str(pendencia.get("id") or "")
        plano_id = str((pendencia.get("metadados") or {}).get("plano_id") or "")
        plano = self.quadro.obter_plano(plano_id)
        if status == "recusar":
            if callable(concluir):
                concluir(pendencia_id, "recusada")
            if plano:
                plano = self.quadro.solicitar_cancelamento(
                    plano_id, "sobrescrita_recusada",
                ) or plano
                self._consumir_referencia_plano(plano)
                self.governanca.finalizar(
                    plano, decisao="recusado", motivo="sobrescrita_recusada",
                )
            self.falar("Tudo bem. Mantive o arquivo existente exatamente como estava.", "calma", 1)
            return True
        if not plano:
            if callable(concluir):
                concluir(pendencia_id, "plano_expirado")
            self.falar("Esse plano expirou. Faça o pedido novamente para eu usar o conteúdo atual.", "calma", 1)
            return True
        metadados = dict(plano.get("metadados") or {})
        snapshot = dict(self.clipboard_snapshot() or {})
        if str(snapshot.get("assinatura") or "") != str(metadados.get("hash_conteudo") or ""):
            if callable(concluir):
                concluir(pendencia_id, "conteudo_alterado")
            plano_cancelado = self.quadro.atualizar_plano(
                plano_id, "cancelado", resultado={"status": "conteudo_alterado"},
            ) or plano
            self._consumir_referencia_plano(plano)
            self.governanca.finalizar(
                plano_cancelado, decisao="cancelado", motivo="conteudo_alterado",
            )
            self.falar("Você copiou outra coisa depois da confirmação. Não sobrescrevi o arquivo.", "calma", 1)
            return True
        if callable(concluir):
            concluir(pendencia_id, "autorizada")
        self.quadro.atualizar_plano(plano_id, "autorizado")
        return self._executar_plano(plano, texto, sobrescrever=True)

    def processar(self, texto: str) -> bool:
        if self._processar_pendencia(texto):
            return True
        if callable(self.detectar_visao_jogo):
            try:
                pedido_visual = self.detectar_visao_jogo(texto)
            except Exception:
                pedido_visual = None
            if (
                isinstance(pedido_visual, Mapping)
                and str(pedido_visual.get("intent") or "").upper() == "GAME_VISION"
                and str((pedido_visual.get("params") or {}).get("tipo") or "") == "avaliacao_item"
            ):
                return self._processar_analise_item_jogo(pedido_visual, texto)
        intencao = self.detectar(texto)
        if not intencao:
            return False
        if str(intencao.get("tipo") or "") == "organizacao_desktop_inteligente":
            return self._processar_organizacao_desktop(intencao, texto)

        snapshot = dict(self.clipboard_snapshot() or {})
        if snapshot.get("status") != "ok":
            self.falar("Não encontrei um texto disponível na área de transferência.", "calma", 1)
            return True
        if snapshot.get("bloqueado") or str(snapshot.get("tipo") or "") == "sensivel":
            self.falar("O conteúdo copiado parece sensível. Não vou colocá-lo em um arquivo.", "preocupada", 2)
            self._registrar_decisao("bloqueado", "conteúdo sensível")
            return True
        if callable(self.marcar_clipboard_consumido):
            try:
                self.marcar_clipboard_consumido(snapshot)
            except Exception:
                # A deduplicação passiva é auxiliar e nunca pode impedir um
                # pedido explícito de seguir pela rota segura.
                pass
        conteudo = str(self.clipboard_getter() or "")
        assinatura = str(snapshot.get("assinatura") or "")
        if not conteudo or not assinatura or _hash_texto(conteudo) != assinatura:
            self.falar("O conteúdo copiado mudou enquanto eu montava o plano. Copie novamente e repita o pedido.", "calma", 1)
            return True

        referencia = self.quadro.guardar_referencia(
            conteudo, tipo="texto_clipboard", ttl_s=600.0,
        )
        evento = self.quadro.publicar_evento(
            origem="area_transferencia",
            tipo="conteudo_copiado_solicitado",
            resumo="texto copiado destinado a um arquivo local",
            confianca=float(intencao.get("confianca") or 0.0),
            relevancia=0.96,
            sensibilidade="temporaria",
            habilidades=("area_transferencia", "arquivos"),
            evidencias=("referência explícita ao conteúdo copiado", "pedido explícito para criar arquivo"),
            chave_deduplicacao=f"clipboard_arquivo:{assinatura}:{intencao['nome']}",
            referencia=str(referencia.get("token") or ""),
        )
        caminho = self._caminho(str(intencao["nome"]), str(intencao.get("pasta") or ""))
        plano = self.quadro.criar_plano(
            objetivo="salvar conteúdo copiado em arquivo de texto",
            evento_ids=(str(evento.get("id") or ""),),
            etapas=(
                {
                    "ordem": 1, "habilidade": "area_transferencia",
                    "acao": "fornecer_referencia", "estado": "confirmado",
                    "orcamento_ms": 500, "idempotente": True,
                    "evidencia_esperada": "hash_e_tamanho_da_referencia_validos",
                },
                {
                    "ordem": 2, "habilidade": "arquivos", "acao": "criar_arquivo",
                    "intent": "CREATE_FILE",
                    "depende_de": [1], "estado": "proposto", "orcamento_ms": 5_000,
                    "idempotente": True, "politica_falha": "interromper",
                    "evidencia_esperada": "arquivo_existente_e_hash_confirmado",
                },
            ),
            confianca=float(intencao.get("confianca") or 0.0),
            risco="baixo",
            autorizacao="explicita_no_pedido",
            orcamento_total_ms=8_000,
            politica_falha_parcial="interromper",
            metadados={
                "fluxo": "clipboard_para_arquivo",
                "referencia_conteudo": str(referencia.get("token") or ""),
                "hash_conteudo": assinatura,
                "tamanho_conteudo": len(conteudo),
                "nome": str(intencao["nome"]),
                "pasta": str(intencao.get("pasta") or ""),
                "caminho": caminho,
            },
        )
        self.log(
            "🤝 [COOPERAÇÃO] plano criado | fluxo=clipboard_para_arquivo "
            f"id={plano.get('id')} tamanho={len(conteudo)}"
        )

        if os.path.exists(caminho):
            if self._hash_arquivo(caminho) == assinatura:
                plano = self.quadro.atualizar_plano(
                    str(plano.get("id") or ""), "confirmado",
                    resultado={"status": "arquivo_ja_contem_conteudo", "confirmado": True},
                ) or plano
                self.quadro.atualizar_etapa(
                    str(plano.get("id") or ""), "2", "confirmado",
                    resultado={
                        "status": "arquivo_ja_contem_conteudo", "confirmado": True,
                        "evidencia": "arquivo_existente_e_hash_confirmado",
                    },
                )
                self._consumir_referencia_plano(plano)
                self.governanca.finalizar(
                    self.quadro.obter_plano(str(plano.get("id") or "")) or plano,
                    decisao="aceito", motivo="arquivo_ja_contem_conteudo",
                )
                self.falar(f"{intencao['nome']} já contém exatamente o texto copiado. Não precisei alterar nada.", "calma", 1)
                return True
            atual = getattr(self.pendencia_runtime, "obter", lambda: None)()
            if atual:
                plano = self.quadro.atualizar_plano(
                    str(plano.get("id") or ""), "cancelado",
                    resultado={"status": "outra_confirmacao_ativa"},
                ) or plano
                self._consumir_referencia_plano(plano)
                self.governanca.finalizar(
                    plano, decisao="cancelado", motivo="outra_confirmacao_ativa",
                )
                self.falar("Esse arquivo já existe, mas há outra confirmação esperando. Não alterei nada.", "calma", 1)
                return True
            pergunta = f"{intencao['nome']} já existe. Quer substituir pelo texto que está copiado?"
            pendencia = self.pendencia_runtime.registrar(
                origem=self.ORIGEM_PENDENCIA,
                acao=self.ACAO_SOBRESCREVER,
                pergunta=pergunta,
                referencia=str(plano.get("id") or ""),
                metadados={"plano_id": str(plano.get("id") or ""), "arquivo": str(intencao["nome"])},
                ttl_s=300.0,
            ) if self.pendencia_runtime is not None else None
            if pendencia:
                self.quadro.atualizar_plano(str(plano.get("id") or ""), "aguardando_autorizacao")
                self.falar(pergunta, "calma", 1)
            else:
                plano = self.quadro.atualizar_plano(
                    str(plano.get("id") or ""), "cancelado",
                    resultado={"status": "confirmacao_indisponivel"},
                ) or plano
                self._consumir_referencia_plano(plano)
                self.governanca.finalizar(
                    plano, decisao="cancelado", motivo="confirmacao_indisponivel",
                )
                self.falar("O arquivo já existe e eu não consegui abrir uma confirmação segura. Não alterei nada.", "calma", 1)
            return True

        self.quadro.atualizar_plano(str(plano.get("id") or ""), "autorizado")
        return self._executar_plano(plano, texto, sobrescrever=False)

    def resolver_referencia(self, token: str, *, hash_esperado: str = "") -> dict[str, Any]:
        return self.quadro.resolver_referencia(token, hash_esperado=hash_esperado)

    def diagnostico(self) -> dict[str, Any]:
        return self.quadro.diagnostico()


def criar_quadro_cooperacao_runtime(**kwargs: Any) -> QuadroCooperacaoRuntime:
    return QuadroCooperacaoRuntime(**kwargs)


def criar_executor_plano_cooperativo_runtime(**kwargs: Any) -> ExecutorPlanoCooperativoRuntime:
    return ExecutorPlanoCooperativoRuntime(**kwargs)


def criar_orquestrador_cooperativo_runtime(**kwargs: Any) -> OrquestradorCooperativoRuntime:
    return OrquestradorCooperativoRuntime(**kwargs)
