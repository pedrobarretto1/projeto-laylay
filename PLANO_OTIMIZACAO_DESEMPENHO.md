# Plano de otimização de desempenho da Laylay

## Objetivo

Reduzir o tempo real e percebido de resposta sem enfraquecer linguagem natural,
personalidade, contexto, memória, segurança, confirmação observada ou a
orquestração cooperativa dos nove pilares.

## Linha de base observada

O diagnóstico registrado em `teste.md` mostra, em média:

- interpretação: 13 ms;
- preparação do prompt: 39 ms;
- LLM HTTP: 3.102 ms;
- resposta principal da LLM: 3.891 ms;
- pós-processamento: 5 ms;
- execução de comandos com integrações: 4.843 ms;
- fila de voz: 428 ms;
- síntese TTS: 1.988 ms;
- reprodução da fala: 5.360 ms;
- TTS total: 7.867 ms.

A duração da reprodução não é atraso puro: ela representa o tempo em que a
Laylay já está falando. Os maiores atrasos evitáveis são a LLM, eventuais
chamadas adicionais de reparo, a espera por confirmação externa e a síntese
antes do primeiro áudio.

## Princípios obrigatórios

1. Desempenho nunca autoriza uma ação nem substitui evidência real.
2. Fragmentos de streaming não entram em memória, aprendizado ou executores.
3. Fallback rápido não pode afirmar sucesso sem confirmação observada.
4. Cache de navegador, email ou IoT sempre informa idade e pode ficar obsoleto.
5. Cada etapa terá comparação antes/depois e chave de desligamento.
6. Otimizações preservam o contrato dos nove pilares e a voz única.

## P0 — Telemetria ponta a ponta

### Implementação

- [x] Criar um identificador de trace por turno e propagar pelos runtimes.
- [x] Medir entrada, fim do roteamento, prompt pronto, início/fim de cada chamada
      LLM, texto final publicado, entrada na fila TTS, fim da síntese, primeiro
      áudio e fim da fala.
- [x] Separar chamadas `principal`, `reparo_json`, `reparo_factual`,
      `continuação`, `reparo_comunicação` e `autoria_operacional`.
- [x] Registrar backend, modelo, rota, tamanho do prompt, limite de saída,
      quantidade de chamadas e motivo do reparo, sem conteúdo privado.
- [x] Expor p50, p95 e máximo por rota no diagnóstico, além da média atual.
- [x] Criar uma bateria fixa de conversas, comandos locais e integrações
      simuladas para comparar cada alteração.

### Arquivos principais

- `mente_laylay/memoria_mental/observabilidade.py`
- `mente_laylay/autonomia/resposta_ia_runtime.py`
- `mente_laylay/integracao/cliente_llm_runtime.py`
- `mente_laylay/personalidade/voz_runtime.py`
- `mente_laylay/memoria_mental/diagnostico_mente.py`

### Aceite

- [x] Todo turno informa p50/p95 por rota sem registrar prompts ou credenciais.
- [x] É possível distinguir espera de LLM, executor, fila, síntese e reprodução.

### Resultado da P0

- trace limitado aos 40 turnos mais recentes e percentis calculados sobre uma
  janela numérica limitada a 128 amostras;
- fase e rota são campos separados, evitando misturar `llm_normal` com estados
  finais como `executado`;
- nenhuma fala, mensagem, prompt, URL, caminho ou credencial entra no trace;
- bateria de regressão em `tests/test_p0_telemetria_desempenho.py`;
- validação final: 2.251 testes e 45 subtestes aprovados.

## P1 — Orçamento único de LLM por turno

Esta é a etapa com maior retorno esperado.

### Implementação

- [x] Criar um orçamento compartilhado por turno com prazo e contador de
      chamadas.
- [x] Permitir uma chamada principal e, no máximo, um reparo indispensável.
- [x] Priorizar reparo de segurança/factualidade, depois estrutura; estilo e
      variedade usam transformação local ou fallback natural.
- [x] Impedir sequências de três ou mais chamadas entre correção de JSON,
      realidade, continuação, comunicação e autoria.
- [x] Descartar resposta obsoleta por geração do turno e impedir sua entrega
      posterior; quando o transporte permitir, cancelar a requisição.
- [x] Aplicar circuit breaker depois de falhas repetidas e fazer uma sondagem
      controlada em estado `half-open` antes de liberar novamente a rota. A
      sondagem usa a próxima solicitação real, sem acordar o modelo local em
      background nem gerar tráfego sem pedido do usuário.
- [x] Adotar timeouts por classe: curto/interativo, normal e tarefa longa
      explícita, mantendo tarefas complexas fora do prazo curto.

### Arquivos principais

- `mente_laylay/autonomia/processamento_resposta_ia.py`
- `mente_laylay/autonomia/higiene_resposta_ia.py`
- `mente_laylay/personalidade/confirmacao_llm.py`
- `mente_laylay/personalidade/autoria_conversacional.py`
- `mente_laylay/integracao/llm_http.py`
- `mente_laylay/integracao/composicao_inteligencia_externa.py`

### Metas

- p95 de chamadas LLM por turno: 1;
- máximo normal: 2, somente quando o reparo for necessário;
- nenhum turno com três ou mais chamadas;
- fallback de conversa curta após falha: menos de 8 s;
- conversa curta com modelo local quente: p95 abaixo de 4 s.

### Resultado da P1

- orçamento canônico limitado a duas chamadas por turno, compartilhado entre
  interpretação, resposta principal, reparos, continuação e autoria;
- classes de timeout em 8 s, 20 s e 60 s, sempre limitadas também pelo prazo
  restante do turno e pelo timeout explícito menor do chamador;
- respostas concluídas depois de o turno ficar obsoleto são absorvidas antes
  de chegar à fala, ao histórico ou à memória;
- circuito abre após três falhas consecutivas, bloqueia novas chamadas por 15 s
  e só fecha após uma sondagem real bem-sucedida;
- chave de reversão `LAYLAY_ORCAMENTO_LLM_ATIVO=0`, sem alterar o comportamento
  histórico de timeout quando desativada;
- diagnóstico publica somente identificadores opacos, contadores, tipos e
  motivos; não guarda prompt, resposta nem texto do usuário;
- regressões específicas em `tests/test_p1_orcamento_llm_turno.py`;
- validação final: 2.264 testes e 45 subtestes aprovados.

## P2 — Prompt e saída proporcionais ao pedido

### Implementação

- [x] Decidir a rota antes de consultar fontes de contexto caras.
- [x] Não buscar páginas, arquivos, logs ou retratos amplos quando o assunto não
      precisar deles.
- [x] Criar orçamento explícito por fonte e manter o prefixo estável do sistema.
- [x] Reduzir conservadoramente a saída: rápida 96–128 tokens, objetiva
      192–256 e normal 320–400; preservar limites atuais em matemática,
      explicações longas e tarefas técnicas.
- [x] Compactar preventivamente prompts locais grandes antes do transporte.
- [x] Manter o servidor portátil vivo durante a sessão. Pré-aquecimento
      proativo não foi adicionado: ele poderia acordar o modelo sem pedido do
      usuário e será reavaliado junto da inicialização em duas fases na P4.

### Arquivos principais

- `mente_laylay/integracao/preparacao_llm.py`
- `mente_laylay/integracao/preparador_requisicao_llm.py`
- `mente_laylay/personalidade/proporcao_resposta.py`
- `mente_laylay/integracao/runtime_llm_portatil.py`

### Metas

- preparação do prompt p95 abaixo de 120 ms;
- conversa comum local com no máximo 7.000 caracteres de payload no p95;
- redução de 25% a 40% no tempo de geração de respostas curtas;
- nenhuma queda nos testes de naturalidade, continuidade e resposta completa.

### Resultado da P2

- conversa rápida usa um contrato canônico compacto com a mesma identidade,
  segurança, linguagem natural, aprendizado explícito e formato JSON;
- fontes de página, navegador, arquivos, playlists e resumo diário são
  consultadas somente quando o texto atual demonstra necessidade;
- o retrato seletivo da mente substitui a antiga duplicação da memória SQLite;
  a memória legada continua disponível quando esse retrato não existir;
- limites de saída: rápida 128, objetiva 224, normal 384, emocional 320,
  explicativa 512 e matemática até 800 tokens;
- compactação local agora acompanha a proporção da tarefa e não reduz a saída
  necessária para explicações ou cálculos;
- chave de reversão `LAYLAY_OTIMIZACAO_PROMPT_ATIVA=0`;
- diagnóstico informa se a otimização está ativa e quantas consultas de fonte
  foram poupadas, sem registrar o conteúdo dessas fontes;
- na amostra equivalente à saudação do teste manual, o payload caiu de 7.538
  para aproximadamente 2.203 caracteres, redução de cerca de 71%;
- regressões específicas em `tests/test_p2_prompt_proporcional.py`;
- validação final: 2.273 testes e 45 subtestes aprovados.

### P2.1 — Correção após teste manual

- [x] Compactar o retrato da mente por relevância antes do transporte,
      preservando plano, referente, segurança, evidência, continuidade,
      pessoas e aprendizados aplicáveis.
- [x] Limitar o histórico por caracteres e atos completos; a fala atual nunca
      é descartada e tarefas especializadas não sofrem esse corte.
- [x] Usar o contrato semântico compacto também no turno normal otimizado,
      sem remover obrigações, proibições ou autorização.
- [x] Separar resumo de página do perfil rápido: 320 tokens, classe longa e
      instrução factual sem saudação, metalinguagem ou personalidade forçada.
- [x] Recuperar interações do arquivo diário ainda não consolidadas quando o
      usuário perguntar o que aconteceu hoje.
- [x] Normalizar somente formatos legados inválidos da pendência canônica;
      pendências válidas continuam intactas e auditáveis.
- [x] Preaquecer o modelo local em tarefa mínima de infraestrutura, sem
      memória e sem bloquear a interface; desativável com
      `LAYLAY_PREAQUECER_LLM=0` e cancelado antes da chamada se a conversa já
      tiver começado.
- [x] Adicionar regressões específicas em
      `tests/test_p2_1_correcao_prompt.py` e `tests/test_runtime_llm_portatil.py`.
- [x] Validação completa: 2.281 testes e 45 subtestes aprovados.

## P3 — Tempo percebido no Terminal e na voz

### Implementação

- [x] Publicar o texto final validado imediatamente após o fechamento do turno,
      sem esperar a fala anterior sair da fila.
- [x] Manter a reprodução de voz serializada e garantir uma única mensagem
      visual por resposta.
- [x] Medir `texto_pronto → texto_visível` e `texto_pronto → primeiro_áudio`.
- [x] Avaliar síntese por frases: sintetizar a primeira frase, começar a tocar e
      preparar as seguintes em paralelo, preservando barge-in, lipsync e
      ducking suave.
- [ ] Somente depois, experimentar `assistant_draft` visual efêmero para conversa
      pura; substituir pelo texto validado e nunca encaminhar fragmentos a
      comandos, memória, aprendizado ou TTS.
- [ ] Se o perfil confirmar degradação em conversas longas, agrupar relayouts ou
      virtualizar mensagens antigas no Terminal 2.1.

### Arquivos principais

- `mente_laylay/personalidade/voz_runtime.py`
- `mente_laylay/autonomia/resposta_ia_runtime.py`
- `mente_laylay/integracao/desktop_bridge.py`
- `cliente/terminal_laylay_2.py`

### Metas

- texto final visível em até 100 ms depois de validado;
- fila de voz livre com p95 abaixo de 100 ms;
- síntese até o primeiro áudio com p95 abaixo de 2 s;
- nenhuma fala duplicada, misturada ou entregue antes da validação.

### Resultado da P3

- o texto consolidado agora é publicado pelo orquestrador logo depois da
  validação final, antes de aguardar qualquer fala anterior da fila;
- a voz continua serializada, e pedidos diretos que não passam pelo
  orquestrador conservam a publicação no início do áudio como compatibilidade;
- candidatos melhores do mesmo turno reutilizam `message_id` e atualizam o
  mesmo balão no Terminal 2.1, sem criar uma segunda resposta visual;
- `tts_texto_visivel` mede a entrega antecipada e `tts_primeiro_audio` passou a
  incluir fila mais síntese, refletindo o atraso realmente percebido;
- a mudança pode ser revertida com
  `LAYLAY_PUBLICACAO_VISUAL_ANTECIPADA=0`;
- a síntese neural fragmentada não foi ativada: o Edge TTS atual cria um
  arquivo completo por requisição, e dividir a fala multiplicaria chamadas,
  timeouts e risco de pausas entre frases. O experimento fica condicionado ao
  novo p95 de `tts_primeiro_audio` em uso real;
- `assistant_draft` e virtualização continuam condicionais: não entram antes
  de dados demonstrarem benefício, e rascunhos jamais poderão alimentar voz,
  memória, aprendizado ou executores;
- regressões cobrem publicação imediata, fallback de publicação no início da
  voz, atualização do mesmo balão, protocolo do bridge e métrica ponta a ponta;
- validação final: 2.284 testes e 45 subtestes aprovados.

### P3.1 — Correção após medição manual

- [x] Remover introduções metalinguísticas do resumo e limitar a resposta a
      frases completas, descartando finais truncados ou terminados em
      preposição solta.
- [x] Reduzir o resumo especializado para 3–4 frases e 240 tokens, mantendo o
      fallback extrativo factual quando a geração não fechar corretamente.
- [x] Em falas longas, sintetizar primeiro uma frase curta e preparar o
      restante em paralelo durante sua reprodução.
- [x] Preservar fila e reprodução únicas; se a segunda síntese falhar, somente
      o restante usa fallback local e o começo não é repetido.
- [x] Manter falas curtas no caminho simples e oferecer reversão com
      `LAYLAY_TTS_ANTECIPAR_PRIMEIRA_FRASE=0`.
- [x] Medir separadamente `tts_sintese_primeiro_trecho`, com orçamento de
      diagnóstico de 2 segundos, sem alterar a evidência de execução.
- [x] Validação final: 2.288 testes e 45 subtestes aprovados.

## P4 — Inicialização, persistência e integrações

### Implementação

- [x] Dividir inicialização em `chat_pronto` e `serviços_completos`.
- [x] Carregar primeiro interface, entrada, memória mínima e fila de voz;
      inicializar avatar, rede associativa, playlists e observadores depois,
      respeitando dependências.
- [x] Unificar operações SQLite relacionadas em uma transação e medir commits e
      espera por lock antes de considerar write-behind.
- [x] Reutilizar o estado passivo já publicado pela extensão e o cache do daemon
      de email, sem duplicar caches nem permitir que leitura antiga confirme uma
      ação. O resumo de uma página idêntica usa cache exato por conteúdo e TTL.
- [x] Manter timeout curto somente no contexto passivo do Chrome e conservar
      timeout de confirmação para comandos reais. As portas operacionais não
      consultam cache para alegar execução.
- [x] Cachear configuração Tuya por ambiente, tamanho e mtime dos snapshots;
      a chamada de rede continua síncrona no executor do dispositivo e só
      confirma sucesso depois da resposta observada.
- [x] Avaliar o polling do clipboard: a leitura permanece no observador de
      background e não apareceu no caminho crítico medido; o modo adaptativo
      não foi ativado para não perder alterações copiadas.

### Resultado da P4

- a inicialização publica `startup_chat_pronto` depois do núcleo mínimo e
  conclui avatar, rede associativa, Game Bar e demais serviços numa fase
  supervisionada de background;
- reversão disponível por `LAYLAY_INICIALIZACAO_DUAS_FASES=0`;
- as duas falas automáticas de início foram desativadas por padrão, inclusive
  a saudação ao abrir o chat; `LAYLAY_FALAS_INICIAIS=1` restaura o legado;
- gravações relacionadas da memória SQLite compartilham uma conexão e uma
  transação, com rollback integral se alguma etapa falhar;
- repetir o resumo do mesmo URL, título e texto em até dez minutos não chama a
  LLM novamente; qualquer alteração do conteúdo invalida a entrada;
- Gmail já mantinha cache atualizado pelo daemon, e a percepção de aba ativa
  já chega por eventos da extensão; esses estados continuam apenas informativos;
- a configuração Tuya é relida automaticamente quando variável, snapshot,
  tamanho ou data de modificação mudam, sem cachear o estado físico;
- nenhum write-behind, cache de confirmação ou polling adaptativo foi ativado
  sem evidência de ganho, preservando durabilidade e percepção de mudanças;
- validação final: 2.295 testes e 45 subtestes aprovados.

### Arquivos principais

- `mente_laylay/autonomia/composicao_servicos.py`
- `mente_laylay/autonomia/servicos_background.py`
- `memoria_sqlite.py`
- `mente_laylay/integracao/chrome_ws_transport.py`
- `mente_laylay/integracao/gmail_mental.py`
- `mente_laylay/iot/protocolos/tuya.py`

### Metas

- interface pronta para chat em até 3 s no p95;
- serviços completos em até 10 s no p95;
- SQLite comum abaixo de 20 ms no p95;
- leitura de email em cache abaixo de 250 ms;
- SLAs de Chrome e Tuya separados do tempo de conversa e sempre confirmados.

## P5 — Verificação e implantação gradual

- [x] Implementar uma fase por vez e conservar comparação com a linha de base.
- [x] Criar flags para orçamento LLM, publicação visual antecipada, TTS por
      frases, startup em duas fases e caches externos.
- [x] Rodar a suíte completa depois de cada fase.
- [x] Executar uma matriz automatizada equivalente aos testes manuais de
      conversa, comando composto, timeout, Chrome
      desconectado, IoT indisponível, voz interrompida e mensagens consecutivas.
- [x] Reverter automaticamente a otimização se aumentar fallback, contradição,
      fala duplicada, perda de contexto ou falso sucesso.

### Resultado da P5

- chave mestre `LAYLAY_OTIMIZACOES_DESEMPENHO=0` retorna toda a sessão ao
  comportamento conservador; as flags individuais continuam disponíveis;
- caches de resumo e Tuya ganharam flags próprias e nunca confirmam estado
  externo; conteúdo ou configuração alterados invalidam a entrada;
- o guardião de implantação observa somente códigos técnicos sanitizados, sem
  texto de conversa, prompt, caminho, URL ou credencial;
- uma ocorrência isolada não reverte nada. Três sinais consecutivos da mesma
  regressão, ou quatro sinais na janela de cinco minutos, desativam as
  otimizações pelo restante da sessão;
- a reversão desliga orçamento otimizado, prompt proporcional, publicação
  visual antecipada, TTS fragmentado e caches. A fala visual volta ao caminho
  compatível do início do áudio e nenhuma ação em andamento é interrompida;
- se a fase secundária de inicialização não puder ser agendada em background,
  suas etapas voltam automaticamente ao fluxo síncrono;
- `/diagnostico mente` mostra modo, quantidade de flags ativas, sinais e motivo
  de eventual reversão, sempre com `autoriza_execução=False`;
- matriz P5 focada: 196 testes aprovados;
- validação completa final: 2.303 testes e 45 subtestes aprovados.

## O que não fazer primeiro

- Não trocar o modelo antes de medir chamadas extras, prompt e cold start.
- Não remover verificadores de segurança ou confirmação para ganhar milissegundos.
- Não paralelizar ações mutáveis nem etapas com dependência causal.
- Não enviar streaming parcial à voz, memória ou executor.
- Não usar cache para afirmar estado atual de janela, áudio, email ou IoT.
- Não começar pelo streaming completo do TTS: é mais arriscado e o ganho maior
  está antes da síntese.

## Ordem recomendada

1. P0 — telemetria e benchmark.
2. P1 — orçamento único de LLM por turno.
3. P2 — prompt e tokens proporcionais.
4. P3 — texto antecipado e primeiro áudio.
5. P4 — startup, SQLite e caches de integração.
6. P5 — validação prolongada e remoção gradual das flags.
