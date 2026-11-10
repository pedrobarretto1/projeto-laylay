"""Recortes nominais de um ato; não são atos novos, autorização ou comandos.

O verbo compartilhado e cada membro conservam intervalos na fonte original.
A projeção para um resolver singular é declaradamente derivada desses recortes,
nunca apresentada como frase adicional dita pelo usuário.
"""
from dataclasses import dataclass
import re

from mente_laylay.arquivos.nome_natural import mapear_pares_aspas_globais
from mente_laylay.cognicao.gramatica_operacional import tipo_recurso_nucleo_operacional


@dataclass(frozen=True, slots=True)
class CoordenacaoNominal:
    fonte_textual: str
    nucleo: tuple[int, int]
    alvos: tuple[tuple[int, int], ...]
    inequivoca: bool

    def projetar(self, indice: int) -> str:
        """Entrada derivada para resolução, sem multiplicar a fonte ou o ato."""
        if not self.inequivoca:
            raise ValueError("coordenacao_nominal_indeterminada")
        return self.fonte_textual[slice(*self.nucleo)] + " " + self.fonte_textual[slice(*self.alvos[indice])]


def ler_coordenacao_nominal(texto: str) -> CoordenacaoNominal | None:
    """Lê enumeração qualificada por artigos/tipos, fora de nomes delimitados.

    Nenhum léxico de apps/dispositivos nem proposta operacional participa.
    Alternativa e modificadores que não podem ser distribuídos com segurança
    são reconhecidos como indeterminados, impedindo o fallback singular.
    Nomes como ``a pasta E Depois`` e conectores literais não criam membros.
    """
    pares = mapear_pares_aspas_globais(texto)
    if pares is None:
        return None
    externo = list(texto)
    for inicio, fim in pares.items():
        externo[inicio:fim + 1] = " " * (fim + 1 - inicio)
    externo = "".join(externo)
    nucleo = re.match(r"\s*(?P<verbo>\w+)\s+", externo)
    if not nucleo:
        return None
    conectores = list(re.finditer(r"\s+(?:e|ou)\s+|,\s*", externo[nucleo.end():], re.IGNORECASE))
    if not conectores:
        return None
    inicio = nucleo.end()
    intervalos = []
    for conector in conectores:
        fim = nucleo.end() + conector.start()
        intervalos.append((inicio, fim))
        inicio = nucleo.end() + conector.end()
    fim = len(texto.rstrip(" .!?\t\r\n"))
    intervalos.append((inicio, fim))
    intervalos = [(i + len(texto[i:f]) - len(texto[i:f].lstrip()),
                   f - len(texto[i:f]) + len(texto[i:f].rstrip())) for i, f in intervalos]
    verbo = texto[slice(*nucleo.span("verbo"))]

    def qualificado(intervalo: tuple[int, int]) -> bool:
        trecho = texto[slice(*intervalo)]
        return bool(re.match(r"(?:a|o|as|os|um|uma|esse|essa|este|esta)\s+\S", trecho, re.IGNORECASE)
                    or tipo_recurso_nucleo_operacional(verbo + " " + trecho))

    # Sem moldura nominal em todos os membros, não adivinhar listas a partir
    # de tokens em nomes nem dividir orações que pertencem à segmentação.
    if not all(qualificado(i) for i in intervalos):
        return None
    indecidivel = bool(re.search(
        r"\b(?:ou|nao|não|se|quando|caso|so|só|somente|apenas|exceto|menos|"
        r"no|na|nos|nas|para|pra|com|sem|depois|antes|agora|hoje)\b", externo[nucleo.end():], re.IGNORECASE,
    ))
    return CoordenacaoNominal(texto, nucleo.span("verbo"), tuple(intervalos), not indecidivel)


def alvo_resolvido_exato(pedido: dict, fonte: CoordenacaoNominal, indice: int) -> bool:
    """Resolução por substring não qualifica o membro nominal inteiro.

    O resolver continua dono da operação. Esta verificação só impede que um
    membro maior/ambíguo seja substituído por uma parte de seu nome. Aliases
    que não possam ser comprovados por equivalência nominal permanecem fechados.
    """
    from mente_laylay.cognicao.referencias_linguagem import separar_tipo_e_alvo_nomeado
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico

    literal = fonte.fonte_textual[slice(*fonte.alvos[indice])]
    sem_artigo = re.sub(r"^(?:a|o|as|os|um|uma|esse|essa|este|esta)\s+", "", literal, flags=re.IGNORECASE)
    primeiro = sem_artigo.split(maxsplit=1)
    tipo = tipo_recurso_nucleo_operacional(fonte.projetar(indice))
    tipos = (primeiro[0],) if tipo and len(primeiro) == 2 else ()
    alvo, _, _ = separar_tipo_e_alvo_nomeado(sem_artigo, tipos)
    params = pedido.get("params") or {}
    resolvido = next((params[k] for k in ("nome_app", "alvo", "query", "nome_playlist", "caminho")
                      if isinstance(params.get(k), str) and params[k]), None)
    if resolvido is None:
        return False
    # Nomes Windows e aliases de site aceitam a mesma normalização básica
    # usada pelos resolvers. URL/caminho/conteúdo são argumentos opacos.
    if pedido.get("intent") in {"APP_OPEN", "CLOSE_APP"} or tipo == "site" and "://" not in alvo:
        return normalizar_texto_basico(resolvido) == normalizar_texto_basico(alvo)
    return resolvido == alvo
