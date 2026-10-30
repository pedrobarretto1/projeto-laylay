"""Critérios declarados em uma escolha; publicação não os transforma em fatos."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
import re
import time
from typing import Any, Mapping


CRITERIOS_AUTORAIS = {
    'curiosidade': 'curiosidade',
    'afinidade_estetica': 'afinidade estética',
    'clareza': 'clareza',
    'simplicidade': 'simplicidade',
    'nao_declarado': '',
}


def validar_codigo_criterio(codigo: Any) -> str:
    if type(codigo) is not str or codigo not in CRITERIOS_AUTORAIS:
        raise ValueError('criterio_autoral_nao_contratado')
    return codigo


@dataclass(frozen=True, slots=True)
class FundamentoCriterioAutoral:
    snapshot_id: str
    alvo: str
    fonte_id: str
    trecho: str
    expira_em: float
    alcance: str = field(default='premissa_citada_integralmente', init=False)
    prova_factual: bool = field(default=False, init=False)
    prova_causal: bool = field(default=False, init=False)
    adequacao_avaliativa_comprovada: bool = field(default=False, init=False)
    autoriza_execucao: bool = field(default=False, init=False)


def _fundamento_criterio_integro(fundamento: Any) -> bool:
    import hashlib
    return bool(type(fundamento) is FundamentoCriterioAutoral
        and type(fundamento.expira_em) in (int, float) and math.isfinite(fundamento.expira_em)
        and type(fundamento.fonte_id) is str and type(fundamento.trecho) is str
        and 0 < len(fundamento.trecho) <= 850
        and fundamento.snapshot_id == hashlib.sha256((fundamento.fonte_id+'\0'+fundamento.trecho).encode('utf8')).hexdigest()
        and not fundamento.prova_factual and not fundamento.prova_causal
        and not fundamento.adequacao_avaliativa_comprovada and not fundamento.autoriza_execucao)


def fundamento_criterio_vigente(fundamento: Any, *, agora: float | None = None) -> bool:
    instante = time.time() if agora is None else agora
    return bool(_fundamento_criterio_integro(fundamento)
        and type(instante) in (int, float) and math.isfinite(instante) and instante < fundamento.expira_em)


@dataclass(frozen=True, slots=True)
class CriterioAutoralEmissao:
    turno_id: str
    texto_usuario: str
    declaracao: str
    codigo: str
    emissao_sha256: str
    fundamento: FundamentoCriterioAutoral | None = None
    prova_factual: bool = field(default=False, init=False)
    prova_causal: bool = field(default=False, init=False)
    autoriza_execucao: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class CriterioAutoralPublicado:
    origem_id: str
    turno_origem: str
    texto_origem: str
    declaracao: str
    codigo: str
    emissao_sha256: str
    ts_origem: float
    portadora_id: str
    turno_portador: str
    fala_portadora: str
    ts_portadora: float
    fundamento: FundamentoCriterioAutoral | None = None
    natureza: str = field(default='criterio_declarado_na_autoria', init=False)
    prova_factual: bool = field(default=False, init=False)
    prova_causal: bool = field(default=False, init=False)
    autoriza_execucao: bool = field(default=False, init=False)


def _entrada_valida(entrada: Mapping[str, Any], agora: float) -> bool:
    return bool(entrada.get('autoriza_execucao') is False
        and type(entrada.get('ts')) in (int, float) and math.isfinite(entrada['ts'])
        and 0 <= agora - entrada['ts'] <= 900
        and entrada.get('canais')
        and all(c in {'texto_publicado', 'audio_reproducao_confirmada'} for c in entrada['canais']))


def criterio_origem_vigente(criterio: CriterioAutoralPublicado, *, agora: float | None = None) -> bool:
    instante = time.time() if agora is None else agora
    return bool(type(criterio) is CriterioAutoralPublicado
        and type(instante) in (int, float) and math.isfinite(instante)
        and type(criterio.ts_origem) in (int, float) and math.isfinite(criterio.ts_origem)
        and 0 <= instante - criterio.ts_origem <= 900)


def criterio_publicado_da_fala(registro: Mapping[str, Any] | None,
    fala: Mapping[str, Any], *, agora: float | None = None) -> CriterioAutoralPublicado | None:
    instante = time.time() if agora is None else agora
    if type(instante) not in (int, float) or not math.isfinite(instante):
        return None
    criterio = fala.get('criterio_autoral')
    if (type(criterio) is not CriterioAutoralPublicado or not _entrada_valida(fala, instante)
        or type(criterio.codigo) is not str or criterio.codigo not in CRITERIOS_AUTORAIS or criterio.codigo == 'nao_declarado'
        or criterio.prova_factual or criterio.prova_causal or criterio.autoriza_execucao
        or (criterio.portadora_id, criterio.turno_portador, criterio.fala_portadora, criterio.ts_portadora)
        != (fala.get('id'), fala.get('turno_id'), fala.get('fala'), fala.get('ts'))
        or type(criterio.emissao_sha256) is not str or not re.fullmatch('[0-9a-f]{64}', criterio.emissao_sha256)
        or not criterio_origem_vigente(criterio, agora=instante)):
        return None
    raizes = [f for f in (registro or {}).get('falas_observadas', ())
              if isinstance(f, Mapping) and f.get('id') == criterio.origem_id]
    if len(raizes) != 1 or not _entrada_valida(raizes[0], instante):
        return None
    raiz = raizes[0]
    original = raiz.get('criterio_autoral')
    if (type(original) is not CriterioAutoralPublicado
        or original.origem_id != original.portadora_id
        or (original.origem_id, original.turno_origem, original.texto_origem,
            original.declaracao, original.codigo, original.emissao_sha256, original.ts_origem)
        != (criterio.origem_id, criterio.turno_origem, criterio.texto_origem,
            criterio.declaracao, criterio.codigo, criterio.emissao_sha256, criterio.ts_origem)
        or raiz.get('fala') != criterio.declaracao or raiz.get('turno_id') != criterio.turno_origem
        or raiz.get('ts') != criterio.ts_origem or original.fundamento != criterio.fundamento
        or (criterio.fundamento is not None and not _fundamento_criterio_integro(criterio.fundamento))):
        return None
    return criterio


def materializar_criterio_publicado(fonte: CriterioAutoralEmissao | CriterioAutoralPublicado | None, *,
    registro: Mapping[str, Any], ocorrencia_id: str, turno_id: str, fala: str,
    instante: float) -> CriterioAutoralPublicado | None:
    if fonte is None:
        return None
    existentes = [f for f in registro.get('falas_observadas', ())
                  if isinstance(f, Mapping) and f.get('id') == ocorrencia_id]
    # Um segundo canal confirma a mesma publicação, sem renovar sua origem.
    ts_publicacao = existentes[0]['ts'] if len(existentes) == 1 else instante
    if type(fonte) is CriterioAutoralEmissao:
        validar_codigo_criterio(fonte.codigo)
        if (fonte.codigo == 'nao_declarado' or fonte.turno_id != turno_id or fonte.declaracao != fala
            or not fonte.texto_usuario or type(fonte.emissao_sha256) is not str
            or not re.fullmatch('[0-9a-f]{64}', fonte.emissao_sha256)):
            raise ValueError('criterio_sem_vinculo_com_publicacao')
        # Expiração restringe uso explicativo; não apaga a entrega efetiva de
        # uma escolha cujo anexo foi admitido antes do callback assíncrono.
        if fonte.fundamento is not None and not _fundamento_criterio_integro(fonte.fundamento):
            raise ValueError('fundamento_sem_fonte_integra')
        return CriterioAutoralPublicado(ocorrencia_id, turno_id, fonte.texto_usuario, fala,
            fonte.codigo, fonte.emissao_sha256, ts_publicacao, ocorrencia_id, turno_id, fala, ts_publicacao,
            fonte.fundamento)
    if type(fonte) is CriterioAutoralPublicado:
        portadoras = [f for f in registro.get('falas_observadas', ())
                      if isinstance(f, Mapping) and f.get('id') == fonte.portadora_id]
        if (len(portadoras) != 1 or criterio_publicado_da_fala(registro, portadoras[0], agora=instante) != fonte
            or fonte.declaracao.casefold() not in fala.casefold()):
            raise ValueError('criterio_historico_sem_origem_vigente')
        # TTL e identidade da autoria original não são renovados pela explicação.
        return replace(fonte, portadora_id=ocorrencia_id, turno_portador=turno_id,
                       fala_portadora=fala, ts_portadora=ts_publicacao)
    raise TypeError('criterio_exige_fonte_nativa')
