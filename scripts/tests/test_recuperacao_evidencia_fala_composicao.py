"""Recuperação da própria fala pela composição instalada, sem efeitos externos.

Os receipts são sintéticos nas folhas; publicação, memória, continuidade e
preparação de prompt são os componentes reais registrados em laylay.py.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope="module")
def recuperacao_instalada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("recuperacao_fala_instalada")
    codigo = textwrap.dedent(r'''
        import json, os, sys, traceback
        from pathlib import Path
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
        from mente_laylay.integracao import instancia_unica
        pasta = Path(os.environ["LAYLAY_RECUPERACAO_MEMORIA_TESTE"])
        sqlite = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: sqlite(self, str(pasta / Path(caminho or "laylay.sqlite").name))
        resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: resumo(self, pasta_memoria=str(pasta / "resumo"), **k)
        pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: pessoas(self, caminho=pasta / "pessoas.json", **k)
        central = CentralNotificacoesRuntime.__init__
        CentralNotificacoesRuntime.__init__ = lambda self, caminho, **k: central(self, str(pasta / "central.json"), **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(str(ident) + ".recuperacao-" + str(os.getpid()), **k)
        transportes = []
        selecao_modelo = None
        if os.environ.get("LAYLAY_RECUPERACAO_MODELO_LOCAL_REAL") == "1":
            import requests
            from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
            selecao_modelo = selecao_local()
            requests.sessions.Session.request = criar_guarda_http_local(
                selecao_modelo, transportes, requests.sessions.Session.request)
        import laylay as root
        root._rosto_oled_runtime.abrir_serial = lambda *_a: (_ for _ in ()).throw(AssertionError('USB proibido'))
        root._rosto_oled_runtime.abrir_tcp = lambda *_a: (_ for _ in ()).throw(AssertionError('TCP proibido'))
        from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        estado = root._estado_compartilhado_runtime
        orquestrador = root._orquestrador_fala_runtime
        for nome in ("_coleta_entradas_neurais", "_especialista_neural_comandos_runtime", "_interpretador_semantico_runtime", "_pesquisa_contextual_runtime"):
            root._composicao_turno_runtime._servicos[nome] = None
        # Não substituir publicador, registro de memória, continuidade ou prompt.
        # Inferência/voz são folhas controladas; nenhuma conexão externa.
        executar_modelo_instalado = RegistroModeloLLM.executar
        falar_voz_instalada = root._voz_runtime.falar
        RegistroModeloLLM.executar = lambda self, pedido: ResultadoModelo("", False)
        root._voz_runtime.falar = lambda *_a, **_k: False
        textos = []
        trilhas_publicacao = []
        aceite_texto = True
        def observar_texto(texto, *_a, **_k):
            textos.append(texto)
            trilhas_publicacao.append({"texto": texto, "pilha": [
                {"arquivo": f.filename, "linha": f.lineno, "funcao": f.name}
                for f in traceback.extract_stack(limit=14)]})
            return aceite_texto
        orquestrador.registrar_observador_texto_final(observar_texto)
        saida = {"selecao_modelo": selecao_modelo, "owners": {
            "fala": root.falar_com_lipsync.__self__ is orquestrador,
            "publicador": root._registrar_resultado_execucao.__self__ is root._adaptadores_aplicacao_runtime,
            "memoria": root._registrar_mente_curta.__self__ is root._adaptadores_aplicacao_runtime,
        }, "casos": {}}
        def publicar(intent, identidade, status, alvo, parametros, fala, *, confirmado):
            adapter = AdaptadorResultadoOperacional(
                {"intent": intent, "id_solicitacao": identidade}, {**parametros, "alvo": alvo},
                "pedido da sonda", "pc_a", root._contexto_intencao_runtime.montar())
            adapter.marcar_resultado(status, confirmado, confirmado=confirmado,
                evidencia_confirmacao="observacao_" + identidade)
            adapter.falar_texto_da_invocacao(fala)
        for nome, voz_aceita in (("simples", False), ("composto_parcial", False),
                                ("simples_voz_aceita", True), ("composto_parcial_voz_aceita", True),
                                ("composto_arquivos_email", False), ("confirmacao_firmware", False),
                                ("confirmacao_owner", False), ("composto_integral", False),
                                ('composto_integral_modelo', False)):
            estado.substituir("mental", criar_estado_mental_inicial())
            textos.clear()
            root._voz_runtime.falar = lambda *_a, **_k: voz_aceita
            simples = nome.startswith("simples")
            entrada = "pausa a música" if simples else "liga a luz e coloca a playlist piano"
            if nome == "composto_arquivos_email":
                entrada = "cria o arquivo relatorio.txt e consulta o e-mail de reunião"
            if nome.startswith('composto_integral'):
                entrada = ('liga a luz, abre piano, cria relatorio.txt, consulta o e-mail, '
                    'pausa a música, move o corpo, ajusta o volume e abre a calculadora')
                if nome.endswith('_modelo'):
                    entrada = ('liga a luz da sala, abre piano, liga a luz da cozinha, abre jazz, '
                        'liga a luz do quarto, abre rock, liga a luz da varanda e abre blues')
            root._iniciar_planejamento_turno(entrada, origem="teste_recuperacao_fala")
            origem_id = str(estado.obter_copia("mental", "turno_atual", {})["id"])
            if nome in {"confirmacao_firmware", "confirmacao_owner"}:
                # Folha sintética: publica receipt, sem acionar corpo/dispositivo.
                firmware = nome == 'confirmacao_firmware'
                publicar('CORPO_MOVER' if firmware else 'CORPO_COMPANHIA', nome + '-origem',
                    'resultado_registrado', 'corpo', {},
                    'Registrei a confirmação do firmware.' if firmware else 'Registrei a concessão do owner.', confirmado=True)
                ids = [nome + '-origem']
            elif simples:
                publicar("MEDIA_CONTROL", "pausa-origem", "pausado", "música",
                    {"acao": "pause"}, "Pausei a música.", confirmado=True)
                ids = ["pausa-origem"]
            elif nome.startswith('composto_integral'):
                ctx = root._contexto_intencao_runtime.montar()
                especificacoes = [('IOT_CONTROL', 'lâmpada', True), ('PLAYLIST_PLAY', 'piano', False),
                    ('CREATE_FILE', 'relatorio.txt', True), ('EMAIL_READ', 'mensagem de reunião', False),
                    ('MEDIA_CONTROL', 'música', True), ('CORPO_MOVER', 'corpo', False),
                    ('VOLUME_SET', 'volume', True), ('OPEN_APP', 'calculadora', False)]
                if nome.endswith('_modelo'):
                    especificacoes = [('IOT_CONTROL', 'lâmpada da sala', True), ('PLAYLIST_PLAY', 'piano', False),
                        ('IOT_CONTROL', 'lâmpada da cozinha', True), ('PLAYLIST_PLAY', 'jazz', False),
                        ('IOT_CONTROL', 'lâmpada do quarto', True), ('PLAYLIST_PLAY', 'rock', False),
                        ('IOT_CONTROL', 'lâmpada da varanda', True), ('PLAYLIST_PLAY', 'blues', False)]
                ids = []
                with ctx['_agrupar_resultados_operacionais'](texto_usuario=entrada):
                    for i, (intent, alvo, confirmado) in enumerate(especificacoes):
                        identidade = f'integral-{i}'
                        ids.append(identidade)
                        fala_folha = (f'Não consegui concluir o pedido em {alvo}.' if nome.endswith('_modelo')
                            else f'Falhou o pedido de {alvo}.')
                        status = ('ligado' if intent == 'IOT_CONTROL' and confirmado and nome.endswith('_modelo')
                            else 'resultado' if confirmado else 'falha_execucao')
                        publicar(intent, identidade, status, alvo, {},
                            f'Registrei resultado de {alvo}.' if confirmado else fala_folha,
                            confirmado=confirmado)
            elif nome == "composto_arquivos_email":
                ctx = root._contexto_intencao_runtime.montar()
                with ctx["_agrupar_resultados_operacionais"](texto_usuario=entrada):
                    publicar("CREATE_FILE", "arquivo-origem", "arquivo_criado", "relatorio.txt",
                        {"caminho": "relatorio.txt"}, "Criei relatorio.txt.", confirmado=True)
                    publicar("EMAIL_READ", "email-origem", "falha_execucao", "mensagem de reunião",
                        {"assunto": "reunião"}, "Não consegui consultar a mensagem.", confirmado=False)
                ids = ["arquivo-origem", "email-origem"]
            else:
                ctx = root._contexto_intencao_runtime.montar()
                with ctx["_agrupar_resultados_operacionais"](texto_usuario=entrada) as lote:
                    publicar("IOT_CONTROL", "luz-origem", "ligado", "lâmpada do quarto",
                        {"alvo": "lâmpada do quarto", "acao": "ligar"}, "Liguei a lâmpada do quarto.", confirmado=True)
                    publicar("PLAYLIST_PLAY", "playlist-origem", "falha_execucao", "piano",
                        {"nome_playlist": "piano"}, "Não consegui abrir a playlist piano.", confirmado=False)
                ids = ["luz-origem", "playlist-origem"]
            fala_original = textos[-1]
            antes = estado.retrato_dominio("mental")
            root._registrar_mente_curta(entrada, fala_original)
            root._iniciar_planejamento_turno("coloca o volume em 30", origem="teste_recuperacao_intermediario")
            publicar("VOLUME_SET", "volume-intermediario", "volume_ajustado", "volume do sistema",
                {"volume": 30}, "Ajustei o volume para 30.", confirmado=True)
            root._registrar_mente_curta("coloca o volume em 30", textos[-1])
            pergunta = 'Quando você disse "' + fala_original + '", o que estava confirmado em cada ação?'
            root._iniciar_planejamento_turno(pergunta, origem="teste_recuperacao_pergunta")
            mental = estado.retrato_dominio("mental")
            pacote = root._contexto_prompt_runtime.preparar_pacote(pergunta)
            rapido = root._contexto_prompt_runtime.preparar_instrucao_rapida(pergunta)
            projecoes = {}
            for rota, entrada_modelo in (
                ('normal', [*pacote.mensagens, {'role': 'user', 'content': pergunta}]),
                ('rapido', [{'role': 'system', 'content': rapido}, {'role': 'user', 'content': pergunta}]),
            ):
                projetado = root._contexto_prompt_runtime.preparar_envio_modelo(
                    entrada_modelo, turno_id=mental['turno_atual']['id'])
                projecoes[rota] = {'contexto_fechado': projetado.contexto_fechado,
                    'mensagens': projetado.mensagens,
                    'response_format': projetado.contrato_saida.response_format if projetado.contrato_saida else None}
            saida["casos"][nome] = {
                "fala_original": fala_original, "pergunta": pergunta,
                "turno_origem": origem_id,
                "receipts_origem": antes["plano_turno_atual"]["comandos"],
                "ids_esperados": ids,
                "ultimo_receipt": mental["ultima_acao_contrato"]["id_solicitacao"],
                "normal": pacote.prompt_sistema,
                "rapido": rapido,
                "modalidade": mental["turno_atual"].get("modalidade"),
                "autoriza_execucao": mental["turno_atual"].get("autoriza_execucao"),
                "plano_pergunta": mental["plano_turno_atual"],
                "projecoes": projecoes,
                "textos_publicados": list(textos),
            }
            if nome in {"simples", "composto_parcial", "composto_arquivos_email", "confirmacao_firmware", "confirmacao_owner", 'composto_integral', 'composto_integral_modelo'}:
                chamadas = []
                pedidos_modelo = []
                respostas_modelo = []
                inicio_transportes = len(transportes)
                comandos_propostos = []
                from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_fala_historica
                resposta = realizacoes_fala_historica(
                    mental["plano_turno_atual"]["contrato_fala"]["evidencia_fala_historica"])[0]
                arquivo_replay = os.environ.get("LAYLAY_RESPOSTA_REPLAY_ARQUIVO")
                if arquivo_replay:
                    replay = json.loads(Path(arquivo_replay).read_text(encoding="utf-8"))
                    caso_replay = next((c for c in replay["casos"] if c["caso"] == nome), None)
                    if caso_replay:
                        resposta = caso_replay["fala_bruta"]
                        comandos_propostos = caso_replay.get("comandos", [])
                def responder(self, pedido):
                    chamadas.append([dict(m) for m in pedido.mensagens])
                    pedidos_modelo.append({'contexto_fechado': pedido.contexto_fechado,
                        'tipo_chamada': pedido.tipo_chamada,
                        'response_format': pedido.contrato_saida.response_format if pedido.contrato_saida else None})
                    if selecao_modelo and (not os.environ.get('LAYLAY_RECUPERACAO_CASO_REAL')
                        or nome == os.environ['LAYLAY_RECUPERACAO_CASO_REAL']):
                        resultado = executar_modelo_instalado(self, pedido)
                        respostas_modelo.append({"texto": resultado.texto, "sucesso": resultado.sucesso,
                            "tipo_chamada": pedido.tipo_chamada, "com_tools": pedido.com_tools})
                        return resultado
                    if not arquivo_replay and pedido.contexto_fechado:
                        from mente_laylay.cognicao.suporte_autoria import segmentar_realizacao_autoral
                        dados = pedido.contrato_saida.decodificar_json(json.dumps({
                            'suporte_proposicoes': [{'texto': parte, 'fontes': []}
                                for parte in segmentar_realizacao_autoral(resposta)], 'comandos': []}))
                    else:
                        dados = {"fala": resposta, "comandos": comandos_propostos, "emocao": "calma", "nivel_emocao": 1}
                    resultado = ResultadoModelo(json.dumps(dados, ensure_ascii=False), True)
                    respostas_modelo.append({'texto': resultado.texto, 'sucesso': True,
                        'tipo_chamada': pedido.tipo_chamada, 'com_tools': pedido.com_tools})
                    return resultado
                RegistroModeloLLM.executar = responder
                verificacoes = []
                verificar_original = root._verificar_fala_turno_mente
                def verificar(fala, **kwargs):
                    resultado = verificar_original(fala, **kwargs)
                    verificacoes.append({"entrada": fala, "plano": kwargs["plano"],
                        "resultado": resultado})
                    return resultado
                root._verificar_fala_turno_mente = verificar
                quantidade = len(textos)
                inicio_trilhas = len(trilhas_publicacao)
                root._resposta_ia_runtime.processar(pergunta)
                saida["casos"][nome]["turno_completo"] = {
                    "resposta_esperada": resposta,
                    "chamadas": chamadas,
                    "pedidos_modelo": pedidos_modelo,
                    "textos_novos": textos[quantidade:],
                    "trilhas_publicacao": trilhas_publicacao[inicio_trilhas:],
                    "verificacoes": verificacoes,
                    "respostas_modelo": respostas_modelo,
                    "transportes": transportes[inicio_transportes:],
                    "mental_depois": estado.retrato_dominio("mental"),
                }
                root._verificar_fala_turno_mente = verificar_original
                RegistroModeloLLM.executar = lambda self, pedido: ResultadoModelo("", False)
            variantes = []
            for consulta in ('Por que você disse "' + fala_original + '"?',
                             'Você pode explicar "' + fala_original + '"?'):
                root._iniciar_planejamento_turno(consulta, origem="teste_variante_retrospectiva")
                variante = estado.retrato_dominio("mental")
                variantes.append({"texto": consulta, "turno": variante["turno_atual"],
                    "contrato": variante["plano_turno_atual"]["contrato_fala"]})
            saida["casos"][nome]["variantes"] = variantes
        # Exercita o contrato de entrega também fora da pergunta histórica.
        # A composição/emitidor/pipeline são os instalados; só reprodução e
        # consumidores externos são controlados. A deduplicação da voz é real.
        from mente_laylay.autonomia.pre_fluxo_contextual import executar_pipeline_pre_fluxo
        saida["entregas"] = {}
        for nome, aceite_texto, voz_aceita in (("texto_sem_voz", True, False),
                ("voz_sem_texto", False, True), ("nenhum_canal", False, False),
                ("deduplicacao_voz_real", True, None)):
            estado.substituir("mental", criar_estado_mental_inicial())
            root._iniciar_planejamento_turno("vamos conversar sobre cores", origem="teste_entrega")
            textos.clear()
            fala_entrega = "Podemos conversar sobre cores."
            voz = root._voz_runtime
            if voz_aceita is None:
                voz.iniciar_worker = lambda: None
                voz._ultima_solicitacao_fala = ""
                voz._ultima_solicitacao_fala_ts = 0.0
                voz._ultima_chave_turno_emitida = 0.0
                voz._pedido_turno_pendente = None
                voz.falar = falar_voz_instalada
                assert voz.falar(fala_entrega) is True
            else:
                voz.falar = lambda *_a, **_k: voz_aceita
            chamadas_seguintes = []
            historico_antes = len(estado.memoria_conversa.get("messages", []))
            def etapa_entrega():
                return root._emitir_resposta_curta("vamos conversar sobre cores", fala_entrega), "entrega"
            def etapa_seguinte():
                chamadas_seguintes.append(True)
                return False, "seguinte"
            tratado = executar_pipeline_pre_fluxo({}, "vamos conversar sobre cores",
                [etapa_entrega, etapa_seguinte])
            mental_entrega = estado.retrato_dominio("mental")
            saida["entregas"][nome] = {"tratado": tratado, "textos_tentados": list(textos),
                "seguintes": chamadas_seguintes, "mental": mental_entrega,
                "historico_adicionado": list(estado.memoria_conversa.get("messages", []))[historico_antes:],
                "fila_voz": voz.fila.qsize()}
        from dataclasses import asdict
        sys.__stdout__.write("RECUPERACAO_INSTALADA " + json.dumps(saida, ensure_ascii=False, default=asdict) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_RECUPERACAO_MEMORIA_TESTE=str(pasta)),
        capture_output=True, text=True, encoding="utf-8",
        timeout=180 if os.environ.get("LAYLAY_RECUPERACAO_MODELO_LOCAL_REAL") == "1" else 60,
    )
    assert processo.returncode == 0, processo.stdout[-2000:] + processo.stderr[-5000:]
    linha = next(x.removeprefix("RECUPERACAO_INSTALADA ") for x in processo.stdout.splitlines()
                 if x.startswith("RECUPERACAO_INSTALADA "))
    dados = json.loads(linha)
    evidencia = os.environ.get("LAYLAY_EVIDENCIA_RECUPERACAO")
    if evidencia:
        destino = Path(evidencia)
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("x", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    return dados


@pytest.mark.parametrize('rota', ['normal', 'rapido'])
@pytest.mark.parametrize('nome', ['simples', 'composto_parcial', 'composto_arquivos_email',
    'confirmacao_firmware', 'confirmacao_owner'])
def test_owner_instalado_negocia_realizacao_historica_integral_sem_prosa_livre(nome, rota, recuperacao_instalada):
    caso = recuperacao_instalada['casos'][nome]
    projetado = caso['projecoes'][rota]
    assert projetado['contexto_fechado'], 'primeira fronteira: envio perde o limite conferido pelo owner'
    esquema = projetado['response_format']['json_schema']['schema']
    permitidas = esquema['properties']['suporte_proposicoes']['items']['properties']['texto']['enum']
    turno = caso['turno_completo']
    assert turno['textos_novos'] == [permitidas[0]]
    assert len(projetado['mensagens']) == 2
    assert projetado['mensagens'][-1]['content'] == caso['pergunta']
    for pedido, mensagens in zip(turno['pedidos_modelo'], turno['chamadas'], strict=True):
        # O resumo diário usa historicamente tipo_chamada=principal também.
        # Só o pedido da mesma consulta participa desta obrigação autoral.
        if mensagens[-1]['content'] == caso['pergunta']:
            assert pedido['contexto_fechado'] and pedido['response_format'] == projetado['response_format']
    assert not turno['mental_depois']['plano_turno_atual']['comandos']


@pytest.mark.parametrize('nome', ['simples', 'composto_parcial', 'confirmacao_firmware', 'confirmacao_owner'])
def test_qwen_real_entrega_realizacao_negociada_antes_da_revisao_final(nome, recuperacao_instalada):
    if not recuperacao_instalada['selecao_modelo']:
        pytest.skip('Exige LAYLAY_RECUPERACAO_MODELO_LOCAL_REAL=1.')
    caso = recuperacao_instalada['casos'][nome]
    turno = caso['turno_completo']
    assert len(turno['transportes']) == 1, 'contar HTTP efetivo, não wrappers aninhados'
    http = turno['transportes'][0]
    assert http['status'] == 200
    resposta = json.loads(http['resposta_http'])
    assert resposta['choices'][0]['finish_reason'] == 'stop'
    bruto = json.loads(resposta['choices'][0]['message']['content'])
    esquema = http['payload']['response_format']['json_schema']['schema']
    fala = esquema['properties']['suporte_proposicoes']['items']['properties']['texto']['enum'][0]
    assert bruto == {'comandos': [], 'suporte_proposicoes': [{'texto': fala, 'fontes': []}]}
    assert turno['textos_novos'] == [fala]
    assert not turno['mental_depois']['plano_turno_atual']['comandos']


@pytest.mark.parametrize('rota', ['normal', 'rapido'])
@pytest.mark.parametrize('nome', ['composto_integral', 'composto_integral_modelo'])
def test_historico_integral_instalado_preserva_oito_receipts_e_suporte(nome, rota, recuperacao_instalada):
    caso = recuperacao_instalada['casos'][nome]
    projetado = caso['projecoes'][rota]
    assert len(caso['receipts_origem']) == 8
    fonte = caso['plano_pergunta']['contrato_fala']['evidencia_fala_historica']['falas'][0]
    assert [r['id_solicitacao'] for r in fonte['resultados']] == caso['ids_esperados']
    assert projetado['contexto_fechado']
    esquema = projetado['response_format']['json_schema']['schema']
    unidades = esquema['properties']['suporte_proposicoes']
    partes = unidades['items']['properties']['texto']['enum']
    fala = ' '.join(partes)
    assert len(fala) > 500 and 1 < unidades['maxItems'] <= 8
    assert all(0 < len(p) <= 500 for p in partes)
    for r in fonte['resultados']:
        assert f'alvo "{r["alvo"]}"' in fala and f'"{r["confirmacao_oferecida"]}"' in fala
    assert sum(r['confirmado'] is True for r in fonte['resultados']) == 4
    assert fala.count('efeito confirmado') == sum(r['confirmado'] is True
        and r['confirmacao_oferecida'] != 'indisponivel' for r in fonte['resultados'])
    assert fala.count('efeito não confirmado') == 4
    turno = caso['turno_completo']
    assert turno['textos_novos'] == [fala]
    assert not turno['mental_depois']['plano_turno_atual']['comandos']
    respostas = [json.loads(r['texto']) for r in turno['respostas_modelo'] if r['sucesso']]
    respostas_autorais = [r for r in respostas if r.get('fala') == fala]
    if nome.endswith('_modelo'):
        assert respostas_autorais
    else:
        assert not turno['chamadas'], 'controle: esse texto conclui no pré-fluxo instalado'
    for resposta in respostas_autorais:
        from mente_laylay.cognicao.suporte_autoria import conferir_suporte_proposicoes
        assert conferir_suporte_proposicoes(resposta)[1]['cobertura_textual'] is True


def test_qwen_real_gera_realizacao_integral_em_varias_unidades(recuperacao_instalada):
    if not recuperacao_instalada['selecao_modelo']:
        pytest.skip('Exige LAYLAY_RECUPERACAO_MODELO_LOCAL_REAL=1.')
    caso = recuperacao_instalada['casos']['composto_integral_modelo']
    turno = caso['turno_completo']
    assert len(turno['transportes']) == 1
    http = turno['transportes'][0]
    assert http['status'] == 200
    resposta = json.loads(http['resposta_http'])
    assert resposta['choices'][0]['finish_reason'] == 'stop'
    bruto = json.loads(resposta['choices'][0]['message']['content'])
    unidades = http['payload']['response_format']['json_schema']['schema']['properties']['suporte_proposicoes']
    partes = unidades['items']['properties']['texto']['enum']
    assert bruto == {'comandos': [], 'suporte_proposicoes': [{'texto': p, 'fontes': []} for p in partes]}
    assert len(' '.join(partes)) > 500 and turno['textos_novos'] == [' '.join(partes)]


def test_recuperacao_usa_owners_instalados_e_pergunta_nao_autoriza_efeito(recuperacao_instalada):
    assert all(recuperacao_instalada["owners"].values())
    for caso in recuperacao_instalada["casos"].values():
        assert caso["receipts_origem"], "Receipt ausente antes da recuperação"
        assert caso["fala_original"] in caso["textos_publicados"]
        assert caso["ultimo_receipt"] == "volume-intermediario"
        assert caso["autoriza_execucao"] is False


@pytest.mark.parametrize("nome", ["simples", "composto_parcial", "simples_voz_aceita", "composto_parcial_voz_aceita", "composto_arquivos_email"])
@pytest.mark.parametrize("rota", ["normal", "rapido"])
def test_consulta_a_fala_anterior_recupera_evidencia_da_mesma_ocorrencia(nome, rota, recuperacao_instalada):
    caso = recuperacao_instalada["casos"][nome]
    assert caso["receipts_origem"] and caso["fala_original"] in caso["textos_publicados"]
    for identidade in caso["ids_esperados"]:
        assert "observacao_" + identidade in caso[rota], (
            "Primeira fronteira: publicação conhecia fala e receipt, mas a recuperação "
            f"{rota} perdeu a evidência {identidade} após outro turno."
        )


def test_pergunta_passa_pelo_runtime_instalado_sem_executar_nova_acao(recuperacao_instalada):
    turno = recuperacao_instalada["casos"]["simples"]["turno_completo"]
    assert turno["chamadas"]
    # O envio fechado leva a realização conferida no schema. A evidência
    # integral continua no plano do host, sem duplicá-la na geração.
    assert "observacao_pausa-origem" in json.dumps(
        recuperacao_instalada['casos']['simples']['plano_pergunta'], ensure_ascii=False)
    assert 'variavel' in json.dumps(turno['pedidos_modelo'][0]['response_format'], ensure_ascii=False)
    if recuperacao_instalada['selecao_modelo']:
        # A folha controlada escolhe a última opção. O modelo/owner podem
        # escolher outra realização integral do mesmo contrato de fonte.
        from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_fala_historica
        evidencia = recuperacao_instalada['casos']['simples']['plano_pergunta']['contrato_fala']['evidencia_fala_historica']
        assert len(turno['textos_novos']) == 1
        assert turno['textos_novos'][0] in realizacoes_fala_historica(evidencia)
    else:
        assert turno["resposta_esperada"] in turno["textos_novos"]


def test_juiz_recebe_a_mesma_evidencia_historica_que_o_modelo(recuperacao_instalada):
    for caso in recuperacao_instalada["casos"].values():
        plano = caso["plano_pergunta"]
        assert not plano["comandos"]
        evidencia = plano["contrato_fala"].get("evidencia_fala_historica")
        assert evidencia, "Primeira fronteira: evidência recuperada no prompt ausente do contrato do juiz."
        assert evidencia["autoriza_execucao"] is False
        assert [r["id_solicitacao"] for r in evidencia["falas"][0]["resultados"]] == caso["ids_esperados"]


@pytest.mark.parametrize('nome', ['simples', 'composto_parcial', 'composto_arquivos_email', 'confirmacao_firmware', 'confirmacao_owner'])
@pytest.mark.parametrize('rota', ['normal', 'rapido'])
def test_historico_instalado_conserva_premissa_de_escopo_do_receipt(nome, rota, recuperacao_instalada):
    caso = recuperacao_instalada['casos'][nome]
    receipts = {r['id_solicitacao']: r for r in caso['receipts_origem']}
    resultados = caso['plano_pergunta']['contrato_fala']['evidencia_fala_historica']['falas'][0]['resultados']
    for r in resultados:
        original = receipts[r['id_solicitacao']]
        assert original.get('confirmacao_oferecida'), 'controle: executor/registro do turno precisa carregar escopo'
        assert r.get('confirmacao_oferecida') == original['confirmacao_oferecida'], 'primeira fronteira: publicação/recuperação perdem a premissa do receipt'
        assert original['confirmacao_oferecida'] in caso[rota]
    turno = caso['turno_completo']
    assert len(turno['textos_novos']) == 1
    for r in resultados:
        assert f'no escopo registrado "{r["confirmacao_oferecida"]}"' in turno['textos_novos'][0]
    assert not turno['mental_depois']['plano_turno_atual']['comandos']


def test_contrato_instalado_preserva_parcialidade_tambem_em_arquivos_e_email(recuperacao_instalada):
    caso = recuperacao_instalada["casos"]["composto_arquivos_email"]
    turno = caso["turno_completo"]
    assert turno["textos_novos"]
    for fala in turno["textos_novos"]:
        assert 'alvo "relatorio.txt": execução registrada, efeito confirmado' in fala
        assert 'alvo "mensagem de reunião": execução não concluída, efeito não confirmado' in fala
        assert "não informa a causa" in fala
    assert not turno["mental_depois"]["plano_turno_atual"]["comandos"]


def test_perguntas_retrospectivas_naturais_usam_o_mesmo_contrato(recuperacao_instalada):
    for caso in recuperacao_instalada["casos"].values():
        for variante in caso["variantes"]:
            assert variante["turno"]["autoriza_execucao"] is False
            assert variante["turno"]["modalidade"] == "pergunta"
            evidencia = variante["contrato"].get("evidencia_fala_historica")
            assert evidencia, "Pergunta retrospectiva perdeu os receipts por causa da modalidade."
            assert [r["id_solicitacao"] for r in evidencia["falas"][0]["resultados"]] == caso["ids_esperados"]


def test_entrega_textual_no_pre_fluxo_nao_deve_cair_em_segunda_publicacao(recuperacao_instalada):
    # RED histórico independente da fidelidade factual: o aceite textual deve
    # concluir o pré-fluxo mesmo quando a porta de voz devolve False.
    turno = recuperacao_instalada["casos"]["composto_arquivos_email"]["turno_completo"]
    assert len(turno["textos_novos"]) == 1
    assert not turno["chamadas"], "Não gerar outra resposta depois da conclusão observável."


@pytest.mark.parametrize("nome", ["texto_sem_voz", "voz_sem_texto", "nenhum_canal", "deduplicacao_voz_real"])
def test_pipeline_instalado_conclui_por_canal_sem_falsificar_receipt_de_audio(nome, recuperacao_instalada):
    entrega = recuperacao_instalada["entregas"][nome]
    esperado = nome != "nenhum_canal"
    assert entrega["textos_tentados"] == ["Podemos conversar sobre cores."]
    assert entrega["tratado"] is esperado
    assert entrega["seguintes"] == ([] if esperado else [True])
    assert len(entrega["historico_adicionado"]) == (2 if esperado else 0)
    falas = entrega["mental"].get("registro_semantico", {}).get("falas_observadas", [])
    assert [f["canais"] for f in falas] == ([["texto_publicado"]] if nome in {"texto_sem_voz", "deduplicacao_voz_real"} else [])
    assert not entrega["mental"]["plano_turno_atual"]["comandos"]
    if nome == "deduplicacao_voz_real":
        assert entrega["fila_voz"] == 1, "A voz recusou a duplicata real sem apagar a conclusão textual."


@pytest.fixture(scope="module", params=[
    'Quando disse "Liguei lâmpada do quarto", a ligação foi confirmada por observação direta do sistema — a luz acendeu. Já o pedido de "piano" falhou porque o sistema não conseguiu executar a ação, e não houve confirmação de sucesso. A falha foi registrada como não executada, com evidência de que o comando não foi processado.',
    "No primeiro resultado há confirmação; para piano, o servidor estava indisponível.",
    "Eu me adiantei na fala, mas essa ação não foi executada nem confirmada.",
])
def replay_causal_instalado(request, tmp_path_factory):
    pasta = tmp_path_factory.mktemp("replay_causal")
    fonte = pasta / "propostas.json"
    fonte.write_text(json.dumps({"casos": [
        {"caso": "simples", "fala_bruta": "A pausa foi confirmada naquele pedido; isso não prova o estado atual."},
        {"caso": "composto_parcial", "fala_bruta": request.param,
         "comandos": [{"intent": "IOT_CONTROL", "parametros": {"alvo": "lâmpada do quarto", "acao": "desligar"}}]},
    ]}, ensure_ascii=False), encoding="utf-8")
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv("LAYLAY_RESPOSTA_REPLAY_ARQUIVO", str(fonte))
        ambiente.delenv("LAYLAY_EVIDENCIA_RECUPERACAO", raising=False)
        return recuperacao_instalada.__wrapped__(tmp_path_factory)


def test_replay_nao_publica_causa_sem_fonte_nem_apaga_sucesso_parcial(replay_causal_instalado):
    caso = replay_causal_instalado["casos"]["composto_parcial"]
    turno = caso["turno_completo"]
    assert len(turno["chamadas"]) == 1, "Cobertura ausente não deve tentar provar causalidade por outra geração."
    assert len(turno["textos_novos"]) == 1
    publicada = turno["textos_novos"][0]
    assert turno["resposta_esperada"] != publicada
    assert 'alvo "lâmpada do quarto": execução registrada, efeito confirmado' in publicada
    assert 'alvo "piano": execução não concluída, efeito não confirmado' in publicada
    assert "não informa a causa nem a etapa de processamento" in publicada
    assert "não comprova o estado atual" in publicada
    assert turno["mental_depois"]["ultima_acao_contrato"]["id_solicitacao"] == "volume-intermediario"
    assert not turno["mental_depois"]["plano_turno_atual"]["comandos"], "Histórico/proposta da LLM não pode criar execução."
    falas = turno["mental_depois"]["registro_semantico"]["falas_observadas"]
    assert falas[-1]["fala"] == publicada
    assert falas[-1]["resultados"] == [], "Explicação não é outro receipt de execução."
    assert not any(f["fala"] == turno["resposta_esperada"] for f in falas)
