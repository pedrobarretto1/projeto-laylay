# CORPO-USB-IDENTIDADE-01 — seleção por alvo persistido

Autorização: Pedro pediu implementação do reconhecimento por chip/nome para
acompanhar mudanças de COM e de PC; informou indisponibilidade para testes
manuais. Baseline main/d850b8c90cc5ce40bd4832e759ed991ba88cd5cc; worktree suja
preservada em baseline_worktree.txt. Sem commit, regravação ou teste de motores.

## Fronteira e contrato

Antes: enumeração VID/PID exigia candidato único. Duas placas bloqueavam mesmo
com identidade conhecida; uma placa diferente sozinha era aceita como corpo.
Não era erro na unicidade: faltava uma seleção vinculada ao alvo persistido.
HEALTH já oferecia identidade efuse/fingerprint estável, separada de boot.

REDs comportamentais em red.txt: múltiplas portas, único corpo divergente e
configuração inválida. Ausência do setter persistente também foi registrada.
Contrato: configuração humana escolhe fingerprint; HEALTH comprova o candidato;
apenas correspondência única admite HELLO/FACE. Nome, porta e percepção não
concedem motores. Sem pareamento conserva a política anterior, sem TOFU novo.

## Implementação

- ConfiguracaoAplicacaoRuntime continua único owner persistente: duas chaves
  adicionais em configuracao.env, escrita atômica e validação compartilhada.
  Backup pessoal ignorado pelo Git em configuracao.env.identidade-usb.bak.
  Outros campos do arquivo foram comparados e preservados.
- RostoOledRuntime continua único owner serial de todas as capacidades do corpo.
  Sondagem HEALTH limitada a16 portas, sem reset DTR/RTS, sem comandar candidatos
  diferentes. Recusa duplicidade e ausência; porta ocupada não impede outra
  identidade correta. Revalida após HELLO; respeita encerramento durante sondagem.
  Manual também exige identidade; OFF, TCP e legado sem pareamento preservados.
- laylay.py injeta o getter do owner de configuração; sem scanner privado nas
  habilidades. A seleção é infraestrutura da capacidade existente, sem plano
  cooperativo novo, parser de autorização ou aprendizado de permissão.
- Diagnóstico chega à mente compartilhada, disponibilidade, catálogo e DEV→CORPO.
  Perguntas naturais distinguem configuração de conexão confirmada. Nome/fase
  de pareamento são dados públicos; não há identidade efuse bruta no DEV.
  Nenhuma memória semântica ou aprendizagem infere propriedade ou movimento.
- Fontes alteradas nesta tarefa: saude_corporal.py, rosto_oled_runtime.py,
  configuracao_aplicacao.py, laylay.py, dev_console_runtime.py,
  disponibilidade_operacional.py, capacidades.py, mapa_habilidades.py e
  cliente/terminal_2/desenvolvedor.py. Os diffs Git também contêm alterações
  anteriores preservadas. Nenhum firmware, motor ou sensor foi modificado.

## Provas

-62 testes focados passaram em contratos_final.txt, incluindo alteração de COM,
  múltiplos ESPs, identidade divergente/duplicada, firmware sem HEALTH, configuração
  inválida, mudança após HELLO, interrupção, porta ocupada, persistência, catálogo,
  perguntas naturais, composição instalada e regressivos de recuperação/DEV.
- Composição real importada, mesmos owners do corpo/mente e configuração salva:
 17/17 sincronizações pela COM4; nome e identidade verificados. Sem iniciar main,
  interface, companhia ou motores. Evidência em runtime_real.json.
- Controle negativo no hardware real: fingerprint diferente recusado; somente
  HEALTH enviado, sem HELLO/FACE/MOTOR. Serial fechada em negativo_real.json.
- Pareamento aplicado ao chip observado como Corpo da Laylay. No DEV, render
  com fontes Windows inspecionado em dev_pareamento.png (1500×900); nome e
  confirmação legíveis. Capturas iniciais offscreen sem fontes não provaram
  legibilidade e foram substituídas pelo controle com fontes carregadas.
- Outra máquina física/múltiplos ESPs reais não foram usados. Trocas de COM e
  placas foram verificadas nas portas simuladas, sem chamar isso de prova em
  outro PC. Transferir configuracao.env é necessário para conservar o vínculo.

## Regressão ampla e limites

Seleção ampla:290 passaram,2 falharam,1 xfailed e3 desmarcados. Os dois REDs
eram composição TCP (expectativa textual 'pulso') e coerência de indisponibilidade
musical. Dois controles adicionais falharam na sequência ICAPS esperada antiga
e no prazo do glitch TCP. provar_baseline.py retira só a seleção nova EM MEMÓRIA,
inclusive no subprocesso TCP: os quatro REDs continuam,3 controles passam.
Isso separa esses resultados do mecanismo novo; não encerra suas causas.

O teste antigo com relógio congelado e firmware falso que ignora ICAPS pode
ficar preso na espera. Execução foi interrompida e esse caso ficou desmarcado;
nenhum teste foi enfraquecido para anunciar verde global. Outros dois
desmarcados foram executados e mantidos como RED nos controles acima.
Sem suíte global verde ou declaração de saúde geral da worktree.

CORPO-I2C-01 continua aberta e separada: selecionar o chip correto não corrige
perda física/de barramento nem prova estabilidade prolongada. A identidade não
é autenticação criptográfica. Aplicação e serial encerradas; motores não acionados.
