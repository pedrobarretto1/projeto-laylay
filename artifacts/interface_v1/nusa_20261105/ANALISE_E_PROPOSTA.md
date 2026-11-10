# Nusa → apresentação da Laylay — 05/11/2026

## Pedido

Pedro pediu analisar `C:\Users\pbarr\Downloads\NusaSetup` e aplicar o visual e
comportamento à Laylay, com foco explícito nas animações e transições.

## Base e escopo

- Laylay: branch `main`, HEAD `ae7b8775daab6637026829e20890a76d983477e4`.
- Worktree já contém alterações paralelas em cognição, corpo e testes.
- Nenhum arquivo de produção foi alterado nesta investigação; nenhum commit criado.
- Extração e ferramentas estão em `C:\Users\pbarr\Downloads\NusaSetup\analise`.

## Evidência confirmada

1. Instalador Inno Setup 6.7.0, Nusa 1.2.0, atribuído a Rama.
2. SHA-256 do instalador:
   `bc4133305b28b929eca42cc32833dc4fd34002ce35676d27761942419f4d4b02`.
   Confere com a release oficial v1.2.0.
3. Conteúdo extraído: `nusa.exe` (1.265.664 bytes) e script do instalador.
   SHA-256 do aplicativo:
   `89426b46cdf06a976df130159551cd45a53f2aa4aac46893f0f93a3f2ea21303`.
4. PE x64 nativo, sem CLR; strings de Rust e imports de Direct2D/DirectWrite.
   Existe uma referência CodeView a `nusa.pdb`, mas o arquivo não está no pacote.
   Extração não equivale a recuperação do fonte original.
5. Repositório oficial `rama2555/nusa`, HEAD público
   `8572b333b0e081eb75f55b080fe0533b0e3c5199`: uma branch (`main`), 27 commits,
   24 árvores distintas verificadas sem truncamento. Só README, HTML do site e
   ícone; a árvore inicial contém apenas README. Tags v1.0.0/v1.1.0/v1.2.0 apontam
   para commits desse histórico. As três releases oferecem instaladores.
6. O site oficial inclui uma demonstração com código de movimento:
   expansão de 620 ms com curva (0.34, 1.32, 0.5, 1), recolhimento de 500 ms com
   curva (0.3, 0, 0.15, 1), conteúdo com escala inicial (0.86, 0.9), fade e
   deslocamento. Esses valores provam a demonstração web, não o motor nativo.
7. NusaLite (`Pidzzzz/nusa-lite`) é outro aplicativo, em C#/WPF, com licença MIT.
   Não é o fonte do executável Rust fornecido por Pedro.
8. A Laylay já separa geometria Qt, confirmação da apresentação pelo renderer e
   animações HTML. O owner está em `cliente/terminal_2/interface_web_v1.py`;
   apresentação em `web_v1/interface.js` e `web_v1/desktop.css`.

## Limite de runtime

O executável extraído iniciou e respondeu como processo `nusa`, janela `Notch`.
As duas APIs de Computer Use não o incluíram entre as janelas controláveis.
Não houve captura nem medição visual das animações nativas. Não declarar
equivalência exata com o Nusa nativo a partir da demonstração do site.

## Adaptação aprovada em 07/11/2026

O caminho proposto é reimplementar a linguagem visual de movimento no renderer
existente, usando o site oficial como referência e mantendo o personagem Laylay.
Copiar o binário não integra as animações ao Qt/HTML; portar NusaLite introduziria
WPF e usaria movimentos de outro aplicativo, sem recuperar o Nusa original.

Mudança focada:

- Expansão e recolhimento com curvas distintas e continuidade quando interrompidos.
- Entrada do conteúdo com fade e escala suave, depois da confirmação da geometria.
- Troca de páginas com deslocamento direcional e fade; mudança de estado de dados
  não deve reiniciar a transição.
- Superfície escura, bordas arredondadas e controles discretos na ilha desktop.
- Reutilizar o owner de geometria, a sequência de transição e a preferência de
  movimento reduzido já existentes. Animação não recebe autoridade operacional.
- Passar o mouse pela cápsula e permanecer brevemente abre o resumo sem ativar
  a janela. Sair do resumo recolhe depois de uma tolerância curta. Interagir
  mantém o painel aberto para navegação e digitação, com os controles já existentes.

Produção alterada em `interface_web_v1.py`, `web_v1/interface.js` e
`web_v1/refino-inteligente.css`. O último arquivo já governa o acabamento
compacto no renderer oficial.

## Resultado na Laylay em 07/11/2026

O Qt usa os prazos existentes de permanência de 200 ms e saída de 750 ms.
O resumo passivo projeta a apresentação sem gravar outra aba selecionada.
A edição ativa protege o painel e o rascunho guardado reaparece ao reabrir.
O retângulo da janela usa curvas de 620 ms para expandir e 500 ms para recolher.
O rebote discreto fica na escala do conteúdo após a confirmação de geometria,
o que permite manter o retângulo dentro da área útil da tela.

Contrato reutilizável. Apresentação temporária é uma projeção local, sem
autoridade de operação e sem sobrescrever a escolha do usuário. Durante uma
transição a região clicável deve corresponder à superfície visível. A cobertura
nativa impede o ponteiro de alcançar os controles enquanto estão encobertos.

- RED inicial. A janela não abria por hover, os dois sentidos usavam 230 ms e a
  entrada HTML usava deslocamento sem escala. A revisão reproduziu ainda os REDs
  de cursor retornando entre amostras, clique na cobertura, aba sobrescrita e
  rascunho passivo impedindo o recolhimento.
- GREEN focado. Seis testes do Qt e renderer passaram, incluindo os casos acima.
- GREEN regressão de interface. 119 testes em 88,85 s nos módulos desktop,
  interface web, ponte web, páginas, estabilidade e desktop bridge. Resultado
  em `regressao-interface.xml`.
- GREEN runtime do cliente. `validar_web.py --desktop-hover --movimento` executou
  na plataforma Windows com bundle local e ponte autenticada. A cápsula abriu
  272 × 54 → 640 × 320 e recolheu para 272 × 54, no mesmo HWND e sem mudar o
  foreground nem enviar uma entrada à mente. O trace registrou 28 posições
  distintas na expansão e 26 no recolhimento. Evidência em
  `qt_windows_final/resultado_hover.json` e capturas no mesmo diretório.
- A prova adicional de foco depois de `QTest.mouseClick` ficou inconclusiva.
  O clique sintético não produziu a troca de foreground esperada. A tentativa
  de observar a janela de teste para um clique real encontrou a janela encoberta.
  A mente, a voz e os executores ficaram fora da prova da interface.

Sintaxe Python e JavaScript e `git diff --check` passaram para o recorte.
HEAD continua `ae7b8775daab6637026829e20890a76d983477e4` em `main`.

## Fontes

- https://github.com/rama2555/nusa
- https://api.github.com/repos/rama2555/nusa/git/trees/main?recursive=1
- https://github.com/rama2555/nusa/releases/tag/v1.2.0
- https://github.com/rama2555/nusa/blob/8572b333b0e081eb75f55b080fe0533b0e3c5199/index.html
- https://github.com/rama2555/nusa/issues/3 (pedido de fonte, sem comentários na consulta)
- https://github.com/Pidzzzz/nusa-lite
