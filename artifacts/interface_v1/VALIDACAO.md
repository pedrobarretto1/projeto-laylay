# Interface Laylay V1.0 — renderer local oficial

## Base congelada em 18/10/2026

- HEAD: `ca592a9609dd1865b63b22c714f8d3e802fa2a5c`.
- Branch: `main`.
- Worktree previamente modificada em `laylay.py`, mente/autonomia/cognição/memória/voz/corpo, planos/registros e testes desses contratos. Nada disso pertence a esta alteração visual; preservar integralmente.
- `cliente/terminal_laylay_2.py` e os módulos novos/tema/música deste recorte estavam sem modificações antes desta tarefa.
- Protótipo aprovado em `.codex/visualizations/.../laylay-coucou`; usado como referência visual. Seu HTML, dados fictícios e handlers simulados não são produção.

## Contrato de apresentação

Uma janela, uma ponte autenticada, uma sessão, um feed e um composer. Completa, painel e ilha alteram somente apresentação. O modo de apresentação não altera o modo Chat/Voz, não autoriza ações e não confirma efeitos. Estado real chega pela ponte; mascote apenas o apresenta. Música, playlists, configuração, memória, automação, streaming e sistema preservam seus executores/receipts existentes.

## Controle antes de produção

Comando:

```powershell
.\.venv314\Scripts\python.exe -m pytest -q scripts/tests/test_terminal_laylay_2_ui.py scripts/tests/test_terminal_3_p1_ui.py scripts/tests/test_terminal_3_p5_acabamento.py scripts/tests/test_terminal_streaming.py
```

Resultado anterior à V1: **54 passed, 1 failed em 12,25s**.

Falha anterior: `test_dashboard_pela_ponte_real_preserva_streaming_e_desconexao`, comparação do texto da página local. A extensão real do navegador conectou durante o teste e trocou `Aguardando conexão da extensão Laylay…` por `Extensão conectada · nenhum vídeo visível…`. Isso é uma mudança externa ao snapshot da mente; não foi atribuído à V1 e não deve ser escondido enfraquecendo a expectativa. Preservar como limite do baseline e retestar separadamente.

## Validação após aplicação

### Direção visual corrigida pelo usuário

A primeira implementação em Qt Widgets preservou transporte/dados, mas as capturas nativas mostraram diferenças de composição importantes em relação à prévia. Pedro reforçou que quer **exatamente o estilo da prévia**, não uma aproximação. Essa adaptação não é a entrega final aprovada.

A entrega segue com HTML/CSS local dentro do QtWebEngine existente, mantendo o layout aprovado e ligando controles ao protocolo canônico via QWebChannel. A página não depende do servidor da prévia. Dados fictícios e handlers simulados não entram no renderer de produção.

### Evidência intermediária nativa

O instrumento `validar_nativa.py` percorreu JanelaLaylay + PonteWorker + DesktopBridgeRuntime reais com plataforma `windows` e DashboardTerminalRuntime + psutil somente leitura. Houve handshake, snapshot, dashboard, envio/ack/resposta recebida enquanto recolhido e restauração da página anterior. Zero erros de slots Qt. Preferências isoladas em INI temporário, sem ler histórico pessoal. A mente não foi iniciada, nem microfone, player ou efeitos externos. Capturas `*-nativo.png` documentam somente essa etapa intermediária.

Novo teste do transporte autenticado: `scripts/tests/test_terminal_interface_v1_ponte.py` GREEN. O teste observa separadamente a chegada ao socket e sua aplicação pela fila Qt; na recusa, aguarda o balão falho e o fim da pendência. Não muda o contrato para confundir recebimento do protocolo com efeito visível.

### Evidência do renderer oficial

`validar_web.py` percorreu as nove páginas, painel e ilha com QtWebEngine na plataforma Windows, bundle local e DesktopBridgeRuntime autenticado. CPU/RAM são coletadas pelo DashboardTerminalRuntime com psutil. O teste usa preferências temporárias e conversa de validação com UUID válido; não carrega o histórico pessoal, credenciais ou a mente. A resposta publicada identifica explicitamente essa condição. As capturas `web-*.png` incluem 1440, 768 e 390 px. A captura aguarda a leitura real e duas pinturas do Chromium; uma primeira captura anterior podia registrar o frame passado, e não foi aceita como prova final.

`test_terminal_interface_web_v1_ponte.py` passou com envio pelo formulário HTML, QWebChannel, transporte autenticado, ack separado da resposta, resposta recebida enquanto recolhido, retorno à conversa, recusa observável com tentativa explícita e bloqueio do composer após desconexão. Conteúdo com marcação HTML é apresentado como texto. As três apresentações preservam rascunho e modo Chat/Voz sem emitir comandos.

A revisão visual independente aprovou a composição e o estilo da prévia nas nove páginas e três modos, inclusive 375/768 px. O resumo de métricas do DevConsole precisou de uma regra CSS ausente; foi corrigido e recapturado. Essa aprovação antecede os novos refinamentos pedidos em 20/10/2026 e não substitui a revisão desses refinamentos.

Regressão intermediária: 335 testes passaram e 1 falhou porque uma alteração da etapa nativa mudara o breakpoint do inspector de 1480 para 1240. O breakpoint original foi restabelecido no controlador de compatibilidade, preservando o renderer oficial aprovado. O teste responsável e vizinhos passaram (23/23). A falha anterior da extensão Streaming não se repetiu nessa rodada.

O teste de replay de receipt terminal reproduziu um pedido de ação já confirmado reaparecendo como pendente após recarregar o renderer. O cache agora encerra pendências por `action_state` terminal e pelos resultados tipados dos demais pedidos, mantendo o receipt publicado. RED e GREEN foram observados no mesmo teste.

Capas personalizadas reaproveitam o cache nativo `~/.laylay/playlist_artwork`. O renderer recebe somente o token público de 24 dígitos hexadecimais; o handler de imagens só aceita esse formato e imagens no cache, sem permitir caminho arbitrário, navegação ou script. Testes cobrem token inválido, query inesperada e bloqueio de origem remota.

### Refinamentos pedidos em 20/10/2026

- Música: play explícito por faixa, preservando `video_id`, revisão e executor canônico; animação condicionada ao estado observado e à preferência de movimento.
- Conversa: eliminar destruição/recriação dos balões, composer e mascote em cada tick de telemetria. A primeira fronteira demonstrada é a substituição integral de `workspace.innerHTML`, que reinicia as animações mesmo sem mudança na conversa.
- DevConsole: métricas com estilo, colunas de logs legíveis, módulos organizados e prompt/saída com aparência de terminal. Dados continuam vindo dos owners existentes.

Regressão do reparo de reinício visual e primeiros refinamentos: **352 passed em 86,98 s** (módulos `test_terminal*.py`, `test_desktop_bridge.py` e `test_saida_audio_terminal_musica.py`). A suíte inclui os 12 casos de estabilidade das páginas e o medidor pelo protocolo autenticado.

Um RED intermediário do teste DevConsole foi investigado: o foco explícito no prompt rolava de 31 para 308 antes dos eventos. Os ticks conservavam 308. O baseline do teste passou a ser capturado depois do foco/modal, e a invariância é verificada em cada tick; nenhuma proteção de produção foi removida para obter GREEN.

#### Raiz compartilhada de reinício visual

O usuário esclareceu que o defeito também aparece no Início, mascote, botão da trilha e outros elementos. O contrato é compartilhado: um evento de observação atualiza a projeção, sem destruir componentes vivos cuja identidade e conteúdo permanecem válidos. Não se corrigiu cada balão/player com temporizadores particulares.

Antes do candidato, o teste com mensagem realmente enviada pela ponte mostrou que ticks de `dashboard_state`, `state`, `music_meter` e `dev_events` trocavam as identidades de feed, input, mensagem e avatar. A substituição de `workspace.innerHTML` era a primeira fronteira incorreta. O candidato usa reconciliação incremental e mantém o relógio da animação; a montagem integral fica reservada à navegação ou troca de modo solicitada pelo usuário.

`validar_web.py --movimento` passou no Windows com telemetria psutil real e preferências isoladas. Quatro capturas `web-inicio-movimento-{0..3}.png` foram feitas entre atualizações. As asserções provaram a mesma instância DOM do mascote e do botão play, a mesma instância `CSSAnimation`, e `currentTime` avançando. O arquivo `resultado_web.json` registra `continuidade_dom_e_animacao: true`. Isso valida movimento contínuo sem obter um verde simplesmente desligando animações.

### Fluidez durante o uso

Após a correção de identidade/animação, o usuário pediu reduzir a sensação de peso na navegação e interação. Preservar nós evita o reinício visual, mas não prova que gerar/reconciliar a árvore completa para cada evento é barato. O instrumento `medir_fluidez_web.py` demonstrou renders síncronos dos subscribers somados ao RAF do core: seis rajadas de observações causavam 78 templates por cenário. A correção unifica invalidação em um RAF, conserva dados e notificação dos subscribers imediatamente, atualiza medidor localmente e evita projeção de áreas que não estão abertas. Navegação explícita cancela pintura redundante pendente. Ramos DOM idênticos são preservados sem nova visita, com exceção do reset controlado de campos após receipt.

Comparação no Windows com as mesmas fixtures, aquecimento de 350 ms, cópias congeladas de fontes, hashes SHA256 e filtro temporal para não contar o carregamento inicial:

| Cenário | Templates antes → depois | Tempo acumulado nos handlers antes → depois | Long tasks durante as rajadas |
| --- | --- | --- | --- |
| Conversa de 200 mensagens | 78 → 1 | 1257,9 → 7,1 ms | 6 → 0 |
| DevConsole de 160 eventos | 78 → 6 | 1991,5 → 5,6 ms | 6 → 0 |
| Playlist de 125 faixas | 78 → 0 | 1763,3 → 10,4 ms | 6 → 0 |

Fontes: `fluidez-antes-windows-aquecido.json` e `fluidez-depois-windows-aquecido.json`. São fixtures declaradas no renderer Qt, com GPU de software para comparação controlada; nenhuma habilidade é executada. O tempo de handler não representa todo o custo de layout/pintura nem garante FPS universal. O maior callback RAF visível do DevConsole foi 24,4 ms no candidato; a eliminação do trabalho repetido não significa ausência absoluta de um quadro mais longo.

A avaliação independente de interação enviou 400 observações: todas chegaram aos subscribers, o estado mais recente foi preservado e não houve templates síncronos. Uma recusa intercalada mudou a pendência imediatamente e apareceu no próximo quadro, sem perder foco/seleção. Navegação, filtro ERRORs, digitação e scroll foram exercitados sob atualizações. O visual das páginas e o contrato dos executores permanecem os mesmos.

### Últimos ajustes solicitados

Os seis cartões de métricas do DevConsole (CPU, RAM, VRAM, rede, eventos e ponte) foram removidos. A página conserva o terminal, os filtros, a saúde publicada e os resultados de comandos. Na Música, foram removidos os cartões laterais Modo de audição, Rotinas & agenda e Luzes RGB; o conteúdo passou a ocupar a largura disponível e mantém um único volume no player. Sistema e Automação continuam oferecendo seus dados e controles. As capturas Windows foram renovadas e os sete testes de páginas passaram.

No formulário de configurações, a migração para DOM estável expôs uma restauração indevida de valores antigos: o snapshot assíncrono atualizava o atributo do input, mas a rotina de restauração reaplicava seu valor vazio anterior. A restauração indiscriminada foi retirada; o navegador preserva campos editados no mesmo nó, e o receipt continua tendo reset explícito. Os testes aguardam a leitura pelo transporte real e verificam o valor visível, além do atributo e da identidade.

Regressão intermediária de fluidez: **354 passed, 1 failed em 89,71 s**. A única falha foi a mesma conexão assíncrona da extensão Streaming já reproduzida no baseline anterior à V1; nenhum teste foi enfraquecido e nenhum serviço do navegador foi parado para escondê-la. Após as últimas remoções e ajuste de formulário: **29 testes Web passaram em 36,78 s**.

Regressão final da worktree: **355 passed em 86,14 s** para todos os módulos `scripts/tests/test_terminal*.py`, `test_desktop_bridge.py` e `test_saida_audio_terminal_musica.py`. O teste Streaming passou nesta rodada; o comportamento assíncrono do baseline continua documentado, sem alteração da expectativa. `git diff --check` não encontrou erros nos arquivos do cliente/testes deste recorte. A avaliação final aprovou as remoções em 1440, 768 e 375 px sem overflow ou espaço reservado vazio. A última captura Windows com movimento confirmou novamente continuidade DOM/animação, telemetria e entrega autenticada. Nenhum teste equivale a uma sessão completa da mente ou confirmação de efeitos externos.

### Escopo e limites

O entrypoint `cliente/terminal_laylay_2.py:main()` abre `JanelaInterfaceWebV1`; a prévia HTTP não é necessária. As alterações ficam no cliente e testes/artefatos associados. Nenhum módulo da mente, voz, modelo ou executor foi modificado por esta tarefa.

Produção alterada:

- `cliente/terminal_laylay_2.py`: composição oficial do renderer e compatibilidade do controlador.
- `cliente/terminal_2/interface_web_v1.py`: canal local, renderer, apresentação e segurança de recursos.
- `cliente/terminal_2/web_v1/index.html`, `interface.js`, `paginas.js`: visual aprovado, projeção incremental e controles das páginas.
- `cliente/terminal_2/musica_m1.py`: remoção visual do sistema compacto musical pedida anteriormente.
- `cliente/terminal_2/mascote_v1.py`, `apresentacao_v1.py`, `theme/v1.py`: componentes de compatibilidade da etapa nativa, ainda usados pelo controlador e testes.

Produção não alterada por esta tarefa: `laylay.py`, `mente_laylay/`, firmware e executores externos. Suas alterações anteriores ou paralelas continuam preservadas.

O player Streaming preserva captura e fontes do módulo Qt existente em janela auxiliar local; navegar ou recolher interrompe a captura. Essa parte continua independente da IA. A tela HTML informa o botão que abre esse player.

A validação prova cliente, protocolo, apresentação e telemetria de leitura. Não prova execução musical externa, reprodução de voz, IoT ou uma sessão completa da mente, e não gerou executável portátil.

Nenhum commit criado. Não alterar credenciais, voz, modelos ou estado pessoal para validar a apresentação.
