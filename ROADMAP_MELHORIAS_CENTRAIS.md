# Roadmap de melhorias centrais da Laylay

Este arquivo acompanha capacidades da mente e do comportamento. Melhorias exclusivamente
visuais ficam em `ROADMAP_AVATAR_LAYLAY.md`.

## Base já existente

- [x] Interpretação semântica separa conversa, pergunta, menção, hipótese e comando.
- [x] Menção de música ou ação não autoriza execução automaticamente.
- [x] Resultados operacionais guardam `executou` e `confirmado`.
- [x] O verificador final bloqueia falas que alegam execução sem confirmação.
- [x] Aprendizados semânticos guardam origem, confiança e confirmação do usuário.
- [x] Correções do usuário podem invalidar aprendizados anteriores.
- [x] Fundamentação factual limita detalhes que não aparecem em evidência confiável.
- [x] O porteiro de proatividade considera conversa ativa, turno, fala recente,
  sensibilidade do momento, repetição e urgência.

## Entregue nesta etapa

- [x] Diagnóstico unificado da mente sem expor mensagens, credenciais ou memória privada.
- [x] Resumo de saúde dos módulos, fala, áudio, turno, última ação e pendências.
- [x] Comando prioritário que não depende da interpretação da IA.
- [x] Auditoria de saúde renovada no momento da consulta.

Comandos aceitos:

```text
/diagnostico
mostra o diagnóstico da mente
qual o status interno da Laylay?
mostra seus módulos
```

Perguntas subjetivas como “como você se sente dentro do PC?” continuam sendo conversa.

## Próximas etapas

### 1. Atualidade factual

- [x] Classificar se uma pergunta depende de informação recente.
- [x] Guardar data e validade da evidência usada.
- [x] Expirar fatos temporais antigos antes de reutilizá-los.
- [x] Distinguir opinião, memória do usuário e informação externa.

### 2. Cobertura de confirmação operacional

- [x] Auditar cada intent e documentar qual confirmação real ele oferece.
- [x] Marcar intents sem confirmação possível como `não_confirmado`.
- [x] Impedir frases conclusivas nesses intents.
- [x] Acrescentar testes de contrato para programas, navegador, mídia, arquivos e IoT.

### 3. Aprendizado contextual

- [x] Aplicar decaimento de confiança por tempo e falta de repetição.
- [x] Separar preferência geral de preferência condicionada a horário ou atividade.
- [x] Guardar contraexemplos e exceções sem apagar a regra principal cedo demais.
- [x] Pedir confirmação quando duas preferências confiáveis entrarem em conflito.

### 4. Autonomia adaptativa

- [x] Aprender frequência tolerada por tipo de sugestão.
- [x] Aumentar o intervalo depois de recusas.
- [x] Reduzir intervenções em jogos, reuniões e momentos de foco.
- [x] Manter alarmes e avisos de segurança fora dessas reduções.

Detalhes de comportamento e persistência: `AUTONOMIA_ADAPTATIVA.md`.

### 5. Diagnóstico evoluído

- [x] Exibir histórico curto de falhas sem dados privados.
- [x] Mostrar latência de interpretação, TTS e execução.
- [x] Informar por que uma ação foi bloqueada ou uma sugestão foi adiada.
- [ ] Criar painel opcional somente depois de estabilizar o retrato textual.

Detalhes das métricas e da proteção de privacidade: `DIAGNOSTICO_EVOLUIDO.md`.

### 6. Consciência temporal V2

- [x] Interpretar datas complexas, horários e recorrências em português.
- [x] Aprender duração aproximada de projetos concluídos.
- [x] Distinguir tempo cronológico de convivência ativa.
- [x] Recuperar eventos antigos com envelhecimento e relevância contextual.
- [x] Integrar observações da memória visual sem confirmar conclusões por imagem.
- [x] Pedir confirmação antes de encerrar uma pendência ambígua.
- [x] Calibrar acompanhamentos por perfil, emoção, atividade e porteiro central.

Arquitetura e exemplos: `CONSCIENCIA_TEMPORAL_V2.md`.

## Regras

- Não duplicar classificadores ou estados já existentes.
- Toda nova decisão deve usar a mente compartilhada.
- Uma intenção planejada nunca equivale a ação executada.
- Diagnósticos devem omitir mensagens, tokens, chaves, senhas e conteúdo pessoal.
- Melhorias entram em etapas pequenas, cada uma acompanhada por testes de regressão.
