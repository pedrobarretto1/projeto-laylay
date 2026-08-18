"""Orquestração do plano, estado e verificação de cada turno."""

from __future__ import annotations

import time

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.leitura_semantica_turno import (
    aplicar_leitura_conversacional,
    comparar_com_legado,
)
from mente_laylay.cognicao.intencao_visual_jogo import (
    aplicar_pedido_visual_ao_turno,
    detectar_pedido_visao_jogo,
)
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
from mente_laylay.memoria_mental.referencia_fala import extrair_referencia_musical_verificada
from mente_laylay.memoria_mental.memoria_confiavel import (
    extrair_aprendizados_pessoais_explicitos,
)


def registrar_metrica_opcional(ns: dict, componente: str, duracao_ms: float, sucesso: bool) -> None:
    """Registra telemetria sem depender de variáveis do escopo chamador."""
    observabilidade = ns.get('_observabilidade_mente_runtime') if isinstance(ns, dict) else None
    if observabilidade is None:
        return
    try:
        observabilidade.registrar_metrica(componente, duracao_ms, sucesso)
    except Exception:
        # Telemetria nunca pode interromper uma conversa.
        return


def registrar_falha_opcional(
    ns: dict,
    componente: str,
    codigo: str,
    erro: BaseException,
    *,
    classe: str,
    impacto: str,
    fallback: str,
) -> None:
    """Torna uma degradação visível no diagnóstico sem quebrar o turno.

    O objeto de observabilidade sanitiza o erro: mensagem, caminhos e conteúdo
    do usuário não são persistidos. Se a própria telemetria falhar, o fluxo
    principal continua intacto.
    """
    observabilidade = ns.get('_observabilidade_mente_runtime') if isinstance(ns, dict) else None
    registrar = getattr(observabilidade, 'registrar_falha', None)
    if not callable(registrar):
        return
    try:
        registrar(
            componente,
            codigo,
            erro=erro,
            classe=classe,
            impacto=impacto,
            fallback=fallback,
        )
    except Exception:
        # Observabilidade nunca pode ser uma nova causa de falha do turno.
        return


def resolver_repeticao_operacional_segura(ns: dict, texto: str) -> dict | None:
    """Consulta a continuidade; em falha, deixa um diagnóstico acionável."""
    resolver = ns.get('_resolver_repeticao_ultima_acao')
    if not callable(resolver):
        return None
    try:
        repeticao = resolver(texto)
        return repeticao if isinstance(repeticao, dict) else None
    except Exception as erro:
        registrar_falha_opcional(
            ns,
            'continuidade_turno',
            'falha_resolver_repeticao',
            erro,
            classe='defeito',
            impacto='turno',
            fallback='conversa_sem_repeticao',
        )
        return None


def obter_contexto_jogo_seguro(ns: dict) -> dict:
    """Obtém o modo de jogo sem esconder a perda de contexto perceptivo."""
    modo_jogo = ns.get('_modo_jogo_runtime')
    obter_contexto = getattr(modo_jogo, 'contexto_atual', None)
    if not callable(obter_contexto):
        return {}
    try:
        return dict(obter_contexto() or {})
    except Exception as erro:
        registrar_falha_opcional(
            ns,
            'contexto_jogo',
            'falha_contexto_atual',
            erro,
            classe='degradacao',
            impacto='turno',
            fallback='turno_sem_contexto_jogo',
        )
        return {}


def anexar_estado_visual_recente_seguro(ns: dict, jogo_contexto: dict) -> dict:
    """Anexa a recência visual ou registra por que ela não pôde ser usada."""
    contexto = dict(jogo_contexto or {})
    visao_jogo = ns.get('_registro_visao_jogo_leitura_runtime')
    verificar = getattr(visao_jogo, 'tem_analise_recente', None)
    if not callable(verificar):
        return contexto
    try:
        contexto['analise_visual_recente'] = bool(verificar())
    except Exception as erro:
        contexto['analise_visual_recente'] = False
        registrar_falha_opcional(
            ns,
            'contexto_visual_jogo',
            'falha_verificar_analise_recente',
            erro,
            classe='degradacao',
            impacto='turno',
            fallback='turno_sem_memoria_visual_recente',
        )
    return contexto


def aplicar_repeticao_operacional_ao_turno(turno: dict, repeticao: object) -> dict:
    """Autoriza uma repetição somente quando a mente recuperou uma ação real.

    A frase curta por si só continua ambígua. A autorização nasce do contrato
    persistido da última ação reexecutável, não de palavras-chave isoladas.
    """
    resultado = dict(turno or {})
    if not isinstance(repeticao, dict):
        return resultado
    intent = str(repeticao.get("intent") or "").strip().upper()
    params = repeticao.get("params")
    if not intent or not isinstance(params, dict):
        return resultado
    resultado.update(
        modalidade="comando",
        modalidade_geral="comando",
        ato_principal="comando",
        texto_operacional=str(resultado.get("texto") or "").strip(),
        confianca=max(0.97, float(resultado.get("confianca") or 0.0)),
        motivo="repetição explícita de ação reexecutável recuperada da mente",
        motivo_decisao="repetição explícita de ação reexecutável recuperada da mente",
        acao_explicita=True,
        autoriza_execucao=True,
        requer_esclarecimento=False,
        depende_contexto=True,
        natureza_acao="repeticao_operacional",
        repeticao_operacional={"intent": intent, "params": dict(params)},
    )
    return resultado

def reconciliar_alvo_eliptico_janela_confirmado(texto: str, *, turno: dict, retrato: dict, mente: dict) -> tuple[dict, dict]:
    """Resolve somente o alvo contextual comprovado do `maximiza` exato.

    Não cria autoridade. A ação precisa já estar autorizada e o mesmo app
    precisa existir simultaneamente em `ultimo_app_janela` e na entidade app
    congelada do retrato.
    """
    leitura = dict(turno or {})
    snapshot = dict(retrato or {})
    forma = str(texto or "").casefold().strip(" \t\r\n.,!?;:")
    if forma != "maximiza":
        return leitura, snapshot
    if not bool(leitura.get("autoriza_execucao")):
        return leitura, snapshot
    if not bool(leitura.get("requer_esclarecimento")):
        return leitura, snapshot
    ultimo_app = str(dict(mente or {}).get("ultimo_app_janela") or "").strip()
    entidade_app = dict(dict(snapshot.get("entidades") or {}).get("app") or {})
    nome_app = str(entidade_app.get("nome") or "").strip()
    if not ultimo_app or not nome_app:
        return leitura, snapshot
    if ultimo_app.casefold() != nome_app.casefold():
        return leitura, snapshot
    referencia = dict(entidade_app)
    snapshot["referencia_tipo"] = "app"
    snapshot["referencia_resolvida"] = referencia
    leitura["requer_esclarecimento"] = False
    leitura["depende_contexto"] = True
    leitura["referencia_resolvida"] = referencia
    leitura["alvo_contextual_resolvido"] = {
        "tipo": "app", "nome": nome_app,
        "origem": "elipse_operacional_maximiza_confirmada",
    }
    return leitura, snapshot

_ORIGENS_ENTRADA_VALIDAS = {
    'terminal', 'voz', 'modo_jogo', 'barra', 'api', 'desconhecida',
}


def _normalizar_origem_entrada(origem: object) -> str:
    valor = str(origem or 'desconhecida').strip().casefold()
    return valor if valor in _ORIGENS_ENTRADA_VALIDAS else 'desconhecida'


# P0_REVISAO_INTRA_TURNO_B1_2_1_20260816
def alinhar_identidade_plano_revisao(
    plano: dict,
    *,
    texto_original: str,
    texto_operacional_efetivo: str = '',
    revisao_intra_turno: dict | None = None,
) -> dict:
    """Separa a identidade pública do turno de sua visão operacional revisada.

    O planejador deve continuar recebendo a proposta final consolidada para não
    reintroduzir ações/alvos descartados. Depois do planejamento, porém,
    ``texto_usuario`` volta a representar a fala que realmente originou o
    turno. A visão operacional fica em um campo próprio e auditável.
    """
    resultado = dict(plano or {})
    resultado['texto_usuario'] = str(texto_original or '').strip()[:500]

    revisao = dict(revisao_intra_turno or {})
    if bool(revisao.get('detectada')):
        resultado['texto_operacional_efetivo'] = str(
            texto_operacional_efetivo or ''
        ).strip()[:500]
        resultado['revisao_intra_turno'] = revisao

    return resultado


def iniciar_planejamento_turno(
    namespace_getter,
    texto: str,
    *,
    origem: str = 'desconhecida',
) -> dict:
    inicio_diagnostico = time.perf_counter()
    sucesso = False
    ns = namespace_getter()
    observabilidade = ns.get('_observabilidade_mente_runtime')
    try:
        resultado = _iniciar_planejamento_turno(
            namespace_getter,
            texto,
            origem=origem,
        )
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


def _iniciar_planejamento_turno(
    namespace_getter,
    texto: str,
    *,
    origem: str = 'desconhecida',
) -> dict:
    ns = namespace_getter()
    mente_antes_turno = dict(ns['_estado_compartilhado_runtime'].mental)
    pendencia_turno = ns['_pendencia_ativa_turno_mente'](mente_antes_turno) or {}
    confirmacao_contextual_valida = bool(pendencia_turno.get('intencao') and (str(pendencia_turno.get('resposta_esperada') or '') == 'sim_ou_nao' or str(pendencia_turno.get('tipo') or '') in {'confirmacao', 'escolha'}))

    # P0_REVISAO_INTRA_TURNO_V1_1_20260816
    # Revisões dentro da própria fala são consolidadas antes do primeiro
    # detector operacional. O texto original continua auditável; apenas a
    # visão cognitiva/operacional recebe a última proposta válida.
    revisao_intra_turno = resolver_revisao_intra_turno(texto)
    revisao_detectada = bool(revisao_intra_turno.get('detectada'))
    revisao_resolvida = bool(revisao_intra_turno.get('resolvida'))
    revisao_cancelada = bool(revisao_intra_turno.get('cancelada'))
    texto_efetivo = str(
        revisao_intra_turno.get('texto_operacional_efetivo') or ''
    ).strip()
    texto_cognitivo = (
        texto_efetivo
        if revisao_detectada and revisao_resolvida and not revisao_cancelada and texto_efetivo
        else texto
    )

    turno = ns['_classificar_modalidade_turno_mente'](texto_cognitivo, normalizar_texto=ns['_normalizar_texto_com_apelidos'], texto_tem_comando_explicito=ns['_texto_tem_comando_explicito'], confirmacao_contextual_valida=confirmacao_contextual_valida)
    turno['origem_entrada'] = _normalizar_origem_entrada(origem)
    if revisao_detectada:
        turno['texto_original'] = str(texto or '')[:500]
        turno['texto'] = str(texto or '')[:500]
        turno['revisao_intra_turno'] = dict(revisao_intra_turno)
        turno['texto_operacional_efetivo'] = texto_efetivo
        if not revisao_resolvida:
            turno.update(
                modalidade='correcao',
                modalidade_geral='correcao',
                ato_principal='correcao',
                autoriza_execucao=False,
                requer_esclarecimento=True,
                acao_explicita=False,
                texto_operacional='',
                natureza_acao='revisao_ambigua',
                motivo='revisão interna detectada sem resolução operacional segura',
                motivo_decisao='revisão interna detectada sem resolução operacional segura',
            )
        elif revisao_cancelada:
            turno.update(
                modalidade='recusa',
                modalidade_geral='recusa',
                ato_principal='recusa',
                autoriza_execucao=False,
                requer_esclarecimento=False,
                acao_explicita=False,
                texto_operacional='',
                natureza_acao='cancelamento_revisao',
                motivo='usuário cancelou a proposta antes da execução',
                motivo_decisao='usuário cancelou a proposta antes da execução',
            )
        else:
            turno['texto_operacional'] = (
                texto_efetivo if bool(turno.get('autoriza_execucao')) else ''
            )
            ns['print'](
                '🧠 [REVISÃO:TURNO] '
                f"tipo={revisao_intra_turno.get('tipo')} | "
                f"efetivo={texto_efetivo!r}"
            )

    # Uma revisão atual não pode ser reinterpretada como repetição da ação
    # anterior só porque a proposta final contém "continua", "de novo" etc.
    repeticao_operacional = (
        None if revisao_detectada
        else resolver_repeticao_operacional_segura(ns, texto)
    )
    turno = aplicar_repeticao_operacional_ao_turno(turno, repeticao_operacional)
    if repeticao_operacional:
        ns['print'](
            f"🔁 [TURNO] repetição operacional autorizada | "
            f"intent={str(repeticao_operacional.get('intent') or '-')}"
        )
    jogo_contexto = obter_contexto_jogo_seguro(ns)
    visao_jogo_runtime = ns.get('_registro_visao_jogo_leitura_runtime')
    jogo_contexto = anexar_estado_visual_recente_seguro(ns, jogo_contexto)
    if jogo_contexto.get('ativo') and callable(getattr(visao_jogo_runtime, 'observar_texto_usuario', None)):
        try:
            visao_jogo_runtime.observar_texto_usuario(texto)
        except Exception as erro:
            ns['print'](f"⚠️ [VISÃO:SESSÃO] contexto ignorado: {type(erro).__name__}")
    pedido_visao_jogo = detectar_pedido_visao_jogo(texto_cognitivo, jogo_contexto)
    if pedido_visao_jogo:
        turno = aplicar_pedido_visual_ao_turno(turno, pedido_visao_jogo)
        ns['print'](
            f"🎮 [VISÃO:PEDIDO] tipo={pedido_visao_jogo['params'].get('tipo')} "
            f"| jogo={pedido_visao_jogo['params'].get('jogo') or '-'}"
        )
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
            interpretador_semantico.observar(texto_cognitivo, turno_legado=dict(turno))
        except Exception as erro:
            ns['print'](f"⚠️ [SEMÂNTICA] falha isolada ao agendar observação: {type(erro).__name__}")
    elif modo_semantico == 'conversation' and bool(turno.get('autoriza_execucao')):
        # A migração atual não toca em pedidos que o porteiro legado autorizou.
        leitura_semantica = {}
    elif interpretador_semantico is not None and callable(getattr(interpretador_semantico, 'analisar', None)):
        try:
            leitura_semantica = dict(interpretador_semantico.analisar(texto_cognitivo, turno_legado=turno) or {})
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
    funcao_comunicativa = ns['_analisar_funcao_comunicativa_mente'](texto_cognitivo)
    encerramento_assunto = ns['_classificar_encerramento_assunto_mente'](texto, mente_antes_turno)
    correcao_duravel = ns['_extrair_correcao_duravel_mente'](texto, estado_mental=mente_antes_turno)
    correcao_interpretacao = ns['_abrir_correcao_interpretacao_mente'](mente_antes_turno, texto, eh_correcao=str(funcao_comunicativa.get('funcao') or '') == 'correcao')
    turno['identidade'] = identidade_turno
    turno['funcao_comunicativa'] = funcao_comunicativa
    turno['encerramento_assunto'] = encerramento_assunto
    retrato_turno, entidades_recentes = ns['_construir_retrato_turno_mente'](texto_cognitivo, turno=turno, mente=mente_antes_turno, contexto_perceptivo=ns['_obter_contexto_perceptivo'](), playlist_state=ns['playlist_state'], jogo_contexto=jogo_contexto)
    turno, retrato_turno = reconciliar_alvo_eliptico_janela_confirmado(
        texto_cognitivo, turno=turno, retrato=retrato_turno, mente=mente_antes_turno,
    )
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
    aprendizados_explicitos = extrair_aprendizados_pessoais_explicitos(texto)
    turno['aprendizados_explicitos'] = aprendizados_explicitos
    tema_factual = ns['_extrair_tema_fundamentacao_mente'](
        texto_cognitivo, retrato=retrato_turno, registro_semantico=registro_semantico,
    )
    # Uma declaração pessoal pode ativar memória e pesquisa ao mesmo tempo.
    # A memória guarda a preferência confirmada; a pesquisa apenas enriquece
    # a conversa. Nenhuma das duas substitui a resposta humana do turno.
    if not tema_factual and aprendizados_explicitos:
        tema_factual = str(aprendizados_explicitos[0].get('valor') or '').strip()[:160]
    turno['tema_factual'] = tema_factual
    if tema_factual and (not dict(retrato_turno.get('referencia_resolvida') or {}).get('nome')):
        registro_semantico = ns['_atualizar_registro_turno_mente'](registro_semantico, texto, retrato={'entidade_explicita': {'tipo': 'tema', 'nome': tema_factual, 'origem': 'tema_pesquisavel'}}, funcao=funcao_atual, encerramento=encerramento_assunto)
        mente_antes_turno['registro_semantico'] = registro_semantico
    turno_operacional = bool(retrato_turno.get('operacao_explicita')) or str(turno.get('modalidade_geral') or turno.get('modalidade') or '') == 'comando'
    if tema_factual and (not turno_operacional):
        inicio_pesquisa = time.perf_counter()
        pesquisa_runtime = ns['_pesquisa_contextual_runtime']
        modalidade_pesquisa = str(turno.get('modalidade_geral') or turno.get('modalidade') or '').casefold()
        exige_resposta_factual_agora = bool(
            atualidade_factual.get('depende_atualidade')
            or modalidade_pesquisa in {'pergunta', 'misto'}
            or funcao_atual == 'correcao'
        )
        try:
            if exige_resposta_factual_agora:
                pesquisa_factual = pesquisa_runtime.pesquisar_contexto_tema(tema_factual)
            else:
                pesquisa_factual = pesquisa_runtime.obter_contexto_cache(tema_factual)
                if not pesquisa_factual:
                    pesquisa_runtime.precarregar_contexto_tema(tema_factual)
                    pesquisa_factual = {
                        'ok': False,
                        'tema': tema_factual,
                        'motivo': 'pesquisa_em_background',
                    }
                    ns['print'](f"🔎 [FUNDAMENTAÇÃO] pesquisa de {tema_factual!r} iniciada em segundo plano.")
        except Exception as erro:
            pesquisa_factual = {'ok': False, 'motivo': f"falha_pesquisa:{type(erro).__name__}"}
        registrar_metrica_opcional(
            ns,
            'pesquisa_factual',
            (time.perf_counter() - inicio_pesquisa) * 1000.0,
            bool(pesquisa_factual.get('ok')),
        )
        fundamentacao_factual = ns['_montar_fundamentacao_mente'](
            tema_factual,
            pesquisa_factual,
            atualidade=atualidade_factual,
        )
        fundamentacao_factual.update({
            'papel_cooperativo': 'enriquecimento_auxiliar',
            'nao_substitui_resposta_principal': True,
            'declaracao_pessoal_explicita': bool(aprendizados_explicitos),
        })
        ns['print'](f"🔎 [FUNDAMENTAÇÃO] tema={tema_factual!r} | confiavel={fundamentacao_factual.get('confiavel')} | fonte={fundamentacao_factual.get('fonte') or '-'} | confianca={float(fundamentacao_factual.get('confianca') or 0.0):.2f}")
    mente_antes_turno['fundamentacao_factual_turno'] = fundamentacao_factual
    turno['retrato_id'] = retrato_turno.get('id')
    turno['entidades'] = dict(retrato_turno.get('entidades') or {})
    turno['referencia_resolvida'] = dict(retrato_turno.get('referencia_resolvida') or {})
    turno['operacao_explicita'] = str(retrato_turno.get('operacao_explicita') or '')
    especialistas = ns['_construir_parecer_especialistas_mente'](texto_cognitivo, turno=turno, funcao_comunicativa=funcao_comunicativa, retrato=retrato_turno, saude=ns['_saude_mente_runtime'].snapshot())
    deliberacao = dict(especialistas.get('deliberacao') or {})
    orquestrador_cooperativo = ns.get('_orquestrador_cooperativo_runtime')
    registrar_consenso = getattr(orquestrador_cooperativo, 'registrar_deliberacao_turno', None)
    if deliberacao and callable(registrar_consenso):
        try:
            publicacao_consenso = dict(registrar_consenso(deliberacao) or {})
        except Exception as erro:
            publicacao_consenso = {
                'publicado': False,
                'motivo': f'falha_publicacao:{type(erro).__name__}',
            }
            ns['print'](
                f"⚠️ [COOPERAÇÃO:CONSENSO] publicação isolada falhou: {type(erro).__name__}"
            )
        deliberacao['quadro_canonico'] = publicacao_consenso
        especialistas['deliberacao'] = deliberacao
    turno['especialistas'] = especialistas
    assunto_estruturado = ns['_atualizar_assunto_estruturado_mente'](mente_antes_turno.get('assunto_estruturado_atual') if isinstance(mente_antes_turno.get('assunto_estruturado_atual'), dict) else {}, texto, turno=turno, retrato=retrato_turno, encerramento=encerramento_assunto)
    plano = ns['_planejar_turno_mente'](texto_cognitivo, turno=turno, mente=mente_antes_turno, periodo=ns['_contexto_horario_atual']())
    # O plano nasce semanticamente da proposta final, mas sua identidade pública
    # pertence à fala original. Não confundir conteúdo operacional com RG do turno.
    plano = alinhar_identidade_plano_revisao(
        plano,
        texto_original=texto,
        texto_operacional_efetivo=texto_efetivo,
        revisao_intra_turno=revisao_intra_turno,
    )
    evidencia_habilidades_getter = ns.get('_evidencia_habilidades_turno_mente')
    if callable(evidencia_habilidades_getter):
        try:
            evidencia_habilidades = evidencia_habilidades_getter(texto_cognitivo, turno=turno)
        except Exception:
            evidencia_habilidades = {}
        if isinstance(evidencia_habilidades, dict):
            plano['evidencia_capacidades'] = dict(evidencia_habilidades)
    plano['fundamentacao_factual'] = fundamentacao_factual
    plano['atualidade_factual'] = atualidade_factual
    plano['deliberacao_habilidades'] = dict(especialistas.get('deliberacao') or {})
    mensagens_recentes = list(
        getattr(ns['_estado_compartilhado_runtime'], 'memoria_conversa', {}).get('messages', [])
        or []
    )
    falas_recentes = [
        str(item.get('content') or '').strip()
        for item in mensagens_recentes
        if isinstance(item, dict) and str(item.get('role') or '').casefold() == 'assistant'
    ][-3:]
    contrato_fala = construir_contrato_semantico_fala(
        texto,
        turno=turno,
        plano=plano,
        funcao_comunicativa=funcao_comunicativa,
        mente=mente_antes_turno,
        falas_recentes=falas_recentes,
    )
    turno['contrato_fala'] = contrato_fala
    plano['contrato_fala'] = contrato_fala
    atualizacoes_turno = {'ultima_entrada_ts': ns['time'].time(), 'turno_atual': turno, 'plano_turno_atual': plano, 'contrato_fala_atual': contrato_fala, 'identidade_turno_atual': identidade_turno, 'identidade_turno_resumo': ns['_resumo_identidade_turno_mente'](identidade_turno), 'funcao_comunicativa_atual': funcao_comunicativa, 'retrato_turno_atual': retrato_turno, 'entidades_recentes': entidades_recentes, 'especialistas_turno_atual': especialistas, 'assunto_estruturado_atual': assunto_estruturado, 'registro_semantico': registro_semantico, 'fundamentacao_factual_turno': fundamentacao_factual, **limpeza_pergunta_turno}
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
                    ns['print'](f"🧠 [MEMÓRIA] correção do usuário persistida: {correcao_duravel.get('regra')}")
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
            for campo in (
                'status', 'executou', 'confirmado',
                'confirmacao_oferecida', 'evidencia_confirmacao',
            ):
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
    argumentos = {
        'plano': dict(mente.get('plano_turno_atual') or {}),
        'periodo': ns['_contexto_horario_atual'](),
        'ultima_resposta': str(mente.get('ultima_resposta') or ''),
        'origem': origem,
    }
    verificacao = ns['_verificar_fala_turno_mente'](fala, **argumentos)
    plano = dict(mente.get('plano_turno_atual') or {})
    plano['fase'] = 'fala_verificada'
    plano['ultima_verificacao'] = dict(verificacao)
    avaliacoes = list(mente.get('avaliacoes_turno') or [])
    avaliacoes.append({'plano_id': plano.get('id'), 'origem': str(origem or 'conversa'), 'pontuacao': float(verificacao.get('pontuacao') or 0.0), 'problemas': list(verificacao.get('problemas') or []), 'acao': str(verificacao.get('acao') or ''), 'ts': ns['time'].time()})
    metricas = dict(mente.get('metricas_verificador') or {})
    metricas['falas_verificadas'] = int(metricas.get('falas_verificadas') or 0) + 1
    aderencia_contrato = dict(verificacao.get('aderencia_contrato') or {})
    if aderencia_contrato.get('avaliado'):
        metricas['contratos_verificados'] = int(metricas.get('contratos_verificados') or 0) + 1
        estrategia = str(aderencia_contrato.get('estrategia') or 'resposta_direta')[:64]
        chave_estrategia = f'estrategia:{estrategia}'
        metricas[chave_estrategia] = int(metricas.get(chave_estrategia) or 0) + 1
        if not verificacao.get('aceita', True):
            metricas['contratos_rejeitados'] = int(metricas.get('contratos_rejeitados') or 0) + 1
        else:
            metricas['contratos_aprovados'] = int(metricas.get('contratos_aprovados') or 0) + 1
            if aderencia_contrato.get('problemas'):
                metricas['contratos_com_observacoes'] = int(
                    metricas.get('contratos_com_observacoes') or 0
                ) + 1
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
