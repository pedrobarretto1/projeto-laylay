# Reparo de retomada: geração compatível com a conferência — 25/10/2026

O contrato de geração do reparo passou a oferecer realizações que o host
consegue conferir integralmente. A composição instalada conserva essas opções
na autoria compartilhada e rejeita prosa livre, mesclas e comandos. Isso resolve
a divergência de formato entre geração e conferência neste recorte; ainda não
resolve a escolha de uma fonte pertinente à pergunta.

Na conversa real de 30 turnos, três das quatro retomadas-alvo responderam com
a fonte esperada. A quarta perguntou sobre rock e recebeu uma citação sobre
chá. A citação era fiel ao histórico, mas a resposta era inadequada. Não contar
esse turno como êxito conversacional ou compreensão. A fonte de rock estava
disponível entre as opções, como demonstra a auditoria do payload.

## Base, evidência anterior e primeira fronteira

Base congelada: `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree
limpa no início. `resultados_testes/reparo_retomada_conferivel_20261025/baseline.json`
registra estado e hashes de 527 fontes; `fontes_antes/` conserva os dois owners.
Os hashes do candidato anterior nos três owners daquela etapa coincidem com
esta base. O avanço de HEAD não foi tratado como autorização para reaplicar
patch antigo ou atualizar travas cegamente.

O relatório anterior, `RELATORIO_RETOMADA_PESSOA_RELATO_20261024.md`, demonstrou
que as quatro retomadas-alvo terminavam em limite de tentativas: o Qwen recebia
fontes, mas propunha inversões ou paráfrases não conferíveis. O guard correto
retinha a publicação. A nova base mantém esse mecanismo e os 22 testes vizinhos
passaram antes do candidato (`baseline_vizinho.xml`).

Cadeia causal estudada:

```text
consulta ao dizer do usuário
→ perspectiva e fontes presentes
→ núcleo inadequado retido pela qualidade
→ pedido de reparo ainda aceita redação livre
→ modelo propõe forma fora da conferência disponível
→ revisão rejeita
→ limite de tentativas observado
```

A primeira divergência desta investigação está no pedido de reparo, não na
necessidade de remover o guard ou aumentar tentativas. O schema aceitava texto
arbitrário enquanto o revisor só podia conferir certas paráfrases ou citação
integral atribuída. Fontes ausentes e protocolo de autoria errado foram
falsificados na coleta anterior: fontes estavam no payload, a autoria era
`autoria_com_suporte_v2` e os HTTPs eram 200. Isso não certifica qualidade do
conteúdo gerado nem exclui outras falhas em outros turnos.

`contrato_red.xml`: 13 falhas e um controle aprovado, antes de produção.
Os quatro casos centrais falham porque o pacote ainda é aberto, na fronteira
estudada. Não foi um erro de importação ou ausência de fonte.

## Contrato e responsáveis

| Responsabilidade | Owner | Critério |
| --- | --- | --- |
| Qualificar o dizer e gerar realizações literais | `fundamentacao_factual.realizacoes_retomada_usuario` | Mesma perspectiva tipada e ocorrência, consulta retrospectiva pura, sem operação/outro owner histórico; fonte `dialogo:usuario` íntegra, hash e proveniência qualificados |
| Negociar o reparo | `qualidade_comunicacao.montar_pacote_reparo_comunicacao` | Oferecer citação integral atribuída ou limite; admitir somente opções representáveis pelo segmentador canônico, sem truncar fonte |
| Transportar autoria | Codec existente `realizacao_discursiva_v1` composto por `exigir_suporte_no_pacote_autoral` | Enum conservado em `suporte_proposicoes`; reconstrução literal integral, sem mesclar opções; `comandos=[]` |
| Conferir antes de entregar | Qualidade e revisão final já existentes | A proposta deve voltar a passar pela conferência do núcleo; seleção não prova verdade atual, pertinência, causa ou autorização |
| Validar a utilidade nesta coleta | Auditoria com alvos esperados explícitos | Comparar a fonte escolhida com a fonte pertinente de cada pergunta; fonte válida sozinha não equivale a resposta correta |

Não há classificação privada por assunto, nome ou frase. Não se escolhe a fonte
por recência nem se transforma relato em prova externa. Todas as fontes
históricas elegíveis continuam disponíveis, sem ranking novo ou corte textual.
Falas históricas podem incluir perguntas ou instruções: citá-las relata o dizer,
nunca concede autoridade. Alegações normalizadas, fonte atual, autor alheio,
contestação, hash divergente, texto longo e delimitadores incompatíveis não
geram essas citações. Ausência de fonte oferece o limite em vez de reabrir
redação livre. O restante da conversa mantém seus owners existentes.

Princípio reutilizável: a geração deve negociar uma linguagem de saída que o
revisor responsável possa conferir; a composição deve conservar integralmente
essas restrições. Isso beneficia retomadas de qualquer domínio, sem alterar
separadamente música, aplicativos, arquivos ou outras habilidades.

## Candidato mínimo, falsificações e revisão

Produção alterada somente em:

- `mente_laylay/cognicao/fundamentacao_factual.py`;
- `mente_laylay/cognicao/qualidade_comunicacao.py`.

O codec, wrapper de autoria, guard final, modelo, voz, timeout e orçamento
existentes foram reutilizados. Nenhum commit criado. O diff contra as fontes
congeladas está em `candidato_contra_base.patch`; a comparação final de todos
os hashes confirma o escopo.

Um teste composto inicialmente esperava o nome do codec intermediário no HTTP.
O resultado contrariou essa expectativa. O estudo mostrou que o serviço de
modelo o envolve legitimamente em `autoria_com_suporte_v2`, preservando enum e
validador original. Nenhum patch no adaptador foi necessário. O teste agora
confere as restrições reais no HTTP e rejeição no codec composto. A folha HTTP
positiva propõe citação literal esperada; os controles primários apoiados
continuam exigindo suas respostas originais. Não se substituiu o revisor.

A revisão independente encontrou uma borda concreta: fonte com 498/499
caracteres contínuos passa na qualificação literal, mas sua citação não cabe
nas unidades reconstruíveis. Isso abortava também as opções válidas e o
limite. `borda_transporte_red.xml` reproduziu duas falhas e 16 controles.
A montagem do pacote agora consulta `segmentar_realizacao_autoral`, sem cortar
nem reescrever a fonte. O controle com 499 caracteres e espaços conserva a
citação; os dois contínuos conservam o limite. Revisão posterior confirmou
a resolução e não apontou bloqueio restante (`revisao_independente.json`).

`contrato_final.xml`: 40 testes aprovados, incluindo as duas factories,
negativos de proveniência/autoridade, fonte ausente, mescla, comandos e as
bordas de transporte. Na factory positiva, quatro inversões provocadas
recebem quatro citações corretas, uma publicação por turno; os quatro
controles apoiados continuam intactos. A factory negativa retém as propostas
inadequadas. Sem áudio ou efeitos reais.

## Composição real com Qwen e limites abertos

`conversa_validada/`: 30 turnos, 30 conclusões, 37 HTTP 200, 17 pacotes primários
conferidos e 527 fontes sem drift durante a coleta. Mesmo
`qwen3:4b-instruct`/Ollama local; perfil isolado, voz suprimida e executor
substituído por recusa com receipt negativo real do adaptador. Um pedido de
Calculadora foi simulado; nenhuma aplicação foi aberta. Tempo acumulado dos
turnos: 280,325 segundos, sem inferir benchmark. Pesquisa externa foi
deliberadamente bloqueada; esta coleta não valida explicações com fontes web.

| Turno-alvo | Resultado observado | Conferência de utilidade |
| --- | --- | --- |
| 20, aplicativo antes preferido | Reparo: `Você contou: «eu prefiro Obsidian».` | Fonte esperada |
| 22, bebida antes recusada | Primária: `Você disse que não gostava de café.` | Paráfrase conferida, fonte esperada; não atribuir o acerto primário ao novo reparo |
| 25, dizer sobre chá | Reparo: `Você contou: «eu não gosto de chá».` | Fonte esperada |
| 26, dizer sobre não gostar de rock | Reparo: `Você contou: «eu não gosto de chá».` | Fonte fiel, assunto errado; falha conversacional |

No recorte-alvo: quatro núcleos com fonte conferida, três com fonte pertinente.
Entre os três reparos fechados desses alvos, dois pertinentes e um inadequado.
O alvo de rock estava no enum do último reparo; falta de fonte foi falsificada
nesse caso. Não houve limite de tentativas nesses quatro alvos. Isso é uma
observação desta coleta, não uma taxa geral de acerto ou comparação causal de
todos os resultados estocásticos com a rodada anterior.

Cinco reparos fechados foram auditados no total (7/16/20/25/26). Todos
preservaram as opções e a ausência de comandos; o 7 escolheu o limite e o 16
citou rock ao perguntar o gênero anterior ao jazz. A resposta primária do 7
veio malformada e terminou por comprimento: HTTP 200 não significa autoria
válida. A recapitulação do 29 terminou em limite de tentativas. Essas falhas
não são declaradas corrigidas pelo novo contrato.

A coleta inicial `conversa_real/` foi interrompida apenas nos processos desta
sonda quando surgiu a borda de tamanho. Seu material parcial foi preservado;
não integra os números finais. `auditoria_validada.json`,
`auditoria_retomada.json` e `TRANSCRICAO_VALIDADA.md` preservam resultados e
separam conferência da fonte de pertinência à pergunta.

Regressão de 95 módulos: 2.328 testes aprovados, 14 skips e as mesmas nove
falhas anteriores, sem erro ou falha nova. Os 30 subtests adicionais não
falharam. Comparação por IDs em `comparacao_falhas_anteriores.json`; comando,
log e XML preservados. Permanecem o caso antigo de Calculadora e oito
expectativas antigas de pacote/reserva. O teste de import deselecionado nessa
suíte passou separadamente no root isolado (`import_isolado.xml`).

Próxima fronteira demonstrada: escolher e conferir a relação entre a pergunta
e o dizer histórico pertinente, preservando negação, correções e mudanças ao
longo da conversa. O owner não pode tomar a escolha ou rótulo da IA como prova.
Antes de novo patch, demonstrar o primeiro RED dessa relação e falsificar
ausência de fonte, perda no transporte e interferência de outra ocorrência.
Consultas pessoais gerais, atos mistos, causalidade e recapitulação continuam
abertos nos seus próprios contratos. Preservar F1/C5/C7/AUT e o mapa histórico;
não fundir essas raízes por semelhança de sintomas.
