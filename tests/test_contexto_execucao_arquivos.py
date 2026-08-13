from __future__ import annotations

import os
import time

import pytest

from mente_laylay.arquivos.contexto_execucao import (
    item_local_existe,
    registrar_arquivo,
    resolver_caminho_local,
    resolver_referencia_arquivo_contextual,
)
from mente_laylay.arquivos.execucao_arquivos import executar_intencao_arquivos
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


def test_quero_ele_de_volta_restaura_ultima_exclusao() -> None:
    resultado = detectar_intencao_arquivos(
        "quero ele de volta",
        params_cb=lambda **kwargs: kwargs,
        estado_mental={},
    )
    assert resultado == {"intent": "RESTORE_DELETED_ITEM", "params": {}}


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
        "Abre ele.",
        params_cb=lambda **params: params,
        estado_mental=estado,
    ) == {
        "intent": "FILE_OPEN_RESULT",
        "params": {"caminho": str(arquivo), "alvo": "exemplo.txt"},
    }
    assert detectar_intencao_arquivos(
        "Apaga ele.",
        params_cb=lambda **params: params,
        estado_mental=estado,
    ) == {
        "intent": "DELETE_ITEM",
        "params": {"alvo": str(arquivo), "tipo": "arquivo"},
    }


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
