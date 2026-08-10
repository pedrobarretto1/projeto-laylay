from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.execucao_ia import CoordenadorExecRuntime
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.integracao.composicao_entrada_interacao import (
    criar_composicao_entrada_interacao_runtime,
)
from mente_laylay.integracao.registro_memoria_pessoas import registrar_memoria_pessoas
from mente_laylay.integracao.registro_iot import registrar_iot
from mente_laylay.especialistas.area_transferencia import (
    AreaTransferenciaRuntime,
    classificar_conteudo_para_aprendizado,
)
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime


class ClipboardFalso:
    def __init__(self, texto=""):
        self.texto = texto

    def ler(self):
        return self.texto

    def escrever(self, texto):
        self.texto = texto


def criar_runtime(texto="Texto original", resposta_llm="Texto transformado"):
    clipboard = ClipboardFalso(texto)
    falas = []
    execucoes = []
    registros = []
    resultados = []
    aprendizados = []
    observacoes = []
    runtime = AreaTransferenciaRuntime(
        falar=lambda fala, *_: falas.append(fala),
        enviar_mensagem=lambda *_args, **_kwargs: resposta_llm,
        executar_intencao=lambda resultado, pedido: execucoes.append((resultado, pedido)) or True,
        registrar_operacao=lambda *args, **kwargs: registros.append((args, kwargs)),
        registrar_resultado=lambda *args, **kwargs: resultados.append((args, kwargs)),
        aprender_conteudo=lambda conteudo, pedido: aprendizados.append((conteudo, pedido)) or True,
        observar_conteudo=lambda classificacao: observacoes.append(classificacao) or True,
        leitor=clipboard.ler,
        escritor=clipboard.escrever,
        log=lambda *_: None,
    )
    runtime._resultados_teste = resultados
    runtime._aprendizados_teste = aprendizados
    runtime._observacoes_teste = observacoes
    return runtime, clipboard, falas, execucoes, registros


def test_nao_intercepta_conversa_sem_referencia_ao_clipboard():
    runtime, *_ = criar_runtime()
    assert runtime.processar("corrige esse texto") is False


def test_le_texto_somente_quando_solicitado():
    runtime, _clipboard, falas, _execucoes, registros = criar_runtime("um texto curto")
    assert runtime.processar("o que tem na área de transferência?") is True
    assert "um texto curto" in falas[-1]
    assert registros[-1][1]["intencao"] == "CLIPBOARD_READ"


def test_link_e_exibido_sem_query_sensivel():
    runtime, _clipboard, falas, *_ = criar_runtime(
        "https://exemplo.com/pagina?origem=teste"
    )
    assert runtime.processar("qual o conteúdo do link copiado?") is True
    assert "https://exemplo.com/pagina" in falas[-1]
    assert "origem=" not in falas[-1]


def test_segredo_nao_e_lido_nem_enviado_para_llm():
    chamadas = []
    clipboard = ClipboardFalso("API_KEY=segredo-super-secreto-123")
    falas = []
    runtime = AreaTransferenciaRuntime(
        falar=lambda fala, *_: falas.append(fala),
        enviar_mensagem=lambda *args, **kwargs: chamadas.append((args, kwargs)),
        leitor=clipboard.ler,
        escritor=clipboard.escrever,
        log=lambda *_: None,
    )
    assert runtime.processar("resume o que eu copiei") is True
    assert "sensível" in falas[-1]
    assert chamadas == []


def test_correcao_nao_substitui_clipboard_automaticamente():
    runtime, clipboard, falas, _execucoes, registros = criar_runtime(
        "eu foi", "Eu fui."
    )
    assert runtime.processar("corrige o texto que eu copiei") is True
    assert clipboard.texto == "eu foi"
    assert "copia o resultado" in falas[-1]
    assert registros[-1][1]["intencao"] == "CLIPBOARD_TRANSFORM"


def test_maiusculas_sao_transformadas_localmente_sem_resposta_antiga():
    chamadas_llm = []
    clipboard = ClipboardFalso("texto Misto")
    falas = []
    runtime = AreaTransferenciaRuntime(
        falar=lambda fala, *_: falas.append(fala),
        enviar_mensagem=lambda *_args, **_kwargs: chamadas_llm.append(True),
        leitor=clipboard.ler,
        escritor=clipboard.escrever,
        log=lambda *_: None,
    )

    assert runtime.processar("coloca o que eu copiei em letras maiúsculas") is True
    assert chamadas_llm == []
    assert falas[-1].startswith("TEXTO MISTO")
    assert "TEXTO MISTO. Se quiser" in falas[-1]
    assert clipboard.texto == "texto Misto"

    assert runtime.processar("copia o resultado") is True
    assert clipboard.texto == "TEXTO MISTO"


def test_uso_explicito_silencia_oferta_passiva_do_mesmo_conteudo():
    consumidos = []
    clipboard = ClipboardFalso("um texto grande de teste")
    runtime = AreaTransferenciaRuntime(
        falar=lambda *_args: None,
        leitor=clipboard.ler,
        escritor=clipboard.escrever,
        marcar_consumido=lambda snapshot: consumidos.append(dict(snapshot)),
        log=lambda *_: None,
    )

    assert runtime.processar("o que eu copiei?") is True
    assert len(consumidos) == 1
    assert consumidos[0]["assinatura"]


def test_confirmacao_explicita_copia_e_desfazer_restaura_original():
    runtime, clipboard, falas, *_ = criar_runtime("eu foi", "Eu fui.")
    runtime.processar("corrige o texto que eu copiei")
    assert runtime.processar("copia o resultado") is True
    assert clipboard.texto == "Eu fui."
    assert "guardei o original" in falas[-1]

    assert runtime.processar("desfaz a alteração da área de transferência") is True
    assert clipboard.texto == "eu foi"


def test_nao_sobrescreve_conteudo_copiado_depois_da_transformacao():
    runtime, clipboard, falas, *_ = criar_runtime("original", "corrigido")
    runtime.processar("corrige o texto que eu copiei")
    clipboard.texto = "conteúdo novo"
    assert runtime.processar("copia o resultado") is True
    assert clipboard.texto == "conteúdo novo"
    assert "não vou sobrescrever" in falas[-1].casefold()


def test_pesquisa_erro_copiado_pelo_executor_existente():
    runtime, _clipboard, _falas, execucoes, registros = criar_runtime(
        "ValueError: invalid volume"
    )
    assert runtime.processar("pesquisa esse erro que eu copiei") is True
    assert execucoes[-1][0] == {
        "intent": "SEARCH",
        "params": {"query": "ValueError: invalid volume"},
    }
    assert registros[-1][1]["intencao"] == "CLIPBOARD_SEARCH"


def test_abre_apenas_link_http_valido():
    runtime, _clipboard, _falas, execucoes, _registros = criar_runtime(
        "https://example.com/documento"
    )
    assert runtime.processar("abre o link que eu copiei") is True
    assert execucoes[-1][0]["intent"] == "OPEN_URL"
    args, kwargs = runtime._resultados_teste[-1]
    assert args[0] == execucoes[-1][0]
    assert args[1:] == ("abre o link que eu copiei", True)
    assert kwargs == {"origem": "area_transferencia"}


def test_aprendizado_do_clipboard_exige_pedido_explicito():
    runtime, _clipboard, falas, *_ = criar_runtime("Eu prefiro estudar à noite")

    assert runtime.processar("o que eu copiei?") is True
    assert runtime._aprendizados_teste == []

    assert runtime.processar("aprende sobre mim com o que eu copiei") is True
    assert runtime._aprendizados_teste == [(
        "Eu prefiro estudar à noite",
        "aprende sobre mim com o que eu copiei",
    )]
    assert "guardei" in falas[-1].casefold()


def test_classificador_separa_preferencia_de_erro_e_documento():
    preferencia = classificar_conteudo_para_aprendizado("Eu prefiro estudar à noite")
    erro = classificar_conteudo_para_aprendizado("Traceback: ValueError: invalid volume")
    documento = classificar_conteudo_para_aprendizado("A" * 1300)

    assert preferencia["decisao"] == "evidencia"
    assert preferencia["tipo"] == "preferencia_usuario"
    assert erro == {"decisao": "irrelevante", "motivo": "conteudo_tecnico_ou_documental"}
    assert documento == {"decisao": "irrelevante", "motivo": "conteudo_tecnico_ou_documental"}


def test_observacao_automatica_e_seletiva_e_nao_duplica_conteudo():
    runtime, _clipboard, *_ = criar_runtime("Eu gosto de rock progressivo")

    assert runtime.processar("o que eu copiei?") is True
    assert len(runtime._observacoes_teste) == 1
    assert runtime._observacoes_teste[0]["tipo"] == "preferencia_usuario"

    assert runtime.processar("o que eu copiei?") is True
    assert len(runtime._observacoes_teste) == 1


def test_link_vira_apenas_evidencia_agregada_do_dominio():
    resultado = classificar_conteudo_para_aprendizado(
        "https://www.youtube.com/watch?v=abc&list=RDabc"
    )

    assert resultado["decisao"] == "evidencia"
    assert resultado["chave"] == "clipboard:site:youtube.com"
    assert "watch?v=" not in str(resultado)


def test_runtime_prioritario_evitar_llm_e_roteadores_paralelos():
    area, *_ = criar_runtime("conteúdo")
    chamadas = []
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_area_transferencia_runtime": area,
            "detectar_intencao_deterministica": lambda texto: chamadas.append(texto),
        },
        loop_getter=lambda: None,
    )
    assert runtime.processar_prioritarios("o que tem na área de transferência?") is True
    assert chamadas == []


def test_composicao_entrega_continuacao_clipboard_ao_roteador_prioritario():
    chamadas = []

    class MemoriaPessoasNula:
        def processar(self, _texto): return False
        def contexto_para_prompt(self, _texto): return ""
        def diagnostico(self): return {}
        def retrato_para_mente(self, _texto=""): return {}
        def reexecutar(self, _resultado, _texto): return False

    class IoTNulo:
        def detectar(self, _texto, _estado=None): return None
        def executar(self, _resultado, _texto=""): return {"handled": False}
        def retrato_para_mente(self, _texto=""): return {"dispositivos": []}

    servicos = {
        "_processar_oferta_area_transferencia_pendente": (
            lambda texto: chamadas.append(texto) or True
        ),
        "_estado_compartilhado_runtime": type(
            "Estado", (), {"mental": {}}
        )(),
        "_registro_memoria_pessoas_runtime": registrar_memoria_pessoas(
            MemoriaPessoasNula()
        ),
        "_registro_iot_runtime": registrar_iot(IoTNulo()),
        "resolver_comando_natural": lambda _texto, _origem: (None, ""),
    }
    composicao = criar_composicao_entrada_interacao_runtime(
        servicos=servicos,
        estado_mental_getter=lambda: {},
        sites_diretos={},
        apps_map={},
    )
    comandos, _chat = composicao.conectar(
        servicos=servicos,
        loop_getter=lambda: None,
        estado_chat_getter=lambda: {},
        memoria_sqlite=None,
    )

    assert comandos.processar_prioritarios("quero sim") is True
    assert chamadas == ["quero sim"]
    assert (
        "_processar_oferta_area_transferencia_pendente"
        in composicao.servicos_interacao_registrados
    )


def test_confirmacao_prioritaria_acontece_depois_da_criacao_do_turno():
    prioridade = []
    turnos = []
    contexto = {
        "marcar_inicio_turno": lambda texto: turnos.append(texto),
        "obter_turno_atual": lambda: {},
        "processar_comandos_prioritarios": (
            lambda texto: prioridade.append(texto) or True
        ),
        "enviar_mensagem": lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("a LLM não deveria ser chamada")
        ),
    }
    resposta = RespostaIARuntime(
        contexto_getter=lambda: contexto,
        log=lambda *_args: None,
    )

    coordenador = CoordenadorExecRuntime(
        contexto_exec_getter=lambda: None,
        resposta_ia_getter=lambda: resposta,
        loop_getter=lambda: None,
        log=lambda *_args: None,
    )

    thread = coordenador.agendar("quero sim")
    thread.join(timeout=2)

    assert turnos == ["quero sim"]
    assert prioridade == ["quero sim"]


def test_mapa_de_habilidades_conhece_area_de_transferencia():
    mapa = MapaHabilidadesRuntime().snapshot()
    dominio = mapa["dominios"]["area_transferencia"]
    assert dominio["estado"] == "disponivel"
    assert "CLIPBOARD_READ" in dominio["intents"]
    assert "CLIPBOARD_WRITE" in dominio["intents"]
