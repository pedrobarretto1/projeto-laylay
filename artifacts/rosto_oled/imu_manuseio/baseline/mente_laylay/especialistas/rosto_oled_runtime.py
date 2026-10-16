"""Saída expressiva USB/TCP: um owner de sessão, sem interpretar ou autorizar ações."""
from __future__ import annotations

import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping

from mente_laylay.emocoes.estado_emocional import retrato_emocional_expressavel
from mente_laylay.especialistas.percepcao_distancia import (
    interpretar_linha_distancia, interpretar_linha_protecao, RISCOS,
)
from mente_laylay.especialistas.saude_corporal import interpretar_saude
from mente_laylay.memoria_mental.atividade_operacional_runtime import (
    projetar_atividade_operacional, projetar_falha_operacional, projetar_sucesso_operacional, projetar_envio_operacional,
)
from mente_laylay.especialistas.corpo_wifi_transporte import (
    CAMINHO_CONFIGURACAO_WIFI, ConfiguracaoCorpoWifi, ConfiguracaoCorpoWifiInvalida,
    abrir_corpo_tcp, carregar_configuracao_corpo_wifi,
)

EMOCOES_ROSTO = (
    "calma", "alegre", "triste", "brava", "irritada", "surpresa",
    "envergonhada", "debochada", "acalmando-se",
)


def projetar_rosto(estado: Mapping[str, Any], *, agora: float | None = None) -> tuple[int, int, int]:
    emocao, nivel = retrato_emocional_expressavel(estado, agora=agora)
    indice = EMOCOES_ROSTO.index(emocao) if emocao in EMOCOES_ROSTO else 0
    # Campo legado conservado no protocolo, sem transportar estado de voz.
    return indice, nivel if indice else 1, 0


def _abrir_serial(porta: str) -> Any:
    import serial  # Opcional: instalação sem corpo continua iniciando normalmente.
    # Configurar antes de open: o padrão True/True do pyserial altera as linhas
    # de controle do USB-JTAG e pode resetar a placa numa simples reconexão.
    dispositivo=serial.Serial(port=None,baudrate=115200,timeout=0.1,write_timeout=0.5)
    dispositivo.dtr=False
    dispositivo.rts=False
    dispositivo.port=porta
    dispositivo.open()
    return dispositivo


def _listar_portas_rosto() -> tuple[str, ...]:
    """USB nativa da Espressif é candidata, nunca prova de firmware de rosto."""
    from serial.tools.list_ports import comports
    return tuple(sorted({
        p.device for p in comports()
        if p.vid == 0x303A and p.pid == 0x1001 and p.device
    }))


class RostoOledRuntime:
    def __init__(
        self, *, estado_getter: Callable[[], Mapping[str, Any]], porta: str = "",
        atividade_getter: Callable[[], Mapping[str, Any]] | None = None,
        interacao_getter: Callable[[], bool] | None = None,
        companhia_getter: Callable[[], Mapping[str, Any]] | None = None,
        busca_obstaculos_getter: Callable[[str], bool] | None = None,
        autodetectar: bool = False,
        listar_portas: Callable[[], tuple[str, ...]] = _listar_portas_rosto,
        abrir_serial: Callable[[str], Any] = _abrir_serial,
        config_wifi_path: Path | str | None = None,
        abrir_tcp: Callable[[ConfiguracaoCorpoWifi], Any] = abrir_corpo_tcp,
        publicar_diagnostico: Callable[[dict[str, Any]], Any] | None = None,
        relatar_falha: Callable[..., Any] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.estado_getter = estado_getter
        self.atividade_getter = atividade_getter or (lambda: {})
        self.interacao_getter = interacao_getter or (lambda: False)
        self.companhia_getter = companhia_getter or (lambda: {})
        self.busca_obstaculos_getter = busca_obstaculos_getter or (lambda _: False)
        self._vigia_suportada = self._vigia_ativa = False
        self._seq_vigia = 0
        self._expressao_suportada = False
        self._seq_expressao = 0
        self._ultimo_ack_expressao = float("-inf")
        self._erro_expressao = "nao_negociado"
        self._ultima_expressao: tuple[int, int, int] = (0, 0, 0)
        self._duracao_expressao_ms = 0
        self._atencao_anterior = False
        self.porta = porta.strip()
        self.autodetectar = bool(autodetectar and not self.porta)
        self.listar_portas = listar_portas
        self._porta_ativa = ""
        self.abrir_serial = abrir_serial
        self.abrir_tcp = abrir_tcp
        self._config_wifi_path = Path(config_wifi_path) if config_wifi_path is not None else None
        self._config_wifi: ConfiguracaoCorpoWifi | None = None
        self._erro_wifi = ""
        if self._config_wifi_path is not None:
            self.autodetectar = False
            self.porta = ""
            self._ler_config_wifi()
        self.publicar_diagnostico = publicar_diagnostico
        self.relatar_falha = relatar_falha
        self.monotonic = monotonic
        self._lock = threading.RLock()
        self._serial: Any = None
        self._rx = bytearray()
        self._sessao = ""
        self._seq = 0
        self._ultimo_ack = float("-inf")
        self._confirmado: tuple[int, int, int] | None = None
        self._hack_suportado = False
        self._seq_atividade = 0
        self._ultimo_ack_hack = float("-inf")
        self._hack_confirmado = False
        self._erro_hack = "nao_negociado"
        self._glitch_suportado = False
        self._seq_glitch = 0
        self._ultimo_ack_glitch = float("-inf")
        self._ultima_falha_consumida = 0  # Não reexecuta eventos numa nova conexão.
        self._erro_glitch = "nao_negociado"
        self._som_suportado = False
        self._som_envio_suportado = False
        self._seq_som = 0
        self._acordar_som_pendente = True
        self._ultima_emocao_sonora: tuple[int, int] = (0, 1)
        self._eventos_som_consumidos = {"sucesso": 0, "falha": 0, "envio": 0}
        self._resultados_som_pendentes: dict[str, tuple[int, float]] = {}
        self._ultimo_envio_som = float("-inf")
        self._ultimo_ack_som = float("-inf")
        self._erro_som = "nao_negociado"
        self._motor_suportado = False
        self._limite_motor_ms = 500
        self._rampa_suportada = False
        self._seq_motor = self._seq_parada = 0
        self._motor_cancelar: threading.Event | None = None
        self._motor_em_pulso = self._motor_parada_solicitada = False
        self._motor_pwm_confirmado = self._motor_parada_confirmada = False
        self._erro_motor = "nao_negociado"
        self._sensores_suportados = False
        self._seq_sensores = 0
        self._sensores: dict[str, Any] = {}
        self._protecao: dict[str, Any] = {}
        self._sensores_em = float("-inf")
        self._risco_motor = ""
        self._saude: dict[str, Any] = {}
        self._saude_em = float("-inf")
        self._saude_suportada: bool | None = None
        self._seq_saude = self._reinicios_observados = 0
        self._ultimo_boot = ""
        self._ultimo_dispositivo = ""
        self._erro = "aguardando_esp32" if self.autodetectar else (
            "porta_nao_configurada" if not self.porta else "aguardando_conexao"
        )
        if self._config_wifi_path is not None:
            self._erro = self._erro_wifi or "aguardando_conexao"
        self._ultima_falha_relatada = ""
        self._falha_publicacao_relatada = False
        self._deve_parar: Callable[[], bool] = lambda: False

    def _ler_config_wifi(self) -> None:
        try:
            self._config_wifi = carregar_configuracao_corpo_wifi(self._config_wifi_path)
            self._erro_wifi = "" if self._config_wifi is not None else "configuracao_wifi_inativa"
        except ConfiguracaoCorpoWifiInvalida:
            self._config_wifi = None
            self._erro_wifi = "configuracao_wifi_invalida"

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            recente = self.monotonic() - self._ultimo_ack < 2.5
            hack_recente = self.monotonic() - self._ultimo_ack_hack < 1.2
            return {
                "configurado": bool(self.porta or self.autodetectar or self._config_wifi_path is not None),
                "conectado": self._serial is not None,
                "sessao": self._sessao,
                "transporte": "tcp" if self._config_wifi_path is not None else "serial",
                "modo_conexao": "rede" if self._config_wifi_path is not None else "automatico" if self.autodetectar else "manual",
                "endpoint": self._config_wifi.endpoint if self._config_wifi is not None else "",
                "porta_ativa": self._porta_ativa,
                "evidencia_recente": recente, "aplicacao_confirmada": recente and not self._erro,
                "estado": "disponivel" if recente and not self._erro else "indisponivel",
                "motivo": self._erro or ("frame_confirmado_pelo_esp" if recente else "ack_expirado"),
                "confirmado": list(self._confirmado) if recente and not self._erro else [],
                "evidencia": "ack_apos_renderizacao", "prova_optica": False,
                "autoriza_execucao": False,
                "sensores": self._diagnostico_sensores(),
                "saude": {**self._saude,"suportado":self._saude_suportada is True,
                    "recente":self._serial is not None and self.monotonic()-self._saude_em<3,
                    "reinicios_observados":self._reinicios_observados},
                "expressao": {
                    "suportado": self._expressao_suportada,
                    "confirmada": recente and not self._erro_expressao and self.monotonic() - self._ultimo_ack_expressao < self._duracao_expressao_ms / 1000,
                    "motivo": self._erro_expressao,
                    "fase": list(self._ultima_expressao),
                    "evidencia": "eack_apos_render", "prova_visual_humana": False,
                    "autoriza_execucao": False,
                },
                "som": {
                    "resultados_pendentes": sorted(self._resultados_som_pendentes),
                    "suportado": self._som_suportado,
                    "envio_suportado": self._som_envio_suportado,
                    "solicitacao_confirmada": recente and not self._erro and not self._erro_som
                        and self.monotonic() - self._ultimo_ack_som < 3,
                    "motivo": self._erro_som or "sequencia_aceita_pelo_firmware",
                    "prova_auditiva": False, "autoriza_execucao": False,
                    "confirma_efeito_da_acao": False,
                },
                "hack": {
                    "suportado": self._hack_suportado,
                    "aplicacao_confirmada": hack_recente and not self._erro_hack and not self._erro,
                    "ativo": self._hack_confirmado if hack_recente and not self._erro_hack and not self._erro else False,
                    "motivo": self._erro_hack or ("overlay_confirmado_pelo_esp" if hack_recente else "ack_expirado"),
                    "evidencia": "ack_apos_renderizacao", "prova_optica": False,
                    "autoriza_execucao": False, "confirma_efeito_da_acao": False,
                },
                "glitch": {
                    "suportado": self._glitch_suportado,
                    "aplicacao_confirmada": self.monotonic() - self._ultimo_ack_glitch < 0.9 and not self._erro_glitch and not self._erro,
                    "motivo": self._erro_glitch or "glitch_confirmado_pelo_esp",
                    "evidencia": "ack_apos_renderizacao", "prova_optica": False,
                    "autoriza_execucao": False, "confirma_efeito_da_acao": False,
                },
                "motor": {
                    "rampa_suportada": self._rampa_suportada,
                    "duracao_maxima_ms": self._limite_motor_ms,
                    "suportado": self._motor_suportado,
                    "disponivel": self._motor_suportado and recente and not self._erro,
                    "aplicacao_pwm_confirmada": self._motor_pwm_confirmado,
                    "parada_confirmada": self._motor_parada_confirmada,
                    "em_andamento": self._motor_cancelar is not None or (
                        self.monotonic()-self._sensores_em<.5 and self._protecao.get("reflexo_ativo") is True),
                    "motivo": self._erro_motor,
                    "evidencia": "negociacao_firmware_e_receipts_correlacionados",
                    "prova_rotacao": False, "prova_parada_fisica": False,
                    "autoriza_execucao": False,
                },
            }

    def _publicar(self) -> None:
        try:
            if self.publicar_diagnostico:
                self.publicar_diagnostico(self.diagnostico())
            self._falha_publicacao_relatada = False
        except Exception as erro:
            # Observabilidade não substitui o receipt nem interrompe o corpo.
            if not self._falha_publicacao_relatada and self.relatar_falha:
                try:
                    self.relatar_falha("rosto_oled", "publicacao_diagnostico", erro=erro)
                except Exception:
                    pass
            self._falha_publicacao_relatada = True

    def _escrever(self, linha: str) -> None:
        dados = (linha + "\n").encode("ascii")
        if self._serial.write(dados) != len(dados):
            raise ConnectionError("escrita_serial_parcial")

    def _esperar(self, esperado: str, timeout: float, *, reenviar: str = "", opcional: bool = False,
                 cancelar: Callable[[], bool] | None = None, durante_encerramento: bool = False,
                 capturar: Callable[[str], bool] | None = None) -> bool:
        prazo = self.monotonic() + timeout
        proximo_envio = self.monotonic() + 0.5
        while self.monotonic() < prazo:
            if cancelar is not None and cancelar():
                return False
            if self._deve_parar() and not durante_encerramento:
                raise InterruptedError("encerramento_solicitado")
            if reenviar and self.monotonic() >= proximo_envio:
                self._escrever(reenviar)
                proximo_envio = self.monotonic() + 0.5
            self._rx.extend(self._serial.read(128))
            if len(self._rx) > 2048:
                raise ConnectionError("recepcao_serial_excessiva")
            while b"\n" in self._rx:
                linha, _, resto = self._rx.partition(b"\n")
                self._rx = bytearray(resto)
                recebida = linha.rstrip(b"\r").decode("ascii", errors="replace")
                if (recebida=="BOOT 1 LAYLAY_ROSTO" and self._confirmado is not None
                    and not esperado.startswith("READY ")):
                    # O boot invalida imediatamente o receipt anterior, mesmo
                    # quando a porta USB continua aberta e o ACK era recente.
                    self._ultimo_ack=float("-inf")
                    self._vigia_ativa=False
                    if self._motor_cancelar is not None:
                        self._motor_cancelar.set()
                    raise ConnectionError("boot_observado_no_esp")
                if recebida.startswith("HAZARD "):
                    p = recebida.split()
                    if (len(p) == 6 and p[:3] == ["HAZARD", "1", self._sessao]
                        and p[3].isdecimal() and p[4].isdecimal()
                        and p[5] in RISCOS | {"AGUARDANDO_ESTABILIDADE"}
                        and int(p[3]) == self._seq_motor and self._motor_em_pulso):
                        self._risco_motor = p[5]
                        if esperado.startswith("MACK "):
                            return False
                if capturar is not None and capturar(recebida):
                    return True
                if recebida == esperado:
                    return True
                if esperado.startswith("SOUNDACK ") and recebida.startswith("ERROR 1 SOM_"):
                    if opcional:
                        self._erro_som = recebida
                        return False
                    raise ConnectionError(recebida)
                if opcional and recebida == "ERROR 1 PACOTE_INVALIDO":
                    return False
        if opcional:
            return False
        raise TimeoutError("sem_confirmacao_do_esp")

    def _diagnostico_sensores(self) -> dict[str, Any]:
        idade = max(0, int((self.monotonic() - self._sensores_em) * 1000)) if self._sensores else 4294967295
        recente = self._serial is not None and idade <= 500
        leituras = {}
        for nome, s in self._sensores.items():
            idade_total = min(4294967295, s["idade_ms"] + idade)
            expirada = idade_total > 300
            leituras[nome] = {**s, "idade_ms": idade_total,
                "estado": "EXPIRADA" if expirada else s["estado"],
                "mm": None if expirada else s["mm"]}
        return {"suportado": self._sensores_suportados, "recente": recente,
            "consulta_id": self._seq_sensores,
            "alerta_suportado": self._vigia_suportada, "busca_renovada": self._vigia_ativa,
            "leituras": leituras, "protecao": {**self._protecao, "recente": recente},
            "origem": "owner_usb_dist_guard", "autoriza_execucao": False}

    def _consultar_sensores(self) -> None:
        if not self._sensores_suportados:
            return
        self._seq_sensores += 1
        seq = self._seq_sensores
        dados: dict[str, Any] = {}
        def distancia(linha: str) -> bool:
            if not linha.startswith(f"DIST 1 {seq} "):
                return False
            dados.update(interpretar_linha_distancia(linha, seq))
            return True
        self._escrever(f"DIST 1 {seq}")
        self._esperar("", .35, capturar=distancia)
        protecao: dict[str, Any] = {}
        def guarda(linha: str) -> bool:
            if not linha.startswith(f"GUARD 1 {seq} "):
                return False
            protecao.update(interpretar_linha_protecao(linha, seq, self._sessao))
            return True
        self._escrever(f"GUARD 1 {seq}")
        self._esperar("", .35, capturar=guarda)
        self._sensores, self._protecao = dados, protecao
        self._sensores_em = self.monotonic()

    def _sincronizar_vigia(self) -> None:
        if not self._vigia_suportada:
            return
        try:
            ativa = not self._deve_parar() and self.busca_obstaculos_getter(self._sessao) is True
        except Exception:
            ativa = False
        self._seq_vigia += 1
        campos = f"{self._sessao} {self._seq_vigia} {int(ativa)}"
        self._escrever(f"SENTRY 1 {campos} 1200")
        self._vigia_ativa = self._esperar(f"SENTRYACK 1 {campos}",.3,opcional=True) and ativa

    def _consultar_saude(self) -> None:
        if (not self._vigia_suportada or self._saude_suportada is False
            or self.monotonic()-self._saude_em<2):
            return
        self._seq_saude+=1
        dados: dict[str, Any]={}
        def receber(linha: str) -> bool:
            if not linha.startswith(f"HEALTH 1 {self._seq_saude} "):
                return False
            dados.update(interpretar_saude(linha,self._seq_saude)); return True
        self._escrever(f"HEALTH 1 {self._seq_saude}")
        if self._esperar("",.3,opcional=True,capturar=receber):
            if (self._ultimo_boot and self._ultimo_dispositivo==dados["dispositivo"]
                and self._ultimo_boot!=dados["boot"]):
                self._reinicios_observados+=1
            self._ultimo_boot=dados["boot"]
            self._ultimo_dispositivo=dados["dispositivo"]
            self._saude,self._saude_em,self._saude_suportada=dados,self.monotonic(),True
        elif self._saude_suportada is None:
            self._saude_suportada=False

    def _sincronizar_atividade(self) -> None:
        if not self._hack_suportado:
            return
        # A saída só lê o owner observado; planos e textos não entram na serial.
        try:
            ativo = int(projetar_atividade_operacional(self.atividade_getter(), agora=self.monotonic()))
        except Exception:
            ativo = 0
        self._seq_atividade += 1
        campos = f"{self._sessao} {self._seq_atividade} {ativo}"
        self._escrever(f"ACTIVITY 1 {campos} 1200")
        if self._esperar(f"AACK 1 {campos}", 0.3, opcional=True):
            self._ultimo_ack_hack = self.monotonic()
            self._hack_confirmado = bool(ativo)
            self._erro_hack = ""
        else:
            # A falha deste overlay não invalida um FACE recém-confirmado.
            self._ultimo_ack_hack = float("-inf")
            self._erro_hack = "sem_confirmacao_da_atividade"

    def _sincronizar_falha(self) -> None:
        if not self._glitch_suportado:
            return
        try:
            falha = projetar_falha_operacional(self.atividade_getter(), agora=self.monotonic())
        except Exception:
            return
        if falha is None or falha[0] <= self._ultima_falha_consumida:
            return
        # Consome antes do envio: uma resposta perdida não autoriza replay.
        self._ultima_falha_consumida = falha[0]
        self._seq_glitch += 1
        campos = f"{self._sessao} {self._seq_glitch} 900"
        self._escrever(f"GLITCH 1 {campos}")
        if self._esperar(f"GACK 1 {campos}", 0.3, opcional=True):
            self._ultimo_ack_glitch = self.monotonic()
            self._erro_glitch = ""
        else:
            self._ultimo_ack_glitch = float("-inf")
            self._erro_glitch = "sem_confirmacao_glitch"

    def _descartar_resultados_som(self) -> None:
        for nome, (identidade, _) in self._resultados_som_pendentes.items():
            self._eventos_som_consumidos[nome] = max(self._eventos_som_consumidos.get(nome, 0), identidade)
        self._resultados_som_pendentes.clear()

    def _sincronizar_som(self, rosto: tuple[int, int, int], *, pela_coreografia: bool = False) -> None:
        """Resultados atuais aguardam o intervalo; nenhuma tentativa é repetida."""
        if not self._som_suportado:
            return
        agora = self.monotonic()
        tipo: int | None = None
        try:
            modo = self.companhia_getter()
            atividade = self.atividade_getter()
            falha_atual = projetar_falha_operacional(atividade, agora=agora)
            for nome, projetor, codigo in (("envio", projetar_envio_operacional, 8),
                                           ("sucesso", projetar_sucesso_operacional, 1),
                                           ("falha", projetar_falha_operacional, 2)):
                if nome == "envio" and not self._som_envio_suportado:
                    continue
                evento = projetor(atividade, agora=agora)
                if evento and evento[0] > self._eventos_som_consumidos.get(nome, 0):
                    pendente = self._resultados_som_pendentes.get(nome)
                    if pendente is None or evento[0] > pendente[0]:
                        # Apenas ocorrências admitidas ainda frescas pelo owner.
                        # Um por tipo, prazo fixo; amostrar não o renova.
                        self._resultados_som_pendentes[nome] = (evento[0], agora + 2.5)
                pendente = self._resultados_som_pendentes.get(nome)
                if pendente and (agora >= pendente[1] or atividade.get("origem") != "atividade_operacional_observada"):
                    self._eventos_som_consumidos[nome] = max(self._eventos_som_consumidos[nome], pendente[0])
                    del self._resultados_som_pendentes[nome]
                elif pendente:
                    tipo = codigo  # Falha prevalece no conjunto acumulado.
            if (tipo is None and not pela_coreografia and not self._acordar_som_pendente and self._expressao_suportada
                    and modo.get("ativa") is True and modo.get("perfil_corporal") == "rodas_suspensas"
                    and not falha_atual):
                return  # Só o detalhe emocional aguarda a fase expressiva.
            pose = rosto[:2]
            if tipo is None and pose != self._ultima_emocao_sonora and pose[0] and pose[1] >= 2:
                tipo = {1: 3, 2: 4, 3: 5, 4: 5, 5: 7, 6: 6, 7: 3}.get(pose[0])
            self._ultima_emocao_sonora = pose
            acordando = self._acordar_som_pendente
            if acordando:
                self._acordar_som_pendente = False
                tipo = 0
            if tipo is None or agora - self._ultimo_envio_som < 2:
                return
            if not acordando and tipo in {1, 2, 8}:
                self._descartar_resultados_som()
            self._ultimo_envio_som = agora  # Consome antes do envio; ACK perdido não toca de novo.
            self._seq_som += 1
            campos = f"{self._sessao} {self._seq_som} {tipo}"
            self._escrever(f"SOUND 1 {campos}")
            self._erro_som = "aguardando_confirmacao_som"
            if self._esperar(f"SOUNDACK 1 {campos}", .3, opcional=True):
                self._ultimo_ack_som = self.monotonic()
                self._erro_som = ""
            elif not self._erro_som.startswith("ERROR 1 SOM_"):
                self._erro_som = "sem_confirmacao_som"
        except Exception as erro:
            self._erro_som = type(erro).__name__
        # Expressão sonora degradada não muda o receipt da ação nem o FACE.

    def expressar_gesto(self, estilo: int, fase: int, lado: int, duracao_ms: int, *,
                       validar_inicio: Callable[[], bool] | None = None,
                       tocar_som: bool = False) -> dict[str, Any]:
        """Detalhe visual temporário, confirmado após render; nunca concede motor."""
        if (any(type(v) is not int for v in (estilo, fase, lado, duracao_ms))
                or not 0 <= estilo <= 10 or not 0 <= fase <= 3 or lado not in {-1, 0, 1}
                or not 50 <= duracao_ms <= 6000):
            return {"ok": False, "motivo": "expressao_invalida"}
        with self._lock:
            if (not self._expressao_suportada or not self.diagnostico()["aplicacao_confirmada"]
                    or (validar_inicio is not None and not validar_inicio())):
                return {"ok": False, "motivo": "expressao_sem_sessao_ou_causa"}
            self._seq_expressao += 1
            campos = f"{self._sessao} {self._seq_expressao} {estilo} {fase} {lado} {duracao_ms}"
            self._erro_expressao = "aguardando_render"
            try:
                self._escrever(f"EXPR 1 {campos}")
                ok = self._esperar(f"EACK 1 {campos}", .35, opcional=True)
                if ok:
                    self._ultimo_ack_expressao = self.monotonic()
                    self._ultima_expressao = (estilo, fase, lado)
                    self._duracao_expressao_ms = duracao_ms
                self._erro_expressao = "" if ok else "sem_confirmacao_expressao"
                if ok and tocar_som:
                    self._sincronizar_som(self._confirmado or (0, 1, 0), pela_coreografia=True)
                return {"ok": ok, "confirmado": ok, "evidencia": "eack_render" if ok else "",
                        "motivo": self._erro_expressao, "prova_visual_humana": False}
            except Exception as erro:
                self._erro_expressao = type(erro).__name__
                return {"ok": False, "motivo": self._erro_expressao}

    def _sincronizar_presenca(self) -> None:
        if not self._expressao_suportada:
            return
        from mente_laylay.integracao.politicas_composicao import construir_estado_visual
        try:
            c = self.estado_getter()
            visual = construir_estado_visual(conversa_get=lambda k, p=None: c.get(k, p), plano_get=lambda: {})
            atenta = not visual["speaking"] and (self.interacao_getter() is True
                or visual["activity"] in {"listening", "thinking", "executing"})
        except Exception:
            atenta = True
        if atenta:
            self.expressar_gesto(9, 3, 0, 1200)
        elif self._atencao_anterior and self._ultima_expressao[:2] == (9, 3):
            self.expressar_gesto(0, 2, 0, 900)
        self._atencao_anterior = atenta

    def sincronizar(self) -> bool:
        """Uma amostra atual e um receipt correlacionado; nenhuma fila histórica."""
        if not self.porta and not self.autodetectar and self._config_wifi_path is None:
            return False
        with self._lock:
            try:
                if self._serial is None:
                    porta = self.porta
                    if self._config_wifi_path is not None:
                        self._ler_config_wifi()
                        if self._erro_wifi:
                            self._erro = self._erro_wifi
                            self._publicar()
                            return False
                        self._serial = self.abrir_tcp(self._config_wifi)
                        porta = self._config_wifi.endpoint
                    elif self.autodetectar:
                        candidatas = self.listar_portas()
                        if len(candidatas) != 1:
                            self._erro = "multiplos_esp32" if candidatas else "aguardando_esp32"
                            self._publicar()
                            return False
                        porta = candidatas[0]
                    if self._config_wifi_path is None:
                        self._serial = self.abrir_serial(porta)
                    self._porta_ativa = porta
                if self.monotonic() - self._ultimo_ack >= 2.5:
                    # A placa dorme e invalida a sessão após TTL. Uma pausa no
                    # supervisor precisa renovar antes de enviar a amostra atual.
                    if self._motor_em_pulso and self._motor_cancelar is not None:
                        self._motor_cancelar.set()
                    self._ultimo_ack = float("-inf")
                    self._sessao = secrets.token_hex(4)
                    self._descartar_resultados_som()
                    self._seq = 0
                    self._seq_atividade = 0
                    self._seq_glitch = self._seq_motor = self._seq_parada = 0
                    self._seq_som = 0
                    self._seq_expressao = 0
                    self._sensores_suportados = False
                    self._vigia_suportada = self._vigia_ativa = False
                    self._seq_vigia = 0
                    self._saude_suportada=None
                    self._saude_em=float("-inf")
                    self._sensores, self._protecao = {}, {}
                    self._sensores_em = float("-inf")
                    self._atencao_anterior = False
                    self._ultimo_ack_hack = float("-inf")
                    self._hack_suportado = False
                    self._rx.clear()
                    hello = f"HELLO 1 {self._sessao}"
                    self._escrever(hello)
                    self._esperar(f"READY 1 {self._sessao} SSD1306 128 64", 3.0, reenviar=hello)
                    self._escrever(f"CAPS 1 {self._sessao}")
                    self._hack_suportado = self._esperar(f"CAPS 1 {self._sessao} HACK1", 0.3, opcional=True)
                    self._erro_hack = "aguardando_ack" if self._hack_suportado else "firmware_sem_hack"
                    self._escrever(f"GCAPS 1 {self._sessao}")
                    self._glitch_suportado = self._esperar(f"GCAPS 1 {self._sessao} GLITCH1", 0.3, opcional=True)
                    self._erro_glitch = "aguardando_falha" if self._glitch_suportado else "firmware_sem_glitch"
                    self._escrever(f"MCAPS 1 {self._sessao}")
                    self._motor_suportado = self._esperar(f"MCAPS 1 {self._sessao} MOTOR1", 0.3, opcional=True)
                    self._erro_motor = "" if self._motor_suportado else "firmware_sem_motor"
                    self._escrever(f"LCAPS 1 {self._sessao}")
                    self._limite_motor_ms = 5000 if self._esperar(f"LCAPS 1 {self._sessao} LONGO1", .3, opcional=True) else 500
                    self._escrever(f"SCAPS 1 {self._sessao}")
                    self._som_suportado = self._esperar(f"SCAPS 1 {self._sessao} SOM1", .3, opcional=True)
                    if self._som_suportado:
                        self._escrever(f"SENCAPS 1 {self._sessao}")
                        self._som_envio_suportado = self._esperar(f"SENCAPS 1 {self._sessao} ENVIO1", .3, opcional=True)
                    self._erro_som = "aguardando_evento" if self._som_suportado else "firmware_sem_som"
                    self._escrever(f"ECAPS 1 {self._sessao}")
                    self._expressao_suportada = self._esperar(f"ECAPS 1 {self._sessao} OLHOS2", .3, opcional=True)
                    self._erro_expressao = "aguardando_evento" if self._expressao_suportada else "firmware_sem_expressao"
                    self._escrever(f"RCAPS 1 {self._sessao}")
                    self._rampa_suportada = self._esperar(f"RCAPS 1 {self._sessao} RAMPA1", .3, opcional=True)
                    self._escrever(f"DCAPS 1 {self._sessao}")
                    self._sensores_suportados = self._esperar(f"DCAPS 1 {self._sessao} SENSORES2", .3, opcional=True)
                    if self._sensores_suportados:
                        self._escrever(f"PCAPS 1 {self._sessao}")
                        self._vigia_suportada = self._esperar(f"PCAPS 1 {self._sessao} VIGIA1",.3,opcional=True)
                # Amostra depois do handshake: a mente pode ter mudado durante o boot.
                rosto = projetar_rosto(self.estado_getter())
                self._seq += 1
                campos = f"{self._sessao} {self._seq} {rosto[0]} {rosto[1]} {rosto[2]}"
                self._erro = "aguardando_ack"
                self._escrever(f"FACE 1 {campos} 3500")
                self._esperar(f"ACK 1 {campos}", 1.0)
                self._confirmado = rosto
                self._ultimo_ack = self.monotonic()
                self._erro = ""
                self._consultar_saude()
                self._sincronizar_vigia()
                self._consultar_sensores()
                self._sincronizar_atividade()
                self._sincronizar_falha()
                self._sincronizar_presenca()
                self._sincronizar_som(rosto)
                self._ultima_falha_relatada = ""
            except Exception as erro:
                if isinstance(erro, InterruptedError) and self._deve_parar():
                    # O shutdown pode chegar dentro de FACE/ACTIVITY. Preservar
                    # a porta até STOP e GOODNIGHT, sem abrir outra sessão.
                    self.encerrar()
                    return False
                self._erro = type(erro).__name__ + ":" + str(erro)[:100]
                self._ultimo_ack = float("-inf")
                self._fechar()
                if self.relatar_falha and not self._deve_parar() and self._erro != self._ultima_falha_relatada:
                    self.relatar_falha("rosto_oled", "sincronizacao_tcp" if self._config_wifi_path is not None else "sincronizacao_serial", erro=erro,
                                       classe="degradacao", impacto="rosto", fallback="rosto_local_dormindo")
                    self._ultima_falha_relatada = self._erro
                self._publicar()
                return False
            self._publicar()
            return True

    def _fechar(self) -> None:
        self._descartar_resultados_som()
        if self._motor_cancelar is not None:
            self._motor_cancelar.set()
            if self._serial is not None:
                try:
                    self._escrever("STOP")  # Corte adicional; sem promover envio a receipt.
                except Exception:
                    pass
        dispositivo, self._serial = self._serial, None
        self._sessao = ""
        self._ultimo_ack = float("-inf")
        self._confirmado = None
        self._porta_ativa = ""
        self._hack_suportado = False
        self._ultimo_ack_hack = float("-inf")
        self._hack_confirmado = False
        self._erro_hack = "desconectado"
        self._motor_suportado = self._glitch_suportado = False
        self._limite_motor_ms = 500
        self._rampa_suportada = False
        self._sensores_suportados = False
        self._vigia_suportada = self._vigia_ativa = False
        self._sensores, self._protecao = {}, {}
        self._sensores_em = float("-inf")
        self._ultimo_ack_glitch = float("-inf")
        self._motor_pwm_confirmado = self._motor_parada_confirmada = False
        self._erro_motor = self._erro_glitch = "desconectado"
        self._som_suportado = False
        self._som_envio_suportado = False
        self._expressao_suportada = False
        self._erro_expressao = "desconectado"
        self._ultimo_ack_som = float("-inf")
        self._erro_som = "desconectado"
        if dispositivo is not None:
            try:
                dispositivo.close()
            except Exception:
                pass

    def _receipt_motor(self, *, ok: bool, motivo: str, pwm: bool = False,
                       parada: bool = False, esquerdo: int = 0, direito: int = 0,
                       duracao: int = 0, cancelado: bool = False) -> dict[str, Any]:
        return {
            "ok": ok, "motivo": motivo, "aplicacao_pwm_confirmada": pwm,
            "parada_confirmada": parada, "pwm_esquerdo": esquerdo,
            "pwm_direito": direito, "duracao_ms": duracao,
            "evidencia": "mack_pwm_e_sack" if pwm and parada else "sack" if parada else "sem_receipt_completo",
            "prova_rotacao": False, "prova_parada_fisica": False,
            "cancelado": cancelado, "status": "cancelado" if cancelado else "sucesso" if ok else "falha_execucao",
            "interrompido_por_protecao": bool(self._risco_motor),
            "risco_detectado": self._risco_motor,
            "protecao": self._diagnostico_sensores() if self._sensores_suportados else {},
        }

    def _parar_corpo_conectado(self, *, durante_encerramento: bool = False) -> bool:
        if self._serial is None or not self._sessao:
            return False
        self._seq_parada += 1
        campos = f"{self._sessao} {self._seq_parada}"
        self._escrever(f"STOP 1 {campos}")
        return self._esperar(f"SACK 1 {campos}", 0.5, opcional=True, durante_encerramento=durante_encerramento)

    def parar_corpo(self) -> dict[str, Any]:
        """Parada prioritária: não precisa de autorização para iniciar tração."""
        cancelar = self._motor_cancelar
        if cancelar is not None:
            self._motor_parada_solicitada = True
            cancelar.set()
        with self._lock:
            # A operação pode ter mudado enquanto STOP aguardava o lock.
            if self._motor_cancelar is not None:
                self._motor_parada_solicitada = True
                self._motor_cancelar.set()
            try:
                if self._serial is None and not self.sincronizar():
                    return self._receipt_motor(ok=False, motivo="corpo_indisponivel")
                parada = self._parar_corpo_conectado()
                self._motor_parada_confirmada = parada
                self._erro_motor = "" if parada else "sem_confirmacao_parada"
                try:
                    self._publicar()
                except Exception:
                    pass
                return self._receipt_motor(ok=parada, motivo=self._erro_motor, parada=parada)
            except Exception as erro:
                self._fechar()
                return self._receipt_motor(ok=False, motivo=type(erro).__name__ + ":" + str(erro)[:100])

    def mover_corpo(self, pwm_esquerdo: int, pwm_direito: int, duracao_ms: int,
                    *, validar_inicio: Callable[[], bool] | None = None, suave: bool = False) -> dict[str, Any]:
        """Um pulso finito. Repetição/reconexão jamais reenviam MOTOR."""
        if (type(suave) is not bool or any(type(v) is not int for v in (pwm_esquerdo, pwm_direito, duracao_ms))
                or not -255 <= pwm_esquerdo <= 255 or not -255 <= pwm_direito <= 255
                or not 50 <= duracao_ms <= self._limite_motor_ms or (pwm_esquerdo == 0 and pwm_direito == 0)):
            return self._receipt_motor(ok=False, motivo="parametros_invalidos")
        cancelar = threading.Event()
        pwm = parada = False
        motivo = ""
        sessao_operacao = ""
        serial_operacao: Any = None
        with self._lock:
            if self._motor_cancelar is not None:
                return self._receipt_motor(ok=False, motivo="motor_ocupado")
            self._motor_cancelar = cancelar
            self._motor_em_pulso = self._motor_parada_solicitada = False
            self._motor_pwm_confirmado = self._motor_parada_confirmada = False
            self._risco_motor = ""
            try:
                if not self.sincronizar():
                    motivo = "corpo_indisponivel"
                elif not self._motor_suportado:
                    motivo = "firmware_sem_motor"
                elif suave and not self._rampa_suportada:
                    motivo = "firmware_sem_rampa"
                elif duracao_ms > self._limite_motor_ms:
                    motivo = "firmware_sem_movimento_longo"
                elif cancelar.is_set():
                    motivo = "movimento_cancelado"
                elif validar_inicio is not None and not validar_inicio():
                    motivo = "concessao_expirada_antes_do_motor"
                else:
                    self._seq_motor += 1
                    sessao_operacao, serial_operacao = self._sessao, self._serial
                    campos = f"{self._sessao} {self._seq_motor} {pwm_esquerdo} {pwm_direito} {duracao_ms}"
                    versao = 2 if suave else 1
                    self._escrever(f"MOTOR {versao} {campos}")
                    self._motor_em_pulso = True
                    pwm = self._esperar(f"MACK {versao} {campos}", 0.5, opcional=True,
                        cancelar=lambda: cancelar.is_set() or (validar_inicio is not None and not validar_inicio()))
                    motivo = ("" if pwm else "concessao_expirada_antes_do_motor"
                              if validar_inicio is not None and not validar_inicio() else "sem_confirmacao_pwm")
            except Exception as erro:
                motivo = type(erro).__name__ + ":" + str(erro)[:100]
        try:
            if pwm or self._risco_motor:
                # Solta o lock serial: STOP e heartbeats podem passar durante o pulso.
                prazo_movimento = time.monotonic() + duracao_ms / 1000 + .02
                prazo_reflexo = time.monotonic() + 3.3
                proxima_consulta = time.monotonic()
                proxima_face = time.monotonic() + .5
                while not cancelar.is_set():
                    if validar_inicio is not None and not validar_inicio():
                        motivo = "concessao_expirada_antes_do_motor"
                        cancelar.set()
                        break
                    if self._sensores_suportados and time.monotonic() >= proxima_consulta:
                        with self._lock:
                            self._consultar_sensores()
                            if time.monotonic() >= proxima_face:
                                if not self.sincronizar():
                                    motivo = "corpo_indisponivel"
                                    break
                                proxima_face = time.monotonic() + .5
                        proxima_consulta = time.monotonic() + .05
                    if self._risco_motor:
                        motivo = "interrompido_por_protecao:" + self._risco_motor
                        if not self._protecao.get("reflexo_ativo") or time.monotonic() >= prazo_reflexo:
                            break
                    elif time.monotonic() >= prazo_movimento:
                        break
                    cancelar.wait(.02 if self._risco_motor else min(.05, max(0, prazo_movimento - time.monotonic())))
        except Exception as erro:
            motivo = type(erro).__name__ + ":" + str(erro)[:100]
        finally:
            with self._lock:
                cancelado = self._motor_parada_solicitada
                sessao_alterada = bool(sessao_operacao and (
                    sessao_operacao != self._sessao or serial_operacao is not self._serial))
                try:
                    if self._motor_suportado or pwm:
                        parada = self._parar_corpo_conectado()
                        if pwm and not parada:
                            motivo = "sem_confirmacao_parada"
                except Exception as erro:
                    motivo = motivo or type(erro).__name__ + ":" + str(erro)[:100]
                    self._fechar()
                self._motor_cancelar = None
                self._motor_em_pulso = False
                if sessao_alterada:
                    motivo = "sessao_alterada"
                elif cancelado:
                    motivo = "movimento_cancelado"
                self._motor_pwm_confirmado, self._motor_parada_confirmada = pwm, parada
                self._erro_motor = motivo
                try:
                    self._publicar()
                except Exception:
                    pass  # Publicação diagnóstica não muda o receipt observado.
        return self._receipt_motor(ok=pwm and parada and not sessao_alterada and not cancelado and not motivo,
                                   motivo=motivo, pwm=pwm, parada=parada, cancelado=cancelado,
                                   esquerdo=pwm_esquerdo, direito=pwm_direito, duracao=duracao_ms)

    def executar(self, *, deve_parar: Callable[[], bool], aguardar_fn: Callable[[float], Any]) -> None:
        self._deve_parar = deve_parar
        if not self.porta and not self.autodetectar and self._config_wifi_path is None:
            self._publicar()
            return
        try:
            while not deve_parar():
                ok = self.sincronizar()
                if aguardar_fn(0.25 if ok else 3.0):
                    break
        finally:
            self.encerrar()

    def encerrar(self) -> None:
        # A animação de adormecer não adia o corte dos motores.
        if self._motor_cancelar is not None:
            self._motor_parada_solicitada = True
            self._motor_cancelar.set()
        with self._lock:
            if self._serial is not None:
                try:
                    self._parar_corpo_conectado(durante_encerramento=True)
                except Exception:
                    pass
            if self._serial is not None and self._expressao_suportada and self._sessao:
                self._seq_expressao += 1
                campos = f"{self._sessao} {self._seq_expressao}"
                try:
                    self._escrever(f"GOODNIGHT 1 {campos}")
                    self._esperar(f"NACK 1 {campos}", .3, opcional=True, durante_encerramento=True)
                except Exception:
                    pass  # Perda da sessão/TTL também conduz ao sono.
            self._fechar()
            self._ultimo_ack = float("-inf")
            self._erro = "encerrado"
        self._publicar()


def criar_rosto_oled_runtime(**kwargs: Any) -> RostoOledRuntime:
    preferir_usb = kwargs.pop("preferir_usb", False) is True
    porta = str(kwargs.pop("porta", os.environ.get("LAYLAY_ROSTO_PORTA", "AUTO"))).strip()
    automatico = porta.casefold() in {"", "auto"}
    desligado = porta.casefold() in {"off", "0", "desligado"}
    caminho_wifi = kwargs.pop("config_wifi_path", os.environ.get("LAYLAY_CORPO_WIFI_CONFIG", CAMINHO_CONFIGURACAO_WIFI))
    if automatico and not preferir_usb:
        try:
            config_wifi = carregar_configuracao_corpo_wifi(caminho_wifi)
        except ConfiguracaoCorpoWifiInvalida:
            # Nunca substituir configuração inválida por outra porta/owner.
            config_wifi = True
        if config_wifi is not None:
            kwargs["config_wifi_path"] = caminho_wifi
    kwargs["porta"] = "" if automatico or desligado else porta
    kwargs.setdefault("autodetectar", automatico and "config_wifi_path" not in kwargs)
    return RostoOledRuntime(**kwargs)
