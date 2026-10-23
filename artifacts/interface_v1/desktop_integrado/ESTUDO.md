# Laylay integrada ao desktop — estudo e validação

Pedido de Pedro: apresentação pequena na borda do Windows que se expande como o Coucou mostrado nas duas imagens, usando seu código como base. HEAD b128f4e48b774352846a40672de493d19c30f109, main; worktree suja com refinamento/mascote e mudanças paralelas de corpo/cognição/documentação, preservadas. Sem reset, commit, push ou shutdown.

## Fontes verificadas

- `C:/Users/pbarr/AppData/Local/Coucou/coucou.exe`: metadados confirmam0.5.0. A instalação contém executáveis, sons e logs; não contém o fonte do aplicativo.
- `C:/Users/pbarr/Downloads/coucou-main/coucou-main`: cópia anterior com NotchBuddy/Swift, sem diretórioWindows. Não representa a versãoWindows instalada.
- Fonte oficial correspondente: https://github.com/Louis-CFM/coucou/tree/windows-v0.5.0/windows — revisão841a81ce1d75b65882b30139e6b716d0837dce30. Arquivos relevantes baixados para pasta temporária de estudo: `src/island/fsm.ts`, `island.ts`, `desktop.ts`, `src-tauri/src/island.rs`, `src-tauri/src/platform/windows.rs`, configuraçãoTauri, CSS e licenças.
- CódigoMIT, copyright2026LouisRaillé. Nome/Mochi/sons/media têm restrições separadas. A adaptação usa mecanismo de apresentação e identidade visual própria da Laylay, com atribuição do código.

## Como o Coucou obtém o comportamento

O Windows utiliza Tauri/Rust/TypeScript, com janela sem bordas, transparente e acima das outras, fora do AltTab. A FSM em `fsm.ts` distingue hidden/petit/home/coucou, cancela timers ao mudar intenção, permite abertura transitória por hover e mantém pendências importantes visíveis. `island.rs` separa faixa240×6 do painel720×320, aplica geometria no monitor escolhido e limita a observação do cursor ao modo ativo. `platform/windows.rs` usa WS_EX_NOACTIVATE/WS_EX_TOOLWINDOW para não capturar foco involuntariamente, liberando ativação quando o usuário quer escrever. Região de input acompanha a forma visível, não o retângulo transparente inteiro.

## Fronteira atual na Laylay

O entrypoint já cria uma JanelaInterfaceWebV1, um WebEngine/QWebChannel, um controlador canônico oculto, um PonteWorker/thread e uma sessão autenticada. Full/quick/island compartilham essa composição. A geometria atual muda abruptamente, sem apresentação desktop, transparênciaQt/máscara, tray ou animação de expansão. Portanto não é necessário outro aplicativo, segunda mente, novo backend nem iframe remoto.

Hipóteses falsificadas por composição: não faltam bridge/estado emocional/receipts; não é preciso reproduzir integraçõesClaude/Coucou; a cópia localMac não fornece implementaçãoWindows. Dono da responsabilidade: apresentação nativa e projeção local da interface, não cognição/executor.

## Contrato adotado

Novo modo `desktop`, com compacto e expandido, preserva full/quick/island e todos os dados. Uma única janela/página/canal/controlador/worker permanece viva. A expansão usa uma animação cancelável partindo da geometria atual; reduzirmovimento aplica destino imediato. Âncora no topo e região de input ficam dentro do monitor disponível, inclusive coordenadas negativas. Hover/cursor/tray/pin são somente apresentação local: não autorizam ação, não publicam emoção mental e não enviam texto à mente.

O painel reutiliza dados reais, composer/pedidos canônicos e o mascote atual. Cursor global chega somente ao controlador visual existente, sem render a cada tick. Nenhum serviço, registrodeinicializaçãoWindows, hook global ou chaveCoucou será instalado. O entrypoint pode iniciar no modo desktop por preferência local; construtor mantém compatibilidadefull.

## RED antes de produção

`scripts/tests/test_terminal_desktop_integrado.py`: **2failed em1,63s**. Com controladorQt/ponte existentes, `apresentar('desktop')` deixa o modo emfull. A falha está na ausência desse contrato de apresentação; não em import, rede ou criação de pedido. Segundo teste cria um pedido pendente pelo controlador atual antes de alcançar a mesma fronteiraRED.

## Implementação e provas focadas

Novo `apresentacao_desktop.py` adapta geometria e ativação; `interface_web_v1.py` permanece owner da janela, timers, animação e bandeja. O renderer oficial usa `desktop.css` e a mesma projeção emocional/composer/canal. `terminal_laylay_2.main()` consulta a preferência local `v1/iniciar_no_desktop`, inicialmente verdadeira, sem instalar autostartWindows. Código MIT atribuído em `licencas/Coucou-MIT.txt` e no arquivo de licenças já distribuído pelo empacotamento. Nenhum asset Mochi/som foi copiado.

**10 testes focados passaram em10,66s**, incluindo controlador existente, geometria em monitor negativo/tela estreita, reversão da mesma animação, reduced-motion, identidade dos objetos, rascunho e resposta recebida enquanto recolhida, envio explícito por formulário/socket e recusa sem conexão. Gestos desconhecidos e pin/edição não viram comandos. Entrypoint real foi executado em subprocessos com QApplication e ponteSocket reais, preferênciastrue/false e fechamento do ciclo, sem iniciar a mente.

A validação do entrypoint revelou uma segunda fronteira do mesmo ciclo de apresentação: com Qt.Tool, `janela.close()` não provocava saída automática do eventloop, embora full fosse controleGREEN (**1failed,1passed em12,35s**). Owner do encerramento é o entrypoint, por isso a janela agora emite `encerrada` uma vez após liberar recursos, e main conecta o sinal a `app.quit`. Não foi colocado quit global na classe de UI; as fixtures continuam reutilizando QApplication. O teste exige saída real, sem um quit artificial no callback de inspeção.

## Prova no Windows

`validar_web.py --movimento --desktop --saida artifacts/interface_v1/desktop_integrado/qt_real` passou na plataformaWindows com bundle local, ponte autenticada e psutil real. Artefato: `qt_real/resultado_web.json`.

- Ilha264×50→painel640×320,24amostras de geometria com múltiplos estados intermediários, sem nova página/canal/controlador.
- `GetForegroundWindow` confirmou que hover manteve o foco na janela auxiliar em uso.
- `WindowFromPoint`/`GetAncestor` no canto arredondado retornaram uma janela diferente: o retângulo transparente não intercepta aquele ponto. Isso prova o hit-test, sem executar cliques em aplicativos do usuário.
- Clique explícito no campo e QTest.keyClicks ativaram a interface e produziram rascunho através dos eventos reais do WebEngine. O rascunho sobreviveu ao recolher/reabrir.
- Mascote visível animou sem foco; reduzirmovimento aplicou destino imediato. Compacto e expandido possuem elementos permanentes separados: o mascote compacto oculto não é usado como prova da animação do expandido.
- Foram capturadas também as nove abas e modos anteriores, com continuidade de identidade DOM/animação na interface completa.

A bancada auxiliar do teste restaura explicitamente o foco na janela completa ao terminar; isso não altera produção. Estado de edição e emoções nessa composição são amostras de apresentação. **Mente completa, síntese de voz e executores externos não foram iniciados.**

## Avaliação visual

Rodada1 aprovou a direção e apontou sobreposição do play musical em larguras≤500px e contraste baixo do rodapé. Correção localizada no CSS separou o play em linha própria e elevou o rodapé a10px/contraste6,52:1. Rodada2: **PASS sem prioridades pendentes**, inspecionando640/390/375/320px e264×50. Relatórios `eval_desktop_1.md`/`eval_desktop_2.md`; capturas finais no mesmo diretório.

## Escopo e limite

Produção desta melhoria: helper/owner nativo, projeçãoJS/CSSdesktop/linkHTML, preferência nas Configurações, entrada do cliente e atribuições de licença. Preservados os refinamentos e o mascote anteriores e as alterações paralelas de corpo/cognição/memória. Nenhum commit, push, shutdown, serviço ou inicialização automática do Windows aplicado.

Princípio reutilizável: apresentação possui ciclo de vida e autoridade próprios; abrir/fechar/hover não executam comandos e não confirmam efeitos da mente. Um owner controla janela/recursos, o entrypoint controla a vida da aplicação, e pedidos continuam passando pelo transporte e receipts canônicos.

## Resultado final

Regressão ampliada: **466passed em112,76s**, incluindo os10novos casos e regressivos de terminal, bridge, áudio musical e validade/persistência emocional. JUnit em `regressivos.xml`. Sintaxe JS/Python e diff check passaram. Avaliação visualPASS na segunda rodada e validação nativaWindows separada, com foco, inputregion, animação, teclado e continuidade. O mesmo validador oferece `--inspecionar` para demonstração nativa temporária, claramente sem iniciar a mente completa.
