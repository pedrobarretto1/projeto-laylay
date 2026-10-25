# C5/P01 — consulta ao que o usuário disse antes do corte lexical, 24/10/2026

## Contrato e resultado

Esta etapa trata a perda de declarações na preparação do contexto. A consulta
retrospectiva explícita ao ato de dizer do próprio usuário não pode depender
de a pergunta repetir palavras da declaração. Recuperar o diálogo solicitado
não certifica categoria, identidade de entidade, apoio semântico, verdade,
pertinência, autorização ou efeito.

Owners de produção alterados nesta tarefa:
- `mente_laylay/cognicao/referencias_linguagem.py`: leitura central do escopo
  retrospectivo próprio, reutilizando normalização, projeção fora de citações
  e o reconhecimento anterior de recapitulação;
- `mente_laylay/cognicao/seletor_contexto.py`: seleção do intervalo de falas
  do usuário quando esse escopo está explícito.

Os demais pedidos mantêm a seleção lexical anterior. A nova leitura admite
interrogativas ligadas ao relato próprio, resumo com oração relativa e perguntas
polares de relato próprio com interrogação. É um recorte gramatical, não um
interpretador completo da língua. Não resolve entidades, pessoa implícita de
“disse”, elipses ou todas as formas possíveis de consulta. Nenhuma exceção por
Obsidian, bebida, café, Nirvana ou número de turno foi adicionada à produção.

O intervalo preserva falante, texto literal e ordem, incluindo perguntas,
retificações e negações. Respostas da IA e instruções antigas não viram fontes
do usuário. Pergunta histórica permanece pergunta: recuperação não a promove
a afirmação. Não é consolidação de memória durável.

Os limites existentes de 1200/2600 caracteres, 4/8 mensagens e serialização
integral continuam no mesmo owner. Um pacote que não cabe é rejeitado inteiro,
sem publicar só uma âncora e perder a correção. A consulta de admissibilidade do
perfil rápido reutiliza essa mesma seleção; usa o perfil normal quando ele
preserva o intervalo que o rápido perderia. Não houve aumento de limites,
troca de modelo, alteração de prompts, executores ou configuração de voz.

## Base e primeira fronteira demonstrada

Branch `main`, HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, worktree
previamente suja preservada. Artefatos desta tarefa ficam em
`resultados_testes/recuperacao_atos_fala_20261024/`. O baseline contém status e
527 hashes; as cópias dos dois owners e do teste antigo alterado estão em
`fontes_antes/`. Não confundir esse candidato com o diff acumulado contra HEAD.

A coleta anterior `parafrases_historico_20261024/conversa_real` preservou cinco
casos de ausência de fonte no HTTP. Reproduzindo os mesmos pedidos internos:

| Turno histórico | Pedido | Primeira perda no seletor | Custo do intervalo completo |
| --- | --- | --- | --- |
| 6 | aplicativo que disse preferir | nenhuma âncora | 636 caracteres |
| 7 | bebida que disse não gostar | nenhuma âncora | 702 caracteres |
| 18 | aplicativo que tinha dito preferir | âncora em pergunta anterior, após a declaração | 1417 caracteres |
| 22 | bebida que tinha dito não gostar | âncora em pergunta anterior, após a declaração | 1711 caracteres |
| 29 | preferências que realmente declarei | nenhuma âncora | 2130 caracteres |

As declarações estão no histórico, no pedido canônico e no plano. Não é
apagamento da memória. Também não é excesso inevitável de contexto: todos os
intervalos completos cabem no perfil normal existente. A ausência de dados
primários no HTTP ocorre antes da geração; portanto o erro do Qwen não é
necessário para demonstrar essa perda.

Perguntas usam categorias e flexões diferentes das declarações: “aplicativo”
não está em “eu prefiro Obsidian”. Perguntas anteriores podem repetir essas
mesmas categorias sem conter a declaração original. Ancorar só nelas também
não satisfaz o pedido retrospectivo. O seletor não deve inferir que um nome é
aplicativo ou banda para recuperar o diálogo que o usuário pediu.

## Falsificações, controle de escopo e evidência

`diagnostico_baseline.json` registra os cinco pedidos, índices selecionados,
presença da fonte e custos antes do candidato. Foram confirmados 13 REDs causais
e 12 controles em `contrato_red_confirmado.xml` antes de editar produção.

Dois controles da primeira execução estavam exigindo proibir uma recuperação
lexical legítima preexistente. Foram corrigidos para usar histórico sem
sobreposição e isolar o novo mecanismo; a execução inicial foi preservada em
`contrato_red.xml`. Isso não alterou as expectativas dos REDs causais.

O primeiro auditor da factory procurava o marcador `FONTES_JSON` com um
backslash-n literal, em vez da quebra de linha. As capturas já continham as
fontes corretas. A hipótese de segunda perda no preparador/transporte foi
falsificada; nenhuma produção mudou por ela. Provas incorretamente auditadas
foram preservadas e não contadas como RED da composição. A verificação está em
`falsificacao_perda_posterior.json`.

A revisão independente identificou falso escopo no primeiro reconhecedor:
palavra interrogativa e verbo de relato eram encontrados sem vínculo de
oração. Declaração temporal, comparação metalinguística e pergunta sobre relato
de outra pessoa podiam solicitar todo o histórico. O impacto no orçamento
também foi reproduzido. Esses casos são do mesmo contrato de escopo, não novas
raízes por frase:
- `escopo_red.xml`: três REDs de temporal/metalinguagem/terceiro;
- `vinculo_oracao_red.xml`: duas variações de relato de terceiro em pergunta
  nominal;
- `pessoa_composto_red.xml`: dezesseis combinações de auxiliar/particípio
  demonstrando que a mesma regra de pessoa deve valer no pretérito composto.

A correção vincula a abertura ao relato próprio e trata os mesmos predicados
simples/compostos em ambas as posições. Preserva “Quando eu disse isso?” e
“Que horas eu disse?”, sem tomar a declaração temporal como pergunta.
A recusa de preposição solta no objeto evita aceitar uma comparação de
expressões como consulta ao ato histórico. Não se declara análise completa de
orações arbitrárias fora desse recorte.

Um teste anterior esperava não recuperar “Eu gosto de Nirvana” para “Qual banda
mencionei?”. O contrato mudou explicitamente: consultar a própria fala recupera
o dado literal; isso não deriva `Nirvana é uma banda` nem confirma a resposta.
O controle vizinho “Qual banda ganhou o prêmio?” continua sem recuperação
semântica inventada. A fonte anterior do teste foi preservada.

## Composição instalada e critérios de validação

`composicao_baseline_final.json` e `composicao_candidato_validado.json` usam o
mesmo composition root e os mesmos cinco históricos arquivados, com folha HTTP
controlada. Na base, nenhuma declaração-alvo chega ao HTTP; no candidato,
todas chegam. Os dois owners congelados são carregados em memória na contraprova,
sem restaurar a worktree. A comparação não é replay da árvore inteira do HEAD.

A primeira asserção causal exige a fonte literal no HTTP da pergunta atual,
seguida de papel/ordem, preservação da correção e ausência de autoridade/efeito.
A resposta controlada da IA não é usada como prova de recuperação ou de
entendimento. A memória raiz é redirecionada somente no loader em RAM; áudio e
efeitos ficam suprimidos. As mesmas instâncias cognitivas instaladas são
restauradas depois das folhas externas isoladas pelo helper.

O teste permanente `scripts/tests/test_consulta_fala_usuario.py` também passa
pela factory em aplicativo, bebida e jogos, inclui correção e pedido operacional
antigo, e propõe um comando não autorizado na folha HTTP. O histórico recuperado
não concede autoridade e não executa a proposta. Não foi criada uma habilidade
nem um estado paralelo por domínio.

Compreensão geral, apoio da prosa livre, pertinência, fidelidade da geração,
retomada de reformulação e entrega operacional mantêm suas raízes e owners.
Preservar C5/P01, C7, F1 e F3; não somar uma nova causa por pergunta ou confundir
fonte entregue com resposta correta.

## Qwen real e limites mantidos

As coletas usam o modelo local configurado `qwen3:4b-instruct`, sem trocar sua
configuração. Persistência isolada, voz suprimida, rede externa/processos e
dispositivos bloqueados, executor substituído por receipt negativo de simulação.

- `conversa_real`: primeira coleta, antes da restrição de escopo;30turnos,
  31HTTP200,12pacotes de fontes conferidos,527fontes sem drift,um receipt negativo,
  219,613s somados. Algumas respostas ainda negaram dados recebidos. Preservada,
  sem seleção de uma resposta favorável para substituir evidência desfavorável.
- `conversa_validada`: após restringir escopo simples;30turnos/30conclusões,
  30HTTP200,12pacotes conferidos contra os pedidos canônicos,527fontes sem drift,
  um receipt negativo,177,698s. As cinco fontes históricas6/7/18/22/29 chegaram
  ao HTTP. Respostas6/18 recuperaram Obsidian e7 recuperou café.22 ainda negou
  o registro recebido;23 aceitou indevidamente a premissa sobre Atlas;29 chegou
  ao limite de tentativas.14/20 ainda entraram em retomada operacional. Não é
  GREEN de coerência geral ou de fidelidade da geração.
- Depois dessa coleta, a restrição ao relato de terceiro foi estendida ao
  MESMO padrão composto já usado para relato próprio. As30decisões do roteiro
  permaneceram idênticas (`paridade_escopo_roteiro.json`), mas o hash mudou:
  não declarar a coleta longa como executada depois dessa última mudança.
- `foco_final`: prova da versão final,14turnos/14conclusões,13HTTP200,
  dois pacotes conferidos,527fontes sem drift,um receipt negativo,53,249s.
  11/12 receberam as declarações e responderam Obsidian/café; o revisor pessoal
  conferiu ambas. O benefício no caminho final está registrado, sem inferir
  equivalência semântica geral ou qualidade de todas as respostas.

O foco final também mostrou uma fronteira anterior distinta: em5/6, o pedido
começa com `role=user`, sem mensagem de sistema canônica. A preparação não
entra no caminho do seletor de histórico e corta as declarações, apesar de elas
existirem no pedido interno. Repetir a preparação com os dois owners congelados
produz a MESMA perda. Evidência:
`ausencia_base_primeiros_turnos_contrafactual.json`. Não foi causada pelo
candidato nem silenciada com alteração do roteiro. Não foi corrigida aqui.

A próxima investigação prioritária é localizar por que a conversa iniciada
somente pela rota rápida não mantém a base canônica antes de preparar o
pedido. O ponto observado antecede a seleção; ainda falta provar o writer/owner
responsável e criar seu contrato/RED próprios. Depois, geração com fonte entregue,
falsa adoção de pergunta como declaração e retomada operacional continuam
fronteiras separadas. Não fechar C5/P01/C7/F1 ou a compreensão geral.

## Verificação final do candidato

`contrato_final_confirmado.xml`:128GREEN, incluindo factories e49casos do
novo módulo. A revisão independente final confirmou a correção do P2 no recorte
e executou48testes leves, sem editar produção. `import_isolado.xml`:1GREEN
para o teste da composição principal deselecionado na regressão ampla por
isolamento do import. Nenhum commit ou reinício da sessão pessoal.

Regressão ampla relevante final:2.109GREEN,30subtests GREEN,14SKIP,uma
deseleção de import e uma falha anterior da calculadora:
`test_pedidos_modais_autoridade.py::test_orquestrador_deterministico_resolve_mesmo_app_apos_moldura[pode abri a calculadora para mim]`
ainda escolhe MUSIC_SEARCH em vez de APP_OPEN. A mesma falha já foi
reproduzida antes desta tarefa em
`resultados_testes/respostas_prazos_20261024/relato_composto/falha_vizinha_baseline.xml`.
Não foi silenciada nem incorporada ao patch de contexto. O comando dos85módulos
está em `regressao_comando.json`; resultado em `regressao_ampla.xml`.

Após a última restrição, o par controlado foi repetido em
`composicao_baseline_encerramento.json`/`composicao_candidato_encerramento.json`,
incluindo hashes dos owners carregados:base perde5/5fontes,candidato entrega5/5.
Produção limitada aos dois owners;script de revisão do diff contra a base,
hashes e resultados consolidados em `entrega.json`. Não se declara a suíte
inteira do repositório ou a conversa geral verde.

