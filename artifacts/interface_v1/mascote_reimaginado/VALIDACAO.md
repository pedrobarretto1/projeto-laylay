# Mascote reimaginado — referência de Pedro, 20/10/2026

Pedido: substituir o avatar do Início e da Conversa pelo personagem da prancha `referencia.png`, o mais fiel possível, com expressões e movimento de acordo com as emoções reais. O componente compartilhado também atende Painel e Ilha. Baseline HEAD `b128f4e`; a worktree já continha todo o refinamento oficial validado anteriormente. Esse trabalho e a atualização paralela do hotspot foram preservados, sem reset/restauração/commit automático.

## Contratos e fronteiras

O desenho deve preservar a identidade do personagem (corpo quadrado orgânico lilás, mecha, marca losangular e ponto, olhos escuros brilhantes, blush e luz/sombra). Um componente por camadas deve mudar pose/expressão sem substituir os nós, perder gaze/piscada ou reanimar em cada heartbeat. Movimento reduzido mantém a emoção estática. Não gerar emoções mentais pelo texto, mouse, ação ou animação; não criar TTL no navegador.

Estudo demonstrou duas fronteiras distintas:

1. `_estado_terminal_2` lia `current_emotion/is_speaking` brutos, enquanto o overlay já usa `_estado_visual_laylay`/`construir_estado_visual`, com validade do episódio e retrato da fala entregue. O contrato canônico já existe (RPV19/RPV21); a integração deve reutilizá-lo.
2. O frontend recebe `emotion/emotion_level`, mas descarta o nível e seu `avatar()` só distingue atividades ouvindo/pensando. Portanto a emoção não chega à aparência, embora o transporte funcione.

Falsificadas por código: ausência de emoção no canal, necessidade de quatro renderizadores e necessidade de um novo mecanismo mental de emoções. Só a apresentação e seu getter de composição precisam integrar os owners existentes.

## RED antes de candidato

- Dois testes QtWebEngine/socket/QWebChannel: emoção alegre chega ao estado, mas expressão feliz não aparece; nível3 não chega ao avatar. **2 failed em11,20s**. Não foram falhas de import/conexão.
- Testes executam os próprios nós de composição de `laylay.py` com `EstadoCompartilhadoRuntime`, `construir_estado_visual` e reader de entrega reais, sem importar/iniciar o processo inteiro. Só ouvido/serviço de hardware têm amostras inertes. Episódio vigente é controle GREEN; expirado, inexistente, contido, preparação sem áudio e retrato de áudio entregue divergem do overlay: **5 failed,1passed em1,03s**.

Candidato de composição: o getter do terminal passa a consumir `_estado_visual_laylay` nos quatro campos visuais. Modo, ouvido e nível do microfone permanecem no mesmo owner do terminal. Nenhuma política emocional, executor, firmware ou estado persistente foi alterado.

## Olhar seguindo o mouse — 21/10/2026

O pedido adicional foi validado com entrada de mouse, em vez de atribuir manualmente variáveis CSS. No Chrome da galeria, registro de avatares e `translate` funcionam: hipóteses de ausência geral do listener e de CSS incapaz de mover o rosto foram falsificadas. Não foi possível medir `matchMedia` na aba IAB do usuário, portanto não se atribui a esse navegador uma causa não observada.

No QtWebEngine offscreen, `document.hasFocus()` é verdadeiro, eventos de mouse reais de `QTest.mouseMove` chegam ao renderer, mas a media query de hover/fine é falsa. A primeira barreira indevida é exigir uma inferência de capacidade além do evento `pointerType=mouse`. O teste canônico falhou aguardando deslocamento negativo do olhar (**1 failed em9,97s**). Remover a condição de media query no controlador compartilhado tornou o mesmo teste GREEN (**1 passed em2,86s**), incluindo esquerda/direita/cima/baixo, `translate` computado, identidade do avatar e centralização ao reduzir movimento. Toque/caneta continuam fora do listener; foco, visibilidade e movimento reduzido continuam protegidos. O mouse não muda emoção e não envia comandos.

Desenho e expressões reutilizam o mesmo renderer oficial na galeria. Galeria/fixtures de expressões são demonstração de apresentação e não evidência de emoções ou efeitos reais da mente. O teste de composição com validade emocional e seus regressivos focados ficaram **92 passed em1,57s**; o transporte e a apresentação emocional nos quatro formatos ficaram **3 passed em6,48s**. Regressão ampliada e inspeção nativa serão registradas abaixo.

A própria aba IAB do usuário foi atualizada e testada com entrada de mouse em áreas vazias: o avatar grande recebeu `--look-x=-18.025px/--look-y=-5.430px` à esquerda/acima e `+4.485px/+2.520px` à direita/abaixo. Portanto há prova de resposta nessa galeria, além do Chrome separado e do Qt offscreen.

A primeira execução ampliada terminou com **453 passed e3 failed**. Os dois testes anteriores de feed/burst usavam40/50ms antes de o renderer terminar; passaram a aguardar o conteúdo esperado (mensagem atualizada e200mensagens carregadas), preservando as asserções de identidade e zero renders provocados por observações invisíveis. O módulo completo ficou **18 passed em22,52s**. Isso corrige sincronização da prova; não se alterou produção para mascarar essas falhas.

A hipótese de o primeiro ponto de mouse ser igual à posição anterior foi testada inicializando outro ponto, mas não resolveu a execução conjunta (**455 passed,1failed**). Instrumentação restrita ao teste demonstrou `events=[]`: nenhum pointermove nativo chega ao WebView após os testes Qt anteriores, embora o elemento esteja conectado, com foco, visível e sem movimento reduzido. Isso antecede o controlador JS. A mesma entrada passa em processo limpo, no módulo isolado e na composição Windows nativa. Portanto o teste de mouse passou a executar as mesmas asserções num processo com QApplication própria, sem injetar PointerEvent JavaScript nem relaxar expectativas. Não se atribui essa interferência de infraestrutura ao código de produção.

Princípio reutilizável: observar o evento concreto do dispositivo antes de confiar em uma heurística geral de capacidade. O mesmo controlador atende todos os tamanhos do mascote; não há correção separada por página.

## Qt nativo e avaliação visual

`validar_web.py --movimento --mascote --saida artifacts/interface_v1/mascote_reimaginado/qt_real` passou com QtWebEngine/Windows, arquivos oficiais locais, ponte autenticada e telemetria psutil. Mouse nativo deslocou o rosto nos dois eixos (x±8,925px; y±5,328px), com25capturas, continuidade de identidade DOM/animação, expressões feliz/triste/brava/surpresa transportadas e inspeção de todas as abas, Painel425×720 e Ilha330×86. Artefato `qt_real/resultado_web.json`. Não foi iniciado o processo completo da mente nem executores de música/IoT; as emoções nessa composição são amostras de demonstração.

A avaliação independente recebeu **PASS** na primeira rodada: referência,9expressões, quatro formatos oficiais e responsividade375/768/1440px. Além de blink/reduced,374amostras do gaze mostraram72frames em movimento e maior passo de1,368px. Relatório `eval_mascote_1.md`; imagens desktop/mobile salvas neste diretório.

Produção alterada nesta substituição: `cliente/terminal_2/web_v1/interface.js`, novo `mascote.css`, link no `index.html` e o getter visual de `laylay.py`. O refinamento anterior foi preservado; alterações paralelas de corpo/cognição/documentação não pertencem a este trabalho. Nenhum commit, push ou shutdown criado nesta entrega.

## Resultado final

Regressão ampliada: **456 passed em98,81s**, incluindo terminal, transporte, saída de áudio musical e validade/persistência da personalidade. JUnit em `regressivos.xml`. Teste de mouse usa QApplication isolada com QTest nativo e asserções preservadas; a prova Windows real e a aba IAB também foram validadas separadamente. Sintaxe JS/Python e diff check passaram. O limite continua explícito: não houve inicialização nem conversa de validação com a mente completa, e nenhuma emoção de demonstração é alegada como estado mental observado.
