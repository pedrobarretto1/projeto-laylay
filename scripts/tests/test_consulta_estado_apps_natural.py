from __future__ import annotations

import pytest

from mente_laylay.autonomia.pre_fluxo_contextual import (
    emitir_conversa_curta,
    processar_consulta_sistema_local,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    registrar_resultado_execucao,
)


def _contexto(
    *,
    apps_validos: set[str] | None = None,
    ultimo_app: str = "",
) -> tuple[dict, list[str], list[str], list[dict]]:
    alvos_resolvidos: list[str] = []
    falas: list[str] = []
    recibos: list[dict] = []
    validos = {item.casefold() for item in (apps_validos or set())}

    def resolver(nome: str) -> dict:
        alvos_resolvidos.append(nome)
        return {
            "programa_aberto": nome.casefold() in validos,
            "programa_em_foco": False,
        }

    contexto = {
        "APPS_MAP": {nome: nome for nome in validos},
        "mente_integrada_estado": {"ultimo_app_janela": ultimo_app},
        "_resolver_alvo_ambiente": resolver,
        "_validar_alvo_app_consulta": (
            lambda nome, estado=None: (
                nome.casefold() in validos
                or bool(dict(estado or {}).get("programa_aberto"))
            )
        ),
        "_emitir_resposta_curta": (
            lambda _texto, fala, **_kwargs: falas.append(fala)
        ),
        "_registrar_resultado_execucao": (
            lambda resultado, *_args, **_kwargs: recibos.append(dict(resultado))
        ),
    }
    return contexto, alvos_resolvidos, falas, recibos


@pytest.mark.parametrize(
    ("texto", "alvo"),
    (
        ("O VLC ainda está aberto?", "vlc"),
        ("O Discord ainda está rodando?", "discord"),
        ("A Ferramenta de Recortes permanece aberta?", "ferramenta de recortes"),
        ("O editor Krita segue aberto?", "editor krita"),
        ("O Notepad++ está em execução?", "notepad++"),
        ("Será que o Opera está aberto?", "opera"),
        ("Por acaso a Calculadora continua aberta?", "calculadora"),
        ("Você pode me dizer se o VLC está aberto?", "vlc"),
        ("Me diz se o Discord está rodando?", "discord"),
        ("Só quero saber se a Microsoft Store está aberta.", "microsoft store"),
        ("Confere para mim se o OBS Studio continua aberto.", "obs studio"),
        ("Dá uma olhada se o Krita ainda está aberto.", "krita"),
        ("opera tá aberto?", "opera"),
        ("calculadora continua aberta", "calculadora"),
    ),
)
def test_consulta_de_app_extrai_alvo_sem_prefacios_ou_marcadores(
    texto: str,
    alvo: str,
) -> None:
    contexto, resolvidos, falas, recibos = _contexto(apps_validos={alvo})

    tratado, rota = processar_consulta_sistema_local(contexto, texto)

    assert (tratado, rota) == (True, "consulta_estado_programa")
    assert resolvidos == [alvo]
    assert falas
    assert recibos[-1]["intent"] == "LIST_WINDOWS"
    assert recibos[-1]["params"]["alvo"] == alvo


@pytest.mark.parametrize(
    "texto",
    (
        "Ele continua aberto?",
        "Ela ainda está aberta?",
        "Confirma se ela continua aberta.",
    ),
)
def test_pronome_de_consulta_usa_ultimo_app_confirmado(texto: str) -> None:
    contexto, resolvidos, _falas, recibos = _contexto(
        apps_validos={"vlc"},
        ultimo_app="vlc",
    )

    tratado, rota = processar_consulta_sistema_local(contexto, texto)

    assert (tratado, rota) == (True, "consulta_estado_programa")
    assert resolvidos == ["vlc"]
    assert recibos[-1]["params"]["alvo"] == "vlc"


@pytest.mark.parametrize(
    "texto",
    (
        "A porta está aberta?",
        "A inscrição continua aberta?",
        "Meu chamado ainda está aberto?",
        "O arquivo relatório está aberto?",
        "A aba da documentação está aberta?",
        "O menu do jogo está aberto?",
    ),
)
def test_substantivo_fora_do_catalogo_nao_vira_consulta_de_app(texto: str) -> None:
    contexto, _resolvidos, falas, recibos = _contexto(apps_validos={"opera"})

    assert processar_consulta_sistema_local(contexto, texto) == (False, "")
    assert falas == []
    assert recibos == []


@pytest.mark.parametrize(
    "texto",
    (
        '"O Opera está aberto?"',
        "O Opera está aberto.",
        "Eu deixei o Opera aberto.",
        "Não quero saber se o Opera está aberto.",
        "Nem precisa verificar se o Opera está aberto.",
        "Como eu perguntaria se o Opera está aberto?",
        'A frase "o Opera está aberto?" é apenas um exemplo.',
        'Se eu disser "o Opera está aberto?", isso é uma consulta.',
    ),
)
def test_citacao_afirmacao_negacao_e_metalinguagem_nao_consultam_app(
    texto: str,
) -> None:
    contexto, resolvidos, falas, recibos = _contexto(apps_validos={"opera"})

    assert processar_consulta_sistema_local(contexto, texto) == (False, "")
    assert resolvidos == []
    assert falas == []
    assert recibos == []


@pytest.mark.parametrize(
    "texto",
    (
        "Quais programas estão abertos?",
        "Quais aplicativos estão rodando?",
        "Lista as janelas abertas.",
        "Mostra os apps em execução.",
        "Que processos estão rodando?",
        "Pode listar os programas abertos?",
        "Eu queria saber quais janelas estão abertas.",
        "Quantos programas estão abertos?",
        "Tem alguma janela aberta?",
        "O que está aberto no computador?",
        "Mostra só os aplicativos com janela visível.",
        "Quais programas continuam abertos agora?",
    ),
)
def test_inventario_natural_publica_retrato_readonly(texto: str) -> None:
    falas: list[str] = []
    recibos: list[dict] = []
    contexto = {
        "observar_programas_abertos": lambda: {
            "janelas_visiveis": ["Opera", "Calculadora"],
            "processos_segundo_plano": ["Spotify"],
        },
        "_emitir_resposta_curta": (
            lambda _texto, fala, **_kwargs: falas.append(fala)
        ),
        "_registrar_resultado_execucao": (
            lambda resultado, *_args, **_kwargs: recibos.append(dict(resultado))
        ),
    }

    tratado, rota = processar_consulta_sistema_local(contexto, texto)

    assert (tratado, rota) == (True, "consulta_programas_abertos")
    assert falas and "Opera" in falas[-1]
    assert recibos[-1]["intent"] == "LIST_WINDOWS"
    assert recibos[-1]["status"] == "janelas_listadas"


@pytest.mark.parametrize(
    "texto",
    (
        "Você consegue verificar programas abertos?",
        "Não liste os programas abertos.",
        "A frase 'quais programas estão abertos?' é um exemplo.",
    ),
)
def test_capacidade_negacao_e_citacao_nao_disparam_inventario(texto: str) -> None:
    observacoes: list[bool] = []
    contexto = {
        "observar_programas_abertos": (
            lambda: observacoes.append(True) or {"janelas_visiveis": []}
        ),
    }

    assert processar_consulta_sistema_local(contexto, texto) == (False, "")
    assert observacoes == []


def test_receipt_confirmado_de_leitura_direcionada_publica_referente_app() -> None:
    estado = registrar_resultado_execucao(
        {},
        resultado={
            "intent": "LIST_WINDOWS",
            "params": {"alvo": "vlc"},
            "status": "estado_app_consultado",
            "executou": True,
            "confirmado": True,
        },
        texto="O VLC está aberto?",
        executou=True,
        origem="consulta_sistema_local",
        status="estado_app_consultado",
    )

    assert estado["ultimo_app_janela"] == "vlc"
    assert estado["ultimo_alvo"] == "vlc"


@pytest.mark.parametrize(
    "texto",
    (
        "O Visual Studio Code continua aberto?",
        "Quais programas estão abertos?",
    ),
)
def test_leitura_local_publica_receipt_antes_da_fala(texto: str) -> None:
    eventos: list[str] = []
    contexto = {
        "APPS_MAP": {"visual studio code": "Code.exe"},
        "mente_integrada_estado": {},
        "_resolver_alvo_ambiente": lambda _nome: {
            "programa_aberto": True,
            "programa_em_foco": False,
        },
        "_validar_alvo_app_consulta": lambda *_args, **_kwargs: True,
        "observar_programas_abertos": lambda: {
            "janelas_visiveis": ["Visual Studio Code"],
            "processos_segundo_plano": [],
        },
        "_registrar_resultado_execucao": (
            lambda *_args, **_kwargs: eventos.append("receipt")
        ),
        "_emitir_resposta_curta": (
            lambda *_args, **_kwargs: eventos.append("fala")
        ),
    }

    tratado, _rota = processar_consulta_sistema_local(contexto, texto)

    assert tratado is True
    assert eventos == ["receipt", "fala"]


def test_emissao_curta_nao_declara_tratado_quando_porta_de_fala_rejeita() -> None:
    contexto = {
        "_emitir_resposta_curta": lambda *_args, **_kwargs: False,
    }

    assert emitir_conversa_curta(
        contexto,
        "O Opera está aberto?",
        "Opera não está entre os programas abertos agora.",
        emocao="calma",
        nivel=1,
    ) is False


def test_inventario_plural_ou_leitura_nao_confirmada_nao_inventam_referente() -> None:
    inicial = {"ultimo_app_janela": "opera"}
    inventario = registrar_resultado_execucao(
        inicial,
        resultado={
            "intent": "LIST_WINDOWS",
            "params": {"alvo": "janelas visiveis"},
            "status": "janelas_listadas",
            "executou": True,
            "confirmado": True,
        },
        texto="Quais programas estão abertos?",
        executou=True,
        status="janelas_listadas",
    )
    falha = registrar_resultado_execucao(
        {},
        resultado={
            "intent": "LIST_WINDOWS",
            "params": {"alvo": "vlc"},
            "status": "falhou",
            "executou": False,
            "confirmado": False,
        },
        texto="O VLC está aberto?",
        executou=False,
        status="falhou",
    )

    assert inventario["ultimo_app_janela"] == "opera"
    assert "ultimo_app_janela" not in falha
