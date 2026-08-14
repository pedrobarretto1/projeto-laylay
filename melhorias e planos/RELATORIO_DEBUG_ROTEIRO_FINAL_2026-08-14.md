# Relatório de depuração — roteiro final de 88 turnos

## Fonte analisada

- Execução: `resultados_testes/roteiro_teste_laylay-20260814-010924-714787`
- Artefatos cruzados: `checkpoint.json`, `conversa.md`, `planos.jsonl` e
  `terminal.log`
- Critério do roteiro: `transporte_resposta_e_resultado_turno`
- Preparação: modo chat confirmado, atraso inicial de 10 segundos e voz
  silenciada durante o teste
- Continuidade do processo: uma ponte e uma interface iniciadas; nenhum
  reinício durante os 88 turnos

O roteiro concluiu **88 de 88 entradas**, mas `respondido` comprova apenas que
o turno terminou. A auditoria semântica foi feita separadamente, cruzando a
fala, o plano e o contrato operacional.

| Resultado mecânico observado | Turnos |
| --- | ---: |
| Execução confirmada | 62 |
| Resposta sem execução | 17 |
| Aguardando confirmação do usuário | 4 |
| Falha confirmada | 4 |
| Execução não publicada | 1 |

Latência do turno: mediana de **1,84 s**, p95 de **7,43 s** e máximo de
**20,74 s**. Houve um timeout de LLM. Quinze confirmações operacionais usaram
fallback local seguro; a causa mais comum foi fala prolixa ou JSON inválido,
não indisponibilidade geral da mente.

## Auditoria detalhada

### Turnos 1–13 — conversa, identidade e capacidade

- Identidade geral, instrução para abrir Spotify, aplicativo inexistente,
  explicação da falha e bloqueio do `obrigado de novo` funcionaram.
- `Você consegue abrir e organizar programas?` encontrou a resposta local
  correta, mas o guardião confundiu `não abri` com uma falsa alegação de
  execução e substituiu a fala por um fallback.
- `Talvez fosse legal abrir o Spotify` e `Não abra o Spotify` não executaram,
  porém a LLM negou falsamente que a Laylay tivesse acesso ao programa.

Correções: verbos explicitamente negados não são mais classificados como
execução alegada; hipóteses diretas e proibições operacionais recebem uma
confirmação local de não ação; negações falsas de capacidade são rejeitadas
pelo contrato de fala.

### Turnos 14–34 — arquivos, referências, lixeira e restauração

- Criação composta, escrita contextual, abertura, fechamento seguro,
  criação da pasta, movimentação e restauração vinculada funcionaram.
- As três consultas `Onde o roteiro correcao.txt fica?` usaram pesquisa
  aproximada e listaram arquivos não relacionados, apesar de o caminho exato
  continuar no contexto recente.
- O cancelamento da exclusão falou corretamente, mas publicou
  `confirmado=False`, fazendo o avaliador contar uma não ação segura como
  falha.
- A fala da primeira consulta de caminho recebeu uma instrução aleatória
  anexada pela autoria (`não fale... vá embora`).

Correções: consulta nominal usa o caminho recente quando o nome-base
coincide; cancelamento publica `confirmado=True`; a autoria operacional rejeita
ordens alheias ao resultado. A segunda tentativa de restauração continua
proibida depois que o mesmo item já foi restaurado.

### Turnos 35–47 — janelas, pesquisa e abas

- Posicionamento do Bloco de Notas e VS Code, abertura/maximização do Opera,
  listagem de janelas, Prime Video e fechamento exclusivo da aba funcionaram.
- `Pesquisa por documentação oficial do Python` caiu na conversa com
  `comandos=[]`.
- O `Abre o primeiro resultado` seguinte reutilizou uma pesquisa local antiga
  e abriu `roteiro_teste_laylay.py`, contaminando a continuidade web.

Correções: `SEARCH` passa pela porta determinística de leitura antes da
conversa; a continuação ordinal web só usa uma busca web confirmada. A barreira
foi posicionada depois das portas de clipboard e IoT, evitando roteadores
paralelos em turnos já consumidos.

### Turnos 48–59 — mídia e playlists

- Pausa, próxima, anterior, criação/listagem/exclusão da playlist e inclusão
  contextual de duas faixas funcionaram.
- A primeira consulta musical tratou o título genérico `YouTube` como nome de
  faixa.
- `Continua` falhou porque a extensão não confirmou reprodução. A Laylay
  relatou falha em vez de inventar sucesso; isso permanece um caso operacional
  real para reteste no Opera/YouTube.
- `Tenta de novo` preservou uma única cópia da música, mas a fala dizia que a
  playlist estava `desligada`.

Correções: títulos genéricos de plataforma não viram faixa; o estado
`playlist_musica_ja_existia` tem fala idempotente específica, sem vocabulário
de dispositivo ligado/desligado.

### Turnos 60–70 — memória, agenda e caixa de entrada

- Memória pessoal, lembrete, reagendamento, listagem e cancelamento de agenda,
  composição ideia + lembrete e referência tipada funcionaram.
- A mesma ideia apareceu duas vezes na caixa por execuções persistidas de
  rodadas anteriores.
- A pergunta sobre o presidente não contaminou o referente da ideia, mas a
  resposta factual disse que não podia confirmar em tempo real e, na mesma
  frase, alegou registro oficial. A base factual ainda precisa de fonte atual
  para perguntas políticas mutáveis.

Correções: caixa não grava duplicata ativa com mesmo tipo e conteúdo;
`nota_ja_guardada` é no-op confirmado. O foco tipado da última ideia criada
continua separado de perguntas gerais e listagens.

### Turnos 71–77 — briefing, clima e visão

- Briefing, repetição com variação, previsão de amanhã e temperatura máxima
  funcionaram.
- A descrição meteorológica `smoky haze` atravessou para o português sem
  tradução.
- A captura visual foi concluída, mas a descrição terminou no meio da palavra.
- `O que você consegue identificar?` escapou para a resposta geral de
  capacidades em vez de consultar a captura recente.

Correções: descrições climáticas conhecidas são traduzidas; limite visual
fecha em frase ou palavra e usa reticências; `VISION_QUERY` passa pela mesma
porta canônica de leitura, sem acionar a LLM conversacional.

### Turnos 78–88 — clipboard, limpeza e diagnóstico

- Leitura/transformação/restauração do clipboard, exclusão final de arquivo
  e pasta, agenda, janelas e memória pessoal concluíram.
- O diagnóstico final ainda refletiu a degradação produzida durante a rodada:
  duas falhas de impacto, uma semântica, um comando perdido e um timeout de
  LLM. Isso é evidência do estado antes destas correções, não do código agora
  validado.

## Correções implementadas nesta depuração

1. Porta determinística integrada para `SEARCH` e `VISION_QUERY`.
2. Consulta de arquivo recente por nome resolve o caminho exato.
3. Cancelamento de exclusão é uma não ação confirmada.
4. Fala própria para playlist já preenchida, sem falso `desligado`.
5. Guardas contra negação falsa de capacidade e instrução aleatória anexada.
6. Hipótese e proibição operacional recebem resposta local sem executar.
7. Deduplicação de ideias ativas na caixa de entrada.
8. Tradução da descrição climática `smoky haze`.
9. Títulos genéricos de player não são chamados de música.
10. Descrição visual não é truncada no meio da palavra.
11. Guardião diferencia `abri` de `não abri`, preservando consultas de
    capacidade honestas.
12. Desejo imediato `Eu queria que o Opera estivesse aberto agora` preserva
    `APP_OPEN` mesmo com contexto musical recente; o alvo não vira mais uma
    busca musical por `opera`.

## Validação automatizada

- Regressões exatas do roteiro e variantes próximas: aprovadas.
- Ruff nos arquivos alterados: aprovado.
- `git diff --check`: aprovado; há somente avisos preexistentes de normalização
  CRLF.
- Suíte completa: **2.773 testes e 45 subtestes aprovados** em 38,93 s.

## Pendências de teste real

1. Repetir `Pausa a música` → `Continua` no Opera/YouTube. O código deve
   continuar exigindo confirmação da extensão; não foi convertido em falso
   sucesso.
2. Validar a qualidade factual da captura real. O truncamento foi corrigido,
   mas nomes de arquivos inferidos pelo modelo visual dependem da imagem.
3. Conectar perguntas factuais mutáveis a uma fonte atual antes de afirmar
   cargo político como oficial.
4. Para comparar memória, agenda, caixa e playlists entre rodadas, iniciar com
   snapshot/restore ou um perfil temporário; o roteiro atual usa estado real
   persistente.

## Conclusão

A rodada mais recente foi contínua, terminou todos os turnos e reduziu bastante
as falhas mecânicas. Os defeitos semânticos encontrados no log receberam
regressões exatas e a suíte completa ficou verde. O próximo passo correto é
rodar novamente o roteiro real para medir as falas novas e isolar a única
falha externa ainda conhecida: a confirmação de retomada do player.
