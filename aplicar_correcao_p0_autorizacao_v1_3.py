#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0.1 — autorização/modalidade central da Laylay. Patch v1.3.

Uso:
    python aplicar_correcao_p0_autorizacao.py
    python aplicar_correcao_p0_autorizacao.py --root "C:\\caminho\\projeto-laylay"
    python aplicar_correcao_p0_autorizacao.py --sem-testes
"""
from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from datetime import datetime
from pathlib import Path

MARCADOR = "P0_AUTORIZACAO_MODALIDADE_20260814"

BLOCO_MODALIDADE = r'''

# P0_AUTORIZACAO_MODALIDADE_20260814
# A classificação composta histórica continua como fonte de contexto, mas o
# ato de fala INTEIRO ganha a palavra final sobre autorização. Assim uma
# citação/pergunta não recupera permissão por causa da segmentação interna.
_P0_GATILHOS_OPERACIONAIS = re.compile(
    r"\b(?:"
    r"abre|abrir|abra|abriria|"
    r"fecha|fechar|feche|fecharia|"
    r"liga|ligar|ligue|ligaria|"
    r"desliga|desligar|desligue|desligaria|"
    r"toca|tocar|toque|tocaria|"
    r"coloca|colocar|coloque|colocaria|"
    r"cria|criar|crie|criaria|"
    r"apaga|apagar|apague|apagaria|"
    r"remove|remover|remova|removeria|"
    r"deleta|deletar|delete|deletaria|"
    r"move|mover|mova|moveria|"
    r"renomeia|renomear|renomeie|renomearia|"
    r"maximiza|maximizar|maximize|maximizaria|"
    r"minimiza|minimizar|minimize|minimizaria|"
    r"pausa|pausar|pause|pausaria|"
    r"retoma|retomar|continue|continua|continuar|"
    r"organiza|organizar|organize|organizaria|"
    r"pesquisa|pesquisar|pesquise|"
    r"busca|buscar|busque|procura|procurar|procure|"
    r"encontra|encontrar|encontre|"
    r"escreve|escrever|escreva|escreveria|"
    r"grava|gravar|grave|gravaria|"
    r"executa|executar|execute|executaria|"
    r"repete|repetir|repita|refaz|refazer|refaca|"
    r"tenta|tentar|tente"
    r")\b",
    re.IGNORECASE,
)


def _normalizar_p0_ato_fala(
    texto: str,
    normalizar_texto: Callable[[str], str] | None = None,
) -> str:
    normalizar = normalizar_texto if callable(normalizar_texto) else (
        lambda valor: str(valor or "").casefold().strip()
    )
    bruto = str(normalizar(texto) or "").casefold()
    base = unicodedata.normalize("NFKD", bruto)
    sem_acentos = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", sem_acentos).strip()


def _protecao_p0_ato_fala(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
) -> Dict[str, Any] | None:
    """Lê quando a frase fala SOBRE uma ação sem autorizá-la."""
    t = _normalizar_p0_ato_fala(texto, normalizar_texto)
    if not t:
        return None

    existente = analisar_protecao_operacional(
        t,
        normalizar_texto=lambda valor: _normalizar_p0_ato_fala(valor),
    )
    if bool(existente.get("bloqueia_execucao")):
        return {
            "modalidade": str(existente.get("modalidade") or "conversa"),
            "natureza_acao": str(existente.get("natureza_acao") or "nenhuma"),
            "motivo": str(existente.get("motivo") or "proteção operacional"),
            "requer_esclarecimento": (
                str(existente.get("natureza_acao") or "") == "capacidade"
            ),
        }

    tem_gatilho = bool(_P0_GATILHOS_OPERACIONAIS.search(t))
    if not tem_gatilho:
        return None

    # Metalinguagem/citação: o verbo é conteúdo da frase, não uma ordem.
    if (
        re.search(
            r"^(?:(?:eu\s+)?(?:estou|to)\s+)?(?:so\s+|apenas\s+|somente\s+)?"
            r"(?:estou\s+)?(?:escrevendo|digitando|citando|mencionando|"
            r"falando\s+a\s+frase|dizendo)\b",
            t,
        )
        or re.search(r"^(?:a\s+)?(?:palavra|frase|expressao|texto|termo)\b", t)
        or re.search(r"\bnao\s+(?:e|eh)\s+(?:um\s+)?(?:pedido|comando|ordem)\b", t)
        or re.search(
            r"\b(?:so|apenas|somente)\s+(?:um\s+)?"
            r"(?:exemplo|teste|texto|citacao|mencao)\b",
            t,
        )
        or re.search(
            r"^(?:quando|se)\s+eu\s+(?:digo|disser|escrevo|escrever|falo|falar)\b",
            t,
        )
    ):
        return {
            "modalidade": "conversa",
            "natureza_acao": "mencao_operacional",
            "motivo": "menção/citação de comando sem autorização",
            "requer_esclarecimento": False,
        }

    # Explicação/instrução sobre COMO fazer algo.
    if (
        re.search(
            r"^(?:(?:me|pra\s+mim|para\s+mim)\s+)?"
            r"(?:explica|explique|ensina|ensine|mostra|mostre)\s+como\b",
            t,
        )
        or re.search(
            r"^(?:eu\s+)?(?:quero|queria|gostaria)\s+(?:de\s+)?saber\s+como\b",
            t,
        )
    ):
        return {
            "modalidade": "pergunta",
            "natureza_acao": "instrucao_ou_explicacao",
            "motivo": "pedido de explicação sobre ação; não é execução",
            "requer_esclarecimento": False,
        }

    # Perguntas informativas que começam pelo infinitivo da ação. Antes da P0
    # elas venciam a pergunta genérica e podiam ser classificadas como ordem.
    if "?" in str(texto or "") and (
        re.search(
            r"^(?:abrir|fechar|ligar|desligar|tocar|colocar|criar|apagar|"
            r"remover|deletar|mover|renomear|maximizar|minimizar|pausar|"
            r"organizar|executar)\b.*\b(?:e|eh)\s+"
            r"(?:(?:uma|a)\s+)?(?:boa|ma)\s+ideia\b",
            t,
        )
        or re.search(
            r"^(?:abrir|fechar|ligar|desligar|tocar|colocar|criar|apagar|"
            r"remover|deletar|mover|renomear|maximizar|minimizar|pausar|"
            r"organizar|executar)\b.*\b"
            r"(?:muda|altera|afeta|causa|serve|significa|acontece|funciona|"
            r"pode\s+causar|vai\s+causar)\b",
            t,
        )
    ):
        return {
            "modalidade": "pergunta",
            "natureza_acao": "informativa_sobre_acao",
            "motivo": "pergunta informativa sobre uma ação; não é pedido",
            "requer_esclarecimento": False,
        }

    return None


def classificar_modalidade_turno(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
    texto_tem_comando_explicito: Callable[[str], bool] | None = None,
    confirmacao_contextual_valida: bool = False,
) -> Dict[str, Any]:
    """Classifica o turno com proteção P0 do ato de fala inteiro."""
    resultado = _classificar_modalidade_turno_composta_base(
        texto,
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
        confirmacao_contextual_valida=confirmacao_contextual_valida,
    )
    protecao = _protecao_p0_ato_fala(texto, normalizar_texto=normalizar_texto)
    if not protecao:
        return resultado

    normalizado = _normalizar_p0_ato_fala(texto, normalizar_texto)
    modalidade = str(protecao.get("modalidade") or "conversa")
    natureza = str(protecao.get("natureza_acao") or "nenhuma")
    motivo = str(protecao.get("motivo") or "ato de fala sem autorização")
    requer = bool(protecao.get("requer_esclarecimento"))
    resultado.update(
        modalidade=modalidade,
        modalidade_geral=modalidade,
        ato_principal=modalidade,
        atos=[modalidade],
        segmentos=[{
            "indice": 0,
            "texto": normalizado[:300],
            "modalidade": modalidade,
            "confianca": 0.99,
            "motivo": motivo,
            "autoriza_execucao": False,
            "acao_explicita": False,
            "requer_esclarecimento": requer,
            "natureza_acao": natureza,
        }],
        texto_operacional="",
        texto_conversacional=normalizado[:500],
        acao_explicita=False,
        autoriza_execucao=False,
        requer_esclarecimento=requer,
        natureza_acao=natureza,
        motivo=motivo,
        motivo_decisao=motivo,
        confianca=max(float(resultado.get("confianca") or 0.0), 0.99),
    )
    return resultado


def bloqueia_execucao_operacional_prioritaria(
    texto: str,
    *,
    classificacao: Dict[str, Any] | None = None,
    normalizar_texto: Callable[[str], str] | None = None,
    texto_tem_comando_explicito: Callable[[str], bool] | None = None,
    confirmacao_contextual_valida: bool = False,
) -> bool:
    """Barreira fail-closed para roteadores operacionais imediatos."""
    if _protecao_p0_ato_fala(texto, normalizar_texto=normalizar_texto):
        return True

    analise = dict(classificacao or {})
    if not analise:
        analise = classificar_modalidade_turno(
            texto,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
            confirmacao_contextual_valida=confirmacao_contextual_valida,
        )
    if bool(analise.get("autoriza_execucao")):
        return False

    natureza = str(analise.get("natureza_acao") or "").casefold()
    if natureza in {
        "capacidade", "instrucao_ou_explicacao", "informativa_sobre_acao",
        "hipotetica", "cancelamento", "mencao_operacional", "decepcao",
    }:
        return True

    normalizado = _normalizar_p0_ato_fala(texto, normalizar_texto)
    return bool(_P0_GATILHOS_OPERACIONAIS.search(normalizado))
'''

TESTES = r'''# -*- coding: utf-8 -*-
"""P0.1 — regressões de autorização/modalidade no caminho real da Laylay."""

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.cognicao.modalidade_turno import (
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)

NAO_EXECUTAR = (
    "Me explica como pausar uma música sem pausar agora.",
    "Abrir o Opera é uma boa ideia?",
    "Maximizar uma janela muda a resolução?",
    "Estou apenas escrevendo: abre o Opera.",
    "A palavra fecha não é um pedido para fechar nada.",
    "Não abra a Calculadora.",
    "Talvez eu abra a Calculadora depois.",
    "Como eu apagaria um arquivo?",
)

EXECUTAR = (
    "Pausa a música.",
    "Abre o Opera.",
    "Maximiza a Calculadora.",
    "Fecha a Calculadora.",
    "Pode abrir o Opera?",
    "Continua a música.",
)


def test_matriz_p0_nao_autoriza_mencao_pergunta_hipotese_ou_negacao():
    for texto in NAO_EXECUTAR:
        turno = classificar_modalidade_turno(texto)
        assert turno["autoriza_execucao"] is False, (texto, turno)
        assert bloqueia_execucao_operacional_prioritaria(
            texto, classificacao=turno,
        ) is True, (texto, turno)


def test_matriz_p0_preserva_comandos_reais_e_pedido_polido():
    for texto in EXECUTAR:
        turno = classificar_modalidade_turno(texto)
        assert turno["autoriza_execucao"] is True, (texto, turno)
        assert bloqueia_execucao_operacional_prioritaria(
            texto, classificacao=turno,
        ) is False, (texto, turno)


def _runtime_para(texto, *, detector=None, resolver_app=None):
    executados, registros, falas = [], [], []

    class Estado:
        mental = {"turno_atual": classificar_modalidade_turno(texto)}

    ns = {
        "_estado_compartilhado_runtime": Estado(),
        "detectar_intencao_deterministica": detector or (lambda _texto: None),
        "executar_intencao": lambda comando, _texto: executados.append(dict(comando)) or True,
        "_registrar_resultado_execucao": lambda *args, **kwargs: registros.append((args, kwargs)),
        "_emitir_resposta_curta": lambda _texto, fala, **_kwargs: falas.append(fala),
    }
    if resolver_app is not None:
        ns["_resolver_alvo_ambiente"] = resolver_app
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: ns,
        loop_getter=lambda: None,
    )
    return runtime, executados, registros, falas


def test_runtime_imediato_nao_executa_detector_agressivo_sem_autorizacao():
    texto = "Me explica como pausar uma música sem pausar agora."
    runtime, executados, _registros, _falas = _runtime_para(
        texto,
        detector=lambda _texto: {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}},
    )
    assert runtime.processar_prioritarios(texto) is False
    assert executados == []


def test_runtime_imediato_executa_comando_real():
    texto = "Pausa a música."
    runtime, executados, _registros, _falas = _runtime_para(
        texto,
        detector=lambda _texto: {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}},
    )
    assert runtime.processar_prioritarios(texto) is True
    assert [item["intent"] for item in executados] == ["MEDIA_CONTROL"]


def test_consulta_read_only_do_opera_continua_passando_pela_barreira_existente():
    texto = "O Opera continua aberto?"
    runtime, executados, registros, falas = _runtime_para(
        texto,
        detector=lambda _texto: {"intent": "APP_OPEN", "params": {"programa": "opera"}},
        resolver_app=lambda _nome: {"programa_aberto": True, "programa_em_foco": False},
    )
    assert runtime.processar_prioritarios(texto) is True
    assert executados == []
    assert falas == ["Opera está aberto, mas não está em foco."]
    assert registros
    contrato = registros[-1][0][0]
    assert contrato["intent"] == "LIST_WINDOWS"
    assert contrato["status"] == "estado_app_consultado"


def test_inventario_read_only_tambem_passa_antes_da_barreira():
    texto = "Quais programas estão abertos?"
    falas = []

    class Estado:
        mental = {"turno_atual": classificar_modalidade_turno(texto)}

    ns = {
        "_estado_compartilhado_runtime": Estado(),
        "observar_programas_abertos": lambda: {
            "janelas_visiveis": ["Opera", "Calculadora"],
            "processos_segundo_plano": [],
        },
        "_emitir_resposta_curta": (
            lambda _texto, fala, **_kwargs: falas.append(fala)
        ),
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
        "detectar_intencao_deterministica": lambda _texto: {
            "intent": "APP_OPEN",
            "params": {"programa": "opera"},
        },
        "executar_intencao": lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("rota mutante não deveria ser alcançada")
        ),
    }

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: ns,
        loop_getter=lambda: None,
    )
    assert runtime.processar_prioritarios(texto) is True
    assert falas


def test_metalinguagem_nao_e_segmentada_como_comando():
    turno = classificar_modalidade_turno("Estou apenas escrevendo: abre o Opera.")
    assert turno["autoriza_execucao"] is False
    assert turno["texto_operacional"] == ""
    assert turno["atos"] == ["conversa"]
    assert turno["natureza_acao"] == "mencao_operacional"
'''


def achar_raiz(inicio: Path) -> Path:
    for base in (inicio, *inicio.parents):
        if (
            (base / "laylay.py").is_file()
            and (base / "mente_laylay" / "cognicao" / "modalidade_turno.py").is_file()
            and (base / "mente_laylay" / "autonomia" / "comandos_imediatos.py").is_file()
        ):
            return base
    raise FileNotFoundError(
        "Não encontrei a raiz do projeto. Coloque este script ao lado de laylay.py ou use --root."
    )


def validar_ast(caminho: Path) -> None:
    ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))


def aplicar_modalidade(texto: str) -> str:
    if MARCADOR in texto:
        return texto
    if "import unicodedata" not in texto:
        ancora_import = "import re\nimport time\n"
        if ancora_import not in texto:
            raise RuntimeError("Âncora de imports não encontrada em modalidade_turno.py.")
        texto = texto.replace(ancora_import, "import re\nimport time\nimport unicodedata\n", 1)

    assinatura = "def classificar_modalidade_turno(\n"
    if texto.count(assinatura) != 1:
        raise RuntimeError(
            "Esperava exatamente uma definição de classificar_modalidade_turno antes da P0."
        )
    texto = texto.replace(
        assinatura,
        "def _classificar_modalidade_turno_composta_base(\n",
        1,
    )
    return texto.rstrip() + "\n" + BLOCO_MODALIDADE.lstrip("\n") + "\n"


def aplicar_comandos(texto: str) -> str:
    if MARCADOR in texto:
        return texto

    import_antigo = (
        "from mente_laylay.cognicao.modalidade_turno "
        "import classificar_modalidade_turno\n"
    )
    import_novo = (
        "from mente_laylay.cognicao.modalidade_turno import (\n"
        "    bloqueia_execucao_operacional_prioritaria,\n"
        "    classificar_modalidade_turno,\n"
        ")\n"
    )
    if import_antigo not in texto:
        raise RuntimeError(
            "Import canônico de classificar_modalidade_turno não encontrado em comandos_imediatos.py."
        )
    texto = texto.replace(import_antigo, import_novo, 1)

    ancora = '''        contexto_prioritario["mente_integrada_estado"] = getattr(
            estado_runtime, "mental", {},
        )

        # Comandos internos iniciados por barra nunca são respostas naturais
'''
    insercao = '''        contexto_prioritario["mente_integrada_estado"] = getattr(
            estado_runtime, "mental", {},
        )

        # P0_AUTORIZACAO_MODALIDADE_20260814
        # Consultas locais canônicas de estado são somente leitura. Elas podem
        # vencer a barreira de mutação, mas apenas pela habilidade read-only já
        # existente. Assim "O Opera continua aberto?" não é confundido com o
        # comando musical "continua".
        try:
            tratado_readonly_p0, rota_readonly_p0 = processar_consulta_sistema_local(
                contexto_prioritario, texto
            )
        except Exception as erro:
            print(
                "⚠️ [P0:READ-ONLY] consulta local falhou sem liberar mutação | "
                f"{type(erro).__name__}: {erro}"
            )
        else:
            if tratado_readonly_p0:
                print(
                    "🔎 [P0:READ-ONLY] consulta segura tratada antes da barreira | "
                    f"rota={rota_readonly_p0 or 'consulta_sistema_local'}"
                )
                return True

        # Detectar uma intent não concede permissão para executá-la. Esta
        # barreira faz a rota determinística usar o mesmo dono do turno da LLM.
        mente_atual = getattr(estado_runtime, "mental", {})
        turno_atual = (
            dict(mente_atual.get("turno_atual") or {})
            if isinstance(mente_atual, dict)
            else {}
        )
        normalizar_turno = ns.get("_normalizar_texto_com_apelidos")
        texto_tem_comando = ns.get("_texto_tem_comando_explicito")
        if bloqueia_execucao_operacional_prioritaria(
            texto,
            classificacao=turno_atual or None,
            normalizar_texto=(normalizar_turno if callable(normalizar_turno) else None),
            texto_tem_comando_explicito=(
                texto_tem_comando if callable(texto_tem_comando) else None
            ),
        ):
            modalidade_p0 = str(
                turno_atual.get("modalidade_geral")
                or turno_atual.get("modalidade")
                or "conversa"
            )
            motivo_p0 = str(
                turno_atual.get("motivo_decisao")
                or turno_atual.get("motivo")
                or "sem autorização operacional"
            )
            print(
                "🛡️ [P0:AUTORIZAÇÃO] rota operacional imediata bloqueada | "
                f"modalidade={modalidade_p0} motivo={motivo_p0}"
            )
            return False

        # Comandos internos iniciados por barra nunca são respostas naturais
'''
    if ancora not in texto:
        raise RuntimeError(
            "Âncora do início de processar_prioritarios não encontrada; nenhum patch parcial foi aplicado."
        )
    return texto.replace(ancora, insercao, 1)


def rodar(cmd: list[str], cwd: Path) -> int:
    print(">", " ".join(cmd))
    return int(subprocess.run(cmd, cwd=str(cwd)).returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--sem-testes", action="store_true")
    args = parser.parse_args()

    if args.root:
        raiz = achar_raiz(args.root.expanduser().resolve())
    else:
        # Procura primeiro a partir da pasta do próprio patcher. Assim ele
        # funciona mesmo quando o PowerShell está aberto na pasta pai.
        tentativas = [
            Path(__file__).resolve().parent,
            Path.cwd().resolve(),
        ]
        ultimo_erro = None
        raiz = None
        for inicio in tentativas:
            try:
                raiz = achar_raiz(inicio)
                break
            except FileNotFoundError as erro:
                ultimo_erro = erro
        if raiz is None:
            raise ultimo_erro or FileNotFoundError("Não encontrei a raiz do projeto.")
    print(f"Projeto: {raiz}")

    alvo_modalidade = raiz / "mente_laylay" / "cognicao" / "modalidade_turno.py"
    alvo_comandos = raiz / "mente_laylay" / "autonomia" / "comandos_imediatos.py"
    alvo_testes = raiz / "tests" / "test_p0_autorizacao_modalidade.py"

    originais = {
        alvo_modalidade: alvo_modalidade.read_text(encoding="utf-8"),
        alvo_comandos: alvo_comandos.read_text(encoding="utf-8"),
    }
    if alvo_testes.exists():
        originais[alvo_testes] = alvo_testes.read_text(encoding="utf-8")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = raiz / "_backup_correcao_p0_autorizacao" / timestamp
    gravados: list[Path] = []

    try:
        novo_modalidade = aplicar_modalidade(originais[alvo_modalidade])
        novo_comandos = aplicar_comandos(originais[alvo_comandos])

        mudancas = (
            novo_modalidade != originais[alvo_modalidade]
            or novo_comandos != originais[alvo_comandos]
            or not alvo_testes.exists()
            or alvo_testes.read_text(encoding="utf-8") != TESTES
        )
        if mudancas:
            backup.mkdir(parents=True, exist_ok=True)
            for caminho, conteudo in originais.items():
                destino = backup / caminho.relative_to(raiz)
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_text(conteudo, encoding="utf-8")

            alvo_modalidade.write_text(novo_modalidade, encoding="utf-8")
            gravados.append(alvo_modalidade)
            alvo_comandos.write_text(novo_comandos, encoding="utf-8")
            gravados.append(alvo_comandos)
            alvo_testes.parent.mkdir(parents=True, exist_ok=True)
            alvo_testes.write_text(TESTES, encoding="utf-8")
            gravados.append(alvo_testes)

        for caminho in (alvo_modalidade, alvo_comandos, alvo_testes):
            validar_ast(caminho)
            if rodar([sys.executable, "-m", "py_compile", str(caminho)], raiz) != 0:
                raise RuntimeError(f"py_compile falhou: {caminho}")
        print("✓ AST/py_compile válidos.")

        if not args.sem_testes:
            try:
                import pytest  # noqa: F401
            except Exception:
                print("⚠ pytest não está instalado neste Python; pulei os testes.")
            else:
                codigo = rodar(
                    [
                        sys.executable, "-m", "pytest",
                        "tests/test_p0_autorizacao_modalidade.py",
                        "tests/test_regressoes_roteiro_118.py",
                        "-q",
                    ],
                    raiz,
                )
                if codigo != 0:
                    raise RuntimeError("Os testes P0/regressão falharam.")

        print("\n✓ P0.1 aplicada com sucesso.")
        if mudancas:
            print(f"Backup: {backup}")
        print("Arquivos alterados:")
        print(" - mente_laylay/cognicao/modalidade_turno.py")
        print(" - mente_laylay/autonomia/comandos_imediatos.py")
        print(" - tests/test_p0_autorizacao_modalidade.py")
        return 0

    except Exception as erro:
        print(f"\nERRO: {type(erro).__name__}: {erro}")
        if gravados:
            print("Restaurando estado anterior...")
            for caminho, conteudo in originais.items():
                caminho.parent.mkdir(parents=True, exist_ok=True)
                caminho.write_text(conteudo, encoding="utf-8")
            if alvo_testes not in originais and alvo_testes.exists():
                alvo_testes.unlink()
            print("✓ Restauração concluída.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
