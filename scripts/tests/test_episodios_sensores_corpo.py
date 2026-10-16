"""Percepção confirmada vira experiência; experiência nunca concede tração."""
from copy import deepcopy
import pytest

from scripts.tests.test_protecao_sensores_corpo import EspPresenca
from scripts.tests.test_companhia_corporal import montar, ativar, motores
from scripts.tests.test_experiencia_corporal_continua import conectar_aprendizado
from scripts.tests.test_corpo_transporte_oled import EspCorpo


class EspEpisodios(EspPresenca):
    def __init__(self):
        super().__init__()
        self.incidente=0; self.fase="PRONTA"; self.risco="NENHUM"; self.tentativa=0
        self.borda=100; self.frente=200

    def write(self, dados):
        p=dados.decode().split()
        if p[0]=="MOTOR":
            return EspCorpo.write(self,dados)
        if p[0] in {"GUARD","DIST"}:
            self.enviados.append(dados.decode().strip())
            if p[0]=="GUARD":
                r=f"GUARD 1 {p[2]} {self.sessao} {self.incidente} 0 {self.risco} {self.fase} 130 100 IRRITADA {self.tentativa} {int(self.vigia)}"
            else:
                r=f"DIST 1 {p[2]} FRENTE 48 VALIDA {self.frente} 10 0 BORDA 49 VALIDA {self.borda} 10 0"
            self.rx.extend((r+"\n").encode()); return len(dados)
        return super().write(dados)


def observar(rosto, corpo, esp, fase, *, incidente=1, risco="OBSTACULO", tentativa=1):
    esp.incidente=incidente; esp.fase=fase; esp.risco=risco; esp.tentativa=tentativa
    esp.frente=80 if risco=="OBSTACULO" else 200
    assert rosto.sincronizar()
    return corpo.companhia.processar()


def episodios(estado):
    return [e for e in estado.obter_copia("mental","historico_corporal",[]) if e.get("tipo")=="episodio_sensorial"]


def test_busca_local_entra_na_experiencia_mesmo_sem_iniciativa_do_pc(tmp_path):
    estado,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    motor=conectar_aprendizado(corpo,tmp_path)
    observar(rosto,corpo,esp,"BUSCANDO")
    h=episodios(estado)
    assert len(h)==1, "GUARD validado não chega ao owner da experiência compartilhada"
    e=h[0]
    assert e["fase"]=="BUSCANDO" and e["risco"]=="OBSTACULO"
    assert e["turno_id"]=="" and e["origem_intencao"]=="reflexo_firmware"
    assert e["observacao_confirmada"] and not e["confirmado"]
    assert not e["prova_deslocamento"] and not e["autoriza_execucao"]
    assert not motores(esp) and not corpo.companhia.diagnostico()["ativa"]
    observar(rosto,corpo,esp,"ESPERA_BUSCA",tentativa=4)
    e=episodios(estado)[0]
    assert e["resultado"]=="busca_em_espera" and e["tentativa_busca"]==4
    chave="corpo_sensorial:bancada:OBSTACULO:busca_em_espera"
    eventos=motor.memoria.listar_eventos_aprendizado(chave)
    assert len(eventos)==1 and eventos[0]["contexto"]["experiencia"]["id"]==e["id"]
    for _ in range(4): observar(rosto,corpo,esp,"ESPERA_BUSCA",tentativa=4)
    assert len(episodios(estado))==1 and len(motor.memoria.listar_eventos_aprendizado(chave))==1
    assert not motores(esp)
    rosto.encerrar()


def test_rodadas_distintas_preservam_identidade_e_chegam_ao_raciocinio():
    from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal
    estado,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    for i in (1,2):
        observar(rosto,corpo,esp,"BUSCANDO",incidente=i)
        observar(rosto,corpo,esp,"ESPERA_BUSCA",incidente=i,tentativa=4)
    h=episodios(estado)
    assert len(h)==2 and h[0]["id"]!=h[1]["id"]
    modelo=corpo.modelo_para_mente()
    assert modelo["experiencia"]["sensorial"]["buscas_em_espera"]==2
    prompt=formatar_modelo_corporal(modelo)
    assert "busca_em_espera" in prompt and "deslocamento" in prompt
    assert len(prompt)<=3800
    rosto.encerrar()


def test_experiencia_sensorial_nao_empresta_sucesso_ao_plano_ou_gesto(tmp_path):
    estado,esp,rosto,corpo,quadro,_=montar(esp=EspEpisodios())
    motor=conectar_aprendizado(corpo,tmp_path)
    observar(rosto,corpo,esp,"CONCLUIDA",risco="NENHUM",tentativa=0)
    e=episodios(estado)
    assert e and not e[0]["confirmado"] and not e[0]["parada_confirmada"]
    assert not motores(esp) and not quadro.snapshot()["planos_recentes"]
    assert not estado.obter_copia("mental","atividade_operacional",{}).get("sucesso_id")
    assert not e[0]["prova_deslocamento"]
    rosto.encerrar()


def test_historia_de_buscas_muda_proxima_decisao_sem_desarmar_reflexo(monkeypatch):
    import time
    estado,esp,rosto,corpo,_,agora=montar(esp=EspEpisodios())
    relogio=[time.time()]
    corpo.experiencias.clock=lambda:relogio[0]
    rosto.busca_obstaculos_getter=corpo.companhia.autorizar_busca_obstaculos
    assert ativar(corpo)["ok"]
    for i in (1,2):
        observar(rosto,corpo,esp,"BUSCANDO",incidente=i)
        observar(rosto,corpo,esp,"ESPERA_BUSCA",incidente=i,tentativa=4)
    decisao=corpo.companhia.diagnostico()["intencao"]
    assert decisao.get("motivo")=="busca_local_em_espera", "PC não acompanha a intenção da proteção"
    assert corpo.companhia.autorizar_busca_obstaculos(rosto.diagnostico()["sessao"])
    # O reflexo local conserva sua autorização. O sossego altera só iniciativas
    # futuras do PC após o sensor voltar a indicar uma situação sem risco.
    observar(rosto,corpo,esp,"PRONTA",incidente=2,risco="NENHUM",tentativa=4)
    assert corpo.companhia.diagnostico()["intencao"]["motivo"]=="acomodacao_apos_buscas"
    assert not motores(esp)
    # A história não bloqueia uma ordem manual com autorização própria.
    assert corpo.executar("CORPO_MOVER",{"direcao":"frente"})["ok"]
    assert not corpo.companhia.diagnostico()["ativa"]
    rosto.encerrar()


@pytest.mark.parametrize("fronteira",["fonte","expirada","sem_sessao","sem_receipt","replay","regressao_incidente"])
def test_snapshot_sem_fonte_vigente_nao_cria_nem_reescreve_experiencia(fronteira):
    estado,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    esp.incidente=1;esp.fase="BUSCANDO";esp.risco="OBSTACULO";esp.tentativa=1
    assert rosto.sincronizar()
    d=deepcopy(rosto.diagnostico())
    if fronteira in {"replay","regressao_incidente"}:
        corpo.experiencias.observar_sensores(d,perfil="bancada")
        antes=deepcopy(estado.obter_copia("mental","historico_corporal",[]))
        if fronteira=="regressao_incidente":
            d["sensores"]["consulta_id"]+=1
            d["sensores"]["protecao"]["incidente_id"]=0
    else:
        antes=[]
        if fronteira=="fonte":d["sensores"]["origem"]="modelo"
        if fronteira=="expirada":d["sensores"]["recente"]=False
        if fronteira=="sem_sessao":d["sessao"]=""
        if fronteira=="sem_receipt":d["sensores"]["protecao"]["origem"]="contexto"
    assert not corpo.experiencias.observar_sensores(d,perfil="bancada")
    assert estado.obter_copia("mental","historico_corporal",[])==antes
    assert not motores(esp)
    rosto.encerrar()


def test_recuperacao_traz_historia_sem_reabrir_risco_atual_ou_concessao(tmp_path):
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
    from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
    estado,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    motor=conectar_aprendizado(corpo,tmp_path)
    observar(rosto,corpo,esp,"BUSCANDO")
    observar(rosto,corpo,esp,"ESPERA_BUSCA",tentativa=4)
    observar(rosto,corpo,esp,"PRONTA",risco="NENHUM",tentativa=4)
    novo_estado=criar_estado_compartilhado_runtime()
    novo=CorpoMotorRuntime(transporte=rosto,estado=novo_estado)
    novo.experiencias.conectar_aprendizado(motor)
    h=episodios(novo_estado)
    assert len(h)==1 and h[0]["resultado"]=="protecao_rearmada"
    assert h[0]["recuperada_da_memoria"]
    contexto=novo.experiencias.contexto_sensorial(rosto.diagnostico(),perfil="bancada")
    assert contexto["buscas_em_espera"]==0
    assert not novo.companhia.diagnostico()["ativa"] and not motores(esp)
    rosto.encerrar()


def test_falha_de_persistencia_nao_apaga_observacao_ou_inventa_aprendizado(monkeypatch,tmp_path):
    estado,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    motor=conectar_aprendizado(corpo,tmp_path)
    monkeypatch.setattr(motor,"registrar_evidencia",lambda **kw:None)
    observar(rosto,corpo,esp,"BLOQUEADA")
    assert episodios(estado)[0]["observacao_confirmada"]
    assert corpo.experiencias.retrato()["ultimo_erro"]=="falha_persistencia_experiencia_sensorial"
    assert not motores(esp)
    rosto.encerrar()


def test_catalogo_vivo_e_pergunta_natural_explicam_experiencia_condicional():
    from mente_laylay.especialistas.capacidades import consultar_capacidade
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    _,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    observar(rosto,corpo,esp,"ESPERA_BUSCA",tentativa=4)
    mapa=MapaHabilidadesRuntime(operacional_getter=DisponibilidadeOperacionalRuntime(corpo_motor_getter=corpo.diagnostico).snapshot)
    resposta=mapa.responder_pergunta_capacidade("você aprende com o que seus sensores detectam?")
    assert "mesma experiência corporal" in resposta
    assert "deslocamento" in resposta and not motores(esp)
    assert "Episódios sensoriais" in consultar_capacidade("CORPO_COMPANHIA")["percepcao_condicional"]
    rosto.encerrar()


def test_protecao_no_plano_cooperativo_permanece_parcial_ao_virar_experiencia(monkeypatch):
    from scripts.tests.test_companhia_corporal import emocao
    class EspInterrompe(EspEpisodios):
        def write(self,dados):
            p=dados.decode().split()
            if p[0]=="MOTOR":
                self.enviados.append(dados.decode().strip())
                self.incidente=1;self.fase="BLOQUEADA";self.risco="OBSTACULO";self.frente=80
                self.rx.extend(f"HAZARD 1 {self.sessao} {p[3]} 1 OBSTACULO\n".encode())
                return len(dados)
            return super().write(dados)
    estado,esp,rosto,corpo,quadro,_=montar(esp=EspInterrompe())
    assert ativar(corpo)["ok"]
    monkeypatch.setattr(corpo.companhia,"_aguardar_gesto",lambda ms,validar:validar())
    emocao(estado,rosto,"alegre")
    retorno=corpo.companhia.processar()
    assert not retorno["ok"] and retorno["interrompido_por_protecao"]
    assert quadro.snapshot()["planos_recentes"][-1]["estado"]=="falhou"
    corpo.companhia.processar()
    assert episodios(estado) and not episodios(estado)[0]["confirmado"]
    assert len(motores(esp))==1
    assert not estado.obter_copia("mental","atividade_operacional",{}).get("sucesso_id")
    rosto.encerrar()


def test_composicao_real_liga_observacao_aprendizado_modelo_e_catalogo(monkeypatch,tmp_path):
    from scripts.tests.test_corpo_motor import _root_instalado
    from scripts.tests.test_corpo_na_mente import instalar_turno
    from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
    from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal
    monkeypatch.setenv("LAYLAY_ROSTO_PORTA","OFF")
    root,_,_=_root_instalado(monkeypatch,tmp_path)
    corpo=root._corpo_motor_runtime; estado=root._estado_compartilhado_runtime
    corpo.companhia.revogar("ensaio_sem_motores")
    monkeypatch.setitem(estado.mental,"historico_corporal",[])
    monkeypatch.setitem(estado.mental,"experiencia_corporal",{})
    monkeypatch.setattr(corpo.experiencias,"_consulta_sensorial",("",0,0))
    esp=EspEpisodios()
    rosto=RostoOledRuntime(estado_getter=lambda:estado.retrato_dominio("conversacional"),
        porta="TESTE",abrir_serial=lambda _:esp)
    monkeypatch.setattr(corpo,"transporte",rosto)
    assert rosto.sincronizar()
    assert corpo.experiencias.aprendizado is root._motor_aprendizado_runtime
    assert corpo.companhia.coordenador is root._orquestrador_cooperativo_runtime
    observar(rosto,corpo,esp,"BUSCANDO")
    observar(rosto,corpo,esp,"ESPERA_BUSCA",tentativa=4)
    e=episodios(estado)[0]
    assert root._motor_aprendizado_runtime.memoria.obter_hipotese_aprendizado("corpo_sensorial:bancada:OBSTACULO:busca_em_espera")
    instalar_turno(estado,turno_id="pergunta_sobre_corpo")
    corpo.modelo_para_mente("pergunta_sobre_corpo")
    p=estado.obter_copia("mental","plano_turno_atual",{})
    assert p["retrato_corporal"]["ultima_experiencia"]["id"]==e["id"]
    assert not p["retrato_corporal"]["ultima_experiencia"]["pertence_ao_turno_atual"]
    assert "busca_em_espera" in formatar_modelo_corporal(p["retrato_corporal"])
    resposta=root._mapa_habilidades_runtime.responder_pergunta_capacidade("você aprende com os sensores do corpo?")
    assert "mesma experiência corporal" in resposta
    assert not motores(esp)
    rosto.encerrar()


def test_feedback_sobre_reacao_nao_ensina_preferencia_por_variante_inexistente(tmp_path):
    estado,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    motor=conectar_aprendizado(corpo,tmp_path)
    observar(rosto,corpo,esp,"ESPERA_BUSCA",tentativa=4)
    e=episodios(estado)[0]
    assert corpo.experiencias.observar_feedback("gostei desse movimento",turno_id="avaliacao",referencia_id=e["id"])
    assert not motor.memoria.obter_hipotese_aprendizado("corpo_preferencia:bancada:protecao_sensorial:0")
    assert not motores(esp)
    rosto.encerrar()


def test_contexto_de_rodadas_em_companhia_cabe_no_prompt_e_preserva_limites():
    from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal
    _,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    assert ativar(corpo)["ok"]
    for i in (1,2):
        observar(rosto,corpo,esp,"BUSCANDO",incidente=i)
        observar(rosto,corpo,esp,"ESPERA_BUSCA",incidente=i,tentativa=4)
    modelo=corpo.modelo_para_mente()
    prompt=formatar_modelo_corporal(modelo)
    assert len(prompt)<=3800
    assert '"buscas_em_espera":2' in prompt
    assert "Não copie o retrato" in prompt and "perm" in prompt
    rosto.encerrar()


def test_episodios_dos_sensores_nao_apagam_o_orcamento_de_gestos_recentes():
    estado,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    assert corpo.executar("CORPO_MOVER",{"direcao":"frente"})["ok"]
    for i in range(1,14):
        observar(rosto,corpo,esp,"ESPERA_BUSCA",incidente=i,tentativa=4)
    ritmo=corpo.experiencias.ritmo_recente(sessao=rosto.diagnostico()["sessao"],perfil="bancada")
    assert ritmo["gestos_120s"]==1, "telemetria dos sensores consumiu a janela dos comandos de motor"
    assert ritmo["motor_ms_60s"]>0
    assert len(episodios(estado))==12
    assert len(estado.obter_copia("mental","historico_corporal",[]))<=24
    rosto.encerrar()


@pytest.mark.parametrize("alvo",["sensores","música","memória"])
def test_pergunta_sobre_aprendizado_usa_porta_de_capacidades_sem_autorizar(alvo):
    from mente_laylay.especialistas.mapa_habilidades import _texto_pergunta_capacidade
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    texto=f"você aprende com {alvo}?"
    assert _texto_pergunta_capacidade(texto)
    assert not classificar_modalidade_turno(texto)["autoriza_execucao"]


def test_sossego_pos_busca_expira_e_atencao_pc_mantem_prioridade():
    from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
    vivencia={"origem":"experiencia_sensorial_observada","vigente":True,
        "autoriza_execucao":False,"buscas_em_espera":2,"segundos_ultima_espera":2,
        "fase_atual":"PRONTA","risco_atual":"NENHUM"}
    d=decidir_intencao_corporal({}, {},permitir_passeio=True,vivencia_sensorial=vivencia)
    assert d.nome=="descansar" and d.motivo=="acomodacao_apos_buscas" and not d.permite_movimento
    d=decidir_intencao_corporal({}, {},permitir_passeio=True,vivencia_sensorial=vivencia,interacao_prioritaria=True)
    assert d.motivo=="atividade_pc_em_andamento"
    d=decidir_intencao_corporal({}, {},permitir_passeio=True,vivencia_sensorial={**vivencia,"segundos_ultima_espera":13})
    assert d.motivo!="acomodacao_apos_buscas"
    d=decidir_intencao_corporal({}, {},permitir_passeio=False,vivencia_sensorial={**vivencia,"vigente":False})
    assert not d.permite_movimento


def test_retrato_sem_companhia_define_saida_sem_copiar_observacoes():
    from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal
    prompt=formatar_modelo_corporal({"origem":"owner_corpo_usb","conectada":True,"companhia_ativa":False})
    assert '"fala":' in prompt and '"comandos":[]' in prompt, "retrato factual não pode virar o schema de saída"
    assert "omita intencao_corporal" in prompt
