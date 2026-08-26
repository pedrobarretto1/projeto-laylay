"""Contrato tipado e sanitizado para o domínio IoT."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PortaIoT(Protocol):
    def detectar(
        self, texto: str, estado: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None: ...

    def executar(
        self, resultado: dict[str, Any], texto_original: str = "",
    ) -> dict[str, Any]: ...

    def retrato_para_mente(self, texto: str = "") -> dict[str, Any]: ...

    def diagnostico(self) -> dict[str, Any]: ...


_OPERACOES_OBRIGATORIAS = ("detectar", "executar", "retrato_para_mente")


@dataclass(frozen=True)
class RegistroIoT:
    """Expõe capacidades IoT sem transportar configuração de protocolo."""

    servico: PortaIoT = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroIoT":
        ausentes = tuple(
            nome for nome in _OPERACOES_OBRIGATORIAS
            if not callable(getattr(servico, nome, None))
        )
        if ausentes:
            raise RuntimeError(
                "serviço IoT inválido na composição; operações ausentes: "
                + ", ".join(ausentes)
            )
        return cls(servico=servico)

    def detectar(
        self, texto: str, estado: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        resultado = self.servico.detectar(texto, estado)
        return dict(resultado) if isinstance(resultado, dict) else None

    def executar(
        self, resultado: dict[str, Any], texto_original: str = "",
    ) -> dict[str, Any]:
        retorno = self.servico.executar(resultado, texto_original)
        return dict(retorno) if isinstance(retorno, dict) else {}

    def retrato_para_mente(self, texto: str = "") -> dict[str, Any]:
        retrato = dict(self.servico.retrato_para_mente(texto) or {})
        proibidos = {"configuracao", "credenciais", "device_id", "local_key", "secret"}
        dispositivos_sanitizados = []
        for dispositivo in retrato.get("dispositivos") or ():
            if isinstance(dispositivo, dict):
                dispositivo = dict(dispositivo)
                for chave in proibidos:
                    dispositivo.pop(chave, None)
                dispositivos_sanitizados.append(dispositivo)
        retrato["dispositivos"] = dispositivos_sanitizados
        return retrato

    def diagnostico(self) -> dict[str, Any]:
        metodo = getattr(self.servico, "diagnostico", None)
        if callable(metodo):
            bruto = dict(metodo() or {})
        else:
            retrato = self.retrato_para_mente()
            bruto = {
                "configurado": bool(retrato.get("dispositivos")),
                "provedor_disponivel": False,
                "total_dispositivos": len(retrato.get("dispositivos") or []),
            }
        permitidos = {
            "configurado", "modo", "provedor_disponivel", "total_dispositivos",
            "evidencia_recente", "credenciais_expostas", "autoriza_execucao",
        }
        return {chave: bruto[chave] for chave in permitidos if chave in bruto}


def registrar_iot(servico: Any) -> RegistroIoT:
    if isinstance(servico, RegistroIoT):
        return servico
    return RegistroIoT.criar(servico)
