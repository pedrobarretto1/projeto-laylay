# Especialista neural de comandos

Este pacote interpreta linguagem operacional de vários domínios sem substituir
a autoridade canônica do turno. O modo padrão é `shadow`: a previsão é anexada
ao turno, mas sempre publica `autoriza_execucao=false`.

O aprendizado possui duas velocidades:

- receipts confirmados entram no buffer como evidência para revisão, nunca como
  rótulo automático de intenção;
- correções explícitas confirmadas por uma execução correta tornam-se elegíveis
  para revisão; somente as aprovadas no ledger append-only
  `memoria/neural/revisoes_correcoes.jsonl` entram no próximo treino.

O ciclo controlado é executado com:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.treino `
  --estado memoria\neural `
  --promover-se-aprovado
```

Lotes novos não entram diretamente no DEV canônico. Eles são avaliados em
staging com:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.treino `
  --estado memoria\neural `
  --versao tfidf-candidato `
  --lote-candidato mente_laylay\neural\datasets\candidatos\lote.jsonl
```

Um lote staged passa pela validação de schema e pelo detector de leakage antes
de criar o artefato candidato. Enquanto `--lote-candidato` estiver presente, o
ciclo recusa `--promover-se-aprovado`: primeiro o lote precisa passar as
métricas e ser incorporado explicitamente ao DEV. Reprovação não contamina a
base canônica e não troca o modelo ativo.

A promoção só troca o artefato quando o candidato não piora falso comando,
negação perdida, precisão, recall nem acurácia de intenção no challenge
congelado. Quando já existe um modelo ativo, também precisa existir aprendizado
novo comprovável: correções fortes inéditas, mudança da base ou melhora de
métrica. Retreinar exatamente os mesmos dados nunca troca apenas o número da
versão. Mesmo promovido, ele continua em modo sombra; liberação operacional
exige um gate separado por intenção e risco.

A meta inicial de coleta para a expansão do dataset é de 150 a 200 exemplos DEV
por variante `intent:ação`. Cada variante também precisa de pelo menos 12
famílias linguísticas e 15 comandos negados; cada domínio operacional precisa de
30 hard negatives DEV próximos de comandos reais. São cotas configuráveis de
coleta, não prova de qualidade nem permissão de execução. Famílias continuam
separadas entre DEV e challenge, e segurança e receipts são gates independentes.
Esse intervalo é um piso inicial de cobertura, não um teto: novas famílias podem
ultrapassá-lo sempre que erros reais ou validação fora da amostra demonstrarem
uma fronteira ainda fraca. A quantidade nunca substitui os gates de qualidade.

A cobertura atual pode ser auditada sem treinar nem promover modelo:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.cobertura
```

O arquivo `memoria/neural/cobertura_dataset.json` separa a quantidade de DEV da
quantidade congelada, mostra lacunas por capacidade registrada e mede a meta por
`intent:ação`, famílias, negações e hard negatives por domínio. O challenge
nunca é somado a nenhuma cota DEV. A cobertura de ações ainda desconhecidas
precisa ser declarada no catálogo; o relatório não inventa ações ausentes.

As 17 variantes iniciais ficam declaradas em
`datasets/catalogo_variantes_v0.json`. Esse catálogo serve apenas para revelar
classes com zero exemplos, fixar as cotas iniciais e validar a cobertura; todas
as entradas mantêm `operational_influence_enabled=false`. Domínios observados
sem variante operacional, como conversa geral, aparecem no diagnóstico, mas não
criam um gate acidental de hard negatives.

Antes de ampliar ou treinar, audite também o isolamento do challenge:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.qualidade
```

O resultado em `memoria/neural/qualidade_dataset.json` aponta famílias
compartilhadas, duplicatas e paráfrases lexicalmente próximas entre DEV e
Frozen. A auditoria não move nem remove frases automaticamente.

Para medir generalização sem ajustar o modelo pelo Frozen Challenge, execute:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.validacao_cruzada `
  --destino memoria\neural\cv_canonico.json

.\.venv314\Scripts\python.exe -m mente_laylay.neural.validacao_cruzada `
  --lote-candidato mente_laylay\neural\datasets\candidatos\lote.jsonl `
  --destino memoria\neural\cv_candidato.json

.\.venv314\Scripts\python.exe -m mente_laylay.neural.validacao_cruzada `
  --agrupamento validation_group `
  --destino memoria\neural\cv_semantica.json
```

Cada família linguística fica inteira em um fold: uma paráfrase irmã nunca
aparece no treino quando outra frase da mesma família está em validação. Esse
relatório é diagnóstico de generalização, não autorização de promoção ou
execução. O Frozen permanece reservado ao gate final.

Os lotes gerados mais recentes também declaram `validation_group`. Esse campo
agrupa famílias de superfície que exercitam o mesmo mecanismo linguístico.
Com `--agrupamento validation_group`, todas essas famílias ficam no mesmo fold;
essa é a validação principal para comparar candidatos, pois impede que moldes
irmãos do mesmo mecanismo apareçam simultaneamente em treino e validação. A CV
por `family` continua disponível como diagnóstico secundário e compatível com
lotes antigos.

Na configuração experimental de 3.106 exemplos, a linha de base semântica
revelou que a CV somente por família era otimista. O candidato com ownership
das features por cabeça e n-gramas especializados ficou em `6,20%` de falsos
comandos, `98,73%` de precisão de comando, `96,37%` de recall, `90,08%` de
intenção, `86,99%` de ação e `86,87%` de acerto conjunto. A taxa de negação
perdida caiu para `0%`, com apenas uma falsa negação nos 3.106 exemplos. O
relatório canônico está em
`memoria/neural/cv_catalogo_17_variantes_semantica_v7_fallback_corrigido.json`
e não autoriza promoção nem execução.

Os relatórios semânticos v1–v6 são históricos e não devem ser usados como
baseline: um fallback convertia a ausência de `validation_group` na string
`"none"` e colapsava famílias legadas em um só grupo. O fallback corrigido usa
a própria `family`, elevando o total real de 412 para 611 grupos. Um teste de
regressão protege lotes antigos que ainda não declaram grupo explícito.

Na representação `tfidf_indicadores`, cada pista tem um owner: extensões de
negação alimentam somente a cabeça de negação; a cabeça de comando preserva
apenas as pistas já úteis à detecção de comandos; intenção e ação recebem o
texto TF-IDF normal. Isso evita que uma melhoria local desloque classificadores
que não possuem aquela decisão.

As cabeças de comando e negação usam n-gramas de caracteres `4–6`, enquanto
intenção e ação preservam `3–5`. O intervalo especializado reduziu colisões
morfológicas e dominou o candidato anterior nos gates de falso comando,
precisão, recall e negação. Experimentos que apenas aumentaram o peso de
palavras ou aplicaram o intervalo globalmente foram rejeitados por regressão.

Um benchmark isolado com
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, usando ONNX
quantizado e preservando os gates lexicais de comando e negação, elevou
intenção para `90,66%`, ação para `88,03%` e acerto conjunto para `87,84%` nos
mesmos 611 grupos. O encoder agora possui integração experimental explícita:
os embeddings alimentam somente intenção e ação, enquanto comando e negação
continuam sob os gates lexicais. O artefato é carregado de forma tardia,
validado opcionalmente por SHA-256 e nunca vira fallback automático. Essa
integração não autoriza promoção nem influência operacional.

Uma validação experimental pode ser executada apontando para o diretório local
do encoder, sem incorporar o challenge ao treino:

```powershell
python -m mente_laylay.neural.validacao_cruzada `
  --estrategia sgd_log_loss `
  --arquitetura-comando intent_gated `
  --arquitetura-acao hierarchical `
  --limiar-comando 0.65 `
  --representacao onnx_semantico `
  --encoder-semantico memoria/neural/modelos/paraphrase-multilingual-MiniLM-L12-v2-onnx-qint8-avx2 `
  --sha256-encoder-semantico 98a01d88b7de996cdea58c32ca71208c09968d143798814b2ea09d3439dc334f `
  --agrupamento validation_group
```

O limiar OOD lexical não é reaproveitado como se estivesse calibrado para os
embeddings: previsões semânticas publicam `ood_calibrated=false` até existir
uma calibração própria. `onnxruntime` e `tokenizers` são dependências opcionais
desse experimento e só são importadas quando ele é solicitado.

A CV integrada canônica está em
`memoria/neural/cv_catalogo_17_variantes_semantica_v8_minilm_integrado.json`.
Nos mesmos 3.106 exemplos, 611 grupos semânticos e cinco folds, ela obteve
falso comando `0,0446`, precisão de comando `0,9909`, recall `0,9618`, intenção
`0,9037`, ação `0,8973`, acerto conjunto `0,8942` e nenhuma negação perdida.
Ela substitui o benchmark isolado como prova da composição real. Os números
diferem porque `intent_gated` agora aplica o veto usando a intenção semântica
do próprio modelo integrado; o benchmark anterior preservava a decisão final
de comando do baseline lexical. O relatório continua declarando
`autoriza_execucao=false` e `autoriza_promocao=false`.

## Calibração OOD semântica

O conjunto `datasets/ood_calibracao_v0.jsonl` contém 200 comandos fora das 17
variantes do catálogo, em 20 famílias: 100 frases para escolher o limiar e 100
paráfrases reservadas para holdout. Esses exemplos não entram no treino das
cabeças de intenção, comando, negação ou ação.

O relatório
`memoria/neural/cv_catalogo_17_variantes_semantica_v10_ood_diagnostico.json`
falsificou a hipótese de que um único corte na confiança da intenção separaria
comandos conhecidos de comandos fora do catálogo:

- limitando falso aceite OOD a `1%`, o recall operacional conhecido caiu para
  `75,27%`;
- preservando recall conhecido em `85,10%`, o falso aceite OOD ficou em `5%`
  na calibração e `9,4%` no holdout.

Por isso, `ood_calibrated` continua falso para a representação semântica e não
há limiar recomendado. A normalização preserva esse estado, o gate operacional
rejeita candidatos não calibrados e o shadow não transforma um OOD ainda não
calibrado em falso “comando perdido”. O próximo experimento arquitetural deve
avaliar um owner específico para pertinência ao catálogo, separado das cabeças
de intenção e ação; ele não deve ser promovido antes de superar o mesmo holdout.

O primeiro detector binário (`ood_detector_v1`) foi preservado como diagnóstico
histórico, mas não como prova: as mesmas famílias OOD atravessavam treino,
calibração e avaliação. O `ood_detector_v2` corrige essa fronteira com 30
famílias inteiras e disjuntas, dez por partição. Nesse teste mais realista:

- a cabeça binária MiniLM + SGD, mantendo `85,14%` dos comandos conhecidos,
  aceitou `49,6%` dos OOD na calibração e `61,2%` no holdout;
- a distância aos protótipos das variantes conhecidas, mantendo `85,00%`,
  aceitou `27,8%` dos OOD já na calibração.

Ambas foram rejeitadas. Os relatórios são
`memoria/neural/benchmark_detector_ood_v2.json` e
`memoria/neural/benchmark_detector_ood_prototipos_v1.json`. Nenhum desses
detectores foi integrado ao modelo.

## Modelo semântico no shadow real

O artefato `memoria/neural/modelo_semantico_shadow.joblib` contém a configuração
`minilm-shadow-v1-3106`. Quando `LAYLAY_NEURAL_MODE=shadow`, esse arquivo existe
e `LAYLAY_NEURAL_MODEL_PATH` está vazio, a composição o seleciona apenas para
observação. Em qualquer outro modo, o padrão continua sendo
`modelo_ativo.joblib`; um caminho configurado explicitamente sempre prevalece.

O shadow não altera o turno, não concede autoridade e não executa. Mesmo se
alguém habilitar o gate experimental, `ood_calibrated=false` resulta em
`ood_nao_calibrado`. Assim, o runtime pode colher divergências e receipts reais
sem transformar a falha de OOD em permissão.

O benchmark pode usar `--estrategia logistic`, `sgd_log_loss` ou
`complement_nb`. A regressão logística continua sendo o padrão. Estratégias
alternativas são experimentais e o ciclo recusa promovê-las; elas precisam
primeiro superar generalização por famílias e depois todos os gates do Frozen.

Também existem duas arquiteturas experimentais, avaliáveis sem promoção:

- `--arquitetura-comando intent_gated` exige uma intenção conhecida para
  manter `is_command=true`. Se a cabeça binária sugerir comando com
  `intent=NONE`, o resultado final é vetado, os parâmetros executáveis são
  removidos e a observação bruta fica disponível para diagnóstico;
- `--arquitetura-acao hierarchical` escolhe a ação somente pela cabeça da
  intenção prevista, impedindo que uma intenção conhecida publique uma ação
  pertencente a outro owner.

Os padrões estáveis continuam `--arquitetura-comando independent` e
`--arquitetura-acao global`. Trocar qualquer arquitetura torna a configuração
experimental e o ciclo recusa `--promover-se-aprovado` até que o contrato seja
aprovado explicitamente após CV por famílias e Frozen.

## Relatório do modo shadow

O runtime compara a previsão com duas autoridades diferentes, sem criar outro
roteador:

- ao final do turno, compara comando executável com a autorização canônica já
  reconciliada com vetos, contexto e esclarecimentos;
- depois de uma ação, compara intenção e ação somente com receipt confirmado.

Os eventos append-only ficam em `memoria/neural/shadow_eventos.jsonl`, e o
resumo acumulado em `memoria/neural/shadow_relatorio.json`. O resumo separa
falso comando, comando perdido, divergência de intenção e divergência de ação,
inclusive por intenção. Texto completo só é retido nos casos divergentes; os
acordos guardam apenas o hash. Todo registro declara `autoriza_execucao=false`,
`apto_treino=false` e `predicao_propria_vira_label=false`: divergência indica um
caso para revisão, não um rótulo verdadeiro.

### Auditoria das evidências reais

O auditor fail-closed separa eventos antigos do modelo esperado, receipts que
servem apenas para revisão e correções explícitas confirmadas que podem formar
um lote candidato. Ele também separa correções pendentes, aprovadas e rejeitadas.
O treino consulta a última decisão válida por ID e, na ausência dela, mantém a
correção fora do dataset. O auditor não publica o texto das conversas, não
transforma divergência em label e não incorpora exemplos automaticamente ao
treino ou ao DEV:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.auditoria_shadow `
  --pasta-estado memoria\neural `
  --modelo-esperado minilm-shadow-v1-3106
```

O status `aguardando_sessao_modelo_esperado` significa que a Laylay ainda não
registrou um turno real com esse artefato. O status
`sem_correcoes_explicitamente_confirmadas` significa que a coleta existe, mas
ainda não há exemplos elegíveis. `sem_correcoes_pendentes_revisao` significa
que as correções existentes já foram rejeitadas. Mesmo quando houver correções
disponíveis, elas continuam em revisão e fora do treino e do DEV até aprovação.

## Onda `MUSIC_SEARCH` v3 em staging

O gerador `datasets/gerar_musica_search_onda_v3.py` produz um lote reproduzível
com 240 exemplos: 120 comandos afirmativos, 40 comandos negados e 80 hard
negatives. Somado aos exemplos canônicos e aos lotes candidatos anteriores, o
conjunto chega a 185 comandos `MUSIC_SEARCH`, dentro da meta de 150 a 200
exemplos por comando.

A validação cruzada por famílias, usando a mesma estratégia experimental
`sgd_log_loss` nos dois lados, mostrou ganho de compreensão mas regressão de
segurança:

- acurácia de intenção: `0.5544 -> 0.6397`;
- acurácia conjunta: `0.4715 -> 0.7208`;
- falso comando: `0.2857 -> 0.3800`;
- negação perdida: `0.0370 -> 0.1735`.

Por isso, a onda v3 permanece em staging: não foi incorporada ao DEV, não
alterou o modelo ativo e não habilitou influência operacional. O relatório de
CV agora também agrupa erros por família linguística para orientar a próxima
onda sem converter previsões do próprio modelo em rótulos.

## Ondas contrastivas v4 e volume v2

A onda `MUSIC_SEARCH` v4 mantém o volume da v3, mas distribui os mecanismos em
100 famílias menores. A onda `VOLUME` v2 adiciona 132 exemplos para `down`, 132
para `up` e 60 hard negatives. Com o DEV e os pilotos anteriores, a cobertura
chega a:

- `MUSIC_SEARCH:search`: 185 exemplos;
- `VOLUME:down`: 151 exemplos;
- `VOLUME:up`: 152 exemplos.

A representação experimental `tfidf_indicadores` acrescenta marcadores gerais
de negação e exclusão como atributos de aprendizado. Esses marcadores não
classificam, não autorizam e não executam. O limiar experimental de comando
`0.65` apenas veta propostas de baixa confiança; ambos preservam os padrões
anteriores quando não solicitados e impedem promoção automática.

Na validação cruzada por famílias dos 810 exemplos, o candidato obteve falso
comando `0.1059`, precisão `0.9536`, recall `0.8955`, intenção `0.8580` e
negação `0.9988`. No Frozen, porém, o recall caiu para `0.5294`: somente 3 das
17 variantes declaradas alcançaram a faixa de 150 a 200 exemplos. Portanto, o
candidato continua rejeitado e em shadow. O próximo passo é completar outras
variantes, sem afrouxar o gate e sem transformar o Frozen em treino.

## Onda navegador v1

O gerador `datasets/gerar_navegador_onda_v1.py` acrescenta 144 exemplos para
cada uma das variantes `CLOSE_TAB:close`, `OPEN_URL:open`, `LIST_TABS:list` e
`SEARCH:search`, além de 80 hard negatives. Na combinação com as ondas
anteriores, essas variantes alcançam respectivamente 150, 150, 150 e 151
exemplos DEV, deixando 10 das 17 variantes ainda abaixo da meta.

Nos 1.466 exemplos combinados não há duplicatas internas nem leakage com o
Frozen. A CV por famílias obteve falso comando `0.0981`, precisão `0.9723`,
recall `0.9461`, intenção `0.8950`, acerto conjunto `0.9330` e nenhuma negação
perdida. O Frozen ainda reprovou o estágio: falso comando `0.1429` e recall
`0.5882`. Nenhum dado do Frozen foi incorporado ao treino, nenhum modelo foi
promovido e o runtime permanece em shadow.

## Cobertura completa do catálogo v0

As ondas `apps_arquivos_onda_v1` e `iot_midia_clima_onda_v1` completam as dez
variantes restantes. O conjunto em staging possui 3.106 exemplos e todas as 17
variantes declaradas ficam entre 150 e 185 exemplos, com cotas mínimas de
famílias, negações e hard negatives atendidas em todos os domínios. A combinação
não possui duplicatas internas nem leakage com o Frozen.

Na CV por famílias, a configuração experimental obteve falso comando `0.0698`,
precisão `0.9859`, recall `0.9730`, intenção `0.9363`, acerto conjunto `0.9633`
e nenhuma negação perdida. O Frozen ainda rejeitou o candidato com falso
comando `0.1429` e recall `0.7647`, embora intenção tenha chegado a `0.9167` e
ação a `0.7059`. A cobertura completa não substitui generalização: o candidato
continua sem promoção, sem influência operacional e em shadow. Próximos ajustes
devem nascer de CV e receipts reais revisados, nunca de frases copiadas do
challenge.

## Candidato híbrido guiado pelo shadow real

A auditoria do shadow separou seis receipts reais confirmados para avaliação
reservada, sem transformá-los automaticamente em treino. O artefato semântico
ativo acertava somente um dos seis pares intenção/ação; o candidato híbrido com
o lote `shadow_mecanismos_v3` passou a acertar cinco. O sexto caso, `desliga a
luz`, revelou uma fronteira independente entre comando IoT e frases que apenas
descrevem hábito, estado, preferência ou planejamento.

O primeiro lote contrastivo amplo (`shadow_contrastivo_v2`, 207 exemplos) foi
rejeitado porque melhorava os receipts, mas piorava a validação global e a
negação. A correção arquitetural não foi aumentar dados cegamente. A
representação `onnx_semantico_hibrido` passou a combinar o vetor MiniLM com
atributos lexicais determinísticos para intenção e ação, enquanto gates de
comando e negação permanecem lexicais e independentes.

Exemplos agora podem declarar `training_heads`. Um lote especializado altera
somente os owners indicados; `intent`, `intent_gate`, `command`, `negation` e
`action` não compartilham escopo implicitamente. Hard negatives direcionados
podem declarar `command_head_intent`, criando uma cabeça de comando do domínio
sem contaminar o classificador global. A intenção principal seleciona essa
cabeça; o gate semântico continua apenas como veto de intenção desconhecida e
não assume ownership de outro domínio. Essa separação não concede autoridade e
não muda o executor.

Para comparações incrementais, `--estrategia-particao hash_estavel` atribui cada
grupo a um fold por hash. Assim, adicionar famílias não redistribui as famílias
antigas. `--lotes-base-comparavel` publica métricas somente da fatia histórica,
evitando comparar bases diferentes como se fossem o mesmo experimento. Limiar
por intenção também é aceito no treino e continua sendo configuração
experimental, bloqueada para promoção automática.

O lote `iot_fronteira_comando_v4` possui 168 exemplos: 66 comandos e 102 hard
negatives, em 56 grupos. Ele não contém frases dos seis receipts nem do Frozen,
e a auditoria encontrou zero duplicatas exatas, zero quase duplicatas e zero
famílias compartilhadas com o challenge. Na CV estável final:

- a fatia histórica de 3.106 exemplos manteve 26 falsos comandos e uma falsa
  negação;
- recall de comando ficou em `0,9494`, intenção em `0,9317`, ação em `0,9112`
  e acerto conjunto em `0,9100`, todos acima da linha híbrida estável anterior;
- no objetivo próprio do v4, 159 de 168 exemplos acertaram a fronteira
  comando/não-comando (`94,64%`): restaram três falsos comandos e seis comandos
  perdidos.

O artefato integral `hibrido-v3-iot-v4-168` acertou os seis receipts reais e
recuperou o recall do Frozen para `0,8235`, com precisão `1,0` e zero falso
comando. Ainda foi rejeitado: três comandos de outros domínios permanecem abaixo
do limiar global e o comando IoT `deixa a lâmpada acesa` recuperou a fronteira de
comando, mas ainda errou a ação. Portanto, nenhum modelo ativo foi substituído.
O próximo lote deve atacar action `on/off` e os comandos globais perdidos como
raízes separadas; não deve reutilizar frases reservadas como treino.

## Estados afirmativos e negação contrastiva

A auditoria da fronteira IoT encontrou rótulos semanticamente invertidos nos
geradores: frases como `mantenha o abajur desligado` e `deixa o abajur
funcionando` estavam representadas como negação da transição oposta. Quando a
ação inversa existe no catálogo, o contrato correto é um pedido afirmativo do
estado descrito. Os geradores de IoT/mídia e apps/arquivos agora materializam
esses casos como `negated=false` e com a ação canônica de destino. Para manter a
cobertura mínima depois da correção, foram acrescentadas 60 variações
afirmativas independentes: 12 de `CLOSE_APP:close`, 24 de `IOT_CONTROL:off` e
24 de `MEDIA_CONTROL:pause`.

Uma cabeça de negação hierárquica e uma variante híbrida foram testadas e
rejeitadas. Elas acertaram o Frozen, mas perderam respectivamente 79 e 28
negações na CV por grupos. A arquitetura permaneceu global. A solução aprovada
para continuar em staging foi ensinar cada owner explicitamente:

- os 66 comandos afirmativos do `iot_fronteira_comando_v4` treinam `command` e
  `negation`; seus 102 não-comandos continuam exclusivos de `command`;
- o lote `negacao_contrastiva_v5` traz 108 exemplos, 54 afirmativos e 54
  negados, em 36 grupos, e treina somente `negation`;
- `command_head_intent` continua selecionando apenas a cabeça de comando, mas
  pode coexistir com outros heads declarados em `training_heads`.

Não há frases dos 24 itens Frozen nem dos seis receipts no v5. A auditoria
registrou zero duplicatas exatas, zero quase duplicatas e zero famílias
compartilhadas. Na CV estável da combinação v4+v5, a fatia histórica ampliada
para 3.166 exemplos obteve precisão de comando `0,9898`, recall `0,9487`,
intenção `0,9362`, ação `0,9272` e acerto conjunto `0,9260`. A negação ficou em
`0,9940`, com cinco falsas negações e 14 negações perdidas. Como controles,
antes da ampliação v4 sozinho somou 28 erros históricos de negação; v5 sozinho
somou 16, mas não corrigiu o caso reservado; a combinação anterior somou 17.
Depois da ampliação, a combinação soma 19 e continua corrigindo o caso.

O artefato `hibrido-v3-iot-v4-negacao-v5-v3` interpreta `deixa a lâmpada
acesa` como `IOT_CONTROL:on`, comando afirmativo e não negado, preserva recusas
explícitas e acerta os seis receipts em intenção/ação. No Frozen, obteve
negação `1,0`, ação `0,8235`, precisão de comando `1,0` e recall `0,8235`.
Na leitura completa dos receipts, quatro de seis também atravessam o limiar de
comando; `liga a luz` e `desliga a luz` preservam intenção/ação, mas ficam em
`0,6019` e `0,6028`, abaixo do limiar global `0,65`.
Ele continua rejeitado por `command_recall_fora_do_limite`; nenhum modelo ativo
foi substituído e a próxima raiz permanece nos três comandos globais abaixo do
limiar, além da preservação desses dois imperativos curtos de IoT.

## Fronteiras dirigidas de comando v6

O lote `fronteiras_comando_v6` adiciona 252 exemplos em 82 grupos para os
owners `IOT_CONTROL`, `OPEN_URL`, `MUSIC_SEARCH` e `WEATHER`: 108 comandos e
144 não-comandos. Todos treinam exclusivamente `command`, com
`command_head_intent` explícito. A auditoria contra o Frozen e os seis receipts
registrou zero duplicatas exatas, zero quase duplicatas e zero famílias
compartilhadas.

O primeiro candidato v6 tornou precisão e recall de comando do Frozen iguais a
`1,0`, mas a CV histórica expôs a raiz arquitetural: um head dirigido reunia os
comandos globais do intent e ignorava os hard negatives globais do mesmo
domínio. Isso elevou os falsos comandos históricos de 26 para 55. O treinador
agora reutiliza os não-comandos globais do domínio do owner, sem absorver
negativos de outros domínios. Um teste inspeciona o vocabulário efetivamente
entregue ao head, em vez de inferir a composição por resultado final.

Com essa correção e calibração apenas de `MUSIC_SEARCH=0,75` e
`WEATHER=0,725`, o candidato experimental
`hibrido-v3-iot-v4-negacao-v5-cmd-v6-cal-v8` obteve no Frozen precisão e recall
de comando `1,0`, negação `1,0` e ação `0,9412`. Ele reconhece os quatro alvos
reservados desta etapa e os seis receipts completos como comandos, com intenção
e ação corretas. Na base comparável de 3.166 exemplos, precisão passou de
`0,9898` para `0,9902`, recall de `0,9487` para `0,9491` e falsos comandos de 26
para 25; intenção e negação permaneceram iguais.

O lote ainda não foi promovido. Na validação apenas das 252 famílias novas, a
precisão de comando foi `0,9213`, o recall `0,7593` e a taxa de falso comando
`0,0486`. Ensinar também o `intent_gate` foi falsificado: o recall novo subiu
para `0,8148`, mas os falsos comandos históricos aumentaram para 36; essa
variante foi retirada. A próxima fronteira é ampliar mecanismos realmente
independentes e tornar a CV consciente de `training_heads`, para não cobrar
intent/action/negation de lotes que treinam somente command. Nenhum modelo ativo
foi substituído.

## Expansão por mecanismos v7 e avaliação por owner

A avaliação agora respeita `training_heads`: cada métrica usa somente exemplos
que pertencem ao owner avaliado. A ação é comparada pelo `raw_action`, enquanto
`params` continua representando apenas a conclusão operacional permitida pelo
gate. O diagnóstico também publica intenção lexical, confiança, escopo, limiar
e motivo do veto, sempre como evidência sem autoridade de execução ou promoção.

O lote `expansao_mecanismos_v7` possui 126 exemplos, 78 comandos e 48
não-comandos em 39 grupos. Música e clima ampliam mecanismos positivos; IoT e
navegador recebem hard negatives dirigidos. As três variações `OPEN_URL` e as
três variações musicais elípticas treinam exclusivamente `command`, pois os
erros observados já chegavam com intenção e ação corretas. A auditoria contra
dados anteriores, Frozen e receipts encontrou zero duplicatas ou famílias
compartilhadas.

O gate `intent_gated` ganhou um fallback semântico opcional e calibrado por
intent. Somente `WEATHER=0,60` foi aceito: libera uma proposta quando a intenção
semântica está forte, mas o gate lexical não reconheceu a forma. A arquitetura
sem gate lexical e um fallback global foram rejeitados por aumentarem falsos
comandos. Os limiares finais do candidato são `MUSIC_SEARCH=0,755`,
`OPEN_URL=0,66`, `WEATHER=0,725` e global `0,65`.

Na CV agrupada de 3.904 exemplos, a candidata v18 obteve precisão de comando
`0,9873`, recall `0,9394`, 35 falsos comandos, intenção `0,9371`, ação
`0,9508`, acerto conjunto `0,9498` e negação `0,9925`. Na fatia histórica
comparável, manteve 26 falsos comandos e elevou recall para `0,9487`. No Frozen,
precisão e recall de comando foram `1,0`, com zero falso comando, negação `1,0`
e ação `0,9412`; os seis receipts reais também passaram integralmente.

A sonda telegráfica `acha canção amor` ainda fica em `0,7424`, abaixo do limiar
musical `0,755`. Tentar aproximar os exemplos dessa frase piorou recall e
adicionou falsos comandos, portanto essa variante foi rejeitada. A v18 permanece
como candidata isolada, sem promoção e sem alterar o modelo ativo; essa elipse é
a próxima fronteira contrastiva.

## Contraste telegráfico v8

O lote `contraste_telegraphico_v8` resolve a elipse sem copiar a sonda
reservada. São 18 exemplos balanceados em seis grupos: nove pedidos curtos com
`acha`, `busca` e `encontra`, e nove não-pedidos que contrastam primeira pessoa,
opinião de terceiro e descrição de capacidade musical. Todos treinam
`command`; somente as três variantes de `acha` treinam também `intent_gate`,
pois a CV provou que esse era o primeiro owner em RED. Nenhum exemplo treina
ação, negação, autoridade ou execução.

Os grupos por alvo mantêm pedido e não-pedidos semanticamente próximos na mesma
partição. A auditoria contra todos os lotes anteriores, Frozen e receipts
registrou zero duplicatas exatas, zero quase duplicatas e zero famílias
compartilhadas. Um fallback semântico específico de `MUSIC_SEARCH=0,75` foi
aceito porque a fronteira diagnóstica não continha não-comandos nessa faixa; o
head de comando ainda precisa ultrapassar `0,755`.

Na CV de 3.922 exemplos, a candidata v26 obteve precisão de comando `0,9881`,
recall `0,9409` e 33 falsos comandos. Na fatia histórica, obteve precisão
`0,9902`, recall `0,9498` e 25 falsos comandos, melhorando os três valores da
v18. Intenção (`0,9371`), ação (`0,9508`), acerto conjunto (`0,9498`) e negação
(`0,9925`) foram preservados. O lote v8 passou `18/18` na CV.

No artefato integral, `acha canção amor` passou como
`MUSIC_SEARCH/search` com probabilidade `0,8029`; `acho canção de amor bonita`,
`ela acha canção de amor bonita` e a descrição sobre música em apresentações
permaneceram não-comandos. Frozen manteve precisão e recall de comando `1,0`,
zero falsos comandos e negação `1,0`; os seis receipts reais passaram. A v26
continua não promovida.

### Validação shadow da v26 no runtime

O script `validar_neural_v26_shadow_composicao.py` valida, pelo carregador e
pelas fronteiras reais do orquestrador, o hash exato da v26, sete sondas
contrastivas, a persistência da telemetria e a preservação do modelo ativo. O
ensaio grava somente em pasta temporária e exige `autoriza_execucao=false`,
`apto_treino=false` e `predicao_propria_vira_label=false` em todos os eventos.

Em seguida, `roteiro_neural_v26_shadow_seguro.py` passou pelo runtime completo
com três frases não operacionais. O auditor encontrou três eventos da versão
esperada, todos em `SHADOW`, todos concordantes como não-comandos, sem receipts
e sem efeito executado. A primeira inferência incluiu a carga tardia do modelo
(`7.383,203 ms`); depois disso, a mediana observada foi `18,548 ms`. O hash do
`modelo_ativo.joblib` permaneceu inalterado. A candidata está configurada para
continuar coletando evidência no uso real, ainda sem autoridade e sem promoção.

### Caos completo da v26

O runtime real `roteiro_teste_laylay_caos-20260904-051237-659508` concluiu os
267 turnos. A avaliação semântica marcou 46 de 49 casos como corretos
(`93,88%`); as três falhas foram fallbacks conversacionais para entradas
degradadas e pertencem a outra fronteira, não ao executor neural. Durante o
intervalo, a v26 registrou 405 eventos shadow (267 comparações de turno e 138
de receipt), sempre com `somente_observacao=true`,
`autoriza_execucao=false`, `apto_treino=false` e
`predicao_propria_vira_label=false`. Depois da carga do modelo, a latência foi
`p50=12,707 ms`, `p95=19,772 ms` e máximo de `32,715 ms`.

A comparação contra os casos semanticamente avaliados mostrou precisão de
comando `0,75`, recall `0,25` e taxa de falso comando `0,2308`. O caos executou
32 intenções distintas, enquanto a v26 conhece apenas 13 intenções operacionais
mais `NONE`; além disso, houve 12 turnos multi-intenção e o modelo ainda produz
uma única intenção por entrada completa. Portanto, a primeira fronteira atual é
de cobertura e granularidade, não apenas de limiar. A v26 continua segura em
shadow, mas não está apta para promoção.

A mesma auditoria revelou duas correções históricas falsamente confirmadas por
execuções de turnos posteriores. O runtime agora exige identidade textual entre
a correção e o receipt que a conclui. Os dois registros originais foram
preservados e rejeitados no ledger; nenhum deles pode entrar em treino.

### Base segmentada para a v27

O caos também provou que comparar somente a entrada inteira escondia perdas em
turnos multi-ação. O observador neural agora reutiliza exclusivamente os
segmentos produzidos por `modalidade_turno`: não possui segmentador privado e
continua sem autoridade. A comparação shadow mede cada segmento separadamente,
além da compatibilidade agregada do turno.

Receipts de uma entrada com mais de um segmento neural executável ficam com o
status `receipt_multi_segmento_nao_correlacionado`. Enquanto o runtime não
publicar uma identidade receipt→segmento verificável, eles não contam como
concordância nem divergência de intenção ou ação. Isso impede escolher a
previsão mais conveniente depois de observar o efeito.

`validar_neural_v26_shadow_composicao.py` foi ampliado sem alterar o artefato:
duas frases compostas produziram quatro segmentos comparáveis, quatro
concordâncias por segmento, nenhuma divergência e zero ações executadas. A
frase contrastiva `não abra o opera, mas abaixa o volume` preservou o veto no
primeiro ato e o comando no segundo. O hash do modelo ativo permaneceu igual.

Pelos receipts do caos, a próxima onda de cobertura deve começar por intenções
de leitura ausentes e frequentes: `LIST_WINDOWS` (7 ocorrências), `IOT_STATUS`
(5), `MUSIC_STATUS` (4), `LEARNING_QUERY` (3), `PLAYLIST_LIST` (2),
`PEOPLE_QUERY` (2) e `RESUMIR_PAGINA` (2). Intenções mutáveis como
`CREATE_FILE`, `DELETE_ITEM` e `ORGANIZAR_DESKTOP` permanecem em uma onda
posterior, com gates de segurança próprios. Esta etapa prepara a v27, mas ainda
não cria, treina ou promove um novo modelo.
