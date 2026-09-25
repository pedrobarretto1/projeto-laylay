# Laylay — registro de problemas e correções

Atualizado em **23/09/2026**, por Astra e SOL, a pedido do Pedro.

### Complemento da observabilidade da entrada — prompts vazios, 23/09

- Evidência do Pedro às 10:30:40 confirma que o texto recebido agora aparece;
  a correção anterior estava incompleta porque `💬 Você:` e `>` vazios ainda
  eram publicados como eventos SYSTEM. Não é perda da fala nem falha da ponte.
- Base `bd94bc3e`, main, worktree compartilhada preservada (124 entradas no
  status). Arquivos de DEV/terminal envolvidos estavam sem diff antes deste patch.
- Primeira fronteira RED: captura de stdout promovia controles de apresentação
  do leitor de stdin a eventos. Leitor real + espelho real reproduzem dois
  eventos após Enter vazio e zero mensagens processadas. Cinco REDs antes
  do candidato, 19 controles verdes.
- Produção alterada somente em `dev_console_runtime.py`: marcadores completos
  sem conteúdo são ignorados na admissão de stdout (inclusive captura oculta).
  Console original, mensagens preenchidas, linhas diagnósticas e stderr
  preservados. Não há filtro por palavra solta nem alteração de entrada/execução.
- GREEN: 68 testes em DEV, canais, terminal e ponte. Transporte autenticado
  por socket real confirma snapshot/live sem prompts vazios, preservando
  `💬 Você: 'pode ligar a luz' | origem=desktop`.
- Novos registros exigem reinício para carregar o patch; sessão real do Pedro
  não reiniciada e histórico antigo não apagado. Nenhum commit criado.

### Recibo ilegível não autoriza confirmação — 23/09

- Continuação da fronteira operacional/RED 5 descrita abaixo, não nova raiz
  independente por habilidade. Base `bd94bc3e`, main; worktree paralela preservada.
- Primeira fronteira RED: falha de `como_dict()` virava `{}` e o bloco
  `if dados_resultado` pulava a validação mantendo o texto otimista. Não era
  invenção do TTS: o texto já chegava errado à publicação visual e à fila.
  Os controles de sucesso confirmado e de confirmação desconhecida passaram.
- Antes do candidato: 15 REDs e 14 controles verdes. Além do caso histórico,
  cobertos retorno vazio/tipo inválido, acesso ao serializador com exceção,
  falas de aplicativo/arquivo/IoT e reserva indevida da deduplicação por
  atributos de um objeto cujo recibo não podia ser lido.
- Produção alterada somente em `falar_resultado_operacional`, no orquestrador
  de fala: ler uma única representação antes de validar/deduplicar; se ilegível,
  informar que o resultado não pôde ser validado, sem afirmar sucesso ou falha
  do efeito externo. Recibo posterior válido continua elegível à confirmação.
  Sem alteração em executores, autorização, LLM ou correção anterior do briefing.
- GREEN: **173 testes em oito módulos**, incluindo direção e fila de voz reais
  sem reprodução física, publicação visual, memória, receipts, guardião e
  briefing. `git diff --check` sem erros. Nenhum commit criado.
- Sessão real pendente: Laylay aberta (PIDs 26928/9880), não interrompida.
  Não foi injetada corrupção na sessão do usuário; resultado integrado não
  é uma validação de áudio físico nem encerramento de toda factualidade.

### Retomada proativa e observabilidade da entrada — 23/09

- Base: `bd94bc3e3a29c49906dc603f9ca1540310ca3274`, main, worktree
  compartilhada suja preservada. Não houve commit nem reinício da sessão.
- Raiz reproduzida: canal de chat aberto era tratado como ocupação permanente,
  tanto no Porteiro quanto no callback legado composto em `laylay.py`.
  O timer retomava normalmente, mas a mesma condição impedia a liberação.
  Quatro REDs: briefing/e-mails/rotina após silêncio e callback real extraído
  da composição. Corrigido para considerar owner, turno e atividade recente;
  reunião, foco, jogo e usuário falando continuam protegidos.
- Raiz separada: timeout da espera síncrona do briefing declarava pendente=False
  sem cancelar a fila. O recibo posterior não salvava o estado diário. RED
  reproduzido; agora a pendência continua acompanhada e sucesso tardio chama
  a persistência uma vez, somente após recibo positivo.
- Raiz separada de diagnóstico: `💬 Você:` era um prompt, não registro de fala.
  Desktop/voz não produzem eco de stdin. Cinco REDs mostram texto chegando ao
  processamento sem aparecer no DEV. O coordenador registra a entrada uma vez
  no worker comum, com origem e sanitização, sem alterar o texto processado.
- Validação: 97 testes passaram em dez módulos de porteiro, fila, briefing,
  entrada, DEV, presença e prioridade. Integração com Porteiro e Voz reais usa
  relógio/timer e saída física controlados; não equivale a áudio em produção.
  A Laylay estava aberta (PIDs 29700/4716); validação ao vivo pendente.
- Achado separado a investigar: a execução de oito módulos teve 79 PASS e
  um FAIL em `test_fronteira_operacional_falha_fechada_se_resultado_nao_serializa`:
  receipt corrompido terminou em “Pronto, abri o Chrome”. O método operacional
  não foi alterado neste patch; a worktree já contém mudanças paralelas nele.
  Não atribuir automaticamente ao patch atual nem declarar regressão ampla verde.
- Fora do patch: sincronizações repetidas da lista de conversas, indisponibilidade
  HTTP do LRCLIB, momentos sensíveis persistentes e outras possíveis causas de
  silêncio. O log HTTP isolado não identifica status ou causa do provedor.

### P01 — Continuação incerta: investigação da recusa, 23/09

- Base mantida em `bd94bc3e`, branch main e worktree compartilhada preservada.
  `quero im` chega intacto ao HTTP junto da pergunta anterior. A recusa já vem
  do Qwen, antes do verificador. Isso falsifica perda literal da entrada,
  ausência da última pergunta no payload e criação da recusa pelo guardião,
  mas ainda não identifica qual instrução/comportamento da geração a causa.
- Controle local do owner de modalidade: `quero im` é conversa, sem autorização
  e sem comandos; não é classificado como comando inválido. `quero sim` é
  confirmação contextual, também sem autorização independente. Preservar
  essa distinção; não normalizar erro de digitação para autorização presumida.
- Preparada sonda `scripts/analises/diagnosticar_continuacao_incerta.py`:
  reutiliza exatamente um payload da captura, varia fala atual e retira
  separadamente contrato efêmero e instruções gerais. Mantém histórico,
  modelo, temperatura, orçamento e schema; registra seed/entrada/saída local.
  Não importa runtime, não executa propostas nem alimenta aprendizado. As
  variantes reduzidas são ablações, **não candidatos promovidos a produção**.
- Seis testes da sonda passaram: preservação das variáveis de controle,
  imutabilidade do payload original, aborto para captura ambígua/schema
  inesperado. Não são seis respostas corretas da Laylay ou prova do modelo.
- Comparação executada depois do encerramento da sessão, sem abrir a Laylay:
  `resultados_testes/continuacao_incerta-20260923-103913-389155/comparacao.jsonl`.
  Foram oito chamadas locais (`quero im`/`quero sim`, quatro variantes).
  Algumas variantes entregaram o exemplo após `quero sim`, mas as interpretações
  de `quero im` divergiram entre si. É indício de sensibilidade ao contrato,
  não prova de uma instrução causal única. Nenhuma variante foi promovida a
  produção; preservar autorização literal sem adivinhar `im = sim`.

### P01 — Ensino aberto: referência certa, conteúdo ainda não fundamentado — 23/09

- Base `main`/`bd94bc3e`, worktree paralela preservada. A sonda com geração
  real do Qwen3:4b-instruct e 21 entradas em sete assuntos está em
  `resultados_testes/roteiro_ensino_multidominio-20260923-104318-248836/`.
  Todos os turnos responderam sem comandos, mas a métrica `19/21` mede a
  rubrica operacional/latência; `fala_coerente=nao_avaliado`. O texto final
  errou tradução de idade em inglês, conceitos de força/energia, representação
  de corte arquitetônico e exemplos de plantas anuais/perenes. Os erros já
  estavam na geração HTTP. Transporte, executor e verificador não são a
  primeira fronteira desses erros de conteúdo.
- Causa de continuidade demonstrada: `esclarecimento_literal` ancorava o
  pedido `não entendi` na fala anterior da assistente, que pode estar errada,
  sem recuperar o pedido de ensino do usuário. RED em três domínios mais
  controle de expiração. O contrato agora usa a estratégia
  `reensino_didatico`, com o pedido recente como tema e a resposta anterior
  como tentativa a revisar, não como fonte ou autorização. Produção alterada
  somente em `cognicao/contrato_fala.py`, `cognicao/geracao_concreta.py`;
  a classificação de pedidos explícitos em `personalidade/proporcao_resposta.py`
  e o roteiro genérico já estavam no candidato desta investigação.
  145 testes focados passaram; sem commit.
- Validação real posterior, sem replay:
  `resultados_testes/roteiro_ensino_multidominio-20260923-123010-079343/`.
  Os sete pedidos de reexplicação chegaram com `reensino_didatico` e sem
  execução, 21/21 responderam. O placar `18/21` volta a medir operação e
  latência, **não qualidade didática**. Persistiram erros factuais nos temas
  acima. Logo o reparo do referente é GREEN no runtime; **P01/geração factual
  permanece RED**.
- Ablação `scripts/analises/comparar_contrato_ensino.py` em quatro assuntos:
  trocar a regra de evidência/definição no prompt mudou algumas respostas,
  mas não eliminou imprecisões. Uma revisão isolada pelo mesmo Qwen aprovou
  sete reexplicações como `ERRO OBJETIVO: Nenhum`, inclusive erros verificáveis
  de tradução, física e botânica. **Autoavaliação sem evidência externa não é
  guardião factual**. Não promovê-la a produção por parecer convincente.
- A pesquisa contextual atual não é ainda uma base para cinco sites de ensino:
  `pesquisa_contextual.py` tentou Wikipédia PT/EN e recebeu HTTP 403 neste
  ambiente; a busca HTML reutilizada encontrou quatro hits sobre força/energia,
  dos quais dois abriram no teste. Disponibilidade e relevância são limites
  distintos. O desenho adaptativo e critérios de ativação estão em
  `melhorias e planos/PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md`. Não ativar busca
  compulsória nem converter snippet em confirmação factual.
- Achados separados: ao ler `planta`, uma tarefa IoT tentou pesquisar RGB
  repetidas vezes sem comando; uma reescrita de realidade introduziu `nn`
  visível na fala de inglês. Investigar por suas primeiras fronteiras, sem
  atribuir esses sintomas à raiz factual ou encobri-los com o placar 21/21.
- **23/09, candidata multifonte não promovida:** foi criada recuperação de
  até cinco páginas realmente lidas, domínios independentes, URLs e trechos,
  com guarda contra URL privada/redirecionamento e sem autoridade de ação.
  Dois ensaios de 21 turnos com influência ativada ficaram em 6/21 e 7/21
  sem alertas operacionais (p95 perto de 20 s), piores que a referência 18/21.
  A inspeção das falas encontrou definição correta na fonte, mas inversão
  produzida pelo Qwen (planta baixa vista de baixo), tradução “eu sou 25”,
  código de exemplo com repetição incorreta e exemplos botânicos inventados.
  Logo a camada de leitura é GREEN local, mas **P01/geração + verificação de
  alegações continua RED no runtime**. `LAYLAY_PESQUISA_MULTIFONTE_MODO`
  fica `desativado` por padrão; `ativo` serve somente para experimento.
  `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md` registra portões restantes. Não
  somar o sintoma IoT `planta` como nova raiz factual.
- **24/09, mesma raiz P01, candidata de prompt ainda insuficiente:** no
  cenário hipotético com leitura de 15% e limiar de 20%, o Qwen recebeu os
  dados, mas sua resposta bruta omitia a comparação ou acrescentava causas
  não demonstradas; o verificador as preservou. O roteiro compacto recebeu
  o contrato premissas → relação → conclusão (RED em três assuntos).
  Depois, dois REDs mostraram que falas antigas da assistente voltavam ao
  ensino pelo histórico e por `Evite repetir`; ambas as rotas foram retiradas
  só do prompt didático, sem alterar memória nem autorização. No runtime,
  a comparação `15 < 20` melhorou, mas ainda surgiram promessas de umidade
  e explicações botânicas não ancoradas. **P01 continua RED; inventário de
  cenário segue em sombra.** 236 testes relevantes verdes; os 4/4 do roteiro
  mediam transporte/não execução, não verdade. Evidência e próxima fronteira
  de alegações atômicas em `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md`.

### P01 — Perfil explicativo perdido na escolha do prompt — 23/09

- Base `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`. Conferidos HEAD,
  branch e worktree; trabalho paralelo neural/operacional preservado.
  Sem novo ID por frase: esta é uma causa demonstrada de instrução inadequada
  dentro de P01, não a explicação de todas as recusas/erros do modelo.
- Captura anterior `transporte_evidencia-20260922-173130-396574`: pedido
  `quero passo a passo usando metodos praticos` chegou com o tema da divisão
  no histórico, mas prompt rápido mandava uma ou duas frases, contrato três,
  e retrato expressivo permitia oito. O modelo só prometeu explicar, usando
  58 tokens e `finish_reason=stop`: **não foi corte por esgotar tokens**.
  Falsificadas perda do tema no transporte e mutilação desse rascunho pelo
  verificador. A hipótese de que a compressão explica toda a má geração não
  foi demonstrada e não deve ser usada para fechar P01.
- Primeira divergência: `classificar_proporcao` já dizia `explicativa`, mas
  `usar_modo_rapido_conversa` verificava só fórmulas/reexplicação e tamanho.
  Logo um pedido curto de desenvolvimento recebia rota/prompt de fala breve;
  o contrato efêmero também ignorava o perfil ao escolher o limite inicial.
- Contrato reutilizável: **necessidade da resposta governa a compactação, não
  tamanho da entrada**. Rota e contrato reutilizam a classificação existente
  em `proporcao_resposta`. Perfis explicativo/matemático não entram no rápido;
  contrato herda seu espaço, preservando teto atual de oito e as restrições
  específicas posteriores. Saudação segue rápida; autoridade e receipts não
  mudam. Não foram acrescentados gatilhos privados, modelo ou fallback.
- RED: **6 falhas causais / 82 controles verdes**, com pedido histórico,
  divisão, fotossíntese, detalhes e comparação de conceitos. Candidato de
  produção somente em `autonomia/fluxos_conversa.py` e
  `cognicao/contrato_fala.py`. Em fluxos, alterações anteriores de P03 foram
  preservadas. Testes em `test_latencia_resposta.py` e
  `test_contrato_semantico_fala.py`, incluindo o callback realmente injetado
  em `_resposta_ia_runtime` pelo `laylay.py`. Sem treino, promoção ou commit.
- Regressão final selecionada: **643 aprovados / 13 xfailed preexistentes**
  em 22 módulos, 7,12 s, incluindo os contratos de P10. `git diff --check`
  sem erro de whitespace; aviso CRLF no relato do usuário não foi corrigido
  por estar fora do escopo. Não foi executada a suíte global.
- Geração real, **sem replay**, duas sessões Qwen3:4b-instruct:
  `roteiro_ensino_divisao-20260923-100339-722094` e
  `roteiro_ensino_divisao-20260923-100458-680059`. Transporte respectivamente
  em `transporte_evidencia-20260923-100338-508086` e
  `transporte_evidencia-20260923-100457-371895`, todos em `resultados_testes/`.
  O turno 2 recebeu prompt completo, contrato de sete frases e 512 tokens
  disponíveis. Produziu e entregou três passos na primeira sessão e cinco na
  segunda. Primeira resposta consumiu 173 tokens e terminou por `stop`.
  Melhora observada, não taxa de acerto estimada nem ablação estatística.
- Ambas encerraram com código zero; nenhuma sessão do Pedro foi encerrada
  pelo agente. A tentativa anterior 10:02:48 foi bloqueada corretamente por
  instância ativa; sondas só continuaram após Pedro encerrar. Voz/UI/mic off,
  Gmail inativo, IoT simulado; observadores e memória normal ativos. Áudio
  físico não testado. Placar 4/4 mede não execução, não aprovação do ensino.
- **Ainda aberto:** em ambas, turno 3 confundiu contrário/inverso; turno 4
  interpretou `quero im` como pedido impossível/sem comprovação. Os erros já
  vieram no HTTP, com a pergunta anterior no histórico. A maior disponibilidade
  de tokens não resolve isso. Próxima investigação: contexto/instrução e
  tratamento de continuação incerta na geração, com contrastes, sem ensinar
  `im = sim` como regra autorizante. JSON literal fora do envelope e perguntas
  excessivas também ocorreram; entrega recuperou o texto, não certificou
  conformidade estrutural. Achado de resumo `principal_duplicada` reapareceu,
  segue separado e sem prova de contaminação persistida.

### P10 — Aspas indeterminadas não são evidência de obra — 22/09, continuação

- Base mantida: `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`,
  worktree suja/compartilhada preservada. Primeira fronteira: ramo residual de
  `_destaques_com_papel` atribuía `obra_candidata` a tudo que não reconhecia.
  O verificador rejeitava e o orquestrador pesquisava `desfaz`/`o contrário`.
  Capturas anteriores e RED sem modelo/provedor falsificam truncamento na
  geração e falha de pesquisa como causas desse corte específico.
- Contrato: título precisa de indício relacional (tipo, seleção, nomeação,
  enumeração tipificada ou resposta nominal ao tipo solicitado). Sem indício,
  papel `indeterminado`, não obra e não enunciado isento. Datas, medidas,
  categorias e estados continuam passando por suas verificações; contexto
  não vira fonte nem autorização. A leitura do texto completo sobrevive à
  divisão em frases. Pesquisa e validação recebem o mesmo contexto do usuário.
- RED inicial: **15 falhas / 24 verdes**, sendo **11 falhas comportamentais**
  e quatro da nova assinatura contextual ainda inexistente (estas quatro não
  contam como prova causal). O teste com `x` ficava verde pela limitação antiga
  de duas letras no scanner, não pelo papel correto; trocado por `delta`.
- Dois controles antigos de obras revelaram lacunas na primeira versão do
  candidato; mantidos e atendidos. Um controle diferente atribuía um título
  de filme a `Noite Inventada` num exemplo ambíguo de abrir aplicativo.
  Expectativa corrigida por não haver indício de obra; nova prova conserva
  a rejeição de data dentro desse trecho, sem mascará-lo como enunciado.
- Produção desta rodada: `cognicao/fundamentacao_factual.py` e passagem do
  `texto_usuario` em `cognicao/orquestrador_turno_runtime.py`. Testes ampliados
  nos arquivos de explicação didática e citações existentes. Sem mudança em
  pesos, autorização, executores, personalidade ou `laylay.py`; nenhum commit.
- Provas: **430 aprovados / 13 xfailed preexistentes**, seleção de 16 módulos,
  incluindo import da composição real, segurança e recomendação. Não é suíte
  global. Uma tentativa paralela à sonda deu três falhas de import pelo lock
  de instância única (427 verdes); repetida após saída da sonda, sem alterar
  a proteção, resultou nos 430 verdes acima.
- Runtime: `resultados_testes/roteiro_ensino_divisao-20260922-173131-509832/`;
  HTTP em `transporte_evidencia-20260922-173130-396574/`. Somente turno 3 usa
  replay explícito da captura `transporte_evidencia-20260922-171829-788015`;
  demais turnos têm geração nova. As explicações entre aspas chegaram inteiras
  sem busca de obra. O guardião de perguntas marcou `perguntas_em_excesso` e
  ajustou pontuação na saída do terminal, não removeu as cláusulas citadas.
  Sessão terminou com código zero, sem processo Laylay restante. Voz/UI/mic
  desligados, IoT simulado, Gmail inativo; observadores e persistência normais
  ativos. Placar 4/4 só certifica ausência de comandos, não qualidade didática.
- **Limites e próxima raiz:** não é classificador semântico universal nem
  verificador matemático. Mantida a distinção incorreta contrário/inverso do
  rascunho para provar preservação, não sua verdade. Nesta geração nova, turno
  2 prometeu passos sem entregá-los; turno 4 recusou `quero im` como comando
  inválido. Ambos já constam do texto bruto: **P01/geração**, próximo alvo,
  não novos remendos no extrator. Resumo com `principal_duplicada` reapareceu;
  permanece achado separado, sem prova do conteúdo persistido.

### P10 / P01 — Ensino perde passos no verificador; geração tem falhas próprias — 22/09

- Base `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`; worktree paralela
  preservada. Relato de 21/09, 10:37:02–10:37:05: o rascunho contém a divisão
  por agrupamento e seus passos; o extrator interpreta a pergunta citada
  `6 cabe quantas vezes em 18?` e o nome do método como obras. Pesquisa sem
  evidência → rejeição das frases → só enunciado e resultado chegam ao usuário.
- Falsificações: não era necessário aumentar o limite de tokens para salvar
  esses passos, pois já estavam na geração; o corte se reproduz sem modelo e
  sem provedor de pesquisa. O problema não é exclusivamente matemática: o mesmo
  classificador de papéis trata perguntas instrutivas e referências conceituais.
  A resposta a `quero im` no log histórico já era inadequada antes do guardião,
  portanto não se atribuiu toda a qualidade do ensino ao mesmo defeito.
- Contrato P10 ampliado no owner existente `fundamentacao_factual.py`:
  pergunta proposta ao interlocutor e retomada explícita do que ele quis dizer
  são enunciados; nome tipificado como método/conceito/termo é referência
  conceitual, não obra. Referência conceitual não mascara datas/medidas nem
  certifica a existência, correção ou propriedades do conceito. Citações não
  viram utterances autorizantes; obras vizinhas continuam exigindo evidência.
- RED inicial: **7 falhas / 6 controles verdes**. Primeira sonda revelou outra
  ocorrência da mesma fronteira: a geração pedia esclarecimento citando
  `quero im`, mas o verificador substituía por falta de fonte factual.
  Reproduzidos mais **3 REDs / 14 verdes** antes de incluir essa retomada.
- Produção alterada nesta rodada: somente `cognicao/fundamentacao_factual.py`.
  Novo `scripts/tests/test_explicacao_didatica_preservada.py`; roteiro
  `scripts/roteiros/roteiro_ensino_divisao.py`, aceito na sonda existente de
  transporte. Nenhum patch de pesos, executor, personalidade ou orçamento.
  Pesquisa em cinco camadas continua fora do escopo.
- Provas finais: **19 testes próprios**, incluindo o verificador ligado pelo
  `laylay.py`, com pesquisa proibida para a aula histórica; seleção ampliada
  **212 aprovados / 13 xfailed preexistentes**. Sem alteração dos xfails.
- Duas sessões completas com geração local nova, microfone/voz/UI desativados,
  Gmail inativo, IoT simulado e observadores/persistência normais ativos:
  `roteiro_ensino_divisao-20260922-171645-086047` e
  `roteiro_ensino_divisao-20260922-171831-067132`, em `resultados_testes/`.
  Capturas HTTP/preparação: `transporte_evidencia-20260922-171643-712042` e
  `transporte_evidencia-20260922-171829-788015`. Ambas preservaram integralmente
  o passo a passo gerado no turno 2, sem pesquisar sua pergunta como obra.
  Primeira tentativa 17:16:31 abortou antes dos turnos por expressão não literal
  nas expectativas do roteiro; corrigida somente a fixture para o loader.
- **Ainda RED, mesma P10:** aspas de ênfase/predicado (`a divisão 'desfaz' a
  multiplicação`, `'o contrário'`) e outras molduras (`a divisão pergunta:`)
  seguem caindo na classificação residual de obra. Não basta ir adicionando
  frases: a próxima investigação deve separar papel desconhecido de evidência
  positiva de obra, preservando os controles de títulos e fatos externos.
- **Ainda aberto, P01/geração:** as duas sondas geraram distinção confusa entre
  contrário/inverso. No último turno da segunda sessão o modelo voltou a negar
  capacidades externas, sem relação com a aula; o texto ruim já estava no HTTP.
  O esclarecimento citado pós-correção está validado localmente, mas essa última
  geração não o produziu: não alegar correção integral de `quero im` no runtime.
- A primeira sonda marcou 2 aprovações/1 falha/1 alerta; a segunda marcou 4/4,
  apesar desses defeitos visíveis. Expectativas verificam ausência de comandos,
  não qualidade didática. **4/4 não é aprovação do ensino.**
- Achado separado durante a segunda sonda: tentativa de resumo das últimas
  cinco interações recebeu `principal_duplicada` e em seguida houve log de
  memória salva. Isso não prova o conteúdo persistido; auditar o consumidor de
  sentinelas antes de atribuir contaminação a essa origem. Não corrigido aqui.
- Estado: melhoria de P10 comprovada nos passos históricos e em geração real;
  P10/P01 permanecem abertos nos limites acima. Nenhum commit criado.

### P04 — Contador observava a porta legada, não o ADD executado — 22/09

- Base `main`, HEAD `bd94bc3e3a29c49906dc603f9ca1540310ca3274`;
  alterações paralelas preservadas. Reproduzido novamente o histórico:
  a faixa correta está no arquivo, mas `add_final=0` (um RED / um controle).
- Cadeia demonstrada por código e observação: feedback chama
  `RegistroOperacoesMusicais.adicionar_faixa_resultado` →
  `OperacoesMusicaisRuntime.adicionar_faixa_resultado` →
  `PlaylistRuntime.add_and_verify_result`. O contador do teste envolvia apenas
  `add_and_verify`, o wrapper bool legado, que essa cadeia não chama.
- Duas observações independentes, uma em cada porta, confirmaram **zero chamadas
  legadas e uma detalhada**, com uma faixa persistida. A comparação com o
  contador antigo produziu outro RED, antes da correção do teste. No controle
  de CREATE falho, ambas as portas tiveram zero chamadas e nenhum alvo salvo.
  Falsificadas ausência de ADD e falha de persistência como causas de P04.
- Correção exclusivamente no harness histórico
  `scripts/tests/test_red151_runtime_canonico_c3.py`: contador envolve a porta
  detalhada, sem mudar o retorno nem a exigência de **exatamente uma** chamada.
  Removida instrumentação duplicada; bloqueio após CREATE falho segue exigindo
  zero ADD. Nenhum executor de produção foi alterado para satisfazer o teste.
- Outra lacuna de composição do mesmo harness: faltava o callback de publicação
  que `laylay.py` realmente fornece. Incluída captura de receipts e reforçadas
  as asserções de sucesso/falha, alvo musical e ordem `receipt → fala`. Não é
  prova do publicador real: essa fronteira é coberta separadamente por
  `test_root_publica_receipt_antes_da_fala_com_persistencia_real` (P03).
- Provas: **4/4** no composto e controle da medição; **24/24** incluindo P03,
  guardião e composição real importada; **352 aprovados** na seleção ampliada
  playlist/feedback/receipt/adaptador/cooperação. Escritas somente em diretórios
  temporários dos testes. Nenhuma playlist pessoal, rede ou sessão alterada.
- Estado: **P04 encerrado como defeito de instrumentação**, não como bug de
  salvamento corrigido em produção. Isso não encerra P03 no runtime completo,
  nem a qualidade geral da conversa. Próxima raiz prevista: ensino/conversa,
  separando o texto gerado da informação removida pelos verificadores.

### Verdade operacional da fala — receipt limita a certeza — 22/09

- Objetivo desta frente: impedir que personalidade, status otimista ou autoria
  da LLM aumentem a certeza acima do resultado realmente observado. Não houve
  redesenho do estilo da Laylay: repertório, emoção e personalidade foram
  preservados; a mudança atua somente na camada factual que antecede a fala.
- A arquitetura já possuía boas defesas: `planejar_resposta_acao()` separava
  sucesso/falha/incerteza, a autoria LLM recebia um contrato imutável e o
  guardião de alegações já sabia remover conclusão sem evidência. A
  investigação procurou os pontos onde essa verdade ainda podia ser
  reconstruída ou promovida antes de chegar a essas defesas.
- RED 1 — `AdaptadorResultadoOperacional.falar_por_status()`: um executor
  moderno podia publicar `confirmado=False` ou `confirmado=None` e, em
  seguida, a fala reconstruía `confirmado=True` apenas porque o status era
  otimista, como `app_aberto`. O adapter agora consome o tratamento moderno
  já publicado; inferência por status ficou restrita à compatibilidade legada.
  Resultado moderno explícito nunca perde seu `False/None` durante a fala.
- RED 2 — semântica da incerteza: `executou=None, confirmado=None` era
  verbalizado como “Enviei o comando...”, inventando até a tentativa.
  `executou=True, confirmado=None` continua podendo dizer que o comando foi
  enviado sem resultado confirmado; execução desconhecida agora diz somente
  que **não há confirmação de que a ação chegou a ser executada**.
- RED 3 — não execução por política: `nao_executado_por_politica` era
  classificado como falha e podia virar “não consegui/tentei”. O planejador
  ganhou a classe `nao_executado`: a fala-base declara “não executei”, sem
  inventar tentativa ou incapacidade. Essa classe permanece calma e não passa
  pelo estilizador de sucesso.
- RED 4 — tri-state perdido na normalização:
  `normalizar_resultado_acao()` tratava campo ausente e
  `"confirmado": None` como a mesma coisa, podendo promover `None` explícito
  a `True` por causa do status. Agora **campo ausente** mantém a inferência
  legada; **campo presente com None** preserva a incerteza moderna.
- RED 5 — última fronteira antes do TTS:
  `OrquestradorFalaRuntime.falar_resultado_operacional()` deduplicava a fala,
  mas confiava integralmente no texto recebido. Ele agora aplica o guardião
  existente usando somente o receipt atual antes de chamar a voz. Uma fala
  “Pronto, abri o Chrome” permanece idêntica quando o receipt confirma; com
  `confirmado=None` é corrigida para envio sem confirmação; com não execução
  confirmada, a alegação de sucesso é removida. O gate é exclusivo da fala
  operacional e não altera conversa/personagem.
- Auditoria de bypasses diretos: sucessos diretos encontrados em organização de
  janelas, volume/autonomia e leituras de agenda/navegador já estavam atrás de
  confirmação/releitura local. Não foram migrados desnecessariamente.
- Scanner estrutural encontrou somente dois executores não musicais capazes de
  publicar status listado como confirmado sem `confirmado=` explícito:
  `site_aberto` remoto no PC B e `remetente_silenciado` no Gmail.
  Ambos foram fechados e o scanner terminou em **0 ocorrências**.
- PC B: enviar `open_url` prova despacho, não que a aba apareceu. O resultado
  passou de `site_aberto` para `abertura_solicitada`,
  `executou=True, confirmado=None`; a fala informa que a abertura foi pedida
  e ainda não confirmada.
- Gmail: o executor descartava o bool real de
  `_gmail_silenciar_remetente()`, engolia exceção e sempre dizia sucesso.
  Agora só publica `remetente_silenciado` com retorno `True`;
  `False`/exceção viram `falha_execucao` e alvo ausente vira
  `alvo_ausente`, todos com execução/confirmação explícitas.
- Provas focadas da fronteira de fala: **161/161 aprovados**. REDs adicionais
  de adapter, tri-state, semântica de incerteza, política e último gate do TTS
  também ficaram verdes. Scanner final:
  `CONFIRMED_STATUS_WITHOUT_EXPLICIT_RECEIPT=0` fora da frente musical.
- Regressão global controlada final:
  **6.692 passed, 1 skipped, 13 deselected, 14 xfailed, 56 subtests passed**,
  zero falhas. Os mesmos oito testes de root bloqueados pela instância real
  passaram **8/8** com bypass de mutex exclusivamente no processo de pytest.
- Validação mecânica: `py_compile=0`, `git diff --check=0`. Neural continua
  em `shadow`; hashes do modelo ativo e v27 permaneceram
  `07C539...9E62` e `CAAA93...E0CF`. A frente
  `executor_musical/executor_playlists/controle_midia/playlist_runtime`
  permaneceu fora do diff desta investigação.
- Regra arquitetural consolidada: **a personalidade decide como dizer; o
  receipt decide o que ela pode afirmar. A fala nunca aumenta a certeza.**

### P03 — Publicação do resultado antes da conclusão — 22/09

- Base preservada: `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`,
  worktree suja. Nesta retomada o adaptador, o planejador e os testes da frente
  paralela já continham mudanças posteriores: os dois REDs citados em P18/P19
  passaram sem novo patch nosso nesses arquivos. A normalização preserva
  `confirmado=None` explícito; os testes agora publicam tratamento depois da
  construção do adaptador, conforme o ciclo de vida da invocação.
- P03 continuava RED: `create → add → ultima → fala → receipt`. O callback
  oficial existe tanto no teste quanto no getter real em `laylay.py`;
  `FeedbackPendenteRuntime` já o repassa. Ausência de injeção é falsificada.
  CREATE/ADD retornam sucesso e o mesmo guardião aceita a fala quando recebe
  antes o receipt: não é necessário relaxar o guardião nem corrigir o storage.
- Primeira divergência: `fluxos_conversa.handle_feedback_pendente` emitia a
  conclusão antes do bloco de publicação. Contrato compartilhado: **efeito
  observado → publicação canônica → conclusão**, não fala como prova de efeito.
  A implementação foi ajustada no orquestrador responsável, reutilizando o
  registrador e o contrato consumidos pelos demais domínios.
- RED novo: 15 casos falharam antes do patch. Incluem sucesso, idempotência,
  falha de criação/adição, faixa ausente, dois nomes e indisponibilidade do
  publicador. No ramo sem faixa, o receipt acessava `criacao` não inicializada;
  esse caminho agora publica a falha e produz uma única resposta.
- A publicação vem antes da fala; ausente, com exceção ou `False` explícito,
  impede a confirmação de sucesso. O fluxo informa a falha de registro sem
  inventar falha da escrita nem repetir o efeito. Duplicata é reconhecida como
  estado já satisfeito; criação só é anunciada se o executor informou `criada`.
- Produção alterada nesta rodada: somente `autonomia/fluxos_conversa.py`.
  Novo teste: `scripts/tests/test_feedback_publicacao_antes_fala.py`.
  Guardião, armazenador, composition root, neural e patches paralelos intactos;
  nenhum commit, alteração das playlists pessoais ou efeito em Chrome/IoT.
- Provas: histórico P03 e controles passaram; **16 testes novos verdes**.
  Um deles importa o `laylay.py` e usa os objetos reais de feedback, registro
  musical, operações, armazenamento e publicação. CREATE/ADD gravam arquivo
  temporário, a saída verifica receipt no plano antes da fala e a segunda
  confirmação mantém uma só faixa. Voz é capturada, observação do player é
  controlada e aprendizado desligado: **integração da composição real**, não
  uma sessão completa com áudio/Chrome/modelo.
- Regressão ampliada de playlist/feedback/receipts/adaptador/cooperação:
  **348 aprovados**. O teste composto P04, executado separadamente, permanece
  **1 falha / 1 aprovado**, no contador `add_final=0` em vez de 1; não foi
  removido, alterado ou considerado resolvido pela correção P03.
- Estado P03: corrigido e validado localmente e na composição com disco real;
  sessão completa ainda pendente. Próxima fronteira operacional: esclarecer a
  medição de P04 antes de mudar o executor. Ensino/conversa permanece outra raiz.

### P18 / P19 — Escopo da consulta e evidência da confirmação — 22/09

- Base: `main`, HEAD `bd94bc3e3a29c49906dc603f9ca1540310ca3274`,
  worktree suja com alterações paralelas de cliente, neural, modalidade e
  contratos operacionais. Essas alterações foram preservadas; nenhum commit.
- Evidência histórica: os dois últimos relatos em `erros/erros_encontrados.md`
  (pergunta sobre garantia de chuva amanhã; clima anexado ao salvar em yago).
  São duas causas demonstradas, não uma causa única comprovada de briefing.
- **P18 / F1, escopo perdido:** o publicador canônico de continuidade removia
  `local`, `cidade` e `day_offset`; o detector tratava o aprofundamento como
  consulta nova para hoje. O executor respondia com condições atuais sem
  responder sobre certeza. A redação histórica existe nesse executor, portanto
  não é necessário atribuí-la a briefing ou alucinação do modelo. RED local
  demonstrou a perda antes de qualquer chamada ao provedor.
- Contrato: aprofundamento meteorológico herda escopo apenas de consulta
  bem-sucedida, recente, do domínio ativo e do mesmo dia. Cidade/data explícita
  vence; troca de assunto/expiração impede herança. Probabilidade não vira
  garantia, inclusive em 0%/100%; ausência de dados não vira confirmação.
- **P19 / F2, fatos alheios na autoria:** o pedido de confirmação levava falas
  anteriores completas como exemplos de não repetição. O verificador aceitava
  a paráfrase climática histórica; repetição literal e paráfrase não são o
  mesmo contrato. Reproduzido em playlist, IoT e criação de pasta. O HTTP
  histórico não foi capturado: a exposição e vulnerabilidade estão provadas,
  mas não se afirma conhecer todo o prompt daquela execução do usuário.
- Contrato: autoria operacional recebe somente dados do resultado atual,
  usando o mecanismo existente `_contexto_fechado`. Histórico permanece no
  verificador local, não no pedido ao modelo. Números novos sem evidência
  provocam reparo e, se ele falhar, a fala factual segura. A limpeza de pergunta
  opcional também repassa por toda a validação, sem atalho de aprovação.
- Hipóteses concorrentes: defeito no provedor não explica a perda local de
  parâmetros; briefing não é necessário para produzir a resposta histórica;
  problema exclusivo de playlist é falsificado pelas provas em três domínios.
  Isso não é prova geral contra toda invenção verbal sem números.
- Produção alterada somente em `continuidade_geral.py`,
  `roteador_deterministico.py`, `orquestrador_deterministico.py`,
  `executor_informacoes.py` e `confirmacao_llm.py`. Nenhuma mudança nossa em
  pesos, ativação neural, armazenamento de playlists, IoT ou `laylay.py`.
- RED inicial: **6 falhas / 5 controles verdes**. Após candidato:
  **19/19** em `scripts/tests/test_escopo_consulta_e_confirmacao.py`, incluindo
  publicação/detecção do composition root real e preparação HTTP real com
  transporte controlado. Receipts sintéticos nessa prova não certificam efeito.
- Regressão ampliada atual: **189 aprovados / 2 falhas** em dez módulos.
  Os dois REDs são `test_fala_por_status_nao_eleva_confirmacao_negada_pelo_contrato`
  e `test_fala_por_status_nao_transforma_sem_receipt_em_sucesso`, também
  reproduzidos isoladamente no adaptador (**26 aprovados / 2 falhas**).
  A primeira divergência está antes da autoria: o construtor apaga o tratamento
  que os testes publicam antes dele; há também inferência por status quando
  `confirmado=None`. Pertencem à frente paralela tratado/receipt, não foram
  corrigidos aqui nem removidos da contagem. Verificar ciclo de vida e preservar
  a distinção entre ausência legada e incerteza explícita antes de novo patch.
- Runtime real executado com voz/microfone/presença desativados e IoT simulado:
  `resultados_testes/roteiro_escopo_previsao-20260922-064429-204197/`.
  Três consultas, nenhuma escrita de playlist. Fonte primária e reserva deram
  timeout; três falhas foram informadas com `executou=False, confirmado=False`.
  O resumo automático tem **zero casos avaliados**, não três aprovações.
  **Runtime com previsão bem-sucedida ainda não validado.** O roteiro reutilizável
  está em `scripts/roteiros/roteiro_escopo_previsao.py`.
- Estado: GREEN local/integração nos contratos novos; regressão ampliada não
  totalmente verde; P18/P19 ainda não encerrados no runtime. Próxima prova:
  repetir consulta com fonte disponível e verificar confirmação operacional
  com geração real. Relatos antigos de ensino, DEV e presença continuam
  separados; esta entrada não encerra toda a pasta de erros.

### Contrato tratado ≠ executado ≠ confirmado — 21/09

- A investigação partiu de um risco sistêmico: callbacks históricos retornam
  `True` tanto para “esta camada tratou o pedido” quanto para “o efeito ocorreu”.
  O candidato já presente na worktree separava `tratado`, `executou` e
  `confirmado`, mas ainda considerava `executou=True, confirmado=None` como
  `sucesso_habilidade=True`.
- RED real reproduzido em três fronteiras do mesmo fato: uma execução moderna
  sem receipt era registrada no autoaprimoramento como **1 sucesso / 100%**,
  recebia reforço positivo e permitia que uma cadeia avançasse para a etapa
  dependente. Foco inicial: **3 falhas e 6 vizinhos verdes**.
- Contrato canônico ficou trivalente. Para resultados modernos:
  `confirmado=True` = sucesso comprovado; `confirmado=False` = não sucesso;
  `executou=True + confirmado=None` = **resultado incerto**, nunca sucesso.
  Retornos puramente legados preservam temporariamente a compatibilidade do bool
  para não quebrar executores ainda não migrados.
- `ResultadoTratamentoOperacional` ganhou `resultado_incerto`. O
  autoaprimoramento também passou a aceitar resultado neutro: incrementa
  `tentativas` e `incertos`, mas não `sucessos`, não `falhas` e não
  `cookie_reforco`. O resumo expõe “sem confirmação”; a taxa confirmada usa
  somente resultados realmente avaliados.
- O gate central de `EstadoContextoRuntime.registrar_autoaprimoramento` não
  deixa um bool externo transformar contrato moderno em sucesso: receipt
  confirmado entra como sucesso, efeito incerto entra neutro e política/falha
  não reaparece como êxito.
- A deduplicação do `CicloComandosRuntime` estava apagando a identidade de
  compatibilidade do retorno legado. O cache agora preserva `legado` e não
  “moderniza” uma segunda ocorrência de bool antigo em contrato moderno sem
  receipt.
- A caixa de entrada expôs o inverso do mesmo princípio. O helper genérico
  continua proibido de inferir `confirmado=executou`; em vez disso, operações
  que possuem evidência local real publicam seu próprio receipt: persistência
  de nota/discussão, duplicata já observada, listagem local e exclusão salva.
  **O owner que observa o efeito confirma; a camada genérica não adivinha.**
- Provas focadas: **9/9** no contrato novo; **51/51** em cadeia/deduplicação/
  publicação; **350 aprovados + 8 subtests** nos consumidores sensíveis
  (orquestração, autonomia, caixa, transferências e mente única).
- Regressão global controlada:
  `6636 passed, 1 skipped, 13 deselected, 14 xfailed, 56 subtests passed`,
  zero falhas. Dos 13 deselecionados, oito testes do root foram bloqueados pela
  instância real já aberta e passaram **8/8** com bypass de mutex somente de
  teste; os cinco restantes foram reproduzidos no HEAD limpo
  `bd94bc3e`: três REDs históricos de feedback/playlist e dois de ownership
  de presença. Portanto não são regressões desta correção.
- Nenhuma dessas provas promove modelo neural, altera pesos ou transforma
  ausência de confirmação em falha. O objetivo é impedir sucesso fictício sem
  inventar fracasso fictício.

### Migração do legado operacional e barreira sem receipt — 21/09

- Continuação da frente `tratado ≠ executado ≠ confirmado`. Após tornar
  `executou=True + confirmado=None` neutro, a próxima pergunta foi onde um
  bool puro ainda conseguia entrar no contrato moderno.
- Scanner estático dos executores não musicais encontrou quatro saídas reais
  tratadas sem publicação explícita: volume com ação inválida, IoT
  indisponível/bloqueado antes do runtime, `SUGGEST_ACTION` e o alias
  `FECHAR_PROGRAMA`. RED no roteador real: **4 falhas e 9 vizinhos verdes**;
  todos apareciam como `legado=True`.
- Volume inválido agora publica `acao_invalida`,
  `executou=False, confirmado=False`. IoT sem runtime publica
  `indisponivel`; veto de modalidade publica
  `nao_executado_por_politica`. Nenhum desses caminhos pode mais ser
  promovido a sucesso por um bool externo.
- `SUGGEST_ACTION` permanece semanticamente sem efeito operacional, conforme
  o catálogo de capacidades. Quando a sugestão local é registrada, marca
  somente tratamento (`sugestao_registrada`), com
  `executou=False, confirmado=False`; não cria receipt de ação nem
  autoaprimoramento de sucesso.
- `FECHAR_PROGRAMA` deixou de criar um segundo dict recursivo de
  `CLOSE_APP`. O alias delega diretamente à mesma habilidade usando o mesmo
  adapter, preservando a identidade original e produzindo **um único receipt**.
  Sem alvo, publica `alvo_ausente`.
- Foi adicionado um fail-closed no roteador para executores modernos não
  musicais: se um `ResultadoDespacho` disser que tratou a intenção e nenhum
  receipt/tratamento tiver sido publicado, o resultado vira
  `tratado_sem_receipt`, com `executou=None, confirmado=None`. O bool antigo
  continua apenas em `retorno_legado`; não cria sucesso, falha ou efeito
  imaginado. Música/playlist/`MEDIA_CONTROL` ficaram explicitamente fora
  dessa barreira nesta etapa para não invadir a frente paralela do Codex.
- RED específico injetou propositalmente um executor moderno de arquivos que
  retornava `True` sem receipt. Antes: `legado=True, executou=True`; depois:
  `legado=False, tratado=True, executou=None, confirmado=None,
  status=tratado_sem_receipt`.
- O `CicloComandosRuntime` ganhou telemetria de contrato sem alterar
  autoridade ou decisão: `observados`, `legados`,
  `tratados_sem_receipt`, `confirmados`, `nao_confirmados`, `incertos`,
  além de mapas `legados_por_intent` e `sem_receipt_por_intent` e as últimas
  intents observadas. Assim, a migração futura pode ser guiada por uso real.
- O diagnóstico central já consumia
  `diagnostico_linguagem_natural()`; o formatter do Terminal agora expõe uma
  linha compacta “contrato de execução” com esses contadores e as últimas
  intents legada/sem receipt. O snapshot bruto preserva os mapas completos.
  A presença de compatibilidade legada **não degrada automaticamente** a saúde:
  nesta fase a telemetria é informativa.
- Provas da etapa: **53/53** no primeiro lote de executores/contrato;
  **184/184** em todos os executores não musicais + arquivos;
  **206/206** após adicionar a telemetria; **53/53** nas regressões de
  diagnóstico/formatter. Regressão global controlada:
  **6.642 passed, 1 skipped, 13 deselected, 14 xfailed, 56 subtests passed**,
  zero falhas. Os 13 deselecionados são os mesmos já causalmente isolados:
  cinco REDs preexistentes e oito testes de root bloqueados pela instância real.
  Os oito de root passaram novamente **8/8** com bypass de mutex somente no
  processo de pytest.
- Não houve promoção neural, alteração de pesos, commit, push, merge ou
  reescrita destrutiva. A compatibilidade booleana permanece disponível apenas
  para caminhos realmente legados; executores modernos não musicais agora
  falham fechados quando esquecem o receipt.

### Cadeias dependentes exigem sucesso do contrato — 21/09

- A telemetria/migração do contrato revelou outra fronteira booleana no fluxo
  composto. `executar_fluxo_intencao()` já interpretava
  `ResultadoTratamentoOperacional`, mas devolvia `bool(retorno)`. Assim, uma
  etapa moderna podia estar `tratada_sem_receipt`, com
  `sucesso_habilidade=False`, e ainda retornar `True` para a cadeia.
- Reprodução direta antes do patch: executor marcou
  `tratado=True, executou=None, confirmado=None,
  status=tratado_sem_receipt`, retornou `True` e
  `executar_fluxo_intencao()` também devolveu **True**.
- A causalidade foi conferida no HEAD base
  `bd94bc3e3a29c49906dc603f9ca1540310ca3274`: a versão congelada fazia
  `executou = bool(_call(... executar_intencao ...))`, publicava esse bool,
  autoaprimorava quando verdadeiro e devolvia `executou`. Portanto a
  ambiguidade já existia no baseline.
- O retorno padrão foi preservado por compatibilidade: fora de composição
  dependente, `True` ainda pode significar “o turno foi consumido/tratado”.
  Foi adicionado o modo explícito
  `exigir_sucesso_habilidade=True`, que devolve somente
  `tratamento.sucesso_habilidade`.
- `CicloComandosRuntime.processar_cadeia()` é o único consumidor conectado a
  esse modo estrito. Consultas somente leitura continuam concluindo sua etapa
  pelo próprio contrato observacional; mutações passam pelo modo estrito.
- Consequência: se a etapa A for tratada mas não tiver receipt suficiente, a
  cadeia relata a falha e **não chama a etapa B dependente**. O comportamento
  standalone permanece compatível, evitando transformar “não avançar cadeia”
  em “reprocessar o turno inteiro”.
- RED de fronteira inicialmente falhou porque o modo estrito não existia.
  Após a correção, o mesmo caso preserva `True` no standalone e retorna
  `False` no contexto dependente. Teste de composição adicional prova que a
  cadeia canônica chama somente a primeira etapa com
  `exigir_sucesso_habilidade=True` quando ela falha.
- Regressão focada após a mudança: **23/23** nos contratos históricos do fluxo
  e **90/90** no conjunto coordenador/cadeia/linguagem natural/contexto.
  Regressão global controlada final: **6.645 passed, 1 skipped,
  13 deselected, 14 xfailed, 56 subtests passed**, zero falhas. Os mesmos oito
  testes de root bloqueados pela instância real passaram **8/8** com bypass de
  mutex somente no pytest.
- A compatibilidade de bool realmente legado continua temporariamente fora
  desse fechamento total; a frente musical paralela também não foi alterada.
  O objetivo desta etapa foi impedir que **resultado moderno explicitamente
  não comprovado** libere uma dependência posterior.

### Raiz de versionamento da supervisão neural — 21/09

- Base `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`; worktree
  paralela preservada, incluindo `modelo.py` da v29. Primeira fronteira RED:
  leitores históricos recusavam duas dependências da linguagem diferentes.
  Reprodução direta, ultrapassando apenas a leitura para diagnóstico:
  `conferir_casos` falha por **alinhamento divergente**, não por import.
- Falsificadas as hipóteses de corpus alterado e de mudança somente nos hashes:
  os lotes mantêm seus SHA-256, mas há **144 divergências** em cada lote
  (mesmos casos, não 288 casos únicos). Em 96 mudou apenas a referência de
  leitura; em 48 também mudaram segmentação e offsets relativos. O diff da
  linguagem mostra reconhecimento ampliado de recusa e moldura de necessidade.
  Os arquivos de linguagem são iguais a HEAD; não atribuir o bloqueio ao SOL.
- Contrato: **anotação independente preservada não implica leitura histórica
  equivalente**. Owner offline `revalidar_perfil_v4.py` ganhou reprojeção
  explícita, mantendo o replay estrito como padrão. Compara supervisão completa
  em coordenadas literais absolutas: atos, âncoras, alvos/papéis, relações,
  texto e metadados; valida referências, flags e spans antes da comparação.
  Normalização não literal exige outro perfil. Não utiliza previsão como gold.
- Via nova limitada aos pares de dependências revisados e ao manifesto exato
  das divergências observadas. Mudança futura, corpus modificado, reserva,
  identidade duplicada, alteração de supervisão ou corrida de arquivo abortam.
  Preserva protocolos, folds e leitores antigos; não altera resultados antigos.
  Relatório declara `compatibilidade_no_corpus=false`, supervisão preservada,
  classificador não reavaliado e runtime não validado.
- Os testes dos algoritmos atuais agora pedem a reprojeção explicitamente.
  Não enfraquecidas as asserções de comportamento; testes negativos continuam
  exigindo bloqueio dos leitores históricos. Asserções específicas protegem
  adulteração de atos, alvos, âncoras, relações, referência e autoridade.
- **53 testes focados passaram** antes dos controles adicionais. CLI offline
  real executada com sucesso, sem fit: **1.176 casos únicos**, folds idênticos.
  Evidência: `memoria/neural/experimentos/reprojecao_literal_v4_20260921/relatorio.json`.
  Regressão neural ampla após os controles adicionais: **1.425 aprovados,
  1 skipped, 5.220 deselected**, zero falhas/erros, 105,63 s
  (`pytest scripts/tests -k neural -q --tb=short`). Os 23 bloqueios anteriores
  foram resolvidos. Isso não é suíte global, runtime da assistente ou prova
  de qualidade da v29. `compileall` focado e `git diff --check` passaram.
- **Observação separada, associada à fronteira F1, ainda não diagnosticada:**
  no caso `rel_v4_necessidade_apps_e0_t0_q0_recusa_pedido`, a cláusula
  “não é para abrir o aplicativo pelvora” aparece como `conversa`, sem veto,
  enquanto a anotação mantém `recusa`. O pedido subsequente é separado.
  Não houve executor nessa prova; não concluir que a ação proibida foi executada.
  Próxima investigação deve testar recusa isolada/mista em domínios distintos
  no owner de modalidade e no consumidor de autoridade, antes de corrigir.
- **Fechamento da observação F1 — recusa declarativa “não é para…”:** o RED foi
  reproduzido em app, arquivo e IoT; 4 casos falharam com 20 vizinhos verdes.
  A raiz ficou em `analisar_protecao_operacional`: a moldura declarativa
  `não é/eh para|pra + infinitivo operacional` não possuía leitura geral.
  O contrato foi corrigido no owner de modalidade, sem regra privada por domínio.
  Interrogação continua pergunta; sem interrogação vira `recusa/cancelamento`.
  Em turno misto, o veto pertence somente ao segmento recusado, enquanto um
  pedido independente posterior continua autorizado. Teste do consumidor
  confirma que `processar_execucao_pratica_precoce` entrega somente
  `texto_operacional` do pedido permitido ao determinístico.
- O corpus histórico contém **72 nós** com essa moldura e gold `recusa`; após
  a correção, 72/72 são lidos como recusa com veto. A guarda de compatibilidade
  bloqueou a mudança de `modalidade_turno.py` antes de qualquer atualização.
  Replay explícito preservou supervisão literal e as quatro dobras: a diferença
  contra o snapshot histórico passou de 144 para **160 casos**, com as mesmas
  48 resegmentações. Os 16 deltas novos são recusas isoladas de apps/arquivos
  agora alinhadas ao gold; snapshot observado não foi promovido a gold.
- A reprojeção v1 foi preservada. Nova prova publicada em
  `memoria/neural/experimentos/reprojecao_literal_v4_recusa_declarativa_v2_20260921/relatorio.json`.
  Regressões: **25** testes focados de autorização/consumidor, **33** de
  reprojeção, **76 aprovados + 1 skipped + 22 subtests** em modalidade/autoridade,
  e **1.426 aprovados, 1 skipped, 5.226 deselected** na suíte
  `pytest scripts/tests -k neural -q --tb=short`, zero falhas/erros.
  Isso não certifica runtime completo, qualidade da v29 nem execução real.
- Escopo da etapa de reconciliação anterior: um módulo de infraestrutura
  experimental, quatro módulos de testes e documentação. Naquela etapa,
  linguagem de produção, modelo SOL, pesos ativo/v27, configuração e reserva
  v29 permaneceram intactos. A investigação F1 acima alterou depois somente o
  owner de modalidade; não houve commit, promoção ou ativação.

### Reconciliação das frentes neurais — 21/09

- Base `bd94bc3e`, mudanças paralelas preservadas. Após a cópia da v29, o
  consumidor operacional permaneceu mas perdeu a API opcional de projeção:
  **36 falhas TypeError**. Reposto `rotulos_permitidos` em
  `comparar_ocorrencias_v4.py`, sem mudar o catálogo padrão. README agora mantém
  tanto a v29 do SOL quanto a retomada de cobertura/IoT/mídia. Nenhum patch em
  `modelo.py` entregue pelo SOL; SHA-256 preservado
  `58af0476a9907870ed471e5d0e4e91e104213d32f936b199d51e34efd960ef6a`.
- Testes v29 citados no handoff ausentes da cópia local: seis casos de contrato
  escritos no teste existente para integral/híbrido, OOF, grupos, serialização,
  encoder ausente e preservação da base. Encoder sintético, sem certificar
  qualidade linguística. **75 testes focados passaram**, mais **93 regressivos**
  de coleta/revisão/protocolo/preparação. Modelos ativo/v27 com hashes preservados.
- Suíte neural ampla: **1.384 aprovados, 1 skipped, 6 falhas, 21 erros**. Quatro
  falhas vinculadas à raiz já conhecida de caminhos pós-reorganização: fixture
  de revisão contextual ainda apontava para `tests/fixtures`. Caminho ajustado,
  **32 testes do módulo passaram**, nenhuma expectativa relaxada.
- **Pendência separada de compatibilidade histórica:** 21 erros e duas falhas
  restantes param nos hashes do corpus v4. `modalidade_turno.py` e
  `normalizacao_linguagem.py` são iguais a HEAD e diferem dos hashes exigidos
  pelo protocolo antigo. Não causada pela interface reposta nem atribuída ao
  SOL. A via de revalidação existente só autoriza outra revisão antiga do
  normalizador. Falta provar compatibilidade integral do alinhamento atual;
  nenhuma guarda, baseline ou reserva foi alterada. Não declarar suíte verde.
- Sem treino de produção, promoção, interferência na sessão ou commit. Fits
  executados apenas pelos testes com dados sintéticos e artefatos temporários.

### Continuação: coleta recuperada e preservação de foco, 21/09

- Base atual `bd94bc3e3a29c49906dc603f9ca1540310ca3274`. Recuperação do
  analisador já incorporada por commit externo; AST das funções comparada com
  `c8b4c26`, sem diferenças. **85 testes aprovados**; **6.537 testes coletados
  sem erro** antes da nova regressão de foco. Não equivale a executar a suíte
  global nem a validar/promover o modelo histórico.
- Nova observação do Pedro em `../erros/erros_encontrados.md`: troca de faixa
  ativa YouTube e interrompe estudos. Registrada como **P17**, raiz própria de
  transporte da restrição de foco, sem misturar com as raízes conversacionais.
- Preservadas alterações de empacotamento e o relato do usuário. Pedro informou
  trabalho paralelo do ChatGPT: verificar sobreposição antes de editar e avisar
  imediatamente se houver evidência de risco. Nenhum conflito observado nos
  arquivos deste candidato; isso não é auditoria de todo trabalho paralelo.

### Continuação após reorganização do repositório, 21/09

- Base `d268a51`, preservada a nova organização. P09: ajustados pytest,
  imports/caminhos relativos dos testes movidos, sonda e catálogo DEV Console.
  **60 testes focados aprovados**; seleção ampliada **3.018 aprovados,
  14 xfailed e 30 subtestes**. Não é certificação da suíte global.
- Coleta global bloqueada por dependência ausente:
  `analisar_neural_v27_list_windows_caos`, importada pelo teste homônimo.
  **6.526 testes coletados e um erro**. Não removido nem enfraquecido o teste;
  analisador não restaurado sem conferir sua finalidade e versão.
- Encerramento da sonda: repetição com receipt do processo pai resultou em
  **código 0 e stderr vazio**. Código 1 histórico não reproduzido, causa aberta;
  nenhum patch especulativo no lifecycle. O log genérico que anuncia reinício
  mesmo ao concluir roteiro é impreciso, não prova reinício real.
- Evidência e limites em `../raiz/MAPA_RAIZES_CONVERSA.md`, seção de
  infraestrutura após reorganização. Documentos movidos pelo usuário preservados.

Este é o índice central dos problemas encontrados enquanto corrigimos outros
problemas. Serve para não perder achados, não misturar causas e deixar claro o
que falta. Os relatórios ligados abaixo preservam o diagnóstico detalhado.

O preenchimento inicial usa os relatórios de 12–15/09 e as validações da última
rodada. **Não é uma auditoria exaustiva nem uma nova execução dos testes.**
Uma ocorrência antiga permanece datada até ser revalidada.

## Como manter este arquivo

- Ao encontrar um problema lateral, registrar aqui antes de desviar da correção atual.
- Manter o ID do item; atualizar seu estado e acrescentar evidências, sem apagar o histórico.
- Separar sintoma de causa: várias falhas podem ter a mesma raiz; isso precisa ser provado.
- Informar se a evidência é de runtime, integração ou teste unitário.
- Só marcar uma correção como validada no escopo depois de registrar o teste e seus limites.
- Impacto indica risco, **não muda automaticamente a ordem do trabalho** nem autoriza ações destrutivas.
- Nunca copiar credenciais, tokens ou conteúdo pessoal desnecessário para este índice.
- Ideia futura não é defeito e não significa implementação aprovada.

Estados usados: **a investigar**, **reproduzido**, **parcial**, **limite não validado**,
**adiado**, **validado no escopo** e **ideia guardada**.

## Visão rápida das pendências

| ID | Assunto | Estado | Impacto |
| --- | --- | --- | --- |
| P01 | Explicações ruins sobre como usar capacidades | Parcial: catálogo preservado; qualidade ainda aberta | Coerência e confiança |
| P02 | Recomendações técnicas sem evidência suficiente | Adiado; RED histórico aberto | Alto: informação técnica inadequada |
| P03 | Confirmação de playlist antes do receipt | Corrigido em 22/09; integração da composição real e disco temporário validada; sessão completa pendente | Alto: confirmação prematura |
| P04 | Divergência no contador de ADD do teste composto | Encerrado em 22/09: instrumentação observava o wrapper legado; porta detalhada executava e persistia | Medição corrigida sem alterar produção |
| P05 | Presença não cede na transição da entrada para o turno | Reproduzido em teste de integração | Interferência na fala do usuário |
| P06 | Ponto de extensão em nome de arquivo | Reproduzido em teste; xfail conhecido | Interpretação do alvo |
| P07 | Continuidade na rota exclusivamente de áudio | Limite não validado | Possíveis lacunas de histórico |
| P08 | Credencial em logs históricos do Chrome | Parcial: saída nova corrigida | Alto: artefatos sensíveis |
| P09 | Novos testes ficam ignorados pelo Git | Regra corrigida e validada em 21/09; sem staging | Revisar fontes antes de versionar; artefatos já rastreados exigem ação separada |
| P10 | Falso positivo de fundamentação em citação | F1: exemplos com “pedir para” também validados em 21/09; escopo mais amplo aberto | Proteção não deve apagar instruções válidas |
| P11 | Pedido de informação confundido com afirmação de estado | Validado no escopo; ver C08 | Fallback desnecessário corrigido nos casos cobertos |
| P12 | Pergunta de procedimento sem natureza operacional reconhecida | Classificação validada no escopo C11; resposta final ainda falha | Reparo posterior separado em P16 |
| P13 | Nome de aplicativo não recupera seu domínio no catálogo | Recuperação validada no escopo C12 | Resposta final ainda afetada por P10 |
| P14 | Resposta prioritária IoT troca ação e dispositivo | Corrigido e validado no escopo C13 | Qualidade mais ampla da autoria continua em P01 |
| P15 | Falha técnica tratada como pedido ambíguo | Validado no escopo de propagação; limites de conclusão registrados | Causa da latência não investigada |
| P16 | Reparo de explicação presume relato de ação passada | Validado no escopo C15 | Objetivo e fonte preservados; qualidade geral ainda em P01 |
| P17 | Restrição de foco perdida no transporte ao Chrome | Troca musical confirmada por Pedro; fallback compartilhado protegido e testado localmente | Preservação do foco também nas rotas alternativas |

A frente atual é **P01**. O corte do catálogo (C07) e o falso reparo P11 (C08)
foram tratados separadamente; falta melhorar a realização da explicação. A investigação
de recomendações **P02** foi adiada para não bloquear indefinidamente a rede.
Este índice não altera essas decisões e não promove a rede neural.

## Pendências detalhadas

### Organização por contratos — diagnóstico de 20/09

O [mapa causal da conversa](MAPA_RAIZES_CONVERSA.md) passa a orientar a próxima
etapa: F1 significado, F2 capacidade/fonte/escopo e F3 causa técnica. As famílias
não substituem os IDs nem significam que todos os itens têm uma única raiz.
P01 é abrangente; evitar contá-lo novamente como causa de cada subproblema.

Nesta auditoria, nenhum patch novo de produção: quatro REDs de negativas falsas
em música/sistema/IoT/navegador e um RED de exemplos no infinitivo confundidos
com obras: **cinco REDs, oito controles aprovados** e 261 regressivos anteriores
aprovados. O bruto da retomada já negava a capacidade; o verificador ainda
cortou as instruções, agravando a fala. REDs preservados sem xfail no teste
`test_coerencia_capacidade_documentada.py`. P15 também reproduzido localmente:
três categorias técnicas chegam à contingência como se faltasse clareza.
Próxima implementação: coerência documental compartilhada (F2), depois
propagação da causa técnica (F3), sem novo remendo específico para música.

**Experimento F2, 20/09 às 17:00:** projeção ampliada de contratos operacionais
testada e retirada por não demonstrar benefício global no runtime. Doze
respostas, zero comandos; negativas/promessas inadequadas e cortes ainda
presentes. Dados extras no prompt não corrigiram a conferência da resposta.
Cinco REDs comportamentais preservados; não declarar outra correção concluída.
Detalhes e artefatos no mapa causal. A regra de organizar por raiz foi gravada
no `AGENTS.md`; nenhuma alteração permanente nova em produção nesta rodada.

**F2, 20/09 às 22:10 — conferência validada no escopo, reparo ainda aberto:**
o mesmo comparador passou nas negativas de música, aplicativos, IoT e abas,
com predicados do snapshot canônico e sem ampliar o prompt inicial. Disponibilidade
não virou receipt nem autorização. Seleção ampliada: 2.913 aprovados, um RED
F1, 14 xfailed preexistentes e 30 subtestes; controles posteriores na seleção
focada: 58 aprovados e o mesmo RED F1. No replay pelo runtime real, a negativa
histórica foi detectada; o Qwen repetiu a contradição no reparo, que foi rejeitado.
A resposta final pediu clareza indevidamente (F3). Portanto, não encerrar P01:
há prova de bloqueio, não de recuperação da explicação. Próxima fronteira F2:
isolar influência do rascunho/histórico no reparo, sem empilhar instruções.
Captura `transporte_evidencia-20260920-221039-790886`; detalhes e escopo no mapa.

### P01 — Explicações de capacidade e instruções pouco coerentes

- **F2, 20/09 às 22:18:** ablação de 21 chamadas locais isolou duas cópias do
  conteúdo refutado no reparo (rascunho e trecho de diagnóstico). Retirar só
  histórico ou só uma cópia não eliminou a negativa; retirar ambas conservando
  histórico não a repetiu nas três amostras, embora restasse imprecisão.
  Corrigida a projeção no reparador compartilhado, sem aumentar prompt/orçamento
  ou alterar os executores. Quatro REDs por domínio passaram com a mesma regra;
  ampliado: 2.929 aprovados, um RED F1, 14 xfailed e 30 subtestes. Replay real
  reparou a negativa histórica para uma instrução de retomada, sem fallback ou
  comandos; 12/12 no avaliador mínimo não significa qualidade global. Captura
  `transporte_evidencia-20260920-221832-302877`. Paráfrases ainda escapam da
  conferência, IoT ainda transferiu checagem ao usuário e uma variação de PC
  foi cortada. Detalhes no mapa causal; P01/F2 continuam parciais. Próxima raiz
  priorizada: F3, conclusão coerente para falha técnica, não nova expansão neural.
- **C18, 20/09:** descrição de controle local sustentada pela documentação do
  turno não é mais confundida com disponibilidade de obra na plataforma PC.
  Quatro REDs causais passaram; seleção ampliada: 2.873 aprovados e 14 xfailed
  preexistentes. Replay da resposta histórica de volume no runtime preservou
  a frase inteira, sem comandos. A sonda terminou com 12 respostas e 11/12 no
  avaliador mínimo: a geração nova de retomada voltou a negar controle de áudio
  (turno 3). Próxima investigação: confrontar essa negativa com a documentação
  efetivamente entregue ao modelo. P01 permanece parcial; a regra C18 cobre uma
  família gramatical delimitada, não todas as paráfrases nem qualidade global.
- **Após C17, 20/09:** exemplos de comandos sobreviveram nas duas sondas.
  Separadamente, o replay de volume ainda teve a frase sobre sistema local/PC
  removida por `plataforma_sem_evidencia`. A geração nova de retomada chegou a
  negar controle de áudio apesar do catálogo, e IoT voltou a sugerir conferência
  manual de configuração. Esses achados impedem encerrar P01 ou usar o 12/12
  mínimo como prova de qualidade global. Próxima investigação delimitada:
  distinguir descrição de capacidade local de alegação sobre plataforma externa.
- **C16, 20/09:** catálogo passa a descrever limites com escopo, condição e
  responsável. Na projeção para autoria, a regra do envio remoto não é mais
  o limite textual único do sistema. Controle local e envio a outro PC ficam
  separados; releitura IoT é responsabilidade interna da Laylay. O formato
  textual legado é derivado das mesmas regras, sem cadastro duplicado.
  Sonda com geração nova confirmou documentação no HTTP e respostas de
  calculadora/volume sem exigir PC remoto. A fala IoT não pediu ao usuário
  que relesse o dispositivo. **Resultado final ainda parcial:** P10 apagou
  exemplos didáticos em quatro turnos; a frase sobre controle local de volume
  também foi cortada por `plataforma_sem_evidencia`. O modelo ensinou abrir o
  controle de volume, em vez de só pedir o ajuste: precisão geral ainda aberta.
- **19/09, após C15:** no reparo real de volume, o Qwen manteve a explicação,
  mas ainda acrescentou requisito de PC remoto. O verificador retirou essa frase
  (`plataforma_sem_evidencia`) e preservou a instrução. Na mesma sonda, IoT
  transferiu ao usuário a responsabilidade de reler o dispositivo. Próxima
  investigação: escopo dos limites e responsabilidades na documentação por
  capacidade/rota, sem retirar a proteção factual ou criar falas fixas.
- **Encontrado durante:** validação de recusas e continuidade do histórico.
- **Exemplo:** “como eu poderia pausar a música?” recebeu explicações de acesso
  ao player e digressões desnecessárias, apesar de a pergunta direta de capacidade
  ser respondida pelo catálogo local.
- **Comprovado:** desvio no runtime em sondas de 14–15/09. Não houve comando.
- **Atualização de 15/09, tarde:** a captura nas duas fronteiras provou perda do
  catálogo na compactação HTTP: presente no pedido/preparação, ausente no envio.
  C07 preserva a evidência nas rotas normal e rápida. O contrato de não execução
  não mudou; o problema não se resume à competência do Qwen ou ao histórico.
- **Ainda aberto:** a descrição geral das capacidades, agora entregue, não bastou
  para produzir uma instrução boa. A sonda posterior chegou a um fallback por P11.
  Portanto **P01 não está encerrado**, apesar do transporte corrigido.
- **Próximo passo após C08:** reavaliar a realização de instruções com o catálogo
  vivo, inclusive disponibilidade negativa, sem converter pergunta em autorização
  nem criar uma resposta fixa por habilidade. Na sonda de 17:19 a fala não teve
  fallback, mas incluiu “não preciso te ensinar nada”: qualidade e tom ainda RED.
- **Fechar quando:** explicações úteis e verdadeiras, com capacidade disponível e
  indisponível, passarem por contrastes e runtime sem execução não solicitada.
- **15–16/09 — candidato C09:** tarefa de autoria textual separada do planejamento,
  com documentação viva ligada ao texto/ID do turno. Sem fala fixa por habilidade;
  pergunta continua sem autorização e propostas indevidas continuam bloqueadas.
  Disponibilidade parcial, vários atos e referências não recuperadas conservam
  o fluxo completo. A personalidade-base não foi reescrita.
- **Resultado intermediário:** o Qwen passou a ensinar o pedido de pausa; a primeira
  sonda revelou que P10 apagava esse exemplo após a geração. Após o candidato C10,
  os turnos 1 e 2 da sonda de 15/09 às 18:50 chegaram inteiros ao chat. Essa sonda
  foi **interrompida após 8/12 respostas**, não é uma execução concluída.
- **Limites descobertos:** P12/P13 mantêm quatro REDs (duas entradas, rotas normal
  e rápida). P14 é uma resposta fixa anterior à LLM, portanto não se resolve com
  o prompt novo. Não declarar P01 globalmente corrigido.
- **Validação final de 16/09:** seleção ampliada com **1.307 aprovados e quatro
  falhas**, todas de cobertura P12/P13. Sonda completa de 12 mensagens: dez
  aprovações mínimas, duas falhas IoT e zero comandos. Exemplos de pausa/retomada
  preservados no chat; ofertas laterais, promessas e continuação presumida ainda
  impedem considerar a qualidade globalmente aprovada.
- **Evidência:** [histórico e sondas de 15/09](RELATORIO_COLETA_DEBUG_20260914.md#histórico-de-respostas-locais-e-continuidade--15092026).
  [Diagnóstico do corte e resultado parcial](RELATORIO_COLETA_DEBUG_20260914.md#capacidades-relevantes-no-transporte--15092026).

**23/09 — ensino multifonte, mesma raiz P01:** recuperação trouxe “vista
superior”, mas a fala “de baixo para cima” passou sem alerta pelo verificador.
Uma sonda de sete alegações com o Qwen acertou os rótulos, mas somente três
tinham índice/citação literal válidos; não integrar como portão de verdade.
Separadamente, a consulta de RGB de `planta` nasceu do detector IoT, não da
pesquisa factual. A guarda de ordem direta para cor livre passou em 34 testes
IoT, inclusive composição; ainda falta conversa completa no runtime. Evidência
e próximos controles em `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md` e
`scripts/analises/sonda_verificacao_ensino_com_fonte.py`.
Repetição real mostrou outra primeira fronteira: `operacao_explicita=iot` no
retrato por menção de “luz”, vetando pesquisa. A guarda no retrato fez a fonte
voltar ao plano sem comando; o extrator separou “com um exemplo” do tema. A
última sonda expirou no Qwen, então P01 permanece aberto e sem GREEN factual.

**24/09 — P01, auditoria didática em sombra:** a fala candidata pós-verificador
agora recebe um diagnóstico de segmentos, fontes do usuário e comparações
numéricas limitadas. A fala real do sensor é coberta textualmente, mas as
caudas sobre “garantir” umidade e “equilíbrio” ficam sem âncora literal e
pendentes de revisão. Mesmo trecho literal não é tratado como implicação. A
auditoria não muda fala, executor ou autoridade; 145 regressivos focados
passaram. Ainda falta sonda do Qwen no runtime real, revisão semântica da fala
entregue e solução para a composição de alegações adicionais. **P01 segue
aberto**; não contar esta observabilidade como correção de qualidade.

**24/09, sonda real P01:** com Qwen3:4b-instruct e IoT simulado, a geração
HTTP do último turno já incluiu causas/consequências não dadas pelo usuário;
o texto entregue foi idêntico. O payload continha cenário, foco, 15% e 20%,
falsificando falta dessas premissas como raiz desse turno. Auditoria em sombra:
8 segmentos sem âncora literal, 0 comparações locais, sem veto nem efeito.
Houve timeout no primeiro turno; o placar 2 passados/1 falha/1 alerta é
limitado pelo avaliador lexical. Artefatos e limites no plano de ensino.

**24/09 — contrato formal offline P01:** cobertura integral de spans e
citações de fonte registrada passam a ser verificáveis sem conferir verdade;
papel, atomicidade, condição e implicação continuam pendentes. Cauda sem fonte,
omissão, sobreposição, citação forjada e fonte da assistente são recusadas no
envelope de oito testes novos. Seleção conjunta: 192 passed. Sem promoção à
fala do runtime, veto ou executor; falta produtor e revisão semântica
multidomínio antes de atacar a geração RED.

**24/09 — piloto de proponente P01:** Qwen3:4b-instruct recebeu segmentos
fixos e fontes registradas para cinco falas (sensor real + quatro controles).
Cobriu índices, mas inventou citação no sensor/matemática, citou condição
omitida em floricultura/programação e marcou a cópia literal positiva como
`nao_factual`. O código recusou as citações inválidas; as localizadas
continuaram semanticamente pendentes. Recibo aritmético independente protege
somente a equação, não a conclusão sobre pessoas. 199 regressivos relacionados
passaram. Sem integração do piloto ao runtime; P01 permanece aberto.

**24/09 — grafo de premissas P01, ainda offline:** nove testes novos
conferem fontes, escopo, identidade dos referentes, valores literais e
condições separadas em sensor, programação e floricultura; seleção relacionada
de 49 testes passou. Citação literal pode estar ligada ao sensor errado:
sem revisão semântica, o grafo não aprova composição nem ação. Nenhuma mudança
na fala do runtime; próxima fronteira é validar vínculos, direção e condições
independentemente em casos inéditos. P01 permanece RED.

**24/09 — pistas de vínculo P01:** após validar a estrutura do grafo, a
auditoria offline sinaliza referente textual ausente, direção numérica
invertida e negação que impede leitura simples. RED reproduzido para “não
cair abaixo” antes do ajuste; 69 regressivos relacionados passaram. Pistas
textuais não certificam implicação nem condição satisfeita; nenhum efeito na
fala real. Próxima prova: gabaritos independentes e casos novos. P01 aberto.

**24/09 — gabarito local P01:** quatro cenários inéditos, com rótulos manuais
separados do auditor, expõem falso positivo de entidade/valor na mesma frase,
abstenção em correferência correta e condição omitida que o auditor não mede.
Gabarito não é revisão externa. RED estrutural de número com unidade separada
por espaço corrigido antes da medição; nenhuma promoção à fala, pesquisa,
treino ou ação. Próxima fronteira: revisor de relações e completude de
condições, seguido de produtor automático somente em sombra. P01 segue RED.

**24/09 — cobertura condicional P01, ainda offline:** a proposta agora é
confrontada com condições de referência anotadas separadamente, após validar
fontes e escopo. Cache, sensor e cultivo reproduzem omissões; duplicatas e
efeito divergente são controles negativos. O placar do cache passou de
`nao_medida` a `condicao_omitida`. Seleção de 86 testes relacionados passou.
Revisão não autenticada, conectivo `e/ou` não representado e semântica ainda
pendente; nenhuma influência na fala ou execução. P01 permanece aberto.

**24/09 — relação lógica P01, offline:** regras passam a representar
conectivo plano e direção da implicação, com padrão indeterminado. REDs de
`e` versus `ou` e `se` versus `somente quando` ficaram distinguíveis após
confronto com regras revisadas fora dos candidatos. Gabarito local de quatro
casos contém agora condições e relação tipadas; 94 testes relacionados
passaram. Condições completas e relação correta são métricas separadas.
Conectivos aninhados, revisão semântica independente e produtor em sombra
seguem pendentes; nenhuma fala, executor ou treino alterado. P01 aberto.

**24/09 — primeiro produtor P01 em sombra, RED na entrada estruturada:**
Qwen3:4b-instruct recebeu seis fontes inéditas com referentes e efeito fixos,
sem acesso ao gabarito separado. Cinco regras propostas falharam na estrutura
(operador/citação/unidade/valor incompatíveis); na sexta, a árvore mista foi
achatada apesar da instrução de abstenção. **0/6** alinhadas, sem inferir
qualidade de ensino ou uso real. Conferidor local: 10 testes focados e 36
testes de grafo relacionados passaram. Os arquivos e hashes do painel estão
no plano de ensino fundamentado. Primeira fronteira demonstrada: produtor de
condições, não o executor nem o comparador. Próxima prova: contrato de saída
decomposto e novo painel cego. Nenhuma alteração em produção, treino, fala ou
ação; P01 continua aberto.

### P02 — Recomendação técnica sem vínculo verificável com fontes

- **Encontrado durante:** correções dos relatos do Pedro sobre hardware e pesquisa.
- **Última evidência registrada:** 13/09. O modelo ainda recomendou uma peça com
  especificações não sustentadas mesmo recebendo instrução para não escolher sem base.
- **Estado:** adiado por decisão anterior do Pedro; candidato de prompt retirado.
  Não considerar as recomendações das sondas seguras para montagem ou compra.
- **Próximo passo quando retomado:** ligar requisitos informados → candidatos →
  fontes → afirmações; comparar atende/não atende/não comprovado. Reutilizar pesquisa
  e coordenação existentes, sem criar uma habilidade para cada peça.
- **Fechar quando:** faltas de dados, fontes contraditórias e pesquisa indisponível
  não produzirem especificações, compatibilidades ou pesquisas inventadas no runtime.
- **Evidência:** [relatório de recomendações e retirada do candidato](RELATORIO_CORRECOES_CONVERSA_20260912.md).

### P03 — Playlist: fala de confirmação anterior ao receipt

- **Encontrado durante:** regressão ampliada da correção de histórico, em 15/09.
- **Comprovado em teste:** o receipt aparece depois da chamada de voz (`4 < 3`
  falha). O teste alcança CREATE/ADD; não falha no import.
- **Contrato:** receipt confirmado antes da confirmação verbal de efeito.
- **Próximo passo:** rastrear a ordem no fluxo canônico de feedback e comparar
  a composição do teste com produção. Não afirmar que a falha de produção atual
  foi reproduzida apenas porque esse teste falhou.
- **Fechar quando:** sucesso, falha e idempotência publicarem resultados na ordem
  correta, com regressão de composição e prova no runtime.
- **Teste:** [test_red151_c3_guardiao_receipt_saida.py](../tests/test_red151_c3_guardiao_receipt_saida.py),
  `test_red151_c3_feedback_simples_registra_receipt_antes_da_fala`.
- **Controle:** a falha persistiu com o candidato de histórico desativado em memória.
  Detalhes no [relatório de 15/09](RELATORIO_COLETA_DEBUG_20260914.md).

### P04 — Playlist: contador do ADD diverge do resultado composto

- **Encontrado durante:** a mesma regressão de 15/09; relacionado a P03, mas
  **não há prova de raiz compartilhada**.
- **Comprovado em teste:** a playlist e a faixa passam pelas asserções anteriores;
  depois, `add_final` esperado como `1` vale `0`.
- **Não concluir:** que a faixa deixou de ser salva. A falha observada é no contador.
- **Próximo passo:** verificar se a instrumentação acompanha o executor real ou
  se há uma divergência de composição/fluxo. Não mudar a expectativa só para passar.
- **Fechar quando:** a cadeia materialização → ADD → receipt → contador tiver
  explicação causal e validação coerente.
- **Teste:** [test_red151_runtime_canonico_c3.py](../tests/test_red151_runtime_canonico_c3.py),
  `test_red151_c3_runtime_canonico_146_151_cria_salva_responde_sem_llm`.
- **Controle:** também persiste sem o candidato de histórico em memória.

### P05 — Presença na transição entre entrada aceita e turno criado

- **Estado em 25/09/2026:** resolvido na composição atual por
  `PrioridadeInteracaoUsuarioRuntime`: ouvido, coordenador e ponte compartilham
  o mesmo owner, e o diretor bloqueia presença enquanto há claim ativo.
  Os testes antigos omitiam esse owner na montagem manual; foram atualizados
  sem retirar as asserções de preempção. Os testes de composição real para STT
  e handoff também passaram na suíte completa (7.394 aprovados). Isso não é
  evidência de que o código histórico de 15/09 já tivesse o contrato.
- **Encontrado durante:** regressão de 15/09.
- **Comprovado em teste:** o evento de presença retorna `proposta_cognitiva`
  quando o teste espera `bloqueada`, depois da entrada aceita e antes do turno.
- **Contrato esperado:** a entrada já aceita do usuário deve ter prioridade
  nessa janela, não apenas depois da criação do plano.
- **Próximo passo:** mapear quem possui essa prioridade e sua propagação entre
  aceite da entrada, agendamento e diretor de presença; confirmar a composição real.
- **Fechar quando:** corrida controlada e runtime preservarem a prioridade sem
  silenciar definitivamente a iniciativa legítima.
- **Teste:** [test_red_p1h4_handoff_entrada_turno.py](../tests/test_red_p1h4_handoff_entrada_turno.py),
  `test_red_p1h4_entrada_aceita_preempta_presenca_antes_do_turno`.
- **Controle:** persiste sem o candidato de histórico em memória.

### P06 — Segmentação de nomes como `antonio.txt?`

- **Encontrado durante:** testes de pedidos modais e recusas, em 14/09.
- **Evidência registrada:** o segmentador corta no ponto da extensão; xfail conhecido.
- **Próximo passo:** preservar a estrutura do nome/caminho durante a segmentação,
  sem transformar toda pontuação em texto literal nem usar ausência de `?` como autorização.
- **Fechar quando:** nomes com extensão, caminhos, perguntas e frases compostas
  preservarem alvo e modalidade, sem regressão de segurança.
- **Evidência:** [registro de pedidos modais e xfails](RELATORIO_COLETA_DEBUG_20260914.md).

### P07 — Histórico sem publicação textual confirmada

- **Encontrado durante:** definição dos limites da correção C02, em 15/09.
- **Estado:** limite de cobertura, **não bug de áudio já reproduzido**.
  O novo registro usa confirmação dos canais textuais; aceite na fila de voz
  não prova que alguém ouviu a fala.
- **Próximo passo:** rastrear o caminho exclusivamente de áudio e o evento real
  de entrega, incluindo cancelamento, interrupção, fala tardia e troca de chat.
- **Fechar quando:** um contrato de entrega apropriado sustentar o histórico
  dessa rota sem registrar fala cancelada como entregue.
- **Evidência:** [limites da correção do histórico](RELATORIO_COLETA_DEBUG_20260914.md#histórico-de-respostas-locais-e-continuidade--15092026).

### P08 — Logs antigos podem conter credenciais

- **Encontrado durante:** sonda Chrome de 14/09.
- **Comprovado:** uma URL de callback com token foi impressa antes da sanitização.
  Não copiar seu conteúdo para este arquivo.
- **Já corrigido:** sanitização na saída do handler; ver C05.
- **Pendente:** os artefatos antigos não foram apagados nem higienizados; não
  compartilhar ou versionar logs brutos. A correção não foi uma auditoria global.
- **Próximo passo:** delimitar artefatos afetados e combinar com Pedro o tratamento
  de material sensível e eventual revogação da credencial, sem usá-la.
- **Fechar quando:** tratamento dos artefatos e da exposição estiver documentado;
  sanitizar logs novos, sozinho, não encerra esse item.
- **Evidência:** [achado de segurança e sanitização Chrome](RELATORIO_COLETA_DEBUG_20260914.md).

### P09 — Testes novos fora do versionamento

- **Verificado em 15/09:** `git check-ignore -v` aponta `.gitignore:10:tests/`
  para `test_historico_turnos_locais.py` e `test_recusas_alteracao_canonica.py`.
- **Impacto:** os arquivos existem e executam localmente, mas novos testes podem
  não entrar num commit normal. Isso não apaga os testes já rastreados.
- **Próximo passo:** revisar a política de ignore de testes separadamente, mantendo
  artefatos e dados sensíveis excluídos. Nenhuma regra foi alterada nesta organização.
- **Fechar quando:** regressões necessárias puderem ser versionadas com segurança,
  sem adicionar arquivos em massa nem expor dados de teste pessoais.
- **21/09, autorizado por Pedro:** removida a regra ampla `tests/`. Mantidos
  segredos, playlists, memória, resultados e caches ignorados; adicionados
  `*.caos-backup`, backups ocultos identificados, `/conversa.md` e diretórios
  de binários `runtime_llm/cpu/` e `runtime_llm/vulkan/`. Licença preservada.
  Retirada a exceção inoperante de terminal.log sob diretório ignorado.
  Doze contrastes `git check-ignore --no-index` provam código/exemplos visíveis
  e dados locais ignorados. Novos testes ficam visíveis, não adicionados ao Git.
- **Organização autorizada:** 21 roteiros apagados recuperados de HEAD em
  `scripts/roteiros/`; o caos restante foi movido da worktree, preservando seu
  conteúdo. Total 22. Alterações apagadas que não estavam no Git não são
  recuperáveis por esse procedimento. Loader aceita caminho legado da raiz
  somente quando ausente; arquivo explícito existente tem prioridade; caminho
  ausente fora da raiz não é substituído. Sonda usa o caminho novo; imports e
  caminho da fixture do caos ajustados, sem executar o caos.
  104 testes de organização/loader/fixture/P15 aprovados. Guia em
  `scripts/roteiros/README.md`. Outros analisadores/aplicadores apagados não
  foram restaurados fora do escopo de roteiros.
- **Limite do ignore:** continuam rastreados 306 arquivos em resultados,
  103 em runtime_llm, backup de playlists, conversa.md e três backups de código
  (estes últimos já removidos da worktree pelo usuário). Não houve `git rm`,
  staging, commit, exclusão de dados locais ou reescrita de histórico. Ignore
  não desversiona conteúdo existente; revisão do índice é trabalho separado.

### P10 — Citações confundidas com conteúdo que exige fundamentação

- **Última evidência registrada:** sonda de 13/09 tratou uma citação de estado
  emocional como obra; ainda estava aberta naquele relatório.
- **Estado atual:** requer revalidação após as mudanças posteriores nos guardiões.
  Não presumir que é a mesma raiz das recusas já corrigidas.
- **Próximo passo:** recuperar o turno e verificar a primeira classificação incorreta,
  contrastando citação, transformação textual e afirmação factual independente.
- **Fechar quando:** essas operações forem distinguidas sem liberar fatos inventados.
- **Evidência:** [limites das sondas de reparo parcial](RELATORIO_CORRECOES_CONVERSA_20260912.md).
- **Revalidação 15/09:** a resposta HTTP “Para pausar a música, basta dizer
  'pausa a música'” foi aceita na preparação, pesquisada como obra e cortada no
  verificador final. Captura `transporte_evidencia-20260915-184447-325549`;
  roteiro `roteiro_recusas_autoria-20260915-184448-437661`, turno 10.
- **Candidato C10:** extrator compartilhado distingue exemplos de enunciado de
  títulos candidatos. Validação factual continua examinando dados externos ao
  exemplo; uma citação didática não dispensa a verificação da frase inteira.
  A variante indireta “pedir para …, por exemplo” reutiliza o classificador
  canônico para reconhecer o exemplo, sem tratá-lo como fala autorizante.
- **Regressão detectada e corrigida durante validação:** retirar o título candidato
  também retirava o gatilho factual de uma data externa à citação. Separados
  `contem_citacao_destacada` e `extrair_titulos_citados`; o teste existente de
  metalinguagem/data voltou a passar sem alteração de expectativa.
- **Escopo:** citações didáticas explícitas, não toda citação emocional ou toda
  metalinguagem. O caso histórico original de 13/09 ainda requer revalidação.
- **Validação de 16/09:** 27 contrastes próprios; 42 aprovados com metalinguagem.
  Exemplos de pausa e retomada preservados na geração real e entrega ao chat da
  sonda `roteiro_explicacao_capacidades-20260916-084558-409596`.
- **Novo limite às 09:37:** “abrir o programa 'Calculadora'. Por exemplo:
  'abre a calculadora'.” retorna dois títulos no extrator; o runtime pesquisou
  Calculadora na Wikipédia e substituiu a explicação. Nome de entidade citado e
  exemplo em frase separada não são cobertos por C10. Não corrigido junto com C12.
- **C14, 19/09:** separados os papéis de exemplo de enunciado, referência
  operacional tipificada e obra candidata. Nome de recurso deixa de ser título,
  mas não tem datas/medidas mascaradas nem comprova estado. “Programa” requer
  moldura operacional para não liberar títulos de rádio/TV. Exemplo na frase
  seguinte exige orientação de pedido imediatamente anterior e leitura canônica
  do trecho como pedido/consulta; não libera qualquer citação após “por exemplo”.
- **Validação:** oito REDs causais → GREEN; 48 testes de citações ao final.
  Seleção ampliada: **2.801 aprovados, 14 xfails preexistentes, 30 subtests**.
  Replay da resposta histórica no processo real chegou inteiro ao chat;
  geração nova também preservou a instrução e manteve verificação de fatos
  adicionais. O caso emocional original de 13/09 não foi revalidado.
- **Novo limite em 20/09, durante C16:** a sonda
  `roteiro_explicacao_capacidades-20260920-085230-637670` voltou a pesquisar
  exemplos como títulos: “como em 'abre a calculadora'”, “pedir para mim:
  'ligue a lâmpada'”, “Exemplo: 'Laylay, desligue o ventilador'” e “Por exemplo:
  'Laylay, aumente o volume'”. A primeira frase da explicação da lâmpada foi
  apagada, restando apenas a condição de configuração. Captura HTTP:
  `transporte_evidencia-20260920-085228-787217`. Guardião não alterado em C16.
  Próxima fronteira: distinguir esses exemplos com contexto e vocativo, sem
  liberar títulos reais ou executar o texto citado; não ampliar listas de
  frases cegamente nem usar o placar mínimo como prova de resposta boa.
- **C17, 20/09:** 11 REDs reproduzidos antes do patch. A moldura de destinatário
  (“pedir para mim”), o conector de exemplo e a referência tipificada entre
  verbo e exemplo não eram preservados. Além disso, o exemplo citado precisava
  passar pelo classificador operacional; “aumente o volume” retorna natureza
  `nenhuma`. Reutilizado o reconhecedor canônico de vocativo, apenas sob moldura
  didática, sem alterar a gramática de execução ou conceder autorização.
- **Validação C17:** 68 testes de citação, incluindo três de integração com
  composição/estado/verificador reais e transporte de pesquisa observado;
  título real continua sendo pesquisado. Seleção ampliada: 2.849 aprovados,
  14 xfails anteriores e 30 subtestes. Dois replays no runtime completo (lâmpada
  e volume) preservaram os exemplos no chat, sem pesquisa de obra; demais
  chamadas ao Qwen tiveram geração nova. Ambas as sondas: 12 respostas e zero
  comandos. Plataforma/local é outra fronteira, não corrigida em C17.
- **F1, 21/09 — conteúdo citado de pedido:** o mesmo extrator não reconhecia
  a preposição em “pedir para 'tocar a música'”. A primeira fronteira RED era
  o papel da citação, antes da pesquisa e do corte factual. Treze REDs causais
  reproduzidos em música, aplicativos, IoT, agenda e verbos não executáveis.
  Corrigida somente a moldura compartilhada de `pedir/peça para/pra` seguida
  imediatamente do conteúdo citado; sem lista privada de ações ou autorização.
  “Pedir para tocar 'Noite Inventada'” continua candidato a título; fatos externos
  à citação continuam exigindo evidência. Não é liberação de qualquer aspas.
- **Validação F1:** 142 testes focados aprovados; seleção ampliada **3.002
  aprovados, 14 xfailed preexistentes e 30 subtestes aprovados**. Trecho
  instrucional histórico preservado inteiro no runtime:
  `roteiro_explicacao_capacidades-20260921-092057-398886`, turno 3;
  captura `transporte_evidencia-20260921-092056-114513`. É replay de recorte
  controlado, sem a negativa final de F2, não geração nova nesse turno.
  Doze respostas, zero comandos e 12/12 no avaliador mínimo. Sem pesquisa de
  títulos ou reparo nessa coleta. Qualidade global e equivalência operacional
  entre “tocar” e “retomar” não são provadas por preservar o enunciado.
  Caso emocional de 13/09 permanece pendente; ver mapa causal para limites.
- **F1 original, revalidação em 21/09 às 09:29:** localizado o turno 4 de
  `roteiro_reparo_parcial_conversa-20260913-073420-186234`. “Escutar o que você
  tá pensando — mesmo que seja só um 'estou triste' ou um 'cansado'” ainda era
  tratado como obra. Dez REDs reproduzidos; candidato no mesmo owner preserva
  exemplos de conteúdo discursivo, sem exceção para emoção ou título específico.
  Focado: **133 aprovados**. Ampliado: **3.017 aprovados, uma falha por roteiro
  ausente, 14 xfailed e 30 subtestes**. **Runtime pendente:** diversos roteiros
  foram removidos paralelamente durante a tarefa; a sonda não pôde carregar
  `roteiro_reparo_parcial_conversa.py`. Remoções preservadas, sem restauração.
  Não encerrar P10 antes da prova real; detalhes e artefatos no mapa causal.
- **Prova após reposição, 21/09 às 09:41:** sonda
  `transporte_evidencia-20260921-094144-781221`, roteiro
  `roteiro_reparo_parcial_conversa-20260921-094145-775708`. Replay integral da
  resposta histórica no turno 4: conteúdo preservado sem pesquisa de obra ou
  corte; terminal acrescentou ponto depois do emoji, conversa.md manteve original.
  Quatro respostas, zero comandos. Seleção ampliada **3.018 aprovados,
  14 xfailed e 30 subtestes**. P10 histórico validado nesse contrato, não toda F1.
  Processo retornou código 1 apesar dos relatórios completos e `atexit_concluido`;
  causa ainda não provada, sem falha nativa registrada. Não declarar encerramento
  limpo nem encobrir isso com o placar 4/4. Detalhes no mapa causal.

### P11 — Pedido de informação tratado como estado afirmado

- **Descoberto em:** 15/09, na validação real da preservação do catálogo (P01/C07).
- **Observado:** “me diga o nome da música ou o app que tá rodando, para eu te
  ajudar a localizar” foi marcado como `resultado_operacional_sem_evidencia`.
  O reparo também foi rejeitado e a resposta virou “Dá pra responder, mas agora
  seria no chute. Explica só um pouquinho melhor?”.
- **Primeira fronteira isolada:** o detector de resultados narrados em
  `cognicao/guardiao_alegacoes.py` trata o trecho subordinado “tá rodando” como
  afirmação independente. O pedido de informação não comprova um estado,
  mas também não deve ser interpretado como observação própria da Laylay.
- **Controles reproduzidos:** “me diga qual app está rodando” passa;
  “o app está rodando” continua corretamente bloqueado sem evidência.
  A formulação longa acima falha também chamando o detector diretamente,
  sem LLM, comandos propostos ou transporte. Não remover o guardião de estados.
- **Próximo passo:** RED contrastivo de escopo do pedido de informação; incluir
  orações coordenadas, afirmação posterior e efeitos realmente inventados.
  Reutilizar o contrato canônico de incerteza/pedido de informação.
- **Fechar quando:** perguntas e pedidos subordinados legítimos sobreviverem
  sem liberar alegações independentes; regressivos e runtime sem esse fallback.
- **Evidência:** [sonda e diagnóstico de 15/09](RELATORIO_COLETA_DEBUG_20260914.md#capacidades-relevantes-no-transporte--15092026).
- **Escopo:** registrado, não corrigido junto com C07. A qualidade da instrução
  sobre a capacidade continua em P01 e não será resolvida só liberando essa fala.
- **Atualização posterior — C08, 15/09:** corrigido o reconhecedor compartilhado
  para pedidos nominais (“me diga o app que…”), preservando nomes coordenados.
  O guardião delimita cada ocorrência pelo conjunto de estados/resultados já
  analisados; outra alegação não herda a permissão linguística do pedido anterior.
- **Validação:** 44 contrastes novos; seleção ampliada **918 passed**. A fala
  histórica completa passou pela preparação e verificação final sem reparo,
  tanto sem comandos como com a proposta de pausa original, que é descartada.
- **Prova da composição real:** replay explícito da resposta HTTP histórica
  no processo da Laylay entregou a fala integral sem reparo/fallback nem comando
  executado. O turno de replay **não é nova geração do Qwen**. A sonda separada
  com geração real passou 18/18, mas não repetiu a subordinada histórica.
- **Limites:** não é análise irrestrita de português nem liberação geral de
  orações coordenadas; ambiguidades continuam conservadoras. Preservar uma fala
  não certifica que sua orientação ou tom sejam bons (P01).
- **Detalhes:** [correção e validações de P11](RELATORIO_COLETA_DEBUG_20260914.md#pedido-de-informação-não-é-alegação-de-estado--p11--15092026).

### P12 — Perguntas de procedimento sem natureza reconhecida

- **Descoberto em:** testes contrastivos de C09, 15/09.
- **Reproduzido:** “como eu poderia aumentar o volume?” é `pergunta`, sem
  autorização, mas `natureza_acao=nenhuma`. “Me ensina como aumentar o volume”
  é conversa genérica. O catálogo recupera sistema, mas o contrato não tem uma
  interpretação procedural canônica para selecionar a tarefa específica.
- **Primeira fronteira:** classificação, antes da geração; nenhuma alteração
  em `modalidade_turno.py` foi feita nesta rodada.
- **Próximo passo:** estudar a moldura de explicação na classificação canônica,
  com pedidos reais, perguntas de estado, hipóteses e textos citados como controles.
  Não adicionar um parser privado de volume no preparador de prompt.
- **RED preservado:** `test_explicacao_capacidades_sem_execucao.py`, duas rotas.

- **Atualização C11, 16/09:** a moldura de procedimento seguida de infinitivo
  agora é reconhecida na proteção operacional compartilhada antes das listas
  de ações. Não adiciona verbos à autorização nem atesta capacidades. Hipóteses,
  negações e transformações conservam precedência. É uma gramática limitada,
  não um analisador irrestrito de português.
- **Prova:** 36 REDs novos na primeira fronteira → GREEN; 15 controles negativos
  e de comandos mantidos. Volume passou nas duas rotas de documentação. Seleção
  ampliada: **2.556 aprovados, duas falhas P13, 14 xfails preexistentes e 30
  subtests aprovados**. Não foi a suíte global.
- **Runtime:** turno 11 de `roteiro_explicacao_capacidades-20260916-085853-170785`
  reconheceu o procedimento e enviou documentação de sistema no HTTP real.
  A fala final ainda virou contingência após reparo rejeitado; P16 registra essa
  fronteira posterior. Corrigir a classificação não encerrou P01.

### P13 — Recuperação do catálogo perde domínio quando só há nome de app

- **Descoberto em:** testes contrastivos de C09, 15/09.
- **Reproduzido:** “como eu poderia abrir a calculadora?” já é instrução/explicação
  sem autorização, mas o seletor por termos não recupera sistema: “calculadora”
  não é “app/programa/janela” e a pergunta não contém comandos executáveis.
  “Como eu faria para abrir um programa?” serve de controle e passa.
- **Primeira fronteira:** recuperação do catálogo, não capacidade do executor.
- **Próximo passo:** reutilizar resolução de entidades/capacidades para consulta
  documental sem autorização; não cadastrar uma exceção para cada aplicativo.
- **RED preservado:** `test_explicacao_capacidades_sem_execucao.py`, duas rotas.

- **Atualização C12, 16/09:** o mapa consulta os aliases do `APPS_MAP` real por
  callback tardio, sem copiar a lista nem chamar executores. Referências completas
  selecionam sistema; não provam instalação, abertura ou disponibilidade.
  Ausência/falha da fonte mantém a recuperação anterior por termos.
- **Validação:** quatro REDs causais com a declaração/factory extraídas de
  `laylay.py` → GREEN; nove testes novos no total. As duas rotas de explicação
  usam essa composição, não um mapa isolado sem a dependência de aliases.
  Seleção ampliada: **2.567 aprovados, 14 xfails preexistentes e 30 subtests**.
- **Runtime:** captura `transporte_evidencia-20260916-093745-215501`, turno 4 de
  `roteiro_explicacao_capacidades-20260916-093746-337804`: documentação de sistema
  entregue no HTTP ao Qwen, que explicou como pedir a abertura. O verificador
  pesquisou “Calculadora” como título e substituiu a fala. Recuperação GREEN,
  fala final RED em P10; P01 continua parcial.
- **Limites:** recuperação lexical de aliases, não desambiguação universal nem
  descoberta de apps instalados. Disponibilidade e autorização não mudaram.

### P14 — Explicação prioritária IoT substitui ação e alvo

- **Descoberto em:** sonda real de explicações, 15/09, turnos 6 e 7.
- **Reproduzido:** perguntar como ligar a lâmpada ou desligar o ventilador recebe
  “É só me pedir diretamente para desligar a luz”. Nenhum comando foi executado.
- **Provado por código:** `ComandosImediatosRuntime` detecta a pergunta IoT e usa
  essa frase fixa antes da LLM. Não é uma invenção do Qwen nessa rota.
- **Próximo passo:** preservar o veto operacional e devolver a autoria da
  explicação ao contrato compartilhado, testando ligação/desligamento, alvos
  diferentes, indisponibilidade, recusa, hipótese e pedidos reais.
- **Não corrigido nesta rodada:** não remover a barreira IoT para silenciar o erro.
  O roteiro novo verifica também a inversão de ação/alvo, não só falta de comandos.
- **Atualização C13, 16/09 à noite:** mantida a mesma condição de veto, mas a
  porta prioritária retorna `False` para delegar a autoria à conversa. Não fala
  por cima do turno, não o marca como respondido e não alcança detectores ou
  executores subsequentes. Perguntas recebem documentação pelo caminho comum;
  recusas e hipóteses seguem com seu ato original, sem frase fixa sobre a luz.
- **RED/GREEN:** oito casos causais reproduzidos antes do patch; quatro controles
  de documentação/autoria já passavam. Depois, 12 aprovados, incluindo proposta
  operacional válida no JSON rejeitada pela autoridade do turno. O teste antigo
  que exigia a resposta fixa foi atualizado para o contrato de delegação; seu
  requisito de não alcançar o roteador foi preservado.
- **Runtime:** `roteiro_explicacao_capacidades-20260916-190855-889031` entregou
  explicações corretas de ligar a lâmpada/desligar o ventilador. Sonda adicional
  `roteiro_iot_explicacoes-20260916-191051-714954`: oito respostas, ações inversas,
  tomada, brilho, recusa e hipótese, zero comandos. Recusa: “Certo, não vou
  desligar o ventilador.” IoT simulado; não houve ensaio físico de dispositivos.
- **Limite restante em P01:** a LLM ainda pode explicar mal a confirmação,
  por exemplo “após o dispositivo ser refeito na configuração”, ou oferecer
  configuração sem uma capacidade comprovada. Não é o retorno da frase fixa;
  o placar automático da sonda não certifica esse conteúdo. Não alterados os
  guardiões, prompts, rede nem executores nesta correção.

### P15 — Falha técnica pede reformulação de uma pergunta clara

- **F3, 21/09 às 09:07:** recuperação vazia agora devolve fala e motivo
  separados; o cliente preserva nove razões canônicas de bloqueio em vez de
  convertê-las todas em OCUPADA. Nove REDs passaram; ampliado 2.974 aprovados,
  um RED F1, 14 xfailed e 30 subtestes. Controles posteriores: focado 108.
  Sonda concluída `transporte_evidencia-20260921-090740-395230`: replay + reparo
  vazio controlado atingiram limite de chamadas **real**, sem novo HTTP; fala
  informou limite sem pedir clareza. Doze respostas, zero comandos. Primeira
  tentativa de 20/09 interrompida após seis respostas, preservada como parcial.
  Limites: log intermediário ainda chama placeholder de reparo; sucesso da
  recuperação textual não foi reauditado amplamente. Demais categorias têm
  provas locais, não todas induzidas no runtime. Detalhes no mapa causal.
- **F3, 20/09 às 22:30:** categoria técnica chega à contingência no caminho
  principal e no reparo/autoria final, sem substituir conclusões locais válidas
  (social/observação confirmada). Quinze testes novos verdes; focado 122;
  ampliado 2.944 aprovados, um RED F1, 14 xfailed e 30 subtestes. Runtime real
  com timeout/conexão/ocupação **injetados** entregou as três causas sem pedir
  reformulação ou emitir comandos. Captura `transporte_evidencia-20260920-223000-712393`.
  Falhas em reparo/autoria ainda validadas localmente, não nessa sonda real.
  Permanecem na mesma raiz: saída vazia passando por recuperação perde motivo
  subsequente; orçamento ainda vira OCUPADA no cliente. Não inventar carga ou
  timeout a partir desse estado genérico. Detalhes no mapa causal. P15 parcial,
  não encerrado; origem física da latência segue fora desta correção.
- **Auditoria 20/09:** reprodução local com timeout, serviço indisponível e
  modelo ocupado confirmou pedidos indevidos de esclarecimento, sem comandos.
  A sentinela é reduzida a booleano; a chamada à contingência não transmite a
  categoria técnica. Primeira perda localizada nesse caminho. Origem da latência
  continua aberta; não confundir diagnóstico da conclusão com causa do timeout.
  Evidência e plano em [F3](MAPA_RAIZES_CONVERSA.md#f3-perda-de-categoria-de-falha).
- **Descoberto em:** sonda `roteiro_explicacao_capacidades-20260916-084208-340029`.
- **Observado:** timeouts de leitura nas duas primeiras chamadas (9 e 19 segundos)
  terminaram em contingências como “Faltou uma peça” e “Peguei o começo”, embora
  as perguntas de pausa fossem claras. Houve também timeout de preparação inicial.
- **Contrato necessário:** indisponibilidade técnica não é ambiguidade da entrada;
  a conclusão deve preservar a causa conhecida, sem atribuir o problema ao usuário.
- **Ainda aberto:** causa da latência e primeira perda da categoria de falha entre
  transporte e autoria da contingência. Carga ou inicialização são hipóteses, não
  causas comprovadas. A sonda posterior sem timeout não encerra esse defeito.
- **Próximo passo:** rastrear o motivo do erro até o fallback e criar contrastes de
  timeout, indisponibilidade e ambiguidade real. Nenhum prazo alterado nesta rodada.

### P16 — Reparo transforma pergunta de procedimento em relato passado

- **Descoberto em:** validação real de C11, turno 11 da sonda de 16/09 às 08:58.
- **Comprovado:** a entrada “como eu poderia aumentar o volume?” e o contrato
  `explicacao_capacidades` chegaram corretamente. A geração ensinou “ajusta o
  volume”, mas acrescentou uma condição sobre PC remoto. Após rejeição por
  `resultado_operacional_sem_evidencia`, o prompt de reparo afirmou “O usuário
  relatou um pedido” e permitiu perguntar “como foi”. O modelo terminou com
  “Como foi, dessa vez?”, foi rejeitado e houve contingência pedindo mais detalhes.
- **Dono localizado:** `qualidade_comunicacao.py`, seleção pelo indicador
  `resultado_operacional_desconhecido`. Esse indicador não prova o ato de relato.
- **Contrato necessário:** reparo deve preservar o ato e o objetivo do turno;
  desconhecer resultado não transforma pergunta em relato. O catálogo também
  não prova que uma rota remota é requisito para uma operação local.
- **Ainda aberto:** escopo exato da primeira rejeição e separação entre condição
  indevida gerada, falso positivo linguístico e reconstrução inadequada no reparo.
  Não remover o guardião para aceitar a fala. Nenhum patch dessa raiz nesta rodada.
- **Limite do avaliador:** marcou esse turno como aprovado e contou zero fallbacks,
  embora o terminal registre reparo rejeitado e contingência. Auditoria manual
  prevalece sobre esse placar mínimo; não usar 10/12 como qualidade aprovada.
- **C15, 19/09:** reproduzidos nove REDs locais antes do candidato, com um
  controle verde de relato explícito. Classificação e catálogo corretos antes
  do reparo falsificaram erro anterior como explicação dessa divergência. Além
  da premissa indevida no prompt, `_resumo_reparo` descartava a documentação.
  Agora o reparador mantém o objetivo/atos do contrato e recebe a documentação
  já selecionada quando a estratégia é `explicacao_capacidades`. Não resolve
  entidades novamente, não concede execução e não modifica o guardião.
- **Validação:** dez testes novos; 159 na seleção focada e 2.811 na ampliada,
  com 14 xfails preexistentes e 30 subtestes aprovados. Runtime completo:
  `roteiro_explicacao_capacidades-20260919-181949-614989`, captura
  `transporte_evidencia-20260919-181948-526867`. Replay somente do rascunho
  histórico de volume; reparo novo pelo `qwen3:4b-instruct` ensinou o pedido,
  sem “como foi” ou contingência. A frase adicional sobre remoto ainda foi
  removida pelo verificador: P01 permanece aberto. Houve também reparo novo
  de pergunta sobre aba, preservando o objetivo. Doze respostas, zero comandos;
  12/12 no avaliador mínimo não certifica a qualidade geral das explicações.

## Correções com validação registrada

“Validado no escopo” não significa ausência de outros defeitos naquela habilidade.
Datas e contagens abaixo descrevem cada rodada registrada, não uma suíte global.

| ID | Correção | Validação registrada | Limite restante |
| --- | --- | --- | --- |
| C01 | Recusas de alterar/mudar/ajustar reconhecidas pela base verbal canônica | 14/09: 41 testes focados; sonda de 18 turnos sem comandos | Não certifica toda interpretação de linguagem |
| C02 | Respostas locais publicadas entram no histórico do chat, com idempotência e compatibilidade com o emissor legado | 15/09: 17 testes novos, seleção de 103 aprovados e sonda final 18/18 | P07; conversa livre e demais writers não foram auditados integralmente |
| C03 | Realização de recusas e reconhecimento de perguntas não feitas sem falsos reparos em casos subordinados | 14/09: testes contrastivos e sondas reais sem contingência na rodada final | Não elimina toda invenção de estados |
| C04 | Orçamento do JSON estruturado separado do limite de fala curta; preservação do pacote fechado | 14/09: testes de geração/composição e sondas reais | Não garante universalmente JSON válido nem resolve qualidade sozinho |
| C05 | Sanitização de eventos/URLs Chrome antes da impressão, preservando dados dos handlers | 14/09: 27 testes com vizinhos e 2 subtests | P08; outros loggers não foram auditados globalmente |
| C06 | Reparo parcial preserva a resposta temática; verificador não apaga frases apenas por tamanho | 13/09: quatro turnos reais preservaram acolhimento e explicação | Preservar conteúdo não certifica sua correção factual; ver P02 |
| C07 | Catálogo vivo relevante acompanha a instrução do turno, sobrevivendo à compactação e retry | 15/09: 17 REDs → GREEN; seleção ampliada 451 passed; presença confirmada no HTTP real | P01 ainda parcial; P11 posteriormente tratado em C08; 18/18 sem execução não certificam qualidade da fala |
| C08 | Pedido nominal de informação não vira estado observado; escopo não vaza para outra alegação | 15/09: 44 contrastes; seleção ampliada 918 passed; replay histórico na composição real sem fallback | Sonda com Qwen real não repetiu a subordinada; tom e utilidade da explicação continuam em P01 |
| C09 | Autoria de explicações recebe documentação viva e tarefa textual, não planejamento genérico | Seleção conjunta: 1.307 aprovados / quatro REDs P12–P13; runtime: dez aprovações mínimas / duas falhas IoT | P01 não encerrado; cobertura, disponibilidade parcial e qualidade |
| C10 | Exemplo didático não é título pesquisável; fatos ao redor continuam exigindo evidência | 27 contrastes próprios; 42 aprovados com metalinguagem; exemplos preservados no chat real | P10 histórico mais amplo continua aberto |
| C11 | Moldura de procedimento reconhecida independentemente do vocabulário executável | 51 contrastes; seleção ampliada 2.556 aprovados / duas falhas P13; documentação de volume no HTTP real | Gramática limitada; P16 impede considerar a fala final corrigida |
| C12 | Catálogo documental consulta aliases dos aplicativos da composição | Nove testes novos; seleção ampliada 2.567 aprovados; documentação da calculadora no HTTP real | P10 corta a explicação gerada; referência não é instalação/estado |
| C13 | Veto IoT delega autoria sem substituir ação/alvo nem consumir o turno | 12 testes novos; 2.780 aprovados na seleção ampliada; duas sondas reais sem comandos, incluindo oito contrastes IoT | Não certifica hardware nem toda qualidade das explicações; P01 aberto |
| C14 | Papel da citação separa recurso, exemplo e obra; preserva contexto entre frases | 48 testes de citações; 2.801 aprovados na seleção ampliada; replay histórico no runtime e geração nova | Não prova existência/estado de recursos nem resolve toda citação ou P16 |
| C15 | Reparo preserva objetivo do turno e fonte da explicação | 10 testes novos; 2.811 aprovados na seleção ampliada; reparos novos de volume e aba no runtime | Requisitos indevidos sobre remoto ainda gerados; guardião permanece necessário |
| C16 | Limites documentados com escopo, condição e responsável | 9 testes novos; 2.829 aprovados na seleção ampliada; geração nova e HTTP real com controle local separado do remoto | Entrega final parcial: P10 ainda corta variantes didáticas; não certifica qualidade global |
| C17 | Papel de enunciado preservado com destinatário, referência intermediária e vocativo | 68 testes de citações; 2.849 aprovados na seleção ampliada; dois replays reais sem pesquisa indevida | Não amplia comandos executáveis; plataforma e qualidade geral continuam em P01 |
| C18 | Descrição de controle local usa documentação canônica do turno sem virar prova de fatos externos | 24 contrastes novos; 2.873 aprovados na seleção ampliada; frase histórica preservada no runtime | Família gramatical limitada; negativa indevida de controle de áudio continua em P01 |

Fontes: [rodadas de 14–15/09](RELATORIO_COLETA_DEBUG_20260914.md) e
[reparo parcial de 13/09](RELATORIO_CORRECOES_CONVERSA_20260912.md).

Na última seleção ampliada de C02: **605 passaram, 3 falharam e 8 subtests
passaram**. As falhas estão individualizadas em P03–P05; não foram escondidas
por uma declaração de suíte global verde.

## Ideias futuras — fora da fila de bugs

### I01 — Pesquisa em cinco sites/camadas

- Proposta do Pedro: extrair de cinco sites os pontos importantes para o pedido.
- **Somente guardada; não implementada nem ativada.** Não confundir com autorização
  para reconstruir a pesquisa durante uma correção de conversa.
- Registro original: [IDEIA_PESQUISA_CINCO_CAMADAS.md](IDEIA_PESQUISA_CINCO_CAMADAS.md).

## Modelo para o próximo achado

### P17 — Restrição de foco condicionada indevidamente ao modo jogo

- **Observado:** log do usuário às 10:49:51 registra avanço automático com
  `youtube_play`, `permitir_foco=False` e `target_tab_id` presente. Pedro relata
  que a troca ativa YouTube. Mesmo contrato ocorre no avanço manual.
- **Cadeia demonstrada:** callback real de `laylay.py` → registro do navegador
  → `NavegadorOperacoesRuntime` fornece a restrição → `chrome_comandos.py` só
  traduzia para `background=True` se jogo ativo → extensão ativa aba e janela
  quando `background` não está presente. Primeira divergência no transporte.
- **Falsificações:** alvo não estava ausente; `target_tab_id` chega ao transporte.
  Foco não é requisito do confirmador: `confirmYouTubeNavigation` lê/aciona o
  player pelo ID da aba, sem chamar ativação. Modo jogo é controle interno em
  que a restrição já funcionava. Não atribuído ao classificador ou à rede.
- **Contrato:** uma restrição explícita da operação sobrevive à tradução e
  não pode ser relaxada por contexto ou fallback. Owner: envio Chrome
  compartilhado. Aplicado a reprodução, busca e abertura de URLs; alias
  `entrar_no_site` normalizado antes da política. Foco autorizado e chamadas
  legadas sem restrição preservados. Sem extensão, operação protegida retorna
  falha em vez de abertura nativa que não garante preservação de foco.
- **Provas:** antes do candidato, **13 falhas causais e 7 controles verdes**.
  Após patch e três controles adicionais, seleção de navegador/playlist/jogo:
  **690 aprovados, 1 skipped, 9 subtestes**. Integração extrai o callback real
  de composição e usa registro, runtime e executor reais; somente a fronteira
  externa é simulada. Sucesso e falha mantêm receipt e alvo.
- **Escopo:** produção alterada somente em
  `mente_laylay/integracao/chrome_comandos.py`; teste novo
  `scripts/tests/test_chrome_preservacao_foco.py`. Extensão, playlist, rede e
  `laylay.py` não alterados. Nenhum commit ou treino pelo agente.
- **Limite:** Laylay aberta; não encerrada nem iniciada outra sessão. Ainda
  falta validar no Chrome real após reinício, com aba de estudos em foco,
  avanço manual/automático e observação do áudio/aba. Não declarar encerrada.
  A rota independente `chrome_navegacao.abrir_url_reutilizando_aba` possui
  fallback nativo sem guarda de `preservar_foco`; hipótese de outra ocorrência
  do mesmo contrato, não alterada nem certificada por estes testes.

- **Atualização após teste do Pedro, 21/09:** Pedro confirmou que a troca musical
  funcionou perfeitamente após o teste de foco/áudio. Evidência de uso real
  relatada pelo usuário, não uma nova captura feita pelo agente; não inferir
  cobertura de todos os modos a partir desse relato.
- **Complemento da mesma raiz:** demonstrado com dois REDs que o helper
  `abrir_url_reutilizando_aba`, chamado diretamente com `preservar_foco=True`
  e extensão desconectada, invocava o fallback nativo. A hipótese de falha
  inevitável na composição atual foi falsificada: `AmbienteNavegacaoRuntime`
  já injeta um callback protegido quando o modo jogo exige preservar foco.
  Portanto este complemento fortalece o contrato público, não comprova outro
  defeito da sessão do Pedro. Navegação normal fora do modo protegido permanece
  com a política anterior; não transformar todo pedido de abertura em background.
- **Patch e prova:** guarda mínima em `chrome_navegacao.py`, sem alterar o
  ambiente, rede ou extensão. Antes: **2 REDs e 28 controles aprovados**; depois:
  **56 aprovados e 2 subtestes** focados. Regressão ampliada: **697 aprovados,
  1 skipped, 9 subtestes**, 10,48 s. Protege URLs comuns e YouTube; sucesso/falha
  do fallback sem restrição e composição real do ambiente mantidos. Não houve
  desconexão da extensão ou abertura real de abas nesta etapa.
- **Trabalho paralelo:** estado Git conferido antes do patch e após os testes;
  sem diff visível em `mente_laylay/neural`, `laylay.py` ou `pyproject.toml` no
  momento das checagens. Nenhum conflito observado; não é auditoria de mudanças
  futuras, modelos ignorados pelo Git ou outra worktree. Arquivos do cliente
  e relato original preservados, nenhum commit criado.

### PXX — Título curto

- **Descoberto em / durante:** data e correção que estava em andamento.
- **Estado e impacto:** suspeita, reprodução, parcial etc.; consequência para Pedro.
- **Observado versus esperado:** exemplo mínimo, sem dados sensíveis.
- **Primeira fronteira / dono:** se conhecidos; não preencher com hipótese como fato.
- **Evidência e hipóteses falsificadas:** teste, artefato ou relatório; nível de prova.
- **Próximo passo:** menor investigação ou correção que falta.
- **Fechar quando:** contrato e validação necessários, incluindo runtime quando aplicável.
- **Atualizações:** data, alteração, resultado e limites; preservar o histórico.

## Atualizações do índice

- **15/09/2026:** criado por solicitação do Pedro; reunidos dez itens pendentes,
  seis correções com escopo validado e uma ideia futura. Somente documentação;
  nenhuma mudança de produção, treino, ativação neural, teste de runtime ou commit.
- **15/09/2026, continuação:** investigado P01; registrada C07 com prova do
  transporte. P11 separado após aparecer na sonda. Não houve treino/promoção
  neural nem mudança de autorização, executores ou guardiões nesta etapa.
- **15/09/2026, P11:** C08 altera somente a distinção/escopo linguístico nos
  validadores compartilhados. Rede, autorização, executores e personalidade
  preservados. A próxima frente permanece P01, agora sem o falso reparo histórico.
- **16/09/2026:** C09/C10 aplicados e validados com os limites acima. P12–P15
  separados; quatro REDs preservados, sem xfail. Rede e executores não alterados,
  nenhum treino, promoção ou commit criado. Próxima fronteira: P12, depois P13/P14.
- **16/09/2026, C11:** classificação P12 validada no escopo; produção alterada
  somente em `modalidade_turno.py`, preservando os patches anteriores. P16
  registrado sem desviar para outra correção. P13/P14 continuam pendentes;
  rede, catálogo, prompt, guardião, reparador e executores não alterados nesta etapa.
- **16/09/2026, C12:** alterados somente o mapa e sua injeção em `laylay.py`.
  P13 validado na recuperação; P10 reapareceu com nome de programa citado e
  exemplo em frase separada. Próxima frente planejada: P14; P10/P16 abertos.
- **16/09/2026, C13:** somente `comandos_imediatos.py` alterado em produção,
  preservando patches anteriores. P14 validado no escopo com geração real;
  nenhuma ação física, promoção neural ou commit. P01/P10/P16 continuam abertos.
- **19/09/2026, C14:** somente `fundamentacao_factual.py` alterado em produção;
  preservadas alterações anteriores. Citação histórica da calculadora validada.
  Próxima frente: P16, reparo preservando o ato e o objetivo da pergunta.
- **19/09/2026, C15:** produção alterada somente em `qualidade_comunicacao.py`
  e `validacao_contrato_fala.py`. Classificador, catálogo, guardiões, executores
  e rede preservados. Nenhum commit, treino ou promoção. Próxima fronteira:
  limites por capacidade/rota em P01; não ampliar automaticamente a correção.
- **19–20/09/2026, C16:** alterados catálogo `capacidades.py`, projeção no
  `mapa_habilidades.py` e instrução de autoria em `fala_capacidades.py`.
  Na retomada, o HEAD já era `c8b4c26f31deabd21168a458273896f398e2ddf0`,
  com o candidato de produção incorporado externamente; nada foi reaplicado
  ou revertido. Testes novos continuam ignorados pelo Git (P09). Nenhum commit
  criado pelo agente, promoção neural ou efeito físico. Guardiões preservados.
- **20/09/2026, C17:** produção alterada somente em `fundamentacao_factual.py`;
  regressões acrescentadas ao arquivo de testes existente. Execução, catálogo,
  reparador e rede preservados. A sessão do usuário não foi encerrada pelo
  agente; sondas iniciadas após Pedro fechar a Laylay. Nenhum commit criado.
- **20/09/2026, C18:** produção alterada somente em `fundamentacao_factual.py`
  e `plano_turno.py`, preservando C17. Fonte documental restrita ao contrato
  explicativo do mesmo turno; nenhum relaxamento de autorização ou receipt.
  Sonda concluída e ausência de processos Python conferida. Nenhum commit,
  treino ou promoção neural. Novo teste permanece ignorado pelo Git (P09).
