# Coerência de conversa longa — diagnóstico sem voz e sem efeitos

Base: `main`, HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, worktree
previamente modificada. Pedido de Pedro: testar coerência em conversa longa;
complemento obrigatório: comandos simulados, sem ação real e sem voz.
**Produção não alterada nesta rodada. O teste encontrou falhas de coerência.**

Artefatos: `resultados_testes/coerencia_conversa_longa_20261023/`.
Roteiro/gabarito congelados antes da coleta em `roteiro.json`; transcrição em
`TRANSCRICAO.md`; entradas e respostas completas em `conversa_longa/conversa.json`.
O gabarito nunca foi enviado à Laylay e contém somente fatos sintéticos
introduzidos pelas entradas do roteiro, não fatos pessoais verdadeiros de Pedro.

## Execução e isolamento

Foram30 entradas na **mesma conversa**, sem limpar a memória entre turnos:
aula/desenho, preferência musical, encontro com Bia, alteração15h→16h,
projeto com Leo, alteração verde→amarelo, comandos intercalados e retomadas
distantes. Duas entradas pediram abrir aplicativos; todas as demais eram
conversa, correção, pergunta ou encerramento.

Reutilizada `scripts/analises/sonda_conversa_continua.py`, com a composição
de `laylay.py`, histórico, memória, interpretação, prioridade, autoria,
validação e publicação reais. Os quatro serviços que o helper de isolamento
desconecta foram reconectados às **mesmas instâncias da factory**. A coleta
registrou interpretador semântico `main`, especialista neural `shadow` e
pesquisa ampla desativada. Não foi escolhido outro modelo nem alterada sua
configuração. HTTP real foi permitido somente para o Qwen local configurado.

Persistência da instância de teste redirecionada em memória para o perfil
da rodada; arquivos relativos usam o diretório isolado. O código de produção
no disco não foi editado. Audithook impede escrita/remoção/movimento fora
da pasta de teste, processos externos além de três consultas Git somente
leitura e rede fora do backend local. SQLite também tem guarda de caminho.
AppOpener foi substituído desde o import porque sua inicialização grava cache
no pacote instalado; não houve abertura/fechamento real. Serial, voz e beeps
foram interceptados. Não há prova de áudio ou abertura real — foram excluídos
explicitamente do teste, conforme o pedido.

Os comandos usam **recusa simulada**, não sucesso inventado. A folha de efeito
publica receipt negativo pelo `AdaptadorResultadoOperacional` existente:
`status=simulado_sem_efeito`, `executou=False`, `confirmado=False`,
`contexto.simulacao=True`. O histórico e as respostas seguintes consomem esse
mesmo contrato. Isso prova continuidade sobre tentativa/resultado simulado;
não valida execução real, instalação do app ou materialização do alvo.

## Resultado da coleta longa

-30 entradas,30 conclusões textuais observáveis, nenhuma entrada silenciosa.
-2 comandos capturados: `APP_OPEN` nos turnos16 e23; ambos com receipt
  negativo simulado. Nenhum outro turno chegou ao executor de domínio.
-0 ações reais,0 voz. Nenhum arquivo Python de produção alterado durante
  a coleta; dados sintéticos não foram gravados na memória pessoal.
-32 HTTP200 e1 ReadTimeout. Chamadas auxiliares e registros internos
  duplicados não são contados como novas respostas ou novas execuções.
-230,901 segundos acumulados no processamento dos turnos. Não simula pausas
  humanas nem comprova estabilidade por horas/dias.

Nas10 retomadas-alvo, a leitura descritiva foi:2 coerentes,2 parciais,
5 divergentes e1 inconclusiva por transporte. Essa rubrica está em
`avaliacao.json`, ancorada no transcript congelado. **Não é métrica universal,
juiz de produção, avaliação humana independente ou prova geral de compreensão.**

| Turno | Fonte no roteiro | Resultado observado |
| --- | --- | --- |
|11|Horário corrigido para16h no10|Timeout; não classificar como esquecimento.|
|15|Caderno alterado para amarelo no14|Cor correta; troca ator para “que vou usar”. Parcial.|
|17|Abertura simulada sem efeito no16|Respeita receipt negativo; não anuncia abertura real.|
|18|Bia leva livro azul,8/9|Bia recuperada corretamente.|
|19|Leo faz música,12/13|Inventa análise de dados e otimização de processos “como você mencionou”.|
|25|Biblioteca Aurora e16h,8/10|Mantém16h, mas não responde o local. Parcial.|
|26|Nome Ponte de Papel,12|Inventa “O Labirinto dos Sonhos”.|
|27|Cachorro não vai ao encontro,21|Responde sobre o que a própria IA não teria dito, em vez do relato do usuário.|
|28|Preferência Nirvana,5|Não recupera a banda e troca usuário por si própria.|
|29|Plano após correções8/10/14/20|Pré-fluxo consome a pergunta como feedback sobre o último aplicativo simulado.|

Outros sinais: o4 repete integralmente a resposta do3, sem acompanhar a
conquista atual; o13 repete a resposta do12, sem incorporar a divisão de
papéis. No21, o cachorro do usuário aparece como “meu cachorro” na fala da IA.
Tom poético/excessivo é uma observação de estilo separada dessas divergências.

## Fronteiras comprovadas, hipóteses e controles

### Retomada distante: informação arquivada não chega ao modelo

Nos19,26 e28, as falas de origem continuam no histórico canônico **e no
PedidoModelo antes da preparação**. No transporte autoral, elas foram
descartadas. No26, `Ponte de Papel` não aparece em nenhuma mensagem do envio;
no28, `Nirvana` também não aparece. Isso é perda de disponibilidade entre
pedido interno e payload, não apagamento da memória persistida.

`preparacao_llm._selecionar_historico_com_orcamento` mantém uma cauda cronológica
limitada; o caminho atual não reintroduziu as fontes relevantes antes desse
corte. Limitar a janela é uma restrição útil. **Não remover o limite nem
considerar aumento de janela solução demonstrada.** O contrato faltante é
recuperar contexto pertinente e sua proveniência antes de aplicar o orçamento.

Controle real `contraste_curto`:mesmas entradas12,13 e19 em perfil novo, com
os mesmos owners e modelo. A fonte da função de Leo chegou ao transporte e a
resposta identificou música. Falsifica falta de informação original, perda na
persistência e incapacidade absoluta de lidar com esse papel. Uma repetição
curta não prova generalização nem que toda alucinação seja causada pelo corte.

### Resposta obsoleta: nova entrada está presente, mas a autoria repete

No4 o último user do HTTP é o relato atual de exercícios concluídos.
O Qwen retorna, em HTTP200, a mesma resposta anterior sobre o caderno; essa
proposta é publicada. No13 ocorre o mesmo padrão. Não é duplicação da
publicação: cada turno tem somente uma resposta. Não culpar entrega ou ausência
da fala atual por esses dois casos. Permanece aberta a revisão do atendimento
ao ato atual, sem proibir repetições explicitamente solicitadas.

### Correção pessoal passa a expectativa operacional

No14 a origem observada é anterior à entrega: turno `misto`, autorização
operacional verdadeira e roteiro `resultado_observado`, embora nenhum comando
tenha sido proposto ou executado. O rascunho reconhece a troca verde→amarelo;
a fala final vira “Entendi a ação que você pediu...”. Não atribuir esse sintoma
à geração de um comando pelo Qwen: o envelope autoral não contém comando.

`classificacao_sem_efeitos.json` reproduz a classificação composta fora da
conversa longa. Variantes pessoais simples não recebem autoridade, enquanto
“abra o aplicativo Calculadora” continua comando. Portanto a falha não exige
memória longa nem receipt simulado anterior (o14 antecede o primeiro comando16).
Mecanismo interno da composição de segmentos/sujeito ainda precisa de estudo;
não criar exceção para caderno, cores ou a frase histórica.

### Perspectiva e continuidade de último resultado

Trocas de usuário/assistente nos15/21/27/28 são evidências de atribuição
inadequada. Não basta substituir `eu` por `você`: citações e falas legítimas
da IA exigem fonte e falante próprios. Hipótese de contrato compartilhado
de perspectiva, ainda não encerrada.

No29 há consumo pelo pré-fluxo, sem envio autoral daquela pergunta. A chamada
registrada no intervalo que termina em “Resuma tudo acima...” pertence ao
resumo auxiliar; não foi tratada como geração da resposta atual. O último
resultado de aplicativo tomou o lugar do plano da conversa. É uma fronteira
de vinculação do ato/contexto, separada do corte de histórico no transporte.

## Responsáveis e critérios para correções posteriores

| Contrato / owner | Critério de validação |
| --- | --- |
| Contexto compartilhado/seletor + preparação do modelo | Retomada deve recuperar fontes antigas necessárias, com ocorrência/falante/correções, antes do corte. Manter limites e não promover fala inventada da IA a fato do usuário. |
| Autoria/revisão comunicativa | Atender o novo ato quando a fonte atual está presente; manter repetição pedida e perguntas legitimamente iguais como controles. Não usar mera similaridade/ausência de palavra como prova. |
| Modalidade/contrato de fala | Relato/correção pessoal não viram pedido de efeito; testar cláusulas compostas, sujeitos explícitos/elípticos e comandos diretos sem ampliar autoridade por contexto. |
| Memória/proveniência/perspectiva | Preservar quem disse, de quem é o objeto, posição corrigida e escopo da negação. Citação literal do usuário continua citação, não experiência da IA. |
| Pré-fluxo/continuidade | Último receipt não substitui novo assunto nem torna pergunta sobre plano em feedback de aplicativo. Testar efeitos confirmados, falhos e simulados separadamente. |
| Transporte | Timeout continua timeout, sem mascarar como falta de contexto ou “não lembro”. Não misturar F3 com correções C5/C7/F1. |

Os casos mantêm vínculos às famílias históricas C5/C7/F1/F3. São fronteiras
distintas;30 turnos e vários sintomas não equivalem a30 bugs nem provam uma
raiz única. Antes de aplicar candidato, localizar primeiro RED de cada família,
falsificar alternativas e criar regressão canônica com variantes em outros
assuntos. A conversa longa permanece regressão integrada, não substitui o
RED focado. Teste sozinho não melhora o entendimento: fornece a evidência para
uma correção arquitetural verificável.

## Correção do isolamento do próprio teste

As tentativas preliminares de setup foram preservadas. As guardas bloquearam
formato Windows da consulta Git, inicialização de console e escrita de cache
do AppOpener. São falhas do isolamento antes da conversa; não REDs de coerência.
Consultas Git foram reconhecidas estritamente, shell/integração de app foram
suprimidos e nenhum bloqueio foi liberado para ações de domínio.

A primeira rodada curta retornava só `False` do mock de efeito e produziu
turno silencioso. Esse mock não publicava o resultado que um executor moderno
deve publicar. Não usar essa rodada para diagnosticar produção. O adaptador
canônico foi reutilizado no simulador para publicar resultado negativo e
conclusão textual. A rodada curta seguinte teve uma conclusão por turno e
receipt negativo; só então a rodada longa começou. Não houve patch de produção
para compensar um harness incompleto.

A única guarda bloqueada durante a rodada longa foi uma sondagem de bind
IPv6 local, na inicialização da biblioteca de rede. Não houve escrita externa
admitida nem tentativa real de abrir aplicativos. O catálogo externo de apps
é simulado e a pesquisa web é bloqueada; isso limita o ensaio e não demonstra
o funcionamento das habilidades externas ou disponibilidade factual online.

## Entrega

`avaliar.py` verifica30 respostas, somente dois despachos esperados e seus
receipts negativos, sem alteração de produção; produz `resumo.json`,
`fronteiras.json`, `avaliacao.json` e a transcrição. `executar_coleta_longa.py.txt`
preserva a versão usada nos30 turnos; `executar.py` ganhou somente opção de
seleção para o controle curto posterior. Ambos mantêm as guardas de efeitos.

Nenhuma mudança em módulos de produção, modelo, configuração, voz pessoal,
UI ou hardware; nenhum commit, reinício pessoal ou shutdown. Não é preciso
reabrir a Laylay por este diagnóstico. Dados da sessão de teste ficam na pasta
isolada e não devem ser promovidos a memória pessoal ou treino.
