"""Perda de sessão suspende concessão identificada, sem repetir a ação antiga."""
import pytest
from scripts.tests.test_protecao_sensores_corpo import EspPresenca
from scripts.tests.test_companhia_corporal import montar,ativar,motores,emocao
from mente_laylay.especialistas.saude_corporal import interpretar_saude

class EspSaude(EspPresenca):
    def __init__(self):
        super().__init__(); self.uid="112233445566"; self.boot="00000001"
        self.derrubado=False; self.borda=100
        self.reset_no_motor=False
    def reiniciar(self):
        self.boot=f"{int(self.boot,16)+1:08x}"; self.derrubado=True
        self.sessao=""; self.vigia=False
    def write(self,dados):
        p=dados.decode().split()
        if p[0]=="MOTOR" and self.reset_no_motor:
            self.reset_no_motor=False; self.enviados.append(dados.decode().strip())
            self.reiniciar(); self.rx.extend(b"BOOT 1 LAYLAY_ROSTO\n"); return len(dados)
        if self.derrubado and p[0]=="STOP" and len(p)==4:
            self.enviados.append(dados.decode().strip())
            self.rx.extend(b"ERROR 1 STOP_SEM_SESSAO\n"); return len(dados)
        if p[0]=="HELLO": self.derrubado=False
        if self.derrubado and p[0]=="FACE":
            self.enviados.append(dados.decode().strip())
            self.rx.extend(b"ERROR 1 PACOTE_INVALIDO\n"); return len(dados)
        if p[0]=="HEALTH":
            self.enviados.append(dados.decode().strip())
            self.rx.extend(f"HEALTH 1 {p[2]} {self.uid} {self.boot} 9 10000 210000 200000 0 NENHUMA 0\n".encode())
            return len(dados)
        return super().write(dados)

def preparar():
    estado,esp,rosto,corpo,quadro,agora=montar(esp=EspSaude(),automatico=True)
    rosto.busca_obstaculos_getter=corpo.companhia.autorizar_busca_obstaculos
    assert ativar(corpo)["ok"]
    assert rosto.sincronizar() and esp.vigia
    return estado,esp,rosto,corpo,quadro,agora

def perder(esp,rosto,corpo):
    esp.reiniciar(); assert not rosto.sincronizar()
    corpo.companhia.processar()

def test_apos_esp_reiniciar_companhia_retoma_no_mesmo_corpo_sem_reiniciar_laylay():
    _,esp,rosto,corpo,_,agora=preparar()
    sessao=rosto._sessao
    perder(esp,rosto,corpo)
    assert corpo.companhia.diagnostico().get("recuperacao_pendente"),"primeira fronteira: perda transitória revogou definitivamente o pedido"
    assert not corpo.companhia.diagnostico()["ativa"]
    assert rosto.sincronizar() and rosto._sessao!=sessao and not esp.vigia
    corpo.companhia.processar(); agora[0]+=1.1; corpo.companhia.processar()
    assert corpo.companhia.diagnostico()["ativa"]
    assert rosto.sincronizar() and esp.vigia
    assert rosto.diagnostico()["saude"]["reinicios_observados"]==1
    assert not motores(esp),"reconectar não repete o movimento antigo"
    rosto.encerrar()

def test_espera_por_nova_amostra_nao_apaga_estabilidade_da_conexao_confirmada():
    _,esp,rosto,corpo,_,agora=preparar(); perder(esp,rosto,corpo)
    assert rosto.sincronizar()
    corpo.companhia.processar()
    agora[0]+=.4; rosto._sensores_em=rosto.monotonic()-.8
    corpo.companhia.processar() # Amostra velha veta esta tentativa, não é nova queda USB.
    agora[0]+=.8; assert rosto.sincronizar()
    corpo.companhia.processar()
    assert corpo.companhia.diagnostico()["ativa"]
    assert not motores(esp)
    rosto.encerrar()

def test_reset_durante_gesto_cooperativo_preserva_falha_sem_replay_e_recupera():
    estado,esp,rosto,corpo,quadro,agora=preparar()
    # EspPresenca é um controle de alerta: GUARD informa BORDA constante,
    # mesmo com DIST inferior=100. Aqui precisamos realmente alcançar MOTOR;
    # perigo observado deve bloquear o gesto, não ser ignorado para testar reset.
    escrever=esp.write
    def sem_perigo(dados):
        if dados.decode().startswith('GUARD '):
            p=dados.decode().split()
            esp.enviados.append(dados.decode().strip())
            esp.rx.extend(f'GUARD 1 {p[2]} {esp.sessao} 0 0 NENHUM PRONTA 130 100 NENHUMA 0 {int(esp.vigia)}\n'.encode())
            return len(dados)
        return escrever(dados)
    esp.write=sem_perigo
    emocao(estado,rosto,"triste"); esp.reset_no_motor=True
    r=corpo.companhia.processar()
    assert not r["ok"] and len(motores(esp))==1
    assert corpo.companhia.diagnostico()["recuperacao_pendente"]
    assert quadro.snapshot()["planos_recentes"][-1]["estado"]!="confirmado"
    assert rosto.sincronizar(); corpo.companhia.processar(); agora[0]+=1.1
    corpo.companhia.processar()
    assert corpo.companhia.diagnostico()["ativa"] and len(motores(esp))==1
    rosto.encerrar()

def test_catalogo_e_dev_recebem_saude_verificada_sem_identidade_fisica_bruta():
    from mente_laylay.integracao.dev_console_runtime import DevConsoleRuntime
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    _,esp,rosto,corpo,_,_=preparar()
    disponibilidade=DisponibilidadeOperacionalRuntime(corpo_motor_getter=corpo.diagnostico)
    mapa=MapaHabilidadesRuntime(operacional_getter=disponibilidade.snapshot)
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    pergunta='você consegue andar e controlar os motores?'
    assert 'mesmo ESP identificado' in mapa.responder_pergunta_capacidade(pergunta,turno=classificar_modalidade_turno(pergunta))
    dev=DevConsoleRuntime(); dev.configurar_corpo_getter(lambda:{'transporte':rosto.diagnostico(),'corpo':corpo.diagnostico()})
    d=dev.snapshot()['body']
    assert d['motivo_boot']=='brownout' and esp.uid not in str(d)
    assert corpo.modelo_para_mente()['condicao']['saude_executor']['motivo_boot']=='brownout'
    rosto.encerrar()

@pytest.mark.parametrize("veto",["stop","outro_corpo","sem_saude"])
def test_recuperacao_nao_supera_parada_corpo_diferente_ou_diagnostico_sem_prova(veto):
    _,esp,rosto,corpo,_,agora=preparar(); perder(esp,rosto,corpo)
    if veto=="stop": corpo.executar("CORPO_PARAR",{})
    if veto=="outro_corpo": esp.uid="aabbccddeeff"
    assert rosto.sincronizar()
    if veto=="sem_saude": rosto._saude_em=float("-inf")
    corpo.companhia.processar(); agora[0]+=2; corpo.companhia.processar()
    assert not corpo.companhia.diagnostico()["ativa"] and not motores(esp)
    assert not corpo.companhia.autorizar_busca_obstaculos(rosto._sessao)
    rosto.encerrar()

@pytest.mark.parametrize("linha",[
    "HEALTH 1 8 112233445566 00000001 9 10 100 90 0 NENHUMA 0",
    "HEALTH 1 7 qualquer 00000001 9 10 100 90 0 NENHUMA 0",
    "HEALTH 1 7 112233445566 00000001 9 -1 100 90 0 NENHUMA 0",
    "HEALTH 1 7 112233445566 00000001 9 10 100 90 0 INVENTADO 0",
])
def test_receipt_de_saude_invalido_nao_vira_fato(linha):
    with pytest.raises(ValueError): interpretar_saude(linha,7)

def test_abertura_usb_nao_ativa_linhas_de_reset_do_esp(monkeypatch):
    import serial
    from mente_laylay.especialistas.rosto_oled_runtime import _abrir_serial
    aberturas=[]
    class Porta:
        def __init__(self,port=None,baudrate=115200,**kwargs):
            self.port=port; self.dtr=self.rts=True
            if port is not None: aberturas.append((self.dtr,self.rts))
        def open(self): aberturas.append((self.dtr,self.rts))
    monkeypatch.setattr(serial,"Serial",Porta)
    _abrir_serial("COM_TESTE")
    assert aberturas==[(False,False)],"abrir a porta com DTR/RTS padrão pode reiniciar o USB-JTAG"
