# Piloto de ajuste supervisionado do encoder — 2026-09-08

## Objetivo e limite

Testar se adaptar o encoder melhora identificação de ocorrência/variante/ato
em português, em comparação pareada com o mesmo encoder congelado. Não é
treino do zero, troca do Qwen de conversa ou liberação operacional da rede.
Só depois de melhorar essa fronteira avaliar alvos, relações e superioridade
sobre a composição real do interpretador atual.

Base: main, HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, worktree suja
preservada. Os protocolos v4 e o modelo configurado permanecem intocados.

## Decisões já tomadas

- Parar a sequência de ablações de atributos lexicais.
- Usar primeiro checkpoint MiniLM treinável, NÃO tentar ajustar o ONNX int8.
- Congelado e ajustado terão o mesmo checkpoint não quantizado, tokenizer,
  projeção de subtokens, cabeça, inicialização pareada e entrada bruta.
- Sementes fixadas: 27, 53, 89. A única diferença pretendida entre braços é
  atualizar ou não os parâmetros do encoder. Treinar a cabeça nos dois.
- O resultado antigo da MLP é referência histórica, não controle equivalente
  ao novo braço congelado. Não atribuir toda diferença entre eles ao fine-tuning.
- Seleção de época/configuração usa apenas seleção; calibração usa somente
  a partição destinada a isso. Reserva não entra nesses mecanismos.
- Critérios e orçamento serão fechados antes do primeiro fit, depois do
  inventário de dados e da prova técnica de memória. Ainda não estão fechados.

## Etapa 1 implementada: prontidão e preparação de dados

`mente_laylay/neural/protocolo_ajuste_supervisionado.py` define o envelope
experimental e o consumidor `preparar_particao`. Reutiliza:

- `supervisao_relacoes_v4.validar_fonte_relacional`: catálogo, atos, spans,
  alvos e relações, sem inventar outro interpretador;
- `comparar_ocorrencias_v4.rotular_ocorrencias`: projeção existente de rótulos
  para todos os tokens, sem deixar anotação entrar na entrada de inferência;
- `qualidade.auditar_leakage_dataset`: checagem lexical e de famílias.

Por caso, separar origem do texto de origem do rótulo. Texto de uso real
com anotação feita por IA continua tendo `origem_rotulo=curadoria_ia`.
Revisão pendente, linhagem desconhecida e exposição prévia são explícitas.
O código valida declarações; não certifica a identidade de quem revisou.

Partições: desenvolvimento, treino, seleção e calibração. Este leitor rejeita
reservas. Histórico pode ser deliberadamente incorporado ao treino em uma
etapa posterior, mas não pode reaparecer como seleção/calibração inéditas.
Os 1.176 casos v4 foram importados APENAS como desenvolvimento conhecido.

`supervisionado` reutiliza os nove rótulos variante/ato atuais. `fora_perfil`
exige motivo e nenhuma anotação operacional: por exemplo, referência sem
contexto, condicional, dúvida sobre capacidade, revisão temporal ou âncora
multitoken ainda não representada. Esses casos permanecem contabilizados,
mas não viram `ausente`, recusa ou pedido na perda do classificador.
Isso é uma limitação declarada do piloto, não uma regra do runtime da Laylay.

Para preparar treino, o corpus precisa de todas as nove combinações nas
três partições, pelo menos dois grupos de treino, ausência de parentesco
cruzado/duplicação/vazamento e ao menos um exemplo de uso real com revisão
humana declarada em cada partição. São mínimos técnicos, NÃO garantia de
diversidade suficiente. A revisão do conjunto ainda precisa justificar a
representatividade das famílias e a confiabilidade dessas declarações.

O consumidor só exporta texto na entrada; rótulos ficam separados. Corpus
válido não significa dados prontos; dados prontos não significam viabilidade
de fit, generalização comprovada ou autorização de execução/promoção.

## REDs do novo contrato e decisão arquitetural

Quatro regressões foram reproduzidas antes do endurecimento:

1. Casos já explorados podiam ser rebatizados como seleção/calibração.
2. Nomes de família equivalentes por caixa/espaços eram detectados pelo
   auditor canônico, mas o resultado não era consumido.
3. A preparação anunciava prontidão e depois falhava no alinhador v4 com
   frases em maiúsculas (`Para trabalhar ... Firefox`).
4. Duplicação dentro da mesma partição inflacionava o corpus sem impedimento.

No terceiro caso, os spans brutos eram válidos. O alinhador de normalização
era a operação errada para um piloto cuja entrada é a frase bruta já anotada:
o classificador normaliza caixa, enquanto o mapa usado pelo alinhador não
confirmava essa transformação. Não modificar normalizador/porteiro nem
converter a fixture para minúsculas. O adaptador agora usa a própria fonte
bruta como sistema de coordenadas para a projeção existente. Isso preserva
nomes, maiúsculas e offsets; não simula a composição de produção e não
transforma anotação em permissão. O alinhador v4 histórico não foi alterado.

Princípio reutilizável: preparar supervisão a partir da evidência anotada,
sem exigir que o interpretador que queremos avaliar decida a validade da
entrada. Sua validação estrutural continua obrigatória.

## Histórico: prontidão e ambiente antes da instalação — 2026-09-08

Auditoria real dos 1.176 casos, sem inferência nem fit:
`memoria/neural/experimentos/prontidao_ajuste_supervisionado_20260908/`.
Manifesto válido, dados ainda não prontos. Nenhuma partição inédita ou reserva
foi fabricada. O artefato contém os impedimentos e hashes de código/corpus.

Ambiente verificado: Python 3.14.6 da `.venv314`; PyTorch e Transformers não
estão instalados. GPU informada por `nvidia-smi`: GTX 1660 SUPER, 6.144 MiB.
O índice PyPI retornou distribuições compatíveis com a seleção do pip atual,
mas isso NÃO verifica CUDA, memória de treino nem o checkpoint. Não houve
instalação ou download de pesos. Não modificar `.venv314` para este treino:
preparar ambiente separado e fixar as versões após prova de compatibilidade.

## Próximas entregas, nesta ordem

### Atualização 2026-09-09: fila local de revisão preparada

`curadoria_encoder.py` exporta os registros pelos leitores/ledger canônicos,
agrupando apenas texto bruto idêntico. Conserva IDs, índice do registro válido
(não número de linha), origem do componente, evidência declarada e decisão
do ledger. Não exporta predições como labels, nem atribui partições/ancestrais.
Mesmo correção aprovada no ledger não substitui anotação por ocorrência.

Exportação real: `memoria/neural/experimentos/curadoria_encoder_20260909/`.
665 objetos válidos, 77 textos únicos, 658 receipts declarados verificados,
7 não verificados e zero registros de correção explícita na fonte atual. Os 665 registros
estão pendentes de revisão; duas revisões antigas referem-se a IDs ausentes.
Uma linha JSON inválida foi excluída da fila, sem reparo ou remoção da fonte.
Os arquivos originais permaneceram iguais (hashes conferidos antes/depois).

`origem=executor` ou `consulta_sistema_local` não informa chat/teste/caos;
todos os exemplos continuam com origem do turno desconhecida. A fila NÃO
é um corpus natural certificado, nem uma reserva inédita. A próxima curadoria
precisa recuperar procedência/contexto antes de usar exemplos no piloto.

20 testes focados novos passaram, incluindo preservação literal, revisões
aprovadas, corrupção, fonte concorrente, saída exclusiva e guards da sonda.
Regressão neural/P0: **1.231 passaram em 79,54 s**, sem runtime completo.

`sonda_ambiente_encoder.py` prepara prova técnica com um texto e rótulos
artificiais: duas condições sequenciais, mesma inicialização, float32,
batch 1, comprimento 128, dropout desligado, um passo AdamW. Verifica
gradientes finitos, igualdade inicial e alteração do encoder somente no
braço ajustado. Não mede aprendizado linguístico nem salva pesos ajustados.

### Prova técnica executada — 2026-09-09

Ambiente isolado `.venv_neural314` (sem system-site-packages): Python 3.14.6,
PyTorch 2.11.0+cu128, Transformers 5.16.1, NumPy 2.5.1. `pip check` passou.
O wheel PyTorch foi conferido com SHA-256
`d6c21797ff75271b4fbdd905e2d703be4ecea5ea5bbdde4d1c201e9c71bc411d`.
Checkpoint MiniLM fixado em `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`;
pesos e tokenizer conferidos antes da carga, somente safetensors local,
sem código remoto. `.venv314`, configuração e modelo ativo preservados.

Execução real da sonda na GTX 1660 SUPER, CUDA 12.8: **GREEN técnico**.
Os hashes de encoder, cabeça e logits iniciais foram idênticos nos dois
braços. Gradientes finitos; cabeça mudou nos dois, encoder somente no ajustado.
Pico de memória alocada pelo PyTorch: congelado 514,11 MiB; ajustado 2.591,36
MiB. Não é memória total do processo/driver. Os tempos de passo únicos foram
0,203 s e 0,165 s, respectivamente: não constituem benchmark de velocidade.

Artefatos: `memoria/neural/experimentos/sonda_ambiente_encoder_20260909/`
(`protocolo.json` registra todas as versões, hashes, GPU e parâmetros;
`resultado.json` registra os efeitos e limites). Um texto sintético, rótulos
artificiais, batch 1, len 128, eval com autograd e float32. Não houve treino
linguístico, persistência de pesos ajustados ou teste no runtime da Laylay.
O resultado não valida batch maior, dropout ativo ou estabilidade multietapas.

### Revisão do lote de experiências — 2026-09-09

`revisao_encoder.py` aplica decisões de curadoria explícitas, sem interpretar
frases automaticamente. A entrada fica vinculada ao SHA-256 da fila; exige
cobertura de todos os índices, sem duplicação, e valida anotações com a
supervisão/projeção canônicas. Fontes Python selecionadas são lidas via AST,
nunca importadas/executadas. Não existe fallback que converta item sem
decisão, fora do perfil ou sem contexto em negativo `ausente`.

Entrada de curadoria IA: `memoria/neural/experimentos/revisao_encoder_20260909_entrada.json`.
Saída auditável: `memoria/neural/experimentos/revisao_encoder_20260909/`.
Preserva texto, referências, fila anterior e arquivos de experiências.
Nenhuma revisão humana foi fabricada; nenhum registro foi promovido no ledger.

Resultados da leitura dos 77 textos:

- **3 supervisionados por IA**, todos `APP_OPEN|open|pedido`: abrir Microsoft
  Store, Forza Horizon 6 e Visual Studio Code. Mesma família proposta de
  abertura direta; não devem ser distribuídos como famílias independentes.
- **74 fora do perfil atual**, conservados: 46 consultas de janelas/estado,
  9 referências dependentes de contexto, 6 consultas sobre outros referentes,
  1 metalinguagem, 10 outros domínios e 2 destinos ambíguos (app versus site).
  Isso NÃO significa que essas capacidades sejam inválidas ou indisponíveis.
- **56 textos têm coincidência literal** em três scripts v27 explicitamente
  selecionados (shadow seguro, caos, validação de composição), abrangendo
  619 registros associados. Isso comprova exposição do texto nos arquivos
  atuais, NÃO qual processo produziu cada receipt nem quando o texto nasceu.
- Ausência nos três scripts não certifica novidade. A fila inteira foi
  examinada no desenvolvimento nesta etapa; não é avaliação independente.

Hipóteses concorrentes verificadas: receipt verificado não fornece revisão de
compreensão; `BufferExperienciasNeurais` grava resultados/correções e não tem
ID de sessão/turno original nesse formato. Presença no roteiro não identifica
o evento. Consulta SQLite com `mode=ro`, sem instanciar runtime/migrações,
encontrou 9 mensagens em conversas não excluídas e uma correspondência literal
de usuário; sem vínculo ao ID da experiência, não certifica procedência.
SHA do banco observado: `62da60fb1a626efb8e02caa5edfbfd8a7f442c60e3430a49c9e4a2cb1995c013`.

**Partições não formadas.** Faltam oito das nove combinações variante/ato,
grupos independentes e uso real revisado. Dividir três pedidos similares em
treino/seleção/calibração não resolveria esse impedimento.

Alternativa encontrada nos serviços existentes: `shadow_eventos.jsonl`
contém 2.146 objetos válidos e uma linha inválida, preservada. Há 740 eventos
com texto (317 comparações de turno, 423 de receipt), 178 textos literais
distintos; 46 coincidem com a fila e **132 são adicionais para curadoria**.
SHA observado: `5e52aa5775f832f4d8c75904da1d7f5535773de1d1b1bde2601c4a2864edcb68`.
O shadow persiste texto nas divergências: é outra amostra enviesada, não um
corpus representativo nem gold. Próxima etapa deve aproveitar esse canal
existente sem promover previsão neural ou decisão do legado a rótulo.

Princípio geral: procedência do evento, exposição anterior do texto, anotação
semântica, resultado operacional e autorização de treino são evidências
distintas. A curadoria separa essas responsabilidades para qualquer domínio.
Produção, coleta, executor, porteiro e modelo configurado não foram alterados.

Verificação: 16 testes novos verdes (buffer real, revisão divergente do receipt,
AST sem execução, exposição sem certificação de origem, anotações/flags,
completude, snapshot, saída exclusiva, corrida e falha de fonte). Regressão
neural + P0 autorização/modalidade/isolamento: **1.247 passaram em 71,08 s**.
É GREEN offline; não é GREEN runtime, caos ou benefício linguístico medido.

### Curadoria do shadow concluída — 2026-09-09

`curadoria_shadow_encoder.py` reutiliza o leitor tolerante e exporta somente
os textos adicionais registrados em comparações de turno/receipt. Não exporta
predições nem a decisão canônica como supervisão. Mantém ID de evento,
timestamp, índice do registro válido e hash declarado como referência, sem
tratá-los como ID de turno/sessão. Hashes das fontes são conferidos antes e
depois; corrupção no shadow é contabilizada sem reparo, enquanto corrupção
na fila de sobreposição aborta a exportação.

Fonte shadow permaneceu no SHA `5e52aa5775f832f4d8c75904da1d7f5535773de1d1b1bde2601c4a2864edcb68`.
Dos 2.146 registros válidos, 1.406 não têm texto; 507 correspondem aos 46
textos já presentes na fila anterior; **233 eventos geram 132 textos adicionais**
(120 comparações de turno, 113 de receipt). Uma linha inválida permanece
na fonte. Texto é literal do log, não transcrição bruta: o coletor já compacta
espaços e limita a 500 caracteres. As duas fontes não devem ser fundidas
como se tivessem a mesma fidelidade. A fila conserva essa distinção.

Artefatos locais, sem upload:

- `memoria/neural/experimentos/curadoria_shadow_encoder_20260909/`;
- `memoria/neural/experimentos/revisao_shadow_encoder_20260909_entrada.json`;
- `memoria/neural/experimentos/revisao_shadow_encoder_20260909/`.

Curadoria IA explícita dos 132 textos, validada pelo revisor existente:
**5 supervisionados** (4 APP_OPEN/pedido e 1 FILE_READ/pedido), **127 fora
do perfil** preservados. Não cortar comandos compostos para aproveitar só
a parte compatível; não remover condição, inventar referente ou decidir
app versus site pelo receipt. A grafia registrada permanece nas anotações.
As exclusões são limites deste piloto, não incapacidades da Laylay.

101 textos coincidem literalmente com os três roteiros selecionados
(caos geral, caos v27 e shadow seguro v27), abrangendo 181 eventos. Não é
certificação da origem do evento nem data da primeira exposição.

O cruzamento anterior olhava apenas igualdade com a constante AST inteira.
O caos geral usa uma constante multilinha: a frase estava presente mas o
auditor não a encontrava. Dois REDs reproduziram a omissão, com newline
físico e com escape `\\n`. O candidato mínimo em `revisao_encoder.py` também
busca linhas literais do valor decodificado, sem substring ou normalização;
registra a linha da constante e o índice no valor, sem inventar linha física.
Não executa/importa o roteiro. Artefatos históricos não foram sobrescritos.

Acumulado das duas filas: **209 textos distintos; 8 anotações IA compatíveis**,
sendo 7 APP_OPEN/pedido e 1 FILE_READ/pedido, em dois grupos propostos.
Continuam faltando 7 das 9 combinações variante/ato; zero revisão humana
certificada e zero partição formada. Nenhum fit foi iniciado.

Primeira fronteira insuficiente agora demonstrada: os registros disponíveis
foram desenhados para resultados operacionais e divergências, não para
amostrar compreensão de forma independente do resultado. O código do shadow
só persiste `texto` quando diverge. Recusas/relatos com concordância podem
ficar apenas com hash; não é possível reconstruir a fala a partir dele.
Trocar o otimizador ou aumentar épocas não supre essa lacuna de dados.

Próxima etapa deve ser coleta prospectiva auditável no caminho canônico,
com identidade de sessão/turno, origem (usuário/teste/evento), fidelidade e
contexto necessário, sem depender de execução ou divergência. Inventariar
serviços de coleta existentes antes de alterar produção; testar que texto
de percepção/teste não vira fala autorizadora nem exemplo humano. Previsões,
receipts e rótulos revisados seguem separados. Dados históricos permanecem
desenvolvimento conhecido; futuros splits exigem grupos e revisão reais.

Verificação: 29 testes focados passaram (11 novos de extração e 18 do
revisor, incluindo os 2 REDs corrigidos). Regressão neural/P0:
**1.260 passaram em 79,59 s**. Nenhum runtime completo ou caos executado.

### Sequência restante

Atualização da coleta prospectiva em 2026-09-09: implementação em
`mente_laylay/neural/coleta_entradas.py`, integração em `composicao_turno.py`
e wiring em `laylay.py`. Dois REDs reproduzidos antes de ligar o serviço
pela allowlist; GREEN focal com 15 testes. Original recebido e contexto
mínimo são capturados ANTES do planejamento; ID canônico só é anexado depois.
Falha de planejamento também gera evidência, sem inventar ID/label. Não
depende de modelo, concordância ou execução. Eventos estruturados e origem
presenca ficam fora da fila de falas. Getters/IO falhando preservam o turno.

Reutiliza o writer `BufferExperienciasNeurais` em arquivo separado, sem
alterar buffers históricos. Limite 64 MiB sem descarte automático; entrada
até 16.000 caracteres e até quatro mensagens anteriores com 2.000 caracteres,
sempre sinalizando truncamento/tamanho/hash. Contexto não copia system/tool,
credenciais de configuração ou todo o estado mental. Não se garante que
quatro mensagens bastem para resolver toda referência: vínculo/contexto
continua sujeito a revisão. Conversa ID e marcador `sessao_conversa_ts`
vêm dos donos existentes; ausência não gera identidade fictícia.

`LAYLAY_NEURAL_COLETA_ENTRADAS=1` ativa na próxima inicialização (`0` desativa).
Roteiro declarado ou diagnóstico ativo marca teste; outros canais NÃO
certificam autoria humana. A origem é a recebida na composição e pode já
ter sido transformada no agendador. Sem promover contexto a autoridade.
Arquivo local: `memoria/neural/entradas_prospectivas.jsonl`, pendente de revisão.
Wiring real executado isoladamente com componentes de composição é prova
de integração, não runtime completo. Modelo e autorização permanecem iguais.

Regressão: **1.306 testes passaram em 69,10 s** (neurais/P0, composição,
presença e revisão intra-turno); 16 testes adicionais de composição passaram.
Compilação e diff check verdes. Nenhum processo Laylay estava aberto na
verificação final; arquivo prospectivo de produção ainda ausente. Testes
usaram diretórios temporários e não produziram amostras humanas fictícias.
Nenhum commit criado. SHA do modelo ativo preservado.

1. A triagem IA das duas filas (209 textos) está concluída; ainda não é corpus
   apto. Coleta prospectiva validada em sessão real controlada (abaixo).
   Acompanhar uso cotidiano, obter revisão dos rótulos naturais e
   formar lote com fontes, contextos e linhagens. Preservar as exclusões e
   registrar ambiguidades sem fabricar anotação humana. Não exigir centenas
   de paráfrases do mesmo molde só para alcançar uma quantidade.
2. Ambiente isolado e prova pareada de um passo concluídos. Antes do fit,
   dimensionar o perfil multietapas efetivamente escolhido, preservando os
   hashes e versões registrados; não extrapolar esta medição para batch maior.
3. Fechar split, orçamento, loss/máscaras, otimização, seleção e métricas;
   comparar os dois braços nas três sementes. Não alterar o protocolo em
   função das dobras de avaliação; reportar resultado negativo/inconclusivo.
4. Só avançar a alvos/relações se a melhoria se repetir entre sementes e
   famílias, sem aumento de pedidos inventados e com ganho de recall/cobertura
   sob o mesmo limite de risco. Zero erro observado não garante risco zero.
5. Comparar com o legado na fronteira equivalente e, depois, em composição
   com o mesmo contexto. `comparacao_linguistica.py` é reutilizável, mas sua
   versão atual não mede alvos nem memória/aliases; não chamá-la de runtime.
   Qwen3:4B-instruct pode ser referência de propostas, nunca verdade automática.

Feedback continua pelo buffer/revisão/promoção existentes. Separar erro de
interpretação, alvo, execução e estilo; não fazer atualização online a cada
like/dislike. Nenhuma etapa pode contornar autorização ou receipts.

### Prova runtime real da coleta — 2026-09-09

Sessão oficial: `resultados_testes/roteiro_neural_coleta_prospectiva_seguro-20260909-084143-400566/`.
Base main/HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, worktree preservada
com candidato de coleta já aplicado. Nenhuma Laylay estava aberta antes da
sonda. Executado com `.venv314` pelo `cliente/executor_roteiro_laylay.py`,
encerramento normal código 0. Quatro frases sem solicitação de efeito;
quatro respostas; zero comandos operacionais registrados nos planos.
Overrides apenas do processo: Terminal 2/microfone/presença/briefing/falas
iniciais/modo jogo auto desligados, IoT simulado, coleta ligada. Sem alterar
configuracao.env. Serviços regulares ainda emitiram notificação de email;
não se anuncia ausência de todo efeito incidental da inicialização.

Validador `mente_laylay/neural/validar_coleta_runtime.py` gerou
`validacao_coleta.json`, com hashes das fontes. Conferiu texto literal,
hash/tamanho, quatro identidades canônicas únicas iguais às dos planos,
origem de teste, mesma conversa/sessão, cadeia de turnos anteriores, flags
sem autoridade e ausência de rótulos/partições. Coleta SHA ao fim da sonda:
`b5eed479b3a0e025701c707b645b07b827719a546199b77e50fea182170d25cd`.
29 testes focados verdes (14 do validador, 15 da coleta); não é suíte global.

**GREEN runtime da coleta somente.** O histórico em `messages` tem 0, 0, 2,
4 mensagens nos quatro snapshots. O primeiro turno tratado prioritariamente
não aparece ali no turno seguinte; seu ID aponta para o registro prospectivo
anterior. Não declarar histórico completo, nem inferir alvo só por essa
proximidade. Os quatro registros continuam identificados como testes.

Falha independente no turno 2: ao receber relato sobre ter pedido para abrir
Opera ontem, a resposta inventou que não abriu e sugeriu erro de conexão,
apesar de planos sem comandos e sem evidência apresentada para esse evento.
O avaliador geral marcou 4/4 porque a expectativa era somente `sem_comando`;
isso não prova correção factual das respostas. Registrar separadamente em
erros_encontrados.md; não treinar a partir dessa resposta nem alterar o
coletor para esconder o defeito. Produção não precisou de novo patch nesta
sonda; modelo ativo mantido em shadow, sem fit e sem commit.

## Verificação

Testes: `tests/test_neural_protocolo_ajuste_supervisionado.py`; integração com
validadores/projeção reais, negativos de autoridade/partição e caso positivo
com texto bruto preservado. Fixtures são artificiais e seus metadados de
revisão humana não são exportados como evidência real.

Executar também `tests/test_neural*.py`, P0 autorização/modalidade/isolamento,
compilação e `git diff --check`. Essa validação é offline; nenhum resultado
deve ser descrito como GREEN runtime completo ou rede pronta para promoção.

Resultado desta etapa: **28 focados passaram; 1.211 neurais/P0 passaram em
74,08 s**. Compilação e diff check passaram. SHA-256 do modelo configurado
preservado: `CAAA93027EB96451CBBF1C61136389AC8402533226C666225DA3A2DEF356E0CF`.

### Retomada: fila prospectiva por evento — 2026-09-09

Depois da correção focal da conversa, leitura atual do arquivo prospectivo:
**4 registros, todos `teste_declarado=True` / `origem_declarada=roteiro_teste`**.
Nenhuma nova entrada cotidiana. Não contar sondas como uso humano nem usar
a resposta da Laylay como anotação correta do pedido.

Novo utilitário offline `mente_laylay/neural/curadoria_prospectiva_encoder.py`
reutiliza o leitor JSONL tolerante e os flags de supervisão existentes.
Ao contrário da fila histórica por texto, preserva **um item por evento**,
com registro original, contexto anterior, sessão/turno e referência ao hash
da fonte. Duas ocorrências de “sim” com contextos diferentes não são fundidas.

Separa teste declarado, revisão pendente e quarentena por inconsistência.
Ausência de flag de teste NÃO certifica autoria humana; ausência de anotação
NÃO vira classe negativa. Entrada truncada, identidade ausente/duplicada,
fidelidade inconsistente ou autoridade/rótulo indevido impedem candidatura.
Linhas JSON inválidas são contabilizadas, nunca reparadas na fonte. A
verificação estrutural não certifica completude ou veracidade do contexto.

Exportação atual: `memoria/neural/experimentos/curadoria_prospectiva_encoder_20260909/`.
Contém `fila.jsonl` e `resumo.json`: quatro testes, zero candidatos cotidianos,
zero partições, zero rótulos, treino/promoção proibidos. Leitura vinculada ao
SHA `b5eed479b3a0e025701c707b645b07b827719a546199b77e50fea182170d25cd`;
fonte original e modelo ativo preservados. Saída exclusiva; repetição exige
novo diretório para não apagar a auditoria anterior.

Uso, após novas conversas (escolher um destino novo):

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.curadoria_prospectiva_encoder --destino memoria/neural/experimentos/curadoria_prospectiva_proximo_lote
```

A fila é artefato para revisão, não entrada automática do treinador. Revisar
origem, contexto e linhagens antes de anotação e formação dos splits.
Código de coleta permanece com padrão ligado na inicialização normal;
`LAYLAY_NEURAL_COLETA_ENTRADAS=0` pode desativá-lo. Não abrir uma nova sonda
para preencher artificialmente a falta de uso cotidiano.

Escopo desta entrega: novo utilitário offline, testes e documentação.
Sem alteração de produção/runtime, configuração, pesos, ledger ou executores.
Sem treino, promoção ou commit. Testes novos usam o coletor real e o caminho
de composição existente; não são nova prova de conversa em runtime completo.

Validação: **54 testes focados passaram** (25 da fila, 29 de coleta/validação
runtime persistida). Regressão neural/P0: **1.295 passaram, 19 erros de setup
em 74,08 s**. Não declarar suíte ampla verde. Os 19 erros partem da mesma
guarda em `expandir_relacoes_v4.carregar_base`: o protocolo da supervisão v4
exige hash antigo de `cognicao/normalizacao_linguagem.py`. A correção anterior
do relato explícito adicionou uma função nesse arquivo compartilhado.
Hash exigido `fb48a34a71c6c94faf9fe0e031282e3ea73e956bf9b940c258ba30d5eee7fb69`;
atual `850dbbce1423fdca7162c47978618a73a727081ca7d9fc374d850277ae57bf55`.
Nenhuma outra dependência listada nesse protocolo divergiu na checagem.
Não alterar o hash esperado nem sobrescrever artefatos históricos.

Próxima fronteira técnica: revalidar compatibilidade da supervisão/projeção
v4 com o normalizador atual e documentar eventual nova versão experimental,
antes de reutilizar o perfil na comparação. Essa trava não impede a coleta
cotidiana e não indica, por si, queda de acurácia do modelo ativo. Compilação,
diff check e hashes da fila/fonte/código passaram. Teste novo permanece
local em pasta tests ignorada pelo Git; nenhum staging ou commit.

### Compatibilidade da projeção revalidada — 2026-09-09

Base continua main/HEAD `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, worktree
preservada. Reproduzido o bloqueio em `carregar_base()`. Diagnóstico causal:
retirar apenas o bloco da função `texto_delimita_relato_explicito` dos bytes
atuais **em memória**, sem editar o arquivo, reproduz exatamente o SHA
histórico `fb48a34a71c6c94faf9fe0e031282e3ea73e956bf9b940c258ba30d5eee7fb69`.
Isso falsifica alteração adicional no restante desse arquivo desde a captura.

Reexecutados `alinhar_relacoes` e `rotular_ocorrencias` reais em toda a base
de 672 casos e na expansão de 1.176. **Zero divergência de alinhamento completo
ou projeção**, zero erro. São **1.176 casos únicos**, pois a expansão inclui
a base; não somar os dois lotes como evidências independentes. A expansão
tem 22.320 tokens, incluindo 20.472 `ausente`, e 1.848 ocorrências anotadas.
Segmentos, âncoras, alvos, relações, proveniência e flags foram comparados;
as quatro dobras também são idênticas às persistidas. Não é inferência do
classificador nem prova de generalização fora desse corpus conhecido.

Nova via offline explícita: `revalidar_perfil_v4.carregar_perfil_revalidado()`.
Retorna casos, dobras e relatório; só aceita a mudança de hash revisada do
normalizador e repete a comparação integral em cada chamada. Qualquer outra
dependência declarada alterada, corpus modificado, divergência de alinhamento
ou de dobras aborta. Hashes de 20 arquivos são registrados e reconferidos
antes/depois. O relatório não serve como autorização automática para treino.

Artefato final:
`memoria/neural/experimentos/revalidacao_projecao_v4_20260909/resultado_revisado.json`.
`resultado.json` na mesma pasta preserva a primeira execução diagnóstica;
usar o revisado, cujo código inclui a trava de mudança explicitamente revisada.
Nenhum manifesto, lote, resultado ou hash histórico foi sobrescrito.

**116 testes focados passaram em 10,99 s**, incluindo 18 novos de revalidação,
supervisão, protocolo, curadoria prospectiva e P0 autorização/isolamento.
Negativos cobrem fonte adulterada, alteração concorrente, IDs duplicados,
partição reserva, autoridade indevida, alterações de alinhamento, migração
desconhecida e preservação de relatório anterior. Os testes exercitam a
composição real de normalização/alinhamento, sem substituir esses componentes.
Diff check e conferência dos snapshots passaram.

Limite importante: os leitores históricos não foram alterados. Os 19 erros
de setup da suíte antiga continuam bloqueados pela referência antiga; não
declarar que esta entrega tornou a suíte global verde. A nova API é uma via
experimental explícita para o piloto com o estado atual, não bypass silencioso
dos leitores antigos. Adoção em um comparador futuro deve registrar esse novo
perfil e preservar seus controles pareados.

Escopo: novo módulo offline, testes e documentação. Runtime, normalizador,
executores e modelo ativo intocados nesta etapa; SHA do modelo segue
`CAAA93027EB96451CBBF1C61136389AC8402533226C666225DA3A2DEF356E0CF`.
Sem treino, promoção ou commit. Testes novos permanecem locais sob tests
ignorada pelo Git. Próximo bloqueio para aprendizado linguístico continua
sendo corpus prospectivo cotidiano revisado e separação por linhagens;
a compatibilidade técnica agora está comprovada para os exemplos conhecidos.

## Retomada após investigação conversacional — 13/09/2026

Prioridade explícita do Pedro: voltar à rede; os REDs restantes de recomendação foram documentados e não impedem a preparação offline do corpus. Não confundir isso com aprovação da conversa ou autorização de promoção do modelo.

Reexecutado o preparador canônico `curadoria_prospectiva_encoder` sobre a coleta atual, sem alterar classificadores, rótulos, normalização ou corpus históricos. Exportação nova e imutável em `memoria/neural/experimentos/retomada_encoder_20260913/` (`fila.jsonl` e `resumo.json`). A fila de 09/09 foi preservada.

- 265 eventos JSON válidos, zero linhas inválidas/quarentena; 106 textos distintos.
- 257 eventos declarados como teste, separados dos 8 eventos pendentes de revisão.
- Os 8 pendentes têm origem declarada `desktop`, 7 textos distintos e pertencem à conversa de Arduino já investigada. Isso não certifica autoria humana nem os torna exemplos inéditos.
- Cruzamento pelo leitor canônico `revisao_encoder.cruzar_exposicao`, sem executar os roteiros: 5 dos 8 eventos possuem texto presente nos quatro roteiros explícitos comparados (`roteiro_recomendacao_contextual.py`, `roteiro_reparo_parcial_conversa.py`, `roteiro_site_por_assunto.py`, `roteiro_transformacao_conversacional.py`). Ausência de match nos outros três não certifica ausência de exposição.
- Fonte SHA256: `e6a926f35c943fa82bb20e59408c201bac3aecae09c2712a76e9015a2a6b42ce`; fila SHA256: `af6bba5c22c19e95c6b828a11d6c015928f61396793a5b761523669ed8f44ab2`.
- `dados_prontos=False`, sem partições, sem revisão humana certificada, `treino_permitido=False`, `autoriza_execucao=False`, `autoriza_promocao=False`. Nenhum fit ou mudança de pesos.

Próximo passo da rede: curadoria explícita desses eventos/contextos, com origem de rótulo `curadoria_ia` e exposição conhecida; separar discussão, pergunta e pedido operacional, sem extrair rótulos das respostas da Laylay. Revisar o enquadramento no perfil v4 e registrar motivos de fora do perfil. Não colocar esses exemplos conhecidos em seleção/calibração inéditas nem fabricar revisão humana. Depois, completar cobertura/linhagens e avaliar prontidão do piloto pareado. Ainda não existe evidência nova de superioridade da rede.

Verificação: coleta, protocolo, fila prospectiva e regressões focadas de conversa tiveram 88 testes aprovados e 13 xfails explícitos de recomendação. A seleção ampliada terminou em 806 aprovados, os mesmos 13 xfails e a falha preexistente de orçamento de tokens. Sem suíte global GREEN, sem staging ou commit.

## Curadoria dos oito eventos pendentes — 13/09/2026

Concluída a revisão IA do recorte, sem executar ações, iniciar a Laylay ou treinar modelos. Base Git permanece `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`/main, com a worktree anterior preservada.

O perfil declarado em `preparar_lote_relacional_v3.VARIANTES` cobre apenas `APP_OPEN/open`, `MUSIC_SEARCH/search` e `FILE_READ/read`, cada uma com pedido/recusa/relato. Isso é o escopo do **piloto**, não uma afirmação de que a rede ativa ou a Laylay só possuem essas habilidades.

| Índice na fila original | Leitura da entrada | Destinação no piloto |
| --- | --- | --- |
| 208 | Saudação e pergunta sobre a assistente | Fora do perfil; não fabricar negativo `ausente` |
| 209 | Estado pessoal + pergunta sobre painel solar | Fora do perfil; relato pessoal não é relato de comando |
| 210–211 | Perguntas informativas sobre painel e DC-DC | Fora do perfil; nenhum comando das três variantes |
| 212 | Pedido de abrir site por assunto | Fora do perfil; navegação não é abertura de aplicativo |
| 213–214 | Recomendação contextual repetida | Dois eventos preservados; fora do perfil |
| 215 | Requisitos para recomendação | Fora do perfil; não autoriza efeitos nem comprova especificações |

Resultado: **8 fora do perfil, 0 anotações operacionais treináveis**. As justificativas são julgamentos de curadoria IA, não revisão humana. Contextos foram lidos como indícios, não como fonte de rótulos ou prova de vinculação à sessão; o indicador de vínculo permanece falso. As respostas técnicas da Laylay não foram adotadas como gold. Os dois pedidos iguais mantêm IDs/contextos próprios. Um grupo conservador comum foi proposto para a conversa; não criar partições independentes a partir desses eventos relacionados.

Artefatos em `memoria/neural/experimentos/revisao_prospectiva_20260913/`:

- `fila_pendente.jsonl`: recorte das linhas 208–215, intactas; os outros 257 eventos continuam na fila original, não foram apagados.
- `revisao.json`: decisões explícitas por índice, hash do recorte, hash/índices da fila pai e sete justificativas para os oito eventos.
- `resultado/fila_revisada.jsonl` e `resultado/resumo.json`: produzidos pelo aplicador canônico `revisao_encoder.executar`, com validação de snapshot e fontes, sem sobrescrever artefatos anteriores.

Hashes: recorte `6d330d19b7bd7cbb822050c3252a6c2ac20701fa7b0ef447ff0a47d4be5dae8e`; revisão aplicada `b868b488e454348a33dd266285818f0f5fedb7224280f69d05d386860b07f4d1`. A fila pai manteve o hash `af6bba5c22c19e95c6b828a11d6c015928f61396793a5b761523669ed8f44ab2`.

Verificações: **87 testes passaram** (coleta, revisão, fila prospectiva e protocolo). Nova integração protege eventos repetidos com contextos distintos e navegação fora do perfil, sem fusão, rótulo automático ou certificação humana. Conferência direta dos artefatos confirmou oito linhas idênticas às originais e preservação integral dos eventos/contextos após revisão. `git diff --check` sem erros. Nenhum arquivo de produção, peso, configuração ativa ou partição foi alterado; nenhum commit.

Próximo passo: preparar cobertura revisada das variantes-alvo do piloto (abrir aplicativo, buscar música e ler arquivo, incluindo pedido, recusa e relato), com linhagens explícitas. Este lote conhecido não deve virar seleção/calibração inéditas. Se quisermos incluir navegação ou conversa contextual no fit, isso exige extensão explícita do perfil e avaliação própria, não rebatizar esses oito exemplos. Ainda faltam dados elegíveis/revisão humana declarada e partições suficientes para anunciar prontidão de treino; não há ganho de desempenho medido nesta etapa.

## Lote de contrastes explícitos — 13/09/2026

Continuação autorizada da preparação da rede, sem retomar as correções de
conversa. Base `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`/main e worktree
anterior preservadas. As duas revisões históricas de 09/09 contêm oito
registros supervisionados: sete de abertura e um de leitura, todos pedidos.
Isso não significa oito famílias independentes nem origem humana certificada;
esses registros não foram rebatizados/importados como uso real revisado.

Preparador offline `mente_laylay/neural/preparar_contrastes_piloto.py`:

- 27 exemplos sintéticos, três por combinação das três variantes com
  pedido/recusa/relato. Contrastes diretos, de cortesia e com negação dentro
  de nomes literais, incluindo nomes fictícios. Não comprova existência de alvos.
- Seis casos fora do perfil: site, pergunta de capacidade, recusa genérica,
  referência contextual, citação metalinguística e condição futura. Sem gold
  operacional; não entram como negativos `ausente` artificialmente fáceis.
- Marcações explícitas transportadas pelo `preencher` existente, verificadas
  por `validar_caso`/validador v4 e projeção bruta canônica. Nenhuma previsão,
  resposta da Laylay ou receipt foi usado para escolher rótulos.
- Todos conhecidos, sintéticos, `curadoria_ia`, somente desenvolvimento.
  Os nove trios compartilham uma linhagem conservadora; não são nove dobras
  independentes e não podem ser repartidos aleatoriamente entre treino/teste.

Auditoria lexical somente leitura contra os 1.176 casos conhecidos de
`expansao_relacoes_v4_20260908/lote.json` (SHA256
`f389af34b78ecf540ce551867d27e21191d6855e8113410535a106392fb55a07`):
zero duplicatas exatas normalizadas, oito pares próximos com limiar 0,9.
Todos envolvem a nova recusa de ler `não apagar.txt` e a família histórica
`vontade`. Registrado `gerador_v4:vontade` como ancestral conservador desse
caso, reutilizando a identidade do importador canônico. Por transitividade,
o lote inteiro não poderá ser separado dessa família como avaliação inédita.
Ausência de outros matches lexicais não certifica novidade semântica.
Essa comparação lê textos do snapshot, não revalida o alinhamento histórico,
não contorna as travas do leitor de perfil para treino e não lê reserva.

Artefatos exclusivos em `memoria/neural/experimentos/contrastes_piloto_20260913/`:
`corpus.jsonl` e `resumo.json`. Corpus SHA256
`2611367875561de800061f9865330be69417a0dc6ff99653e9e05f9f693136f8`.
Reexecução no mesmo destino aborta; o gerador não sobrescreve lote anterior.
O registro da comparação histórica é uma revisão datada, não uma nova
auditoria automática a cada exportação.

**98 testes focados passaram**: contrastes, protocolo, revisão, fila prospectiva
e coleta. Incluem integração com os validadores/projetores reais, bloqueio de
fit, parentesco transitivo com a importação histórica, alvo adulterado, flags
indevidas e exportação reproduzível/exclusiva. Não são testes de acurácia da
rede, nem prova do runtime em execução. Não foi rodada a suíte global.

Contrato fortalecido: supervisão linguística não concede autoridade; material
conhecido e seus parentes não se tornam avaliação independente por renomeação.
Nenhum runtime, modelo ativo, peso, normalizador ou configuração foi alterado
nesta etapa. Sem execução dos comandos, fit, promoção ou commit.

Próxima fronteira: usar o lote como diagnóstico de desenvolvimento na comparação
existente, relatando erros por variante/ato sem ajustar gold às previsões. Antes
do fit pareado, continuam pendentes os dados cotidianos revisados e as partições
independentes de treino/seleção/calibração previstas no protocolo. Cobertura
sintética de desenvolvimento completa não satisfaz essas condições; não há
ganho de desempenho medido nem liberação nova da rede nesta etapa.

## Diagnóstico dos modelos salvos nos contrastes — 14/09/2026

Concluída inferência offline dos 33 textos pelo carregador real de modelos,
`ModeloNeuralComandos.prever`, normalizador neural canônico e predicado de
priorização do especialista. Novo consumidor:
`mente_laylay/neural/diagnosticar_contrastes_piloto.py`. O consumidor recebe
apenas texto na inferência e consulta gold posteriormente para medir. Não
instancia a Laylay, buffer de experiências, treinador ou executor.

Inventário corrigiu uma premissa do próximo passo: o comparador de ocorrências
v4 salva métricas das dobras, mas não persiste cabeças treinadas para esta
inferência. O novo encoder ajustado ainda não possui pesos linguísticos
treinados. Portanto, foram medidos os artefatos existentes, identificados:

- Base `modelo_ativo.joblib`, versão `tfidf-v0.4`, SHA256
  `07c539917eae7792b2b4ecb1f0335697802fc7f6672e920656f8c5dfc2289e62`.
- Candidato configurado em `configuracao.env`, modo `shadow`, versão
  `hibrido_v26_ext_list_windows_estado_estrutura_v4_v27`, SHA256
  `caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf`.
  O launcher usa ambiente externo antes do arquivo; nenhuma sobrescrita
  neural foi encontrada no ambiente deste processo. Isso confirma a seleção
  em disco para uma nova sessão com esse ambiente, não inspeciona uma sessão
  da Laylay já aberta.

| Medida nos casos supervisionados | Base | Candidato em sombra |
| --- | ---: | ---: |
| Pedidos de aplicativo propostos com variante correta | 1/3 | 2/3 |
| Pedidos de música propostos com variante correta | 0/3 | 0/3 |
| Pedidos de leitura propostos com variante correta | 2/3 | 2/3 |
| Total de pedidos propostos com variante correta | 3/9 | 4/9 |
| Propostas indevidas nos nove relatos | 1/9 | 0/9 |
| Propostas indevidas nas nove recusas | 0/9 | 0/9 |

Essas frações não são acurácia global nem superioridade sobre o interpretador
Python completo. Os modelos por texto não devolvem os atos por ocorrência do
piloto. Prever `NONE` para relato pode respeitar seu objetivo histórico de
detector operacional; não implica que o modelo reconheceu semanticamente o
relato. Intenção/ação de recusas e relatos ficam como diagnóstico descritivo,
não como exigência retrospectiva de nove classes para esses modelos.
Os seis casos fora do perfil foram observados sem score ou rótulo fabricado.

Primeiras divergências observadas no candidato:

1. `Abra o aplicativo "Não Feche".` e `Leia o arquivo "não apagar.txt".`:
   intent e ação corretos, comando acima do limiar, `negated=True`; o predicado
   remove a proposta. A negação da frase inteira não representa o escopo do
   nome literal. Falsificada insuficiência de confiança nesses dois casos:
   probabilidades de comando 0,921 e 0,957, limiar 0,65, nenhum veto de comando.
   Falsificado erro de intenção/ação nesses dois casos: ambas estão corretas.
2. `Busque a música Aquarela.`: primeira saída intent já é `NONE`, ação `none`.
   O problema antecede o consumidor de autorização. Reduzir um limiar não
   fornece a variante musical ausente.
3. `Por favor, procure a faixa Trem-Bala para mim.`: intent `FILE_SEARCH`,
   ação `search`, comando 0,963 e proposta presente. É pedido reconhecido no
   domínio errado; não é recusa nem falha do executor.
4. `Busque a música "Não Volte".`: intent/ação musicais corretos, mas há
   `negated=True` e veto por probabilidade 0,661 abaixo do limiar 0,755.
   Corrigir somente uma dessas saídas não prova correção do pedido.

No controle base, `Na semana passada, tentei ler o arquivo "diário da
oficina.txt".` produziu proposta de leitura, ilustrando passado confundido
com pedido. O candidato não propôs operação nesse relato. Porém, fora do
perfil, `Você consegue abrir aplicativos?` produziu proposta APP_OPEN no
candidato: registrar como alerta qualitativo de pergunta de capacidade,
sem incluí-la na taxa das nove combinações nem alegar execução indevida.

O enriquecedor lexical em `modelo.py` acrescenta pista de negação mesmo
quando o termo aparece no nome. Isso é compatível com a hipótese de escopo,
mas não demonstra sozinho qual atributo causou a decisão aprendida. Não foi
feita ablação de atributos nem alterada proteção de produção. A raiz no nível
da interface está reproduzida: uma negação global não consegue localizar
qual ocorrência/alvo foi negado. O piloto de ato por ocorrência busca medir
essa distinção; ainda precisa provar que a aprende.

Artefato exclusivo:
`memoria/neural/experimentos/diagnostico_contrastes_20260914/resultado.json`,
SHA256 `37dfaa8f4dd79a206f1d29be4dcb11c24b781890e284ff01961a5ed8396f1fd8`.
Inclui previsões brutas/normalizadas por texto, fatias, versões e hashes dos
modelos, corpus, módulos neurais e encoder/tokenizer usados. Fontes
reconferidas após a inferência; alterações concorrentes abortam a publicação.

**50 testes passaram**: consumidor do diagnóstico, contrastes e protocolo.
Testes do consumidor cobrem denominadores, gates canônicos, exclusão de
fora-perfil das métricas, ausência de gold na entrada, erro de carga que não
vira abstenção correta, fonte concorrente e preservação de destino existente.
Os testes usam previsões artificiais para verificar a métrica; os números da
tabela vêm dos modelos locais reais. Nenhum teste de runtime completo ou
suíte global foi executado nesta etapa. Arquivos de teste são locais/ignorados.

Decisão: manter a influência operacional atual. Não retunar limiares neste
lote conhecido. Próximo trabalho é preparar a avaliação da distinção entre
pedido, negação com escopo e relato no piloto, usando estas falhas como
desenvolvimento e garantindo exemplos revisados independentes para seleção e
calibração. A pergunta de capacidade deve continuar observada fora do perfil
até uma extensão explícita, para que uma média favorável não esconda esse
limite. Permanecem os requisitos de dados antes do fit pareado. Runtime,
pesos, corpus gold e configuração não foram alterados; sem commit ou promoção.

## Preparação da entrada de aprendizado — 14/09/2026

Autorizada a continuação do ensinamento após o diagnóstico. Implementada a
ponte entre supervisão bruta e tokenizer do MiniLM treinável, em
`mente_laylay/neural/preparar_entrada_encoder.py`. Base Git permanece
`76aa525ef61fdb4ecfbfdb578adf572c0b83949a`/main; worktree anterior preservada.

Contrato: a entrada e o mapa de agregação dependem apenas do texto. A
supervisão fica separada, com IDs no catálogo canônico; trocar um rótulo não
pode mudar a entrada. O token literal continua sendo a unidade de aprendizado:
os pedaços do tokenizer contribuem por interseção de caracteres, seguidos de
normalização L2, como no comparador existente. Um pedaço compartilhado com
pontuação pode contribuir para dois tokens, sem receber dois rótulos
conflitantes diretamente. Nenhum parser de domínio decide o gold.

Validação numérica do mapa contra `comparar_ocorrencias_v4.alinhar_subtokens`,
com estados artificiais de 384 dimensões. Essa equivalência não executa o
encoder nem prova fluxo de gradiente; a implementação diferenciável da
agregação/perda continua uma etapa futura do treinador. O tokenizer real
fixado foi carregado localmente, com hash conferido, truncamento e padding
desligados. Entradas acima de 128 subtokens, cobertura incompleta, token
desconhecido ou tokenizer adulterado abortam; não corrigir dados cortando
nomes ou âncoras silenciosamente.

Resultado real do corpus de contrastes: **27 exemplos, 296 tokens literais,
máximo de 23 subtokens por entrada; seis fora do perfil mantidos à parte**.
Os nomes com negação e acentuação foram preservados. Exportação exclusiva:
`memoria/neural/experimentos/entrada_encoder_contrastes_20260914/preparacao.json`.
Artefato contém entrada, supervisão separada, mapa, auditoria e hashes das
fontes; permanece `uso=diagnostico`, `treino_permitido=False`,
`forward_encoder_executado=False`, `aprendizado_medido=False`.

**45 testes passaram**, cobrindo a nova ponte, protocolo e corpus. Integrações
usaram tokenizer real e agregador existente. Negativos verificaram mudança de
gold sem mudança da entrada, mapa adulterado, truncamento, limite de tamanho,
hash errado, destino existente e tentativa de preparar treino com corpus
insuficiente. Nenhuma suíte global ou execução completa da Laylay nesta etapa.

O ambiente isolado `.venv_neural314` contém torch/transformers/tokenizers, mas
não sklearn/pytest. Por isso a preparação canônica usa `.venv314` e entrega
JSON; o futuro consumidor torch poderá receber essa fronteira explícita,
sem misturar site-packages entre ambientes nem duplicar a curadoria.

Próxima etapa técnica: consumidor diferenciável desse mapa e perda por token,
com controle de gradientes/congelamento e carregamento apenas de partições
aprovadas. Antes do fit linguístico continuam obrigatórios os dados reais
revisados e a separação por linhagens prevista no protocolo. A preparação
de treino reutiliza `preparar_particao` e foi testada para recusar o corpus
atual; não se criou um atalho a partir do lote conhecido. A coleta existente
é o caminho para obter exemplos cotidianos, que exigem revisão de procedência
e rótulos antes de particionar. O conjunto de desenvolvimento não pode virar
uma avaliação independente por renomeação.

Pesos, configuração, gold e runtime permaneceram intactos, hashes dos dois
modelos e do corpus conferidos. Nenhum treinamento ou commit nesta etapa.

## Cálculo de perda e gradientes reais — 14/09/2026

Implementados `perda_encoder.py` (agregação diferenciável, inferência por
tokens literais e cross-entropy) e `sonda_perda_encoder.py` (prova técnica
no ambiente torch isolado). HEAD continua
`76aa525ef61fdb4ecfbfdb578adf572c0b83949a`/main, worktree preservada.

A agregação usa a média ponderada pelo mapa preparado e normalização L2
sem destacar tensores do grafo. Um subtoken compartilhado recebe a soma das
contribuições dos tokens literais correspondentes. Gold entra exclusivamente
na perda, depois dos logits. A CE usa média por token literal, incluindo a
classe ausente; nenhum peso de classe, limiar ou hiperparâmetro foi ajustado
pelos resultados deste lote. A prevalência de ausente deve ser considerada
na definição futura do treino; queda de perda isolada não será critério de
qualidade de comandos.

Módulo de perda não carrega corpus nem possui otimizador ou persistência.
É componente matemático, não consumidor autorizado de treino. O futuro
treinador deverá consumir partições aprovadas pelo protocolo canônico.
A sonda exige a exportação de diagnóstico com hash explícito, confere fontes
e checkpoint antes/depois, executa forward/backward e não chama optimizer.step.
Uma saída só é publicada quando todas as verificações passam; destino
existente é preservado.

**Prova com MiniLM local real, CUDA/GTX 1660 SUPER, torch 2.11.0+cu128:**

- 27 exemplos por condição, 54 forward/backward no total, batch físico 1,
  float32, dropout desligado e semente 27 para a cabeça de dez classes.
- Cabeça com gradientes finitos e não nulos nas duas condições; encoder
  com gradientes finitos e não nulos somente quando liberado.
- Hashes iniciais do encoder/cabeça iguais entre condições e perdas por
  exemplo exatamente iguais. Encoder/cabeça conservaram seus hashes após
  todos os backward. Nenhum passo de otimizador e nenhum peso salvo.
- Pico alocado pelo PyTorch: 514,23 MiB congelado e 1.786,64 MiB liberado.
  Não representa consumo total do driver/processo nem memória com AdamW.
- Perdas iniciais entre 2,237394 e 2,305708. São erros de uma cabeça aleatória;
  não houve curva de aprendizado nem medição de melhora linguística.

Artefato:
`memoria/neural/experimentos/sonda_perda_encoder_20260914/resultado.json`,
SHA256 `0daa54e1d3e3cf0fdda3f4ca9b45f38abbf4c5736acf0e893f435298e92bc959`.
Preparação consumida manteve SHA256
`f808bbd75d12db40f03b03e242daa701eec91a1a1bf6f8c9d3ad311aa8fb38d6`.
Relatório registra fontes/checkpoint, perdas por caso, hashes de estados,
gradientes, ambiente e memória. Mantém `aprendizado_medido=False` e todas
as flags de treino/execução/promoção falsas.

Verificação automatizada: **7 testes unittest passaram no ambiente isolado**,
incluindo derivada numérica por gradcheck, equivalência com média NumPy,
contribuição de subtokens compartilhados, sinal da derivada da CE, preservação
de pesos, congelamento, mapa inválido, NaN e rótulos incompatíveis. Outros
**6 testes da preparação passaram no ambiente principal**, com o módulo torch
explicitamente pulado ali por ausência da dependência (1 skip). Nenhuma
mistura de bibliotecas entre ambientes. A prova com checkpoint real é
adicional a esses testes locais; não constitui execução completa da Laylay.

Próximo trabalho: formar as partições revisadas previstas no protocolo e
fixar orçamento/critérios para conectar esse cálculo ao otimizador do piloto
pareado. Até lá, desenvolvimento conhecido pode diagnosticar representação
e gradientes, mas não fundamenta generalização. Continua faltando evidência
para liberar a rede; não há ganho novo de acurácia nesta etapa.

Produção operacional, pesos ativos, candidato em sombra e configurações
intocados; hashes dos dois artefatos conferidos. Código novo restrito ao
experimento offline, testes e documentação; nenhum commit.

## Critérios fechados e disponibilidade de dados — 14/09/2026

Desenho prévio ao fit registrado em
`mente_laylay/neural/protocolo_treino_piloto_v1.json`. É especificação
declarativa versionada; ainda não existe treinador que consuma/garanta todas
essas condições. Não apresentar esse arquivo como implementação do treino.
Valores são decisões experimentais locais fixadas antes do fit, não resultado
de busca de hiperparâmetros ou promessa de configuração ótima.

Comparação: sementes 27/53/89, mesmo MiniLM não quantizado, mesma cabeça
Linear(384,10), mesma inicialização por par e mesma ordem de dados. Encoder
congelado versus liberado, dropout desligado, float32. AdamW, LR da cabeça
0,001 e do encoder 0,00002, weight decay 0,01, clipping de norma 1. Sem
scheduler ou pesos de classe nesta primeira versão. A taxa maior da cabeça
aleatória é uma escolha prévia; se ficar inadequada, registrar falha e nova
versão em vez de retunar usando os resultados de calibração.

Orçamento fixado: oito épocas completas, batch físico 1, até 128 subtokens,
máximo 4.000 passos por condição/semente (24.000 no conjunto de seis corridas).
Se 8 vezes o tamanho do treino exceder o teto, abortar antes do fit e rever o
orçamento/dados em uma nova versão. Isso não autoriza truncar épocas ou
selecionar silenciosamente exemplos. OOM/NaN invalidam a corrida; a prova
multietapas com o otimizador ainda precisa existir antes de anunciar viabilidade
nesse orçamento. A sonda de backward não mediu memória dos estados AdamW.

A seleção de época usará somente seleção: primeiro menos pedidos inventados,
depois maior macro-F1 das nove classes de ocorrência (sem ausente), maior
exatidão por caso e, no empate, época anterior. Calibração será lida uma vez
depois dessa escolha, sem ajuste de threshold nesta versão. Todas as épocas
e falhas terão relatório. Os 27 contrastes conhecidos não escolhem época,
taxa de aprendizado ou limiar. Uma avaliação futura de limiares exige outro
protocolo e novos dados para não reutilizar calibração como seleção.

Critério de avanço experimental: em cada semente ajustada, pelo menos 95%
de casos exatos sem alvos, zero pedidos inventados e zero ações extras em
calibração. Mediana do ganho pareado de macro-F1 de pelo menos 0,02; nenhuma
semente pode perder mais de 0,01 em macro-F1 ou exatidão. São critérios locais
para avançar à avaliação de alvos/relações/composição. Zero erros em uma
amostra pequena não certifica segurança; esses gates não liberam o runtime.

**Disponibilidade atual conferida:** a coleta prospectiva continua byte a
byte igual à captura de 13/09: SHA256
`e6a926f35c943fa82bb20e59408c201bac3aecae09c2712a76e9015a2a6b42ce`.
Continuam 265 eventos, dos quais 257 são testes declarados e oito já revisados
fora do perfil. Nenhuma nova exportação duplicada foi criada. A fila e suas
revisões anteriores foram preservadas. Os históricos de experiências já
examinados não oferecem conjuntos inéditos certificados. Os 27 contrastes
sintéticos têm origem IA conhecida e não podem ser marcados como revisão
humana ou movidos para avaliação independente por conveniência.

Consequência: **não foi possível formar as partições revisadas com os dados
disponíveis**. Para obter material elegível, é necessário uso cotidiano da
Laylay nas três famílias do piloto, com formulações próprias e contextos
registrados. Pedidos, recusas e relatos reais devem ser revisados como atos
distintos; a ausência de execução não fornece um rótulo por si só. Rodar mais
um roteiro escrito pela IA não cumpre essa necessidade de origem. Mesmo
novos dados não são automaticamente aprovados: conferir origem, exposição,
parentesco e cobertura antes de decidir partições e fixar seus hashes.

O próximo passo dependente é essa coleta/revisão de novos exemplos. O
consumidor de treino também permanece pendente, mas implementá-lo não deve
ser apresentado como solução para a falta de dados. Não houve fit, mudança
de pesos, novas partições fictícias ou alteração das guardas canônicas.
Escopo desta etapa: especificação de critérios e atualização do plano;
validação sintática/consistência do JSON, sem alegação de nova suíte verde.

## Novas frases do usuário recebidas — 14/09/2026

A coleta agora tem 546 eventos: 281 novos, sendo 267 do caos e 14 desktop.
As 14 frases pessoais estão presentes, apesar da flag conservadora de sessão
de teste. Curadoria canônica concluída: seis supervisionadas dentro do piloto
e oito fora do perfil, mantendo todas as entradas/contextos. O usuário confirmou
o ato de pedido em `abri a calculadora do windowns`; grafia preservada e
confirmação registrada sem certificar os outros rótulos como revisão humana.

O debug forneceu evidência real de pedidos modais classificados como conversa
e falas que confirmam pausa sem comando registrado. Replay do classificador
canônico reproduziu a primeira divergência. Não é evidência de que o modelo
em sombra tenha causado o bloqueio. Não houve patch de produção ou fit.

Dados, hashes, revisão final, limites do caos e próxima fronteira estão em
[RELATORIO_COLETA_DEBUG_20260914.md](RELATORIO_COLETA_DEBUG_20260914.md).
Diretório final da revisão:
`memoria/neural/experimentos/revisao_manual_pos_caos_20260914/resultado_confirmado/`.
A conclusão anterior de ausência de novas entradas foi superada por esta
coleta. O corpus ainda não satisfaz cobertura/independência para o fit pareado,
mas as frases pessoais foram aproveitadas e não precisam ser reenviadas.

## Referências técnicas

- [Token classification e fine-tuning](https://huggingface.co/docs/transformers/tasks/token_classification)
- [MiniLM: finalidade e arquitetura](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
- [CheckList: avaliação comportamental](https://aclanthology.org/2020.acl-main.442/)
- [NegBERT: pistas e escopo](https://aclanthology.org/2020.lrec-1.704/)
- [PyTorch: instalação e verificação](https://pytorch.org/get-started/locally/)

São referências para o desenho, não evidência de desempenho na Laylay.
