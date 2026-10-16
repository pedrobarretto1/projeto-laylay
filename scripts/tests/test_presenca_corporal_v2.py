"""Presença expressiva usa prioridade, emoção e sessão dos owners existentes."""
from scripts.tests.test_companhia_corporal import montar, ativar, emocao, motores
from mente_laylay.integracao.prioridade_interacao_usuario import PrioridadeInteracaoUsuarioRuntime


from scripts.tests.test_corpo_transporte_oled import EspCorpo


class EspPresenca(EspCorpo):
    def __init__(self, *, eack=True, **kwargs):
        super().__init__(**kwargs)
        self.eack=eack

    def write(self, dados):
        p=dados.decode().split()
        resposta=None
        if p[0] in {"ECAPS", "LCAPS", "SCAPS", "RCAPS"}:
            resposta=f"{p[0]} 1 {p[2]} " + {"ECAPS":"OLHOS2", "LCAPS":"LONGO1", "SCAPS":"SOM1", "RCAPS":"RAMPA1"}[p[0]]
        elif p[0] == "EXPR":
            resposta="EACK " + " ".join(p[1:]) if self.eack else "ERROR 1 EXPR_SEM_OLED"
        elif p[0] == "GOODNIGHT":
            resposta="NACK " + " ".join(p[1:])
        elif p[0] == "SOUND":
            resposta="SOUNDACK " + " ".join(p[1:])
        if resposta is None: return super().write(dados)
        self.enviados.append(dados.decode().strip())
        self.rx.extend((resposta+"\n").encode())
        return len(dados)


def test_entrada_recebida_suspende_corpo_antes_da_resposta_da_ia():
    estado, esp, rosto, corpo, _, _ = montar()
    prioridade = PrioridadeInteracaoUsuarioRuntime()
    corpo.companhia.prioridade_interacao_getter = prioridade.ativa
    assert ativar(corpo)["ok"]
    claim = prioridade.adquirir("entrada_canonica")
    emocao(estado, rosto, "alegre")
    assert not corpo.companhia.processar()["ok"], "claim canônico deve suspender o gesto antes da LLM"
    assert not motores(esp)
    assert estado.mental["intencao_corporal"]["nome"] == "atenta"
    prioridade.liberar(claim)
    assert corpo.companhia.processar()["ok"], "emoção vigente pode reagir quando termina a atenção"


def test_variantes_emocionais_preservam_estilo_sem_repeticao_imediata():
    from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
    from scripts.tests.test_rosto_oled import estado_emocional
    _, _, _, corpo, _, _ = montar()
    decisao = decidir_intencao_corporal(estado_emocional("alegre"), {},
                                      permitir_passeio=False, nova_emocao=True)
    gestos = [corpo.companhia._gesto_suspenso(decisao, (1, 2, 0), variante=i) for i in range(3)]
    assert len({g.movimentos for g in gestos}) == 3
    for gesto in gestos:
        assert len(gesto.movimentos) <= 4
        assert all(50 <= ms <= 5000 and max(abs(e), abs(d)) <= 230 for e, d, ms in gesto.movimentos)


def test_variantes_mudam_a_partitura_e_nao_apenas_escala_ou_espelho():
    from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
    from scripts.tests.test_rosto_oled import estado_emocional
    _, _, _, corpo, _, _ = montar()
    for nome, codigo in (("alegre", 1), ("envergonhada", 6), ("surpresa", 5), ("brava", 3)):
        decisao = decidir_intencao_corporal(estado_emocional(nome), {},
                                          permitir_passeio=False, nova_emocao=True)
        bases = [corpo.companhia._gesto_suspenso(decisao, (codigo, 2, 0), variante=i) for i in (0, 2)]
        assinaturas = [tuple((0 if e == d else 1, e * d > 0, e + d > 0) for e, d, _ in g.movimentos) for g in bases]
        assert assinaturas[0] != assinaturas[1], nome
        assert all(len(g.movimentos) <= 4 and sum(ms for _, _, ms in g.movimentos) <= 12000 for g in bases)


def test_composicao_instalada_reusa_prioridade_da_entrada_e_da_percepcao(tmp_path):
    import subprocess, sys
    codigo=f'''
from mente_laylay.integracao import instancia_unica
adquirir=instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica=lambda _:adquirir({str(tmp_path/'instancia')!r})
import laylay
p=laylay._prioridade_interacao_usuario_runtime
assert not p.ativa()
claim=p.adquirir("entrada_canonica")
assert laylay._rosto_oled_runtime.interacao_getter()
assert laylay._corpo_motor_runtime.companhia.prioridade_interacao_getter()
p.liberar(claim)
assert not laylay._rosto_oled_runtime.interacao_getter()
assert not laylay._corpo_motor_runtime.companhia.prioridade_interacao_getter()
'''
    r=subprocess.run([sys.executable,"-"],input=codigo,text=True,capture_output=True,timeout=35)
    assert r.returncode == 0,r.stdout+r.stderr


def test_prioridade_olhos_reage_sem_motor_sem_bip_repetido():
    from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
    esp=EspPresenca()
    p=PrioridadeInteracaoUsuarioRuntime()
    r=RostoOledRuntime(estado_getter=lambda:{},interacao_getter=p.ativa,
                      porta="TESTE",abrir_serial=lambda _:esp)
    assert r.sincronizar()
    qtd_som=len([x for x in esp.enviados if x.startswith("SOUND ")])
    claim=p.adquirir("entrada_canonica")
    assert r.sincronizar()
    assert r.diagnostico()["expressao"]["fase"] == [9,3,0]
    assert not motores(esp)
    assert len([x for x in esp.enviados if x.startswith("SOUND ")]) == qtd_som
    p.liberar(claim)
    assert r.sincronizar()
    assert r.diagnostico()["expressao"]["fase"] == [0,2,0]
    r.encerrar()
    assert any(x.startswith("GOODNIGHT ") for x in esp.enviados)
    assert esp.enviados.index(next(x for x in esp.enviados if x.startswith("STOP "))) < esp.enviados.index(next(x for x in esp.enviados if x.startswith("GOODNIGHT ")))


def test_coreografia_cooperativa_confirma_olhos_antes_de_motor_e_acomoda(monkeypatch):
    from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
    from mente_laylay.autonomia.orquestracao_cooperativa import OrquestradorCooperativoRuntime
    from scripts.tests.test_rosto_oled import estado_emocional
    estado,esp,rosto,_,quadro,clock=montar(esp=EspPresenca())
    corpo=CorpoMotorRuntime(transporte=rosto,estado=estado,perfil_corporal="rodas_suspensas",
                           companhia_bancada_ao_iniciar=True,monotonic=lambda:clock[0])
    coordenador=OrquestradorCooperativoRuntime(quadro=quadro,clipboard_snapshot=lambda:{},
        clipboard_getter=lambda:"",executar_intencao=lambda *_:False,resolver_caminho=lambda x:x,
        falar=lambda *_:None,log=lambda _:None)
    corpo.companhia.coordenador=coordenador
    coordenador.governanca.registrar_autorizador_escopo("corpo_companhia",corpo.companhia.autorizar_escopo)
    rosto.companhia_getter=corpo.companhia.diagnostico
    assert corpo.companhia.processar()["ok"]
    # O bip de boot também respeita o espaçamento de 2 s do owner sonoro.
    import time
    time.sleep(2.05)
    estado.substituir("conversacional",estado_emocional("alegre"))
    assert rosto.sincronizar()
    antes=len(esp.enviados)
    mover=rosto.mover_corpo
    monkeypatch.setattr(rosto,"mover_corpo",lambda e,d,ms,**kw:mover(e,d,50,**kw))
    monkeypatch.setattr(corpo.companhia,"_aguardar_gesto",lambda ms,validar:validar())
    assert corpo.companhia.processar()["ok"]
    comandos=esp.enviados[antes:]
    expr=[x for x in comandos if x.startswith("EXPR ")]
    assert expr[0].split()[5]=="0" and expr[-1].split()[5]=="2"
    inicio_motor=next(i for i,c in enumerate(comandos) if c.startswith("MOTOR "))
    assert any(c.startswith("EXPR ") and c.split()[5]=="1" for c in comandos[:inicio_motor])
    assert comandos[inicio_motor].startswith("MOTOR 2 ")
    assert sum(c.startswith("SOUND ") for c in comandos)==1
    assert quadro.snapshot()["planos_recentes"][-1]["estado"]=="confirmado"
    # Sem ACK óptico, não usar receipt do motor anterior como confirmação.
    clock[0]+=3
    esp.eack=False
    estado.substituir("conversacional",estado_emocional("brava"))
    assert rosto.sincronizar()
    n=len(motores(esp))
    assert not corpo.companhia.processar()["ok"]
    assert len(motores(esp))==n
    assert quadro.snapshot()["planos_recentes"][-1]["estado"]!="confirmado"


def test_expressao_sem_causa_sem_sessao_ou_parametros_validos_nao_envia():
    from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
    esp=EspPresenca()
    r=RostoOledRuntime(estado_getter=lambda:{},porta="TESTE",abrir_serial=lambda _:esp)
    assert not r.expressar_gesto(1,1,1,900)["ok"]
    assert r.sincronizar()
    n=len(esp.enviados)
    assert not r.expressar_gesto(1,1,1,900,validar_inicio=lambda:False)["ok"]
    assert not r.expressar_gesto(1,1,1,6001)["ok"]
    assert len(esp.enviados)==n


def test_catalogo_vivo_descreve_presenca_negociada_sem_inventar_suporte():
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    _,esp,rosto,corpo,_,_=montar(esp=EspPresenca())
    disp=DisponibilidadeOperacionalRuntime(rosto_oled_getter=rosto.diagnostico,corpo_motor_getter=corpo.diagnostico)
    mapa=MapaHabilidadesRuntime(operacional_getter=disp.snapshot)
    pergunta="você consegue expressar emoções no rosto OLED?"
    resposta=mapa.responder_pergunta_capacidade(pergunta,turno=classificar_modalidade_turno(pergunta))
    assert "OLHOS2 está disponível" in resposta and "gradualmente" in resposta and not motores(esp)
    rosto._expressao_suportada=False
    assert "OLHOS2 está indisponível" in mapa.responder_pergunta_capacidade(pergunta,turno=classificar_modalidade_turno(pergunta))


def test_rampa_exige_suporte_e_parada_nao_depende_do_ack_do_alvo():
    from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
    esp=EspCorpo()
    r=RostoOledRuntime(estado_getter=lambda:{},porta="TESTE",abrir_serial=lambda _:esp)
    assert r.sincronizar()
    assert not r.mover_corpo(180,180,250,suave=True)["ok"] and not motores(esp)
    esp=EspPresenca(mack=False)
    r=RostoOledRuntime(estado_getter=lambda:{},porta="TESTE",abrir_serial=lambda _:esp)
    assert r.sincronizar()
    resultado=r.mover_corpo(180,180,250,suave=True,validar_inicio=lambda:True)
    assert not resultado["ok"] and resultado["parada_confirmada"]


def test_shutdown_do_supervisor_envia_boa_noite_mesmo_com_stop_event():
    from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
    esp=EspPresenca()
    r=RostoOledRuntime(estado_getter=lambda:{},porta="TESTE",abrir_serial=lambda _:esp)
    assert r.sincronizar()
    r._deve_parar=lambda:True
    r.encerrar()
    assert any(c.startswith("GOODNIGHT ") for c in esp.enviados)
    assert esp.fechado and not r.diagnostico()["aplicacao_confirmada"]


def test_shutdown_durante_heartbeat_preserva_boa_noite_antes_de_fechar(monkeypatch):
    from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
    esp=EspPresenca()
    r=RostoOledRuntime(estado_getter=lambda:{},porta="TESTE",abrir_serial=lambda _:esp)
    assert r.sincronizar()
    interrompendo=[False]
    r._deve_parar=lambda:interrompendo[0]
    original=esp.write
    def encerrar_no_frame(dados):
        retorno=original(dados)
        if dados.startswith(b"FACE "):interrompendo[0]=True
        return retorno
    monkeypatch.setattr(esp,"write",encerrar_no_frame)
    assert not r.sincronizar()
    assert any(c.startswith("GOODNIGHT ") for c in esp.enviados)
    assert esp.fechado


def test_falha_atual_toca_mesmo_sem_oportunidade_de_gesto_corporal():
    from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
    from scripts.tests.test_rosto_oled import Relogio
    esp=EspPresenca()
    clock=Relogio()
    atividade={}
    r=RostoOledRuntime(estado_getter=lambda:{},atividade_getter=lambda:atividade,monotonic=clock,
        companhia_getter=lambda:{"ativa":True,"perfil_corporal":"rodas_suspensas"},
        interacao_getter=lambda:True,porta="TESTE",abrir_serial=lambda _:esp)
    assert r.sincronizar()
    clock.agora+=2.1
    atividade.update(origem="atividade_operacional_observada",falha_id=1,falha_monotonic=clock.agora)
    assert r.sincronizar()
    assert any(c.startswith("SOUND ") and c.endswith(" 2") for c in esp.enviados)
    n=sum(c.startswith("SOUND ") for c in esp.enviados)
    assert r.sincronizar()
    assert sum(c.startswith("SOUND ") for c in esp.enviados)==n
    assert not motores(esp)
