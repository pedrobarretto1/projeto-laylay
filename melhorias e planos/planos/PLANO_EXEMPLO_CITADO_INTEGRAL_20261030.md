# Exemplo citado integral — plano por raiz, 30/10

**Objetivo:** preservar o escopo de exemplos de fala durante a revisão factual,
sem conceder prova, autorização ou receipt ao conteúdo citado.

**Base:** `1197daf0d6b5e69b7243f571542bf17666274ea2`, branch
`codex/correcao-autoria-conversa-20261030`, worktree inicialmente limpa.
Sessão `20261030T195853Z-0d4ab6c2`, evidência `casa-20261030-14`.
Baseline e fontes preservados em `resultados_testes/exemplo_citado_20261030`.

## Contrato e desenho

O owner `fundamentacao_factual.py` já distingue enunciado exemplificado de
obra citada. O reconhecimento deve abranger a citação delimitada inteira,
independentemente do tamanho e da pontuação interna. A divisão para revisão
não pode perder essa relação. Flexões condicionais de dizer, responder ou
escrever podem introduzir o conteúdo exemplificado; relato de fala passada,
título de obra e afirmação externa vizinha não herdam esse papel.

Reutilizar o segmentador discursivo compartilhado e o leitor de papéis já
existente. Não isentar ficção inteira, relaxar o codec, aumentar orçamento ou
mudar personalidade. O verificador de efeitos continua independente: citar
uma instrução ou propor um receipt não executa nem confirma ação.

Responsáveis: fundamentação factual decide o papel local; `plano_turno`
mantém sua revisão; o publicador confirma a entrega; o executor conserva a
autoridade exclusiva sobre efeitos. Nenhuma nova capacidade ou owner.

## Execução e validação

- [x] Confirmar RED com a fala histórica e variações naturais, incluindo
  citações com mais de 100 caracteres e pontuação interna.
- [x] Falsificar: truncamento de transporte, perda por higiene final e
  atribuição de experiência física como causa do corte histórico.
- [x] Aplicar candidato mínimo no owner de fundamentação, preservando
  fatos externos, obras, datas, medidas e receipts como controles negativos.
- [x] Validar exemplos de conversa, redação e instrução operacional citada;
  testar também ausência/ambiguidade de moldura e mudança de escopo.
- [x] Validar composição instalada com HTTP fixo, histórico da sessão,
  publicação nativa, perfil isolado, sem voz nem efeitos.
- [x] Rodar regressivos dos owners e revisão independente; registrar limites.

Foco217 aprovado;49 novos casos (três composições) também passaram na cópia
original após instalação por delta e guardas de hash. Comparação instalada:
base conserva corte exato, candidato publica autoria integral com uma HTTP.
Ampla123:3.625 aprovados,24 falhas/30 erros todos reproduzidos também na base;
dez falhas de preparo desapareceram após criar pastas, em ambos candidatos.
Permanecem14 falhas/30 erros anteriores, sem redução de critérios ou remoção
de testes. Sem regressão nova demonstrada, sem alegação de suíte global verde.

Testes novos: `scripts/tests/test_exemplo_citado_integral.py` e fixture
`scripts/tests/fixtures/exemplo_citado_integral.json`.

Reparos bloqueados da rodada16, ausência de publicação da18, perguntas abertas,
troca de interlocutor e seleção de contexto permanecem investigações separadas.
Testes naturais com Qwen continuam com Pedro. Nenhum desligamento ou nova
publicação Git faz parte desta etapa sem pedido atual.
