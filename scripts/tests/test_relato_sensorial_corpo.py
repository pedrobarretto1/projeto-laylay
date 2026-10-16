"""Comentários sobre episódios medidos reutilizam presença/cognição/fala."""
import pytest
from scripts.tests.test_companhia_corporal import montar,motores
from scripts.tests.test_episodios_sensores_corpo import EspEpisodios,observar


@pytest.mark.parametrize('risco',['OBSTACULO','BORDA','BORDA_SEM_RETORNO'])
def test_episodio_sensorial_vira_oportunidade_factual_unica_sem_motor(risco):
    _,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    try:
        observar(rosto,corpo,esp,'RECUANDO',risco=risco)
        e=corpo.experiencias.candidato_presenca()
        assert e.get('observacao_corporal',{}).get('tipo_observacao')=='protecao_sensorial'
        assert e['observacao_corporal']['risco_observado']==risco
        assert e['autoriza_execucao'] is False and not e['executavel']
        assert corpo.experiencias.evento_presenca_vigente(e)
        assert not corpo.experiencias.candidato_presenca() and not motores(esp)
        rosto._sensores_em-=2
        assert not corpo.experiencias.evento_presenca_vigente(e)
    finally:rosto.encerrar()


def test_sensorial_perdido_recuperado_da_memoria_ou_sessao_antiga_nao_gera_comentario():
    estado,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    try:
        observar(rosto,corpo,esp,'RECUANDO')
        h=estado.obter_copia('mental','historico_corporal',[])
        estado.atualizar_campos('mental',historico_corporal=[{**x,'recuperada_da_memoria':True} for x in h])
        assert not corpo.experiencias.candidato_presenca()
    finally:rosto.encerrar()


def test_fases_recentes_nao_rejuvenescem_a_deteccao_inicial_antiga():
    estado,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    try:
        observar(rosto,corpo,esp,'RECUANDO')
        h=estado.obter_copia('mental','historico_corporal',[])
        estado.atualizar_campos('mental',historico_corporal=[{**x,'iniciada_em':x['ts']-60} for x in h])
        assert not corpo.experiencias.candidato_presenca()
    finally:rosto.encerrar()


def test_sensorial_atravessa_presenca_e_contrato_fala_compartilhados_sem_efeito():
    from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
    from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
    from scripts.tests.test_manuseio_fofo import turno_corporal
    from scripts.tests.test_red_p1c_resposta_evento_porteiro import _PromptRealista,_ModeloObservado
    _,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    fila=[];turnos=[]
    autor=RespostaEventoRuntime(preparacao_prompt=_PromptRealista(),
        modelo_llm=_ModeloObservado('{"fala":"Tinha algo bem na minha frente... caminho disputado, hein.","comandos":[]}'),
        agendar_fala_proativa=lambda *a,**kw:fila.append((a,kw)) or True,log=lambda _:None)
    def cognição(evento):
        turno=turno_corporal(evento);turnos.append(turno);return turno
    diretor=DiretorPresencaRuntime(candidato_observado_getter=corpo.experiencias.candidato_presenca,
        validar_observacao=corpo.experiencias.evento_presenca_vigente,
        processar_evento_cognitivo=cognição,processar_proposta_comunicativa=autor.processar,
        registrar_oportunidade=lambda _:{'decisao':'sugerir'},log=lambda _:None)
    try:
        observar(rosto,corpo,esp,'BUSCANDO')
        r=diretor.executar_ciclo()
        assert r['proposta_comunicativa']['agendada'] and len(fila)==1
        assert turnos[0]['contrato_fala']['observacao_corporal']['tipo_observacao']=='protecao_sensorial'
        assert fila[0][1]['validar_vigencia']() and not motores(esp)
        rosto._sessao='12345678'
        assert not fila[0][1]['validar_vigencia'](), 'o callback deve chegar até a fila de voz'
    finally:rosto.encerrar()


@pytest.mark.parametrize('fala',['Recuei e escapei da borda.',
    'Encontrei uma saída, agora está seguro.', 'Caí da mesa.',
    'Minha bateria ficou cansada.', 'Você me derrubou!'])
def test_observacao_sensorial_nao_publica_conclusao_fisica_sem_medida(fala):
    import json
    from scripts.tests.test_manuseio_fofo import turno_corporal
    from scripts.tests.test_red_p1c_resposta_evento_porteiro import _PromptRealista,_ModeloObservado
    from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
    _,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    fila=[]
    try:
        observar(rosto,corpo,esp,'RECUANDO')
        e=corpo.experiencias.candidato_presenca()
        evento={'natureza':'evento','origem':'experiencia_corporal','tipo':'presenca_companhia',
            'autoridade_usuario':False,'permissao_execucao':False,
            'evidencia':{'itens':e['evidencias'],'observacao_corporal':e['observacao_corporal']}}
        autor=RespostaEventoRuntime(preparacao_prompt=_PromptRealista(),
            modelo_llm=_ModeloObservado(json.dumps({'fala':fala,'comandos':[]})),
            agendar_fala_proativa=lambda *a,**kw:fila.append(a) or True,log=lambda _:None)
        r=autor.processar(turno_corporal(evento),dominio='corpo',
            validar_vigencia=lambda:corpo.experiencias.evento_presenca_vigente(e))
        assert not r['agendada'] and not fila
    finally:rosto.encerrar()


def test_catalogo_e_pergunta_natural_conhecem_relato_condicional_sem_mover():
    from mente_laylay.especialistas.capacidades import consultar_capacidade
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    _,esp,rosto,corpo,_,_=montar(esp=EspEpisodios())
    try:
        disp=DisponibilidadeOperacionalRuntime(corpo_motor_getter=corpo.diagnostico)
        mapa=MapaHabilidadesRuntime(operacional_getter=disp.snapshot)
        fala=mapa.responder_pergunta_capacidade('você aprende com o que seus sensores detectam?')
        assert 'comentário breve' in fala and 'detecção não prova' in fala
        assert 'ficar quietinha' in consultar_capacidade('CORPO_COMPANHIA')['objetivos_e_relato_condicionais']
        assert not motores(esp)
    finally:rosto.encerrar()
