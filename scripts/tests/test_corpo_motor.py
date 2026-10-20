"""Movimento corporal: autoridade canônica e receipt limitado à ponte."""
import pytest
from types import SimpleNamespace
from copy import deepcopy
import importlib

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.capacidades import consultar_capacidade
from mente_laylay.cognicao.gramatica_corpo import detectar_intencao_corpo
from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from mente_laylay.memoria_mental.resultado_acao import interpretar_tratamento_operacional
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_resultado_execucao
from mente_laylay.memoria_mental.compatibilidade_contexto import resolver_repeticao_ultima_acao
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime


@pytest.mark.parametrize("texto", [
    "anda para frente", "gira para a esquerda", "pare os motores",
    "pode andar um pouquinho?", "ande para trás", "vire para a direita",
])
def test_pedido_corporal_atual_tem_autoridade_canonicamente_classificada(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno.get("autoriza_execucao") is True, turno


@pytest.mark.parametrize("texto", [
    "não ande para frente", "se eu pedir para andar", "você consegue andar?",
    "como faço para andar?", "eu vou andar para frente", "ontem ela andou",
])
def test_conversa_corporal_nao_concede_autoridade(texto):
    assert classificar_modalidade_turno(texto).get("autoriza_execucao") is not True


def test_catalogo_descreve_receipt_da_ponte_sem_prometer_deslocamento():
    capacidade = consultar_capacidade("CORPO_MOVER")
    assert capacidade.get("dominio") == "corpo_motor", capacidade
    assert "deslocamento" in capacidade["limites"]


@pytest.mark.parametrize("texto,direcao", [
    ("pode andar um pouquinho?", "frente"), ("ande para trás", "tras"),
    ("vire para a esquerda", "esquerda"), ("gire à direita", "direita"),
])
def test_detector_deriva_entidades_sem_criar_outro_owner_de_autorizacao(texto, direcao):
    assert detectar_intencao_corpo(texto)["params"]["direcao"] == direcao


@pytest.mark.parametrize("texto", [
    "não ande para frente", "talvez ande para trás", "você consegue andar?",
    "mova o arquivo para a esquerda", "mover música para playlist", "vire a janela para a direita",
    "a ponte girou os motores", "como eu poderia andar para frente?", "ande por cinco minutos",
    "anda muito estranho", "traduza 'ande para frente'", "ande para frente e apague a pasta",
])
def test_detector_nao_herda_autoridade_ou_alvo_de_mencao(texto):
    assert detectar_intencao_corpo(texto) is None


class _Ponte:
    """Só substitui o transporte físico; mente, autoridade e receipts são reais."""
    def __init__(self, *, ok=True, parada=True):
        self.chamadas = []
        self.ok, self.parada, self.disponivel = ok, parada, True
    def mover_corpo(self, esquerda, direita, duracao):
        self.chamadas.append((esquerda, direita, duracao))
        return {"ok": self.ok, "aplicacao_pwm_confirmada": self.ok,
                "parada_confirmada": self.parada, "evidencia": "mack_pwm_e_sack" if self.ok and self.parada else "",
                "motivo": "motor_confirmado" if self.ok and self.parada else "ack_ausente"}
    def parar_corpo(self):
        self.chamadas.append("STOP")
        return {"ok": self.ok, "parada_confirmada": self.parada, "evidencia": "sack"}
    def diagnostico(self):
        return {"motor": {"disponivel": self.disponivel, "suportado": True}}


def _caminho(*, ponte=None, texto="ande para frente"):
    ponte = ponte or _Ponte()
    estado = criar_estado_compartilhado_runtime()
    corpo = CorpoMotorRuntime(transporte=ponte, estado=estado)
    receipts, falas = [], []
    def registrar(contrato, *_args, **_kwargs):
        receipts.append(contrato)
        novo = registrar_resultado_execucao(dict(estado.mental), contrato, contrato.texto_usuario,
                                            contrato.executou, origem="executor", status=contrato.status)
        estado.substituir("mental", novo)
        return True
    ctx = {"turno_atual": classificar_modalidade_turno(texto), "_corpo_motor_runtime": corpo,
           "_registrar_resultado_execucao": registrar,
           "falar_com_lipsync": lambda *a: falas.append(a), "modo_jogo_ativo": True,
           "_resolver_repeticao_ultima_acao": lambda t: resolver_repeticao_ultima_acao(t, dict(estado.mental), lambda v: v.casefold())}
    return SimpleNamespace(ponte=ponte, estado=estado, corpo=corpo, ctx=ctx, receipts=receipts, falas=falas)


def test_router_publica_receipt_canonicamente_e_contexto_temporario_sem_afirmar_giro():
    caminho = _caminho()
    pedido = detectar_intencao_corpo("ande para frente")
    assert executar_intencao(pedido, "ande para frente", caminho.ctx)
    assert caminho.ponte.chamadas == [(255, 255, 250)]
    tratamento = interpretar_tratamento_operacional(pedido, True)
    assert tratamento.confirmado is True and tratamento.resultado_publicado
    receipt = caminho.receipts[-1]
    assert receipt.contexto["prova_deslocamento"] is False
    assert receipt.contexto["receipt_corpo"]["parada_confirmada"] is True
    assert caminho.estado.mental["corpo_motor"]["autoriza_execucao"] is False
    assert caminho.estado.mental["corpo_motor"]["prova_rotacao"] is False
    assert len(caminho.falas) == 1
    assert "pulso" in caminho.falas[0][0].casefold()
    assert "andei" not in caminho.falas[0][0].casefold()
    assert "permitir_foco" not in receipt.params, "o corpo não posiciona janelas"


def test_pedido_composto_autoriza_somente_segmento_corporal_vigente():
    texto = "ande para frente e abre a calculadora"
    caminho = _caminho(texto=texto)
    assert caminho.ctx["turno_atual"]["autoriza_execucao"] is True
    pedido = detectar_intencao_corpo("ande para frente")
    assert executar_intencao(pedido, texto, caminho.ctx)
    assert caminho.ponte.chamadas == [(255, 255, 250)]
    texto_negado = "não ande para frente e abre a calculadora"
    caminho.ctx["turno_atual"] = classificar_modalidade_turno(texto_negado)
    assert not executar_intencao(pedido, texto_negado, caminho.ctx)
    assert len(caminho.ponte.chamadas) == 1


@pytest.mark.parametrize("parada", [False, True])
def test_sem_mack_ou_sack_nao_ha_sucesso_emprestado_da_animacao(parada):
    caminho = _caminho(ponte=_Ponte(ok=parada, parada=False))
    pedido = detectar_intencao_corpo("ande para frente")
    assert not executar_intencao(pedido, "ande para frente", caminho.ctx)
    assert caminho.receipts[-1].confirmado is False
    assert caminho.receipts[-1].status == "falha_execucao"
    assert "pulso para" not in caminho.falas[-1][0]


@pytest.mark.parametrize("texto", [
    "não ande para frente", "você pode andar?", "talvez ande para frente", "eu vou andar para frente",
])
def test_proposta_corporal_nao_substitui_fala_ou_modalidade(texto):
    caminho = _caminho(texto=texto)
    assert not executar_intencao({"intent": "CORPO_MOVER", "params": {"direcao": "frente"}}, texto, caminho.ctx)
    assert not caminho.ponte.chamadas
    assert caminho.receipts[-1].status == "bloqueado_sem_autorizacao"


def test_direcao_e_parametros_da_proposta_precisam_corresponder_ao_pedido_atual():
    caminho = _caminho()
    for params in ({"direcao": "tras"}, {"direcao": "frente", "duracao_ms": 500},
                   {"direcao": "frente", "pwm": 120}):
        assert not executar_intencao({"intent": "CORPO_MOVER", "params": params}, "ande para frente", caminho.ctx)
    assert not caminho.ponte.chamadas


@pytest.mark.parametrize("params", [
    {"direcao": "frente", "pwm": True}, {"direcao": "frente", "duracao_ms": True},
    {"direcao": "frente", "duracao_ms": 501}, {"direcao": "frente", "pwm": 256},
    {"direcao": "frente", "duracao_ms": "250"}, {"direcao": "inventada"},
])
def test_porta_tipadas_rejeita_parametros_sem_acionar_transporte(params):
    ponte = _Ponte()
    assert CorpoMotorRuntime(transporte=ponte).executar("CORPO_MOVER", params)["ok"] is False
    assert not ponte.chamadas


def test_repeticao_usa_receipt_e_nova_fala_autorizadora_do_owner_compartilhado():
    caminho = _caminho()
    primeiro = detectar_intencao_corpo("ande para frente")
    assert executar_intencao(primeiro, "ande para frente", caminho.ctx)
    repeticao = caminho.ctx["_resolver_repeticao_ultima_acao"]("de novo")
    assert repeticao and repeticao["intent"] == "CORPO_MOVER"
    from mente_laylay.cognicao.orquestrador_turno_runtime import aplicar_repeticao_operacional_ao_turno
    caminho.ctx["turno_atual"] = aplicar_repeticao_operacional_ao_turno(classificar_modalidade_turno("de novo"), repeticao)
    assert executar_intencao(repeticao, "de novo", caminho.ctx)
    assert len(caminho.ponte.chamadas) == 2
    assert caminho.receipts[0].id_solicitacao != caminho.receipts[1].id_solicitacao


def test_catalogo_vivo_sem_negociacao_motor_nao_afirma_controle_mesmo_com_rosto_confirmado():
    ponte = _Ponte()
    corpo = CorpoMotorRuntime(transporte=ponte)
    disponibilidade = DisponibilidadeOperacionalRuntime(
        rosto_oled_getter=lambda: {"aplicacao_confirmada": True}, corpo_motor_getter=corpo.diagnostico)
    mapa = MapaHabilidadesRuntime(operacional_getter=disponibilidade.snapshot)
    pergunta = "você consegue andar e controlar os motores?"
    turno = classificar_modalidade_turno(pergunta)
    assert mapa.consultar("CORPO_MOVER")["disponivel"]
    assert "pulso" in mapa.responder_pergunta_capacidade(pergunta, turno=turno)
    assert not ponte.chamadas
    ponte.disponivel = False
    assert not mapa.consultar("CORPO_MOVER")["disponivel"]
    assert "indisponível" in mapa.responder_pergunta_capacidade(pergunta, turno=turno)
    assert mapa.snapshot()["dominios"]["rosto_oled"]["estado"] == "disponivel"


def test_acao_autonoma_sem_contrato_corporal_nao_herda_permissao_de_iot():
    from mente_laylay.autonomia.executor_acoes_autonomas import ExecutorAcoesAutonomasRuntime
    efeitos = []
    executor = ExecutorAcoesAutonomasRuntime(executar_iot=lambda *a: efeitos.append(a),
        estado_mental_getter=lambda: {}, obter_volume=lambda: 10, ajustar_volume=lambda _: True,
        falar=lambda *a: efeitos.append(a))
    assert executor.executar({"intent": "CORPO_MOVER", "params": {"direcao": "frente"}})["status"] == "intent_nao_elegivel"
    assert not efeitos


def test_cancelamento_preserva_acionamento_parcial_sem_virar_falha_visual():
    from mente_laylay.memoria_mental.atividade_operacional_runtime import criar_atividade_operacional_runtime
    caminho = _caminho()
    owner = criar_atividade_operacional_runtime(estado=caminho.estado)
    def interrompido(*_args):
        return {"ok": False, "cancelado": True, "status": "cancelado", "motivo": "movimento_cancelado",
                "aplicacao_pwm_confirmada": True, "parada_confirmada": True, "evidencia": "mack_pwm_e_sack"}
    caminho.ponte.mover_corpo = interrompido
    assert not executar_intencao(detectar_intencao_corpo("ande para frente"), "ande para frente", caminho.ctx)
    receipt = caminho.receipts[-1]
    assert receipt.status == "cancelado"
    assert receipt.executou is True and receipt.confirmado is False
    assert owner.observar_resultado(receipt) is False


def _root_instalado(monkeypatch, tmp_path):
    from memoria_sqlite import MemoriaSQLite
    from mente_laylay.integracao import instancia_unica
    from mente_laylay.integracao.configuracao_aplicacao import ConfiguracaoAplicacaoRuntime
    adquirir = instancia_unica.adquirir_instancia_unica
    # A primeira importação fica em cache; não deixe o pareamento pessoal
    # definir a composição USB compartilhada pelos testes seguintes.
    monkeypatch.setenv("LAYLAY_CORPO_WIFI_CONFIG", str(tmp_path / "sem_pareamento_wifi.json"))
    # O dispositivo de controle desta fixture só implementa o perfil curto.
    # A preferência física do usuário não pode escolher o perfil do ensaio.
    monkeypatch.setattr(ConfiguracaoAplicacaoRuntime, "perfil_corporal", lambda self: "bancada")
    monkeypatch.setattr(instancia_unica, "adquirir_instancia_unica",
                        lambda _: adquirir(tmp_path / "composicao_corpo"))
    root = importlib.import_module("laylay")
    # Outro teste pode já ter composto a raiz em cache antes desta fixture.
    monkeypatch.setattr(root._corpo_motor_runtime.companhia, "perfil_corporal", "bancada")
    # Mantém o owner e o mecanismo SQLite reais, mas isola a persistência do
    # aprendizado para o teste não alterar hipóteses do usuário.
    memoria = MemoriaSQLite(str(tmp_path / "aprendizado_corpo.sqlite"))
    monkeypatch.setattr(root._motor_aprendizado_runtime, "memoria", memoria)
    monkeypatch.setattr(root._motor_aprendizado_runtime.maturidade, "memoria", memoria)
    monkeypatch.setattr(root._motor_aprendizado_runtime, "_resultados_recentes", [])
    monkeypatch.setattr(root._motor_aprendizado_runtime, "_acoes_recentes", [])
    contexto = root._composicao_ciclo_comandos_runtime.contexto
    falas = []
    # Substitui apenas o dispositivo, modelo externo e entrega de som. Os
    # owners de língua, porteiro, ciclo, estado, receipt e autoria são reais.
    ponte = _Ponte()
    monkeypatch.setattr(root._corpo_motor_runtime, "transporte", ponte)
    monkeypatch.setitem(contexto._servicos_estaticos, "enviar_mensagem", None)
    monkeypatch.setitem(contexto._servicos_estaticos, "falar_com_lipsync", lambda *a: falas.append(a))
    monkeypatch.setattr(root._orquestrador_fala_runtime, "falar", lambda *a, **_k: falas.append(a) or True)
    return root, ponte, falas


def test_composicao_instalada_resolve_executa_publica_e_conhece_corpo(monkeypatch, tmp_path):
    root, ponte, falas = _root_instalado(monkeypatch, tmp_path)
    ciclo = root._composicao_ciclo_comandos_runtime.ciclo
    assert root._composicao_ciclo_comandos_runtime.contexto.montar()["_corpo_motor_runtime"] is root._corpo_motor_runtime
    texto = "pode andar um pouquinho?"
    # A publicação vinculada exige o mesmo frame que a entrada real instala:
    # classificação isolada não cria identidade de turno/plano/retrato.
    root._iniciar_planejamento_turno(texto, origem="teste_corpo")
    pedido, rota = ciclo.resolver_comando_natural(texto, "teste_corpo")
    assert pedido and pedido["intent"] == "CORPO_MOVER", rota
    assert not ponte.chamadas, "resolver não executa"
    assert ciclo.executar_intencao(pedido, texto)
    assert ponte.chamadas == [(255, 255, 250)]
    retrato = root._estado_compartilhado_runtime.obter_copia("mental", "ultima_acao_contrato", {})
    assert retrato["intent"] == "CORPO_MOVER" and retrato["confirmado"] is True
    assert "pulso" in falas[-1][0].casefold()
    pergunta = "você consegue andar?"
    root._iniciar_planejamento_turno(pergunta, origem="teste_capacidade_corpo")
    turno = root._estado_compartilhado_runtime.obter_copia("mental", "turno_atual", {})
    assert "pulso" in root._mapa_habilidades_runtime.responder_pergunta_capacidade(pergunta, turno=turno)
    proposta, _ = ciclo.resolver_comando_natural(pergunta, "teste_corpo")
    assert proposta is None
    assert len(ponte.chamadas) == 1


def test_receipt_instalado_alimenta_aprendizado_compartilhado_sem_criar_permissao_duravel(monkeypatch, tmp_path):
    root, ponte, _falas = _root_instalado(monkeypatch, tmp_path)
    texto = "ande para frente"
    ciclo = root._composicao_ciclo_comandos_runtime.ciclo
    root._iniciar_planejamento_turno(texto, origem="teste_aprendizado_corpo")
    pedido, _rota = ciclo.resolver_comando_natural(texto, "teste_aprendizado_corpo")
    assert pedido and pedido["intent"] == "CORPO_MOVER"
    assert ciclo.executar_intencao(pedido, texto)
    assert ponte.chamadas == [(255, 255, 250)]
    memoria = root._motor_aprendizado_runtime.memoria
    chave = "confiabilidade:CORPO_MOVER::corpo"
    hipotese = memoria.obter_hipotese_aprendizado(chave)
    assert hipotese and hipotese["tipo"] == "resultado_habilidade"
    assert hipotese["evidencias_positivas"] == 1 and hipotese["status"] == "candidata"
    eventos = memoria.listar_eventos_aprendizado(chave)
    assert len(eventos) == 1 and eventos[0]["origem"] == "executor_confirmado"
    assert "autoriza_execucao" not in hipotese["valor"]
    # Uma hipótese de confiabilidade não concede uma nova ação nem torna
    # uma pergunta sobre movimento em autorização.
    pergunta = "você consegue andar?"
    root._iniciar_planejamento_turno(pergunta, origem="teste_pergunta_sem_autorizacao")
    proposta, _rota = ciclo.resolver_comando_natural(pergunta, "teste_aprendizado_corpo")
    assert proposta is None and len(ponte.chamadas) == 1


@pytest.mark.parametrize("disponivel", [False, True])
def test_documentacao_corporal_chega_ao_prompt_instalado_com_disponibilidade_real(monkeypatch, tmp_path, disponivel):
    import json
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
    from mente_laylay.cognicao.plano_turno import planejar_turno
    root, ponte, _falas = _root_instalado(monkeypatch, tmp_path)
    ponte.disponivel = disponivel
    texto = "como eu poderia andar?"
    turno = {**classificar_modalidade_turno(texto), "id": 9181}
    plano = planejar_turno(texto, turno=turno, mente={})
    plano["evidencia_capacidades"] = root._mapa_habilidades_runtime.evidencia_conversacional(texto, turno=turno)
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={})
    assert turno["autoriza_execucao"] is False
    documento = json.loads(contrato["documentacao_capacidades"])
    corpo = next(item for item in documento if item["dominio"] == "corpo_motor")
    assert corpo["estado"] == ("disponivel" if disponivel else "indisponivel")
    assert bool(corpo["exemplos"]) is disponivel
    root._estado_compartilhado_runtime.atualizar_campos("mental", turno_atual=turno, contrato_fala_atual=contrato)
    mensagens = [{"role": "system", "content": "PERSONALIDADE"}, {"role": "user", "content": texto}]
    pacote = root._contexto_prompt_runtime.preparar_envio_modelo(mensagens, turno_id=9181)
    assert pacote.contexto_fechado
    assert contrato["documentacao_capacidades"] in pacote.mensagens[0]["content"]
    assert not ponte.chamadas


def test_cadeia_instalada_preserva_receipts_independentes_e_publica_falha_parcial(monkeypatch, tmp_path):
    root, ponte, falas = _root_instalado(monkeypatch, tmp_path)
    texto = "ande para frente e pare os motores"
    root._iniciar_planejamento_turno(texto, origem="teste_corpo_composto")
    # O segundo efeito falha; não pode emprestar o MACK/SACK do primeiro.
    def parada_sem_receipt():
        ponte.chamadas.append("STOP")
        return {"ok": False, "parada_confirmada": False, "motivo": "sack_ausente"}
    monkeypatch.setattr(ponte, "parar_corpo", parada_sem_receipt)
    assert root._composicao_ciclo_comandos_runtime.processar_cadeia(texto, "teste_corpo_composto")
    assert ponte.chamadas == [(255, 255, 250), "STOP"]
    assert len(falas) == 1, "a cadeia deve publicar uma resposta autoral"
    assert "pulso" in falas[0][0].casefold()
    receipt_final = root._estado_compartilhado_runtime.obter_copia("mental", "ultima_acao_contrato", {})
    assert receipt_final["intent"] == "CORPO_PARAR"
    assert receipt_final["status"] == "falha_execucao" and receipt_final["confirmado"] is False
    # O owner autoral já possui variantes locais legítimas de falha. O
    # contrato é ausência de sucesso do STOP e uma fala parcial, não três
    # frases exatas sorteadas pelo fallback.
    assert any(s in falas[0][0].casefold() for s in (
        "não consegui", "falh", "não respondeu", "não confirmou", "não colaborou",
    )), falas
