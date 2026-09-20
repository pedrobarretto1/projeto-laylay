# Laylay — registro de problemas e correções

Atualizado em **19/09/2026**, por Astra, a pedido do Pedro.

Este é o índice central dos problemas encontrados enquanto corrigimos outros
problemas. Serve para não perder achados, não misturar causas e deixar claro o
que falta. Os relatórios ligados abaixo preservam o diagnóstico detalhado.

O preenchimento inicial usa os relatórios de 12–15/09 e as validações da última
rodada. **Não é uma auditoria exaustiva nem uma nova execução dos testes.**
Uma ocorrência antiga permanece datada até ser revalidada.

## Como manter este arquivo

- Ao encontrar um problema lateral, registrar aqui antes de desviar da correção atual.
- Manter o ID do item; atualizar seu estado e acrescentar evidências, sem apagar o histórico.
- Separar sintoma de causa: várias falhas podem ter a mesma raiz; isso precisa ser provado.
- Informar se a evidência é de runtime, integração ou teste unitário.
- Só marcar uma correção como validada no escopo depois de registrar o teste e seus limites.
- Impacto indica risco, **não muda automaticamente a ordem do trabalho** nem autoriza ações destrutivas.
- Nunca copiar credenciais, tokens ou conteúdo pessoal desnecessário para este índice.
- Ideia futura não é defeito e não significa implementação aprovada.

Estados usados: **a investigar**, **reproduzido**, **parcial**, **limite não validado**,
**adiado**, **validado no escopo** e **ideia guardada**.

## Visão rápida das pendências

| ID | Assunto | Estado | Impacto |
| --- | --- | --- | --- |
| P01 | Explicações ruins sobre como usar capacidades | Parcial: catálogo preservado; qualidade ainda aberta | Coerência e confiança |
| P02 | Recomendações técnicas sem evidência suficiente | Adiado; RED histórico aberto | Alto: informação técnica inadequada |
| P03 | Confirmação de playlist antes do receipt | Reproduzido em integração | Alto: confirmação prematura |
| P04 | Divergência no contador de ADD do teste composto | Reproduzido em integração | Diagnóstico a esclarecer |
| P05 | Presença não cede na transição da entrada para o turno | Reproduzido em teste de integração | Interferência na fala do usuário |
| P06 | Ponto de extensão em nome de arquivo | Reproduzido em teste; xfail conhecido | Interpretação do alvo |
| P07 | Continuidade na rota exclusivamente de áudio | Limite não validado | Possíveis lacunas de histórico |
| P08 | Credencial em logs históricos do Chrome | Parcial: saída nova corrigida | Alto: artefatos sensíveis |
| P09 | Novos testes ficam ignorados pelo Git | Confirmado por configuração | Perda de regressões no versionamento |
| P10 | Falso positivo de fundamentação em citação | C10/C14 validados para exemplos e recursos tipificados; escopo mais amplo aberto | Proteção não deve apagar instruções válidas |
| P11 | Pedido de informação confundido com afirmação de estado | Validado no escopo; ver C08 | Fallback desnecessário corrigido nos casos cobertos |
| P12 | Pergunta de procedimento sem natureza operacional reconhecida | Classificação validada no escopo C11; resposta final ainda falha | Reparo posterior separado em P16 |
| P13 | Nome de aplicativo não recupera seu domínio no catálogo | Recuperação validada no escopo C12 | Resposta final ainda afetada por P10 |
| P14 | Resposta prioritária IoT troca ação e dispositivo | Corrigido e validado no escopo C13 | Qualidade mais ampla da autoria continua em P01 |
| P15 | Timeout tratado como pedido ambíguo | Reproduzido no runtime; causa da latência aberta | Pede reformulação de pergunta já clara |
| P16 | Reparo de explicação presume relato de ação passada | Validado no escopo C15 | Objetivo e fonte preservados; qualidade geral ainda em P01 |

A frente atual é **P01**. O corte do catálogo (C07) e o falso reparo P11 (C08)
foram tratados separadamente; falta melhorar a realização da explicação. A investigação
de recomendações **P02** foi adiada para não bloquear indefinidamente a rede.
Este índice não altera essas decisões e não promove a rede neural.

## Pendências detalhadas

### P01 — Explicações de capacidade e instruções pouco coerentes

- **19/09, após C15:** no reparo real de volume, o Qwen manteve a explicação,
  mas ainda acrescentou requisito de PC remoto. O verificador retirou essa frase
  (`plataforma_sem_evidencia`) e preservou a instrução. Na mesma sonda, IoT
  transferiu ao usuário a responsabilidade de reler o dispositivo. Próxima
  investigação: escopo dos limites e responsabilidades na documentação por
  capacidade/rota, sem retirar a proteção factual ou criar falas fixas.
- **Encontrado durante:** validação de recusas e continuidade do histórico.
- **Exemplo:** “como eu poderia pausar a música?” recebeu explicações de acesso
  ao player e digressões desnecessárias, apesar de a pergunta direta de capacidade
  ser respondida pelo catálogo local.
- **Comprovado:** desvio no runtime em sondas de 14–15/09. Não houve comando.
- **Atualização de 15/09, tarde:** a captura nas duas fronteiras provou perda do
  catálogo na compactação HTTP: presente no pedido/preparação, ausente no envio.
  C07 preserva a evidência nas rotas normal e rápida. O contrato de não execução
  não mudou; o problema não se resume à competência do Qwen ou ao histórico.
- **Ainda aberto:** a descrição geral das capacidades, agora entregue, não bastou
  para produzir uma instrução boa. A sonda posterior chegou a um fallback por P11.
  Portanto **P01 não está encerrado**, apesar do transporte corrigido.
- **Próximo passo após C08:** reavaliar a realização de instruções com o catálogo
  vivo, inclusive disponibilidade negativa, sem converter pergunta em autorização
  nem criar uma resposta fixa por habilidade. Na sonda de 17:19 a fala não teve
  fallback, mas incluiu “não preciso te ensinar nada”: qualidade e tom ainda RED.
- **Fechar quando:** explicações úteis e verdadeiras, com capacidade disponível e
  indisponível, passarem por contrastes e runtime sem execução não solicitada.
- **15–16/09 — candidato C09:** tarefa de autoria textual separada do planejamento,
  com documentação viva ligada ao texto/ID do turno. Sem fala fixa por habilidade;
  pergunta continua sem autorização e propostas indevidas continuam bloqueadas.
  Disponibilidade parcial, vários atos e referências não recuperadas conservam
  o fluxo completo. A personalidade-base não foi reescrita.
- **Resultado intermediário:** o Qwen passou a ensinar o pedido de pausa; a primeira
  sonda revelou que P10 apagava esse exemplo após a geração. Após o candidato C10,
  os turnos 1 e 2 da sonda de 15/09 às 18:50 chegaram inteiros ao chat. Essa sonda
  foi **interrompida após 8/12 respostas**, não é uma execução concluída.
- **Limites descobertos:** P12/P13 mantêm quatro REDs (duas entradas, rotas normal
  e rápida). P14 é uma resposta fixa anterior à LLM, portanto não se resolve com
  o prompt novo. Não declarar P01 globalmente corrigido.
- **Validação final de 16/09:** seleção ampliada com **1.307 aprovados e quatro
  falhas**, todas de cobertura P12/P13. Sonda completa de 12 mensagens: dez
  aprovações mínimas, duas falhas IoT e zero comandos. Exemplos de pausa/retomada
  preservados no chat; ofertas laterais, promessas e continuação presumida ainda
  impedem considerar a qualidade globalmente aprovada.
- **Evidência:** [histórico e sondas de 15/09](RELATORIO_COLETA_DEBUG_20260914.md#histórico-de-respostas-locais-e-continuidade--15092026).
  [Diagnóstico do corte e resultado parcial](RELATORIO_COLETA_DEBUG_20260914.md#capacidades-relevantes-no-transporte--15092026).

### P02 — Recomendação técnica sem vínculo verificável com fontes

- **Encontrado durante:** correções dos relatos do Pedro sobre hardware e pesquisa.
- **Última evidência registrada:** 13/09. O modelo ainda recomendou uma peça com
  especificações não sustentadas mesmo recebendo instrução para não escolher sem base.
- **Estado:** adiado por decisão anterior do Pedro; candidato de prompt retirado.
  Não considerar as recomendações das sondas seguras para montagem ou compra.
- **Próximo passo quando retomado:** ligar requisitos informados → candidatos →
  fontes → afirmações; comparar atende/não atende/não comprovado. Reutilizar pesquisa
  e coordenação existentes, sem criar uma habilidade para cada peça.
- **Fechar quando:** faltas de dados, fontes contraditórias e pesquisa indisponível
  não produzirem especificações, compatibilidades ou pesquisas inventadas no runtime.
- **Evidência:** [relatório de recomendações e retirada do candidato](RELATORIO_CORRECOES_CONVERSA_20260912.md).

### P03 — Playlist: fala de confirmação anterior ao receipt

- **Encontrado durante:** regressão ampliada da correção de histórico, em 15/09.
- **Comprovado em teste:** o receipt aparece depois da chamada de voz (`4 < 3`
  falha). O teste alcança CREATE/ADD; não falha no import.
- **Contrato:** receipt confirmado antes da confirmação verbal de efeito.
- **Próximo passo:** rastrear a ordem no fluxo canônico de feedback e comparar
  a composição do teste com produção. Não afirmar que a falha de produção atual
  foi reproduzida apenas porque esse teste falhou.
- **Fechar quando:** sucesso, falha e idempotência publicarem resultados na ordem
  correta, com regressão de composição e prova no runtime.
- **Teste:** [test_red151_c3_guardiao_receipt_saida.py](../tests/test_red151_c3_guardiao_receipt_saida.py),
  `test_red151_c3_feedback_simples_registra_receipt_antes_da_fala`.
- **Controle:** a falha persistiu com o candidato de histórico desativado em memória.
  Detalhes no [relatório de 15/09](RELATORIO_COLETA_DEBUG_20260914.md).

### P04 — Playlist: contador do ADD diverge do resultado composto

- **Encontrado durante:** a mesma regressão de 15/09; relacionado a P03, mas
  **não há prova de raiz compartilhada**.
- **Comprovado em teste:** a playlist e a faixa passam pelas asserções anteriores;
  depois, `add_final` esperado como `1` vale `0`.
- **Não concluir:** que a faixa deixou de ser salva. A falha observada é no contador.
- **Próximo passo:** verificar se a instrumentação acompanha o executor real ou
  se há uma divergência de composição/fluxo. Não mudar a expectativa só para passar.
- **Fechar quando:** a cadeia materialização → ADD → receipt → contador tiver
  explicação causal e validação coerente.
- **Teste:** [test_red151_runtime_canonico_c3.py](../tests/test_red151_runtime_canonico_c3.py),
  `test_red151_c3_runtime_canonico_146_151_cria_salva_responde_sem_llm`.
- **Controle:** também persiste sem o candidato de histórico em memória.

### P05 — Presença na transição entre entrada aceita e turno criado

- **Encontrado durante:** regressão de 15/09.
- **Comprovado em teste:** o evento de presença retorna `proposta_cognitiva`
  quando o teste espera `bloqueada`, depois da entrada aceita e antes do turno.
- **Contrato esperado:** a entrada já aceita do usuário deve ter prioridade
  nessa janela, não apenas depois da criação do plano.
- **Próximo passo:** mapear quem possui essa prioridade e sua propagação entre
  aceite da entrada, agendamento e diretor de presença; confirmar a composição real.
- **Fechar quando:** corrida controlada e runtime preservarem a prioridade sem
  silenciar definitivamente a iniciativa legítima.
- **Teste:** [test_red_p1h4_handoff_entrada_turno.py](../tests/test_red_p1h4_handoff_entrada_turno.py),
  `test_red_p1h4_entrada_aceita_preempta_presenca_antes_do_turno`.
- **Controle:** persiste sem o candidato de histórico em memória.

### P06 — Segmentação de nomes como `antonio.txt?`

- **Encontrado durante:** testes de pedidos modais e recusas, em 14/09.
- **Evidência registrada:** o segmentador corta no ponto da extensão; xfail conhecido.
- **Próximo passo:** preservar a estrutura do nome/caminho durante a segmentação,
  sem transformar toda pontuação em texto literal nem usar ausência de `?` como autorização.
- **Fechar quando:** nomes com extensão, caminhos, perguntas e frases compostas
  preservarem alvo e modalidade, sem regressão de segurança.
- **Evidência:** [registro de pedidos modais e xfails](RELATORIO_COLETA_DEBUG_20260914.md).

### P07 — Histórico sem publicação textual confirmada

- **Encontrado durante:** definição dos limites da correção C02, em 15/09.
- **Estado:** limite de cobertura, **não bug de áudio já reproduzido**.
  O novo registro usa confirmação dos canais textuais; aceite na fila de voz
  não prova que alguém ouviu a fala.
- **Próximo passo:** rastrear o caminho exclusivamente de áudio e o evento real
  de entrega, incluindo cancelamento, interrupção, fala tardia e troca de chat.
- **Fechar quando:** um contrato de entrega apropriado sustentar o histórico
  dessa rota sem registrar fala cancelada como entregue.
- **Evidência:** [limites da correção do histórico](RELATORIO_COLETA_DEBUG_20260914.md#histórico-de-respostas-locais-e-continuidade--15092026).

### P08 — Logs antigos podem conter credenciais

- **Encontrado durante:** sonda Chrome de 14/09.
- **Comprovado:** uma URL de callback com token foi impressa antes da sanitização.
  Não copiar seu conteúdo para este arquivo.
- **Já corrigido:** sanitização na saída do handler; ver C05.
- **Pendente:** os artefatos antigos não foram apagados nem higienizados; não
  compartilhar ou versionar logs brutos. A correção não foi uma auditoria global.
- **Próximo passo:** delimitar artefatos afetados e combinar com Pedro o tratamento
  de material sensível e eventual revogação da credencial, sem usá-la.
- **Fechar quando:** tratamento dos artefatos e da exposição estiver documentado;
  sanitizar logs novos, sozinho, não encerra esse item.
- **Evidência:** [achado de segurança e sanitização Chrome](RELATORIO_COLETA_DEBUG_20260914.md).

### P09 — Testes novos fora do versionamento

- **Verificado em 15/09:** `git check-ignore -v` aponta `.gitignore:10:tests/`
  para `test_historico_turnos_locais.py` e `test_recusas_alteracao_canonica.py`.
- **Impacto:** os arquivos existem e executam localmente, mas novos testes podem
  não entrar num commit normal. Isso não apaga os testes já rastreados.
- **Próximo passo:** revisar a política de ignore de testes separadamente, mantendo
  artefatos e dados sensíveis excluídos. Nenhuma regra foi alterada nesta organização.
- **Fechar quando:** regressões necessárias puderem ser versionadas com segurança,
  sem adicionar arquivos em massa nem expor dados de teste pessoais.

### P10 — Citações confundidas com conteúdo que exige fundamentação

- **Última evidência registrada:** sonda de 13/09 tratou uma citação de estado
  emocional como obra; ainda estava aberta naquele relatório.
- **Estado atual:** requer revalidação após as mudanças posteriores nos guardiões.
  Não presumir que é a mesma raiz das recusas já corrigidas.
- **Próximo passo:** recuperar o turno e verificar a primeira classificação incorreta,
  contrastando citação, transformação textual e afirmação factual independente.
- **Fechar quando:** essas operações forem distinguidas sem liberar fatos inventados.
- **Evidência:** [limites das sondas de reparo parcial](RELATORIO_CORRECOES_CONVERSA_20260912.md).
- **Revalidação 15/09:** a resposta HTTP “Para pausar a música, basta dizer
  'pausa a música'” foi aceita na preparação, pesquisada como obra e cortada no
  verificador final. Captura `transporte_evidencia-20260915-184447-325549`;
  roteiro `roteiro_recusas_autoria-20260915-184448-437661`, turno 10.
- **Candidato C10:** extrator compartilhado distingue exemplos de enunciado de
  títulos candidatos. Validação factual continua examinando dados externos ao
  exemplo; uma citação didática não dispensa a verificação da frase inteira.
  A variante indireta “pedir para …, por exemplo” reutiliza o classificador
  canônico para reconhecer o exemplo, sem tratá-lo como fala autorizante.
- **Regressão detectada e corrigida durante validação:** retirar o título candidato
  também retirava o gatilho factual de uma data externa à citação. Separados
  `contem_citacao_destacada` e `extrair_titulos_citados`; o teste existente de
  metalinguagem/data voltou a passar sem alteração de expectativa.
- **Escopo:** citações didáticas explícitas, não toda citação emocional ou toda
  metalinguagem. O caso histórico original de 13/09 ainda requer revalidação.
- **Validação de 16/09:** 27 contrastes próprios; 42 aprovados com metalinguagem.
  Exemplos de pausa e retomada preservados na geração real e entrega ao chat da
  sonda `roteiro_explicacao_capacidades-20260916-084558-409596`.
- **Novo limite às 09:37:** “abrir o programa 'Calculadora'. Por exemplo:
  'abre a calculadora'.” retorna dois títulos no extrator; o runtime pesquisou
  Calculadora na Wikipédia e substituiu a explicação. Nome de entidade citado e
  exemplo em frase separada não são cobertos por C10. Não corrigido junto com C12.
- **C14, 19/09:** separados os papéis de exemplo de enunciado, referência
  operacional tipificada e obra candidata. Nome de recurso deixa de ser título,
  mas não tem datas/medidas mascaradas nem comprova estado. “Programa” requer
  moldura operacional para não liberar títulos de rádio/TV. Exemplo na frase
  seguinte exige orientação de pedido imediatamente anterior e leitura canônica
  do trecho como pedido/consulta; não libera qualquer citação após “por exemplo”.
- **Validação:** oito REDs causais → GREEN; 48 testes de citações ao final.
  Seleção ampliada: **2.801 aprovados, 14 xfails preexistentes, 30 subtests**.
  Replay da resposta histórica no processo real chegou inteiro ao chat;
  geração nova também preservou a instrução e manteve verificação de fatos
  adicionais. O caso emocional original de 13/09 não foi revalidado.

### P11 — Pedido de informação tratado como estado afirmado

- **Descoberto em:** 15/09, na validação real da preservação do catálogo (P01/C07).
- **Observado:** “me diga o nome da música ou o app que tá rodando, para eu te
  ajudar a localizar” foi marcado como `resultado_operacional_sem_evidencia`.
  O reparo também foi rejeitado e a resposta virou “Dá pra responder, mas agora
  seria no chute. Explica só um pouquinho melhor?”.
- **Primeira fronteira isolada:** o detector de resultados narrados em
  `cognicao/guardiao_alegacoes.py` trata o trecho subordinado “tá rodando” como
  afirmação independente. O pedido de informação não comprova um estado,
  mas também não deve ser interpretado como observação própria da Laylay.
- **Controles reproduzidos:** “me diga qual app está rodando” passa;
  “o app está rodando” continua corretamente bloqueado sem evidência.
  A formulação longa acima falha também chamando o detector diretamente,
  sem LLM, comandos propostos ou transporte. Não remover o guardião de estados.
- **Próximo passo:** RED contrastivo de escopo do pedido de informação; incluir
  orações coordenadas, afirmação posterior e efeitos realmente inventados.
  Reutilizar o contrato canônico de incerteza/pedido de informação.
- **Fechar quando:** perguntas e pedidos subordinados legítimos sobreviverem
  sem liberar alegações independentes; regressivos e runtime sem esse fallback.
- **Evidência:** [sonda e diagnóstico de 15/09](RELATORIO_COLETA_DEBUG_20260914.md#capacidades-relevantes-no-transporte--15092026).
- **Escopo:** registrado, não corrigido junto com C07. A qualidade da instrução
  sobre a capacidade continua em P01 e não será resolvida só liberando essa fala.
- **Atualização posterior — C08, 15/09:** corrigido o reconhecedor compartilhado
  para pedidos nominais (“me diga o app que…”), preservando nomes coordenados.
  O guardião delimita cada ocorrência pelo conjunto de estados/resultados já
  analisados; outra alegação não herda a permissão linguística do pedido anterior.
- **Validação:** 44 contrastes novos; seleção ampliada **918 passed**. A fala
  histórica completa passou pela preparação e verificação final sem reparo,
  tanto sem comandos como com a proposta de pausa original, que é descartada.
- **Prova da composição real:** replay explícito da resposta HTTP histórica
  no processo da Laylay entregou a fala integral sem reparo/fallback nem comando
  executado. O turno de replay **não é nova geração do Qwen**. A sonda separada
  com geração real passou 18/18, mas não repetiu a subordinada histórica.
- **Limites:** não é análise irrestrita de português nem liberação geral de
  orações coordenadas; ambiguidades continuam conservadoras. Preservar uma fala
  não certifica que sua orientação ou tom sejam bons (P01).
- **Detalhes:** [correção e validações de P11](RELATORIO_COLETA_DEBUG_20260914.md#pedido-de-informação-não-é-alegação-de-estado--p11--15092026).

### P12 — Perguntas de procedimento sem natureza reconhecida

- **Descoberto em:** testes contrastivos de C09, 15/09.
- **Reproduzido:** “como eu poderia aumentar o volume?” é `pergunta`, sem
  autorização, mas `natureza_acao=nenhuma`. “Me ensina como aumentar o volume”
  é conversa genérica. O catálogo recupera sistema, mas o contrato não tem uma
  interpretação procedural canônica para selecionar a tarefa específica.
- **Primeira fronteira:** classificação, antes da geração; nenhuma alteração
  em `modalidade_turno.py` foi feita nesta rodada.
- **Próximo passo:** estudar a moldura de explicação na classificação canônica,
  com pedidos reais, perguntas de estado, hipóteses e textos citados como controles.
  Não adicionar um parser privado de volume no preparador de prompt.
- **RED preservado:** `test_explicacao_capacidades_sem_execucao.py`, duas rotas.

- **Atualização C11, 16/09:** a moldura de procedimento seguida de infinitivo
  agora é reconhecida na proteção operacional compartilhada antes das listas
  de ações. Não adiciona verbos à autorização nem atesta capacidades. Hipóteses,
  negações e transformações conservam precedência. É uma gramática limitada,
  não um analisador irrestrito de português.
- **Prova:** 36 REDs novos na primeira fronteira → GREEN; 15 controles negativos
  e de comandos mantidos. Volume passou nas duas rotas de documentação. Seleção
  ampliada: **2.556 aprovados, duas falhas P13, 14 xfails preexistentes e 30
  subtests aprovados**. Não foi a suíte global.
- **Runtime:** turno 11 de `roteiro_explicacao_capacidades-20260916-085853-170785`
  reconheceu o procedimento e enviou documentação de sistema no HTTP real.
  A fala final ainda virou contingência após reparo rejeitado; P16 registra essa
  fronteira posterior. Corrigir a classificação não encerrou P01.

### P13 — Recuperação do catálogo perde domínio quando só há nome de app

- **Descoberto em:** testes contrastivos de C09, 15/09.
- **Reproduzido:** “como eu poderia abrir a calculadora?” já é instrução/explicação
  sem autorização, mas o seletor por termos não recupera sistema: “calculadora”
  não é “app/programa/janela” e a pergunta não contém comandos executáveis.
  “Como eu faria para abrir um programa?” serve de controle e passa.
- **Primeira fronteira:** recuperação do catálogo, não capacidade do executor.
- **Próximo passo:** reutilizar resolução de entidades/capacidades para consulta
  documental sem autorização; não cadastrar uma exceção para cada aplicativo.
- **RED preservado:** `test_explicacao_capacidades_sem_execucao.py`, duas rotas.

- **Atualização C12, 16/09:** o mapa consulta os aliases do `APPS_MAP` real por
  callback tardio, sem copiar a lista nem chamar executores. Referências completas
  selecionam sistema; não provam instalação, abertura ou disponibilidade.
  Ausência/falha da fonte mantém a recuperação anterior por termos.
- **Validação:** quatro REDs causais com a declaração/factory extraídas de
  `laylay.py` → GREEN; nove testes novos no total. As duas rotas de explicação
  usam essa composição, não um mapa isolado sem a dependência de aliases.
  Seleção ampliada: **2.567 aprovados, 14 xfails preexistentes e 30 subtests**.
- **Runtime:** captura `transporte_evidencia-20260916-093745-215501`, turno 4 de
  `roteiro_explicacao_capacidades-20260916-093746-337804`: documentação de sistema
  entregue no HTTP ao Qwen, que explicou como pedir a abertura. O verificador
  pesquisou “Calculadora” como título e substituiu a fala. Recuperação GREEN,
  fala final RED em P10; P01 continua parcial.
- **Limites:** recuperação lexical de aliases, não desambiguação universal nem
  descoberta de apps instalados. Disponibilidade e autorização não mudaram.

### P14 — Explicação prioritária IoT substitui ação e alvo

- **Descoberto em:** sonda real de explicações, 15/09, turnos 6 e 7.
- **Reproduzido:** perguntar como ligar a lâmpada ou desligar o ventilador recebe
  “É só me pedir diretamente para desligar a luz”. Nenhum comando foi executado.
- **Provado por código:** `ComandosImediatosRuntime` detecta a pergunta IoT e usa
  essa frase fixa antes da LLM. Não é uma invenção do Qwen nessa rota.
- **Próximo passo:** preservar o veto operacional e devolver a autoria da
  explicação ao contrato compartilhado, testando ligação/desligamento, alvos
  diferentes, indisponibilidade, recusa, hipótese e pedidos reais.
- **Não corrigido nesta rodada:** não remover a barreira IoT para silenciar o erro.
  O roteiro novo verifica também a inversão de ação/alvo, não só falta de comandos.
- **Atualização C13, 16/09 à noite:** mantida a mesma condição de veto, mas a
  porta prioritária retorna `False` para delegar a autoria à conversa. Não fala
  por cima do turno, não o marca como respondido e não alcança detectores ou
  executores subsequentes. Perguntas recebem documentação pelo caminho comum;
  recusas e hipóteses seguem com seu ato original, sem frase fixa sobre a luz.
- **RED/GREEN:** oito casos causais reproduzidos antes do patch; quatro controles
  de documentação/autoria já passavam. Depois, 12 aprovados, incluindo proposta
  operacional válida no JSON rejeitada pela autoridade do turno. O teste antigo
  que exigia a resposta fixa foi atualizado para o contrato de delegação; seu
  requisito de não alcançar o roteador foi preservado.
- **Runtime:** `roteiro_explicacao_capacidades-20260916-190855-889031` entregou
  explicações corretas de ligar a lâmpada/desligar o ventilador. Sonda adicional
  `roteiro_iot_explicacoes-20260916-191051-714954`: oito respostas, ações inversas,
  tomada, brilho, recusa e hipótese, zero comandos. Recusa: “Certo, não vou
  desligar o ventilador.” IoT simulado; não houve ensaio físico de dispositivos.
- **Limite restante em P01:** a LLM ainda pode explicar mal a confirmação,
  por exemplo “após o dispositivo ser refeito na configuração”, ou oferecer
  configuração sem uma capacidade comprovada. Não é o retorno da frase fixa;
  o placar automático da sonda não certifica esse conteúdo. Não alterados os
  guardiões, prompts, rede nem executores nesta correção.

### P15 — Falha técnica pede reformulação de uma pergunta clara

- **Descoberto em:** sonda `roteiro_explicacao_capacidades-20260916-084208-340029`.
- **Observado:** timeouts de leitura nas duas primeiras chamadas (9 e 19 segundos)
  terminaram em contingências como “Faltou uma peça” e “Peguei o começo”, embora
  as perguntas de pausa fossem claras. Houve também timeout de preparação inicial.
- **Contrato necessário:** indisponibilidade técnica não é ambiguidade da entrada;
  a conclusão deve preservar a causa conhecida, sem atribuir o problema ao usuário.
- **Ainda aberto:** causa da latência e primeira perda da categoria de falha entre
  transporte e autoria da contingência. Carga ou inicialização são hipóteses, não
  causas comprovadas. A sonda posterior sem timeout não encerra esse defeito.
- **Próximo passo:** rastrear o motivo do erro até o fallback e criar contrastes de
  timeout, indisponibilidade e ambiguidade real. Nenhum prazo alterado nesta rodada.

### P16 — Reparo transforma pergunta de procedimento em relato passado

- **Descoberto em:** validação real de C11, turno 11 da sonda de 16/09 às 08:58.
- **Comprovado:** a entrada “como eu poderia aumentar o volume?” e o contrato
  `explicacao_capacidades` chegaram corretamente. A geração ensinou “ajusta o
  volume”, mas acrescentou uma condição sobre PC remoto. Após rejeição por
  `resultado_operacional_sem_evidencia`, o prompt de reparo afirmou “O usuário
  relatou um pedido” e permitiu perguntar “como foi”. O modelo terminou com
  “Como foi, dessa vez?”, foi rejeitado e houve contingência pedindo mais detalhes.
- **Dono localizado:** `qualidade_comunicacao.py`, seleção pelo indicador
  `resultado_operacional_desconhecido`. Esse indicador não prova o ato de relato.
- **Contrato necessário:** reparo deve preservar o ato e o objetivo do turno;
  desconhecer resultado não transforma pergunta em relato. O catálogo também
  não prova que uma rota remota é requisito para uma operação local.
- **Ainda aberto:** escopo exato da primeira rejeição e separação entre condição
  indevida gerada, falso positivo linguístico e reconstrução inadequada no reparo.
  Não remover o guardião para aceitar a fala. Nenhum patch dessa raiz nesta rodada.
- **Limite do avaliador:** marcou esse turno como aprovado e contou zero fallbacks,
  embora o terminal registre reparo rejeitado e contingência. Auditoria manual
  prevalece sobre esse placar mínimo; não usar 10/12 como qualidade aprovada.
- **C15, 19/09:** reproduzidos nove REDs locais antes do candidato, com um
  controle verde de relato explícito. Classificação e catálogo corretos antes
  do reparo falsificaram erro anterior como explicação dessa divergência. Além
  da premissa indevida no prompt, `_resumo_reparo` descartava a documentação.
  Agora o reparador mantém o objetivo/atos do contrato e recebe a documentação
  já selecionada quando a estratégia é `explicacao_capacidades`. Não resolve
  entidades novamente, não concede execução e não modifica o guardião.
- **Validação:** dez testes novos; 159 na seleção focada e 2.811 na ampliada,
  com 14 xfails preexistentes e 30 subtestes aprovados. Runtime completo:
  `roteiro_explicacao_capacidades-20260919-181949-614989`, captura
  `transporte_evidencia-20260919-181948-526867`. Replay somente do rascunho
  histórico de volume; reparo novo pelo `qwen3:4b-instruct` ensinou o pedido,
  sem “como foi” ou contingência. A frase adicional sobre remoto ainda foi
  removida pelo verificador: P01 permanece aberto. Houve também reparo novo
  de pergunta sobre aba, preservando o objetivo. Doze respostas, zero comandos;
  12/12 no avaliador mínimo não certifica a qualidade geral das explicações.

## Correções com validação registrada

“Validado no escopo” não significa ausência de outros defeitos naquela habilidade.
Datas e contagens abaixo descrevem cada rodada registrada, não uma suíte global.

| ID | Correção | Validação registrada | Limite restante |
| --- | --- | --- | --- |
| C01 | Recusas de alterar/mudar/ajustar reconhecidas pela base verbal canônica | 14/09: 41 testes focados; sonda de 18 turnos sem comandos | Não certifica toda interpretação de linguagem |
| C02 | Respostas locais publicadas entram no histórico do chat, com idempotência e compatibilidade com o emissor legado | 15/09: 17 testes novos, seleção de 103 aprovados e sonda final 18/18 | P07; conversa livre e demais writers não foram auditados integralmente |
| C03 | Realização de recusas e reconhecimento de perguntas não feitas sem falsos reparos em casos subordinados | 14/09: testes contrastivos e sondas reais sem contingência na rodada final | Não elimina toda invenção de estados |
| C04 | Orçamento do JSON estruturado separado do limite de fala curta; preservação do pacote fechado | 14/09: testes de geração/composição e sondas reais | Não garante universalmente JSON válido nem resolve qualidade sozinho |
| C05 | Sanitização de eventos/URLs Chrome antes da impressão, preservando dados dos handlers | 14/09: 27 testes com vizinhos e 2 subtests | P08; outros loggers não foram auditados globalmente |
| C06 | Reparo parcial preserva a resposta temática; verificador não apaga frases apenas por tamanho | 13/09: quatro turnos reais preservaram acolhimento e explicação | Preservar conteúdo não certifica sua correção factual; ver P02 |
| C07 | Catálogo vivo relevante acompanha a instrução do turno, sobrevivendo à compactação e retry | 15/09: 17 REDs → GREEN; seleção ampliada 451 passed; presença confirmada no HTTP real | P01 ainda parcial; P11 posteriormente tratado em C08; 18/18 sem execução não certificam qualidade da fala |
| C08 | Pedido nominal de informação não vira estado observado; escopo não vaza para outra alegação | 15/09: 44 contrastes; seleção ampliada 918 passed; replay histórico na composição real sem fallback | Sonda com Qwen real não repetiu a subordinada; tom e utilidade da explicação continuam em P01 |
| C09 | Autoria de explicações recebe documentação viva e tarefa textual, não planejamento genérico | Seleção conjunta: 1.307 aprovados / quatro REDs P12–P13; runtime: dez aprovações mínimas / duas falhas IoT | P01 não encerrado; cobertura, disponibilidade parcial e qualidade |
| C10 | Exemplo didático não é título pesquisável; fatos ao redor continuam exigindo evidência | 27 contrastes próprios; 42 aprovados com metalinguagem; exemplos preservados no chat real | P10 histórico mais amplo continua aberto |
| C11 | Moldura de procedimento reconhecida independentemente do vocabulário executável | 51 contrastes; seleção ampliada 2.556 aprovados / duas falhas P13; documentação de volume no HTTP real | Gramática limitada; P16 impede considerar a fala final corrigida |
| C12 | Catálogo documental consulta aliases dos aplicativos da composição | Nove testes novos; seleção ampliada 2.567 aprovados; documentação da calculadora no HTTP real | P10 corta a explicação gerada; referência não é instalação/estado |
| C13 | Veto IoT delega autoria sem substituir ação/alvo nem consumir o turno | 12 testes novos; 2.780 aprovados na seleção ampliada; duas sondas reais sem comandos, incluindo oito contrastes IoT | Não certifica hardware nem toda qualidade das explicações; P01 aberto |
| C14 | Papel da citação separa recurso, exemplo e obra; preserva contexto entre frases | 48 testes de citações; 2.801 aprovados na seleção ampliada; replay histórico no runtime e geração nova | Não prova existência/estado de recursos nem resolve toda citação ou P16 |
| C15 | Reparo preserva objetivo do turno e fonte da explicação | 10 testes novos; 2.811 aprovados na seleção ampliada; reparos novos de volume e aba no runtime | Requisitos indevidos sobre remoto ainda gerados; guardião permanece necessário |

Fontes: [rodadas de 14–15/09](RELATORIO_COLETA_DEBUG_20260914.md) e
[reparo parcial de 13/09](RELATORIO_CORRECOES_CONVERSA_20260912.md).

Na última seleção ampliada de C02: **605 passaram, 3 falharam e 8 subtests
passaram**. As falhas estão individualizadas em P03–P05; não foram escondidas
por uma declaração de suíte global verde.

## Ideias futuras — fora da fila de bugs

### I01 — Pesquisa em cinco sites/camadas

- Proposta do Pedro: extrair de cinco sites os pontos importantes para o pedido.
- **Somente guardada; não implementada nem ativada.** Não confundir com autorização
  para reconstruir a pesquisa durante uma correção de conversa.
- Registro original: [IDEIA_PESQUISA_CINCO_CAMADAS.md](IDEIA_PESQUISA_CINCO_CAMADAS.md).

## Modelo para o próximo achado

### PXX — Título curto

- **Descoberto em / durante:** data e correção que estava em andamento.
- **Estado e impacto:** suspeita, reprodução, parcial etc.; consequência para Pedro.
- **Observado versus esperado:** exemplo mínimo, sem dados sensíveis.
- **Primeira fronteira / dono:** se conhecidos; não preencher com hipótese como fato.
- **Evidência e hipóteses falsificadas:** teste, artefato ou relatório; nível de prova.
- **Próximo passo:** menor investigação ou correção que falta.
- **Fechar quando:** contrato e validação necessários, incluindo runtime quando aplicável.
- **Atualizações:** data, alteração, resultado e limites; preservar o histórico.

## Atualizações do índice

- **15/09/2026:** criado por solicitação do Pedro; reunidos dez itens pendentes,
  seis correções com escopo validado e uma ideia futura. Somente documentação;
  nenhuma mudança de produção, treino, ativação neural, teste de runtime ou commit.
- **15/09/2026, continuação:** investigado P01; registrada C07 com prova do
  transporte. P11 separado após aparecer na sonda. Não houve treino/promoção
  neural nem mudança de autorização, executores ou guardiões nesta etapa.
- **15/09/2026, P11:** C08 altera somente a distinção/escopo linguístico nos
  validadores compartilhados. Rede, autorização, executores e personalidade
  preservados. A próxima frente permanece P01, agora sem o falso reparo histórico.
- **16/09/2026:** C09/C10 aplicados e validados com os limites acima. P12–P15
  separados; quatro REDs preservados, sem xfail. Rede e executores não alterados,
  nenhum treino, promoção ou commit criado. Próxima fronteira: P12, depois P13/P14.
- **16/09/2026, C11:** classificação P12 validada no escopo; produção alterada
  somente em `modalidade_turno.py`, preservando os patches anteriores. P16
  registrado sem desviar para outra correção. P13/P14 continuam pendentes;
  rede, catálogo, prompt, guardião, reparador e executores não alterados nesta etapa.
- **16/09/2026, C12:** alterados somente o mapa e sua injeção em `laylay.py`.
  P13 validado na recuperação; P10 reapareceu com nome de programa citado e
  exemplo em frase separada. Próxima frente planejada: P14; P10/P16 abertos.
- **16/09/2026, C13:** somente `comandos_imediatos.py` alterado em produção,
  preservando patches anteriores. P14 validado no escopo com geração real;
  nenhuma ação física, promoção neural ou commit. P01/P10/P16 continuam abertos.
- **19/09/2026, C14:** somente `fundamentacao_factual.py` alterado em produção;
  preservadas alterações anteriores. Citação histórica da calculadora validada.
  Próxima frente: P16, reparo preservando o ato e o objetivo da pergunta.
- **19/09/2026, C15:** produção alterada somente em `qualidade_comunicacao.py`
  e `validacao_contrato_fala.py`. Classificador, catálogo, guardiões, executores
  e rede preservados. Nenhum commit, treino ou promoção. Próxima fronteira:
  limites por capacidade/rota em P01; não ampliar automaticamente a correção.
