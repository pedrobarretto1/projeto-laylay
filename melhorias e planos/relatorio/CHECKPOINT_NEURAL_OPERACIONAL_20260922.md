# Checkpoint neural operacional — 22/09/2026

## Estado desta rodada

Trabalho realizado somente na cópia local. Nenhum modelo foi promovido e o modelo ativo não foi sobrescrito.

### 1. Extensões multi-action
- validacao_extensao agora usa intent + action + escopo.
- Uma mesma intent pode manter extensões de actions distintas.
- Chaves antigas continuam compatíveis; extensões adicionais podem usar INTENT::action.
- Concorrência entre extensões continua fail-closed.
- O loader rejeita pares (intent, action) duplicados.

### 2. Gate de comando após extensão
- Uma extensão pode limpar somente o veto obsoleto intent_desconhecida.
- Isso só ocorre quando raw_is_command is True e a probabilidade original de comando já atingiu o threshold.
- Veto confianca_comando_abaixo_limiar não é removido.
- Extensão nunca transforma raw_is_command=False em comando.
- Campo de auditoria: command_gate_recomputed_after_extension=True.

### 3. Triagem prospectiva
Snapshot original: retomada_prospectiva_20260921.
- 52 eventos pendentes.
- 46 textos distintos.
- 21 candidatos literais.
- 5 contextuais.
- 1 agendado.
- 25 fora do perfil.
- 6 repetições textuais.
### 4. Rascunhos supervisionados
Foram gerados 21 rascunhos de curadoria IA, todos validados pelo contrato operacional canônico.
Eles continuam com revisão humana, treino, promoção e execução desabilitados.

O agrupamento de entidade usa alvo canônico sem alterar o texto literal.
Exemplos: ventildor -> ventilador e muica -> musica apenas para agrupamento.

### 5. VOLUME/set
O v26 original acertava 0/4 actions VOLUME/set, prevendo up.
Uma extensão semântica treinada apenas como sonda em memória:
- reconheceu os 4 eventos de volume;
- ativou em 0 dos outros 48 eventos;
- levou os 21 rascunhos de 17/21 para 21/21 em intent/action;
- corrigiu o veto obsoleto de volume 100 sem inventar comando;
- não foi persistida nem promovida.
A amostra possui só 2 textos positivos únicos, portanto não prova generalização.

### 6. IOT command head
No v26: ligue a luz = 0.529601; desligue a luz = 0.536968; threshold = 0.65.
A onda sintética v5, sem usar luz, elevou para 0.627758 e 0.586049.
Não houve falso comando nos 6 contrastes metalinguísticos testados.
Ainda não cruza o threshold e não deve ser promovida.

## Testes
Regressão focada final: 257 passed, 0 failed.

## Próxima fronteira recomendada
Não ajustar threshold para perseguir os dois challenges já observados.
Coletar novos exemplos prospectivos inéditos de flexões imperativas IoT e VOLUME/set.
Depois revisar/anotar independentemente e só então avaliar nova onda/candidato.
