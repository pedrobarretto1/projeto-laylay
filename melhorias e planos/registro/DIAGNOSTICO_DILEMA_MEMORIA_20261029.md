# Rodada do dilema da memória — diagnóstico dos quatro journals

Pedido de Pedro: conferir o relato anexado e buscar mais informações nos
arquivos da sessão. Foram localizadas e examinadas as quatro sessões novas,
sem abrir conversa com Qwen, ativar voz ou executar ações externas.

## Base, contagens e proveniência

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. Base de 536 fontes e estado Git congelados em
`resultados_testes/rodada_memoria_20261029/baseline.json` e `base/`.
As quatro cópias históricas contêm essas mesmas 536 fontes, sem divergências.
Portanto os sintomas ocorreram com as correções atuais presentes; não é válido
atribuir a rodada a uma instalação anterior nem a um teste de código inexistente.

Origem dos journals:
`C:/Users/pbarr/Documents/Codex/2026-10-28/ch/work/ponte_sessoes/`.

| Sessão | Mensagens enviadas | Respostas entregues pela ponte | Erros fatais da ponte | Publicações textuais internas |
| --- | ---: | ---: | ---: | ---: |
| `20261029T151408Z-bee5fcef` | 7 | 6 | 1 | 7 |
| `20261029T151938Z-2cd29ed7` | 4 | 3 | 1 | 4 |
| `20261029T152204Z-ba3bf64e` | 3 | 2 | 1 | 3 |
| `20261029T152347Z-769cbc1c` | 4 | 3 | 1 | 4 |
| Total | 18 | 14 | 4 | 18 |

Os quatro turnos finais receberam contingências no runtime, mas a ponte os
devolveu como erro fatal por registrar falha da última chamada do modelo.
Publicação interna, resposta útil e entrega pela ponte são estados distintos.
As contingências internas não são as respostas argumentativas que se perderam.
Não modificar a ponte para chamar essas contingências de respostas completas.

Os dados completos, hashes dos três journals de cada sessão, retornos e estado
resumido dos turnos estão preservados em `sessoes.json`. Não houve mudança em
fonte de produção ou configuração nesta investigação.

## Fronteiras demonstradas, por contrato

| Evidência | Primeira divergência demonstrada | Owner / família existente | Estado |
| --- | --- | --- | --- |
| `respeito-003` — `Responda em poucas frases` | A diretiva de forma no canal da conversa recebe `comando`, autoridade e texto operacional | `normalizacao_linguagem.tipo_transformacao_conversacional` / `modalidade_turno`; continuação da distinção entre ato textual e efeito | Reproduzido em funções puras e composição instalada controlada; não corrigido |
| `memoria-005` — `apagá-lo faria...` | O normalizador instalado transforma `apagá-lo` em `apaga lo`; o classificador lê o núcleo como pedido direto, apesar do predicado hipotético | Normalização e modalidade; preservação da morfologia antes de conceder autoridade | Reproduzido somente ao incluir o normalizador real, e no runtime composto; raiz distinta da diretiva de forma |
| `memoria-002`, `sorte-002` | A presença de referência à resposta passada e linguagem explicativa em outras partes torna o turno inteiro obrigação retrospectiva | `referencias_linguagem.referencia_explicacao_propria` e composição de `contrato_fala`; família referente ≠ finalidade | Rota histórica reproduzida; não há correção ou prova de cobertura semântica geral |
| `decisao-001` | Discutir se uma assistente pode recomendar uma escolha é reconhecido como pedido factual de recomendação | `fundamentacao_factual.texto_pede_recomendacao` | Captura lexical demonstrada; mesmo aviso reproduzido, sem pesquisar ou aprovar recomendação |
| `memoria-007` | Concordância `você tá certo:` seguida de comentário sobre outro assunto é tratada como atribuição pessoal sem apoio | `afirmacoes_interlocutor` e `referencias_linguagem.natureza_predicado_pessoal`; família posicionamento ≠ biografia | Recusa local reproduzida; continuação do recorte anterior, sem isentar fatos no comentário |
| `decisao-004` | O modelo repete a resposta recusada quando solicitado a reconhecer a contradição | Autoria do modelo; guarda existente de `continuidade_resposta` | Texto normalizado idêntico: 97 palavras. Guarda detecta corretamente reuso integral/predominante e pede reparo |
| Quatro encerramentos | Uma ou mais gerações posteriores não concluem; por último o orçamento impede outra tentativa | Autoria/reparo, revisão, orçamento e ponte, com papéis separados | Orçamento é o último estado observado; a causa anterior varia. Não é prova de que basta aumentar o limite |

As linhas não devem ser contadas como sete bugs novos: várias são novas
evidências de famílias já abertas. Também não se deve agrupar os dois falsos
comandos como uma só raiz apenas porque terminam no mesmo aviso.

## Provas e controles específicos

**Diretiva de forma.** A entrada histórica e a forma curta são classificadas
como comando antes de qualquer LLM ou executor. `Responda ao e-mail em poucas
frases` continua sendo um controle operacional; retirar o verbo do léxico
indiscriminadamente não respeitaria esse contraste. O contrato existente só
cobre transformações discursivas delimitadas, não todas as instruções de forma.

**Morfologia e normalização.** Sem normalizador, `Apagá-lo faria a assistente
perder informação` não autoriza ação; com `normalizar_texto`, autoriza. A forma
sem clítico, `Apagar o registro faria...`, permanece não operacional em ambas.
`Apague o registro agora` autoriza em ambas. Isso falsifica uma falha geral do
executor e uma falha indistinta em qualquer hipótese. Próxima investigação deve
preservar infinitivo/clítico e sua relação com o predicado; não cadastrar
exceção para `apagá-lo` nem remover paradas/ordens reais.

**Referente e finalidade.** O leitor histórico retorna vazio para `Sua resposta
ficou ambígua. Você concorda com essa distinção?`, mas retorna `fala` ao acrescentar
`porque só um causou dano`. A presença global de `sua resposta` e `porque` basta
para satisfazer a combinação lexical, embora a pergunta matriz peça uma posição
conceitual. Em `memoria-002`, a indicação de uma fala anterior e o pedido final
`Explique` também ativam a rota. A fonte mencionada pode ser pertinente sem
impor explicar causa ou resultado de uma ação passada.

**Recomendação.** Tanto `Uma assistente pode recomendar uma escolha num dilema
moral?` quanto `Qual é a diferença entre recomendar e manipular?` são marcados
como pedido factual, assim como o controle legítimo `Me recomenda um notebook
para estudar`. A função busca o verbo em qualquer posição fora da moldura
metalinguística reconhecida. A correção futura deve distinguir ato discutido e
serviço solicitado, preservando a fundamentação de recomendações reais.

**Concordância e atribuição.** `Tá, você tá certo.` não recebe recusa. A extensão
`Tá, você tá certo: o tom neutro não é um muro.` recebe
`afirmacao_interlocutor_sem_apoio`. A proteção não deve ser removida: `Você está
certa: você está triste.` é um controle em que existe atribuição pessoal sem
fonte. Separar o ato avaliativo da afirmação seguinte não certifica a verdade
da afirmação nem dispensa sua revisão individual.

**Repetição.** A fala primária de `decisao-004` é igual, após normalização, à
publicação de `decisao-003`. As duas têm 97 palavras. `RespostasAnterioresTurno`
detecta a cópia e a composição solicita `resposta_repetida_literal`. Isso é
comportamento correto do guardião. Não liberar essa proposta para evitar uma
falha de geração subsequente, nem confundir a cópia do modelo com um bloqueio
indevido de texto que resolveu a contradição.

## Chamadas finais observadas historicamente

| Turno final | Retornos registrados, em ordem |
| --- | --- |
| `memoria-007` | `principal`, sucesso; `contrato_saida_invalido`, falha; `orcamento_bloqueado`, prazo esgotado |
| `decisao-004` | `principal`, sucesso com repetição; `contrato_saida_invalido`, falha; `orcamento_bloqueado`, prazo esgotado |
| `sorte-003` | `principal`, sucesso; `orcamento_bloqueado`, fatia secundária insuficiente |
| `respeito-004` | duas emissões `principal` bem-sucedidas; `orcamento_bloqueado`, prazo esgotado |

`sucesso` confirma que o contrato daquela emissão foi aceito pelo transporte,
não que o conteúdo é verdadeiro, adequado ou completo. A segunda emissão de
`respeito-004` e a proposta de `sorte-003` não devem ser aprovadas integralmente
apenas por conterem uma frase boa. A avaliação precisa considerar todo o texto.

`contrato_saida_invalido` também não significa necessariamente JSON com sintaxe
inválida: `ClienteLLMRuntime` devolve essa categoria para erros de decodificação
ou de contrato. Nesses journals, o texto da emissão recusada não foi preservado
nesse evento; ele é vazio. Falta evidência para declarar se houve chave indevida,
enum errado, quebra de cobertura, semântica de fonte ou JSON malformado. Uma
correção desse contrato exige capturar o motivo concreto sem conceder aceitação
permissiva. A ponte não mostra o tipo da chamada nesse evento; não atribuir
uma rota posterior específica sem outra evidência.

## Reapresentação controlada e seus limites

`diagnosticar.py --canonico` exercita os componentes instalados, com HTTP fixo,
histórico textual anterior ao alvo, memória isolada, áudio bloqueado e executor
interceptado. Nove alvos foram examinados. Não é uma nova conversa com Qwen.
Não reconstrói o registro semântico nativo, relógio, prazo gasto ou todas as
decisões transitórias da sessão original.

A primeira reprodução enviava de volta `partes` do evento do observador. Isso
era incorreto: o observador registra o resultado **pós-codec**, enquanto o
wire v5 negocia `texto` e depois o particiona internamente. Os erros de formato
dessa primeira tentativa são artefatos da reprodução e não prova de raiz em
produção. Foram preservados em `diagnostico.json`, sem escondê-los. A versão
canônica reconstrói `texto` pela junção literal das partes e mantém proposições
e referências; seus resultados estão em `diagnostico_canonico.json`.

Em chamadas posteriores, a reprodução reapresenta a mesma proposta fixa, não a
emissão histórica recusada que os journals não guardaram. Portanto a falha de
um segundo codec na reprodução não prova a causa original do reparo. O arquivo
registra os pedidos, contratos e mensagens para localizar o que o host exigia.

Resultados úteis dessa reprodução: os falsos comandos e a captura por
recomendação persistem; o roteiro histórico de `sorte-002` reaparece; a guarda
de repetição recusa a cópia. Em `memoria-007`, o primeiro reparo controlado é
solicitado por atribuição pessoal sem apoio. Em `sorte-003`, o parecer pede
`ato_opiniao_nao_respondido`, apesar da abertura `Sim, daria...`. Esse último
limite merece estudo próprio do contrato de posição, sem declarar toda a
proposta longa correta. Em `respeito-004`, o reparo composto não conclui todas
as partes; o histórico textual sozinho não prova a raiz exata do encerramento.

## Próxima prioridade e critério de encerramento

Priorizar as fronteiras de modalidade, antes de interpretar os avisos finais:
diretiva textual não pode autorizar efeito; normalização não pode transformar
infinitivo com clítico em imperativo. São duas investigações, com RED canônico,
controles de destino externo/ordem real e prova na composição com normalizador
real. Em seguida, delimitar a pergunta matriz na consulta histórica e o ato
discutido na recomendação.

Para recuperação, preservar a recusa correta da repetição e separar concordância
de atribuição pessoal, com revisão das afirmações restantes. Só depois medir
se o reparo agora válido chega à entrega dentro do orçamento existente. Não
aumentar limite de mensagens ou orçamento para esconder recusas anteriores.

Produção alterada nesta investigação: **nenhuma**. Somente diagnóstico,
artefatos e registro de pendências; sem novos commits. O resultado é um mapa
causal com provas e limites, não declaração de correção das quatro sessões nem
de compreensão geral concluída. Os testes de conversa permanecem com Pedro.
