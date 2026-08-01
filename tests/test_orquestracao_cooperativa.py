from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from mente_laylay.arquivos.arquivos_sistema import escrever_arquivo_texto_seguro
from mente_laylay.arquivos.execucao_arquivos import executar_intencao_arquivos
from mente_laylay.arquivos.mutacoes import criar_arquivos_mutacao_runtime
from mente_laylay.integracao.registro_mutacoes_arquivos import registrar_arquivos_mutacao
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.executor_sistema import (
    DependenciasExecutorSistema,
    executar_intencao_sistema,
)
from mente_laylay.autonomia.orquestracao_cooperativa import (
    ExecutorPlanoCooperativoRuntime,
    GovernancaPlanoCooperativoRuntime,
    OrquestradorCooperativoRuntime,
    QuadroCooperacaoRuntime,
)
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime
from mente_laylay.memoria_mental.contexto_compartilhado import (
    registrar_resultado_execucao,
    resolver_repeticao_ultima_acao,
)
from mente_laylay.memoria_mental.continuidade_geral import (
    registrar_evento_continuidade,
)
from tests.fakes_visao_jogo import VisaoJogoAnaliseFake


def _digest(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _montar_fluxo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, conteudo_inicial: str):
    monkeypatch.setenv("LAYLAY_ARQUIVOS_RAIZES_PERMITIDAS", str(tmp_path))
    clipboard = {"texto": conteudo_inicial, "bloqueado": False}
    estado: dict = {}
    falas: list[str] = []
    publicacoes: list[dict] = []
    comandos: list[dict] = []
    aprendizados: list[tuple[dict, str]] = []
    orquestrador_ref: list[OrquestradorCooperativoRuntime | None] = [None]

    def atualizar(mutador):
        novo = dict(mutador(dict(estado)) or estado)
        estado.clear()
        estado.update(novo)
        return dict(estado)

    pendencia = PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        log=lambda _texto: None,
    )

    def snapshot_clipboard():
        texto = clipboard["texto"]
        return {
            "status": "ok",
            "tipo": "sensivel" if clipboard["bloqueado"] else "texto_longo",
            "bloqueado": clipboard["bloqueado"],
            "assinatura": _digest(texto),
        }

    def resolver_caminho(valor: str) -> str:
        caminho = Path(valor)
        return str(caminho if caminho.is_absolute() else tmp_path / caminho)

    def executar(resultado: dict, texto_original: str) -> bool:
        comandos.append(resultado)

        def marcar(status: str, executou: bool | None) -> None:
            estado.update({
                "ultima_acao_intent": str(resultado.get("intent") or ""),
                "ultima_acao_status": status,
                "ultima_acao_confirmada": (
                    True if status == "arquivo_criado" and executou is True else False
                ),
            })

        runtime = orquestrador_ref[0]
        assert runtime is not None
        return executar_intencao_arquivos(
            str(resultado.get("intent") or ""),
            dict(resultado.get("params") or {}),
            "pc_local",
            {
                "falar_com_lipsync": lambda fala, _emocao, _nivel: falas.append(fala),
                "criar_ou_editar_arquivo": lambda *_args: False,
                "escrever_arquivo_texto_seguro": escrever_arquivo_texto_seguro,
                "_resolver_referencia_cooperativa": runtime.resolver_referencia,
            },
            texto_original=texto_original,
            marcar_resultado=marcar,
            registrar_arquivo=lambda _caminho, _habilidade: None,
            item_local_existe=lambda caminho, _tipo: Path(caminho).is_file(),
            resolver_caminho_local=resolver_caminho,
            resolver_referencia_arquivo_contextual=lambda alvo, _tipo: alvo,
            arquivos_mutacao=registrar_arquivos_mutacao(
                criar_arquivos_mutacao_runtime(
                    resolver_caminho_cb=resolver_caminho,
                    criar_arquivo_cb=lambda *_args: False,
                    escrever_texto_seguro_cb=escrever_arquivo_texto_seguro,
                )
            ),
        )

    quadro = QuadroCooperacaoRuntime(
        modo="sombra",
        publicar_contexto=lambda snapshot: publicacoes.append(dict(snapshot)),
        log=lambda _texto: None,
    )
    orquestrador = OrquestradorCooperativoRuntime(
        quadro=quadro,
        clipboard_snapshot=snapshot_clipboard,
        clipboard_getter=lambda: "" if clipboard["bloqueado"] else clipboard["texto"],
        executar_intencao=executar,
        resolver_caminho=resolver_caminho,
        falar=lambda fala, _emocao, _nivel: falas.append(fala),
        estado_getter=lambda: estado,
        pendencia_runtime=pendencia,
        registrar_aprendizado=lambda plano, decisao: aprendizados.append(
            (dict(plano), str(decisao)),
        ),
        registrar_decisao=lambda *_args, **_kwargs: None,
        log=lambda _texto: None,
    )
    orquestrador_ref[0] = orquestrador
    imediato = ComandosImediatosRuntime(
        namespace_getter=lambda: {"_orquestrador_cooperativo_runtime": orquestrador},
        loop_getter=lambda: None,
    )
    return {
        "clipboard": clipboard,
        "estado": estado,
        "falas": falas,
        "publicacoes": publicacoes,
        "comandos": comandos,
        "aprendizados": aprendizados,
        "pendencia": pendencia,
        "orquestrador": orquestrador,
        "imediato": imediato,
    }


def test_composicao_real_clipboard_para_arquivo_confirma_conteudo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    segredo = "conteúdo único que não pode aparecer no quadro"
    ambiente = _montar_fluxo(tmp_path, monkeypatch, segredo)

    tratado = ambiente["imediato"].processar_prioritarios(
        "pode colocar o que eu copiei em um arquivo de texto chamado tete"
    )

    assert tratado is True
    assert (tmp_path / "tete.txt").read_text(encoding="utf-8") == segredo
    assert ambiente["estado"]["ultima_acao_status"] == "arquivo_criado"
    assert ambiente["estado"]["ultima_acao_confirmada"] is True
    assert len(ambiente["falas"]) == 1
    assert len(ambiente["comandos"]) == 1
    comando = ambiente["comandos"][0]
    assert "conteudo" not in comando["params"]
    assert comando["params"]["conteudo_ref"]
    assert segredo not in str(ambiente["publicacoes"])
    assert str(tmp_path) not in str(ambiente["publicacoes"])
    assert ambiente["orquestrador"].diagnostico()["confirmados"] == 1
    assert ambiente["orquestrador"].diagnostico()["referencias_ativas"] == 0
    assert ambiente["aprendizados"][0][1] == "aceito"
    assert segredo not in str(ambiente["aprendizados"])


def test_composicao_janelas_percebe_prioriza_e_confirma_um_so_layout() -> None:
    estado: dict = {}
    falas: list[str] = []
    comandos: list[dict] = []
    aprendizados: list[tuple[dict, str]] = []
    quadro = QuadroCooperacaoRuntime(
        modo="sombra", publicar_contexto=lambda _snapshot: None,
        log=lambda _texto: None,
    )

    def executar(resultado: dict, _texto: str) -> bool:
        comandos.append(resultado)
        estado.update({
            "ultima_acao_intent": "ORGANIZAR_DESKTOP",
            "ultima_acao_status": "layout_confirmado",
            "ultima_acao_confirmada": True,
        })
        falas.append("Organizei e conferi o layout.")
        return True

    runtime = OrquestradorCooperativoRuntime(
        quadro=quadro,
        clipboard_snapshot=lambda: {},
        clipboard_getter=lambda: "",
        executar_intencao=executar,
        resolver_caminho=lambda valor: valor,
        falar=lambda fala, _emocao, _nivel: falas.append(fala),
        planejar_layout=lambda: {
            "ok": True,
            "confirmado": True,
            "status": "layout_planejado",
            "quantidade": 3,
            "nome_esquerda": "Visual Studio Code",
            "nome_direita": "Google Chrome",
            "prioridades": [
                {"titulo": "Visual Studio Code", "pontuacao": 1000, "motivos": ["janela em foco"]},
                {"titulo": "Google Chrome", "pontuacao": 340, "motivos": ["reproduzindo áudio"]},
                {"titulo": "Discord", "pontuacao": 100, "motivos": ["uso recente"]},
            ],
        },
        estado_getter=lambda: estado,
        autorizar_acao=lambda *_args, **_kwargs: {
            "permitido": True, "motivo": "pedido explícito",
        },
        registrar_aprendizado=lambda plano, decisao: aprendizados.append(
            (dict(plano), str(decisao)),
        ),
        log=lambda _texto: None,
    )

    assert runtime.processar("organiza minha área de trabalho") is True
    assert len(comandos) == 1
    assert comandos[0]["intent"] == "ORGANIZAR_DESKTOP"
    assert comandos[0]["params"]["left"] == "Visual Studio Code"
    assert comandos[0]["params"]["right"] == "Google Chrome"
    assert comandos[0]["params"]["modo"] == "automatico_cooperativo"
    assert len(falas) == 1
    plano = quadro.snapshot()["planos_recentes"][-1]
    assert plano["estado"] == "confirmado"
    assert [etapa["estado"] for etapa in plano["etapas"]] == [
        "confirmado", "confirmado", "confirmado",
    ]
    assert plano["metadados"]["quantidade_janelas"] == 3
    assert aprendizados[-1][1] == "aceito"


def test_composicao_item_jogo_reusa_detector_executor_e_fecha_assincrono() -> None:
    quadro = QuadroCooperacaoRuntime(
        modo="sombra", publicar_contexto=lambda _snapshot: None,
        log=lambda _texto: None,
    )
    comandos: list[dict] = []
    falas: list[str] = []
    aprendizados: list[str] = []
    resultados_visao: list[tuple[str, dict]] = []
    analise_tipado = VisaoJogoAnaliseFake()
    runtime_ref: list[OrquestradorCooperativoRuntime | None] = [None]

    def detectar(_texto: str) -> dict:
        return {
            "intent": "GAME_VISION",
            "params": {
                "pergunta": "essa bota é boa?",
                "tipo": "avaliacao_item",
                "jogo": "Path of Exile 2",
                "requer_cursor": True,
            },
        }

    def executar(resultado: dict, _texto: str) -> bool:
        comandos.append(resultado)
        despacho = executar_intencao_sistema(
            "GAME_VISION",
            dict(resultado.get("params") or {}),
            "pc_a",
            {"_registro_visao_jogo_analise_runtime": analise_tipado},
            DependenciasExecutorSistema(
                marcar_resultado=lambda status, **kwargs: resultados_visao.append(
                    (status, kwargs)
                ),
                falar_por_status=lambda *_args, **_kwargs: None,
            ),
        )
        assert despacho.retorno is True
        runtime = runtime_ref[0]
        assert runtime is not None
        plano_id = resultado["params"]["_plano_cooperativo_id"]
        for evento in (
            {"fase": "leitura_visual", "status": "item_lido", "duracao_ms": 120},
            {"fase": "pesquisa", "status": "evidencia_externa_encontrada", "duracao_ms": 180},
            {"fase": "parecer_final", "status": "parecer_pronto", "duracao_ms": 220},
        ):
            assert runtime.registrar_progresso_visao_jogo({
                "plano_id": plano_id, **evento,
            })
        return True

    runtime = OrquestradorCooperativoRuntime(
        quadro=quadro,
        clipboard_snapshot=lambda: {},
        clipboard_getter=lambda: "",
        executar_intencao=executar,
        resolver_caminho=lambda valor: valor,
        falar=lambda fala, _emocao, _nivel: falas.append(fala),
        detectar_visao_jogo=detectar,
        autorizar_acao=lambda *_args, **_kwargs: {
            "permitido": True, "motivo": "pedido_explicito",
        },
        registrar_aprendizado=lambda _plano, decisao: aprendizados.append(decisao),
        registrar_decisao=lambda *_args, **_kwargs: None,
        log=lambda _texto: None,
    )
    runtime_ref[0] = runtime

    imediato = ComandosImediatosRuntime(
        namespace_getter=lambda: {"_orquestrador_cooperativo_runtime": runtime},
        loop_getter=lambda: None,
    )
    assert imediato.processar_prioritarios("essa bota é boa?") is True
    assert len(comandos) == 1
    assert comandos[0]["intent"] == "GAME_VISION"
    assert analise_tipado.chamadas[0][0] == "executar"
    assert resultados_visao == [
        ("analise_visual_solicitada", {"executou": True})
    ]
    plano_id = comandos[0]["params"]["_plano_cooperativo_id"]
    plano = quadro.obter_plano(plano_id)
    assert plano and plano["estado"] == "confirmado"
    assert [etapa["estado"] for etapa in plano["etapas"]] == [
        "confirmado", "confirmado", "confirmado",
    ]
    assert falas == []
    assert aprendizados == ["aceito"]


def test_composicao_item_jogo_nao_sequestra_outra_pergunta_visual() -> None:
    runtime = OrquestradorCooperativoRuntime(
        quadro=QuadroCooperacaoRuntime(log=lambda _texto: None),
        clipboard_snapshot=lambda: {},
        clipboard_getter=lambda: "",
        executar_intencao=lambda *_args: True,
        resolver_caminho=lambda valor: valor,
        falar=lambda *_args: None,
        detectar_visao_jogo=lambda _texto: {
            "intent": "GAME_VISION",
            "params": {"tipo": "pergunta_visual", "pergunta": "o que é isso?"},
        },
        log=lambda _texto: None,
    )

    assert runtime.processar("o que é isso?") is False


@pytest.mark.parametrize(
    "texto",
    (
        "não organiza minha área de trabalho",
        "talvez fosse legal organizar as janelas",
        "como eu faria para organizar o desktop?",
        "você consegue organizar minhas janelas?",
    ),
)
def test_composicao_janelas_nao_executa_negacao_hipotese_ou_capacidade(
    texto: str,
) -> None:
    assert OrquestradorCooperativoRuntime.detectar(texto) is None


def test_sobrescrita_exige_pendencia_canonica_e_confirma_depois(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "tete.txt").write_text("conteúdo anterior", encoding="utf-8")
    ambiente = _montar_fluxo(tmp_path, monkeypatch, "conteúdo novo")

    assert ambiente["imediato"].processar_prioritarios(
        "salva o texto copiado em um arquivo chamado tete"
    ) is True
    assert (tmp_path / "tete.txt").read_text(encoding="utf-8") == "conteúdo anterior"
    pendencia = ambiente["pendencia"].obter()
    assert pendencia and pendencia["origem"] == "orquestracao_cooperativa"
    assert ambiente["comandos"] == []

    assert ambiente["imediato"].processar_prioritarios("sim, pode substituir") is True
    assert (tmp_path / "tete.txt").read_text(encoding="utf-8") == "conteúdo novo"
    assert ambiente["pendencia"].obter() is None
    assert ambiente["estado"]["ultima_acao_confirmada"] is True
    assert len(ambiente["falas"]) == 2
    assert ambiente["aprendizados"][-1][1] == "aceito"


def test_mudanca_do_clipboard_invalida_confirmacao_de_sobrescrita(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    arquivo = tmp_path / "tete.txt"
    arquivo.write_text("original", encoding="utf-8")
    ambiente = _montar_fluxo(tmp_path, monkeypatch, "primeiro texto")
    ambiente["imediato"].processar_prioritarios(
        "coloca o texto copiado em um arquivo chamado tete"
    )

    ambiente["clipboard"]["texto"] = "outro texto copiado depois"
    assert ambiente["imediato"].processar_prioritarios("sim") is True

    assert arquivo.read_text(encoding="utf-8") == "original"
    assert ambiente["comandos"] == []
    assert "outra coisa" in ambiente["falas"][-1].casefold()


def test_recusa_ensina_sem_alterar_arquivo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    arquivo = tmp_path / "tete.txt"
    arquivo.write_text("não mexer", encoding="utf-8")
    ambiente = _montar_fluxo(tmp_path, monkeypatch, "texto novo")
    ambiente["imediato"].processar_prioritarios(
        "salva o que copiei em um arquivo chamado tete"
    )

    assert ambiente["imediato"].processar_prioritarios("não, deixa como está") is True

    assert arquivo.read_text(encoding="utf-8") == "não mexer"
    assert ambiente["comandos"] == []
    assert ambiente["aprendizados"][-1][1] == "recusado"
    assert ambiente["orquestrador"].diagnostico()["cancelados"] == 1


def test_conteudo_sensivel_e_frases_nao_executaveis_nao_criam_plano(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ambiente = _montar_fluxo(tmp_path, monkeypatch, "senha=segredo")
    ambiente["clipboard"]["bloqueado"] = True

    assert ambiente["imediato"].processar_prioritarios(
        "salva o que eu copiei em um arquivo chamado senha"
    ) is True
    assert not (tmp_path / "senha.txt").exists()
    assert ambiente["comandos"] == []
    assert ambiente["orquestrador"].diagnostico()["planos"] == 0

    for frase in (
        "não coloca o que copiei em um arquivo chamado x",
        "como eu faria para salvar o que copiei em um arquivo chamado x?",
        "você consegue colocar o que copiei em um arquivo chamado x?",
    ):
        assert OrquestradorCooperativoRuntime.detectar(frase) is None


def test_referencia_expira_e_snapshot_nunca_expoe_valor() -> None:
    agora = [100.0]
    quadro = QuadroCooperacaoRuntime(relogio=lambda: agora[0], log=lambda _texto: None)
    referencia = quadro.guardar_referencia("texto privado", tipo="teste", ttl_s=2)
    quadro.publicar_evento(
        origem="teste", tipo="texto", resumo="referência privada",
        confianca=1.0, relevancia=1.0, referencia=referencia["token"],
    )

    assert "texto privado" not in str(quadro.snapshot())
    assert referencia["token"] not in str(quadro.snapshot())
    assert quadro.resolver_referencia(referencia["token"])["ok"] is True
    agora[0] = 103.0
    assert quadro.resolver_referencia(referencia["token"])["status"] == "referencia_expirada"


def test_mapa_de_habilidades_da_nocao_da_cooperacao_sem_autorizar() -> None:
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt(
        "você consegue combinar habilidades para pôr o que copiei em um arquivo?"
    )
    resposta = mapa.responder_pergunta_capacidade(
        "Lay, você consegue combinar habilidades?"
    )

    assert "- cooperacao [disponivel]" in contexto
    assert "referência temporária" in resposta
    assert "orçamento de tempo" in resposta
    assert "falhas parciais" in resposta
    assert "Sobrescrita pede confirmação" in resposta
    assert mapa.consultar("COOPERATIVE_PLAN")["dominio"] == "cooperacao"


def test_falha_temporaria_preserva_repeticao_sem_persistir_conteudo() -> None:
    estado = registrar_resultado_execucao(
        {},
        {
            "intent": "CREATE_FILE",
            "params": {
                "alvo": "tete.txt",
                "conteudo_ref": "token-temporario",
                "conteudo_hash": "hash-seguro",
            },
            "status": "falha_execucao",
            "executou": False,
            "confirmado": False,
        },
        "coloca o que copiei em um arquivo chamado tete",
        False,
        origem="orquestracao_cooperativa",
    )

    repeticao = resolver_repeticao_ultima_acao(
        "tenta de novo", estado, lambda texto: texto.casefold(),
    )

    assert estado["ultima_acao_reexecutavel"] is True
    assert repeticao == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": "tete.txt",
            "conteudo_ref": "token-temporario",
            "conteudo_hash": "hash-seguro",
        },
    }
    assert "conteúdo bruto" not in str(estado)


def _plano_generico(
    quadro: QuadroCooperacaoRuntime,
    etapas: tuple[dict, ...],
    *,
    politica: str = "interromper",
    orcamento_ms: int = 1_000,
) -> dict:
    return quadro.criar_plano(
        objetivo="validar contrato cooperativo",
        evento_ids=(),
        etapas=etapas,
        confianca=1.0,
        risco="baixo",
        autorizacao="teste_explicito",
        orcamento_total_ms=orcamento_ms,
        politica_falha_parcial=politica,
        metadados={"fluxo": "teste_contrato", "segredo": "não publicar"},
    )


def test_contrato_rejeita_dependencia_futura_e_etapa_nao_idempotente() -> None:
    quadro = QuadroCooperacaoRuntime(log=lambda _texto: None)

    with pytest.raises(ValueError, match="etapa anterior"):
        _plano_generico(quadro, (
            {"id": "segunda", "acao": "b", "depende_de": ["primeira"]},
            {"id": "primeira", "acao": "a"},
        ))
    with pytest.raises(ValueError, match="idempotentes"):
        _plano_generico(quadro, (
            {"id": "unica", "acao": "a", "idempotente": False},
        ))


def test_executor_continua_etapa_independente_apos_falha_opcional() -> None:
    quadro = QuadroCooperacaoRuntime(log=lambda _texto: None)
    plano = _plano_generico(
        quadro,
        (
            {
                "id": "enriquecer", "habilidade": "pesquisa", "acao": "enriquecer",
                "obrigatoria": False, "politica_falha": "continuar",
                "evidencia_esperada": "fonte_confirmada",
            },
            {
                "id": "registrar", "habilidade": "memoria", "acao": "registrar",
                "evidencia_esperada": "registro_confirmado",
            },
        ),
        politica="continuar_independentes",
    )
    chamadas: list[str] = []
    executor = ExecutorPlanoCooperativoRuntime(quadro=quadro, log=lambda _texto: None)

    resultado = executor.executar(str(plano["id"]), {
        "enriquecer": lambda etapa, _plano: (
            chamadas.append(str(etapa["id"]))
            or {"ok": False, "confirmado": False, "status": "fonte_indisponivel"}
        ),
        "registrar": lambda etapa, _plano: (
            chamadas.append(str(etapa["id"]))
            or {
                "ok": True, "confirmado": True, "status": "registrado",
                "evidencia": "registro_confirmado",
            }
        ),
    })

    assert chamadas == ["enriquecer", "registrar"]
    assert resultado["ok"] is True
    assert resultado["status"] == "plano_confirmado_com_falha_parcial"
    assert quadro.diagnostico()["falhas_parciais"] == 1


def test_dependencia_falha_bloqueia_etapa_dependente() -> None:
    quadro = QuadroCooperacaoRuntime(log=lambda _texto: None)
    plano = _plano_generico(quadro, (
        {
            "id": "origem", "habilidade": "origem", "acao": "ler",
            "politica_falha": "continuar",
        },
        {
            "id": "destino", "habilidade": "destino", "acao": "gravar",
            "depende_de": ["origem"], "politica_falha": "continuar",
        },
    ), politica="continuar_independentes")
    chamadas: list[str] = []
    executor = ExecutorPlanoCooperativoRuntime(quadro=quadro, log=lambda _texto: None)

    resultado = executor.executar(str(plano["id"]), {
        "ler": lambda _etapa, _plano: {
            "ok": False, "confirmado": False, "status": "sem_evidencia",
        },
        "gravar": lambda _etapa, _plano: chamadas.append("gravar") or {
            "ok": True, "confirmado": True, "status": "gravado",
        },
    })

    assert resultado["ok"] is False
    assert chamadas == []
    final = quadro.obter_plano(str(plano["id"]))
    assert [etapa["estado"] for etapa in final["etapas"]] == ["falhou", "bloqueado"]
    assert quadro.diagnostico()["dependencias_bloqueadas"] == 1


def test_orcamento_excedido_interrompe_proximas_etapas() -> None:
    relogio = [10.0]
    quadro = QuadroCooperacaoRuntime(log=lambda _texto: None)
    plano = _plano_generico(quadro, (
        {"id": "lenta", "acao": "lenta", "orcamento_ms": 10},
        {"id": "seguinte", "acao": "seguinte"},
    ), orcamento_ms=50)
    chamadas: list[str] = []
    executor = ExecutorPlanoCooperativoRuntime(
        quadro=quadro, relogio=lambda: relogio[0], log=lambda _texto: None,
    )

    def lenta(_etapa, _plano):
        chamadas.append("lenta")
        relogio[0] += 0.060
        return {"ok": False, "confirmado": False, "status": "demorou"}

    resultado = executor.executar(str(plano["id"]), {
        "lenta": lenta,
        "seguinte": lambda _etapa, _plano: chamadas.append("seguinte") or {},
    })

    assert resultado["estado"] == "expirado"
    assert chamadas == ["lenta"]
    assert quadro.diagnostico()["orcamentos_excedidos"] == 1


def test_cancelamento_impede_execucao_e_repeticao_final_e_idempotente() -> None:
    quadro = QuadroCooperacaoRuntime(log=lambda _texto: None)
    cancelado = _plano_generico(quadro, ({"id": "acao", "acao": "agir"},))
    chamadas: list[str] = []
    quadro.solicitar_cancelamento(str(cancelado["id"]), "usuario_recusou")
    executor = ExecutorPlanoCooperativoRuntime(quadro=quadro, log=lambda _texto: None)

    resultado = executor.executar(str(cancelado["id"]), {
        "agir": lambda _etapa, _plano: chamadas.append("agir") or {},
    })
    assert resultado["estado"] == "cancelado"
    assert chamadas == []

    confirmado = _plano_generico(quadro, ({"id": "acao", "acao": "agir"},))
    retorno = {
        "ok": True, "confirmado": True, "status": "feito", "evidencia": "confirmada",
    }
    assert executor.executar(str(confirmado["id"]), {
        "agir": lambda _etapa, _plano: chamadas.append("agir") or retorno,
    })["ok"] is True
    assert executor.executar(str(confirmado["id"]), {
        "agir": lambda _etapa, _plano: chamadas.append("duplicada") or retorno,
    })["idempotente"] is True
    assert chamadas == ["agir"]


def test_snapshot_publico_expoe_contrato_sem_metadados_privados() -> None:
    quadro = QuadroCooperacaoRuntime(log=lambda _texto: None)
    plano = _plano_generico(quadro, ({
        "id": "acao", "habilidade": "arquivos", "acao": "agir",
        "evidencia_esperada": "resultado_confirmado",
    },))

    publico = quadro.plano_publico(plano)

    assert publico["orcamento_total_ms"] == 1_000
    assert publico["etapas"][0]["evidencia_esperada"] == "resultado_confirmado"
    assert "não publicar" not in str(publico)


def test_governanca_usa_porteiro_e_finaliza_pilares_uma_vez() -> None:
    quadro = QuadroCooperacaoRuntime(log=lambda _texto: None)
    plano = _plano_generico(quadro, ({
        "id": "acao", "habilidade": "iot", "acao": "controlar",
        "intent": "IOT_CONTROL",
    },))
    autorizacoes: list[tuple] = []
    continuidades: list[str] = []
    aprendizados: list[str] = []
    decisoes: list[tuple] = []
    chamadas: list[str] = []

    def autorizar(acao, texto, **kwargs):
        autorizacoes.append((acao, texto, kwargs))
        return {"permitido": False, "motivo": "porteiro_teste"}

    governanca = GovernancaPlanoCooperativoRuntime(
        quadro=quadro,
        autorizar_acao=autorizar,
        registrar_continuidade=lambda _plano, evento: continuidades.append(evento),
        registrar_aprendizado=lambda _plano, decisao: aprendizados.append(decisao),
        registrar_decisao=lambda *args, **kwargs: decisoes.append((args, kwargs)),
        log=lambda _texto: None,
    )
    executor = ExecutorPlanoCooperativoRuntime(
        quadro=quadro, governanca=governanca, log=lambda _texto: None,
    )

    resultado = executor.executar(
        str(plano["id"]),
        {"controlar": lambda _etapa, _plano: chamadas.append("executou") or {}},
        contexto_execucao={"texto": "liga a luz", "confirmado": False},
    )
    repetido = executor.executar(
        str(plano["id"]),
        {"controlar": lambda _etapa, _plano: chamadas.append("duplicou") or {}},
        contexto_execucao={"texto": "liga a luz", "confirmado": False},
    )

    assert resultado["ok"] is False
    assert repetido["estado"] == "falhou"
    assert chamadas == []
    assert autorizacoes[0][0] == "IOT_CONTROL"
    assert autorizacoes[0][1] == "liga a luz"
    assert continuidades == ["iniciado", "finalizado"]
    assert aprendizados == ["falhou"]
    assert len(decisoes) == 1
    assert quadro.diagnostico()["autorizacoes_bloqueadas"] == 1
    assert quadro.diagnostico()["finalizacoes_governanca"] == 1


def test_governanca_exige_confirmacao_para_plano_de_alto_risco() -> None:
    quadro = QuadroCooperacaoRuntime(log=lambda _texto: None)
    plano = quadro.criar_plano(
        objetivo="ação destrutiva de teste",
        evento_ids=(),
        etapas=({"id": "apagar", "acao": "apagar", "intent": "DELETE_ITEM"},),
        confianca=1.0,
        risco="destrutivo",
        autorizacao="explicita_no_pedido",
    )
    governanca = GovernancaPlanoCooperativoRuntime(quadro=quadro, log=lambda _texto: None)
    executor = ExecutorPlanoCooperativoRuntime(
        quadro=quadro, governanca=governanca, log=lambda _texto: None,
    )
    chamadas: list[str] = []

    resultado = executor.executar(
        str(plano["id"]),
        {"apagar": lambda _etapa, _plano: chamadas.append("apagou") or {
            "ok": True, "confirmado": True, "status": "apagado",
        }},
        contexto_execucao={"texto": "apaga isso", "confirmado": False},
    )

    assert resultado["status"] == "autorizacao_negada"
    assert chamadas == []


def test_continuidade_do_plano_nao_rouba_foco_da_ultima_habilidade() -> None:
    estado = registrar_evento_continuidade(
        {}, evento="acao", intent="CREATE_FILE", habilidade="arquivos",
        alvo="teste.txt", status="arquivo_criado", origem="executor",
    )
    estado = registrar_evento_continuidade(
        estado,
        evento="plano_finalizado",
        dominio="cooperacao",
        intent="COOPERATIVE_PLAN",
        habilidade="orquestracao_cooperativa",
        tipo="clipboard_para_arquivo",
        alvo="salvar conteúdo copiado em arquivo de texto",
        status="confirmado",
        origem="orquestracao_cooperativa",
        ativa=False,
        reexecutavel=False,
    )

    continuidade = estado["continuidade_geral"]
    assert continuidade["dominio_ativo"] == "arquivos"
    assert continuidade["dominios"]["cooperacao"]["ativa"] is False
    assert continuidade["historico"][-1]["dominio"] == "cooperacao"
