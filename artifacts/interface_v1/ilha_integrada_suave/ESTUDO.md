# Ilha integrada: player, interação e fronteira de pintura

Pedido atual: playerStreaming na mesma janela; hover não abre; melhorar glitches/transições/entrada; recolher após20s sem interação. O refinamento anterior permanece especificação visual.

Base congelada: main, HEADb128f4e48b774352846a40672de493d19c30f109, worktree suja com UI e alterações paralelas de corpo/cognição. Não foi criado commit. Registro geral e mapa causal foram consultados, sem atribuir estes sintomas a roots cognitivas. Evidências anteriores preservadas.

## Fronteiras demonstradas antes do candidato

1. Navegação→abrirplayer: `JanelaInterfaceWebV1.abrir_streaming()` criaQDialog eparentaPaginaStreaming nele. O widget/captura não exigem janela própria. REDQt: `PaginaStreaming.window()!=JanelaInterfaceWebV1`.
2. Observação→abertura: `_observar_cursor_desktop()` inicia timer200ms ao entrar na área compacta; callback expande semclique. REDQt: depois400ms de hover estadoexpanded emvezcompact. Os dois testes falharam pelo motivo correto,2failed em2,03s.
3. Destino→pintura: diagnóstico Windows `diagnosticar_transicao.py baseline` mostra HWNDconstante, mas o DOM permanece264×50 quando janela nativa jácresceu para389×140; depoisDOM363×120 contra517×231. PNG `baseline/resumo-003.png`,517×231, possui pixelinterior(w-15,h-15)RGBA(0,0,0,0); final640×320 essemesmoponto éopaco(11,13,18,255). Portanto parte da superfície nova fica transparente enquantoChromiumpinta o tamanhoantigo. Isso sustenta os glitches de expansão e falsifica a necessidade de outra janela/reload como explicação desse registro.
4. Inicialização→primeira projeção: as amostrasrAF nativas registram modo/classefull com conteúdo aos317–367ms, antes de classe desktop aos433ms. `baseline/startup-12.png` mostra cabeçalhoAbas/Início dentro264×50. A apresentação nativa jáera desktop. É uma divergência de bootstrap/pintura, não uma resposta da mente.
5. Inatividade: não havia timer de20s; os novos contratos de timer/atividade tiveram RED por ausência do owner. Trata-se de melhoria autorizada, não regressão histórica atribuída ao prazo750ms antigo.

## Contratos mínimos

- Owner único de apresentação/atividade: JanelaInterfaceWebV1. Hover atualiza olhar; apenas clique abre. Um timer preciso20000ms é renovado por interação humana dentro da ilha, incluindo widgetsStreaming. Heartbeat, frames, render, cursor parado/fora, resize e animação não renovam. Rascunho/foco/pin não inibem o prazo; IME/modal podem receber uma curta conclusão segura, sem apagar texto.
- Superfície permanente: HWND, WebView, página, canal, controlador eworker conservados. Geometria cancelável deriva do mesmo centro/topo. Snapshot nativo temporário e confirmação deviewport/pintura coordenam conteúdo e moldura; ack antigo não pode concluir transição nova. Reduced-motion aplicaestadofinal sem efeitos.
- Bootstrap: a primeira projeção jádeveconhecer o modo inicial e a ilha sódeveaparecercomconteúdopronto; entrada umaúnicavez, semflashfull.
- Player: PaginaStreamingfilha da mesma janela, emviewportlocal validado, mantendoHTMLnav. Frames continuamQImage→VisorQt, semserializaçãoJS/mente. Ampliarplayer não abreQDialog nessehost. Outrascomposições legadas preservam comportamento explícito anterior. Sair/recolher encerra captura e invalidaframeantigo; fechar encerrafontes/timers.

## Validação planejada

Root mantém testes e scripts de prova; implementação/revisão visual seguem skillfrontend-design. Os testes deCTA que exigiamQDialog serão atualizados porque o usuário alterouexplicitamenteessecontrato, conservando asserçãozeroentradasparaamente. Validar hover/click,20s/renovação/inatividadepassiva, reversão/ackantigo, viewportmalformado, playerembutido, captura válida/encerramento, reduzirmovimento econtinuidadeanteriores.

Prova finalWindows: startupsemfullflash, ausência de buracosalfa nas capturas intermediárias, novecaminhosmesmoHWND, playercomquadrosnativosdistintos de janela própria de teste viafonteWebSocketlocal e capturaQt reais, mais20s reais seminteração/draftpreservado. A janela fonte de teste não equivale a um player real deYouTube; o detector/crop da extensão existente não será alterado semcausa. Não iniciarmente/voz/música/IoT.

## Evidência do primeiro candidato

Diagnóstico Windows `candidato_1/resultado.json`: primeira pintura já em desktop, mesmo HWND e10.519 amostras de alfa interior, todas255. Nenhum vazio transparente nas amostras, frente ao alfa0 reproduzido no baseline. Os PNGs mostram a superfície anterior enquanto o compositor se ajusta; o conteúdo final só é revelado após confirmar tamanho e duas pinturas. Isso não equivale a garantir todos os frames em todas as GPUs.

`qt_real/resultado_web.json`: nove abas conservaram HWND/flags/centro/topo. Hover não abriu nem roubou foco; clique abriu, teclado funcionou, cantos transparentes não interceptaram a janela atrás, rascunho e DOM foram preservados. O helper adicional `validar_ilha_suave.py` usou uma janela própria animada e fonte WebSocket real em porta efêmera, seleção pelo controle real e captura QWindowCapture/QVideoSink. Houve15 quadros distintos no visor integrado, e as duas ampliações permaneceram na mesma janela sem interromper a captura.

O prazo foi medido enquanto o vídeo continuava produzindo quadros e a ponte publicava telemetria: recolhimento em20,048s, captura encerrada no recolhimento e rascunho restaurado ao voltar à conversa. Não houve execução pela mente.

Focados iniciais:69 GREEN. Dois testes históricos precisaram atualizar pressupostos de composição: a apresentação é agora estado mais recente em `_ultimos`, evitando replay de fases antigas, e o CTA de Streaming possui viewport integrado em vez do cartão que lançava um diálogo. O teste continua exigindo publicação real no canal, estado mais recente e zero entradas para a mente. Um teste adicional de ack antigo/dimensão incorreta também ficou GREEN.

## Fronteira estreita descoberta na revisão

Apesar do HTML estreito aprovado, o player nativo numa QScrollArea360×540 produziu largura752 e overflow394: o sizeHint largo impedia o resizeEvent de entrar no breakpoint estreito. O mesmo contrato foi reproduzido em390px. A primeira correção baseada no viewport reduziu o overflow para58/28, mas não passou; esses testes não foram enfraquecidos. O mínimo restante vinha do botão "Atualizar extensão da Laylay". Seu rótulo estreito passou a "Atualizar extensão", conservando ação, tooltip e nome acessível completo. Os dois testes ficaram GREEN, sem esconder controles ou rolagem necessária.

## Resultado final e escopo

- Regressão final: **488 testes GREEN em114,23s**, sem erros, falhas ou skips; relatório `regressivos.xml`. Inclui todos os módulos `test_terminal*.py`, bridge, áudio/música e personalidade/persistência relacionadas.
- Última prova Windows autenticada: `qt_resize_trace/resultado_web.json`. Quinze quadros diferentes, player390px sem overflow horizontal, retorno à largura1000px e duas ampliações mantendo a captura na mesma janela. Recolhimento em **20,033s** com vídeo ao vivo; frames e telemetria não renovaram o prazo, e o rascunho permaneceu disponível.
- As nove abas, clique/hover, foco, cantos transparentes e identidades já foram comprovados em `qt_real/resultado_web.json`. Primeira pintura e transições estão em `candidato_1/resultado.json` e PNGs; nenhuma fase de produção desse mecanismo mudou depois dessa prova.
- Sintaxe Python/JavaScript e `git diff --check` GREEN. Avisos de conversão de quebras de linha do Git não são erros de validação.
- Revisão visual independente: PASS na rodada2, sem prioridade bloqueadora. O player nativo390px, desktop1000px e ampliações foram inspecionados; relatórios `eval_suave_1.md` e `eval_suave_2.md` preservados nesta pasta.

Produção desta iteração: `cliente/terminal_2/interface_web_v1.py`, `cliente/terminal_2/streaming.py`, `cliente/terminal_2/web_v1/interface.js`, `paginas.js`, `desktop.css` e chamada de entrada em `cliente/terminal_laylay_2.py`. Testes e validadores foram atualizados separadamente. A cognição, voz, autorização e executores não foram alterados por esta iteração. Alterações paralelas já existentes foram preservadas. Nenhum commit ou push criado.

### Limites registrados

Uma execução mais longa interrompeu a captura após o resize, antes de a instrumentação estar disponível. A hipótese de retângulo DOM antigo não foi reproduzida nas duas execuções instrumentadas seguintes: todos os viewports foram aceitos e a captura permaneceu ativa. Não foi aplicado patch especulativo, e essa observação não é declarada uma raiz corrigida. Os traces estão em `player_resize_red/trace_viewport.json` e `qt_resize_trace/trace_player.json`.

O Windows também recusou ativação por clique Qt sintético em uma execução. O harness passou a registrar o foco real do aplicativo ativo, e um clique Computer Use na própria janela de teste forneceu entrada física antes das provas subsequentes. Isso não alterou a política de foco da produção.

A captura foi comprovada com janela própria animada e transporte local reais. Não equivale a testar YouTube/DRM ou áudio do navegador nesta rodada. O mecanismo de detecção/crop da extensão foi preservado. Uma demonstração usa somente a UI e a ponte local de teste, sem iniciar a mente; não substitui nem encerra sessões reais do usuário. As mudanças do código são carregadas quando o terminal oficial é reaberto.

Para abrir apenas essa demonstração por15min: `.\.venv314\Scripts\python.exe artifacts/interface_v1/validar_web.py --movimento --demonstracao --saida artifacts/interface_v1/ilha_integrada_suave/demonstracao`. Encerrar pela bandeja ou pelo arquivo local `demonstracao/encerrar` fecha apenas esse validador.
