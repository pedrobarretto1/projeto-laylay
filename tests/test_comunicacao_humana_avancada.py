from __future__ import annotations

from memoria_sqlite import MemoriaSQLite
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa
from mente_laylay.memoria_mental.correcoes_usuario import (
    extrair_correcao_duravel,
    persistir_correcao_duravel,
)
from mente_laylay.memoria_mental.encerramento_assunto import (
    classificar_encerramento_assunto,
    encerrar_topico,
)
from mente_laylay.personalidade.falas_variadas import escolher_contextual
from mente_laylay.personalidade.memoria_sutil import sutilizar_referencia_memoria
from mente_laylay.personalidade.ritmo_natural import ajustar_encerramento_organico


def test_funcao_emocional_define_postura_e_limite_de_pergunta() -> None:
    leitura = analisar_funcao_comunicativa("já falei, isso não funcionou")
    assert leitura["funcao"] in {"correcao", "frustracao"}
    assert leitura["postura_esperada"] in {"receptiva", "reparadora"}
    assert leitura["permite_pergunta"] is False


def test_plano_carrega_contrato_emocional_sem_reescrever_a_llm() -> None:
    texto = "não Lay, eu quis dizer outra coisa"
    funcao = analisar_funcao_comunicativa(texto)
    plano = planejar_turno(
        texto,
        turno={"modalidade": "conversa", "ato_principal": "conversa", "funcao_comunicativa": funcao},
    )
    assert plano["postura_esperada"] == "receptiva"
    assert plano["permite_pergunta"] is False
    verificada = verificar_fala_turno(
        "Entendi a correção. Quer conversar sobre outra coisa?",
        plano=plano,
    )
    assert verificada["fala"] == "Entendi a correção. Quer conversar sobre outra coisa?"
    assert "pergunta_inadequada_a_funcao_emocional" not in verificada["problemas"]


def test_correcao_de_capacidade_e_persistida_como_confirmada(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "mente.sqlite"))
    correcao = extrair_correcao_duravel(
        "você ainda não tem essa habilidade",
        estado_mental={"capacidade_futura": {"alvo": "controlar a luz"}},
    )
    assert correcao is not None
    assert "controlar a luz" in correcao["regra"]
    assert persistir_correcao_duravel(memoria, correcao, "você ainda não tem essa habilidade")
    itens = memoria.listar_aprendizados_semanticos()
    assert itens[0]["status"] == "ativo"
    assert bool(itens[0]["confirmado_usuario"])


def test_agradecimento_fecha_topico_mas_nao_apaga_fatos() -> None:
    assert classificar_encerramento_assunto("obrigado Lay") == "topico"
    assert classificar_encerramento_assunto("obrigado, mas como faz isso?") == ""
    mente, conversa = encerrar_topico(
        {
            "foco_conversacional_topico": "receita de coxinha",
            "preferencia_musical": "rock",
            "pendencia_atual": {"status": "ativa"},
        },
        {"ultimo_topico_conversa": "receita de coxinha"},
        motivo="obrigado",
        agora=123.0,
    )
    assert mente["foco_conversacional_topico"] == ""
    assert mente["preferencia_musical"] == "rock"
    assert mente["assuntos_encerrados"][-1]["topico"] == "receita de coxinha"
    assert conversa["ultimo_topico_conversa"] == ""


def test_confirmacao_curta_nao_fecha_quando_existe_acao_pendente() -> None:
    estado = {"pendencia_atual": {"status": "ativa"}}
    assert classificar_encerramento_assunto("beleza", estado) == ""


def test_pergunta_generica_isolada_nao_forca_conversa_sem_assunto() -> None:
    fala = ajustar_encerramento_organico("Posso te ajudar em mais alguma coisa?", "agora nada demais")
    assert fala == "Tudo certo. Um pouco de sossego também vale."


def test_selecao_contextual_prefere_fala_curta_no_modo_jogo() -> None:
    fala = escolher_contextual(
        ["Feito.", "Pronto, terminei essa operação e deixei tudo certinho para você."],
        contexto={"modo_jogo": True},
    )
    assert fala == "Feito."


def test_memoria_e_demonstrada_sem_anunciar_o_mecanismo() -> None:
    fala = sutilizar_referencia_memoria(
        "Segundo minha memória, eu lembro que você costuma estudar no SENAI."
    )
    assert fala == "Você costuma estudar no SENAI."
    assert "memória" not in fala.casefold()
