from __future__ import annotations

import pytest
import joblib
import numpy as np

from mente_laylay.neural.modelo import treinar_modelo
from mente_laylay.neural.validacao_extensao import validar_extensao_por_grupos


class _EncoderFixoTeste:
    """Fronteira sintética para testar wiring, não qualidade semântica."""

    def codificar(self, textos):
        return np.asarray([
            [float("consulta" in texto), float("app" in texto), 1.0]
            for texto in textos
        ])


@pytest.mark.parametrize("representacao", ["integral_v1", "semantico_hibrido_base"])
def test_v29_cv_fatorada_preserva_oof_grupos_e_modelo_base(tmp_path, representacao):
    modelo = _modelo_base(tmp_path)
    if representacao == "semantico_hibrido_base":
        modelo.encoder_semantico = _EncoderFixoTeste()
    antes = joblib.hash(modelo)
    r = validar_extensao_por_grupos(
        modelo, _exemplos_fatorados(), intent="LIST_WINDOWS", action="list",
        escopo="consulta_ativa", n_splits=2, limiares=(0.5,),
        representacoes_fatores={"ato_consulta": representacao, "dominio_app": "tfidf"},
    )
    assert joblib.hash(modelo) == antes
    assert not modelo.extensoes_intent
    assert len(r["previsoes_oof"]) == 16
    assert all(not f["grupos_compartilhados"] for f in r["folds"])
    for linha in r["previsoes_oof"]:
        assert set(linha["fatores"]) == {"ato_consulta", "dominio_app"}
        assert all(np.isfinite(p) and 0 <= p <= 1 for p in linha["fatores"].values())
        assert linha["probabilidade"] == min(linha["fatores"].values())
    assert r["contrato"]["nao_promove_modelo"] is True


@pytest.mark.parametrize("fatorada", [False, True])
def test_v29_sem_encoder_falha_sem_fallback_lexical(tmp_path, fatorada):
    from mente_laylay.neural.modelo import adicionar_extensao_intent, adicionar_extensao_intent_fatorada
    modelo = _modelo_base(tmp_path)
    argumentos = {"representacoes_fatores": {"ato_consulta": "semantico_hibrido_base"}} if fatorada else {
        "representacao": "semantico_hibrido_base",
    }
    funcao = adicionar_extensao_intent_fatorada if fatorada else adicionar_extensao_intent
    with pytest.raises(ValueError, match="exige encoder semântico"):
        funcao(modelo, _exemplos_fatorados(), intent="LIST_WINDOWS", action="list", **argumentos)
    assert not modelo.extensoes_intent


@pytest.mark.parametrize("fatorada", [False, True])
def test_v29_detector_reutiliza_encoder_e_sobrevive_serializacao(tmp_path, fatorada):
    from mente_laylay.neural.modelo import (
        DetectorExtensaoEncoderBase, adicionar_extensao_intent, adicionar_extensao_intent_fatorada,
    )
    modelo = _modelo_base(tmp_path)
    modelo.encoder_semantico = _EncoderFixoTeste()
    antes = joblib.hash(modelo)
    argumentos = {"representacoes_fatores": {"ato_consulta": "semantico_hibrido_base"}} if fatorada else {
        "representacao": "semantico_hibrido_base",
    }
    funcao = adicionar_extensao_intent_fatorada if fatorada else adicionar_extensao_intent
    caminho = tmp_path / "candidato.joblib"
    candidato = funcao(modelo, _exemplos_fatorados(), intent="LIST_WINDOWS", action="list",
                       caminho=caminho, **argumentos)
    extensao = candidato.extensoes_intent["LIST_WINDOWS"]
    detector = extensao.detectores_fatores["ato_consulta"] if fatorada else extensao.detector
    assert isinstance(detector, DetectorExtensaoEncoderBase)
    assert detector.encoder is modelo.encoder_semantico
    textos = ["consulta app", "relato porta"]
    esperado = detector.predict_proba(textos)
    recarregado = joblib.load(caminho)
    ext = recarregado.extensoes_intent["LIST_WINDOWS"]
    det = ext.detectores_fatores["ato_consulta"] if fatorada else ext.detector
    np.testing.assert_allclose(det.predict_proba(textos), esperado)
    np.testing.assert_allclose(det.predict_proba(textos[0]), esperado[:1])
    assert det.encoder is recarregado.encoder_semantico
    assert joblib.hash(modelo) == antes
    assert not modelo.extensoes_intent


def _modelo_base(tmp_path):
    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "aumenta o som", "intent": "VOLUME", "is_command": True, "negated": False, "action": "up"},
        {"text": "abre o editor", "intent": "APP_OPEN", "is_command": True, "negated": False, "action": "open"},
        {"text": "gosto de música", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    return treinar_modelo(
        exemplos,
        caminho=tmp_path / "base.joblib",
        versao="base-teste",
        estrategia="sgd_log_loss",
    )


def test_v30_validacao_distingue_actions_da_mesma_intent(tmp_path) -> None:
    exemplos = []
    for grupo in range(4):
        exemplos.extend((
            {
                "text": f"liga a luz {grupo}",
                "intent": "IOT_CONTROL",
                "action": "on",
                "extension_scope": "operacional_literal_v1",
                "validation_group": f"grupo_{grupo}",
            },
            {
                "text": f"desliga a luz {grupo}",
                "intent": "IOT_CONTROL",
                "action": "off",
                "extension_scope": "operacional_literal_v1",
                "validation_group": f"grupo_{grupo}",
            },
        ))

    relatorio = validar_extensao_por_grupos(
        _modelo_base(tmp_path),
        exemplos,
        intent="IOT_CONTROL",
        action="on",
        escopo="operacional_literal_v1",
        n_splits=2,
        limiares=(0.5,),
    )

    assert relatorio["positivos"] == 4
    assert relatorio["negativos"] == 4


def test_validacao_extensao_isola_grupos_e_publica_matriz_por_limiar(
    tmp_path,
) -> None:
    modelo = _modelo_base(tmp_path)
    exemplos = []
    for grupo in range(4):
        exemplos.extend((
            {
                "text": f"consulta janela aplicativo {grupo}",
                "intent": "LIST_WINDOWS",
                "action": "list",
                "extension_scope": "consulta_ativa",
                "validation_group": f"grupo_{grupo}",
            },
            {
                "text": f"relato janela assunto {grupo}",
                "intent": "NONE",
                "action": "none",
                "extension_scope": "contraste",
                "validation_group": f"grupo_{grupo}",
            },
        ))

    relatorio = validar_extensao_por_grupos(
        modelo,
        exemplos,
        intent="LIST_WINDOWS",
        action="list",
        escopo="consulta_ativa",
        representacao="estrutura_pontuacao",
        agrupamento="validation_group",
        n_splits=2,
        limiares=(0.5, 0.9),
    )

    assert relatorio["agrupamento"] == "validation_group"
    assert relatorio["total"] == 8
    assert relatorio["positivos"] == 4
    assert relatorio["negativos"] == 4
    assert len(relatorio["folds"]) == 2
    assert all(not fold["grupos_compartilhados"] for fold in relatorio["folds"])
    assert set(relatorio["limiares"]) == {"0.5", "0.9"}
    assert all(
        sum(matriz[chave] for chave in ("tp", "fn", "fp", "tn")) == 8
        for matriz in relatorio["limiares"].values()
    )
    assert relatorio["contrato"] == {
        "predicao_vira_label": False,
        "grupos_inteiros_por_fold": True,
        "nao_promove_modelo": True,
    }


def _exemplos_fatorados():
    itens = []
    for grupo in range(4):
        for ato, dominio in ((True, True), (True, False), (False, True), (False, False)):
            itens.append({
                "text": f"{'consulta' if ato else 'relato'} {'app' if dominio else 'porta'} {grupo}",
                "intent": "LIST_WINDOWS" if ato and dominio else "NONE",
                "action": "list" if ato and dominio else "none",
                "extension_scope": "consulta_ativa" if ato and dominio else "contraste",
                "validation_group": f"grupo_{grupo}",
                "validation_entity_group": f"entidade_{grupo}",
                "extension_factors": {"ato_consulta": ato, "dominio_app": dominio},
            })
    return itens


def test_cv_fatorada_publica_evidencia_oof_de_cada_fator_e_da_conjuncao(tmp_path):
    modelo = _modelo_base(tmp_path)
    relatorio = validar_extensao_por_grupos(
        modelo, _exemplos_fatorados(), intent="LIST_WINDOWS", action="list",
        escopo="consulta_ativa", n_splits=2, limiares=(0.5,),
        representacoes_fatores={"ato_consulta": "tfidf", "dominio_app": "tfidf"},
    )

    assert relatorio["positivos"] == 4
    assert len(relatorio["previsoes_oof"]) == 16
    assert set(relatorio["fatores"]) == {"ato_consulta", "dominio_app"}
    assert not modelo.extensoes_intent
    for fator in relatorio["fatores"].values():
        assert fator["positivos"] == 8
        assert fator["negativos"] == 8
        assert sum(fator["limiares"]["0.5"][k] for k in ("tp", "fp", "fn", "tn")) == 16
    for linha in relatorio["previsoes_oof"]:
        assert linha["probabilidade"] == min(linha["fatores"].values())
        assert linha["fold"] in (1, 2)
        assert len(linha["texto_sha256"]) == 64
    matriz = relatorio["limiares"]["0.5"]
    assert matriz["tp"] == sum(
        linha["esperado"] and linha["probabilidade"] >= 0.5
        for linha in relatorio["previsoes_oof"]
    )


def test_cv_recusa_rotulo_final_contraditorio_com_fatores(tmp_path):
    exemplos = _exemplos_fatorados()
    exemplos[0]["extension_factors"]["dominio_app"] = False
    with pytest.raises(ValueError, match="conjunção"):
        validar_extensao_por_grupos(
            _modelo_base(tmp_path), exemplos, intent="LIST_WINDOWS", action="list",
            escopo="consulta_ativa", n_splits=2,
            representacoes_fatores={"ato_consulta": "tfidf", "dominio_app": "tfidf"},
        )


@pytest.mark.parametrize("limiares", [(), (float("nan"),), (1.1,)])
def test_cv_recusa_grade_invalida_antes_de_treinar(tmp_path, monkeypatch, limiares):
    def treino_indevido(*args, **kwargs):
        pytest.fail("treino começou antes de validar a grade")
    monkeypatch.setattr(
        "mente_laylay.neural.validacao_extensao.adicionar_extensao_intent", treino_indevido,
    )
    with pytest.raises(ValueError, match="limiares"):
        validar_extensao_por_grupos(
            _modelo_base(tmp_path), _exemplos_fatorados(),
            intent="LIST_WINDOWS", action="list", n_splits=2, limiares=limiares,
        )


@pytest.mark.parametrize("eixo", ["validation_group", "validation_entity_group"])
def test_complemento_preserva_prova_e_nunca_treina_grupo_retido(tmp_path, monkeypatch, eixo):
    from mente_laylay.neural import validacao_extensao as modulo

    base = _modelo_base(tmp_path)
    ancora = _exemplos_fatorados()
    complemento = [dict(x, text="forma complementar " + x["text"]) for x in ancora]
    chamadas = []
    treinar_real = modulo.adicionar_extensao_intent_fatorada

    def registrar_treino(modelo, exemplos, **kwargs):
        itens = list(exemplos)
        chamadas.append(itens)
        return treinar_real(modelo, itens, **kwargs)

    monkeypatch.setattr(modulo, "adicionar_extensao_intent_fatorada", registrar_treino)
    argumentos = dict(
        intent="LIST_WINDOWS", action="list", escopo="consulta_ativa",
        n_splits=2, limiares=(0.5,), agrupamento=eixo,
        representacoes_fatores={"ato_consulta": "tfidf", "dominio_app": "tfidf"},
    )
    antes = validar_extensao_por_grupos(base, ancora, **argumentos)
    chamadas.clear()
    depois = validar_extensao_por_grupos(
        base, ancora, exemplos_complementares=complemento, **argumentos,
    )
    assert depois["total"] == antes["total"] == len(ancora)
    assert [(x["texto_sha256"], x["fold"]) for x in antes["previsoes_oof"]] == [
        (x["texto_sha256"], x["fold"]) for x in depois["previsoes_oof"]
    ]
    for fold, treino in zip(depois["folds"], chamadas, strict=True):
        retidos = {x["grupo"] for x in depois["previsoes_oof"] if x["fold"] == fold["fold"]}
        assert not retidos & {x[eixo] for x in treino}
        assert fold["complementares_treino"] == 8
        assert fold["complementares_excluidos"] == 8
        assert len(treino) == 16
    assert not base.extensoes_intent


@pytest.mark.parametrize("defeito", ["duplicata", "sem_grupo", "fator_contraditorio"])
def test_complemento_invalido_aborta_antes_do_treino(tmp_path, monkeypatch, defeito):
    ancora = _exemplos_fatorados()
    extra = dict(ancora[0], text="consulta complementar de app")
    if defeito == "duplicata":
        extra["text"] = ancora[0]["text"].upper() + "  "
    elif defeito == "sem_grupo":
        extra.pop("validation_group")
    else:
        extra["extension_factors"] = {"ato_consulta": False, "dominio_app": True}

    def treino_indevido(*args, **kwargs):
        pytest.fail("complemento inválido alcançou o treino")
    monkeypatch.setattr(
        "mente_laylay.neural.validacao_extensao.adicionar_extensao_intent_fatorada",
        treino_indevido,
    )
    with pytest.raises(ValueError, match="complement|conjunção"):
        validar_extensao_por_grupos(
            _modelo_base(tmp_path), ancora, exemplos_complementares=[extra],
            intent="LIST_WINDOWS", action="list", escopo="consulta_ativa",
            n_splits=2, representacoes_fatores={"ato_consulta": "tfidf", "dominio_app": "tfidf"},
        )
