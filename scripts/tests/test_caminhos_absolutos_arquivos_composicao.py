"""Classificação, coordenação e roteamento instalados; efeitos isolados."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope="module")
def composicao_caminhos() -> dict:
    codigo = textwrap.dedent(r'''
        import json, os, sys
        from copy import deepcopy
        from mente_laylay.integracao import instancia_unica
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda identificador, **kw: adquirir(
            str(identificador) + ".caminhos-literais-" + str(os.getpid()), **kw,
        )
        import laylay as root
        from mente_laylay.memoria_mental.continuidade_contexto import registrar_estrutura_arquivo_recente
        alvo = r"C:\Users\pbarr\Downloads\pasta organizada\projeto lay\p16 teste\prova.txt"
        antigo = r"C:\Users\pbarr\Downloads\outro alvo\prova.txt"
        root.MEMORIA_SQLITE = None
        root.salvar_memoria = lambda *_args, **_kw: None
        root._registrar_autocorrecao_virtual = lambda *_args, **_kw: None
        composicao = root._composicao_turno_runtime
        composicao._servicos["_coleta_entradas_neurais"] = None
        composicao._servicos["MEMORIA_SQLITE"] = None
        estado = root._estado_compartilhado_runtime
        base = estado.snapshot()
        ciclo = root._ciclo_comandos_runtime
        saida = {"casos": {}, "instalacao": {
            "ciclo": ciclo is not None,
            "detector": callable(root.detectar_intencao_deterministica),
            "resolver": callable(root._registro_arquivos_mutacao_runtime.resolver_caminho),
        }}
        casos = {
            "leitura": "Leia " + alvo,
            "abertura": "Abra \"" + alvo + "\"",
            "escrita_no": "Escreva Texto literal no arquivo " + alvo,
            "append_no": "Acrescente Texto literal no arquivo \"" + alvo + "\"",
            "escrita_dentro": "Escreva Texto literal dentro do arquivo " + alvo,
            "exclusao_tipada": "apaga o arquivo \"" + alvo + "\"",
            "movimento_coloca": "coloca \"" + alvo + "\" para " + r"C:\Users\pbarr\Downloads\nova pasta",
            "mover_sem_modalidade": "move \"" + alvo + "\" para " + r"C:\Users\pbarr\Downloads\nova pasta",
            "solto": alvo,
            "capacidade": "Você consegue ler arquivos pelo caminho " + alvo + "?",
            "negacao": "Não escreva Texto literal no arquivo " + alvo,
            "hipotese": "Se eu pedir para abrir " + alvo,
            "explicacao": "Como eu escrevo Texto literal no arquivo " + alvo + "?",
        }
        for nome, texto in casos.items():
            for dominio in ("mental", "conversacional", "memoria_conversa"):
                estado.substituir(dominio, deepcopy(base[dominio]))
            estado.atualizar("mental", lambda atual: registrar_estrutura_arquivo_recente(atual, {
                "tipo": "arquivo", "caminho": antigo, "arquivo_nome": "prova.txt",
            }))
            turno = root._iniciar_planejamento_turno(texto, origem="sonda_caminho_literal")
            ctx = ciclo._montar_contexto_resolucao()
            # Portas sem efeito: não usam o modelo nem executam ações.
            ctx["tentar_intencao_ai_primeiro"] = lambda *_args, **_kw: None
            ctx["executar_intencao"] = lambda *_args, **_kw: (_ for _ in ()).throw(AssertionError("resolução executou efeito"))
            ctx["falar_com_lipsync"] = lambda *_args, **_kw: None
            ctx["_emitir_resposta_curta"] = lambda *_args, **_kw: None
            entradas = []
            instalado = ctx["detectar_intencao_deterministica"]
            def observar(entrada):
                entradas.append(entrada)
                return instalado(entrada)
            ctx["detectar_intencao_deterministica"] = observar
            resultado, rota = ciclo._resolver_decisao_canonica(texto, "sonda_caminho_literal", contexto=ctx)
            saida["casos"][nome] = {
                "turno": {"modalidade": turno.get("modalidade"), "autoriza": turno.get("autoriza_execucao")},
                "resultado": resultado, "rota": rota, "entradas_detector": entradas,
            }
        sys.__stdout__.write("CAMINHOS_COMPOSICAO " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_MASCOT_ENABLED="0", LAYLAY_AVATAR_ATIVO="0"),
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    assert processo.returncode == 0, processo.stderr[-5000:]
    linhas = [linha.removeprefix("CAMINHOS_COMPOSICAO ") for linha in processo.stdout.splitlines() if linha.startswith("CAMINHOS_COMPOSICAO ")]
    assert linhas, processo.stdout[-4000:]
    return json.loads(linhas[-1])


@pytest.mark.parametrize("caso,intent,campo", [
    ("leitura", "FILE_READ", "caminho"),
    ("abertura", "FILE_OPEN_RESULT", "caminho"),
    ("escrita_no", "CREATE_FILE", "alvo"),
    ("append_no", "CREATE_FILE", "alvo"),
    ("escrita_dentro", "CREATE_FILE", "alvo"),
    ("exclusao_tipada", "DELETE_ITEM", "alvo"),
    ("movimento_coloca", "FILE_TRANSACTION", "origem"),
])
def test_coordenador_instalado_preserva_ato_e_alvo_literal(composicao_caminhos: dict, caso: str, intent: str, campo: str) -> None:
    observado = composicao_caminhos["casos"][caso]
    assert observado["turno"]["autoriza"] is True, "primeira fronteira: autoridade do pedido atual"
    resultado = observado["resultado"]
    assert resultado is not None, observado
    assert resultado["intent"] == intent, observado
    assert resultado["params"][campo] == r"C:\Users\pbarr\Downloads\pasta organizada\projeto lay\p16 teste\prova.txt", observado


@pytest.mark.parametrize("caso", ["solto", "capacidade", "negacao", "hipotese", "explicacao", "mover_sem_modalidade"])
def test_coordenador_instalado_nao_promove_caminho_a_autoridade(composicao_caminhos: dict, caso: str) -> None:
    observado = composicao_caminhos["casos"][caso]
    assert observado["turno"]["autoriza"] is False
    assert observado["resultado"] is None, observado


def test_servicos_existentes_instalados(composicao_caminhos: dict) -> None:
    assert all(composicao_caminhos["instalacao"].values())
