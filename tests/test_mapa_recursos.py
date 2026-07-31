from __future__ import annotations

from mente_laylay.memoria_mental.mapa_recursos import MapaRecursosRuntime
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime
from mente_laylay.memoria_mental.playlist_laylay_runtime import PlaylistLaylayRuntime
from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.autonomia.agendamento_mental import AgendaRuntime


def test_mapa_recursos_so_injeta_recurso_quando_relevante() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "playlists_usuario",
        arquivo="playlists.json",
        descricao="playlists reais",
        termos=("playlist", "musicas salvas"),
        leitor=lambda _texto: {
            "playlists": [{"nome": "rock", "total": 3}],
        },
        escrita_via="comandos de playlist",
    )

    assert mapa.contexto_para_prompt("como você está?") == ""
    contexto = mapa.contexto_para_prompt("quais são minhas playlists?")
    assert "playlists.json" in contexto
    assert "rock (3)" in contexto
    assert "não invente conteúdo" in contexto
    assert mapa.diagnostico()["acesso_bruto"] is False


def test_retrato_playlist_expoe_titulos_sem_expor_urls(tmp_path) -> None:
    arquivo = tmp_path / "playlists.json"
    arquivo.write_text(
        '{"rock": [{"titulo": "Duality", "url": "https://segredo.example/1"}], '
        '"calma": [{"titulo": "Brisa", "url": "https://segredo.example/2"}]}',
        encoding="utf-8",
    )
    runtime = PlaylistRuntime(
        state_file=str(arquivo),
        legacy_file=str(tmp_path / "legado.json"),
        cache={},
        ultima_playlist_getter=lambda: "",
        log=lambda _mensagem: None,
    )

    retrato = runtime.retrato_para_mente("o que tem na playlist rock?")

    assert retrato["playlists"] == [
        {"nome": "calma", "total": 1},
        {"nome": "rock", "total": 1},
    ]
    assert retrato["detalhe"] == {"nome": "rock", "titulos": ["Duality"]}
    assert "segredo.example" not in str(retrato)


def test_contexto_da_llm_recebe_recurso_somente_na_consulta_relacionada() -> None:
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _texto: "",
        formatar_playlists=lambda: "",
        get_status_humor_prompt=lambda: "",
        base_system_prompt="Você é Laylay.",
        estado_getter=lambda: {"messages": [], "turno_atual": {}},
        mapa_recursos_prompt=lambda texto: (
            "RECURSO REAL: rock (3)." if "playlist" in texto else ""
        ),
    )

    _, prompt_playlist = runtime.preparar("qual minha playlist?")
    _, prompt_conversa = runtime.preparar("como você está?")

    assert "RECURSO REAL: rock (3)." in prompt_playlist
    assert "RECURSO REAL" not in prompt_conversa


def test_retrato_agenda_omite_intencao_executavel(tmp_path) -> None:
    agora = 1_800_000_000.0
    runtime = AgendaRuntime(
        str(tmp_path / "agendamentos.json"),
        falar_cb=lambda *_: None,
        abrir_programa_cb=lambda *_: None,
        enviar_pc_b_cb=lambda *_: None,
        enviar_chrome_local_cb=lambda *_: None,
        executar_exec_cb=lambda *_: None,
        time_cb=lambda: agora,
        log=lambda *_: None,
    )
    runtime.save([{
        "nome": "Academia", "tipo": "daily", "hora": "18:30", "ativo": True,
        "intencao_no_disparo": {"intent": "APP_OPEN", "params": {"segredo": "x"}},
    }])

    retrato = runtime.retrato_para_mente()

    assert retrato["agendamentos"] == [{
        "nome": "Academia", "tipo": "daily", "quando": "18:30",
    }]
    assert "APP_OPEN" not in str(retrato)
    assert "segredo" not in str(retrato)


def test_retrato_playlists_da_laylay_omite_urls(tmp_path) -> None:
    arquivo = tmp_path / "playlists_da_laylay.json"
    arquivo.write_text(
        '{"xodos_que_eu_seperei": [{"titulo": "Sulfur", '
        '"url": "https://privado.example/faixa"}]}',
        encoding="utf-8",
    )
    runtime = PlaylistLaylayRuntime(
        state_file=str(arquivo),
        cache={},
        playlists_usuario_getter=lambda: {},
        historico_musical_getter=lambda: {},
        adicionar_playlist_usuario=lambda *_: {},
    )

    retrato = runtime.retrato_para_mente("o que tem nos xodos que eu separei?")

    assert retrato["playlists"] == [{"nome": "xodos_que_eu_seperei", "total": 1}]
    assert retrato["detalhe"]["titulos"] == ["Sulfur"]
    assert "privado.example" not in str(retrato)


def test_mapa_recursos_formata_agenda_real() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "agenda",
        arquivo="memoria/agendamentos.json",
        descricao="agenda real",
        termos=("agenda",),
        leitor=lambda _texto: {
            "agendamentos": [{"nome": "Academia", "quando": "18:30"}],
            "total_ativos": 1,
        },
        escrita_via="comandos de agenda",
    )

    contexto = mapa.contexto_para_prompt("o que tem na minha agenda?")

    assert "Agenda atual: 1 ativo(s); Academia — 18:30." in contexto


def test_mapa_recursos_resolve_consulta_natural_por_dado_confirmado() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "playlists_usuario",
        arquivo="playlists.json",
        descricao="playlists reais",
        termos=("playlist", "musicas salvas"),
        leitor=lambda texto: {
            "playlists": [{"nome": "trap", "total": 5}],
            "detalhe": (
                {"nome": "trap", "titulos": ["Faixa real"]}
                if "trap" in texto.casefold() else {}
            ),
        },
        intent_consulta="PLAYLIST_LIST",
        parametro_detalhe="nome_playlist",
    )

    assert mapa.resolver_consulta("o que tem em trap?") == {
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "trap"},
    }
    assert mapa.resolver_consulta("o que tem em um lugar desconhecido?") is None


def test_mapa_recursos_reconhece_quantas_e_nome_repetido_de_playlist() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "playlists_usuario",
        arquivo="playlists.json",
        descricao="playlists reais",
        termos=("playlist", "musicas salvas"),
        leitor=lambda texto: {
            "detalhe": (
                {"nome": "sendo sendo", "titulos": ["Faixa real"]}
                if "sendo sendo" in texto.casefold() else {}
            ),
        },
        intent_consulta="PLAYLIST_LIST",
        parametro_detalhe="nome_playlist",
    )

    assert mapa.resolver_consulta(
        "quantas musicas tem a playlist sendo sendo"
    ) == {
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "sendo sendo"},
    }


def test_mapa_recursos_prioriza_autoria_sobre_playlist_generica() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "playlists_usuario",
        arquivo="playlists.json",
        descricao="playlists do usuário",
        termos=("playlist", "playlists"),
        leitor=lambda _texto: {"playlists": [{"nome": "anime", "total": 2}]},
        intent_consulta="PLAYLIST_LIST",
    )
    mapa.registrar(
        "playlists_laylay",
        arquivo="playlists_da_laylay.json",
        descricao="curadorias próprias da Laylay",
        termos=(
            "suas playlists", "playlists que voce criou",
            "playlists voce criou",
        ),
        leitor=lambda _texto: {
            "playlists": [{"nome": "xodos_que_eu_separei", "total": 4}],
        },
        intent_consulta="LAYLAY_PLAYLIST_LIST",
    )

    assert mapa.resolver_consulta("quais playlists voce criou?") == {
        "intent": "LAYLAY_PLAYLIST_LIST", "params": {},
    }
    assert mapa.resolver_consulta("quais minhas playlists?") == {
        "intent": "PLAYLIST_LIST", "params": {},
    }
    assert mapa.resolver_consulta(
        "você consegue criar suas próprias playlists?"
    ) is None


def test_mapa_recursos_ancora_nome_real_mesmo_sem_palavra_playlist() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "playlists_usuario",
        arquivo="playlists.json",
        descricao="playlists reais",
        termos=("playlist", "musicas salvas"),
        leitor=lambda texto: {
            "detalhe": (
                {"nome": "trap", "titulos": ["Faixa real"]}
                if "trap" in texto.casefold() else {}
            ),
        },
        intent_consulta="PLAYLIST_LIST",
        parametro_detalhe="nome_playlist",
    )

    contexto = mapa.contexto_para_prompt("o que tem em trap?")

    assert "Detalhe confirmado de trap: Faixa real." in contexto
    assert mapa.contexto_para_prompt("o que você acha de música?") == ""


def test_mapa_recursos_nao_executa_pergunta_sobre_capacidade() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "agenda",
        arquivo="agenda.json",
        descricao="agenda real",
        termos=("agenda", "compromissos"),
        leitor=lambda _texto: {"agendamentos": []},
        intent_consulta="LISTAR_AGENDAMENTOS",
    )

    assert mapa.resolver_consulta("você consegue listar minha agenda?") is None


def test_mapa_recursos_resolve_iot_com_ambiente_e_ancora_dispositivos() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "dispositivos_iot",
        arquivo="sqlite",
        descricao="IoT real",
        termos=("dispositivo", "aparelho", "iot"),
        leitor=lambda _texto: {
            "dispositivos": [
                {
                    "nome": "lampada_quarto",
                    "nome_amigavel": "lâmpada do quarto",
                    "ambiente": "quarto",
                    "capacidades": ["ligar", "desligar", "ajustar_cor"],
                },
                {
                    "nome": "tomada_ventilador",
                    "nome_amigavel": "ventilador",
                    "ambiente": "quarto",
                    "capacidades": ["ligar", "desligar"],
                },
            ],
            "parametros_consulta": {"ambiente": "quarto"},
        },
        intent_consulta="IOT_LIST",
    )

    assert mapa.resolver_consulta("quais dispositivos tem no quarto?") == {
        "intent": "IOT_LIST", "params": {"ambiente": "quarto"},
    }
    prompt = mapa.contexto_para_prompt("quais dispositivos tem no quarto?")
    assert "lâmpada do quarto" in prompt
    assert "ventilador" in prompt
    assert "ajustar_cor" in prompt


def test_mapa_recursos_entende_variacoes_naturais_da_mesma_consulta() -> None:
    mapa = MapaRecursosRuntime()
    chamadas = []
    mapa.registrar(
        "caixa_entrada_pessoal",
        arquivo="memoria/caixa_entrada_pessoal.json",
        descricao="ideias reais",
        termos=("minhas ideias", "ideias salvas", "caixa de entrada"),
        leitor=lambda texto: {
            "notas": [{"tipo": "ideia", "conteudo": "Melhorar o avatar"}],
            "parametros_consulta": {"filtro": texto},
        },
        intent_consulta="INBOX_LIST",
        executor_consulta=lambda resultado, texto: chamadas.append((resultado, texto)) or True,
    )

    for frase in (
        "me fale as minhas ideias",
        "me diga quais ideias estão salvas",
        "quero ver minha caixa de entrada",
        "quais são minhas ideias?",
    ):
        resultado = mapa.resolver_consulta(frase)
        assert resultado is not None
        assert resultado["intent"] == "INBOX_LIST"
        assert mapa.executar_consulta(resultado, frase) is True

    assert len(chamadas) == 4


def test_mapa_recursos_nao_converte_negacao_hipotese_ou_opiniao_em_consulta() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "caixa_entrada_pessoal",
        arquivo="caixa.json",
        descricao="ideias reais",
        termos=("minhas ideias", "ideias salvas"),
        leitor=lambda _texto: {"notas": []},
        intent_consulta="INBOX_LIST",
    )

    assert mapa.resolver_consulta("não me fale as minhas ideias") is None
    assert mapa.resolver_consulta("como eu faria para listar minhas ideias?") is None
    assert mapa.resolver_consulta("o que você acha da minha ideia?") is None


def test_mapa_recursos_formata_notas_sem_metadados_internos() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "caixa_entrada_pessoal",
        arquivo="caixa.json",
        descricao="ideias reais",
        termos=("minhas ideias",),
        leitor=lambda _texto: {
            "notas": [{
                "tipo": "ideia_discutida",
                "conteudo": "Criar skins do avatar",
                "id": "interno-123",
            }],
        },
        intent_consulta="INBOX_LIST",
    )

    contexto = mapa.contexto_para_prompt("me fale as minhas ideias")

    assert "ideia discutida: Criar skins do avatar" in contexto
    assert "interno-123" not in contexto
