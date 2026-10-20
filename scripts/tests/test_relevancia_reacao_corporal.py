"""Decisão de reagir considera mudança e saturação, não um minuto universal."""
from scripts.tests.test_presenca_episodios_observados import montar, evento


def risco(agora, nome='OBSTACULO', *, episodio='sensor:1', marco='inicio'):
    e=evento(agora,episodio=episodio,marco=marco)
    e['assunto']='protecao:'+nome.lower()
    e['observacao_corporal'].update(tipo_observacao='protecao_sensorial',risco_medido=nome)
    return e


def test_mudanca_importante_pode_reagir_antes_de_um_minuto():
    d,t,_,f,_,_=montar()
    assert d.considerar(risco(t[0]))['status']=='proposta_cognitiva'
    f[-1](True,'entregue');t[0]+=5
    r=d.considerar(risco(t[0],'BORDA_SEM_RETORNO',episodio='sensor:2'))
    assert r['status']=='proposta_cognitiva',r


def test_mesma_parede_com_novos_ids_nao_provoca_comentarios_repetidos():
    d,t,_,f,_,_=montar()
    d.considerar(risco(t[0]));f[-1](True,'entregue')
    for n in range(2,9):
        t[0]+=2
        r=d.considerar(risco(t[0],episodio=f'sensor:{n}'))
        assert r['motivo']=='reacao_sem_novidade_suficiente'
    assert len(f)==1


def test_recuperacao_recente_pode_acrescentar_algo_sem_espera_universal():
    d,t,_,f,_,_=montar()
    d.considerar(risco(t[0],'BORDA',episodio='sensor:1'));f[-1](True,'entregue')
    t[0]+=24
    r=d.considerar(risco(t[0],'NENHUM',episodio='sensor:1',marco='recuperacao'))
    assert r['status']=='proposta_cognitiva',r


def test_mudar_somente_id_nao_muda_a_relevancia_e_falha_tts_nao_vira_fala():
    d,t,s,f,_,_=montar()
    d.considerar(risco(t[0]));f[-1](False,'falha_audio');t[0]+=8
    r=d.considerar(risco(t[0],episodio='outro'))
    assert r['motivo']=='reacao_sem_novidade_suficiente'
    assert not s['historico'] and s['contadores']['emitidas']==0


def test_saturacao_pode_escolher_silencio_mesmo_com_varios_estimululos_distintos():
    d,t,_,f,_,_=montar()
    d.considerar(risco(t[0]));f[-1](True,'entregue');t[0]+=1
    d.considerar(risco(t[0],'BORDA',episodio='sensor:2'));t[0]+=1
    r=d.considerar(risco(t[0],'BORDA_SEM_RETORNO',episodio='sensor:3'))
    assert r['motivo']=='reacao_sem_novidade_suficiente'
    assert len(f)==2


def test_reacao_precisa_de_admissao_tipificada_para_nao_decidir_de_novo_no_porteiro():
    from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
    from scripts.tests.test_porteiro_proatividade import _voz
    d,t,_,_,_,_=montar()
    admissoes=[]
    p=PorteiroProatividadeRuntime(contexto_getter=lambda:{},agora=lambda:t[0])
    v=_voz(avaliador=p.avaliar)
    def autoria(turno,**kw):
        opcoes={k:kw[k] for k in ('admissao_observada','validar_vigencia') if k in kw}
        admissoes.append(opcoes)
        aceito=v.agendar_fala_proativa('presenca_corporal',f'Reação diferente {len(admissoes)}.',**opcoes)
        return {'agendada':aceito,'autoriza_execucao':False}
    d.processar_proposta_comunicativa=autoria
    assert d.considerar(risco(t[0]))['proposta_comunicativa']['agendada']
    t[0]+=5
    r=d.considerar(risco(t[0],'BORDA',episodio='sensor:2'))
    assert r['proposta_comunicativa']['agendada'],r
    assert len(v.proativa_buffer)==2
    assert admissoes[0].get('admissao_observada') is not None
    # Booleano/dict livre não representa decisão do Diretor, mesmo com callback.
    t[0]+=1
    assert not v.agendar_fala_proativa('presenca_corporal','Sem admissão real.',
        admissao_observada={'permitido':True},validar_vigencia=lambda:True)


def test_recusa_aprendida_e_prioridade_humana_nao_sao_substituidas_pela_admissao():
    from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
    from mente_laylay.autonomia.ocorrencia_observada import AdmissaoReacaoObservada
    contexto={};t=[1000.0]
    p=PorteiroProatividadeRuntime(contexto_getter=lambda:contexto,agora=lambda:t[0])
    p.registrar_feedback('presenca_corporal',False)
    token=AdmissaoReacaoObservada('evento:1',lambda:True)
    t[0]+=5
    assert p.avaliar(tipo='presenca_corporal',texto='Um susto novo.',admissao_observada=token)['acao']=='descartar'
    t[0]+=150;contexto['usuario_falando']=True
    assert p.avaliar(tipo='presenca_corporal',texto='Um susto novo.',admissao_observada=token)['acao']=='adiar'


def test_porteiro_com_erro_nao_cai_em_compatibilidade_para_admissao_tipificada():
    from mente_laylay.autonomia.ocorrencia_observada import AdmissaoReacaoObservada
    from scripts.tests.test_porteiro_proatividade import _voz
    def quebrado(**kwargs):raise TypeError('adaptador antigo')
    v=_voz(avaliador=quebrado)
    assert not v.agendar_fala_proativa('presenca_corporal','Um fato.',
        admissao_observada=AdmissaoReacaoObservada('e1',lambda:True))
    assert not v.proativa_buffer and v.fila.empty()


def test_vigencia_e_reavaliada_na_entrega_sem_outro_minuto_de_espera():
    from mente_laylay.autonomia.ocorrencia_observada import AdmissaoReacaoObservada
    from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
    from scripts.tests.test_porteiro_proatividade import _voz
    viva=[True];fim=[]
    p=PorteiroProatividadeRuntime(contexto_getter=lambda:{},agora=lambda:1000)
    v=_voz(avaliador=p.avaliar)
    assert v.agendar_fala_proativa('presenca_corporal','Um fato observado.',
        admissao_observada=AdmissaoReacaoObservada('e1',lambda:viva[0]),
        ao_concluir=lambda *a:fim.append(a))
    viva[0]=False
    v.flush_fala_proativa()
    assert not v.proativa_buffer and v.fila.empty() and fim and fim[0][0] is False


def test_recibo_de_outro_evento_nao_chega_a_fila_como_reacao_admitida():
    from mente_laylay.autonomia.ocorrencia_observada import AdmissaoReacaoObservada
    from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
    from scripts.tests.test_manuseio_fofo import turno_corporal
    from scripts.tests.test_red_p1c_resposta_evento_porteiro import _PromptRealista,_ModeloObservado
    fila=[]
    e={'natureza':'evento','origem':'experiencia_corporal','tipo':'presenca_companhia',
        'trace_id':'evento-atual','conteudo':'O corpo esteve inclinado.',
        'autoridade_usuario':False,'permissao_execucao':False,
        'evidencia':{'itens':['O corpo esteve inclinado.'],
            'observacao_corporal':{'fase_manuseio':'DESCONFIADA','autoriza_execucao':False}}}
    r=RespostaEventoRuntime(preparacao_prompt=_PromptRealista(),
        modelo_llm=_ModeloObservado('{"fala":"Fiquei tortinha.","comandos":[]}'),
        agendar_fala_proativa=lambda *a,**kw:fila.append(kw),log=lambda _:None)
    resultado=r.processar(turno_corporal(e),dominio='corpo',evento=e,
        validar_vigencia=lambda:True,admissao_observada=AdmissaoReacaoObservada('outro-evento',lambda:True))
    assert resultado['status']=='admissao_observada_invalida' and not fila


def test_foco_e_feedback_aumentam_seletividade_sem_retirar_a_decisao_do_diretor():
    from mente_laylay.autonomia.ocorrencia_observada import avaliar_relevancia_observada
    e=risco(1000,'BORDA')
    h=[{'ts':995,'assunto':'corpo:OBSTACULO:alerta','identidade':'anterior'}]
    adaptativo=avaliar_relevancia_observada(e,h,agora=1000,perfil='adaptativo',pontuacao_feedback=0)
    quieta=avaliar_relevancia_observada(e,h,agora=1000,perfil='silencioso',pontuacao_feedback=-2)
    assert adaptativo['permitida'] and not quieta['permitida']
