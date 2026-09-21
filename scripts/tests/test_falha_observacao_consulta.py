"""Falha de leitura não é prova de ausência; componentes reais, I/O controlado."""
from types import SimpleNamespace

import pytest

from mente_laylay.percepcao.janelas_sistema import observar_programas_abertos, listar_programas_abertos, resolver_alvo_ambiente
from mente_laylay.percepcao.planejamento_janelas import normalizar_alvo_ambiente
from mente_laylay.integracao.ambiente_navegacao import AmbienteNavegacaoRuntime
from mente_laylay.integracao.catalogo_aplicativos import CatalogoAplicativosRuntime
from mente_laylay.autonomia.pre_fluxo_contextual import processar_consulta_sistema_local
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_resultado_execucao
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime


def _falhar(*args):
    raise RuntimeError("leitura indisponível")


def _ambiente(falha_janelas=False, falha_processos=False):
    gw = SimpleNamespace(getAllWindows=_falhar if falha_janelas else lambda: [])
    ps = SimpleNamespace(process_iter=_falhar if falha_processos else lambda _: [],
                         NoSuchProcess=LookupError, AccessDenied=PermissionError)
    return AmbienteNavegacaoRuntime(servicos_iniciais={
        "gw": gw, "psutil": ps,
        "_listar_programas_abertos_mente": listar_programas_abertos,
        "_observar_programas_abertos_mente": observar_programas_abertos,
        "_normalizar_alvo_ambiente": normalizar_alvo_ambiente,
        "_resolver_alvo_ambiente_mente": resolver_alvo_ambiente,
        "_janela_app_esta_em_foco": lambda _: False,
    }), gw, ps


def test_observador_preserva_falha_na_primeira_fronteira():
    _, gw, ps = _ambiente(falha_janelas=True)
    assert observar_programas_abertos(gw, ps)["janelas_observadas"] is False
    with pytest.raises(RuntimeError):
        listar_programas_abertos(gw, ps)


def test_fachada_nao_converte_falha_em_estado_ausente():
    a, _, _ = _ambiente(falha_janelas=True)
    with pytest.raises(RuntimeError):
        a.resolver_alvo("Excel")


@pytest.mark.parametrize("texto", ["O Excel está aberto?", "Quais programas estão abertos?"])
@pytest.mark.parametrize("falha", [True, False])
def test_caminho_real_distingue_falha_de_observacao_vazia(texto, falha):
    a, _, _ = _ambiente(falha_janelas=falha)
    eventos, recibos, falas = [], [], []
    mente = {"ultimo_app_janela": "opera"}
    def registrar(r, t, executou, **kw):
        nonlocal mente
        eventos.append("receipt")
        recibos.append(r)
        mente = registrar_resultado_execucao(mente, resultado=r, texto=t, executou=executou, **kw)
    def falar(t, f, **kw):
        eventos.append("fala")
        falas.append(f)
    c = CatalogoAplicativosRuntime(apps_map={"excel": "excel.exe"})
    ctx = {"_resolver_alvo_ambiente": a.resolver_alvo,
           "_validar_alvo_app_consulta": c.validar,
           "observar_programas_abertos": a.observar_programas,
           "_registrar_resultado_execucao": registrar, "_emitir_resposta_curta": falar}
    tratado, _ = processar_consulta_sistema_local(ctx, texto)
    assert recibos[-1]["confirmado"] is (not falha)
    assert tratado is True
    assert eventos == ["receipt", "fala"]
    if falha:
        assert recibos[-1]["status"] == "falha_observacao"
        assert mente["ultimo_app_janela"] == "opera"
        assert "não consegui" in falas[-1].casefold()


def test_inventario_parcial_nao_confirma_leitura_completa():
    a, _, _ = _ambiente(falha_processos=True)
    recibos, falas = [], []
    ctx = {"observar_programas_abertos": a.observar_programas,
           "_registrar_resultado_execucao": lambda r, *args, **kw: recibos.append(r),
           "_emitir_resposta_curta": lambda t, f, **kw: falas.append(f)}
    assert processar_consulta_sistema_local(ctx, "Quais programas estão abertos?")[0]
    assert recibos[-1]["confirmado"] is False
    assert falas


@pytest.mark.parametrize("voz_aceita", [True, False])
def test_cadeia_para_antes_do_proximo_comando_quando_consulta_falha(voz_aceita):
    a, _, _ = _ambiente(falha_janelas=True)
    recibos, falas, tentativas = [], [], []
    contexto = {
        "turno_atual": {"id": "leitura-falha", "autoriza_execucao": True},
        "_resolver_alvo_ambiente": a.resolver_alvo,
        "_validar_alvo_app_consulta": CatalogoAplicativosRuntime(apps_map={"excel": "excel.exe"}).validar,
        "_registrar_resultado_execucao": lambda r, *args, **kw: recibos.append(r),
        "_emitir_resposta_curta": lambda t, f, **kw: (falas.append(f), voz_aceita)[1],
    }
    ciclo = CicloComandosRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_com_apelidos": str.casefold,
            "detectar_intencao_deterministica": lambda t: tentativas.append(t),
        },
        contexto_intencao_runtime=SimpleNamespace(montar=lambda: dict(contexto)),
        log=lambda *args: None,
    )
    assert ciclo.processar_cadeia("confira se o Excel está aberto e depois abra o Paint")
    assert recibos and recibos[0]["confirmado"] is False
    assert tentativas == [], "falha comunicada não pode liberar a próxima etapa"


@pytest.mark.parametrize("estado", [{}, None, {"programa_aberto": "false"}])
def test_resposta_invalida_do_observador_nao_e_ausencia(estado):
    recibos = []
    ctx = {"_resolver_alvo_ambiente": lambda _: estado,
           "_validar_alvo_app_consulta": CatalogoAplicativosRuntime(apps_map={"excel": "excel.exe"}).validar,
           "_registrar_resultado_execucao": lambda r, *args, **kw: recibos.append(r),
           "_emitir_resposta_curta": lambda *args, **kw: True}
    assert processar_consulta_sistema_local(ctx, "O Excel está aberto?") == (True, "falha_observacao")
    assert recibos[-1]["confirmado"] is False


def test_falha_de_processos_nao_invalida_observacao_independente_de_janelas():
    a, _, _ = _ambiente(falha_processos=True)
    assert a.resolver_alvo("Excel")["programa_aberto"] is False
