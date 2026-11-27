"""Conferência lexical de reuso; não avalia verdade ou pertinência livre."""
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Iterable, Mapping

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


def _posicoes_copiadas(tokens: list[str], fonte: list[str], *, bloco_minimo: int) -> set[int]:
    blocos = SequenceMatcher(None, fonte, tokens, autojunk=False).get_matching_blocks()
    return {i for bloco in blocos if bloco.size >= bloco_minimo
            for i in range(bloco.b, bloco.b + bloco.size)}


def _cobertura_por_fonte(tokens: list[str], fontes: Iterable[str]) -> dict[str, set[int]]:
    cobertura: dict[str, set[int]] = {}
    for fonte in dict.fromkeys(fontes):
        palavras = fonte.split()
        if len(palavras) >= 8:
            copias = _posicoes_copiadas(tokens, palavras, bloco_minimo=8)
            if copias:
                cobertura[fonte] = copias
    return cobertura


def _fontes_do_reuso_predominante(
    tokens: list[str], fontes: Iterable[str], *, minimo_copiado: int = 64,
) -> set[str]:
    """Conta cada posição copiada uma vez, mesmo quando consta em várias fontes."""
    if len(tokens) < minimo_copiado:
        return set()
    cobertura = _cobertura_por_fonte(tokens, fontes)
    cobertas = set().union(*cobertura.values())
    if len(cobertas) >= minimo_copiado and len(cobertas) * 5 >= len(tokens) * 4:
        return set(cobertura)
    return set()


def contem_copia_extensa(candidata: str, fonte: str) -> bool:
    """Detecta blocos extensos ou uma reprodução quase integral do interlocutor."""
    from mente_laylay.cognicao.referencias_linguagem import texto_fora_de_citacoes

    tokens = normalizar_texto(candidata).split()
    fonte_normalizada = normalizar_texto(fonte)
    palavras = fonte_normalizada.split()
    if len(palavras) >= 16:
        # A reprodução integral continua sendo eco mesmo quando o modelo
        # acrescenta conteúdo próprio. Essa cobertura pertence à fonte.
        autoral = normalizar_texto(texto_fora_de_citacoes(candidata))
        if f" {fonte_normalizada} " in f" {autoral} ":
            return True
    if _fontes_do_reuso_predominante(tokens, (fonte_normalizada,), minimo_copiado=32):
        return True
    menor = min(len(tokens), len(palavras))
    if not 16 <= menor < 32:
        return False
    maior = max(len(tokens), len(palavras))
    # No recorte curto, a cobertura tem de ser de pelo menos 90% dos dois
    # textos. Reagir a um detalhe de uma mensagem longa continua permitido.
    if menor * 10 < maior * 9:
        return False
    copiados = len(_posicoes_copiadas(tokens, palavras, bloco_minimo=4))
    return copiados >= 16 and copiados * 10 >= maior * 9


def contem_ciclo_de_enunciados(fala: str) -> bool:
    """Detecta reiteração literal na própria fala, fora de citações."""
    from mente_laylay.cognicao.referencias_linguagem import enunciados_discursivos, intervalos_citados

    partes = [normalizar_texto(trecho) if not intervalos_citados(trecho) else ""
              for trecho in enunciados_discursivos(fala)]
    ocorrencias: dict[str, list[int]] = defaultdict(list)
    for indice, parte in enumerate(partes):
        if len(parte.split()) >= 2:
            ocorrencias[parte].append(indice)
    # Três ocorrências intercaladas caracterizam o ciclo. Uma ênfase
    # consecutiva ou duas menções da mesma escolha ainda podem ser naturais.
    return any(sum(any(partes[inicio + 1:fim]) for inicio, fim in zip(indices, indices[1:])) >= 2
               for indices in ocorrencias.values() if len(indices) >= 3)


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
        return bool(_fontes_do_reuso_predominante(
            normalizar_texto(fala).split(), map(normalizar_texto, self.falas),
        ))

    def fontes_da_colagem_com_interlocutor(self, fala: str) -> set[str]:
        """Localiza falas antigas usadas junto com a mensagem atual."""
        from mente_laylay.cognicao.referencias_linguagem import texto_fora_de_citacoes

        tokens = normalizar_texto(texto_fora_de_citacoes(fala)).split()
        if len(tokens) < 32:
            return set()
        usuario = _posicoes_copiadas(tokens, normalizar_texto(self.texto_usuario).split(), bloco_minimo=8)
        if not usuario:
            return set()
        cobertura = _cobertura_por_fonte(tokens, map(normalizar_texto, self.falas))
        assistente = set().union(*cobertura.values())
        total = len(usuario | assistente)
        # As duas origens precisam ter contribuição própria. A mesma posição
        # registrada em ambas não conta duas vezes nem caracteriza colagem.
        if (len(usuario - assistente) >= 8 and len(assistente - usuario) >= 8
                and total >= 32 and total * 5 >= len(tokens) * 4):
            return {fonte for fonte, copias in cobertura.items() if copias - usuario}
        return set()

    def contexto_sem_reuso(
        self, mensagens: list[dict[str, str]], fala: str, *, colagem_com_interlocutor: bool = False,
    ) -> list[dict[str, str]]:
        """Preserva a cena recente, sem reapresentar a resposta integral recusada."""
        candidata = normalizar_texto(fala)
        fontes = [normalizar_texto(m['content']) for m in mensagens
                  if m.get('role') == 'assistant' and isinstance(m.get('content'), str)]
        reutilizadas = _fontes_do_reuso_predominante(
            candidata.split(), [*map(normalizar_texto, self.falas), *fontes],
        )
        if colagem_com_interlocutor:
            reutilizadas.update(self.fontes_da_colagem_com_interlocutor(fala))
        resultado = []
        for mensagem in mensagens:
            role = mensagem.get('role')
            conteudo = mensagem.get('content')
            if role not in {'user', 'assistant'} or not isinstance(conteudo, str):
                continue
            if role == 'assistant' and candidata:
                anterior = normalizar_texto(conteudo)
                if (f' {candidata} ' in f' {anterior} '
                        or anterior in reutilizadas):
                    continue
            resultado.append({'role': role, 'content': conteudo})
        return resultado[-8:]
