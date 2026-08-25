from __future__ import annotations

from types import SimpleNamespace

from mente_laylay.autonomia.analise_comandos import (
    processar_comandos_em_cadeia,
    segmentar_comandos_em_cadeia,
)
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.pre_fluxo_contextual import (
    processar_consulta_sistema_local,
)
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_organizacao_desktop,
)
from mente_laylay.especialistas.area_transferencia import AreaTransferenciaRuntime
from mente_laylay.integracao.avaliador_roteiro_teste import avaliar_turno_roteiro
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.memoria_mental.continuidade_semantica import (
    resolver_continuidade_semantica,
)


FALA_227 = (
    "eu quero que você abra a microsoft store, coloque ela na direita, "
    "confira se ficou aberta e só então me diga o resultado"
)


def _area_transferencia() -> AreaTransferenciaRuntime:
    return AreaTransferenciaRuntime(falar=lambda *_: None, log=lambda *_: None)


def test_red_turno227_nao_e_pedido_de_copiar_resultado() -> None:
    assert _area_transferencia().detectar(FALA_227) == ""


def test_guard_pedidos_reais_de_copiar_resultado_continuam_reconhecidos() -> None:
    runtime = _area_transferencia()
    assert runtime.detectar("copia o resultado") == "copiar_resultado"
    assert runtime.detectar("copie esse texto corrigido") == "copiar_resultado"
    assert (
        runtime.detectar("coloque o resultado na área de transferência")
        == "copiar_resultado"
    )


def test_red_turno227_segmenta_tres_etapas_operacionais() -> None:
    assert segmentar_comandos_em_cadeia(FALA_227) == [
        "abra a microsoft store",
        "coloque ela na direita",
        "confira se ficou aberta e só então me diga o resultado",
    ]


def test_guard_segmentador_executa_as_tres_etapas_na_ordem() -> None:
    chamadas: list[tuple[str, str]] = []
    assert processar_comandos_em_cadeia(
        FALA_227,
        "turno-227",
        executar_trecho=lambda trecho, origem: chamadas.append((trecho, origem)) or True,
    ) is True
    assert chamadas == [
        ("abra a microsoft store", "turno-227-1"),
        ("coloque ela na direita", "turno-227-2"),
        (
            "confira se ficou aberta e só então me diga o resultado",
            "turno-227-3",
        ),
    ]


def test_red_confirmacao_contextual_consulta_o_ultimo_app_sem_reabri_lo() -> None:
    falas: list[str] = []
    registros: list[dict] = []
    tratado, rota = processar_consulta_sistema_local(
        {
            "mente_integrada_estado": {"ultimo_app_janela": "Microsoft Store"},
            "_resolver_alvo_ambiente": lambda nome: {
                "programa_aberto": nome == "Microsoft Store",
                "programa_em_foco": True,
            },
            "_emitir_resposta_curta": lambda _texto, fala, **_kwargs: falas.append(fala),
            "_registrar_resultado_execucao": (
                lambda resultado, *_args, **_kwargs: registros.append(dict(resultado))
            ),
        },
        "confira se ficou aberta e só então me diga o resultado",
    )

    assert tratado is True
    assert rota == "consulta_estado_programa"
    assert falas and "aberto" in falas[-1].casefold()
    assert registros[-1]["intent"] == "LIST_WINDOWS"
    assert registros[-1]["status"] == "estado_app_consultado"
    assert registros[-1]["params"]["alvo"] == "Microsoft Store"


def test_guard_confirmacao_contextual_sem_referente_nao_inventa_app() -> None:
    assert processar_consulta_sistema_local(
        {
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": True,
                "programa_em_foco": True,
            },
        },
        "confira se ficou aberta",
    ) == (False, "")


def test_red_contexto_oficial_publica_ultimo_app_vivo_para_etapa_seguinte() -> None:
    mente = {"ultimo_app_janela": "microsoft store"}
    namespace = {
        "_musica_estado_get": lambda _chave: None,
        "_conversa_estado_get": lambda _chave, padrao=None: padrao,
        "_memoria_conversa_get": lambda _chave, padrao=None: padrao,
        "_continuidades_get": lambda _chave: None,
        "playlist_state": {},
        "_musica_estado_set": lambda *_args: None,
        "_continuidades_set": lambda *_args: None,
        "_continuidades_update": lambda *_args: None,
        "_foco_vivo_atual": lambda: {},
        "_normalizar_texto_com_apelidos": str.casefold,
        "_atualizar_foco_vivo": lambda *_args, **_kwargs: None,
        "_estrutura_arquivo_recente": lambda **_kwargs: {},
        "BRIEFING_CIDADE": "Boituva",
    }
    runtime = EstadoContextoRuntime(
        namespace_getter=lambda: namespace,
        estado_runtime_getter=lambda: SimpleNamespace(mental=mente),
    )

    contexto = runtime.estado_contexto_intencao()

    assert contexto["ultimo_app_janela"] == "microsoft store"
    assert contexto["mente_integrada_estado"] == mente


class _ContextoCadeia:
    def __init__(self) -> None:
        self.mente = {
            "ultima_acao_intent": "APP_OPEN",
            "ultima_acao_params": {"nome_app": "microsoft store"},
            "ultimo_app_janela": "microsoft store",
            "aprendizado_continuidade": {
                "preferencias_conflito": {},
                "preferencias_operacao": {"app:ABRIR>FECHAR": 3},
                "correcoes": [],
            },
        }
        self.falas: list[str] = []
        self.registros: list[dict] = []

    def montar(self) -> dict:
        return {
            "turno_atual": {"id": "turno-227", "autoriza_execucao": True},
            "retrato_turno_atual": {},
            "ultimo_app_janela": self.mente["ultimo_app_janela"],
            "_resolver_alvo_ambiente": lambda nome: {
                "programa_aberto": nome == self.mente["ultimo_app_janela"],
                "programa_em_foco": nome == self.mente["ultimo_app_janela"],
            },
            "_emitir_resposta_curta": (
                lambda _texto, fala, **_kwargs: self.falas.append(fala)
            ),
            "_registrar_resultado_execucao": (
                lambda resultado, *_args, **_kwargs: self.registros.append(
                    dict(resultado)
                )
            ),
        }


def test_red_ciclo_canonico_executa_mutacoes_e_confirmacao_readonly() -> None:
    contexto = _ContextoCadeia()

    def detectar(trecho: str) -> dict | None:
        t = str(trecho or "").casefold().strip()
        if t == "abra a microsoft store":
            return {
                "intent": "APP_OPEN",
                "params": {"nome_app": "microsoft store"},
            }
        return detectar_organizacao_desktop(
            t,
            params_cb=lambda **kwargs: kwargs,
        )

    def resolver_contextual(trecho: str) -> dict | None:
        return resolver_continuidade_semantica(
            trecho,
            mente=contexto.mente,
        ).para_intencao()

    namespace = {
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_texto_depende_de_contexto": (
            lambda texto: any(
                pronome in str(texto).casefold().split()
                for pronome in ("ela", "ele", "isso")
            )
        ),
        "detectar_intencao_deterministica": detectar,
        "_resolver_comando_contextual_forcado": resolver_contextual,
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
        "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
    }
    ciclo = CicloComandosRuntime(
        namespace_getter=lambda: namespace,
        contexto_intencao_runtime=contexto,
        log=lambda *_: None,
    )

    def executar(intent: dict, _texto: str) -> bool:
        contexto.registros.append(dict(intent))
        contexto.mente["ultima_acao_intent"] = str(intent.get("intent") or "")
        contexto.mente["ultima_acao_params"] = dict(intent.get("params") or {})
        contexto.mente["ultimo_app_janela"] = "microsoft store"
        return True

    ciclo.executar_intencao = executar

    assert ciclo.processar_cadeia(FALA_227, "turno-227") is True
    assert [item["intent"] for item in contexto.registros] == [
        "APP_OPEN",
        "ORGANIZAR_DESKTOP",
        "LIST_WINDOWS",
    ]


def test_avaliador_v8_congela_contrato_operacional_do_turno227() -> None:
    falho = avaliar_turno_roteiro(
        indice=226,
        comando=FALA_227,
        resposta="Não tenho um resultado recente esperando para ser copiado.",
        plano={"comandos": []},
        respondeu=True,
        motivo_resultado="execucao_nao_publicada",
    )
    assert falho["resultado_semantico"] == "falhou"
    assert "intent_ausente:APP_OPEN" in falho["erros_semanticos"]
    assert "intent_ausente:ORGANIZAR_DESKTOP" in falho["erros_semanticos"]
    assert "intent_ausente:LIST_WINDOWS" in falho["erros_semanticos"]

    correto = avaliar_turno_roteiro(
        indice=226,
        comando=FALA_227,
        resposta="A Microsoft Store está aberta e ficou posicionada à direita.",
        plano={
            "comandos": [
                {
                    "intent": "APP_OPEN",
                    "status": "ja_aberto_focado",
                    "executou": False,
                    "confirmado": True,
                },
                {
                    "intent": "ORGANIZAR_DESKTOP",
                    "status": "layout_confirmado",
                    "executou": True,
                    "confirmado": True,
                },
                {
                    "intent": "LIST_WINDOWS",
                    "status": "estado_app_consultado",
                    "executou": True,
                    "confirmado": True,
                },
            ]
        },
        respondeu=True,
    )
    assert correto["resultado_semantico"] == "passou"
