"""Propósito finito no mesmo owner; quietude é uma decisão executável sem PWM."""
import pytest
from mente_laylay.cognicao.decisao_corporal import IntencaoCorporal
from scripts.tests.test_companhia_corporal import montar, ativar, motores


@pytest.mark.parametrize('nome,mover', [('atenta',False),('descansar',False),
    ('explorar',True),('expressar',True),('comemorar',True),('reagir_falha',True)])
def test_objetivo_curto_publicado_na_mente_tem_proposito_criterio_e_prazo(nome,mover):
    _,esp,rosto,corpo,_,clock=montar()
    try:
        assert ativar(corpo)['ok']
        corpo.companhia._registrar_intencao(IntencaoCorporal(nome,'causa_observada',70,1,2,mover))
        i=corpo.modelo_para_mente()['intencao_em_curso']
        objetivo=i.get('objetivo_curto') or {}
        assert objetivo.get('proposito'), 'a mente recebe apenas um nome de gesto, sem propósito finito'
        assert objetivo['criterio_conclusao']
        assert clock[0]<objetivo['ate_monotonic']<=clock[0]+90
        assert objetivo['autoriza_execucao'] is False and objetivo['prova_deslocamento'] is False
        assert not motores(esp)
        prazo=objetivo['ate_monotonic']
        clock[0]+=1
        corpo.companhia._registrar_intencao(IntencaoCorporal(nome,'causa_observada',70,1,2,mover))
        assert corpo.modelo_para_mente()['intencao_em_curso']['objetivo_curto']['ate_monotonic']==prazo
        clock[0]=prazo+1
        corpo.companhia._registrar_intencao(IntencaoCorporal(nome,'causa_observada',70,1,2,mover))
        novo=corpo.modelo_para_mente()['intencao_em_curso']
        assert novo['id']!=i['id'] and novo['objetivo_curto']['ate_monotonic']>clock[0]
        assert not motores(esp), 'reavaliar cria uma oportunidade, não uma fila de movimentos'
    finally: rosto.encerrar()


def test_objetivo_curto_expirado_nao_autoriza_mais_etapas():
    _,_,rosto,corpo,_,clock=montar()
    try:
        assert ativar(corpo)['ok']
        corpo.companhia._registrar_intencao(IntencaoCorporal('explorar','causa_observada',70,1,2,True))
        i=corpo.companhia.diagnostico()['intencao']
        c=corpo.companhia._concessao
        meta={'concessao_id':c['id'],'perfil':c['perfil'],'proposto_em':clock[0],
              'objetivo_curto_id':i['id'],'objetivo_curto_ate':clock[0]-1}
        assert not corpo.companhia._vigente(meta), 'concessão não pode estender o prazo do objetivo'
    finally:rosto.encerrar()


def test_termino_de_gesto_requer_parada_confirmada_e_nao_prova_caminho():
    _,_,rosto,corpo,_,_=montar()
    try:
        assert ativar(corpo)['ok']
        corpo.companhia._registrar_intencao(IntencaoCorporal('explorar','causa_observada',70,1,2,True))
        i=corpo.companhia.diagnostico()['intencao']['id']
        corpo.companhia._fase_intencao(i,'acomodando',estado='concluida',resultado={'ok':True,'parada_confirmada':False})
        o=corpo.companhia.diagnostico()['intencao'].get('objetivo_curto') or {}
        assert o.get('estado')!='confirmado'
        corpo.companhia._fase_intencao(i,'acomodando',estado='concluida',resultado={'ok':True,'parada_confirmada':True})
        o=corpo.companhia.diagnostico()['intencao'].get('objetivo_curto') or {}
        assert o.get('estado')=='confirmado_por_receipts'
        assert o['prova_deslocamento'] is False
    finally:rosto.encerrar()


@pytest.mark.parametrize('perfil',['bancada','rodas_suspensas'])
def test_descanso_escolhido_na_mente_e_respeitado_por_todos_os_perfis(perfil):
    from scripts.tests.test_companhia_corporal import emocao
    from scripts.tests.test_corpo_transporte_oled import EspCorpo
    class EspLongo(EspCorpo):
        def write(self,dados):
            p=dados.decode().split()
            if p[0]=='LCAPS':
                self.rx.extend(f'LCAPS 1 {p[2]} LONGO1\n'.encode());return len(dados)
            return super().write(dados)
    estado,esp,rosto,corpo,_,_=montar(esp=EspLongo())
    try:
        corpo.companhia.perfil_corporal=perfil
        emocao(estado,rosto,'triste')
        assert ativar(corpo)['ok']
        r=corpo.companhia.processar()
        assert r.get('em_repouso') is True
        assert corpo.modelo_para_mente()['intencao_em_curso']['nome']=='descansar'
        assert not motores(esp)
    finally:rosto.encerrar()


def test_catalogo_vivo_explica_objetivos_curtos_e_quietude_sem_mover():
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    _,esp,rosto,corpo,_,_=montar()
    try:
        d=DisponibilidadeOperacionalRuntime(rosto_oled_getter=rosto.diagnostico,corpo_motor_getter=corpo.diagnostico)
        mapa=MapaHabilidadesRuntime(operacional_getter=d.snapshot)
        pergunta='você consegue manter um objetivo corporal entre turnos?'
        fala=mapa.responder_pergunta_capacidade(pergunta,turno=classificar_modalidade_turno(pergunta))
        assert 'propósito curto' in fala and 'ficar quietinha' in fala
        assert not motores(esp)
    finally:rosto.encerrar()


def test_preparacao_de_fala_mantem_quietude_em_vez_de_executar_fallback_motor():
    estado,esp,rosto,corpo,_,_=montar()
    try:
        assert ativar(corpo)['ok']
        estado.atualizar_campos('conversacional',is_speaking=True,audio_playing=False)
        assert rosto.sincronizar()
        r=corpo.companhia.processar()
        assert r.get('em_observacao') is True and not motores(esp)
        assert corpo.companhia.diagnostico()['intencao']['nome']=='atenta'
    finally:rosto.encerrar()
