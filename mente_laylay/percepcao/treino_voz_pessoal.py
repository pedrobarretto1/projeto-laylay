"""Coleta e avaliação local de fala pessoal para adaptar o ouvido da Laylay."""

from __future__ import annotations

from collections import Counter, deque
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import unicodedata
import uuid
from typing import Any, Callable, Iterable

from mente_laylay.percepcao.dispositivos_audio import selecionar_dispositivo_audio


FRASES_TREINO_PADRAO = (
    "Laylay, liga a luz.",
    "Laylay, desliga a luz.",
    "Laylay, deixa a luz azul.",
    "Laylay, deixa a luz vermelha.",
    "Laylay, deixa a luz verde.",
    "Laylay, deixa a luz rosa.",
    "Laylay, deixa a luz roxa.",
    "Laylay, aumenta o brilho da luz.",
    "Laylay, diminui o brilho da luz.",
    "Laylay, deixa a luz mais clara.",
    "Laylay, deixa a luz mais escura.",
    "Laylay, liga o ventilador.",
    "Laylay, desliga o ventilador.",
    "Laylay, aumenta o volume.",
    "Laylay, diminui o volume.",
    "Laylay, pausa a música.",
    "Laylay, continua a música.",
    "Laylay, abre o navegador.",
)


def normalizar_transcricao(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", base)).strip()


def distancia_edicao_palavras(referencia: str, hipotese: str) -> tuple[int, int]:
    esperado = normalizar_transcricao(referencia).split()
    obtido = normalizar_transcricao(hipotese).split()
    anterior = list(range(len(obtido) + 1))
    for indice_ref, palavra_ref in enumerate(esperado, 1):
        atual = [indice_ref]
        for indice_hip, palavra_hip in enumerate(obtido, 1):
            atual.append(min(
                atual[-1] + 1,
                anterior[indice_hip] + 1,
                anterior[indice_hip - 1] + (palavra_ref != palavra_hip),
            ))
        anterior = atual
    return anterior[-1], len(esperado)


class DatasetVozPessoal:
    def __init__(self, raiz: str | os.PathLike[str]) -> None:
        self.raiz = Path(raiz)
        self.audios = self.raiz / "audios"
        self.manifesto = self.raiz / "manifesto.jsonl"

    def preparar(self) -> None:
        self.audios.mkdir(parents=True, exist_ok=True)

    def registros(self) -> list[dict[str, Any]]:
        if not self.manifesto.exists():
            return []
        saida = []
        for linha in self.manifesto.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(linha)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(item, dict) and item.get("audio") and item.get("texto"):
                saida.append(item)
        return saida

    def contagens(self) -> Counter[str]:
        return Counter(normalizar_transcricao(item["texto"]) for item in self.registros())

    def salvar(self, audio: Any, taxa: int, texto: str, *, soundfile_mod: Any) -> dict[str, Any]:
        self.preparar()
        identificador = uuid.uuid4().hex
        relativo = Path("audios") / f"{identificador}.wav"
        destino = self.raiz / relativo
        soundfile_mod.write(str(destino), audio, taxa, subtype="PCM_16")
        repeticao = self.contagens()[normalizar_transcricao(texto)] + 1
        registro = {
            "id": identificador,
            "audio": relativo.as_posix(),
            "texto": str(texto).strip(),
            "repeticao": repeticao,
            "divisao": "teste" if repeticao % 5 == 0 else "treino",
            "taxa": int(taxa),
            "criado_em": datetime.now(timezone.utc).isoformat(),
        }
        with self.manifesto.open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        return registro


def capturar_frase(
    *,
    sounddevice_mod: Any,
    numpy_mod: Any,
    indice: int,
    taxa: int,
    log: Callable[[str], Any] = print,
    deve_continuar: Callable[[], bool] | None = None,
) -> Any:
    """Espera a voz, grava até o silêncio e devolve áudio mono float32."""
    sd, np = sounddevice_mod, numpy_mod
    continuar = deve_continuar or (lambda: True)
    bloco_s = 0.10
    bloco = max(160, int(taxa * bloco_s))
    calibracao = []
    preroll = deque(maxlen=3)
    gravando = []
    voz_consecutiva = 0
    silencio = 0.0
    esperou = 0.0
    with sd.InputStream(
        device=indice, channels=1, samplerate=taxa, dtype="float32", blocksize=bloco,
    ) as stream:
        while continuar() and len(calibracao) < 8:
            dados, _ = stream.read(bloco)
            chunk = np.asarray(dados, dtype=np.float32).reshape(-1).copy()
            calibracao.append(float(np.sqrt(np.mean(np.square(chunk), dtype=np.float64))))
        ruido = max(0.0005, float(np.percentile(calibracao or [0.0], 30)))
        limiar = max(0.012, ruido * 1.8)
        log(f"Nível calibrado: ruído={ruido:.4f}, fala={limiar:.4f}. Pode falar.")
        while continuar() and esperou < 12.0:
            dados, _ = stream.read(bloco)
            chunk = np.asarray(dados, dtype=np.float32).reshape(-1).copy()
            rms = float(np.sqrt(np.mean(np.square(chunk), dtype=np.float64)))
            esperou += bloco_s
            if not gravando:
                preroll.append(chunk)
                voz_consecutiva = voz_consecutiva + 1 if rms >= limiar else 0
                if voz_consecutiva >= 2:
                    gravando = list(preroll)
                    log("Gravando...")
                continue
            gravando.append(chunk)
            silencio = silencio + bloco_s if rms < max(0.009, ruido * 1.3) else 0.0
            duracao = len(gravando) * bloco_s
            if (silencio >= 0.9 and duracao >= 0.6) or duracao >= 6.0:
                return np.concatenate(gravando).astype(np.float32)
    return np.asarray([], dtype=np.float32)


def selecionar_entrada_treino(sounddevice_mod: Any, preferencia: str = "") -> tuple[int, dict, int]:
    indice, info, _ = selecionar_dispositivo_audio(sounddevice_mod, "entrada", preferencia)
    taxa = 16000
    try:
        sounddevice_mod.check_input_settings(
            device=indice, channels=1, dtype="float32", samplerate=taxa,
        )
    except Exception:
        taxa = int(float(info.get("default_samplerate") or 44100))
    return indice, info, taxa


def frases_pendentes(
    dataset: DatasetVozPessoal,
    frases: Iterable[str],
    repeticoes: int,
) -> list[str]:
    contagens = dataset.contagens()
    saida = []
    for frase in frases:
        faltam = max(0, int(repeticoes) - contagens[normalizar_transcricao(frase)])
        saida.extend([frase] * faltam)
    return saida

