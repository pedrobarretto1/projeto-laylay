"""Vínculo histórico não transforma contexto social em obrigação ou evidência."""
from copy import deepcopy
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.explicacao_fala_historica import (
    avaliar_fala_historica, vincular_explicacoes_por_ato,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.decisao_observada import ExplicacoesHistoricasPorAto
from mente_laylay.memoria_mental.decisao_observada import ExplicacaoOcorrencia
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


RAIZ = Path(__file__).resolve().parents[2]
CASO = next(c for c in json.loads((Path(__file__).parent / 'fixtures/biblioteca_20261031.json').read_text(encoding='utf8')) if c['id'] == 'teste-06')


def consulta_mista(texto, *, fala="Registrei o resultado do pedido.", intent="IOT_CONTROL", alvo="lâmpada"):
    registro = registrar_fala_observada(None, ocorrencia_id="fala-real", turno_id="anterior",
        fala=fala, canal="texto_publicado", resultados=(ResultadoAcao(intent=intent, alvo=alvo,
            status="resultado", executou=True, confirmado=True, origem="executor",
            id_solicitacao="resultado-real", evidencia_confirmacao="critério local"),) if intent else ())
    mente = {"registro_semantico": registro, "ultima_resposta": fala}
    turno = classificar_modalidade_turno(texto)
    plano = {"id": turno["id"], "texto_usuario": texto, "autoriza_execucao": False,
             "requer_execucao": False, "comandos": []}
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    return turno, plano, mente


@pytest.mark.parametrize("prefixo", ["Gostei da brincadeira.", "Entendi.", "Eu uso Linux."])
@pytest.mark.parametrize("intent,alvo", [("IOT_CONTROL", "lâmpada"), ("CREATE_FILE", "relatorio.txt")])
def test_contexto_conversacional_nao_invalida_fontes_historicas_dos_outros_atos(prefixo, intent, alvo):
    texto = prefixo + ' Por que você disse "Registrei o resultado do pedido."?'
    turno, plano, mente = consulta_mista(texto, intent=intent, alvo=alvo)
    antes = deepcopy(mente)
    fonte = plano["contrato_fala"].get("explicacoes_historicas_por_ato")
    assert type(fonte) is ExplicacoesHistoricasPorAto, "Primeiro RED: ato conversacional invalidou o vínculo inteiro."
    assert len(fonte.partes) == len(turno["segmentos"]) == 2
    social, historica = fonte.partes
    assert social.ato.modalidade == ("conversa" if prefixo == "Eu uso Linux." else "reacao")
    assert social.ato.indice == 0
    assert social.ocorrencia is social.fala is None and social.falha_fonte is False
    assert historica.fala is not None and historica.ocorrencia is None
    assert historica.fala.como_dict()["falas"][0]["resultados"][0]["alvo"] == alvo
    # A fonte canônica delimita a oração sem o separador entre os atos.
    assert social.fonte_textual.como_dict()["texto_original"] == prefixo.removesuffix(".")
    assert mente == antes
    resposta = avaliar_fala_historica("Foi porque o servidor voltou.", plano=plano)
    assert resposta["fonte_valida"] is True
    assert "não informa a causa" in resposta["fala"] and alvo in resposta["fala"]
    assert prefixo not in resposta["fala"] and "ainda não foi respondida" not in resposta["fala"]
    assert resposta["fala"].count("Sobre ") == 1


def test_binder_nao_consulta_owner_por_relato_sem_obrigacao_historica():
    texto = 'Eu uso Linux. Por que você apagou esse arquivo?'
    turno = classificar_modalidade_turno(texto)
    chamadas = []
    def recuperar(literal, *, turno):
        chamadas.append(literal)
        return None
    fonte = vincular_explicacoes_por_ato(texto, turno=turno, mente={}, recuperar_ocorrencia=recuperar)
    assert fonte is not None, "Contexto sem obrigação deve sobreviver ao vínculo."
    assert chamadas == [fonte.partes[1].fonte_textual.como_dict()["texto_original"]]
    assert fonte.partes[0].ocorrencia is fonte.partes[0].fala is None
    assert fonte.partes[1].ocorrencia.referencia == "ausente"


def test_entrada_historica06_preserva_todos_atos_e_nao_inventa_fonte_por_recencia():
    entrada = CASO['entrada']
    fala = CASO['historico'][-1]['content']
    turno, plano, _ = consulta_mista(entrada, fala=fala, intent=None)
    fonte = plano["contrato_fala"].get("explicacoes_historicas_por_ato")
    assert type(fonte) is ExplicacoesHistoricasPorAto
    assert len(fonte.partes) == len(turno["segmentos"]) == 6
    assert [p.ato.indice for p in fonte.partes] == list(range(6))
    assert all(p.ocorrencia is p.fala is None for p in fonte.partes[:-1])
    # O registro identifica a fala por conteúdo; o resumo não vira prova de
    # equivalência/causa. Restrição, literal integral e identidade sobrevivem.
    assert fonte.partes[-1].ocorrencia is None
    evidencia = fonte.partes[-1].fala.como_dict()
    assert evidencia['origem_referencia'] == 'conteudo_indireto'
    assert evidencia['falas'][0]['fala'] == fala
    assert evidencia['falas'][0]['resultados'] == []


@pytest.mark.parametrize("alteracao", ["turno", "texto", "comandos", "autoridade"])
def test_contexto_misto_nao_relaxa_guardas_historicas_ou_autoriza_efeitos(alteracao):
    texto = 'Entendi. Por que você disse "Registrei o resultado do pedido."?'
    _, plano, _ = consulta_mista(texto)
    if alteracao == "turno": plano["id"] = "outro"
    elif alteracao == "texto": plano["texto_usuario"] = "outra pergunta"
    elif alteracao == "comandos": plano["comandos"] = [{"intent": "IOT_CONTROL"}]
    else: plano["autoriza_execucao"] = True
    resultado = avaliar_fala_historica("A lâmpada acendeu porque o servidor voltou.", plano=plano)
    assert resultado["problemas"] == ["evidencia_historica_invalida"]
    assert resultado["autoriza_execucao"] is resultado["prova_semantica_livre"] is False


def test_contexto_social_nao_admite_fonte_historica_fabricada_na_parte_tipificada():
    _, plano, _ = consulta_mista('Entendi. Por que você disse "Registrei o resultado do pedido."?')
    fonte = plano["contrato_fala"].get("explicacoes_historicas_por_ato")
    assert fonte is not None
    with pytest.raises(ValueError):
        replace(fonte.partes[0], fala=fonte.partes[1].fala)


def test_pergunta_autonoma_sem_fonte_continua_visivel_apos_contexto_social():
    texto = 'Entendi. Por que você apagou esse arquivo? Qual é a capital do Brasil?'
    _, plano, _ = consulta_mista(texto)
    fonte = plano["contrato_fala"].get("explicacoes_historicas_por_ato")
    assert fonte is not None
    resposta = avaliar_fala_historica("Expliquei tudo.", plano=plano)["fala"]
    assert "Entendi." not in resposta
    assert "Ainda falta saber qual é a capital do Brasil." in resposta
    assert "você lembra de quando foi?" in resposta


def test_relato_sem_pergunta_historica_nao_cria_obrigacao_historica():
    _, plano, _ = consulta_mista('Entendi. Eu uso Linux.')
    assert "explicacoes_historicas_por_ato" not in plano["contrato_fala"]


@pytest.mark.parametrize('invalida', ['turno', 'texto', 'json'])
def test_fonte_fornecida_invalida_nao_desaparece_quando_contexto_misto_tem_vinculo(invalida):
    texto = 'Gostei da ideia. Como isso funcionaria?'
    turno, plano, mente = consulta_mista(texto)
    assert turno['modalidade'] in {'pergunta', 'deliberacao'}
    assert len(turno['segmentos']) == 2
    fonte = ExplicacaoOcorrencia(str(turno['id']), texto, (), 'ausente')
    if invalida == 'turno': fonte = replace(fonte, turno_consulta='outro')
    elif invalida == 'texto': fonte = replace(fonte, texto_consulta='outra pergunta')
    else: fonte = {'turno_consulta': str(turno['id']), 'texto_consulta': texto}
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano,
        mente=mente, explicacao_ocorrencia=fonte)
    assert 'explicacoes_historicas_por_ato' in contrato
    assert contrato['explicacoes_historicas_por_ato'] is None


def coletar_composicao(perfil, entrada, *, preparos=(), registro=None, artefatos=None):
    from scripts.tests.test_papo_casual_composicao import CODIGO, PONTE
    # A ponte exige o perfil privado dentro da raiz recebida; o audit hook
    # continua impedindo qualquer escrita fora deste subdiretório isolado.
    artefatos = artefatos or RAIZ / "resultados_testes/biblioteca_correcoes_20261031/historico"
    artefatos.mkdir(parents=True, exist_ok=True)
    perfil = Path(tempfile.mkdtemp(prefix=perfil.name + "-", dir=artefatos))
    codigo = CODIGO
    proposta = "proposta=casos['propostas'][len(envios)-1]"
    assert codigo.count(proposta) == 1
    codigo = codigo.replace(proposta, proposta + """
    esquema=kwargs['json'].get('response_format',{}).get('json_schema',{}).get('schema',{})
    unidade=esquema.get('properties',{}).get('suporte_proposicoes',{}).get('items',{})
    opcoes=unidade.get('properties',{}).get('texto',{}).get('enum',[])
    if opcoes:
        proposta={'comandos':[],'suporte_proposicoes':[{'texto':o,'fontes':[]}for o in opcoes]}
""")
    executar = "resposta=ponte.receber({'tipo':'mensagem','id':'x','texto':casos['entrada']})"
    assert codigo.count(executar) == 1
    codigo = codigo.replace(executar, """if casos.get('registro'):
        root._estado_compartilhado_runtime.atualizar_campos('mental',registro_semantico=casos['registro'])
    """ + executar + """
    from dataclasses import asdict
    p=root._estado_compartilhado_runtime.mental['plano_turno_atual']
    f=p['contrato_fala'].get('explicacoes_historicas_por_ato')
    sys.__stdout__.write('VINCULO_JSON='+json.dumps({'fonte':asdict(f)if f else None,'preparos':preparos,
        'tipo_fonte':type(f).__name__,'segmentos':p.get('atos'),
        'registro':root._estado_compartilhado_runtime.mental.get('registro_semantico')},default=str,ensure_ascii=False)+'\\n')
""")
    dados = {"entrada": entrada, "historico": [], "ponte": str(PONTE), "preparos": preparos,
             "registro": registro, "propostas": [{"comandos": [], "suporte_proposicoes": [
                 {"texto": "Não tenho base para reconstruir o motivo.", "fontes": []}]}]}
    perfil.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, "-B", "-c", codigo, str(perfil), json.dumps(dados, ensure_ascii=False)],
        cwd=RAIZ, env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off"),
        capture_output=True, text=True, encoding="utf8", timeout=60)
    (perfil / "subprocesso.log").write_text(r.stdout + r.stderr, encoding="utf8")
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-3000:]
    resultado = json.loads(next(l.split("=", 1)[1] for l in r.stdout.splitlines() if l.startswith("EFEITO_JSON=")))
    vinculo = json.loads(next(l.split("=", 1)[1] for l in r.stdout.splitlines() if l.startswith("VINCULO_JSON=")))
    (perfil / "resultado.json").write_text(json.dumps({"resultado": resultado, "vinculo": vinculo},
        indent=2, ensure_ascii=False), encoding="utf8")
    assert not resultado["efeitos"] and not resultado["voz"] and not resultado["violacoes"]
    assert not resultado["autoriza"] and not resultado["comandos"]
    return resultado, vinculo


def test_factory_publica_historico_apos_relato_sem_transformar_relato_em_pendencia(tmp_path):
    fala = "Podemos inventar histórias juntos."
    preparos = [{"id": "fonte", "entrada": "Vamos brincar de inventar uma história?", "propostas": [
        {"comandos": [], "suporte_proposicoes": [{"texto": fala, "fontes": []}]}]}]
    d, v = coletar_composicao(tmp_path / "fonte_publicada", 'Eu uso Linux. Por que você disse "' + fala + '"?', preparos=preparos)
    assert v["tipo_fonte"] == "ExplicacoesHistoricasPorAto"
    assert len(v["fonte"]["partes"]) == 2
    assert v["preparos"][0]["resposta"]["texto"] == fala, "A fala de referência precisa ter publicação nativa."
    resposta = d["resposta"]["texto"]
    assert "Essa fala foi entregue" in resposta and "não prova que uma ação aconteceu" in resposta
    assert "Eu uso Linux" not in resposta and "ainda não foi respondida" not in resposta
    assert d["http"] == 1 and not d["resposta"]["degradada"]


def test_factory_reconstroi_vinculo06_sem_apagar_limites_de_lookup_e_segmentacao(tmp_path):
    entrada = CASO['entrada']
    registro = None
    for indice, e in enumerate(CASO['historico']):
        if e['role'] == 'assistant':
            registro = registrar_fala_observada(registro, ocorrencia_id=str(indice), turno_id=str(indice),
                fala=e['content'], resultados=(), canal="texto_publicado")
    d, v = coletar_composicao(tmp_path / "replay06", entrada, registro=registro,
        artefatos=RAIZ / 'resultados_testes/rodada6_20261101/composicao')
    assert v["tipo_fonte"] == "ExplicacoesHistoricasPorAto" and len(v["fonte"]["partes"]) == 6
    assert d["resposta"]["tipo"] == "resposta" and not d["resposta"]["degradada"]
    assert "Não tenho evidência histórica válida para explicar essas partes da pergunta." != d["resposta"]["texto"]
    assert "Não tenho uma ocorrência histórica identificada" not in d["resposta"]["texto"]
    assert 'resultado operacional' not in d['resposta']['texto']
    assert 'formulação não ficou registrado' in d['resposta']['texto']
    assert 'ainda não foi respondida' not in d['resposta']['texto']
    assert not d['resposta']['falhas_geracao'] and not d['resposta']['encerrada']
    assert d["http"] == 1
