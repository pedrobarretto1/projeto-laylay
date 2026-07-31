from __future__ import annotations

from mente_laylay.pesquisa_jogos.contratos import (
    extrair_item_da_resposta_visual,
    planejar_pesquisa_item,
)
from mente_laylay.pesquisa_jogos.poe2 import FontePoe2Wiki, MAXROLL_POE2
from mente_laylay.pesquisa_jogos.runtime import PesquisaJogosRuntime
from mente_laylay.percepcao.visao_jogo.presenca_visual import extrair_presenca_visual


class _Resposta:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def _identidade_poe2():
    return {
        "chave": "path-of-exile-2:poe2.exe",
        "nome_candidato": "Path of Exile 2",
        "titulo": "Path of Exile 2",
        "processo": "PathOfExileSteam.exe",
    }


def _item():
    return {
        "nome": "Tempest March", "base": "Embossed Boots",
        "categoria": "Boots", "raridade": "Rare", "nivel_item": 18,
        "atributos": ["15% increased Movement Speed", "+12% Fire Resistance"],
        "termos_pesquisa": ["Embossed Boots", "Boots"], "confianca": 0.88,
    }


def test_contrato_remove_json_tecnico_da_fala() -> None:
    fala, item = extrair_item_da_resposta_visual(
        'Essas botas têm velocidade e resistência.\n'
        'DADOS_ITEM_JSON: {"nome":"Tempest March","base":"Embossed Boots",'
        '"categoria":"Boots","atributos":["15% speed"],'
        '"termos_pesquisa":["Embossed Boots"],"confianca":0.88}'
    )
    assert fala == "Essas botas têm velocidade e resistência."
    assert item["base"] == "Embossed Boots"
    assert item["confianca"] == 0.88


def test_contrato_nao_fala_json_visual_truncado_ou_multilinha() -> None:
    fala_truncada, item_truncado = extrair_item_da_resposta_visual(
        'Essas botas ajudam na evasão. DADOS_ITEM_JSON: {"nome":"Passos", "atributos":'
    )
    fala_multilinha, item_multilinha = extrair_item_da_resposta_visual(
        'É uma bota defensiva.\nDADOS_ITEM_JSON: {\n'
        '  "nome": "Passos",\n  "categoria": "botas",\n  "confianca": 0.9\n}'
    )

    assert fala_truncada == "Essas botas ajudam na evasão."
    assert item_truncado == {}
    assert fala_multilinha == "É uma bota defensiva."
    assert item_multilinha["nome"] == "Passos"


def test_presenca_visual_descarta_oracao_cortada_em_conector() -> None:
    _fala, evento = extrair_presenca_visual(
        'Observação ambiental.\nPRESENCA_JOGO_JSON: '
        '{"relevante":true,"categoria":"companhia",'
        '"fala":"Vejo que você e.","motivo":"menu aberto",'
        '"evidencias":["menu aberto"],"confianca":0.9,'
        '"momento_seguro":true,"clima_musical":"calmo"}'
    )

    assert evento["relevante"] is False
    assert evento["categoria"] == "nenhuma"
    assert evento["fala"] == ""


def test_fonte_wiki_prefere_titulo_exato_e_guarda_procedencia() -> None:
    chamadas = []

    def get(_url, *, params, **_kwargs):
        chamadas.append(dict(params))
        return _Resposta({"query": {"pages": {"42": {
            "pageid": 42, "title": "Embossed Boots",
            "extract": "Embossed Boots is a boots base item with evasion.",
            "fullurl": "https://www.poe2wiki.net/wiki/Embossed_Boots",
        }}}})

    fonte = FontePoe2Wiki(requests_get=get)
    resultado = fonte.consultar("Embossed Boots")
    assert resultado["fonte"] == "poe2wiki"
    assert resultado["titulo"] == "Embossed Boots"
    assert resultado["url"].endswith("Embossed_Boots")
    assert chamadas[0]["titles"] == "Embossed Boots"


def test_pesquisa_paralela_usa_threads_daemon_que_nao_prendem_encerramento() -> None:
    criadas = []

    class ThreadImediata:
        def __init__(self, *, target, name, daemon):
            self.target = target
            self.name = name
            self.daemon = daemon
            criadas.append(self)

        def start(self):
            self.target()

        def join(self, timeout=None):
            return None

    fonte = FontePoe2Wiki(thread_factory=ThreadImediata)
    fonte.consultar = lambda termo: {
        "fonte": "poe2wiki", "titulo": termo,
        "url": f"https://exemplo/{termo}", "resumo": "dados", "confianca": 0.8,
    }
    resultados = fonte.pesquisar({
        "termos_pesquisa": ["Embossed Boots", "Boots"], "categoria": "Boots",
    })

    assert len(resultados) == 2
    assert criadas
    assert all(thread.daemon is True for thread in criadas)
    assert all(thread.name.startswith("Laylay-Pesquisa-PoE2-") for thread in criadas)


def test_pesquisa_poe2_usa_cache_persistente_e_nao_coleta_maxroll(tmp_path) -> None:
    class Fonte:
        def __init__(self):
            self.chamadas = 0

        def pesquisar(self, _item):
            self.chamadas += 1
            return [{
                "fonte": "poe2wiki", "titulo": "Embossed Boots",
                "url": "https://www.poe2wiki.net/wiki/Embossed_Boots",
                "resumo": "Base de botas com evasão.", "confianca": 0.9,
            }]

    fonte = Fonte()
    db = str(tmp_path / "mente.sqlite")
    runtime = PesquisaJogosRuntime(db_path=db, fonte_poe2=fonte, log=lambda *_: None)
    primeiro = runtime.pesquisar_item(_item(), {"identidade": _identidade_poe2()})
    segundo = runtime.pesquisar_item(_item(), {"identidade": _identidade_poe2()})
    reaberto = PesquisaJogosRuntime(db_path=db, fonte_poe2=fonte, log=lambda *_: None)
    terceiro = reaberto.pesquisar_item(_item(), {"identidade": _identidade_poe2()})

    assert primeiro["ok"] is True
    assert primeiro["cache"] is False
    assert primeiro["fonte_editorial_manual"]["url"] == MAXROLL_POE2
    assert "bloqueado" in primeiro["fonte_editorial_manual"]["motivo"]
    assert segundo["cache"] is True
    assert terceiro["cache"] is True
    assert fonte.chamadas == 1


def test_pesquisa_recusa_item_lido_com_baixa_confianca() -> None:
    class Fonte:
        def pesquisar(self, _item):
            raise AssertionError("não deveria pesquisar")

    runtime = PesquisaJogosRuntime(fonte_poe2=Fonte(), log=lambda *_: None)
    resultado = runtime.pesquisar_item(
        {**_item(), "confianca": 0.3}, {"identidade": _identidade_poe2()},
    )
    assert resultado == {
        "ok": False, "motivo": "leitura_visual_incerta", "fontes": [],
    }


def test_item_raro_pesquisa_base_e_mecanicas_sem_nome_procedural() -> None:
    plano = planejar_pesquisa_item(_item())
    consultas = {(item["tipo"], item["termo"]) for item in plano["consultas"]}
    assert plano["estrategia"] == "base_e_modificadores"
    assert plano["nome_procedural_ignorado"] is True
    assert ("base", "Embossed Boots") in consultas
    assert ("mecanica", "Movement Speed") in consultas
    assert ("mecanica", "Fire Resistance") in consultas
    assert all(item["termo"] != "Tempest March" for item in plano["consultas"])


def test_item_unico_pesquisa_nome_exato_antes_da_base() -> None:
    plano = planejar_pesquisa_item({
        **_item(), "nome": "Wanderlust", "raridade": "Unique",
    })
    assert plano["estrategia"] == "item_unico"
    assert plano["consultas"][0] == {
        "termo": "Wanderlust", "tipo": "nome_unico", "prioridade": 100,
    }


def test_base_traduzida_preserva_alias_ingles_sem_reabilitar_nome_raro() -> None:
    plano = planejar_pesquisa_item({
        **_item(),
        "nome": "Marcha da Tempestade",
        "base": "Botas em Relevo",
        "termos_pesquisa": ["Embossed Boots", "Marcha da Tempestade"],
    })
    consultas = {(item["tipo"], item["termo"]) for item in plano["consultas"]}
    assert ("alias_visual", "Embossed Boots") in consultas
    assert all(item["termo"] != "Marcha da Tempestade" for item in plano["consultas"])


def test_cache_de_raro_e_reutilizado_quando_apenas_numeros_mudam(tmp_path) -> None:
    class Fonte:
        def __init__(self):
            self.chamadas = 0

        def pesquisar(self, item):
            self.chamadas += 1
            assert all(
                consulta["termo"] != "Tempest March"
                for consulta in item["consultas_pesquisa"]
            )
            return [{
                "fonte": "poe2wiki", "titulo": "Embossed Boots",
                "url": "https://www.poe2wiki.net/wiki/Embossed_Boots",
                "resumo": "Base de botas.", "confianca": 0.9,
                "correspondencia": 100, "tipo_evidencia": "base",
            }]

    fonte = Fonte()
    runtime = PesquisaJogosRuntime(
        db_path=str(tmp_path / "mente.sqlite"), fonte_poe2=fonte,
        log=lambda *_: None,
    )
    primeiro = runtime.pesquisar_item(_item(), {"identidade": _identidade_poe2()})
    segundo = runtime.pesquisar_item({
        **_item(),
        "atributos": ["18% increased Movement Speed", "+20% Fire Resistance"],
    }, {"identidade": _identidade_poe2()})
    assert primeiro["ok"] is True
    assert segundo["cache"] is True
    assert fonte.chamadas == 1


def test_falha_do_cache_de_pesquisa_chega_a_observabilidade(tmp_path) -> None:
    falhas = []

    PesquisaJogosRuntime(
        db_path=str(tmp_path),
        log=lambda *_: None,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
    )

    assert falhas
    assert falhas[0][0] == ("pesquisa_jogos", "cache_inicializacao")
    assert isinstance(falhas[0][1]["erro"], Exception)
