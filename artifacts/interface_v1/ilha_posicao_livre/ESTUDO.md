# Ilha arrastável e posição persistente

Base: main, HEAD b128f4e48b774352846a40672de493d19c30f109; worktree suja preservada. Nenhum commit criado nesta iteração. Evolução do contrato de apresentação registrado em `../ilha_integrada_suave/ESTUDO.md`, sem atribuição a raízes de cognição.

Pedido: arrastar a ilha, salvar a posição e iniciar abaixo das abas do navegador; manter a mesma janela, as abas, as transições e o recolhimento em 20s.

Primeira fronteira demonstrada: o cálculo de geometria fixava centro horizontal/topo da área útil em cada apresentação. A ponte tinha startSystemMove sem chamada correspondente no renderer, sem posição persistida. A preferência do usuário não tinha owner representável. RED canônico antes do candidato: `test_posicao_inicial_da_ilha_libera_a_faixa_das_abas_do_navegador`, 1 failed em 1,48s, top=0 contra top esperado=120; a execução alcançou geometria real do controlador Qt.

Hipóteses concorrentes: não é preciso detectar abas de um navegador específico para reservar a faixa superior (a própria geometria invade a faixa); não é preciso outra janela ou outro renderer para mover a superfície (o HWND e os objetos existentes são os donos da apresentação). A persistência não deve adotar o clamp de uma página grande como se fosse uma nova escolha humana.

Contrato: JanelaInterfaceWebV1 possui a âncora lógica da ilha compacta. Sem preferência, inicia centralizada e 120 DIP abaixo do topo útil. Arrasto humano concluído salva versão, monitor e offsets locais em QSettings. Navegação, expansão, clamp e mudanças de tela não gravam uma escolha fictícia. O painel é ajustado para caber, e o recolhimento volta à âncora. Movimento usa coordenadas lógicas Qt; nenhum envio à mente. Soltura fora da janela encerra arrasto; arrasto não produz clique nem recolhimento no meio do gesto.

Validação focada final: 43 passed em 17,24s (`focado.xml`), incluindo soltura fora da ilha, aplicação do último deslocamento e posição salva dentro da área útil. Uma falha intermediária da fixture foi investigada: o stub de QCursor devolvia a mesma instância mutável de QPoint, fazendo o deslocamento também modificar a origem. O stub passou a retornar cópia como a API real. Não houve patch de produção para compensar esse erro da bancada.

Regressão ampla relevante: 498 passed em 122,59s (`regressivos.xml`), módulos terminal, desktop_bridge, saída de áudio musical e política/persistência de personalidade. O caso adicional de soltura fora foi acrescentado após a coleta da suíte ampla e está incluído nos43 focados finais; total499 casos distintos verdes. Nenhuma mudança de produção entre as execuções.

Prova integrada Windows em `qt_temporal/resultado-integrado.json`: renderer oficial QtWebEngine, WebChannel e owner reais, janela Qt.Tool canônica, entrada Qt sintética com estado do botão injetado exclusivamente na bancada. Default [1148,120,264,50], destino após arrasto [1308,205,264,50], HWND3409494 constante, nove abas, zero envios à mente, objetos preservados. O arrasto não expande; clique posterior abre. Cada página volta à mesma posição sem regravar a preferência. As asserções aguardam fase idle e opacidade1, e as capturas completas estão na mesma pasta.

Reabertura em outro processo: `restauracao-processo.json` confirma primeira geometria [1308,205,264,50] em novo HWND1312400, zero envios. O registro exploratório recebeu outros gestos após a abertura; por isso a restauração é conferida na primeira amostra, em vez de supor ausência de interação posterior.

Revisão visual independente PASS na tentativa1, sem prioridades bloqueadoras; relatório copiado em `avaliacao_visual.md` sem leitura pelo orquestrador. Browser confirmou eventos reais de mouse, grab/grabbing, limiar, supressão de clique residual, clique seguinte, nove abas375px e DOM preservado.

Limites: o Computer Use não enumerou a janela da bancada, inclusive numa tentativa com tipo normal; não foi inventado um handle. A prova controlada nativa usa entrada Qt sintética e não é anunciada como arrasto físico Sky. Monitores negativos, monitor ausente e preferências inválidas têm regressões de contrato; desconexão física de monitor/DPI não foi executada. A reserva120DIP é política previsível, sem detecção de barras de navegadores. A captura exploratória anterior que mostrava corpo vazio foi reproduzida como amostra durante a transição; aguardar idle/opacidade1 confirmou conteúdo completo, sem nova alteração de produção.

Produção desta iteração: `cliente/terminal_2/apresentacao_desktop.py`, `interface_web_v1.py`, `web_v1/interface.js`, `desktop.css` e orientação de posição em `paginas.js`. Nenhuma alteração de cognição, captura ou permissões operacionais foi necessária. Alterações paralelas em corpo/cognição preservadas. Bancadas usam INI isolado, sem regravar preferências pessoais. Nenhum commit/push/shutdown nesta iteração.
