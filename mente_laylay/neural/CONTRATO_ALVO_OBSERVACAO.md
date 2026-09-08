# Contrato de alvo e observação — estudo do item 3

Estado: contrato completo ainda proposto; candidato C1 de correspondência textual
aplicado em produção, conforme atualização ao final. Não é aprovação de dataset ou modelo.
Base: `main`, HEAD `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, worktree suja
preservada. Data: 2026-09-05. Autoria: Astra, revisão assistida por IA.

## O que a composição atual faz

`laylay.py` injeta `AmbienteNavegacaoRuntime.resolver_alvo` e
`CatalogoAplicativosRuntime.validar` no caminho de conversa. A fachada usa
`listar_programas_abertos`, que retorna títulos de janelas apresentáveis, e a
lista de abas. A consulta direcionada não usa o retrato estruturado completo
de processos em segundo plano. A presença de processo, janela e conteúdo não
pode ser tratada como uma única evidência.

O resolvedor em `percepcao/janelas_sistema.py` aceita tanto alvo contido no título
quanto título contido no alvo. A segunda direção permite que o título `Excel`
satisfaça `planilha do Excel`. Não devolve identidade de documento nem preserva
o título da janela que sustentou `programa_aberto` (o campo `titulo` refere-se
à aba). O catálogo aceita qualquer retrato com `programa_aberto=True`;
`pre_fluxo_contextual.processar_consulta_sistema_local` publica então um receipt
confirmado para a expressão inteira e produz uma fala sobre ela.

Primeira fronteira incorreta reproduzida: **candidato textual vira prova de alvo**
no resolvedor. Catálogo, receipt e fala propagam essa inferência. Não é falha de
treino, nem foi causada por Qwen, vocabulário insuficiente ou ausência de callback.

## Evidência e limites

Diagnóstico original migrado para `tests/test_resolucao_alvo_observado.py`.
As mesmas classes/funções usadas em produção são conectadas, mas os títulos de
entrada e as saídas de fala/receipt são controlados. Não importa nem inicializa
`laylay.py`, não abre programas, não consulta desktop, não acessa o navegador.
Isso **não é prova de sessão completa**; a ligação de produção foi inspecionada
separadamente em `laylay.py`, incluindo o registro dos serviços da fachada.

- RED no resolvedor: Excel → planilha; Word → documento; VLC → vídeo.
- RED no caminho integrado: as três consultas publicam `confirmado=True` sem
  observar o conteúdo correspondente.
- Controles: aplicativos explícitos funcionam; título sem relação não confirma;
  qualificadores legítimos `janela do <app>` continuam funcionando.

Os controles falsificam duas explicações concorrentes: falha geral do catálogo
e qualquer título aberto causando confirmação. O mecanismo exige a sobreposição
textual indevida. Os testes não provam que todo documento consultado falha.

Não remover apenas a comparação inversa: ela também sustenta qualificadores
legítimos. A comparação na outra direção também pode confundir um nome citado
num título de navegador com o aplicativo correspondente. Uma substituição precisa
de resolução por identidade e tipo, não de mais listas locais de palavras.

## Contrato proposto

**O resultado deve provar a propriedade pedida sobre o alvo resolvido, no mesmo
nível de detalhe. Um candidato textual não é uma observação confirmada.**

| Pedido | Identificação necessária | Evidência que pode sustentar a resposta |
| --- | --- | --- |
| Aplicativo em execução | App canônico | Observação de processo do app; distinguir processos auxiliares e falha de leitura |
| Janela aberta/visível/em foco | Janela ou conjunto explicitamente pedido | Identificador da janela, app associado e propriedade observada; não apenas processo existente |
| Documento/planilha/vídeo aberto | Conteúdo identificado e relação com app/janela/aba | Observação do conteúdo no escopo correto; título compatível é pista, não prova universal |
| Aba aberta | Aba identificada no navegador conectado | Registro de aba e identidade/URL; não inferir de navegador aberto |
| Área de trabalho | Superfície e propriedade pedida | Observação própria; não rotular automaticamente como app em execução |
| Referência genérica (`ele`, `a janela do editor`) | Referente compartilhado válido ou esclarecimento | Resolver atual com proveniência/validade; reobservar o estado após resolver |

Separar estados `observado_presente`, `observado_ausente`, `indeterminado` e
`falha_observacao`. Ausência exige leitura bem-sucedida com cobertura adequada.
`False` não pode representar ao mesmo tempo não encontrado, falha ou alvo mal
resolvido. No RED legado, `programa_aberto=False` significa apenas não confirmar
a expressão solicitada; não prova que seu conteúdo esteja fechado.

O receipt deve carregar o alvo efetivamente resolvido, tipo, propriedade,
fonte, instante e evidência que sustentam seu status. Emitir receipt antes da
fala continua necessário, mas **a mera presença de receipt não valida seu conteúdo**.
Se só houver evidência do aplicativo, comunicar esse limite ou esclarecer o
conteúdo pedido, sem consumir o turno silenciosamente e sem anunciar confirmação
do conteúdo. Não usar LLM para preencher a evidência ausente.

## Entrada contextual para avaliação futura

Os campos abaixo são especificação, **não schema já suportado pela rede**:

| Informação | Fonte/dono | Uso permitido |
| --- | --- | --- |
| Texto original + identidade do turno | Turno canônico | Interpretar o pedido, preservar negação e correção |
| Tipo, identidade e escopo do alvo | Cognição/resolução canônica | Preservar a diferença app/janela/conteúdo; não reparsear no executor |
| Referente, origem, turno e validade | Memória compartilhada/continuidade | Resolver referência; nunca autorizar efeito pelo contexto |
| Ato pragmático quando necessário | Intérprete canônico com contexto conversacional | Distinguir capacidade de pedido indireto sem rotular ausência como negativo |
| Disponibilidade do observador | Catálogo vivo de capacidades e integração | Escolher a fonte realmente disponível, sem inventar acesso |
| Estado observado + instante + cobertura | Percepção/integração responsável | Fundamentar a resposta, não substituir o texto do pedido nem vazar o gabarito de intenção |

Para avaliar intenção, fornecer somente informações disponíveis antes da decisão.
Observações posteriores pertencem à avaliação de resultado, não às features de
intenção. Para avaliar estado, separar resolução e observação em etapas e testar
alvo ausente, ambíguo, expirado, recusa e falha de leitura. Variantes do mesmo
cenário/referente devem permanecer no mesmo grupo de validação. Sem fit nesta fase.

O owner atual do referente de app é `contexto_compartilhado` e o leitor existente
é `pre_fluxo_contextual`. A memória atual tem `ultimo_app_janela`; não presumir
que ela já fornece todo o contrato de validade/tipo descrito acima. Não criar
uma memória privada no módulo neural nem um segundo resolvedor no executor.

## Decisão sobre os dados e próximo candidato

Manter os 19 casos da revisão v2 separados. Não aprovar os demais 686 enquanto
a granularidade estiver aberta: 84/107 (planilha), 89/113 (desktop), 91/115
(editor genérico) e 696/700 (consultas de documentos) precisam da mesma política
de alvo, não de rótulos opostos baseados só no nome de um aplicativo.

Próximo candidato de produção: evoluir a fronteira canônica de resolução para
preservar tipo/identidade/evidência, adaptar seus consumidores causais e validar
qualificadores, homônimos, documentos, abas e falhas de observação. Não alterar
catálogo ou fala isoladamente para compensar o erro do resolvedor. Inventariar
consumidores antes do patch, pois o mesmo resolvedor participa de ações de janelas
e validação de efeitos. Migrar o RED para a suíte de regressão ao aplicar o candidato.

Achado separado: a fachada converte exceções de listagem em listas vazias e o
pré-fluxo pode apresentá-las como ausência confirmada. Provado por leitura de
código, **não reproduzido neste diagnóstico**; requer RED próprio antes de correção.

Na etapa original de diagnóstico não houve alteração em produção. Dataset,
modelo, configuração e permissões seguem preservados após o C1 abaixo.

## C1 aplicado — correspondência direcional, 2026-09-05

Os seis REDs originais foram reconfirmados antes do patch. A ampliação verificou
limites de palavra, alvos compostos, aliases, qualificadores e auxiliares Steam.
O caso de `janela do editor` observado como `Editor` não estabelece sozinho um
falso positivo: a observação realmente contém o nome pedido após qualificação.
Por isso o teste de especificidade usa `janela do editor de vídeo` contra `Editor`,
em que há informação adicional que não foi observada; não exige inventar o tipo
de uma janela com título literal. Não foi introduzida exceção para esse nome.

Produção alterada:

- `planejamento_janelas.py`: owner compartilhado `variantes_alvo_aplicativo`,
  extraído da regra existente do catálogo; reaplica aliases após qualificação.
- `catalogo_aplicativos.py`: delega à mesma regra, sem parser privado duplicado.
- `janelas_sistema.py`: para programas exige a variante inteira no título,
  com limites de palavra; elimina título-curto contido no alvo-composto. O filtro
  de auxiliares usa as mesmas variantes, preservando SteamService/WebHelper.

O diagnóstico foi migrado (sem perder os casos originais) para a suíte normal.
Resultado: **425 testes e 8 subtestes passaram**. Uma regressão intermediária do
candidato com `cliente Steam`/`janela do Steam` foi reproduzida e corrigida na
mesma fronteira, mantendo os testes. Não há xfail escondendo os REDs originais.

Prova adicional com observadores reais de Windows: fachada de produção reconheceu
o VS Code aberto, tratou a consulta explícita e não publicou receipt para
`documento do Visual Studio Code`. Foco antes/depois igual, zero ações. Voz e
persistência foram capturadas em memória. Isso valida leitura real e integração,
**não sessão completa da Laylay nem correção de todo fallback posterior**.

Limites: C1 não implementa identidades de documento/HWND/PID, nem o schema completo
acima. Menção de app dentro de título, homônimos, semântica de ausência/falha,
processos sem janela e correspondência de abas exigem investigações próprias.
A regra de abas foi preservada. O pré-fluxo agora não consome as consultas de
conteúdo sem correspondência, mas a resposta do restante do pipeline não foi
validada em sessão completa. Não apresentar o C1 como solução total de observação.

Modelo ativo e fonte v2 mantiveram seus hashes anteriores. Nenhum treino, promoção,
mudança em executores, configuração ou autorização. Nenhum commit criado.

## C2 aplicado — falha não é ausência, 2026-09-05

Primeira fronteira: o observador capturava erro e devolvia a mesma lista vazia de
uma leitura válida. Foram reproduzidos cinco REDs e dois controles antes do patch.
Leitura bem-sucedida vazia continua válida; falha não é ausência observada.

O retrato passa a informar `janelas_observadas` e `processos_observados`. Se a
enumeração de janelas falha, o adaptador de lista levanta erro e a fachada não o
converte em lista vazia. Falha de processos não invalida consulta direcionada
que depende somente de janelas; inventário parcial não confirma leitura completa.
`NoSuchProcess` é corrida benigna; acesso negado indica cobertura incompleta.

O pré-fluxo publica `falha_observacao`, `executou=False`, `confirmado=False` antes
da resposta. A memória compartilhada conserva o referente anterior. Resultado
direcionado sem booleano válido e inventário sem lista também não confirmam
ausência. Observadores legados sem os novos metadados continuam compatíveis se
entregam a estrutura esperada; isso não certifica fontes externas arbitrárias.

Um RED adicional mostrou que a cadeia interpretava falha comunicada como sucesso
por causa de `tratado=True`. O coordenador agora interrompe em `falha_observacao`,
mesmo se a voz rejeitar a emissão. A regressão prova que o detector da etapa
seguinte nem é chamado; nenhuma mutação foi executada.

Produção alterada: `percepcao/janelas_sistema.py`, `integracao/ambiente_navegacao.py`,
`autonomia/pre_fluxo_contextual.py`, `autonomia/coordenador_intencao.py`.
Worktree paralela preservada; catálogo, executores, configuração e datasets intactos.

13 testes focados em `tests/test_falha_observacao_consulta.py`. Observadores reais
pygetwindow/psutil funcionaram para ambas as fontes; consulta de VS Code e inventário
publicaram receipts confirmados. Foco inalterado, zero ações, voz e persistência
capturadas em memória. Falhas foram injetadas apenas em entradas controladas.

Limites: não houve sessão completa com LLM; o caminho posterior ao conteúdo não
resolvido continua pendente. Abas, validadores de efeitos que tratam `{}` como
ausência, precisão dos títulos e erros ocultos em getters individuais precisam
de diagnóstico próprio. C2 não corrige todos os consumidores. Treinos pausados.

## C3 observado — segurança preservada, conversa estagnada, 2026-09-05

Base e procedimento registrados no README. Prova completa atual:
`resultados_testes/roteiro_consulta_conteudo_c3-20260905-194754-467157`;
fontes: `conversa.md`, `planos.jsonl`, `terminal.log`, `resumo.json`.

O turno sobre VS Code publicou receipt confirmado. Os dois turnos sobre documento
não executaram comando e não confundiram aplicativo com conteúdo confirmado, mas
entregaram a mesma contingência mesmo após a correção explícita do usuário.
Os 3/3 do smoke check não contradizem esse RED de utilidade: o roteiro verifica
critérios básicos de segurança, não resolução do pedido nem progresso da conversa.

Cadeia sustentada pelo código e pelos artefatos:

1. A consulta de conteúdo chega à conversa sem evidência suficiente; o plano usa
   `estado_observavel_sem_evidencia`, sem autorização operacional inferida.
2. `contingencia_comunicacao` retorna uma frase fixa nessa estratégia.
3. `processamento_resposta_ia` tenta autoria final; ambos os logs registram
   `fala_invalida`. Quando não há autoria válida, mantém a contingência.
4. O contrato final aceita essa frase como incerteza legítima, mas o turno de
   correção não reconhece o escopo nem produz informação adicional ou próximo
   passo útil. A resposta idêntica aparece nos dois turnos reais.

Falsificações: não é ausência total de acesso à observação (consulta do aplicativo
funcionou no mesmo processo); não é execução dos patches antigos (sessão foi
iniciada após encerramento e recarregou a worktree atual). A hipótese de que a
repetição veio de duas falas autorais aceitas também contraria os logs de rejeição
e o ramo de contingência observado.

Ainda aberto: `fala_invalida` agrega extração vazia, estado técnico, JSON sem fala
e tamanho inválido. O log não identifica qual desses casos ocorreu. Não atribuir
a falha ao Qwen, a timeout ou a incapacidade de compreender sem capturar evidência
nessa fronteira. A falha que levou ao primeiro reparo também precisa ser isolada.

Próxima etapa: reproduzir a entrada/saída do callback real de autoria, registrando
metadados mínimos de diagnóstico, sem despejar contexto privado. Depois criar o
RED canônico de correção de escopo sem evidência: preservar o alvo e a limitação
real, reconhecer a correção e encaminhar somente um próximo passo sustentado pelas
capacidades disponíveis. Não substituir a investigação por variantes aleatórias
da frase fixa nem remover a exigência de receipt. Revisar separadamente o contador
de contingências do avaliador, que marcou zero apesar dos dois fallbacks reais.

Escopo deste registro: documentação e prova real, sem patch adicional de produção.
Modelo ativo, treinamento e promoção permanecem fora desta etapa. Não declarar
raiz C3 encerrada nem estender o GREEN da consulta de app a documentos ou outros
domínios.

## C3.1 — autoria rastreada e falso negativo reproduzido, 2026-09-05

Base mantida: `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, `main`, worktree
paralela preservada. Não houve treinamento nem alteração de modelo/configuração.

Diagnóstico opt-in: `diagnosticar_autoria_c3.py` executa `laylay.py` por `runpy`
com o roteiro oficial, instrumentando retornos por profiling. Não substitui LLM,
orçamento, composição, validadores ou executores. Por padrão guarda somente
metadados; `LAYLAY_DIAGNOSTICO_FALAS_SONDA=1` também registra falas avaliadas
restritas às três perguntas fixas (normalização de caixa, acentos e pontuação).
Não captura prompts nem o retrato mental. Não é sandbox e o profiling pode
afetar latência; os tempos não constituem benchmark. Exige sessão anterior fechada.

Evidências em `resultados_testes/`:

- `diagnostico_autoria_c3-20260905-195552-918817/fronteiras.jsonl`: reparo
  devolve JSON com fala; autoria seguinte recebe estado técnico, não fala do Qwen.
- `diagnostico_autoria_c3-20260905-200418-009085/fronteiras.jsonl`: prova do
  bloqueio `limite_chamadas` antes de HTTP; não inferir `reparo_duplicado`, embora
  também exista essa guarda no orçamento. Diagnóstico novo informa
  `estado_tecnico_llm`, não `fala_invalida`.
- `diagnostico_autoria_c3-20260905-200631-088850/fronteiras.jsonl`: principal
  afirma sem prova que o documento não está aberto (rejeição correta). Reparo
  começa com “Não há evidência atual de que um documento do Visual Studio Code
  esteja aberto”, mas recebe `estado_observavel_sem_incerteza` (falso negativo).
  O texto integral está na fixture `REPARO_REAL_C3`.
- `roteiro_consulta_conteudo_c3-20260905-200902-169240/` e diagnóstico
  `diagnostico_autoria_c3-20260905-200900-437594/`: execução após ambos os patches.
  Três respostas entregues, app com receipt, mas documento/correção ainda caem
  na mesma contingência. Surgiram `estado_observavel_negou_habilidade` e
  `estado_observavel_herdou_entidade_antiga`. **Não é GREEN conversacional.**

Uma tentativa intermediária `diagnostico_autoria_c3-20260905-200253-125553`
foi bloqueada porque Pedro reabriu a Laylay; não houve segunda instância.
Após ele encerrar, as sondas prosseguiram. A tentativa de 20:05:33 terminou com
código 1 apesar dos três turnos concluídos; não conta como encerramento limpo.
Avisos de serviço Gmail órfão apareceram em algumas sondas; registrar à parte,
sem atribuir a eles a cadeia conversacional já observada.

Contratos corrigidos e escopo:

1. Estado técnico de transporte não é fala autoral inválida. Quatro REDs foram
   reproduzidos; `autoria_conversacional.py` usa o reconhecedor técnico canônico
   antes de extrair a fala. A contingência e as permissões não mudam.
2. Negação explícita de evidência atual/suficiente é uma forma legítima de
   incerteza, não exclusiva de um domínio ou da frase fixa. Cinco REDs foram
   reproduzidos em documentos, janelas, IoT, processos e música.
   `validacao_contrato_fala.py` reconhece essa construção e a falta de confirmação.
   Afirmações positivas/negativas sem leitura e negação genérica de capacidade
   continuam bloqueadas. O orçamento não foi relaxado nem a autoria renomeada
   para contornar a proteção.

Validação: **236 testes passaram**, incluindo os dois módulos novos/ampliados,
qualidade, contrato semântico, orçamento, cliente, autorização e C1/C2. A integração
de `preparar_resposta_para_execucao` com o reparo real integral agora o preserva
após uma chamada, sem tentar uma segunda autoria. Essa prova tem modelo simulado;
a sonda real posterior gerou falas diferentes e continuou vermelha em utilidade.

Hipóteses falsificadas: não era JSON incompreensível na autoria final da primeira
sonda (chegou sentinela técnica); não era timeout dessa autoria (orçamento bloqueou
antes do HTTP); o primeiro reparo de 20:06 não omitiu incerteza (o validador não
reconhecia a construção). Isso não significa que todas as falas do modelo sejam
corretas: a afirmação inicial de documento fechado continuava sem evidência.

Próxima fronteira: inventariar a evidência de capacidade e de referente que chega
ao contrato em uma correção de escopo. Retomar “VS Code” do turno imediatamente
anterior foi marcado como entidade antiga; confirmar se a regra protege contra
contaminação ou se está sendo usada na continuidade errada. Separadamente, o
guardião de alegações substituiu uma frase com “não consegui verificar qual
documento está aberto” em sondas anteriores: seu reconhecedor de incerteza é
diferente do validador. Criar REDs de escopo de negação e de continuidade antes
de alterar esse guardião; não liberar uma afirmação factual posterior só porque
outra oração contém incerteza. Também não afirmar acesso a documentos só porque
há um catálogo de aplicativos ou uma janela observada.

Produção alterada nesta etapa: somente autoria e validação do contrato de fala.
Testes, diagnóstico opt-in e documentação adicionados/atualizados. Nenhum commit.
O problema geral de fallback repetido permanece aberto.

## C3.2 — escopo da incerteza e contexto de correção, 2026-09-05

Base preservada: `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, `main`, worktree
modificada, sem commit. Duas cadeias investigadas e testadas separadamente.

### Guardião: ressalva local, não salvo-conduto global

O guardião procurava qualquer incerteza na frase inteira, mas não reconhecia
“não consegui verificar”. Três relatos legítimos eram rejeitados e quatro
afirmações independentes depois de ressalvas eram aceitas. Os sete REDs foram
reproduzidos antes do patch, junto de quatro controles.

`guardiao_alegacoes.py` agora verifica cada ocorrência de estado observável com a
ressalva que a antecede na mesma oração. Pontuação e conectores explícitos limitam
o alcance. Isso preserva “não consegui verificar qual documento está aberto”, mas
não libera “não sei …, mas a janela está aberta”. Não é parser geral de português;
coordenações e construções ainda não cobertas continuam sendo limite conhecido.
Não foram alterados receipts nem a autoridade de qualquer executor.

### Continuidade: pergunta corrigida não é alvo observado

O histórico real de 20:09/20:23 tinha `referencia_resolvida={}` e `referente=''`.
O extrator resolve entidades operacionais conhecidas, não identifica o documento
apenas por seu aplicativo. Essa ausência não deve ser compensada inventando um
alvo. Outra primeira fronteira foi reproduzida: o owner da função comunicativa
classificava o contraste “estou perguntando sobre X, não sobre Y” como informação.

`leitura_usuario.py` reconhece esse contraste como correção, sem decidir comandos.
`contrato_fala.py` leva a entrada imediatamente anterior da mente compartilhada ao
campo efêmero `texto_usuario_corrigido`, somente para correção e idade entre 0 e
240 segundos. Timestamp inválido/futuro/expirado e entrada igual à atual não geram
esse contexto. Não usa a última ação nem textos arbitrários da própria Laylay.
O contexto aparece no prompt normal/compacto e no contrato de reparo.

`validacao_contrato_fala.py` usa essa fonte delimitada para a continuidade dos
nomes; não permite todo o histórico. O referente operacional continua vazio e
`autoriza_execucao=False`. Os testes mantêm bloqueados nomes presentes apenas na
fala da Laylay, perguntas independentes e afirmações sem leitura. Quatro REDs de
classificação/transporte do contexto precederam o patch. O guardião continua
avaliando prova de estado de modo independente da referência conversacional.

### Evidência e limites

**405 testes passaram** na regressão de comunicação, contratos, orçamento,
autorização, janelas e C1/C2. Novos módulos:
`tests/test_escopo_incerteza_alegacoes.py` (11) e
`tests/test_contexto_correcao_conversacional.py` (12), incluindo o caminho composto
`verificar_fala_turno` com componentes reais e controle negativo de afirmação.

Sonda final: `resultados_testes/roteiro_consulta_conteudo_c3-20260905-202732-986921/`;
metadados em `diagnostico_autoria_c3-20260905-202731-073804/fronteiras.jsonl`.
Runtime completo, três turnos respondidos, processo terminou com código 0.
O plano final comprovou `funcao='correcao'`, pergunta anterior correta no novo
campo, referente vazio e nenhuma autorização. A fala “Não, não consegui verificar
qual documento está aberto. O Visual Studio Code não compartilha esse detalhe
comigo.” atravessou os validadores e chegou ao usuário sem nova autoria/fallback.

Isso é GREEN do transporte do contexto e da preservação de “não consegui
verificar”, **não aprovação integral da fala**: a explicação de que o VS Code não
compartilha o detalhe não tem evidência específica nessa sonda. No turno anterior,
“Falta uma observação atual…” ainda foi rejeitado pelo reconhecedor de incerteza
do contrato e caiu em contingência. A afirmação inicial do modelo de documento
fechado foi corretamente rejeitada. Não declarar C3 encerrado por 3/3 do avaliador.

A sonda intermediária `roteiro_consulta_conteudo_c3-20260905-202344-620889`
(diagnóstico `20260905-202342-735357`) respondeu os
três turnos, mas encerrou com código 1 e não certifica shutdown saudável. Na sonda
final apareceu aviso de serviço Gmail órfão; registrado como questão separada.
Após o encerramento final não havia processos Python ativos.

Produção alterada nesta etapa: `emocoes/leitura_usuario.py`,
`cognicao/contrato_fala.py`, `cognicao/validacao_contrato_fala.py` e
`cognicao/guardiao_alegacoes.py`. Composition root, extrator de alvo operacional,
memória durável, modelo, treinamento, orçamento e executores não foram alterados.

Próxima fronteira: alinhar o reconhecimento de falta de evidência entre os
validadores e vincular explicações de capacidade à evidência específica do
catálogo/observador. Não responder “o app não fornece acesso” só porque não há
leitura disponível; também não prometer acesso a documento sem uma capacidade
confirmada. Evitar corrigir isso apenas adicionando variantes de uma frase fixa.

## C3.3 — ressalva compartilhada e pedido de informação, 2026-09-06

Base mantida: `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, `main`, alterações
paralelas preservadas. A sessão pessoal foi encerrada por Pedro antes das sondas.

Cinco REDs mostraram divergência entre os reconhecedores: algumas construções
eram rejeitadas pelo contrato (“Falta uma observação atual…”), outras passavam no
contrato e falhavam no guardião (“Não há evidência atual de qual documento está
aberto”). A menor fronteira comum é agora `incerteza_observacao.py`, importada por
ambos, com reconhecimento de ressalvas, sem escolha de ação ou efeito. O guardião
mantém a checagem por oração e a exigência de evidência; reconhecer incerteza não
torna verdadeira uma alegação nem comprova capacidade.

A sonda `roteiro_consulta_conteudo_c3-20260906-100126-123270/`, com diagnóstico
`diagnostico_autoria_c3-20260906-100122-940897/`, revelou um caso vizinho: “se você
puder me dizer qual arquivo ou pasta está aberto…” era interpretado como afirmação
de estado. Três REDs em pedidos de informação precederam a correção; declarações
como “posso informar que está aberto” e afirmações depois de “mas” continuam
bloqueadas. O helper compartilhado agora reconhece esse operador de pergunta
indireta ao usuário; isso não executa a consulta nem atesta disponibilidade.

**423 testes passaram** na mesma regressão ampla de C3.2. O teste composto de
`verificar_fala_turno` preserva a formulação “Falta uma observação atual…” até a
saída final. O reconhecimento linguístico continua conservador, não é uma PLN
irrestrita e não substitui proveniência de fatos ou identificação de alvo.

### Sonda final pelo launcher normal, sem profiling

`resultados_testes/roteiro_consulta_conteudo_c3-20260906-100353-826265/`.
Três turnos respondidos; saída do processo 0. Briefing e interface desativados
somente no ambiente desse processo; voz silenciada pelo roteiro. Serviços e
persistência normais, não sandbox. O estado real do app foi confirmado por receipt.

No segundo turno, o reparo passou pela qualidade, mas foi substituído pelo
guardião com `estado_atual_sem_evidencia`. O plano preservou a fala pré-guardião:
“Não há evidência atual de que um documento … esteja aberto. A última informação
foi que o VS Code está aberto, mas não em foco …”. A referência a uma observação
anterior requer uma investigação própria de proveniência temporal e alvo; não
liberar a frase só por conter “a última informação foi”. O receipt anterior do
app não prova estado atual do documento.

No terceiro turno, a correção manteve sua pergunta anterior no contrato e a fala
não foi substituída: “Não, não consegui verificar qual documento está aberto.
O VS Code não me permite acessar esse detalhe diretamente.” A primeira frase
preserva a limitação da observação; a explicação da segunda continua sem evidência
específica de uma restrição do VS Code. Não aprovar esse conteúdo integralmente.

O resumo marca 3/3 e nenhuma repetição literal nesta sonda, mas
`fallbacks_conversacionais=0` segue omitindo a substituição feita pelo guardião.
Não anunciar ausência de fallback. Aviso de serviço Gmail órfão apareceu no fim;
não foi misturado a esta raiz. A nova sonda não certifica voz audível nem UI.

Produção alterada em C3.3: novo helper `cognicao/incerteza_observacao.py` e os dois
consumidores `cognicao/guardiao_alegacoes.py`, `cognicao/validacao_contrato_fala.py`.
Testes ampliados nos módulos de incerteza/escopo. Nenhum treino, promoção, alteração
do modelo, executor, orçamento ou configuração persistente; nenhum commit.

Próxima fronteira: inventariar a passagem de evidência observada por alvo e tempo
ao contrato de fala. O catálogo `evidencia_conversacional` publica domínios gerais
(inclusive disponíveis/parciais/degradados), não uma prova de acesso ao documento
específico. Essa projeção não basta para justificar “o app não permite acesso”.
Separar estado atual do alvo, relato atribuído de observação anterior, ausência de
leitura e indisponibilidade comprovada. Criar REDs antes de ampliar essa ponte.
**C3 permanece aberto; GREEN dos contratos locais não encerra a conversa real.**
