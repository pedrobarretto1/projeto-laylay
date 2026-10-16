"""Expressão sonora reutiliza estado causal, receipts e sessão do corpo."""
from copy import deepcopy
import pytest
from scripts.tests.test_rosto_oled import EspSerial, Relogio, estado_emocional
from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime, projetar_rosto


class EspSom(EspSerial):
    def __init__(self, som=True, ack_som=True, envio=False):
        super().__init__()
        self.som, self.ack_som = som, ack_som
        self.envio = envio

    def write(self, dados):
        partes = dados.decode().split()
        if partes[0] == "SENCAPS":
            self.enviados.append(dados.decode().strip())
            self.rx.extend((f"SENCAPS 1 {partes[2]} ENVIO1" if self.envio else "ERROR 1 PACOTE_INVALIDO").encode() + b"\n")
            return len(dados)
        if partes[0] == "SCAPS":
            self.enviados.append(dados.decode().strip())
            self.rx.extend((f"SCAPS 1 {partes[2]} SOM1" if self.som else "ERROR 1 PACOTE_INVALIDO").encode() + b"\n")
            return len(dados)
        if partes[0] == "SOUND":
            self.enviados.append(dados.decode().strip())
            if self.ack_som:
                self.rx.extend(("SOUNDACK " + " ".join(partes[1:]) + "\n").encode())
            return len(dados)
        return super().write(dados)


def criar(esp=None):
    esp = esp or EspSom()
    relogio = Relogio()
    estado = {"conversa": {}, "atividade": {}}
    runtime = RostoOledRuntime(estado_getter=lambda: estado["conversa"],
        atividade_getter=lambda: estado["atividade"], porta="TESTE",
        abrir_serial=lambda _: esp, monotonic=relogio)
    return runtime, esp, relogio, estado


def sons(esp):
    return [x for x in esp.enviados if x.startswith("SOUND ")]


def test_rosto_somente_olhos_nao_transmite_fala_nem_altera_estado():
    estado = estado_emocional("envergonhada")
    estado["is_speaking"] = True
    antes = deepcopy(estado)
    assert projetar_rosto(estado) == (6, 2, 0)
    assert estado == antes


def test_acordar_uma_vez_e_ausencia_de_som_em_cada_amostra():
    runtime, esp, _, _ = criar()
    assert runtime.sincronizar()
    assert len(sons(esp)) == 1 and sons(esp)[0].endswith(" 0")
    assert runtime.sincronizar()
    assert len(sons(esp)) == 1
    assert runtime.diagnostico()["som"]["solicitacao_confirmada"]
    assert runtime.diagnostico()["som"]["prova_auditiva"] is False


def test_sucesso_falha_e_emocao_recentemente_observados_sem_replay():
    runtime, esp, relogio, estado = criar()
    assert runtime.sincronizar()
    relogio.agora += 2.1
    estado["atividade"] = {"origem": "atividade_operacional_observada",
        "sucesso_id": 1, "sucesso_monotonic": relogio.agora}
    assert runtime.sincronizar()
    assert sons(esp)[-1].endswith(" 1")
    relogio.agora += 2.1
    estado["atividade"] = {"origem": "atividade_operacional_observada",
        "falha_id": 1, "falha_monotonic": relogio.agora}
    assert runtime.sincronizar()
    assert sons(esp)[-1].endswith(" 2")
    relogio.agora += 2.1
    estado["conversa"] = estado_emocional("envergonhada")
    assert runtime.sincronizar()
    assert sons(esp)[-1].endswith(" 6")
    quantidade = len(sons(esp))
    assert runtime.sincronizar()
    assert len(sons(esp)) == quantidade


@pytest.mark.parametrize("falhou", [False, True], ids=["sucesso", "falha"])
def test_resultado_durante_intervalo_sonoro_aguarda_sem_ser_consumido(falhou):
    from mente_laylay.integracao.composicao_rosto_oled import criar_composicao_rosto_oled_runtime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
    from mente_laylay.memoria_mental.atividade_operacional_runtime import criar_atividade_operacional_runtime
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    from types import SimpleNamespace
    mente, esp, clock = criar_estado_compartilhado_runtime(), EspSom(), Relogio()
    owner = criar_atividade_operacional_runtime(estado=mente, monotonic=clock)
    rosto = criar_composicao_rosto_oled_runtime(estado=mente,
        observabilidade=SimpleNamespace(relatar_falha=lambda *a, **k: None),
        porta="TESTE", abrir_serial=lambda _: esp, monotonic=clock)
    assert rosto.sincronizar()
    clock.agora += .3
    owner.observar_resultado(ResultadoAcao(intent="VOLUME", status="falha_execucao" if falhou else "volume_ajustado",
        origem="executor", executou=not falhou, confirmado=not falhou, ok=not falhou, id_solicitacao="acao-atual"))
    nome, codigo = ("falha", 2) if falhou else ("sucesso", 1)
    assert owner.retrato()[nome+"_id"] == 1, "primeira fronteira: receipt chegou ao owner compartilhado"
    assert rosto.sincronizar()
    assert len(sons(esp)) == 1
    assert rosto._eventos_som_consumidos[nome] == 0, "intervalo não deve consumir um resultado ainda não enviado"
    clock.agora += 1.8
    assert rosto.sincronizar()
    assert len(sons(esp)) == 2 and sons(esp)[-1].endswith(f" {codigo}")
    assert rosto.sincronizar() and len(sons(esp)) == 2


def test_sucesso_toca_sem_depender_de_gesto_quando_corpo_esta_atento_ao_pc():
    from scripts.tests.test_presenca_corporal_v2 import EspPresenca
    from mente_laylay.integracao.composicao_rosto_oled import criar_composicao_rosto_oled_runtime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
    from mente_laylay.memoria_mental.atividade_operacional_runtime import criar_atividade_operacional_runtime
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    from types import SimpleNamespace
    mente, esp, clock = criar_estado_compartilhado_runtime(), EspPresenca(), Relogio()
    owner = criar_atividade_operacional_runtime(estado=mente, monotonic=clock)
    rosto = criar_composicao_rosto_oled_runtime(estado=mente,
        observabilidade=SimpleNamespace(relatar_falha=lambda *a, **k: None),
        companhia_getter=lambda: {"ativa": True, "perfil_corporal": "rodas_suspensas"},
        interacao_getter=lambda: True, porta="TESTE", abrir_serial=lambda _: esp, monotonic=clock)
    assert rosto.sincronizar() and rosto.diagnostico()["expressao"]["suportado"]
    clock.agora += 2.1
    owner.observar_resultado(ResultadoAcao(intent="VOLUME", status="volume_ajustado", origem="executor",
        executou=True, confirmado=True, ok=True, id_solicitacao="volume-sem-gesto"))
    assert owner.retrato()["sucesso_id"] == 1
    assert rosto.sincronizar()
    assert sons(esp)[-1].endswith(" 1"), "som operacional independe da oportunidade para mover motores"
    assert not any(p.startswith(("MOTOR ", "MOTOR2 ")) for p in esp.enviados)
    assert rosto.expressar_gesto(1, 1, 0, 1000, tocar_som=True)["ok"]
    assert len(sons(esp)) == 2, "a coreografia não repete o resultado já sinalizado"


@pytest.mark.parametrize("interrupcao", ["expiracao", "reconexao", "origem_nao_certificada"])
def test_resultado_pendente_expira_ou_e_descartado_sem_replay(interrupcao):
    rosto, esp, clock, estado = criar()
    assert rosto.sincronizar()
    estado["atividade"] = {"origem": "atividade_operacional_observada", "falha_id": 1, "falha_monotonic": clock.agora}
    assert rosto.sincronizar()
    assert rosto.diagnostico()["som"]["resultados_pendentes"] == ["falha"]
    if interrupcao == "expiracao":
        clock.agora += 3
    elif interrupcao == "reconexao":
        rosto._fechar()
    else:
        estado["atividade"]["origem"] = "plano"
    assert rosto.sincronizar()
    assert len(sons(esp)) == 1
    assert not rosto.diagnostico()["som"]["resultados_pendentes"]
    assert rosto._eventos_som_consumidos["falha"] == 1


def test_resultado_adiado_e_tentado_uma_vez_mesmo_sem_ack():
    rosto, esp, clock, estado = criar(EspSom(ack_som=False))
    assert rosto.sincronizar()
    estado["atividade"] = {"origem": "atividade_operacional_observada", "falha_id": 1, "falha_monotonic": clock.agora}
    assert rosto.sincronizar()
    clock.agora += 1.8
    assert rosto.sincronizar()
    assert len(sons(esp)) == 2 and sons(esp)[-1].endswith(" 2")
    assert not rosto.diagnostico()["som"]["solicitacao_confirmada"]
    assert rosto.sincronizar() and len(sons(esp)) == 2


def test_estado_nao_certificado_nao_comemora_e_falha_sonora_nao_quebra_rosto():
    runtime, esp, relogio, estado = criar(EspSom(ack_som=False))
    assert runtime.sincronizar()
    assert runtime.diagnostico()["aplicacao_confirmada"]
    assert not runtime.diagnostico()["som"]["solicitacao_confirmada"]
    relogio.agora += 2.1
    estado["atividade"] = {"sucesso_id": 99, "sucesso_monotonic": relogio.agora, "origem": "plano"}
    estado["conversa"] = {"current_emotion": "brava", "is_speaking": True}
    assert runtime.sincronizar()
    assert len(sons(esp)) == 1


def test_firmware_antigo_sem_som_mantem_olhos():
    runtime, esp, _, _ = criar(EspSom(som=False))
    assert runtime.sincronizar()
    assert not sons(esp) and not runtime.diagnostico()["som"]["suportado"]


def test_ack_perdido_nao_repete_evento_e_intervalo_descarta_excesso():
    runtime, esp, relogio, estado = criar(EspSom(ack_som=False))
    assert runtime.sincronizar()
    relogio.agora += 2.1
    estado["atividade"] = {"origem": "atividade_operacional_observada",
        "sucesso_id": 1, "sucesso_monotonic": relogio.agora}
    assert runtime.sincronizar()
    quantidade = len(sons(esp))
    assert runtime.sincronizar() and len(sons(esp)) == quantidade
    estado["conversa"] = estado_emocional("brava")
    assert runtime.sincronizar() and len(sons(esp)) == quantidade
    relogio.agora += 2.1
    assert runtime.sincronizar() and len(sons(esp)) == quantidade


def test_reconexao_nao_reexecuta_acordar_nem_receipt_antigo():
    runtime, esp, relogio, estado = criar()
    assert runtime.sincronizar()
    estado["atividade"] = {"origem": "atividade_operacional_observada",
        "sucesso_id": 1, "sucesso_monotonic": relogio.agora - 20}
    relogio.agora += 4
    assert runtime.sincronizar()
    assert len(sons(esp)) == 1


def test_composicao_reusa_owner_e_lote_parcial_nao_toca_sucesso():
    from mente_laylay.integracao.composicao_rosto_oled import criar_composicao_rosto_oled_runtime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
    from mente_laylay.memoria_mental.atividade_operacional_runtime import criar_atividade_operacional_runtime
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    from types import SimpleNamespace
    mente, esp, clock = criar_estado_compartilhado_runtime(), EspSom(), Relogio()
    owner = criar_atividade_operacional_runtime(estado=mente, monotonic=clock)
    runtime = criar_composicao_rosto_oled_runtime(estado=mente,
        observabilidade=SimpleNamespace(relatar_falha=lambda *a, **k: None),
        porta="TESTE", abrir_serial=lambda _: esp, monotonic=clock)
    assert runtime.sincronizar()
    clock.agora += 2.1
    with owner.escopo():
        owner.observar_resultado(ResultadoAcao(intent="VOLUME", status="volume_ajustado", origem="executor",
            executou=True, confirmado=True, ok=True, id_solicitacao="volume-a"))
        owner.observar_resultado(ResultadoAcao(intent="IOT", status="falha_execucao", origem="executor",
            executou=False, confirmado=False, ok=False, id_solicitacao="luz-b"))
    assert not owner.retrato()["sucesso_id"]
    assert runtime.sincronizar()
    assert sons(esp)[-1].endswith(" 2")
    assert not any(x.endswith(" 1") for x in sons(esp))
    assert not any(x.startswith("MOTOR ") for x in esp.enviados)
    assert mente.obter_copia("mental", "rosto_oled", {})["som"]["suportado"]


def test_catalogo_bip_informa_suporte_vivo_e_olhos_sem_boca():
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    for suportado in (False, True):
        runtime, _, _, _ = criar(EspSom(som=suportado))
        assert runtime.sincronizar()
        disponibilidade = DisponibilidadeOperacionalRuntime(rosto_oled_getter=runtime.diagnostico)
        mapa = MapaHabilidadesRuntime()
        mapa.conectar_disponibilidade_operacional(disponibilidade.snapshot)
        resposta = mapa.responder_pergunta_capacidade("Você consegue emitir bips no ESP32?")
        assert resposta and "sem boca" in resposta
        assert ("oferece SOM1" in resposta) is suportado


def test_raiz_real_instala_os_mesmos_getters_sem_dono_de_som_paralelo(monkeypatch, tmp_path):
    import importlib
    from mente_laylay.integracao import instancia_unica
    adquirir = instancia_unica.adquirir_instancia_unica
    monkeypatch.setattr(instancia_unica, "adquirir_instancia_unica", lambda _: adquirir(tmp_path / "som-root"))
    root = importlib.import_module("laylay")
    retrato = root._estado_compartilhado_runtime.obter_copia("mental", "atividade_operacional", {})
    assert root._rosto_oled_runtime.atividade_getter() == retrato
    assert projetar_rosto(root._rosto_oled_runtime.estado_getter())[2] == 0


def test_executor_instalado_publica_falha_para_o_mesmo_rosto_sonoro(monkeypatch, tmp_path):
    # Owners reais, persistência de aprendizado isolada em SQLite temporário.
    from scripts.tests.test_corpo_motor import _root_instalado
    root, _, _ = _root_instalado(monkeypatch, tmp_path)
    esp, rosto = EspSom(), root._rosto_oled_runtime
    anteriores = {d: deepcopy(root._estado_compartilhado_runtime.retrato_dominio(d))
                  for d in ("mental", "conversacional")}
    rosto.encerrar()
    monkeypatch.setattr(rosto, "porta", "TESTE")
    monkeypatch.setattr(rosto, "_config_wifi_path", None)
    monkeypatch.setattr(rosto, "abrir_serial", lambda _: esp)
    monkeypatch.setattr(rosto, "_acordar_som_pendente", True)
    monkeypatch.setattr(rosto, "_eventos_som_consumidos", {"sucesso": 0, "falha": 0})
    assert rosto.sincronizar()
    monkeypatch.setattr(rosto, "_ultimo_envio_som", float("-inf"))
    monkeypatch.setitem(root._contexto_intencao_runtime._servicos_estaticos, "ajustar_volume_sistema", lambda _: False)
    monkeypatch.setitem(root._contexto_intencao_runtime._servicos_estaticos, "obter_volume_sistema", lambda: None)
    pedido = {"intent": "VOLUME", "params": {"nivel_volume": 42, "_execucao_silenciosa": True}}
    try:
        assert root.executar_intencao(pedido, "deixe o volume em 42 por cento") is True
        assert pedido["_laylay_tratamento_operacional"]["confirmado"] is False
        assert rosto.sincronizar()
        assert sons(esp)[-1].endswith(" 2")
    finally:
        rosto.encerrar()
        for dominio, retrato in anteriores.items():
            root._estado_compartilhado_runtime.substituir(dominio, retrato)


@pytest.mark.parametrize("texto", ["despausa a musica", "retoma a música", "pausa a musica"])
@pytest.mark.parametrize("confirmado", [None, True, False], ids=["envio", "sucesso", "falha"])
def test_receipt_midia_instalado_distingue_envio_sucesso_e_falha(monkeypatch, tmp_path, texto, confirmado):
    from scripts.tests.test_corpo_motor import _root_instalado
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    root, _, _ = _root_instalado(monkeypatch, tmp_path)
    mente, rosto, owner = root._estado_compartilhado_runtime, root._rosto_oled_runtime, root._atividade_operacional_runtime
    anteriores = {d: deepcopy(mente.retrato_dominio(d)) for d in ("mental", "conversacional")}
    esp = EspSom(envio=True)
    rosto.encerrar()
    monkeypatch.setattr(rosto, "porta", "TESTE")
    monkeypatch.setattr(rosto, "_config_wifi_path", None)
    monkeypatch.setattr(rosto, "abrir_serial", lambda _: esp)
    monkeypatch.setattr(rosto, "_acordar_som_pendente", True)
    monkeypatch.setattr(rosto, "_eventos_som_consumidos", {nome: owner.retrato()[nome+"_id"] for nome in ("envio", "sucesso", "falha")})
    servicos = root._composicao_ciclo_comandos_runtime.contexto._servicos_estaticos
    chamadas = []
    monkeypatch.setattr(root._registro_navegador_leitura_runtime.servico, "aba_ativa", lambda **kwargs: {"url": "https://youtube.com/watch?v=abcdefghijk", "tabId": 123})
    def controlar(cmd, **kwargs):
        chamadas.append(cmd)
        return {"ok": confirmado is not False, "confirmado": confirmado, "status": "observado"}
    monkeypatch.setattr(root._registro_navegador_operacoes_runtime.servico, "controlar_youtube_detalhado", controlar)
    monkeypatch.setitem(servicos, "_executar_controle_midia_nativo", lambda cmd: chamadas.append(cmd) or True)
    if confirmado is None:
        monkeypatch.setattr(root._registro_navegador_leitura_runtime.servico, "aba_ativa", lambda **kwargs: {})
    try:
        assert rosto.sincronizar()
        antes = owner.retrato()
        mente.atualizar_campos("mental", turno_atual=classificar_modalidade_turno(texto))
        ciclo = root._composicao_ciclo_comandos_runtime.ciclo
        pedido, rota = ciclo.resolver_comando_natural(texto, "teste_som_midia")
        assert pedido and pedido["intent"] == "MEDIA_CONTROL", rota
        if confirmado is not None:
            pedido["params"]["platform"] = "music"
        ciclo.executar_intencao(pedido, texto)
        receipt = mente.obter_copia("mental", "ultima_acao_contrato", {})
        assert chamadas and receipt["intent"] == "MEDIA_CONTROL"
        assert receipt["confirmado"] is confirmado, "executor preserva o nível de evidência"
        nome, codigo = ("envio", 8) if confirmado is None else ("sucesso", 1) if confirmado else ("falha", 2)
        assert owner.retrato().get(nome+"_id", 0) == antes.get(nome+"_id", 0) + 1
        if confirmado is None:
            assert owner.retrato()["sucesso_id"] == antes["sucesso_id"]
        monkeypatch.setattr(rosto, "_ultimo_envio_som", float("-inf"))
        assert rosto.sincronizar()
        assert sons(esp)[-1].endswith(f" {codigo}")
        quantidade = len(sons(esp))
        assert rosto.sincronizar() and len(sons(esp)) == quantidade
        assert not any(x.startswith(("MOTOR ", "MOTOR2 ")) for x in esp.enviados)
    finally:
        rosto.encerrar()
        for dominio, retrato in anteriores.items():
            mente.substituir(dominio, retrato)


@pytest.mark.parametrize("suporte", [True, False])
def test_envio_aguarda_intervalo_e_exige_capacidade_negociada(suporte):
    runtime, esp, clock, estado = criar(EspSom(envio=suporte))
    assert runtime.sincronizar()
    clock.agora += .3
    estado["atividade"] = {"origem": "atividade_operacional_observada", "envio_id": 1, "envio_monotonic": clock.agora}
    assert runtime.sincronizar() and len(sons(esp)) == 1
    clock.agora += 1.8
    assert runtime.sincronizar()
    assert len(sons(esp)) == (2 if suporte else 1)
    if suporte:
        assert sons(esp)[-1].endswith(" 8")
    assert not any(x.endswith(" 1") for x in sons(esp))


def test_catalogo_explica_envio_sem_promover_a_sucesso():
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    for suportado in (True, False):
        runtime, _, _, _ = criar(EspSom(envio=suportado))
        assert runtime.sincronizar()
        disponibilidade = DisponibilidadeOperacionalRuntime(rosto_oled_getter=runtime.diagnostico)
        mapa = MapaHabilidadesRuntime()
        mapa.conectar_disponibilidade_operacional(disponibilidade.snapshot)
        resposta = mapa.responder_pergunta_capacidade("Você consegue emitir bips no ESP32?")
        assert ("ENVIO1" in resposta) is suportado
        if suportado:
            assert "sem confirmar o efeito" in resposta
