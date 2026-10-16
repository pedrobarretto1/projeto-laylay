# CORPO-DECISAO-V1 — equilíbrio contextual inspirado no V7.3

13/10/2026. Pedido autorizado: trazer a disputa entre observar, descansar e
explorar, persistência e moderação por atividade recente para a mente da Laylay.
Baseline main d850b8c90cc5ce40bd4832e759ed991ba88cd5cc; worktree paralela
preservada. Três owners congelados e status inicial em baseline/. Sem commit.

## Contrato e diagnóstico

O incremento anterior dava repouso45–90s, mas ao terminar o prazo voltava a
explorar sem comparar alternativas. O V7.3 pontua objetivos, conserva momentos
e usa repetição/tempo de motores para favorecer ações sem locomoção. Não é
necessário transplantar DNA, fadiga simulada, território virtual ou um cérebro
no firmware: a decisão já pertence à cognicao/decisao_corporal.py.

RED: sem a projeção de ritmo, a cena após movimento recente volta a comandar
motor. Faltavam a escolha concorrente e sua persistência no owner. A intenção
descansar, os executores e o histórico compartilhado já existiam e foram reusados.

## Implementação

- ExperienciaCorporalRuntime registra duração comandada com ACK PWM a partir
  dos receipts. Resume os12 registros recentes do owner, na mesma sessão/perfil,
  descartando recuperação, origem inválida, data futura/expirada e duplicata.
  Contabiliza comando parcialmente confirmado sem promover gesto a sucesso.
  Compatibilidade com coreografias antigas inteiramente confirmadas usa partitura.
- Decisor puro compara atenta(observar), descansar e explorar. Repetição de
  exploração e atividade recente favorecem sossego; tempo sem gesto e alegria
  causal aumentam oportunidade de explorar. A primeira iniciativa curta continua
  possível após a acomodação inicial já aprovada.
- Escolhas quietas persistem30–60s para observação e45–90s para descanso, segundo
  a cena recente. O owner guarda esse prazo na intenção efêmera existente, sem
  ampliar concessão ou prazo de proposta. Turno/sessão/contexto novos invalidam
  o aproveitamento do momento anterior. Conversa e tarefa PC continuam prioritárias.
-20s de duração comandada confirmada na amostra da última janela60s favorecem
  repouso, inclusive para propostas/reação automática. Isso é política de ritmo,
  não temperatura, fadiga, distância ou medição exata de duty. Pedido manual usa
  o executor canônico e seus limites existentes.
- Pontuações e motivo acompanham a intenção no modelo corporal para a mente.
  Projeção textual mantém o orçamento3800 caracteres no caso de composição
  testado. DEV recebe nome/motivo/fase pelo canal atual e continua sob filtro CORPO.

Cadência é decisão cognitiva observável, não receipt de movimento. Na pausa
não cria plano, som, deslocamento ou efeito fictício. Olhos/heartbeats existentes
continuam ativos, e não houve alterações nas partituras/PWM, firmware ou bips.

## Validação

- red.txt:5 REDs canônicos antes do candidato.
- green_final.txt:209 testes passaram;2 casos excluídos por falhas externas já
  reproduzidas com owners congelados no incremento anterior (receipt instalado
  sem intent e perfil configurado). Não alterados para produzir verde.
- Casos protegem alternativas concorrentes, repetição, persistência/expiração,
  prioridade PC, proposta sem concessão, entrada inválida/não finita, sessão/
  perfil/restauração, janela temporal, receipt parcial, comandos manuais e modelo
  entregue à autoria pela composição real. Owners/transporte/coordenador reais;
  hardware é simulado nos testes de efeitos.
- Uma asserção adicional inicialmente usou nome incorreto de função de formatação;
  corrigida para formatar_modelo_corporal. O teste passa com o limite preservado.
- runtime_usb.json: composição instalada, FACE confirmado na COM4, resumo factual
  da nova sessão, consulta diagnóstica ao decisor e publicação no owner/mente/ponte
  autenticada. Escolheu observar, com pontuações55/44/30. Sem concessão ativada,
  proposta de LLM ou MOTOR enviado. Fechou ponte/serial com STOP e GOODNIGHT.
- git diff --check sem erros. Aplicação normal não aberta; nenhum processo da
  Laylay/Terminal2 ficou aberto ao final da conferência.

Limites: o diagnóstico USB prova leitura/entrega, não uma sessão prolongada de
passeio nem satisfação subjetiva com o ritmo. A experiência física após reabrir
continua necessária para avaliar o equilíbrio percebido. Não declara suíte global
verde nem port completo de todos os comportamentos do V7.3.

Produção deste incremento: decisao_corporal.py, companhia_corporal.py,
experiencia_corporal_runtime.py, corpo_motor_runtime.py e modelo_corporal.py.
Catálogo, interpretadores de linguagem, cooperação/autorizações, voz e firmware
mantidos. Nenhum armazenamento privado ou novo dono de decisão.
