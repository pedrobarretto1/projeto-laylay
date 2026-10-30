# Proposta operacional — separar o caminho instalado da porta conversacional

Base congelada:HEAD c91cae1bd407b02db946ae7bc752d1ed3269bfd9,main,535
fontes. Worktree anterior preservada. Artefatos:
`resultados_testes/proposta_operacional_20261028`.

## O que a comparação provou

O sintoma anterior vinha da coleta `seguranca_categoria`,na porta da ponte:
o pedido da Calculadora tinha modalidade comando,autorização e plano de
execução,mas a LLM escreveu “Estou abrindo” sem propor comando. A revisão
não confirmou efeito;publicou a ausência de execução. A omissão do modelo é
real nesse caminho,não prova de que o executor perdeu uma proposta recebida.

Controle na composição normal,sem retirar processar_comandos_prioritarios,
processar_inicio_fluxo ou modo_chat_runtime:os pedidos de pausar música,
desligar ventilador e abrir Calculadora chegam aos três executores simulados.
Há receipts nativos MEDIA_CONTROL/IOT_CONTROL/APP_OPEN,com executou=False,
confirmado=False e status simulado_sem_efeito. Nenhum HTTP de LLM foi preciso
nesses três pedidos explícitos. Cada turno teve uma publicação observável.
Isso falsifica uma falha geral de proposta/roteamento nesses comandos.

A porta da ponte desliga esses atalhos e bloqueia dispatch/execução por
contrato. Ela permite estudar autoria conversacional e propostas,mas não
representa todos os caminhos de execução do aplicativo. O runner comparativo
preservou tanto essa porta quanto a rota normal;nenhuma guarda foi relaxada.

## Candidato investigado e retirado

A emissão genérica permite omitir comandos e não oferece claramente o
protocolo canônico pré-execução. O contrato de fala final orienta resultado
observado;isso não basta para ensinar a representação de uma proposta.
Contrafactuais de schema isolado,fase isolada e ambos produziram omissão ou
operações erradas. Um documento explícito de protocolo produziu APP_OPEN.
Esses sorteios não equivalem a reexecução determinística da amostra antiga.

O candidato compartilhava estrutura/validator da interpretação principal e
projetava o protocolo antes do envio.14 REDs/quatorze controles;foco153
aprovados/dois ignorados. O primeiro guard confundiu autoridade do plano com
o campo autoriza_execucao=False do contrato de fala;foi corrigido sem dar
autoridade à fala. Sua expectativa local foi ajustada ao contrato documentado.

Na composição,Qwen chegou a propor APP_OPEN e o receipt negativo apareceu.
Contudo,houve publicação posterior com diagnóstico inventado. Nos controles
de música/IoT,o mesmo candidato omitiu a operação ou escolheu PEOPLE_LIST.
Projetar apenas os domínios do catálogo vivo também não resolveu os dois
REDs;houve timeout. Não forçar minItems=1 para obter qualquer comando.

Candidato REJEITADO. Três fontes voltaram exatamente aos SHA da base:
contexto_resposta_ia,suporte_autoria e saida_interpretacao_principal. Código,
testes e hashes do candidato ficam em candidato_rejeitado. Não estão ativos
nem na suíte regular. Não aumentar orçamento ou mudar modelo para mascarar
essa insuficiência;nenhum patch de proposta foi mantido.

## Relação com as novas conversas

No journal `20261029T000204Z-57d38f3a`,19 rodadas atravessaram a quinta
interação e a sessão encerrou normalmente. A quarta rodada é outro defeito:
“Acha que isso faz parte do seu estilo?” recebeu autorização pelo sentido
operacional de achar. A fala de ausência de efeito foi consequência dessa
classificação incorreta,não da falha do executor. Investigação separada em
`resultados_testes/modalidade_opiniao_20261028`.

As rodadas17/18 repetiram texto na própria emissão do modelo. A revisão
lexical só cobria cópia integral e deixou escapar pequenas mudanças e cauda
nova. Continuação dessa raiz em `resultados_testes/reuso_predominante_20261028`.
Não contar cada tema,rodada ou mecanismo técnico como nova raiz histórica.

Sem voz,efeitos externos reais ou commit. Não declarar toda a seleção livre
de comandos corrigida:sua generalização continua sem prova. O controle
instalado comprova os três caminhos explícitos citados,com efeito simulado.
