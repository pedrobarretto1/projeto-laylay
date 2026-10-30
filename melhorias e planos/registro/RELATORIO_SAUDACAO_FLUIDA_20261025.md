# F1 — cortesia integral no contrato de presença, 25/10/2026

## Pedido e base congelada

Pedro pediu estudar saudações longas e técnicas, corrigir a raiz no contrato
compartilhado e validar na composição instalada, preservando fluidez, sem voz e
com ações simuladas. Continuação do owner de presença de F1, já documentado no
mapa causal em 23/10; não contar outra raiz por cumprimento ou domínio.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. Estado e hashes de 530 fontes congelados em
`resultados_testes/saudacao_fluida_20261025/baseline.json`. Cópias anteriores em
`fontes_antes`, diff desta continuação em `candidato.diff`. Nenhum commit,
shutdown, alteração de modelo/configuração, voz ou executor.

## Cadeia causal demonstrada

1. A utterance `oi lay, tudo bem com voce?` é conversa sem autorização operacional.
2. O contrato geral exige cortesia e brevidade, mas o leitor de presença só
   reconhece algumas perguntas, como `como você está?`. Não reconhecia `tudo
   bem com você?`, pergunta sobre o dia nem saudação isolada.
3. Sem fonte de presença, o envio usa contexto geral. O payload real contém o
   retrato de corpo desconectado e suas restrições; o modelo pode redigi-los
   como resposta à cortesia, embora ninguém tenha pedido esse diagnóstico.
4. A revisão registra excesso como estilo consultivo e publica a resposta. O
   contrato conhecido de presença poderia rejeitar toda a extrapolação, mas
   não foi instalado para essas formas equivalentes.
5. Quando uma resposta de presença é rejeitada, o reparo também não reutilizava
   seu pacote: negociava prosa geral, reabrindo o assunto técnico.

A raiz demonstrada é a **lacuna de escopo entre leitura, autoria, revisão e
reparo da presença**, não uma palavra técnica específica. Não atribuir ao corpo
sozinho a causa de todo desvio livre do Qwen. Dados corporais corretos continuam
necessários em suas consultas; não foram apagados nem tornados falsos.

## Evidências e falsificações

O log final da etapa anterior continha uma saudação de cinco frases, com
sensores, temperatura e percepção, aceita com avisos de proporção. O baseline
novo reproduziu `Estou aqui e funcionando normalmente, só que agora estou
desconectada.` com HTTP 200 e sem rejeição. A pergunta sobre o dia esgotou as
tentativas; `como você está?` respondeu pelo contrato fechado existente.

Portanto, não é falha geral do transporte nem ausência de uma solução canônica.
A utterance e o contrato geral estavam presentes nesses casos; não era pedido
de diagnóstico ou autorização. Também não se deve tornar qualquer texto longo
um erro bloqueante: respostas compostas podem precisar de suas ressalvas. O
candidato não altera a política global de estilo nem trunca frases publicadas.

RED canônico: **16 falhas e 16 controles**, incluindo o texto publicado,
perguntas de outros objetos, terceiros, citações, comandos anexos e transição
para companhia corporal. O reparo aberto foi demonstrado também com a pergunta
que já tinha fonte de presença. Esses REDs precedem a alteração de produção.

## Contrato e responsáveis

| Responsabilidade | Owner | Critério de validação |
| --- | --- | --- |
| Ler o ato integral de presença/cortesia | `cognicao/presenca_conversacional._ler_pergunta` | Sujeito, vocativo e complemento são lidos integralmente; outro pedido ou complemento técnico permanece fora |
| Oferecer a redação compatível com o ato | `presenca_conversacional._realizacoes_do_ato` | Opções curtas, até duas frases; saudação, reciprocidade e atividade atual mantêm funções distintas |
| Vincular a fonte | `construir_fonte_presenca` e `realizacoes_presenca` existentes | Mesmo turno, texto, hash e ausência de execução; fonte do host não certifica corpo, efeito externo ou entrega |
| Autorizar a publicação | Verificador compartilhado já existente | Confere a realização inteira contra o mesmo owner, sem aceitar apêndice técnico ou efeito inventado |
| Reparar uma proposta inválida | `qualidade_comunicacao.montar_pacote_reparo_comunicacao` | Reutiliza `montar_pacote_presenca`; não reapresenta o diagnóstico ou rascunho rejeitado como fonte |
| Explicar uma cortesia publicada | Fonte de sentido do mesmo owner | Exige publicação integral observada; esclarece a gentileza sem inventar condição corporal |

Reutilizadas as instâncias e as integrações existentes. Nenhum parser privado
no executor, catálogo paralelo, memória durável de gosto ou nova capacidade.
Corpo ativo ou ativado entre leitura/envio preserva sua rota anterior, conferida
pelo retrato canônico. Perguntas explícitas sobre sensores e disponibilidade,
retrospectivas, terceiros e pedidos compostos não são consumidos como cortesia.

Há opções com e sem devolução da cortesia. Não se obriga uma pergunta em toda
resposta e não se escolhe pelo host uma única fala para o caso histórico. O
Qwen continua escolhendo a redação entre realizações limitadas do ato conhecido;
isso não equivale a certificar semântica livre ou experiência subjetiva.

## Candidato e regressivos

Produção alterada somente em:

- `mente_laylay/cognicao/presenca_conversacional.py`;
- `mente_laylay/cognicao/qualidade_comunicacao.py`.

O contexto geral, contrato de capacidades, revisor factual, política global de
proporção, sessão, modelo, composição e voz não foram alterados nesta raiz.

Primeiro GREEN: 66 testes. O foco ampliado revelou uma regressão real: a nova
lista recusava `Oi! Tudo bem comigo.`, antes legítima. A expectativa foi mantida
e a realização curta foi preservada. Outro RED revelou três frases ao somar
prefixo e reciprocidade; a saudação passou a integrar a primeira frase nesses
casos, sem cortar palavras da saída. `proporcao_red.xml` conserva os quatro REDs.

Foco final: **282 aprovados, dois ignorados**. O arquivo novo possui 36 casos,
incluindo esclarecimento de cortesia publicada. Artefatos `contrato_red.xml`,
`proporcao_red.xml`, `bordas_green.xml` e `foco_final.xml`.

Regressão ampla em **120 módulos**: **3.013 aprovados**, nove falhas, 44 erros,
14 ignorados, um desmarcado e 30 subtestes aprovados. `comparacao_regressao.json`
confirma exatamente os mesmos IDs das nove falhas e 44 erros anteriores:
comando natural antigo da Calculadora, expectativas antigas de pacote/tokens e
fixture que serializa `PerspectivaEnunciador`. Nenhum RED foi removido para
produzir um verde global.

## Composição instalada e Qwen

`final_dialogo` preserva 13 entradas contínuas, 13 HTTP 200 e 12 publicações.
Nove atos de presença/cortesia/esclarecimento passaram pelo contrato corrigido:
um HTTP por consulta, no máximo duas frases, sem diagnóstico técnico, sem
fontes/citações faladas e sem limite de tentativas. Exemplos publicados:

- `Oi! Tudo bem comigo.`
- `Estou por aqui, pronta para conversar. Como você está?`
- `Olá! Tudo bem comigo.`
- `Eu estava retribuindo sua gentileza e dizendo que estou por aqui para conversar.`

Os outros três turnos publicados preservam relato, gosto e retificação de
assunto. O relato livre ainda pode trazer encorajamento genérico; não contá-lo
como prova de compreensão integral ou como correção desta raiz.

A factory, intérpretes, pacote de autoria, verificador, Qwen
`qwen3:4b-instruct` e persistência são os instalados. Persistência foi isolada,
gravada e relida; 530 fontes sem drift. Sem pesquisa factual necessária para
as cortesias. O controle `seguranca_final` tem três turnos e uma ação simulada
com receipt negativo, sem efeito confirmado. Nenhuma voz reproduzida.

`auditar.py` confere respostas, fontes, escopo do payload, receipts, persistência,
hashes e falhas amplas por identidade. O coletor legado inclui uma fronteira
anterior em `indices_http`; a auditoria correlaciona pelo texto integral do
pedido realmente enviado, sem alterar o coletor ou atribuir chamada de outro
turno à consulta atual.

## Outra fronteira anterior: renovação de sessão, ainda aberta

O turno 7, `boa noite, Laylay`, **não foi publicado**. O problema também aparece
no baseline e no primeiro candidato. Não foi excluído do roteiro nem contado
como sucesso do novo contrato.

Cadeia observada: planejamento cria ocorrência → pré-fluxo reconhece despedida
→ `processar_encerramento_conversa(..., emitir_fala=False)` chama renovação →
`renovar_contexto_sessao` limpa turno/plano/contrato → o caminho deixa seguir à
LLM sem ocorrência → o Qwen gera texto → vínculo de proposta não pode ser
confirmado → publicação descartada. Trace final:
`proposta_principal_nao_vinculada`, sem falha de transporte. Estado confirma
`sessao_conversa_motivo=despedida_usuario` e os três contratos vazios.

Owners a estudar: `autonomia/pre_fluxo_contextual.processar_encerramento_conversa`,
`integracao/estado_contexto_runtime.renovar_sessao_conversa` e
`memoria_mental/sessao_conversa.renovar_contexto_sessao`. A limpeza tem função
legítima contra vazamento de contexto; não removê-la nem afrouxar o verificador
de propostas para publicar sem identidade. Próximo contrato necessário:
**encerrar contexto não deve apagar a ocorrência que ainda deve receber sua
conclusão observável**. É fronteira distinta, com política de encerramento e
autoridade própria; não corrigida neste patch de autoria.

O manifesto mantém esse RED separado. A etapa prova a correção limitada da
autoria/reparo das cortesias cobertas, não todas as saudações no runtime, conversa
geral, experiência humana, áudio físico ou encerramento completo de F1/C5/C7/AUT.
