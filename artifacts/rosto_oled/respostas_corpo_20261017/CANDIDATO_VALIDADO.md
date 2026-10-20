# Comentários por episódio e continuidade da companhia — 17/10/2026

Base preservada: main, ca592a9609dd1865b63b22c714f8d3e802fa2a5c.
O baseline original e a investigação sem patch estão em baseline.json e
RELATORIO.md. Alterações anteriores de AUTO/USB/TCP e demais trabalhos foram
preservadas. Nenhum commit criado, firmware e pinagem não foram alterados.

## CORPO-DECISAO-V1 — admissão do comentário observado

Primeira divergência demonstrada: oportunidades distintas com o mesmo assunto
eram deduplicadas por 300 s. Após áudio bem-sucedido, cotas de companhia de
rotina também impediriam nova reação. A segunda geração da sessão histórica
foi descartada pelo intervalo de 120 s do porteiro. Falha de sensores e ausência
geral de geração foram falsificadas pelos eventos reais e pelo DEV.

Contrato: identidade de episódio e marco não é autorização. O produtor publica
início, mudança do risco e recuperação observados; fases repetidas do motor
não rejuvenescem a observação. O owner revalida sessão, origem, histórico e
TTL de 25 s. Coordenador distingue identidades em qualquer domínio; Diretor
só aplica o orçamento corporal após validação viva do owner. Corpo tem mínimo
de 60 s entre admissões, preservando foco, recusas, silêncio, prioridade humana
e deduplicação textual. Recusas aprendidas podem ampliar o intervalo. Valores
derivados da base antiga de 120 s são migrados preservando as recusas.

Admissão, geração/fila e entrega continuam distintos. Uma falha de voz não
conta como reprodução nem libera uma rajada de novas tentativas. A prova antiga
de HTTP 429 permanece histórica; não se trocou a voz nem se criou fallback.

## CORPO-CANCELAMENTO-01 — falha técnica não apaga pedido humano

Novo relato de Pedro durante o trabalho: motores já ignoravam sensores antes
do ensaio sem tração. Não atribuir esse relato ao desarme do diagnóstico.

Evidência histórica da mesma sessão ba710e67: execução corporal registrada às
13:50:14.155533, id 07a3b412a4c044689508623556f388fa,
resultado gesto_nao_confirmado, motivo sem_confirmacao_expressao,
zero movimentos confirmados. O ramo revogar apagava concessão e retomada;
autorizar_busca_obstaculos passava a negar SENTRY. Isso explica o silêncio
persistente posterior sem exigir que o sensor tivesse parado de medir.
Não demonstra a causa elétrica do EACK ausente nem encerra CORPO-I2C-01.

Contrato do owner: parada/desativação humana e encerramento revogam; falha
técnica suspende a concessão elétrica e conserva somente o pedido identificado.
Há pausa progressiva 2/5/15/30 s, sem reenviar a operação anterior. Recuperação
exige mesmo dispositivo, canal permitido, FACE confirmado, sensores recentes,
motor disponível/parado, IMU sem bloqueio, nova consulta HEALTH posterior à
falha, estabilidade de um segundo e STOP/SACK confirmado. A identidade da
consulta é acrescentada só após receber HEALTH correlacionado. STOP humano
concorrente vence a retomada. Falha de SACK mantém suspensão e intervalo de
nova tentativa; não vira loop de STOP a cada tick. O gesto continua falho nos
receipts e no aprendizado. A autorização não é fabricada pela percepção.

## Produção alterada neste candidato

- autonomia/ocorrencia_observada.py: identidade compartilhada de relato.
- autonomia/coordenador_oportunidades.py: deduplicação por ocorrência.
- autonomia/diretor_presenca.py: admissão de reação validada e orçamento.
- autonomia/porteiro_proatividade.py: base de 60 s e migração derivada.
- memoria_mental/experiencia_corporal_runtime.py: marcos e vínculo à prova.
- autonomia/companhia_corporal.py: suspensão técnica/retomada do owner.
- especialistas/rosto_oled_runtime.py: consulta_id no HEALTH recebido.
- especialistas/capacidades.py: descrição verdadeira da política de relato.

Sem alteração no executor de ações do PC, roteamento de autorização, voz,
firmware, configurações persistentes dos motores ou proteção física.

## Evidências e limites

- RED canônico inicial: 9 falhas pelos bloqueios de política/ausência de
  marcos; controles de prioridade passaram. Duas falhas de fixture foram
  corrigidas antes de tomar o RED como evidência (estado do coordenador e
  argumento obrigatório do porteiro).
- RED da suspensão: EACK ausente deixou companhia inativa sem retomada,
  reproduzindo a primeira fronteira histórica.
- Focados finais: 39 passaram, incluindo root instalado, modelo/saída física
  isolados somente nas bordas, dois domínios na identidade, fonte adulterada,
  repetição, recuperação de EACK e MACK, pausa progressiva, parada concorrente,
  outro ESP, saúde velha/ausente, manuseio e SACK ausente.
- Regressão mais ampla: 311 passaram, 1 RED anterior de receipt do ciclo
  CORPO_COMPANHIA (KeyError intent em ultima_acao_contrato). Já estava separado
  em transporte_automatico_20261017/RELATORIO.md; não enfraquecido nem corrigido
  nesta investigação. Conjuntos de testes se sobrepõem.
- validar_marcos_runtime.py: composição instalada e hardware reais, 55
  amostras, nenhum evento fabricado, nenhum movimento. Montagem permaneceu
  estável; não houve comentário corporal novo para comprovar ponta a ponta.
  Probe separado de voz recebeu confirmação de reprodução com FranciscaNeural.
  Isso não prova audição humana nem autoria de um comentário de sensor novo.
- validar_recuperacao_main.py: main/serviços reais por 55 s, placa conectada,
  uma confirmação EACK deliberadamente ignorada apenas pelo diagnóstico.
  Falha observada 14:51:52.868; companhia retomou 14:51:55.031; vigia voltou
  14:51:55.831. Mesmo boot 586bd4fb, sem reinício da aplicação. Após recuperar,
  foram enviados três comandos MOTOR novos; não se reenviou o gesto falho.
  Não confundir comando enviado com movimento humano observado.
- Encerramento: STOP final, concessão revogada, conexão encerrada, nenhum
  processo da Laylay/interface/avatar/sonda remanescente. Sem UI aberta.

Pendente: Pedro observar novamente a reação física a uma parede/borda e os
comentários em situações novas. Não houve estímulo manual de sensor no último
ensaio nem prova de estabilidade por horas; o frontal estava INVALIDA e o
inferior válido em cerca de 27 mm. Não declarar todas as quedas elétricas ou
falhas de sensores encerradas com esse resultado.
