"""Coleta prospectiva local: entrada não é rótulo, contexto não é autoridade."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
from typing import Any, Callable, Mapping

from .experiencias import BufferExperienciasNeurais


class ColetaEntradasNeurais:
    """Reutiliza escrita append-only; não depende de previsão nem de receipt."""

    def __init__(self, caminho: str | Path, *, estado: Any,
                 conversa_getter: Callable[[], str], teste_getter: Callable[[], bool],
                 ativo: bool = False, limite_bytes: int = 64 * 1024 * 1024) -> None:
        self.buffer = BufferExperienciasNeurais(caminho)
        self.estado = estado
        self.conversa_getter = conversa_getter
        self.teste_getter = teste_getter
        self.ativo = ativo
        self.limite_bytes = limite_bytes

    @staticmethod
    def _texto(texto: str, limite: int) -> dict:
        return {"texto": texto[:limite], "caracteres_originais": len(texto),
                "truncado": len(texto) > limite,
                "sha256_original": hashlib.sha256(texto.encode("utf-8")).hexdigest()}

    def preparar(self, entrada: Any, origem: str) -> dict | None:
        # Não serializar eventos, OCR, clipboard ou payloads estruturados como fala.
        if not self.ativo or not isinstance(entrada, str) or not entrada.strip():
            return None
        if str(origem).casefold() == "presenca":
            return None
        mental = dict(self.estado.mental)
        conversa_id = self.conversa_getter() or None
        teste = bool(self.teste_getter()) or str(origem).casefold() == "roteiro_teste"
        mensagens = []
        for m in list(self.estado.memoria_conversa.get("messages") or [])[-4:]:
            if isinstance(m, Mapping) and m.get("role") in {"user", "assistant"} and isinstance(m.get("content"), str):
                mensagens.append({"papel": m["role"], **self._texto(m["content"], 2000)})
        anterior = dict(mental.get("turno_atual") or {})
        return {
            "tipo": "entrada_prospectiva", "versao": 1, "capturada_em": time.time(),
            "entrada": self._texto(entrada, 16000),
            "fidelidade": "literal_recebido_na_composicao_antes_da_revisao",
            "origem_declarada": str(origem), "teste_declarado": teste,
            "origem_humana_certificada": False,
            "conversa_id": str(conversa_id) if conversa_id else None,
            "sessao_conversa_ts": mental.get("sessao_conversa_ts") or None,
            "contexto_anterior": {"turno_id": anterior.get("id"), "mensagens": mensagens,
                "fonte": "estado_compartilhado_antes_do_planejamento",
                "vinculo_mensagens_sessao_certificado": False, "autoriza_execucao": False},
            "anotacao": None, "origem_rotulo": "pendente", "particao": None,
            "requer_revisao": True, "apto_treino": False, "treino_permitido": False,
            "autoriza_execucao": False, "autoriza_promocao": False,
        }

    def registrar(self, captura: dict | None, turno: Mapping[str, Any] | None,
                  *, erro: str | None = None) -> None:
        if captura is None:
            return
        registro = dict(captura)
        registro.update(turno_id=(turno or {}).get("id"),
                        planejamento="falhou" if erro else "concluido", erro_tipo=erro)
        # Limite explícito: nunca apagar histórico para liberar espaço nem
        # interromper a conversa. A composição reporta a falha de observabilidade.
        with self.buffer._lock:
            tamanho = self.buffer.caminho.stat().st_size if self.buffer.caminho.exists() else 0
            estimado = len(json.dumps(registro, ensure_ascii=False).encode("utf-8")) + 256
            if tamanho + estimado > self.limite_bytes:
                raise OSError("limite_local_coleta_atingido")
            self.buffer._gravar(registro)
