"""Contrato inerte para inventários de referentes com proveniência.

Não ligado ao runtime. O seletor de trechos conversacionais não é um produtor
de inventário completo; somente a fonte que enumera o escopo pode declará-lo.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Literal, Mapping

from mente_laylay.cognicao.referencias_linguagem import qualificador_referencia_nominal
from mente_laylay.memoria_mental.registro_semantico import guardar_candidato_foco_contextual


@dataclass(frozen=True)
class ReferenteContextual:
    identificador: str
    tipo: str
    grandeza: str
    origem: str
    escopo: str


@dataclass(frozen=True)
class InventarioContextual:
    origem: str
    escopo: str
    capturado_em: float
    ttl_s: float
    cobertura: Literal["parcial", "completa"]
    metodo_cobertura: str
    referentes: tuple[ReferenteContextual, ...]


@dataclass(frozen=True)
class AntecedenteContextual:
    identificador: str
    origem: str
    origem_inventario: str
    escopo: str
    entidade_id: str
    registrado_em: float
    ttl_s: float
    retrato_id: int


def antecedente_do_retrato(
    retrato: Mapping[str, object] | None,
    registro: Mapping[str, object] | None,
    inventario: InventarioContextual,
    *,
    agora: float,
    ttl_s: float = 120.0,
) -> AntecedenteContextual | None:
    """Projeta somente identidade canônica que a fonte do inventário vinculou."""
    if (not isinstance(inventario, InventarioContextual)
            or not isinstance(inventario.referentes, tuple)
            or any(not isinstance(item, ReferenteContextual)
                   or not _texto_valido(item.identificador)
                   or not _texto_valido(item.tipo)
                   for item in inventario.referentes)
            or not isinstance(retrato, Mapping)
            or not isinstance(registro, Mapping)
            or not _numero_finito(agora)
            or not _numero_finito(ttl_s)
            or ttl_s <= 0):
        return None
    referencia = retrato.get("referencia_resolvida")
    if not isinstance(referencia, Mapping):
        return None
    entidade_id = referencia.get("entidade_id")
    if (referencia.get("origem") != "registro_semantico"
            or not _texto_valido(entidade_id)
            or retrato.get("entidade_explicita")
            or not _numero_finito(retrato.get("ts"))
            or not _numero_finito(retrato.get("id"))
            or not 0 <= agora - retrato["ts"] <= ttl_s):
        return None
    entidades = registro.get("entidades")
    if not isinstance(entidades, Mapping):
        return None
    entidade = entidades.get(entidade_id)
    if not isinstance(entidade, Mapping):
        return None
    dados = entidade.get("dados")
    if not isinstance(dados, Mapping):
        return None
    identificador = dados.get("inventario_id")
    registrado_em = entidade.get("ultima_mencao_ts")
    if (not _texto_valido(identificador)
            or not _numero_finito(registrado_em)
            or not 0 <= agora - registrado_em <= ttl_s
            or entidade.get("fonte") != inventario.origem
            or dados.get("inventario_origem") != inventario.origem
            or dados.get("inventario_escopo") != inventario.escopo
            or str(entidade.get("nome") or "").casefold()
            != str(referencia.get("nome") or "").casefold()
            or str(entidade.get("tipo") or "").casefold()
            != str(referencia.get("tipo") or "").casefold()
            or not any(item.identificador == identificador
                       and item.tipo.casefold() == str(entidade.get("tipo") or "").casefold()
                       for item in inventario.referentes)):
        return None
    tipo_nomeado, qualificador_nomeado = qualificador_referencia_nominal(
        str(retrato.get("texto") or ""),
    )
    if qualificador_nomeado:
        item = next(
            (item for item in inventario.referentes
             if item.identificador == identificador),
            None,
        )

        if (_tokens_descritor(tipo_nomeado) != _tokens_descritor(item.tipo)
                or not _tokens_descritor(qualificador_nomeado)
                <= _tokens_descritor(item.grandeza)):
            return None
    candidatos_retrato = retrato.get("referencia_candidatos")
    if not isinstance(candidatos_retrato, list) or not candidatos_retrato:
        return None
    elegiveis = [item for item in candidatos_retrato
                if isinstance(item, Mapping)
                and item.get("compativel_dominio") is not False
                and item.get("compativel_qualificador") is not False]
    if not elegiveis or not _numero_finito(elegiveis[0].get("pontuacao")):
        return None
    if len(elegiveis) > 1 and not _numero_finito(elegiveis[1].get("pontuacao")):
        return None
    if (str(elegiveis[0].get("nome") or "").casefold()
            != str(referencia.get("nome") or "").casefold()
            or elegiveis[0]["pontuacao"] < 0.45
            or (len(elegiveis) > 1
                and elegiveis[0]["pontuacao"]
                - elegiveis[1]["pontuacao"] < 0.15)):
        return None
    return AntecedenteContextual(
        identificador=identificador,
        origem="registro_semantico_tipado",
        origem_inventario=inventario.origem,
        escopo=inventario.escopo,
        entidade_id=entidade_id,
        registrado_em=registrado_em,
        ttl_s=ttl_s,
        retrato_id=int(retrato["id"]),
    )


def antecedente_de_mencao_explicita(
    retrato: Mapping[str, object] | None,
    inventario: InventarioContextual | None,
    *,
    agora: float,
    origens_enumeradoras: frozenset[str] = frozenset(),
    ttl_s: float = 120.0,
) -> AntecedenteContextual | None:
    """Projeta foco dito explicitamente sobre um inventário enumerado.

    A frase escolhe apenas entre identidades que a fonte já forneceu. A
    projeção não registra uma medição nem permite que texto livre declare
    sozinho a completude do inventário.
    """
    if (not isinstance(retrato, Mapping)
            or not isinstance(inventario, InventarioContextual)
            or not inventario.referentes
            or not _numero_finito(retrato.get("id"))
            or not _numero_finito(retrato.get("ts"))
            or not _numero_finito(agora)
            or not _numero_finito(ttl_s)
            or ttl_s <= 0
            or not 0 <= agora - retrato["ts"] <= ttl_s
            or str(retrato.get("modalidade") or "") not in {"conversa", "pergunta"}
            or not _texto_valido(retrato.get("texto"))
            or retrato.get("operacao_explicita")):
        return None
    primeiro = inventario.referentes[0]
    if not isinstance(primeiro, ReferenteContextual):
        return None
    validade = avaliar_referente_contextual(
        inventario,
        tipo=primeiro.tipo,
        grandeza_requerida=primeiro.grandeza,
        agora=agora,
        origens_enumeradoras=origens_enumeradoras,
    )
    if validade.get("estado") not in {
        "candidato_unico_pendente", "referentes_concorrentes",
    }:
        return None

    descricao_dita = _descricao_foco_explicito(str(retrato["texto"]))
    if descricao_dita is None:
        return None
    correspondentes = [
        item for item in inventario.referentes
        if descricao_dita == _normalizar_foco(f"{item.tipo} de {item.grandeza}")
    ]
    if len(correspondentes) != 1:
        return None
    item = correspondentes[0]
    return AntecedenteContextual(
        identificador=item.identificador,
        origem="mencao_explicita_inventariada",
        origem_inventario=inventario.origem,
        escopo=inventario.escopo,
        entidade_id=(f"inventario:{inventario.origem}:"
                     f"{inventario.escopo}:{item.identificador}"),
        registrado_em=agora,
        ttl_s=ttl_s,
        retrato_id=int(retrato["id"]),
    )


def _normalizar_foco(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto.casefold())
    base = "".join(letra for letra in base
                   if not unicodedata.combining(letra))
    return re.sub(r"\s+", " ", base).strip(" .!?;:")


def _descricao_foco_explicito(texto: str) -> str | None:
    achado = re.fullmatch(
        r"(?:estamos falando|vamos falar|quero falar)\s+"
        r"(?:de|do|da)\s+(?:o\s+|a\s+)?(.+)",
        _normalizar_foco(texto),
    )
    return achado.group(1) if achado else None


def atualizar_foco_contextual_inventariado(
    registro: Mapping[str, object] | None,
    retrato: Mapping[str, object] | None,
    inventario: InventarioContextual | None,
    *,
    agora: float,
    origens_enumeradoras: frozenset[str] = frozenset(),
) -> dict[str, object]:
    """Preserva foco em turnos independentes e cancela trocas ambíguas."""
    estado = dict(registro or {})
    if not isinstance(retrato, Mapping):
        return estado
    if _descricao_foco_explicito(str(retrato.get("texto") or "")) is None:
        return estado
    foco = antecedente_de_mencao_explicita(
        retrato, inventario, agora=agora,
        origens_enumeradoras=origens_enumeradoras,
    )
    return guardar_candidato_foco_contextual(
        estado, asdict(foco) if foco else None, agora=agora,
    )


def antecedente_do_foco_guardado(
    registro: Mapping[str, object] | None,
    inventario: InventarioContextual | None,
    *,
    agora: float,
    origens_enumeradoras: frozenset[str] = frozenset(),
) -> AntecedenteContextual | None:
    """Relê o foco compartilhado somente após revalidá-lo na fonte atual."""
    if not isinstance(registro, Mapping) or not isinstance(inventario, InventarioContextual):
        return None
    dados = registro.get("foco_contextual_tipado")
    if not isinstance(dados, Mapping):
        return None
    try:
        foco = AntecedenteContextual(**dados)
    except (TypeError, ValueError):
        return None
    if foco.origem != "mencao_explicita_inventariada":
        return None
    item = next((item for item in inventario.referentes
                 if isinstance(item, ReferenteContextual)
                 and item.identificador == foco.identificador), None)
    if item is None:
        return None
    resultado = avaliar_referente_contextual(
        inventario, tipo=item.tipo, grandeza_requerida=item.grandeza,
        agora=agora, origens_enumeradoras=origens_enumeradoras,
        antecedente=foco,
        origens_antecedente=frozenset({"mencao_explicita_inventariada"}),
    )
    if resultado.get("estado") != "candidato_focal_pendente":
        return None
    return foco


def _texto_valido(valor: object) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


def _numero_finito(valor: object) -> bool:
    return type(valor) in (int, float) and math.isfinite(valor)


def _tokens_descritor(texto: str) -> set[str]:
    base = unicodedata.normalize("NFKD", texto.casefold())
    base = "".join(letra for letra in base if not unicodedata.combining(letra))
    return set(re.findall(r"[a-z0-9]+", base)) - {
        "de", "do", "da", "dos", "das",
    }


def avaliar_referente_contextual(
    inventario: InventarioContextual | None,
    *,
    tipo: str,
    grandeza_requerida: str,
    agora: float,
    origens_enumeradoras: frozenset[str] = frozenset(),
    antecedente: AntecedenteContextual | None = None,
    origens_antecedente: frozenset[str] = frozenset(),
) -> dict[str, object]:
    """Avalia candidatos, sem interpretar texto nem autorizar fala/efeito."""
    base: dict[str, object] = {
        "referente_resolvido": False,
        "aprovado_para_compor": False,
        "autoriza_efeito": False,
        "cobertura_verificada": False,
    }
    if not isinstance(inventario, InventarioContextual):
        return {**base, "estado": "inventario_nao_tipado"}
    if (not _texto_valido(inventario.origem)
            or not _texto_valido(inventario.escopo)
            or not _numero_finito(inventario.capturado_em)
            or not _numero_finito(inventario.ttl_s)
            or inventario.ttl_s <= 0
            or not _numero_finito(agora)
            or agora < inventario.capturado_em
            or not isinstance(inventario.referentes, tuple)
            or any(not isinstance(item, ReferenteContextual)
                   for item in inventario.referentes)):
        return {**base, "estado": "proveniencia_invalida"}
    if agora - inventario.capturado_em > inventario.ttl_s:
        return {**base, "estado": "inventario_expirado"}
    for item in inventario.referentes:
        if (not _texto_valido(item.identificador)
                or not _texto_valido(item.tipo)
                or not _texto_valido(item.grandeza)
                or item.origem != inventario.origem
                or item.escopo != inventario.escopo):
            return {**base, "estado": "proveniencia_invalida"}
    ids = [item.identificador for item in inventario.referentes]
    if len(ids) != len(set(ids)):
        return {**base, "estado": "identificadores_duplicados"}
    if (not isinstance(origens_enumeradoras, frozenset)
            or inventario.origem not in origens_enumeradoras):
        return {**base, "estado": "fonte_nao_registrada"}
    # Relevância, ausência de outro item na seleção e texto da LLM não são
    # enumeração. Somente o produtor dono da fonte pode declarar cobertura.
    if (inventario.cobertura != "completa"
            or inventario.metodo_cobertura != "enumeracao_da_fonte"):
        return {**base, "estado": "cobertura_nao_demonstrada"}

    def normalizar(texto: str) -> str:
        return re.sub(r"\s+", " ", texto.casefold()).strip()

    if not _texto_valido(tipo) or not _texto_valido(grandeza_requerida):
        return {**base, "estado": "consulta_invalida"}
    candidatos = [item for item in inventario.referentes
                  if normalizar(item.tipo) == normalizar(tipo)]
    if not candidatos:
        return {**base, "estado": "referente_ausente"}
    if antecedente is not None:
        if (not isinstance(antecedente, AntecedenteContextual)
                or not _texto_valido(antecedente.identificador)
                or not _texto_valido(antecedente.origem)
                or antecedente.origem_inventario != inventario.origem
                or not _texto_valido(antecedente.escopo)
                or not _texto_valido(antecedente.entidade_id)
                or not _numero_finito(antecedente.registrado_em)
                or not _numero_finito(antecedente.ttl_s)
                or antecedente.ttl_s <= 0
                or antecedente.escopo != inventario.escopo
                or not 0 <= agora - antecedente.registrado_em <= antecedente.ttl_s):
            return {**base, "estado": "antecedente_invalido"}
        if (not isinstance(origens_antecedente, frozenset)
                or antecedente.origem not in origens_antecedente):
            return {**base, "estado": "antecedente_nao_registrado"}
        candidato_focal = next(
            (item for item in candidatos
             if item.identificador == antecedente.identificador), None,
        )
        if candidato_focal is None:
            return {**base, "estado": "antecedente_sem_item"}
        if normalizar(candidato_focal.grandeza) != normalizar(grandeza_requerida):
            return {**base, "estado": "grandeza_divergente"}
        return {**base, "estado": "candidato_focal_pendente",
                "identificador_candidato": candidato_focal.identificador,
                "entidade_id_antecedente": antecedente.entidade_id,
                "origem_candidata": inventario.origem,
                "escopo_candidato": inventario.escopo}
    if len(candidatos) > 1:
        return {**base, "estado": "referentes_concorrentes",
                "identificadores_candidatos": sorted(item.identificador
                                                    for item in candidatos)}
    candidato = candidatos[0]
    if normalizar(candidato.grandeza) != normalizar(grandeza_requerida):
        return {**base, "estado": "grandeza_divergente"}
    return {**base, "estado": "candidato_unico_pendente",
            "identificador_candidato": candidato.identificador,
            "origem_candidata": inventario.origem,
            "escopo_candidato": inventario.escopo}


def avaliar_referencia_nominal_contextual(
    texto: str,
    inventario: InventarioContextual | None,
    *,
    tipo: str,
    grandeza_requerida: str,
    agora: float,
    origens_enumeradoras: frozenset[str] = frozenset(),
    antecedente: AntecedenteContextual | None = None,
    origens_antecedente: frozenset[str] = frozenset(),
) -> dict[str, object]:
    """Vincula um nome definido a um candidato, sem provar fatos narrados.

    Texto conversacional não é inventário, receipt nem autorização. A identidade
    só pode vir do inventário enumerado e, quando há concorrentes, do
    antecedente tipado. O qualificador dito no exemplo pode vetar o foco.
    """
    base: dict[str, object] = {
        "referente_resolvido": False,
        "aprovado_para_compor": False,
        "autoriza_efeito": False,
        "cobertura_verificada": False,
    }
    if not isinstance(texto, str) or not _texto_valido(tipo):
        return {**base, "estado": "referencia_nominal_invalida"}
    mencoes = list(re.finditer(
        rf"\b(?P<det>o|a|esse|essa|este|esta|aquele|aquela|um|uma)\s+"
        rf"{re.escape(tipo)}\b",
        texto, flags=re.IGNORECASE,
    ))
    if not mencoes:
        return {**base, "estado": "referencia_nominal_ausente"}
    if len(mencoes) != 1:
        return {**base, "estado": "referencia_nominal_multipla"}
    if mencoes[0].group("det").casefold() in {"um", "uma"}:
        return {**base, "estado": "referencia_nominal_ausente"}

    resultado = avaliar_referente_contextual(
        inventario,
        tipo=tipo,
        grandeza_requerida=grandeza_requerida,
        agora=agora,
        origens_enumeradoras=origens_enumeradoras,
        antecedente=antecedente,
        origens_antecedente=origens_antecedente,
    )
    if resultado.get("estado") not in {
        "candidato_focal_pendente", "candidato_unico_pendente",
    }:
        return resultado

    trecho_nominal = texto[mencoes[0].start():]
    tipo_nomeado, qualificador_nomeado = qualificador_referencia_nominal(
        trecho_nominal,
    )
    if tipo_nomeado.casefold() != tipo.casefold() or not qualificador_nomeado:
        return resultado
    identificador = resultado.get("identificador_candidato")
    item = next((item for item in inventario.referentes
                 if item.identificador == identificador), None)
    if item is None:
        return {**base, "estado": "candidato_sem_item"}

    if not _tokens_descritor(qualificador_nomeado) <= _tokens_descritor(item.grandeza):
        return {**base, "estado": "qualificador_divergente"}
    return resultado
