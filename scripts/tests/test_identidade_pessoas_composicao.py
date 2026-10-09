"""Identidade antes de persistir pelo serviço e callbacks instalados por laylay.py."""

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope="module")
def identidade_instalada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("pessoas_composicao")
    codigo = textwrap.dedent(r'''
        import json, os, sys, threading
        from pathlib import Path
        from mente_laylay.integracao import instancia_unica
        from scripts.roteiros.sonda_transporte_evidencia import _instalar_observacao_p16
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda identificador, **kwargs: adquirir(
            str(identificador)+'.sonda-identidade-'+str(os.getpid()), **kwargs)
        pasta = Path(os.environ['SONDA_PESSOAS_DIR'])
        restauracoes = _instalar_observacao_p16(pasta, threading.local(), isolar_pessoas=True)
        import laylay as root
        root._composicao_turno_runtime._servicos['_coleta_entradas_neurais'] = None
        servico = root._memoria_pessoas_runtime
        registro = root._registro_memoria_pessoas_runtime
        estado = root._estado_compartilhado_runtime
        out = {'owners': {
            'mesmo_servico': registro.servico is servico,
            'mesmo_registro': root._comandos_imediatos_runtime.memoria_pessoas is registro,
            'porta_isolada': servico.caminho == pasta / 'pessoas_proprias.json',
            'callback_receipt': callable(servico.registrar_resultado),
            'callback_aprendizado': callable(servico.registrar_aprendizado),
        }, 'casos': []}
        for texto in (
            'Meu irmão está bravo. Eu me sinto culpado.',
            'Minha amiga parece cansada.',
            'Meu colega chegou atrasado.',
            'Meu irmão se chama Esta.',
            'Meu irmão estava bravo.',
            'Meu projeto se chama Aurora.',
            'O arquivo se chama Relatorio.',
            'Ana é minha prima.',
        ):
            root._iniciar_planejamento_turno(texto, origem='sonda_identidade')
            antes = servico.caminho.read_bytes() if servico.caminho.exists() else None
            tratado = root._processar_comandos_prioritarios(texto)
            depois = servico.caminho.read_bytes() if servico.caminho.exists() else None
            plano = estado.obter_copia('mental', 'plano_turno_atual')
            out['casos'].append({'texto': texto, 'tratado': tratado,
                'arquivo_inalterado': antes == depois,
                'pessoas': json.loads(depois)['pessoas'] if depois else [],
                'comandos': plano.get('comandos'),
                'apelidos': root._linguagem_aprendida_runtime.carregar_apelidos(force=True),
                'entidades': estado.obter_copia('mental', 'registro_semantico').get('entidades', {})})
        for owner,nome,original in reversed(restauracoes):
            setattr(owner,nome,original)
        sys.__stdout__.write('IDENTIDADE_INSTALADA '+json.dumps(out,ensure_ascii=False)+'\n')
    ''')
    env = dict(os.environ, SONDA_PESSOAS_DIR=str(pasta), PYTHONIOENCODING="utf-8",
        LAYLAY_MICROFONE_ATIVO="0", LAYLAY_MASCOT_ENABLED="0", LAYLAY_AVATAR_ATIVO="0",
        LAYLAY_PRESENCA="0", LAYLAY_IOT_MODO="simulado", LAYLAY_BRIEFING_INICIAL="0")
    p = subprocess.run([sys.executable, "-c", codigo], env=env,
        cwd=Path(__file__).resolve().parents[2], capture_output=True,
        text=True, encoding="utf-8", timeout=60)
    assert p.returncode == 0, p.stderr[-4000:]
    linhas = [s.removeprefix("IDENTIDADE_INSTALADA ") for s in p.stdout.splitlines()
        if s.startswith("IDENTIDADE_INSTALADA ")]
    assert len(linhas) == 1, p.stdout[-2000:]
    return json.loads(linhas[0])


def test_identidade_usa_servico_registro_e_callbacks_reais(identidade_instalada):
    assert all(identidade_instalada["owners"].values())


@pytest.mark.parametrize("indice", [0, 1, 2, 4, 5, 6])
def test_predicado_sem_nome_nao_persiste_nem_publica_receipt_na_composicao(
    identidade_instalada, indice,
):
    caso = identidade_instalada["casos"][indice]
    assert caso["arquivo_inalterado"], "primeira fronteira: observação sem identidade explícita não escreve"
    assert caso["comandos"] == []
    assert caso["tratado"] is False
    assert caso["apelidos"] == {}


@pytest.mark.parametrize("indice,nome,nomes", [(3, "Esta", ["Esta"]), (7, "Ana", ["Esta", "Ana"])])
def test_nomeacao_explicita_persiste_nome_literal_e_publica_receipt(identidade_instalada, indice, nome, nomes):
    caso = identidade_instalada["casos"][indice]
    assert [p["nome"] for p in caso["pessoas"]] == nomes
    assert caso["pessoas"][-1]["relacoes"][0]["evidencia"] == caso["texto"]
    receipt = caso["comandos"][0]
    assert receipt["intent"] == "PEOPLE_REMEMBER"
    assert receipt["alvo"] == nome
    assert receipt["executou"] is receipt["confirmado"] is True
    assert any(e["nome"] == nome for e in caso["entidades"].values())
    assert caso["tratado"] is False
    assert caso["apelidos"] == {}
