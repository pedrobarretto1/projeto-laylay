"""Adaptador local Tuya isolado do restante da mente da Laylay."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

from mente_laylay.iot.configuracao import carregar_dispositivo_snapshot, carregar_variaveis
from mente_laylay.iot.contratos import DispositivoIoT, ResultadoProtocolo
from mente_laylay.iot.protocolos.base import ProtocoloIoT


ClienteFactory = Callable[..., Any]


class ProtocoloTuya(ProtocoloIoT):
    nome = "tuya"

    def __init__(
        self,
        *,
        cliente_factory: ClienteFactory | None = None,
        timeout: float = 3.0,
        tentativas: int = 2,
    ) -> None:
        self._cliente_factory = cliente_factory or self._criar_cliente_padrao
        self.timeout = max(0.5, float(timeout))
        self.tentativas = max(1, int(tentativas))

    @staticmethod
    def _criar_cliente_padrao(**dados: Any) -> Any:
        # Importação propositalmente tardia: TinyTuya fica restrito ao adaptador.
        import tinytuya

        classe = tinytuya.BulbDevice if dados.get("classe_tuya") == "bulb" else tinytuya.OutletDevice
        return classe(
            dev_id=dados["device_id"],
            address=dados["ip"],
            local_key=dados["local_key"],
            version=dados["version"],
            connection_timeout=dados["timeout"],
            persist=False,
            connection_retry_limit=dados["tentativas"],
            connection_retry_delay=0.1,
        )

    def _configuracao(self, dispositivo: DispositivoIoT) -> tuple[Dict[str, Any], str]:
        configuracao = dict(dispositivo.configuracao or {})
        referencias = dict(configuracao.get("variaveis") or {})
        valores, faltando = carregar_variaveis(
            referencias,
            obrigatorias=("device_id", "local_key", "ip"),
        )
        caminhos_snapshot = [
            str(configuracao.get("snapshot_path") or "").strip(),
            *[
                str(caminho or "").strip()
                for caminho in configuracao.get("snapshot_fallback_paths", ())
            ],
        ]
        candidatos_snapshot: list[tuple[float, int, Dict[str, str]]] = []
        for indice, caminho_snapshot in enumerate(caminhos_snapshot):
            if not caminho_snapshot:
                continue
            snapshot = carregar_dispositivo_snapshot(
                caminho_snapshot,
                nome=str(configuracao.get("snapshot_device_name") or ""),
                device_id=str(valores.get("device_id") or ""),
            )
            # Uma variável de ambiente explícita continua soberana e não pode
            # ser completada com dados pertencentes a outro dispositivo que
            # por acaso manteve o mesmo nome no aplicativo.
            if (
                valores.get("device_id")
                and snapshot.get("device_id")
                and snapshot["device_id"] != valores["device_id"]
            ):
                continue
            if not snapshot:
                continue
            path = Path(caminho_snapshot)
            if not path.is_absolute():
                path = Path.cwd() / path
            try:
                modificado = float(path.stat().st_mtime)
            except OSError:
                modificado = 0.0
            # O índice invertido preserva a preferência declarada quando dois
            # arquivos são cópias com a mesma data de modificação.
            candidatos_snapshot.append((modificado, -indice, snapshot))

        for _modificado, _ordem, snapshot in sorted(candidatos_snapshot, reverse=True):
            for chave, valor in snapshot.items():
                if not valores.get(chave):
                    valores[chave] = valor
            faltando = [chave for chave in ("device_id", "local_key", "ip") if not valores.get(chave)]
            if not faltando:
                break
        if faltando:
            return {}, "configuração Tuya incompleta: " + ", ".join(sorted(faltando))

        try:
            version = float(valores.get("version") or "3.4")
        except (TypeError, ValueError):
            return {}, "versão Tuya inválida"
        if version < 3.1 or version > 3.5:
            return {}, "versão Tuya fora da faixa suportada"

        dps = str(configuracao.get("dps_estado") or "1").strip()
        if not dps.isdigit():
            return {}, "DPS de estado Tuya inválido"

        return {
            "device_id": valores["device_id"],
            "local_key": valores["local_key"],
            "ip": valores["ip"],
            "version": version,
            "dps": dps,
            "timeout": self.timeout,
            "tentativas": self.tentativas,
            "classe_tuya": str(configuracao.get("classe_tuya") or "outlet").strip().lower(),
        }, ""

    def _cliente(self, dispositivo: DispositivoIoT) -> tuple[Any | None, Dict[str, Any], str]:
        dados, erro = self._configuracao(dispositivo)
        if erro:
            return None, {}, erro
        try:
            cliente = self._cliente_factory(**dados)
            if hasattr(cliente, "set_socketPersistent"):
                cliente.set_socketPersistent(False)
            if hasattr(cliente, "set_socketTimeout"):
                cliente.set_socketTimeout(self.timeout)
            if hasattr(cliente, "set_socketRetryLimit"):
                cliente.set_socketRetryLimit(self.tentativas)
            return cliente, dados, ""
        except Exception:
            return None, {}, "não consegui preparar a conexão Tuya"

    @staticmethod
    def _erro_resposta(resposta: Any) -> str:
        if not isinstance(resposta, dict):
            return "resposta Tuya inválida"
        if resposta.get("Error") or resposta.get("error"):
            return "dispositivo Tuya não respondeu corretamente"
        codigo = resposta.get("Err")
        if codigo not in (None, 0, "0", False):
            return "dispositivo Tuya retornou erro de protocolo"
        return ""

    def consultar_estado(self, dispositivo: DispositivoIoT) -> ResultadoProtocolo:
        cliente, dados, erro = self._cliente(dispositivo)
        if cliente is None:
            return ResultadoProtocolo(False, None, False, erro)
        try:
            resposta = cliente.status()
        except Exception:
            return ResultadoProtocolo(False, None, False, "dispositivo Tuya indisponível")

        erro_resposta = self._erro_resposta(resposta)
        if erro_resposta:
            return ResultadoProtocolo(False, None, False, erro_resposta)
        dps = resposta.get("dps") or {}
        estado = dps.get(dados["dps"])
        if estado is None and dados["dps"].isdigit():
            estado = dps.get(int(dados["dps"]))
        if not isinstance(estado, bool):
            return ResultadoProtocolo(
                True,
                None,
                True,
                "estado não identificado no DPS configurado",
                {"dps": dados["dps"]},
            )
        return ResultadoProtocolo(True, estado, True, detalhes={"dps": dados["dps"]})

    def definir_estado(self, dispositivo: DispositivoIoT, ligado: bool) -> ResultadoProtocolo:
        cliente, dados, erro = self._cliente(dispositivo)
        if cliente is None:
            return ResultadoProtocolo(False, None, False, erro)
        try:
            if dados.get("classe_tuya") == "bulb":
                resposta = cliente.turn_on() if ligado else cliente.turn_off()
            else:
                resposta = cliente.set_status(bool(ligado), switch=int(dados["dps"]))
        except Exception:
            return ResultadoProtocolo(False, None, False, "dispositivo Tuya indisponível")

        erro_resposta = self._erro_resposta(resposta)
        if erro_resposta:
            return ResultadoProtocolo(False, None, False, erro_resposta)
        return ResultadoProtocolo(True, bool(ligado), True, detalhes={"dps": dados["dps"]})

    def definir_parametros(
        self,
        dispositivo: DispositivoIoT,
        acao: str,
        parametros: Dict[str, Any],
    ) -> ResultadoProtocolo:
        cliente, dados, erro = self._cliente(dispositivo)
        if cliente is None:
            return ResultadoProtocolo(False, None, False, erro)
        if dados.get("classe_tuya") != "bulb":
            return ResultadoProtocolo(False, None, True, "dispositivo não aceita cor ou brilho")

        try:
            resposta_ligar = cliente.turn_on()
            erro_ligar = self._erro_resposta(resposta_ligar)
            if erro_ligar:
                return ResultadoProtocolo(False, None, False, erro_ligar)
            if acao == "ajustar_brilho":
                valor = int(parametros.get("valor"))
                if not 1 <= valor <= 100:
                    raise ValueError
                resposta = cliente.set_brightness_percentage(valor)
                detalhes = {"brilho": valor}
            elif acao == "ajustar_cor":
                rgb = tuple(int(item) for item in parametros.get("rgb", ()))
                if len(rgb) != 3 or any(item < 0 or item > 255 for item in rgb):
                    raise ValueError
                resposta = cliente.set_colour(*rgb)
                detalhes = {
                    "rgb": rgb,
                    "cor": str(parametros.get("cor") or "").strip(),
                    "brilho": max(1, round(max(rgb) * 100 / 255)),
                }
            elif acao == "ajustar_branco":
                brilho = int(parametros.get("brilho", 70))
                temperatura = int(parametros.get("temperatura", 50))
                if not 1 <= brilho <= 100 or not 0 <= temperatura <= 100:
                    raise ValueError
                resposta = cliente.set_white_percentage(brightness=brilho, colourtemp=temperatura)
                detalhes = {
                    "brilho": brilho,
                    "temperatura": temperatura,
                    "cor": str(parametros.get("cor") or "branco").strip(),
                }
            else:
                return ResultadoProtocolo(False, None, True, "parâmetro não suportado")
        except (TypeError, ValueError):
            return ResultadoProtocolo(False, None, True, "parâmetros inválidos")
        except Exception:
            return ResultadoProtocolo(False, None, False, "dispositivo Tuya indisponível")

        erro_resposta = self._erro_resposta(resposta)
        if erro_resposta:
            return ResultadoProtocolo(False, None, False, erro_resposta)
        return ResultadoProtocolo(True, True, True, detalhes=detalhes)
