import json
from types import SimpleNamespace

import pytest

from mente_laylay.neural import curadoria_prospectiva_encoder as c
from mente_laylay.neural.coleta_entradas import ColetaEntradasNeurais
from mente_laylay.neural.supervisao_relacoes_v4 import FLAGS
from mente_laylay.neural.revisao_encoder import aplicar_revisao
from tests.test_neural_coleta_entradas import compor


def gravar(tmp_path, *, teste=False, texto="Abre o Editor", turno=1, contexto=None):
    estado = SimpleNamespace(mental={"sessao_conversa_ts": 10},
                             memoria_conversa={"messages": contexto or []})
    coletor = ColetaEntradasNeurais(tmp_path / "coleta.jsonl", estado=estado,
        conversa_getter=lambda: "sessao-fixture", teste_getter=lambda: teste, ativo=True)
    coletor.registrar(coletor.preparar(texto, "terminal"), {"id": turno})
    return coletor.buffer.caminho


def modificar(p, **mudancas):
    r = json.loads(p.read_text(encoding="utf-8"))
    r.update(mudancas)
    p.write_text(json.dumps(r, ensure_ascii=False) + "\n", encoding="utf-8")


def test_evento_real_da_composicao_preserva_origem_teste(tmp_path):
    h, coletor, runtime = compor(tmp_path)
    h.estado.atualizar_campos("mental", sessao_conversa_ts=123.5)
    turno = runtime.iniciar("Não abra a Microsoft Store.", origem="roteiro_teste")
    antes = coletor.buffer.caminho.read_bytes()
    fila, resumo = c.preparar_fila(coletor.buffer.caminho)
    assert fila[0]["destinacao"] == "teste_declarado"
    assert fila[0]["registro_origem"]["turno_id"] == turno["id"]
    assert fila[0]["anotacao"] is fila[0]["particao"] is None
    assert all(fila[0][k] is False for k in FLAGS)
    assert resumo["revisoes_humanas_certificadas"] == 0
    assert coletor.buffer.caminho.read_bytes() == antes


def test_revisao_prospectiva_preserva_eventos_repetidos_e_contexto_sem_criar_rotulos(tmp_path):
    texto = "pode me recomendar um modelo que seja bom e barato"
    gravar(tmp_path, texto=texto, turno=1, contexto=[
        {"role": "user", "content": "vamos conversar sobre módulos DC-DC"},
    ])
    gravar(tmp_path, texto=texto, turno=2, contexto=[
        {"role": "assistant", "content": "Não tenho capacidade de recomendar."},
    ])
    caminho = gravar(tmp_path, texto="pode abrir um site sobre módulo de conversão DC-DC", turno=3)
    antes = caminho.read_bytes()
    fila, _ = c.preparar_fila(caminho)
    revisao = {"origem_rotulo": "curadoria_ia", "grupos": [{
        "indices_fila": [1, 2, 3], "grupo": "conversa_comum",
        "motivo": "Recomendação contextual e navegação estão fora do perfil de três variantes.",
        "enquadramento": "fora_perfil", "fonte_v4": None, **FLAGS,
    }]}
    saida, resumo = aplicar_revisao(fila, revisao, {})
    assert len(saida) == 3
    assert len({r["id"] for r in saida}) == 3
    assert saida[0]["texto"] == saida[1]["texto"]
    assert saida[0]["registro_origem"]["contexto_anterior"] != saida[1]["registro_origem"]["contexto_anterior"]
    for original, revisado in zip(fila, saida):
        assert revisado["registro_origem"] == original["registro_origem"]
        assert revisado["referencias"] == original["referencias"]
        assert revisado["anotacao"] is revisado["particao"] is None
        assert revisado["conhecido_no_desenvolvimento"] is True
        assert revisado["origem_rotulo"] == "curadoria_ia"
        assert all(revisado[k] is False for k in FLAGS)
    assert resumo["cobertura_anotada_ia"] == {}
    assert resumo["revisoes_humanas"] == 0
    assert resumo["dados_prontos"] is False
    assert caminho.read_bytes() == antes


def test_sem_marcador_de_teste_nao_certifica_humano(tmp_path):
    p = gravar(tmp_path)
    fila, resumo = c.preparar_fila(p)
    assert fila[0]["destinacao"] == "revisao_pendente"
    assert fila[0]["origem_texto"] == "desconhecida"
    assert fila[0]["registro_origem"]["origem_humana_certificada"] is False
    assert resumo["dados_prontos"] is False


def test_texto_igual_nao_funde_eventos_com_contextos_distintos(tmp_path):
    p = gravar(tmp_path, texto="sim", contexto=[{"role": "assistant", "content": "Abrir o Editor?"}])
    gravar(tmp_path, texto="sim", turno=2,
           contexto=[{"role": "assistant", "content": "Você gosta de rock?"}])
    fila, resumo = c.preparar_fila(p)
    assert len(fila) == 2 and resumo["textos_distintos"] == 1
    assert fila[0]["id"] != fila[1]["id"]
    assert fila[0]["registro_origem"]["contexto_anterior"] != fila[1]["registro_origem"]["contexto_anterior"]
    assert all(r["contexto_completo_certificado"] is False for r in fila)


@pytest.mark.parametrize("mudancas", [
    {"tipo": "evento_percepcao"}, {"versao": 9}, {"id": None},
    {"turno_id": None}, {"turno_id": True}, {"conversa_id": None},
    {"planejamento": "falhou"}, {"anotacao": {"rotulo": "pedido"}},
    {"particao": "treino"}, {"autoriza_execucao": True},
    {"origem_humana_certificada": True}, {"teste_declarado": "False"},
    {"origem_declarada": "presenca"}, {"contexto_anterior": None},
    {"entrada": {"texto": "texto adulterado", "truncado": False}},
])
def test_contrato_invalido_fica_em_quarentena_sem_alterar_original(tmp_path, mudancas):
    p = gravar(tmp_path)
    modificar(p, **mudancas)
    antes = p.read_bytes()
    fila, resumo = c.preparar_fila(p)
    assert fila[0]["destinacao"] == "quarentena"
    assert fila[0]["motivos"]
    assert resumo["dados_prontos"] is False
    assert p.read_bytes() == antes


def test_truncamento_nao_recebe_fidelidade_integral(tmp_path):
    p = gravar(tmp_path, texto="a" * 16001)
    fila, _ = c.preparar_fila(p)
    assert "texto_truncado_ou_fidelidade_desconhecida" in fila[0]["motivos"]
    assert len(fila[0]["texto"]) == 16000


@pytest.mark.parametrize("duplicar_registro", [False, True])
def test_identidade_duplicada_quarentena_todas_as_ocorrencias(tmp_path, duplicar_registro):
    p = gravar(tmp_path)
    if duplicar_registro:
        registro = p.read_text(encoding="utf-8")
        with p.open("a", encoding="utf-8") as f:
            f.write(registro)
    else:
        gravar(tmp_path, texto="outra entrada", turno=1)
    fila, _ = c.preparar_fila(p)
    assert len(fila) == 2 and all(r["destinacao"] == "quarentena" for r in fila)


def test_linha_invalida_contabilizada_sem_reparo_da_fonte(tmp_path):
    p = gravar(tmp_path)
    with p.open("a", encoding="utf-8") as f:
        f.write("{\n")
    gravar(tmp_path, turno=2)
    antes = p.read_bytes()
    fila, resumo = c.preparar_fila(p)
    assert resumo["linhas_invalidas"] == 1
    assert fila[1]["referencias"][0]["indice_registro_valido"] == 2
    assert p.read_bytes() == antes


def test_mudanca_durante_leitura_aborta_sem_exportar(tmp_path, monkeypatch):
    p = gravar(tmp_path)
    ler = c.ler_jsonl_tolerante
    def mudar(caminho):
        registros = ler(caminho)
        gravar(tmp_path, turno=2)
        return registros
    monkeypatch.setattr(c, "ler_jsonl_tolerante", mudar)
    with pytest.raises(RuntimeError, match="mudou"):
        c.executar(p, tmp_path / "saida")
    assert not (tmp_path / "saida").exists()


def test_exportacao_auditavel_preserva_artefato_anterior(tmp_path):
    p = gravar(tmp_path, teste=True)
    destino = tmp_path / "saida"
    resumo = c.executar(p, destino)
    assert c._hash(destino / "fila.jsonl") == resumo["fila_sha256"]
    assert c._hash(p) == resumo["fonte_sha256"]
    with pytest.raises(FileExistsError):
        c.executar(p, destino)


def test_fonte_ausente_aborta(tmp_path):
    with pytest.raises(FileNotFoundError):
        c.executar(tmp_path / "ausente", tmp_path / "saida")
    assert not (tmp_path / "saida").exists()
