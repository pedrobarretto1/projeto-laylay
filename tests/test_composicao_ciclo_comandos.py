from __future__ import annotations

from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.composicao_ciclo_comandos import (
    ComposicaoCicloComandosRuntime,
)
from mente_laylay.integracao.registro_iot import registrar_iot
from mente_laylay.integracao.registro_arquivos import registrar_arquivos_leitura
from mente_laylay.arquivos.mutacoes import criar_arquivos_mutacao_runtime
from mente_laylay.integracao.registro_mutacoes_arquivos import registrar_arquivos_mutacao
from mente_laylay.integracao.registro_musica import registrar_musica_leitura
from mente_laylay.integracao.registro_operacoes_musicais import (
    registrar_operacoes_musicais,
)
from mente_laylay.integracao.registro_conversa_llm import (
    RegistroModeloLLM,
    ResultadoModelo,
)
from tests.fakes_navegador import NavegadorLeituraFake, NavegadorOperacoesFake
from tests.fakes_visao_jogo import VisaoJogoAnaliseFake, VisaoJogoLeituraFake


class _IoTNulo:
    def detectar(self, _texto, _estado=None): return None
    def executar(self, _resultado, _texto=""): return {"handled": False}
    def retrato_para_mente(self, _texto=""): return {"dispositivos": []}


class _ArquivosLeituraNulo:
    def pesquisar(self, _consulta, **_kwargs): return {"resultados": []}
    def abrir(self, _caminho): return False
    def diagnostico(self): return {"somente_leitura": True}


class _MusicaLeituraNula:
    def listar_usuario(self): return "Sem playlists."
    def consultar_usuario(self, _nome): return {"ok": False, "total": 0}
    def contar_usuario(self, _nome): return 0
    def formatar_prompt(self): return "Nenhuma playlist salva ainda."
    def retrato_usuario(self, _texto=""): return {"playlists": [], "detalhe": {}}
    def indice_usuario(self): return {}
    def listar_laylay(self, _nome=""): return "Sem curadorias."
    def retrato_laylay(self, _texto=""): return {"playlists": [], "detalhe": {}}
    def estado(self): return {"playlist_ativa": ""}
    def diagnostico(self): return {"somente_leitura": True, "expondo_urls": False}


class _MusicaOperacoesNula:
    def apagar_playlist(self, _nome): return False
    def adicionar_faixa(self, *_args): return False
    def mover_faixa(self, _origem, _destino, _musica=""): return {"ok": False}
    def tocar_playlist(self, _nome): return False
    def preparar_shuffle(self, _nome): return {}
    def primeira_url(self, _nome): return ""
    def avancar_proxima(self): return False
    def voltar_anterior(self): return False
    def definir_ultima_playlist(self, _nome): return None
    def definir_ultima_url(self, _url): return None
    def faixa_atual(self): return {}
    def copiar_curadoria(self, _origem, _musica, _destino): return {"ok": False}
    def estado(self): return {"playlist_ativa": ""}
    def diagnostico(self): return {"mutacao_disponivel": True}


class _ModeloNulo:
    def executar(self, _pedido):
        return ResultadoModelo("ok", True)

    def diagnostico(self):
        return {"disponivel": True}


def _com_servicos_tipados(servicos=None):
    resultado = dict(servicos or {})
    resultado["_registro_iot_runtime"] = registrar_iot(_IoTNulo())
    resultado["_registro_arquivos_leitura_runtime"] = registrar_arquivos_leitura(
        _ArquivosLeituraNulo()
    )
    resultado["_registro_arquivos_mutacao_runtime"] = registrar_arquivos_mutacao(
        criar_arquivos_mutacao_runtime()
    )
    resultado["_registro_musica_leitura_runtime"] = registrar_musica_leitura(
        _MusicaLeituraNula()
    )
    resultado["_registro_musica_operacoes_runtime"] = registrar_operacoes_musicais(
        _MusicaOperacoesNula()
    )
    resultado["_registro_navegador_leitura_runtime"] = NavegadorLeituraFake()
    resultado["_registro_navegador_operacoes_runtime"] = NavegadorOperacoesFake()
    resultado["_registro_visao_jogo_leitura_runtime"] = VisaoJogoLeituraFake()
    resultado["_registro_visao_jogo_analise_runtime"] = VisaoJogoAnaliseFake()
    return resultado


class _ContextoFake:
    def __init__(self):
        self.validacoes = 0

    def validar_conexoes(self):
        self.validacoes += 1
        return {"status": "saudavel"}


class _CicloFake:
    def __init__(self):
        self.validacoes = 0
        self.chamadas = []

    def validar_conexoes(self):
        self.validacoes += 1
        return {"status": "saudavel"}

    def executar_intencao(self, resultado, texto):
        self.chamadas.append(("intencao", resultado, texto))
        return True

    def executar_texto(self, texto, origem=""):
        self.chamadas.append(("texto", texto, origem))
        return True

    def processar_cadeia(self, texto, origem=""):
        self.chamadas.append(("cadeia", texto, origem))
        return True

    def processar_deterministico(self, texto, origem="", texto_original=""):
        self.chamadas.append(("deterministico", texto, origem, texto_original))
        return True

    def tentar_intencao_ai_primeiro(self, texto):
        self.chamadas.append(("ia", texto))
        return {"intent": "NONE"}

    def resolver_comando_natural(self, texto, origem=""):
        self.chamadas.append(("natural", texto, origem))
        return {"intent": "APP_OPEN", "params": {"nome_app": "opera"}}, "ia-first-arbitrada"

    def decisao_ja_avaliada(self, texto):
        self.chamadas.append(("decisao", texto))
        return True


def _montar():
    capturado = {}
    contexto = _ContextoFake()
    ciclo = _CicloFake()

    def contexto_factory(**kwargs):
        capturado["contexto"] = kwargs
        return contexto

    def ciclo_factory(**kwargs):
        capturado["ciclo"] = kwargs
        return ciclo

    runtime = ComposicaoCicloComandosRuntime(
        contexto_factory=contexto_factory,
        ciclo_factory=ciclo_factory,
        log=lambda *_: None,
    )
    return runtime, contexto, ciclo, capturado


def test_composicao_exige_conexao_antes_de_executar() -> None:
    runtime, *_ = _montar()
    with pytest.raises(RuntimeError, match="ainda não conectado"):
        runtime.executar_texto("oi")
    with pytest.raises(RuntimeError, match="ainda não conectado"):
        _ = runtime.contexto


@pytest.mark.parametrize(
    ("dependencia", "mensagem"),
    (
        ("_registro_visao_jogo_leitura_runtime", "leitura da visão de jogo"),
        ("_registro_visao_jogo_analise_runtime", "análise da visão de jogo"),
    ),
)
def test_composicao_falha_cedo_sem_porta_visual_obrigatoria(
    dependencia: str, mensagem: str,
) -> None:
    runtime, *_ = _montar()
    servicos = _com_servicos_tipados()
    servicos.pop(dependencia)

    with pytest.raises(RuntimeError, match=mensagem):
        runtime.conectar(servicos=servicos, estado_getter=lambda: {})


def test_composicao_congela_somente_servicos_da_allowlist() -> None:
    runtime, contexto, ciclo, capturado = _montar()
    servicos = _com_servicos_tipados({
        "_target_from_params": object(),
        "_interpretacao_intencao_runtime": object(),
        "detectar_intencao_deterministica": object(),
        "criar_pasta": object(),
        "criar_ou_editar_arquivo": object(),
        "escrever_arquivo_texto_seguro": object(),
        "deletar_item": object(),
        "resolver_caminho": object(),
        "mover_arquivo": object(),
        "SEGREDO_FORA_DO_CONTRATO": "não deve ficar retido",
    })
    criado_contexto, criado_ciclo = runtime.conectar(
        servicos=servicos,
        estado_getter=lambda: {"turno_atual": {}},
    )

    assert criado_contexto is contexto
    assert criado_ciclo is ciclo
    assert "SEGREDO_FORA_DO_CONTRATO" not in runtime.servicos_registrados
    assert set(runtime.servicos_registrados) == {
        "_target_from_params",
        "_interpretacao_intencao_runtime",
        "detectar_intencao_deterministica",
    }
    assert runtime.servicos_tipados_registrados == (
        "arquivos_leitura", "arquivos_mutacao", "iot", "musica_leitura",
        "musica_operacoes", "navegador_leitura", "navegador_operacoes",
        "visao_jogo_leitura", "visao_jogo_analise",
    )
    servicos["_target_from_params"] = "alterado depois"
    snapshot = capturado["contexto"]["namespace_getter"]()
    assert snapshot["_target_from_params"] != "alterado depois"
    assert contexto.validacoes == 1
    assert ciclo.validacoes == 1


def test_composicao_encaminha_api_estavel_ao_ciclo_conectado() -> None:
    runtime, contexto, ciclo, _ = _montar()
    primeiro = runtime.conectar(
        servicos=_com_servicos_tipados(), estado_getter=lambda: {}
    )
    segundo = runtime.conectar(
        servicos={"SEGREDO_FORA_DO_CONTRATO": "outro"},
        estado_getter=lambda: {"mudou": True},
    )

    assert primeiro == segundo == (contexto, ciclo)
    assert runtime.executar_intencao({"intent": "TESTE"}, "faça") is True
    assert runtime.executar_texto("texto", "chat") is True
    assert runtime.processar_cadeia("um e dois", "voz") is True
    assert runtime.processar_deterministico("abre", "teste", "abre isso") is True
    assert runtime.tentar_intencao_ai_primeiro("talvez") == {"intent": "NONE"}
    assert runtime.resolver_comando_natural("traz o opera", "chat") == (
        {"intent": "APP_OPEN", "params": {"nome_app": "opera"}},
        "ia-first-arbitrada",
    )
    assert runtime.decisao_comando_ja_avaliada("traz o opera") is True
    assert [item[0] for item in ciclo.chamadas] == [
        "intencao", "texto", "cadeia", "deterministico", "ia", "natural", "decisao",
    ]


def test_composicao_injeta_compatibilidade_llm_a_partir_do_registro_tipado() -> None:
    runtime, _contexto, _ciclo, capturado = _montar()
    tipados = _com_servicos_tipados()
    registros = SimpleNamespace(
        iot=tipados["_registro_iot_runtime"],
        arquivos_leitura=tipados["_registro_arquivos_leitura_runtime"],
        arquivos_mutacao=tipados["_registro_arquivos_mutacao_runtime"],
        musica_leitura=tipados["_registro_musica_leitura_runtime"],
        musica_operacoes=tipados["_registro_musica_operacoes_runtime"],
        navegador_leitura=tipados["_registro_navegador_leitura_runtime"],
        navegador_operacoes=tipados["_registro_navegador_operacoes_runtime"],
        visao_jogo_leitura=tipados["_registro_visao_jogo_leitura_runtime"],
        visao_jogo_analise=tipados["_registro_visao_jogo_analise_runtime"],
        modelo_llm=RegistroModeloLLM.criar(_ModeloNulo()),
    )

    runtime.conectar(
        servicos={},
        estado_getter=lambda: {},
        registros_principais=registros,
    )

    contexto = capturado["contexto"]["namespace_getter"]()
    assert contexto["enviar_mensagem"]([{"role": "user", "content": "oi"}]) == "ok"
    assert "modelo_llm" in runtime.servicos_tipados_registrados


def test_composicao_falha_cedo_sem_registro_de_arquivos() -> None:
    runtime, *_ = _montar()
    with pytest.raises(RuntimeError, match="leitura de arquivos"):
        runtime.conectar(
            servicos={"_registro_iot_runtime": registrar_iot(_IoTNulo())},
            estado_getter=lambda: {},
        )


def test_composicao_rejeita_servico_de_arquivos_invalido() -> None:
    runtime, *_ = _montar()
    servicos = {
        "_registro_iot_runtime": registrar_iot(_IoTNulo()),
        "_registro_arquivos_leitura_runtime": object(),
    }
    with pytest.raises(RuntimeError, match="serviço de leitura de arquivos inválido"):
        runtime.conectar(servicos=servicos, estado_getter=lambda: {})


def test_composicao_falha_cedo_sem_registro_de_mutacoes_de_arquivos() -> None:
    runtime, *_ = _montar()
    servicos = {
        "_registro_iot_runtime": registrar_iot(_IoTNulo()),
        "_registro_arquivos_leitura_runtime": registrar_arquivos_leitura(
            _ArquivosLeituraNulo()
        ),
    }
    with pytest.raises(RuntimeError, match="mutação de arquivos"):
        runtime.conectar(servicos=servicos, estado_getter=lambda: {})


def test_composicao_rejeita_servico_de_mutacoes_invalido() -> None:
    runtime, *_ = _montar()
    servicos = _com_servicos_tipados()
    servicos["_registro_arquivos_mutacao_runtime"] = object()
    with pytest.raises(RuntimeError, match="serviço de mutação de arquivos inválido"):
        runtime.conectar(servicos=servicos, estado_getter=lambda: {})


def test_composicao_falha_cedo_sem_registro_de_leitura_musical() -> None:
    runtime, *_ = _montar()
    servicos = _com_servicos_tipados()
    servicos.pop("_registro_musica_leitura_runtime")
    with pytest.raises(RuntimeError, match="leitura musical"):
        runtime.conectar(servicos=servicos, estado_getter=lambda: {})


def test_composicao_rejeita_servico_musical_invalido() -> None:
    runtime, *_ = _montar()
    servicos = _com_servicos_tipados()
    servicos["_registro_musica_leitura_runtime"] = object()
    with pytest.raises(RuntimeError, match="serviço de leitura musical inválido"):
        runtime.conectar(servicos=servicos, estado_getter=lambda: {})
