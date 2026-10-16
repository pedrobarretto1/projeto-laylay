# Estudo e plano — interpretação natural da Laylay

14/10/2026. Pesquisa documental e inspeção de código; não implementação.

## Conclusão executiva

A opção mais promissora é uma interpretação híbrida, ligada aos contratos
existentes: estrutura linguística como indício, contexto operacional tipado,
recuperação seletiva de exemplos e interpretação semântica estruturada pelo
Qwen atual. Isso é uma hipótese de desenho, não superioridade medida.

Não recomendo instalar uma coleção de bibliotecas nem substituir o runtime
por um framework inteiro. Primeiro comparar braços pequenos e identificar o
componente que realmente reduz erros sem perder comandos legítimos.

spaCy merece avaliação como enriquecimento morfossintático. Embeddings merecem
avaliação como recuperação, não como juiz de autorização. SetFit e modelos
especializados de ferramentas são alternativas futuras que exigem dados e
avaliação próprios; a frente neural continua pausada.

Único arquivo criado nesta etapa de estudo: este estudo/plano. Nenhum pacote instalado,
modelo baixado, teste/benchmark executado, treinamento, configuração, produção
ou sessão da Laylay alterados. Não houve consulta a API de inferência externa.

## 1. Base observada e limites da evidência

Referência Git lida: main, HEAD d850b8c90cc5ce40bd4832e759ed991ba88cd5cc.
A worktree contém mudanças anteriores e paralelas, inclusive arquivos ainda
não rastreados. A leitura não certifica que todos os caminhos estejam ativos
na configuração real, nem substitui uma coleta congelada do runtime.

As habilidades de pesquisa e planejamento foram usadas para cruzar fontes
primárias com os owners atuais. Nenhum resultado de parser ou modelo nas
frases abaixo foi medido nesta etapa. Os exemplos representam contratos
esperados a avaliar, não saídas observadas dessas bibliotecas.

## 2. A tarefa é maior que classificar uma intenção

O entendimento precisa preservar, separadamente:

| Dimensão | Exemplo de distinção necessária |
| --- | --- |
| Ato de fala | Pedir, relatar, perguntar capacidade, citar, sugerir ou corrigir |
| Operação | Atribuir nível, incrementar, abrir, fechar, criar ou consultar |
| Recurso e papel | Arquivo de origem não é pasta de destino; nome citado não é necessariamente alvo |
| Parâmetro | PARA100 é destino; EM10 pode ser variação, não nível final |
| Escopo | Uma negação não cancela automaticamente todas as orações seguintes |
| Referência | “ele”, “essa também”, “coloca em40” dependem de contexto qualificado |
| Relação entre atos | Coordenação independente não é dependência de resultado |
| Admissão | Interpretação proposta não é autorização operacional |
| Resultado | Comando proposto/enviado não é efeito confirmado |

Reconhecer VOLUME não basta se o sistema troca set100 por up10. Reconhecer
dois aplicativos não basta se troca quem deve ser fechado. Uma classificação
correta pode coexistir com um plano operacional errado.

## 3. O que a Laylay já possui

Inventário verificado por leitura, não por ativação dos componentes:

| Peça existente | Responsabilidade e limite |
| --- | --- |
| [Modelo neural](</C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay/mente_laylay/neural/modelo.py:595>) | TF-IDF de palavras/caracteres e classificadores; cabeças de intenção, comando, ação e negação. O resultado dessas cabeças não é um quadro completo de papéis/referentes. |
| [Encoder ONNX](</C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay/mente_laylay/neural/encoder_semantico.py:15>) | Encoder opcional e combinação lexical/semântica. O código já referencia MiniLM multilíngue em experimentos; não tratar esse modelo como descoberta inédita ou presumir que esteja ativo. |
| [Interpretador semântico](</C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay/mente_laylay/cognicao/interpretador_semantico_runtime.py:21>) | Atos, relação contextual, pendência e hipótese operacional; não concede autoridade. |
| [Interpretação por ato](</C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay/mente_laylay/cognicao/contratos_turno.py:537>) | Representação com operação, recurso, alvo, parâmetros, referências, condição e dependências. O próprio contrato distingue vínculo literal de validade semântica. |
| [Saída principal estruturada](</C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay/mente_laylay/cognicao/saida_interpretacao_principal.py:21>) | Schema e fontes textuais vinculadas já existem na worktree. Formato correto não certifica o sentido dos campos. |
| [Admissão por ato](</C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay/mente_laylay/cognicao/escopo_autorizacao.py:86>) | Fonte, turno e identidade operacional têm dono canônico. Não substituir por confiança declarada pelo modelo. |
| [Materialização contextual](</C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay/mente_laylay/cognicao/materializacao_contextual.py:16>) | Relaciona atos, referências e publicações qualificadas; não é autorização nem receipt novo. |
| [Sonda spaCy](</C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay/scripts/analises/sonda_fronteira_pos_portugues.py:422>) | Já há experimento de POS/dependências; não equivale a integração operacional ou semântica aprovada. |

Portanto, a lacuna principal a medir é o vínculo entre esses componentes:
ato → operação/alvo → referência contextual → proposta → admissão. Não há
evidência suficiente para dizer que falta simplesmente instalar um encoder,
um parser ou um schema novo.

### Risco de validação circular

O owner de admissão constrói autorizações sobre segmentos previamente
autorizados e consulta um resolver. Um candidato semanticamente correto pode
continuar barrado por uma limitação lexical anterior. O caso recente de
“reduza para30” expôs exatamente uma diferença entre reconhecimento do valor
e reconhecimento do ato.

Não resolver isso aceitando `autoriza_execucao=True` da IA. O estudo da
integração precisa explicitar qual evidência da fala sustenta a admissão,
sem exigir que o parser antigo seja o gabarito semântico de qualquer rival.
Medir a candidata antes e depois da admissão para localizar essa diferença.

## 4. Bibliotecas, técnicas e modelos avaliados documentalmente

### 4.1 scikit-learn + TF-IDF — manter como referência

TF-IDF representa ocorrências ponderadas; n-gramas acrescentam padrões
locais. Isso é útil para classificação, mas não produz por si só papéis,
dependências entre comandos ou memória de diálogo. A combinação específica
TF-IDF + regressão logística é aprendizado estatístico, não uma rede neural.
[Extração textual no scikit-learn](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction).

Aplicação proposta: baseline rápido e eventual recuperação lexical. Não
reativar o classificador pausado nem iniciar mais rodadas de treino nesta
etapa. Não remover indiscriminadamente palavras como “não”, “para” e “em”.

### 4.2 spaCy — primeiro candidato de enriquecimento

Fornece tokens, lemas, morfologia, classes gramaticais e dependências. Esses
sinais podem ajudar a propor estrutura e reduzir listas de flexões verbais.
As anotações são previsões, não prova de intenção ou de escopo correto.
[Recursos linguísticos](https://spacy.io/usage/linguistic-features).

Os pipelines portugueses `pt_core_news_*` são descritos como modelos de texto
escrito de notícias/mídia. Isso não demonstra desempenho em comandos curtos,
erros de digitação e fala informal. O benefício local precisa ser medido.
[Modelos portugueses](https://spacy.io/models/pt).

Proposta: reaproveitar a sonda existente, publicar indícios com offsets para
a representação compartilhada e comparar. Não transformar o parser em novo
porteiro nem confiar que um arco sintático resolve “ele” entre turnos.

### 4.3 Stanza e UDPipe — alternativas de estrutura, não dois parsers obrigatórios

Stanza oferece lemas, morfologia e dependências, com modelos portugueses
listados em sua avaliação UD. Os números publicados nessa página são de
treebanks e de versões específicas, não de comandos da Laylay.
[Pipeline Stanza](https://stanfordnlp.github.io/stanza/pipeline.html),
[avaliação e modelos portugueses](https://stanfordnlp.github.io/stanza/performance.html).

UDPipe também tem modelos de análise morfossintática em português. Licenças
dos modelos precisam ser conferidas: a distribuição UD2.17 consultada declara
CC BY-NC-SA. Não assumir que licença do código é a dos pesos.
[Modelos UDPipe](https://ufal.mff.cuni.cz/udpipe/2/models).

Prioridade: comparar Stanza se spaCy falhar em relações importantes ou se
oferecer vantagem operacional mensurável. Não executar todos em série por
precaução. Compatibilidade da pilha completa com Windows/Python3.14, consumo
e latência não foram testados aqui.

### 4.4 Sentence Transformers — recuperar exemplos e capacidades

O MiniLM multilíngue já referenciado no projeto é uma opção de comparação,
não um novo substituto do sistema. A documentação inclui português entre
os idiomas da família multilíngue. Similaridade pode recuperar exemplos
relacionados, mas não determina se a frase é pedido, negação ou relato.
[Modelos multilíngues](https://sbert.net/docs/sentence_transformer/pretrained_models.html).

Uso proposto: recuperar poucos exemplos contrastivos e descrições do catálogo
vivo para o interpretador. A recuperação não escolhe executor, não resolve
sozinha alvo ambíguo e não cria autorização. “Liga a luz” e “não liga a luz”
devem fazer parte dos contrastes, não ser aceitos apenas por proximidade.

ONNX/quantização são opções documentadas de implantação, mas não garantem
velocidade ou qualidade no hardware de Pedro. Reusar o loader existente
quando compatível; validar tokenizer, pooling, entradas e hashes.
[Inferência e ONNX](https://sbert.net/docs/sentence_transformer/usage/efficiency.html).

### 4.5 multilingual-e5-small — alternativa de recuperação, não prioridade inicial

O model card inclui português, embeddings de384 dimensões e instruções
específicas de prefixo `query:`/`passage:`. Isso exige comparar o protocolo
correto, não trocar somente o nome do arquivo no loader MiniLM. A ficha
limita textos longos a512 tokens.
[Ficha dos autores](https://huggingface.co/intfloat/multilingual-e5-small).

Avaliar só se a recuperação existente mostrar uma lacuna mensurável.
Multilíngue não é evidência de superioridade em português informal.

### 4.6 SetFit — opção futura de aprendizagem supervisionada

Combina ajuste contrastivo de Sentence Transformer com classificador. A
documentação diferencia similaridade geral e agrupamento adequado à tarefa;
eles não são automaticamente equivalentes. Os resultados com poucos exemplos
publicados são de tarefas determinadas, não um mínimo garantido para Laylay.
[Conceito de SetFit](https://huggingface.co/docs/setfit/main/en/conceptual_guides/setfit),
[documentação estável](https://huggingface.co/docs/setfit/v1.1.3/en/index).

Pode ser útil quando retomarmos aprendizagem com rótulos confiáveis, negativos
difíceis e avaliação independente. Não resolve sozinho referentes, dependências
ou autorização; não iniciar agora enquanto a frente neural estiver pausada.

### 4.7 GLiNER multilíngue — candidato de extração de entidades

Permite propor spans para categorias fornecidas na entrada, além de um conjunto
fixo tradicional de entidades. A ficha de `gliner_multi-v2.1` declara modelo
multilíngue; não fornece ali prova suficiente de qualidade nos comandos PT
da Laylay.
[Ficha do GLiNER](https://huggingface.co/urchade/gliner_multi-v2.1).

Pode ajudar a localizar nomes de playlist, aplicativo ou dispositivo. Não
distingue automaticamente origem/destino nem prova que o nome existe ou é o
alvo operacional. Avaliar somente se a extração de spans for a primeira RED;
não é necessário acrescentá-lo ao primeiro experimento.

### 4.8 Rasa/DIET — inspiração arquitetural, não migração recomendada

DIET combina classificação de intenção e extração de entidades. A documentação
também alerta para duplicações quando extratores sobrepostos disputam entidades.
[Componentes do Rasa OSS, documentação legada](https://legacy-docs-oss.rasa.com/docs/rasa/components/#dietclassifier).

O princípio de papéis/grupos importa: identificar dois lugares não distingue
origem e destino. Essa mesma diferença existe em arquivos e playlists.
[Papéis e grupos de entidades](https://rasa.com/blog/introducing-entity-roles-and-groups).

Slots tipados separam valores de contexto da extração da frase atual.
[Slots](https://rasa.com/docs/reference/primitives/slots/).

A Laylay já tem estado, continuidade, admissão e executores. Migrar todo esse
trabalho para outro framework acrescentaria uma segunda arquitetura. Aproveitar
os princípios e medir o componente faltante, não importar o framework inteiro.

### 4.9 Qwen atual + schema + contexto seletivo — principal braço semântico

Ollama documenta saída condicionada a JSON Schema. Isso reduz problemas de
formato, não demonstra que o alvo, o escopo ou o sentido de um valor estejam
corretos. Essa distinção também está escrita nos contratos da Laylay.
[Saída estruturada no Ollama](https://docs.ollama.com/capabilities/structured-outputs).

Proposta: comparar a emissão por ato existente com contexto compacto e fontes
necessárias; poucas demonstrações contrastivas podem ser recuperadas em uma
ablação separada. Preservar o modelo de conversa atual e o limite de chamadas.
Não criar “spaCy→modeloA→modeloB→fallback” para toda entrada nem duplicar uma
interpretação que a chamada principal já poderia transportar.

### 4.10 FunctionGemma — especializado, mas não atalho pronto

É uma base pequena para chamadas de funções e ajuste a tarefas específicas.
A documentação recomenda fine-tuning para o caso de uso e explicita que a
avaliação apresentada usa prompts em inglês. Não é um modelo de diálogo geral.
[Ficha oficial](https://ai.google.dev/gemma/docs/functiongemma/model_card).

Pode entrar num estudo futuro de um roteador especializado, com corpus PT e
comparação local. Não é justificativa para trocar o Qwen, retomar treinamento
ou prometer compreensão melhor sem prova.

### 4.11 Normalizadores especializados — ganhos pequenos e delimitados

- `text2num`: converte números escritos, com suporte declarado a português
  brasileiro/europeu. Aplicar apenas a um campo numérico já identificado;
  “cem” num título não deve alterar o nome original. A tabela de wheels do
  README consultado não certifica a pilha Python3.14 aqui.
  [Projeto oficial](https://github.com/Allo-Media/text2num).
- RapidFuzz: comparação aproximada de nomes. Usar para candidatos de um
  inventário conhecido, sem reescrever a fala toda, escolher um arquivo para
  apagar ou eliminar ambiguidade por similaridade.
  [Documentação oficial](https://rapidfuzz.github.io/RapidFuzz/).
- dateparser: possível auxiliar para um slot temporal identificado; a lista
  documenta português. Data extraída não significa lembrete autorizado nem
  resolve fuso/base temporal automaticamente por nós.
  [Idiomas e localidades](https://dateparser.readthedocs.io/en/latest/supported_locales.html).

Inventariar normalizadores do domínio antes de adicionar qualquer substituto.

## 5. Arquitetura proposta: enriquecer o contrato existente

Fluxo conceitual, não nova implementação nem cadeia obrigatória de modelos:

```text
fala original preservada
  → candidatos de interpretação por ato, vinculados à fonte
  → referentes e parâmetros resolvidos pelos owners canônicos
  → admissão explícita do pedido e validação do domínio
  → execução
  → receipt e estado observado
  → uma resposta coerente com os resultados
```

Regras locais, parser e Qwen são fontes alternativas/complementares de
candidatos. Somente o owner canônico decide admissão. Não usar voto majoritário
como licença para um efeito, nem promover confiança numérica a permissão.

O quadro deve preservar operação, tipo de recurso, literal e papel do alvo,
valor/unidade, modo absoluto/relativo, negação, condição, referência e
dependência. Campos ausentes/ambíguos ficam explícitos; não preenchidos com o
último nome que apareceu na conversa. Isso deve adaptar o contrato atual,
não inaugurar um segundo dicionário de estado.

Para “aumenta para100”, após volume70 confirmado, a leitura esperada é pedido
de atribuição de nível100, com parâmetro herdado de referência operacional
qualificada. Sem esse antecedente, a mesma frase não contém o nome do parâmetro.
O receipt ajuda a identificar referente; a autorização vem do pedido atual.

Para “abre Firefox e depois fecha ele”, a relação é proposta antes do efeito,
mas o segundo ato não deve fechar outro aplicativo se a abertura falhar. O
resultado do primeiro precisa ser validado pelo executor antes da dependência.

Uma consulta a inventário existente é diferente de criação: “cria a playlist
viagem” pode fornecer nome novo válido. Não exigir ID existente para impedir
uma criação autorizada nem usar fuzzy lookup como criação implícita.

## 6. Como avaliar sem repetir o ciclo de remendos

### Conjuntos separados

As250 frases já usadas e os incidentes corrigidos são regressão conhecida,
não conjunto inédito. Preservá-los. Criar outra reserva por famílias de
expressão/cenários, sem paráfrases quase idênticas entre desenvolvimento e
avaliação. Separação por grupos é uma técnica documentada contra esse tipo
de vazamento; o agrupamento precisa representar famílias reais.
[Validação por grupos](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data).

Rótulos esperados devem ser independentes do parser atual e das candidatas.
Não chamar anotação feita pela IA de revisão humana. Ambiguidades legítimas
precisam de rótulo próprio e, quando necessário, esclarecimento de Pedro.

### Casos contrastivos obrigatórios

- PARA100 × EM10; números por extenso; unidade incompatível.
- Pedido direto × relato passado × pergunta de capacidade × hipótese.
- “Não liga a luz, só abre a calculadora”: escopos independentes.
- “Não liga a luz nem o ventilador”: negação coordenada.
- Dois alvos com um verbo; dois verbos com alvos diferentes.
- “Abre Firefox e depois fecha ele”: dependência de resultado.
- Títulos como “Não Me Deixe Só” e “Sobe o Volume”: conteúdo não é comando.
- “Coloca em40” com receipt confirmado, falho, vencido, outro domínio e dois
  referentes compatíveis. Nenhum contexto precisa continuar sendo uma opção.
- Correção de nome/valor, troca de assunto e confirmação de pendência ativa.
- “Abri a calculadora do windowns”: manter a intenção previamente esclarecida
  por Pedro sem generalizar qualquer pretérito como imperativo.
- Erros de digitação, falta de pontuação e transcrição; preservar texto bruto.
- Conectores de condição/tempo; comandos atuais não viram agendamento implícito.
- Perguntas e conversa que usam o mesmo vocabulário de uma habilidade.

CLINC150 é referência de desenho para fora-de-escopo, não benchmark suficiente
para nós: os próprios autores indicam inglês e uma intenção por consulta.
[Dataset dos autores](https://github.com/clinc/oos-eval).

### Braços e ablações

1. A: sistema atual, baseline instalado.
2. B: A enriquecido por sinais spaCy, sem nova autoridade.
3. C: interpretação por ato do Qwen atual, schema/contexto seletivo, sem
   alterar simultaneamente modelo, sampling, executor ou política.
4. C+recuperação: mesma composição com exemplos contrastivos recuperados;
   primeiro recursos existentes, sem treinamento e sem ativar classificador
   neural. Separar benefício da recuperação do benefício do prompt/schema.
5. Stanza/E5/GLiNER só se uma primeira fronteira RED justificar o custo.

Não rodar todos os componentes juntos e atribuir o resultado a uma biblioteca.
Não usar a decisão lexical antiga como gabarito obrigatório da nova semântica.
Registrar claramente onde regras, proposta, vínculo e admissão divergem.

### Métricas da cadeia

Medir separadamente ato, operação, alvo/papel, valor/unidade, negação, condição,
referente e dependência; depois a correção conjunta do plano inteiro.
Contar comandos legítimos perdidos, ações indevidas, alvo errado e esclarecimentos
úteis/inúteis. Menos erros por recusar quase tudo não é ganho suficiente.

Registrar falha técnica de geração separada de erro semântico, sem apagá-la
do custo operacional. Medir latência fria/quente, p50/p95, número de chamadas,
tokens/contexto e consumo de memória. Não usar números de outro hardware
como estimativa do PC de Pedro.

Scores de similaridade/confiança precisam de avaliação e, quando aplicável,
calibração com dados separados. Não fixar0,8/0,9 por conveniência nem tratar
calibração como garantia para qualquer entrada desconhecida.
[Calibração no scikit-learn](https://scikit-learn.org/stable/modules/calibration.html).

### Prova e critério de adoção

Primeiro diagnóstico sem efeitos na composição existente. O runner atual
retira prioridade/prefluxo explicitamente: não prova sozinho o desktop.
Usar as sondas já existentes para a fronteira instalada correspondente, sem
substituir o owner avaliado por mocks ou inventar receipts no runner para
obter pontuação maior. Depois, somente ações reversíveis e autorizadas com
receipts reais podem provar efeito.

Adotar apenas se melhorar famílias inéditas e a cobertura de pedidos legítimos
sem regressão relevante de segurança/alvo/escopo. Zero erro observado no painel
não é garantia universal. Quando a melhoria for só formato, classificação ou
latência, reportar exatamente isso.

## 7. Próxima ação recomendada, após autorização de execução

Prioridade: contrato e avaliação da fronteira semântica → admissão. Reaproveitar
a IR, instrumentação, catálogo, estado e contexto já presentes, definir o gold
independente e comparar A/B/C em um recorte contrastivo antes de ampliar.

Arquivos a inspecionar na implementação futura: contratos_turno,
leitura_semantica_turno, saida_interpretacao_principal, escopo_autorizacao,
materializacao_contextual, interpretacao_intencao e composição real do turno.
Isso não autoriza modificar todos eles. O primeiro patch deve ter um owner
responsável e um RED canônico, identificado pelo experimento.

spaCy é o primeiro candidato externo de enriquecimento; recuperação com o
encoder existente é uma ablação; SetFit/FunctionGemma ficam para estudo futuro
de treinamento. Preservar o Qwen atual, voz, estado do usuário e pausa da rede.
Não há porcentagem de ganho ou prazo de conclusão medidos nesta etapa.

## 8. Ensaio aprovado em 14/10 — escopo de implementação

Pedro aprovou iniciar a comparação sem efeitos. Reutilizar
`scripts/analises/sonda_ordem_interpretacao.py`, preservando o painel histórico.
Receber corpus externo e comparar resolução instalada singular, Qwen por ato
com schema canônico sem fontes pré-fixadas e Qwen com os mesmos dados mais
indícios POS. O braço antigo de antecipação continua disponível separadamente.

Criar um avaliador instrumental e um corpus de desenvolvimento contrastivo;
anotação IA explícita, sem chamá-lo de holdout. Separar significado, proposta,
vínculo literal e admissão. Gold, família e expectativas nunca entram no modelo.
Contexto sintético qualificado deve ser reiniciado por braço e declarado como
fixture, não efeito ocorrido. Nenhum executor, treino ou promoção participa.

Verificação: testes do avaliador/projeção e guardas antes do instrumento;
regressivos das sondas existentes; coleta instalada sem modelo primeiro;
depois geração local selecionada, em pasta nova, journal incremental,
hashes antes/depois e trava de sessão. Parser externo em ambiente isolado,
sem alterar dependências principais. Latência do parser deve ser registrada
separadamente e não confundida com consulta de tokens pré-computados.

Produção e configuração permanecem intocadas. Um resultado semântico bom não
encerra integração, admissão, execução ou comportamento desktop.

### Ensaio inicial concluído

Sonda existente ampliada e corpusdev36/nove famílias coletado com o Qwen
selecionado `qwen3:4b-instruct`. 163 testes focados,108 observações instaladas,
518 fontes/entradas estáveis. C35/36 e C+POS31/36 retornos tipificados aceitos;
isso não mede acerto semântico. Nenhuma tentativa de executor/dispatcher
detectada. spaCy3.8.16/pt_core_news_sm3.8.0 isolados em ambiente3.11 de
resultados_testes, não nas dependências operacionais.

Não adotar POS em produção a partir desta amostra: houve classificação
nominal de imperativos, propostas que o porteiro negou, perda de atos mistos
e parâmetros não canônicos. Próxima fronteira: coerência ato/operação/valor
e proposta tipada, sem retomada da rede. A singular versus C multiato não é
ranking justo da cadeia inteira; gold parcial não é equivalência semântica;
fixtures sem origem executor não comprovam falha do contexto vivo.

Relatório e evidências: `resultados_testes/interpretacao_natural_20261014/RELATORIO.md`.
