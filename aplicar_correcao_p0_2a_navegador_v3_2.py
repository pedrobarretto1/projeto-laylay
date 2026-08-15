#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0.2A v3.2 — fecha a ponte faltante de "Volta para a anterior.".

Não inicia a Laylay e não chama executor real de navegador.
"""

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
import time
from pathlib import Path

MARCADOR = "P0_NAVEGADOR_PONTE_V3_2_20260815"
CONTEXTO_REL = Path("mente_laylay/memoria_mental/contexto_imediato.py")
TESTE_REL = Path("tests/test_p0_2a_navegador_v3_2.py")

REF_ANTIGA = '    referencia_curta = bool(re.search(\n        r"\\b(?:ele|ela|isso|esse|essa|este|esta)\\b",\n        texto_norm,\n    ))\n'
REF_NOVA = '    # P0_NAVEGADOR_PONTE_V3_2_20260815\n    # "anterior/de antes" são dêiticos operacionais como "essa": o domínio\n    # vem do contrato/continuidade, não da palavra isolada.\n    referencia_curta = bool(re.search(\n        r"\\b(?:ele|ela|isso|esse|essa|este|esta|anterior|de\\s+antes)\\b",\n        texto_norm,\n    ))\n'
ANCORA_DOMINIO = '    # Uma confirmação operacional recente é mais saliente que a fala usada\n'
BLOCO_DOMINIO = '    # P0_NAVEGADOR_PONTE_V3_2_20260815\n    # A camada de domínio já aplica contrato e TTL. Esta ponte apenas\n    # transporta a decisão canônica para referencia_contextual_imediata.\n    if not dominio_pedido and referencia_curta:\n        dominio_pedido = _dominio_restrito_referencia(\n            texto_norm,\n            estado,\n            ttl_s=ttl_s,\n        )\n\n'
TESTE = '# -*- coding: utf-8 -*-\n"""Regressões puras da ponte P0.2A v3.2."""\n\nfrom __future__ import annotations\n\nimport re\nimport time\nimport unicodedata\nimport unittest\n\nfrom mente_laylay.memoria_mental.contexto_imediato import (\n    ContextoImediatoRuntime,\n    _dominio_restrito_referencia,\n    referencia_contextual_imediata,\n    resolver_comando_acao_geral_contextual,\n)\n\n\ndef _normalizar(valor):\n    base = unicodedata.normalize("NFKD", str(valor or "").casefold())\n    base = "".join(ch for ch in base if not unicodedata.combining(ch))\n    base = re.sub(r"[^a-z0-9\\s]", " ", base)\n    return re.sub(r"\\s+", " ", base).strip()\n\n\ndef _estado_site():\n    agora = time.time()\n    return {\n        "ts": agora,\n        "ultima_acao_ts": agora,\n        "ultima_acao_intent": "OPEN_URL",\n        "ultima_intencao": "OPEN_URL",\n        "ultima_habilidade": "site",\n        "ultima_acao_params": {"alvo": "prime video"},\n        "ultima_acao_promovivel": True,\n        "ultima_acao_contrato": {\n            "intent": "OPEN_URL",\n            "dominio": "site",\n            "executou": True,\n            "confirmado": True,\n            "alvo": "prime video",\n        },\n        "ultimo_site_aba": "prime video",\n        "ultimo_app_janela": "opera",\n        "continuidade_geral": {\n            "dominio_ativo": "app",\n            "dominios": {\n                "app": {\n                    "dominio": "app",\n                    "intent": "APP_OPEN",\n                    "alvo": "opera",\n                    "params": {"nome_app": "opera"},\n                    "status": "executado",\n                    "ativa": True,\n                    "ts": agora,\n                    "expira_em": agora + 300.0,\n                },\n                "site": {\n                    "dominio": "site",\n                    "intent": "OPEN_URL",\n                    "alvo": "prime video",\n                    "params": {"alvo": "prime video"},\n                    "status": "executado",\n                    "ativa": True,\n                    "ts": agora - 1.0,\n                    "expira_em": agora + 300.0,\n                },\n            },\n            "historico": [],\n            "ts": agora,\n        },\n    }\n\n\nclass EstadoFalso:\n    def __init__(self, mental):\n        self.mental = mental\n\n    def musica_get(self, _chave):\n        return ""\n\n    def substituir(self, _chave, valor):\n        self.mental = valor\n\n\nclass P02ANavegadorV32Tests(unittest.TestCase):\n    def test_dominio_da_frase_continua_site(self):\n        self.assertEqual(\n            _dominio_restrito_referencia(\n                "Volta para a anterior.",\n                _estado_site(),\n                ttl_s=300.0,\n            ),\n            "site",\n        )\n\n    def test_ponte_resolve_referencia_site_para_anterior(self):\n        estado = _estado_site()\n        referencia = referencia_contextual_imediata(\n            mente_integrada_estado=estado,\n            foco_vivo={\n                "habilidade": "janela",\n                "alvo": "Opera",\n                "ts": time.time(),\n            },\n            texto_atual="Volta para a anterior.",\n            normalizar_texto=_normalizar,\n            ttl_s=300.0,\n        )\n        self.assertEqual(referencia["tipo"], "site")\n        self.assertEqual(referencia["alvo"], "prime video")\n\n        comando = resolver_comando_acao_geral_contextual(\n            "Volta para a anterior.",\n            referencia,\n        )\n        self.assertIsInstance(comando, dict)\n        self.assertEqual(comando["intent"], "SWITCH_PREVIOUS_TAB")\n\n    def test_runtime_completo_materializa_switch_previous_tab(self):\n        estado = EstadoFalso(_estado_site())\n        runtime = ContextoImediatoRuntime(\n            estado_runtime_getter=lambda: estado,\n            servicos_iniciais={\n                "_normalizar_texto_com_apelidos": _normalizar,\n                "_alvo_corrigido_atual": lambda: "",\n                "_registrar_alvo_corrigido": lambda _alvo: None,\n                "falar_com_lipsync": lambda *_args, **_kwargs: None,\n                "_contexto_musical_ativo": lambda: True,\n                "_estrutura_arquivo_recente": lambda _ttl: {},\n                "_foco_vivo_atual": lambda **_kwargs: {\n                    "habilidade": "janela",\n                    "alvo": "Opera",\n                    "ts": time.time(),\n                },\n                "enviar_mensagem": None,\n            },\n            iot=None,\n        )\n        comando = runtime.resolver("Volta para a anterior.")\n        self.assertIsInstance(comando, dict)\n        self.assertEqual(comando["intent"], "SWITCH_PREVIOUS_TAB")\n        self.assertEqual(comando.get("_dominio_contextual"), "site")\n\n    def test_fecha_essa_permanece_site(self):\n        estado = _estado_site()\n        referencia = referencia_contextual_imediata(\n            mente_integrada_estado=estado,\n            foco_vivo={\n                "habilidade": "janela",\n                "alvo": "Opera",\n                "ts": time.time(),\n            },\n            texto_atual="Fecha essa.",\n            normalizar_texto=_normalizar,\n            ttl_s=300.0,\n        )\n        self.assertEqual(referencia["tipo"], "site")\n        comando = resolver_comando_acao_geral_contextual(\n            "Fecha essa.",\n            referencia,\n        )\n        self.assertEqual(comando["intent"], "CLOSE_TAB")\n\n\nif __name__ == "__main__":\n    unittest.main()\n'


def localizar_raiz(explicita: str | None) -> Path:
    candidatos = []
    if explicita:
        candidatos.append(Path(explicita).expanduser().resolve())
    aqui = Path(__file__).resolve().parent
    cwd = Path.cwd().resolve()
    candidatos.extend([
        aqui, aqui.parent, cwd, cwd / "laylay", cwd / "projeto-laylay", cwd.parent,
    ])
    vistos = set()
    for candidato in candidatos:
        if candidato in vistos:
            continue
        vistos.add(candidato)
        if (
            (candidato / "laylay.py").is_file()
            and (candidato / CONTEXTO_REL).is_file()
        ):
            return candidato
    raise FileNotFoundError(
        "Não encontrei a raiz da Laylay. Use --root CAMINHO_DO_PROJETO."
    )


def ler(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def escrever(path: Path, conteudo: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(conteudo, encoding="utf-8", newline="\n")


def substituir_unico(fonte: str, antigo: str, novo: str, rotulo: str) -> str:
    quantidade = fonte.count(antigo)
    if quantidade != 1:
        raise RuntimeError(
            f"Âncora {rotulo!r}: esperado 1, encontrado {quantidade}."
        )
    return fonte.replace(antigo, novo, 1)


def inserir_unico(fonte: str, ancora: str, bloco: str, rotulo: str) -> str:
    quantidade = fonte.count(ancora)
    if quantidade != 1:
        raise RuntimeError(
            f"Âncora {rotulo!r}: esperado 1, encontrado {quantidade}."
        )
    return fonte.replace(ancora, bloco + ancora, 1)


def validar_ast(path: Path) -> None:
    try:
        ast.parse(ler(path), filename=str(path))
    except SyntaxError as erro:
        raise RuntimeError(
            f"AST inválida em {path}: linha {erro.lineno}: {erro.msg}"
        ) from erro


def executar_testes(raiz: Path) -> None:
    suites = ["tests.test_p0_2a_navegador_v3_2"]
    if (raiz / "tests/test_p0_2a_navegador_v3_1.py").is_file():
        suites.append("tests.test_p0_2a_navegador_v3_1")

    resultado = subprocess.run(
        [sys.executable, "-m", "unittest", *suites, "-v"],
        cwd=raiz,
        text=True,
        capture_output=True,
        timeout=120,
    )
    saida = (resultado.stdout or "") + (resultado.stderr or "")
    if saida.strip():
        print(saida.rstrip())
    if resultado.returncode != 0:
        raise RuntimeError(
            "Testes P0.2A falharam; o patch será revertido."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aplica P0.2A v3.2 — ponte de 'anterior'."
    )
    parser.add_argument("--root")
    args = parser.parse_args()

    try:
        raiz = localizar_raiz(args.root)
        contexto_path = raiz / CONTEXTO_REL
        teste_path = raiz / TESTE_REL
        print(f"📁 Projeto: {raiz}")

        atual = ler(contexto_path)

        if MARCADOR in atual:
            if not teste_path.is_file():
                raise RuntimeError(
                    "Marcador da v3.2 existe, mas o teste correspondente não."
                )
            validar_ast(contexto_path)
            validar_ast(teste_path)
            executar_testes(raiz)
            print("✅ P0.2A v3.2 já estava aplicada e continua válida.")
            return 0

        sinais_v31 = (
            "P0_NAVEGADOR_SUBTIPO_V3_1_20260815",
            "def _dominio_contrato_referencia(",
            '"SWITCH_PREVIOUS_TAB", "APP_OPEN"',
        )
        ausentes = [s for s in sinais_v31 if s not in atual]
        if ausentes:
            raise RuntimeError(
                "A base v3.1 esperada não foi encontrada; "
                f"ausentes: {ausentes!r}"
            )

        novo = substituir_unico(
            atual,
            REF_ANTIGA,
            REF_NOVA,
            "referencia_curta da ponte",
        )
        novo = inserir_unico(
            novo,
            ANCORA_DOMINIO,
            BLOCO_DOMINIO,
            "propagacao de dominio",
        )

        ast.parse(novo, filename=str(contexto_path))
        ast.parse(TESTE, filename=str(teste_path))

        backup = (
            raiz
            / "_backup_p0_2a_navegador_v3_2"
            / time.strftime("%Y%m%d-%H%M%S")
        )
        backup_contexto = backup / CONTEXTO_REL
        backup_teste = backup / TESTE_REL
        backup_contexto.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(contexto_path, backup_contexto)

        teste_existia = teste_path.exists()
        if teste_existia:
            backup_teste.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(teste_path, backup_teste)

        print(f"📦 Backup: {backup}")

        try:
            escrever(contexto_path, novo)
            escrever(teste_path, TESTE)

            validar_ast(contexto_path)
            validar_ast(teste_path)

            contexto_gravado = ler(contexto_path)
            obrigatorios = (
                MARCADOR,
                r"anterior|de\s+antes",
                "dominio_pedido = _dominio_restrito_referencia(",
            )
            faltando = [x for x in obrigatorios if x not in contexto_gravado]
            if faltando:
                raise RuntimeError(
                    f"Validação estrutural pós-gravação falhou: {faltando!r}"
                )

            executar_testes(raiz)

        except Exception:
            shutil.copy2(backup_contexto, contexto_path)
            if teste_existia:
                shutil.copy2(backup_teste, teste_path)
            elif teste_path.exists():
                teste_path.unlink()
            print("↩️ Alterações revertidas a partir do backup.")
            raise

        print("✅ P0.2A v3.2 aplicada com sucesso.")
        print("   - 'Volta para a anterior.' atravessa a ponte tipada")
        print("   - nenhum executor real foi chamado pelos testes")
        return 0

    except Exception as erro:
        print(
            f"❌ P0.2A v3.2 não aplicada: "
            f"{type(erro).__name__}: {erro}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
