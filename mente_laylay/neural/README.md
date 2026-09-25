# Especialista neural de comandos

## Estado atual: v29 — ato semântico selecionado; domínio é a próxima fronteira — 2026-09-21

Base congelada antes da investigação: `main`, HEAD
`bf9353e2a77bc0ca756932ed56ce97cf4988e1ab`, worktree limpa. O objetivo foi
a fronteira de ato da extensão `LIST_WINDOWS`; música/player e seus receipts
ficaram fora deste escopo. Nenhum runtime, gate de autoridade ou modelo ativo
foi promovido.

A hipótese de perda literal foi testada primeiro. `integral_v1` foi conectada
somente ao avaliador de extensões e comparada na mesma âncora v28. Em
`validation_group`, no limiar fixo 0,5, a extensão final ficou em 72,26% de
precisão, 79,53% de recall e 91 falsos positivos, contra 75,64% / 79,19% / 76
do controle `estrutura_pontuacao`. Os 64 falsos positivos das quatro famílias
críticas permaneceram. Portanto, preservar mais texto isoladamente não explica
a raiz de generalização.

O modelo-base já carrega `EncoderSemanticoHibrido`. Um head experimental
sobre esse encoder, sem fine-tuning, foi então avaliado com os mesmos folds.
Com `ato_consulta=semantico_hibrido_base` e `dominio_app=tfidf`, a prova
oficial DEV ficou em 81,01% de precisão / 91,61% de recall / 64 FP no eixo de
famílias e 92,62% / 84,23% / 20 FP no eixo de entidades. O fator de ato sozinho
passou de 64 FP / 44 FN para 50 FP / 5 FN no eixo de famílias.

Nas cinco famílias críticas, `consulta_permanece` passou de 16 FN para zero;
hipótese de abrir e permanência afirmada passaram de 16 FP para zero; hipótese
de estado caiu de 16 FP para 2. Metalinguagem permaneceu com 16 FP e é a
principal lacuna de ato ainda aberta.

Somente depois dessa seleção em DEV, a reserva sintética
`datasets/reservas/list_windows_ato_v1.json` foi aberta uma vez. O fator de
ato obteve 11 TP, 1 FN, 1 FP e 11 TN (91,67% de precisão/recall). A conjunção
final ficou em 70% de precisão, 87,5% de recall e 83,33% de acurácia porque
`dominio_app=tfidf` marcou seis dos oito exemplos não-app como domínio de
aplicativo. A reserva está agora consumida: qualquer ajuste posterior exige
outra prova de confirmação e não pode reutilizá-la como inédita.

Artefatos: `memoria/neural/experimentos/v29_ato_integral_avaliacao/` e
`memoria/neural/experimentos/v29_ato_semantico_avaliacao/`. O relatório da
reserva declara `treino_com_reserva=false` e `nao_promove_modelo=true`.
A regressão focal fechou com 279 testes aprovados; `py_compile` e
`git diff --check` também passaram. Próxima fronteira isolada: generalização
de `dominio_app`; não empilhar essa mudança sobre a rodada de ato. O modelo
configurado continua em shadow.

## Retomada: cobertura do piloto auditada — 2026-09-21

Frente distinta e complementar à extensão LIST_WINDOWS v29 acima. Coleta atual
exportada pelo componente existente para
`memoria/neural/experimentos/retomada_prospectiva_20260921/`: 1.096 eventos,
1.044 declarados de teste e 52 pendentes, sem corrupção ou quarentena.
Os pendentes são 46 textos distintos em 12 sessões; não certificar autoria
humana, independência ou rótulos automaticamente.

A triagem por IA mostra uma barreira de cobertura: o piloto de três variantes
(abrir aplicativo, buscar música, ler arquivo) não representa essas 52 entradas,
predominantemente IoT, mídia, sistema e conversa. Isso não mede acurácia. A
curadoria supervisionada anterior permanece preservada. Não descartar os
casos fora do perfil nem convertê-los em negativos para forçar um treino.

Detalhes e hashes no [relatório de cobertura](../../melhorias%20e%20planos/relatorio/RETOMADA_NEURAL_COBERTURA_20260921.md).

### Perfil diagnóstico ampliado e reconciliação local

`supervisao_operacional_v1.py` valida nove variantes (as três históricas,
IoT on/off, mídia pause/play/next e volume absoluto set), com pedido/recusa/relato.
Reutiliza spans e validação v4; o percentual de volume possui dono, unidade e
evidência literal separados do alvo/ação. Texto bruto é a única entrada; a
supervisão nunca vira autoridade. Escopo literal/imediato é declaração revisável,
não detecção semântica automática. Referências contextuais e agendamentos não
estão representados. Ainda não há integração deste perfil com treino/partições.

Na cópia das frentes, o consumidor novo permaneceu, mas a assinatura ampliada
de `rotular_ocorrencias` foi perdida: 36 testes falharam com `TypeError`.
Restituído somente o argumento opcional `rotulos_permitidos`; chamadas históricas
continuam restritas aos dez rótulos antigos, sem mutação global do catálogo.
O arquivo `modelo.py` entregue pelo SOL não foi editado nesta reconciliação.

Os testes novos mencionados no handoff v29 não vieram na cópia local. Foram
escritos seis casos locais em `test_neural_validacao_extensao.py`: OOF/conjunção,
isolamento por grupos, ausência de encoder sem fallback, identidade do encoder,
serialização/recarga e preservação da base. Encoder sintético nesses testes
verifica integração, não qualidade semântica nem reproduz a avaliação v29.
Junto do perfil operacional: **75 testes aprovados**, 2,24 s.

Não atualizar hashes históricos para liberar testes: o protocolo de
`supervisao_relacoes_v4_20260908` exige hashes antigos de `modalidade_turno.py`
e `normalizacao_linguagem.py`. HEAD local e worktree possuem os mesmos hashes
atuais, ambos distintos do protocolo. É bloqueio histórico separado da junção;
nenhuma reserva, baseline ou configuração de produção foi reescrita.

Regressão neural ampla desta reconciliação: **1.384 aprovados, 1 skipped,
6 falhas e 21 erros**, 75,18 s. Quatro falhas eram o caminho antigo da fixture
em `test_neural_revisao_contextual.py`; corrigido para `scripts/tests/fixtures`,
sem mudar expectativas, e **32 testes desse módulo passaram**. Os outros dois
testes que falharam também pararam antes da fronteira desejada na guarda de
`revalidar_perfil_v4`; junto dos 21 erros, permanecem **23 casos bloqueados por
compatibilidade histórica**. Não há verde global. Mais **93 testes** de coleta,
curadoria, revisão e preparação passaram separadamente em 6,05 s.

Próximo passo de infraestrutura neural: revalidar explicitamente o alinhamento
do corpus histórico contra a linguagem atual e registrar diferenças, antes de
autorizar outro par de hashes na via de compatibilidade. Nunca substituir os
hashes do protocolo original. Essa pendência não é evidência de piora semântica
da v29. A reserva v29 permanece consumida; nenhuma reavaliação/seleção ocorreu.

### Reprojeção explícita do corpus histórico — 2026-09-21

Continuação da pendência acima, não alteração dos resultados da v29. O replay
refutou equivalência integral: 144 casos mudaram de leitura, dos quais 48
também mudaram segmentação e coordenadas relativas. Os lotes originais estão
intactos. Os mesmos 144 casos aparecem nos dois lotes, sem somar cobertura.

`revalidar_perfil_v4` agora oferece `--reprojetar`, exclusivamente offline:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.revalidar_perfil_v4 --reprojetar --destino memoria/neural/experimentos/reprojecao_literal_v4_20260921/relatorio.json
```

Esse destino já foi produzido e é protegido contra sobrescrita. Para outra
auditoria, escolher outro destino. A API correspondente é
`carregar_perfil_revalidado(reprojetar=True)`; a base de 672 casos é acessível
por `carregar_base_reprojetada()`, passando pelas mesmas guardas.

A nova via verifica integridade dos históricos, dependências revisadas,
diferenças exatas e igualdade da supervisão em offsets absolutos. Preserva
atos, alvos, relações, partições e flags falsas. Não aceita deriva futura
automaticamente; não transforma referência observada em anotação de treino.
Retorna cópias reprojetadas, sem editar os arquivos históricos. A via padrão
continua estrita; `carregar_base` e `carregar_perfil` históricos não mudaram.

Prova CLI: 1.176 casos únicos, folds idênticos, supervisão literal preservada,
**compatibilidade integral falsa**. Modelos e resultados históricos precisam
de nova avaliação antes de qualquer alegação de qualidade na representação
atual. Nenhum fit, reserva, promoção ou execução de habilidade nessa prova.
Os testes de algoritmos atuais usam a nova via explicitamente; as guardas
históricas permanecem cobertas por testes negativos.

Regressão neural final: **1.425 aprovados, 1 skipped, zero falhas/erros**,
105,63 s; 5.220 testes fora do recorte. Resolve os 23 bloqueios anteriores,
sem equivaler a suíte global ou runtime validado. Pesos ativo/v27 e
`modelo.py` do SOL conservam os hashes anteriores.

Foi registrada separadamente uma divergência entre a anotação de recusa e a
leitura de “não é para…” em turno misto. A reprojeção conserva essa diferença;
não certifica a correção semântica ou operacional do interpretador.

### Fechamento da fronteira declarativa “não é para…” — 2026-09-21

A investigação reproduziu o RED em
`rel_v4_necessidade_apps_e0_t0_q0_recusa_pedido`: a cláusula
`não é para abrir o aplicativo pelvora` era classificada como `conversa`,
sem veto de segmento, enquanto `preciso que você abra o aplicativo zafrin`
seguia como comando autorizado. O consumidor determinístico já usa
`texto_operacional`, portanto a raiz ficou no owner de modalidade, não no
executor nem no corpus supervisionado.

`analisar_protecao_operacional` passou a reconhecer, de forma independente
de domínio, a moldura `não é/eh para|pra + infinitivo operacional`. Sem
interrogação, ela produz `recusa/cancelamento`; com `?`, permanece pergunta
informativa sem autorização. Em turno misto, o veto continua pertencendo ao
segmento recusado: um pedido posterior independente permanece autorizado e
`texto_operacional` contém somente esse pedido. Não foi criado veto global
para o turno.

No corpus histórico há 72 nós com essa moldura; todos já possuem gold
`recusa`. Após a correção, os 72 são lidos como recusa com veto de segmento.
A nova leitura não foi absorvida atualizando hashes cegamente: a guarda
histórica bloqueou primeiro, depois um replay integral confirmou supervisão
literal preservada e quatro dobras idênticas. A reprojeção passou de 144 para
160 leituras diferentes do snapshot antigo, mantendo 48 resegmentações. Os 16
novos deltas são recusas isoladas de apps/arquivos que agora se alinham ao gold;
o snapshot observado antigo não é tratado como gold.

A reprojeção anterior permanece intacta em
`reprojecao_literal_v4_20260921/`. A revisão v2 foi publicada separadamente em
`reprojecao_literal_v4_recusa_declarativa_v2_20260921/relatorio.json`, com
`compatibilidade_no_corpus=false`, supervisão literal preservada,
classificador não reavaliado e runtime não validado.

Provas: 25 testes focados de autorização/consumidor, 33 de reprojeção,
76 testes de modalidade/autorização mais 22 subtests (1 skipped), e regressão
neural completa com **1.426 aprovados, 1 skipped, zero falhas/erros** usando
`pytest scripts/tests -k neural -q --tb=short`. Nenhum fit de produção,
promoção, alteração de pesos ou abertura de reserva foi feito.

## Histórico: coleta validada em sessão real controlada — 2026-09-09

`laylay.py` foi iniciado pelo executor oficial com
`roteiro_neural_coleta_prospectiva_seguro.py`: quatro frases de recusa/relato,
sem solicitar efeitos externos. Processo encerrou com código 0, quatro
respostas e zero comandos operacionais nos planos. Voz/microfone, abertura
do Terminal 2, briefing/presença e modo jogo automático foram desativados
somente no ambiente desse processo; IoT em modo simulado. Não é validação
dessas integrações. Serviços regulares ainda puderam produzir notificações.

`validar_coleta_runtime.py` conferiu os quatro registros persistidos contra
os planos e o roteiro: textos/tamanhos/hashes, IDs únicos, mesma conversa e
sessão, origem `roteiro_teste`, encadeamento anterior e ausência de rótulos,
partições ou autorização. **GREEN runtime da coleta**, não da conversa geral.
29 testes focados passaram (14 do validador e 15 da coleta).

Artefatos: `resultados_testes/roteiro_neural_coleta_prospectiva_seguro-20260909-084143-400566/`
(`validacao_coleta.json`, `planos.jsonl`, `resumo.json`, `conversa.md`). Coleta
em `memoria/neural/entradas_prospectivas.jsonl`: quatro amostras de teste,
zero amostra humana certificada. Contexto contém 0/0/2/4 mensagens; vínculo
ao turno anterior existe, mas histórico completo não foi certificado.

Falha separada observada no turno 2: resposta afirmou que o Opera não abriu
e sugeriu erro de conexão, sem evidência desse efeito. O avaliador `sem_comando`
passou porque não houve comando; isso não avalia fundamentação factual da
fala. Registrada em `melhorias e planos/erros_encontrados.md`, sem patch de
personalidade misturado à coleta. Modelo ativo permaneceu intacto em shadow.

Próximo: acompanhar uso cotidiano e revisar procedência/semântica dos novos
registros antes de formar partições. Não usar os quatro turnos roteirizados
como revisão humana ou avaliação inédita; investigar a fala inventada em
fronteira separada de fundamentação da resposta.

## Histórico: coleta prospectiva ligada à composição — 2026-09-09

`coleta_entradas.py` registra entrada literal recebida por
`ComposicaoTurnoRuntime.iniciar`, antes da revisão intra-turno, independente
do modelo neural, divergência ou executor. Ao retornar, associa o ID canônico
do turno; falha de planejamento mantém tipo de erro e ID ausente, sem inventar
um turno. Reutiliza o writer append-only do buffer existente em arquivo
separado `memoria/neural/entradas_prospectivas.jsonl`.

A raiz publica o coletor no registro allowlist. A próxima inicialização usa
`LAYLAY_NEURAL_COLETA_ENTRADAS=1` por padrão; `0` desativa sem apagar dados.
Sem coleta de eventos estruturados ou texto de origem `presenca`. Registra
conversa ativa, marcador de sessão do estado compartilhado, origem declarada
e contexto mínimo anterior (ID do turno e até quatro mensagens user/assistant,
sem system/tool). Origem humana e vínculo das mensagens à sessão NÃO são
certificados automaticamente. Roteiro/origem declarada e diagnóstico ativo
marcam teste, mas ausência desses sinais não prova autoria humana.

Limites explícitos: 16.000 caracteres por entrada, 2.000 por mensagem de
contexto, com tamanho original/hash e flag de truncamento; arquivo até 64 MiB,
sem limpeza automática. Falhas são reportadas à observabilidade e não mudam
decisão ou resposta do turno. Não grava previsões/receipts como rótulos;
nenhum registro autoriza treino, execução ou promoção. O modelo ativo segue
em shadow. Captura o que chega à composição, não certifica transcrição de
voz nem recupera transformações que já ocorreram antes dessa fronteira.

Dois REDs de integração foram reproduzidos antes do wiring: recusa sem
modelo/executor não chegava à coleta, e original revisado/contexto anterior
não era preservado. 15 testes focados passaram, incluindo wiring extraído
da raiz real e executado sobre o harness com componentes canônicos. Isso
NÃO é execução completa de `laylay.py`; não se anunciou GREEN runtime.

Regressão neural/P0 + composição, presença e revisão intra-turno: **1.306
passaram em 69,10 s**. Mais 16 testes de registros/composição passaram.
Compilação e `git diff --check` verdes; hash do modelo configurado preservado.
Nenhum arquivo prospectivo de produção foi criado pelos testes (usam tmp_path).

Próximo: observar uma sessão real controlada, verificar os registros, origem
e contexto, então revisar amostras naturais e fechar partições. Coleta nova
não torna o corpus atual pronto nem elimina revisão humana/grupos independentes.

## Histórico: shadow revisado; identificada lacuna de coleta — 2026-09-09

Extração por `curadoria_shadow_encoder.py`: 132 textos adicionais, com
referências a 233 eventos e marcação de compactação/truncamento do coletor.
Curadoria IA concluída: **5 casos compatíveis** (4 pedidos APP_OPEN e 1
FILE_READ); 127 fora do perfil conservados, sem virar negativos `ausente`.
101 textos aparecem literalmente nos roteiros verificados. Isso não prova
a origem de cada evento. Não há revisão humana ou promoção de rótulos.

O auditor de exposição passou a reconhecer linhas dentro de constantes
multilinha sem executar o roteiro. Dois REDs reproduzidos antes do patch;
posição no valor decodificado não é confundida com linha física do arquivo.

Acumulado: **209 textos distintos, 8 anotações IA no perfil, só 2 das 9
combinações variante/ato**. Partições continuam inviáveis. O buffer privilegia
resultados; o shadow só guarda texto nas divergências. Ambos são insuficientes
para medir compreensão representativamente. Não iniciar fit para compensar
essa ausência. Próximo: coleta prospectiva com origem/sessão/turno e contexto,
independente de sucesso/divergência, reutilizando o caminho canônico.

Artefatos: `memoria/neural/experimentos/curadoria_shadow_encoder_20260909/`
e `memoria/neural/experimentos/revisao_shadow_encoder_20260909/`. Produção,
modelo ativo em `shadow` e fontes históricas preservados; nenhum fit.

29 testes focados passaram (11 novos de extração, 18 do revisor, incluindo
os 2 REDs corrigidos). Regressão neural/P0: **1.260 passaram em 79,59 s**.
É validação offline; não prova runtime completo ou superioridade linguística.

## Histórico: triagem dos dados concluída; partições ainda insuficientes — 2026-09-09

`revisao_encoder.py` aplica revisão IA explícita à fila de experiências, com
snapshot fixado por hash e validação canônica das anotações. Os 77 textos
foram revisados: **3 pedidos APP_OPEN anotados, 74 fora do perfil atual**.
Esses 74 não viram negativos `ausente` nem são descartados; incluem consultas
de janelas, outros domínios, referências contextuais e destinos ambíguos.
Nenhuma anotação foi declarada humana ou promovida no ledger de aprendizado.

56 textos coincidem literalmente com três scripts v27 inspecionados, ligados
a 619 registros do buffer. Coincidência comprova exposição, não origem de cada
evento. A revisão não inventa contexto, linhagem ou partição independente.
Faltam oito das nove combinações do piloto; três pedidos da mesma família não
sustentam treino/seleção/calibração separados. **Não houve fit nem promoção.**

Saída: `memoria/neural/experimentos/revisao_encoder_20260909/`; entrada revisável
em `memoria/neural/experimentos/revisao_encoder_20260909_entrada.json`.
Próxima fonte identificada: log shadow existente, com 132 textos adicionais
às experiências. Suas divergências não são gold nem amostra representativa;
precisam de curadoria e procedência. Modelo ativo permanece em `shadow`.

16 testes novos passaram; regressão neural/P0: **1.247 passaram em 71,08 s**.
Validação offline de curadoria, não prova de compreensão ou runtime completo.

## Histórico: curadoria preparada e prova técnica na GPU concluída — 2026-09-09

`curadoria_encoder.py` organizou 665 registros válidos em **77 textos brutos
distintos**, com referências aos registros e decisões do ledger. Os textos
continuam pendentes: receipt não é rótulo de compreensão, e a origem do
componente não comprova uso cotidiano versus teste/caos. Uma linha inválida
ficou fora da exportação, sem alteração da fonte. Nenhuma anotação, linhagem
ou partição foi inventada. Fila: `memoria/neural/experimentos/curadoria_encoder_20260909/`.

Ambiente separado `.venv_neural314`: Python 3.14.6, PyTorch 2.11.0+cu128,
Transformers 5.16.1 e NumPy 2.5.1. `pip check` passou. Pesos MiniLM e tokenizer
conferidos por SHA-256 na revisão `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`.
A `.venv314` de produção não foi alterada.

`sonda_ambiente_encoder.py` executou na GTX 1660 SUPER duas condições pareadas:
encoder congelado e ajustável, mesma cabeça, pesos e logits iniciais. Um passo
AdamW com rótulos artificiais confirmou gradientes finitos, alteração da cabeça
nos dois braços e alteração do encoder somente no ajustável. Picos alocados:
514,11 MiB e 2.591,36 MiB, respectivamente. O teste usa batch 1, comprimento
128, float32 e dropout desligado; não dimensiona um treino completo, não mede
qualidade linguística e não salva pesos ajustados. Protocolo com versões/hashes
e resultados: `memoria/neural/experimentos/sonda_ambiente_encoder_20260909/`.

20 testes focados novos e **1.231 regressivos neurais/P0 passaram**. Não é
suíte global, caos ou prova do runtime completo. Modelo configurado e `shadow`
permanecem intactos; nenhum porteiro, executor ou composição de produção mudou.

Próximo: recuperar procedência/contexto e revisar a fila; fechar partições,
orçamento e seleção antes do comparativo congelado versus ajustado em três
sementes. A prova técnica não autoriza promoção. Detalhes no
[plano do piloto](../../melhorias%20e%20planos/PLANO_PILOTO_ENCODER_SUPERVISIONADO.md).

## Histórico: prontidão do piloto de ajuste supervisionado implementada — 2026-09-08

Direção aprovada: comparar Transformer congelado e ajustado, com mesma base
treinável, tokenizer e cabeça. Primeiro preparar dados e protocolo; não
continuar ablações lexicais nem promover o candidato anterior.

`protocolo_ajuste_supervisionado.py` implementa validação de procedência,
partições, parentesco transitivo, leakage e enquadramento, mais o consumidor
`preparar_particao`. Reutiliza supervisão v4, projeção de rótulos por token e
auditor canônico. Casos fora do perfil ficam contabilizados e separados,
nunca convertidos automaticamente em negativos da perda.

Quatro REDs do contrato novo foram reproduzidos e corrigidos: exposição
anterior em seleção/calibração; famílias equivalentes por caixa/espaço;
dependência indevida do alinhador de normalização para preparar texto bruto;
duplicação interna. O texto original, inclusive maiúsculas, é preservado.
Nenhum normalizador, porteiro, executor ou script experimental anterior mudou.

Auditoria dos 1.176 casos v4: corpus válido, todos ainda em desenvolvimento
conhecido, não pronto para preparação de treino. Sem reserva independente
fabricada; sem fit ou inferência. Artefatos em
`memoria/neural/experimentos/prontidao_ajuste_supervisionado_20260908/`.
28 testes focados e **1.211 regressivos neurais/P0 passaram em 74,08 s**;
compilação e `git diff --check` também passaram. Não é prova de runtime.

Próximo: inventariar experiências/correções, preparar curadoria natural e
partições; verificar ambiente isolado com forward/backward antes de fechar
orçamento e iniciar o comparativo. PyTorch/Transformers ausentes da `.venv314`;
nenhuma instalação realizada. Modelo ativo e configuração `shadow` intactos.
Detalhes e critérios no
[plano do piloto](../../melhorias%20e%20planos/PLANO_PILOTO_ENCODER_SUPERVISIONADO.md).

## Histórico: ablação lexical concluída; retirada isolada não resolve o ato de fala — 2026-09-08

`ablar_lexico_ocorrencias_v4.py` repetiu primeiro as quatro dobras do controle
contextual anterior: métricas de treino/teste e listas de erros individuais
idênticas, não apenas a média. Só então ajustou a condição que recebe os
mesmos 384 estados contextuais, sem o bloco explícito de janela lexical,
sufixos, capitalização e posição. Dados, dobras, encoder, tokenização,
hiperparâmetros e seed foram mantidos; nenhum alvo ou limite gold foi
fornecido como entrada. O protocolo registra hashes e aborta se a referência
divergir. Nenhum modelo operacional foi salvo ou promovido.

| Condição | Casos exatos / 1.176 | Ações ausentes | Ações extras | Pedidos inventados |
| --- | --- | --- | --- | --- |
| Contexto + bloco lexical/posição | 653 (55,53%) | 4 | 56 | 310 |
| Só estados contextuais | 618 (52,55%) | 146 | 12 | 256 |

Esta comparação mede ocorrência/variante/ato, ainda **sem alvos e sem execução**.
As duas condições continuam abaixo do gate de 95% exatos e zero pedidos
inventados/ações extras. A média com peso igual por grupo sobe de 49,63% para
54,69%, enquanto a taxa global cai: não selecionar somente a métrica favorável.

| Família deixada fora do treino | Casos | Exatos com bloco | Exatos sem bloco |
| --- | --- | --- | --- |
| alvo_topicalizado | 168 | 166 | 87 |
| estr_v3_direto (bloco histórico conectado) | 672 | 426 | 334 |
| instrucao_destacada | 168 | 31 | 138 |
| sequencia_solicitada | 168 | 30 | 59 |

Os 146 desaparecimentos da condição sem bloco estão na dobra histórica:
33 pedidos e 113 recusas viram `ausente`. A confusão recusa → pedido cai de
233 para 80, mas relato → pedido sobe de 76 para 167; pedidos novos fora das
ocorrências esperadas sobem de 1 para 9. Portanto, retirar os atributos não
elimina a confusão de autoridade: redistribui os erros entre mecanismos.

Ambas as condições acertam 100% dos respectivos treinos nas quatro dobras,
sem avisos de ajuste. A condição sem bloco usa 90/101/82/84 iterações,
contra 31/34/33/33 do controle. Isso não sustenta aumentar épocas como
resposta imediata ao RED de generalização. Também não prova incapacidade do
encoder: a ablação muda a dimensão, a quantidade de parâmetros e a
inicialização efetiva da MLP, apesar da mesma seed. O encoder ainda codifica
palavras e ordem; “sem léxico” significa sem o bloco explícito adicional.

Próxima fronteira: auditar os contrastes de pedido/recusa/relato nas famílias
que ganharam e perderam, separando desaparecimento de ocorrência de troca
de ato. A partir dessa evidência, especificar supervisão de escopo e tempo
para um controle posterior, sem entregar escopo gold na inferência, criar
parser paralelo ou avançar ao decoder de alvos com ato ainda RED. Não
retreinar o modelo ativo nem abrir reservas para escolher esse desenho.

Artefatos: `memoria/neural/experimentos/ablacao_lexico_ocorrencias_v4_20260908/`
(`protocolo.json`, oito relatórios por dobra e `resultado.json`); execução
offline em 113,23 s. Nove testes novos protegem a matriz, exclusão efetiva
do bloco, entradas inválidas, reprodução individual e completude. Os 22
testes focados passaram; a regressão neural ampliada + P0 autorização,
modalidade e isolamento terminou com **1.183 testes passando em 69,84 s**.
Não é suíte global nem caos. Compilação dos dois arquivos novos e
`git diff --check` também passaram. Modelo ativo e configuração `shadow` conferidos
intactos; produção, dados e artefatos anteriores não alterados. Este resultado
não é uma comparação com o parser operacional nem uma prova de runtime real.

## Histórico: contrastes auditados; erros isolados e influência da composição separados — 2026-09-08

`auditar_contrastes_ato_v4.py` analisou os oito relatórios congelados da sonda,
sem novo fit, inferência de modelo ou mudança de dado/parâmetro. Conferiu os
hashes de código e as quatro dobras. As previsões implícitas na lista COMPLETA
de erros foram reconstruídas e as métricas de cada relatório reproduzidas
integralmente. Uma inconsistência, erro removido ou contagem divergente aborta
a auditoria; reconstrução de relatório não é nova previsão do modelo.

Foram ligados 1.344 pares de ocorrências compostas às frases isoladas já
existentes, com texto literal e supervisão equivalentes, na mesma dobra de
avaliação. Há reutilização da mesma ocorrência isolada em vários pares;
portanto, não são 1.344 amostras estatisticamente independentes.

Na condição contextual, examinando a âncora esperada:

| Ato verdadeiro | Sozinho: previsto como pedido | Composto: previsto como pedido |
| --- | --- | --- |
| Recusa | 69/168 | 164/336 |
| Relato | 13/168 | 63/336 |

Isso refuta a hipótese de que todos os erros de ato venham de outra ação no
mesmo turno: 82 ocorrem também em frases isoladas. Por outro lado, **59 pares**
passam de ato correto isolado a pedido no composto (21 recusas e 38 relatos).
Composição afeta previsões, mas não prova causa exclusiva no encoder:
posição relativa, janela lexical e contexto do Transformer variam juntos.
Nenhuma dessas análises escolheu alvos gold para executar ou refez o treino.
O único pedido inventado fora das âncoras esperadas continua no relatório
original; as fatias acima não o transformam em acerto nem substituem o gate.

Também foi demonstrada uma limitação da janela lexical: **seis assinaturas
de atributos idênticas com rótulos distintos** em três das quatro fatias de
treino, impondo pelo menos **24 erros de token** por fatia a um classificador
determinístico que receba só esses atributos. Isso é limite por tokens, não
por casos, e não explica sozinho todos os erros do controle.

Exemplo concreto: o último `abra` em
`quero que você abra o aplicativo zafrin; não quero que você abra o aplicativo pelvora`
e em
`não quero que você abra o aplicativo pelvora; quero que você abra o aplicativo zafrin`
tem a mesma janela `que você abra o aplicativo`, mesmos atributos locais e
mesma posição relativa 0,8, mas um é recusa e o outro pedido. O `não` fica
fora da janela de duas palavras. Não é corrupção do rótulo: a representação
removeu a distinção relevante. Essa prova se aplica ao controle lexical;
o candidato contextual recebe informação adicional e ajustou todo seu treino.

Próximo controle: separar a contribuição lexical/posição da contextual nas
mesmas dobras, reproduzindo primeiro o controle contextual 653/1.176. Uma
ablação sem atributos lexicais pode testar dependência desses atalhos, mas
não é automaticamente uma correção nem deve receber fronteiras gold. Se a
combinação continuar RED, investigar escopo e tempo com supervisão explícita
antes de aumentar épocas ou dados. Ainda não há causa única demonstrada para
a generalização ruim do candidato contextual; não avançar ao decoder de alvos.

Artefato: `memoria/neural/experimentos/auditoria_contrastes_ato_v4_20260908/auditoria.json`,
incluindo pares, transições, colisões, hashes e flags de isolamento. Sete testes
novos protegem reconstrução, completude, pareamento na mesma dobra e limites
da representação. Os 20 testes focados (auditoria + sonda) passaram; regressão
ampliada: **1.174 passaram em 69,83 s** (`tests/test_neural*.py` + P0 autorização,
modalidade e isolamento), não suíte global/caos nem runtime completo.
Modelo ativo, reservas, configuração, scripts e artefatos anteriores intactos;
apenas auditor offline, testes e documentação adicionados nesta etapa.

## Histórico: comparação por ocorrência executada; ato de fala ainda RED — 2026-09-08

Implementado `comparar_ocorrencias_v4.py`, exclusivamente offline. Nas mesmas
quatro dobras congeladas, compara duas MLPs de 32 unidades (seed 27, até 1.200
iterações, mesmos demais parâmetros). Cada uma classifica TODOS os 22.320
tokens da entrada bruta, inclusive nomes e pontuação: nove combinações
variante/ato e `ausente`. Nenhum filtro de verbos, âncora gold ou modalidade
do porteiro determina quais posições serão avaliadas.

- Controle: janela lexical de dois tokens de cada lado, posição e atributos
  locais reutilizados de `atributos_token`.
- Candidato: mesmos atributos + 384 estados contextuais do token, extraídos
  do MiniLM local congelado. Só a MLP é ajustada; não houve fine-tuning do
  Transformer, download ou uso de serviço externo para os dados.

**É um controle adaptado à tarefa por ocorrência, não o head histórico por
segmento nem o modelo operacional.** Não se compara diretamente com 112/144
da sonda anterior: unidade, dados e supervisão mudaram. As duas condições
atuais compartilham exatamente entrada, rótulos, dobras e medição.

O [model card do MiniLM](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
documenta estados contextuais antes do pooling da frase, e a documentação de
[Encoding](https://huggingface.co/docs/tokenizers/api/encoding) descreve offsets
e máscaras. O adaptador offline usa uma instância isolada da sessão existente.
A projeção para tokens literais é nossa escolha experimental, não garantia de
compreensão de negação oferecida por essas fontes.

Antes do fit, o mapeamento encontrou 576 incidências de fronteira compartilhada:
subtokens `\";` e `\",` cobriam dois tokens de pontuação do tokenizador genérico.
RED focado reproduzido; corrigida a suposição de correspondência um-para-um.
A média agora é ponderada pela interseção em caracteres e normalizada L2,
preservando ambas as posições. Cobertura incompleta/vetores inválidos continuam
abortando, sem descartar tokens. Os 1.176 textos tiveram no máximo 47 tokens
do encoder, sem truncamento. Codificação completa: 7,02 s; execução válida:
35,88 s. Não são medidas de latência no runtime da assistente.

| Condição | Casos exatos / 1.176 | Ocorrências ausentes | Extras | Pedidos inventados |
| --- | --- | --- | --- | --- |
| Janela lexical | 432 (36,73%) | 16 | 140 | 344 |
| Janela + contexto por token | 653 (55,53%) | 4 | 56 | 310 |

Média de exatidão entre os quatro grupos: 33,93% e 49,63%, respectivamente.
São esperadas 1.848 ocorrências, incluindo recusas e relatos, NÃO 1.848 ações
autorizadas. A medição reutiliza `medir_acoes`; a segunda coordenada nas chaves
dos erros representa offset bruto da âncora, não índice de segmento.

| Família avaliada | Lexical | Contextual |
| --- | --- | --- |
| Alvo topicalizado | 152/168 | 166/168 |
| Bloco conectado anterior | 272/672 | 426/672 |
| Instrução destacada | 8/168 | 31/168 |
| Sequência solicitada | 0/168 | 30/168 |

**As duas condições reprovaram o gate de 95%, zero pedidos inventados e zero
extras. Não avançamos a vínculos/alvos.** No candidato contextual, os 310
pedidos inventados são 233 recusas, 76 relatos e uma âncora extra classificados
como pedido. Outros 221 pedidos esperados viraram recusa (116) ou relato (105).
Isso localiza uma fronteira importante no ato de fala, não apenas na detecção
de âncoras. Ainda existem quatro ausências e 56 extras; localização não está
encerrada. “Inventado” aqui é previsão offline, nunca efeito executado.

A condição contextual acertou todos os próprios casos de treino em cada dobra,
parando em 31–34 iterações sem avisos. Portanto, falta de ajuste ao treino não
explica seu RED de generalização. O controle lexical teve 936/1.008 nas três
dobras maiores e 504/504 na menor; essa diferença também deve ser preservada,
não escondida pelo resultado composto. Um seed e desenvolvimento sintético
não demonstram superioridade geral ou sobre o legado Python.

Artefatos válidos:
`memoria/neural/experimentos/comparacao_ocorrencias_v4_20260908_r1/`, com
protocolo anterior aos fits, oito relatórios por condição/dobra e resultado.
A tentativa sem `_r1` ficou incompleta: a publicação do primeiro relatório
falhou porque `loss_` era `float32`. Ela foi preservada e excluída do resultado.
A correção converte apenas os escalares dos metadados; nenhum parâmetro,
rótulo ou partição mudou na repetição. Hashes de código e fontes reconferidos.
Versões verificadas: sklearn 1.9.0, ONNX Runtime 1.27.0, tokenizers 0.23.1,
SciPy 1.18.1, Python do ambiente `.venv314`.

**13 testes focados e 1.167 regressivos passaram** (69,55 s na regressão neural
+ P0 autorização/modalidade e isolamento). Incluem ausência de gold na entrada,
várias ocorrências no mesmo trecho, contagem de pedidos falsos, cobertura de
subtokens e publicação de metadados float32. Não equivalem a runtime completo
ou suíte global/caos. Nenhum commit, reserva consultada ou modelo operacional
salvo/promovido. Configuração e hash do modelo ativo permanecem os mesmos.

Próxima fronteira: analisar os contrastes de escopo/tempo que fazem o candidato
trocar recusa ou relato por pedido fora da família de treino. Antes de ampliar
o treino ou ajustar o encoder, formular uma hipótese e controles para esses
atos, preservando todas as falhas e as quatro divisões como desenvolvimento.
Vínculos, alvos, comparação operacional e promoção continuam pendentes.

## Histórico: expansão com quatro grupos auditados, comparação ainda não treinada — 2026-09-08

`expandir_relacoes_v4.py` preservou integralmente os 672 casos anteriores e
acrescentou 504 contrastes: instrução destacada, sequência solicitada e alvo
mencionado antes do verbo. Mesmos domínios, inversões de nomes/papéis, aspas e
ordens; rótulos foram definidos nos moldes, sem consultar previsões. São agora
**1.176 casos e 1.848 ocorrências**, não 1.176 construções independentes.
O carregamento confere o hash do lote anterior e de suas dependências; nenhuma
guarda, anotação histórica ou arquivo de produção foi alterado.

O bloco anterior permanece unido. O auditor lexical compartilhado comparou
todos os pares entre blocos candidatos, mantendo o limiar 0,9: **zero pares
exatos/quase duplicados entre grupos**. A auditoria de entradas locais também
não encontrou repetição entre grupos. Irmãos da mesma construção/contraste
ficam juntos; nenhuma linha foi retirada para passar a divisão.

| Grupo avaliado fora do treino | Treino | Avaliação |
| --- | --- | --- |
| Alvo topicalizado | 1.008 | 168 |
| Bloco conectado anterior | 504 | 672 |
| Instrução destacada | 1.008 | 168 |
| Sequência solicitada | 1.008 | 168 |

Cada caso é avaliado uma única vez. Cada fatia de treino e avaliação tem as
nove combinações ato/variante e as quatro composições em ambas as ordens.
Essas são divisões de **desenvolvimento**, não uma reserva independente nem
certificação de independência semântica. A revisão dos moldes continua
assistida por IA, sem avaliador humano independente. Os textos são conhecidos
durante o desenho do experimento; não chamar o lote de teste cego.

Verificação adicional somente leitura: as 1.848 âncoras correspondem a tokens
inteiros no texto canônico. Os 1.176 textos distintos da entrada global/local
ocupam no máximo 47 tokens no tokenizer local sem truncamento. Isso viabiliza
a representação, não prova que o modelo consiga predizer as âncoras. Nenhum
encoder foi ajustado e nenhuma inferência de modelo foi feita nesta etapa.

Artefatos: `memoria/neural/experimentos/expansao_relacoes_v4_20260908/`
(`protocolo.json`, `lote.json`, `resultado.json`). SHA256 do lote:
`f389af34b78ecf540ce551867d27e21191d6855e8113410535a106392fb55a07`.
`divisao_viavel=True` indica somente aprovação estrutural da divisão;
`treino_permitido`, `autoriza_execucao` e `autoriza_promocao` seguem falsos.

Próximo comparativo, a implementar com protocolo congelado antes de ajustar:

1. Receber só texto e segmentos; não fornecer âncora, trecho anotado, ato,
   relação ou alvo esperado como atributo. Validar primeiro a detecção de
   ocorrências/atos, sem mascarar erros com alvos gold.
2. Usar as mesmas quatro dobras para controle e candidato, preservando o
   controle anterior. Se as saídas tiverem contratos diferentes, declarar e
   validar a projeção comum antes de comparar; não apagar recusas/relatos para
   adaptar o denominador ao head antigo.
3. Separar métricas por ocorrência, ato, variante, vínculo, alvo e plano
   completo. Relatar também por grupo e a média entre grupos: o bloco de 672
   casos não deve esconder uma regressão nas famílias de 168.
4. Manter 95% de exatidão e zero pedidos inventados/extras como critério de
   avanço da primeira fronteira, nunca como liberação operacional. Alvos e
   relações devem ter prova própria antes da comparação com o runtime/legado.

Validação desta etapa: sete testes novos, **26 focados** incluindo supervisão,
e **1.154 regressivos passaram em 74,00 s** (`tests/test_neural*.py` + P0
autorização/modalidade e isolamento). Não é suíte global/caos nem runtime
completo. Sem commits, downloads, consultas a reservas ou novo treino.
Configuração continua `shadow`; hash do modelo ativo foi reconferido e segue
`caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf`.

## Histórico: supervisão por ocorrência implementada; lote sem holdout válido — 2026-09-08

Escopo offline: `supervisao_relacoes_v4.py` e `preparar_relacoes_v4.py`.
Nenhum consumidor de produção, executor, configuração ou modelo ativo mudou.
Baseline desta etapa: `76aa525ef61fdb4ecfbfdb578adf572c0b83949a`, worktree já
continha mudanças no README e o comparador contextual v3 não rastreado.

Fronteira reproduzida antes da implementação: a anotação anterior rejeita
duas ocorrências da mesma variante no mesmo segmento com
`consolidar escopo da mesma ação no segmento`. Essa guarda permanece correta
para o plano consolidado v1/v2 e **não foi removida**. Não houve rerrotulagem
dos 144 casos nem alteração dos hashes históricos.

O novo perfil separa cada ocorrência com ID, ato, variante, trecho-fonte,
âncora e alvos. “Abra A; não abra B” conserva pedido e recusa mesmo quando o
segmentador real devolve um único segmento. A relação anotada `restringe`
liga uma recusa a um pedido da mesma variante; relato não cria essa relação.
IDs são referências da supervisão, nunca atributos de inferência. O payload
de entrada contém apenas texto original e segmentos canônicos.

Reutilizados: classificador/normalizador canônicos, transporte de offsets por
proveniência, `vincular_plano_manual` e `validar_anotacao_escopo` por ocorrência.
O novo contrato valida estrutura, não adivinha o sentido de texto livre.
Alvos literais com negação dentro do nome são preservados. Campos de autoridade,
relações incompatíveis, spans inválidos e escopos sobrepostos são rejeitados.
O perfil inicial não cobre escopos aninhados, referências implícitas ou conflitos
temporais: exigem revisão própria, não fallback nem autorização presumida.

Preparados **672 casos sintéticos e 1.056 ocorrências**: 480 pedidos, 288 recusas
e 288 relatos. Quatro paradigmas, três domínios, nomes com papéis invertidos,
com/sem aspas, atos isolados e composições em ambas as ordens. Nenhuma frase
integral duplicada exata; não são 672 construções semanticamente independentes.
Toda a grade foi alinhada usando os componentes reais de linguagem, sem abrir
a Laylay, usar previsão de modelo como rótulo ou executar comandos.

**A comparação ficou bloqueada na independência dos grupos, antes de qualquer
treino.** O auditor lexical compartilhado, com limiar mantido em 0,9, encontrou
128 pares entre paradigmas. O fecho transitivo reuniu todos os casos em um
único grupo: `direto` ↔ `possibilidade` ↔ `necessidade` ↔ `vontade`.
Não há dobras válidas. A verificação adicional de projeções locais não precisou
unir mais grupos. Não baixamos o limiar nem redistribuímos os irmãos para criar
um verde. O identificador `estr_v3_direto` veio do agrupador compartilhado;
o perfil e a supervisão deste lote são v4.

Artefatos preservados em
`memoria/neural/experimentos/supervisao_relacoes_v4_20260908/`:
`lote.json` e `protocolo.json`, com fontes, hashes, composição, auditoria e
pendências. SHA256 do lote:
`f0b93360db17042b7c5af3794e44448a39611dfee62c96f135815d6bc074d09b`.
Flags de treino, execução e promoção permanecem falsas. Nenhuma reserva foi
consultada. Moldes são assistidos por IA, sem revisão humana independente.

Validação: **19 testes focados e 1.147 regressivos passaram** (72,58 s na
regressão `tests/test_neural*.py` + P0 autorização/modalidade e isolamento).
Isso prova contratos offline e integração com linguagem real, não runtime
completo, superioridade do modelo ou suíte global/caos. O teste novo está
presente localmente, mas é ignorado pela regra existente do Git para testes;
essa regra não foi alterada. Nenhum commit criado.

Próxima fronteira: revisar os rótulos e preparar famílias de construção
independentes desse bloco conectado. Fixar a comparação pareada antes do fit,
com as mesmas partições para ambos os candidatos e métricas separadas para
ato, vínculo, alvos e plano completo. Os 672 casos ficam em desenvolvimento,
não viram teste independente nem justificam liberação. Modelo ativo segue
`shadow`, com o mesmo hash registrado abaixo.

## Histórico: controles de contexto não resolvem o dono da ação — 2026-09-08

Executado `comparar_dono_contextual_v3.py`, sem alterar produção: mesmos 144
casos de desenvolvimento, 12 dobras por construção, encoder congelado e MLP
do comparativo anterior. Protocolo registrado antes dos ajustes. O controle
global/local reproduziu exatamente o resumo anterior; não houve mudança de
limiares nem uso das reservas.

| Representação | Casos exatos / 144 | Ações ausentes | Ações extras | Pedidos inventados |
| --- | --- | --- | --- | --- |
| Global/local (controle) | 112 | 9 | 15 | 22 |
| Somente segmento local | 107 | 11 | 15 | 21 |
| Contexto com segmento marcado + local | 97 | 14 | 16 | 26 |

“Marcado” significa serialização textual em português indicando o segmento
analisado, não tokens especiais treinados nem fine-tuning do encoder. Os 360
textos distintos tinham no máximo 79 tokens; nenhum sofreu truncamento.
Codificação ONNX: 2,94 s no lote; experimento completo: 160,47 s. Esses tempos
não medem latência de produção.

**Nenhuma condição passou o gate de ação; não avançamos para alvos/BIO.**
Nas três condições, cada dobra acertou os próprios 132 casos de treino.
As 12 propostas positivas extras em `pedido_apos_exclusao` persistiram mesmo
sem vetor global. Portanto, a hipótese de que retirar o contexto global seria
suficiente foi falsificada neste protocolo; isso não prova que contexto jamais
contribua para erros. Na família `pedido_escolha`, os três extras locais
mudaram de pedido para recusa, mas continuaram extras. Relatos transformados
em pedidos passaram de 7 no controle para 8 no local e 11 no marcado; o local
também inventou um pedido em cancelamento. Não houve redução geral do risco.

Próxima fronteira: auditar a supervisão e a representação da relação entre
ato de fala, ação candidata e segmento, começando pelos erros que persistiram
nas três condições. Essa auditoria deve conferir o texto original, a
segmentação real e o contrato de anotação antes de propor um head conjunto
ou ajuste do encoder. Não ampliar dados, ajustar parâmetros ou remover guardas
para compensar esses erros sem um novo protocolo causal. O resultado ainda
não compara este candidato com o legado Python ou com o modelo ativo.

Artefatos: `memoria/neural/experimentos/ablacao_dono_contextual_v3_20260908/`
(`protocolo.json`, `resultado.json`). Nove testes novos protegem isolamento do
vetor local, controle idêntico, marcação/posição e rejeição de gabarito; os 21
testes dos dois experimentos passaram. Regressão ampliada: **1.128 passaram
em 73,78 s** (`tests/test_neural*.py` + P0 autorização/modalidade e isolamento
de contexto), não suíte global/caos nem validação do runtime real.
Nenhum modelo operacional foi salvo,
promovido ou executado. Configuração continua `shadow`; hash do modelo ativo
permanece `caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf`.

O protocolo conserva o baseline `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`.
Durante a execução, o HEAD externo avançou para
`76aa525ef61fdb4ecfbfdb578adf572c0b83949a`; todos os hashes de código fixados
neste protocolo foram reconferidos e permaneceram iguais. Não foi criado
commit por esta execução, nem regravado o baseline histórico.

## Histórico: sonda semântica melhora, mas não passa segurança — 2026-09-07

Pesquisa técnica e inventário confirmaram que já existe um encoder local:
`EncoderSemanticoONNX`, MiniLM multilíngue quantizado. Ele foi reutilizado em
instância separada, sem downloads, alteração do encoder ou uso de serviços
externos para os dados. O [model card do MiniLM](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
documenta vetores de 384 dimensões, média dos tokens e contexto de 128 tokens.
Isso não é um decodificador de relações ação/alvo. O trabalho
[BERT para intenção e slots](https://arxiv.org/abs/1902.10909) avalia treinamento
conjunto dessas tarefas; a documentação de
[Cross-Encoders](https://sbert.net/examples/cross_encoder/applications/README.html)
descreve classificação/pontuação de pares. Nenhuma dessas fontes prova que uma
dessas arquiteturas já resolve os contratos da Laylay.

Executado `comparar_contexto_semantico_v3.py`: mesma MLP de 32 unidades, seed
27, limite 1200 e as mesmas 12 dobras dos 144 casos. Três condições congeladas
antes da inferência/treino:

- lexical: controle cruzado anterior, reproduzido;
- semântica: vetor da frase original completa + vetor do segmento analisado,
  posição e variante candidata, com interação genérica variante/vetor;
- híbrida: atributos lexicais e semânticos concatenados, sem calibrar pesos.

O encoder é pré-treinado e **congelado**; o treino desta sonda ajusta só a MLP.
Vetores foram pré-computados sem rótulos; o vectorizer de cada head aprende
somente no treino da dobra. A inferência recebe texto, segmentos e candidata,
não gabarito/veto/alvos. Ausência/vetor inválido aborta, sem fallback lexical.
Preflight com tokenizer separado conferiu os 192 textos distintos: máximo de
32 tokens, nenhum truncamento. Codificação real ONNX levou 1,36 s no lote;
isso não é latência por turno em produção. Sonda completa levou 102,90 s.

| Representação | Casos exatos / 144 | Ações ausentes | Ações extras | Pedidos inventados |
| --- | --- | --- | --- | --- |
| Lexical (controle) | 37 | 11 | 12 | 74 |
| Semântica global/local | 112 | 9 | 15 | 22 |
| Híbrida | 51 | 7 | 12 | 54 |

**Nenhuma passou o gate anterior de 95%, zero pedidos inventados e zero extras.**
Medição apenas do head de ação, não dos alvos completos, legado Python ou
modelo ativo. Um seed e dados sintéticos conhecidos não certificam ganho
estatístico/geral. O resultado sustenta investigar semântica pré-treinada,
não simplesmente acumular atributos ou declarar uma arquitetura vencedora.
Não houve seleção/promocão de modelo operacional nem avaliação das reservas.

Na condição semântica, todos os 132 casos de treino de cada dobra foram exatos.
Dos 22 pedidos inventados, 15 surgiram no segmento sem ação positiva anotada
(12 na família de exclusão seguida de pedido; 3 na de escolha), e 7 vieram de
relatos. As quatro famílias de relato, antes zeradas no controle cruzado,
agora somam 39/48 exatos. Melhorou o ato de fala, mas **o dono da ação continua
RED**. Contexto global influenciando um segmento negativo é uma hipótese para
os 15 extras, não causa única comprovada.

Próxima fronteira: controles local-only versus global/local e representação
do segmento dentro da sequência contextual, antes de mexer no decoder de
alvos. Comparar por família e manter os 15 erros de dono e 7 relatos no
denominador. Só depois investigar head conjunto/token-level ou fine-tuning,
com protocolo próprio; o encoder médio atual não foi convertido em um
CrossEncoder ajustado nem em classificador por token nesta etapa.

Artefatos: `memoria/neural/experimentos/sonda_contexto_semantico_v3_20260908/`
(`protocolo.json`, `vetores_congelados.npy`, `resultado.json`; identificador UTC).
Protocolo inclui fontes, hashes de encoder/tokenizer/código, versões,
comprimentos, textos sem rótulos e dobras. Controle lexical repetiu exatamente
o resumo anterior. Doze testes focados passaram para representação, posição,
ausência de gabarito, vetores inválidos e truncamento. Regressão ampliada:
**1.119 passaram em 70,09 s** (`tests/test_neural*.py` + P0 autorização/modalidade
e isolamento de contexto), não suíte global/caos. Modelo ativo, configuração,
dados pessoais e reservas preservados; nenhum commit ou lançamento da Laylay.

## Histórico: comparativo estrutural reprovado — 2026-09-07

Executado `comparar_lote_estrutural_v3.py` sobre os 144 casos alinhados e
congelados. O perfil explícito deriva supervisão pela interface existente,
sem modificar as proibições dos sidecars. Fontes fixadas por SHA256; reservas
não abertas. São 12 dobras de 132 casos no treino e 12 no teste, cada família
completa fora do treino uma vez. Irmãos, nomes e aspas da mesma construção
permanecem no mesmo grupo. Todas as variantes, atos e donos no segundo segmento
continuam representados no treino de cada dobra.

Protocolo gravado antes de qualquer ajuste: representação original versus
cruzada, mesma MLP de 32 unidades, seed 27, até 1200 iterações em ambas.
Nenhuma busca adaptativa de parâmetros. Cada vectorizer aprende somente na
dobra de treino. O critério pré-registrado para avançar à medição BIO exige
ao menos 95% de exatidão da ação, zero pedidos inventados e zero ações extras.
Esse critério não permite promoção ou execução, mesmo se for satisfeito.

| Head avaliado | Casos exatos / 144 | Ações ausentes | Ações extras | Pedidos inventados |
| --- | --- | --- | --- | --- |
| Original | 22 | 32 | 12 | 58 |
| Cruzado | 37 | 11 | 12 | 74 |

Os números medem variante, dono, ato e resolução; **não medem alvos completos**.
Pedidos inventados são previsões offline, não ações executadas. A representação
cruzada melhorou parte da cobertura, mas piorou o risco; não é um candidato
aprovado. Os resultados não podem ser comparados diretamente aos 49/96 do lote
anterior, pois dados e desenho de avaliação mudaram. A comparação pareada
válida aqui é original versus cruzada nas mesmas dobras de 144 casos.

Em todos os 24 ajustes, os próprios **132 casos de treino foram exatos**.
A original parou entre 350 e 423 iterações, e a cruzada entre 78 e 118, abaixo
do teto. Portanto, subajuste ao treino observado nas dobras antigas não explica
sozinho o RED atual. O problema está na generalização para construções fora do
treino: por exemplo, na representação cruzada, todas as quatro famílias de
relato tiveram zero casos exatos, e três delas viraram pedido nos 12 exemplos.
Negação e dono da ação também continuam falhando em famílias específicas.

**Os dois candidatos reprovaram o gate.** Nenhuma cabeça BIO foi ajustada ou
avaliada nesta etapa, nenhum modelo final foi escolhido/salvo para uso e nenhum
executor foi chamado. Não esconder o RED de ação com preenchimento de alvos ou
retorno da decisão do porteiro. O modelo configurado permanece o v27 em sombra.

Próxima investigação: representação de contexto/ordem e contrastes de ato de
fala, tomando este baseline vermelho como controle. Não continuar apenas
aumentando iterações ou substituindo nomes em moldes. Os 144 exemplos contêm
somente 12 construções sintéticas: representação, diversidade e objetivos de
aprendizado ainda precisam ser separados por controles antes de escolher a
próxima arquitetura. Um codificador contextual é uma hipótese a avaliar, não
uma solução já comprovada. Continuam pendentes relações completas, comparação
com o sistema atual/histórico, sombra real e liberação operacional gradual.

Artefatos: `memoria/neural/experimentos/comparacao_estrutural_v3_20260907/`
(`protocolo.json`, `resultado.json`), com fontes/código/ambiente/HEAD/worktree,
ids das dobras, métricas de treino/teste e erros por caso. Duração dos ajustes
e avaliação: 13,50 s. Sete testes focados passaram para isolamento, cobertura,
denominadores e gate; esse verde não altera a reprovação do modelo.
Regressão ampliada: **1.107 passaram em 64,92 s** (`tests/test_neural*.py` +
P0 autorização/modalidade e isolamento de contexto), não suíte global/caos.
Produção, modelo ativo, configuração e reservas intactos; nenhum commit.

## Histórico: transporte por proveniência, 144/144 alinhados — 2026-09-07

Implementado `transporte_anotacoes_normalizadas.py`, exclusivamente offline.
O alinhador literal anterior e o gerador congelado não foram modificados.
O RED foi reproduzido antes do candidato: `cancele ...` vira `cancela ...` no
corretor compartilhado e deixa de corresponder literalmente ao segmento.

O novo transporte chama o mesmo corretor e o classificador canônico, valida a
anotação original e reconstrói exatamente o texto normalizado usando os eventos
`de/para/tipo`. Cada caractere não alterado conserva sua origem; menções e
âncoras só são transportadas quando permanecem literais e contíguas. Mudanças
de comprimento anteriores ao alvo deslocam offsets, não o alvo ou seu papel.
Nenhum nome é procurado por semelhança, nenhum rótulo vem de modalidade/veto
e nenhuma saída do modelo é consultada para montar o esperado.

Guarda geral: sem posição no evento, a ocorrência precisa ser única, inclusive
contra ocorrências sobrepostas. Evento ausente, transformação não registrada,
correções sobrepostas, alteração dentro de alvo/âncora, referência ambígua ou
divergência do texto estrutural abortam. Casefold e compactação de espaços sem
mapa explícito continuam bloqueados; não alegar suporte universal a qualquer
normalização. Fontes com múltiplas ações ainda exigem âncoras separadas e são
rejeitadas por este adaptador. Esses limites não autorizam descartar exemplos.

**Execução no lote congelado: 144/144 alinhados, 12 com transformação registrada.**
As 12 recusas continuam recusas, com o mesmo alvo excluído e texto original.
Os outros 132 casos mantêm anotações idênticas ao alinhador anterior. O medidor
canônico recebe a frase original e os segmentos reais normalizados, sem
gabarito: foi testado que uma previsão vazia continua contando como ação ausente.
Isso é GREEN de preparação/integração de componentes reais, não prova de
qualidade neural ou operação da assistente em sessão real.

Artefato novo, sem sobrescrever os anteriores:
`memoria/neural/experimentos/lote_relacional_estrutural_v3_alinhado_20260907/alinhamento.json`.
Contém fonte original, texto normalizado, passos/offsets, âncora antes/depois,
hashes e grupos. O lote selecionado precisa estar vinculado ao protocolo e
todas as fontes congeladas são verificadas. Qualquer falha impede publicação
de um lote parcial. `treino_permitido`, `autoriza_execucao` e
`autoriza_promocao` permanecem falsos.

Próximo passo: perfil explícito de treino para este desenvolvimento alinhado,
protocolo comparativo por grupos e avaliação primeiro dos falsos pedidos, depois
das relações completas. As reservas continuam fora do treino/ajuste. Ainda
faltam demonstrar superioridade segura, validar em sombra real e liberar
gradualmente; nenhum modelo foi treinado ou promovido nesta etapa.

Testes iniciais de transporte + lote: **315 passaram**; depois foram adicionados
dois controles do medidor e do vínculo entre protocolo e arquivo selecionado.
Regressão ampliada final: **1.100 passaram em 69,72 s** (`tests/test_neural*.py`
+ P0 autorização/modalidade e isolamento de contexto), não suíte global/caos.
Compilação e hashes do artefato passaram; recarga confirmou igualdade das 132
anotações anteriores e preservação das fontes das 12 transformadas.
Produção operacional, corretor linguístico, executores, configuração e modelo
ativo preservados. Sem lançamento da Laylay ou commit. Base
`a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, `main`, worktree suja preservada.

## Histórico: lote estrutural de desenvolvimento preparado — 2026-09-07

Criado `preparar_lote_relacional_v3.py`, sem treinamento ou consulta de modelo.
O lote contém **144 exemplos sintéticos**, em 12 moldes: quatro de pedido com
exclusão/correção, quatro de recusa e quatro de relato. São 48 casos por ato e
48 por domínio (apps, música e arquivos). Usa somente os dois pares de nomes
já conhecidos no desenvolvimento, com/sem aspas e negação dentro de títulos.
Não equivale a 144 construções independentes nem a uma amostra de uso real.
As três variantes continuam `APP_OPEN/open`, `MUSIC_SEARCH/search` e
`FILE_READ/read`; este lote não cobre OOD geral, alternativas ou todos os atos.

Os rótulos são definidos nos moldes revisados, com autoria assistida por IA.
Offsets são construídos junto com os slots; uma âncora explícita antes do
verbo anotado identifica o dono. O alinhamento usa apenas posição literal
única e monotônica no segmento canônico, sem decidir intenção a partir do
veto/modalidade, sem fuzzy matching e sem escolher alvo pelo modelo.

Todos os irmãos de uma construção (nomes, domínios, aspas) permanecem juntos.
O agrupador reutiliza `auditar_leakage_dataset`, limiar **0,9**, e une famílias
por fecho transitivo se houver proximidade entre moldes. Neste lote, não houve
pares entre moldes acima do limiar: ficaram **12 grupos de 12 casos**.
Isso é auditoria lexical interna, não certificação de independência semântica
ou comparação contra reservas. O lote e o protocolo foram gravados antes da
auditoria formal; nenhuma reserva foi aberta, rerrotulada ou usada para treino.

**Resultado de alinhamento: 132/144; 12 pendentes, não descartados.** Todos os
12 casos de cancelamento de ideia permaneceram na fonte e na lista de falhas.
O relatório continua com `treino_permitido=False`, `autoriza_execucao=False`
e `autoriza_promocao=False`. Não treinar apenas os 132 para contornar o problema.

Primeira fronteira localizada:

`cancele a ideia de abrir o aplicativo zafrin`
→ `corrigir_erros_portugues_operacionais`
→ `cancela a ideia de abrir o aplicativo zafrin`
→ segmento canônico sem correspondência literal integral na fonte
→ alinhamento estrito rejeita.

O corretor confirma a transformação com `{de: cancele, para: cancela,
tipo: verbo_operacional}`. O classificador conserva um único segmento e o
ato recusa. Portanto, não é divisão indevida em vários segmentos nem erro de
offset do nome que explique esses 12 bloqueios. O contrato faltante no
alinhamento é **proveniência explícita entre texto original e normalizado**.
Não foi removida a correção linguística nem alterada a frase da fonte para
obter um verde. O mesmo princípio deve proteger qualquer domínio e qualquer
transformação compatível, inclusive alterações de comprimento.

A auditoria de suporte dos registros já alinhados mostra que, retirando cada
família alinhada, o restante ainda contém pedido/recusa/relato e ação no segundo
segmento. Isso corrige a lacuna estrutural detectada no lote antigo, mas não
prova aprendizado. O grupo de cancelamento tem zero casos de teste alinhados;
seu resumo não é uma dobra utilizável nem pode ser reportado como acerto.

**Próxima fronteira, antes do treino:** transportar os vínculos por um mapa de
transformações verificável, preservando a fonte, os papéis e a âncora. Rejeitar
transformações ambíguas, não registradas ou que alterem uma menção literal sem
contrato. Confirmar os 144 alinhamentos, revisar as separações semânticas e só
então criar o perfil explícito de treino e o protocolo comparativo. Reservas
continuam fora desse processo; o próximo candidato completo ainda precisará
demonstrar segurança, superioridade, sombra real e liberação gradual.

Artefatos preservados:
`memoria/neural/experimentos/lote_relacional_estrutural_v3_20260907/`
(`lote_fonte.json`, `protocolo.json`, `auditoria.json`). Testes focados:
**210 passaram**, incluindo 152 novos testes de geração, transporte literal,
papéis, agrupamento transitivo, falhas no denominador e proibições. Esse verde
comprova também a rejeição segura dos 12 casos, não alinhamento completo.
Regressão ampliada: **935 passaram em 78,63 s** (`tests/test_neural*.py` +
P0 autorização/modalidade e isolamento de contexto), não suíte global/caos.
Produção, modelos, configuração, executores e dados pessoais não foram
alterados; sem treino, lançamento da Laylay ou commit. Base
`a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, worktree suja preservada.

## Histórico: diagnóstico controlado do head de ação — 2026-09-07

Executado `diagnosticar_head_relacional.py`: quatro condições pré-registradas,
com os mesmos 96 exemplos de desenvolvimento, mesmas dobras e seed 27.
Variações: representação original/cruzada × limite de 180/1200 iterações.
Representação cruzada mantém os atributos anteriores e acrescenta interações
lexicais texto–variante para **todas** as variantes candidatas; não consulta
rótulos, nomes cadastrados ou uma lista de comandos por domínio.

O objetivo é medir a primeira fronteira (variante, segmento dono, ato e
resolução), sem executar a cabeça BIO e sem fornecer alvos esperados à rede.
**As métricas abaixo NÃO são da relação completa ação/alvo.** O controle
original reproduziu as ausências, extras e pedidos inventados das quatro
dobras do experimento anterior. Os 16 ajustes são experimentais; nenhum head
foi instalado no candidato completo ou no runtime.

| Condição | Ações exatas / 96: construções | Ações exatas / 96: entidades | Pedidos inventados: construções / entidades |
| --- | --- | --- | --- |
| Original, 180 | 0 | 6 | 0 / 5 |
| Original, até 1200 | 18 | 95 | 8 / 0 |
| Cruzada, 180 | 49 | 96 | 24 / 0 |
| Cruzada, até 1200 | 49 | 96 | 24 / 0 |

**Diagnóstico refinado:** não era simplesmente memorizar os dados e falhar
fora deles. Com 180 iterações, as quatro dobras originais acertavam somente
19/48, 29/48, 0/48 e 0/48 dos seus próprios casos de treino. O ajuste final
anterior em 96 casos não revelava essa diferença. O batch automático local
usa até 200 linhas: as dobras têm 144–180 linhas e um passo por época; o
ajuste final tem 324 linhas e dois passos (360 passos Adam em 180 épocas,
confirmados no artefato). Isso explica parte da diferença de orçamento, não
prova isoladamente a causa inteira.

Mantendo dados e representação, o limite maior levou todas as dobras a 48/48
no treino e melhorou entidades para 95/96: **ajuste insuficiente contribuiu**.
Mantendo o limite original e cruzando atributos, todas também chegaram a
48/48 no treino, com 96/96 em entidades: **a representação contribuiu**.
A representação cruzada parou entre 119 e 151 iterações pelo critério do
otimizador. A condição de até 1200 repetiu exatamente as mesmas métricas,
portanto aumentar apenas o teto não resolve o RED restante dessas condições.
Não é prova de ótimo global nem conclusão estatística com múltiplos seeds.

Fronteira ainda RED em construções: 12 recusas viraram pedidos e 12 ações
extras foram propostas no segmento sem ação anotada. Também houve confusão
entre relato/recusa e perda do ato pedido no dono correto. Os 24 pedidos
inventados impedem promover a representação pelo ganho médio. O zero anterior
não certificava segurança útil: o baseline omitia todas as ações esperadas.

Auditoria somente de desenvolvimento confirmou que **as classes esperadas
existem em ambos os treinos**, mas não toda a estrutura: em uma dobra, as 48
entradas de treino têm um único segmento; no teste, 12 exigem dois segmentos
e dono no segundo. Há 176 e 212 features novas nas dobras cruzadas de
construção. Isso sustenta uma lacuna de cobertura, sem provar que adicionar
exemplos sozinho resolverá tudo. Não foram encontradas colisões exatas com
rótulos contraditórios nos vetores de teste dessas dobras; não se declarou
perda irreversível de informação como raiz.

**Próximo passo:** preparar um lote de desenvolvimento revisado que cubra
formas de pedido/recusa/relato e múltiplos segmentos por famílias distintas,
preservando irmãos e paráfrases da mesma construção no mesmo grupo. Congelar
novo protocolo antes dos ajustes; comparar a representação sustentada pelos
controles, medir primeiro os falsos pedidos e só depois a saída completa BIO.
Não treinar nas reservas nem corrigir seus rótulos para acompanhar a rede.
Uma vez sustentado o candidato completo, ainda faltam comparação contra o
sistema atual/histórico, sombra no runtime real e liberação gradual com
governança e receipts externos. Nenhuma etapa de liberação foi antecipada.

Artefatos: `memoria/neural/experimentos/diagnostico_head_relacional_fatorial_v1_20260907/`
(`protocolo.json`, `resultado.json`). Protocolo gravado antes dos fits, com
hashes das fontes/código, ambiente, HEAD, branch, worktree e ids das dobras.
O baseline anterior e seu código permanecem intactos. Testes focados:
**129 passaram**, cobrindo também o candidato anterior; 15 testes novos de
diagnóstico. Regressão ampliada: **783 passaram em 63,28 s**
(`tests/test_neural*.py` + P0 autorização/modalidade e isolamento de contexto),
não suíte global nem caos. Nenhuma reserva consultada, modelo completo ajustado, promoção,
lançamento da Laylay ou efeito físico. Modelo ativo mantém `shadow` e SHA256
`caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf`.
Produção operacional inalterada. Base
`a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, `main`, worktree suja preservada;
nenhum commit criado.

## Histórico: reserva alinhada e primeiro candidato relacional — 2026-09-07

Etapa 1 concluída: **32/32 casos** da reserva independente revisados e alinhados
com o classificador canônico, sem consultar previsões neurais. Rótulos e texto
original preservados; revisão assistida por IA, não revisão humana independente.
Cinco planos têm múltiplos segmentos. No caso IoT, o classificador omite
`, mas ` dos segmentos: a lacuna foi explicitamente revisada e registrada,
mantendo o conector na entrada completa. Nenhuma menção pode ser realocada para
essa lacuna; ela não vira segmento, alvo ou autoridade. Alinhamento ausente ou
inválido continua abortando. Artefato:
`resultados_testes/reserva_independente_alinhada_20260907.json`.

Etapa 2 iniciada com **treino efetivo**, exclusivamente experimental:
`candidato_relacional.py` usa duas MLPs pequenas (32 unidades ocultas):

- Cabeça de ação: propõe variante, segmento dono, ato e resolução do alvo.
- Cabeça de menções: prevê papéis BIO por token e reconstrói offsets literais,
  inclusive quando a menção está em outro segmento. BIO incompatível é falha
  de inferência mensurável, sem corrigir a previsão usando o esperado.

Features lexicais genéricas de palavras/bigramas, janela de tokens e posições;
não há lista de nomes-alvo nem parser privado de comandos. A inferência recebe
somente texto e índices/textos dos segmentos; não recebe anotações, veto,
modalidade, grupos ou variantes esperadas. Isso é um primeiro baseline neural
relacional, **não uma arquitetura contextual pré-treinada**.

O perfil explícito `desenvolvimento_relacional_v1`, em
`treinar_relacional_isolado.py`, deriva supervisão somente dos **96 casos de
desenvolvimento** revisados, com fontes fixadas por hash. Não modifica as
proibições dos sidecars originais. Reservas são rejeitadas e nenhum arquivo de
reserva é aberto pelo treino. O protocolo foi gravado antes do primeiro fit;
parâmetros/seed fixos, sem busca de hiperparâmetros, normalizador aprendido
apenas na dobra de treino e separação dos irmãos com/sem aspas.

Experimento preservado em
`memoria/neural/experimentos/candidato_relacional_mlp_v1_20260907/`:
`protocolo.json`, `resultado.json`, `candidato_offline.joblib`.

| Medição | Casos exatos | Interpretação |
| --- | --- | --- |
| Mesmos 96 casos do ajuste final | 95/96 | Ajuste in-sample; não prova generalização |
| Validação por família de construção (2 dobras) | 0/96 | RED; 96 ações esperadas ausentes |
| Validação por grupo de entidades (2 dobras) | 6/96 | RED; 76 ações ausentes, 16 extras, 5 pedidos inventados |
| Reserva independente | Não avaliada | Mantida fora da escolha do candidato |

Primeira fronteira RED: **seleção da ação**, anterior à decodificação dos
alvos. Não houve exceções de inferência nessas dobras. A round-trip BIO dos 96
casos preserva spans e o artefato recarregado reproduz exatamente a medição
in-sample: essas evidências afastam perda de offsets/serialização como
explicação desses resultados. Não provam uma única causa de generalização.
Nove cabeças atingiram o limite de 180 iterações sem convergência declarada;
qualidade da representação, baixa diversidade e ajuste insuficiente continuam
hipóteses concorrentes. Não aumentar épocas ou exemplos cegamente.

**Próxima fronteira:** diagnosticar o head de ação nos dados de desenvolvimento,
separando essas hipóteses com controles pré-registrados e preservando este
baseline vermelho. As três variantes treinadas são `APP_OPEN/open`,
`MUSIC_SEARCH/search`, `FILE_READ/read`; não há cobertura geral/OOD certificada.
Não avançar para comparação de liberação usando a reserva antes de existir
um candidato sustentado pela validação de desenvolvimento.

Para liberar ainda faltam: generalização e cobertura suficientes; comparação
pareada contra o sistema atual e histórico sem piora de segurança; validação
no runtime real em sombra; integração gradual de baixo risco com governança,
veto, resolução e receipts externos, desligamento e retorno ao modelo anterior.
O treino acima **não habilita o candidato na Laylay**.

Testes focados: **172 passaram** (alinhamento, vínculos, exportação, isolamento
das dobras, proibições e BIO). Regressão ampliada: **768 passaram em 61,94 s**
(`tests/test_neural*.py` + P0 autorização/modalidade e isolamento de contexto);
não é a suíte global nem caos completo. Compilação passou; recarga do artefato manteve
as previsões. Não houve lançamento da assistente nem prova no runtime real.
Configuração segue `shadow` com o modelo v27 anterior, SHA256
`caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf` inalterado.
Produção operacional, executores, dados pessoais e reservas preservados.
Base `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, `main`, worktree suja
preservada; nenhum commit criado.

## Histórico: reserva diversa e critérios de liberação — 2026-09-07

Criados `datasets/reserva_relacional_independente_v1.json` e
`auditar_reserva_independente.py`. A reserva contém **32 casos manuais**, em
música, aplicativos, arquivos, IoT e navegador, com formulações variadas de
correção, recusa, relato, escolha com exclusão, nome literal, preservação de
estado e referência dependente de contexto. Não é grade de substituição de
nomes, nem uma amostra de uso real de Pedro. A autoria dos rótulos foi assistida
por IA; eles ainda precisam de revisão semântica e alinhamento.

A auditoria reutiliza o validador de spans/ações, o catálogo real e o medidor
canônico de leakage. Congelou a reserva e o protocolo **antes de comparar**,
sem selecionar frases pelos resultados, reescrever rótulos ou relaxar o limiar.
Resultado: **8.258 registros conhecidos × 32 casos**, zero famílias de rótulo
compartilhadas, zero duplicatas normalizadas exatas e zero pares quase
duplicados no limiar original 0,9. GREEN lexical, não aprovação operacional.
Famílias com ids diferentes e distância lexical não provam independência
semântica, nem garantem ausência de mecanismos conhecidos.

O inventário cobre todos os JSONL encontrados em `neural/datasets`, os
`lote_negacao.jsonl` dos experimentos, DEV/Frozen, o piloto relacional anterior,
a bateria linguística, os controles de aspas, as quatro partições relacionais
e a grade booleana de escopo incluindo suas reservas. O manifesto enumera cada
arquivo com hash e quantidade; registros repetidos entre experimentos não são
contados como exemplos únicos. É o corpus disponível nessas fontes, **não todos
os logs/conversas ou possíveis materiais não inventariados**. Fonte obrigatória
ausente/corrompida aborta; não há aprovação silenciosa com corpus parcial.

Artefatos congelados:
`memoria/neural/experimentos/reserva_relacional_independente_v1_20260907/`
(`reserva_congelada.json`, `protocolo.json`, `auditoria.json`). Os nomes dos
artefatos não significam que independência semântica já foi certificada.
As reservas anteriores, inclusive os 108 pares semelhantes da prova de troca
de nomes, foram preservadas como controles distintos.

Os offsets desta reserva referem-se à **fonte manual integral**. Validá-los em
um contrato sintético não prova segmentação real: ainda não houve classificação
canônica, alinhamento v2, inferência neural ou uso para treino. Referência
contextual não foi substituída por um alvo inventado. O conjunto está protegido
com treino, execução e promoção proibidos. Nenhum destes 32 casos deve ser
incorporado ao treino após observar resultados de um candidato.

### O que falta para liberar a rede

| Fronteira | Estado atual / evidência necessária |
| --- | --- |
| Avaliação independente | Reserva diversa congelada e GREEN lexical; falta revisar rótulos e alinhar as menções com segmentos reais, sem usar scores para corrigir o esperado. 32 casos não cobrem todas as intenções/riscos. |
| Modelo de relações | Contrato v2 e medidor existem. O modelo configurado ainda prevê intenção/ação/negação booleana, sem inferir essas relações de menções. Falta implementar/treinar o candidato e sua saída no contrato, sem entregar rótulos como features. |
| Superioridade comprovada | Comparação pareada fora do treino contra legado e modelo estável, por intenção/ação e família. Ganho de entendimento sem piorar falsos comandos, recusas, alvo correto ou histórico; medir latência/OOD e manter as fatias difíceis no denominador. |
| Uso real em sombra | Rodar candidato integrado nos mesmos turnos da Laylay, mantendo decisão operacional atual; verificar divergências, contexto, referências, recusas, falhas e receipts reais. Não confundir score ou intenção com efeito. |
| Caminho operacional controlado | Reutilizar governança por intenção/risco, árbitro, resolvedor e executor. Demonstrar veto/ambiguidade/erro, receipt antes de confirmação e nenhuma ação adicional em falha. Só então habilitar uma lista inicial de baixo risco, com desligamento e retorno ao modelo anterior. |
| Substituição do legado | Ampliar domínio por domínio após prova real. Remover regras redundantes somente quando houver cobertura e equivalência/superioridade demonstradas; manter os contratos de segurança externos ao modelo. |

Inspeção atual: `orquestrador_turno_runtime.observar_especialista_neural_turno`
anexa telemetria; `normalizar_previsao_neural` força observação sem autorização.
`governanca.avaliar_roteamento_neural` já define guardas de desligamento, veto,
intenção, risco, OOD e confiança, mas a busca por chamadas encontra definição,
exportação e testes, não ligação desse gate ao caminho de execução em produção.
Não deve ser substituído por outro gate privado. `promocao.avaliar_promocao`
compara artefatos; passar nele não prova superioridade contra o legado nem
autoriza efeitos. Mudar `shadow` para `candidate` sozinho não libera a rede.

Portanto, a rede **ainda não está pronta para assumir comandos em geral**.
Os verdes recentes são de contratos, dados e ferramentas; não houve treino de
um modelo relacional. Não há porcentagem honesta de prontidão ou quantidade
fixa de exemplos que substitua as provas acima. Próxima etapa concreta: revisar
e alinhar esta reserva sem inferência neural, preservá-la fora do treino e
implementar a supervisão/saída do candidato com os dados de desenvolvimento.

Testes novos: **40 passaram**, incluindo os 32 exemplos, proibições,
congelamento anterior à comparação, destino preservado, corpus incompleto,
id duplicado e span incorreto. O teste de fluxo usa corpus mínimo com o medidor
real; a auditoria de 8.258 registros foi executada separadamente nas fontes
inventariadas. Produção, modelo e configuração permanecem intactos.

Regressão ampliada (`tests/test_neural*.py` + P0 autorização/modalidade e
isolamento de contexto): **620 testes passaram em 67,28 s**. Compilação dos
dois arquivos Python novos passou; hash da reserva congelada confirmado.
O inventário registra 41 fontes. Modelo mantém SHA256
`caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf`, modo `shadow`.
Base: `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, `main`, worktree suja
preservada. Nenhum treino, efeito físico, lançamento da assistente ou commit.

## Vínculos explícitos entre segmentos — 2026-09-07

O contrato de anotação aceita agora **v1 e v2**. Na v2, cada menção informa
`segmento`, `inicio`, `fim` e `texto`; a ação continua pertencendo explicitamente
ao segmento em cuja lista foi anotada. Isso representa, por exemplo, uma ação
no segmento 1 cujo alvo excluído está no segmento 0. Nenhum texto é colado,
nenhuma negação é removida e nenhuma ligação é inferida pelo validador.

A v1 continua estrita e compatível: seus exemplos antigos não são migrados
automaticamente. A v2 permite segmentos com lista de ações vazia, mantendo-os
no snapshot completo; vazio não concede autoridade nem permite omitir um
segmento da anotação. A menção deve apontar a uma origem existente e o span
precisa corresponder exatamente ao texto nessa origem. Referência obsoleta,
origem ausente/ambígua no plano, sobreposição na mesma ação e campos de
autorização são rejeitados. Os contratos semânticos de pedido/recusa/relato
e as proibições de treino, efeito e promoção permanecem compartilhados.

O medidor `avaliacao_escopo.py` foi atualizado para incluir o segmento de origem
na identidade de uma menção, além do segmento dono da ação. Uma ação ligada ao
segmento errado conta como ação esperada ausente e ação extra; solicitar o alvo
excluído em outro segmento continua sendo erro específico de alvo. O callback
segue recebendo somente texto/índices, sem ligações ou rótulos esperados; seu
formato de saída deve corresponder à versão do conjunto avaliado.

### Prova do contrato e revisão da grade conhecida

Antes do candidato, seis testes da v2 (três domínios, com/sem aspas) chegaram
ao validador e ficaram RED porque essa versão não era suportada. Após a
mudança, ficaram GREEN, juntamente com os testes antigos da v1. Os seis
regressivos que provam o limite da v1 continuam válidos: não foram enfraquecidos
para aceitar dados de outro formato.

`revisar_vinculos_segmentos.py` materializa um **plano manual de alinhamento**,
nunca uma previsão neural. Para os 12 casos conhecidos, o plano declara que a
ação pertence ao segundo trecho e que o primeiro contém a restrição. Para os
84 casos que não mudam de segmentação, o plano preserva o único trecho.
Todos os intervalos e donos são registrados no novo artefato.

A conversão exige correspondência literal dos intervalos com o texto canônico,
valida os rótulos da fonte e só recalcula offsets por subtração. Não busca alvos
por nome, não usa correspondência aproximada e não escolhe o dono da ação.
Se uma menção cruza uma fronteira, um dono está ausente ou o plano descartaria
conteúdo lexical, aborta. Só separadores de pontuação/espaço podem ficar entre
os intervalos. É ferramenta para essa revisão explícita de dados de fonte
única, não um mecanismo geral de compreensão ou de resolução operacional.

Resultado: **96/96 exemplos de desenvolvimento alinhados na v2**, com os 12
vínculos revisados e sem alterar textos ou papéis esperados. Isso é GREEN de
alinhamento com classificador/detector reais, não 96 acertos da rede nem prova
do runtime completo. Os 216 exemplos congelados, suas partições e relatórios
históricos permanecem intactos. Reservas não foram migradas ou classificadas.

Artefato: `resultados_testes/revisao_vinculos_segmentos_20260907.json`.
Produção não alterada: apenas contrato/medidor experimentais, ferramenta de
revisão, testes e documentação. Nenhum treino, lançamento da assistente,
efeito físico ou commit. Base Git permanece
`a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, `main`, worktree suja.

Testes focados novos: **24 passaram**. Cobrem ligação entre segmentos, v1
preservada pela regressão vizinha, veto preservado, origem inexistente,
offset inválido, snapshot obsoleto, cobertura incompleta, dono incorreto,
pedido do alvo rejeitado, ausência de rótulos na entrada e conversão que
descartaria conteúdo. Predições-oráculo continuam restritas aos testes do
medidor; nenhum modelo ganhou resultado de acurácia nesta etapa.

Regressão ampliada (`tests/test_neural*.py` + P0 autorização/modalidade e
isolamento de contexto): **580 testes passaram em 70,57 s**. Compilação dos
quatro arquivos Python alterados/criados passou; hashes das quatro partições
congeladas continuam iguais. Modelo mantém SHA256
`caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf` e modo `shadow`.

Próxima fronteira: a reserva independente. Ao localizar os 108 pares quase
duplicados do relatório anterior, **todos pertencem à reserva de entidades**,
que repete moldes e troca nomes deliberadamente. Ela pode continuar como
controle de transferência de nomes, mas não deve ser chamada de avaliação
linguisticamente independente. Preservar esse controle, preparar uma reserva
mais diversa e auditar contra o histórico completo, sem relaxar o limiar.
O gate lexical anterior segue RED; o alinhamento resolvido não o compensa.

## Grade ampliada e medidor ação/alvo — 2026-09-07

Implementados `avaliacao_escopo.py`,
`datasets/gerar_escopo_relacional_v2.py` e `auditar_grade_relacional.py`.
São ferramentas offline. Modelo, classificador canônico, executor, rótulos
booleanos históricos e configuração de produção não foram alterados.
Base: `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, `main`, worktree suja.

### Medidor pronto, modelo ainda não avaliado

O medidor compara relações por `(índice do segmento, intent, action)`, com
papéis de alvos em spans exatos. Mede ações ausentes/extras, ato e resolução,
alvos solicitados/excluídos/mencionados corretos, ausentes e extras, pedidos
perdidos/inventados, alvo excluído previsto como solicitado e menção prevista
como pedido. Assim, acertar `MUSIC_SEARCH` mas tocar o alvo rejeitado não conta
como acerto completo. A mesma menção em ações diferentes não é confundida.

Antes da primeira inferência, todos os sidecars esperados passam pelo
validador existente. O callback recebe **somente texto de entrada e segmentos
com índice/texto**: não recebe rótulos, spans esperados, variantes esperadas,
decisão canônica, grupos, partição ou id do caso. Erros de formato/inferência
permanecem no denominador; uma exceção não vira recusa correta. Saída vazia
significa ações ausentes, não descarte de um caso. Texto privado de exceções
não é publicado. Ordem das ações não afeta o resultado.

O resultado mede correspondência exata; não resolve aliases nem equivalência
semântica de spans parcialmente coincidentes. Previsão estruturalmente inválida
falha como caso inteiro; os contadores específicos de erros de alvo não devem
ser lidos isoladamente do contador de falhas de inferência. Nenhum adaptador
finge que a cabeça booleana antiga prevê relações. Preditores-oráculo e
preditores errados existem **somente nos testes do medidor**, não são resultados
da Laylay, de um candidato neural ou de superioridade sobre o legado.

### Grade congelada antes de inferência

**216 exemplos**: 3 domínios (apps, música, arquivos), 3 pares de entidades
sintéticas, 3 famílias de moldes, 4 mecanismos (correção, recusa, alternativa,
relato) e versões com/sem aspas. Alvos de música/arquivo incluem “não” no nome;
`chamado/chamada` explicita a referência literal. Os 108 pares de aspas ficam
na mesma partição e mantêm os papéis. Rótulos vêm dos moldes manuais, não de
scores ou da classificação canônica; ainda exigem revisão semântica.

| Partição desta rodada | Casos |
| --- | ---: |
| Desenvolvimento | 96 |
| Reserva de entidades | 48 |
| Reserva de construções | 48 |
| Reserva de ambas | 24 |

Os arquivos e seus hashes foram gravados em
`memoria/neural/experimentos/escopo_relacional_v2_20260907/`, antes da auditoria.
Todos continuam com treino proibido. Essas reservas são relativas a esta
grade, **não uma alegação de novidade frente a todo o histórico do projeto**.
O piloto anterior de 16 casos continua conhecido e intacto.

Auditoria canônica lexical DEV × reservas (limiar original 0,9): zero famílias
de contraste compartilhadas, zero duplicatas normalizadas exatas e **108 pares
quase duplicados**. Portanto, o gate lexical está RED. Trocar entidades mantendo
moldes semelhantes pode ser útil como diagnóstico controlado, mas não é prova
de generalização independente. Não mudamos o limiar nem removemos pares para
melhorar esse resultado. Ainda falta auditoria contra todo o histórico e uma
reserva linguisticamente mais diversa. Nenhum classificador foi aplicado às
reservas; houve apenas geração/validação estrutural e comparação lexical.

### Primeira fronteira RED: vínculo entre segmentos

A auditoria estrita `auditar_escopo_manual` abortou no primeiro contraste
anteposto. O diagnóstico da grade preservou todos os casos: **84/96 alinhados,
12/96 incompatíveis**, não um subconjunto avaliado como 84/84. São quatro casos
por domínio; seis com aspas e seis sem, todos na construção `em vez de B, faça A`.

O classificador/detector reais separam esse texto em dois segmentos:
`em vez de B` e `faça A`. O alvo excluído está no primeiro; o solicitado, no
segundo. O texto não foi perdido, mas o contrato experimental v1 supunha
ambos dentro de um único segmento. Não se deve adaptar os offsets, eliminar
o primeiro segmento ou remover a segmentação canônica para fazê-lo passar.

Falsificações: não é específico de aspas, de nomes de arquivos ou de uma
entidade; controles dos três domínios reproduzem a mesma fronteira. Não é
falha de treino, pois nenhum modelo foi ajustado ou consultado. Isso demonstra
um limite da **representação experimental**, não um bug de efeito no runtime
completo. Seis regressivos com componentes reais protegem a rejeição atual e
a conservação dos dois trechos; não representam solução dessa limitação.

Próxima fronteira: representar relações entre **ação proposta e menções que
podem estar em outro segmento**, com referência explícita de origem/destino.
Preservar o dono canônico da segmentação, as recusas independentes, o vínculo
ação/alvo e a ausência de autorização. Só depois revisar o alinhamento e a
diversidade das reservas antes de qualquer treino. Não consumir o conjunto
parcial, não alterar rótulos históricos, nem promover por esses testes.

Artefato: `resultados_testes/auditoria_grade_relacional_v2_20260907.json`.
Inclui os 12 casos esperados/observados, ids dos alinhados, pares de similaridade
e hashes das fontes principais. O destino da auditoria estrita abortada não
foi criado. Testes focados do medidor/grade: **22 passaram**; isso comprova
as guardas e as métricas, não GREEN estatístico/operacional da rede.

Regressão ampliada (`tests/test_neural*.py` + P0 autorização/modalidade e
isolamento de contexto): **556 testes passaram em 80,78 s**. Compilação dos
cinco arquivos Python novos passou. Modelo configurado mantém SHA256
`caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf`, `shadow`
mantido. Nenhum treino, execução física, inicialização da assistente, alteração
de produção ou commit nesta etapa. As duas fronteiras RED acima seguem abertas.

## Piloto de anotação relacional, sem treino — 2026-09-07

Implementado `anotacao_escopo.py`: contrato experimental **offline**, separado
do schema booleano e não conectado ao roteador. Não é um interpretador novo,
não resolve entidades e não cria permissões. Recebe a leitura canônica já
produzida e uma anotação manual independente sobre seus segmentos.

Inventário reutilizado: `LeituraTurnoDict`, segmentos de
`classificar_modalidade_turno`, detector `texto_tem_comando_explicito` e
manifesto `catalogo_variantes_v0.json` validado por
`carregar_manifesto_variantes` com `intents_registradas`. Não foram alterados
o classificador, o catálogo, o modelo neural, a composição ou o executor.
Base continua `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, `main`, worktree suja.

Cada ação anotada possui:

- variante `intent/action` do catálogo existente;
- ato esperado: pedido, recusa, relato, preservação ou indeterminado;
- alvos solicitados, excluídos e apenas mencionados, em spans `[inicio, fim)`;
- resolução ainda necessária: explícito no texto, contextual, escolha de
  alternativa, ausente ou não aplicável a um pedido.

**Explícito no texto não significa alvo localizado no mundo.** Os offsets
apontam ao texto do segmento canônico, não à fala bruta: a fronteira existente
pode normalizar/corrigir sua grafia. Guardamos ambos no relatório, sem inventar
um mapeamento de offsets entre eles. Um hash captura texto, índices e decisões
relevantes; mudanças invalidam uma anotação já vinculada. Timestamp não muda
esse hash. A função não resegmenta, não completa alvo e não repara anotações.

Guarda de coerência: cobertura de todos os segmentos; spans exatos; nenhuma
sobreposição de papéis na mesma ação; ausência de alvo solicitado em uma
recusa; relato não cria exclusão operacional. Repetições da mesma variante no
mesmo segmento precisam ser consolidadas. Contradições não representáveis
devem ser revistas manualmente, não convertidas em permissão. Restrição de
fechar A pode coexistir com pedido de abrir A, pois são ações diferentes.
O validador não determina se dois nomes diferentes são aliases do mesmo alvo.

`datasets/escopo_relacional_piloto_v1.json` contém **16 casos manuais conhecidos**
de música, aplicativos, arquivos e preservação de estado: recusas, correções,
alternativas, nome com “não”, relato, referência contextual, alvo ausente,
ambiguidade e ações distintas. Não é expansão de treino nem reserva inédita.
Os rótulos não vêm do classificador: por exemplo, o pedido anotado em
`abra o opera, não o firefox` coexiste com o veto canônico observado. A anotação
não remove esse veto nem prova que a ação deva executar sem outras validações.

`auditar_escopo_manual.py` alinha o piloto com o classificador/detector reais
sem contexto e o catálogo real, grava as duas leituras e hashes das fontes
principais. A rodada confirmou **16/16 alinhamentos**, não 16 acertos neurais.
O hash é vinculado à observação desta rodada; os textos, spans e rótulos
manuais permanecem fixos, e divergência de segmentação aborta. O destino usa
criação exclusiva para preservar relatórios anteriores.

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.auditar_escopo_manual --saida resultados_testes/auditoria_escopo_manual_20260907.json
```

Esse destino já existe; uma nova rodada precisa de outro nome. Artefato:
`resultados_testes/auditoria_escopo_manual_20260907.json`.
Todos os resultados proíbem treino, execução e promoção; o schema de treino
antigo rejeita esse sidecar. Nenhum `negated` histórico foi reescrito.

Validação focada: **37 testes passaram**. Cobrem os 16 casos com componentes
reais, ausência de mutação, injeção de autorização, ação fora do catálogo,
referência obsoleta, sobreposição, ambiguidade, isolamento entre ações e
cobertura parcial de um turno realmente segmentado em dois. São provas do
contrato de anotação, não de compreensão aprendida ou da composição completa.

Regressão local ampliada: todos os `tests/test_neural*.py`, mais
`test_p0_autorizacao_modalidade.py` e `test_p0_isolamento_contexto.py`:
**534 testes passaram em 140,97 s**. Compilação dos três arquivos Python novos
passou. Modelo configurado mantém SHA256
`caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf`, modo
`shadow`. Nenhum modelo treinado, assistente aberta, efeito físico, alteração
de produção ou commit nesta etapa.

Próxima fronteira: preparar supervisão e avaliação **relativas à proposta**,
com papel do alvo separado do ato, sem fornecer o rótulo esperado como feature.
Antes de treinar, ampliar os contrastes anotados e reservar famílias/entidades
realmente novas. Manter o histórico booleano como regressão separada; o piloto
conhecido não serve para aprovar promoção. A anotação manual ainda precisa de
revisão semântica: validação estrutural não atesta que cada rótulo está certo.

## Reprodução das regressões e contrato de escopo — 2026-09-07

`diagnostico_regressoes_regional.py` reproduziu os quatro folds por construção
da rodada regional, com os mesmos dados e partições. O controle usa somente
histórico no fit; o regional usa histórico + lote novo, sempre fora do fold
avaliado. Não houve novo candidato, modelo salvo, mudança de rótulos ou
promoção. Baseline Git: `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, branch
`main`, worktree suja (inclusive `neural/` não rastreado); HEAD não representa
sozinho o código experimental. Fontes, dados e modelo são verificados por hash.

Foram reproduzidos **65 regressões e 17 ganhos históricos**, além das métricas
agregadas históricas/novas do relatório original. O novo artefato guarda as
previsões fora do treino por índice e as contribuições das duas cabeças para
cada mudança histórica. Os índices se referem à lista filtrada pela cabeça de
negação, não a turnos do runtime. O relatório original não guardava todas as
previsões individuais: a igualdade demonstrada é de partições, métricas e
contagens pareadas, não de pesos antigos bit a bit.

Das 65 regressões, 36 ativam apenas o indicador canônico de exclusão, 11 apenas
o de negação explícita e 18 nenhum dos dois. Esses indicadores descrevem
pistas de texto, **não são uma classificação semântica dos 65 casos**. A troca
regional também remove caracteres e muda n-gramas; a contagem não isola qual
canal causou cada erro. Recusas claras como `nunca toque ...` e `evite procurar
na web ...` continuam sendo regressões legítimas a preservar.

### Primeira fronteira conceitual a esclarecer

O gerador musical v4 rotula `coloca qualquer uma menos X` e `troca X por outra
música` como `MUSIC_SEARCH/search`, `is_command=True`, `negated=True`.
Já a grade de escopo v2 rotula `reproduza A, não B` como `negated=False`, com
supervisão somente da cabeça de negação. Não são frases idênticas com rótulos
contraditórios: a primeira não dá um alvo positivo exato; a segunda dá.
O veto histórico pode proteger contra buscar justamente o alvo excluído.

| Fala ilustrativa | Pedido e restrição que precisam permanecer distintos |
| --- | --- |
| Não toque A | Vetar tocar A; não inferir pedido de outra faixa |
| Toque A, não B | Pedido de A e exclusão de B |
| Toque qualquer outra, menos A | Pedido com escolha ainda necessária e exclusão de A |
| Mantenha esta aba aberta | Preservação do estado; não autoriza fechar a aba |
| Toque a faixa chamada Não Volte | A palavra do título não é veto operacional |

O schema neural atual guarda um booleano `negated`, sem vínculo explícito com
o alvo excluído. O runtime já reutiliza segmentos canônicos: quando há mais de
um, prevê por segmento e conserva os não vetados; não cancela necessariamente
o turno inteiro. Dentro de cada previsão, porém, `_comando_executavel` filtra
`negated=True`. Essa seleção observacional **não substitui autorização nem
executor**. A cabeça recebe texto, não uma proposta estruturada com alvo para
avaliar seu escopo. Isso é uma limitação comprovada do contrato representado;
não prova que explica sozinho as 65 regressões ou um efeito errado ao vivo.

Próxima etapa: especificar uma anotação experimental ligada a **segmento,
ação proposta, alvo positivo, alvos excluídos e necessidade de resolução**,
reutilizando os contratos de turno existentes. Uma restrição deve valer sobre
a proposta correspondente, não ser convertida em permissão geral. Antes de
qualquer integração, testar pedido/recusa/correção/nome literal, ambiguidade e
alvo ausente em música, arquivos, aplicativos e estados. Alvo não resolvido
continua sem efeito; receipt continua necessário para confirmar sucesso.

Não relabelar os exemplos históricos, ajustar o limiar ou remover a guarda
para melhorar o placar. Manter os relatórios históricos intactos, avaliar o
eventual contrato novo separadamente e preservar as recusas inequívocas.
Os controles de aspas já observados permanecem fora do treino.

Artefato reproduzido:
`resultados_testes/diagnostico_regressoes_regional_20260906.json`.
O script recusa sobrescrita e fontes com hash divergente; testes próprios
cobrem essas guardas antes do carregamento de dados/modelos. Não foi aberta a
Laylay nem testado efeito físico nesta etapa. Configuração permanece `shadow`.

Validação local: **3/3** guardas novas; seleção de todos os arquivos
`tests/test_neural*.py` mais `test_p0_autorizacao_modalidade.py` e
`test_p0_isolamento_contexto.py`: **497 testes passaram em 96,37 s**.
Compilação dos dois arquivos Python novos passou. Modelo configurado manteve
SHA256 `caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf`.
Produção não alterada; nenhum commit. Isso é GREEN de regressão local, não
aprovação do candidato nem validação da assistente ao vivo.

## Controles pareados de aspas e primeiro treino regional — 2026-09-06

Implementados `datasets/gerar_controles_aspas_v1.py` e
`experimento_regioes_aspas.py`. São **96 controles de avaliação**, organizados
em 48 pares: aplicativos, músicas e arquivos; dois pares de nomes sintéticos;
duas molduras; pedido, correção, recusa e relato. Cada par difere apenas nas
aspas, sem mudar intenção/rótulo/grupo. Nomes não atestam recursos instalados.
Música/arquivo incluem “não” no nome e usam `chamado/chamada` para explicitar
o nome também na versão sem aspas. Não representam todas as ambiguidades reais.

72 exemplos supervisionam somente a cabeça de negação. Os 24 relatos, como
`ontem ela disse para não ...`, supervisionam somente comando negativo:
o `negated=False` obrigatório no schema não é usado como alvo da negação.
As variantes compartilham família e grupo; a normalização canônica remove
aspas e torna irmãos duplicatas intencionais dentro do mesmo conjunto.
Não dividir irmãos entre fit e avaliação.

Controles e protocolo foram gravados **antes de auditoria e fit**, sem
escolher rótulos pelos scores. Auditoria canônica contra os 4.210 exemplos de
treino (3.922 históricos + 288 novos): zero famílias compartilhadas, zero
duplicatas exatas normalizadas e zero quase duplicatas no limiar padrão 0,9.
Não interpretar isso como prova de independência semântica completa. Nenhum
dos 96 controles entrou no fit; agora que seus resultados foram observados,
eles são diagnóstico conhecido para qualquer próxima rodada.

Uma única cabeça regional foi ajustada com forma + conteúdo regional,
classificador clonado, peso 1 e limiar zero. Não reutiliza coeficientes antigos
com um extrator novo: a cabeça é retreinada. O candidato troca representação
lexical/caracteres/indicadores por regiões; logo, o experimento mede essa
arquitetura conjunta, não isola a contribuição de cada mudança. O modelo
configurado não foi alterado. Uma cabeça lexical v2 é reconstruída nos mesmos
dados como comparação adicional nos controles.

| Controles de negação | Configurada | Lexical v2 | Regional |
| --- | ---: | ---: | ---: |
| Sem aspas: acertos / 36 | 16 | 18 | 18 |
| Com aspas: acertos / 36 | 16 | 20 | 30 |
| Pares com decisão diferente / 36 | 0 | 2 | 12 |

Nesses controles, todos os erros de negação são falsos cancelamentos; não há
recusas perdidas. Igualdade entre pares não significa correção: o modelo
configurado repete os mesmos erros com e sem aspas. Nos 24 relatos nenhum
modelo propôs pedido operacional nem classificou comando positivo; essa
cabeça de comando não foi treinada nesta etapa.

CV com as mesmas divisões verificadas da referência:

| Fatia | Controle histórico | Regional |
| --- | ---: | ---: |
| Construção / novos | 144/288 | 288/288 |
| Construção / histórico | 3315/3340 | 3267/3340 |
| Entidade / novos | 144/288 | 282/288 |
| Entidade / histórico | 3321/3340 | 3279/3340 |

No histórico por construção: 17 ganhos e **65 regressões pareadas**, recusas
perdidas 18 → 59, falsas negações 7 → 14. Por entidade: 12 ganhos e 54
regressões, recusas perdidas 11 → 55. Frozen cai de 24/24 para 23/24 (falso
cancelamento em `frozen_iot_ligar_b`). Portanto, **candidato reprovado** apesar
dos 288/288: ele não supera o histórico com segurança.

Na cabeça final, três correções originais passam a `negated=False` (volume,
Opera/Firefox e arquivo); Brisa/Aurora continua `True`. Isso mede apenas
negação, não execução correta, resolução do alvo ou resposta da Laylay real.

Conclusão: há dependência observada de aspas em 12 pares semanticamente
equivalentes. Isso confirma uma limitação de transferência da representação;
não prova, sozinho, que todo ganho seja causado por identificar o lote através
das aspas. A substituição também perde proteções históricas em famílias de
recusa/exclusão. Próxima fronteira: preservar pistas de recusa em contextos
regionais e estudar os spans de nomes sem aspas; manter esta bateria fora do
treino e acrescentar futuramente uma avaliação realmente nova. Não ajustar
pesos pelos 96 controles nem promover os três exemplos históricos corrigidos.

Artefatos: `memoria/neural/experimentos/regioes_controles_aspas_v1_20260906/`
(`protocolo.json`, `auditoria.json`, `relatorio.json`, cabeça não promovida).
Protocolo contém os textos e metadados dos controles; relatório inclui todas
as previsões e métricas separadas. Seleção neural/P0: **421 testes passaram em
60,28 s**; compilação passou. Produção, autorização, executor e configuração
intocados, `shadow` mantido. Modelo verificado por SHA256
`caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf`.
Nenhum commit, lançamento da assistente ou teste físico. GREEN de testes não
equivale à aprovação estatística ou operacional desse candidato.

## Regiões sem perda e auditoria de aspas — 2026-09-06

Implementada a base experimental `representacao_regioes_texto.py`, **sem
treinar uma nova cabeça** nem substituir extratores dos modelos salvos.
Ela reutiliza `mapear_pares_aspas_globais` e divide a entrada em spans
contíguos de texto exterior/citado. Espaços, acentos, delimitadores e offsets
são preservados; concatenar as regiões reconstrói exatamente a entrada.
Pares aninhados permanecem no conteúdo da citação externa. Aspas incoerentes
mantêm todo o texto como exterior, com a incoerência explícita.

Dois canais experimentais não ajustados:

- forma: reutiliza o canal estrutural local anterior;
- conteúdo regional: palavras e pontuação em sequências de 1–4 tokens, com
  namespaces de exterior/citado e bordas de região. Não cria sequências
  entre duas citações distintas. Metadados são serializados sem colisão
  com palavras digitadas pelo usuário.

Isso preserva a forma externa ao mudar um título, mas mantém seu conteúdo
separado e disponível. A colisão anterior de `"abra o Opera"` e
`"não abra o Opera"` continua existindo no canal de forma, porém não mais
nas pistas de conteúdo regional. Uma negação citada recebe namespace
distinto de uma negação exterior. **Isso não é rótulo de escopo aprendido**:
exterior não significa instrução, citação não significa alvo e nenhuma região
concede permissão. Separar regiões também não garante invariância da decisão
final, pois coeficientes futuros ainda podem aprender pistas espúrias.

Inventário: `retrato_turno.extrair_entidade_explicita` trata categorias e
referências conversacionais, sem contrato geral de spans de alvo; os
extratores de arquivos/playlists são específicos de domínio. Não foram usados
como parser universal nem duplicados. `abre o Opera, não o Firefox` permanece
inteiro como exterior, sem adivinhar que Opera/Firefox são entidades. Assim,
esta etapa **ainda não resolve** a identidade de alvos sem aspas. Para conectar
um resolvedor no futuro será necessário um contrato explícito de offsets e
proveniência; uma previsão não poderá inventar spans ou autorizar execução.

Auditoria somente leitura usando o histórico reconstruído e seu hash:

| Base | Textos | Com região citada | Aspas incoerentes |
| --- | ---: | ---: | ---: |
| Histórico | 3922 | 0 | 0 |
| Novo treino v2 | 288 | 144 | 0 |
| Reservas v2 | 288 | 144 | 0 |

Nos **4498 textos**, reconstrução exata preservada. A ausência de citações
reconhecidas no histórico mostra diferença de distribuição: a presença de
aspas pode identificar o lote novo. Isso é risco de atalho, não prova de que
um modelo já o aprendeu. Não usar uma melhora concentrada em citações como
evidência de generalização a comandos naturais sem aspas. Próxima etapa:
preparar controles pareados com/sem aspas e recusa/correção/discurso citado,
mantendo variantes da mesma origem no mesmo grupo de validação. Esses
controles devem anteceder um treino isolado; não alterar os rótulos históricos.

Testes específicos: preservação de todos os caracteres e offsets, citações
aninhadas/incoerentes, separação das negações, conteúdo antes colapsado,
ausência de resolução inventada, serialização e entradas inválidas. Uma
asserção inicial comparou `fit_transform` com `transform` após serialização
e encontrou diferença de arredondamento de 5,55e-17; foi corrigida para
comparar `transform` antes/depois da serialização com igualdade exata.
Não foi um RED de interpretação da Laylay. Seleção focada: 37 testes verdes.
Seleção ampla neural/P0: **415 testes passaram em 58,44 s**. Compilação
também passou; nenhum desses resultados mede a acurácia de uma nova cabeça.

Produção, modelo configurado, limiares, executor e autorização intocados;
modo `shadow` mantido. Somente representação e testes novos, sem treino
de classificador, commit, lançamento da assistente ou efeito físico.

## Ablação de canais com controles de recusa — 2026-09-06

`diagnostico_ablacao_canais.py` mediu o candidato local **já ajustado**, sem
fit, mudanças nos pesos ou normalização adicional. Primeiro verifica classes
booleanas, dimensões, finitude, soma das contribuições e equivalência com
`predict`. Depois zera cada canal numa cópia esparsa do vetor. A decisão
contrafactual é verificada contra a subtração algébrica das contribuições;
erro máximo de reconstrução observado: `1,33e-14`.

Condições diagnósticas fixas: integral, sem palavras, sem caracteres e
somente escopo local. Não houve busca por pesos de combinação ou ajuste de
limiar. Os pesos antigos dependem dos canais originais; ablação **não** é
modelo retreinado nem evidência de que uma arquitetura futura falharia igual.

| Conjunto / medida | Integral | Sem palavras | Sem caracteres | Só escopo |
| --- | ---: | ---: | ---: | ---: |
| Contrastes conhecidos: acertos / 20 | 12 | 12 | 10 | 10 |
| Recusas perdidas nesses contrastes / 10 | 0 | 0 | 10 | 10 |
| Negações falsas nesses contrastes / 10 | 8 | 8 | 0 | 0 |
| Frozen: acertos / 24 | 24 | 24 | 20 | 18 |
| Reserva entidades: acertos / 96 | 91 | 81 | 58 | 50 |
| Reserva construções: acertos / 144 | 144 | 138 | 72 | 72 |
| Reserva ambas: acertos / 48 | 42 | 40 | 26 | 24 |

Contrastes incluem as quatro correções originais, recusas diretas/modais,
música e arquivo com “não” literal, nomes sem aspas, IoT e estado de app.
Foram escolhidos para diagnóstico, não como avaliação inédita. Frozen e v2
também são conhecidos. Nenhum conjunto entrou em fit nesta etapa.

Exemplo causal, mesmo classificador, apenas o vetor de caracteres zerado:

- `abre o Opera, não o Firefox`: score `+6,14157 → -2,58696`, corrige o rótulo;
- `não abra o Opera`: score `+8,62474 → -0,45842`, perde uma recusa verdadeira.

Portanto, fica falsificada a solução de simplesmente desligar caracteres
com os pesos atuais. Desligar só palavras não resolve os oito falsos
cancelamentos nos contrastes e piora as reservas. O canal estrutural adicional
foi aprendido em conjunto com os legados; não se sustenta como substituto
isolado com esse intercepto e esses coeficientes.

Outra limitação do extrator foi registrada: `"abra o Opera"` e
`"não abra o Opera"`, quando são citações inteiras, geram vetores idênticos
**no canal estrutural**, pois ambos viram um trecho citado. Isso não prova
bug de autorização (ambas podem ser discurso citado) nem colisão no modelo
completo, cujos canais lexicais ainda leem o conteúdo. Prova que esse canal
não pode ser tratado como representação semântica completa e autossuficiente.

Próxima hipótese: preservar separadamente a moldura da ação e o conteúdo
literal, sem decidir que qualquer citação é alvo ou que qualquer “não” cancela
tudo. Uma experiência de desacoplamento deve ser retreinada de forma isolada
e avaliar recusa explícita, referência/identidade, correção e discurso citado.
O conjunto original continua como controle; não promover a ablação nem
transformar `negated=False` em permissão. Antes de novo candidato, delimitar
como o mesmo mecanismo mantém informação suficiente em frases sem aspas.

Evidência: `resultados_testes/diagnostico_ablacao_canais_20260906.json`, com
scores por variante, itens, contribuições, métricas, hashes e limites. A
ferramenta recusa sobrescrever saída; cabeça preservada por SHA256. Na primeira
execução, a chamada ao leitor de Frozen omitiu o catálogo obrigatório e
abortou antes de gerar artefato; corrigida para reutilizar `intents_registradas`.
Essa falha do runner não foi interpretada como RED do classificador.

Produção, modelo configurado, autorização, executor e modo `shadow` intocados;
sem novo treino, commit, lançamento da assistente ou efeito físico nesta etapa.
Validação: **396 testes passaram em 57,62 s** na seleção neural/P0, incluindo
sete testes da ablação; compilação passou. Esse GREEN valida ferramentas e
contratos locais, não a qualidade de uma variante operacional.

## Escopo local aditivo e transferência — 2026-09-06

Implementado candidato **experimental, não promovido**, em
`representacao_escopo_local.py`. Reutiliza o mapa canônico de aspas de
`arquivos/nome_natural.py`; registra spans no texto original. Um canal TF-IDF
adicional representa sequências de 1–5 tokens, início/fim, pontuação e tipos
de trecho. Conteúdo citado e números recebem categorias nesse canal;
palavras não citadas continuam lexicais. O texto e os dois canais antigos
permanecem preservados. Aspas incoerentes não ocultam texto; citação não é
prova de alvo, permissão ou cancelamento. Não é um parser semântico completo.

Experimento único: canal adicional, mesmos parâmetros do classificador,
peso 1 e limiar zero. O runner separado `experimento_escopo_local.py` mantém
intactos os scripts usados pelos artefatos anteriores. Confere hashes do
modelo/dados/código/bateria e reproduz os folds nos dois eixos. Protocolo
salvo antes de fit; reservas v2 são diagnóstico conhecido, não teste inédito.
Não atribuir o ganho a um único recurso (aspas ou ordem): o canal os combina.

| Medida | Lexical v2 anterior | Canal local adicional |
| --- | ---: | ---: |
| CV construção / novos | 277/288 | 282/288 |
| Recusas perdidas nessa fatia | 3 | 0 |
| CV construção / histórico | 3310/3340 | 3314/3340 |
| CV entidade / novos | 225/288 | 270/288 |
| CV entidade / histórico | 3314/3340 | 3317/3340 |
| Reserva entidades | 81/96 | 91/96 |
| Reserva construções | 144/144 | 144/144 |
| Reserva ambas | 40/48 | 42/48 |

Contra o controle histórico sem novos exemplos, ainda há duas regressões
pareadas e um ganho no histórico da CV por construção (controle 3315/3340),
e cinco regressões e um ganho na CV por entidade (controle 3321/3340).
Portanto, o candidato **não preserva todos os comportamentos históricos**.
Na fatia nova por construção os seis erros restantes são falsas negações da
família c1; nenhuma recusa perdida. O candidato atômico anterior tinha
259/288 e 29 recusas perdidas nessa mesma fatia, mas a comparação de uma
adição isolada é com o lexical v2 (277/288), não com o atômico.

Frozen 24/24. Bateria antiga continua 27/40 neural contra 33/40 Python;
as quatro correções originais continuam `negated=True`. Troca de cabeça em
cópia do modelo completo preservou as demais previsões na bateria. Isso
não valida o runtime, nem prova superioridade geral sobre o sistema Python.

### Primeira fronteira restante: contribuição lexical dependente do alvo

`diagnostico_transferencia_escopo.py` inspeciona a cabeça salva sem fit ou
alteração de pesos. Soma todas as contribuições, com erro de reconstrução
máximo observado `8,88e-15`. Pares escolhidos após observar falhas são apenas
diagnóstico, não avaliação inédita. Exemplos de score (positivo = negação):

| Mudança | Antes | Depois |
| --- | ---: | ---: |
| `inicie o Cedrion, não o Belmora` → Opera/Firefox | -0,99305 | +2,94352 |
| `ajuste o áudio para 14, não para 28` → 30/50 | -1,46489 | -0,75851 |
| `ajuste o áudio para 30, não para 50` → `coloca o volume em 30, não em 50` | -0,75851 | +4,30314 |
| `reproduza a canção "Rota Cedrion", não a canção "Rota Belmora"` → Brisa/Aurora | -2,25777 | +1,66237 |

No último par, a contribuição do canal local é **idêntica: -2,16814**.
O intercepto também é igual. Palavras mudam de -1,16514 para +0,06167 e
caracteres de +3,53778 para +6,23111. Logo, nesse par a primeira transição
incorreta não é perda da estrutura citada: os canais lexicais restantes
fazem a soma cruzar zero quando apenas o título muda. O canal local recebeu
forma invariável, mas isso não torna a decisão completa invariável.

Em apps, o canal local até contribui mais contra o cancelamento após a troca
de nome (-1,57527 → -2,42347); o canal de caracteres sobe de +4,11794 para
+7,33779 e domina a mudança. Na moldura de áudio, porém, 25 de 43 pistas
estruturais emitidas ficam fora do vocabulário, contra zero na moldura
anterior: há também perda de transferência de construção. Não misturar
essas duas fronteiras. Aspas adicionadas a Opera/Firefox não corrigem a
decisão; alterar só os valores de áudio também não explica a falha original.

Próxima hipótese delimitada: desacoplar a identidade do alvo da decisão de
negação sem apagar o texto necessário ao resolver. Antes de outro treino,
medir uma ablação diagnóstica de canais nos contrastes positivos e negativos,
incluindo recusas reais, nomes literais e frases sem aspas. Não simplesmente
remover os canais legados: eles ainda sustentam proteções históricas.

Artefatos: `memoria/neural/experimentos/escopo_local_aditivo_v1_20260906/`
(protocolo, relatório e cabeça não promovida) e
`resultados_testes/diagnostico_transferencia_escopo_local_20260906.json`.
Testes: 387 passaram em 57,80 s na seleção neural/P0 após implementar o
candidato. Dois testes adicionais de atribuição e preservação do diagnóstico
foram acrescentados depois; não estão nessa contagem ampla.
Produção/modelo configurado/autoridade/executor intocados, `shadow` mantido,
sem commit nem teste físico. HEAD `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`,
branch `main`, worktree já suja. Resultado: melhora intermediária, não correção
encerrada e não autorização para uso operacional da cabeça candidata.

## Calibração com treino/calibração/teste separados — 2026-09-06

Experimento concluído; **a política testada não preservou o histórico no
teste externo**, portanto não foi aplicada. `calibracao_negacao_experimental.py`
ajusta somente o limiar da cabeça de negação, sem calibrar probabilidades,
salvar pesos, alterar o modelo configurado ou autorizar execução.

Protocolo congelado antes do fit: quatro folds externos por construção,
reproduzindo IDs/grupos da rodada atômica. Dentro de cada fold, `GroupKFold(3)`
separa treino e calibração; escolhe a divisão interna `fold_externo % 3`, sem
consultar resultados. Em cada rodada: 1.814 exemplos para fit, 907 para
calibração e 907 para teste. Famílias e duplicatas normalizadas ficam juntas;
cada exemplo recebe exatamente uma previsão externa por representação.

O grupo c3 **não** calibra o limiar aplicado ao próprio c3 (teste do fold 0).
Na rotação, ele pode participar da calibração de outro fold, como ocorre no
fold 3. Isso esclarece a orientação anterior de não calibrar no grupo observado:
nunca calibrar e avaliar a mesma família na mesma rodada. Os dados continuam
conhecidos de pesquisa, não uma reserva inédita para alegar superioridade.

Escolha fixada antes dos scores: aceitar somente limiares que não aumentem
nenhum dos dois tipos de erro na calibração, **separadamente no histórico e
nos novos**. Entre os elegíveis, minimizar recusas perdidas, depois negações
falsas, depois distância a zero. Ausência de uma fatia ou de ambas as classes
preserva zero. A escolha recebe apenas scores/rótulos/fatias de calibração.
O teste só é previsto depois; não há refit que altere a escala dos scores.

O modelo com limiar zero e o ajustado têm os **mesmos pesos** em cada par.
Não comparar diretamente seus acertos com a CV anterior: agora o fit usa
menos dados para reservar calibração. Comparação desta rodada:

| Representação / fatia de teste | Acertos: zero → ajustado | Recusas perdidas | Negações falsas |
| --- | ---: | ---: | ---: |
| Lexical / histórico (3.340) | 3303 → 3302 | 28 → 26 | 9 → 12 |
| Lexical / novos (288) | 260 → 260 | 16 → 9 | 12 → 19 |
| Atômica / histórico (3.340) | 3304 → 3301 | 27 → 25 | 9 → 14 |
| Atômica / novos (288) | 236 → 245 | 35 → 29 | 17 → 14 |

Comparação pareada atômica: histórico com dois ganhos e **cinco regressões**;
novos com onze ganhos e duas regressões. No histórico, passaram a ser
canceladas entradas antes corretas como `como está o tempo hoje`, `mantenha
o VS Code aberto` e `por gentileza pare o ventilador`. A última tem score
-0,14040, mas o limiar aprendido para seu fold é -0,37510: cruza a fronteira
de negação apesar de não existir uma recusa nessa instrução. As outras duas
regressões são pedidos musicais polidos. Não ocorreu execução física.

Fronteira demonstrada: melhoria Pareto na calibração não garante melhoria
Pareto em famílias externas. O teste falsifica a suficiência **desta política
de limiar**, não a possibilidade de qualquer calibração futura. Não escolher
um dos limiares dos folds para produção nem ajustar novamente pelos erros
externos. Próxima fronteira: voltar à representação do alcance da negação,
com contrastes entre recusa da ação, correção do alvo e texto literal;
preservar estes resultados como controles, antes de novo treino.

Serviços reutilizados: schema/catálogo de exemplos, filtro `training_heads`,
união canônica de grupos duplicados, reprodução de folds e fit clonado da
cabeça. A calibração OOD existente foi inventariada, mas usa confiança de
intenção e falso aceite fora do catálogo; não é a mesma decisão nem métrica.
Referência metodológica: [scikit-learn: separação dos dados para ajuste do
limiar](https://scikit-learn.org/1.5/modules/classification_threshold.html).

Artefatos: `memoria/neural/experimentos/calibracao_negacao_tres_partes_v1_20260906/`.
`protocolo.json` registra regra, partições, hashes e worktree antes do fit;
`relatorio.json` registra limiares, calibração, métricas e todas as previsões
externas com IDs/scores. Nenhum modelo novo foi salvo.

Validação: **371 testes passaram em 56,32 s**, incluindo separação de famílias,
duplicatas, preservação de zero, dados inválidos, trade-offs proibidos e
regressivos neurais/P0. Compilação passou. Não é GREEN de runtime nem aprovação
do classificador. Produção, executor e configuração intocados; modelo mantém
SHA256 `caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf`
e modo `shadow`. Nenhum commit ou teste físico.

## Recusas fora do treino: reprodução e margem — 2026-09-06

`diagnostico_fold_negacao.py` reconstrói **somente o fold 0** da CV por
construção, sem salvar pesos ou criar candidato para promoção. São 2.505
exemplos históricos + 216 novos no treino; 907 no teste. A família
`escopo_v2_c3` fica inteira fora do treino, com 72 contrastes no teste.
As demais famílias históricas continuam presentes conforme o split original.

Hashes dos dados, modelo e componentes da rodada atômica foram conferidos;
IDs e grupos de todos os folds foram reproduzidos para os dois experimentos.
O runner da rodada lexical antecede a adição do modo atômico: seu hash antigo
**não foi atualizado**; a divergência está registrada no diagnóstico. As
contagens de erros por família foram reproduzidas, mas os relatórios antigos
não guardavam previsões individuais nem pesos dos folds. Não alegar igualdade
bit a bit de pesos antigos indisponíveis.

| Na família fora do treino | Controle histórico | Candidato lexical | Candidato atômico |
| --- | ---: | ---: | ---: |
| Acertos | 36/72 | 69/72 | 43/72 |
| Recusas perdidas | 0 | 3 | 29 |
| Correções canceladas indevidamente | 36 | 0 | 0 |

A primeira fronteira errada reproduzida é a decisão da cabeça de negação,
não executor, voz ou Qwen. Em `não quero que você inicie o Cedrion`, o
candidato atômico produz:

`intercepto -2,75560 + palavras -1,84612 + caracteres -2,86564
+ sinal explícito 6,78545 = score -0,68191 → negated=False`.

O sinal explícito vale 1; não foi perdido ou invertido. O alvo `Cedrion`
está no vocabulário; o único bigrama de palavras OOV desse exemplo é
`voce inicie`. Portanto, ausência do marcador e alvo desconhecido não explicam
esse erro. Todas as 72 entradas possuem os mesmos sinais `(1, 0)`: eles
indicam presença, não o alcance da negação. As contribuições locais de texto
superam o sinal nesse exemplo. A soma completa reproduz os scores com erro
máximo de `1,42e-14`; as pistas principais exibidas são apenas um recorte.

Controle diagnóstico mantendo o alvo: trocar a moldura por `não inicie o
Cedrion` eleva o score a `+0,69614`. O delta exato é `+1,54485` de pistas
removidas, `+0,24843` de pistas novas e `-0,41522` de reponderação das
compartilhadas. Essa troca recupera 24 das 29 recusas; cinco continuam erradas.
Os pares são diagnóstico conhecido, não uma reserva nova nem exemplos de fit.

**Nuance importante:** não está provado que falta uma representação capaz de
separar essa família. Os scores atômicos de suas correções vão até -1,95410,
enquanto suas recusas começam em -1,46668. Existe um intervalo separador
local, apesar do limiar zero errar. No fold completo, porém, há uma entrada
rotulada como não recusa em +3,69548 (`mantenha o aplicativo de música fora de
execução`): nenhum limiar único elimina todos os erros desse fold, dados os
rótulos atuais. Isso **não** mede se deslocar o limiar melhoraria o compromisso
global; não foi aplicado deslocamento nem escolhida uma configuração.

Próxima etapa: avaliar margem e calibração em partições próprias, comparando
com o candidato lexical e contabilizando os dois tipos de erro. Não calibrar
no grupo c3 observado nem tratar seu intervalo como parâmetro de produção.
Separar a hipótese de limiar inadequado da hipótese de pistas de escopo
insuficientes antes de acrescentar mais exemplos ou outra arquitetura.

Ferramenta de atribuição ampliada para explicar os sinais fixos, sem inventar
vocabulário/OOV para eles. RED local: dois testes falharam na antiga exigência
de vocabulário; após a extensão, 38 testes focados passaram. Seleção ampla:
353 passaram em 74,67 s. A análise de margem acrescentada depois passou em
12 testes do módulo (incluindo cinco novos); a seleção ampla não inclui esses
cinco nesta contagem.

Evidências preservadas:
`resultados_testes/diagnostico_fold_negacao_c3_20260906.json` e
`resultados_testes/diagnostico_fold_negacao_c3_margens_20260906.json`.
O segundo acrescenta as margens com nova reprodução do mesmo fold, sem novo
candidato. Ambos contêm casos, contribuições, pares e proveniência.

Escopo: ferramentas de diagnóstico e testes; nenhuma alteração em produção,
configuração, autorização ou executor. Modelo configurado preservado por hash,
modo `shadow` mantido, sem lançamento da assistente ou teste físico. Base Git
`a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, branch `main`, worktree já suja;
nenhum commit criado. Diagnóstico de ML não é GREEN de runtime.

## Sinais atômicos separados do texto — 2026-09-06

Experimento implementado e **reprovado para substituição**. O módulo
`representacao_sinais_atomicos.py` clona os dois vetorizadores lexicais,
preserva o texto normalizado e move somente os metadados anexados pelo
extrator canônico para duas colunas fixas 0/1. Ocorrências literais dos nomes
dos marcadores continuam no texto; mudança incompatível do contrato aborta.
As funções serializadas dos modelos antigos não foram alteradas.

Condição única: `sinais_atomicos`, peso 1, protocolo `entidades_v2`, somente
cabeça de negação. Comparação com `escopo_entidades_v2_base_peso1_20260906`:
hash do treino, conteúdo reservado e IDs dos testes de cada fold são iguais
nos dois eixos. A reserva v2 já era conhecida: serve como diagnóstico,
**não** como avaliação inédita após escolha da representação.

| Medida da cabeça de negação | Candidato lexical v2 anterior | Sinais atômicos |
| --- | ---: | ---: |
| CV por construção — novos | 277/288 | 259/288 |
| Cancelamentos verdadeiros perdidos nessa fatia | 3 | 29 |
| CV por construção — histórico | 3310/3340 | 3312/3340 |
| CV por entidade — novos | 225/288 | 241/288 |
| CV por entidade — histórico | 3314/3340 | 3314/3340 |
| Reserva de entidades | 81/96 | 87/96 |
| Reserva de construções | 144/144 | 126/144 |
| Reserva de ambas | 40/48 | 37/48 |

Os 29 cancelamentos perdidos na CV nova estão na família `escopo_v2_c3`
(`não quero que você ...`), quando essa construção fica fora do treino.
O modelo ajustado com todas as construções acerta 288/288 no próprio lote:
isso não prova generalização. Não confundir esses modelos dos folds com
a cabeça final ajustada sobre todo o lote.

O controle histórico sem os novos exemplos faz 3315/3340 na CV por
construção: o candidato ainda introduz três regressões pareadas, sem ganhos
históricos. Na CV por entidade, o controle faz 3321/3340; ambos os candidatos
ficam em 3314. O gate local reprova a condição. As reservas não perderam
cancelamentos verdadeiros; seus erros são cancelamentos falsos.

A bateria antiga continua **27/40 neural contra 33/40 Python**. As quatro
correções originais (volume 30/50, Brisa/Aurora, Opera/Firefox e
rascunho/relatório) continuam com `negated=True`; Frozen permanece 24/24.
Essas métricas não são uma avaliação do runtime completo.

Conclusão sustentada: separar metadados melhorou parte da transferência de
entidades, mas não resolveu escopo e piorou cancelamentos de uma construção
excluída. Fica falsificada a hipótese de que essa separação, sozinha, basta.
Próxima fronteira: inspecionar as decisões **fora do treino** dessa família,
comparando as contribuições locais de ordem/texto e dos dois sinais; não
aumentar pesos ou promover com base no acerto do próprio lote. O contrato é
geral: correção de alvo não cancela a ação, mas recusa explícita deve continuar
bloqueando-a, independentemente do domínio ou nome do alvo.

Artefatos: `memoria/neural/experimentos/escopo_sinais_atomicos_v2_peso1_20260906/`
(`protocolo.json`, `relatorio.json`, lote e cabeça não promovida). O protocolo
foi salvo antes do fit. Somente carregar artefatos locais confiáveis.

Escopo: módulo experimental, integração no runner e regressivos. Nenhuma
alteração no modelo configurado, executor, autorização, `laylay.py` ou modo
`shadow`; SHA256 do modelo continua
`caaa93027eb96451cbbf1c61136389ac8402533226c666225da3a2def356e0cf`.
Nenhum commit, lançamento da assistente ou teste físico nesta etapa.

Validação final: **344 testes passaram** na seleção de sinais atômicos,
diagnóstico de pistas, reservas, escopo, comparação linguística, representação,
linguagem neural e P0 de autorização/modalidade (71,65 s). Compilação dos
arquivos Python alterados também passou. GREEN dos contratos experimentais
não equivale à aprovação estatística do candidato, que permanece RED.

## Diagnóstico das pistas da negação — 2026-09-06

Sem novo treino de candidato. `diagnostico_pistas_negacao.py` inspeciona a
cabeça lexical v2 já salva e decompõe a decisão linear em intercepto mais
`valor_da_feature × coeficiente`. A soma de **todas** as contribuições,
não apenas das doze maiores exibidas, reproduz o score real (erro máximo
observado `1,07e-14`). A ferramenta recusa classes não booleanas/invertidas,
dimensões incompatíveis e valores não finitos. Não autoriza efeitos.

Nesta cabeça, score positivo corresponde a `negated=True`; o score não é
probabilidade calibrada nem acurácia. Exemplos medidos, mantendo a estrutura:

| Troca de alvo | Score antes | Score depois | Resultado |
| --- | ---: | ---: | --- |
| `ajuste o áudio para 14, não para 28` → `83, não para 96` | -0,4875 | +0,2434 | correção vira cancelamento |
| `inicie o Cedrion, não o Belmora` → `Zelvoria, não o Tarselio` | -0,6906 | +5,0468 | correção vira cancelamento |

O relatório contém os textos completos dos pares. Decomposição exata do
delta nos exemplos acima:

| Componentes do delta | Áudio | Apps |
| --- | ---: | ---: |
| Pistas que desapareceram | +1,13437 | +2,95032 |
| Pistas que apareceram | 0 | -0,01182 |
| Pistas compartilhadas reponderadas | -0,40350 | +2,79889 |
| Total | +0,73087 | +5,73739 |

Primeira fronteira demonstrada nesses pares:

`troca apenas do alvo → n-gramas lexicais ausentes no vocabulário → perda de
contribuições e reponderação TF-IDF/L2 → score cruza zero → negated=True`.

Não é uma penalidade direta atribuída ao nome desconhecido: no áudio nenhuma
feature nova entrou; em apps as features novas contribuíram levemente no
sentido contrário ao erro. Trocar somente o verbo também não explica o par
de apps, pois ambos começam com `inicie`.

O extrator atual acrescenta `marcador_negacao_explicita` ao próprio texto que
alimenta **palavras e caracteres**. O marcador isolado emite 72 fragmentos
distintos no analisador de caracteres da cabeça v2, todos no vocabulário.
No par de apps, o canal de caracteres contribui +3,8826 antes e +7,7000
depois. Essas somas incluem caracteres naturais e metadados: não atribuir
toda a diferença ao marcador apenas pela inspeção dos nomes das features.

Uma ablação adicional, **somente em cópia temporária do vetor**, removeu do
canal de caracteres apenas o sufixo de metadados anexado pelo extrator,
preservando texto original, canal de palavras e pesos. Corrigiu os exemplos
de alternativa inspecionados, mas também mudou `não inicie o Cedrion` de
cancelamento para não cancelamento (score contrafactual -4,3699). Isso
falsifica a proposta de simplesmente retirar o marcador em produção. A
ablação também muda a normalização do canal; não isola somente um coeficiente
e não representa um modelo retreinado/validado.

Evidência: `resultados_testes/diagnostico_pistas_negacao_v2_20260906.json`.
Reprodução:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.diagnostico_pistas_negacao `
  --cabeca memoria/neural/experimentos/escopo_entidades_v2_base_peso1_20260906/cabeca_negacao_nao_promovida.joblib `
  --saida resultados_testes/diagnostico_pistas_NOVA_EXECUCAO.json
```

Somente carregar artefato local confiável. Saída existente aborta. O hash da
cabeça é verificado antes/depois; não há fit, promoção, execução ou edição de
modelo nesta ferramenta. Testes usam pequenas cabeças de fixture, sem
substituir a inspeção do artefato real.

Próxima experiência proposta: representar metadados de negação como sinais
atômicos separados dos caracteres do texto, retreinando só essa cabeça e
preservando os sinais de cancelamento e o texto literal para resolução do
alvo. Essa representação ainda **não foi implementada nem validada**.
Não alterar as funções serializadas dos modelos antigos. Medir cancelamento
verdadeiro, correção de alternativa, nomes literais e transferência a alvos
novos; v2 já é diagnóstico conhecido, não uma reserva inédita para ajustes.

Validação desta etapa: **326 testes passaram** na seleção de diagnóstico,
reservas, negação, comparador, representação, linguagem neural e P0. Modelo
configurado e cabeça inspecionada preservados por hash; modo `shadow`
inalterado. Produção não foi editada, nenhum commit criado e nenhum teste
físico realizado. O diagnóstico não equivale à correção encerrada.

## Transferência entre entidades e construções — 2026-09-06

O protocolo `entidades_v2` varia construções e alvos independentemente. São
576 contrastes balanceados: 288 de treino e 288 reservados **antes do fit do
candidato**, sem alterar rótulos conforme as previsões. Quatro construções
e seis pares de entidades entram no treino; duas construções e dois pares
ficam reservados. Há quatro domínios e duas fatias adicionais com “não” no
nome literal (música/arquivo). Nomes são sintéticos, não habilidades novas.

`datasets/gerar_escopo_negacao_v2.py` declara a grade. Os metadados de partição,
entidade, domínio e rótulo não são fornecidos ao classificador; apenas texto
e rótulo de negação entram em fit. As reservas nunca são usadas em fit ou CV.
`protocolo.json` registra parâmetros, reserva e hashes antes do treino.
Alvos reservados (inclusive 83/89/96/98 e nomes sintéticos) foram procurados
também nos 3.922 exemplos históricos: nenhuma ocorrência. Auditoria do novo
treino contra histórico e os diagnósticos antigos: nenhuma duplicata exata,
quase duplicata ou família compartilhada na checagem canônica.

Condição única pré-definida: representação **base**, peso **1**, somente a
cabeça de negação. Não houve busca de hiperparâmetros usando esta reserva.

| Reserva fora do fit | Base configurada | Candidato |
| --- | ---: | ---: |
| Entidades novas, construções conhecidas | 48/96 | 81/96 |
| Construções novas, entidades conhecidas | 96/144 | 144/144 |
| Construções e entidades novas | 32/48 | 40/48 |

Nenhum cancelamento verdadeiro foi perdido nessas três reservas. Os erros
restantes são cancelamentos inventados. Ainda assim, **não promover**:

- CV por construção: nova fatia 144→277/288, mas três cancelamentos
  verdadeiros passaram a ser perdidos. Histórico 3315→3310/3340 (cinco
  regressões pareadas, nenhum ganho).
- CV por entidade: nova fatia 144→225/288; histórico 3321→3314/3340
  (oito regressões pareadas e um ganho).
- Ajuste nos próprios exemplos novos: 288/288. Isso não substitui os
  resultados fora do treino acima.
- Bateria antiga permanece 27/40, abaixo do classificador Python 33/40;
  as quatro correções originais ainda retornam `negated=True`.
- Frozen conhecido mantém 24/24 na negação. Todas as demais saídas do modelo
  foram preservadas na bateria de 44 frases, exceto negação/confiança dela.

Os controles de CV mudam quando o conjunto/grupamento muda. Comparar cada
candidato com **seu controle pareado**, não com os 3327 acertos de outra
partição v1. A CV por entidade reaproveita grupos de entidade disponíveis e
os grupos históricos restantes; não garante sozinha que todo valor numérico
de um fold esteja ausente dos históricos. Essa ausência foi validada
explicitamente para os alvos da reserva fixa.

As reservas compartilham deliberadamente um eixo com o treino (ou nenhum no
caso `ambas`); não se exige distância lexical entre frases que testam apenas
a troca do alvo. Isso é uma avaliação sintética de transferência, não prova
de conversa natural completa. Depois desta leitura, a reserva passa a ser
diagnóstico conhecido: não ajustar repetidamente mirando seu placar e
continuar chamando-a de inédita.

Evidência: `memoria/neural/experimentos/escopo_entidades_v2_base_peso1_20260906/`
contém `protocolo.json`, `relatorio.json`, lote de treino e apenas a cabeça
experimental. O `gate_local` atual mede a CV por construção e já reprova o
candidato; CV por entidade, reservas e bateria também devem ser consultadas.
Nenhum desses campos autoriza promoção ou execução.

Reprodução: usar o comando do experimento com `--protocolo entidades_v2`,
`--representacao base --peso-novos 1` e **destino novo**. Se interrompido após
criar `protocolo.json`, manter essa pasta como execução incompleta; não
sobrescrevê-la para produzir verde artificial.

**315 testes passaram** (reservas, negação, comparador, representação,
linguagem neural e P0). Hashes do modelo e bateria preservados; configuração
continua `shadow`. Nenhuma habilidade foi executada fisicamente, nenhum
modelo ativo foi substituído e nenhum commit foi criado.

Próxima fronteira: investigar quais pistas lexicais ainda fazem o escopo
depender do alvo, antes de outro treino. A reserva de entidades deixa 15
erros (apps 6, áudio 4, música 3 e música literal 2); a reserva conjunta deixa
oito (dois em cada uma dessas fatias). Não trocar os erros por heurísticas
com nomes especiais. O contrato procurado é: trocar apenas uma entidade ou
valor não deve mudar qual parte do pedido foi negada; o texto literal do
alvo continua preservado para seu resolvedor canônico.

## Ablação de canais e peso do lote — 2026-09-06

Quatro condições definidas antes da execução: representação `base` ou
`combinada` (extrator antigo + canais integrais), com `peso_novos=1` ou `4`.
O peso é aplicado via `sample_weight` somente no classificador durante o
treino, sem replicar registros ou alterar vocabulário por duplicação. Os
mesmos dados, grupos, quatro folds e rótulos foram preservados. Hashes dos
índices de teste conferem nas quatro execuções. Nenhum threshold mudou.

| Condição | CV nova /52 | CV histórica /3340 | Regressões históricas pareadas | Bateria /40 |
| --- | ---: | ---: | ---: | ---: |
| Base, peso 1 (reprodução) | 41 | 3327 | 0 | 27 |
| Base, peso 4 | 50 | 3326 | 1 | 27 |
| Combinada, peso 1 | 47 | 3325 | 3 | 27 |
| Combinada, peso 4 | 50 | 3325 | 2 | 27 |

Controle histórico das quatro execuções: 3327/3340 e 34/52. A combinada com
peso 1 também corrige um erro histórico, por isso suas três regressões não
equivalem à diferença líquida de dois acertos. O primeiro resultado reproduz
o experimento anterior; os outros três reprovam o gate local histórico.
Nenhum resolve as quatro correções originais. Nenhum candidato foi ativado.

### Falsificação adicional: alvos não deveriam decidir o escopo

Sonda posterior, apenas diagnóstico, no artefato `base_peso4`:

| Texto | `negated` previsto |
| --- | --- |
| ajuste o áudio para 23, não para 67 | false |
| ajuste o áudio para 30, não para 50 | true |
| inicie o Krita, não o Inkscape | false |
| inicie o Opera, não o Firefox | true |
| abre o Krita, não o Inkscape | false |
| abre o Opera, não o Firefox | true |

O sentido de correção permanece, mas trocar somente valores/nomes altera a
decisão. Isso demonstra sensibilidade indevida às entidades nestes pares;
não prova que todo erro de negação tenha a mesma causa. A hipótese de que
somente o verbo `abre` causasse a falha é falsificada pelo par com Krita.
Aumentar o peso ou juntar canais, nas condições testadas, não produziu uma
regra generalizada de escopo. Não continuar escolhendo pesos pelo placar da
bateria já conhecida.

Próxima fronteira: ampliar os contrastes com variação independente de
construção e entidades/parâmetros, avaliando separadamente grupos de
construção e grupos de entidade (incluindo nomes literais negados). O lote
v1 tem poucos alvos fixos por domínio; sua CV por construção, sozinha, não
mede essa transferência. Manter a bateria conhecida como diagnóstico e
reservar famílias/alvos inéditos antes do próximo ajuste.

Artefatos completos nas quatro pastas
`memoria/neural/experimentos/ablacao_negacao_{base|combinada}_peso{1|4}_20260906/`.
Para reproduzir, o comando do experimento abaixo aceita
`--representacao combinada --peso-novos 4`, sempre com destino novo.

**307 testes passaram** na seleção de negação, comparador, representação,
linguagem neural e autorização P0. Incluem equivalência com pesos unitários,
rejeição de pesos inválidos, clonagem dos canais e prova de que ponderação
não modifica as partições. Modelo configurado conferido pelo hash e
`LAYLAY_NEURAL_MODE=shadow` preservado. Produção, executor e demais cabeças
não foram editados; nenhum commit criado e nenhum teste físico executado.

## Experimento de escopo da negação — 2026-09-06

Continuação da comparação Python/rede abaixo. **Nenhuma promoção**: dois
candidatos isolados foram medidos e nenhum resolveu a fronteira com segurança.
Produção, modelo configurado, limiares e configuração `shadow` preservados.

Base: HEAD `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, branch `main`,
worktree modificada (inventário completo nos relatórios). Os 3.922 exemplos
históricos foram reconstruídos pelo manifesto v26 e hashes originais de DEV
e lotes. Refazer somente a cabeça de negação reproduziu suas previsões no
histórico e no lote novo; isso falsifica uma divergência de base de treino
como explicação dos resultados deste experimento.

RED reproduzido antes do candidato: as quatro correções da bateria
(`coloca o volume em 30, não em 50` e equivalentes em música, apps e arquivos)
retornam `negated=True`. O head de comando aceita essas frases e OOD é falso:
o cancelamento indevido ocorre na cabeça de negação, não no executor ou no
limiar do comando. O extrator atual adiciona marcador global de negação;
isso não prova sozinho que o marcador seja a causa — foram comparadas duas
representações sem modificar a função serializada do modelo em uso.

`datasets/gerar_escopo_negacao_v1.py` fornece 52 contrastes balanceados,
exclusivos do head `negation`, distribuídos em sete grupos de construção.
Paráfrases irmãs em domínios diferentes e oposições ficam no mesmo grupo.
Inclui correção de alternativa, cancelamento inicial/tardio e nomes literais
com “não”. Auditoria canônica: zero duplicatas exatas/quase duplicatas ou
famílias compartilhadas contra os 3.922 históricos e os 68 diagnósticos
(44 da bateria + 24 Frozen). Isso não transforma o lote sintético em reserva
representativa do uso real.

CV pareada em quatro folds, somente negação: 3.340 exemplos históricos
aplicáveis ao head e 52 novos. Controle e candidato usam os mesmos testes;
o controle treina só o histórico restante e o candidato acrescenta apenas
os grupos novos que não estão em teste. Grupos com textos normalizados
idênticos são unidos para não atravessar folds.

| Resultado | Controle | Mesma representação + lote | Integral + lote |
| --- | ---: | ---: | ---: |
| CV nova: acertos | 34/52 | 41/52 | 50/52 |
| CV histórica: acertos | 3327/3340 | 3327/3340 | 3302/3340 |
| CV histórica: negações perdidas | 6 | 6 | 31 |
| CV histórica: negações falsas | 7 | 7 | 7 |
| Bateria de pedidos conhecida | 27/40 | 27/40 | 24/40 |
| Frozen conhecido, somente negação | 24/24 | 24/24 | 23/24 |

Na fatia histórica, o primeiro candidato teve zero ganhos/regressões pareados;
o integral teve oito ganhos e 33 regressões. Na fatia nova, os ganhos foram
respectivamente sete e 16, sem regressões pareadas. Ambos preservaram todas
as outras saídas do modelo na bateria completa de 44 frases: apenas negação
e sua confiança mudaram. Não há execução física nesses testes.

Mesmo no ajuste integral dos próprios 52 exemplos de treino, o candidato
lexical acerta apenas 43; o integral acerta 52. Portanto **não basta atribuir
tudo à generalização**: a primeira variante ainda tem erro de ajuste nessa
base, enquanto a segunda aprende o lote mas prejudica a cobertura histórica.
Não reduzir thresholds para ocultar nenhum dos dois problemas.

Artefatos preservados em `memoria/neural/experimentos/`:

- `escopo_negacao_v1_20260906/relatorio.json`;
- `escopo_negacao_integral_v1_20260906/relatorio.json`.

Cada pasta contém o lote e **somente a cabeça experimental não promovida**,
não um substituto configurado do modelo completo. `gate_local.aprovado` do
primeiro relatório refere-se apenas à melhora/não regressão agregada da CV
de negação; não aprova a bateria, o runtime nem a promoção.

Reprodução, com destino novo (o executor recusa sobrescrita):

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.experimento_escopo_negacao `
  --modelo memoria/neural/experimentos/v27_list_windows_onda_v1/modelo_candidato_extensao_estado_estrutura_v4.joblib `
  --historico memoria/neural/experimentos/hibrido_v3_iot_v4_negacao_v5_cmd_v6_exp_v7_telegraphic_final_v8_v26 `
  --bateria tests/fixtures/neural/bateria_linguistica_v1.json `
  --destino memoria/neural/experimentos/escopo_negacao_NOVA_EXECUCAO `
  --representacao base
```

Para a segunda variante, `--representacao integral` reutiliza os canais
integrais já existentes e o mesmo classificador, sem alterar a representação
dos demais heads. Validação de contratos: 298 testes passaram na seleção
ampla antes da última ampliação do teste de CV; depois, 25 testes focados
passaram, incluindo a troca de protótipo. Não confundir isso com acurácia.

Próxima fronteira: separar, por ablação controlada, o peso dos exemplos novos
e as pistas estruturais/lexicais preservadas. Só aceitar melhora que reduza
cancelamentos inventados sem perder cancelamentos verdadeiros nas famílias
históricas, antes de ampliar para contexto e propor remoção de regras Python.

## Comparação com o classificador Python — 2026-09-06

Objetivo autorizado: superar a interpretação atual antes de substituir regras.
Primeira etapa entregue: diagnóstico pareado de **pedido operacional sem
contexto**, usando o artefato configurado v27 e o classificador canônico com seu
detector real de comandos. Não é comparação da Laylay completa: não carrega
aliases/memória, não resolve alvos e não executa habilidades.

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.comparacao_linguistica `
  --bateria tests/fixtures/neural/bateria_linguistica_v1.json `
  --modelo memoria/neural/experimentos/v27_list_windows_onda_v1/modelo_candidato_extensao_estado_estrutura_v4.joblib `
  --saida resultados_testes/comparacao_neural_python_NOVA_EXECUCAO.json
```

O comando recusa sobrescrever a saída. Usa somente artefato local confiável;
não treina, promove, muda configuração ou escreve no buffer de aprendizado.
O relatório registra hashes, HEAD, branch e worktree; o HEAD sozinho não
representa esta worktree modificada.

Evidência: `resultados_testes/comparacao_neural_python_20260906_v2.json`.
Dos 44 casos conhecidos de desenvolvimento, 4 exigem contexto e ficam
explicitamente excluídos. Nos outros 40:

| Fronteira de pedidos | Python | Rede v27 |
| --- | ---: | ---: |
| Acertos | 33/40 | 27/40 |
| Falsos pedidos | 1 | 3 |
| Pedidos perdidos | 6 | 10 |
| Falhas de inferência | 0 | 0 |

Comparação pareada: 26 acertos compartilhados, 6 erros compartilhados,
1 ganho da rede e 7 regressões. Rótulos independentes vêm da bateria já
revisada, nunca da resposta do legado. Falhas de inferência não contam como
negativos corretos; não somem do denominador. Domínio, ID e expectativa não
são fornecidos aos preditores. A rede é medida pelo critério de candidatura da
sombra (comando, negação e OOD), não como autorização de execução.

Primeiras fronteiras observadas:

- Citações: 3 menções isoladas viram candidatas na rede.
- Correção de alvo/parâmetro: nos quatro domínios, o head de comando aceita o
  pedido, mas o head de negação cancela tudo. Exemplo: `coloca o volume em 30,
  não em 50`. OOD é falso; não é falha do executor nem do limiar de comando
  nestes quatro casos. O modelo configurado é híbrido ONNX; a cabeça de
  negação permanece lexical TF-IDF/SGD.
- Pedidos longos: ambos os componentes perdem os quatro pedidos desta fatia.
- Outros pedidos: relatório separa probabilidade, limiar, head bruto e veto;
  não atribuir todas as perdas à mesma causa.

Próxima etapa: investigar e treinar **candidato isolado de escopo de negação**
(negar o pedido versus corrigir alvo/parâmetro), com controles de cancelamento
real, negação em nome literal e diferentes domínios. Separar famílias de
treino/validação; a bateria acima permanece diagnóstico, não reserva inédita
nem fonte automática de treino. Comparar efeitos nas fatias históricas antes
de qualquer promoção. Depois ampliar para contexto, intenção, alvo e sonda
da composição real. Só então decidir quais regras de interpretação podem ser
retiradas; autorização, confirmação do efeito e execução seguem externas.

Esta etapa **não habilita a rede** e não prova superioridade global. Nenhum
modelo, limiar, executor ou configuração de produção foi alterado.
Validação: **291 testes passaram** nos módulos de comparação, representação
integral, linguagem neural e autorização P0. São regressivos locais, não
291 acertos da rede nem prova no runtime completo. Hashes do modelo e da
bateria conferidos após a execução, sem alterações.

Este pacote interpreta linguagem operacional de vários domínios sem substituir
a autoridade canônica do turno. O modo padrão é `shadow`: a previsão é anexada
ao turno, mas sempre publica `autoriza_execucao=false`.

O aprendizado possui duas velocidades:

- receipts confirmados entram no buffer como evidência para revisão, nunca como
  rótulo automático de intenção;
- correções explícitas confirmadas por uma execução correta tornam-se elegíveis
  para revisão; somente as aprovadas no ledger append-only
  `memoria/neural/revisoes_correcoes.jsonl` entram no próximo treino.

O ciclo controlado é executado com:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.treino `
  --estado memoria\neural `
  --promover-se-aprovado
```

Lotes novos não entram diretamente no DEV canônico. Eles são avaliados em
staging com:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.treino `
  --estado memoria\neural `
  --versao tfidf-candidato `
  --lote-candidato mente_laylay\neural\datasets\candidatos\lote.jsonl
```

Um lote staged passa pela validação de schema e pelo detector de leakage antes
de criar o artefato candidato. Enquanto `--lote-candidato` estiver presente, o
ciclo recusa `--promover-se-aprovado`: primeiro o lote precisa passar as
métricas e ser incorporado explicitamente ao DEV. Reprovação não contamina a
base canônica e não troca o modelo ativo.

A promoção só troca o artefato quando o candidato não piora falso comando,
negação perdida, precisão, recall nem acurácia de intenção no challenge
congelado. Quando já existe um modelo ativo, também precisa existir aprendizado
novo comprovável: correções fortes inéditas, mudança da base ou melhora de
métrica. Retreinar exatamente os mesmos dados nunca troca apenas o número da
versão. Mesmo promovido, ele continua em modo sombra; liberação operacional
exige um gate separado por intenção e risco.

A meta inicial de coleta para a expansão do dataset é de 150 a 200 exemplos DEV
por variante `intent:ação`. Cada variante também precisa de pelo menos 12
famílias linguísticas e 15 comandos negados; cada domínio operacional precisa de
30 hard negatives DEV próximos de comandos reais. São cotas configuráveis de
coleta, não prova de qualidade nem permissão de execução. Famílias continuam
separadas entre DEV e challenge, e segurança e receipts são gates independentes.
Esse intervalo é um piso inicial de cobertura, não um teto: novas famílias podem
ultrapassá-lo sempre que erros reais ou validação fora da amostra demonstrarem
uma fronteira ainda fraca. A quantidade nunca substitui os gates de qualidade.

A cobertura atual pode ser auditada sem treinar nem promover modelo:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.cobertura
```

O arquivo `memoria/neural/cobertura_dataset.json` separa a quantidade de DEV da
quantidade congelada, mostra lacunas por capacidade registrada e mede a meta por
`intent:ação`, famílias, negações e hard negatives por domínio. O challenge
nunca é somado a nenhuma cota DEV. A cobertura de ações ainda desconhecidas
precisa ser declarada no catálogo; o relatório não inventa ações ausentes.

As 17 variantes iniciais ficam declaradas em
`datasets/catalogo_variantes_v0.json`. Esse catálogo serve apenas para revelar
classes com zero exemplos, fixar as cotas iniciais e validar a cobertura; todas
as entradas mantêm `operational_influence_enabled=false`. Domínios observados
sem variante operacional, como conversa geral, aparecem no diagnóstico, mas não
criam um gate acidental de hard negatives.

Antes de ampliar ou treinar, audite também o isolamento do challenge:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.qualidade
```

O resultado em `memoria/neural/qualidade_dataset.json` aponta famílias
compartilhadas, duplicatas e paráfrases lexicalmente próximas entre DEV e
Frozen. A auditoria não move nem remove frases automaticamente.

Para medir generalização sem ajustar o modelo pelo Frozen Challenge, execute:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.validacao_cruzada `
  --destino memoria\neural\cv_canonico.json

.\.venv314\Scripts\python.exe -m mente_laylay.neural.validacao_cruzada `
  --lote-candidato mente_laylay\neural\datasets\candidatos\lote.jsonl `
  --destino memoria\neural\cv_candidato.json

.\.venv314\Scripts\python.exe -m mente_laylay.neural.validacao_cruzada `
  --agrupamento validation_group `
  --destino memoria\neural\cv_semantica.json
```

Cada família linguística fica inteira em um fold: uma paráfrase irmã nunca
aparece no treino quando outra frase da mesma família está em validação. Esse
relatório é diagnóstico de generalização, não autorização de promoção ou
execução. O Frozen permanece reservado ao gate final.

Os lotes gerados mais recentes também declaram `validation_group`. Esse campo
agrupa famílias de superfície que exercitam o mesmo mecanismo linguístico.
Com `--agrupamento validation_group`, todas essas famílias ficam no mesmo fold;
essa é a validação principal para comparar candidatos, pois impede que moldes
irmãos do mesmo mecanismo apareçam simultaneamente em treino e validação. A CV
por `family` continua disponível como diagnóstico secundário e compatível com
lotes antigos.

Na configuração experimental de 3.106 exemplos, a linha de base semântica
revelou que a CV somente por família era otimista. O candidato com ownership
das features por cabeça e n-gramas especializados ficou em `6,20%` de falsos
comandos, `98,73%` de precisão de comando, `96,37%` de recall, `90,08%` de
intenção, `86,99%` de ação e `86,87%` de acerto conjunto. A taxa de negação
perdida caiu para `0%`, com apenas uma falsa negação nos 3.106 exemplos. O
relatório canônico está em
`memoria/neural/cv_catalogo_17_variantes_semantica_v7_fallback_corrigido.json`
e não autoriza promoção nem execução.

Os relatórios semânticos v1–v6 são históricos e não devem ser usados como
baseline: um fallback convertia a ausência de `validation_group` na string
`"none"` e colapsava famílias legadas em um só grupo. O fallback corrigido usa
a própria `family`, elevando o total real de 412 para 611 grupos. Um teste de
regressão protege lotes antigos que ainda não declaram grupo explícito.

Na representação `tfidf_indicadores`, cada pista tem um owner: extensões de
negação alimentam somente a cabeça de negação; a cabeça de comando preserva
apenas as pistas já úteis à detecção de comandos; intenção e ação recebem o
texto TF-IDF normal. Isso evita que uma melhoria local desloque classificadores
que não possuem aquela decisão.

As cabeças de comando e negação usam n-gramas de caracteres `4–6`, enquanto
intenção e ação preservam `3–5`. O intervalo especializado reduziu colisões
morfológicas e dominou o candidato anterior nos gates de falso comando,
precisão, recall e negação. Experimentos que apenas aumentaram o peso de
palavras ou aplicaram o intervalo globalmente foram rejeitados por regressão.

Um benchmark isolado com
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, usando ONNX
quantizado e preservando os gates lexicais de comando e negação, elevou
intenção para `90,66%`, ação para `88,03%` e acerto conjunto para `87,84%` nos
mesmos 611 grupos. O encoder agora possui integração experimental explícita:
os embeddings alimentam somente intenção e ação, enquanto comando e negação
continuam sob os gates lexicais. O artefato é carregado de forma tardia,
validado opcionalmente por SHA-256 e nunca vira fallback automático. Essa
integração não autoriza promoção nem influência operacional.

Uma validação experimental pode ser executada apontando para o diretório local
do encoder, sem incorporar o challenge ao treino:

```powershell
python -m mente_laylay.neural.validacao_cruzada `
  --estrategia sgd_log_loss `
  --arquitetura-comando intent_gated `
  --arquitetura-acao hierarchical `
  --limiar-comando 0.65 `
  --representacao onnx_semantico `
  --encoder-semantico memoria/neural/modelos/paraphrase-multilingual-MiniLM-L12-v2-onnx-qint8-avx2 `
  --sha256-encoder-semantico 98a01d88b7de996cdea58c32ca71208c09968d143798814b2ea09d3439dc334f `
  --agrupamento validation_group
```

O limiar OOD lexical não é reaproveitado como se estivesse calibrado para os
embeddings: previsões semânticas publicam `ood_calibrated=false` até existir
uma calibração própria. `onnxruntime` e `tokenizers` são dependências opcionais
desse experimento e só são importadas quando ele é solicitado.

A CV integrada canônica está em
`memoria/neural/cv_catalogo_17_variantes_semantica_v8_minilm_integrado.json`.
Nos mesmos 3.106 exemplos, 611 grupos semânticos e cinco folds, ela obteve
falso comando `0,0446`, precisão de comando `0,9909`, recall `0,9618`, intenção
`0,9037`, ação `0,8973`, acerto conjunto `0,8942` e nenhuma negação perdida.
Ela substitui o benchmark isolado como prova da composição real. Os números
diferem porque `intent_gated` agora aplica o veto usando a intenção semântica
do próprio modelo integrado; o benchmark anterior preservava a decisão final
de comando do baseline lexical. O relatório continua declarando
`autoriza_execucao=false` e `autoriza_promocao=false`.

## Calibração OOD semântica

O conjunto `datasets/ood_calibracao_v0.jsonl` contém 200 comandos fora das 17
variantes do catálogo, em 20 famílias: 100 frases para escolher o limiar e 100
paráfrases reservadas para holdout. Esses exemplos não entram no treino das
cabeças de intenção, comando, negação ou ação.

O relatório
`memoria/neural/cv_catalogo_17_variantes_semantica_v10_ood_diagnostico.json`
falsificou a hipótese de que um único corte na confiança da intenção separaria
comandos conhecidos de comandos fora do catálogo:

- limitando falso aceite OOD a `1%`, o recall operacional conhecido caiu para
  `75,27%`;
- preservando recall conhecido em `85,10%`, o falso aceite OOD ficou em `5%`
  na calibração e `9,4%` no holdout.

Por isso, `ood_calibrated` continua falso para a representação semântica e não
há limiar recomendado. A normalização preserva esse estado, o gate operacional
rejeita candidatos não calibrados e o shadow não transforma um OOD ainda não
calibrado em falso “comando perdido”. O próximo experimento arquitetural deve
avaliar um owner específico para pertinência ao catálogo, separado das cabeças
de intenção e ação; ele não deve ser promovido antes de superar o mesmo holdout.

O primeiro detector binário (`ood_detector_v1`) foi preservado como diagnóstico
histórico, mas não como prova: as mesmas famílias OOD atravessavam treino,
calibração e avaliação. O `ood_detector_v2` corrige essa fronteira com 30
famílias inteiras e disjuntas, dez por partição. Nesse teste mais realista:

- a cabeça binária MiniLM + SGD, mantendo `85,14%` dos comandos conhecidos,
  aceitou `49,6%` dos OOD na calibração e `61,2%` no holdout;
- a distância aos protótipos das variantes conhecidas, mantendo `85,00%`,
  aceitou `27,8%` dos OOD já na calibração.

Ambas foram rejeitadas. Os relatórios são
`memoria/neural/benchmark_detector_ood_v2.json` e
`memoria/neural/benchmark_detector_ood_prototipos_v1.json`. Nenhum desses
detectores foi integrado ao modelo.

## Modelo semântico no shadow real

O artefato `memoria/neural/modelo_semantico_shadow.joblib` contém a configuração
`minilm-shadow-v1-3106`. Quando `LAYLAY_NEURAL_MODE=shadow`, esse arquivo existe
e `LAYLAY_NEURAL_MODEL_PATH` está vazio, a composição o seleciona apenas para
observação. Em qualquer outro modo, o padrão continua sendo
`modelo_ativo.joblib`; um caminho configurado explicitamente sempre prevalece.

O shadow não altera o turno, não concede autoridade e não executa. Mesmo se
alguém habilitar o gate experimental, `ood_calibrated=false` resulta em
`ood_nao_calibrado`. Assim, o runtime pode colher divergências e receipts reais
sem transformar a falha de OOD em permissão.

O benchmark pode usar `--estrategia logistic`, `sgd_log_loss` ou
`complement_nb`. A regressão logística continua sendo o padrão. Estratégias
alternativas são experimentais e o ciclo recusa promovê-las; elas precisam
primeiro superar generalização por famílias e depois todos os gates do Frozen.

Também existem duas arquiteturas experimentais, avaliáveis sem promoção:

- `--arquitetura-comando intent_gated` exige uma intenção conhecida para
  manter `is_command=true`. Se a cabeça binária sugerir comando com
  `intent=NONE`, o resultado final é vetado, os parâmetros executáveis são
  removidos e a observação bruta fica disponível para diagnóstico;
- `--arquitetura-acao hierarchical` escolhe a ação somente pela cabeça da
  intenção prevista, impedindo que uma intenção conhecida publique uma ação
  pertencente a outro owner.

Os padrões estáveis continuam `--arquitetura-comando independent` e
`--arquitetura-acao global`. Trocar qualquer arquitetura torna a configuração
experimental e o ciclo recusa `--promover-se-aprovado` até que o contrato seja
aprovado explicitamente após CV por famílias e Frozen.

## Relatório do modo shadow

O runtime compara a previsão com duas autoridades diferentes, sem criar outro
roteador:

- ao final do turno, compara comando executável com a autorização canônica já
  reconciliada com vetos, contexto e esclarecimentos;
- depois de uma ação, compara intenção e ação somente com receipt confirmado.

Os eventos append-only ficam em `memoria/neural/shadow_eventos.jsonl`, e o
resumo acumulado em `memoria/neural/shadow_relatorio.json`. O resumo separa
falso comando, comando perdido, divergência de intenção e divergência de ação,
inclusive por intenção. Texto completo só é retido nos casos divergentes; os
acordos guardam apenas o hash. Todo registro declara `autoriza_execucao=false`,
`apto_treino=false` e `predicao_propria_vira_label=false`: divergência indica um
caso para revisão, não um rótulo verdadeiro.

### Auditoria das evidências reais

O auditor fail-closed separa eventos antigos do modelo esperado, receipts que
servem apenas para revisão e correções explícitas confirmadas que podem formar
um lote candidato. Ele também separa correções pendentes, aprovadas e rejeitadas.
O treino consulta a última decisão válida por ID e, na ausência dela, mantém a
correção fora do dataset. O auditor não publica o texto das conversas, não
transforma divergência em label e não incorpora exemplos automaticamente ao
treino ou ao DEV:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.auditoria_shadow `
  --pasta-estado memoria\neural `
  --modelo-esperado minilm-shadow-v1-3106
```

O status `aguardando_sessao_modelo_esperado` significa que a Laylay ainda não
registrou um turno real com esse artefato. O status
`sem_correcoes_explicitamente_confirmadas` significa que a coleta existe, mas
ainda não há exemplos elegíveis. `sem_correcoes_pendentes_revisao` significa
que as correções existentes já foram rejeitadas. Mesmo quando houver correções
disponíveis, elas continuam em revisão e fora do treino e do DEV até aprovação.

## Onda `MUSIC_SEARCH` v3 em staging

O gerador `datasets/gerar_musica_search_onda_v3.py` produz um lote reproduzível
com 240 exemplos: 120 comandos afirmativos, 40 comandos negados e 80 hard
negatives. Somado aos exemplos canônicos e aos lotes candidatos anteriores, o
conjunto chega a 185 comandos `MUSIC_SEARCH`, dentro da meta de 150 a 200
exemplos por comando.

A validação cruzada por famílias, usando a mesma estratégia experimental
`sgd_log_loss` nos dois lados, mostrou ganho de compreensão mas regressão de
segurança:

- acurácia de intenção: `0.5544 -> 0.6397`;
- acurácia conjunta: `0.4715 -> 0.7208`;
- falso comando: `0.2857 -> 0.3800`;
- negação perdida: `0.0370 -> 0.1735`.

Por isso, a onda v3 permanece em staging: não foi incorporada ao DEV, não
alterou o modelo ativo e não habilitou influência operacional. O relatório de
CV agora também agrupa erros por família linguística para orientar a próxima
onda sem converter previsões do próprio modelo em rótulos.

## Ondas contrastivas v4 e volume v2

A onda `MUSIC_SEARCH` v4 mantém o volume da v3, mas distribui os mecanismos em
100 famílias menores. A onda `VOLUME` v2 adiciona 132 exemplos para `down`, 132
para `up` e 60 hard negatives. Com o DEV e os pilotos anteriores, a cobertura
chega a:

- `MUSIC_SEARCH:search`: 185 exemplos;
- `VOLUME:down`: 151 exemplos;
- `VOLUME:up`: 152 exemplos.

A representação experimental `tfidf_indicadores` acrescenta marcadores gerais
de negação e exclusão como atributos de aprendizado. Esses marcadores não
classificam, não autorizam e não executam. O limiar experimental de comando
`0.65` apenas veta propostas de baixa confiança; ambos preservam os padrões
anteriores quando não solicitados e impedem promoção automática.

Na validação cruzada por famílias dos 810 exemplos, o candidato obteve falso
comando `0.1059`, precisão `0.9536`, recall `0.8955`, intenção `0.8580` e
negação `0.9988`. No Frozen, porém, o recall caiu para `0.5294`: somente 3 das
17 variantes declaradas alcançaram a faixa de 150 a 200 exemplos. Portanto, o
candidato continua rejeitado e em shadow. O próximo passo é completar outras
variantes, sem afrouxar o gate e sem transformar o Frozen em treino.

## Onda navegador v1

O gerador `datasets/gerar_navegador_onda_v1.py` acrescenta 144 exemplos para
cada uma das variantes `CLOSE_TAB:close`, `OPEN_URL:open`, `LIST_TABS:list` e
`SEARCH:search`, além de 80 hard negatives. Na combinação com as ondas
anteriores, essas variantes alcançam respectivamente 150, 150, 150 e 151
exemplos DEV, deixando 10 das 17 variantes ainda abaixo da meta.

Nos 1.466 exemplos combinados não há duplicatas internas nem leakage com o
Frozen. A CV por famílias obteve falso comando `0.0981`, precisão `0.9723`,
recall `0.9461`, intenção `0.8950`, acerto conjunto `0.9330` e nenhuma negação
perdida. O Frozen ainda reprovou o estágio: falso comando `0.1429` e recall
`0.5882`. Nenhum dado do Frozen foi incorporado ao treino, nenhum modelo foi
promovido e o runtime permanece em shadow.

## Cobertura completa do catálogo v0

As ondas `apps_arquivos_onda_v1` e `iot_midia_clima_onda_v1` completam as dez
variantes restantes. O conjunto em staging possui 3.106 exemplos e todas as 17
variantes declaradas ficam entre 150 e 185 exemplos, com cotas mínimas de
famílias, negações e hard negatives atendidas em todos os domínios. A combinação
não possui duplicatas internas nem leakage com o Frozen.

Na CV por famílias, a configuração experimental obteve falso comando `0.0698`,
precisão `0.9859`, recall `0.9730`, intenção `0.9363`, acerto conjunto `0.9633`
e nenhuma negação perdida. O Frozen ainda rejeitou o candidato com falso
comando `0.1429` e recall `0.7647`, embora intenção tenha chegado a `0.9167` e
ação a `0.7059`. A cobertura completa não substitui generalização: o candidato
continua sem promoção, sem influência operacional e em shadow. Próximos ajustes
devem nascer de CV e receipts reais revisados, nunca de frases copiadas do
challenge.

## Candidato híbrido guiado pelo shadow real

A auditoria do shadow separou seis receipts reais confirmados para avaliação
reservada, sem transformá-los automaticamente em treino. O artefato semântico
ativo acertava somente um dos seis pares intenção/ação; o candidato híbrido com
o lote `shadow_mecanismos_v3` passou a acertar cinco. O sexto caso, `desliga a
luz`, revelou uma fronteira independente entre comando IoT e frases que apenas
descrevem hábito, estado, preferência ou planejamento.

O primeiro lote contrastivo amplo (`shadow_contrastivo_v2`, 207 exemplos) foi
rejeitado porque melhorava os receipts, mas piorava a validação global e a
negação. A correção arquitetural não foi aumentar dados cegamente. A
representação `onnx_semantico_hibrido` passou a combinar o vetor MiniLM com
atributos lexicais determinísticos para intenção e ação, enquanto gates de
comando e negação permanecem lexicais e independentes.

Exemplos agora podem declarar `training_heads`. Um lote especializado altera
somente os owners indicados; `intent`, `intent_gate`, `command`, `negation` e
`action` não compartilham escopo implicitamente. Hard negatives direcionados
podem declarar `command_head_intent`, criando uma cabeça de comando do domínio
sem contaminar o classificador global. A intenção principal seleciona essa
cabeça; o gate semântico continua apenas como veto de intenção desconhecida e
não assume ownership de outro domínio. Essa separação não concede autoridade e
não muda o executor.

Para comparações incrementais, `--estrategia-particao hash_estavel` atribui cada
grupo a um fold por hash. Assim, adicionar famílias não redistribui as famílias
antigas. `--lotes-base-comparavel` publica métricas somente da fatia histórica,
evitando comparar bases diferentes como se fossem o mesmo experimento. Limiar
por intenção também é aceito no treino e continua sendo configuração
experimental, bloqueada para promoção automática.

O lote `iot_fronteira_comando_v4` possui 168 exemplos: 66 comandos e 102 hard
negatives, em 56 grupos. Ele não contém frases dos seis receipts nem do Frozen,
e a auditoria encontrou zero duplicatas exatas, zero quase duplicatas e zero
famílias compartilhadas com o challenge. Na CV estável final:

- a fatia histórica de 3.106 exemplos manteve 26 falsos comandos e uma falsa
  negação;
- recall de comando ficou em `0,9494`, intenção em `0,9317`, ação em `0,9112`
  e acerto conjunto em `0,9100`, todos acima da linha híbrida estável anterior;
- no objetivo próprio do v4, 159 de 168 exemplos acertaram a fronteira
  comando/não-comando (`94,64%`): restaram três falsos comandos e seis comandos
  perdidos.

O artefato integral `hibrido-v3-iot-v4-168` acertou os seis receipts reais e
recuperou o recall do Frozen para `0,8235`, com precisão `1,0` e zero falso
comando. Ainda foi rejeitado: três comandos de outros domínios permanecem abaixo
do limiar global e o comando IoT `deixa a lâmpada acesa` recuperou a fronteira de
comando, mas ainda errou a ação. Portanto, nenhum modelo ativo foi substituído.
O próximo lote deve atacar action `on/off` e os comandos globais perdidos como
raízes separadas; não deve reutilizar frases reservadas como treino.

## Estados afirmativos e negação contrastiva

A auditoria da fronteira IoT encontrou rótulos semanticamente invertidos nos
geradores: frases como `mantenha o abajur desligado` e `deixa o abajur
funcionando` estavam representadas como negação da transição oposta. Quando a
ação inversa existe no catálogo, o contrato correto é um pedido afirmativo do
estado descrito. Os geradores de IoT/mídia e apps/arquivos agora materializam
esses casos como `negated=false` e com a ação canônica de destino. Para manter a
cobertura mínima depois da correção, foram acrescentadas 60 variações
afirmativas independentes: 12 de `CLOSE_APP:close`, 24 de `IOT_CONTROL:off` e
24 de `MEDIA_CONTROL:pause`.

Uma cabeça de negação hierárquica e uma variante híbrida foram testadas e
rejeitadas. Elas acertaram o Frozen, mas perderam respectivamente 79 e 28
negações na CV por grupos. A arquitetura permaneceu global. A solução aprovada
para continuar em staging foi ensinar cada owner explicitamente:

- os 66 comandos afirmativos do `iot_fronteira_comando_v4` treinam `command` e
  `negation`; seus 102 não-comandos continuam exclusivos de `command`;
- o lote `negacao_contrastiva_v5` traz 108 exemplos, 54 afirmativos e 54
  negados, em 36 grupos, e treina somente `negation`;
- `command_head_intent` continua selecionando apenas a cabeça de comando, mas
  pode coexistir com outros heads declarados em `training_heads`.

Não há frases dos 24 itens Frozen nem dos seis receipts no v5. A auditoria
registrou zero duplicatas exatas, zero quase duplicatas e zero famílias
compartilhadas. Na CV estável da combinação v4+v5, a fatia histórica ampliada
para 3.166 exemplos obteve precisão de comando `0,9898`, recall `0,9487`,
intenção `0,9362`, ação `0,9272` e acerto conjunto `0,9260`. A negação ficou em
`0,9940`, com cinco falsas negações e 14 negações perdidas. Como controles,
antes da ampliação v4 sozinho somou 28 erros históricos de negação; v5 sozinho
somou 16, mas não corrigiu o caso reservado; a combinação anterior somou 17.
Depois da ampliação, a combinação soma 19 e continua corrigindo o caso.

O artefato `hibrido-v3-iot-v4-negacao-v5-v3` interpreta `deixa a lâmpada
acesa` como `IOT_CONTROL:on`, comando afirmativo e não negado, preserva recusas
explícitas e acerta os seis receipts em intenção/ação. No Frozen, obteve
negação `1,0`, ação `0,8235`, precisão de comando `1,0` e recall `0,8235`.
Na leitura completa dos receipts, quatro de seis também atravessam o limiar de
comando; `liga a luz` e `desliga a luz` preservam intenção/ação, mas ficam em
`0,6019` e `0,6028`, abaixo do limiar global `0,65`.
Ele continua rejeitado por `command_recall_fora_do_limite`; nenhum modelo ativo
foi substituído e a próxima raiz permanece nos três comandos globais abaixo do
limiar, além da preservação desses dois imperativos curtos de IoT.

## Fronteiras dirigidas de comando v6

O lote `fronteiras_comando_v6` adiciona 252 exemplos em 82 grupos para os
owners `IOT_CONTROL`, `OPEN_URL`, `MUSIC_SEARCH` e `WEATHER`: 108 comandos e
144 não-comandos. Todos treinam exclusivamente `command`, com
`command_head_intent` explícito. A auditoria contra o Frozen e os seis receipts
registrou zero duplicatas exatas, zero quase duplicatas e zero famílias
compartilhadas.

O primeiro candidato v6 tornou precisão e recall de comando do Frozen iguais a
`1,0`, mas a CV histórica expôs a raiz arquitetural: um head dirigido reunia os
comandos globais do intent e ignorava os hard negatives globais do mesmo
domínio. Isso elevou os falsos comandos históricos de 26 para 55. O treinador
agora reutiliza os não-comandos globais do domínio do owner, sem absorver
negativos de outros domínios. Um teste inspeciona o vocabulário efetivamente
entregue ao head, em vez de inferir a composição por resultado final.

Com essa correção e calibração apenas de `MUSIC_SEARCH=0,75` e
`WEATHER=0,725`, o candidato experimental
`hibrido-v3-iot-v4-negacao-v5-cmd-v6-cal-v8` obteve no Frozen precisão e recall
de comando `1,0`, negação `1,0` e ação `0,9412`. Ele reconhece os quatro alvos
reservados desta etapa e os seis receipts completos como comandos, com intenção
e ação corretas. Na base comparável de 3.166 exemplos, precisão passou de
`0,9898` para `0,9902`, recall de `0,9487` para `0,9491` e falsos comandos de 26
para 25; intenção e negação permaneceram iguais.

O lote ainda não foi promovido. Na validação apenas das 252 famílias novas, a
precisão de comando foi `0,9213`, o recall `0,7593` e a taxa de falso comando
`0,0486`. Ensinar também o `intent_gate` foi falsificado: o recall novo subiu
para `0,8148`, mas os falsos comandos históricos aumentaram para 36; essa
variante foi retirada. A próxima fronteira é ampliar mecanismos realmente
independentes e tornar a CV consciente de `training_heads`, para não cobrar
intent/action/negation de lotes que treinam somente command. Nenhum modelo ativo
foi substituído.

## Expansão por mecanismos v7 e avaliação por owner

A avaliação agora respeita `training_heads`: cada métrica usa somente exemplos
que pertencem ao owner avaliado. A ação é comparada pelo `raw_action`, enquanto
`params` continua representando apenas a conclusão operacional permitida pelo
gate. O diagnóstico também publica intenção lexical, confiança, escopo, limiar
e motivo do veto, sempre como evidência sem autoridade de execução ou promoção.

O lote `expansao_mecanismos_v7` possui 126 exemplos, 78 comandos e 48
não-comandos em 39 grupos. Música e clima ampliam mecanismos positivos; IoT e
navegador recebem hard negatives dirigidos. As três variações `OPEN_URL` e as
três variações musicais elípticas treinam exclusivamente `command`, pois os
erros observados já chegavam com intenção e ação corretas. A auditoria contra
dados anteriores, Frozen e receipts encontrou zero duplicatas ou famílias
compartilhadas.

O gate `intent_gated` ganhou um fallback semântico opcional e calibrado por
intent. Somente `WEATHER=0,60` foi aceito: libera uma proposta quando a intenção
semântica está forte, mas o gate lexical não reconheceu a forma. A arquitetura
sem gate lexical e um fallback global foram rejeitados por aumentarem falsos
comandos. Os limiares finais do candidato são `MUSIC_SEARCH=0,755`,
`OPEN_URL=0,66`, `WEATHER=0,725` e global `0,65`.

Na CV agrupada de 3.904 exemplos, a candidata v18 obteve precisão de comando
`0,9873`, recall `0,9394`, 35 falsos comandos, intenção `0,9371`, ação
`0,9508`, acerto conjunto `0,9498` e negação `0,9925`. Na fatia histórica
comparável, manteve 26 falsos comandos e elevou recall para `0,9487`. No Frozen,
precisão e recall de comando foram `1,0`, com zero falso comando, negação `1,0`
e ação `0,9412`; os seis receipts reais também passaram integralmente.

A sonda telegráfica `acha canção amor` ainda fica em `0,7424`, abaixo do limiar
musical `0,755`. Tentar aproximar os exemplos dessa frase piorou recall e
adicionou falsos comandos, portanto essa variante foi rejeitada. A v18 permanece
como candidata isolada, sem promoção e sem alterar o modelo ativo; essa elipse é
a próxima fronteira contrastiva.

## Contraste telegráfico v8

O lote `contraste_telegraphico_v8` resolve a elipse sem copiar a sonda
reservada. São 18 exemplos balanceados em seis grupos: nove pedidos curtos com
`acha`, `busca` e `encontra`, e nove não-pedidos que contrastam primeira pessoa,
opinião de terceiro e descrição de capacidade musical. Todos treinam
`command`; somente as três variantes de `acha` treinam também `intent_gate`,
pois a CV provou que esse era o primeiro owner em RED. Nenhum exemplo treina
ação, negação, autoridade ou execução.

Os grupos por alvo mantêm pedido e não-pedidos semanticamente próximos na mesma
partição. A auditoria contra todos os lotes anteriores, Frozen e receipts
registrou zero duplicatas exatas, zero quase duplicatas e zero famílias
compartilhadas. Um fallback semântico específico de `MUSIC_SEARCH=0,75` foi
aceito porque a fronteira diagnóstica não continha não-comandos nessa faixa; o
head de comando ainda precisa ultrapassar `0,755`.

Na CV de 3.922 exemplos, a candidata v26 obteve precisão de comando `0,9881`,
recall `0,9409` e 33 falsos comandos. Na fatia histórica, obteve precisão
`0,9902`, recall `0,9498` e 25 falsos comandos, melhorando os três valores da
v18. Intenção (`0,9371`), ação (`0,9508`), acerto conjunto (`0,9498`) e negação
(`0,9925`) foram preservados. O lote v8 passou `18/18` na CV.

No artefato integral, `acha canção amor` passou como
`MUSIC_SEARCH/search` com probabilidade `0,8029`; `acho canção de amor bonita`,
`ela acha canção de amor bonita` e a descrição sobre música em apresentações
permaneceram não-comandos. Frozen manteve precisão e recall de comando `1,0`,
zero falsos comandos e negação `1,0`; os seis receipts reais passaram. A v26
continua não promovida.

### Validação shadow da v26 no runtime

O script `validar_neural_v26_shadow_composicao.py` valida, pelo carregador e
pelas fronteiras reais do orquestrador, o hash exato da v26, sete sondas
contrastivas, a persistência da telemetria e a preservação do modelo ativo. O
ensaio grava somente em pasta temporária e exige `autoriza_execucao=false`,
`apto_treino=false` e `predicao_propria_vira_label=false` em todos os eventos.

Em seguida, `roteiro_neural_v26_shadow_seguro.py` passou pelo runtime completo
com três frases não operacionais. O auditor encontrou três eventos da versão
esperada, todos em `SHADOW`, todos concordantes como não-comandos, sem receipts
e sem efeito executado. A primeira inferência incluiu a carga tardia do modelo
(`7.383,203 ms`); depois disso, a mediana observada foi `18,548 ms`. O hash do
`modelo_ativo.joblib` permaneceu inalterado. A candidata está configurada para
continuar coletando evidência no uso real, ainda sem autoridade e sem promoção.

### Caos completo da v26

O runtime real `roteiro_teste_laylay_caos-20260904-051237-659508` concluiu os
267 turnos. A avaliação semântica marcou 46 de 49 casos como corretos
(`93,88%`); as três falhas foram fallbacks conversacionais para entradas
degradadas e pertencem a outra fronteira, não ao executor neural. Durante o
intervalo, a v26 registrou 405 eventos shadow (267 comparações de turno e 138
de receipt), sempre com `somente_observacao=true`,
`autoriza_execucao=false`, `apto_treino=false` e
`predicao_propria_vira_label=false`. Depois da carga do modelo, a latência foi
`p50=12,707 ms`, `p95=19,772 ms` e máximo de `32,715 ms`.

A comparação contra os casos semanticamente avaliados mostrou precisão de
comando `0,75`, recall `0,25` e taxa de falso comando `0,2308`. O caos executou
32 intenções distintas, enquanto a v26 conhece apenas 13 intenções operacionais
mais `NONE`; além disso, houve 12 turnos multi-intenção e o modelo ainda produz
uma única intenção por entrada completa. Portanto, a primeira fronteira atual é
de cobertura e granularidade, não apenas de limiar. A v26 continua segura em
shadow, mas não está apta para promoção.

A mesma auditoria revelou duas correções históricas falsamente confirmadas por
execuções de turnos posteriores. O runtime agora exige identidade textual entre
a correção e o receipt que a conclui. Os dois registros originais foram
preservados e rejeitados no ledger; nenhum deles pode entrar em treino.

### Base segmentada para a v27

O caos também provou que comparar somente a entrada inteira escondia perdas em
turnos multi-ação. O observador neural agora reutiliza exclusivamente os
segmentos produzidos por `modalidade_turno`: não possui segmentador privado e
continua sem autoridade. A comparação shadow mede cada segmento separadamente,
além da compatibilidade agregada do turno.

Receipts de uma entrada com mais de um segmento neural executável ficam com o
status `receipt_multi_segmento_nao_correlacionado`. Enquanto o runtime não
publicar uma identidade receipt→segmento verificável, eles não contam como
concordância nem divergência de intenção ou ação. Isso impede escolher a
previsão mais conveniente depois de observar o efeito.

`validar_neural_v26_shadow_composicao.py` foi ampliado sem alterar o artefato:
duas frases compostas produziram quatro segmentos comparáveis, quatro
concordâncias por segmento, nenhuma divergência e zero ações executadas. A
frase contrastiva `não abra o opera, mas abaixa o volume` preservou o veto no
primeiro ato e o comando no segundo. O hash do modelo ativo permaneceu igual.

Pelos receipts do caos, a próxima onda de cobertura deve começar por intenções
de leitura ausentes e frequentes: `LIST_WINDOWS` (7 ocorrências), `IOT_STATUS`
(5), `MUSIC_STATUS` (4), `LEARNING_QUERY` (3), `PLAYLIST_LIST` (2),
`PEOPLE_QUERY` (2) e `RESUMIR_PAGINA` (2). Intenções mutáveis como
`CREATE_FILE`, `DELETE_ITEM` e `ORGANIZAR_DESKTOP` permanecem em uma onda
posterior, com gates de segurança próprios. Esta etapa prepara a v27, mas ainda
não cria, treina ou promove um novo modelo.

### Primeira fronteira v27: extensão aditiva de intenção

O primeiro alvo investigado foi `LIST_WINDOWS`. O runtime canônico já reconhece
essas consultas e publica receipts confirmados, mas o artefato v26 não possui a
classe: perguntas de inventário eram desviadas para `APP_OPEN`, `MEDIA_CONTROL`,
`LIST_TABS` ou `NONE`. Retreinar a cabeça multiclasse inteira foi rejeitado. Na
fatia histórica, a expansão para a 15ª classe alterou decisões antigas mesmo
quando `command` não era treinado; o melhor ensaio integral manteve recall de
comando `0,9409`, mas elevou falsos comandos de 33 para 40.

`modelo.py` agora possui um contrato geral de extensão one-vs-rest. Ele treina
um detector lexical separado e o anexa a uma cópia do modelo-base. Somente uma
extensão única acima do próprio limiar pode substituir `intent`, `gate_intent`
e a proposta de ação. Nenhuma correspondência preserva a saída-base integral;
duas correspondências também preservam a base, sem desempate oportunista. Os
gates de comando e negação não são recalculados, e a normalização do runtime
continua impondo `somente_observacao=true` e `autoriza_execucao=false`.

O lote `list_windows_onda_v1.jsonl` contém 198 exemplos: 150 da intenção
(`120` afirmativos e `30` negados), 48 hard negatives, 50 famílias e 46 grupos
de validação. Ele treina intent/action e uma fatia balanceada de negação, mas
não treina `command`. Todas as formas afirmativas alcançam o interpretador
canônico; receipts reservados são proibidos no treino.

Os candidatos ainda foram rejeitados. A primeira versão, com entidades
repetidas entre moldes, aparentou recall out-of-fold de `0,92` no limiar
`0,925`, mas acertou somente 1/5 dos receipts reais reservados: o resultado
estava inflado pelo reaparecimento dos mesmos nomes em famílias distintas. A
diversificação chegou a 3/5. Após balancear entidades masculinas, femininas,
curtas e compostas por mecanismo, uma terceira reserva inédita chegou a 8/10,
mas a validação por grupos linguísticos obteve apenas `0,7533` de recall e dois
falsos positivos entre os contrastes novos. Dar peso geral a sufixos elevou o
recall para `0,90`, porém criou 27 falsos positivos contrastivos, portanto essa
representação também foi descartada.

Os artefatos rejeitados permanecem apenas em
`memoria/neural/experimentos/v27_list_windows_onda_v1/`; nenhum foi copiado para
`modelo_ativo.joblib` ou configurado no runtime. O hash ativo continuou
`07C539917EAE7792B2B4ECB1F0335697802FC7F6672E920656F8C5DFC2289E62`.

O schema de dataset e a validação cruzada agora aceitam também
`validation_entity_group`, sem substituir o `validation_group` linguístico.
Isso permite duas provas independentes. No limiar `0,925`, o detector lexical
obteve recall `0,7533` por molde, com zero falso positivo histórico e dois nos
contrastes novos; isolando entidades, obteve recall `0,56`, sem falsos
positivos. O encoder semântico híbrido da v26 não resolveu a fronteira: no eixo
de entidade ficou em `0,4867`, com dois falsos contrastivos. Dois detectores por
subtipo e a redução dos negativos aos domínios vizinhos também foram
rejeitados; esta última chegou a 129 falsos históricos.

A próxima fronteira é uma representação que generalize slots de entidade e
atos de consulta sem receber o rótulo do parser canônico. Até isso ser provado
nos dois eixos, `LIST_WINDOWS` permanece somente como dataset/candidato de
pesquisa, e a extensão aditiva não entra no runtime.

### Candidata v27 em shadow: consultas de estado de janelas

A separação por subtipo mostrou que o agregado anterior escondia duas tarefas
distintas. Perguntas sobre o estado de um aplicativo (`extension_scope` igual a
`estado_alvo`) generalizavam melhor do que pedidos amplos de inventário. A
extensão continua geral e one-vs-rest, mas agora pode selecionar explicitamente
um escopo de dataset. Isso não cria uma regra privada de linguagem no executor:
o dataset declara a fatia e o modelo continua sendo apenas proponente.

A representação `estrutura_bordas` usa marcadores genéricos de tamanho, prefixo
e sufixo, sem receber intenção, rótulo ou resultado do parser canônico. No
limiar `0,925`, a validação agrupada da fatia `estado_alvo` obteve recall
`0,8750` por família linguística e `1,0000` por entidade, com zero ativação nos
negativos históricos e zero nos novos exemplos `NONE`. No ajuste integral, as
25 reservas externas passaram. O Frozen permaneceu 24/24 idêntico ao modelo
base e os 12 contrastes também permaneceram bit a bit iguais.

O artefato
`modelo_candidato_extensao_estado_estrutura_v4.joblib`, versão
`hibrido_v26_ext_list_windows_estado_estrutura_v4_v27`, tem SHA-256
`CAAA93027EB96451CBBF1C61136389AC8402533226C666225DA3A2DEF356E0CF`.
Ele está configurado em `LAYLAY_NEURAL_MODE=shadow`; não substituiu
`modelo_ativo.joblib` e não ganhou autoridade operacional.

`validar_neural_v27_list_windows_shadow_composicao.py` verificou o caminho real
da configuração, 5 sondas-alvo, 6 contrastes, 11 eventos somente-observação,
zero ações e preservação do hash ativo. Depois, o runtime completo
`roteiro_neural_v27_list_windows_shadow_seguro-20260904-184122-110250` consultou
Opera, Ferramenta de Recortes e Krita no sistema local. Os três turnos e seus
três receipts foram concordantes como `LIST_WINDOWS`; nenhuma consulta
autorizou efeito mutável ou virou rótulo de treino.

O runtime também revelou duas observações separadas desta candidata. O alvo de
`O editor Krita ainda está aberto?` foi extraído como `editor krita ainda`, e a
base v26 marca `A microsoft store está aberta?` como negada. Ambas pertencem aos
donos canônicos de entidade/negação e não devem ser corrigidas dentro da
extensão de intenção. A v27 permanece em shadow para ampliar evidência antes de
qualquer promoção.

### Caos adversarial LIST_WINDOWS da v27

O roteiro `roteiro_neural_v27_list_windows_caos.py` amplia a prova para 70
turnos, todos com expectativa determinística: consultas diretas, verbos
alternativos, prefácios naturais, pontuação, continuidade pronominal,
inventário e contrastes de domínio. O avaliador passou a verificar também o
alvo exato dos receipts e tokens que não podem vazar para ele. O contrato foi
criado primeiro em RED: `editor krita ainda` passava apenas porque intenção e
status estavam corretos; depois da ampliação, o avaliador rejeitou o alvo.

O runtime real
`roteiro_neural_v27_list_windows_caos-20260904-185258-859543` obteve 35/70
casos corretos (`50%`), com 35 falhas e nenhum alerta semântico. O turno 64,
`Como eu perguntaria se o Opera está aberto?`, foi repetido por retomada segura
e nas duas tentativas publicou um receipt `LIST_WINDOWS` para um alvo incorreto,
mas não entregou fala em 120 segundos. Portanto, o turno silencioso é
reproduzível e não foi tratado como simples flutuação de latência.

As 35 falhas se agrupam em contratos, não em 35 patches:

- marcadores temporais como `ainda` vazam para o alvo;
- prefácios como `será que`, `por acaso` e `me diz se` viram parte do alvo;
- `permanece`, `segue` e `em execução` escapam do leitor local;
- pronomes `ele` e `ela` não reutilizam a última entidade confirmada;
- formas naturais de inventário ficam sem receipt apesar de dados disponíveis;
- substantivos de outros domínios (`porta`, `inscrição`, `arquivo`, `aba` e
  `menu`) são aceitos como nomes de aplicativo;
- a normalização de `opera tá aberto?` removeu o primeiro caractere e consultou
  `pera`;
- uma consulta metalinguística pode ser consumida sem conclusão observável.

No mesmo conjunto adversarial, a candidata v27 propôs `LIST_WINDOWS` com 25
verdadeiros positivos, 22 falsos negativos, 9 falsos positivos e 14 verdadeiros
negativos: precisão `0,7353` e recall `0,5319`. A fatia de inventário ainda não
é coberta pela extensão `estado_alvo`, como esperado, mas os falsos positivos
em citações, afirmações e outros domínios impedem promoção. A rodada registrou
110 eventos shadow, incluindo a retomada: 71 comparações de turno e 39 de
receipt. Todos permaneceram somente-observação, sem autoridade e sem usar a
própria previsão como rótulo. O modelo ativo continuou intocado.

`analisar_neural_v27_list_windows_caos.py` reproduz o cruzamento entre o
checkpoint, as expectativas, a v26, a candidata v27 e o ledger shadow. A
próxima fronteira é separar canonicamente `ato de consulta`, `entidade de app`
e `alvo resolvido`; ampliar somente o vocabulário ou baixar o limiar repetiria
os falsos positivos encontrados pelo caos.

### Correção canônica após o caos LIST_WINDOWS

A separação proposta acima foi implementada fora do classificador neural. O
pré-fluxo agora distingue o ato de pergunta dos prefácios e marcadores
temporais, consulta o estado real pelo resolvedor existente e só publica o
receipt quando um catálogo read-only comprova o domínio de aplicativo. Esse
catálogo combina `APPS_MAP`, os nomes descobertos pelo AppOpener e a evidência
de uma janela realmente observada; ele não abre, fecha nem autoriza apps.

O receipt confirmado `LIST_WINDOWS/estado_app_consultado` passou a poder
estabelecer `ultimo_app_janela`, pois prova qual alvo foi lido. O inventário
plural `janelas_listadas` não recebe essa promoção. Também foi removido o
acoplamento incorreto entre veto de mutação e consulta read-only: uma
deliberação como `Eu queria saber quais janelas estão abertas` pode observar o
sistema, mas continua sem autorizar qualquer executor mutável.

Dois ciclos reais provaram a progressão no mesmo roteiro de 70 turnos:

- `roteiro_neural_v27_list_windows_caos-20260904-232148-199355`: 65/70; as
  únicas falhas restantes eram quatro continuidades sem referente e uma
  consulta indireta bloqueada pelo veto de mutação;
- `roteiro_neural_v27_list_windows_caos-20260904-232713-287151`: 70/70,
  70 respostas, zero falhas e zero alertas semânticos.

O teste revelou ainda uma contradição no staging neural: as 48 consultas
direcionadas eram geradas sem `?`, ensinando afirmações como `o Discord está
aberto` como `LIST_WINDOWS`. O gerador e o JSONL de staging foram corrigidos
para produzir perguntas explícitas; o joblib v27 configurado não foi retreinado.
A suíte neural completa passou com 136
testes. Isso não promove a candidata v27 existente: ela conserva precisão
`0,7353`, recall `0,5319` e 9 falsos positivos no caos. Foram observados 117
eventos shadow na última rodada, todos sem autorização ou auto-rotulagem, e o
hash do modelo ativo permaneceu
`07C539917EAE7792B2B4ECB1F0335697802FC7F6672E920656F8C5DFC2289E62`.

Respostas livres ruins em citações, negações e perguntas metalinguísticas
continuam registradas como uma raiz conversacional separada; o 70/70 acima
prova o contrato operacional/semântico do roteiro, não a qualidade textual de
todas as falas da LLM.

### Avaliação v28 por fatores e grupos — 2026-09-05

Base da investigação: `main`, HEAD
`a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, com worktree já modificada.
As alterações paralelas foram preservadas; nenhum commit foi criado.

A reanálise do caos real
`roteiro_neural_v27_list_windows_caos-20260905-130443-326372` confirmou
70/70 turnos respondidos e aprovados pelo contrato operacional. O analisador
agora recupera os planos completos em `planos.jsonl`, cruzando índice e comando:
o checkpoint compacto omitia informações e produzia uma reavaliação incorreta
de 58/70. Os 70 planos completos estavam disponíveis. O leitor compartilhado
tolera e contabiliza uma linha inválida no ledger shadow, sem modificar o
arquivo nem declarar sua integridade: status `analisado_com_artefatos_degradados`.
Os 117 eventos válidos dessa sessão continuam somente-observação, sem
autorização ou auto-rotulagem. A v27 mantém TP=25, FN=22, FP=9 e TN=14.

O novo staging `datasets/candidatos/list_windows_onda_v2.jsonl`, reproduzível
por `datasets/gerar_list_windows_onda_v2.py`, contém 705 exemplos: 298 consultas
ativas e 407 contrastes, 336 famílias, 100 grupos linguísticos e 85 grupos de
entidade. As frases exatas do caos conhecido são excluídas, preservando
diferenças estruturais de pergunta/citação. Isso **não torna o caos uma reserva
independente**: ele já orientou a investigação e é regressão de desenvolvimento.

Este dataset é especializado na extensão `consulta_ativa`, não na taxonomia
global de comandos: negações de consultas são negativas para ativar a extensão.
Não se deve mesclá-lo cegamente ao treino multiclasse. O campo opcional
`extension_factors` distingue `ato_consulta` e `dominio_app`; suas conjunções
devem corresponder ao rótulo final. São 451 positivos de ato e 552 de domínio.
Nenhum desses rótulos ou escores concede autoridade de execução.

Foram adicionados dois mecanismos experimentais gerais:

- `estrutura_pontuacao` conserva marcadores de interrogação final e citação
  total. A função antiga `estrutura_bordas` permanece intacta, pois joblibs
  existentes referenciam essa função ao inferir.
- A extensão fatorada treina detectores independentes e só propõe intenção
  quando todos atingem o limiar. O mínimo dos escores não é uma probabilidade
  conjunta calibrada. Fator ausente, malformado ou escore inválido não pode
  eliminar uma condição; falha na inferência preserva a previsão-base.

`validacao_extensao.py` executa cinco folds, ajustando representações e
classificadores somente no treino de cada fold. Famílias linguísticas e
entidades são avaliadas em eixos separados; um eixo não prova isolamento do
outro. O relatório registra previsões out-of-fold, escores individuais,
matrizes, grupos, hashes dos insumos/código e versões do ambiente. Os textos
não são copiados para o relatório, apenas seus hashes.

Comparação em limiar fixo `0,5`, como referência diagnóstica, não como escolha
de implantação (P = precisão, R = recall da extensão):

| Representação | Famílias: P / R / falsos positivos | Entidades: P / R / falsos positivos |
| --- | --- | --- |
| Monolítica com pontuação | 63,5% / 75,8% / 130 | 82,8% / 88,9% / 55 |
| Fatorada lexical | 69,6% / 75,2% / 98 | 92,7% / 84,9% / 20 |
| Ato com pontuação + domínio lexical | 75,6% / 79,2% / 76 | 94,2% / 82,2% / 15 |

Relatórios preservados em
`memoria/neural/experimentos/v28_list_windows_avaliacao/`:
`cv_monolitica.json`, `cv_fatorada_lexical.json` e `cv_fatorada_pontuacao.json`.
Para reproduzir a terceira avaliação, usando um caminho de saída novo:

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.validacao_extensao `
  --modelo-base memoria/neural/experimentos/hibrido_v3_iot_v4_negacao_v5_cmd_v6_exp_v7_telegraphic_final_v8_v26/modelo_candidato.joblib `
  --dataset mente_laylay/neural/datasets/candidatos/list_windows_onda_v2.jsonl `
  --intent LIST_WINDOWS --action list --escopo consulta_ativa `
  --fator ato_consulta=estrutura_pontuacao --fator dominio_app=tfidf `
  --saida memoria/neural/experimentos/v28_list_windows_avaliacao/cv_fatorada_pontuacao_repeticao.json
```

A CLI recusa sobrescrever relatórios, não persiste os modelos dos folds e
confere que os insumos não mudaram durante a avaliação. Para a monolítica,
substituir os dois `--fator` por `--representacao estrutura_pontuacao`; para a
fatorada lexical, usar `ato_consulta=tfidf`. A varredura de limiares é
diagnóstica: a seleção final exige validação independente.

**Conclusão: v28 não aprovada para promoção.** A fatoração melhorou algumas
medidas, mas não eliminou a primeira fronteira de linguagem. No eixo de
famílias, o fator de ato com pontuação teve 64 falsos positivos: 16 em cada
grupo de hipótese de estado, hipótese de abrir, afirmação de permanência e
metalinguagem. Também perdeu as 16 consultas da família `consulta_permanece`.
O catálogo canônico pode apoiar a resolução de aplicativos, mas não foi
demonstrado que resolva esse erro de ato; injetar o resultado do parser agora
mascararia a lacuna neural.

Verificação desta etapa: 162 testes aprovados nos módulos de linguagem neural,
validação da extensão, auditoria shadow e analisador do caos. A verificação de
composição v27 publicou 11 eventos somente-observação e zero ações. A reanálise
70/70 usa artefatos de uma sessão real anterior, não uma nova execução completa
da Laylay. O hash ativo e o hash da candidata v27 configurada permaneceram os
registrados acima. Nenhum modelo v28 foi salvo ou configurado; gates globais,
autoridade, executores e composição da Laylay não foram alterados nesta etapa.

Próxima fronteira: investigar os contrastes de ato por família sem incorporar
as próprias previsões como rótulos; preparar uma reserva inédita antes de
novas escolhas de representação/limiar; depois exigir preservação da fatia
histórica e prova no runtime antes de ampliar a influência da extensão.

### Complemento de atos v3: comparação com prova fixa — 2026-09-05

O controle com ajuste integral acertou as 80 frases das cinco famílias críticas
(hipótese de estado, hipótese de abrir, permanência afirmada, metalinguagem e
consulta com `permanece`). A previsão out-of-fold anterior errava essas 80
frases quando suas famílias eram retidas. Isso afasta a hipótese de simples
incapacidade de ajustar essas amostras, mas não prova compreensão: a fronteira
observada é generalização entre famílias, não funcionamento do executor.

Antes de avaliar a ampliação, foi criada a reserva sintética
`datasets/reservas/list_windows_ato_v1.json`: 24 frases, com as quatro
combinações de ato/domínio, entidades e redações novas. Seu SHA-256 é
`D23E1E596136BD4DC4D45FA033DC57B2371267D02F2D40C6D019B87685301A67`.
Nenhuma previsão foi consultada nessa reserva nesta etapa. Ela não é amostra
independente de usuários; depois de avaliar um candidato nela, ajustes
posteriores exigirão uma nova reserva de confirmação. O formato é separado
do schema de treino, e a auditoria não encontrou colisões textuais normalizadas
com os JSONLs atuais de candidatos, DEV e Frozen. Isso não prova ausência de
similaridade semântica.

`datasets/gerar_list_windows_atos_v3.py` gera um complemento de 320 frases:
128 positivas, 192 negativas, 15 grupos e 16 entidades. Os rótulos são manuais,
não derivados de previsões ou receipts. Variantes de mecanismos históricos
mantêm seus grupos antigos. O staging está em
`datasets/candidatos/list_windows_atos_v3.jsonl`; não foi mesclado aos dados
do modelo ativo.

O contrato reutilizável de `validacao_extensao.py` agora aceita
`exemplos_complementares` / CLI `--complemento`: a âncora determina os folds e
permanece a única prova, enquanto o complemento participa somente do treino.
Qualquer complemento do grupo retido é excluído naquele fold. Duplicatas
textuais normalizadas, grupos ausentes e fatores contraditórios abortam antes
do treino. Cinco testes inicialmente RED por API ausente passaram após a
implementação, exercitando os classificadores reais e os dois eixos.

A comparação repetiu a configuração anterior, sem escolher novo limiar:
`ato_consulta=estrutura_pontuacao`, `dominio_app=tfidf`. No limiar fixo `0,5`:

| Prova fixa de 705 frases | Sem complemento | Com complemento |
| --- | --- | --- |
| Famílias: precisão / recall / FP | 75,64% / 79,19% / 76 | 75,24% / 80,54% / 79 |
| Entidades: precisão / recall / FP | 94,23% / 82,21% / 15 | 94,16% / 81,21% / 15 |

Os hashes das frases, seus rótulos e os folds são idênticos nas duas avaliações.
Houve 15 correções e 14 regressões no eixo linguístico; no eixo de entidade,
3 correções e 6 regressões. Os quatro grupos críticos de negativos continuam
com 16 falsos positivos cada no fator de ato. Portanto, aumentar exemplos
nessa forma não resolveu a fronteira; o complemento não foi aprovado para
promoção. Também não se pode concluir que aumentar dados nunca ajude.

Relatórios em `memoria/neural/experimentos/v28_list_windows_avaliacao/`:
`cv_ancora_atos_v3_controle.json` e `cv_complemento_atos_v3.json`. O controle
reproduziu as métricas da etapa anterior com o avaliador novo. Para repetir a
comparação, usar o comando anterior de validação, um novo `--saida`, e
acrescentar ao ensaio com complemento:

```text
--complemento mente_laylay/neural/datasets/candidatos/list_windows_atos_v3.jsonl
```

Validação: 173 testes aprovados, incluindo isolamento de complemento nos dois
eixos, rejeição de contaminação, reprodução do staging e preservação dos
contratos neurais existentes. Mudanças limitadas ao avaliador offline,
gerador/staging experimental, reserva, testes e documentação. `modelo.py`,
`laylay.py`, gates e executores não foram alterados nesta etapa. Nenhum modelo
novo foi salvo/configurado, nem houve nova sessão completa de caos.
A checagem de composição v27 voltou a produzir 11 eventos shadow, zero ações
e os mesmos hashes do modelo ativo e da candidata configurada.

Próxima fronteira: comparar representações do ato na mesma âncora, investigando
quais informações linguísticas se perdem ou ficam subponderadas. A reserva
permanece sem resultados até existir um candidato escolhido apenas pela
validação de desenvolvimento; depois ainda serão necessárias a fatia histórica
e a prova no runtime. Não ampliar catálogo ou baixar gates para compensar as
falhas observadas nesta avaliação.

### Contratos linguísticos e representação integral v1 — itens 1 e 2

Etapa autorizada em 2026-09-05, ainda sobre `main` / HEAD
`a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, preservando a worktree modificada.
Treinos continuam pausados. Esta entrega prepara diagnóstico e representação;
não instala outro modelo, não adapta pesos nem amplia a autoridade neural.

**Bateria de desenvolvimento:**
`tests/fixtures/neural/bateria_linguistica_v1.json` contém 44 casos e 32
relações entre pares, cobrindo volume, música, aplicativos e arquivos. Cada
domínio contém pedido, polidez, negação, hipótese, citação, metalinguagem,
comentário, correção, referência sem contexto, pedido longo e negação no meio.
As expectativas são manuais e não derivam de um parser ou de previsões. Não é
dataset de treino nem uma reserva independente.

`dominio_da_fatia` serve para organizar a cobertura, não para fornecer a
resposta ao modelo. As referências não possuem alvo literal resolvido. Os
rótulos `pedido_operacional` e `negacao_do_pedido` descrevem comportamento
linguístico esperado, não substituem os heads globais nem são permissões.
Todas as fixtures declaram `autoriza_execucao=false`. Uma correção como
`coloca o volume em 30, não em 50` pede definição do nível 30: não é recusa do
pedido inteiro, nem necessariamente diminuição do volume atual.

**Primeira fronteira reproduzida:** com as funções antigas, os quatro pares
`por favor antes de responder <pedido> e depois me avise aqui` e sua versão
com `não` no meio produziram exatamente os mesmos indicadores. A asserção de
distinção falhou nos quatro domínios antes da implementação. O defeito nessa
fronteira é a perda de informação anterior ao classificador; não depende de
limiar, quantidade de épocas, pesos ou executor.

**Representação experimental isolada:** `representacao_integral.py` expõe:

- `representar_texto_integral_v1(texto)`: texto original e indicadores em dois
  campos separados, sem remover acentos, pontuação, espaços ou trechos;
- `criar_extrator_texto_integral_v1()`: `FeatureUnion` não ajustado com canais
  de palavras integrais (1–2 gramas, incluindo palavras de uma letra),
  caracteres integrais (1–5 gramas) e indicadores estruturais existentes.

Os canais mantêm texto literal e indicadores em espaços de características
separados. São funções nomeadas, serializáveis, sem callbacks de domínio ou
estado contextual. O extrator não chama `fit`, não possui vocabulário ajustado
e não está registrado como opção de treino/runtime. O uso futuro depende da
etapa de comparação autorizada, não acontece automaticamente.

**Limites da prova:** os testes garantem preservação na entrada e distinção
dos contrastes nos analisadores antes do ajuste. Não garantem que um
vocabulário futuro preserve palavras desconhecidas, que n-gramas representem
toda a ordem da sequência, ou que o classificador compreenda os atos.
Invariância semântica, como adicionar `por favor`, não exige vetores iguais.
A coerência das expectativas da bateria não é acurácia medida de um modelo.
Resolução de contexto e revisão do staging antigo pertencem ao item 3 e não
foram implementadas nesta etapa.

**Verificação sem treino:** 118 testes novos de representação/bateria e dois
regressivos existentes passaram, totalizando 120. A composição v27 gerou
11 eventos shadow e zero ações, com os hashes ativo e candidato preservados.
Não houve nova sessão completa de caos, atualização de pesos ou avaliação da
reserva `list_windows_ato_v1.json`.

```powershell
.\.venv314\Scripts\python.exe -m pytest tests/test_neural_representacao_integral.py tests/test_neural_linguagem_comandos.py::test_representacao_estrutura_bordas_e_generica_e_independe_de_rotulo tests/test_neural_linguagem_comandos.py::test_representacao_estrutura_pontuacao_distingue_pergunta_afirmacao_e_citacao -q
.\.venv314\Scripts\python.exe validar_neural_v27_list_windows_shadow_composicao.py
```

Escopo: módulo experimental novo, bateria, testes e esta documentação.
`modelo.py`, preprocessadores antigos, `laylay.py`, configurações, Qwen,
gates e executores permaneceram intactos. Nenhum commit criado. Os relatórios
v28 antigos não foram sobrescritos.

### Revisão dos rótulos dependentes de contexto — item 3, 2026-09-05

Primeira fatia revisada: seis consultas pronominais da onda v2 (índices 370–375,
base zero). O gerador atribui `dominio_app=true` a essas frases, enquanto a
extensão recebe somente `text`, sem referente. A verificação anterior à revisão
confirmou seis domínios fixados indevidamente para entradas sem contexto.
`me conta se ela ficou aberta?`, por exemplo, pede consulta, mas a frase isolada
não determina qual entidade está sendo consultada.

O contrato é geral: **rótulo dependente de informação ausente fica indeterminado,
não negativo**. Não usar `NONE` ou `dominio_app=false` para representar essa
ausência. Nesta fatia, a anotação manual conserva `ato_consulta=true` como
informação textual e suspende os rótulos de intenção, ação, domínio e fator de
aplicativo para uso sem contexto. Os exemplos inteiros ficam fora da lista dos
não revisados, sem reaproveitamento parcial automático para treino.

`datasets/revisoes/list_windows_contexto_v1.json` registra as decisões manuais,
o hash da fonte e os hashes dos textos. `revisao_contextual.py` aplica apenas
essas decisões explícitas, sem parser, lista de pronomes ou previsão de modelo.
Ele valida fonte, índice, texto, motivo e consistência dos fatores, recusa
autoridade/treino e não sobrescreve saídas existentes.

O bundle publicado em
`memoria/neural/experimentos/revisao_contextual_v1/list_windows_revisao.json`
contém seis pendências com rótulos indeterminados (`null`), evidências textuais
e uma cópia aninhada dos exemplos históricos. O formato não é aceito como
exemplo de treino pelo validador atual. Os outros 699 registros aparecem como
`nao_revisados`: **não estão certificados como livres de dependência contextual**.
O bundle também não é um novo dataset de treino ou uma avaliação de acurácia.

O JSONL original, seus grupos e rótulos históricos permanecem intactos, com
SHA-256 `85A0006D39B1E75A6F24A9089BE7A8973C7C8CA214698BCC909F5CBB9AC66FB7`.
Isso preserva a reprodução das métricas antigas. Uma futura comparação deve
declarar a população efetivamente avaliada e não comparar diretamente 699
exemplos com a prova histórica de 705 como se a composição fosse igual.

**Owner do contexto:** `contexto_compartilhado.registrar_resultado_execucao`
publica o alvo de uma consulta direcionada; o pré-fluxo existente lê
`mente_integrada_estado.ultimo_app_janela`. Os testes conectaram esses dois
componentes reais com receipts sintéticos: a mesma pergunta `Ele continua
aberto?` retornou VLC ou Opera conforme o estado, não retornou alvo com estado
ausente e não reaproveitou o alvo diante de negação. Isso é integração de
componentes, não nova prova de sessão completa. Nenhum resolvedor novo foi criado.
Não houve revisão do ciclo de vida/TTL dos referentes nesta etapa.

**Validação:** 186 testes passaram entre revisão contextual, representação
integral e consultas naturais de aplicativos, sem ajuste de pesos ou vocabulário.
O mecanismo de revisão também foi exercitado nas referências sem contexto da
bateria de volume, música, aplicativos e arquivos. Isso prova sua aplicação
genérica, não uma auditoria completa dos datasets desses domínios.

```powershell
.\.venv314\Scripts\python.exe -m mente_laylay.neural.revisao_contextual --fonte mente_laylay/neural/datasets/candidatos/list_windows_onda_v2.jsonl --revisao mente_laylay/neural/datasets/revisoes/list_windows_contexto_v1.json --saida memoria/neural/experimentos/revisao_contextual_v1/list_windows_revisao_repeticao.json
.\.venv314\Scripts\python.exe -m pytest tests/test_neural_revisao_contextual.py tests/test_consulta_estado_apps_natural.py tests/test_neural_representacao_integral.py -q
```

Escopo: revisão offline nova, manifesto manual, testes e documentação. Nenhuma
alteração em `modelo.py`, `dataset.py`, geradores históricos, runtime, Qwen,
autorizações, executores ou configuração. Treinos seguem pausados; a reserva
nova não foi avaliada. Próxima fronteira: ampliar a auditoria dos demais exemplos
e definir a entrada contextual explícita antes de qualquer comparação que
pretenda medir resolução de referência. Não existe ainda uma integração neural
nova que consuma contexto; isso não foi presumido a partir destes testes.

### Ampliação da triagem contextual — item 3, 2026-09-05

Base conferida: branch `main`, HEAD
`a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, worktree com alterações paralelas
preservadas. Foram lidos os textos e fatores dos 705 registros da onda v2,
incluindo os 699 fora da revisão anterior, e os geradores v1/v2. Essa leitura
é uma triagem assistida por IA, não validação humana independente dos rótulos.

Resultado: manifesto cumulativo `datasets/revisoes/list_windows_contexto_v2.json`,
com **19 pendências contextuais**. Preserva integralmente as seis decisões v1 e
acrescenta 13. O campo legado `origem=REVISAO_MANUAL` significa decisões explícitas,
não aprovação de Pedro; a autoria assistida está declarada no manifesto.

| Fatia (índices base zero) | Decisão e limite |
| --- | --- |
| 370–375 | Seis pronomes: consulta textual conhecida; domínio/referente ausentes. |
| 74, 80, 82, 85, 93, 97, 103, 105, 109, 116 | Dez consultas nominais: galeria, câmera, agenda, tela de desenho e biblioteca de mídia admitem aplicativo, conteúdo/interface ou objeto físico. Suspender domínio, não negar a consulta. |
| 177–179 | Três frases `você consegue identificar ...`: capacidade ou pedido indireto. Domínio app explícito, mas ato indeterminado sem contexto pragmático. Não converter automaticamente para pedido nem para recusa. |

**Evidência causal e controles:** o gerador v1 fixa o ato das três frases de
capacidade como negativo; a importação v2 conserva esse fator. O treino fatorado
em `modelo.py` usa somente `text`, não o cenário imaginado pelo autor do gerador.
A verificação anterior à ampliação falhou porque os 13 índices ainda estavam
em `nao_revisados` na vista v1. É RED de cobertura de anotação, não prova de erro
da Laylay numa sessão real. Isso falsifica que a dependência contextual se limita
a pronomes. Também não basta suspender todo fator: nos casos de capacidade o
domínio está explícito; nos nomes ambíguos a consulta está explícita. Cada decisão
preserva apenas o que o texto sustenta. Nenhuma consulta real de apps foi executada.

**Pendência diferente, mantida separada:** registros 84/107 consultam uma planilha
do Excel; 89/113 a área de trabalho; 91/115 a janela de um editor não identificado.
Os negativos 696/700 consultam planilhas/documentos. Antes de aprovar esse conjunto,
definir a granularidade do alvo e o contrato de observação: processo aberto não
prova documento aberto; uma janela genérica não identifica sozinha qual editor.
Não foram relabelados como negativos nem incluídos nas 19 decisões contextuais.
Essa fronteira precisa de revisão do owner de consulta, não de mais exemplos.

A leitura das demais famílias cobriu inventário (0–71, 355–369), consultas nominais
(72–116, 195–354), recusas/relatos/capacidade (117–194), contrastes de ato (376–551)
e entidades/operações vizinhas (552–704). Sem aprovação automática: nomes como
`loja`/`sessão`, citações isoladas e consultas indiretas merecem uma política de
anotação consistente com o contexto. Não foi feita auditoria exaustiva de todos
os rótulos, aliases, qualidade gramatical ou cobertura de executores.

O bundle `memoria/neural/experimentos/revisao_contextual_v2/list_windows_revisao.json`
tem 19 pendências e 686 registros em `nao_revisados`. Esse nome significa sem
decisão contextual formal aplicada, mesmo após leitura; não significa aprovados.
Mantém cópias históricas, desconhecidos como `null`, treino/autoridade falsos e
recusa sobrescrita. O mecanismo de revisão existente foi reutilizado sem alteração.
O dataset histórico e o manifesto v1 continuam disponíveis: esta vista offline
não bloqueia globalmente quem chamar diretamente o treinador com a fonte antiga.

Verificação: **201 testes passaram** entre revisão, representação integral e consultas naturais;
nenhum ajuste de pesos ou vocabulário. O hash do modelo ativo antes/depois foi
`07C539917EAE7792B2B4ECB1F0335697802FC7F6672E920656F8C5DFC2289E62`;
o hash da fonte permaneceu `85A0006D39B1E75A6F24A9089BE7A8973C7C8CA214698BCC909F5CBB9AC66FB7`.
Nenhum novo teste de sessão completa, promoção, reserva avaliada ou commit.

Próximo passo: definir o contrato de alvo/observação e os campos contextuais
necessários por decisão antes de preparar uma população de avaliação revisada.
Não usar ausência de contexto como exemplo negativo, nem contexto como autorização.

### Contrato de alvo/observação — diagnóstico, 2026-09-05

Estudo documentado em [CONTRATO_ALVO_OBSERVACAO.md](CONTRATO_ALVO_OBSERVACAO.md).
A fronteira atual de resolução aceita o título do app contido no alvo composto:
`Excel` prova indevidamente `planilha do Excel`. O catálogo aceita o booleano e
o pré-fluxo publica receipt confirmado para o conteúdo. Reproduzido também com
Word/documento e VLC/vídeo, sem rede ou LLM, com componentes reais e observações
controladas. Não é nova sessão completa nem correção de produção.

O diagnóstico opt-in abaixo mantém **6 REDs explícitos e 9 controles GREEN**,
sem xfail: três na primeira fronteira e três em sua consequência integrada.
Os controles preservam consulta explícita, ausência de correspondência e
qualificador legítimo de janela. Em execução separada, **211 regressivos passaram**.
Isso não elimina os seis REDs nem torna a raiz encerrada.

```powershell
.\.venv314\Scripts\python.exe -m pytest tests/test_resolucao_alvo_observado.py -q --tb=short
.\.venv314\Scripts\python.exe -m pytest tests/test_neural_revisao_contextual.py tests/test_consulta_estado_apps_natural.py tests/test_neural_representacao_integral.py tests/test_catalogo_aplicativos_consulta.py tests/test_ambiente_navegacao_registro.py -q
```

Contrato proposto: identificar alvo/tipo/propriedade, separar candidato textual
de evidência, distinguir ausência de falha e manter proveniência/validade do
contexto compartilhado. Os campos estão especificados no estudo, não implementados
na rede. Próxima etapa é inventariar consumidores e aplicar o candidato na
resolução canônica, preservando qualificadores legítimos e validações de efeitos.
Não criar parser neural ou fallback de fala para compensar essa fronteira.

Escopo desta etapa: documento, diagnóstico opt-in e README. Produção, revisões
v1/v2, modelo ativo e dados históricos não alterados; sem treinamento ou commit.

### C1 de resolução aplicado — 2026-09-05

Atualização do diagnóstico acima: os seis REDs foram reconfirmados e corrigidos
na correspondência de programas. O teste foi migrado para
`tests/test_resolucao_alvo_observado.py`; o comando acima agora usa esse caminho.
O helper de qualificadores do catálogo foi centralizado em `planejamento_janelas`,
reutilizado no resolvedor. Título curto não prova alvo mais específico;
qualificadores legítimos e aliases são preservados. Não altera o matching de abas.

**425 testes e 8 subtestes passaram**, incluindo consumidores de janelas,
catálogo, validação de ambiente e revisão neural. A leitura real do desktop pela
fachada reconheceu VS Code aberto, mas não confirmou seu documento; foco igual,
zero ações, voz/persistência capturadas. Ainda não é sessão completa da Laylay.

Produção alterada: `percepcao/janelas_sistema.py`, `percepcao/planejamento_janelas.py`
e `integracao/catalogo_aplicativos.py`. Nenhuma alteração em Qwen, modelo ativo,
datasets, permissões ou executores. Treinos continuam pausados. Detalhes e limites
estão na seção C1 do [contrato](CONTRATO_ALVO_OBSERVACAO.md).

Próxima fronteira: distinguir falta de evidência/falha de leitura de ausência
observada e validar o turno completo após o pré-fluxo devolver uma consulta de
conteúdo não resolvida. Não aprovar os 686 exemplos apenas pelo GREEN deste patch.

### C2 de observação aplicado — 2026-09-05

Falha de enumeração preserva seu estado desde o observador até a resposta:
receipt não confirmado, falha comunicada e referente preservado. Uma leitura
bem-sucedida vazia continua válida. Inventário parcial não confirma resultado
completo. O coordenador interrompe cadeias quando a consulta falha, inclusive
se a voz rejeitar a emissão.

13 regressivos em `tests/test_falha_observacao_consulta.py` cobrem fonte, fachada,
pré-fluxo, memória e cadeia canônica. A prova com observadores reais manteve
consultas saudáveis funcionando, sem ações ou mudança de foco. Não é sessão
completa com LLM: conteúdo não resolvido permanece como próxima fronteira.

Escopo e limites na seção C2 do [contrato](CONTRATO_ALVO_OBSERVACAO.md).
Regressão ampliada: **474 testes e 30 subtestes passaram**. Modelo ativo e fonte
v2 mantiveram os hashes registrados no C1; não houve avaliação de reserva.
Nenhum treino, promoção, alteração de configuração ou commit.

### C3 — preparação da prova de turno completo, 2026-09-05

**Ainda não executada.** Sessão encontrada: Python launcher 4368, processo real
16504, início 19:03:37; interface 20936, sessão `4deb6edf`. Eram processos pai/filho
do mesmo lançamento, não duas instâncias independentes. Os arquivos C1/C2 foram
alterados depois do início: não usar essa sessão como GREEN dos patches atuais.

O controle Windows exibiu a interface e criou conversa de teste, mas não conseguiu
focar/preencher o composer: foco reportado persistiu em `Buscar conversas`;
`set_value` retornou `A propriedade solicitada não estava no CacheRequest
(0x80070057)`. Nenhuma pergunta de sonda foi enviada. Duas entradas `Nova conversa`
ficaram visíveis durante a tentativa; não foram apagadas. Não houve encerramento
da sessão, interrupção musical ou nova instância concorrente.

Preparado `roteiro_consulta_conteudo_c3.py`, usando o launcher e leitor oficiais:
consulta de app, consulta de documento e correção de escopo. Configuração validada
pelo leitor real (3 turnos, voz silenciosa, encerramento ao final). Isso prova
somente carregamento do roteiro, não comportamento conversacional. As expectativas
lexicais são smoke checks: turnos 2/3 precisam de revisão manual de resposta,
plano e receipts, inclusive mutações inesperadas e alegações de observação.

Para retomar, encerrar a sessão antiga antes de iniciar o roteiro com
`.\.venv314\Scripts\python.exe roteiro_consulta_conteudo_c3.py`.
O roteiro abre o runtime completo com serviços/persistência normais; não é sandbox.
Não alterar produção para compensar problema de UI nem afirmar raiz C3 corrigida.

### C3 — prova de turno completo executada, 2026-09-05

Após Pedro encerrar a sessão anterior, foi confirmado que não havia processos
Python ativos. Base: `a215d9e5e31dd92d2cd9deb9b8622c8f642e6752`, branch `main`,
worktree modificada preservada. A primeira tentativa, em
`resultados_testes/roteiro_consulta_conteudo_c3-20260905-194642-893537`, foi
interrompida e não conta como prova completa (briefing atrasou a entrada do roteiro).

A segunda terminou normalmente, com os três turnos pelo canal canônico de roteiro
do runtime real e LLM. Artefatos:
`resultados_testes/roteiro_consulta_conteudo_c3-20260905-194754-467157`.
Somente para esse processo: `LAYLAY_BRIEFING_INICIAL=0`,
`LAYLAY_FALAS_INICIAIS=0`, `LAYLAY_TERMINAL_2=0`; configuração persistente intacta.
Serviços e persistência normais continuam ativos: não foi sandbox.

- Aplicativo: respondeu que VS Code estava aberto, sem foco, com receipt
  `LIST_WINDOWS / estado_app_consultado`, `executou=True`, `confirmado=True`.
- Documento: não alegou observação nem executou comando operacional.
- Correção de escopo: também não alegou observação, mas repetiu literalmente a
  resposta anterior: “Não tenho uma leitura atual desse estado para te responder
  com segurança.”

**GREEN de segurança nesta sonda; RED de utilidade/continuidade conversacional.**
O avaliador marcou 3/3, mas os critérios lexicais não certificam qualidade.
`fallbacks_conversacionais=0` não representa ausência de contingência: o log dos
dois últimos turnos registra `autoria final indisponível / fala_invalida`, e a
resposta fixa foi efetivamente entregue. A maior repetição registrada foi 2.
Não usar esse contador isolado para aprovar o comportamento.

O processo encerrou automaticamente; uma nova consulta de processos não encontrou
Python ativo. Nesta etapa não houve patch de produção, treino, promoção ou commit.
A próxima investigação está descrita na seção C3 do
[contrato](CONTRATO_ALVO_OBSERVACAO.md); a prova não encerra essa raiz.

### C3.1 — por que a autoria falhou, 2026-09-05

O rastreamento real demonstrou que a autoria final recebeu um estado técnico:
`limite_chamadas` bloqueou o transporte após principal + reparo. Não foi uma fala
vazia produzida pelo Qwen nem timeout dessa tentativa. O diagnóstico agora separa
`estado_tecnico_llm` de `fala_invalida` (4 REDs antes do patch).

Também foi reproduzido um falso negativo do contrato: o reparo dizia “Não há
evidência atual…” e era rejeitado como falta de incerteza. Corrigida a construção
linguística geral, com 5 REDs em domínios diferentes e controles negativos.
O replay integrado do reparo real completo agora o preserva sem segunda autoria.
**236 testes passaram**, mas a nova sonda real ainda repetiu a contingência com
outras rejeições: capacidade e entidade antiga. Não declarar C3 encerrado.

Artefato pós-patch: `resultados_testes/roteiro_consulta_conteudo_c3-20260905-200902-169240/`.
O avaliador continua marcando 3/3 por critérios básicos; não é prova de utilidade.
Detalhes, falsificações, limites e próxima fronteira na seção C3.1 do
[contrato](CONTRATO_ALVO_OBSERVACAO.md). Produção alterada somente em
`personalidade/autoria_conversacional.py` e `cognicao/validacao_contrato_fala.py`.
Orçamento, modelo, treinamento, executores e configuração preservados; sem commit.

### C3.2 — correção de escopo chegou à conversa, 2026-09-05

Corrigidos separadamente o alcance das ressalvas no guardião e a continuidade
conversacional de uma correção explícita. “Não consegui verificar…” não vira
confirmação de estado; “não sei …, mas está aberto” continua exigindo receipt.
A pergunta imediatamente anterior do usuário pode contextualizar uma correção
por até 240 segundos, sem inventar referente operacional nem autorizar ação.

**405 testes passaram**. Na sonda real
`resultados_testes/roteiro_consulta_conteudo_c3-20260905-202732-986921/`, o plano
recebeu o contexto correto e a resposta à correção chegou ao usuário sem ser
substituída pela contingência. Ainda não é conversa aprovada: o turno anterior
caiu em fallback e a fala final incluiu uma explicação não comprovada sobre o
acesso ao VS Code. O problema geral C3 continua aberto; treinos continuam pausados.

Detalhes, sete REDs do guardião, quatro REDs da correção, escopo e próxima fronteira
estão na seção C3.2 do [contrato](CONTRATO_ALVO_OBSERVACAO.md). Nenhum commit,
mudança de modelo, relaxamento de orçamento ou alteração de executores.

### C3.3 — unificação das ressalvas, 2026-09-06

Os validadores agora reutilizam `cognicao/incerteza_observacao.py`, em vez de
discordar sobre formas legítimas de declarar falta de leitura. Cinco REDs
precederam essa mudança. Três REDs adicionais protegeram pedidos de informação:
“me diga qual arquivo está aberto” não confirma estado nem permite afirmações
independentes sem receipt.

**423 testes passaram.** Sonda pelo launcher normal (sem profiling):
`resultados_testes/roteiro_consulta_conteudo_c3-20260906-100353-826265/`.
Três turnos concluídos e processo encerrado com código 0; a correção preservou
o contexto, mas ainda houve contingência no turno do documento. A fala também
acrescentou uma explicação não comprovada de limitação de acesso do VS Code.
Não é aprovação integral da conversa, apesar dos 3/3 no avaliador básico.

Próxima investigação: proveniência temporal e por alvo dos estados observados,
e evidência específica de capacidade. Não confundir ausência de leitura com
proibição de acesso. Detalhes, artefatos e escopo na seção C3.3 do
[contrato](CONTRATO_ALVO_OBSERVACAO.md). Treinos e promoções continuam pausados.
