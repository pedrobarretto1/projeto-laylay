"""Composição instalada + USB real: tarefa local interrompe intenção corporal.

Uma tarefa de leitura realmente executada, e emoção como estímulo diagnóstico.
Não mede deslocamento, não executa saída do modelo nem altera configuração.
"""
from pathlib import Path
import json
import sys
import tempfile
import threading
import time
import uuid

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
DESTINO = RAIZ / "artifacts/rosto_oled/continuidade_corporal"
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(DESTINO / "instancia_sonda")
import laylay
from memoria_sqlite import MemoriaSQLite
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao

estado, rosto, corpo = laylay._estado_compartilhado_runtime, laylay._rosto_oled_runtime, laylay._corpo_motor_runtime
fim = threading.Event()
trilha, etapas, fases = [], [], []
abrir = rosto.abrir_serial


class SerialObservada:
    def __init__(self, porta):
        self.serial, self.buffer = abrir(porta), bytearray()
    def write(self, dados):
        trilha.append({"tx": dados.decode().strip(), "tempo": time.monotonic()})
        return self.serial.write(dados)
    def read(self, tamanho):
        dados = self.serial.read(tamanho)
        self.buffer.extend(dados)
        while b"\n" in self.buffer:
            linha, _, resto = self.buffer.partition(b"\n")
            self.buffer = bytearray(resto)
            texto = linha.decode(errors="replace").strip()
            if texto.startswith(("ACK ", "MACK", "SACK", "EACK", "NACK", "ERROR")):
                trilha.append({"rx": texto, "tempo": time.monotonic()})
        return dados
    def close(self):
        self.serial.close()


def turno(identidade, texto="diagnóstico de continuidade corporal"):
    estado.atualizar_campos("mental", turno_atual={"id": identidade, "retrato_id": identidade, "texto": texto},
        retrato_turno_atual={"id": identidade, "texto": texto},
        plano_turno_atual={"id": identidade, "retrato_id": identidade, "texto_usuario": texto,
            "decisao_turno": {"turno_id": identidade}, "fase": "executado", "ts": time.time()})


def emocao(nome):
    evento = criar_evento_emocional_causal(origem="controle_rosto", causa="ensaio de continuidade autorizado",
        evidencia_ref="diagnostico:continuidade_corporal", natureza_evidencia="fato_observado",
        responsabilidade="usuario", confianca=.99, relevancia=.95, intensidade=2,
        permite_expressao=True, emocao=nome, nivel=2, ts=time.time(), validade_s=90)
    estado.atualizar("conversacional", lambda atual: aplicar_evento_emocional(atual, evento, agora=time.time()))
    assert rosto.sincronizar()


def observar_fases():
    while not fim.wait(.025):
        i = corpo.modelo_para_mente().get("intencao_em_curso") or {}
        chave = (i.get("id"), i.get("fase"))
        if not fases or (fases[-1].get("id"), fases[-1].get("fase")) != chave:
            fases.append({**i, "tempo": time.monotonic()})


supervisor = threading.Thread(target=lambda: rosto.executar(deve_parar=fim.is_set, aguardar_fn=fim.wait), daemon=True)
observador = threading.Thread(target=observar_fases, daemon=True)
falha = ""
consulta = {}
with tempfile.TemporaryDirectory(prefix="laylay_continuidade_") as pasta:
    motor = laylay._motor_aprendizado_runtime
    memoria_anterior, maturidade_anterior = motor.memoria, motor.maturidade.memoria
    motor.memoria = motor.maturidade.memoria = MemoriaSQLite(str(Path(pasta) / "aprendizado.sqlite"))
    estado.atualizar_campos("mental", historico_corporal=[], experiencia_corporal={})
    rosto.abrir_serial = SerialObservada
    try:
        supervisor.start()
        prazo = time.monotonic() + 10
        while time.monotonic() < prazo and not rosto.diagnostico()["aplicacao_confirmada"]:
            time.sleep(.05)
        assert rosto.diagnostico()["aplicacao_confirmada"], rosto.diagnostico()
        time.sleep(3.3)
        turno("continuidade-a")
        texto = "ative modo companhia com rodas suspensas"
        assert corpo.executar("CORPO_COMPANHIA", {"acao": "ativar", "passeio": False},
            autorizacao=classificar_modalidade_turno(texto))["ok"]
        observador.start()
        emocao("triste")
        retorno = {}
        executor = threading.Thread(target=lambda: retorno.update(corpo.companhia.processar()), daemon=True)
        executor.start()
        prazo = time.monotonic() + 5
        while time.monotonic() < prazo and not any("rx" in e and e["rx"].startswith("MACK") for e in trilha):
            time.sleep(.01)
        assert any("rx" in e and e["rx"].startswith("MACK") for e in trilha), "sem motor confirmado antes da tarefa"
        def ler_codigo():
            # Mantém o escopo real por tempo suficiente para o corpo observar a tarefa.
            dados = (RAIZ / "mente_laylay/autonomia/companhia_corporal.py").read_bytes()
            assert dados
            assert not corpo.companhia._revogada.wait(.6)
            return ResultadoAcao(intent="FILE_READ", status="leitura_confirmada", origem="executor",
                executou=True, confirmado=True, ok=True, id_solicitacao=uuid.uuid4().hex)
        laylay._atividade_operacional_runtime.executar(ler_codigo)
        executor.join(8)
        assert not executor.is_alive(), "gesto não interrompeu"
        assert retorno.get("ok") is False, retorno
        i = estado.obter_copia("mental", "intencao_corporal", {})
        assert i["fase"] == "interrompida"
        assert any("rx" in e and e["rx"].startswith("SACK") for e in trilha)
        etapas.append({"fase": "tarefa_real_interrompeu", "intencao": i,
                       "experiencia": estado.obter_copia("mental", "experiencia_corporal", {})})
        assert corpo.companhia.diagnostico()["ativa"], "interrupção por contexto não revoga a companhia"
        time.sleep(3.2)
        turno("continuidade-b")
        emocao("envergonhada")
        assert corpo.companhia.processar()["ok"]
        modelo = corpo.modelo_para_mente()
        i = modelo["intencao_em_curso"]
        assert i["fase"] == "acomodando" and i["resultado"]["parada_confirmada"]
        assert i["resultado"]["experiencia_id"] == modelo["ultima_experiencia"]["id"]
        assert modelo["ultima_experiencia"]["objetivo_id"] == i["objetivo_id"]
        etapas.append({"fase": "novo_objetivo_concluido", "modelo": modelo})
        quantidade = sum(e.get("tx", "").startswith("MOTOR ") for e in trilha)
        pergunta = "O que você estava fazendo com o corpo, como terminou e o que não foi medido?"
        resposta = laylay._registro_modelo_llm_runtime.enviar([
            {"role": "system", "content": formatar_modelo_corporal(modelo)},
            {"role": "user", "content": pergunta}], max_tokens=400, timeout=35,
            modo_rapido=True, _permitir_durante_interacao=True, _contexto_fechado=True, _com_tools=False)
        consulta = {"pergunta": pergunta, "resposta": resposta, "executou_proposta": False}
        consulta["json_valido"] = isinstance(json.loads(resposta), dict)
        assert sum(e.get("tx", "").startswith("MOTOR ") for e in trilha) == quantidade
    except Exception as erro:
        falha = type(erro).__name__ + ": " + str(erro)
    finally:
        corpo.companhia.revogar("fim_sonda_continuidade")
        rosto.parar_corpo()
        fim.set()
        supervisor.join(5)
        if observador.is_alive(): observador.join(2)
        rosto.encerrar()
        rosto.abrir_serial = abrir
        motor.memoria, motor.maturidade.memoria = memoria_anterior, maturidade_anterior
        dados = {"falha": falha, "etapas": etapas, "fases": fases, "trilha": trilha,
                 "consulta_modelo": consulta, "prova_deslocamento": False,
                 "emocao_diagnostica": True, "feedback_usuario_real": False}
        destino = DESTINO / "receipt_fisico.json"
        destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"receipt": str(destino), "falha": falha}, ensure_ascii=False), flush=True)
if falha: raise SystemExit(1)
