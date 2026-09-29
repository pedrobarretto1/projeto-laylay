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

### Dois estágios e painel novo: primeira fronteira medida (27/09)

O experimento `sonda_produtor_condicoes_v2.py` separa (1) escolha de trechos
literais e relação lógica de (2) normalização de referente, atributo,
operador, valor e unidade. O segundo estágio só roda quando os trechos e a
relação coincidem com a revisão manual local; esse *gate pelo gabarito* serve
apenas à sonda, não é uma política transportável ao runtime. O modelo não
recebe os slots revisados em nenhuma chamada. A revisão não é externa nem
autenticada. Os controles locais protegem citação inventada, condição
fundida, conectivo trocado, árvore mista e ausência de autorização.

O painel v2 foi usado para ajustar a aferição: artigo inicial e `Se` com
diferença de caixa passaram a ser aceitos quando o trecho literal existe
unicamente na fonte. A repetição de v2, portanto, é **diagnóstica, não um
novo holdout**: 2/6 terminaram alinhados; 1 chegou à normalização e errou
operador/unidade; 1 acertou os trechos e errou a implicação; 2 pararam na
segmentação/representabilidade. Hashes SHA-256 de v2: entradas
`5B5839E70F40A07DC098A3E655AA66C527940FA44A9A3CCFBB4E062741FB8B6F`,
gabarito `43524B3777347266C367AB23F04430178E83A5FE1C7FE2584C9F7105FA868B1B`.

Com código e avaliador fixos, o painel **v3 inédito** teve **1/6 alinhado de
ponta a ponta** (`PAINEL_IFF`). As outras primeiras fronteiras foram:

- `FORNO_E`: trecho para a temperatura omitiu `ficar`, perdendo literalidade;
- `MUDA_ONLY`: os dois trechos estavam presentes, mas o modelo declarou
  `unico` para duas condições (erro de cardinalidade/conectivo);
- `VALVULA_OU`: trechos vieram sem os acentos da fonte, logo não eram citações
  literais; rejeitar evita transformar paráfrase em evidência;
- `SENSOR_CAIXA_B`: um único trecho incluiu condição **e** efeito;
- `FILTRO_MISTO`: forçou regra plana onde havia `(filtro e bomba) ou operador`.

Só `PAINEL_IFF` alcançou o segundo estágio; assim, **não há base para afirmar
que a normalização geral melhorou**. Hashes SHA-256 do primeiro painel v3:
entradas `A3D1BDD6C13CA3FE179725602A83E9257026365D1166028B9A4B107928F0E462`,
gabarito `551D33CCB756090803E19E478720D21A86CC5476C92A60F65EE85DA7E8C9E609`.
O enunciado `FORNO_E` diz “pode assar”, portanto seu efeito deve ser tratado
como possibilidade/permissão, não como prova de que o pão de fato assou.

**Próxima hipótese, ainda não provada:** a tarefa de copiar texto e definir
a lógica ao mesmo tempo excede o contrato que o produtor segue de modo
confiável. Próximo experimento não deve relaxar a âncora nem retreinar sobre
v3: gerar candidatos de trechos literais, identificados por posições na
fonte, selecionar IDs e aferir a relação em um **novo painel cego**. O gerador
de candidatos precisará demonstrar cobertura sem entregar o gabarito, e a
árvore mista deverá continuar fail-closed. P01 segue aberto, sem promoção.

### Falsificação de intervalos livres de tokens (27/09, diagnóstico)

Um protótipo adicional pediu ao mesmo Qwen os índices de início/fim de cada
condição numa lista de tokens da fonte. O código reconstrói as citações
literalmente a partir dos offsets; não existe normalização silenciosa de
acentos, nem trecho inventado. Cinco controles locais passaram: reconstrução
dos cinco casos representáveis, índices inválidos, sobreposição, inclusão do
efeito e gabarito ausente do pedido ao modelo. Este contrato é apenas
diagnóstico offline e não altera o produtor da Laylay.

No **v3 já visto**, portanto sem valor de holdout independente, houve **0/6
propostas alinhadas**. Em `FORNO_E` o modelo declarou abstenção com intervalos
não vazios; em `MUDA_ONLY` escolheu limites que excluíram os valores e usou
`unico` para duas condições; em `VALVULA_OU` cortou o referente e a unidade;
em `PAINEL_IFF` incluiu só “autoteste”, sem “passar”; em `SENSOR_CAIXA_B`
incluiu o valor mas perdeu o referente; e em `FILTRO_MISTO` achatou a árvore.
A proposta de índices elimina erros de *grafia copiada*, mas **não resolve a
identificação dos limites nem a lógica**. Não compará-la numericamente com o
primeiro uso cego de v3: o painel foi reutilizado, e uma nova chamada ao
modelo não isola a diferença de contrato de toda variação de geração.

Essa experiência enfraquece a hipótese de que bastaria trocar citação por
offset. Antes de criar outro painel ou treinar, o próximo passo é especificar
um **gerador de candidatos atômicos com cobertura auditável**, sem derivar
opções do gabarito; só então medir se a escolha entre candidatos e a relação
condicional melhoram em fontes novas. Se a cobertura falhar, a sonda deve se
abster, não inventar segmento. P01 permanece aberto e fora do runtime.

### Candidatos literais indexados: painel v4 (27/09)

`sonda_produtor_candidatos_v1.py` oferece trechos retirados da própria fonte
por uma segmentação lexical de condicionais explícitas com `se`/`apenas se`.
O gerador não lê gabarito nem decide verdade, referente ou autoridade; a
cobertura é medida depois, com revisão manual local separada. O modelo só
recebe IDs e citações candidatas, fonte, referentes e efeito fixo. Nenhuma
opção ou resposta pode autorizar composição de fala ou executar efeito.

O painel v4 de **sete fontes novas** foi congelado antes da primeira chamada
ao Qwen3:4b-instruct. SHA-256 das entradas:
`CE748D3FF108875879E6CD7437C9BDF7C6FF2CDFB7E1D9AF6A66140F6C5259B4`;
do gabarito local:
`BA3A3DAF6A161CCEE2C03BD97FCF300736E6B591A193B13FE00BC42BD7C837B6`.
Cinco regras planas receberam candidatos com cobertura relativa à revisão;
`SOLO_QUANDO` ficou sem candidatos (o marcador `quando` ainda não é suportado)
e `TRAVA_MISTA` serviu como controle não plano. Essa cobertura **não é prova
de interpretação geral**: frases condicionais implícitas, conjunção dentro
de um sujeito e outros arranjos podem ser segmentados incorretamente.

Na primeira sonda, o Qwen alinhou **4/5 regras planas com cobertura**:
`ESTUFA_E`, `BOMBA_OU`, `STATUS_IFF` e `MEDIDOR_RESERVATORIO`. Em
`ARQUIVO_ONLY`, escolheu os dois candidatos e o conectivo corretos, mas
classificou `apenas se` como suficiência quando o gabarito o marca como
necessidade (`implicacao_divergente`). Portanto o placar global é **4/7**,
não 4/5: uma regra ficou sem cobertura e a árvore mista não foi resolvida.
Nessa primeira chamada o modelo também tentou achatar `TRAVA_MISTA`; o
comparador recusou `forcou_regra_nao_representavel`.

Esse último RED revelou que o veto à mistura `e/ou` dependia do gabarito.
Um teste canônico vermelho mostrou a chamada ao modelo acontecendo. O
contrato experimental agora marca a mistura textual de conectivos e **não
consulta o modelo para propor uma regra plana**; o teste passou. É uma guarda
conservadora: pode gerar falsas abstenções quando `e/ou` pertencem ao nome ou
ao sujeito, então não equivale a um parser lógico geral. O ganho da guarda
não foi somado aos quatro acertos da primeira sonda. Nenhum resultado foi
retreinado ou promovido; falta medir cobertura e relação em outras formas
linguísticas e validar ensino, verificador e fala final no runtime. P01 aberto.

### Direção explícita, `quando` e painel v5 (27/09)

Um sinal lexical separado agora reconhece `apenas/somente/só se` e
`apenas/somente quando` como **necessidade**, e `se e somente/só se` como
**equivalência**. `Se` condicional simples sinaliza suficiência só nos
contextos superficiais cobertos; `quando` simples não recebe direção
automática. Negação e citação deixam o sinal indeterminado. A seleção do
marcador passou a priorizar operador composto quando existe um `se`
pronominal anterior (`o braço se move apenas se...`). O sinal pode **vetar**
direção incompatível antes de consultar o gabarito local, mas não certificar
verdade, completude ou contexto. REDs canônicos reproduziram inversão de
direção mesmo com gabarito alterado e seleção do `se` pronominal; os testes
ficaram verdes após o candidato mínimo. O gerador também passou a oferecer
um candidato para `quando`, sem inferir que a relação temporal é lógica.

O painel v5 (sete fontes inéditas, congeladas antes da chamada) tem SHA-256
das entradas
`7461AE8F8E4424626AA3C339136690693FD918A157F8E58AA6D79920713EAC89`
e do gabarito local
`4774D24D64D6D0FDAF05AACC680F77501BE45FF8954ECD733B103737AED288A5`.
Cinco regras planas tiveram candidatos cobertos; `SENSORES_SUJEITO_COMPOSTO`
foi segmentado incorretamente em `sensores A` + `B detectarem fumaça` e parou
antes do modelo; `ACESSO_MISTO` foi recusado antes do modelo por mistura
textual `e/ou`. Assim o gerador continua sem cobertura geral.

Na primeira sonda v5, **3/5 regras planas cobertas** alinharam seleção,
conectivo e direção à revisão manual local (`BACKUP_SOMENTE_QUANDO`,
`ICONE_SE_E_SO_SE`, `BRACO_SE_MOVE`). `VASO_OU` teve candidatos corretos, mas
o Qwen trocou o `ou` por `e`. Em `NIVEL_QUANDO`, selecionou o candidato e
absteve-se da direção (`indeterminado`), divergindo do gabarito local que
marcava suficiência; essa abstenção é mais segura que inventar uma implicação
a partir do marcador temporal. O resultado global é **3/7 alinhados à
referência local**, não uma medida de qualidade de ensino. Nada foi enviado
ao runtime.

O RED de `VASO_OU` mostrou que o comparador ainda dependia do gabarito para
vetar `e` versus `ou`. A sonda passou a expor um sinal textual do conectivo
entre candidatos e a vetar a troca **antes** do gabarito; teste com gabarito
deliberadamente errado confirmou RED→GREEN. Essa guarda pós-sonda não conta
como novo acerto de v5. Sujeitos compostos podem confundir a segmentação e
o próprio sinal, então o próximo trabalho deve distinguir conectivos **entre
orações condicionais** de conectivos **dentro de referentes**. Não expandir
o uso operacional nem reescrever o gabarito histórico para elevar a métrica.
P01 segue aberto.

### Segmentações alternativas e painel v6 (27/09)

A primeira fronteira RED de v5 era a **segmentação**, não a direção lógica:
`SENSORES_SUJEITO_COMPOSTO` cortava `sensores A e B` em duas supostas
condições. Uma sonda offline nova (`sonda_segmentacoes_condicionais.py`)
oferece duas segmentações literais da mesma região da fonte: `integral`
(um predicado com possível sujeito composto) e `atomica` (condições
separadas por `e`/`ou`). O modelo escolhe só um ID e a direção; o código
reconstitui os trechos originais. A comparação e a autorização continuam
fora do modelo. Misturas textuais de `e/ou` continuam recusadas antes da
chamada por não caberem no contrato plano. Nenhuma integração runtime.

O painel v6 foi revisado localmente e congelado antes da primeira consulta
ao Qwen. SHA-256 das entradas:
`485DED76A32AEA6D6305CEA8CB5A012142109AE4B9E009A698524B3B6BFEA5A4`;
do gabarito:
`D4BC5068D963EC3783B58656C6230C72C9E8159766B9C3C04DCB4E7E54DE4CBE`.
As seis regras planas tinham uma alternativa com cobertura textual segundo
essa revisão; a regra mista foi recusada antes do modelo. A primeira sonda
com `qwen3:4b-instruct` selecionou `integral` **nas seis regras**: alinhou
três com sujeito/referente composto (`VALVULAS_SUJEITO_E`,
`CODIGO_SUJEITO_OU`, `PORTAS_NECESSARIAS`) e errou três com predicados
independentes (`ESTUFA_PREDICADOS_E`, `FILA_PREDICADOS_OU`,
`PAINEL_EQUIVALENTE`). Portanto, **3/6 escolhas planas** alinharam à
referência local; não é sucesso geral nem ensino validado. O primeiro RED
remanescente é a escolha semântica entre segmentações, com possível viés
da opção integral vir primeiro. Próximo experimento: aferir pistas de
fronteira de predicados e balancear ordem das opções em um painel novo,
sem alterar o gabarito v6 ou ampliar a influência da rede. P01 segue aberto.

### Controle de ordem e fronteiras predicativas (27/09)

O controle de ordem no v6 apresentou as mesmas opções e IDs ao Qwen, apenas
invertendo a lista. Com `integral` primeiro, a proposta foi `integral` nos
**6/6** casos planos (3/6 alinhados à referência local); com `atomica`
primeiro, foi `atomica` em **5/6** (2/6 alinhados). Portanto, a ordem das
opções influencia fortemente a escolha; mera votação entre as duas ordens
também não é critério suficiente, pois `PAINEL_EQUIVALENTE` permaneceu
`integral` nas duas apresentações e está divergente do gabarito. A primeira
fronteira RED continua sendo **seleção da segmentação**, não geração de
trechos literais nem direção do marcador.

Uma sonda alternativa (`sonda_fronteira_predicados_v1.py`) retirou a escolha
`integral`/`atomica` do modelo. Ele propõe para cada fragmento se há verbo
predicativo explícito e uma palavra-âncora literal; o código valida ID,
âncora e posição, e reconstrói grupos até cada predicado. IDs válidos podem
vir permutados na resposta, pois são remontados pela ordem da fonte; IDs
duplicados, âncoras inventadas, grupos incompletos e estrutura mista são
recusados. Isso representa também a partição intermediária `sujeito A e B
predicam` + `bateria predica`, ausente da lista binária anterior. Uma âncora
literal ainda **não prova** que a palavra seja verbo; a etapa segue em sombra.

O painel v7 de oito fontes foi revisado localmente e congelado antes de
consultar o modelo. SHA-256 das entradas:
`2D52828D5D2A20BEE9A6492C18428719E3EEAADF15F9A8DBEE0A541C62D790C8`;
do gabarito:
`84CBD940FD2EEFB17DE8FE902DAC4F2C4224180438283640F9C94729C6B9FAC4`.
Na primeira sonda com `qwen3:4b-instruct`, **3/7** regras planas alinharam
à referência local (`MODULOS_SUJEITO_E`, `PROTOCOLO_SUJEITO_OU`,
`CREDENCIAL_PREDICADOS_OU`); três propostas foram rejeitadas por formato
incoerente de IDs/âncoras (`SOLO_PREDICADOS_E`, `ICONE_EQUIVALENTE_V7`,
`SENSORES_E_BATERIA`) e uma por âncora fora do fragmento (`FREIOS_NECESSARIOS`).
`PROTOCOLO_MISTO_V7` foi recusado antes do modelo. O novo contrato **não
superou** o resultado anterior neste painel, mas tornou as falhas visíveis
e bloqueadas. Próxima hipótese a testar: saída indexada por IDs fixos,
sem strings de ID livres; mesmo que o formato melhore, a classificação
predicativa precisará de avaliação independente e painel novo. Nada foi
promovido a fala, treino, autorização, executor ou runtime. P01 segue aberto.

### IDs fixos, POS português e painel v8 (27/09)

Base observada: `main`/`a078360e6b694c37f981e8be11f1470dd14571d5`,
worktree suja com alterações paralelas preservadas. Nenhum commit criado.

No mesmo v7 já usado como desenvolvimento, o contrato aninhado com IDs fixos
continuou em **3/7 alinhados**; o contrato de campos planos e entrada mínima
também ficou em **3/7**. A saída livre de IDs era uma falha de interface,
mas não era a raiz suficiente: o Qwen ainda inseriu texto de sintaxe em
âncoras, escreveu `"false"` como string no lugar de vazio e confundiu
adjetivo com verbo. Essas propostas foram recusadas; não se normalizou o
erro para fabricar acertos. As duas variantes estão na sonda offline v2,
com o contrato aninhado original preservado para comparação.

Foi avaliado isoladamente o [pipeline português do spaCy](https://spacy.io/models/pt)
`pt_core_news_sm` 3.8.0, com spaCy 3.8.16 em cache temporário do `uv`, sem
instalação na `.venv314` nem alteração da Laylay em execução. A sonda
`sonda_fronteira_pos_portugues.py` usa POS `VERB`/`AUX` do texto inteiro
para fornecer âncoras à mesma reconstrução literal; seu resultado continua
sem autoridade para fala ou efeitos. No v7 reutilizado ela alinhou 7/7 regras
planas à revisão local, apenas como diagnóstico de desenvolvimento.

O painel v8 (14 fontes, 13 regras planas na revisão local) foi congelado
antes da primeira execução POS. SHA-256 das entradas:
`C2D8E86F871B2D8262EB257166E72BEBC5F73B55146BE5079AB51DEF25A8A4AC`;
do gabarito:
`9E3C63AA237693A65C8F7FE8C43E9056CEC1D1C4535DCC31206A6E99C7CAA1FF`.
Na primeira execução, **9/13** regras planas alinharam à revisão manual
local. Uma árvore realmente mista foi recusada corretamente antes do POS.
As outras quatro divergências têm primeiras fronteiras diferentes:

- `CHUVA_VENTO_OU`: POS marcou `cessar` como `ADJ`, apesar de ser o verbo
  da primeira condição; a sonda juntou as duas condições indevidamente.
- `RELATIVA_OBJETO_COMPOSTO`: `monitora` é `VERB` em uma oração relativa
  dentro do sujeito, não um predicado independente. Contar qualquer verbo
  no fragmento gerou uma separação falsa — **risco de falso positivo**.
- `LED_ELIPSE`: a segunda condição tem verbo elíptico; o contrato de verbo
  explícito se absteve. É perda de cobertura, não confirmação inventada.
- `MISTO_SUJEITO_OU`: o `e` pertence ao sujeito composto e o `ou` liga
  condições; o gerador lexical tratou a mistura superficial como árvore
  mista e recusou uma regra plana antes do POS.

Conclusão: POS é um sinal melhor que a seleção por posição neste piloto,
mas **não prova fronteira de oração** e não deve entrar em produção como
decisor isolado. As duas frentes seguintes são separadas por raiz: (1)
escopo sintático do conectivo/oração relativa, priorizando impedir falso
positivo; (2) cobertura de elipse e mistura textual sem transformar uma
árvore real em regra plana. Nenhum gabarito v8 será editado para elevar o
placar; validação de ensino e fala final no runtime seguem ausentes. P01
continua aberto.

### Escopo da oração relativa: candidato offline e controle v9 (27/09)

Base observada: `main`/`a078360e6b694c37f981e8be11f1470dd14571d5`;
worktree já suja, preservada. Primeira fronteira RED do caso
`RELATIVA_OBJETO_COMPOSTO`: a segmentação lexical apresentava dois
fragmentos, mas a sonda POS usava `monitora` (`VERB`, `acl:relcl`) como
prova de predicado independente no primeiro. A hipótese de POS não reconhecer
o verbo foi falsificada: ele o reconheceu, mas seu papel é descrever
`sensor`. A hipótese de impossibilidade de reconstrução literal também caiu:
quando esse verbo deixa de fechar um grupo, o trecho completo é recuperado
sem mudar o gerador lexical nem o gabarito v8.

O candidato mínimo da sonda exclui verbos `acl:relcl` e auxiliares ligados
diretamente a eles ao escolher a âncora que fecha um grupo. Um filtro para
**todos** os descendentes foi falsificado no painel v9: caiu de 8/8 para
5/8 porque o parser ligou três verbos principais a uma relativa. O filtro
amplo foi rejeitado; não se usou essa árvore como prova semântica plena.
Os REDs de relativa simples, relativa com outra premissa e auxiliar subordinado foram
reproduzidos antes do respectivo ajuste; 55 testes focados dos módulos de
sonda passaram depois. No v8 de desenvolvimento, o caso original alinhou
à referência local; o total passou de 9/13 para **10/13** regras planas.
Permanecem os REDs independentes de `cessar` etiquetado `ADJ`, elipse de
`LED verde` e recusa da mistura superficial `e/ou`.

O painel v9, de oito frases novas, foi congelado antes da primeira execução
com o modelo português: SHA-256 das entradas
`423C4FBBF9BEA9A0AECAA191CA3F682F433B6F2D32B308D0F07EFDFC88D401F4`;
do gabarito local
`CA2EC79C637394AE51F0FDFAE22FD556B7306DA182A4282460984283AC0C7F34`.
Houve **8/8 alinhamentos de trechos e relação na revisão local**, incluindo
controles com duas premissas independentes. Isso não equivale a 8/8 análises
sintáticas corretas: em `PESSOA_RELATIVA_DOIS_VERBOS`, o parser marcou
`escreve` como `ROOT` e `confirmar` como `xcomp`; a sonda fechou o grupo
com `escreve`, embora a condição principal dependa de `confirmar`.
O alinhamento de superfície foi acidental e essa dependência ambígua é a
próxima fronteira RED. A revisão do painel é manual local, não validação
externa. O candidato não entrou em `laylay.py`, fala, treino, autorização,
executor ou runtime real. P01 segue aberto.

### Âncora acidental em relativa coordenada: abstenção local (27/09)

Mesma base `main`/`a078360e6b694c37f981e8be11f1470dd14571d5` e
worktree paralela preservada. No caso `PESSOA_RELATIVA_DOIS_VERBOS`, a
referência local exige uma condição completa, mas o parser marcou `escreve`
como `ROOT` e `confirmar` como `xcomp`. A reconstrução anterior alinhava o
trecho por acaso, com âncora incompatível com a condição principal. A primeira
fronteira RED é a aceitação de uma fronteira sintática incerta pela sonda POS;
não é erro de execução, fala ou gabarito. Um RED focado confirmou a aceitação
indevida antes do ajuste.

O contrato novo é conservador: se um fragmento tem apenas verbo de oração
relativa e o fragmento seguinte começa diretamente por verbo após o
conectivo, a sonda não decide se esse verbo continua a relativa ou inaugura
a condição. Ela retorna `abstencao_escopo_relativo_ambiguo`, com evidências,
sem reconstrução, aferição ou aprovação para produção. É uma perda deliberada
de cobertura; não é uma interpretação gramatical definitiva. No v9 já usado
para diagnóstico, o resultado passou de 8 alinhamentos de superfície (um
acidental) para **7 alinhamentos e 1 abstenção**.

Um painel v10 com seis fontes novas foi congelado antes da primeira execução
do parser português. SHA-256 das entradas:
`589F45008F20537BD4B9A6A366B36ED79D96BE0D128DDA41DBDD7F98EF786C14`;
do gabarito local:
`8A206B6557E0B9B3AB9BC391EEC86EAD54693D44F4DDA2D33EB80DA8CA0125A1`.
Primeira execução: **4 alinhamentos de superfície e 2 abstenções** nas
relativas coordenadas. Controles com duas premissas independentes e com
relativa seguida de verbo principal claro permaneceram alinhados. A revisão
continua manual local; a execução do spaCy é isolada, não runtime da Laylay.
No v8 de desenvolvimento, os estados permaneceram 10 alinhamentos, uma
divergência, uma abstenção por predicado insuficiente e duas recusas de
estrutura plana. A seleção de testes da sonda passou **68/68**. Nenhuma
mudança em `laylay.py`, fala, treino, autorização ou executor. Próxima
fronteira: aferir o papel do verbo de fechamento sem confiar no `ROOT` do
parser e, separadamente, os REDs de POS, elipse e mistura lexical. P01 aberto.

### Auditoria da âncora independente dos trechos: painel v11 (27/09)

Base `main`/`a078360e6b694c37f981e8be11f1470dd14571d5`, worktree
paralela preservada. A auditoria dos painéis v8–v10 mostrou que `ROOT`
não identifica com estabilidade o verbo que fecha uma condição: verbos
principais receberam `acl`, `conj` e `xcomp`, enquanto `escreve` recebeu
`ROOT` na relativa coordenada e não era a âncora correta. Logo, escolher
`ROOT` ou confiar somente no alinhamento do trecho é insuficiente.

O contrato offline `confrontar_ancoras` compara, **após** a proposta da
sonda, cada âncora por ID com uma revisão manual separada. Ele distingue
`ancoras_alinhadas_revisao_pendente`, `ancoras_divergentes`, referência
inválida e `abstencao_sem_afericao_de_ancora`; nenhum desses estados concede
aprovação ou autorização. Um RED mostrou que trecho alinhado podia esconder
âncora divergente; outro protegeu a abstenção sem convertê-la em acerto.
O gabarito não entra na escolha de âncoras.

O painel v11 foi escrito e congelado antes da primeira execução do parser:
oito fontes novas, com trecho e âncoras por fragmento revisados localmente.
SHA-256 das entradas:
`6C188D1D8336168F6F5D5FE8C9C7B5FFC013AD3592CCEF4A55DDC9EB2AEE5745`;
do gabarito:
`0CCEE083F50E95C6CF2F87920C8AC37848D8F3F15212B6755AD8CCC433F49024`.
Na primeira execução, **6/8 âncoras de caso alinharam à revisão local** e
**2/8 se abstiveram**, sem proposta aceita com âncora divergente nesse painel.
`ALUNA_RELATIVA_COORDENADA` se absteve na fronteira relativa ambígua.
`VALVULA_RELATIVA_OBJETO` também se absteve: o parser classificou `vapor`
como `VERB`, criando um candidato falso de âncora; é a frente de erro POS,
não motivo para inserir exceção lexical para `vapor`. Em
`ARTISTA_RELATIVA_COORDENADA`, a âncora `confirmar` alinhou, mas o parser
nem reconheceu `pinta` como verbo; alinhamento de âncora não valida sua
análise gramatical completa. A suíte focada da área passou **71/71**.

Este é um benchmark manual local e offline, não prova de ensino, fala final
ou runtime real. `laylay.py`, treino, autoridade e executores não foram
alterados. Próximo trabalho por raiz: tratar a confiabilidade do sinal POS
sem perder o fail-closed de escopo; elipse e mistura lexical continuam
fronteiras distintas dentro de P01.

### POS conflitante e fronteira interna sem âncora: painéis v12–v15 (27/09)

Base `main`/`a078360e6b694c37f981e8be11f1470dd14571d5`, worktree
paralela preservada. Primeira fronteira RED em `CHUVA_VENTO_OU`: o gerador
literal produzia as duas condições corretas, mas `pt_core_news_sm` marcava
`cessar` como `ADJ/advcl`; a sonda fundia as condições. A hipótese de erro
no gerador foi falsificada. Um RED novo com `soprar` em posição intermediária
mostrou o mesmo risco com `ADJ/acl`; frases com adjetivos atributivos
`amod` continuaram como controle positivo.

O candidato POS não promove adjetivo a verbo nem usa lista de palavras ou
sufixos. Quando um fragmento sem predicado reconhecido contém POS não verbal
com papel oracional suspeito (`ADJ` em `advcl`/`acl`, ou raiz não verbal com
sujeito), retorna `abstencao_predicado_pos_ambiguo`. No v8 de desenvolvimento,
`CHUVA_VENTO_OU` passou de fusão falsa para abstenção; os dez alinhamentos
locais permaneceram. Uma sonda composta mostrou que `soprar` no meio de três
premissas também passou de fusão falsa para abstenção.

Painel v12 congelado antes da primeira execução: SHA-256 entradas
`4CB773AF569485FEB2E99E9F9570323E15C87AD115C595546427BF8FD49E3971`,
gabarito local
`D59BF490922A5EB6A4E3694CF2E3A572CC812BAC327C5284E1CDACD737B5E40B`.
Primeira execução: **5 alinhamentos e 3 abstenções**; uma abstenção inicial
era apenas `sem_predicado_suficiente`. O mesmo verbo `soprar` apareceu como
`ADJ/acl` sem sujeito ligado e o fim do grupo impediu sucesso falso.

Painel v13 congelado antes da primeira execução: SHA-256 entradas
`FBB3EF2812EADB248DE4FF39057520155AF6EE46428CB1D43D8748F1BFE73DD8`,
gabarito local
`A7FCCB7BED4CEE369606C139941A7BF8F6EB7F48274BEE3B73D0EFB4EACC8DE1`.
Primeira execução: **4 alinhamentos, 2 fusões falsas e 1 abstenção**.
`soprar` virou `ADJ/ROOT` e `soar`, `PROPN/ROOT`; ambos tinham sujeito ligado.
O teste falsificou a regra anterior, que só cobria `ADJ` clausal. O candidato
ampliado os marcou como conflito POS e repetiu o v13 com **4 alinhamentos e
3 abstenções**, sem fusão aceita. Não se concluiu daí que toda classificação
POS errada esteja detectada.

Painel v14 congelado antes da primeira execução: SHA-256 entradas
`C70BA2A22769FD186520709FC863BD9E331CBFECD65624B881BE5776247A8F2E`,
gabarito local
`1F6951A8C5DD303116520BDF1A25B8719B02B9BA3B607D923A22E39669B140AC`.
Ainda surgiram **2 fusões falsas**, com `soprar` como `ADJ/amod` e `soar`
como `PROPN/ROOT` sem sujeito ligado; houve 3 alinhamentos e 1 abstenção.
Isso falsificou a tentativa de resolver segurança apenas por etiquetas do
parser. A primeira fronteira comum é a reconstrução: fragmento sem âncora
**entre** dois fragmentos já ancorados era unido automaticamente ao próximo.

O contrato compartilhado de `reconstruir_condicoes` agora retorna
`fronteira_interna_sem_predicado_ambigua` para esse padrão. Prefixos sem
predicado antes da primeira condição continuam podendo compor um sujeito;
um sufixo sem predicado continua `sem_predicado_suficiente`. Dois REDs
reproduziram a fusão antes do ajuste, um deles com um segundo sujeito
composto que seria semanticamente válido, mas não demonstrável apenas pela
âncora ausente. Depois, o v14 ficou em **3 alinhamentos e 3 abstenções**.

Painel v15 congelado antes da primeira execução: SHA-256 entradas
`ECEE69FB7FA665FABF9E2FF1291B4464550EF52B1ECE8497542B38B19283F8F7`,
gabarito local
`0712D04251EA084C239C25E32C90E39D844B71E896D61B3BB9A63C7D41C99544`.
Primeira execução: **4 alinhamentos e 3 abstenções**; duas são casos
semanticamente válidos com sujeito/objeto composto depois de uma primeira
condição. Essa perda de cobertura é deliberada e não deve ser ocultada.
A suíte focada passou **79/79**. O modelo português foi carregado do cache
isolado do `uv` com `--offline` após a URL remota falhar; nenhuma dependência
foi instalada na `.venv314`. Revisão e gabaritos são manuais locais.

Nenhuma alteração em `laylay.py`, fala, treino, autorização, executor ou
runtime real. P01 segue aberto: a segurança de fronteira melhorou na sonda,
mas restaurar cobertura requer evidência sintática adicional e outro painel
congelado, sem afrouxar a abstenção. Elipse e mistura lexical são frentes
distintas da mesma investigação, não corrigidas nesta etapa.

### Continuidade nominal é evidência, não liberação: painel v16 (27/09)

Mesma base `main`/`a078360e6b694c37f981e8be11f1470dd14571d5`;
worktree paralela preservada. A guarda de `fronteira_interna_sem_predicado_ambigua`
impediu fusões falsas no v14, mas também se absteve em `CAMERA_OBJETO_COMPOSTO`
e `SERVIDOR_SENSORES_SUJEITO` do v15, apesar de ambos serem casos válidos
na revisão local. A primeira fronteira ainda incerta é a atribuição do
fragmento nominal intermediário ao grupo anterior ou ao seguinte; ausência
de `VERB/AUX` não resolve essa direção.

Uma prova somente diagnóstica foi adicionada à sonda POS: quando o fragmento
interno sem âncora contém um único substantivo coordenado, ligado por
dependência a um objeto nominal do verbo ancorado imediatamente antes,
registra `continuidades_nominais_candidatas` com ID, token, antecedente e
âncora. O resultado **continua**
`fronteira_interna_sem_predicado_ambigua`, sem reconstrução aceita,
`afericao`, aprovação ou autorização. REDs de integração provaram que a
evidência aparece para `foto e vídeo` e não aparece em `vento soprar`
etiquetado erroneamente.

O painel v16 de seis fontes novas foi congelado antes da execução com o
parser português. SHA-256 das entradas:
`37247CCF22688A2B11FE65A6C4F369F5810878B3C8B025BCFEAD6CE5563EAD42`;
do gabarito local:
`808FAA67CBA736E92A76D47C628D4C65A8D4CBF9D8A740D2A827A7A069D9685E`.
Primeira execução: **1 alinhamento de superfície e 5 abstenções**. A
evidência nominal apareceu em **2/3 objetos compostos** e em **0/2 controles
problemáticos** (verbo POS perdido e sujeito composto). No terceiro objeto,
o parser rotulou `câmera` como `VERB`, escolheu a âncora errada e a prova
nominal não foi emitida. Portanto, nem a presença nem a ausência dessa
evidência podem autorizar uma reconstrução automática hoje. A revisão é
manual local, sem validação de fala ou ensino. **81 testes focados verdes**.

Produção não alterada; `laylay.py`, treino, fala, autorização, executores
e runtime real não receberam o candidato. P01 permanece aberto. Próximo
contrato a investigar: representação explícita de vínculo de fragmentos
nominais com validação independente da etiqueta POS e da âncora inicial;
não enfraquecer o fail-closed atual por causa de cobertura local.

### Etiqueta verbal contraditória e controle inédito: painel v17 (27/09)

Base `main`/`a078360e6b694c37f981e8be11f1470dd14571d5`, worktree
paralela preservada. No v16, o parser marcou `câmera` simultaneamente como
`VERB/nsubj` e núcleo de um determinante `a/DET/det`, escolhendo esse token
antes de `registrar`. O primeiro desvio observável foi a seleção da âncora,
não a reconstrução posterior. Nos painéis v8–v16, não apareceu outro token
verbal com esse mesmo conflito de papel e determinante; isso apoia a guarda
local, mas não demonstra cobertura geral. Hipóteses concorrentes de que
`registrar` estivesse ausente ou que a continuação `vídeo` não tivesse
vínculo nominal foram falsificadas pela análise do mesmo texto completo.

Um RED focado reproduziu a âncora incorreta. O candidato mínimo, **somente
na sonda POS offline**, exclui da lista de âncoras um `VERB` com papel
`nsubj`/`obj` e filho `DET/det`, registra `pos_contraditorio` e **se abstém**.
No v16 repetido, `registrar` aparece como âncora e o vínculo candidato
`vídeo` → `foto` fica visível; esse caso continua sem aferição, aprovação
ou autorização. Os painéis v8–v15 mantiveram suas contagens de estados.

O v17 foi congelado antes da primeira execução. SHA-256 entradas:
`3356446DA7B3E243EA3446F1991CE622BB62E4B478381BE9ADDD1AC66164BCE6`;
gabarito manual local:
`DAB98CA4D3BE7B62951F400F78A5649CE9B1E263D789649609810BDFA3A5FD55`.
Na primeira execução com `pt_core_news_sm` isolado em cache: os **3/3**
objetos compostos trouxeram evidência nominal e ficaram em
`fronteira_interna_sem_predicado_ambigua`; o controle de três condições
independentes alinhou trechos e âncoras; o sujeito composto ficou em
abstenção sem evidência nominal. O controle `porta/vento/bateria` também se
absteve, porque `soprar` foi novamente classificado fora de `VERB/AUX`.
Assim, houve **1 alinhamento e 5 abstenções** em seis casos; não houve
fusão falsa aceita, mas há perda de cobertura real. O gabarito não foi
adaptado ao resultado. Suíte focada: **82/82 verdes**.

Esta prova não valida ensino, verificador de alegações nem fala final.
Nenhuma mudança em `laylay.py`, treino, fala, autorização, executores ou
runtime; P01 permanece aberto. A próxima fronteira é demonstrar uma
representação de agrupamento nominal e detectar POS incorreto sem depender
de exceções lexicais; até lá, abstenção permanece o resultado seguro.

### Vínculo de objeto com offsets e prévia isolada: painel v18 (27/09)

Mesma base `main`/`a078360e6b694c37f981e8be11f1470dd14571d5`;
mudanças paralelas da worktree preservadas. O v17 sustentou o vínculo
`conj` → `obj` → âncora anterior, mas a evidência descartava posições e
dependia do POS nominal. A primeira fronteira ainda RED para uma partição
auditável era a perda de identidade literal do vínculo; o reconstrutor
canônico se abstinha corretamente. Um RED novo exigiu offsets da fonte mesmo
quando as etiquetas POS são contraditórias. Outro RED exigiu prévia literal
isolada, sem transformar essa evidência em decisão do reconstrutor.

A sonda POS offline agora registra `vinculos_objeto_candidatos` com IDs,
relação direta, offsets do termo, antecedente e âncora, além de
`pos_conflitante`. A detecção do arco não usa POS como condição de entrada;
etiqueta `VERB` coordenada a um `obj` é conflito e provoca abstenção, não
uma condição nova. Somente com arco direto, offsets exatos, POS coerente e
todos os fragmentos internos cobertos há `particao_objeto_em_sombra`: uma
**prévia**, com `aprovado_para_producao=False` e `autoriza_efeito=False`.
`reconstruir_condicoes` continua dono da decisão e continua devolvendo
`fronteira_interna_sem_predicado_ambigua`. Sujeito composto, oração
independente e offset adulterado não produzem a prévia. Um RED adicional
mostrou que arco sintático incompleto lançava exceção; a sonda agora o
descarta sem interromper a análise. Nenhum novo parser foi acoplado ao
runtime.

O painel v18 foi revisado e congelado antes da primeira execução do parser.
SHA-256 entradas:
`8065BD82E5A4D4043C9340027109924776134956688F590BD05C7DB70FB7C208`;
gabarito manual local:
`D8D55387F3913C36D0DB86E783C0A00313300BA3879FDD822B821F3A974F131D`.
O modelo POS em cache gerou a prévia nos **3/3 objetos compostos** e em
**0/4 controles** (oração com POS perdido, sujeito composto, três condições
independentes e relativa com objeto coordenado). Dois controles tiveram
trechos/âncoras alinhados; os outros cinco casos ficaram em abstenção no
caminho canônico. A prévia coincidiu literalmente com os grupos da revisão
local, mas não foi promovida a aferição ou prova semântica. Nos painéis
v8–v17, as contagens de estado permaneceram iguais; a prévia apareceu em
1 caso do v15, 2 do v16 e 3 do v17, sem alterar o resultado canônico.
**86 testes focados verdes.**

P01 permanece aberto: uma dependência sintática também pode errar, e a
ausência de vínculos não prova ausência de relação. Antes de qualquer
influência na Laylay, são necessários contraste semântico adversarial,
validação independente da relação e prova da fala final no runtime.
Produção, treino, autorização e executores não foram alterados nesta etapa.

### Contraste adversarial: dependência pode atravessar a oração (27/09)

Base `main`/`a078360e6b694c37f981e8be11f1470dd14571d5`; worktree
paralela preservada. O v18 não continha a armadilha mais relevante: um
sujeito composto da condição seguinte podia ser etiquetado pelo parser
como `conj` do objeto da condição anterior. Painel v19 foi escrito e
congelado antes da primeira execução. SHA-256 entradas:
`6C9861DEF7B2581E2A0AAA2FE997675F089D20F9184F0A4E18A2B2EAF24A9BB5`;
gabarito manual local:
`95D7E8FAB90C71F8EDA053F0FFDFB19B6F7A7E3CCBA8FDBEF85A6199601A9E9B`.
**Primeira execução: 2/3 controles de sujeito composto geraram prévia
errada**, juntando `o sensor` ou `a câmera` ao objeto da oração anterior;
1/2 objetos compostos recebeu prévia válida. Os outros controles se
abstiveram. Logo, a hipótese “arco direto + offsets + POS nominal bastam”
foi **falsificada**. Não foi erro de offset nem apenas de POS: o parser
atribuiu o próprio arco ao lado errado. A reconstrução canônica continuou
em `fronteira_interna_sem_predicado_ambigua`; nenhuma prévia chegou à fala
ou execução.

Dois REDs focados protegeram a primeira divergência. A sonda agora veta a
prévia quando um fragmento nominal determinado pode começar um sujeito
composto com predicado plural no fragmento seguinte; um objeto composto com
artigo seguido de condição singular continua representável na prévia.
Também se abstém quando um token rotulado `VERB` recebe um determinante,
independentemente de o parser chamá-lo `nsubj`, `obj` ou `advcl`. Repetindo
o v19: **0/5 controles com prévia** e **1/2 objetos com prévia**; a perda do
outro objeto decorre de `recibo` classificado `ADJ`, não de mudança no
gabarito. Esse veto é conservador, não uma prova de análise correta.

Painel v20 novo foi então congelado antes da primeira execução da guarda.
SHA-256 entradas:
`183FB3BF3CE21CDBE0444BE1691C8DA26B62C802DC9E060FC61B0CC3DF06E221`;
gabarito manual local:
`B35ADABB00466EC27B86590BC5FBA34B7CE3AEF3B237CF55C61ED7E7A5778F25`.
A primeira rodada deu **2/3 objetos com prévia, 0/3 controles**. O terceiro
objeto revelou um falso veto diferente: `reiniciarem`, com sujeito próprio
`os servidores`, foi ligado pelo parser a `foto/obj`. Um RED preservou o
verbo com sujeito explícito, mas ainda veta `VERB/conj` de objeto sem
sujeito próprio. Repetição do v20: **3/3 objetos com prévia e 0/3 controles**.
Como essa última restrição foi ajustada após observar o v20, a repetição
**não conta como holdout independente**. Os estados dos painéis v8–v18
permaneceram iguais. **90 testes focados verdes**.

Contrato mantido: `vinculos_objeto_candidatos` e
`particao_objeto_em_sombra` são evidências exploratórias, não revisão
semântica, decisão canônica, prova de ensino ou autorização. O v19 mostrou
um limite estrutural real do parser; novos exemplos ou mais heurísticas
locais não substituem um verificador independente de fronteira. Nenhuma
alteração em `laylay.py`, fala, treino, executor ou runtime real. P01 aberta.

### Segunda checagem unilateral sem parser; Qwen não passou no piloto (27/09)

Mesma base `main`/`a078360e6b694c37f981e8be11f1470dd14571d5` e
worktree paralela preservada. Foi verificada a disponibilidade local de
`qwen3:4b-instruct`, já carregado no Ollama. Piloto somente leitura em três
frases hipotéticas (objeto composto, sujeito composto e ação subordinada):
ao pedir apenas o lado do fragmento intermediário, as saídas foram
`indeterminado`, `anterior`, `anterior`, contra revisão local
`anterior`, `seguinte`, `anterior`. Ao oferecer duas partições literais,
respondeu `indeterminado` nas três. Isso **falsifica o uso desse piloto como
segundo voto confiável**, não prova incapacidade geral do modelo. Nenhum
resultado foi ligado à sonda ou usado como autorização; não foi carregado
outro modelo.

Um RED separado reproduziu que, se a morfologia do parser faltasse, o
sujeito composto `a câmera e o drone pararem` voltaria a produzir prévia
falsa. A menor guarda independente possível foi adicionada em
`veto_superficie_sujeito_composto.py`: ela recebe apenas fonte e três
fragmentos literais com offsets, valida os spans e identifica artigo no
fragmento intermediário seguido de possível predicado plural no seguinte.
Não recebe POS, dependências, árvore sintática nem gabarito. Retorna
`sujeito_composto_possivel`, `sem_veto_superficial` ou `entrada_invalida`;
**nenhum estado aprova a partição**. O veto cobre formas `-arem/-erem/-irem`,
`-aram/-eram/-iram`, `-avam/-iam` e `-assem/-essem/-issem`, sem lista de
verbos específicos. `sem_veto_superficial` significa somente ausência desse
padrão. O guardião morfológico anterior permanece como defesa adicional.

Testes com parser simulado sem morfologia reproduziram e fecharam o RED em
quatro flexões; entradas com offsets adulterados são recusadas. Há perda de
cobertura deliberada: `a peça e a etiqueta e os sensores dispararem` pode
ter objeto composto legítimo, mas recebe o veto por também caber no padrão
superficial. Flexões irregulares, presente e estruturas mais longas não estão
cobertas. Os painéis v15–v20 mantiveram estados e prévias após a mudança;
**97 testes focados verdes**. Essa checagem é um **falsificador parcial**,
não o verificador independente completo necessário para liberar P01.
Nenhuma alteração de produção, fala, treino, executor ou runtime real.

### Painel v21: POS no presente e auditoria da prévia em sombra (28/09)

Base `main`/`a078360e6b694c37f981e8be11f1470dd14571d5`; alterações
paralelas na worktree preservadas. O v21 foi escrito com cinco contrastes
antes da primeira execução: dois sujeitos compostos, três objetos compostos,
incluindo um objeto legítimo seguido de predicado plural. SHA-256 das
entradas: `07335803E693BDBCFB45803DE4B39E2C290CDE899CF3A955F7D9B1E262BE7782`;
gabarito manual local: `635026DFC42F899DD85964BB7202B45768E13735DE1B1979AD992B0CC891AAE4`.
Não há revisão externa nem autenticação semântica desse gabarito.

Na primeira execução com `pt_core_news_sm`, os dois controles de sujeito
composto não produziram prévia. Um objeto composto teve prévia alinhada
literalmente à revisão; os outros dois se abstiveram, um deles por veto
superficial conservador apesar de objeto legítimo. O parser etiquetou
`falham` como `PROPN/flat:name` num controle e como `ADJ/conj` com sujeito
próprio num objeto. Assim, a primeira fronteira deste último era POS, não
reconstrução. Um RED focado acrescentou apenas abstenção explícita para
`ADJ/conj` com sujeito no mesmo trecho; descrições adjetivais coordenadas
sem sujeito próprio continuam sem esse veto. A classificação `PROPN` ainda
não possui verificador independente e continua sem predicado suficiente.

A ausência de `particao_objeto_em_sombra` agora recebe diagnóstico tipado:
vínculo ausente/extra, conflito POS, veto superficial, veto morfológico ou
composição literal inválida. Uma função separada, chamada **após** a
proposta no CLI, compara somente os trechos da prévia ao gabarito local;
ela não compara conectivo nem direção e nunca influencia a decisão. Teste
protege que trocar o gabarito não muda a prévia. Regressão com parser real
nos painéis v15–v21: **44 casos, 14 prévias, 14 trechos alinhados à revisão
manual local, 0 divergentes nessa amostra**. Isso é medição retrospectiva,
não estimativa de precisão em uso real; os painéis anteriores incluem
ajustes feitos após resultados observados. **106 testes focados verdes**
na regressão final desta etapa; P01 continua aberta. Nenhuma
mudança em `laylay.py`, fala, treino, autorização ou executores.
O conjunto ampliado de testes `test_sonda*` e `test_sinal_relacao*` também
passou: **230 testes verdes**. Essa ampliação continua sendo evidência local,
não substitui verificador independente ou runtime real.

Um controle pareado simulado adicional deu ao analisador a **mesma topologia de arco
`conj` ligado a `obj` e a mesma morfologia plural** em dois enunciados do v21:
num, o fragmento é sujeito composto; no outro, objeto composto válido. A
sonda se absteve nos dois. Logo, esse conjunto de sinais não distingue as
leituras por si só; relaxar o veto para recuperar cobertura sem evidência
independente reabriria a prévia falsa. Isto explica por que P01 não deve ser
liberada com uma heurística de sufixos ou com mais exemplos similares apenas.

O CLI agora aceita `--resumo` para emitir contagens reproduzíveis por painel:
`previas`, `trechos_alinhados`, `trechos_divergentes`, `sem_previa` e
`afericao_invalida`. A contagem não transforma abstenções em acertos nem
estima acurácia operacional; exige IDs únicos e estados de não promoção.
Nos painéis v7–v14, 65 casos foram processados pelo mesmo CLI: todos
permaneceram sem prévia experimental, sem estado inválido no resumo.

**Próxima fronteira de P01:** um segundo avaliador precisa produzir, sem ver
o arco do spaCy nem a escolha da sonda, um julgamento tipado sobre a
fronteira: `objeto_da_oracao_anterior`, `sujeito_da_oracao_seguinte` ou
`indeterminado`, com citação literal que sustente a escolha. Primeiro medir
esse avaliador isoladamente em pares mínimos inéditos e balanceados, inclusive
objeto legítimo seguido de verbo plural e sujeito composto com parse enganoso.
Só depois comparar desacordos; acordo de dois modelos **não** equivale a
verdade, revisão humana ou autorização. O gate de produção exigiria, ainda,
validação de trechos e relação, ensino factual e fala final no runtime real.
Não ajustar o gabarito do próximo painel aos erros observados no v21.

### Segunda leitura sem parse: primeira medição v22 (28/09)

`sonda_avaliador_fronteira_independente.py` consulta o `qwen3:4b-instruct`
somente com a fonte e três fragmentos literais gerados lexicalmente. Não
envia POS, dependências, prévia do spaCy nem gabarito. O modelo propõe
`objeto_anterior`, `sujeito_seguinte` ou `indeterminado` e uma citação;
o validador exige que a citação contenha o fragmento do meio e palavras
do lado escolhido, sem atravessar o efeito. Rótulo bruto, citação validada
e confronto retrospectivo com revisão local são medidas separadas. Nenhum
dos estados aprova produção ou efeito.

Painel v22 com dez exemplos novos (4 sujeitos, 4 objetos, 2 ambíguos)
foi escrito antes da primeira consulta. SHA-256 das entradas:
`DDCC794F8395141A6E9C124A05B29B9A545E641AFA332D897AE9938C86C6F871`;
revisão manual local, não autenticada:
`8C18C0B7DE70B27A4D021CEEB4FFB14E1D707C7B7A517522D2D973DD64D42620`.
Na **primeira execução**, só 3/10 julgamentos passaram pela guarda de
citação, todos do grupo `sujeito_seguinte`. A primeira versão da sonda não
preservava a resposta bruta rejeitada, portanto não se atribui placar de
rótulo bruto àquela primeira execução.

Depois de adicionar observabilidade sem mudar o prompt nem o validador,
uma **repetição diagnóstica, não novo holdout**, mostrou 5/10 rótulos brutos
alinhados à revisão: 4/4 sujeitos, 0/4 objetos, 1/2 ambíguos. Os quatro
objetos foram rotulados `sujeito_seguinte`; algumas citações omitiram o
fragmento do meio e citaram apenas a condição seguinte. Só 3/10 respostas
continuaram ancoradas e alinhadas. Assim, a primeira fronteira RED não é
apenas a forma da citação: este contrato de pergunta também erra a relação
nos controles de objeto. Isso **não prova incapacidade geral do Qwen**;
falsifica este contrato como verificador independente confiável. Não usar
concordância com spaCy como autorização. P01 permanece em sombra.

No **mesmo v22 já visto**, uma segunda formulação de desenvolvimento mostrou
as duas partições literais completas e perguntou só pelo rótulo, duas vezes
com a ordem invertida. O Qwen devolveu `objeto_anterior` em **20/20 chamadas**:
as ordens concordaram nos dez casos, mas apenas 4/10 rótulos coincidiram
com a revisão local (0/4 sujeitos, 4/4 objetos, 0/2 ambíguos). Este painel
não é holdout para a segunda formulação. A estabilidade à ordem não corrige
o viés de rótulo; repetir o mesmo modelo não cria evidência independente.
Nenhum desses resultados altera a decisão canônica ou a Laylay em produção.
Próxima hipótese exige **fonte de evidência diferente**, não mais ajustes
do prompt sobre v22.

Uma tentativa de controle com outra família já instalada, `gemma4:26b`,
usando o mesmo contrato de citação, **não gerou classificação**: a primeira
consulta atingiu o `ReadTimeout` de 90 segundos do cliente. As nove consultas
restantes foram interrompidas; o modelo experimental foi descarregado. Esse
resultado mede disponibilidade/custo do avaliador nesta máquina, não sua
qualidade semântica. Não contar como acerto, erro de relação ou confirmação
independente. A próxima fonte deve ser operacionalmente viável e aferida em
painel inédito, mantendo o gabarito fora da entrada. Até lá, a fronteira
semântica segue RED e a abstenção continua sendo o comportamento seguro.

Para testar um modelo externo sem instalar outro modelo local, foi preparado
`scripts/analises/sonda_openrouter_fronteira.py`. Ele faz **uma consulta por
execução** usando chave local, JSON Schema e um caso sintético v22, sem mandar
gabarito ou parse e sem conectar ao runtime. O v22 aqui serve apenas para
verificar transporte, formato e comportamento inicial de outra família;
permanece um painel de desenvolvimento já visto. Após comprovar a chamada,
congelar um novo painel cego antes de qualquer placar comparativo.

Primeira chamada real da sonda OpenRouter: o carregador de credencial DPAPI
já existente na Laylay forneceu a chave sem digitação e sem exibi-la. Com
`google/gemini-3.1-flash-lite`, um caso sintético do v22
(`ENTREGADOR_PEDIDO_CLIENTE_GERENTE`) retornou `sujeito_seguinte` e citação
literal validada. O recibo da API informou 348 tokens de entrada, 25 de
saída e custo de US$ 0,0001245. Isto prova transporte e guarda de formato
para **um** caso; não mede taxa de acerto, não é holdout e não libera P01.

### Painel cego local v23 congelado antes da API (28/09)

Doze fontes sintéticas novas: 4 com fragmento intermediário como sujeito
seguinte, 4 como objeto anterior e 4 com as duas leituras plausíveis.
Todas passaram pela guarda lexical plana antes da primeira consulta. A
revisão é manual e local, mantida em arquivo separado, e **não** é enviada ao
modelo. O contrato de citação e o prompt são os mesmos já usados no v22;
nenhum ajuste será feito durante a primeira medição. SHA-256 das entradas:
`2903EFF673E92D13139F5D3F9CD0F1E3094005FF6A21BCED129138D9100FBB1E`;
SHA-256 da revisão local:
`AA4A5BA0FA1EAFDDE70E6CABDE1DDC9091E70D673FD772D9D9B43801017BD4A0`.
Primeiro medir rótulo bruto, citação validada e abstinência separadamente;
nenhuma coincidência com essa revisão local autoriza integração ou fala.

**Auditoria do gabarito após as 12 chamadas:** os oito casos definidos do
v23 receberam o rótulo esperado com citação válida (4/4 sujeitos e 4/4
objetos). Porém a revisão local dos quatro supostos ambíguos estava errada:
na partição `objeto_anterior`, o último sujeito singular ficava com verbo
plural (`o zagueiro correrem`, `o táxi passarem`, `o javali fugirem`,
`a filha saírem`). Esse grupo **não mede abstenção**; suas quatro propostas
não entram no denominador de qualidade semântica. Uma das quatro citações
também falhou na guarda literal. O custo total observado nas 12 chamadas
foi US$ 0,001586. Não alterar os arquivos v23 após a consulta nem
reclassificar seus casos para fabricar um placar. A mesma falha de revisão
afeta os dois supostos ambíguos do v22 (`o cavalo correrem` e
`o helicóptero desaparecerem`); retirar qualquer conclusão anterior de
"0/2 ambíguos" como medição válida de ambiguidade.

### Contraste focado v24 após a falha da revisão

Seis casos novos/variantes foram preparados para testar apenas a abstenção:
o último sujeito agora é plural e concorda com o verbo plural em **ambas**
as partições. A revisão local registra explicitamente as duas condições
literais plausíveis em cada leitura, não somente o rótulo
`indeterminado`. Isto ainda é julgamento manual, não verdade externa; v24 é
um diagnóstico focado informado pelo erro de v23, **não** um holdout global
intocado. Antes da primeira consulta, os seis casos passaram pela guarda
lexical e o teste de duas partições literais. SHA-256 das entradas:
`46335FC48C2CF302330F84C761A5050BBBDF0680F9CE5F823DEE22B0FBDCCD29`;
SHA-256 da revisão:
`7272F78728BC890BC8F870EF7B22D59B2B0E432FA86F81DCE8F6017E7EEA2530`.
Manter o mesmo prompt, formato e modelo na primeira medição.

Medição v24 com prompt original: `google/gemini-3.1-flash-lite` escolheu
`objeto_anterior` em 6/6 casos e nenhuma abstenção; as seis citações
passaram na guarda literal. Custo observado: US$ 0,00076375. Controle de
outra família, `openai/gpt-4o-mini`, escolheu 4 sujeitos e 2 objetos, também
sem abstenção; uma das seis citações foi rejeitada. Custo observado:
US$ 0,00037395. As famílias diferem no lado preferido, mas nenhuma sinalizou
as duas leituras plausíveis. A guarda de citação só comprova origem textual,
não exclusividade semântica. Hipótese ainda não provada: o prompt original
oferece `indeterminado`, porém não define que **duas leituras plausíveis
exigem abstenção**. Não atribuir essa lacuna somente ao modelo.

### Contrato de ambiguidade explícita e painel v25

O prompt original permanece preservado para reprodução. Uma variante
experimental instrui a comparar as duas partições e retornar
`indeterminado` se ambas mantêm concordância e sentido plausível, ainda que
uma pareça mais natural; rótulo definitivo só quando a alternativa é
inviável. Ela recebe a mesma entrada literal, sem POS, parse ou revisão.
Antes de qualquer chamada com esse prompt, o v25 foi preparado com nove
casos inéditos: 3 sujeitos, 3 objetos, 3 ambíguos; as duas leituras dos
ambíguos estão registradas literalmente na revisão local separada. Todos
passaram nos testes de preparação. SHA-256 entradas:
`C8DD3B71A4D153BAA1983D2CB90113E87CD35F9652029EA3518C343C90B6F221`;
SHA-256 revisão:
`0069B68E39678951FD628CDCD8D9B376C63B438DA6F3A5DC532DA39862B66DD3`.
Primeira medição usará o mesmo Gemini, com o novo prompt fixo. O resultado
continua sendo proposta offline, não verificação factual nem fala.

Primeira medição v25 concluída sem mudar prompt ou revisão: com
`google/gemini-3.1-flash-lite`, os 3/3 sujeitos tiveram rótulo e citação
alinhados à revisão local; os 3/3 ambíguos receberam `indeterminado`;
**os 3/3 objetos definidos também receberam `indeterminado`** apesar de a
partição de sujeito criar sujeito composto com verbo singular. Custo
observado: US$ 0,00107775. Assim, a instrução explícita melhora a
abstenção nos casos ambíguos, mas perde toda a cobertura desses controles
de objeto. Não declarar ganho geral nem promover o prompt. O primeiro RED
do novo contrato é a avaliação de viabilidade **de cada partição**, em
particular concordância sujeito–verbo da alternativa descartada. Uma
citação literal da leitura escolhida e uma abstenção vazia não provam essa
avaliação. Próximo experimento: expor as duas partições com verificação
estruturada de viabilidade e uma checagem externa/conservadora de
concordância; ainda sem fala, treino, runtime ou autorização.

### Viabilidade de cada leitura isolada e contexto condicional (28/09)

`sonda_viabilidade_particoes.py` envia duas consultas isoladas: cada uma vê
**apenas sua partição** e devolve `viavel`, `inviavel` com motivo e citação
literal da condição inteira, ou `incerta`. Duas viáveis propõem ambiguidade;
uma viável e uma inviável propõem relação **para revisão**; parecer inválido,
duas inviáveis ou incerteza não viram decisão. Um RED local provou que o
agregador antes aceitava estados forjados sem validação; ele agora exige o
estado retornado pelo validador. Nenhuma proposta autoriza produção ou fala.

No v25 já visto, a primeira formulação sem frase completa deu ao Gemini
3/3 sujeitos e 3/3 ambíguos alinhados à revisão, mas só 1/3 objetos; duas
leituras de sujeito com verbo singular foram chamadas viáveis. Foram 18
consultas, custo observado US$ 0,002342. O GPT-4o mini detectou a
inviabilidade das três leituras de sujeito, porém chamou duas leituras de
objeto também inviáveis. Uma repetição mostrou que ele tratara a primeira
condição sem `Se` como erro de concordância. O parser `pt_core_news_sm`
isolado também não é árbitro confiável nesse controle: leu `aprendiz` como
`VERB` e `chegar` como infinitivo. A regra geral para sujeito composto
anteposto é plural, com exceções que exigem análise específica
([Ciberdúvidas](https://ciberduvidas.iscte-iul.pt/artigos/rubricas/idioma/concordancia-do-verbo/5015)).

O contrato experimental passou a reconstruir a frase condicional completa,
com parênteses indicando apenas a partição avaliada, sem mostrar a outra.
Nos três objetos de desenvolvimento o GPT-4o mini passou a chamar a
leitura de objeto viável e a de sujeito inviável, mas copiou os parênteses
inseridos pela sonda nas citações. RED focado levou a permitir **somente**
remover um par externo exato desses parênteses; qualquer outra edição da
citação continua rejeitada. Essa repetição sobre v25 é diagnóstico, não
holdout nem placar final.

O v26 foi congelado **antes** da primeira consulta com a versão
contextualizada: 9 frases inéditas, 3 por classe, com duas leituras literais
registradas para cada ambiguidade. SHA-256 entradas:
`68C3E8D3E0D4110CCF8B5A64A2032BD5FF7615CE778231A305FA4ED319E1537E`;
SHA-256 revisão local:
`3482D41EF10965802249DA22B357113DD6C406BF78B007A26B284FEEEF3BB9B1`.
Os testes de estrutura e partição passaram. A revisão segue manual e não
autenticada; acordo com ela ainda não libera P01.

Primeira medição v26, sem alterar entradas, revisão ou contrato: com
`openai/gpt-4o-mini` e duas chamadas isoladas por caso, 6/9 conclusões
coincidiram com a revisão local (2/3 sujeitos, 1/3 objetos, 3/3 ambíguos).
Em um sujeito e um objeto, ambas as leituras foram chamadas inviáveis e a
sonda absteve; em outro objeto, ambas foram chamadas viáveis e a sonda
propôs ambiguidade indevida. O custo observado nas 18 chamadas foi
US$ 0,0011121. Repetições **diagnósticas** de dois casos que falharam
mudaram o julgamento para o esperado; um terceiro permaneceu sem decisão.
Essas repetições não alteram o placar da primeira medição nem tornam v26
um holdout reutilizável.

Foi acrescentado controle opcional de `--temperatura` e `--semente` ao
transporte offline. Repetir um dos casos com `--temperatura 0 --semente 42`
continuou produzindo pareceres diferentes. Assim, os parâmetros enviados
não provaram reprodutibilidade neste caminho; o provedor não foi fixado e
a origem da variação permanece aberta. A primeira fronteira RED agora é a
**confiabilidade do julgamento de viabilidade**, não a seleção do rótulo
final. Citação literal demonstra origem textual, mas não comprova a
avaliação gramatical ou semântica. Próxima investigação deve obter critério
independente para essa viabilidade e medir repetibilidade sem adaptar o
gabarito aos erros. P01 continua offline/sombra; não houve treino,
integração de fala, autorização ou execução.

#### Controle de roteamento e repetibilidade (28/09)

A sonda offline passou a solicitar metadados de roteamento da OpenRouter,
registrando **por chamada** somente provedor selecionado, fingerprint,
motivo de término, ID opaco e SHA-256 do corpo do pedido (sem chave). Um RED
local confirmou a ausência anterior dessa observabilidade. Uma repetição
sem fixar rota mostrou Azure e OpenAI em chamadas do mesmo caso/modelo;
portanto, comparar apenas o ID `openai/gpt-4o-mini` não fixa o executor da
inferência. Isso era uma causa concorrente plausível, não explicação provada.
Os campos de metadados e o filtro `provider.only` seguem a
[documentação da API](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion)
e de [roteamento](https://openrouter.ai/docs/guides/routing/provider-selection).

Com `provider.only=["openai"]`, `allow_fallbacks=false`, temperatura zero e
semente 42, cinco medições diagnósticas do mesmo caso v26 produziram duas
vezes `sujeito_seguinte` e três vezes abstenção por **ambas as leituras
alegadas inviáveis**. Nas três medições com hash instrumentado, o pedido da
leitura de sujeito teve sempre SHA-256
`c34428eeaf4a7b8685dd2f5c543602c1f1eb546f6550b88f2c12be0ed3ee5f2e`;
provedor `OpenAI`, fingerprint `fp_2e30314e0f` e término `stop` também
permaneceram iguais. A leitura de objeto foi sempre alegada inviável; a
leitura de sujeito alternou entre viável e inviável. Assim, **troca de
provedor, diferença de corpo enviado e truncamento aparente não explicam
sozinhos a variação observada**. Isto não prova qual mecanismo interno
produziu a diferença, nem que a semente foi efetivamente honrada pelo
serviço. Os cinco usos são repetições de desenvolvimento, nunca cinco casos
independentes ou novo placar v26.

Contrato que falta: uma alegação isolada do modelo sobre concordância não
é evidência suficiente para declarar uma partição inviável. Um gate de
consistência pode rejeitar divergência, mas repetição concordante tampouco
é verificação gramatical independente. A próxima prova precisa de controle
morfossintático com cobertura e limites explícitos, sem converter ausência
de veto em viabilidade provada. Nenhum resultado foi promovido ao runtime.

#### Primeira contraprova independente e unilateral (28/09)

RED de arquitetura: no caso de sujeito composto `o técnico e a coordenadora
entrarem`, um parecer `inviavel/concordancia` com citação literal era aceito;
se a outra leitura viesse `viavel`, a sonda propunha erroneamente
`objeto_anterior`. O problema não era a literalidade nem o agregador: era a
falta de checagem do **motivo alegado** antes de usá-lo para excluir uma
leitura. A fonte linguística consultada confirma que sujeito composto
anteposto com dois grupos nominais coordenados normalmente concorda no plural,
com exceções contextuais
([Ciberdúvidas](https://ciberduvidas.iscte-iul.pt/consultorio/perguntas/a-sintaxe-de-roma-e-pavia-nao-se-fizeram-num-dia/37778));
formas regulares em `-arem`, `-erem`, `-irem` marcam a terceira pessoa plural
do futuro do conjuntivo/subjuntivo
([conjugação](https://www.conjugacao.com.br/futuro-do-subjuntivo/)).

O módulo superficial já existente recebeu um sinal **estreito**: dois grupos
curtos `artigo + palavra`, unidos por `e`, seguidos de uma forma com marca
plural explícita. `saírem` também é reconhecido; formas irregulares, grupos
longos, pontuação adicional e morfologia incerta ficam fora do alcance. Se
o modelo disser que essa **mesma segunda condição** é inviável por
`concordancia`, o parecer passa a `conflito_concordancia_superficial`, sem
`viabilidade`, e o agregador se abstém. O sinal não transforma a leitura em
`viavel`, não refuta alegações semânticas e não aprova fala ou efeito. Ele é
independente do parecer do modelo, mas ainda depende da partição literal
preparada pela sonda; não identifica a estrutura sintática em frases gerais.

REDs focados confirmaram o falso rótulo e a ausência do sinal; após o
candidato mínimo, os controles em quatro domínios, verbo singular, forma
irregular, citação parentetizada, motivo semântico e abstenção passaram.
O conjunto de sondas/testes relacionados passou em **290 testes**. Isso é
GREEN local/offline, não medição nova do modelo nem validação do runtime.
O v26 congelado e seu placar de primeira consulta não foram alterados.
Ainda falta um verificador morfossintático mais abrangente e aferição cega;
ausência desse sinal não prova erro nem correção de concordância.

#### Índice morfológico e painel pré-registrado (28/09, antes da aferição)

Para não depender de um segundo modelo como árbitro, foi isolado o
[PortiLexicon-UD](https://github.com/LuceleneL/PortiLexicon-UD), léxico de
português brasileiro com forma, lema e traços UD. A fonte `VERB.tsv` de
71.016.248 bytes está fixada no commit
`315e063da1f89c89e2097c6e72428ebefb9ab1d1`, SHA-256
`3c3ccbf94e0c6e7a1673722f6adceb36e75fde7a70fd5a1dc0edc5b7bcc69342`.
Um gerador fail-closed extraiu somente formas de 3ª pessoa do futuro do
subjuntivo e número singular/plural: índice local de 367.990 bytes, SHA-256
`a9a48993a3cfc8b2f957cf1a1d2315a5401e9b1d726ffeba08df7df00c6f35d6`.
O recurso mantém o aviso da [licença MIT da fonte](https://github.com/LuceleneL/PortiLexicon-UD/blob/main/LICENSE).
Fonte ausente ou hash diferente não deve virar evidência gramatical.

Um painel **novo para esta verificação morfológica** foi separado em entradas
e revisão local, com 21 condições curtas: 8 convergentes, 8 divergentes e
5 fora de escopo. SHA-256 das entradas, antes da primeira aferição:
`E7A2E6CEA0EB8FEB9FAECBBCB6E1DEAC1FD2739F7E89032F33B956B962549D5B`;
SHA-256 da revisão:
`85C33AE101C573D671F78575672DAF700AF5A636623204DE7F787CC4FAF5B087`.
Esta revisão é manual e não autenticada. O painel mede apenas a checagem
local de número em estruturas curtas, não a escolha semântica da partição,
qualidade de ensino, fala ou runtime. Não alterar entradas ou revisão após
o primeiro resultado para fabricar um placar.

Primeira aferição **após o congelamento**: 21/21 alinhados à revisão local,
distribuídos em 8 `numero_convergente`, 8 `numero_divergente` e 5
`sem_analise`. Isso não é acurácia geral: os exemplos foram compostos
manualmente para o formato estreito e a revisão não é independente de um
linguista. Um `pt_core_news_md` consultado isoladamente, sem instalação na
Laylay, marcou `entrarem` com `Number=Plur`, mas `VerbForm=Inf`; acertar
número no controle não o torna árbitro da estrutura completa. O índice
lexical confirma formas como `forem` (antes fora da regra por sufixo) e
recusa uma forma inventada terminada em `-arem`; também não decide qual
palavra é verbo no contexto sem a hipótese estrutural curta.

Contrato de integração **somente na sonda offline**: para aceitar uma
alegação do modelo `inviavel/concordancia`, o trecho literal citado precisa
ter `numero_divergente` no verificador. `numero_convergente` produz conflito
e abstenção; forma desconhecida, estrutura longa, índice ausente ou hash
corrompido produzem `concordancia_nao_corroborada` e abstenção. Mesmo uma
divergência não é prova definitiva de inviabilidade, por exceções sintáticas
e semânticas; continua `revisao_pendente`. Alegações `inviavel/semantica`
não são verificadas por esse índice e seguem um risco separado. Testes
focados e de composição protegem sucesso provisório, falha, recurso ausente
e forma inventada. O painel v26 e sua primeira medição permanecem intactos.
Nenhum treino, prompt permanente, fala, executor ou runtime foi alterado.

### P01: alegacao semantica isolada e nova afericao integral (28/09)

Primeira fronteira RED reproduzida: uma resposta `inviavel/semantica` com
citacao literal da condicao era aceita como exclusao de leitura, apesar de a
citacao provar apenas alinhamento textual, nao impossibilidade semantica.
Isso permitia uma relacao provisoria com um unico parecer do modelo, sem
corroboracao independente. O contrato offline agora marca essa alegacao como
`semantica_nao_corroborada` e se abstem; nao altera a aceitacao provisoria
de divergencia morfologica corroborada. Nenhuma dessas propostas autoriza
fala, treino, producao ou efeito.

Painel v27 preparado para medir **a decisao completa** depois desse veto,
com nove frases novas e revisao manual local previa (3 por classe), antes
da primeira consulta. SHA-256 das entradas:
`7BCC9924A20A43BF169DE26B0312EE573450A2F6DDD0AC5A0C77EBDCC9230F56`;
SHA-256 da revisao:
`E4076615B49EC08627E1FF0716F2C3E41E00FF3401072921C6F1ECC77EFDC546`.
O painel nao e validacao linguistica externa nem prova de qualidade de ensino;
nao alterar entradas/revisao para melhorar o placar apos a primeira medicao.

Primeira medicao v27: `openai/gpt-4o-mini`, provedor OpenAI fixo, temperatura
0, semente 42, duas consultas isoladas por frase, 18 consultas no total,
custo observado US$ 0,0011091. Resultado da **versao anterior ao veto de
viabilidade**: 6 propostas alinhadas a revisao manual local, 1 proposta
divergente e 2 abstencoes. As duas abstencoes vieram de citacoes que copiaram
as duas condicoes juntas, em vez da condicao exigida. Nenhuma alegacao
`inviavel/semantica` apareceu nessa rodada; o veto semantico teve prova
local, mas nao medicao de campo nesse painel. A proposta divergente foi
`JARDINEIRO_ROSEIRA_SAMAMBAIA_VIZINHO`: o modelo marcou como viavel a
condicao `a samambaia e o vizinho aparecer`; a sonda entao propos
ambiguidade, enquanto a revisao previa marcava `objeto_anterior`.

Nova primeira fronteira RED: o verificador de numero era chamado para
`inviavel/concordancia`, mas nao para `viavel/nenhum`. A mesma condicao curta
recebe `numero_divergente` no indice independente. Agora esse conflito
produz `conflito_viabilidade_superficial` e abstenção, sem converter
divergencia em prova de uma leitura oposta. Repeticao **diagnostica apenas
desse caso ja visto**, com o mesmo modelo/parametros, devolveu a mesma
resposta bruta do modelo e terminou em abstenção. Isso nao e novo holdout
nem melhora retroativa do placar 6/9 da primeira medicao. Regressivos
offline da familia de sondas: 292 passaram. Runtime, fala final e qualidade
de ensino seguem sem validacao; P01 continua aberta e fora de producao.

### P01: painel v28 congelado para o contrato corrigido (28/09)

Painel novo de 12 frases, quatro por classe, com revisao manual local
registrada **antes** de qualquer consulta ao modelo. Todas as entradas
preparam duas particoes literais; os controles ambíguos preservam as duas
leituras plausiveis. SHA-256 das entradas:
`D3FAA3B50C0FD5CFD4F47A04F4FBBA205825000C1B1E357948400F3CB3DAEC49`;
SHA-256 da revisao:
`B8626731E7EDCE3D94D17F9549CCA6E869E67ACBF4A33671520531C6D287BFC8`.
A revisao nao e externa nem autenticada. Nao ajustar o painel apos a
primeira medicao para melhorar placar; resultados posteriores nele sao
diagnosticos, nao novos holdouts.

Primeira medicao v28 com `openai/gpt-4o-mini`, provedor OpenAI fixo,
temperatura 0 e semente 42: 24 consultas isoladas; custo observado
US$ 0,0014973. Das 12 frases, 8 produziram proposta alinhada a revisao
manual local, 4 se abstiveram e nenhuma proposta emitida divergiu. Por
classe, foram 1/4 de sujeito seguinte, 3/4 de objeto anterior e 4/4
ambiguidades com proposta alinhada. As abstencoes vieram de duas citacoes
com as duas condicoes em vez de uma, uma alegacao de concordancia
contradita pelo indice morfologico e uma alegacao semantica literal sem
corroboracao. Portanto, houve ganho de seguranca no painel, **nao prova
de acuracia geral ou de cobertura suficiente**. O caso semantico demonstra
o veto no modelo real; continua sem verificador semantico independente.

Medição separada do **modelo local configurado pela Laylay**,
`qwen3:4b-instruct`, no mesmo painel v28 ja congelado e sem mudar o
contrato: 12/12 abstencoes, nenhuma proposta. Predominaram respostas
`inviavel/semantica` que citavam a frase completa, mesmo em controles
plausiveis; houve tambem pares incoerentes de rotulo/motivo e um erro de
concordancia alegado em sujeito composto plural que o indice contradisse.
Isto comprova falha de cobertura e de formato **na sonda**, nao do ensino
inteiro da Laylay. Como diagnostico no painel ja visto, um prompt que
explicita que nao se deve julgar se a condicao causa o efeito e exige
citacao igual a um item da lista produziu ambiguidade plausivel em um
controle; em um caso de sujeito e um de objeto, deu `viavel` nas duas
leituras, e o veto morfologico gerou abstenção. Esses tres replays nao
sao uma nova medicao nem justificam trocar o prompt sem novo painel.

### P01: sonda do ensino no runtime real, separada da particao (28/09)

Com a Laylay fechada, rodei o roteiro benigno de quatro turnos
`roteiro_ensino_cenario_sensor_sombra.py` pelo composition root real,
capturando o transporte em
`resultados_testes/transporte_evidencia-20260928-112356-291082` e a
conversa em
`resultados_testes/roteiro_ensino_cenario_sensor_sombra-20260928-112358-488897`.
Modelo local `qwen3:4b-instruct`, IoT simulado, Gmail sem credenciais,
microfone e voz desativados. O roteiro registrou 3 aprovacoes, 0 falhas
deterministicas e 1 alerta; esse placar **nao mede verdade didatica**.

No turno da leitura isolada, a fala entregue afirmou que 15% era
"bastante seco". Sem calibracao, tipo de solo ou politica de interpretacao,
essa qualidade nao decorre apenas do numero, mesmo com o sensor do solo
explicitado. No turno final, a inferencia condicional central foi coerente
com a regra fornecida: 15% < 20% e, no cenario hipotetico, a bomba deve
ligar. A fala tambem acrescentou que a rega manteria o solo umido; isso
nao e medicao observada. Nenhum comando operacional foi executado. A
auditoria de ensino em sombra marcou 16 segmentos, 14 sem ancora literal
e 0 comparacoes aritmeticas confirmadas; ela nao alterou a resposta.

Primeira fronteira para a alegacao de secura: a geracao HTTP ja continha
"bastante seco"; a fala entregue a preservou. O payload final transportou
os dois sensores, o foco explicito no sensor do solo, 15% e o limiar de
20%; ausencia desses dados no transporte nao explica a afirmacao. A sonda
de particoes v28 nao e importada pelo runtime e nao participou da fala.
Portanto, a melhoria offline nao corrige a qualidade factual de ensino.
Falta um verificador de alegacoes/derivacoes com evidencias e um teste do
texto final entregue antes de qualquer promocao; audio fisico nao foi
testado nesta execucao.

### P01: derivacao qualitativa tipada em sonda (28/09)

O RED foi reproduzido no contrato offline: uma proposta podia citar
`15% de umidade` e ainda deixar `Isso e bastante seco` apenas como
`revisao_semantica_pendente`, sem identificar a falta especifica do
criterio de classificacao. O contrato agora reconhece uma derivacao
**proposta** `qualificacao_qualitativa` e distingue valor/rotulo sem ancora,
criterio ausente e criterio apenas citado. Mesmo com criterio citado,
`condicoes_verificadas=False` e `aprovado_para_compor=False`: nem a LLM nem
uma citacao autenticam a relacao semantica. A sonda de propostas pode
encaminhar essa derivacao ao verificador; nao foi conectada a fala/runtime.

Painel novo de oito falas sinteticas, com revisao manual local registrada
antes de consultar o Qwen: quatro qualificacoes sem criterio, duas com
criterio textual e dois controles sem qualificacao. Entradas SHA-256:
`6549DCDB93AE5E7EB7DDC532CE84A018B5388A6CE1925A401FDED2F64650CCDE`;
revisao SHA-256:
`37A7C929AC1FF0336FE49C9EF79C10C4FC8D36A22CA04BC34D2B113F061D0A7D`.
Nao alterar painel/revisao para melhorar placar depois da primeira medicao.

Primeira medicao do painel qualitativo v1 com `qwen3:4b-instruct` local:
8/8 respostas trouxeram o objeto opcional `derivacao` em segmentos que nao
eram qualificacoes, inclusive o controle literal de programacao; os campos
vieram frequentemente vazios, nao numericos ou inventados. Nenhum caso
demonstrou uma derivacao tipada suficiente para verificar a qualificacao;
os controles tambem receberam `derivacao_invalida`. A validacao externa
recusou essas propostas, mas a cobertura util da sonda combinada foi zero.
Nao e falha do texto-fonte nem motivo para afrouxar valores/rotulos. A
primeira fronteira RED da nova interface e misturar identificacao de
qualificador com extracao de evidencias num campo opcional do mesmo schema.
O v1 permanece como diagnostico visto; mudar a interface exige painel novo.

### P01: triagem qualitativa separada, painel v2 congelado (28/09)

A classificacao de segmentos foi separada da extracao de derivacao. A
resposta do modelo continua sendo somente uma proposta; o verificador
local exige indices exatos e rotulo literal, e nao aprova composicao nem
efeito. No replay diagnostico do v1 ja visto, o Qwen marcou tambem os
controles como qualificacoes e produziu rotulos invalidos. Duas sondas
diagnosticas com `openai/gpt-4o-mini` no mesmo v1 identificaram o rotulo
`seco` e deixaram um controle de programacao como `outro`; isto nao e
holdout nem comprova generalizacao.

O painel v2 foi escrito e revisado manualmente antes de qualquer chamada
de modelo: dez casos sinteticos, cinco com qualificacao e cinco controles.
Entradas SHA-256:
`B782593CA24CEBE1B79E8BC4887303E30DF97C782EC7934536FEE8790BBD7BC6`;
revisao SHA-256:
`ABCF803C75566F9D350AF6DCD5CAD2555387CA36CB2873DDF8A53E80F94723BB`.
Nao alterar entradas ou revisao apos a primeira medicao. A proxima prova
e medir classificacao e rejeicao de controles sem transformar esse painel
offline em autorizacao de fala.

Primeira medicao do v2 congelado: `openai/gpt-4o-mini`, provedor OpenAI
fixo no OpenRouter, `temperature=0`, `seed=42`, uma chamada por caso.
As dez respostas respeitaram os indices e rotulos literais; os cinco
casos com qualificacao tiveram o rotulo revisado (`fraca`, `baixo`,
`insuficiente`, `segura`, `quente`) e os cinco controles ficaram sem
candidato. Alinhamento com a revisao manual local: 10/10 casos; custo
observado total US$ 0,0006195. O painel e sintetico e pequeno, a revisao
nao e fonte independente de verdade, e a interface nao verifica se um
criterio realmente implica o rotulo. Logo, esse resultado sustenta apenas
que separar triagem de extracao e promissor para a sonda offline. Nao
promover a verificador final, fala ou runtime com base nesse placar.

Comparacao na primeira medicao local do mesmo v2 com
`qwen3:4b-instruct`: 9/10 propostas inteiras foram rejeitadas por
rotulo ausente, nao literal ou tipo incorreto; a unica proposta que
passou pela conferencia formal (`RESERVATORIO_BAIXO`) marcou tambem o
segmento literal `12 L.` como qualificacao. Portanto, 0/10 casos
alinharam com a revisao manual local. O transporte retornou JSON, mas
marcar todo segmento como qualitativo impediu uma triagem util. O
verificador recusou as propostas sem aprovar fala. Isso falsifica a
hipotese de que separar em duas chamadas, por si so, torna este Qwen
confiavel nessa tarefa. Nao alterar o painel ou afrouxar a validacao
para melhorar a contagem.

Dois REDs adicionais de robustez foram reproduzidos: `tipo` como lista
na proposta de triagem e `origem` como lista numa fonte de criterio
causavam `TypeError`. Ambos agora falham fechados com estados invalidos,
sem aprovar composicao. Os testes focados passaram; ainda falta prova
de adequacao semantica e do texto final no runtime real.

### P01: criterio numerico e fala final historica (28/09)

Base desta investigacao: HEAD `a078360e6b694c37f981e8be11f1470dd14571d5`,
branch `main`, worktree ja suja por trabalhos paralelos; nenhuma mudanca de
producao ou commit nesta etapa. A primeira divergencia no contrato offline
era precisa: `15%` podia ser associado ao rotulo `seco` citando `abaixo de
10% e seco`, pois o verificador apenas encontrava o rotulo literal e nao
conferia a desigualdade. Controles falsificaram explicacoes concorrentes:
a medida, a unidade e a citacao estavam presentes e formalmente validas;
o erro era a aplicacao da regra citada a medida observada.

O verificador de propostas agora distingue, em criterios numericos
simples e univocos citados, limiar nao satisfeito, unidade divergente,
negacao/multiplos limiares indeterminados e comparacao numerica
satisfeita. Isso vale tambem para igualdade na fronteira (`abaixo de`
estrito versus `ate` inclusivo) e para bateria em volts, alem do solo
em porcentagem. Uma comparacao satisfeita permanece
`criterio_numerico_satisfeito_relacao_pendente`: nao autentica se o
criterio textual realmente define o rotulo, se fala do mesmo referente,
nem se a medicao e verdadeira. Nenhum estado aprova composicao ou efeito.

Na auditoria do texto final historico do cenario dos sensores, uma
sonda manual inicialmente transmitiu acentos como `?` pelo pipe do
PowerShell. Isso gerou 21 segmentos artificiais e resposta incompleta;
elevar o limite de tokens nao corrigiu porque a premissa de entrada
estava errada. A mudanca experimental de limite foi retirada. Lendo
diretamente `conversa.md` em UTF-8, a resposta final tem 16 segmentos.
O avaliador externo na sonda offline devolveu os 16 indices e apontou
`seco` e `umido` como candidatos qualitativos. Isso e evidencia de
localizacao no texto entregue, nao prova de que essas alegacoes sao
corretas. A regra do usuario (`abaixo de 20% liga a bomba`) nao declara
que qualquer leitura abaixo desse limite seja classificada como solo
seco, nem que a bomba efetivamente mantera o solo umido. O texto final
permanece sem validacao semantica e nenhuma nova execucao do runtime
foi feita nesta etapa.

REDs dos limiares foram observados antes do candidato; 55 testes
focados passaram depois. Proximo contrato em aberto: obter/validar de
forma independente a relacao entre criterio, rotulo e referente,
inclusive condicoes compostas e fonte de verdade, e entao medir nova
fala no runtime real sem usar a triagem como autorizacao automatica.

### P01: vinculo tipado entre medida, referente e criterio (28/09)

Foi criado no grafo didatico offline um conferidor de encadeamento de
qualificacao que reutiliza o validador estrutural, a auditoria de
vinculos literais e o sinal conservador de direcao condicional. Ele
exige fonte/escopo validos, regra de uma unica condicao suficiente,
mesmo referente/atributo/unidade entre premissa e condicao, efeito no
mesmo referente, rotulo igual ao efeito, citacoes literais coerentes e
comparacao numerica verdadeira. Caso contrario retorna estados de
divergencia ou pendencia, nunca aprova fala/efeito. A relacao semantica
entre texto da regra e efeito permanece nao verificada, mesmo no caso
numericamente satisfeito. O mecanismo nao foi ligado ao runtime.

REDs reproduzidos: o grafo ancorado isolado nao vinculava a medida de
15% ao referente correto, nao impedia usar a regra de ligar a bomba
como criterio para o rotulo `seco`, nem confrontava uma proposta de
`condicoes_suficientes` com uma fonte que dizia `apenas se`. O candidato
falha fechado nesses casos. Um controle de bateria/volts prova que o
contrato nao depende do caso especifico de solo; entradas tipadas
malformadas deixam de gerar `TypeError` no grafo. Os resultados ainda
sao somente estruturais/aritmeticos e nao autenticam a proposicao da
LLM.

Nova sonda no runtime real, com `qwen3:4b-instruct` local, IoT simulado,
Gmail sem credenciais, microfone/voz desativados e sem comando
operacional: `resultados_testes/roteiro_ensino_cenario_sensor_sombra-20260928-121302-583875`
e transporte `resultados_testes/transporte_evidencia-20260928-121301-464453`.
O roteiro marcou 2 aprovacoes, 0 falhas deterministicas e 2 alertas,
mas esse placar nao representa verdade didatica. A primeira fala ja
inventou diferencas entre umidade do solo e do ar; no turno da leitura
isolada disse que 15% era `bem baixo`/`quase seco`; na explicacao final,
`seco demais` e `a planta precisa de agua`. As afirmacoes constavam na
geracao HTTP bruta e sobreviveram ate a fala entregue. Logo, a primeira
fronteira RED da fala continua na geracao de inferencias sem criterio;
o verificador atual nao as barrou. A auditoria em sombra marcou 13
segmentos, todos sem ancora literal, mas nao possui poder de veto.
Esta sonda persistiu os artefatos de teste e o resumo diario normal
em `memoria/`; nenhum efeito fisico foi pedido ou confirmado.
Regressao offline ampliada: 237 testes passaram, `py_compile` e
`git diff --check` sem erros; isso nao equivale a GREEN da fala real.

Proxima fronteira: produtor independente e confiavel de regra tipada
(ou abstencao explicita quando so ha medida), com revisao da relacao
regra→rotulo e da identidade da fonte; depois um controle do texto
final integrado em sombra no composition root. Nao promover ao fluxo
de publicacao com base neste GREEN offline, nem mascarar a geracao
inadequada por fallback generico.

### P01: autoria da fonte de criterio proposta (28/09)

Base: HEAD `a078360e6b694c37f981e8be11f1470dd14571d5`, branch
`main`, worktree ja suja; nenhuma alteracao de producao ou commit nesta
etapa. Releitura do transporte real mostrou que o quarto turno recebeu
a instrucao didatica de nao inventar causas e que a fala anterior da
assistente nao foi reenviada como fonte. Assim, falta da instrucao no
payload e contaminacao pela resposta anterior foram falsificadas para
esse turno. Uma sonda local repetiu os payloads capturados dos turnos
3 e 4 com instrucao adicional explicita sobre medida, criterio e regra
de acionamento: o Qwen ainda chamou 15% de solo seco e acrescentou
efeitos nao dados. Prompt reforcado sozinho nao e correção demonstrada.

Novo RED offline: o grafo podia trazer `FonteDidatica(origem="usuario")`
proposta pelo modelo, mas sua autoria nao era confrontada com as falas
realmente recebidas na sessao. O adaptador
`conferir_qualificacao_na_conversa` compara cada texto integral de fonte
com os ultimos turnos do usuario obtidos pelo contrato de auditoria do
runtime; rejeita fonte inventada, fala da assistente, recorte que omite
condicao, sessao expirada e pesquisa apenas autodeclarada. Sem regra
proposta, devolve abstencao explicita. So apos isso chama o conferidor
tipado existente. Regra de ligar a bomba continua incapaz de definir
o rotulo `seco`; uma regra literal de qualificacao numericamente
satisfeita continua `relacao_pendente`, nunca permissao de fala/efeito.

Os quatro REDs iniciais e um RED de fonte malformada foram reproduzidos; 76
testes focados passaram depois, `git diff --check` limpo. Este adaptador
permanece offline: nao extrai automaticamente um criterio confiavel da
linguagem, nao interpreta todas as alegacoes da resposta final, nao
autentica pesquisa externa e nao veta a fala da Laylay. A sonda real
anterior permanece RED. Proxima fronteira: produtor de propostas tipadas
com abstencao quando faltam criterio/referente, aferido em painel cego;
somente depois conectar a auditoria do texto final em sombra no runtime.

### P01: produtor de criterio tipado, painel cego v1 (28/09)

Base: HEAD `a078360e6b694c37f981e8be11f1470dd14571d5`, branch
`main`, worktree preexistente suja; nenhum arquivo de producao ou commit
alterado. A primeira fronteira RED foi reproduzida no produtor antigo:
ele ancora a condicao `abaixo de 20%` da regra `a bomba liga`, mas esse
resultado nao decide se a regra define o rotulo `solo seco`. A selecao
da fonte do criterio precisa anteceder a normalizacao de operador/valor.

Foi criado um painel sintetico de oito casos em sensores, bateria e
temperatura, com revisao separada do payload do modelo. Cinco casos
exigem abstencao (somente medida, regra de acao, rotulo diferente ou
referente ambiguo); tres incluem criterio textual, entre eles um
`apenas se` que nao autoriza a conclusao. O proponente local envia
somente fontes observadas, referentes tipados, medida e rotulo alvo ao
`qwen3:4b-instruct`; ele nao pode inventar uma fonte_id aceita pelo
avaliador. O avaliador monta o grafo com o texto integral do painel e
passa pelo contrato `conferir_qualificacao_na_conversa`; mesmo uma
proposta alinhada a revisao nao aprova fala, treino ou efeito.

Primeira medicao do painel v1, com `temperature=0`: **0/8 alinhamentos**.
O Qwen forçou `criterio_candidato` nos oito casos, incluindo os cinco
que exigiam abstencao; devolveu `>` para todas as fontes que diziam
`abaixo de`; no caso `apenas se`, inverteu a implicacao para suficiente.
Os oito casos permaneceram sem aprovacao para producao. Diferencas
adicionais de citacao nao alteram esse diagnostico: os erros de
abstencao, operador e direcao ja bastam. Nao ajustar a revisao ao
output, nem contar uma repeticao deste painel como novo holdout.

Um RED do proprio avaliador mostrou que igualdade com a revisao podia
ser rotulada como alinhada mesmo com grafo rejeitado. O contrato agora
exige grafo nao rejeitado antes de reportar alinhamento; outro RED
garantiu que limiares numericos sem unidade, como contagem de erros,
sejam representaveis. O painel v1 nao foi modificado apos a medicao.
Validacao: 85 testes focados, `py_compile` e `git diff --check` verdes.
Isto e apenas GREEN offline do avaliador, nao do produtor nem da fala
real. Proxima decisao arquitetural: dividir a tarefa do modelo em
selecao de fonte/abstencao e normalizacao, aferindo ambos num painel
novo; ou comparar outro produtor. Nao integrar este Qwen ao runtime.

### P01: fonte/abstencao antes de normalizacao, painel v2 (28/09)

Base: HEAD `a078360e6b694c37f981e8be11f1470dd14571d5`, branch
`main`, worktree preexistente suja. O painel v1 e seu gabarito nao
foram modificados. Novo painel v2 sintetico, nove casos em reservatorio,
motor, teste de software, pneus e carregador: cinco pedem abstencao e
quatro tem criterio explicito, inclusive `apenas se` e contagem sem
unidade. A revisao foi separada da entrada do modelo e conferida contra
o grafo antes da chamada real. Hashes SHA-256 congelados antes e iguais
depois da medicao: entradas `8C57D828858B7F814AEEC8A04B047698DB2CFC226AB0E542888725F38B314CB0`,
revisao `AC194D5F701C9D188607A4B8BCF320963FA9540720D5EAD0394C0907987BA166`.

O novo orquestrador offline chama primeiro a selecao de fonte ou
abstencao; somente fonte_id existente, rotulo literalmente presente no
texto integral e referente da medida resolvido permitem chamar a
normalizacao. Esses sinais sao necessarios, nao prova semantica. A
revisao manual afere o resultado, mas nao controla a passagem de uma
etapa a outra. A normalizacao recebe fonte integral escolhida pelo
host e nao pode trocar o fonte_id. Um RED de injecao de fonte_id extra
foi reproduzido e fechado com esquema exato; testes garantem os dois
sentidos da independencia entre gate e gabarito.

Medicao nova com `qwen3:4b-instruct`, temperatura zero: decisao binaria
de fonte/abstencao correta em **6/9** (absteve-se nos cinco negativos,
selecionou um dos quatro criterios explicitos). Contando tambem motivo
de abstencao e fonte exata, **1/9** alinhou com a revisao: as cinco
abstencoes corretas foram marcadas como `outro_indeterminado` ou
`regra_composta`, e tres criterios explicitos foram perdidos. A segunda
etapa rodou uma vez; produziu `limiar="He"` para uma regra `acima de 3`
e o grafo a rejeitou. End-to-end **0/9**; nenhuma aprovacao de fala,
treino, efeito ou integracao. Esta rodada e um holdout novo apenas para
o experimento offline, nao uma prova de ensino ou do runtime real.

Validacao: 92 testes focados verdes. Proxima fronteira: procurar um
proponente que selecione criterio e normalize limiar/direcao com
confiabilidade em casos cegos mais amplos, ou reformular a tarefa em
extracao textual ainda menor. Nao corrigir o painel v2 para elevar
placar nem promover o Qwen atual ao caminho de publicacao.

### P01: comparador externo e limite literal do verificador (28/09)

Base: mesmo HEAD `a078360e6b694c37f981e8be11f1470dd14571d5`,
branch `main`, worktree preexistente suja. O painel v2 e a revisao
congelada nao foram modificados. O orquestrador v2 recebeu uma porta
injetavel de consulta apenas para comparar outro produtor pelas mesmas
guardas; o gabarito continua fora do gate. Nenhuma integracao de runtime
ou autorizacao de fala, treino e efeito foi criada.

Em comparacao diagnostica (painel v2 ja visto pelo Qwen, portanto nao
novo holdout), `openai/gpt-4o-mini` via OpenRouter, temperatura zero,
teve resultado misto. Selecionou a fonte certa em quatro criterios
explicitos e absteve-se corretamente no caso do referente aberto, mas
escolheu a fonte de leitura em tres negativos; em outro negativo
absteve-se pelo motivo errado. A repeticao isolada do caso do motor
tambem mudou a escolha de fonte, portanto nao tratar uma chamada de
temperatura zero como determinismo comprovado. Nenhum caso demonstrou
alinhamento completo da proposta. Estes sao resultados de sonda
sintetica, nao medicao do comportamento de ensino da Laylay real.

Uma proposta do motor com operador e limiar corretos citou a regra
inteira. A primeira fronteira RED do verificador nao era o numero:
`conferir_grafo_premissas` devolvia `valor_sem_ancora_literal` porque
rejeitava a virgula da frase depois de `5 mm/s`. Depois da correcao
minima dessa guarda, a auditoria literal seguinte ainda marcava
`direcao_literal_pendente` pelo mesmo limite de pontuacao. Dois REDs
focados reproduziram ambas as fronteiras antes dos ajustes. A ancora
agora admite pontuacao apos limiar com ou sem unidade, mas continua
rejeitando valor decimal diferente e extensao da unidade. Com a citacao
integral, o grafo dos criterios positivos do painel deixa de rejeitar
a pontuacao, mas a proposta permanece divergente da revisao e sem
aprovacao para composicao. A falha real de selecao/normalizacao do
produtor nao foi corrigida por relaxamento do verificador.

Validacao: 55 testes focados e 319 regressivos didaticos verdes,
incluindo limites negativos e casos de motor/contagem em dominios
distintos; `py_compile` e `git diff --check` limpos nos arquivos
afetados. Proxima fronteira: testar a
selecao e a normalizacao em casos cegos novos, com origem fixa e
avaliacao separada; sem desempenho confiavel, manter P01 offline.

### P01: painel cego v3 congelado antes da medicao (28/09)

Base: HEAD `a078360e6b694c37f981e8be11f1470dd14571d5`, branch
`main`, worktree preexistente suja. Sem tocar o painel v2 ou o runtime,
foram escritos dez casos sinteticos novos: cinco criterios explicitos
(incluindo contagem sem unidade, `apenas se` e fonte distratora) e cinco
abstencoes (rotulo apenas na leitura, regra de acao, outro rotulo,
referente aberto e regra composta). A revisao foi feita separadamente
e cada proposta canonica passou pelo grafo sem aprovar fala ou efeito.

Antes da primeira chamada de modelo, os SHA-256 foram congelados no
loader v3: entradas `D4EAFB9DEE41E8EED47760A22DC69DF231F334558C66647D0445D654F2DAAB23`,
revisao `EFE5D80656F76932C354543E0F59FF23DE230DD586FD45E50949503293DBB61C`.
O loader recusa qualquer mudanca silenciosa. Um teste explicita dois
limites da guarda literal: ela ainda deixa passar como candidata uma
leitura que contem o rotulo e uma regra composta; isso nao e aprovacao
semantica nem autorizacao para compor resposta. Os testes do painel
e regressivos proximos somaram 50 verdes antes da medicao.

Primeira medicao cega v3, com contrato v2 inalterado: no
`qwen3:4b-instruct` local, quatro de dez selecoes alinharam fonte ou
abstencao/motivo com a revisao; no `openai/gpt-4o-mini` via OpenRouter,
provedor OpenAI fixo, `temperature=0` e `seed=42`, foram tres de dez.
Ambos ficaram em **0/10 propostas completas alinhadas**. O externo
escolheu `leitura` nos tres positivos aquario, estoque e robo; o Qwen
selecionou esses criterios, mas suas normalizacoes foram rejeitadas pelo
grafo. O externo gastou 14 chamadas, custo observado US$ 0,0011591.
Essas medidas nao sao prova de equivalencia estatistica entre modelos.

Falsificacao diagnostica sem editar o painel: ao inverter apenas a
ordem das fontes, mantendo textos, IDs e revisao, o externo passou a
selecionar `criterio` nos tres positivos. Na estufa, ainda selecionou
`leitura`, mesmo depois da inversao; portanto ha sensibilidade a
apresentacao, mas nao uma regra universal de escolher a primeira fonte.
Quantidade ou operador nao explicam a primeira falha, pois a escolha
errada ocorreu antes da segunda etapa.

Um RED exigiu que a primeira etapa receba somente IDs de fontes que
contenham literalmente o rotulo alvo. O filtro e partilhado com a
guarda estrutural existente, invariante a ordem e independente do
gabarito; o esquema JSON limita `fonte_id` a esses IDs ou vazio.
Isto e uma condicao necessaria, nunca validacao da regra. O modelo
continua vendo os textos para julgar se deve abster-se. Em repeticao
diagnostica do v3, ja exposto (nao novo holdout), Qwen e externo
passaram a selecionar `criterio` nos tres positivos. Ambos ainda
forcaram criterio em `PACOTE_ROTULO_NA_LEITURA` e
`BATERIA_REGRA_COMPOSTA`; nenhuma proposta completa alinhou nos cinco
casos repetidos. O novo contrato permanece apenas no orquestrador de
sonda offline, sem conexao com a Laylay real.

Proxima fronteira: aferir o pre-filtro em painel cego novo e separar
normalizacao de limiar/direcao da selecao do trecho literal da condicao.
Nao contar a repeticao do v3 como evidencia independente, nem promover
qualquer modelo antes de vencer os negativos semanticos e validar fala
final no runtime.

Validacao apos o pre-filtro: 326 regressivos didaticos verdes,
`py_compile` e `git diff --check` limpos; hashes do v3 iguais aos
congelados. Nenhum arquivo de runtime, executor ou treino foi alterado.

### P01: consequência da fonte não pode ser preenchida pelo rótulo desejado (28/09)

Base preservada: `a078360e6b694c37f981e8be11f1470dd14571d5`, branch
`main`, worktree compartilhada suja. Esta continuação alterou apenas o
avaliador offline, testes e documentação; não alterou `laylay.py`, rede,
treino, executor nem a frente paralela P16. Nenhum commit criado.

Primeira divergência demonstrada: `_conferir_grafo_do_caso` preenche
`efeito_valor` com o rótulo procurado e `efeito_referente_id` com o referente
da condição. A âncora antiga procurava menções na regra inteira, não exigia
que o rótulo fosse uma predicação afirmativa na consequência. Com propostas
numéricas corretas fornecidas diretamente, sem modelo nem gabarito, os casos
v4 `CIRCUITO_ACAO_COM_ROTULO` e `PORTA_EFEITO_NEGADO` chegaram a
`condicao_numerica_satisfeita_relacao_pendente`. Isso **não** era aprovação
de fala/efeito: todos os indicadores de autoridade já estavam falsos.

Falsificadas como explicação suficiente: erro exclusivo do Qwen (reprodução
sem chamada ao modelo), erro exclusivo do gabarito (não consultado) e
pontuação/operador numérico (controles mantêm os mesmos slots e mudam só a
consequência). Seis REDs canônicos cobriram ação, negação, modalidade e
ressalva; a expectativa antiga aceitava todos os seis numericamente.

Contrato: **rótulo desejado não é evidência da consequência**. O owner da
qualificação no grafo agora exige a análise da fonte integral antes da
comparação numérica. `analisar_efeito_qualificativo`, no módulo compartilhado
de sinais condicionais, preserva trecho, offsets, sujeito e predicado
literais e polaridade. A gramática superficial é intencionalmente limitada
a predicações com `é/está/fica`; extração do predicado ocorre antes de
compará-lo ao rótulo. Ações, negação, modalidade/ressalvas cobertas e
formatos não reconhecidos ficam pendentes, não são reinterpretados como
afirmações. Não é um classificador semântico universal.

A primeira regressão ampla revelou um controle legítimo com prefixo
`Neste protocolo, se ...`: o segmentador inicial não o representava.
O contrato foi ampliado para preservar esse prefixo como `escopo_literal`,
com `escopo_verificado=False`, sem remover a expectativa ou mudar o painel.
Também se testou `No modo automático`: o prefixo não vira fato observado.

Provas: **360 testes didáticos aprovados**, compilação e `git diff --check`
limpos. Replay diagnóstico das propostas canônicas do painel v4 manteve os
cinco positivos (quatro comparações satisfeitas e uma direção necessária
pendente); os dois negativos acima agora retornam
`efeito_qualificativo_pendente`, sem comparação numérica. Um gabarito que
repita a proposta errada também não contorna a guarda. Hashes congelados
v4 preservados. Não houve nova chamada ao modelo: esse replay mede o
avaliador, não ganho do Qwen e não novo holdout.

Limites e próxima fronteira: identidade do sujeito ainda não verificada,
escopo não demonstrado e semântica geral pendente. A forma `sujeito é rótulo`
não prova que esse sujeito seja o referente da medição; não transformar
substring/ID em prova. Tampouco se certificou qualidade de ensino no runtime.
Antes de integrar, preservar condição/consequência/direção separadamente na
proposta, resolver o vínculo do sujeito com evidência independente e medir
slots numéricos em painel novo. Não aumentar listas de exceções para simular
compreensão geral nem ajustar o gabarito v4 aos erros do modelo.

### P01: sujeito do efeito exige vínculo próprio, não menção na condição (28/09)

Base mantida em `a078360e6b694c37f981e8be11f1470dd14571d5`, `main`,
worktree compartilhada preservada. Nesta continuação: somente
`scripts/analises/grafo_premissas_didaticas.py`, testes e documentação;
nenhuma modificação de produção, treino ou prompt do modelo. Sem commit.

Primeira fronteira RED: depois de reconhecer uma predicação afirmativa,
`auditar_vinculos_literais` ainda localizava o referente na regra inteira.
Assim, menção na condição compensava sujeito errado na consequência. Seis
REDs canônicos confirmados sem modelo/gabarito: solo → reservatório,
bateria → bateria reserva, impressora → ventoinha da impressora,
água da cafeteira → água da chaleira, pronome sem vínculo e duas descrições
iguais com IDs diferentes. Controles conservam fonte/limiar/unidade e
mudam apenas o sujeito. Falsificadas explicações por erro exclusivo do
modelo, comparação numérica ou ausência do rótulo na consequência.

Contrato do owner da qualificação: antes de comparar numericamente,
confrontar o sujeito extraído com a **descrição completa já ancorada** de
um único referente; conservar os qualificadores. A normalização tolera
caixa, espaços e artigo definido inicial, não deriva alias de ID/grandeza
nem aceita substring. Havendo zero, vários ou outro candidato, retorna
`sujeito_efeito_pendente`. Compatibilidade retorna apenas
`sujeito_literal_compativel_revisao_pendente`; `identidade_verificada`
continua falsa, assim como autoridade para composição/efeito.

Inventariados os serviços `avaliar_referente_contextual` e
`avaliar_referencia_nominal_contextual`: resolvem candidatos em inventário
registrado com origem, cobertura e validade temporal. O painel offline não
possui esse registro; fabricar um inventário completo para satisfazer a
API falsificaria evidência. Esta guarda é confronto literal local do grafo,
não um substituto daquele resolvedor de identidade do runtime.

Regressões revelaram duas questões de evidência, não motivo para relaxar a
guarda: `_qualificacao_solo` usava tipo/âncora de sensor para representar o
solo. A fixture de controle agora identifica o ambiente, e um novo teste
preserva a falha histórica sensor≠solo. Painéis v1/v2 continuam inalterados;
`SOLO_CRITERIO_EXPLICITO` ancora `umidade do solo`, mas o efeito fala de
`solo`; `VOLUME_CRITERIO_BAIXO` ancora `volume do reservatório`, mas o efeito
usa `volume`. São equivalências não demonstradas por este contrato, não
afirmações de que as frases humanas estejam necessariamente erradas.
As expectativas dos testes passam a exigir pendência nesses dois casos;
não se alterou gabarito nem se inventou alias para recuperar o placar antigo.

Validação: **371 testes didáticos verdes**, compilação e diff-check limpos.
Além dos seis REDs: alvo realmente distinto registrado, tolerância apenas
superficial, ausência de autoridade e composição completa de `medir_caso`
com apenas o proponente controlado (seleção, auditor e grafo reais).
O gabarito repetindo a proposta errada não burla o bloqueio. Loader e hashes
v4 mantidos; cinco positivos canônicos v4 continuam aceitos para revisão.
Não houve consulta ao Qwen nem teste da Laylay em execução; portanto nenhum
ganho novo da rede foi medido e P01 não está encerrado.

Próxima fronteira: separar citações de condição/efeito e direção explícita
dos slots numéricos na proposta do modelo, mantendo as guardas independentes.
Aliases e pronomes exigirão evidência contextual própria, não mais recortes
de nomes. Escopo, identidade semântica e generalização permanecem abertos.

### P01: comparação A/B real dos slots segmentados — painel v5 (28/09)

Base permanece `a078360e6b694c37f981e8be11f1470dd14571d5`, main, worktree
compartilhada preservada. Alterados somente scripts de análise offline,
testes e documentação. Nenhuma mudança em `laylay.py`, runtime, rede de
comandos ou treino; nenhum commit. Esta é melhoria experimental do produtor,
não nova liberação da Laylay.

Contrato implementado como `normalizacao_segmentada=True` opcional em v2:
reusar `gerar_candidatos`, `analisar_marcador_condicional` e
`analisar_efeito_qualificativo`; exigir condição única e intervalos sem
sobreposição; preservar citações/offsets/consequência/direção no host. O
Qwen propõe somente referente_id, atributo, operador, limiar e unidade.
Campos extras que tentem trocar fonte, citação ou direção são recusados,
não ignorados. Guardas finais do grafo continuam ativas. O gabarito não
determina se uma chamada ocorre, e o caminho antigo continua padrão.

Diferenças experimentais explícitas: segunda entrada contém a condição
segmentada e a fonte integral, mas não a medida observada; schema reduzido
de sete para cinco campos, com prompt próprio. Portanto o A/B avalia esse
conjunto, não isola qual de suas partes explica o ganho. Nenhum número ou
unidade esperados foi injetado via gabarito.

Painel novo v5: estufa/temperatura, compressor/vibração, canal/contagem,
fonte/tensão decimal e servidor/condição necessária; quatro negativos:
outro sujeito, negação, ação e conjunção. Ordem da fonte de critério alternada.
Citações revisadas antes da coleta usam trecho completo da condição com
artigo; nenhuma comparação foi relaxada depois. Os testes antigos v4
permanecem exatos: artigo adicional pode continuar divergindo do gabarito
histórico, mesmo com vínculo estrutural ancorado.

Hashes congelados antes da primeira consulta:
- entradas: `bab9fba73c34fdbfc964da688a140ee8bed217dfe280ce879763976296958786`;
- revisão: `a4e02626b34786634405e994d47ee1a84d710bf51b78c91106a204e989b3a6b1`.

Loader recusa alteração; coleta usa arquivo exclusivo e grava cada resposta.
Ordem dos braços alternada por caso; chamadas sem histórico compartilhado.
Modelo local `qwen3:4b-instruct`, temperatura zero, sem novo treino. Artefato:
`resultados_testes/sonda_criterios_v5_ab_primeira.jsonl` (metadata inclui hash
do produtor, confirmado inalterado ao fim; 18 resultados, nove por braço).

Resultado real: **original 0/5 positivos completos; segmentada 5/5**.
O original ainda copiou regra inteira, trocou direção e devolveu limiares
como `>`, `He` e `logica`. A segmentada extraiu os cinco slots corretamente,
inclusive decimal e contagem sem unidade. O caso `apenas se` permaneceu
`direcao_implicacao_pendente`, sem inferência de suficiência.

Seleção exata: **5/9 nos dois braços**, somente os positivos. Qwen forçou
critério nos três primeiros negativos e devolveu candidato de fonte vazia
no composto. Na segmentada, negação/ação pararam antes de normalizar; sujeito
errado foi barrado pelo grafo; composto pela guarda de seleção. Não contar
esses vetos como abstenções corretas do modelo. Não houve falsa aprovação,
fala, efeito externo ou integração com a Laylay em execução.

Validação local: **392 testes didáticos aprovados**, compilação e diff-check
limpos, hashes mantidos. Regressões cobrem sobreposição/segmentação,
preservação de offsets/direção, veto antes da chamada, campos adicionais,
baseline e fluxo composto real da sonda com proponente controlado.

Limites: nove casos próximos da gramática conhecida, revisão local elaborada
junto ao experimento (não humana/independente), uma execução por braço,
sem seed fixado nem ablação individual. Não traduzir 5/5 em capacidade geral
ou qualidade de ensino final. Próxima fronteira é uma avaliação nova de
variação de construção, contexto e abstenções, sem reciclar v5 como holdout;
manter separadas qualidade do proponente, cobertura da guarda e autorização.

### P01: generalização controlada v6 — ganho parcial e RED de vigência (28/09)

Base `a078360e6b694c37f981e8be11f1470dd14571d5`, main, worktree suja
preservada. Somente runner de análise, painel, testes e documentação foram
alterados nesta etapa. Produtor v2, segmentadores, grafo e runtime permaneceram
inalterados durante a coleta. Nenhum treino, commit ou ativação.

Reuso do runner A/B v5 com `--painel 6`; v5 continua padrão, com hashes e
resultados originais preservados. V6 contém seis critérios semanticamente
válidos e seis negativos/indeterminados segundo a revisão local prévia.
Os positivos abrangem ordem invertida, limiar negativo, `somente se`,
comparador inclusivo, número por extenso e `classificado como`. Os negativos
cobrem referente aberto, pronome sem vínculo tipado, negação, ação, conjunção
e revogação em fonte posterior. Um pronome plausível para um humano não vira
identidade comprovada pelo pipeline; esse é o critério da anotação local,
não declaração de que a frase humana seja necessariamente ininteligível.

Congelados antes da primeira consulta:
- entradas: `1b9e8d4645e7423f178f09cfbf58bb5f20e636e0432ab20cbcd8c65aedf1147b`;
- revisão: `f9243521064713ee1228d298bab5bcd0b16a598d875228e5876eea95752c7392`.

Modelo `qwen3:4b-instruct`, temperatura 0, uma execução por braço/caso,
ordem dos braços alternada, sem seed fixado nem histórico entre chamadas.
Revisão local, não humana independente. Artefato bruto exclusivo:
`resultados_testes/sonda_criterios_v6_ab_primeira.jsonl`, com 24 resultados
e hash do produtor confirmado inalterado ao fim.

Resultados: original **0/6 positivos completos**, segmentada **3/6**.
Os três acertos são ordem invertida, temperatura negativa e `somente se`.
Seleção exata **5/12 em ambos**: cinco positivos selecionados, comparador
inclusivo não selecionado e nenhum negativo com abstenção correta. Não
contar os vetos do host como acertos do Qwen. Houve nove normalizações no
original e seis na segmentada.

Cobertura localizada sem mudar código/gabarito após o resultado:
- `maior ou igual`: `gerar_candidatos` lê `ou` como conjunção entre condições;
  fonte perde elegibilidade antes da normalização. Guarda útil aplicada a
  estrutura lexical equivocada, não motivo para remover a guarda global.
- `vinte`: Qwen segmentado preserva o texto em vez de normalizar `20`;
  direção numérica fica pendente. Proposta canônica `20` também falha na
  âncora atual; há limitações diferentes no produtor e no verificador.
- `classificado como`: frase válida fora da gramática superficial do efeito,
  impedindo normalização segmentada. Não alterar revisão para chamar o veto
  de sucesso e não misturar isso com a questão de validade da fonte.

Achado prioritário: `DUTO_REGRA_REVOGADA`. A seleção recebe todas as fontes,
inclusive a revogação, mas propõe a regra antiga. A segunda chamada recebe
somente a fonte escolhida; não pode recuperar a relação de revogação omitida.
O grafo recebe as fontes, porém confere observação literal, não validade da
regra. A segmentada extrai slots corretos e o grafo chega a
`condicao_numerica_satisfeita_relacao_pendente`; o gabarito marca
`forcou_criterio_ausente`. Não atribuir esse veto ao verificador independente.
Todas as flags de semântica verificada/composição/efeito permanecem falsas.

Falsificações: fornecer proposta correta diretamente, sem modelo e sem
revisão, reproduz o avanço; retirar somente a revogação produz o mesmo
resultado. Logo erro do Qwen não explica sozinho a lacuna. Não é erro de
número/unidade nem consequência da gramática de negação dentro da regra.
Contrato a construir: **registro/observação de fonte não atesta vigência**;
validade e relações de correção/substituição precisam acompanhar a seleção
antes da qualificação. Não resolver por uma lista local de palavras nem
injetar gabarito como autoridade.

RED canônico preservado sem xfail em
`scripts/tests/test_criterio_revogado_nao_fundamenta_qualificacao.py`, junto
do controle sem revogação. Validação final **399 aprovados e 1 falha esperada
pela investigação, ainda não corrigida**; compilação e diff-check limpos.
Os 398 verdes anteriores à inclusão do RED não significam suíte final verde.
Sem prova em runtime, sem falsa confirmação externa e sem promoção da rede.

Próximo passo prioritário: inventariar contratos existentes de proveniência,
contexto e validade, projetar um owner para vigência do critério e falsificar
casos de revogação ambígua, fonte errada e correção válida antes do patch.
Expandir gramática/treino depois dessa fronteira; não perder o ganho de
extração nem deixar que ele esconda o novo RED do avaliador.

### P01: contrato de vigência revisada, ainda sem interpretação automática (28/09)

Base mantida `a078360e6b694c37f981e8be11f1470dd14571d5`, main, worktree
compartilhada preservada. Inventário: `fontes_usuario_da_conversa` autentica
presença literal e limita a janela, mas usa texto truncado/deduplicado e não
revisa vigência. `memoria_confiavel` possui fatos pessoais ativos/confirmados,
não relações de validade entre regras didáticas. Reutilizou-se a validação
estrutural/conversacional do grafo; não se importou um resolver de preferências
para validar critérios externos. Nenhuma mudança nesses serviços de runtime.

Não há evidência suficiente para uma inferência universal por `revogada`:
pergunta, negação, citação e outro alvo podem conter a palavra. Também não
seria correto declarar qualquer texto posterior uma revogação. O candidato
implementado é o contrato anterior à interpretação, não um parser semântico:

- `RetratoVigencia` sela grafo inteiro, regra escolhida, escopo, textos
  integrais do usuário e ordem/repetições. Não usa resumo truncado para
  identificar o objeto revisado. Fontes precisam ser observadas integralmente.
- `RegistroVigenciaCriterios` pertence exclusivamente ao revisor confiável;
  guarda `vigente`, `revogado` ou `indeterminado`. Não recebe nem interpreta
  JSON do modelo. Escrever no registro pressupõe revisão confiável real;
  o registro não verifica sozinho se essa decisão semântica estava correta.
- Revisões conflitantes do mesmo retrato ficam pendentes. Repetição não
  reverte revogação. Novo texto/alvo/ordem requer nova revisão, sem invalidar
  automaticamente outra regra como fato nem inventar que ela foi revogada.
- `conferir_qualificacao_com_vigencia` consulta o registro e só depois chama
  o verificador existente. Mesmo com vigência revisada, direção, fonte e
  número ainda passam pelas guardas; composição e efeito continuam proibidos.
- `_conferir_grafo_do_caso(..., registro_vigencia=registro)` permite testar
  essa composição por opt-in; ausência do argumento preserva o baseline.
  Não há autoaprovação, preenchimento do registro por gabarito nem integração
  ao produtor de modelos. O teste histórico da rota automática permanece RED.

Provas: 16 testes novos do contrato cobrem revisão ausente/revogada/pendente,
conflitos, troca de alvo com mesmos IDs, JSON fabricado, owner distinto,
contexto alterado, ordem, repetição, diferenças depois de 500 caracteres e
preservação da guarda numérica. Duas provas adicionais usam a composição da
sonda histórica: registro vazio e registro fabricado não deixam avançar.
Os testes registram decisões sintéticas explicitamente; não demonstram que
um revisor automático consegue interpretar as frases. Perguntas/negações/
outro alvo causam necessidade de revisar o retrato, **não** `criterio_revogado`.

Validação: **417 testes aprovados e 1 RED original aberto**, sem xfail nem
mudança da expectativa. Compilação e diff-check limpos. Produção/runtime,
treino, prompts, dados congelados e modelo não foram alterados ou executados.
Arquivos de análise: novo contrato e opção no construtor da sonda v1;
testes/documentação atualizados; nenhum commit.

Próxima fronteira ainda necessária: conectar um owner confiável de revisão
de relações entre fontes a propostas contextualizadas, preservando evidência,
alvo e autoridade. Medir relações ambíguas antes de usar o registro no fluxo
automático. Não exigir clique humano por turno no produto sem decisão de UX,
nem usar a declaração `vigente=True` da própria LLM como revisão independente.
O veto opt-in sem registro é seguro, mas não equivale a correção funcional
completa da revogação. Raiz continua parcial e explicitamente aberta.

### P01: correção do caminho automático — contexto posterior não pode sumir (28/09)

Base permanece `a078360e6b694c37f981e8be11f1470dd14571d5`, main, worktree
preservada. Investigação confirmou primeira transição incorreta no avaliador:
contexto observado integral → seleção/ancoragem da regra → nenhuma obrigação
de conferir as falas posteriores → comparação numérica. Falsificadas falha
exclusiva do Qwen/gabarito e causa numérica pelo RED sem modelo e pelo controle
que remove só a revogação. Não modificar dados ou expectativas para esconder
a diferença entre regra observada e regra vigente.

Contrato mínimo compartilhado implementado em `conferir_contexto_criterio`,
ligado por padrão a `conferir_qualificacao_na_conversa`: usar as falas reais
do usuário em ordem, com conteúdo integral, não a ordem/conteúdo escolhidos
pelo proponente. Depois da primeira ocorrência da regra selecionada, falas
não conferidas deixam o critério pendente antes da comparação. Repetição da
regra não apaga uma alteração intermediária; omitir a revogação da lista
proposta de fontes não omite a fala observada. Assistente não revoga fonte
do usuário. Falha estrutural anterior continua reportada como `grafo_invalido`,
não mascarada por erro de snapshot.

Sem revisão externa, só passa como cobertura posterior uma observação
numérica integral da premissa selecionada, na superfície estreita
`[artigo] [sensor de] atributo foi/mediu/leu/marcou valor unidade`. Atributo,
valor e unidade são confrontados com a premissa; texto extra ou ressalva
não passa por estar incluído numa citação longa. Esta gramática é de cobertura
de leitura, não lista de palavras revogadoras nem resolvedor de intenção.
Formas fora dela permanecem pendentes. O registro explícito já implementado
pode revisar o snapshot inteiro para resolver contexto adicional, mas nunca
é preenchido pela própria proposta ou pelo gabarito automaticamente.

Oito REDs confirmados antes do patch: original, seis variantes de contexto
e revogação escondida em citação de leitura. Pergunta, negação, citação e
outro alvo exigem revisão; **não** recebem `criterio_revogado` por token.
Cinco provas adicionais cobrem omissão pelo proponente em dois domínios,
repetição após alteração, ordem falsa de fontes e fala da assistente.
Regressões do registro comprovam que uma revisão externa pode liberar
contexto adicional sem contornar guardas numéricas.

Resultados: **431 testes didáticos aprovados**, sem xfail/RED restante nessa
seleção, compilação e diff-check limpos. Repetição diagnóstica real local com
`qwen3:4b-instruct` em três casos v6, mesmo produtor segmentado:
- câmara negativa: proposta alinhada; comparação satisfeita, sem autorização;
- rotor `somente se`: proposta alinhada; direção necessária continua pendente;
- duto revogado: modelo ainda seleciona regra antiga e extrai slots; grafo
  agora retorna `contexto_criterio_pendente`, comparação falsa. O confronto
  posterior continua `forcou_criterio_ausente`: veto não é acerto do modelo.

Essas três chamadas foram diagnósticas, não novo holdout. Coleta v6 original
e hashes dos painéis preservados. A evidência pós-patch ficou no stdout da
sonda desta sessão; não sobrescreveu a coleta A/B histórica.

Escopo: alterados contrato offline de vigência, adaptador conversacional do
grafo, comentários da sonda e testes/documentação. Produção, `laylay.py`,
treino, prompt e executores não foram alterados; sem commit. Não abrimos a
Laylay nem comprovamos sua fala final em uso real.

Limite importante: bloquear contexto não coberto é **conservador**, não
compreensão geral. Uma conversa posterior irrelevante também requer revisão;
ausência de pendências literais não prova vigência semântica. Portanto o
avanço indevido reproduzido está corrigido no avaliador automático, mas a
raiz mais ampla continua parcial: resolver relações/contexto com evidência
independente sem excesso de abstenções antes de qualquer integração de uso.

### P01: comparador inclusivo como átomo compartilhado (29/09)

Base mantida: HEAD `a078360e6b694c37f981e8be11f1470dd14571d5`, main.
Worktree suja verificada antes do patch: grafo já modificado; sinais e
produtor de candidatos não rastreados de etapas anteriores. Alterações
paralelas em `laylay.py` e P16 preservadas. Nenhum commit criado.

Próxima lacuna reproduzida a partir do v6 congelado: `_JUNCAO` cortava o
`ou` de `maior ou igual a 40 L`. Primeira fronteira RED é lexical: transforma
um comparador em duas condições. Não é erro de extração do Qwen: ocorre
sem modelo. Não é perda do efeito/sujeito: trechos mantêm as âncoras quando
a condição inteira é fornecida. A conferência direta isolou a fronteira
seguinte: o grafo só auditava/calculava operadores estritos `<` e `>`.

Contrato: operador composto numérico tem precedência lexical sobre junção
de condições, preservando os offsets da fonte. Implementação compartilhada
`encontrar_comparadores_inclusivos` no módulo de sinais; consumida pelo
segmentador e pela auditoria literal do grafo. Não substitui todos os `ou`
da frase. O grafo exige correspondência de operador, número e unidade antes
de usar Decimal para `<=`/`>=`. Guardas de sujeito, negação, contexto e
autoridade permanecem; o novo sinal sozinho não prova nenhuma delas.

Prova incremental: **12 falhas e 7 controles verdes** antes do patch.
Após somente corrigir segmentação: 12 verdes e 7 falhas no grafo, exatamente
na próxima fronteira, sem enfraquecer expectativas. Correção do grafo e
novos controles cobrem igualdade/abaixo/acima, dois domínios, negativo
decimal, operador proposto errado, unidades/limiares divergentes, contexto
revogado, alternativas reais e condições mistas. Notação científica e
números por extenso não são reconhecidos como átomos suportados.

Repetição diagnóstica local, `qwen3:4b-instruct`, produtor segmentado e
prompt intacto, três casos históricos v6:
- `TANQUE_INCLUSIVO`: `>=`, limiar `40`, unidade `L`, proposta alinhada e
  `condicao_numerica_satisfeita_relacao_pendente` (3,52 s).
- `CAMARA_LIMIAR_NEGATIVO`: extração e comparação preservadas (11,32 s).
- `DUTO_REGRA_REVOGADA`: modelo ainda seleciona regra antiga; grafo retorna
  `contexto_criterio_pendente`, comparação falsa (3,61 s). Veto não é acerto.

Validação final: **459 testes didáticos aprovados**, compilação e diff-check
limpos; não equivale à suíte completa de produção nem a runtime real Laylay.
Evidência das respostas no stdout desta sessão; coleta A/B original não foi
sobrescrita. Hashes v6 verificados, inalterados. Não contar repetição como
holdout nem inferir ganho agregado do painel sem medi-lo integralmente.

Escopo: três módulos offline de análise, um módulo novo de testes e estes
registros. Nenhuma produção, modelo, treino, gabarito ou configuração alterada
nesta etapa. Nenhuma execução da Laylay/entrega de fala testada. A raiz geral
continua parcial: seleção/vigência semântica das fontes e cobertura além da
gramática literal ainda precisam de prova independente antes de integração.

### P01: relações entre fontes, proposta sem autoridade (29/09)

Base: `a078360e6b694c37f981e8be11f1470dd14571d5`, main; status consultado,
worktree e patches paralelos preservados. O seletor anterior já recebia todas
as fontes, mas sua saída não mostrava relações com as falas posteriores.
Logo, falta de envio do contexto não explica sozinha a seleção incorreta.
Esta etapa mede proposta semântica; não cria um verificador independente.

Novo experimento offline `scripts/analises/sonda_relacoes_fontes_v1.py`,
reusando a consulta local do produtor existente. O host fornece uma regra
alvo e o contexto ordenado, sem IDs diagnósticos/gabarito para o modelo.
Papéis propostos: revoga, mantém, substitui, restaura, sem alteração ou
indeterminada. Cada fala deve estar coberta e citada integralmente. Mesmo
com cobertura perfeita: `relacao_semantica_verificada=False`,
`pode_registrar_vigencia=False`, sem fala ou efeito autorizado. Nenhuma
ligação com o RegistroVigenciaCriterios ou com a seleção de produção.

Doze casos locais escritos e revisados antes da primeira consulta, com
pergunta, negação, outro alvo, citação, conversa irrelevante, substituição,
ambiguidade entre duas regras, repetição sem adoção e restauração. Dois
domínios. Casos intencionalmente contrastivos, não amostra representativa.
Revisão do agente, não revisão humana independente. Hashes congelados:
- entradas `b739153c495c355a77ecae3c238c4de761c07e993bca98d64787f8e3313ddc6d`;
- revisão `45ec3439f1ea7c27e53a0544ea257130b00fafc419e3514dac55f4d681a41b65`.

Primeira execução, Qwen `qwen3:4b-instruct`, temperatura zero: **5/12 casos
completos alinhados**, **7/12 com cobertura/citação corretas**. Nos demais,
copiou a regra alvo em vez da fala analisada ou confundiu IDs/citações.
Pergunta e mudança de outro alvo falharam mesmo com a citação correta:
não é apenas erro de cópia. Artefato exclusivo:
`resultados_testes/sonda_relacoes_fontes_v1_primeira.jsonl`.

Candidato opcional `--relacao-isolada`: uma chamada por fala posterior,
com contexto completo e ID da fala fixado pelo host. Modelo propõe apenas
`relacao`; host preenche ID/citação com a fonte real. A revisão não participa
da chamada ou schema. Replay **diagnóstico**, sem novo holdout:
**9/12 casos completos**, **12/12 ancorados**. Quatro casos antes incorretos
passam; não atribuir o ganho só à cópia, pois prompt/schema/quantidade de
chamadas também mudaram (12 versus 15). Restam C02 (pergunta→revoga), C04
(outro alvo→revoga), C05 (citação sem adoção→mantém). C05 tinha rótulo correto
mas citação errada na primeira rodada, portanto houve regressão semântica
nesse item, apesar do ganho agregado. Artefato:
`resultados_testes/sonda_relacoes_fontes_v1_isolada_diagnostico.jsonl`.

Validação local: **486 testes didáticos aprovados**, incluindo 27 testes
novos de cobertura, ancoragem, formato, isolamento do gabarito e ausência de
autoridade para registrar vigência. Compilação e diff-check limpos. Testes
controlados verdes não substituem os três erros reais de geração acima.

Escopo: sonda nova, dois arquivos de painel/revisão, testes e documentação.
Nenhum módulo existente de análise ou produção foi alterado nesta etapa;
nenhum treino, integração de runtime ou relaxamento de guarda. Próxima
fronteira: ato de fala e vínculo com o alvo, não mais offsets/cópia. Não
resolver com lista de palavras revogadoras nem preencher o registro confiável
com a própria classificação do modelo. Fixar o contrato e medir novos casos
antes de afirmar generalização ou substituir a proteção conservadora.

### P01: ato/alvo/operação — hipótese medida, candidato não promovido (29/09)

Base preservada `a078360e6b694c37f981e8be11f1470dd14571d5`, main, worktree
suja e mudanças paralelas verificadas. Inventário: `modalidade_turno` e
`interpretador_semantico_runtime` já tratam atos/modalidade no runtime.
Não duplicar esses owners em produção. Esta sonda é experimento restrito
de relações entre fontes, reusando o transporte, entrada e conferência v1;
não substitui o interpretador canônico e não registra revisão de vigência.

Hipótese: três campos menores (ato, alvo da operação e operação) propostos
pelo Qwen, convertidos por contrato tipado, poderiam reduzir a confusão entre
perguntar, citar e efetivamente alterar uma regra. O texto não é parseado
por listas privadas de frases. A conversão apenas compõe rótulos propostos;
não os verifica semanticamente e mantém todas as autorizações falsas.

Painel novo v2, 12 casos em servidor, estufa e estoque, revisão local antes
de qualquer chamada. Inclui pergunta sem interrogação, pedido educado com
interrogação, alvos trocados em pares, citação adotada/não adotada, hipótese,
manutenção explícita, substituição, restauração e ambiguidade. Hashes:
- entradas `cf8ec5894c700e834b3767b869b1b94cb1232c15ecdb56bf3ecd21c48cbf8abc`;
- revisão `5bf3486bcbfa84001d1c9b1c3d3913942e72477ee3fa967729577171c1c438a5`.

Primeira medição dos novos casos, mesmo Qwen `qwen3:4b-instruct`, temperatura
zero, ordem dos braços alternada, sem compartilhar respostas: baseline
isolado **6/12**, decomposição **8/12** na relação final de todas as falas do
caso. Mesmo número de chamadas por braço (14), mas prompt/schema/entrada
diferentes; não atribuir o ganho somente à quantidade de campos. Ganha N01,
N03 e N04; perde N12 (conversa irrelevante passa a indeterminada). Restam N05
(citação), N07 (hipótese), N11 (referência indeterminada) e N12. Artefato:
`resultados_testes/sonda_relacoes_fontes_v2_ab_primeira.jsonl`.

Sem mudar candidato ou gabarito após essa coleta, replay do v1 histórico:
baseline **9/12**, candidato **7/12**. Ganha C02, mas perde C06, C08 e C11;
C04 e C05 continuam incorretos. Em C11, negação de manutenção com revogação
explícita foi interpretada como manutenção. Em C08, relatos declarativos
foram rotulados como perguntas; o primeiro dá relação final correta por
compensação, o segundo oculta ambiguidade. Portanto acerto da relação não
significa acerto de todos os campos. Revisão congelada avalia relação final,
não valida formalmente cada decomposição. Artefato diagnóstico:
`resultados_testes/sonda_relacoes_fontes_v2_v1_ab_diagnostico.jsonl`.

Decisão: **não promover** esta decomposição sobre o baseline. A hipótese de
melhora consistente não foi sustentada; não ajustar o gabarito, selecionar
apenas os ganhos ou relaxar o contrato para fazer o resultado parecer melhor.
Mantidos casos/saídas completas e os erros semânticos visíveis. O painel novo
é local e pequeno, sem revisão humana independente; replay v1 não é holdout.

Validação: **510 testes didáticos aprovados**, 24 novos; compilação e
diff-check limpos. Testes cobrem formato/coerência tipada, ausência de escrita
de vigência, fonte completa fixada pelo host e isolamento do gabarito. Nenhum
módulo existente de produção/análise foi alterado, nenhum treino ou runtime
foi iniciado. Adicionados sonda v2, painel/revisão, testes e documentação.
Próximo contrato a investigar: provar ato e alvo separadamente, confrontando
também os serviços canônicos já disponíveis, em vez de supor que mais campos
numa única chamada resolveram a interpretação. Vigência continua fora da LLM.

### P01: veto estrutural opcional e painel cego v4 (28/09)

Base: HEAD `a078360e6b694c37f981e8be11f1470dd14571d5`, branch
`main`, worktree preexistente suja. No v3 diagnostico, a guarda
puramente literal ainda admitia `PACOTE_ROTULO_NA_LEITURA` e
`BATERIA_REGRA_COMPOSTA`. A primeira fronteira e a elegibilidade da
fonte antes da normalizacao, nao o operador numerico.

O sinal compartilhado `gerar_candidatos` foi testado sem patch: gerou
zero condicoes para a leitura do pacote, duas para a regra da bateria
e uma para os criterios simples, inclusive `apenas se`. Isto sustenta
um veto conservador de estrutura para a sonda de criterio **unico**;
nao prova que o efeito seja uma qualificacao do referente. Um RED
focado exigiu que a selecao com `exigir_condicao_unica=True` nao chame
normalizacao quando a fonte so menciona o rotulo ou tem duas
condicoes. O contrato foi implementado como opcao, preservando o
piloto v2 como baseline. O esquema limita o ID proposto e a guarda
host revalida a estrutura mesmo se o modelo ignorar o esquema.

Antes de consultar modelo, o painel v4 foi escrito e revisado com dez
casos novos: cinco criterios simples e cinco abstencoes. Dois negativos
foram escolhidos para falsificar a suposicao de que uma condicao unica
basta: regra de **acao** que contem o rotulo e efeito **negado** com
rotulo literal. Ambos ainda passam pela guarda estrutural, mas a
revisao exige abstencao. As propostas canonicas positivas passaram
pelo grafo, permanecendo sem aprovacao para fala/efeito. Hashes
SHA-256 congelados antes da primeira medicao: entradas
`0217A119EFD0457B17585EADDCAACA5B33A8AD4BB11EB7F6AA8EE776A1855B35`,
revisao `E5B5DCC945AE2DB289A7CF00EF65BC687169412FE417E083B2E76041516D7691`.
Loader v4 recusa alteracao silenciosa; 21 testes dos pilotos v2-v4
verdes antes da medicao.

Primeira medicao v4, `qwen3:4b-instruct` local, temperatura zero, sem
alterar painel ou revisao: selecao exata em **5/10** casos (os cinco
positivos); **0/10** propostas completas alinhadas. Para os negativos
sem fonte estrutural (`CAIXA_ROTULO_NA_LEITURA` e
`POMAR_REGRA_COMPOSTA`), o modelo ainda respondeu
`fonte_candidata` com ID vazio, mas a guarda recusou e nao chamou a
normalizacao. Em `CIRCUITO_ACAO_COM_ROTULO` e
`PORTA_EFEITO_NEGADO`, fontes com uma condicao textual passaram e o
modelo forcou criterio; a revisao posterior rejeitou. Portanto o veto
de estrutura nao verifica papel do efeito ou polaridade, e a sonda
permanece inapta a publicacao mesmo que a selecao positiva melhore.

Repeticao diagnostica de dois positivos, nao novo holdout, isolou a
normalizacao: em `POMAR_CRITERIO_SECO` o Qwen copiou a regra inteira
como `citacao_condicao` e trocou `Se` (suficiente) por direcao
necessaria; em `SERVICO_APENAS_SE` tambem copiou a regra inteira e
devolveu `limiar=">"` em vez do numero. A proxima fronteira e separar
trecho literal e direcao explicitamente marcada — que os servicos
compartilhados ja podem fornecer — dos slots numericos propostos pelo
modelo. Isto deve ser provado em novo painel; ainda restara um
verificador independente do efeito/negacao. Nao ajustar gabarito v4
nem declarar ensino resolvido com o filtro estrutural.

Validacao ao fim desta etapa: 331 regressivos didaticos verdes,
`py_compile` e `git diff --check` limpos; hashes do v4 iguais aos
congelados. Nenhum arquivo de runtime, executor ou treino foi alterado.
