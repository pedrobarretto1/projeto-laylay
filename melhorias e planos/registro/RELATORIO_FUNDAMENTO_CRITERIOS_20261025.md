# Base dos critérios autorais — 25/10/2026

## Pedido, base e unidade causal

Pedro autorizou estudar como fundamentar critérios dos gostos sem usar proposta
da IA como prova, corrigir o contrato comum e validar composição instalada sem
voz e com ações simuladas. Continuação da raiz de opinião autoral; não renomear
F1/C5/C7/AUT nem incorporar clipboard, prazo ou explicação didática livre nesta
correção.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. `resultados_testes/fundamento_criterios_20261025/baseline.json`
registra status e hashes de 530 fontes. `fontes_antes/` contém os owners antes
deste candidato; o diff do HEAD inclui outras investigações e não representa
este patch. Nenhum commit, shutdown, mudança de modelo, voz ou configuração.

## Primeira fronteira demonstrada

O contrato anterior conservava a preferência e o código de critério na emissão
original. O baseline instalado/Qwen em seis turnos confirmou ambos presentes;
HTTP200 e publicação funcionavam. Mas o schema só permitia declarar o rótulo
do critério, sem indicar uma descrição considerada como base. Mesmo uma fonte
individual válida no contexto não chegava ao pacote fechado de opinião. A
captura também descartava qualquer referência de fundamento adicional.

`contrato_red.xml` reproduz as duas falhas: falta do campo no schema e perda da
referência de base na captura. Não era perda do histórico da preferência nem
falha geral do serviço. Pedir que a IA inventasse uma justificativa posterior
não corrigiria essa fronteira de autoria e não provaria causa histórica.

Contraprovas no revisor existente demonstraram que ele já confere citação
integral da fonte individual e recusa URL não lida ou evidência vencida. Essa
capacidade foi extraída e reutilizada, não substituída por outro julgador da IA.
Uma descrição do objeto pode apoiar uma premissa atribuída; não comprova a
adequação de um critério subjetivo nem a causa psicológica da preferência.

## Contrato corrigido e responsáveis

1. **Leitura e proveniência:** os coletores existentes continuam responsáveis
   pelo conteúdo, origem e validade da fundamentação factual. Não há pesquisa
   automática ao perguntar sobre gostos. O orquestrador preserva apenas a
   leitura factual do turno anterior para consumo contextual no turno atual,
   mantendo seu timestamp e sua validade, sem criar depósito durável paralelo.
2. **Conferência textual:** `revisao_suporte_autoria.conferir_apoio_fonte` é o
   mesmo owner compartilhado usado na revisão das proposições. Verifica fonte
   individual não ambígua, origem admissível e apoio literal integral ou a
   paráfrase estrutural previamente contratada. Neste recorte de critérios,
   somente a descrição integral é inventariada, preservando ressalvas e alvo.
3. **Inventário na autoria:** `opiniao_autoral` aceita uma descrição apenas
   quando o alvo literal corresponde a uma das opções e o texto predica esse
   alvo pelo leitor existente da pesquisa. Resumo agregado, fonte interna,
   fonte vencida, origem do modelo, ambiguidade e outra entidade não bastam.
   O snapshot contém URL, trecho integral, alvo, hash de URL+conteúdo e expiração.
4. **Proposta:** quando há bases elegíveis, o schema oferece seus IDs e
   `sem_fundamento`. A autora pode indicar qual descrição considerou ou recusar
   todas. O protocolo confronta o alvo com a opção efetivamente escolhida e
   impede indicar fundamento quando nenhum critério foi declarado. A base não
   entra na lista de fontes da frase subjetiva como se comprovasse o gosto.
5. **Captura e admissão:** `suporte_autoria` conserva a referência como
   `fundamento_criterio_proposto`. O host só a admite na mesma emissão,
   consulta, turno e fala revisada, contra o inventário nativo vigente. Uma
   reescrita precisa declarar sua própria referência; mesclas não herdam a de
   uma parte. A revisão aceita a realização integral do owner subjetivo, sem
   estender essa cobertura a causas ou características acrescentadas.
6. **Publicação e continuidade:** `criterio_autoral` anexa o snapshot à mesma
   declaração efetivamente entregue, reutilizando o callback e o registro
   canônico anteriores. Origem, timestamp e TTL não são renovados no porquê ou
   esclarecimento. A persistência já existente projeta o anexo em descrição
   JSON, sem reconstruir credencial nativa ao carregar.
7. **Explicação:** recupera a posição, o critério registrado e, se ainda
   vigente, a descrição considerada com atribuição explícita de fonte. A
   relação entre descrição e critério continua sendo avaliação declarada,
   com `adequacao_avaliativa_comprovada=False`, `prova_factual=False`,
   `prova_causal=False` e `autoriza_execucao=False`. Não se afirma experiência,
   propriedade nova ou causa psicológica. Sem base admitida, a realização
   informa que não há base factual conferida para essa relação.

Esses contratos são compartilhados. Música, software e bebidas aparecem como
instâncias de uma mesma avaliação declarada; não há regra especial para indie,
Linux, chá ou para a frase histórica do usuário. Não foi criada habilidade ou
permissão operacional nova, nem habilitado modo amplo de pesquisa/autonomia.

## REDs intermediários e revisão independente

O primeiro candidato perdeu o inventário polar por contar o mesmo alvo duas
vezes nas opções positiva e negativa. O teste inicial permaneceu RED pelo motivo
correto; deduplicar o alvo preservou as duas posições legítimas da autoria.

`revisao_red.xml` mostrou três REDs em música/software/bebidas: a presença de
fontes fazia a revisão tratar a própria preferência como afirmação factual e
substituí-la por limite genérico. O revisor agora consome a decisão integral do
owner de opinião, assim como as outras guardas já faziam. A isenção não é por
primeira pessoa ou tema; o texto inteiro precisa pertencer ao ato conferido.

O controle adversarial inicial usou um marcador inventado `fonte=proposta_llm`.
Ele foi substituído por metadados de origem efetivamente usados pelo sistema,
`llm` e `llm_principal`, para não basear um patch em rótulo de fixture. Três
REDs em `proveniencia_red.xml` confirmaram que URL/confiança/contexto factual
podiam receber precedência sobre essa origem explícita. O owner comum
`proveniencia_informacao` agora mantém a emissão como proposta sem poderes
factuais ou pessoais. Isso protege também outros consumidores do mesmo contrato;
não é um veto local de gosto nem uma lista de frases do modelo.

A revisão independente da skill `requesting-code-review` encontrou um bloqueador
do candidato: fundamento que vencia entre admissão e callback impedia registrar
a entrega da preferência. `entrega_ttl_red.xml` reproduziu primeiro canal tardio
e confirmação em segundo canal. Integridade e vigência foram separadas: a
publicação conserva o que foi entregue, mas a explicação não reutiliza fonte
vencida. Não houve renovação artificial do prazo. O revisor repetiu seis
controles focados e não encontrou bloqueador remanescente nesse recorte.

## Validação instalada e alcance das evidências

`instalada_green.xml`: 23 casos novos aprovados. A factory instalada percorre
leitura de pesquisa, fundamentação, escolha, captura, revisão, callback,
persistência e continuidade. Só as folhas externas HTTP/modelo/efeitos são
controladas nesse regressivo. A opinião e seu porquê não fazem novas buscas.

`foco_entrega.xml`: 354 aprovados e quatro ignorados. Inclui contratos anteriores
de critério, opinião, fontes, paráfrases, proveniência e explicação de gostos.
`regressao.xml` e `comparacao_regressao.json` registram a ampla relevante e a
comparação por identidade das falhas anteriores. Não chamar seleção ampla de
suíte global: preservou-se a seleção compatível com testes sem efeitos reais.

Ampla em **111 módulos distintos**: **2.830 aprovados**, nove falhas,44 erros,
14 ignorados,um desmarcado e30 subtestes aprovados. A auditoria comparou os IDs:
as nove falhas e os44 erros são exatamente os mesmos da entrega anterior.
Permanecem o comando natural antigo da Calculadora, oito expectativas antigas
de pacote/tokens e44 erros de fixture por serialização de
`PerspectivaEnunciador`. Nenhum foi ocultado, reclassificado como GREEN ou
atribuído a este candidato. A lista individual completa está na comparação.

Qwen real, configuração atual, composition root `laylay.py`, persistência isolada:

- `candidato_fundamentado/`: 12 turnos,12 HTTP200,12 publicações e12 gravações
  relidas. A folha HTTP da pesquisa fornece páginas **sintéticas**, marcadas no
  conteúdo como cenário simulado; busca/leitura/fundamentação são reais. Não
  apresentar esses trechos como pesquisa de fatos reais sobre gêneros ou produtos.
  Qwen declarou base em indie e chá, e `sem_fundamento` em Linux. A explicação
  respeitou essas três decisões; repetição e esclarecimento conservaram a origem.
  A premissa divergente sobre rock não criou novo gosto.
- As três perguntas de leitura (`me explica ...`) obtiveram fontes, mas o modelo
  não produziu explicação com apoio integral conferível. Foram publicadas as
  limitações corretas. **Não** contar esses três turnos como explicação didática
  resolvida nem ampliar este patch para corrigir essa outra fronteira.
- `entrega_sem_base/`: seis turnos e seis HTTP200/publicações/persistências.
  Sem fonte disponível, nenhum fundamento foi inventado; a explicação informa
  o limite da avaliação. Qwen pôde escolher café em vez de chá, sem gênero ou
  preferência fixados pelo host.
- `entrega_fumaca/`: três turnos separados de segurança. Um APP_OPEN passa pelo
  adaptador de resultado real com executor simulado, `executou=False` e
  `confirmado=False`. Nenhuma aplicação foi aberta. Não contar o controle de
  ação como explicação de gosto.

As coletas mantêm as 530 fontes estáveis durante cada execução, sem voz e sem
efeito externo permitido. `auditar.py` compara HTTP original, schema, seleção
proposta, fonte anterior, hash, anexo publicado e registro gravado/relido, sem
tomar a própria resposta da IA como certificação da sua base. Artefatos e
transcrições ficam em `resultados_testes/fundamento_criterios_20261025/`.
`entrega.json` sela hashes finais, contagens, escopo das coletas e seus limites.

## Escopo de produção e próxima fronteira

Produção alterada nesta investigação: `criterio_autoral.py`, `opiniao_autoral.py`,
`suporte_autoria.py`, `revisao_suporte_autoria.py`, `proveniencia_informacao.py`
e `orquestrador_turno_runtime.py`. A publicação, armazenamento, executores,
modelo e voz existentes foram reutilizados. Nenhum commit criado.

Está demonstrado o vínculo auditável entre premissa atribuída e avaliação
declarada, com limite explícito quando falta base. Não está demonstrada a
adequação subjetiva do critério ao objeto, verdade externa universal, experiência
vivenciada ou causa psicológica. Persistência durável de gostos e reposição de
fontes após vários turnos não foram introduzidas. A próxima fronteira é conferir
o alcance da relação avaliativa e tornar explicações mais informativas somente
na medida em que seu apoio puder ser demonstrado. Não declarar compreensão
geral encerrada com base nesses resultados.
