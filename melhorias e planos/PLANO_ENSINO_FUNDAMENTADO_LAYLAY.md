# Ensino fundamentado da Laylay — contrato proposto para P01

Estado em 23/09/2026: **recuperação implementada, influência na fala não
liberada por padrão**. Modelo local atual: `qwen3:4b-instruct`. Nenhum serviço
pago ou troca de modelo está pressuposto. Para uma sonda controlada, usar
`LAYLAY_PESQUISA_MULTIFONTE_MODO=ativo`; sem essa variável, o fluxo anterior
permanece. Não recomendar ainda esse modo para uso diário.

Atualização da investigação: o verificador factual atual aceita, sem apontar
problema, “A planta baixa mostra a casa de baixo para cima” mesmo com a fonte
do turno afirmando “vista superior”. Isso reproduz o RED na fronteira de
verificação: nomes, números e títulos têm guardas, mas a relação conceitual
central e o exemplo não têm prova de implicação. A hipótese de falta de fonte
não explica este caso: o plano do turno continha cinco trechos lidos, incluindo
“vista superior”. Uma segunda opinião do mesmo Qwen **sem** a fonte também já
falhou na sonda anterior. Não promover uma revisão por LLM ou regras de
antônimos sem medir controles positivos, negativos, casos inéditos e latência.

A interferência separada de IoT foi reproduzida com o mesmo pedido “me explica
com um exemplo o papel da luz na planta”: o alias “luz” encontrava a lâmpada
e a condição genérica de texto autorizava procurar RGB de “planta”, mesmo sem
ordem operacional. O portão de pesquisa de cor livre agora exige pedido direto
de ajuste; 34 testes IoT passaram, incluindo a frase real, controle de
comando e detector registrado na composição real. Ainda falta uma conversa
fim a fim com geração pelo modelo; não confundir GREEN de composição com
raiz encerrada.

Uma sonda isolada com `qwen3:4b-instruct` e trechos reais comparou sete
alegações corretas, contraditas e sem prova. Ele acertou os sete **rótulos**,
mas só três saíram com índice e citação literal válidos. Portanto nem esse
resultado pequeno, nem a opinião do mesmo modelo, fornece ainda um portão
auditável para publicação. A sonda reproduzível é
`scripts/analises/sonda_verificacao_ensino_com_fonte.py`; ela não altera a
Laylay. Em 23/09 a sonda passou a oferecer frases completas com IDs, mapeados
por código de volta à URL e ao texto literal. Em dez alegações, incluindo
contradições e casos sem prova, o Qwen acertou 10/10 rótulos, mas escolheu a
frase decisiva em apenas 5/10. A amostra é pequena e usa artefatos já lidos;
não houve avaliação de custo/latência no turno real. **Não integrar esse
verificador ainda.** O próximo experimento deve confrontar casos inéditos e
fontes com assuntos misturados, exigir implicação rastreável da definição *e*
do exemplo, e medir latência antes de cogitar segunda chamada de LLM.

Nova aferição em 23/09: o gabarito por palavra-chave acima era permissivo em
um caso e rígido demais em outro. “A luz é transformada em CO2” não é
*refutada* pelas frases lidas só porque elas também dizem luz → energia
química; essas relações poderiam coexistir. Por outro lado, “anuais morrem no
espaço de um ano” é prova válida contra “vivem mais de dois anos”, mesmo sem
repetir a frase de outra fonte. O gabarito experimental agora registra IDs
semanticamente aceitos por alegação. Repetindo a mesma sonda: **9/10 rótulos,
6/10 rótulos com evidência adequada**. Em oito controles de pares
alegação–frase, isolar a citação eliminou algumas escolhas erradas, mas o
mesmo Qwen também deixou de reconhecer contradições válidas. Portanto uma
segunda chamada sobre uma única frase não resolve por si o contrato.

Uma sonda diferente, `scripts/analises/sonda_rascunho_didatico_ancorado.py`,
forneceu duas frases curadas por assunto ao Qwen e pediu definição e exemplo
hipotético com IDs. Nas três saídas, as definições citaram IDs existentes,
mas a de fotossíntese introduziu água e gás carbônico ausentes dos trechos.
Todos os exemplos vieram com `ids_exemplo=[]`; o de arquitetura voltou a
confundir a orientação da planta baixa, e o de jardinagem atribuiu espécie e
época de floração sem fonte. **ID válido é só proveniência formal; não é
prova de implicação.** A sonda não altera produção. O próximo experimento deve
recuperar também exemplos trabalhados nas fontes e confrontar definição e
exemplo separadamente, com negativos de tópico parecido e controles de
recusa de prova. Os testes focados de pesquisa, factualidade, didática e
auditoria da sonda somam 184 aprovados; isso não é GREEN de ensino no runtime.
Não ativar geração ancorada nem revisor LLM por padrão.

Experimento seguinte, ainda fora da produção: a sonda
`scripts/analises/sonda_exemplos_lidos.py` percorreu o texto completo de três
páginas reais já usadas como fonte. Um contrato conservador aceita apenas
instância nomeada com classificação explícita na mesma frase. Nas páginas de
planta baixa e fotossíntese não encontrou caso apto; na página de plantas
anuais encontrou petúnias. Um falso positivo real (“Baratas:” era uma
propriedade, não uma espécie) foi reproduzido em RED e corrigido exigindo que
o nome da instância seja sujeito da predicação. Quatro testes locais passaram.
Ao fornecer a frase das petúnias junto das duas definições ao Qwen, ele citou
o ID correto no exemplo, mas acrescentou outubro e estações que a frase não
estabelece. Assim, **nem um exemplo da fonte + ID citado certificam o texto
final**. Antes de qualquer influência na fala, medir cobertura em mais
domínios e impedir adições factuais não sustentadas; quando não houver caso
documentado, não fabricar um apenas para preencher o formato da aula.

Medição ampliada, ainda somente leitura, reproduzível por
`python -m scripts.analises.medir_cobertura_exemplos`: oito temas
(biologia, arquitetura, jardinagem, matemática, eletricidade, Python e
floricultura), 39 páginas relidas na última execução. O extrator conservador
de instância explícita cobriu **1/8 temas e 1/39 páginas**. Um segundo tipo,
conta de multiplicação conferida por código, elevou a cobertura a **2/8
temas** e encontrou contas em duas páginas. O contrato matemático publica
somente `a × b = c`, após verificar `a*b == c`; mantém a frase da página e
URL como proveniência, sem importar pronomes ou passos incompletos. Isso não
generaliza para exemplos de circuitos, arquitetura ou código. Na página de
Python inspecionada havia blocos `<pre>`/`<code>` que o parser textual atual
não captura como exemplos; essa é uma fronteira distinta para investigar.

Para impedir acréscimos na saída, a sonda de rascunho ganhou um **portão
extrativo experimental**: definição e exemplo só passam se cada frase final
for literalmente uma das frases citadas por ID (admitindo apenas espaços e
aspas tipográficas diferentes). O controle positivo literal passou; o caso
com “florescem em outubro” foi rejeitado. Repetindo os três rascunhos reais
do Qwen, **0/3 aulas completas seriam publicáveis**; em arquitetura apenas a
definição era literal, enquanto o exemplo não era. É uma prova de bloqueio
de adições, **não** uma solução de ensino natural: paráfrases fiéis também
podem ser rejeitadas, páginas podem errar e um ID não garante relevância.
O portão permanece fora do runtime; não transformar o fracasso em fallback
genérico. Próximas fronteiras: blocos de código com validação estática
segura, exemplos de cenário com relação causal explícita e um avaliador de
implicação confiável para paráfrases antes de qualquer publicação diária.

Sondas seguintes (também fora do runtime):

- `scripts/analises/sonda_exemplos_lidos.py` agora lê blocos `<pre>` de Python
  sem executá-los. Na página real de laço `for` da freeCodeCamp, preservou
  seis blocos: cinco com sintaxe válida e um fragmento de notação de `range`
  que não é programa. Comentários `# imprime ...` permanecem no texto bruto,
  mas são removidos de `codigo_apresentavel` pela árvore sintática; nenhuma
  saída é considerada confirmada. Na documentação oficial Python, os blocos
  `>>>` foram classificados como transcrição, não como código puro/receipt.
  O parser também ignora menus e instruções externas no contexto imediato.
  **Sintaxe válida não prova comportamento, segurança nem adequação didática.**
- `scripts/analises/sonda_cenarios_lidos.py` preserva URL, ordem e seção de
  parágrafos. O contrato experimental distingue relação causal explícita
  (`se` → `porque` → `por isso`) de contraste observacional entre duas lentes
  sobre o mesmo objeto. Testes sintéticos protegem contra legenda, pergunta,
  circuito paralelo usado como série, URL/seção ausente e união de páginas
  diferentes. Ambos os tipos são apenas *candidatos estruturais*, com
  `verdade_externa_verificada=False`.
- Nas páginas reais examinadas, o artigo de circuito em série descreveu uma
  interrupção, mas não ofereceu numa frase a cadeia inteira exigida pela sonda.
  O artigo de arquitetura descreveu a mesma janela em desenhos diferentes,
  porém em subseções distintas; a regra de mesma seção a rejeitou. São falsos
  negativos esperados do portão conservador. Não usá-lo ainda para concluir
  que os sites não têm bons exemplos, nem afrouxá-lo para juntar trechos sem
  relação. A próxima evolução é preservar a hierarquia de títulos e spans
  contíguos antes de medir novamente a cobertura.

Essas sondas **não** foram ligadas ao pesquisador, prompt, verificador ou
fala em produção. O contrato comum descoberto é: exemplo tem tipo, origem,
escopo e prova própria; HTML, sintaxe válida ou citação formal isolados não
autorizam a publicação de um fato nem de um efeito observado. Seleção local de
pesquisa, didática, factualidade e sondas: **203 testes aprovados**; não há
GREEN de ensino no runtime real nesta etapa.

Nova rodada da mesma raiz P01, ainda **somente experimental** em 23/09:

- A sonda de cenários agora preserva o título-pai, a subseção e a identidade
  estrutural de cada abertura de seção, além da URL e da posição dos blocos.
  No artigo real de arquitetura, isso permitiu localizar a janela da sala na
  planta baixa e na fachada (blocos 32 e 34). Não inferiu a comparação com o
  corte: o parágrafo desse corte não estabelece relação com a mesma janela.
  Controles RED→GREEN impedem unir capítulos diferentes, inclusive quando
  repetem literalmente o mesmo título. O resultado continua um candidato
  observacional, não um fato conferido.
- Nova busca de oito temas encontrou candidatos em **4/8**: plantas anuais,
  multiplicação, laço `for` e variáveis em Python. As buscas e leituras da web
  variam entre execuções. Para Python, o critério foi somente sintaxe válida
  contendo o elemento pedido; não se executou código e a saída não foi
  confirmada. Fotossíntese, arquitetura, circuitos em série e orquídeas não
  renderam candidato pelo extrator geral nessa rodada. A página de arquitetura
  conhecida acima foi uma sonda dirigida, não evidência de cobertura geral.
- A sonda independente por pares `sonda_implicacao_didatica.py` apresentou ao
  `qwen3:4b-instruct` uma única frase-fonte real e uma alegação por vez. Em 23
  casos, incluindo paráfrases, contradições, detalhes plausíveis sem prova e
  alegações parcialmente sustentadas, houve **9/11 definições e 10/12
  exemplos corretos (19/23)**. Quatro alegações sem prova foram classificadas
  como contraditas; nenhuma alegação não sustentada foi aprovada nessa amostra
  pequena e correlacionada. A confusão entre ausência de prova e refutação
  já reprova o diagnóstico ternário. O mesmo modelo julgando a própria saída
  não constitui verificação independente.

**Portão:** não integrar o extrator, o julgador ou a geração ancorada na fala
diária. A etapa seguinte de comparação no runtime real **não foi executada**:
faltou primeiro uma candidata que passe o controle semântico. Próxima fronteira
de P01: obter julgamento de implicação auditável para definição *e* exemplo,
com gabarito novo e revisão humana cega, mantendo recusa de detalhes sem prova;
depois medir latência e só então comparar falas finais no caminho real.

Sonda de implicação **inédita**, com gabarito fixado antes da primeira
execução, mas ainda **sem revisão humana independente**: 24 pares em três
fontes primárias novas ([Python](https://docs.python.org/3.11/tutorial/controlflow.html),
[NASA](https://science.nasa.gov/kids/earth/what-is-the-water-cycle/) e
[OpenStax](https://openstax.org/books/physics/pages/19-2-series-circuits)).
São 12 definições e 12 exemplos, com sustentação, contradição, ausência de
prova e afirmações compostas. O classificador anterior acertou **18/24**.
Pedir ao mesmo Qwen um trecho literal rastreável elevou o rótulo a **22/24**
(11/12 em cada campo), com trecho localizado nos acertos; ainda houve **um
falso positivo de sustentação**. Em “um `for` visita `a` antes de `b` **e
imprime ambos automaticamente**”, a citação prova só a ordem da visita, mas
o julgador aprovou também a impressão. Em circuitos, classificou “todos têm
a mesma tensão” como contradito embora a frase oferecida fale apenas da
posição dos componentes. Isso falsifica falta de fonte e falha de citação
como explicações suficientes: a fonte e a citação estavam presentes; faltou
validar a **implicação completa**. As 24 chamadas de cada variante somaram
9,85 s no classificador anterior e 14,05 s no que exige citação, sem contar
busca, geração ou custos de um turno completo. São medidas locais, não SLA.

Uma segunda candidata experimental tentou exigir recibo por oração unida
por “e”. Ela bloqueou o falso positivo acima, mas acertou só **17/24** e
levou **30,04 s** nas 24 chamadas. O separador textual quebrou entidades como
“R1 e R2”; também persistiram confusões entre `sem_prova` e `contradita`.
Portanto **não há GREEN do portão**, nem justificativa para promovê-lo ao
runtime. O próximo contrato precisa representar proposições atômicas com
cobertura verificável do texto final, sem depender de cortar conjunções
superficialmente, e exigir evidência por proposição. Mesmo isso não torna o
mesmo modelo revisor independente; antes de liberar, usar outro conjunto
inédito, revisão humana cega e comparação da fala entregue no caminho real.

Nova candidata de P01, somente experimental: em vez de cortar no conectivo
“e”, o Qwen propôs segmentos com `trecho_original`, proposição autocontida,
classe e citação literal. O código exigiu que os segmentos reconstruíssem a
alegação inteira, sem perder palavras de conteúdo, e localizou cada citação
na frase-fonte. Em testes locais o contrato recusou caudas omitidas e citações
inventadas, preservando “R1 e R2” como uma única relação quando segmentado
assim. Porém, no conjunto de desenvolvimento de 24 pares, acertou só
**14/24**; frequentemente omitiu pontuação no span ou classificou ausência
de prova como contradição, e somou **43,43 s** de inferência. Zero falsos
positivos de sustentação nesta amostra não compensa a perda de cobertura.
Não transformar `invalida` em aprovação nem afrouxar a reconstrução apenas
para elevar o placar. O problema permanece na autoria/checagem semântica,
não na falta de IDs ou no transporte da fonte.

Como controle independente leve, foi baixada para o cache local (não para o
repositório) a variante ONNX uint8 do
[`multilingual-MiniLMv2-L6-mnli-xnli`](https://huggingface.co/onnx-community/multilingual-MiniLMv2-L6-mnli-xnli-ONNX).
Ela foi usada somente em CPU, com revisão e ordem de classes fixadas, sem
enviar textos a provedor remoto. O smoke inglês→português passou em **2/4**
pares e chamou de `sem_prova` uma definição sustentada e uma contradição;
por isso **não se expandiu** para os 24 casos. O modelo é rápido, mas não
passou o pré-requisito de precisão neste recorte. A observação não condena
todo NLI multilíngue; apenas falsifica esta variante/uso como portão pronto.
Controles adicionais em inglês com fontes também em inglês continuaram
classificando como neutras paráfrases sustentadas e contradições simples;
portanto a troca de idioma, isoladamente, não explica o RED observado.
O Qwen principal da Laylay não foi trocado.
Para falsificar a hipótese de que só a quantização causou o erro, a variante
ONNX de precisão completa foi testada nos mesmos quatro controles e em três
pares diagnósticos adicionais. Ela recuperou a definição positiva de Python,
mas aprovou falsamente a alegação de ordem inversa, rejeitou um exemplo
verdadeiro de circuito e chamou o exemplo composto de `for` de contradito
em vez de sem prova. Resultado: **4/7** nesse smoke ampliado, com um falso
positivo de sustentação. Nem o modelo completo, nem um veto cruzado simples
entre ele e o Qwen parece suficiente: pelos pares observados, o veto bloqueia
o falso positivo composto, mas também perde um exemplo válido de circuito.
Ambos os pesos
ONNX ficaram apenas no cache local; nenhum foi ligado à Laylay.

**Estado atualizado:** P01 segue aberta. Não houve novo holdout nem sonda
de fala real nesta rodada, pois a candidata falhou no conjunto de
desenvolvimento. Próxima alternativa a desenhar: unidades de evidência
selecionadas *antes* da redação, com uma afirmação por unidade e texto final
composto apenas depois de validar cada unidade; ainda será necessária prova
de que a redação não acrescentou relações ou números. Uma avaliação cega e
inédita, mais latência no turno real, seguem como pré-condições de promoção.

Outra primeira fronteira RED apareceu antes da geração: o extrator às vezes
truncava parágrafos no meio da frase, e títulos de busca podiam tornar uma
página editorial pouco pertinente aparentemente suficiente. O candidato
experimental agora seleciona somente frases completas, exige cobertura do
corpo em vez de confiar no título, separa os dois lados de uma comparação e
prioriza definição informativa sobre apresentação genérica. Dois testes novos
falharam na fronteira esperada antes do patch; mais controles próximos foram
adicionados. `scripts/tests/test_pesquisa_multifonte.py` e
`scripts/tests/test_explicacao_didatica_preservada.py`: 51 aprovados; com as
suítes de fundamentação factual e citação didática, 180 aprovados. Consulta
direta às páginas reais: fotossíntese trouxe cinco trechos completos; planta
baixa versus corte trouxe primeiro “vista superior” e “seção transversal”,
mas ainda incluiu três fontes genéricas. “I am” versus “I have” falhou
fechado, sem fontes aceitas. Isso melhora o material de entrada, **não** prova
fidelidade da aula nem cobertura multidomínio. O modo segue desligado por
padrão e P01 segue RED na verificação das alegações finais.

Prova posterior do caminho real (IoT simulado, multifonte experimental):
`roteiro_ensino_luz_planta-20260923-192423-262541` não consultou RGB nem
executou comando, porém o retrato ainda marcou `operacao_explicita=iot` só
pela palavra “luz”; a pesquisa ficou vazia. Esse RED revelou uma segunda
fronteira anterior à geração. O retrato agora distingue menção de operação
pelo ato do turno e preserva controles de ajuste/status. Na repetição
`roteiro_ensino_luz_planta-20260923-192654-074063`, a operação ficou vazia,
a fonte multifonte chegou ao plano e a resposta foi entregue sem comando.
Ainda houve alegações didáticas não comprovadas pela fonte, logo P01 segue RED.
A consulta de uma aula iniciada diretamente com “com um exemplo” também
incluía indevidamente esse formato no tema. Após separá-lo, a terceira sonda
`roteiro_ensino_luz_planta-20260923-192806-199040` registrou o tema correto
“o papel da luz na planta” e fonte confiável, mas a chamada principal ao Qwen
expirou em 13 s e caiu na contingência. Não há GREEN de conteúdo final nessa
terceira sonda. Seleção focada após os patches: 111 testes aprovados.

## O que a implementação já prova — e o que falhou

- `cognicao/pesquisa_multifonte.py` consulta até três variantes da dúvida,
  descobre resultados no DuckDuckGo Lite com Bing como alternativa, lê no
  máximo cinco domínios distintos e guarda URL, título, trecho e data. Snippet
  de busca não vira evidência; HTTP ruim, página privada, redirecionamento,
  falta de texto ou menos de duas páginas lidas falham fechados. O pesquisador
  original continua intacto para o modo padrão.
- O orquestrador liga o tema de ensino e o foco do exemplo ao pesquisador
  apenas no modo experimental. O prompt recebe no máximo três âncoras curtas,
  mantendo URLs e demais fontes no estado do turno. Leitura externa nunca
  autoriza comando.
- Duas sondas com 21 turnos reais, sem replay:
  `resultados_testes/roteiro_ensino_multidominio-20260923-130529-847592/`
  e `resultados_testes/roteiro_ensino_multidominio-20260923-132343-110341/`.
  Respectivamente 6/21 e 7/21 passaram sem alertas operacionais, contra
  18/21 da referência prévia. O p95 ficou perto de 20 s. Esses placares não
  medem verdade; as falas mostraram timeouts, código `for` que executaria
  três tarefas três vezes, tradução “eu sou 25”, planta baixa vista “de baixo
  para cima” e espécies botânicas atribuídas sem prova. A busca trouxe
  definições corretas para alguns turnos, mas a geração as contradisse.
- Logo a primeira fronteira ainda RED após material pertinente é a composição
  e verificação da fala, não apenas o provedor de busca. A busca HTML também
  oscila e um turno sobre “planta” sofre interferência separada da IoT. Não
  chamar duas fontes lidas de validação de todas as afirmações geradas.

Próximo portão: verificar definições e exemplos concretos contra os trechos
antes de publicar (com teste negativo de contradição), corrigir a confusão
IoT/ensino no owner próprio e comparar nova candidata no runtime completo.
Só então considerar ativação por padrão. Like não certifica fato.

## O que uma boa professora faria

Se Pedro diz “me ensina”, a Laylay deve descobrir **qual conceito** e **qual
nível** ele pediu, separar o que sabe do que precisa conferir, então entregar
uma definição, um exemplo que realmente obedeça à definição e uma conclusão.
Se ele diz “não entendi”, deve voltar ao objetivo original, questionar o que
acabou de dizer e mudar de abordagem — não defender uma analogia errada.
Uma resposta calorosa e fluente que ensina algo falso falhou.

## Primeira fronteira demonstrada

Em `resultados_testes/roteiro_ensino_multidominio-20260923-123010-079343/`,
o roteiro pedagógico e o orçamento de 512 tokens chegaram ao Qwen; os erros
factuais nasceram **na resposta HTTP**, antes do verificador. O novo
`reensino_didatico` recuperou o último pedido do usuário no runtime, mas não
consertou as definições. Uma segunda chamada ao mesmo modelo aprovou como
“sem erro” sete rascunhos, inclusive traduções e conceitos falsos. Assim,
autocrítica sem evidência externa não pode ser o critério de publicação.

## Cinco camadas, até cinco fontes úteis

1. **Entender a tarefa.** O contrato conversacional identifica objetivo,
   conceito, nível e se há pedido de reexplicação. O pedido de ensino autoriza
   uma resposta e pesquisa de leitura; não autoriza ação operacional. Guardar
   o *pedido do usuário* como fio da aula, não a resposta anterior como fato.
2. **Buscar evidência.** Consultar material local já verificado e, quando
   necessário, pesquisar a web. Tentar até cinco fontes independentes e
   relevantes, preferindo documentação, instituições educativas e fontes
   primárias. Cinco é um teto de diversidade, nunca uma quota: duas páginas
   boas valem mais que cinco snippets ou páginas inacessíveis. Manter URL,
   título, trecho, acesso, data e escopo; páginas externas são dados não
   confiáveis, jamais instruções ou permissão.
3. **Conferir o material.** Pontuar correspondência com a pergunta, qualidade
   do texto realmente lido, independência de domínios e conflitos. Extrair
   afirmações curtas com ligação ao trecho. Se a busca falha ou diverge, não
   preencher lacunas com certeza do modelo. O pesquisador contextual atual
   retornou HTTP 403 na Wikipédia PT/EN; apenas dois de quatro resultados de
   outra busca abriram no teste de física. Ele ainda não satisfaz este portão.
4. **Ensinar com presença.** A LLM compõe uma explicação natural: definição
   literal, um exemplo correto, o porquê do exemplo e uma checagem curta de
   entendimento quando útil. Adaptar linguagem e profundidade ao usuário;
   personalidade vem depois da clareza. Citar a fonte perto da afirmação que
   depende dela, sem despejar links ou transformar uma busca em aula genérica.
5. **Verificar e aprender.** Antes da entrega, testar afirmações centrais
   contra trechos observados. Matemática e código admitem checagens
   determinísticas; fatos externos precisam de fonte atual quando cabível.
   Sem evidência suficiente, delimitar o que ficou incerto e dar a melhor
   orientação honesta possível. Em “não entendi” ou dislike, armazenar o tipo
   do erro e a correção comprovada; like sozinho reforça preferência de
   apresentação, **não** converte um possível erro em verdade de treino.

## Escolhas arquiteturais

- O orquestrador cognitivo é dono da decisão “precisa de fundamentação?”; o
  pesquisador é dono de buscar/avaliar páginas; o modelo é autor da fala; o
  verificador compara afirmações com evidência. Nenhuma camada ganha poder de
  executar comandos por pesquisar ou ensinar.
- A pesquisa pode ser dispensada para operações verificáveis localmente e
  fatos presentes em corpus curado com proveniência. É obrigatória para
  informação recente, alegações específicas sem memória confiável e assuntos
  de alto risco. Não usar a autoconfiança verbal do Qwen como portão.
- A indisponibilidade de fonte não vira nem “pronto, confirmei” nem fallback
  repetitivo. A Laylay distingue conceito que consegue explicar de detalhe
  que não confirmou e pode oferecer continuar pesquisando.
- Medir separadamente: acerto factual, relevância, clareza para iniciante,
  reparo após “não entendi”, fontes válidas, latência, ausência de comandos e
  honestidade diante de falha de rede. Um placar 21/21 sem comandos não aprova
  ensino. Comparar baseline e candidato com os mesmos 21 turnos mais assuntos
  inéditos, revisão humana cega e exemplos errados como controles negativos.

## Sequência segura de experimento

1. Criar corpus de avaliação com a sonda real e anotações de conceitos certos,
   erros graves e qualidade da aula em vários domínios; preservar o baseline.
2. Prototipar recuperação somente leitura fora do runtime. Provar que pelo
   menos duas fontes abertas sustentam cada afirmação usada, que páginas 403
   não passam e que conteúdo de site não vira instrução operacional.
3. Comparar geração com/sem evidência em isolamento, com o mesmo Qwen e
   entradas pareadas. Só integrar se corrigir erros **sem** degradar clareza,
   tempo de resposta e segurança.
4. Integrar no owner cognitivo com orçamento/observabilidade e testar
   composição real; depois repetir o roteiro completo sem replay. Não
   promover apenas por teste de mock ou nota de execução do caos.

## Referências de arquitetura (inspiração, não dependência de API)

- [RAG, artigo original](https://arxiv.org/abs/2005.11401): combinar geração
  com material recuperado para tarefas intensivas em conhecimento.
- [Corrective RAG, artigo original](https://arxiv.org/abs/2401.15884): avaliar
  a qualidade do material recuperado antes de usá-lo; buscar novamente se
  ele for fraco.
- [ReAct, artigo original](https://arxiv.org/abs/2210.03629): intercalar
  raciocínio e consulta a ferramentas/fontes em vez de confiar só no texto
  lembrado pelo modelo.
- [Estudo de autocorreção sem feedback](https://arxiv.org/abs/2310.01798):
  revisão puramente interna pode falhar — consistente com a sonda local.
- [Documentação oficial OpenAI: ferramentas](https://developers.openai.com/api/docs/guides/tools)
  e [avaliação de agentes](https://developers.openai.com/api/docs/guides/agent-evals):
  inspiração para separar ferramentas, rastros e avaliação fim a fim.

## Medição seguinte de P01 — unidades e implicação (23/09)

- `scripts/analises/contrato_unidades_ensino.py` é um contrato **offline**:
  trecho localizado, cópia literal e conta aritmética conferida recebem estados
  diferentes. A alegação invertida sobre planta baixa continua pendente mesmo
  quando `montar_fundamentacao` marca a pesquisa como confiável. Texto literal
  da página não prova verdade universal nem relação definição–exemplo. Oito
  testes novos cobrem esse limite; nenhum código de produção usa a sonda.
- `scripts/analises/sonda_implicacao_contramundo.py` tentou falsificar a
  implicação antes da aprovação. No desenvolvimento antigo de 24 pares, a
  classificação ternária ficou em **18/24**, sem falso suporte observado; cinco
  contradições copiaram a própria alegação em vez da fonte e foram inválidas,
  além de uma ausência de prova classificada como contradição. Não trocar a
  classificação inválida por sucesso aparente.
- O holdout `holdout_implicacao_ensino_v2.py` foi congelado **antes da primeira
  medição**: 24 pares balanceados em quatro temas, com definições e exemplos.
  Usa documentação Python, NASA e RHS. No portão binário seletivo, que só
  aceita `sustentada` com trecho localizado, tanto o verificador anterior
  quanto o contramundo aceitaram **8/8 sustentadas e 0/16 não sustentadas**;
  latências totais de **14,18 s** e **14,9 s**, respectivamente. Portanto o
  contramundo **não demonstrou ganho** frente à opção simples. O conjunto é
  pequeno, tem gabarito elaborado pelo agente sem revisão humana independente,
  e ficou consumido: não ajustar a candidata usando esses 24 casos e depois
  apresentá-los como inéditos.
- **P01 continua aberta.** Nenhuma dessas métricas verifica automaticamente a
  decomposição de uma resposta inteira em alegações, a verdade da página,
  a relação pedagógica entre definição e exemplo, nem a fala entregue no
  runtime. Próximo experimento útil: aferir essa decomposição e a cobertura
  de cada afirmação da fala real; não ativar pesquisa ou verificador novo no
  uso diário por causa deste 8/8.

## Auditoria da fala inteira entregue (23/09)

Base congelada nesta leitura: `bd94bc3e3a29c49906dc603f9ca1540310ca3274`,
com worktree paralela suja. Foram cruzados `conversa.md`, `planos.jsonl`,
`fundamentacao_factual` e `ultima_verificacao`, não apenas o `fala_planejada`:
este último contém um trecho truncado da fala e não serve para medir a aula
inteira. A auditoria abaixo se refere à evidência **capturada naquele turno**;
não certifica a veracidade externa de cada página.

| Fala real | O que a evidência alcança | Primeira divergência observável |
| --- | --- | --- |
| Divisão, turno 002 de `roteiro_ensino_multidominio-20260923-132343-110341`: 12 objetos / 3 pessoas e exemplo novo de 15 / 3 | O trecho da SME Goiânia explica repartição igual. As duas contas e o vínculo entre 3 grupos e 4 ou 5 objetos podem ser conferidos aritmeticamente, sem confiar no Qwen como juiz. Controle positivo; isso **não** valida os outros domínios. | Nenhuma incorreção central identificada nessa fala; ainda falta uma verificação automática da conta e de todos os acréscimos antes da publicação. |
| Luz, turno 001 de `roteiro_ensino_luz_planta-20260923-192654-074063`: fotossíntese e girassol | O trecho de Jardineriaon sustenta que girassóis jovens acompanham o sol e cita alongamento diferencial. Os excertos preservados não sustentam a produção de *glucose e oxigênio*, nem a direção específica “lado esquerdo ou direito”. Uma das cinco páginas preservadas é completamente fora de assunto (demanda global de metal). | `fundamentacao_factual.confiavel=True` é confiança **no tema**, não recibo por alegação; depois a fala acrescenta detalhes e `ultima_verificacao.aceita=True` sem detectar essa lacuna. Não afirmar que os detalhes são falsos no mundo apenas por faltar prova no trecho. |
| Arquitetura, turno 014 de `roteiro_ensino_multidominio-20260923-132343-110341`: planta baixa vista “de baixo para cima” | O plano desse turno registra `confiavel=False`, zero fontes. A resposta entregue ensina direção invertida e acrescenta teto de madeira e tubo de ventilação como se fossem dados da casa. | O seguimento perdeu fundamentação verificável **antes** da composição; o texto incorreto chegou à resposta e `ultima_verificacao.aceita=True`. Não atribuir este turno a uma fonte correta que chegou a outro turno/sonda. |
| Floricultura, turno 021 do mesmo roteiro: anuais, perenes, begônia fúcsia e tuberosa | A definição de anual em uma estação e a longevidade das perenes têm apoio nos excertos. O excerto que cita begônia fúcsia e tuberosa as trata como perenes sensíveis ao frio, cultivadas como anuais em climas frios. A fala tornou “begônia fúcsia — planta anual” incondicional e inventou calendário inverno/verão/inverno. A tuberosa recebeu ressalva climática. | Há fonte no plano, mas a geração apagou a condição do exemplo. `ultima_verificacao.aceita=True` apesar da ligação definição–exemplo errada. A citação ao fim não dá suporte coletivo a todas as frases. |

O controle negativo mais importante é o contraste entre floricultura e
arquitetura: **fonte presente, usada com qualificador perdido** é diferente de
**fonte ausente no turno**. Ambos chegaram à fala, mas não têm a mesma primeira
fronteira RED. A sonda `scripts/analises/auditoria_fala_integral.py` apenas
garante que uma revisão humana cubra a fala inteira, inclusive caudas e frases
mistas, e que citações alegadas existam nos trechos preservados. Não julga
implicação semântica, não substitui conferência humana e não participa do
runtime. Seus seis testes locais passaram; nenhuma produção foi alterada.

Próximo contrato a testar: cada alegação verificável da resposta final deve
ter fonte específica que a implique, cálculo/código conferido ou incerteza
expressa; um exemplo não pode perder as condições da fonte. Antes de ligar
um portão ao runtime, medir cobertura, falso bloqueio de aulas corretas,
falso aceite de frases mistas e latência em novas falas reais com gabarito
revisado independentemente. O par de 24 alegações anterior não mede isso.

## Portão offline de falas reais completas — resultado RED (23/09)

`scripts/analises/sonda_fala_integral_real.py` congela os hashes de quatro
pares `conversa.md`/`planos.jsonl` do runtime, confere que a fala avaliada
foi a efetivamente entregue e exige uma decisão para cada uma das 38 partes
da resposta. Os rótulos por sentença foram definidos **antes** da primeira
chamada ao Qwen, mas elaborados pelo próprio agente: são um gabarito
provisório, **não** uma revisão independente. O juiz usa
`qwen3:4b-instruct`, o mesmo modelo da geração, em uma chamada por fala.

Na repetição após corrigir somente a contabilização da métrica (não o
prompt nem os rótulos), a latência agregada foi **32,78 s**; mediana por
fala **8,82 s**, com variação de 4,72 a 10,41 s. São quatro amostras num
Ollama local, não uma promessa de latência de produção.

| Fala | Resultado do portão offline |
| --- | --- |
| Divisão, 13 partes | A saída cobriu as partes e não bloqueou o exemplo correto. Porém **sete propostas de aceite não têm recibo numérico independente**: a citação de uma regra geral de repartição não prova `12 / 3 = 4`, `15 / 3 = 5` ou a coerência dos grupos. O `0` em falso bloqueio não é aprovação da aula. |
| Luz, 5 partes | **Dois falsos aceites**: a fonte citada para a frase inicial só fala da importância da luz para a fotossíntese, não prova o acréscimo “glucose e oxigênio”; a fonte citada para a adaptação fala de alongamento diferencial, não da consequência alegada. O trecho sobre girassóis jovens foi localizado; o detalhe esquerda/direita ficou sem prova. |
| Arquitetura, 12 partes | Saída inteira inválida (`citacao_2`): o juiz propôs suporte literal para uma frase sem nenhuma fonte no plano. O validador de proveniência rejeitou a resposta; isso é falha fechada, não evidência de que a explicação foi corrigida. |
| Floricultura, 8 partes | Saída inteira inválida (`citacao_6`): a citação apresentada não é substring da fonte preservada. As duas partes positivamente rotuladas ficaram bloqueadas pelo fail-closed. Esse resultado não permite avaliar a semântica das demais propostas da saída descartada. |

Primeira fronteira RED do candidato: **citação localizada não implica a frase
inteira**. O caso da luz é uma prova direta de que o mesmo Qwen aceita uma
frase mista por sua metade fácil. Há também uma fronteira separada para
cálculos: o rótulo `calculo` ou `sustentada` emitido pela LLM não é validação
aritmética. A estrutura de cobertura funcionou, mas o portão semântico não.
Nenhum desses resultados autoriza ligar o juiz ao runtime ou treinar com likes.

Antes de outro candidato: obter revisão humana independente dos rótulos,
adicionar conferência determinística de contas e comportamento de código,
e medir o juiz por **alegação composta**, não apenas pela sentença que a
contém. Repetir em falas inéditas depois de congelar novo gabarito; este
conjunto já foi consumido e não deve ser ajustado para fabricar holdout verde.

## Continuação do portão — contas e afirmações compostas (23/09)

O primeiro RED factual foi reproduzido em uma frase menor, sem depender de
segmentação: diante de “transformar dióxido de carbono e água em glucose e
oxigênio”, o Qwen respondeu **sustentada** e citou somente um trecho sobre a
importância da luz para a fotossíntese. Separar a oração por travessão,
portanto, **não corrige** a implicação. Na mesma sonda, ele classificou como
`sem_prova` a consequência de que uma adaptação faz a planta captar mais luz;
o comportamento do mesmo juiz não é uniforme. A primeira fronteira RED
continua sendo a inferência fonte → alegação, não a falta de IDs ou a
extensão da frase.

`extrair_contas_explicitas` em `contrato_unidades_ensino.py` agora confere
somente operações inteiras escritas literalmente (divisão e multiplicação),
com spans preservados. Na fala real de divisão, encontrou e verificou as
duas ocorrências de `12 dividido por 3 = 4`. Uma conta errada ou divisão por
zero não vira recibo. As outras cinco partes matemáticas da fala, inclusive
“Aí seria 5 por pessoa”, seguem **pendentes**: dependem do contexto e não
ganham validade pelo acerto das duas equações. A verificação da conta tampouco
aprova uma cauda extra na mesma frase.

Como tentativa de veto, `veto_lexical_ensino.py` procura palavras de conteúdo
da afirmação que não aparecem na citação escolhida. No material real de luz,
o veto detecta “dióxido”, “carbono”, “glucose” e “oxigênio” ausentes, e também
os termos sem rastro da frase sobre captar mais luz. Porém barraria **também**
o exemplo verdadeiro do girassol por diferença lexical entre “seguindo” e
“acompanhando”. Aplicado ao mesmo rascunho da divisão, vetou **7/7** partes
matemáticas consideradas corretas no gabarito provisório, inclusive as duas
equações conferidas por código. Na repetição da fala sobre luz, o Qwen
produziu uma citação não localizada (`citacao_0`); o portão fechou antes da
comparação lexical. A variação reforça que uma única execução não é métrica
estável de produção.

Conclusão: o cálculo literal é uma **capacidade parcial comprovada offline**;
o veto lexical é **rejeitado como portão de fala** por falso bloqueio. Ele
também não detectaria uma relação invertida composta das mesmas palavras.
Não integrar nenhum dos dois ao runtime nesta etapa. A próxima arquitetura
deve representar alegações e condições vindas das fontes **antes** da
redação, com verificação independente da saída, e aferir exemplos em que
sinônimos são legítimos, qualificadores são obrigatórios e termos novos são
falsos. Não voltar a treinar ou ajustar sobre estes mesmos quatro discursos
como se fossem holdout.

## Protótipo de composição por evidência anterior à fala (23/09)

`scripts/analises/sonda_composicao_extrativa_ensino.py` experimenta a
fronteira seguinte, ainda **sem modificar a Laylay**. Um curador escolhe
unidades literalmente presentes nos trechos capturados pelo runtime; o
código valida URL, localização, completude e que o texto apresentado difere
do original apenas em caixa/espaçamento. Contas inteiras explícitas passam
por verificação aritmética. Só depois o compositor monta a resposta, e o
auditor a reconstrói integralmente: qualquer frase acrescentada fora das
unidades causa rejeição. URLs ficam nos recibos por span, **não** na fala.
Padrões de instrução externa já detectados pelo projeto são rejeitados; isso
não é uma prova exaustiva contra toda injeção em página.

Nos quatro casos históricos congelados:

| Tema | Resultado offline | Limite pedagógico |
| --- | --- | --- |
| Divisão | Uma definição literal e `12 / 3 = 4` calculado; fala de 132 caracteres, sem URL pronunciada. | Não prova que os operandos desempenham os papéis que o usuário quis nem explica por que cada pessoa recebe quatro. A unidade marca `mapeamento_de_entidades_verificado=False`. |
| Luz | Definição curta e exemplo literal dos girassóis; fala de 279 caracteres. Não aparecem “glucose e oxigênio” sem fonte. | A fonte lida é editorial e o texto não explica a relação causal entre seguir o sol e fotossíntese. Não confundir ausência de acréscimo com aula completa. |
| Floricultura | Duas definições e janela literal com três frases; a ressalva quente/frio permanece junto de begônias e tuberosas. Fala de 571 caracteres. | Está compreensível, mas ainda é sobretudo uma sequência de citações sem uma síntese própria segura para iniciante. A verdade externa das páginas não foi auditada. |
| Arquitetura | `aula_incompleta`: o turno final histórico não tinha fonte, então não há fala composta. | Falhar fechado evita ensinar a direção invertida, mas também não atende ao usuário; falta recuperar evidência no fluxo real. |

O protótipo demonstra **transporte sem acréscimo factual** e preservação da
condição naquele exemplo curado, não solução geral. A escolha dos trechos
foi manual e sobre artefatos já conhecidos; não há métrica de recuperação
automática, avaliação humana independente de naturalidade, prova de verdade
da página ou GREEN de runtime. O verificador de forma não aprova a relação
semântica entre definição e exemplo. Próxima fronteira: seleção automática
de unidades *autossuficientes* com dependências de contexto explícitas,
qualidade da fonte e papel dos números; depois testar uma fala didática
natural que não acrescente alegações. Não promover este render extrativo
para o uso diário só porque passou no contrato formal.

## Sonda de seleção automática de evidências (24/09)

`scripts/analises/sonda_selecao_evidencias_ensino.py` acrescenta uma etapa
**offline** entre a leitura já capturada e o compositor. Reutiliza a separação
de frases completas da pesquisa multifonte e o validador literal da sonda
anterior. O assunto vem do `tema` preservado no plano do turno, necessário
quando o pedido atual é apenas “não entendi”. Seleciona candidatos a
definição/exemplo por estrutura e sobreposição lexical, sem chamar a LLM ou
fazer nova pesquisa. Um exemplo anafórico deve carregar o antecedente e a
condição contíguos; sem antecedente, fica pendente. Instrução externa,
trecho incompleto e página só parecida com o assunto não viram evidência.

O primeiro RED revelou que sobreposição lexical confundia “O fotoperíodo,
que se refere...” com definição do papel da luz e uma pergunta introdutória
com definição de plantas anuais. Um controle adversarial adicional revelou
que “Em um estudo sobre luz, a clorofila é...” e “Na aula sobre luz, um
exemplo de bactéria...” também passavam por mera menção no preâmbulo. Os
testes agora barram esses formatos. Isso **não** prova classificação
semântica geral; apenas delimita os padrões observados.

Na comparação com os quatro artefatos históricos já consumidos, a seleção
automática entregou unidades suficientes para a composição literal de
**1/4** (floricultura). A janela de begônias mantém a distinção entre
clima quente e frio. Divisão recuperou a definição de repartir em partes
iguais, mas não um exemplo vinculado com papéis numéricos verificados.
Luz recuperou a frase sobre fotossíntese, mas deixou o exemplo dos
girassóis como `ligacao_semantica_pendente`, porque “sol” e “luz/planta” não
foram demonstrados como vínculo pelo filtro lexical. Arquitetura não tinha
fontes naquele turno. Os três casos permanecem `aula_incompleta` e **não**
representam resposta aceitável para uso diário.

Resultado de teste local: 22 testes focados passaram (seleção, composição e
artefatos congelados). Ainda faltam: avaliação humana independente dos
papéis pedagógicos e da verdade das páginas, recuperação que cubra relações
por paráfrase sem aceitar assunto só parecido, mapeamento de números para
entidades do pedido, evidência útil quando um turno anterior não forneceu
fontes, e prova de naturalidade/runtime. Nenhum componente de produção foi
alterado nem esse seletor foi ligado à fala da Laylay.

## Paráfrase: recuperação sem autorização semântica (24/09)

`scripts/analises/sonda_relacao_semantica_ensino.py` avaliou o encoder ONNX
multilíngue **já disponível localmente**, com o artefato e SHA usados pela
frente neural. Os quatro contrastes foram escritos antes da primeira
inferência. Os positivos de luz/girassol e floricultura vêm dos trechos
históricos congelados; os negativos são controles sintéticos com tema e
vocabulário próximos, inclusive condição invertida. O rótulo aqui mede
*relevância à consulta*, não verdade da página nem suficiência da aula.

O encoder ordenou **2/4** pares corretamente. Para girassóis, o positivo
ficou acima do negativo (0,5371 vs 0,3438). Porém, em luz/fotossíntese,
o texto que só **mencionava** o tema foi mais similar que a frase explicativa
(0,7901 vs 0,6701). Na floricultura, a versão com a condição **invertida**
superou a correta (0,8160 vs 0,7822). Em divisão, a troca dos papéis de
12 objetos e 3 pessoas quase empatou (0,8792 vs 0,8734). Assim, similaridade
vetorial não pode ser o portão que aceita evidências para a fala; um limiar
ou o primeiro resultado da lista daria falsos aceites nesse conjunto.

Foi acrescentada apenas uma **fila offline de revisão** para candidatos
perdidos pelo filtro lexical. No caso real da luz, o exemplo F3 dos
girassóis reaparece com texto e fonte preservados, mas continua marcado
`revisao_semantica_pendente` e `aprovado_para_compor=False`; a aula não é
publicada por isso. Os 26 testes focados de seleção, contraste, composição
e artefatos congelados passaram. Nenhum novo caminho foi ligado ao runtime.

Próxima fronteira: um contrato verificável de **relação, direção e condições**
entre pedido, definição e exemplo, avaliado em dados novos anotados por
humano. O recuperador pode propor; só esse julgamento independente, junto
com proveniência literal e recibos de cálculo quando houver números, poderia
autorizar composição. Não ajustar o encoder nem escolher limiar olhando
esses quatro contrastes já consumidos.

## Vínculo definição–exemplo: primeira fronteira RED (24/09)

O compositor extrativo anterior exige uma unidade rotulada `definicao` e uma
rotulada `exemplo`, mas **não verifica se as duas afirmam a mesma relação**.
Essa é a primeira fronteira RED depois da proveniência literal. Dois
controles nos próprios trechos históricos mostram a diferença:

- A frase “luz é essencial para fotossíntese” e o trecho “girassóis jovens
  acompanham o sol” são ambos rastreáveis e rendem `forma_rastreavel`, mas o
  segundo não exemplifica diretamente a relação de fotossíntese.
- Na floricultura, “plantas anuais completam seu ciclo numa estação” e
  “certas perenes são cultivadas como anuais em climas frios” também rendem
  `forma_rastreavel`. O segundo é uma **exceção/contextualização** à comparação,
  não um exemplo direto do ciclo de vida descrito na primeira definição.

`scripts/analises/contrato_vinculo_didatico.py` é uma sonda **offline** que
recebe relações anotadas explicitamente e confere, nessa ordem: trechos
literais localizados, identidade da relação, direção/papéis e condições
obrigatórias. Os testes cobrem também divisão com papéis invertidos e clima
omitido. Uma estrutura que passa recebe apenas
`estrutura_compativel_revisao_pendente`; **nunca**
`aprovado_para_compor=True`. A anotação da relação ainda é feita manualmente
pela própria investigação, sem revisão humana independente; localizar suas
palavras na página não prova que o rótulo semântico está correto.

Foram **33 testes focados verdes** no conjunto de vínculo, recuperação,
seleção, composição e artefatos congelados. Isto não transforma o antigo
`1/4` em aula aprovada: aquele número permanece somente sucesso de
**transporte literal**. A primeira correção arquitetural necessária é
representar o tipo de vínculo (`exemplo_direto`, `excecao`, `analogia` ou
`sem_vinculo`) antes da redação, e exigir prova para qualquer frase de ponte.
Ainda faltam dados novos com avaliação humana independente, extração
confiável dessas relações e validação da fala final no runtime. Nenhum
arquivo de produção foi modificado por esta sonda.

## Extração automática de vínculo: piloto com dados novos (24/09)

Foi congelado, antes da primeira inferência, o conjunto sintético
`scripts/analises/dados/vinculos_ensino_sinteticos_v1.jsonl` (SHA-256
`9994e07f421bca5ba86f82f9bf7d60ea06663d946820c5ab80e3bed7317efe74`).
São 16 pares distribuídos em irrigação, arquitetura, programação e culinária:
8 de desenvolvimento e 8 de reserva por **domínio inteiro**, sem vazamento
de paráfrases irmãs entre splits. Há exemplos diretos, outras relações,
inversão de papéis, condição omitida e analogia. Todos os trechos são
autoria sintética desta investigação; não medem qualidade de fontes web.
Os rótulos são **provisórios do agente**, sem revisão humana independente.

`scripts/analises/sonda_extracao_vinculo_ensino_v1.py` enviou somente os
dois textos, não o gabarito, ao Ollama local `qwen3:4b-instruct` (digest
observado `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`).
O modelo propôs classe, relação, papéis, condições e citações literais; o
código conferiu formato, fonte das citações e estrutura separadamente.

Na primeira leitura de desenvolvimento, o modo JSON livre produziu **8/8
saídas inválidas**: o modelo usou `tipo` para nomear a relação e devolveu
papéis como listas, não como objetos. Essa execução não mediu acerto
semântico. A segunda leitura mudou **somente o contrato de saída** para
[JSON Schema no parâmetro `format` do Ollama](https://ollama.com/blog/structured-outputs),
mantendo dataset e rótulos congelados. Resultado: 8/8 saídas formalmente
válidas, **4/8 classes corretas** contra o gabarito provisório e **2 falsos
`exemplo_direto`**:

- `IRR-02`: o modelo aceitou a bomba ligada sem o modo automático informado.
- `ARQ-02`: o modelo tratou o corte vertical como exemplo direto da planta
  baixa, embora mostrem relações espaciais diferentes.

As citações desses falsos aceites estavam literalmente nos textos. Portanto
o primeiro RED atual é **interpretação de relação e condição**, não falta de
JSON ou de provenance. A anotação livre de `relacao` também produziu formas
como `liga`/`ligou`; o contrato estrutural as tratou como diferentes até nos
positivos. Não corrigir isso com stemming local sobre os mesmos oito pares:
o owner futuro precisa de representação canônica de predicado, papéis e
qualificadores, com revisão independente de seu alinhamento ao trecho.

A reserva de programação/culinária **não foi executada** porque o candidato
já falhou em desenvolvimento. Foram 38 testes focados verdes para os
contratos locais e controles de segurança, mas isso não muda o RED
semântico nem aprova o ensino no runtime. Nenhum arquivo de produção foi
alterado. Próxima decisão arquitetural: separar proposta de relação,
normalização semântica e julgamento independente; só então avaliar um
novo candidato em desenvolvimento e, se passar sem falsos diretos, abrir a
reserva congelada.

## Primeira fronteira RED dos requisitos: extração da definição (24/09)

Antes de pedir ao modelo que julgue um exemplo, é necessário saber quais
partes da **definição** são obrigatórias. A sonda offline
`scripts/analises/contrato_requisitos_ensino.py` separa requisitos, seus
trechos de origem e os trechos propostos do exemplo. A conferência por código
rejeita IDs ausentes e citações inventadas, compara somente um limiar numérico
simples e deixa condições textuais, paráfrases, papéis e direção em revisão.
Mesmo quando tudo está localizado, `aprovado_para_compor` permanece falso.
Isso evita que a simples presença de “atravessa a escada” em “sem informar se
atravessa a escada” vire prova da condição.

Na sonda `sonda_alinhamento_requisitos_ensino.py`, requisitos curados apenas
para os oito casos de desenvolvimento foram alinhados pelo Qwen a trechos do
exemplo. Os dois falsos diretos anteriores (`IRR-02`, `ARQ-02`) receberam
`requisito_faltante`, mas o positivo `IRR-01` foi invalidado porque o modelo
copiou “abaixo de 20%” da definição em lugar de citar “15%” do exemplo.
Inversão de papéis e analogia continuam em revisão; o alinhador não as
resolve. Resultado: quatro faltantes, um alinhamento inválido, três revisões
pendentes e **zero aprovações**.

Foi então testada a fronteira anterior em três definições únicas de
desenvolvimento, dando ao Qwen **somente a definição**, sem exemplos, IDs de
requisitos ou gabarito. A instrução e os dados foram congelados antes da
chamada: SHA-256 do script
`9FB5276F4D387D51C54791F381C9B5765DBFF85483A40180A694E30377DDD78D`;
SHA-256 do dataset
`9994E07F421BCA5BA86F82F9BF7D60EA06663D946820C5AB80E3BED7317EFE74`.

| Definição | Validação literal | Primeira divergência observada |
| --- | --- | --- |
| `IRR-01` | válida | omitiu o qualificador obrigatório “modo automático” |
| `ARQ-01` | inválida | inventou “posicao das paredes/portas”, sem acento e sem trecho literal correspondente |
| `ARQ-04` | inválida | devolveu “quando...” em minúscula quando a definição traz “Quando...” |

A omissão em `IRR-01` sustenta uma falha **de cobertura semântica**; as duas
falhas de arquitetura sustentam um problema separado de **transporte literal**.
Não são três provas de uma mesma causa. Uma comparação tolerante a caixa ou
acentos poderia resolver parte do transporte, mas não tornaria a condição
omitida presente nem provaria papéis e direção. Portanto não alteramos o
contrato para produzir um verde cosmético. Foram 12 testes focados verdes
para os contratos das duas sondas e a sonda de definição; são apenas provas
locais. A reserva permanece fechada e nenhum arquivo de produção foi
alterado.

Próxima hipótese a falsificar: enumerar por código todos os trechos/cláusulas
da definição **antes** da proposta semântica, mantendo seus offsets originais.
O modelo poderia escolher índices em vez de reescrever citações; uma decisão
de ignorar uma cláusula qualificadora ficaria explícita e auditável. Isso só
resolve transporte e rastreabilidade. Ainda exigirá julgamento independente
de obrigatoriedade, equivalência, papéis e condições, seguido de teste da
fala final no runtime real antes de qualquer promoção.

## Índices de cláusulas: transporte GREEN, seleção RED (24/09)

O experimento acima foi executado em
`scripts/analises/sonda_indices_requisitos_ensino.py`. O código segmenta
definições curtas por vírgula/ponto-e-vírgula e fornece índice e offsets de
cada fatia literal. O Qwen devolve somente os índices que considera
necessários; nunca reescreve o trecho. O script SHA-256
`79ADB49613EDE7D6577E4657B1CB65481805B18D1FAA135967435E8414FCC485`
e o dataset de desenvolvimento SHA-256
`9994E07F421BCA5BA86F82F9BF7D60EA06663D946820C5AB80E3BED7317EFE74`
foram congelados antes das três chamadas. A reserva não foi aberta.

| Caso | Índices selecionados | Resultado |
| --- | --- | --- |
| `IRR-01` | `[0, 1, 2]` | todos os requisitos curados cobertos; interpretação ainda pendente |
| `ARQ-01` | `[1]` | omitiu `[0]`, “Na planta baixa”, e portanto o tipo do desenho |
| `ARQ-04` | `[]` | omitiu ambas as cláusulas, inclusive a condição de atravessar a escada |

As três respostas eram formalmente válidas; o código localizou exatamente o
que foi omitido, sem falsos trechos. Foram quatro testes novos GREEN para
offsets, índice inventado/repetido, falta de requisito e ausência de
exemplo/gabarito no prompt. **Primeira fronteira RED atual:** decidir por
modelo quais cláusulas são obrigatórias. Não sabemos por que ele devolveu
lista vazia em `ARQ-04`; o texto e os índices chegaram íntegros. Não atribuir
essa falha ao transporte literal ou concluir que outro prompt já resolveria.

O contrato candidato seguinte deve ser *conservativo por construção*:
preservar todas as cláusulas da definição no envelope de evidência, deixando
o modelo apenas propor papéis e correspondências. Qualquer descarte de uma
cláusula exige uma decisão justificada e verificável; se a justificativa não
for confiável, a cláusula permanece obrigatória ou a aula fica pendente.
Esse desenho pode bloquear aulas corretas, portanto a taxa de falso bloqueio
precisa ser medida. Continua faltando julgamento independente de semântica,
dados revisados, exemplo sustentado, auditoria da fala inteira e integração
testada no runtime. Nenhum código de produção foi alterado.

## Envelope conservativo: proteção parcial e falso bloqueio medido (24/09)

`scripts/analises/sonda_envelope_clausulas_ensino.py` implementa somente
um contrato offline: **todas** as cláusulas com offsets originais ficam
ativas; o Qwen deve propor um trecho literal do exemplo para cada índice,
ou vazio. A proposta não tem campo para excluir cláusulas. Falta de índice,
duplicata e trecho inventado falham fechados. Mesmo com todos os trechos,
papéis, condições e equivalência não são verificados; não há aprovação para
composição ou publicação. Script congelado antes da rodada: SHA-256
`B9D8B59B5CB48EC9E807FF6268F47B005364F8AAEC89F3AA9471DD4C7BC0F068`;
dataset congelado sem alteração. O prompt não recebeu rótulos esperados nem
requisitos manualmente curados; a reserva permaneceu fechada.

Nos oito casos de desenvolvimento: cinco saíram com pelo menos uma cláusula
sem evidência, dois com trecho inventado (um deles o caso de papéis
invertidos), e um com evidência literal em todas as cláusulas, **sempre
pendente de revisão semântica**. Dos seis negativos provisórios, nenhum
recebeu sequer evidência literal completa validada. Isso mede a contenção
nesse conjunto pequeno, não taxa real de falso aceite. Dos dois positivos,
`ARQ-01` teve alinhamentos literais completos porém ainda não foi aprovado;
`IRR-01` sofreu **falso bloqueio**: o modelo deixou vazio o trecho para
“se a umidade do solo cair abaixo de 20%”, apesar de o exemplo informar
“15%”. O contrato de comparação numérica anterior consegue conferir a
desigualdade *quando recebe o span correto*, mas o alinhamento automático
não o forneceu. O caso `ARQ-04` também mostra que o Qwen ainda pode citar
texto da definição em vez do exemplo; o portão literal rejeitou isso.

Primeira fronteira RED agora: recuperar e relacionar **valores e entidades
do exemplo** com a condição da cláusula, sem que o mesmo modelo invente a
ponte ou omita a informação. Uma tentativa só de melhorar o prompt nos
mesmos oito casos não seria evidência generalizável. Próxima prova deve usar
extração tipada e comparação determinística onde possível, com negativos
de número, unidade, entidade, negação e papéis; depois medir falso bloqueio
em dados independentes revisados. Ainda falta comprovar a fala completa no
runtime real. Nenhum código de produção foi alterado.

## Limiar numérico tipado: conta provada, entidade ainda RED (24/09)

O contrato offline `scripts/analises/contrato_requisitos_ensino.py` agora
localiza um **único** valor com unidade no exemplo e reutiliza seu comparador
de `menor_que`. Ausência de valor, unidade diferente, vários valores e
negação antes da leitura não recebem confirmação. O resultado transporta o
trecho literal e separa `comparacao_numerica=True` de
`entidade_verificada=False`, `modo_verificado=False` e
`papeis_verificados=False`; `aprovado_para_compor` segue falso. Controles
em porcentagem, °C e kg evitam um remendo exclusivo de irrigação. O caso
“desconto de 15%” pode satisfazer a **desigualdade**, mas fica explicitamente
sem prova de que mede a umidade; não serve como exemplo da definição.

Na repetição dos oito casos de desenvolvimento, o Qwen continuou deixando
vazia a cláusula de limiar de `IRR-01`. O código acrescentou uma *pista*
numérica `15% < 20%`, sem preencher silenciosamente o alinhamento nem liberar
a fala. `IRR-02` recebeu a mesma pista, mas continua sem modo automático;
isso falsifica a ideia de que conferir só a conta resolveria os falsos
diretos. `IRR-03` seguiu rejeitado por trecho inventado no alinhamento do
modelo; a comparação direta isolada ainda encontra 15%, mas não confirma os
papéis invertidos. O caso `IRR-04` não contém leitura numérica. Arquitetura
permanece como na rodada anterior. A reserva continua fechada.

A primeira fronteira ainda aberta é **ligar o valor à entidade e à condição
corretas**, incluindo referências implícitas como “15% de umidade” versus
“umidade do solo”. A curadoria provisória considera `IRR-01` direto, mas
esse elo não é textual e independente o bastante para ser certificado pelo
comparador. Antes de uso real, precisamos medir esse elo em dados revisados,
com controles de desconto, umidade do ar/solo, números múltiplos, escopo de
negação e papéis. A sonda de desenvolvimento não prova qualidade da aula
entregue. Nenhum código de produção foi alterado.

## Rótulo da grandeza: contexto implícito continua pendente (24/09)

O contrato offline agora distingue o **rótulo textual** da grandeza junto ao
valor. Com um limiar em definição curta (`se/quando a/o [grandeza]
cair/ficar/estiver/for abaixo de ...`) e um rótulo explícito após o valor
do exemplo, ele diferencia:

- `15% de umidade do solo`: rótulo literal igual, ainda **sem** comprovar
  medição, condição, modo, direção ou papéis;
- `15% de umidade`: falta o qualificador “do solo”;
- `15% de umidade do ar`: qualificador textual divergente;
- `15% de desconto`: rótulo diferente;
- `15%` sem rótulo, múltiplos valores ou negação: pendente/fail-closed.

O mesmo contrato foi testado com “temperatura da água” em °C. Não é um parser
geral de entidades: construções fora desse formato retornam indeterminação,
e correspondência literal não valida verdade externa. O envelope de todas
as cláusulas expõe esse diagnóstico por índice, mas não remove cláusulas nem
aprova composição. Na repetição dos oito exemplos de desenvolvimento, os
dois casos `IRR-01` e `IRR-02` ficaram com `qualificador_ausente`; os outros
estados permaneceram na mesma fronteira. O script desta rodada tinha SHA-256
`7F0ED17FB33B1812AFC7A93266B1EFB3E153197C1CBFEA29A93A2006478406D0`
para o contrato e
`55373F87A3CA9F201B6B894CDCC7836426F5469934A5E4866C76B50C4D6BE603`
para o envelope; o dataset permaneceu no hash congelado anterior. Reserva
não executada.

**Revisão de diagnóstico:** a seção anterior chamou o bloqueio de `IRR-01`
de “falso bloqueio” contra o gabarito provisório. Isso descreve a discordância
com o rótulo sintético, **não** um erro do portão comprovado: o exemplo omite
literalmente “do solo”. Talvez o contexto de irrigação resolva a referência
para uma pessoa, mas o teste pareado não certifica essa inferência. O gabarito
foi mantido congelado por rastreabilidade; não foi reescrito para tornar a
métrica favorável. A primeira fronteira RED passa a ser a resolução
**auditável da referência implícita** (ou revisão humana do gabarito), antes
de papéis, implicação da frase completa e runtime real. Nenhuma alteração de
produção foi feita.

## Painel cego de referências implícitas (24/09)

Foi congelado um novo painel **sem gabarito** em
`scripts/analises/dados/revisao_referencias_ensino_v1.jsonl`, SHA-256
`CB840DBFBD8C5A1B5AF0CE02853FA0A2E56D1052AFE567BE6C33809093ECF2E5`.
São dez cenários sintéticos curtos, não páginas reais nem revisão humana:
qualificador explícito, omitido e divergente; número de desconto; sensor
único versus dois sensores; sensor do ar; leitura negada; temperatura da água
com e sem qualificador. A definição, o exemplo e eventuais frases de contexto
estão presentes, mas **não há rótulo esperado** no arquivo. A antiga reserva
de programação/culinária continua fechada.

`scripts/analises/revisao_referencias_ensino.py` lê o painel apenas se o hash
corresponder, não aceita gabarito embutido e oferece dois modos: a execução
normal imprime os casos cegos; `--diagnostico` mostra o estado da heurística
atual e não deve ser mostrado ao avaliador antes da revisão. Uma futura
revisão precisa marcar separadamente (a) se a leitura se refere à mesma
grandeza, outra ou é indeterminada, e (b) se a leitura é afirmada, negada ou
indeterminada; deve citar trecho literal e justificar. A validação desse
formato **não** autentica o revisor, não certifica o rótulo e nunca transforma
o painel em dados de treino ou em fala aprovada.

O diagnóstico local já mostra um limite concreto: `REF-01` sem contexto,
`REF-05` com um único sensor de solo e `REF-06` com sensores de solo e ar
recebem igualmente `qualificador_ausente`. Também `REF-07`, com “sensor do
ar” antes do número, permanece nesse estado porque o parser experimental
só extrai rótulos após o valor. Esses resultados **não** estabelecem o
gabarito dos casos; apontam a primeira fronteira a avaliar: identidade do
sensor/referente e escopo do contexto, sem converter contexto em autorização
ou em prova do efeito. A revisão humana de `REF-01` foi solicitada e ainda
não foi incorporada a métricas. Nenhuma produção foi alterada.

## Vínculo contextual proposto: unicidade não é cobertura (24/09)

O serviço compartilhado `mente_laylay/cognicao/seletor_contexto.py` pontua
relevância conversacional, mas não emite um recibo que vincule “o sensor” a
uma grandeza específica. Por isso, a sonda isolada
`scripts/analises/sonda_contexto_referente_ensino.py` pede ao Qwen uma
proposta com expressão do exemplo, grandeza e trecho literal do contexto.
Ela não executa nem aprova respostas da Laylay.

Na primeira rodada, `REF-05` (somente sensor de solo) e `REF-06` (sensores de
solo e ar) receberam a mesma proposta única para o solo. Isso falsificou a
premissa de que unicidade da proposta prova ausência de concorrentes no
contexto. O conferidor passou a procurar grandezas concorrentes explícitas
com o mesmo núcleo; na segunda rodada, `REF-05` ficou apenas como candidato
pendente, enquanto `REF-06` foi bloqueado por concorrência, mesmo com a
omissão do modelo. `REF-07` preservou a diferença entre sensor do ar e
definição sobre o solo. Em `REF-09`, o modelo copiou um trecho do exemplo
como se fosse do contexto; a verificação literal rejeitou a origem falsa.

O painel segue no SHA-256 congelado
`CB840DBFBD8C5A1B5AF0CE02853FA0A2E56D1052AFE567BE6C33809093ECF2E5`;
a sonda da segunda rodada estava no SHA-256
`D5C1ED02DBB581B95A9AE836133C319C4D32E9C0B5CB37DB36DFDC9300C56405`.
Ainda não há rótulos humanos nem escore de acerto semântico. A detecção de
concorrência é estreita (qualificadores textuais explícitos), não prova
cobertura completa. Todos os caminhos mantêm `aprovado_para_compor=False`:
vínculo contextual não confirma que uma leitura ocorreu, nem autoriza
efeito. Próxima fronteira: revisão independente do painel e, só depois,
considerar integração com o dono compartilhado do contexto e prova no
runtime real. Nenhuma produção foi alterada.

## Unicidade do medidor e revisão parcial (24/09)

Um controle novo falsificou a hipótese de que verificar apenas grandezas
concorrentes bastava: com um sensor de umidade do solo e outro de temperatura
do ar, a proposta do Qwen para solo ainda parecia “candidata única”. O
primeiro RED foi em `conferir_vinculos`, não na resposta final nem no
seletor de contexto. A sonda agora exige **declaração positiva textual** de
unicidade do medidor para usar o estado de candidato pendente. O silêncio
sobre outros medidores, uma declaração negada e uma contradição explícita
permanecem indeterminados. Isso é uma guarda estreita para experimento, não
um parser geral nem comprovação de completude do contexto.

A primeira rodada Qwen após essa guarda revelou um falso bloqueio em
`REF-05`: a expressão proposta incluía a ação e o valor (“o sensor leu 15%
de umidade”), enquanto o conferidor procurava unicidade da última palavra.
Um RED específico mostrou o desvio; a extração passou a usar o primeiro
grupo nominal da expressão. Na repetição real, `REF-05` voltou a candidato
pendente, `REF-06` continuou bloqueado por concorrência, `REF-07` por
grandeza divergente e `REF-09` por citação contextual sem origem. Os demais
casos não tiveram vínculo proposto. Um controle vizinho revelou ainda que
“sensor do ar” dentro do trecho proposto podia ser ignorado e receber o
estado de candidato para “solo”. A qualificação explícita agora prevalece
tanto dentro quanto após o trecho; uma qualificação compatível continua
permitida. A repetição Qwen manteve os estados acima. A sonda atual tem
SHA-256 `D91CED9453C78C8DF944751DB53786D28604882F06FDF57D06E1C374BAF9B476`;
o painel permaneceu no hash congelado. Os 54 testes focados passaram.

Pedro revisou apenas a pergunta de **referente** de `REF-01`: sem contexto,
“o sensor leu 15% de umidade” fica **indeterminado**, não comprovadamente
“umidade do solo”. Não foi colhido rótulo da leitura nem dos nove casos
restantes. Portanto, não há revisão completa, escore semântico, autorização
para treino, aprovação de aula ou validação no runtime. Produção não foi
alterada. Próxima fronteira: revisão independente restante e definição de
um inventário contextual com origem, escopo e cardinalidade pelo owner
compartilhado, em vez de inferir completude de texto livre.

## Contrato compartilhado de inventário contextual (24/09)

A primeira fronteira arquitetural ficou explícita: o
`seletor_contexto_turno` retorna trechos **relevantes** (com limite e corte de
conteúdo), não uma enumeração completa de entidades. Um teste com o seletor
real confirma que até um trecho selecionado sobre sensor não pode ser
promovido automaticamente a inventário tipado. A hipótese concorrente de
que bastaria ausência de segunda **grandeza** já fora falsificada: outro
sensor pode medir algo diferente e ainda disputar “o sensor”.

Foi adicionado `mente_laylay/cognicao/contrato_inventario_contextual.py`,
sem chamadas na composição de produção. O snapshot tipado separa origem,
escopo, instante, TTL, método de cobertura e itens identificados. O
avaliador usa cardinalidade por **tipo de medidor**, antes de comparar a
grandeza: dois sensores são concorrentes mesmo se um mede umidade e o outro
temperatura. Inventário parcial, expirado, com origem/escopo misturado ou
IDs repetidos não produz candidato. Mesmo um inventário declarado completo
falha por padrão se sua origem não estiver registrada pelo chamador como
enumeradora. `cadastro_sensores` nos testes é uma fonte **sintética**; não
foi registrada no runtime da Laylay. Um único item compatível resulta
somente em `candidato_unico_pendente`, sempre com
`referente_resolvido=False`, `aprovado_para_compor=False` e
`autoriza_efeito=False`. Declarar cobertura não é prová-la: o contrato não
verifica a enumeração na fonte.

O RED de fonte não registrada demonstrou que a primeira versão aceitaria
uma autodeclaração de completude. A guarda de registro corrigiu essa
fronteira. Outro RED mostrou que uma origem malformada gerava exceção, e
agora falha fechada. O grupo de 79 testes focados e regressivos de contexto
passou; não houve prova no runtime real nem alteração de fluxo de fala.

Ao ser consultado sobre `REF-06`, Pedro observou que a resposta depende
do assunto anterior e das informações que levaram à frase. Isso **não é**
um rótulo formal de “solo”, “ar” ou “indeterminado”: o painel contém apenas
o inventário de dois sensores, sem antecedente discursivo. A próxima
fronteira é um vínculo de foco/continuidade com origem, escopo e validade,
produzido pelo owner canônico da referência. Ele pode selecionar um
candidato entre itens existentes, mas não criar autorização operacional,
confirmar medição ou aprovar ensino. Ainda falta revisão independente dos
casos e teste da composição real antes de cogitar ativação.

## Triagem cruzada cega não substitui revisão humana (24/09)

`scripts/analises/sonda_revisao_cruzada_referencias_ensino.py` envia ao
`gemma4:26b` somente definição, exemplo e contexto dos dez casos
congelados, sem diagnósticos ou propostas do Qwen. A primeira tentativa
teve timeout e JSON vazio/inválido; `ollama show` revelou que o modo de
raciocínio desse modelo é ligado por padrão. Com `think=False`, o painel
completo terminou. A sonda agora interrompe no primeiro erro para não
repetir dez timeouts. SHA-256 do script:
`128C10E3943A2600530209180659D76D84175D3FF827A64A8DB0432533E83F85`.

| Caso | Gemma: referente / leitura | Observação |
| --- | --- | --- |
| REF-01 | mesmo / afirmada | Discorda da revisão parcial de Pedro: referente sem contexto indeterminado. |
| REF-02 | mesmo / afirmada | Grandeza explícita no exemplo. |
| REF-03 | outro / afirmada | Grandeza explícita diferente. |
| REF-04 | outro / indeterminada | Exemplo fala de desconto, não de leitura. |
| REF-05 | mesmo / afirmada | Contexto sintético declara sensor único. |
| REF-06 | mesmo / afirmada | Escolheu sem antecedente entre dois sensores; Pedro pediu mais contexto. |
| REF-07 | outro / afirmada | O exemplo nomeia o sensor do ar. |
| REF-08 | outro / negada | Separou a negação, mas o rótulo “outro” conflita com “umidade do solo” literal. |
| REF-09 | mesmo / afirmada | Contexto sintético declara termômetro único. |
| REF-10 | mesmo / afirmada | Grandeza explícita no exemplo. |

`validar_revisao` aceitou **o formato** das dez saídas, não sua correção
semântica. REF-01 e REF-06 mostram que o segundo modelo também tende a
preencher referência ausente; REF-08 sugere confusão entre identidade da
grandeza e negação da leitura. Não há gabarito completo, escore nem revisão
humana substituída por IA. O contrato de inventário tem SHA-256
`409B48988D16BD41105E89EB9EDF458425AA6DD417D046B24CB7C622BBEE2D75`;
somente testes registram a fonte fictícia `cadastro_sensores`. Os 83 testes
focados, incluindo o seletor de contexto real, passaram. A produção segue
sem ligação a esses experimentos e sem alteração do caminho de fala.

Próxima fronteira arquitetural: localizar um antecedente conversacional
**tipado e vigente** no resolver canônico, com identidade que exista no
inventário e escopo coincidente. Sem esse vínculo, a presença de dois
sensores continua ambígua. Mesmo com ele, seleção de referente não é
autorização de ação nem prova de medição.

## Primeira fronteira RED do antecedente canônico (24/09)

Ao tentar ligar o inventário ao retrato real, a ordem causal mudou. Em
`construir_retrato_turno`, “estamos falando do sensor de umidade do solo”
não registra automaticamente uma entidade e “o sensor leu…” no turno
seguinte não recebe `referencia_resolvida`. Esse caminho continua **aberto**;
texto genérico não vira ID por uma heurística local do ensino. Como controle,
um sensor previamente registrado em `registro_semantico` é resolvido para
“esse sensor” com `entidade_id`, mas o retrato não leva o escopo da fonte.

O RED mais perigoso apareceu antes da ponte: com o sensor de solo ativo,
“esse sensor **do ar**” era resolvido como solo; com dois sensores, o foco
antigo podia vencer o qualificador atual. O owner do ranking,
`resolver_referencia_pontuada`, agora recebe do leitor compartilhado de
referências o tipo e o qualificador nominais da fala atual. Candidato cujo
tipo/nome não contém essa qualificação não é elegível, mesmo se for o foco
mais recente. “Esse sensor” e “esse sensor do solo” continuam funcionando.
Um controle com duas playlists confirma que a regra não é uma exceção de
sensor. `construir_retrato_turno` não foi editado nesta correção.

Só após esse GREEN foi adicionada ao contrato de inventário a projeção
`antecedente_do_retrato`. Ela exige simultaneamente: ID entregue pelo
resolvedor canônico, entidade existente no registro, fonte registrada pela
enumeração sintética, ID de item existente no inventário, mesmo escopo,
tipo/nome coerentes, timestamps válidos e vencedor com margem sobre outros
candidatos. O resultado é `candidato_focal_pendente`, nunca
`referente_resolvido`, fala aprovada, autorização ou medição confirmada.
Fonte de usuário, ID ausente, qualificador conflitante, inventário parcial,
origem não registrada, dados vencidos e pontuação malformada falham fechados.
Não há chamada dessa projeção na composição de produção nem fonte real
registrada como enumeradora.

Evidência: 150 testes de contrato, referência e contexto passaram; outro
grupo de 236 testes da mente/comunicação passou (mais oito subtestes).
São GREENs de código e composição com componentes reais, **não** validação
da fala final no runtime nem escore de ensino. Próxima fronteira: decidir
se e como o owner canônico pode registrar uma menção explícita a sensor e
resolver com segurança “o sensor” quando houver antecedente inequívoco.
Até lá, essa forma deve permanecer indeterminada.

### Controles de qualificadores e limite atual da ponte

Uma regressão de vizinhança mostrou que exigir todas as palavras descritivas
no **título** era forte demais: “esse jogo de corrida” não podia mais
continuar um jogo ativo chamado “Forza Horizon”. O contrato canônico agora
usa o qualificador como veto apenas quando o nome registrado já contém
uma descrição nominal comparável (`sensor de umidade do solo` versus
`sensor de umidade do ar`). Um nome sem tal atributo não é rejeitado por
ausência de palavra; isso preserva conversa natural, **não** prova que a
descrição do usuário seja verdadeira. Uma cadeia como “sensor de umidade
do ar” deve ser considerada inteira, não só “umidade”. O mesmo controle
foi exercitado com playlists nominalmente qualificadas.

Na ponte experimental, o nível de exigência é maior: mesmo que o resolvedor
canônico conserve um nome genérico como “Sensor A”, a projeção compara o
qualificador dito agora com a **grandeza tipada do item** do inventário.
“Esse sensor do ar” não pode produzir antecedente para um ID de umidade do
solo só porque o título genérico não traz “solo”. O RED reproduziu essa
promoção indevida; o conferidor de inventário agora retorna `None`.

Os 390 testes relevantes de referência, inventário, mente e comunicação
passaram (mais oito subtestes). Não foi executado o processo inteiro da
Laylay nem alterada a geração de fala. O texto “o sensor leu…” ainda não
obtém automaticamente um ID canônico mesmo depois de menção anterior;
portanto a proposta original de ensino permanece bloqueada nesse caminho.
Antes de liberar uso real, é necessário demonstrar a captura de uma menção
explícita, sua identidade/escopo no registro compartilhado e a validação
da resposta final entregue, sem usar uma classificação sintética como
prova de qualidade da aula.

### Nome definido no exemplo: candidato, não prova (24/09)

O contrato experimental `avaliar_referencia_nominal_contextual` agora lê
“o sensor” apenas para vincular o texto a um **candidato** de inventário
enumerado. Com dois sensores e sem antecedente tipado, devolve
`referentes_concorrentes`; com antecedente válido, devolve
`candidato_focal_pendente`; com um único item em enumeração completa,
`candidato_unico_pendente`. Menção ausente ou múltipla, foco vencido,
inventário parcial e qualificador contraditório não podem herdar o foco.
Em todos esses casos, `referente_resolvido`, `aprovado_para_compor` e
`autoriza_efeito` permanecem falsos: nem identidade candidata prova que
houve medição de 15%, nem a narrativa autoriza ligar uma bomba.

O teste de dois turnos com “Estamos falando do sensor de umidade do solo”
seguido de “O sensor leu 15% de umidade” documenta a primeira fronteira
que ainda falta: o retrato/registro de produção não recebe um ID da fonte
para essa menção textual. Não inferir o ID a partir da frase nem do último
item enumerado; uma fonte real deve publicar identidade e escopo, e o
owner conversacional deve registrar **foco explícito** separadamente da
enumeração. A ponte continua inerte, sem alteração na fala de produção.

### Menção explícita com fonte tipada e continuidade em memória (24/09)

O RED seguinte mostrou que um antecedente da fonte A atravessava para a
fonte B se ambas reutilizassem `solo_1` no mesmo escopo. O antecedente agora
carrega `origem_inventario`, exigida na revalidação. Isso protege a identidade
composta `(origem, escopo, identificador)`, não apenas o ID textual.

`antecedente_de_mencao_explicita` projeta um foco apenas quando um retrato
conversacional diz integralmente uma construção explícita como “Estamos
falando do sensor de umidade do solo” e a descrição corresponde a **um único
item** de inventário completo, vigente e de fonte registrada. A mesma regra
foi testada com playlists; menção vaga, descrição duplicada, fonte não
registrada, inventário parcial e texto incidental não criam foco. O retorno
é um candidato, não um fato sobre medições.

O registro semântico agora possui armazenamento separado de
`entidade_ativa_id` para esse candidato. `guardar_candidato_foco_contextual`
preserva o foco entre turnos; `antecedente_do_foco_guardado` o revalida contra
o inventário atual, TTL, origem e escopo. `atualizar_foco_contextual_inventariado`
preserva o foco em turnos independentes e cancela uma nova indicação de foco
que não identifica um item único. Renovar a sessão também limpa o foco.
Um teste percorreu `construir_retrato_turno` → foco explícito → registro
compartilhado → turno seguinte → nome definido “o sensor”, sem aprovar fala ou
efeito. **Ainda não há produtor registrado nem chamada desse caminho no
orquestrador de produção.** Os inventários dos testes são sintéticos. A
próxima fronteira é integrar um produtor adequado (cenário didático declarado
ou inventário operacional real, com contratos distintos) e provar no runtime
que a resposta final não atribui uma leitura ao referente errado.

### Produtor de cenário do usuário em sombra e primeira prova real (24/09)

Foi integrado um produtor **restrito a premissas hipotéticas explícitas do
usuário** em `inventario_cenario_didatico.py`. “Um único” e “exatamente dois”
podem declarar enumeração completa no escopo do cenário; listar dois itens
sem totalidade explícita continua parcial. A origem é `cenario_usuario`, não
um cadastro de sensores físicos. O orquestrador observa essa fonte e conserva
o foco tipado entre turnos, mas `referente_resolvido`,
`aprovado_para_compor` e `autoriza_efeito` continuam falsos. O inventário
não entra no prompt nem substitui a decisão ou o executor.

Dois REDs de composição foram reproduzidos antes da correção: a origem
`roteiro_teste` era normalizada fora da lista de entradas pessoais, impedindo
o produtor de receber a fala do roteiro; e a renovação de sessão deixava o
cenário hipotético no estado transitório. A primeira foi limitada à origem
bruta do roteiro, sem ampliar autorização operacional; a segunda limpa os
dois campos de cenário ao renovar a sessão. Outro RED mostrou que um campo
numérico no inventário serializado passava na reidratação; agora a fonte
malformada é descartada. Os 231 testes relevantes passaram antes desta
última guarda, e seus 15 testes específicos passaram depois dela. Na
regressão repetida, 229 passaram e três testes que importam `laylay.py`
pararam na proteção de instância única: outra sessão da Laylay foi aberta
no VS Code durante a execução. Esses três precisam ser repetidos com a
sessão livre; não são evidência de falha no contrato didático.

A sonda real de quatro turnos com Qwen em
`resultados_testes/roteiro_ensino_cenario_sensor_sombra-20260924-123054-056747`
confirmou, nos logs, inventário completo, foco explícito preservado e
`candidato_focal_pendente` em “O sensor leu 15% de umidade”. Nenhum comando
foi executado. O roteiro marcou 4/4 **somente nas expectativas de transporte
e ausência de comando**. Isso não mede correção do ensino. O HTTP bruto já
continha “o solo tá comendo” no segundo turno e, no quarto, a resposta não
expôs a comparação `15 < 20`; ela atribuiu risco à planta sem premissa
correspondente. O verificador final não reparou essas falhas e a fala entregue
as preservou. Assim, o produtor/contexto funcionou em sombra, mas a
**composição didática final ainda não está aprovada**.

Próxima fronteira: separar explicitamente, no contrato de ensino, a leitura
declarada (`15%`), o limiar condicional (`abaixo de 20%`), a consequência
autorizada pela regra hipotética (`bomba liga`) e qualquer explicação causal
adicional não demonstrada. Exigir prova no texto final, não apenas no
classificador ou no verificador. Não promover o candidato de referente a
fato físico, nem conectar este cenário de teste a IoT real.

### P01: premissas no prompt não bastam para certificar a aula (24/09)

Os três testes antes bloqueados pela instância única passaram quando a
sessoão ficou livre (`test_explicacao_didatica_preservada.py`: 39/39).
No payload da sonda acima, a leitura de 15% e a regra de 20% chegaram ao
Qwen, mas o roteiro **compacto** continha somente instruções genéricas de
exemplo. Três REDs em ensino de sensor, programação e floricultura
provaram que faltava a sequência de premissas → relação → conclusão. O
owner `geracao_concreta.py` agora a inclui apenas em
`explicacao_didatica`, exigindo comparação explícita quando houver valores
compatíveis e vedando causas extras e a fala anterior da assistente como
fonte. O pedido atual, não um referente incidental, ancora esse roteiro.

A sonda real seguinte (`roteiro_ensino_cenario_sensor_sombra-20260924-123956-818763`)
recuperou os 15% na resposta final, mas ainda inventou necessidade de água
das plantas. Duas fronteiras de transporte do **mesmo problema de proveniência**
foram então reproduzidas em RED: falas anteriores da assistente voltavam
como mensagens de histórico e dentro de `Evite repetir: ...` no contrato.
O prompt de `explicacao_didatica` agora omite ambas, preservando as mensagens
do usuário e o histórico armazenado; outras estratégias mantêm seu fluxo.
Nenhuma delas foi promovida a evidência factual.

Na sonda após filtrar o histórico, mas **antes** de retirar o texto de
`Evite repetir`, o mesmo problema persistiu; o campo de estilo ainda
copiava a fala errada (`roteiro_ensino_cenario_sensor_sombra-20260924-124307-246827`).
A sonda após retirar ambos (`roteiro_ensino_cenario_sensor_sombra-20260924-124538-011364`)
teve prompt com mensagens do usuário e sem respostas antigas da assistente.
Mesmo assim, a geração HTTP e a fala final afirmaram que a bomba “garante”
umidade e que o solo precisa de água para um “equilíbrio” não definido.
Logo a contaminação por fala anterior foi corrigida, mas **P01/alegações
didáticas continua RED**; não atribuir toda a falha ao histórico.

O roteiro manual agora marca termos historicamente inventados como proibidos.
Isso deve tornar esses casos RED em vez de exibir 4/4 enganoso, mas uma
allowlist/denylist de palavras não prova a correção semântica de qualquer
nova explicação. Os 236 regressivos relevantes passaram. Próximo contrato:
compor alegacões didáticas atômicas com fonte e papel (`premissa do usuário`,
`regra hipotética`, `comparação verificável`, `conclusão derivada`,
`fato externo`); o verificador precisa sinalizar a afirmação adicional
sem cortar uma explicação correta nem gerar um fallback. Os contratos offline
de requisitos e vínculo existentes são insumo, não certificados de verdade.
Uma sonda real multidomínio e revisão de fala integral ainda são necessárias
antes de alterar a permissão de composição do inventário sombra.

Achado **separado**: no turno final, o resolvedor escolheu sucessivamente
`Comando para Laylay`, `blender.exe` e uma aba do Opera como referente de
“essa leitura”, embora a tarefa fosse de sensor. Não houve execução, e
isso não explica sozinho o RED factual; investigar o ranking/escopo da
referência como outra raiz, sem acrescentar exceção de sensor neste patch.

### P01: auditoria de alegações em sombra (24/09)

O owner do verificador passou a registrar
`auditoria_alegacoes_didaticas_sombra` só para `explicacao_didatica` e
`reensino_didatico` sem comandos. O registro usa apenas a fala **candidata após
verificação** e fontes candidatas de turnos do usuário da sessão corrente;
fala anterior da Laylay e mensagens de sistema não se tornam fontes. A
observação divide o texto em segmentos com cobertura de caracteres, aponta
repetições literais e confere somente comparações aritméticas pequenas quando
os números e unidades aparecem nas fontes. Não certifica vínculo de entidade,
condicional, causalidade, verdade externa nem cobertura semântica. Mesmo uma
citação literal permanece `revisao_pendente`; nenhuma classificação aprova
composição, veta fala, dispara fallback ou autoriza efeito. Há limpeza a cada
novo turno e na renovação de sessão.

O teste de regressão com a fala real do sensor preserva a comparação `15% <
20%` e expõe separadamente as caudas “garante” e “equilíbrio” sem fonte
literal. Controles em programação, engenharia e floricultura, valor errado,
unidade diferente, negação e histórico da assistente passaram. A seleção
focada com contratos vizinhos terminou em **145 passed**. Isto é GREEN local e
de integração do observador, **não GREEN factual do ensino**. A auditoria
ainda não prova que a fala candidata chegou ao usuário e não substitui revisão
de alegações atômicas. A sonda no Qwen do runtime real ficou pendente porque a
Laylay voltou a abrir durante a validação; não interromper a sessão do Pedro.

### Sonda real da auditoria (24/09, 19:06)

Com a instância livre, o roteiro de quatro turnos foi executado em
`resultados_testes/roteiro_ensino_cenario_sensor_sombra-20260924-190608-739393`
e o transporte local foi capturado em
`resultados_testes/transporte_evidencia-20260924-190606-912934`. Modelo real:
`qwen3:4b-instruct`; IoT simulado e voz desativada. A primeira chamada sofreu
timeout e produziu contingência; o último turno recebeu HTTP 200. O payload
final continha o cenário dos dois sensores, o foco em umidade do solo, 15%,
20% e instruções para não inventar. Portanto, falta de transporte dessas
premissas não explica a falha final. A saída HTTP já dizia que o solo estava
“seca demais para manter a vegetação saudável” e que o sistema manteria o
“equilíbrio de umidade”; a fala entregue preservou exatamente esse texto.
Não há indicação de que o verificador tenha introduzido tais alegações. Uma
proposta de comando vazia foi descartada pela autorização, sem execução.

O relatório determinístico marcou 2 aprovações, 1 falha no último turno pelo
termo histórico “equilíbrio” e 1 alerta de latência. Essa regra lexical só
detecta a ocorrência conhecida, não garante qualidade de ensino. A auditoria
em sombra registrou oito segmentos, oito sem âncora **literal** e zero
comparações aritméticas: o Qwen disse “15% abaixo do limiar”, sem repetir
“20%” nessa relação. O número 20% apareceu em outra oração, mas resolver
“limiar” e o mesmo sensor exige vínculo semântico e escopo, não a aritmética
local. Ausência de literal não significa falsidade de cada paráfrase. P01
permanece RED na geração; o próximo contrato deve representar alegações,
condições, referentes, fontes e derivação separadamente, sem promover a sonda
lexical ou o mesmo Qwen a árbitro de verdade.

### Primeiro contrato formal de alegações, ainda offline (24/09)

`scripts/analises/contrato_alegacoes_didaticas.py` agora confere propostas
separadas da lista de fontes registrada pelo chamador. Cada intervalo deve
cobrir o texto final sem saltos nem sobreposição; cada citação precisa existir
literalmente em uma fonte de origem permitida. Citação forjada, fonte
desconhecida, fala da assistente como fonte e cauda sem fonte ficam explícitas.
Papéis como premissa, regra, comparação, conclusão e fato externo são **apenas
propostas**: nem a atomicidade do intervalo, nem condição, entidade ou
implicação são aprovadas por essa conferência. A fonte tipada
`pesquisa_verificada` só pode ser fornecida pelo chamador confiável, nunca
autoatribuída pelo modelo; mesmo ela não certifica a alegação. Não há ligação
com publicação, veto, fallback ou executor. Esta é uma estrutura de
falsificação para um próximo produtor de alegações, não um verificador de
verdade pronto.

Os oito testes novos do contrato, os regressivos da auditoria/contratos
vizinhos e a composição didática real passaram juntos (**192 passed**).
Ainda falta demonstrar, em casos
multidomínio revisados independentemente, que um produtor consiga decompor
frases mistas sem omissões e que a revisão de vínculos recuse causas extras
sem cortar paráfrases corretas. Somente após isso considerar influência na
fala final. P01 permanece aberto.

### Proponente de vínculos na fala final — piloto RED (24/09)

`scripts/analises/sonda_propostas_alegacoes_fala.py` usa os segmentos da
auditoria como índices fixos: o Qwen só propõe papel e citação por índice; não
pode escolher a cobertura nem registrar novas fontes. O contrato anterior
confere cada citação literalmente. Reutiliza-se ainda
`extrair_contas_explicitas` para recibos aritméticos independentes: `12
dividido por 3 = 4` é conferível, mas “cada pessoa recebe 4” mantém o
mapeamento de papéis pendente. Nenhum desses recibos aprova a fala inteira.

Foram testados, sem alterar o runtime, o último discurso real do sensor e
quatro controles sintéticos de matemática, floricultura, programação e cópia
literal. Modelo: `qwen3:4b-instruct`, temperatura zero, JSON Schema. O
resultado não sustenta promoção:

| Caso | Primeira falha da proposta |
| --- | --- |
| Sensor real | Cinco segmentos sem fonte; uma citação inventada (“detecta” no lugar de “leu”); duas citações localizadas mas sem prova de implicação. |
| Divisão correta | A conta é validável por código, mas o modelo citou como fonte uma equação que só existia na fala; a conclusão sobre pessoas segue pendente. |
| Floricultura | Citou literalmente a fonte condicional para “begônias são anuais” sem preservar “em climas frios”; depois enviou citação vazia como evidência. |
| Programação | Citou a regra `True se x > 0` para “sempre retorna True”; depois enviou citação vazia. |
| Cópia literal positiva | Rotulou uma afirmação condicional como `nao_factual`, sem citar a fonte disponível. |

O validador agora destaca `papeis_semanticos_pendentes` quando o modelo usa
`nao_factual`; não converte esse rótulo em permissão. O piloto repete a
fronteira já vista na extração definição–exemplo: proveniência literal e
JSON válido não conferem relação, condição nem papel. Ajustar prompt ou
aceitar citação vazia nesses mesmos cinco casos seria otimização sobre dados
consumidos, não prova de generalização. Próxima via: fatos/regras tipados
**antes** da redação, com operador, referentes e condições verificáveis por
serviço independente; composição limitada a esse grafo e avaliação humana
multidomínio em casos novos. O proponente atual continua somente diagnóstico
offline. Seleção de 199 regressivos relacionados passou; P01 segue RED.

### Grafo de premissas anterior à redação — primeiro contrato offline (24/09)

`scripts/analises/grafo_premissas_didaticas.py` reutiliza a identidade
`ReferenteContextual` e registra fonte, escopo, premissas, condições e efeito
de cada regra *antes* da fala. Confere existência da fonte, citação literal,
identidades, escopo e valor textual/numérico citado; rejeita fonte da própria
assistente, valor inventado e referente ausente. Uma fonte marcada
`pesquisa_verificada` ainda precisa ser registrada por um chamador confiável:
o rótulo recebido do modelo sozinho não confere autoridade.

O teste com sensor, programação e floricultura mostra as condições separadas
de fatos observados. Um controle adversarial associa a leitura de 15% ao
sensor de ar apesar da citação dizer sensor de solo: a estrutura literal pode
passar, mas `anotacao_semantica_revisada`, `condicoes_satisfeitas`,
`consequencias_observadas`, `aprovado_para_compor` e `autoriza_efeito`
continuam falsos. Isto demonstra o limite, não a correção do ensino. Nove
testes do grafo e 49 regressivos relacionados passaram; nenhum produtor
automático ou elo com publicação/runtime foi acrescentado. Próxima fronteira:
revisar independentemente o vínculo referente–atributo, a direção das
relações e as condições em casos multidomínio inéditos. P01 permanece RED.

### Auditoria conservadora dos vínculos explícitos (24/09, continuação)

`auditar_vinculos_literais` só opera após a conferência do grafo. Compara a
âncora literal do referente com a premissa/condição/efeito e confronta sinais
numéricos explícitos (`<`, `>`, “abaixo de”, “acima de”) com o operador
proposto. A leitura do sensor de ar com citação do sensor de solo recebe
`referente_sem_ancora_literal`; inverter `abaixo de 20%` para `> 20%` recebe
`direcao_literal_divergente`. Uma negação na condição deixa a direção
indeterminada, inclusive em “não cair abaixo de 20%”. Os controles também
incluem programação (`x > 0`) e floricultura condicional. Seleção relacionada:
**69 passed**.

Essas comparações não são prova da verdade do vínculo: uma paráfrase legítima
pode não compartilhar palavras, e uma anotação maliciosa poderia repetir a
âncora correta com o papel errado. Portanto o resultado continua
`pistas_literais_revisao_pendente`, com composição, satisfação de condições,
observação de efeitos e autorização falsas. Próximo experimento: gabaritos
independentes de fonte/referente/relação/condição em cenários novos para medir
os falsos positivos e falsos negativos; depois produtor automático em sombra.
Nenhuma fala do runtime foi modificada. P01 permanece aberto.

### Gabarito local separado e limites medidos (24/09)

`scripts/analises/dados/gabarito_grafo_didatico_v1.json` mantém rótulos
manuais fora do auditor literal. Quatro cenários novos confrontam a auditoria
em refrigeração, logística, ambiente e programação. O confronto
`scripts/analises/avaliar_grafo_premissas.py` exige cobertura de todos os
slots observáveis e falha fechado se o grafo ou o gabarito forem inválidos.
O gabarito é **revisão manual local**, não revisão externa autenticada nem
verdade certificada por um segundo serviço.

Resultado diagnóstico: o cenário explícito da câmara teve quatro pistas
compatíveis; o das caixas revelou um **falso positivo lexical** — `8 kg`
pertence à caixa azul, mas a citação inteira também contém “caixa vermelha”.
O medidor do quarto mostrou uma **abstenção em vínculo correto**: a segunda
frase usa “equipamento”, identificado na primeira. No cache, duas pistas
locais são compatíveis e a direção textual gera uma abstenção, mas a condição
de validade do registro foi omitida;
o auditor **não mede completude de condições**. Assim, nenhum placar local
aprova composição, efeito ou ensino real.

Ao montar o conjunto, apareceu um RED mais cedo: `8 kg`/`15 %` com espaço
entre número e unidade era rejeitado pela conferência estrutural. O contrato
agora aceita espaço sem deixar `20` casar com `120`. Teste focal RED→GREEN;
seleção relacionada **78 passed**. Nada entrou no runtime. O produtor
automático em sombra só será interpretável junto de uma revisão independente
do vínculo entre entidade e valor e da completude das condições; um modelo
que apenas reproduza pistas literais herdará os falsos positivos acima.
P01 permanece aberto.

### Cobertura de condições anotadas separadamente (24/09, continuação)

`confrontar_condicoes_revisadas` compara a proposta com regras de referência
anotadas fora dela, depois de validar ambas contra as fontes/escopo do grafo.
Compara multiplicidade de condições sem depender da ordem: no cache, a
validade do registro omitida agora aparece como `condicao_omitida`; no
cenário de sensor, a falta do modo automático também; em cultivo, a falta de
sombra parcial. Condição duplicada é `condicao_extra`, citação inventada da
referência é recusada, e efeito/fonte divergente interrompe a comparação.
O placar diagnóstico do cache registra a omissão sem aprovar a fala.

O resultado `slots_condicoes_alinhados_revisao_pendente` não prova que os
slots extraídos representam corretamente a fonte. A estrutura atual não
expressa nem confere o conectivo entre condições (`e` versus `ou`), não
autentica a independência da revisão e não observa se uma condição se
realizou. Logo, completude só pode ser medida **relativamente a uma
referência revisada**; ela não é descoberta automaticamente pela função.
REDs canônicos antes do candidato; seleção de **86 testes relacionados
passou**. Sem ligação com publicação, comando ou produção. Próxima fronteira:
representar/revisar relações e conectivos de modo independente, depois medir
um produtor automático somente em sombra. P01 continua aberto.

### Relação lógica de regras, separada da lista de condições (24/09)

`RegraDidatica` agora pode representar o conectivo plano das condições
(`unico`, `e`, `ou`, ou `indeterminado`) e a direção da implicação
(`condicoes_suficientes`, `condicoes_necessarias`, `equivalencia`, ou
`indeterminado`). O valor padrão segue indeterminado: regras históricas não
ganham significado por compatibilidade. Conectivo fora do vocabulário e
`unico` aplicado a duas condições falham na validação estrutural.

Com as mesmas condições e o mesmo efeito, os REDs mostraram que a comparação
anterior não distinguia `e` de `ou`, nem `se` de `somente quando`. O confronto
agora expõe `conectivo_divergente`, `implicacao_divergente` e os estados
pendentes quando a proposta não declara a relação. Casos de cache,
irrigação e programação cobrem conjunção, disjunção, necessidade,
suficiência e bicondicional. O placar distingue completude dos slots de
correção relacional: condições completas com conectivo errado não viram
`condicao_omitida`.

As quatro regras revisadas do gabarito local foram movidas para
`gabarito_grafo_didatico_v1.json`, fora dos candidatos; o comparador valida
citações e escopo antes de usá-las. Isso permite medir propostas futuras em
sombra sem copiar os valores esperados do teste. **94 testes relacionados
passaram.** A revisão é manual local, não autenticada como independente;
igualdade com ela continua `revisao_pendente`, sem compor fala ou autorizar
efeito. Regras com conectivos mistos ou aninhados ainda não têm expressão
segura nessa estrutura e devem permanecer indeterminadas. P01 segue aberto.

### Primeira sonda do produtor Qwen em sombra (24/09)

Seis fontes inéditas, de pintura, login, alarme, bicondicional, irrigação e
conectivo misto, foram congeladas antes da chamada ao Qwen3:4b-instruct.
O modelo recebeu apenas fonte, referentes e efeito fixo; o gabarito manual
local ficou separado. A sonda apenas imprime a proposta e o confronto, sem
persistir treinamento, acionar executor ou publicar fala. SHA-256 das
entradas: `EA321020063F199C72D574D9F072A12D42133BF6578805B344C3332D6C7FCBFB`;
do gabarito: `AADD3F23C292C1E51BA6F2575042862C52218215F5F67241A65857B009F8B635`.

Resultado bruto: **0/6 regras alinhadas**. Cinco propostas representáveis
foram estruturalmente inválidas (`regra_invalida`): o modelo colocou `e/ou`
ou verbos no campo do operador, preencheu unidade com outro atributo, citou
apenas o referente sem ancorar o valor e, em um caso, confundiu o efeito com
condição. O caso misto exigia `(porta e janela) ou botão`; o modelo forçou
um conectivo plano e recebeu `forcou_regra_nao_representavel`. O classificador
isolado de direção acertou alguns rótulos, mas isso não compensa os campos
errados. Nenhuma saída obteve autoridade para composição ou efeito.

A primeira fronteira RED observada é a **produção estruturada da condição**,
antes do confronto com a revisão. Não há evidência de que mudar somente o
verificador ou acrescentar exemplos de treino resolva essa falha. Próximo
experimento: decompor a proposta em seleção de trechos da fonte e normalização
de operadores/relações, definir um contrato de saída menos ambíguo e medir em
um novo painel cego, incluindo abstenção em árvore aninhada. Não ajustar este
gabarito aos erros do modelo. P01 permanece aberto; não liberar no runtime.
