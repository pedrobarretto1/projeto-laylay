from __future__ import annotations

import mente_laylay.autonomia.executor_integracoes as executor_integracoes
import mente_laylay.autonomia.roteador_intencao as roteador
from mente_laylay.autonomia.coordenador_intencao import executar_fluxo_intencao
from mente_laylay.autonomia.analise_comandos import (
    executar_comando_em_texto,
    processar_comandos_em_cadeia,
)
from mente_laylay.autonomia.pre_fluxo_contextual import executar_resultado_contextual
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.memoria_mental.resultado_acao import (
    interpretar_tratamento_operacional,
    marcar_tratamento_operacional,
)


def _rodar(resultado, executar):
    registros = []
    aprendizados = []
    tratado = executar_resultado_contextual(
        {
            "executar_intencao": executar,
            "_registrar_resultado_execucao": (
                lambda *args, **kwargs: registros.append((args, kwargs))
            ),
            "_registrar_autoaprimoramento": (
                lambda *args, **kwargs: aprendizados.append((args, kwargs))
            ),
        },
        resultado,
        "pedido de teste",
        origem_resultado="teste",
        contexto_autoaprimoramento="teste contrato",
        log_rota="TESTE",
    )
    return tratado, registros, aprendizados


def test_intencao_desconhecida_tratada_nao_vira_execucao_ou_sucesso():
    resultado = {"intent": "INTENT_DESCONHECIDA", "params": {}}

    def executar(pedido, texto):
        return roteador.executar_intencao(
            pedido,
            texto,
            {
                "_target_from_params": lambda *_args: "pc_a",
                "falar_com_lipsync": lambda *_args: None,
            },
        )

    tratado, registros, aprendizados = _rodar(resultado, executar)

    assert tratado is True
    assert registros == []
    assert aprendizados == []


def test_bloqueio_de_politica_tratado_nao_vira_execucao_ou_sucesso():
    resultado = {"intent": "APP_OPEN", "params": {"nome_app": "Opera"}}
    def executar(pedido, texto):
        return roteador.executar_intencao(
            pedido,
            texto,
            {
                "_target_from_params": lambda *_args: "pc_a",
                "_bloqueio_por_emocao": lambda *_args: True,
            },
        )

    tratado, registros, aprendizados = _rodar(resultado, executar)

    assert tratado is True
    assert registros == []
    assert aprendizados == []


def test_executor_legado_sem_receipt_preserva_fallback_temporario():
    resultado = {"intent": "LEGADO_TESTE", "params": {}}

    tratado, registros, aprendizados = _rodar(
        resultado,
        lambda _pedido, _texto: True,
    )

    assert tratado is True
    assert len(registros) == 1
    assert registros[0][0][2] is True
    assert len(aprendizados) == 1


class _EstadoAutoFake:
    def __init__(self):
        self.mental = {"autoaprimoramento_estado": {}}

    def obter(self, dominio, chave, padrao=None):
        assert dominio == "mental"
        return self.mental.get(chave, padrao)

    def atualizar_campos(self, dominio, **campos):
        assert dominio == "mental"
        self.mental.update(campos)


def test_autoaprimoramento_central_recusa_sucesso_sem_efeito():
    estado = _EstadoAutoFake()
    runtime = EstadoContextoRuntime(
        namespace_getter=lambda: {},
        estado_runtime_getter=lambda: estado,
    )
    resultado = {"intent": "APP_OPEN", "params": {"nome_app": "Opera"}}
    marcar_tratamento_operacional(
        resultado,
        tratado=True,
        executou=False,
        confirmado=False,
        status="nao_executado_por_politica",
        retorno_legado=True,
    )

    runtime.registrar_autoaprimoramento(
        resultado,
        "abre o Opera",
        True,
        contexto="chamador legado ambiguo",
        origem="teste",
    )

    assert estado.mental["autoaprimoramento_estado"] == {}


def test_efeito_sem_confirmacao_nao_inventa_receipt_mas_conta_tentativa_util():
    resultado = {"intent": "OPEN_URL", "params": {"url": "https://example.com"}}
    marcar_tratamento_operacional(
        resultado,
        tratado=True,
        executou=True,
        confirmado=None,
        status="comando_enviado",
        retorno_legado=True,
    )

    tratamento = interpretar_tratamento_operacional(resultado, True)

    assert tratamento.tratado is True
    assert tratamento.executou is True
    assert tratamento.confirmado is None
    assert tratamento.sucesso_habilidade is False
    assert tratamento.resultado_incerto is True
    assert tratamento.deve_publicar_fallback is False


def test_estado_ja_satisfeito_confirmado_e_sucesso_sem_novo_efeito():
    resultado = {"intent": "IOT_CONTROL", "params": {"acao": "ligar"}}
    marcar_tratamento_operacional(
        resultado,
        tratado=True,
        executou=False,
        confirmado=True,
        status="ja_estava_ligado",
        resultado_publicado=True,
        retorno_legado=False,
    )

    tratamento = interpretar_tratamento_operacional(resultado, False)

    assert tratamento.tratado is True
    assert tratamento.executou is False
    assert tratamento.confirmado is True
    assert tratamento.sucesso_habilidade is True
    assert tratamento.resultado_publicado is True


def test_falha_confirmada_nao_e_sucesso_da_habilidade():
    resultado = {"intent": "APP_OPEN", "params": {"nome_app": "inexistente"}}
    marcar_tratamento_operacional(
        resultado,
        tratado=True,
        executou=False,
        confirmado=False,
        status="nao_encontrado",
        retorno_legado=False,
    )

    tratamento = interpretar_tratamento_operacional(resultado, True)

    assert tratamento.tratado is True
    assert tratamento.executou is False
    assert tratamento.confirmado is False
    assert tratamento.sucesso_habilidade is False


def test_autoaprimoramento_execucao_sem_confirmacao_fica_neutro():
    estado = _EstadoAutoFake()
    runtime = EstadoContextoRuntime(
        namespace_getter=lambda: {},
        estado_runtime_getter=lambda: estado,
    )
    resultado = {"intent": "OPEN_URL", "params": {"url": "https://example.com"}}
    marcar_tratamento_operacional(
        resultado,
        tratado=True,
        executou=True,
        confirmado=None,
        status="comando_enviado",
        retorno_legado=True,
    )

    runtime.registrar_autoaprimoramento(
        resultado,
        "abre example.com",
        True,
        contexto="tentativa sem receipt",
        origem="teste",
    )

    info = estado.mental["autoaprimoramento_estado"]["habilidades"]["navegacao"]
    assert info["tentativas"] == 1
    assert info["sucessos"] == 0
    assert info["falhas"] == 0
    assert info["incertos"] == 1
    assert estado.mental["autoaprimoramento_estado"]["cookie_reforco"] == 0
    assert "sem confirmação" in estado.mental["autoaprimoramento_estado"]["ultimo_resumo"]


def test_cadeia_para_antes_de_dependente_sem_confirmacao_moderno():
    chamadas = []

    def executar_trecho(trecho: str, origem: str) -> bool:
        chamadas.append((trecho, origem))
        resultado = {"intent": "OPEN_URL", "params": {"url": "https://example.com"}}

        def executar(res, _texto):
            marcar_tratamento_operacional(
                res,
                tratado=True,
                executou=True,
                confirmado=None,
                status="comando_enviado",
                retorno_legado=True,
            )
            return True

        return executar_comando_em_texto(
            trecho,
            origem,
            interpretar_comando_local_rapido=lambda _t: resultado,
            executar_intencao=executar,
        )

    tratado = processar_comandos_em_cadeia(
        "abre example.com, maximiza ela",
        "teste-incerto",
        segmentar=lambda *_args, **_kwargs: [
            "abre example.com",
            "maximiza ela",
        ],
        executar_trecho=executar_trecho,
    )

    assert tratado is True
    assert [item[0] for item in chamadas] == ["abre example.com"]



def _tratamento_roteador_real(resultado, texto, extras=None):
    receipts = []
    ctx = {
        "_target_from_params": lambda *_args: "pc_a",
        "_registrar_resultado_execucao": (
            lambda contrato, *_args, **_kwargs: receipts.append(contrato)
        ),
        "falar_com_lipsync": lambda *_args: None,
    }
    if isinstance(extras, dict):
        ctx.update(extras)
    retorno = roteador.executar_intencao(resultado, texto, ctx)
    return interpretar_tratamento_operacional(resultado, retorno), receipts


def test_volume_sem_acao_nao_cai_em_sucesso_legado():
    resultado = {"intent": "VOLUME", "params": {}}

    tratamento, receipts = _tratamento_roteador_real(
        resultado,
        "muda o volume",
    )

    assert tratamento.legado is False
    assert tratamento.tratado is True
    assert tratamento.executou is False
    assert tratamento.confirmado is False
    assert tratamento.status == "acao_invalida"
    assert tratamento.sucesso_habilidade is False
    assert receipts and receipts[-1].status == "acao_invalida"


def test_iot_sem_runtime_e_bloqueio_modal_publicam_nao_execucao():
    ausente = {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "luz"}}
    tratamento_ausente, receipts_ausente = _tratamento_roteador_real(
        ausente,
        "liga a luz",
    )

    assert tratamento_ausente.legado is False
    assert tratamento_ausente.tratado is True
    assert tratamento_ausente.executou is False
    assert tratamento_ausente.confirmado is False
    assert tratamento_ausente.status == "indisponivel"
    assert receipts_ausente and receipts_ausente[-1].status == "indisponivel"

    bloqueado = {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "luz"}}
    tratamento_bloqueado, receipts_bloqueado = _tratamento_roteador_real(
        bloqueado,
        "não liga a luz",
    )

    assert tratamento_bloqueado.legado is False
    assert tratamento_bloqueado.tratado is True
    assert tratamento_bloqueado.executou is False
    assert tratamento_bloqueado.confirmado is False
    assert tratamento_bloqueado.status == "nao_executado_por_politica"
    assert receipts_bloqueado[-1].status == "nao_executado_por_politica"


def test_sugestao_registrada_e_tratamento_sem_efeito_nao_sucesso_legado():
    resultado = {
        "intent": "SUGGEST_ACTION",
        "params": {
            "acao_sugerida": {
                "intent": "IOT_CONTROL",
                "params": {"acao": "ligar", "alvo": "luz"},
            }
        },
    }

    tratamento, receipts = _tratamento_roteador_real(
        resultado,
        "talvez liga a luz",
        {"_registrar_sugestao_indireta": lambda *_args: True},
    )

    assert tratamento.legado is False
    assert tratamento.tratado is True
    assert tratamento.executou is False
    assert tratamento.confirmado is False
    assert tratamento.status == "sugestao_registrada"
    assert tratamento.sucesso_habilidade is False
    assert receipts == []


def test_alias_fechar_programa_sem_alvo_e_com_alvo_preserva_receipt_no_mesmo_resultado():
    sem_alvo = {"intent": "FECHAR_PROGRAMA", "params": {}}
    tratamento_sem_alvo, receipts_sem_alvo = _tratamento_roteador_real(
        sem_alvo,
        "fecha o programa",
    )

    assert tratamento_sem_alvo.legado is False
    assert tratamento_sem_alvo.executou is False
    assert tratamento_sem_alvo.confirmado is False
    assert tratamento_sem_alvo.status == "alvo_ausente"
    assert receipts_sem_alvo[-1].status == "alvo_ausente"

    estado = {"aberto": True}
    com_alvo = {"intent": "FECHAR_PROGRAMA", "params": {"programa": "opera"}}
    tratamento_com_alvo, receipts_com_alvo = _tratamento_roteador_real(
        com_alvo,
        "fecha o opera",
        {
            "APPS_MAP": {"opera": "opera.exe"},
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": estado["aberto"],
            },
            "fechar_programa": lambda _nome: estado.update(aberto=False) or True,
        },
    )

    assert tratamento_com_alvo.legado is False
    assert tratamento_com_alvo.executou is True
    assert tratamento_com_alvo.confirmado is True
    assert tratamento_com_alvo.status == "app_fechado"
    assert len(receipts_com_alvo) == 1
    assert receipts_com_alvo[0].intent == "FECHAR_PROGRAMA"
    assert receipts_com_alvo[0].status == "app_fechado"



def test_roteador_moderno_sem_receipt_falha_fechado_sem_virar_legado(monkeypatch):
    monkeypatch.setattr(
        executor_integracoes,
        "executar_intencao_arquivos",
        lambda *_args, **_kwargs: True,
    )
    resultado = {
        "intent": "CREATE_FOLDER",
        "params": {"nome": "teste_sem_receipt"},
    }

    tratamento, receipts = _tratamento_roteador_real(
        resultado,
        "cria uma pasta teste_sem_receipt",
    )

    assert tratamento.legado is False
    assert tratamento.tratado is True
    assert tratamento.executou is None
    assert tratamento.confirmado is None
    assert tratamento.status == "tratado_sem_receipt"
    assert tratamento.sucesso_habilidade is False
    assert tratamento.resultado_incerto is False
    assert receipts == []



def test_fluxo_dependente_exige_sucesso_habilidade_sem_mudar_consumo_padrao():
    def resolver(_texto, _origem, _ctx):
        return {"intent": "CREATE_FOLDER", "params": {"nome": "x"}}, "teste"

    def executar(pedido, _texto):
        marcar_tratamento_operacional(
            pedido,
            tratado=True,
            executou=None,
            confirmado=None,
            status="tratado_sem_receipt",
            retorno_legado=True,
        )
        return True

    ctx = {"executar_intencao": executar}

    assert executar_fluxo_intencao(
        "cria pasta x",
        "standalone",
        ctx,
        resolver_cb=resolver,
    ) is True

    assert executar_fluxo_intencao(
        "cria pasta x",
        "cadeia-1",
        ctx,
        resolver_cb=resolver,
        exigir_sucesso_habilidade=True,
    ) is False
