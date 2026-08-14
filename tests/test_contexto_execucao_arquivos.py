from __future__ import annotations

import os
import shutil
import time

import pytest

from mente_laylay.arquivos.contexto_execucao import (
    item_local_existe,
    registrar_arquivo,
    resolver_caminho_local,
    resolver_referencia_arquivo_contextual,
)
from mente_laylay.arquivos.execucao_arquivos import executar_intencao_arquivos
from mente_laylay.arquivos.transacao_arquivos import ResultadoTransacaoArquivo
from mente_laylay.autonomia.analise_comandos import processar_comandos_em_cadeia
from mente_laylay.arquivos.mutacoes import criar_arquivos_mutacao_runtime
from mente_laylay.integracao.registro_mutacoes_arquivos import registrar_arquivos_mutacao
from mente_laylay.arquivos import lixeira_laylay
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.memoria_mental.contexto_imediato import (
    resolver_comando_arquivo_contextual,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.memoria_mental.pendencia_acao import (
    CHAVE_PENDENCIA_ACAO,
    PendenciaAcaoRuntime,
)
from mente_laylay.integracao.adaptadores_aplicacao_runtime import (
    AdaptadoresAplicacaoRuntime,
)
from mente_laylay.autonomia import pre_fluxo_contextual


def _mutacoes(**callbacks):
    return registrar_arquivos_mutacao(criar_arquivos_mutacao_runtime(**callbacks))


def _pendencia_lixeira(estado: dict) -> PendenciaAcaoRuntime:
    def atualizar(mutador):
        novo = mutador(dict(estado))
        estado.clear()
        estado.update(novo)
        return dict(estado)

    return PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        log=lambda *_args: None,
    )


def test_referencia_pronominal_prefere_caminho_confirmado_da_estrutura(tmp_path) -> None:
    caminho = tmp_path / "teste.md"
    caminho.write_text("ok", encoding="utf-8")
    ctx = {
        "ultimo_alvo": "teste",
        "ultima_pasta_contextual": lambda: "",
        "ultimo_arquivo_contextual": lambda: "teste",
        "estrutura_arquivo_recente": lambda: {
            "tipo": "arquivo",
            "arquivo_nome": "teste.md",
            "caminho": str(caminho),
        },
        "resolver_caminho": lambda valor: valor,
    }

    assert resolver_referencia_arquivo_contextual(
        ctx, "ele", "arquivo",
    ) == str(caminho)


def test_quero_ele_de_volta_sem_exclusao_confirmada_nao_restaura() -> None:
    resultado = detectar_intencao_arquivos(
        "quero ele de volta",
        params_cb=lambda **kwargs: kwargs,
        estado_mental={},
    )
    assert resultado is None


def test_quero_ele_de_volta_vincula_exclusao_confirmada_recente(tmp_path) -> None:
    arquivo = tmp_path / "teste natural.txt"
    estado = {
        "ultima_acao_ts": time.time(),
        "ultima_acao_alvo": str(arquivo),
        "ultima_acao_contrato": {
            "intent": "CONFIRM_DELETE_ITEM",
            "status": "movido_para_lixeira",
            "alvo": str(arquivo),
            "executou": True,
            "confirmado": True,
        },
    }

    assert detectar_intencao_arquivos(
        "quero ele de volta",
        params_cb=lambda **kwargs: kwargs,
        estado_mental=estado,
    ) == {
        "intent": "RESTORE_DELETED_ITEM",
        "params": {
            "alvo": str(arquivo),
            "referencia_exclusao_confirmada": True,
        },
    }


def test_referencia_explicita_nao_e_substituida_pela_memoria() -> None:
    ctx = {
        "ultima_pasta_contextual": lambda: "C:/antiga",
        "ultimo_arquivo_contextual": lambda: "C:/antigo.txt",
    }

    assert resolver_referencia_arquivo_contextual(
        ctx, "C:/pedido/novo.txt", "arquivo"
    ) == "C:/pedido/novo.txt"


def test_pronome_de_pasta_prioriza_ultima_pasta_contextual() -> None:
    ctx = {
        "ultima_pasta_contextual": lambda: "C:/projeto",
        "ultimo_arquivo_contextual": lambda: "C:/projeto/notas.txt",
        "estrutura_arquivo_recente": lambda: {"pasta": "C:/estrutura"},
    }

    assert resolver_referencia_arquivo_contextual(ctx, "essa", "pasta") == "C:/projeto"


def test_pronome_de_arquivo_prioriza_ultimo_arquivo_contextual() -> None:
    ctx = {
        "ultima_pasta_contextual": lambda: "C:/projeto",
        "ultimo_arquivo_contextual": lambda: "C:/projeto/notas.txt",
        "estrutura_arquivo_recente": lambda: {"arquivo": "rascunho"},
    }

    assert resolver_referencia_arquivo_contextual(
        ctx, "esse arquivo", "arquivo"
    ) == "C:/projeto/notas.txt"


def test_estrutura_recente_completa_extensao_txt_do_arquivo() -> None:
    ctx = {
        "ultima_pasta_contextual": lambda: "",
        "ultimo_arquivo_contextual": lambda: "",
        "estrutura_arquivo_recente": lambda: {
            "arquivo_nome": "contexto",
            "tipo": "arquivo",
            "tipo_arquivo": "texto",
        },
    }

    assert resolver_referencia_arquivo_contextual(
        ctx, "ele", "arquivo"
    ) == "contexto.txt"


def test_estrutura_recente_preserva_arquivo_sem_extensao(tmp_path) -> None:
    arquivo = tmp_path / "teste governança"
    arquivo.write_text("preservar nome real", encoding="utf-8")
    ctx = {
        "ultima_pasta_contextual": lambda: "",
        "ultimo_arquivo_contextual": lambda: "",
        "estrutura_arquivo_recente": lambda: {
            "arquivo_nome": arquivo.name,
            "caminho": str(arquivo),
            "tipo": "arquivo",
            "tipo_arquivo": "",
        },
    }

    assert resolver_referencia_arquivo_contextual(
        ctx, "ele", "arquivo"
    ) == str(arquivo)


def test_resolver_caminho_preserva_valor_se_callback_falhar() -> None:
    ctx = {
        "resolver_caminho": lambda _valor: (_ for _ in ()).throw(
            RuntimeError("resolver indisponível")
        )
    }

    assert resolver_caminho_local(ctx, " caminho relativo ") == "caminho relativo"


def test_item_local_existe_respeita_tipo_de_arquivo_e_pasta(tmp_path) -> None:
    pasta = tmp_path / "pasta"
    pasta.mkdir()
    arquivo = pasta / "nota.txt"
    arquivo.write_text("teste", encoding="utf-8")

    assert item_local_existe({}, str(pasta), "pasta") is True
    assert item_local_existe({}, str(pasta), "arquivo") is False
    assert item_local_existe({}, str(arquivo), "arquivo") is True
    assert item_local_existe({}, str(arquivo), "pasta") is False


def test_registro_contextual_repassa_alvo_e_tipo() -> None:
    registros: list[tuple] = []

    registrar_arquivo(
        {"registrar_contexto_arquivo": lambda *args: registros.append(args)},
        "C:/projeto/nota.txt",
        "arquivos",
    )

    assert registros == [("C:/projeto/nota.txt", "arquivos")]


def test_pedido_natural_cria_arquivo_dentro_de_pasta() -> None:
    resultado = detectar_intencao_arquivos(
        "coloca um arquivo de texto chamado carlos dentro de antonio",
        params_cb=lambda **params: params,
        estado_mental={"ultima_acao_intent": "CREATE_FOLDER"},
    )

    assert resultado == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": "carlos",
            "pasta": "antonio",
            "tipo_arquivo": "texto",
        },
    }
    assert detectar_intencao_arquivos(
        "cria uma pasta chamada antonio",
        params_cb=lambda **params: params,
        estado_mental={},
    ) == {"intent": "CREATE_FOLDER", "params": {"nome": "antonio"}}


@pytest.mark.parametrize(
    ("frase", "nome", "conteudo"),
    [
        (
            "cria um arquivo de texto chamado teste e dentro dele escreva voce \u00e8 gay",
            "teste",
            "voce \u00e8 gay",
        ),
        (
            'crie um documento de texto chamado notas e escreva nele "linha um"',
            "notas",
            "linha um",
        ),
        (
            "coloque um arquivo de texto com nome recado contendo ol\u00e1 mundo",
            "recado",
            "ol\u00e1 mundo",
        ),
        (
            "cria um arquivo de texto chamado lembrete e grave comprar caf\u00e9 dentro dele",
            "lembrete",
            "comprar caf\u00e9",
        ),
    ],
)
def test_pedido_composto_cria_arquivo_com_conteudo_sem_confundir_referencia(
    frase: str,
    nome: str,
    conteudo: str,
) -> None:
    assert detectar_intencao_arquivos(
        frase,
        params_cb=lambda **params: params,
        estado_mental={},
    ) == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": nome,
            "conteudo": conteudo,
            "tipo_arquivo": "texto",
        },
    }


def test_nome_com_e_sem_verbo_de_escrita_continua_inteiro() -> None:
    assert detectar_intencao_arquivos(
        "cria um arquivo de texto chamado teste e revis\u00e3o",
        params_cb=lambda **params: params,
        estado_mental={},
    ) == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": "teste e revis\u00e3o",
            "tipo_arquivo": "texto",
        },
    }


def test_pedido_composto_executa_criacao_e_escrita_no_mesmo_arquivo(tmp_path) -> None:
    frase = "cria um arquivo de texto chamado teste e dentro dele escreva voce \u00e8 gay"
    roteado = detectar_intencao_arquivos(
        frase,
        params_cb=lambda **params: params,
        estado_mental={},
    )
    assert roteado is not None
    resultados: list[tuple[str, bool | None]] = []

    def resolver(valor: str) -> str:
        caminho = str(valor or "")
        return caminho if os.path.isabs(caminho) else str(tmp_path / caminho)

    def criar(caminho: str, conteudo: str, _modo: str) -> bool:
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
        return True

    tratado = executar_intencao_arquivos(
        roteado["intent"],
        roteado["params"],
        "pc_a",
        {
            "falar_com_lipsync": lambda *_args: None,
            "criar_ou_editar_arquivo": criar,
            "_registrar_estrutura_arquivo_recente": lambda _dados: None,
        },
        texto_original=frase,
        marcar_resultado=lambda status, executou, **_kwargs: resultados.append(
            (status, executou)
        ),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda caminho, _tipo: os.path.isfile(caminho),
        resolver_caminho_local=resolver,
        resolver_referencia_arquivo_contextual=lambda alvo, _tipo: alvo,
        arquivos_mutacao=_mutacoes(
            resolver_caminho_cb=resolver,
            criar_arquivo_cb=criar,
        ),
    )

    arquivo = tmp_path / "teste.txt"
    assert tratado is True
    assert arquivo.read_text(encoding="utf-8") == "voce \u00e8 gay"
    assert resultados[-1] == ("arquivo_criado", True)


def test_pronome_dela_resolve_ultima_pasta_criada() -> None:
    resultado = detectar_intencao_arquivos(
        "coloca um arquivo de texto chamado exemplo dentro dela",
        params_cb=lambda **params: params,
        estado_mental={
            "ultima_acao_intent": "CREATE_FOLDER",
            "ultima_acao_params": {"nome": "teste laylay"},
        },
    )

    assert resultado == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": "exemplo",
            "pasta": "teste laylay",
            "tipo_arquivo": "texto",
        },
    }


def test_continuidade_de_arquivo_escreve_localiza_e_abre_o_mesmo_caminho(tmp_path) -> None:
    arquivo = tmp_path / "teste manutenção" / "exemplo.txt"
    arquivo.parent.mkdir()
    arquivo.write_text("", encoding="utf-8")
    estado = {
        "ultima_estrutura_arquivo_params": {
            "tipo": "arquivo",
            "arquivo_nome": "exemplo.txt",
            "caminho": str(arquivo),
        },
    }

    assert detectar_intencao_arquivos(
        'Escreve "teste concluído" nele.',
        params_cb=lambda **params: params,
        estado_mental=estado,
    ) == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": str(arquivo),
            "conteudo": "teste concluído",
            "editar_existente": True,
        },
    }
    assert detectar_intencao_arquivos(
        "Onde ele fica?",
        params_cb=lambda **params: params,
        estado_mental=estado,
    )["params"]["referencia_caminho"] == str(arquivo)
    assert detectar_intencao_arquivos(
        "Qual é o caminho completo dele?",
        params_cb=lambda **params: params,
        estado_mental=estado,
    )["params"] == {
        "query": "exemplo.txt",
        "referencia_caminho": str(arquivo),
        "alvo": "exemplo.txt",
    }
    assert detectar_intencao_arquivos(
        "Abre ele.",
        params_cb=lambda **params: params,
        estado_mental=estado,
    ) == {
        "intent": "FILE_OPEN_RESULT",
        "params": {"caminho": str(arquivo), "alvo": "exemplo.txt"},
    }
    assert detectar_intencao_arquivos(
        "Abre ele e deixa em foco.",
        params_cb=lambda **params: params,
        estado_mental=estado,
    ) == {
        "intent": "FILE_OPEN_RESULT",
        "params": {
            "caminho": str(arquivo),
            "alvo": "exemplo.txt",
            "modo": "focus",
            "referencia_contextual": True,
        },
    }
    assert detectar_intencao_arquivos(
        "Apaga ele.",
        params_cb=lambda **params: params,
        estado_mental=estado,
    ) == {
        "intent": "DELETE_ITEM",
        "params": {"alvo": str(arquivo), "tipo": "arquivo"},
    }


def test_movimentacao_natural_resolve_pasta_criada_sem_entregar_ao_llm(tmp_path) -> None:
    pasta = tmp_path / "carlos"
    estado = {
        "ultima_estrutura_arquivo_params": {
            "tipo": "pasta",
            "nome": "carlos",
            "caminho": str(pasta),
        },
        "ultima_pasta": str(pasta),
    }

    assert detectar_intencao_arquivos(
        "coloca o teste.txt dentro dele",
        params_cb=lambda **params: params,
        estado_mental=estado,
    ) == {
        "intent": "FILE_TRANSACTION",
        "params": {
            "operacao": "mover",
            "origem": "teste.txt",
            "destino": str(pasta),
            "referencia_contextual": True,
        },
    }


@pytest.mark.parametrize(
    ("frase", "origem"),
    [
        ("coloca o teste completo txt dentro dela", "teste completo.txt"),
        ("coloca o teste natural txt dentro dela", "teste natural.txt"),
    ],
)
def test_movimentacao_normalizada_remove_artigo_e_restaura_extensao_txt(
    tmp_path, frase: str, origem: str,
) -> None:
    pasta = tmp_path / "carlos teste"
    estado = {
        "ultima_estrutura_arquivo_params": {
            "tipo": "pasta",
            "nome": "carlos teste",
            "caminho": str(pasta),
        },
        "ultima_pasta": str(pasta),
    }

    resultado = detectar_intencao_arquivos(
        frase,
        params_cb=lambda **params: params,
        estado_mental=estado,
    )

    assert resultado == {
        "intent": "FILE_TRANSACTION",
        "params": {
            "operacao": "mover",
            "origem": origem,
            "destino": str(pasta),
            "referencia_contextual": True,
        },
    }


def test_abertura_por_nome_explicito_usa_caminho_recente_e_basename(tmp_path) -> None:
    arquivo = tmp_path / "teste completo.txt"
    estado = {
        "ultima_estrutura_arquivo_params": {
            "tipo": "arquivo",
            "arquivo_nome": str(arquivo),
            "caminho": str(arquivo),
        },
    }

    assert detectar_intencao_arquivos(
        "Abre o arquivo teste completo txt.",
        params_cb=lambda **params: params,
        estado_mental=estado,
    ) == {
        "intent": "FILE_OPEN_RESULT",
        "params": {"caminho": str(arquivo), "alvo": "teste completo.txt"},
    }

    sem_extensao = tmp_path / "teste natural"
    estado["ultima_estrutura_arquivo_params"] = {
        "tipo": "arquivo",
        "arquivo_nome": sem_extensao.name,
        "caminho": str(sem_extensao),
        "tipo_arquivo": "texto",
    }
    assert detectar_intencao_arquivos(
        "Abre o arquivo teste natural txt.",
        params_cb=lambda **params: params,
        estado_mental=estado,
    ) == {
        "intent": "FILE_OPEN_RESULT",
        "params": {"caminho": str(sem_extensao), "alvo": "teste natural"},
    }


def test_movimentacao_natural_nao_sequestra_criacao_de_arquivo_generico() -> None:
    estado = {
        "ultima_estrutura_arquivo_params": {
            "tipo": "pasta",
            "nome": "carlos",
            "caminho": "C:/Users/teste/Downloads/carlos",
        },
    }

    assert detectar_intencao_arquivos(
        "coloca um arquivo dentro dela",
        params_cb=lambda **params: params,
        estado_mental=estado,
    ) != {
        "intent": "FILE_TRANSACTION",
        "params": {
            "operacao": "mover",
            "origem": "um arquivo",
            "destino": "C:/Users/teste/Downloads/carlos",
            "referencia_contextual": True,
        },
    }


def test_transacao_natural_move_e_rele_destino(tmp_path) -> None:
    origem = tmp_path / "teste.txt"
    destino = tmp_path / "carlos"
    origem.write_text("ok", encoding="utf-8")
    destino.mkdir()
    falas: list[str] = []
    resultados: list[dict] = []
    estruturas: list[dict] = []

    tratado = executar_intencao_arquivos(
        "FILE_TRANSACTION",
        {
            "operacao": "mover",
            "origem": "teste.txt",
            "destino": "carlos",
            "referencia_contextual": True,
        },
        "pc_local",
        {
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "_registrar_estrutura_arquivo_recente": estruturas.append,
        },
        texto_original="coloca o teste.txt dentro dele",
        marcar_resultado=lambda status, executou, **kwargs: resultados.append({
            "status": status,
            "executou": executou,
            **kwargs,
        }),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda caminho, _tipo: os.path.exists(caminho),
        resolver_caminho_local=lambda valor: str(
            valor if os.path.isabs(str(valor)) else tmp_path / str(valor)
        ),
        resolver_referencia_arquivo_contextual=lambda valor, _tipo: valor,
        arquivos_mutacao=_mutacoes(
            resolver_caminho_cb=lambda valor: str(
                valor if os.path.isabs(str(valor)) else tmp_path / str(valor)
            ),
        ),
    )

    movido = destino / "teste.txt"
    assert tratado is True
    assert movido.read_text(encoding="utf-8") == "ok"
    assert not origem.exists()
    assert resultados[-1]["status"] == "movido"
    assert resultados[-1]["confirmado"] is True
    assert resultados[-1]["alvo_resolvido"] == str(movido)
    assert estruturas[-1]["tipo"] == "arquivo"
    assert estruturas[-1]["caminho"] == str(movido)
    assert "Coloquei teste.txt dentro de" in falas[-1]


def test_transacao_natural_informa_arquivo_ausente_sem_cair_na_ia(tmp_path) -> None:
    falas: list[str] = []
    resultados: list[dict] = []

    tratado = executar_intencao_arquivos(
        "FILE_TRANSACTION",
        {
            "operacao": "mover",
            "origem": "tete.txt",
            "destino": "carlos",
        },
        "pc_local",
        {"falar_com_lipsync": lambda fala, *_args: falas.append(fala)},
        texto_original="coloca o tete.txt dentro dele",
        marcar_resultado=lambda status, executou, **kwargs: resultados.append({
            "status": status,
            "executou": executou,
            **kwargs,
        }),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda *_args: False,
        resolver_caminho_local=lambda valor: str(tmp_path / str(valor)),
        resolver_referencia_arquivo_contextual=lambda valor, _tipo: valor,
        arquivos_mutacao=_mutacoes(
            transacionar_cb=lambda params: ResultadoTransacaoArquivo(
                False,
                "origem_nao_encontrada",
                origem=str(params.get("origem") or ""),
            ),
        ),
    )

    assert tratado is True
    assert resultados[-1]["status"] == "origem_nao_encontrada"
    assert resultados[-1]["executou"] is False
    assert resultados[-1]["confirmado"] is False
    assert falas[-1].endswith("Não encontrei tete.txt, então não movi nada.")
    assert "origem_nao_encontrada" not in falas[-1]


def test_cadeia_real_cria_pasta_e_move_arquivo_na_segunda_etapa(tmp_path) -> None:
    origem = tmp_path / "teste.txt"
    origem.write_text("conteúdo", encoding="utf-8")
    estado: dict = {}
    resultados: list[str] = []

    def resolver(valor: str) -> str:
        bruto = str(valor or "")
        return bruto if os.path.isabs(bruto) else str(tmp_path / bruto)

    def transacionar(params: dict) -> ResultadoTransacaoArquivo:
        origem_local = str(params.get("origem") or "")
        pasta_local = str(params.get("destino") or "")
        destino_local = os.path.join(pasta_local, os.path.basename(origem_local))
        shutil.move(origem_local, destino_local)
        return ResultadoTransacaoArquivo(
            True, "movido", origem_local, destino_local,
        )

    mutacoes = _mutacoes(
        resolver_caminho_cb=resolver,
        criar_pasta_cb=lambda caminho: (
            os.makedirs(resolver(caminho), exist_ok=True) or True
        ),
        transacionar_cb=transacionar,
    )

    def executar_trecho(trecho: str, _origem: str) -> bool:
        comando = detectar_intencao_arquivos(
            trecho,
            params_cb=lambda **params: params,
            estado_mental=estado,
        )
        if not comando:
            return False
        return executar_intencao_arquivos(
            comando["intent"],
            comando["params"],
            "pc_local",
            {
                "falar_com_lipsync": lambda *_args: None,
                "_registrar_estrutura_arquivo_recente": lambda dados: (
                    estado.__setitem__("ultima_estrutura_arquivo_params", dict(dados))
                    or estado.__setitem__("ultima_pasta", str(dados.get("caminho") or ""))
                ),
            },
            texto_original=trecho,
            marcar_resultado=lambda status, _executou, **_kwargs: resultados.append(status),
            registrar_arquivo=lambda *_args: None,
            item_local_existe=lambda caminho, _tipo: os.path.exists(resolver(caminho)),
            resolver_caminho_local=resolver,
            resolver_referencia_arquivo_contextual=lambda valor, _tipo: valor,
            arquivos_mutacao=mutacoes,
        )

    assert processar_comandos_em_cadeia(
        "cria uma pasta chamada carlos e coloca o teste.txt dentro dele",
        origem="teste-real",
        executar_trecho=executar_trecho,
    ) is True
    assert (tmp_path / "carlos" / "teste.txt").read_text(encoding="utf-8") == "conteúdo"
    assert resultados == ["pasta_criada", "movido"]


def test_abertura_de_arquivo_com_foco_aguarda_e_confirma_janela(tmp_path) -> None:
    arquivo = tmp_path / "teste.txt"
    arquivo.write_text("ok", encoding="utf-8")
    falas: list[str] = []
    resultados: list[dict] = []
    alvos_foco: list[str] = []
    esperas: list[float] = []

    class Leitura:
        def abrir(self, caminho: str) -> bool:
            return caminho == str(arquivo)

    def focar(alvo: str) -> bool:
        alvos_foco.append(alvo)
        return len(alvos_foco) >= 3

    tratado = executar_intencao_arquivos(
        "FILE_OPEN_RESULT",
        {
            "caminho": str(arquivo),
            "alvo": str(arquivo),
            "modo": "focus",
        },
        "pc_local",
        {
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "focar_janela_app": focar,
            "_aguardar_foco_arquivo": esperas.append,
        },
        texto_original="abre ele e deixa em foco",
        marcar_resultado=lambda status, executou, **kwargs: resultados.append({
            "status": status,
            "executou": executou,
            **kwargs,
        }),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda *_args: True,
        resolver_caminho_local=lambda valor: valor,
        resolver_referencia_arquivo_contextual=lambda valor, _tipo: valor,
        arquivos_leitura=Leitura(),
    )

    assert tratado is True
    assert alvos_foco == ["teste.txt", "teste.txt", "teste.txt"]
    assert esperas == [0.08, 0.14]
    assert resultados == [{
        "status": "arquivo_aberto_focado",
        "executou": True,
        "alvo_resolvido": str(arquivo),
        "confirmado": True,
    }]
    assert "janela na frente" in falas[-1].casefold()


def test_abertura_de_arquivo_nao_inventa_foco_quando_janela_nao_confirma(tmp_path) -> None:
    arquivo = tmp_path / "teste.txt"
    arquivo.write_text("ok", encoding="utf-8")
    falas: list[str] = []
    resultados: list[dict] = []

    class Leitura:
        def abrir(self, _caminho: str) -> bool:
            return True

    tratado = executar_intencao_arquivos(
        "FILE_OPEN_RESULT",
        {
            "caminho": str(arquivo),
            "alvo": "teste.txt",
            "modo": "focus",
        },
        "pc_local",
        {
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "focar_janela_app": lambda _alvo: False,
            "_aguardar_foco_arquivo": lambda _segundos: None,
        },
        texto_original="abre ele e deixa em foco",
        marcar_resultado=lambda status, executou, **kwargs: resultados.append({
            "status": status,
            "executou": executou,
            **kwargs,
        }),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda *_args: True,
        resolver_caminho_local=lambda valor: valor,
        resolver_referencia_arquivo_contextual=lambda valor, _tipo: valor,
        arquivos_leitura=Leitura(),
    )

    assert tratado is True
    assert resultados == [{
        "status": "arquivo_aberto_sem_foco",
        "executou": True,
        "alvo_resolvido": str(arquivo),
        "confirmado": False,
    }]
    assert "mas não consegui confirmar" in falas[-1].casefold()
    assert "deixei a janela na frente" not in falas[-1].casefold()


def test_pesquisa_de_arquivos_remove_caminhos_duplicados(tmp_path) -> None:
    arquivo = tmp_path / "controlador.py"
    arquivo.write_text("# luz", encoding="utf-8")
    falas: list[str] = []

    class Leitura:
        def pesquisar(self, *_args, **_kwargs):
            item = {
                "caminho": str(arquivo),
                "nome": "controlador.py",
                "motivos": ["conteúdo"],
            }
            return {"ok": True, "resultados": [item, dict(item)]}

    tratado = executar_intencao_arquivos(
        "FILE_SEARCH",
        {"query": "código que controla a lâmpada"},
        "pc_a",
        {
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "_registrar_estrutura_arquivo_recente": lambda _dados: None,
        },
        texto_original="encontra o código que controla a lâmpada",
        marcar_resultado=lambda *_args, **_kwargs: None,
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda *_args: False,
        resolver_caminho_local=lambda valor: valor,
        resolver_referencia_arquivo_contextual=lambda valor, _tipo: valor,
        arquivos_leitura=Leitura(),
        arquivos_mutacao=_mutacoes(),
    )

    assert tratado is True
    assert len(falas) == 1
    assert "Encontrei controlador.py" in falas[0]
    assert "2 arquivos" not in falas[0]


def test_escrita_nomeada_reaproveita_caminho_contextual_do_arquivo(tmp_path) -> None:
    arquivo = tmp_path / "teste manutenção" / "exemplo.txt"
    estado = {
        "ultima_estrutura_arquivo_params": {
            "tipo": "arquivo",
            "arquivo_nome": "exemplo.txt",
            "caminho": str(arquivo),
        },
    }

    resultado = detectar_intencao_arquivos(
        "escreve teste concluido dentro do exemplo.txt",
        params_cb=lambda **params: params,
        estado_mental=estado,
    )

    assert resultado == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": str(arquivo),
            "conteudo": "teste concluido",
            "editar_existente": True,
        },
    }


def test_executor_atualiza_arquivo_existente_sem_criar_outro(tmp_path) -> None:
    arquivo = tmp_path / "exemplo.txt"
    arquivo.write_text("antigo", encoding="utf-8")
    resultados: list[tuple[str, bool | None]] = []

    def criar(caminho: str, conteudo: str, _modo: str) -> bool:
        with open(caminho, "w", encoding="utf-8") as stream:
            stream.write(conteudo)
        return True

    tratado = executar_intencao_arquivos(
        "CREATE_FILE",
        {
            "alvo": str(arquivo),
            "conteudo": "teste concluído",
            "editar_existente": True,
        },
        "pc_a",
        {
            "falar_com_lipsync": lambda *_args: None,
            "_registrar_estrutura_arquivo_recente": lambda _dados: None,
        },
        texto_original='escreve "teste concluído" nele',
        marcar_resultado=lambda status, executou, **_kwargs: resultados.append((status, executou)),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda caminho, tipo: os.path.isfile(caminho) if tipo == "arquivo" else os.path.exists(caminho),
        resolver_caminho_local=lambda valor: str(valor),
        resolver_referencia_arquivo_contextual=lambda alvo, _tipo: alvo,
        arquivos_mutacao=_mutacoes(
            resolver_caminho_cb=lambda valor: str(valor),
            criar_arquivo_cb=criar,
        ),
    )

    assert tratado is True
    assert arquivo.read_text(encoding="utf-8") == "teste concluído"
    assert resultados[-1] == ("conteudo_atualizado", True)


def test_escreve_uma_segunda_linha_acrescenta_sem_apagar_conteudo(tmp_path) -> None:
    arquivo = tmp_path / "teste completo.txt"
    arquivo.write_text("teste concluído com sucesso", encoding="utf-8")
    estado = {
        "ultima_estrutura_arquivo_params": {
            "tipo": "arquivo",
            "arquivo_nome": arquivo.name,
            "caminho": str(arquivo),
        },
    }
    comando = detectar_intencao_arquivos(
        "Escreve uma segunda linha nele.",
        params_cb=lambda **params: params,
        estado_mental=estado,
    )
    assert comando == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": str(arquivo),
            "conteudo": "uma segunda linha",
            "editar_existente": True,
            "modo_escrita": "append",
        },
    }

    modos: list[str] = []
    estruturas: list[dict] = []
    resultados: list[tuple[str, bool | None]] = []

    def escrever(caminho: str, conteudo: str, modo: str) -> bool:
        modos.append(modo)
        with open(caminho, modo, encoding="utf-8") as stream:
            stream.write(conteudo)
        return True

    tratado = executar_intencao_arquivos(
        comando["intent"],
        comando["params"],
        "pc_local",
        {
            "falar_com_lipsync": lambda *_args: None,
            "_registrar_estrutura_arquivo_recente": estruturas.append,
        },
        texto_original="Escreve uma segunda linha nele.",
        marcar_resultado=lambda status, executou, **_kwargs: resultados.append(
            (status, executou)
        ),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda caminho, tipo: (
            os.path.isfile(caminho) if tipo == "arquivo" else os.path.exists(caminho)
        ),
        resolver_caminho_local=lambda valor: str(valor),
        resolver_referencia_arquivo_contextual=lambda alvo, _tipo: alvo,
        arquivos_mutacao=_mutacoes(
            resolver_caminho_cb=lambda valor: str(valor),
            criar_arquivo_cb=escrever,
        ),
    )

    assert tratado is True
    assert modos == ["a"]
    assert arquivo.read_text(encoding="utf-8") == (
        "teste concluído com sucesso\numa segunda linha"
    )
    assert estruturas[-1]["arquivo_nome"] == "teste completo.txt"
    assert estruturas[-1]["caminho"] == str(arquivo)
    assert resultados[-1] == ("conteudo_acrescentado", True)


def test_executor_aceita_contrato_ia_e_combina_pasta_com_arquivo(tmp_path) -> None:
    pasta = tmp_path / "antonio"
    pasta.mkdir()
    falas: list[str] = []
    resultados: list[tuple[str, bool | None]] = []

    def resolver(valor: str) -> str:
        caminho = str(valor or "")
        return caminho if os.path.isabs(caminho) else str(tmp_path / caminho)

    def criar(caminho: str, conteudo: str, _modo: str) -> bool:
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
        return True

    tratado = executar_intencao_arquivos(
        "CREATE_FILE",
        {"nome_arquivo": "carlos", "tipo_arquivo": "texto", "pasta": "antonio"},
        "pc_a",
        {
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "criar_ou_editar_arquivo": criar,
            "resolver_caminho": resolver,
            "_registrar_estrutura_arquivo_recente": lambda _dados: None,
        },
        texto_original="coloca um arquivo de texto chamado carlos dentro de antonio",
        marcar_resultado=lambda status, executou: resultados.append((status, executou)),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda caminho, tipo: os.path.isfile(caminho) if tipo == "arquivo" else os.path.exists(caminho),
        resolver_caminho_local=resolver,
        resolver_referencia_arquivo_contextual=lambda alvo, _tipo: alvo,
        arquivos_mutacao=_mutacoes(
            resolver_caminho_cb=resolver,
            criar_arquivo_cb=criar,
        ),
    )

    assert tratado is True
    assert (pasta / "carlos.txt").is_file()
    assert resultados[-1] == ("arquivo_criado", True)
    assert len(falas) == 1
    assert "carlos.txt" in falas[0]
    assert "antonio" in falas[0]


def test_criacao_de_arquivo_sem_extensao_registra_caminho_e_tipo(tmp_path) -> None:
    estruturas: list[dict] = []
    registros: list[tuple[str, str]] = []

    def resolver(valor: str) -> str:
        caminho = str(valor or "")
        return caminho if os.path.isabs(caminho) else str(tmp_path / caminho)

    def criar(caminho: str, conteudo: str, _modo: str) -> bool:
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
        return True

    tratado = executar_intencao_arquivos(
        "CREATE_FILE",
        {"alvo": "teste governança"},
        "pc_local",
        {
            "falar_com_lipsync": lambda *_args: None,
            "criar_ou_editar_arquivo": criar,
            "_registrar_estrutura_arquivo_recente": estruturas.append,
        },
        texto_original="cria um arquivo chamado teste governança",
        marcar_resultado=lambda *_args: None,
        registrar_arquivo=lambda caminho, tipo: registros.append((caminho, tipo)),
        item_local_existe=lambda caminho, _tipo: os.path.isfile(caminho),
        resolver_caminho_local=resolver,
        resolver_referencia_arquivo_contextual=lambda alvo, _tipo: alvo,
        arquivos_mutacao=_mutacoes(
            resolver_caminho_cb=resolver,
            criar_arquivo_cb=criar,
        ),
    )

    caminho = str(tmp_path / "teste governança")
    assert tratado is True
    assert os.path.isfile(caminho)
    assert registros == [(caminho, "arquivo")]
    assert estruturas == [{
        "arquivo_nome": "teste governança",
        "caminho": caminho,
        "pasta": "",
        "tipo": "arquivo",
        "tipo_arquivo": "",
        "target": "pc_local",
    }]


def test_criacao_de_pasta_registra_caminho_exato_para_continuidade(tmp_path) -> None:
    estruturas: list[dict] = []

    def resolver(valor: str) -> str:
        caminho = str(valor or "")
        return caminho if os.path.isabs(caminho) else str(tmp_path / caminho)

    tratado = executar_intencao_arquivos(
        "CREATE_FOLDER",
        {"nome": "teste"},
        "pc_a",
        {
            "falar_com_lipsync": lambda *_args: None,
            "criar_pasta": lambda caminho: (os.makedirs(resolver(caminho), exist_ok=True) is None),
            "resolver_caminho": resolver,
            "_registrar_estrutura_arquivo_recente": estruturas.append,
        },
        texto_original="cria uma pasta chamada teste",
        marcar_resultado=lambda *_args: None,
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda caminho, _tipo: os.path.isdir(resolver(caminho)),
        resolver_caminho_local=resolver,
        resolver_referencia_arquivo_contextual=lambda alvo, _tipo: alvo,
        arquivos_mutacao=_mutacoes(
            resolver_caminho_cb=resolver,
            criar_pasta_cb=lambda caminho: (
                os.makedirs(resolver(caminho), exist_ok=True) is None
            ),
        ),
    )

    assert tratado is True
    assert estruturas[-1]["nome"] == "teste"
    assert estruturas[-1]["tipo"] == "pasta"
    assert estruturas[-1]["caminho"] == str(tmp_path / "teste")


def test_nome_curto_completa_delete_item_que_pediu_alvo() -> None:
    resultado = resolver_comando_arquivo_contextual(
        "antonio",
        mente_integrada_estado={
            "ultima_acao_intent": "DELETE_ITEM",
            "ultima_acao_params": {},
            "ultima_acao_status": "alvo_ausente",
            "ultima_habilidade": "arquivos",
            "ts": time.time(),
        },
        estrutura_recente={},
    )

    assert resultado == {"intent": "DELETE_ITEM", "params": {"alvo": "antonio"}}


@pytest.mark.parametrize(
    ("resposta", "intent_esperada"),
    [
        ("sim", "CONFIRM_DELETE_ITEM"),
        ("não", "CANCEL_DELETE_ITEM"),
        ("não, deixa como está", "CANCEL_DELETE_ITEM"),
        ("melhor deixar como está", "CANCEL_DELETE_ITEM"),
        ("não apaga isso", "CANCEL_DELETE_ITEM"),
        ("cancela isso por favor", "CANCEL_DELETE_ITEM"),
    ],
)
def test_confirmacao_da_lixeira_vence_conversa_generica(
    monkeypatch, resposta: str, intent_esperada: str,
) -> None:
    chamadas: list[dict] = []
    monkeypatch.setattr(
        pre_fluxo_contextual, "existe_exclusao_pendente", lambda: True,
    )
    tratado, etapa = pre_fluxo_contextual.processar_resposta_pendencia_prioritaria(
        {
            "mente_integrada_estado": {"pendencia_atual": {}},
            "_executar_intencao_curta_contextual": lambda intent, *_args, **_kwargs: (
                chamadas.append(intent) or True
            ),
        },
        resposta,
    )

    assert tratado is True
    assert chamadas == [{"intent": intent_esperada, "params": {}}]
    assert etapa in {"confirmacao_exclusao", "cancelamento_exclusao"}


def test_confirmacao_positiva_de_outro_assunto_nao_apaga_item(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chamadas: list[dict] = []
    monkeypatch.setattr(
        pre_fluxo_contextual, "existe_exclusao_pendente", lambda: True,
    )

    tratado, etapa = pre_fluxo_contextual.processar_resposta_pendencia_prioritaria(
        {
            "mente_integrada_estado": {"pendencia_atual": {}},
            "_executar_intencao_curta_contextual": lambda intent, *_args, **_kwargs: (
                chamadas.append(intent) or True
            ),
        },
        "pode falar",
    )

    assert tratado is False
    assert etapa == ""
    assert chamadas == []


@pytest.mark.parametrize(
    "resposta",
    (
        "não, deixa como está",
        "melhor deixar como está",
        "não apaga isso",
        "cancela isso por favor",
    ),
)
def test_roteador_de_arquivos_reutiliza_recusa_natural_canonica(
    monkeypatch: pytest.MonkeyPatch,
    resposta: str,
) -> None:
    monkeypatch.setattr(
        "mente_laylay.arquivos.roteador_arquivos.existe_exclusao_pendente",
        lambda: True,
    )

    resultado = detectar_intencao_arquivos(
        resposta,
        params_cb=lambda **params: params,
        estado_mental={},
    )

    assert resultado == {"intent": "CANCEL_DELETE_ITEM", "params": {}}


def test_recusa_natural_cancela_lixeira_no_fluxo_integrado(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    arquivo = tmp_path / "teste governanca.txt"
    arquivo.write_text("preservar", encoding="utf-8")
    estado_canonico: dict = {}
    runtime_lixeira = lixeira_laylay.LixeiraLaylay(
        str(tmp_path / ".lixeira"),
        pendencia_runtime=_pendencia_lixeira(estado_canonico),
    )
    monkeypatch.setattr(lixeira_laylay, "_RUNTIME", runtime_lixeira)
    pendencia_fisica = runtime_lixeira.mover(str(arquivo), confirmado=False)
    assert pendencia_fisica.status == "aguardando_confirmacao"

    mente = registrar_resultado_execucao(
        {},
        ResultadoAcao(
            intent="DELETE_ITEM",
            status="aguardando_confirmacao",
            alvo=str(arquivo),
            params={"alvo": str(arquivo), "tipo": "arquivo"},
            executou=False,
            confirmado=False,
        ),
        "apaga ele",
        False,
        status="aguardando_confirmacao",
    )
    falas: list[str] = []
    resultados: list[tuple[str, bool | None]] = []

    def executar(intent: dict, texto: str, **_kwargs) -> bool:
        return executar_intencao_arquivos(
            str(intent.get("intent") or ""),
            dict(intent.get("params") or {}),
            "pc_local",
            {"falar_com_lipsync": lambda fala, *_args: falas.append(fala)},
            texto_original=texto,
            marcar_resultado=lambda status, executou: resultados.append((status, executou)),
            registrar_arquivo=lambda *_args: None,
            item_local_existe=lambda *_args: False,
            resolver_caminho_local=lambda valor: valor,
            resolver_referencia_arquivo_contextual=lambda valor, _tipo: valor,
            arquivos_mutacao=_mutacoes(),
        )

    tratado, etapa = pre_fluxo_contextual.processar_resposta_pendencia_prioritaria(
        {
            "mente_integrada_estado": mente,
            "_executar_intencao_curta_contextual": executar,
        },
        "não, deixa como está",
    )

    assert tratado is True
    assert etapa == "cancelamento_exclusao"
    assert arquivo.read_text(encoding="utf-8") == "preservar"
    assert runtime_lixeira.tem_confirmacao_pendente() is False
    assert resultados == [("exclusao_cancelada", False)]
    assert len(falas) == 1
    assert "cancelei" in falas[0].casefold()
    assert "não mexi" in falas[0].casefold()
    assert "não executei nem confirmei" not in falas[0].casefold()


def test_resultado_da_lixeira_nao_cria_pendencia_paralela() -> None:
    canonica = {
        "id": "pendencia-lixeira",
        "origem": "lixeira_laylay",
        "acao": "confirmar_exclusao",
        "status": "ativa",
        "expira_em": time.time() + 90,
    }
    estado = registrar_resultado_execucao(
        {CHAVE_PENDENCIA_ACAO: canonica},
        ResultadoAcao(
            intent="DELETE_ITEM",
            status="aguardando_confirmacao",
            alvo="antonio",
            params={"alvo": "antonio", "tipo": "pasta"},
            executou=False,
            confirmado=False,
        ),
        "apaga a pasta antonio",
        False,
        status="aguardando_confirmacao",
    )

    assert estado.get("pendencia_atual", {}) == {}
    assert estado[CHAVE_PENDENCIA_ACAO] == canonica

    estado = registrar_resultado_execucao(
        estado,
        ResultadoAcao(
            intent="CONFIRM_DELETE_ITEM",
            status="movido_para_lixeira",
            alvo="antonio",
            executou=True,
            confirmado=True,
        ),
        "sim",
        True,
        status="movido_para_lixeira",
    )

    assert estado.get("pendencia_atual", {}) == {}
    assert estado[CHAVE_PENDENCIA_ACAO] == canonica


def test_confirmacao_da_lixeira_preserva_caminho_no_contrato_e_na_fala(tmp_path) -> None:
    caminho = str(tmp_path / "teste capacidade.txt")
    falas: list[str] = []
    resultados: list[dict] = []

    tratado = executar_intencao_arquivos(
        "CONFIRM_DELETE_ITEM",
        {},
        "pc_local",
        {"falar_com_lipsync": lambda fala, *_args: falas.append(fala)},
        texto_original="sim",
        marcar_resultado=lambda status, executou, **kwargs: resultados.append({
            "status": status,
            "executou": executou,
            **kwargs,
        }),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda *_args: False,
        resolver_caminho_local=lambda valor: valor,
        resolver_referencia_arquivo_contextual=lambda valor, _tipo: valor,
        arquivos_mutacao=_mutacoes(
            confirmar_exclusao_cb=lambda: lixeira_laylay.ResultadoLixeira(
                "movido_para_lixeira", True, caminho,
            ),
        ),
    )

    assert tratado is True
    assert resultados == [{
        "status": "movido_para_lixeira",
        "executou": True,
        "alvo_resolvido": caminho,
        "params_resolvidos": {"alvo": caminho},
        "confirmado": True,
    }]
    assert caminho in falas[0]
    assert ";" not in falas[0]
    assert ". Ainda dá para desfazer." in falas[0]

def test_registro_generico_nao_transforma_pendencia_em_execucao_confirmada() -> None:
    class EstadoFalso:
        def __init__(self) -> None:
            self.mental = {
                "plano_turno_atual": {
                    "fase": "tratado_pre_fluxo",
                    "comandos": [{
                        "intent": "DELETE_ITEM",
                        "alvo": "antonio",
                        "status": "aguardando_confirmacao",
                        "executou": False,
                        "confirmado": False,
                    }],
                },
            }

        def atualizar_campos(self, secao: str, **campos) -> None:
            assert secao == "mental"
            self.mental.update(campos)

    estado = EstadoFalso()
    namespace = {
        "_registrar_resultado_execucao_base": lambda *_args, **_kwargs: None,
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": lambda plano, **kwargs: {
            **plano, "comandos": kwargs["comandos"],
        },
        "_concluir_correcao_interpretacao_mente": lambda *_args, **_kwargs: {},
        "print": lambda *_args: None,
    }
    adaptador = AdaptadoresAplicacaoRuntime(lambda: namespace)

    adaptador.registrar_resultado_execucao(
        {"intent": "DELETE_ITEM", "params": {"alvo": "antonio"}},
        "apaga a pasta antonio",
        True,
        origem="deterministico",
    )

    comando = estado.mental["plano_turno_atual"]["comandos"][0]
    assert comando["status"] == "aguardando_confirmacao"
    assert comando["executou"] is False
    assert comando["confirmado"] is False
