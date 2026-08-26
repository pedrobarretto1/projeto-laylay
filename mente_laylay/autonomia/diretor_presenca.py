"""Diretor único para presença espontânea da Laylay.

Sensores podem perceber muitas coisas; este runtime decide se vale interromper o
silêncio. Ele não executa comandos e não substitui o coordenador de
oportunidades. Seu papel é aplicar relevância, orçamento, variedade e segurança
antes de encaminhar uma observação ao restante da mente.
"""

from __future__ import annotations

import re
import threading
import time
import unicodedata
from typing import Any, Callable, Mapping

from mente_laylay.autonomia.governanca_iniciativa import decisao_permite_emissao


PERFIS_COMPANHIA = frozenset({"silencioso", "adaptativo", "presente"})
JANELA_FEEDBACK_PRESENCA_S = 600.0


def _codigo(valor: Any, limite: int = 96) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "").casefold())
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-z0-9 _.:/-]+", "", texto)
    return re.sub(r"\s+", "_", texto).strip("_.:/-")[:limite]


def estado_presenca_inicial() -> dict[str, Any]:
    return {
        "versao": 2,
        "configuracao": {
            "ativo": True,
            "perfil": "adaptativo",
            "motivo_perfil": "inicio",
            "atualizado_ts": 0.0,
        },
        "aprendizado": {"categorias": {}},
        "historico": [],
        "ultima_emissao": {},
        "atividade": {},
        "contadores": {
            "recebidas": 0,
            "emitidas": 0,
            "bloqueadas_contexto": 0,
            "bloqueadas_orcamento": 0,
            "bloqueadas_qualidade": 0,
            "bloqueadas_variedade": 0,
            "feedbacks": 0,
        },
    }


class DiretorPresencaRuntime:
    """Seleciona intervenções curtas sem transformar companhia em spam."""

    COOLDOWN_CATEGORIA = {
        "motivacao": 420.0,
        "celebracao": 300.0,
        "dica": 720.0,
        "musica": 1200.0,
        "companhia": 900.0,
        "curiosidade": 720.0,
    }
    COOLDOWN_JOGO = {
        "motivacao": 300.0,
        "celebracao": 180.0,
        "dica": 480.0,
        "musica": 900.0,
        "companhia": 420.0,
        "curiosidade": 300.0,
    }
    CONFIANCA_MINIMA = {
        "motivacao": 0.74,
        "celebracao": 0.76,
        "dica": 0.88,
        "musica": 0.78,
        "companhia": 0.72,
        "curiosidade": 0.72,
    }

    def __init__(
        self,
        *,
        estado_get: Callable[[], Mapping[str, Any]] = lambda: {},
        estado_set: Callable[[dict[str, Any]], Any] = lambda _estado: None,
        contexto_getter: Callable[[], Mapping[str, Any]] = lambda: {},
        registrar_oportunidade: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        emitir_fala: Callable[[str, str, int], Any] | None = None,
        registrar_feedback: Callable[..., Any] | None = None,
        registrar_falha: Callable[..., Any] | None = None,
        recomendacao_musical: Callable[[str], str] | None = None,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], Any] = time.sleep,
        log: Callable[[str], Any] = print,
        habilitado: bool = True,
        intervalo_ciclo_s: float = 15.0,
        stop_event: threading.Event | None = None,
    ) -> None:
        self.estado_get = estado_get
        self.estado_set = estado_set
        self.contexto_getter = contexto_getter
        self.registrar_oportunidade = registrar_oportunidade
        self.emitir_fala = emitir_fala
        self.registrar_feedback = registrar_feedback
        self.registrar_falha = registrar_falha
        self.recomendacao_musical = recomendacao_musical
        self.clock = clock
        self.sleep = sleep
        self.log = log
        self.habilitado = bool(habilitado)
        self.intervalo_ciclo_s = max(2.0, float(intervalo_ciclo_s))
        self.stop_event = stop_event or threading.Event()
        self._lock = threading.RLock()
        self._running = False

    def _falha(self, codigo: str, erro: BaseException) -> None:
        if callable(self.registrar_falha):
            self.registrar_falha("diretor_presenca", codigo, erro=erro)

    def _estado(self) -> dict[str, Any]:
        try:
            recebido = dict(self.estado_get() or {})
        except Exception as erro:
            self._falha("estado_leitura", erro)
            recebido = {}
        base = estado_presenca_inicial()
        base.update(recebido)
        base["contadores"] = {
            **estado_presenca_inicial()["contadores"],
            **dict(base.get("contadores") or {}),
        }
        base["historico"] = [
            dict(item) for item in list(base.get("historico") or [])[-40:]
            if isinstance(item, Mapping)
        ]
        configuracao = {
            **estado_presenca_inicial()["configuracao"],
            **dict(base.get("configuracao") or {}),
        }
        perfil = str(configuracao.get("perfil") or "adaptativo").casefold()
        configuracao["perfil"] = perfil if perfil in PERFIS_COMPANHIA else "adaptativo"
        configuracao["ativo"] = bool(configuracao.get("ativo", True))
        base["configuracao"] = configuracao
        base["aprendizado"] = {
            "categorias": dict(
                dict(base.get("aprendizado") or {}).get("categorias") or {}
            ),
        }
        return base

    def configuracao_atual(self) -> dict[str, Any]:
        estado = self._estado()
        return dict(estado.get("configuracao") or {})

    def presenca_habilitada(self, _dominio: str = "") -> bool:
        return bool(self.habilitado and self.configuracao_atual().get("ativo", True))

    @staticmethod
    def _pontuacao_categoria(estado: Mapping[str, Any], categoria: str) -> int:
        categorias = dict(dict(estado.get("aprendizado") or {}).get("categorias") or {})
        return int(dict(categorias.get(categoria) or {}).get("pontuacao") or 0)

    def _escolher_perfil(
        self,
        estado: dict[str, Any],
        contexto: Mapping[str, Any],
        categoria: str = "companhia",
    ) -> str:
        """A própria Laylay calibra presença por atividade e feedback acumulado."""
        pontuacao = self._pontuacao_categoria(estado, categoria)
        if pontuacao <= -2:
            perfil, motivo = "silencioso", "feedback_negativo"
        elif contexto.get("modo_foco"):
            perfil, motivo = "silencioso", "concentracao_detectada"
        elif contexto.get("modo_jogo_ativo") and pontuacao >= 1:
            perfil, motivo = "presente", "jogo_com_feedback_positivo"
        else:
            perfil, motivo = "adaptativo", "contexto_neutro"
        config = dict(estado.get("configuracao") or {})
        if config.get("perfil") != perfil or config.get("motivo_perfil") != motivo:
            config.update(
                perfil=perfil,
                motivo_perfil=motivo,
                atualizado_ts=float(self.clock()),
            )
            estado["configuracao"] = config
        return perfil

    def _contexto(self) -> dict[str, Any]:
        try:
            valor = self.contexto_getter() or {}
            return dict(valor) if isinstance(valor, Mapping) else {}
        except Exception as erro:
            self._falha("contexto_leitura", erro)
            return {}

    @staticmethod
    def _evidencias(dados: Mapping[str, Any]) -> list[str]:
        valor = dados.get("evidencias")
        if isinstance(valor, str):
            valor = [valor]
        if not isinstance(valor, (list, tuple, set, frozenset)):
            return []
        return [str(item).strip()[:180] for item in valor if str(item).strip()][:5]

    @staticmethod
    def _incrementar(estado: dict[str, Any], campo: str) -> None:
        contadores = dict(estado.get("contadores") or {})
        contadores[campo] = int(contadores.get(campo) or 0) + 1
        estado["contadores"] = contadores

    def _bloqueio_contextual(self, dados: Mapping[str, Any], contexto: Mapping[str, Any], agora: float) -> str:
        if contexto.get("is_speaking") or contexto.get("turno_ativo"):
            return "fala_ou_turno_em_andamento"
        ultima_entrada = float(contexto.get("ultima_entrada_ts") or 0.0)
        if ultima_entrada and agora - ultima_entrada < 30.0:
            return "usuario_acabou_de_falar"
        dominio = _codigo(dados.get("dominio"), 24)
        categoria = _codigo(dados.get("categoria"), 24)
        if dominio == "jogo" and not contexto.get("modo_jogo_ativo"):
            return "jogo_nao_ativo"
        if dominio == "jogo" and categoria in {
            "dica", "musica", "motivacao", "celebracao", "companhia", "curiosidade",
        }:
            if not bool(dados.get("momento_seguro")):
                return "momento_de_jogo_inseguro"
        return ""

    def _bloqueio_qualidade(self, dados: Mapping[str, Any]) -> str:
        categoria = _codigo(dados.get("categoria"), 24) or "companhia"
        fala = str(dados.get("fala") or "").strip()
        try:
            confianca = float(dados.get("confianca") or 0.0)
        except (TypeError, ValueError):
            confianca = 0.0
        if not fala or len(fala) > 360:
            return "fala_ausente_ou_longa"
        if confianca < self.CONFIANCA_MINIMA.get(categoria, 0.80):
            return "confianca_insuficiente"
        evidencias = self._evidencias(dados)
        if categoria == "dica" and (not dados.get("fundamentada") or len(evidencias) < 2):
            return "dica_sem_duas_evidencias"
        if categoria == "musica" and bool(dados.get("executar_automaticamente")):
            return "musica_nao_pode_autotocar"
        return ""

    def _bloqueio_orcamento(self, estado: Mapping[str, Any], dados: Mapping[str, Any], agora: float) -> str:
        historico = list(estado.get("historico") or [])
        origem = str(dados.get("origem") or "").strip().casefold()
        if origem == "observador_area_transferencia":
            # Copiar algo relevante é uma interação implícita do usuário, não
            # uma dica aleatória da rotina. Ela possui antispam próprio e não
            # disputa o orçamento de comentários espontâneos.
            if any(
                item.get("origem") == origem
                and agora - float(item.get("ts") or 0.0) < 60.0
                for item in historico
            ):
                return "cooldown_area_transferencia"
            return ""
        config = dict(estado.get("configuracao") or {})
        perfil = str(config.get("perfil") or "adaptativo")
        dominio = _codigo(dados.get("dominio"), 24) or "cotidiano"
        if dominio == "jogo" and perfil != "silencioso":
            janela_global = 1200.0
            limite_global = 7 if perfil == "presente" else 5
        else:
            janela_global = 2700.0 if perfil == "silencioso" else 1800.0
            limite_global = 1 if perfil == "silencioso" else 4 if perfil == "presente" else 3
        recentes = [item for item in historico if agora - float(item.get("ts") or 0.0) < janela_global]
        if len(recentes) >= limite_global:
            return "orcamento_global_30m"
        if perfil == "silencioso":
            janela, limite = (1500.0, 1) if dominio == "jogo" else (2700.0, 1)
        elif perfil == "presente":
            janela, limite = (600.0, 4) if dominio == "jogo" else (1200.0, 2)
        else:
            janela, limite = (600.0, 3) if dominio == "jogo" else (1200.0, 1)
        if sum(1 for item in historico if item.get("dominio") == dominio and agora - float(item.get("ts") or 0.0) < janela) >= limite:
            return "orcamento_dominio"
        categoria = _codigo(dados.get("categoria"), 24) or "companhia"
        cooldowns = self.COOLDOWN_JOGO if dominio == "jogo" else self.COOLDOWN_CATEGORIA
        cooldown = cooldowns.get(categoria, 900.0)
        fator = 1.65 if perfil == "silencioso" else 0.75 if perfil == "presente" else 1.0
        aprendido = dict(dict(estado.get("aprendizado") or {}).get("categorias") or {})
        pontuacao = int(dict(aprendido.get(categoria) or {}).get("pontuacao") or 0)
        if pontuacao < 0:
            fator += min(0.75, abs(pontuacao) * 0.15)
        elif pontuacao > 0:
            fator -= min(0.20, pontuacao * 0.05)
        cooldown *= max(0.65, fator)
        if any(item.get("categoria") == categoria and agora - float(item.get("ts") or 0.0) < cooldown for item in historico):
            return "cooldown_categoria"
        return ""

    def considerar(self, evento: Mapping[str, Any] | None) -> dict[str, Any]:
        dados = dict(evento or {})
        agora = float(self.clock())
        with self._lock:
            estado = self._estado()
            self._incrementar(estado, "recebidas")
            if not self.habilitado or not bool(dict(estado.get("configuracao") or {}).get("ativo", True)):
                estado["ultima_decisao"] = {"status": "desabilitado", "ts": agora}
                self.estado_set(estado)
                return dict(estado["ultima_decisao"])

            categoria = _codigo(dados.get("categoria"), 24) or "companhia"
            dominio = _codigo(dados.get("dominio"), 24) or "cotidiano"
            chave = _codigo(dados.get("chave") or dados.get("fala"), 96)
            contexto = self._contexto()
            self._escolher_perfil(estado, contexto, categoria)
            motivo = self._bloqueio_contextual(dados, contexto, agora)
            contador = "bloqueadas_contexto"
            if not motivo:
                motivo = self._bloqueio_qualidade(dados)
                contador = "bloqueadas_qualidade"
            if not motivo:
                motivo = self._bloqueio_orcamento(estado, dados, agora)
                contador = "bloqueadas_orcamento"
            ultima = dict(estado.get("ultima_emissao") or {})
            if not motivo and chave and chave == ultima.get("chave"):
                motivo = "repeticao_semantica"
                contador = "bloqueadas_variedade"
            idade_ultima = agora - float(ultima.get("ts") or 0.0)
            cooldowns_variedade = self.COOLDOWN_JOGO if dominio == "jogo" else self.COOLDOWN_CATEGORIA
            limite_variedade = cooldowns_variedade.get(categoria, 900.0) * 1.10
            if (
                not motivo and ultima.get("categoria") == categoria
                and str(dados.get("origem") or "").casefold() != "observador_area_transferencia"
                and categoria not in {"celebracao"} and idade_ultima < limite_variedade
            ):
                motivo = "categoria_consecutiva"
                contador = "bloqueadas_variedade"
            if motivo:
                self._incrementar(estado, contador)
                decisao = {"status": "bloqueada", "motivo": motivo, "categoria": categoria, "ts": agora}
                estado["ultima_decisao"] = decisao
                self.estado_set(estado)
                if dominio == "jogo":
                    self.log(
                        f"🌙 [PRESENÇA:JOGO] bloqueada | categoria={categoria} "
                        f"| motivo={motivo}"
                    )
                return decisao

            oportunidade = {
                "origem": str(dados.get("origem") or "diretor_presenca"),
                "tipo": f"presenca_{categoria}",
                "dominio": dominio,
                "chave": f"presenca:{dominio}:{categoria}:{chave}",
                "confianca": float(dados.get("confianca") or 0.0),
                "utilidade": int(dados.get("utilidade") or (84 if categoria == "dica" else 68)),
                "risco": "baixo",
                "momento_seguro": bool(dados.get("momento_seguro")),
                "validade_s": float(dados.get("validade_s") or 120.0),
                "tags": [dominio, categoria, *self._evidencias(dados)],
            }
            decisao_iniciativa: Mapping[str, Any] = {}
            if callable(self.registrar_oportunidade):
                try:
                    decisao_iniciativa = self.registrar_oportunidade(oportunidade) or {}
                except Exception as exc:
                    self.log(f"⚠️ [PRESENÇA] coordenador indisponível: {type(exc).__name__}: {exc}")
            if not decisao_permite_emissao(decisao_iniciativa):
                decisao = {"status": "bloqueada", "motivo": "governanca", "categoria": categoria, "ts": agora}
                estado["ultima_decisao"] = decisao
                self.estado_set(estado)
                return decisao

            emocao = str(dados.get("emocao") or ("animada" if categoria in {"motivacao", "celebracao"} else "calma"))
            emitida = False
            if callable(self.emitir_fala):
                try:
                    dados_emissao = {"dominio": dominio, "categoria": categoria}
                    if callable(dados.get("ao_concluir")):
                        dados_emissao["ao_concluir"] = dados.get("ao_concluir")
                    if str(dados.get("origem") or "").casefold() == "observador_area_transferencia":
                        dados_emissao["origem"] = "observador_area_transferencia"
                    emitida = bool(self.emitir_fala(
                        str(dados.get("fala") or "").strip(),
                        emocao,
                        int(dados.get("nivel") or 1),
                        **dados_emissao,
                    ))
                except TypeError:
                    emitida = bool(self.emitir_fala(
                        str(dados.get("fala") or "").strip(),
                        emocao,
                        int(dados.get("nivel") or 1),
                    ))
            if not emitida:
                decisao = {"status": "nao_emitida", "motivo": "fila_de_fala_recusou", "categoria": categoria, "ts": agora}
                estado["ultima_decisao"] = decisao
                self.estado_set(estado)
                return decisao

            registro = {
                "ts": agora,
                "dominio": dominio,
                "categoria": categoria,
                "chave": chave,
                "origem": str(dados.get("origem") or "diretor_presenca").casefold(),
            }
            estado["historico"] = [*list(estado.get("historico") or []), registro][-40:]
            estado["ultima_emissao"] = {**registro, "feedback_registrado": False}
            self._incrementar(estado, "emitidas")
            decisao = {"status": "emitida", "categoria": categoria, "dominio": dominio, "ts": agora}
            estado["ultima_decisao"] = decisao
            self.estado_set(estado)
            self.log(f"✨ [PRESENÇA] dominio={dominio} categoria={categoria} status=emitida")
            return decisao

    def observar_resposta(self, texto: str) -> dict[str, Any]:
        """Aprende com resposta explícita sem consumir nem reinterpretar o turno."""
        fala = _codigo(texto, 180).replace("_", " ")
        if not fala:
            return {}
        agora = float(self.clock())
        with self._lock:
            estado = self._estado()
            ultima = dict(estado.get("ultima_emissao") or {})
            if (
                not ultima or ultima.get("feedback_registrado")
                or agora - float(ultima.get("ts") or 0.0) > JANELA_FEEDBACK_PRESENCA_S
            ):
                return {}
            resultado = ""
            if re.search(r"\b(boa dica|isso ajudou|ajudou bastante|gostei dessa|manda mais|foi util|foi boa)\b", fala):
                resultado = "aceita"
            elif re.search(r"\b(para de comentar|nao precisa comentar|fica quieta|isso e obvio|nao interrompe|sem dica)\b", fala):
                resultado = "recusa"
            elif re.search(r"\b(na verdade|nao e isso|voce entendeu errado|essa dica esta errada)\b", fala):
                resultado = "correcao"
            if not resultado:
                return {}
            ultima["feedback_registrado"] = True
            ultima["feedback"] = resultado
            estado["ultima_emissao"] = ultima
            aprendizado = dict(estado.get("aprendizado") or {})
            categorias = dict(aprendizado.get("categorias") or {})
            categoria = str(ultima.get("categoria") or "companhia")
            registro = dict(categorias.get(categoria) or {})
            delta = 1 if resultado == "aceita" else -2 if resultado == "recusa" else -1
            registro["pontuacao"] = max(-4, min(4, int(registro.get("pontuacao") or 0) + delta))
            registro["ultimo_feedback"] = resultado
            registro["ts"] = agora
            categorias[categoria] = registro
            estado["aprendizado"] = {"categorias": categorias}
            self._incrementar(estado, "feedbacks")
            self.estado_set(estado)
        if callable(self.registrar_feedback):
            try:
                self.registrar_feedback(
                    "jogo" if ultima.get("dominio") == "jogo" else ultima.get("categoria"),
                    True if resultado == "aceita" else False if resultado == "recusa" else None,
                    resultado=resultado,
                )
            except Exception as erro:
                self._falha("feedback_resposta", erro)
        return {"resultado": resultado, "categoria": ultima.get("categoria")}

    def registrar_silencio_pendente(self) -> dict[str, Any]:
        """Registra silêncio como sinal fraco, uma única vez e sem punição imediata."""
        agora = float(self.clock())
        with self._lock:
            estado = self._estado()
            ultima = dict(estado.get("ultima_emissao") or {})
            idade = agora - float(ultima.get("ts") or 0.0)
            if (
                not ultima or ultima.get("feedback_registrado")
                or idade < JANELA_FEEDBACK_PRESENCA_S
            ):
                return {}
            ultima["feedback_registrado"] = True
            ultima["feedback"] = "silencio"
            estado["ultima_emissao"] = ultima
            self._incrementar(estado, "feedbacks")
            self.estado_set(estado)
        if callable(self.registrar_feedback):
            try:
                self.registrar_feedback(
                    "jogo" if ultima.get("dominio") == "jogo" else ultima.get("categoria"),
                    None, resultado="silencio",
                )
            except Exception as erro:
                self._falha("feedback_silencio", erro)
        return {"resultado": "silencio", "categoria": ultima.get("categoria")}

    def _candidato_cotidiano(self, contexto: Mapping[str, Any], estado: dict[str, Any], agora: float) -> dict[str, Any]:
        if contexto.get("modo_jogo_ativo"):
            estado["atividade"] = {}
            return {}
        assunto = str(contexto.get("assunto") or "").strip()
        titulo = str(contexto.get("titulo_janela") or "").strip()
        chave = _codigo(f"{assunto}:{titulo}", 96)
        atividade = dict(estado.get("atividade") or {})
        if not chave or chave != atividade.get("chave"):
            estado["atividade"] = {"chave": chave, "assunto": assunto, "inicio_ts": agora}
            return {}
        duracao = agora - float(atividade.get("inicio_ts") or agora)
        perfil = self._escolher_perfil(estado, contexto, "companhia")
        limiar = 3600.0 if perfil == "silencioso" else 2100.0 if perfil == "presente" else 3000.0
        if duracao < limiar or assunto not in {"Programação", "Estudo", "Trabalho"}:
            return {}
        fala = "Você tá num foco bonito faz um tempo. Só não deixa o corpo pagar a conta: uma pausa curta agora pode salvar o ritmo depois."
        if callable(self.recomendacao_musical) and not contexto.get("musica_atual_status"):
            try:
                musical = str(self.recomendacao_musical("foco") or "").strip()
            except Exception as erro:
                self._falha("recomendacao_musical", erro)
                musical = ""
            if musical:
                fala = musical
                categoria = "musica"
            else:
                categoria = "companhia"
        else:
            categoria = "companhia"
        return {
            "origem": "presenca_cotidiana",
            "dominio": "musica" if categoria == "musica" else "rotina",
            "categoria": categoria,
            "fala": fala,
            "confianca": 0.86,
            "utilidade": 61,
            "evidencias": [assunto, "atividade contínua por cinquenta minutos"],
            "fundamentada": True,
            "momento_seguro": True,
            "chave": f"foco_longo:{chave}",
        }

    def executar_ciclo(self) -> dict[str, Any]:
        self.registrar_silencio_pendente()
        agora = float(self.clock())
        with self._lock:
            estado = self._estado()
            contexto = self._contexto()
            candidato = self._candidato_cotidiano(contexto, estado, agora)
            self.estado_set(estado)
        return self.considerar(candidato) if candidato else {"status": "observando"}

    def executar(self) -> None:
        self._running = True
        while self._running and not self.stop_event.is_set():
            try:
                self.executar_ciclo()
            except Exception as exc:
                self.log(f"⚠️ [PRESENÇA] ciclo ignorado: {type(exc).__name__}: {exc}")
                self._falha("ciclo", exc)
            if self.stop_event.wait(self.intervalo_ciclo_s):
                break

    def encerrar(self) -> None:
        self._running = False
        self.stop_event.set()


def criar_diretor_presenca_runtime(**kwargs: Any) -> DiretorPresencaRuntime:
    return DiretorPresencaRuntime(**kwargs)
