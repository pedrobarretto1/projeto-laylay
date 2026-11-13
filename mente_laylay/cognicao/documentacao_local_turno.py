"""Documentos do catálogo ligados ao turno, sem certificar dados ou efeitos."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class DocumentoLocal:
    identidade: str
    texto: str
    dominio: str
    proprietario: str


@dataclass(frozen=True, slots=True)
class DocumentacaoLocalTurno:
    turno_id: str
    texto_usuario: str
    documentos: tuple[DocumentoLocal, ...]
    autoriza_execucao: bool = field(default=False, init=False)
    comprova_efeito: bool = field(default=False, init=False)


def selecionar_documentacao_local(texto: str, *, turno_id: Any,
                                  dominios_registrados: tuple[str, ...]) -> DocumentacaoLocalTurno | None:
    """Recuperação lexical de documentos, sem classificar intenção ou autorizar.

    A relevância apenas oferece fontes: a revisão exige identidade e conteúdo
    integral. Selecionar um documento não prova nem o fato citado pelo usuário
    nem disponibilidade da habilidade. Documentos descrevem contratos estáveis.
    """
    if not turno_id or not texto:
        return None
    from mente_laylay.especialistas.capacidades import documentos_explicativos_locais
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    termos = set(re.findall(r'\w+', normalizar_texto_basico(texto)))
    documentos = []
    for d in documentos_explicativos_locais():
        if d['dominio'] not in dominios_registrados or not all(
                termos.intersection(grupo) for grupo in d['assuntos']):
            continue
        digest = hashlib.sha256((str(turno_id) + '\0' + texto + '\0' + d['proprietario']
                                 + '\0' + d['texto']).encode('utf8')).hexdigest()
        documentos.append(DocumentoLocal('local:documentacao:' + digest, d['texto'], d['dominio'], d['proprietario']))
    return DocumentacaoLocalTurno(str(turno_id), texto, tuple(documentos[:3])) if documentos else None


def documentacao_local_vigente(plano: Mapping[str, Any]) -> DocumentacaoLocalTurno | None:
    contrato = plano.get('contrato_fala') or {}
    fonte = contrato.get('documentacao_local_turno')
    if (type(fonte) is not DocumentacaoLocalTurno or not plano.get('id')
        or fonte.turno_id != str(plano['id']) or fonte.texto_usuario != plano.get('texto_usuario')
        or str(contrato.get('turno_id')) != fonte.turno_id or contrato.get('origem') != 'mente_unica'
        or contrato.get('autoriza_execucao') is not False or plano.get('autoriza_execucao') is not False
        or plano.get('requer_execucao') or plano.get('comandos') or plano.get('natureza_entrada') == 'evento'):
        return None
    # Reconfere contra o catálogo, não contra a documentação declarada pela IA.
    esperada = selecionar_documentacao_local(fonte.texto_usuario, turno_id=fonte.turno_id,
        dominios_registrados=tuple(d.dominio for d in fonte.documentos))
    return fonte if fonte == esperada else None


def formatar_documentacao_local(fonte: DocumentacaoLocalTurno) -> str:
    return ('Documentação local do host para esta resposta. Estes trechos descrevem regras e limites; '
            'não comprovam existência de dados, disponibilidade atual, execução ou efeito. '
            'Use as referências em fontes; conserve cada trecho integral, sem acrescentar conclusões. '
            + json.dumps([{'id': d.identidade, 'texto': d.texto, 'proprietario': d.proprietario,
                           'alcance': 'documentacao_de_contrato'} for d in fonte.documentos], ensure_ascii=False))


def fala_documental_integral(fala: str, plano: Mapping[str, Any]) -> bool:
    """Confere escopo contra documentos do host, inclusive antes do pós-codec.

    Só reconhece texto documental integral, sem acréscimos. Não dispensa
    declaração de referências nem a revisão factual posterior da autoria.
    """
    fonte = documentacao_local_vigente(plano)
    if fonte is None or not fala:
        return False
    restante = fala
    documentos = {d.texto for d in fonte.documentos}
    while restante:
        trecho = next((d for d in documentos if restante == d or restante.startswith(d + ' ')), None)
        if trecho is None:
            return False
        documentos.remove(trecho)
        restante = restante[len(trecho):].lstrip()
    return True
