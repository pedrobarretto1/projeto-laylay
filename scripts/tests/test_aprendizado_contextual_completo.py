from __future__ import annotations

from datetime import datetime, timedelta
import os
import tempfile

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.sugestoes_sistema import processar_confirmacao_sugestao
from mente_laylay.memoria_mental.maturidade_aprendizado import MaturidadeAprendizadoRuntime
from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime


def _memoria_temporaria():
    pasta = tempfile.TemporaryDirectory()
    return pasta, MemoriaSQLite(os.path.join(pasta.name, "memoria.sqlite"))


def _alternativa_volume(nivel: int) -> dict:
    return {
        "alternativa": {"intent": "VOLUME", "params": {"nivel_volume": nivel}},
        "descricao": f"deixar o volume em {nivel} por cento",
        "evidencia": f"prefiro o volume em {nivel} por cento",
    }


def _envelhecer(memoria: MemoriaSQLite, chave: str, instante: datetime) -> None:
    conn = memoria._conectar()
    try:
        texto = instante.isoformat(" ")
        conn.execute(
            "UPDATE aprendizado_eventos SET criado_em = ? WHERE chave = ?",
            (texto, chave),
        )
        conn.execute(
            "UPDATE aprendizado_hipoteses SET ultima_evidencia_em = ?, atualizado_em = ? WHERE chave = ?",
            (texto, texto, chave),
        )
        conn.commit()
    finally:
        conn.close()


def test_preferencia_confirmada_tambem_decai_sem_novo_reforco() -> None:
    pasta, memoria = _memoria_temporaria()
    base = datetime(2020, 1, 1, 12, 0)
    try:
        memoria.registrar_evidencia_aprendizado(
            chave="preferencia:antiga", tipo="preferencia_contextual", escopo="geral",
            valor={"descricao_humana": "prefere uma opção antiga"}, sinal=1.0,
            origem="usuario", confirmado_usuario=True,
        )
        _envelhecer(memoria, "preferencia:antiga", base)
        maturidade = MaturidadeAprendizadoRuntime(
            memoria_sqlite=memoria, contexto_getter=lambda: {},
            agora=lambda: base + timedelta(days=1200),
        )

        avaliacao = maturidade.avaliar("preferencia:antiga")

        assert avaliacao["confirmacoes_usuario"] == 1
        assert avaliacao["confianca_efetiva"] < 0.30
        assert avaliacao["nivel"] == "enfraquecida"
        assert avaliacao["aplicavel"] is False
    finally:
        pasta.cleanup()


def test_repeticoes_independentes_aumentam_resistencia_ao_tempo() -> None:
    pasta, memoria = _memoria_temporaria()
    base = datetime(2024, 1, 1, 12, 0)
    try:
        for chave, repeticoes in (("preferencia:isolada", 1), ("preferencia:reforcada", 4)):
            for indice in range(repeticoes):
                memoria.registrar_evidencia_aprendizado(
                    chave=chave, tipo="preferencia_contextual", escopo="geral",
                    valor={"descricao_humana": "prefere luz baixa"}, sinal=1.0,
                    origem="usuario", confirmado_usuario=indice == 0,
                )
            conn = memoria._conectar()
            try:
                ids = [row[0] for row in conn.execute(
                    "SELECT id FROM aprendizado_eventos WHERE chave = ? ORDER BY id", (chave,),
                ).fetchall()]
                for indice, evento_id in enumerate(ids):
                    conn.execute(
                        "UPDATE aprendizado_eventos SET criado_em = ? WHERE id = ?",
                        ((base + timedelta(days=indice)).isoformat(" "), evento_id),
                    )
                ultima = (base + timedelta(days=max(0, repeticoes - 1))).isoformat(" ")
                conn.execute(
                    "UPDATE aprendizado_hipoteses SET ultima_evidencia_em = ?, atualizado_em = ? WHERE chave = ?",
                    (ultima, ultima, chave),
                )
                conn.commit()
            finally:
                conn.close()

        maturidade = MaturidadeAprendizadoRuntime(
            memoria_sqlite=memoria, contexto_getter=lambda: {},
            agora=lambda: base + timedelta(days=300),
        )
        isolada = maturidade.avaliar("preferencia:isolada")
        reforcada = maturidade.avaliar("preferencia:reforcada")

        assert reforcada["fator_reforco"] > isolada["fator_reforco"]
        assert reforcada["meia_vida_ajustada_dias"] > isolada["meia_vida_ajustada_dias"]
        assert reforcada["confianca_efetiva"] > isolada["confianca_efetiva"]
    finally:
        pasta.cleanup()


def test_preferencia_condicionada_distingue_atividade_no_mesmo_horario() -> None:
    pasta, memoria = _memoria_temporaria()
    contexto = {"periodo": "noite", "atividade": "jogando"}
    try:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=memoria, contexto_getter=lambda: dict(contexto), log=lambda *_: None,
        )
        hipotese = motor.registrar_contraproposta("VOLUME", _alternativa_volume(20))
        assert hipotese and motor.avaliar_hipotese(hipotese["chave"])["aplicavel"]

        contexto["atividade"] = "programando"
        avaliacao = motor.avaliar_hipotese(hipotese["chave"])

        assert avaliacao["aplicavel"] is False
        assert any("atividade" in motivo for motivo in avaliacao["motivos"])
    finally:
        pasta.cleanup()


def test_preferencia_global_e_condicionada_coexistem_e_a_especifica_tem_prioridade() -> None:
    pasta, memoria = _memoria_temporaria()
    contexto = {"periodo": "noite", "atividade": "jogando"}
    try:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=memoria, contexto_getter=lambda: dict(contexto), log=lambda *_: None,
        )
        global_ = _alternativa_volume(35)
        global_["evidencia"] = "de agora em diante sempre prefiro o volume em 35 por cento"
        motor.registrar_contraproposta("VOLUME", global_)
        motor.registrar_contraproposta("VOLUME", _alternativa_volume(15))

        durante_jogo = motor.selecionar_preferencia_sugestao("VOLUME")
        contexto["atividade"] = "programando"
        fora_do_jogo = motor.selecionar_preferencia_sugestao("VOLUME")

        assert durante_jogo["alternativa"]["params"]["nivel_volume"] == 15
        assert fora_do_jogo["alternativa"]["params"]["nivel_volume"] == 35
        assert len(motor._variantes_preferencia("preferencia_sugestao:VOLUME")) == 2
    finally:
        pasta.cleanup()


def test_excecao_contextual_nao_rebaixa_preferencia_principal() -> None:
    pasta, memoria = _memoria_temporaria()
    contexto = {"periodo": "noite", "atividade": "jogando"}
    try:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=memoria, contexto_getter=lambda: dict(contexto), log=lambda *_: None,
        )
        registro = _alternativa_volume(30)
        registro["evidencia"] = "sempre prefiro o volume em 30 por cento"
        principal = motor.registrar_contraproposta("VOLUME", registro)
        confianca_antes = memoria.obter_hipotese_aprendizado(principal["chave"])["confianca"]

        excecao = motor.registrar_excecao_preferencia(principal["chave"], "hoje jogando deixa mais alto")
        durante_jogo = motor.avaliar_hipotese(principal["chave"])
        contexto["atividade"] = "programando"
        fora_do_jogo = motor.avaliar_hipotese(principal["chave"])
        principal_depois = memoria.obter_hipotese_aprendizado(principal["chave"])

        assert excecao["tipo"] == "excecao_preferencia"
        assert principal_depois["confianca"] == confianca_antes
        assert principal_depois["evidencias_negativas"] == 0
        assert durante_jogo["aplicavel"] is False
        assert durante_jogo["excecao_ativa"]
        assert fora_do_jogo["aplicavel"] is True
    finally:
        pasta.cleanup()


def test_duas_preferencias_confiaveis_no_mesmo_contexto_aguardam_confirmacao() -> None:
    pasta, memoria = _memoria_temporaria()
    contexto = {"periodo": "noite", "atividade": "jogando"}
    try:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=memoria, contexto_getter=lambda: dict(contexto), log=lambda *_: None,
        )
        primeira = motor.registrar_contraproposta("VOLUME", _alternativa_volume(20))
        conflito = motor.registrar_contraproposta("VOLUME", _alternativa_volume(10))

        assert conflito["conflito"] is True
        assert conflito["status"] == "aguardando_confirmacao"
        assert "Quer substituir" in conflito["pergunta"]
        assert memoria.obter_hipotese_aprendizado(primeira["chave"])["valor"]["alternativa"]["params"]["nivel_volume"] == 20

        motor.resolver_conflito_preferencia(conflito, True)
        escolhida = motor.selecionar_preferencia_sugestao("VOLUME")
        assert escolhida["alternativa"]["params"]["nivel_volume"] == 10
        assert memoria.obter_hipotese_aprendizado(primeira["chave"])["status"] == "enfraquecida"
    finally:
        pasta.cleanup()


def test_fluxo_conversacional_transforma_conflito_em_pergunta_pendente() -> None:
    agora = __import__("time").time()
    estado = {
        "comando_sugerido": "EXECUTE_INTENT",
        "comando_sugerido_payload": {"descricao": "baixar volume"},
        "comando_sugerido_estado": "PENDING_CONFIRM",
        "comando_sugerido_ts": agora,
    }
    atualizacoes = []
    falas = []
    conflito = {
        "conflito": True,
        "status": "aguardando_confirmacao",
        "chave_existente": "preferencia_sugestao:VOLUME",
        "pergunta": "Você prefere 20, mas agora disse 10. Quer substituir?",
    }

    tratado = processar_confirmacao_sugestao({
        "continuidades_get": lambda chave, padrao=None: estado.get(chave, padrao),
        "resetar_sugestao": lambda: None,
        "interpretar_contraproposta": lambda *_: {
            "intent": "VOLUME", "params": {"nivel_volume": 10},
        },
        "registrar_preferencia_sugestao": lambda *_: conflito,
        "continuidades_update": lambda **dados: atualizacoes.append(dados),
        "falar": lambda texto, *_: falas.append(texto),
    }, "não, prefiro deixar em 10")

    assert tratado is True
    assert atualizacoes[-1]["comando_sugerido"] == "LEARN_CONFLICT"
    assert atualizacoes[-1]["comando_sugerido_estado"] == "PENDING_CONFIRM"
    assert "Quer substituir" in falas[-1]


def test_revisao_de_inatividade_nao_aplica_o_mesmo_decaimento_duas_vezes() -> None:
    pasta, memoria = _memoria_temporaria()
    base = datetime(2025, 1, 1, 12, 0)
    agora = base + timedelta(days=120)
    try:
        memoria.registrar_evidencia_aprendizado(
            chave="rotina:antiga", tipo="rotina", escopo="geral",
            valor={"descricao_humana": "abre o editor"}, sinal=1.0,
            origem="observacao",
        )
        _envelhecer(memoria, "rotina:antiga", base)
        assert memoria.revisar_hipoteses_aprendizado(agora=agora, inatividade_dias=30) == 1
        primeira = memoria.obter_hipotese_aprendizado("rotina:antiga")["confianca"]

        assert memoria.revisar_hipoteses_aprendizado(agora=agora, inatividade_dias=30) == 0
        segunda = memoria.obter_hipotese_aprendizado("rotina:antiga")["confianca"]
        assert segunda == primeira
    finally:
        pasta.cleanup()


def test_preferencia_semantica_antiga_nao_reaparece_no_prompt_com_confianca_original() -> None:
    pasta, memoria = _memoria_temporaria()
    try:
        memoria.salvar_aprendizado_semantico(
            tipo="preferencia", gatilho="volume para jogar", valor="20 por cento",
            regra="Pedro prefere volume baixo para jogar.", confianca=0.95,
            origem="usuario", status="ativo", confirmado_usuario=True,
        )
        conn = memoria._conectar()
        try:
            antigo = (datetime.now() - timedelta(days=2000)).isoformat(" ")
            conn.execute(
                "UPDATE aprendizados_semanticos SET atualizado_em = ? WHERE tipo = 'preferencia'",
                (antigo,),
            )
            conn.commit()
        finally:
            conn.close()

        assert memoria.buscar_aprendizados_relevantes("qual volume para jogar?") == []
    finally:
        pasta.cleanup()
