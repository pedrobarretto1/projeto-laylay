from __future__ import annotations

import datetime as dt
import json
import time

from mente_laylay.autonomia.comandos_sistema import normalizar_nome_app
from mente_laylay.especialistas.caixa_entrada_pessoal import CaixaEntradaPessoalRuntime
from mente_laylay.memoria_mental.continuidade_geral import selecionar_referente_saliente
from mente_laylay.memoria_mental.continuidade_geral import registrar_evento_continuidade
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime
from mente_laylay.personalidade.continuidade_conversa_natural import (
    resposta_pergunta_curta_dependente_topico,
)


def _caixa(tmp_path, *, mensagens, pendencia=None):
    falas: list[str] = []
    runtime = CaixaEntradaPessoalRuntime(
        caminho=tmp_path / "caixa.json",
        falar=lambda fala, *_args: falas.append(fala),
        registrar_resultado=lambda *_args, **_kwargs: None,
        contexto_getter=lambda: {"messages": mensagens},
        pendencia_runtime=pendencia,
        agora=lambda: dt.datetime(2026, 8, 2, 10, 0),
        log=lambda *_args: None,
    )
    return runtime, falas


def test_p15_detalhamento_transforma_a_fala_imediata_sem_assunto_antigo() -> None:
    chamadas = []
    ctx = {
        "mente_integrada_estado": {
            "ultima_resposta": "Uma skin nebulosa pode deixar o avatar calmo e cósmico.",
            "ultima_opiniao": "usar cores profundas e partículas sutis",
            "assunto_da_fala": "skin nebulosa do avatar",
            "continuidade_fala_ts": time.time(),
        },
        "enviar_mensagem": lambda mensagens, **_kwargs: (
            chamadas.append(mensagens)
            or json.dumps({"fala": "Na skin nebulosa do avatar, as cores profundas formam a base e as partículas sutis criam movimento sem poluir a tela."})
        ),
    }

    fala = resposta_pergunta_curta_dependente_topico(
        ctx, "agora explique com mais detalhes"
    )

    assert "skin nebulosa" in fala.casefold()
    assert "partículas" in fala
    assert chamadas and "fala_anterior" in chamadas[0][1]["content"]


def test_p15_salienca_prefere_pendencia_contrato_e_ultima_acao() -> None:
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "IOT_CONTROL",
            "params": {"acao": "ligar", "alvo": "lampada_quarto"},
            "status": "ligado",
            "executou": True,
            "confirmado": True,
        },
        "liga a luz",
    )
    estado["pendencia_acao_canonica"] = {
        "status": "ativa",
        "expira_em": time.time() + 60,
        "origem": "lixeira_laylay",
        "acao": "confirmar_exclusao",
        "referencia": "arquivo_teste.txt",
        "metadados": {"intent": "CONFIRM_DELETE_ITEM"},
    }

    pendente = selecionar_referente_saliente(estado)
    assert pendente["fonte_salienca"] == "pendencia_canonica"
    assert pendente["alvo"] == "arquivo_teste.txt"

    estado["pendencia_acao_canonica"] = {}
    atual = selecionar_referente_saliente(estado)
    assert atual["fonte_salienca"] == "acao_atual"
    assert atual["alvo"] == "lampada_quarto"


def test_p15_nova_entidade_do_mesmo_dominio_invalida_a_anterior() -> None:
    estado = registrar_evento_continuidade(
        estado_mental_inicial(),
        evento="acao",
        intent="CREATE_FOLDER",
        alvo="rascunhos antigos",
        params={"nome": "rascunhos antigos"},
        status="pasta_criada",
    )
    estado = registrar_evento_continuidade(
        estado,
        evento="acao",
        intent="CREATE_FOLDER",
        alvo="projeto atual",
        params={"nome": "projeto atual"},
        status="pasta_criada",
    )

    referente = selecionar_referente_saliente(estado, dominio="arquivos")
    assert referente["alvo"] == "projeto atual"
    assert "rascunhos" not in json.dumps(referente, ensure_ascii=False)


def test_p15_nome_de_app_remove_repeticao_sem_apagar_o_nome() -> None:
    assert normalizar_nome_app("Opera de novo") == "opera"
    assert normalizar_nome_app("Path of Exile 2 novamente") == "path of exile 2"
    assert normalizar_nome_app("Bloco de Notas outra vez") == "bloco de notas"


def test_p15_caixa_ignora_logs_comandos_e_isola_episodio_atual(tmp_path) -> None:
    mensagens = [
        {"role": "user", "content": "cria uma pasta chamada rascunhos"},
        {"role": "assistant", "content": "🧠 [PLANO:FASE] fase=executado"},
        {"role": "user", "content": "Seria legal criar skins de nebulosa para o avatar"},
        {"role": "assistant", "content": "Podemos usar partículas sutis e tons de azul profundo."},
        {"role": "user", "content": "fecha o navegador"},
        {"role": "assistant", "content": "Entendi a ação que você pediu, mas não executei nem confirmei o resultado."},
    ]
    runtime, _falas = _caixa(tmp_path, mensagens=mensagens)

    assert runtime.processar("salva nossa discussão") is True
    item = json.loads((tmp_path / "caixa.json").read_text(encoding="utf-8"))["itens"][0]
    texto = json.dumps(item, ensure_ascii=False).casefold()
    assert "nebulosa" in texto
    assert "plano:fase" not in texto
    assert "pasta chamada" not in texto
    assert "não executei" not in texto


def test_p15_discussao_ambigua_pede_confirmacao_canonica_antes_de_salvar(tmp_path) -> None:
    estado: dict = {}

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
    mensagens = [
        {"role": "user", "content": "o que você acha?"},
        {"role": "assistant", "content": "Talvez seja uma boa ideia."},
    ]
    runtime, falas = _caixa(tmp_path, mensagens=mensagens, pendencia=pendencia)

    assert runtime.processar("salva nossa discussão") is True
    assert not (tmp_path / "caixa.json").exists()
    assert pendencia.obter()["acao"] == "salvar_discussao"
    assert "Confirma" in falas[-1]

    assert runtime.processar("sim") is True
    assert json.loads((tmp_path / "caixa.json").read_text(encoding="utf-8"))["itens"]
