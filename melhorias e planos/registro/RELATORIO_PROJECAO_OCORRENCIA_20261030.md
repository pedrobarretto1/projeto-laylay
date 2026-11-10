# Rodada 18 — falsa perda de ocorrência antes da publicação

Investigação iniciada em 30/10; validação retomada em 31/10/2026.
Base congelada: 1197daf0d6b5e69b7243f571542bf17666274ea2, branch
codex/correcao-autoria-conversa-20261030. Worktree anterior preservada.
Artefatos: resultados_testes/sem_publicacao_18_20261030.

## Cadeia causal demonstrada

Sessão 20261030T195853Z-0d4ab6c2, id casa-20261030-18. Entrada integral de
510 caracteres; turno e retrato publicaram recortes de 500, terminados em
espaço. Plano conservou 510. O normalizador fazia strip antes do corte: a
mesma projeção reaplicada ao turno produzia 499 caracteres e aplicada ao plano
produzia 500. motivo_incoerencia_contratos_turno recusava o frame e o runtime
descartava a proposta como não vinculada, antes de publicar. Não houve falha
do publicador; sua guarda de ocorrência obsoleta continua necessária.

O snapshot histórico contém a mesma regra. Replay com factory real da ponte,
root, preparador, orçamento, revisão, orquestrador e observador nativos reproduz
sem_publicacao. Histórico fixado: 34 mensagens anteriores. Retorno histórico
legado com fala fornecido no HTTP controlado, não uma nova inferência Qwen.
O evento modelo_retornou histórico é pós-codec; nesta rota sua representação
legada foi aceita sem reconversão V5. Não inferir equivalência em outras rotas.

Hipóteses falsificadas: orçamento/timeout (uma chamada, nenhuma bloqueada),
conteúdo específico da autoria (mesma falha com outro bilhete sob o mesmo
contrato), defeito geral do publicador (mesma composição publica com apenas
o owner corrigido). IDs e falas realmente divergentes continuam rejeitados.

## Contrato e escopo

Owner único alterado nesta etapa: mente_laylay/cognicao/decisao_turno.py.
Projeção textual compartilhada usa strip, corte de 500 e rstrip. Assim sua
reaplicação é idempotente. Nenhuma normalização de espaços internos, caixa,
parâmetros ou identidade; recorte não certifica o sufixo nem concede autoridade.
O comparador de ocorrência já removia a borda após o corte; agora coerência
reutiliza a mesma função. Revisão, executor, publicador e orçamento preservados.
Fonte original integral e texto da resposta não são truncados pelo candidato.

baseline.json e fontes_candidato.json confirmam um owner alterado entre 539,
com 538 fontes de produção preservadas. candidato.diff é contra o baseline
sujo congelado, não contra HEAD; conserva a correção nominal da etapa anterior.

## Evidências de validação

RED canônico: 14 falhas e 16 controles aprovados. Quatro falhas preliminares
eram erros do teste ao copiar/comparar o estado sincronizado; corrigiu-se a
sonda para usar snapshot nativo antes do RED canônico, sem alterar produção.
Foco: 207 aprovados, um xfail anterior. Casos 499/500/501/650, espaço/tab/quebra/
NBSP, writer, callbacks obsoletos, revisão, identidade e divergência interna.
APP_OPEN/IOT_CONTROL/DELETE_ITEM/PLAYLIST_CREATE continuam sem autoridade
quando a IA muda o sufixo fora da projeção; receipt proposto não vira efeito.

Replay pareado: histórico e autoria alternativa, cada um com owner anterior
carregado da fonte congelada somente no subprocesso privado, e com candidato.
Antes: zero texto_publicado, sem_publicacao. Depois: um texto_publicado nativo,
texto integral igual ao modelo, uma chamada, zero bloqueios/degradação.
Arquivos historico_antes/candidato.json e alternativa_antes/candidato.json.

Instalação original ae7b8775/main: SHA256 antes da escrita, backup_original,
um owner e dois arquivos novos de teste/fixture transportados por apply_patch.
Três fontes neurais com EOL distinto não foram tocadas. Replay final instalado
também publica integralmente uma vez, sem voz/efeitos/rede real, em perfil
privado dentro da instalação original. A primeira sonda cruzada foi recusada
corretamente porque o perfil estava fora dessa instalação; corrigiu-se só
o local do perfil, preservando a guarda de isolamento.

No venv original: 301 aprovados, um xfail conhecido, zero falhas/erros em
88,01 segundos, dez módulos. original_depois.json confirma 538 fontes
preexistentes preservadas e somente o owner autorizado alterado. Probes
adversariais adicionais: 8.400 reaplicações idempotentes em bordas, espaços
Unicode e entradas com whitespace externo. Sem mudança de fonte nos testes.
Regressão ampla: 131 módulos, 3.967 aprovados, 25 skips, um deselected, dois
xfails e três subtests aprovados; zero falhas/erros em 428,88 segundos. Mantido
o filtro anterior test_composicao_principal_injeta_rota_que_respeita_perfil_explicativo,
sem exclusão nova. Auditoria XML confirma os 44 IDs históricos aprovados,
nenhum removido/ignorado, e os 539 fontes sem drift. O segundo xfail é o RED
anterior de segmentação de atribuição/pergunta causal em finalidade_contexto_historico,
incluído pela seleção ampliada; não é um novo defeito introduzido nesta etapa.
Detalhes e motivos dos dois em resumo_final.json; execução em ampla.xml/log.

## Limites e pendências preservadas

O xfail de revisão com 520 espaços permanece RED por outra relação: a revisão
compacta a fonte integral, enquanto o recorte já perdeu o restante da fala.
--runxfail antes/depois confirma texto operacional incompleto. Não removido,
não contado como corrigido, não ampliado o patch de publicação para essa raiz.
O plano inicial relacionava as bordas; a contraprova separou os mecanismos.

Uma autoria alternativa V5 sem enquadramento teve conclusão sobre fontes:
agora ela é publicada como revisão, em vez de desaparecer. Sua qualidade é
outra fronteira, preservada no artefato; não se aceita automaticamente toda
proposta. A comparação causal definitiva varia somente a fala do retorno
legado histórico, conservando formato e leitura, e publica dois bilhetes.

Não há prova de coerência geral, comportamento estocástico Qwen, áudio ou
efeito real. Testes naturais continuam com Pedro. Nenhuma sessão pessoal foi
encerrada/reiniciada. Sessão já aberta usa snapshot anterior: abrir nova sessão
para testar a instalação atual. Sem commit, push ou desligamento nesta etapa.
