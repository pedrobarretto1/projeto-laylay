"""Owner da relação de adequação ao usuário, distinto de gosto da autora.

Sem uma avaliação fundamentada de adequação, negocia um critério para a
escolha. O ato não afirma ausência de memória, traços pessoais, características
de uma opção ou efeito externo. Primário, reparo e revisão usam o mesmo vínculo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, TYPE_CHECKING

from mente_laylay.cognicao.referencias_linguagem import PerspectivaEnunciador, consulta_adequacao_pessoal

if TYPE_CHECKING:
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt


@dataclass(frozen=True, slots=True)
class AdequacaoPessoal:
    turno_id: str
    texto_usuario: str
    categoria: str
    alvo: str = field(default='usuario', init=False)
    relacao: str = field(default='adequacao', init=False)
    autoriza_execucao: bool = field(default=False, init=False)
    prova_factual: bool = field(default=False, init=False)


def construir_adequacao_pessoal(texto: str, *, turno: Mapping[str, Any],
    plano: Mapping[str, Any], contrato: Mapping[str, Any]) -> AdequacaoPessoal | None:
    categoria = consulta_adequacao_pessoal(texto)
    perspectiva = contrato.get('perspectiva_enunciador')
    if (not categoria or type(perspectiva) is not PerspectivaEnunciador
        or not perspectiva.vigente(texto, plano.get('id'))
        or str(turno.get('id')) != perspectiva.turno_id
        or (turno.get('texto_original') or turno.get('texto')) != texto
        or plano.get('texto_usuario') != texto
        or turno.get('autoriza_execucao') is not False or plano.get('autoriza_execucao') is not False
        or plano.get('requer_execucao') or plano.get('comandos')
        or turno.get('natureza_entrada') == 'evento' or plano.get('natureza_entrada') == 'evento'):
        return None
    return AdequacaoPessoal(perspectiva.turno_id, texto, categoria)


def realizacoes_adequacao(texto: str, *, contrato: Mapping[str, Any], turno_id: Any) -> tuple[str, ...]:
    fonte = contrato.get('adequacao_pessoal')
    perspectiva = contrato.get('perspectiva_enunciador')
    categoria = consulta_adequacao_pessoal(texto)
    if (type(fonte) is not AdequacaoPessoal or type(perspectiva) is not PerspectivaEnunciador
        or not perspectiva.vigente(texto, turno_id) or fonte.turno_id != str(turno_id)
        or fonte.texto_usuario != texto or not categoria or fonte.categoria != categoria
        or str(contrato.get('turno_id')) != str(turno_id) or contrato.get('origem') != 'mente_unica'
        or contrato.get('autoriza_execucao') is not False
        or contrato.get('atos') != ['adequacao_pessoal']
        or dict(contrato.get('roteiro_concreto') or {}).get('estrategia') != 'adequacao_ao_usuario'):
        return ()
    return (f'Pensando em {categoria} para você, o que mais importa nessa escolha?',
            f'Para escolher {categoria} pensando em você, me conta o que você procura.')


def avaliar_adequacao_pessoal(texto: str, fala: str, *, plano: Mapping[str, Any]) -> dict[str, Any] | None:
    contrato = plano.get('contrato_fala') or {}
    if 'adequacao_pessoal' not in contrato and 'adequacao_pessoal' not in contrato.get('atos', ()):
        return None
    opcoes = realizacoes_adequacao(texto, contrato=contrato, turno_id=plano.get('id'))
    aceita = bool(opcoes and fala in opcoes and plano.get('autoriza_execucao') is False
        and not plano.get('comandos') and not plano.get('requer_execucao'))
    problemas = [] if aceita else ['adequacao_pessoal_sem_relacao_conferida']
    return {'aceita':aceita, 'requer_reparo':not aceita, 'problemas':problemas,
        'problemas_bloqueantes':problemas, 'somente_consultiva':False, 'foco':{}, 'ultima_resposta':'',
        'contrato_reparo':{'adequacao_pessoal':True, 'autoriza_execucao':False},
        'aderencia_contrato':{'avaliado':True, 'aceita':aceita, 'prova_semantica_livre':False,
            'prova_factual':False, 'autoriza_execucao':False}, 'autoriza_execucao':False}


def montar_pacote_adequacao(texto: str, *, contrato: Mapping[str, Any], turno_id: Any) -> PacotePrompt | None:
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    opcoes = realizacoes_adequacao(texto, contrato=contrato, turno_id=turno_id)
    if not opcoes:
        return None

    def validar(dados: dict[str, Any]) -> None:
        if set(dados) != {'fala','comandos'} or dados.get('fala') not in opcoes or dados.get('comandos') != []:
            raise ValueError('adequacao_pessoal_sem_relacao_conferida')

    codec = ContratoSaidaEstruturada('adequacao_pessoal_v1', '[ADEQUACAO_PESSOAL]', {
        'type':'object', 'additionalProperties':False, 'required':['fala','comandos'],
        'properties':{'fala':{'type':'string','enum':list(opcoes)},
            'comandos':{'type':'array','maxItems':0,'items':{'type':'object'}}}}, validar)
    return PacotePrompt(({'role':'system','content':
        'Você é Laylay. A pergunta pede uma escolha adequada ao usuário, não o seu gosto. '
        'Escolha uma realização breve que busque o critério dele. Isso não afirma que falta '
        'memória nem que você conhece seus traços ou uma opção adequada. Não transfira sua '
        'preferência, não invente recomendação ou causa e não acrescente fatos, execução ou '
        'avisos técnicos de fontes. A relação com o usuário deve permanecer em toda a resposta.'},
        {'role':'user','content':texto}), contexto_fechado=True, contrato_saida=codec)
