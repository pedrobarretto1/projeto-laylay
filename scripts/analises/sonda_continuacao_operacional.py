"""Continuidade no detector/coordenador instalados; sem executar efeitos ou IA."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from scripts.analises.sonda_escopo_propostas_mistas import RAIZ, preparar_instalacao_isolada


def coletar_politica_voz_instalada(root) -> dict:
    """Fila/player externos isolados; método de reprodução instalado é real."""
    voz = root._voz_runtime
    nomes = ("_sintetizar_edge", "fallback_pyttsx", "registrar_falha_cb")
    originais = {nome: getattr(voz, nome) for nome in nomes}
    locais, falhas = [], []
    try:
        def indisponivel(*_a, **_k):
            raise RuntimeError("falha de síntese injetada, sem rede")
        voz._sintetizar_edge = indisponivel
        voz.fallback_pyttsx = lambda *_a: locais.append(True) or True
        voz.registrar_falha_cb = lambda *a, **k: falhas.append({"dominio": a[0],
            "evento": a[1], "fallback": k.get("fallback")})
        sucesso = voz.reproduzir_fala("Resposta textual do diagnóstico de voz.", "calma", 1)
        return {"identidade": voz.voice, "reservas": list(voz.fallback_voices),
            "fallback_local_permitido": voz.permitir_fallback_local,
            "sucesso_audio": sucesso, "chamadas_voz_local": len(locais),
            "falhas": falhas, "metodo_instalado": True,
            "sintese_real": False, "reproducao_fisica": False}
    finally:
        for nome, valor in originais.items():
            setattr(voz, nome, valor)


def coletar_instalado(pasta: Path, *, contraprova_prioridade: bool = False, painel_contexto: bool = False,
                      sondar_executor: bool = False, painel_ajustes: bool = False) -> dict:
    from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    root = preparar_instalacao_isolada(pasta)
    if contraprova_prioridade:
        # Somente neste subprocesso: retirar o consumo prioritário, mantendo
        # o owner contextual. Não é replay de HEAD nem candidato de produção.
        from mente_laylay.autonomia import orquestrador_deterministico as detector
        detector.resolver_continuacao_operacional_confirmada = lambda *_a, **_k: None
        detector.texto_pede_ajuste_parametrico_contextual = lambda *_a, **_k: False
    ciclo = root._composicao_ciclo_comandos_runtime.ciclo
    chamadas_modelo = []
    # Porta não consultará rede nem gerará comandos para compensar o detector.
    ciclo.tentar_intencao_ai_primeiro = lambda texto: chamadas_modelo.append(texto) or None
    resultados = []
    casos = [
        ("relato", "coloca em 40", "vigente", "VOLUME", 40),
        ("outro_nivel", "coloca em 25", "vigente", "VOLUME", 25),
        ("outro_verbo", "deixa em 40", "vigente", "VOLUME", 40),
        ("controle_explicito", "coloca o volume em 40", "vigente", "VOLUME", 40),
        ("vencido", "coloca em 40", "vencido", "", None),
        ("nao_confirmado", "coloca em 40", "nao_confirmado", "", None),
        ("pergunta", "como coloca em 40", "vigente", "", None),
        ("negacao", "não coloca em 40", "vigente", "", None),
        ("titulo_numerico", "coloca a música adolescente de 40 anos", "vigente", "MUSIC_SEARCH", None),
        ("aumento_destino", "aumenta para 100", "vigente", "VOLUME", 100),
        ("reducao_destino", "abaixa pra 40", "vigente", "VOLUME", 40),
        ("direcional_vencido", "aumenta para 100", "vencido", "", None),
        ("direcional_nao_confirmado", "aumenta para 100", "nao_confirmado", "", None),
        ("direcional_negacao", "não aumenta para 100", "vigente", "", None),
        ("direcional_pergunta", "como eu faria para aumentar para 100?", "vigente", "", None),
        ("extenso_atribuicao", "coloca em quarenta", "vigente", "VOLUME", 40),
        ("extenso_composto", "deixa em vinte e dois", "vigente", "VOLUME", 22),
        ("extenso_destino", "aumenta para cem", "vigente", "VOLUME", 100),
        ("extenso_reducao", "reduza pra trinta e cinco", "vigente", "VOLUME", 35),
        ("extenso_percentual", "coloca em quarenta por cento", "vigente", "VOLUME", 40),
        ("extenso_maiuscula", "Coloca em Três", "vigente", "VOLUME", 3),
        ("extenso_vencido", "coloca em quarenta", "vencido", "", None),
        ("extenso_nao_confirmado", "coloca em quarenta", "nao_confirmado", "", None),
        ("extenso_negacao", "não coloca em quarenta", "vigente", "", None),
        ("extenso_pergunta", "como eu faria para colocar em quarenta?", "vigente", "", None),
        ("extenso_literal", 'toca a música "Quarenta e Dois"', "vigente", "MUSIC_SEARCH", None),
        ("invalido_composto", "coloca em quarenta e onze", "vigente", "", None),
        ("invalido_decimal", "coloca em 5.5", "vigente", "", None),
        ("invalido_decimal_virgula", "coloca em 5,5", "vigente", "", None),
        ("invalido_unidade", "coloca em quarenta minutos", "vigente", "", None),
        ("invalido_misto", "coloca em 40 e cinco", "vigente", "", None),
        ("invalido_sem_relacao", "coloca 5.5", "vigente", "", None),
        ("invalido_vencido", "coloca em quarenta e onze", "vencido", "", None),
        ("invalido_nao_confirmado", "coloca em quarenta minutos", "nao_confirmado", "", None),
        ("literal_quantidade", 'coloca "Em Quarenta e Onze"', "vigente", "MUSIC_SEARCH", None),
        ("literal_decimal", 'coloca "Em 5.5"', "vigente", "MUSIC_SEARCH", None),
        ("musica_unidade", "coloca a música quarenta minutos", "vigente", "MUSIC_SEARCH", None),
        ("artigo_titulo", "coloca em um lugar ao sol", "vigente", "MUSIC_SEARCH", None),
        ("agenda_parametro", "coloca em 40 daqui 5 minutos", "vigente", "AGENDAR_ACAO", None),
        ("agenda_outro_dominio", "abre a calculadora daqui 5 minutos", "vigente", "AGENDAR_ACAO", None),
        ("conector_midia", "e pausa a musica", "vigente", "MEDIA_CONTROL", None),
        ("conector_iot", "e liga o ventilador", "vigente", "IOT_CONTROL", None),
        ("conector_app", "e abre a calculadora", "vigente", "APP_OPEN", None),
        ("conector_volume", "e coloca o volume em 40", "vigente", "VOLUME", 40),
        ("conector_site", "e abre o site github", "vigente", "OPEN_URL", None),
        ("conector_literal", 'e toca a música "E Hoje"', "vigente", "MUSIC_SEARCH", None),
        ("conector_negacao", "e não liga o ventilador", "vigente", "", None),
        ("conector_pergunta", "e como eu faria para ligar a luz?", "vigente", "", None),
        ("conector_condicao", "e quando eu confirmar, abre a calculadora", "vigente", "", None),
        ("conector_capacidade", "e você pode abrir a calculadora?", "vigente", "", None),
        ("conector_elipse", "e coloca em 40", "vigente", "VOLUME", 40),
        ("conector_destino", "e aumenta para 100", "vigente", "VOLUME", 100),
        ("conector_elipse_vencida", "e coloca em 40", "vencido", "", None),
        ("conector_invalido_decimal", "e coloca em 5.5", "vigente", "", None),
    ]
    antecedentes = {}
    if painel_contexto:
        # Gold diagnóstico, nunca injetado no detector/coordenador. Os mesmos
        # callbacks instalados recebem diferentes domínios e pedidos atuais.
        casos = []
        for dominio, primeiro, intent, alvo, status, params, pedidos in [
            ("app", "abre a calculadora", "APP_OPEN", "calculadora", "aberto",
             {"nome_app": "calculadora"}, [
                 ("pronome", "fecha ele", "CLOSE_APP", {"nome_app": "calculadora"}),
                 ("novo_alvo", "abre o bloco de notas de novo", "APP_OPEN", {"nome_app": "bloco de notas"}),
                 ("troca_dominio", "abre o site github de novo", "OPEN_URL", {"alvo": "github"}),
                 ("explicito", "fecha o bloco de notas", "CLOSE_APP", {"nome_app": "bloco de notas"}),
                 ("negacao", "não fecha ele", "", {}),
                 ("pergunta", "como eu faria para fechar ele?", "", {}),
             ]),
            ("site", "abre o site youtube", "OPEN_URL", "youtube", "aberto",
             {"alvo": "youtube"}, [
                 ("pronome", "fecha essa", "CLOSE_TAB", {"alvo": "youtube"}),
                 ("novo_alvo", "abre o site github de novo", "OPEN_URL", {"alvo": "github"}),
                 ("troca_dominio", "abre a calculadora de novo", "APP_OPEN", {"nome_app": "calculadora"}),
                 ("aba", "fecha essa aba", "CLOSE_TAB", {"alvo": "youtube"}),
                 ("negacao", "não fecha essa", "", {}),
                 ("pergunta", "como eu faria para fechar essa?", "", {}),
             ]),
            ("playlist", "coloca a playlist rock", "PLAYLIST_PLAY", "rock", "playlist_reproduzindo",
             {"nome_playlist": "rock"}, [
                 ("pronome", "coloca ela de novo", "MEDIA_CONTROL", {"acao": "replay"}),
                 ("novo_alvo", "coloca a playlist jazz de novo", "PLAYLIST_PLAY", {"nome_playlist": "jazz"}),
                 ("troca_dominio", "abre a calculadora de novo", "APP_OPEN", {"nome_app": "calculadora"}),
                 ("explicito", "fecha a calculadora", "CLOSE_APP", {"nome_app": "calculadora"}),
                 ("negacao", "não coloca ela de novo", "", {}),
                 ("pergunta", "como eu faria para colocar ela de novo?", "", {}),
             ]),
            ("volume", "coloca o volume em 90", "VOLUME", "", "volume_ajustado",
             {"acao": "set", "nivel_volume": 90}, [
                 ("parametro", "coloca em 40", "VOLUME", {"nivel_volume": 40}),
                 ("novo_assunto", "coloca a música máximo respeito", "MUSIC_SEARCH", {"query": "maximo respeito"}),
                 ("aula", "me explica o máximo divisor comum", "", {}),
             ]),
        ]:
            for nome, texto, esperado, esperado_params in pedidos:
                ident = dominio + "_" + nome
                antecedentes[ident] = (primeiro, intent, alvo, status, params, esperado_params)
                casos.append((ident, texto, "vigente", esperado, None))
        for ident, origem, texto, esperado, esperado_params in [
            ("playlist_literal", "playlist_pronome", 'coloca a playlist "jazz de novo"', "PLAYLIST_PLAY", {"nome_playlist": "jazz de novo"}),
            ("playlist_literal_repetida", "playlist_pronome", 'coloca a playlist "jazz de novo" de novo', "PLAYLIST_PLAY", {"nome_playlist": "jazz de novo"}),
            ("app_literal", "app_pronome", 'abre "ensaio de novo"', "APP_OPEN", {"nome_app": "ensaio de novo"}),
            ("site_literal_repetido", "site_pronome", 'abre o site "ensaio de novo" de novo', "OPEN_URL", {"alvo": "ensaio de novo"}),
            ("volume_extremo", "volume_parametro", "coloca no máximo", "VOLUME", {"nivel_volume": 100}),
            ("volume_extremo_minimo", "volume_parametro", "abaixa ao mínimo", "VOLUME", {"nivel_volume": 0}),
            ("volume_extremo_negacao", "volume_parametro", "não coloca no máximo", "", {}),
            ("volume_extremo_pergunta", "volume_parametro", "como eu faria para deixar no mínimo?", "", {}),
        ]:
            antecedentes[ident] = (*antecedentes[origem][:5], esperado_params)
            casos.append((ident, texto, "vigente", esperado, None))
        for ident, variante in [("volume_extremo_vencido", "vencido"),
                                ("volume_extremo_nao_confirmado", "nao_confirmado")]:
            antecedentes[ident] = (*antecedentes["volume_parametro"][:5], {})
            casos.append((ident, "coloca no máximo", variante, "", None))
        for ident, origem, texto in [
            ("playlist_literal_negacao", "playlist_pronome", 'não coloca a playlist "jazz de novo"'),
            ("playlist_literal_pergunta", "playlist_pronome", 'como eu faria para colocar a playlist "jazz de novo"?'),
            ("app_literal_negacao", "app_pronome", 'não abre "ensaio de novo"'),
            ("app_literal_pergunta", "app_pronome", 'como eu faria para abrir "ensaio de novo"?'),
        ]:
            antecedentes[ident] = (*antecedentes[origem][:5], {})
            casos.append((ident, texto, "vigente", "", None))
        for ident, texto, esperado, esperado_params in [
            ("musica_tipo", "coloca a música antes do amanhecer", "MUSIC_SEARCH", {"query": "antes do amanhecer"}),
            ("musica_tipo_interno", "toca a música a música de ontem", "MUSIC_SEARCH", {"query": "a musica de ontem"}),
            ("musica_literal", 'coloca a música "Música de Ontem"', "MUSIC_SEARCH", {"query": "Música de Ontem"}),
            ("musica_literal_extremo", 'coloca a música "Volume Máximo"', "MUSIC_SEARCH", {"query": "Volume Máximo"}),
            ("musica_literal_favorita", 'coloca a música "Minha Música Favorita"', "MUSIC_SEARCH", {"query": "Minha Música Favorita"}),
            ("musica_literal_som", 'escuta uma faixa "O Som do Silêncio"', "MUSIC_SEARCH", {"query": "O Som do Silêncio"}),
            ("musica_literal_negacao", 'não toca a música "Volume Máximo"', "", {}),
            ("musica_literal_pergunta", 'como eu faria para tocar a música "Volume Máximo"?', "", {}),
            ("musica_nome_mudo", 'coloca a música "Mudo"', "MUSIC_SEARCH", {"query": "Mudo"}),
            ("musica_nome_pausa", 'coloca a faixa "Pausa"', "MUSIC_SEARCH", {"query": "Pausa"}),
            ("musica_nome_despausa", 'toca a música "Despausa"', "MUSIC_SEARCH", {"query": "Despausa"}),
            ("musica_nome_volume", 'toca a faixa "Mais Alto"', "MUSIC_SEARCH", {"query": "Mais Alto"}),
            ("musica_referencia_temporal", "coloca a música anterior", "MEDIA_CONTROL", {"acao": "prev"}),
            ("tipo_playlist_silencio", "coloca a playlist Som do Silencio", "PLAYLIST_PLAY", {"nome_playlist": "som do silencio"}),
            ("tipo_playlist_volume", "coloca a playlist Volume em 40", "PLAYLIST_PLAY", {"nome_playlist": "volume em 40"}),
            ("tipo_playlist_alto", "coloca a playlist Mais Alto", "PLAYLIST_PLAY", {"nome_playlist": "mais alto"}),
            ("tipo_site_nome_musical", "abre o site Musica de Ontem", "OPEN_URL", {"alvo": "musica de ontem"}),
            ("tipo_app_nome_arquivo", "abre o app chamado Arquivo Vivo", "APP_OPEN", {"nome_app": "arquivo vivo"}),
            ("tipo_arquivo_nome_musical", "abre o arquivo musica.txt", "FILE_SEARCH", {"query": "musica.txt"}),
            # Não é gold de reprodução: sem candidato de vídeo, não admitir
            # MUSIC_SEARCH. Os REDs de resolução de vídeo ficam separados.
            ("tipo_video_sem_candidato", "coloca um video do jazzghost", "", {}),
            ("tipo_playlist_negacao", "não coloca a playlist Som do Silencio", "", {}),
            ("tipo_site_pergunta", "como eu faria para abrir o site Musica de Ontem?", "", {}),
        ]:
            antecedentes[ident] = (*antecedentes["volume_parametro"][:5], esperado_params)
            casos.append((ident, texto, "vigente", esperado, None))
    if painel_ajustes:
        casos, antecedentes = [], {}
        for ident, texto, esperado, esperado_params in [
            ("volume_delta10", "aumenta o volume em 10", "VOLUME", {"acao": "up", "delta": 10}),
            ("volume_delta5", "aumente o som em 5", "VOLUME", {"acao": "up", "delta": 5}),
            ("volume_delta25", "reduza o volume em 25", "VOLUME", {"acao": "down", "delta": 25}),
            ("volume_destino", "aumenta o volume para 40", "VOLUME", {"acao": "set", "nivel_volume": 40}),
            ("volume_atribuicao", "coloca o volume em 10", "VOLUME", {"acao": "set", "nivel_volume": 10}),
            ("volume_negacao", "não aumenta o volume em 10", "", {}),
            ("volume_consulta", "como eu faria para aumentar o volume em 10?", "", {}),
            ("volume_relato", "ontem eu aumentei o volume em 10", "", {}),
            ("volume_condicao", "se eu confirmar, aumenta o volume em 10", "", {}),
            ("volume_percentual_ambiguo", "aumenta o volume em 5%", "", {}),
            ("volume_decimal", "aumenta o volume em 5.5", "", {}),
            ("volume_sem_relacao", "aumenta o volume 10", "", {}),
            ("volume_literal", 'toca a música "Aumenta o Volume em 10"', "MUSIC_SEARCH", {}),
            ("brilho_delta10", "aumenta o brilho da luz em 10", "IOT_CONTROL", {"acao": "ajustar_brilho", "valor": 70}),
            ("brilho_delta5", "diminui o brilho da luz em 5", "IOT_CONTROL", {"acao": "ajustar_brilho", "valor": 55}),
            ("brilho_destino", "aumenta o brilho da luz para 10", "IOT_CONTROL", {"acao": "ajustar_brilho", "valor": 10}),
            ("brilho_atribuicao", "coloca o brilho da luz em 10", "IOT_CONTROL", {"acao": "ajustar_brilho", "valor": 10}),
            ("brilho_negacao", "não aumenta o brilho da luz em 10", "", {}),
            ("brilho_sem_base", "aumenta o brilho da luz em 10", "", {}),
            ("brilho_destino_invalido", "aumenta o brilho da luz para 101", "", {}),
            ("brilho_percentual_ambiguo", "aumenta o brilho da luz em 5%", "", {}),
            ("brilho_decimal", "aumenta o brilho da luz em 5.5", "", {}),
            ("volume_extenso40", "coloca o volume em quarenta", "VOLUME", {"acao": "set", "nivel_volume": 40}),
            ("volume_extenso82", "aumenta o volume para oitenta e dois", "VOLUME", {"acao": "set", "nivel_volume": 82}),
            ("volume_extenso_delta15", "diminui o volume em quinze", "VOLUME", {"acao": "down", "delta": 15}),
            ("volume_modificador_extenso", "deixa o som do computador em quarenta por cento", "VOLUME", {"acao": "set", "nivel_volume": 40}),
            ("volume_modificador_digitos", "deixa o som do computador em 40 por cento", "VOLUME", {"acao": "set", "nivel_volume": 40}),
            ("volume_extenso100", "coloca o volume em cem", "VOLUME", {"acao": "set", "nivel_volume": 100}),
            ("brilho_extenso40", "coloca o brilho da luz em quarenta", "IOT_CONTROL", {"acao": "ajustar_brilho", "valor": 40}),
            ("brilho_extenso_destino", "aumenta o brilho da luz para trinta", "IOT_CONTROL", {"acao": "ajustar_brilho", "valor": 30}),
            ("brilho_extenso_delta5", "diminui o brilho da luz em cinco", "IOT_CONTROL", {"acao": "ajustar_brilho", "valor": 55}),
            ("brilho_extenso_delta22", "aumenta o brilho da luz em vinte e dois", "IOT_CONTROL", {"acao": "ajustar_brilho", "valor": 82}),
        ]:
            antecedente = (("coloca o brilho da luz em 60", "IOT_CONTROL", "lampada_quarto", "brilho_ajustado",
                 {"acao": "ajustar_brilho", "alvo": "lampada_quarto", "valor": 60})
                if ident.startswith("brilho_") else
                ("coloca o volume em 90", "VOLUME", "", "volume_ajustado", {"acao": "set", "nivel_volume": 90}))
            antecedentes[ident] = (*antecedente, esperado_params)
            casos.append((ident, texto, "vigente", esperado, None))
    for ident, texto, variante, esperado, nivel in casos:
        root._estado_compartilhado_runtime.substituir("mental", estado_mental_inicial())
        primeiro, intent_inicial, alvo, status, params, esperado_params = antecedentes.get(
            ident, ("coloca o volume em 90", "VOLUME", "", "volume_ajustado", None, {}))
        root._iniciar_planejamento_turno(primeiro, origem="sonda_continuacao")
        inicial = root.detectar_intencao_deterministica(primeiro)
        if not inicial or inicial["intent"] != intent_inicial:
            raise RuntimeError("não alcançou o primeiro ajuste explícito")
        # Fixture declarada, publicada pela BASE realmente instalada no adaptador.
        # Não representa uma releitura material do Windows.
        root._registrar_resultado_execucao_base(ResultadoAcao(
            id_solicitacao="sonda-contexto-" + ident, intent=intent_inicial, alvo=alvo, status=status,
            executou=True, confirmado=True, origem="executor", params=dict(params or inicial["params"])), primeiro)
        if painel_ajustes and ident.startswith("brilho_"):
            # Fonte antecedente sintética no slot canônico; sem lâmpada/Tuya.
            root._estado_compartilhado_runtime.atualizar_campos("mental",
                parametros_iot_por_dispositivo={"lampada_quarto": {"brilho": 60}}
                if ident != "brilho_sem_base" else {}, ultimos_parametros_iot={})
        if variante == "vencido":
            root._estado_compartilhado_runtime.mental["ultima_acao_ts"] = time.time() - 301
        elif variante == "nao_confirmado":
            root._estado_compartilhado_runtime.mental["ultima_acao_contrato"]["confirmado"] = None
        antes = root._estado_compartilhado_runtime.snapshot()["mental"]
        turno = root._iniciar_planejamento_turno(texto, origem="sonda_continuacao")
        detector = root.detectar_intencao_deterministica(texto)
        ctx = ciclo._montar_contexto_resolucao()
        detector_ctx = ctx["detectar_intencao_deterministica"](texto)
        modelo_antes = len(chamadas_modelo)
        decisao, rota = root.resolver_comando_natural(texto, "sonda_continuacao")
        estado_depois = root._estado_compartilhado_runtime.snapshot()["mental"]
        intent = str((decisao or {}).get("intent") or "")
        parametros = dict((decisao or {}).get("params") or {})
        normalizacao_posterior = None
        if intent == "MUSIC_SEARCH" and parametros.get("query"):
            consulta = str(parametros["query"])
            normalizada = root._normalizar_query_musical(consulta)
            # Diagnóstico da porta usada pelo executor; nenhuma busca/efeito.
            # Não entra no gold da resolução e não prova execução posterior.
            normalizacao_posterior = {"entrada": consulta, "saida": normalizada,
                "alterou": normalizada != consulta, "executor_chamado": False}
        red = ("coordenador_divergiu_do_vinculo" if intent != esperado else
               "nivel_novo_nao_preservado" if nivel is not None and parametros.get("nivel_volume") != nivel else
               "argumento_atual_substituido" if any(parametros.get(k) != v for k, v in esperado_params.items()) else "")
        admissao_quantitativa = None
        if ident.startswith("invalido_") or ident in {
            "conector_negacao", "conector_pergunta", "conector_condicao", "conector_capacidade",
            "conector_elipse_vencida", "conector_invalido_decimal",
        }:
            propostas = [
                {"intent": "MUSIC_SEARCH", "params": {"query": "em quarenta"}},
                {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": 40}},
                {"intent": "APP_OPEN", "params": {"nome_app": "calculadora"}},
            ]
            admissao_quantitativa = root._validador_comandos_turno_runtime(propostas)
            if not red and admissao_quantitativa["comandos"]:
                red = "admissao_reintroduziu_proposta_sem_resolucao"
        elif decisao and (ident in {"extenso_atribuicao", "literal_quantidade", "literal_decimal", "artigo_titulo",
                       "agenda_parametro", "agenda_outro_dominio"} or ident.startswith("conector_")):
            admissao_quantitativa = root._validador_comandos_turno_runtime([decisao])
            if not red and admissao_quantitativa["comandos"] != [decisao]:
                red = "admissao_recusou_pedido_canonico_legitimo"
        controles_agendamento = []
        if ident in {"agenda_parametro", "agenda_outro_dominio"} and decisao:
            # Exercita a admissão instalada, não um comparador substituído.
            # Mesmo mudando rota, prazo/alvo/destino/extras continuam exatos.
            for nome, caminho, valor in [
                ("prazo", ("atraso_segundos",), 600),
                ("acao", ("acao_agendada", "intent"), "CLOSE_APP"),
                ("alvo", ("acao_agendada", "params", "nome_app"), "Notepad"),
                ("destino", ("acao_agendada", "params", "target"), "pc_b"),
                ("extra", ("_execucao_silenciosa",), True),
                ("substituir", ("substituir_agendamento_anterior",), True),
                ("rota_malformada", ("rota_original",), {"target": "pc_b"}),
            ]:
                divergente = deepcopy(decisao)
                params_divergentes = divergente["params"]
                for chave in caminho[:-1]:
                    params_divergentes = params_divergentes[chave]
                params_divergentes[caminho[-1]] = valor
                propostas_agenda = [divergente, deepcopy(decisao), deepcopy(decisao)]
                resultado_agenda = root._validador_comandos_turno_runtime(propostas_agenda)
                correto = (resultado_agenda["comandos"] == [decisao]
                    and len(resultado_agenda["rejeitados"]) == 2)
                controles_agendamento.append({"nome": nome, "propostos": propostas_agenda,
                    "validacao": resultado_agenda, "correto": correto})
                if not red and not correto:
                    red = "admissao_agendamento_divergente_ou_duplicado_" + nome
        execucao_consulta = None
        if sondar_executor and intent == "MUSIC_SEARCH":
            consultas, normalizacoes, conclusoes = [], [], []
            runtime_ctx = ciclo.contexto_intencao_runtime
            servicos = runtime_ctx._servicos()
            normalizar_original = servicos["_normalizar_query_musical"]
            def normalizar_observado(valor):
                normalizacoes.append(valor)
                return normalizar_original(valor)
            def buscar_sem_video(query, **_k):
                consultas.append(query)
                return {}  # Fronteira externa declarada; nenhuma busca ou efeito.
            def concluir_sem_voz(receipt, fala, *_a, **_k):
                conclusoes.append({"status": receipt.status, "executou": receipt.executou,
                    "confirmado": receipt.confirmado, "fala": fala})
            substitutos = {"_normalizar_query_musical": normalizar_observado,
                "_resolver_primeiro_video_youtube": buscar_sem_video,
                "_falar_resultado_operacional": concluir_sem_voz,
                "falar_com_lipsync": lambda *_a, **_k: None, "enviar_mensagem": None}
            originais = {nome: (nome in runtime_ctx._servicos_estaticos, runtime_ctx._servicos_estaticos.get(nome),
                                hasattr(root, nome), getattr(root, nome, None)) for nome in substitutos}
            try:
                runtime_ctx._servicos_estaticos.update(substitutos)
                for nome, valor in substitutos.items():
                    setattr(root, nome, valor)
                comando = deepcopy(decisao)
                retorno = root.executar_intencao(comando, texto)
                execucao_consulta = {"consultas": consultas, "normalizacoes_fala": normalizacoes,
                    "retorno": retorno, "comando_depois": comando, "conclusoes": conclusoes,
                    "executor_instalado_chamado": True, "busca_externa_substituida": True,
                    "efeito_confirmado": False}
            finally:
                for nome, (existia, valor, existia_root, valor_root) in originais.items():
                    if existia: runtime_ctx._servicos_estaticos[nome] = valor
                    else: runtime_ctx._servicos_estaticos.pop(nome, None)
                    if existia_root: setattr(root, nome, valor_root)
                    else: delattr(root, nome)
        resultados.append({"id": ident, "texto_inicial": primeiro, "texto": texto,
            "fixture_receipt": True, "estado_antes": antes, "turno": turno,
            "detector": detector, "decisao": decisao, "rota": rota,
            "detector_contexto": detector_ctx,
            "arbitragem": estado_depois.get("historico_arbitragem", [])[-1:],
            "contrato_depois": estado_depois.get("ultima_acao_contrato"),
            "params_depois": estado_depois.get("ultima_acao_params"),
            "operacoes_depois": estado_depois.get("continuidade_geral", {}).get("operacoes_reexecutaveis"),
            "retrato": estado_depois.get("retrato_turno_atual", {}),
            "porta_modelo_consultada": len(chamadas_modelo) - modelo_antes,
            "diagnostico_normalizacao_posterior": normalizacao_posterior,
            "admissao_quantitativa": admissao_quantitativa,
            "controles_agendamento": controles_agendamento,
            "execucao_consulta": execucao_consulta,
            "esperado": {"intent": esperado, "nivel_volume": nivel, "params": esperado_params}, "primeira_fronteira_red": red})
    return {"resultados": resultados, "contraprova_prioridade": contraprova_prioridade, "instalacao": {
        "detector": root.detectar_intencao_deterministica == root._deteccao_deterministica_runtime.detectar,
        "coordenador": root.resolver_comando_natural == root._composicao_ciclo_comandos_runtime.resolver_comando_natural,
        "publicador_base": root._registrar_resultado_execucao_base == root._estado_contexto_runtime.registrar_resultado_execucao,
        "contexto": root._resolver_comando_contextual_forcado == root._contexto_imediato_runtime.resolver},
        "voz_instalada": {"principal": root._voz_runtime.voice,
            "reservas": list(root._voz_runtime.fallback_voices),
            "fallback_local_permitido": root._voz_runtime.permitir_fallback_local},
        "politica_voz_instalada": coletar_politica_voz_instalada(root),
        "modelo_real_consultado": False, "runtime_main_validado": False,
        "efeitos_externos_executados": False, "voz_validada": False}


def coletar(*, contraprova_prioridade: bool = False, painel_contexto: bool = False,
            sondar_executor: bool = False, painel_ajustes: bool = False) -> dict:
    fontes = ["laylay.py", "mente_laylay/memoria_mental/contexto_imediato.py",
        "mente_laylay/memoria_mental/contexto_compartilhado.py", "mente_laylay/memoria_mental/continuidade_geral.py",
        "mente_laylay/autonomia/orquestrador_deterministico.py", "mente_laylay/autonomia/coordenador_intencao.py",
        "mente_laylay/autonomia/roteador_deterministico.py", "mente_laylay/autonomia/detectores_playlist.py",
        "mente_laylay/autonomia/executor_musical.py", "mente_laylay/memoria_mental/busca_youtube.py",
        "mente_laylay/autonomia/roteador_intencao.py", "mente_laylay/autonomia/adaptador_resultado.py",
        "mente_laylay/integracao/contexto_execucao_ia.py", "mente_laylay/cognicao/refinamento_pesquisa.py",
        "mente_laylay/cognicao/arbitro_turno.py", "mente_laylay/especialistas/capacidades.py",
        "mente_laylay/memoria_mental/atividade_operacional_runtime.py",
        "mente_laylay/cognicao/modalidade_turno.py", "mente_laylay/integracao/estado_contexto_runtime.py",
        "mente_laylay/cognicao/gramatica_operacional.py",
        "mente_laylay/cognicao/escopo_autorizacao.py", "mente_laylay/cognicao/decisao_turno.py",
        "mente_laylay/autonomia/dispatcher_comandos_json.py", "mente_laylay/autonomia/executor_agenda.py",
        "mente_laylay/cognicao/normalizacao_linguagem.py", "mente_laylay/personalidade/voz_runtime.py",
        "mente_laylay/autonomia/executor_audio.py", "mente_laylay/iot/runtime.py",
        "mente_laylay/cognicao/referencias_linguagem.py", "mente_laylay/cognicao/retrato_turno.py",
        "mente_laylay/memoria_mental/registro_semantico.py", "mente_laylay/memoria_mental/continuidade_semantica.py",
        "scripts/analises/sonda_continuacao_operacional.py", "scripts/analises/sonda_escopo_propostas_mistas.py"]
    def hashes():
        return {p: hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in fontes}
    antes = hashes()
    base = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True)}
    with tempfile.TemporaryDirectory(prefix="laylay_continuacao_") as pasta:
        env = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off",
            LAYLAY_NEURAL_COLETA_ENTRADAS="0", LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
            LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
            LAYLAY_PRESENCA="0", LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
            LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0", GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
        codigo = ("import sys,json; from pathlib import Path; "
            "from scripts.analises.sonda_continuacao_operacional import coletar_instalado; "
            "r=coletar_instalado(Path(sys.argv[1]),contraprova_prioridade=sys.argv[2]=='1',painel_contexto=sys.argv[3]=='1',sondar_executor=sys.argv[4]=='1',painel_ajustes=sys.argv[5]=='1'); sys.__stdout__.write('CONTINUIDADE_JSON='+json.dumps(r,ensure_ascii=False)+'\\n')")
        p = subprocess.run([sys.executable, "-c", codigo, pasta, "1" if contraprova_prioridade else "0", "1" if painel_contexto else "0", "1" if sondar_executor else "0", "1" if painel_ajustes else "0"], cwd=RAIZ, env=env,
            capture_output=True, text=True, encoding="utf-8", timeout=60)
    linhas = [l for l in p.stdout.splitlines() if l.startswith("CONTINUIDADE_JSON=")]
    if p.returncode or len(linhas) != 1:
        raise RuntimeError("sonda não alcançou a fronteira: " + p.stderr[-3000:] + p.stdout[-2000:])
    depois = hashes()
    return {**base, **json.loads(linhas[0].split("=", 1)[1]), "hashes_antes": antes,
        "hashes_depois": depois, "fontes_estaveis": antes == depois,
        "logs": "\n".join(l for l in p.stdout.splitlines() if not l.startswith("CONTINUIDADE_JSON=")),
        "stderr": p.stderr, "limite": "resolução instalada; receipts antecedentes fixtures; executor opcional com busca vazia e voz substituídas, sem main/efeitos"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--contraprova-prioridade", action="store_true")
    parser.add_argument("--painel-contexto", action="store_true")
    parser.add_argument("--sondar-executor", action="store_true")
    parser.add_argument("--painel-ajustes", action="store_true", help="destino/delta em volume e brilho, sem efeito")
    args = parser.parse_args()
    if args.painel_ajustes and (args.painel_contexto or args.sondar_executor):
        parser.error("painel de ajustes é isolado e não chama executor")
    destino = args.saida.resolve()
    if destino.exists() or not destino.is_relative_to((RAIZ / "resultados_testes").resolve()):
        parser.error("saída nova dentro de resultados_testes")
    r = coletar(contraprova_prioridade=args.contraprova_prioridade, painel_contexto=args.painel_contexto,
                sondar_executor=args.sondar_executor, painel_ajustes=args.painel_ajustes)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as arquivo:
        json.dump(r, arquivo, ensure_ascii=False, indent=2)
    print(json.dumps([{ "id": c["id"], "decisao": c["decisao"], "red": c["primeira_fronteira_red"]}
        for c in r["resultados"]], ensure_ascii=False))
    return int(not r["fontes_estaveis"] or not all(r["instalacao"].values())
               or any(c["primeira_fronteira_red"] for c in r["resultados"]))


if __name__ == "__main__":
    raise SystemExit(main())
