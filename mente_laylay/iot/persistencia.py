"""Persistência segura dos dispositivos e resultados do subsistema IoT."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from mente_laylay.iot.contratos import DispositivoIoT, ResultadoIoT
from mente_laylay.iot.registro import RegistroDispositivos


class PersistenciaIoT:
    """Adapta o contrato IoT ao armazenamento compartilhado da Laylay."""

    def __init__(self, memoria: Any) -> None:
        self.memoria = memoria

    @staticmethod
    def _dados_dispositivo(dispositivo: DispositivoIoT) -> dict[str, Any]:
        return {
            "nome": dispositivo.nome,
            "nome_amigavel": dispositivo.nome_amigavel,
            "tipo": dispositivo.tipo,
            "ambiente": dispositivo.ambiente,
            "protocolo": dispositivo.protocolo,
            "aliases": list(dispositivo.aliases),
            "capacidades": sorted(dispositivo.capacidades),
            "risco": dispositivo.risco,
            "configuracao": dispositivo.configuracao,
            "ativo": dispositivo.ativo,
        }

    @staticmethod
    def _dispositivo_salvo(dados: dict[str, Any]) -> DispositivoIoT:
        return DispositivoIoT(
            nome=str(dados.get("nome") or ""),
            nome_amigavel=str(dados.get("nome_amigavel") or dados.get("nome") or ""),
            tipo=str(dados.get("tipo") or "dispositivo"),
            ambiente=str(dados.get("ambiente") or "desconhecido"),
            protocolo=str(dados.get("protocolo") or ""),
            aliases=tuple(dados.get("aliases") or ()),
            capacidades=frozenset(dados.get("capacidades") or ()),
            risco=str(dados.get("risco") or "moderado"),
            configuracao=dict(dados.get("configuracao") or {}),
            ativo=bool(dados.get("ativo", True)),
        )

    def cadastrar(self, dispositivo: DispositivoIoT) -> dict[str, Any]:
        return self.memoria.salvar_dispositivo_iot(self._dados_dispositivo(dispositivo))

    def sincronizar(self, dispositivos: Iterable[DispositivoIoT]) -> None:
        for dispositivo in dispositivos:
            self.cadastrar(dispositivo)

    def carregar_registro(self, ambiente: str = "") -> RegistroDispositivos:
        itens = self.memoria.listar_dispositivos_iot(ambiente, somente_ativos=True)
        return RegistroDispositivos(self._dispositivo_salvo(item) for item in itens)

    def registrar_resultado(self, resultado: ResultadoIoT, *, origem: str = "usuario") -> None:
        if not resultado.dispositivo:
            return

        indisponivel = resultado.status in {
            "indisponivel",
            "protocolo_indisponivel",
            "nao_encontrado",
        }
        estado = {
            "status": resultado.status,
            "ligado": resultado.estado_atual,
            "disponivel": not indisponivel,
            "confirmado": bool(resultado.confirmado),
        }
        brilho = dict(resultado.detalhes or {}).get("brilho")
        if (
            isinstance(brilho, (int, float))
            and not isinstance(brilho, bool)
            and 1 <= int(brilho) <= 100
        ):
            estado["brilho"] = int(brilho)
        ultimo_contato = None if indisponivel else datetime.now().isoformat(" ")
        self.memoria.atualizar_estado_iot(
            resultado.dispositivo,
            estado,
            ultimo_contato=ultimo_contato,
        )
        detalhes = dict(resultado.detalhes or {})
        if resultado.erro:
            # Erros de bibliotecas externas podem ecoar configuração sensível.
            detalhes["houve_erro"] = True
        self.memoria.registrar_historico_iot(
            resultado.dispositivo,
            acao=resultado.acao,
            estado_anterior=resultado.estado_anterior,
            estado_resultante=resultado.estado_atual,
            status=resultado.status,
            origem=origem,
            detalhes=detalhes,
        )
