"""Consulta local por recurso: observação de consumo não autoriza encerramento."""
from dataclasses import dataclass
import math
import re
from time import time
from typing import Any
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico


def resolver_consulta_consumo(texto: str) -> dict[str, Any] | None:
    t = normalizar_texto_basico(texto)
    m = re.fullmatch(
        r'(?:(?:por favor,? )?(?:ver|ve|veja|mostre|mostra|identifique) )?'
        r'(?:quem|qual processo|quais processos) (?:esta|estao|ta|tao) '
        r'(?:usando|consumindo|pegando|gastando) (?:(?:tanta?|muita?|mais) )?'
        r'(?P<recurso>ram|memoria(?: ram)?)(?: (?:agora|no pc))?[?.!]*', t)
    if not m:
        return None
    return {'intent': 'PROCESS_RESOURCE_USAGE', 'params': {'metrica': 'memoria'}}


@dataclass(frozen=True)
class ObservacaoConsumo:
    metrica: str
    momento: float
    processos: tuple[tuple[int, str, float], ...]
    parcial: bool
    disponivel: bool

    def fala(self) -> str:
        recurso = 'RAM' if self.metrica == 'memoria' else 'CPU'
        if not self.disponivel:
            return f'Não consegui ler o consumo de {recurso} dos processos agora.'
        if not self.processos:
            return f'A leitura de {recurso} não retornou processos com dados válidos.'
        itens = '; '.join(f'{nome} (PID {pid}): {valor:.1f}%' for pid, nome, valor in self.processos)
        alcance = 'Entre os processos que consegui ler' if self.parcial else 'Nesta amostra'
        return f'{alcance}, os maiores consumos de {recurso} são: {itens}.'


def observar_consumo(psutil_mod: Any, metrica: str) -> ObservacaoConsumo:
    if metrica != 'memoria':
        raise ValueError('métrica de consumo inválida')
    campo = 'memory_percent' if metrica == 'memoria' else 'cpu_percent'
    valores = []
    parcial = False
    try:
        for processo in psutil_mod.process_iter(['pid', 'name', campo]):
            try:
                info = processo.info
                pid, nome, valor = int(info['pid']), str(info['name']), float(info[campo])
                if not nome or not math.isfinite(valor) or valor < 0:
                    raise ValueError('amostra inválida')
                if nome.casefold() not in {'idle', 'system idle process', 'system idle process.exe'}:
                    valores.append((pid, nome, valor))
            except Exception:
                parcial = True
    except Exception:
        return ObservacaoConsumo(metrica, time(), tuple(sorted(valores, key=lambda p: p[2], reverse=True)[:5]), True, bool(valores))
    return ObservacaoConsumo(metrica, time(), tuple(sorted(valores, key=lambda p: p[2], reverse=True)[:5]), parcial, bool(valores) or not parcial)
