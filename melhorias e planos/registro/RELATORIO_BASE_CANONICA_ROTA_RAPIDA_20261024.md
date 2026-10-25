# C5/P01 — base canônica na projeção do envio rápido, 24/10/2026

## Resultado e responsabilidade

Corrigida a ausência da base principal em pedidos conversacionais vinculados ao
turno atual que começavam pela rota rápida. A base configurada pelo host deve
estar no envio comum, independentemente de já existir no histórico. A instrução
efêmera do turno não substitui a base e não é memória do usuário.

Produção alterada somente em
`mente_laylay/autonomia/contexto_resposta_ia.py`, no método
`ContextoPromptRuntime.preparar_envio_modelo`. A correção altera a projeção do
pedido, sem escrever no histórico nem modificar personalidade, prompt-base,
modelo, configuração, seletor, orçamento, autoridade, executor ou receipts.
Nenhum commit ou reinício da sessão pessoal.

O owner do preparo possui a base configurada e já recebe todos os envios
da rota normal e rápida. Portanto é a fronteira adequada para garantir sua
presença. Não foi criada uma inicialização paralela no dispatcher, na memória,
em cada habilidade ou no cliente HTTP.

## Base congelada e primeira fronteira

HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, branch `main`, worktree
previamente suja preservada. Artefatos em
`resultados_testes/base_canonica_rota_rapida_20261024/`: baseline com status e
527 hashes, cópia exata do owner anterior em `fontes_antes/`.

Cadeia demonstrada na coleta anterior:

1. O histórico pode começar vazio ou conter apenas falas user/assistant.
2. A rota normal chama `preparar_pacote/preparar`, que inclui a base principal.
3. A rápida chama somente `preparar_instrucao_rapida`. O próprio contrato desse
   método diz que sua instrução efêmera não substitui a base.
4. `EstadoConversaRuntime` registra a utterance com o papel correto; ele não
   possui a base da personalidade nem deve inventá-la.
5. A projeção do envio não garantia a base. O primeiro item podia ser user ou
   somente a instrução efêmera system.
6. `preparar_payload_llm` não reconhecia esse primeiro item como prompt
   principal. Seguia o corte legado e perdia fontes, mesmo elas estando no
   pedido interno e cabendo no orçamento canônico.
7. O Qwen respondia não localizar a preferência. Este sintoma de geração não
   era necessário para reproduzir a ausência de fonte no transporte.

O primeiro contrato quebrado está antes do transporte: a preparação do envio
comum recebia um pedido vinculado sem garantir a base que lhe pertence. O
registro da conversa e o seletor não apagaram as declarações.

Falsificações:
- Não é falta de memória: fontes constam no histórico e no pedido tipado.
- Não é insuficiência inevitável do orçamento: inserir somente a base nos
  mesmos pedidos5/6 faz as fontes chegarem, sem alterar seletor ou limites.
- Não é falha de geração: mesma resposta HTTP controlada e mesma factory,
  trocando apenas este owner, reproduzem a diferença.
- Não é preciso persistir a personalidade no histórico para corrigir: o
  candidato insere somente no clone do envio e testes preservam a memória.
- A base escrita numa mensagem user não se torna instrução system; uma base
  precisa vir da configuração do host ou de mensagem system já reconhecida.

A prova de inserir apenas a base está em `falsificacoes.json`. Esta raiz é
distinta da perda lexical corrigida antes: com base e seletor anteriores à
correção lexical, certas consultas ainda não recuperariam as declarações.
Preservar C5/P01, sem fundir geração livre, revisão e retomada operacional.

## Contrato compartilhado aplicado

Depois dos retornos dos pacotes fechados, um envio comum recebe a base
configurada quando:
- a identidade do turno e do contrato coincide;
- a autoria está vinculada ao canal e ao texto atuais;
- a configuração possui uma base não vazia;
- a primeira mensagem ainda não contém base configurada ou perfil canônico
  reconhecido pelo mesmo leitor usado na preparação do transporte.

O preparador insere uma nova mensagem system antes das mensagens existentes;
não converte falas user/assistant em instruções e não descarta o contrato
efêmero. A negociação de autoria posterior mantém seus campos, schema,
inventário de fontes e reserva de saída.

Base existente, prefixos/sufixos do host e perfis longo/rápido/compacto são
preservados sem duplicação. Pacotes fechados continuam com seus protocolos
próprios. Identidade/canal divergentes não autorizam esta projeção. O patch não
concede permissão para executar e não transforma conteúdo lembrado em receipt.

A preservação de uma base personalizada genérica foi testada. Isso não promete
recuperação histórica para todo prompt personalizado: o seletor canônico de
transporte continua dependendo do reconhecimento de prompt principal. O
benefício de recuperação foi demonstrado com a base real configurada da Laylay
e a otimização de contexto ativa.

## RED e testes permanentes

`scripts/tests/test_base_canonica_envio_conversa.py`:
- seis REDs causais antes do patch, com sete controles;
- contraprova do owner congelado repete os mesmos seis REDs/sete controles;
-14GREEN na versão final, incluindo a factory em aplicativo, bebida e jogos,
  com histórico inicial sem base, correção preservada e pedido antigo que não
  pode ser reexecutado;
- a factory propõe comando não autorizado na folha HTTP e comprova ausência
  de efeito/autoridade. Sua memória continua começando por fala user: não foi
  normalizada silenciosamente para fazer o teste passar;
- bases existentes, papel user com texto da base, base customizada e identidade
  divergente protegem os comportamentos vizinhos.

Provas principais: `contrato_red_causal.xml`, `contrafactual_contrato.xml`,
`contrato_final.xml`. Execuções iniciais de teste com ID artificial incompatível
e com expectativa de igualdade que ignorava a negociação de autoria preexistente
foram preservadas, mas não contadas como RED do defeito.

A revisão independente do único diff não encontrou bloqueio concreto e
confirmou os13controles leves antes da inclusão da factory. Observou o limite
da base customizada, registrado acima.

O primeiro conjunto vizinho executou213GREEN,2SKIP e oito REDs em
`test_geracao_limite_sem_estado.py`. Os MESMOS oito foram reproduzidos com o
owner congelado em `vizinho_orcamento_baseline.xml`:
- seis casos de `test_pergunta_relato_pedido_e_misto_nao_viram_recusa_curta`
  esperam igualdade literal do pacote, apesar da instrução de negociação de
  autoria já existir antes deste candidato;
- duas variantes de `test_orquestrador_preserva_utterance_e_envia_apenas_realizacao_do_ato`
  esperam256tokens onde o envelope preexistente reserva1024.

São expectativas vizinhas anteriores, não regressões produzidas por esta
inserção de base. Não foram apagadas, alteradas ou incorporadas à correção.

## Composição instalada e Qwen

O par `composicao_baseline_final.json`/`composicao_candidato_final.json`
reutiliza os históricos exatos de5/6da coleta
`recuperacao_atos_fala_20261024/foco_final`, sem inserir base no fixture.
O loader da contraprova carrega somente o owner congelado e mantém as demais
dependências. A memória raiz é redirecionada em RAM; folhas externas são
isoladas. Mesmos pedidos e folha HTTP:base anterior perde as duas fontes,
candidato envia primeira mensagem system e ambas as fontes completas.

A primeira verificação causal é a presença da base no PedidoModelo; depois
vem a fonte no HTTP da pergunta atual, papel/ordem, publicação e ausência de
efeito. A resposta da folha controlada não é prova de recuperação ou verdade.

`foco_final` com Qwen local `qwen3:4b-instruct`:14turnos/14conclusões,
15HTTP200,5pacotes de fontes conferidos contra o pedido,527fontes sem drift,
um comando simulado com receipt negativo,nenhuma voz/efeito real,97,704s.
Nos5/6,o modelo respondeu “Você disse preferir Obsidian” e “Você disse não
gostar de café”. A prova `prova_inicializacao_real.json` verifica a base em
todos os pedidos principais abertos e as fontes primárias nesses dois envios.

Não é GREEN de conversa geral. O mesmo foco ainda recusou respostas posteriores
e entrou em retomada operacional em8/10. A declaração de brincadeira é
ambígua quanto ao que retifica; não foi resolvida por uma exceção neste patch.
O revisor de paráfrases e a fidelidade da geração mantêm seus limites e owners.

Na coleta longa final `conversa_validada`:30turnos/30conclusões,33HTTP200,
13pacotes primários conferidos,527fontes sem drift,um receipt negativo simulado,
220,465s somados. Nenhuma voz ou efeito real. A base foi auditada nos25turnos
com pedidos principais abertos; os pacotes fechados mantiveram protocolo próprio.
Não houve timeout HTTP nessa amostra, mas29 ainda encerrou por limite de
tentativas. Não interpretar transporte200 como correção da resposta.

Falhas preservadas:5mistura rock/Obsidian;7troca enunciador ao dizer “eu disse”;
12/22alegam ausência ou desviam apesar de dados disponíveis;14/20entram em
retomada operacional de fala;26adota conteúdo de pergunta como preferência.
17identifica Dora e18retoma Obsidian, mas esses acertos não encerram coerência
geral. As duas transcrições e todos os resultados foram mantidos.

`fronteiras_abertas.json` registra modalidades, fontes, revisões e respostas.
Em23 a entrada sobre Atlas é pergunta sem autorização; em26 uma forma
normalizada dessa pergunta aparece como `opiniao` nas fontes do registro.
Isso é uma nova evidência sobre o tratamento do ato de fala, não prova do
momento ou writer responsável. A próxima investigação deve rastrear como a
pergunta é admitida/registrada e usada pela autoria/revisão, antes de atribuir
a causa somente ao Qwen ou criar exceções para Atlas/rock. Preservar C7/F1 e
C5/P01 gerais abertos, separados desta garantia da base no envio.

## Regressão final e entrega

A regressão foi ampliada para89módulos relevantes, incluindo os vizinhos que
não estavam no conjunto anterior:2.222GREEN,30subtests GREEN,14SKIP,
uma deseleção de import e nove falhas anteriores. O comando e os nomes estão
em `regressao_comando.json`/`regressao_ampla.xml`.

Oito são as expectativas de negociação de autoria/orçamento descritas acima,
reproduzidas nesta tarefa com o owner congelado. A nona é a seleção antiga de
MUSIC_SEARCH para `pode abri a calculadora para mim`, em
`test_pedidos_modais_autoridade.py::test_orquestrador_deterministico_resolve_mesmo_app_apos_moldura`.
A contraprova histórica está em
`resultados_testes/respostas_prazos_20261024/relato_composto/falha_vizinha_baseline.xml`.
Os testes e os REDs não foram apagados ou alterados para obter verde.

O teste de composição principal deselecionado passou isoladamente na factory:
um GREEN em `import_isolado.xml`. A exclusão evita importação pessoal sem o
isolamento já usado nas provas; não omite seu resultado.

`entrega.json` registra hashes antes/depois, escopo, comparação das falhas,
testes e coletas. `candidato_contra_base.patch` mostra somente a alteração
desta tarefa contra o owner congelado. Uma fonte de produção alterada entre
527conferidas; nenhum commit ou alteração de configuração. Esta fronteira
foi corrigida e validada; a suíte inteira e a compreensão geral continuam sem
declaração de conclusão.

