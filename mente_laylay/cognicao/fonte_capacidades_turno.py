"""Disponibilidade observada no catálogo, separada de permissão e efeito."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA


@dataclass(frozen=True, slots=True)
class FonteCapacidadesTurno:
    turno_id: str
    texto_usuario: str
    dados: SnapshotComandoIA
    autoriza_execucao: bool = field(default=False, init=False)
    comprova_efeito: bool = field(default=False, init=False)

    def vigente(self, texto: str, turno_id: Any) -> bool:
        return bool(turno_id and self.turno_id == str(turno_id) and self.texto_usuario == texto)

    def para_prompt(self) -> dict[str, Any]:
        dados = self.dados.como_dict()
        dominios = set(dados['dominios_disponiveis'])
        return {'fonte':'catalogo_vivo', 'turno_id':self.turno_id,
            'predicados':[p for p in dados['predicados'] if p.get('dominio') in dominios],
            'limite':'disponibilidade não prova autorização, execução, efeito ou causa de falha',
            'autoriza_execucao':False, 'comprova_efeito':False}


def fonte_capacidades_vigente(contrato: Mapping[str, Any], texto: str,
    turno_id: Any) -> FonteCapacidadesTurno | None:
    fonte = contrato.get('fonte_capacidades_turno')
    if (type(fonte) is FonteCapacidadesTurno and fonte.vigente(texto,turno_id)
        and str(contrato.get('turno_id')) == str(turno_id)
        and contrato.get('origem') == 'mente_unica' and contrato.get('autoriza_execucao') is False):
        return fonte
    return None


def formatar_fonte_capacidades(contrato: Mapping[str, Any]) -> str:
    fonte = contrato.get('fonte_capacidades_turno')
    if type(fonte) is not FonteCapacidadesTurno:
        return ''
    fonte = fonte_capacidades_vigente(contrato,fonte.texto_usuario,contrato.get('turno_id'))
    if fonte is None:
        return ''
    p = fonte.para_prompt()
    rotulos = list(dict.fromkeys(f"{v['acao']} {'/'.join(v['objetos'])}" for v in p['predicados']))
    if not rotulos:
        return ''
    return ('Capacidades pertinentes disponíveis neste turno: '+ '; '.join(rotulos[:6])
        + '. Uma tentativa não executada não prova incapacidade nem falta de acesso. '
        'Não invente esse diagnóstico. Disponibilidade não confirma efeito nem autoriza ação. '
        'Continue respondendo ao assunto atual; não transforme um relato em explicação de capacidades.')
