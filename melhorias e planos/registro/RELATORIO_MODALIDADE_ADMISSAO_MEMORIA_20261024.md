# F1/C7 — modalidade canônica na admissão da memória, 24/10/2026

## Base e raiz demonstrada antes do candidato

HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, branch `main`, worktree
preexistente preservada. Baseline com status e 527 hashes em
`resultados_testes/modalidade_admissao_memoria_20261024/baseline.json`.
Owners estudados e congelados: registro_semantico e contexto_compartilhado.

A etapa anterior preservou a fonte literal no coordenador. Nesta fronteira,
`Qual aplicativo eu prefiro`, `Qual gênero eu gosto` e `Como eu trabalho no
laboratório` chegam à factory como modalidade pergunta. O registro semântico
usa pontuação e um léxico de imperativos para recusar alegações, mas não recebe
essa modalidade. Sem '?', admite pergunta como opinião/relato do usuário.

`composicao_baseline.json` captura as três admissões antes do HTTP; a folha HTTP
é controlada, sem voz e sem efeitos. `contrato_red_confirmado.xml` contém 12 REDs
causais e 4 controles. O primeiro XML inclui erro de serialização da sonda;
ele foi corrigido antes de contar a prova da factory, sem alterar produção.

Falsificações: não é perda atual de texto/pontuação; o texto já chega literal.
Não exige resposta inventada pela IA: ocorre antes do primeiro HTTP. Também
não é falha do classificador nesses exemplos: ele produz pergunta. Declarações
legítimas no mesmo caminho são controles positivos.

## Contrato e escopo do candidato

| Responsável | Contrato |
| --- | --- |
| Classificador canônico | Decide modalidade; não haverá parser interrogativo privado na memória. |
| Contexto compartilhado | Encaminha a classificação do usuário ao registro sem transformá-la em prova ou autorização. |
| Registro semântico | Pergunta canônica não entra como alegação. Reutiliza classificação só para fonte literal coincidente. Sem vínculo ou em frase distinta, consulta o mesmo classificador canônico. |
| Histórico literal | Conserva a mensagem, inclusive perguntas; ausência de alegação não elimina fonte de conversa. |
| Execução | Contexto e modalidade não substituem autorização nem receipt; comandos propostos permanecem propostas. |

Aplicação na porta comum de alegações, para usuário e Laylay. A classificação
do usuário não se aplica à fala da IA. A segmentação em frases já existente
continua; declaração e pergunta separadas têm admissões independentes. Não
há remoção de registros antigos nem mudança de modelo, voz ou configuração.

Limites observados antes do patch: `Você acha que eu gosto de rock` ainda é
classificada como conversa; certas condições são deliberação e algumas mesclas
sem pontuação não são segmentadas. São fronteiras anteriores distintas. Esta
correção não pode certificar a compreensão desses casos nem a conversa geral.

## Candidato e revisão

Produção alterada somente em `registro_semantico.py` e
`contexto_compartilhado.py`. O contexto encaminha `turno_usuario`; a porta comum
rejeita pergunta conforme modalidade canônica. Não se alterou o classificador,
coordenador, executor, voz, modelo ou configuração. Não houve commit.

A revisão independente encontrou uma regressão do primeiro candidato: texto
do turno truncado a 500 caracteres podia coincidir com a primeira declaração
de um turno misto e fazê-la herdar a modalidade pergunta do todo. Reproduzida
em `revisao_red.xml` antes do ajuste. O vínculo agora só reutiliza fontes
menores que o limite; no limite ou além dele, consulta o mesmo owner canônico.
Revisão confirmou 499/500/501 caracteres, sem novos bloqueios concretos.

As coletas intermediárias foram interrompidas antes de modificar produção;
foram preservadas em `conversa_validada/` e `regressao_ampla.log`, sem contar
como validação final. `coletas_intermediarias.json` registra o motivo.

`contrato_final.xml`: 136 GREEN, incluindo 18 casos novos e os contratos
vizinhos de fonte literal, registro semântico, decisão única, pré-fluxo e
continuidade. `composicao_baseline.json`/`composicao_candidato.json` mostram o
mesmo defeito antes do HTTP em três domínios e a recusa da admissão com o
candidato, preservando a mensagem no histórico. Ambas usam HTTP controlado,
sem executar a proposta de abrir Calculadora. `composicao_final.json` repete a
prova depois do ajuste do vínculo de 500 caracteres e registra hashes dos owners.

`contrafactual_final.xml`: com apenas os dois owners congelados carregados em
memória, os testes finais leves reproduzem 12 REDs, 5 controles e uma factory
deselecionada (ela usa subprocesso próprio). Não foi revertida produção em
disco. A validação do import no root isolado também passou: `import_isolado.xml`.

## Qwen real, regressão e limites finais

Coleta final `conversa_real/`: 30 turnos e 30 conclusões, 34 HTTP 200, 17 pacotes
primários com fontes conferidas e 527 fontes sem drift. Mesmo modelo configurado
`qwen3:4b-instruct` em Ollama local. Persistência isolada; voz suprimida; um
pedido de Calculadora recebeu receipt negativo de simulação, sem efeito real.
Tempo acumulado dos turnos: 216,725 segundos, sem inferir benchmark de latência.

`auditoria_modalidade.json` comprova seis consultas canônicas sem interrogação
mantidas como mensagens literais, sem alegação atribuída ao usuário e sem
autorização. Cinco declarações legítimas de controle foram preservadas,
incluindo a declaração de jazz no turno misto. `auditoria.json` e
`TRANSCRICAO.md` registram a coleta e seus limites; resposta da IA não é usada
como prova da verdade das declarações.

Nesta coleta final, os turnos 5/6/7 recuperam Obsidian, rock e café. Ainda houve
falhas próprias da resposta livre: no turno 9 a autora descreve experimentos
em primeira pessoa sem fonte para essa atividade; o turno 15 repete o texto
misto sem responder sua pergunta; o turno 19 não resolve o pronome para Dora;
no turno 29 a recapitulação esgota tentativas. Essas observações não anulam a
prova da admissão, nem são consideradas corrigidas por ela. As recusas das
consultas iniciais da coleta intermediária interrompida não foram atribuídas
à coleta final. Não foi realizado outro patch para esses sintomas.

Regressão ampliada de 92 módulos: 2.264 GREEN, 30 subtests GREEN, 14 SKIP, uma
deseleção de import e as mesmas nove falhas anteriores. Comando e resultados em
`regressao_comando_final.json`, `regressao_final.log` e `regressao_final.xml`.
`comparacao_falhas_anteriores.json` compara os nomes com a etapa anterior:
nenhuma falha nova nesse conjunto. Não é uma suíte inteiramente verde.

Falhas preservadas: rota MUSIC_SEARCH para a variação antiga de abrir
calculadora (um caso) e expectativas anteriores de pacote/reserva de saída em
`test_geracao_limite_sem_estado.py` (oito casos). As contraprovas prévias estão
em `resultados_testes/respostas_prazos_20261024/relato_composto/falha_vizinha_baseline.xml`
e `resultados_testes/base_canonica_rota_rapida_20261024/vizinho_orcamento_baseline.xml`.
Nenhum teste existente foi enfraquecido para ocultar essas falhas.

Próxima fronteira observada: fidelidade de respostas livres com histórico
disponível, incluindo troca de perspectiva e respostas incompletas. Antes de
corrigir, localizar a primeira divergência entre fonte, seleção, autoria e
revisão. Também continuam abertas as modalidades não reconhecidas e condições;
não misturar esses owners com a admissão de pergunta já reconhecida.

`entrega.json` registra escopo e verificações finais;
`candidato_contra_base.patch` contém somente a diferença contra os owners
congelados. Duas fontes de produção alteradas entre 527 conferidas, preservando
todas as alterações anteriores da worktree. Nenhum commit ou migração de memória.
