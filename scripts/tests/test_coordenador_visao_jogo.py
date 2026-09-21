from __future__ import annotations

from mente_laylay.percepcao.visao_jogo.coordenador import (
    CoordenadorVisaoJogoRuntime,
)


class _MemoriaFake:
    def listar_recentes(self, identidade, limite=5):
        return [{"jogo": identidade.get("chave"), "limite": limite}]


class _ObservadorFake:
    def __init__(self):
        self.armados = []
        self.desarmados = []

    def armar(self, **kwargs):
        self.armados.append(kwargs)

    def desarmar(self, motivo):
        self.desarmados.append(motivo)


class _DiretorFake:
    def __init__(self, status="proposta_cognitiva"):
        self.status = status
        self.eventos = []

    def considerar(self, evento):
        self.eventos.append(evento)
        return {
            "status": self.status,
            "proposta_comunicativa": {
                "agendada": True,
                "autoriza_execucao": False,
            },
        }


def _montar(*, diretor=None):
    estado = {"pendencia_atual": {}}
    observador = _ObservadorFake()
    registros, falas, curtas, salvos = [], [], [], []

    def registrar_pendencia(mente, pendencia):
        novo = dict(mente)
        novo["pendencia_atual"] = dict(pendencia)
        return novo

    def limpar_pendencia(mente, **_kwargs):
        novo = dict(mente)
        novo["pendencia_atual"] = {}
        return novo

    runtime = CoordenadorVisaoJogoRuntime(
        memoria_jogos=_MemoriaFake(),
        observador_inventario_getter=lambda: observador,
        diretor_presenca_getter=lambda: diretor,
        recomendar_playlist=lambda clima: f"Playlist real para {clima}.",
        registrar_oportunidade=lambda evento: registros.append(evento) or {"status": "aceita"},
        decisao_permite_emissao=lambda decisao: decisao.get("status") == "aceita",
        agendar_fala=lambda *args, **kwargs: falas.append((args, kwargs)) or True,
        registrar_mente_curta=lambda *args, **kwargs: curtas.append((args, kwargs)),
        estado_mental_getter=lambda: estado,
        estado_mental_substituir=lambda novo: estado.update(novo),
        criar_pendencia=lambda **kwargs: dict(kwargs),
        registrar_pendencia=registrar_pendencia,
        pendencia_ativa=lambda mente, **_kwargs: mente.get("pendencia_atual"),
        limpar_pendencia=limpar_pendencia,
        salvar_memoria=lambda: salvos.append(True),
        clock=lambda: 1234.5,
    )
    return runtime, {
        "estado": estado,
        "observador": observador,
        "registros": registros,
        "falas": falas,
        "curtas": curtas,
        "salvos": salvos,
    }


def test_coordenador_envia_sugestao_fundamentada_ao_diretor_de_presenca() -> None:
    diretor = _DiretorFake()
    runtime, dados = _montar(diretor=diretor)

    assert runtime.processar_sugestao_proativa(
        {
            "relevante": True,
            "fala": "Essa bota melhora sua defesa.",
            "confianca": 0.88,
            "categoria": "dica",
            "item": "Bota da Tempestade",
            "slot": "botas",
            "motivo": "mais resistência",
        },
        {"chave": "poe2"},
        {"classe": "monge"},
    ) is True

    evento = diretor.eventos[0]
    assert evento["dominio"] == "jogo"
    assert evento["fundamentada"] is True
    assert len(evento["evidencias"]) == 3
    assert dados["falas"] == []


def test_coordenador_usa_iniciativa_quando_diretor_ainda_nao_existe() -> None:
    runtime, dados = _montar(diretor=None)

    assert runtime.processar_sugestao_proativa(
        {
            "relevante": True,
            "fala": "Tem uma melhoria interessante aqui.",
            "confianca": 0.8,
            "item": "Cajado",
            "slot": "arma",
        },
        {"chave": "poe2"},
        {"classe": "monge", "build": "gelo"},
    ) is True

    assert dados["registros"][0]["objetivo"] == "melhorar_build_atual"
    assert dados["falas"][0][0][:2] == (
        "visao_jogo", "Tem uma melhoria interessante aqui.",
    )
    assert dados["falas"][0][1]["mesclar_turno"] is True


def test_coordenador_arma_e_desarma_observacao_do_inventario() -> None:
    runtime, dados = _montar()
    runtime.ao_mapear_inventario(
        {"chave": "poe2"},
        {"tela_inventario_ativa": True, "confianca": 0.9},
        "imagem-atual",
        False,
    )
    runtime.ao_mapear_inventario(
        {"chave": "poe2"},
        {"tela_inventario_ativa": False},
        "",
        True,
    )

    assert dados["observador"].armados == [{
        "jogo_chave": "poe2", "imagem": "imagem-atual",
    }]
    assert dados["observador"].desarmados == ["inventário fechado"]


def test_coordenador_registra_contexto_e_pendencia_na_mesma_mente() -> None:
    runtime, dados = _montar()
    runtime.registrar_analise({
        "identidade": {"chave": "poe2", "nome_candidato": "Path of Exile 2"},
        "perfil": {"classe": "monge", "nivel": 12},
        "pergunta": "Essa bota é boa?",
        "resposta": "Ela ajuda sua resistência elétrica.",
        "solicita_complemento": True,
    })

    contexto = dados["estado"]["contexto_jogo_atual"]
    assert contexto["chave"] == "poe2"
    assert contexto["perfil"]["nivel"] == 12
    assert contexto["memorias_recentes"][0]["jogo"] == "poe2"
    assert contexto["ts"] == 1234.5
    assert dados["estado"]["pendencia_atual"]["origem"] == "visao_jogo"
    assert dados["curtas"][0][1]["habilidade"] == "visao_jogo"
    assert dados["salvos"] == [True]
