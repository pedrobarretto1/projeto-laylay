# Comentário corporal ausente — 16/10/2026

Base: main, db2afb312341911c09836f678f046a9a273f14d4. Worktree já modificada,
incluindo firmware, corpo, UI e outros domínios; playlists.json no index foi
preservado. Nenhum commit criado. O baseline d850b8c de investigação anterior
não foi promovido nem usado como retrato do runtime atual.

## Primeira fronteira demonstrada

Pedro vê olhos/bips, mas não comentário no PC. A memória SQLite contém
observações IMU confirmadas da sessão ecad4105 às06:48, inclusive DESCONFIADA,
DESORIENTADA e RECOMPONDO. A desconexão posterior foi manual, segundo ele.

Replay dessa observação na composição instalada, sem USB nem voz: diretor
publica evento tipado e ComposicaoTurnoRuntime publica seu plano. A ponte de
iniciativa considera a fase planejado como conversa humana ativa, inclusive
quando plano e turno são o próprio evento sem autoridade operacional. O
callback real do ClienteLLMRuntime retorna ocupado; transporte retorna adiada
antes da chamada ao modelo. Evidência: composicao_antes.json.

Falsificados: ausência geral de percepção corporal (episódios reais existem),
perda do contrato/evento na cognição (publicados completos), necessidade de
alterar motores/firmware para remover esse bloqueio (fronteira no PC).

## Contrato e candidato

Owner: PonteIniciativaAplicacaoRuntime.turno_em_andamento. Um evento observado
coerente, com mesmo ID em turno/plano, ambos tipados evento e sem autorização
operacional, não toma a prioridade da conversa humana nem bloqueia a própria
autoria. Turnos humanos/legados, claims, fala e entrada recente conservam suas
guardas. Aplica-se a qualquer fonte de evento; não há exceção textual para IMU.

Produção alterada nesta investigação: somente
mente_laylay/integracao/ponte_iniciativa_aplicacao.py, neste método. O outro
trecho já modificado no arquivo e alterações anteriores da worktree são
preservados. Sem mudança de voz, configuração, firmware, sensibilidade ou PWM.

## Provas

- RED canônico:3 failed,8 passed; duas origens de evento e composição instalada
  falham na primeira asserção causal. red.txt.
- GREEN focado:63 passed. green.txt.
- Regressivos de presença/iniciativa/cognição:120 passed. regressivos.txt.
- Modelo real em replay offline: primeira tentativa excedeu12s; segunda gerou
  proposta em4,045s, aceita pela porta de agendamento capturada. Sem voz física
  ou observação nova nesse replay. composicao_depois*.json.
- Ensaio USB vivo de115s: leitura recente na mesma sessão0a91fee4, inclinação,
  DESCONFIADA e recomposição chegaram ao diretor. Primeira autoria teve timeout;
  segunda gerou comentário, mas suprimida_sombra. ensaio_vivo.json.

O ensaio isolado importa o root, não executa a inicialização completa que
carrega memória e prepara governança. Por isso seu modo sombra não prova a
configuração da aplicação normal. Não alterar produção para contornar essa
diferença de composição. Rodada de voz explicitamente autorizada é separada,
com modo sugestão somente no processo finito, sem outros produtores/executores.

## Limites

Não encerra CORPO-I2C-01 nem prova causa de reinícios históricos. O bloqueio de
prioridade e o timeout do modelo são fronteiras diferentes. Testes verdes e
proposta aceita não provam audição física. Ensaio bloqueia MOTOR, TURN, DEMO e
SENTRY ativo; não inicia companhia ou passeio. Resultado da rodada de voz e
estado final são registrados abaixo após o encerramento.

## Encerramento solicitado por Pedro para ir à escola

Segunda rodada, ensaio_vivo_voz.json: leituras recentes da sessão7bcd8876,
inclinação e recomposição chegaram ao diretor sem erros serial registrados.
Uma proposta foi reprovada pelo guardião corporal; outra gerada ficou novamente
suprimida_sombra. Alterar modo_padrao somente no processo não mudou o modo já
materializado no estado compartilhado. Portanto a preparação de voz desse
ensaio foi insuficiente; não usar esse resultado para declarar a configuração
normal bloqueada, nem a entrega física validada. Nenhum texto publicado ou
receipt de fala emitida foi registrado. Não enfraquecer o guardião nem liberar
autonomia global para fazer o ensaio passar.

Pedro interrompeu os testes para ir à escola e pediu o perfil normal pronto.
Consulta final somente de capacidades/estado:3/3 sincronizações na COM4,
motor suportado/disponível com limite5000ms, sensores ativos, inferior27mm,
frontal sem retorno válido, IMU calibrada/estável. Companhia e passeio ao iniciar
permanecem true, perfil rodas_suspensas. Sem regravação ou mudança persistente de
preferências; bloqueios temporários pertenciam apenas ao processo de ensaio.
Transporte encerrado, aplicativo fechado, nenhum processo Python restante.
Evidência: perfil_final.json. Nenhum movimento foi enviado nestas consultas.

Próxima fronteira: reproduzir comentário espontâneo com inicialização real
(memória e governança carregadas), mantendo motores bloqueados no transporte;
separar modo sombra do ensaio, rejeição de autoria e timeout. A correção de
prioridade tem RED/GREEN e geração real, mas entrega auditiva continua aberta.
