r"""R1-RT1 — prova de runtime real da repetição tipada.

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

Sequência causal
================
1. APP_OPEN(Calculadora)             -> incompatível e reexecutável
2. CREATE_FILE(A, marcador ALFA)     -> arquivo A
3. FILE_READ(A)                      -> leitura que deve continuar repetível
4. CREATE_FILE(B, marcador BETA)     -> B vira a operação/arquivo mais recente
5. "Leia de novo."                   -> DEVE executar FILE_READ(A)

O turno 5 só é aceito se:
- existir FILE_READ no plano/resultado;
- não houver APP_OPEN/CREATE_FILE/IOT_CONTROL/DELETE_ITEM/FILE_TRANSACTION;
- a execução for confirmada;
- a resposta contiver o marcador exclusivo de A.

Isso testa a invariância:
    fala atual = restrição
    foco atual != última operação reexecutável compatível

Segurança / isolamento
======================
- Nenhum IoT é acionado.
- Só abre a Calculadora (ação local e reversível).
- Cria dois arquivos-fixture com nomes exclusivos em ~/Downloads.
- Antes de iniciar, ABORTA se qualquer fixture já existir.
- Ao terminar, remove um fixture SOMENTE se ele contiver o marcador que
  pertence a este RT1. Se o conteúdo não bater, preserva o arquivo.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

from cliente.executor_roteiro_laylay import executar_roteiro


ARQUIVO_A = "laylay_r1_rt1_a_7f9c2d.txt"
ARQUIVO_B = "laylay_r1_rt1_b_4d2e8a.txt"

MARCADOR_A = "MARCADOR R1 RT1 ALFA 7F9C2D"
MARCADOR_B = "MARCADOR R1 RT1 BETA 4D2E8A"


# IMPORTANTE:
# carregar_configuracao_roteiro() lê estas constantes via AST/literal_eval.
# Por isso COMANDOS e EXPECTATIVAS_SEMANTICAS precisam permanecer literais.
COMANDOS = (
    "Abre a calculadora.",
    "Cria um arquivo chamado laylay_r1_rt1_a_7f9c2d.txt e escreve MARCADOR R1 RT1 ALFA 7F9C2D.",
    "Leia o laylay_r1_rt1_a_7f9c2d.txt.",
    "Cria um arquivo chamado laylay_r1_rt1_b_4d2e8a.txt e escreve MARCADOR R1 RT1 BETA 4D2E8A.",
    "Leia de novo.",
)

EXPECTATIVAS_SEMANTICAS = {
    1: {
        "intents_any": ("APP_OPEN",),
        "confirmado": True,
        "dominio": "apps",
        "nome": "rt1_predecessor_incompativel_reexecutavel",
    },
    2: {
        "intents_any": ("CREATE_FILE",),
        "confirmado": True,
        "dominio": "arquivos",
        "nome": "rt1_cria_fixture_a",
    },
    3: {
        "intents_any": ("FILE_READ",),
        "confirmado": True,
        "fala_any": ("marcador r1 rt1 alfa 7f9c2d",),
        "dominio": "arquivos",
        "nome": "rt1_leitura_a_confirmada",
    },
    4: {
        "intents_any": ("CREATE_FILE",),
        "confirmado": True,
        "dominio": "arquivos",
        "nome": "rt1_b_sombreia_foco_de_arquivos",
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
        "fala_any": ("marcador r1 rt1 alfa 7f9c2d",),
        "dominio": "arquivos",
        "nome": "r1_rt1_repeticao_tipificada_preserva_file_read_a",
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


def _fixtures() -> tuple[tuple[Path, str], ...]:
    downloads = Path.home() / "Downloads"
    return (
        (downloads / ARQUIVO_A, MARCADOR_A),
        (downloads / ARQUIVO_B, MARCADOR_B),
    )


def _preflight() -> None:
    conflitos = [str(caminho) for caminho, _ in _fixtures() if caminho.exists()]
    if conflitos:
        linhas = "\n  - ".join(conflitos)
        raise SystemExit(
            "\n❌ R1-RT1 abortado por segurança.\n"
            "Já existe fixture com o mesmo nome:\n"
            f"  - {linhas}\n"
            "Nenhum arquivo foi removido automaticamente antes da prova.\n"
        )


def _limpar_fixtures() -> None:
    for caminho, marcador in _fixtures():
        if not caminho.exists():
            continue
        try:
            texto = caminho.read_text(encoding="utf-8")
        except Exception as erro:
            print(
                "⚠️ [R1-RT1:CLEANUP] preservei fixture que não consegui validar "
                f"| caminho={caminho} | erro={type(erro).__name__}"
            )
            continue

        if marcador.casefold() not in texto.casefold():
            print(
                "⚠️ [R1-RT1:CLEANUP] preservei arquivo porque o marcador "
                f"não confere | caminho={caminho}"
            )
            continue

        try:
            caminho.unlink()
            print(f"🧹 [R1-RT1:CLEANUP] fixture removido: {caminho}")
        except OSError as erro:
            print(
                "⚠️ [R1-RT1:CLEANUP] não consegui remover fixture "
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


def _imprimir_diagnostico_rt1() -> None:
    diretorio = _diretorio_resultado_mais_recente()
    if diretorio is None:
        print("⚠️ [R1-RT1] diretório de resultado não localizado.")
        return

    print(f"\n📁 [R1-RT1] resultado: {diretorio}")

    checkpoint = diretorio / "checkpoint.json"
    if not checkpoint.is_file():
        print("⚠️ [R1-RT1] checkpoint.json não encontrado.")
        return

    try:
        estado = json.loads(checkpoint.read_text(encoding="utf-8"))
    except Exception as erro:
        print(
            "⚠️ [R1-RT1] checkpoint ilegível "
            f"| erro={type(erro).__name__}"
        )
        return

    itens = [
        dict(item)
        for item in estado.get("itens") or []
        if isinstance(item, dict)
    ]
    if len(itens) < 5:
        print(f"❌ [R1-RT1] apenas {len(itens)} turnos registrados.")
        return

    turno = itens[4]
    avaliacao = dict(turno.get("avaliacao") or {})
    print("\n" + "=" * 78)
    print("R1-RT1 — DIAGNÓSTICO DO TURNO 5")
    print("=" * 78)
    print(f"comando   : {turno.get('comando')!r}")
    print(f"status    : {turno.get('status')!r}")
    print(f"resposta  : {turno.get('resposta')!r}")
    print(
        "avaliacao : "
        + json.dumps(avaliacao, ensure_ascii=False, sort_keys=True)
    )

    resultado_semantico = str(
        avaliacao.get("resultado_semantico") or ""
    ).strip().casefold()
    erros_semanticos = list(avaliacao.get("erros_semanticos") or [])
    alertas_semanticos = list(avaliacao.get("alertas_semanticos") or [])
    passou = (
        resultado_semantico == "passou"
        and not erros_semanticos
        and not alertas_semanticos
    )

    if passou:
        print("\n✅ R1-RT1: TURNO CRÍTICO SEMÂNTICAMENTE VERDE.")
    else:
        print(
            "\n❌ R1-RT1: TURNO CRÍTICO NÃO FOI COMPROVADO COMO VERDE "
            f"| resultado={resultado_semantico!r} "
            f"| erros={erros_semanticos!r} "
            f"| alertas={alertas_semanticos!r}"
        )

    relatorio = diretorio / "relatorio_semantico.md"
    resumo = diretorio / "resumo.json"
    if relatorio.is_file():
        print(f"relatório : {relatorio}")
    if resumo.is_file():
        print(f"resumo    : {resumo}")


def main() -> int:
    _preflight()
    print("🧪 R1-RT1 — runtime real")
    print("   entrada: laylay.py --roteiro → _agendar_entrada_canonica")
    print("   efeitos: Calculadora + dois fixtures isolados em Downloads")
    print("   crítico: turno 5 precisa executar FILE_READ(A)")
    print(
        "   observação: a Calculadora é aberta de propósito e não é fechada "
        "automaticamente para não encerrar uma instância que já fosse sua."
    )

    codigo = 1
    try:
        codigo = int(executar_roteiro(__file__))
        return codigo
    finally:
        _imprimir_diagnostico_rt1()
        _limpar_fixtures()


if __name__ == "__main__":
    raise SystemExit(main())
