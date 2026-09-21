import ast
import os
from pathlib import Path

import pytest

from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
from mente_laylay.neural.coleta_entradas import ColetaEntradasNeurais
from mente_laylay.cognicao import composicao_turno
from mente_laylay.integracao.registro_servicos_aplicacao import RegistroServicosAplicacaoRuntime
from tests.test_r1_hs1_fluxo_real_repeticao_tipificada import _HarnessHS1


def compor(tmp_path, **kwargs):
    h = _HarnessHS1()
    coletor = ColetaEntradasNeurais(tmp_path / "entradas.jsonl", estado=h.estado,
        conversa_getter=lambda: "chat-teste", teste_getter=lambda: True, ativo=True, **kwargs)
    servicos = h.turnos._snapshot()
    servicos["_coleta_entradas_neurais"] = coletor
    return h, coletor, ComposicaoTurnoRuntime(servicos=servicos)


def ler(c):
    return c.buffer.listar()


def test_composicao_canonica_coleta_recusa_sem_modelo_nem_executor(tmp_path):
    h, c, runtime = compor(tmp_path)
    turno = runtime.iniciar("Não abra a Microsoft Store.", origem="roteiro_teste")
    assert turno["autoriza_execucao"] is False
    assert len(ler(c)) == 1, "entrada canônica deve alcançar coleta mesmo sem modelo/execução"
    r = ler(c)[0]
    assert r["turno_id"] == turno["id"]
    assert r["origem_declarada"] == "roteiro_teste"
    assert r["teste_declarado"] is True
    assert r["anotacao"] is r["particao"] is None
    assert r["autoriza_execucao"] is r["apto_treino"] is False


def test_preserva_original_revisado_e_contexto_antes_do_turno(tmp_path):
    h, c, runtime = compor(tmp_path)
    h.estado.atualizar_campos("mental", sessao_conversa_ts=123.5, turno_atual={"id": 91})
    texto = "Abre Wikipédia... não, melhor Prime Video."
    turno = runtime.iniciar(texto, origem="terminal")
    assert turno["revisao_intra_turno"]["detectada"] is True
    assert len(ler(c)) == 1
    r = ler(c)[0]
    assert r["entrada"]["texto"] == texto
    assert r["contexto_anterior"]["turno_id"] == 91
    assert r["conversa_id"] == "chat-teste" and r["sessao_conversa_ts"] == 123.5


def test_evento_presenca_nao_entra_como_utterance(tmp_path):
    _, c, runtime = compor(tmp_path)
    turno = runtime.iniciar({"natureza": "evento", "tipo": "observacao", "origem": "visao",
        "evidencia": {"texto_detectado": "abre o aplicativo"},
        "autoridade_usuario": False, "permissao_execucao": False}, origem="presenca")
    assert turno["autoriza_execucao"] is False and ler(c) == []


def test_falha_coleta_nao_altera_planejamento(tmp_path):
    _, c, runtime = compor(tmp_path, limite_bytes=1)
    turno = runtime.iniciar("Não abra a Microsoft Store.", origem="terminal")
    assert turno["autoriza_execucao"] is False
    assert ler(c) == []


@pytest.mark.parametrize("texto", ["Ontem pedi para abrir o Opera.", "Não leia o arquivo.", "oi"])
def test_coleta_nao_seleciona_apenas_comandos(tmp_path, texto):
    _, c, runtime = compor(tmp_path)
    runtime.iniciar(texto, origem="terminal")
    assert ler(c)[0]["entrada"]["texto"] == texto


def test_falha_planejamento_preservada_e_registrada_sem_id_inventado(tmp_path, monkeypatch):
    _, c, runtime = compor(tmp_path)
    def falhar(*a, **k): raise ValueError("erro privado")
    monkeypatch.setattr(composicao_turno, "iniciar_planejamento_turno", falhar)
    with pytest.raises(ValueError, match="erro privado"):
        runtime.iniciar("entrada", origem="terminal")
    r = ler(c)[0]
    assert r["planejamento"] == "falhou" and r["turno_id"] is None
    assert r["erro_tipo"] == "ValueError" and "erro privado" not in str(r)


def test_falha_getter_nao_impede_turno(tmp_path):
    _, c, runtime = compor(tmp_path)
    def falhar(): raise RuntimeError("privado")
    c.conversa_getter = falhar
    assert runtime.iniciar("Não abra o Opera", origem="terminal")["autoriza_execucao"] is False
    assert ler(c) == []


def test_mesmo_texto_em_turnos_distintos_nao_e_deduplicado(tmp_path):
    _, c, runtime = compor(tmp_path)
    a = runtime.iniciar("oi", origem="terminal")
    b = runtime.iniciar("oi", origem="terminal")
    rs = ler(c)
    assert len(rs) == 2 and rs[0]["turno_id"] == a["id"] and rs[1]["turno_id"] == b["id"]
    assert rs[0]["id"] != rs[1]["id"]


def test_limite_texto_espacos_e_contexto_sem_system_prompt(tmp_path):
    h, c, _ = compor(tmp_path)
    h.estado.atualizar_campos("memoria_conversa", messages=[
        {"role": "system", "content": "segredo"},
        {"role": "user", "content": "  texto   anterior  "},
        {"role": "assistant", "content": "resposta"},
        {"role": "tool", "content": "não incluir"}])
    txt = "  A   B  " + "x" * 17000
    captura = c.preparar(txt, "terminal")
    assert captura["entrada"]["texto"].startswith("  A   B  ")
    assert captura["entrada"]["truncado"] is True
    assert captura["entrada"]["caracteres_originais"] == len(txt)
    assert "segredo" not in str(captura) and "não incluir" not in str(captura)
    assert captura["contexto_anterior"]["mensagens"][0]["texto"] == "  texto   anterior  "


def test_off_e_origem_desconhecida_nao_fabricam_humano(tmp_path):
    _, c, runtime = compor(tmp_path)
    c.ativo = False
    runtime.iniciar("oi", origem="terminal")
    assert ler(c) == []
    c.ativo = True
    c.conversa_getter = lambda: ""
    c.teste_getter = lambda: False
    r = c.preparar("oi", "api")
    assert r["conversa_id"] is None and r["origem_humana_certificada"] is False


def test_snapshot_antes_nao_muda_com_estado_depois(tmp_path):
    h, c, _ = compor(tmp_path)
    h.estado.atualizar_campos("mental", turno_atual={"id": 7})
    captura = c.preparar("oi", "terminal")
    h.estado.atualizar_campos("mental", turno_atual={"id": 8})
    c.registrar(captura, {"id": 9})
    assert ler(c)[0]["contexto_anterior"]["turno_id"] == 7


def test_limite_nao_apaga_arquivo_e_registra_falha_diagnostica(tmp_path):
    h, c, runtime = compor(tmp_path)
    runtime.iniciar("oi", origem="terminal")
    antes = c.buffer.caminho.read_bytes()
    c.limite_bytes = 1
    falhas = []
    class Diagnostico:
        def registrar_falha(self, *a, **k): falhas.append((a, k))
        def registrar_metrica(self, *a, **k): pass
    servicos = runtime._snapshot()
    servicos["_observabilidade_mente_runtime"] = Diagnostico()
    ComposicaoTurnoRuntime(servicos=servicos).iniciar("oi", origem="terminal")
    assert c.buffer.caminho.read_bytes() == antes
    assert any(a[:2] == ("neural_coleta", "falha_coleta_entrada") for a, k in falhas)


def test_binding_da_raiz_publica_coletor_no_registro_e_composicao(tmp_path, monkeypatch):
    # Executa apenas as instruções de wiring reais, não importa laylay.py
    # nem inicializa áudio, aplicações, rede ou serviços externos.
    h = _HarnessHS1()
    class Conversas:
        def id_ativo(self): return "chat-raiz"
    ns = dict(os=os, PASTA_MEMORIA=str(tmp_path),
        _estado_compartilhado_runtime=h.estado, _gerenciador_conversas_runtime=Conversas(),
        _registro_servicos_aplicacao_runtime=RegistroServicosAplicacaoRuntime(h.turnos._snapshot()),
        _criar_composicao_turno_runtime=composicao_turno.criar_composicao_turno_runtime)
    raiz = ast.parse((Path(__file__).resolve().parents[1] / "laylay.py").read_text(encoding="utf-8"))
    selecionados = []
    for no in raiz.body:
        if isinstance(no, ast.ImportFrom) and no.module == "mente_laylay.neural.coleta_entradas": selecionados.append(no)
        if isinstance(no, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {
            "_coleta_entradas_neurais", "_composicao_turno_runtime"} for t in no.targets): selecionados.append(no)
        if isinstance(no, ast.Expr) and isinstance(no.value, ast.Call) and any(
            k.arg == "_coleta_entradas_neurais" for k in no.value.keywords): selecionados.append(no)
    assert len(selecionados) == 4
    monkeypatch.setenv("LAYLAY_NEURAL_COLETA_ENTRADAS", "1")
    monkeypatch.setenv("LAYLAY_DIAGNOSTICO_DIR", "teste-local")
    exec(compile(ast.Module(body=selecionados, type_ignores=[]), "laylay.py:wiring-coleta", "exec"), ns)
    turno = ns["_composicao_turno_runtime"].iniciar("Não abra o Opera.", origem="terminal")
    r = ler(ns["_coleta_entradas_neurais"])[0]
    assert r["turno_id"] == turno["id"] and r["conversa_id"] == "chat-raiz"
    assert r["teste_declarado"] is True
