"""USB real → experiência/SQLite/feedback compartilhados; diagnóstico isolado.

Movimento manual e gesto causal são físicos. Emoção e feedback são estímulos
diagnósticos e ficam em SQLite temporário, sem ensinar preferências a Pedro.
Não altera configuração, firmware ou permissões salvas.
"""
from pathlib import Path
import json
import sys
import tempfile
import threading
import time

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
DESTINO = RAIZ / "artifacts/rosto_oled/corpo_integrado_v1"
DESTINO.mkdir(parents=True, exist_ok=True)
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(DESTINO / "instancia_sonda")
import laylay
from memoria_sqlite import MemoriaSQLite
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional
from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal

estado, rosto, corpo = laylay._estado_compartilhado_runtime, laylay._rosto_oled_runtime, laylay._corpo_motor_runtime
trilha, etapas, modelos = [], [], []
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

def turno(texto, identidade):
    t = {**classificar_modalidade_turno(texto), "id": identidade, "retrato_id": identidade, "texto": texto}
    estado.atualizar_campos("mental", turno_atual=t,
        retrato_turno_atual={"id": identidade, "texto": texto},
        plano_turno_atual={"id": identidade, "retrato_id": identidade, "texto_usuario": texto,
            "decisao_turno": {"turno_id": identidade}, "fase": "executado", "ts": time.time()})

fim = threading.Event()
supervisor = threading.Thread(target=lambda: rosto.executar(deve_parar=fim.is_set, aguardar_fn=fim.wait), daemon=True)
falha = ""
consulta_modelo = {}
with tempfile.TemporaryDirectory(prefix="laylay_experiencia_corporal_") as pasta:
    motor = laylay._motor_aprendizado_runtime
    memoria_anterior, maturidade_anterior = motor.memoria, motor.maturidade.memoria
    motor.memoria = motor.maturidade.memoria = MemoriaSQLite(str(Path(pasta) / "aprendizado.sqlite"))
    estado.atualizar_campos("mental", historico_corporal=[], experiencia_corporal={})
    rosto.abrir_serial = SerialObservada
    contexto = laylay._composicao_ciclo_comandos_runtime.contexto
    contexto._servicos_estaticos["enviar_mensagem"] = None
    contexto._servicos_estaticos["falar_com_lipsync"] = lambda *a, **k: None
    laylay._orquestrador_fala_runtime.falar = lambda *a, **k: True
    try:
        supervisor.start()
        limite = time.monotonic() + 10
        while time.monotonic() < limite and not rosto.diagnostico()["aplicacao_confirmada"]:
            time.sleep(.05)
        assert rosto.diagnostico()["aplicacao_confirmada"], rosto.diagnostico()
        time.sleep(3.3)
        texto = "ande para frente"
        turno(texto, "sonda-manual")
        ciclo = laylay._composicao_ciclo_comandos_runtime.ciclo
        pedido, rota = ciclo.resolver_comando_natural(texto, "diagnostico_experiencia")
        assert pedido and pedido["intent"] == "CORPO_MOVER", rota
        assert ciclo.executar_intencao(pedido, texto)
        e = estado.obter_copia("mental", "experiencia_corporal", {})
        assert e["confirmado"] and e["origem_intencao"] == "pedido_usuario" and not e["prova_deslocamento"]
        etapas.append({"fase": "pedido_manual_real", "experiencia": e})
        texto = "ative modo companhia com rodas suspensas"
        turno(texto, "sonda-companhia")
        pedido, rota = ciclo.resolver_comando_natural(texto, "diagnostico_experiencia")
        assert pedido and ciclo.executar_intencao(pedido, texto), rota
        time.sleep(2.1)
        evento = criar_evento_emocional_causal(origem="controle_rosto", causa="diagnóstico autorizado de experiência corporal",
            evidencia_ref="diagnostico:experiencia_corporal", natureza_evidencia="fato_observado", responsabilidade="usuario",
            confianca=.99, relevancia=.95, intensidade=2, permite_expressao=True, emocao="alegre", nivel=2, ts=time.time(), validade_s=90)
        estado.atualizar("conversacional", lambda atual: aplicar_evento_emocional(atual, evento, agora=time.time()))
        assert rosto.sincronizar()
        assert corpo.companhia.processar()["ok"]
        e = estado.obter_copia("mental", "experiencia_corporal", {})
        assert e["confirmado"] and e["origem_intencao"] == "mente_causal"
        assert len(estado.obter_copia("mental", "historico_corporal", [])) == 2
        etapas.append({"fase": "gesto_causal_estimulacao_diagnostica", "experiencia": e})
        assert any(h["tipo"] == "execucao_corporal" for h in motor.memoria.listar_hipoteses_aprendizado())
        texto = "gostei desse movimento"
        turno(texto, "sonda-feedback")
        modelo = corpo.modelo_para_mente("sonda-feedback")
        laylay._adaptadores_aplicacao_runtime.registrar_mente_curta(texto, "feedback de diagnóstico")
        feedback = estado.obter_copia("mental", "feedback_corporal", {})
        assert feedback["experiencia_id"] == e["id"]
        etapas.append({"fase": "feedback_simulado_sqlite_temporario", "feedback": feedback})
        modelos.append(modelo)
        corpo.companhia.revogar("fim_movimentos_diagnostico")
        assert rosto.parar_corpo()["parada_confirmada"]
        # Consulta ao modelo configurado; nenhuma proposta retornada é executada.
        pergunta = "O que sua experiência corporal registra agora e o que você ainda não pode confirmar sobre movimento físico?"
        resposta = laylay._registro_modelo_llm_runtime.enviar([
            {"role": "system", "content": formatar_modelo_corporal(corpo.modelo_para_mente())},
            {"role": "user", "content": pergunta}], max_tokens=512, timeout=35,
            modo_rapido=True, _permitir_durante_interacao=True, _contexto_fechado=True, _com_tools=False)
        consulta_modelo = {"pergunta": pergunta, "resposta": resposta, "executou_proposta": False}
        consulta_modelo["json_valido"] = isinstance(json.loads(resposta), dict)
    except Exception as erro:
        falha = type(erro).__name__ + ": " + str(erro)
    finally:
        corpo.companhia.revogar("fim_sonda_experiencia")
        rosto.parar_corpo()
        fim.set()
        supervisor.join(5)
        rosto.encerrar()
        modelos.append(corpo.modelo_para_mente())
        rosto.abrir_serial = abrir
        motor.memoria, motor.maturidade.memoria = memoria_anterior, maturidade_anterior
        dados = {"falha": falha, "etapas": etapas, "modelos": modelos, "trilha": trilha,
            "consulta_modelo": consulta_modelo, "feedback_usuario_real": False,
            "aprendizado_usuario_alterado": False, "prova_deslocamento": False, "observacao_humana": "pendente"}
        (DESTINO / "receipt_fisico.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"falha": falha, "etapas": len(etapas)}, ensure_ascii=False), flush=True)
if falha:
    raise SystemExit(1)
