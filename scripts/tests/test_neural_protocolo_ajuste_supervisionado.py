"""Fixtures são artificiais; nenhum atestado humano é gerado fora dos testes."""
from copy import deepcopy

import pytest

from mente_laylay.neural.protocolo_ajuste_supervisionado import (
    auditar_corpus, importar_desenvolvimento_v4, preparar_particao, validar_caso,
)
from mente_laylay.neural.supervisao_relacoes_v4 import FLAGS


def caso(texto="abre o Chrome", *, identidade="a", grupo="g1", particao="desenvolvimento",
         ancora="abre", alvo="Chrome", intent="APP_OPEN", action="open", ato="pedido"):
    def span(t):
        inicio = texto.index(t)
        return {"inicio": inicio, "fim": inicio + len(t), "texto": t}
    return {"id": identidade, "texto": texto, "grupo": grupo, "ancestrais": [], "particao": particao,
            "origem_texto": "sintetico", "referencia_texto": "fixture/" + identidade,
            "origem_rotulo": "curadoria_ia", "referencia_rotulo": "fixture/anotacao/" + identidade,
            "conhecido_no_desenvolvimento": True, "enquadramento": "supervisionado",
            "motivo_fora_perfil": None, "fonte_v4": {"versao": 4, "texto_entrada": texto,
            "nos": [{"id": "n0", "intent": intent, "action": action, "ato": ato,
                     "trecho": {"inicio": 0, "fim": len(texto), "texto": texto},
                     "ancora": span(ancora), "alvos": [span(alvo)]}], "relacoes": [], **FLAGS}, **FLAGS}


def fora_perfil(texto, motivo, **kwargs):
    c = caso(**kwargs)
    c.update(texto=texto, enquadramento="fora_perfil", motivo_fora_perfil=motivo,
             fonte_v4=None, origem_rotulo="pendente")
    return c


def corpus_pronto():
    # Revisão humana fictícia para verificar o contrato técnico, não evidência de qualidade.
    modelos = {
        "t1": ("treino", {
            "pedido": "Para trabalhar nesta manhã, quero que você {v} {a}",
            "recusa": "Por favor, não {v} {a}, isso me atrapalharia hoje",
            "relato": "Lembro que ele decidiu {i} {a} durante a reunião da equipe"}),
        "t2": ("treino", {
            "pedido": "Minha solicitação concreta é {i} {a} imediatamente",
            "recusa": "Você está proibida de {i} {a}, mantenha essa restrição",
            "relato": "Minha colega comentou ter conseguido {i} {a} anteriormente"}),
        "s": ("selecao", {
            "pedido": "O próximo passo que estou pedindo consiste em {i} {a}",
            "recusa": "Não execute a operação de {i} {a} em nenhuma circunstância",
            "relato": "O relatório da semana passada dizia que ela foi {i} {a}"}),
        "c": ("calibracao", {
            "pedido": "Faça agora o seguinte: {v} {a}",
            "recusa": "Evite {i} {a}; esse procedimento está vetado",
            "relato": "Ontem minha irmã tentou {i} {a} e depois foi descansar"}),
    }
    variantes = [("APP_OPEN", "open", "abra", "abrir", "o aplicativo"),
                 ("MUSIC_SEARCH", "search", "toque", "tocar", "a faixa"),
                 ("FILE_READ", "read", "leia", "ler", "o arquivo")]
    nomes = {"t1": "Firefox", "t2": "Aquarela", "s": "Calendario", "c": "Horizonte"}
    saida = []
    for g, (p, moldes) in modelos.items():
        for intent, action, v, i, objeto in variantes:
            for ato, molde in moldes.items():
                texto = molde.format(v=v, i=i, a=objeto + " " + nomes[g])
                c = caso(texto, identidade=f"{g}_{intent}_{ato}", grupo=g, particao=p,
                         ancora=v if "{v}" in molde else i, alvo=nomes[g], intent=intent, action=action, ato=ato)
                c.update(origem_texto="uso_real", origem_rotulo="revisao_humana", conhecido_no_desenvolvimento=False)
                saida.append(c)
    return saida


def test_corpus_valido_nao_e_pronto_nem_reserva_independente():
    r = auditar_corpus([caso()])
    assert r["manifesto_valido"] is True
    assert r["dados_prontos_para_preparacao"] is False
    assert r["avaliacao_independente_disponivel"] is False
    assert r["viabilidade_de_fit_verificada"] is False
    with pytest.raises(ValueError, match="corpus não pronto"):
        preparar_particao([caso()], "treino")


@pytest.mark.parametrize("texto,motivo", [
    ("consegue abrir esse daqui?", "referencia_sem_contexto"),
    ("se eu pedir amanhã, abre o Chrome", "condicional_fora_do_perfil"),
    ("qual aplicativo você consegue abrir?", "pergunta_de_capacidade"),
    ("não abre; pensando melhor, abre sim", "correcao_temporal"),
])
def test_fora_perfil_nao_recebe_ato_fabricado(texto, motivo):
    c = fora_perfil(texto, motivo)
    r = auditar_corpus([c])
    assert r["fora_perfil"] == [{"id": "a", "motivo": motivo}]
    c["fonte_v4"] = caso()["fonte_v4"]
    with pytest.raises(ValueError, match="não pode carregar"):
        validar_caso(c)


@pytest.mark.parametrize("chave", sorted(FLAGS))
@pytest.mark.parametrize("valor", [True, 0, None])
def test_metadados_nao_concedem_autoridade(chave, valor):
    c = caso(); c[chave] = valor
    with pytest.raises(ValueError, match="não autoriza"):
        validar_caso(c)


def test_validador_v4_real_rejeita_alvo_inventado():
    c = caso(); c["fonte_v4"]["nos"][0]["alvos"][0]["texto"] = "Spotify"
    with pytest.raises(ValueError, match="intervalo"):
        validar_caso(c)


def test_mesmo_grupo_cruzado_bloqueia_preparacao():
    cs = [caso(particao="treino"), caso("leia as notas", identidade="b", particao="selecao",
                                      ancora="leia", alvo="notas", intent="FILE_READ", action="read")]
    r = auditar_corpus(cs)
    assert "parentesco_entre_particoes" in r["motivos"]


def test_linhagem_transitiva_nao_e_independencia():
    a = caso(particao="treino"); a["ancestrais"] = ["ancestral"]
    b = caso("toque a faixa azul", identidade="b", grupo="g2", particao="treino", ancora="toque", alvo="azul",
             intent="MUSIC_SEARCH", action="search"); b["ancestrais"] = ["ancestral", "elo"]
    c = caso("leia as notas", identidade="c", grupo="g3", particao="calibracao", ancora="leia", alvo="notas",
             intent="FILE_READ", action="read"); c["ancestrais"] = ["elo"]
    r = auditar_corpus([a, b, c])
    assert r["parentescos_cruzados"][0]["ids"] == ["a", "b", "c"]


def test_auditor_lexical_canonico_detecta_duplicata_sem_republicar_texto():
    a = caso(particao="treino")
    b = deepcopy(a); b.update(id="b", grupo="novo", particao="selecao")
    r = auditar_corpus([a, b])
    assert r["vazamentos_lexicais"] == [{"a": "a", "b": "b", "similaridade": 1.0}]
    assert "Chrome" not in str(r)


def test_importacao_v4_preserva_origem_e_nao_altera_fonte():
    c = {"id": "a", "grupo_validacao": "g", "grupo_construcao": "f", "fonte": caso()["fonte_v4"]}
    antes = deepcopy(c)
    r = importar_desenvolvimento_v4([c])[0]
    assert c == antes
    assert r["particao"] == "desenvolvimento" and r["conhecido_no_desenvolvimento"] is True
    assert r["origem_texto"] == "sintetico" and r["origem_rotulo"] == "curadoria_ia"
    validar_caso(r)


def test_preparacao_reutiliza_projecao_real_mas_so_exporta_texto_na_entrada():
    cs = corpus_pronto()
    antes = deepcopy(cs)
    r = auditar_corpus(cs)
    assert r["dados_prontos_para_preparacao"], r["motivos"]
    cs.append(fora_perfil("se eu pedir depois, faz isso", "condicional", identidade="fora", grupo="t1", particao="treino"))
    lote = preparar_particao(cs, "treino")
    assert len(lote["exemplos"]) == 18
    assert lote["fora_perfil"] == [{"id": "fora", "motivo": "condicional"}]
    assert set(lote["rotulos_catalogo"]) == {"ausente"} | {
        f"{i}|{a}|{ato}" for i, a in [("APP_OPEN", "open"), ("MUSIC_SEARCH", "search"), ("FILE_READ", "read")]
        for ato in ("pedido", "recusa", "relato")}
    assert all(set(e["entrada"]) == {"texto"} for e in lote["exemplos"])
    assert all(any(y.endswith("|pedido") for y in e["rotulos"]) for e in lote["exemplos"] if e["id"].endswith("pedido"))
    assert cs[:-1] == antes
    assert lote["autoriza_execucao"] is lote["autoriza_promocao"] is lote["treino_permitido"] is False


@pytest.mark.parametrize("alteracao,motivo", [("linhagem", "linhagem_desconhecida"),
                                             ("rotulo", "rotulos_pendentes"), ("origem", "sem_uso_real_revisado")])
def test_falsa_prontidao_bloqueada_antes_de_produzir_lote(alteracao, motivo):
    cs = corpus_pronto()
    for c in cs:
        if c["particao"] == "selecao":
            if alteracao == "linhagem": c["ancestrais"] = None
            elif alteracao == "rotulo": c["origem_rotulo"] = "pendente"
            else: c["origem_rotulo"] = "curadoria_ia"
    with pytest.raises(ValueError, match=motivo):
        preparar_particao(cs, "treino")


def test_reserva_nunca_entra_na_preparacao():
    c = caso(); c["particao"] = "holdout"
    with pytest.raises(ValueError, match="reserva"):
        validar_caso(c)
    with pytest.raises(ValueError, match="nunca reserva"):
        preparar_particao([caso()], "holdout")


def test_selecao_e_calibracao_nao_rebatizam_casos_ja_explorados():
    cs = corpus_pronto()
    next(c for c in cs if c["particao"] == "selecao")["conhecido_no_desenvolvimento"] = True
    assert "exposicao_anterior:selecao" in auditar_corpus(cs)["motivos"]


def test_familias_equivalentes_detectadas_pelo_auditor_canonico_bloqueiam():
    cs = corpus_pronto()
    for c in cs:
        if c["grupo"] == "s": c["grupo"] = " T1 "
    assert "familias_compartilhadas_entre_particoes" in auditar_corpus(cs)["motivos"]


def test_anotacao_bruta_nao_depende_da_normalizacao_do_parser():
    cs = corpus_pronto()
    # O perfil bruto deve conservar maiúsculas e nomes exatamente como anotados.
    r = preparar_particao(cs, "treino")
    primeiro = r["exemplos"][0]
    assert primeiro["entrada"]["texto"] == cs[0]["texto"]
    assert "Firefox" in primeiro["entrada"]["texto"]
    assert primeiro["rotulos"].count("APP_OPEN|open|pedido") == 1


def test_duplicacao_dentro_da_mesma_particao_nao_inflaciona_cobertura():
    cs = corpus_pronto()
    c = deepcopy(cs[0]); c["id"] = "duplicado"
    cs.append(c)
    assert "textos_repetidos" in auditar_corpus(cs)["motivos"]
