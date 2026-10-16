# Ritmo corporal — continuidade de CORPO-DECISAO-V1

Baseline: main d850b8c90cc5ce40bd4832e759ed991ba88cd5cc, worktree paralela
preservada. Os dois owners congelados antes do candidato estão em baseline/.

Pedro pediu que não fazer nada fosse opção e apontou o equilíbrio do primeiro
protótipo. No atual, livre + passeio concedido escolhia explorar; o supervisor
apenas aguardava8–14s antes de repetir. Isso é política de iniciativa, não
problema dos motores/firmware nem ausência da intenção descansar no modelo.

RED canônico com owners/transporte/coordenador reais e hardware simulado:
primeiro passeio confirma;20s depois outro passeio é executado nos dois perfis,
em vez de decisão de repouso. O teste de decisão também mostrou parâmetro ausente.
Falsificado problema geral de motor: os mesmos executores produziram receipts
válidos na primeira exploração. Descansar já existia na proposta da mente.

## Comparação com control_display.ino V7.3

Fonte: C:/Users/pbarr/Downloads/control_display/control_display.ino.
-69: ACAO_QUIETA, observar e outras ações sem locomoção fazem parte do repertório.
-1226–1365: momentos persistentes, duração variável e pontuação contextual.
-6439–6705: objetivos observar/descansar/explorar competem; exploração perde
  pontuação com saciedade e repetição, e há influência do estado anterior.
-7014: escolha conserva objetivo válido com inércia, em vez de trocar a cada ciclo.
-4365–4445: tempo comandado de motores por janela/sessão altera pontuação e
  substitui etapas pesadas por observar/parar.

Esse mecanismo ajuda a explicar o equilíbrio descrito pelo usuário; comparação
estática não mede a distribuição temporal que ele observou. Energia/fadiga,
território virtual e focos imaginários do protótipo são simulações, não prova de
bateria, distância ou percepção. Não foram transferidos como sensações reais.

## Incremento aplicado

Decisor compartilhado recebe o fato transitório `passeio_em_repouso` do owner,
usando o prazo da concessão já existente. Fora de conversa/reação causal/proposta
vigente, escolhe descansar/repouso_espontaneo, sem candidato a movimento.
O supervisor publica fase repousando/estado em_repouso e retorna sem montar
plano, som ou receipt fictício. Concessão continua ativa; leituras repetidas não
substituem essa decisão nem encurtam o prazo.

Após coreografia bem sucedida, passeio aguarda45/70/55/90s, contados do final;
força/partitura/limites e primeiro intervalo de8s preservados. Emoção nova,
interação, resultado operacional e pedido manual seguem seus contratos prévios.
O quadro mental/DEV recebem a intenção do mesmo owner, não inteligência separada.

É uma primeira correção de ritmo: dá espaço real ao repouso e não reproduz todo
o sistema de pontuações/momentos/orçamento do protótipo. A comparação identifica
esses mecanismos como próximos candidatos para um equilíbrio mais contextual.

## Provas e limites

146 testes passaram,2 casos excluídos após controle com os dois owners congelados
reproduzir as mesmas falhas: receipt instalado sem chave intent e configuração
influenciada pelo perfil rodas_suspensas. Não foram enfraquecidos nem corrigidos
neste incremento. Resultado bruto anterior e seleção verde estão nesta pasta.

O teste antigo que exigia manter a intenção explorar durante a pausa foi atualizado:
o objetivo continua, mas a intenção muda para descansar; nova asserção protege
estabilidade de identidade do repouso em leituras subsequentes. Isso corresponde
à mudança expressamente pedida pelo usuário.

Teste de composição importa laylay.py e verifica intenção no modelo da mente e
no DEV; apenas a fronteira de hardware é simulada, com envio de movimento
proibido. Não é prova de runtime físico. Não abri aplicação normal nem enviei
MOTOR para o ESP. Processos já existentes preservados; carregar ajuste ao reabrir.

Produção: decisao_corporal.py e companhia_corporal.py. Testes novos e atualização
de expectativa em test_decisao_corporal_v1.py. Nenhum commit ou firmware novo.
