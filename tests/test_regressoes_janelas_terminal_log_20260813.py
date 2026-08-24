from __future__ import annotations

import time
from copy import deepcopy

import pytest

from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.dispatcher_comandos_json import (
    adaptar_acao_json_para_intencao,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_fechar_alvo,
    extrair_intencao_abrir_app,
)
from mente_laylay.autonomia.roteador_intencao import (
    executar_intencao as executar_intencao_canonica,
)
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.continuidade_contexto import (
    registrar_estrutura_arquivo_recente,
)
from mente_laylay.memoria_mental.contexto_imediato import (
    referencia_contextual_imediata,
    resolver_comando_acao_geral_contextual,
)


def _normalizar(texto: str) -> str:
    return str(texto or "").casefold().strip().rstrip(".")


def _detector_com_estado(estado: dict):
    apps = {
        "bloco de notas": "notepad.exe",
        "vs code": "code.exe",
        "opera": "opera.exe",
    }

    def extrair_abertura(texto: str):
        return extrair_intencao_abrir_app(
            texto,
            normalizar_texto=_normalizar,
            limpar_destino=lambda valor: str(valor or "").strip(),
            apps_map=apps,
            sites_diretos={},
        )

    contexto_detector = {
        "normalizar_texto": _normalizar,
        # O mesmo objeto é atualizado após cada execução. Isso reproduz a
        # composição real: o retrato do turno fica congelado, mas o resultado
        # confirmado da etapa anterior já está na mente compartilhada.
        "mente_integrada_estado": estado,
        "texto_depende_de_contexto": lambda texto: any(
            pronome in _normalizar(texto).split()
            for pronome in ("ele", "ela", "isso")
        ),
        "extrair_intencao_abrir_app": extrair_abertura,
        "apps_map": apps,
        "sites_diretos": {},
    }
    return (
        lambda texto: detectar_intencao_deterministica_mente(
            texto, contexto_detector,
        )
    ), apps


def _registrar_contrato_na_mente(
    estado: dict,
    contratos: list,
    contrato,
    texto: str = "",
    executou: bool | None = None,
    **kwargs,
) -> None:
    contratos.append(contrato)
    novo = registrar_resultado_execucao(
        estado,
        contrato,
        texto,
        executou,
        origem=str(kwargs.get("origem") or "executor"),
        status=str(kwargs.get("status") or getattr(contrato, "status", "")),
    )
    estado.clear()
    estado.update(novo)


def test_fecha_programa_chamado_limpa_alvo_e_nao_cai_em_aba() -> None:
    frase = "Fecha um programa chamado Aplicativo Que Não Existe"
    resultado = detectar_fechar_alvo(
        _normalizar(frase),
        params_cb=lambda **params: params,
        sites_diretos=set(),
        apps_map={},
    )
    assert resultado == {
        "intent": "CLOSE_APP",
        "params": {
            "nome_app": "aplicativo que não existe",
            "alvo_tipado": "app",
        },
    }

    contratos = []

    class NavegadorNaoPodeSerTocado:
        @staticmethod
        def fechar_aba(*_args, **_kwargs):
            raise AssertionError("um programa explícito não pode virar aba")

    assert executar_intencao_canonica(
        resultado,
        frase,
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": False,
                # Reproduz o falso candidato que antes desviava o domínio.
                "aba_aberta": True,
                "url": "https://example.invalid/",
            },
            "_registro_navegador_operacoes_runtime": NavegadorNaoPodeSerTocado(),
            "fechar_programa": lambda _nome: (_ for _ in ()).throw(
                AssertionError("não deve encerrar processo ausente")
            ),
            "_registrar_resultado_execucao": (
                lambda contrato, *_args, **_kwargs: contratos.append(contrato)
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    ) is True

    assert len(contratos) == 1
    contrato = contratos[0]
    assert contrato.status == "nao_encontrado"
    assert contrato.executou is False
    assert contrato.confirmado is False
    assert contrato.confirmacao_oferecida == "estado_observado"
    assert "janela" in contrato.evidencia_confirmacao.casefold()

    # A evidência lexical também precisa sobreviver quando o nome existe no
    # mapa ou parece um site; "programa" continua sendo o domínio solicitado.
    assert detectar_fechar_alvo(
        "fecha o aplicativo chamado youtube",
        params_cb=lambda **params: params,
        sites_diretos={"youtube"},
        apps_map={"youtube": "youtube.exe"},
    ) == {
        "intent": "CLOSE_APP",
        "params": {"nome_app": "youtube", "alvo_tipado": "app"},
    }


def test_alias_fecha_openwith_vira_close_app_canonico_e_e_bloqueado() -> None:
    resultado = adaptar_acao_json_para_intencao({
        "acao": "fecha",
        "alvo": "OpenWith.exe",
    })
    assert resultado == {
        "intent": "CLOSE_APP",
        "params": {
            "nome_app": "OpenWith.exe",
            "target": "pc_a",
            "referencia_nao_tipificada": True,
        },
    }

    contratos = []
    assert executar_intencao_canonica(
        resultado,
        "Fecha ele.",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_resolver_alvo_ambiente": lambda _nome: (_ for _ in ()).throw(
                AssertionError("processo auxiliar nem deve chegar à percepção")
            ),
            "fechar_programa": lambda _nome: (_ for _ in ()).throw(
                AssertionError("OpenWith.exe não pode ser encerrado por palpite")
            ),
            "_registrar_resultado_execucao": (
                lambda contrato, *_args, **_kwargs: contratos.append(contrato)
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    ) is True

    assert len(contratos) == 1
    assert contratos[0].status == "referencia_insegura"
    assert contratos[0].executou is False
    assert contratos[0].confirmado is False


def test_turno_120_fecha_arquivo_tipado_mesmo_sem_confirmar_foco() -> None:
    caminho = r"C:\Users\pbarr\Downloads\teste natural.txt"
    estado = estado_mental_inicial()
    estado["ultima_estrutura_arquivo_params"] = {
        "tipo": "arquivo",
        "caminho": caminho,
        "arquivo_nome": "teste natural.txt",
    }
    estado = registrar_resultado_execucao(
        estado,
        {
            "intent": "FILE_OPEN_RESULT",
            "params": {
                "caminho": caminho,
                "alvo": "teste natural.txt",
                "modo": "focus",
            },
            "status": "arquivo_aberto_sem_foco",
            "executou": True,
            "confirmado": False,
        },
        "Abre ele e traz para frente.",
    )
    estado["ts"] = time.time()

    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado,
        foco_vivo={"exe": "OpenWith.exe", "title": ""},
        texto_atual="Fecha ele.",
        normalizar_texto=_normalizar,
    )
    assert referencia["tipo"] == "arquivo"
    assert referencia["alvo"] == caminho
    assert referencia["origem_continuidade"] == (
        "arquivo_aberto_foco_nao_confirmado"
    )

    comando = resolver_comando_acao_geral_contextual(
        "fecha ele", referencia,
    )
    assert comando == {
        "intent": "CLOSE_APP",
        "params": {
            "nome_app": "teste natural.txt",
            "janela_titulo": "teste natural.txt",
            "referencia_arquivo": True,
        },
    }

    titulos = []
    contratos = []
    assert executar_intencao_canonica(
        comando,
        "Fecha ele.",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "fechar_janela_por_titulo": lambda titulo: (
                titulos.append(titulo) or False
            ),
            "fechar_programa": lambda _nome: (_ for _ in ()).throw(
                AssertionError("fechamento tipado de arquivo não encerra processo")
            ),
            "_registrar_resultado_execucao": (
                lambda contrato, *_args, **_kwargs: contratos.append(contrato)
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    ) is True
    assert titulos == ["teste natural.txt"]
    assert contratos[0].status == "falha_execucao"
    assert contratos[0].executou is False
    assert contratos[0].confirmado is False


def test_retrato_nao_promove_openwith_sem_titulo_a_referente() -> None:
    estado = registrar_estrutura_arquivo_recente(
        {},
        {
            "tipo": "arquivo",
            "caminho": r"C:\Users\pbarr\Downloads\teste natural.txt",
            "arquivo_nome": "teste natural.txt",
        },
    )
    retrato, _estado = construir_retrato_turno(
        "Fecha ele.",
        turno={"modalidade": "comando"},
        mente=estado,
        contexto_perceptivo={"exe": "OpenWith.exe", "title": ""},
        agora=time.time(),
    )
    assert "OpenWith.exe" not in repr(retrato)
    assert any(
        candidato.get("tipo") == "arquivo"
        and candidato.get("nome") == "teste natural.txt"
        for candidato in retrato["referencia_candidatos"]
    )


@pytest.mark.parametrize(
    ("frase", "app", "lado"),
    (
        ("Abre Bloco de Notas e coloca ele na esquerda", "bloco de notas", "left"),
        ("Abre o VS Code e coloca ele na direita", "vs code", "right"),
    ),
)
def test_composicao_abre_app_e_posiciona_referencia_viva_com_evidencia(
    frase: str,
    app: str,
    lado: str,
) -> None:
    estado = estado_mental_inicial()
    detector, apps = _detector_com_estado(estado)
    executadas = []
    contratos = []
    ambiente = {"aberto": False, "foco": False}

    class ContextoCongelado:
        @staticmethod
        def montar():
            return {
                "turno_atual": classificar_modalidade_turno(frase),
                # Um retrato antigo não pode vencer o resultado real da etapa 1.
                "retrato_turno_atual": {
                    "referencia_resolvida": {
                        "tipo": "janela",
                        "nome": "YouTube - Opera",
                    },
                },
                "mente_integrada_estado": estado,
                "continuidade_geral": {},
            }

    namespace = {
        "_normalizar_texto_com_apelidos": _normalizar,
        "_texto_depende_de_contexto": lambda texto: any(
            pronome in _normalizar(texto).split()
            for pronome in ("ele", "ela", "isso")
        ),
        "_texto_parece_consulta_operacional": lambda _texto: True,
        "detectar_intencao_deterministica": detector,
    }
    runtime = CicloComandosRuntime(
        namespace_getter=lambda: namespace,
        contexto_intencao_runtime=ContextoCongelado(),
        log=lambda *_args: None,
    )

    def executar_etapa(resultado: dict, texto: str) -> bool:
        executadas.append(deepcopy(resultado))

        def registrar(contrato, texto_registro="", executou=None, **kwargs):
            _registrar_contrato_na_mente(
                estado,
                contratos,
                contrato,
                texto_registro,
                executou,
                **kwargs,
            )

        def abrir_programa(_nome: str) -> bool:
            ambiente.update(aberto=True, foco=True)
            return True

        return executar_intencao_canonica(
            resultado,
            texto,
            {
                "_target_from_params": lambda *_args: "pc_a",
                "APPS_MAP": apps,
                "_resolver_alvo_ambiente": lambda _nome: {
                    "programa_aberto": ambiente["aberto"],
                    "programa_em_foco": ambiente["foco"],
                },
                "abrir_programa": abrir_programa,
                "focar_janela_app": lambda _nome: (
                    ambiente.update(foco=True) or True
                ),
                "organizar_janelas_robusto": lambda esquerda, direita: {
                    "ok": True,
                    "executou": True,
                    "confirmado": True,
                    "status": "layout_confirmado",
                    "nome_esquerda": esquerda,
                    "nome_direita": direita,
                },
                "_registrar_resultado_execucao": registrar,
                "falar_com_lipsync": lambda *_args: None,
            },
        )

    runtime.executar_intencao = executar_etapa
    assert runtime.processar_cadeia(frase, "regressao-terminal-log") is True

    assert [item["intent"] for item in executadas] == [
        "APP_OPEN", "ORGANIZAR_DESKTOP",
    ]
    assert executadas[0]["params"]["nome_app"] == app
    params_layout = executadas[1]["params"]
    assert params_layout[lado] == app
    assert params_layout[f"{lado}_original"] == "ele"
    assert params_layout["referencia_contextual"] is True
    assert not params_layout.get("right" if lado == "left" else "left")

    assert contratos[0].status == "app_iniciado_focado"
    assert contratos[0].executou is True
    assert contratos[0].confirmado is True
    assert "janela" in contratos[0].evidencia_confirmacao.casefold()
    assert contratos[1].status == "layout_confirmado"
    assert contratos[1].executou is True
    assert contratos[1].confirmado is True
    assert "geometria" in contratos[1].evidencia_confirmacao.casefold()


@pytest.mark.parametrize(
    ("maximizou", "status", "executou", "confirmado"),
    (
        (False, "maximizacao_nao_confirmada", False, False),
        (True, "janela_maximizada", True, True),
    ),
)
def test_maximiza_opera_exige_geometria_e_nao_confirma_so_foco(
    maximizou: bool,
    status: str,
    executou: bool,
    confirmado: bool,
) -> None:
    estado = estado_mental_inicial()
    detector, _apps = _detector_com_estado(estado)
    resultado = detector("Maximiza o Opera")
    assert resultado == {
        "intent": "MAXIMIZE_WINDOW",
        "params": {"nome_app": "opera"},
    }

    contratos = []
    assert executar_intencao_canonica(
        resultado,
        "Maximiza o Opera",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "APPS_MAP": {"opera": "opera.exe"},
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": True,
                # A regressão é justamente esta: foco verdadeiro não prova
                # que a geometria já está maximizada.
                "programa_em_foco": True,
            },
            "ativar_tela_cheia_robusta": lambda _nome: maximizou,
            "focar_janela_app": lambda _nome: True,
            "_registrar_resultado_execucao": (
                lambda contrato, *_args, **_kwargs: contratos.append(contrato)
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    ) is True

    assert len(contratos) == 1
    contrato = contratos[0]
    assert contrato.status == status
    assert contrato.executou is executou
    assert contrato.confirmado is confirmado
    assert contrato.confirmacao_oferecida == "estado_observado"
    assert "maximiza" in contrato.evidencia_confirmacao.casefold()
