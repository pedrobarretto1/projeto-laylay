# Revisão com espaços longos — fonte integral antes da projeção

Base1197daf0d6b5e69b7243f571542bf17666274ea2,
codex/correcao-autoria-conversa-20261030. Worktree prévia preservada, inclusive
projeção idempotente da rodada18. Baseline/status/hashes539fontes em
resultados_testes/revisao_espacos_20261031/baseline.json.

## Raiz demonstrada

O resolver compacta whitespace da entrada integral e só depois publica seu
texto_original recortado. O gate _revisao_bloqueada_coerente compactava o texto
original do turno já recortado. Uma sequência de520 espaços fazia esse recorte
conter somente "abre" e espaços, enquanto a revisão preservava alvo e
cancelamento. Compactar e recortar em ordens diferentes não é equivalente.
Primeira divergência: fonte da revisão não conferida pelo gate, não parsing,
autorização, orçamento ou publicação. A revisão já cancelava corretamente;
o frame era recusado como texto operacional incompleto e sumia a resposta.

Hipóteses falsificadas: parsing de espaço longo (mesma revisão compactada do
controle curto), orçamento (uma chamada,nenhuma bloqueada), regra anterior da
rodada18 (projeção idempotente já presente no baseline), defeito geral de
publicação (controle curto publica nos dois owners). Não atribuir esta raiz
a todo problema de fonte, segmentação ou revisão livre.

## Contrato e candidato

Único owner de produção alterado: decisao_turno.py. A revisão é uma derivação
do texto integral preservado no plano identificado; conferir essa fonte antes
de compactar e recortar. Comparação continua literal sobre a projeção de500
do produtor. rstrip após o corte conserva estabilidade quando a borda é espaço.
Turno/retrato não ganham texto inventado ou autorização, nem substituem fonte.

Conservadas as exigências: duas cópias iguais da revisão, flags booleanas,
tipo/modalidade/origem do veto compatíveis, decisão de conversa, IDs coerentes,
veto ativo, nenhuma autorização, nenhuma operação efetiva. Plano ou revisão
adulterados depois do caractere500 bruto continuam recusados pela conferência
da derivação integral. Fonte projetada não certifica informação além de500
caracteres compactados nem prova efeito externo.

Nenhuma mudança no resolver, orquestrador, executor, publicador, orçamento,
LLM ou configuração. Benefício compartilhado de correlação/explicação de
cancelamento e revisão ambígua, demonstrado em apps, arquivos, IoT e música;
nenhum domínio recebe exceção própria.

## RED, controles e instalação

RED histórico: um caso xfail confirmado com --runxfail,30controles verdes.
RED canônico:21falhas/6controles;20variantes em cinco casos de cancelamento/
ambiguidade e quatro espaços,mais factory real com entrada longa. Fonte/plano
adulterados,turno estrangeiro,veto retirado,operação reintroduzida são negativos.
GREEN inicial58; depois235aprovados no foco de cinco módulos. Removida somente
a marca xfail resolvida, mantendo o texto e ID do caso histórico.

Replay da factory da ponte e root instalado, HTTP fixo, perfil privado, folhas
de voz/efeito bloqueadas. Mesmo texto de resposta: curto baseline/candidato
publica uma vez; longo baseline zero publicações/sem_publicacao; longo
candidato uma publicação literal,uma chamada,sem degradação ou bloqueio.
JSONs curto_baseline/candidato e longo_baseline/candidato, trace e eventos
texto_publicado nativos. Um primeiro replay usou um payload legado incompleto
e falhou em contrato_saida_invalido; descartado como prova desta raiz.
Replay válido usa proposta V5 aceita pela rota nos quatro percursos, sem
modificar nenhum owner para satisfazer a sonda.

Instalação original ae7b8775/main por delta apply_patch, conferência SHA256,
backup de fonte e teste anterior. Um owner de produção,um teste atualizado,
um teste novo. Demais538fontes preservadas,inclusive três neurais com EOL
distinto. No venv original:251aprovados,zero falhas/erros em62,91segundos,
sete módulos,incluindo factory real da ponte e a regressão da rodada18.
original_depois.json confirma que somente o owner autorizado mudou em539fontes.
Regressão ampla132módulos:3.995aprovados,25skips,um deselected,um xfail
preexistente de segmentação causal,três subtests;zero falhas/erros em431,47s.
Mesmo filtro anterior,sem exclusões novas. Auditoria XML confirma44IDs da
investigação anterior aprovados e os oito casos históricos de revisão ativos
e aprovados,inclusive o de espaços longos. Os539fontes mantiveram SHA256
durante a validação. Evidências ampla.xml/log,resumo_final.json e
original.xml/log. Não equivale à suíte global ou qualidade espontânea Qwen.

## Limites

Sem conversa nova com Qwen, voz, efeitos reais, commit, push ou desligamento.
Não encerrar a outra pendência preexistente de segmentação causal nem qualidade
livre/coerência geral. Testes naturais ficam com Pedro; sessão já aberta guarda
snapshot antigo. A validação é de composição instalada com autoria controlada.
