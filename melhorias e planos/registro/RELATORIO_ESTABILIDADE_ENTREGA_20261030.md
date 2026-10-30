# Estabilidade de entrega e continuidade do canal ChatGPT

## Base e evidência histórica

Investigação autorizada por Pedro após o relato de falhas às21:29, com testes
de conversa mantidos com ele. Não contar falhas de protocolo, recusas da revisão
e lacunas de histórico como uma única raiz. Continuação do diagnóstico anterior
de resultado auxiliar/entrega e das famílias de posicionamento e encerramento.
Os IDs anteriores e pendências não foram removidos.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, main, worktree suja preservada.
Base de538 fontes em `resultados_testes/estabilidade_entrega_20261030/base`,
com hash/status em `baseline.json`. Backups das duas distribuições da ponte em
`base_ponte` e `base_ponte_canonica`. As cópias de Downloads e Documents eram
distintas; o adaptador não integra o manifesto dos fontes da Laylay. Não tomar
o código atual da ponte como reprodução exata da versão que iniciou cada log.

Lidos os seis journals `20261030T001314Z` a `20261030T002918Z` na pasta indicada
de Documents:32 entradas e32 publicações internas;27 respostas de protocolo e
cinco `falha_modelo`. Há ainda duas recusas de ID duplicado, sem nova entrada
no runtime. Todas as538 fontes de produção dos snapshots coincidem com a base
congelada desta investigação. Isso falsifica uma divergência desses fontes
como causa da rodada; não prova identidade de dependências/latências/adaptador.

Cinco IDs com erro: `identidade-007`, `identidade2-004`, `identidade3-006`,
`identidade-retoma-003` e `fecho-identidade-009`. Em todos existe publicação
interna, mas nem toda publicação corresponde à proposta temática original:
algumas são contingências após revisão/geração recusadas. O journal não permite
concluir que todos os rascunhos eram corretos ou publicáveis.

## Resultado de geração não é resultado de entrega

O adaptador antigo usava apenas o último `modelo_retornou.sucesso` para decidir
`modelo_falhou`. Assim uma chamada auxiliar/reparo recusada apagava, no protocolo,
uma entrega já registrada. O contador de mensagens é ilimitado nesses logs;
timeout de processo, falta geral de texto e queda obrigatória na quinta mensagem
não explicam essa decisão do adaptador.

O candidato reutiliza `OrquestradorFalaRuntime.textos_publicados_turno`, owner
existente de confirmação textual. O observador também exige o `mensagem_id` da
ocorrência atual. Texto só gerado, proativo ou de outro turno não fornece receipt.
Falha posterior não transforma entrega em ausência. O journal passa a registrar
`PedidoModelo.tipo_chamada`, sem inferi-lo da rota genérica `principal`.

Falhas continuam observáveis em `falhas_geracao`. Uma conclusão textual com
falha de geração da resposta tem `degradada=true`; não é classificada como geração
perfeita. Manutenção permanece separada. Sem texto confirmado, continua havendo
erro: só um retorno síncrono com `turno_concluido=true` pode manter a sessão
disponível para outra entrada. Timeout do processo, ID inválido, exceção e ação
bloqueada continuam fechando a sessão. Não se publica o JSON bruto como recuperação.

RED do adaptador antigo:5 falhas/1 controle. Testes do candidato incluem entrega
seguida de manutenção falha, contingência após falha de reparo, texto alheio,
proposta sem publicação e tipo de chamada no journal. Controles anteriores de
timeout, correlação, duplicata e ação bloqueada foram mantidos.

## Duas recusas sociais comprovadas, com owners distintos

`identidade2-004`: o guardião biográfico absorvia “eu precisei revisar” no
predicado “você tem razão”. Pausa com travessão, vírgula ou ponto e vírgula não
preservava a troca explícita de sujeito. O owner `afirmacoes_interlocutor`
mantém a classificação dialógica do núcleo e usa o léxico existente para a
autodeclaração explícita seguinte. Sujeito omitido/segunda pessoa e outro
predicado pessoal permanecem fora dessa leitura. Não certifica a autodeclaração;
fatos, experiências, efeitos e receipts continuam nos demais guardiões.

`fecho-identidade-009`: o primeiro reparo já agradecia, mas o owner de aderência
exigia sua lista particular de respostas como “de nada”. Reconhecimento de
reciprocidade agora inclui matriz autoral positiva de agradecer, fora de
citação. Não concede evidência aos detalhes da frase, nem libera perguntas
que reabrem um encerramento. Não são exceções para identidade, anestesia ou
perdão; a mesma leitura é compartilhada pelos pedidos que alcançam os owners.

RED causal social:6 falhas/7 controles. O primeiro roteiro com agradecimento
composto não atingia `encerramento_social`; foi preservado como experimento
mal delimitado, e a pergunta canônica “Obrigado!” alcançou a fronteira correta
antes do patch. Não se conta erro de fixture/import/indentação como RED de produção.

Comparação base/candidato com propostas históricas e componentes instalados,
sem nova geração e sem reproduzir latência: em `identidade2-004`, duas chamadas
e contingência passam a uma chamada com a primeira proposta; no fecho, o mesmo
primeiro reparo passa a ser publicado integralmente em duas chamadas. O texto
pós-codec foi reconstruído para o transporte V5 retirando apenas `fala` redundante;
quando faltava suporte, declarou-se o texto com fontes vazias. Não são novas
amostras do Qwen nem prova de verdade de cada afirmação filosófica/médica.

## Enquadramento do interlocutor chegava ao pedido, mas não ao payload

A ponte inseria sua identidade como outro `system` no conjunto de mensagens.
Na composição real, a seleção de histórico do preparador descartava esse item.
Portanto adicionar instrução de reencontro ou personalidade no adaptador não
garantia que o modelo a recebesse. O teste pelo construtor real reproduziu:
histórico disponível no payload, mas nenhuma identificação de canal.

Contrato compartilhado: `ContextoCanalConversa`, opcional e nativo em
`PedidoModelo`, contém canal/interlocutor/instrução limitada do host, com
`autoriza_execucao=false` e `comprova_fato=false`. O preparador aplica esse
enquadramento depois da seleção, como prefixo do contrato principal. Não
promove texto de `user`, página, JSON do modelo ou histórico a instrução.
Controles cobrem ponte ChatGPT e terminal de visitante, modos rápido/normal,
contexto fechado e duas compactações posteriores. Nenhum orçamento foi aumentado.

Dois testes antigos da ponte foram atualizados para usar `PedidoModelo` e o
preparador reais: o dublê que somente copiava `mensagens` não implementava o novo
contrato. Mantidas identidade, imutabilidade, correlação e ausência de autoridade;
o teste ficou mais próximo da composição. Os demais35 casos da ponte passaram.

## Retomada ancorada no protocolo e estado canônico

Na distribuição recente em Documents havia um resumo fixo afirmando temas
mesmo sem arquivos, além de excertos cortados a190/230 caracteres. Essa versão
foi preservada antes de substituí-la; é diferente da cópia antiga em Downloads.
O candidato remove o resumo e o carregador paralelo. Não usa a proposta do
modelo como evidência de uma lembrança.

O carregador retoma até6 pares integrais/12.000 caracteres dos16 journals
recentes do mesmo canal/projeto. Exige entrada ChatGPT e resposta correspondente
efetivamente enviada, origem Laylay, interlocutor ChatGPT e ações desabilitadas.
Não importa erros, publicações só internas, respostas degradadas, IDs alheios,
outros projetos ou dados pessoais de Pedro. Para journals antigos sem projeto,
há migração limitada pelo manifesto/hash da composição raiz. Links, arquivos
excessivos ou JSON inconsistente não fornecem histórico.

Os pares vão para `memoria_conversa.messages`, estado canônico já consumido
pelo runtime. Não há outra memória, sumarizador ou geração auxiliar. Proveniência
em `continuidade.json` e no evento `continuidade_carregada`; `pronta` informa
`turnos_retomados`. Sem fontes, o contexto reconhece a lacuna sem afirmar um
reencontro factual. `--nova-conversa` desativa a retomada.

Essa retomada de canal não é autenticação de pessoas, memória ilimitada ou
certificação dos fatos contidos na conversa. As regras de fonte e autorização
continuam independentes. A identidade ChatGPT não vira Pedro porque a mensagem
diz “sou eu”. O estilo existente da Laylay foi preservado; sua manifestação
espontânea com o modelo precisa do próximo teste natural de Pedro.

## Validação e escopo

-35 testes anteriores da ponte aprovados, sem remover casos.
-Ensaios pelo construtor real de `SessaoLaylay`, composition root instalado,
  orçamento e orquestrador reais; HTTP fixo, perfil/memória privados antes dos
  imports, auditoria de socket/subprocesso/escrita. Nenhuma violação observada.
-Casos instalados: reciprocidade sem reparo, autodeclaração sem biografia,
  falha auxiliar posterior à entrega, carregador de journal até estado/payload,
  timeout HTTP seguido de outro turno na mesma sessão, receipt/ação inventados.
-Regressão ampla relevante:180 módulos,4.588 aprovados,zero falhas/erros,
  14 pulados,um deselecionado,um xfail e30 subtestes aprovados;469,78s.
  Mesmo filtro da ampla anterior, nenhum ID anterior removido. Uma variante
  adicional de despedida foi aprovada no foco final de sete composições depois
  de a coleta ampla já ter carregado os módulos; sem alteração de produção.
  Comando integral, log, XML e comparação de IDs preservados nos artefatos.
-Auditoria: exatamente quatro fontes existentes de produção alteradas entre538;
  nenhuma fonte nova de produção. Cópias da ponte em Documents e Downloads
  alinhadas por hash nos quatro módulos, com backup de cada base distinta.

Produção alterada nesta investigação: `cognicao/afirmacoes_interlocutor.py`,
`cognicao/validacao_contrato_fala.py`, `integracao/registro_conversa_llm.py` e
`integracao/preparador_requisicao_llm.py`, sob `mente_laylay`.
Na ponte: adaptador, protocolo, novo carregador de continuidade e documentação;
a distribuição antiga recebe a tela já existente na versão usada nas sessões.
Sem commit, troca de modelo, prazo adicional, voz ou efeitos reais.

O replay ainda conserva limitações temáticas em `identidade3-006` e
`identidade-retoma-003`: a existência de texto gerado não certifica que ele
atendeu à pergunta. Um desses logs registra `contrato_saida_invalido` sem corpo
HTTP original, insuficiente para provar a causa sintática/semântica do JSON.
Não se declara esse defeito do Qwen resolvido, nem se libera uma proposta
recusada para evitar o erro. A queda indevida da sessão é tratada no contrato
de entrega; os problemas de redação/classificação/revisão continuam ligados
às suas próprias fronteiras. Nenhuma conversa nova foi executada aqui.

## Adendo da investigação temática seguinte

O replay deste relatório reapresentava `partes` pós-codec como se fossem o
corpo HTTP V5, que negocia `texto` integral. Sua contingência inicial não comprova
uma recusa semântica do runtime histórico. A coleta foi preservada; reconstrução
de transporte, comparação corrigida e limites da evidência estão documentados
em `RELATORIO_LIMITES_TEMATICOS_20261030.md`. Os resultados independentes de
entrega, canal e continuidade acima não dependem dessa representação do replay.
