# Aba Streaming local — evidência de 09/10/2026

Base: `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, branch `main`.
As alterações anteriores de planos, registro causal e sondas foram preservadas.

Contrato: clique explícito escolhe um vídeo; geometria DOM recente identifica
o conteúdo; limites nativos do Windows descontam bordas invisíveis; somente
o recorte confirmado chega ao visor. Não há fallback para janela inteira e
não há comunicação com a IA.

Provas com a composição real `JanelaLaylay`, Qt/Windows e Chrome for Testing:

- MP4 em `<video>`: 374 imagens distintas na prova final, visor de 800 × 449 pixels; sem barra
  do navegador ou página. Janela flutuante, tela cheia, parada e saída passaram.
- Alterar largura do player de 800 para 480 pixels e deslocá-lo 60 pixels:
  enquadramento acompanhou sem seleção ou ajuste manual.
- Vídeo num iframe de outra origem (`127.0.0.1` / `localhost`): 275 imagens
  distintas; recorte de 800 × 449 pixels; página hospedeira excluída.
- Fechar o navegador: origem removida pelo canal local, captura encerrada,
  visor limpo e falha observável. A primeira versão da sonda esperava o erro
  nativo de captura, mas a descoberta da fonte encerra a sessão antes dele;
  a asserção foi ajustada para verificar essa primeira fronteira real.
- Em todas essas provas: zero mensagens no transporte para a mente.

Contratos focados: 13 testes passaram, incluindo geometria ausente/expirada,
origem inválida, callbacks de sessão anterior, compensação de zoom/DPI/bordas,
canal WebSocket real que rejeita origens de páginas web e aceita extensões,
proporção visual, ciclo de vida e composição da aba sem conexão com a mente.
Regressão final de todos os módulos `test_terminal*`: **256 passed**, em 40,35 s.

As primeiras provas da versão manual revelaram dois limites que foram
corrigidos antes da entrega automática: igualdade de wrappers de janelas não
é identidade nativa no PySide6 instalado; bordas invisíveis do Windows não
pertencem ao frame Qt. A implementação usa validade nativa e limites DWM.

Instalação da extensão no perfil habitual do usuário ainda é necessária.
O teste usou um perfil isolado, encerrado depois da validação. Não foi feito
build de executável nem commit. DRM, players sem HTML5 e efeitos de perspectiva
não possuem prova de compatibilidade; menus do próprio player podem aparecer.

## Correção do log do Terminal conectado

O log enviado depois da entrega reproduziu `AttributeError` em
`_aplicar_dashboard_pagina`: a página Streaming já estava materializada, mas
o despachante assumia que toda página recebia o dashboard da mente.
A mesma suposição existia em `estado_conexao(False)`, ao chamar `invalidar`.
O carregamento adiado já verificava esses contratos opcionais corretamente;
portanto, o owner da correção é o despacho compartilhado do Terminal.

Contrato geral: uma página registrada não é automaticamente consumidora do
dashboard nem do ciclo de conexão da mente. Cada callback só é chamado quando
o componente o implementa. Falhas dentro de callbacks existentes continuam
visíveis. Não foram adicionados métodos vazios ao Streaming nem exceções pelo
nome da aba.

- RED antes do patch: quatro casos falharam na fronteira correta, incluindo
  dois dashboards válidos, desconexão e outra página Qt independente.
- GREEN focado: 47 testes de Streaming, fluidez, interface e Desenvolvedor.
- Regressão relevante: `pytest scripts/tests -q -k test_terminal` terminou
  com **275 passed, 1 skipped**, em 46,39 s.
- Integração TCP/Qt real: `DesktopBridgeRuntime` → `PonteWorker` em `QThread`
  → `JanelaLaylay`, com snapshot autenticado, dois dashboards periódicos e
  desconexão. Estado local e geração da captura preservados, nenhuma exceção
  de slot e nenhuma entrada de conversa enviada. Passou também com a
  plataforma Qt nativa `windows`, em 2,31 s.
- A primeira tentativa dessa integração usou uma métrica sem `observed_at`;
  a sanitização canônica corretamente tornou seu valor indisponível. A fonte
  do teste foi corrigida para fornecer observação datada, sem mudar produção.

A prova anterior do player usava transporte sem mente e não exercitava o
dashboard conectado; esse limite da validação permitiu a regressão inicial.
A prova nova cobre os componentes reais da ponte e da interface. Não inicia
os demais runtimes da assistente nem substitui a sessão já aberta do usuário.
É necessário reiniciar a Laylay para carregar o patch nessa sessão.

Produção alterada nesta correção: somente `cliente/terminal_laylay_2.py`.
Regressões adicionadas em `scripts/tests/test_terminal_streaming.py`.
Nenhum commit ou build criado; mudanças paralelas preservadas.

## Streaming na extensão existente — Brave

O usuário relatou lista vazia e espera indefinida pela extensão, e pediu usar
a extensão Laylay já instalada. A leitura da sessão confirmou servidor local
na porta 19769, extensão separada instalada e ausência de conexão TCP; isso
não identifica sozinho por que o service worker separado não se conectou.
O inventário confirmou que a extensão existente não incluía o detector.

Contrato de composição: a instalação é compartilhada, mas o módulo de
streaming tem transporte e ciclo de descoberta próprios. `background.js`
importa `streaming_background.js` e recusa explicitamente o envelope de
streaming no handler da IA. O manifest 2.9 inclui `streaming_detector.js` em
todos os frames. O detector também é injetado em páginas já abertas quando o
canal conecta; a identidade é protegida contra timers duplicados.

O handshake independe da descoberta de vídeos. O Terminal distingue extensão
conectada sem vídeo de extensão ausente; após seis segundos informa a ação
necessária para atualizar a extensão, sem continuar uma espera indefinida.
A pasta `cliente/streaming_extensao` foi substituída pelos módulos da extensão
existente; a instalação antiga separada deve ser desativada pelo usuário.

Na prova com Brave, a captura chegou, mas o cálculo rejeitou o enquadramento:
o frame era 1251 × 1005, enquanto a página informava medidas externas
1250 × 926. A hipótese de problema exclusivo da automação foi examinada com
outra instância nativa; a página também informou medidas externas próximas
das internas. A documentação primária do Brave descreve a alteração dessas
APIs por suas proteções de fingerprinting:
https://github.com/brave/brave-browser/issues/23170

A fronteira corrigida foi a origem dos limites externos: a extensão agora
usa `chrome.windows.get`, enquanto o DOM continua fornecendo a região do
vídeo. Um RED em Node executando o módulo real reproduziu a escolha indevida
das medidas da página. Nenhuma configuração de privacidade foi desativada.

Prova final com Qt/Windows, Brave e extensão completa em perfil isolado:

- conexão antes de haver vídeo, com diagnóstico visível;
- limites externos 1265 × 1012, frame nativo 1251 × 1005 e margens DWM
  7/0/7/7; visor de vídeo 800 × 449, conferido visualmente;
- 13 quadros distintos; sem página ou barras do navegador no visor;
- recarregar a extensão e voltar à página já aberta restaurou a descoberta e
  a imagem sem recarregar essa página;
- zero envelopes de streaming no coletor TCP que substituiu apenas o
  destino da IA; zero mensagens da interface para a mente;
- captura, servidor e navegador de prova encerrados.

Para preservar a sessão aberta do usuário, a cópia da extensão de prova usou
19770 para streaming e 19771 para o coletor da IA. A produção permanece em
19769 e a comunicação existente da IA em 8080. A interface e os componentes
Qt eram os mesmos de produção. A captura final está em `integrada_brave.png`.
O primeiro perfil de teste exigiu ativar modo de desenvolvedor para permitir
recarregar uma extensão descompactada; foi uma condição do perfil isolado.

Raiz adicional de encerramento, mantida separada: desconexões de sockets Qt
durante a destruição do componente invocavam closures com o emissor já
destruído. O erro `Signal source has been deleted` foi reproduzido com sockets
Qt reais antes do patch. `encerrar` agora remove os callbacks antes de fechar
e destruir os sockets. A prova final não produziu essa exceção.

GREEN focado: **23 passed**, incluindo prazo real de conexão, handshake sem
vídeo, geometria externa e destruição do canal. Regressão de Terminal,
extensão, Chrome e composição Chrome: **363 passed, 1 skipped, 2 subtests
passed**, em 46,77 s. A única falha intermediária da regressão era o teste de
fila musical exigir literalmente manifest 2.8; a expectativa foi atualizada
para 2.9, mantendo as asserções de transporte e receipt.

Escopo desta rodada: módulos de Streaming, manifest/background da extensão
existente, testes e evidências acima. Os arquivos de planos, sondas e registro
causal em alteração paralela foram preservados. Nenhum commit ou build.
Na sessão habitual ainda é necessário recarregar a extensão existente,
desativar a antiga separada e reiniciar o Terminal para carregar os módulos.

## Vídeo ausente no YouTube — overflow propagado ao viewport

Relato posterior: o vídeo do YouTube não aparecia na lista. O servidor da
sessão habitual tinha conexão estabelecida. Uma prova no YouTube real, com
Brave e a extensão integrada em perfil isolado, reproduziu o RED: **38
snapshots, extensão conectada, zero vídeos**, enquanto o elemento `<video>`
estava reproduzindo, `readyState=4`, com dimensões 854 × 480.

A primeira fronteira incorreta era `localVideos`, antes do transporte e da
captura nativa. O detector aplicava o overflow do `body` como recorte da sua
caixa DOM de altura zero. Na página observada, o `body` tinha `overflow: auto
scroll`, o HTML tinha overflow `visible` e ambos tinham `contain: none`.
Esse overflow é propagado ao viewport; a caixa de altura zero não representa
um contêiner que oculta o player. Referência primária da regra CSS:
https://www.w3.org/TR/css-overflow-3/#overflow-propagation

Falsificações: a conexão estava autenticada e entregava snapshots; o player
HTML5 tinha metadados e área visível, descartando falta de elemento ou mídia
ainda não carregada. Antes de iniciar a reprodução, o próprio YouTube
posicionava o vídeo fora da área do player; a prova causal foi feita depois
do clique em Reproduzir, quando ele voltou a x=16/y=68.

Contrato corrigido somente em `extençao_google/streaming_detector.js`: os
recortes da raiz e do body cujo overflow foi propagado pertencem ao viewport,
já limitado pelo detector. Contêineres normais continuam recortando; body
com overflow próprio ou containment continua sujeito ao seu recorte. Não há
exceção por hostname, ID ou classe do YouTube, nem fallback para tela inteira.

RED canônico em Node executando o detector real: **1 failed, 4 passed**.
Controles: body com overflow próprio, containment, contêiner de altura zero
e vídeo fora do viewport. Depois do patch: **28 testes focados passaram**.
Regressão de Terminal, Chrome, extensão e composição Chrome: **369 passed,
1 skipped, 2 subtests passed**, em 48,25 s.

GREEN no YouTube real: um vídeo descoberto em 33 snapshots, exibido no
`JanelaLaylay` nativo com **12 quadros distintos**, visor **850 × 478** e
zero mensagens da interface para a mente. A imagem `youtube_brave.png` foi
conferida visualmente e contém só a região do vídeo. Conteúdo de prova:
`Big Buck Bunny 60fps 4K - Official Blender Foundation Short Film`, da
Blender Foundation, no YouTube. A prova usa as portas isoladas já descritas.
Uma tentativa intermediária estava na página inicial do YouTube após o
recarregamento da extensão; a prova válida voltou ao vídeo e confirmou sua
reprodução antes de avaliar a descoberta.

A validação anterior cobria MP4 local e não provava compatibilidade com o
layout do YouTube. Esta rodada corrige e comprova esse layout observado,
sem afirmar compatibilidade universal com todo player ou conteúdo protegido.
O perfil/navegador de prova foi encerrado. Na sessão habitual, recarregue a
extensão Laylay existente e depois a página do YouTube para substituir o
detector já carregado. Nenhum outro arquivo de produção foi alterado nesta
rodada; nenhum commit ou build foi criado.
