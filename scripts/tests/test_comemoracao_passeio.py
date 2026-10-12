"""Resultado confirmado pode motivar gesto; somente a concessão permite motores."""
import pytest
from copy import deepcopy

from mente_laylay.memoria_mental.atividade_operacional_runtime import criar_atividade_operacional_runtime
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.cognicao.gramatica_corpo import detectar_intencao_corpo
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from scripts.tests.test_companhia_corporal import montar, ativar, motores


@pytest.fixture(autouse=True)
def isolar_pareamento_pessoal(monkeypatch, tmp_path):
    # A raiz importada pela primeira fixture também deve usar a configuração
    # USB de teste, jamais o pareamento Wi-Fi persistido do usuário.
    monkeypatch.setenv("LAYLAY_CORPO_WIFI_CONFIG", str(tmp_path / "sem_pareamento.json"))


@pytest.fixture
def raiz_instalada(monkeypatch, tmp_path):
    from scripts.tests.test_corpo_motor import _root_instalado
    dados = _root_instalado(monkeypatch, tmp_path)
    estado = dados[0]._estado_compartilhado_runtime
    anteriores = {d: deepcopy(estado.retrato_dominio(d)) for d in ("mental", "conversacional")}
    yield dados
    for dominio, retrato in anteriores.items():
        estado.substituir(dominio, retrato)


def sucesso(identidade="acao-a", **campos):
    dados = dict(intent="VOLUME", status="volume_ajustado", origem="executor",
                 executou=True, confirmado=True, ok=True, id_solicitacao=identidade)
    dados.update(campos)
    return ResultadoAcao(**dados)


def owner_corporal():
    estado, esp, rosto, corpo, quadro, agora = montar()
    owner = criar_atividade_operacional_runtime(estado=estado, monotonic=lambda: agora[0])
    return estado, esp, rosto, corpo, quadro, agora, owner


def test_sucesso_certificado_cria_sinal_sem_permissao_e_sem_texto_pessoal():
    estado, esp, _, corpo, _, _, owner = owner_corporal()
    assert owner.observar_resultado(sucesso(detalhe="conteúdo pessoal"))
    sinal = estado.obter_copia("mental", "atividade_operacional", {})
    assert sinal.get("sucesso_id") == 1
    assert sinal["autoriza_execucao"] is False
    assert "pessoal" not in str(sinal)
    assert not corpo.companhia.processar()["ok"] and not motores(esp)


@pytest.mark.parametrize("receipt", [
    True, {"ok": True, "confirmado": True, "executou": True, "status": "feito"},
    sucesso(origem="llm"), sucesso(confirmado=None), sucesso(executou=False),
    sucesso(id_solicitacao=""), sucesso(intent="CORPO_PARAR", status="corpo_parado"),
    sucesso(intent="CORPO_COMPANHIA", status="companhia_ativada"),
    sucesso(status="cancelado"), sucesso(ok=False),
])
def test_bool_plano_sem_confirmacao_parada_e_concessao_nao_geram_comemoracao(receipt):
    *_, owner = owner_corporal()
    owner.observar_resultado(receipt, retorno_executor=True)
    assert owner.retrato().get("sucesso_id", 0) == 0


def test_lote_so_comemora_apos_concluir_e_falha_parcial_descarta_sucesso():
    *_, owner = owner_corporal()
    with owner.escopo():
        assert owner.observar_resultado(sucesso())
        assert owner.retrato().get("sucesso_id", 0) == 0
        with owner.escopo():
            assert owner.observar_resultado(ResultadoAcao(intent="CREATE_FILE", status="falha_execucao",
                origem="executor", executou=False, confirmado=False, id_solicitacao="etapa-b"))
    assert owner.retrato().get("sucesso_id", 0) == 0
    with owner.escopo():
        assert owner.observar_resultado(sucesso("outro-lote"))
        assert owner.retrato().get("sucesso_id", 0) == 0
    assert owner.retrato()["sucesso_id"] == 1


@pytest.mark.parametrize("intent,status", [
    ("APP_OPEN", "app_aberto"), ("CREATE_FILE", "arquivo_criado"),
    ("IOT_CONTROL", "ligado"), ("IOT_LIST", "dispositivos_listados"),
])
def test_observador_compartilhado_serve_dominios_distintos(intent, status):
    *_, owner = owner_corporal()
    assert owner.observar_resultado(sucesso(intent=intent, status=status))
    assert owner.retrato()["sucesso_id"] == 1


def test_escopos_concorrentes_nao_emprestam_falha_nem_comemoracao():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    *_, owner = owner_corporal()
    entrou, liberar = Event(), Event()
    def tarefa():
        with owner.escopo():
            owner.observar_resultado(sucesso())
            entrou.set()
            assert liberar.wait(3)
    with ThreadPoolExecutor(max_workers=1) as pool:
        futuro = pool.submit(tarefa)
        try:
            assert entrou.wait(3)
            with owner.escopo():
                owner.invalidar_sucesso_do_escopo()
            assert owner.retrato()["sucesso_id"] == 0
        finally:
            liberar.set()
        futuro.result(3)
    assert owner.retrato()["sucesso_id"] == 1


def test_receipt_cancelado_nao_comemora_etapa_anterior():
    *_, owner = owner_corporal()
    with owner.escopo():
        owner.observar_resultado(sucesso())
        assert not owner.observar_resultado(sucesso("cancelado", status="cancelado"))
    assert owner.retrato()["sucesso_id"] == 0
    assert owner.retrato()["falha_id"] == 0


def test_sucesso_novo_danca_uma_vez_sem_feedback_dos_proprios_motores():
    _, esp, _, corpo, quadro, _, owner = owner_corporal()
    assert ativar(corpo)["ok"]
    assert owner.observar_resultado(sucesso())
    assert corpo.companhia.processar()["ok"]
    assert len(motores(esp)) == 3
    assert [linha.split()[-3:] for linha in motores(esp)] == [
        ["-100", "100", "240"], ["100", "-100", "480"], ["-100", "100", "240"]]
    assert corpo.companhia.diagnostico()["comemoracoes_emitidas"] == 1
    assert not owner.observar_resultado(sucesso())
    assert not corpo.companhia.processar()["ok"]
    assert len(motores(esp)) == 3


def test_sucesso_anterior_a_concessao_nao_e_reproduzido():
    _, esp, _, corpo, _, _, owner = owner_corporal()
    assert owner.observar_resultado(sucesso())
    assert ativar(corpo)["ok"]
    assert not corpo.companhia.processar()["ok"] and not motores(esp)


@pytest.mark.parametrize("texto", [
    "ative modo passeio na mesa com barreiras", "ative passeio na área delimitada",
    "pode ativar o modo passeio na bancada?",
])
def test_passeio_usa_concessao_canonicamente_autorizada(texto):
    pedido = detectar_intencao_corpo(texto)
    assert pedido and pedido["intent"] == "CORPO_COMPANHIA"
    assert pedido["params"]["passeio"] is True
    assert classificar_modalidade_turno(texto)["autoriza_execucao"] is True


@pytest.mark.parametrize("texto", ["ative passeio na mesa", "não ative passeio na bancada",
    "ela sabe passear sozinha?", "traduza 'ative passeio na bancada'"])
def test_passeio_sem_area_declarada_ou_sem_ordem_nao_arma(texto):
    assert detectar_intencao_corpo(texto) is None


def test_passeio_avanca_sem_fala_e_para_ao_revogar_sem_reconexao_automatica():
    _, esp, _, corpo, _, agora, _ = owner_corporal()
    texto = "ative modo passeio na mesa com barreiras"
    pedido = detectar_intencao_corpo(texto)
    assert pedido, "ausência de concessão de passeio deve ser a primeira fronteira RED"
    assert corpo.executar(pedido["intent"], pedido["params"],
                         autorizacao=classificar_modalidade_turno(texto))["ok"]
    agora[0] += 20
    assert corpo.companhia.processar()["ok"]
    assert motores(esp) and motores(esp)[0].split()[-3:-1] == ["100", "100"]
    assert corpo.executar("CORPO_PARAR", {})["ok"]
    quantidade = len(motores(esp))
    agora[0] += 20
    assert not corpo.companhia.processar()["ok"] and len(motores(esp)) == quantidade


def test_cancelamento_de_lote_descarta_sucesso_sem_publicar_falha():
    from asyncio import CancelledError
    *_, owner = owner_corporal()
    with pytest.raises(CancelledError):
        with owner.escopo():
            owner.observar_resultado(sucesso())
            raise CancelledError()
    assert owner.retrato()["sucesso_id"] == 0
    assert owner.retrato()["falha_id"] == 0
    assert owner.retrato()["ativos"] == 0


@pytest.mark.parametrize("campo,valor", [
    ("origem", "llm"), ("sucesso_id", True), ("sucesso_id", 0),
    ("sucesso_monotonic", True), ("sucesso_monotonic", float("nan")),
    ("sucesso_monotonic", 96), ("sucesso_monotonic", 101),
])
def test_sinal_nao_confiavel_antigo_ou_futuro_nao_dispara(campo, valor):
    from mente_laylay.memoria_mental.atividade_operacional_runtime import projetar_sucesso_operacional
    sinal = {"origem": "atividade_operacional_observada", "sucesso_id": 1, "sucesso_monotonic": 100}
    sinal[campo] = valor
    assert projetar_sucesso_operacional(sinal, agora=100) is None


def test_comemoracoes_variam_e_falha_motor_revoga_sem_replay():
    _, esp, _, corpo, _, agora, owner = owner_corporal()
    assert ativar(corpo)["ok"]
    for indice, quantidade in enumerate((3, 4, 3)):
        inicio = len(motores(esp))
        owner.observar_resultado(sucesso(f"sucesso-{indice}"))
        assert corpo.companhia.processar()["ok"]
        assert len(motores(esp)) - inicio == quantidade
        agora[0] += 4
    assert not corpo.companhia.diagnostico()["giro_360_calibrado"]
    owner.observar_resultado(sucesso("motor-falhara"))
    esp.mack = False
    assert not corpo.companhia.processar()["ok"]
    assert not corpo.companhia.diagnostico()["ativa"]
    esp.mack = True
    total = len(motores(esp))
    agora[0] += 4
    assert not corpo.companhia.processar()["ok"] and len(motores(esp)) == total


@pytest.mark.parametrize("falha_segunda", [False, True])
def test_cadeia_instalada_so_publica_sucesso_depois_do_pedido_inteiro(monkeypatch, raiz_instalada, falha_segunda):
    root, _, _ = raiz_instalada
    owner = root._atividade_operacional_runtime
    antes = owner.retrato()["sucesso_id"]
    chamadas = []
    def ajustar(valor):
        assert owner.retrato()["sucesso_id"] == antes, "não comemorar entre efeitos do mesmo pedido"
        chamadas.append(valor)
        return not (falha_segunda and len(chamadas) == 2)
    servicos = root._composicao_ciclo_comandos_runtime.contexto._servicos_estaticos
    monkeypatch.setitem(servicos, "ajustar_volume_sistema", ajustar)
    monkeypatch.setitem(servicos, "obter_volume_sistema", lambda: chamadas[-1] if chamadas else 0)
    texto = "deixe o volume em 42 por cento e depois deixe o volume em 43 por cento"
    root._estado_compartilhado_runtime.atualizar_campos("mental", turno_atual=classificar_modalidade_turno(texto))
    assert root._composicao_ciclo_comandos_runtime.processar_cadeia(texto, "teste_receipt_composto")
    assert chamadas == [42, 43]
    assert owner.retrato()["sucesso_id"] == antes + (0 if falha_segunda else 1)
    assert owner.retrato()["ativos"] == 0


def test_composicao_instalada_passeio_conhecido_sem_receipt_dar_permissao(monkeypatch, raiz_instalada):
    from scripts.tests.test_companhia_corporal import EspCorpo, RostoOledRuntime
    root, _, falas = raiz_instalada
    estado = root._estado_compartilhado_runtime
    esp = EspCorpo()
    rosto = RostoOledRuntime(estado_getter=lambda: estado.retrato_dominio("conversacional"),
                            porta="TESTE", abrir_serial=lambda _: esp)
    assert rosto.sincronizar()
    corpo, ciclo = root._corpo_motor_runtime, root._composicao_ciclo_comandos_runtime.ciclo
    monkeypatch.setattr(corpo, "transporte", rosto)
    agora = [100.0]
    monkeypatch.setattr(corpo.companhia, "monotonic", lambda: agora[0])
    corpo.companhia.revogar("inicio_teste")
    texto = "ative modo passeio na mesa com barreiras"
    estado.atualizar_campos("mental", turno_atual=classificar_modalidade_turno(texto))
    pedido, _ = ciclo.resolver_comando_natural(texto, "teste_passeio")
    assert pedido and pedido["params"]["passeio"] is True
    assert ciclo.executar_intencao(pedido, texto)
    assert corpo.diagnostico()["companhia"]["passeio_ativado"]
    assert "passeio" in falas[-1][0].casefold()
    pergunta = "você consegue passear sozinha e comemorar?"
    fala = root._mapa_habilidades_runtime.responder_pergunta_capacidade(pergunta,
        turno=classificar_modalidade_turno(pergunta))
    assert "passeio espontâneo está ativo" in fala.casefold()
    assert "360" in fala
    agora[0] += 20
    assert corpo.companhia.processar()["ok"] and len(motores(esp)) == 2
    corpo.companhia.revogar("fim_teste")
    assert not corpo.companhia.processar()["ok"]
    rosto.encerrar()
