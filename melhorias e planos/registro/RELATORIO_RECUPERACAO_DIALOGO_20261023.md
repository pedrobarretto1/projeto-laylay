# C7/C5 — recuperação de fontes antigas antes do orçamento de diálogo

Pedido: continuar a etapa de coerência; comandos de teste simulados, sem voz.
Pedro autorizou separadamente `shutdown.exe /s /t 1800`, executado com saída0
no início deste trabalho. Não houve reagendamento nem cancelamento.

## Base e primeira fronteira

HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, branch `main`, worktree suja
preservada. Manifesto inicial de527 fontes, status e backups dos dois owners:
`resultados_testes/recuperacao_contexto_conversa_20261023/baseline.json`.
Não comparar este runtime com HEAD limpo: há mudanças anteriores e paralelas.

Na coleta anterior, usuário12 apresentou Leo/jogo Ponte de Papel;13 atribuiu
música a ele. No19, essas declarações estavam no histórico e PedidoModelo,
mas não no HTTP enviado ao Qwen. A resposta inventou outra função. O controle
curto, com a fonte disponível, respondeu música. Isso falsifica apagamento do
arquivo e incapacidade inevitável de compreender essa atribuição. Não prova
que ausência de contexto seja a causa de todas as invenções da IA.

Inventário: EstadoConversaRuntime conserva o diálogo; ContextoPromptRuntime
compõe o ato; seletor_contexto seleciona contexto; preparacao_llm aplica o
orçamento; llm_http compacta retries; modalidade/validação/executor mantêm
autoridade e receipts. Não havia recuperação de mensagens antigas antes do
corte por recência. O patch reutiliza esses owners, sem outro banco/parser de
comandos, memória durável, catálogo ou serviço de busca privado.

## Contrato e candidato aplicado

Produção alterada somente:

- `mente_laylay/cognicao/seletor_contexto.py`: seleção lexical de ocorrências
  do usuário, da fala anterior à primeira âncora até a última fala histórica.
- `mente_laylay/integracao/preparacao_llm.py`: empacotamento literal JSON com
  índice da ocorrência, papel e texto; anexo ao contrato efêmero atual.

O intervalo não omite falas subsequentes do usuário, incluindo correções e
negações sem o substantivo original. O pacote inteiro, com metadados, disputa
os mesmos1200/2600 caracteres do histórico; a recência usa só a sobra.
Os limites4/8 mensagens permanecem. Se não couber, recusa o pacote inteiro;
não publica a âncora cortada de seu contexto. A instrução atual e o usuário
atual continuam atômicos. O retryHTTP400 preserva o pacote com a instrução.
Pacotes fechados não passam por essa seleção; eventos system posteriores ao
usuário não usam esse usuário histórico como consulta atual.

O JSON contém dados citados, não novos turnos do usuário: não é autorização
vigente, receipt ou prova de verdade/efeito. Nenhuma fala da IA ou instrução
system antiga é promovida a declaração do usuário. Índices identificam a
ocorrência na lista normalizada daquele PedidoModelo, não um ID durável.
O arquivo histórico é preservado; o pacote é efêmero. Recuperação lexical não
resolve semanticamente pronomes, correções, sinônimos ou implicação.

Não foram alterados roteamento/execução de habilidades, revisão de apoio,
modelo `qwen3:4b-instruct`, configuração, voz, UI ou hardware. Nenhum commit,
reinício ou ativação da sessão pessoal foi realizado. A única ação real de
sistema solicitada nesta etapa foi o agendamento de desligamento.

## Candidato rejeitado e falsificações

O primeiro candidato recuperava frases individuais por prioridade lexical.
Passou84 testes, mas a revisão encontrou Azul sem a correção elíptica Âmbar
quando menções intermediárias disputavam vagas. Reproduzimos4RED; esse
candidato foi abandonado, preservado em `*.candidato_rejeitado`. Sua coleta
parcial foi interrompida após18 turnos e não conta como validação final.

Não removemos a proteção de orçamento nem ampliamos janela/tokens/timeouts.
O erro foi admitir fontes individualmente sem o intervalo que continha suas
correções. A segunda revisão verificou o novo contrato e não apontou outro
defeito concreto; as limitações semânticas/orçamentárias permanecem.

## Evidências de validação

Artefatos em `resultados_testes/recuperacao_contexto_conversa_20261023/`:

- `red.xml`:7 falhas de chegada de fonte e5 controles aprovados antes do patch.
- `red_correcao.xml`:4 falhas de correção,10 controles aprovados no candidato rejeitado.
- `green_guardas.xml`:23 testes de fonte, autoria, correção, orçamento,
  intervalo grande, evento, imutabilidade e retry aprovados.
- `green_final.xml`:101 testes focados aprovados na verificação final, incluindo
  os dois novos módulos e os contratos de transporte/perfil/orçamento existentes.
- `instalada_baseline_red.xml`:4RED na factory/portaHTTP com os dois owners
  anteriores carregados em memória, sem restaurar arquivos de produção.
- `instalada_canonica.xml`:4GREEN no mesmo caminho, dois assuntos, modos
  normal/rápido, proposta adversarial APP_OPEN rejeitada sem pedido atual.
- `continuidade.xml`:119 aprovados, incluindo histórico local, conversa
  cotidiana, latência e27 testes novos. Sobrepõe outros conjuntos; não somar.
- `regressao.xml`:1493 aprovados,30 subtests aprovados,14 skips opcionais,
 1 teste deselecionado por ordem/importação já documentada anteriormente.
  Há2 falhas anteriores em `test_autoria_reescritas`[4]/[6], ordem
  interpretacao/principal. `falhas_anteriores_baseline.xml` reproduziu as mesmas
  2 falhas e30 aprovações usando os owners congelados via `baseline_hook/`.
  O teste deselecionado passou no conjunto isolado de continuidade/latência.

O ensaio instalado inicialmente sem sistema canônico no histórico teve2RED
na rota forçada rápida (`instalada.json`): o preparador conserva a primeira
mensagem user como primeiro item e não a consulta como histórico. A fixture
final representa a conversa após preparação normal, que mantém o sistema
canônico. Não usar essa mudança de fixture como prova de correção do cenário
sem sistema: ele permanece uma condição separada de composição a estudar.

## Composição real com Qwen e conversa longa

`conversa_validada/`:30 turnos contínuos,30 conclusões textuais,32HTTP200,
209,878s dentro dos turnos. Mesma factory e serviços cognitivos, modelo real;
perfil isolado, executores externos substituídos por receipts negativos
tipados do adaptador real. Dois APP_OPEN simulados, nenhum efeito real/voz.
Gabarito externo não entra no prompt. AppOpener é folha simulada desde import;
rede externa, serial, shell e escritas fora do perfil são bloqueados. A única
guarda acionada foi a sondagem IPv6 na inicialização da biblioteca de rede.

`avaliar.py` conferiu sete pacotes enviados no HTTP: cada índice/papel/texto
corresponde exatamente a um PedidoModelo daquele ato. Não toma a saída do
modelo por prova da origem. Todos os527 hashes permaneceram estáveis durante
a coleta; comparando ao baseline desta etapa, só os dois owners mudaram.

No19, ambas as fontes12/13 chegaram ao Qwen, que publicou:
“No projeto, a parte do Leo é a música.” Esse é GREEN real deste recorte.
Não encerra coerência da conversa: no13 a IA respondeu assunto anterior mesmo
com o ato novo presente; no14 a correção de caderno continua tratada como ação;
15/21/27/28 mantêm erros de perspectiva;29 ainda é consumido como feedback do
último aplicativo. Essas fronteiras não foram remendadas neste patch.

18/25/26/28 ainda não recuperaram seus intervalos na rota rápida: o pacote
completo ultrapassa1200 caracteres. Houve negação de registro no18, local
inventado no25, nome inventado no26 e banda não retomada no28. O fallback
orçamentário preserva a seleção anterior; não impede a autoria de extrapolar.
`contrafactual_mesma_entrada.json` confirma seleção idêntica ao preparador
anterior nesses quatro casos, dados exatamente os mesmos pedidos internos.
Isso falsifica atribuir essas diferenças textuais à nova recuperação naquele
ato, sem provar independência dos turnos anteriores.

No replay dos mesmos pedidos com o perfil normal já existente, os intervalos
19/25/26/28 cabem e chegam completos (`replay_intervalo.json`); é contraprova
determinística do orçamento, não uma validação Qwen do modo normal nesses
casos. Não alteramos modo nem escondemos falhas forçando essa rota no ensaio.

## Responsáveis e próxima fronteira

| Owner/contrato | Critério para avançar |
| --- | --- |
| Seletor + preparação do modelo | Manter literalidade, falante, ordem e intervalo inteiro dentro do orçamento; GREEN focado/instalado/real do19 obtido. |
| Decisão de modo + ContextoPromptRuntime | Investigar por que retomadas antigas continuam no perfil rápido quando seu contexto necessário não cabe; provar RED antes de alterar a decisão compartilhada. Não aumentar janela cegamente. |
| Autoria/revisão comunicativa | Falta de fonte não permite inventar causa, nome, local ou experiência. Fonte disponível também não garante atender o ato atual. |
| Modalidade/perspectiva/pré-fluxo | Preservar as raízes já registradas: correção pessoal, atribuição usuário/IA e vínculo do novo ato ao contexto correto. |
| Composição inicial | Estudar o histórico sem sistema canônico na primeira rota rápida, separadamente do intervalo recuperado nesta etapa. |

Vínculos históricos C7/C5/F1 preservados. Concluído o contrato limitado de
recuperação literal quando o intervalo cabe, com prova do19; a família de
perda de contexto e a compreensão geral continuam abertas. Próxima prioridade:
decisão do perfil rápido versus necessidade de fonte antiga, antes de novos
patches de autoria ou de qualquer mudança de modelo/voz.
