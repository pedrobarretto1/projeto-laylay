# Pendências da regressão — diagnóstico e candidatos por raiz, 30/10

Base Git1197daf, branch codex/correcao-autoria-conversa-20261030. A correção
anterior do exemplo citado integral já estava na worktree e foi preservada.
Baseline/44ocorrências por ID em resultados_testes/pendencias_44_20261030.
As14falhas/30erros não são44raízes. Nenhum ID histórico deve desaparecer.
Diretório absoluto dos artefatos desta etapa:
`C:/Users/pbarr/.codex/worktrees/publicacao-conversa-segura/laylay/resultados_testes/pendencias_44_20261030`.

## Exportação diagnóstica de fontes tipadas

Trinta erros de setup e a falha de composição social ocorriam no json.dumps
final dos coletores. O cenário já passava por componentes reais; objetos
FonteCapacidadesTurno/PerspectivaEnunciador possuem identidade que não deve ser
achatada para alimentar produção. Não mudar os DTOs ou sua aceitação tipada
para tornar um relatório exportável.

Candidato somente nos testes: observacao_tipadas.py usa projeções explícitas
para_prompt dos dois tipos, identificadas como observação; rejeita novos tipos
ou subclasses e não exporta campos secretos por asdict/default=str. Planos são
exportados apenas nos campos usados pela prova. Fontes nativas continuam no
runtime, nunca são reconstruídas dos dados observados.

Coletores de correlação, erro próprio, recomendação e reação social reutilizam
perfil privado/auditoria antes do import da aplicação, sem rede, processos,
gravação externa ou voz. Folha AppOpener é substituída antes de seu import.
O RED herdado anterior ao reforço do isolamento não prova ausência de efeitos
do bootstrap antigo. Provas finais isoladas:76aprovações/6falhas,zero erros
de exportação;75aprovações nos demais coletores+controles. Os seis resultados
negativos restantes revelam a admissão nominal abaixo, antes encoberta pelo
erro de relatório. Não se alteraram suas expectativas para esconder o RED.

## Apoio pessoal em mensagem com atos distintos

Entrada “estou cansado, pode me recomendar um filme?” chega com declaração e
pergunta distintas na segmentação canônica. O contrato exige acolher o estado;
o revisor de atribuição descartava TODA mensagem com interrogação e vetava o
próprio acolhimento. Primeira fronteira: seleção da fonte, não estilo/modelo.

Owner afirmacoes_interlocutor reutiliza a segmentação da mensagem real, não
rótulos propostos pelo plano/modelo, para recuperar a declaração literal.
Hipótese, citação, pergunta, terceira pessoa e causas/qualificações adicionais
não sustentam a atribuição. A leitura compartilhada de pergunta confirmatória
preserva sua dependência: “estou cansado, será/não é/você acha?” não declara
certeza. Não existe certificação factual, memória persistente ou autoridade.

RED7/9controles com fonte nativa; protótipo anterior de teste sem contrato
tipado não alcançava owner e foi corrigido antes do patch. Depois controles
adicionais revelaram quatro perguntas elípticas; REDs preservados. A solução
usa o leitor compartilhado existente, não uma exceção por pergunta histórica.

Revisão independente demonstrou ressalvas intermediárias e novas caudas de
dúvida. O candidato inicial por atos podia amputá-las; foi restringido ao
escopo demonstrável: cada enunciado sem pergunta conserva o predicado inteiro;
no mesmo enunciado interrogativo, só declaração+pergunta autônoma em dois
segmentos recebe projeção. Três ou mais segmentos não certificam o núcleo,
pois o intermediário pode qualificá-lo. Não é parser semântico universal.
Perguntas confirmatórias são lidas pelo owner compartilhado: cópula modal,
alternativa negativa e negativa com verbo finito sem complemento permanecem
dependentes, sem criar consentimento ou certeza.

## Estado discursivo não é efeito de recurso

“Entendi, o assunto continua aberto” era lido como resultado operacional sem
receipt. O adjetivo de estado não basta para atribuir um recurso: o sujeito
nominal discursivo explícito pertence à conversa. O guardião reconhece esse
papel local no predicado; arquivo chamado assunto, nomes qualificados ou
outro estado/efeito na continuação continuam exigindo evidência. Nenhuma
ação é executada e nenhum sucesso físico é certificado por essa classificação.

RED válido12/7controles; primeiro teste usava toda resposta como fonte e
produzia verde acidental, corrigido e preservado como dado de diagnóstico.
Estado+apoio pessoal+vizinhos:254aprovados, incluindo duas composições com
HTTPfixo, publicador/root reais, sem voz/efeitos.

A revisão também encontrou predicado operacional elíptico depois do sujeito
discursivo (“e o Opera também”). A dispensa agora exige final da oração após
o predicado; coordenação/complemento não distribuído conserva a exigência de
evidência. REDs de revisão preservados em red_revisao_root.xml e
red_ressalva_no_mesmo_enunciado.xml. Foco final dos owners:264aprovados;
comparação instalada base/candidato mantém mesma fala e retorno HTTP: base
altera a resposta, candidato publica a resposta integral em uma chamada,
nos dois casos de apoio pessoal e estado discursivo. Evidência em
comparacao_apoio_estado.json. Revisão final independente:52testes e24probes
aprovados sem nova alteração de produção.

## Porta de capacidade e fronteiras legadas

O catálogo canônico já responde perguntas condicionais sobre suas capacidades,
sem permitir ações. A porta prioritária ainda filtrava a natureza antiga
“hipotetica” e impedia consultar o catálogo para “condicao_nao_verificada”.
Uma linha em comandos_imediatos.py permite APENAS a consulta read-only, ainda
dependente de resposta reconhecida pelo catálogo. Condição futura não passa
ao executor. RED5/22controles, GREEN31/3subtests; sete módulos255/3subtests.
Duas instalações reais controladas (arquivos/programas):zeroHTTP,zeroexecutor,
zero voz. Não prova efeito externo nem autonomia.

Outras expectativas ajustadas com evidência, mantendo IDs:

- Volume: dois pedidos explícitos já davam set100; “nao lay o volume no maximo”
  não fornece autoridade, permanece controle negativo. Continuidade exige
  receipt do publicador real; só última intent/params ou receipt expirado/não
  confirmado não sustentam continuação. Não retirar negação nem falsificar
  recibo para restaurar teste antigo.
- Hipótese: natureza atual é condicao_nao_verificada, autorização/execução
  continuam falsas. Não restaurar literal antigo em produção.
- Limpeza de pergunta: fake não implementava retrato_dominio; substituir pelo
  EstadoCompartilhadoRuntime real e receipt tipado preserva a fronteira de
  ocorrência e prova estado resultante, sem excluir playlist real.
- Personalidade: prompt contém os owners versionados integrais de identidade
  e perfil social; dois literais antigos foram removidos pelo perfilv2.
  Teste agora confere composição canônica+limite+contratoJSON/operacional,
  em vez de reinserir texto antigo só para satisfazer snapshot lexical.

## Realização histórica e publicação única

Três testes exigiam zero gerações porque detector antigo interceptava
palavras de resultado DENTRO da citação e respondia sobre o último volume.
Mesmo histórico/receipts, detector antigo em memória confirmou essa causa;
o atual não deve restaurá-la. O contrato atual usa uma realização fechada
por enumerações do schema, com fonte integral, oito receipts e escopos.

Testes mantêm IDs e agora exigem uma chamada de realização da mesma consulta,
schema fechado e uma publicação, sem nova resposta depois da conclusão.
Quatro testes dedicados de pré-fluxo/canais continuam protegendo deduplicação
real. Outra expectativa exigia auditoria histórica em “Você pode explicar X”;
o lookup conserva receipts, mas só retrospectiva explícita cria tal obrigação.
Testes distinguem finalidade e fonte sem dar ação à citação. Esclarecimento
livre dessa variante não é declarado validado por uma fixture só de plano.

RED4/43aprovações/5skips; controles108/1xfail. Candidato155/5skips/1xfail;
seis testes finais com IDs históricos preservados passaram. Cinco adulterações
controladas (chamada duplicada, contexto aberto, receipt perdido, obrigação
histórica forçada e lookup sem IDs) foram rejeitadas.

## Alívio: rejeição anterior à proporção

A fala fantasiosa continua vetada por afirmar uma cena sobre o interlocutor.
A revisão de atribuição hoje precede proporção; teste antigo forçava motivo
posterior “alivio_resposta_desproporcional”. Alterar somente esse assert para
o bloqueio efetivo preservou as demais expectativas:zerochamadas adicionais,
resposta causal curta, sem cena física. Não mudou produção nem personalidade.

## Admissão nominal revelada pelos coletores

“abre a Calculadora e o Bloco de Notas” é um ato com dois objetos, não dois
atos inventados. Resolver singular escolhe Calculadora por substring até se
a ordem dos nomes é invertida; gate admite uma única proposta e bloqueia a
segunda antes de gerar seu ID. Dois verbos explícitos admitem duas. Logo a
perda ocorre antes de execução/receipt/correlação; seis falhas posteriores
são consequências, não seis novas raízes. Citar nome com “e”, alternativa
com “ou”, negação ou condição não fornece enumeração autorizada.

Candidato em `coordenacao_nominal.py`, `escopo_autorizacao.py` e
`decisao_turno.py`: verbo compartilhado e objetos conservam intervalos literais
na fala. A projeção para o resolver é explicitamente derivada, não outro ato
inventado. Cada membro precisa resolução nominal exata; substring que troca
“Bloco de Notas Inexistente” por “Bloco de Notas” não qualifica o conjunto.
Cardinalidade indeterminada permanece fechada. Cada escopo possui chave
(índice do ato, índice do alvo); consumo de um alvo não apaga outro nem libera
duplicata. Modelo, IDs, receipt proposto e ordem da lista não criam escopo.

RED15/9controles, incluindo seis falhas históricas da correlação; GREEN24.
Fonte literal e um ato mantidos, formas flat/canônica recebem dois IDs/receipts
e sucesso parcial não vira conclusão total. Controles de alvos novos, duplicata,
PC diferente, alternativa, condição e resolução parcial recusados. Sites
também exercitam o contrato compartilhado. O wrapper de vínculo por ato mantém
seu retorno anterior; não muda índice dos consumidores de materialização.

Limites: enumeração exige membros qualificados por artigos/tipos; aliases sem
equivalência lexical não são distribuídos. Ausência de expansão em um nome
delimitado não prova que o resolver singular legado resolveu esse nome
corretamente. Essa fronteira anterior por substring não foi corrigida em
todos os caminhos pela presente mudança. O DTO de roteiro progressivo ainda
não representa dois membros com um mesmo índice de ato; não inventar índices
ou declarar validada materialização contextual dependente desse conjunto.

Quatro probes instalados com as duas formas de proposta e receipts negativos
demonstraram zero fechamentos dependentes após o conjunto nominal; fase final
é falha_execucao, não sucesso. Controle misto APP_OPEN+OPEN_URL no mesmo ato
preserva dois escopos e recusa destino estranho/duplicata. Consumidores vizinhos:
215aprovados/uma falha de exportação antiga na sonda test_observacao_execucao,
fora dos127módulos desta regressão. Não alterar a produção para serializar um
coletor desconhecido nem contar essa evidência como regressão causal nova.

## Validação final e limites

Primeira repetição dos módulos-alvo:451aprovados/6falhas/
5skips/3subtests,zeroerros; todos os44IDs preservados, seis falhas de admissão
reveladas acima em correlação. Nenhum resultado de suíte completa é inferido.
Sondas vizinhas fora dos123módulos também possuem exportação tipada obsoleta;
registradas separadamente, sem modificar produção para acomodar coletores.
Regressão conclusiva:127módulos,3.760aprovados,25skips,um xfail,um deselected,
três subtests,zero falhas/erros em418.69s. Mesmo filtro prévio,sem filtros novos.
Auditoria XML por par classe/nome confirmou todos44IDs originais aprovados;
nenhum foi removido ou marcado como skip. Os539fontes testados mantiveram hash
durante a execução. Evidências regressao_conclusiva.xml/log e
resumo_conclusivo.json, gerado por auditar_conclusao.py. Ensaios amplos
interrompidos quando a revisão encontrou novos REDs foram preservados e não
servem como prova final. A última execução completa ocorreu depois de fixar
as fontes finais. Não extrapolar este verde à suíte total do projeto.

Sem conversaQwen nova, voz, ações reais, commit, push ou desligamento.

Preparação da instalação: a cópia original está no HEADae7b8775/main e a
worktree no1197daf. O snapshot anterior não deve ser substituído pelo HEAD.
Baseline dos538fontes originais foi congelado antes da escrita. Três arquivos
neurais rastreados diferem em bytes entre as bases e não pertencem a esta investigação:
modelo.py e geradores volume_set_absoluto_v5_gate_minimo/v7_gate_duplo. Foram
excluídos do manifesto de instalação; não se sobrescreve o subsistema neural.
A conferência textual posterior confirmou conteúdo igual nesses três arquivos,
com diferença apenas de quebras de linha (diferencas_neurais_preservadas.json).
O delta autorizado é de seis owners existentes mais coordenacao_nominal.py;
os demais fontes originais devem conservar seus hashes. Sessões já abertas
continuam com seus snapshots e não serão encerradas automaticamente.

Instalação aplicada com guardas de SHA256 de todos22arquivos antes da escrita
e backups dos arquivos existentes em backup_original. Sete fontes de produção
(seis existentes e um módulo novo) e15arquivos de teste foram transportados
por apply_patch; igualdade textual conferida. Demais532fontes originais
mantiveram seus hashes, incluindo os três neurais com EOL distinto. Nenhum
arquivo de configuração privada ou estado pessoal foi exportado/alterado.
Validação concluída no .venv314 original:489aprovados,5skips,3subtests,zero
falhas/erros em78.38s,16módulos-alvo e vizinhos. Auditoria XML confirmou44IDs
originais aprovados também nessa cópia, sem remoção ou skip. SHA256 após testes
confirma532fontes preexistentes preservados. Resultado em original_instalado.xml/
log e instalacao_original.json. Nenhuma sessão pessoal foi reiniciada ou
encerrada. Uma sessão já aberta conserva o código antigo copiado; para testar
o candidato naturalmente, abrir nova sessão da ponte. Testes naturais continuam
com Pedro. Revisão livre, compreensão global e demais problemas da conversa
(incluindo a ocorrência sem publicação da rodada18) não são encerrados por
esta seleção. O grupo44 e seus seis REDs de admissão revelados estão verdes.
