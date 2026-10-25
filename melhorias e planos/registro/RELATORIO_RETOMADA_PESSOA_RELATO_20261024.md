# F1/C7 — atribuição e apoio no núcleo da retomada do usuário, 24/10

## Base e raiz antes do candidato

HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, main, worktree preservada.
Baseline com status e 527 hashes em `resultados_testes/retomada_pessoa_relato_20261024/`.
Owners congelados: fundamentacao_factual, qualidade_comunicacao e
revisao_suporte_autoria. Nenhum arquivo anterior foi restaurado em disco.

Consultas de relato composto/negado eram corretamente reconhecidas por
pedido_consulta_fala_usuario, com PerspectivaEnunciador tipada vigente. Fontes
do usuário estavam no plano e no histórico. O rascunho da IA, em primeira pessoa,
ficava fora da gramática limitada que confere relatos atribuídos. A ausência de
conferência não impedia o núcleo da resposta de passar pela qualidade/revisão.

Primeira fronteira autoritativa incorreta: admitir núcleo não conferido em
resposta a uma consulta canônica ao dizer do usuário. Não se exige que toda
proposta do Qwen seja correta; proposta não é prova. Adicionar frases ou verbos
ao detector de inversão não comprovaria o apoio no histórico.

`composicao_baseline.json`: quatro rascunhos invertidos e quatro controles
atribuídos publicados pela mesma factory/HTTP controlado, com fontes no plano.
Isso falsifica falta de fonte, falha de reconhecimento da consulta e perda do
tipo de perspectiva como causas necessárias. Mudar para segunda pessoa sem
fonte também não comprova o relato; haverá controle de autor/hash/contestação.

As primeiras execuções unitárias não alinhavam os atos do plano com a produção:
o helper didático usado não montava atos de pergunta. `contrato_red_canonico.xml`
mostra a guarda abortando essa montagem, antes de produção ser alterada. O
helper passou a encaminhar os atos do classificador canônico; somente
`contrato_red_confirmado.xml` e a factory são usados como prova causal.

## Contrato e responsáveis

| Owner | Responsabilidade |
| --- | --- |
| Leitor canônico de consulta | Reconhecer o dizer do próprio usuário; não duplicar listas de confirmação ou frases. |
| Fundamentação factual | Conferir atribuição e apoio do núcleo com a gramática de paráfrases existente ou citação integral de fonte qualificada. Fora do recorte não é aprovação. |
| Qualidade compartilhada | Impedir publicação e pedir reparo quando o núcleo exigido não foi conferido. Reutilizar a seleção de histórico e preservar fontes como dados do usuário. |
| Revisão final | Conferir novamente após reparo; reparo da IA não constitui prova. Se não houver núcleo conferível, publicar limite honesto, sem dizer falsamente que o usuário nada contou. |

Escopo: pergunta canônica simples ao dizer do usuário, vinculada à ocorrência,
sem execução ou outro owner histórico ativo. Declarações comuns, perguntas sobre
a própria Laylay, recapitulações compostas e efeitos operacionais não serão
reinterpretados por este contrato. A conferência do núcleo não aprova afirmações
adicionais; elas continuam nos revisores existentes. Citação não certifica
pertinência livre, verdade atual ou efeito. Nenhuma troca de modelo/voz/config.

## Candidato e provas focadas

Produção alterada somente nos três owners congelados. A validação já existente
da fonte pessoal foi extraída para uma função comum, preservando autor,
proveniência, estado, tamanho e hash, para reutilização na citação. Não há
substituição textual de eu por você nem novos verbos/frases de preferência.

`contrato_final.xml`: 117 GREEN, incluindo 22 novos casos e os vizinhos de
perspectiva, preferência com fonte e paráfrase histórica. `contrafactual_final.xml`:
somente os três owners congelados em memória voltam a produzir 12 REDs e 8
controles; as duas factories são deselecionadas porque usam subprocesso próprio.
Nenhum arquivo em disco foi revertido para obter o RED.

`composicao_baseline.json`: oito emissões controladas; quatro inversões e quatro
controles apoiados publicados. `composicao_candidato.json`: inversões retidas,
controles mantidos. Quando a folha HTTP continua oferecendo a mesma inversão
no reparo, há emissão observada de limite de tentativas. A hipótese de protocolo
incorreto foi falsificada: principal e reparo negociam autoria_com_suporte_v2.
Não houve mudança de produção para ocultar esse resultado.

`composicao_reparo_positivo.json`: na mesma composição, apenas a folha de geração
passa a oferecer resposta apoiada no reparo. Cada inversão exige dois HTTPs
(principal e reparo) e entrega uma resposta correta com a fonte. Cada controle
já apoiado usa um HTTP e permanece intacto. O revisor não é simulado. Sem áudio,
executores ou confirmação falsa de efeito.

A revisão independente dos três diffs não encontrou bloqueio concreto e
confirmou 20 testes leves (duas factories excluídas). Ressalvou corretamente
que núcleo conferido não é cobertura integral, citação não prova pertinência
livre e gramática restrita não certifica paráfrase arbitrária. Fontes de outro
autor, hash inválido, contestação, outra ocorrência e dicionário proposto pela
IA não fornecem a conferência solicitada.

## Qwen real, regressão e fronteira que continua aberta

`conversa_real/`: 30 turnos e 30 conclusões, 38 HTTP 200, 17 pacotes primários
conferidos, 527 fontes sem drift. Mesmo `qwen3:4b-instruct`/Ollama local;
persistência isolada, sem voz ou efeitos reais. Um pedido de Calculadora teve
receipt negativo simulado. Tempo acumulado: 272,382 segundos, sem inferir
benchmark geral. `auditoria.json`/`TRANSCRICAO.md` preservam a coleta.

As quatro retomadas-alvo (20/22/25/26) deixaram de publicar as inversões, mas
TODAS terminaram em limite observado de tentativas: zero dessas quatro obteve
resposta apoiada concluída. `auditoria_retomada.json` mantém essa contagem, sem
rotulá-la como êxito conversacional. A correção do bloqueio não é uma prova de
melhora da autoria livre ou de compreensão geral.

O estudo dos HTTPs confirmou as fontes de Obsidian, café e chá no payload do
reparo, com papéis de usuário. Isso falsifica falta necessária de fonte no
reparo nesta coleta. O Qwen ainda retornou primeira pessoa, concordância errada
ou premissa não apoiada. O próximo pedido excedeu o orçamento já existente;
não houve HTTP indisponível, aumento de timeout ou aumento de tentativas.
O limite observado comunica a falha sem converter a proposta em prova.

Continuam abertos: consultas pessoais sem referência explícita ao dizer (5/6),
causa pessoal inventada (14), turno misto (15), autorreferência musical (23) e
recapitulação que atribui desgosto por rock contra a fonte (29). Não foram
incluídos em outro patch nem tratados como corrigidos por este guard.

Próxima fronteira: por que a autoria de reparo, mesmo com fonte, não produz um
núcleo conferível; estudar negociação de uma realização apoiada e útil, sem
adotar rótulo/seleção da IA como prova de pertinência ou verdade. A presença
dos dados e o cumprimento do protocolo não bastam para inferir compreensão.

Regressão de 94 módulos: 2.310 GREEN, 30 subtests GREEN, 14 SKIP, uma deseleção
de import e as mesmas nove falhas anteriores. `comparacao_falhas_anteriores.json`
confere IDs com a etapa anterior, sem falha nova nesse conjunto. Comando e saída
em `regressao_comando_final.json`, `regressao_final.log`, `regressao_final.xml`.
O import deselecionado passou no root isolado (`import_isolado.xml`).

As nove falhas anteriores permanecem: um caso da rota de calculadora e oito
expectativas de pacote/reserva de saída. Contraprovas prévias em
`resultados_testes/respostas_prazos_20261024/relato_composto/falha_vizinha_baseline.xml`
e `resultados_testes/base_canonica_rota_rapida_20261024/vizinho_orcamento_baseline.xml`.
Não houve enfraquecimento de testes para ocultá-las, nem alegação de suíte toda
verde. `entrega.json` consolida escopo/hashes; `candidato_contra_base.patch`
contém apenas os três owners desta etapa. Nenhum commit ou migração.
