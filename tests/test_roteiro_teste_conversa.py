from __future__ import annotations

import json
from pathlib import Path
import threading
import time

import pytest

from mente_laylay.integracao.roteiro_teste_conversa import (
    ConfiguracaoRoteiro,
    EspelhoTerminalPersistente,
    RoteiroTesteConversaRuntime,
    carregar_configuracao_roteiro,
    preparar_diretorio_resultado,
)
from mente_laylay.personalidade.terminal_laylay import should_log_message


def test_carrega_lista_e_opcoes_sem_executar_codigo_do_roteiro(tmp_path) -> None:
    roteiro = tmp_path / "roteiro.py"
    roteiro.write_text(
        "COMANDOS = ['oi lay', 'como você está?']\n"
        "TIMEOUT_RESPOSTA_S = 35\n"
        "INTERVALO_ENTRE_COMANDOS_S = 0.25\n"
        "PARAR_SEM_RESPOSTA = False\n"
        "ENCERRAR_AO_FINAL = True\n"
        "raise RuntimeError('não deve executar')\n",
        encoding="utf-8",
    )

    configuracao = carregar_configuracao_roteiro(roteiro)

    assert configuracao == ConfiguracaoRoteiro(
        comandos=("oi lay", "como você está?"),
        atraso_inicial_s=10.0,
        timeout_resposta_s=35.0,
        timeout_voz_s=240.0,
        intervalo_comandos_s=0.25,
        parar_sem_resposta=False,
        encerrar_ao_final=True,
    )


def test_espera_atraso_ativa_e_confirma_chat_antes_do_primeiro_comando(
    tmp_path,
) -> None:
    eventos: list[str] = []
    chat_ativo = {"valor": False}
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def ativar_chat() -> None:
        eventos.append("chat")
        chat_ativo["valor"] = True

    def enviar(_texto: str) -> bool:
        eventos.append("envio")
        holder["runtime"].observar_resposta("resposta pronta")
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("oi lay",),
            atraso_inicial_s=0.03,
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        ativar_modo_chat=ativar_chat,
        modo_chat_ativo_getter=lambda: chat_ativo["valor"],
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime
    iniciou = time.monotonic()

    assert runtime.executar() is True
    assert time.monotonic() - iniciou >= 0.03
    assert eventos == ["chat", "envio"]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["preparacao"] == {
        "status": "modo_chat_confirmado",
        "atraso_inicial_s": 0.03,
    }


def test_nao_envia_comando_quando_modo_chat_nao_e_confirmado(tmp_path) -> None:
    enviados: list[str] = []
    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("não deve sair",),
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=lambda texto: enviados.append(texto) or True,
        resultado_getter=lambda: {},
        ativar_modo_chat=lambda: None,
        modo_chat_ativo_getter=lambda: False,
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )

    assert runtime.executar() is False
    assert enviados == []
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["preparacao"]["status"] == "modo_chat_nao_confirmado"
    assert checkpoint["itens"][0]["status"] == "pendente"


def test_envia_um_turno_por_vez_e_persiste_resposta_antes_do_proximo(tmp_path) -> None:
    enviados: list[str] = []
    checkpoint_antes_do_segundo: list[dict] = []
    runtime_holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str):
        enviados.append(texto)
        if len(enviados) == 2:
            checkpoint_antes_do_segundo.append(json.loads(
                (tmp_path / "checkpoint.json").read_text(encoding="utf-8")
            ))

        def responder() -> None:
            time.sleep(0.015)
            runtime_holder["runtime"].observar_resposta(f"resposta para {texto}")

        thread = threading.Thread(target=responder)
        thread.start()
        return thread

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("primeiro", "segundo"),
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {"fase": "executado"},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    runtime_holder["runtime"] = runtime

    assert runtime.executar() is True
    assert enviados == ["primeiro", "segundo"]
    assert checkpoint_antes_do_segundo[0]["itens"][0]["status"] == "respondido"
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["concluido"] is True
    assert [item["status"] for item in checkpoint["itens"]] == [
        "respondido", "respondido",
    ]
    conversa = runtime.conversa_path.read_text(encoding="utf-8")
    assert conversa.index("primeiro") < conversa.index("resposta para primeiro")
    assert conversa.index("resposta para primeiro") < conversa.index("segundo")
    assert '"fase": "executado"' in conversa


def test_exibe_pergunta_no_terminal_antes_dos_logs_do_turno(tmp_path) -> None:
    logs: list[str] = []
    logs_visiveis: list[str] = []
    ordem: list[str] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def registrar(texto: str) -> None:
        logs.append(texto)
        if should_log_message(texto):
            logs_visiveis.append(texto)
        ordem.append("log")

    def enviar(texto: str) -> bool:
        ordem.append("envio")
        holder["runtime"].observar_resposta(f"resposta para {texto}")
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("qual é o meu nome?",),
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=registrar,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is True
    saida = "\n".join(logs)
    saida_visivel = "\n".join(logs_visiveis)
    bloco = "💬 Você:\n> qual é o meu nome?"
    assert saida.count("💬 Você:") == 1
    assert bloco in saida
    assert bloco in saida_visivel
    assert saida.index(bloco) < saida.index(
        "🧪 [ROTEIRO:001] enviando: qual é o meu nome?"
    )
    assert ordem.index("envio") > ordem.index("log")


def test_sem_resposta_para_e_deixa_proximo_comando_pendente(tmp_path) -> None:
    enviados: list[str] = []
    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("sem resposta", "não deve sair"),
            timeout_resposta_s=0.03,
            intervalo_comandos_s=0.0,
            parar_sem_resposta=True,
        ),
        enviar_entrada=lambda texto: enviados.append(texto) or True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )

    assert runtime.executar() is False
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert enviados == ["sem resposta"]
    assert checkpoint["itens"][0]["status"] == "sem_resposta"
    assert checkpoint["itens"][1]["status"] == "pendente"
    assert "Nenhuma resposta foi observada" in runtime.conversa_path.read_text(
        encoding="utf-8"
    )


def test_proximo_comando_espera_a_voz_terminar(tmp_path) -> None:
    enviados: list[tuple[str, float]] = []
    voz_ocupada = threading.Event()
    voz_terminou_em: list[float] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str):
        enviados.append((texto, time.monotonic()))

        def processar() -> None:
            holder["runtime"].observar_resposta(f"resposta {texto}")
            voz_ocupada.set()

            def reproduzir() -> None:
                time.sleep(0.08)
                voz_terminou_em.append(time.monotonic())
                voz_ocupada.clear()

            threading.Thread(target=reproduzir).start()

        thread = threading.Thread(target=processar)
        thread.start()
        return thread

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("um", "dois"),
            timeout_resposta_s=1.0,
            timeout_voz_s=1.5,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        voz_ocupada_getter=voz_ocupada.is_set,
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is True
    assert [texto for texto, _ts in enviados] == ["um", "dois"]
    assert enviados[1][1] >= voz_terminou_em[0]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["itens"][0]["voz_observada"] is True
    assert checkpoint["itens"][0]["voz_concluida"] is True


def test_voz_que_nao_termina_interrompe_roteiro(tmp_path) -> None:
    enviados: list[str] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str):
        enviados.append(texto)
        holder["runtime"].observar_resposta("resposta pronta")
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("um", "dois"),
            timeout_resposta_s=1.0,
            timeout_voz_s=0.05,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        voz_ocupada_getter=lambda: bool(enviados),
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is False
    assert enviados == ["um"]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["itens"][0]["status"] == "voz_nao_finalizada"
    assert checkpoint["itens"][1]["status"] == "pendente"


def test_primeiro_comando_tambem_espera_fala_inicial(tmp_path) -> None:
    voz_ocupada = threading.Event()
    voz_ocupada.set()
    fala_inicial_terminou = {"valor": 0.0}
    enviado_em: list[float] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def liberar_fala_inicial() -> None:
        time.sleep(0.06)
        fala_inicial_terminou["valor"] = time.monotonic()
        voz_ocupada.clear()

    threading.Thread(target=liberar_fala_inicial).start()

    def enviar(_texto: str):
        enviado_em.append(time.monotonic())
        holder["runtime"].observar_resposta("pronto")
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("primeiro",),
            timeout_resposta_s=1.0,
            timeout_voz_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        voz_ocupada_getter=voz_ocupada.is_set,
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is True
    assert enviado_em[0] >= fala_inicial_terminou["valor"]


def test_retomada_pula_turno_ja_respondido(tmp_path) -> None:
    comandos = ("já foi", "continua daqui")
    diretorio = preparar_diretorio_resultado(
        tmp_path / "roteiro.py", raiz=tmp_path / "resultados",
    )
    runtime_inicial = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(comandos=comandos),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=diretorio,
        log=lambda *_args: None,
    )
    runtime_inicial._atualizar_item(  # noqa: SLF001 - prepara checkpoint real
        0, status="respondido", resposta="pronto",
    )
    enviados: list[str] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str):
        enviados.append(texto)
        holder["runtime"].observar_resposta("resposta retomada")
        return True

    retomado = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=comandos,
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        diretorio_resultado=diretorio,
        retomar=True,
        log=lambda *_args: None,
    )
    holder["runtime"] = retomado

    assert retomado.executar() is True
    assert enviados == ["continua daqui"]


def test_retomada_reconstroi_referencia_com_consultas_seguras(tmp_path) -> None:
    comandos = (
        "Encontra o código e abre o primeiro resultado",
        "Onde esse arquivo fica?",
        "Fecha ele.",
        "O que eu copiei?",
    )
    inicial = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(comandos=comandos),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    inicial._atualizar_item(0, status="respondido", resposta="aberto")  # noqa: SLF001
    inicial._atualizar_item(1, status="respondido", resposta="caminho")  # noqa: SLF001
    inicial._atualizar_item(2, status="enviado")  # noqa: SLF001
    enviados: list[str] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str) -> bool:
        enviados.append(texto)
        holder["runtime"].observar_resposta(f"resposta: {texto}")
        return True

    retomado = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=comandos,
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        retomar=True,
        log=lambda *_args: None,
    )
    holder["runtime"] = retomado

    assert retomado.executar() is True
    assert enviados == list(comandos)
    checkpoint = json.loads(retomado.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["retomada_contexto"] == {
        "status": "reconstrucao_programada",
        "inicio": 0,
        "fim": 2,
    }


def test_retomada_nao_refaz_exclusao_para_reconstruir_sim(tmp_path) -> None:
    comandos = ("Apaga o arquivo teste.txt", "Sim")
    inicial = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(comandos=comandos),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    inicial._atualizar_item(0, status="respondido", resposta="confirma?")  # noqa: SLF001
    inicial._atualizar_item(1, status="enviado")  # noqa: SLF001
    enviados: list[str] = []
    retomado = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(comandos=comandos, intervalo_comandos_s=0.0),
        enviar_entrada=lambda texto: enviados.append(texto) or True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        retomar=True,
        log=lambda *_args: None,
    )

    assert retomado.executar() is False
    assert enviados == []
    checkpoint = json.loads(retomado.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["retomada_contexto"]["status"] == (
        "contexto_nao_reconstruivel_com_seguranca"
    )


def test_espelho_terminal_confirma_conteudo_no_disco(tmp_path) -> None:
    class Saida:
        encoding = "utf-8"

        def __init__(self) -> None:
            self.texto = ""

        def write(self, texto: str) -> int:
            self.texto += texto
            return len(texto)

        def flush(self) -> None:
            return None

        def isatty(self) -> bool:
            return False

    original = Saida()
    caminho = tmp_path / "terminal.log"
    espelho = EspelhoTerminalPersistente(original, caminho)
    espelho.write("mensagem enviada\n")
    espelho.write("resposta recebida\n")

    assert original.texto == "mensagem enviada\nresposta recebida\n"
    assert caminho.read_text(encoding="utf-8") == original.texto
    espelho.fechar()


def test_retomada_recusa_checkpoint_de_outro_roteiro(tmp_path) -> None:
    primeiro = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(comandos=("um",)),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    assert primeiro.checkpoint_path.is_file()

    with pytest.raises(ValueError, match="roteiro mudou"):
        RoteiroTesteConversaRuntime(
            ConfiguracaoRoteiro(comandos=("outro",)),
            enviar_entrada=lambda _texto: True,
            resultado_getter=lambda: {},
            diretorio_resultado=tmp_path,
            retomar=True,
            log=lambda *_args: None,
        )
