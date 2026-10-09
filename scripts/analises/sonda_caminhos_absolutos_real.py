"""Prova caminhos literais no loop instalado, somente em arquivos próprios.

Conserva os artefatos. Dois arquivos de mesmo basename controlam a prioridade
do caminho sobre a memória recente. Não inicia editor nem apaga arquivos.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from scripts.analises.sonda_p16_falha_recuperacao_real import _interromper_sessao_criada


RAIZ = Path(__file__).resolve().parents[2]


_BOOTSTRAP_DIAGNOSTICO_PLANO = r'''
import functools, json, os, runpy, sys, threading, time, traceback
from pathlib import Path
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.conversas_runtime import GerenciadorConversasRuntime

destino = Path(os.environ["LAYLAY_SONDA_PUBLICACOES_PLANO"])
registros_lock = threading.RLock()

def registrar(registro):
    # A observação não pode interromper o owner depois de ele publicar estado.
    try:
        registro.update(ts=time.time(), monotonic=time.monotonic(), pid=os.getpid(),
                        thread=threading.current_thread().name,
                        pilha=[{"arquivo": f.filename, "linha": f.lineno, "funcao": f.name}
                               for f in traceback.extract_stack(limit=14)[:-2]])
        linha = json.dumps(registro, ensure_ascii=False) + "\n"
        with registros_lock:
            with destino.open("a", encoding="utf-8") as stream:
                stream.write(linha)
    except (OSError, TypeError, ValueError):
        pass

def identidade(estado):
    mental = estado.mental
    plano = mental.get("plano_turno_atual") or {}
    turno = mental.get("turno_atual") or {}
    retrato = mental.get("retrato_turno_atual") or {}
    return {
        "plano_id": plano.get("id"), "turno_id": turno.get("id"),
        "retrato_id": retrato.get("id"), "fase": plano.get("fase"),
        "receipts": [{k: r.get(k) for k in ("id_solicitacao", "intent", "status")}
                     for r in plano.get("comandos", []) if isinstance(r, dict)],
        "sessao_motivo": mental.get("sessao_conversa_motivo"),
        "sessao_ts": mental.get("sessao_conversa_ts"),
    }

def observar(nome):
    original = getattr(EstadoCompartilhadoRuntime, nome)
    @functools.wraps(original)
    def publicar(self, *args, **kwargs):
        # A API já usa este RLock; o diagnóstico lê antes/depois do mesmo commit.
        # Não reconstrói estado, não fornece receipt e não força sucesso.
        with self._lock:
            antes = identidade(self)
            retorno = original(self, *args, **kwargs)
            depois = identidade(self)
            if antes != depois:
                registrar({
                    "tipo": "estado", "api": nome,
                    "antes": antes, "depois": depois,
                })
            return retorno
    setattr(EstadoCompartilhadoRuntime, nome, publicar)

def observar_conversa(nome):
    original = getattr(GerenciadorConversasRuntime, nome)
    @functools.wraps(original)
    def chamar(self, *args, **kwargs):
        # Os métodos observados já usam este RLock. IDs/estado antes e depois
        # pertencem à mesma chamada; não guardar títulos, mensagens ou contexto.
        with self._lock:
            conversa_antes = self.id_ativo()
            with self.estado._lock:
                antes = identidade(self.estado)
            campos = {"tipo": "conversa", "api": "conversa." + nome,
                      "antes": antes, "depois": antes,
                      "conversa_antes": conversa_antes, "conversa_depois": conversa_antes}
            if nome == "selecionar":
                campos["conversa_solicitada"] = str(args[0] if args else kwargs.get("conversa_id") or "")[:128]
            registrar(dict(campos, etapa="entrada"))
            try:
                retorno = original(self, *args, **kwargs)
            except BaseException as erro:
                etapa, erro_tipo = "excecao", type(erro).__name__
                raise
            else:
                etapa, erro_tipo = "retorno", ""
                return retorno
            finally:
                with self.estado._lock:
                    depois = identidade(self.estado)
                registrar(dict(campos, etapa=etapa, erro_tipo=erro_tipo,
                               depois=depois, conversa_depois=self.id_ativo()))
    setattr(GerenciadorConversasRuntime, nome, chamar)

for nome in ("substituir", "atualizar_dominios", "mesclar_campos"):
    observar(nome)
for nome in ("selecionar", "criar", "reaplicar_ativa", "iniciar_sem_conversa"):
    observar_conversa(nome)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
'''


_BOOTSTRAP_CONTROLE_TROCA = r'''
# Estímulo optativo: troca de chat depois do receipt e da saída, antes da fase.
# SQLite próprio evita ler ou selecionar conversas pessoais para este controle.
import socket
from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime

# A ponte atende uma interface por sessão. O controle usa esse lugar com o
# cliente TCP abaixo; main continua iniciando a ponte real, sem lançar GUI.
def cliente_controlado(self, caminho):
    registrar({"tipo": "controle_cliente_tcp", "interface_grafica": False})
    return False
DesktopBridgeRuntime.iniciar_cliente = cliente_controlado

sqlite_inicializar = MemoriaSQLite.__init__
def sqlite_proprio(self, caminho, *args, **kwargs):
    return sqlite_inicializar(self, str(Path(os.environ["LAYLAY_SONDA_SQLITE"]) / Path(caminho).name), *args, **kwargs)
MemoriaSQLite.__init__ = sqlite_proprio

def resposta_tipo(cliente, tipo):
    limite = time.monotonic() + 5
    while time.monotonic() < limite:
        cliente.settimeout(max(0.05, limite - time.monotonic()))
        dados = b""
        while not dados.endswith(b"\n"):
            bloco = cliente.recv(1)
            assert bloco, "ponte fechou antes da seleção controlada"
            dados += bloco
        mensagem = json.loads(dados)
        if mensagem.get("type") == tipo:
            return mensagem
    raise AssertionError("resposta da ponte ausente")

inicializar_resposta = RespostaIARuntime.__init__
def resposta_observada(self, *, contexto_getter, **kwargs):
    controle = {"preparado": False, "trocado": False}
    ns = contexto_getter.__globals__
    def contexto():
        ctx = contexto_getter()
        if not controle["preparado"]:
            conversas = ns["_gerenciador_conversas_runtime"]
            a = conversas.id_ativo()
            assert a, "entrada real deve ter criado a conversa de origem"
            b = conversas.criar("controle P16 troca após saída")["id"]
            assert conversas.selecionar(a), "preparação deve restaurar origem antes do turno"
            controle.update(preparado=True, a=a, b=b)
        prioritario = ctx["processar_comandos_prioritarios"]
        def processar_e_trocar(texto):
            retorno = prioritario(texto)
            estado = ns["_estado_compartilhado_runtime"]
            plano = estado.obter_copia("mental", "plano_turno_atual")
            receipts = plano.get("comandos") or []
            registrar({"tipo": "controle_callback",
                "statuses": [r.get("status") for r in receipts]})
            if (not controle["trocado"] and len(receipts) == 1
                    and receipts[0].get("status") == "conteudo_atualizado"):
                assert retorno is True and len(receipts) == 1
                receipt = receipts[0]
                assert receipt.get("origem") == "executor" and receipt.get("confirmado") is True
                assert receipt.get("status") == "conteudo_atualizado" and receipt.get("id_solicitacao")
                textos = ns["_orquestrador_fala_runtime"].textos_publicados_turno(plano["id"])
                assert textos, "troca deve ocorrer depois de texto aceito na origem"
                antes = identidade(estado)
                ponte = ns["_desktop_bridge_runtime"]
                with socket.create_connection(ponte.endereco, timeout=5) as cliente:
                    cliente.sendall((json.dumps({"type": "hello", "token": ponte.token}) + "\n").encode())
                    resposta_tipo(cliente, "snapshot")
                    cliente.sendall((json.dumps({"type": "conversation_select", "id": "troca-controlada-p16",
                        "conversation_id": controle["b"]}) + "\n").encode())
                    selecionado = resposta_tipo(cliente, "conversations_state")
                assert selecionado.get("success") is True
                assert ns["_gerenciador_conversas_runtime"].id_ativo() == controle["b"]
                controle["trocado"] = True
                registrar({"tipo": "controle_troca", "antes": antes, "depois": identidade(estado),
                    "origem": controle["a"], "destino": controle["b"], "texto_confirmado": bool(textos),
                    "receipt": {k: receipt.get(k) for k in ("id_solicitacao", "intent", "status", "origem", "executou", "confirmado")}})
            return retorno
        ctx["processar_comandos_prioritarios"] = processar_e_trocar
        trace = ctx["atualizar_trace_diagnostico"]
        def atualizar_trace(*args, **campos):
            resultado = trace(*args, **campos)
            if controle["trocado"] and campos.get("fase") == "conclusao_local_obsoleta":
                registrar({"tipo": "controle_recusa", "fase": campos["fase"],
                    "depois": identidade(ns["_estado_compartilhado_runtime"]),
                    "ativa": ns["_gerenciador_conversas_runtime"].id_ativo()})
            return resultado
        ctx["atualizar_trace_diagnostico"] = atualizar_trace
        return ctx
    inicializar_resposta(self, contexto_getter=contexto, **kwargs)
RespostaIARuntime.__init__ = resposta_observada
'''


def main(*, diagnosticar_plano: bool = False, controlar_troca: bool = False) -> int:
    diagnosticar_plano = diagnosticar_plano or controlar_troca
    identidade = uuid.uuid4().hex
    pasta = (RAIZ / "resultados_testes" / ("caminhos_absolutos_" + identidade)).resolve()
    assert pasta.parent == (RAIZ / "resultados_testes").resolve()
    pasta.mkdir(parents=True, exist_ok=False)
    downloads = (Path.home() / "Downloads").resolve()
    base = (downloads / ("p16_caminhos_" + identidade[:10])).resolve()
    assert base.parent == downloads
    base.mkdir(exist_ok=False)
    a = base / "prova.txt"
    b = base / "pasta com espaços" / "prova.txt"
    ausente = base / "outra pasta" / "prova.txt"
    b.parent.mkdir()
    a.write_text("CONTROLE ORIGINAL", encoding="utf-8")
    b.write_text("ALVO ORIGINAL", encoding="utf-8")
    comandos = (
        f"Leia {a}",
        f'Leia "{b}"',
        f'Escreva CONTEÚDO NOVO no arquivo "{b}"',
        f'Acrescente "LINHA ADICIONAL" no arquivo "{b}"',
        f"Leia {a}",
        f'Leia "{ausente}"',
        f"Leia {b}",
    )
    alvos = (a, b, b, b, a, ausente, b)
    statuses = ("conteudo_lido", "conteudo_lido", "conteudo_atualizado",
                "conteudo_acrescentado", "conteudo_lido", "arquivo_indisponivel", "conteudo_lido")
    expectativas = {
        i + 1: {"nome": f"caminho_literal_{i+1}", "dominio": "arquivos",
                "intents_any": (("CREATE_FILE",) if i in (2, 3) else ("FILE_READ",)),
                "statuses_any": (status,), "confirmado": i != 5}
        for i, status in enumerate(statuses)
    }
    roteiro = pasta / "roteiro_caminhos_absolutos.py"
    roteiro.write_text(
        f"COMANDOS = {comandos!r}\nEXPECTATIVAS_SEMANTICAS = {expectativas!r}\n"
        "ATRASO_INICIAL_S = 4\nTIMEOUT_RESPOSTA_S = 45\n"
        "SILENCIAR_VOZ_DURANTE_TESTE = True\nAGUARDAR_CONFIRMACAO_EXECUCAO = True\n"
        "INTERVALO_ENTRE_COMANDOS_S = 1\nPARAR_SEM_RESPOSTA = True\nENCERRAR_AO_FINAL = True\n",
        encoding="utf-8",
    )
    prova = {"status": "em_execucao", "arquivo_controle": str(a), "arquivo_alvo": str(b),
             "diagnostico_plano": diagnosticar_plano,
             "troca_controlada": controlar_troca,
             "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip()}
    processo = None
    iniciado_em = time.time()
    print(f"CAMINHOS_PROVA pasta={pasta}", flush=True)
    try:
        ambiente = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_MASCOT_ENABLED="0",
                        LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0")
        argumentos = [sys.executable, "-u"]
        if diagnosticar_plano:
            ambiente["LAYLAY_SONDA_PUBLICACOES_PLANO"] = str(pasta / "publicacoes_plano.jsonl")
            bootstrap = _BOOTSTRAP_DIAGNOSTICO_PLANO
            if controlar_troca:
                banco = pasta / "sqlite_proprio"
                banco.mkdir()
                ambiente["LAYLAY_SONDA_SQLITE"] = str(banco)
                marcador = "sys.argv = sys.argv[1:]"
                assert bootstrap.count(marcador) == 1
                bootstrap = bootstrap.replace(marcador, _BOOTSTRAP_CONTROLE_TROCA + "\n" + marcador)
            argumentos.extend(["-c", bootstrap])
        argumentos.extend([str(RAIZ / "laylay.py"), "--roteiro", str(roteiro),
                           "--resultado-raiz", str(pasta / "runtime")])
        with (pasta / "processo.log").open("w", encoding="utf-8") as log:
            processo = subprocess.Popen(
                argumentos,
                cwd=RAIZ, env=ambiente, stdout=log, stderr=subprocess.STDOUT,
            )
            processo.wait(timeout=360)
        assert processo.returncode == 0, processo.returncode
        diretorios = list((pasta / "runtime").glob("roteiro_caminhos_absolutos-*"))
        assert len(diretorios) == 1, diretorios
        diretorio = diretorios[0]
        checkpoint = json.loads((diretorio / "checkpoint.json").read_text(encoding="utf-8"))
        if controlar_troca:
            # O roteiro conserva o snapshot identificado com receipt capturado
            # na saída de A. A seleção posterior não invalida esse efeito; as
            # sete barreiras comuns abaixo ainda exigem o resultado próprio.
            registros = [json.loads(l) for l in (pasta / "publicacoes_plano.jsonl").read_text(encoding="utf-8").splitlines() if l]
            trocas = [r for r in registros if r.get("tipo") == "controle_troca"]
            recusas = [r for r in registros if r.get("tipo") == "controle_recusa"]
            assert len(trocas) == len(recusas) == 1
            troca, recusa = trocas[0], recusas[0]
            assert troca["texto_confirmado"] is True and troca["antes"]["plano_id"]
            assert recusa["ativa"] == troca["destino"] and troca["origem"] != troca["destino"]
            assert not recusa["depois"]["plano_id"] and recusa["depois"] == troca["depois"]
            intervalo = [r for r in registros if r.get("tipo") == "estado"
                         and troca["monotonic"] < r["monotonic"] <= recusa["monotonic"]]
            assert not any(r["depois"]["plano_id"] or r["depois"]["fase"] for r in intervalo)
            prova.update(troca=troca, recusa=recusa, interface_grafica_no_controle=False)
        assert checkpoint.get("concluido") is True, checkpoint.get("itens")
        itens = checkpoint.get("itens") or []
        assert len(itens) == len(comandos)
        assert all(item.get("status") == "respondido" and item.get("processamento_concluido") is True
                   and item.get("resultado_turno_concluido") is True for item in itens)
        registros = [json.loads(linha) for linha in (diretorio / "planos.jsonl").read_text(
            encoding="utf-8").splitlines() if linha.strip()]
        assert [r["indice"] for r in registros] == list(range(len(comandos)))
        receipts = []
        for i, registro in enumerate(registros):
            etapas = registro["plano"].get("comandos") or []
            assert len(etapas) == 1, etapas
            receipt = etapas[0]
            assert receipt.get("origem") == "executor", receipt
            assert receipt.get("intent") == ("CREATE_FILE" if i in (2, 3) else "FILE_READ"), receipt
            assert receipt.get("status") == statuses[i], receipt
            assert receipt.get("executou") is (i != 5) and receipt.get("confirmado") is (i != 5), receipt
            caminho = receipt.get("params", {}).get("caminho") or receipt.get("params", {}).get("alvo")
            assert os.path.normcase(os.path.abspath(str(caminho))) == os.path.normcase(str(alvos[i])), receipt
            if i != 5:
                assert os.path.normcase(os.path.abspath(receipt.get("alvo", ""))) == os.path.normcase(str(alvos[i])), receipt
            assert receipt.get("id_solicitacao"), receipt
            receipts.append(receipt)
        assert len({r["id_solicitacao"] for r in receipts}) == len(comandos)
        if controlar_troca:
            assert troca["receipt"]["id_solicitacao"] == receipts[2]["id_solicitacao"]
        assert a.read_text(encoding="utf-8") == "CONTROLE ORIGINAL"
        assert b.read_text(encoding="utf-8") == "CONTEÚDO NOVO\nLINHA ADICIONAL"
        assert not ausente.exists()
        assert "CONTROLE ORIGINAL" in itens[0]["resposta"] and "ALVO ORIGINAL" in itens[1]["resposta"]
        assert "CONTEÚDO NOVO" in itens[6]["resposta"] and "LINHA ADICIONAL" in itens[6]["resposta"]
        prova.update(status=("green_loop_e_conteudo_com_troca_controlada" if controlar_troca else "green_loop_e_conteudo"), receipts=receipts,
                     hash_controle=hashlib.sha256(a.read_bytes()).hexdigest(),
                     hash_alvo=hashlib.sha256(b.read_bytes()).hexdigest(), diretorio_runtime=str(diretorio))
        print("CAMINHOS_PROVA sete turnos, alvos e conteúdo físico confirmados.", flush=True)
        return 0
    except Exception as erro:
        prova.update(status="red", erro=f"{type(erro).__name__}: {erro}")
        raise
    finally:
        try:
            if processo is not None and processo.poll() is None:
                _interromper_sessao_criada(processo, iniciado_em)
        finally:
            (pasta / "prova.json").write_text(json.dumps(prova, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnosticar-plano", action="store_true")
    parser.add_argument("--controlar-troca", action="store_true",
                        help="Seleciona chat próprio após a terceira saída para provar recusa da fase tardia, preservando as barreiras do roteiro.")
    opcoes = parser.parse_args()
    raise SystemExit(main(diagnosticar_plano=opcoes.diagnosticar_plano, controlar_troca=opcoes.controlar_troca))
