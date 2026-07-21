"""Reconhecimento acústico conservador dos comandos gravados por Pedro."""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import re
import threading
from typing import Any, Callable


PADRAO_ATIVACAO_PESSOAL = re.compile(
    r"^(?:laylay|lay|lai|leilei|lelei|leil[eêií]|l[eê]i?\s*[,.-]?\s*l[eê]i?)\b[\s,;:.-]*(.*)$",
    flags=re.IGNORECASE,
)


def extrair_comando_rotulado(texto: str) -> str:
    limpo = re.sub(r"\s+", " ", str(texto or "")).strip(" .!?;:")
    achou = PADRAO_ATIVACAO_PESSOAL.match(limpo)
    return str(achou.group(1) or "").strip(" .!?;:") if achou else ""


def extrair_caracteristicas(audio: Any, taxa: int, *, numpy_mod: Any = None) -> Any:
    """MFCC normalizado e deltas, reduzido no tempo para comparação rápida."""
    np = numpy_mod
    if np is None:
        import numpy as np_importado
        np = np_importado
    vetor = np.asarray(audio, dtype=np.float32).reshape(-1)
    taxa = max(8000, int(taxa or 16000))
    if taxa != 16000 and len(vetor):
        tamanho = max(1, round(len(vetor) * 16000 / taxa))
        vetor = np.interp(
            np.linspace(0, len(vetor), tamanho, endpoint=False),
            np.arange(len(vetor)), vetor,
        ).astype(np.float32)
        taxa = 16000
    quadro, salto = 400, 160
    if len(vetor) < quadro:
        vetor = np.pad(vetor, (0, quadro - len(vetor)))
    indices = np.arange(quadro)[None, :] + salto * np.arange(
        1 + (len(vetor) - quadro) // salto,
    )[:, None]
    quadros = vetor[indices] * np.hanning(quadro)
    energia = np.sqrt(np.mean(np.square(quadros), axis=1) + 1e-10)
    ativos = np.where(energia > max(0.005, float(np.percentile(energia, 20)) * 3.0))[0]
    if len(ativos):
        inicio = max(0, int(ativos[0]) - 3)
        fim = min(len(quadros), int(ativos[-1]) + 4)
        quadros = quadros[inicio:fim]

    espectro = np.abs(np.fft.rfft(quadros, 512)) ** 2
    frequencias = np.linspace(0, taxa / 2, espectro.shape[1])
    para_mel = lambda hz: 2595 * np.log10(1 + hz / 700)
    para_hz = lambda mel: 700 * (10 ** (mel / 2595) - 1)
    pontos = para_hz(np.linspace(para_mel(80), para_mel(7600), 32))
    bancos = []
    for indice in range(30):
        esquerda, centro, direita = pontos[indice:indice + 3]
        bancos.append(np.maximum(0, np.minimum(
            (frequencias - esquerda) / (centro - esquerda + 1e-9),
            (direita - frequencias) / (direita - centro + 1e-9),
        )))
    log_mel = np.log(np.maximum(espectro @ np.asarray(bancos).T, 1e-8))
    n = np.arange(30)[None, :]
    k = np.arange(1, 14)[:, None]
    dct = np.cos(np.pi / 30 * (n + 0.5) * k)
    mfcc = log_mel @ dct.T
    mfcc = (mfcc - mfcc.mean(axis=0)) / (mfcc.std(axis=0) + 1e-5)
    caracteristicas = np.concatenate([mfcc, np.gradient(mfcc, axis=0)], axis=1)[::2]
    return caracteristicas / (
        np.linalg.norm(caracteristicas, axis=1, keepdims=True) + 1e-6
    )


def distancia_dtw(a: Any, b: Any, *, numpy_mod: Any = None) -> float:
    np = numpy_mod
    if np is None:
        import numpy as np_importado
        np = np_importado
    custo = 1.0 - np.asarray(a) @ np.asarray(b).T
    linhas, colunas = custo.shape
    anterior = np.full(colunas + 1, np.inf)
    anterior[0] = 0.0
    faixa = max(abs(linhas - colunas) + 2, int(max(linhas, colunas) * 0.35))
    for linha in range(1, linhas + 1):
        atual = np.full(colunas + 1, np.inf)
        centro = round(linha * colunas / linhas)
        inicio = max(1, centro - faixa)
        fim = min(colunas, centro + faixa)
        for coluna in range(inicio, fim + 1):
            atual[coluna] = custo[linha - 1, coluna - 1] + min(
                atual[coluna - 1], anterior[coluna], anterior[coluna - 1],
            )
        anterior = atual
    return float(anterior[colunas] / (linhas + colunas))


class ReconhecedorVozPessoal:
    """Compara uma fala com um medóide acústico de cada comando conhecido."""

    def __init__(
        self,
        raiz_dados: str | Path,
        *,
        log: Callable[[str], Any] = print,
        limite_distancia: float = 0.30,
        margem_minima: float = 0.018,
    ) -> None:
        self.raiz = Path(raiz_dados)
        self.log = log
        self.limite_distancia = float(limite_distancia)
        self.margem_minima = float(margem_minima)
        self._prototipos: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._tentou_carregar = False

    def _carregar(self) -> None:
        with self._lock:
            if self._tentou_carregar:
                return
            self._tentou_carregar = True
            manifesto = self.raiz / "manifesto.jsonl"
            if not manifesto.exists():
                return
            import numpy as np
            import soundfile as sf
            grupos: dict[str, list[Any]] = defaultdict(list)
            for linha in manifesto.read_text(encoding="utf-8").splitlines():
                try:
                    item = json.loads(linha)
                except (json.JSONDecodeError, TypeError):
                    continue
                if item.get("divisao") != "treino":
                    continue
                comando = extrair_comando_rotulado(item.get("texto", ""))
                caminho = self.raiz / str(item.get("audio") or "")
                if not comando or not caminho.is_file():
                    continue
                try:
                    audio, taxa = sf.read(str(caminho), dtype="float32")
                    grupos[comando].append(extrair_caracteristicas(audio, taxa, numpy_mod=np))
                except Exception:
                    continue
            for comando, exemplos in grupos.items():
                if len(exemplos) < 3:
                    continue
                melhor = min(
                    range(len(exemplos)),
                    key=lambda i: sum(
                        distancia_dtw(exemplos[i], exemplos[j], numpy_mod=np)
                        for j in range(len(exemplos)) if j != i
                    ),
                )
                self._prototipos[comando] = exemplos[melhor]
            if self._prototipos:
                self.log(
                    f"🎙️ [VOZ PESSOAL] {len(self._prototipos)} comandos acústicos carregados."
                )

    def reconhecer(self, audio: Any, taxa: int = 16000) -> dict[str, Any] | None:
        self._carregar()
        if len(self._prototipos) < 2:
            return None
        import numpy as np
        atual = extrair_caracteristicas(audio, taxa, numpy_mod=np)
        ranking = sorted(
            (distancia_dtw(atual, prototipo, numpy_mod=np), comando)
            for comando, prototipo in self._prototipos.items()
        )
        distancia, comando = ranking[0]
        margem = ranking[1][0] - distancia
        aceito = distancia <= self.limite_distancia and margem >= self.margem_minima
        return {
            "aceito": aceito,
            "comando": comando,
            "distancia": round(float(distancia), 4),
            "margem": round(float(margem), 4),
        }
