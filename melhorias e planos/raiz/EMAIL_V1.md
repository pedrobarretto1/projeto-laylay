# E-mail V1 — compreensão e operações com identidade preservada

Autorização de Pedro em 13/10/2026: implementar no Gmail atual a compreensão
de mensagens, continuidade de perguntas, rascunhos persistentes e operações
de trabalho. Várias contas ficam para depois, com uma principal e triagem das
secundárias por prioridade. Não houve autorização para enviar mensagens de
teste a terceiros ou modificar e-mails pessoais para validar a implementação.

## Base e preservação

- HEAD inicial e atual: `d850b8c90cc5ce40bd4832e759ed991ba88cd5cc`, branch `main`.
- `git status --short` foi consultado antes do primeiro RED. A worktree já
  continha mudanças extensas em corpo/firmware, conversa, contexto, receipts,
  terminal e testes. O baseline daquela execução está na saída das ferramentas
  da investigação, não deve ser substituído pelo estado posterior ao candidato.
- Nenhum reset, restore, clean, pull, rebase, troca de modelo, mudança de
  configuração ou commit. Fontes compartilhadas já alteradas foram editadas
  apenas nos blocos de integração causalmente necessários.
- Evidência real registrada sem remetentes, assuntos, corpos ou credenciais.
  Rascunhos das sondas são sintéticos e ficam em memória de teste temporária.

## Raízes e fronteiras distintas

### EMAIL-IDENTIDADE-01 — aviso sem referência recuperável

O transporte antigo só buscava cabeçalhos. A central preservava assunto e
remetente, mas descartava a identidade da mensagem. Não era apenas problema
de entender a expressão “que tipo de entrega?”. Um intérprete correto não
conseguiria buscar o corpo a partir daquele contrato.

REDs: referência descartada na sanitização do aviso, ausência de leitura de
corpo, consulta vazia sem resultado explícito. Sete controles legados passaram
enquanto os três REDs novos falharam, antes de alterar produção.

Owners: transporte Gmail para leitura e identidade; central para a entrega
do aviso; estado compartilhado para referência, seleção e TTL. O corpo é lido
por `BODY.PEEK[]` em seleção somente de leitura. Conta, pasta, UID e UIDVALIDITY
são validados; IDs globais de mensagem e conversa vêm do servidor Gmail.
Referência do aviso entra no contexto somente após receipt de entrega.

### CONTEUDO-RELATO-01 — explicação confundida com confirmação externa

Na composição instalada com Qwen real, o prompt inicial negou informação
presente: “Seu teclado chega amanha. Rastreio AB123.” chegava integralmente
ao modelo, mas ele exigia verificação externa para explicar o relato.
Foram falsificadas ausência do corpo e perda no transporte até a chamada.

Contrato compartilhado `explicar_texto_observado`, em `resumo_conteudo.py`:
explicar o que uma fonte afirma não certifica que aconteceu no mundo externo.
Pergunta, texto consultado e citações literais sustentam a proposta explicativa.
As citações são conferidas pelo host, mas não provam por si só aderência
semântica completa; interpretação continua sujeita à qualidade do modelo.
Os testes exercitam o mesmo contrato com fonte e-mail, arquivo e página.
Se a geração falhar, o extrato é identificado como extrato, sem falsa resposta.

### EMAIL-REVISAO-01 — operação precisa conservar artefato e versão

Rascunho persistente é artefato de trabalho pedido pelo usuário, não memória
factual aprendida. Destinatários, assunto, corpo, anexos, conta e versão são
revisados. Pendência canônica guarda ID/versão/hash, não bytes ou cópia do corpo.
Editar invalida a revisão. CAS no SQLite impede dois envios da mesma versão.
Recusa, cancelamento, falha e incerteza têm conclusões explícitas.

Controles adicionais reproduziram aceites operacionais legados (“pode abrir”)
como aceite de envio. O consumidor usa `somente_aceite_generico=True` do
resolver compartilhado; só os verbos de envio do próprio domínio resolvem
explicitamente sua pendência. Comando independente não vira confirmação.

Revisão final reproduziu oito REDs de alvo/roteamento: IDs explícitos de
rascunho eram perdidos em edição/descarte/envio; ID inválido recaía no ativo;
“apaga esse email” criava rascunho e “manda ... para a lixeira” não chegava à
operação certa. O lookup/persistência já aceitava o ID correto, falsificando
falha geral de armazenamento. A primeira divergência estava no detector do
domínio. Agora preserva referência explícita mesmo inválida, distingue caixa
de rascunho e seleciona verbo no núcleo canônico, sem usar verbos do conteúdo.
Descartar outro ID preserva o rascunho ativo. A composição instalada confirma
esse caminho e bloqueia envio com ID inexistente. Consulta singular mostra o
rascunho atual; consulta plural lista. Controle musical preserva comando novo.

Anexos usam o owner compartilhado de arquivos e o coordenador cooperativo:
até cinco arquivos e 12 MB totais. Raízes/sensibilidade são verificadas;
manifesto com SHA-256 é revalidado antes do envio. Falha de arquivo bloqueia
a etapa dependente. SMTP aceito não comprova entrega ao destinatário; parcial
ou incerto ficam sem retry automático. IMAP que perde a releitura depois da
mutação publica incerteza, não uma falsa garantia de que nada mudou.

## Inventário e integração

| Responsabilidade | Serviço reutilizado |
|---|---|
| Estado, referência e seleção | `EstadoCompartilhadoRuntime` |
| Ciclo de vida e troca de chat | `ciclo_vida_contexto`, `sessao_conversa`, `conversas_runtime` |
| Modalidade e autorização | classificador/arbitragem canônicos; vocabulário de e-mail acrescentado ao léxico compartilhado |
| Confirmação, recusa e concorrência | `PendenciaAcaoRuntime` |
| Ordinais | `extrair_indice_referencia_ordinal` |
| Modelo, schema e orçamento | `RegistroModeloLLM`, `ContratoSaidaEstruturada`, preparador/transporte existentes |
| Voz e receipt | executor informativo, adaptador de resultado e orquestrador de fala existentes |
| Aprendizado | motor compartilhado para eventos de pendência/correção; confirmação não vira preferência permanente |
| Notificação | central compartilhada, com identidade preservada após entrega |
| Cooperação de arquivos/e-mail | quadro, governança e executor cooperativos existentes |
| Consciência da capacidade | catálogo vivo, disponibilidade operacional e recuperação contextual |

Não existe um parser privado de sim/não, segunda memória mental, segundo
transporte LLM ou permissão derivada do corpo recebido. Referências expiram
em dez minutos; trocar/renovar o chat limpa a seleção. Rascunhos continuam
salvos localmente e podem ser consultados novamente pelo ID mostrado.

## Comportamento implementado

- Consultar não lidos, buscar por remetente/termo, ler mensagem selecionada,
  perguntar sobre o conteúdo e consultar até cinco mensagens da conversa.
- Escolher por ordinal, manter a lista e voltar à mensagem anterior.
- Criar, mostrar, listar, editar e descartar rascunhos locais; resposta e
  encaminhamento são preparados como rascunhos, com revisão antes do envio.
- Pedido de e-mail novo pode preparar um rascunho antes da revisão de envio.
  Não reutiliza o rascunho anterior para outro destinatário explícito.
- Marcar como lido/não lido, arquivar e mover para a lixeira exigem confirmação
  da mensagem exata e releitura do estado. Nenhuma exclusão permanente.
- Arquivos anexados usam leitura autorizada e revalidação compartilhadas.

Exemplos para experimentar após carregar a nova versão:

```text
lê meus emails
lê o segundo email
que tipo de entrega?
tem código de rastreio?
quando chega?
mostra a conversa desse email
prepara um email para ENDERECO dizendo que o relatório será enviado na sexta
deixa mais formal
anexa o arquivo "CAMINHO COMPLETO"
mostra esse rascunho
envia esse email
sim
lista os rascunhos
mostra o rascunho ID
```

## Evidência e limites

- Testes: `scripts/tests/test_email_conteudo_operacoes.py` e
  `scripts/tests/test_email_composicao.py`; regressivos incluem notificação,
  aprendizado, segurança, catálogo, composição, arquivos, cooperação e contexto.
  Última execução focada: **91 passed**, incluindo silêncio qualificado pelo
  motor compartilhado, sem tratá-lo como autorização ou preferência ativa.
- Regressão de 32 módulos em `regressao_final_v2.json`: **538 passed,
  22 subtests passed, 3 failed**. Uma seleção anterior mais ampla teve 795
  verdes e os mesmos três REDs. Eles envolvem hipótese de criação de arquivo,
  sua resposta prioritária e negativa de capacidade musical indisponível.
  `controle_sem_blocos_email.json` reproduz os três (75 controles verdes)
  removendo em memória somente os novos blocos lexicais, porta prioritária e
  descrições de e-mail. Hashes antes/depois confirmam fontes preservadas; as
  mudanças paralelas continuaram presentes. Não foram removidos nem corrigidos
  para maquiar a regressão. A comparação antecede os refinamentos finais de
  ID/roteamento; os mesmos REDs permaneceram na regressão final.
- Sonda: `scripts/analises/sonda_email_v1.py`. Importa `laylay.py` sem `main`,
  conserva o executor/receipt/estado/voz textual instalados, controla IMAP e
  SMTP externos e usa rascunhos/memória temporários. `--modelo-real` usa a
  configuração local existente, sem troca de modelo. Recusa sobrescrever coleta.
- `resultados_testes/email_v1/modelo_real_diagnostico/relatorio.json`: RED
  semântico com corpo recebido integralmente.
- `resultados_testes/email_v1/fluxo_modelo_real_v3/relatorio.json`: perguntas
  sobre produto/rastreio, criação e edição por Qwen real, revisão e um envio
  sintético; “pode abrir” e o segundo “sim” não enviaram. Não comprova SMTP real.
- `resultados_testes/email_v1/probe_real_sanitizado.json`: consulta e leitura
  reais com UIDVALIDITY/IDs Gmail, autenticação SMTP e NOOP confirmados. Nenhum
  SMTP SEND ou mutação IMAP foi executado na conta real.
- `py_compile` e `git diff --check` passaram. Ruff não está instalado nesse
  ambiente; não foi instalado nem usado como evidência de validação.

Ainda abertos: envio/recebimento real de uma mensagem de teste autorizada,
alterações da caixa em uso real e conversa na sessão desktop diária depois
de carregar as fontes novas. Esta investigação não reiniciou nem encerrou
a sessão diária. Não declarar GREEN runtime global a partir desta sonda.

Limites da V1: uma conta, rascunhos locais (não aparecem automaticamente na
pasta Rascunhos do Gmail), leitura do corpo textual; conteúdo dos anexos
recebidos ainda indisponível. Consulta/lista e texto têm limites anunciados.
Autoria é uma proposta revisável; citações literais não certificam toda a
interpretação. Resultado incerto não deve ser repetido como sucesso.

## Escopo do candidato aplicado

Produção criada: `integracao/caixa_gmail.py`, `especialistas/email_runtime.py`,
`cognicao/linguagem_email.py` e `memoria_mental/rascunhos_email.py`, sob
`mente_laylay/`.

Produção alterada nos blocos necessários:

- Gmail/notificação: `gmail_mental`, `composicao_gmail`, `central_notificacoes`.
- Texto/arquivos/cooperação: `resumo_conteudo`, `pesquisa_semantica`,
  `registro_arquivos`, `orquestracao_cooperativa`.
- Execução/catálogo: `executor_informacoes`, `capacidades`, `mapa_habilidades`,
  `classificacao_habilidade`, `continuidade_geral`, `interpretacao_intencao`.
- Linguagem/estado: `modalidade_turno`, `gramatica_operacional`,
  `referencias_linguagem`, `ciclo_vida_contexto`, `sessao_conversa`,
  `conversas_runtime`, `disponibilidade_operacional`, `estado_contexto_runtime`.
- Wiring: `laylay.py`, `contexto_execucao_ia`, `composicao_contextos_ia`,
  `composicao_entrada_interacao`, `coordenador_intencao`,
  `orquestrador_deterministico`, `comandos_imediatos`,
  `composicao_estado_aplicacao`.

Nenhuma alteração desta investigação em firmware, terminais, decisão corporal,
executor musical, transporte/modelo/voz configurados ou credenciais.
Diffs nesses domínios pertencem ao trabalho paralelo. Nenhum commit criado.
`ROADMAP_NOVAS_HABILIDADES.md` não existe nesta checkout; o estado do incremento
foi registrado no mapa causal, registro e neste handoff, sem criar um roadmap
substituto desconectado.

Referências técnicas verificadas: [extensões IMAP do Gmail](https://developers.google.com/workspace/gmail/imap/imap-extensions),
[IMAP/SMTP do Gmail](https://developers.google.com/workspace/gmail/imap/imap-smtp),
[SMTP do Python](https://docs.python.org/3.14/library/smtplib.html).

## Continuação após o RED desktop de 13/10, 19:34

O log fornecido por Pedro confirmou consulta, seleção do segundo e-mail e
leitura do corpo do TotalPass. A primeira fronteira RED observada estava na
explicação, que retornava um extrato bruto. A prova anterior com texto sintético
curto não cobria a mensagem real com formatação e links. HEAD permaneceu
`d850b8c90cc5ce40bd4832e759ed991ba88cd5cc`; status da worktree foi registrado
antes da investigação e as novas alterações paralelas foram preservadas.

### CONTEUDO-REFERENCIA-01 — o modelo reescrevia a própria prova textual

Não fundir com CONTEUDO-RELATO-01: ali o modelo exigia confirmação externa;
aqui a explicação era produzida, mas sua forma de evidência era rejeitada.

O corpo real tinha 4698 caracteres, dos quais 3191 em 16 URLs. O primeiro
controle atingiu 20 segundos sem resposta. Remover URLs em memória reduziu a
demora, mas continuou RED: o modelo retornou citações com espaços/quebras de
linha alterados. Com a fonte original e prazo diagnóstico maior, retornou oito
citações, excedendo quatro, com divergências literais. Foram falsificadas perda
do corpo, indisponibilidade geral do modelo e a hipótese de URLs como causa
suficiente. O controle curto passou. O prazo maior foi só diagnóstico; não
alterou timeout ou configuração de produção.

Owner: `explicar_texto_observado`, compartilhado por leitores de e-mail,
arquivo e página. Agora indexa trechos literais da fonte. A LLM seleciona até
quatro IDs; o host valida existência, tipo e unicidade e materializa as
citações originais. Não há casamento aproximado, tolerância a texto inventado
ou remoção da guarda. A associação semântica da resposta aos trechos continua
uma proposta do modelo, não certificação de efeito externo.

O schema negociado passou de strings em `citacoes` para inteiros em
`evidencias`; o resultado público conserva `citacoes` literais. Fixtures de
transporte foram atualizadas por essa mudança explícita de contrato, e novos
negativos rejeitam IDs inexistentes, booleanos, floats, repetidos, mais de
quatro, ausência de evidência e citações autoradas pelo modelo.

### EMAIL-LINGUAGEM-01 — seleção da fonte não é pergunta sobre seu texto

Dois controles da mesma fronteira do detector:

- Perguntas como “qual o cupom desse email?” e “o que pedem nele?” usavam um
  subconjunto privado de pronomes. “Que desconto esse email oferece?” vinha
  como `natureza_acao=consulta` do owner canônico, e o consumidor aceitava só
  `modalidade_geral=pergunta`. Agora reutiliza `texto_tem_referencia_contextual`
  e a modalidade de consulta, conservando bloqueios e comandos independentes.
- “Lê o segundo email” escolhia corretamente a fonte, mas era entregue ao
  modelo como pergunta literal sobre o corpo. Após resolver a evidência, o
  modelo respondeu com o link de visualização. O controle com tarefa de
  síntese, mesma fonte/modelo, explicou a oferta. O detector agora separa
  seleção simples de leitura e consulta específica: leitura pede síntese do
  assunto; perguntas específicas conservam o texto do usuário. A fala original
  continua sendo a autorização, e o índice continua sendo resolvido pelo host.

Resposta vazia do modelo não entra no decoder JSON como se fosse texto válido.
Falha de compreensão publica código sanitizado no diagnóstico, separado da
leitura confirmada; falha do observador não impede a conclusão do turno.

### Provas posteriores ao candidato

- **111 testes focados verdes**, com REDs prévios de referência/evidência,
  consulta natural, seleção versus pergunta e diagnóstico. Contrato de fonte
  também exercitado em arquivo e página; nenhuma mudança nos respectivos
  executores, nem novo parser de confirmação.
- Regressão dos mesmos 32 módulos: **560 passed, 22 subtests passed, 3 failed**,
  em `resultados_testes/email_v1/regressao_leitura_desktop.json`. São os mesmos
  três REDs paralelos anteriormente isolados, sem novas falhas.
- `falha_desktop_diagnostico/resumo.json`, `falha_desktop_controles/resumo.json`
  e `falha_desktop_validacao/resumo.json` conservam métricas das falsificações,
  sem corpos/credenciais. `controle_pedido_de_leitura/resumo.json` conserva
  respostas do modelo com URLs suprimidas para a comparação da tarefa.
- `falha_desktop_green_real_v2/resumo.json` preserva o verde intermediário:
  desconto/cupom corretos, mas síntese genérica ainda escolhendo o link. Não
  promover esse verde intermediário a conclusão da raiz.
- **`falha_desktop_green_real_v3/resumo.json`**: composição instalada,
  transporte Gmail e Qwen reais; mesma referência nas três leituras. Síntese
  informa desconto de 30% e TP2; perguntas retornam desconto e cupom conferido
  no corpo. Uma fala por turno, sem fallback ou URLs brutas. Tempos totais
  10,65 s, 5,63 s e 4,24 s. Sem mutação IMAP, SMTP SEND ou leitura de anexos.

Escopo deste ajuste de produção: `resumo_conteudo.py`, `linguagem_email.py` e
`email_runtime.py`. Testes e fixture da sonda acompanham o novo schema. Nenhuma
troca de modelo, configuração, conta, timeout, firmware ou commit. `py_compile`
e `git diff --check` passaram. A sessão desktop diária não foi reiniciada por
esta investigação; carregar as fontes e repetir nela continua sendo a próxima
prova de experiência, distinta da composição instalada com portas reais.
Latência da primeira chamada permanece uma observação separada, sem afirmar
causa ou melhora geral de desempenho. Envios e mutações reais continuam abertos.

## NOTIFICACOES-APRESENTACAO-01 — repetição após consulta manual, 13/10, 20:45

Pedro relatou uma lista entregue às 20:44:53 seguida de um aviso sobre o mesmo
LinkedIn às 20:45:25. A segunda frase foi localizada no compositor de fala
proativa (prefixo de e-mails ajustado ao período noturno), a partir do texto
singular da central. Não era uma segunda resposta do executor EMAIL_READ.
Owner da decisão: central de notificações; fila/porteiro conservam ownership
da entrega. Contrato ausente: apresentação manual confirmada de uma identidade
precisa satisfazer aviso automático da mesma identidade.

Foram falsificadas duplicação do executor e identidade incompatível entre
consulta e monitor: a composição instalada entregou uma resposta manual, e
ambos conservam o mesmo UID global/conta. A central possuía dedupe de ingestão
e receipt do anúncio automático, mas não recebia o receipt da apresentação
manual. A fila persistente preservava o aviso depois do turno. Somente adiar
mais ou silenciar todos os e-mails esconderia o contrato ausente.

O executor informativo agora publica `itens_apresentados` no receipt canônico,
com identidade/origem e âncora textual dos cinco itens realmente mostrados.
Os demais quinze consultados não são marcados como apresentados. O orquestrador
compartilhado captura o mesmo retrato usado na validação/deduplicação e entrega
seus receipts aos observadores somente após publicação textual ou reprodução
de áudio confirmada. Enfileirar, ler, contexto/última ação e autorização não
substituem esse receipt. Callback tardio conserva a identidade capturada.

A central valida origem executor, confirmação, ocorrência, canal e presença
literal da âncora na fala entregue. Guarda chaves opacas/canal/receipt por até
sete dias, limitada a400 registros, com a mesma janela do dedupe existente.
Não altera preferências, não aprende silêncio e não marca mensagem como lida
no Gmail. Eventos continuam no resumo. `anunciado` continua reservado ao
receipt do anúncio automático; apresentação manual tem registro separado.

A fila recebeu uma porta opcional genérica `preparar_entrega_cb`. Antes de
compor/publicar o lote, consulta o owner: lote satisfeito é dispensado, lote
parcial é recomposto apenas com os itens restantes. Falha na preparação adia
fail-closed; não publica texto antigo como sucesso. Guardas do porteiro,
conversa ativa e prioridade continuam aplicadas. Um evento realmente novo e
itens fora da parte mostrada continuam elegíveis. O contrato é compartilhado
e os controles também exercitam avisos de sistema, sem heurística exclusiva
para LinkedIn ou o assunto histórico.

Provas:

- RED antes do candidato:8 contratos da central ausentes e2 contratos de
  entrega do orquestrador ausentes. Depois: **166 focados verdes**, incluindo
  consulta antes/depois da ingestão, lote total/parcial, persistência, identidade
  distinta com mesmo assunto, fonte/canal inválidos, falha de voz, retorno
  tardio e somente os cinco itens mostrados.
- A sonda de composição instalada ganhou `notificacao_apos_consulta`: fila
  preparada antes da consulta, uma resposta manual, zero repetições no flush,
  outro ID anunciado. Nenhuma reprodução física ou envio SMTP na sonda.
- `resultados_testes/email_v1/notificacoes_consulta_real/resumo.json`:
  Gmail real readonly, composição/central/fila instaladas, aviso real LinkedIn
  preparado antes da consulta;20 mensagens selecionadas, uma resposta manual,
  zero duplicadas, fila vazia e zero avisos pendentes. Timer e áudio controlados;
  fontes/memória de teste temporárias, resultado final sanitizado sem assuntos,
  corpos ou credenciais. Não comprova reprodução física na sessão diária.
- Regressão de42 módulos em
  `notificacoes_consulta_regressao_v3/resumo.json`: **910 passed,
  22 subtests passed, 3 failed**, os mesmos REDs paralelos de conversa.
  Os dois controles de root passam com a composição isolada. A primeira
  execução comum teve469 verdes e2 bloqueios de instância (Laylay diária aberta).
  Uma tentativa posterior de isolar o root contaminou testes ao manter os
  construtores temporários da sonda:30 falhas/883 verdes, preservada em v2.
  Restaurar apenas esses construtores após compor o root resolveu essa
  contaminação sem editar testes/produção nem disputar o mutex da sessão real.
  Um refinamento final do retrato capturado foi validado pelos166 focados.

Produção alterada neste incremento:central_notificacoes, email_runtime,
executor_informacoes, orquestrador_fala_runtime, voz_runtime e wiring em laylay.
Arquivos completos já aplicados; nenhuma edição manual necessária. Preservadas
mudanças paralelas (inclusive teste de modo jogo presente na base desta rodada).
HEAD continua d850b8c90cc5ce40bd4832e759ed991ba88cd5cc; nenhum commit, reset,
mudança de configuração/modelo ou reinício da Laylay. `py_compile` e
`git diff --check` verificados. Próxima prova:recarregar fontes e repetir na
sessão desktop diária, mantendo a distinção entre entrega textual e audição.
