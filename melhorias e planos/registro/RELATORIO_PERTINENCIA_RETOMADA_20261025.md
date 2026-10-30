# Relação entre a pergunta e a fonte da retomada — 25/10/2026

Corrigida a admissão de citação de outro assunto quando a pergunta explicita
o conteúdo consultado. A mesma conferência é usada na qualidade, nas opções
de reparo e na revisão final. No caso real que perguntava sobre rock e recebia
chá, a nova coleta respondeu `Você contou: «eu gosto de rock».` A fonte de chá
não estava mais entre as realizações admissíveis daquele reparo.

Validação real: 30 turnos da conversa longa e 12 de controle em outros domínios,
sem voz ou efeitos reais. As oito retomadas-alvo dessas duas coletas tiveram a
fonte esperada. Isso não certifica todas as respostas dos 42 turnos, semântica
livre ou acerto geral do Qwen. Categorias implícitas e resumos permanecem nos
contratos anteriores, com os limites descritos abaixo.

## Base congelada e raiz demonstrada

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`. A worktree já
continha as alterações da etapa anterior: elas foram preservadas. Estado,
527 hashes e snapshots em `resultados_testes/pertinencia_retomada_20261025/`.
`baseline.json` distingue esta base do Git; `fontes_antes/` conserva os owners.
O diff desta etapa, contra essas fontes, está em `candidato_contra_base.patch`.

Evidência histórica imediata: `reparo_retomada_conferivel_20261025`, turno 26.
Pergunta `eu contei que não gosto de rock?`; proposta e publicação sobre
`eu não gosto de chá`. A auditoria do HTTP demonstra que a fonte correta de
rock estava no enum e que o transporte conservou a escolha feita pelo Qwen.
Ausência de fonte e alteração da proposta pelo transporte foram falsificadas.

Primeira transição incorreta:

```text
pergunta retrospectiva reconhecida e perspectiva vigente
→ fontes de ambos os assuntos disponíveis e qualificadas
→ citação de chá literal e fiel
→ revisor aprova porque a fonte existe, sem conferir o conteúdo consultado
→ enum admite fonte alheia à pergunta
→ Qwen escolhe chá
→ revisão final repete a admissão
```

O erro não era inexistência da citação nem falha do codec fechado. Faltava ao
owner do núcleo conferir uma restrição distinta: a relação literal entre o
conteúdo explícito da pergunta e a fonte usada para respondê-la. A escolha do
modelo não preenche essa obrigação.

`contrato_red.xml`: 12 falhas e dois controles antes de produção. Seis pares
de fontes em domínios diferentes demonstram o mesmo mecanismo. Há também
paráfrase indevida, fronteira de nome e duas factories instaladas. Estas últimas
publicavam a citação de chá apesar de ambas as fontes estarem no plano. O RED
alcançou a revisão de conteúdo, sem falha de importação ou efeito externo.

## Contrato, owners e escopo

| Responsabilidade | Owner | Critério verificável |
| --- | --- | --- |
| Reconhecer consulta ao dizer | `pedido_consulta_fala_usuario` existente | Não confundir declaração, terceiro, citação ou outra ocorrência com consulta do usuário |
| Ler o conteúdo explícito consultado | `referencias_linguagem.recorte_consulta_fala_usuario` | Depois do detector canônico: complemento de pergunta polar `eu … que …?` ou tópico de pergunta aberta `o que … sobre/a respeito de/acerca de …` |
| Conferir fonte e vínculo | `fundamentacao_factual.avaliar_nucleo_retomada_usuario` | Além da fonte qualificada, conferir o mesmo núcleo literal ou presença do tópico nominal com fronteiras; rejeitar citação/paráfrase de outro conteúdo |
| Produzir e revisar reparo | Owners já existentes de qualidade, autoria e revisão | Reutilizar a mesma conferência no enum e no final; texto livre, escolha do modelo e referência proposta não substituem prova |
| Validar utilidade da coleta | Auditorias com alvos explícitos | Fonte efetivamente conferida deve coincidir com a fonte esperada da pergunta; não contar limite como resposta correta |

O complemento polar conserva o texto integral do núcleo, desconsiderando apenas
o sujeito inicial `eu` e a negação inicial na comparação. A negação da pergunta
não é assumida como declaração: a fonte positiva sobre rock pode contrariar a
premissa negativa, mantendo sua própria polaridade na citação. Não se reescreve
a fonte nem se conclui ausência histórica de todas as afirmações contrárias.

A comparação conserva acentos e usa NFC/caixa/espaços. Normalização de busca
que eliminasse acentos não foi usada como prova de identidade de nomes. O
tópico deve ocorrer com fronteiras de palavra, sem aceitar apenas prefixo de
outro nome. Isso é vínculo literal, não implicação semântica livre.

A saída registra `vinculo_consulta`: vínculo literal conferido, fonte fora da
consulta ou fora do recorte literal. Todos os indicadores de semântica livre,
prova de implicação, fato externo e autorização continuam falsos. Perguntas
sem esse conteúdo explícito conservam `conferido=None`; o patch não inventa
uma resolução de categoria, elipse ou referência indireta.

Princípio geral reutilizável: existir no histórico e responder à pergunta são
obrigações distintas. A conferência pertence ao contrato comum de resposta,
não a listas de nomes, habilidades ou frases históricas. O mesmo mecanismo
protege conteúdo sobre música, software, trabalho, estudos, viagens e animais.
Não há patch por `rock`, `chá`, número de turno ou domínio.

Produção alterada nesta etapa somente em:

- `mente_laylay/cognicao/referencias_linguagem.py`;
- `mente_laylay/cognicao/fundamentacao_factual.py`.

Qualidade, codec, composição, executores, configuração do modelo, voz,
timeout e orçamento foram reutilizados sem alteração nesta etapa. O candidato
anterior em qualidade permanece preservado. Nenhum commit criado.

## Revisão, RED adicional e regressão

A revisão independente reproduziu uma fuga: o detector canônico removia `e`
ou `então`, mas o novo leitor de complemento não. Assim, a mesma pergunta com
conector reabria a aprovação de chá. O achado foi verificado antes do patch:
`abertura_red.xml`, 12 falhas nas variantes dos seis casos.

Detector e leitor agora reutilizam `_abertura_consulta_fala_usuario`, com a
mesma regra de abertura existente. Não foi criado outro parser por habilidade.
Acentos do conteúdo permanecem intactos. O revisor confirmou 24 testes e
probes de caixa/`entao`, sem bloqueio restante no recorte declarado.
`revisao_independente.json` preserva achado, resolução e limites.

`contrato_final.xml`: 66 testes aprovados, com quatro factories dos três
módulos. Na factory negativa, proposta fiel sobre assunto errado é retida;
na positiva, a folha HTTP oferece a fonte esperada e há uma publicação por
turno. Controles já corretos são preservados. Qualificação de fonte, outro
autor, hash, contestação, outra ocorrência e autoridade continuam protegidos
pelos regressivos existentes. Os executores e a voz não foram acionados.

Regressão de 96 módulos: 2.354 aprovados, 14 skips, 30 subtests aprovados, uma
deseleção de import e as mesmas nove falhas anteriores. Zero falha nova por
comparação de IDs em `comparacao_falhas_anteriores.json`. Permanecem um caso
antigo de Calculadora e oito expectativas de pacote/reserva; os testes não
foram enfraquecidos. Comando, saída e XML preservados. O teste de import passou
separadamente no root isolado (`import_isolado.xml`).

## Prova com Qwen na composição instalada

Mesmo `qwen3:4b-instruct` no Ollama local. Persistência isolada por redirecionamento
em memória do composition root, fontes do disco preservadas, serviços canônicos
restaurados e callbacks de revisão reais. Somente rede local do modelo foi
permitida; pesquisa externa foi bloqueada deliberadamente. Voz suprimida e
ações substituídas por recusa com receipt negativo do adaptador real. Não
houve mudança de modelo para produzir os resultados.

`conversa_validada/`: 30 turnos/conclusões, 34 HTTP 200, 17 pacotes primários
conferidos, 527 fontes sem drift. Um pedido de Calculadora simulado com receipt
negativo. Tempo acumulado dos turnos: 239,510 segundos, sem alegar benchmark.

| Turno | Fonte esperada | Resultado |
| --- | --- | --- |
| 20, aplicativo antes preferido | `eu prefiro Obsidian` | Citação correta após reparo; categoria implícita segue fora do novo recorte |
| 22, bebida antes recusada | `eu não gosto de café` | Paráfrase primária conferida; fora do novo recorte literal |
| 25, dizer sobre chá | `eu não gosto de chá` | Paráfrase primária com tópico conferido |
| 26, dizer negativo sobre rock | `eu gosto de rock` | Reparo com citação de rock e núcleo explícito conferido |

O reparo do 26 recebeu exatamente duas escolhas: a citação de rock e o limite.
A citação de chá foi excluída pela mesma conferência final que rejeitaria sua
publicação. A fonte não desapareceu do histórico: deixou de ser admissível
como resposta àquela pergunta. A auditoria distingue essa restrição de uma
escolha semanticamente certificada pelo modelo.

`foco_final/`: nova conversa independente de 12 turnos/conclusões, 16 HTTP 200,
seis pacotes primários conferidos, mesmas 527 fontes sem drift. Sem pedidos de
ação ou receipts de efeito. Tempo acumulado: 76,014 segundos.

| Pergunta com distrator mais recente | Fonte entregue e conferida |
| --- | --- |
| `eu falei que uso Obsidian?`, depois de mencionar Blender | `eu uso Obsidian` |
| `então eu mencionei que trabalho no hospital?`, depois de laboratório | `eu trabalho no hospital` |
| `e o que eu disse sobre meu cachorro?`, depois de falar do gato | `Meu cachorro fica em casa.` |
| `e eu falei que uso Blender?` | `eu uso Blender` |

Os quatro passaram por reparo e tiveram `vinculo_consulta.conferido=True` na
revisão final. Nenhum distrator foi publicado como resposta. As duas coletas
somam 42 turnos/conclusões e oito alvos com a fonte esperada. Evidência em
`auditoria_validada.json`, `auditoria_retomada.json`, `auditoria_foco_final.json`,
`auditoria_foco.json` e nas duas transcrições. Não inferir daí correção de toda
conversa livre ou causalidade de cada diferença estocástica entre rodadas.

## Limites preservados e próxima fronteira

O turno 7 da conversa longa terminou em limite de conferência; o 29, de
recapitulação, terminou em limite de tentativas. Não são êxitos conversacionais.
Os turnos de conversa livre também contêm respostas inadequadas que não pedem
retomada explícita. Esses contratos não são declarados corrigidos por este
patch.

Permanecem fora da conferência nova: categorias implícitas, sinônimos, paráfrase
livre da pergunta, elipses, nomes com formas fora da leitura nominal, seleção
temporal entre correções e cobertura de frases adicionais. Presença literal
do tópico não prova que a fonte responde todos os requisitos da pergunta;
igualdade integral pode recusar fonte pertinente com conteúdo adicional.
Nesse limite, não se pode promover `conferido=None` a prova semântica.

Próxima investigação possível: vínculo de categoria ou restrição indireta
entre pergunta e fonte, com evidência independente da seleção da IA; também
permanece separado o contrato de recapitulação. Antes de ampliar, produzir
RED próprio e preservar F1/C5/C7/AUT e as demais famílias do mapa. A falha
demonstrada de chá no lugar de rock foi corrigida no recorte explícito e
validada na composição real; compreensão geral não foi encerrada.
