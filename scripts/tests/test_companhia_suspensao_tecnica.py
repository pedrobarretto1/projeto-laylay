"""Falha técnica pausa a concessão; só o owner humano a encerra definitivamente."""
import pytest

from scripts.tests.test_recuperacao_corpo_usb import EspSaude
from scripts.tests.test_presenca_corporal_v2 import EspPresenca as EspExpressiva
from scripts.tests.test_companhia_corporal import montar, ativar, emocao, motores


class EspSaudeExpressiva(EspSaude):
    def __init__(self):
        super().__init__(); self.eack=True

    def write(self,dados):
        p=dados.decode().split()
        if p[0] in {'ECAPS','LCAPS','RCAPS','EXPR','SOUND','GOODNIGHT'}:
            return EspExpressiva.write(self,dados)
        if p[0]=='GUARD':
            self.enviados.append(dados.decode().strip())
            self.rx.extend(f'GUARD 1 {p[2]} {self.sessao} 0 0 NENHUM PRONTA 130 100 NENHUMA 0 {int(self.vigia)}\n'.encode())
            return len(dados)
        return super().write(dados)


def preparar():
    estado,esp,rosto,corpo,quadro,t=montar(esp=EspSaudeExpressiva())
    corpo.companhia.perfil_corporal='rodas_suspensas'
    rosto.busca_obstaculos_getter=corpo.companhia.autorizar_busca_obstaculos
    assert ativar(corpo)['ok']
    assert rosto.sincronizar() and esp.vigia
    return estado,esp,rosto,corpo,quadro,t


def falhar_expressao(estado,esp,rosto,corpo):
    esp.eack=False
    emocao(estado,rosto,'alegre')
    r=corpo.companhia.processar()
    assert not r['ok'] and r['motivo']=='sem_confirmacao_expressao'
    assert not motores(esp)
    return r


def test_eack_perdido_nao_apaga_pedido_e_retomada_exige_stop_sem_repetir_gesto():
    estado,esp,rosto,corpo,quadro,t=preparar()
    try:
        falhar_expressao(estado,esp,rosto,corpo)
        d=corpo.companhia.diagnostico()
        assert not d['ativa'] and d['recuperacao_pendente'],d
        assert quadro.snapshot()['planos_recentes'][-1]['estado']!='confirmado'
        esp.eack=True
        t[0]+=1; corpo.companhia.processar()
        assert not corpo.companhia.diagnostico()['ativa']
        t[0]+=5; rosto._saude_em=float('-inf'); assert rosto.sincronizar()
        corpo.companhia.processar(); t[0]+=1.1; corpo.companhia.processar()
        assert corpo.companhia.diagnostico()['ativa']
        assert rosto.sincronizar() and esp.vigia
        assert not motores(esp),'recuperar não repete o gesto interrompido'
    finally:rosto.encerrar()


@pytest.mark.parametrize('veto',['stop','sem_sack','outro_corpo','sem_saude','manuseio','saude_anterior'])
def test_suspensao_tecnica_nao_contorna_veto_ou_receipt_de_parada(veto):
    estado,esp,rosto,corpo,_,t=preparar()
    try:
        falhar_expressao(estado,esp,rosto,corpo); esp.eack=True
        if veto=='stop': corpo.executar('CORPO_PARAR',{})
        if veto=='sem_sack': esp.stopped=False
        if veto=='outro_corpo': esp.uid='aabbccddeeff'
        t[0]+=6
        if veto!='saude_anterior': rosto._saude_em=float('-inf')
        assert rosto.sincronizar()
        if veto=='sem_saude': rosto._saude_em=float('-inf')
        if veto=='manuseio':
            diagnostico=rosto.diagnostico
            rosto.diagnostico=lambda:{**diagnostico(),'imu':{'bloqueio_manuseio':True}}
        corpo.companhia.processar(); t[0]+=1.1; corpo.companhia.processar()
        assert not corpo.companhia.diagnostico()['ativa'] and not motores(esp)
        assert not corpo.companhia.autorizar_busca_obstaculos(rosto._sessao)
    finally:rosto.encerrar()


def test_falhas_repetidas_ampliam_pausa_sem_apagar_pedido_e_sem_replay():
    estado,esp,rosto,corpo,_,t=preparar()
    try:
        for n,pausa in enumerate((2,5,15,30),1):
            # Cada tentativa é uma expressão nova; não se reenvia a anterior.
            esp.eack=False
            emocao(estado,rosto,'alegre' if n%2 else 'brava')
            assert not corpo.companhia.processar()['ok']
            d=corpo.companhia.diagnostico()
            assert d['falhas_tecnicas_consecutivas']==n and d['retomada_em_s']==pausa
            esp.eack=True; t[0]+=pausa+1
            rosto._saude_em=float('-inf'); assert rosto.sincronizar()
            corpo.companhia.processar();t[0]+=1.1;corpo.companhia.processar()
            assert corpo.companhia.diagnostico()['ativa'] and not motores(esp)
            t[0]+=3
    finally:rosto.encerrar()


def test_recuperacao_de_pwm_nao_confirmado_exige_nova_saude_e_nao_repete_motor():
    from scripts.tests.test_corpo_transporte_oled import EspCorpo
    estado,esp,rosto,corpo,_,t=preparar()
    original=esp.write
    esp.write=lambda dados:EspCorpo.write(esp,dados) if dados.decode().startswith('MOTOR ') else original(dados)
    try:
        esp.mack=False; emocao(estado,rosto,'triste')
        r=corpo.companhia.processar()
        assert not r['ok'] and len(motores(esp))==1
        assert corpo.companhia.diagnostico()['recuperacao_pendente']
        esp.mack=True; t[0]+=4; rosto._saude_em=float('-inf'); assert rosto.sincronizar()
        corpo.companhia.processar();t[0]+=1.1;corpo.companhia.processar()
        assert corpo.companhia.diagnostico()['ativa'] and len(motores(esp))==1
    finally:rosto.encerrar()


def test_parada_humana_durante_stop_de_recuperacao_impede_nova_concessao():
    estado,esp,rosto,corpo,_,t=preparar()
    try:
        falhar_expressao(estado,esp,rosto,corpo); esp.eack=True
        t[0]+=4; rosto._saude_em=float('-inf'); assert rosto.sincronizar()
        corpo.companhia.processar();t[0]+=1.1
        parar=rosto.parar_corpo
        def cancelar():
            corpo.companhia.revogar('parada_solicitada')
            return parar()
        rosto.parar_corpo=cancelar
        assert not corpo.companhia.processar()['ok']
        assert not corpo.companhia.diagnostico()['ativa']
        assert not corpo.companhia.diagnostico()['recuperacao_pendente']
        assert not motores(esp)
    finally:rosto.encerrar()
