from __future__ import annotations

import re
import unicodedata

import pytest

from mente_laylay.arquivos.nome_natural import aspas_globalmente_coerentes
from mente_laylay.arquivos.roteador_arquivos import reconciliar_literalidade_filename
from mente_laylay.autonomia.comandos_imediatos import _candidato_prioritario_autorizado
from mente_laylay.autonomia.coordenador_intencao import (
    CicloComandosRuntime,
    resolver_intencao,
)
from mente_laylay.autonomia.pre_fluxo_contextual import (
    processar_resposta_pendencia_prioritaria,
)
from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno
from mente_laylay.cognicao.decisao_turno import (
    criar_contrato_decisao,
    filtrar_comandos_pelo_turno,
)
from mente_laylay.cognicao.modalidade_turno import (
    autoriza_execucao_efetiva,
    classificar_modalidade_turno,
    turno_tem_veto_execucao,
)
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    sem_acento = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", sem_acento).strip()


@pytest.mark.parametrize(
    "texto",
    [
        "fecha microsoft store nao o opera",
        "fecha a Microsoft Store, não o Opera",
        "fecha a Store mas não feche o Opera",
    ],
)
def test_negacao_interna_stt_cria_veto_monotonico(texto: str) -> None:
    turno = classificar_modalidade_turno(texto)

    assert turno_tem_veto_execucao(turno) is True
    assert autoriza_execucao_efetiva(turno) is False
    assert turno["autoriza_execucao"] is False
    assert turno["acao_explicita"] is False
    assert turno["texto_operacional"] == ""
    assert all(segmento["autoriza_execucao"] is False for segmento in turno["segmentos"])


@pytest.mark.parametrize(
    "texto",
    [
        "cria arquivo chamado nao.txt",
        'cria arquivo chamado "nao.txt"',
        "cria arquivo chamado 'nao.txt'",
        "cria arquivo chamado “nao.txt”",
    ],
)
def test_filename_nao_literal_valido_nao_cria_veto(texto: str) -> None:
    turno = classificar_modalidade_turno(texto)

    assert turno_tem_veto_execucao(turno) is False
    assert autoriza_execucao_efetiva(turno) is True


@pytest.mark.parametrize(
    "texto",
    [
        'cria arquivo chamado "nao.txt',
        'cria arquivo chamado “nao.txt"',
        'cria arquivo chamado ”nao.txt“',
        'cria arquivo chamado "nao.txt" e escreve "órfã',
        'cria arquivo chamado “nao.txt” e escreve "cruzada”',
    ],
)
def test_filename_com_aspas_globais_malformadas_falha_fechado(texto: str) -> None:
    assert aspas_globalmente_coerentes(texto) is False
    turno = classificar_modalidade_turno(texto)
    assert turno_tem_veto_execucao(turno) is True
    assert autoriza_execucao_efetiva(turno) is False


def test_revisao_nao_preserva_polaridade_e_correcao_pontuada() -> None:
    ambigua = resolver_revisao_intra_turno("fecha a Store, não o Opera")
    negada = resolver_revisao_intra_turno("fecha a Store, não feche o Opera")
    corrigida = resolver_revisao_intra_turno("fecha a Store, não, melhor o Opera")

    assert ambigua["detectada"] is True and ambigua["resolvida"] is False
    assert negada["detectada"] is True and negada["resolvida"] is False
    assert corrigida["resolvida"] is True
    assert corrigida["texto_operacional_efetivo"] == "fecha o Opera"


def test_veto_stale_bloqueia_plano_decisao_filtro_arbitro_e_readonly() -> None:
    turno = classificar_modalidade_turno("fecha a Store mas não o Opera")
    turno["autoriza_execucao"] = True  # simula produtor posterior defeituoso
    plano = planejar_turno("fecha a Store", turno=turno)
    contrato = criar_contrato_decisao(turno, plano)
    filtro = filtrar_comandos_pelo_turno(
        [{"intent": "CLOSE_APP", "params": {"alvo": "Opera"}}],
        turno=turno,
        plano=plano,
    )
    arbitragem = arbitrar_turno(
        "fecha a Store",
        [CandidatoDecisao(
            tipo="comando_explicito",
            valor={"intent": "CLOSE_APP", "params": {"alvo": "Opera"}},
            origem="teste",
            confianca=1.0,
        )],
        turno=turno,
    )

    assert plano["requer_execucao"] is False
    assert plano["autoriza_execucao"] is False
    assert contrato["permite_acao"] is False
    assert filtro["comandos"] == []
    assert arbitragem["decisao"] is None
    assert _candidato_prioritario_autorizado(
        {"intent": "SYSTEM_STATUS", "params": {}}, turno
    ) is False


def test_veto_permite_cancelar_pendencia_mas_nao_confirmar() -> None:
    chamadas: list[str] = []
    turno = classificar_modalidade_turno("fecha a Store mas não o Opera")
    ctx = {
        "mente_integrada_estado": {
            "turno_atual": turno,
            "pendencia_atual": {
                "status": "ativa",
                "origem": "lixeira_laylay",
                "foi_falada": True,
            },
        },
        "_executar_intencao_curta_contextual": (
            lambda resultado, *_args, **_kwargs: chamadas.append(resultado["intent"]) or True
        ),
    }

    cancelou, _ = processar_resposta_pendencia_prioritaria(ctx, "não")
    confirmou, _ = processar_resposta_pendencia_prioritaria(ctx, "sim")

    assert cancelou is True
    assert confirmou is False
    assert chamadas == ["CANCEL_DELETE_ITEM"]


def test_coordenador_bloqueia_veto_antes_de_refinar_ou_detectar() -> None:
    chamadas: list[str] = []
    turno = classificar_modalidade_turno("fecha a Store mas não o Opera")
    turno["autoriza_execucao"] = True
    resultado, rota = resolver_intencao(
        "fecha a Store",
        "teste",
        {
            "turno_atual": turno,
            "normalizar_texto": _normalizar,
            "refinar_contexto_mental": lambda _texto: chamadas.append("refinar"),
            "detectar_intencao_deterministica": lambda _texto: chamadas.append("detectar"),
        },
    )

    assert resultado is None
    assert rota == "veto_operacional_turno"
    assert chamadas == []


def test_reconciliacao_rev5_recupera_so_filename_raw_globalmente_valido() -> None:
    op = {"intent": "CREATE_FILE", "params": {"alvo": "nao txt"}}
    raw = {"intent": "CREATE_FILE", "params": {"alvo": '"nao.txt"'}}

    corrigido, campos = reconciliar_literalidade_filename(
        op,
        raw,
        texto_operacional="cria arquivo chamado nao txt",
        texto_original='cria arquivo chamado "nao.txt"',
        normalizar_texto=_normalizar,
    )
    malformado, campos_malformados = reconciliar_literalidade_filename(
        op,
        raw,
        texto_operacional="cria arquivo chamado nao txt",
        texto_original='cria arquivo chamado "nao.txt',
        normalizar_texto=_normalizar,
    )

    assert corrigido["params"]["alvo"] == "nao.txt"
    assert campos == ["alvo"]
    assert malformado == op
    assert campos_malformados == []


def test_ciclo_real_reconcilia_filename_sem_criar_autoridade() -> None:
    turno = {
        "id": "rev5-integracao-real",
        "modalidade": "comando",
        "modalidade_geral": "comando",
        "ato_principal": "comando",
        "autoriza_execucao": True,
        "texto_operacional": "cria arquivo chamado nao txt",
    }
    execucoes: list[tuple[dict, str]] = []

    class Contexto:
        @staticmethod
        def montar() -> dict:
            return {
                "turno_atual": dict(turno),
                "retrato_turno_atual": {},
                "continuidade_geral": {},
            }

    def detectar(texto: str) -> dict | None:
        if _normalizar(texto) == "cria arquivo chamado nao txt":
            return {
                "intent": "CREATE_FILE",
                "params": {"alvo": "nao txt", "tipo_arquivo": "texto"},
            }
        return None

    namespace = {
        "_normalizar_texto_com_apelidos": _normalizar,
        "_texto_depende_de_contexto": lambda _texto: False,
        "_texto_parece_consulta_operacional": lambda _texto: True,
        "detectar_intencao_deterministica": detectar,
        "_resolver_comando_contextual_forcado": lambda _texto: None,
        "_resolver_repeticao_ultima_acao": lambda _texto: None,
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
        "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
    }
    ciclo = CicloComandosRuntime(
        namespace_getter=lambda: namespace,
        contexto_intencao_runtime=Contexto(),
        log=lambda *_args: None,
    )
    ciclo.executar_intencao = (
        lambda resultado, texto: execucoes.append((resultado, texto)) or True
    )

    assert ciclo.processar_deterministico(
        "cria arquivo chamado nao txt",
        "teste-rev5",
        'cria arquivo chamado "nao.txt"',
    ) is True
    assert len(execucoes) == 1
    assert execucoes[0][0]["params"]["alvo"] == "nao.txt"
    assert execucoes[0][1] == 'cria arquivo chamado "nao.txt"'
