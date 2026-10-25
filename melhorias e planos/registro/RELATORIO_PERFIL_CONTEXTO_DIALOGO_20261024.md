# C7/C5 — escolha do perfil deve admitir o contexto recuperável

Continuação autorizada da investigação de coerência da conversa. Os comandos
da Laylay foram simulados e a voz permaneceu desligada. Não houve ação externa
de domínio, mudança de modelo ou reinício da sessão pessoal.

## Base congelada e primeira fronteira

HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, branch `main`, worktree suja
preservada. Estado Git,527 hashes e quatro arquivos `.antes` estão em
`resultados_testes/perfil_contexto_dialogo_20261024/baseline.json` e na mesma pasta.
Essa base já contém o contrato anterior de recuperação literal; não confundir
o diff acumulado contra HEAD com a mudança desta investigação.

A etapa anterior comprovou recuperação quando o intervalo cabe, mas18/25/26/28
do roteiro longo continuavam sem fontes: o perfil rápido recusava o pacote
acima de1200 caracteres, embora o normal existente o admitisse em2600.

Cadeia reproduzida:

```text
fala curta → candidato a modo rápido → preparação rápida
→ pacote histórico necessário não cabe → fonte omitida no HTTP
```

A decisão de modo ocorria antes da montagem do pedido e consultava somente os
sinais linguísticos da fala. A necessidade concreta do contexto não voltava ao
orquestrador. Não é apagamento da memória: fonte/correção continuam no pedido
interno. Não é incapacidade inevitável do seletor: o mesmo pedido no orçamento
normal conserva ambas. Não depende de uma opinião da IA: dois REDs foram
reproduzidos com a saída do modelo controlada na porta HTTP da factory.
As falsificações e os controles curto/médio/grande estão em `falsificacoes.json`.

## Contrato compartilhado e responsáveis

| Owner | Responsabilidade e critério |
| --- | --- |
| `preparacao_llm` | Uma única seleção/serialização/orçamento governa a avaliação e o envio. Resultado tipado informa necessidade e preservação das fontes. Sem outro parser ou lista de frases. |
| `ContextoPromptRuntime` | Consulta a mesma memória temporária antes de preparar o turno; não gera fala, não persiste nem promove proposta a fato. |
| `RegistroPreparacaoConversa` | Expõe a necessidade de contexto sem entregar memória ao orquestrador; preparadores antigos continuam aceitos pelo adaptador. |
| `RespostaIARuntime` | Trata o modo rápido como candidato: usa normal quando ele recupera o que o rápido perderia. Prioridades e respostas locais continuam anteriores à decisão de orçamento LLM. |
| Modalidade/validador/executor existentes | Conservam autoridade e receipts. Contexto recuperado não autoriza executar proposta da IA nem repetir comando histórico. |

A nova consulta chama o mesmo seletor do transporte em simulação dos dois
orçamentos, com o papel atômico da instrução atual representado. Só há veto
ao rápido quando o perfil normal preserva as fontes que ele perde. Quando
ambos recusam, a mudança não promete recuperar o intervalo nem aumenta limites.
Se a avaliação falhar, o orquestrador usa o caminho normal e registra a falha.
Não há chamada extra à LLM para escolher o perfil.

Os limites1200/2600 caracteres e4/8 mensagens, a serialização com origem/papel,
a aceitação integral ou recusa do intervalo, a preservação das correções e os
pacotes fechados permanecem. O resultado tipado não é prova de implicação nem
verificação semântica. A recuperação continua lexical e limitada à sessão.

## Candidato mínimo e revisão

Produção alterada somente em:

- `mente_laylay/integracao/preparacao_llm.py`;
- `mente_laylay/autonomia/contexto_resposta_ia.py`;
- `mente_laylay/integracao/registro_conversa_llm.py`;
- `mente_laylay/autonomia/resposta_ia_runtime.py`.

O seletor lexical anterior, os domínios, a classificação de autoridade,
executores, catálogo de habilidades, cooperação, configuração/modelo/voz e
composition root não foram alterados nesta etapa. Não se trata de uma nova
habilidade: reutiliza contexto, memória de sessão, interpretação, diagnóstico
e validação canônicos, sem criar outro serviço ou estado privado. Nenhum commit.

A revisão encontrou uma regressão no primeiro candidato: avaliar orçamento
antes do porteiro social do jogo desviava uma saudação local para a LLM quando
o arquivo continha a mesma saudação antiga. Reproduzimos RED com preparador,
estado e orquestrador reais. O veto foi movido para depois do retorno social.
`repro_jogo_red.jsonl`: baseline1 fala local/0 pedidos, candidato0/1.
`repro_jogo_green.jsonl`: ambos1 fala local/0 pedidos.
A revisão final não identificou outro defeito concreto; não prova cobertura
de todas as diferenças possíveis entre histórico bruto e projeções especiais.

## Testes e contraprovas

Artefatos em `resultados_testes/perfil_contexto_dialogo_20261024/`:

- `red.xml`:2 RED na primeira fronteira de modo,4 controles GREEN. Telescópio
  e congresso; fonte e correção; intervalos curto, médio e acima dos dois perfis.
- `contrafactual_baseline.xml`: mesmos2 RED e4 controles nos quatro owners
  congelados, carregados em memória sem restaurar arquivos da worktree.
- `red_atalho.xml`:1 RED do candidato na saudação do jogo,8 controles GREEN.
- `green_atalho.xml`:15 testes novos GREEN, incluindo o atalho social reparado.
- `green_final.xml`:133 testes focados GREEN, com contratos anteriores de
  recuperação, perfil, transporte, orçamento e registro tipado.
- `regressao.xml`:1554 aprovados,30 subtests aprovados,14 skips opcionais,
  1 deselecionado por ordem/importação já conhecida. Persistem2 falhas de
  `test_autoria_reescritas`[4]/[6], expectativa de primeira chamada principal
  versus interpretação. `falhas_anteriores_baseline.xml` reproduziu exatamente
  essas2 falhas e30 aprovações nos owners congelados. Não são suíte toda verde.
- `import_isolado.xml`:o teste deselecionado de composição/latência passou
  isoladamente, no root redirecionado e sem rede/voz/integração real de apps.

Os seis casos instalados usam a factory e o caminho até HTTP reais, com modelo
controlado que propõe APP_OPEN sem pedido atual. A autoridade permanece falsa
e nenhum executor é chamado. Os controles curtos continuam rápidos; os médios
usam normal com fonte/correção integrais; o intervalo acima de ambos segue
recusado inteiro. A consulta de admissibilidade não muda estado/diagnóstico,
nem prepara resposta; otimização desligada e adaptador antigo têm controles.

## Composição real, Qwen e conversa contínua

`conversa_final/` contém a execução da versão final em30 turnos contínuos,
com os serviços cognitivos reais da factory restaurados por identidade.
Persistência em perfil isolado, AppOpener simulado desde import, rede pública,
serial, shell e escrita fora da pasta bloqueados. Os únicos despachos foram
dois APP_OPEN simulados com receipts negativos tipados, sem sucesso inventado.
Não usar esse ensaio como prova do funcionamento das habilidades externas.

Resultado:30 conclusões textuais,29HTTP200 e2 timeouts;241,146s dentro dos
turnos,0 voz/efeitos. `avaliar.py` conferiu16 pacotes enviados: cada índice,
papel e texto corresponde a um PedidoModelo daquele ato.527 hashes estáveis
durante a coleta. O modelo permaneceu `qwen3:4b-instruct`, sem alteração de
configuração, tempo limite ou janela do backend.

| Turno do roteiro | Modo final | Fonte original no primeiro HTTP autoral | Resultado observado |
| --- | --- | --- | --- |
|18, livro azul | normal |8/9 presentes | timeout; não classificar como esquecimento |
|19, parte de Leo | rápido |12/13 presentes | respondeu música no projeto Ponte de Papel |
|25, encontro | normal |8/10/20 presentes | biblioteca Aurora e16h corretos |
|26, nome do jogo | normal |12/20 presentes | timeout; não houve resposta factual avaliada |
|28, banda anterior | normal |5/Nirvana presente | resposta sobre “Eu Falei Que Gosto”, ainda inadequada |

Para18/25/26/28, o contraste determinístico do mesmo pedido mostra rápido sem
preservação e normal com preservação. A primeira fronteira de escolha/corte
foi corrigida e validada no envio real, inclusive quando o transporte depois
falhou. Não usar timeout como prova de compreensão e nem de falta de fonte.

O ensaio anterior à correção da ordem do atalho foi preservado em `conversa_real/`
com hashes estáveis, mas a validação final é `conversa_final/`. Não repetimos
coleta para selecionar uma resposta favorável: a segunda execução verifica
a versão de produção após a mudança de ordem exigida pela revisão.

## O que permanece aberto e próxima fronteira

O contexto chegar não garante uso fiel. Persistem perspectiva usuário/IA,
correção de caderno classificada como ação e o novo plano consumido como
feedback do aplicativo.28 falhou apesar da fonte disponível; o primeiro ponto
incorreto depois da entrega da fonte deve ser estudado na autoria/revisão,
sem reabrir a ausência de fonte como explicação desse caso.

Os dois timeouts são evidência de limite de entrega no orçamento do turno;
maior contexto não permite prometer menor latência. É necessário investigar
custo, chamadas anteriores e prazo disponível sem cortar fontes nem aumentar
limites cegamente. O intervalo acima do perfil normal e a condição inicial
sem sistema canônico também permanecem fora da correção demonstrada.

Vínculos C7/C5/F1/F3 preservados, sem contar cada fala como uma nova raiz.
Encerrado o recorte de admissão do perfil para contexto recuperável; não
encerrar a compreensão geral nem fundir falhas de autoria, perspectiva,
modalidade, pré-fluxo e transporte. A próxima investigação deve escolher uma
dessas primeiras fronteiras remanescentes e conservar as outras como controles.
