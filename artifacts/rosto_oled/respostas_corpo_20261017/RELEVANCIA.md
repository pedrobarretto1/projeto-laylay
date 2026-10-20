# CORPO-DECISAO-V1 — seleção contextual, 17/10/2026

Baseline: main, ca592a9609dd1865b63b22c714f8d3e802fa2a5c. Worktree
anterior de transporte/companhia/notificação/comentários e trabalhos paralelos
de explicação histórica preservados. Nenhum commit criado.

Pedro propôs substituir o tempo simples por uma escolha inteligente. A frase
"deixar aquele tempo de 1minuto" era ambígua; foi enviada pergunta assíncrona
e, sem resposta durante o trabalho, comunicada explicitamente a interpretação
de substituir o mínimo fixo. Não reduzir frequência global ou alterar motores.

## Primeira fronteira e contrato

Diretor validava a observação e descartava qualquer novo acontecimento antes
de 60 s. Porteiro de voz aplicava outro intervalo da mesma categoria, mesmo
quando o Diretor já decidira reagir. RED canônico demonstrou uma possível
borda nova bloqueada cinco segundos após obstáculo. Sem novidade relevante,
retirar os dois limites cegamente causaria repetição a cada ID de incidente.

O Diretor continua único dono da escolha comunicativa. A função pura em
ocorrencia_observada.py considera tipo de mudança medida, recuperação,
habituação ao mesmo assunto, custo de tentativas recentes e feedback/foco.
Tempos participam do decaimento contínuo da saturação; não existe minuto
universal nem agendamento para falar assim que ele vencer. O produtor não
republica situação inalterada e a política não confunde ID novo com novidade.

Valores iniciais explícitos: relevância comum 76, recuperação 68, susto e
resmungo 84, desorientação 90, possível borda 93; limiar 55, aumentado por
perfil silencioso e feedback negativo. Cada tentativa admitida soma custo 32
com decaimento de 20 s; mesmo assunto soma habituação 24 com decaimento de
120 s. Esses parâmetros são heurística inicial auditável, não aprendizado
sensorial nem uma chamada adicional de LLM. A mudança pode reagir antes de
um minuto ou escolher silêncio mesmo após ele, conforme contexto/histórico.

## Contrato até a voz

AdmissaoReacaoObservada é um receipt interno tipado, vinculado ao trace_id e
à vigência do mesmo owner, passado por Diretor -> autora -> fila -> porteiro.
Não contém permissão de execução nem confirma áudio. Autora rejeita receipt
de outro evento; fila e porteiro rejeitam inválido/expirado ou adaptador com
erro, sem fallback aberto. Só a frequência de emissões anteriores é delegada
ao Diretor. Recusa aprendida, prioridade humana, foco, repetição textual e
revalidação de entrega continuam válidos. Caminho legado sem receipt tipado
conserva sua governança anterior e não recebe essa delegação.

Tentativa falha no modelo ou TTS conta na saturação para evitar rajadas,
mas não vira reprodução confirmada. O owner conserva a identidade, validade
e efeito observado; não se inventa sensação, queda, saída ou deslocamento.
Dados de avaliação permanecem na mente compartilhada para inspeção.

## Escopo

Produção alterada neste incremento: autonomia/ocorrencia_observada.py,
autonomia/diretor_presenca.py, autonomia/resposta_evento_runtime.py,
autonomia/porteiro_proatividade.py, personalidade/voz_runtime.py e descrição
da capacidade em especialistas/capacidades.py. Os testes antigos do minuto
foram atualizados explicitamente para o contrato autorizado de saturação,
com novos controles de reação antes de 60 s e de repetição com novos IDs.

Sem alterar firmware, GPIO, PWM, autorização motora, modelo/pesos, voz ou
prompt. Nenhuma aplicação gráfica ou motor foi iniciado neste incremento.

## Provas

- RED inicial: seis falhas, incluindo novo perigo e recuperação bloqueados
  pelo intervalo universal, além da segunda decisão temporal do porteiro.
- Final: 152 testes passaram, cobrindo fatos/autoridade, saturação, foco,
  feedback, expiração, receipt de outro evento, falha de adaptador, fila,
  áudio/configuração, preempção e root instalado.
- Composição instalada: dois fatos de riscos distintos separados por cinco
  segundos chegam ao modelo simulado e à fila real de voz com porteiro real;
  falha de entrega permanece sem emissão confirmada. Hardware isolado.
- validar_relevancia_modelo_real.py: root e modelo reais, diagnósticos
  explicitamente controlados, timer sem execução e nenhum hardware/áudio.
  Primeira geração deu timeout de 12 s, resultado modelo_indisponivel. Segunda
  mudança para BORDA_SEM_RETORNO foi admitida cerca de 12,13 s após primeira
  admissão e agendada em 17,052 s desde início. Nova repetição do mesmo risco
  foi bloqueada imediatamente com pontuação 31,3 abaixo do limiar 55.
  Emitidas por áudio: zero; não se anunciou sucesso da geração que falhou.

Limites: ensaio controlado não comprova audição ou reação física aos sensores.
Timeout do modelo permanece separado. Parâmetros de expressividade podem ser
afinados pelo uso, sem garantir comentário em cada estímulo. O próximo início
da Laylay carrega o candidato; nenhum reinício de sessão pessoal foi imposto.
