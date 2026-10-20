# Estudo de refinamento da interface Laylay

Data: 20/10/2026. Escopo: estudo das nove abas, painel rápido e ilha. Nenhuma alteração de produção ou aplicação das propostas.

## Direção

A identidade aprovada já está presente: fundo grafite, violeta/ciano, formas arredondadas, mascote expressivo e uma composição tranquila no Início e na Conversa. O refinamento deve aproximar todas as abas desse mesmo nível de cuidado.

Recomendação: melhorar leitura, hierarquia, consistência e continuidade de navegação. A suavidade deve vir de resposta imediata, conteúdo estável e movimento discreto. Os ajustes propostos preservam as remoções já pedidas: nenhuma coluna lateral de audição/rotinas/RGB na Música e nenhum retorno dos seis cartões de métricas no DevConsole.

## Base e evidência

- HEAD `ca592a9609dd1865b63b22c714f8d3e802fa2a5c`, branch `main`, worktree com a V1 ainda não commitada e outras alterações paralelas. Tudo preservado.
- Fontes estudadas: `cliente/terminal_2/web_v1/index.html`, `interface.js`, `paginas.js`, `interface_web_v1.py` e o registro `artifacts/interface_v1/VALIDACAO.md`.
- Capturas Windows da composição real em `artifacts/interface_v1/web-*.png`: nove abas, playlist preenchida, conversa, painel e ilha. São capturas de validação com transporte autenticado, sem iniciar a mente; algumas telas estão vazias ou com fontes indisponíveis.
- Conferência independente de código e capturas por um segundo agente, somente leitura.
- Navegação do bundle atual em uma sessão isolada do navegador, em 1440×900, 1366×768, 768×800 e 375×812. Todas as nove abas foram percorridas até o fim do conteúdo. Nenhum pedido operacional alcançou a Laylay.
- Medidas iniciais sem ponte em `medidas_*.json`. O teste de mensagem longa, tema ciano e retorno de aba usou uma fixture visual declarada, registrada em `continuidade_1366.json`.

As medidas verificam a apresentação do bundle, e as capturas Windows ajudam a conferir a aparência nativa. Elas não substituem a observação da sessão pessoal preenchida, escala de 125% do Windows, reprodução externa ou todos os dispositivos possíveis. Não foi executada novamente a suíte de produção, pois esta etapa não modifica código.

Hashes dos fontes estudados:

| Arquivo | SHA256 |
| --- | --- |
| index.html | 3c05aaa260340fa432c9ba686cdcb499ec02b19f3b9daafdd630a105a842ba44 |
| interface.js | 1eed9234ee69fcd93537a55d19dc783ec59ac50dfe048968aa0978adb6fa136e |
| paginas.js | ec31d38a00517ce371e46917c27a010081318e12affc329d581073b0274c870a |

## Achados transversais

### 1. Escala de leitura pequena para a área disponível — prioridade alta

Fato: as abas usam frequentemente texto de 10–12 px; no DevConsole há controles de 9–10 px. Na amostra inicial em 1366×768, 116 de 147 elementos de texto simples do Sistema e 69 de 73 do DevConsole ficaram abaixo de 12 px. A contagem inclui metadados, filtros e gráficos, portanto não significa que todo conteúdo principal tenha esse tamanho.

Na conversa com texto longo, o balão mediu cerca de 950 px de largura com fonte de 12 px e entrelinha de 21,6 px. A linha longa obriga o olhar a percorrer uma distância grande.

Proposta inicial para validar visualmente: conteúdo de 14 px, apoio de 12 px e títulos de seção de 15–16 px; terminal em mono de 12 px, com densidade própria. Na conversa, testar largura máxima em torno de 68–76 caracteres, sem centralizar balões curtos ou alterar seu alinhamento. Esses valores são uma direção proposta, não uma exigência aplicada.

Benefício esperado: leitura mais confortável e melhor distinção entre conteúdo, contexto e metadados. Risco: aumentar a fonte sem reorganizar as linhas pode criar quebras e scroll excessivo; validar o conjunto em vez de aplicar um zoom geral.

### 2. Muitas molduras e níveis de atenção semelhantes — prioridade alta

Fato: `empty()` reutiliza a mesma caixa tracejada com padding de 28×18 px, inclusive dentro de cards já delimitados. Vários blocos de estado e conteúdo recebem o mesmo fundo, borda e espaçamento. A Memória começa por saúde/contagem; a Automação por contadores; detalhes técnicos competem com a atividade principal.

Avaliação estética: essa repetição dá mais peso aos contêineres do que ao conteúdo. As telas podem ficar simultaneamente extensas e pouco informativas quando faltam dados.

Proposta: distinguir região principal, apoio e detalhe; usar estados vazios compactos dentro de seções existentes; reservar bordas fortes para seleção, foco ou ação importante. Manter toda informação necessária acessível. Ausência de dados continua sendo ausência, nunca preenchida com zeros ou resultados presumidos.

### 3. Os componentes precisam de regras visuais compartilhadas — prioridade alta

Fato: convivem componentes do shell e `.tp-*`, três blocos de CSS e vários ajustes posteriores. Botões de play, primários, secundários, filtros, avisos e diálogos recebem regras diferentes. Existem dois construtores de diálogo, um no core e outro em páginas.

Fato medido: ao selecionar o destaque ciano na fixture, `--accent` mudou para `#7fd2e4`, mas a navegação ativa e o botão Salvar conservaram tratamentos violetas. É uma inconsistência reproduzida de tema.

Proposta: estabelecer poucos papéis para texto, superfície, borda, estado e ação; fazer componentes equivalentes usarem os mesmos papéis. Normalizar hover, foco, desabilitado e aguardando confirmação. Dar aos dois diálogos a mesma aparência e ordem dos botões, preservando suas validações.

O inventário encontrou 422 cores hexadecimais literais distintas contando transparências e estilos herdados. Esse número não equivale a 422 cores visíveis nem demonstra, sozinho, um defeito de performance. Serve apenas para localizar decisões de estilo dispersas.

### 4. Continuidade ao mudar de aba — prioridade média

Fato medido: Sistema com scroll em 500 px → Memória → Sistema voltou a 0. O renderer conserva a apresentação durante atualizações da mesma aba, mas remonta o conteúdo em uma navegação explícita.

Proposta: guardar localmente a posição por aba e subpágina, restaurar depois da montagem e manter foco previsível ao usar teclado. Preservar a distinção entre posição de leitura e rolagem automática de novas mensagens/logs.

Movimento proposto: feedback de hover/pressionar em torno de 120–180 ms e, se a avaliação justificar, entrada discreta da região nova em 160–220 ms. O clique produz efeito imediatamente; a animação acompanha a mudança sem atrasá-la. Não animar cada tick de telemetria, não interpolar medições históricas e não inserir outro controlador de roda do mouse.

### 5. Legibilidade dos controles compactos — prioridade média

Fato: na página inicial do DevConsole há 19 controles com uma dimensão abaixo de 32 px; a contagem inclui os filtros compactos. O play por faixa tem 29×29 px. Isso não é uma auditoria formal de acessibilidade, mas indica áreas para avaliar conforto de mouse e toque.

Proposta: revisar área clicável e espaçamento sem tornar todos os botões visualmente grandes. Validar foco, rótulo, tooltip e razão da indisponibilidade. Ação indisponível continua bloqueada; a interface pode explicar o motivo com clareza.

## Estudo de cada aba

| Aba | O que preservar | Refinamento proposto | Como verificar |
| --- | --- | --- | --- |
| **Início** | Hero com mascote, navegação, trilha e lembrança como acessos rápidos. | Ajustar o equilíbrio entre texto, mascote e agenda; reduzir a aparência abandonada da agenda vazia; aumentar o apoio textual e deixar o composer mais convidativo. | Comparar agenda vazia e preenchida, nomes longos e janela baixa. Mascote, olhos e botão play mantêm identidade e relógio de animação durante ticks. |
| **Conversa** | Balões, composer fixo, ordem de mensagens e contraste entre usuário/Laylay. | Melhorar tamanho do texto e largura de leitura, agrupamento de mensagens consecutivas e discrição do estado final de entrega. Falhas e pedidos pendentes continuam evidentes. | Textos curtos/longos, nova mensagem, falha, retry, histórico grande, cursor e seleção preservados. |
| **Automação** | Dispositivos, estado confirmado, controles reais, rotinas e contexto de apoio. | Fazer dispositivos e suas ações liderarem; contadores mais discretos; alinhar controles e estados; vazios compactos. | Fonte ausente, um/vários dispositivos, nomes extensos, ação ocupada, falha parcial. Nenhum estado presumido de ligado/desligado. |
| **Música** | Largura total, play explícito, faixa atual, player inferior, medidor observado e volume único. | Organizar player e biblioteca como protagonistas; agrupar busca e Buscar; manter Adicionar URL junto das ferramentas; reduzir peso visual de contexto/saída/letra. | Playlist preenchida, faixa pausada/ativa, nomes/canais longos, 125 faixas, busca e paginação, medidor ausente/atual e movimento reduzido. Não reintroduzir a coluna removida. |
| **Streaming** | Player local separado da IA e controles nativos reais. | Reduzir a arte vazia e colocar Abrir player na primeira dobra; dizer claramente que abre uma janela própria. | Em 1366×768 o botão atual ficou em y=848, fora da janela de 768 px. A proposta deve deixá-lo visível e coerente com o comportamento real; sem iniciar captura neste estudo. |
| **Memória** | Busca, filtros, lembranças, origem e indicação honesta de disponibilidade. | Dar prioridade à busca e às lembranças; saúde do serviço em faixa menor; filtros com contagens leves; separar vazio inicial de nenhum resultado de busca. | Sem dados, memórias preenchidas, busca sem resultado, origem longa e serviço indisponível. A contagem continua restrita ao que foi publicado. |
| **Sistema** | Hardware, seis gráficos de 24 posições, frescor, dados ausentes e estado dos módulos. | Organizar em estado atual → tendências → detalhes; metadados menores em importância, corpo maior em leitura; usar seções de detalhe para reduzir repetição. | A amostra inicial tem ~2494 px de conteúdo em 687 px úteis. Preservar todos os dados e a escala fixa dos gráficos; não fabricar valores ou consumo por módulo. |
| **DevConsole** | Aparência de terminal, fonte mono, alinhamento dos logs, prompt, filtros, saídas e limites do buffer. | Aumentar leitura dos logs, aliviar o peso dos filtros, aproveitar melhor a altura útil e diferenciar comando digitado, saída e estado. | Mensagens longas, níveis success/warning/error, fluxo contínuo, pause/live, scroll manual e seleção. Nenhum retorno dos seis cartões removidos. |
| **Configurações** | Modelo, voz, perfil, interface, segredo transitório e confirmação de salvamento/reinício. | Criar navegação visual clara entre grupos; campos com largura adequada; explicações mais curtas; retorno do salvamento junto da ação. | Em 1366×768, Voz começa em y=705, Perfil em 937 e Interface em 1076. Testar navegação entre grupos, edição não salva, leitura assíncrona, sucesso e falha, sem perder valores. |

## Painel rápido e ilha

O painel já concentra as funções certas: presença, conversa, player e composer. Refinar apoio textual e áreas de clique; preservar composer/player ancorados e reduzir competição do texto repetido de conexão. Não transferir todos os painéis da janela completa para esse formato.

A ilha deve continuar curta: rosto, nome, estado e abertura do painel. O estudo recomenda manter o desenho, conferir alvos e foco e suavizar somente a passagem entre apresentações, preservando a sessão e o rascunho. Não adicionar métricas ou música detalhada à ilha.

## Sequência proposta para uma futura aplicação

1. **Base compartilhada:** escala de leitura, espaçamentos, superfícies, bordas, foco, botões, diálogos e tema ciano/violeta coerente. Validar inicialmente Início/Conversa e uma página técnica, pois elas expõem os dois estilos atuais.
2. **Hierarquia por aba:** aplicar o mapa acima a todas as nove abas, priorizando Streaming, Música, Memória e Configurações pela descoberta da ação/conteúdo. Conservar os dados e controles do Sistema/Automação e a aparência terminal do DEV.
3. **Continuidade e movimento:** memória local de scroll/subpágina, feedback imediato e transições discretas. Medir antes/depois; conservar reconciliação, RAF único, medidor local, reduced-motion, cursor e seleção.

Cada conjunto deve ser mostrado em uma prévia de refinamento antes de ser promovido à interface oficial. Não começar por uma alteração ampla de fontes/cores em todo o CSS sem conferir o resultado de composição.

Critérios de aceitação: todas as abas em 1366×768 e 1440×900; controle de janelas em 768 e 375 px; escala do Windows 100% e 125%; conteúdo vazio e representativo preenchido; dados pendentes, antigos e indisponíveis; teclado; diálogos; fonte e credencial editadas; respostas reais recebidas durante troca de apresentação. Medir fluidez com fixtures reproduzíveis e conferir o cliente nativo. Um layout mais bonito não deve custar atraso de input ou ressuscitar o reinício visual.

## Estado da entrega

Estudo concluído. Foram criados somente este documento e os instrumentos/medidas nesta pasta de artefatos. Nenhum fonte, preferência pessoal, credencial, módulo da mente ou executor foi alterado; nenhuma proposta acima foi aplicada. As verificações usaram o bundle local e capturas de validação, sem navegar em sites externos nem iniciar a assistente.
