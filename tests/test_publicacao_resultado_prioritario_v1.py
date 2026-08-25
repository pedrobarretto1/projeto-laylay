from __future__ import annotations

# P0_PUBLICACAO_RESULTADO_PRIORITARIO_V1_20260815

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime
from mente_laylay.memoria_mental.resultado_acao import (
    CHAVE_RESULTADO_OPERACIONAL_PUBLICADO,
)


class _EstadoFake:
    def __init__(self) -> None:
        self.mental = {
            "plano_turno_atual": {
                "fase": "executado",
                "comandos": [],
                "erros": [],
                "especialistas": {},
            }
        }

    def atualizar_campos(self, dominio: str, **campos) -> None:
        assert dominio == "mental"
        self.mental.update(campos)


class _MotorFake:
    def __init__(self) -> None:
        self.resultados = []

    def observar_resultado(self, *args, **kwargs) -> None:
        self.resultados.append((args, kwargs))


class _MapaFake:
    def __init__(self) -> None:
        self.resultados = []

    def registrar_resultado(self, *args, **kwargs) -> None:
        self.resultados.append((args, kwargs))


def _atualizar_plano_fake(plano, *, fase, comandos, erros=(), fala=""):
    novo = dict(plano or {})
    novo.update(
        fase=fase,
        comandos=[dict(item) for item in comandos],
        erros=list(erros),
        fala_planejada=fala,
    )
    return novo


def _runtime(base_callback=None):
    estado = _EstadoFake()
    motor = _MotorFake()
    mapa = _MapaFake()
    base = []
    logs = []
    namespace = {
        "_registrar_resultado_execucao_base": (
            base_callback
            or (lambda *args, **kwargs: base.append((args, kwargs)))
        ),
        "_motor_aprendizado_runtime": motor,
        "_mapa_habilidades_runtime": mapa,
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": _atualizar_plano_fake,
        "_concluir_correcao_interpretacao_mente": lambda *_args, **_kwargs: {},
        "print": logs.append,
    }
    runtime = AdaptadoresAplicacaoRuntime(lambda: namespace)
    return runtime, estado, motor, mapa, base, logs


def _executar_com_adaptador(runtime, pedido, texto="pesquisa python"):
    params = dict(pedido.get("params") or {})
    adaptador = AdaptadorResultadoOperacional(
        pedido,
        params,
        texto,
        "pc_a",
        {"_registrar_resultado_execucao": runtime.registrar_resultado_execucao},
    )
    adaptador.marcar_resultado(
        "busca_aberta",
        executou=True,
        confirmado=True,
        detalhe="resultado real observado",
    )
    return adaptador


def test_resultado_detalhado_torna_registro_generico_apenas_fallback():
    runtime, estado, motor, mapa, base, logs = _runtime()
    pedido = {
        "intent": "SEARCH",
        "params": {"query": "python", "engine": "google"},
    }

    adaptador = _executar_com_adaptador(runtime, pedido)

    assert pedido[CHAVE_RESULTADO_OPERACIONAL_PUBLICADO] == adaptador.id_solicitacao
    assert len(estado.mental["plano_turno_atual"]["comandos"]) == 1
    assert len(base) == 1
    assert len(motor.resultados) == 1
    assert len(mapa.resultados) == 1

    # Reproduz exatamente o padrão dos bypasses prioritários:
    # executar_intencao(...) -> executor publica ResultadoAcao ->
    # camada prioritária tenta registrar novamente o dict original.
    runtime.registrar_resultado_execucao(
        pedido,
        "pesquisa python",
        True,
        origem="prioritario_leitura_deterministica",
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["id_solicitacao"] == adaptador.id_solicitacao
    assert comandos[0]["intent"] == "SEARCH"
    assert comandos[0]["status"] == "busca_aberta"
    assert comandos[0]["confirmado"] is True
    assert comandos[0]["detalhe"] == "resultado real observado"

    # A publicação redundante não pode contaminar consumidores laterais.
    assert len(base) == 1
    assert len(motor.resultados) == 1
    assert len(mapa.resultados) == 1
    assert logs == []


def test_fallback_generico_continua_valido_quando_executor_nao_publicou():
    runtime, estado, motor, mapa, base, logs = _runtime()
    pedido = {
        "intent": "SEARCH",
        "params": {"query": "fallback"},
    }

    runtime.registrar_resultado_execucao(
        pedido,
        "pesquisa fallback",
        True,
        origem="prioritario_legado_sem_publicacao",
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["intent"] == "SEARCH"
    assert comandos[0]["executou"] is True
    assert comandos[0]["status"] == ""
    assert len(base) == 1
    assert len(motor.resultados) == 1
    assert len(mapa.resultados) == 1
    assert logs == []


def test_red_fallback_tipado_publica_confirmacao_inferida_no_plano():
    runtime, estado, _motor, _mapa, _base, logs = _runtime()
    pedido = {"intent": "RESUMIR_PAGINA", "params": {}}

    runtime.registrar_resultado_execucao(
        pedido,
        "Resume isso.",
        True,
        origem="prioritario_resumo_pagina",
        status="resumo_concluido",
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["status"] == "resumo_concluido"
    assert comandos[0]["executou"] is True
    assert comandos[0]["confirmado"] is True
    assert comandos[0]["confirmacao_oferecida"] == "retorno_dados"
    assert comandos[0]["evidencia_confirmacao"]
    assert logs == []


def test_guard_fallback_nao_inventa_confirmacao_para_status_desconhecido():
    runtime, estado, _motor, _mapa, _base, logs = _runtime()

    runtime.registrar_resultado_execucao(
        {"intent": "SEARCH", "params": {"query": "python"}},
        "pesquisa python",
        True,
        origem="prioritario_legado_sem_publicacao",
        status="comando_enviado",
    )

    comando = estado.mental["plano_turno_atual"]["comandos"][0]
    assert comando["executou"] is True
    assert comando["confirmado"] is None
    assert logs == []


def test_novo_adaptador_limpa_marcador_transitorio_reutilizado():
    runtime, estado, motor, mapa, base, logs = _runtime()
    pedido = {
        "intent": "SEARCH",
        "params": {"query": "novo turno"},
        CHAVE_RESULTADO_OPERACIONAL_PUBLICADO: "execucao-antiga",
    }

    # Um dict reaproveitado não pode herdar a prova transitória da execução
    # anterior. O adaptador representa uma nova invocação e limpa o marcador.
    AdaptadorResultadoOperacional(
        pedido,
        dict(pedido["params"]),
        "nova pesquisa",
        "pc_a",
        {"_registrar_resultado_execucao": runtime.registrar_resultado_execucao},
    )
    assert CHAVE_RESULTADO_OPERACIONAL_PUBLICADO not in pedido

    runtime.registrar_resultado_execucao(
        pedido,
        "nova pesquisa",
        False,
        origem="prioritario_fallback_nova_invocacao",
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["intent"] == "SEARCH"
    assert comandos[0]["executou"] is False
    assert len(base) == 1
    assert len(motor.resultados) == 1
    assert len(mapa.resultados) == 1
    assert logs == []


def test_publicacoes_detalhadas_repetidas_do_mesmo_adaptador_continuam_permitidas():
    runtime, estado, motor, mapa, base, logs = _runtime()
    pedido = {
        "intent": "SEARCH",
        "id_solicitacao": "exec-search",
        "params": {"query": "python"},
    }
    adaptador = AdaptadorResultadoOperacional(
        pedido,
        dict(pedido["params"]),
        "pesquisa python",
        "pc_a",
        {"_registrar_resultado_execucao": runtime.registrar_resultado_execucao},
    )

    adaptador.marcar_resultado(
        "busca_aberta",
        executou=True,
        confirmado=True,
    )
    adaptador.marcar_resultado(
        "resultado_web_aberto",
        executou=True,
        confirmado=True,
        params_resolvidos={"abrir_resultado": 1},
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["id_solicitacao"] == "exec-search"
    assert comandos[0]["status"] == "resultado_web_aberto"
    assert comandos[0]["params"]["abrir_resultado"] == 1
    # Só o fallback genérico é suprimido; publicações oficiais sucessivas
    # da mesma execução continuam chegando aos observadores.
    assert len(base) == 2
    assert len(motor.resultados) == 2
    assert len(mapa.resultados) == 2
    assert logs == []


def test_red_resultado_prioritario_nasce_vinculado_ao_turno_sem_plano_previo():
    runtime, estado, _motor, _mapa, _base, logs = _runtime()
    estado.mental["plano_turno_atual"] = {}

    runtime.registrar_resultado_execucao(
        {
            "id_solicitacao": "exec-app-novo",
            "intent": "APP_OPEN",
            "status": "nao_encontrado",
            "executou": False,
            "confirmado": False,
            "params": {"nome_app": "calcuradora"},
        },
        "abre a calcuradora",
        False,
        origem="executor",
    )

    plano = estado.mental["plano_turno_atual"]
    assert plano["id"]
    assert plano["texto_usuario"] == "abre a calcuradora"
    assert plano["comandos"][0]["id_solicitacao"] == "exec-app-novo"
    assert logs == []


def test_red_resultado_prioritario_nao_herda_plano_de_outro_turno():
    runtime, estado, _motor, _mapa, _base, logs = _runtime()
    estado.mental["ultima_entrada"] = "fexa a microsoft store"
    estado.mental["plano_turno_atual"] = {
        "id": "turno-antigo",
        "texto_usuario": "comando anterior",
        "fase": "executado",
        "comandos": [{
            "id_solicitacao": "exec-antiga",
            "intent": "SEARCH",
            "status": "busca_aberta",
            "executou": True,
            "confirmado": True,
        }],
        "erros": [],
    }

    runtime.registrar_resultado_execucao(
        {
            "id_solicitacao": "exec-app-nova",
            "intent": "APP_OPEN",
            "status": "nao_encontrado",
            "executou": False,
            "confirmado": False,
            "params": {"nome_app": "microsoft store"},
        },
        "fexa a microsoft store",
        False,
        origem="executor",
    )

    plano = estado.mental["plano_turno_atual"]
    assert plano["id"] != "turno-antigo"
    assert plano["texto_usuario"] == "fexa a microsoft store"
    assert [item["id_solicitacao"] for item in plano["comandos"]] == [
        "exec-app-nova",
    ]
    assert logs == []


def test_red_subetapas_prioritarias_herdam_identidade_da_fala_completa():
    runtime, estado, _motor, _mapa, _base, logs = _runtime()
    fala = (
        "Cria um arquivo chamado caos seguro.txt e escreve primeira linha."
    )
    estado.mental.update(
        ultima_entrada=fala,
        plano_turno_atual={},
    )

    runtime.registrar_resultado_execucao(
        {
            "id_solicitacao": "criar-arquivo",
            "intent": "CREATE_FILE",
            "status": "arquivo_criado",
            "executou": True,
            "confirmado": True,
            "params": {"alvo": "caos seguro.txt"},
        },
        "Cria um arquivo chamado caos seguro.txt",
        True,
        origem="executor",
    )
    runtime.registrar_resultado_execucao(
        {
            "id_solicitacao": "editar-arquivo",
            "intent": "CREATE_FILE",
            "status": "conteudo_atualizado",
            "executou": True,
            "confirmado": True,
            "params": {
                "alvo": "caos seguro.txt",
                "conteudo": "primeira linha",
            },
        },
        "escreve primeira linha",
        True,
        origem="executor",
    )

    plano = estado.mental["plano_turno_atual"]
    assert plano["texto_usuario"] == fala
    assert [item["id_solicitacao"] for item in plano["comandos"]] == [
        "criar-arquivo",
        "editar-arquivo",
    ]
    assert logs == []


def test_red_identidade_e_capturada_antes_de_consumidor_lateral_mutar_estado():
    fala = "Abre o Opera... não, abre a microsoft store."
    estado_holder = {}

    def base_mutante(*_args, **_kwargs):
        estado = estado_holder["estado"]
        estado.mental["ultima_entrada"] = "abre a microsoft store"
        estado.mental["plano_turno_atual"] = {}

    runtime, estado, _motor, _mapa, _base, logs = _runtime(base_mutante)
    estado_holder["estado"] = estado
    estado.mental.update(
        ultima_entrada=fala,
        plano_turno_atual={
            "id": "turno-revisado",
            "texto_usuario": fala,
            "fase": "executado",
            "comandos": [],
            "erros": [],
        },
    )

    runtime.registrar_resultado_execucao(
        {
            "id_solicitacao": "abrir-store-revisado",
            "intent": "APP_OPEN",
            "status": "protocolo_aberto",
            "executou": True,
            "confirmado": None,
            "params": {"nome_app": "microsoft store"},
        },
        "abre a microsoft store",
        True,
        origem="executor",
    )

    plano = estado.mental["plano_turno_atual"]
    assert plano["id"] == "turno-revisado"
    assert plano["texto_usuario"] == fala
    assert plano["comandos"][0]["intent"] == "APP_OPEN"
    assert logs == []


def test_red_plano_identificado_vence_ultima_entrada_operacional_reduzida():
    runtime, estado, _motor, _mapa, _base, logs = _runtime()
    fala = "Abre o Opera... não, abre a microsoft store."
    estado.mental.update(
        ultima_entrada="abre a microsoft store",
        plano_turno_atual={
            "id": "turno-revisado",
            "texto_usuario": fala,
            "fase": "executado",
            "comandos": [],
            "erros": [],
        },
    )

    runtime.registrar_resultado_execucao(
        {
            "id_solicitacao": "abrir-store-revisado",
            "intent": "APP_OPEN",
            "status": "app_focado",
            "executou": True,
            "confirmado": True,
            "params": {"nome_app": "microsoft store"},
        },
        "abre a microsoft store",
        True,
        origem="executor",
    )

    plano = estado.mental["plano_turno_atual"]
    assert plano["id"] == "turno-revisado"
    assert plano["texto_usuario"] == fala
    assert plano["comandos"][0]["intent"] == "APP_OPEN"
    assert logs == []


def test_red_texto_operacional_efetivo_prova_revisao_com_alvo_herdado():
    runtime, estado, _motor, _mapa, _base, logs = _runtime()
    fala = "Fecha a microsoft store... quer dizer, maximiza ela."
    estado.mental.update(
        ultima_entrada="maximiza microsoft store",
        plano_turno_atual={
            "id": "turno-revisado-alvo-herdado",
            "texto_usuario": fala,
            "texto_operacional_efetivo": "maximiza microsoft store",
            "revisao_intra_turno": {
                "detectada": True,
                "resolvida": True,
                "tipo": "substituicao_acao",
            },
            "fase": "executado",
            "comandos": [],
            "erros": [],
        },
    )

    runtime.registrar_resultado_execucao(
        {
            "id_solicitacao": "maximizar-store-revisado",
            "intent": "MAXIMIZE_WINDOW",
            "status": "maximizacao_nao_confirmada",
            "executou": False,
            "confirmado": False,
            "params": {"nome_app": "microsoft store"},
        },
        "maximiza microsoft store",
        False,
        origem="executor",
    )

    plano = estado.mental["plano_turno_atual"]
    assert plano["id"] == "turno-revisado-alvo-herdado"
    assert plano["texto_usuario"] == fala
    assert plano["comandos"][0]["intent"] == "MAXIMIZE_WINDOW"
    assert logs == []
