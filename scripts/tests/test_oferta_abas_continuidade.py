"""Oferta operacional deve chegar à confirmação canônica antes da conversa."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest
from tests.instalacao_privada import isolar_base_do_codigo

from mente_laylay.autonomia.porteiro_chrome import PorteiroChromeRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime
from mente_laylay.memoria_mental.resultado_acao import ResultadoTratamentoOperacional
from mente_laylay.memoria_mental.aprendizado_rotina_musica import classificar_confirmacao_local


def _oferta(*, falar_resultado=None):
    relogio = [10_000.0]
    estado = EstadoCompartilhadoRuntime(mental={})
    pendencias = PendenciaAcaoRuntime(
        estado_getter=lambda: estado.mental,
        estado_atualizar=lambda fn: estado.atualizar("mental", fn),
        agora=lambda: relogio[0], log=lambda *_: None,
    )
    falas, envios = [], []
    def falar(texto, *_):
        falas.append(texto)
        return falar_resultado
    runtime = PorteiroChromeRuntime(
        abas_sugeridas=[], obter_ram_percent=lambda: 91,
        listar_abas=lambda **_: [
            {"url": "https://ativa", "title": "Ativa"},
            {"url": "https://antiga-1", "title": "YouTube"},
            {"url": "https://antiga-2", "title": "WhatsApp"},
        ],
        obter_estado_chrome=lambda: {"aba_url_atual": "https://ativa"},
        falar=falar, enviar_fechamento=lambda url: envios.append(url) or True,
        clock=lambda: relogio[0], log=lambda *_: None,
    )
    # Atribuição permite instalar o RED na base sem falhar por assinatura nova.
    runtime.pendencias = pendencias
    return runtime, pendencias, relogio, falas, envios


def test_oferta_falada_registra_pendencia_no_estado_compartilhado():
    runtime, pendencias, _, _, envios = _oferta()
    assert runtime.executar_ciclo() is True
    item = pendencias.obter()
    assert item is not None, "primeira fronteira: oferta falada sem pendência canônica"
    assert item["origem"] == "porteiro_chrome"
    assert item["dominio"] == "navegador"
    assert item["acao"] == "fechar_abas_paradas"
    assert envios == [], "oferta não autoriza efeito"


def test_oferta_nao_substitui_pendencia_de_outro_dominio():
    runtime, pendencias, _, falas, _ = _oferta()
    anterior = pendencias.registrar(origem="agenda", acao="agendar", pergunta="Agendo?")
    assert runtime.executar_ciclo() is False
    assert pendencias.obter()["id"] == anterior["id"]
    assert falas == []
    assert runtime.abas_sugeridas == []


def test_oferta_recusada_pela_voz_nao_deixa_autorizacao_pendente():
    runtime, pendencias, _, _, _ = _oferta(falar_resultado=False)
    assert runtime.executar_ciclo() is False
    assert pendencias.obter() is None
    assert runtime.abas_sugeridas == []


def test_veto_soberano_impede_confirmacao_sem_consumir_oferta():
    runtime, pendencias, _, _, envios = _oferta()
    assert runtime.executar_ciclo()
    item = pendencias.obter()
    assert runtime.processar_confirmacao("pode ser", permitir_execucao=False,
        executar=lambda *_: pytest.fail("veto não pode executar")) is False
    assert pendencias.obter()["id"] == item["id"]
    assert envios == []


def test_excecao_do_executor_conclui_com_falha_observavel():
    runtime, pendencias, _, falas, _ = _oferta()
    assert runtime.executar_ciclo()
    def falhar(*_):
        raise RuntimeError("executor indisponível")
    assert runtime.processar_confirmacao("pode ser", executar=falhar)
    assert pendencias.obter() is None
    assert "Não consegui confirmar" in falas[-1]


def test_lista_simples_sem_oferta_nao_autoriza_confirmacao():
    runtime, pendencias, _, _, envios = _oferta()
    runtime.abas_sugeridas[:] = ["https://antiga"]
    assert runtime.processar_confirmacao("sim", executar=lambda *_: pytest.fail("sem oferta")) is False
    assert pendencias.obter() is None
    assert envios == []


@pytest.mark.parametrize("texto", ["pode sim abrir o Chrome", "pode abrir", "quero sim tocar rock", "toca", "pode falar"])
def test_outro_pedido_operacional_nao_confirma_fechamento(texto):
    runtime, pendencias, _, _, _ = _oferta()
    assert runtime.executar_ciclo()
    item = pendencias.obter()
    assert runtime.processar_confirmacao(texto, executar=lambda *_: pytest.fail("outro pedido fechou abas")) is False
    assert pendencias.obter()["id"] == item["id"]


@pytest.mark.parametrize("dominio,acao", [("navegador", "fechar_abas_paradas"), ("arquivos", "confirmar_exclusao")])
def test_aceite_generico_tipado_protege_pendencias_de_dominios_distintos(dominio, acao):
    _, pendencias, _, _, _ = _oferta()
    item = pendencias.registrar(origem=dominio, dominio=dominio, acao=acao, pergunta="Posso continuar?")
    outro = pendencias.resolver("quero sim tocar rock", somente_aceite_generico=True)
    assert outro["tratado"] is False
    assert pendencias.obter()["id"] == item["id"]
    assert pendencias.resolver("pode ser", somente_aceite_generico=True)["status"] == "aceitar"


@pytest.mark.parametrize("texto", ["abre", "toca", "pode falar", "quero sim tocar rock"])
def test_modo_generico_preserva_compatibilidade_dos_consumidores_existentes(texto):
    assert classificar_confirmacao_local(texto) is True
    assert classificar_confirmacao_local(texto, somente_aceite_generico=True) is None


def test_aceite_nao_e_transferido_para_pendencia_concorrente(monkeypatch):
    runtime, pendencias, _, falas, _ = _oferta()
    assert runtime.executar_ciclo()
    original = pendencias.resolver
    def trocar(texto, **kw):
        pendencias.concluir(pendencias.obter()["id"], "cancelada")
        pendencias.registrar(origem="agenda", acao="agendar", pergunta="Agendo?")
        return original(texto, **kw)
    monkeypatch.setattr(pendencias, "resolver", trocar)
    assert runtime.processar_confirmacao("sim", executar=lambda *_: pytest.fail("troca não autoriza"))
    assert pendencias.obter()["origem"] == "agenda"
    assert "mudando" in falas[-1]


def test_bool_legado_sem_receipt_nao_conclui_oferta_como_executada():
    runtime, pendencias, _, _, _ = _oferta()
    assert runtime.executar_ciclo()
    assert runtime.processar_confirmacao("sim", executar=lambda *_: ResultadoTratamentoOperacional(
        tratado=False, executou=True, confirmado=None, legado=True))
    assert pendencias._estado_getter()["ultima_pendencia_acao"]["status"] == "falha_execucao"


@pytest.fixture(scope="module")
def composicao_oferta(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("oferta_abas")
    codigo = textwrap.dedent(r'''
        import importlib.abc, importlib.machinery, importlib.util
        import json, os, sys, time
        from copy import deepcopy
        from dataclasses import asdict, is_dataclass
        from pathlib import Path
        from types import ModuleType
        perfil = Path(os.environ["LAYLAY_SONDA_SQLITE"])
        raiz = Path.cwd()
        apps = ModuleType('AppOpener')
        apps.open = apps.close = lambda *a, **k: False
        apps.give_appnames = lambda *a, **k: {}
        sys.modules['AppOpener'] = apps
        fonte = (raiz/'laylay.py').read_bytes()
        bloco = b'PASTA_MEMORIA = os.path.join(_base_dir, "memoria")'
        assert fonte.count(bloco)==1
        fonte = fonte.replace(bloco,('PASTA_MEMORIA = '+repr(str(perfil/'raiz'))).encode())
        class Loader(importlib.machinery.SourceFileLoader):
            def get_code(self,nome):return compile(fonte,self.path,'exec')
        class Finder(importlib.abc.MetaPathFinder):
            def find_spec(self,nome,path=None,target=None):
                if nome=='laylay':
                    return importlib.util.spec_from_loader(nome,Loader(nome,str(raiz/'laylay.py')))
        sys.meta_path.insert(0,Finder())
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        root = preparar_instalacao_isolada(perfil/'simulada')
        root._voz_runtime.definir_modo_silencioso(True,origem='teste_oferta_abas')
        root._voz_runtime.falar = lambda *a, **k: False
        root.salvar_memoria = lambda *a, **kw: None
        root._registrar_autocorrecao_virtual = lambda *a, **kw: None
        root._composicao_turno_runtime._servicos["_coleta_entradas_neurais"] = None
        estado = root._estado_compartilhado_runtime
        base = estado.snapshot()
        porteiro = root._porteiro_runtime
        falas, enviados = [], []
        root.falar_com_lipsync = lambda texto, *a, **kw: falas.append(texto)
        porteiro.obter_ram_percent = lambda: 91
        porteiro.listar_abas = lambda **kw: [
            {"url": "https://ativa", "title": "Ativa"},
            {"url": "https://antiga-1", "title": "YouTube"},
            {"url": "https://antiga-2", "title": "WhatsApp"}]
        porteiro.obter_estado_chrome = lambda: {"aba_url_atual": "https://ativa"}
        saida = {}
        casos = [(t, t) for t in ("pode ser", "sim", "pode fechar", "pode sim", "pode fechar as abas paradas", "não", "deixa para depois", "mostra minhas playlists", "se eu disser pode fechar", "como eu faço para fechar?")]
        casos += [(nome, "pode ser") for nome in ("falha_parcial", "expirada", "alvos_alterados", "sem_oferta", "confirmacao_apos_intermediario")]
        for nome, texto in casos:
            for dominio in ("mental", "conversacional", "memoria_conversa"):
                estado.substituir(dominio, deepcopy(base[dominio]))
            estado.atualizar("mental", lambda atual: {**atual, "pendencia_acao_canonica": {}})
            porteiro.abas_sugeridas.clear()
            porteiro.ultima_sugestao_ts = 0
            falas.clear(); enviados.clear()
            porteiro.enviar_fechamento = lambda url: enviados.append(url) or True
            ofereceu = porteiro.executar_ciclo()
            pendencia = root._pendencia_acao_runtime.obter()
            if nome == "falha_parcial":
                porteiro.enviar_fechamento = lambda url: enviados.append(url) or url != "https://antiga-2"
            elif nome == "expirada":
                estado.atualizar("mental", lambda atual: {**atual, "pendencia_acao_canonica": {**dict(atual["pendencia_acao_canonica"]), "expira_em": time.time() - 1}})
            elif nome == "alvos_alterados":
                porteiro.abas_sugeridas[:] = ["https://outro-alvo"]
            elif nome == "sem_oferta":
                root._pendencia_acao_runtime.concluir(pendencia["id"], "cancelada")
            elif nome == "confirmacao_apos_intermediario":
                root._iniciar_planejamento_turno("mostra minhas playlists", origem="teste_oferta_abas")
                root._processar_comandos_prioritarios("mostra minhas playlists")
            turno = root._iniciar_planejamento_turno(texto, origem="teste_oferta_abas")
            tratado = root._processar_comandos_prioritarios(texto)
            saida[nome] = {"ofereceu": ofereceu, "pendencia": pendencia,
                "tratado": tratado, "envios": list(enviados), "falas": list(falas),
                "depois": root._pendencia_acao_runtime.obter(),
                "ultimo_resultado": estado.snapshot()["mental"].get("ultima_acao_contrato"),
                "abas_restantes": list(porteiro.abas_sugeridas),
                "ultima_pendencia": estado.snapshot()["mental"].get("ultima_pendencia_acao"),
                "turno": turno}
        def serializar_diagnostico(valor):
            if is_dataclass(valor):return asdict(valor)
            raise TypeError('Tipo não previsto no diagnóstico: '+type(valor).__name__)
        sys.__stdout__.write("OFERTA_ABAS " + json.dumps(saida, ensure_ascii=False,
            default=serializar_diagnostico) + "\n")
    ''')
    codigo = isolar_base_do_codigo(codigo,variavel_fonte='fonte')
    processo = subprocess.run([sys.executable, "-B", "-c", codigo],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_MASCOT_ENABLED="0",
            LAYLAY_AVATAR_ATIVO="0", LAYLAY_SONDA_SQLITE=str(pasta)),
        capture_output=True, text=True, encoding="utf-8", timeout=120)
    (pasta / "composicao.log").write_text(processo.stdout + processo.stderr, encoding="utf-8")
    assert processo.returncode == 0, processo.stderr[-5000:] + processo.stdout[-3000:]
    linhas = [x.removeprefix("OFERTA_ABAS ") for x in processo.stdout.splitlines() if x.startswith("OFERTA_ABAS ")]
    assert linhas, processo.stdout[-4000:]
    return json.loads(linhas[-1])


@pytest.mark.parametrize("texto", ["pode ser", "sim", "pode fechar", "pode sim", "pode fechar as abas paradas"])
def test_confirmacao_da_oferta_instalada_executa_alvos_oferecidos(composicao_oferta, texto):
    caso = composicao_oferta[texto]
    assert caso["pendencia"] is not None, "primeira fronteira: publicação da oferta"
    assert caso["tratado"] is True
    assert caso["envios"] == ["https://antiga-1", "https://antiga-2"]
    assert caso["depois"] is None
    assert caso["ultima_pendencia"]["status"] == "executada"
    assert caso["ultimo_resultado"]["intent"] == "CLOSE_IDLE_TABS"
    assert caso["ultimo_resultado"]["confirmado"] is True
    assert "Limpei 2 abas" in caso["falas"][-1]


@pytest.mark.parametrize("texto", ["não", "deixa para depois"])
def test_recusa_da_oferta_instalada_nao_executa(composicao_oferta, texto):
    caso = composicao_oferta[texto]
    assert caso["pendencia"] is not None
    assert caso["tratado"] is True
    assert caso["envios"] == []
    assert caso["depois"] is None
    assert caso["ultima_pendencia"]["status"] == "recusada"


@pytest.mark.parametrize("texto", ["mostra minhas playlists", "se eu disser pode fechar", "como eu faço para fechar?"])
def test_novo_pedido_ou_discussao_nao_confirma_oferta(composicao_oferta, texto):
    caso = composicao_oferta[texto]
    assert caso["pendencia"] is not None
    assert caso["envios"] == []
    assert caso["depois"] is not None, json.dumps({k: caso[k] for k in ("ultima_pendencia", "ultimo_resultado", "falas")}, ensure_ascii=False)
    assert caso["depois"]["id"] == caso["pendencia"]["id"]


def test_falha_parcial_instalada_preserva_abas_e_publica_falha(composicao_oferta):
    caso = composicao_oferta["falha_parcial"]
    assert caso["tratado"] is True
    assert caso["envios"] == ["https://antiga-1", "https://antiga-2"]
    assert caso["abas_restantes"] == ["https://antiga-2"]
    assert caso["ultimo_resultado"]["confirmado"] is False
    assert caso["ultima_pendencia"]["status"] == "falha_execucao"
    assert "não respondeu" in caso["falas"][-1]
    assert not any("Pronto. Limpei" in fala for fala in caso["falas"])


@pytest.mark.parametrize("caso", ["expirada", "alvos_alterados", "sem_oferta"])
def test_confirmacao_sem_oferta_valida_nao_fecha_abas(composicao_oferta, caso):
    assert composicao_oferta[caso]["envios"] == []
    assert composicao_oferta[caso]["depois"] is None


def test_confirmacao_apos_comando_intermediario_preserva_mesmo_alvo(composicao_oferta):
    caso = composicao_oferta["confirmacao_apos_intermediario"]
    assert caso["tratado"] is True
    assert caso["envios"] == ["https://antiga-1", "https://antiga-2"]
    assert caso["ultima_pendencia"]["id"] == caso["pendencia"]["id"]
    assert caso["ultima_pendencia"]["status"] == "executada"
