r"""RED151-C3 — prova no runtime real da Laylay.

Objetivo
=======
Validar o candidato C1+C2 atravessando o mesmo launcher usado pelo chaos:

    executar_roteiro(...)
        -> nova execução de laylay.py
        -> --roteiro <este arquivo>
        -> entrada canônica da Laylay
        -> comandos prioritários reais
        -> pré-fluxo real
        -> FeedbackPendenteRuntime real
        -> operações musicais reais
        -> PlaylistRuntime/persistência real

A cadeia reproduz o bloco histórico 146 -> 151, adicionando apenas uma etapa
inicial para colocar uma fonte musical determinística em execução.

Segurança
=========
- playlists.json é salvo byte a byte antes do teste;
- VMZ e "caos sonora" são removidas apenas da fixture temporária;
- uma playlist-fonte RED151 é instalada temporariamente;
- ao final, playlists.json é restaurado byte a byte;
- um backup persistente permite recuperar o catálogo caso o processo seja
  interrompido depois da instalação da fixture;
- nenhum commit é criado;
- nenhum código de produção é modificado.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any

from cliente.executor_roteiro_laylay import executar_roteiro


# ============================================================================
# ROTEIRO
# ============================================================================

COMANDOS = """
Coloca a playlist red151 origem.
Coloca a playlist VMZ, pausa a música e me diz o estado dela.
Continua a música, passa para a próxima faixa e me diz qual está tocando.
Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela.
Vai para a próxima faixa e adiciona essa também na caos sonora.
Mostra a playlist caos sonora e depois apaga ela.
sim
"""


# O C3 deve ser rápido porque todos os turnos relevantes são operacionais ou
# pré-fluxo. Ainda assim, 60 s deixa margem para Chrome/YouTube sem repetir os
# 120 s históricos do RED151.
ATRASO_INICIAL_S = 5
TIMEOUT_RESPOSTA_S = 60
SILENCIAR_VOZ_DURANTE_TESTE = True
TIMEOUT_VOZ_S = 120
AGUARDAR_CONFIRMACAO_EXECUCAO = True
INTERVALO_ENTRE_COMANDOS_S = 0.0
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True


# ============================================================================
# FIXTURE MUSICAL REAL
# ============================================================================

PLAYLIST_FONTE = "red151 origem"

FAIXAS_FONTE = [
    {
        "url": "https://www.youtube.com/watch?v=C7d7capE-n4",
        "titulo": "Anny - SE EU TE PEDIR ft. Lucas A.R.T",
        "canal": "",
    },
    {
        "url": "https://www.youtube.com/watch?v=ZLzDMCS6pPY",
        "titulo": "Anny - VÍCIO DE AMOR ft. Chrono",
        "canal": "",
    },
    {
        "url": "https://www.youtube.com/watch?v=LNoulHM7Lms",
        "titulo": "Shaman - Amor de Primavera feat. Anny",
        "canal": "",
    },
]

_BACKUP_EXISTE = b"LAYLAY_RED151_C3_PLAYLIST_EXISTE\n"
_BACKUP_AUSENTE = b"LAYLAY_RED151_C3_PLAYLIST_AUSENTE\n"


def _chave_normalizada(valor: Any) -> str:
    return " ".join(str(valor or "").strip().casefold().split())


def _gravar_bytes_atomicos(caminho: Path, conteudo: bytes) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(
        f".{caminho.name}.red151-c3-{os.getpid()}.tmp"
    )
    try:
        temporario.write_bytes(conteudo)
        os.replace(temporario, caminho)
    finally:
        temporario.unlink(missing_ok=True)


def _caminho_backup(caminho: Path) -> Path:
    return caminho.with_name(f".{caminho.name}.red151-c3-backup")


def _restaurar_backup_persistente(caminho: Path) -> bool:
    backup = _caminho_backup(caminho)
    if not backup.is_file():
        return False

    bruto = backup.read_bytes()

    if bruto.startswith(_BACKUP_EXISTE):
        _gravar_bytes_atomicos(
            caminho,
            bruto[len(_BACKUP_EXISTE):],
        )
    elif bruto == _BACKUP_AUSENTE:
        caminho.unlink(missing_ok=True)
    else:
        raise RuntimeError(
            "backup persistente RED151-C3 inválido; "
            "o catálogo não será alterado automaticamente"
        )

    backup.unlink(missing_ok=True)
    return True


def _carregar_catalogo_bytes(bruto: bytes | None) -> dict[str, Any]:
    if bruto is None:
        return {}

    try:
        valor = json.loads(bruto.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise RuntimeError(
            "playlists.json inválido; C3 abortado antes de alterar o catálogo"
        ) from erro

    if not isinstance(valor, dict):
        raise RuntimeError(
            "playlists.json precisa conter um objeto JSON; "
            "C3 abortado antes de alterar o catálogo"
        )

    return dict(valor)


def _remover_chave_casefold(
    catalogo: dict[str, Any],
    alvo: str,
) -> None:
    alvo_norm = _chave_normalizada(alvo)
    for chave in list(catalogo):
        if _chave_normalizada(chave) == alvo_norm:
            catalogo.pop(chave, None)


def _preparar_fixture(caminho: Path) -> bytes | None:
    caminho = Path(caminho)

    # Se uma execução anterior morreu depois de instalar a fixture, recupera
    # primeiro o catálogo original.
    _restaurar_backup_persistente(caminho)

    original = caminho.read_bytes() if caminho.is_file() else None
    catalogo = _carregar_catalogo_bytes(original)

    # O alvo do RED precisa realmente começar inexistente.
    _remover_chave_casefold(catalogo, "vmz")

    # O alvo auxiliar usado pelos turnos equivalentes a 148-150 também começa
    # limpo para que os comandos sejam determinísticos.
    _remover_chave_casefold(catalogo, "caos sonora")

    # A fonte é controlada pelo próprio roteiro.
    _remover_chave_casefold(catalogo, PLAYLIST_FONTE)
    catalogo[PLAYLIST_FONTE] = [
        dict(item) for item in FAIXAS_FONTE
    ]

    serializado = (
        json.dumps(
            catalogo,
            ensure_ascii=False,
            indent=4,
        ).encode("utf-8")
        + b"\n"
    )

    backup = _caminho_backup(caminho)
    recibo = (
        _BACKUP_EXISTE + original
        if original is not None
        else _BACKUP_AUSENTE
    )

    _gravar_bytes_atomicos(backup, recibo)

    try:
        _gravar_bytes_atomicos(caminho, serializado)
    except BaseException:
        _restaurar_backup_persistente(caminho)
        raise

    return original


def _restaurar_fixture(
    caminho: Path,
    original: bytes | None,
) -> None:
    caminho = Path(caminho)

    if _restaurar_backup_persistente(caminho):
        return

    if original is None:
        caminho.unlink(missing_ok=True)
        return

    _gravar_bytes_atomicos(caminho, original)


# ============================================================================
# EVIDÊNCIAS
# ============================================================================

def _catalogo_atual(caminho: Path) -> dict[str, Any]:
    if not caminho.is_file():
        return {}
    return _carregar_catalogo_bytes(caminho.read_bytes())


def _achar_chave(
    catalogo: dict[str, Any],
    alvo: str,
) -> str:
    alvo_norm = _chave_normalizada(alvo)
    for chave in catalogo:
        if _chave_normalizada(chave) == alvo_norm:
            return str(chave)
    return ""


def _faixa_youtube_valida(item: Any) -> bool:
    if isinstance(item, dict):
        url = str(item.get("url") or "").strip()
    else:
        url = str(item or "").strip()

    return (
        "youtube.com/watch" in url
        or "youtu.be/" in url
    )


def _diretorios_resultado(raiz: Path) -> set[Path]:
    pasta = raiz / "resultados_testes"
    if not pasta.is_dir():
        return set()

    prefixo = f"{Path(__file__).stem}-"

    return {
        item.resolve()
        for item in pasta.glob(prefixo + "*")
        if item.is_dir()
    }


def _novo_resultado(
    antes: set[Path],
    depois: set[Path],
) -> Path | None:
    novos = list(depois - antes)
    if not novos:
        return None

    return max(
        novos,
        key=lambda p: p.stat().st_mtime_ns,
    )


def _ler_texto(caminho: Path) -> str:
    try:
        return caminho.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        return ""


def _validar_resultado_roteiro(pasta: Path | None) -> list[str]:
    erros: list[str] = []

    if pasta is None:
        return [
            "nenhuma pasta nova de resultados foi localizada "
            "para o roteiro C3"
        ]

    checkpoint = _ler_texto(pasta / "checkpoint.json")
    terminal = _ler_texto(pasta / "terminal.log")
    conversa = _ler_texto(pasta / "conversa.md")

    checkpoint_norm = checkpoint.casefold()
    terminal_norm = terminal.casefold()

    if '"status": "sem_resposta"' in checkpoint_norm:
        erros.append(
            "checkpoint contém status=sem_resposta"
        )

    if "sem resposta; checkpoint salvo" in terminal_norm:
        erros.append(
            "terminal registrou timeout/sem resposta"
        )

    # O ponto histórico que queremos observar no runtime real.
    if "[feedback playlist]" not in terminal_norm:
        erros.append(
            "terminal não registrou FEEDBACK PLAYLIST no turno final"
        )

    if "vmz" not in terminal_norm:
        erros.append(
            "terminal não associa o feedback final ao alvo VMZ"
        )

    if "tratado_pre_fluxo" not in terminal_norm:
        erros.append(
            "turno final não deixou evidência de tratamento pelo pré-fluxo"
        )

    # O arquivo de conversa precisa possuir alguma resposta depois do último
    # comando. Não tentamos validar frase exata, apenas observabilidade.
    if conversa and "sim" not in conversa.casefold():
        erros.append(
            "conversa.md não contém o comando final 'sim'"
        )

    return erros


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent
    arquivo_playlists = raiz / "playlists.json"

    print("RED151-C3 — RUNTIME REAL / 146→151")
    print("=" * 76)
    print(f"raiz ...............: {raiz}")
    print(f"playlists.json .....: {arquivo_playlists}")

    antes_resultados = _diretorios_resultado(raiz)

    original: bytes | None = None
    codigo_saida = 99
    erros: list[str] = []

    try:
        original = _preparar_fixture(arquivo_playlists)

        print("fixture .............: instalada")
        print(f"fonte ...............: {PLAYLIST_FONTE}")
        print("alvo VMZ ............: garantido ausente")
        print("caos sonora .........: garantida ausente")
        print()

        codigo_saida = executar_roteiro(
            __file__,
            retomar="--retomar" in sys.argv[1:],
        )

        depois_resultados = _diretorios_resultado(raiz)
        pasta_resultado = _novo_resultado(
            antes_resultados,
            depois_resultados,
        )

        catalogo = _catalogo_atual(arquivo_playlists)
        chave_vmz = _achar_chave(catalogo, "vmz")
        chave_caos = _achar_chave(catalogo, "caos sonora")

        if codigo_saida != 0:
            erros.append(
                f"laylay.py encerrou com código {codigo_saida}"
            )

        if not chave_vmz:
            erros.append(
                "VMZ não existe no playlists.json após o 'sim'"
            )
        else:
            itens_vmz = catalogo.get(chave_vmz)
            if not isinstance(itens_vmz, list) or not itens_vmz:
                erros.append(
                    "VMZ existe, mas não contém a faixa confirmada"
                )
            elif not any(
                _faixa_youtube_valida(item)
                for item in itens_vmz
            ):
                erros.append(
                    "VMZ não contém nenhuma faixa YouTube válida"
                )

        # O turno equivalente ao 150 deveria ter apagado a playlist auxiliar.
        if chave_caos:
            erros.append(
                "'caos sonora' ainda existe após o turno de exclusão"
            )

        erros.extend(
            _validar_resultado_roteiro(pasta_resultado)
        )

        print()
        print("EVIDÊNCIAS")
        print("-" * 76)
        print(f"codigo processo .....: {codigo_saida}")
        print(
            "resultado ............: "
            + (
                str(pasta_resultado)
                if pasta_resultado is not None
                else "<não localizado>"
            )
        )
        print(f"VMZ materializada ...: {bool(chave_vmz)}")

        if chave_vmz:
            itens_vmz = catalogo.get(chave_vmz)
            print(
                "faixas em VMZ .......: "
                f"{len(itens_vmz) if isinstance(itens_vmz, list) else 0}"
            )

        print(
            "caos sonora removida : "
            f"{not bool(chave_caos)}"
        )

        print()

        if erros:
            print("🔴 RED151-C3 — FALHOU")
            for indice, erro in enumerate(erros, start=1):
                print(f"  {indice}. {erro}")
        else:
            print("🟢 RED151-C3 — GREEN NO RUNTIME REAL")
            print()
            print("Contrato observado:")
            print("  oferta VMZ inexistente")
            print("      -> comandos intermediários")
            print("      -> sim")
            print("      -> CREATE VMZ confirmado")
            print("      -> ADD confirmado")
            print("      -> resposta observável")
            print("      -> sem timeout")
            print("      -> VMZ persistida com faixa")

    finally:
        try:
            _restaurar_fixture(
                arquivo_playlists,
                original,
            )
            print()
            print(
                "🧹 playlists.json original restaurado "
                "byte a byte."
            )
        except Exception as erro_restauro:
            print()
            print(
                "🔴 FALHA CRÍTICA AO RESTAURAR playlists.json: "
                f"{type(erro_restauro).__name__}: "
                f"{erro_restauro}"
            )
            raise

    raise SystemExit(1 if erros else 0)
