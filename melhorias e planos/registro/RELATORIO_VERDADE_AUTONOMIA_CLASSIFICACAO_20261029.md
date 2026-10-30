# Rodada sobre verdade e autonomia — fronteiras de classificação

Journal de Pedro: `C:/Users/pbarr/Documents/Codex/2026-10-28/ch/work/ponte_sessoes/20261029T134901Z-e78610af`.
Os 14 turnos e o anexo foram lidos; a sessão terminou sem erro fatal, mas com
contingências e respostas incorretas. Isso não equivale a uma conversa aprovada.
Não foram abertas novas conversas nem chamadas Qwen. Os testes de conversa
permanecem com Pedro; as provas abaixo usam HTTP controlado, voz desligada e
efeitos interceptados, com persistência isolada.

## Base e proveniência

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. As 535 fontes históricas coincidem com a base anterior ao candidato
de resultado perifrástico. A nova base foi congelada depois daquele candidato;
as duas investigações permanecem distintas. Artefatos:
`resultados_testes/rodada_verdade_autonomia_20261029`.

O observador do serviço registra a fala derivada junto às proposições. O
diagnóstico reapresenta o conteúdo destas no schema atual, sem reenviar a fala
derivada como um segundo campo autoral. Não é replay do pacote HTTP original,
nem reconstrução de todo estado mental da sessão. A versão com histórico usa
somente as entradas e publicações reais anteriores ao alvo.

## Fronteiras demonstradas e candidatos mínimos

| Caso | Primeira divergência | Contrato e owner | Estado |
| --- | --- | --- | --- |
| `autonomia-003` | Imperativo sobre uma frase exige execução externa | `normalizacao_linguagem.tipo_transformacao_conversacional`: ato completo com alvo discursivo e sem destino externo; modalidade e segmentação reutilizam o mesmo leitor | Classificação corrigida; resposta composta ainda bloqueada pela revisão didática |
| `autonomia-014` | Vírgula separa `Para nos despedirmos` e o prefixo ganha autoridade de parada | `modalidade_turno._separar_matriz_apos_adjunto`: finalidade infinitiva com pausa tem papel subordinado; somente a matriz é classificada como possível ordem | GREEN focado e composição instalada controlada |

A redação aproveita o contrato já usado por resumo e comparação. Aceita
flexões de escrever/redigir/formular/reescrever, objetos discursivos e
modificadores de forma/canal delimitados. Não absorve destino em arquivo ou
e-mail, nome de arquivo citado nem ordem independente. Uma resposta textual
continua sujeita às guardas existentes; reconhecer o pedido não certifica o
conteúdo que o modelo vier a propor.

A finalidade reconhece infinitivo pessoal, sujeito e clítico, com pausa
explícita. Preserva o caminho anterior sem vírgula. Usa o papel canônico
`adjunto_finalidade`, evitando reclassificar a preposição ou o verbo subordinado
isoladamente. Aspas são projetadas por seus intervalos canônicos: vírgulas e
pontos no nome citado não criam outra matriz. Paradas reais continuam ordens.

Falsificações: os REDs surgem sem chamar a IA, antes de qualquer executor ou
receipt; logo, não dependem do Qwen nem de falha de execução. Trocar o detector
externo por um que sempre indica comando não deve superar a proteção
discursiva. Nos controles, escrita externa e parada continuam autorizadas;
portanto não basta remover os verbos do léxico operacional. Finalidade seguida
de pedido operacional autoriza apenas a matriz, não o objetivo subordinado.

Produção alterada nesta base: `normalizacao_linguagem.py` e
`modalidade_turno.py`. Guardas de alegações, revisão de fontes, executores,
orçamento, modelo, persona e composition root preservados. Nenhum commit.
O princípio reutilizável é **forma imperativa não basta para demonstrar efeito
externo; papel subordinado não concede autoridade**.

## Provas e limites

RED inicial: 14 falhas causais e 15 controles aprovados. Candidato inicial:
88 aprovações nos módulos novos e vizinhos. Um controle adicional expôs uma
vírgula dentro de literal sendo tratada como fronteira; o candidato passou a
usar os intervalos canônicos de aspas antes de localizar a pausa.

Foco final: 35 aprovações, incluindo quatro casos da composição instalada.
Três publicam a proposta controlada em uma chamada. O quarto é um controle
diagnóstico: o caso composto 003 já não exige efeito, mas ainda recebe o aviso
didático em duas chamadas. Esse teste NÃO prova fluidez nem resolução integral.
Uma expectativa inicial de aprovação integral foi corrigida depois dessa
evidência, explicitando a fronteira ainda aberta em vez de enfraquecer a revisão.
Outro controle passou a usar uma resposta literal pertinente ao pedido breve;
`Podemos conversar com calma` era rejeitada por falta de âncora temática.

Regressão ampliada: 161 módulos, **4.108 aprovados, zero falhas/erros**, 14
ignorados, um desmarcado, um xfail anterior e 30 subtestes. Auditoria de 535
fontes aprovada: somente os dois arquivos declarados diferem da nova base.
Consultar `regressao_classificacao_resumo.json`,
`regressao_classificacao.xml` e `auditoria_classificacao.json`. Nenhum ID ou
filtro anterior foi retirado. Essa seleção não é a suíte inteira nem um novo
teste de conversa real.

## Casos que continuam abertos, sem mistura de raízes

- `autonomia-003`, obrigação didática: o perfil de tamanho reconhece a equação
  e vira finalidade de ensino factual. É continuação da fronteira registrada
  em `RELATORIO_FINALIDADE_FICCIONAL_20261028.md`, não uma nova raiz por frase.
  O escopo ficcional atual é conservador e não cobre essa redação hipotética.
  Próxima prova: declarar o ato solicitado sem isentar uma explicação factual
  independente ou uma alegação real inserida na resposta.
- `autonomia-011`, aviso de fontes: observado historicamente; não reproduzido
  na reapresentação individual, com ou sem histórico textual. Não foi provado
  que bastaria retirar uma obrigação. A próxima fronteira exige reconstruir
  vínculo autoral, transformações e contexto factual/mental efetivamente usados.
- `autonomia-013`, revisão de argumento: `Você contou...` foi reproduzido com
  os componentes instalados, inclusive com histórico textual. O contrato de
  relato aceita conversa informativa e ancora no pedido atual, sem demonstrar
  que ele é um relato. A proposta do Qwen também inventa uma posição anterior
  sobre `não sei` como fraqueza. Não publicar essa proposta como prova da revisão.
  Próximo contrato deve distinguir pedido retrospectivo e relato, mantendo
  fontes das falas publicadas e da objeção, sem certificar paráfrase livre.
- `autonomia-005`, repetição: a resposta anterior aparece como prefixo de uma
  resposta majoritariamente nova. O detector vigente protege repetição integral
  ou predominante e preserva retomadas curtas legítimas. Reduzir limiares não
  demonstra irrelevância; investigar o núcleo da resposta e a mudança temática.

As outras duas sessões citadas no anexo encerraram por falha, mas não foram
reconstruídas a partir deste terceiro journal. Não atribuir suas falhas fatais
a uma raiz sem a evidência correspondente. Os 34 REDs de efeito já corrigidos
continuam sob seu relatório e não são contados novamente nesta rodada.
