"""Materializa reações curtas a partir de um contrato cognitivo já decidido.

A seleção de oportunidade, os fatos e a direção social pertencem à cognição.
O compositor apenas varia a apresentação local; não interpreta pedidos nem
produz comandos, memória pessoal ou confirmação de efeitos.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from mente_laylay.personalidade.higiene_fala import (
    remover_fragmento_final_incompleto,
    remover_residuos_operacionais,
)
from mente_laylay.personalidade.variacao_fala import escolher_variacao


_ABERTURAS_POR_OBJETIVO: dict[str, tuple[str, ...]] = {
    "reagir_brevemente": ("Olha só.", "Vi isso.", "Tô acompanhando."),
    "compartilhar_curiosidade": ("Olha esse detalhe.", "Isso chamou minha atenção.", "Reparei nisso."),
    "celebrar_junto": ("Boa!", "Gostei disso!", "Essa merece comemorar!"),
    "encorajar": ("Vai no seu ritmo.", "Tô contigo.", "Vamos com calma."),
    "acompanhar_sem_deboche": ("Tô contigo.", "Sem pressa.", "Vamos no seu ritmo."),
    "provocar_brincando": ("Olha a confiança sendo testada.", "Essa confiança teve trabalho.", "Deu trabalho para aquela confiança."),
}

_REACOES_DESCRITIVAS: dict[str, tuple[str, ...]] = {
    "reagir_brevemente": ("Olha isso! {fato}", "{fato} Chamou minha atenção.", "Caramba. {fato}"),
    "compartilhar_curiosidade": ("{fato} Esse detalhe é interessante.", "Olha só! {fato}", "{fato} Chamou minha atenção."),
    "celebrar_junto": ("Boa! {fato}", "{fato} Essa merece comemorar!", "Gostei disso! {fato}"),
    "encorajar": ("{fato} Vai no seu ritmo.", "Tô contigo. {fato}", "{fato} Vamos com calma."),
    "acompanhar_sem_deboche": ("Tô contigo. {fato}", "{fato} Sem pressa.", "{fato} Vamos no seu ritmo."),
    "provocar_brincando": ("{fato} Essa confiança teve trabalho.", "Olha a confiança sendo testada. {fato}", "{fato} Deu trabalho para aquela confiança."),
}


def compor_reacao_evento_local(contrato: Mapping[str, Any]) -> str:
    """Varia a moldura social preservando uma âncora literal inteira.

    Uma âncora longa ou incompleta não é cortada para caber nem substituída por
    fato inventado. A ausência de texto suficiente permanece ausência de fala.
    """
    dados = dict(contrato or {})
    if dados.get("motivo_supressao_reacao"):
        return ""
    if not (
        dados.get("funcao") == "reacao_evento"
        and dados.get("natureza_entrada") == "evento"
        and dados.get("autoriza_execucao") is False
        and not bool(dados.get("autoridade_usuario"))
        and not bool(dados.get("permissao_execucao"))
    ):
        return ""
    roteiro = dados.get("roteiro_concreto")
    if not isinstance(roteiro, Mapping) or roteiro.get("estrategia") != "reacao_evento":
        return ""
    direcao = dados.get("direcao_social")
    if not isinstance(direcao, Mapping) or any(
        direcao.get(chave) is not False
        for chave in ("autoridade_usuario", "permissao_execucao", "autoriza_execucao")
    ):
        return ""
    objetivo = str(direcao.get("objetivo") or "").strip()
    aberturas = _ABERTURAS_POR_OBJETIVO.get(objetivo)
    if not aberturas:
        return ""
    if objetivo == "provocar_brincando" and direcao.get("permite_humor") is not True:
        return ""

    reacao = dados.get("reacao_validada")
    if isinstance(reacao, Mapping) and reacao:
        if (reacao.get("autoriza_execucao") is not False
            or reacao.get("foco_evidencia") != dados.get("ancora_factual_completa")):
            return ""
        # A cognição validou a proposta da mesma chamada visual. O compositor
        # conserva autoria, sem confundir a tirada com a fonte factual.
        return str(reacao.get("fala") or "")

    fonte = (
        dados.get("ancora_factual_completa")
        if "ancora_factual_completa" in dados
        else roteiro.get("ancora_literal")
    )
    ancora = re.sub(r"\s+", " ", str(fonte or "")).strip()
    ancora = remover_fragmento_final_incompleto(remover_residuos_operacionais(ancora))
    # Rótulos iniciais do protocolo visual são metadados da fonte literal.
    # A remoção só afeta sua apresentação; ordens e primeira pessoa seguem
    # citadas e não ganham autoridade por terem aparecido na tela.
    ancora = re.sub(
        r"^(?:texto exato(?: vis[ií]vel)?|nome leg[ií]vel|artista leg[ií]vel)\s*:\s*",
        "", ancora, count=1, flags=re.IGNORECASE,
    ).strip()
    # Materializamos uma oração completa e curta, sem cortar palavras ou
    # acrescentar conclusão. O restante continua disponível no contrato.
    primeira = re.split(r"(?<=[.!?…])\s+", ancora, maxsplit=1)[0].strip()
    if not primeira or len(primeira) > 260 or not re.search(r"\w", primeira):
        return ""
    if primeira[-1] not in ".!?…":
        primeira += "."
    evitar = dados.get("respostas_recentes_evitar") or ()
    if dados.get("apresentacao_evidencia") == "descricao":
        if objetivo in {"reagir_brevemente", "compartilhar_curiosidade"}:
            # A própria observação pode ter sido formulada em linguagem de
            # conversa na chamada que viu a cena. Não anexar bordões, nem
            # substituir uma frase concreta pela fala livre da proposta.
            return primeira
        # O contrato decidiu o papel. A variação é compartilhada entre fatos
        # diferentes, evitando reiniciar o mesmo bordão a cada nova captura.
        padroes = _REACOES_DESCRITIVAS[objetivo]
        evitar_padroes = [p for p in padroes if p.format(fato=primeira) in evitar]
        return escolher_variacao(padroes, evitar=evitar_padroes).format(fato=primeira)
    # A atribuição explícita conserva texto observado em primeira pessoa ou
    # imperativo como evidência citada, nunca como promessa/receipt da Laylay.
    opcoes = [f'{abertura} Na tela: "{primeira}"' for abertura in aberturas]
    return escolher_variacao(opcoes, evitar=evitar)
