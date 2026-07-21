"""Orquestração do plano, estado e verificação de cada turno."""

from __future__ import annotations

import time

from mente_laylay.cognicao.leitura_semantica_turno import (
    aplicar_leitura_conversacional,
    comparar_com_legado,
)
from mente_laylay.memoria_mental.referencia_fala import extrair_referencia_musical_verificada

def iniciar_planejamento_turno(namespace_getter, texto: str) -> dict:
    inicio_diagnostico = time.perf_counter()
    sucesso = False
    ns = namespace_getter()
    observabilidade = ns.get('_observabilidade_mente_runtime')
    try:
        resultado = _iniciar_planejamento_turno(namespace_getter, texto)
        sucesso = True
        return resultado
    except Exception as erro:
        if observabilidade is not None:
            observabilidade.registrar_falha('interpretacao', 'falha_planejamento', erro=erro)
        raise
    finally:
        if observabilidade is not None:
            observabilidade.registrar_metrica(
                'interpretacao', (time.perf_counter() - inicio_diagnostico) * 1000.0, sucesso,
            )


def _iniciar_planejamento_turno(namespace_getter, texto: str) -> dict:
    ns = namespace_getter()
    mente_antes_turno = dict(ns['_estado_compartilhado_runtime'].mental)
    pendencia_turno = ns['_pendencia_ativa_turno_mente'](mente_antes_turno) or {}
    confirmacao_contextual_valida = bool(pendencia_turno.get('intencao') and (str(pendencia_turno.get('resposta_esperada') or '') == 'sim_ou_nao' or str(pendencia_turno.get('tipo') or '') in {'confirmacao', 'escolha'}))
    turno = ns['_classificar_modalidade_turno_mente'](texto, normalizar_texto=ns['_normalizar_texto_com_apelidos'], texto_tem_comando_explicito=ns['_texto_tem_comando_explicito'], confirmacao_contextual_valida=confirmacao_contextual_valida)
    # A leitura nova nasce como observadora. Ela é persistida para comparação,
    # mas não substitui modalidade, planejamento nem autorização de execução.
    leitura_semantica = {}
    interpretador_semantico = ns.get('_interpretador_semantico_runtime')
    modo_semantico = str(getattr(interpretador_semantico, 'modo', 'off') or 'off').lower()
    if modo_semantico == 'main':
        # A leitura virá junto da resposta principal; não faça uma segunda
        # chamada ao modelo antes do turno.
        leitura_semantica = {}
    elif modo_semantico == 'shadow' and callable(getattr(interpretador_semantico, 'observar', None)):
        try:
            interpretador_semantico.observar(texto, turno_legado=dict(turno))
        except Exception as erro:
            ns['print'](f"⚠️ [SEMÂNTICA] falha isolada ao agendar observação: {type(erro).__name__}")
    elif modo_semantico == 'conversation' and bool(turno.get('autoriza_execucao')):
        # A migração atual não toca em pedidos que o porteiro legado autorizou.
        leitura_semantica = {}
    elif interpretador_semantico is not None and callable(getattr(interpretador_semantico, 'analisar', None)):
        try:
            leitura_semantica = dict(interpretador_semantico.analisar(texto, turno_legado=turno) or {})
        except Exception as erro:
            ns['print'](f"⚠️ [SEMÂNTICA] falha isolada no modo observador: {type(erro).__name__}")
    if leitura_semantica:
        if modo_semantico == 'conversation':
            turno = aplicar_leitura_conversacional(turno, leitura_semantica)
            if str(turno.get('origem_modalidade') or '') == 'semantica_conversacional':
                ns['print'](
                    f"🧠 [SEMÂNTICA:APLICADA] modalidade={turno.get('modalidade_geral')} "
                    f"| atos={[item.get('ato') for item in turno.get('segmentos') or []]}"
                )
        else:
            turno['leitura_semantica_shadow'] = leitura_semantica
    identidade_turno = ns['_analisar_identidade_turno_mente'](texto, falante='pedro')
    funcao_comunicativa = ns['_analisar_funcao_comunicativa_mente'](texto)
    encerramento_assunto = ns['_classificar_encerramento_assunto_mente'](texto, mente_antes_turno)
    correcao_duravel = ns['_extrair_correcao_duravel_mente'](texto, estado_mental=mente_antes_turno)
    correcao_interpretacao = ns['_abrir_correcao_interpretacao_mente'](mente_antes_turno, texto, eh_correcao=str(funcao_comunicativa.get('funcao') or '') == 'correcao')
    turno['identidade'] = identidade_turno
    turno['funcao_comunicativa'] = funcao_comunicativa
    turno['encerramento_assunto'] = encerramento_assunto
    jogo_contexto = {}
    try:
        jogo_contexto = dict(ns['_modo_jogo_runtime'].contexto_atual() or {})
    except Exception:
        pass
    retrato_turno, entidades_recentes = ns['_construir_retrato_turno_mente'](texto, turno=turno, mente=mente_antes_turno, contexto_perceptivo=ns['_obter_contexto_perceptivo'](), playlist_state=ns['playlist_state'], jogo_contexto=jogo_contexto)
    atualidade_factual = dict(retrato_turno.get('atualidade_factual') or {})
    turno['atualidade_factual'] = atualidade_factual
    if atualidade_factual.get('depende_atualidade'):
        ns['print'](
            f"🕒 [ATUALIDADE] classe={atualidade_factual.get('classe')} | "
            f"validade_sugerida={float(atualidade_factual.get('validade_sugerida_s') or 0.0):.0f}s | "
            f"confiança={float(atualidade_factual.get('confianca') or 0.0):.2f}"
        )
    limpeza_pergunta_turno = {}
    entidade_explicita = dict(retrato_turno.get('entidade_explicita') or {})
    topico_pendente = str(mente_antes_turno.get('pergunta_aberta_topico') or '').strip()
    nome_explicito = str(entidade_explicita.get('nome') or '').strip()
    funcao_atual = str(funcao_comunicativa.get('funcao') or '')
    topico_incompativel = bool(nome_explicito and topico_pendente and (nome_explicito.casefold() not in topico_pendente.casefold()) and (topico_pendente.casefold() not in nome_explicito.casefold()))
    if funcao_atual == 'correcao' or topico_incompativel:
        mente_limpa = ns['_limpar_pergunta_aberta_estado_mente'](mente_antes_turno)
        chaves_limpeza = ('pergunta_aberta_texto', 'pergunta_aberta_topico', 'pergunta_aberta_origem', 'pergunta_aberta_tipo', 'pergunta_aberta_proposito', 'pergunta_aberta_resposta_esperada', 'pergunta_aberta_ts', 'pendencia_atual', 'historico_pendencias')
        limpeza_pergunta_turno = {chave: mente_limpa.get(chave) for chave in chaves_limpeza if chave in mente_limpa}
        mente_antes_turno = mente_limpa
    registro_semantico = ns['_atualizar_registro_turno_mente'](mente_antes_turno.get('registro_semantico'), texto, retrato=retrato_turno, funcao=funcao_atual, encerramento=encerramento_assunto)
    mente_antes_turno['registro_semantico'] = registro_semantico
    candidatos_referencia = list(retrato_turno.get('referencia_candidatos') or [])
    if candidatos_referencia:
        resumo_candidatos = ', '.join((f"{item.get('nome')}:{float(item.get('pontuacao') or 0.0):.2f}" for item in candidatos_referencia[:3]))
        escolhida = dict(retrato_turno.get('referencia_resolvida') or {})
        ns['print'](f"🧠 [REFERÊNCIA] candidatos=[{resumo_candidatos}] | escolhido={escolhida.get('nome') or '-'} | operacao={retrato_turno.get('operacao_explicita') or '-'}")
    fundamentacao_factual = {}
    tema_factual = ns['_extrair_tema_fundamentacao_mente'](texto, retrato=retrato_turno, registro_semantico=registro_semantico)
    if tema_factual and (not dict(retrato_turno.get('referencia_resolvida') or {}).get('nome')):
        registro_semantico = ns['_atualizar_registro_turno_mente'](registro_semantico, texto, retrato={'entidade_explicita': {'tipo': 'tema', 'nome': tema_factual, 'origem': 'tema_pesquisavel'}}, funcao=funcao_atual, encerramento=encerramento_assunto)
        mente_antes_turno['registro_semantico'] = registro_semantico
    turno_operacional = bool(retrato_turno.get('operacao_explicita')) or str(turno.get('modalidade_geral') or turno.get('modalidade') or '') == 'comando'
    if tema_factual and (not turno_operacional):
        try:
            pesquisa_factual = ns['_pesquisa_contextual_runtime'].pesquisar_contexto_tema(tema_factual)
        except Exception as erro:
            pesquisa_factual = {'ok': False, 'motivo': f"falha_pesquisa:{type(erro).__name__}"}
        fundamentacao_factual = ns['_montar_fundamentacao_mente'](
            tema_factual,
            pesquisa_factual,
            atualidade=atualidade_factual,
        )
        ns['print'](f"🔎 [FUNDAMENTAÇÃO] tema={tema_factual!r} | confiavel={fundamentacao_factual.get('confiavel')} | fonte={fundamentacao_factual.get('fonte') or '-'} | confianca={float(fundamentacao_factual.get('confianca') or 0.0):.2f}")
    mente_antes_turno['fundamentacao_factual_turno'] = fundamentacao_factual
    turno['retrato_id'] = retrato_turno.get('id')
    turno['entidades'] = dict(retrato_turno.get('entidades') or {})
    turno['referencia_resolvida'] = dict(retrato_turno.get('referencia_resolvida') or {})
    turno['operacao_explicita'] = str(retrato_turno.get('operacao_explicita') or '')
    especialistas = ns['_construir_parecer_especialistas_mente'](texto, turno=turno, funcao_comunicativa=funcao_comunicativa, retrato=retrato_turno, saude=ns['_saude_mente_runtime'].snapshot())
    turno['especialistas'] = especialistas
    assunto_estruturado = ns['_atualizar_assunto_estruturado_mente'](mente_antes_turno.get('assunto_estruturado_atual') if isinstance(mente_antes_turno.get('assunto_estruturado_atual'), dict) else {}, texto, turno=turno, retrato=retrato_turno, encerramento=encerramento_assunto)
    plano = ns['_planejar_turno_mente'](texto, turno=turno, mente=mente_antes_turno, periodo=ns['_contexto_horario_atual']())
    plano['fundamentacao_factual'] = fundamentacao_factual
    plano['atualidade_factual'] = atualidade_factual
    atualizacoes_turno = {'ultima_entrada_ts': ns['time'].time(), 'turno_atual': turno, 'plano_turno_atual': plano, 'identidade_turno_atual': identidade_turno, 'identidade_turno_resumo': ns['_resumo_identidade_turno_mente'](identidade_turno), 'funcao_comunicativa_atual': funcao_comunicativa, 'retrato_turno_atual': retrato_turno, 'entidades_recentes': entidades_recentes, 'especialistas_turno_atual': especialistas, 'assunto_estruturado_atual': assunto_estruturado, 'registro_semantico': registro_semantico, 'fundamentacao_factual_turno': fundamentacao_factual, **limpeza_pergunta_turno}
    if leitura_semantica:
        atualizacoes_turno['leitura_semantica_turno'] = leitura_semantica
    if correcao_interpretacao:
        atualizacoes_turno['correcao_interpretacao_pendente'] = correcao_interpretacao
    if encerramento_assunto == 'topico':
        atualizacoes_turno.update(encerramento_assunto_pendente='topico', encerramento_assunto_motivo=str(texto or '').strip()[:300])
    if str(funcao_comunicativa.get('funcao') or '') == 'correcao':
        atualizacoes_turno.update(ultima_correcao_conversacional=str(texto or '').strip()[:500], ultima_correcao_conversacional_ts=ns['time'].time())
    if correcao_duravel:
        chave_correcao = f"{correcao_duravel.get('tipo')}|{correcao_duravel.get('gatilho')}|{correcao_duravel.get('valor')}".casefold()
        if chave_correcao != str(mente_antes_turno.get('ultima_correcao_persistida_chave') or ''):
            try:
                if ns['_persistir_correcao_duravel_mente'](ns['MEMORIA_SQLITE'], correcao_duravel, texto):
                    atualizacoes_turno.update(ultima_correcao_persistida_chave=chave_correcao, ultima_correcao_persistida=correcao_duravel, ultima_correcao_persistida_ts=ns['time'].time())
                    ns['print'](f"🧠 [MEMÓRIA] correção de Pedro persistida: {correcao_duravel.get('regra')}")
            except Exception as erro:
                ns['print'](f"⚠️ [MEMÓRIA] não consegui persistir a correção: {erro}")
    ns['_estado_compartilhado_runtime'].atualizar_campos('mental', **atualizacoes_turno)
    ns['print'](f"🧠 [PLANO:TURNO] modalidade={plano.get('modalidade')} | dominio={plano.get('dominio')} | execucao={plano.get('requer_execucao')} | coordenacao={plano.get('modo_coordenacao')} | contexto={plano.get('contexto_necessario')}")
    return turno


def registrar_leitura_semantica_principal(namespace_getter, texto: str, leitura: dict | None) -> dict:
    """Registra a leitura da resposta principal sem alterar sua autorização."""
    ns = namespace_getter()
    semantica = dict(leitura or {})
    if not semantica.get('valida'):
        return {}
    mente = dict(ns['_estado_compartilhado_runtime'].mental)
    turno = dict(mente.get('turno_atual') or {})
    comparacao = comparar_com_legado(semantica, turno)
    semantica.update(
        modo='main',
        comparacao_legado=comparacao,
        somente_observacao=True,
    )
    # Copia apenas para observabilidade/contexto futuro. Campos de decisão,
    # plano e autorização do turno atual permanecem exatamente como estavam.
    turno['leitura_semantica_principal'] = semantica
    ns['_estado_compartilhado_runtime'].atualizar_campos(
        'mental',
        turno_atual=turno,
        leitura_semantica_turno=semantica,
    )
    atos = [str(item.get('tipo') or '') for item in semantica.get('atos') or [] if isinstance(item, dict)]
    ns['print'](
        f"🧠 [SEMÂNTICA:PRINCIPAL] atos={atos or ['-']} | "
        f"modalidade={semantica.get('modalidade_geral') or '-'} | "
        f"confiança={float(semantica.get('confianca') or 0.0):.2f} | "
        f"divergências={comparacao.get('divergencias') or []}"
    )
    return semantica

def atualizar_planejamento_turno(namespace_getter, fase: str, *, comandos=(), erros=(), fala: str='') -> dict:
    ns = namespace_getter()
    atual = dict(ns['_estado_compartilhado_runtime'].mental.get('plano_turno_atual') or {})
    comandos_atuais = list(atual.get('comandos') or [])
    comandos_novos = [dict(item) for item in comandos or () if isinstance(item, dict)]
    comandos_finais = list(comandos_atuais)
    if comandos_novos:
        por_intent = {str(item.get('intent') or item.get('acao') or '').upper(): dict(item) for item in comandos_atuais if str(item.get('intent') or item.get('acao') or '').strip()}
        ordem = list(por_intent)
        for item in comandos_novos:
            chave = str(item.get('intent') or item.get('acao') or '').upper()
            anterior = dict(por_intent.get(chave) or {})
            mesclado = dict(anterior)
            mesclado.update(item)
            for campo in ('status', 'executou', 'confirmado'):
                if item.get(campo) in (None, '') and anterior.get(campo) not in (None, ''):
                    mesclado[campo] = anterior[campo]
            por_intent[chave] = mesclado
            if chave not in ordem:
                ordem.append(chave)
        comandos_finais = [por_intent[chave] for chave in ordem]
    novo = ns['_atualizar_plano_turno_mente'](atual, fase=fase, comandos=comandos_finais, erros=erros, fala=fala)
    ns['_estado_compartilhado_runtime'].atualizar_campos('mental', plano_turno_atual=novo)
    trilha = ns['_registrar_etapa_turno_mente'](ns['_estado_compartilhado_runtime'].mental.get('trilha_decisoes_turno') or [], novo, fase=fase)
    ns['_estado_compartilhado_runtime'].atualizar_campos('mental', trilha_decisoes_turno=trilha)
    ns['print'](f"🧠 [PLANO:FASE] fase={novo.get('fase')} | comandos={novo.get('comandos') or []} | erros={novo.get('erros') or []}")
    return novo

def verificar_fala_do_turno(namespace_getter, fala: str, *, origem: str='conversa') -> dict:
    ns = namespace_getter()
    mente = ns['_estado_compartilhado_runtime'].mental
    fala = ns['_ajustar_autorreferencia_assistente_mente'](fala)
    verificacao = ns['_verificar_fala_turno_mente'](fala, plano=dict(mente.get('plano_turno_atual') or {}), periodo=ns['_contexto_horario_atual'](), ultima_resposta=str(mente.get('ultima_resposta') or ''), origem=origem)
    plano = dict(mente.get('plano_turno_atual') or {})
    plano['fase'] = 'fala_verificada'
    plano['ultima_verificacao'] = dict(verificacao)
    avaliacoes = list(mente.get('avaliacoes_turno') or [])
    avaliacoes.append({'plano_id': plano.get('id'), 'origem': str(origem or 'conversa'), 'pontuacao': float(verificacao.get('pontuacao') or 0.0), 'problemas': list(verificacao.get('problemas') or []), 'acao': str(verificacao.get('acao') or ''), 'ts': ns['time'].time()})
    metricas = dict(mente.get('metricas_verificador') or {})
    metricas['falas_verificadas'] = int(metricas.get('falas_verificadas') or 0) + 1
    if verificacao.get('problemas'):
        metricas['falas_ajustadas'] = int(metricas.get('falas_ajustadas') or 0) + 1
        for problema in verificacao.get('problemas') or []:
            chave = f'problema:{problema}'
            metricas[chave] = int(metricas.get(chave) or 0) + 1
    ns['_estado_compartilhado_runtime'].atualizar_campos('mental', plano_turno_atual=plano, avaliacoes_turno=avaliacoes[-50:], metricas_verificador=metricas)
    referencia_musical = extrair_referencia_musical_verificada(str(verificacao.get('fala') or ''), plano)
    if referencia_musical:
        agora = ns['time'].time()
        entidades = dict(mente.get('entidades_recentes') or {})
        entidades['musica'] = {'tipo': 'musica', 'nome': referencia_musical, 'origem': 'fala_verificada', 'ts': agora}
        ns['_estado_compartilhado_runtime'].atualizar_campos(
            'mental',
            ultima_musica_mencionada={'titulo': referencia_musical, 'origem': 'fala_verificada', 'ts': agora},
            entidades_recentes=entidades,
        )
    if verificacao.get('problemas'):
        casos = list(mente.get('casos_regressao_candidatos') or [])[-29:]
        casos.append({'origem': 'verificador_fala', 'texto': str(plano.get('texto_usuario') or '')[:500], 'fala': str(verificacao.get('fala') or '')[:500], 'problemas': list(verificacao.get('problemas') or []), 'plano_id': plano.get('id'), 'ts': ns['time'].time()})
        ns['_estado_compartilhado_runtime'].atualizar_campos('mental', casos_regressao_candidatos=casos)
        ns['print'](f"🛡️ [VERIFICADOR:FALA] origem={origem} | acao={verificacao.get('acao')} | problemas={verificacao.get('problemas')}")
    return verificacao
