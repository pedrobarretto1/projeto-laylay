from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from mente_laylay.cognicao import composicao_turno


def test_composicao_turno_filtra_e_congela_servicos(monkeypatch) -> None:
    capturas = []
    estado_runtime = object()
    normalizador_original = lambda texto: texto  # noqa: E731
    servicos = {
        "_estado_compartilhado_runtime": estado_runtime,
        "_normalizar_texto_com_apelidos": normalizador_original,
        "SEGREDO_FORA_DO_TURNO": "não reter",
    }

    def substituir(nome, retorno):
        def chamada(namespace_getter, *args, **kwargs):
            capturas.append((nome, namespace_getter(), args, kwargs))
            return retorno
        monkeypatch.setattr(composicao_turno, nome, chamada)

    substituir("iniciar_planejamento_turno", {"inicio": True})
    substituir("atualizar_planejamento_turno", {"fase": "executado"})
    substituir("verificar_fala_do_turno", {"fala": "oi"})
    substituir("registrar_leitura_semantica_principal", {"valida": True})

    runtime = composicao_turno.ComposicaoTurnoRuntime(servicos=servicos)
    servicos["_normalizar_texto_com_apelidos"] = lambda _texto: "mudou"
    servicos["novo_servico"] = object()

    assert runtime.iniciar("oi", origem="terminal") == {"inicio": True}
    assert runtime.atualizar("executado", comandos=[{"intent": "TESTE"}]) == {
        "fase": "executado"
    }
    assert runtime.verificar_fala("oi", origem="teste") == {"fala": "oi"}
    assert runtime.registrar_leitura_semantica("oi", {"valida": True}) == {
        "valida": True
    }

    for _, snapshot, _, _ in capturas:
        assert snapshot["_estado_compartilhado_runtime"] is estado_runtime
        assert snapshot["_normalizar_texto_com_apelidos"] is normalizador_original
        assert "SEGREDO_FORA_DO_TURNO" not in snapshot
        assert "novo_servico" not in snapshot
    assert "SEGREDO_FORA_DO_TURNO" not in runtime.servicos_registrados
    chamada_inicio = next(item for item in capturas if item[0] == "iniciar_planejamento_turno")
    assert chamada_inicio[3]["origem"] == "terminal"


def test_composicao_turno_preserva_setter_causal_do_estado_conversacional() -> None:
    setter = lambda *_args: None
    runtime = composicao_turno.ComposicaoTurnoRuntime(
        servicos={"_definir_emocao_conversacional": setter},
    )

    assert "_definir_emocao_conversacional" in runtime.servicos_registrados


def test_composicao_turno_encaminha_argumentos_sem_alterar_contrato(monkeypatch) -> None:
    recebidos = {}

    def atualizar(_namespace_getter, fase, *, comandos, erros, fala):
        recebidos.update(fase=fase, comandos=comandos, erros=erros, fala=fala)
        return recebidos

    def verificar(_namespace_getter, fala, *, origem):
        return {"fala": fala, "origem": origem}

    monkeypatch.setattr(composicao_turno, "atualizar_planejamento_turno", atualizar)
    monkeypatch.setattr(composicao_turno, "verificar_fala_do_turno", verificar)
    runtime = composicao_turno.ComposicaoTurnoRuntime(servicos={})

    assert runtime.atualizar(
        "resposta_planejada", comandos=(1,), erros=("erro",), fala="pronto",
    ) == {
        "fase": "resposta_planejada",
        "comandos": (1,),
        "erros": ("erro",),
        "fala": "pronto",
    }
    assert runtime.verificar_fala("pronto", origem="ia_final") == {
        "fala": "pronto",
        "origem": "ia_final",
    }


@pytest.fixture(scope="module")
def resultados_composicao_principal() -> dict:
    # A composição instala print/configuração globais durante o bootstrap.
    # O subprocesso mantém esses efeitos fora dos outros módulos de teste.
    codigo = textwrap.dedent('''
        import json
        import os
        import sys
        from types import SimpleNamespace
        from mente_laylay.integracao import instancia_unica
        # A sonda importa a composição, sem iniciar main/entrada desktop.
        # Usa a trava real com identidade própria para não disputar a sessão
        # da Laylay aberta pelo usuário nem depender de seu encerramento.
        adquirir_real = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda identificador, **kwargs: adquirir_real(
            str(identificador) + ".sonda-composicao-" + str(os.getpid()), **kwargs,
        )
        import laylay as root
        from mente_laylay.cognicao.contratos_turno import (
            ContratoPropostaPrincipal, normalizar_resposta_preparada,
        )
        from mente_laylay.integracao.registro_conversa_llm import (
            RegistroModeloLLM, ResultadoModelo,
        )
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
        from mente_laylay.cognicao.plano_turno import planejar_turno
        from mente_laylay.cognicao.retrato_turno import construir_retrato_turno

        resultados = {"trocas": {}, "inicio": {}, "receipts": {}, "extracoes": {}, "vinculos": {}, "candidatos": {}}
        estado = root._estado_compartilhado_runtime
        root._composicao_turno_runtime._servicos["_coleta_entradas_neurais"] = None
        callback = root._resposta_ia_runtime._contexto()["validar_comandos_planejados"]
        for texto, intent in [
            ("cria a playlist foco", "PLAYLIST_CREATE"),
            ("liga a lâmpada", "IOT_CONTROL"),
            ("abre o Opera", "APP_OPEN"),
        ]:
            turno = classificar_modalidade_turno(texto)
            retrato, _ = construir_retrato_turno(
                texto, turno=turno, mente={}, contexto_perceptivo={},
            )
            turno["retrato_id"] = retrato["id"]
            plano = planejar_turno(texto, turno=turno, mente={})
            estado.mental.update(
                turno_atual=turno, plano_turno_atual=plano, retrato_turno_atual=retrato,
            )
            autorizado = {"intent": intent, "params": {}}
            controle = callback([autorizado])
            outro_texto = "apaga o arquivo foco"
            outro_turno = classificar_modalidade_turno(outro_texto)
            outro_turno["id"] = int(turno["id"]) + 1
            outro_retrato, _ = construir_retrato_turno(
                outro_texto, turno=outro_turno, mente={}, contexto_perceptivo={},
            )
            estado.mental["retrato_turno_atual"] = outro_retrato
            proposta = {"intent": "DELETE_ITEM", "params": {}}
            resultados["trocas"][texto] = {
                "controle": controle,
                "ids": [retrato["id"], outro_retrato["id"]],
                "permitidos_estrangeiros": outro_retrato["intents_permitidos"],
                "resultado": callback([proposta]),
            }

        for texto, intent in [
            ("Cria a playlist foco", "PLAYLIST_CREATE"),
            ("Liga a lâmpada do quarto", "IOT_CONTROL"),
            ("Abre o Opera... não, abre a Calculadora.", "APP_OPEN"),
            ("Pausa a música... esquece, continua tocando.", "MEDIA_CONTROL"),
            ("Toca uma música do C418", "MUSIC_SEARCH"),
        ]:
            turno = root._iniciar_planejamento_turno(texto, origem="teste_composicao")
            plano = estado.mental["plano_turno_atual"]
            retrato = estado.mental["retrato_turno_atual"]
            comando = {"intent": intent, "params": {}}
            resultados["inicio"][texto] = {
                "ids": [turno["id"], plano["id"], retrato["id"]],
                "autoriza_turno": turno["autoriza_execucao"],
                "resultado": callback([comando]),
            }

        contexto_ia = root._resposta_ia_runtime._contexto()
        for texto, intent, alegacao in [
            ("apaga o arquivo foco", "DELETE_ITEM", "Apaguei o arquivo foco."),
            ("liga a lâmpada", "IOT_CONTROL", "Liguei a lâmpada."),
            ("cria a playlist foco", "PLAYLIST_CREATE", "Criei a playlist foco."),
        ]:
            resultados["receipts"][texto] = {}
            for estrangeiro in (False, True):
                turno = root._iniciar_planejamento_turno(texto, origem="teste_composicao")
                plano = dict(estado.mental["plano_turno_atual"])
                recibo = {
                    "intent": intent, "alvo": "foco", "status": "sucesso",
                    "confirmado": True, "executou": True,
                }
                plano["comandos"] = [recibo]
                if estrangeiro:
                    outro_id = int(turno["id"]) + 1
                    plano["id"] = outro_id
                    plano["retrato_id"] = outro_id
                    plano["decisao_turno"] = dict(plano["decisao_turno"], turno_id=outro_id)
                    plano["contrato_fala"] = dict(plano["contrato_fala"], turno_id=outro_id)
                estado.mental["plano_turno_atual"] = plano
                validacao = callback([{"intent": intent, "params": {}}])
                # Nenhum efeito novo: o controle só conserva uma evidência
                # sintética já publicada; no negativo, o filtro recusa a proposta.
                comandos = []
                novo = contexto_ia["atualizar_plano_turno"](
                    "resposta_planejada", comandos=comandos, fala=alegacao,
                )
                executores = []
                contexto_dispatch = contexto_ia["contexto_dispatch_runtime"].montar()
                contexto_dispatch["salvar_memoria"] = lambda: None
                contexto_dispatch["executar_intencao"] = lambda *a, **k: executores.append(a)
                dispatch = contexto_ia["executar_comandos_json"](
                    contexto_dispatch, texto, comandos, alegacao, "comando",
                    False, False, False,
                )
                contexto_final = contexto_ia["contexto_finalizacao_runtime"].montar()
                falas = []
                contexto_final["messages"] = [{"role": "user", "content": texto}]
                contexto_final["falar_com_lipsync"] = lambda fala, *a: falas.append(fala) or True
                contexto_final["memoria_inteligente"] = None
                contexto_final["salvar_memoria"] = lambda: None
                final = contexto_ia["finalizar_execucao"](
                    contexto_final, comandos, dispatch["erros"], alegacao,
                    dispatch["fala_ja_emitida"], dispatch["fala_emitida_por_acao"],
                    dispatch["fala_salva_no_inicio"],
                )
                resultados["receipts"][texto][str(estrangeiro)] = {
                    "turno_id": turno["id"], "plano_id": plano["id"],
                    "validacao": validacao, "publicacao": novo,
                    "executores": executores, "falas": falas, "final": final,
                    "verificacao": estado.mental["plano_turno_atual"].get("ultima_verificacao"),
                }

        # O protocolo moderno recebe a emissão; a rota legada permite reproduzir
        # o RED anterior no mesmo callback instalado, sem outro filtro.
        def validar_principal(comandos, principal):
            moderno = getattr(callback, "validar_proposta", None)
            return moderno(comandos, principal) if callable(moderno) else callback(comandos)
        for texto, intent in [
            ("cria a playlist foco", "PLAYLIST_CREATE"),
            ("liga a lâmpada", "IOT_CONTROL"),
            ("abre a Calculadora", "APP_OPEN"),
        ]:
            turno = root._iniciar_planejamento_turno(texto, origem="teste_vinculo")
            comando = {"intent": intent, "params": {}}
            principal = ContratoPropostaPrincipal(
                turno_id=turno["id"], texto_usuario=texto,
                resposta_bruta=json.dumps({"fala":"Vou verificar.", "comandos":[comando]}),
            )
            controle = validar_principal([comando], principal)
            novo_turno = root._iniciar_planejamento_turno(texto, origem="teste_vinculo")
            mesma_fala = validar_principal([comando], principal)
            root._iniciar_planejamento_turno("apaga o arquivo foco", origem="teste_vinculo")
            outra_operacao = validar_principal([comando], principal)
            resultados["vinculos"][texto] = {
                "ids": [turno["id"], novo_turno["id"]], "controle": controle,
                "mesma_fala": mesma_fala, "outra_operacao": outra_operacao,
            }

        # O callback instalado usa o preparador, normalizador e higiene reais.
        # Somente o transporte do modelo e as portas persistentes são isolados.
        pedidos_reparo = []
        reparada = '{"fala":"Entendi seu pedido.","comandos":[]}'
        def reparar(pedido):
            pedidos_reparo.append(pedido.tipo_chamada)
            return ResultadoModelo(reparada, True, rota="sonda_extracao")
        root._registro_modelo_llm_runtime = RegistroModeloLLM.criar(SimpleNamespace(
            executar=reparar, diagnostico=lambda: {"disponivel": True},
        ))
        root._registrar_autocorrecao_virtual = lambda *a, **k: None
        root.MEMORIA_SQLITE = None
        preparar = contexto_ia["preparar_resposta"]
        for nome, bruto in [
            ("json_explicito", '{"fala":"Vou abrir.","comandos":[{"acao":"open_app","alvo":"Calculadora"}]}'),
            ("apenas_fala", '{"fala":"Eu poderia usar open_app: Calculadora","comandos":[]}'),
            ("explicacao_solta", "Eu poderia usar open_app: Calculadora"),
            ("json_truncado", '{"fala":"Vou abrir.","comandos":[{"acao":"open_app","alvo":"Calculadora"}]'),
        ]:
            texto = "abra a Calculadora"
            turno = root._iniciar_planejamento_turno(texto, origem="teste_extracao")
            antes_pedidos = len(pedidos_reparo)
            preparada = preparar(texto, bruto)
            proposta = ContratoPropostaPrincipal(
                turno_id=turno["id"], texto_usuario=texto, resposta_bruta=bruto,
            )
            contrato = normalizar_resposta_preparada(preparada, proposta_principal=proposta)
            extracao = contrato.extracao_original
            resultados["extracoes"][nome] = {
                "metodo": extracao.metodo,
                "quantidade": extracao.quantidade_comandos,
                "explicita": extracao.proposta_operacional_explicita,
                "vinculada": extracao.resposta_bruta == proposta.resposta_bruta,
                "autoriza": extracao.autoriza_execucao,
                "substituida": contrato.resposta_bruta != bruto,
                "pedidos_reparo": pedidos_reparo[antes_pedidos:],
                "originais": [item.como_dict() for item in extracao.comandos_originais] if extracao.comandos_originais is not None else None,
                "normalizados": [item.como_dict() if item is not None else None for item in extracao.comandos_normalizados] if extracao.comandos_normalizados is not None else None,
                "preservados": extracao.candidatos_preservados,
                "normalizacao_completa": extracao.normalizacao_completa,
            }
        casos_candidatos = [
            ("playlist_legada", "cria a playlist foco", {"acao":"criar_playlist", "alvo":"foco"}),
            ("app_legado", "abre a Calculadora", {"acao":"open_app", "alvo":"Calculadora"}),
            ("iot_legado", "liga a lâmpada", {"acao":"ligar", "alvo":"lampada_quarto"}),
            ("playlist_canonica", "cria a playlist foco", {"intent":"PLAYLIST_CREATE", "params":{"nome_playlist":"foco", "target":"pc_b", "extra":[1]}}),
            ("app_canonico", "abre a Calculadora", {"intent":"APP_OPEN", "params":{"nome_app":"Calculadora", "target":"pc_b", "extra":{"v":2}}}),
            ("iot_canonico", "liga a lâmpada", {"intent":"IOT_CONTROL", "params":{"acao":"ligar", "alvo":"lampada_quarto", "target":"pc_b"}}),
            ("campos_concorrentes", "abre a Calculadora", {"intent":"DELETE_ITEM", "acao":"open_app", "alvo":"Calculadora"}),
        ]
        for nome, texto, comando in casos_candidatos:
            turno = root._iniciar_planejamento_turno(texto, origem="teste_snapshot_original")
            bruto = json.dumps({"fala":"Entendi seu pedido.", "comandos":[comando]})
            preparada = preparar(texto, bruto)
            principal = ContratoPropostaPrincipal(
                turno_id=turno["id"], texto_usuario=texto, resposta_bruta=bruto,
            )
            contrato = normalizar_resposta_preparada(preparada, proposta_principal=principal)
            extracao = contrato.extracao_original
            originais = getattr(extracao, "comandos_originais", None)
            normalizados = getattr(extracao, "comandos_normalizados", None)
            resultados["candidatos"][nome] = {
                "comando": comando,
                "originais": [item.como_dict() for item in originais] if originais is not None else None,
                "normalizados": [item.como_dict() if item is not None else None for item in normalizados] if normalizados is not None else None,
                "preservados": getattr(extracao, "candidatos_preservados", False),
                "normalizacao_completa": getattr(extracao, "normalizacao_completa", False),
                "explicita": extracao.proposta_operacional_explicita,
                "vinculada": extracao.resposta_bruta == principal.resposta_bruta,
                "autoriza": extracao.autoriza_execucao,
            }
        from dataclasses import asdict
        resultados["violacoes"] = {}
        for nome, texto, comando in [
            ("playlist", "cria a playlist foco", {"intent":"DELETE_ITEM", "params":{}}),
            ("iot", "liga a lâmpada", {"intent":"DELETE_ITEM", "params":{}}),
            ("veto", "como apagar o arquivo foco?", {"intent":"DELETE_ITEM", "params":{}}),
            ("alias", "cria a playlist foco", {"acao":"criar_playlist", "alvo":"foco"}),
            ("params", "cria a playlist foco", {"intent":"PLAYLIST_CREATE", "params":{"nome_playlist":""}}),
            ("app_sem_cobertura", "abre a Calculadora", {"intent":"DELETE_ITEM", "params":{}}),
        ]:
            turno = root._iniciar_planejamento_turno(texto, origem="teste_violacao")
            bruto = json.dumps({"fala":"Entendi seu pedido.", "comandos":[comando]})
            principal = ContratoPropostaPrincipal(turno_id=turno["id"], texto_usuario=texto, resposta_bruta=bruto)
            contrato = normalizar_resposta_preparada(preparar(texto, bruto), proposta_principal=principal)
            # Lista final vazia representa reparo/remoção. A fonte continua a
            # vir do preparador real instalado, sobre o início real do turno.
            resultado = callback.validar_proposta_original([], principal, contrato.extracao_original)
            provas = resultado.pop("violacoes_proposta_original")
            resultados["violacoes"][nome] = {
                "resultado": resultado, "provas": [asdict(item) for item in provas],
                "normalizacao_completa": contrato.extracao_original.normalizacao_completa,
                "decisao": estado.mental["plano_turno_atual"]["decisao_turno"],
            }
        sys.__stdout__.write("COMPOSICAO_CONTRATOS " + json.dumps(resultados, ensure_ascii=False) + "\\n")
    ''')
    ambiente = dict(os.environ, PYTHONIOENCODING="utf-8")
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=ambiente, capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert processo.returncode == 0, processo.stderr[-2000:]
    linhas = [
        linha.removeprefix("COMPOSICAO_CONTRATOS ")
        for linha in processo.stdout.splitlines()
        if linha.startswith("COMPOSICAO_CONTRATOS ")
    ]
    assert len(linhas) == 1, "a composição real precisa publicar seu resultado verificável"
    return json.loads(linhas[0])


@pytest.mark.parametrize("nome,intent", [
    ("playlist_legada", "PLAYLIST_CREATE"), ("app_legado", "APP_OPEN"), ("iot_legado", "IOT_CONTROL"),
    ("playlist_canonica", "PLAYLIST_CREATE"), ("app_canonico", "APP_OPEN"), ("iot_canonico", "IOT_CONTROL"),
    ("campos_concorrentes", None),
])
def test_preparador_instalado_preserva_candidatos_originais_e_visao_tipados(
    resultados_composicao_principal: dict, nome: str, intent: str | None,
) -> None:
    dados = resultados_composicao_principal["candidatos"][nome]
    assert dados["originais"] == [dados["comando"]], "a primeira prova é a preservação dos parâmetros originais"
    assert dados["preservados"] is True
    assert dados["vinculada"] is True
    assert dados["explicita"] is True
    assert dados["autoriza"] is False
    if intent is None:
        assert dados["normalizados"] == [None]
        assert dados["normalizacao_completa"] is False
    else:
        assert dados["normalizados"][0]["intent"] == intent
        assert dados["normalizacao_completa"] is True
        if "params" in dados["comando"]:
            assert dados["normalizados"] == [dados["comando"]]


@pytest.mark.parametrize("nome,quantidade,explicita", [
    ("json_explicito", 1, True), ("apenas_fala", 0, False),
    ("explicacao_solta", 1, False), ("json_truncado", 1, False),
])
def test_transporte_instalado_conserva_snapshots_originais_inclusive_apos_reparo(
    resultados_composicao_principal: dict, nome: str, quantidade: int, explicita: bool,
) -> None:
    dados = resultados_composicao_principal["extracoes"][nome]
    assert dados["preservados"] is True
    assert len(dados["originais"]) == quantidade
    assert dados["vinculada"] is True
    assert dados["explicita"] is explicita
    assert dados["autoriza"] is False
    assert dados["normalizacao_completa"] is bool(quantidade)
    if quantidade:
        assert dados["originais"][0]["alvo"] == "Calculadora"
        assert dados["normalizados"][0]["intent"] == "APP_OPEN"
        assert dados["normalizados"][0]["params"]["nome_app"] == "Calculadora"
    if nome == "json_truncado":
        assert dados["substituida"] is True


@pytest.mark.parametrize(("texto", "intent"), [
    ("cria a playlist foco", "PLAYLIST_CREATE"),
    ("liga a lâmpada", "IOT_CONTROL"),
    ("abre o Opera", "APP_OPEN"),
])
def test_callback_da_composicao_recusa_retrato_de_outro_turno(
    resultados_composicao_principal: dict, texto: str, intent: str,
) -> None:
    dados = resultados_composicao_principal["trocas"][texto]
    # A composição real aceita o pedido atual antes da troca controlada.
    autorizado = {"intent": intent, "params": {}}
    controle = dados["controle"]
    assert controle["autoriza_execucao"] is True
    assert controle["comandos"] == [autorizado]
    assert dados["ids"][0] != dados["ids"][1]
    assert "DELETE_ITEM" in dados["permitidos_estrangeiros"]
    resultado = dados["resultado"]
    # Rejeitar a autoridade divergente vem antes de qualquer executor/fala.
    assert resultado["autoriza_execucao"] is False
    assert resultado["comandos"] == []
    assert [item["intent"] for item in resultado["rejeitados"]] == ["DELETE_ITEM"]


@pytest.mark.parametrize(("texto", "intent"), [
    ("Cria a playlist foco", "PLAYLIST_CREATE"),
    ("Liga a lâmpada do quarto", "IOT_CONTROL"),
    ("Abre o Opera... não, abre a Calculadora.", "APP_OPEN"),
    ("Pausa a música... esquece, continua tocando.", "MEDIA_CONTROL"),
    ("Toca uma música do C418", "MUSIC_SEARCH"),
])
def test_filtro_da_composicao_aceita_snapshot_publicado_pelo_inicio_real(
    resultados_composicao_principal: dict, texto: str, intent: str,
) -> None:
    dados = resultados_composicao_principal["inicio"][texto]
    assert len(set(dados["ids"])) == 1
    assert dados["autoriza_turno"] is True
    resultado = dados["resultado"]
    assert resultado["autoriza_execucao"] is True, resultado["rejeitados"]
    assert resultado["comandos"] == [{"intent": intent, "params": {}}]


@pytest.mark.parametrize(("texto", "alegacao"), [
    ("apaga o arquivo foco", "Apaguei o arquivo foco."),
    ("liga a lâmpada", "Liguei a lâmpada."),
    ("cria a playlist foco", "Criei a playlist foco."),
])
def test_composicao_nao_atualiza_nem_consume_receipt_de_plano_estrangeiro(
    resultados_composicao_principal: dict, texto: str, alegacao: str,
) -> None:
    dados = resultados_composicao_principal["receipts"][texto]["True"]
    assert dados["turno_id"] != dados["plano_id"]
    assert dados["validacao"]["autoriza_execucao"] is False
    assert dados["validacao"]["comandos"] == []
    # Primeira fronteira: não publicar evidência estrangeira como resultado
    # desta resposta, mesmo quando a lista nova está vazia.
    assert not any(
        comando.get("confirmado") is True
        for comando in dados["publicacao"].get("comandos") or []
    ), dados["publicacao"]
    assert dados["executores"] == []
    assert dados["final"]["fala"] != alegacao
    assert dados["falas"] == [dados["final"]["fala"]]
    assert "não" in dados["final"]["fala"].casefold()


@pytest.mark.parametrize(("texto", "alegacao"), [
    ("apaga o arquivo foco", "Apaguei o arquivo foco."),
    ("liga a lâmpada", "Liguei a lâmpada."),
    ("cria a playlist foco", "Criei a playlist foco."),
])
def test_composicao_preserva_receipt_do_mesmo_plano_na_atualizacao_vazia(
    resultados_composicao_principal: dict, texto: str, alegacao: str,
) -> None:
    dados = resultados_composicao_principal["receipts"][texto]["False"]
    assert dados["turno_id"] == dados["plano_id"]
    assert dados["validacao"]["autoriza_execucao"] is True
    assert dados["publicacao"]["comandos"][0]["confirmado"] is True
    assert dados["publicacao"]["comandos"][0]["executou"] is True
    assert dados["executores"] == []
    assert dados["final"]["fala"] == alegacao
    assert dados["falas"] == [dados["final"]["fala"]]


@pytest.mark.parametrize(("texto", "alegacao"), [
    ("apaga o arquivo foco", "Apaguei o arquivo foco."),
    ("liga a lâmpada", "Liguei a lâmpada."),
    ("cria a playlist foco", "Criei a playlist foco."),
])
def test_finalizador_real_recusa_fala_sustentada_por_receipt_estrangeiro(
    resultados_composicao_principal: dict, texto: str, alegacao: str,
) -> None:
    dados = resultados_composicao_principal["receipts"][texto]["True"]
    assert dados["validacao"]["comandos"] == []
    assert dados["executores"] == []
    assert dados["final"]["fala"] != alegacao
    assert dados["falas"] == [dados["final"]["fala"]]
    assert "não" in dados["final"]["fala"].casefold()


@pytest.mark.parametrize(("nome", "metodo", "quantidade", "explicita"), [
    ("json_explicito", "json_objeto", 1, True),
    ("apenas_fala", "json_objeto", 0, False),
    ("explicacao_solta", "recuperacao_padrao_textual", 1, False),
    ("json_truncado", "recuperacao_campo_comandos", 1, False),
])
def test_preparador_instalado_preserva_procedencia_original_apos_reparo(
    resultados_composicao_principal: dict, nome: str, metodo: str,
    quantidade: int, explicita: bool,
) -> None:
    dados = resultados_composicao_principal["extracoes"][nome]
    assert dados["metodo"] == metodo
    assert dados["quantidade"] == quantidade
    assert dados["explicita"] is explicita
    assert dados["vinculada"] is True
    assert dados["autoriza"] is False
    if nome in {"explicacao_solta", "json_truncado"}:
        assert dados["substituida"] is True
        assert dados["pedidos_reparo"]


@pytest.mark.parametrize("texto", ["cria a playlist foco", "liga a lâmpada", "abre a Calculadora"])
def test_callback_instalado_recusa_emissao_antiga_apos_troca_coerente(
    resultados_composicao_principal: dict, texto: str,
) -> None:
    dados = resultados_composicao_principal["vinculos"][texto]
    assert dados["controle"]["comandos"]
    assert dados["ids"][0] != dados["ids"][1]
    assert dados["mesma_fala"]["comandos"] == []
    assert dados["mesma_fala"]["proposta_vinculada"] is False
    assert "proposta principal" in dados["mesma_fala"]["rejeitados"][0]["motivo"]


@pytest.mark.parametrize("texto", ["cria a playlist foco", "liga a lâmpada", "abre a Calculadora"])
def test_callback_instalado_nao_atribui_incompatibilidade_usando_operacao_de_outro_turno(
    resultados_composicao_principal: dict, texto: str,
) -> None:
    dados = resultados_composicao_principal["vinculos"][texto]["outra_operacao"]
    assert dados.get("proposta_vinculada") is False
    assert "intenção incompatível" not in dados["rejeitados"][0]["motivo"]


@pytest.mark.parametrize("nome,quantidade", [
    ("playlist", 1), ("iot", 1), ("veto", 1), ("alias", 0),
    ("params", 0), ("app_sem_cobertura", 0),
])
def test_composicao_instalada_demonstrar_violacao_original_exige_contrato_suficiente(
    resultados_composicao_principal: dict, nome: str, quantidade: int,
) -> None:
    dados = resultados_composicao_principal["violacoes"][nome]
    assert dados["normalizacao_completa"] is True
    assert dados["resultado"]["proposta_vinculada"] is True
    assert dados["resultado"]["comandos"] == [] and dados["resultado"]["rejeitados"] == []
    assert len(dados["provas"]) == quantidade, dados["decisao"]
    for prova in dados["provas"]:
        assert prova["origem"] == "contrato_proposta_principal"
        assert prova["owner"] == "validador_comandos_turno"
        assert prova["autoriza_execucao"] is False and prova["comprova_efeito_externo"] is False
