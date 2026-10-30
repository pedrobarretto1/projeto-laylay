# Categoria da pergunta e preferência pessoal — 25/10/2026

Perguntas como `qual aplicativo eu prefiro` e `qual gênero eu gosto` agora
exigem dois apoios distintos: a declaração pessoal e o vínculo de categoria
do nome. O Qwen não fornece prova para esse vínculo. No teste focado real,
cinco perguntas receberam a fonte esperada, incluindo Obsidian, rock e a
negação de gosto por jazz, com distratores do mesmo predicado.

## Base e fronteiras demonstradas

Base: HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, `main`, worktree suja com
etapas anteriores, preservadas. Estado e 527 hashes iniciais em
`resultados_testes/categoria_consulta_usuario_20261025/baseline.json`.
Snapshots e diff contra a base estão na mesma pasta. Outra alteração de
`artifacts/rosto_oled/wifi/hotspot_windows.json` surgiu paralelamente e não faz
parte deste trabalho.

Primeira divergência: perguntas pessoais diretas não entravam no guard de
retomada; nas retrospectivas, a existência da preferência era admitida sem
comprovar a categoria perguntada. `contrato_red.xml` reproduziu seis falhas,
incluindo duas factories. A composição publicou preferência de outra categoria.

O catálogo de aplicativos existente já classificava Firefox, mas estava fora
do registro filtrado do turno. `composicao_red.xml` confirmou a ausência da
MESMA instância do catálogo: duas falhas antes do patch de ligação. A lista
de dependências agora entrega essa instância pelo caminho oficial; não se
criou um catálogo de teste dentro da produção.

O catálogo local deste PC não contém Obsidian. Não adicionar esse nome a uma
lista para esconder o caso. A pesquisa existente encontra sua página e pode
ler a declaração estruturada da entidade correspondente. A documentação
oficial também identifica o produto como aplicativo, mas não foi convertida
em regra textual específica: [Obsidian](https://obsidian.md/) e
[item estruturado](https://www.wikidata.org/wiki/Q103994532).

## Contrato e responsáveis

| Responsabilidade | Owner | Limite |
| --- | --- | --- |
| Ler lacuna, sujeito e predicado | `referencias_linguagem.consulta_categoria_preferencia_usuario` | Pergunta do usuário, não gosto da Laylay; conserva negação do dizer separada da negação da preferência |
| Provar preferência | Leitor e qualificação já existentes em `fundamentacao_factual` | Autor, identidade, hash e status da fonte pessoal; pergunta atual não vira declaração |
| Provar tipo local | Catálogo real de aplicativos e léxico já usado por `memoria_pessoas` | Só classificação; não prova preferência, instalação atual, reprodução ou efeito |
| Ler tipo externo | `PesquisaContextualRuntime.pesquisar_categoria_entidade` | QID, nome exato, P31, classe explícita, rank, ausência de qualificadores, hash e validade |
| Vincular apoios ao turno | `categoria_preferencia.ApoiosCategoriaPreferencia` | Snapshot nativo imutável com id/texto do turno e id/texto/hash da fonte pessoal; dict proposto pela IA não é aceito |
| Admitir resposta | `avaliar_nucleo_retomada_usuario` já compartilhado | Qualidade, opções do reparo e revisão final consomem o mesmo vínculo; nenhum atalho de efeito |

Categorias desta entrega: app/aplicativo/programa/software e gênero/estilo
musical. O mapa de predicados de preferência foi centralizado sem duplicar
o leitor das declarações. O léxico musical da memória foi exposto e reutilizado,
mantendo sua implementação e dados anteriores. Outros tipos não foram
adivinhados nem incluídos automaticamente.

O snapshot publica metadados da relação memória + catálogo/léxico/pesquisa no
quadro, pelo coordenador cooperativo existente. A publicação tem autoridade
falsa e não é confirmação de entrega, efeito ou acerto de toda a resposta.
As factories conferem essa publicação e a identidade do catálogo.

## Fonte externa: candidato rejeitado e contrato final

Uma primeira leitura de prefixo copular externo foi falsificada na revisão:
`X é um aplicativo? Essa alegação é falsa.` e caudas que apresentavam hipótese
ainda eram aceitas. `operadores_red.xml` e `estrutura_red.xml` preservam os
REDs. A correção não foi ampliar uma lista de palavras proibidas: o caminho
que classificava por prosa foi removido por inteiro.

O produtor final usa o QID retornado pela página lida na API, e então lê o JSON
da entidade em Wikidata. Confere o mesmo id e nome literal em rótulos/aliases
pt/en/mul; admite somente P31 com valor de entidade, classe documentada
`Q40056`/`Q7397` para software/programa ou `Q188451` para gênero musical,
rank normal/preferred e sem qualificadores. Não infere subclasses ou uma
categoria a partir do título, resumo, snippet, descrição ou proposta da IA.

A pesquisa reaproveita cache, worker e orçamento interativo de quatro segundos.
Há no máximo uma pesquisa nova por turno e nenhuma quando já existe apoio
local suficiente. Negação/ausência do ato de dizer não é provada por uma
preferência positiva; nesses pedidos o snapshot não inventa itens.

`conhecimento_obtido_rede.json`: leitura real, quatro HTTP 200,
`Q103994532`/P31/`Q40056`, 1,831 segundo observado e resposta na primeira
consulta. Preserva documento e hash, sem alegar benchmark. O item é evidência
do que o catálogo externo declara; não é verdade universal nem preferência
atual do usuário.

## Validação e escopo de produção

Produção nesta etapa:

- `cognicao/categoria_preferencia.py` novo;
- `cognicao/referencias_linguagem.py`;
- `cognicao/fundamentacao_factual.py`;
- `cognicao/orquestrador_turno_runtime.py`;
- `cognicao/composicao_turno.py`;
- `cognicao/pesquisa_contextual.py`;
- `memoria_mental/memoria_pessoas.py`.

Todos sob `mente_laylay/`. Não houve alteração de `laylay.py`, executor,
configuração de modelo/voz, orçamento ou ativação autônoma; nenhum commit.

93 testes focados aprovados, incluindo identidade/fonte/ocorrência inválida,
negação do relato, páginas interrogativas/refutadas/hipotéticas, P31 de classe
errada, entidade/nome divergentes, depreciação, qualificadores, cache e duas
novas factories. Revisão independente confirmou a remoção do caminho por
prosa e os controles estruturados. Negativos de prosa bloqueiam rede.

Fixtures antigas de autoria pressupunham que Obsidian era um app. Agora
declaram essa fonte no catálogo real da fixture, conservando a exigência de
resposta correta. O teste que antes oferecia hospital para pergunta de app
foi fortalecido: essa opção deve ser rejeitada. Não foi reduzida a expectativa
para aceitar qualquer limite.

Regressão de 98 módulos: 2.462 aprovados, 30 subtests aprovados, 14 skips,
mesmas nove falhas anteriores e 44 erros na fixture adicional de
`test_composicao_turno`. Estes 44 têm uma única causa anterior: serialização
JSON de `PerspectivaEnunciador` sem adaptador. A contraprova sobre fontes
congeladas reproduz a MESMA primeira exceção, sem restaurar arquivos no disco.
Não chamar esta suíte de inteiramente verde nem contar 44 novas raízes.
O teste de import separado passou. XMLs, logs, comando e comparação preservados.

## Composição com Qwen

Mesmo `qwen3:4b-instruct`/Ollama local, perfis isolados, sem voz/efeitos reais.
A fonte externa REAL recente foi reproduzida na folha HTTP e requalificada
pelo produtor real para o cache do perfil. Id, classe, claim e hash coincidem
com a captura; o TTL original NÃO foi estendido. Isso prova o caminho com
cache da composição. A aquisição real em rede foi validada separadamente;
não apresentar a coleta como navegação externa nova a cada pergunta.

`conversa_validada/`: 30 turnos/conclusões, 36 HTTP 200, 17 pacotes primários,
528 fontes sem drift e um receipt negativo de Calculadora simulada. As
perguntas diretas de aplicativo/gênero passaram, e as quatro retomadas-alvo
anteriores conservaram a fonte esperada. O turno 7 teve limite de prazo e o
29 de tentativas: não são êxitos conversacionais.

`foco_final/`: 12 turnos/conclusões, 17 HTTP 200, oito pacotes primários,
mesmas 528 fontes, zero pedidos de ação. Cinco alvos corretos:

- app preferido → Obsidian;
- gênero apreciado → rock;
- app antes preferido, depois de preferência por chá → Obsidian;
- gênero antes apreciado, depois de gosto por Firefox → rock;
- gênero não apreciado → jazz.

`auditoria_categoria.json` verifica nove respostas com apoios separados,
incluindo a publicação no quadro e a origem estruturada do tipo. As duas
coletas somam 42 turnos; não são prova de acerto integral de toda conversa.

## Limites e novo log

Sem fonte de categoria válida, não completar o vínculo com a escolha da IA.
Continuam fora do recorte: todos os tipos possíveis, subclasses livres,
paráfrases/sinônimos não conferidos, preferências atuais conflitantes,
completude de múltiplos gostos e resolução temporal de correções.

Durante esta investigação Pedro forneceu novo diálogo sobre gosto próprio,
`como assim?`, indie, clipboard e prazo. Esse log NÃO tem sua raiz demonstrada
pela categoria da preferência do usuário. Foi preservado em
`NOVO_LOG_PENDENTE.md` e ganhou investigação separada em
`resultados_testes/conversa_gosto_clareza_20261025/`.
O texto interno em multiato já foi reproduzido com o registro real de fala;
a correção dessa fronteira não pertence a este candidato. Não fundir
F1/C5/C7/AUT nem os outros mecanismos por semelhança de sintomas.
