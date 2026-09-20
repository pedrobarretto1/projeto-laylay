"""Roteiro concreto para a geração da fala de cada turno.

Este módulo não valida a resposta depois de pronta. Ele organiza a geração
antes da chamada ao modelo: qual ideia precisa aparecer primeiro, em que ordem
os atos devem ser atendidos e quais fontes podem sustentar a fala. O roteiro é
efêmero, não executa ações e não transforma contexto em autorização.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Iterable, Mapping
from mente_laylay.cognicao.normalizacao_linguagem import texto_discute_evidencia_textual


_ABSTRACOES_COMUNS = (
    "energia",
    "vibe",
    "sensação",
    "sentir-se vivo",
    "alma",
    "universo",
    "ritmo",
    "essência",
)

_DECLARACAO_ESTADO_OBSERVAVEL = re.compile(
    r"^(?:eu\s+)?(?:deixei|mantive)\b.{0,100}\b"
    r"(?:abert[oa]s?|fechad[oa]s?|ativ[oa]s?|rodando|em\s+execu[cç][aã]o)\b|"
    r"^.{0,100}\b(?:est[aá]|t[aá]|continua|segue|permanece)\s+"
    r"(?:abert[oa]s?|fechad[oa]s?|ativ[oa]s?|rodando|em\s+execu[cç][aã]o)\b",
    re.IGNORECASE,
)


def _texto_curto(valor: Any, limite: int) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()[:limite]


def _itens_unicos(valores: Iterable[Any], *, limite_item: int) -> tuple[str, ...]:
    itens: list[str] = []
    vistos: set[str] = set()
    for valor in valores:
        item = _texto_curto(valor, limite_item)
        chave = item.casefold()
        if not item or not chave or chave in vistos:
            continue
        vistos.add(chave)
        itens.append(item)
    return tuple(itens)


@dataclass(frozen=True, slots=True)
class RoteiroGeracaoConcreta:
    """Plano linguístico sem qualquer autoridade operacional."""

    versao: int = 1
    estrategia: str = "resposta_direta"
    ancora_literal: str = ""
    nucleo_resposta: str = "responder diretamente ao pedido atual"
    sequencia: tuple[str, ...] = ()
    exigencias_concretude: tuple[str, ...] = ()
    abstracoes_a_concretizar: tuple[str, ...] = _ABSTRACOES_COMUNS
    base_permitida: tuple[str, ...] = ("fala atual do usuário",)
    primeira_frase_responde_nucleo: bool = True
    autoriza_execucao: bool = False
    origem: str = "mente_unica"

    def __post_init__(self) -> None:
        object.__setattr__(self, "versao", 1)
        object.__setattr__(
            self,
            "estrategia",
            _texto_curto(self.estrategia, 64) or "resposta_direta",
        )
        object.__setattr__(self, "ancora_literal", _texto_curto(self.ancora_literal, 500))
        object.__setattr__(
            self,
            "nucleo_resposta",
            _texto_curto(self.nucleo_resposta, 320)
            or "responder diretamente ao pedido atual",
        )
        object.__setattr__(
            self,
            "sequencia",
            _itens_unicos(self.sequencia, limite_item=220),
        )
        object.__setattr__(
            self,
            "exigencias_concretude",
            _itens_unicos(self.exigencias_concretude, limite_item=240),
        )
        object.__setattr__(
            self,
            "abstracoes_a_concretizar",
            _itens_unicos(self.abstracoes_a_concretizar, limite_item=64),
        )
        object.__setattr__(
            self,
            "base_permitida",
            _itens_unicos(self.base_permitida, limite_item=180)
            or ("fala atual do usuário",),
        )
        object.__setattr__(self, "primeira_frase_responde_nucleo", True)
        # Invariante: roteiro de linguagem nunca é permissão de ação.
        object.__setattr__(self, "autoriza_execucao", False)
        object.__setattr__(self, "origem", "mente_unica")

    def como_dict(self) -> dict[str, Any]:
        dados = asdict(self)
        for campo in (
            "sequencia",
            "exigencias_concretude",
            "abstracoes_a_concretizar",
            "base_permitida",
        ):
            dados[campo] = list(dados[campo])
        return dados


def normalizar_roteiro_geracao_concreta(
    roteiro: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Reconstrói um roteiro externo mantendo limites e invariantes."""
    dados = dict(roteiro or {})
    if not dados:
        return {}
    return RoteiroGeracaoConcreta(
        estrategia=dados.get("estrategia", "resposta_direta"),
        ancora_literal=dados.get("ancora_literal", ""),
        nucleo_resposta=dados.get("nucleo_resposta", ""),
        sequencia=tuple(dados.get("sequencia") or ()),
        exigencias_concretude=tuple(dados.get("exigencias_concretude") or ()),
        abstracoes_a_concretizar=tuple(
            dados.get("abstracoes_a_concretizar") or _ABSTRACOES_COMUNS
        ),
        base_permitida=tuple(dados.get("base_permitida") or ()),
        primeira_frase_responde_nucleo=True,
        autoriza_execucao=False,
    ).como_dict()


def _atos_relevantes(atos: Iterable[Any]) -> list[str]:
    relevantes = {
        "pergunta",
        "metalinguagem",
        "saudacao",
        "estado_pessoal",
        "bem_estar",
        "opiniao",
        "esclarecimento",
        "agradecimento",
        "adiamento",
        "provocacao_curta",
        "codigo_laylay",
    }
    saida: list[str] = []
    for item in atos:
        ato = _texto_curto(item, 48).casefold()
        if ato in relevantes and ato not in saida:
            saida.append(ato)
    # Opinião, esclarecimento e bem-estar já são especializações da pergunta,
    # não um segundo ato. A pergunta genérica só permanece quando carrega
    # conteúdo próprio, como em "oi, pode recomendar um filme?".
    if "pergunta" in saida and any(
        especial in saida
        for especial in {"metalinguagem", "opiniao", "esclarecimento", "bem_estar"}
    ):
        saida.remove("pergunta")
    return saida


def _sequencia_multiacto(atos: Iterable[str]) -> tuple[str, ...]:
    presentes = set(atos)
    sequencia: list[str] = []
    if "saudacao" in presentes:
        sequencia.append("responder brevemente à saudação")
    if "metalinguagem" in presentes:
        sequencia.append("responder sobre a formulação citada, não sobre seu conteúdo factual")
    if "pergunta" in presentes:
        sequencia.append("responder diretamente à pergunta temática atual")
    if "estado_pessoal" in presentes:
        sequencia.append("reconhecer literalmente o estado informado pelo usuário")
    if "bem_estar" in presentes:
        sequencia.append("responder à pergunta de bem-estar como presença digital")
    if "opiniao" in presentes:
        sequencia.append("declarar a posição e dar um critério concreto")
    if "esclarecimento" in presentes:
        sequencia.append("explicar literalmente a fala anterior")
    if "agradecimento" in presentes:
        sequencia.append("reconhecer o agradecimento e encerrar sem retomar a tarefa anterior")
    if "adiamento" in presentes:
        sequencia.append("aceitar o adiamento de forma curta e literal")
    if "provocacao_curta" in presentes:
        sequencia.append("reagir à cutucada atual com limite ou deboche proporcional")
    sequencia.append("adicionar personalidade somente depois de responder todos os atos")
    return tuple(sequencia)


def _fundamentacao_confiavel(dados: Mapping[str, Any] | None) -> bool:
    base = dict(dados or {})
    return bool(
        base.get("confiavel")
        and base.get("evidencia_dentro_validade", True) is not False
    )


def plano_tem_resultado_confirmado(plano: Mapping[str, Any] | None) -> bool:
    """Reconhece evidência operacional já publicada, sem inferir execução."""
    for item in list(dict(plano or {}).get("comandos") or []):
        if not isinstance(item, Mapping):
            continue
        if (
            item.get("confirmado") is True
            and str(item.get("intent") or "").strip()
            and str(item.get("status") or "").strip()
        ):
            return True
    return False


def plano_indica_negacao_operacional_sem_efeito(
    texto: str,
    plano: Mapping[str, Any] | None,
) -> bool:
    """Usa a modalidade canônica para distinguir recusa de resultado factual."""
    planejamento = dict(plano or {})
    modalidade = str(
        planejamento.get("modalidade")
        or planejamento.get("ato_principal")
        or ""
    ).strip().casefold()
    if modalidade == "recusa":
        return True
    if modalidade != "correcao":
        return False
    return bool(re.search(
        r"\bn[aã]o\s+(?:te\s+)?(?:pedi|perguntei|solicitei)\b",
        str(texto or ""),
        re.IGNORECASE,
    ))


def texto_declara_estado_observavel(texto: str) -> bool:
    """Distingue um estado informado pelo usuário de uma consulta desse estado."""
    bruto = str(texto or "").strip()
    return bool(bruto and "?" not in bruto and _DECLARACAO_ESTADO_OBSERVAVEL.search(bruto))


def construir_roteiro_geracao_concreta(
    texto: str,
    *,
    contrato: Mapping[str, Any] | None = None,
    plano: Mapping[str, Any] | None = None,
    fundamentacao_factual: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Escolhe uma estratégia concreta a partir do contrato já deliberado."""
    dados_contrato = dict(contrato or {})
    planejamento = dict(plano or {})
    bruto = _texto_curto(texto, 500)
    atos = [str(item or "").casefold() for item in dados_contrato.get("atos") or []]
    especiais = _atos_relevantes(atos)
    referente = _texto_curto(dados_contrato.get("referente"), 180)
    anterior = _texto_curto(dados_contrato.get("fala_anterior_relevante"), 500)
    requer_execucao = bool(planejamento.get("requer_execucao"))
    resultado_confirmado = plano_tem_resultado_confirmado(planejamento)
    atualidade_factual = dict(planejamento.get("atualidade_factual") or {})
    estado_observavel_sem_evidencia = bool(
        atualidade_factual.get("classe") == "estado_observavel"
        and atualidade_factual.get("depende_atualidade")
        and not _fundamentacao_confiavel(fundamentacao_factual)
        and not resultado_confirmado
        and not requer_execucao
    )
    negacao_operacional_sem_efeito = plano_indica_negacao_operacional_sem_efeito(
        bruto,
        planejamento,
    )
    declaracao_estado_observavel = texto_declara_estado_observavel(bruto)
    recomendacao = bool(
        str(planejamento.get("dominio") or "").casefold() == "recomendacao"
        or re.search(
            r"\b(?:recomenda|recomende|recomendar|indica|indique|sugere|sugira)\b",
            bruto,
            flags=re.IGNORECASE,
        )
    )

    base_permitida = ["fala atual do usuário"]
    if referente:
        base_permitida.append("referente resolvido no turno atual")
    if anterior and "esclarecimento" in especiais:
        base_permitida.append("fala anterior explicitamente vinculada ao esclarecimento")
    if requer_execucao:
        base_permitida.append("resultado operacional publicado pelo executor, quando existir")
    elif resultado_confirmado:
        base_permitida.append("resultado operacional confirmado e publicado no turno atual")
    if _fundamentacao_confiavel(fundamentacao_factual):
        base_permitida.append("fundamentação factual confiável e válida do turno")
    capacidades_confirmadas = tuple(
        str(item or "").strip()
        for item in dados_contrato.get("capacidades_confirmadas") or ()
        if str(item or "").strip()
    )
    if capacidades_confirmadas:
        base_permitida.append(
            "catálogo vivo confirmou capacidades locais: "
            + ", ".join(capacidades_confirmadas[:8])
        )

    exigencias = [
        "usar a fala atual antes de puxar contexto antigo",
        "nomear o referente quando ele estiver resolvido",
        "ligar toda abstração, na mesma frase, a uma característica descritiva ou observável",
        "marcar como opinião ou incerteza o que não estiver sustentado por uma fonte permitida",
    ]

    if requer_execucao or resultado_confirmado:
        estrategia = "resultado_observado"
        ancora = referente or bruto
        nucleo = (
            "relatar primeiro o resultado realmente observado da ação e preservar "
            "a incerteza quando não houver confirmação"
        )
        sequencia = (
            "dizer o que foi observado, sem promover envio a sucesso",
            "informar a consequência prática ou a incerteza essencial",
            "adicionar personalidade apenas sem alterar o resultado",
        )
    elif negacao_operacional_sem_efeito:
        estrategia = "negacao_operacional_sem_efeito"
        ancora = bruto
        nucleo = (
            "reconhecer que a consulta ou ação não foi solicitada e não será "
            "executada, sem alegar nenhum estado do mundo"
        )
        sequencia = (
            "reconhecer literalmente a recusa ou correção do usuário",
            "confirmar apenas a não execução",
            "não afirmar resultado, estado atual ou motivo factual sem receipt",
        )
        exigencias.append(
            "tratar a negação como limite de ação, nunca como evidência sobre o alvo"
        )
    elif texto_discute_evidencia_textual(bruto):
        estrategia = "analise_evidencia_textual"
        ancora = bruto
        nucleo = (
            "analisar o que o relato fornecido permite concluir; se o conteúdo "
            "do relato não estiver disponível, pedir esse conteúdo brevemente"
        )
        if dados_contrato.get("estado_referencia_textual") == "nao_resolvida":
            nucleo = (
                "pedir brevemente que o usuário identifique ou envie o relato; "
                "a referência não foi resolvida, portanto não concluir o que ele comprova"
            )
        sequencia = (
            "usar somente o relato fornecido na fala ou explicitamente resolvido no contexto",
            "distinguir pedido de ação, relato atribuído e resultado confirmado pelo executor",
            "responder à dúvida sobre evidência, não explicar a formulação da pergunta",
        )
        exigencias.extend((
            "não concluir que nenhum relato pode comprovar algo; avaliar a fonte e o conteúdo concretos",
            "não inferir acesso ou incapacidade a partir da ausência de consulta neste turno",
            "não consultar recursos nem inventar o relato ausente para preencher a resposta",
        ))
    elif estado_observavel_sem_evidencia:
        estrategia = "estado_observavel_sem_evidencia"
        ancora = referente or bruto
        nucleo = (
            "dizer que ainda não existe uma leitura atual suficiente para responder, "
            "sem afirmar o estado nem negar a habilidade de consultá-lo"
        )
        sequencia = (
            "deixar explícito que falta uma observação atual neste turno",
            "não responder sim ou não sem evidência confirmada",
            "oferecer no máximo um próximo passo útil, sem alegar incapacidade permanente",
        )
        exigencias.append(
            "não converter ausência de leitura atual em falta permanente de acesso ou capacidade"
        )
    elif "metalinguagem" in especiais:
        estrategia = "resposta_metalinguistica"
        ancora = bruto
        nucleo = (
            "responder sobre a frase, a formulação ou o exemplo apresentado, "
            "sem tratá-lo como consulta atual"
        )
        sequencia = (
            "identificar brevemente que o assunto é a formulação",
            "responder à dúvida sobre como dizer ou interpretar a frase",
            "não afirmar se o conteúdo citado é verdadeiro no mundo atual",
        )
        exigencias.append(
            "marcar explicitamente a diferença entre citar uma pergunta e fazer essa pergunta agora"
        )
    elif "relato_explicito" in atos:
        estrategia = "reconhecimento_relato_explicito"
        ancora = bruto
        nucleo = (
            "acolher brevemente o que o usuário está contando, como relato e não "
            "como pedido atual, sem completar a história com resultados presumidos"
        )
        sequencia = (
            "reconhecer o conteúdo relatado em palavras próprias e naturais",
            "encerrar sem perguntar pelo resultado nem pedir mais informação",
            "não oferecer uma ação nem puxar outro assunto do contexto",
        )
    elif declaracao_estado_observavel:
        estrategia = "reconhecimento_estado_declarado"
        ancora = bruto
        nucleo = (
            "reconhecer somente o estado informado pelo usuário, sem confirmá-lo "
            "como observação própria nem acrescentar outra entidade"
        )
        sequencia = (
            "reconhecer brevemente o que o usuário informou",
            "atribuir o estado à fala atual quando repetir a informação",
            "não puxar outro aplicativo, objeto ou estado do contexto",
        )
        exigencias.append(
            "manter todas as entidades nomeadas ancoradas na fala atual"
        )
    elif "codigo_laylay" in especiais:
        estrategia = "conversa_codigo_laylay"
        ancora = bruto
        nucleo = (
            "continuar a conversa sobre o código da própria Laylay com interesse e "
            "uma observação nova, preservando sua voz em primeira pessoa"
        )
        sequencia = (
            "reagir ao que o usuário disse sem apenas repetir a frase",
            "acrescentar uma observação concreta ou uma tirada curta sobre o próprio código",
            "não interromper a conversa para explicar que Laylay é texto, regras ou um sistema sem vida",
        )
    elif recomendacao and len(especiais) > 1:
        estrategia = "resposta_multiacto"
        ancora = bruto
        nucleo = (
            "responder a todos os atos e entregar uma recomendação concreta escolhida "
            "somente da evidência factual do turno"
        )
        sequencia = _sequencia_multiacto(especiais) + (
            "entregar uma opção concreta presente na evidência factual",
        )
        exigencias.append(
            "não substituir a recomendação por outra pergunta nem inventar título"
        )
    elif recomendacao:
        estrategia = "recomendacao_fundamentada"
        ancora = referente or bruto
        nucleo = (
            "escolher uma opção concreta somente da evidência factual do turno "
            "e recomendá-la diretamente"
        )
        sequencia = (
            "escolher uma opção concreta presente na evidência factual",
            "dizer o título e uma razão curta sustentada pela mesma evidência",
            "perguntar preferência adicional somente depois de recomendar, se necessário",
        )
        exigencias.append(
            "não devolver a escolha ao usuário antes de oferecer um título real"
        )
    elif len(especiais) > 1:
        estrategia = "resposta_multiacto"
        ancora = bruto
        nucleo = "responder, na mesma fala, a todos os atos explícitos da mensagem atual"
        sequencia = _sequencia_multiacto(especiais)
    elif "esclarecimento" in especiais:
        estrategia = "esclarecimento_literal"
        ancora = anterior or bruto
        nucleo = "explicar com palavras literais o sentido da fala anterior"
        sequencia = (
            "reformular literalmente a ideia anterior",
            "dar a razão concreta que sustenta essa ideia",
            "usar no máximo um exemplo simples, somente se ajudar",
        )
        exigencias.append("não substituir a explicação por outra metáfora")
    elif "opiniao" in especiais:
        estrategia = "opiniao_com_criterio"
        ancora = referente or bruto
        alvo = referente or "o tema perguntado"
        nucleo = (
            f"declarar primeiro uma posição clara sobre {alvo} e sustentá-la "
            "com um critério descritivo ou observável"
        )
        sequencia = (
            "declarar a posição ou preferência",
            "citar um aspecto concreto que explica a posição",
            "fazer pergunta curta somente se ela avançar a conversa",
        )
    elif "estado_pessoal" in especiais:
        estrategia = "acolhimento_literal"
        ancora = bruto
        nucleo = "reconhecer primeiro, sem reinterpretar, o estado que o usuário informou"
        sequencia = (
            "reconhecer o estado nas palavras do usuário",
            "responder com companhia proporcional, sem dramatizar",
            "oferecer ajuda somente se ela fizer sentido",
        )
    elif "bem_estar" in especiais:
        estrategia = "reciprocidade_social"
        ancora = bruto
        nucleo = "responder brevemente como presença digital disponível, sem inventar corpo ou rotina"
        sequencia = (
            "responder diretamente como Laylay está na conversa",
            "devolver a cortesia com naturalidade, se couber",
        )
    elif "saudacao" in especiais:
        estrategia = "saudacao_simples"
        ancora = bruto
        nucleo = "responder à saudação sem atribuir ao usuário um humor não declarado"
        sequencia = (
            "cumprimentar de volta",
            "fazer no máximo uma pergunta simples, se couber",
        )
    elif "agradecimento" in especiais:
        estrategia = "encerramento_social"
        ancora = bruto
        nucleo = "reconhecer brevemente o agradecimento e encerrar o assunto atual"
        sequencia = (
            "responder ao agradecimento",
            "não recuperar tarefa, sugestão ou pendência anterior",
        )
    elif "adiamento" in especiais:
        estrategia = "adiamento_literal"
        ancora = bruto
        nucleo = "aceitar de forma curta que o assunto ficou para depois"
        sequencia = (
            "confirmar o adiamento",
            "encerrar sem metáfora, promessa ou pergunta",
        )
    elif "provocacao_curta" in especiais:
        estrategia = "reacao_social_curta"
        ancora = bruto
        nucleo = "reagir diretamente à provocação atual sem tratá-la como falha de comunicação"
        sequencia = (
            "mostrar que a cutucada foi compreendida",
            "usar no máximo uma tirada curta ou estabelecer um limite leve",
            "não inventar um assunto anterior para preencher a resposta",
        )
    elif dados_contrato.get("documentacao_capacidades"):
        estrategia = "explicacao_capacidades"
        ancora = bruto
        nucleo = "responder à dúvida sobre a habilidade usando a documentação viva do turno"
        sequencia = (
            "explicar o que foi perguntado; se for como usar, dar um exemplo de pedido",
            "respeitar disponibilidade e limites documentados sem inferir estados atuais",
            "tratar a dúvida com atenção; exemplos didáticos não são ações deste turno",
        )
    else:
        estrategia = "resposta_direta"
        ancora = referente or bruto
        nucleo = "responder primeiro ao conteúdo explícito da fala atual"
        sequencia = (
            "dar a resposta direta",
            "explicar apenas o necessário",
            "acrescentar personalidade sem desviar do assunto",
        )

    return RoteiroGeracaoConcreta(
        estrategia=estrategia,
        ancora_literal=ancora,
        nucleo_resposta=nucleo,
        sequencia=tuple(sequencia),
        exigencias_concretude=tuple(exigencias),
        abstracoes_a_concretizar=_ABSTRACOES_COMUNS,
        base_permitida=tuple(base_permitida),
        primeira_frase_responde_nucleo=True,
        autoriza_execucao=False,
    ).como_dict()
