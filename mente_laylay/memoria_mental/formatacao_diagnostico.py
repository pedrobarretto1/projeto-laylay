"""Normalização segura e apresentação do diagnóstico da mente."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping

def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or ""))
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base.casefold()).strip()

def _codigo_seguro(valor: Any, limite: int = 96) -> str:
    texto = _normalizar(str(valor or ""))
    texto = re.sub(r"https?://\S+|[a-z]:\\\S+|[/\\][^\s]+", "", texto)
    texto = re.sub(r"[^a-z0-9_.: -]+", "", texto)
    return re.sub(r"\s+", "_", texto).strip("_.:-")[:limite]

def formatar_diagnostico_terminal(diagnostico: Mapping[str, Any]) -> str:
    saude = dict(diagnostico.get("saude") or {})
    saude_estrutural = dict(diagnostico.get("saude_estrutural") or saude)
    saude_operacional = dict(diagnostico.get("saude_operacional") or {})
    interacao = dict(diagnostico.get("interacao") or {})
    turno = dict(diagnostico.get("turno") or {})
    contrato_fala = dict(diagnostico.get("contrato_fala") or {})
    verificador_fala = dict(diagnostico.get("verificador_fala") or {})
    acao = dict(diagnostico.get("ultima_acao") or {})
    acao_auditoria = dict(diagnostico.get("ultima_acao_auditoria") or {})
    continuidade = dict(diagnostico.get("continuidade_geral") or {})
    problemas = list(saude.get("problemas") or [])
    latencias = dict(diagnostico.get("latencias") or {})
    tamanhos_prompt = dict(diagnostico.get("tamanhos_prompt") or {})
    orcamento_prompt = dict(diagnostico.get("orcamento_prompt") or {})
    pendencias_detalhadas = list(diagnostico.get("pendencias_detalhadas") or [])
    falhas = list(diagnostico.get("falhas_recentes") or [])
    falhas_recuperadas = int(diagnostico.get("falhas_recuperadas") or 0)
    falhas_por_classe = dict(diagnostico.get("falhas_por_classe") or {})
    servicos_background = list(diagnostico.get("servicos_background") or [])
    decisoes = list(diagnostico.get("decisoes_recentes") or [])
    iniciativa = dict(diagnostico.get("iniciativa") or {})
    rede = dict(diagnostico.get("rede_associativa") or {})
    habilidades = dict(diagnostico.get("habilidades") or {})
    pesquisa_arquivos = dict(diagnostico.get("pesquisa_arquivos") or {})
    mutacoes_arquivos = dict(diagnostico.get("mutacoes_arquivos") or {})
    musica_leitura = dict(diagnostico.get("musica_leitura") or {})
    musica_operacoes = dict(diagnostico.get("musica_operacoes") or {})
    navegador_leitura = dict(diagnostico.get("navegador_leitura") or {})
    navegador_operacoes = dict(diagnostico.get("navegador_operacoes") or {})
    visao_jogo_leitura = dict(diagnostico.get("visao_jogo_leitura") or {})
    visao_jogo_analise = dict(diagnostico.get("visao_jogo_analise") or {})
    conversa_llm = dict(diagnostico.get("conversa_llm") or {})
    composicao_principal = dict(diagnostico.get("composicao_principal") or {})
    cooperacao = dict(diagnostico.get("orquestracao_cooperativa") or {})
    agenda = dict(diagnostico.get("agenda") or {})
    pessoas = dict(diagnostico.get("memoria_pessoas") or {})
    aprendizado = dict(diagnostico.get("memoria_aprendizado") or {})
    linguagem_natural = dict(diagnostico.get("linguagem_natural") or {})
    fala_operacional = dict(diagnostico.get("fala_operacional") or {})
    pendencia_acao = dict(diagnostico.get("pendencia_acao") or {})
    protecoes_ciclo = dict(diagnostico.get("protecoes_ciclo") or {})
    linhas = [
        "🩺 [DIAGNÓSTICO:MENTE]",
        (
            f"  módulos: saudáveis={saude_estrutural.get('saudavel', 0)} "
            f"degradados={saude_estrutural.get('degradado', 0)} "
            f"indisponíveis={saude_estrutural.get('indisponivel', 0)} "
            "(saúde estrutural)"
        ),
        (
            f"  operação observada: estado={saude_operacional.get('estado') or 'sem_amostras'} "
            f"amostras={int(saude_operacional.get('amostras_passivas') or 0)} "
            f"falhas_impactantes={int(saude_operacional.get('falhas_impactantes') or 0)} "
            f"serviços_degradados={int(saude_operacional.get('servicos_degradados') or 0)} "
            f"problemas_fala_atual={int(saude_operacional.get('problemas_fala_atual') or 0)} "
            f"probes={bool(saude_operacional.get('probes_executados'))}"
        ),
        (
            f"  interação: emoção={interacao.get('emocao')} nível={interacao.get('nivel')} "
            f"fala_reservada={interacao.get('fala_reservada')} áudio={interacao.get('audio_reproduzindo')}"
        ),
        (
            f"  turno: fase={turno.get('fase')} modalidade={turno.get('modalidade') or '-'} "
            f"origem={turno.get('origem') or '-'} "
            f"execução_autorizada={turno.get('autoriza_execucao')}"
        ),
        (
            f"  contrato de fala: ativo={bool(contrato_fala.get('ativo'))} "
            f"função={contrato_fala.get('funcao') or '-'} "
            f"atos={','.join(contrato_fala.get('atos') or []) or '-'} "
            f"referente={contrato_fala.get('referente') or '-'} "
            f"máximo_frases={int(contrato_fala.get('max_frases') or 0)} "
            f"metáfora={bool(contrato_fala.get('permite_metafora'))} "
            f"geração={contrato_fala.get('estrategia_concreta') or '-'} "
            f"núcleo_primeiro={bool(contrato_fala.get('primeira_frase_responde_nucleo'))} "
            f"cooperação={bool(contrato_fala.get('cooperacao_considerada'))} "
            "autoriza_execução=False"
        ),
        (
            "  verificador de fala: "
            f"contratos={int(verificador_fala.get('contratos_verificados') or 0)} "
            f"aprovados={int(verificador_fala.get('contratos_aprovados') or 0)} "
            f"rejeitados={int(verificador_fala.get('contratos_rejeitados') or 0)} "
            f"última_estratégia={verificador_fala.get('ultima_estrategia') or '-'} "
            f"núcleo_atendido={bool(verificador_fala.get('ultimo_nucleo_atendido'))} "
            f"problemas={','.join(verificador_fala.get('ultimos_problemas') or []) or '-'} "
            "autoriza_execução=False"
        ),
        (
            f"  última ação: intent={acao.get('intent') or '-'} alvo={acao.get('alvo') or '-'} "
            f"status={acao.get('status') or '-'} confirmada={acao.get('confirmado')} "
            f"domínio={acao_auditoria.get('dominio') or '-'} "
            f"fonte={acao_auditoria.get('fonte') or '-'} "
            f"coerente={bool(acao_auditoria.get('coerente'))}"
        ),
        (
            f"  continuidade geral: modo={continuidade.get('modo') or 'oficial'} "
            f"oficial={bool(continuidade.get('fonte_autoritativa', True))} "
            f"domínio_ativo={continuidade.get('dominio_ativo') or '-'} "
            f"domínios={int(continuidade.get('dominios') or 0)}"
        ),
        f"  pendências contextuais: {diagnostico.get('pendencias', 0)}",
        (
            f"  iniciativa: modo={iniciativa.get('modo') or 'sombra'} "
            f"avaliadas={int(iniciativa.get('avaliadas') or 0)} "
            f"duplicadas={int(iniciativa.get('duplicadas') or 0)}"
        ),
        (
            f"  rede associativa: modo={rede.get('modo') or 'desligado'} "
            f"influência={bool(rede.get('influencia_habilitada', False))} "
            f"nós={int(rede.get('nos') or 0)} conexões={int(rede.get('conexoes') or 0)} "
            f"ativações={int(rede.get('ativacoes') or 0)} fila={int(rede.get('fila') or 0)} "
            f"duplicados={int(rede.get('duplicados') or 0)} "
            f"comparações={int(rede.get('comparacoes_sombra') or 0)} "
            f"candidatos={int(rede.get('candidatos_sombra') or 0)} "
            f"feedbacks={int(rede.get('feedbacks') or 0)} "
            f"plasticidade={int(rede.get('ajustes_plasticidade') or 0)}/"
            f"{int(rede.get('plasticidade_amostras') or 0)} "
            f"continuidade={int(rede.get('influencias_continuidade') or 0)}/"
            f"{int(rede.get('sinais_continuidade') or 0)} "
            f"falhas={int(rede.get('falhas') or 0)}"
        ),
    ]
    if pendencia_acao.get("ativa"):
        linhas.insert(
            6,
            "  pendência de ação: "
            f"origem={pendencia_acao.get('origem') or '-'} "
            f"ação={pendencia_acao.get('acao') or '-'} "
            f"status={pendencia_acao.get('status') or '-'}",
        )
    for pendencia in pendencias_detalhadas[:8]:
        idade = (
            f"{float(pendencia.get('idade_s')):.1f}s"
            if pendencia.get("idade_s") is not None else "desconhecida"
        )
        prazo = (
            f"{float(pendencia.get('prazo_s')):.1f}s"
            if pendencia.get("prazo_s") is not None else "sem_prazo"
        )
        linhas.insert(
            7,
            "  pendência: "
            f"origem={pendencia.get('origem') or '-'} "
            f"ação={pendencia.get('acao') or '-'} idade={idade} prazo={prazo} "
            f"motivo={pendencia.get('motivo') or '-'} "
            f"status={pendencia.get('status') or '-'}",
        )
    if habilidades:
        linhas.append(
            "  mapa de habilidades: "
            f"catalogadas={int(habilidades.get('catalogadas') or 0)} "
            f"disponíveis={int(habilidades.get('disponiveis') or 0)} "
            f"indisponíveis={int(habilidades.get('indisponiveis') or 0)} "
            f"observações={int(habilidades.get('observacoes_ativas') or 0)} "
            "autoriza_execução=False"
        )
    if linguagem_natural:
        linhas.append(
            "  linguagem natural: "
            f"modo={linguagem_natural.get('modo') or 'coordenador_canonico'} "
            f"tentativas={int(linguagem_natural.get('tentativas') or 0)} "
            f"resolvidas={int(linguagem_natural.get('resolvidas') or 0)} "
            f"sem_intenção={int(linguagem_natural.get('sem_intencao') or 0)} "
            f"reusos_turno={int(linguagem_natural.get('reutilizadas_no_turno') or 0)} "
            f"última={linguagem_natural.get('ultima_intent') or '-'} "
            f"rota={linguagem_natural.get('ultima_rota') or '-'} "
            "autoriza_execução=False"
        )
        tolerancia = dict(linguagem_natural.get("tolerancia_portugues") or {})
        if tolerancia:
            linhas.append(
                "  tolerância de português: "
                f"modo={tolerancia.get('modo') or 'operacional_conservador'} "
                f"normalizações={int(tolerancia.get('normalizacoes') or 0)} "
                f"entradas_corrigidas={int(tolerancia.get('entradas_corrigidas') or 0)} "
                f"substituições={int(tolerancia.get('substituicoes') or 0)} "
                "únicas_turno="
                f"{int(tolerancia.get('normalizacoes_unicas_turno') or 0)} "
                "reaplicações="
                f"{int(tolerancia.get('reaplicacoes_identicas') or 0)} "
                "aproxima_argumentos=False autoriza_execução=False"
            )
        nao_resolvida = dict(linguagem_natural.get("ultima_nao_resolvida") or {})
        if nao_resolvida:
            linhas.append(
                "  intenção natural não resolvida: "
                f"motivo={nao_resolvida.get('motivo') or '-'} "
                f"moldura={nao_resolvida.get('moldura') or '-'} "
                f"rota={nao_resolvida.get('rota') or '-'} "
                f"parecia_operacional={bool(nao_resolvida.get('parecia_operacional'))} "
                "conteúdo_exposto=False"
            )
        execucao_turno = dict(linguagem_natural.get("execucao_turno") or {})
        if execucao_turno:
            linhas.append(
                "  idempotência do turno: "
                f"iniciadas={int(execucao_turno.get('iniciadas') or 0)} "
                f"reutilizadas={int(execucao_turno.get('reutilizadas') or 0)} "
                f"aguardadas={int(execucao_turno.get('aguardadas') or 0)} "
                f"ativas={int(execucao_turno.get('ativas') or 0)} "
                f"timeouts={int(execucao_turno.get('timeouts') or 0)} "
                f"falhas={int(execucao_turno.get('falhas') or 0)}"
            )
    if fala_operacional:
        linhas.append(
            "  voz operacional única: "
            f"tentativas={int(fala_operacional.get('tentativas') or 0)} "
            f"emitidas={int(fala_operacional.get('emitidas') or 0)} "
            f"duplicadas_suprimidas={int(fala_operacional.get('duplicadas_suprimidas') or 0)} "
            f"reservadas={int(fala_operacional.get('reservadas') or 0)} "
            f"rejeitadas={int(fala_operacional.get('rejeitadas_voz') or 0)} "
            "autoriza_execução=False"
        )
        emocao_causal = dict(fala_operacional.get("emocao_causal") or {})
        if emocao_causal:
            ultima_causa = dict(emocao_causal.get("ultima") or {})
            linhas.append(
                "  emoção causal operacional: "
                f"avaliados={int(emocao_causal.get('avaliados') or 0)} "
                f"expressões={int(emocao_causal.get('expressoes') or 0)} "
                f"contenções={int(emocao_causal.get('contencoes') or 0)} "
                f"decisão={_codigo_seguro(emocao_causal.get('ultima_decisao_expressao'), 12)} "
                f"motivo={_codigo_seguro(ultima_causa.get('motivo_expressao'), 38)} "
                f"responsabilidade={_codigo_seguro(ultima_causa.get('responsabilidade'), 16)} "
                f"confiança={round(float(ultima_causa.get('confianca') or 0.0) * 100):.0f}% "
                f"emoção={_codigo_seguro(ultima_causa.get('emocao'), 16)} "
                "autoriza_execução=False persistência_pessoal=False"
            )
    if protecoes_ciclo:
        linhas.append(
            "  proteções do ciclo: "
            f"reentradas_evitadas={int(protecoes_ciclo.get('reentradas_evitadas') or 0)} "
            "execuções_duplicadas_convergidas="
            f"{int(protecoes_ciclo.get('execucoes_duplicadas_convergidas') or 0)} "
            "falas_duplicadas_suprimidas="
            f"{int(protecoes_ciclo.get('falas_duplicadas_suprimidas') or 0)} "
            f"órfãos_atuais={int(protecoes_ciclo.get('servicos_orfaos_atuais') or 0)} "
            f"órfãos_detectados={int(protecoes_ciclo.get('servicos_orfaos_detectados') or 0)}"
        )
    if pesquisa_arquivos:
        linhas.append(
            "  pesquisa de arquivos: "
            f"indexados={int(pesquisa_arquivos.get('arquivos_indexados') or 0)} "
            f"pesquisas={int(pesquisa_arquivos.get('pesquisas') or 0)} "
            f"cache={bool(pesquisa_arquivos.get('cache_ativo'))} "
            f"índice_incompleto={bool(pesquisa_arquivos.get('indice_incompleto'))} "
            f"falhas={int(pesquisa_arquivos.get('falhas') or 0)} "
            "somente_leitura=True envio_externo=False"
        )
    if mutacoes_arquivos:
        linhas.append(
            "  mutações de arquivos: "
            f"raízes_autorizadas={bool(mutacoes_arquivos.get('somente_raizes_autorizadas'))} "
            f"escrita_segura={bool(mutacoes_arquivos.get('escrita_segura_disponivel'))} "
            f"lixeira_reversível={bool(mutacoes_arquivos.get('lixeira_reversivel'))} "
            "confirmação_pendente="
            f"{bool(mutacoes_arquivos.get('confirmacao_exclusao_pendente'))}"
        )
    if musica_leitura:
        linhas.append(
            "  leitura musical: "
            f"playlists={int(musica_leitura.get('playlists_usuario') or 0)} "
            f"curadorias_laylay={int(musica_leitura.get('playlists_laylay') or 0)} "
            f"histórico_na_curadoria={bool(musica_leitura.get('curadoria_usa_historico'))} "
            f"cooperação={bool(musica_leitura.get('curadoria_cooperativa'))} "
            f"falhas_curadoria={int(musica_leitura.get('curadoria_falhas') or 0)} "
            f"playlist_ativa={bool(musica_leitura.get('playlist_ativa'))} "
            f"estado_disponível={bool(musica_leitura.get('estado_disponivel'))} "
            "somente_leitura=True expõe_urls=False"
        )
    if musica_operacoes:
        linhas.append(
            "  operações musicais: "
            f"mutação={bool(musica_operacoes.get('mutacao_disponivel'))} "
            f"reprodução={bool(musica_operacoes.get('reproducao_disponivel'))} "
            f"auto_next={bool(musica_operacoes.get('auto_next_disponivel'))} "
            f"curadoria={bool(musica_operacoes.get('curadoria_disponivel'))} "
            f"playlist_ativa={bool(musica_operacoes.get('playlist_ativa'))}"
        )
    if navegador_leitura or navegador_operacoes:
        linhas.append(
            "  navegador tipado: "
            f"conectado={bool(navegador_leitura.get('conectado'))} "
            f"leitura_aba={bool(navegador_leitura.get('leitura_aba_disponivel'))} "
            f"listagem={bool(navegador_leitura.get('listagem_disponivel'))} "
            f"navegação={bool(navegador_operacoes.get('navegacao_disponivel'))} "
            f"comandos={bool(navegador_operacoes.get('comandos_disponiveis'))} "
            "expõe_urls=False autoriza_execução=False"
        )
    if visao_jogo_leitura or visao_jogo_analise:
        linhas.append(
            "  visão de jogo tipada: "
            f"habilitada={bool(visao_jogo_leitura.get('habilitado'))} "
            f"credencial={bool(visao_jogo_leitura.get('credencial_disponivel'))} "
            f"em_andamento={bool(visao_jogo_leitura.get('em_andamento'))} "
            f"recente={bool(visao_jogo_leitura.get('analise_recente'))} "
            f"análise={bool(visao_jogo_analise.get('analise_disponivel'))} "
            f"continuidade={bool(visao_jogo_analise.get('continuidade_disponivel'))} "
            f"falhas={int(visao_jogo_analise.get('falhas') or 0)} "
            "captura_persistida=False imagem_exposta=False "
            "autoriza_execução=False"
        )
    if conversa_llm:
        linhas.append(
            "  conversa e LLM tipadas: "
            f"prompt={bool(conversa_llm.get('prompt_disponivel'))} "
            f"modelo={bool(conversa_llm.get('modelo_disponivel'))} "
            f"estado={bool(conversa_llm.get('estado_disponivel'))} "
            f"requisições={int(conversa_llm.get('requisicoes') or 0)} "
            f"falhas={int(conversa_llm.get('falhas') or 0)} "
            "memória_exposta=False credencial_exposta=False "
            f"contratos_rápidos={int(conversa_llm.get('prompts_rapidos') or 0)} "
            f"consecutivas={int(conversa_llm.get('falhas_consecutivas') or 0)} "
            f"saúde_backend={conversa_llm.get('estado') or 'desconhecida'} "
            "autoriza_execução=False"
        )
    if composicao_principal:
        linhas.append(
            "  composição principal: "
            f"disponível={bool(composicao_principal.get('disponivel'))} "
            f"registros={int(composicao_principal.get('quantidade') or 0)} "
            f"namespace_global={bool(composicao_principal.get('namespace_global'))} "
            "credencial_exposta=False autoriza_execução=False"
        )
    if cooperacao:
        linhas.append(
            "  orquestração cooperativa: "
            f"modo={cooperacao.get('modo') or 'sombra'} "
            f"eventos={int(cooperacao.get('eventos') or 0)} "
            f"planos={int(cooperacao.get('planos') or 0)} "
            f"confirmados={int(cooperacao.get('confirmados') or 0)} "
            f"falhas={int(cooperacao.get('falhas') or 0)} "
            f"parciais={int(cooperacao.get('falhas_parciais') or 0)} "
            f"dependências_bloqueadas={int(cooperacao.get('dependencias_bloqueadas') or 0)} "
            f"orçamentos_excedidos={int(cooperacao.get('orcamentos_excedidos') or 0)} "
            f"cancelamentos={int(cooperacao.get('cancelamentos_solicitados') or 0)} "
            f"autorizações_bloqueadas={int(cooperacao.get('autorizacoes_bloqueadas') or 0)} "
            f"ciclos_finalizados={int(cooperacao.get('finalizacoes_governanca') or 0)} "
            f"ativos={int(cooperacao.get('planos_ativos') or 0)} "
            f"referências_ativas={int(cooperacao.get('referencias_ativas') or 0)}"
        )
    if agenda:
        linhas.append(
            "  agenda: "
            f"disponível={bool(agenda.get('disponivel'))} "
            f"daemon={bool(agenda.get('daemon_ativo'))} "
            f"ativos={int(agenda.get('agendamentos_ativos') or 0)} "
            f"gravações={int(agenda.get('gravacoes') or 0)} "
            f"falhas_persistência={int(agenda.get('falhas_persistencia') or 0)} "
            f"disparos={int(agenda.get('disparos_confirmados') or 0)} "
            f"retries={int(agenda.get('retries') or 0)} "
            "conteúdo_exposto=False autoriza_execução=False"
        )
    if pessoas:
        linhas.append(
            "  memória de pessoas: "
            f"ativas={int(pessoas.get('ativas') or 0)} "
            f"relações={int(pessoas.get('relacoes_ativas') or 0)} "
            f"fatos={int(pessoas.get('fatos_ativos') or 0)} "
            f"correções={int(pessoas.get('correcoes') or 0)} "
            f"esquecimentos={int(pessoas.get('esquecimentos') or 0)} "
            f"ambiguidades={int(pessoas.get('ambiguidades') or 0)} "
            f"falhas={int(pessoas.get('falhas') or 0)} "
            "persistência_local=True envio_externo=False"
        )
    if aprendizado:
        semanticos = dict(aprendizado.get("semanticos") or {})
        hipoteses = dict(aprendizado.get("hipoteses") or {})
        linhas.append(
            "  memória e aprendizado: "
            f"disponível={bool(aprendizado.get('disponivel'))} "
            f"semânticos_ativos={int(semanticos.get('ativo') or 0)} "
            f"não_verificados={int(semanticos.get('nao_verificado') or 0)} "
            f"contraditos={int(semanticos.get('contradito') or 0)} "
            f"hipóteses_ativas={int(hipoteses.get('ativa') or 0)} "
            f"candidatas={int(hipoteses.get('candidata') or 0)} "
            f"enfraquecidas={int(hipoteses.get('enfraquecida') or 0)} "
            f"legados={int(aprendizado.get('legados') or 0)} "
            "persistência_local=True conteúdo_exposto=False autoriza_execução=False"
        )
    ultima_iniciativa = dict(iniciativa.get("ultima") or {})
    if ultima_iniciativa:
        linhas.append(
            f"  última iniciativa: {ultima_iniciativa.get('tipo') or '-'} "
            f"decisão={ultima_iniciativa.get('decisao') or '-'} "
            f"pontuação={int(ultima_iniciativa.get('pontuacao') or 0)} "
            f"confiança={float(ultima_iniciativa.get('confianca') or 0.0):.0%} "
            f"risco={ultima_iniciativa.get('risco') or '-'}"
        )
    coordenacao = dict(iniciativa.get("coordenacao") or {})
    if coordenacao.get("recebidas"):
        linhas.append(
            "  coordenação de oportunidades: "
            f"recebidas={int(coordenacao.get('recebidas') or 0)} "
            f"encaminhadas={int(coordenacao.get('encaminhadas') or 0)} "
            f"agrupadas={int(coordenacao.get('duplicadas') or 0)} "
            f"baixa_confiança={int(coordenacao.get('baixa_confianca') or 0)} "
            f"alinhadas_objetivo={int(coordenacao.get('alinhadas_objetivo') or 0)} "
            f"feedbacks={int(coordenacao.get('feedbacks') or 0)} "
            f"perfis_maduros={int(coordenacao.get('perfis_maduros') or 0)}"
        )
    presenca = dict(iniciativa.get("presenca") or {})
    linhas.append(
            "  presença autônoma: "
            f"perfil={presenca.get('perfil') or 'adaptativo'} "
            f"motivo={presenca.get('motivo_perfil') or 'inicio'} "
            f"recebidas={int(presenca.get('recebidas') or 0)} "
            f"emitidas={int(presenca.get('emitidas') or 0)} "
            f"bloqueadas_contexto={int(presenca.get('bloqueadas_contexto') or 0)} "
            f"bloqueadas_orçamento={int(presenca.get('bloqueadas_orcamento') or 0)} "
            f"bloqueadas_qualidade={int(presenca.get('bloqueadas_qualidade') or 0)}"
        )
    auditoria = dict(iniciativa.get("auditoria") or {})
    linhas.append(
        f"  auditoria da iniciativa: status={auditoria.get('status') or 'sem_amostras'} "
        f"amostras={int(auditoria.get('amostras') or 0)} "
        f"domínios_candidatos={int(auditoria.get('dominios_candidatos') or 0)} "
        f"duplicação={float(auditoria.get('taxa_duplicacao') or 0.0):.1%} "
        "execução_autorizada=False"
    )
    permissoes = dict(iniciativa.get("permissoes") or {})
    if permissoes:
        linhas.append(
            "  permissões da autonomia: "
            + ", ".join(f"{dominio}={nivel}" for dominio, nivel in sorted(permissoes.items()))
        )
    vontade = dict(iniciativa.get("vontade_segura") or {})
    if vontade:
        linhas.append(
            "  vontade segura: "
            f"modo={vontade.get('modo') or 'vontade_segura'} "
            f"capacidade_bloqueada={int(vontade.get('bloqueios_capacidade') or 0)} "
            f"confirmação_exigida={int(vontade.get('bloqueios_confirmacao') or 0)} "
            f"orçamento_bloqueado={int(vontade.get('bloqueios_orcamento') or 0)} "
            f"simulações={int(vontade.get('simulacoes_orcamento') or 0)} "
            "execução_autorizada=False"
        )
    if latencias:
        resumo_latencias = []
        for nome, metrica in sorted(latencias.items()):
            alerta = " ⚠" if metrica.get("excedeu_orcamento") else ""
            resumo_latencias.append(
                f"{nome}={float(metrica.get('ultimo_ms') or 0.0):.0f}ms"
                f" (média {float(metrica.get('media_ms') or 0.0):.0f}ms/{int(metrica.get('amostras') or 0)})"
                f"{alerta}"
            )
        linhas.append("  latências: " + " | ".join(resumo_latencias))
    if tamanhos_prompt:
        resumo_prompts = [
            f"{nome}={int(metrica.get('ultimo_chars') or 0)} chars"
            for nome, metrica in sorted(tamanhos_prompt.items())
        ]
        linhas.append("  prompts: " + " | ".join(resumo_prompts))
    etapas_prompt = dict(orcamento_prompt.get("etapas") or {})
    for etapa, metrica in sorted(etapas_prompt.items()):
        linhas.append(
            f"  orçamento do prompt ({etapa}): "
            f"brutos={int(metrica.get('brutos') or 0)} "
            f"selecionados={int(metrica.get('selecionados') or 0)} "
            f"truncados={int(metrica.get('truncados') or 0)} "
            f"injetados={int(metrica.get('injetados') or 0)} "
            f"enviados={int(metrica.get('enviados') or 0)} "
            f"fecha_seleção={bool(metrica.get('fecha_selecao'))} "
            f"fecha_envio={bool(metrica.get('fecha_envio'))}"
        )
    if decisoes:
        ultima = decisoes[-1]
        motivos = ",".join(ultima.get("motivos") or []) or "sem_motivo"
        linhas.append(
            f"  decisão recente: {ultima.get('componente') or '-'}={ultima.get('acao') or '-'} "
            f"categoria={ultima.get('categoria') or '-'} motivo={motivos}"
        )
    if servicos_background:
        ativos = sum(1 for item in servicos_background if item.get("classe_estado") == "ativos")
        desativados = sum(1 for item in servicos_background if item.get("classe_estado") == "desativados")
        encerrados = sum(1 for item in servicos_background if item.get("classe_estado") == "encerrados")
        degradados = sum(1 for item in servicos_background if item.get("classe_estado") == "degradados")
        quedas = sum(int(item.get("quedas") or 0) for item in servicos_background)
        reinicios = sum(int(item.get("reinicios") or 0) for item in servicos_background)
        orfaos = sum(int(item.get("orfaos") or 0) for item in servicos_background)
        linhas.append(
            "  serviços de fundo: "
            f"total={len(servicos_background)} ativos={ativos} degradados={degradados} "
            f"quedas={quedas} reinícios={reinicios} órfãos={orfaos} "
            f"desativados={desativados} encerrados={encerrados}"
        )
        for servico in servicos_background:
            if servico.get("classe_estado") != "degradados":
                continue
            linhas.append(
                f"  serviço: {servico.get('nome') or '-'}={servico.get('estado') or '-'} "
                f"tentativa={int(servico.get('tentativa') or 0)} "
                f"fallback={servico.get('fallback') or 'nenhum'}"
            )
    linhas.append(
        f"  falhas técnicas recentes: {len(falhas)} "
        f"(esperadas={int(falhas_por_classe.get('esperada') or 0)} "
        f"degradações={int(falhas_por_classe.get('degradacao') or 0)} "
        f"defeitos={int(falhas_por_classe.get('defeito') or 0)} "
        f"não_classificadas={int(falhas_por_classe.get('nao_classificada') or 0)} "
        f"recuperadas={falhas_recuperadas})"
    )
    for falha in falhas[-5:]:
        linhas.append(
            f"  falha: {falha.get('componente') or '-'}={falha.get('codigo') or '-'} "
            f"classe={falha.get('classe') or '-'} impacto={falha.get('impacto') or '-'} "
            f"fallback={falha.get('fallback') or 'nenhum'} tipo={falha.get('tipo') or '-'}"
        )
    for problema in problemas:
        ausentes = ",".join(problema.get("ausentes") or []) or "sem detalhe"
        linhas.append(f"  atenção: {problema.get('modulo')}={problema.get('status')} ({ausentes})")
    return "\n".join(linhas)

