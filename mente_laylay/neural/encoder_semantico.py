"""Encoder semântico ONNX opcional, carregado somente sob configuração explícita."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
import threading
from typing import Any, Iterable

from sklearn.feature_extraction.text import HashingVectorizer


@dataclass
class EncoderSemanticoONNX:
    pasta_artefatos: str | Path
    arquivo_modelo: str = "onnx/model_quint8_avx2.onnx"
    arquivo_tokenizer: str = "tokenizer.json"
    sha256_modelo: str = ""
    max_length: int = 128
    batch_size: int = 64
    _sessao: Any = field(default=None, init=False, repr=False, compare=False)
    _tokenizer: Any = field(default=None, init=False, repr=False, compare=False)
    _lock: Any = field(default=None, init=False, repr=False, compare=False)
    _hash_validado: bool = field(default=False, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.pasta_artefatos = str(Path(self.pasta_artefatos).resolve())
        self.sha256_modelo = str(self.sha256_modelo or "").strip().casefold()
        self.max_length = max(8, int(self.max_length))
        self.batch_size = max(1, int(self.batch_size))
        self._lock = threading.RLock()

    @property
    def caminho_modelo(self) -> Path:
        return Path(self.pasta_artefatos) / self.arquivo_modelo

    @property
    def caminho_tokenizer(self) -> Path:
        return Path(self.pasta_artefatos) / self.arquivo_tokenizer

    def validar_artefatos(self) -> bool:
        if not self.caminho_modelo.is_file():
            raise FileNotFoundError(self.caminho_modelo)
        if not self.caminho_tokenizer.is_file():
            raise FileNotFoundError(self.caminho_tokenizer)
        if self.sha256_modelo and not self._hash_validado:
            digest = sha256()
            with self.caminho_modelo.open("rb") as arquivo:
                for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
                    digest.update(bloco)
            if digest.hexdigest().casefold() != self.sha256_modelo:
                raise ValueError("SHA-256 do encoder semântico não confere")
            self._hash_validado = True
        return True

    @staticmethod
    def _carregar_dependencias() -> tuple[Any, Any, Any]:
        try:
            import numpy as np
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError as erro:
            raise RuntimeError(
                "encoder semântico requer numpy, onnxruntime e tokenizers"
            ) from erro
        return np, ort, Tokenizer

    def precarregar(self) -> bool:
        with self._lock:
            self.validar_artefatos()
            if self._sessao is not None and self._tokenizer is not None:
                return True
            _np, ort, Tokenizer = self._carregar_dependencias()
            tokenizer = Tokenizer.from_file(str(self.caminho_tokenizer))
            pad_id = tokenizer.token_to_id("<pad>")
            tokenizer.enable_truncation(max_length=self.max_length)
            tokenizer.enable_padding(
                pad_id=1 if pad_id is None else int(pad_id),
                pad_token="<pad>",
            )
            self._sessao = ort.InferenceSession(
                str(self.caminho_modelo),
                providers=["CPUExecutionProvider"],
            )
            self._tokenizer = tokenizer
            return True

    def codificar(self, textos: Iterable[str]) -> Any:
        lote = [str(texto or "").strip() for texto in textos]
        if not lote or any(not texto for texto in lote):
            raise ValueError("encoder semântico exige textos não vazios")
        self.precarregar()
        np, _ort, _Tokenizer = self._carregar_dependencias()
        blocos = []
        for inicio in range(0, len(lote), self.batch_size):
            codificados = self._tokenizer.encode_batch(
                lote[inicio : inicio + self.batch_size]
            )
            ids = np.asarray([item.ids for item in codificados], dtype=np.int64)
            mascara = np.asarray(
                [item.attention_mask for item in codificados],
                dtype=np.int64,
            )
            tipos = np.asarray(
                [item.type_ids for item in codificados],
                dtype=np.int64,
            )
            ocultos = self._sessao.run(
                None,
                {
                    "input_ids": ids,
                    "attention_mask": mascara,
                    "token_type_ids": tipos,
                },
            )[0]
            pesos = mascara[..., None].astype(np.float32)
            vetores = (ocultos * pesos).sum(axis=1) / np.clip(
                pesos.sum(axis=1),
                1.0,
                None,
            )
            vetores /= np.clip(
                np.linalg.norm(vetores, axis=1, keepdims=True),
                1e-12,
                None,
            )
            blocos.append(vetores.astype(np.float32))
        return np.vstack(blocos)

    def __getstate__(self) -> dict[str, Any]:
        estado = dict(self.__dict__)
        estado["_sessao"] = None
        estado["_tokenizer"] = None
        estado["_lock"] = None
        # A validação pertence à leitura corrente do artefato externo. Não
        # persista um receipt antigo como se também provasse o arquivo futuro.
        estado["_hash_validado"] = False
        return estado

    def __setstate__(self, estado: dict[str, Any]) -> None:
        self.__dict__.update(estado)
        self._sessao = None
        self._tokenizer = None
        self._lock = threading.RLock()
        self._hash_validado = False


@dataclass
class EncoderSemanticoHibrido:
    """Combina sentido da frase com morfologia lexical local e determinística."""

    encoder_semantico: Any
    n_features_lexicais: int = 1024
    peso_semantico: float = 1.0
    peso_lexical: float = 1.0
    _vetorizador: Any = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.n_features_lexicais = max(128, int(self.n_features_lexicais))
        self.peso_semantico = float(self.peso_semantico)
        self.peso_lexical = float(self.peso_lexical)
        if self.peso_semantico <= 0.0 or self.peso_lexical <= 0.0:
            raise ValueError("pesos da representação híbrida devem ser positivos")
        self._vetorizador = HashingVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            n_features=self.n_features_lexicais,
            alternate_sign=False,
            norm="l2",
            lowercase=True,
            strip_accents="unicode",
        )

    def validar_artefatos(self) -> bool:
        validar = getattr(self.encoder_semantico, "validar_artefatos", None)
        if not callable(validar):
            raise TypeError("encoder semântico base não implementa validar_artefatos")
        return bool(validar())

    def precarregar(self) -> bool:
        precarregar = getattr(self.encoder_semantico, "precarregar", None)
        if not callable(precarregar):
            raise TypeError("encoder semântico base não implementa precarregar")
        return bool(precarregar())

    def codificar(self, textos: Iterable[str]) -> Any:
        _semanticos, hibridos = self.codificar_componentes(textos)
        return hibridos

    def codificar_componentes(self, textos: Iterable[str]) -> tuple[Any, Any]:
        """Retorna base e combinação sem executar o ONNX duas vezes."""
        lote = [str(texto or "").strip() for texto in textos]
        if not lote or any(not texto for texto in lote):
            raise ValueError("encoder híbrido exige textos não vazios")
        import numpy as np

        semanticos = np.asarray(
            self.encoder_semantico.codificar(lote),
            dtype=np.float32,
        )
        lexicais = self._vetorizador.transform(lote).toarray().astype(np.float32)
        hibridos = np.hstack((
            semanticos * self.peso_semantico,
            lexicais * self.peso_lexical,
        ))
        return semanticos, hibridos
