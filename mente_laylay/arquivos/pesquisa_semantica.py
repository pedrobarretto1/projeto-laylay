"""Pesquisa local de arquivos por nome, caminho, conteúdo, tipo e recência.

O índice vive apenas em memória, não envia conteúdo para serviços externos e
ignora arquivos grandes, binários e nomes com aparência de credencial.
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Iterable


EXTENSOES_TEXTO = frozenset({
    ".txt", ".md", ".py", ".json", ".toml", ".yaml", ".yml", ".ini",
    ".cfg", ".csv", ".log", ".html", ".htm", ".css", ".js", ".ts",
    ".tsx", ".jsx", ".xml", ".sql", ".ps1", ".bat", ".cmd", ".sh",
    ".java", ".c", ".h", ".cpp", ".hpp", ".cs", ".rs", ".go",
})
EXTENSOES_IMAGEM = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"})
PASTAS_IGNORADAS = frozenset({
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".idea", ".vscode", "node_modules", "dist", "build",
    ".venv", ".venv314", "venv", "env", "runtime_llm", "site-packages",
    "bin", "obj", "packages",
    "appdata", "$recycle.bin", "windowsapps",
})
TERMOS_VAZIOS = frozenset({
    "a", "ao", "aos", "aquele", "aquela", "arquivo", "arquivos", "as", "com",
    "da", "das", "de", "do", "documento", "documentos", "e", "em", "encontra",
    "encontrar", "esse", "esta", "estao", "fica", "falam", "falando", "me",
    "meu", "meus", "minha", "minhas", "no", "nos", "o", "onde", "os", "pasta",
    "por", "procura", "procurar", "que", "sobre", "um", "uma",
})
EXPANSOES = {
    "lampada": {"luz", "iot", "tuya", "brilho", "cor", "iluminacao"},
    "luz": {"lampada", "iot", "tuya", "brilho", "cor", "iluminacao"},
    "jogo": {"game", "gaming", "modo_jogo", "visao_jogo"},
    "avatar": {"sprite", "png", "emocao", "animacao", "gamebar"},
    "voz": {"fala", "tts", "audio", "speech"},
    "musica": {"playlist", "faixa", "youtube", "audio"},
    "memoria": {"contexto", "aprendizado", "mente", "sqlite"},
    "email": {"gmail", "mensagem", "notificacao"},
    "agenda": {"lembrete", "agendamento", "compromisso"},
}
PADRAO_SENSIVEL = re.compile(
    r"(?:^|[._-])(?:\.env|credential|credentials|secret|secrets|token|tokens|"
    r"password|passwd|senha|private[_-]?key|tinytuya|tuya[_-]?raw|devices)(?:[._-]|$)",
    flags=re.IGNORECASE,
)


def _normalizar(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-zA-Z0-9]+", " ", texto.casefold())
    return re.sub(r"\s+", " ", texto).strip()


def _tokens_consulta(consulta: str) -> tuple[str, ...]:
    vistos: list[str] = []
    for token in _normalizar(consulta).split():
        if len(token) < 2 or token in TERMOS_VAZIOS or token in vistos:
            continue
        vistos.append(token)
    return tuple(vistos[:12])


def _tipo_pedido(consulta: str) -> str:
    texto = _normalizar(consulta)
    if re.search(r"\b(?:imagem|imagens|foto|fotos|png|jpg|jpeg)\b", texto):
        return "imagem"
    if re.search(r"\b(?:codigo|script|python|javascript|programacao)\b", texto):
        return "codigo"
    if re.search(r"\b(?:texto|nota|documento|markdown|pdf)\b", texto):
        return "documento"
    return ""


def _eh_ontem(timestamp: float, agora: datetime) -> bool:
    try:
        data = datetime.fromtimestamp(float(timestamp)).date()
    except (OSError, OverflowError, TypeError, ValueError):
        return False
    return data == (agora.date() - timedelta(days=1))


class PesquisaSemanticaArquivosRuntime:
    """Índice local efêmero e pesquisador determinístico de arquivos."""

    def __init__(
        self,
        *,
        raizes: Iterable[str | os.PathLike[str]] | None = None,
        projeto_raiz: str | os.PathLike[str] | None = None,
        abrir_caminho: Callable[[str], Any] | None = None,
        relogio: Callable[[], float] = time.time,
        cache_ttl_s: float = 90.0,
        max_arquivos: int = 16000,
        max_tempo_indice_s: float = 4.0,
        max_bytes_texto: int = 262_144,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.relogio = relogio
        self.cache_ttl_s = max(5.0, float(cache_ttl_s))
        self.max_arquivos = max(100, int(max_arquivos))
        self.max_tempo_indice_s = max(0.2, float(max_tempo_indice_s))
        self.max_bytes_texto = max(4096, int(max_bytes_texto))
        self.log = log
        self.abrir_caminho = abrir_caminho or self._abrir_padrao
        self._lock = RLock()
        self._indice: list[dict[str, Any]] = []
        self._indice_ts = 0.0
        self._incompleto = False
        self._metricas = {
            "indexacoes": 0, "pesquisas": 0, "falhas": 0,
            "arquivos_indexados": 0, "cache_hits": 0,
        }

        candidatas: list[Path] = []
        if projeto_raiz:
            candidatas.append(Path(projeto_raiz))
        if raizes is None:
            home = Path.home()
            candidatas.extend(home / nome for nome in ("Downloads", "Desktop", "Documents", "Pictures"))
        else:
            candidatas.extend(Path(item) for item in raizes)
        self._raizes = self._normalizar_raizes(candidatas)

    @staticmethod
    def _normalizar_raizes(candidatas: Iterable[Path]) -> tuple[Path, ...]:
        saida: list[Path] = []
        for candidata in candidatas:
            try:
                raiz = candidata.expanduser().resolve(strict=False)
            except (OSError, RuntimeError, ValueError):
                continue
            if not raiz.is_dir() or raiz in saida:
                continue
            saida.append(raiz)
        return tuple(saida)

    @staticmethod
    def _abrir_padrao(caminho: str) -> bool:
        iniciador = getattr(os, "startfile", None)
        if not callable(iniciador):
            return False
        iniciador(caminho)
        return True

    def _permitido(self, caminho: Path) -> bool:
        try:
            resolvido = caminho.resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            return False
        return any(resolvido == raiz or raiz in resolvido.parents for raiz in self._raizes)

    def _ler_texto(self, caminho: Path, tamanho: int, sensivel: bool) -> str:
        if sensivel or caminho.suffix.casefold() not in EXTENSOES_TEXTO or tamanho > self.max_bytes_texto:
            return ""
        try:
            with caminho.open("r", encoding="utf-8", errors="replace") as arquivo:
                return arquivo.read(self.max_bytes_texto)
        except (OSError, UnicodeError):
            return ""

    def _construir_indice(self) -> list[dict[str, Any]]:
        inicio = time.monotonic()
        vistos: set[str] = set()
        indice: list[dict[str, Any]] = []
        incompleto = False
        for posicao, raiz in enumerate(self._raizes):
            subraizes_anteriores = [item for item in self._raizes[:posicao] if raiz in item.parents]
            for diretorio, pastas, arquivos in os.walk(raiz, topdown=True):
                pasta_atual = Path(diretorio)
                pastas[:] = [
                    nome for nome in pastas
                    if nome.casefold() not in PASTAS_IGNORADAS
                    and not nome.casefold().startswith("build_")
                    and not nome.casefold().endswith(".egg-info")
                    and not any((pasta_atual / nome).resolve(strict=False) == sub for sub in subraizes_anteriores)
                ]
                if time.monotonic() - inicio > self.max_tempo_indice_s or len(indice) >= self.max_arquivos:
                    incompleto = True
                    break
                for nome in arquivos:
                    caminho = pasta_atual / nome
                    try:
                        chave = str(caminho.resolve(strict=False)).casefold()
                        if chave in vistos or not self._permitido(caminho):
                            continue
                        vistos.add(chave)
                        stat = caminho.stat()
                        sensivel = bool(PADRAO_SENSIVEL.search(nome))
                        conteudo = self._ler_texto(caminho, int(stat.st_size), sensivel)
                        relativo = str(caminho.relative_to(raiz))
                        indice.append({
                            "caminho": str(caminho.resolve(strict=False)),
                            "nome": nome,
                            "extensao": caminho.suffix.casefold(),
                            "relativo": relativo,
                            "raiz": str(raiz),
                            "prioridade_raiz": max(0, len(self._raizes) - posicao),
                            "modificado": float(stat.st_mtime),
                            "tamanho": int(stat.st_size),
                            "sensivel": sensivel,
                            "nome_norm": _normalizar(caminho.stem),
                            "caminho_norm": _normalizar(relativo),
                            "conteudo": conteudo,
                            "conteudo_norm": _normalizar(conteudo),
                        })
                    except (OSError, RuntimeError, ValueError):
                        self._metricas["falhas"] += 1
            if incompleto:
                break
        self._incompleto = incompleto
        self._metricas["indexacoes"] += 1
        self._metricas["arquivos_indexados"] = len(indice)
        self.log(
            f"🔎 [ARQUIVOS:ÍNDICE] arquivos={len(indice)} "
            f"incompleto={incompleto} tempo={time.monotonic() - inicio:.2f}s"
        )
        return indice

    def _obter_indice(self, *, forcar: bool = False) -> list[dict[str, Any]]:
        agora = self.relogio()
        with self._lock:
            if self._indice and not forcar and agora - self._indice_ts < self.cache_ttl_s:
                self._metricas["cache_hits"] += 1
                return list(self._indice)
            self._indice = self._construir_indice()
            self._indice_ts = agora
            return list(self._indice)

    @staticmethod
    def _trecho(item: dict[str, Any], tokens: tuple[str, ...]) -> str:
        if item.get("sensivel"):
            return ""
        conteudo = re.sub(r"\s+", " ", str(item.get("conteudo") or "")).strip()
        if not conteudo:
            return ""
        normalizado = _normalizar(conteudo)
        posicao_norm = min(
            (normalizado.find(token) for token in tokens if normalizado.find(token) >= 0),
            default=0,
        )
        # A posição normalizada é apenas uma aproximação segura para escolher
        # uma janela legível no texto original.
        inicio = max(0, posicao_norm - 80)
        return conteudo[inicio:inicio + 240].strip()

    def pesquisar(
        self,
        consulta: str,
        *,
        limite: int = 5,
        forcar_indice: bool = False,
        somente_projeto: bool = False,
    ) -> dict[str, Any]:
        consulta_limpa = re.sub(r"\s+", " ", str(consulta or "")).strip()[:240]
        tokens = _tokens_consulta(consulta_limpa)
        if not tokens:
            return {"ok": False, "status": "consulta_vazia", "consulta": consulta_limpa, "resultados": []}
        tipo = _tipo_pedido(consulta_limpa)
        consulta_norm = " ".join(tokens)
        expandidos = set()
        for token in tokens:
            expandidos.update(EXPANSOES.get(token, set()))
        pede_ontem = "ontem" in _normalizar(consulta_limpa).split()
        agora_dt = datetime.now()
        indice = self._obter_indice(forcar=forcar_indice)
        projeto = self._raizes[0] if self._raizes else None
        candidatos: list[dict[str, Any]] = []
        for item in indice:
            if somente_projeto and projeto and str(item.get("raiz")) != str(projeto):
                continue
            nome = str(item.get("nome_norm") or "")
            caminho = str(item.get("caminho_norm") or "")
            conteudo = str(item.get("conteudo_norm") or "")
            score = 0.0
            motivos: list[str] = []
            if consulta_norm and consulta_norm in nome:
                score += 14.0
                motivos.append("nome")
            elif consulta_norm and consulta_norm in caminho:
                score += 9.0
                motivos.append("caminho")
            elif consulta_norm and consulta_norm in conteudo:
                score += 6.0
                motivos.append("conteúdo")
            acertos_nome = sum(token in nome for token in tokens)
            acertos_caminho = sum(token in caminho for token in tokens)
            acertos_conteudo = sum(token in conteudo for token in tokens)
            if acertos_nome:
                score += acertos_nome * 7.0
                motivos.append("nome relacionado")
            if acertos_caminho:
                score += acertos_caminho * 3.5
                motivos.append("pasta relacionada")
            if acertos_conteudo:
                score += min(acertos_conteudo, 5) * 2.0
                motivos.append("texto relacionado")
            expansao_nome = sum(token in nome for token in expandidos)
            expansao_caminho = sum(token in caminho for token in expandidos)
            expansao_conteudo = sum(token in conteudo for token in expandidos)
            score += expansao_nome * 2.5 + expansao_caminho * 1.5 + min(expansao_conteudo, 4) * 0.8
            if expansao_nome or expansao_caminho or expansao_conteudo:
                motivos.append("significado relacionado")
            similaridade = SequenceMatcher(None, consulta_norm, nome).ratio()
            if similaridade >= 0.56:
                score += similaridade * 5.0
                motivos.append("nome semelhante")
            relevancia_textual = score
            extensao = str(item.get("extensao") or "")
            if tipo == "imagem" and extensao in EXTENSOES_IMAGEM and (relevancia_textual > 0 or pede_ontem):
                score += 5.0
                motivos.append("tipo imagem")
            elif tipo == "codigo" and relevancia_textual > 0 and extensao in EXTENSOES_TEXTO and extensao not in {".txt", ".md", ".csv", ".log"}:
                score += 4.0
                motivos.append("tipo código")
            elif tipo == "documento" and relevancia_textual > 0 and extensao in {".txt", ".md", ".pdf", ".docx", ".odt"}:
                score += 4.0
                motivos.append("tipo documento")
            if pede_ontem:
                if _eh_ontem(float(item.get("modificado") or 0.0), agora_dt):
                    score += 8.0
                    motivos.append("modificado ontem")
                else:
                    score -= 2.0
            # Testes continuam encontráveis, mas a implementação costuma ser
            # mais útil como primeiro resultado quando a consulta não pede um teste.
            pede_teste = bool({"test", "teste", "testes"} & set(tokens))
            caminho_partes = set(caminho.split())
            if not pede_teste and (
                str(item.get("nome") or "").casefold().startswith(("test_", "teste_"))
                or "tests" in caminho_partes
                or "testes" in caminho_partes
            ):
                score -= 18.0
                motivos.append("teste relacionado")
            if relevancia_textual <= 0 and not pede_ontem:
                continue
            score += min(1.0, float(item.get("prioridade_raiz") or 0) * 0.08)
            if score < 2.5:
                continue
            candidatos.append({
                "caminho": str(item.get("caminho") or ""),
                "nome": str(item.get("nome") or ""),
                "extensao": extensao,
                "score": round(score, 3),
                "motivos": list(dict.fromkeys(motivos))[:4],
                "trecho": self._trecho(item, tokens),
                "modificado": float(item.get("modificado") or 0.0),
                "sensivel": bool(item.get("sensivel")),
            })
        candidatos.sort(key=lambda item: (-float(item["score"]), -float(item["modificado"]), item["nome"].casefold()))
        resultados = candidatos[:max(1, min(10, int(limite or 5)))]
        self._metricas["pesquisas"] += 1
        return {
            "ok": True,
            "status": "encontrado" if resultados else "sem_resultados",
            "consulta": consulta_limpa,
            "resultados": resultados,
            "indice_incompleto": self._incompleto,
            "arquivos_indexados": len(indice),
            "somente_projeto": bool(somente_projeto),
        }

    def abrir(self, caminho: str) -> bool:
        alvo = Path(str(caminho or "")).expanduser()
        if not self._permitido(alvo) or not alvo.is_file():
            return False
        try:
            retorno = self.abrir_caminho(str(alvo.resolve(strict=False)))
            return retorno is not False
        except (OSError, RuntimeError, ValueError):
            self._metricas["falhas"] += 1
            return False

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            return {
                **dict(self._metricas),
                "raizes": len(self._raizes),
                "cache_ativo": bool(self._indice),
                "indice_incompleto": bool(self._incompleto),
                "somente_leitura": True,
                "envia_conteudo_externo": False,
            }


def criar_pesquisa_semantica_arquivos_runtime(**kwargs: Any) -> PesquisaSemanticaArquivosRuntime:
    return PesquisaSemanticaArquivosRuntime(**kwargs)
