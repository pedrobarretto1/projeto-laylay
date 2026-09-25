"""Inventário de referentes de cenários didáticos declarados pelo usuário."""

from __future__ import annotations

import math
import re
from dataclasses import asdict
from typing import Mapping

from mente_laylay.cognicao.contrato_inventario_contextual import (
    InventarioContextual, ReferenteContextual,
    antecedente_do_foco_guardado, atualizar_foco_contextual_inventariado,
    avaliar_referencia_nominal_contextual,
)
from mente_laylay.memoria_mental.registro_semantico import guardar_candidato_foco_contextual


_PREFIXO = r"Neste cenário hipotético\s+"
_NOME = r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ-]*"
_UNICO = re.compile(
    rf"^{_PREFIXO}(?:existe|há)\s+"
    rf"(?:um único|uma única|apenas um|apenas uma)\s+"
    rf"(?P<tipo>{_NOME}),?\s+(?:que|e (?:ele|ela))\s+mede\s+"
    r"(?:exclusivamente\s+)?(?:a|o)\s+"
    r"(?P<grandeza>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s-]*)\.$",
    re.IGNORECASE,
)
_DOIS_MEDIDORES = re.compile(
    rf"^{_PREFIXO}há\s+(?P<exato>exatamente\s+)?(?:dois|duas)\s+"
    rf"(?P<plural>{_NOME}):\s+(?:um|uma)\s+mede\s+(?:a|o)\s+"
    r"(?P<primeira>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s-]*?)\s+e\s+"
    r"(?:o|a)\s+outr[oa]\s+mede\s+(?:a|o)\s+"
    r"(?P<segunda>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s-]*)\.$",
    re.IGNORECASE,
)
_DOIS_NOMEADOS = re.compile(
    rf"^{_PREFIXO}há\s+(?:um|uma)\s+(?P<tipo>{_NOME})\s+de\s+"
    r"(?P<primeira>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s-]*?)\s+e\s+"
    rf"(?:um|uma)\s+(?P=tipo)\s+de\s+"
    r"(?P<segunda>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s-]*)\.$",
    re.IGNORECASE,
)


def _singular(plural: str) -> str:
    nome = plural.casefold()
    if nome.endswith("ores"):
        return nome[:-2]
    if nome.endswith("s") and len(nome) > 3:
        return nome[:-1]
    return ""


def extrair_inventario_cenario_didatico(
    texto: str,
    *,
    escopo: str,
    capturado_em: float,
    origem_texto: str,
    ttl_s: float = 120.0,
) -> InventarioContextual | None:
    """Lê premissas explícitas do usuário, sem representar sensores reais.

    ``único`` e ``exatamente dois`` fecham o universo do cenário declarado.
    A mera enumeração de dois itens é parcial: pode haver outros não citados.
    """
    if (origem_texto != "usuario" or not isinstance(texto, str)
            or not isinstance(escopo, str) or not escopo.strip()
            or type(capturado_em) not in (int, float)
            or not math.isfinite(capturado_em)
            or type(ttl_s) not in (int, float)
            or not math.isfinite(ttl_s) or ttl_s <= 0):
        return None
    frase = re.sub(r"\s+", " ", texto).strip()
    if not frase or len(frase) > 500:
        return None
    unico = _UNICO.fullmatch(frase)
    if unico:
        tipo = unico.group("tipo").casefold()
        grandezas = (unico.group("grandeza").casefold(),)
        completa = True
    else:
        dois = _DOIS_MEDIDORES.fullmatch(frase)
        nomeados = _DOIS_NOMEADOS.fullmatch(frase) if dois is None else None
        if dois:
            tipo = _singular(dois.group("plural"))
            grandezas = (dois.group("primeira").casefold(),
                         dois.group("segunda").casefold())
            completa = bool(dois.group("exato"))
        elif nomeados:
            tipo = nomeados.group("tipo").casefold()
            grandezas = (nomeados.group("primeira").casefold(),
                         nomeados.group("segunda").casefold())
            completa = False
        else:
            return None
    if (not tipo or any(not grandeza.strip() for grandeza in grandezas)
            or len(set(grandezas)) != len(grandezas)):
        return None
    origem = "cenario_usuario"
    escopo_limpo = escopo.strip()[:120]
    referentes = tuple(
        ReferenteContextual(
            identificador=f"item_{indice}", tipo=tipo,
            grandeza=grandeza.strip(), origem=origem, escopo=escopo_limpo,
        )
        for indice, grandeza in enumerate(grandezas, start=1)
    )
    return InventarioContextual(
        origem=origem, escopo=escopo_limpo,
        capturado_em=float(capturado_em), ttl_s=float(ttl_s),
        cobertura="completa" if completa else "parcial",
        metodo_cobertura=("enumeracao_da_fonte" if completa
                          else "enumeracao_parcial_da_fonte"),
        referentes=referentes,
    )


def _inventario_do_estado(dados: object, *, agora: float) -> InventarioContextual | None:
    if not isinstance(dados, Mapping):
        return None
    try:
        itens = tuple(ReferenteContextual(**item) for item in dados["referentes"])
        inventario = InventarioContextual(
            origem=dados["origem"], escopo=dados["escopo"],
            capturado_em=dados["capturado_em"], ttl_s=dados["ttl_s"],
            cobertura=dados["cobertura"],
            metodo_cobertura=dados["metodo_cobertura"], referentes=itens,
        )
    except (KeyError, TypeError, ValueError):
        return None
    if (inventario.origem != "cenario_usuario"
            or not isinstance(inventario.escopo, str)
            or not inventario.escopo.startswith("cenario:")
            or type(inventario.capturado_em) not in (int, float)
            or type(inventario.ttl_s) not in (int, float)
            or not math.isfinite(inventario.capturado_em)
            or not math.isfinite(inventario.ttl_s)
            or not 0 <= agora - inventario.capturado_em <= inventario.ttl_s
            or not itens):
        return None
    if (inventario.cobertura, inventario.metodo_cobertura) not in {
        ("completa", "enumeracao_da_fonte"),
        ("parcial", "enumeracao_parcial_da_fonte"),
    }:
        return None
    if any(
        item.origem != inventario.origem or item.escopo != inventario.escopo
        or any(type(campo) is not str or not campo.strip()
               for campo in (item.identificador, item.tipo, item.grandeza))
        for item in itens
    ):
        return None
    if len({item.identificador for item in itens}) != len(itens):
        return None
    return inventario


def observar_cenario_didatico_sombra(
    texto: str,
    *,
    retrato: Mapping[str, object] | None,
    registro: Mapping[str, object] | None,
    inventario_anterior: object,
    origem_texto: str,
    agora: float,
) -> dict[str, object]:
    """Compõe fonte e foco na memória, sem mudar prompt, fala ou executor."""
    estado_registro = dict(registro or {})
    base = {
        "referente_resolvido": False,
        "aprovado_para_compor": False,
        "autoriza_efeito": False,
    }
    if (origem_texto != "usuario"
            or not isinstance(retrato, Mapping) or not isinstance(texto, str)
            or retrato.get("texto") != texto.strip()[:500]
            or type(agora) not in (int, float) or not math.isfinite(agora)):
        return {"registro": estado_registro, "inventario": {},
                "diagnostico": {**base, "estado": "entrada_invalida"}}
    inventario = extrair_inventario_cenario_didatico(
        texto, escopo=f"cenario:{retrato.get('id')}",
        capturado_em=agora, origem_texto=origem_texto,
    )
    novo_cenario = bool(re.match(
        r"^\s*Neste cenário hipotético\b", texto, re.IGNORECASE,
    ))
    if inventario is not None:
        estado_registro = guardar_candidato_foco_contextual(
            estado_registro, None, agora=agora,
        )
    elif novo_cenario:
        estado_registro = guardar_candidato_foco_contextual(
            estado_registro, None, agora=agora,
        )
        return {"registro": estado_registro, "inventario": {},
                "diagnostico": {**base, "estado": "cenario_nao_enumeravel"}}
    else:
        inventario = _inventario_do_estado(inventario_anterior, agora=agora)
    if inventario is None:
        estado_registro = guardar_candidato_foco_contextual(
            estado_registro, None, agora=agora,
        )
        return {"registro": estado_registro, "inventario": {},
                "diagnostico": {**base, "estado": "sem_cenario_vigente"}}

    estado_registro = atualizar_foco_contextual_inventariado(
        estado_registro, retrato, inventario, agora=agora,
        origens_enumeradoras=frozenset({"cenario_usuario"}),
    )
    foco = antecedente_do_foco_guardado(
        estado_registro, inventario, agora=agora,
        origens_enumeradoras=frozenset({"cenario_usuario"}),
    )
    tipos = {item.tipo for item in inventario.referentes}
    if len(tipos) == 1:
        tipo = next(iter(tipos))
        candidato = next(
            (item for item in inventario.referentes
             if foco and item.identificador == foco.identificador),
            inventario.referentes[0],
        )
        leitura = avaliar_referencia_nominal_contextual(
            texto, inventario, tipo=tipo,
            grandeza_requerida=candidato.grandeza, agora=agora,
            origens_enumeradoras=frozenset({"cenario_usuario"}),
            antecedente=foco,
            origens_antecedente=frozenset({"mencao_explicita_inventariada"}),
        )
        estado = str(leitura.get("estado") or "sem_referencia_nominal")
    else:
        estado = "tipos_concorrentes"
    return {
        "registro": estado_registro,
        "inventario": asdict(inventario),
        "diagnostico": {**base, "estado": estado,
                        "origem": inventario.origem,
                        "cobertura": inventario.cobertura,
                        "tem_foco": foco is not None},
    }
