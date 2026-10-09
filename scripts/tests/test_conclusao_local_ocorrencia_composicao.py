"""Retorno local pertence ao turno capturado, inclusive após selecionar outro chat.

Importa a composição real; não inicia main/GUI/modelo. A troca pela ponte TCP
é estímulo controlado, sem atribuir autoria à ocorrência histórica da P16.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope="module")
def conclusoes_instaladas(tmp_path_factory) -> dict:
    codigo = textwrap.dedent(r'''
        import json, os, socket, sys, time
        from copy import deepcopy
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.integracao import instancia_unica

        inicializar = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho, *a, **k: inicializar(
            self, os.path.join(os.environ["LAYLAY_CONTROLE_SQLITE"], os.path.basename(caminho)), *a, **k,
        )
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda identificador, **kw: adquirir(
            str(identificador) + ".conclusao-local-" + str(os.getpid()), **kw,
        )
        import laylay as root

        estado = root._estado_compartilhado_runtime
        composicao = root._composicao_turno_runtime
        composicao._servicos["_coleta_entradas_neurais"] = None
        composicao._servicos["_especialista_neural_comandos_runtime"] = None
        conversas = root._gerenciador_conversas_runtime
        ponte = root._desktop_bridge_runtime
        contexto = root._resposta_ia_runtime._contexto()
        prioritario = contexto["processar_comandos_prioritarios"]
        root._voz_runtime.definir_modo_silencioso(True, origem="controle_conclusao_local")

        def linha_tipo(cliente, tipo):
            limite = time.monotonic() + 4
            while time.monotonic() < limite:
                cliente.settimeout(max(0.05, limite - time.monotonic()))
                dados = b""
                while not dados.endswith(b"\n"):
                    bloco = cliente.recv(1)
                    assert bloco, "ponte encerrou antes da resposta"
                    dados += bloco
                mensagem = json.loads(dados)
                if mensagem.get("type") == tipo:
                    return mensagem
            raise AssertionError("resposta da ponte ausente: " + tipo)

        def selecionar(cliente, identificador):
            cliente.sendall((json.dumps({"type": "conversation_select", "id": "troca-controle",
                "conversation_id": identificador}) + "\n").encode())
            return linha_tipo(cliente, "conversations_state")

        saida = {"casos": {}, "instalacao": {
            "writer": getattr(contexto["atualizar_plano_turno"], "__self__", None) is composicao,
            "estado": conversas.estado is estado,
            "selecionar": ponte.conversa_selecionar == conversas.selecionar,
        }}
        ponte.iniciar()
        try:
            with socket.create_connection(ponte.endereco, timeout=4) as cliente:
                cliente.sendall((json.dumps({"type": "hello", "token": ponte.token}) + "\n").encode())
                linha_tipo(cliente, "snapshot")
                # Duas rotas locais reais, sem executar efeitos externos.
                for dominio, texto in (("arquivos", "você consegue ler arquivos?"),
                                       ("musica", "você consegue pausar a música?")):
                    for modo in ("vigente", "mesma_conversa", "outra_vazia", "outra_com_turno"):
                        a = conversas.criar("controle origem")["id"]
                        b = conversas.criar("controle destino")["id"]
                        assert selecionar(cliente, a)["success"] is True
                        observado = {}

                        def processar_e_trocar(entrada):
                            retorno = prioritario(entrada)
                            turno = estado.obter_copia("mental", "turno_atual")
                            plano = estado.obter_copia("mental", "plano_turno_atual")
                            textos = root._orquestrador_fala_runtime.textos_publicados_turno(turno["id"])
                            observado.update(tratado=retorno, turno_id=turno["id"],
                                fala=list(textos), plano_antes=plano)
                            if modo != "vigente":
                                alvo = a if modo == "mesma_conversa" else b
                                observado["selecao"] = selecionar(cliente, alvo)
                            if modo == "outra_com_turno":
                                root._iniciar_planejamento_turno("Qual é a sua capacidade de criar lembretes?",
                                    origem="controle_novo_turno")
                            observado["plano_destino"] = estado.obter_copia("mental", "plano_turno_atual")
                            observado["trilha_destino"] = estado.obter_copia("mental", "trilha_decisoes_turno")
                            return retorno

                        ctx = dict(contexto, processar_comandos_prioritarios=processar_e_trocar)
                        root._resposta_ia_runtime._contexto_getter = lambda: ctx
                        root._resposta_ia_runtime.processar(texto, origem="controle_conclusao_local")
                        observado.update(
                            plano_final=estado.obter_copia("mental", "plano_turno_atual"),
                            trilha_final=estado.obter_copia("mental", "trilha_decisoes_turno"),
                            origem=[m for m in conversas.mensagens(a) if m.get("role") != "system"],
                            destino=[m for m in conversas.mensagens(b) if m.get("role") != "system"],
                            conversa_ativa=conversas.id_ativo(), a=a, b=b,
                        )
                        saida["casos"][dominio + ":" + modo] = observado
        finally:
            ponte.parar()
        sys.__stdout__.write("CONCLUSAO_LOCAL " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_MASCOT_ENABLED="0",
                 LAYLAY_AVATAR_ATIVO="0", LAYLAY_CONTROLE_SQLITE=str(tmp_path_factory.mktemp("conclusao-sqlite"))),
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    assert processo.returncode == 0, processo.stderr[-4000:] + processo.stdout[-4000:]
    linha = next(l.removeprefix("CONCLUSAO_LOCAL ") for l in processo.stdout.splitlines()
                 if l.startswith("CONCLUSAO_LOCAL "))
    return json.loads(linha)


def test_conclusao_usa_owners_instalados(conclusoes_instaladas: dict) -> None:
    assert all(conclusoes_instaladas["instalacao"].values())


@pytest.mark.parametrize("dominio", ("arquivos", "musica"))
@pytest.mark.parametrize("modo", ("vigente", "mesma_conversa", "outra_vazia", "outra_com_turno"))
def test_conclusao_local_nao_recria_nem_altera_plano_de_outra_ocorrencia(
    conclusoes_instaladas: dict, dominio: str, modo: str,
) -> None:
    observado = conclusoes_instaladas["casos"][dominio + ":" + modo]
    assert observado["tratado"] is True and observado["fala"], "rota real deve concluir texto antes da troca"
    assert observado["plano_antes"]["id"] == observado["turno_id"]
    assert observado["origem"][-1]["role"] == "assistant"
    assert observado["origem"][-1]["content"] == "\n".join(observado["fala"])
    assert observado["destino"] == [], "histórico confirmado permanece na origem"
    if modo in ("vigente", "mesma_conversa"):
        assert observado["plano_final"]["id"] == observado["turno_id"]
        assert observado["plano_final"]["fase"] == "tratado_prioritario"
    else:
        assert observado["selecao"]["success"] is True
        assert observado["conversa_ativa"] == observado["b"]
        assert observado["plano_destino"].get("id") != observado["turno_id"]
        assert observado["plano_final"] == observado["plano_destino"], "retorno de A não pode publicar no plano de B"
        assert observado["trilha_final"] == observado["trilha_destino"]
