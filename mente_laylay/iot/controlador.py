"""Controlador central: planeja, executa, valida e relata ações IoT."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from mente_laylay.iot.contratos import DispositivoIoT, ResultadoIoT
from mente_laylay.iot.protocolos.base import ProtocoloIoT
from mente_laylay.iot.registro import RegistroDispositivos
from mente_laylay.iot.seguranca import avaliar_acao


class ControladorIoT:
    def __init__(
        self,
        registro: RegistroDispositivos,
        protocolos: Iterable[ProtocoloIoT] = (),
        persistencia: Any = None,
    ) -> None:
        self.registro = registro
        self.persistencia = persistencia
        self.protocolos: Dict[str, ProtocoloIoT] = {}
        for protocolo in protocolos:
            self.registrar_protocolo(protocolo)

    def registrar_protocolo(self, protocolo: ProtocoloIoT) -> None:
        nome = str(getattr(protocolo, "nome", "") or "").strip().lower()
        if not nome:
            raise ValueError("Protocolo IoT precisa declarar um nome.")
        self.protocolos[nome] = protocolo

    def listar(self, ambiente: str = "") -> list[DispositivoIoT]:
        return self.registro.listar(ambiente)

    def executar(
        self,
        acao: str,
        alvo: str,
        *,
        ambiente: str = "",
        origem: str = "usuario",
        confirmado: bool = False,
        parametros: Dict[str, Any] | None = None,
    ) -> ResultadoIoT:
        resultado = self._executar(
            acao,
            alvo,
            ambiente=ambiente,
            origem=origem,
            confirmado=confirmado,
            parametros=parametros,
        )
        if self.persistencia is not None:
            try:
                self.persistencia.registrar_resultado(resultado, origem=origem)
            except Exception as exc:
                print(f"[IOT:PERSISTENCIA] Não consegui registrar o resultado: {exc}")
        return resultado

    def _executar(
        self,
        acao: str,
        alvo: str,
        *,
        ambiente: str = "",
        origem: str = "usuario",
        confirmado: bool = False,
        parametros: Dict[str, Any] | None = None,
    ) -> ResultadoIoT:
        acao_norm = str(acao or "").strip().lower()
        dispositivo = self.registro.resolver(alvo, ambiente)
        if dispositivo is None:
            return ResultadoIoT(False, "nao_encontrado", acao_norm, erro="dispositivo não encontrado")

        base = {
            "acao": acao_norm,
            "dispositivo": dispositivo.nome,
            "ambiente": dispositivo.ambiente,
            "protocolo": dispositivo.protocolo,
        }
        decisao = avaliar_acao(dispositivo, acao_norm, origem=origem, confirmado=confirmado)
        if decisao.confirmacao_necessaria:
            return ResultadoIoT(
                False,
                "confirmacao_necessaria",
                confirmado=False,
                erro=decisao.motivo,
                **base,
            )
        if not decisao.permitido:
            return ResultadoIoT(False, "bloqueado_por_seguranca", erro=decisao.motivo, **base)

        protocolo = self.protocolos.get(str(dispositivo.protocolo).lower())
        if protocolo is None:
            return ResultadoIoT(False, "protocolo_indisponivel", erro="adaptador não carregado", **base)

        anterior = protocolo.consultar_estado(dispositivo)
        acao_estado_explicito = acao_norm in {"ligar", "desligar"}
        if not anterior.disponivel and not acao_estado_explicito:
            return ResultadoIoT(False, "indisponivel", estado_anterior=None, erro=anterior.erro, **base)
        if anterior.disponivel and not anterior.ok and not acao_estado_explicito:
            return ResultadoIoT(False, "falha_consulta", estado_anterior=anterior.estado, erro=anterior.erro, **base)

        if acao_norm == "status":
            status = "estado_desconhecido" if anterior.estado is None else "ligado" if anterior.estado else "desligado"
            return ResultadoIoT(
                anterior.estado is not None,
                status,
                estado_anterior=anterior.estado,
                estado_atual=anterior.estado,
                confirmado=anterior.estado is not None,
                **base,
            )

        if acao_norm in {"ajustar_brilho", "ajustar_cor", "ajustar_branco"}:
            execucao = protocolo.definir_parametros(dispositivo, acao_norm, dict(parametros or {}))
            if not execucao.disponivel:
                return ResultadoIoT(
                    False, "indisponivel", estado_anterior=anterior.estado,
                    erro=execucao.erro, detalhes=dict(execucao.detalhes or {}), **base,
                )
            if not execucao.ok:
                return ResultadoIoT(
                    False, "falha_execucao", estado_anterior=anterior.estado,
                    estado_atual=execucao.estado, erro=execucao.erro,
                    detalhes=dict(execucao.detalhes or {}), **base,
                )
            status_parametro = {
                "ajustar_brilho": "brilho_ajustado",
                "ajustar_cor": "cor_ajustada",
                "ajustar_branco": "branco_ajustado",
            }[acao_norm]
            return ResultadoIoT(
                True,
                status_parametro,
                estado_anterior=anterior.estado,
                estado_atual=execucao.estado,
                confirmado=True,
                detalhes=dict(execucao.detalhes or {}),
                **base,
            )

        if acao_norm == "alternar":
            if anterior.estado is None:
                return ResultadoIoT(
                    False,
                    "estado_desconhecido",
                    estado_anterior=None,
                    erro="não é seguro alternar sem conhecer o estado atual",
                    **base,
                )
            desejado = not anterior.estado
        elif acao_norm == "ligar":
            desejado = True
        elif acao_norm == "desligar":
            desejado = False
        else:
            return ResultadoIoT(False, "acao_invalida", estado_anterior=anterior.estado, erro="ação desconhecida", **base)

        if anterior.ok and anterior.disponivel and anterior.estado is desejado:
            return ResultadoIoT(
                True,
                "ja_estava_ligado" if desejado else "ja_estava_desligado",
                estado_anterior=anterior.estado,
                estado_atual=anterior.estado,
                confirmado=True,
                **base,
            )

        execucao = protocolo.definir_estado(dispositivo, desejado)
        if not execucao.disponivel:
            return ResultadoIoT(False, "indisponivel", estado_anterior=anterior.estado, erro=execucao.erro, **base)
        if not execucao.ok:
            return ResultadoIoT(False, "falha_execucao", estado_anterior=anterior.estado, estado_atual=execucao.estado, erro=execucao.erro, **base)

        validacao = protocolo.consultar_estado(dispositivo)
        confirmado_real = validacao.ok and validacao.disponivel and validacao.estado is desejado
        if not confirmado_real:
            return ResultadoIoT(
                False,
                "falha_validacao",
                estado_anterior=anterior.estado,
                estado_atual=validacao.estado,
                erro=validacao.erro or "estado final não confirmou a ação",
                **base,
            )

        return ResultadoIoT(
            True,
            "ligado" if desejado else "desligado",
            estado_anterior=anterior.estado,
            estado_atual=validacao.estado,
            confirmado=True,
            **base,
        )
