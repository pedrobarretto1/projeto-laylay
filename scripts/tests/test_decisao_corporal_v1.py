"""Decisão corporal usa contexto/emoção reais e perfil explícito de bancada."""
import pytest
from scripts.tests.test_rosto_oled import estado_emocional


def test_acao_no_pc_suspende_gesto_corporal_mesmo_com_emocao_nova():
    from scripts.tests.test_companhia_corporal import montar, ativar, emocao, motores
    estado, esp, rosto, corpo, _, _ = montar()
    assert ativar(corpo)["ok"]
    estado.atualizar_campos("mental", atividade_operacional={
        "origem": "atividade_operacional_observada", "ativos": 1})
    emocao(estado, rosto, "brava")
    assert not corpo.companhia.processar()["ok"]
    assert not motores(esp), "tarefa vigente no PC deve suspender movimento espontaneo"


def test_tarefa_no_pc_tem_prioridade_sobre_alegria_e_passeio():
    from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
    d = decidir_intencao_corporal(estado_emocional("alegre"),
        {"origem": "atividade_operacional_observada", "ativos": 1},
        permitir_passeio=True, nova_emocao=True, agora=10)
    assert d.nome == "atenta" and not d.permite_movimento


def test_emocao_causal_muda_intencao_e_emocao_sem_causa_nao_move():
    from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
    d = decidir_intencao_corporal(estado_emocional("envergonhada"), {},
        permitir_passeio=False, nova_emocao=True, agora=10)
    assert d.nome == "expressar" and d.emocao == 6
    d = decidir_intencao_corporal({"current_emotion": "brava"}, {},
        permitir_passeio=False, nova_emocao=True, agora=10)
    assert d.nome == "descansar" and not d.permite_movimento


def test_recusa_de_passeio_nao_vira_exploracao_e_plano_nao_vira_sucesso():
    from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
    d = decidir_intencao_corporal({}, {"origem": "plano", "sucesso_id": 1},
        permitir_passeio=False, novo_sucesso=True, agora=10)
    assert d.nome == "descansar"


def test_contexto_atual_e_sucesso_certificado_formam_decisoes_distintas():
    from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
    d = decidir_intencao_corporal({"audio_playing": True}, {},
        permitir_passeio=True, agora=10)
    assert d.nome == "interagir"
    d = decidir_intencao_corporal({}, {"origem": "atividade_operacional_observada",
        "sucesso_id": 1, "sucesso_monotonic": 10}, permitir_passeio=True,
        novo_sucesso=True, agora=10)
    assert d.nome == "comemorar"


def test_perfil_longo_exige_negociacao_e_nao_pode_vir_de_estado_restaurado():
    from scripts.tests.test_companhia_corporal import montar
    from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
    estado, esp, rosto, _, quadro, _ = montar()
    corpo = CorpoMotorRuntime(transporte=rosto, estado=estado,
        perfil_corporal="rodas_suspensas", companhia_bancada_ao_iniciar=True)
    corpo.companhia.coordenador = object()
    estado.atualizar_campos("mental", intencao_corporal={"perfil": "rodas_suspensas", "ativa": True})
    assert not corpo.companhia.processar()["ok"]
    assert not any(p.startswith("MOTOR ") for p in esp.enviados)


def test_limite_do_firmware_longo_e_contrato_explicito():
    from scripts.tests.test_corpo_transporte_oled import EspCorpo
    from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
    class EspLongo(EspCorpo):
        def write(self, dados):
            p = dados.decode().split()
            if p[0] == "LCAPS":
                self.enviados.append(dados.decode().strip())
                self.rx.extend(f"LCAPS 1 {p[2]} LONGO1\n".encode())
                return len(dados)
            return super().write(dados)
    rosto = RostoOledRuntime(estado_getter=lambda: {}, porta="TESTE", abrir_serial=lambda _: EspLongo())
    assert rosto.sincronizar()
    assert rosto.diagnostico()["motor"]["duracao_maxima_ms"] == 5000


def test_cauda_do_overlay_nao_e_execucao_no_pc():
    from mente_laylay.memoria_mental.atividade_operacional_runtime import projetar_execucao_operacional, projetar_atividade_operacional
    estado = {"origem": "atividade_operacional_observada", "ativos": 0, "ultimo_inicio_monotonic": 10}
    assert projetar_atividade_operacional(estado, agora=10.2)
    assert not projetar_execucao_operacional(estado)


def test_perfil_e_preferencia_explicita_preserva_configuracao(tmp_path,monkeypatch):
    from mente_laylay.integracao.configuracao_aplicacao import ConfiguracaoAplicacaoRuntime, ErroConfiguracaoAplicacao
    arquivo = tmp_path / "configuracao.env"
    monkeypatch.delenv('LAYLAY_CORPO_PERFIL', raising=False)
    arquivo.write_text("OUTRA_CONFIG=valor\n", encoding="utf-8")
    c = ConfiguracaoAplicacaoRuntime(raiz=tmp_path)
    assert c.perfil_corporal() == "bancada"
    assert c.definir_perfil_corporal("rodas_suspensas")["saved"]
    assert c.perfil_corporal() == "rodas_suspensas"
    assert "OUTRA_CONFIG=valor" in arquivo.read_text(encoding="utf-8")
    with pytest.raises(ErroConfiguracaoAplicacao): c.definir_perfil_corporal("mesa_livre")


def test_longos_continuos_revalidam_causa_e_parametros_sem_replay():
    import threading, time
    from scripts.tests.test_corpo_transporte_oled import EspCorpo
    from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
    class EspLongo(EspCorpo):
        def write(self, dados):
            p = dados.decode().split()
            if p[0] == "LCAPS":
                self.rx.extend(f"LCAPS 1 {p[2]} LONGO1\n".encode())
                return len(dados)
            return super().write(dados)
    esp = EspLongo()
    rosto = RostoOledRuntime(estado_getter=lambda: {}, porta="TESTE", abrir_serial=lambda _: esp)
    assert rosto.sincronizar()
    inicio=time.monotonic()
    r=rosto.mover_corpo(180,180,2000,validar_inicio=lambda: time.monotonic()-inicio < .15)
    assert not r["ok"] and r["parada_confirmada"]
    assert time.monotonic()-inicio < .7
    assert len([x for x in esp.enviados if x.startswith("MOTOR ")]) == 1
    assert not rosto.mover_corpo(180,180,5001)["ok"]


def test_intencao_suspensa_persiste_no_owner_e_publica_no_quadro(monkeypatch):
    import threading
    from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
    from scripts.tests.test_companhia_corporal import montar, motores
    from scripts.tests.test_corpo_transporte_oled import EspCorpo
    class EspLongo(EspCorpo):
        def write(self, dados):
            p=dados.decode().split()
            if p[0]=="LCAPS":
                self.rx.extend(f"LCAPS 1 {p[2]} LONGO1\n".encode()); return len(dados)
            return super().write(dados)
    estado, esp, rosto, _, quadro, agora = montar(esp=EspLongo())
    from mente_laylay.autonomia.orquestracao_cooperativa import OrquestradorCooperativoRuntime
    corpo=CorpoMotorRuntime(transporte=rosto,estado=estado,perfil_corporal="rodas_suspensas",
        companhia_bancada_ao_iniciar=True,passeio_bancada_ao_iniciar=True,monotonic=lambda:agora[0])
    coord=OrquestradorCooperativoRuntime(quadro=quadro,clipboard_snapshot=lambda:{},clipboard_getter=lambda:"",
        executar_intencao=lambda *_:False,resolver_caminho=lambda s:s,falar=lambda *_:None,log=lambda _:None)
    corpo.companhia.coordenador=coord
    coord.governanca.registrar_autorizador_escopo("corpo_companhia",corpo.companhia.autorizar_escopo)
    assert corpo.companhia.processar()["ok"]
    estado.atualizar_campos("conversacional", visual_activity="thinking", visual_activity_until=9999999999)
    assert not corpo.companhia.processar()["ok"] and not motores(esp)
    assert estado.mental["intencao_corporal"]["nome"]=="atenta"
    estado.atualizar_campos("conversacional", visual_activity="idle")
    agora[0]+=9
    # Porta real, owner real e coordenador real; acelerar só esperas do relógio externo.
    original=rosto.mover_corpo
    pedidos=[]
    def acelerar(e,d,ms,**kwargs):
        pedidos.append((e,d,ms))
        return original(e,d,50,**kwargs)
    monkeypatch.setattr(rosto,"mover_corpo",acelerar)
    monkeypatch.setattr(corpo.companhia,"_aguardar_gesto",lambda ms,validar:validar())
    assert corpo.companhia.processar()["ok"]
    assert max(x[2] for x in pedidos)>=3000 and max(abs(x[0]) for x in pedidos)>100
    assert estado.mental["intencao_corporal"]["nome"]=="explorar"
    identidade=estado.mental["intencao_corporal"]["id"]
    assert quadro.snapshot()["planos_recentes"][-1]["estado"]=="confirmado"
    assert not corpo.companhia.processar()["ok"]
    repouso = estado.mental["intencao_corporal"]
    assert repouso["id"] != identidade
    assert repouso["nome"] == "descansar" and repouso["fase"] == "repousando"
    identidade_repouso = repouso["id"]
    assert not corpo.companhia.processar()["ok"]
    assert estado.mental["intencao_corporal"]["id"] == identidade_repouso
    assert corpo.executar("CORPO_PARAR",{})["ok"]
    assert not corpo.companhia.processar()["ok"]


def test_plano_novo_no_pc_muda_assinatura_e_nao_confirma_sucesso():
    from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
    d=decidir_intencao_corporal({}, {}, permitir_passeio=True,
        plano={"id":"turno-a","fase":"planejado","ts":100},wall_time=100,agora=10)
    assert d.nome=="atenta" and not d.permite_movimento
    d=decidir_intencao_corporal({}, {}, permitir_passeio=True,
        plano={"id":"turno-a","fase":"executado","ts":100,"comandos":[{"confirmado":True}]},
        novo_sucesso=True,wall_time=100,agora=10)
    assert d.nome!="comemorar", "plano visual não substitui receipt canônico"


def test_raiz_instalada_injeta_perfil_no_owner_existente(tmp_path):
    import subprocess,sys,os
    env=dict(os.environ,LAYLAY_CORPO_PERFIL="rodas_suspensas",LAYLAY_CORPO_WIFI_CONFIG=str(tmp_path/"sem_wifi.json"))
    codigo=f'''
from mente_laylay.integracao import instancia_unica
adquirir=instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica=lambda _:adquirir({str(tmp_path/'instancia')!r})
import laylay
assert laylay._corpo_motor_runtime.companhia.perfil_corporal=="rodas_suspensas"
assert laylay._corpo_motor_runtime.companhia.estado is laylay._estado_compartilhado_runtime
assert laylay._corpo_motor_runtime.transporte is laylay._rosto_oled_runtime
assert laylay._corpo_motor_runtime.companhia.coordenador is laylay._orquestrador_cooperativo_runtime
'''
    r=subprocess.run([sys.executable,"-"],input=codigo,text=True,capture_output=True,env=env,timeout=35)
    assert r.returncode==0,r.stdout+r.stderr


def test_catalogo_vivo_informa_perfil_e_indisponibilidade_sem_executar():
    import json
    from scripts.tests.test_companhia_corporal import montar, motores
    from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    estado, esp, rosto, _, _, _ = montar()
    corpo = CorpoMotorRuntime(transporte=rosto, estado=estado, perfil_corporal="rodas_suspensas")
    disp = DisponibilidadeOperacionalRuntime(rosto_oled_getter=rosto.diagnostico,
                                             corpo_motor_getter=corpo.diagnostico)
    mapa = MapaHabilidadesRuntime(operacional_getter=disp.snapshot)
    pergunta = "você consegue andar e controlar os motores?"
    turno = classificar_modalidade_turno(pergunta)
    resposta = mapa.responder_pergunta_capacidade(pergunta, turno=turno)
    assert "rodas suspensas" in resposta and "LONGO1" in resposta
    assert "Não tenho sensores" in resposta and not motores(esp)
    evidencia = mapa.evidencia_conversacional(pergunta, turno=turno)
    docs = json.loads(evidencia["documentacao_capacidades"])
    assert any("rodas_suspensas" in d["descricao"] for d in docs)
    rosto.encerrar()
    assert "indisponível" in mapa.responder_pergunta_capacidade(pergunta, turno=turno)
    assert not motores(esp)
