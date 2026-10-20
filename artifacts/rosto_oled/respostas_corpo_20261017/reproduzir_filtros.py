"""Replay diagnóstico de políticas com episódios persistidos, sem hardware/voz.

Não reproduz o processo vivo: coordenador, diretor, produtor e porteiro reais;
modelo e reprodução excluídos. A falha de áudio é entrada histórica explícita.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from mente_laylay.autonomia.coordenador_oportunidades import CoordenadorOportunidadesRuntime
from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_evento
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from mente_laylay.memoria_mental.experiencia_corporal_runtime import ExperienciaCorporalRuntime


def instante(hora: str) -> float:
    return datetime.fromisoformat('2026-10-17 ' + hora).timestamp()


def main() -> None:
    db = sqlite3.connect((ROOT / 'memoria/laylay_memoria.sqlite').as_uri() + '?mode=ro', uri=True)
    rows = db.execute("""select criado_em, contexto_json from aprendizado_eventos
        where criado_em >= '2026-10-17 13:47:35' and criado_em <= '2026-10-17 13:50:20'
        and tipo='episodio_sensorial_corporal' order by id""").fetchall()
    db.close()
    registros = [(ts, json.loads(payload)['experiencia']) for ts, payload in rows]
    assert registros, 'Faltam os registros históricos; não fabricar fixture substituta.'
    agora = [instante('13:47:51.59')]
    estado = criar_estado_compartilhado_runtime()
    diagnostico: dict = {}
    produtor = ExperienciaCorporalRuntime(estado=estado, diagnostico_getter=lambda: diagnostico,
                                         clock=lambda: agora[0])
    politica = PorteiroProatividadeRuntime(contexto_getter=lambda: {}, agora=lambda: agora[0])
    estado_coordenador: dict = {}
    coordenador = CoordenadorOportunidadesRuntime(
        encaminhar=lambda _: {'decisao': 'sugerir'}, clock=lambda: agora[0],
        estado_get=lambda: estado_coordenador,
        estado_set=lambda novo: estado_coordenador.update(novo), log=lambda _: None)
    estado_diretor: dict = {}
    admissoes: list[dict] = []

    def cogitar(evento):
        return {'natureza_entrada': 'evento', 'autoriza_execucao': False,
                'contrato_fala': construir_contrato_semantico_evento(evento)}

    def materializar(turno, **opcoes):
        # Tempos de admissão extraídos do DEV, não medidos neste replay.
        admissao = ('13:47:58.918' if not admissoes else '13:48:20.196')
        agora[0] = instante(admissao)
        fala = ('A medição frontal indicou algo perto.' if not admissoes
                else 'A medição inferior deixou de confirmar a superfície.')
        decisao = politica.avaliar(tipo='presenca_corporal', texto=fala)
        admissoes.append({'hora': admissao, **decisao})
        opcoes['ao_materializar_fala'](fala)
        # Receipt histórico: primeira falhou no TTS; segunda descartada.
        opcoes['ao_concluir'](False, 'entrega_nao_confirmada' if len(admissoes) == 1
                             else 'politica_descartou')
        aceita = decisao['acao'] == 'emitir'
        return {'status': 'agendada' if aceita else 'bloqueada_porteiro',
                'agendada': aceita, 'emissao_fisica': False, 'autoriza_execucao': False}

    diretor = DiretorPresencaRuntime(
        estado_get=lambda: estado_diretor,
        estado_set=lambda novo: estado_diretor.update(novo),
        contexto_getter=lambda: {}, clock=lambda: agora[0],
        registrar_oportunidade=coordenador.registrar,
        processar_evento_cognitivo=cogitar,
        processar_proposta_comunicativa=materializar, log=lambda _: None)
    resultados = []
    # Duas entradas têm hora real de PLANO:EVENTO. As demais são ciclos
    # aproximados de 15 s, portanto não provam a decisão histórica individual.
    for hora in ('13:47:51.59', '13:48:14.289', '13:48:35.2', '13:48:50.2',
                 '13:49:05.2', '13:49:20.2'):
        agora[0] = instante(hora)
        historico = {}
        for ts, experiencia in registros:
            if datetime.fromisoformat(ts).timestamp() <= agora[0]:
                historico[experiencia['id']] = deepcopy(experiencia)
        estado.atualizar_campos('mental', historico_corporal=list(historico.values()))
        sessao = list(historico.values())[-1]['sessao']
        diagnostico.update(aplicacao_confirmada=True, sessao=sessao,
                           sensores={'recente': True, 'origem': 'owner_usb_dist_guard',
                                     'protecao': {'recente': True, 'origem': 'executor_protecao_esp',
                                                  'autoriza_execucao': False}})
        evento = produtor.candidato_presenca()
        if not evento:
            resultados.append({'hora': hora, 'candidato': False})
            continue
        assert evento['autoriza_execucao'] is False and evento['executavel'] is False
        resultado = diretor.considerar(evento)
        resultados.append({'hora': hora, 'incidente': evento['observacao_corporal']['incidente_id'],
                           'assunto': evento['assunto'], 'resultado': resultado})
    assert resultados[0]['incidente'] == 10
    assert resultados[1]['incidente'] == 13
    assert admissoes[0]['acao'] == 'emitir' and admissoes[1]['acao'] == 'descartar'
    assert '120 segundos' in ' '.join(admissoes[1]['motivos'])
    assert len(admissoes) == 2, 'Duplicatas deveriam parar antes de nova geração.'
    for resultado in resultados[2:5]:
        assert resultado['resultado']['decisao_iniciativa']['decisao'] == 'ignorar_duplicada_semantica'
    # O banco registra marcos, não cada leitura: depois do 21 não há outro
    # marco persistido nessa seleção. Não inferir daí ausência de sensor vivo.
    assert resultados[5] == {'hora': '13:49:20.2', 'candidato': False}
    assert estado_diretor['contadores']['emitidas'] == 0
    assert not estado_diretor['historico'], 'Falha de áudio não é receipt de reprodução.'

    # Controle: a janela semântica reabre após 5 min, sem mudar as proteções.
    agora[0] = instante('13:53:00')
    controle = coordenador.registrar({'dominio': 'corpo', 'tipo': 'presenca_companhia',
        'assunto': 'protecao:obstaculo', 'confianca': .94, 'utilidade': 80,
        'validade_s': 25, 'executavel': False})
    assert controle['decisao'] == 'sugerir'
    saida = {'tipo': 'replay_manual_de_componentes_reais', 'prova_runtime': False,
             'registros_historicos': len(registros), 'ciclos': resultados,
             'admissoes': admissoes, 'controle_apos_5min': controle,
             'emitidas_audio': estado_diretor['contadores']['emitidas'],
             'sem_hardware_sem_voz_sem_modelo': True}
    Path(__file__).with_name('replay_filtros.json').write_text(
        json.dumps(saida, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'ciclos': [{k: r.get(k) for k in ('hora', 'incidente', 'assunto')}
                               | {'status': r.get('resultado', {}).get('motivo',
                                  r.get('resultado', {}).get('status'))} for r in resultados],
                      'admissoes': admissoes, 'controle': controle}, ensure_ascii=False))


if __name__ == '__main__':
    main()
