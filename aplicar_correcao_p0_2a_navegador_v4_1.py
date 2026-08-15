#!/usr/bin/env python3
"""P0.2A v4.1 — aba anterior canônica + proteção de domínios na fala.

Corrige dois bugs observados no roteiro de caos de 2026-08-15:
1. ``Volta para a anterior.`` executava e confirmava a troca, mas a fala
   terminada em ``google.com.`` era apagada pela higiene como se ``com`` fosse
   uma preposição pendurada.
2. ``SWITCH_PREVIOUS_TAB`` escolhia a aba inativa com ``lastAccessed`` mais
   recente, em vez da aba que realmente perdeu o foco imediatamente antes.

A correção não cria uma segunda memória de navegação. O evento existente
``active_tab_changed`` passa a alimentar ``ChromeEstadoRuntime``, que já possui
``aba_anterior_id``. A porta de leitura expõe esse valor de forma opcional e o
executor o prefere, mantendo ``lastAccessed`` apenas como fallback compatível.

O script:
- valida âncoras antes de alterar;
- cria backup em <raiz>/backups/p0_2a_navegador_v4_1/<timestamp>/;
- aplica mudanças idempotentes;
- cria regressões focadas com a frase real do bug;
- roda py_compile + testes v4/v4.1;
- restaura automaticamente qualquer arquivo alterado se algo falhar.
"""

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable


MARCADOR_HIGIENE = "P0_NAVEGADOR_DOMINIO_FALA_V4_1_20260815"
MARCADOR_ESTADO = "P0_NAVEGADOR_HISTORICO_CANONICO_V4_1_20260815"
MARCADOR_HANDLER = "P0_NAVEGADOR_EVENTO_HISTORICO_V4_1_20260815"
MARCADOR_RUNTIME = "P0_NAVEGADOR_PORTA_ANTERIOR_V4_1_20260815"
MARCADOR_REGISTRO = "P0_NAVEGADOR_REGISTRO_ANTERIOR_V4_1_20260815"
MARCADOR_EXECUTOR = "P0_NAVEGADOR_ANTERIOR_CANONICO_V4_1_20260815"
MARCADOR_COMPOSICAO = "P0_NAVEGADOR_COMPOSICAO_ANTERIOR_V4_1_20260815"
MARCADOR_TESTE = "P0_NAVEGADOR_TESTES_V4_1_20260815"

ARQUIVO_HIGIENE = Path("mente_laylay/personalidade/higiene_fala.py")
ARQUIVO_ESTADO = Path("mente_laylay/integracao/chrome_estado.py")
ARQUIVO_HANDLER = Path("mente_laylay/integracao/chrome_ws_handlers.py")
ARQUIVO_RUNTIME = Path("mente_laylay/integracao/navegador_runtime.py")
ARQUIVO_REGISTRO = Path("mente_laylay/integracao/registro_navegador.py")
ARQUIVO_EXECUTOR = Path("mente_laylay/autonomia/executor_navegador.py")
ARQUIVO_COMPOSICAO = Path("laylay.py")
ARQUIVO_TESTE = Path("tests/test_p0_2a_navegador_v4_1.py")
ARQUIVO_TESTE_V4 = Path("tests/test_p0_2a_navegador_v4.py")

ARQUIVOS_PRODUCAO = (
    ARQUIVO_HIGIENE,
    ARQUIVO_ESTADO,
    ARQUIVO_HANDLER,
    ARQUIVO_RUNTIME,
    ARQUIVO_REGISTRO,
    ARQUIVO_EXECUTOR,
    ARQUIVO_COMPOSICAO,
)

TESTE_V4_1 = r'''"""Regressões P0.2A v4.1: fala com domínio e aba anterior real."""

from __future__ import annotations

# P0_NAVEGADOR_TESTES_V4_1_20260815

from dataclasses import dataclass
from typing import Any

from mente_laylay.autonomia.executor_navegador import (
    DependenciasExecutorNavegador,
    _executar_aba_anterior,
)
from mente_laylay.integracao.chrome_estado import ChromeEstadoRuntime
from mente_laylay.integracao.chrome_ws_handlers import handle_action
from mente_laylay.integracao.navegador_runtime import NavegadorLeituraRuntime
from mente_laylay.integracao.registro_navegador import registrar_navegador_leitura
from mente_laylay.personalidade.higiene_fala import limpar_fala_operacional


def test_volta_para_anterior_nao_apaga_fala_terminada_em_google_com() -> None:
    fala = "Voltei para no navegador nao pesquise nada - Pesquisa Google — google.com."
    assert limpar_fala_operacional(fala) == fala


def test_higiene_preserva_dominio_com_br_e_continua_removendo_conector_solto() -> None:
    assert (
        limpar_fala_operacional("Voltei para Notícias — globo.com.br.")
        == "Voltei para Notícias — globo.com.br."
    )
    assert limpar_fala_operacional("Eu estava falando com.") == ""


def _aplicar_evento(
    estado: ChromeEstadoRuntime,
    *,
    tab_id: int,
    titulo: str,
    url: str,
) -> dict[str, Any]:
    updates = handle_action(
        {
            "action": "active_tab_changed",
            "tabId": tab_id,
            "title": titulo,
            "url": url,
        },
        estado.contexto_handler(),
    )
    estado.aplicar_updates(updates)
    return updates


def test_active_tab_changed_guarda_a_aba_que_realmente_perdeu_o_foco() -> None:
    estado = ChromeEstadoRuntime()

    _aplicar_evento(
        estado, tab_id=1, titulo="Pesquisa Google", url="https://google.com/",
    )
    _aplicar_evento(
        estado, tab_id=2, titulo="Wikipédia", url="https://pt.wikipedia.org/",
    )
    _aplicar_evento(
        estado, tab_id=3, titulo="Prime Video", url="https://primevideo.com/",
    )

    retrato = estado.snapshot()
    assert retrato["aba_ativa_id"] == 3
    assert retrato["aba_anterior_id"] == 2


def test_evento_repetido_na_mesma_aba_nao_destroi_o_historico() -> None:
    estado = ChromeEstadoRuntime()
    _aplicar_evento(estado, tab_id=1, titulo="Google", url="https://google.com/")
    _aplicar_evento(
        estado, tab_id=2, titulo="Wikipédia", url="https://pt.wikipedia.org/",
    )
    _aplicar_evento(
        estado, tab_id=3, titulo="Prime Video", url="https://primevideo.com/",
    )

    _aplicar_evento(
        estado,
        tab_id=3,
        titulo="Prime Video - detalhe",
        url="https://primevideo.com/detail",
    )
    retrato = estado.snapshot()
    assert retrato["aba_ativa_id"] == 3
    assert retrato["aba_anterior_id"] == 2


def test_identidade_da_aba_muda_historico_mesmo_com_titulo_e_url_iguais() -> None:
    estado = ChromeEstadoRuntime()
    _aplicar_evento(
        estado, tab_id=10, titulo="Nova guia", url="https://example.com/",
    )
    _aplicar_evento(
        estado, tab_id=11, titulo="Nova guia", url="https://example.com/",
    )
    retrato = estado.snapshot()
    assert retrato["aba_ativa_id"] == 11
    assert retrato["aba_anterior_id"] == 10


class _SolicitacoesFake:
    def conectado(self) -> bool:
        return True

    def solicitar_aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]:
        return {"tabId": 3, "title": "Prime Video", "url": "https://primevideo.com/"}


class _AmbienteFake:
    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        return []


def test_porta_leitura_expoe_historico_existente_sem_torna_lo_obrigatorio() -> None:
    estado = ChromeEstadoRuntime()
    estado.aplicar_updates({"aba_ativa_id": 3, "aba_anterior_id": 2})
    runtime = NavegadorLeituraRuntime(
        solicitacoes=_SolicitacoesFake(),
        ambiente=_AmbienteFake(),
        estado=estado,
    )
    registro = registrar_navegador_leitura(runtime)
    assert registro.aba_anterior_id() == 2

    class _ServicoLegado:
        def conectado(self) -> bool:
            return True

        def aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]:
            return {}

        def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
            return []

        def diagnostico(self) -> dict[str, Any]:
            return {}

    legado = registrar_navegador_leitura(_ServicoLegado())
    assert legado.aba_anterior_id() is None


@dataclass
class _LeituraExecutorFake:
    anterior: int | None
    ativo: int = 3

    def conectado(self) -> bool:
        return True

    def aba_anterior_id(self) -> int | None:
        return self.anterior

    def aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]:
        titulos = {
            1: ("Google", "https://google.com/"),
            2: ("Wikipédia", "https://pt.wikipedia.org/"),
            3: ("Prime Video", "https://primevideo.com/"),
        }
        titulo, url = titulos[self.ativo]
        return {
            "tabId": self.ativo,
            "windowId": 7,
            "active": True,
            "title": titulo,
            "url": url,
        }

    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        # Google tem lastAccessed maior de propósito. O histórico canônico
        # precisa vencer essa heurística e escolher Wikipédia (id=2).
        return [
            {
                "id": 1, "windowId": 7, "active": False,
                "title": "Google", "url": "https://google.com/",
                "lastAccessed": 9999,
            },
            {
                "id": 2, "windowId": 7, "active": False,
                "title": "Wikipédia", "url": "https://pt.wikipedia.org/",
                "lastAccessed": 100,
            },
            {
                "id": 3, "windowId": 7, "active": True,
                "title": "Prime Video", "url": "https://primevideo.com/",
                "lastAccessed": 500,
            },
        ]


class _OperacoesExecutorFake:
    def __init__(self, leitura: _LeituraExecutorFake) -> None:
        self.leitura = leitura
        self.focados: list[int] = []

    def focar_aba(self, tab_id: int) -> bool:
        self.focados.append(tab_id)
        self.leitura.ativo = tab_id
        return True


def _deps_executor(resultados: list[dict[str, Any]]) -> DependenciasExecutorNavegador:
    def marcar_resultado(status: str, **dados: Any) -> None:
        resultados.append({"status": status, **dados})

    return DependenciasExecutorNavegador(
        marcar_resultado=marcar_resultado,
        falar_por_status=lambda *_args, **_kwargs: None,
        abrir_url_com_validacao=lambda *_args, **_kwargs: False,
        alvo_preciso_para_aba=lambda valor: str(valor),
        esperar_aba_fechar=lambda *_args, **_kwargs: False,
        esperar_programa_fechar=lambda *_args, **_kwargs: False,
        executar_recursivo=lambda *_args, **_kwargs: False,
    )


def test_volta_para_a_anterior_prefere_historico_canonico_a_last_accessed() -> None:
    leitura = _LeituraExecutorFake(anterior=2)
    operacoes = _OperacoesExecutorFake(leitura)
    resultados: list[dict[str, Any]] = []
    falas: list[str] = []

    retorno = _executar_aba_anterior(
        {
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": operacoes,
            "falar_com_lipsync": lambda texto, *_args: falas.append(texto),
        },
        _deps_executor(resultados),
    )

    assert retorno.tratado is True
    assert operacoes.focados == [2]
    assert resultados[-1]["status"] == "aba_anterior_focada"
    assert resultados[-1]["confirmado"] is True
    assert falas == ["Voltei para Wikipédia — pt.wikipedia.org."]


def test_sem_historico_canonico_last_accessed_permanece_fallback_compativel() -> None:
    leitura = _LeituraExecutorFake(anterior=None)
    operacoes = _OperacoesExecutorFake(leitura)
    resultados: list[dict[str, Any]] = []

    retorno = _executar_aba_anterior(
        {
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": operacoes,
            "falar_com_lipsync": lambda *_args: None,
        },
        _deps_executor(resultados),
    )

    assert retorno.tratado is True
    assert operacoes.focados == [1]
    assert resultados[-1]["status"] == "aba_anterior_focada"
'''


def _raiz_valida(candidato: Path) -> bool:
    return all((candidato / relativo).is_file() for relativo in ARQUIVOS_PRODUCAO)


def localizar_raiz(explicita: str | None) -> Path:
    candidatos: list[Path] = []
    if explicita:
        candidatos.append(Path(explicita).expanduser())

    script_dir = Path(__file__).resolve().parent
    cwd = Path.cwd()
    candidatos.extend((script_dir, script_dir / "laylay", cwd, cwd / "laylay"))
    candidatos.extend(script_dir.parents)
    candidatos.extend(cwd.parents)

    vistos: set[Path] = set()
    for candidato in candidatos:
        try:
            resolvido = candidato.resolve()
        except OSError:
            continue
        if resolvido in vistos:
            continue
        vistos.add(resolvido)
        if _raiz_valida(resolvido):
            return resolvido
    raise FileNotFoundError(
        "Não encontrei a raiz do projeto. Use --root CAMINHO se necessário."
    )


def ler(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def substituir_unico(
    texto: str,
    antigo: str,
    novo: str,
    *,
    rotulo: str,
) -> str:
    quantidade = texto.count(antigo)
    if quantidade != 1:
        raise RuntimeError(
            f"{rotulo}: trecho esperado exatamente 1 vez; encontrei {quantidade}."
        )
    return texto.replace(antigo, novo, 1)


def patch_higiene(texto: str) -> str:
    if MARCADOR_HIGIENE in texto:
        return texto

    ancora_regex = '''_PALAVRA_PENDURADA = re.compile(
    r"\\b(?:e|mas|ou|porque|pois|que|de|do|da|dos|das|em|no|na|nos|nas|"
    r"com|sem|para|pra|por|pelo|pela|um|uma|uns|umas)\\s*[.!?…]*$",
    re.IGNORECASE,
)
_SUFIXO_APLICATIVO = re.compile(
'''
    regex_nova = '''_PALAVRA_PENDURADA = re.compile(
    r"\\b(?:e|mas|ou|porque|pois|que|de|do|da|dos|das|em|no|na|nos|nas|"
    r"com|sem|para|pra|por|pelo|pela|um|uma|uns|umas)\\s*[.!?…]*$",
    re.IGNORECASE,
)
# P0_NAVEGADOR_DOMINIO_FALA_V4_1_20260815
# Um host válido no fim da fala não é a preposição portuguesa ``com``.
# A regra é apenas uma exceção de fronteira: não altera URLs nem gramática.
_DOMINIO_FINAL = re.compile(
    r"(?<![\\w@])(?:https?://)?"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\\.)+"
    r"[a-z]{2,63}(?:[/?#][^\\s]*)?[.!?…]*$",
    re.IGNORECASE,
)
_SUFIXO_APLICATIVO = re.compile(
'''
    texto = substituir_unico(
        texto, ancora_regex, regex_nova, rotulo="higiene: regex de domínio",
    )

    antigo = '''    fala = re.sub(r"\\s+", " ", str(texto or "")).strip()
    if not fala or not _PALAVRA_PENDURADA.search(fala):
        return fala
'''
    novo = '''    fala = re.sub(r"\\s+", " ", str(texto or "")).strip()
    if (
        not fala
        or _DOMINIO_FINAL.search(fala)
        or not _PALAVRA_PENDURADA.search(fala)
    ):
        return fala
'''
    return substituir_unico(
        texto, antigo, novo, rotulo="higiene: proteção de domínio final",
    )


def patch_estado(texto: str) -> str:
    if MARCADOR_ESTADO in texto:
        return texto

    texto = substituir_unico(
        texto,
        '''        self._aba_ativa_setter = aba_ativa_setter
        self._aba_anterior_id: Any = None
''',
        '''        self._aba_ativa_setter = aba_ativa_setter
        # P0_NAVEGADOR_HISTORICO_CANONICO_V4_1_20260815
        # Identidade da aba ativa e imediatamente anterior pertencem ao mesmo
        # estado observado; não são inferidas pelo executor.
        self._aba_ativa_id: Any = None
        self._aba_anterior_id: Any = None
''',
        rotulo="chrome_estado: identidade ativa",
    )
    texto = substituir_unico(
        texto,
        '''                "aba_url_atual": url,
                "aba_anterior_id": self._aba_anterior_id,
''',
        '''                "aba_url_atual": url,
                "aba_ativa_id": self._aba_ativa_id,
                "aba_anterior_id": self._aba_anterior_id,
''',
        rotulo="chrome_estado: snapshot",
    )
    texto = substituir_unico(
        texto,
        '''            self._gravar_aba_ativa(titulo, url)
            if "aba_anterior_id" in updates:
''',
        '''            self._gravar_aba_ativa(titulo, url)
            if "aba_ativa_id" in updates:
                self._aba_ativa_id = updates.get("aba_ativa_id")
            if "aba_anterior_id" in updates:
''',
        rotulo="chrome_estado: aplicar identidade",
    )
    return texto


def patch_handler(texto: str) -> str:
    if MARCADOR_HANDLER in texto:
        return texto

    texto = substituir_unico(
        texto,
        '''    aba_titulo_atual = str(ctx.get("aba_titulo_atual") or "")
    aba_url_atual = str(ctx.get("aba_url_atual") or "")
    aba_anterior_id = ctx.get("aba_anterior_id")
''',
        '''    aba_titulo_atual = str(ctx.get("aba_titulo_atual") or "")
    aba_url_atual = str(ctx.get("aba_url_atual") or "")
    # P0_NAVEGADOR_EVENTO_HISTORICO_V4_1_20260815
    aba_ativa_id = ctx.get("aba_ativa_id")
    aba_anterior_id = ctx.get("aba_anterior_id")
''',
        rotulo="chrome_ws_handlers: ler identidade ativa",
    )

    antigo = '''    if action in ("url_update", "active_tab_changed") or (not action and "url" in data):
        nova_url = str(data.get("url") or "").strip()
        novo_titulo = str(data.get("title") or "").strip()

        mudou = False
'''
    novo = '''    if action in ("url_update", "active_tab_changed") or (not action and "url" in data):
        nova_url = str(data.get("url") or "").strip()
        novo_titulo = str(data.get("title") or "").strip()

        # ``active_tab_changed`` é a fonte causal da ordem de foco. A
        # identidade precisa ser registrada mesmo quando título/URL são iguais.
        if action == "active_tab_changed":
            novo_tab_id = data.get("tabId")
            if (
                isinstance(novo_tab_id, int)
                and not isinstance(novo_tab_id, bool)
                and novo_tab_id != aba_ativa_id
            ):
                if isinstance(aba_ativa_id, int) and not isinstance(aba_ativa_id, bool):
                    updates["aba_anterior_id"] = aba_ativa_id
                updates["aba_ativa_id"] = novo_tab_id

        mudou = False
'''
    texto = substituir_unico(
        texto, antigo, novo, rotulo="chrome_ws_handlers: histórico por ativação",
    )

    texto = substituir_unico(
        texto,
        '''            updates["aba_anterior_id"] = frm
            print(f"🔄 [Chrome] Troca de aba manual: {ft} ({frm}) → {tt} ({to})")
''',
        '''            updates["aba_anterior_id"] = frm
            if isinstance(to, int) and not isinstance(to, bool):
                updates["aba_ativa_id"] = to
            print(f"🔄 [Chrome] Troca de aba manual: {ft} ({frm}) → {tt} ({to})")
''',
        rotulo="chrome_ws_handlers: compatibilidade manual_tab_change",
    )
    return texto


def patch_runtime(texto: str) -> str:
    if MARCADOR_RUNTIME in texto:
        return texto

    texto = substituir_unico(
        texto,
        '''class NavegadorLeituraRuntime:
    def __init__(self, *, solicitacoes: Any, ambiente: Any) -> None:
        self.solicitacoes = solicitacoes
        self.ambiente = ambiente
''',
        '''class NavegadorLeituraRuntime:
    def __init__(
        self, *, solicitacoes: Any, ambiente: Any, estado: Any = None,
    ) -> None:
        self.solicitacoes = solicitacoes
        self.ambiente = ambiente
        # P0_NAVEGADOR_PORTA_ANTERIOR_V4_1_20260815
        # Estado é opcional para preservar composições e fakes antigos.
        self.estado = estado
''',
        rotulo="navegador_runtime: estado opcional",
    )

    texto = substituir_unico(
        texto,
        '''    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        return list(self.ambiente.listar_abas(timeout_s=timeout_s) or [])

    def diagnostico(self) -> dict[str, Any]:
''',
        '''    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        return list(self.ambiente.listar_abas(timeout_s=timeout_s) or [])

    def aba_anterior_id(self) -> int | None:
        snapshot = getattr(self.estado, "snapshot", None)
        if not callable(snapshot):
            return None
        try:
            valor = dict(snapshot() or {}).get("aba_anterior_id")
        except Exception:
            return None
        return (
            valor
            if isinstance(valor, int) and not isinstance(valor, bool)
            else None
        )

    def diagnostico(self) -> dict[str, Any]:
''',
        rotulo="navegador_runtime: leitura aba anterior",
    )
    return texto


def patch_registro(texto: str) -> str:
    if MARCADOR_REGISTRO in texto:
        return texto

    antigo = '''    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        abas = self.servico.listar_abas(timeout_s=timeout_s) or []
        return [dict(aba) for aba in abas if isinstance(aba, dict)]

    def diagnostico(self) -> dict[str, Any]:
'''
    novo = '''    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        abas = self.servico.listar_abas(timeout_s=timeout_s) or []
        return [dict(aba) for aba in abas if isinstance(aba, dict)]

    def aba_anterior_id(self) -> int | None:
        # P0_NAVEGADOR_REGISTRO_ANTERIOR_V4_1_20260815
        # Capacidade opcional: não entra em _LEITURAS e não quebra serviços
        # legados que implementam o contrato anterior.
        obter = getattr(self.servico, "aba_anterior_id", None)
        if not callable(obter):
            return None
        try:
            valor = obter()
        except Exception:
            return None
        return (
            valor
            if isinstance(valor, int) and not isinstance(valor, bool)
            else None
        )

    def diagnostico(self) -> dict[str, Any]:
'''
    return substituir_unico(
        texto, antigo, novo, rotulo="registro_navegador: capacidade opcional",
    )


def patch_executor(texto: str) -> str:
    if MARCADOR_EXECUTOR in texto:
        return texto

    antigo = '''    candidatos: list[tuple[float, Dict[str, Any]]] = []
    for aba in abas:
        tab_id = _id_aba(aba)
        if tab_id is None or tab_id == ativa_id or aba.get("active") is True:
            continue
        if janela_ativa is not None and aba.get("windowId") != janela_ativa:
            continue
        try:
            recencia = float(aba.get("lastAccessed") or 0.0)
        except (TypeError, ValueError):
            recencia = 0.0
        candidatos.append((recencia, aba))
    if not candidatos:
        deps.marcar_resultado(
            "aba_anterior_indisponivel", executou=False, confirmado=True,
        )
        _falar(ctx, "Não encontrei outra aba observada para voltar.", "calma", 1)
        return ResultadoDespacho.concluido(False)

    candidatos.sort(key=lambda item: item[0], reverse=True)
    anterior = candidatos[0][1]
'''
    novo = '''    # P0_NAVEGADOR_ANTERIOR_CANONICO_V4_1_20260815
    # A ordem de foco é publicada pelo WebSocket. ``lastAccessed`` continua
    # apenas como fallback para estado legado, inicialização ou aba já fechada.
    obter_anterior = getattr(leitura, "aba_anterior_id", None)
    try:
        anterior_id_canonico = (
            obter_anterior() if callable(obter_anterior) else None
        )
    except Exception:
        anterior_id_canonico = None
    if not (
        isinstance(anterior_id_canonico, int)
        and not isinstance(anterior_id_canonico, bool)
    ):
        anterior_id_canonico = None

    anterior = next(
        (
            aba for aba in abas
            if _id_aba(aba) == anterior_id_canonico
            and anterior_id_canonico != ativa_id
            and (
                janela_ativa is None
                or aba.get("windowId") == janela_ativa
            )
        ),
        {},
    )

    if not anterior:
        candidatos: list[tuple[float, Dict[str, Any]]] = []
        for aba in abas:
            tab_id = _id_aba(aba)
            if tab_id is None or tab_id == ativa_id or aba.get("active") is True:
                continue
            if janela_ativa is not None and aba.get("windowId") != janela_ativa:
                continue
            try:
                recencia = float(aba.get("lastAccessed") or 0.0)
            except (TypeError, ValueError):
                recencia = 0.0
            candidatos.append((recencia, aba))
        if not candidatos:
            deps.marcar_resultado(
                "aba_anterior_indisponivel", executou=False, confirmado=True,
            )
            _falar(
                ctx,
                "Não encontrei outra aba observada para voltar.",
                "calma",
                1,
            )
            return ResultadoDespacho.concluido(False)

        candidatos.sort(key=lambda item: item[0], reverse=True)
        anterior = candidatos[0][1]
'''
    return substituir_unico(
        texto, antigo, novo, rotulo="executor_navegador: anterior canônica",
    )


def patch_composicao(texto: str) -> str:
    if MARCADOR_COMPOSICAO in texto:
        return texto

    antigo = '''_navegador_leitura_runtime = _criar_navegador_leitura_runtime(
    solicitacoes=_chrome_solicitacoes,
    ambiente=_ambiente_navegacao_runtime,
)
'''
    novo = '''_navegador_leitura_runtime = _criar_navegador_leitura_runtime(
    solicitacoes=_chrome_solicitacoes,
    ambiente=_ambiente_navegacao_runtime,
    # P0_NAVEGADOR_COMPOSICAO_ANTERIOR_V4_1_20260815
    estado=_chrome_estado,
)
'''
    return substituir_unico(
        texto, antigo, novo, rotulo="laylay.py: compor estado do navegador",
    )


PATCHES: dict[Path, Callable[[str], str]] = {
    ARQUIVO_HIGIENE: patch_higiene,
    ARQUIVO_ESTADO: patch_estado,
    ARQUIVO_HANDLER: patch_handler,
    ARQUIVO_RUNTIME: patch_runtime,
    ARQUIVO_REGISTRO: patch_registro,
    ARQUIVO_EXECUTOR: patch_executor,
    ARQUIVO_COMPOSICAO: patch_composicao,
}


def validar_python(caminhos: Iterable[Path]) -> None:
    for caminho in caminhos:
        if caminho.suffix != ".py":
            continue
        ast.parse(ler(caminho), filename=str(caminho))


def executar(cmd: list[str], *, cwd: Path) -> None:
    print("▶", " ".join(cmd))
    concluido = subprocess.run(cmd, cwd=cwd, check=False)
    if concluido.returncode != 0:
        raise RuntimeError(
            f"comando falhou com código {concluido.returncode}: {' '.join(cmd)}"
        )


def criar_backup(
    raiz: Path,
    caminhos: Iterable[Path],
) -> tuple[Path, dict[Path, bool]]:
    instante = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = raiz / "backups" / "p0_2a_navegador_v4_1" / instante
    backup.mkdir(parents=True, exist_ok=False)
    existiam: dict[Path, bool] = {}
    for relativo in caminhos:
        origem = raiz / relativo
        existia = origem.is_file()
        existiam[relativo] = existia
        if existia:
            destino = backup / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origem, destino)
    return backup, existiam


def restaurar(
    raiz: Path,
    backup: Path,
    existiam: dict[Path, bool],
) -> None:
    for relativo, existia in existiam.items():
        destino = raiz / relativo
        copia = backup / relativo
        if existia:
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(copia, destino)
        elif destino.exists():
            destino.unlink()


def preparar_alteracoes(raiz: Path) -> dict[Path, str]:
    novos: dict[Path, str] = {}
    for relativo, patch in PATCHES.items():
        atual = ler(raiz / relativo)
        novos[relativo] = patch(atual)

    # O teste é deliberadamente recriado para que a validação reflita esta
    # versão do patch mesmo numa segunda execução idempotente.
    novos[ARQUIVO_TESTE] = TESTE_V4_1
    for relativo, conteudo in novos.items():
        if relativo.suffix == ".py":
            ast.parse(conteudo, filename=str(relativo))
    return novos


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="raiz do projeto Laylay")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="valida âncoras e sintaxe sem escrever arquivos",
    )
    args = parser.parse_args()

    raiz = localizar_raiz(args.root)
    print(f"📁 Raiz: {raiz}")
    novos = preparar_alteracoes(raiz)

    alterados = [
        relativo
        for relativo, conteudo in novos.items()
        if not (raiz / relativo).is_file() or ler(raiz / relativo) != conteudo
    ]
    if not alterados:
        print("ℹ️ P0.2A v4.1 já está aplicada; executando validações.")
    else:
        print("🧩 Arquivos que serão alterados:")
        for relativo in alterados:
            print(f"   - {relativo}")

    if args.dry_run:
        print("✅ Dry-run: âncoras e sintaxe válidas; nada foi escrito.")
        return 0

    gerenciados = tuple(dict.fromkeys((*ARQUIVOS_PRODUCAO, ARQUIVO_TESTE)))
    backup, existiam = criar_backup(raiz, gerenciados)
    print(f"🛟 Backup: {backup}")

    try:
        for relativo, conteudo in novos.items():
            destino = raiz / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(conteudo, encoding="utf-8", newline="\n")

        validar_python(raiz / relativo for relativo in ARQUIVOS_PRODUCAO)
        validar_python((raiz / ARQUIVO_TESTE,))

        compilaveis = [
            str(relativo)
            for relativo in (*ARQUIVOS_PRODUCAO, ARQUIVO_TESTE)
            if relativo.suffix == ".py"
        ]
        executar(
            [sys.executable, "-m", "py_compile", *compilaveis],
            cwd=raiz,
        )

        testes = [str(ARQUIVO_TESTE)]
        if (raiz / ARQUIVO_TESTE_V4).is_file():
            testes.insert(0, str(ARQUIVO_TESTE_V4))
        executar(
            [sys.executable, "-m", "pytest", "-q", *testes],
            cwd=raiz,
        )
    except Exception as erro:
        print(f"❌ P0.2A v4.1 falhou: {type(erro).__name__}: {erro}")
        print("↩️ Restaurando os arquivos anteriores...")
        restaurar(raiz, backup, existiam)
        print("✅ Rollback concluído.")
        return 1

    print("✅ P0.2A v4.1 aplicada e validada.")
    print("   - domínios finais não somem da fala")
    print("   - active_tab_changed alimenta a aba anterior real")
    print("   - SWITCH_PREVIOUS_TAB prefere o histórico canônico")
    print("   - lastAccessed permanece como fallback compatível")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
