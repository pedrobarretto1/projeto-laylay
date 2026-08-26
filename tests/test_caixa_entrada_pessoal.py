from __future__ import annotations

import datetime as dt
import json

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.especialistas.caixa_entrada_pessoal import CaixaEntradaPessoalRuntime
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


def criar_runtime(
    tmp_path, *, mensagens=None, clipboard="", observar_item=None,
    enviar_mensagem=None,
):
    falas = []
    resultados = []
    execucoes = []
    instante = dt.datetime(2026, 7, 27, 20, 30)
    estado: dict = {}

    def atualizar(mutador):
        novo = mutador(dict(estado))
        estado.clear()
        estado.update(novo)
        return dict(estado)

    pendencia = PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        agora=lambda: instante.timestamp(),
        log=lambda *_args: None,
    )
    runtime = CaixaEntradaPessoalRuntime(
        caminho=tmp_path / "caixa.json",
        falar=lambda fala, *_args: falas.append(fala),
        registrar_resultado=lambda *args, **kwargs: resultados.append((args, kwargs)),
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        contexto_getter=lambda: {"messages": list(mensagens or [])},
        clipboard_getter=lambda: clipboard,
        observar_item=observar_item,
        enviar_mensagem=enviar_mensagem,
        pendencia_runtime=pendencia,
        agora=lambda: instante,
        log=lambda *_args: None,
    )
    return runtime, falas, resultados, execucoes


def itens_salvos(tmp_path):
    return json.loads((tmp_path / "caixa.json").read_text(encoding="utf-8"))["itens"]


def test_adiciona_e_classifica_ideia_com_persistencia_atomica(tmp_path):
    runtime, falas, resultados, _ = criar_runtime(tmp_path)

    assert runtime.processar("anota essa ideia: criar um modo cinema") is True

    itens = itens_salvos(tmp_path)
    assert len(itens) == 1
    assert itens[0]["tipo"] == "ideia"
    assert itens[0]["conteudo"] == "criar um modo cinema"
    assert itens[0]["status"] == "ativo"
    assert "Guardei como ideia" in falas[-1]
    assert resultados[-1][0][0]["intent"] == "INBOX_ADD"
    assert resultados[-1][0][0]["status"] == "nota_guardada"
    assert resultados[-1][0][0]["confirmado"] is True
    assert resultados[-1][1]["origem"] == "caixa_entrada_pessoal"


def test_guarda_como_ideia_remove_wrapper_do_conteudo(tmp_path) -> None:
    runtime, *_ = criar_runtime(tmp_path)

    assert runtime.processar(
        "Guarda como ideia melhorar os testes da Laylay"
    ) is True

    item = itens_salvos(tmp_path)[0]
    assert item["tipo"] == "ideia"
    assert item["conteudo"] == "melhorar os testes da Laylay"
    assert "guarda como ideia" not in item["conteudo"].casefold()


def test_repetir_a_mesma_ideia_mantem_uma_copia_e_confirma_noop(tmp_path) -> None:
    runtime, falas, resultados, _ = criar_runtime(tmp_path)

    assert runtime.processar("Guarda como ideia melhorar os testes da Laylay") is True
    assert runtime.processar("Guarda como ideia melhorar os testes da Laylay") is True

    assert len(itens_salvos(tmp_path)) == 1
    contrato = resultados[-1][0][0]
    assert contrato["status"] == "nota_ja_guardada"
    assert contrato["executou"] is False
    assert contrato["confirmado"] is True
    assert "uma só cópia" in falas[-1]


def test_composto_essa_ideia_usa_ultimo_item_criado_e_nao_pergunta_historica(
    tmp_path,
) -> None:
    mensagens = [
        {"role": "user", "content": "Quem é o presidente do Brasil?"},
        {"role": "assistant", "content": "Não vou responder sem uma fonte atual."},
    ]
    caixa, falas, *_ = criar_runtime(tmp_path, mensagens=mensagens)
    caixa.processar("Guarda como ideia melhorar os testes da Laylay")
    item_criado = caixa.ultimo_item_criado()
    assert item_criado is not None

    # Uma listagem pode mudar o foco operacional, mas não a referência tipada
    # publicada para uma composição com a agenda.
    caixa.processar("quais ideias eu anotei?")
    comandos_agenda: list[dict] = []

    class Orquestrador:
        @staticmethod
        def processar_caixa_para_agenda(**dados) -> dict:
            comandos_agenda.append(dict(dados["comando_agenda"]))
            return {"ok": True, "status": "plano_confirmado"}

    estado = type("Estado", (), {"mental": {}})()
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "_caixa_entrada_pessoal_runtime": caixa,
        "_orquestrador_cooperativo_runtime": Orquestrador(),
        "resolver_comando_natural": lambda _texto, _origem: ({
            "intent": "AGENDAR_LEMBRETE",
            "params": {"descricao": "dela", "dia": "amanhã", "hora": "11:00"},
        }, "agenda"),
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
        "processar_comandos_em_cadeia": lambda *_args: False,
        "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
    }
    imediato = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert imediato.processar_prioritarios(
        "Guarda essa ideia e me lembra dela amanhã às 11 horas"
    ) is True

    assert len(itens_salvos(tmp_path)) == 1
    assert len(comandos_agenda) == 1
    params = comandos_agenda[0]["params"]
    assert params["descricao"] == "melhorar os testes da Laylay"
    assert params["referencia_nota"] == item_criado["id"]
    assert "presidente" not in str(comandos_agenda).casefold()


def test_composto_essa_ideia_sem_item_criado_nao_usa_pergunta_historica(
    tmp_path,
) -> None:
    mensagens = [{"role": "user", "content": "Quem é o presidente do Brasil?"}]
    caixa, falas, *_ = criar_runtime(tmp_path, mensagens=mensagens)
    chamadas: list[dict] = []

    class Orquestrador:
        @staticmethod
        def processar_caixa_para_agenda(**dados) -> dict:
            chamadas.append(dict(dados))
            return {"ok": True}

    estado = type("Estado", (), {"mental": {}})()
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "_caixa_entrada_pessoal_runtime": caixa,
        "_orquestrador_cooperativo_runtime": Orquestrador(),
        "resolver_comando_natural": lambda *_args: ({
            "intent": "AGENDAR_LEMBRETE", "params": {"descricao": "dela"},
        }, "agenda"),
        "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
    }
    imediato = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert imediato.processar_prioritarios(
        "Guarda essa ideia e me lembra dela amanhã às 11 horas"
    ) is True

    assert chamadas == []
    assert not (tmp_path / "caixa.json").exists()
    assert "recém-guardada" in falas[-1]
    assert "presidente" not in falas[-1].casefold()


def test_essa_ideia_recupera_contexto_anterior_sem_salvar_o_comando(tmp_path):
    mensagens = [
        {"role": "user", "content": "Seria legal criar um modo silencioso para estudar"},
        {"role": "assistant", "content": "Gostei da ideia."},
    ]
    runtime, *_ = criar_runtime(tmp_path, mensagens=mensagens)

    assert runtime.processar("anota essa ideia") is True

    item = itens_salvos(tmp_path)[0]
    assert item["conteudo"] == "Seria legal criar um modo silencioso para estudar"
    assert item["origem"] == "conversa"


def test_essa_ideia_junto_com_sugestoes_salva_a_discussao_real(tmp_path) -> None:
    mensagens = [
        {"role": "user", "content": "Quero uma aparência espacial para o avatar."},
        {
            "role": "assistant",
            "content": "Eu usaria cinza metálico, estrelas discretas e olhos lilás.",
        },
    ]
    runtime, *_ = criar_runtime(tmp_path, mensagens=mensagens)

    assert runtime.processar("Guarda essa ideia junto com suas sugestões") is True

    item = itens_salvos(tmp_path)[0]
    assert item["tipo"] == "ideia_discutida"
    assert "junto com suas sugestões" not in item["conteudo"].casefold()
    assert runtime.ultimo_item_salvo()["id"] == item["id"]


def test_anota_essa_ideia_com_ponto_recupera_fala_anterior(tmp_path) -> None:
    mensagens = [
        {
            "role": "user",
            "content": "Acho que seria legal criar uma nova aparência para o avatar.",
        },
        {"role": "assistant", "content": "Quer que eu sugira algo rápido?"},
    ]
    runtime, *_ = criar_runtime(tmp_path, mensagens=mensagens)

    assert runtime.processar("Anota essa ideia.") is True

    item = itens_salvos(tmp_path)[0]
    assert item["conteudo"] == (
        "Acho que seria legal criar uma nova aparência para o avatar."
    )
    assert item["origem"] == "conversa"


def test_anota_essa_ideia_salva_proposta_e_sugestao_em_vez_da_continuacao_curta(
    tmp_path,
) -> None:
    mensagens = [
        {
            "role": "user",
            "content": "Acho que seria legal criar uma aparência espacial para o avatar.",
        },
        {
            "role": "assistant",
            "content": "Interessante! Quer que eu sugira um estilo ou cores pra começar?",
        },
        {"role": "user", "content": "quero um estilo"},
        {
            "role": "assistant",
            "content": (
                "Talvez algo com luzes suaves, bordas leves e um olho que "
                "brilha como estrela. Tipo um ser do espaço com um toque de humor."
            ),
        },
    ]
    runtime, *_ = criar_runtime(tmp_path, mensagens=mensagens)

    assert runtime.processar("Anota essa ideia.") is True

    item = itens_salvos(tmp_path)[0]
    assert item["tipo"] == "ideia_discutida"
    assert item["ideia_original"] == (
        "Acho que seria legal criar uma aparência espacial para o avatar."
    )
    assert item["conteudo"] != "quero um estilo"
    assert item["sugestoes_laylay"] == [
        "Talvez algo com luzes suaves, bordas leves e um olho que brilha como estrela."
    ]
    assert item["origem"] == "conversa_resumida"


def test_anota_ideia_reconhece_estilo_direto_como_sugestao_da_laylay(
    tmp_path,
) -> None:
    mensagens = [
        {
            "role": "user",
            "content": "Acho que seria legal criar uma aparência espacial para o avatar.",
        },
        {
            "role": "assistant",
            "content": (
                "Espacial? Como um drone de colete com luvas de neblina? "
                "Tá, mas só se for com cara de eu sei o que estou fazendo."
            ),
        },
        {"role": "user", "content": "Quero um estilo."},
        {
            "role": "assistant",
            "content": (
                "Cinza metálico com reflexos de estrelas, como se fosse um robô "
                "que só falava em frases curtas e com sotaque de outro planeta."
            ),
        },
    ]
    runtime, *_ = criar_runtime(tmp_path, mensagens=mensagens)

    assert runtime.processar("Anota essa ideia.") is True

    item = itens_salvos(tmp_path)[0]
    assert item["tipo"] == "ideia_discutida"
    assert item["ideia_original"].startswith(
        "Acho que seria legal criar uma aparência espacial"
    )
    assert item["sugestoes_laylay"] == [
        (
            "Cinza metálico com reflexos de estrelas, como se fosse um robô "
            "que só falava em frases curtas e com sotaque de outro planeta."
        ),
    ]
    assert item["conteudo"] != "Quero um estilo."


def test_guarda_isso_para_amanha_usa_contexto_e_data_de_revisao(tmp_path):
    mensagens = [{"role": "user", "content": "Pesquisar um microfone melhor"}]
    runtime, *_ = criar_runtime(tmp_path, mensagens=mensagens)

    assert runtime.processar("guarda isso para eu ver amanhã") is True

    item = itens_salvos(tmp_path)[0]
    assert item["conteudo"] == "Pesquisar um microfone melhor"
    assert item["revisar_em"] == "2026-07-28"


def test_link_copiado_e_salvo_somente_quando_referenciado(tmp_path):
    link = "https://example.com/artigo?tema=python"
    runtime, *_ = criar_runtime(tmp_path, clipboard=link)

    assert runtime.processar("salva esse link copiado nas minhas anotações") is True

    item = itens_salvos(tmp_path)[0]
    assert item["tipo"] == "link"
    assert item["conteudo"] == link
    assert item["origem"] == "clipboard"


def test_segredo_nao_e_persistido(tmp_path):
    runtime, falas, *_ = criar_runtime(tmp_path, clipboard="API_KEY=segredo-super-secreto-123")

    assert runtime.processar("salva o texto copiado nas minhas anotações") is True

    assert not (tmp_path / "caixa.json").exists()
    assert "sensível" in falas[-1]


def test_lista_ideias_da_semana_sem_expor_excluidas(tmp_path):
    runtime, falas, *_ = criar_runtime(tmp_path)
    runtime.processar("anota essa ideia: melhorar a busca")
    runtime.processar("anota a tarefa comprar café")

    assert runtime.processar("quais ideias eu anotei esta semana?") is True

    assert "melhorar a busca" in falas[-1]
    assert "comprar café" not in falas[-1]


def test_exclusao_exige_confirmacao_e_e_soft_delete(tmp_path):
    runtime, falas, resultados, _ = criar_runtime(tmp_path)
    runtime.processar("anota essa ideia: testar a caixa")

    assert runtime.processar("apaga essa nota") is True
    assert itens_salvos(tmp_path)[0]["status"] == "ativo"
    assert "Confirma" in falas[-1]

    assert runtime.processar("sim") is True
    assert itens_salvos(tmp_path)[0]["status"] == "excluido"
    assert resultados[-1][0][0]["intent"] == "CONFIRM_INBOX_DELETE"


def test_recusa_mantem_nota_ativa(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)
    runtime.processar("anota essa ideia: manter isto")
    runtime.processar("apaga essa nota")

    assert runtime.processar("não") is True
    assert itens_salvos(tmp_path)[0]["status"] == "ativo"


def test_recusa_natural_composta_mantem_nota_ativa(tmp_path):
    runtime, falas, resultados, _ = criar_runtime(tmp_path)
    runtime.processar("anota essa ideia: manter isto")
    runtime.processar("apaga essa nota")

    assert runtime.processar("não, deixa como está") is True
    assert itens_salvos(tmp_path)[0]["status"] == "ativo"
    assert falas[-1] == "Certo, não alterei a nota."
    assert resultados[-1][0][0]["intent"] == "CANCEL_INBOX_ACTION"


def test_converter_em_lembrete_exige_confirmacao_e_reusa_agenda(tmp_path):
    runtime, falas, resultados, execucoes = criar_runtime(tmp_path)
    runtime.processar("anota a tarefa revisar os testes")

    assert runtime.processar("transforma essa nota em lembrete") is True
    assert execucoes == []
    assert "Confirma" in falas[-1]

    assert runtime.processar("sim") is True
    assert execucoes[-1][0] == {
        "intent": "AGENDAR_LEMBRETE",
        "params": {"descricao": "revisar os testes"},
    }
    assert resultados[-1][0][0]["intent"] == "AGENDAR_LEMBRETE"
    assert itens_salvos(tmp_path)[0]["status"] == "ativo"


def test_converter_em_lembrete_preserva_data_hora_e_descricao(tmp_path):
    runtime, _falas, _resultados, execucoes = criar_runtime(tmp_path)
    runtime.processar("anota a ideia de revisar a interface")

    assert runtime.processar(
        "transforma essa ideia em lembrete para amanhã às 18 horas"
    ) is True
    assert runtime.processar("sim") is True

    assert execucoes[-1] == ({
        "intent": "AGENDAR_LEMBRETE",
        "params": {
            "descricao": "de revisar a interface",
            "hora_alvo": "18:00",
            "data_hora": "amanhã",
        },
    }, "transforma essa ideia em lembrete para amanhã às 18 horas")


def test_runtime_prioritario_intercepta_caixa_sem_chamar_llm(tmp_path):
    caixa, *_ = criar_runtime(tmp_path)
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {"_caixa_entrada_pessoal_runtime": caixa},
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("anota essa ideia: testar prioridade") is True
    assert itens_salvos(tmp_path)[0]["conteudo"] == "testar prioridade"


def test_snapshot_nao_expoe_conteudo_das_notas(tmp_path):
    runtime, *_ = criar_runtime(tmp_path)
    runtime.processar("anota essa ideia: conteúdo privado da nota")

    snapshot = runtime.snapshot()

    assert snapshot["ativos"] == 1
    assert snapshot["tipos"]["ideia"] == 1
    assert "conteúdo privado" not in str(snapshot)


def test_nova_nota_alimenta_aprendizado_agregado(tmp_path):
    observados = []
    runtime, *_ = criar_runtime(tmp_path, observar_item=observados.append)

    runtime.processar("anota essa ideia: melhorar avatar animação")

    assert len(observados) == 1
    assert observados[0]["tipo"] == "ideia"
    assert observados[0]["assuntos"] == ["melhorar", "avatar", "animação"]


def test_tenta_de_novo_repete_listagem_pela_continuidade_oficial(tmp_path):
    caixa, falas, *_ = criar_runtime(tmp_path)
    caixa.processar("anota essa ideia: continuidade da caixa")
    caixa.processar("quais ideias eu anotei?")
    falas.clear()
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_caixa_entrada_pessoal_runtime": caixa,
            "_resolver_repeticao_ultima_acao": lambda texto: {
                "intent": "INBOX_LIST",
                "params": {"filtro": "quais ideias eu anotei"},
            } if texto == "tenta de novo" else None,
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("tenta de novo") is True
    assert "continuidade da caixa" in falas[-1]


def test_listagem_recebe_personalidade_sem_perder_fato(tmp_path):
    def responder(*_args, **_kwargs):
        return json.dumps({
            "fala": "Olha ela aqui, quietinha mas cheia de potencial: 1: ideia — melhorar o avatar",
            "emocao": "debochada",
            "nivel": 2,
        }, ensure_ascii=False)

    runtime, falas, *_ = criar_runtime(tmp_path, enviar_mensagem=responder)
    runtime.processar("anota essa ideia: melhorar o avatar")

    assert runtime.processar("o que tem na minha caixa de entrada?") is True
    assert falas[-1] == "Olha ela aqui, quietinha mas cheia de potencial: 1: ideia — melhorar o avatar"


def test_listagem_recusa_estilo_que_omite_conteudo_real(tmp_path):
    def responder(*_args, **_kwargs):
        return json.dumps({
            "fala": "Sua caixa tem uma ideia misteriosa e maravilhosa.",
            "emocao": "alegre",
            "nivel": 2,
        })

    runtime, falas, *_ = criar_runtime(tmp_path, enviar_mensagem=responder)
    runtime.processar("anota essa ideia: melhorar o avatar")

    assert runtime.processar("o que tem na minha caixa de entrada?") is True
    assert falas[-1] == "Na sua caixa: 1: ideia — melhorar o avatar"


def test_salva_discussao_separando_ideia_e_sugestoes(tmp_path):
    mensagens = [
        {"role": "user", "content": "Acho que seria legal melhorar o avatar"},
        {"role": "assistant", "content": "Podemos adicionar transições suaves entre as emoções."},
        {"role": "user", "content": "Gostei, vamos começar pelas transições."},
        {"role": "assistant", "content": "O próximo passo é escolher as emoções prioritárias."},
    ]
    runtime, falas, resultados, _ = criar_runtime(tmp_path, mensagens=mensagens)

    assert runtime.processar("salva nossa ideia junto com suas sugestões") is True

    item = itens_salvos(tmp_path)[0]
    assert item["tipo"] == "ideia_discutida"
    assert item["ideia_original"] == "Acho que seria legal melhorar o avatar"
    assert item["sugestoes_laylay"] == [
        "Podemos adicionar transições suaves entre as emoções.",
    ]
    assert item["decisoes"] == ["Gostei, vamos começar pelas transições."]
    assert item["proximos_passos"] == ["O próximo passo é escolher as emoções prioritárias."]
    assert item["origem"] == "conversa_resumida"
    assert item["mensagens_consideradas"] == 4
    assert resultados[-1][0][0]["intent"] == "INBOX_ADD_DISCUSSION"
    assert "Guardei nossa discussão" in falas[-1]


def test_discussao_sobre_topico_recorta_assunto_antigo(tmp_path):
    mensagens = [
        {"role": "user", "content": "Quero organizar minha playlist de rock"},
        {"role": "assistant", "content": "Podemos separar as faixas por energia."},
        {"role": "user", "content": "Seria legal melhorar o avatar com movimentos suaves"},
        {"role": "assistant", "content": "No avatar, podemos suavizar a troca dos PNGs."},
    ]
    runtime, *_ = criar_runtime(tmp_path, mensagens=mensagens)

    runtime.processar("anota o que discutimos sobre o avatar")

    item = itens_salvos(tmp_path)[0]
    assert "avatar" in item["titulo"].casefold()
    assert "playlist" not in item["conteudo"].casefold()
    assert item["ideia_original"] == "Seria legal melhorar o avatar com movimentos suaves"


def test_resumo_llm_so_e_aceito_com_autoria_apoiada_na_conversa(tmp_path):
    mensagens = [
        {"role": "user", "content": "Quero um avatar mais expressivo"},
        {"role": "assistant", "content": "Podemos criar uma animação curta de surpresa."},
    ]

    def responder(mensagens_llm, **_kwargs):
        if "Organize uma discussão" not in mensagens_llm[0]["content"]:
            return "{}"
        return json.dumps({
            "titulo": "Avatar mais expressivo",
            "ideia_original": "Quero um avatar mais expressivo",
            "resumo": "Avatar mais expressivo com animação curta de surpresa.",
            "sugestoes_laylay": ["Podemos criar uma animação curta de surpresa."],
            "decisoes": [],
            "proximos_passos": [],
        }, ensure_ascii=False)

    runtime, *_ = criar_runtime(
        tmp_path, mensagens=mensagens, enviar_mensagem=responder,
    )
    runtime.processar("salva nossa discussão")

    item = itens_salvos(tmp_path)[0]
    assert item["resumo"] == "Avatar mais expressivo com animação curta de surpresa."
    assert item["sugestoes_laylay"] == ["Podemos criar uma animação curta de surpresa."]


def test_resumo_llm_inventado_cai_no_resumo_literal(tmp_path):
    mensagens = [
        {"role": "user", "content": "Quero melhorar o avatar"},
        {"role": "assistant", "content": "Podemos suavizar as transições."},
    ]
    resposta_inventada = json.dumps({
        "titulo": "Avatar holográfico",
        "ideia_original": "Quero melhorar o avatar",
        "resumo": "Vamos comprar sensores holográficos amanhã.",
        "sugestoes_laylay": ["Comprar sensores holográficos."],
        "decisoes": [],
        "proximos_passos": [],
    })
    runtime, *_ = criar_runtime(
        tmp_path,
        mensagens=mensagens,
        enviar_mensagem=lambda *_args, **_kwargs: resposta_inventada,
    )

    runtime.processar("salva nossa discussão")

    item = itens_salvos(tmp_path)[0]
    assert "holográfico" not in item["conteudo"]
    assert item["sugestoes_laylay"] == ["Podemos suavizar as transições."]


def test_discussao_com_segredo_nao_e_salva(tmp_path):
    mensagens = [
        {"role": "user", "content": "Minha ideia usa API_KEY=segredo-super-secreto-123"},
        {"role": "assistant", "content": "Não devemos persistir essa chave."},
    ]
    runtime, falas, *_ = criar_runtime(tmp_path, mensagens=mensagens)

    assert runtime.processar("salva nossa discussão") is True

    assert not (tmp_path / "caixa.json").exists()
    assert "sensível" in falas[-1]


def test_conversa_real_de_skins_ignora_claro_e_resposta_de_tentativa_falha(tmp_path):
    mensagens = [
        {"role": "user", "content": "lay, eu tive uma ideia para melhorar o seu avatar"},
        {"role": "assistant", "content": "Conta essa ideia, fiquei curiosa."},
        {"role": "user", "content": "de fazer varias skin para ela, uma medieval, futurista ou cyberpunk, ficaria muito legal nè?"},
        {"role": "assistant", "content": "Posso te ajudar a desenhar uma descrição de cada estilo."},
        {"role": "user", "content": "pode me manda uma descricao"},
        {"role": "assistant", "content": "Claro!"},
        {"role": "user", "content": "quais outras skin voce acha legal fazer?"},
        {"role": "assistant", "content": "Uma com cores de neblina e raios leves, como uma chuva elétrica no oceano."},
        {"role": "user", "content": "guarda minha ideia junto com suas sugestões"},
        {"role": "assistant", "content": "Tô com o notebook aberto só no coração. Essas ideias vão girando lá dentro."},
    ]
    runtime, falas, *_ = criar_runtime(
        tmp_path,
        mensagens=mensagens,
        enviar_mensagem=lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError()),
    )

    assert runtime.processar("guarda minha ideia junto com suas sugestões") is True

    item = itens_salvos(tmp_path)[0]
    assert item["titulo"] == "Skins medieval, futurista e cyberpunk para o avatar"
    assert item["ideia_original"].startswith("de fazer varias skin")
    assert item["resumo"] == (
        "Fazer várias skins para o avatar da Laylay, uma medieval, futurista ou cyberpunk."
    )
    assert item["sugestoes_laylay"] == [
        "Posso te ajudar a desenhar uma descrição de cada estilo.",
        "Uma com cores de neblina e raios leves, como uma chuva elétrica no oceano.",
    ]
    assert "Claro!" not in item["sugestoes_laylay"]
    assert "notebook" not in str(item).casefold()
    assert "2 sugestões" in falas[-1]
    assert "sugestãoões" not in falas[-1]


def test_repetir_salvamento_da_mesma_discussao_nao_duplica(tmp_path):
    mensagens = [
        {"role": "user", "content": "Seria legal criar skins para o avatar"},
        {"role": "assistant", "content": "Podemos começar por uma versão medieval."},
    ]
    runtime, falas, *_ = criar_runtime(tmp_path, mensagens=mensagens)

    runtime.processar("salva nossa discussão")
    runtime.processar("salva nossa discussão")

    assert len(itens_salvos(tmp_path)) == 1
    assert "Não dupliquei" in falas[-1]
