# CORPO-SENSORES-PROTECAO-01 — presença e linguagem corporal

Baseline: main d850b8c90cc5ce40bd4832e759ed991ba88cd5cc, worktree extensa e
suja preservada. Sem commit. Baseline local dos dois headers em baseline/.

## Cadeia / owner

Medições→risco local→concessão vigente→reflexo finito→GUARD/HAZARD→owner USB→
mente/DEV. Expressão não concede tração; HAZARD interrompe o pedido original,
não o transforma em sucesso. Companhia decide a concessão; firmware decide
corte/recuo/busca, sem parser verbal ou LLM duplicado.

## Evidência e limites causais

- Usuário confirmou companhia ativa e superfície inferior durante a queixa.
  Isto não prova a vigia confirmada na placa ou a qualidade da amostra histórica.
- Controle host com firmware real comprovou quatro giros com superfície segura
  e concessão renovada: falsifica ausência da rotina de busca no executor.
- RED canônico parede: depois de quatro tentativas, não havia outra rodada em
  12s, apesar de sessão/concessão/dados vigentes. Primeira fronteira incorreta:
  término BLOQUEADA era irreversível até desaparecer o obstáculo.
- RED canônico medo: mesma concessão e risco inferior persistente não produziam
  passinhos após o primeiro recuo. Novo contrato explícito, finito por episódio.
- Leitura física anterior mostrou ambos inválidos, sessão SEMSESS naquele
  instante. Não é prova do motivo do teste histórico do usuário.
- Continua aberta a causa de não observar o PRIMEIRO giro no teste relatado.
  DEV agora distingue vigia confirmada da preferência de companhia.
- Investigação posterior reproduziu outra fronteira da mesma trava: após borda
  bloqueada, inferior seguro e parede presente não admitiam busca. `contarSegura`
  exigia também frente livre para resolver a trava da borda; assim não havia
  transição entre riscos. RED transicao falhou na ausência de giro/novo episódio.
  Candidato delimita a trava ao episódio: três amostras inferiores novas<=120mm
  admitem episódio de parede, com concessão vigente, sem liberar avanço. Duas
  amostras não bastam; STOP/TTL continuam vetando. Isso é prova de código e host,
  não identificação retroativa incontestável do ocorrido na montagem do usuário.

## Candidato

Proteção local: até4 giros/rodada,4s descanso e reavaliação com SENTRY vigente;
recuo de borda250ms+até3x120ms com320ms de pausa, sem giro/avanço no perigo;
bips com quatro contornos e variação leve, sem aumento de corrente. Limite de
rodada3s, STOP/TTL/falha/frescor preservados. Mesmo mapa físico e limiares.
Integração: fases no parser canônico, companhia cede durante reflexo/descanso;
mente mantém percepção factual; DEV mostra autorização confirmada da placa;
catálogo explica limites. Pavor, sono, voz, música e receipts paralelos preservados.

## Validação

REDs executados antes do patch e falharam nas asserções de segunda rodada e
quatro recuos. Depois: parede/medo/vetos/sons GREEN em firmware real compilado
contra hardware simulado. Vizinhos de sensores/sono/som/olhos/motor GREEN.
125 testes Python focados/regressivos GREEN; novos contratos parser/DEV
adicionais GREEN (27 no conjunto proteção+DEV). Hardware e artefatos de
composição são registrados separadamente após gravação.

Regressão expandida desta rodada:206passed/1failed. Falha conhecida do conjunto
amplo anterior, `test_composicao_instalada_ativa_por_fala_aprende_receipt_e_conhece_modo`,
com KeyError intent no receipt. Não enfraquecida nem atribuída a nova causa.
DEV renderizado/inspecionado em dev.png: dados só em Corpo, campo de vigia visível.

Firmware compilado no core3.3.12 e gravado COM4, hash verificado;429692 bytes,
19300 bytes globais. Primeira prova física em composicao_armada.json:19 amostras,
vigia confirmada, inferior/frontal inválidos, fases ESPERA_MEDROSA/RECUO_MEDROSO/
BLOQUEADA com PAVOR alcançando mente/DEV. Nenhuma ordem MOTOR do PC; reflexos
locais receberam concessão do owner real. Revogação/STOP/GOODNIGHT e porta fechada.
Sem confirmação humana, fases do executor não provam movimento/audição.

Segunda prova física, usuário acompanhando e montagem suspensa: consulta inicial
frente95mm/inferior96mm. Firmware final gravado com hash verificado, root real
com concessão salva e sem ordens MOTOR do PC. composicao_parede.json registra
19 amostras: frente85–94mm, inferior79–92mm; duas rodadas com BUSCANDO/CONFERINDO
até tentativa4, ESPERA_BUSCA entre elas. Vigia confirmada em todas as amostras.
Fechamento revoga concessão, STOP e GOODNIGHT; nenhum processo Laylay/terminal
restante. Confirmação visual/auditiva humana solicitada separadamente.

Pedro confirmou após esta rodada: "Sim, vi a busca e os bips combinaram".
Confirmação humana cobre recuo, giros de procura, descanso/nova tentativa e
combinação dos bips no teste suspenso. Não comprova navegação/antiqueda em mesa.

Sons: RED adicional mostrou contorno de procura inalcançável pelo intervalo1,5s
quando disparado apenas no começo da busca. Solicitação também nas tentativas
seguintes, sem reduzir intervalo, tornou a assinatura alcançável (GREEN somBusca).

15 REDs da regressão ampla anterior continuam separados no relatório pai.
Não se declara integração global encerrada. Giro é tempo/PWM, não ângulo
medido; recuo não possui cobertura traseira e o sensor ainda está na protoboard.
