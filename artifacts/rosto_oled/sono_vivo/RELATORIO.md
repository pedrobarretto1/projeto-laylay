# Sono vivo — 12/10/2026

Pedido: variar somente a animação de sono, como se estivesse sonhando,
sem andar e com no máximo um bip discreto ocasional.

Base: main, d850b8c90cc5ce40bd4832e759ed991ba88cd5cc. Worktree já continha
expressões, som e integração corporal, além de alterações paralelas.
Baseline específico preservado em baseline/; nenhum commit criado.

Fronteira: o render de repouso usava um arco fixo, respiração periódica fixa
e Zs reiniciados a cada 3120 ms. Sessão e presença já tratavam o sono;
nenhum defeito no cérebro foi inferido desse aspecto visual.

Contrato: variações locais do periférico não escrevem emoções da mente,
não concedem movimento, não consomem receipts ou sequências e cedem à
reconexão. O owner da presença mantém seu morph quintico de 3 segundos.
O executor motor e o protocolo de controle permanecem sob seus gates.

Produção deste incremento:
- sono_vivo.h: cenas de olhos fechados, intervalos variáveis, respiração e Zs.
- rosto_laylay.ino: mistura dessas cenas no desenho de sono.
- som_expressivo.h: nota local de 65 ms, duty 10/255, prioridades e corte.

Notas locais não alteram o duty 128/255 e as melodias diurnas. Primeiro som
após 55–90 s; seguintes a cada 65–120 s. Exclusivo GPIO6, circuito preservado.
As cenas representam sonhos visualmente, sem alegar experiência mental.

GREEN host: validar_sono_vivo percorreu quatro minutos do loop real, três
estilos, dois bips no ensaio final, nenhum PWM de motor, nSLEEP LOW, reconexão sem bloqueio
do SOUND diurno e passagem pelo wrap de millis. Validadores presença V2,
som/olhos e expressões V3 também verdes. Hardware substituído no host:
essas provas não medem som físico ou movimento real. Frames PGM e GIF
produzidos pelo firmware, sorriso inspecionado visualmente.

Arduino core 3.3.12: USB CDC, Wi-Fi OFF, motores ON, limite 5000 ms;
399732 bytes de sketch final, 17508 bytes globais. COM4 identificou ESP32-C3,
gravou o refinamento final e verificou hash dos segmentos.
Nenhum comando de movimento enviado nesta tarefa. Laylay fechada para
liberar a serial e deixada fechada para observar o sono.

Pedro confirmou a primeira variação: "esta bem melhor, mas falta ficar fluido".
Esse retorno rejeitou a suficiência visual da primeira versão, apesar dos hosts
verdes. Refinamento seguinte: cobertura fracionária das bordas com dither
espacial estável, entrada/saída gradual dos Zs e intervalo de atualização
de 20 ms apenas no sono (cadência física limitada também pelo I2C/display).
Ensaio final mediu maior passo de 54 pixels entre amostras de 20 ms; isso
não é comparação controlada com a primeira versão nem prova isolada de fluidez.

Confirmações físicas finais: "Sim, ficou fluido" e "ouvi o BIP e esta do meu
agrado". O arquivo de som foi preservado no segundo refinamento. Nenhum
movimento foi solicitado. Não declarar suíte global ou medições elétricas.

Prévia final: sono_vivo_v2.gif; poses_sono_v2.png. Frames da primeira versão
também preservados para histórico.
