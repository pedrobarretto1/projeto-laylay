from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from mente_laylay.memoria_mental.rede_associativa import (
    RedeAssociativaRuntime,
    RepositorioRedeAssociativa,
)
from mente_laylay.cognicao.seletor_contexto import selecionar_contexto_turno


def _repo(tmp_path: Path, **kwargs) -> RepositorioRedeAssociativa:
    return RepositorioRedeAssociativa(str(tmp_path / "mente.sqlite"), **kwargs)


def test_rede_persiste_nos_e_reforca_conexao_sem_duplicar(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    conceitos = [
        {"tipo": "dominio", "rotulo": "música", "confianca": 0.8},
        {"tipo": "alvo", "rotulo": "Slipknot", "confianca": 0.9},
    ]

    repo.registrar_contexto(conceitos, origem_evento="conversa")
    repo.registrar_contexto(conceitos, origem_evento="conversa")
    diagnostico = repo.diagnostico()

    assert diagnostico["nos"] == 2
    assert diagnostico["conexoes"] == 1
    with sqlite3.connect(repo.db_path) as conn:
        evidencias, peso = conn.execute(
            "SELECT evidencias, peso FROM rede_associativa_conexoes"
        ).fetchone()
    assert evidencias == 2
    assert peso > 0.10


def test_ativacao_se_espalha_por_associacao_sem_virar_fato(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.registrar_contexto(
        [
            {"tipo": "dominio", "rotulo": "jogo"},
            {"tipo": "alvo", "rotulo": "Path of Exile 2"},
        ],
        origem_evento="turno_1",
    )
    with sqlite3.connect(repo.db_path) as conn:
        conn.execute("DELETE FROM rede_associativa_ativacoes")
        conn.commit()

    resultado = repo.registrar_contexto(
        [
            {"tipo": "dominio", "rotulo": "jogo"},
            {"tipo": "intencao", "rotulo": "GAME_VISION"},
        ],
        origem_evento="turno_2",
    )

    chaves = {item["chave"] for item in resultado["ativados"]}
    assert "alvo:path_of_exile_2" in chaves
    assert "intencao:game_vision" in chaves


def test_contexto_generico_nao_vira_ponte_entre_dominios(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    for _ in range(3):
        repo.registrar_contexto(
            [
                {"tipo": "contexto", "rotulo": "cotidiano"},
                {"tipo": "intencao", "rotulo": "MUSIC_SEARCH"},
                {"tipo": "alvo", "rotulo": "Paranoid Android"},
                {"tipo": "dominio", "rotulo": "música"},
            ],
            origem_evento="musica",
        )

    somente_contexto = repo.simular_memoria_trabalho(
        [{"tipo": "contexto", "rotulo": "cotidiano"}],
    )
    contexto_musical = repo.simular_memoria_trabalho(
        [
            {"tipo": "intencao", "rotulo": "MUSIC_SEARCH"},
            {"tipo": "dominio", "rotulo": "música"},
        ],
    )

    assert somente_contexto == []
    assert any(item["chave"] == "alvo:paranoid_android" for item in contexto_musical)


def test_migracao_desativa_cliques_da_primeira_versao(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    agora = time.time()
    with sqlite3.connect(repo.db_path) as conn:
        conn.execute(
            "INSERT INTO rede_associativa_nos(chave,tipo,rotulo,confianca,ativacao_base,proveniencia,criado_ts,atualizado_ts,ultimo_uso_ts) VALUES ('contexto:cotidiano','contexto','cotidiano',.5,.1,'teste',?,?,?)",
            (agora, agora, agora),
        )
        conn.execute(
            "INSERT INTO rede_associativa_nos(chave,tipo,rotulo,confianca,ativacao_base,proveniencia,criado_ts,atualizado_ts,ultimo_uso_ts) VALUES ('alvo:lampada','alvo','lampada',.5,.1,'teste',?,?,?)",
            (agora, agora, agora),
        )
        ids = [row[0] for row in conn.execute(
            "SELECT id FROM rede_associativa_nos WHERE chave IN ('contexto:cotidiano','alvo:lampada') ORDER BY id"
        )]
        conn.execute(
            "INSERT INTO rede_associativa_conexoes(origem_id,destino_id,relacao,peso,confianca,evidencias,contradicoes,proveniencia,status,criado_ts,atualizado_ts) VALUES (?,?,'coocorre',.8,.8,9,0,'v1','observando',?,?)",
            (*ids, agora, agora),
        )
        conn.commit()

    RepositorioRedeAssociativa(repo.db_path)

    with sqlite3.connect(repo.db_path) as conn:
        status = conn.execute(
            "SELECT status FROM rede_associativa_conexoes WHERE relacao='coocorre'"
        ).fetchone()[0]
    assert status == "legado_sombra"


def test_rede_recusa_segredos_urls_emails_e_caminhos(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    resultado = repo.registrar_contexto(
        [
            {"tipo": "alvo", "rotulo": "pessoa@example.com"},
            {"tipo": "alvo", "rotulo": "https://exemplo.com/privado"},
            {"tipo": "alvo", "rotulo": r"C:\\Users\\Pessoa\\segredo.txt"},
            {"tipo": "contexto", "rotulo": "cotidiano"},
        ],
        origem_evento="seguranca",
    )

    assert resultado["nos"] == 1
    assert repo.diagnostico()["nos"] == 1


def test_ativacao_tem_decaimento_temporal(tmp_path: Path) -> None:
    agora = [1_000_000.0]
    repo = _repo(tmp_path, clock=lambda: agora[0])
    repo.registrar_contexto(
        [{"tipo": "dominio", "rotulo": "música"}],
        origem_evento="agora",
    )
    inicial = repo.listar_ativados(limit=1)[0]["intensidade"]
    agora[0] += 1800.0
    posterior = repo.listar_ativados(limit=1)[0]["intensidade"]

    assert inicial == 0.9
    assert 0.44 <= posterior <= 0.46


def test_runtime_enfileira_sem_bloquear_e_processa_em_sombra(tmp_path: Path) -> None:
    runtime = RedeAssociativaRuntime(
        db_path=str(tmp_path / "mente.sqlite"),
        modo="sombra",
        contexto_getter=lambda: {
            "periodo": "noite", "aplicativo": "PathOfExileSteam.exe",
            "modo_jogo_ativo": True,
        },
        log=lambda *_args: None,
    )

    aceito = runtime.observar_interacao(
        intencao="GAME_VISION", alvo="bota rara",
        escopo="jogo", habilidade="visao_jogo",
    )
    processados = runtime.processar_pendentes()
    diagnostico = runtime.diagnostico()

    assert aceito is True
    assert processados == 1
    assert diagnostico["modo"] == "sombra"
    assert diagnostico["influencia_habilitada"] is False
    assert diagnostico["nos"] >= 6
    assert diagnostico["metricas"]["processados"] == 1
    assert diagnostico["metricas"]["comparacoes_sombra"] == 1


def test_runtime_deduplica_evento_repetido_e_ignora_sinal_tecnico(tmp_path: Path) -> None:
    runtime = RedeAssociativaRuntime(
        db_path=str(tmp_path / "mente.sqlite"), modo="sombra", log=lambda *_args: None,
    )

    primeiro = runtime.observar_interacao(
        intencao="IOT_CONTROL", alvo="lampada_quarto", habilidade="iot",
    )
    repetido = runtime.observar_interacao(
        intencao="IOT_CONTROL", alvo="lampada_quarto", habilidade="iot",
    )
    tecnico = runtime.observar_interacao(
        intencao="FALA_PROATIVA", alvo="inicialização", habilidade="abertura",
    )
    runtime.processar_pendentes()

    assert primeiro is True
    assert repetido is False
    assert tecnico is False
    assert runtime.diagnostico()["metricas"]["duplicados"] == 1
    chaves = {
        item["chave"] for item in runtime.repositorio.listar_ativados(limit=20)
    }
    assert "intencao:fala_proativa" not in chaves


def test_runtime_observa_topico_estruturado_em_conversa(tmp_path: Path) -> None:
    runtime = RedeAssociativaRuntime(
        db_path=str(tmp_path / "mente.sqlite"),
        modo="sombra",
        contexto_getter=lambda: {
            "ultimo_topico_conversa": "inteligência artificial",
            "periodo": "tarde",
        },
        log=lambda *_args: None,
    )

    assert runtime.observar_interacao(habilidade="conversa") is True
    runtime.processar_pendentes()

    with sqlite3.connect(runtime.repositorio.db_path) as conn:
        topicos = conn.execute(
            "SELECT chave FROM rede_associativa_nos WHERE tipo='topico'"
        ).fetchall()
    assert topicos == [("topico:inteligencia_artificial",)]


def test_runtime_nao_anexa_topico_antigo_a_comando(tmp_path: Path) -> None:
    runtime = RedeAssociativaRuntime(
        db_path=str(tmp_path / "mente.sqlite"),
        modo="sombra",
        contexto_getter=lambda: {"ultimo_topico_conversa": "inventário do jogo"},
        log=lambda *_args: None,
    )

    assert runtime.observar_interacao(
        intencao="IOT_CONTROL",
        alvo="lampada_quarto",
        habilidade="iot",
    ) is True
    runtime.processar_pendentes()

    with sqlite3.connect(runtime.repositorio.db_path) as conn:
        quantidade = conn.execute(
            "SELECT COUNT(*) FROM rede_associativa_nos WHERE tipo='topico'"
        ).fetchone()[0]
    assert quantidade == 0


def test_runtime_isola_falha_do_repositorio(tmp_path: Path) -> None:
    class _RepositorioFalho:
        def registrar_contexto(self, *_args, **_kwargs):
            raise RuntimeError("falha deliberada")

        def diagnostico(self):
            return {"nos": 0, "conexoes": 0, "ativacoes": 0, "mais_ativos": []}

    runtime = RedeAssociativaRuntime(
        db_path=str(tmp_path / "mente.sqlite"),
        modo="sombra", repositorio=_RepositorioFalho(), log=lambda *_args: None,
    )
    runtime.observar_interacao(intencao="APP_OPEN", alvo="calculadora")

    assert runtime.processar_pendentes() == 1
    assert runtime.diagnostico()["metricas"]["falhas"] == 1


def test_worker_pode_ser_encerrado_sem_prender_python(tmp_path: Path) -> None:
    runtime = RedeAssociativaRuntime(
        db_path=str(tmp_path / "mente.sqlite"), modo="sombra", log=lambda *_args: None,
    )
    runtime.iniciar()
    runtime.observar_resultado(
        intencao="IOT_CONTROL", alvo="lampada_quarto",
        status="ligada", executou=True, confirmado=True,
    )
    limite = time.time() + 2.0
    while runtime.diagnostico()["metricas"]["processados"] < 1 and time.time() < limite:
        time.sleep(0.01)
    runtime.encerrar()

    assert runtime.diagnostico()["metricas"]["processados"] == 1
    assert runtime._thread is not None
    assert not runtime._thread.is_alive()


def test_plasticidade_exige_tres_amostras_antes_de_ajustar(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    conceitos = [
        {"tipo": "intencao", "rotulo": "SUGESTAO_PROATIVA"},
        {"tipo": "alvo", "rotulo": "musica"},
        {"tipo": "dominio", "rotulo": "proatividade"},
        {"tipo": "periodo", "rotulo": "noite"},
    ]

    primeiro = repo.registrar_feedback(conceitos, resultado="aceita")
    segundo = repo.registrar_feedback(conceitos, resultado="aceita")
    terceiro = repo.registrar_feedback(conceitos, resultado="aceita")

    assert primeiro["status"] == "observando"
    assert segundo["status"] == "observando"
    assert terceiro["status"] == "ajustado_sombra"
    assert terceiro["delta_peso"] == 0.06
    assert terceiro["conexoes_ajustadas"] >= 1
    assert repo.diagnostico()["plasticidade"]["amostras"] == 3


def test_correcao_repetida_enfraquece_sem_apagar_associacao(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    conceitos = [
        {"tipo": "intencao", "rotulo": "SUGESTAO_PROATIVA"},
        {"tipo": "alvo", "rotulo": "jogo"},
        {"tipo": "dominio", "rotulo": "proatividade"},
    ]
    repo.registrar_feedback(conceitos, resultado="correcao")
    repo.registrar_feedback(conceitos, resultado="correcao")
    resultado = repo.registrar_feedback(conceitos, resultado="correcao")

    with sqlite3.connect(repo.db_path) as conn:
        peso, contradicoes, status = conn.execute(
            "SELECT peso, contradicoes, status FROM rede_associativa_conexoes "
            "WHERE relacao='refere_se_a'"
        ).fetchone()
    assert resultado["status"] == "ajustado_sombra"
    assert resultado["delta_peso"] == -0.15
    assert peso >= 0.03
    assert contradicoes == 3
    assert status == "observando"


def test_feedback_preserva_perfis_de_periodos_diferentes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    base = [
        {"tipo": "intencao", "rotulo": "SUGESTAO_PROATIVA"},
        {"tipo": "alvo", "rotulo": "pausa"},
        {"tipo": "dominio", "rotulo": "proatividade"},
    ]
    repo.registrar_feedback([*base, {"tipo": "periodo", "rotulo": "manha"}], resultado="aceita")
    repo.registrar_feedback([*base, {"tipo": "periodo", "rotulo": "noite"}], resultado="recusa")

    diagnostico = repo.diagnostico()["plasticidade"]
    assert diagnostico["perfis"] == 2
    assert diagnostico["amostras"] == 2
    assert diagnostico["aceitas"] == 1
    assert diagnostico["recusas"] == 1


def test_runtime_processa_feedback_sem_habilitar_influencia(tmp_path: Path) -> None:
    runtime = RedeAssociativaRuntime(
        db_path=str(tmp_path / "mente.sqlite"),
        modo="sombra",
        contexto_getter=lambda: {"periodo": "noite", "modo_jogo_ativo": True},
        log=lambda *_args: None,
    )

    assert runtime.observar_feedback(categoria="jogo", resultado="aceita") is True
    assert runtime.processar_pendentes() == 1
    diagnostico = runtime.diagnostico()

    assert diagnostico["metricas"]["feedbacks"] == 1
    assert diagnostico["metricas"]["ajustes_plasticidade"] == 0
    assert diagnostico["plasticidade"]["amostras"] == 1
    assert diagnostico["influencia_habilitada"] is False


def test_continuidade_expoe_somente_associacao_madura_sem_contradicao(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    conceitos = [
        {"tipo": "topico", "rotulo": "metal", "confianca": 0.9},
        {"tipo": "alvo", "rotulo": "Slipknot", "confianca": 0.9},
    ]
    for _ in range(6):
        repo.registrar_contexto(conceitos, origem_evento="conversa")
    runtime = RedeAssociativaRuntime(
        db_path=repo.db_path,
        modo="continuidade",
        contexto_getter=lambda: {"ultimo_topico_conversa": "metal"},
        repositorio=repo,
        log=lambda *_args: None,
    )

    runtime.observar_interacao(habilidade="conversa")
    runtime.processar_pendentes()
    sinais = runtime.sinais_continuidade()

    assert runtime.influencia_habilitada is True
    assert any(item["rotulo"] == "Slipknot" for item in sinais)
    assert all(item["evidencias"] >= 5 for item in sinais)


def test_modo_sombra_nunca_expoe_pista_de_continuidade(tmp_path: Path) -> None:
    runtime = RedeAssociativaRuntime(
        db_path=str(tmp_path / "mente.sqlite"), modo="sombra", log=lambda *_args: None,
    )
    runtime._cache_continuidade = {
        "ts": time.time(),
        "itens": [{
            "tipo": "alvo", "rotulo": "Slipknot", "score": 0.8,
            "evidencias": 10, "confianca": 0.9,
        }],
    }

    assert runtime.sinais_continuidade() == []


def test_associacao_so_desempata_referencia_e_nao_injeta_assunto() -> None:
    agora = time.time()
    mente = {"ultimo_topico_ts": agora}
    turno = {"modalidade": "pergunta", "texto": "e ele?"}
    contexto = {
        "topico_ativo": "Slipknot",
        "associacoes_continuidade": [{
            "tipo": "alvo", "rotulo": "Slipknot", "score": 0.2,
            "evidencias": 6, "confianca": 0.8,
        }],
    }

    sem_rede = selecionar_contexto_turno(
        "e ele?", turno=turno, mente=mente,
        contexto_perceptivo={"topico_ativo": "Slipknot"},
    )
    com_rede = selecionar_contexto_turno(
        "e ele?", turno=turno, mente=mente, contexto_perceptivo=contexto,
    )
    novo_assunto = selecionar_contexto_turno(
        "me explica inteligência artificial",
        turno={"modalidade": "pergunta", "texto": "me explica inteligência artificial"},
        mente=mente, contexto_perceptivo=contexto,
    )

    assert sem_rede["selecionados"] == []
    assert com_rede["influencia_associativa"] is True
    assert com_rede["selecionados"][0]["conteudo"] == "Slipknot"
    assert novo_assunto["influencia_associativa"] is False
    assert novo_assunto["selecionados"] == []


def test_comando_nunca_recebe_reforco_associativo() -> None:
    selecao = selecionar_contexto_turno(
        "apaga isso",
        turno={"modalidade": "comando", "texto": "apaga isso"},
        mente={"ultimo_topico_ts": time.time()},
        contexto_perceptivo={
            "topico_ativo": "antonio",
            "associacoes_continuidade": [{
                "tipo": "alvo", "rotulo": "antonio", "score": 0.9,
                "evidencias": 20, "confianca": 0.99,
            }],
        },
    )

    assert selecao["influencia_associativa"] is False


def test_feedbacks_opostos_no_mesmo_contexto_nao_sao_deduplicados(tmp_path: Path) -> None:
    runtime = RedeAssociativaRuntime(
        db_path=str(tmp_path / "mente.sqlite"), modo="sombra", log=lambda *_args: None,
    )

    assert runtime.observar_feedback(categoria="musica", resultado="aceita") is True
    assert runtime.observar_feedback(categoria="musica", resultado="correcao") is True
    assert runtime.processar_pendentes() == 2
    plasticidade = runtime.diagnostico()["plasticidade"]

    assert plasticidade["amostras"] == 2
    assert plasticidade["aceitas"] == 1
    assert plasticidade["correcoes"] == 1
