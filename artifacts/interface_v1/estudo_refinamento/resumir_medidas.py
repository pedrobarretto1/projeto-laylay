"""Resume as medidas do estudo; não escreve nos fontes da interface."""
from collections import Counter
import json
from pathlib import Path
import re

PASTA = Path(__file__).parent
RAIZ = PASTA.parents[2]
for caminho in sorted(PASTA.glob('medidas_*.json')):
    valor = json.loads(caminho.read_text(encoding='utf-8-sig'))
    while isinstance(valor, str):
        valor = json.loads(valor)
    print('VIEWPORT', valor['viewport'])
    for aba in valor['abas']:
        altura = aba['viewportHeight']
        principais = [(acao['text'], acao['y'], acao['height']) for acao in aba['actions']
                      if 'Abrir player' in acao['text'] or 'Salvar configuração' in acao['text']]
        print(aba['name'], 'conteudo/visivel', f"{aba['contentHeight']}/{altura}",
              'textos<12px', f"{aba['textBelow12px']}/{aba['textElements']}",
              'fontes', ','.join(aba['fontSizes']), 'alvos<32', len(aba['smallTargets']),
              'acoes', principais)

html = (RAIZ / 'cliente/terminal_2/web_v1/index.html').read_text(encoding='utf-8')
print('CSS', {
    'blocos': len(re.findall(r'<style\b', html)),
    'fontes_px': dict(Counter(re.findall(r'font-size:\s*([\d.]+px)', html))),
    'raios': Counter(re.findall(r'border-radius:\s*([^;}]+)', html)).most_common(12),
    'cores_literais_distintas': len(set(re.findall(r'#[a-fA-F0-9]{3,8}\b', html))),
    'transicoes': dict(Counter(re.findall(r'transition:\s*([^;}]+)', html))),
})
