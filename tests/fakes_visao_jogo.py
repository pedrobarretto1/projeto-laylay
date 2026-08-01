from __future__ import annotations

from typing import Any, Mapping


class VisaoJogoLeituraFake:
    def __init__(self, *, recente: bool = False, andamento: bool = False) -> None:
        self.recente = recente
        self.andamento = andamento
        self.textos: list[str] = []

    def em_andamento(self) -> bool:
        return self.andamento

    def tem_analise_recente(self, max_idade_s: float = 900.0) -> bool:
        return self.recente and max_idade_s >= 0

    def observar_texto_usuario(self, texto: str) -> dict[str, Any]:
        self.textos.append(texto)
        return {"observado": bool(texto)}

    def perfil_atual(self) -> dict[str, Any]:
        return {}

    def diagnostico(self) -> dict[str, Any]:
        return {
            "habilitado": True, "credencial_disponivel": True,
            "em_andamento": self.andamento, "analise_recente": self.recente,
            "contexto_jogo_ativo": False, "captura_persistida": False,
            "imagem_exposta": False, "autoriza_execucao": False,
        }


class VisaoJogoAnaliseFake:
    def __init__(self, *, resultado: bool = True) -> None:
        self.resultado = resultado
        self.chamadas: list[tuple[Any, ...]] = []

    def executar(self, params: Mapping[str, Any] | None) -> bool:
        self.chamadas.append(("executar", dict(params or {})))
        return self.resultado

    def aplicar_referencia_item(self, texto: str) -> bool:
        self.chamadas.append(("referencia", texto))
        return self.resultado

    def continuar_analise_recente(self, texto: str) -> bool:
        self.chamadas.append(("continuar", texto))
        return self.resultado

    def continuar_pendencia(
        self, texto: str, pendencia: Mapping[str, Any] | None,
    ) -> bool:
        self.chamadas.append(("pendencia", texto, dict(pendencia or {})))
        return self.resultado

    def processar_atualizacao_perfil(self, texto: str) -> bool:
        self.chamadas.append(("perfil", texto))
        return self.resultado

    def diagnostico(self) -> dict[str, Any]:
        return {
            "analise_disponivel": True, "continuidade_disponivel": True,
            "solicitacoes": len(self.chamadas), "aceitas": len(self.chamadas),
            "recusadas": 0, "falhas": 0, "captura_exposta": False,
            "prompt_exposto": False, "autoriza_execucao": False,
        }
