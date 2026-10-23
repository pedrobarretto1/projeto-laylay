"""Só hardware é simulado; parser, owner USB, mente, autoridade e DEV são reais."""
import time
import pytest
from scripts.tests.test_corpo_transporte_oled import EspCorpo
from scripts.tests.test_companhia_corporal import montar, ativar, emocao, motores
from scripts.tests.test_corpo_motor import _caminho
from mente_laylay.especialistas.percepcao_inercial import interpretar_imu
from mente_laylay.cognicao.gramatica_corpo import detectar_intencao_corpo
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal


class EspImu(EspCorpo):
    def __init__(self, *, resultado="ALVO", correlacao="atual"):
        super().__init__()
        self.manuseio="ESTAVEL"
        self.resultado,self.correlacao=resultado,correlacao
    def write(self,dados):
        p=dados.decode().split()
        if p[0] in {"ICAPS", "IMU", "TURN", "LCAPS"}:
            self.enviados.append(dados.decode().strip())
            if p[0]=="ICAPS":r=f"ICAPS 1 {p[2]} IMU1"
            elif p[0]=="LCAPS":r=f"LCAPS 1 {p[2]} LONGO1"
            elif p[0]=="IMU":r=f"IMU 1 {p[2]} 104 PRONTA 5 1 100 -200 300 0 1000 {self.manuseio}"
            else:
                self.aplicou_motor.set()
                seq=str(int(p[3])+1) if self.correlacao=="outra_sequencia" else p[3]
                sessao="abcdef00" if self.correlacao=="outra_sessao" else p[2]
                r=f"TURNACK 1 {p[2]} {p[3]} {p[4]}\nTURNPWM 1 {p[2]} {p[3]}"
                if self.resultado!="AUSENTE":
                    medido=round(int(p[4])*100) if self.resultado=="ALVO" else 0
                    r+=f"\nTURNEND 1 {sessao} {seq} {self.resultado} {medido}"
            self.rx.extend((r+"\n").encode());return len(dados)
        return super().write(dados)


def test_parser_nao_promove_calibracao_ou_idade_invalida_a_medida():
    r=interpretar_imu("IMU 1 4 104 PRONTA 20 1 1200 -300 9000 10 1000 ESTAVEL",4)
    assert r["roll_graus"]==12 and r["yaw_relativo_graus"]==90
    assert r["autoriza_execucao"] is False and r["prova_deslocamento"] is False
    for texto in ["IMU 1 4 104 PRONTA 76 1 0 0 0 0 1000 ESTAVEL",
                  "IMU 1 4 104 PRONTA 10 0 0 0 0 0 1000 ESTAVEL",
                  "IMU 1 5 104 PRONTA 10 1 0 0 0 0 1000 ESTAVEL"]:
        with pytest.raises(ValueError):interpretar_imu(texto,4)
    r=interpretar_imu("IMU 1 4 104 ERRO_I2C 20 1 1200 -300 9000 10 1000 DESCONHECIDO",4)
    assert r["yaw_relativo_graus"] is None
    r=interpretar_imu("IMU 1 4 104 PRONTA 20 1 0 0 0 0 1000 ESTAVEL 152",4)
    assert r["modelo"]=="ICM20689_compativel"


def test_mpu_chega_a_mente_sem_criar_autorizacao_ou_localizacao():
    estado,esp,rosto,corpo,_,_=montar(esp=EspImu())
    try:
        modelo=corpo.modelo_para_mente()
        assert modelo["percepcao_fisica"]["inercial"]["roll_graus"]==1
        assert modelo["percepcao_fisica"]["deslocamento"]=="nao_medido"
        assert modelo["autoriza_execucao"] is False
        prompt=formatar_modelo_corporal(modelo)
        assert '"inercial"' in prompt and "possível levantamento é hipótese" in prompt
        assert not motores(esp)
        rosto._imu_em=time.monotonic()-2
        modelo=corpo.modelo_para_mente()
        assert not modelo["percepcao_fisica"]["inercial"]["recente"]
        assert modelo["condicao"]["estado"]=="manuseio_ou_calibracao"
    finally:rosto.encerrar()


def test_manuseio_suspende_companhia_sem_revogar_e_retorna_quando_estavel():
    estado,esp,rosto,corpo,quadro,_=montar(esp=EspImu())
    try:
        assert ativar(corpo)["ok"]
        esp.manuseio="POSSIVEL_LEVANTAMENTO";rosto.sincronizar()
        emocao(estado,rosto,"alegre")
        r=corpo.companhia.processar()
        assert r["motivo"]=="manuseio_ou_calibracao" and not motores(esp)
        assert corpo.companhia.diagnostico()["ativa"]
        esp.manuseio="ESTAVEL";rosto.sincronizar()
        r=corpo.companhia.processar()
        assert r.get("motivo")!="manuseio_ou_calibracao"
        assert corpo.companhia.diagnostico()["ativa"]
    finally:rosto.encerrar()


@pytest.mark.parametrize("texto,direcao,angulo",[
    ("gire 90 graus para a esquerda","esquerda",90),
    ("pode virar 180 graus para a direita?","direita",180),
    ("gira 360 graus a esquerda","esquerda",360),
])
def test_pedido_natural_de_giro_tem_medida_e_autorizacao_canonica(texto,direcao,angulo):
    pedido=detectar_intencao_corpo(texto)
    assert pedido and pedido["params"]["angulo_graus"]==angulo
    esp=EspImu()
    estado,_,rosto,corpo,_,_=montar(esp=esp)
    try:
        caminho=_caminho(ponte=rosto,texto=texto)
        assert executar_intencao(pedido,texto,caminho.ctx)
        assert caminho.receipts[-1].contexto["receipt_corpo"]["prova_rotacao"]
        # A redação antiga arredondava e apagava o sinal. O contrato comum
        # precisa preservar a leitura do receipt e sua ressalva, sem congelar
        # uma frase particular do executor corporal.
        receipt = caminho.receipts[-1]
        assert len(receipt.medicoes) == 1
        medida = receipt.medicoes[0]
        assert medida.ocorrencia_id == receipt.id_solicitacao
        assert medida.valor == receipt.contexto["receipt_corpo"]["rotacao_medida_graus"]
        assert medida.valor == (angulo if direcao == "esquerda" else -angulo)
        assert medida.unidade == "graus" and medida.metodo == "imu_relativa_turnend_e_sack"
        assert str(medida.valor) in caminho.falas[-1][0]
        assert medida.limite_observacao in caminho.falas[-1][0]
        assert len([c for c in esp.enviados if c.startswith("TURN ")])==1
        assert not motores(esp)
        assert caminho.estado.mental["corpo_motor"]["prova_rotacao"]
        assert caminho.corpo.experiencias.retrato()["historico_recente"][-1]["prova_rotacao"]
    finally:rosto.encerrar()


@pytest.mark.parametrize("resultado",["SEM_ROTACAO","IMU_OU_SESSAO","PROTECAO","TEMPO_LIMITE"])
def test_pwm_e_parada_nao_substituem_angulo_confirmado(resultado):
    _,_,rosto,_,_,_=montar(esp=EspImu(resultado=resultado))
    try:
        r=rosto.girar_corpo(90)
        assert not r["ok"] and not r["prova_rotacao"]
        assert r["aplicacao_pwm_confirmada"] and r["parada_confirmada"]
    finally:rosto.encerrar()


@pytest.mark.parametrize("texto",["não gire 90 graus para a esquerda","você consegue girar 90 graus para a esquerda?"])
def test_mencao_de_giro_nao_aciona_corpo(texto):
    assert detectar_intencao_corpo(texto) is None


def test_proposta_nao_troca_angulo_nem_adiciona_angulo_a_pulso():
    for texto,params in [("gire 90 graus para a esquerda",{"direcao":"esquerda","pwm":160,"duracao_ms":5000,"angulo_graus":180}),
                         ("vire para a esquerda",{"direcao":"esquerda","pwm":255,"duracao_ms":250,"angulo_graus":90})]:
        caminho=_caminho(texto=texto)
        assert not executar_intencao({"intent":"CORPO_MOVER","params":params},texto,caminho.ctx)
        assert not caminho.ponte.chamadas


def test_capacidade_inercial_depende_da_leitura_viva_e_nao_move():
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.especialistas.capacidades import consultar_capacidade
    _,esp,rosto,corpo,_,_=montar(esp=EspImu())
    try:
        disponibilidade=DisponibilidadeOperacionalRuntime(corpo_motor_getter=corpo.diagnostico)
        mapa=MapaHabilidadesRuntime(operacional_getter=disponibilidade.snapshot)
        r=mapa.responder_pergunta_capacidade("você tem giroscópio?")
        assert "leitura recente" in r and "Não meço posição" in r
        assert "TURNEND" in consultar_capacidade("CORPO_MOVER")["evidencia_confirmacao"]
        rosto._imu_em=time.monotonic()-2
        assert "indisponível" in mapa.responder_pergunta_capacidade("você tem giroscópio?")
        assert not motores(esp) and not any(s.startswith("TURN ") for s in esp.enviados)
    finally:rosto.encerrar()


def test_transicao_inercial_e_registrada_uma_vez_sem_inventar_movimento():
    _,esp,rosto,corpo,_,_=montar(esp=EspImu())
    try:
        corpo.experiencias.observar_sensores(rosto.diagnostico(),perfil="bancada")
        esp.manuseio="INCLINADA";rosto.sincronizar()
        for _ in range(3):corpo.experiencias.observar_sensores(rosto.diagnostico(),perfil="bancada")
        h=corpo.experiencias.retrato()["historico_recente"]
        assert len(h)==1 and h[-1]["resultado"]=="inclinada"
        assert not h[-1]["confirmado"] and not h[-1]["prova_deslocamento"]
        assert corpo.estado.obter_copia("mental","historico_corporal",[])[-1]["autoriza_execucao"] is False
    finally:rosto.encerrar()


@pytest.mark.parametrize("correlacao",["outra_sessao","outra_sequencia"])
def test_giro_nao_empresta_resultado_de_outra_ocorrencia(correlacao):
    _,esp,rosto,_,_,_=montar(esp=EspImu(correlacao=correlacao))
    try:
        r=rosto.girar_corpo(90)
        assert not r["ok"] and not r["prova_rotacao"]
        assert r["rotacao_medida_graus"] is None
        assert len([c for c in esp.enviados if c.startswith("TURN ")])==1
        assert r["parada_confirmada"]
    finally:rosto.encerrar()


def test_dev_inercial_atualiza_sem_inundar_console_e_apenas_na_opcao_corpo(monkeypatch):
    from scripts.tests.test_dev_corpo import dados_corpo
    from mente_laylay.integracao.dev_console_runtime import DevConsoleRuntime
    from cliente.terminal_2.desenvolvedor import PaginaDesenvolvedor
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont
    from cliente.terminal_laylay_2 import carregar_fontes_interface
    monkeypatch.setenv("QT_QPA_PLATFORM","offscreen")
    app=QApplication.instance() or QApplication([])
    fonte_anterior=app.font()
    app.setFont(QFont(carregar_fontes_interface(),10))
    dados=dados_corpo()
    dados["transporte"]["imu"]={"suportado":True,"recente":True,"estado":"PRONTA",
                                 "manuseio":"INCLINADA","roll_graus":20,"pitch_graus":-5,"yaw_relativo_graus":30}
    dev=DevConsoleRuntime();dev.configurar_corpo_getter(lambda:dados)
    s=dev.snapshot();pagina=PaginaDesenvolvedor();pagina.definir_conectada(True)
    pagina.aplicar_corpo(s["body"]);pagina.resize(1500,900);pagina.show();app.processEvents()
    assert pagina.card_corpo.isHidden()
    pagina.botoes_categoria["CORPO"].click();app.processEvents()
    assert "MPU: PRONTA" in pagina.corpo_detalhes.text() and "INCLINADA" in pagina.corpo_detalhes.text()
    dados["transporte"]["imu"]["roll_graus"]=21
    assert dev.snapshot()["sequence"]==s["sequence"]
    pagina.grab().save("artifacts/rosto_oled/imu_manuseio/dev_imu.png")
    pagina.close()
    app.setFont(fonte_anterior)


def test_sensor_disponivel_nao_afirma_motor_disponivel_no_perfil_isolado():
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    esp=EspImu();esp.motor=False
    _,_,rosto,corpo,_,_=montar(esp=esp)
    try:
        d=DisponibilidadeOperacionalRuntime(corpo_motor_getter=corpo.diagnostico)
        mapa=MapaHabilidadesRuntime(operacional_getter=d.snapshot)
        resposta=mapa.responder_pergunta_capacidade("você tem acelerômetro?")
        assert "leitura recente" in resposta and "não posso executar giros agora" in resposta
        assert not rosto.girar_corpo(90)["ok"]
    finally:rosto.encerrar()


def test_manuseio_interrompe_gesto_cooperativo_sem_confirmar_tudo_ou_revogar_sessao():
    class EspNoColo(EspImu):
        def write(self,dados):
            p=dados.decode().split()
            n=super().write(dados)
            if p[0]=="MOTOR":
                self.manuseio="INCLINADA"
                self.rx.extend(f"HAZARD 1 {p[2]} {p[3]} 0 MANUSEIO\n".encode())
            return n
    estado,esp,rosto,corpo,quadro,_=montar(esp=EspNoColo())
    try:
        assert ativar(corpo)["ok"]
        emocao(estado,rosto,"alegre")
        r=corpo.companhia.processar()
        assert not r["ok"] and r["interrompido_por_protecao"]
        assert r["risco_detectado"]=="MANUSEIO"
        assert corpo.companhia.diagnostico()["ativa"]
        assert quadro.snapshot()["planos_recentes"][-1]["estado"]!="confirmado"
        assert corpo.experiencias.retrato()["historico_recente"][-1]["confirmado"] is False
        assert len(motores(esp))==1
    finally:rosto.encerrar()
