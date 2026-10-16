"""Episódio medido -> presença canônica; observação não concede execução."""
import json
import pytest
from mente_laylay.especialistas.percepcao_inercial import interpretar_imu
from scripts.tests.test_imu_corporal import EspImu
from scripts.tests.test_companhia_corporal import montar, motores


class EspManuseio(EspImu):
    def __init__(self):
        super().__init__()
        self.fase="TRANQUILA";self.evento=0
    def write(self,dados):
        p=dados.decode().split()
        if p[0]=="IMU":
            self.enviados.append(dados.decode().strip())
            self.rx.extend((f"IMU 1 {p[2]} 104 PRONTA 5 1 2000 0 0 0 1000 {self.manuseio} 152 "
                f"{self.fase} {self.evento} 2000 1\n").encode())
            return len(dados)
        return super().write(dados)


def test_fase_medida_chega_sem_outro_classificador_e_sem_autoridade():
    i=interpretar_imu("IMU 1 7 104 PRONTA 5 1 2000 0 0 0 1000 INCLINADA 152 DESCONFIADA 3 2000 1",7)
    assert i["fase_manuseio"]=="DESCONFIADA" and i["evento_manuseio"]==3
    assert i["autoriza_execucao"] is False


def test_episodio_real_do_owner_vira_oportunidade_sem_repeticao_ou_movimento():
    estado,esp,rosto,corpo,_,_=montar(esp=EspManuseio())
    try:
        esp.manuseio="INCLINADA";esp.fase="DESCONFIADA";esp.evento=2
        rosto.sincronizar();corpo.companhia.processar()
        c=corpo.experiencias.candidato_presenca()
        assert c["dominio"]=="corpo" and "inclinado" in c["conteudo"]
        assert c["executavel"] is False and c["autoriza_execucao"] is False
        assert not corpo.experiencias.candidato_presenca()
        assert not motores(esp)
        assert estado.mental["experiencia_corporal"]["fase_manuseio"]=="DESCONFIADA"
    finally:rosto.encerrar()


def test_percepcao_expirada_ou_sessao_nova_nao_vira_comentario():
    _,esp,rosto,corpo,_,_=montar(esp=EspManuseio())
    try:
        esp.manuseio="MOVIMENTO_BRUSCO";esp.fase="RESMUNGO";esp.evento=3
        rosto.sincronizar();corpo.companhia.processar()
        rosto._imu_em-=2
        assert not corpo.experiencias.candidato_presenca()
        rosto.sincronizar();c=corpo.experiencias.candidato_presenca()
        assert c
        rosto._sessao="abcdef00"
        assert not corpo.experiencias.evento_presenca_vigente(c)
    finally:rosto.encerrar()


def turno_corporal(evento):
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_evento
    return {"natureza_entrada":"evento","entrada_cognitiva":evento,
        "autoridade_usuario":False,"permissao_execucao":False,"autoriza_execucao":False,
        "contrato_fala":construir_contrato_semantico_evento(evento)}


def test_presenca_usa_cognicao_e_fila_compartilhadas_sem_promover_observacao():
    from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
    from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
    from scripts.tests.test_red_p1c_resposta_evento_porteiro import _PromptRealista,_ModeloObservado
    _,esp,rosto,corpo,_,_=montar(esp=EspManuseio())
    recebidos=[];fila=[]
    autor=RespostaEventoRuntime(preparacao_prompt=_PromptRealista(),
        modelo_llm=_ModeloObservado('{"fala":"Fiquei tortinha aqui... minha pose elegante foi passear.","comandos":[]}'),
        agendar_fala_proativa=lambda *a,**k:fila.append((a,k)) or True,log=lambda _:None)
    def cognicao(e):
        recebidos.append(e);return turno_corporal(e)
    diretor=DiretorPresencaRuntime(candidato_observado_getter=corpo.experiencias.candidato_presenca,
        validar_observacao=corpo.experiencias.evento_presenca_vigente,
        processar_evento_cognitivo=cognicao,processar_proposta_comunicativa=autor.processar,
        registrar_oportunidade=lambda _: {"decisao":"sugerir"},log=lambda _:None)
    try:
        esp.manuseio="INCLINADA";esp.fase="DESCONFIADA";esp.evento=2
        rosto.sincronizar();corpo.companhia.processar()
        r=diretor.executar_ciclo()
        assert recebidos and recebidos[0]["autoridade_usuario"] is False
        assert recebidos[0]["evidencia"]["observacao_corporal"]["fase_manuseio"]=="DESCONFIADA"
        assert r["proposta_comunicativa"]["agendada"] and len(fila)==1
        assert fila[0][1]["validar_vigencia"]()
        assert not motores(esp)
        assert not diretor.executar_ciclo().get("proposta_comunicativa")
        esp.fase="RECOMPONDO";esp.manuseio="ESTAVEL";esp.evento=3;rosto.sincronizar()
        # Relato no passado continua factual após recompor; sessão/TTL
        # continuam sendo fronteiras de invalidação.
        assert fila[0][1]["validar_vigencia"]()
        rosto._sessao="abcdef00"
        assert not fila[0][1]["validar_vigencia"]()
    finally:rosto.encerrar()


@pytest.mark.parametrize("fala",[
    "Você me machucou!", "Estou no seu colo.", "Minha bateria acabou.",
    "Vou girar para sair daqui.", "Você é malvado!",
])
def test_autoria_corporal_sem_medida_ou_acusatoria_nao_chega_a_voz(fala):
    from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
    from scripts.tests.test_red_p1c_resposta_evento_porteiro import _PromptRealista,_ModeloObservado
    evento={"natureza":"evento","origem":"experiencia_corporal","tipo":"presenca_companhia",
        "autoridade_usuario":False,"permissao_execucao":False,
        "evidencia":{"itens":["Meu corpo ficou inclinado."],"observacao_corporal":{
            "fase_manuseio":"DESCONFIADA","autoriza_execucao":False}}}
    fila=[]
    autor=RespostaEventoRuntime(preparacao_prompt=_PromptRealista(),
        modelo_llm=_ModeloObservado(json.dumps({"fala":fala,"comandos":[]})),
        agendar_fala_proativa=lambda *a,**k:fila.append(a) or True,log=lambda _:None)
    r=autor.processar(turno_corporal(evento),dominio="corpo")
    assert not r["agendada"] and not fila


@pytest.mark.parametrize("dominio",["corpo","cotidiano"])
def test_vigencia_tem_owner_e_e_revalidada_apos_modelo_e_na_fila(dominio):
    from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
    from scripts.tests.test_red_p1c_resposta_evento_porteiro import _PromptRealista,_ModeloObservado,_voz_com_porteiro,_turno_evento
    viva=[True];fim=[];modelo=_ModeloObservado('{"fala":"Opa, fiquei tortinha.","comandos":[]}')
    voz=_voz_com_porteiro("emitir")
    autor=RespostaEventoRuntime(preparacao_prompt=_PromptRealista(),modelo_llm=modelo,
        agendar_fala_proativa=voz.agendar_fala_proativa,log=lambda _:None)
    r=autor.processar(_turno_evento(),dominio=dominio,validar_vigencia=lambda:viva[0],
        ao_concluir=lambda *a:fim.append(a))
    assert r["agendada"] and len(voz.proativa_buffer)==1
    viva[0]=False;voz.flush_fala_proativa()
    assert not voz.proativa_buffer and voz.fila.empty()
    assert fim==[(False,"observacao_expirada")]
    assert autor.processar(_turno_evento(),validar_vigencia=lambda:False)["status"]=="observacao_expirada"


def test_modelo_lento_e_composicao_lenta_nao_publicam_observacao_vencida():
    from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
    from scripts.tests.test_red_p1c_resposta_evento_porteiro import _PromptRealista,_ModeloObservado,_voz_com_porteiro,_turno_evento
    viva=[True];fila=[]
    class ModeloLento(_ModeloObservado):
        def executar(self,p):
            viva[0]=False;return super().executar(p)
    autor=RespostaEventoRuntime(preparacao_prompt=_PromptRealista(),
        modelo_llm=ModeloLento('{"fala":"Fiquei tortinha.","comandos":[]}'),
        agendar_fala_proativa=lambda *a,**k:fila.append(a),log=lambda _:None)
    r=autor.processar(_turno_evento(),validar_vigencia=lambda:viva[0])
    assert r["status"]=="observacao_expirada" and not fila
    viva[0]=True;conclusoes=[];voz=_voz_com_porteiro("emitir")
    assert voz.agendar_fala_proativa("observacao","Fiquei tortinha.",
        validar_vigencia=lambda:viva[0],ao_concluir=lambda *a:conclusoes.append(a))
    def compor(itens):
        viva[0]=False;return itens[0]["texto"],"calma",1
    voz.compor_fala_proativa_cb=compor
    voz.flush_fala_proativa()
    assert voz.fila.empty() and conclusoes==[(False,"observacao_expirada")]


def test_contexto_ocupado_nao_vira_fala_e_memoria_nao_reativa_episodio():
    from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
    _,esp,rosto,corpo,_,_=montar(esp=EspManuseio())
    try:
        esp.manuseio="INCLINADA";esp.fase="DESCONFIADA";esp.evento=2
        rosto.sincronizar();corpo.companhia.processar()
        assert corpo.experiencias.candidato_presenca()
        # A observação recente pode ser relatada no passado após recompor;
        # não vira afirmação de que o balanço continua.
        esp.fase="RECOMPONDO";esp.manuseio="ESTAVEL";esp.evento=3
        rosto.sincronizar();corpo.companhia.processar()
        esp.fase="TRANQUILA";esp.evento=4;rosto.sincronizar();corpo.companhia.processar()
        c=corpo.experiencias.candidato_presenca()
        assert c["observacao_corporal"]["fase_manuseio"]=="RECOMPONDO"
        chamadas=[]
        diretor=DiretorPresencaRuntime(contexto_getter=lambda:{"usuario_falando":True},
            processar_evento_cognitivo=lambda e:chamadas.append(e),
            processar_proposta_comunicativa=lambda *_a,**_k:{})
        assert diretor.considerar(c)["motivo"]=="usuario_falando" and not chamadas
        corpo.experiencias._presenca_inercial_considerada=None
        corpo.experiencias.clock=lambda:c["timestamp"]+26
        assert not corpo.experiencias.candidato_presenca()
    finally:rosto.encerrar()


@pytest.mark.parametrize("pergunta",["Você consegue perceber manuseio?","Você tem giroscópio?"])
def test_catalogo_vivo_descreve_comentario_condicional_no_perfil_sem_motor(pergunta):
    from mente_laylay.especialistas.capacidades import consultar_capacidade
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    esp=EspManuseio();esp.motor=False
    _,_,rosto,corpo,_,_=montar(esp=esp)
    try:
        mapa=MapaHabilidadesRuntime(operacional_getter=DisponibilidadeOperacionalRuntime(
            corpo_motor_getter=corpo.diagnostico).snapshot)
        resposta=mapa.responder_pergunta_capacidade(pergunta)
        assert "comentários ocasionais" in resposta and "motores estão indisponíveis" in resposta
        assert "receipt de entrega" in consultar_capacidade("CORPO_MOVER")["expressao_inercial_condicional"]
        assert not motores(esp)
    finally:rosto.encerrar()


def test_assunto_medido_distingue_fases_sem_desligar_deduplicacao_compartilhada():
    from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
    from scripts.tests.test_coordenador_oportunidades import _coordenador
    coordenador,_,encaminhadas=_coordenador()
    diretor=DiretorPresencaRuntime(registrar_oportunidade=coordenador.registrar,
        processar_evento_cognitivo=turno_corporal,
        processar_proposta_comunicativa=lambda *_a,**_k:{"agendada":False,"autoriza_execucao":False},
        clock=lambda:1000,log=lambda _:None)
    base={"origem":"experiencia_corporal","dominio":"corpo","categoria":"companhia",
          "evidencias":["O corpo esteve inclinado."],"confianca":.94,"utilidade":80}
    a=diretor.considerar({**base,"assunto":"manuseio:desconfiada","chave":"episodio1"})
    b=diretor.considerar({**base,"assunto":"manuseio:recompondo","chave":"episodio2"})
    c=diretor.considerar({**base,"assunto":"manuseio:recompondo","chave":"episodio3"})
    assert a["status"]==b["status"]=="proposta_cognitiva"
    assert c["motivo"]=="governanca" and len(encaminhadas)==2
    assert c["decisao_iniciativa"]["decisao"]=="ignorar_duplicada_semantica"


def test_observacao_corporal_nao_contorna_prioridade_do_porteiro_real():
    from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
    porteiro=PorteiroProatividadeRuntime(contexto_getter=lambda:{"usuario_falando":True},agora=lambda:1000)
    r=porteiro.avaliar(tipo="presenca_corporal",texto="Fiquei tortinha.",turno_ativo=True)
    assert r["acao"]!="emitir"


@pytest.mark.parametrize("dominio",["corpo","cotidiano"])
def test_instrucao_final_de_evento_preserva_fatos_e_limites_em_compactacao_e_retry(dominio):
    from mente_laylay.integracao.llm_http import compactar_payload_llm_local
    from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
    atual={"role":"system","content":"EVENTO COGNITIVO ESTRUTURADO. "+"contexto anterior "*120+
        json.dumps({"dominio":dominio,"fato":"corpo permaneceu inclinado","autoriza_execucao":False})+
        " RECLAMONA_FOFA_NO_PASSADO_SEM_INVENTAR_COLO"}
    p={"_laylay_preservar_evento_sistema":True,"messages":[{"role":"system","content":BASE_SYSTEM_PROMPT},
        {"role":"user","content":"última fala real independente"},atual],"max_tokens":180}
    for _ in range(2):
        p=compactar_payload_llm_local(p)
        assert p["messages"][-1]==atual
        assert sum(m["content"]==atual["content"] for m in p["messages"])==1


def test_retry_http_preserva_evento_tipado_sem_enviar_metadado_interno_ao_provedor():
    import threading
    from types import SimpleNamespace
    from mente_laylay.integracao.llm_http import post_chat_llm
    evento={"role":"system","content":"EVENTO ATUAL "+"fato comprovado "*160+" SEM AUTORIDADE"}
    enviados=[]
    def post(_url,**kwargs):
        enviados.append(kwargs["json"])
        return SimpleNamespace(status_code=400 if len(enviados)==1 else 200,text="diagnostico")
    resultado,_=post_chat_llm({}, {"_laylay_preservar_evento_sistema":True,"max_tokens":180,
        "messages":[{"role":"system","content":"Você é Laylay."},evento]},
        base_url="http://localhost:11434/v1",local_timeout=12,remote_timeout=12,
        bad_request_until=0,lock=threading.Lock(),requests_post=post,print_fn=lambda *_:None)
    assert resultado.status_code==200 and len(enviados)==2
    assert all(p["messages"][-1]==evento and "_laylay_preservar_evento_sistema" not in p for p in enviados)
