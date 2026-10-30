"""Apoio de categoria separado do relato pessoal e da proposta da LLM."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
import time
import unicodedata
from typing import Any

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
from mente_laylay.cognicao.referencias_linguagem import consulta_categoria_preferencia_usuario


def _literal(texto: str) -> str:
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(texto)).casefold()).strip(' .!?')


def categoria_consulta_preferencia(texto: str) -> dict[str, Any] | None:
    consulta = consulta_categoria_preferencia_usuario(texto)
    if consulta is None:
        return None
    categorias = {'aplicativo': 'app', 'app': 'app', 'programa': 'app', 'software': 'app',
        'gênero': 'genero_musical', 'genero': 'genero_musical', 'gênero musical': 'genero_musical',
        'genero musical': 'genero_musical', 'estilo musical': 'genero_musical'}
    categoria = categorias.get(_literal(consulta['categoria']))
    return {**consulta, 'categoria': categoria} if categoria else None


@dataclass(frozen=True)
class ApoiosCategoriaPreferencia:
    turno_id: str
    texto_usuario: str
    dados: SnapshotComandoIA

    def __post_init__(self) -> None:
        if type(self.dados) is not SnapshotComandoIA or type(self.turno_id) is not str or type(self.texto_usuario) is not str:
            raise TypeError('apoio_categoria_exige_snapshot_do_host')

    def vigente(self, plano: dict[str, Any]) -> bool:
        return bool(self.turno_id and self.turno_id == str(plano.get('id') or '')
                    and self.texto_usuario == plano.get('texto_usuario'))


def montar_apoios_categoria_preferencia(
    plano: dict[str, Any], *, catalogo_aplicativos: Any = None, pesquisa: Any = None,
) -> ApoiosCategoriaPreferencia | None:
    """Projeção efêmera do host; no máximo uma pesquisa nova, no budget existente."""
    from mente_laylay.cognicao.fundamentacao_factual import (
        _ler_preferencia_atribuida, _texto_relato_usuario_qualificado,
    )
    from mente_laylay.cognicao.pesquisa_contextual import CategoriaEntidadeLida
    from mente_laylay.integracao.catalogo_aplicativos import CatalogoAplicativosRuntime
    from mente_laylay.memoria_mental.memoria_pessoas import classificar_gosto_explicito
    consulta = categoria_consulta_preferencia(str(plano.get('texto_usuario') or ''))
    if consulta is None:
        return None
    itens = []
    candidatos = []
    # Ausência/negação do ato de dizer não é comprovada por preferência positiva.
    fontes_pessoais = () if consulta.get('ato_relato_negado') else plano.get('relatos_usuario') or ()
    for fonte in fontes_pessoais:
        texto = _texto_relato_usuario_qualificado(fonte)
        if texto is None or fonte.get('origem') == 'fala_atual':
            continue
        preferencia = _ler_preferencia_atribuida(texto, relato=False)
        if (preferencia is None or preferencia['papeis']['predicado'] != consulta['predicado']
            or preferencia['papeis']['negada'] != consulta['negada']):
            continue
        valor = preferencia['papeis']['valor']
        prova = None
        if (consulta['categoria'] == 'app' and type(catalogo_aplicativos) is CatalogoAplicativosRuntime
            and catalogo_aplicativos.validar(valor)):
            prova = {'origem': 'catalogo_aplicativos', 'somente_tipo': True}
        if consulta['categoria'] == 'genero_musical' and classificar_gosto_explicito(valor)[0] == 'genero_musical':
            prova = {'origem': 'lexico_memoria_pessoas', 'somente_tipo': True}
        candidatos.append((fonte, texto, valor, prova))
    resultados_pesquisa: dict[str, CategoriaEntidadeLida | None] = {}
    pesquisa_iniciada = False
    tem_apoio_local = any(prova for _, _, _, prova in candidatos)
    for fonte, texto, valor, prova in candidatos:
        if prova is None and pesquisa is not None and not tem_apoio_local:
            chave = valor
            if chave not in resultados_pesquisa:
                resultado = pesquisa.pesquisar_categoria_entidade(valor, consulta['categoria'], somente_cache=pesquisa_iniciada)
                pesquisa_iniciada = True
                resultados_pesquisa[chave] = resultado
            resultado = resultados_pesquisa[chave]
            if type(resultado) is CategoriaEntidadeLida and resultado.vigente(valor, consulta['categoria'], time.time()):
                prova = {**resultado.como_dict(), 'origem': 'wikidata_p31'}
        if prova:
            itens.append({'fonte_id': fonte['id'], 'texto_fonte': texto,
                'fonte_sha256': hashlib.sha256(texto.encode('utf8')).hexdigest(),
                'categoria': consulta['categoria'], 'valor': valor, 'apoio_categoria': prova})
    return ApoiosCategoriaPreferencia(str(plano.get('id') or ''), str(plano.get('texto_usuario') or ''),
        SnapshotComandoIA({'consulta': consulta, 'itens': itens, 'pesquisa_iniciada': pesquisa_iniciada}))


def conferir_categoria_da_fonte(plano: dict[str, Any], fonte: dict[str, Any]) -> dict[str, Any]:
    from mente_laylay.cognicao.fundamentacao_factual import _texto_relato_usuario_qualificado
    apoio = plano.get('apoios_categoria_preferencia')
    negativa = {'estado': 'categoria_sem_apoio', 'conferido': False}
    if type(apoio) is not ApoiosCategoriaPreferencia or not apoio.vigente(plano):
        return negativa
    texto = _texto_relato_usuario_qualificado(fonte)
    if texto is None:
        return negativa
    for item in apoio.dados.como_dict()['itens']:
        if (item['fonte_id'] != fonte.get('id') or item['texto_fonte'] != texto
            or item['fonte_sha256'] != hashlib.sha256(texto.encode('utf8')).hexdigest()):
            continue
        prova = item['apoio_categoria']
        if prova.get('expira_em') is not None and not time.time() < prova['expira_em']:
            continue
        return {'estado': 'categoria_com_apoio', 'conferido': True, 'categoria': item['categoria'],
            'valor': item['valor'], 'fonte_pessoal_id': item['fonte_id'], 'apoio_categoria': prova}
    return negativa
