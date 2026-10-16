# CORPO-SENSORES-PROTECAO-01 — 14/10/2026

Base: main d850b8c90cc5ce40bd4832e759ed991ba88cd5cc; worktree suja preservada,
baseline firmware e status salvos nesta pasta. Nenhum commit criado.

Pedido aprovado: manter altura perto de10cm, borda>13cm ou inválida, frontal
válido<=10cm. Borda recua e gira, confirma superfície na nova direção, então
pode avançar. Protoboard/rodas suspensas confirmadas; fechar Laylay ao final.

## Cadeia causal

Antes: VL53L0X → cache/DIST corretos → PWM independente continuava. RED
`red_corte.cpp` falhou depois de confirmar PWM de avanço, pelo motivo certo.
Novo owner local veta/interrompe todos os MOTOR, sob a sessão existente.
Medição/contexto não autorizam tração. Um pedido interrompido jamais vira
sucesso porque a manobra defensiva ocorreu.

Uma segunda fronteira apareceu no teste humano: resposta lenta. Instrumentação
real sem motores falsificou espera da LLM como requisito do corte: o corte é
local. Mediu OLED até35ms bloqueando o loop e intervalo inferior até85ms.
RED `red_oled.cpp` reproduziu o corte ausente DURANTE um frame; candidato passa
a observar entre blocos32bytes. VL53L0X orçamento20ms/I2C400kHz/timeout5ms;
sensor inferior lido primeiro, corte antes de leitura frontal. Novos dados:
`latencia_original.json`, `latencia_depois.json`, `latencia_reflexo.json`.
Na versão final, janela com reação mediu até38ms entre amostras inferiores,
seguida por29ms e24ms. Isso não mede latência borda física→roda parada.

Watchdog inferior75ms e frontal150ms; leitura inferior inválida gera borda,
erro/ausente/velha bloqueia sem recuo cego. Frontal inválida recente é
desconhecida, não confirmação de caminho livre. Giro é temporal900ms;
verificação requer3 novas amostras, sem loop infinito. STOP/TTL cortam.

## Provas

- Compilação core ESP32 3.3.12, Adafruit_VL53L0X1.2.5, flagproteção1, upload
  COM4 com hash verificado. Perfil USB, motor e áudio anteriores mantidos.
- Host: corte, limiares, status, idade, nova amostra, recuo/giro, bloqueio,
  STOP, OLED cooperativo; regressão de sono/olhos/som/motores verde.
- 110 testes focados/regressivos de transporte, sensor, DEV, catálogo,
  equilíbrio e cooperação verdes. Após compactar o retrato factual no prompt,
  mantém o limite3800 sem apagar fatos correntes no owner.
- Root real instalado no painel e `testar_automatico.py`: mesmo ownerUSB,
  corpo/mente/DEV/coordenador; consultas DIST/GUARD e receipt original
  interrompido, SACK confirmado. Sem iniciar os serviços de companhia.
- Humano: confirmou recuo, giro e parada no primeiro teste automático.
  A versão acelerada tem medição elétrica; rapidez percebida e frenagem
  física em chassi ainda não foram confirmadas.
- Painel DEV renderizado e inspecionado em dev_corpo.png; dados em CORPO,
  atualização de mm sem um log por leitura.

## Regressão ampla ainda vermelha (não encerrada)

Rodada 206passed/4failed em companhia/corpo/experiência/catalogo/continuidade:
test_composicao_instalada_ativa_por_fala_aprende_receipt_e_conhece_modo;
test_composicao_instalada_resolve_executa_publica_e_conhece_corpo;
test_receipt_instalado_alimenta_aprendizado_compartilhado_sem_criar_permissao_duravel;
test_cadeia_instalada_preserva_receipts_independentes_e_publica_falha_parcial.
Sintomas: última ação semintent/aprendizado ausente/cadeia para na1ªetapa.

Outra rodada 77passed/12failed: 10 em receipts/sons de mídia,1 no prompt
corporal,1 no TCP. Prompt era regressão deste candidato, corrigida e revalidada
no conjunto110. Os demais15 casos ficam abertos, sem atribuição definitiva de
raiz nem alteração dos contratos de conversa/música/receipt paralelos.
Não se declara regressão geral verde nem integração global encerrada.

## Limites / próxima evidência

Sensor inferior ainda na protoboard, não numa posição física capaz de antecipar
a passagem da roda pela borda. Não há encoder nem sensor traseiro/lateral.
Recuo é breve, sem confirmação de superfície atrás; não é navegação livre
antiqueda. Necessário montar sensor antes das rodas e medir velocidade/distância
de frenagem, validar superfícies e ângulo de giro antes de testar uma mesa real.
Leitura inferior observada muitas vezes inválida ou154–169mm; por isso botão
do painel ficou bloqueado legitimamente. O limite130mm não foi silenciosamente
alterado para permitir o teste.
