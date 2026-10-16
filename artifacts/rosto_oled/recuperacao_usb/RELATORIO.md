# Reconexão corporal e reinícios aparentes — 14/10/2026

Baseline main d850b8c90cc5ce40bd4832e759ed991ba88cd5cc. Worktree extensa e
suja preservada; arquivos causais e status em baseline/. Nenhum commit.
Pedro esclareceu que o defeito já ocorria de manhã, antes da última versão.
Não classificar automaticamente como regressão do último patch de expressões.

## Fronteiras demonstradas

1. CORPO-CONEXAO-01: perda transitória da sessão chamava revogar no owner da
   companhia e consumia a preferência de início. Novo HELLO/FACE podia restaurar
   o rosto, mas não havia pedido vigente para renovar SENTRY/gestos. Regra antiga
   era intencional. Novo pedido de Pedro autoriza recuperação do mesmo corpo,
   mantendo STOP/manual/desativação como revogações. RED alcançou exatamente
   a ausência de recuperação pendente após perda da sessão, não um import.
2. CORPO-USB-RESET-01: abertura pyserial padrão usa DTR/RTS ativos. Na COM4,
   sem motores/HELLO, abrir/fechar padrão mudou identificadores de boot, com
   motivo esp_reset_reason=11 (USB). Configurar ambas as linhas inativas ANTES
   de open manteve o mesmo boot em seis aberturas/fechamentos consecutivos.
3. CORPO-I2C-01 (aberta): no primeiro ensaio natural dos serviços reais houve
   duas perdas OLED, mas boot cb948317 permaneceu e heap livre ficou280516,
   mínimo275340. Isso prova falha de comunicação/sessão naquele ensaio, sem
   reset de CPU nem prova de esgotamento de memória. Não prova mau contato,
   fonte insuficiente, excesso de CPU, NACK ou timeout específicos históricos.

## Contrato e candidato

Pedido de companhia no owner sobrevive a perda involuntária; a concessão antiga
é encerrada. HEALTH identifica o mesmo chip, boot, motivo, uptime, heap e perda
de sessão. Após novo FACE confirmado, saúde recente, sensores novamente
consultáveis e1s de conexão estável, cria nova concessão. Não reexecuta movimento,
emoção ou proposta interrompida. Outro chip, firmware sem identidade, parada,
manual e desativação não recuperam automaticamente. Contexto/LLM não autoriza.

BOOT recebido durante gesto invalida ACK antigo imediatamente, inclusive se a
USB não desaparece. Mudança de sessão impede sucesso do movimento anterior.
Amostra de sensor que envelhece entre consultas veta aquela tentativa; não
apaga sozinha a estabilidade de uma conexão confirmada. Esta segunda fronteira
do candidato foi RED antes da correção e apareceu na primeira composição real.

Firmware: HEALTH é somente leitura, não renova sessão ou tração; motivo de perda
agora separa TTL/OLED/I2C e TIMEOUT_OLED/NACK_OLED quando capturados. Não foram
aumentados timeout, PWM, tensão, orçamento de CPU ou limite de motores. Pinos e
frequências preservados. Diagnóstico chega à mente, catálogo vivo e DEV→Corpo,
sem logs por uptime/frame e sem exibir a identidade física bruta na interface.

Outra fronteira da mesma recuperação foi reproduzida após o relato de parede:
o PC renovava, mas `travaProtecao`/fase CANCELADA da sessão anterior impediam
qualquer nova reação enquanto a parede permanecesse. RED host em
validar_reconexao_protecao.cpp alcançou a segunda sessão/lease e falhou na
ausência de motor. HELLO agora encerra reflexo antigo; a primeira concessão
SENTRY ativa da sessão nova rearma a admissão de NOVOS episódios. FACE sozinho
não move; heartbeats da mesma sessão não reiniciam recuos. Host GREEN e vizinhos
de medo/busca/STOP/sono preservados. Não apagar travas a cada FACE ou por tempo.

## Provas

- RED do contrato de recuperação, GREEN depois; negativos STOP, outro chip,
  saúde antiga, ausência de permissões e interrupção cooperativa sem replay.
- Primeira tentativa de RED do serial tinha assinatura inadequada do dublê;
  descartada. Assinatura corrigida e função EXATA do baseline executada por AST:
  [(True,True)] versus esperado[(False,False)], RED correto. GREEN atual.
- Primeiro RED de amostra antiga usava infinito e falhou no fixture; descartado.
  Idade finita realista reproduziu a fronteira correta de estabilidade apagada.
-141 testes focados/regressivos GREEN. Rodada com companhia:149passed/1failed,
  KeyError intent em receipt da composição instalada, já documentado antes
  desta investigação; não enfraquecido nem corrigido aqui.
- Host C++ de saúde, presença, proteção/sono/som/olhos/motores GREEN.
- Firmware core3.3.12 gravado na COM4, hash verificado:432560 bytes flash,
  19356 bytes globais. Telemetria não aponta pressão de heap nesse ensaio.
  Build final com recuperação da proteção:432644 bytes flash,19356 globais.
- runtime_reset_controlado.json: serviços executar reais do root, com seus
  componentes compartilhados. Companhia ativa~2s, reset deliberado~20s, BOOT
  observado~21s, novo boot~24s, nova concessão~28s e reação aos sensores~29s.
  Não reiniciou processo da Laylay; sem replay do MOTOR anterior. Teste isolou
  os serviços corporais; não abriu toda a UI/conversa da aplicação.
- runtime_sem_motor.json:50s de sincronização, SENTRY desarmado, zero MOTOR,
  mesmo boot e sem novas perdas. Não reproduzir ali não exclui falha intermitente.
- DEV renderizado em dev.png e inspecionado; campos só na opção Corpo.

Build final na placa e prova da perda LÓGICA: runtime_perda_sessao.json, serviços
reais executados50s, montagem suspensa com superfície inferior e parede real.
Três incidentes de busca antes da substituição controlada da sessão~20s.
PC suspendeu, confirmou novo HELLO/FACE/HEALTH no mesmo boot6c382055, renovou
companhia~28s e o ESP saiu de CANCELADA para RECUANDO/BUSCANDO/CONFERINDO,
incidentes4–7. Sem reset de chip/processo Laylay e sem ordens MOTOR do PC;
novas reações locais, não reprodução do gesto antigo. Encerramento STOP/GN.
Esta é a contraprova da trava residual após reconexão sem reboot, ausente no
teste de reset físico que zera toda a RAM. Confirmação humana solicitada.

Pedro confirmou: "Sim, voltou a procurar depois da pausa". Validação humana
cobre a retomada física da busca após perda de sessão sem reiniciar a Laylay.
Não encerra a causa intermitente da comunicação OLED.

## Incidente do teste de reset

Um teste intermediário ligou DTR/RTS sem liberar a sequência completa e a placa
parou de responder, OLED retido; Pedro observou travamento/luz apagada. Esse
ensaio NÃO é prova de falha espontânea. Artefato preservado como
runtime_teste_reset_incompleto.json. Partida restaurada e sequência corrigida
conforme HardReset USB: DTR inativo, RTS alto200ms e baixo200ms, terminando em
repouso. ROM confirmou SPI_FAST_FLASH_BOOT e HEALTH respondeu. Pedro informou
que a luz voltou. A prova válida de recuperação é a rodada posterior acima.

## Ainda aberto / limites

Por que o OLED perdeu comunicação intermitentemente continua em investigação.
Pedro confirmou OLED e dois VL53L0X no3V3, SDA8/SCL9 compartilhados. Não há
medição de alimentação ou integridade dos sinais. Não atribuir a5V em SDA/SCL,
contato, brownout ou firmware grande sem evidência. Esp_reset_reason documenta
motivos de boot, não mede tensão nem comprova causa elétrica anterior.

Último ensaio sem motores foi explicitamente desarmado, então cobrir o frontal
não deveria produzir giro ali. Pedro relatou ausência de movimento; distinguir
essa configuração do teste ativo, e não apresentá-la como falha física provada.

Fontes: código do core local3.3.12/esp_system.h, Wire/esp32-hal-i2c-ng.c;
https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-reference/system/misc_system_api.html
e https://raw.githubusercontent.com/espressif/esptool/v5.3.1/esptool/reset.py.

Processos de teste encerrados, concessão revogada, STOP/GOODNIGHT e porta fechada.
Não declarar correção global da falha elétrica/visual nem proteção antiqueda.
