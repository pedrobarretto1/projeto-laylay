"""Experiência factual do executor, no estado e aprendizado compartilhados."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import math
import threading
import time
from typing import Any, Callable, Mapping
from uuid import uuid4
import hashlib

from mente_laylay.memoria_mental.decisao_observada import (
    DecisaoObservada, EpisodioExplicavel, ExplicacaoOcorrencia, MedicaoObservada, ExpectativaResultado,
    REFERENCIAL_GIRO_RELATIVO,
    NaoQualificacaoMedicao,
)
from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA


def medicoes_rotacao_observadas(dados: Mapping[str, Any], *, ocorrencia_id: str) -> tuple[MedicaoObservada, ...]:
    """Adapta a leitura qualificada para o envelope atual, sem inferir do pedido.

    Publicação imediata e histórico reutilizam a qualificação do transporte;
    medida não confirma conclusão, posição absoluta ou uma nova autorização.
    """
    angulo = dados.get("rotacao_medida_graus")
    if not ocorrencia_id or type(angulo) not in (int, float) or not math.isfinite(angulo):
        return ()
    if (dados.get("ok") is True and dados.get("prova_rotacao") is True
            and dados.get("evidencia") == "imu_relativa_turnend_e_sack"):
        metodo = "imu_relativa_turnend_e_sack"
        limite = "Estimativa relativa da IMU para esta ocorrência; não mede posição absoluta."
    elif (dados.get("leitura_rotacao_valida") is True
            and dados.get("evidencia_leitura_rotacao") == "turnend_correlacionado_imu_valida"):
        metodo = "turnend_correlacionado_imu_valida"
        limite = "Leitura até o encerramento reportado; não confirma conclusão da operação nem posição absoluta."
    else:
        return ()
    return (MedicaoObservada(ocorrencia_id=ocorrencia_id, owner="executor_corpo",
        grandeza="rotação relativa", valor=angulo, unidade="graus", metodo=metodo,
        limite_observacao=limite, referencial=REFERENCIAL_GIRO_RELATIVO),)


def _nao_qualificacao_rotacao(campos: Any, *, ocorrencia_id: str) -> NaoQualificacaoMedicao | None:
    """Valida o envelope do owner, sem refazer a decisão ou interpretar prosa."""
    if (not isinstance(campos, Mapping) or campos.get("fonte") != "qualificacao_turnend_owner_usb_v1"
            or campos.get("autoriza_execucao") is not False or campos.get("confirma_efeito") is not False):
        return None
    if any(campos.get(chave, esperado) != esperado for chave, esperado in (
            ("ocorrencia_id", ocorrencia_id), ("owner", "executor_corpo"),
            ("grandeza", "rotação relativa"), ("unidade", "graus"))):
        return None
    criterio, codigo = campos.get("criterio"), campos.get("codigo")
    if type(criterio) is not str or type(codigo) is not str:
        return None
    if (criterio == "criterio_da_fonte_nao_atendido" and codigo not in
            {"IMU_OU_SESSAO", "SATURACAO", "PROTECAO", "INTERROMPIDO"}) or (
            criterio != "criterio_da_fonte_nao_atendido" and codigo != ""):
        return None
    try:
        return NaoQualificacaoMedicao(ocorrencia_id, "executor_corpo", "rotação relativa", "graus",
            criterio, campos["fonte"], codigo)
    except (ValueError, TypeError):
        return None


def nao_qualificacoes_rotacao_observadas(dados: Mapping[str, Any], *, ocorrencia_id: str) -> tuple[NaoQualificacaoMedicao, ...]:
    """Adapta apenas a decisão explícita da própria chamada do transporte."""
    if (dados.get("leitura_rotacao_valida") is not False or dados.get("prova_rotacao") is True
            or medicoes_rotacao_observadas(dados, ocorrencia_id=ocorrencia_id)):
        return ()
    observada = _nao_qualificacao_rotacao(dados.get("nao_qualificacao_rotacao"), ocorrencia_id=ocorrencia_id)
    return (observada,) if observada is not None else ()


def expectativas_corpo_observadas(ocorrencia: Mapping[str, Any]) -> tuple[ExpectativaResultado, ...]:
    """Lê a captura deste owner; não completa meta com receipt ou intenção."""
    try:
        capturadas = ocorrencia.get("expectativas", ())
        if type(capturadas) not in (list, tuple) or len(capturadas) > 8:
            raise ValueError("Envelope de expectativas inválido.")
        itens = []
        for item in capturadas:
            if (not isinstance(item, Mapping) or item.get("ocorrencia_id") != ocorrencia["id"]
                    or item.get("owner") != "executor_corpo"
                    or item.get("fonte") != "parametros_validados_antes_da_execucao"
                    or item.get("autoriza_execucao") is not False or item.get("confirma_efeito") is not False):
                raise ValueError("Expectativa não pertence à captura deste owner.")
            meta = ExpectativaResultado(**{k: item[k] for k in (
                "ocorrencia_id", "owner", "grandeza", "valor", "unidade", "fonte", "registrada_em")},
                referencial=item.get("referencial", ""))
            if meta.registrada_em > ocorrencia["iniciada_em"]:
                raise ValueError("Expectativa posterior ao início.")
            itens.append(meta)
        if len({(i.grandeza, i.unidade) for i in itens}) != len(itens):
            raise ValueError("Expectativa duplicada.")
        return tuple(itens)
    except (ValueError, TypeError, KeyError):
        return ()


def _limitar_historico(historico: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Um histórico, duas cotas: telemetria não apaga o orçamento dos gestos."""
    contagens = {False:0, True:0}
    mantidos = []
    for e in reversed(historico):
        sensorial = e.get("tipo") == "episodio_sensorial"
        if contagens[sensorial] < 12:
            mantidos.append(e)
            contagens[sensorial] += 1
    return list(reversed(mantidos))


class ExperienciaCorporalRuntime:
    def recuperar_explicacao(self, texto: str, *, turno: Mapping[str, Any]) -> ExplicacaoOcorrencia | None:
        """Seleciona no histórico deste owner; nunca reidrata a projeção da LLM.

        O motivo vivo, diagnóstico atual e último receipt de outro domínio não
        participam. Registros antigos/sem decisão podem comprovar a tentativa,
        mas não justificá-la. Consultar não restabelece concessão.
        """
        from mente_laylay.cognicao.referencias_linguagem import referencia_explicacao_ocorrencia, ids_ocorrencias_citadas
        referencia = referencia_explicacao_ocorrencia(texto, entidades=("gesto", "movimento", "decisao corporal"))
        if not referencia or not turno.get("id"):
            return None
        historico = self.estado.obter_copia("mental", "historico_corporal", []) if self.estado is not None else []
        agora = self.clock()
        episodios = []
        for e in historico:
            if (e.get("origem") != "executor_corpo" or e.get("tipo") == "episodio_sensorial"
                    or type(e.get("ts")) not in (int, float) or not math.isfinite(e["ts"])
                    or not 0 <= agora - e["ts"] <= 900):
                continue
            decisao = None
            d = e.get("decisao_origem")
            try:
                if (isinstance(d, Mapping) and d.get("owner") == "owner_companhia_corporal"
                        and d.get("autoriza_execucao") is False and d.get("confirma_efeito") is False):
                    decisao = DecisaoObservada(id=d["id"], owner=d["owner"], nome=d["nome"], motivo=d["motivo"],
                        turno_id=d["turno_id"], sessao=d["sessao"], intencao_id=d["intencao_id"],
                        objetivo_id=d["objetivo_id"], registrada_em=d["registrada_em"],
                        evidencias=SnapshotComandoIA(dict(d["evidencias"])),
                        criterios=tuple(dict(d.get("criterios") or {}).items()))
            except (ValueError, TypeError, KeyError):
                decisao = None
            if decisao is not None and ((decisao.turno_id, decisao.sessao, decisao.intencao_id) !=
                    (str(e.get("turno_id") or ""), str(e.get("sessao") or ""), str(e.get("intencao_id") or ""))
                    or type(e.get("iniciada_em")) not in (int, float)
                    or (e.get("objetivo_id") and e["objetivo_id"] != decisao.objetivo_id)
                    or decisao.registrada_em > e["iniciada_em"]):
                decisao = None
            try:
                # O booleano confirma somente a obrigação registrada pelo owner.
                # Legado/valor inválido não herda o escopo do diagnóstico atual.
                escopo = e.get("escopo_confirmacao")
                if type(escopo) is not str or escopo not in ("parada elétrica", "PWM e parada elétrica", "giro solicitado, PWM e parada elétrica"):
                    escopo = "escopo não registrado"
                medicoes = medicoes_rotacao_observadas({
                    "ok": e.get("confirmado"), "prova_rotacao": e.get("prova_rotacao"),
                    "evidencia": e.get("evidencia_rotacao"),
                    "rotacao_medida_graus": e.get("rotacao_medida_graus"),
                    "leitura_rotacao_valida": e.get("leitura_rotacao_valida"),
                    "evidencia_leitura_rotacao": e.get("evidencia_leitura_rotacao"),
                }, ocorrencia_id=e["id"])
                # Meta inválida não apaga tentativa ou medição válida.
                expectativas = expectativas_corpo_observadas(e)
                nao_qualificacoes = []
                capturadas_nq = e.get("nao_qualificacoes_medicao", ())
                if (not medicoes and e.get("prova_rotacao") is not True and e.get("leitura_rotacao_valida") is not True
                        and type(capturadas_nq) in (list, tuple) and len(capturadas_nq) == 1):
                    for item in capturadas_nq:
                        if (not isinstance(item, Mapping) or (item.get("ocorrencia_id"), item.get("owner"),
                                item.get("grandeza"), item.get("unidade")) != (e["id"], "executor_corpo", "rotação relativa", "graus")):
                            continue
                        observada = _nao_qualificacao_rotacao(item, ocorrencia_id=e["id"])
                        if observada is not None and observada not in nao_qualificacoes:
                            nao_qualificacoes.append(observada)
                episodio = EpisodioExplicavel(id=e["id"], owner="executor_corpo", nome=e["nome"],
                    turno_origem=str(e.get("turno_id") or ""), sessao=str(e.get("sessao") or ""),
                    iniciada_em=e["iniciada_em"], encerrada_em=e["ts"],
                    intencao_id=str(e.get("intencao_id") or ""), decisao=decisao,
                    justificativa_registrada=decisao is not None and e.get("origem_intencao") != "llm_principal",
                    confirmado=e.get("confirmado"), escopo_confirmacao=escopo,
                    limite_observacao="Não há medição de deslocamento neste registro.", medicoes=medicoes,
                    expectativas=expectativas, nao_qualificacoes_medicao=tuple(nao_qualificacoes))
                episodios.append(episodio)
            except (ValueError, TypeError, KeyError):
                continue
        # Referência explícita vence recência. Nomes repetidos seguem ambíguos.
        citados = ids_ocorrencias_citadas(texto, tuple((e.id, e.nome) for e in episodios))
        if citados is not None:
            episodios = [e for e in episodios if e.id in citados]
        elif referencia == "ultima" and episodios:
            instante = max(e.encerrada_em for e in episodios)
            episodios = [e for e in episodios if e.encerrada_em == instante]
        estado = "unica" if len(episodios) == 1 else "ambigua" if episodios else "ausente"
        return ExplicacaoOcorrencia(str(turno["id"]), str(texto), tuple(episodios[-12:]), estado)

    def __init__(self, *, estado: Any, diagnostico_getter: Callable[[], Mapping[str, Any]],
                 relatar_falha: Callable[..., Any] | None = None,
                 clock: Callable[[], float] = time.time) -> None:
        self.estado, self.diagnostico_getter = estado, diagnostico_getter
        self.relatar_falha, self.clock = relatar_falha, clock
        self.aprendizado: Any = None
        self._ultimo_erro = ""
        self._lock = threading.RLock()
        self._consulta_sensorial: tuple[str, int, int] = ("", 0, 0)
        self._inercial_anterior: tuple[Any, ...] = ("", "ESTAVEL")
        self._presenca_inercial_considerada: tuple[str, int] | None = None
        self._marcos_presenca_considerados: list[tuple[str, str]] = []
        # Sinal coalescido, sem payload, fila ou autoridade. O consumidor
        # acorda e relê o mesmo estado factual; nunca gera fala na thread USB.
        self.notificacao_observada = threading.Event()

    def observar_sensores(self, diagnostico: Mapping[str, Any], *, perfil: str) -> dict[str, Any]:
        """Consome GUARD/DIST do owner; não executa, não estima movimento."""
        self.observar_inercial(diagnostico, perfil=perfil)
        from mente_laylay.especialistas.percepcao_distancia import FASES_REFLEXO, RISCOS
        sensores = diagnostico.get("sensores") or {}
        p = sensores.get("protecao") or {}
        sessao = str(diagnostico.get("sessao") or "")
        consulta, incidente = sensores.get("consulta_id"), p.get("incidente_id")
        fase, risco = p.get("fase"), p.get("risco")
        if (self.estado is None or diagnostico.get("aplicacao_confirmada") is not True
            or not sessao or sensores.get("origem") != "owner_usb_dist_guard"
            or sensores.get("suportado") is not True or sensores.get("recente") is not True
            or p.get("origem") != "executor_protecao_esp" or p.get("recente") is not True
            or p.get("autoriza_execucao") is not False or risco not in RISCOS
            or fase not in FASES_REFLEXO | {"PRONTA","BLOQUEADA","CONCLUIDA","CANCELADA","FALHA_PWM","ESPERA_BUSCA"}
            or type(consulta) is not int or consulta <= 0
            or type(incidente) is not int or incidente <= 0
            or type(p.get("tentativa_busca")) is not int or not 0 <= p["tentativa_busca"] <= 4):
            return {}
        with self._lock:
            anterior_sessao, anterior_consulta, anterior_incidente = self._consulta_sensorial
            if sessao == anterior_sessao and (consulta <= anterior_consulta or incidente < anterior_incidente):
                return {}
            self._consulta_sensorial = (sessao, consulta, incidente)
            identidade = "sensor_" + hashlib.sha256(f"{sessao}:{incidente}".encode()).hexdigest()[:24]
            historico = self.estado.obter_copia("mental", "historico_corporal", [])
            anterior = next((e for e in historico if e.get("id") == identidade), {})
            # Um cancelamento herdado do handshake não é um incidente novo.
            if not anterior and fase in {"PRONTA", "CANCELADA"}:
                return {}
            assinatura = (fase, risco, p["tentativa_busca"], p.get("vigia_ativa") is True)
            if tuple(anterior.get("assinatura_observacao", ())) == assinatura:
                return deepcopy(anterior)
            agora = self.clock()
            desfechos = {"ESPERA_BUSCA":"busca_em_espera", "BLOQUEADA":"protecao_bloqueada",
                "CONCLUIDA":"reflexo_concluido", "CANCELADA":"reflexo_cancelado",
                "FALHA_PWM":"falha_pwm", "PRONTA":"protecao_rearmada"}
            resultado = desfechos.get(fase,"reflexo_em_andamento")
            marcos = list(anterior.get("desfechos_observados") or [])
            novo_marco = fase in desfechos and resultado not in marcos
            if novo_marco:
                marcos.append(resultado)
            e = {**anterior, "id":identidade, "tipo":"episodio_sensorial", "origem":"executor_corpo",
                "origem_intencao":"reflexo_firmware", "nome":"protecao_sensorial", "familia":"protecao_sensorial",
                "perfil":perfil, "variante":0, "turno_id":"", "sessao":sessao,
                "incidente_id":incidente, "consulta_id":consulta,
                "iniciada_em":anterior.get("iniciada_em",agora), "ts":agora,
                "fase":fase, "risco":risco, "risco_inicial_observado":anterior.get("risco_inicial_observado",risco),
                "tentativa_busca":p["tentativa_busca"], "resultado":resultado,
                "desfechos_observados":marcos, "assinatura_observacao":list(assinatura),
                "observacao_confirmada":True, "recuperada_da_memoria":False, "confirmado":False, "parada_confirmada":False,
                "movimentos_confirmados":0, "duracao_comandada_confirmada_ms":0,
                "prova_deslocamento":False, "autoriza_execucao":False, "pertence_ao_turno_atual":False,
                "evidencia":"DIST_GUARD_correlacionados", "leituras_observadas":deepcopy(sensores.get("leituras") or {}),
                "transicoes_observadas":(list(anterior.get("transicoes_observadas") or []) +
                    [{"fase":fase,"risco":risco,"tentativa":p["tentativa_busca"],"ts":agora}])[-12:]}
            if novo_marco and resultado == "busca_em_espera":
                e["espera_observada_em"] = agora
            marco = ("recuperacao" if risco == "NENHUM" else "inicio"
                if risco == e["risco_inicial_observado"] else f"mudanca:{risco}")
            relatos = list(anterior.get("marcos_relato") or [])
            observado = next((m for m in relatos if m["marco"] == marco), None)
            novo_relato = observado is None
            if observado is None:
                observado = {"marco":marco, "risco":risco, "ts":agora}
                relatos.append(observado)
            e["marcos_relato"] = relatos
            e["marco_relato_atual"] = observado
            def publicar(mental):
                h = list(mental.get("historico_corporal") or [])
                h = [e if item.get("id")==identidade else item for item in h]
                if not any(item.get("id")==identidade for item in h):
                    h.append(e)
                return {**mental, "historico_corporal":_limitar_historico(h), "experiencia_corporal":e}
            self.estado.atualizar("mental",publicar)
            if novo_relato:
                self.notificacao_observada.set()
            if novo_marco and self.aprendizado is not None:
                try:
                    aprendido = self.aprendizado.registrar_evidencia(
                        chave=f"corpo_sensorial:{perfil}:{e['risco_inicial_observado']}:{resultado}",
                        tipo="episodio_sensorial_corporal", escopo="corpo_motor",
                        valor={"risco":e["risco_inicial_observado"],"resultado":resultado,
                            "descricao_humana":"fases observadas da proteção, sem medir deslocamento"},
                        sinal=.5, origem="executor_corpo", evidencia=resultado,
                        contexto={"perfil":perfil,"experiencia":e}, id_evento=f"sensorial:{identidade}:{resultado}")
                    self._ultimo_erro = "" if aprendido is not None else "falha_persistencia_experiencia_sensorial"
                except Exception as erro:
                    self._falha("falha_aprendizado_sensorial",erro)
            return deepcopy(e)

    def observar_inercial(self, diagnostico: Mapping[str, Any], *, perfil: str) -> dict[str, Any]:
        """Só transições medidas; hipótese de levantamento não vira fato de colo."""
        i = diagnostico.get("imu") or {}
        sessao = str(diagnostico.get("sessao") or "")
        if (self.estado is None or diagnostico.get("aplicacao_confirmada") is not True or not sessao
                or i.get("origem") != "imu_esp" or i.get("recente") is not True
                or i.get("autoriza_execucao") is not False):
            return {}
        m = i.get("manuseio")
        if m not in {"ESTAVEL", "INCLINADA", "TOMBADA", "MOVIMENTO_BRUSCO", "POSSIVEL_LEVANTAMENTO"}:
            return {}
        with self._lock:
            anterior = self._inercial_anterior
            fase = i.get("fase_manuseio", m)
            assinatura = (sessao, m, fase, i.get("evento_manuseio"))
            self._inercial_anterior = assinatura
            if anterior == assinatura or (anterior[0] != sessao and m == "ESTAVEL"):
                return {}
            e = {"id": "inercial_" + uuid4().hex, "tipo": "episodio_sensorial", "familia": "manuseio_inercial",
                 "nome": "manuseio", "sessao": sessao, "perfil": perfil, "variante": 0, "turno_id": "",
                 "ts": self.clock(), "resultado": m.lower(), "observacao_confirmada": True, "confirmado": False,
                 "origem": "executor_corpo", "evidencia": "imu_esp_recente", "autoriza_execucao": False,
                 "prova_deslocamento": False, "parada_confirmada": False, "movimentos_confirmados": 0,
                 "duracao_comandada_confirmada_ms": 0,
                 "fase_manuseio": fase, "evento_manuseio": i.get("evento_manuseio"),
                 "repeticoes_manuseio": i.get("repeticoes_manuseio", 0),
                 "leituras_observadas": {k: i.get(k) for k in ("modelo", "roll_graus", "pitch_graus", "yaw_relativo_graus")}}
            self.estado.atualizar("mental", lambda mental: {**mental,
                "historico_corporal": _limitar_historico(list(mental.get("historico_corporal") or []) + [e]),
                "experiencia_corporal": e})
            if fase in {"DESCONFIADA", "SUSTO", "RESMUNGO", "DESORIENTADA", "RECOMPONDO"}:
                self.notificacao_observada.set()
            if self.aprendizado is not None:
                try:
                    self.aprendizado.registrar_evidencia(chave=f"corpo_inercial:{perfil}:{m}",
                        tipo="episodio_sensorial_corporal", escopo="corpo_motor",
                        valor={"observacao": m, "descricao_humana": "transição inercial observada; levantamento é hipótese"},
                        sinal=.5, origem="executor_corpo", evidencia=e["evidencia"],
                        contexto={"perfil": perfil, "experiencia": e}, id_evento=e["id"])
                except Exception as erro:
                    self._falha("falha_aprendizado_inercial", erro)
            return deepcopy(e)

    def evento_presenca_vigente(self, evento: Mapping[str, Any]) -> bool:
        """Revalida a mesma observação no envio; memória não substitui o vivo."""
        d = self.diagnostico_getter()
        i = d.get("imu") or {}
        fonte = evento.get("observacao_corporal") or {}
        historico = self.estado.obter_copia("mental","historico_corporal",[]) if self.estado is not None else []
        ocorrencia = evento.get("ocorrencia_observada")
        if ocorrencia is not None:
            if not isinstance(ocorrencia, Mapping):
                return False
            # Vincula o marco genérico à prova deste owner; IDs fornecidos
            # por outro chamador não adquirem a política de reação corporal.
            if fonte.get("tipo_observacao") == "protecao_sensorial":
                comprovada = any(e.get("sessao") == fonte.get("sessao")
                    and e.get("id") == ocorrencia.get("episodio_id")
                    and e.get("id") == fonte.get("experiencia_id")
                    and any(m.get("marco") == ocorrencia.get("marco")
                        and m.get("ts") == evento.get("timestamp")
                        and m.get("risco") == fonte.get("risco_medido")
                        for m in e.get("marcos_relato") or []) for e in historico)
            else:
                comprovada = any(e.get("id") == ocorrencia.get("episodio_id")
                    and e.get("sessao") == fonte.get("sessao")
                    and e.get("evento_manuseio") == fonte.get("evento_manuseio")
                    and e.get("fase_manuseio") == fonte.get("fase_manuseio")
                    and e.get("ts") == evento.get("timestamp")
                    and ocorrencia.get("marco") == ("recuperacao" if e.get("fase_manuseio") == "RECOMPONDO"
                        else f"mudanca:{e.get('fase_manuseio')}") for e in historico)
            if not comprovada:
                return False
        if fonte.get("tipo_observacao") == "protecao_sensorial":
            sensores = d.get("sensores") or {}
            p = sensores.get("protecao") or {}
            origem_medida = any(e.get("id")==fonte.get("experiencia_id")
                and e.get("tipo")=="episodio_sensorial" and e.get("sessao")==fonte.get("sessao")
                and e.get("incidente_id")==fonte.get("incidente_id")
                and e.get("risco_inicial_observado")==fonte.get("risco_observado")
                and e.get("observacao_confirmada") is True and not e.get("recuperada_da_memoria")
                for e in historico)
            return bool(d.get("aplicacao_confirmada") is True and fonte.get("sessao")==d.get("sessao")
                and sensores.get("recente") is True and sensores.get("origem")=="owner_usb_dist_guard"
                and p.get("recente") is True and p.get("origem")=="executor_protecao_esp"
                and p.get("autoriza_execucao") is False and origem_medida
                and 0 <= self.clock()-evento.get("timestamp",0) < 25)
        origem_medida = any(e.get("sessao")==fonte.get("sessao")
            and e.get("evento_manuseio")==fonte.get("evento_manuseio")
            and e.get("fase_manuseio")==fonte.get("fase_manuseio")
            and e.get("observacao_confirmada") is True and not e.get("recuperada_da_memoria")
            for e in historico)
        return bool(d.get("aplicacao_confirmada") is True and i.get("recente") is True
            and i.get("origem") == "imu_esp" and i.get("autoriza_execucao") is False
            and fonte.get("sessao") == d.get("sessao")
            and origem_medida
            and 0 <= self.clock()-evento.get("timestamp",0) < 25)

    def candidato_presenca(self) -> dict[str, Any]:
        """Manuseio e proteção compartilham a mesma governança de presença."""
        return self._candidato_inercial() or self._candidato_sensorial()

    def _candidato_inercial(self) -> dict[str, Any]:
        """Uma oportunidade factual por fase, sem falar nem conceder tração."""
        d = self.diagnostico_getter()
        i = d.get("imu") or {}
        descricoes = {
            "DESCONFIADA": "Meu corpo permaneceu inclinado por mais de um segundo.",
            "SUSTO": "Meu sensor mediu um movimento brusco no corpo.",
            "RESMUNGO": "Meu sensor mediu balanço forte persistente ou repetido no corpo.",
            "DESORIENTADA": "A IMU mediu inclinação forte ou uma combinação compatível com possível levantamento; não sei se estou no colo.",
            "RECOMPONDO": "O sensor voltou a medir o corpo estável depois de um episódio de manuseio.",
        }
        sessao = d.get("sessao")
        with self._lock:
            historico = self.estado.obter_copia("mental","historico_corporal",[]) if self.estado is not None else []
            e = next((e for e in reversed(historico) if e.get("sessao")==sessao
                and e.get("fase_manuseio") in descricoes and type(e.get("evento_manuseio")) is int
                and e.get("familia")=="manuseio_inercial" and e.get("observacao_confirmada") is True
                and not e.get("recuperada_da_memoria")),{})
            fase,numero=e.get("fase_manuseio"),e.get("evento_manuseio")
            if not e or self._presenca_inercial_considerada == (sessao,numero):
                return {}
            fonte = {"sessao":sessao,"evento_manuseio":numero,"fase_manuseio":fase,
                "evento_leitura":i.get("evento_manuseio"),"fase_atual":i.get("fase_manuseio"),
                "relato_de_episodio_recente":True,
                "repeticoes_manuseio":e.get("repeticoes_manuseio",0),"autoriza_execucao":False}
            descricao=descricoes[fase]
            if i.get("fase_manuseio")=="TRANQUILA" and fase!="RECOMPONDO":
                descricao += " Agora a leitura está estável."
            evento = {"origem":"experiencia_corporal", "dominio":"corpo", "categoria":"companhia",
                "conteudo":descricao,"evidencias":[descricao],"foco_evidencia":descricao,
                "observacao_corporal":fonte,"timestamp":e["ts"],"validade_s":25,
                "chave":f"manuseio:{sessao}:{numero}","confianca":.94,"utilidade":80,
                "assunto":f"manuseio:{fase.lower()}",
                "motivo":"Reação breve, reclamona e fofa ao próprio corpo; sem acusar Pedro, sem dor, dano ou colo inventados. Pode ficar em silêncio.",
                "executavel":False,"autoriza_execucao":False}
            evento["ocorrencia_observada"] = {"episodio_id":e["id"],
                "marco":"recuperacao" if fase == "RECOMPONDO" else f"mudanca:{fase}"}
            if not self.evento_presenca_vigente(evento):
                return {}
            self._presenca_inercial_considerada = (sessao,numero)
            return evento

    def _candidato_sensorial(self) -> dict[str, Any]:
        d = self.diagnostico_getter()
        descricoes = {
            "OBSTACULO": "Minha medição frontal indicou algo a dez centímetros ou menos à frente.",
            "BORDA": "Minha medição inferior indicou a superfície mais distante que o limite de proteção.",
            "BORDA_SEM_RETORNO": "Minha medição inferior deixou de confirmar a superfície; isso foi um alerta de possível borda, sem provar queda.",
        }
        with self._lock:
            historico = self.estado.obter_copia("mental","historico_corporal",[]) if self.estado is not None else []
            e = next((e for e in reversed(historico) if e.get("sessao")==d.get("sessao")
                and e.get("tipo")=="episodio_sensorial" and e.get("risco_inicial_observado") in descricoes
                and e.get("observacao_confirmada") is True and not e.get("recuperada_da_memoria")),{})
            if not e:
                return {}
            marco = e.get("marco_relato_atual") or {}
            if not marco:
                return {}
            chave = (e["id"], marco["marco"])
            if chave in self._marcos_presenca_considerados:
                return {}
            recuperacao = marco["marco"] == "recuperacao"
            descricao = ("A proteção voltou a registrar ausência de alerta nos sensores; isso não mede deslocamento nem garante todo o entorno."
                if recuperacao else descricoes.get(marco["risco"], "A proteção registrou uma mudança de alerta."))
            fonte = {"tipo_observacao":"protecao_sensorial", "sessao":e["sessao"],
                "experiencia_id":e["id"], "incidente_id":e["incidente_id"],
                "risco_observado":e["risco_inicial_observado"],
                "risco_medido":marco["risco"],
                "fase_observada":e["fase"], "relato_de_episodio_recente":True,
                "prova_deslocamento":False, "autoriza_execucao":False}
            evento = {"origem":"experiencia_corporal", "dominio":"corpo", "categoria":"companhia",
                "conteudo":descricao, "evidencias":[descricao], "foco_evidencia":descricao,
                "observacao_corporal":fonte, "timestamp":e["iniciada_em"] if marco["marco"] == "inicio" else marco["ts"], "validade_s":25,
                "ocorrencia_observada":{"episodio_id":e["id"], "marco":marco["marco"]},
                "chave":f"protecao:{e['sessao']}:{e['incidente_id']}:{marco['marco']}", "confianca":.94,
                "utilidade":80, "assunto":f"protecao:{marco['risco'].lower()}",
                "motivo":"Reação breve e fofa a algo medido no próprio corpo. Pode ficar em silêncio; não afirmar deslocamento, caminho percorrido ou segurança além da medição.",
                "executavel":False, "autoriza_execucao":False}
            if not self.evento_presenca_vigente(evento):
                return {}
            self._marcos_presenca_considerados = [*self._marcos_presenca_considerados, chave][-128:]
            return evento

    def contexto_sensorial(self, diagnostico: Mapping[str, Any], *, perfil: str) -> dict[str, Any]:
        """Projeção factual da mesma história para raciocínio e ritmo."""
        sensores = diagnostico.get("sensores") or {}
        p = sensores.get("protecao") or {}
        sessao = str(diagnostico.get("sessao") or "")
        historico = self.estado.obter_copia("mental","historico_corporal",[]) if self.estado is not None else []
        recentes = []
        for e in historico:
            ts = e.get("ts")
            if (e.get("tipo")=="episodio_sensorial" and e.get("sessao")==sessao
                and e.get("perfil")==perfil and not e.get("recuperada_da_memoria")
                and type(ts) in {int,float} and math.isfinite(ts) and 0 <= self.clock()-ts <= 180):
                recentes.append(e)
        esperas = [e for e in recentes if "busca_em_espera" in e.get("desfechos_observados",[])]
        return {"origem":"experiencia_sensorial_observada", "vigente":bool(
                diagnostico.get("aplicacao_confirmada") is True and sensores.get("recente") is True
                and sensores.get("suportado") is True and sensores.get("origem")=="owner_usb_dist_guard"
                and p.get("origem")=="executor_protecao_esp" and p.get("recente") is True and sessao),
            "episodios_recentes":len(recentes), "buscas_em_espera":len(esperas),
            "ultima_espera_em":max((e.get("espera_observada_em",0) for e in esperas),default=0),
            "segundos_ultima_espera":max(0,self.clock()-max(e.get("espera_observada_em",0) for e in esperas)) if esperas else None,
            "fase_atual":p.get("fase",""), "risco_atual":p.get("risco",""),
            "autoriza_execucao":False, "prova_deslocamento":False}

    def _falha(self, codigo: str, erro: Exception) -> None:
        self._ultimo_erro = codigo
        try:
            if callable(self.relatar_falha):
                self.relatar_falha("corpo_motor", codigo, erro=erro)
        except Exception:
            pass

    def conectar_aprendizado(self, aprendizado: Any) -> None:
        self.aprendizado = aprendizado
        # Recupera observações, nunca sessão ou concessão. Não substitui o vivo.
        try:
            if self.estado is None or self.estado.obter_copia("mental", "historico_corporal", []):
                return
            historico = []
            for h in aprendizado.memoria.listar_hipoteses_aprendizado(limit=500):
                if h.get("tipo") not in {"execucao_corporal", "episodio_sensorial_corporal"}:
                    continue
                for evento in aprendizado.memoria.listar_eventos_aprendizado(h["chave"], limit=3):
                    e = (evento.get("contexto") or {}).get("experiencia")
                    if isinstance(e, dict) and e.get("origem") == "executor_corpo":
                        historico.append({**e, "recuperada_da_memoria": True, "pertence_ao_turno_atual": False})
            historico = sorted(historico,key=lambda e:e.get("ts",0))
            historico = _limitar_historico(sorted({e["id"]:e for e in historico if e.get("id")}.values(),key=lambda e:e["ts"]))
            if historico:
                self.estado.atualizar_campos("mental", historico_corporal=historico, experiencia_corporal=historico[-1])
        except Exception as erro:
            self._falha("falha_recuperacao_experiencia", erro)

    def iniciar(self, *, nome: str, origem_intencao: str, perfil: str,
                intencao_id: str = "", turno_id: str | None = None,
                variante: int = 0, movimentos: tuple = (), familia: str = "",
                decisao_origem: DecisaoObservada | None = None,
                angulo_solicitado_graus: int | None = None) -> dict[str, Any]:
        mental = self.estado.retrato_dominio("mental") if self.estado is not None else {}
        diag = self.diagnostico_getter()
        ocorrencia = {"id": uuid4().hex, "origem": "executor_corpo", "nome": nome, "familia": familia or nome,
                "origem_intencao": origem_intencao, "perfil": perfil,
                "intencao_id": intencao_id, "turno_id": str(turno_id if turno_id is not None else (mental.get("turno_atual") or {}).get("id", "")),
                "sessao": str(diag.get("sessao") or ""), "iniciada_em": self.clock(),
                "variante": variante % 3, "movimentos": [list(m) for m in movimentos]}
        if angulo_solicitado_graus is not None:
            if type(angulo_solicitado_graus) is not int:
                raise ValueError("Meta angular exige parâmetro inteiro validado antes do efeito.")
            expectativa = ExpectativaResultado(ocorrencia_id=ocorrencia["id"], owner="executor_corpo",
                grandeza="rotação relativa", valor=angulo_solicitado_graus, unidade="graus",
                fonte="parametros_validados_antes_da_execucao", registrada_em=ocorrencia["iniciada_em"],
                referencial=REFERENCIAL_GIRO_RELATIVO)
            ocorrencia["expectativas"] = [asdict(expectativa)]
        if decisao_origem is not None:
            if type(decisao_origem) is not DecisaoObservada:
                raise ValueError("Fonte da decisão exige captura tipada anterior ao efeito.")
            fonte = decisao_origem.como_dict()
            if any(fonte[k] != ocorrencia[k] for k in ("intencao_id", "turno_id", "sessao")):
                raise ValueError("Fonte da decisão não pertence à ocorrência.")
            if fonte["registrada_em"] > ocorrencia["iniciada_em"]:
                raise ValueError("Fonte da decisão não pode nascer depois da ocorrência.")
            ocorrencia["decisao_origem"] = fonte
        return ocorrencia

    def registrar(self, ocorrencia: Mapping[str, Any], retorno: Mapping[str, Any],
                  receipts: list[dict[str, Any]], *, parada: bool = False) -> dict[str, Any]:
        if ocorrencia.get("origem") != "executor_corpo" or not ocorrencia.get("id"):
            raise ValueError("experiência exige ocorrência criada pelo executor")
        confirmado = bool(retorno.get("ok") is True and receipts and all(
            r.get("ok") is True and r.get("parada_confirmada") is True
            and (parada or r.get("aplicacao_pwm_confirmada") is True) for r in receipts))
        cancelado = retorno.get("cancelado") is True or retorno.get("status") == "cancelado"
        e = {**deepcopy(dict(ocorrencia)), "ts": self.clock(), "confirmado": confirmado,
             # A obrigação angular vem do retorno do executor, nunca do nome
             # ou da medida observada; declarar o alvo não comprova seu efeito.
             "escopo_confirmacao": "parada elétrica" if parada else "giro solicitado, PWM e parada elétrica"
                 if type(retorno.get("angulo_solicitado_graus")) is int else "PWM e parada elétrica",
             "duracao_comandada_confirmada_ms": sum(r.get("duracao_ms", 0) for r in receipts
                 if r.get("aplicacao_pwm_confirmada") is True and type(r.get("duracao_ms")) is int
                 and 0 <= r["duracao_ms"] <= 5000),
             "resultado": "parada_eletrica_confirmada" if confirmado and parada else "pwm_e_parada_confirmados" if confirmado else "interrompida" if cancelado else "gesto_nao_confirmado",
             "motivo": str(retorno.get("motivo") or retorno.get("status") or "")[:120],
             "movimentos_confirmados": sum(r.get("aplicacao_pwm_confirmada") is True for r in receipts),
             "parada_confirmada": bool(receipts and receipts[-1].get("parada_confirmada") is True),
             "prova_deslocamento": False, "autoriza_execucao": False}
        if retorno.get("rotacao_medida_graus") is not None:
            e.update(rotacao_medida_graus=retorno["rotacao_medida_graus"],
                     prova_rotacao=retorno.get("prova_rotacao") is True,
                     leitura_rotacao_valida=retorno.get("leitura_rotacao_valida") is True,
                     evidencia_leitura_rotacao=str(retorno.get("evidencia_leitura_rotacao") or "")[:120],
                     evidencia_rotacao="imu_relativa_turnend_e_sack" if retorno.get("prova_rotacao") else "giro_parcial_ou_interrompido")
            if confirmado and e["prova_rotacao"]:
                e["resultado"] = "giro_relativo_confirmado"
        # Só o retorno da chamada atual publica esta decisão, nunca a intenção.
        e.pop("nao_qualificacoes_medicao", None)
        nao_qualificacoes = nao_qualificacoes_rotacao_observadas(retorno, ocorrencia_id=e["id"])
        if nao_qualificacoes:
            e["nao_qualificacoes_medicao"] = [asdict(item) for item in nao_qualificacoes]
        novo = False
        with self._lock:
            if self.estado is not None:
                def publicar(mental):
                    nonlocal novo, e
                    historico = list(mental.get("historico_corporal") or [])
                    if any(item.get("id") == e["id"] for item in historico):
                        return mental
                    novo = True
                    e = {**e, "pertence_ao_turno_atual": bool(e["turno_id"] and str((mental.get("turno_atual") or {}).get("id", "")) == e["turno_id"])}
                    return {**mental, "historico_corporal": _limitar_historico(historico + [e]), "experiencia_corporal": e}
                self.estado.atualizar("mental", publicar)
            else:
                novo = True
            if novo and self.aprendizado is not None:
                try:
                    aprendido = self.aprendizado.registrar_evidencia(
                        chave=f"corpo_execucao:{e['perfil']}:{e['nome']}:{e['variante']}", tipo="execucao_corporal", escopo="corpo_motor",
                        valor={"nome": e["nome"], "perfil": e["perfil"], "variante": e["variante"], "descricao_humana": "confirmação elétrica de gesto, sem observação de deslocamento"},
                        sinal=0 if cancelado else .7 if confirmado else -.8, origem="executor_corpo", evidencia=e["resultado"],
                        contexto={"perfil": e["perfil"], "experiencia": e}, id_evento=f"corpo_execucao:{e['id']}")
                    if aprendido is None:
                        self._ultimo_erro = "falha_persistencia_experiencia"
                    elif self.estado is not None:
                        self._ultimo_erro = ""
                        self.estado.atualizar_campos("mental", aprendizado_corporal={
                            "origem": "aprendizado_compartilhado", "chave": aprendido["chave"],
                            "estado_hipotese": aprendido["status"], "confianca": aprendido["confianca"],
                            "limite_evidencia": "confirmacao_eletrica_sem_deslocamento", "autoriza_execucao": False})
                except Exception as erro:
                    self._falha("falha_aprendizado_experiencia", erro)
        return deepcopy(e)

    def observar_feedback(self, texto: str, *, turno_id: str, referencia_id: str) -> bool:
        from mente_laylay.cognicao.interpretador_continuidade import qualificar_feedback_corporal
        qualificacao = qualificar_feedback_corporal(texto)
        if not qualificacao or not self.aprendizado or self.estado is None or not turno_id or not referencia_id:
            return False
        historico = self.estado.obter_copia("mental", "historico_corporal", [])
        e = next((e for e in reversed(historico) if e.get("id") == referencia_id), {})
        diag = self.diagnostico_getter()
        idade = self.clock() - float(e.get("ts", 0))
        if not e or not math.isfinite(idade) or not 0 <= idade <= 60 or e.get("recuperada_da_memoria") or e.get("sessao") != diag.get("sessao"):
            return False
        if diag.get("aplicacao_confirmada") is not True:
            return False
        fonte = {"dominio": "corpo_motor", "experiencia_id": e["id"], "turno_id": turno_id,
                 "perfil": e["perfil"], "nome": e["nome"], "variante": e["variante"], "autoriza_execucao": False}
        identidade = f"corpo:{turno_id}:{e['id']}"
        tipo, aceito = qualificacao["tipo"], qualificacao["aceito"]
        registro = self.aprendizado.registrar_feedback_contextual(tipo=tipo, aceito=aceito,
            resultado=texto, origem="corpo_motor", alvo=e["nome"], id_evento=identidade, proveniencia=fonte)
        if registro is None:
            return False
        if tipo in {"aceitacao", "recusa"} and e.get("tipo") != "episodio_sensorial":
            self.aprendizado.registrar_evidencia(
                chave=f"{'corpo_preferencia' if aceito else 'corpo_evitacao'}:{e['perfil']}:{e.get('familia', e['nome'])}:{e['variante']}", tipo="preferencia_corporal", escopo="corpo_motor",
                valor={"nome": e["nome"], "perfil": e["perfil"], "variante": e["variante"], "direcao": "favorecer" if aceito else "evitar", "descricao_humana": "avaliação do usuário sobre este gesto corporal"},
                # Recusa é evidência a favor de evitar a variante; não falha
                # da hipótese de preferência. O feedback genérico mantém sinal.
                sinal=.45, origem="feedback_usuario", evidencia=texto,
                contexto=fonte, id_evento=f"corpo_preferencia:{identidade}")
        self.estado.atualizar_campos("mental", feedback_corporal={**fonte, "tipo": tipo, "aceito": aceito})
        return True

    def selecionar_variante(self, nome: str, perfil: str, padrao: int) -> int | None:
        historico = self.estado.obter_copia("mental", "historico_corporal", []) if self.estado is not None else []
        sessao = str(self.diagnostico_getter().get("sessao") or "")
        gestos = [e for e in historico if e.get("tipo") != "episodio_sensorial"]
        recentes = [e for e in gestos[-6:] if e.get("familia") == nome and e.get("perfil") == perfil
                    and e.get("sessao") == sessao and not e.get("recuperada_da_memoria")
                    and (e.get("confirmado") is True or e.get("movimentos_confirmados", 0) > 0)]
        ordem = [(padrao + i) % 3 for i in range(3)]
        # Escolha sobre experiência factual da mesma sessão, sem estimar distância.
        # Não muda a assinatura, os parâmetros ou a autoridade do executor.
        contagens = {v: sum(e.get("variante") == v for e in recentes) for v in ordem}
        ultima = recentes[-1].get("variante") if recentes else None
        ordem.sort(key=lambda v: (v == ultima, contagens[v]))
        if self.aprendizado is None:
            return ordem[0]
        candidatas = []
        evitadas = set()
        try:
            for variante in range(3):
                evitar = f"corpo_evitacao:{perfil}:{nome}:{variante}"
                if self.aprendizado.avaliar_hipotese(evitar).get("aplicavel"):
                    evitadas.add(variante)
                    continue
                chave = f"corpo_preferencia:{perfil}:{nome}:{variante}"
                h = self.aprendizado.memoria.obter_hipotese_aprendizado(chave)
                if not h or h.get("evidencias_positivas", 0) <= h.get("evidencias_negativas", 0):
                    continue
                avaliacao = self.aprendizado.avaliar_hipotese(chave)
                if avaliacao.get("aplicavel"):
                    candidatas.append((h.get("confianca", 0), -ordem.index(variante), variante))
            if candidatas:
                return max(candidatas)[2]
            return next((v for v in ordem if v not in evitadas), None)
        except Exception as erro:
            self._falha("falha_selecao_variante", erro)
            return ordem[0]

    def ritmo_recente(self, *, sessao: str, perfil: str, agora: float | None = None) -> dict[str, Any]:
        """Resumo amostral de comandos confirmados; não estima fadiga ou bateria."""
        agora = self.clock() if agora is None else agora
        historico = self.estado.obter_copia("mental", "historico_corporal", []) if self.estado is not None else []
        motor_ms = gestos = exploracoes = 0
        vistos = set()
        for e in [item for item in historico if item.get("tipo") != "episodio_sensorial"][-12:]:
            if (not isinstance(e, Mapping) or not isinstance(e.get("id"), str) or not e["id"]
                or e["id"] in vistos or e.get("origem") != "executor_corpo"
                or e.get("sessao") != sessao or e.get("perfil") != perfil or e.get("recuperada_da_memoria")):
                continue
            try:
                idade = agora - float(e.get("ts", 0))
            except (ValueError, TypeError):
                continue
            if not math.isfinite(idade) or not 0 <= idade <= 180:
                continue
            duracao = e.get("duracao_comandada_confirmada_ms")
            if duracao is None and e.get("confirmado") is True:
                # Compatibilidade com receipts antigos, de coreografia completa.
                duracao = sum(m[2] for m in e.get("movimentos", [])
                    if isinstance(m, (list, tuple)) and len(m) == 3
                    and type(m[2]) is int and 0 <= m[2] <= 5000)
            if type(duracao) is not int or not 0 < duracao <= 20000:
                continue
            vistos.add(e["id"])
            if idade <= 60:
                motor_ms += duracao
            if e.get("confirmado") is True:
                if idade <= 120:
                    gestos += 1
                familia = str(e.get("familia") or e.get("nome") or "")
                if familia.split(":", 1)[0] == "explorar" or familia.startswith("passeio_"):
                    exploracoes += 1
        return {"origem": "ritmo_corporal_observado", "motor_ms_60s": motor_ms,
                "gestos_120s": gestos, "exploracoes_180s": exploracoes,
                "amostra_maxima": 12, "autoriza_execucao": False, "prova_deslocamento": False}

    def retrato(self) -> dict[str, Any]:
        historico = self.estado.obter_copia("mental", "historico_corporal", []) if self.estado is not None else []
        try:
            sensores_fisicos = (self.diagnostico_getter().get("sensores") or {}).get("suportado") is True
        except Exception:
            sensores_fisicos = False
        campos = ("id", "nome", "tipo", "turno_id", "origem_intencao", "perfil", "variante", "resultado", "confirmado", "ts", "prova_deslocamento", "prova_rotacao", "rotacao_medida_graus", "recuperada_da_memoria", "fase", "risco", "observacao_confirmada", "tentativa_busca", "decisao_origem")
        return {"origem": "experiencia_corporal_observada", "historico_recente": [{k: e[k] for k in campos if k in e} for e in historico[-3:]],
                "aprendizado": self.estado.obter_copia("mental", "aprendizado_corporal", {}) if self.estado is not None else {},
                "feedback": self.estado.obter_copia("mental", "feedback_corporal", {}) if self.estado is not None else {},
                "aprendizado_conectado": self.aprendizado is not None, "autoriza_execucao": False,
                "sensores_fisicos": sensores_fisicos,
                "ultimo_erro": self._ultimo_erro}


def criar_experiencia_corporal_runtime(**kwargs: Any) -> ExperienciaCorporalRuntime:
    return ExperienciaCorporalRuntime(**kwargs)
