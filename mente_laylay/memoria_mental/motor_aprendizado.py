"""Motor unificado de evidências, hipóteses e revisão da Laylay."""

from __future__ import annotations

import re
import threading
import time
import unicodedata
from datetime import datetime, timedelta
from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.maturidade_aprendizado import (
    MaturidadeAprendizadoRuntime,
)
from mente_laylay.memoria_mental.estado_continuidades import sugestao_pendente_ativa


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFD", str(texto or "").casefold())
    base = "".join(ch for ch in base if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9_ -]+", " ", base)).strip()


class MotorAprendizadoRuntime:
    """Aprende somente de usuário, observação e resultado verificável."""

    def __init__(
        self,
        *,
        memoria_sqlite: Any,
        contexto_getter: Callable[[], Dict[str, Any]],
        agendar_fala: Callable[..., Any] | None = None,
        continuidades_get: Callable[[str, Any], Any] | None = None,
        continuidades_update: Callable[..., Any] | None = None,
        interacao_iniciada: Callable[[], bool] | None = None,
        conversa_ativa: Callable[[], bool] | None = None,
        pesquisar_conhecimento: Callable[[str], Dict[str, Any]] | None = None,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.memoria = memoria_sqlite
        self.contexto_getter = contexto_getter
        self.agendar_fala = agendar_fala
        self.continuidades_get = continuidades_get
        self.continuidades_update = continuidades_update
        self.interacao_iniciada = interacao_iniciada or (lambda: True)
        self.conversa_ativa = conversa_ativa or (lambda: False)
        self.pesquisar_conhecimento = pesquisar_conhecimento
        self.log = log
        self._lock = threading.RLock()
        self._acoes_recentes: list[dict[str, Any]] = []
        self._resultados_recentes: list[tuple[float, tuple[Any, ...]]] = []
        self._curiosidade_em_andamento = False
        self.maturidade = MaturidadeAprendizadoRuntime(
            memoria_sqlite=self.memoria,
            contexto_getter=self._contexto,
        )

    def _contexto(self) -> Dict[str, Any]:
        try:
            bruto = dict(self.contexto_getter() or {})
        except Exception:
            bruto = {}
        temporal = bruto.get("ritmo_temporal") if isinstance(bruto.get("ritmo_temporal"), dict) else {}
        return {
            "periodo": temporal.get("periodo") or bruto.get("periodo") or "",
            "fase": temporal.get("fase") or "",
            "hora": temporal.get("hora") or bruto.get("hora_chave") or "",
            "assunto": str(bruto.get("assunto") or "")[:80],
            "aplicativo": str(bruto.get("exe") or "")[:80],
            "atividade": str(
                bruto.get("atividade") or bruto.get("tipo_atividade")
                or bruto.get("assunto") or ""
            )[:80],
        }

    @staticmethod
    def _assinatura_contexto(contexto: Dict[str, Any] | None, *, global_: bool = False) -> str:
        if global_:
            return "global"
        dados = dict(contexto or {})
        partes = (
            _normalizar(dados.get("periodo"))[:24],
            _normalizar(dados.get("atividade") or dados.get("assunto"))[:40],
            _normalizar(dados.get("aplicativo") or dados.get("exe"))[:40],
        )
        return "-".join(parte or "qualquer" for parte in partes)

    def _variantes_preferencia(self, chave_base: str) -> list[Dict[str, Any]]:
        try:
            hipoteses = self.memoria.listar_hipoteses_aprendizado(limit=500)
        except Exception:
            return []
        prefixos = (f"{chave_base}:contexto:", f"{chave_base}:revisao:")
        return [
            item for item in hipoteses
            if str(item.get("chave") or "") == chave_base
            or str(item.get("chave") or "").startswith(prefixos)
        ]

    def _contexto_hipotese(self, chave: str) -> Dict[str, Any]:
        try:
            eventos = self.memoria.listar_eventos_aprendizado(chave, limit=20)
        except Exception:
            return {}
        positivo = next((item for item in eventos if float(item.get("sinal") or 0.0) > 0), {})
        return dict(positivo.get("contexto") or {}) if isinstance(positivo.get("contexto"), dict) else {}

    def registrar_evidencia(
        self,
        *,
        chave: str,
        tipo: str,
        valor: Any,
        sinal: float,
        origem: str,
        evidencia: str = "",
        escopo: str = "geral",
        confirmado_usuario: bool = False,
        contexto: Dict[str, Any] | None = None,
    ) -> Dict[str, Any] | None:
        if _normalizar(origem) in {"ia", "assistente", "resposta ia", "fala ia"}:
            return None
        try:
            hipotese = self.memoria.registrar_evidencia_aprendizado(
                chave=str(chave or "").strip(), tipo=tipo, escopo=escopo,
                valor=valor, sinal=sinal, origem=origem, evidencia=evidencia,
                contexto=contexto or self._contexto(),
                confirmado_usuario=confirmado_usuario,
            )
        except Exception as erro:
            self.log(f"⚠️ [APRENDIZADO] evidência não persistida: {erro}")
            return None
        if hipotese:
            self.log(
                "🧠 [APRENDIZADO] "
                f"chave={hipotese.get('chave')} | confiança={float(hipotese.get('confianca') or 0):.2f} | "
                f"status={hipotese.get('status')} | contradições={hipotese.get('contradicoes')}"
            )
        return hipotese

    def registrar_contraproposta(self, chave: str, registro: Dict[str, Any]) -> Dict[str, Any] | None:
        dados = dict(registro or {})
        evidencia = str(dados.get("evidencia") or "")
        contexto = self._contexto()
        contexto["global"] = bool(re.search(
            r"\b(?:sempre|toda vez|de agora em diante|em qualquer horario|em qualquer horário)\b",
            _normalizar(evidencia),
        ))
        chave_base = f"preferencia_sugestao:{chave}"
        assinatura_nova = self._assinatura_contexto(contexto, global_=bool(contexto["global"]))
        valor_novo = {
            "alternativa": dados.get("alternativa"),
            "descricao": dados.get("descricao"),
            "descricao_humana": f"prefere {dados.get('descricao') or 'a alternativa ensinada'}",
        }
        variantes = self._variantes_preferencia(chave_base)
        mesma_variante: Dict[str, Any] = {}
        for variante in variantes:
            chave_variante = str(variante.get("chave") or "")
            contexto_variante = self._contexto_hipotese(chave_variante)
            assinatura_variante = self._assinatura_contexto(
                contexto_variante,
                global_=bool(contexto_variante.get("global")),
            )
            if assinatura_variante != assinatura_nova:
                continue
            if variante.get("valor") == valor_novo:
                mesma_variante = variante
                break
            avaliacao = self.avaliar_hipotese(chave_variante, contexto=contexto)
            if avaliacao.get("nivel") in {"confirmada", "provavel"}:
                existente = variante.get("valor") if isinstance(variante.get("valor"), dict) else {}
                return {
                    "conflito": True,
                    "status": "aguardando_confirmacao",
                    # Campos de compatibilidade descrevem a proposta detectada,
                    # sem fingir que ela já substituiu o valor persistido.
                    "valor": valor_novo,
                    "contradicoes": int(variante.get("contradicoes") or 0) + 1,
                    "chave_base": chave_base,
                    "chave_existente": chave_variante,
                    "preferencia_existente": existente,
                    "registro_proposto": dados,
                    "contexto": contexto,
                    "assinatura_contexto": assinatura_nova,
                    "pergunta": (
                        f"Nesse contexto você tinha me ensinado a preferir "
                        f"{existente.get('descricao') or 'a opção anterior'}, mas agora escolheu "
                        f"{dados.get('descricao') or 'outra opção'}. Quer substituir a preferência anterior?"
                    ),
                }

        if mesma_variante:
            chave_destino = str(mesma_variante.get("chave") or chave_base)
        elif not variantes:
            chave_destino = chave_base
        else:
            chave_destino = f"{chave_base}:contexto:{assinatura_nova}"
        return self.registrar_evidencia(
            chave=chave_destino, tipo="preferencia_contextual",
            escopo=str(chave or "sugestao"),
            valor=valor_novo,
            sinal=1.0, origem="contraproposta_usuario",
            evidencia=evidencia, confirmado_usuario=True, contexto=contexto,
        )

    def selecionar_preferencia_sugestao(
        self, chave: str, *, contexto: Dict[str, Any] | None = None,
    ) -> Dict[str, Any] | None:
        chave_base = f"preferencia_sugestao:{str(chave or '').strip()}"
        candidatas = []
        for item in self._variantes_preferencia(chave_base):
            avaliacao = self.avaliar_hipotese(str(item.get("chave") or ""), contexto=contexto)
            if not avaliacao.get("aplicavel"):
                continue
            especifica = not bool(avaliacao.get("global"))
            candidatas.append((
                float(avaliacao.get("confianca_efetiva") or 0.0) + (0.03 if especifica else 0.0),
                item,
                avaliacao,
            ))
        if not candidatas:
            return None
        _, item, avaliacao = max(candidatas, key=lambda candidato: candidato[0])
        valor = dict(item.get("valor") or {}) if isinstance(item.get("valor"), dict) else {}
        return {
            **valor,
            "_aprendizado": {
                "hipotese_chave": str(item.get("chave") or ""),
                "nivel_atual": str(avaliacao.get("nivel") or ""),
                "confianca_atual": float(avaliacao.get("confianca_efetiva") or 0.0),
                "contexto": dict(avaliacao.get("contexto_evidencia") or {}),
            },
            "_maturidade_atual": avaliacao,
        }

    def resolver_conflito_preferencia(
        self, conflito: Dict[str, Any] | None, aceitar_nova: bool,
    ) -> Dict[str, Any] | None:
        dados = dict(conflito or {})
        chave_existente = str(dados.get("chave_existente") or "").strip()
        existente = self.memoria.obter_hipotese_aprendizado(chave_existente) if chave_existente else None
        if not aceitar_nova:
            if not isinstance(existente, dict):
                return None
            return self.registrar_evidencia(
                chave=chave_existente,
                tipo=str(existente.get("tipo") or "preferencia_contextual"),
                escopo=str(existente.get("escopo") or "sugestao"),
                valor=existente.get("valor"), sinal=1.0,
                origem="confirmacao_conflito_usuario", confirmado_usuario=True,
                evidencia="manteve a preferência anterior após conflito",
                contexto=dict(dados.get("contexto") or self._contexto()),
            )
        registro = dict(dados.get("registro_proposto") or {})
        contexto = dict(dados.get("contexto") or self._contexto())
        if chave_existente:
            self.memoria.definir_status_hipotese_aprendizado(chave_existente, "enfraquecida")
        chave_base = str(dados.get("chave_base") or "preferencia_sugestao:geral")
        chave_nova = f"{chave_base}:revisao:{int(time.time() * 1000)}"
        return self.registrar_evidencia(
            chave=chave_nova, tipo="preferencia_contextual",
            escopo=str(chave_base.rsplit(":", 1)[-1] or "sugestao"),
            valor={
                "alternativa": registro.get("alternativa"),
                "descricao": registro.get("descricao"),
                "descricao_humana": f"prefere {registro.get('descricao') or 'a nova alternativa'}",
            },
            sinal=1.0, origem="conflito_confirmado_usuario",
            evidencia=str(registro.get("evidencia") or "substituiu a preferência anterior"),
            confirmado_usuario=True, contexto=contexto,
        )

    def avaliar_hipotese(
        self, chave: str, *, contexto: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        try:
            return self.maturidade.avaliar(chave, contexto=contexto)
        except Exception as erro:
            self.log(f"⚠️ [APRENDIZADO] maturidade não avaliada: {erro}")
            return {
                "chave": chave, "nivel": "indisponivel", "aplicavel": False,
                "confianca_efetiva": 0.0, "motivos": [str(erro)],
            }

    def registrar_excecao_preferencia(self, chave: str, evidencia: str = "") -> Dict[str, Any] | None:
        chave_limpa = str(chave or "").strip()
        hipotese_chave = (
            chave_limpa if chave_limpa.startswith("preferencia_sugestao:")
            else f"preferencia_sugestao:{chave_limpa}"
        )
        try:
            atual = self.memoria.obter_hipotese_aprendizado(hipotese_chave)
        except Exception:
            atual = None
        if not isinstance(atual, dict):
            return None
        contexto = self._contexto()
        assinatura = self._assinatura_contexto(contexto)
        return self.registrar_evidencia(
            chave=f"excecao:{hipotese_chave}:{assinatura}",
            tipo="excecao_preferencia",
            escopo=str(atual.get("escopo") or chave or "sugestao"),
            valor={
                "preferencia_base": hipotese_chave,
                "descricao_humana": "não aplicar a preferência neste contexto",
            },
            sinal=1.0,
            origem="excecao_usuario",
            evidencia=str(evidencia or "recusou a preferência sugerida")[:500],
            confirmado_usuario=True,
            contexto=contexto,
        )

    def registrar_feedback_rotina(self, pendente: Dict[str, Any] | None, aceito: bool) -> None:
        dados = dict(pendente or {})
        app = str(dados.get("app") or "").strip()
        hora = str(dados.get("hora") or "").strip()
        if not app:
            return
        self.registrar_evidencia(
            chave=f"rotina:{hora}:{_normalizar(app)[:60]}", tipo="rotina",
            escopo=f"horario:{hora}",
            valor={"app": app, "hora": hora, "descricao_humana": f"costuma querer abrir {app} às {hora}"},
            sinal=1.0 if aceito else -1.0, origem="feedback_rotina",
            evidencia="aceitou sugestão de rotina" if aceito else "recusou sugestão de rotina",
        )

    def registrar_observacao_rotina(self, janela: str, assunto: str, hora: str) -> None:
        janela = re.sub(r"\s+", " ", str(janela or "").strip())[:100]
        assunto = re.sub(r"\s+", " ", str(assunto or "").strip())[:80]
        hora = str(hora or "").strip()
        if not janela:
            return
        self.registrar_evidencia(
            chave=f"rotina_observada:{hora}:{_normalizar(janela)[:70]}",
            tipo="rotina_observada", escopo=f"horario:{hora}",
            valor={
                "janela": janela, "assunto": assunto, "hora": hora,
                "descricao_humana": f"costuma usar {janela} por volta de {hora}",
            },
            sinal=0.35, origem="observacao_ambiente",
            evidencia=f"janela ativa: {janela}; assunto: {assunto}",
        )

    def registrar_feedback_musical(self, alvo: str, aceito: bool, texto: str = "") -> None:
        alvo = str(alvo or "").strip()
        if not alvo:
            return
        self.registrar_evidencia(
            chave=f"musica:{_normalizar(alvo)[:100]}", tipo="preferencia_musical",
            escopo="musica", valor={"alvo": alvo, "descricao_humana": f"gosta de ouvir {alvo}"},
            sinal=1.0 if aceito else -1.0, origem="feedback_usuario",
            evidencia=texto, confirmado_usuario=bool(re.search(r"\b(?:gosto|adoro|amo|odeio|detesto|prefiro)\b", _normalizar(texto))),
        )

    @staticmethod
    def _assinatura_acao(intent: str, params: Dict[str, Any]) -> tuple[str, str, str]:
        acao = str(params.get("acao") or params.get("modo") or "").strip().lower()
        alvo = str(
            params.get("alvo") or params.get("nome_app") or params.get("query")
            or params.get("nome_playlist") or ""
        ).strip().lower()
        valor = str(params.get("valor") or params.get("nivel_volume") or params.get("value") or "")
        return str(intent or "").upper(), f"{acao}:{alvo}", valor

    def observar_resultado(
        self, resultado: Any, texto: str, executou: bool | None, *, origem: str = "", status: str = ""
    ) -> None:
        if isinstance(resultado, dict):
            intent = str(resultado.get("intent") or resultado.get("acao") or "")
            params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
            confirmado = resultado.get("confirmado")
            status_final = str(status or resultado.get("status") or "")
        else:
            intent = str(getattr(resultado, "intent", "") or getattr(resultado, "acao", ""))
            params = dict(getattr(resultado, "params", {}) or {})
            confirmado = getattr(resultado, "confirmado", None)
            status_final = str(status or getattr(resultado, "status", "") or "")
        if not intent:
            return
        assinatura = self._assinatura_acao(intent, params)
        sucesso = bool(executou is True and confirmado is not False and "falh" not in status_final.casefold())
        agora = time.time()
        dedupe = (assinatura, sucesso, status_final.casefold(), str(texto or "")[:120])
        with self._lock:
            self._resultados_recentes = [
                item for item in self._resultados_recentes if agora - item[0] <= 2.0
            ]
            if any(item[1] == dedupe for item in self._resultados_recentes):
                return
            self._resultados_recentes.append((agora, dedupe))
        chave = f"confiabilidade:{assinatura[0]}:{assinatura[1]}"
        self.registrar_evidencia(
            chave=chave, tipo="resultado_habilidade", escopo=assinatura[0].lower(),
            valor={
                "intent": assinatura[0], "acao_alvo": assinatura[1],
                "descricao_humana": f"a ação {assinatura[0]} em {assinatura[1]} costuma funcionar",
            },
            sinal=0.7 if sucesso else -0.8, origem="executor_confirmado",
            evidencia=str(texto or status_final)[:500],
        )

        with self._lock:
            self._acoes_recentes = [item for item in self._acoes_recentes if agora - item["ts"] <= 180.0]
            anterior = next(
                (
                    item for item in reversed(self._acoes_recentes)
                    if item["assinatura"][:2] == assinatura[:2] and item["assinatura"][2] != assinatura[2]
                ),
                None,
            )
            if anterior and sucesso:
                self.registrar_evidencia(
                    chave=anterior["chave"], tipo="ajuste_revertido", escopo=assinatura[0].lower(),
                    valor=anterior["valor"], sinal=-0.65, origem="reversao_usuario",
                    evidencia="o usuário alterou novamente a ação pouco depois",
                )
            if sucesso:
                self._acoes_recentes.append({
                    "ts": agora, "assinatura": assinatura, "chave": chave,
                    "valor": {"intent": assinatura[0], "acao_alvo": assinatura[1]},
                })

    def observar_texto_usuario(self, texto: str, *, habilidade: str = "", alvo: str = "") -> None:
        t = _normalizar(texto)
        if not t:
            return
        positivo = bool(re.search(r"\b(?:gostei|curti|adorei|amo|gosto)\b", t))
        negativo = bool(re.search(r"\b(?:nao gostei|nao curto|nao gosto|odeio|detesto)\b", t))
        if (positivo or negativo) and (habilidade == "musica" or alvo):
            self.registrar_feedback_musical(alvo or t[:80], positivo and not negativo, texto)

    def observar_interacao(
        self, texto_usuario: str, resposta_ia: str, *, habilidade: str = "", alvo: str = ""
    ) -> None:
        self.observar_texto_usuario(texto_usuario, habilidade=habilidade, alvo=alvo)
        resposta = _normalizar(resposta_ia)
        sinais_lacuna = (
            "nao sei", "nao tenho informacao", "nao tenho informacoes",
            "nao consegui verificar", "sem informacao verificada", "nao conheco esse detalhe",
        )
        tema = re.sub(r"\s+", " ", str(texto_usuario or "").strip()).strip(" ?!.:,;")
        sensivel = bool(re.search(r"\b(?:senha|password|token|chave api|cpf|cartao|cartão)\b", _normalizar(tema)))
        if tema and len(tema.split()) <= 18 and not sensivel and any(sinal in resposta for sinal in sinais_lacuna):
            self.registrar_evidencia(
                chave=f"lacuna:{_normalizar(tema)[:140]}", tipo="lacuna_conhecimento",
                escopo="conhecimento", valor={"tema": tema, "descricao_humana": f"ainda precisa aprender sobre {tema}"},
                sinal=0.8, origem="lacuna_detectada", evidencia=resposta_ia[:500],
            )

    def pesquisar_uma_lacuna(self) -> Dict[str, Any]:
        if not callable(self.pesquisar_conhecimento):
            return {"status": "pesquisa_indisponivel"}
        try:
            hipoteses = self.memoria.listar_hipoteses_aprendizado(limit=100)
        except Exception:
            return {"status": "memoria_indisponivel"}
        agora = datetime.now()
        candidata = None
        for item in hipoteses:
            if item.get("tipo") != "lacuna_conhecimento" or item.get("status") in {"enfraquecida", "resolvida"}:
                continue
            try:
                ultima = datetime.fromisoformat(str(item.get("ultima_evidencia_em") or ""))
            except Exception:
                ultima = agora - timedelta(days=2)
            # A primeira lacuna pode ser pesquisada no próximo ciclo; falhas
            # recentes esperam um dia para não martelar serviços externos.
            if int(item.get("evidencias_negativas") or 0) and agora - ultima < timedelta(days=1):
                continue
            candidata = item
            break
        if not candidata:
            return {"status": "sem_lacuna"}
        valor = candidata.get("valor") if isinstance(candidata.get("valor"), dict) else {}
        tema = str(valor.get("tema") or "").strip()
        if not tema:
            return {"status": "tema_vazio"}
        try:
            pesquisa = dict(self.pesquisar_conhecimento(tema) or {})
        except Exception as erro:
            pesquisa = {"ok": False, "erro": str(erro)}
        fonte = str(pesquisa.get("fonte") or "").strip().lower()
        confianca = float(pesquisa.get("confianca") or 0.0)
        confiavel = bool(
            pesquisa.get("ok")
            and pesquisa.get("resumo")
            and ((fonte.startswith("wikipedia_") and confianca >= 0.75) or (fonte == "duckduckgo" and confianca >= 0.82))
        )
        if not confiavel:
            self.registrar_evidencia(
                chave=candidata["chave"], tipo="lacuna_conhecimento", escopo="conhecimento",
                valor=valor, sinal=-0.25, origem="pesquisa_sem_fonte_confiavel",
                evidencia=str(pesquisa.get("motivo") or pesquisa.get("erro") or "nenhuma fonte confiável"),
            )
            return {"status": "nao_verificada", "tema": tema}
        resumo = re.sub(r"\s+", " ", str(pesquisa.get("resumo") or "")).strip()[:700]
        titulo = str(pesquisa.get("titulo") or tema).strip()
        try:
            self.memoria.salvar_aprendizado_semantico(
                tipo="conhecimento", gatilho=tema, valor=titulo,
                regra=resumo, texto_original=tema, confianca=confianca,
                origem=f"pesquisa_autonoma_{fonte}", evidencia=f"fonte={fonte}",
                status="ativo", confirmado_usuario=False,
            )
        except Exception as erro:
            self.log(f"⚠️ [APRENDIZADO] conhecimento verificado não foi salvo: {erro}")
            return {"status": "falha_persistencia", "tema": tema}
        self.registrar_evidencia(
            chave=f"conhecimento:{_normalizar(tema)[:140]}", tipo="conhecimento_verificado",
            escopo="conhecimento", valor={
                "tema": tema, "titulo": titulo, "fonte": fonte,
                "descricao_humana": f"possui conhecimento verificado sobre {titulo}",
            },
            sinal=confianca, origem="pesquisa_verificada", evidencia=f"{fonte}: {resumo[:300]}",
        )
        # Resolve a lacuna sem apagá-la do diário: a evidência negativa reduz
        # sua prioridade, enquanto o conhecimento novo fica em chave própria.
        self.registrar_evidencia(
            chave=candidata["chave"], tipo="lacuna_conhecimento", escopo="conhecimento",
            valor=valor, sinal=-1.0, origem="lacuna_resolvida", evidencia=f"aprendido de {fonte}",
        )
        try:
            self.memoria.definir_status_hipotese_aprendizado(candidata["chave"], "resolvida")
        except Exception:
            pass
        return {"status": "aprendido", "tema": tema, "fonte": fonte}

    def confirmar_hipotese(self, chave: str, aceito: bool) -> Dict[str, Any] | None:
        try:
            return self.memoria.responder_hipotese_aprendizado(chave, aceito)
        except Exception as erro:
            self.log(f"⚠️ [APRENDIZADO] confirmação de hipótese falhou: {erro}")
            return None

    def esquecer_por_prefixo(self, prefixo: str) -> int:
        """Revoga aprendizados de um namespace removido pelo usuário."""
        try:
            return int(self.memoria.esquecer_aprendizado_por_prefixo(prefixo))
        except Exception as erro:
            self.log(f"⚠️ [APRENDIZADO] revogação falhou: {erro}")
            return 0

    def _candidata_curiosidade(self) -> Dict[str, Any] | None:
        try:
            candidatas = self.memoria.listar_hipoteses_aprendizado(status="candidata", limit=30)
        except Exception:
            return None
        agora = datetime.now()
        for item in candidatas:
            if int(item.get("evidencias_positivas") or 0) < 2:
                continue
            confianca = float(item.get("confianca") or 0.0)
            if not 0.58 <= confianca < 0.74:
                continue
            ultima = str(item.get("ultima_pergunta_em") or "")
            if ultima:
                try:
                    if agora - datetime.fromisoformat(ultima) < timedelta(days=7):
                        continue
                except Exception:
                    pass
            valor = item.get("valor") if isinstance(item.get("valor"), dict) else {}
            if str(valor.get("descricao_humana") or "").strip():
                return item
        return None

    def revisar_e_exercitar_curiosidade(self) -> Dict[str, Any]:
        try:
            alteradas = int(self.memoria.revisar_hipoteses_aprendizado())
        except Exception as erro:
            self.log(f"⚠️ [APRENDIZADO] revisão falhou: {erro}")
            alteradas = 0
        pesquisa = self.pesquisar_uma_lacuna()
        if (
            not self.interacao_iniciada() or self.conversa_ativa()
            or not callable(self.agendar_fala) or not callable(self.continuidades_update)
        ):
            return {"revisadas": alteradas, "pesquisa": pesquisa, "curiosidade": "bloqueada"}
        if sugestao_pendente_ativa(self.continuidades_get):
            return {"revisadas": alteradas, "pesquisa": pesquisa, "curiosidade": "outra_pendencia"}
        with self._lock:
            if self._curiosidade_em_andamento:
                return {"revisadas": alteradas, "pesquisa": pesquisa, "curiosidade": "em_andamento"}
            candidata = self._candidata_curiosidade()
            if not candidata:
                return {"revisadas": alteradas, "pesquisa": pesquisa, "curiosidade": "sem_candidata"}
            self._curiosidade_em_andamento = True
        valor = candidata.get("valor") if isinstance(candidata.get("valor"), dict) else {}
        descricao = str(valor.get("descricao_humana") or "esse padrão").strip()
        fala = f"Tenho reparado que você {descricao}. Quer que eu considere isso uma preferência sua?"

        def concluir(entregue: bool, _motivo: str) -> None:
            with self._lock:
                self._curiosidade_em_andamento = False
            if not entregue:
                return
            try:
                self.memoria.marcar_pergunta_hipotese(candidata["chave"])
            except Exception:
                pass
            self.continuidades_update(
                comando_sugerido="LEARN_CONFIRM",
                comando_sugerido_payload={"chave": candidata["chave"], "descricao": descricao},
                comando_sugerido_estado="PENDING_CONFIRM",
                comando_sugerido_ts=time.time(),
                comando_pendente="LEARN_CONFIRM",
                comando_pendente_payload={"chave": candidata["chave"], "descricao": descricao},
            )

        aceito = self.agendar_fala(
            "curiosidade_aprendizado", fala, "curiosa", 1, ao_concluir=concluir,
        )
        if aceito is False:
            with self._lock:
                self._curiosidade_em_andamento = False
        return {"revisadas": alteradas, "pesquisa": pesquisa, "curiosidade": "agendada" if aceito else "adiada"}

    def resumo_para_prompt(self, limit: int = 5) -> str:
        try:
            ativas = self.memoria.listar_hipoteses_aprendizado(status="ativa", limit=limit)
        except Exception:
            return ""
        linhas = []
        for item in ativas:
            avaliacao = self.avaliar_hipotese(str(item.get("chave") or ""))
            if not avaliacao.get("aplicavel"):
                continue
            valor = item.get("valor") if isinstance(item.get("valor"), dict) else {}
            descricao = str(valor.get("descricao_humana") or "").strip()
            if descricao:
                contexto_evidencia = dict(avaliacao.get("contexto_evidencia") or {})
                condicoes = [
                    f"{campo}={contexto_evidencia.get(campo)}"
                    for campo in ("periodo", "atividade", "aplicativo")
                    if contexto_evidencia.get(campo)
                ]
                escopo_contextual = "global" if avaliacao.get("global") else (
                    ", ".join(condicoes) or str(item.get("escopo") or "contextual")
                )
                linhas.append(
                    f"- {descricao} (nível {avaliacao.get('nivel')}, "
                    f"confiança atual {float(avaliacao.get('confianca_efetiva') or 0):.2f}, "
                    f"escopo {escopo_contextual})"
                )
        return "HIPÓTESES APRENDIDAS E CONFIRMADAS:\n" + "\n".join(linhas) if linhas else ""

    def executar(
        self, deve_parar: Callable[[], bool] | None = None,
        intervalo_s: float = 21600.0,
        aguardar_fn: Callable[[float], bool] | None = None,
    ) -> None:
        while not (callable(deve_parar) and deve_parar()):
            self.revisar_e_exercitar_curiosidade()
            espera = max(60.0, float(intervalo_s))
            if callable(aguardar_fn):
                if aguardar_fn(espera):
                    break
            else:
                time.sleep(espera)


def criar_motor_aprendizado_runtime(**kwargs: Any) -> MotorAprendizadoRuntime:
    return MotorAprendizadoRuntime(**kwargs)
