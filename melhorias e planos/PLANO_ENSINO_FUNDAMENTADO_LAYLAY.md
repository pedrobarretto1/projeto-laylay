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

### P01: aferição de cada fronteira e contraste do alvo explícito (29/09)

Base atual verificada: HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, main,
worktree inicialmente limpa. Os trabalhos anteriores já estão no novo
commit; não transportar o HEAD antigo como trava ou baseline de código.
Hashes do produtor v2 continuam iguais aos da primeira coleta. Nenhum
commit criado ou mudança externa revertida nesta etapa.

Entregue `scripts/analises/sonda_relacoes_dimensoes_v1.py` com revisão local
separada de cada campo no painel v2 congelado. A revisão por campo foi
escrita antes das novas chamadas, mas sobre casos já conhecidos: é diagnóstico,
não holdout. Possui alternativas explícitas para relato/outro em conversa
irrelevante; não foi ajustada após geração. Hash:
`0e3ae60225c1f0fcf3616e1667a806aeddbeacab8e4c98f1bfe013c52d9e54bc`.
Os campos descrevem posição relativa à mudança de regra, incluindo operação
apenas mencionada em pergunta/hipótese/citação. Não certificam a relação.

Resultados Qwen real, `qwen3:4b-instruct`, temperatura zero, 14 falas em
12 casos conhecidos; ordem dos braços alternada:

| Fronteira | Conjunta (1 chamada/fala) | Separada (3 chamadas/fala) |
| --- | --- | --- |
| Ato alinhado | 7/14 | 7/14 |
| Alvo alinhado | 11/14 | 2/14 |
| Operação alinhada | 8/14 | 9/14 |
| Todos os campos corretos no caso | 3/12 | 1/12 |
| Relações finais corretas no caso | 9/12 | 4/12 |

Primeira coleta deste diagnóstico:
`resultados_testes/sonda_relacoes_dimensoes_v1_diagnostico.jsonl`.
Exemplo de compensação: ato errado pode produzir `sem_alteracao` correto.
O teste canônico mantém relação final verde e exige campo errado vermelho.
Logo, 9/12 relações não devem ser descritas como 9/12 interpretações completas.
A conjunta variou de 8/12 da coleta anterior para 9/12 nesta repetição com
script preservado. Não atribuir variação à mudança de código e não supor
reprodutibilidade perfeita apenas por temperatura zero.

Contraste adicional isolou só a exposição do alvo. Mesmos prompt, schema,
modelo, fontes e ordem; um braço acrescenta `regra_comparada` com o mesmo
objeto f0 já existente no histórico. Nenhum ID/revisão novo revela resposta.
Resultado: **2/14 nos dois braços**. Saída exclusiva:
`resultados_testes/sonda_relacoes_dimensoes_alvo_ab_diagnostico.jsonl`.
Falsificada como explicação suficiente a falta de destaque da regra no JSON.
Não demonstra incapacidade geral do Qwen: o formato de tarefa e a identidade
contextual ainda precisam de um contrato melhor.

Serviço existente efetivamente consumido: `classificar_modalidade_turno`,
API pública real com opções padrão. Guardados modalidade, atos, natureza e
veto; autoridade não é exportada para decisão da sonda. Na consulta direta,
13/14 falas ficam como conversa; N02 é misto/conversa+pergunta, N08 conversa.
N01 sem '?' fica conversa. O serviço não expõe identidade de regra comparável.
Isso delimita sua cobertura nessa tarefa; não validar alvo por `conversa`.
`leitura_semantica_turno` foi inventariado: normaliza propostas, não verifica
semântica; não foi usado como oracle. Composição real do orquestrador injeta
normalizador/detector e confirmação contextual, que esta API direta não
reproduz. Portanto não declarar falha corrigida ou diagnosticada no loop real.

Decisão: manter candidatos experimentais. Separar chamadas não melhorou
o conjunto e destacar o alvo não resolveu vínculo. Próxima hipótese causal:
explicitar identidade/âncoras da regra e vínculo da menção antes de classificar
relação. Provar com inventário contextual e fonte observada, sem inferir que
um nome mencionado autoriza alteração ou comprova vigência. Erros de ato e
operação continuam medidos separadamente; não agrupá-los como a mesma root
apenas por participarem da mesma frase.

Validação: **520 testes didáticos aprovados**, dez novos; compilação e
diff-check limpos. Os testes protegem isolamento das chamadas, cobertura,
fonte do host, aferição por campo e ausência de escrita de vigência. Produção,
sondas anteriores, painéis v1/v2, modelo e treino preservados. Novos arquivos:
sonda diagnóstica, revisão por campo e testes; documentação atualizada.

### P01: identidade nominal explícita antes do alvo semântico (29/09)

Base preservada: HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, main;
worktree já continha os três documentos e os três arquivos do diagnóstico
por campo. Nenhuma mudança anterior apagada ou commit criado nesta etapa.

Inventário estudado: `contrato_inventario_contextual.py`, suas guardas e
`referencias_linguagem.qualificador_referencia_nominal`. O qualificador é
genérico, não carece de uma lista especial com `regra`. O resolver nominal
existente deliberadamente deixa dois itens como `referentes_concorrentes`,
mesmo em pedido explícito; isso não é bug a ser removido. Seu foco explícito
exige uma declaração própria de assunto e não pode ser fabricado a partir
de pedido/citação. Controle real mantém esse resultado e todas as guardas.

Novo experimento `scripts/analises/sonda_alvo_inventariado_v1.py`:

1. A fonte enumeradora do **painel offline**, não uma LLM/seletor de contexto,
   fornece cadastro tipado, nomes literais, origem, escopo, captura e TTL.
2. Host reusa a validação canônica do inventário completo e confere o mapa
   de nomes. Nome duplicado, origem/escopo divergentes, cadastro parcial,
   vencido ou âncoras sobrepostas bloqueiam. Não registra foco ou vigência.
3. Host localiza todas as ocorrências dos nomes registrados, com offsets,
   fonte/escopo, inclusive as negadas e citadas. A correspondência é literal;
   não certifica a identidade semântica da expressão inteira, paráfrases,
   qualificadores extras, pronomes ou alvo operacional. Fonte sem nome não
   recebe identidade inventada. Todas as aprovações continuam falsas.
4. Qwen propõe só `referente_id`, `nenhum` ou `indeterminado`, entre os mesmos
   IDs permitidos nos dois braços. O host confere formato/ocorrência, não
   aceita que um ID verdadeiro certifique papel na oração. Teste mantém
   âncora válida para ID semântico errado, sem autorização ou autoaprovação.

Contrato geral: identidade cadastrada → ocorrência literal → papel semântico
proposto são fronteiras distintas. O mesmo mecanismo foi exercitado com
sensores, sem parser privado de comandos de regra. A lista de nomes pertence
à fonte do cadastro; não foi descoberta/confirmada automaticamente nesta
etapa. Portanto não substituir a descoberta de identidades no runtime por
esses dados fornecidos manualmente nem anunciar uma nova capacidade ativa.

Painel novo de 12 falas, três cadastros com dois itens: infra, clima e estoque.
Contém pedido educado, pergunta sem '?', citação sem adoção, operações sobre
outro alvo, negação, manutenção, substituição, restauração, conversa
irrelevante e ambiguidade. Revisão **local** escrita antes da primeira
medição; não há validação humana independente. Hashes congelados:

- Entradas: `352cf507f7e05d3e68405199d45291ef953cdc205de77bccbc2c92bb235c817b`.
- Revisão: `152f875c39a77945ac97be0fa25babf530d917a22b327d3b1ac2fc51553ff181`.
- Script medido: `ed66e60740ddf913876e69854b0e21078f33546b5e07a63076dfcdbf2b28d55b`.

Contraste controlado: mesmo texto, inventário, nomes, prompt, schema, IDs
permitidos e modelo; somente o braço ancorado acrescenta ocorrências
calculadas pelo host. Ordem alternada. `qwen3:4b-instruct` local, temperatura
zero, 24 chamadas; artefato exclusivo preservado:
`resultados_testes/sonda_alvo_inventariado_v1_ab_primeira.jsonl`.

| Fronteira de alvo mencionado | Cadastro | Cadastro + âncoras |
| --- | --- | --- |
| IDs/abstenções alinhados à revisão | 10/12 | 11/12 |
| B08, duas regras e retirada sem identificação | escolheu estufa indevidamente | indeterminado |
| B09, regra mencionada sem operação | escolheu loja indevidamente | mesmo erro |

Este é ganho pontual em uma coleta, não superioridade demonstrada da rede,
nem porcentagem comparável ao diagnóstico anterior: houve nova tarefa com
IDs fornecidos e sem classificação de ato/operação/vigência. As nove falas
com alvo definido alinharam nos dois braços; o erro restante demonstra que
nome/ID ancorado não resolve a existência de operação. Nenhum prompt, caso
ou gabarito foi ajustado depois do resultado. Candidato não promovido.

Validação: **62 testes focados** (sonda e contratos reais do inventário/foco),
**468 regressivos didáticos e de inventário** numa seleção com sobreposição;
não somar as contagens nem tratá-las como a seleção anterior de 520.
Compilação e diff-check limpos. Arquivos novos: sonda, painel, revisão e
testes. Produção, resolver nominal, guardas de contexto, demais sondas e
painéis, memória do usuário, treino e runtime preservados. Sem efeito externo.
É prova de componentes reais e geração real do Qwen, não execução da Laylay.

Próxima fronteira: presença e escopo da operação mencionada, mantendo ato e
autoridade separados. Antes de qualquer integração, ampliar painel com nomes
novos, ordens/IDs trocados e referências não literais; não compensar B09 com
um filtro por palavras nem declarar vigência a partir da proposta do modelo.

### P01: presença e escopo da operação antes do alvo — contraste negativo (29/09)

Base: HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, main. Preservados
documentos, sondas, painéis e testes preexistentes na worktree. Investigação
permanece P01; não há outro ID de problema para O01/B09 ou cada modalidade.

Hipótese testada: o alvo errado em mera discussão poderia ser reduzido por
uma etapa independente de presença/escopo antes da proposta de ID. Inventário
de serviços: normalizador semântico canônico não é verificador de sentido;
modalidade ampla não resolve a presença desta operação didática. Reusados
cadastro, âncoras, baseline nominal e transporte existentes; `_ancorar_trecho`
de `sonda_produtor_condicoes_v2` fornece o rastreio literal único, sem copiar
um parser de condição para decidir operações. Nenhum serviço de produção
substituído, antecedente fabricado ou catálogo ativo alterado.

Entregue `scripts/analises/sonda_operacao_antes_alvo_v1.py`, painel/revisão e
regressivos. Contrato experimental:

- Host valida inventário antes de qualquer chamada. Fonte integral, IDs e
  todas as âncoras permanecem disponíveis no braço estagiado.
- Primeiro modelo propõe `operacao_mencionada`, `sem_operacao` ou
  `indeterminado`, com trecho literal único somente na primeira alternativa.
  Pergunta/citação/hipótese podem mencionar uma operação sem adotá-la.
- Trecho inexistente, ambíguo ou formato inválido impede chamada dependente.
  Uma abstenção proposta também evita chamar o seletor de ID, mas continua
  sem verificação semântica: isso pode perder uma operação real mencionada.
- Quando há trecho ancorado, segundo modelo recebe a fonte inteira e o
  trecho com offsets; não removemos negação/histórico para facilitar o alvo.
- Presence/escopo/alvo são aferidos separadamente depois das chamadas.
  Alvo correto com presença ou escopo errado não produz interpretação verde.
  Ausência de operação de regra não consome outro comando, como abrir a
  calculadora, nem marca `tratado=True` no runtime.

Novo painel de 16 falas: oficina/cofre, biblioteca/museu e horta/lago.
Quatro sem operação de regra e doze que mencionam operação, inclusive duas
sem identidade determinada. Inclui apagar uma explicação, não a regra,
pedido educado, pergunta sem '?', negação de outra regra, manutenção,
substituição, restauração, citação e hipótese. Revisão local escrita antes
da coleta; não é revisão humana independente. Intervalos mínimo/máximo de
escopo são expectativas locais explícitas, não um verificador universal de
modalidade ou completude. Hashes congelados antes da medição:

- Entradas: `ec02141a0e92a270df9b63a9fcdf11391faa7e4f217c1c572f3cb2a1854ff4dd`.
- Revisão: `f4714d9cae8ddb0d78e54590874dab040fb4eb846e52abc7fe7c2abe80d88f82`.
- Script da primeira coleta e replay: `d92598a8993e8dadb477c3161f441b38ccc1ab4aecedf754caf186366adae143`.
- Baseline preservado: `ed66e60740ddf913876e69854b0e21078f33546b5e07a63076dfcdbf2b28d55b`.

Qwen real local `qwen3:4b-instruct`, temperatura zero; braços alternados sem
compartilhar respostas. Primeira coleta:
`resultados_testes/sonda_operacao_antes_alvo_v1_ab_primeira.jsonl`.

| Fronteira | Direto, com âncoras | Estagiado |
| --- | --- | --- |
| Alvo alinhado | 11/16 | 11/16 |
| Presença alinhada | não propõe esse campo | 11/16 |
| Escopo alinhado | não propõe esse campo | 10/16 |
| Todas as fronteiras aferidas alinhadas | não aferível | 10/16 |

Três ganhos em menção irrelevante (O01/O09/O14) foram compensados por três
perdas (O05/O06/O16). O10, apagar texto explicativo, continua sendo tomado
como operação sobre a regra; O13 continua sem abstenção correta de alvo.
O04 acerta alvo, mas o trecho perde `Pode`, contrariando a revisão de escopo;
teste mantém esse RED mesmo com resultado final correto. Os demais testes
também expõem presença errada com alvo correto e escopo de outra regra.

Replay diagnóstico dos 12 casos nominais conhecidos, sem ajustar dados:
direto **10/12**, estagiado **9/12**. B09, mero assunto futuro, fica correto
no candidato; B04/B08/B12 falham. Resolver o turno histórico isolado não
prova o contrato generalizável. A coleta direta anterior tinha 11/12 e B08
correto; nesta repetição B08 variou, sem mudança do baseline.
Artefato: `resultados_testes/sonda_operacao_antes_alvo_v1_replay_nominal.jsonl`.

Falsificação adicional após terminar as coletas: um modo diagnóstico foi
acrescentado, sem editar o candidato nem o baseline. Repete só a primeira
chamada nos mesmos 16 casos conhecidos: mesma instrução, schema, modelo e
fonte integral; um braço não expõe cadastro/nomes/IDs. O host mantém a
validação do inventário nos dois. Não é novo holdout nem mudança de produção.
Script desse diagnóstico: `4aec0456adc9e8bf45d4a3d0600146bd5d14a5f278c86ad4a98a368bebc8aa04`.
Artefato: `resultados_testes/sonda_operacao_antes_alvo_v1_presenca_ab_diagnostico.jsonl`.

| Diagnóstico de entrada, sem ID final | Cadastro | Só a fonte |
| --- | --- | --- |
| Presença alinhada | 10/16 | 11/16 |
| Escopo alinhado | 9/16 | 10/16 |

O05/O06/O10/O13 continuam errados nos dois. Retirar cadastro ajuda O01/O16,
mas prejudica manutenção O12. O01 variou na repetição com entrada preservada;
temperatura zero não autoriza afirmar estabilidade perfeita. Não promover
uma diferença de uma fala nessa coleta. Fonte completa já está presente e
o erro de citação/hipótese ocorre na proposta de ausência, antes de copiar
um trecho: não é causado pelo rastreador literal. Falsificadas como soluções
suficientes tanto adicionar um gate simples quanto remover IDs do gate.

Decisão: **candidato não promovido**. Próxima representação a estudar:
proposição/evento mencionado → objeto da operação → moldura discursiva,
sem reduzir falta de adoção ou de identificação à ausência do evento.
É hipótese de arquitetura, não causa única provada de todos os históricos
nem motivo para adicionar palavras-chave ou aumentar campos indiscriminadamente.
Permissão, efeito e vigência continuam sob owners próprios e não são
inferidos dessa representação. Antes de novo contraste, definir esse
contrato e seus controles; não ajustar esta revisão aos erros do Qwen.

Validação final: **492 regressivos relevantes verdes**, 24 novos nesta etapa;
seleção inicial focada de 73 com sobreposição, não somar contagens.
Compilação e diff-check limpos. Nenhum commit, treino, produção, memória
durável, executor ou runtime da Laylay alterado/iniciado. Resultados provam
contratos dos componentes e delimitam falhas reais de geração; não encerram
a raiz semântica nem demonstram qualidade da fala final de ensino.

### P01: proposição, objeto e molduras — contrato inerte e piloto (29/09)

Base preservada: HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch
`main`, worktree com as sondas/relatórios anteriores. A investigação de código
reutilizou fonte, ancoragem e aspas canônicas; não criou outro parser de
comandos, registro de vigência ou inventário privado.

Contrato implementado só em `scripts/analises/contrato_proposicoes_mencionadas.py`:

- fontes tipadas completas, sem normalização ou truncamento;
- proposições de ação/estado, cada uma com predicado/objeto literais e
  polaridade/papel propostos, sem escolher uma identidade inventariada;
- molduras propostas ligadas por IDs, mesma fonte, contenção e ausência de
  ciclos; molduras coextensivas permitidas, não fundidas;
- todos os pares de aspas canônicas, incluindo os aninhados, com parentesco;
  região entre aspas também pode ser filename/título, não prova ordem citada;
- trecho repetido sem âncora única recusado, não escolher primeira ocorrência;
- nenhuma parte de um grafo inválido publicada como grafo completo;
- semântica, cobertura, identidade, autoridade, vigência e produção sempre
  falsas. Lista vazia/objeto desconhecido/moldura omitida não certificam ausência.

Fontes: `FonteDidatica` já existente. Âncora: `_ancorar_trecho` da sonda
canônica de condições. Aspas: `mapear_pares_aspas_globais`, sem importar
extratores neurais ou achatar a árvore. Limites desse mapeador continuam
explícitos; não ampliado neste candidato. Não converter `EventoCognitivo`
perceptivo em proposição/permite-ação. Os owners operacionais continuam intactos.

Testes: 43 de estrutura/inércia e 20 de entrada/aferição. Controles cobrem
arquivo/IoT/música/regra, pergunta com hipótese, citação aninhada, objeto
textual, alteração negada seguida de pedido independente, estado com objeto
desconhecido, fonte extensa, ciclos, fonte/objeto errados, omissão de moldura
e interpretação errada mas literalmente ancorada. Auditoria independente
encontrou uma guarda de origem sem validação de tipo no protótipo; dois REDs
reproduziram TypeError e o candidato mínimo adicionou a validação prévia.
Isso não é uma correção de bug do runtime da Laylay.

Também foi auditada a métrica histórica de escopo: O03 permite remover
`Quero saber se`, O05 permite omitir aspas/envelope de exemplo; O04/O06
exigem modalidade. Esses mínimos continuam válidos como seleção local de
trecho, mas não demonstram preservação uniforme de moldura. Gabaritos,
hashes e contagens anteriores não foram alterados para corrigir o placar.

Piloto `sonda_proposicoes_mencionadas_v1.py`: oito falas novas em dois domínios
(arquivo `croqui.md` e tomada da bancada), quatro contrastes por domínio:
pedido, pedido citado como exemplo, hipótese perguntada e objeto diferente
que menciona o recurso. A tarefa é a operação **principal** de mudança,
não a cobertura de todas as proposições de uma conversa. Fonte integral e
aspas sintáticas chegam ao Qwen; case ID, domínio e revisão não chegam.
Transporte existente, `qwen3:4b-instruct`, temperatura 0, limite 700 tokens.
Gabarito local antes da geração, sem revisão humana independente.

Congelamento:

- entrada: `fb77fbfe071de204a8ff72b7dfc769652309d1178ddc563197f10f528c7fa389`;
- revisão: `7072700e9944467ec08f4ba2a261a6973e958b8243820cbeb6945b8773994d5b`;
- contrato: `e286c3032fa7ee2c02f14112b353b949d167a96bec1699ee3958503dc01dfb99`;
- sonda: `f62dce2dd36fbb15899a38d69d9c77a69f0bd4fb3aab391dce6e6821e9f067da`.

Primeira coleta preservada em
`resultados_testes/sonda_proposicoes_mencionadas_v1_primeira.jsonl`:

| Fronteira | Alinhada à revisão local |
| --- | --- |
| Estrutura/âncora | 6/8 |
| Uma operação do piloto | 5/8 |
| Predicado | 5/8 |
| Objeto literal completo | 3/8 |
| Papel do objeto | 5/8 |
| Polaridade | 0/8 |
| Cadeia completa de molduras | 4/8 |
| Todas as fronteiras | 0/8 |

Interpretação conservadora, **candidato não promovido**:

- F02/I02: primeira fronteira RED na cópia de aspas tipográficas como ASCII;
  moldura/proposição deixam de ser citações literais. No bruto, o predicado
  escolhido é `Usei`, não a operação interna. Não relaxar o rastreador.
- F01/F03: objeto perde só o artigo. Divergência da superfície esperada,
  não prova de entidade semanticamente errada. Não ajustar ouro após geração.
- F04/I04: complementos textuais/automação preservados nessa coleta, mas
  isso não confirma alvo de executor nem cooperação entre habilidades.
- F03/I03: hipótese proposta sem `Se eu`; I03 também representa `mudaria`.
  A tarefa restrita pede uma operação; isso não prova cobertura geral ruim.
- Pedidos sem negação recebem `negativa`; hipóteses recebem `indeterminada`.
  Hipótese de confusão entre negação gramatical, efeito da ação e certeza de
  ocorrência. Ainda precisa de contraste controlado; não declarar root única.
- F02/I02 admitem também um envelope de relato de uso metalinguístico,
  não previsto nesta cadeia local. Uma moldura extra plausível divergiria
  do ouro; não seria erro semântico automaticamente demonstrado.

Não há baseline equivalente nesse piloto, portanto **nenhuma comparação de
ganho**. A representação de múltiplas proposições e estados passou controles
estruturais, mas não foi avaliada amplamente na extração real. Mudar somente
a saída monolítica não foi solução suficiente aqui. Próxima fronteira:
seleção da proposição literal antes da tipagem, sem recopiar o envelope do
host. Depois, controlar negação gramatical separadamente de valor/certeza;
preservar contexto externo, sem tratá-lo como autorização. Não repetir um
gate que confunda citação/hipótese com ausência de operação.

Validação: **555 regressivos relevantes verdes**, incluindo 63 novos nesta
etapa (seleção focada com sobreposição, não somar). Compilação e diff-check
limpos. Nenhum commit, produção, treino, memória durável, registro de vigência,
executor ou runtime da Laylay alterado/iniciado. Contrato estrutural GREEN,
extração sem promoção, nenhuma prova de ensino final/runtime encerrada.

### P01: seleção literal por cópia versus ID — contraste isolado (29/09)

Base mantida: HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch
`main`; sondas e alterações anteriores preservadas. A pesquisa de código
localizou seletores condicionais/nominais já existentes, mas não um seletor
público genérico de uma proposição. O candidato offline reusa
`FonteDidatica`, a conferência pública de proposições com proposta vazia,
a âncora literal existente e o mapeador canônico de aspas. Não adiciona parser
privado nem altera modalidade operacional, resolver contextual ou runtime.

Arquivos: `scripts/analises/sonda_selecao_literal_proposicao_v1.py`, seus
dois JSONs em `scripts/analises/dados/` e
`scripts/tests/test_sonda_selecao_literal_proposicao_v1.py`.
O catálogo preserva fonte integral, todos os conteúdos citados e offsets de
cada ocorrência; não filtra nomes nem verbos. Pares aninhados são preservados.
ID materializa o trecho do host; cópia exige um candidato integral e único,
usando a recuperação de caixa da âncora existente, não cópia byte a byte.
Ocorrências repetidas são distinguíveis por ID/offset, mas ambíguas na cópia:
testadas estruturalmente e excluídas deste A/B. Aspas incoerentes não viram
ausência: a fonte integral permanece disponível e a incoerência é publicada.

Contrato: trecho autêntico continua em `selecao_literal_revisao_pendente`.
Abstenção não prova ausência de operação. Os seis campos de semântica,
cobertura, referente, autorização, vigência e promoção ficam `False`.
A seleção não é convertida automaticamente para interpretação tipada;
perder offsets ao converter ID para texto reintroduziria ambiguidade de
ocorrência. Auditoria reproduziu dois REDs: igualdade Python admitia offset
`0.0`/`False` como `0`. Conferência de catálogo agora exige tipos JSON
preservados, além da igualdade de conteúdo; GREEN após candidato mínimo.

Painel novo de 12 fontes congelado antes da geração. Tarefa comum: selecionar
o menor **candidato do host** contendo a operação principal mencionada, sem
escolher arbitrariamente entre operações sem foco. Citação, hipótese e
negação não apagam uma operação; nome/filename não a provam. Ambos recebem
a mesma fonte e catálogo, sem ouro/ID do caso; diferem apenas no protocolo
de saída. Ordem dos braços e apresentação dos candidatos contrabalançadas,
seis casos em cada ordem. Qwen local `qwen3:4b-instruct`, temperatura zero,
700 tokens; sem runtime da Laylay. Revisão local, não humana independente.

Hashes SHA-256 congelados:

- Fontes: `103214ecce3a59be0d2bf2a101f6121005651964b59eaae677f88d3836bb6799`.
- Revisão: `fe7af8263c6ee65af81fe415ec34b2604ce9c20d9ab6a6696b6714a192f8acb0`.
- Sonda: `2146d76e2afaa87e45c2abbccffbbbdc13a24d1219cafcdc48e04db79bb688ab`.

Coleta exclusiva:
`resultados_testes/sonda_selecao_literal_proposicao_v1_ab_primeira.jsonl`.

| Fronteira local | Cópia | ID |
| --- | --- | --- |
| Saída válida no catálogo | 11/12 | 12/12 |
| Seleção alinhada à revisão | 6/12 | 6/12 |

**Empate, candidato não promovido.** ID melhora L01/L02 (operações citadas),
mas regride L11 (hipótese sem aspas → abstenção) e L12 (nome `Leste` em vez
do pedido negado). Ambos erram L04 (filename `apague isso.txt`), L05 (nome
irrelevante mais operação externa), L06 (comparação sem foco) e L10 (expressão
sem operação). Em L05, cópia propõe subtrecho literal fora do catálogo e é
recusada; ID escolhe `arquivo disponível`. Não atribuir essa falha de cópia
a reescrita de aspas. ID produz texto autêntico, não interpretação correta.

Controle diagnóstico conhecido F02/I02: **2/2 válidos/alinhados nos dois
braços**, preservado em
`resultados_testes/sonda_selecao_literal_proposicao_v1_historico_diagnostico.jsonl`.
A tarefa menor não pede objeto/polaridade/moldura; não altera ouro antigo,
não corrige o pipeline completo e não conta como holdout ou ganho de ID.
Teste de hipótese concorrente repara só aspas da antiga proposta F02 em
memória: estrutura fica ancorada, mas o predicado `Usei` continua divergente.
Logo, cópia não era explicação exclusiva da seleção histórica incorreta.

Validação: **40 testes novos, 595 regressivos relevantes verdes** nesta
seleção, com sobreposição; compilação/diff-check limpos. Produção, treino,
persistência, composição, executor e runtime da Laylay não alterados/iniciados;
nenhum commit. Ouro, hashes e contagens históricos preservados. Próxima
fronteira: estudar papel do trecho na oração e vínculo predicado/objeto,
distinguindo operação mencionada de nome/metalinguagem com componentes
canônicos antes de propor outro candidato. Não aumentar treino/prompt nem
adicionar gate por aspas. GREEN das guardas não encerra a raiz de P01.

### P01: função contextual do foco — diagnóstico sem seleção final (29/09)

Base mantida: HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch
`main`, worktree anterior preservada. Investigação com pesquisa de código
em duas leituras paralelas, sem produção/modelo durante o inventário.

Inventário e responsabilidades:

- `nome_natural.mapear_pares_aspas_globais` e o catálogo literal existente
  preservam fonte, árvore e ocorrência por ID/offset: reuso direto.
- `normalizacao_linguagem.texto_e_metalinguistico` descreve a moldura inteira,
  não autentica função de cada fragmento nem dá autorização.
- `fundamentacao_factual._destaques_com_papel` já usa relação local para
  distinguir referência de enunciado, mas é privado/voltado à saída, com
  regex curta sem árvore aninhada. Não é parser genérico da entrada original.
- `leitura_semantica_turno` descreve ação/alvo sem autorizar; normaliza/trunca
  textos e não fornece spans certificados do foco. Não substitui o catálogo.
- `modalidade_turno` permanece owner de autorização/veto. Nenhuma dessas
  rotas foi alterada ou chamada como executor por esta sonda.

Primeira distinção importante do A/B antigo: catálogo só oferece fonte
inteira e conteúdos citados. A oração operacional externa de L05 não era
candidato; cópia a identificou e o host a recusou corretamente. Esse RED
não prova erro semântico. Preferência por “menor”/aspas e condicionamento do
schema são hipóteses, não raiz universal demonstrada.

Novo diagnóstico remove competição e “menor”: host fornece um foco autêntico
e fonte integral; modelo propõe somente sua função contextual. Não há
seleção da operação principal, resolução de objeto, polaridade, vigência,
ausência geral de operação ou autorização. Rótulos locais:
`nome_designacao`, `operacao_mencionada`, `expressao_sem_operacao`,
`indeterminado`. Nome pode ter formato de ordem; hipótese, exemplo, citação
e negação podem mencionar operação sem autorizá-la. Rótulo tipado continua
proposto, com todos os seis campos BASE `False`, mesmo quando alinha ao ouro.

Implementação isolada: `scripts/analises/sonda_papel_trecho_v1.py`, dois JSONs
em `scripts/analises/dados/` e seu teste em `scripts/tests/`. Reusa preparação
e conferência do seletor literal; não cria parser nem lista privada de verbos.
Foco repetido/aninhado conserva ocorrência e árvore; entrada regenerada exige
conteúdo/tipos íntegros; callback recebe cópia sem poder alterar o envelope
guardado. Nenhum ouro, par ou ID de caso entra na chamada. Aspas incoerentes
não inventam foco nem certificam ausência. A aferição confia no shape de
métricas internas; resumo exige uma resposta por caso, IDs conhecidos únicos
e cobertura completa, não é importador genérico de resultados externos.

Painel: 16 fontes novas, seis pares nome/enunciado com conteúdo focal idêntico,
mais estado e ambiguidade explícita. P01A originalmente falava em “etiqueta”,
que também poderia conter instrução; auditoria mudou a fonte para designação
explícita **antes** do congelamento/geração. Nenhuma mudança pós-resultados.
É diagnóstico dirigido pelos REDs conhecidos, com revisão local, não humana
independente nem holdout do pipeline. Pergunta/enum são fixos; não foi
contrastada sensibilidade à sua ordem/apresentação.

SHA-256 congelados antes da geração:

- Fontes: `5a0c2f000024e2bfe92b4b4615379bef91ac8b9e8452d8fe2609c15d80febd48`.
- Revisão: `0f5517506fa0aaa3143d96028973fe35c80e904a72b8fc3401206ebcf6d60cea`.
- Sonda: `cfa1043d142a01dedaac2e1fb03f8c38e4bdc4686923b5bbdf94a91ae3146bf0`.

Qwen local real `qwen3:4b-instruct`, temperatura zero, 700 tokens; fonte e
saída completas em `resultados_testes/sonda_papel_trecho_v1_primeira.jsonl`.

| Revisão local do papel | Alinhados / total |
| --- | --- |
| Nome/designação | 3/6 |
| Operação mencionada | 5/6 |
| Expressão sem operação | 2/2 |
| Indeterminado | 0/2 |
| Todos os casos | 10/16 |
| Pares contextuais com ambos corretos | 2/6 |

Shape válido **16/16**, sem promoção. P01A (chave chamada), P02A (arquivo
chama-se) e P06A (peça chamada em citação aninhada) ainda recebem operação.
P03B, enunciado de pedido negado, recebe expressão sem operação; isso não
prova erro do normalizador de polaridade, que não foi medido. P08A vira nome
e P08B expressão, apesar de ambas as fontes deixarem a função indeterminada.
P04/P05 são os dois pares completos: há uso contextual correto em casos
específicos, não incapacidade universal do modelo nem solução generalizada.

Falsificações/limites: ausência de competição/reescrita e fonte integral
autêntica não eliminam erros de papel; esses fatores não são explicação
suficiente de todas as divergências. Não demonstra a causa interna exclusiva
de cada erro histórico. Não comparar 10/16 com 6/12: tarefa menor, foco
fornecido, métrica diferente. Essa sonda não resolve seleção externa de
L05/L11 nem foco entre várias operações de L06. **Somente pedir enum não foi
suficiente**, e rótulo intermediário não pode virar gate semântico automático.

Validação: três REDs da aferição — duplicata inflava válidos, ID desconhecido
lançava KeyError e cobertura faltante produzia placar parcial — reproduzidos
antes da guarda; GREEN após candidato mínimo. **43 testes novos e 638
regressivos relevantes verdes**; 83 focados com sobreposição, não somar.
Compilação/diff-check limpos, painéis antigos e produção preservados.
Nenhum treino, escrita de memória/vigência, integração, efeito externo,
runtime da Laylay ou commit. Não anunciar ensino/rede corrigidos.

Próximo contrato a estudar: proposta de vínculo contextual com evidência
literal, distinguindo trecho focal da relação exterior que explica seu papel.
Host verifica origem/ocorrência/contenção; proponente interpreta a relação;
modalidade decide autorização; executor/receipt continuam fora. Evidência
literal não certifica relação semântica e não deverá selecionar ação sozinha.
Só depois medir se isso ajuda **a mesma tarefa final**, em contraste novo,
preservando hipótese/negação/citação/ambiguidade e todo o contexto.

### P01: seleção externa antes do papel — desenho congelado (30/09)

Base de investigação: HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`,
branch `main`; mudanças paralelas de P16/runtime preservadas. Pesquisa e
planejamento encerrados antes do protótipo. Escopo exclusivamente offline,
sem editar as sondas congeladas, painel/revisão, produção ou treino.

Contrato a medir: primeira proposta contém só `evidencias`; host confere
origem, tipos, limites, ordem e disjunção do foco, sem propor papel. Somente
seleção literal não vazia permite segunda consulta de papel. Lista vazia
significa abstenção de seleção, não ausência nem papel `indeterminado`.
Segunda entrada conserva fonte/foco e acrescenta seleção literal autenticada;
verificador de papel não deve ser anunciado como dono dessas evidências.

Reuso: fonte/foco/tokenização, projeção `id/texto`, transporte local e
conferência de papel existentes. Não foi encontrada API neutra que aceite
intervalos externos: a guarda antiga exige papel. Nova guarda experimental
versionada, sem papel fictício e sem parser de linguagem, deve comprovar
equivalência diferencial da fronteira literal com a anterior. Não refatorar
o histórico para satisfazer este contrato novo.

Comparação dirigida com os mesmos 20 casos já vistos, não holdout novo:
controle acoplado contemporâneo contra seleção + papel condicionado. As 40
primeiras chamadas têm fonte/foco/tokens idênticos e ordem 10 AB/10 BA;
prompt/schema diferem por tarefa. Depois, até 20 chamadas de papel elegíveis.
Registrar custo real e todos os casos; não afirmar orçamento igual ou efeito
isolado do desacoplamento. Elegibilidade não consulta ouro/âncoras.

Validação planejada: RED do avanço sem seleção, guardas neutras/diferenciais,
transporte autêntico, contexto aninhado/repetido, recusa atômica, segunda
entrada adulterada, seleção vazia/inválida/consulta com erro, segundo papel
inválido e resumo completo recalculado. Métricas sobre todos os 20 mais
elegíveis condicionais, pares completos sobre oito, apoio/papel locais e
erros/custo por etapa. Literalidade e cobertura lexical nunca viram suporte
semântico, autorização ou promoção. Registrar resultados após a geração.

**Retomada e medição em 06/10/2026 — candidato não promovido.** HEAD/branch,
três dependências, painel/revisão e dois artefatos históricos conferidos sem
alteração. Worktree paralela mais ampla preservada. Instrumento novo:
`scripts/analises/sonda_vinculo_duas_etapas_v1.py`, SHA-256
`656c8d2174469a054d23c826a146085792471849f0e5213ada8eac5b230b68b0`.
Coleta exclusiva `resultados_testes/sonda_vinculo_duas_etapas_v1_ab_replay.jsonl`,
SHA-256 `5c188b8ec0c03847a1fa953d3d574ed5eb5536e085acd153c2ed1d779b91b240`:
42 linhas (metadata, 40 primeiras consultas, resumo); nenhuma segunda consulta.
Qwen local `qwen3:4b-instruct`, temperatura 0, até 700 tokens por consulta,
digest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`
igual nas leituras inicial/final, sem prova de invariância contínua.

| Medida sobre o painel inteiro | Acoplado contemporâneo | Duas etapas |
| --- | --- | --- |
| Casos e primeiras consultas | 20 | 20 |
| Seleções literais não vazias válidas | 0/20 | 0/20 |
| Listas vazias / propostas inválidas | 19 / 1 | 20 / 0 |
| Papel bruto alinhado localmente | 15/20 | não emitido: zero elegíveis |
| Pares com ambos os papéis brutos alinhados | 6/8 | não avaliados na segunda etapa |
| Envelope de papel válido / alinhado após conferência | 19/20 / 14/20 | não consultado |
| Cobertura de âncoras / papel e apoio locais alinhados | 0/20 / 0/20 | 0/20 / 0/20 |
| Consultas totais / duração acumulada | 20 / 44,676 s | 20 / 36,022 s |

O custo é soma das consultas, não latência do runtime ou orçamento igual
quando houver elegíveis. Zero erros de consulta. Q09A do controle propôs
`inicio=20, fim=20`: intervalo vazio e fora dos 15 tokens, rejeitado; papel nominal bruto correto
continua contado separadamente. As 20 propostas do candidato já chegaram
parseadas com lista vazia; a guarda não apagou intervalos. Isso é abstenção
permitida, não erro de parsing nem prova de contexto ausente. O transporte
reusado não fabrica `[]` em falhas; porém esta sonda preserva JSON parseado,
não HTTP/conteúdo bruto/motivo de término, limitando a auditoria da geração.

**Conclusão restrita:** separar a seleção do papel neste pacote não produziu
evidência no replay. Qualidade condicional da segunda etapa **não estimável**
(denominador de elegíveis zero), não acurácia zero nem fracasso demonstrado
do raciocínio condicionado. O 15/20 do controle contemporâneo difere do 14/20
da projeção histórica; não atribuir variação entre rodadas ao desacoplamento
nem afirmar determinismo por temperatura 0. É comparação de pacote, não
isolamento de prompt/schema; nenhum ganho semântico ou incapacidade geral
do Qwen foi demonstrado.

Validação do instrumento: **187 testes próprios**, **352 focados** incluindo
guardas históricas e **947 regressivos relevantes** GREEN (sobrepostos).
Além dos REDs anteriores do avanço/resumo, retomada reproduziu 19 REDs de
duração ausente/inválida ou avanço com duração não finita. Guarda no registro
de consulta exige número finito não negativo (sem bool); soma protegida
recusa transbordamento. Controles de zero/fração permanecem GREEN.
Compilação e `git diff --check` focados limpos. Essas provas são do instrumento,
não do desempenho semântico nem da composição real da Laylay.

Auditoria paralela somente leitura revalidou as entradas/flags/ordem e
recalculou o resumo das 40 propostas: coincidência integral. Rótulos brutos
divergentes no controle: Q01B, Q06A, Q06B, Q08A e Q08B; nenhum apagado.
Hashes atuais e dois artefatos históricos conferem, sem nova inferência.

**Próxima fronteira única:** contrastar o condicionamento da primeira geração
pelo schema restritivo versus JSON genérico, mantendo prompt/fonte/foco/tokens,
modelo e orçamento iguais; controle contemporâneo contrabalanceado, mesma
guarda host e registro de conteúdo bruto/parseado/motivo de término. Não
consultar ouro para entradas/elegibilidade, não forçar `minItems=1`, não
reparar intervalos nem abolir abstenção. Se ambos permanecerem vazios, tarefa,
apresentação e política de abstenção continuam confundidas; se surgirem
intervalos, separar emissão, literalidade e cobertura antes de significado.
Esse controle ainda **não foi implementado nem executado** nesta retomada.
P01 segue aberta; nenhuma produção, treino, memória, execução, fala ou
promoção neural alterada por este experimento. Nenhum commit.

### P01: schema da seleção — controle isolado, 06/10/2026

Desenho registrado antes da coleta. Mesma base `main/90a2fb8`, worktree
paralela preservada. Reuso integral de prompt de seleção, projeção fonte/foco/
tokens `id/texto`, painel/revisão de 20 casos e guarda literal de duas etapas.
Fonte e tarefa não mudam; diferença única na requisição: `format` contém
schema original ou a string `json`. Ambos conservam temperatura 0,
`num_predict=700`, consulta independente e timeout 90 s; ordem 10 AB/10 BA.
Não forçar lista não vazia, dar exemplos novos, reparar campos ou trocar ouro.
Arquivo novo `scripts/analises/sonda_schema_selecao_v1.py`, teste correspondente;
dependência de etapas travada por SHA-256, sem editar instrumentos anteriores.

Captura nova preserva status/texto HTTP antes do parse, conteúdo exato recebido,
envelope e finalização. Não promete bytes de transporte ou headers completos.
JSON inválido/não finito não é normalizado nem substituído por lista vazia.
Literalidade é medida separadamente da finalização: somente `done=true` e
`done_reason=stop` contam como seleção concluída; `length` mantém a proposta
observada, mas não certifica sua conclusão. Nenhuma segunda etapa ou ação.
Resumo relê o HTTP, valida requisição/host e preserva todos os 20 casos.

Hipóteses prévias: seleção válida só no JSON genérico sustenta influência do
campo de formato nesta configuração, não causa interna exclusiva do decoder
nem suporte semântico; emissão com intervalos inválidos separa produção de
coordenadas e literalidade; vazios concluídos nos dois braços deixam tarefa,
apresentação e política de abstenção abertas. Truncamento/erro impedem atribuir
um vazio ou resultado incompleto à interpretação semântica. Não interpretar
replay como holdout, nem treinar/liberar rede com esses resultados.

Validação prévia: três REDs da captura antes do parse no protótipo;
**44 testes novos, 396 focados** GREEN, sobrepostos com os históricos.
Uma falha adicional era wiring da própria fixture CLI (callback substituído
era chamado pela fixture com assinatura diferente), não falha do instrumento;
fixture passou a invocar a referência original sem alterar asserções.
Coleta planejada exclusiva `resultados_testes/sonda_schema_selecao_v1_ab_replay.jsonl`.
Resultados serão registrados após a geração, sem ajuste retroativo.

**Resultado coletado em 06/10 — não promovido.** Quarenta consultas reais
independentes ao Qwen local, 20 por braço. Requisições conferidas par a par:
somente `format` difere; ordem prevista 10 AB/10 BA, nenhum ouro enviado.
Todas HTTP 200, modelo declarado `qwen3:4b-instruct`, `done=true` e motivo
`stop`. Nos 40 conteúdos brutos há exatamente `{"evidencias": []}`: oito
tokens gerados por consulta, 160 por braço, sem truncamento observado.

| Medida | Schema restritivo | JSON genérico |
| --- | --- | --- |
| Casos / respostas JSON concluídas | 20 / 20 | 20 / 20 |
| Listas vazias | 20/20 | 20/20 |
| Emissões de intervalo / seleções literais válidas | 0/20 / 0/20 | 0/20 / 0/20 |
| Cobertura local concluída | 0/20 | 0/20 |
| Erros HTTP/parse / limite de tokens | 0 / 0 | 0 / 0 |
| Duração acumulada das consultas | 23,627 s | 18,873 s |

Resumo recalculado do HTTP/texto recebido coincide integralmente com o salvo;
requisições autênticas, 42 linhas, flags inertes e três artefatos históricos
reconferidos sem alteração. Não é auditoria humana independente. Digest
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`
igual nas leituras extremas; isso não certifica invariância contínua.
Script SHA-256 `7ffe58ee99016093081b359403f74bc33b3ac19a75bb97615059261a8575ae66`.
Artefato `resultados_testes/sonda_schema_selecao_v1_ab_replay.jsonl`, SHA-256
`a4fa8e2780d7af2c7f4fe2439bfce534cdbd2d604f9629479eccc77dc0a5aec6`.
**991 regressivos relevantes GREEN**, incluindo 44 novos/396 focados
sobrepostos; compilação e `git diff --check` focados limpos.

**Falsificações restritas:** remover as restrições de propriedades do schema
não basta para superar esse zero. Parse que apaga intervalos, corte de saída
ou falha HTTP não explicam os vazios desta coleta; eles já estão no conteúdo
recebido de respostas concluídas. Não prova que nenhum condicionamento de
formato tenha influência: o braço genérico ainda usa modo JSON. Tampouco
prova ausência de contexto, incapacidade do Qwen ou inutilidade de dois estágios.
Não estimar papel condicionado quando nenhuma seleção foi produzida. A
primeira fronteira RED observável continua na proposta do selecionador.

**Próximo controle mínimo, antes de novos ajustes semânticos:** verificar a
capacidade de emitir coordenadas numa extração literal explícita sem julgamento
de papel. Usar fontes sintéticas separadas, tokenizador/foco/guarda atuais e
um alvo textual solicitado na entrada, não índices/resposta pronta. Congelar
positivos (alvo único externo antes/depois do foco e expressão de vários tokens)
e negativos (ausente, apenas dentro do foco e ocorrência ambígua), com resultados
canônicos calculados pelo host antes da consulta. Isso calibra a primitiva,
não é novo gabarito semântico nem holdout de ensino. Não reutilizar pistas
de resposta do painel de 20 como alvo solicitado. Se positivos funcionarem,
falsifica incapacidade universal de emitir coordenadas e permite estudar a
tarefa de seleção contextual; se falharem, examinar protocolo/apresentação/
configuração sem culpar uma semântica que não foi exigida. Controle apenas
planejado aqui, não executado. Sem novos exemplos de treino ou promoção.

P01 permanece aberta. Nenhuma produção, fala, memória, executor, personalidade
ou influência da rede alterada neste controle. Nenhum commit criado.

### P01: extração literal explícita — calibração da primitiva, 06/10/2026

Desenho registrado antes da geração: seis fontes sintéticas novas, separadas
do painel semântico. Três positivos (antes, depois e vários tokens) e três
negativos (ausente, somente no foco, duas ocorrências externas). Correspondência
de grafia e espaços é literal, em limites de tokens; a unicidade é avaliada
após excluir o foco. Alvo textual solicitado integra a tarefa legítima, mas
índices/resposta esperada/tipo/ID de caso não chegam ao modelo. Não é aula,
interpretação de papel, alvo operacional, treino ou promoção neural.

Reuso de fonte/foco/aspas/tokenização/projeção/guarda e captura HTTP bruta.
Novo oráculo host enumerador de intervalos literais, não parser de linguagem;
confere disjunção pelo owner existente e aceita só uma ocorrência externa.
Referências calculadas e confrontadas com o painel congelado antes de consultar.
SHA-256 do painel `4265070356773ba82a093a211afbceb18d0181cc051a0d3acd526515973c3054`.
Script/teste novos `sonda_extracao_literal_v1`; fonte em
`scripts/analises/dados/sonda_extracao_literal_v1.json`. Dependência de captura
travada por hash, guardas históricas preservadas, sem refatorar instrumentos.

Doze consultas independentes, dois formatos e ordem 3 AB/3 BA; prompt/fonte/
foco/tokens iguais entre braços, só `format` muda. Prompt é tarefa literal nova,
logo placar não deve ser comparado como melhoria semântica sobre os 20 casos.
Qwen local, temperatura 0, até 700 tokens, timeout 90 s. Positivos e negativos
contados separados: lista vazia universal ganha zero nos três positivos,
não uma taxa agregada artificialmente favorável. Finalização normal exigida
para acerto concluído; metadados registram referências antes das consultas.

Dois REDs da referência no protótipo reproduzidos antes da guarda de escopo/
unicidade; **44 testes novos e 440 focados** GREEN, sobrepostos com históricos.
Testes incluem limites, grafia/espaços, alvo parcialmente dentro de palavra,
alvo dentro/fora do foco, aspas aninhadas, ambiguidade, HTTP/finalização/custo,
resposta salva adulterada, preservação do arquivo e não vazamento de índices.
Coleta exclusiva planejada `resultados_testes/sonda_extracao_literal_v1_calibracao.jsonl`.
Se positivos funcionarem, falsifica incapacidade universal de emitir
coordenadas; não prova seleção contextual. Se falharem, calibração continua
RED e protocolo/apresentação/configuração permanecem hipóteses abertas,
sem alegar incapacidade semântica. Resultados só serão anexados após geração.

**Resultado auditado — 06/10, calibração ainda insuficiente.** Doze consultas
HTTP200 ao Qwen local; todas JSON parseado, `done=true`, `done_reason=stop`.
Artefato com 14 linhas e referências host anteriores à geração. Ordem
3 AB/3 BA conferida; requisições diferem somente no formato, resumo recalculado
do HTTP bruto coincide com o salvo. Sem consulta adicional na auditoria.
Digest inicial/final igual ao das coletas anteriores, sem invariância contínua.

| Fronteira estrutural | Schema restritivo | JSON genérico |
| --- | --- | --- |
| Positivos alinhados e concluídos | 1/3 | 1/3 |
| Negativos alinhados e concluídos | 2/3 | 1/3 |
| Intervalos literais materializados | 1/6 | 1/6 |
| Erros HTTP/parse / truncamentos observados | 0 / 0 | 0 / 0 |
| Duração acumulada de consultas | 8,823 s | 4,157 s |

L01/L02, alvo único externo `lume` antes/depois, retornam listas vazias nos
dois braços. L03, `bruma clara`, retorna exatamente `[0,2)` em ambos,
materializado na fonte pelo owner existente. Isso falsifica incapacidade
universal de produzir coordenadas e falha universal do materializador; não
estabelece confiabilidade geral, preferência por vários tokens ou causa lexical:
esses três positivos não isolam tamanho, grafia e posição entre si.

Negativos: L04/ausente é vazio correto no schema e `{}` inválido no genérico;
L06/duas ocorrências é vazio correto em ambos. L05/alvo somente dentro do foco
gera `[9,13)` no schema e `[2,6)` no genérico, ambos fora dos cinco tokens
da fonte. Rejeição preservada, sem reparar ou reinterpretar esses índices
como caracteres. Não contar proposta sem envelope como abstenção correta.
Não atribuir automaticamente o intervalo errado à confusão de unidades;
isso é hipótese ainda não contrastada. Parser/HTTP/truncamento não explicam
as falhas desta coleta, observadas no conteúdo bruto de respostas concluídas.

**44 próprios, 440 focados e 1.035 regressivos relevantes GREEN**, sobrepostos.
Esses testes validam o instrumento, não os resultados do modelo. SHA-256:
script `2d7a8f1562967848a85e02b1afe21101c983b33ed4eee799ea7eb7fbf64e7d95`;
artefato `resultados_testes/sonda_extracao_literal_v1_calibracao.jsonl`,
`0745102a0353c5a24287366a3530d3d650cbe54ab9e8d7eab4d642a1320ddd91`.
Painel/dependências e artefatos de schema/duas etapas permanecem intactos.

**Próxima hipótese discriminável:** separar localização literal de emissão
numérica no mesmo alvo explícito, comparando cópia literal versus coordenadas.
Host continua dono de tokenização/ocorrência/offsets/disjunção; cópia só é
aceita quando autentica uma ocorrência externa única, sem normalização ou
reparo. Não usar o texto copiado como prova de papel ou ausência semântica.
Congelar antes os mesmos alvos/negativos e medir braços contemporâneos com
bruto, sem comparar diretamente a cópia semântica histórica de 29/09. Se
cópia localizar positivos que índices não localizam, sustenta dificuldade
na representação de saída nesta tarefa; se ambos falharem, não atribuir
a culpa exclusivamente às coordenadas. É apenas plano: contraste não
implementado/executado aqui, nenhuma migração para produção autorizada pelo
placar. Não multiplicar treinos ou acrescentar exemplos para mascarar o RED.

P01 permanece aberta. Nenhuma produção, personalidade, runtime, executor,
fala, treino, memória ou influência da rede alterada nesta calibração;
worktree paralela preservada e nenhum commit criado.

### P01: cópia literal versus índices, schema nos dois braços — 06/10/2026

Desenho congelado antes da geração, sem produção/treino. Reusa os seis casos
da calibração literal e suas referências host; replay conhecido, não holdout.
Schema fica nos dois braços conforme pedido de Pedro: vantagem histórica
restrita aos negativos (2/3 vs 1/3), positivos empatados e custo maior;
não comprova eficiência geral. Comparação contemporânea de representação,
sem misturar novamente JSON genérico. Mesma entrada/opções/Qwen; controle
índices mantém exatamente a requisição histórica restritiva. Cópia muda
instruções indispensáveis da saída e o schema para strings; portanto não é
troca de schema isolada. Ordem 3 AB/3 BA, HTTP bruto/finalização preservados.

Host reusa o enumerador literal de calibração e a guarda de intervalos para
materializar texto copiado: limites de tokens, grafia/espaços exatos, somente
ocorrência externa única. Sem normalização de caixa, escolha do primeiro
duplicado, conserto de índices ou aceite parcial. Ausência/ambiguidade de
uma cópia emitida é rejeição, não abstenção válida. Lista vazia explícita
continua permitida e não significa contexto ausente. Nenhum papel é inserido.

Alvo textual já vem na tarefa e pode ser ecoado: positivos de cópia isolados
não provam localização/raciocínio. Negativos ausente/foco/ambíguo e comparação
do host são obrigatórios. Separar literalmente autenticado de alvo alinhado,
e ambos da conclusão da geração. Se cópia superar índices, sustenta um
resultado do pacote de representação nesta tarefa, não mecanismo interno
único, ganho semântico ou liberação. Se positivos/negativos seguirem RED,
não migrar por sensação de formato melhor.

Instrumento novo `scripts/analises/sonda_copia_indices_literal_v1.py`, teste
correspondente, dependência de calibração travada por hash. Dois REDs do
protótipo (cópia ausente/ambígua virava vazio válido) reproduzidos antes do
candidato mínimo; **45 novos, 485 focados** GREEN, sobrepostos com histórico.
Coleta exclusiva planejada `resultados_testes/sonda_copia_indices_literal_v1_ab.jsonl`.
Nenhum índice pronto ou ID/tipo/gabarito de caso chega ao modelo; referências
calculadas antes das consultas e painel anterior intacto. Resultado será
registrado depois da geração sem ajustes retroativos.

**Resultado em 06/10 — contraste misto, nenhum braço promovido.** Doze
consultas reais/independentes, HTTP200/JSON/término normal `stop` em todas;
sem truncamento ou falha de transporte. Referências host anteriores à coleta,
ordem 3 AB/BA, entrada/opções idênticas e resumo recalculado do bruto conferidos.

| Fronteira estrutural | Índices com schema | Cópia com schema |
| --- | --- | --- |
| Positivos alinhados e concluídos | 1/3 | 2/3 |
| Negativos alinhados e concluídos | 2/3 | 1/3 |
| Literais materializados | 1/6 | 2/6 |
| Duração acumulada | 11,514 s | 7,611 s |

L01 vazio nos dois braços; L02 vazio nos índices e cópia `lume` autêntica;
L03 `[0,2)`/`bruma clara` corretos em ambos. L04 vazio correto em ambos.
L05/alvo apenas no foco: índices `[9,13)` fora dos cinco tokens, cópia `lume`
sem ocorrência externa, ambos rejeitados. L06/ambíguo: índices abstêm corretamente,
cópia `lume` rejeitada por duas ocorrências externas. Não apagar esses negativos
para promover a cópia. O conteúdo errado já está no HTTP bruto; guarda não
criou as propostas nem normalizou falta de ocorrência como abstenção.

**Conclusão limitada:** existe ganho de recuperação literal em um positivo
acompanhado de perda num negativo. Acertos completos totais empatam 3/6;
nenhum vencedor geral e nenhuma taxa generalizável nesta amostra conhecida.
L02 sugere sensibilidade ao pacote de representação, mas pode ser eco do alvo
fornecido; não prova que o modelo localizou a ocorrência nem que coordenadas
sejam a causa exclusiva de toda abstenção. L01 falha também na cópia, e L05/L06
mostram perda de restrição de escopo/unicidade. Não confundir autenticação
literal feita pelo host com compreensão/relevância/autoridade da proposta.
O controle de índices repetiu os estados históricos, sem garantia de determinismo.

**45 próprios, 485 focados e 1.080 regressivos relevantes GREEN**, sobrepostos;
compilação e diff-check focados limpos. SHA-256 do script
`fb9d6085e296e1d70c6f70ccf14c3ac97d3bb81616ec7f44b9eae6633897f2de`;
artefato `resultados_testes/sonda_copia_indices_literal_v1_ab.jsonl` (14 linhas),
SHA-256 `3e2eac546335f5332d2d59bd52bca0abd63c8c36653259a80da27a4229759f1a`.
Digest inicial/final `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`
igual, não invariância contínua. Painel/dependências/artefatos anteriores intactos.

**Direção arquitetural, não patch aprovado pelo placar:** dado um alvo literal
explícito, enumeração geométrica/offsets devem continuar no host; pedir à LLM
que refaça essa decisão conhecida não acrescentou confiabilidade. A lacuna P01
é escolher contexto relevante quando o alvo de apoio não vem pronto na entrada.
Próxima prova útil deve remover essa possibilidade de eco: comparar índices
com cópia de contexto no painel semântico congelado, fonte/foco completos,
schema em ambos, sem informar âncoras/alvo de evidência. Reusar validação
atômica de cópia externa e contar todo o denominador; cobertura lexical não
é suporte. Não avançar para classificação de papel sem seleção válida e
concluída, nem compensar rejeição pedindo ao modelo outra confirmação.
Esse próximo experimento ainda não foi implementado/executado. Não aumentar
treino ou integrar uma troca para cópia com base no empate estrutural.

P01 permanece aberta; não houve produção, treino, memória, personalidade,
executor, fala, runtime Laylay ou aumento de influência neural. Mesma base
`main/90a2fb8`, worktree paralela preservada e nenhum commit.

### P01: seleção de contexto sem alvo fornecido, cópia versus índices — 06/10/2026

**Protocolo anterior à coleta.** Reusar os 20 casos, as referências lexicais
e os oito pares congelados do painel contextual. Não fornecer alvo literal,
âncoras, papel esperado ou ID do caso ao modelo. Fonte, foco, aspas, tokens
ID/texto, opções e modelo são iguais nos braços; o controle de índices é a
requisição histórica de seleção com schema restritivo. No braço de cópia,
alterar somente instruções de representação e schema de evidências para
strings literais. Portanto, contraste de pacotes de representação, não
isolamento do efeito de schema. 40 chamadas independentes, ordem 10 AB/10 BA,
temperatura zero, sem reconsulta ou segunda etapa de classificação de papel.

Owner da autenticação/materialização continua no host: guarda externa neutra
para índices e guarda existente de cópia exata, única, externa, ordenada e
atômica. Cópia rejeitada não vira abstinência válida. Vazio continua revisão
pendente, não ausência comprovada. Cobertura lexical é calculada após a
resposta contra referência congelada, separada de seleção literal e de
finalização HTTP/stop. Não verifica significado, referente, efeito ou vigência.

Instrumentação: `scripts/analises/sonda_contexto_copia_indices_v1.py` e teste
correspondente. Capturar resposta HTTP textual antes do parse, preservar
requisição/entrada host, hashes, HEAD/branch/worktree e digest do Qwen.
Replay autentica painel, gold e requisição e recalcula a partir do bruto;
resumo exige todo o denominador. Arquivo de coleta exclusivo, sem sobrescrita.
Nenhuma mudança em produção, treino, personalidade ou autoridade neural.

Na primeira validação da instrumentação: 71 GREEN e um teste RED cuja
expectativa era incorreta. Em Q10B, `o` tinha só uma ocorrência externa;
a outra era interna ao foco e corretamente desconsiderada. Substituído por
Q04B, onde há duas ocorrências externas de `a`, mantendo a exigência de
rejeição atômica da ambiguidade. Não alterada a guarda para acomodar a fixture.

Coleta ainda não realizada no checkpoint pré-consulta acima. Artefato previsto:
`resultados_testes/sonda_contexto_copia_indices_v1_ab_replay.jsonl`.

**Resultado posterior à coleta — primeira fronteira ainda RED.** 40 consultas
reais ao `qwen3:4b-instruct` local: 20 índices vazios e 20 cópias recusadas,
zero seleção externa válida/concluída em ambos, zero cobertura lexical
autenticada e zero dos oito pares cobertos. Não vencedor de significado ou
seleção. As 40 respostas foram HTTP200, JSON parseável e `done=True/stop`,
sem erro de transporte ou truncamento; índices emitiram 160 tokens no total
e cópia 454. Durações acumuladas 48,986 s e 52,082 s, não benchmark de latência
ou eficiência geral. Digest igual nos extremos, não invariância contínua.

Auditoria manual dos brutos: todas as 20 cópias contêm o texto do foco. Em
14, a cópia ocorre literalmente na fonte, mas intersecta o foco; em seis,
as aspas externas curvas foram trocadas por retas e a cópia nem ocorre
exatamente na fonte (Q02A/B, Q04A, Q05A/B e Q06A). A guarda recusou sem
normalizar aspas, recortar o foco ou converter rejeição em seleção vazia.
Q01A devolve `“abra o baú”`, não `tem o nome`; Q04B devolve a frase inteira,
incluindo contexto e foco. Onze strings recusadas contêm lexicalmente as
âncoras esperadas. Esse diagnóstico do bruto não recebe crédito de cobertura
autenticada: sugere problema de delimitação/contrato de seleção e não autoriza
afirmar ausência geral de entendimento. Também não certifica papel ou suporte.

Fronteira observada: requisição autêntica → HTTP/JSON/finalização GREEN →
proposta de contexto externo RED, antes de materialização utilizável e antes
de papel. Mudar índices para cópia não resolveu a tarefa sob este pacote;
parsing, término por limite e perda da resposta no host foram falsificados
como explicação desses 40 resultados. Não identificada uma causa interna
única do modelo ou do prompt. Sem relaxar a proteção ou chamar segunda etapa
para compensar o RED. Produção não foi corrigida nem investigada por este replay.

Prova do instrumento: **72 próprios, 557 focados e 1.152 regressivos relevantes
GREEN**, conjuntos sobrepostos. Uma fixture foi corrigida conforme checkpoint;
nenhum patch em guarda compartilhada/produção. Replay recalculado dos brutos,
42 linhas, 20 IDs em dois braços, ordem 10 AB/BA, referências pré-consulta,
autenticidade das requisições e aferições conferidas. Baseline HEAD
`90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`, worktree paralela preservada.
SHA-256 do script
`688390e78582949caeeff5fb2ba2c72b3735273c5afa391f311c1f3aec1afa9b`;
do artefato
`7ee84d1406ea1d24c3751f6df201bb1298c7b45ddec194cc2d09af03bc4c4bc0`.

Próxima fronteira proposta, não implementada: tirar da LLM a geometria que o
host já conhece. Enumerar por posição **todos** os trechos externos ao foco,
sem selecionar/rankear por gold, apresentar fonte/foco e esses candidatos
autênticos e pedir apenas IDs de apoio. Comparar com o controle congelado;
host continua conferindo autenticidade, disjunção e ordem. Isso testa
delimitação versus escolha, sem fornecer o trecho certo e sem trocar
literalidade por prova semântica. Não avançar treino ou influência neural com
este resultado; P01 continua aberta e nenhum candidato foi promovido.

### P01: host delimita contexto externo, modelo propõe IDs — 06/10/2026

**Protocolo congelado antes da coleta.** Mesmo painel de 20 casos, oito pares,
referências e controle de índices históricos. Novo braço apresenta todos os
blocos maximais de tokens externos ao foco, em ordem da fonte, como IDs/textos.
Enumeração posicional, sem gold, classificação linguística ou ranking; tokens,
fonte, aspas e foco permanecem iguais. Não remover foco de resposta inválida:
os candidatos são gerados pelo host **antes** da consulta, não reparo posterior.

Reuso do tokenizer/materializador e da guarda neutra existentes. Novo contrato
de IDs exige inventário host autêntico, IDs existentes/tipados, ordem, unicidade,
até dois itens e recusa atômica; não ordenar, deduplicar ou converter ID errado
em vazio. O inventário é de trechos, não de referentes: não substituir nem
publicar no `InventarioContextual` de identidades/vigência. Sem efeitos,
classificação de papel, memória, treinamento ou produção alterada.

40 consultas independentes ao Qwen local, 10 AB/10 BA, schemas em ambos,
mesmas opções. Mudam inventário na entrada, instrução de representação e schema:
é comparação de pacotes, não prova isolada da geometria. Captura textual HTTP
bruta antes do parse e metadados/referências pré-consulta; replay integral.

Controle sem LLM seleciona todos os candidatos e já obtém **20/20 literalidade
e cobertura lexical** antes da coleta. Nesse painel há no máximo dois blocos:
selecioná-los todos pode obter cobertura sem escolher o apoio relevante. Medir
quantas propostas selecionam todos; nenhuma dessas métricas verifica significado.
Um ganho estrutural contra índices não demonstrará seleção semântica superior.

Instrumento: `scripts/analises/sonda_contextos_enumerados_v1.py`, teste
correspondente; **60 próprios GREEN**. Artefato previsto, ainda não coletado
neste checkpoint: `resultados_testes/sonda_contextos_enumerados_v1_ab_replay.jsonl`.
Primeiro RED que motivou a hipótese permanece a coleta anterior (índices
vazios/cópias sobre o foco), não falha inventada no teste do novo instrumento.

**Resultado posterior à coleta — GREEN estrutural, não seleção semântica.**
40 chamadas reais: controle de índices 20 vazios; IDs 20 seleções externas
literais válidas/concluídas, 40 trechos materializados, cobertura lexical
20/20 e oito pares cobertos. Os brutos do braço novo são, em todos os casos,
`{"evidencias": ["e0", "e1"]}`: seleciona todos, tal como o controle sem LLM.
O denominador não exclui abstenções/falhas. Não há superioridade demonstrada
contra o baseline de contexto completo, nem evidência de escolha discriminativa.

Todas as 40 respostas HTTP200/JSON/`done=True/stop`, sem erro/truncamento.
Índices 160 tokens de saída, IDs 280; duração acumulada 48,127/53,211 s, não
benchmark geral. Digest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`
igual nos extremos, não prova de invariância contínua. Replay verifica hash,
requisições/host/inventário/gold, 42 linhas/40 consultas, ordem 10 AB/BA,
resumo recalculado e cada trecho igual à fonte e disjunto do foco. O bruto
histórico anterior também foi autenticado/recalculado, sem modificá-lo.

**60 próprios, 617 focados, 1.212 regressivos relevantes GREEN**, conjuntos
sobrepostos. Nenhuma alteração de produção ou das guardas históricas. Baseline
HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`, worktree paralela
preservada. SHA-256 do script
`9e012ce7e08a176f63c6c87d754678de5bf22bd9a8bcd20c7b37b7b4b34e384f`;
do artefato
`506bcd57356b53ab5f54621f5f7d1d1471ffb631d7f27316debcb73c9cfd9905`.

Conclusão causal limitada: o pacote de IDs sobre geometria autenticada produz
seleção utilizável onde o controle livre não produz. Não prova que geometria
seja a causa interna exclusiva, pois entrada/instrução/schema diferem. Mantém
o owner correto: host conhece limites, modelo propõe uso. Falsifica incapacidade
universal de emitir uma seleção aceita, não comprova interpretação de papel.
P01 permanece aberta; inferência real no Ollama não é runtime da Laylay.

Próxima decisão proposta, não executada: parar de avaliar escolha pelo mero
20/20 lexical. Contexto externo completo fornecido pelo host é o baseline
mais simples, sem seletor neural obrigatório. Comparar, no mesmo painel,
classificação de papel com fonte/foco completos versus fonte/foco com esse
contexto externo explícito, sem pedir outra seleção. Referências congeladas,
pares contrastivos e casos indeterminados avaliam a conclusão, não o formato.
Somente manter um seletor adicional se houver benefício próprio contra o
baseline; para prová-lo depois será necessário painel discriminativo com
distratores/ausência de apoio, congelado antes de consultar o modelo. Não
forçar essa evidência no painel atual nem liberar rede por métricas estruturais.

### P01: papel com fonte integral versus contexto externo explícito — 06/10/2026

**Protocolo anterior à coleta.** Mesmo painel de 20 casos, referências locais
e oito pares contrastivos congelados. Classificação independente, sem selecionar
evidências ou carregar a proposta de uma chamada anterior. Controle usa a
entrada canônica `papel.preparar_entrada`: fonte integral, foco e aspas. Não
fornecer tokens em nenhum braço: nesta tarefa o modelo não calcula intervalos.
No outro braço acrescentar somente `contextos_externos`, IDs/textos de todos
os blocos externos autenticados pelo host, sem ranking/âncoras/gold.

Prompt `papel.SISTEMA`, schema `papel.FORMATO`, modelo, opções e fonte/foco
iguais; diferença **somente um campo da entrada**, sem instrução extra no
sistema. 40 chamadas reais locais, 10 AB/10 BA, temperatura zero, limite
700 tokens, sem reconsulta ou seletor neural. A classificação do papel é
proposta, não apoio semântico, referente, autorização ou efeito.

Reusar enumeração, tokenização/materialização, guarda de papel e captura HTTP
existentes. Aferição confere fonte/foco/inventário/requisição, tipos/flags,
HTTP bruto, shape e finalização; crédito de acerto exige envelope válido e
término confirmado. Resumo exige todos os casos em ambos os braços, recalcula
do bruto e conta ganhos/perdas pareados, oito pares completos, confusão e
denominadores por papel. `indeterminado` só alinha onde a referência o exige.

Não comparar números diretamente com calibração de seis casos ou painéis
anteriores com tokens/saídas acopladas: as 40 chamadas contemporâneas são o
contraste. Painel já reutilizado, não holdout novo nem prova de generalização.
Fonte integral sem campo extra continua baseline mais simples; só acrescentar
complexidade se aparecer benefício comprovável, sem promover resultados para
treinamento ou runtime.

Instrumento `scripts/analises/sonda_papel_contexto_explicito_v1.py` e teste
correspondente: **74 próprios GREEN**. Nenhuma produção ou guarda histórica
modificada; hipóteses motivadas por coleta real anterior, não RED artificial.
Artefato previsto, não coletado neste checkpoint:
`resultados_testes/sonda_papel_contexto_explicito_v1_ab_replay.jsonl`.

**Auditoria concluída em 07/10 — empate, contexto explícito não promovido.**
Coleta preservada com data de contexto 06/10 nos metadados, sem reescrever
script/artefato após a virada do dia. As 40 classificações reais produziram
HTTP200, JSON/envelope válido e `done=True/stop`; sem falha de transporte ou
truncamento. Fonte integral **11/20** alinhados e **3/8** pares completos;
contexto explícito **11/20** e **3/8**. Pares corretos Q04/Q09/Q10 nos dois.
Comparação por ocorrência: um ganho, uma perda, dez acertos em ambos, oito
erros em ambos. Todos os casos permanecem no denominador.

| Papel esperado local | Total por braço | Fonte integral | Contexto explícito |
| --- | ---: | ---: | ---: |
| nome/designação | 8 | 4 | 5 |
| operação mencionada | 8 | 5 | 4 |
| expressão/estado sem operação | 2 | 2 | 2 |
| indeterminado | 2 | 0 | 0 |

Ganho Q03A: `O modo recebeu o nome “não suspenda a faixa”.` deixa de ser
expressão sem operação e vira nome. Perda Q05B: o foco interno a uma citação
com `como ordem de exemplo` deixa de ser operação mencionada e vira nome.
Q01B/Q06B mudam para outro rótulo igualmente errado; não são ganhos.
Q08A/B permanecem nome/expressão, respectivamente, apesar de a fonte declarar
que não distingue nome de instrução. Não reinterpretar esses erros como
abstenção nem revisar a referência depois de ver o resultado.

Primeira fronteira RED observada agora: fonte/foco/contextos autênticos →
transporte e shape GREEN → atribuição do papel contextual RED. Os rótulos
errados já constam do conteúdo HTTP recebido, antes da guarda de papel.
Falsificados parsing/rejeição posterior/truncamento como explicação dos
erros desta coleta. A duplicação explícita do contexto não é suficiente para
resolver o contrato semântico. Não demonstrada uma causa interna exclusiva
de Qwen/prompt, nem um bug do runtime da Laylay.

**74 próprios, 691 focados, 1.286 regressivos relevantes GREEN**, conjuntos
sobrepostos. A primeira tentativa da regressão ampla não produziu resultado
de pytest por interrupção na execução de processos; na retomada de 07/10,
rerun confirmou 1.286 GREEN. Não contar a tentativa interrompida como GREEN
ou RED do contrato. Replay integral recalculou resumo, aferições, confusão,
gold/req/host/inventário, 42 linhas e ordem 10 AB/BA. Prompt/schema/opções
iguais e única diferença de campo conferidos nos testes.

Tokens de saída 228/224; duração acumulada 18,792/18,507 s. Não inferir
eficiência geral de uma coleta. Digest igual nos extremos, não determinismo
ou invariância contínua; não comparar 11/20 diretamente com resultados
anteriores de tarefas/input diferentes. BASE continua integralmente falsa.
HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch `main`, produção e
worktree paralela preservadas, nenhum commit. SHA-256 do script
`e702fcb8876f54c1354f8e8dcc0ce8305cf5ddc64a3bcbafce8170be85ee56fe`;
do artefato
`6f5329010a4815ee37a9d97227e5aa9cb981e742e8138b8ce4f8020cfdda425d`.

Decisão: não acrescentar este campo em produção ou treinar com os rótulos
gerados por ele. Fonte/foco integral permanece o controle simples. Próxima
fronteira de estudo, não implementada: testar a interpretação do **predicado
que enquadra o foco** e indeterminação, separada da aparência de ordem,
negação e autorização. Casos Q02A/Q03B/Q05A/Q06A/Q08 mostram por que essa
hipótese merece contraste; não provam que sejam uma única causa. Antes de
alterar prompt de produção, comparar a mesma tarefa de papel com uma leitura
contextual mais direta, sem exigir geometria/novas etapas e sem exemplos do
painel ou gabarito no prompt. Preservar controles de nome versus menção,
foco aninhado, operação fora do foco e referência explicitamente indeterminada.
P01 aberta: literalidade resolveu-se nesta interface, semântica não.

### P01: pergunta direta pelo nome, protocolo pré-consulta (10/10)

HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, `main`, worktree suja
preservada. `sonda_pergunta_direta_v1.py`: mesmos 12 casos conhecidos e ouro de
referente do painel anterior; 2 braços × 2 rodadas = 48 consultas locais. O
controle `abstrato` é exatamente o pedido anterior de `referente`. `direto`
troca esse enquadramento por uma instrução única de resposta extrativa e
`Qual é o nome do projeto/festival/curso?`, derivada só da relação literal.
Fonte, relação, demais metadados, ausência de catálogo no modelo, mapa do host,
modelo, orçamento, schema e aferição preservados. Muda o pacote de formulação
(sistema + pergunta no lugar do seletor de tarefa), não apenas uma palavra.

Adaptador limitado ao molde do painel, fail-closed fora dele; não é parser
genérico nem implementação de geração de perguntas no runtime. Não envia ouro,
nome-resposta ou flag de indeterminação. Nenhum exemplo resolvido no prompt.
Rodada 2 inverte ordem; sem retries, API externa, treino ou produção alterada.
Começa pelos controles diretos antes dos casos de anáfora/incerteza. Medir
alinhamento e cópia separadamente: determinado 9 casos, indeterminado 3. Comparar
requests e respostas do controle com artefato anterior; auditar HTTP bruto,
ordem, mapas, hashes, digest e resumo antes de contar.

Hipótese: enquadramento abstrato do pedido favorece entidade/atributo em vez
do valor nomeador. Ganho no braço direto sustentaria contribuição do adaptador,
não incapacidade geral do modelo nem prontidão de produção. Se os dois falharem,
não insistir que o rótulo sozinho explica o RED. Preservar incerteza e rejeitar
reparos silenciosos, alterações pós-consulta do ouro ou uso como treino.

### P01: discriminação de menção e referente, protocolo pré-consulta (10/10)

HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, branch `main`, worktree suja
preservada. `sonda_mencao_referente_v1.py`, somente diagnóstico offline. Não
comparar o percentual diretamente com painéis anteriores: tarefa, prompt e
casos mudam. A comparação causal aqui é entre duas tarefas na **mesma fonte**,
com sistema, schema, orçamento e metadados iguais; só muda `tarefa` no input.

48 consultas: 12 fontes novas × 2 tarefas × 2 rodadas. Três famílias lexicais
(projeto/festival/curso), cada uma com sujeito citado direto, anáfora primeira,
anáfora segunda e anáfora explicitamente não resolvida. Casos novos, mas moldes
similares aos anteriores: não são prova de generalização ampla. Na tarefa
`mencao`, copiar o sujeito local; em `referente`, copiar a expressão nomeada,
ou declarar `indeterminado` se a fonte não a determina. Indeterminação não é
cópia literal nem abstenção técnica; não aprova a tarefa de menção. O esquema
comum contém só `resposta`; a referência escrita pode ser localizada mesmo
quando seu referente permanece indeterminado.

Fonte integral e relação literal em ambos. Catálogo omitido do modelo, mapa
completo autenticado no host. Ouro pré-consulta separado por tarefa e reservado
à aferição; sem envio da menção esperada, do referente ou do estado esperado.
Preservar guardas de literalidade e posição, sem normalizar a saída. Rodada 2
inverte ordem; sem retries. Medir tarefas separadas e **par completo**: acertar
referente não compensa menção errada. Contar também se a mesma resposta é usada
nas duas tarefas quando os alvos esperados diferem. Casos diretos são controles
onde as duas respostas podem legitimamente coincidir.

Hipóteses concorrentes: confusão entre tarefas, dificuldade de cópia/recorte,
e resolução indevida da incerteza. A coleta deve separá-las sem declarar causa
interna única. Guardar HTTP bruto/requests/ordem/hashes/digest e recalcular
resumo antes de interpretar. Nenhum resultado autoriza efeito, treino,
integração, geração automática dessas tarefas ou liberação da rede.

#### Resultado auditado de menção versus referente (10/10)

Artefato `resultados_testes/sonda_mencao_referente_v1.jsonl`, SHA-256
`70515d722db95b84aca1d0a062366d7af6fc2723a7f6aaa14df3e92d6bf042a5`.
Script SHA-256 `2805358081ca417e8b17bd093f671edc75284c9356a1abe3ef07646bd2fb1b67`.
48 consultas/50 linhas auditadas: casos/ouro pré-consulta, ordem, requests,
mapas do host, HTTP bruto, resumo e pares recalculados. Todas HTTP 200/done/stop;
máximo 14 tokens gerados. Digest inicial/final do `qwen3:4b-instruct`:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
24 pares de repetições tiveram conteúdo idêntico. Sem retries ou API externa.

| Medida por rodada (duas iguais) | Menção | Referente |
| --- | --- | --- |
| Shape válido | 12/12 | 12/12 |
| Cópia literal localizada | 8/12 | 9/12 |
| Alinhamento ao ouro pré-consulta | 8/12 | 2/12 |
| Indeterminação declarada | 0 | 2 |
| Abstenção técnica | 0 | 0 |

**Pares completos: 0/12**. Os dois acertos de referente são `F_incerto` e
`C_incerto`, não resoluções de nomes. Referentes determinados: 0/9; casos
indeterminados: 2/3. Não somar `indeterminado` como cópia literal.

Menção: P_segunda e os três incertos retornaram as palavras esperadas, mas com
`a`/`uma` minúsculos em vez de `A`/`Uma`; são quatro falhas estritas de cópia,
**não quatro provas de confusão semântica**. Essa leitura qualitativa posterior
não altera o placar nem relaxa o ouro. Os demais oito recortes são literais e
alinhados. Não alterar guardas para absorver a mudança de capitalização.

Referente: P_direto devolve `projeto`; F_direto e F_segunda devolvem `festival`;
C_direto e C_segunda devolvem `curso`. P_primeira/P_segunda/P_incerto devolvem
`o nome do projeto`; F_primeira devolve `o nome do festival`. C_primeira devolve
`a primeira dessas expressões` (referência não resolvida e não literal na caixa).
Todos são resultados diferentes da expressão concreta nomeadora pedida. Erro
já aparece no controle direto, sem necessidade de resolver anáfora: não atribuir
tudo a memória, distância contextual ou resolver pronominal.

**Falsificado no painel:** ignorar a tarefa e repetir a mesma resposta nas duas
solicitações (0/12 pares de saídas iguais); falha de HTTP/truncamento; e cópia
como explicação suficiente dos erros de referente (nove trechos são literais,
mas inadequados). Mudar resposta não prova entender corretamente a tarefa.
**Ainda aberto:** o contrato textual abstrato de `referente` pode estar levando
à seleção da entidade nomeada ou do atributo “nome”, em vez do valor atribuído.
Isso é hipótese sobre enquadramento da tarefa, não causa interna única provada
nem evidência de incapacidade geral do modelo. O padrão contém respostas
distintas e não deve ser contado como uma só categoria de erro sem justificativa.

**Próxima fronteira causal:** antes de encadear mais campos/etapas, comparar o
pedido abstrato com uma pergunta direta, como “Qual é o nome do curso?”, usando
as mesmas fontes, representação e anotação de expressão concreta/indeterminado.
Começar pelos controles diretos, que já falham sem anáfora. Se a pergunta direta
funcionar e a abstrata não, revisar o adaptador da tarefa; se ambas falharem,
não atribuir a falha apenas ao rótulo. Preservar os casos incertos como negativos.
Não treinar com saídas atuais, reparar cópia silenciosamente, ou promover esta
sonda a gate. O plano continua offline; P01 aberta.

16 testes focados passaram (25,66 s). Regressão com ablação, pergunta relacional,
argumento isolado, contrastes e ligação: **83 passed em 136,40 s**. Não é suíte
completa nem validação de composição/runtime. Esta frente alterou somente
sonda, testes e documentação, sem produção, configuração, treino ou commit.

### P01: ablação do catálogo de citações, protocolo pré-consulta (10/10)

HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, branch `main`, worktree suja
preservada. Hipótese: enumerar citações no input favorece selecionar referentes
em vez das menções pedidas. Teste offline, não remoção de segurança da Laylay.

`sonda_ablacao_catalogo_v1.py`: mesmos 13 casos e perguntas do experimento
anterior, sem novo holdout, 2 braços × 2 rodadas (52 consultas). `catalogo`
reproduz a candidata anterior. `sem_catalogo` omite **somente** a propriedade
`aspas_sintaticas.regioes_entre_aspas` enviada ao modelo; não envia lista vazia
como afirmação de ausência. Fonte integral com suas aspas, âncora, pergunta,
demais metadados, sistema, schema de cópia, modelo e orçamento iguais. O sistema
retém a instrução negativa sobre IDs q para não mudar outra variável. O teste
avalia o pacote catálogo (textos, IDs, offsets e parentesco), não cada subcampo.

O host reconstrói, armazena e autentica o mapa completo nos dois braços. A
materialização literal, ambiguidades, offsets e revisão local são os mesmos;
ouro não é enviado. Painel/anotações congelados antes de consultar. Repetição
inverte ordem, sem retries, sem API externa, sem treino ou runtime Laylay.
Auditar requests/HTTP/ordem/hashes/digest e recalcular resumo; medir literalidade,
alinhamento, abstenção e perdas além do total. `grupo=novo` identifica apenas a
origem histórica dos seis casos adicionais: agora todos já são conhecidos.

Se a ablação não corrigir menção/alternativas abertas, rejeitar catálogo como
explicação suficiente, sem declarar ausência total de influência. Mesmo se
houver ganho, não promover a saída a prova nem remover mapa de produção.

#### Resultado auditado da ablação do catálogo (10/10)

Artefato `resultados_testes/sonda_ablacao_catalogo_v1.jsonl`, SHA-256
`a9af3e87cccb9014f2a18d82a9cf0372bf8a7ebbbd9f0be2bee97f8078b54ba3`.
Script SHA-256 `e64fa4bb58cb0079edd8f4dd310ccc0e971bdf36329a4d67945b7579582fca54`.
52 chamadas/54 linhas auditadas: painel pré-consulta, ordem, requests, mapas do
host, HTTP bruto e resumo recalculado íntegros. Todas HTTP 200/done/stop; máximo
39 tokens gerados, sem esgotar 700. Digest inicial/final de `qwen3:4b-instruct`:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
26 pares repetiram as respostas entre rodadas; os 26 controles reproduziram
requests e respostas do braço `pergunta` anterior. Sem retries ou API externa.

| Medida por rodada (duas iguais) | Com catálogo | Sem catálogo |
| --- | --- | --- |
| Shape válido | 13/13 | 13/13 |
| Cópia literal localizada | 13/13 | 11/13 |
| Menção alinhada à revisão local | 6/13 | 7/13 |
| Abstenção | 0 | 0 |

Ganho de alinhamento somente U1, sem perdas de alinhamento nos seis casos que
já passavam (N0,N1,D0,D1,C0,C1). Houve perda de literalidade em U2 e O0.
Respostas mudaram em U0/U1/U2/O0/A0/A1/C1; mudança de delimitadores em C1 não
mudou aprovação local. Casos originalmente novos são agora controles conhecidos,
não outra evidência de generalização independente.

REDs sem catálogo: U0 copia a coordenação das duas citações em vez da menção
`qual dessas expressões`; não selecionar uma única alternativa já não equivale
a cumprir a tarefa. U2 devolve a menção com `a` minúsculo, separando falha de
cópia da interpretação. O0 copia a fonte inteira e troca aspas curvas por retas;
O1 mantém a oração inteira, incluindo predicado e alternativa negada. A0 mantém
o referente; A1 passa à oração `A segunda dessas expressões identifica o projeto`,
maior que o sujeito pedido. Não corrigir por recorte heurístico ou aceitar ouro
mais amplo depois de observar a saída.

**Conclusão causal limitada:** o pacote catálogo influencia a seleção neste
painel (requests só diferem por essa propriedade), mas não é explicação
suficiente para os REDs de menção/escopo. A hipótese “basta retirar o catálogo”
foi falsificada; influência de subcampos individuais e mecanismo interno não
foram isolados. Sem erro de transporte ou limite de geração que explique o
resultado. Guardas, mapa do host e fonte foram preservados; não alterar produção
ou promover esta variante, apesar do ganho líquido de um acerto.

**Próxima fronteira:** revisar a distinção entre tarefas, não acumular mais
variações deste prompt. Preparar pares mínimos com a mesma fonte e duas
solicitações explicitamente diferentes: localizar a menção textual versus
resolver aquilo a que ela se refere. Anotar menção, referente e indeterminação
separadamente antes da consulta; manter cópia literal e interpretação em medidas
distintas. Isso pode testar se o modelo discrimina a tarefa, sem supor que um
referente plausível satisfaz extração literal ou que anáfora autoriza ação.
Não alimentar certeza/execução com saídas desta sonda. Perguntas permanecem
manuais; P01 aberta, sem evidência de runtime Laylay.

14 testes focados passaram (23,19 s). Regressão com pergunta relacional,
argumento isolado/escopo, contrastes e ligação: **80 passed em 136,38 s**.
Isso valida os contratos locais, não composição ou runtime Laylay. Esta frente
alterou somente sonda, testes e documentação; sem produção, treinamento,
configuração ou commit.

### P01: pergunta relacional explícita, protocolo pré-consulta (10/10)

Mesmo HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, `main`, worktree suja
preservada. `sonda_pergunta_relacional_v1.py` testa a hipótese concorrente de
subespecificação do papel procurado no pedido de “argumento”. Não é patch de
produção, treinamento nem substituição do sistema de linguagem da Laylay.

52 chamadas locais: 7 casos conhecidos e 6 novos, 2 braços × 2 rodadas. Controle
preserva integralmente o pedido `copia` anterior. Candidata acrescenta apenas
pergunta relacional pré-escrita no input e instrução para usá-la; fonte, âncora,
mapa de aspas, schema de cópia, modelo, temperatura e orçamento são preservados.
As perguntas identificam papel (sujeito de atribuição, complemento de nomeação
ou conteúdo comunicado), não trecho-resposta, ID ou offsets esperados. Casos
novos contrastam duas relações diretas, primeira/segunda referência e relato
externo/conselho interno. Revisão local pré-consulta no script; não vai ao modelo.
Variantes de artigo e delimitadores seguem o protocolo anterior. Capitalização,
posição, ambiguidades e literalidade permanecem rigorosas, sem reparo de saída.

Medir shape, literalidade, abstenção, alinhamento local e repetibilidade; separar
casos conhecidos dos novos. Rodada 2 inverte ordem; sem retries. Conservar HTTP
bruto e auditar artefato antes de contar. Comparação testa pergunta + instrução
de papel, não identifica mecanismo interno do modelo. Perguntas foram escritas
para o painel, **não geradas pelo runtime**; eventual ganho não prova capacidade
de formular a pergunta correta em produção, de resolver certeza ou de autorizar.
Se o papel explícito não melhorar seleção, não acrescentar mais etapas em cima
dessa saída. Se melhorar, localizar os REDs restantes antes de generalizar.

#### Resultado auditado da pergunta relacional (10/10)

Artefato `resultados_testes/sonda_pergunta_relacional_v1.jsonl`, SHA-256
`02d742e2e6a721e41403cc3e0dc904afdbacaf285edf994dfbe896bafe64f6b0`.
Script SHA-256 `31449aeadb11fe6287a89071b62c2c5cd80eb5767238f5137a07112488a1091c`.
52 consultas/54 linhas auditadas: metadata, painel pré-consulta, requests, ordem,
HTTP bruto e resumo recalculado. Todas HTTP 200/done/stop; máximo 25 tokens
gerados, abaixo de 700. Digest inicial/final de `qwen3:4b-instruct`:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
As 26 duplas repetiram conteúdo byte a byte; os 14 controles históricos também
repetiram requests/respostas anteriores. Sem retries, API externa ou runtime.

| Medida por rodada (duas iguais) | Controle | Pergunta explícita |
| --- | --- | --- |
| Shape válido | 13/13 | 13/13 |
| Cópia literal localizada | 10/13 | 13/13 |
| Menção alinhada, conhecidos | 1/7 | 2/7 |
| Menção alinhada, novos | 1/6 | 4/6 |
| Menção alinhada, total | 2/13 | 6/13 |
| Abstenções | 0 | 0 |

Cinco ganhos (N0,N1,D0,C0,C1), uma perda (U0), D1 preservado. O conteúdo de
fala externa/interna foi distinguido nos dois pares N e C; a mesma pergunta de
conteúdo funciona com verbos e fontes diferentes. Isso sustenta benefício
local da indicação de papel, não um contrato geral já suficiente.

REDs: U0/U1 retornam `“polir o sino”`; U2 `“trocar a corda”`; A0/A1
`“suba a torre”`/`“cruze o rio”`, em vez das menções anafóricas pedidas.
U1/U2/A0/A1 apontam referentes plausíveis, mas violam a tarefa de localizar a
menção. U0 é mais grave: escolhe alternativa apesar da indeterminação explícita.
O0 escolhe `“varra o cais”`, ignorando a alternativa ausente; O1 copia a oração
inteira, incluindo relação e alternativa negada, não apenas o complemento.
Não agrupar falha literal de U2/A0 no controle com erro semântico: eram trocas de
capitalização. A candidata copia literalmente nos 13 casos, mas sete seleções
não atendem à anotação de papel/menção. Literalidade não resolve a interpretação.

**Falsificações:** transporte, truncamento e simples falta de informação não
explicam o conjunto; N/C mostram que a relação interna pode ser distinguida
quando o pedido explicita conteúdo. Porém explicitar papel não é suficiente
para preservar menção e alternativas abertas. A causa interna continua não
isolada, e o ganho veio acompanhado de regressão em U0; candidata rejeitada
como gate, treino ou saída validada para próxima etapa.

**Próxima fronteira causal:** investigar seleção da menção antes da resolução
do referente. Hipótese concorrente: o catálogo de citações no input favorece
selecionar os objetos já enumerados. Teste recomendado: mesma fonte integral,
pergunta e schema de cópia, com/sem catálogo enviado ao modelo; manter o mapa
canônico no host para validação e não remover proteção de produção. Incluir
contrastes equivalentes diretos/anafóricos e alternativas abertas, sem gerar
perguntas automaticamente nem acrescentar certeza sobre uma seleção não provada.
Se a ablação não resolver, revisar a especificação da tarefa em vez de repetir
mais exemplos iguais. Perguntas do painel continuam manuais, não uma capacidade
implementada no runtime. P01 aberta.

14 testes focados passaram (24,61 s). Regressão com seleção isolada,
argumento/escopo, contrastes e ligação: **66 passed em 114,16 s**; não é suíte
completa nem prova de composição/runtime. Esta frente alterou apenas sonda,
testes e documentação; nenhum commit e nenhum arquivo de produção alterado.

### P01: seleção isolada do argumento, protocolo pré-consulta (10/10)

Continuação offline na mesma raiz, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`,
branch `main`, worktree suja preservada. Nenhuma alteração de produção nesta
frente. Primeira fronteira em estudo: fonte/relação → menção do argumento,
antes de resolver referente, certeza ou autoridade.

`sonda_argumento_isolado_v1.py`: 7 casos conhecidos U0–N1, 3 braços, 2 rodadas
(42 consultas locais), sem holdout novo, treino ou consulta externa.
Controle `conjunto` reproduz exatamente o pedido explícito anterior. `copia`
pede somente a menção literal. `tokens` usa a mesma tarefa isolada, mas devolve
um intervalo de tokens, materializado na fonte pelo host; reutiliza
`tokenizar_fonte`, sem empregar a guarda de contexto externo que proibiria
argumentos dentro das aspas. Todos mantêm fonte integral, relação, mapa de
aspas, modelo e orçamento. Rodada 2 inverte a ordem; sem retries.

Revisão pré-consulta: U0 `qual dessas expressões`; U1/U2 `A primeira/segunda
dessas expressões`; O0 a coordenação inteira `a expressão desta página ou uma
expressão da página ausente`; O1 apenas `a expressão desta página`; N0 a fala
externa inteira; N1 `recolha a vela`. Artigo inicial opcional em U1/U2/O0/O1 e
par de delimitadores opcional em N0/N1 são as únicas variantes aceitas. As
anotações são métricas locais, não entram no prompt. Não substituir menção
pelo referente; não incluir o predicado ou a fonte inteira para pontuar.

Validação local pré-coleta detectou que O1 repete `expressão desta página`:
a revisão aponta a primeira menção, junto à relação, não a menção explicativa
posterior. A aferição compara também offsets. Na cópia, só ancorar uma ocorrência
única delimitada por tokens (o `a` final de `única` não é artigo independente).
Cópia ambígua não escolhe silenciosamente a primeira ocorrência. Esse RED foi
do próprio diagnóstico, não um novo defeito demonstrado da Laylay.

Medir separadamente shape, abstenção, literalidade, alinhamento com essa revisão
e repetibilidade. O controle mantém também métricas anteriores de certeza.
Comparar conjunto/cópia estuda simplificação **mais instrução de menção**; não
isola exclusivamente carga cognitiva. Cópia/tokens estuda representação e
entrada tokenizada. Nenhum placar prova compreensão geral ou resolve P01.
Guardar requests, HTTP bruto, ordem, hashes, digest, baseline e flags falsas;
auditar o JSONL final antes de relatar resultados. Se a literalidade melhorar
sem seleção correta, não encadear a saída como argumento validado.

#### Resultado auditado da seleção isolada (10/10)

Artefato `resultados_testes/sonda_argumento_isolado_v1.jsonl`, SHA-256
`95996463a041c767e0fb0d466deb71d421fdca07a8023be6d481d801291faddf`.
Script SHA-256 `e1248619d2aa15b51d22c40177b14795044d6669e21f3f3fe947623731b9982a`.
42 consultas/44 linhas auditadas por recálculo do HTTP bruto; ordem, casos,
anotações pré-consulta, requisições e resumo íntegros. Todas HTTP 200/done/stop.
Qwen `qwen3:4b-instruct`, digest inicial/final
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Os 14 controles reproduziram tanto as requisições quanto as respostas do
experimento anterior. Entre rodadas, 20/21 pares de respostas idênticos; N1
conjunto novamente variou. Sem retries, treino, API externa ou runtime Laylay.

| Medida por 7 casos | Conjunto R1/R2 | Cópia R1/R2 | Tokens R1/R2 |
| --- | --- | --- | --- |
| Contrato de saída válido | 7 e 7 | 7 e 7 | 6 e 6 |
| Argumento literal localizado | 6 e 6 | 6 e 6 | 0 e 0 |
| Alinhamento à anotação local | 1 e 0 | 1 e 1 | 0 e 0 |
| Abstenções | 0 e 0 | 0 e 0 | 6 e 6 |

Na tabela, cada célula mostra contagens R1/R2, não uma fração de aprovação.
Tokens: U0/U1/U2/O0/O1/N0 abstêm-se; N1 fornece `inicio=6,fim=3`, rejeitado pelo
host, embora seja JSON/schema de campos válido. Não inverter limites nem
forçar seleção para melhorar placar. O controle acerta a menção de N1 somente
na primeira rodada. A cópia acerta U0; U1 resolve o referente em vez de localizar
a menção; U2 altera `A` para `a` (falha literal, não prova de erro semântico);
O0/O1/N0/N1 devolvem a própria âncora da relação. Fonte inteira não é argumento
adequado apenas por ser literal. O1 confirma por teste a necessidade de offsets
quando a mesma expressão aparece em duas posições.

**Falsificado neste painel:** simplificar a saída, com este pedido de menção,
seria suficiente; substituir cópia por coordenadas bastaria para selecionar.
Não houve erro HTTP ou corte pelo limite de geração que explique os resultados.
Isso não prova incapacidade geral do modelo nem uma causa interna única.
**Limite do experimento:** os casos O0/O1 chamam `O título` de relação, enquanto
outros oferecem predicado ou sujeito+verbo. O novo pedido de “argumento” depende
de qual papel se procura; essa heterogeneidade é hipótese concorrente de falha
do contrato experimental. As abstenções também não distinguem dificuldade
semântica de efeito do schema/representação. Não rotular esses erros como treino.

**Decisão:** não promover nenhum dos braços. Próxima fronteira é tornar explícita
a pergunta relacional/papel procurado, sem entregar o trecho-resposta, e usar
contrastes novos de menção direta, anáfora e citação interna. Comparar essa
especificação mantendo a representação fixa antes de reintroduzir coordenadas
ou certeza. Não repetir aumento de exemplos ou encadear seleções não validadas.
19 testes focados passaram (31,19 s); regressão conjunta com argumento/escopo,
contrastes, apoio por ocorrência e ligação: **64 passed em 112,14 s**. Não é
suíte completa nem validação de composição/runtime; P01 continua aberta.
Esta frente alterou somente sonda, testes e documentação; nenhum commit.

### P01: argumento e escopo explícitos, protocolo pré-consulta (10/10)

A/B offline no Qwen histórico, sem trocar backend. Sete casos conhecidos
U0/U1/U2/O0/O1/N0/N1; controle de seleção único congelado versus proposta com
argumento, escopo (cópias literais), alternativas_visiveis, alternativa_ausente
e alvo. Mesma fonte, IDs, relação, temperatura zero e limite 700 tokens.
Prompt/schema mudam juntos: medir representação composta, não causalidade de
um campo isolado. Duas rodadas, modos alternados e ordem invertida: 28 consultas.
Nenhuma chamada externa, produção, configuração, treino ou gate de agregação.

Contrato: argumento denota o alvo da relação, não o recipiente da citação;
escopo preserva condições/negações/alternativas que restringem sua resolução.
Alternativa visível única não elimina possibilidade ausente. Rótulo resolvido
precisa ser internamente coerente com as alternativas declaradas. Todos esses
campos são propostas: cópia literal, coerência e gabarito são métricas distintas,
nenhuma confirma semântica. Revisar manualmente argumento/escopo; não contar
texto inteiro ou uma citação verdadeira como prova de ligação adequada.

Métricas pré-fixadas: shape, âncoras únicas literais, coerência estrutural,
alvo correto, conjunto alvo/alternativas/ausência correto. Campo ausente esperado
somente em O0, anotação exclusivamente no avaliador, não no prompt. Não aceitar
ganho agregado que esconda perdas em U1/U2 ou confusão N0/N1. Painel já conhecido,
diagnóstico sem validação de generalização. Controlar estabilidade do seletor
contra a coleta anterior, sem ajustar respostas/gabaritos depois de medir.

Base main, HEAD 2566b621d2c8ee88ff7086c6c36019da85c8a4cd; worktree preservada.
Script `scripts/analises/sonda_argumento_escopo_v1.py`, SHA-256
`80f138ee03a82327005594d90a531c8211d57c29cfb8b2d9f555c67976cff3b9`.
Painel congelado `d8ede83062c3448ffcd4b0d4005c8133c902b62c0a9fe619665a55db31b1d897`;
ancorador reutilizado de `sonda_produtor_condicoes_v2.py`, SHA-256
`829afcb4e7a5fed9ff17a52ec2969401c7f1e675f81b1d0db1baba95f295fc07`.
13 testes locais passaram antes da consulta. Capturas HTTP brutas e flags falsas
preservadas, com auditoria final antes de divulgar resultados.

#### Resultado auditado do argumento/escopo explícito (10/10)

28 consultas/30 linhas em `resultados_testes/sonda_argumento_escopo_v1.jsonl`,
SHA-256 `3e71e832254289e1ec61447baf6a60d0548b3abac1e4e5ed10d28f2e7c645293`.
HTTP 200, done=true, stop e shape válidos em todas. Painel, ordem, hashes,
requisições e resumo conferidos contra o bruto. Digest inicial/final igual:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
14 controles coincidem com os históricos. As 14 requisições repetidas são iguais,
mas somente 13 conteúdos se repetem: N1 explícito muda de q1 para q0, inclusive
argumento/escopo. A primeira checagem de igualdade falhou legitimamente; a
auditoria passou a registrar a divergência, não a eliminar uma das rodadas.
Temperatura zero não foi tratada como garantia de determinismo.

| Métrica (de sete casos) | Rodada 1 | Rodada 2 |
| --- | ---: | ---: |
| Alvo correto no controle | 4 | 4 |
| Alvo correto explícito | 5 | 4 |
| Alvo/alternativas/ausência corretos | 2 | 2 |
| Coerência interna dos campos | 3 | 3 |
| Argumento e escopo ancorados literalmente | 5 | 5 |
| Conjunção das guardas anteriores | 1 | 1 |

Ganho estável de alvo em U0; ganho instável em N1; perda estável em N0. Não
promover o ganho líquido da primeira rodada. U1/U2 mantêm o alvo correto, mas
listam ambas as alternativas, violando o fechamento declarado da referência.
O0 copia a própria alternativa ausente no argumento e ainda marca ausência=false.
Isso expõe interpretação incoerente com o conteúdo recebido, não falta de fonte.

Inspeção literal/manual:

- U0 passa as guardas mecânicas, mas argumento é a fonte inteira. Esse resultado
  recupera abstenção local; não comprova seleção discriminativa de argumento.
- U1/U2 copiam a oração inteira no argumento e deixam no escopo apenas o predicado
  genérico, omitindo primeira/segunda, a informação que resolve a referência.
- O0/O1 mudam aspas curvas para retas. O1 ainda termina o escopo em `varra o ca`.
  São cópias não literais: houve stop com 117 tokens em O1, não teto de 700.
  Não alterar normalização/gabarito para esconder isso nem aumentar tokens por
  suposição de truncamento do backend.
- N0 cita a ação interna como argumento da escrita externa: trecho verdadeiro,
  ligação errada. N1 primeiro cita a ação interna; depois copia a oração inteira
  e escolhe q0. As duas rodadas preservam ambas alternativas indevidamente.

Decisão: candidata rejeitada como resolução/gate. O benefício demonstrado é
observabilidade de contradições, não confiabilidade semântica. Formato válido,
cópia literal e coerência não certificam vínculo; nenhum campo prevalece sobre
outro por conveniência. Primeira divergência permanece na interpretação proposta,
com falhas locais adicionais de cópia; não tratá-las como causa única do erro de
referência. Prompt e schema mudaram juntos, painel conhecido e pequeno.

Próxima fronteira: isolar seleção do argumento da atribuição de certeza, usando
localização canônica para a cópia e mantendo inspeção de escopo. Antes de montar
outra combinação, confrontar esse contrato com os negativos históricos e distinguir
o que pode ser verificado mecanicamente do que ainda depende de interpretação.
Não usar saída desta sonda como treino positivo ou confirmação da rede.

Validação local: 13 testes novos; **45 passaram em 73,56 s** (nova sonda,
contrastes, apoio por ocorrência e ligação). Suíte ampla não repetida neste turno.
Nenhuma produção/configuração/treino alterada nesta frente; nenhum commit criado.
P01 segue aberta, sem prova de runtime real da Laylay.

### P01: contrastes mínimos novos de escopo, pré-consulta (10/10)

Próxima fronteira após os acordos errados: resposta do intérprete à informação
que abre/fecha alternativas e ao alvo de uma relação dentro/fora de aspas.
Sem alteração de prompt, schema, scorer, modelo da Laylay ou gabaritos antigos.
Painel sintético novo, desenhado após observar falhas: diagnóstico direcionado,
não holdout independente nem prova de generalização.

Sete casos congelados em `scripts/analises/sonda_contrastes_escopo_v1.py`:

- U0/U1/U2: mesmas duas expressões; identificação desconhecida/primeira/segunda.
  Esperados: indeterminado/q0/q1. U1→U2 troca somente primeira por segunda.
- O0/O1: uma expressão visível e uma página ausente; troca somente ` ou ` por
  `, não ` para excluir explicitamente a alternativa ausente. Esperados:
  indeterminado/q0. Existência de uma candidata visível não decide O0.
- N0/N1: fonte idêntica com aspas aninhadas; muda somente a relação literal
  avaliada. Escrever refere-se à citação externa; ordenar refere-se à interna.
  Esperados q0/q1, com o mesmo mapeamento canônico de aspas e pai_id.

12 pares e sete seleções por backend/rodada. Dois backends, duas rodadas,
alternados e com segunda ordem invertida: 76 chamadas (38 locais, 38 externas).
Modelo local histórico qwen3:4b-instruct; externo gemini-3.1-flash-lite no
google-ai-studio, sem fallback. Limites anteriores 700/256 tokens preservados.
Medir por backend, rodada e contraste; vetor completo e seleção separados.
Exigir resposta correta a todas as variantes para considerar contraste alinhado;
não esconder regressão de um par pelo placar agregado. Gold somente no host.
Nenhum acordo de modelos qualifica significado ou autoriza efeito.

Base main, HEAD 2566b621d2c8ee88ff7086c6c36019da85c8a4cd; worktree e mudanças
paralelas preservadas. Script SHA-256
`d8ede83062c3448ffcd4b0d4005c8133c902b62c0a9fe619665a55db31b1d897`;
adaptador independente congelado
`364284d5037de19eb3cd4d0915ed18115323e53576b6c7898b3752b2cfd9053c`, que também
confere os hashes anteriores. Nove testes focados passaram antes da coleta.
HTTP bruto, requisições e resumo serão preservados e auditados. Erro de
transporte/schema ou custo desconhecido interrompe sem retry; limite operacional
externo US$ 0,10 com reserva por chamada. Fonte fictícia sem dados pessoais.
Esta frente só altera sonda, testes e documentação, sem produção/treino.

#### Resultado dos contrastes de escopo (10/10)

Validação: nove testes novos focados; **59 testes passaram em 104,78 s**, cobrindo
contrastes, adaptador independente, apoio por ocorrência, candidatos e ligação.
A suíte ampla de 1.614 testes da rodada anterior não foi repetida; não reportar
esse total como validação deste turno. GREEN offline não encerra o RED semântico.
Somente sonda, testes e documentação alterados por esta frente; nenhum commit.

76 consultas completas auditadas, 78 linhas no artefato
`resultados_testes/sonda_contrastes_escopo_v1.jsonl`, SHA-256
`708b9b21a16614ebc062d8fad291fb625d494cc51089fb35d8acb12034819fd4`.
HTTP 200, stop e shape válidos nas 76; fonte integral, mensagens e schemas
iguais entre backends; ordem, painel, hashes e resumo recalculado conferidos.
19 pares de requisições/respostas repetidas iguais por backend. 38 IDs externos
distintos, modelo/provedor esperados; custo externo US$ 0,0049775. Digest local
igual antes/depois: `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Todas as flags de autoridade/qualificação falsas; nenhuma agregação integrada.

| Métrica por rodada (ambas iguais) | Local | Externo |
| --- | ---: | ---: |
| Pares corretos | 6/12 | 8/12 |
| Vetores completos corretos | 2/7 | 4/7 |
| Seleções corretas | 4/7 | 4/7 |
| Famílias completas (seleção e todos os pares) | 0/3 | 1/3 |

U1/U2: ambos seguem corretamente primeira→segunda, incluindo exclusão da outra
ocorrência. U0: externo preserva indeterminação; local escolhe q0 no controle e
exclui ambas na avaliação por par. Informação ausente não é prova de exclusão.
Família U completa somente no externo; capacidade de distinguir posições não
está globalmente ausente em nenhum dos dois.

O0/O1: o fechamento explícito da alternativa ausente não altera as respostas.
Local escolhe q0 nos dois controles e exclui q0 nos dois pares; externo responde
nenhuma/excluida nos dois. Em O0 o vínculo está aberto; em O1 a única expressão
é explicitamente identificada. Nem mais contexto nem um consenso de exclusão
resolvem esse contraste. Ambos erram inclusive O1, em que a informação basta.

N0/N1: texto e IDs idênticos, relação muda de cronista/escrever para capitã/ordenar.
Ambos seletores permanecem q0: não acompanham a troca de alvo para q1. Externo
também repete sustentada/excluida nos pares; local muda de excluida/excluida para
sustentada/sustentada, ainda sem ligação correta exclusiva. Pai_id e offsets
corretos; recipiente de uma relação não equivale ao argumento dessa relação.

Primeira fronteira RED demonstrada: interpretação após projeção íntegra, antes
de qualquer agregação. Falsificadas como explicações suficientes: informação
necessária sempre ausente (O1), incapacidade geral de distinguir IDs (U1/U2),
transporte/JSON ou contexto cortado. Não isolamos uma causa interna única; os
três contrastes não provam que todos os erros tenham a mesma implementação causal.
Não treinar sobre rótulos desses modelos nem usar acordo como gate. Painel novo
mas direcionado e pequeno: não comparar percentuais diretamente com o anterior.

Próxima hipótese de contrato: explicitar, como proposta inspecionável, o argumento
da relação e o escopo que mantém/exclui alternativas, antes de comprimir tudo num
único rótulo. Distinguir localização literal, resolução de referência e apoio
contextual; não criar parser paralelo ou regra específica de página/aspas.
Testar primeiro se essa representação acompanha os contrastes, com controles
de falta de informação, sem presumir que campos preenchidos provam semântica.
P01 continua aberta; nenhum modelo, treino ou regra de produção alterado.

### P01: contraste independente de interpretação, pré-consulta (09/10)

Mesmos 14 casos/27 pares, textos, instruções, schemas e ordem do experimento
anterior; 14 controles de seleção e 27 avaliações por par por rodada, duas
rodadas (82 chamadas). Comparador externo já usado na investigação:
`google/gemini-3.1-flash-lite` via OpenRouter, somente `google-ai-studio`, sem
fallback, temperatura zero. Nenhum gabarito/resposta anterior enviado; fontes
do painel revisadas, sem dados pessoais. Modelo da Laylay não é alterado.

Reutiliza `sonda_openrouter_fronteira.consultar_openrouter` e o projetor/scorer
local da sonda anterior. Captura HTTP bruto antes da interpretação, sem headers
de autenticação, e exige identidade do modelo/provedor, stop e schema válido.
Limite do adaptador externo é 256 tokens versus 700 no controle Ollama; registrar
isso, não fingir identidade de backend. Qualquer truncamento/falha ou custo
ausente interrompe a coleta sem retry. Limite operacional US$ 0,10, reserva
US$ 0,002 antes da próxima chamada. Modelo hospedado não possui digest local;
preservar versão declarada, IDs e metadados brutos sem presumir pesos fixos.

Congelado antes da primeira chamada: script
`scripts/analises/sonda_apoio_independente_v1.py`, SHA-256
`364284d5037de19eb3cd4d0915ed18115323e53576b6c7898b3752b2cfd9053c`.
Dependências: sonda local
`20486559660a8d923d880db25af4b56d53dfa9198b18f77a628d704a1d00f56d`, adaptador
`566679584886163294a9bdf0fc8d04cd03599f634dc2c71db5df6d15a1eb6b64`, artefato local
`0f1c98fee9773f2fc4b921d50342801f8e08ff9bba7ce6a16c600a9e00e56a97`.
Base main, HEAD 2566b621d2c8ee88ff7086c6c36019da85c8a4cd, worktree preservada.
14 testes focados verdes antes da API. Nenhuma produção alterada nesta frente.

Objetivo diagnóstico: medir separadamente pares, vetores e seleção; inspeção das
divergências e de todos os ambiguos, sem voto/agregação. Se outro backend resolver
os mesmos dados, falsifica impossibilidade geral da representação, não prova que
o problema é exclusivamente tamanho/pesos do Qwen nem generalização. Se ambos
falharem, isso também não prova impossibilidade. Painel conhecido, gabarito local,
comparação não simultânea; não é holdout nem autorização de integrar um juiz.
Suporte atual do endpoint e schema verificado na API de endpoints e na
[documentação oficial de structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs).

#### Resultado do contraste independente

Validação: 14 testes focados e **1.614 regressivos relevantes passaram em
320,36 s**. GREEN da ferramenta offline, não do comportamento semântico nem do
runtime da Laylay. Produção/configuração não alteradas por esta frente; somente
sonda, testes e documentação. Nenhum commit criado.

Artefato `resultados_testes/sonda_apoio_independente_v1.jsonl`, SHA-256
`9102f88b23dcca9b0863d1ecafa6d9e866d2ff8669aab6b5f454e044dd8a0e35`.
84 linhas auditadas: metadata, 82 respostas e resumo recalculado do HTTP bruto.
Todas HTTP 200/stop/shape válido, modelo e provedor esperados; 82 IDs distintos.
As 41 entradas repetidas produziram conteúdo idêntico nas duas rodadas. Mensagens
e schemas iguais aos 82 controles correspondentes do artefato local, sem gabarito.
Todas as flags de qualificação/autoridade continuam falsas. Custo observado total
US$ 0,0109395. Nenhuma falha ou retry. Não há digest de pesos do serviço externo.

| Métrica por rodada | Qwen local congelado | Comparador externo |
| --- | ---: | ---: |
| Pares alinhados ao gabarito local | 16/27 | 23/27 |
| Vetores completos corretos | 6/14 | 11/14 |
| Seleção única/abstenção correta | 9/14 | 12/14 |

Ambas rodadas iguais. Ganhos em vetor: OR/L3/L4/L5/M3; sem perda de vetor
completo, mas **há perda por par em M2/q1**. Não esconder esse RED pelo placar
composto. No controle de seleção, ganhos L5/L8/M3/M5, perda M2. Matriz externa
por par: sustentada→sustentada 7, sustentada→excluida 1; excluida→excluida 11,
excluida→sustentada 1; insuficiente→insuficiente 5, insuficiente→sustentada 2.

Inspeção das primeiras divergências restantes:

- L8: fonte explicitamente não informa qual expressão nomeia o curso; seleção
  externa abstém-se, mas avaliação de q1 anuncia apoio. A decomposição não conserva
  a incerteza do enunciado completo. O gabarito insuficiente não foi alterado.
- M2: a ata contém uma citação externa, dentro da qual o técnico pede uma ação
  citada internamente. O comparador seleciona a externa e exclui a interna;
  o seletor Qwen acertava a interna. Coordenadas e pai_id são corretos. Conter a
  oração que menciona a relação não torna o recipiente seu argumento-alvo.
- M7: fonte admite expressão da página presente ou da página perdida. Ambos
  escolhem a única ocorrência visível, sem evidência para excluir a ausente.

**Concordância falsa entre modelos:** L8/q1, M2/q0 e M7/q0 recebem sustentada de
ambos, embora o gabarito e a inspeção da fonte não sustentem essa decisão. Voto ou
aceitação por consenso não pode servir de certificado. Resultado externo melhor
neste painel não é juiz confiável nem resolução da P01.

Falsificada a hipótese forte de que os dados/representação impedem qualquer
backend de resolver OR/L3/L4/L5/M3. Permanecem abertas interações entre modelo,
instrução, backend e representação; o teste não isola pesos/tamanho, não mede
generalização e não autoriza substituir o Qwen. JSON e transporte não explicam
os erros observados. Nenhuma regra de produção, treino ou configuração alterada.

Próxima fronteira causal: **escopo da ligação proposta**, distinguindo argumento
da relação, recipiente de citação e alternativas não observadas. Antes de outro
prompt/treino, congelar contrastes mínimos novos que variem somente informação
disponível ou posição da relação nas aspas; separar localização literal de apoio
contextual. Isso é hipótese de contrato a investigar, não parser paralelo nem
aprovação de um agregador. Preservar os casos históricos e seus resultados.

### P01: apoio por ocorrência, protocolo pré-consulta (09/10)

Próxima hipótese offline: perguntar pelo apoio da fonte a cada par relação/ocorrência,
sem retirar a fonte completa nem as ocorrências concorrentes. O controle mantém a
requisição congelada de seleção de ID único. Não há agregador integrado nem efeito
no runtime. Fonte, localização literal e proposta semântica continuam distintas.

Painel conhecido congelado: NS, OR, L3, L4, L5, L6, L8, M1, M2, M3, M4, M5, M7,
M8 (duas fontes históricas e doze fixtures). São 27 pares e 14 controles por rodada;
duas rodadas, com ordem invertida na segunda: 82 consultas. Gold fica apenas no
avaliador local. Classes: sustentada, excluida, insuficiente. Negação não elimina
uma ligação descrita; uma ocorrência visível não resolve uma referência ausente.

Medir confusão por par, apoio falso em ambiguidades, insuficiência falsa em ligações
claras e vetor exato por caso. A acurácia do controle e o vetor completo são tarefas
distintas. Critério de interesse: preservar ligações/exclusões claras enquanto L5,
L8, M3 e M7 permanecem insuficientes. Mesmo um ganho não demonstra generalização:
painel conhecido, mais chamadas e mudança conjunta de tarefa, prompt e schema.

Base: main, HEAD 2566b621d2c8ee88ff7086c6c36019da85c8a4cd; worktree suja preservada.
Script `scripts/analises/sonda_apoio_por_ocorrencia_v1.py`, SHA-256
`20486559660a8d923d880db25af4b56d53dfa9198b18f77a628d704a1d00f56d`.
Dependência congelada: `sonda_candidatos_ocorrencia_v1.py`, SHA-256
`0937217ce8a4b273129fff28507b3227657e9a4bce479947300568c460e06986`.
Modelo histórico da sonda: qwen3:4b-instruct, temperatura zero, limite 700 tokens.
12 testes locais passaram antes da coleta. Nenhuma alteração de produção por esta
frente; mudanças paralelas de streaming não pertencem a esta investigação.

#### Resultado auditado do apoio por ocorrência

Validação local: 12 testes focados; regressão das sondas e do contrato de
proposições mencionadas: **1.600 passed em 304,66 s**. Esse GREEN comprova os
contratos locais da ferramenta, não corrige os REDs semânticos abaixo nem prova
runtime real da Laylay. Nenhum commit criado.

Coleta completa: `resultados_testes/sonda_apoio_por_ocorrencia_v1.jsonl`, 84 linhas
(metadata, 82 consultas, resumo), SHA-256
`0f1c98fee9773f2fc4b921d50342801f8e08ff9bba7ce6a16c600a9e00e56a97`.
Digest inicial/final igual:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Auditoria recalculada do HTTP bruto: 82 HTTP 200, done=true, stop, shape válido;
painel, sequência, hashes e resumo conferidos; todas as flags de autoridade e
qualificação continuam falsas. As 41 requisições/conteúdos repetidos foram iguais;
os 28 controles também coincidiram com o artefato anterior congelado.

Resultados iguais nas duas rodadas:

| Esperado por par | sustentada | excluida | insuficiente |
| --- | ---: | ---: | ---: |
| sustentada | 7 | 1 | 0 |
| excluida | 3 | 9 | 0 |
| insuficiente | 5 | 2 | 0 |

16/27 pares corretos; 6/14 vetores completos corretos, contra 9/14 seleções
corretas do controle. São tarefas distintas: vetor não é uma decisão agregada
integrada. Vetores corretos: NS/L6/M1/M4/M5/M8. Único ganho diagnóstico em relação
ao controle: M5; perdas em OR/L3/L4/M2. Todos os sete pares ambíguos foram decididos
indevidamente: cinco apoios e duas exclusões. Não houve nenhuma saída insuficiente.

Primeira divergência demonstrada: proposta semântica do par, após projeção íntegra
da fonte/ocorrências e resposta válida. OR/L3/M2 apoiam duas ocorrências quando só
uma corresponde; L4 exclui ambas. A decomposição, nesta configuração, não resolve
o vínculo nem preserva a abstenção. Falsificados como explicação destes resultados:
truncamento/JSON inválido, remoção do contexto na projeção e alteração do controle.
Não foi isolada causa interna única: representação, instrução e capacidade de
interpretação ainda podem interagir. Repetição concordante não comprova semântica.

Decisão: rejeitar a candidata como substituta ou gate; não montar agregador sobre
essas decisões. P01 permanece aberta. Antes de outra variação de prompt, a próxima
fronteira proposta é um contraste independente de interpretação com as mesmas
fontes e contrato, para distinguir limitação desta configuração de dificuldade da
representação. Isso não autoriza troca do modelo da Laylay nem torna um segundo
modelo autoridade; qualquer divergência exige inspeção da evidência literal e
contextual. Nenhuma alteração de produção, treino, configuração ou commit por
esta frente.

### P01: candidatos compatíveis versus unicidade (09/10)

Protocolo pré-consulta. HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`,
main, worktree incluindo streaming paralelo preservada. Sonda
`scripts/analises/sonda_candidatos_ocorrencia_v1.py`, SHA256
`0937217ce8a4b273129fff28507b3227657e9a4bce479947300568c460e06986`.
Controle congelado `sonda_ligacao_ocorrencia_v1.py`, SHA256
`fbdb15e960860d7fec70447702c71b058946212b99119a23fb8d74bcef7f6d67`.

- A/B contemporâneo: `ocorrencia_id` antigo versus `candidatos` + `situacao`.
  Mesma fonte integral, relação, aspas/offsets, modelo textual histórico e
  opções. Mudam instrução e schema juntos; não atribuir efeito exclusivamente
  ao formato. Fonte não contém foco desejado, papel anterior ou gabarito.
- 28 casos × dois braços × duas rodadas = 112 chamadas. Ordem dos braços
  alternada por caso e invertida na segunda rodada. Doze relações reais
  históricas, oito fixtures L1–L8 conhecidas e oito novas M1–M8. Reportar
  os grupos separadamente, sem confundir relações fornecidas com extração
  real. Novos sintéticos da mesma autoria não são holdout independente.
- M1 nega relação mas seu alvo é claro; M2 usa aspas aninhadas; M3 deixa
  dois alvos abertos; M4 desambigua explicitamente para o segundo; M5 não
  se refere a citação; M6 repete texto com duas funções; M7 só tem um
  candidato visível mas admite título em página ausente; M8 é hipotético
  com alvo explícito. Não confundir veracidade, papel e identidade da relação.
- `unico` exige exatamente um candidato; `nenhuma` exige lista vazia;
  `indeterminado` admite zero, um ou vários candidatos visíveis. A lista não
  deve inventar IDs de conteúdo ausente. Cardinalidade não resolve a
  situação automaticamente e nenhuma estrutura confere autoridade semântica.
- Comparar decisão de alvo/abstenção em ambos; aferir conjunto exato de
  candidatos separadamente no novo. Ganho exigido: recuperar L5/L8 sem
  perdas pareadas nas duas rodadas e preservar abstenção M3/M7. Não promover
  por acerto agregado que esconda falsa unicidade. Mesmo GREEN é offline.
- Treze testes locais verdes antes da coleta. Artefato exclusivo
  `resultados_testes/sonda_candidatos_ocorrencia_v1.jsonl`, painel e hashes
  antes das consultas, HTTP bruto e auditoria final. Sem produção, treino,
  configuração ou executor alterados por esta frente.

Resultado auditado: **112 chamadas completas**, 114 linhas, duas rodadas
com requisições e conteúdo de resposta idênticos por caso/braço. Todos HTTP
200, `done=true`, `stop`, shape válido e flags de autoridade/semântica falsas.
Painel/ordem, hashes, requisições e resumo reconferidos a partir do bruto.
Artefato SHA256 `8b123c80accec309be19d8fd4a97fac86b31dfaea7539bd02c1a298802d9cb7a`.
Digest inicial/final `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Os 40 registros de controle comparáveis à coleta anterior têm requisições e
respostas idênticas. Não atribuir o resultado a troca de modelo ou transporte.

| Grupo | Antigo: alvo/abstenção corretos | Candidatos: alvo/abstenção corretos | Lista exata |
|---|---:|---:|---:|
| 12 seleções reais conhecidas | 12/12 | 7/12 | 7/12 |
| 8 fixtures L conhecidas | 6/8 | 5/8 | 5/8 |
| 8 fixtures M novas | 5/8 | 4/8 | 4/8 |

Mesmos placares nas duas rodadas: 23/28 no antigo, 16/28 na candidata.
NR/OR continuam requisições idênticas sem foco desejado, não evidências
independentes. Ganhos pareados: L5/L8/M3/M5/M7. Perdas:
NS/OS/NR/OR/T11/L3/L4/L6/M1/M2/M6/M8. O critério pré-fixado falhou:
**rejeitada esta candidata como substituta geral**, sem apagar seus ganhos.

O novo formato reconhece os quatro casos de referência indeterminada
(L5/L8/M3/M7), incluindo M7 com uma só candidata visível e página ausente.
Porém lista q0 e q1 e se abstém em vários casos de relação inequívoca:
texto repetido, negação M1, aspas aninhadas M2 e hipótese M8. Em T11 propõe
lista vazia/nenhuma, confundindo uma relação fragmentária com falta de alvo;
em L6 propõe ambas as citações para uma relação sobre a mesa. Não é defeito
de enum, offsets ou host: a primeira divergência observada é inclusão/
exclusão semântica de candidatos. Não inferir mecanismo interno único.

Falsificado neste painel: bastaria permitir lista e separar situação para
preservar os acertos anteriores. Fonte, identidade e opções ficaram iguais;
prompt e schema mudaram juntos, logo não isolamos qual deles causou a perda.
Maior abstenção não equivale a melhor entendimento. O antigo também não
resolve a raiz: escolhe indevidamente alvos nas ambiguidades e erra M5.
Não combinar braços por gabarito, voto ou exceções de frases.

Próxima investigação deve reduzir a confusão entre **possibilidade genérica**
e **ligação sustentada pela fonte**: comparar relações e ocorrências
individualmente, usando o mesmo contexto integral e permitindo apoio,
exclusão ou informação insuficiente, antes de agregar candidatos. Isso é
hipótese a falsificar, não arquitetura aprovada. Fixar critérios e pares
positivos/negativos equivalentes antes das consultas; não considerar rótulo
de apoio produzido pelo próprio modelo prova independente. Priorizar casos
já discriminativos (L3/L4 versus L5/L8, M1/M2/M7) e validação em fontes novas
somente se o contrato local melhorar. Não investir em integração/treino de
uma representação que perdeu acertos claros.

13 testes focados verdes antes da coleta; **1.588 regressivos relevantes
passaram**, incluindo esses treze. GREEN do instrumento offline, não da
semântica ou runtime; diff focado sem erros. Esta frente alterou somente sonda,
testes e documentação; produção/configuração/treino intactos por esta frente,
trabalho paralelo de streaming preservado, nenhum commit/liberação.

### P01: proposta de ligação relação→ocorrência (09/10)

Protocolo pré-consulta, sem promoção ou uso como gate de produção. HEAD
`2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, main, trabalho anterior preservado.
Sonda `scripts/analises/sonda_ligacao_ocorrencia_v1.py`, SHA256
`fbdb15e960860d7fec70447702c71b058946212b99119a23fb8d74bcef7f6d67`.
Dependência `sonda_evidencia_interferencia_v1.py`, SHA256
`720ac8f5b08133388cfc43a74075626047c4bffb26ff0f6b9467fc04a442e58d`.
Artefato de seleções congelado em
`8782b585a685c7334cca29abb06892e217700e3b810109428d7f0176a48bdd94`.

- Reusar mapeador canônico de aspas, offsets, transporte HTTP e validação
  tipada existentes. Inventário antigo de referentes nomeados não equivale
  a ocorrências citadas: não promover nome ancorado a vínculo contextual.
- 12 seleções reais da rodada 1 anterior, revalidadas sem consulta nova
  ao seletor; fonte integral e relação literal preservadas. O modelo recebe
  todas as regiões citadas e a relação, sem foco desejado, papel anterior
  ou gabarito. Propõe `ocorrencia_id`, `nenhuma` ou `indeterminado`.
- Gold de alvo fixado antes da consulta: OR aponta q1 (nome posterior),
  não q0 (ordem/foco original). NR/OS também q1; demais históricos q0.
  CX e T11 permitem identificar a ocorrência mesmo com relação insuficiente:
  acertar o alvo não comprova papel, suficiência ou ausência de ambiguidade.
- Oito controles L1–L8 com relações sintéticas explícitas, nunca atribuídas
  a uma seleção real do Qwen. Pares de duas ocorrências distintas e idênticas,
  relação posterior, nenhuma ocorrência pertinente e duas ambiguidades.
  Não são holdout independente: mesma autoria, construídos para diagnóstico.
- 20 casos × duas rodadas = 40 consultas, ordem invertida na segunda.
  Novo pacote de tarefa sem exemplos; não é A/B isolando um token de prompt.
  Separar os 12 históricos dos oito controles e reportar cada erro. Não usar
  acerto bruto, IDs iguais, proximidade ou voto como prova de compreensão.
- Progresso local exigiria rejeitar a ligação de OR ao foco errado, conservar
  ligações corretas e abstinências nas duas rodadas. Mesmo 20/20 não libera
  runtime: não estamos reexecutando classificação nem testando todas as
  construções relacionais/aspas aninhadas. Não completar lacunas por ouro.
- 11 testes do instrumento passaram antes da coleta. Mesmo Qwen textual
  histórico, nenhuma configuração, produção ou treino alterados. Artefato
  exclusivo `resultados_testes/sonda_ligacao_ocorrencia_v1.jsonl`, com painel,
  hashes, entrada efetiva e respostas brutas. Flags de semântica/autoridade falsas.

Resultado auditado: **40 consultas concluídas**, duas rodadas iguais. A
interrupção da ferramenta deixou o arquivo originalmente previsto somente
com metadata; foi preservado, sem afirmar se houve requisição em voo.
A coleta completa está em
`resultados_testes/sonda_ligacao_ocorrencia_v1_retomada1.jsonl`, 42 linhas,
SHA256 `def386e07471a4e6debd7582ee03e22ae25e4705a3748b8ecd032a57697916fb`.
HTTP 200/`done=true`/`stop` e shape válidos em todas; requisições, fontes,
relações reais, hashes, flags e resumo reconferidos. Digest inicial/final
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
São 19 requisições distintas por rodada: NR/OR tornam-se idênticas quando
se retira o foco desejado, pois consultam a mesma relação na mesma fonte.
Não contar esses dois controles como evidências independentes.

| Origem da relação | Alvo correto, rodada 1 | Rodada 2 |
|---|---:|---:|
| 12 seleções reais históricas | 12/12 | 12/12 |
| 8 relações sintéticas fornecidas | 6/8 | 6/8 |

OR propõe q1, divergindo corretamente de q0, foco da ordem original. Isso
reconhece localmente a relação de outra ocorrência, **não é prova de que um
pipeline integrado corrigiu a classificação**. NS/OS e L3/L4 distinguem
ocorrências idênticas por contexto. L6 reconhece nenhuma ocorrência pertinente.
Porém L5 (`Uma dessas expressões nomeia um curso, sem dizer qual`) escolhe
q0, e L8 (`não informa se ... ou ... é nome do curso`) escolhe q1. Ambos
deveriam permanecer indeterminados e falham nas duas rodadas, apesar de a
fonte integral e a opção de abstenção estarem presentes. Transporte/enum
funcionam; a primeira divergência é a proposta semântica de unicidade.

Critério pré-fixado falhou nas abstinências: **não promover a proposta de
ligação a gate semântico**. Aumentar acerto geral esconderia falsa resolução
de referência em todos os dois controles ambíguos deste painel. Isso não
prova incapacidade geral do Qwen nem que todo uso de ID falha. CX/T11 mostram
ainda que identificar a ocorrência não prova suficiência da relação ou papel.

Próxima fronteira: separar candidatos compatíveis de referência unicamente
estabelecida. Investigar uma representação que permita múltiplos candidatos
e indeterminação, com positivos de unicidade, ausência de alvo, negação,
aspas aninhadas e controles inéditos; comparar contra este proponente
congelado. Não gerar uma decisão só porque o schema exige um campo, nem
transformar cardinalidade de uma lista produzida pela LLM em prova de
unicidade. Sem regras especiais por L5/L8, sem recorte da fonte e sem
liberar autoridade. É hipótese de solução a falsificar, não candidato aceito.

11 testes locais passaram antes da coleta; **1.575 regressivos relevantes
passaram**, incluindo esses onze. GREEN do instrumento, não semântica ou
runtime real; diff focado sem erros de whitespace. Esta frente alterou apenas sonda,
testes e documentação; não alterou produção, treino, configuração/modelo ou
executores. Durante a execução surgiram mudanças paralelas em terminal,
extensão Google e streaming, preservadas e não atribuídas a esta investigação.

### P01: evidência proposta na interferência contextual (09/10)

Protocolo pré-consulta: reusar o braço existente `papel_com_trecho`, sem
criar prompt, schema ou seleção por gabarito. HEAD
`2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, main, worktree preservada.
Sonda `scripts/analises/sonda_evidencia_interferencia_v1.py`, SHA256
`720ac8f5b08133388cfc43a74075626047c4bffb26ff0f6b9467fc04a442e58d`;
painel congelado `sonda_interferencia_contextual_v1.py`, SHA256
`f7cf9890d9f730eeeff3817f2272e5b7d450ffda6da890c74b15f4f2b925e939`.

- Doze casos conhecidos D0/DA/NS/OS/NR/OR/C0/CN/CX/T03/T04/T11, duas
  rodadas, três consultas por caso: seleção+papel conjuntos, depois papel
  sem e com o trecho realmente selecionado. Até 72 chamadas (com trecho
  bloqueado se a seleção não for literal válida). Alternar ordem dos dois
  braços isolados e inverter na segunda rodada, reusando sequência existente.
- Entre os dois braços isolados muda apenas `evidencia_proposta` na entrada.
  Mesmos sistema, exemplos, schema, fonte integral, foco, modelo e opções.
  Papel proposto pela primeira consulta e gabarito não entram nas segundas.
- DA/NS examinam ajuda de relação pertinente; OR examina risco de propagar
  relação de outra ocorrência. C0 examina papel errado apesar de relação
  pertinente; CX mantém seleção problemática; T11 preserva ambiguidade.
  Não corrigir uma seleção errada nem fornecer um trecho idealizado.
- Recomputar resultados por caso/rodada, ganhos/perdas pareados entre os
  braços isolados, validade literal e suficiência local separadas. Superioridade
  neste painel exigiria ganho repetido sem perdas; não equivale a generalização.
  Flags de semântica/autoridade/produção continuam falsas, mesmo com acertos.
- Artefato exclusivo `resultados_testes/sonda_evidencia_interferencia_v1.jsonl`,
  metadata antes das chamadas, fontes/requisições/HTTP bruto preservados.
  Mesmo Qwen textual histórico; sem mudança na Laylay, treino ou executor.
  Painel diagnóstico conhecido, sem holdout ou revisão humana independente.

Resultado auditado: **72 chamadas**, 26 linhas, todas HTTP 200 e concluídas
por `stop`, shape válido, sem bloqueios literais. Requisições dos dois braços
isolados diferem somente pela seleção real ancorada em `evidencia_proposta`.
Painel/ordem, hashes, flags e resumo reconferidos a partir do bruto.
SHA256 `8782b585a685c7334cca29abb06892e217700e3b810109428d7f0176a48bdd94`.
Digest inicial/final `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.

| Papel correto / 12 | Rodada 1 | Rodada 2 |
|---|---:|---:|
| Seleção e papel conjuntos | 7 | 7 |
| Isolado sem trecho | 9 | 8 |
| Isolado com trecho | 10 | 10 |

Ganhos pareados repetidos do trecho: NS e C0. Perda repetida: OR. Em OR,
o foco é a instrução anterior, mas a primeira consulta seleciona `o brinquedo
se chama`, relação do nome posterior; sem trecho responde operação e com
trecho responde nome. O transporte conserva foco/offsets: cópia literal
válida não comprova que a relação selecionada descreve aquela ocorrência.
CX permanece errado; T11 mantém indeterminação em todos os braços.

**Variação do controle:** DA sem trecho respondeu descrição na rodada 1 e
operação na rodada 2, com requisições tipadamente iguais, `temperature=0`
e mesmo digest observado. Com trecho acertou nas duas. Não contar DA como
ganho repetido nem atribuir a mudança a compreensão melhor. Das 48 consultas
de conjunto/sem trecho comparáveis ao artefato anterior, requisições iguais
em todas; somente DA/rodada 1 mudou o conteúdo de resposta. O registro mostra
diferença de cache avaliado, mas não demonstra sua causa. Ordem dos braços,
estado do backend/cache e variabilidade numérica não foram isolados; não
declarar determinismo ou causa interna provada a partir de temperatura zero.

Critério pré-fixado não satisfeito: ganho líquido não apaga a regressão OR.
**Não promover o braço com trecho como substituto geral.** Evidência melhora
decisão em alguns casos e propaga seleção errada em outro. Primeira fronteira
a resolver é qualificação da ligação relação→ocorrência, não executor,
geometria de cópia ou simples inclusão de mais texto. Owner desta investigação
é o proponente/qualificador semântico offline; o host continua validando
identidade e literalidade, sem presumir apoio semântico.

Próximo desenho: exigir uma proposta explícita de qual ocorrência é descrita
pela relação selecionada, preservando fonte integral e possibilidade de
indeterminação. Comparar com o caminho atual e testar troca de foco/ordem,
repetição, relações antes/depois e ambiguidade. Não usar proximidade, mesmo
ID declarado pelo modelo, voto ou igualdade textual como prova suficiente.
Antes de qualquer integração, falsificar a proposta em seleção errada e
fontes inéditas; qualificação ainda é hipótese, não solução demonstrada.
Casos com relação pertinente mas papel errado continuam controle separado.

Oito testes focados passaram antes da coleta; **1.564 regressivos relevantes
passaram**, incluindo esses oito. GREEN do instrumento offline, não GREEN
semântico ou runtime real. Produção, configuração, modelo da Laylay, treino
e executores não alterados; nenhum commit/liberação. `git diff --check` limpo.

### P01: interferência contextual e ocorrência (09/10)

Protocolo pré-consulta, diagnóstico sem candidato novo. HEAD
`2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, main, worktree anterior preservada.
Sonda `scripts/analises/sonda_interferencia_contextual_v1.py`, SHA256
`f7cf9890d9f730eeeff3817f2272e5b7d450ffda6da890c74b15f4f2b925e939`.
Dependência congelada `sonda_transferencia_papel_isolado_v1.py`, SHA256
`2c9a9c039827ca5283ab3b266b502ccca872f360faba61b1e382ab3b05e22138`.

- 18 casos × dois braços × duas rodadas = 72 consultas. Reusar prompts,
  exemplos, schema, modelo textual histórico e validadores anteriores.
  Rodada dois inverte casos; conjunta precede isolada em cada bloco.
  Arquivo exclusivo `resultados_testes/sonda_interferencia_contextual_v1.jsonl`.
- D0/DN/DA/DB: descrição sem segunda frase, com segunda frase neutra,
  com ação posterior (H11 exato) e ação anterior. Foco e função preservados.
- N0/NN/ND/NS: nome sozinho, contexto neutro, outra ordem de texto distinto
  e outra ordem de texto igual (H05 exato). OS (H06) troca apenas foco no
  texto de NS. NR/OR repetem a troca com ordem das orações invertida.
- C0/CN/CX: título sozinho, contexto neutro e concessão de aparência
  hipotética (H01 exato). Controles T03/T04/T11/T14 preservados integralmente.
- Hipóteses concorrentes: ação fora do foco é necessária para o erro;
  repetição literal é necessária; erro depende da posição; classificação
  já falha sem concorrência. Se D0/N0/C0 falharem, não atribuir seus erros
  exclusivamente à distração. Comparar respostas por par, não só somar
  acertos num painel deliberadamente desbalanceado de diagnóstico.
- Fontes modificadas são intervenções sintéticas conhecidas, não holdout
  independente. Mudança de fonte altera também offsets/tokens e catálogo
  no braço conjunto; controles neutros não igualam tokenização. Portanto,
  um contraste sustenta efeito da intervenção neste painel, não prova
  mecanismo interno geral. Não recortar automaticamente fontes em produção.
- Registrar fonte, mapeamento, requisições e HTTP bruto. Auditar novamente
  o artefato final; flags de autoridade/semântica permanecem falsas.
  Nenhuma alteração de produção, treino, configuração ou liberação da rede.

Resultado: **72 chamadas auditadas**, 38 linhas. HTTP 200/`done=true`/`stop`
e shape válidos em todas. Painel/ordem, hashes, requisições e resumo
reconferidos; requisições e conteúdos de resposta iguais entre as duas
rodadas. Os oito casos herdados reproduziram exatamente as 32 requisições
e conteúdos de resposta correspondentes da coleta anterior, sob IDs novos.
SHA256 do artefato `52b1ff8b88e2e30eeb8b924c3ffdc833e2a6444625bf1222cac6fd6036826057`.
Digest inicial/final `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.

| Contraste | Resultado nas duas rodadas | Limite da conclusão |
|---|---|---|
| D0/DN/DA/DB | Isolado erra só DA, ação posterior; conjunto acerta os quatro | Interferência contextual reproduzida neste par; presença de ação sozinha não basta |
| N0/NN/ND/NS | Isolado erra só NS, ordem posterior com texto repetido; conjunto acerta os quatro | Repetição e ordem importam nesta família, não regra geral de recência |
| NS/OS e NR/OR | Isolado acerta ambos após inversão; conjunto erra OR, selecionando a relação do nome posterior | Identidade é transportada, mas nem sempre respeitada pela decisão; não é colapso de offsets no host |
| C0/CN/CX | Conjunto erra os três; isolado acerta apenas CN, contexto neutro | C0 falha sem oração concorrente: distração não explica todos os erros |
| T03/T04/T11/T14 | Conjunto 3/4, isolado 4/4, repetindo histórico | Não há superioridade universal de um braço |

Primeiras fronteiras observadas: em OR, o foco é a ordem da montadora, mas
o conjunto seleciona `o brinquedo se chama`, referente à outra ocorrência.
Em C0, seleciona corretamente `tem o título` e propõe operação. Assim,
**seleção da relação de outra ocorrência** e **papel incompatível com a
relação selecionada** são erros distintos observáveis; mecanismo interno
compartilhado ainda não demonstrado. Não criar novos IDs de raiz por caso.
H11/DA sustenta interferência da ação posterior; não explica C0 nem permite
atribuir causalidade universal à última oração. Ambiguidade T11 preservada.

Decisão: nenhum patch em produção e nenhum recorte automático de contexto.
Próximo experimento deve testar vínculo explícito com a ocorrência antes
de promover um papel. Reusar inicialmente o braço existente com trecho
real selecionado, sem corrigir seleção com gabarito: DA/NS têm relação
pertinente; OR tem relação de outra ocorrência; C0 tem relação pertinente
mas papel errado. Esse contraste separa possível ajuda da evidência de
propagação de uma seleção errada. A seleção continua proposta, não prova
semântica. Qualquer candidato posterior exige controles inéditos e validação
na composição real; este painel é diagnóstico conhecido.

10 testes locais do instrumento passaram antes da coleta; **1.556 regressivos
relevantes passaram** depois, incluindo esses dez (não somar as contagens).
GREEN do instrumento offline, não encerramento semântico nem runtime real.
Nenhum modelo, configuração, treino, runtime ou executor alterado.
Sem commit/liberação.

### P01: transferência da classificação isolada (09/10)

Protocolo pré-consulta: 16 fontes novas H01–H16 e quatro controles históricos
T03/T04/T11/T14. Novos e históricos reportados separadamente. Quatro exemplos
novos por classe; um controle histórico por classe. Inclui nome de aparência
condicional/descritiva, hipótese/proibição realmente mencionada, título fora
do foco, aspas aninhadas, ambiguidade e duas ocorrências idênticas H05/H06.
Os prefixos/sufixos distratores do experimento anterior permanecem iguais.

- HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, main, alterações anteriores
  preservadas. Sonda/painel `scripts/analises/sonda_transferencia_papel_isolado_v1.py`,
  SHA256 `2c9a9c039827ca5283ab3b266b502ccca872f360faba61b1e382ab3b05e22138`.
  Candidata congelada em
  `3bf0c5a7a545d5977e03126a548089f0c3f7b3e7874b4f066088a479ec24b7ce`.
- Reusar as mesmas funções de coleta, projeção e validação. Primeiro
  resposta conjunta catalogada, depois `papel_sem_trecho`. A classificação
  isolada não recebe a seleção/decisão anterior; nenhum gabarito no prompt.
  Não executar o braço com trecho, que não trouxe ganho no contraste anterior.
- 20 casos × 2 chamadas × 2 rodadas = 80 consultas, casos em ordem inversa
  na segunda rodada. A ordem conjunta→isolada dentro do bloco permanece
  fixa por reutilização do instrumento: não é controle de efeitos temporais,
  nem benchmark de latência. Mudam pacotes de tarefa, não um fator isolado.
- Fontes/referências escritas antes de consultar o modelo; focos novos
  distintos dos exemplos/painéis prévios conferidos. Fontes sintéticas por
  mesma autoria e famílias relacionadas, sem revisão humana independente.
- Critério pré-fixado de superioridade neste painel: mais papéis corretos
  nos novos nas duas rodadas, sem perdas pareadas, preservando os quatro
  controles no isolado. Empate nos novos não comprova superioridade; perda
  não pode ser compensada silenciosamente pelo controle histórico.
- Medir interpretação e transporte por grupo. Não apresentar acerto de
  papel como suporte semântico, execução, autorização ou liberação. Aferição
  de suficiência da seleção continua separada, sem promover o composto.
- 11 testes locais verdes antes da coleta. Metadata, hashes e ordem antes
  das chamadas; arquivo exclusivo
  `resultados_testes/sonda_transferencia_papel_isolado_v1.jsonl`.
  Qwen textual histórico, nenhuma mudança de modelo/configuração da Laylay.
  Coleta pendente ao fixar este protocolo; resultado registrado abaixo.

Resultado auditado: 80 chamadas, 42 linhas preservadas, duas rodadas com
requisições e conteúdos de resposta idênticos por caso/braço. Todas as
respostas HTTP 200, concluídas por `stop`, com shape válido. Metadata/painel,
ordem, hashes, requisições e placar foram reconferidos a partir do bruto;
nenhuma flag de semântica, autoridade ou produção foi promovida.
Digest inicial/final `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
SHA256 do artefato `283a3bb756e8087134eb6b7accd071e8197a6f24fe098e05ed2792f717239aff`.

| Grupo | Conjunto: papel correto | Isolado: papel correto | Pareamento nas duas rodadas |
|---|---:|---:|---|
| 16 novos | 15/16 | 13/16 | Sem ganhos; perdas H05 e H11 |
| 4 históricos | 3/4 | 4/4 | Ganho T03, sem perdas |

O critério pré-fixado falhou: **rejeitada a classificação isolada como
substituta geral**, sem apagar o ganho histórico. H05/H06 têm a mesma fonte
e texto citado, mas focos distintos (`c1`, 53–69; `c2`, 105–121). O conjunto
distingue nome/operação; o isolado responde operação para ambos. Em H11,
o conjunto seleciona `informa a localização` e classifica descrição; o
isolado responde operação, havendo um pedido de mover bancada fora do foco.
H01 falha nos dois: o conjunto seleciona `a expressão pareça uma hipótese`
e propõe expressão; o isolado propõe operação apesar da relação de título.
T03 mantém ganho isolado, embora o conjunto copie corretamente a relação
de título e erre o papel. Portanto, não consolidar seleção errada e papel
errado com seleção correta como se a causa já estivesse demonstrada.

Falsificados neste artefato: perda da identidade pelo host, falha de
transporte/formato e superioridade geral inferida do 8/8 conhecido. Ainda
aberto: mecanismo da confusão contextual; mudar tarefa/schema/exemplos
juntos não permite atribuir causalidade a um componente interno do modelo.
Hipótese seguinte: ligação da ocorrência marcada à relação que a descreve.
Antes de outro candidato, contrastar foco/ocorrência e contexto concorrente
separadamente, preservando fonte integral, ambiguidade e controles. Não
escolher braço por gabarito, acrescentar exceções por frase ou promover
seleção literal a prova semântica. Estes casos agora são diagnóstico,
não holdout inédito de um candidato futuro.

Validação do instrumento: 11 testes focados e **1.546 regressivos relevantes
passaram**. GREEN de testes offline, não GREEN semântico nem runtime real.
Produção/modelo/configuração/treino não alterados; nenhum commit criado.
P01 permanece aberta, sem liberação da rede.

### P01: papel após seleção real, ablação da decisão (09/10)

Protocolo pré-consulta. Hipótese ainda não provada: seleção e classificação
na mesma resposta podem interferir; fornecer o trecho já materializado pode
ajudar a decisão. Não assumir que dividir tarefas resolve o erro. Comparar
classificação isolada sem trecho para distinguir divisão de tarefa de
influência da evidência. Nenhum candidato de produção nesta investigação.

- HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, main, alterações anteriores
  preservadas. Sonda `scripts/analises/sonda_papel_apos_selecao_v1.py`, hash
  `3bf0c5a7a545d5977e03126a548089f0c3f7b3e7874b4f066088a479ec24b7ce`.
  Seletor congelado `39a3e21f02116e70aca87248663e6ce3deee7ad567d474cc7748941999c27565`.
- Oito fontes derivadas conhecidas, T03/T04/T07/T08/T11/T12/T14/T15, duas
  de cada classe, prefixo/sufixo do teste anterior conservados. T03/T04
  contrastam título de aparência condicional e hipótese real. Não é holdout.
- Primeiro executar o seletor catalogado real (predicado + papel); esse
  papel é o controle conjunto. Em seguida duas chamadas independentes:
  `papel_sem_trecho` e `papel_com_trecho`. Mesmo sistema de leitura direta,
  mesmas oito fontes de exemplo, respostas dos exemplos somente com papel,
  mesmo schema de papel. Só a última entrada recebe a evidência no segundo.
- Evidência é o span literal da primeira saída, revalidado pelo contrato.
  Não enviar papel anterior, gabarito, pista esperada, aferição ou feedback
  de acerto. Fonte integral permanece. O sistema avisa nos dois braços que
  uma eventual evidência não tem apoio semântico confirmado nem autoridade.
- Seleção inválida/vazia bloqueia apenas o braço dependente, mantendo-o no
  denominador; controle sem trecho pode rodar. Falha não é substituída pelo
  gabarito. O composto usa a mesma seleção, congelada por bloco, nos três
  braços; classificação correta não repara pista insuficiente.
- Oito blocos × duas rodadas × até três chamadas = até 48 consultas.
  Primeira obrigatoriamente precede as dependentes; alternar AB/BA das
  segundas por caso e inverter ordem na segunda rodada. Controle conjunto
  versus isolado muda pacote de tarefa/schema/exemplos, não um único fator.
  Somente comparação entre as duas segundas isola a evidência adicional.
- Critério para ganho específico da evidência: `com_trecho` superar
  `sem_trecho` em papel e composto nas duas rodadas sem perdas pareadas
  frente ao conjunto. Se ambos isolados melhorarem igualmente, atribuir o
  resultado ao pacote isolado, não à evidência. Se falhar T03, não declarar
  raiz encerrada. Medir transporte, bloqueios e instabilidade explicitamente.
- Artefato exclusivo `resultados_testes/sonda_papel_apos_selecao_v1.jsonl`,
  metadata antes de chamar modelo, primeiras/segundas brutas preservadas.
  Qwen textual histórico, sem treino ou alteração do modelo ativo da Laylay.
  Coleta pendente neste protocolo.

#### Resultado auditado — decisão isolada (09/10)

48 chamadas concluídas em 16 blocos; 18 linhas com metadata/resumo. Artefato
SHA256 `4df5a7f5d6e0fe7f14cd7c5635d02000fd0032701cfc72f8069cabc50ed548ee`.
Reaferição integral do resumo, requisições, fontes, ocorrências, ordem e flags;
48 HTTP 200, `done=True`/`stop`, shapes válidos. Nenhuma segunda bloqueada
nesta coleta (as 16 primeiras tiveram vínculo literal válido). Casos de
bloqueio continuam protegidos pelos testes, não alegados como prova do modelo.
Hashes do script e seletor preservados; digest inicial/final igual ao Qwen
textual histórico. Nenhuma proposta variou entre as duas rodadas.

| Braço (oito casos por rodada) | Papel certo, rodada 1 / 2 | Papel + pista sem distrator, 1 / 2 |
|---|---:|---:|
| Conjunto: seleção + papel | 7 / 7 | 4 / 4 |
| Papel isolado sem trecho adicional | 8 / 8 | 5 / 5 |
| Papel isolado com trecho real | 8 / 8 | 5 / 5 |

O critério de **ganho específico da evidência adicional não foi atendido**:
as duas versões isoladas são iguais no painel. A alternativa pré-declarada
ocorreu: ambas recuperam T03 sem perdas pareadas, nas duas rodadas. O ganho
é do pacote de tarefa isolada, não evidência de benefício de duplicar o trecho
nem demonstração de um mecanismo interno de atenção/carga do modelo.

- T03: primeira seleciona `é o título do ensaio, não uma tarefa` e propõe
  expressão; ambas as segundas propõem nome. A fonte/foco se mantêm íntegros.
  É falsificada, neste caso, a necessidade de acrescentar evidência explícita
  para corrigir a decisão. Não prova que evidência seja dispensável em geral.
- T04 continua hipótese de operação; T07/T08 preservam nome versus proibição
  mencionada; T11/T12 preservam indeterminação; T14/T15 permanecem descrição.
  Esses controles impedem explicar o ganho como promoção indiscriminada a nome.
- T11 acerta papel mas a primeira só seleciona `A função de “`: não cobre a
  pista de indeterminação. T04/T08 também continuam sem toda a referência
  lexical. Por isso 8/8 de papel não virou 8/8 no composto. Fragmento literal
  não é evidência semanticamente suficiente; a guarda não foi enfraquecida.
- Nenhuma segunda recebeu papel anterior, avaliação de acerto ou gabarito;
  somente o braço com trecho recebeu o span selecionado pela primeira.
  Repetição usa nova primeira chamada, não escolha posterior da melhor saída.
- Conjunto versus isolado modifica instrução, schema e respostas dos exemplos;
  não atribuir causalidade exclusiva a número de campos ou ordem de geração.
  A fonte já continha a evidência nos três braços. Oito casos conhecidos não
  demonstram generalização, qualidade geral de ensino ou prontidão da rede.

Decisão: preferir **classificação isolada sem evidência redundante** como
próxima candidata offline, mantendo seleção e suporte como contratos separados.
Não acrescentar segunda etapa dependente do trecho só para reproduzir um ganho
que apareceu sem ele. Próximo passo: validar transferência dessa classificação
em fontes novas e controles históricos; depois medir o custo e a validade no
modelo/runtime realmente usado pela Laylay. O catálogo continua experimental,
com limite de tamanho e lacunas de suficiência; não liberar produção.

13 testes novos passaram antes da coleta. **1.535 testes relevantes passaram
em 134,22 s**, incluindo esses 13; `git diff --check` limpo.
Somente sonda/testes e documentação alterados nesta etapa;
produção, guardas anteriores, exemplos originais e pesos preservados, sem commit.

### P01: predicado catalogado e discriminação de contexto (09/10)

Protocolo pré-consulta: testar a fronteira de cópia sem reutilizar a hierarquia
rejeitada. Reusar tokenizer, blocos externos canônicos, ancoragem única,
materialização e aferição. O host enumera todos os spans contíguos de tokens
externos ao foco que ocorrem uma única vez na fonte. Não procura verbos nem
pista, não classifica papel, não corta saída inválida. Limite offline de
64 tokens na fonte; enumeração quadrática, não projeto de escala de produção.

- HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, main, três documentos já
  modificados preservados. Script `scripts/analises/sonda_predicado_catalogado_v1.py`
  SHA256 `39a3e21f02116e70aca87248663e6ce3deee7ad567d474cc7748941999c27565`.
- Oito casos conhecidos T01/T02/T03/T08/T09/T12/T14/T15, dois por classe,
  com prefixo `Há uma caixa vermelha na mesa. ` e sufixo
  ` O catálogo possui nove páginas.`. Esses distratores entram na fonte,
  sem marcação especial para o modelo. As referências da avaliação ficam
  no host. Painel derivado congelado, não holdout novo.
- `livre` é o proponente contrastivo original. `catalogado` muda somente
  o schema de predicado para enum dos trechos mais string vazia. Prompt,
  mensagens, oito respostas de demonstração, campo papel e parâmetros iguais.
  Nenhum ranking do catálogo por gabarito; 188–270 alternativas por fonte.
  Schema limita as saídas, mas não prova o motivo da escolha.
- 8 casos × 2 braços × 2 rodadas = 32 consultas; AB/BA alternado, segunda
  passagem inversa, sem retentativa seletiva. Metadata captura Git, fonte,
  referências, ordem, hashes e digest antes da primeira chamada. Artefato
  exclusivo `resultados_testes/sonda_predicado_catalogado_v1.jsonl`.
- Requisição efetiva/catalogo autenticados antes de delegar aferição. Guarda
  continua ativa: se backend ignorar enum, seleção fora do catálogo não é
  aceita. Nenhuma correção de grafia ou poda de foco na resposta. Vazio é
  abstenção, não ausência demonstrada ou permissão.
- Além de papel/vínculo/pista/conjunto, aferir presença dos distratores na
  evidência. Seleção discriminativa local exige pista coberta sem tocar os
  dois distratores; conjunto discriminativo exige também papel correto.
  São referências sintéticas locais, não verificação semântica geral.
- Controle sem LLM seleciona os dois blocos externos: cobre pista 8/8, mas
  discrimina 0/8. Critério para continuar candidato: superar esse controle
  e a cópia livre em discriminação nas duas rodadas, sem perdas pareadas de
  papel. Não contar literalidade garantida pelo enum como ganho semântico.
- 16 testes do instrumento verdes antes da coleta, incluindo adulteração,
  saída fora do enum, sobreposição, papel errado com pista certa e selecionar
  tudo. Produção/treino/permissões intactos. Qwen textual histórico confirmado
  pelo digest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`;
  Qwen3-VL instalado não participa desta medição. Coleta ainda pendente aqui.

#### Resultado auditado — catálogo de predicados (09/10)

32/32 HTTP 200, `done=True`/`stop`, shape válido; 34 linhas incluindo
metadata/resumo. Artefato SHA256
`b8c5d9db41fa5624c4abbf17f3d1625b357877f18f254b2f9f44217c4d3217ec`.
Todos os brutos reaferidos; resultado salvo igual ao recalculado. Fontes,
host, enum, requisições, ordem, hashes e flags conferidos, digest igual nos
extremos. Entre braços, apenas o enum do schema difere; entre repetições,
requisições e propostas são idênticas nos 16 pares caso/braço.

Contagens por rodada (oito casos; resultados iguais nas duas):

| Métrica | Cópia livre | Catálogo |
|---|---:|---:|
| Papel alinhado | 7 | 7 |
| Vínculo literal externo | 5 | 8 |
| Pista sem distrator | 4 | 5 |
| Papel + pista sem distrator | 3 | 4 |
| Seleções aceitas com distrator | 0 | 0 |

Critério local para continuar investigando atendido: ganho discriminativo
T12 nas duas rodadas, nenhuma perda pareada de papel ou conjunto. Controle
sem LLM que seleciona todos os blocos cobre pista 8/8 mas discrimina 0/8.
Isso não prova discriminação aberta: os distratores são duas sentenças
fixas e fáceis, em oito fontes derivadas de casos conhecidos.

**Fronteiras observadas:**

- T02/T09/T12 ganham literalidade. O backend respeitou o enum em 16/16
  respostas catalogadas. A restrição exclui foco e reescrita por construção;
  esse ganho estrutural não deve ser contado como compreensão nova.
- T12 passa a `não há contexto para classificar '` e cobre a pista externa
  sem copiar o foco. É o único ganho no composto local. A aspa terminal faz
  parte da fonte; não foi removida pelo host.
- T02 escolhe `recomendou '` e T09 `saber se '`: são fragmentos literais
  admissíveis, mas não cobrem a referência congelada. O caso T09 perde no
  trecho selecionado a indicação de informação ausente. Não promover
  fragmento válido a suporte suficiente. A observação também é compatível
  com continuação limitada pela gramática, não prova raciocínio seletivo.
- T08 continua com `proibiu a operação ao dizer`, literal e compatível,
  mas sem o sujeito incluído na pista de referência. Sua falha de cobertura
  lexical, isoladamente, não demonstra falha semântica.
- T03 seleciona `é o título do ensaio, não uma tarefa` nos dois braços,
  mas propõe expressão sem operação. Fonte, foco e pista são corretos;
  primeiro RED é a proposta de papel, não o transporte ou a cópia. Consertar
  literalidade não basta para interpretar a relação. Nenhuma troca automática
  de papel pelo host, mesmo quando o marcador contém a palavra título.
- T01/T14/T15 preservam conjunto. T03/T15 diferem da coleta sem distratores:
  isso é sensibilidade à fonte modificada, não regressão atribuível ao enum.
  Os braços desta coleta recebem exatamente a mesma fonte.

Decisão: catálogo permanece candidato **estrutural offline**, com ganho
semântico local modesto, não substituto do roteador nem liberação da rede.
Não aumentar o catálogo/treino para esconder T03: próxima fronteira é a
decisão de papel a partir da relação contextual já selecionada, usando
contrastes de nome/operação/descrição e controles de ambiguidade. Preservar
também T09 como insuficiência de evidência, sem fundir essas duas causas.
Antes de qualquer promoção, ainda faltam transferência para fontes novas,
evidência suficiente além da cobertura lexical, custo em textos maiores e
validação no modelo/runtime efetivamente usado pela Laylay.

Produção, guardas históricas, exemplos e pesos não alterados. Escopo desta
continuação: sonda/testes novos e três documentos de acompanhamento, sem
commit. Os 16 testes novos passaram antes da coleta; **1.522 testes relevantes
passaram em 109,91 s**, incluindo esses 16 (contagens sobrepostas).
`git diff --check` limpo. Não houve validação de produção nesta coleta.

### P01: transferência da hierarquia sem ajuste do proponente (08/10)

Protocolo pré-consulta: 16 casos novos escritos antes de consultar o modelo,
quatro por classe, incluindo quatro pares nome/operação, aspas aninhadas,
ressalva, texto repetido com ocorrências diferentes e ação fora do foco.
São variações sintéticas das famílias conhecidas, não revisão independente
nem prova de generalização aberta. Referências permanecem somente no host.

- HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch `main`, worktree
  paralela preservada. Script/painel juntos em
  `scripts/analises/sonda_hierarquia_transferencia_v1.py`, SHA256
  `3c4f4631ac6113a23a9749c9d65f163d260c2f6b909b8647a834ac82ba663636`.
- Dependência hierarquia congelada em
  `5a6612b1df26195f6a6d4a8f2040874789dcd5b24eda14023e4de46c2447adc9`;
  reutiliza sua projeção, coleta e aferição. Nenhuma alteração de prompt,
  exemplos, schema, parâmetros, identidade canônica, guardas ou pesos.
- `base` versus `hierarquia`, duas repetições, ordem dos braços alternada
  por caso, segunda passagem inversa: 64 consultas. Não uniformizar IDs.
  Metadata registra fontes, referências, ordem, hashes, estado Git e digest
  antes da coleta; arquivo exclusivo
  `resultados_testes/sonda_hierarquia_transferencia_v1.jsonl`.
- Critério descritivo pré-fixado: ganho de papel nas duas repetições sem
  perdas pareadas de papel e sem queda do conjunto em cada repetição.
  Se falhar, não tratar hierarquia como melhoria geral; conservar ganhos e
  perdas por caso. Mesmo atendido, não autoriza produção. Conjunto continua
  métrica lexical congelada, distinta de validade semântica independente.
- Relatar instabilidade com requisição idêntica, vínculo literal separado
  do papel, sobreposição/paráfrase e falsos indeterminados. Sem correção
  automática de propostas, retentativa seletiva ou seleção do melhor resultado.
- Escopo: uma sonda com painel, seus testes e documentação. Produção
  inalterada; não é teste do runtime Laylay. Coleta pendente neste protocolo.

#### Resultado auditado da transferência (09/10)

As 64 consultas terminaram; arquivo com 66 linhas, SHA256
`6dc537f3a31af138ebf38f4911bcb778939125e6cda8ab0c6cf19f1a5e4ce56c`.
Reaferição integral reproduziu todas as métricas salvas a partir dos brutos:
64 HTTP 200, shape válido, `done=True`/`stop`, sem retentativas. Requisições,
host, fontes, ordem, referências e seis flags falsas conferidos. Digest
inicial/final igual: `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Script/painel e dependências congeladas continuam com os hashes do protocolo.

Na retomada de 09/10, HEAD é `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`,
branch `main`, worktree limpa antes desta documentação. O commit externo
incorporou os arquivos preparados; não foi criado nesta investigação.
Preservado o baseline da coleta `90a2fb8`, sem atualizar trava cegamente.

Resultados idênticos nas duas repetições; não variou nenhuma das 32
propostas pareadas entre rodadas:

| Métrica (16 casos por braço/rodada) | Base | Hierarquia |
|---|---:|---:|
| Papel alinhado | 15 | 15 |
| Vínculo literal estrutural | 13 | 11 |
| Pista lexical congelada | 11 | 8 |
| Papel + pista | 10 | 8 |
| Falso indeterminado | 0 | 1 |

**Critério pré-fixado não atendido.** A hierarquia não é aceita como
melhoria geral, apesar do ganho anterior nos casos conhecidos. T15 ganha
papel, T03 perde; no conjunto ganha T15 e perde T01/T03/T14, nas duas rodadas.
Não escolher o melhor braço por ID de caso nem adaptar a resposta ao gabarito.

- T03: fonte identifica expressamente um título, apesar da forma condicional.
  Base acerta; hierarquia propõe indeterminado e `parece uma condição`, que
  nem é trecho literal da fonte (`pareça`). Primeiro RED é já na proposta,
  antes da ancoragem. Não é falha de transporte, identidade ou truncamento.
- T15: fonte descreve localização e menciona outra ação depois. Base seleciona
  a pista correta mas propõe nome; hierarquia propõe descrição corretamente.
  Isso falsifica seleção literal como explicação única dos erros de papel.
- T01: ambos acertam papel; hierarquia inclui o próprio foco no predicado.
  T14: ambos acertam papel; hierarquia remove acentos de `composição`.
  Guardas recusam corretamente essas propostas; não normalizar/cortar o
  texto para transformar regressão em sucesso.
- T09/T12 continuam sem evidência aceita: paráfrase ou sobreposição. T02
  melhora vínculo estrutural com hierarquia, mas não inclui a pista inteira.
  T04/T08 também selecionam trechos literais sem todo o marcador escolhido.
  Falha da métrica lexical isolada não prova erro semântico nesses casos.
- T05/T06 preservam as duas ocorrências de texto idêntico e seus papéis.
  Não houve reutilização de focos dos exemplos/painéis anteriores verificados.
  As fontes novas são sintéticas e próximas às famílias conhecidas; não
  constituem avaliação humana independente nem cobertura aberta de linguagem.

Decisão: conservar a base como controle e parar de ampliar essa hierarquia
como candidata geral. Próximo trabalho é o contrato de seleção de evidência,
sem fundi-lo com classificação: inventariar os seletores já existentes e
contrastar a escolha de trechos materializados pelo host com a cópia livre.
Reusar `sonda_contextos_enumerados_v1`/`sonda_vinculo_duas_etapas_v1` somente
após conferir seus limites históricos; não simplesmente repetir uma solução
anterior nem fornecer o marcador esperado ao seletor. Um intervalo literal
não comprova apoio semântico e um papel correto não conserta evidência inválida.
T03/T15 permanecem controles separados de interpretação para qualquer candidato.

Limite histórico relido: o inventário de dois blocos externos de 06/10 teve
20/20 seleções de todos os blocos, igual ao controle sem LLM. Reutilizar a
materialização segura não significa adotar esse seletor como resolvido.
Qualquer contraste seguinte precisa distinguir apoio relevante de contexto
completo e comparar explicitamente contra selecionar tudo; do contrário
repetirá um GREEN estrutural já conhecido, sem avanço semântico.

Validação: **31 testes focados** passaram antes da coleta (13 desta sonda e
18 da interface anterior). Na retomada, **1.506 testes relevantes passaram
em 102,28 s**; incluem os focados, não somar. `git diff --check` limpo.
Nesta retomada foram alterados somente plano, registro e mapa causal.

Não houve alteração de produção, treino, memória, permissões ou composição
da Laylay. P01 continua aberta. Resultado atual é rejeição de uma candidata
offline por evidência, não correção do runtime nem liberação da rede.

### P01: hierarquia sintática e identidade de transporte (07/10)

Protocolo pré-consulta. O diagnóstico de moldura mudou fonte, pontuação,
profundidade, IDs e offsets juntos. Este fatorial mantém fontes/offsets e
isola dois fatores de interface: explicitação do caminho de aspas até o foco
e etiqueta de transporte `foco.id`. Reusa `preparar_entrada`, o catálogo e o
mapeador canônico de aspas; não introduz parser de domínio ou leitura semântica.

- HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`; worktree preservada.
  Sonda `scripts/analises/sonda_hierarquia_identidade_v1.py`, SHA256
  `5a6612b1df26195f6a6d4a8f2040874789dcd5b24eda14023e4de46c2447adc9`.
  Proponente anterior continua congelado em
  `45cdb3e8fe8802d65fed5c6d38b1e69608ca74eaf4930663643706d5dc326244`.
- Dez casos conhecidos: E04A/E04B/U04/N03, E03A/E03B, U02/N06 e E05A/E05B.
  Os últimos têm texto repetido em ocorrências diferentes; não podem ser
  fundidos pela etiqueta de transporte. Nenhuma fonte é reescrita ou recortada.
- Quatro braços: `base`, `id_uniforme`, `hierarquia`, `hierarquia_id_uniforme`.
  No fator ID, somente `foco.id` enviado ao modelo passa a `c1`. IDs de regiões,
  fonte, offsets e texto não mudam. Identidade canônica fica intacta no host;
  nenhuma resposta operacional usa o rótulo de transporte. Em focos já c1,
  esse fator produz requisições idênticas, úteis como controle de variação.
- Hierarquia acrescenta `hierarquia_sintatica_do_foco`, com fonte_id,
  regiões ancestrais externa→interna e cópia da ocorrência marcada.
  Tudo deriva da árvore/offsets autenticados; não inclui pista, papel esperado,
  justificativa ou interpretação da moldura. Fonte integral e metadados
  originais continuam presentes. É redundância de apresentação, não nova prova.
- A mesma projeção é aplicada às oito entradas de demonstração e à entrada
  final. Respostas dos exemplos, prompt de sistema, schema, opções e modelo
  permanecem idênticos. Aumentar saliência/texto/tokens é parte desse fator;
  eventual ganho não isola estrutura de repetição ou comprimento do prompt.
- Dez casos × quatro braços × duas repetições = 80 consultas. Braços rotacionam
  por caso; segunda passagem inverte blocos e ordem. Não há balanceamento
  perfeito por posição em dez casos, nem 80 fontes independentes. Metadata,
  referências/ordem/hashes antes das consultas; sem retentativa ou ajuste.
- O aferidor valida a requisição efetiva exata antes de delegar a saída bruta
  ao aferidor anterior. A ponte transitória só adapta seu envelope de chamada;
  texto proposto, host, offsets, flags e evidência HTTP não são reescritos.
  Artefato conserva a requisição efetivamente enviada. Testar adulteração
  antes dessa delegação para não mascarar divergência de protocolo.
- Sinal pré-fixado para investigar a hierarquia: recuperar E04A/U04 nas duas
  repetições, sem perder papéis dos controles antes corretos nem reduzir
  conjunto local. Medir separadamente a mesma comparação com ID uniforme.
  E03A permanece controle aberto, não exigir nem alegar sua correção por aspas.
  Um efeito apenas do ID não conta como prova do benefício da hierarquia.
- Saída exclusiva `resultados_testes/sonda_hierarquia_identidade_v1.jsonl`.
  Somente sonda/testes/documentação; produção, guardas, exemplos e treino
  inalterados. Coleta pendente neste registro; não há holdout novo ou promoção.

#### Resultado auditado — hierarquia e identidade

Coleta concluída: 80/80 HTTP 200, `done=True`, `done_reason=stop`, shape
válido; 82 linhas incluindo metadata/resumo. Reaferição dos brutos reproduziu
integralmente aferições e resumo, com requisições efetivas, fontes, ordem,
ocorrências e flags conferidas. SHA256 do artefato
`f30eece03a5110f81119f786b7d891fea9ecc03e37851519e0e46d77dc2b28b3`.
Script/dependências/dados congelados preservados. Digest inicial/final do
Qwen `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.

Contagens por repetição, sempre sobre os mesmos dez casos conhecidos:

| Braço | Papel 1 / 2 | Vínculo estrutural 1 / 2 | Pista 1 / 2 | Conjunto 1 / 2 |
|---|---:|---:|---:|---:|
| base | 7 / 7 | 7 / 7 | 5 / 5 | 4 / 4 |
| id_uniforme | 7 / 7 | 6 / 7 | 5 / 5 | 4 / 4 |
| hierarquia | 10 / 9 | 7 / 6 | 6 / 4 | 6 / 4 |
| hierarquia_id_uniforme | 10 / 9 | 7 / 6 | 5 / 4 | 5 / 4 |

O sinal pré-fixado para continuar investigando foi atendido nos dois
contrastes: E04A/U04 recuperam papel nas duas repetições; nenhum papel de
controle correto se perde; conjunto não diminui frente ao braço pareado.
Isso não representa ganho repetido no conjunto: na segunda rodada ambos
os braços com hierarquia empatam com a base em 4/10. Zero falsos indeterminados.

- **Prova localizada:** E04A muda de operação para nome e U04 de expressão
  para indeterminado, mesmo com fonte/offsets intactos. Uniformizar apenas
  `foco.id` não recupera nenhum papel. Falsificada a explicação de que essa
  troca isolada de ID bastaria, não toda influência possível de identificadores.
- **Estabilidade ainda aberta:** E03A acerta nome somente na primeira
  repetição com hierarquia; na segunda volta a expressão e propõe trecho
  não literal. As requisições são idênticas entre repetições. Como seu foco
  já é c1, os dois braços com hierarquia também têm requisições idênticas:
  essa oscilação não é efeito causal do fator ID. Temperatura zero não
  garantiu saída idêntica. Não há evidência para atribuir a oscilação a cache
  ou a uma causa interna específica.
- **Seleção não corrigida:** E04A passa a copiar o foco junto de `batizada`,
  recusado por sobreposição; E04B faz isso nos quatro braços. U02 mantém
  paráfrase/junção não contígua. Não recortar a proposta nem afrouxar a guarda
  para aproveitar um papel correto. Em U04, hierarquia seleciona a pista
  completa só na primeira rodada; nas demais seleciona um trecho literal
  que omite `perdeu o contexto`. N06 seleciona `informa uma propriedade`,
  literal e compatível, mas sem o marcador lexical congelado. Métrica de
  pista não é veredito geral de falsidade semântica.
- **Controles:** N03/E03B/E05A/E05B preservam papel e conjunto em todos os
  braços/repetições. E05A/B continuam ocorrências distintas apesar do mesmo
  texto. Requisições base são idênticas às da coleta contrastiva anterior;
  seus predicados variam em E03B (duas rodadas) e U02 (primeira), sem mudança
  nas métricas locais. Não interpretar reexecução como determinismo perfeito.
- **Limite causal:** a intervenção inclui redundância, saliência e projeção
  dos exemplos, além de estrutura. Tokens de entrada registrados: 2563–2629
  na base e 3738–3865 com hierarquia. Não isola hierarquia de comprimento/
  repetição, nem mede desempenho de latência. Dez casos selecionados não
  são holdout novo, nem 80 observações independentes.

Validação local: 18 testes novos passaram; regressão das sondas e contrato
de proposições, **1.493 passed**, inclui esses 18 (não somar as contagens).
Produção, composição de `laylay.py`, guardas, respostas dos exemplos, pesos,
memória e permissões não foram alterados; nenhum commit criado.

Próxima fronteira: preservar esta interface como candidata offline e avaliar
estabilidade/generalização em fontes novas, congeladas antes das consultas.
Separadamente, investigar seleção literal externa ao foco, reaproveitando
os seletores existentes, sem usar rótulo correto como prova de evidência e
sem alimentar respostas do painel ao proponente. E03A permanece RED de papel;
sobreposição/paráfrase são REDs de seleção. P01 aberta, sem runtime real,
treino, promoção operacional ou alegação de rede liberada.

### P01: diagnóstico de moldura e foco (07/10)

Protocolo pré-consulta: localizar por que o mesmo proponente com exemplos
falha em E04A/U04/E03A, antes de qualquer candidato de produção. Fonte,
offset e foco dos registros históricos são autênticos; a proposta bruta já
contém o papel errado, antes da ancoragem. U04 conserva pista literal e erra
papel, logo erro de cópia não explica sozinho essa interpretação.

- HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`; worktree paralela
  preservada. Sonda `scripts/analises/sonda_moldura_foco_v1.py`, SHA256
  `29094aad4729847325fd85cc9db2c988b787ee8c14edc8a1e2fea8dd375fd0c4`.
  Proponente anterior preservado em
  `45cdb3e8fe8802d65fed5c6d38b1e69608ca74eaf4930663643706d5dc326244`,
  com os mesmos oito exemplos, prompt, schema e opções. Reusar coleta,
  aferição e guardas anteriores, sem duplicar parser ou corrigir propostas.
- E04A/E04B/U04/N03: fonte original; citação plana mantendo frase introdutória;
  somente conteúdo interno. A versão plana troca aspas externas por dois-pontos
  para conservar uma apresentação legível: não isola exclusivamente um caractere
  de aspas. A versão interna remove também a frase introdutória. São fontes
  contrafactuais sintéticas, nunca reescrita automática em produção.
- E03A: original; sem ressalva sobre forma de hipótese; ressalva anteposta.
  A posição/capitalização varia no último braço, mas título e foco continuam
  os mesmos. E03B controla a hipótese realmente apresentada como operação.
  U02 controla classificação correta com paráfrase; N06 controla trecho literal
  sem a pista lexical escolhida. Nenhum desses controles é corrigido pelo host.
- 18 fontes variantes, duas repetições (36 chamadas), segunda em ordem inversa.
  Fontes/focos derivados de casos conhecidos: não há holdout novo nem revisão
  humana independente. IDs/variantes/referências ficam no host; os exemplos e
  demais mensagens não mudam. Nos originais, a requisição é idêntica à histórica.
- Conferir papel, vínculo, pista, conjunto e finalização por variante/repetição;
  não somar como amostra independente. Uma melhora só na variante simplificada
  não corrige o original nem autoriza descartar contexto. Observar se erro
  persiste após remover cada moldura e se os controles positivos sobrevivem.
  Isso discrimina hipóteses de sensibilidade contextual, não mecanismo interno.
- Metadata com fontes/referências/ordem/hashes antes das chamadas; arquivo
  exclusivo `resultados_testes/sonda_moldura_foco_v1.jsonl`. Falhas e truncamentos
  permanecem nos resultados. Coleta pendente neste registro pré-consulta.

#### Resultado auditado — moldura e foco

36/36 consultas concluídas com HTTP200, JSON, shape válido, `done=true` e
`done_reason=stop`. As 18 propostas completas se repetiram nas duas passagens.
Artefato com 38 linhas: `resultados_testes/sonda_moldura_foco_v1.jsonl`, SHA256
`e300f1c856dd928502704a700bc8aa41cbc8cb122ee05dc146ac5c6867d5f023`.
Auditoria releu brutos, fontes pré-consulta, requisições, ordem e referências;
recalculou aferições/resumo sem confiar em métricas salvas. As 16 requisições
dos oito originais são idênticas às históricas correspondentes. Hashes de
sonda/proponente/dados preservados. Digest Qwen inicial/final igual:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.

O quadro resume papel alinhado à referência local nas duas repetições;
não mede compreensão geral nem prova vínculo semântico.

| Família | Original | Citação plana | Sem frase introdutória |
| --- | --- | --- | --- |
| E04A, nome aninhado | errado: operação | nome correto | nome correto |
| U04, contexto indeterminado aninhado | errado: estado | indeterminado correto | indeterminado correto |
| E04B, operação aninhada | correto | correto | correto |
| N03, estado aninhado | correto | correto | correto |

Em E03A (título com forma de hipótese), o original recebe estado; sem ressalva
recebe nome corretamente; com ressalva anteposta recebe operação, ainda errado.
Na última versão, o predicado proposto é “a exposição foi intitulada”, literal
e cobrindo a pista nominal, mas o papel continua sendo operação. E03B, que
realmente apresenta uma hipótese de operação, permaneceu correto.

Cadeia causal e hipóteses discriminadas:

1. **Host → foco correto, proposta → papel errado.** Os offsets das fontes
   originais recortam exatamente a ocorrência pretendida (c2 em E04A/U04,
   c1 em E03A); a proposta HTTP bruta já erra antes da ancoragem. Falsificada
   a hipótese de o host ter enviado outro trecho ou de a guarda ter trocado
   o papel. Isso não prova que o modelo usou o foco corretamente.
2. **Falta de pista não explica todos os erros.** U04 seleciona a mesma pista
   de contexto perdido nas três apresentações, mas só erra o papel na original.
   E03A com ressalva anteposta seleciona a atribuição nominal e ainda erra.
   Não resolver esses casos apenas melhorando recópia ou cobertura lexical.
3. **Verbo introdutório isolado não basta.** A versão plana mantém “registra”
   ou “diz” e corrige E04A/U04. Há sensibilidade à apresentação/estrutura do
   foco, não prova de que aqueles verbos determinem o erro. A transformação
   também altera pontuação, profundidade, IDs c2→c1 e offsets; não foi isolado
   qual desses fatores produziu o ganho. N03/E04B originais corretos impedem
   declarar incapacidade geral de ler citações aninhadas ou foco c2.
4. **Posição final da ressalva não é explicação suficiente.** Antepor a ressalva
   de E03A muda o rótulo errado, mas não recupera o nome. Retirá-la recupera.
   Sustenta interferência do contexto sobre forma hipotética na atribuição de
   função, sem identificar mecanismo interno ou provar que toda concessiva falha.
5. **Seleção e papel seguem fronteiras distintas.** E04B acerta o papel mas
   inclui foco no predicado nas três versões, recusadas pela guarda. U02 acerta
   indeterminação e continua propondo paráfrase ausente da fonte. Logo,
   aninhamento não é necessário para esses defeitos de seleção literal.

Limites da aferição mantidos: E04A sem moldura escolhe “batizada”, literal e
nominal, mas não cobre toda a pista congelada “a oficina batizada”; N06 conserva
“informa uma propriedade” sem cobrir “A descrição visual”. Ambos permanecem
fora do conjunto por cobertura local; não transformar isso em novo bug nem
alterar referência após coleta. Nenhuma abstenção falsa foi produzida nos
controles conclusivos; a amostra pequena não garante segurança futura.

Decisão: não remover aspas, frases introdutórias ou ressalvas em produção.
O resultado demonstra sensibilidade contextual nesta sonda; não encerra P01.
Próximo candidato de interface a investigar: explicitar a hierarquia sintática
fonte → citação externa → foco com trechos/offsets autenticados, conservando
a fonte integral, sem acrescentar interpretação, pista manual ou autorização.
Conferir primeiro os mecanismos já existentes de aspas/foco e fazer controles
de representação/identidade para não atribuir ao aninhamento um efeito de ID.
E03A deve continuar como controle aberto: hierarquia de aspas por si só não
foi demonstrada como solução para a interferência da ressalva. Não alterar
exemplos, prompt e guardas juntos nem repetir novas variações sem hipótese.

Validação: 14 testes novos, 35 focados, 1.475 na regressão das sondas/contrato,
sem somar contagens sobrepostas. Escopo desta investigação: uma sonda offline,
seus testes e estes registros. Produção, dados/exemplos anteriores, materializador,
treino e memória factual intactos; nenhum commit ou efeito externo na Laylay.

### P01: ensino contrastivo com avaliação separada (07/10)

Protocolo pré-consulta. Hipótese: exemplos de funções diferentes para a mesma
forma superficial ajudam mais que repetir a prioridade da indeterminação.
O experimento anterior mostrou que selecionar a pista correta não assegura
papel correto; não declarou incapacidade do modelo ou causa interna única.
Este contraste altera apenas as mensagens de demonstração, mantendo prompt
de sistema, entrada final, schema, modelo, opções e materializador da base
`predicado_host`. São exemplos no contexto, não treinamento dos pesos.

- HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`; worktree paralela
  preservada. Produção, guardas e sondas congeladas anteriores intocadas.
- Dados `scripts/analises/dados/sonda_ensino_contrastivo_v1.json`, SHA256
  `becead72f0fde7b20cc46e50741aeaa6b65c4da8c320b562e3db08e5670d01d5`:
  oito demonstrações (duas por classe) e 24 avaliações novas (seis por classe).
  As demonstrações reutilizam duas formas imperativas em nomes, operações e
  indeterminação; incluem dois estados descritivos. Avaliação contém seis
  pares nome/operação, seis estados e seis indeterminados, incluindo
  nome versus estado, aspas aninhadas, duas ocorrências iguais e ação fora do
  foco. Focos não se repetem entre demonstração/avaliação/painel anterior.
- Dados e referências são elaborados pelo mesmo agente antes da coleta,
  com estruturas relacionadas: avaliação separada não significa corpus
  independente, amostra aleatória ou revisão humana. Não chamar de prova
  geral de compreensão. Referências de avaliação e justificativas ficam
  somente no host. Modelos recebem respostas apenas das oito demonstrações.
- Sonda `scripts/analises/sonda_ensino_contrastivo_v1.py`, SHA256
  `45cdb3e8fe8802d65fed5c6d38b1e69608ca74eaf4930663643706d5dc326244`;
  dependência `sonda_predicado_host_v1.py` preservada em
  `cabbfe97fa3c2f2e1711dda5cdce3f0c2343ba08475c953bde6e2f20257aa01c`.
- 24 casos × dois braços × duas repetições = 96 chamadas independentes.
  Primeira repetição alterna AB/BA; segunda inverte ordem dos casos e de
  cada par. São 24 casos, não 96 observações independentes. Mesma requisição
  repetida sem seed novo, sem retentativa, escolha da melhor saída ou mudança
  após observar resultados. Temperatura zero não é prova de determinismo.
- Critério descritivo pré-fixado para merecer nova investigação: em ambas
  as repetições, candidato completo em 24/24, conjunto estritamente maior,
  papel total não inferior, indeterminação estritamente melhor, nenhuma
  classe conclusiva com menor contagem e nenhum aumento de falsos
  indeterminados. Contar ganhos/perdas por ID e papéis iguais nas duas
  repetições; igualdade não significa acerto. Não é teste de significância,
  aprovação de produção ou compensação de um erro individual por outro acerto.
- Conjunto exige papel local + vínculo literal + pista pré-fixada. Pista
  é cobertura lexical, não relação semântica provada. Outra formulação correta
  pode não cobrir a pista; não mudar referências após coleta. Truncamento,
  JSON inválido e falha de transporte permanecem no denominador.
- Saída exclusiva `resultados_testes/sonda_ensino_contrastivo_v1.jsonl`,
  metadata/ordem/referências/hashes antes da primeira consulta, envelopes
  brutos preservados, resumos recalculados deles. Nenhuma flag de semântica,
  autoridade, vigência ou aprovação pode ser promovida.

Instrumento: 20 testes locais passaram antes de acrescentar o controle de
critério positivo versus perda de classe conclusiva. Coleta ainda não iniciada
neste registro pré-consulta; executar somente após revalidar esse controle.

#### Resultado auditado — ensino contrastivo

Controle adicional validado antes da coleta: 21 testes novos; 136 testes
focados passaram. Regressão posterior das sondas e contrato de proposições:
1.461 testes passaram. Suítes se sobrepõem, não somar. Nenhum desses verdes
transforma o rótulo do modelo em evidência semântica ou valida o runtime.

96/96 consultas concluídas com HTTP200, JSON, shape válido, `done=true` e
`done_reason=stop`. Artefato com 98 linhas (metadata + consultas + resumo):
`resultados_testes/sonda_ensino_contrastivo_v1.jsonl`, SHA256
`edc1651808f9a3a24e7868bdc0c7ec2a87f3efad305a1ef32640c1695504f6a2`.
Auditoria releu cada envelope bruto, confirmou requisições, referências e
ordem pré-consulta e recalculou as 96 aferições e o resumo. Hashes de script,
dados e dependência preservados. Digest inicial/final do Qwen:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.

| Medida | Base, repetição 1 | Exemplos, repetição 1 | Base, repetição 2 | Exemplos, repetição 2 |
| --- | ---: | ---: | ---: | ---: |
| Papel alinhado /24 | 12 | 21 | 12 | 21 |
| Vínculo estrutural /24 | 16 | 20 | 16 | 21 |
| Pista local /24 | 7 | 17 | 7 | 18 |
| Conjunto /24 | 5 | 16 | 5 | 17 |
| Nome /6 | 4 | 4 | 4 | 4 |
| Operação mencionada /6 | 4 | 6 | 4 | 6 |
| Expressão de estado /6 | 4 | 6 | 4 | 6 |
| Indeterminado /6 | 0 | 5 | 0 | 5 |
| Falso indeterminado /18 conclusivos | 0 | 0 | 0 | 0 |
| Pares com ambos os papéis alinhados /6 | 2 | 4 | 2 | 4 |

O critério pré-fixado foi atendido nas duas repetições. Isso justifica
continuar investigando a abordagem de demonstrações, não liberá-la. O papel
ganhou nos mesmos dez casos (E02B/U01/N02/U02/E05A/E06B/U03/U05/N06/U06),
mas perdeu E04A nas duas repetições. A contagem nominal 4→4 esconde essa troca;
não equivale à ausência de regressão individual. O conjunto ganhou 11 casos
na primeira e 12 na segunda, sem perdas nessa métrica, mas tampouco anula a
regressão de papel em E04A, cujo conjunto da base já estava inválido.

Estabilidade observada: os 24 papéis se repetiram dentro de cada braço, tanto
corretos quanto errados. Todas as propostas da base foram iguais; no candidato,
U02 e U06 mudaram apenas o predicado. U02 continuou sem ancoragem; U06 passou
de paráfrase recusada para trecho literal válido. Conjunto correto nas duas
repetições: 5/24 base, 16/24 candidato. Duas execuções não provam estabilidade
geral. Contexto do candidato acrescentou 1.818 tokens de prompt: 2.552–2.629
contra 734–811; não houve benchmark isolado de latência.

Pendências distintas dentro da P01, sem novos IDs de raiz:

- **Papel contextual ainda errado:** E03A (título com forma de hipótese),
  E04A (nome dentro de aspas aninhadas, regressão) e U04 (indeterminação
  dentro de aspas aninhadas). Em U04 o candidato copia a pista correta de
  contexto perdido e continua classificando como expressão de estado.
  Portanto, falta de pista selecionada não explica esse erro.
- **Seleção literal:** E04B acerta papel, mas inclui o foco no predicado;
  U02 acerta indeterminação, mas substitui o começo da fonte por “não sabemos
  se...”, inexistente nela. E03A propõe “tem forma de hipótese”, também
  ausente; U06 falha por paráfrase só na primeira repetição. Materializador
  recusa esses trechos sem reescrever nem preencher a fonte. A semelhança de
  U02 com a demonstração D07 sugere transferência de formulação, mas não prova
  mecanismo interno nem torna a citação inventada aceitável.
- **Limite da métrica lexical, não bug automaticamente:** N06 seleciona
  “informa uma propriedade”, literal e compatível com descrição, mas não
  cobre a pista congelada “A descrição visual”. E06B seleciona “foi citado
  pelo revisor”, literal, mas sem a pista “O pedido”; citação isolada não
  decide o papel. Ambos ficam fora do conjunto por cobertura. Não atualizar
  o gabarito pós-coleta, nem criar patch para forçar palavras da referência.

Conclusão restrita: acrescentar estas oito demonstrações melhorou os resultados
deste painel nas duas repetições, com ganho real sobre sua base contemporânea.
Não compara percentuais com o painel anterior de 32 casos; não isola conteúdo
contrastivo de tamanho/ordem do contexto; não prova aprendizagem durável.

Próxima fronteira: estudar a atribuição de função ao foco em molduras aninhadas
e concessivas, preservando os ganhos de indeterminação. E04A serve de regressão
obrigatória; U04 separa falha semântica de falha de seleção. Conservar também
o contrato de literalidade em U02/E04B, sem corrigir resposta por gabarito.
Antes de novos ajustes, distinguir erro de papel, trecho inválido e mera
ausência da pista local. P01 segue aberta; nenhum treino, integração runtime,
memória factual, autorização ou commit realizado.

### P01: unidade externa e prioridade da indeterminação (07/10)

Protocolo congelado antes da coleta. Duas hipóteses de interface, sem atribuir
causa interna à rede: (A) chamar a unidade de `predicado` contribui para copiar
orações incluindo o foco; (B) explicitar a decisão de indeterminação antes
dos rótulos conclusivos ajuda quando a fonte mantém funções alternativas.
O diagnóstico anterior mostrou 15 seleções incluindo foco/outra ocorrência,
além de U02 com pista de incerteza copiada e papel errado. Uma causa única
para geometria e abstenção ainda não foi demonstrada.

- HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch `main`; worktree
  paralela preservada. Sonda `scripts/analises/sonda_unidade_abstencao_v1.py`,
  SHA256 `31e3696dfc86eaf5e141eb720c926794a99b9f8000da32b6883b111e8683ced2`.
  Dependência `sonda_predicado_host_v1.py` congelada em
  `cabbfe97fa3c2f2e1711dda5cdce3f0c2343ba08475c953bde6e2f20257aa01c`.
- Fatorial 2×2: `predicado`, `trecho_externo`, `predicado_abstencao`,
  `trecho_externo_abstencao`. Primeiro fator troca apenas nome do campo e
  suas menções no prompt; preserva ordem/propriedades/required do schema.
  Segundo fator acrescenta instrução inicial de verificar se a fonte decide
  uma função ou mantém alternativas sem decisão. Não inclui frases de teste,
  referências locais ou novos exemplos no prompt.
- Mesmo materializador real da sonda anterior. Adaptador traduz apenas nome
  de campo após validar shape completo; valores não são reescritos, cortados
  ou preenchidos. Texto e ocorrência do host permanecem canônicos. Papel
  proposto não é corrigido por pista lexical, gabarito ou regra de abstenção.
- 32 casos conhecidos, referências e pistas anteriores intactas. Fonte,
  foco, aspas, modelo e opções idênticos. 128 chamadas independentes, ordens
  em quadrado latino: cada variante aparece oito vezes em cada posição.
  Sem retentativa ou ajuste após saída. Metadata pré-consulta, saída exclusiva
  `resultados_testes/sonda_unidade_abstencao_v1.jsonl`.
- Métricas: shape, rótulo local, vínculo estrutural, pista no trecho selecionado,
  conjunto, repetição textual do foco no trecho e falso `indeterminado` nas
  28 fontes conclusivas. Repetição textual é diagnóstico, não prova de que
  corresponde à ocorrência certa nem nova guarda. Reportar quatro inconclusivos
  separadamente e manter falhas/truncamentos no denominador completo.
- Comparações de fatores dentro dos dois níveis do outro fator, com IDs de
  ganhos/perdas. `ganho_booleano` significa aumento da métrica, não melhoria
  quando a métrica é cópia do foco ou falso indeterminado. Não combinar braços
  como se fossem 128 fontes independentes. Cada caso continua sendo uma fonte
  conhecida; não há novo holdout, revisão humana independente ou runtime Laylay.
- 19 novos testes passaram; 115 focados passaram antes do ajuste pré-coleta
  que preserva ordem das propriedades; os 19 foram revalidados após esse ajuste.
  Guardas existentes, produção, treino e artefatos históricos preservados.

No congelamento acima, a coleta estava pendente. Resultado posterior abaixo;
mesma P01 aberta, sem promoção de interface, autorização, memória ou commit.

#### Resultado do fatorial e decisão — 07/10

128/128 chamadas concluídas com HTTP 200, JSON, shape válido, `done=true`
e `done_reason=stop`. Auditoria posterior releu os envelopes brutos, conferiu
as requisições, a ordem, as referências pré-consulta e recalculou cada aferição
e o resumo. Artefato com 130 linhas (metadata + 128 consultas + resumo):
`resultados_testes/sonda_unidade_abstencao_v1.jsonl`, SHA256
`645e7b5c973c8cf904417fd6b24cdbf2daef6c068adbe2c3f1b95b47a1b3aef2`.
Script, dependência e painel conservam os hashes pré-consulta. Digest do modelo
igual nas leituras inicial/final:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Isso não é monitoramento contínuo do servidor nem prova de determinismo.

Todas as métricas abaixo usam os mesmos 32 casos conhecidos e as referências
locais congeladas, não uma revisão humana independente. “Conjunto” exige
papel alinhado, vínculo literal válido e pista local no trecho selecionado;
não comprova a relação semântica nem autoriza efeito.

| Medida | Predicado (base) | Trecho externo | Predicado + prioridade | Trecho externo + prioridade |
| --- | ---: | ---: | ---: | ---: |
| Papel alinhado /32 | 24 | 23 | 19 | 18 |
| Vínculo estrutural /32 | 15 | 13 | 20 | 16 |
| Pista local no trecho /32 | 13 | 11 | 17 | 13 |
| Conjunto /32 | 12 | 9 | 10 | 6 |
| Reprodução textual do foco /32 (menor é preferível) | 16 | 19 | 11 | 16 |
| Indeterminação alinhada /4 | 0 | 0 | 1 | 1 |
| Falso indeterminado /28 conclusivos | 0 | 0 | 0 | 0 |
| Pares com ambos os papéis alinhados /12 | 10 | 8 | 4 | 3 |

Evidência e hipóteses:

- Renomear a unidade não reduziu cópia do foco nesta coleta: 16→19 sem
  prioridade e 11→16 com prioridade; o conjunto caiu 12→9 e 10→6.
  O resultado contraria o benefício esperado da troca de vocabulário/campo,
  sem provar uma causa interna do modelo ou equivalência estatística geral.
- Priorizar indeterminação melhorou geometria, mas piorou o papel: 24→19
  com `predicado` e 23→18 com `trecho_externo`. No primeiro contraste há
  dois ganhos de papel (N01/U04) e sete perdas (H02B/H03A/H07A/H08B/H11A/
  H03B/H06A). No segundo, um ganho (U04) e seis perdas (H02B/H03A/H07A/
  H08B/H03B/H12A). A maioria das novas perdas recebeu
  `expressao_sem_operacao`, não `indeterminado`. Não houve excesso de
  abstenções como explicação dessas perdas; zero falso indeterminado não
  significa segurança semântica.
- U02 selecionou literalmente “não sei se é etiqueta de vaso ou uma orientação
  citada.” nos quatro braços, mas todos propuseram `expressao_sem_operacao`.
  Ausência de pista selecionada não explica esse erro; o host não modificou
  o papel. U04 passou de operação para indeterminação apenas com a prioridade,
  ainda insuficiente para compensar as perdas dos controles conclusivos.
- Requisições das 32 consultas da base são idênticas às do braço
  `predicado_host` anterior. Mesmo assim, N01 mudou de expressão para nome
  (papel 25→24); N01/H05B/H10A tiveram propostas diferentes. Essa variação
  impede atribuir toda diferença pequena ao fator experimental. Uma execução
  por caso/braço, em painel já conhecido, não estima estabilidade nem
  generalização. Opções explícitas continuam com temperatura zero.

Decisão: não promover nenhum dos dois fatores. Preservar materializador e
guardas; não compensar papel errado com palavras-chave, referência local ou
fallback. A primeira fronteira semântica continua sendo a leitura da função
do foco no contexto, inclusive quando o trecho correto já foi selecionado.
Geometria e interpretação permanecem medidas separadas, sem declarar raiz
interna única ou incapacidade geral do Qwen.

Próxima investigação proposta: sair das trocas de vocabulário e testar ensino
por exemplos contrastivos, com nomes, operações mencionadas, expressões e
fontes realmente inconclusivas em contextos vizinhos. Exemplos de demonstração
devem ser distintos de um novo painel de avaliação congelado antes de consultas;
não reutilizar estes 32 casos como holdout. Comparar também preservação dos
positivos e repetibilidade, além da abstenção. Preparar protocolo e critérios
antes da próxima coleta; não treinar pesos, integrar ao runtime ou promover
saídas em memória/autoridade nesta etapa. Nenhuma nova coleta dessa proposta
foi iniciada aqui.

Validação do instrumento: 19 testes novos; regressão relevante de 1.443 testes
passou após o ajuste pré-coleta da ordem das propriedades. Contagens de suítes
se sobrepõem, não devem ser somadas. GREEN local verifica o instrumento e os
contratos, não a semântica do modelo. Produção, treino, guardas e artefatos
anteriores não foram alterados por este experimento. Nenhum commit criado.

### P01: predicado proposto e intervalo materializado pelo host (07/10)

Protocolo pré-consulta. A primeira falha estrutural do braço anterior foi
recopiar enunciados com aspas alteradas (23/32). Fonte canônica e ancorador
estavam preservados. Novo experimento remove essa recópia: o modelo propõe
`predicado` e `papel`; o host já conhece o foco, ancora o predicado na fonte
integral e materializa o intervalo mínimo que contém ambos. Esse intervalo
é geometria literal, não uma proposição semanticamente descoberta pelo host.

Diferença para as sondas de IDs: não pedir uma lista de blocos externos ou
índices livres. O proponente aponta um predicado literal, geralmente curto;
não enumera todos os contextos. Nenhum inventário manual ou recorte correto é
fornecido. A mudança reduz recópia do enunciado, mas mantém uma seleção
semântica pendente. Não garante impedir seleção vazia ou predicado irrelevante.

- HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`, worktree preservada.
  Nova sonda `scripts/analises/sonda_predicado_host_v1.py`, SHA256
  `cabbfe97fa3c2f2e1711dda5cdce3f0c2343ba08475c953bde6e2f20257aa01c`.
  Baseline `sonda_vinculo_enunciado_v1.py` congelado em
  `5020f5bb72a45528025bb85e5f1a7c5a796133a294d2be5b144b02a6628fa570`.
- Reusa catálogo, contrato de proposições e guarda de vínculo existentes.
  Primeiro ancora apenas predicado na fonte integral, com objeto indeterminado;
  depois fatia por offsets verificados e confere foco, unicidade, contenção e
  sobreposição na guarda anterior. Grafia não é reescrita ou normalizada.
  Predicado deve ser único na fonte inteira: mais restritivo que unicidade
  apenas no enunciado do braço anterior. Não escolher o predicado mais próximo.
- Um intervalo contendo duas cópias do foco continua recusado. Predicado vazio
  conserva revisão pendente; papel errado continua errado mesmo com pista
  correta. Predicado de outra oração pode passar geometricamente: cobrir essa
  limitação com teste e conservar todas as flags semânticas/operacionais falsas.
- Comparação de interface composta, com prompt/schema/materialização distintos.
  Não isola causa interna do modelo. Baseline anterior recebe requisição exata;
  fonte/foco/aspas/opções iguais nos dois braços. 32 casos conhecidos, mesmas
  referências locais e pistas congeladas; nenhum novo holdout ou revisão humana.
- 64 consultas independentes, 16 AB/16 BA, sem retentativa ou ajuste após
  resultados. Metadata antes das chamadas; saída exclusiva
  `resultados_testes/sonda_predicado_host_v1_ab.jsonl`.
- Métricas comuns: shape, rótulo projetado, vínculo estrutural, pista lexical
  **no predicado** e conjunto dessas últimas três. Cobertura ampla do intervalo
  não vale como pista do predicado. Mesmo conjunto alinhado não prova semântica.
  Erros/truncamentos/vazios permanecem no denominador de 32. Recontar HTTP bruto.
- 26 testes novos / 96 focados verdes sobrepostos antes da coleta. Controle
  reproduz a falha anterior de aspas e mostra materialização original quando
  apenas predicado é proposto; não modifica guarda antiga nem escores históricos.

Coleta pendente neste registro. Escopo: diagnóstico offline e testes; nenhuma
mudança em produção, treino, memória ou executor. Mesma P01 aberta; sem commit.

#### Resultado do predicado e materialização host (07/10)

64/64 consultas HTTP200, JSON/shape válido, `done=True`/`stop`, sem reparo ou
retentativa. Recontagem a partir do HTTP bruto confirmou rótulos, métricas,
requisições, host, referências, ordem AB/BA, hashes e flags. Painel conhecido;
resultados são diagnósticos locais, não estimativa de generalização.

| Métrica comum | Copiar enunciado | Predicado + host |
|---|---:|---:|
| Rótulos alinhados concluídos | 24/32 | 25/32 |
| Pares de rótulos completos | 8/12 | 10/12 |
| Vínculos estruturais válidos | 8/32 | 16/32 |
| Pista lexical no predicado | 5/32 | 14/32 |
| Rótulo + vínculo + pista no predicado | 4/32 | 12/32 |
| Pares completos desse conjunto | 0/12 | 4/12 |
| Indeterminação alinhada | 1/4 | 0/4 |

O conjunto usa pista no **predicado** nos dois braços. Não comparar o 4/32
com o 5/32 composto anterior, que contava pista no enunciado inteiro. Nomes
9/12 → 11/12; operações 10/12 → 11/12; estados 4/4 → 3/4. Três ganhos de
rótulo H05A/H07A/H08B, duas perdas N03/U04, 22 ambos alinhados e cinco ambos
errados. Vínculo: 12 ganhos e quatro perdas. Conjunto: nove ganhos e uma perda.
As perdas permanecem registradas; melhorar geometria não resolveu a semântica.

O baseline congelado repetido obteve 24/32; sua coleta histórica tinha 23/32.
H11A mudou de `expressao_sem_operacao` para `nome_designacao` sob requisição
idêntica. Usar a comparação contemporânea 24 → 25. Temperature=0 e digest
igual não autorizam atribuir oscilações históricas ao novo candidato.

Primeiras recusas no candidato: nove predicados sem âncora literal única,
sete sobrepondo o foco, 16 intervalos ancorados. Inspeção do bruto dos nove:
oito contêm troca de aspas; H03B produz `debate a hipótese`, paráfrase de
`Estamos debatendo a hipótese`. Nenhum foi reparado na aferição. Contrafactual
de leitura restaurando só as aspas nos oito revela sete sobreposições e um
objeto ambíguo (H11A); **nenhum** desses oito ganha vínculo válido. Portanto,
a troca de aspas já não explica por si a barreira restante dessa interface.

Há 15 casos demonstráveis de seleção que inclui o foco ou a outra ocorrência
(sete recusados diretamente, oito visíveis após diagnóstico de grafia).
O proponente frequentemente coloca a oração completa no campo `predicado`,
apesar do pedido de trecho externo. Isso sustenta investigar a especificação
da unidade pedida; ainda não prova causa interna do Qwen ou efeito causal
do nome do campo. O host não corta o foco desse texto para fabricar acerto.

Controles que impedem uma conclusão forte:

- H10A ancora `preserve seu conteúdo`, mas esse predicado é de outra ação;
  rótulo permanece errado. Geometria não certifica relação contextual.
- U02 ancora `não sei se é etiqueta de vaso ou uma orientação citada`, com
  pista de incerteza explícita, mas classifica `expressao_sem_operacao`.
  A falha de abstenção persiste mesmo com a pista selecionada corretamente.
- U04 perde a abstenção do baseline. Não transferir exemplos para treino,
  substituir o classificador ou promover a interface com base no ganho literal.

Artefato `resultados_testes/sonda_predicado_host_v1_ab.jsonl`, 66 linhas,
SHA256 `346dfbab055ca7dabe60a5de97b1424333cd3f41e30ac213b5dbc4f4d0d56d49`.
Script mantém hash pré-consulta. Digest nas leituras início/fim/auditoria:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
**26 novos / 96 focados / 1.424 relevantes verdes, sobrepostos**. Prova
estrutural offline e geração local com Qwen; não execução da Laylay real.

Decisão: materialização literal pelo host mostrou utilidade neste diagnóstico,
com fonte e ocorrência intactas, mas o candidato completo segue sem promoção.
Próxima fronteira: especificar e testar a escolha de **pista contextual externa**,
incluindo as recusas observadas de foco dentro do trecho. Investigar se pedir
`predicado` favorece oração completa como hipótese de interface; não simplesmente
trocar o nome e declarar raiz. A abstenção precisa de critério próprio de
aceitação, pois já falha com evidência de incerteza selecionada. Preservar
as referências atuais e exigir validação em fontes novas antes de generalizar.

Escopo final: nova sonda, testes e os três documentos P01. Nenhuma alteração
de produção/treino/memória/executor por este trabalho, nenhum commit. Guardas,
painéis e artefatos históricos preservados. P01 permanece aberta.

### P01: proposta de vínculo enunciado–ocorrência (07/10)

Protocolo congelado antes de consultar o Qwen; mesma raiz P01, somente offline.
Produção, treino, catálogo de capacidades e composição da Laylay não alterados.
O experimento anterior falsificou recorte de contexto como solução geral,
não diagnosticou a causa interna da rede. Este candidato testa uma interface
composta mais explícita, não declara uma correção da interpretação.

- Baseline HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch `main`;
  worktree concorrente preservada. Sonda nova
  `scripts/analises/sonda_vinculo_enunciado_v1.py`, SHA256
  `5020f5bb72a45528025bb85e5f1a7c5a796133a294d2be5b144b02a6628fa570`.
  Reutiliza transferência `05ddfa7d4be55e47c6f4942df196d2e5a2e775e78ada2e588b4ab457428689b2`
  e contrato de proposições `e286c3032fa7ee2c02f14112b353b949d167a96bec1699ee3958503dc01dfb99`;
  mantém hashes transitivos, dados e artefatos anteriores intactos.
- 32 casos **já conhecidos** do painel de transferência; não novo holdout.
  Mesmos rótulos locais congelados: 12 nomes, 12 operações mencionadas,
  quatro estados, quatro fontes explicitamente inconclusivas. Revisão local
  do agente, não humana independente nem estimativa populacional.
- Baseline `leitura_direta` exato. Novo braço retorna três strings:
  `enunciado`, `predicado`, `papel`. Fonte integral/foco/aspas/opções iguais;
  muda prompt **e** schema: comparação de interface composta, não efeito
  isolado de uma instrução. Zero recorte-oráculo, pistas locais, gabaritos,
  IDs históricos de caso ou exemplos fornecidos ao modelo.
- Host autentica entrada e pedido; usa contrato existente para ancorar
  predicado/objeto dentro do enunciado. Objeto é o foco canônico já conhecido
  pelo host, não uma entidade adivinhada pelo modelo. Tipo/polaridade/papel
  do objeto permanecem placeholders indeterminados, não inferências.
  Fonte e offsets do objeto devem coincidir com a ocorrência marcada;
  texto igual em outra ocorrência ou envelope com duas cópias não basta.
  Predicado deve ser externo, sem sobreposição parcial ou total ao foco.
  Guarda canônica aceita diferença de capitalização e recupera grafia da
  fonte; isso não equivale a exigir cópia byte a byte.
- Shape/HTTP/finalização, rótulo local, vínculo estrutural e cobertura lexical
  são métricas separadas. Pistas locais pré-congeladas em `PISTAS_LOCAIS`
  são apenas alternativas literais fora do foco; cobertura no enunciado e
  no predicado contadas separadamente. Enunciado amplo com palavra correta
  e predicado da outra oração pode passar estruturalmente: teste explicita
  esse limite. Até alinhamento composto local não certifica relação semântica.
  Vínculo não se aplica ao baseline que só produz rótulo: usar `null`, não zero.
- Vazio conserva revisão pendente, nunca ausência ou papel inventado.
  Campos extras invalidam a proposta composta; projeção bruta do rótulo é
  apenas métrica separada. Truncamento/erro permanecem no denominador de 32,
  sem crédito concluído. Todas as flags de semântica/autoridade/efeito falsas.
- 64 consultas independentes; 16 AB/16 BA, sem retentativa ou ajuste após
  saída observada. Metadata e referências gravadas antes da primeira chamada.
  Artefato exclusivo `resultados_testes/sonda_vinculo_enunciado_v1_ab.jsonl`.
  Recontagem deve usar HTTP bruto e autenticar registros, não escores salvos.
- **26 novos / 108 focados verdes (sobrepostos)** antes da coleta. Um RED
  de integração da própria sonda identificou confusão entre envelope host
  com tokens e porta canônica de três campos; corrigida a chamada após
  autenticação integral, sem enfraquecer testes nem alterar guardas existentes.
  Não é diagnóstico de bug histórico do modelo ou da produção.
- Revisão pré-consulta encontrou assimetria na métrica de rótulo para chave
  extra: referência exigia shape, candidato projetava apenas rótulo. Corrigida
  antes de qualquer consulta e protegida por controle simétrico nos dois
  braços. Agora papel projetado e shape são métricas separadas nos dois.
  Hash acima é o congelamento final pré-consulta, não ajuste após inferência.

Contrato geral investigado: ocorrência literal → enunciado enquadrador
proposto → papel/indeterminação, sempre separando geometria, interpretação,
autorização e efeito. Coleta e decisão semântica pendentes neste registro;
P01 permanece aberta. Nenhum commit, treino ou promoção para runtime.

#### Resultado e decisão do vínculo explícito (07/10)

Coleta fechada, sem retentativa, reparo ou ajuste da sonda. 64/64 HTTP200,
JSON/shape válido, `done=True`/`stop`; nenhum truncamento. Recontagem integral
do HTTP bruto confirmou todas as aferições, ordem, referências, entradas,
requisições e flags. Segunda revisão independente também contou pelo bruto.

| Métrica local | Leitura direta | Vínculo enunciado |
|---|---:|---:|
| Rótulos alinhados concluídos | 22/32 | 23/32 |
| Pares contextuais completos | 7/12 | 7/12 |
| Nomes | 7/12 | 8/12 |
| Operações mencionadas | 11/12 | 10/12 |
| Estados | 4/4 | 4/4 |
| Indeterminação explícita | 0/4 | 1/4 |
| Vínculo estrutural | não aplicável | 8/32 |
| Pista local externa no enunciado | não aplicável | 8/32 |
| Pista local no predicado | não aplicável | 5/32 |
| Rótulo + vínculo + pista no enunciado | não aplicável | 5/32 |

Três ganhos de rótulo (H02A/H06A/U04), duas perdas (H07A/H08B), 20 ambos
alinhados e sete ambos desalinhados. Ganho líquido de um neste painel conhecido,
sem ganho de pares. **Não é melhora suficiente para promover a interface.**
Os três ganhos nem produziram vínculo estrutural válido; não contar o rótulo
isolado como sucesso da proposta completa. U04 se abstém no papel, mas deixa
predicado vazio: revisão pendente, não evidência de vínculo ou ausência.

Primeira fronteira estrutural RED: 23/32 enunciados sem âncora. Comparação
literal verificou nos 23 que a única diferença do enunciado proposto para um
trecho único da fonte é trocar as aspas tipográficas `“/”` por ASCII `"`.
Fonte/pedido preservaram a grafia; a resposta capturada já contém a troca.
Isso demonstra a primeira divergência de cópia neste braço, não defeito da
guarda canônica nem a causa interna do modelo. Oito enunciados ancoram, portanto
não há falha global de transporte, JSON ou serviço que explique todas as recusas.

Contrafactual de leitura **apenas diagnóstico**, sem alterar artefato, escores,
guarda, fonte fornecida ou saída do modelo: recuperar a grafia única da fonte
e do predicado nos 23 faz 21 chegarem à revisão estrutural. Dois REDs posteriores
permanecem: H11A copiou envelope com ambas as ocorrências e objeto segue ambíguo;
H10A incluiu foco no predicado e segue sobreposto. **21 não é novo escore de
sucesso do candidato**: o contrato congelado rejeitou os 23, corretamente.
Falsificada a explicação de que somente restaurar aspas corrigiria o fluxo.

Interpretação é outra fronteira, não resolvida por copiar melhor:

- H07A copia `é o título do gráfico` no predicado e ancora corretamente,
  mas propõe `expressao_sem_operacao` em vez de nome. Logo nem ausência da
  pista na saída nem falha de cópia explica todos os erros de papel.
- H04A ancora `começa amanhã`, que descreve horário, não designação. Vínculo
  geométrico e pista `denominada` no enunciado não certificam o enquadramento.
  A métrica composta local alinha nesse caso e sua limitação permanece exposta.
- U01 ancora `foi copiado`, mas ignora a alternativa em aberto; U02/U03
  também não se abstêm. 1/4 de abstenção não resolve a família de indeterminação.

Artefato exclusivo `resultados_testes/sonda_vinculo_enunciado_v1_ab.jsonl`,
66 linhas, SHA256
`3b7e5c27f8e7f249575bf1a6f2f0cbbaeb86affefb9171979191cb571d030eaf`.
Script/dependências/painel mantiveram hashes pré-consulta e artefatos anteriores
foram conferidos intactos. Digest igual nas leituras início/fim/auditoria:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Isso não certifica invariância contínua nem determinismo do modelo.

Após coleta, acrescentado um controle da troca de aspas, mantendo a recusa
canônica e o controle de fonte exata; nenhum prompt/guard/script da sonda
alterado após inferência. **27 novos / 1.398 relevantes verdes (sobrepostos)**.
Esse verde comprova contratos locais/offline, não semântica ou runtime Laylay.

Decisão: preservar o experimento como evidência, sem promover, treinar ou
enfraquecer ancoragem. Próxima investigação deve separar seleção semântica de
reprodução textual: materialização literal tem de continuar pertencendo ao
host, com identidade/offsets/proveniência intactos. Não repetir simplesmente
“trocar cópia por IDs”: sondas anteriores já mostraram seleção vazia ou tudo
selecionado. Antes de novo candidato, explicar qual contrato novo evitaria
esse comportamento e provar controles de ocorrência e de indeterminação.
Corrigir cópia não basta para corrigir papel; duas fronteiras evidenciadas,
não uma root neural interna proclamada.

Escopo desta investigação: nova sonda e seus testes; notas nos mesmos três
documentos P01. Contrato/catálogo/captura antigos, produção, fontes/dados,
memória, treino e executor não alterados por este trabalho; worktree paralela
preservada, nenhum commit. P01 aberta, rede não liberada por este diagnóstico.

### P01: ablação contextual e controles de abstenção (07/10)

Investigação da próxima fronteira, sem patch de produção. O catálogo literal
seleciona ocorrência por ID/offset, não por primeira string igual. A guarda
`conferir_papel` autentica fonte/foco e shape, retorna revisão pendente e
não pretende provar interpretação semântica. Portanto rótulo errado mas
bem formado não é bug de validação literal; transformar essa guarda em
classificador de frases seria trocar responsabilidades e esconder o RED.
`InventarioContextual` enumera referentes com proveniência, não predicações
de um texto livre; não reutilizá-lo como certificador de papel. O contrato
de vínculo didático também compara anotações propostas, não as certifica.

Protocolo congelado antes da consulta:

- HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`, worktree preservada.
- `scripts/analises/sonda_ablacao_contexto_papel_v1.py`, SHA256
  `426f33a27ac7b951f80eb425b7b06b1539bb21e957d744b423bd018d71890443`.
  Reutiliza medição, validação, schema, prompts e base da transferência
  congelada `05ddfa7d4be55e47c6f4942df196d2e5a2e775e78ada2e588b4ab457428689b2`;
  não altera dados, sondas ou respostas anteriores.
- Dez casos conhecidos: H05A/H10A/H11A/H11B, H02A/H06A, U01/U02/U03/U04.
  Mesmas referências locais anteriores, não holdout novo. Quatro intervenções
  manuais: copiar apenas trechos literais que mantêm a predicação do foco
  nos quatro primeiros. Seis controles repetem **exatamente** o mesmo input;
  quatro deles são indeterminação explícita. Zero regra de classificação.
- Projeção de ocorrência por offsets antigos menos início do recorte, com
  catálogo/árvore de aspas existentes. H11B recorta a segunda ocorrência:
  novo c1 continua apontando para o c2 original, não para a primeira cópia.
  Retirada de contexto foi escolhida manualmente: uma ablação-oráculo
  diagnóstica, nunca seletor automático ou candidato para produção.
- 40 consultas independentes (10 casos × duas variantes × dois prompts),
  sem retentativa ou ajuste; cinco integral-primeiro, cinco recorte-primeiro.
  Prompts/opções/schema intactos; nenhuma referência, mapa, ID de caso ou
  justificativa fornecidos ao modelo. Só fonte/foco/aspas reais da variante.
- Recorte remove contexto mas também muda comprimento/sintaxe/offsets/aspas.
  Ganho não isolaria mecanismo interno de interferência; controles idênticos
  ajudam a observar instabilidade, não garantem determinismo em temperature=0.
- Fonte original, recortes manuais, referências e hashes na metadata antes
  das chamadas. Saída exclusiva
  `resultados_testes/sonda_ablacao_contexto_papel_v1.jsonl`.
  **15 novos / 36 focados verdes (sobrepostos)**; coleta pendente neste registro.

Hipóteses separadas: contexto concorrente pode contribuir em certos erros;
falha de abstenção pode persistir sem concorrência. Não declarar uma root
interna comum nem adicionar fallback com gabarito. P01 segue aberta,
literalidade/proposta/autoridade/efeito separados, sem treino ou commit.

#### Resultado e decisão da ablação (07/10)

40/40 HTTP200/JSON/shape válido/done=True/stop, sem truncamento; recontagem
independente do bruto confirmou escores, ordem, projeções e gabarito.
Script/transferência/painel mantiveram os hashes pré-consulta. Comparação
nos quatro casos intervenientes, não no conjunto de 32 como se fosse novo:

| Prompt congelado | Integral (4 casos) | Recorte manual (4 casos) | Ganhos / perdas |
|---|---:|---:|---:|
| Atual | 2/4 | 1/4 | 1 / 2 |
| Direto | 1/4 | 3/4 | 2 / 0 |

No denominador completo deste diagnóstico dirigido, 2/10 → 1/10 no atual e
1/10 → 3/10 no direto. **Não são escores de população geral**: casos foram
selecionados por riscos/erros já conhecidos. H05A alinha após recorte nos
dois prompts; H10A continua errado nos dois. H11A alinha com recorte no
direto, mas erra com recorte no atual; H11B sofre perda no atual. Recortar
o contexto, portanto, não é uma solução geral e nem garante preservar acerto.

Os seis controles por prompt tiveram requisições exatamente iguais entre
variantes e rótulos estáveis nesta coleta: 12 comparações controladas, sem
alegar determinismo contínuo. H02A/H06A continuam nome → operação mesmo
sem outro comando externo ou outra ocorrência concorrente. U01–U04
continuam sem abstenção (0/4 em ambos os prompts, nas duas variantes).
Isso falsifica a explicação **exclusiva** de que todos esses REDs dependem
de outro comando ou de segunda ocorrência na fonte. Não falsifica eventual
contribuição de contexto nem demonstra a causa interna da falta de abstenção.

Artefato `resultados_testes/sonda_ablacao_contexto_papel_v1.jsonl`, 42 linhas,
SHA256 `025891330c3cc43350be4ba04336d8396d5bfad6e025374af68691866c7cbb1c`.
Digest igual nas leituras de início/fim/auditoria:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Primeira RED continua na interpretação proposta; não há evidência de erro
de identidade literal, fonte, transporte, shape ou recontagem nestas consultas.

Após a coleta, três testes adicionais exercitaram o componente real existente
`contrato_proposicoes_mencionadas`: duas proposições da mesma fonte com
objetos textualmente iguais receberam offsets distintos; predicado emprestado
da outra proposição causou recusa atômica, sem publicação parcial; alterar
anotação semântica não ganhou autoridade ou verdade por contenção.
**18 testes novos / 82 focados / 1.371 relevantes verdes (sobrepostos)**.
`git diff --check` sem erro. Esses testes provam
integração estrutural local, não produção do vínculo correto pelo Qwen.
Produção, treino, prompts anteriores e artefatos históricos não alterados;
nenhum commit. P01 não encerrada nem rede liberada.

Direção arquitetural para a próxima investigação, ainda não implementada:

1. Reusar catálogo/árvore de aspas para identidade da ocorrência e o contrato
   existente de proposições para ancorar predicado/objeto no seu enunciado.
   Não criar outro tokenizer, parser privado de títulos ou inventário de
   referentes usado como verificador de texto.
2. O proponente deve indicar **qual proposição** enquadra **qual ocorrência**,
   antes de reduzir a leitura a um rótulo. Conferir fonte, IDs, contenção e
   igualdade de offsets do objeto com o foco; string igual não basta. Um
   vínculo estrutural válido continua hipótese, não prova semântica.
3. Conservar alternativa não decidida quando a fonte não fornece papel
   conclusivo. Não usar silêncio, evidência vazia ou voto de modelo como
   prova de ausência, certeza ou autorização. Falha de abstenção permanece
   hipótese separada até que a mesma mudança explique os respectivos REDs.
4. Medir a proposta completa contra referências pré-congeladas e controles
   (enunciados concorrentes, repetição, negação, citações e fonte inconclusiva).
   Comparar ao caminho atual sem recortes-oráculo na entrada e sem promover
   validação estrutural a acerto semântico. Não iniciar treino nem runtime
   antes dessa prova. Não tratar o recorte manual como seletor implementado.

O contrato reutilizável é **ocorrência → enunciado enquadrador proposto →
papel/indeterminação**, mantendo evidência, decisão e efeito separados. É
aplicável a comandos, citações, memória e ensino sem alterar esses domínios
juntos ou prometer que essa estrutura, sozinha, fará o modelo acertar.

### P01: transferência contextual — protocolo pré-consulta (07/10)

Continuação do candidato de instrução, não nova root. Pergunta: o ganho
11/20 → 16/20 no painel conhecido persiste em fontes/focos novos, mantendo
os dois prompts congelados? Nenhuma produção ou treinamento alterados.
Base `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`, worktree preservada.

Congelamento antes de qualquer chamada do painel novo:

- Painel `scripts/analises/dados/sonda_papel_transferencia_v1.json`, SHA256
  `e93ae74cd152f93a75fdb52b226404ab7659288203188c509ef174ce0cbb8ee2`.
  32 casos: 12 pares nome/operação, quatro estados, quatro indeterminados.
  Novos textos e focos em relação ao replay anterior; distribuição 12/12/4/4.
  Inclui negação, hipótese, citações aninhadas, operações externas ao foco,
  instruções sem autorização, predicação posterior e texto repetido com
  duas ocorrências de papéis distintos. Domínios variados, sem efeito real.
- Revisão local com justificativa por caso, escrita antes de consultar.
  Não é revisão humana independente, corpus externo ou amostra aleatória:
  painel foi desenhado após observar o replay e seus riscos. Pode medir
  transferência local limitada, não generalização universal ou superioridade
  da rede. Após consulta deixa de ser teste não visto; não retreinar nele.
- `scripts/analises/sonda_papel_transferencia_v1.py`, SHA256
  `05ddfa7d4be55e47c6f4942df196d2e5a2e775e78ada2e588b4ab457428689b2`.
  Reutiliza **sem alteração** preparar requisição, medir, aferir, fonte/foco,
  captura HTTP, decoder e guarda de papel do contraste anterior congelado
  `05e6a2c74001bd70a113e00b23837631bd7f8a33876357e7e7d189a6349cda59`.
  Novo resumo exige denominador completo e gabarito/painel autênticos.
- Ambos os prompts, categorias, schema, modelo `qwen3:4b-instruct`, opções
  temperature=0/num_predict=700 intactos; só sistema difere entre braços.
  Fonte/foco/aspas são os únicos dados de usuário fornecidos; nenhuma
  justificativa, gabarito, ID de caso, exemplos de calibração ou âncora.
- 64 consultas independentes, 16 AB/16 BA, sem retentativas/adaptação.
  Referências copiadas antes das chamadas, respostas brutas preservadas,
  escores recalculados, pares exigem os dois lados. Indeterminação não vira
  autorização, ausência, referente ou confirmação de efeito.
- Saída exclusiva `resultados_testes/sonda_papel_transferencia_v1_ab.jsonl`.
  21 testes novos / 67 com o contraste anterior verdes (sobrepostos), sem
  consulta Qwen nestes testes. Coleta ainda pendente neste checkpoint.

Não trocar instrução/gabarito após observar respostas. Resultado nulo ou
negativo será preservado e impedirá alegação de ganho generalizado; ganho
exigirá tratar os erros remanescentes antes de qualquer promoção ao runtime.

#### Resultado da transferência, auditado sem retocar prompts (07/10)

64/64 HTTP200, JSON, shape válido e done=True/stop; todos os casos mantidos
no denominador. Recontagem do conteúdo HTTP bruto confirmou o resumo;
requisições, gabarito pré-consulta, host, focos por offset, flags, ordem e
hashes revalidados, sem confiar em escores armazenados.

| Medida | Prompt atual | Leitura direta |
|---|---:|---:|
| Papéis alinhados / casos novos | 20/32 | 22/32 |
| Pares com ambos os lados alinhados | 6/12 | 7/12 |
| Nomes | 6/12 | 7/12 |
| Operações mencionadas | 11/12 | 11/12 |
| Expressões/estados | 3/4 | 4/4 |
| Indeterminação explícita | 0/4 | 0/4 |

Quatro ganhos (H02B, H03A, H07A, N03), **duas perdas** (H11A, H05B), 18
acertos comuns e oito erros comuns. U02 muda de operação para expressão e
permanece errado. As contagens de ganhos/perdas não podem ser substituídas
pelo ganho líquido de dois casos; o contraste anterior sem perdas não se
reproduziu neste painel. Não declarar ganho robusto a partir de uma coleta.

Dez erros na leitura direta, agrupados como evidências de P01, não dez roots:

- Cinco nomes classificados como operação: H02A/H05A/H06A/H10A/H11A.
  H05A/H10A contêm comando externo ao foco; H11A contém duas ocorrências
  textualmente iguais com funções diferentes. É hipótese que haja competição
  entre contextos, não uma causa interna demonstrada do modelo.
- Uma operação exemplificada classificada como nome: H05B. A fonte diz
  exemplo de instrução; é uma perda em relação ao controle, não veto do host.
- Quatro fontes explicitamente inconclusivas classificadas sem abstenção:
  U01/U02/U03/U04. Nem presença de negação nem formato de ordem permitem
  ignorar a indeterminação declarada na fonte.

Primeira RED: fonte/foco íntegros → rótulo proposto no HTTP bruto. Falsificados
para esses resultados: foco errado por offset, corrupção de transporte/JSON/
shape e erro de contabilização. Digest igual nas leituras não sustenta troca
de modelo, mas tampouco prova invariância durante todas as chamadas. A fonte
e a revisão local sustentam a função esperada, mas não há revisão humana
independente; manter esse limite. O host já conserva separadas literalidade,
proposta, autorização e efeito. Não fazê-lo converter rótulo válido em
suporte verificado para compensar os erros semânticos do modelo.

Artefato exclusivo de 66 linhas (metadata + 64 consultas + resumo):
`resultados_testes/sonda_papel_transferencia_v1_ab.jsonl`, SHA256
`2e2c9aa636d79afe2154abfde59ea24be29d454bbaed55d6e6627d0465642075`.
Script/painel/prompts conservaram os hashes pré-consulta. Digest igual nas
leituras de início/fim/auditoria:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`;
isso não prova invariância contínua ou determinismo. Tempos somados de
consulta 32,9990s / 31,3635s, sem alegação de eficiência.

**21 testes novos, 67 focados e 1.353 relevantes verdes (sobrepostos)**.
Somente painel, sonda, teste e três documentos P01 adicionados/atualizados
nesta continuação. Não alterei produção, treino ou prompts anteriores;
nenhum commit. Este GREEN é de infraestrutura/regressão, não semântico,
runtime real da Laylay, efeito externo ou liberação da rede.

Decisão: **não promover o prompt direto como substituto**. A melhora local
existe, mas é pequena, inclui regressões e não resolve indeterminação.
Próxima fronteira: investigar o contrato de vínculo entre predicação da
fonte e **ocorrência específica** do foco, incluindo fonte inconclusiva;
usar o inventário/guardas existentes, não listas de frases ou fallback de
rótulo. Separar as hipóteses de competição contextual e falha de abstenção
antes de consolidá-las como mesma causa ou propor candidato. Painel agora
é conhecido: não reutilizá-lo como holdout novo ou dado de treino.

### P01: leitura direta do papel — protocolo congelado (07/10)

Hipótese, não raiz interna provada: explicitar que a decisão depende de como
a fonte apresenta o foco pode reduzir competição com a aparência de ordem
do conteúdo citado. Primeiro RED disponível: rótulos incorretos já presentes
no bruto de 40 respostas anteriores válidas/concluídas; contexto externo
explícito não trouxe ganho líquido (11/20 e 3/8 pares em ambos os braços).
Isso falsifica erro do parser e falta de delimitação como explicações desses
rótulos, não prova qual mecanismo interno do Qwen os produziu.

Antes da primeira consulta, congelados:

- HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`, worktree suja
  preservada; estado completo será capturado na metadata.
- `scripts/analises/sonda_papel_leitura_direta_v1.py`, SHA256
  `05e6a2c74001bd70a113e00b23837631bd7f8a33876357e7e7d189a6349cda59`;
  depende do anterior `e702fcb8876f54c1354f8e8dcc0ce8305cf5ddc64a3bcbafce8170be85ee56fe`
  e reutiliza captura HTTP, decoder, fonte/foco, validação tipada e guarda
  canônica de papel. Não rebatiza registros para o auditor antigo.
- Painel/revisão existentes intactos, SHA256
  `fe94a2a77ac28b2b870004f16f9ca21f4bebf4469955b6f17b4cd10f29dfc682` /
  `04d53c818d217f910dfd2eb766e3800865544c9a3fd7b64ccd98318743c5d6a0`.
- 20 casos, 8 pares; 8 nomes, 8 operações, 2 estados, 2 indeterminados.
  Referências locais copiadas na metadata antes de consultar, nunca no prompt.
- Dois braços independentes `prompt_atual` / `leitura_direta`; somente o
  sistema muda. Fonte, foco, aspas, quatro categorias, schema, modelo,
  temperature=0 e num_predict=700 iguais. Sem exemplos, gatilhos de frases,
  IDs dos casos ou âncoras na instrução; sem contexto externo adicional.
- 40 consultas, 10 AB/10 BA, sem retentativas adaptativas; HTTP bruto e
  finalização preservados. Resumo exige todo o denominador, revalida o bruto,
  separa shape/conclusão/alinhamento, ganhos/perdas e ambos os lados dos pares.
- Arquivo exclusivo `resultados_testes/sonda_papel_leitura_direta_v1_ab_replay.jsonl`.
  Protocolo validado por **46 testes**; coleta ainda não executada neste registro.

Limites: painel já conhecido, não holdout; não mede runtime da Laylay nem
superioridade da rede. Papel alinhado não verifica suporte, referente,
vigência ou autoridade. Nenhuma produção/treino alterados, nenhum commit.
Ganho neste painel exigirá avaliação independente antes de promoção; empate
ou regressão não justificam incorporar o prompt à produção.

#### Resultado auditado após o congelamento (07/10)

Coleta completa, sem mudar script/protocolo/gabarito: 40 HTTP200, JSON,
shape de papel válido e done=True/stop; zero erros de transporte ou cortes.
Replay autenticou requisições contra os dois prompts reais, host, flags,
ordem, referências e hashes; recontagem direta dos rótulos no bruto confirmou
os escores sem confiar na aferição salva.

| Medida local | Prompt atual | Leitura direta |
|---|---:|---:|
| Papéis alinhados / todos os casos | 11/20 | 16/20 |
| Pares com ambos os lados alinhados | 3/8 | 6/8 |
| Nomes | 4/8 | 6/8 |
| Operações mencionadas | 5/8 | 7/8 |
| Expressões/estados sem operação | 2/2 | 2/2 |
| Indeterminação explícita | 0/2 | 1/2 |

Cinco ganhos Q01B, Q03A, Q03B, Q05A e Q08A; nenhuma perda, 11 acertos comuns
e quatro erros comuns. Q08B muda de expressão para operação e continua
errado: alteração de rótulo não é melhora. Restantes na leitura direta:

- Q02A: nome de documento classificado como operação.
- Q06A/B: nome de arquivo classificado como operação / exemplo de pedido
  classificado como nome. O par segue invertido.
- Q08B: fonte explicitamente inconclusiva classificada como operação.

Primeira fronteira RED restante: fonte/foco íntegros → atribuição de papel
no bruto. Nenhum desses erros nasce em parser, shape ou veto do host. Não
declarar quatro roots nem inferir mecanismo interno único: a instrução
melhorou o painel, mas não demonstrou por que persistem essas confusões.
O princípio reutilizável é explicitar a diferença entre função do foco na
fonte e aparência de comando, sem transformar nenhuma delas em autorização.
Serve à leitura de comandos, ensino, memória e citações; não exige editar
esses domínios nesta investigação.

Artefato exclusivo, 42 linhas (metadata + 40 consultas + resumo):
`resultados_testes/sonda_papel_leitura_direta_v1_ab_replay.jsonl`, SHA256
`65bd3c3870df9417dce5e674ff4058262484a14f54fc2f03ef366fa0ad3583be`.
Digest no início/fim e na auditoria:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Isso não prova invariância contínua ou determinismo do modelo.
Tempos somados 54,8633s / 19,2147s; tokens de saída 228 / 224. Carregamento
21,7386s / 0,1504s torna a comparação de velocidade inadequada; não alegar
ganho de desempenho por esse contraste.

**46 testes novos e 1.332 relevantes verdes (contagens sobrepostas)**,
`git diff --check` sem erro; não são prova de runtime da Laylay ou de
generalização semântica. Produção/treino não alterados por esta coleta,
nenhum commit. Painéis, sondas e artefatos históricos preservados.

Próxima fronteira, ainda não executada: congelar frases independentes e
referências antes da consulta; comparar os mesmos dois prompts sem novo
ajuste, incluindo funções contextuais, negação, aspas aninhadas, instrução
externa ao foco e ambiguidade real em domínios distintos. Denominador
completo, controles negativos e pares necessários. Não treinar com esse
teste diagnóstico; somente depois discutir composição/validação no runtime.

P01 permanece aberta. Esta evidência sustenta um candidato de instrução,
não liberação da rede, resolução de referente ou validação de suporte.

### P01: coordenadas dos tokens — replay diagnóstico não promovido (29/09)


Base preservada: HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch
`main`, worktree anterior intacta. A pesquisa confirmou o padrão já usado
pelo produtor de intervalos: `id/texto` para o modelo, posições originais
para o host. O experimento anterior, painel/revisão e respostas não mudam.
Novos arquivos apenas:

- `scripts/analises/sonda_coordenadas_vinculo_v1.py`;
- `scripts/tests/test_sonda_coordenadas_vinculo_v1.py`.

Hipótese testada: expor dois tipos de coordenada no registro de cada token
contribui para a falha de propor contexto externo. Contraste de **mesma
tarefa de vínculo**, não comparação com o antigo braço de papel direto:
`tokens_com_offsets` conserva entrada inteira; `tokens_id_texto` retira
somente `inicio/fim` dos tokens. Ambos usam os mesmos prompt, schema,
fonte/foco, opções e `conferir_vinculo`. O verificador recebe entrada host
completa nos dois braços. Foco/árvore de aspas **ainda expõem caracteres**;
não é contraste que remove toda ambiguidade de coordenadas.

Reusa exatamente os 20 casos, oito pares e revisão já congelados: replay
dirigido e visto, **não holdout novo**. Sem alteração do ouro, exemplos extras
no prompt, reancoragem, correção adivinhada de índices ou aceite parcial.
40 consultas locais, 20 por braço, 10 ordens AB e 10 BA. Temperatura 0,
limite 700; digest Qwen observado no início/fim:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Igualdade nos extremos não garante invariância contínua ou determinismo.

Congelamento:

- script replay: `096894e0a2cc6724adc6ccc008981cd3c24961a196063293f80cc97d939033ff`;
- dependência vínculo: `0231344e4d4a9ac975ab1a98995b382222264197e5bea8d835facb7599aca89c`;
- painel/revisão: mesmos hashes do A/B anterior, conferidos antes da geração;
- artefato anterior: `59c97f28c3706fd3ff3f60920ad7a25702e0be096e023e5f45b417e98963c68b`.

Artefato exclusivo `resultados_testes/sonda_coordenadas_vinculo_v1_ab_replay.jsonl`
contém 42 linhas: metadados, 40 propostas JSON parseadas com payload do
modelo/host e conferência, resumo. Hash:
`ffee5c2eabf07aa99eefad4743558d14465ae8862c5f5e034c584f2a016be155`.
Não registra HTTP bruto ou motivo de término. Nenhum erro de consulta.

| Fronteira | Tokens com offsets | Tokens só id/texto |
| --- | ---: | ---: |
| Papel bruto válido | 20/20 | 20/20 |
| Papel alinhado à revisão local | 12/20 | 14/20 |
| Pares contextuais completos | 3/8 | 5/8 |
| Envelope conjunto válido | 15/20 | 18/20 |
| Listas de evidências vazias | 15/20 | 18/20 |
| Envelopes com intervalos inválidos | 5/20 | 2/20 |
| Evidência literal externa materializada | 0/20 | 0/20 |
| Papel e pistas locais alinhados conjuntamente | 0/20 | 0/20 |

Papéis melhoram em Q02A/Q03B/Q04B e regridem em Q05A; Q01B muda rótulo
mas continua errado. A projeção não recupera evidência: as listas vazias
aumentam, e Q05B/Q09A ainda propõem intervalos inválidos. Não reduzir isso
a “precisão melhorou”: distinguir papel bruto, envelope e evidência.
Retirar offsets dos tokens **não basta** para superar o RED literal. Não
prova irrelevância de toda apresentação, nem causa interna única do modelo.

Controle repetido diverge do histórico em propostas de Q05A/Q06B/Q01B/
Q05B/Q08A. O placar 12/20 permanece, mas a composição muda e os pares passam
de 2/8 para 3/8. Não reutilizar o controle histórico como se fosse a rodada
contemporânea; não atribuir a variação ao candidato. Pesos do histórico não
tinham digest registrado, tampouco há revisão humana independente.

Validação: **64 testes novos; 760 regressivos relevantes verdes**, com 122
focados sobrepostos. A réplica da apresentação anterior reproduziu o RED
de offsets ainda visíveis em 20 fontes antes da projeção. GREEN após retirar
somente esses campos. Testes capturam payload real da consulta substituída,
protegem host/schema de mutação, comparam mesma proposta materializada em
ambos, mantêm rejeição atômica e tipos, recusam resumo adulterado/duplicado/
parcial e preservam arquivo exclusivo. Resumo recalcula conferência e
métrica em vez de confiar em aferição armazenada. Compilação/diff-check limpos.

Próxima investigação: separar seleção literal externa da classificação de
papel, medindo cada fronteira, sem forçar evidência falsa quando a proposta
for incerta. Antes de outro contraste novo, definir qual saída comprova
ocorrência sem escolher significado, como validar foco/negativas/ambiguidade,
e qual contribuição se espera na mesma tarefa final. Não acumular novos
prompts de enum, treino ou gates por aspas. Sem produção, memória, vigência,
treino, runtime, efeito externo ou commit. P01 não encerrada.

### P01: vínculo contextual com intervalos — contraste não promovido (29/09)

Base mantida: HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch
`main`, worktree anterior preservada. Pesquisa de código orientou o reuso de
fonte/foco/aspas do diagnóstico de papel e de `tokenizar_fonte`, que conserva
ocorrência e offsets originais, inclusive trechos repetidos. Não transplantar
o conversor de condições como verificador semântico genérico.

Contrato do protótipo: proponente envia papel e até dois intervalos de tokens
externos ao foco; host autentica entrada, tipos, limites, ordem e disjunção
do foco e materializa texto da fonte. Contexto externo a uma citação interna
pode pertencer à citação externa. Lista vazia é abstenção de evidência, não
prova de ausência. Literal válido e cobertura lexical de pistas não provam
suporte semântico. Todas as flags de semântica, referente, autorização,
vigência e produção permanecem falsas.

Arquivos funcionais novos:

- `scripts/analises/sonda_vinculo_contextual_v1.py`;
- `scripts/analises/dados/sonda_vinculo_contextual_v1.json`;
- `scripts/analises/dados/sonda_vinculo_contextual_revisao_v1.json`;
- `scripts/tests/test_sonda_vinculo_contextual_v1.py`.

20 fontes novas, oito pares com conteúdo focal idêntico e relação nominal
ou operacional diferente, mais estados e ambiguidades. Inclui menção negada,
hipótese, nome de arquivo dentro de comando externo, aspas aninhadas e
múltiplas operações sem seleção da principal. Revisão local dirigida, não
holdout independente nem certificação de semântica geral.

Congelamento anterior à geração:

- painel: `fe94a2a77ac28b2b870004f16f9ca21f4bebf4469955b6f17b4cd10f29dfc682`;
- revisão: `04d53c818d217f910dfd2eb766e3800865544c9a3fd7b64ccd98318743c5d6a0`;
- script usado: `0231344e4d4a9ac975ab1a98995b382222264197e5bea8d835facb7599aca89c`.

Qwen `qwen3:4b-instruct`, temperatura 0, limite 700, fonte/foco/tokens
idênticos nos dois braços e ordem contrabalanceada. Baseline mantém prompt e
schema do papel; candidato altera instrução/schema para pedir intervalos.
Essa comparação avalia o pacote candidato, não isola evidência de custo de
formato. Ordem de emissão “evidências antes do papel” solicitada não comprova
ordem do raciocínio interno. Nenhum gabarito/âncora foi enviado ao modelo.
Não comparar ao antigo 10/16: painel e apresentação diferentes.

Artefato exclusivo, preservado com entrada, proposta JSON parseada, conferência e
metadados: `resultados_testes/sonda_vinculo_contextual_v1_ab_primeira.jsonl`.
Não registra HTTP bruto, motivo de término ou digest do modelo; é uma execução
local de 20 casos, sem revisão humana independente.

| Fronteira | Papel direto | Papel + evidências |
| --- | ---: | ---: |
| Rótulo bruto válido | 20/20 | 20/20 |
| Papel bruto alinhado à revisão local | 14/20 | 12/20 |
| Pares contextuais completos | 5/8 | 2/8 |
| Envelope conjunto válido | 20/20 | 15/20 |
| Evidência literal externa válida | Não solicitada | 0/20 |
| Papel e pistas locais alinhados conjuntamente | Não solicitado | 0/20 |

**Não demonstrou ganho.** No candidato há 15 listas vazias e cinco propostas
de intervalo inválidas (limites, intervalos vazios/invertidos). O papel bruto
é medido antes e independentemente da guarda conjunta: seus 12 acertos não
desaparecem por erro de coordenada. Duas trocas favorecem o candidato e quatro
o prejudicam; não ajustar ouro após observar saídas.

Primeira fronteira da evidência: o proponente não fornece conjunto válido;
a cobertura lexical de pistas não recebe evidência materializada. Não culpar
somente a conferência/âncora, nem concluir que uma fonte literal garantiria
significado. Q05B tem um intervalo individual válido, que selecionaria
`como`, mas o segundo extrapola os tokens; a guarda rejeita atomicamente o
conjunto, sem evidência parcial publicada. Possível ambiguidade da
apresentação ainda **não contrastada**:
tokens/foco expõem `inicio/fim` de caracteres e a resposta exige campos
homônimos em IDs de tokens. Valores observados compatíveis com outra escala
não demonstram a causa interna exclusiva; listas vazias tampouco a provam.
Interpretar retrospectivamente os números como caracteres também não recupera
vínculo válido: quando selecionam texto, atingem aspas ou a citação externa
que intersecta o foco; outros continuam vazios/invertidos. Isso não substitui
o contraste de apresentação e não autoriza normalizar respostas antigas.

Validação: **58 testes novos e 696 regressivos relevantes verdes**, com 141
focados sobrepostos. RED da própria sonda: foco citado vazio chegava à
consulta; guarda mínima passa a recusá-lo antes da geração. Testes cobrem
entrada adulterada, tipos bool/float, intervalos inválidos sem aceite parcial,
ocorrência repetida, contexto aninhado, ambiguidade, separação papel/evidência
e impossibilidade de fabricar uma âncora concatenando fragmentos distintos.
Compilação e diff-check limpos. Painéis/gabaritos antigos intactos.

Próximo diagnóstico: contrastar apresentação de coordenadas sem homonímia,
mantendo offsets originais no host, fonte/foco e objetivo intactos. Usar
replay marcado como diagnóstico, nunca como holdout novo, e testar tanto
intervalos quanto papel bruto. Só se a fronteira literal alinhar avaliar
vínculo semântico; não corrigir intervalo por adivinhação nem usar rótulo
como gate automático. Nenhum runtime, treino, memória, vigência, efeito,
produção ou commit alterado. P01 e liberação da rede continuam pendentes.

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
