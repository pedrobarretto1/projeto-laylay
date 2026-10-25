# F1/C7 — relato de atividade não comprova os detalhes de seu modo, 24/10

## Base e diagnóstico antes do candidato

HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, branch `main`; 527 hashes e
status da worktree preservados em `resultados_testes/explicacao_pessoal_modo_20261024/`.

A coleta anterior com Qwen publicou, em resposta a `Como eu trabalho no
laboratório`, uma descrição de experimentos em primeira pessoa. A única
declaração disponível era `eu trabalho no laboratório`. O HTTP continha a
fonte e a instrução de perspectiva. O plano mantinha PerspectivaEnunciador
tipada e ligada ao turno, mas a revisão declarava sem obrigação individual de
fonte e aceitava o rascunho. A proposta inválida da IA não é prova; a primeira
fronteira autoritativa incorreta é admiti-la para publicação.

O conferidor lexical de perspectiva cobre posse, futuro com objeto e certos
relatos, não demonstra genericamente sujeito elíptico ou modo de atividade.
Ampliar uma lista de verbos/objetos não prova detalhes nem resolve a versão
em segunda pessoa. Não se aplicará um filtro por laboratório/experimento.

`composicao_baseline.json`: três domínios com fonte no plano e rascunho
sem apoio publicado (trabalho, estudo, notas). `contrato_red_confirmado.xml`:
6 REDs causais e 13 controles. O primeiro XML também inclui uma expectativa
incorreta de que metalinguagem didática não poderia exigir fonte; o controle
foi ajustado para verificar ausência de empréstimo do relato pessoal, sem
remover o contrato didático já existente.

Falsificados: falta de histórico como causa necessária; perda do contrato de
perspectiva; omissão de interrogação como causa; necessidade de inversão de
pessoa para produzir a extrapolação (segunda pessoa também falha).

## Contrato e candidato delimitado

| Owner | Responsabilidade |
| --- | --- |
| Referências linguísticas canônicas | Qualificar a relação de modo com sujeito explícito eu, separando orientação modal, outro agente, citação e metalinguagem. Não decidir verdade ou execução. |
| PerspectivaEnunciador capturada pelo host | Vincular pessoa, texto integral e ocorrência. Dicionário proposto pelo modelo não substitui o tipo. |
| Revisão compartilhada de suporte | Quando a pergunta de modo está vinculada a relato pessoal íntegro do mesmo predicado, limitar a realização ao relato atribuível. Presença do relato não demonstra detalhes livres. |
| Histórico/proveniência | Fornecer fontes já recuperadas pelo owner existente; conferir autor, origem, estado, ID e hash integral. Sem memória paralela ou busca pública para completar rotina pessoal. |

O candidato reutilizará a fonte de perspectiva e o histórico já presentes no
plano. Uma realização limitada poderá citar integralmente o relato disponível
e explicitar que ele não confirma outros detalhes. Não aprova implicação livre,
verdade externa ou autoridade. Não exige que o Qwen declare sua própria prova.

Escopo conservador: pergunta de modo com pessoa explícita e vínculo textual
com atividade relatada no histórico. Não será uma solução universal para
perguntas sem fonte, aconselhamento ambíguo, sinônimos, elipses ou paráfrases.
Esses limites devem continuar registrados, sem chamar o recorte de compreensão
geral. Recapitulação e resposta composta continuam em raízes separadas.

## Candidato, controles e revisão

Produção alterada somente em `referencias_linguagem.py` e
`revisao_suporte_autoria.py`. Não foram alterados modelo, configuração, voz,
classificador de modalidade, registro de memória ou executores. O candidato
não pesquisa detalhes de uma rotina pessoal na web nem guarda estado privado.

`contrato_final.xml`: 342 GREEN e 4 SKIP opcionais, incluindo 24 novos casos e
os módulos vizinhos de perspectiva, obrigação didática, suporte, paráfrase,
consulta histórica, escopo de predicado, contrato de fala e integridade autoral.
`contrafactual_final.xml`: apenas os dois owners congelados carregados em memória
reproduzem 6 REDs e 17 controles; a factory é explicitamente deselecionada por
usar subprocesso próprio. Nenhum arquivo de produção foi revertido em disco.

`composicao_baseline.json`/`composicao_candidato.json` usam a mesma proposta HTTP
nos mesmos três domínios. Antes: fonte disponível, rascunho inventado publicado.
Depois: uma publicação com relato integral atribuído e limite. Nenhuma execução
ou áudio real. O modelo não aprova sua própria descrição.

A revisão independente não encontrou bloqueio concreto. Verificou proveniência,
integridade, ocorrência e separação de efeito; rodou 23 testes leves, sem a
factory. Identificou um limite de chamada: plano artificial que retém comando
bloqueado fica fora do guard. No caminho real desta consulta, propostas
rejeitadas são removidas antes de publicar resposta_planejada. Não se demonstrou
essa ocorrência; não ampliar o patch para outro fluxo por hipótese.

Um controle adicional inicialmente exigia que uma fonte condicional não fosse
lida. A sonda mostrou citação integral de `se você me chamar`, sem confirmação
de cumprimento. A expectativa era mais forte que o contrato delimitado e foi
corrigida para proteger ressalva integral e `modo_verificado=False`, com revisão
independente. `controles_fontes.xml` preserva a execução intermediária; nenhuma
alteração de produção foi feita para mascarar essa condição ou mudar seu parser.

## Qwen real e regressão ampliada

`conversa_real/`: 30 turnos e 30 conclusões; 30 HTTP 200; 17 pacotes primários
com fontes conferidas; 527 fontes sem drift. Mesmo modelo local configurado,
`qwen3:4b-instruct` em Ollama. Tempo acumulado dos turnos: 236,083 segundos,
sem inferir benchmark geral. Sem voz ou efeitos reais; um pedido de Calculadora
recebeu receipt negativo simulado. Resultado e transcrição em `auditoria.json`
e `TRANSCRICAO.md`.

No turno 9, a resposta foi `Você contou: «eu trabalho no laboratório». Esse
relato não confirma outros detalhes da sua rotina.`. `auditoria_modo_pessoal.json`
confere origem, autoria, hash e presença da fonte no histórico real anterior.
Não usou o rascunho, a pergunta ou a declaração de suporte como prova do método.
`modo_verificado`, confirmação externa e autoridade permanecem falsos.

A conversa geral não está corrigida. Turnos 5/6 deixam de recuperar preferências;
14 atribui causa pessoal a gostar de rock sem relato causal; 15/20/22/23/24/25/26
incluem inversões, negações ou mesclas; 29 repete o pedido em vez de recapitular.
`falhas_livres_abertas.json` preserva sintomas e fontes no plano. Não se atribui
a diferença entre coletas estocásticas a uma regressão deste patch sem um
contrafactual controlado. A comparação HTTP controlada é a prova antes/depois
do recorte; a conversa real demonstra seu uso e os limites restantes.

Esses sintomas continuam vinculados às famílias históricas F1/C7. Não se
provou uma raiz única entre eles. Próximo passo: isolar a troca de pessoa nas
respostas de retomada (inclusive relato composto/negado), conferindo fonte,
seleção, autoria e revisão na mesma ocorrência. Causa pessoal e recapitulação
permanecem evidências abertas, sem outro patch local nesta entrega.

Regressão de 93 módulos: 2.288 GREEN, 30 subtests GREEN, 14 SKIP, uma deseleção
de import e nove falhas anteriores. `comparacao_falhas_anteriores.json` confere
os mesmos IDs da etapa anterior, sem falha nova nesse conjunto. Comando/saída:
`regressao_comando_final.json`, `regressao_final.log`, `regressao_final.xml`.
O import deselecionado passou na factory isolada (`import_isolado.xml`).

As nove falhas preservadas são a rota antiga de calculadora (um caso) e as
expectativas anteriores de pacote/reserva de saída (oito casos). Contraprovas:
`resultados_testes/respostas_prazos_20261024/relato_composto/falha_vizinha_baseline.xml`
e `resultados_testes/base_canonica_rota_rapida_20261024/vizinho_orcamento_baseline.xml`.
Nenhum teste existente foi alterado para silenciá-las; não declarar suíte toda
verde. O candidato/escopo/hashes estão em `candidato_contra_base.patch` e
`entrega.json`. Nenhum commit, migração ou reinício da sessão pessoal.
