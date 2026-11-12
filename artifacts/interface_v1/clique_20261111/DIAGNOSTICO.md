# UI-ACK-ENTRADA-COMPACTA — 11/11/2026

Base: `fff5b04d4cf9e9a21a008dfbc517d7fc839f5794`, branch `main`.
Worktree já continha alterações em interface, geometria, mascote, CSS,
renderer, testes e diversos subsistemas; preservadas. O diff contra HEAD
inclui essas alterações anteriores e não representa somente este candidato.

## Relato e limite da conclusão

Pedro relatou que clicar na ilha a tornava aparentemente invisível. A janela
isolada com o renderer atual abriu normalmente, conforme confirmação dele.
Assim, não foi demonstrado que a falha abaixo explica todo o relato original.
O caminho completo de `laylay.py`, com a sessão pessoal, ainda precisa ser
reaberto e conferido por Pedro. Nenhuma sessão da mente foi iniciada.

## Raiz demonstrada

`iniciar_apresentacao()` coloca a ilha compacta em `starting`, com opacidade
zero, e aguarda confirmação visual. O renderer tratava todo `starting` como
preparação de expansão: exigia `desktopState === expanded` e conteúdo expandido
visível para responder. Na entrada compacta, nenhuma dessas condições existe.
Primeira fronteira RED: seleção do protocolo de confirmação no renderer,
antes da alteração de geometria ou do executor de ações.

O protocolo de preparação foi introduzido nas alterações locais anteriores;
o diagnóstico corresponde à worktree, não a uma atribuição ao HEAD histórico.

Contrato: cada transição visual deve confirmar a apresentação correspondente
ao seu estado. Entrada compacta confirma o viewport; expansão prepara o novo
conteúdo antes de animar. O owner continua sendo a janela Qt existente, com o
renderer compartilhado por todas as páginas/habilidades.

## Hipóteses concorrentes

- Falha geral de encaminhamento do clique: falsificada por eventos de mouse
  no WebEngine em três posições e pela abertura manual confirmada por Pedro.
- Geometria incapaz de expandir no Windows: falsificada pelo crescimento nativo
  de 272×36 para 1100×730 na mesma janela.
- Falha geral do renderer ou da conexão à mente: a ponte local já estava pronta
  quando a entrada compacta permanecia invisível; a prova nativa não dependeu
  de modelo, voz, rede ou executor externo.

## Candidato mínimo e validação

Produção alterada nesta tarefa: apenas `cliente/terminal_2/web_v1/interface.js`,
na condição de escolha entre preparação da expansão e confirmação do viewport.
Produção Qt, CSS, mente e executores preservados. Nenhum commit criado.

RED observado em pytest: `_entrada_pendente` continuava verdadeiro depois da
renderização compacta. RED também observado no Windows pelo diagnóstico nativo:
renderer pronto, ilha 272×36, fase `starting`, opacidade 0 antes do clique.

Após o candidato: seis testes focados GREEN, incluindo clique em três posições,
entrada com/sem movimento reduzido e preparação da expansão. Diagnóstico
nativo GREEN: entrada compacta chega a `idle` com opacidade 1; clique expande
para 1100×730, mantém opacidade 1 e não envia entradas para a mente.
Captura da superfície expandida: `expandida.png`.

Regressão final: **142 passed in 115.41s**, cobrindo desktop integrado,
interface web, ponte, estabilidade, páginas e início inteligente. Inclui o
entrypoint oficial com a ponte real e assertivas de opacidade, confirmação de
entrada e ausência da tela de erro. `node --check` e `git diff --check` no
escopo alterado passaram. Suíte global da mente não executada.

Reprodução nativa isolada, com preferências temporárias e saída automática:

```powershell
.\.venv314\Scripts\python.exe artifacts/interface_v1/clique_20261111/diagnostico_nativo.py --automatico
```
