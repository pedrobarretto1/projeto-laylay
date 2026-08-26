"""Guardas semânticas compartilhadas para candidatos de ação prática."""

from __future__ import annotations

import re
import unicodedata

from mente_laylay.cognicao.modalidade_turno import analisar_protecao_operacional


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9\s?]", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def autoriza_candidato_iot_direto(texto: str, *, modalidade: str = "") -> bool:
    """Autoriza o detector IoT antes do portão casual somente em pedidos reais.

    O detector especializado ainda precisa reconhecer dispositivo, propriedade e
    parâmetros. Esta função decide apenas se a forma comunicativa permite ação.
    """
    t = _normalizar(texto)
    t = re.sub(
        r"^(?:por favor\s+)?(?:voce\s+)?(?:pode|poderia|consegue|conseguiria)\s+",
        "",
        t,
        count=1,
    ).strip()
    if not t or str(modalidade or "").casefold() == "deliberativo":
        return False
    if analisar_protecao_operacional(t).get("bloqueia_execucao"):
        return False
    if re.search(
        r"\b(?:imagino|suponho|voce acha|o que voce acha|eu gosto de|"
        r"eu costumo|eu queria)\b",
        t,
    ):
        return False

    # A moldura de cortesia já foi removida por ``normalizar_pedido_natural``.
    # Exigimos que o ato restante comece como pedido, não como comentário que
    # apenas contém um verbo operacional no meio.
    return bool(re.match(
        r"^(?:deixa|deixe|deixar|coloca|coloque|colocar|bota|bote|botar|poe|"
        r"muda|mude|mudar|ajusta|ajuste|ajustar|define|defina|definir|"
        r"torna|torne|tornar|quero)\b",
        t,
    ))


def bloqueia_controle_iot_por_modalidade(texto: str) -> bool:
    """Impede que menções, hipóteses e negações virem controle físico.

    Esta guarda vive também dentro do runtime IoT: mesmo que um roteador mais
    externo classifique mal o turno, o executor especializado não transforma
    uma pergunta sobre *como fazer* nem um ``não desliga`` em ação real.
    """
    t = _normalizar(texto)
    if not t:
        return True
    return bool(analisar_protecao_operacional(t).get("bloqueia_execucao"))


def detectar_consulta_lista_iot(texto: str) -> dict[str, object] | None:
    """Reconhece somente pedidos de listagem dos dispositivos inteligentes.

    É uma função pura para que a consulta exista antes mesmo de o runtime IoT
    estar conectado ao roteador. Não reconhece controle nem altera estado.
    """
    t = _normalizar(texto)
    if not re.search(r"\b(?:quais|lista|listar|liste|mostra|mostrar|mostre)\b", t):
        return None
    if not re.search(
        r"\b(?:dispositivos?|aparelhos?|casa inteligente|iot)\b", t,
    ):
        return None
    ambiente = ""
    encontrado = re.search(
        r"\b(?:do|da|de|no|na)\s+"
        r"(quarto|sala|cozinha|banheiro|escritorio)\b",
        t,
    )
    if encontrado:
        ambiente = encontrado.group(1)
    return {"intent": "IOT_LIST", "params": {"ambiente": ambiente}}


def texto_tem_evidencia_iot_parametro(texto: str) -> bool:
    """Reconhece pedido de propriedade IoT sem conhecer aliases do registro."""
    t = _normalizar(texto)
    if not autoriza_candidato_iot_direto(t):
        return False
    alvo = bool(re.search(
        r"\b(?:lampada|luz|tomada|ventilador|dispositivo|aparelho|iot|ela|ele|isso)\b",
        t,
    ))
    parametro = bool(re.search(
        r"\b(?:cor|brilho|clar[oa]|escur[oa]|pastel|branc[oa]|pret[oa]|cinza|"
        r"marrom|vermelh[oa]|verde|azul|amarel[oa]|rox[oa]|rosa|laranja|"
        r"cian[oa]|violeta|lilas|turquesa|dourad[oa]|magenta|coral|"
        r"\d{1,3}\s*(?:%|por cento))\b",
        t,
    ))
    return alvo and parametro
