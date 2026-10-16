# CORPO-SENSORES-PROTECAO-01 — retomada da busca após prioridade

Base: main, d850b8c90cc5ce40bd4832e759ed991ba88cd5cc. Worktree suja
preservada, status e arquivos anteriores neste diretório; nenhum commit.

## Primeira fronteira demonstrada

Companhia vigente → prioridade de conversa/tarefa → SENTRY0 → ESP corta tração,
mas muda a busca para CANCELADA → prioridade termina/SENTRY1 na mesma sessão
→ a trava não se libera enquanto a parede permanece. O owner do PC não
revogou a companhia. Cancelamento definitivo e suspensão temporária estavam
recebendo a mesma semântica no executor.

RED C++ em pausa durante giro, durante descanso e por lease vencida. Controles
GREEN antes do candidato: concessão contínua repete busca; STOP e borda não
repetem. Logo o esgotamento normal das quatro tentativas e a falta geral de
PWM não explicam esse RED. A borda é mantida segura nos três casos positivos.

Runtime anterior com montagem estável: runtime_antes_estavel.json. Mesma sessão
1b35ac3a, incidentes14/15 em busca, prioridade10.495–14.284s; CANCELADA10.65s,
vigia novamente ativa14.439s, sem novo incidente até32s. Superfície inferior
31–38mm/frontal33–47mm nas amostras listadas. Nenhum MOTOR do PC ou STOP no
intervalo; parada final32.028s. Prova real do mesmo mecanismo, não só harness.
runtime_antes.json anterior teve mudanças de leituras/gesto e não é a prova
isolada da prioridade.

## Contrato e candidato

Owner da concessão continua no PC. No ESP, suspensão de vigia de uma busca
autônoma de parede corta a ponte e passa a ESPERA_BUSCA; não afeta as fases
canceladas por STOP. Descanso4s e nova concessão vigente admitem novo episódio
após três leituras inferiores novas<=120mm, dados recentes e parede<=100mm.
Não avança enquanto a saída não for confirmada. Não restaura o giro anterior,
nem repete os recuos limitados de borda. A mesma admissão de superfície atende
a transição borda resolvida→parede e a repetição da busca.

Produção alterada: firmware/rosto_laylay/protecao_corporal.h.
Produção Python, pinos, PWM, limiares, sono e olhos não alterados. Testes no
host e contrato de concessão existente ampliados; runner de diagnóstico usa
o owner real de prioridade, sem parser paralelo ou autorização por diagnóstico.

## Validação

- RED e GREEN em red.json/green.json.12 cenários host: pausa em giro/descanso,
  lease, STOP, borda, histerese125mm, falha I2C, repetição normal, transição,
  medo, vetos e sons.
-141 testes Python passaram (39 proteção/recuperação/DEV +102 transporte/
  companhia). Um teste conhecido de receipt intent foi explicitamente excluído
  do segundo conjunto; não enfraquecido nem contado como GREEN.
- Host saúde/reconexão/presença/proteção/sensores/sono/som/olhos/motores GREEN.
- Compilado core3.3.12,432690 bytes flash/19356 globais; COM4 gravada e hash
  verificado. Perfil USB, sensores e proteção habilitados, limite motor5000ms.
- Primeiro ensaio posterior: timeout de comunicação, recuperação automática
  e novas buscas na sessão seguinte. Preservado runtime_depois.json; não prova
  isolada da pausa. Falha intermitente de comunicação continua separada/aberta.
- Repetição fixa também teve NACK_OLED e mudanças de superfície; preservada
  em runtime_depois_repeticao.json, sem contar como prova isolada da pausa.
- Prova posterior condicionada à montagem válida: runtime_depois_condicionado.json.
  Houve perda serial/reconexão antes do trecho. Na mesma sessão b3314471, busca
  do incidente1 confirmada37.908s; prioridade37.908–42.449s corta e mantém
  ESPERA_BUSCA; incidente2 inicia42.605s, CONFERINDO43.634s/BUSCANDO44.444s.
  Verificação automática confirma mesmo boot/sessão, companhia ativa e ausência
  de HELLO/MOTOR/STOP do PC nesse intervalo. Não é replay de ordem antiga.
  Depois a leitura inferior mudou para borda e bloqueou, preservando o veto.
  Encerramento56.232s com STOP/GOODNIGHT, serviços terminados e porta fechada.
  Confirmação visual humana solicitada; GUARD sozinho não prova deslocamento.

Retorno humano inicial: "pausa em duas sessoes". Ambíguo entre duas rodadas
com descanso e uma reconexão; esclarecimento solicitado. Ainda não contar como
confirmação visual de retomada contínua. Serviços permanecem encerrados.

## Segunda fronteira demonstrada pelo retorno humano

Pedro esclareceu: "Fez duas rodadas e depois parou de vez, mesmo com a parede
e o inferior seguro". Reaberto o encerramento: na mesma captura, incidente3
entrou em BLOQUEADA por BORDA51.342s e voltou a OBSTACULO52.151s. O incidente
havia começado como parede; sua causa inicial permanecia OBSTACULO, e a admissão
borda resolvida→parede não reconhecia o motivo que interrompeu aquela busca.

Novo RED canônico parede→borda transitória→superfície segura+parede: trava
permanente, mesmo com vigia contínua. Registro red_borda_durante_busca.json.
Candidato conserva a interrupção por borda separadamente da causa inicial e
reusa a admissão de três medições inferiores novas, sem liberar durante borda.
STOP também cancela fase já bloqueada; heartbeats não o apagam. Falha I2C não
ganha o marcador de borda. Sem alteração dos limiares, motores ou corpo Python.

14 cenários host finais GREEN, incluindo STOP entre a borda transitória e sua
resolução; regressivos completos de firmware repetidos GREEN. Build final
432726 bytes/19356 globais, gravada COM4 com verificação. Confirmação física da
primeira versão não foi aceita como GREEN; preservada acima por rastreabilidade.

runtime_final.json:50s sem falha de comunicação, mas inferior sem retorno em
toda a janela. O executor fez os recuos finitos de borda e ficou BLOQUEADA,
sem buscar parede; veto correto, não prova do candidato final. STOP/GN e serviços
encerrados. Solicitada superfície clara fixa8–10cm abaixo do inferior e consulta
das medidas antes de outro teste de tração. Não aceitar como GREEN físico.

Consulta posterior sem concessão: consulta_final.json, frontal63–64mm e
inferior59–60mm válidos, zero MOTOR/zero SENTRY ativo. Pedro confirmou montagem
pronta antes do novo teste. Firmware final em runtime_final_superficie.json:
uma sessão598cc5a2, mesmo boot, quatro incidentes de busca (2/3/4/5), pausa por
prioridade3.095–7.594s, novos giros8.773s/14.620s/20.784s. Sem falha de
comunicação ou MOTOR do PC nesse ensaio; STOP final intencional21.439s,
GOODNIGHT/serviços encerrados. verificacao_final.json valida esses contratos.
Não confundir o fim programado do ensaio com bloqueio. Confirmação humana das
rodadas seguintes solicitada; ainda não afirma proteção em deslocamento real.

Pedro confirmou a versão final: "Sim, continuou procurando nas rodadas
seguintes". GREEN de runtime e observação física das buscas repetidas em rodas
suspensas, após a pausa, na mesma sessão. Laylay/testes encerrados, motores
parados. A causa intermitente de comunicação continua aberta em CORPO-I2C-01;
este fechamento cobre a trava da busca, não esse mecanismo ou antiqueda real.

Sem validação antiqueda em deslocamento real. Rodas suspensas e sensores na
protoboard; não medir ângulo/posição por PWM nem chamar GUARD de prova visual.
