r"""R1-RT2 — runtime real: contraste GENERICA x TIPADA cross-domain.

NÍVEL DA PROVA
==============
Este teste NÃO importa/monta coordenador, árbitro, planner ou resolvedor.

Ele lança:
    laylay.py --roteiro <este arquivo>

por meio do launcher oficial:
    cliente.executor_roteiro_laylay.executar_roteiro

O RoteiroTesteConversaRuntime envia cada frase pela entrada canônica usada
pelos terminais (_agendar_entrada_canonica), aguarda o resultado canônico
do turno e usa o avaliador semântico oficial.

POR QUE RT2 EXISTE
==================
O RT1 provou:
    FILE_READ(A) -> CREATE_FILE(B) -> "Leia de novo." -> FILE_READ(A)

Isso cobre sombreamento dentro do mesmo domínio (arquivos).

O RT2 prova uma fronteira diferente:
    FILE_READ(A)
        -> APP_OPEN(Calculadora), mais recente e reexecutável
        -> "De novo."      == APP_OPEN        [repetição GENERICA]
        -> "Leia de novo." == FILE_READ(A)    [repetição TIPADA / LER]

Portanto, no MESMO estado:
- a repetição genérica continua livre para usar a operação incompatível
  mais recente;
- a repetição tipada precisa aplicar a restrição lexical LER e recuperar
  a leitura compatível anterior.

Isso testa as invariâncias:
    fala atual = restrição
    repetição genérica != repetição tipada
    domínio ativo != autoridade para repetição tipada

IMPORTANTE SOBRE EMAIL_READ
===========================
A prova unitária/contratual R1-C2 já demonstrou que LER atravessa FILE_READ
e EMAIL_READ, e a R1-C3 prova fidelidade de EMAIL_READ(urgentes=True).

Este RT2 NÃO usa Gmail real de propósito:
- o executor EMAIL_READ de produção depende da configuração/cache/IMAP;
- o --roteiro não possui fixture literal para substituir esses callbacks;
- introduzir rede/credenciais aqui tornaria a prova não determinística.

Assim, RT2 é a prova de runtime real do mecanismo cross-domain da repetição,
enquanto C2/C3 continuam as provas específicas do domínio e-mail.

SEGURANÇA / ISOLAMENTO
======================
- Nenhum IoT é acionado.
- Nenhuma rede/Gmail é necessária.
- Só abre a Calculadora, uma ação local e reversível.
- Cria um único arquivo-fixture com nome exclusivo em ~/Downloads.
- Antes de iniciar, ABORTA se o fixture já existir.
- Ao terminar, remove o fixture SOMENTE se o conteúdo contiver o marcador
  exclusivo deste RT2. Caso contrário, preserva o arquivo.
- A Calculadora não é fechada automaticamente para não encerrar uma
  instância que já fosse do usuário.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

from cliente.executor_roteiro_laylay import executar_roteiro


ARQUIVO_A = "laylay_r1_rt2_cross_91c4e7.txt"
MARCADOR_A = "MARCADOR R1 RT2 CROSS 91C4E7"

# carregar_configuracao_roteiro() lê estas constantes via AST/literal_eval.
COMANDOS = (
    "Cria um arquivo chamado laylay_r1_rt2_cross_91c4e7.txt e escreve MARCADOR R1 RT2 CROSS 91C4E7.",
    "Leia o laylay_r1_rt2_cross_91c4e7.txt.",
    "Abre a calculadora.",
    "De novo.",
    "Leia de novo.",
)

EXPECTATIVAS_SEMANTICAS = {
    1: {
        "intents_any": ("CREATE_FILE",),
        "confirmado": True,
        "dominio": "arquivos",
        "nome": "rt2_cria_fixture_a",
    },
    2: {
        "intents_any": ("FILE_READ",),
        "confirmado": True,
        "fala_any": ("marcador r1 rt2 cross 91c4e7",),
        "dominio": "arquivos",
        "nome": "rt2_leitura_a_confirmada",
    },
    3: {
        "intents_any": ("APP_OPEN",),
        "intents_forbidden": (
            "FILE_READ",
            "IOT_CONTROL",
            "DELETE_ITEM",
            "FILE_TRANSACTION",
        ),
        "confirmado": True,
        "dominio": "apps",
        "nome": "rt2_app_vira_operacao_incompativel_mais_recente",
    },
    4: {
        "intents_any": ("APP_OPEN",),
        "intents_forbidden": (
            "FILE_READ",
            "CREATE_FILE",
            "IOT_CONTROL",
            "DELETE_ITEM",
            "FILE_TRANSACTION",
        ),
        "confirmado": True,
        "dominio": "apps",
        "nome": "rt2_guard_repeticao_generica_continua_no_app",
    },
    5: {
        "intents_any": ("FILE_READ",),
        "intents_forbidden": (
            "APP_OPEN",
            "CREATE_FILE",
            "IOT_CONTROL",
            "DELETE_ITEM",
            "FILE_TRANSACTION",
        ),
        "confirmado": True,
        "fala_any": ("marcador r1 rt2 cross 91c4e7",),
        "dominio": "arquivos",
        "nome": "r1_rt2_repeticao_tipificada_vence_cross_domain",
    },
}

ATRASO_INICIAL_S = 3.0
TIMEOUT_RESPOSTA_S = 120.0
SILENCIAR_VOZ_DURANTE_TESTE = True
TIMEOUT_VOZ_S = 240.0
AGUARDAR_CONFIRMACAO_EXECUCAO = True
INTERVALO_ENTRE_COMANDOS_S = 0.0
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True


def _fixture() -> tuple[Path, str]:
    return Path.home() / "Downloads" / ARQUIVO_A, MARCADOR_A


def _preflight() -> None:
    caminho, _ = _fixture()
    if caminho.exists():
        raise SystemExit(
            "\n❌ R1-RT2 abortado por segurança.\n"
            "Já existe fixture com o mesmo nome:\n"
            f"  - {caminho}\n"
            "Nenhum arquivo foi removido automaticamente antes da prova.\n"
        )


def _limpar_fixture() -> None:
    caminho, marcador = _fixture()
    if not caminho.exists():
        return
    try:
        texto = caminho.read_text(encoding="utf-8")
    except Exception as erro:
        print(
            "⚠️ [R1-RT2:CLEANUP] preservei fixture que não consegui validar "
            f"| caminho={caminho} | erro={type(erro).__name__}"
        )
        return
    if marcador.casefold() not in texto.casefold():
        print(
            "⚠️ [R1-RT2:CLEANUP] preservei arquivo porque o marcador "
            f"não confere | caminho={caminho}"
        )
        return
    try:
        caminho.unlink()
        print(f"🧹 [R1-RT2:CLEANUP] fixture removido: {caminho}")
    except OSError as erro:
        print(
            "⚠️ [R1-RT2:CLEANUP] não consegui remover fixture "
            f"| caminho={caminho} | erro={type(erro).__name__}"
        )


def _diretorio_resultado_mais_recente() -> Path | None:
    raiz = Path(__file__).resolve().parent
    pasta = raiz / "resultados_testes"
    prefixo = f"{Path(__file__).stem}-"
    if not pasta.is_dir():
        return None
    candidatos = [
        item
        for item in pasta.iterdir()
        if item.is_dir() and item.name.startswith(prefixo)
    ]
    if not candidatos:
        return None
    return max(candidatos, key=lambda item: item.stat().st_mtime)


def _avaliacao_verde(item: dict) -> bool:
    avaliacao = dict(item.get("avaliacao") or {})
    resultado = str(
        avaliacao.get("resultado_semantico") or ""
    ).strip().casefold()
    erros = list(avaliacao.get("erros_semanticos") or [])
    alertas = list(avaliacao.get("alertas_semanticos") or [])
    return resultado == "passou" and not erros and not alertas


def _imprimir_turno(indice_humano: int, item: dict) -> None:
    avaliacao = dict(item.get("avaliacao") or {})
    print(f"\n--- TURNO {indice_humano} ---")
    print(f"comando   : {item.get('comando')!r}")
    print(f"status    : {item.get('status')!r}")
    print(f"resposta  : {item.get('resposta')!r}")
    print(
        "avaliacao : "
        + json.dumps(avaliacao, ensure_ascii=False, sort_keys=True)
    )


def _imprimir_diagnostico_rt2() -> None:
    diretorio = _diretorio_resultado_mais_recente()
    if diretorio is None:
        print("⚠️ [R1-RT2] diretório de resultado não localizado.")
        return
    print(f"\n📁 [R1-RT2] resultado: {diretorio}")

    checkpoint = diretorio / "checkpoint.json"
    if not checkpoint.is_file():
        print("⚠️ [R1-RT2] checkpoint.json não encontrado.")
        return

    try:
        estado = json.loads(checkpoint.read_text(encoding="utf-8"))
    except Exception as erro:
        print(
            "⚠️ [R1-RT2] checkpoint ilegível "
            f"| erro={type(erro).__name__}"
        )
        return

    itens = [
        dict(item)
        for item in estado.get("itens") or []
        if isinstance(item, dict)
    ]
    if len(itens) < 5:
        print(f"❌ [R1-RT2] apenas {len(itens)} turnos registrados.")
        return

    print("\n" + "=" * 78)
    print("R1-RT2 — DIAGNÓSTICO DO CONTRASTE CROSS-DOMAIN")
    print("=" * 78)

    turno_generico = itens[3]
    turno_tipado = itens[4]
    _imprimir_turno(4, turno_generico)
    _imprimir_turno(5, turno_tipado)

    generico_verde = _avaliacao_verde(turno_generico)
    tipado_verde = _avaliacao_verde(turno_tipado)

    print("\n" + "-" * 78)
    print(
        "GENÉRICA ('De novo.')     : "
        + ("✅ VERDE — APP_OPEN preservado" if generico_verde else "❌ NÃO COMPROVADA")
    )
    print(
        "TIPADA ('Leia de novo.')  : "
        + ("✅ VERDE — FILE_READ(A) recuperado" if tipado_verde else "❌ NÃO COMPROVADA")
    )

    if generico_verde and tipado_verde:
        print(
            "\n✅ R1-RT2: CONTRASTE CROSS-DOMAIN COMPROVADO NO RUNTIME REAL.\n"
            "   A mesma continuidade diferencia repetição GENÉRICA de TIPADA/LER."
        )
    else:
        print(
            "\n❌ R1-RT2: O CONTRASTE CROSS-DOMAIN NÃO FOI TOTALMENTE COMPROVADO."
        )

    relatorio = diretorio / "relatorio_semantico.md"
    resumo = diretorio / "resumo.json"
    if relatorio.is_file():
        print(f"relatório : {relatorio}")
    if resumo.is_file():
        print(f"resumo    : {resumo}")


def main() -> int:
    _preflight()
    print("🧪 R1-RT2 — runtime real / contraste cross-domain")
    print("   entrada: laylay.py --roteiro → _agendar_entrada_canonica")
    print("   efeitos: um fixture isolado em Downloads + Calculadora")
    print("   turno 4: 'De novo.' precisa continuar APP_OPEN")
    print("   turno 5: 'Leia de novo.' precisa recuperar FILE_READ(A)")
    print(
        "   Gmail/IoT: deliberadamente fora desta prova para manter "
        "determinismo e isolamento."
    )

    try:
        return int(executar_roteiro(__file__))
    finally:
        _imprimir_diagnostico_rt2()
        _limpar_fixture()


if __name__ == "__main__":
    raise SystemExit(main())
