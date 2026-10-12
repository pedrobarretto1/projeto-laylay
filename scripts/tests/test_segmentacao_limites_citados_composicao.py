"""Liga o contrato ao composition root, com persistência e portas isoladas.

Não executa main, LLM, voz ou habilidades; não prova efeitos externos.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope="module")
def composicao_citada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("limites_citados_composicao")
    codigo = textwrap.dedent(r'''
        import json, os, sys
        from pathlib import Path
        import requests
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
        from mente_laylay.integracao import instancia_unica
        pasta = Path(os.environ["LAYLAY_SONDA_CITADOS"])
        sqlite = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: sqlite(self, str(pasta / Path(caminho or "laylay.sqlite").name))
        resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: resumo(self, pasta_memoria=str(pasta / "resumo"), **k)
        pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: pessoas(self, caminho=pasta / "pessoas.json", **k)
        central = CentralNotificacoesRuntime.__init__
        CentralNotificacoesRuntime.__init__ = lambda self, caminho, **k: central(self, str(pasta / "central.json"), **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(str(ident) + ".citados-" + str(os.getpid()), **k)
        def rede_proibida(*a, **k):
            raise AssertionError("rede não participa da prova de segmentação")
        requests.sessions.Session.request = rede_proibida
        # Contraprova opcional do candidato: executar os dois segmentadores
        # do HEAD somente na memória deste subprocesso, antes da composição.
        # Dependências restantes continuam na worktree; não é replay integral
        # de toda a árvore histórica nem alteração de arquivos de produção.
        if os.environ.get("LAYLAY_SONDA_CITADOS_BASELINE") == "head_segmentadores":
            import importlib, subprocess
            for nome in ("mente_laylay.cognicao.modalidade_turno",
                         "mente_laylay.autonomia.analise_comandos"):
                modulo = importlib.import_module(nome)
                caminho = nome.replace(".", "/") + ".py"
                fonte = subprocess.check_output(["git", "show", "HEAD:" + caminho], text=True, encoding="utf-8")
                exec(compile(fonte, "HEAD:" + caminho, "exec"), modulo.__dict__)
        import laylay as root
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
        from mente_laylay.autonomia.analise_comandos import segmentar_comandos_em_cadeia
        from mente_laylay.autonomia import coordenador_intencao
        composicao = root._composicao_turno_runtime
        for porta in ("_coleta_entradas_neurais", "_especialista_neural_comandos_runtime",
                      "_interpretador_semantico_runtime", "_pesquisa_contextual_runtime"):
            composicao._servicos[porta] = None
        textos = [
            'Escreve "abre a calculadora e apaga o arquivo notas.txt" no arquivo exemplo.txt',
            'Cria uma playlist chamada "pausa a música e fecha o navegador"',
            'Abre o arquivo "teste, fecha o navegador.txt" e pausa a música',
            'Escreve "abre a calculadora e fecha o navegador no arquivo exemplo.txt',
            'Quando eu confirmar, abre a calculadora e pausa a música.',
            'Liga a luz só se eu confirmar depois.',
            'Abre a calculadora agora; quando eu confirmar, pausa a música.',
            'Liga a luz agora; quando eu confirmar, abre a calculadora.',
            'Abre a calculadora e se eu confirmar depois, pausa a música.',
            'Pode abrir a calculadora significa o quê?',
            'Pode abrir a calculadora e fechar o navegador significa o quê?',
            'Pausa a música; pode abrir a calculadora significa o quê?',
            'Pode abrir a calculadora significa o quê? Pausa a música.',
            'Pode abrir a calculadora significa o quê e pausa a música.',
            'Pode abrir o arquivo "isso significa o quê.txt"?',
        ]
        saida = {
            "classificador_instalado": composicao._servicos["_classificar_modalidade_turno_mente"] is classificar_modalidade_turno,
            "cadeia_instalada": coordenador_intencao.processar_comandos_em_cadeia.__globals__["segmentar_comandos_em_cadeia"] is segmentar_comandos_em_cadeia,
            "casos": [], "efeito_externo": False,
        }
        for texto in textos:
            turno = root._iniciar_planejamento_turno(texto, origem="teste_limites_citados")
            caso = {
                "texto": texto, "segmentos": turno["segmentos"],
                "autoriza": turno["autoriza_execucao"],
                "operacional": turno.get("texto_operacional", ""),
                "cadeia": segmentar_comandos_em_cadeia(texto, normalizar_texto=root._normalizar_texto_com_apelidos),
            }
            if len(saida["casos"]) >= 4:
                # Planner e estado instalados; portas de efeito isoladas.
                # Captura a entrada entregue pelo consumidor real à cadeia,
                # sem invocar main, executores, voz ou serviços pessoais.
                recebidos = []
                prioridade = root._comandos_imediatos_runtime
                getter = prioridade.namespace_getter
                prioridade.namespace_getter = lambda: {
                    "_estado_compartilhado_runtime": root._estado_compartilhado_runtime,
                    "_normalizar_texto_com_apelidos": root._normalizar_texto_com_apelidos,
                    "_texto_tem_comando_explicito": root._texto_tem_comando_explicito,
                    "processar_comandos_em_cadeia": lambda trecho, origem: recebidos.append(trecho) or True,
                }
                try:
                    caso["prioridade_tratou"] = prioridade.processar_prioritarios(texto)
                    caso["entrada_cadeia"] = recebidos
                finally:
                    prioridade.namespace_getter = getter
            saida["casos"].append(caso)
        sys.__stdout__.write("CITADOS_JSON=" + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    env = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_SONDA_CITADOS=str(pasta),
               LAYLAY_NEURAL_MODE="off", LAYLAY_NEURAL_COLETA_ENTRADAS="0",
               LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
               LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0",
               LAYLAY_FALAS_INICIAIS="0", LAYLAY_PRESENCA="0",
               LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
               LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0",
               GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
    processo = subprocess.run([sys.executable, "-c", codigo],
                              cwd=Path(__file__).resolve().parents[2], env=env,
                              capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert processo.returncode == 0, processo.stderr[-3000:]
    linhas = [l for l in processo.stdout.splitlines() if l.startswith("CITADOS_JSON=")]
    assert len(linhas) == 1, processo.stdout[-2500:]
    return json.loads(linhas[0].split("=", 1)[1])


def test_composicao_instala_os_segmentadores_canonicos(composicao_citada):
    assert composicao_citada["classificador_instalado"]
    assert composicao_citada["cadeia_instalada"]


@pytest.mark.parametrize("indice,literal,quantidade", [
    (0, '"abre a calculadora e apaga o arquivo notas.txt"', 1),
    (1, '"pausa a música e fecha o navegador"', 1),
    (2, '"teste, fecha o navegador.txt"', 2),
])
def test_turno_instalado_preserva_literal_e_ordens_externas(composicao_citada, indice, literal, quantidade):
    caso = composicao_citada["casos"][indice]
    assert caso["autoriza"] is True
    assert len(caso["segmentos"]) == quantidade
    assert literal in caso["segmentos"][0]["texto"]
    assert len(caso["cadeia"]) == quantidade
    assert literal in caso["cadeia"][0]


def test_turno_instalado_recusa_aspas_malformadas_sem_cadeia_parcial(composicao_citada):
    caso = composicao_citada["casos"][3]
    assert caso["autoriza"] is False
    assert len(caso["cadeia"]) == 1


@pytest.mark.parametrize("indice", [4, 5])
def test_composicao_nao_despacha_condicao_nao_observada(composicao_citada, indice):
    caso = composicao_citada["casos"][indice]
    assert caso["autoriza"] is False
    assert caso["operacional"] == ""
    assert caso["entrada_cadeia"] == []
    assert caso["prioridade_tratou"] is False


@pytest.mark.parametrize("indice", [6, 7, 8])
def test_composicao_entrega_apenas_ordem_independente(composicao_citada, indice):
    caso = composicao_citada["casos"][indice]
    assert caso["autoriza"] is True
    assert len(caso["segmentos"]) == 2
    assert caso["entrada_cadeia"] == [caso["operacional"]]
    assert "quando eu" not in caso["operacional"]
    assert "se eu" not in caso["operacional"]
    assert caso["prioridade_tratou"] is True


@pytest.mark.parametrize("indice", [9, 10])
def test_composicao_consulta_significado_sem_autorizar_efeito(composicao_citada, indice):
    caso = composicao_citada["casos"][indice]
    assert caso["autoriza"] is False
    assert len(caso["segmentos"]) == 1
    assert caso["operacional"] == ""
    assert caso["entrada_cadeia"] == []
    assert caso["prioridade_tratou"] is False


@pytest.mark.parametrize("indice", [11, 12, 13])
def test_composicao_nao_reintroduz_consulta_no_encaminhamento(composicao_citada, indice):
    caso = composicao_citada["casos"][indice]
    assert len(caso["segmentos"]) == 2
    assert caso["autoriza"] is True
    assert "calculadora" not in caso["operacional"]
    assert caso["entrada_cadeia"] == [caso["operacional"]]
    assert caso["prioridade_tratou"] is True


def test_composicao_nao_veta_predicado_dentro_do_nome_citado(composicao_citada):
    caso = composicao_citada["casos"][14]
    assert caso["autoriza"] is True
    assert '"isso significa o quê.txt"' in caso["operacional"]
