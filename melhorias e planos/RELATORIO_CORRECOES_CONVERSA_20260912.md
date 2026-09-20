# Correções e limites verificados — 12/09/2026

## Base e escopo

HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, branch `main`, worktree já modificada. Nenhum commit criado, nenhum reset e nenhuma promoção/treino neural. Modelo real confirmado no transporte: `qwen3:4b-instruct`.

Solicitação: continuar classificação conversacional e tratar os problemas documentados em `erros_encontrados.md`. **O conjunto não está encerrado.** Os candidatos sem resultado real satisfatório foram retirados; os REDs restantes estão abaixo.

## 1. Classificação de transformação da conversa

Primeira fronteira: imperativo de resumo era classificado como comando, exigindo executor; comparação contendo `agora` e `não` caía no reconhecedor de recusa curta. Falsificado: não dependia de falha do LLM nem de um detector externo (reproduzido com detector ausente e com detector positivo).

O descriptor compartilhado em `normalizacao_linguagem.py` distingue resumo de alvo discursivo e comparação de expressões citadas. `modalidade_turno.py` aplica o contrato antes da normalização destrutiva e preserva atos operacionais independentes. O match integral não captura resumo de página/arquivo/e-mail nem elimina negação real.

O primeiro candidato teve GREEN local, mas a sonda revelou outro desvio: a composição real usa um normalizador que remove aspas. A matriz foi ampliada com esse normalizador, reproduziu 6 REDs e passou após preservar a representação estrutural na fronteira. Isso confirma por que a prova sem callback real era insuficiente.

Outro falso positivo independente: o marcador metalinguístico aceitava `frase`, mas não `frases` (também palavras, expressões, formulações, exemplos, citações). Seis REDs canônicos protegeram a correção morfológica. Não é um validador universal de significado.

Prova final: `resultados_testes/roteiro_transformacao_conversacional-20260912-181318-268884/`. Todos os 8 planos são conversa e `requer_execucao=False`; nenhum comando. O resumo da coruja/raposa voltou a usar o assunto anterior. **Ainda existem respostas semanticamente erradas e intervenções de guardiões** (por exemplo, confundir proibição de abrir com fechar). Portanto GREEN da classificação não significa GREEN de toda a conversa.

## 2. Histórico eliminado pelo orçamento

O payload real do pedido `pode me recomendar um modelo que seja bom e barato` chegava sem a troca sobre DC-DC. O contrato aparecia, mas a conversa anterior só sobrevivia no trecho estilístico “evite repetir”.

Raiz em `_selecionar_historico_com_orcamento`: o comentário dizia que o orçamento limitava histórico opcional, mas a soma incluía a instrução obrigatória de milhares de caracteres. Ela esgotava a verba de 1200 caracteres antes de selecionar o diálogo.

Correção mínima: itens obrigatórios do turno não consomem a verba de caracteres do histórico opcional. Mantidos os limites de mensagens e o descarte de instruções system antigas. Dois REDs canônicos passaram; sondas posteriores carregaram mais mensagens e retomaram o tema. Isso não resolve sozinho curadoria da fonte, recuperação de longo prazo ou fatos inventados.

## 3. Abrir um site por assunto

Cadeia histórica: `site sobre X` → `OPEN_URL(alvo='sobre X')` → busca Google com `auto_click=False` → anúncio de abertura. Não houve tentativa de escolher resultado: não era simplesmente falha do Google ou da extensão.

Correção: o extrator canônico reconhece `SITE_ENTER(tema=X)` e o adaptador conserva essa intenção. O executor confirma a busca antes de chamar a abertura de resultado já existente, agora em helper compartilhado com `SEARCH`. Só confirma conclusão com retorno positivo da extensão. Falha de busca impede o próximo efeito; falha/exceção de seleção gera conclusão negativa observável. O destino remoto falha fechado nesta rota, pois não possui receipt de seleção remota: não se deve clicar localmente para completar uma busca de outro PC.

Prova real: `resultados_testes/roteiro_site_por_assunto-20260912-181113-772346/`. Pedido por documentação oficial do Python → `SITE_ENTER` → `resultado_web_aberto`, executou/confirmado verdadeiros, e URL observada `https://docs.python.org/pt-br/3/`. A página foi deixada aberta. O teste prova abertura do primeiro resultado observado, **não seleção qualitativa do melhor site**. A fala autoral ainda contém deboche desnecessário; não foi mascarado no executor.

## 4. RED aberto: resposta social + pergunta temática

Reproduzido três vezes com captura do transporte:

- `roteiro_recomendacao_contextual-20260912-180307-451798`;
- `roteiro_recomendacao_contextual-20260912-180705-369499`;
- `roteiro_recomendacao_contextual-20260912-180951-097532`.

A classificação identifica conversa + pergunta. O modelo responde à parte temática, omite acolhimento e, no reparo, escreve sobre seu próprio estado (`estou bem`) em vez de reconhecer o estado do usuário. A rejeição dispara contingência que substitui a resposta temática inteira.

Falsificado: a segunda pergunta não desapareceu do classificador ou do payload. Aumentar instruções e explicitar o dono em prompt também não resolveu a inversão no runtime; esses candidatos de prompt foram retirados. Foi mantido apenas metadado estruturado do estado do usuário no contrato de reparo, emitido pelo mesmo owner que o reconhece, com teste de não atribuição em pergunta sobre Laylay.

Próxima fronteira: reparação parcial por ato, preservando o conteúdo validado dos outros atos e verificando atribuição de pessoa. Não enfraquecer a segurança factual para manter texto útil, nem devolver resposta temática incorreta só para evitar fallback.

## 5. RED aberto: recomendação generalizável com evidência

O planejamento exige uma opção da “evidência factual do turno” mesmo sem candidatos. `pesquisar_recomendacoes_tema` oferece fonte especializada apenas para filmes por gênero. Repetição do pedido e negativa de capacidade não são uma limitação comprovada do Qwen: o contrato e a evidência fornecida não são adequados para a tarefa.

Um candidato de orientação por critérios eliminou a negativa em uma sonda, mas produziu recomendações técnicas incorretas. **Foi retirado**, incluindo a permissão adicional de usar conhecimento geral como base de recomendação. Não foi promovido porque o usuário quer resultado confiável, não apenas uma resposta mais confiante.

Exemplo observado: TL431 apresentado como módulo capaz de alimentar o conjunto. A Texas Instruments o documenta como referência/regulador shunt, não um módulo DC-DC completo para esse uso: https://www.ti.com/product/TL431 . Não usar os textos desses testes como projeto elétrico ou lista de compras.

Próximo contrato, sem criar uma habilidade por peça:

1. Recuperar assunto e requisitos explicitamente informados, com origem. Campo ausente permanece desconhecido, sem presumir tensão/corrente de motores, OLED ou bateria.
2. Reutilizar pesquisa/coordenador canônicos para obter fontes do fabricante e candidatos; separar fonte, modelo, especificação e data. Preço/estoque/ranking exigem fonte atual própria.
3. Comparar candidatos aos requisitos, marcando atende/não atende/não comprovado, incluindo perdas, restrições e componentes auxiliares.
4. O LLM escolhe e explica a partir dessa base; não inventa ficha, pesquisa realizada ou compatibilidade. Perguntar dados essenciais quando mudarem a escolha, sem afirmar incapacidade de recomendar.
5. Validar sucesso, indisponibilidade da pesquisa, fontes contraditórias, especificação faltante, correção do usuário e dependências compostas no runtime. A recomendação musical permanece fora desta alteração.

O teste canônico do contrato impossível permanece `xfail(strict=True)` identificado como RED aberto; não é contabilizado como correção.

## Verificação e arquivos

Regressão final selecionada por uso dos classificadores, preparação do payload, verificação/reparo e roteador/executor web: **1827 passaram, 37 subtests passaram, 1 xfail explícito e 1 falha preexistente**. A falha em `test_latencia_resposta.py::test_prompt_rapido_limita_saida_sem_reduzir_resposta_complexa` espera 128 tokens e recebe 256; orçamento de saída não foi alterado nesta rodada. Não é suíte global GREEN.

Produção alterada nesta rodada: `modalidade_turno.py`, `normalizacao_linguagem.py`, `validacao_contrato_fala.py`, `preparacao_llm.py`, `roteador_deterministico.py`, `executor_navegador.py`. Os experimentos em `geracao_concreta.py` e no prompt de `qualidade_comunicacao.py` foram desfeitos preservando as alterações anteriores da worktree. `laylay.py`, pesos neurais e executores de música/IoT não foram alterados por esta rodada.

Testes novos: `test_transformacao_conversacional.py`, `test_orcamento_contexto_dialogo.py`, `test_recomendacao_sem_evidencia_e_reparo_social.py`, `test_abertura_site_por_assunto.py`. Sondas e transportes locais registram as respostas brutas e planos; contêm contexto pessoal e não devem ser publicados. Gmail desconfigurado e IoT simulado nas sondas. Processos iniciados pelos testes foram encerrados.

## Continuação — 13/09/2026: reparo parcial e preservação até a entrega

Base: HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, branch `main`, worktree amplamente modificada antes desta rodada. Os diffs anteriores foram preservados. Nenhum commit criado, modelo/pesos neurais não alterados.

### Contrato do reparo

Um reparo limitado a um ato não pode substituir a resposta inteira. Quando o único problema bloqueante é o reconhecimento do estado pessoal do usuário, sem comandos/execução ou alegações operacionais inválidas, o avaliador qualifica um reparo parcial. A avaliação guarda o hash do rascunho. O modelo recebe apenas o estado com dono explícito e produz uma reação curta; o compositor valida o fragmento, confere o hash e o acrescenta ao original. A composição passa novamente pela qualidade e pelo verificador final. Nenhuma dessas verificações certifica universalmente a verdade do conteúdo técnico.

RED canônico antes do candidato: o callback devolvia um acolhimento válido, mas a preparação aceitava esse fragmento como resposta completa e apagava a explicação temática. Reproduzido em painel solar e em lista/tupla. GREEN após compor em vez de substituir. Cobertos: rascunho trocado, comando introduzido pelo reparador, resultado operacional sem receipt, estado da própria assistente, negação e pergunta sobre Laylay.

Primeira sonda (`roteiro_recomendacao_contextual-20260913-072737-449765`) ainda falhou: Qwen respondeu ao reparo com `Estou aqui pra te acolher.`. A hipótese inicial de que o limite havia impedido esse reparo foi falsificada pela captura completa: **o reparo chegou ao modelo; só a tentativa posterior de autoria foi bloqueada**. O orçamento não foi alterado. Uma variante de prompt com exemplo positivo também foi descartada após comemorar o cansaço e inventar sua causa em uma chamada local de contraste.

A instrução curta final pede reação ao estado informado, sem inventar causa ou aconselhar. Outro RED demonstrou que a validação dependia de bordões: rejeitava `Ah, bom que você está bem.` e `Fico contente que você está bem!`. O owner compartilhado agora reconhece também atribuição explícita em segunda pessoa, sem aceitar oração negada ou pergunta nessa nova alternativa.

### Fronteira posterior: corte cego por proporção

Na sonda `roteiro_reparo_parcial_conversa-20260913-073420-186234`, o reparo chegou corretamente, mas o verificador final apagou a quarta frase por tamanho. O corte ocorre **depois** das verificações semânticas. Dois REDs em lista/tupla (com e sem ato social) confirmaram que ele também apaga a resposta ao segundo conceito ou uma ressalva final. Não era um problema exclusivo de Arduino ou do reparador.

Correção em `plano_turno.py`: proporção excedida continua diagnosticada (`resposta_acima_da_proporcao_do_turno`), mas não trunca o texto no verificador final. Limites de geração e validadores de segurança/fatos permanecem; o utilitário de proporção e seus outros chamadores não foram alterados. Isso protege todas as habilidades que atravessam essa fronteira canônica, sem afirmar que outros caminhos de formatação estejam auditados.

### Prova final e limites

- Runtime real, Qwen `qwen3:4b-instruct`: `resultados_testes/roteiro_reparo_parcial_conversa-20260913-073650-078925/`; captura `transporte_evidencia-20260913-073649-001672/transporte.jsonl`.
- Quatro turnos, zero comandos. Primeiro turno recebeu o fragmento `Ah, bom que você está bem.` e preservou a explicação; quatro frases chegaram ao chat, com proporção apenas diagnosticada. Cansaço/tristeza + perguntas sobre Python tiveram reconhecimento e explicação. Pergunta sobre a própria Laylay não virou estado do usuário. As quatro `falas_planejadas` coincidiram com a fala da última verificação.
- Regressão selecionada: **757 passed, 1 failed preexistente, 1 xfailed conhecido**. A falha continua sendo `test_prompt_rapido_limita_saida_sem_reduzir_resposta_complexa` (128 esperado, 256 real). `git diff --check` sem erros. Não é suíte global nem caos completo GREEN.
- Produção alterada nesta rodada: `processamento_resposta_ia.py`, `qualidade_comunicacao.py`, `validacao_contrato_fala.py`, `plano_turno.py`. Teste novo: `tests/test_reparo_parcial_conversa.py`. Sonda nova: `roteiro_reparo_parcial_conversa.py`, adicionada à lista explícita da captura. `laylay.py`, transporte/orçamento, executores e pesos não alterados nesta rodada.
- **Ainda aberto e prioritário:** conteúdo técnico inventado/inadequado. A sonda intermediária deu orientação inadequada envolvendo alimentação por pinos de sinal; a sonda de recomendação também produziu especificações não sustentadas. Não usar essas conversas como orientação elétrica nem como exemplos positivos de treino. Preservação da resposta não é correção factual. Seguir o contrato de requisitos → fontes → comparação descrito na seção 5, sem liberar recomendações por confiança textual.
- Falsos positivos de fundamentação em trechos citados também continuam abertos: uma sonda tratou uma citação de estado emocional como obra. Não foi mascarado nesta rodada.

Ideia de pesquisa em cinco sites/cinco camadas guardada em `IDEIA_PESQUISA_CINCO_CAMADAS.md`, por pedido explícito do Pedro; **não implementada nem ativada**. Os testes usaram Gmail desconfigurado, IoT simulado e voz suspensa. As conversas de teste ficaram nos artefatos e na memória normal do runtime; não houve treino neural nesta rodada.

## Fechamento da rodada de investigação — 13/09/2026, noite

Por orientação do Pedro, retomar a rede após esta etapa; não transformar a correção de recomendações numa reconstrução indefinida da pesquisa. **Fechamento da rodada não significa encerramento dos REDs de recomendação.**

Foi reproduzida a ordem impossível de escolher uma opção sem candidatos em 13 casos: pedido histórico, três formulações e bases ausente, falha, genérica e vencida. Uma base válida com candidatos serviu de controle. Candidato mínimo em `geracao_concreta.py`: exigir fonte/resumo/candidatos confiáveis antes de ordenar escolha; caso contrário, preparar requisitos sem afirmar incapacidade nem especificações. Foram 60 testes focados verdes com o candidato, mas a prova real não confirmou sua eficácia.

Sonda: `resultados_testes/roteiro_recomendacao_contextual-20260913-181929-806629/`. Captura: `transporte_evidencia-20260913-181927-763839/transporte.jsonl`. O quarto plano tinha `preparacao_recomendacao`, e o payload efetivamente continha a instrução de não escolher sem evidência. Ainda assim, o modelo produziu uma recomendação nominal com especificações não sustentadas. Falsificadas as hipóteses de que apenas a ausência da instrução ou sua perda no transporte explicariam o resultado. O quinto turno continuou com inferências técnicas indevidas; corte parcial do guardião não certifica o restante.

**Candidato retirado de produção**, preservando os patches anteriores. Não aumentar proibições de prompt nem criar filtro de marcas como suposta solução. Os testes negativos continuam explicitamente `xfail(strict=True)` da mesma raiz; não são 13 problemas independentes nem correções aprovadas. A próxima solução de recomendação precisa de ligação verificável entre requisito, candidato, fonte e afirmação, além da descoberta de fontes. Isso fica pendente; a ideia de cinco camadas permanece somente registrada.

Regressão final após retirada e retomada da coleta neural: **806 passed, 13 xfailed da raiz conhecida, 1 falha preexistente** (`test_latencia_resposta.py`, 128 esperado/256 real). Escopo final desta rodada: testes e documentação, mais exportação offline da fila neural; nenhuma nova mudança de produção mantida, nenhum treino/promoção/commit. A Laylay iniciada pela sonda encerrou normalmente. Não usar os textos técnicos dessa sonda para montagem nem como rótulos positivos.
