# Integração do refinamento aprovado — 20/10/2026

Pedido: aplicar em todas as nove abas oficiais exatamente o acabamento de `../previa_refinada/`. Baseline `b128f4e48b774352846a40672de493d19c30f109`, branch `main`, worktree limpa antes desta etapa. A prévia aprovada permanece imutável. Esta autorização trata da integração; não inclui um novo desligamento do PC.

## Contrato

A apresentação aprovada deve usar os mesmos controllers/owners/receipts da interface oficial. CSS e navegação podem mudar; o frontend não pode ganhar fatos fictícios, executores próprios ou resultados otimistas. CSP, QWebChannel, capas locais e Streaming independente da IA permanecem nos respectivos owners. O mesmo renderer e tokens visuais atendem às nove abas e aos três formatos.

Estudo por diff/composição confirmou: o entrypoint `cliente/terminal_laylay_2.py:main` instancia `JanelaInterfaceWebV1`, que carrega o bundle local e reutiliza o controlador nativo. Não é necessário mudar a composição nem os executores. A prévia acrescenta dois CSS e reorganiza views existentes. Duas adaptações são obrigatórias na passagem para produção: preservar os pedidos em andamento da Automação e substituir o cenário demonstrativo de Streaming pelo acionamento do player nativo real, com o mesmo acabamento visual.

## Primeiras fronteiras demonstradas antes do candidato

Os contratos de navegação e rolagem foram reproduzidos com renderer QtWebEngine, QWebChannel e transporte autenticado reais antes de alterar produção. O replay foi depois conferido contra o arquivo do commit congelado, em uma cópia temporária, sem restaurar a worktree:

- `test_navegacao_refinada_movel_nomeia_todas_abas_e_fecha_com_escape`: RED porque falta acesso móvel nomeado às nove abas.
- `test_refinamento_preserva_rolagem_entre_abas_e_streaming_real`: RED porque trocar Sistema → Memória → Sistema muda scrollTop de 300 para zero.
- `test_historico_inicial_conserva_cada_publicacao_antes_da_inscricao`: RED porque 30 publicações válidas, uma duplicata e uma stale anteriores à inscrição das páginas produzem zero amostras, em vez de 24.

O último teste usa cópia temporária dos mesmos scripts e apenas insere publicações de validação entre o core e a inscrição das páginas. Não substitui o componente de replay, renderer ou transporte. A divergência é `evento publicado → sampleDashboard`: a oficial lê o estado final compartilhado em cada replay; como a última publicação é stale, descarta todas as anteriores. Com a última fresh, o mecanismo também pode colapsar o histórico em uma amostra. Isso falsifica tanto ausência de publicações quanto defeito do desenho SVG como explicação primária. A correção é consumir o payload de cada publicação, preservando os filtros de freshness/duplicata e a janela de 24 posições.

Resultado da primeira rodada: **3 failed, 7 deselected em 7,37 s**. As duas falhas de apresentação atingiram as fronteiras esperadas. A primeira montagem do teste de replay apontava ao diretório padrão e não à cópia instrumentada, portanto seu RED inicial não foi aceito como prova. Corrigido o uso do parâmetro existente `diretorio_web` e acrescentada a primeira asserção de que as 30 publicações realmente ocorreram; o mesmo teste então falhou pelo motivo correto com `paginas.js` do commit `b128f4e` (**1 failed, 9 deselected em 2,14 s**) e passou com o candidato (**1 passed em 2,00 s**). A substituição existiu somente na cópia temporária do teste; nenhum arquivo de produção foi restaurado.

O primeiro regressivo também capturou `ReferenceError: categories is not defined` no DEV: a deduplicação de views removeu uma constante usada por `devTerminal`. A constante foi restaurada; não se alterou a expectativa do teste. Duas expectativas antigas exigiam animação de entrada nos balões; a especificação aprovada declara `.message{animation:none}`. Elas foram atualizadas para exigir zero animações antes/depois dos ticks, conservando todas as asserções de identidade, receipt, histórico, foco, cursor e rascunho. A animação do mascote permanece um contrato separado.

Após essas correções, os dez testes das páginas passaram em **19,08 s**.

Os outros três módulos focados de renderer/ponte/estabilidade passaram: **22 passed em 20,00 s**. Total focado: **32 testes verdes**, incluindo paginação musical com owners reais e arquivos temporários, rejeição de envio, correlação de receipts, configuração dirty/in-flight, ausência de frames simulados, continuidade de DOM/rascunho/cursor, navegação móvel e histórico por evento.

## Composição Qt no Windows

`validar_web.py --movimento --saida artifacts/interface_v1/refinamento_oficial/qt_final --inspecionar` concluiu as asserções e gravou `qt_final/resultado_web.json`: renderer local QtWebEngine, ponte autenticada, dashboard real por psutil, uma entrada recebida, resposta transportada e continuidade de identidade DOM/animação do mascote. Capturadas as nove abas, painel/ilha e conversa em 768×800 e 390×844. Esta composição usa perfil de preferências temporário, não inicia a mente e não conecta efeitos externos. Não prova áudio real, atuação IoT ou captura pessoal; esses owners não mudaram nesta integração.

A primeira execução de captura parou na regressão do DEV antes da restauração de `categories`; suas capturas parciais foram preservadas em `qt_real/`. A execução `qt_final/` foi posterior ao ajuste e concluiu todas as asserções.

## Regressão e fidelidade

Primeira regressão completa relevante: todos os arquivos `scripts/tests/test_terminal*.py`, `test_desktop_bridge.py` e `test_saida_audio_terminal_musica.py`: **359 passed em 89,42 s**; relatório em `regressivos.xml`. Inclui prova de que o CTA refinado de Streaming instancia `PaginaStreaming` real e abre/fecha o diálogo nativo sem emitir `enviar_json` para a mente, sem selecionar nem capturar qualquer janela pessoal.

A comparação independente verificou 36 combinações (nove abas nas larguras 1440/1366/768/375), sem overflow horizontal ou controles cortados. Identificou diferença no Painel rápido: o owner Qt ainda fixa 450×700, enquanto a referência usa 425×720; além disso, a largura da janela nativa aciona regras móveis que reduzem fonte e padding mesmo em monitor desktop. Um teste adicional reproduziu a primeira divergência de geometria (**1 failed em 1,86 s**). A correção deve permanecer na apresentação nativa/CSS e respeitar a área realmente disponível; não altera transporte ou execução.

A atualização de PID/horário em `artifacts/rosto_oled/wifi/hotspot_windows.json` surgiu durante esta etapa e foi preservada. Esse arquivo não faz parte do candidato visual nem foi editado manualmente por esta integração; sua autoria não foi inferida a partir do diff.

## Ajuste do Painel nativo

O owner Qt passou a abrir o painel em 425×720, ainda limitado pela área disponível. O mesmo owner publica no evento local de apresentação se a janela é nativa e qual área está disponível; o renderer usa essa informação somente para manter o acabamento desktop do painel quando ele cabe. Não se interpreta a largura compacta de 425 px como se fosse uma tela móvel. Boot e troca de modo reutilizam a mesma projeção de apresentação. Nenhuma configuração pessoal ou decisão operacional passa por esse caminho.

O teste de geometria/fonte/padding passou após o candidato, juntamente com a regressão do histórico: **2 passed em 2,51 s**. A comparação do implementador, em `painel_computados.json`, encontrou igualdade em 31 seletores × 21 propriedades de estilo entre a referência desktop e o painel nativo; inclui Chat/Voz, ícones, composer, título de 22 px e espaçamentos de 23/22 px. O fallback em 320×420 mantém o campo visível e não apresenta overflow horizontal. A avaliação independente final permanece necessária.

Depois do ajuste nativo, a mesma regressão completa relevante passou novamente: **360 passed em 97,69 s**, incluindo o teste adicional do painel. Evidência máquina: `regressivos_finais.xml`. Não se executou a suíte inteira de mente/corpo nesta etapa exclusivamente visual.

O roteiro Qt real foi repetido após esse último ajuste e concluiu novamente todas as asserções. Evidência final: `qt_integrado/resultado_web.json` e respectivas capturas; `web-painel.png` mede 425×720. A composição de inspeção foi encerrada normalmente, com worker, transporte e dashboard finalizados. A prévia aprovada não foi editada.

## Escopo final

Produção: `cliente/terminal_2/web_v1/index.html`, `interface.js`, `paginas.js`, os dois novos CSS `refinamento.css` e `paginas-refinadas.css`, além da apresentação de geometria/metadados locais em `cliente/terminal_2/interface_web_v1.py`. Os arquivos de testes e o roteiro/capturas documentam a integração. Nenhum owner de mente, música, memória, IoT, voz ou Streaming foi substituído. Nenhum commit novo foi criado nesta etapa.

## Encerramento

**PASS na segunda avaliação visual independente.** As nove abas passaram nas quatro larguras e o único bloqueio da primeira rodada (Painel nativo) foi conferido no Qt/CDP após o ajuste: 425×720, título de 22 px, espaçamentos aprovados, microfone e envio de 35 px. O avaliador também repetiu o fallback 320×420 em instância própria: classe desktop desativada, campo visível e ausência de overflow. Relatórios `eval_oficial_1.md` e `eval_oficial_2.md` preservam a avaliação.

Refinamento integrado ao bundle oficial, com **360 regressivos do terminal/ponte verdes**, comparação visual independente aprovada e prova Qt real concluída após a última alteração de produção. A próxima abertura pelo entrypoint existente carregará esse bundle. A aprovação é da apresentação/navegação e da integração com os owners; não inventa comprovação de música audível, atuação física de IoT ou captura pessoal.
