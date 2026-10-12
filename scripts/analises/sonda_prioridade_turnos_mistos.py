"""Audita prioridade instalada → continuação conversacional, sem efeitos.

Não força a rota LLM: mantém o callback prioritário da RespostaIA instalada.
Modelo, executor, gravação operacional e entrega são portas de recusa/captura.
Nenhuma fala capturada comprova resposta correta, áudio ou efeito físico.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

from scripts.analises.sonda_escopo_propostas_mistas import RAIZ, painel, preparar_instalacao_isolada


def projetar_fatos_conversacionais(turno: dict, evidencia: dict) -> dict:
    """Ablação de diagnóstico: projeta owners existentes, sem parser ou gold.

    Não atesta ausência global de pendências e não confere autorização. A
    capacidade disponível não confirma acesso a um alvo concreto nem efeito.
    """
    atos = [s for s in turno.get("segmentos", [])
            if s.get("autoriza_execucao") is False]
    return {
        "fonte": "interpretador_canonico_e_catalogo_vivo",
        "turno_id": turno.get("id"),
        "atos_restantes": [{k: s.get(k) for k in (
            "indice", "texto_estrutural", "modalidade", "natureza_acao", "motivo",
            "autoriza_execucao")} for s in atos],
        "efeito_deste_complemento": "somente_resposta_conversacional",
        "pendencia_criada_por_este_complemento": False,
        "pendencias_de_outros_fluxos": "nao_consultadas",
        "capacidade_nao_prova_acesso_ao_alvo_ou_execucao": True,
        "capacidades": {k: deepcopy(evidencia.get(k)) for k in (
            "fonte", "dominios_relevantes", "dominios_indisponiveis_relevantes",
            "documentacao_capacidades", "documentacao_turno_id", "autoriza_execucao")},
        "autoriza_execucao": False,
    }


def projetar_nucleo_explicativo(turno: dict, texto_usuario: str) -> dict:
    """Protótipo de diagnóstico: consome snapshots, sem reinterpretar/gold.

    A conclusão do caminho read-only não é ausência global de pendências ou
    prova de efeito. Roteiro certo no prompt não atesta a redação resultante.
    """
    from mente_laylay.cognicao.contratos_turno import ComplementoConversacionalTurno
    from mente_laylay.cognicao.contrato_fala import ContratoSemanticoFala
    from mente_laylay.cognicao.geracao_concreta import RoteiroGeracaoConcreta

    complemento = ComplementoConversacionalTurno.da_prioridade(turno, texto_usuario)
    if complemento is None:
        raise ValueError("núcleo sem complemento canônico vigente")
    nucleos = []
    for ato in complemento.atos_explicativos:
        if ato.relacao == "condicao_nao_verificada":
            conclusao = (
                "Este ato depende de uma condição não verificada neste pedido. "
                "Este complemento só explica: não criou uma pendência executável "
                "ou agendamento. Para executar depois, faça um novo pedido direto; "
                "responder apenas sim ou confirmar não substitui esse pedido."
            )
        elif ato.relacao == "consulta_significado":
            conclusao = (
                "Explique o significado de objeto_textual, separado da pergunta "
                "inteira. A consulta atual pede essa explicação, não seu efeito; "
                "não transforme a expressão consultada em descrição da pergunta."
            )
        else:
            conclusao = "Responda ao conteúdo deste ato sem inferir efeito, pendência ou capacidade."
        nucleos.append({
            **ato.como_dict(), "nucleo_a_entregar": conclusao,
            "perspectiva": {"enunciador": "usuário", "destinatario": "Laylay",
                            "grupo": "não reduzir a uma pessoa", "indeterminada": "não atribuir pessoa"},
            "nao_inferir": ["ausência global de pendências", "condição já satisfeita",
                            "acesso a alvo concreto", "incapacidade", "efeito operacional"],
        })
    contrato = ContratoSemanticoFala(
        turno_id=complemento.turno_id, funcao="explicacao_atos_vinculados",
        atos=tuple(a.relacao for a in complemento.atos_explicativos),
        conteudos_obrigatorios=("entregar o núcleo de cada ato, sem mudar sua relação ou referente",),
        inferencias_proibidas=("não inventar continuação, acesso, capacidade ou efeito",),
        permite_pergunta=False, permite_metafora=False,
        roteiro_concreto=RoteiroGeracaoConcreta(
            estrategia="explicacao_atos_vinculados", ancora_literal=complemento.texto,
            nucleo_resposta="explicar cada ato conforme sua relação, objeto e pessoa canônicos",
            sequencia=("explicar o objeto ou condição", "informar somente a conclusão deste escopo"),
        ).como_dict(),
    ).como_dict()
    contrato.update(nucleos_explicativos=nucleos, somente_diagnostico=True,
                    fonte="snapshot_do_interpretador_canonico", pendencias_alheias="nao_consultadas",
                    exigir_nucleo_verificado=True)
    return contrato


def coletar_instalado(pasta: Path, *, contraprova_retornar_nao_tratado: bool = False,
                     modelo_real: bool = False, ablacao_projecao: bool = False,
                     ablacao_avisos: bool = False, painel_pospostas: bool = False,
                     contraprova_compromisso: bool = False, contraprova_reparo: bool = False,
                     ablacao_nucleo: bool = False, realizacao_controlada: bool = False) -> dict:
    from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo

    transportes = []
    selecao = {}
    if modelo_real:
        import requests
        from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
        selecao = selecao_local()
        guarda = criar_guarda_http_local(selecao, transportes, requests.sessions.Session.request)
        root = preparar_instalacao_isolada(pasta, requisicao_http=guarda)
    else:
        root = preparar_instalacao_isolada(pasta)
    runtime = root._resposta_ia_runtime
    instalado = runtime._contexto()
    prioridade = root._comandos_imediatos_runtime
    namespace = prioridade.namespace_getter()
    ciclo = root._composicao_ciclo_comandos_runtime.ciclo
    servicos_ciclo = root._composicao_ciclo_comandos_runtime._servicos
    resultados = []
    textos = []
    root._orquestrador_fala_runtime.registrar_observador_texto_final(
        lambda fala, *_a, **_k: textos.append(str(fala)) or True)
    # Manter classificação/resolução/coordenador reais. As outras capacidades
    # prioritárias são isoladas: este painel não pede suas operações.
    chaves_prioridade = (
        "_estado_compartilhado_runtime", "_normalizar_texto_com_apelidos",
        "_texto_tem_comando_explicito", "detectar_intencao_deterministica",
        "resolver_comando_natural", "processar_comandos_em_cadeia",
    )
    chaves_pipeline = (
        "marcar_inicio_turno", "obter_turno_atual", "usar_modo_rapido",
        "texto_depende_de_contexto", "preparacao_conversa", "estado_conversa",
        "preparar_resposta", "validar_comandos_planejados", "atualizar_plano_proposta",
        "atualizar_plano_turno", "atualizar_plano_ocorrencia",
        "proposta_principal_vigente", "executar_comandos_json",
        "agrupar_resultados_operacionais",
    )
    instalacao = {
        "prioridade_instalada": instalado["processar_comandos_prioritarios"]
            == root._processar_comandos_prioritarios,
        "owner_prioridade": instalado["processar_comandos_prioritarios"].__self__ is prioridade,
        "estado_compartilhado": namespace["_estado_compartilhado_runtime"]
            is root._estado_compartilhado_runtime,
        "cadeia_instalada": namespace["processar_comandos_em_cadeia"]
            == root._composicao_ciclo_comandos_runtime.processar_cadeia,
        "lote_instalado": instalado.get("agrupar_resultados_operacionais")
            == root._orquestrador_fala_runtime.agrupar_resultados_operacionais,
    }
    casos = painel()[:9]
    # Ablação do ato não operacional no painel congelado. Não é segmentador
    # de produção: os seis exemplos contêm exatamente este separador literal.
    for misto in painel()[:6]:
        operacional, separador, _resto = misto["texto"].partition(";")
        if not separador:
            raise ValueError("controle operacional perdeu sua base congelada")
        casos.append({**deepcopy(misto), "id": "controle_operacional_" + misto["id"],
                      "texto": operacional})
    if painel_pospostas:
        # Extensão diagnóstica, não mudança do painel congelado anterior.
        # Gold só é usado para aferir a fronteira, nunca para interpretar.
        casos += [{"id": "posposta_" + ident, "texto": texto, "vigente": True,
                   "propostos": [], "esperados": [esperado], "auditar_escopo": True}
                  for ident, texto, esperado in (
            ("apps_iot", "Abre a calculadora; liga a luz somente quando eu confirmar",
             {"intent": "APP_OPEN", "params": {"nome_app": "calculadora"}}),
            ("apps_musica", "Abre a calculadora. Pausa a música só se eu autorizar",
             {"intent": "APP_OPEN", "params": {"nome_app": "calculadora"}}),
            ("iot_apps", "Liga a luz; abre a calculadora apenas quando eu pedir",
             {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}}),
            ("arquivo_iot", "Abre o arquivo notas.txt; liga a luz só se eu confirmar",
             {"intent": "FILE_SEARCH", "params": {"query": "notas.txt", "alvo": "notas.txt", "abrir_resultado_exato": True}}),
        )]
    if modelo_real:
        casos = casos[:6]  # Controles locais já medidos; seis autorias instaladas.
    if realizacao_controlada:
        # Recorte declarado do painel congelado, não classificação/gold em
        # produção. Consulta de significado não tem essa cobertura.
        casos = [casos[i] for i in (1, 2, 4)]
    if ablacao_projecao or ablacao_avisos or ablacao_nucleo:
        # Duas repetições, ordem de casos/variantes alternada. O controle é
        # exatamente o pedido instalado; intervenção acrescenta só a projeção.
        base = casos[:6]
        casos = [{**deepcopy(c), "repeticao": repeticao, "variante": variante}
                 for repeticao in range(2)
                 for c in (base if repeticao == 0 else base[::-1])
                 for variante in (("controle", "intervencao") if repeticao == 0
                                  else ("intervencao", "controle"))]
    for caso in casos:
        recebidos, modelos, fases, falas, conclusoes, textos = [], [], [], [], [], []
        compromisso_injetado = ""

        def capturar(pedido, texto):
            recebidos.append({"intent": pedido["intent"], "params": deepcopy(pedido["params"]),
                              "texto_porta_executor": texto})
            return False  # Recusa isolada, nenhum efeito/receipt de sucesso.

        def falar(fala, *_a, **_k):
            falas.append(str(fala))
            return True  # Aceite da porta isolada, não receipt de voz/efeito.

        def modelo(pedido):
            nonlocal compromisso_injetado
            entrada_original = None
            if ablacao_avisos and pedido.tipo_chamada == "autoria_operacional":
                entrada_original = json.loads(pedido.mensagens[1]["content"])
                if caso["variante"] == "intervencao":
                    entrada = deepcopy(entrada_original)
                    # Host mantém os avisos na publicação. Só sua exposição
                    # à autora muda; não inventar receipt nem simular sucesso.
                    entrada.pop("avisos_obrigatorios")
                    mensagens = deepcopy(list(pedido.mensagens))
                    mensagens[1]["content"] = json.dumps(entrada, ensure_ascii=False)
                    pedido = replace(pedido, mensagens=tuple(mensagens))
            if ablacao_projecao and pedido.tipo_chamada == "autoria_operacional":
                entrada = json.loads(pedido.mensagens[1]["content"])
                turno = dict(root._estado_compartilhado_runtime.mental["turno_atual"])
                evidencia = root._evidencia_habilidades_turno_mente(
                    entrada["texto_conversacional"], turno=turno)
                projecao = projetar_fatos_conversacionais(turno, evidencia)
                if caso["variante"] == "intervencao":
                    entrada["fatos_conversacionais"] = projecao
                    mensagens = deepcopy(list(pedido.mensagens))
                    mensagens[1]["content"] = json.dumps(entrada, ensure_ascii=False)
                    pedido = replace(pedido, mensagens=tuple(mensagens))
            contrato_nucleo = None
            complemento_nuclear = None
            if ablacao_nucleo and pedido.tipo_chamada in {"autoria_operacional", "reparo_factual"}:
                turno = root._estado_compartilhado_runtime.mental["turno_atual"]
                contrato_nucleo = projetar_nucleo_explicativo(turno, caso["texto"])
                if caso["variante"] == "intervencao":
                    entrada = json.loads(pedido.mensagens[1]["content"])
                    entrada["contrato_fala"] = contrato_nucleo
                    mensagens = deepcopy(list(pedido.mensagens))
                    mensagens[1]["content"] = json.dumps(entrada, ensure_ascii=False)
                    pedido = replace(pedido, mensagens=tuple(mensagens))
            if realizacao_controlada:
                from mente_laylay.cognicao.contratos_turno import ComplementoConversacionalTurno
                from mente_laylay.cognicao.contrato_fala import construir_realizacoes_nucleo_explicativo
                turno = root._estado_compartilhado_runtime.mental["turno_atual"]
                complemento_nuclear = ComplementoConversacionalTurno.da_prioridade(turno, caso["texto"])
                realizacoes = construir_realizacoes_nucleo_explicativo(complemento_nuclear)
                if not realizacoes:
                    raise RuntimeError("painel nuclear fora da cobertura declarada")
                contrato_nucleo = projetar_nucleo_explicativo(turno, caso["texto"])
                # Esta chamada só escolhe redação; receipts/avisos continuam
                # no host e não são uma pergunta de autorização ao seletor.
                entrada = {"realizacoes_permitidas": realizacoes}
                sistema_controlado = (
                    "Você escolhe como redigir uma explicação, não decide executar ações. "
                    "Para CADA item em realizacoes_permitidas, escolha exatamente uma "
                    "opcao pelo seu id e preserve o indice do item. A escolha é obrigatória "
                    "mesmo sem autorização de execução: é apenas uma redação. Não copie "
                    "fala nem acrescente campos. Retorne somente JSON com realizacoes, "
                    "uma lista de objetos com indice e opcao."
                )
                pedido = replace(pedido, mensagens=(
                    {"role": "system", "content": sistema_controlado},
                    {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)},
                ))
            modelos.append({"mensagens": deepcopy(list(pedido.mensagens)),
                            "tipo_chamada": pedido.tipo_chamada})
            if contrato_nucleo is not None:
                modelos[-1]["nucleo_diagnostico"] = contrato_nucleo
            if ablacao_projecao and pedido.tipo_chamada == "autoria_operacional":
                modelos[-1]["projecao_diagnostica"] = projecao
            if entrada_original is not None:
                modelos[-1]["entrada_original"] = entrada_original
            if modelo_real:
                resultado = instalado["modelo_llm"].executar(pedido)
                modelos[-1].update(resposta_bruta=resultado.texto, sucesso=resultado.sucesso)
                if contrato_nucleo is not None and not realizacao_controlada:
                    from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
                    try:
                        fala = json.loads(resultado.texto).get("conversa", "")
                    except (ValueError, TypeError):
                        fala = ""
                    modelos[-1]["avaliacao_validador_existente"] = validar_aderencia_contrato_fala(
                        turno["texto_conversacional"], fala, contrato_fala=contrato_nucleo,
                        turno_id=turno["id"],
                    )
                if not realizacao_controlada:
                    return resultado
            elif realizacao_controlada:
                escolhidas = [{"indice": ato["indice"], "opcao": ato["opcoes"][0]["id"]}
                              for ato in realizacoes]
                dados = {"realizacoes": escolhidas}
                resultado = ResultadoModelo(json.dumps(dados, ensure_ascii=False), True)
                modelos[-1]["resposta_injetada"] = resultado.texto
            if realizacao_controlada:
                from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
                from mente_laylay.cognicao.contrato_fala import realizar_nucleo_explicativo
                try:
                    dados = json.loads(resultado.texto)
                    if not isinstance(dados, (dict, list)):
                        dados = {}
                except (ValueError, TypeError):
                    dados = {}
                fala_realizada, motivo_realizacao = realizar_nucleo_explicativo(complemento_nuclear, dados)
                if contraprova_compromisso and fala_realizada:
                    compromisso_injetado = "Quando você confirmar, a ação acontecerá."
                    fala_realizada += " " + compromisso_injetado
                contrato_local = {**contrato_nucleo, "complemento_nuclear": complemento_nuclear,
                                  "proposta_nuclear": dados}
                avaliacao = validar_aderencia_contrato_fala(
                    complemento_nuclear.texto, fala_realizada,
                    contrato_fala=contrato_local, turno_id=turno["id"],
                )
                modelos[-1]["avaliacao_nuclear"] = avaliacao
                modelos[-1]["fala_realizada"] = fala_realizada
                modelos[-1]["motivo_realizacao"] = motivo_realizacao
                # Ponte diagnóstica agora devolve somente a escolha aprovada
                # ao protocolo cotidiano. Continua intervenção, não prova de
                # que o pedido da autora real foi enviado ao modelo.
                escolhas = dados if isinstance(dados, list) else dados.get("realizacoes")
                devolvida = ({"trechos": [], "realizacoes": escolhas}
                             if avaliacao["aceita"] else
                             {"trechos": [], "conversa": "", "verificacao_nuclear": "rejeitada"})
                modelos[-1]["resposta_devolvida_ao_pipeline"] = devolvida
                return ResultadoModelo(json.dumps(devolvida, ensure_ascii=False), resultado.sucesso)
            if pedido.tipo_chamada in {"autoria_operacional", "reparo_factual"}:
                entrada = json.loads(pedido.mensagens[1]["content"])
                conversa = "Continuação conversacional capturada."
                turno = root._estado_compartilhado_runtime.mental["turno_atual"]
                if any(s.get("natureza_acao") == "condicao_nao_verificada" for s in turno.get("segmentos", [])):
                    # Controle positivo agora precisa satisfazer a cobertura
                    # mínima explícita. Não usar o gold de operação/alvo.
                    conversa += " Essa condição não criou agendamento."
                if (contraprova_compromisso or contraprova_reparo) and any(
                    s.get("natureza_acao") == "condicao_nao_verificada" for s in turno.get("segmentos", [])
                ):
                    conversa = compromisso_injetado = "A ação só será executada quando você confirmar. Vou aguardar seu sinal."
                    if contraprova_reparo:
                        compromisso_injetado = "A ação depende da minha confirmação."
                        conversa = (compromisso_injetado if pedido.tipo_chamada == "autoria_operacional" else
                                    "A condição depende da sua confirmação, mas não deixou a ação agendada. Faça um novo pedido quando quiser executar.")
                dados = {"trechos": [], "conversa": conversa}
                if entrada.get("realizacoes_permitidas") and not compromisso_injetado:
                    # Controle derivado do inventário efetivamente recebido,
                    # nunca dos alvos/operações esperados do painel.
                    dados = {"trechos": [], "realizacoes": [
                        {"indice": ato["indice"], "opcao": ato["opcoes"][0]["id"]}
                        for ato in entrada["realizacoes_permitidas"]]}
                resposta_injetada = json.dumps(dados)
                modelos[-1]["resposta_injetada"] = resposta_injetada
                return ResultadoModelo(resposta_injetada, True)
            # Na contraprova a LLM repete a operação que a prioridade já
            # recebeu. Derivar da captura, nunca preencher com o gold.
            repetidos = ([{"intent": recebidos[0]["intent"],
                           "params": deepcopy(recebidos[0]["params"])}]
                         if contraprova_retornar_nao_tratado and recebidos else [])
            return ResultadoModelo(json.dumps({"fala": "Continuação conversacional capturada.",
                "comandos": repetidos, "leitura_turno": ["pergunta"]}), True)

        def concluir(_ctx, comandos, erros, fala, *flags):
            conclusoes.append({"fala_planejada": fala, "comandos": deepcopy(comandos),
                               "erros": list(erros)})
            return {"registrar_no_historico": False}

        ns = {k: namespace[k] for k in chaves_prioridade if k in namespace}
        ns.update(executar_intencao=capturar, falar_com_lipsync=falar,
                  _registrar_resultado_execucao=lambda *_a, **_k: None)
        prioridade.namespace_getter = lambda: ns
        # A cadeia instalada consulta a execução por self e as portas do seu
        # contexto. Não substitui resolvedor/segmentador pelo gold do painel.
        ciclo.executar_intencao = capturar
        # O estado_getter repõe o agrupador canônico sobre o namespace.
        # Preservar também o canal final/diretor; isolar só a porta de TTS.
        # O observador textual acima comprova a mesma publicação sem áudio.
        root._voz_runtime.falar = falar
        servicos_ciclo.update(falar_com_lipsync=falar, _emitir_resposta_curta=falar,
            _registrar_resultado_execucao=lambda *_a, **_k: None)
        ctx = {k: instalado[k] for k in chaves_pipeline if k in instalado}
        callback_prioritario = instalado["processar_comandos_prioritarios"]
        def contraprova(texto):
            callback_prioritario(texto)
            return False  # Só neste subprocesso: candidato ingênuo rejeitado.

        ctx.update(processar_comandos_prioritarios=(
                contraprova if contraprova_retornar_nao_tratado else callback_prioritario),
            modelo_llm=RegistroModeloLLM(SimpleNamespace(executar=modelo)),
            contexto_dispatch_runtime=SimpleNamespace(montar=lambda: {"executar_intencao": capturar}),
            contexto_finalizacao_runtime=SimpleNamespace(montar=lambda: {}),
            finalizar_execucao=concluir)
        runtime._contexto_getter = lambda: ctx
        runtime.processar(caso["texto"], origem="sonda_prioridade_mista")
        mental = root._estado_compartilhado_runtime.snapshot()["mental"]
        turno = mental["turno_atual"]
        conversacional = str(turno.get("texto_conversacional") or "").strip()
        deve_continuar = bool(conversacional and turno.get("autoriza_execucao") is True)
        reentrada = bool(contraprova_retornar_nao_tratado and len(recebidos) > 1
            and recebidos[0]["intent"] == recebidos[1]["intent"]
            and recebidos[0]["params"] == recebidos[1]["params"])
        red_escopo = ""
        if caso.get("auditar_escopo"):
            if turno.get("autoriza_execucao") is not bool(caso["esperados"]):
                red_escopo = "segmentacao_absorveu_ato_independente"
            elif [{k: r[k] for k in ("intent", "params")} for r in recebidos] != caso["esperados"]:
                red_escopo = "porta_executor_divergiu_do_ato_autorizado"
        if compromisso_injetado:
            red_escopo = ("compromisso_sem_continuacao_publicado"
                          if any(compromisso_injetado in t for t in textos) else
                          "rejeicao_sem_resposta_observavel" if not textos else "")
        resultados.append({"caso": caso, "turno": turno, "recebidos": recebidos,
            "modelos": modelos, "fases": fases, "falas_porta_isolada": falas,
            "textos_publicados": textos,
            "conclusoes_isoladas": conclusoes,
            "compromisso_injetado": compromisso_injetado,
            "continuacao_devida": deve_continuar,
            "continuacao_alcancada": bool(modelos),
            "reentrada_porta_operacional": reentrada,
            "primeira_fronteira_red": red_escopo or (
                "prioridade_consumiu_ato_conversacional" if deve_continuar and not modelos else
                "continuacao_reentrou_porta_operacional" if reentrada else
                "autoria_mista_nao_preservou_contrato" if deve_continuar
                and not compromisso_injetado
                and (mental.get("plano_turno_atual") or {}).get("fase") == "tratado_prioritario_parcial" else ""),
            "plano": mental.get("plano_turno_atual")})
    return {"instalacao": instalacao, "resultados": resultados,
            "transportes": transportes, "selecao_persistida": selecao,
            "ablacao_projecao": ablacao_projecao,
            "ablacao_avisos": ablacao_avisos,
            "ablacao_nucleo": ablacao_nucleo,
            "realizacao_controlada": realizacao_controlada,
            "painel_pospostas": painel_pospostas,
            "contraprova_compromisso": contraprova_compromisso,
            "contraprova_reparo": contraprova_reparo,
            "contraprova_retornar_nao_tratado": contraprova_retornar_nao_tratado}


def coletar(*, contraprova_retornar_nao_tratado: bool = False, modelo_real: bool = False,
            ablacao_projecao: bool = False, ablacao_avisos: bool = False, painel_pospostas: bool = False,
            contraprova_compromisso: bool = False, contraprova_reparo: bool = False,
            ablacao_nucleo: bool = False, realizacao_controlada: bool = False) -> dict:
    if realizacao_controlada and (ablacao_nucleo or ablacao_projecao or ablacao_avisos or painel_pospostas or contraprova_retornar_nao_tratado or contraprova_reparo):
        raise ValueError("realização controlada isolada de outras intervenções")
    if ablacao_nucleo and (ablacao_projecao or ablacao_avisos or painel_pospostas or contraprova_retornar_nao_tratado or contraprova_compromisso or contraprova_reparo):
        raise ValueError("uma intervenção causal: núcleo isolado de outras ablações/contraprovas")
    if contraprova_reparo and (modelo_real or ablacao_projecao or ablacao_avisos or painel_pospostas or contraprova_retornar_nao_tratado or contraprova_compromisso):
        raise ValueError("contraprova de reparo isolada de outras intervenções")
    if contraprova_compromisso and (modelo_real or ablacao_projecao or ablacao_avisos or painel_pospostas or contraprova_retornar_nao_tratado):
        raise ValueError("contraprova de compromisso isolada de outras intervenções")
    if painel_pospostas and (modelo_real or ablacao_projecao or ablacao_avisos or contraprova_retornar_nao_tratado):
        raise ValueError("painel de segmentação isolado de ablações/modelo real/contraprova")
    if ablacao_projecao and ablacao_avisos:
        raise ValueError("uma intervenção causal por coleta")
    if (ablacao_projecao or ablacao_avisos) and contraprova_retornar_nao_tratado:
        raise ValueError("não misturar ablação de autoria com reentrada operacional")
    if not modelo_real:
        return _coletar(contraprova_retornar_nao_tratado=contraprova_retornar_nao_tratado,
                        ablacao_projecao=ablacao_projecao, ablacao_avisos=ablacao_avisos, painel_pospostas=painel_pospostas,
                        contraprova_compromisso=contraprova_compromisso, contraprova_reparo=contraprova_reparo,
                        ablacao_nucleo=ablacao_nucleo, realizacao_controlada=realizacao_controlada)
    if contraprova_retornar_nao_tratado:
        raise ValueError("contraprova e modelo real não podem ser combinados")
    from mente_laylay.integracao.instancia_unica import adquirir_instancia_unica
    instancia = adquirir_instancia_unica(RAIZ / "laylay.py")
    if not instancia.adquirida or instancia.handle is None:
        instancia.liberar()
        raise RuntimeError("mutex indisponível/Laylay aberta; sessão não interrompida")
    try:
        return _coletar(modelo_real=True, ablacao_projecao=ablacao_projecao, ablacao_avisos=ablacao_avisos,
                        ablacao_nucleo=ablacao_nucleo, realizacao_controlada=realizacao_controlada)
    finally:
        instancia.liberar()


def _coletar(*, contraprova_retornar_nao_tratado: bool = False, modelo_real: bool = False,
             ablacao_projecao: bool = False, ablacao_avisos: bool = False, painel_pospostas: bool = False,
             contraprova_compromisso: bool = False, contraprova_reparo: bool = False,
             ablacao_nucleo: bool = False, realizacao_controlada: bool = False) -> dict:
    fontes = [Path(__file__).relative_to(RAIZ).as_posix(), "laylay.py",
        "scripts/analises/sonda_escopo_propostas_mistas.py"] + [
        "mente_laylay/" + p for p in (
            "autonomia/comandos_imediatos.py", "autonomia/resposta_ia_runtime.py",
            "autonomia/coordenador_intencao.py", "autonomia/composicao_ciclo_comandos.py",
            "autonomia/analise_comandos.py", "autonomia/orquestrador_deterministico.py",
            "autonomia/contexto_resposta_ia.py", "cognicao/modalidade_turno.py",
            "autonomia/dispatcher_comandos_json.py", "autonomia/finalizacao_execucao_ia.py",
            "personalidade/orquestrador_fala_runtime.py", "personalidade/confirmacao_llm.py",
            "cognicao/decisao_turno.py", "cognicao/escopo_autorizacao.py",
            "cognicao/contratos_turno.py", "cognicao/orquestrador_turno_runtime.py",
            "cognicao/guardiao_alegacoes.py",
            "cognicao/contrato_fala.py", "cognicao/validacao_contrato_fala.py",
        )]
    if ablacao_projecao:
        fontes += ["mente_laylay/especialistas/mapa_habilidades.py",
                   "mente_laylay/especialistas/capacidades.py",
                   "mente_laylay/memoria_mental/disponibilidade_operacional.py"]
    if modelo_real:
        fontes += ["scripts/analises/sonda_escopo_geracao_real.py", "configuracao.env",
                   "mente_laylay/integracao/llm_http.py", "mente_laylay/integracao/registro_conversa_llm.py"]
    if ablacao_nucleo or realizacao_controlada:
        fontes += ["mente_laylay/cognicao/geracao_concreta.py"]
    def hashes():
        return {p: hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in fontes}
    antes = hashes()
    base = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True)}
    with tempfile.TemporaryDirectory(prefix="laylay_prioridade_") as pasta:
        env = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off",
            LAYLAY_NEURAL_COLETA_ENTRADAS="0", LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
            LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
            LAYLAY_PRESENCA="0", LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
            LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0", GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
        codigo = ("import sys,json; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
            "from scripts.analises.sonda_prioridade_turnos_mistos import coletar_instalado; "
            "r=coletar_instalado(Path(sys.argv[2]),contraprova_retornar_nao_tratado=sys.argv[3]=='1',modelo_real=sys.argv[4]=='1',ablacao_projecao=sys.argv[5]=='1',ablacao_avisos=sys.argv[6]=='1',painel_pospostas=sys.argv[7]=='1',contraprova_compromisso=sys.argv[8]=='1',contraprova_reparo=sys.argv[9]=='1',ablacao_nucleo=sys.argv[10]=='1',realizacao_controlada=sys.argv[11]=='1'); "
            "sys.__stdout__.write('PRIORIDADE_JSON='+json.dumps(r,ensure_ascii=False)+'\\n')")
        processo = subprocess.run([sys.executable, "-c", codigo, str(RAIZ), pasta,
                                  "1" if contraprova_retornar_nao_tratado else "0",
                                  "1" if modelo_real else "0", "1" if ablacao_projecao else "0",
                                  "1" if ablacao_avisos else "0", "1" if painel_pospostas else "0",
                                  "1" if contraprova_compromisso else "0", "1" if contraprova_reparo else "0",
                                  "1" if ablacao_nucleo else "0", "1" if realizacao_controlada else "0"],
            cwd=RAIZ, env=env, capture_output=True, text=True, encoding="utf-8",
            timeout=600 if modelo_real and ablacao_nucleo else 180 if modelo_real else 60)
    linhas = [l for l in processo.stdout.splitlines() if l.startswith("PRIORIDADE_JSON=")]
    if processo.returncode or len(linhas) != 1:
        raise RuntimeError("Não alcançou a fronteira:\n" + processo.stderr[-3000:] + processo.stdout[-1500:])
    instalado = json.loads(linhas[0].split("=", 1)[1])
    depois = hashes()
    return {**base, **instalado, "hashes_antes": antes, "hashes_depois": depois,
        "logs_subprocesso": "\n".join(l for l in processo.stdout.splitlines()
                                     if not l.startswith("PRIORIDADE_JSON=")),
        "stderr_subprocesso": processo.stderr,
        "fontes_estaveis": antes == depois, "runtime_main_validado": False,
        "modelo_real_consultado": any(t.get("status") == 200 for t in instalado["transportes"]),
        "efeitos_externos_executados": False,
        "voz_validada": False, "holdout": False,
        "limite": "prioridade/coordenador instalados; namespace de capacidades restrito, portas de efeitos/fala/modelo isoladas"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--contraprova-retorno", action="store_true",
                        help="somente em memória: recusa o encerramento após a prioridade")
    parser.add_argument("--modelo-real", action="store_true", help="seis autorias Ollama locais, mutex obrigatório")
    parser.add_argument("--painel-pospostas", action="store_true", help="extensão de quatro condições pospostas; somente portas isoladas")
    parser.add_argument("--contraprova-compromisso", action="store_true", help="injeta compromisso inválido na autoria condicional; sem modelo real")
    parser.add_argument("--contraprova-reparo", action="store_true", help="injeta pessoa divergente seguida de reparo válido; sem modelo real")
    parser.add_argument("--ablacao-projecao", action="store_true",
                        help="24 autorias: controle/projeção canônica, duas repetições; só diagnóstico")
    parser.add_argument("--ablacao-avisos", action="store_true",
                        help="24 autorias: controle/aviso retido só no host; só diagnóstico")
    parser.add_argument("--ablacao-nucleo", action="store_true",
                        help="24 turnos: controle/núcleo canônico, duas repetições; só diagnóstico")
    parser.add_argument("--realizacao-controlada", action="store_true",
                        help="três condicionais com vínculo literal da redação; somente sonda")
    args = parser.parse_args()
    destino = args.saida.resolve()
    if not destino.is_relative_to((RAIZ / "resultados_testes").resolve()) or destino.exists():
        parser.error("saída nova dentro de resultados_testes")
    relatorio = coletar(contraprova_retornar_nao_tratado=args.contraprova_retorno, modelo_real=args.modelo_real,
                       ablacao_projecao=args.ablacao_projecao, ablacao_avisos=args.ablacao_avisos,
                       painel_pospostas=args.painel_pospostas, contraprova_compromisso=args.contraprova_compromisso,
                       contraprova_reparo=args.contraprova_reparo, ablacao_nucleo=args.ablacao_nucleo,
                       realizacao_controlada=args.realizacao_controlada)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as arquivo:
        json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
    print(json.dumps([{ "id": r["caso"]["id"], "recebidos": len(r["recebidos"]),
        "modelos": len(r["modelos"]), "red": r["primeira_fronteira_red"]}
        for r in relatorio["resultados"]], ensure_ascii=False))
    return int(not relatorio["fontes_estaveis"] or any(
        r["primeira_fronteira_red"] for r in relatorio["resultados"]))


if __name__ == "__main__":
    raise SystemExit(main())
