# Conversa casual — autoria, comandos e obrigação de evidência

## Escopo e evidência histórica

Sessão `20261030T021917Z-4f76db4d`, na ponte em Documents/Codex/2026-10-28/ch:
16 entradas,16 respostas protocoladas,18 emissões bem-sucedidas de modelo,
encerramento normal, sem queda da sessão. Estabilidade de entrega não significa
que todas as16 respostas eram pertinentes ou factualmente sustentadas.

Pedro mantém os testes de conversa. Aqui foram usados os registros preservados,
propostas HTTP fixas e o construtor real do adaptador/root instalado, em perfis
privados auditados. Nenhum Qwen novo, conversa espontânea, voz ou efeito externo.
Uma proposta controlada demonstra o percurso do contrato, não capacidade
espontânea do modelo ou verdade das afirmações da ficção.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, main, worktree suja preservada.
As538 fontes e estado Git anteriores ao candidato estão em
`resultados_testes/papo_casual_20261030/base` e `baseline.json`.
Comparação com o snapshot da sessão:537 fontes iguais; somente
`validacao_contrato_fala.py` já diferia por uma correção anterior que distingue
“só falar” de alegação de incapacidade. Essa mudança não foi sobrescrita nem
contabilizada como parte deste candidato. `.gitignore` e alterações paralelas
também foram preservadas. Não houve commit.

Durante a validação apareceu outra alteração concorrente nesse mesmo arquivo:
restringe atribuições como “minha única capacidade é só conversar”. A auditoria
abortou ao detectar o oitavo delta. O baseline não foi atualizado: hash e diff
concorrentes foram registrados separadamente em `auditoria.json`, com guarda
contra nova mudança. A revisão independente confirmou que não escreveu esse
arquivo. A comparação final inclui candidato com a versão congelada dessa
validação, para verificar que o benefício não depende do delta paralelo.

O corpo pós-codec de `papo-004` foi truncado no journal em1.208 caracteres:
não se inventou seu restante. O replay desse turno usa uma proposta controlada.
Nas emissões V5 completas, `partes` pós-codec foram recompostas integralmente
em `texto`, sem modificar conteúdo, ordem ou referências. A rota principal de
`papo-004` não negociava V5: a fixture final fornece `fala` no formato legado
que ela realmente pede. A primeira coleta sem essa distinção provocava reparo
artificial; foi preservada e não serve como prova de defeito do codec.

## Famílias causais e donos dos contratos

| Evidência / vínculo histórico | Primeira divergência demonstrada | Owner / correção |
| --- | --- | --- |
| `papo-004` — declaração da própria iniciativa | “deixa eu mudar de assunto” virava comando delegado à Laylay | `modalidade_turno`: permissiva conserva agente explícito; no clítico `me`, confere infinitivo lexical para não confundir beneficiário com agente. Ordem coordenada independente mantém seu próprio ato |
| `papo-008` — contraste com sujeito elidido | Vírgula separava “não muda X, muda Y” e promovia forma indicativa homógrafa a imperativo | `morfologia_oracao`: predicado repetido em contraste mantém dependência; a morfologia não concede autoridade. Forma formal, cortesia e fronteira forte preservam ordens independentes |
| `papo-005/009` — admissão histórica | `porque` declarativo ou “levou dez mensagens” combinavam com atribuição passada de outra oração | `referencias_linguagem`: consulta causal precisa de vínculo dentro do recorte; elipse causal explícita pode recuperar o antecedente imediato. Perguntas reais de motivo continuam exigindo fonte |
| `papo-015` — falsa atualidade e aviso de fonte | Domínio “presidente” da história, “ainda” de outro trecho e interrogação social eram somados como consulta atual | `fundamentacao_factual`: usa fontes dos atos canônicos, preservando relação entre confirmação elíptica e sua proposição. Retomada da fala não exige atualização externa; menção a PC/Xbox sem afirmação não vira disponibilidade |
| `papo-008` — enquadramento social independente | “você tá” e “bem” de “pensando bem” formavam falsamente estado pessoal | `interpretacao_social`: predicado, modificadores e estado pertencem ao mesmo intervalo; perífrase reflexiva de sentimento permanece legítima |
| `papo-004` — vínculo de autoria em entrada longa | `texto_usuario` do plano e do alinhador era cortado em500 caracteres; suporte capturado pelo runtime usava a pergunta integral | `plano_turno` e `orquestrador_turno_runtime`: identidade integral não é projeção de prompt/telemetria. Pedidos com mesmo prefixo e final diferente não recebem o mesmo suporte |
| Controle de F1 — ausência de evidência atual | Atualidade verdadeira sem tema resolvido não construía fundamentação e perdia obrigação antes da revisão | `orquestrador_turno_runtime`: ausência atravessa o construtor canônico com exigência recente preservada. Falha de lookup não dispensa fonte nem autoriza afirmação do modelo |

Os itens são mecanismos separados; não se renomeiam as raízes anteriores nem
se contabiliza cada turno como uma raiz nova. A continuação de F1 trata somente
da perda de obrigação de atualidade no caso sem tema; F1 global continua aberta.

O lookup textual mantinha limite de oito fontes e300 caracteres, adequado aos
consumidores autorais anteriores, mas insuficiente para conferir o contexto da
despedida com dez segmentos e o ato longo de `papo-009`. Os limites padrão foram
preservados. Somente o leitor de contexto solicita32 fontes/até4.000 caracteres.
Quando a visão curta não basta, reutiliza `ContratoExplicativoAto.texto` integral
já capturado pelo host e exige correspondência no texto original. Não adivinha
a cauda nem amplia o schema de autoria ou autorização operacional. Fonte
adulterada conserva a leitura factual conservadora.

## Falsificações e sequência das provas

- Os falsos comandos e a falsa finalidade histórica foram reproduzidos em
  funções puras, sem transporte, modelo, executor ou receipt. Isso falsifica
  indisponibilidade do modelo como causa dessas decisões iniciais.
- Repetir apenas a despedida numa sessão limpa não reproduziu o aviso. Repetir
  os três antecedentes reais antes dela reproduziu, inclusive com uma resposta
  adequada nova. Não é necessário culpar uma referência inventada pela proposta:
  aquela emissão declarava fontes vazias.
- Os pedidos reais “deixe a luz ligada”, “abra o navegador” e consultas atuais
  em outros domínios continuam possuindo seus próprios requisitos; a correção
  não depende do nome dos personagens ou do assunto aspirador.
- Um teste negativo com presidente atual expôs a perda anterior de evidência
  quando não havia tema. A expectativa de rejeitar o fato sem fonte foi mantida
  vermelha até a composição transportar essa obrigação; não se mudou o teste
  para aceitar a afirmação nem se ofereceu uma fonte simulada para escondê-la.
- A revisão de autoria continua recusando fonte interna como prova externa,
  biografia ou efeito não observado; não houve remoção de revisão/codec/receipts.

RED inicial:23 falhas e16 controles. Atualidade por ato:cinco falhas/cinco
controles, com RED posterior para os limites de fontes integrais. Outros REDs
preservam identidade truncada, predicado social e as contraprovas da revisão.
Artefatos XML/logs estão no diretório desta investigação; não apagar execuções
vermelhas por causa de um resultado posterior.

## Revisão independente e regressão

Uma revisão de código independente, somente leitura, apontou seis mecanismos
de regressão no primeiro candidato: elipse causal nominal/imperativa, consultas
com “motivou”, confirmação elíptica factual, ordem coordenada após permissiva,
clítico beneficiário e perífrase reflexiva de sentimento. Os14 REDs derivados
foram preservados em `red_revisao_independente_ampliado.xml`. As correções foram
feitas nos mesmos owners gramaticais; nenhuma exceção por frase histórica.

Uma segunda passagem encontrou variantes acentuadas/reflexivas de permissiva,
elipses com conector e confirmação copular negativa/deítica. Os REDs estão em
`red_variantes_revisao.xml` e `red_permissiva_reflexiva.xml`. O leitor preserva
acentos antes da morfologia; clíticos pertencem ao complemento do infinitivo.
Conector discursivo é removido pelo helper canônico na elipse causal. A pergunta
confirmatória dependente tem leitor compartilhado próprio, sem fornecer
consentimento operacional. A última revisão passou25 controles puros e não
deixou finding aberto nesse recorte.

A primeira ampla teve uma falha legítima em
`test_reparo_historico_aprovado_conclui_sem_pedir_terceira_chamada`:
“qual seria um título divertido para a nossa conversa de hoje?” recebia obrigação
recente por “hoje/última”. O controle F1 expôs essa classificação anterior
incorreta; não foi removido nem o teste enfraquecido. O owner factual distingue
pergunta de nomeação com alvo explicitamente pertencente ao diálogo, incluindo
convite introduzido por dois-pontos, de consulta temporal externa. Os domínios
mutáveis continuam prevalecendo. REDs canônicos e controles externos estão em
`red_nome_conversa.xml`/`red_moldura_nomeacao.xml`.

Foco final:132 aprovados em sete módulos (126 nos seis novos e seis no legado
do primeiro reparo), incluindo nove
composições pelo adaptador/root reais. Cinco respostas adequadas aos turnos
históricos foram publicadas em uma chamada, sem comando, consulta histórica
ou bloqueio de orçamento indevidos. A despedida foi conferida com sequência
anterior e tema residual presentes. Controles de APP_OPEN/MEDIA_CONTROL com
receipt proposto não executam nem confirmam efeito. Pergunta causal real e
pergunta factual real depois da história continuam limitadas por suas fontes.

A comparação instalada com sete owners congelados, carregados somente em
memória, está em `comparacao_instalada_final.json`; a primeira comparação foi
preservada em `comparacao_instalada.json`. O alvo de `papo-004` era recusado
por identidade/autoridade na base; `papo-005/009` ganhavam obrigação histórica;
`papo-008` conservava autoridade indevida; `papo-015` recebia aviso de fonte.
O candidato publica as cinco propostas adequadas em uma chamada. Não é replay
literal da escolha espontânea do Qwen nem garantia de que escolherá essas frases.

Primeira ampla preservada em `regressao_red_1`:1 falha e4.724 aprovados,
nenhum ID anterior ausente. Registra o estado anterior aos últimos ajustes da
revisão; não é prova do candidato final.

Regressão ampla relevante final:191 módulos,4.764 aprovados,14 pulados,
um desmarcado pelo filtro anterior,um xfail e30 subtestes aprovados, em640,02s.
Exit0,nenhuma falha/erro e nenhum ID anterior ausente. Comando/XML/resumo estão
em `regressao_comando.json`, `regressao.xml` e `regressao_resumo.json`. Mantido
o filtro anterior, inclusive a exclusão já existente de
`test_composicao_principal_injeta_rota_que_respeita_perfil_explicativo`.
Não é a suíte completa do projeto nem validação espontânea do Qwen.

A comparação final possui15 percursos:cinco com owners da base,cinco com o
candidato e cinco com o candidato usando a validação congelada anterior ao
delta paralelo. Nos dez percursos candidatos as cinco respostas pertinentes
coincidem, são publicadas em uma chamada sem degradação, autorização ou efeito.
Na base reaparecem o aviso de fonte (004/015), a obrigação histórica (005/009)
e a falha do caminho operacional indevido (008). A diferença não depende da
alteração concorrente. Auditoria final:538 fontes,sete owners do candidato,
uma alteração concorrente separada e530 fontes intactas; baseline/HEAD mantidos.

## Escopo final e limites observados

Produção alterada: sete fontes existentes sob `mente_laylay/cognicao/`:
`modalidade_turno.py`, `morfologia_oracao.py`, `referencias_linguagem.py`,
`fundamentacao_factual.py`, `interpretacao_social.py`, `plano_turno.py` e
`orquestrador_turno_runtime.py`. Outras530 fontes preservadas por hash; uma
alteração concorrente em `validacao_contrato_fala.py` isolada na auditoria.
Sem novo módulo de produção, persona, modelo, orçamento, ponte, voz, executor
ou commit. Diff exclusivo e auditoria em `producao.patch`/`auditoria.json`.

Poesia, humor e tamanho não foram uniformizados. A observação de Pedro sobre
timing é válida como objetivo de produto: uma reação breve pode caber na piada,
uma elaboração longa pode caber no debate. Estes testes não medem espontaneidade,
qualidade literária ou memória autônoma entre sessões.

Inspeção de `autoria_conversacional` e da rota de opinião em `conversa_natural`
mostra instruções já existentes de naturalidade, deboche quando combinar e,
no reparo, de evitar poesia desnecessária. Isso falsifica a explicação simples
de que faltaria apenas acrescentar “seja natural” ao prompt. Não prova quais
instruções o Qwen privilegiou nesta sessão. Antes de alterar timing/persona,
conferir o pedido efetivamente enviado, o contrato do ato e o reuso temático;
não converter a preferência por humor em limite global de palavras.

A coleta também mostrou um tema lexical inadequado (“Ter Companhia”) vindo do
retrato/retrieval. A opinião curta adequada passa; uma elaboração com afirmação
adicional ainda pode encontrar o limite factual daquele tema. Não se dispensou
essa revisão ou certificou uma alegação nova para obter fluidez. A pertinência
de temas/fontes e a leitura de respostas alternativas como “os dois” permanecem
fronteiras distintas, ligadas aos owners existentes, sem declarar resolução
universal das explicações livres, da memória ou da compreensão da Laylay.

Não liberar automaticamente a proposta histórica de `papo-015`: ela responde
como se a pergunta futura já tivesse sido feita e inventa continuidade do cargo.
A prova usa despedida pertinente e mantém separado esse problema de autoria.
