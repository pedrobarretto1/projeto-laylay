"""Contrato de correspondência de alvo; não treina nem consulta o desktop real.

Migrado do diagnóstico opt-in após confirmar os seis REDs históricos.
Os componentes de resolução, catálogo e pré-fluxo são reais; apenas as entradas
de observação e as saídas de voz/receipt são controladas.
"""

from __future__ import annotations

import pytest

from mente_laylay.autonomia.pre_fluxo_contextual import processar_consulta_sistema_local
from mente_laylay.integracao.ambiente_navegacao import AmbienteNavegacaoRuntime
from mente_laylay.integracao.catalogo_aplicativos import CatalogoAplicativosRuntime
from mente_laylay.percepcao.janelas_sistema import resolver_alvo_ambiente
from mente_laylay.percepcao.planejamento_janelas import normalizar_alvo_ambiente


CASOS = [
    ("Excel", "planilha do Excel", "A planilha do Excel ainda está aberta?"),
    ("Word", "documento do Word", "O documento do Word está aberto?"),
    ("VLC", "vídeo do VLC", "O vídeo do VLC está aberto?"),
]


def _compor(titulos: list[str], app: str) -> tuple[dict, list, list]:
    ambiente = AmbienteNavegacaoRuntime(servicos_iniciais={
        "gw": None, "psutil": None,
        "_listar_programas_abertos_mente": lambda *_: list(titulos),
        "_normalizar_alvo_ambiente": normalizar_alvo_ambiente,
        "_resolver_alvo_ambiente_mente": resolver_alvo_ambiente,
        "_janela_app_esta_em_foco": lambda _: False,
    })
    catalogo = CatalogoAplicativosRuntime(apps_map={app: f"{app}.exe"})
    falas, recibos = [], []
    return {
        "_resolver_alvo_ambiente": ambiente.resolver_alvo,
        "_validar_alvo_app_consulta": catalogo.validar,
        "_emitir_resposta_curta": lambda _texto, fala, **_: falas.append(fala),
        "_registrar_resultado_execucao": lambda resultado, *a, **kw: recibos.append(resultado),
    }, falas, recibos


@pytest.mark.parametrize("app,alvo,texto", CASOS)
def test_titulo_do_app_nao_prova_conteudo_especifico(app, alvo, texto):
    estado = resolver_alvo_ambiente(alvo, [app], [])
    assert estado["programa_aberto"] is False, (
        "RED primeira fronteira: nome do aplicativo foi promovido a prova do conteúdo"
    )


@pytest.mark.parametrize("app,alvo,texto", CASOS)
def test_consulta_nao_publica_receipt_de_conteudo_sem_evidencia(app, alvo, texto):
    contexto, falas, recibos = _compor([app], app)
    processar_consulta_sistema_local(contexto, texto)
    assert not any(r.get("confirmado") for r in recibos), (
        "RED consequência: receipt confirmado sem observar o conteúdo solicitado"
    )
    assert not any("está aberto" in fala or "está aberta" in fala for fala in falas)


@pytest.mark.parametrize("app,alvo,texto", CASOS)
def test_controle_app_explicito_continua_consultavel(app, alvo, texto):
    contexto, falas, recibos = _compor([app], app)
    assert processar_consulta_sistema_local(contexto, f"O {app} está aberto?")[0]
    assert recibos[-1]["confirmado"] is True
    assert falas


@pytest.mark.parametrize("app,alvo,texto", CASOS)
def test_controle_sem_correspondencia_nao_confirma_conteudo(app, alvo, texto):
    contexto, falas, recibos = _compor(["Aplicativo independente"], app)
    assert processar_consulta_sistema_local(contexto, texto) == (False, "")
    assert falas == recibos == []


@pytest.mark.parametrize("app,alvo,texto", CASOS)
def test_controle_qualificador_de_janela_nao_deve_ser_perdido(app, alvo, texto):
    contexto, falas, recibos = _compor([app], app)
    assert processar_consulta_sistema_local(contexto, f"A janela do {app} está aberta?")[0]
    assert recibos[-1]["confirmado"] is True
    assert falas


@pytest.mark.parametrize("alvo,titulo", [
    ("editor Krita", "Krita"), ("cliente Steam", "Steam"),
    ("navegador Opera", "Opera GX"), ("janela do vscode", "Visual Studio Code"),
    ("Word", "Relatório - Word"), ("Excel", "Planilha1 - Excel"),
    ("VLC", "filme.mp4 - VLC media player"),
])
def test_qualificadores_aliases_e_titulos_completos_preservados(alvo, titulo):
    assert resolver_alvo_ambiente(alvo, [titulo], [])["programa_aberto"] is True


@pytest.mark.parametrize("alvo,titulo", [
    ("Word", "Crossword"), ("app Word", "Crossword"),
    ("relatório financeiro", "Relatório"),
    ("documento do Word", "Word"), ("janela do editor de vídeo", "Editor"),
])
def test_correspondencia_nao_descarta_partes_semanticas_ou_limites_de_palavra(alvo, titulo):
    assert resolver_alvo_ambiente(alvo, [titulo], [])["programa_aberto"] is False


@pytest.mark.parametrize("alvo", ["Steam", "cliente Steam", "janela do Steam"])
def test_qualificador_nao_promove_processo_auxiliar_a_janela(alvo):
    estado = resolver_alvo_ambiente(alvo, ["SteamService.exe", "SteamWebHelper.exe"], [])
    assert estado["programa_aberto"] is False
