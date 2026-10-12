"""Sonda do caminho principal real, modelo configurado e USB; sem abrir a UI.

O texto é um estímulo de diagnóstico. Não inventa receipts de ações no PC.
Rodas suspensas, montagem e movimentos já autorizados por Pedro.
"""
from pathlib import Path
import json
import sys
import threading
import time

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
DESTINO = RAIZ / "artifacts/rosto_oled/corpo_mente_v1"
DESTINO.mkdir(parents=True, exist_ok=True)

from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(DESTINO / "instancia_sonda")
import laylay

estado = laylay._estado_compartilhado_runtime
rosto = laylay._rosto_oled_runtime
corpo = laylay._corpo_motor_runtime
trilha, respostas = [], []
abrir = rosto.abrir_serial
if "--serial-simulada" in sys.argv:
    from scripts.tests.test_presenca_corporal_v2 import EspPresenca
    esp_simulado = EspPresenca()
    abrir = lambda _: esp_simulado


class CapturaSerial:
    def __init__(self, porta):
        self.serial = abrir(porta)
        self.pendente = bytearray()
    def write(self, dados):
        trilha.append({"direcao": "tx", "tempo": time.monotonic(), "pacote": dados.decode().strip()})
        return self.serial.write(dados)
    def read(self, tamanho):
        dados = self.serial.read(tamanho)
        self.pendente.extend(dados)
        while b"\n" in self.pendente:
            linha, _, resto = self.pendente.partition(b"\n")
            self.pendente = bytearray(resto)
            texto = linha.decode(errors="replace").strip()
            if texto.startswith(("ACK ", "EACK ", "MACK ", "SACK ", "NACK ", "SOUNDACK ", "ERROR ")):
                trilha.append({"direcao": "rx", "tempo": time.monotonic(), "pacote": texto})
        return dados
    def close(self): self.serial.close()


ctx_getter = laylay._resposta_ia_runtime._contexto_getter
class CapturaModelo:
    def __init__(self, modelo): self.modelo = modelo
    def executar(self, pedido):
        assert any("MEU CORPO AGORA" in str(m.get("content")) for m in pedido.mensagens), "retrato perdeu-se antes da LLM principal"
        r = self.modelo.executar(pedido)
        respostas.append({"texto": r.texto, "sucesso": r.sucesso})
        return r
def contexto_observado():
    ctx = dict(ctx_getter())
    ctx["modelo_llm"] = CapturaModelo(ctx["modelo_llm"])
    return ctx

rosto.abrir_serial = CapturaSerial
laylay._resposta_ia_runtime._contexto_getter = contexto_observado
fim = threading.Event()
supervisor = threading.Thread(target=lambda: rosto.executar(deve_parar=fim.is_set, aguardar_fn=fim.wait), daemon=True)
falha, retorno, plano, modelo = "", {}, {}, {}
try:
    supervisor.start()
    prazo = time.monotonic() + 10
    while time.monotonic() < prazo and not rosto.diagnostico()["aplicacao_confirmada"]: time.sleep(.05)
    assert rosto.diagnostico()["aplicacao_confirmada"], "USB não conectou"
    time.sleep(3.2)
    assert corpo.companhia.processar()["ok"], "concessão USB não disponível"
    print("Sonda: corpo conectado; chamando o cérebro real", flush=True)
    texto = "gosto muito de voce"
    if "--componentes" not in sys.argv:
        if "--chat-ativo" in sys.argv:
            # Mesmo setter da entrada de conversa real. Sem ele, a sonda fora
            # de chat permitia que resumo diário disputasse a chamada principal.
            laylay._interacao_chat_runtime.atualizar_estado(True)
        laylay._resposta_ia_runtime.processar(texto, origem="diagnostico_corpo_mente")
    else:
        # Controle independente para separar a integração corporal do bloqueio
        # de orçamento/contexto do fluxo completo. Usa modelo, composição do
        # turno, prompt corporal, estado emocional e executores reais. O pacote
        # fechado é diagnóstico; não modifica a configuração do aplicativo.
        from mente_laylay.integracao.registro_conversa_llm import PedidoModelo
        from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
        from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
        from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional
        laylay._interpretador_semantico_runtime.modo = "off"
        turno = laylay._composicao_turno_runtime.iniciar(texto, origem="diagnostico_corpo_mente")
        # Estímulo causal explicitamente diagnóstico. O modelo recebe e escolhe
        # como expressá-lo; o teste não o apresenta como emoção humana observada.
        evento = criar_evento_emocional_causal(origem="controle_rosto", causa="estímulo diagnóstico de alegria para corpo integrado",
            evidencia_ref="diagnostico:corpo_mente", natureza_evidencia="fato_observado", responsabilidade="usuario",
            confianca=.99, relevancia=.95, intensidade=2, permite_expressao=True, emocao="alegre", nivel=2, ts=time.time(), validade_s=120)
        estado.substituir("conversacional", aplicar_evento_emocional({}, evento, agora=time.time()))
        assert rosto.sincronizar()
        instrucao = laylay._contexto_prompt_runtime.preparar_instrucao_rapida(texto)
        assert "MEU CORPO AGORA" in instrucao
        pedido = PedidoModelo.criar([
            {"role": "system", "content": "Você é Laylay, uma companhia expressiva. Responda em português somente com JSON: fala (curta), emocao, nivel (1 a 3), comandos (lista vazia), intencao_corporal (objeto com nome). Escolha uma emoção e intenção coerentes com a fala e o corpo disponível. Não afirme efeito de motores antes do resultado."},
            {"role": "system", "content": instrucao},
            {"role": "user", "content": texto}],
            com_tools=False, max_tokens=256, contexto_fechado=True, prioridade_interativa=True, tipo_chamada="principal", timeout=30)
        r = CapturaModelo(laylay._registro_modelo_llm_runtime).executar(pedido)
        assert r.sucesso, r.texto
        p = ContratoPropostaPrincipal(turno["id"], texto, r.texto, r.sucesso)
        laylay._composicao_turno_runtime.atualizar_proposta("resposta_planejada", p)
        laylay._composicao_turno_runtime.atualizar_proposta("executado", p)
        dados = json.loads(r.texto)
        # A escolha de intenção não substitui o episódio emocional canônico.
        # Mantemos a causa diagnóstico que estava no prompt da chamada real.
    plano = estado.obter_copia("mental", "plano_turno_atual", {})
    assert plano.get("intencao_corporal"), "modelo não publicou uma intenção corporal válida"
    print("Intenção da IA: " + plano["intencao_corporal"]["nome"], flush=True)
    assert plano["intencao_corporal"]["nome"] == "expressar", "para este estímulo só validamos o gesto emocional"
    prazo = time.monotonic() + 4
    while time.monotonic() < prazo:
        retorno = corpo.companhia.processar()
        if retorno.get("ok"): break
        time.sleep(.25)
    plano = estado.obter_copia("mental", "plano_turno_atual", {})
    assert retorno.get("ok"), retorno
    assert plano["intencao_corporal"]["resultado"]["confirmado"] is True
    modelo = corpo.modelo_para_mente(plano["id"])
    assert modelo["ultima_experiencia"]["prova_deslocamento"] is False
    print("Sonda: gesto confirmado pelo ESP e devolvido à mente", flush=True)
except Exception as erro:
    falha = type(erro).__name__ + ": " + str(erro)
finally:
    corpo.companhia.revogar("fim_sonda_corpo_mente")
    corpo.transporte.parar_corpo()
    fim.set()
    supervisor.join(4)
    rosto.encerrar()
    laylay._resposta_ia_runtime._contexto_getter = ctx_getter
    dados = {"falha": falha, "retorno": retorno, "plano": plano, "modelo": modelo, "respostas_originais": respostas,
        "trilha": trilha, "observacao_humana": "pendente", "interface_aberta": False,
        "serial_simulada": "--serial-simulada" in sys.argv,
        "chat_ativo": "--chat-ativo" in sys.argv,
        "tipo": "componentes reais e modelo em pacote diagnóstico fechado" if "--componentes" in sys.argv else "runtime principal real com observadores de modelo e serial"}
    arquivo = "receipt_fluxo_chat_serial_simulada.json" if "--serial-simulada" in sys.argv else "receipt_componentes_fisico.json" if "--componentes" in sys.argv else "receipt_runtime_fisico.json"
    (DESTINO / arquivo).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"receipt": str(DESTINO / arquivo), "falha": falha}, ensure_ascii=False), flush=True)
if falha: raise SystemExit(1)
