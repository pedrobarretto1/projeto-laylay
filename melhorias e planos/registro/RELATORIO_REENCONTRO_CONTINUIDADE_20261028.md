# Reencontro — aceitação de resposta antiga e diagnóstico da ponte

Base: HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`,
533 fontes de produção no início, worktree já modificada preservada.
Artefatos: `resultados_testes/reencontro_continuidade_20261028`.
Continuação da conferência do ato atual na conversa; não contar outra raiz
por chuva, piada, cidade ou nome artístico. F1/C5/C7/F2 conservam seus escopos.

## Evidência recuperada e falsificações

A pasta antiga em Documents estava vazia. O chat `Testar ponte ChatGPT Laylay`
identificou a mudança do pacote para Downloads. O default relativo da ponte
levou a `C:/Users/pbarr/work/ponte_sessoes`, onde os journals foram encontrados.
Foram conservadas três pastas: uma inicializada sem entradas e duas com cinco
mensagens cada. Os hashes das 666 fontes de cada snapshot não divergiam dos
arquivos correspondentes da worktree no começo desta investigação.

O protocolo tem dez entradas, oito respostas e dois erros `falha_modelo`,
confirmando a contagem relatada. Entretanto, o journal interno tem dez
publicações: nos turnos 005 e 010 houve texto entregue antes da chamada
`orcamento_bloqueado/__LAYLAY_LLM_ORCAMENTO_PRINCIPAL_DUPLICADA__`.
`SessaoLaylay.conversar` considera apenas o último resultado de qualquer
geração, inclusive a chamada de resumo posterior à publicação. A ponte
então transforma essa falha auxiliar em erro fatal da resposta inteira.
Essa causa é separada e **não foi corrigida neste patch**. Não houve evidência
de falha HTTP principal nesses dois turnos. A restrição da ferramenta para
abrir outra sessão não está comprovada pelos journals; não foi alterada.

No turno 003 a proposta já repetia os dois primeiros períodos da resposta
anterior. No 009, pedir nome artístico devolveu integralmente a preferência
por robô publicada no 007. `modelo_retornou` contém essas propostas antes de
`texto_publicado`: não era duplicação exclusiva do transporte ou do áudio.
O contexto recente estava disponível; o reencontro não prova perda geral de
memória. A causa exata da escolha interna do Qwen continua desconhecida.

A primeira divergência comprovada do host está na aceitação: o detector
existente só compara `ultima_resposta` e, fora de entrada repetida, exige
atos exatamente `{'conversa'}`. Perguntas com `conversa/pergunta` escapavam;
resposta de dois turnos antes também não era comparada. Reproduzido com os
owners instalados antes do candidato. Não foi removida obrigação factual,
autoria, receipt ou autorização para permitir conversa.

## Contrato e responsáveis

| Responsabilidade | Owner | Critério de validação |
| --- | --- | --- |
| Capturar as três falas recentes sem corte de 320 caracteres | `contrato_fala` e `RespostasAnterioresTurno` | Fonte nativa ligada ao texto/ID; projeção JSON falsa, origem diferente e fonte vencida não criam veto |
| Detectar reutilização integral | `continuidade_resposta` consumido pelo juiz comum | Toda a candidata com pelo menos oito palavras consta literalmente numa fala recente, mesmo não imediatamente anterior; não depende do tema ou do ato ser somente conversa |
| Distinguir repetição pedida de resposta nova | `referencias_linguagem` | Pedido modal integral de reprodução e consulta retrospectiva da fala não são vetados por mera igualdade; terceiro, negação e ação não recebem essa isenção |
| Reparar mantendo a tarefa | `qualidade_comunicacao` | Pergunta atual e cena recente preservadas; resposta recusada e fonte privada não voltam ao JSON da autoria |
| Produzir e verificar nova resposta | Qwen e composição instalada | Reparo recebe suporte autoral obrigatório e continua passando pelo juiz; proposta da IA não vira fonte factual |

O contrato não verifica pertinência semântica geral. O limiar de oito palavras
preserva confirmações e respostas curtas que podem legitimamente reaparecer.
Texto com alguma novidade não é certificado nem bloqueado por esta conferência.
A fonte apenas registra ocorrência de fala, com `comprova_fato=False` e
`autoriza_execucao=False`; não cria memória durável ou segundo estado de sessão.

## RED, revisão e composição

O primeiro conjunto teve seis REDs e oito controles. Cinco REDs atingiram a
aceitação/reparo; o sexto demonstrou ausência da fonte nativa. O primeiro
candidato teve erro local de materialização do iterador, corrigido no mesmo
owner. Um teste composto de cidade sem referência ficcional foi delimitado:
a revisão factual substituía a proposta antes do juiz de qualidade; não era
prova de aceitação da repetição, nem motivo para mudar a guarda factual.
O teste do juiz final usa o pedido histórico de nome que alcança a fronteira.

Revisão independente encontrou falso positivo em pedidos interrogativos de
reprodução. Cinco casos comportamentais RED foram adicionados antes da
correção do leitor compartilhado, com controles de terceiro/negação/ação.
Os controles cujo helper ainda não existia não contam como prova causal RED.
Resultados e alinhamento final dos dois vetos constam nos XMLs da etapa.

O primeiro replay usou indevidamente o texto pós-codec do journal como saída
HTTP: o campo `fala` independente é proibido no transporte V5. Foi preservado
como coleta inválida para esta fronteira. Corrigiu-se apenas a representação
do replay, removendo essa projeção redundante; texto e referências históricos
ficaram intactos e nenhuma validação de produção foi flexibilizada.

`replay_base_v5` carrega os dois owners anteriores em memória, sem substituir
arquivos. Recebe três propostas históricas pelo codec real e publica a resposta
antiga no pedido de nome. `replay_candidato_v5` usa o candidato intermediário e as mesmas
três propostas. As duas primeiras respostas permanecem; a terceira é recusada
por `resposta_repetida_literal`. A chamada adicional é Qwen real, HTTP200:
propõe **O Escalador do Buraco**, conservando a cena da biblioteca. São quatro
transportes, três históricos e um reparo novo; não são quatro novas gerações.
Auditoria confirma que o payload de reparo não contém a fala repetida nem a
fonte nativa. A porta usa a mesma supressão de pré-fluxo da ponte histórica.

A regressão ampla intermediária encontrou quatro falhas novas além das cinco
basais. O veto estava antes dos owners de realizações canônicas de opinião e
revisão histórica, que podem legitimamente repetir sua resposta conferida.
O veto lexical foi colocado após esses retornos existentes, sem isenção por
mera presença de chave/proposta. Os quatro testes originais ficaram intactos
e passaram no foco final: **174 aprovados, dois ignorados**, incluindo os 27
novos testes desta etapa. Dois REDs adicionais alinharam a exceção retrospectiva
no veto legado para `entrada_usuario_repetida=True`. A revisão independente
confirmou os 27 casos e que injetar chaves vazias não produz aprovação.

`replay_final_v5`, após esse alinhamento, confirma o bloqueio da mesma fala
antiga e a passagem ao reparo. Porém, a geração nova estourou o timeout de doze
segundos: a conclusão publicada foi uma reação à brincadeira, sem dar o nome.
Não é recuperação útil. O sucesso intermediário não encobre esse RED final;
orçamento/conclusão útil permanece aberto, sem nova coleta até obter verde
por acaso e sem aumentar prazo/modelo neste patch.

A coleta adicional `final_instalado` usa a entrada cotidiana completa: seis
turnos, seis publicações, cinco HTTP200 e um APP_OPEN simulado com receipt
negativo. A fantasia inicial foi criada e o pedido de nome recebeu um nome.
Mas explicar a cidade fictícia voltou a exigir fonte; “troque de assunto”
terminou em conclusão operacional sem ação; e o pré-fluxo capturou “você pode
repetir” como pergunta de capacidade. Esses REDs são conservados, sem atribuir
a eles a mesma raiz, sem ajustar o roteiro para obter um verde artificial.

Produção desta etapa: `contrato_fala.py`, `qualidade_comunicacao.py`,
`referencias_linguagem.py` e novo `continuidade_resposta.py`. A ponte externa,
configuração, modelo, executor e voz não foram alterados. Nenhum commit.
Todos os perfis são isolados, sem áudio e sem efeitos reais. Não encerrar
compreensão global, pertinência livre, diagnóstico da ponte ou os REDs novos.

## Regressão e auditoria final

`regressao_final.xml`: **3.695 aprovados, cinco falhas anteriores, zero erros**,
14 ignorados, um desmarcado, um xfail e 30 subtestes aprovados;139 módulos.
`regressao_final_resumo.json` compara IDs com a última ampla anterior:
nenhuma falha nova e nenhuma falha anterior desaparecida artificialmente.
As quatro regressões intermediárias foram eliminadas sem alterar seus testes.
As cinco basais continuam sendo a expectativa musical de indisponibilidade e
as quatro mutações de contrato fora do turno, documentadas na etapa anterior.
Não foram ignoradas nem reclassificadas como sucesso.

`auditoria.json` confirma 534 fontes, somente os três arquivos existentes
declarados e o novo owner alterados em produção, HEAD preservado, sem voz
ou efeitos reais. A comparação desta etapa está em `candidato.diff`, separada
das mudanças antigas da worktree. Critério lexical/repetição solicitada está
validado; recuperação útil sob timeout e os demais REDs não estão encerrados.
