# Comunicação contínua — contratos corrigidos e limites

Base: main, HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, worktree já
modificada. Investigação autorizada por Pedro em “podemos resolver esses” e
“continue”. Nenhum commit, reset, reinício da sessão pessoal ou shutdown.
Backups, estado inicial e hashes em
`resultados_testes/comunicacao_identidade_fala_20261023/baseline.json` e nas
pastas individuais abaixo. Mudanças anteriores e paralelas foram preservadas.

## Contratos e responsáveis

As linhas são mecanismos causais, não fases de uma correção única. Permanecem
vinculados às famílias históricas F1/F3/C5/C7 sem encerrar essas famílias por
contagem de testes ou fundir causas apenas pela semelhança das falas.

| Fronteira demonstrada | Contrato / responsável canônico | Evidência e critério |
| --- | --- | --- |
| Preview substituía identidade da fala entregue | `registro_semantico`, `orquestrador_fala_runtime`, `seletor_contexto`, `contrato_fala`, `validacao_contrato_fala`, `qualidade_comunicacao`: referência integral ligada à ocorrência, consulta e turno; ordem de emissão antecede callbacks | RED inicial3/owners4; revisão5. Fonte longa e cópia rejeitada na instalação; Qwen2 turnos/3 HTTP200, zero drift/executores. Entrega atrasada não substitui fala mais nova; fila aceita não é entrega. |
| Complemento deítico eliminava finalidade de esclarecimento | `referencias_linguagem` fornece leitura integral; `proporcao_resposta` e `continuidade_conversa_natural` consomem | RED5/controles8. “O que você quis dizer com isso?” conserva esclarecimento sem criar autorização. Qwen instalado2 turnos/3 HTTP200; qualidade universal da paráfrase não certificada. |
| Pergunta/citação com “quis dizer” virava correção do usuário antes da autoria | `reparacao_conversacional` consome retificação assertiva do leitor compartilhado, fora de citações | RED4/controles4; revisão preservou RED7 e RED4 de corretores legítimos/prefixos de voz. Pergunta não muda alvo; correção legítima continua disponível. |
| Compactação normal importava políticas da rota rápida | `prompt_voz_unica` / `preparacao_llm`: representar de forma compacta conserva extensão e possibilidade de proposta operacional do contrato normal | RED15 de extensão e RED3 de comandos incondicionalmente vazios. Rápida continua curta/sem comandos; normal respeita turno e receipt. Não aumentar tokens, timeout ou janela para esse defeito. |
| Pedido de ensino no imperativo recebia perfil curto | `proporcao_resposta`: reconhecer a finalidade de explicar/ensinar antes de dimensionar | RED3/controle1; explicações chegam com orçamento apropriado. Isso não prova correção factual da explicação. |
| Consulta natural musical era vetada antes da leitura canônica | `modalidade_turno` conserva leitura reconhecida pelo owner geral; `comandos_imediatos` admite somente candidatos do catálogo somente leitura antes das portas mutantes | RED instalado1 e RED canônico3. Revisão reproduziu2 bypasses de curadoria e4 em e-mail/notificação/web/app. Corrigida admissão comum, retirado remendo por porta. Playlist temporária com2 faixas é lida pelo executor real, sem IA; opinião não consulta nem toca. |
| Interpretação atual era adiada como tarefa secundária | `interpretacao_intencao`: prioridade interativa apenas para texto integral do plano ligado ao mesmo ID, tipo `interpretacao` no orçamento existente; cache ligado ao turno | RED3 domínios/controles2, depois RED1 de texto longo. Interpretação e principal compartilham limite; sem vínculo não recebe prioridade. Qwen real passa a receber a interpretação, sem confundi-la com efeito. |
| F3 residual: recusa de capacidade sem schema perdia a causa no retry | `llm_http`: conservar a resposta de capacidade antes de retry/circuito e também no retorno do retry genérico | RED1 inicial e RED1 de retry. Composição distingue interpretação e autoria, cada uma sem retry permissivo; publicação única conserva causa, sem efeito. Complementa F3 anterior, não é nova causa de TTS. |
| Alvos explicitamente categorizados eram descartados, fundidos ou selecionados arbitrariamente | `retrato_turno` publica coleção; `registro_semantico` mantém identidade tipo+nome, grupo de menções, TTL e ordenação sem perder informação por saturação | RED10; revisão RED3 de rótulos dentro do nome, RED2 de tipos homônimos e RED8 de títulos/ciclo. Títulos citados são atômicos pelo leitor central `intervalos_citados`; escolha explícita renova grupo nas duas projeções. Biblioteca, filme e música cobertos; nenhuma menção vira receipt. |
| Proposta podia substituir reprodução por status do player | `gramatica_musical` lê objeto contextual/finalidade; `retrato_turno` congela operação e intents compatíveis; detector consome o mesmo estado; árbitro existente rejeita operação divergente | RED4/controles5. RED instalado demonstrou mapeamento de álbum como domínio desconhecido: `contexto_imediato` conserva álbum→música. Fonte sem ID/ID divergente/outra fala não materializa alvo. Sem parser privado no executor. |
| Nome explícito fazia formato de álbum virar faixa no refinamento | `refinamento_pesquisa` preserva nome+formato; `busca_youtube` exige compatibilidade de alvo/formato/variação antes da pontuação | RED5/controle1 e revisão RED5/controle1. Álbum diferente, cover/mix/instrumental/karaoke não pedidos recusados; cover pedido permitido. Metadados compatíveis não provam conteúdo integral ou reprodução. |

## Validação final e limites

Conjunto relevante atual: **924 aprovados, 30 subtests aprovados, 1 desmarcado**,
em `resultados_testes/comunicacao_operacao_referente_20261023/validacao_entrega.xml`.
O desmarcado importa `laylay` diretamente e encontra a instância pessoal já
aberta; o MESMO teste passou separadamente com instalação isolada em
`comunicacao_operacao_referente_20261023/import_final.xml`. Não foi removido nem teve
asserções relaxadas. Revisão independente final64 aprovados, incluindo
composições instaladas adversariais e integração com abertura recusada.

A regressão ampla anterior não é declarada verde: P19 tem44 erros de setup,
reproduzidos com os seis owners anteriores (timeout da fixture, antes das
asserções). Dois testes de segmentação musical com negação também falham com
`modalidade_turno.py.antes`; contraprova em `segmentacao_baseline.xml`. Essas
pendências não foram apagadas, compensadas pelo composto ou contadas como
regressões resolvidas. Não executar chaos amplo como substituto do diagnóstico.

Prova final de conversa instalada com Qwen local, seis turnos e5 HTTP200,
fontes estáveis em `comunicacao_operacao_referente_20261023/qwen_instalada_final`:

- Álbum Nevermind mencionado → pedido contextual → `MUSIC_SEARCH`, query
  `Nevermind`, formato `album`, sem chamada de interpretação nesse pedido.
- Dois álbuns concorrentes → pedido pronominal → nenhum executor.
- Escolha explícita de In Utero → novo pedido → `MUSIC_SEARCH`, query
  `In Utero`, formato `album`, sem chamada de interpretação nesse pedido.
- Todas as folhas de efeito externo recusadas pela sonda. Os registros de
  solicitação não são receipt de reprodução. Não afirmar música tocando,
  conteúdo integral de álbum ou audição humana.

Integração do executor real com refinador/seletor reais e HTML controlado:
sem álbum compatível, zero aberturas; com álbum compatível, uma solicitação de
abertura recusada, resultado negativo preservado. Evidência de contrato e
seleção por metadados, não validação do provedor ao vivo ou do áudio.

Esse caminho também passou em **duas composições instaladas completas**:
fonte do usuário → turno/detector/prioridade → executor/refinador → busca e
seletor reais → recusa na folha de abertura → receipt negativo e publicação.
HTTP de metadados, abertura, autoria e TTS foram controlados na prova. Nenhuma
geração antecede seleção ou execução; a chamada posterior de
`autoria_operacional` recebe o receipt negativo já publicado e é recusada de
forma controlada. A contingência comunica falha, sem inventar sucesso.
Álbum errado e cover são rejeitados; sem candidato, não há abertura. Artefato
`comunicacao_formato_musical_20261023/instalada.xml`.
Uma asserção final exigia incorretamente ausência de qualquer chamada de modelo,
incluindo essa autoria posterior. RED preservado em
`comunicacao_formato_musical_20261023/red_assercao_etapa_autoria.xml`; a correção
foi no teste e nesta descrição, sem alteração de produção. O teste agora verifica
tipo da chamada, ordem e receipt vigente também no instante da autoria.
O último filtro do seletor foi refinado depois da coleta Qwen acima; essa
alteração é coberta pela composição instalada e regressões atuais, sem afirmar
que a coleta antiga executou o seletor final ou provou o provedor ao vivo.

## Premissa corrigida e próxima fronteira

**Errata do diagnóstico anterior de saída incompleta:** o codec autoral manda
omitir `fala` no transporte e a reconstrói de `suporte_proposicoes[].texto`.
Portanto ausência desse campo na resposta bruta, sozinha, não é defeito do
Qwen. Os relatórios anteriores foram preservados; essa interpretação não deve
fundamentar mudança no codec validado.

**Autoria factual livre continua aberta.** A declaração estrutural de suporte
tem `semantica_verificada=False` e não prova verdade. O Qwen ainda produz
explicações erradas, exageros e negativas indevidas de capacidade em algumas
respostas livres. Seis ablações HTTP200 em
`resultados_testes/estudo_autoria_livre_20261023/ablacoes.json` falsificaram a
hipótese de que remover histórico ou reduzir o prompt bastaria: também houve
erro com instrução mínima e o mesmo schema. A pergunta principal já era texto
literal, não JSON encapsulado; essa hipótese também caiu.

Próximo estudo: primeira fronteira entre obrigação de fonte, seleção das
fontes permitidas e revisão de proposições livres. Não substituir evidência
por uma segunda opinião do mesmo modelo, proibir toda conversa, adicionar
exceção para gramática/Nirvana ou declarar compreensão global concluída.
Perguntas sobre o conteúdo da conversa ainda podem receber contingência
excessiva; respostas ambíguas podem explicar ausência de execução sem formular
o esclarecimento ideal. São limites semânticos separados dos contratos acima.

## Entrega e preservação

Arquivos já modificados no workspace; não exige edição manual. Escopo final
de produção e hashes anteriores/atuais constam no selo conjunto
`resultados_testes/comunicacao_identidade_fala_20261023/verificacao_entrega.json`.
UI/Terminal, hardware, configuração do modelo e voz não foram alterados nesta
continuação. Main não foi editado por estes candidatos. Não foi criado commit.
Reabrir a Laylay depois de revisar/carregar as mudanças: processo já aberto
não incorpora automaticamente módulos Python alterados no disco.
