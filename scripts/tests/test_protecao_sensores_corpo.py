"""Receipts físicos simulados; owner USB, mente, cooperação e DEV reais."""
import time
import pytest
from scripts.tests.test_corpo_transporte_oled import EspCorpo
from scripts.tests.test_companhia_corporal import montar, ativar, emocao, motores
from mente_laylay.especialistas.percepcao_distancia import interpretar_linha_protecao
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.especialistas.capacidades import consultar_capacidade
from mente_laylay.integracao.dev_console_runtime import DevConsoleRuntime
from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime


class EspSensores(EspCorpo):
    def __init__(self):
        super().__init__()
        self.sessao = ""
        self.incidente = self.origem = 0
        self.fase = "PRONTA"
        self.consultas_reflexo = 0
        self.borda = 100
    def write(self, dados):
        p = dados.decode().split()
        if p[0] == "HELLO":
            self.sessao = p[2]
        if p[0] in {"DCAPS", "DIST", "GUARD", "MOTOR"}:
            self.enviados.append(dados.decode().strip())
            if p[0] == "DCAPS":
                r = f"DCAPS 1 {p[2]} SENSORES2"
            elif p[0] == "DIST":
                r = f"DIST 1 {p[2]} FRENTE 48 VALIDA 200 20 0 BORDA 49 VALIDA {self.borda} 40 0"
            elif p[0] == "MOTOR":
                self.origem = int(p[3]); self.incidente += 1
                self.fase = "RECUANDO"
                r = f"HAZARD 1 {self.sessao} {p[3]} {self.incidente} BORDA"
            else:
                if self.fase == "RECUANDO":
                    self.consultas_reflexo += 1
                    if self.consultas_reflexo >= 2:
                        self.fase = "BLOQUEADA"
                r = f"GUARD 1 {p[2]} {self.sessao} {self.incidente} {self.origem} NENHUM {self.fase} 130 100"
            self.rx.extend((r + "\n").encode())
            return len(dados)
        return super().write(dados)


def test_distancias_reais_no_owner_e_modelo_sem_conceder_movimento():
    estado, esp, rosto, corpo, _, _ = montar(esp=EspSensores())
    assert not motores(esp)
    diag = rosto.diagnostico()["sensores"]
    assert diag["suportado"] and diag["leituras"]["borda"]["mm"] == 100
    modelo = corpo.modelo_para_mente()
    assert modelo["percepcao_fisica"]["distancias"]["leituras"]["frente"]["mm"] == 200
    assert modelo["autoriza_execucao"] is False
    from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal
    assert ativar(corpo)["ok"]
    assert len(formatar_modelo_corporal(corpo.modelo_para_mente())) <= 3800
    rosto._sensores_em = time.monotonic() - 1
    modelo = corpo.modelo_para_mente()
    assert modelo["condicao"]["estado"] == "percepcao_expirada"
    assert modelo["percepcao_fisica"]["distancias"]["leituras"]["borda"]["mm"] is None
    rosto.encerrar()


def test_hazard_aguarda_reflexo_mas_nao_promove_movimento_original_a_sucesso():
    _, esp, rosto, corpo, _, _ = montar(esp=EspSensores())
    r = rosto.mover_corpo(100, 100, 50)
    assert not r["ok"] and r["interrompido_por_protecao"]
    assert not r["aplicacao_pwm_confirmada"] and r["parada_confirmada"]
    assert esp.consultas_reflexo >= 2
    assert len(motores(esp)) == 1
    assert not corpo.confirmar_receipt(r, "CORPO_MOVER")["ok"]
    rosto.encerrar()


def test_protecao_no_gesto_cooperativo_devolve_parcial_sem_revogar_companhia():
    estado, esp, rosto, corpo, quadro, _ = montar(esp=EspSensores())
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "triste")
    r = corpo.companhia.processar()
    assert not r["ok"] and r["interrompido_por_protecao"]
    assert len(motores(esp)) == 1
    assert corpo.companhia.diagnostico()["ativa"]
    assert corpo.experiencias.retrato()["historico_recente"][-1]["confirmado"] is False
    rosto.encerrar()


@pytest.mark.parametrize("correlacao", ["atual", "outra_sessao", "outra_sequencia"])
def test_recusa_de_motor_durante_busca_preserva_companhia_so_com_receipt_correlacionado(correlacao):
    class EspDisputa(EspSensores):
        def write(self, dados):
            p = dados.decode().split()
            if p[0] == "MOTOR":
                self.enviados.append(dados.decode().strip())
                # Episódio local já existe; o MOTOR recusado não o reinicia.
                self.incidente = 5
                self.origem = 0
                self.fase = "RECUANDO"
                sessao = "abcdef00" if correlacao == "outra_sessao" else self.sessao
                seq = str(int(p[3])+1) if correlacao == "outra_sequencia" else p[3]
                self.rx.extend(f"HAZARD 1 {sessao} {seq} 5 OBSTACULO\n".encode())
                return len(dados)
            return super().write(dados)
    estado, esp, rosto, corpo, quadro, _ = montar(esp=EspDisputa())
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "triste")
    r = corpo.companhia.processar()
    assert not r["ok"] and len(motores(esp)) == 1
    assert quadro.snapshot()["planos_recentes"][-1]["estado"] != "confirmado"
    assert corpo.companhia.diagnostico()["ativa"] is (correlacao == "atual")
    e = estado.obter_copia("mental", "experiencia_corporal", {})
    assert not e["confirmado"] and e["movimentos_confirmados"] == 0
    assert r.get("interrompido_por_protecao", False) is (correlacao == "atual")
    rosto.encerrar()


@pytest.mark.parametrize("linha", [
    "GUARD 1 7 outra 0 0 NENHUM PRONTA 130 100",
    "GUARD 1 8 01234567 0 0 NENHUM PRONTA 130 100",
    "GUARD 1 7 01234567 -1 0 NENHUM PRONTA 130 100",
    "GUARD 1 7 01234567 0 0 NENHUM PRONTA 30 100",
])
def test_protecao_sem_receipt_correlacionado_nao_publica_condicao(linha):
    with pytest.raises(ValueError): interpretar_linha_protecao(linha, 7, "01234567")


def test_pergunta_de_sensor_usa_disponibilidade_viva_e_nao_executa():
    _, esp, rosto, corpo, _, _ = montar(esp=EspSensores())
    disponibilidade = DisponibilidadeOperacionalRuntime(corpo_motor_getter=corpo.diagnostico)
    mapa = MapaHabilidadesRuntime(operacional_getter=disponibilidade.snapshot)
    resposta = mapa.responder_pergunta_capacidade("voce tem sensores de borda e obstaculos?")
    assert "13 cm" in resposta and "traseira" in resposta and not motores(esp)
    assert "indisponíveis no firmware" in resposta
    assert "SENSORES2" in consultar_capacidade("CORPO_MOVER")["percepcao_condicional"]
    rosto._sensores_suportados = False
    assert "Não tenho leitura" in mapa.responder_pergunta_capacidade("voce tem sensores de borda?")
    rosto.encerrar()


def test_dev_atualiza_medidas_sem_flood_e_preserva_allowlist():
    from scripts.tests.test_dev_corpo import dados_corpo
    dados = dados_corpo()
    dados["transporte"]["sensores"] = {"recente": True,
        "leituras": {"frente": {"estado": "VALIDA", "mm": 200}, "borda": {"estado": "VALIDA", "mm": 100}},
        "protecao": {"risco": "NENHUM", "fase": "PRONTA"}}
    dev = DevConsoleRuntime(); dev.configurar_corpo_getter(lambda: dados)
    s = dev.snapshot(); assert s["body"]["sensor_borda"] == "100 mm"
    dados["transporte"]["sensores"]["leituras"]["borda"]["mm"] = 101
    novo = dev.snapshot()
    assert novo["body"]["sensor_borda"] == "101 mm" and novo["sequence"] == s["sequence"]
    dados["transporte"]["sensores"]["protecao"]["risco"] = "BORDA"
    assert dev.snapshot()["sequence"] == s["sequence"] + 1


class EspPresenca(EspSensores):
    def __init__(self):
        super().__init__()
        self.vigia = False
        self.reacao = "PAVOR"
        self.borda = 150
    def write(self,dados):
        p=dados.decode().split()
        if p[0]=="PCAPS":
            self.enviados.append(dados.decode().strip())
            self.rx.extend(f"PCAPS 1 {p[2]} VIGIA1\n".encode()); return len(dados)
        if p[0]=="SENTRY":
            self.vigia=p[4]=="1"; self.enviados.append(dados.decode().strip())
            self.rx.extend(f"SENTRYACK 1 {p[2]} {p[3]} {p[4]}\n".encode()); return len(dados)
        if p[0]=="GUARD":
            self.enviados.append(dados.decode().strip())
            self.rx.extend(f"GUARD 1 {p[2]} {self.sessao} 0 0 BORDA PRONTA 130 100 {self.reacao} 0 {int(self.vigia)}\n".encode())
            return len(dados)
        return super().write(dados)


def test_alerta_parado_chega_a_mente_sem_motor_e_sem_mudar_emocao_conversacional():
    estado,esp,rosto,corpo,_,_=montar(esp=EspPresenca())
    assert not motores(esp) and not esp.vigia
    modelo=corpo.modelo_para_mente()
    assert modelo["condicao"]["reacao_expressiva"]=="pavor"
    assert modelo["percepcao_fisica"]["distancias"]["protecao"]["risco"]=="BORDA"
    assert estado.retrato_dominio("conversacional")=={}
    assert not modelo["autoriza_execucao"]
    rosto.encerrar()


def test_busca_requer_owner_da_concessao_vigente_e_revogacao_desarma():
    _,esp,rosto,corpo,_,_=montar(esp=EspPresenca())
    rosto.busca_obstaculos_getter=corpo.companhia.autorizar_busca_obstaculos
    rosto.companhia_getter=lambda:{"ativa":True} # Diagnóstico/contexto não autoriza.
    assert rosto.sincronizar() and not esp.vigia
    assert ativar(corpo)["ok"]
    assert corpo.companhia.autorizar_busca_obstaculos(rosto._sessao)
    assert not corpo.companhia.autorizar_busca_obstaculos("sessao_estrangeira")
    assert rosto.sincronizar() and esp.vigia
    corpo.companhia.prioridade_interacao_getter=lambda:True
    assert rosto.sincronizar() and not esp.vigia
    corpo.companhia.prioridade_interacao_getter=lambda:False
    assert corpo.companhia.diagnostico()["ativa"]
    assert rosto.sincronizar() and esp.vigia # Mesma concessão volta após a prioridade.
    corpo.companhia.revogar("teste_parar")
    assert rosto.sincronizar() and not esp.vigia
    rosto.encerrar()


@pytest.mark.parametrize("extra",["PAVOR 5 1","DESESPERO 1 1","PAVOR 1 2"])
def test_alerta_malformado_nao_entra_no_retrato(extra):
    with pytest.raises(ValueError):
        interpretar_linha_protecao("GUARD 1 7 01234567 0 0 BORDA PRONTA 130 100 "+extra,7,"01234567")


@pytest.mark.parametrize("fase,ativo",[("RECUO_MEDROSO",True),("ESPERA_MEDROSA",True),("ESPERA_BUSCA",False)])
def test_linguagem_corporal_da_protecao_preserva_receipt_e_concessao(fase,ativo):
    r=interpretar_linha_protecao(f"GUARD 1 7 01234567 3 0 BORDA {fase} 130 100 PAVOR 0 1",7,"01234567")
    assert r["fase"]==fase and r["reflexo_ativo"] is ativo
    assert r["vigia_ativa"] and not r["autoriza_execucao"]
    assert not r["rotacao_medida"]


def test_dev_mostra_autorizacao_confirmada_da_placa_sem_confundir_companhia_ativa():
    from scripts.tests.test_dev_corpo import dados_corpo
    dados=dados_corpo()
    dados["transporte"]["sensores"]={"recente":True,"protecao":{"vigia_ativa":False}}
    dev=DevConsoleRuntime(); dev.configurar_corpo_getter(lambda:dados)
    assert not dev.snapshot()["body"]["vigia_sensores_ativa"]
    dados["transporte"]["sensores"]["protecao"]["vigia_ativa"]=True
    assert dev.snapshot()["body"]["vigia_sensores_ativa"]
    dados["transporte"]["sensores"]["recente"]=False
    assert not dev.snapshot()["body"]["vigia_sensores_ativa"]
