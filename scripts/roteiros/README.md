# Roteiros de validação da Laylay

Esta pasta reúne os 22 roteiros antes localizados na raiz. Os arquivos removidos
foram recuperados da versão registrada no Git; mudanças não commitadas que já
tinham sido apagadas não podem ser recuperadas dessa fonte.

Executar a partir da raiz do projeto:

```powershell
.\.venv314\Scripts\python.exe laylay.py --roteiro scripts/roteiros/roteiro_reparo_parcial_conversa.py
.\.venv314\Scripts\python.exe scripts/roteiros/roteiro_teste_laylay_caos.py
```

O caos deve usar seu inicializador próprio, que prepara e restaura a fixture
musical. Pode abrir aplicativos e produzir efeitos: não executá-lo como simples
checagem de organização. Os demais roteiros também exigem revisão de escopo.

O carregador aceita os antigos caminhos na raiz como aliases quando ausentes.
Caminhos explícitos ausentes em outras pastas continuam falhando; não há busca
por nomes parecidos. Os nomes das pastas de resultado e checkpoints permanecem
baseados no nome do roteiro, não no diretório.

`sonda_transporte_evidencia.py` permanece na raiz e aceita os mesmos nomes em
`--roteiro`. Capturas e resultados ficam em `resultados_testes/`, ignorados por
conterem contexto pessoal. Testes em `tests/` e estes roteiros são código-fonte
e devem ser revisados/versionados; não são artefatos descartáveis.
