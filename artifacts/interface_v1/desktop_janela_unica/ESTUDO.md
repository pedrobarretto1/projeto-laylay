# Uma janela ancorada para todas as abas

Pedido: manter a ilha pequena inicial e a expansão aprovada, mas selecionar TODAS as abas dentro da mesma superfície centralizada no topo. Ao mudar de aba, animar largura/altura em vez de restaurar uma janela comum em outro lugar.

Baseline: main, HEADb128f4e48b774352846a40672de493d19c30f109. Worktree inclui refinamento, mascote e apresentação desktop aprovados, além de mudanças paralelas de corpo/cognição/documentação. Preservados integralmente; sem reset/commit/push/shutdown. Evidências anteriores em `desktop_integrado` preservadas.

## Primeira fronteira incorreta

`botão data-page → goPage → state.mode='full' → bridge.apresentar('full') → restauração de flags/geometria da janela comum`.

O backend já usa a mesma janela/controlador/worker, mas a navegação abandona o contrato de apresentação desktop. Isso altera moldura e posição, gerando a experiência de uma janela diferente que Pedro mostrou. O primeiro erro é a decisão de navegação que forçafull; não é falta de estado/dados, necessidade de novo processo nem falha na animação compacta já existente.

RED com QtWebEngine+socket+QWebChannel reais: `test_abas_abrem_dentro_da_ilha_sem_mudar_hwnd_canal_ou_ancora` chegou à ilha expandida, executou `goPage('home')` e falhou por modefull (**1failed em1,78s**). Não foi erro de import/rede. Hipóteses de nova mente necessária e backend ausente falsificadas pela composição e pelo estado autenticado da mesma fixture.

## Contrato

- No modo desktop, qualquer navegação de aba permanece desktop e conserva HWND/flags/âncora/WebView/página/canal/controlador/worker/sessão.
- Compacto/resumo/abas possuem geometrias preferidas limitadas à tela, todas derivadas da mesma âncora superior central. Uma animação cancelável aplica cada destino e respeita reduced-motion.
- Renderers reais das nove abas são reutilizados em região interna rolável; cabeçalho/navegação permanecem. Não há versões reduzidas ou vazias de música/configurações/sistema.
- Links internos, callbacks de conversas e bandeja seguem a mesma política. Rascunhos/scroll/receipts não são apagados e navegação não autoriza ação operacional.
- O gesto de resumo reduz o conteúdo na mesma superfície; recolher volta à ilha inicial. Modos legados só continuam pelos caminhos explicitamente legados, preservando compatibilidade.

## Candidato e controles

Produção desta correção: `interface_web_v1.py` mantém uma política nativa de seleção de página; `apresentacao_desktop.py` calcula os destinos das nove abas; `interface.js` conserva o modo desktop, cabeçalho e raiz DOM; `desktop.css` projeta os renderers oficiais dentro da ilha. Não houve alteração de autorização, executores ou estado da mente nesta correção. Alterações anteriores e paralelas da worktree foram preservadas. Nenhum commit criado.

A bandeja, links internos e callbacks de criar/selecionar/apagar conversa seguem a mesma política de navegação. Testes verificam identidade do HWND, flags, WebView, página, canal, controlador e worker, além da ausência de entradas operacionais por navegação. Há controles para animação interrompida, monitores negativos, telas estreitas, reduced-motion, rascunho, desconexão, receipts e encerramento do entrypoint real.

Foi identificado outro erro no mesmo contrato de continuidade: a conversa consultava a chave de scroll `full:chat` ao entrar em desktop. Uma fixture que já havia visitado o chat legado produziu GREEN inesperado; trocar a pré-condição para início real na Home reproduziu RED (posição5018 em vez de40). A chave comum `presentationLocation()` agora orienta tanto o render quanto a decisão de primeira visita. O teste passou após essa alteração.

A primeira avaliação visual aprovou a direção e pediu três ajustes locais: toast sem altura esticada, Home320px sem overflow ou colisão texto/mascote, e aba ativa sempre visível na faixa horizontal. O candidato inclui os três. A segunda avaliação confirmou toast de61px, Home com318px de conteúdo para318px disponíveis, separação do texto/mascote e preservação da leitura ao trazer a aba ativa à faixa visível. Resta um detalhe não bloqueante: em390px o rótulo Configurações ultrapassa a faixa em aproximadamente4px, sem perder interação ou nome acessível.

## Resultados automatizados

- Focados:23 testes GREEN, incluindo as nove abas, conversas, scroll, animação reversível, geometria, transporte e entrypoint oficial.
- Regressão final:479 testes GREEN em113,70s. Relatório `regressivos.xml` cobre todos os módulos `test_terminal*.py`, desktop bridge, saída de áudio/música e personalidade/persistência relacionadas.
- Sintaxe Python/JavaScript e `git diff --check` GREEN. Avisos Git sobre conversão de quebras de linha não alteraram arquivos.
- A suíte não comprova ações externas nem a mente completa: são verificados separadamente do comportamento local da apresentação.

## Prova nativa e limite de escopo

O validador `validar_web.py --desktop --janela-unica --movimento` clica nos botões das nove abas no Windows, amostra geometrias durante as transições e compara HWND, flags, centro, topo e raiz DOM. Também verifica hover sem roubo de foco, clique/teclado, cantos transparentes, recolhimento, retorno ao resumo e continuidade do mascote.

Execução final GREEN depois dos ajustes e dos479 testes: `qt_real/resultado_web.json`, plataforma Windows, frontend local, ponte autenticada. Todas as nove entradas de `abas_na_mesma_janela` confirmam `mesmo_hwnd`, `mesmas_flags` e `topo_e_centro_preservados`; as amostras mostram tamanhos intermediários. Hover, hit-test dos cantos, rascunho e teclado também passaram. Capturas nativas `qt_real/desktop-aba-*.png` registram cada aba. A segunda avaliação visual independente foi PASS, sem prioridades bloqueadoras; relatórios e capturas estreitas estão nesta pasta.

A execução final usou adicionalmente `--inspecionar`: depois das provas, deixou a própria demonstração compacta no topo para Pedro experimentar. Ela pode ser encerrada pela bandeja ou pelo arquivo local `qt_real/encerrar`, e possui limite de15min. Não há conexão à mente completa.

Isso comprova a navegação na janela Qt real com transporte autenticado de demonstração, não uma sessão da mente completa nem execução externa. A aba Streaming permanece na mesma janela; o comando explícito preexistente "Abrir player" ainda abre seu player nativo separado. Diálogos explícitos de arquivo/configuração também não foram redesenhados.

As evidências anteriores em `desktop_integrado` foram preservadas. A demonstração anterior foi encerrada pelo arquivo de controle do próprio validador, sem tocar Coucou nem processos reais do usuário.
