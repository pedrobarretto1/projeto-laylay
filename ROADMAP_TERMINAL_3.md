# Roadmap — Terminal Laylay 3.0

## Objetivo

Evoluir o Terminal 2.1 para uma central desktop moderna, fiel à identidade da
Laylay e conectada à mente canônica. A interface deve reunir conversa,
automação, música, memória, saúde do sistema, rotinas e modo jogo sem inventar
estado nem criar atalhos paralelos aos executores existentes.

Referência visual: janela escura em três áreas, destaque coral, conversa no
centro, Central Inteligente e cartões operacionais laterais. A reprodução deve
ser fiel em telas grandes e responsiva em telas menores.

## Regras que não podem ser quebradas

- A interface exibe somente dados observados ou estados explicitamente
  indisponíveis; números decorativos são proibidos.
- Todo botão que executa algo envia uma solicitação à mente canônica. A UI não
  controla programas, IoT, música, agenda ou arquivos diretamente.
- Um controle só muda para o estado final depois de receber confirmação
  observável do executor correspondente.
- Memória é projetada por uma API sanitizada; o cliente nunca lê diretamente
  JSON, SQLite, credenciais ou estado interno mutável.
- O transporte autenticado, a reconexão, os ACKs, o indicador de pensamento e
  a configuração protegida do Terminal 2.1 devem continuar funcionando.
- Cada fase termina com testes unitários, integração pelo caminho real e uma
  verificação manual no Windows.

## Arquitetura alvo

```text
mente canônica
  └─ DesktopBridgeRuntime
       ├─ state                  atividade, emoção e modo
       ├─ dashboard_state        projeção pública do painel
       ├─ action_state           ciclo observado das ações rápidas
       ├─ assistant_message      resposta final
       └─ input_submit           ações voltam como linguagem natural

cliente/terminal_2/
  ├─ transporte.py              socket/reconexão, preservado
  └─ ui/
       ├─ tema.py               paleta, métricas e estilos
       ├─ componentes.py        cartões, chips e estados vazios
       ├─ inicio.py             conversa + Central Inteligente + lateral
       ├─ automacao.py
       ├─ musica.py
       ├─ memoria.py
       └─ sistema.py
```

`cliente/terminal_laylay_2.py` permanece como composição da janela. Regras de
domínio e coleta de estado continuam fora do cliente.

## P1 — Estrutura visual e página Início

Status: **concluída**

Escopo:

- Adotar a linguagem visual escura com destaque coral da referência.
- Ampliar a navegação para Início, Conversa, Automação, Música, Memória,
  Sistema e Configurações.
- Reutilizar a conversa real na página Início; não criar um feed duplicado.
- Criar os painéis Central Inteligente e lateral como componentes separados.
- Adicionar chips superiores de modelo, microfone e memória.
- Criar estados vazios honestos para dados cuja integração pertence às fases
  seguintes.
- Recolher painéis laterais de três para duas e depois uma coluna conforme a
  largura disponível.
- Preservar conversa, Chat/Voz, configurações, eventos, diagnóstico,
  reconexão, reenvio e reinício.

Critérios de aceite:

- Em tela ampla, Início apresenta conversa, Central Inteligente e lateral.
- Em tela intermediária, o painel menos importante é recolhido.
- Em tela estreita, a conversa e o compositor continuam utilizáveis sem
  rolagem horizontal.
- Conversa usa o feed, histórico, ACK e indicador já existentes.
- Cartões sem fonte real mostram `Aguardando integração` ou `—`.
- Ações rápidas habilitadas entram por `input_submit`; ações ainda não
  integradas ficam desabilitadas e explicam o motivo.
- A suíte anterior do Terminal 2.1 e as novas regressões da P1 passam.

## P2 — Estado vivo e telemetria sanitizada

Status: **implementada — aguardando validação real no Windows**

Escopo:

- Criar a mensagem tipada `dashboard_state`, separada do `state` rápido.
- Publicar saúde real da LLM, microfone e memória.
- Projetar contexto atual mínimo: projeto, modalidade, cidade configurada e
  modo jogo.
- Projetar memória recente por categorias públicas: lembrete, preferência e
  tarefa confirmada.
- Coletar CPU, RAM, disco e tempo ligado sem bloquear o turno.
- Publicar temperatura apenas quando o sensor for realmente acessível.
- Limitar atualização e deduplicar payloads para não sobrecarregar Qt/socket.

Critérios de aceite:

- Estado indisponível nunca vira zero ou sucesso.
- A UI não acessa arquivos de memória nem `psutil` diretamente.
- Atualizações do dashboard não interferem no ACK ou na fala final.
- Queda de um coletor degrada apenas o cartão correspondente.

Evidência da implementação:

- `dashboard_state` possui contrato versionado, sanitizado e separado do
  `state` rápido da conversa.
- Snapshot, atualização deduplicada e reconexão preservam uma única fonte de
  verdade; sem cliente autenticado, a coleta pesada permanece adormecida.
- Saúde da LLM, microfone, memória, contexto, CPU, RAM, disco, uptime e
  temperatura opcional são cacheados fora da thread da ponte.
- Coletores possuem orçamento individual; falha ou travamento de uma fonte
  não congela o painel nem transforma ausência em sucesso.
- Cartões de memória aceitam apenas lembrete persistido, preferência
  confirmada e tarefa executada e confirmada, com TTL, proveniência fechada e
  redação de conteúdo sensível.
- Estado antigo ou sem instante observável aparece como antigo ou
  indisponível; a UI não interpreta ausência de leitura como `Desativado`,
  lista vazia confirmada ou valor zero.
- O diagnóstico geral expõe saúde, sequência, coleta, fontes pendentes e
  falhas do dashboard sem autorizar execução.
- Validação automatizada: 23 regressões próprias da P2, 111 testes focados de
  UI/ponte/configuração/diagnóstico e suíte completa com 2355 testes e 45
  subtestes aprovados em 2026-08-11.

## P3 — Central Inteligente e ações confirmadas

Status: **implementada — aguardando validação real no Windows**

Escopo:

- Ligar Abrir VS Code, Organizar desktop e Briefing às intenções canônicas
  existentes.
- Consultar o catálogo vivo para Modo foco, Pesquisar e Ativar rotina; uma
  ação sem alvo ou capacidade registrada permanece indisponível, em vez de
  fingir que pode executar.
- Mostrar estados `enviando`, `recebido`, `executando`, `confirmado` e `falhou`.
- Correlacionar cada ação com seu pedido sem reaproveitar resultado antigo.
- Alimentar a atividade recente com resultados confirmados.

Critérios de aceite:

- Nenhuma ação é executada no processo da UI.
- Falha parcial não aparece como sucesso total.
- Repetição, recusa, confirmação e referências naturais continuam passando
  pelos componentes compartilhados da mente.

Evidência da implementação:

- A definição visual compartilhada identifica cada botão, mas o pedido ainda
  entra como linguagem natural por `input_submit`; a UI não importa nem chama
  executores.
- O catálogo vivo decide entre disponível, degradado, precisa de informação e
  indisponível. Somente as três ações atualmente completas podem ser enviadas.
- `action_state` diferencia envio, recebimento, execução, confirmação,
  resultado parcial e falha, sempre correlacionado ao ID do clique.
- A fala final é ligada ao texto do turno em processamento; uma resposta não
  encerra nem reaproveita outro envio pendente.
- Só `executou=True` com `confirmado=True` produz estado confirmado. Execução
  sem evidência fica parcial; ausência ou falha fica não confirmada.
- A atividade recente da Central recebe somente resultados confirmados, não
  eventos transitórios de conexão, pensamento ou simples entrega de fala.
- Validação automatizada: 10 regressões próprias da P3, 62 testes focados de
  UI/ponte/P1/P2, 77 testes de capacidades e linguagem natural e suíte completa
  com 2365 testes e 45 subtestes aprovados em 2026-08-11.

## P4 — Música, rotinas e páginas completas

Status: **implementada — aguardando validação real no Windows**

Escopo:

- Criar páginas próprias de Automação, Música, Memória e Sistema.
- Player com faixa, canal, capa derivada de fonte confiável, progresso,
  duração e estado de reprodução observado.
- Controles de mídia enviados pela mente canônica e confirmados pela extensão.
- Rotinas com horário, dias, estado e alteração confirmada.
- Modo jogo com estado real e transição segura.
- Sistema com histórico curto de CPU/RAM/disco, sem consultas bloqueantes.

Critérios de aceite:

- O player distingue comando enviado de áudio confirmado.
- Toggles nunca são otimistas.
- Ausência da extensão, sensor ou serviço aparece como indisponibilidade local.
- Memória exibida preserva fonte, privacidade e distinção temporal/durável.

Evidência da implementação:

- Automação, Música, Memória e Sistema agora possuem páginas próprias; o
  antigo placeholder não decide nem simula estado operacional.
- A extensão publica título, canal, posição, duração e estado real do elemento
  de vídeo. A capa é derivada exclusivamente do identificador observado do
  YouTube e a ponte aceita somente a origem pública `i.ytimg.com` esperada.
- Anterior, pausar/continuar e próxima faixa entram pela linguagem natural da
  mente como `panel_action`. O botão pendente não altera o estado exibido; só
  um novo evento observado da extensão muda `tocando`, `pausado` ou
  `finalizado`.
- A captura da faixa para playlists não depende mais da aba em foco: a
  extensão sonda todas as abas do YouTube, prefere áudio confirmado, depois
  reprodução confirmada e usa a aba ativa apenas como último recurso.
- Rotinas mostram apenas registros recorrentes ativos, persistidos por pedido
  do usuário. Cancelar envia um pedido canônico e a rotina permanece visível
  até a agenda confirmar a mudança em outro snapshot.
- O modo jogo permanece automático e somente leitura na interface, pois não
  existe hoje uma capacidade canônica confiável de ligá-lo manualmente.
- A página Sistema mantém histórico curto apenas de amostras frescas de
  CPU/RAM/disco. Sensor ausente, dado antigo ou fonte indisponível aparecem
  como `—`, `antigo` ou indisponível.
- A página Memória reutiliza a projeção da P2; não lê SQLite/JSON, não exibe
  payload executável e conserva a origem visual de lembrete, preferência e
  ação confirmada.
- Validação automatizada: 11 regressões próprias da P4/extensão, 109 testes
  focados de UI/ponte/dashboard/extensão e suíte completa com 2432 testes e 45 subtestes
  aprovados em 2026-08-12. Ruff e `git diff --check` aprovados.

## P5 — Acabamento e robustez Windows

Status: **implementada; aguardando validação visual real no Windows**

Escopo:

- Adotar SVGs próprios em vez de depender de glifos Unicode.
- Adicionar waveform real do nível do microfone.
- Refinar microanimações, foco, contraste e navegação por teclado.
- Avaliar barra de título sem moldura, arraste, maximização e resize nativos.
- Fazer stress de abrir, fechar, reiniciar, reconectar e alternar Chat/Voz.
- Medir consumo e fluidez com histórico longo.

Implementação desta etapa:

- A conversa recebeu cabeçalho contextual, balões compactos, avatar por fala
  da Laylay, compositor com acesso ao modo de voz e hierarquia visual próxima
  da referência aprovada.
- A navegação, envio, microfone e controles musicais deixaram de depender de
  glifos de fonte e passaram a usar SVGs locais.
- O ouvido publica somente um nível RMS normalizado e efêmero; o Terminal não
  recebe, grava nem persiste amostras de áudio. O waveform reflete esse valor.
- O painel lateral ganhou barras baseadas em telemetria real, capa musical
  com a mesma thumbnail segura da página Música (e disco genérico como fallback),
  progresso e tempos observados e controles que continuam entrando pela porta
  canônica, sem mudança otimista.
- A moldura personalizada foi avaliada e não ativada. A moldura nativa continua
  sendo a escolha consciente nesta versão por preservar resize, DPI e estabilidade
  após os incidentes nativos de Qt/Tcl; o restante do shell aproxima o visual sem
  trocar robustez por uma semelhança puramente cosmética.
- A largura responsiva desconta o avatar da fala e continua sem rolagem horizontal
  em 375 px. Uma regressão com 90 mensagens preserva a posição de leitura.
- Controles legados de voltar, avançar e título permanecem filhos do cabeçalho
  e ocultos; trocar de página ou redimensionar não os promove a mini janelas.
- A navegação ganhou atalhos `Ctrl+1` a `Ctrl+7`, ordem de Tab, nomes
  acessíveis e foco visível. `LAYLAY_REDUZIR_MOVIMENTO=1` conserva o estado
  visual sem animações obrigatórias.
- Processos Qt independentes abriram, navegaram, alternaram Chat/Voz,
  redimensionaram e fecharam nas escalas 100%, 125% e 150%, sem falha nativa.
- O player efêmero não é restaurado entre sessões. Ao reconectar, a extensão
  publica a faixa realmente observada (tocando ou pausada) ou uma ausência
  explícita que limpa o resíduo anterior sem apagar a playlist persistida.
- Validação automatizada: 12 regressões próprias da P5, 104 testes focados,
  Ruff, compilação e `git diff --check` aprovados; suíte completa com 2444 testes
  e 45 subtestes aprovada em 2026-08-12.

Critérios de aceite:

- Nenhum encerramento nativo de Qt/Tcl no Windows.
- A janela continua operável com escala de 100%, 125% e 150%.
- O histórico longo não pisca, some ou perde a posição de leitura.
- A barra personalizada só entra se igualar a estabilidade da moldura nativa.

## Aplicação dos 9 pilares

1. **Contexto:** o dashboard recebe somente a projeção necessária ao painel.
2. **Memória:** cartões distinguem contexto efêmero de memória persistida e
   mostram apenas fatos com fonte aceita.
3. **Aprendizado:** ações da UI publicam os mesmos sinais de aceitação, recusa,
   correção e repetição usados pelos demais canais.
4. **Linguagem natural:** ações rápidas entram pelo interpretador canônico;
   não haverá um segundo roteador privado na interface.
5. **Continuidade:** respostas, referências e tentativas usam pedido e ação
   pendente canônicos, correlacionados por identificador.
6. **Segurança:** discussão, sugestão, autorização, execução e confirmação
   permanecem separadas; toggles não concedem permissão implícita.
7. **Diagnóstico:** cada coletor e painel informa disponibilidade, latência,
   falha e idade do último estado observado.
8. **Consciência de capacidade:** a Laylay só descreve funções disponíveis no
   runtime e explica limites como sensores, extensão ou credencial ausentes.
9. **Orquestração cooperativa:** ações compostas continuam no coordenador
   compartilhado; o painel apenas acompanha etapas e resultado parcial/final.

## Matriz mínima de testes

- Construção e navegação de todas as páginas.
- Layout amplo, intermediário e estreito.
- Chat, ACK, timeout, reconexão e indicador de pensamento.
- Snapshot sem dashboard e `dashboard_state` parcial/completo.
- Valor indisponível, coletor atrasado e payload inválido.
- Ação rápida aceita, recusada, parcialmente concluída e sem confirmação.
- Player sem extensão, enviado sem áudio e reprodução confirmada.
- Toggle de rotina/modo jogo aceito, recusado e revertido pela observação.
- Memória sanitizada sem credenciais, payload executável ou conteúdo privado.
- Reinício e encerramento real no Windows.

## Registro de progresso

| Data | Fase | Estado | Evidência |
|---|---|---|---|
| 2026-08-11 | P1 | Concluída | Shell em três áreas, navegação, chips, placeholders honestos e ações canônicas; testes automatizados aprovados e validação visual real aprovada pelo usuário. |
| 2026-08-11 | P2 | Implementada | Estado vivo sanitizado, coleta isolada, memória pública, telemetria, deduplicação, reconexão e diagnóstico; 23 regressões próprias, 111 focadas e suíte completa com 2355 testes + 45 subtestes aprovados. Aguardando validação real no Windows. |
| 2026-08-11 | P3 | Implementada | Catálogo vivo das ações, correlação por pedido, estados observáveis e atividade somente confirmada; 10 regressões próprias, 62 focadas, 77 de capacidades e suíte completa com 2365 testes + 45 subtestes aprovados. Aguardando validação real no Windows. |
| 2026-08-12 | P4 | Implementada | Páginas reais de Automação, Música, Memória e Sistema; player observado pela extensão, seleção da aba audível independente do foco, controles canônicos não otimistas, rotinas persistidas, jogo automático e histórico local. 11 regressões próprias, 109 focadas e suíte completa com 2432 testes + 45 subtestes aprovados. Aguardando validação real no Windows e recarga da extensão. |
| 2026-08-12 | P5 | Implementada | Acabamento fiel sem moldura arriscada: SVGs locais, conversa com avatar e balões, waveform RMS efêmero, telemetria visual, player compacto com thumbnail real e reconciliação limpa entre sessões, acessibilidade, movimento reduzido, DPI 100/125/150%, responsividade com histórico longo e correção das mini janelas órfãs. 12 regressões próprias, 104 focadas e suíte completa com 2444 testes + 45 subtestes aprovados. Aguardando validação visual real no Windows. |
