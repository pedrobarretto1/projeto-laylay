# CORPO-DEV-01 — diagnóstico corporal na aba DEV

Data: 13/10/2026. Baseline: main, d850b8c90cc5ce40bd4832e759ed991ba88cd5cc;
worktree extensa preservada. Cópias e estado inicial em `baseline/`. Sem commit.

## Fronteira e contrato

Os owners do transporte, da companhia e da experiência já expunham diagnóstico.
O retrato DEV só entregava eventos; a ponte não projetava o diagnóstico corporal
e a página não tinha apresentação dele. Esta é a primeira fronteira ausente.
Não era falta de decisão do corpo nem problema do protocolo do ESP.

Contrato: projeção observacional dos owners existentes → snapshot/lote DEV
autenticado → cache da interface → painel e histórico de mudanças. A projeção
não publica estado na mente, concede movimento, executa comandos ou estima
deslocamento. Callback diagnóstico falha aberta e não altera receipts.

## Implementação

- DevConsoleRuntime: allowlist sanitizada, getter de diagnóstico, registro de
  mudanças sem flood e consulta somente leitura `inspect corpo`/`inspect body`.
- Companhia/porta corporal: notificam o observador após publicação de intenção
  ou experiência; composição em laylay.py injeta os owners reais.
- DesktopBridgeRuntime: inclui `body` em snapshot e lotes, inclusive alterações
  sem eventos; preserva autenticação e separação de consulta/entrada/controle.
- Terminal: guarda o último retrato para a aba carregada sob demanda e invalida
  na desconexão. Página exibe conexão, perfil, companhia/passeio, intenção,
  fase, motivo, emoção, objetivo/turno, motores, receipt e som. Em larguras abaixo
  de 1320px mostra resumo acima do console; lateral completa nas maiores.

O diagnóstico real usa `porta_ativa`; o fixture foi alinhado a esse contrato.
PWM/parada são confirmações elétricas; a experiência tem seu próprio turno.
Deslocamento permanece não medido e a projeção nunca autoriza execução.

## Provas

- `red.txt`: ausência do contrato DEV antes do candidato.
- `green_final.txt`: 131 testes passaram (DEV, ponte, terminal, continuidade,
  objetivos entre turnos, experiência contínua e presença corporal).
- Teste de composição importa laylay.py real; teste de ponte usa socket e
  autenticação reais. Consulta não é encaminhada como entrada da mente.
- Controle de falha do observador preserva o receipt e o registro de experiência.
- Teste responsivo usa o bootstrap real de fontes. O mínimo de largura do Qt
  impede exigir 900px exatos; a asserção protege o limite real de 1320px e a
  visibilidade de resumo/lateral, sem alterar o layout existente da toolbar.
- `runtime_usb.json`: composição instalada, FACE confirmado pelo ESP na COM4,
  snapshot e atualização pela ponte real, consulta readonly e renderização Qt.
  A intenção `atenta` foi registrada como diagnóstico explícito no owner;
  não é evidência de autoria da LLM nem de movimento espontâneo nesta prova.
  Nenhum MOTOR foi enviado. Encerramento enviou STOP/GOODNIGHT e fechou a ponte.
- PNGs inspecionados: lateral, resumo compacto e página com dados USB reais.
  Renderização offscreen; não foi aberta a janela normal da Laylay.
- `git diff --check` sem erros nos arquivos envolvidos. Nenhum firmware alterado.

Escopo de produção: dev_console_runtime.py, desktop_bridge.py,
corpo_motor_runtime.py, companhia_corporal.py, laylay.py,
terminal_laylay_2.py, desenvolvedor.py e theme/developer.py. Mudanças anteriores
nesses arquivos continuam preservadas; este incremento adiciona observabilidade.

Limite: prova da entrega e apresentação do diagnóstico; não mede rotação,
trajetória, áudio físico ou sensores futuros. Não declara a suíte global verde.
Ao terminar, nenhum processo da Laylay ou do Terminal 2 permaneceu aberto.

## Refinamento solicitado — corpo somente sob seleção

Pedro relatou poluição visual e pediu mostrar dados corporais apenas ao clicar
na opção Corpo. RED no caminho real JanelaLaylay → dev_events → página:
ALL mostrava `[AUTONOMIA:CORPO]` e os painéis não dependiam de seleção.

Contrato de apresentação revisado: opção CORPO sempre acessível na toolbar;
painéis e eventos com o marcador canônico aparecem exclusivamente nesse filtro.
ALL/AUTONOMY e demais filtros não mostram esses eventos. O buffer e a categoria
canônica continuam intactos, sem desligar observação ou mudar decisões do corpo.
Atualizações ocultas ficam disponíveis ao selecionar CORPO.

Produção deste refinamento: somente cliente/terminal_2/desenvolvedor.py.
63 testes DEV/ponte/terminal passaram; regressão cobre chegada pelo receptor real,
seleção por clique, atualização oculta, isolamento de música e largura responsiva.
PNGs geral/CORPO foram renderizados e inspecionados. Sem teste de movimento,
firmware novo ou commit. Não abri a aplicação normal nesta continuação; os
processos que já estavam em execução foram preservados. A interface em execução
precisa ser reaberta para carregar a alteração.
