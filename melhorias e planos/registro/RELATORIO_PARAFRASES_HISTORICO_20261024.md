# C7/C5 — conferência de paráfrases pessoais pelo histórico, 24/10/2026

## Resultado e limite

Corrigida uma fronteira demonstrada do contrato compartilhado de revisão:
a ausência de conferência confundia “fora do recorte” com “relato sem apoio”.
Com pesquisa externa confiável sobre o assunto, o segundo podia ser admitido;
sem tema factual, o chamador nem sequer aplicava a conferência pessoal.

O candidato confere transformações estruturais de preferências atribuídas ao
usuário, inclusive infinitivo e negação, com fonte e derivação auditáveis.
Não confere semântica livre, sinônimos, anáforas, vigência da preferência,
veracidade externa, pertinência da resposta à pergunta ou efeito operacional.
A conversa real continuou apresentando falhas nessas outras fronteiras.

Produção alterada nesta tarefa:
- `mente_laylay/cognicao/fundamentacao_factual.py`: owner da conferência e da
  separação entre apoio pessoal e evidência externa;
- `mente_laylay/cognicao/plano_turno.py`: owner da aplicação da revisão e
  projeção efêmera da entrada atual com vínculo tipado já existente.

Sem alteração nesta tarefa em modelo, configuração, prazos, voz, executores,
roteadores, prompts ou revisão de fontes externas. Nenhum commit criado.
A solução serve ao revisor compartilhado das habilidades; testes abrangem
música, aplicativo, bebida e jogos, sem nomes ou frases no código de produção.

## Base preservada e causalidade

Branch `main`, HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`.
`resultados_testes/parafrases_historico_20261024/baseline.json` contém status
da worktree e hashes de 527 fontes; `fontes_antes/` congela a base desta tarefa.
O diff contra HEAD inclui candidatos anteriores e não representa este patch.

Cadeia reproduzida:

1. Fonte canônica do usuário está disponível, com autor, estado e texto.
2. A autoria propõe uma frase; a proposta não cria prova.
3. O leitor anterior só aceitava a forma indicativa positiva. Infinitivo e
   negação equivalentes não recebiam conferência.
4. O retorno `None` também representava ausência de apoio dentro desse recorte.
   A revisão prosseguia como se fosse um fato genérico do tema.
5. Com `confiavel=True`, uma pesquisa sobre rock podia liberar “você disse
   gostar de rock”, embora a fonte pessoal dissesse gostar de jazz.
6. Sem pesquisa/tema, `plano_turno` pulava a revisão pessoal. A factory anterior
   publicava tanto a preferência não declarada quanto a inversão rock/Nirvana.

Falsificações:
- Falta de histórico não é necessária ao RED: a fonte é passada diretamente,
  chega ao plano e aparece nas provas da factory.
- Geração ruim não é necessária: mesmas respostas HTTP válidas, mesma factory,
  trocando somente os dois owners pelas cópias congeladas.
- Fonte externa confiável não confirma o ato de ter dito; o controle alterna
  apenas a confiabilidade da pesquisa, sem mudar a fonte pessoal.
- Identidade lexical não basta para referentes dependentes de pessoa/momento:
  “meu”, “esse”, “deles”, “hoje” são recusados, sem resolver sua referência.
- A inversão histórica “rock, principalmente Nirvana” para “Nirvana,
  especialmente o rock deles” não foi declarada equivalente nem liberada.
- Negação sobre “disse” não é negação sobre “gostar”. Operadores da atribuição
  não são removidos para fabricar igualdade; perguntas não recebem certificado
  de declaração.

## Contrato e responsabilidades

O avaliador retorna quatro estados: `fora_do_recorte`, `cobertura_incompleta`,
`sem_apoio` e `conferido`. Detecção de recorte não implica aprovação.
Relatos pessoais reconhecidos sem conferência não podem obter aprovação de uma
fonte externa sobre o assunto. A proteção funciona com e sem pesquisa.

Uma conferência exige leitura integral das formas admitidas e igualdade de
predicado, polaridade, valor e foco na mesma declaração. A fonte é atribuída ao
usuário e deve passar pelo classificador canônico de proveniência. Mensagens
literais e a projeção da entrada atual vinculam ID e hash ao texto; o hash
verifica identidade, não autentica por si só um autor. A autoria da fonte vem
do owner que constrói o snapshot, nunca de um campo proposto pela IA.

A derivação registra regra, hashes de origem/destino, campos e intervalos
extraídos pelo código, além do alinhamento estrutural. Mantém falsas as flags
`semantica_verificada`, `prova_implicacao`, `pode_confirmar_fato_externo` e
`autoriza_execucao`. A finalidade inicial continua preservada no snapshot:
não se afirma preferência atual ou equivalência semântica irrestrita.

A entrada atual pode sustentar a mesma conferência somente pelo vínculo
tipado já usado para citação literal do canal do usuário. Essa projeção é
efêmera e não cria memória durável nem declaração persistente.

Não se alterou o classificador de intenção nem se adicionou outro parser de
comandos ao executor. Recibos, autorização, efeitos, revisão de fatos externos
e revisão de recomendações mantêm seus owners.

## RED, GREEN e composição instalada

Artefatos em `resultados_testes/parafrases_historico_20261024/`:
- `contrato_red.xml`: 8 falhas causais e 6 controles antes do candidato;
- `composicao_perspectiva_red.xml`: 7 falhas, demonstrando dêixis e o salto
  da revisão quando não havia pesquisa;
- `entrada_atual_red.xml`: 1 falha na projeção da declaração atual tipada;
- `escopo_atribuicao_red.xml`: 4 falhas de pergunta/operadores de atribuição;
- `contrato_final.xml`: 109 testes GREEN, incluindo a factory;
- `composicao_baseline_final.json` / `composicao_candidato_final.json`:
  mesmo composition root instalado e folha HTTP controlada. No candidato,
  três apoios preservados, dois relatos sem apoio retidos, pergunta preservada.
  Na base, os dois relatos incorretos eram publicados sem conferência pessoal.

O teste permanente `scripts/tests/test_parafrase_relato_historico.py` contém
31 casos, incluindo a factory em domínios distintos, negativos de fonte,
polaridade, foco, atribuição, identidade e estado revisado. O recorte antigo e
o foco prospectivo também passaram nos regressivos focados. Não há aprovação
por proposta da IA, nem geração de áudio ou ação real.

A revisão independente comparou somente os dois owners com a base congelada,
sem encontrar bloqueio concreto no recorte. Recomendação e prosa fora da
gramática permanecem limites explícitos, não garantias novas.

Regressão ampla relevante: 2.059 GREEN, 30 subtests GREEN, 14 SKIP,
uma deseleção por isolamento de import e uma falha anterior. A falha é
`test_pedidos_modais_autoridade.py::test_orquestrador_deterministico_resolve_mesmo_app_apos_moldura[pode abri a calculadora para mim]`:
MUSIC_SEARCH em vez de APP_OPEN. A contraprova anterior está em
`resultados_testes/respostas_prazos_20261024/relato_composto/falha_vizinha_baseline.xml`;
os owners dessa falha não mudaram nesta tarefa. Não foi silenciada nem corrigida
sob o contrato de paráfrases. O teste de import deselecionado passou na factory
isolada: um GREEN em `import_isolado.xml`.

`regressao_comando.json` e `regressao_ampla.xml` preservam comando e resultado.
Não se declara a suíte completa do repositório verde: estes são os 84 módulos
relevantes desta regressão, com a falha e as exclusões explicitadas.

## Qwen real: benefício e falhas abertas

`conversa_real/` usa a factory instalada, restaura as mesmas instâncias
cognitivas, isola a persistência e mantém as portas de efeito simuladas. O
redirecionamento da pasta de memória ocorre somente no loader em RAM.
Guardas bloqueiam escrita fora do perfil, rede externa, processos e dispositivos.
A seleção observada foi Ollama local, `qwen3:4b-instruct`, sem troca de modelo.

`auditoria.json` confirma 30 turnos/30 conclusões, 29 HTTP 200,
8 pacotes primários de fontes conferidos contra o pedido canônico, 527 fontes
sem drift e duração somada de 176,667 s. Houve um comando simulado, com receipt
negativo; nenhuma voz ou efeito real. Não se inferiu coerência de HTTP 200.

Seis passagens pela conferência pessoal: duas conferidas e quatro com
cobertura incompleta. Exemplos concretos:
- 5: “rock, e especificamente Obsidian” foi retido; a preferência de aplicativo
  não passou a ser prova de subgênero musical.
- 23: a afirmação de preferência por Atlas foi retida, sem liberar sua oração
  adicional por pesquisa sobre o tema.
- 25: “Você disse que não gosta de chá” foi preservado e conferido na fonte.
- 26: a mesma frase sobre chá também tem apoio, mas responde a uma pergunta
  sobre rock. **Apoio não prova pertinência**, portanto não é GREEN de coerência.

Limites observados, preservando C5/P01, C7 e F1 sem fundi-los:
- 6/7/18/22/29: dados existem no histórico e no plano, mas sua declaração
  primária não aparece no payload principal correspondente. Nos primeiros
  dois só há menções na instrução de evitar repetição; nos demais nem o nome.
  `diagnostico_fronteira_aberta.json` conserva a evidência. A primeira fronteira
  a estudar é a seleção/admissão de contexto antes da geração, não um remendo
  de resposta para cada aplicativo ou bebida.
- 3/15/17: familiaridade, associação da pessoa Dora a desenho e interpretação
  de pronome como nome foram produzidas sem apoio suficiente.
- 14/20: pedidos de reformulação entraram na retomada operacional de fala.
- 12/26/29: desvio de assunto, resposta apoiada mas não pertinente e falsa
  ausência de preferências ainda impedem declarar conversa coerente.

São evidências para investigação própria, não novas causas comprovadas nem
erros atribuídos automaticamente a este candidato. A próxima fronteira
prioritária é a perda das declarações na preparação do payload para perguntas
naturais sobre preferências. Não encerrar C5/P01 ou “compreensão da Laylay”.

