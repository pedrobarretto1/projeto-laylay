"""Conferência lexical de reuso; não avalia verdade ou pertinência livre."""
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Mapping

from mente_laylay.memoria_mental.memoria_confiavel import normalizar_texto


def projetar_contrato_reparo_conversacional(
    contrato: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Exporta limites sem transportar o estado privado usado pelo revisor.

    A fonte nativa permanece no host para a conferência posterior. Não a
    converter para texto ou dict: ocorrência de fala não é prova nem permissão.
    Demais campos mantêm o contrato de JSON; tipos desconhecidos não são
    silenciosamente convertidos. A projeção não modifica o contrato original.
    """
    return {chave: valor for chave, valor in dict(contrato or {}).items()
            if chave != 'respostas_anteriores_turno'}


def _reuso_predominante(candidata: str, anterior: str, *, minimo_copiado: int = 64) -> bool:
    """Blocos literais longos cobrem ao menos 80% de uma candidata extensa.

    Não é similaridade semântica: palavras comuns soltas não contam. O piso
    de 64 palavras copiadas mantém retomadas breves fora deste novo recorte;
    cópia integral continua sob o contrato anterior de oito palavras.
    """
    tokens = candidata.split()
    fonte = anterior.split()
    if min(len(tokens), len(fonte)) < minimo_copiado:
        return False
    blocos = SequenceMatcher(None, fonte, tokens, autojunk=False).get_matching_blocks()
    copiados = sum(bloco.size for bloco in blocos if bloco.size >= 8)
    return copiados >= minimo_copiado and copiados * 5 >= len(tokens) * 4


def contem_copia_extensa(candidata: str, fonte: str) -> bool:
    """Eco de outra autoria:32 palavras em blocos cobrem80% da candidata.

    Retomadas da própria assistente preservam seu piso anterior de64; citar
    algumas palavras do interlocutor não caracteriza esta cópia extensa.
    """
    return _reuso_predominante(normalizar_texto(candidata), normalizar_texto(fonte), minimo_copiado=32)


@dataclass(frozen=True, slots=True)
class RespostasAnterioresTurno:
    """Falas já entregues, capturadas pelo host e ligadas à entrada atual.

    O texto da assistente permanece uma ocorrência de fala, nunca evidência
    factual, memória durável ou autorização. Não é projetado como instrução.
    """
    turno_id: str
    texto_usuario: str
    falas: tuple[str, ...]
    autoriza_execucao: bool = field(default=False, init=False)
    comprova_fato: bool = field(default=False, init=False)

    def vigente(self, texto_usuario: str, turno_id: object) -> bool:
        return bool(self.turno_id and str(turno_id) == self.turno_id
                    and texto_usuario == self.texto_usuario)

    def contem_resposta_integral(self, fala: str) -> bool:
        """Toda a candidata veio de uma fala recente, com pelo menos oito palavras.

        Texto novo fora do trecho não é julgado por esta conferência. Portanto,
        ausência de repetição não certifica que a resposta atendeu à pergunta.
        """
        candidata = normalizar_texto(fala)
        if len(candidata.split()) < 8:
            return False
        return any(f' {candidata} ' in f' {normalizar_texto(anterior)} '
                   for anterior in self.falas)

    def contem_reuso_predominante(self, fala: str) -> bool:
        """Texto novo marginal não isenta blocos extensos já publicados."""
        if self.contem_resposta_integral(fala):
            return True
        candidata = normalizar_texto(fala)
        return any(_reuso_predominante(candidata, normalizar_texto(anterior))
                   for anterior in self.falas)

    def contexto_sem_reuso(self, mensagens: list[dict[str, str]], fala: str) -> list[dict[str, str]]:
        """Preserva a cena recente, sem reapresentar a resposta integral recusada."""
        candidata = normalizar_texto(fala)
        resultado = []
        for mensagem in mensagens:
            role = mensagem.get('role')
            conteudo = mensagem.get('content')
            if role not in {'user', 'assistant'} or not isinstance(conteudo, str):
                continue
            if role == 'assistant' and candidata:
                anterior = normalizar_texto(conteudo)
                if (f' {candidata} ' in f' {anterior} '
                        or _reuso_predominante(candidata, anterior)):
                    continue
            resultado.append({'role': role, 'content': conteudo})
        return resultado[-8:]
