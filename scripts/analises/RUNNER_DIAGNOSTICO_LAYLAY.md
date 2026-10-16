# Runner diagnóstico headless — uso pelo agente

Objetivo: deixar de escrever uma sonda nova para cada lista de perguntas/comandos.
Entradas JSON são dados; não importar código de roteiros externos. Reutiliza
`ConfiguracaoRoteiro` / `RoteiroTesteConversaRuntime` do caos, na mesma sessão
sequencial, mantendo continuidade entre entradas. Modelo Ollama local selecionado
em `configuracao.env`, sem troca de modelo ou respostas injetadas.

## Porta exercitada e limites

Usa `laylay._resposta_ia_runtime.processar`, prompt, decodificador, validador,
dispatcher, executor e publicação textual instalados. Não inicia `main`, cliente
desktop, voz, microfone ou serviços background. Prioridade, prefluxo e transição
de modo-chat são retirados **explicitamente desta porta diagnóstica** para
observar o principal e manter o bloqueio de efeitos na fronteira inspecionada.
Isso NÃO prova o roteamento prioritário/desktop normal. Para aquela fronteira,
manter os roteiros de runtime/main existentes; não substituir evidência mais forte
por este runner nem atribuir suas restrições à Laylay em produção.

Memória SQLite/resumo/pessoas/central novos na coleta; não clonar histórico
pessoal automaticamente. Neural e periféricos sem inicialização/treino; IoT
simulado, caixa Gmail desabilitada. Não afirmar isolamento de toda persistência
ou semântica visual/física. A trava canônica permanece com o launcher durante
toda a coleta; sessão Laylay existente bloqueia com código 73, sem encerrá-la.

## Execução

Planejamento, sem efeitos, padrão:

```powershell
.\.venv314\Scripts\python.exe scripts/analises/runner_diagnostico_laylay.py scripts/roteiros/dados/diagnostico_headless_exemplo.json --saida resultados_testes/runner_diagnostico/coleta_nova
```

Executar somente os pedidos canônicos em `permitidos` de cada entrada:

```powershell
.\.venv314\Scripts\python.exe scripts/analises/runner_diagnostico_laylay.py scripts/roteiros/dados/diagnostico_headless_exemplo.json --modo executar --saida resultados_testes/runner_diagnostico/execucao_nova
```

O exemplo autoriza apenas abrir Calculadora e posicioná-la à esquerda. Em
planejamento essas permissões não são usadas. Em execução efeitos reais podem
permanecer: não desfazer/fechar apps automaticamente, nem assumir que janela
preexistente pertence ao runner. Testes destrutivos/externos continuam exigindo
escopo e autorização humana apropriados; a permissão do arquivo não amplia essa
autorização. `expectativa` é gold do avaliador e nunca é enviada como autorização
ou instrução ao modelo. Pedido sem permissão exata fecha antes do executor.
Atos dependentes ainda precisam de receipt real: não sintetizar referente futuro
para melhorar a pontuação do planejamento.

`--timeout-turno` controla o sequenciador. Uma chamada síncrona pode demorar no
modelo; `--timeout-total` limita o subprocesso próprio. Após timeout/interrupção,
salvar relatório parcial, nunca reenviar automaticamente um efeito de resultado
desconhecido. Não retomar uma sessão física a partir de JSON diagnóstico.

Em baterias de planejamento, `--continuar-sem-resposta` permite coletar as
entradas seguintes após silêncio. Não remove a falha do checkpoint nem relaxa
a barreira de processamento. Recusado em `--modo executar`; padrão permanece
parar sem resposta. A opção fica registrada no baseline para comparações.

## Evidências úteis ao agente

- `baseline.json`: HEAD, branch, worktree, hashes de fonte/configuração/entradas.
- `eventos.jsonl`: journal incremental de entrada literal, prompt/modelo bruto,
  preparação, autorização/rejeição, plano, dispatcher, executor, publicação de
  receipt, resposta textual e métricas. Publicação tardia conserva entrada da
  invocação; retorno bool, tentativa, receipt recusado e efeito confirmado separados.
- `relatorio.json`: contexto antes/depois por entrada, campo alterado, comandos
  admitidos, rejeições, receipts, tempo por fronteira, primeiro alerta observado.
  O alerta NÃO declara automaticamente raiz causal. Bloqueio do runner não é
  defeito de produção; geração sem sucesso não desaparece por um fallback responder.
- `resumo.md` / `resumo.json`: índice compacto e conversa; última fronteira
  preservada em crash/timeout. Contar efeitos pela última publicação aceita de cada
  solicitação, não pela quantidade de logs nem por um receipt antigo confirmado.
- `roteiro/`: checkpoint, conversa, planos brutos e avaliação semântica originais
  do sequenciador existente. Coleta concluída NÃO significa gold aprovado.
- `runtime.log`: saída do filho em arquivo, sem abrir terminal/UI. Pode conter
  dados da sessão; manter tudo em `resultados_testes` (ignorado no Git).

Funções reutilizáveis: `carregar_entradas`, `pedido_permitido`,
`sintetizar_entrada`, `gerar_resumo` e `comparar_coletas`. Comparação exige revisar
modelo, modo, entrada literal, configuração e fonte antes de inferir melhoria.
Modelo/headers de autenticação não são substituídos nem expostos pelo launcher.

Não atualizar baseline antigo para fazer comparação passar. Usar sempre pasta
nova; o launcher recusa sobrescrita. Não editar produção para obter um relatório
verde: usar as evidências para a próxima investigação por raiz.

## Comparação de interpretação, sem execução

Para medir antes da publicação/execução, reutilizar `sonda_ordem_interpretacao.py`:

```powershell
.\.venv314\Scripts\python.exe scripts/analises/sonda_ordem_interpretacao.py --corpus scripts/roteiros/dados/interpretacao_natural_contrastes_dev_v1.json --por-ato --indicios-pos resultados_testes/interpretacao_natural_20261014/pos_dev_v3.json --modelo-real --limite 36 --saida resultados_testes/interpretacao_natural/coleta_nova.json
```

O caminho atual exercitado é a resolução **singular**, não a cadeia inteira.
Os outros braços são Qwen com schema canônico sem fronteiras pré-fixadas pelo
parser antigo e o mesmo pedido acrescido de sinais spaCy. Só C versus C+POS
compara esse enriquecimento; A versus C também muda prompt/representação/porta.
Não usar vantagem no composto contra A singular como prova de superioridade.

`--modelo-real` preserva a seleção Ollama local. Sem ele, o analisador de A é
substituído por NONE, e os braços tipificados não geram: é smoke instrumental,
não benchmark da Laylay completa. Sem `--por-ato` preserva os dois braços antigos.
O limite padrão continua14 por compatibilidade; informe36 para cobrir o corpus.

O corpus novo é desenvolvimento anotado por IA, não revisão humana ou holdout.
Gold e família são usados só depois da geração. `avaliacao_atos`,
`avaliacao_proposta`, `avaliacao_admissao` e `avaliacao_decisao_singular` são
distintas. Pontuam campos anotados e ordem, não todos os campos, equivalência
semântica de sinônimos ou efeitos. Exemplos: omitir `acao=set` quando o executor
aceita `nivel_volume` pode divergir da anotação sem representar operação errada;
alterar EM10 para set10, por outro lado, muda a operação. Revisar casos antes de
interpretar contagens. Intenção sem capacidade implementada não deve receber
gold vazio para parecer acerto.

Fixtures preservam `origem=fixture_diagnostica`, não `executor`. O owner de
continuidade pode recusá-las legitimamente; isso não prova bug em contexto real.
O contexto bruto visível em C também não recebe autoridade pelo ensaio.
Nenhum receipt futuro/dependente é fabricado para aumentar pontuação.

Amostras incrementais ficam em `.eventos.jsonl`; baseline é salvo antes do filho
em `.eventos.baseline.json`, com hashes de fonte e entradas antes/depois no
resultado final. As chamadas contadas são requisições HTTP, incluindo retries.
Falha técnica não recebe score semântico zero ou acerto por lista vazia. Não
atualizar fontes durante a coleta; qualquer deriva invalida base única.

### Indícios POS fora do ambiente principal

O ambiente de experimento criado em14/10 fica em
`resultados_testes/ambientes/spacy_pt_20261014` (Python3.11, spaCy3.8.16,
pt_core_news_sm3.8.0). Não é dependência operacional nem certifica Python3.14.

```powershell
.\resultados_testes\ambientes\spacy_pt_20261014\Scripts\python.exe -m scripts.analises.avaliacao_interpretacao_natural --exportar-pos scripts/roteiros/dados/interpretacao_natural_contrastes_dev_v1.json --saida resultados_testes/interpretacao_natural/pos_novo.json
```

Saída nova, hash exato do corpus/configuração e offsets originais são exigidos.
O tempo do parser é medido na exportação; não está incluído no tempo de Qwen
com tokens pré-computados. Carga do modelo POS não é inferência fria de Qwen,
e uma amostra por braço não prova estabilidade ou ganho causal de desempenho.
Rede pausada, voz, executores e configuração permanecem fora deste ensaio.
