from __future__ import annotations

import json

from memoria_sqlite import MemoriaSQLite

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.especialistas.capacidades import CAPACIDADES
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime
from mente_laylay.integracao.registro_memoria_pessoas import registrar_memoria_pessoas
from mente_laylay.integracao.registro_iot import registrar_iot
from mente_laylay.integracao.composicao_entrada_interacao import (
    ComposicaoEntradaInteracaoRuntime,
)
from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
from mente_laylay.memoria_mental.diagnostico_mente import (
    DiagnosticoMenteRuntime, formatar_diagnostico_terminal,
)
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


def criar_runtime(tmp_path):
    estado = {}
    falas, resultados, aprendizados, mente_curta, revogacoes = [], [], [], [], []

    def atualizar(atualizador):
        novo = atualizador(dict(estado))
        estado.clear()
        estado.update(novo)
        return estado

    pendencia = PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        log=lambda *_args: None,
    )
    runtime = MemoriaPessoasRuntime(
        caminho=tmp_path / "pessoas.json",
        falar=lambda fala, *_args: falas.append(fala),
        pendencia_runtime=pendencia,
        registrar_resultado=lambda *args, **kwargs: resultados.append((args, kwargs)),
        registrar_mente_curta=lambda *args: mente_curta.append(args),
        registrar_aprendizado=lambda **kwargs: aprendizados.append(kwargs),
        esquecer_aprendizado=lambda prefixo: revogacoes.append(prefixo),
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        log=lambda *_args: None,
    )
    return runtime, pendencia, estado, falas, resultados, aprendizados, mente_curta, revogacoes


def dados_salvos(tmp_path):
    return json.loads((tmp_path / "pessoas.json").read_text(encoding="utf-8"))


class _IoTNulo:
    def detectar(self, _texto, _estado=None): return None
    def executar(self, _resultado, _texto=""): return {"handled": False}
    def retrato_para_mente(self, _texto=""): return {"dispositivos": []}


def test_afirmacao_explicita_persiste_relacao_fato_proveniencia_e_aprendizado(tmp_path):
    runtime, _pendencia, estado, _falas, resultados, aprendizados, _mente, _revogacoes = criar_runtime(tmp_path)

    assert runtime.processar("Ana é minha irmã e ela gosta de rock") is False

    pessoa = dados_salvos(tmp_path)["pessoas"][0]
    assert pessoa["nome"] == "Ana"
    assert pessoa["relacoes"][0]["tipo"] == "irmã"
    assert pessoa["relacoes"][0]["fonte"] == "usuario_explicito"
    assert pessoa["fatos"][0]["valor"] == "rock"
    assert resultados[-1][0][0]["intent"] == "PEOPLE_REMEMBER"
    assert aprendizados[-1]["confirmado_usuario"] is True
    assert estado["registro_semantico"]["entidades"]


def test_consulta_natural_e_pronome_usam_memoria_sem_llm(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]
    runtime.processar("Ana é minha irmã e ela gosta de rock")

    assert runtime.processar("o que você sabe sobre Ana?") is True
    assert "Ana é sua irmã" in falas[-1]
    assert "gosta de rock" in falas[-1]

    assert runtime.reexecutar(
        {
            "intent": "PEOPLE_QUERY",
            "params": {"nome": "Ana", "modo": "complemento"},
        },
        "o que mais?",
    ) is True
    assert falas[-1] == (
        "Não tenho outro fato confirmado sobre Ana além do que já te contei."
    )


def test_autorreferencia_mim_nao_vira_pessoa_chamada_mim(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]

    assert runtime.processar("o que voce sabe sobre mim?") is False
    assert falas == []
    if (tmp_path / "pessoas.json").exists():
        assert dados_salvos(tmp_path)["pessoas"] == []


def test_consultas_de_pessoa_toleram_erro_leve_e_ordem_invertida(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]
    runtime.processar("Nanda é minha namorada e ela gosta de rock")

    assert runtime.processar("o que voce abe sobre a Nanda?") is True
    assert "Nanda é sua namorada" in falas[-1]
    assert runtime.processar("qual a relacao da Nanda comigo?") is True
    assert "Nanda é sua namorada" in falas[-1]
    assert runtime.processar("Nanda é minha o que?") is True
    assert "Nanda é sua namorada" in falas[-1]
    assert runtime.processar("o que ela gosta?") is True
    assert "gosta de rock" in falas[-1]


def test_correcao_invalida_relacao_anterior(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)
    runtime.processar("Ana é minha irmã")
    runtime.processar("na verdade Ana é minha prima")

    pessoa = dados_salvos(tmp_path)["pessoas"][0]
    assert [(r["tipo"], r["status"]) for r in pessoa["relacoes"]] == [
        ("irmã", "corrigido"), ("prima", "ativo"),
    ]
    assert runtime.diagnostico()["correcoes"] == 1
    assert "prima" in runtime.contexto_para_prompt("vou encontrar a Ana")
    assert "irmã" not in runtime.contexto_para_prompt("vou encontrar a Ana")


def test_fato_posterior_por_pronome_reusa_a_pessoa_ativa(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]
    runtime.processar("Ana é minha irmã")
    runtime.processar("ela gosta de metal")

    assert runtime.processar("o que ela gosta?") is True
    assert "gosta de metal" in falas[-1]


def test_forma_natural_tenho_uma_amiga_chamada_e_consulta_lembra(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]

    runtime.processar("eu tenho uma amiga chamada Beatriz")

    assert runtime.processar("você lembra da Beatriz?") is True
    assert "Beatriz é sua amiga" in falas[-1]


def test_pedido_de_lembrete_nunca_vira_consulta_de_pessoa(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]

    for texto in (
        "me lembra de beber água",
        "lembra de revisar o código amanhã",
        "me lembra de fazer uma coisa amanhã",
    ):
        assert runtime.processar(texto) is False

    assert falas == []
    assert not (tmp_path / "pessoas.json").exists()


def test_namorada_com_nome_em_oracao_separada_e_fato_continuado(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]

    assert runtime.processar(
        "lay, sabia que eu tenho uma namorada e o nome dela é nanda"
    ) is False
    assert runtime.processar("é sim, e ela gosta de rock") is False

    pessoa = dados_salvos(tmp_path)["pessoas"][0]
    assert pessoa["nome"] == "Nanda"
    assert pessoa["relacoes"][0]["tipo"] == "namorada"
    assert pessoa["fatos"][0]["chave"] == "gosta_de"
    assert pessoa["fatos"][0]["valor"] == "rock"

    assert runtime.processar("o que você sabe sobre minha namorada") is True
    assert "Nanda é sua namorada" in falas[-1]
    assert "gosta de rock" in falas[-1]


def test_relacao_explicita_em_fato_nao_cria_pessoa_chamada_gosta(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]

    runtime.processar("Eu tenho uma namorada e o nome dela é Nanda.")
    runtime.processar("minha namorada gosta de funk")

    pessoas = dados_salvos(tmp_path)["pessoas"]
    assert [pessoa["nome"] for pessoa in pessoas] == ["Nanda"]
    assert pessoas[0]["fatos"][0]["valor"] == "funk"
    assert runtime.processar("o que você sabe sobre minha namorada?") is True
    assert falas[-1] == "Nanda é sua namorada. Você me contou que ela gosta de funk."


def test_preferencia_musical_continuada_guarda_genero_e_artista_sem_substituir(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]

    runtime.processar("Eu tenho uma namorada e o nome dela é Nanda.")
    runtime.processar("ela gosta de rock")
    runtime.processar("ela gosta dos")  # oração incompleta não vira memória
    runtime.processar("não lay, ela gosta dos guns N roses")

    pessoa = dados_salvos(tmp_path)["pessoas"][0]
    fatos = [f for f in pessoa["fatos"] if f["status"] == "ativo"]
    assert [(f["categoria"], f["valor"]) for f in fatos] == [
        ("genero_musical", "rock"),
        ("artista_musical", "Guns N’ Roses"),
    ]
    assert runtime.processar("o que você sabe sobre a minha namorada") is True
    assert falas[-1] == (
        "Nanda é sua namorada. Você me contou que ela gosta de rock e Guns N’ Roses."
    )


def test_contracoes_de_preferencia_reusam_pessoa_ativa(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)
    runtime.processar("Beatriz é minha amiga")

    runtime.processar("ela gosta da anitta")
    runtime.processar("ela gosta do jazz")
    runtime.processar("ela gosta da praia")

    fatos = dados_salvos(tmp_path)["pessoas"][0]["fatos"]
    assert [(f["categoria"], f["valor"]) for f in fatos] == [
        ("artista_musical", "Anitta"),
        ("genero_musical", "jazz"),
        ("preferencia_geral", "praia"),
    ]


def test_memoria_legada_de_gosto_nao_duplica_ao_ser_repetida(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)
    runtime.processar("Ana é minha irmã e ela gosta de rock")
    dados = dados_salvos(tmp_path)
    dados["pessoas"][0]["fatos"][0].pop("categoria")
    (tmp_path / "pessoas.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    runtime.processar("ela gosta de rock")

    fatos = dados_salvos(tmp_path)["pessoas"][0]["fatos"]
    assert len([f for f in fatos if f["status"] == "ativo"]) == 1


def test_consulta_de_pessoa_nao_e_confundida_com_pergunta_de_capacidade() -> None:
    mapa = MapaHabilidadesRuntime()

    assert mapa.dominios_relevantes(
        "o que você sabe sobre minha namorada"
    ) == ("pessoas",)
    assert mapa.responder_pergunta_capacidade(
        "o que você sabe sobre minha namorada"
    ) == ""


def test_hipotese_e_brincadeira_nao_viram_fato(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)
    runtime.processar("talvez Ana seja minha irmã")
    runtime.processar("Ana é minha irmã kkk, brincadeira")

    pessoas = dados_salvos(tmp_path)["pessoas"]
    # A hipótese com "seja" não é promovida e a brincadeira é só observação contextual.
    assert len(pessoas) == 1
    assert pessoas[0]["relacoes"] == []
    assert pessoas[0]["observacoes"][0]["tipo"] == "brincadeira"


def test_pergunta_e_segredo_nao_sao_memorizados(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)

    assert runtime.processar("Ana é minha irmã?") is False
    assert runtime.processar("Ana é minha irmã e a senha=segredo123") is False

    assert not (tmp_path / "pessoas.json").exists()


def test_esquecimento_usa_pendencia_canonica_e_recusa_preserva(tmp_path):
    runtime, pendencia, _estado, _falas, _resultados, aprendizados, _mente, _revogacoes = criar_runtime(tmp_path)
    runtime.processar("Ana é minha irmã")

    assert runtime.processar("esquece tudo sobre Ana") is True
    assert pendencia.obter()["origem"] == "memoria_pessoas"
    assert dados_salvos(tmp_path)["pessoas"][0]["status"] == "ativa"

    assert runtime.processar("não, deixa como está") is True
    assert dados_salvos(tmp_path)["pessoas"][0]["status"] == "ativa"
    assert aprendizados[-1]["valor"]["descricao_humana"].endswith("recusado")


def test_pedido_de_apagar_arquivo_ou_pasta_nunca_vira_esquecimento_de_pessoa(tmp_path):
    runtime, pendencia, *_ = criar_runtime(tmp_path)

    for texto in (
        "apaga o arquivo exemplo",
        "apaga o aquivo exemplo",
        "remove a pasta teste",
        "apaga o documento da Nanda",
    ):
        assert runtime.processar(texto) is False
        assert pendencia.obter() is None


def test_consulta_sem_memoria_declara_ausencia_em_vez_de_inventar(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]

    assert runtime.processar("o que voce sabe sobre a Nanda?") is True
    assert falas[-1] == "Você ainda não me contou nada confiável sobre Nanda."
    assert "Nanda" in runtime.contexto_para_prompt("o que voce sabe sobre a Nanda?")
    assert "não há memória confirmada" in runtime.contexto_para_prompt(
        "o que voce sabe sobre a Nanda?"
    )


def test_esquecimento_confirmado_faz_soft_delete(tmp_path):
    runtime, _pendencia, estado, _falas, _resultados, aprendizados, _mente, revogacoes = criar_runtime(tmp_path)
    runtime.processar("Ana é minha irmã")
    registro = estado["registro_semantico"]
    registro["alegacoes"] = [{
        "id": "alegacao:ana", "sujeito": "Ana", "texto": "Ana gosta de rock",
    }]
    registro["assuntos"] = [{
        "id": "assunto:ana", "titulo": "Ana", "entidade_id": registro["entidade_ativa_id"],
    }]
    registro["assunto_ativo_id"] = "assunto:ana"
    runtime.processar("esquece tudo sobre Ana")

    assert runtime.processar("sim, pode esquecer") is True
    lapide = dados_salvos(tmp_path)["pessoas"][0]
    assert lapide["status"] == "esquecida"
    assert "nome" not in lapide
    assert "relacoes" not in lapide
    assert "Ana" not in json.dumps(dados_salvos(tmp_path), ensure_ascii=False)
    assert "Ana" not in json.dumps(estado.get("registro_semantico"), ensure_ascii=False)
    assert runtime.diagnostico()["ativas"] == 0
    assert revogacoes == [f"pessoa:{lapide['id']}:"]
    assert aprendizados[-1]["valor"]["descricao_humana"].endswith("aceito")


def test_sqlite_revoga_hipotese_e_eventos_do_prefixo_sem_tocar_outros(tmp_path):
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    memoria.registrar_evidencia_aprendizado(
        chave="pessoa:abc:relacao", tipo="pessoa", escopo="pessoas",
        valor={"descricao_humana": "Ana é irmã"}, sinal=1.0,
        origem="usuario", confirmado_usuario=True,
    )
    memoria.registrar_evidencia_aprendizado(
        chave="preferencia:musica", tipo="preferencia", escopo="musica",
        valor={"descricao_humana": "gosta de rock"}, sinal=1.0,
        origem="usuario", confirmado_usuario=True,
    )

    removidos = memoria.esquecer_aprendizado_por_prefixo("pessoa:abc:")

    assert removidos >= 2
    assert memoria.obter_hipotese_aprendizado("pessoa:abc:relacao") is None
    assert memoria.obter_hipotese_aprendizado("preferencia:musica") is not None


def test_homonimos_nao_sao_unificados_nem_escolhidos_no_chute(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]
    runtime.processar("Ana é minha irmã")
    runtime.processar("outra Ana é minha amiga")

    assert len(dados_salvos(tmp_path)["pessoas"]) == 2
    assert runtime.processar("o que você sabe sobre Ana?") is True
    assert "mais de uma possibilidade" in falas[-1]


def test_prompt_recebe_so_pessoa_relevante(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)
    runtime.processar("Ana é minha irmã")
    runtime.processar("Carlos é meu amigo")

    contexto = runtime.contexto_para_prompt("a Ana gosta disso")

    assert "Ana" in contexto
    assert "Carlos" not in contexto
    assert runtime.contexto_para_prompt("qual a previsão do tempo?") == ""


def test_registro_tipado_nao_expoe_persistencia_e_preserva_o_runtime(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)
    registro = registrar_memoria_pessoas(runtime)

    assert registro.servico is runtime
    assert "pessoas.json" not in repr(registro)
    assert "caminho" not in repr(registro).casefold()


def test_fluxo_prioritario_real_intercepta_consulta_antes_da_llm(tmp_path):
    runtime, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]
    runtime.processar("Ana é minha irmã")
    composicao = ComposicaoEntradaInteracaoRuntime(
        servicos={}, estado_mental_getter=dict, sites_diretos={}, apps_map={},
        deteccao_factory=lambda **_kwargs: object(),
        chat_factory=lambda **_kwargs: object(),
    )
    comandos, _chat = composicao.conectar(
            servicos={
                "_registro_memoria_pessoas_runtime": registrar_memoria_pessoas(runtime),
                "_registro_iot_runtime": registrar_iot(_IoTNulo()),
                "resolver_comando_natural": lambda _texto, _origem: (None, ""),
            },
        loop_getter=lambda: None, estado_chat_getter=dict, memoria_sqlite=None,
    )

    assert comandos.processar_prioritarios("quem é Ana?") is True
    assert "Ana é sua irmã" in falas[-1]
    assert "_memoria_pessoas_runtime" not in composicao.servicos_interacao_registrados
    assert composicao.servicos_tipados_registrados == ("iot", "memoria_pessoas")


def test_fluxo_prioritario_real_liga_relacao_fato_e_consulta_natural(tmp_path):
    memoria, *_resto = criar_runtime(tmp_path)
    falas = _resto[2]
    comandos = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_responder_pergunta_capacidade_local": (
                MapaHabilidadesRuntime().responder_pergunta_capacidade
            ),
        },
        loop_getter=lambda: None,
        memoria_pessoas=registrar_memoria_pessoas(memoria),
    )

    # Afirmações são observadas sem sequestrar a resposta conversacional.
    assert comandos.processar_prioritarios(
        "lay, sabia que eu tenho uma namorada e o nome dela é nanda"
    ) is False
    assert comandos.processar_prioritarios("é sim, e ela gosta de rock") is False

    # A consulta, ao contrário, é consumida antes da LLM e lê o JSON real.
    assert comandos.processar_prioritarios(
        "o que você sabe sobre minha namorada"
    ) is True
    assert "Nanda é sua namorada" in falas[-1]
    assert "gosta de rock" in falas[-1]


def test_observacao_nao_sequestra_turno_conversacional(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)
    comandos = ComandosImediatosRuntime(
        namespace_getter=dict,
        loop_getter=lambda: None,
        memoria_pessoas=registrar_memoria_pessoas(runtime),
    )

    assert comandos.processar_prioritarios("Ana é minha irmã") is False
    assert dados_salvos(tmp_path)["pessoas"][0]["nome"] == "Ana"


def test_mapa_da_consciencia_da_habilidade_e_da_seguranca():
    mapa = MapaHabilidadesRuntime()

    contexto = mapa.contexto_para_prompt("você lembra das pessoas que eu te apresento?")
    resposta = mapa.responder_pergunta_capacidade(
        "Lay, você consegue lembrar pessoas e relações?"
    )

    assert "- pessoas [disponivel]" in contexto
    assert "proveniência" not in resposta  # fala natural, sem jargão interno
    assert "ficam locais" in resposta
    assert "confirmação" in resposta
    assert CAPACIDADES["PEOPLE_FORGET"]["exige_confirmacao"] is True


def test_adaptador_injeta_contexto_de_pessoa_antes_do_aprendizado(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)
    runtime.processar("Ana é minha irmã")

    class Motor:
        def resumo_para_prompt(self):
            return "APRENDIZADO GERAL"

    namespace = {
        "_resumo_mente_integrada_para_prompt_base": lambda _texto: "MENTE BASE",
        "_motor_aprendizado_runtime": Motor(),
        "print": lambda *_args: None,
    }
    adaptador = AdaptadoresAplicacaoRuntime(lambda: namespace)
    adaptador.conectar_memoria_pessoas(registrar_memoria_pessoas(runtime))

    resumo = adaptador.resumo_mente_integrada_para_prompt("e a Ana?")

    assert "MENTE BASE" in resumo
    assert "MEMÓRIA DE PESSOAS RELEVANTE" in resumo
    assert "Ana é sua irmã" in resumo
    assert "APRENDIZADO GERAL" in resumo


def test_diagnostico_expoe_apenas_metricas_seguras(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)
    runtime.processar("Ana é minha irmã e ela gosta de rock")
    diagnostico = DiagnosticoMenteRuntime(
        estado_getter=lambda: {
            "mental": {}, "conversacional": {}, "percepcao": {}, "continuidades": {},
        },
        saude_getter=lambda: {"memoria_pessoas": {"status": "saudavel"}},
        memoria_pessoas_getter=runtime.diagnostico,
        falar=lambda *_args: None,
        log=lambda *_args: None,
    ).snapshot()

    texto = formatar_diagnostico_terminal(diagnostico)

    assert "memória de pessoas: ativas=1 relações=1 fatos=1" in texto
    assert "Ana" not in texto
    assert "rock" not in texto
    assert diagnostico["memoria_pessoas"]["envio_externo"] is False
