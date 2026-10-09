# Laylay — registro de problemas e correções

### AUT-01 — conferir ocorrência na admissão da próxima etapa — 06/10/2026

Continuação da janela posterior à publicação aceita já registrada, sem outro
ID por domínio/frase. Base `main/90a2fb8`, worktree preservada. Mescla por
solicitação e procedência semântica já possuem candidatos de outras frentes:
26/75/33 controles atuais GREEN, com sobreposição; não reaplicados aqui.

Primeira RED: publicação vinculada legítima → montagem de contexto ou primeiro
comando troca o turno → comando/finalização antigo ainda inicia. Writer depois
recusa corretamente; isso falsifica sua falha como condição necessária. Nova
ocorrência pode ter a mesma frase, e três controles vigentes passam normalmente.

Contrato canônico somente leitura em `ComposicaoTurnoRuntime.proposta_vigente`,
instalado pela composição. Runtime consulta após montar dispatcher/finalizador;
dispatcher consulta antes de cada comando, inclusive rota legada. Retorno
incerto, erro ou callback malformado presente recusa; contexto antigo sem a
chave mantém compatibilidade. IDs não concedem autoridade ou comprovam efeito.

16 REDs/3 controles antes do candidato; 31 focados depois (19 locais e 12 da
composição instalada), três domínios. Gate: **600 aprovados e 10 subtestes**,
41,67 s. Ampla final: **10.161 aprovados, um ignorado e 56 subtestes**, zero
falhas, 499,80 s; XML `.pytest_cache/aut01_admissao_ampla.xml`, manifesto
`.pytest_cache/aut01_admissao_hashes.json`, 222 Python estáveis durante/depois.
HEAD/branch preservados e diff sem erros. Resultado no checkpoint 10 do
[plano de autonomia](../planos/PLANO_LAYLAY_ASSISTENTE_AUTONOMA.md).

Produção desta entrega: `composicao_turno.py`, `resposta_ia_runtime.py`,
`dispatcher_comandos_json.py` e instalação do callback em `laylay.py`.
Nenhum executor de domínio ou parser alterado; nenhum commit. SQLite/mutex
próprios, transporte/efeito/fala controlados. Não certifica GUI, áudio ou
dispositivos físicos, nem atomicidade entre leitura e efeito dentro do executor.
AUT-01 parcial: ação em curso, resultado tardio e fala após admissão continuam
fora deste candidato. Não atribuir a intercalação à troca histórica `55ee6435...`.

### RC-OFERTA-01 — aceite de oferta não chegava ao executor — 06/10/2026

- Evidência histórica: imagem fornecida por Pedro e TXT diário local de
  06/10, 18:03/18:04. “Pode ser” → “Manda quando quiser”; “pode fechar” →
  ausência de execução; pedido com alvo explícito → fechamento de três abas.
- Baseline `main`, HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`.
  Worktree suja preservada; HEAD não equivale ao processo histórico.
- Raiz reproduzida: oferta do `PorteiroChromeRuntime` só publicava fala/lista;
  sem `PendenciaAcaoRuntime`, reconhecimento próprio incompleto e consumo
  tardio atrás das barreiras conversacionais. Não é defeito demonstrado do
  classificador compartilhado de “pode ser” ou falha geral do fechamento.
- Candidato: registrar ID/TTL/hash dos alvos na pendência existente, respeitar
  outra pendência ativa e política de sobrevivência; resolver aceite/recusa
  pelo intérprete compartilhado; consumir antes da conversa; fechar pelo
  roteador/executor atual e concluir somente com receipt confirmado.
  Verbos de fechamento permanecem informação do domínio, sem lista privada
  de sim/não. Detector legado passa a exigir pedido com alvo explícito.
- RED inicial: 12 falhas de contrato, inclusive composição instalada.
  Cinco REDs adicionais: outro pedido com aceite verbal/verbo de outra ação
  não confirma esta oferta. Opção `somente_aceite_generico` no classificador
  e resolver compartilhados; default conserva consumidores existentes.
  Provas de pendências reais de navegador/arquivos e compatibilidade legada.
  GREEN final focado: 34. Gate final: 282 aprovados, XML em
  `.pytest_cache/oferta_abas_regressivos_finais.xml`; intermediário de 258
  em `.pytest_cache/oferta_abas_regressivos.xml`. Ampla detalhada abaixo.
  Manifestos intermediários preservados em
  `.pytest_cache/oferta_abas_hashes.json` e `oferta_abas_hashes_finais.json`;
  revisão validada em `.pytest_cache/oferta_abas_hashes_validados.json`.
- Produção desta correção: `porteiro_chrome.py`, `detectores_playlist.py`,
  `comandos_imediatos.py`, wiring em `composicao_entrada_interacao.py` e
  `laylay.py`, opção genérica em `aprendizado_rotina_musica.py` e passagem
  dessa opção em `pendencia_acao.py`. Não altera executores Chrome ou motor
  de aprendizado. Nenhum commit criado; outros diffs preservados.
- Limite: composição carrega `laylay.py` e usa serviços reais com SQLite
  isolado; efeito Chrome/percepção/fala são controlados. Fechamento no navegador
  e som físico após reinício continuam sem prova. Não marcar encerramento
  global por verde de harness; raiz vinculada ao mapa RC-OFERTA-01.
- Ampla intermediária: **10.025 passed, 1 skipped, 56 subtests passed**,
  oito falhas, 400,08 s. Log/XML `.pytest_cache/oferta_abas_ampla.*`.
  Sete falhas são `SystemExit: 0` na proteção de instância antes da composição,
  pois a Laylay pessoal está aberta. Revalidação das sete: **7 passed**,
  5,64 s, mutex canônico com identificador isolado no processo do teste,
  sem encerrar a Laylay ou editar produção; XML `oferta_abas_bloqueios_instancia.xml`.
  Falha restante `test_cache_com_quebrado_migra_para_sapi_nativo_sem_repetir_pyttsx`
  também reproduzida isoladamente (47 controles passaram na seleção).
  Voz já alterada na worktree anterior, sem mudança desta investigação;
  sintoma separado, raiz não diagnosticada aqui. Não enfraquecer o teste.
  Ampla coletou a revisão intermediária antes do refinamento final genérico;
  282 é o gate da revisão final, não uma nova ampla totalmente verde.

### P16 — fonte original disponível e sequência interrompida por efeito real — 04/10/2026

Sem novo candidato de produção; base main/90a2fb8, 1.245 Python e arquivos pessoais
anteriores preservados por hash. Após jogo encerrado e pré-aquecimento canônico
no orçamento padrão, coleta `182525-927021` tem oito principais novas HTTP200,
correlacionadas a payload/bruto/turno/plano: oito controles GREEN, p95 7,953 s,
zero comandos/violações/efeitos IoT. Não observou erro original próprio; não fecha
publicação/admissão positiva, nem prova causa única dos timeouts históricos.

Coleta real com voz/avatar `182929-427557`: 16 respostas/filas de áudio concluídas,
sem silenciamento, código zero; **5 passaram, 8 falharam, 3 alertas**, p95 23,244 s.
Primeira RED no turno 4: Calculadora sem foco → `app_focado`, executou/confirmou,
receipt `7e0b232057f04911879fc46ec91d310c`, enquanto roteiro exigia não-ação
redundante. Outra interrupção no turno 9, `7043e96cfbb24f6b9e26e81968d6ec61`.
Retratos apontam navegador em primeiro plano; ator da troca não identificado.
Os oito sintomas 4/5/6/7/9/10/11/14 permanecem ligados às duas interrupções de
pré-condição, sem oito novos bugs atribuídos à emoção. Reavaliação offline pelo
owner canônico dos dez receipts corresponde aos eventos gravados. Primeira
interrupção em 20,195 s, dentro dos 300 s: contador/TTL não explicam essa RED.
Um efeito real interrompe redundâncias consecutivas; não alterar o receipt nem
enfraquecer expectativas para certificar uma sequência que não ocorreu.

Seis principais de conversa novas/HTTP200/vinculadas, sem comandos/violações.
Conquista/vulnerabilidade/assunto novo encerram episódios observados; relato
temporal publica alívio sem tristeza passada lexical. Autoria/reparos existentes
participaram, detalhados na prova; não declarar fidelidade global. Computer-use
não retornou janela capturável do avatar e não emitiu entrada/ativação. Confirmação
humana de som/visual desta coleta pendente; `brava 3` não foi atingida. Próxima
fronteira: sequência com foco realmente observado e observação física; positivo
próprio fresco e lacunas históricas permanecem abertos. Provas e limites no novo
checkpoint do roadmap e `prova_voz_avatar.json`; nenhuma expectativa removida.

### P16 — identidade literal e nomeação antes de persistir — 04/10/2026

**Raiz da pessoa indevida demonstrada:** `MemoriaPessoasRuntime._extrair_relacao`
aceitava qualquer palavra justaposta a `meu/minha + relação`, salvo sete verbos.
O histórico `210441-907211`, `Meu irmão está bravo. Eu me sinto culpado.`, virou
`Esta`; variantes viravam `Estava`, `Parece`, `Chegou` etc. A mesma regra solta,
avaliada por último, sobrescrevia `se chama Esta` com `Se`. Primeira fronteira:
seleção da evidência de identidade, antes de classificação, armazenamento e LLM.
Falsificadas origem na principal e falha geral de escrita: extração direta RED,
apresentações explícitas e armazenamento real usados como controles.

Candidato mínimo somente `memoria_pessoas.py`: remover a moldura de justaposição;
nomeação/apresentação explícitas continuam no mesmo serviço, com proveniência,
aprendizado, contexto e receipts existentes. Sem lista de palavras do histórico.
Menções como `meu irmão Carlos` deixam de criar identidade por si só; formas como
`Carlos é meu irmão`, `meu irmão é Carlos` e `se chama Carlos` continuam cobertas.
O patch não certifica interpretação arbitrária de nomes/adjetivos nas copulas.
RED inicial: 11 falhas/36 controles locais, cinco falhas/um controle na composição.

**Raiz separada encontrada no controle positivo instalado:** a linguagem aprendida
consumia `Meu irmão se chama Esta.` como alias `meu irmao se → esta`, impedindo a
memória de pessoas de receber o relato. O trace chegou ao atalho de apelidos,
sem chamada ao serviço; o extrator de pessoas já estava correto. Não era barreira
P0, composição ausente ou persistência quebrada. Quatro REDs/ quatro controles
com SQLite real, em pessoas/projeto/arquivo. Candidato mínimo no owner
`LinguagemAprendidaRuntime.extrair_apelido_ensinavel`: `se chama` não é o separador
lexical `chama`; ensino explícito de alias continua válido. Não reordenar handlers.
Princípio compartilhado: evidência literal deve autorizar o tipo de aprendizado;
uma nomeação não autoriza outra substituição global na linguagem.

**GREEN local/composição:** 95 focados antes da guarda CLI; sonda final 17 GREEN,
incluindo abortar o roteiro novo sem isolamento. Callbacks e serviços instalados
por `laylay.py` preservados, casos negativos/positivos e ensino lexical vizinho.

**GREEN do contrato no loop real:** `transporte_evidencia-20261004-174111-482431`,
oito turnos. Três negativos iniciais sem arquivo/perfis; apresentação de Esta
gera PEOPLE_REMEMBER confirmado, relação/ID/fonte relidos. Predicado após cadastro
não altera bytes. Consulta canônica retorna `Esta é seu irmão`, PEOPLE_QUERY
confirmado. Nomeação de projeto não escreve pessoas/aliases; Ana apresentada e
relida como prima. SQLite próprio contém zero aliases; todos os planos conservam
`autoriza_execucao=False`. Cinco passaram/três alertas de latência/zero falhas,
p95 29,426 s. Receipt e releitura são a prova, não o placar isolado.

**Limites:** sete principais só técnicas insuficientes (timeouts/circuito),
contingências existentes participaram da fala; não validar autoria/fidelidade ou
positivo próprio da P16. Voz/avatar off. 119 Python preservados durante a coleta;
JSON pessoal e TXT diário anteriores preservados por hash. O registro pessoal
histórico `pessoa:105d09395b32` permanece intacto. Isolamento opcional da sonda
abrange SQLite/resumo/pessoas, não todo estado. Base main/90a2fb8; nenhuma alteração
no classificador/executor/orquestrador, nenhum commit ou limpeza. Provas/baselines
em `prova_identidade_pessoas.json` e no checkpoint do roadmap. **Ampla: 9.429 passed,
1 skipped, 56 subtests passed**, 280,69 s, código zero; 119 hashes do manifesto e
arquivos pessoais conferidos depois. Manifesto acompanha a base suja e testes/
roteiro novos; os dois owners, antes limpos, não estavam nesses 119. Baselines
originais, diff mínimo e mtimes anteriores à coleta conferidos separadamente em
`auditoria_fontes_candidato.json`; hashes dos candidatos registrados após a ampla,
sem alegar captura anterior que não ocorreu. P16 continua parcial.

### P16 — atribuição lexical de emoção fora do predicado pessoal — 01/10/2026

Raiz demonstrada, owner `analisar_intencao_emocional`: marcador pessoal e sinal
eram buscados globalmente. `estou` atual validava `triste` passado, publicando
vulnerabilidade lexical que a prioridade direta preservava sobre alívio original.
Histórico `203531-829003`, plano 1790897998476775600. Transporte/perda da principal,
reparo como fonte e obrigação de copiar alívio para a Laylay foram falsificados.

Produção somente `leitura_usuario.py`: verbo/sinal/grau no mesmo predicado;
incerteza segue para a principal. Não alterar prioridade, executor ou emoção
própria. Dez REDs antes do patch (dois na composição instalada); 408 focados,
oito subtestes e 13 da sonda GREEN. Ampla: **9.394 passed, 1 skipped, 56 subtests
passed**, 221,15 s. Base main/90a2fb8, 116 Python/hash e TXT diário preservados.

Main novo `transporte_evidencia-20261001-210441-907211`: três relatos temporais
publicam alívio original sem evento lexical anterior, comandos ou alteração da
expressão própria. Tristeza presente mantém a proteção direta. Voz/avatar off;
não certifica leitura temporal arbitrária nem fecha P16. Prova local e detalhes
no checkpoint do roadmap. Nenhum interpretador extra, replay ou commit.

**Falha vizinha preservada:** sexto relato `Meu irmão está bravo. Eu me sinto
culpado.` gerou `PEOPLE_REMEMBER` de `Esta`, antes da principal, e persistiu
`pessoa:105d09395b32` em `memoria/pessoas_relacoes.json` (releitura confirmada).
Identidade literal antes da persistência exige investigação própria; não agrupar
por semelhança com esta raiz nem contar como erro operacional original da LLM.
Placar completo: três passaram, dois alertas de latência e uma falha; expectation
intacta. Dois originais não JSON e `Senti isso antes` são observações de formato/
fidelidade ainda sem raiz atribuída. Registro persistente preservado, sem limpeza.

### P16 — sequência real de 16 turnos com voz/avatar, som físico pendente — 01/10/2026

Coleta `transporte_evidencia-20261001-203531-829003`, main/roteiro real, base
`main`/`90a2fb8`, dez receipts distintos/confirmados (sete redundâncias em foco).
Campos emocionais/refs conferidos nos 16 planos: intensidade causal, continuidade,
conquista/desculpa/vulnerabilidade/renovação e assunto novo. Dez passaram, seis
alertas só de latência, zero falhas; todas as esperas de voz concluídas, voz ativa.
Capturas `computer-use` sem ativação/input mostram avatar calmo e com bronca;
contexto publicado/intervalos arquivados. Captura pontual não certifica sincronismo
integral; som físico aguarda observação humana desta execução. Não encerrar P16.

Código zero e log nativo vazio não encerram crash histórico. 114 Python/hash e
TXT pessoal preservados. 99 focados GREEN; nenhuma produção alterada nesta etapa,
apenas roteiro/sonda/testes/documentação. Isolamento limitado a SQLite/resumo.
44 registros/28 HTTP200 (um pré-aquecimento + 27 gerações); retornos locais e
tentativas bloqueadas separados em `prova_voz_avatar.json`. Reparos/contingências
existentes participaram; nenhum interpretador emocional novo. Turno 10 disse
ser chatbot, observação de fidelidade sem raiz nova atribuída. Detalhes no roadmap.
Auditoria visual: IDs longos arredondados pelo JS; originais preservados e adendo
com IDs exatos em strings da fonte Python. Isso não prova ID lido do renderer.
Turno 15 verifica só ausência de comando. A principal original reconheceu alívio;
o plano conservou vulnerabilidade lexical do `triste` passado. `Calma 1` era
proposta de expressão do modelo, não leitura lexical. Diagnóstico na continuidade acima.

### P16 — vetos naturais compostos, sem proposta própria incompatível — 01/10/2026

Continuação da prova P16, sem outra raiz contada. Main real, base `main`/`90a2fb8`,
coleta `transporte_evidencia-20261001-202847-916595`, seis recusas IoT em roteiro
dedicado; whitelist/observadores da sonda, sem candidato de produção. Cinco
principais novas/HTTP200/sucesso, conteúdo e seis identidades correspondentes.
Veto inequívoco, owner conversa/origem classificador; cinco comandos originais
vazios, validadores/dispatchers vazios, zero violação/evento/admissão/entrada IoT.
Controle negativo real auditado independentemente; positivo próprio ausente.

Sexto turno: pre-fluxo de reparação local, sem principal. Sexto registro do modelo:
resumo bloqueado antes de HTTP e adiado sem consumo. Placar mínimo 6/6 verifica
ausência de comandos; não avalia fidelidade da fala. Quinto original afirmou
estado sem leitura e foi corrigido pelo guardião antes da entrega. Sexta resposta
local teve referente inadequado. Essa é observação separada, com raiz ainda não
diagnosticada; não promover a erro operacional P16. SQLite/resumo próprios,
TXT pessoal preservado por hash, IoT simulado/voz e avatar desativados.
Tentativa 202759-703726 parou no loader literal antes de qualquer principal;
roteiro corrigido e carregamento real protegido. Detalhes no roadmap/prova local.

### Memória diária — estado técnico promovido a resumo e consumo do lote — 01/10/2026

Raiz separada demonstrada no runtime, base `main`/`90a2fb8`, owner
`MemoriaLaylay.atualizar_resumo_diario`. Callback ligado pelo root retorna só
texto; resumo aceita sentinela não vazia sem `LAYLAY_LLM_INDISPONIVEL`, substitui
resumo anterior, limpa lote/contador e persiste. Fonte real f9731f24... da coleta
`transporte_evidencia-20261001-195555-791829`: `sucesso=False`,
`__LAYLAY_LLM_ORCAMENTO_PRAZO_ESGOTADO__`, sem HTTP. TXT tem cabeçalho e a
sentinela como resumo; helper canônico confirma `orcamento_prazo_esgotado`.
Artefato de metadados/hash: `diagnostico_resumo_diario.json` na mesma coleta.

Falsificados autoria semântica da LLM nesse retorno e falha geral da escrita;
não quantificados dados pessoais removidos nem excluídos todos writers externos.
Contrato: falha técnica nunca consolida memória nem consome lote. **11 REDs e
8 controles GREEN** antes do candidato: timeout/ocupação/nove estados de orçamento
substituíam o resumo na primeira asserção causal. Indisponível já protegido,
texto legítimo sobre timeout e controles antigos GREEN. Teste canônico protege
resumo anterior/lote/contador/bytesTXT/recarga/cooldown29s/retentativa30s.

Candidato mínimo: só `mente_laylay/memoria_mental/resumo_diario.py`, guarda com
`eh_estado_tecnico_llm` compartilhado, preservando proteção antiga. **34 focados
GREEN** em 1,75 s. Main real `transporte_evidencia-20261001-201034-289090`:
resumo recebeu `__LAYLAY_LLM_ORCAMENTO_PRINCIPAL_DUPLICADA__` sem HTTP, adiou;
TXT próprio conserva oito pendentes e placeholder, sem sentinela consolidada.
TXT pessoal anteriormente contaminado preservado por hash; não restaurado.
Ampla **9.359 passed, 1 skipped, 56 subtests passed** em 226,04 s, código zero:
`.pytest_cache/resumo_diario_ampla.log`. Auditoria persistida em
`.pytest_cache/resumo_diario_ampla_hashes.json`: 113 arquivos Python acompanhados
com hashes iguais antes/depois, nenhuma alteração durante a suíte.

Limites: prevenção de novos consumos técnicos; não recupera lote histórico nem
valida/limpa resumo contaminado ao carregar. O tipo de chamada do resumidor e a
possibilidade de consolidação real em outro momento não foram alterados. Não
pertence à raiz da proposta emocional ou ao isolamento da sonda. Sem commit.

### P16 — oito principais novas, controles negativos reais — 01/10/2026

Coleta `transporte_evidencia-20261001-201034-289090`, base `main`/`90a2fb8`.
Após GPU liberar e modelo expirar normalmente, recarga no caminho normal;
backend observado Qwen com 3.178.149.969 bytes na VRAM. Nenhum processo existente
encerrado ou orçamento/modelo alterado. Oito principais/HTTP200/originais/extrações
idênticas e vinculadas ao ID corrente: seis sem campo comandos, duas lista vazia.
Oito dispatchers vazios; nenhum receipt/executor IoT/evento/admissão de erro próprio.
Código zero/8 turnos. Controle negativo real; a prova positiva continua pendente.

Observador contou oito principais, um reparo de comunicação existente e um resumo
bloqueado (dez registros, mas só nove gerações do modelo + pré-aquecimento HTTP).
Nenhum interpretador emocional adicional. SQLite e resumo próprios; TXT pessoal
preservado por hash. A lacuna do caminho de resumo da sonda foi reproduzida RED
antes da correção só no construtor observado; teste com serviços reais GREEN.
Guardas de coleta rejeitam prova positiva sem fonte/validação; 34 focados incluem
esses três controles. `prova_p16.json` distingue o negativo da ausência de culpa.
Detalhes/limites no roadmap. A ampla anterior precedia a instrumentação atual.

### P16 — fonte técnica insuficiente na prova própria nova — 01/10/2026

Pré-condição da prova positiva, sem outra raiz semântica declarada. Main real,
roteiro IoT existente com veto, SQLite próprio e observadores delegando fonte,
validação, publicação, confirmação e finalização. Somente sonda de transporte
alterada nesta etapa. Artefatos `transporte_evidencia-20261001-195336-817698` e
`transporte_evidencia-20261001-195555-791829`: oito fontes técnicas cada,
zero comandos no dispatcher/entrada executor IoT/evento de erro próprio.
Código zero e placar 8/8 não provam geração válida; coleta/prova registram fonte
insuficiente. Nona chamada externa é resumo diário, não outro turno válido.

Primeiro controle: carregamento 21,15 s; principais expiraram. Segundo, modelo
já carregado: timeout 5/7/7 s → circuito. Frio sozinho falsificado. Ollama
0/37 camadas GPU; consulta posterior GPU 96%, cerca de 190 MiB livres, Forza
em execução. Consumo por PID indisponível: recursos são hipótese sustentada,
não atribuição exclusiva ao jogo. Nenhuma alteração em orçamento/modelo ou
encerramento de processo existente. Próxima fronteira: principal nova válida
com recursos disponíveis, depois verificar a cadeia positiva. P16 aberta.
Compilação/guardas/duas coletas/resumos conferidos; 109 hashes da ampla intactos.
SQLite próprio não isola TXT de resumo diário. Detalhes no checkpoint do roadmap.

### P16 — conclusão local de outra ocorrência, segunda transição — 01/10/2026

Mesmo RED histórico `55ee6435...`, sem identificar seu autor e sem contar outra
raiz por sintoma. Controle instalado: saída de A aceita → seleção B via ponte
real → retorno A → fase publicada em B. Quatro REDs (B vazio/parcial e B com
novo turno, em duas perguntas de capacidade); cinco controles iniciais GREEN.
Histórico A já correto. Contrato neutro de ID/texto capturado antes das rotas
locais, conferido no commit do owner do plano; recusa observável sem fallback
legado. Reutiliza checagem da proposta principal sem inventar origem LLM.

**174 focados/vizinhos GREEN**. Main real controlado a282c7...: receipt/arquivo
próprios confirmados antes da seleção, conclusão tardia recusada, B preservado;
sete turnos e código zero. GUI omitida só no controle, TCP ocupa cliente único.
SQLite próprio consultado `mode=ro`: três pares A/quatro B. Controle normal
9c2264... com GUI: sete turnos/arquivo/código zero, sem seleção. Voz silenciada.
Tentativas anteriores da sonda preservadas RED: socket sem atendimento enquanto
GUI conectada; depois expectativa incorreta de interromper roteiro, que mantém
snapshot identificado da saída de A. Expectativa corrigida com evidência;
barreiras do roteiro intactas. Detalhes/IDs/limites no checkpoint do roadmap.

Seis arquivos de produção, sonda existente e testes focados; worktree preservada.
Ampla: **9.343 passed, 1 skipped, 56 subtests passed** em 252,93 s, código zero;
log `.pytest_cache/p16_conclusao_local_ampla_conferida.log`. Auditoria
`.pytest_cache/p16_conclusao_local_ampla_hashes.json`: 109 arquivos Python
acompanhados sem mudança de hash durante a suíte. P16 parcial:
autor da troca histórica, crash nativo, origem própria positiva e sequência
física estável não foram encerrados. Sem commit/push.

### P16 — perda do plano, hipótese de restauração contextual — 01/10/2026

Continuação de `caminhos_absolutos_55ee6435...`, base `main`/`90a2fb8`.
Forma parcial criada às 22:43:31.559, antes do timeout; escrita física correta.
`atualizar_plano_turno({})` explica a forma posterior, não o esvaziamento inicial.
SQLite `mode=ro`, dois IDs, somente metadados: chat próprio c19210ad... termina
com dois pares e calma às 22:43:27.933; chat antigo f1dafa7f... é salvo no
encerramento às 22:44:13.810, com entrada antiga e acalmando-se, como o parcial.
Hipótese de restauração sustentada; pedido/autor/PID do writer ainda não provados.

Boot síncrono, inatividade de 600 s, registro local restaurando contexto e
renderização selecionando automaticamente foram falsificados. Escritores
explícitos conhecidos usam APIs já observadas; ausência global não certificada.
Sonda optativa passa a registrar chamadas do gerenciador real e seus IDs/pilhas,
sem título/texto. Falha de gravação não interfere no owner. Dois REDs antes
do candidato de diagnóstico; controle de limpeza já GREEN. **29 focados/vizinhos
aprovados**. Loops ef9eacee... e cdbf0154...: sete turnos, arquivos conferidos,
código zero, voz silenciada; último com 25 publicações e seis registros de
conversa, nenhuma troca/perda durante turnos. RED histórico não reproduzido.

Sem mudança de produção; só sonda e um módulo de testes. 107 Python iniciais
estáveis exceto sonda, total atual 108; HEAD/branch mantidos e diff sem erros.
Última ampla é a anterior (9.307), não repetida. Próxima fronteira: capturar
quem pede a troca entre efeito/finalização. P16 parcial; detalhes no roadmap.

### P16 — continuação de estado/encerramento, causas separadas — 01/10/2026

Base `main`, `90a2fb8`, worktree preservada. Controle instrumentado de caminhos
`caminhos_absolutos_dd30046da88a4c3baee8f3bd22754f06` passou sete turnos e
conteúdo físico, código zero; 25 publicações compartilhadas sem perda de plano.
Opção `--diagnosticar-plano` registra metadados/pilha nas três APIs de mutação,
sem produzir estado/evento/receipt. Pode alterar timing e não observa writers
diretos fora dessas APIs. RED `55ee6435...` continua aberto, sem patch do plano.

Lacuna de observabilidade demonstrada: sentinela desativava a captura antes
dos callbacks registrados anteriormente, que `atexit` executa depois. Dois
REDs em filhos descartáveis precederam o candidato no owner compartilhado
`diagnostico_encerramento`: handler/descritor permanecem até os callbacks
posteriores; desregistro explícito de teste libera ambos. Marker limita seu
alcance ao callback da sentinela. Nove controles do módulo e 20 vizinhos
passaram. Isso corrige a lacuna de captura, sem identificar/corrigir a causa
nativa histórica ou garantir captura após a finalização interna do handler.

Repetição real `p16_falha_recuperacao_bd12a6f56cea42558b1d11cc2e7d77fb`:
duas falhas sob lock sem mudança do arquivo, liberação após barreiras e escrita
exata; receipts distintos, `calma → irritada → acalmando-se`, código zero.
Voz/avatar habilitados e fila concluída; sem nova confirmação física de áudio
ou sequência visual. Falha nativa não reproduzida; não declarar seu reparo
pelo código zero. Artefatos de 30/09 preservados, detalhes no roadmap; P16 parcial.
Ampla: **9.307 aprovados, nenhuma falha, um ignorado/56 subtestes em 231,23 s**;
107 Python com hashes estáveis, HEAD/branch mantidos e diff sem erros.

### P16 — observação do receipt independente da porta de fala — 30/09/2026

Base `main`, `90a2fb8`, worktree preservada. Dois receipts reais de falha de
escrita e uma recuperação eram publicados, mas a emoção permanecia calma.
Primeira fronteira: avaliação acoplada a `falar_por_status`, contornado pela
fala própria de arquivos. TTL, vulnerabilidade e callback ausente falsificados;
replay dos receipts confirmou que o avaliador reconhece a sequência.

Dez REDs antes do candidato. Owner compartilhado `adaptador_resultado` observa
o receipt após aceitação do registrador; fala consome avaliação privada isolada
sem contar evento novamente. Recusa/falha de publicação não observam; falha ou
mutação do observador não certificam avaliação. IDs continuam organizando a
ocorrência, sem conceder autoridade ou deduplicação global entre instâncias.

Runtime `p16_falha_recuperacao_823da9ac0af7457a827625a1455d5784`: três turnos
finalizados, dois `falha_execucao` e um `conteudo_atualizado`; hash protegido
durante lock e conteúdo físico `P16 RECUPERADA` depois da liberação.
`calma 1 → irritada 1 → acalmando-se 1`, com evidência ligada ao receipt do
turno. Pedro confirmou as três falas completas. Avatar irritado falando foi
observado em captura; sequência visual completa não certificada. Processo
principal saiu `0xc000041d` depois do callback da sentinela em `atexit`; essa
marca não conclui os demais callbacks. Limites de encerramento ficam
na investigação de infraestrutura já aberta, sem patch especulativo.

### Identidade de caminho explícito antes da continuidade — 30/09/2026

Pedido adicional de Pedro. Normalização e lookup por basename podiam perder
drive/separadores/grafia ou substituir o alvo por outro arquivo recente. Serviço
de arquivos aceita caminho absoluto, espaços e aspas; não remover suas guardas.
REDs locais/seis instalados antes do candidato em nome natural, roteador,
resolver contextual e gate de argumentos do coordenador. Catálogo vivo e
perguntas naturais explicam uso/indisponibilidade sem executar. Caminho não é
autorização; pedidos negativos/hipotéticos/capacidade permanecem sem efeito.

Raiz adicional demonstrada, sem misturar com identidade: append retirava “linha”
de conteúdo **citado** antes do executor. Seis REDs em caminho/basename/pronome/
elipse; helper único conserva literal citado e mantém moldura sem aspas.

Dois loops completos de sete turnos com código zero e arquivo relido:
`caminhos_absolutos_53a53d3eb5aa4d70ae45158b10455070` e
`caminhos_absolutos_c8bcf0ca678047ea81f5d77463280625`. Alvos homônimos separados,
controle intacto, escrita/append exatos e falha de leitura ausente sem fallback
para outro arquivo. Voz silenciada nesses controles. Seleção final: **146
aprovados**, com sobreposição aos controles anteriores. Ampla estável: **9.303
aprovados, nenhuma falha, um ignorado/56 subtestes em 230,14 s**, 105 hashes
Python iguais, HEAD/branch mantidos e diff sem erros.

### Pendências observadas no loop — 30/09/2026

`caminhos_absolutos_55ee643598eb41f6a2881bd90f87db98` perdeu ID/receipts do plano
após a escrita física no terceiro turno. Arquivo correto; finalização RED.
Hashes descartam edição concorrente de produção. Duas repetições com mesmo
roteiro/diagnóstico passaram, falsificando falha inevitável; writer causal
ainda não localizado. Não aceitar plano vazio nem aumentar timeout para ocultar.

Encerramento P16: Windows registra `0xc0000005` e `0xc000041d` no mesmo PID
principal, WER com módulo desconhecido. Diagnóstico `0x8001010d` do cliente
Terminal também aparece no loop de código zero; não prova morte do cliente ou
causa do erro principal. Associado como novo achado à investigação histórica
de infraestrutura/saída, sem afirmar causa compartilhada. P16 parcial;
detalhes/artefatos no checkpoint do roadmap. Nenhum commit/push/desligamento.

### P16 — continuação da procedência da leitura semântica — 30/09/2026

Mesma perda de fonte já registrada; não acrescentar raiz por frase emocional.
Base `main`, `90a2fb8`, worktree paralela preservada. O preparador preferia
leitura do reparo com rótulo principal; o publicador conferia turno, sem
comparar a leitura à emissão capturada. Normalização pura e ausência de
autorização foram falsificadas como causas da substituição. Onze REDs do
preparo/publicação/transporte e um da API legada precederam seus candidatos.

Leitura original permanece canônica; diagnóstico reparado fica separado,
rotulado pelo host e recusado como fonte de evento. Runtime e publicador
reutilizam a extração da principal tipada; publicação deriva sua própria cópia
e preserva CAS/ocorrência. Sem parser paralelo, chamada adicional ou promoção
de contexto a autoridade. Diagnóstico cobre somente o bruto final disponível.

270 focados/vizinhos GREEN, incluindo dez da composição instalada. Fixtures
antigas passaram a fornecer `leitura_turno` no bruto, mantendo seus controles
de autorização/transação. Portas externas/persistência isoladas não provam
voz/avatar físicos ou interpretação temporal geral. Ampla estável: **9.221
aprovados, nenhuma falha, um ignorado e 56 subtestes em 208,94 s**, 94 Python
com hashes iguais, HEAD/branch preservados e diff limpo. Detalhes e limites
no checkpoint do roadmap.
P16 permanece parcial para o loop desktop contínuo; nenhum commit/push.

### Continuação da correlação P16/AUT-01 — identidade de solicitação — 30/09/2026

Mesma pendência de correlação já registrada, sem outro ID por frase/domínio.
Base `main`, `90a2fb8`, worktree paralela preservada. As 16 falhas históricas
foram localizadas: 12 mesclas por intent, uma identidade ausente no host, três
sondas com chave de callback incorreta. Corrigir a porta dessas sondas permitiu
reproduzir a perda de ID no dispatcher antes de aplicar o candidato.

Owner compartilhado de resultado identifica cópias após validação, recusa
aliases ambíguos e remove IDs/receipts propostos pelo modelo. Dispatcher,
coordenador e adaptador conservam a identidade no envelope. Helper comum dos
dois writers mescla somente mesma ID + intenção canônica; sem ID mantém
ocorrências independentes. Proposta republicada preserva receipt resolvido;
resultado novo não herda confirmação anterior. Contexto de última ação também
exige a mesma ocorrência. Copiador canônico protege params sincronizados.

REDs focados demonstraram a primeira fronteira; controles falsificaram falha
geral do executor e necessidade de apagar receipts legítimos. Sete controles
da composição instalada passaram e replay do writer histórico reproduziu a
transferência de evidência. SQLite temporário/portas externas isoladas;
nenhuma abertura, áudio ou avatar físicos certificados.

Primeira ampla estável: 9.184 GREEN, três RED, um ignorado e 56 subtestes,
222,02 s, hashes iguais em 88 Python. As três fixtures exigiam deduplicação
legada por intent, comando sem ID host ou dois feedbacks no mesmo plano;
ajustes preservam provas de efeito e usam início real de turnos separados.
Seus três módulos passaram em 100 testes. Também 220 focados de identidade,
contexto/continuidade/composição passaram, com sobreposição. Ampla seguinte:
9.187 aprovados/um ignorado/56 subtestes, 213,62 s, 91 hashes Python iguais.
Revisão encontrou recusa de receipt ignorada pelo adaptador: quatro REDs
precederam o refinamento de False explícito no publicador e limpeza dos
marcadores da tentativa anterior. 177 focados/composição passaram. Ampla final
do refinamento: **9.190 aprovados, nenhuma falha, um ignorado e 56 subtestes em
214,32 s**, 91 hashes Python iguais, HEAD/branch mantidos, mutex próprio e
diff limpo. Detalhes no checkpoint do roadmap de personalidade.

P16/AUT-01 continuam parciais. Leitura semântica do reparo ainda pode receber
origem da principal (reprodução local, sem candidato); loop físico mantém
evidência própria. IDs organizam receipts, sem conceder autoridade. Nenhum
commit/push ou desligamento.

### AUT-01 — continuação do callback tardio: ocorrência na publicação, 30/09/2026

Pedido de Pedro para iniciar o plano de assistente autônoma. Mesma pendência de
correlação já registrada, sem ID por frase ou domínio. Base `main`, `90a2fb8`,
worktree paralela preservada. Nova ocorrência coerente com a mesma frase era
atualizada por retorno antigo: writer não recebia ocorrência esperada; leitura
semântica anterior também publicava sem vínculo. Controles falsificaram falha
geral do filtro e necessidade de apagar receipts do mesmo turno.

Candidato reusa a principal tipada e o validador canônico de ocorrência dentro
da transação. Semântica usa origem e CAS do snapshot; runtime recebe callbacks
vinculados da composição e para após recusa pré/pós-dispatch. API legada mantém
compatibilidade sem certificar atomicidade. Fase técnica suprimida identificada
na revisão como consumidor adicional do mesmo contrato.

Trinta e cinco testes locais e 13 da composição principal protegem a fronteira;
446 com vizinhos passaram após o refinamento técnico. Regressão ampla final:
**8.975 aprovados, um ignorado e 56 subtestes aprovados em 202,48 s**, sem falhas.
HEAD preservado, hashes do candidato estáveis e `git diff --check` limpo.

Checkpoint e resultados detalhados no
[plano AUT-01](../planos/PLANO_LAYLAY_ASSISTENTE_AUTONOMA.md#9-checkpoint-aut-01--ocorrência-esperada-nas-publicações-30092026).
O runtime usado é o objeto instalado, sob mutex real de identidade própria.
Provas com portas externas isoladas não certificam
executor físico ou loop da sessão aberta. Mescla por intent, adaptador de receipt
e janela posterior à publicação aceita continuam fora desta entrega. Não encerrar
AUT-01 ou personalidade P16 pelo GREEN intermediário. Nenhum commit.

Atualizado em **23/09/2026**, por Astra e SOL, a pedido do Pedro.

### P01 — generalização v6 e validade de critério revogado, 28/09/2026

**07/10 — hierarquia/ID, 80 brutos auditados:** papel base 7/10 nas duas
rodadas; hierarquia 10/10 e 9/10, com ou sem ID uniforme. E04A/U04 recuperados
nas duas; ID isolado não resolve. E03A oscila apesar de requisição idêntica.
Conjunto base 4/4; hierarquia 6/4; hierarquia+ID 5/4: não houve ganho repetido
de evidência completa. E04A/E04B sobrepõem foco; U02 não copia trecho contíguo;
N06 falha apenas no marcador lexical, não prova erro de sentido. Fonte inteira
e identidade host preservadas. 18 testes novos e 1.493 regressivos passaram
(contagens sobrepostas). Protocolo, hashes, tabela e limites no plano.
Próximo: validar generalização/estabilidade e investigar seleção literal como
fronteira distinta, sem afrouxar guardas. Mesma P01 aberta, sem produção/treino.

**07/10 — hierarquia/ID, protocolo pré-consulta:** quatro braços com dez
fontes conhecidas e duas repetições. Fonte/offsets e host intactos; fatores
são caminho sintático redundante e etiqueta de transporte `foco.id=c1`.
Reutiliza árvore de aspas existente; E05A/B protegem identidade de ocorrências
iguais. Requisição efetiva validada antes da aferição delegada. 80 consultas
pendentes, sem produção ou treino; critérios e hashes no plano.

**07/10 — moldura/foco, 36 brutos auditados:** E04A/U04 erram papel nas fontes
aninhadas e acertam nas versões planas/internas, nas duas repetições; E04B/N03
preservam papel correto. E03A só recupera nome sem a ressalva; antepô-la continua
errado, mesmo selecionando “a exposição foi intitulada”. Host/foco autênticos;
ausência de pista e viés apenas de posição final não explicam esses REDs.
Pontuação, profundidade, IDs e offsets variam juntos: não declarar aninhamento
como causa isolada. E04B mantém sobreposição literal em todas as versões;
U02 mantém paráfrase. 14 testes novos, 35 focados, 1.475 na regressão (sobrepostos).
Próximo contraste proposto: hierarquia sintática explícita e autenticada, fonte
integral preservada e controle de identidade/representação. Ainda sem candidato
em produção; hash, hipóteses e limites no plano. Mesma P01 aberta.

**07/10 — moldura/foco, protocolo pré-consulta:** mesmo proponente e oito
exemplos; 18 fontes variantes em duas repetições. Contrastar citação aninhada,
plana com dois-pontos e conteúdo interno; no título hipotético, retirar ou
antepor a ressalva. E03B/U02/N06 são controles de interpretação/literalidade/
cobertura. Não é patch para remover contexto; coleta pendente, hashes no plano.

**07/10 — ensino contrastivo aferido:** 96 consultas brutas revalidadas;
duas repetições no painel novo de 24 casos. Papel 12→21 em ambas, conjunto
5→16 e 5→17; indeterminação 0→5 de 6 sem falsas abstenções nos 18 conclusivos.
Critério descritivo atendido, não aprovação de produção. Regressão individual
E04A persiste apesar do empate agregado de nomes; E03A/U04 também erram papel.
U04 seleciona pista correta e erra interpretação; U02 acerta indeterminação
e inventa parte do trecho; E04B inclui foco na seleção. N06/E06B ficam fora
da cobertura lexical, o que não basta para declará-los bugs. 21 testes novos,
136 focados e 1.461 na regressão das sondas/contrato (sobrepostos). Artefato,
hashes e limites no plano; próxima fronteira é função do foco em molduras
aninhadas/concessivas, sem relaxar literalidade. Produção e treino intactos.

**07/10 — ensino contrastivo, protocolo pré-consulta:** oito demonstrações
fixas e 24 avaliações novas/separadas; duas repetições de dois braços (96
chamadas). Só mensagens de exemplos variam; materializador, schema e opções
preservados. Ganho deve se repetir sem reduzir contagem de nenhuma classe
conclusiva nem elevar falsos indeterminados. Instrumento e hashes no plano;
coleta pendente neste registro, sem treino de pesos ou patch de produção.

**07/10 — fatorial concluído, nenhuma variante promovida:** 128 respostas
brutas revalidadas, todas completas/HTTP200/shape válido. Na ordem base,
renomeação, prioridade, ambas: papel 24/23/19/18 de 32; conjunto local
(papel + vínculo + pista) 12/9/10/6. Prioridade melhora geometria, mas perde
nomes/operações para outros rótulos conclusivos; indeterminação 0/0/1/1 de 4,
sem falsos indeterminados nos 28 conclusivos. U02 copia pista explícita de
incerteza e erra papel nos quatro braços. Renomear não reduz cópia do foco.
Base também variou 25→24 frente à coleta anterior com requisições idênticas:
não confundir variação com efeito causal comprovado. 1.443 testes relevantes
verdes validam instrumento/contratos, não semântica. Hashes, perdas e limites
no plano; próximo contraste proposto é ensino por exemplos separados de nova
avaliação congelada, ainda não executado. Sem produção, treino ou promoção.

**07/10 — fatorial unidade/indeterminação, protocolo pré-consulta:** comparar
nome `predicado` versus `trecho_externo` e instrução de decidir indeterminação
primeiro, mantendo fonte/materializador/guardas. 32 casos conhecidos × quatro
variantes = 128 chamadas; ordem balanceada, referências intactas. Medir rótulo,
geometria, repetição do foco e falsas abstenções nas fontes conclusivas. 19
testes novos verdes; coleta pendente, protocolo/hash no plano. Mesma P01,
sem alteração de produção, treino ou memória.

**07/10 — materialização host, resultado conferido:** 64/64 HTTP200/JSON/shape/
stop. No contraste contemporâneo, rótulo 24/32 → 25/32, vínculo 8/32 → 16/32,
rótulo + vínculo + pista no predicado 4/32 → 12/32. Há três ganhos e duas
perdas de rótulo; abstenção piora de 1/4 para 0/4. Baseline histórico 23/32
oscilou para 24/32 com mesma requisição: não atribuir essa mudança ao candidato.
Nove predicados sem âncora e sete sobrepostos; oito dos nove mudaram aspas,
mas restaurar apenas grafia em diagnóstico ainda deixa sobreposição/ambiguidade.
H03B parafraseia; H10A escolhe outra ação; U02 seleciona incerteza mas erra papel.
26 novos / 96 focados / 1.424 relevantes verdes, sobrepostos, apenas offline.
Artefato `sonda_predicado_host_v1_ab.jsonl`; hashes/decisão no plano. Manter
materialização como candidato de diagnóstico e investigar unidade contextual
externa e abstenção antes de promoção. Produção/treino intactos, P01 aberta.

**07/10 — predicado proposto / intervalo host, protocolo pré-consulta:**
modelo copia só predicado e propõe papel; host ancora na fonte integral e
materializa intervalo por offsets, reutilizando contrato e guarda anteriores.
26 novos / 96 focados verdes sobrepostos; inclui repetição, aspas aninhadas,
vazio, predicado irrelevante e ambiguidade. Comparação composta em 32 casos
conhecidos, 64 consultas, mesmas referências; coleta pendente. Isso reduz
recópia e não transforma geometria em interpretação. Protocolo/hash no plano;
produção/treino preservados, mesma P01 aberta.

**07/10 — vínculo explícito, coleta encerrada sem promoção:** 64 respostas
HTTP200/JSON/shape/stop, duas recontagens pelo bruto. Rótulos 22/32 → 23/32,
três ganhos/duas perdas, pares 7/12 nos dois; vínculo estrutural só 8/32,
proposta composta local 5/32, abstenção 0/4 → 1/4. Primeira divergência nos
23 enunciados sem âncora: troca de aspas tipográficas por ASCII. Contrafactual
de leitura não altera escore; mesmo restaurando grafia, H11A permanece com
objeto ambíguo e H10A com predicado sobreposto. H07A ancora a pista de título
mas erra papel: cópia não explica toda a interpretação. H04A demonstra
predicado de horário passando estruturalmente sem enquadrar designação.
27 novos / 1.398 relevantes verdes, sobrepostos, apenas offline. Artefato
`sonda_vinculo_enunciado_v1_ab.jsonl` e hashes no plano. Não promover esta
interface, não relaxar guarda, não treinar. Próxima fronteira: separar escolha
semântica e reprodução literal pelo host, sem repetir seleção por IDs já
falsificada. Produção preservada; mesma P01 aberta, sem commit.

**07/10 — vínculo enunciado–ocorrência, protocolo antes da coleta:** nova
sonda offline reutiliza contrato de proposições e identidade canônica; não
cria parser de nomes. Propõe enunciado/predicado/papel, exige objeto nos
offsets exatos do foco e predicado externo. Estrutura não certifica relação
semântica. Mesmo painel conhecido de 32, 64 consultas independentes,
baseline direto intacto, entrada integral sem recortes-oráculo ou gabarito.
Muda prompt + schema, portanto comparação composta. Cobertura lexical no
enunciado/predicado separada do rótulo e do vínculo; vazio conserva revisão.
26 novos / 108 focados verdes (sobrepostos); coleta pendente. Protocolo/hash
em `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md`. Produção/treino não alterados,
P01 aberta, sem commit.

07/10, ablação concluída: quatro intervenções manuais, atual 2/4 → 1/4
(um ganho/duas perdas), direto 1/4 → 3/4 (dois ganhos/nenhuma perda).
Seis controles de input idêntico por prompt tiveram rótulos estáveis;
H02A/H06A ainda erram sem concorrente externo e indeterminação 0/4 em ambos.
Falsificada explicação exclusiva por segundo comando/ocorrência; recortar
não é solução geral. 40/40 HTTP/JSON/shape/stop e mapas revalidados no bruto.
Artefato `sonda_ablacao_contexto_papel_v1.jsonl`, SHA256
`025891330c3cc43350be4ba04336d8396d5bfad6e025374af68691866c7cbb1c`.
18 novos/82 focados/1.371 relevantes verdes (sobrepostos); três testes provam uso do contrato
existente de proposições para ancorar objetos iguais em enunciados distintos,
recusar predicado emprestado e não promover ancoragem à verdade. Próximo:
proposta explícita de vínculo enunciado–ocorrência e indeterminação, não
novo parser ou recorte-oráculo de produção. P01 aberta, sem treino/commit.

07/10, diagnóstico pré-consulta por ablação manual: quatro contextos
recortados + seis controles de input idêntico (quatro indeterminados),
dois prompts congelados, 40 chamadas previstas. Ocorrência preservada por
offset, inclusive segunda string repetida. 15 novos/36 focados verdes,
coleta pendente. Recorte-oráculo não é seletor de produção; muda também
sintaxe/comprimento, logo não prova sozinho causa interna. A guarda literal
corretamente não certifica papel. Sem produção/treino/novo gabarito/commit.

07/10, transferência concluída sem ajustar os prompts: **20/32 → 22/32**,
6/12 → 7/12 pares; quatro ganhos e **duas perdas** (H11A, H05B). Ambiguidade
explícita 0/4 em ambos. Dez erros na leitura direta permanecem em P01, não
viram dez roots. As 64 respostas HTTP200/JSON/shape/stop foram revalidadas
no bruto, focos/offsets e referências autênticos; primeira RED na atribuição
de papel, não transporte/host. Artefato `sonda_papel_transferencia_v1_ab.jsonl`,
SHA256 `2e2c9aa636d79afe2154abfde59ea24be29d454bbaed55d6e6627d0465642075`.
21 novos/67 focados/1.353 relevantes verdes (sobrepostos). Ganho modesto,
com regressões e sem revisão humana independente: **não promover**. Próximo
contrato a investigar: predicação vinculada à ocorrência e indeterminação,
sem consolidar prematuramente suas hipóteses internas. Sem produção/treino/commit.

07/10, protocolo de transferência pré-consulta: 32 casos novos, 12 pares
nome/operação e quatro controles de cada tipo estado/indeterminado; 64
chamadas previstas, 16 AB/16 BA, mesmos prompts congelados. Painel e revisão
local fixados por hash antes de consultar, sem gabarito no modelo. 21 testes
novos/67 focados verdes (sobrepostos). Não é revisão humana independente
nem corpus externo; não mudar produção/treino ou retocar prompts pelo resultado.
Protocolo completo no plano; coleta pendente neste checkpoint.

07/10, conclusão do contraste abaixo, sem ajuste durante a coleta:
**11/20 → 16/20 papéis; 3/8 → 6/8 pares**. Cinco ganhos, nenhuma perda;
Q02A/Q06A/Q06B/Q08B continuam errados na leitura direta, Q08B apenas troca
de erro. Todas as 40 HTTP200/JSON/shape/stop, bruto e requisições revalidados,
referências intactas. Artefato `sonda_papel_leitura_direta_v1_ab_replay.jsonl`,
SHA256 `65bd3c3870df9417dce5e674ff4058262484a14f54fc2f03ef366fa0ad3583be`.
46 novos/1.332 relevantes verdes (sobrepostos). Candidato promissor em painel
conhecido, não holdout nem runtime; primeira RED restante ainda atribuição
de papel no bruto. Próximo: casos independentes pré-congelados, mesmos
prompts, antes de promover qualquer integração. Sem produção/treino/commit.

07/10, próximo contraste congelado antes da coleta: `sonda_papel_leitura_direta_v1`,
mesma fonte/foco/schema/opções/gabarito em 20 casos e 8 pares, alterando apenas
instrução de sistema. 46 testes locais verdes; 40 consultas independentes,
10 AB/10 BA planejadas. Testa a formulação da leitura contextual, não cria
regra para frases históricas nem nova raiz; não promove produção ou treino.
Protocolo e hashes no plano de ensino; coleta ainda pendente neste checkpoint.

07/10, auditoria da classificação com fonte/foco integral versus mesmo input
com contexto externo explícito (coleta com contexto de 06/10): **11/20 e 3/8
pares nos dois braços**. Um ganho Q03A e uma perda Q05B; Q01B/Q06B trocam
erro por outro erro. Indeterminação Q08A/B zero/2 em ambos. Todas as 40
HTTP200/JSON/shape/stop; rótulos errados já no bruto, não rejeição do host.
Primeiro RED observado é atribuição contextual de papel, não delimitação.
Contexto extra não trouxe ganho líquido; não promover para runtime/treino.

**74 próprios, 691 focados e 1.286 regressivos relevantes GREEN**, sobrepostos.
Tentativa ampla interrompida sem resultado de pytest; rerun na retomada
confirmou 1.286. Brutos, denominador, referências, req/host/inventário e
resumo recalculados. Artefato exclusivo
`resultados_testes/sonda_papel_contexto_explicito_v1_ab_replay.jsonl`, SHA-256
`6f5329010a4815ee37a9d97227e5aa9cb981e742e8138b8ce4f8020cfdda425d`.
Próxima hipótese a estudar: predicado que enquadra o foco versus aparência
de ordem/negação, com indeterminação separada de autorização. Não causa
única provada, não implementada nem nova raiz. P01 continua aberta;
produção/worktree e histórico preservados, nenhum commit. Detalhes no plano.

06/10, host delimita todos os contextos externos e Qwen propõe IDs: **20/20
seleções literais válidas/concluídas**, contra zero/20 do controle de índices.
Mas o modelo seleciona `e0/e1` nos vinte casos, empatando com o controle
"selecionar tudo" sem LLM. Cobertura lexical 20/20/oito pares não demonstra
escolha discriminativa ou papel. GREEN estrutural offline, P01 semântica aberta.

40 HTTP200/JSON/stop, sem truncamento; 42 linhas, entrada/host/inventário/
gold/ordem/resumo bruto e disjunção conferidos. **60 próprios, 617 focados,
1.212 regressivos relevantes GREEN**, sobrepostos. Nenhum patch de produção,
treino, materializador ou autoridade. Artefato exclusivo
`resultados_testes/sonda_contextos_enumerados_v1_ab_replay.jsonl`, SHA-256
`506bcd57356b53ab5f54621f5f7d1d1471ffb631d7f27316debcb73c9cfd9905`.
Mesmo HEAD/main/worktree preservada; nenhum commit. Próxima proposta: avaliar
papel com contexto completo versus externo explícito, sem repetir uma seleção
que ainda não supera o baseline sem modelo. Não executada, detalhes no plano.

06/10, seleção de contexto **sem alvo fornecido**, cópia versus índices com
schema em ambos, não promovida. Mesmos 20 casos/oito pares/referências,
40 chamadas reais ao Qwen: índices 20 vazios; cópia 20 recusadas por ausência
de ocorrência externa única. Zero seleção externa válida nos dois. Todas
HTTP200/JSON/`done=True/stop`, sem truncamento. Brutos de cópia: 20 incluem
o foco, 14 ocorrem exatamente na fonte e seis trocam aspas; onze contêm
âncoras lexicais, mas não cumprem delimitação e não recebem crédito semântico.
Primeira fronteira RED observada é a proposta de apoio externo, não o parse
ou a execução. Não atribuir ausência geral de compreensão ou causa interna
única. Guarda preservada, nenhuma segunda etapa/treino/produção alterada.

**72 próprios, 557 focados, 1.152 regressivos relevantes GREEN**, sobrepostos;
uma expectativa de ambiguidade da fixture foi corrigida, não a guarda.
Replay bruto/denominador/requisições/fonte/gold/ordem autenticados. Artefato
`resultados_testes/sonda_contexto_copia_indices_v1_ab_replay.jsonl`, SHA-256
`7ee84d1406ea1d24c3751f6df201bb1298c7b45ddec194cc2d09af03bc4c4bc0`.
Próxima fronteira proposta: host enumerar todos os segmentos externos por
posição e LLM selecionar IDs sem gold/ranking. Ainda não implementada;
mesma P01 aberta, sem criar outra raiz, liberação neural ou commit.

06/10, cópia literal versus índices com **schema nos dois braços**, não promovido.
Seis casos/referências de calibração preservados; alvo explícito, não tarefa
semântica. Positivos **1/3 índices vs 2/3 cópia**, negativos **2/3 vs 1/3**:
empate global 3/6, sem vencedor geral. L02 ganha cópia autêntica de `lume`,
L01 vazio em ambos e L03 correto em ambos. L05/cópia ecoa `lume` só no foco;
L06/cópia ecoa ocorrência ambígua: guarda recusa, sem transformar em abstênção.
L06/índices abstém corretamente; L05/índices viola limites. Não esconder
negativos para promover cópia, nem interpretar eco como localização provada.

Doze HTTP200/JSON/término `stop`, referências pré-consulta, ordem 3 AB/BA,
entrada/opções idênticas, bruto preservado e resumo recalculado conferidos.
Prompt/schema mudam somente pela representação, não é comparação de schema
isolado. Duração acumulada 11,514/7,611 s, sem generalizar eficiência. Digest
igual nos extremos, não invariância contínua. Dois REDs de tradução de cópia
ausente/ambígua para vazio no protótipo; **45 próprios, 485 focados, 1.080
regressivos relevantes GREEN** sobrepostos. Artefato exclusivo
`resultados_testes/sonda_copia_indices_literal_v1_ab.jsonl`, SHA-256
`3e2eac546335f5332d2d59bd52bca0abd63c8c36653259a80da27a4229759f1a`.

Próxima fronteira planejada: seleção de contexto sem fornecer o alvo de apoio
na entrada, comparando representações com schema no painel semântico preservado.
Host segue dono de ocorrência/offsets, LLM apenas propõe apoio. Não executado
aqui, nenhum treinamento ou migração por empate estrutural. P01 aberta,
produção/memória/rede ativa/runtime intactos; worktree paralela e histórico
preservados, nenhum commit. Detalhes no plano de ensino.

06/10, calibração literal explícita, **não promovida**. Seis fontes sintéticas
separadas, três positivos e três negativos; esperado host congelado/calculado
antes da geração, sem índices ou tipo do caso no prompt. Reuso das guardas/
tokenização/captura, tarefa sem papel. Positivos **1/3 em ambos os formatos**;
negativos **2/3 schema vs 1/3 JSON genérico**. L03 materializa `bruma clara`
corretamente `[0,2)` em ambos, falsificando incapacidade universal de emitir
coordenadas ou falha universal do materializador, mas não prova confiabilidade.
L01/L02 (`lume` antes/depois) retornam vazio; não inferir causa por tamanho/grafia.
L05/alvo no foco propõe índices fora dos cinco tokens: `[9,13)`/`[2,6)`,
rejeitados sem reparar. L04/ausente dá `{}` inválido no genérico; L06/ambíguo
dá vazio correto em ambos. HTTP200/JSON/término `stop` em todas as 12 consultas;
sem corte/erro de parse que explique as falhas. Sem taxa agregada que esconda
os positivos RED e sem considerar vazio prova de contexto ausente.

Artefato exclusivo `resultados_testes/sonda_extracao_literal_v1_calibracao.jsonl`,
SHA-256 `0745102a0353c5a24287366a3530d3d650cbe54ab9e8d7eab4d642a1320ddd91`,
14 linhas; resumo bruto recalculado/ordem 3 AB/BA conferidos. Digest igual nos
extremos, não determinismo contínuo. Dois REDs do oráculo no protótipo antes
da guarda de escopo/unicidade; **44 próprios, 440 focados, 1.035 regressivos
relevantes GREEN** com sobreposição, sem concluir qualidade semântica/runtime.
Base `main/90a2fb8`, histórico/worktree preservados. Próximo contraste planejado:
cópia literal versus índices na mesma tarefa explícita, host dono de ocorrência/
offsets, sem usar copia como prova semântica nem migrar por um pequeno placar.
Não executado aqui. P01 aberta, sem produção, treino, memória, rede ativa,
efeitos externos ou commit. Detalhes no checkpoint do plano de ensino.

06/10, controle isolado do schema na primeira seleção, **não promovido**.
Mesmo prompt/fonte/foco/tokens/opções; apenas `format` muda entre schema
restritivo e JSON genérico. **20/20 listas vazias em cada braço**, zero
intervalos/seleções válidas/cobertura local. Todas as 40 respostas HTTP200,
JSON parseado, `done=true`, `done_reason=stop`, oito tokens cada; conteúdo bruto
uniforme `{"evidencias": []}`. Sem erro de transporte ou truncamento observado.
Logo schema restritivo não é explicação suficiente do zero nesta configuração;
parse que apagaria trechos também não explica a coleta. Modo JSON continua
nos dois braços: não concluir ausência de toda influência do formato, nem
incapacidade do modelo ou qualidade zero de uma segunda etapa não executada.

Base `main/90a2fb8`, worktree paralela/histórico preservados; 10 AB/10 BA,
requisições e resumo recalculados, digest igual nos extremos (não invariância
contínua). Durações acumuladas 23,627 s / 18,873 s, sem alegar ganho de latência.
Instrumento/teste novos `sonda_schema_selecao_v1`, sem alterar sondas antigas.
Três REDs de captura antes do parse no protótipo; **44 próprios, 396 focados,
991 regressivos relevantes** GREEN, com sobreposição. Artefato exclusivo
`resultados_testes/sonda_schema_selecao_v1_ab_replay.jsonl`, SHA-256
`a4fa8e2780d7af2c7f4fe2439bfce534cdbd2d604f9629479eccc77dc0a5aec6`.
Preserva texto HTTP/conteúdo/finalização, não bytes/headers completos.

Próximo controle planejado: extração literal explícita em fontes sintéticas
separadas, para distinguir capacidade de coordenadas da seleção semântica.
Positivos/negativos congelados antes de consulta, sem passar índices/resposta
nem usar o gabarito semântico como instrução. Não executado aqui. Mesma raiz
P01 permanece aberta; produção, treino, memória, rede ativa e runtime da
Laylay não alterados. Provas e limites no plano de ensino. Nenhum commit.

06/10, retomada do desenho de seleção externa antes do papel, **não promovido**.
Mesmo HEAD `main/90a2fb8`, painel/revisão e dependências congelados; alterações
paralelas preservadas. Qwen local real em replay dirigido, não runtime da Laylay:
controle acoplado **15/20 papéis brutos alinhados, 6/8 pares completos**,
mas **0/20 evidências válidas**, 19 listas vazias e um intervalo vazio Q09A
(`inicio=fim=20`). Envelope de papel válido 19/20, alinhado conferido 14/20;
papel bruto é aferido independentemente da seleção.

Candidato com seleção separada: **20 listas vazias, zero elegíveis e zero
segundas consultas**. Apoio/papel locais conjuntos 0/20 em ambos; a qualidade
condicional da segunda etapa é não estimável, não acurácia zero. Não fabricar
papel `indeterminado` ou ausência a partir da abstenção. Primeira fronteira
observada permanece na proposta do selecionador, antes da guarda/cobertura.
Separar tarefas neste pacote não resolveu esse RED; não prova incapacidade
do modelo, inutilidade do contexto ou falha universal de dois estágios.

Coleta completa: 40 consultas, zero erros, 42 linhas, 10 AB/10 BA. Durações
acumuladas 44,676 s / 36,022 s; digest igual nas leituras extremas, não prova
de invariância contínua. Variação do controle histórico 14/20 → 15/20 impede
atribuir diferenças entre rodadas ao candidato. Artefato exclusivo
`resultados_testes/sonda_vinculo_duas_etapas_v1_ab_replay.jsonl`, SHA-256
`5c188b8ec0c03847a1fa953d3d574ed5eb5536e085acd153c2ed1d779b91b240`;
script/teste novos `sonda_vinculo_duas_etapas_v1`. **187 próprios, 352 focados,
947 regressivos relevantes** GREEN, sobrepostos; 19 REDs da guarda de duração
reproduzidos nesta retomada antes do candidato mínimo no instrumento.
JSON parseado preservado, sem HTTP bruto/motivo de término. Próximo controle
planejado: schema restritivo versus JSON genérico na mesma primeira tarefa,
com registro bruto, sem forçar seleção. Não executado aqui; P01 aberta,
nenhuma produção, treino, memória, promoção neural ou commit. Provas completas
no checkpoint de 06/10 do plano de ensino; não adicionar outra raiz por caso.

29/09, replay diagnóstico de coordenadas, **não promovido**. Reusa os 20
casos/gabarito congelados e a mesma tarefa de vínculo nos dois braços;
diferença única: retirar `inicio/fim` dos tokens enviados ao Qwen. Host
mantém offsets autênticos; foco/aspas ainda expõem posições de caracteres.
Controle e projeção: **12/20 vs 14/20** papéis alinhados; **3/8 vs 5/8**
pares completos. **0/20 evidências válidas em ambos**: listas vazias
**15 vs 18**, envelopes de intervalo inválidos **5 vs 2**. Redução de
envelopes inválidos não é recuperação de evidência nem suporte semântico.

Três melhorias de papel (Q02A/Q03B/Q04B), uma regressão (Q05A), Q01B troca
de erro. Não usar como holdout novo, prova de causa exclusiva, ganho geral
ou autorização de treino/runtime. Controle repetido também mudou respostas
em relação ao A/B histórico, apesar de temperatura 0; conservar os dois.
Digest igual no início/fim desta rodada, sem garantia de invariância contínua.
Retirar os offsets dos tokens não basta para superar o RED de evidência.

**64 testes novos; 760 regressivos relevantes verdes**, com sobreposição;
RED da projeção reproduzido antes da mudança, validação preserva payload,
materialização, rejeição atômica e métrica de papel independente. Script/teste
novos `sonda_coordenadas_vinculo_v1`; artefato exclusivo
`resultados_testes/sonda_coordenadas_vinculo_v1_ab_replay.jsonl`.
Próxima fronteira: estudar seleção literal externa separada da classificação
de papel, sem obrigar evidência falsa nem deduzir ausência de uma lista vazia.
Produção, memória, treino e runtime não alterados; nenhum commit.

29/09, vínculo contextual com intervalos: contraste offline **não promovido**.
20 fontes novas e revisão congeladas antes da geração; mesmo Qwen, entrada
tokenizada e foco nos dois braços. Baseline mantém prompt/schema do papel;
candidato acrescenta proposta de até dois intervalos externos ao foco.
Rótulos brutos alinhados: **14/20 direto vs 12/20 com evidências**; pares
contextuais completos: **5/8 vs 2/8**. Não comparar ao 10/16 anterior, de
outro painel e outra apresentação. Este A/B não demonstrou benefício.

No candidato, **0/20 evidências literais válidas**: 15 listas vazias e cinco
propostas com intervalos inválidos. Os 12 rótulos alinhados foram contados
independentemente dessa guarda; não é queda artificial causada pelo veto.
A primeira fronteira da evidência falha antes da cobertura das pistas: não
há vínculo materializado que permita avaliar suporte semântico. Entrada
expõe `inicio/fim` de caracteres, enquanto saída pede `inicio/fim` de IDs
de tokens; ambiguidade de coordenadas é hipótese de apresentação, ainda não
contrastada, não causa exclusiva demonstrada dos erros de papel.

Reuso do tokenizador, fonte/foco e roles existentes; **58 testes novos, 696
regressivos relevantes verdes** (141 focados com sobreposição). RED da própria
sonda permitia consultar foco citado vazio; guarda mínima passou a recusá-lo.
Artefato preservado: `resultados_testes/sonda_vinculo_contextual_v1_ab_primeira.jsonl`.
Próxima falsificação: separar as coordenadas apresentadas ao proponente das
coordenadas originais mantidas pelo host, sem alterar fonte/foco, semântica
esperada ou gabarito, em replay explicitamente diagnóstico. Nenhuma promoção,
produção, treino, persistência, runtime da Laylay, efeito externo ou commit.

29/09, papel contextual de foco host: diagnóstico offline **não promovido**.
Inventário distingue owners: aspas/ocorrência podem ser reutilizadas; o
guardião factual tipifica destaques da fala da assistente, não é extrator
genérico da entrada; modalidade continua dona da autorização. Não foi
encontrada API pública que autentique o papel semântico de cada foco original.
Catálogo antigo oferece só fonte inteira e aspas: operação externa compete
como trecho longo com nome curto. L05/cópia reconheceu a oração operacional,
mas ela não existia como candidato; não agrupar esse RED com erro semântico.

Nova tarefa reduzida marca um foco pelo host e remove competição/“menor”.
16 casos novos, revisão congelada antes da geração: Qwen real **16/16 saídas
válidas, 10/16 papéis alinhados**, apenas **2/6 pares contextuais completos**.
Nomes 3/6, operações mencionadas 5/6, expressões sem operação 2/2,
indeterminados 0/2. Nos seis pares, conteúdo focal idêntico muda de função
nominal para enunciado de operação; nomes não viram ordens por aparência.
P01A/P02A/P06A ainda leem nome como operação; P03B reduz enunciado negado a
expressão sem operação; P08A/P08B decidem fontes explicitamente ambíguas.
Erros persistem sem competição ou reescrita: esses fatores não são explicação
suficiente de todas as divergências. Dois pares completos também impedem
afirmar que o modelo nunca usa contexto. Não comparar 10/16 ao antigo 6/12:
tarefas diferentes e foco fornecido pelo host. Painel dirigido pelos REDs,
não holdout independente do pipeline. Artefato exclusivo:
`resultados_testes/sonda_papel_trecho_v1_primeira.jsonl`.

**43 testes novos; 638 regressivos relevantes verdes** (83 focados com
sobreposição). Auditoria retirou ambiguidade da fonte P01A antes de congelar;
nenhum ouro ajustado após gerar. Três REDs da própria aferição (duplicata,
ID desconhecido, cobertura faltante) corrigidos para recusar resumo parcial.
Próximo contrato a estudar: vínculo contextual com evidência literal, não
só enum de papel; a evidência também permanece proposta e nunca cria efeito,
autoridade ou vigência. Só depois comparar sua contribuição numa mesma tarefa
final. Fontes/contagens anteriores preservadas; sem produção, treino,
persistência, runtime da Laylay, liberação da rede ou commit.

29/09, contraste de seleção literal: candidato offline **não promovido**.
Reusa fonte/âncora e aspas canônicas para catalogar a fonte integral e todos
os conteúdos citados, inclusive nomes e citações aninhadas. O host materializa
IDs com offsets; não valida significado, autorização ou vigência. Dois REDs
de adulteração de tipo (`0.0`/`False` no lugar de offset inteiro) reproduzidos
e corrigidos na guarda do catálogo. **40 testes novos; 595 regressivos
relevantes verdes**, com sobreposição, sem validação do runtime da Laylay.

Qwen real em 12 fontes novas, tarefa/catálogo iguais entre cópia e ID:
saída literal válida **11/12 vs 12/12**, seleção alinhada à revisão local
**6/12 vs 6/12**. Há duas melhorias e duas regressões no ID; não sustenta
ganho semântico consistente. Ambos selecionam filename com aparência de
comando, expressão sem operação e escolha arbitrária em comparação sem foco.
ID também seleciona nome da tomada e se abstém de hipótese sem aspas.
A falha literal de cópia neste painel é subtrecho fora do catálogo, não
reescrita de aspas. Nas duas citações históricas, ambos acertam **2/2** na
tarefa menor; replay diagnóstico não prova correção da extração completa.
Controle histórico mantém `Usei` errado mesmo reparando só as aspas em memória:
cópia não é explicação exclusiva. Artefatos exclusivos
`sonda_selecao_literal_proposicao_v1_ab_primeira.jsonl` e
`sonda_selecao_literal_proposicao_v1_historico_diagnostico.jsonl`, em
resultados_testes. Ouro/contagens anteriores intactos. Próxima fronteira:
papel do trecho na oração — operação mencionada versus nome/metalinguagem —
antes de tipar objeto/polaridade. Sem produção, treino, integração, registro
de vigência, efeito externo ou commit.

29/09, representação de proposição/objeto/moldura: protótipo **inerte**, não
promovido. Reusa `FonteDidatica`, âncora literal e mapeador canônico de aspas;
conserva fonte integral, pares aninhados, polaridade proposta e múltiplas
proposições com seus próprios objetos. Parentais exigem mesma fonte,
contenção e ausência de ciclo. Listas vazias e molduras omitidas não provam
ausência de evento/discurso direto. Literalidade não autentica papel,
polaridade, enquadramento ou identidade; nenhum desses dados registra vigência.
Auditoria corrigiu um defeito do próprio protótipo: origem list/dict lançava
TypeError. Dois REDs reproduzidos na guarda de origem antes da correção de tipo.
**63 testes novos; 555 regressivos relevantes verdes** nesta seleção.

Piloto Qwen real de oito fontes novas, em arquivos/IoT, com gabarito local
congelado: estrutura ancorada 6/8, quantidade do piloto 5/8, predicado 5/8,
objeto completo 3/8, papel 5/8, polaridade 0/8, cadeia de molduras 4/8;
**0/8 completos alinhados à revisão local**. Não interpretar essas contagens
como verdade semântica: F01/F03 omitem só o artigo do objeto; moldura extra de
relato pode ser plausível nas falas de uso metalinguístico; I03 propõe também
o estado perguntado. O piloto exige uma operação principal, não cobertura de
todas as proposições. Nas duas citações, primeira fronteira RED é cópia de
aspas tipográficas como ASCII; no bruto escolhe `Usei`, não a operação interna.
Pedidos sem negação recebem polaridade `negativa`, hipóteses `indeterminada`:
há divergência de interpretação da dimensão, não prova de causa única.
Artefato exclusivo: `resultados_testes/sonda_proposicoes_mencionadas_v1_primeira.jsonl`.

Auditoria do experimento anterior também delimitou seu GREEN: mínimos de
O03/O05 permitem perder pergunta/citação externas, enquanto O04/O06 exigem
modalidade. Isso mede seleção local, não preservação uniforme da moldura.
Painéis/gabaritos e contagens históricos foram preservados, sem reclassificação
retroativa. Próxima fronteira de P01: selecionar a proposição literal sem
recopiar o envelope do host, antes de tipar seu objeto/moldura. Separar negação
gramatical de valor da ação e certeza de ocorrência em controle próprio;
não acrescentar outro gate de ausência ou ampliar o prompt por palavras-chave.
Sem produção, treino, integração, escrita de vigência ou runtime da Laylay.

29/09, presença/escopo antes do alvo: candidato **não promovido**. Em 16
falas novas congeladas, direto e estagiado acertam 11/16 alvos. Estagiado
alinha presença em 11/16 e todas as fronteiras em 10/16; corrige menções
irrelevantes, mas perde citação, hipótese e uma abstenção por alvo desconhecido.
Replay conhecido: 10/12 direto, 9/12 estagiado. B09 fica correto no candidato,
sem compensar regressões. Não declarar root corrigida por esse turno.
Contraste diagnóstico com mesmo prompt/schema e só a fonte na primeira
chamada: presença 11/16 contra 10/16 com cadastro nessa repetição. Erros em
citação/hipótese/objeto errado continuam em ambos; exposição de IDs não é
explicação suficiente. O01 variou com entrada preservada; não inferir ganho
reprodutível pela temperatura zero. **492 regressivos verdes**, 24 novos.
Produção/treino preservados, sem escrita de vigência. Três artefatos
`sonda_operacao_antes_alvo_v1_*` em resultados_testes. Próximo contrato:
separar proposição/evento mencionado, seu objeto e sua moldura discursiva;
não reduzir falta de adoção/identificação a ausência de operação.

29/09, vínculo nominal inventariado: nova sonda offline usa as guardas reais
de origem/escopo/TTL/cobertura do `InventarioContextual`, sem alterar seu
resolver conservador. Cadastro explícito do painel fornece nomes e IDs;
host ancora todas as ocorrências com offsets, inclusive negação/citação.
Não inventar antecedente a partir de um pedido nem extrair cadastro completo
do histórico. Ocorrência de nome registrado não certifica referente semântico.
Qwen real em 12 casos novos congelados: cadastro **10/12**, mesmo cadastro
com âncoras **11/12**. Apenas B08 muda para abstenção correta; B09 continua
confundindo menção sem operação com alvo de mudança, nos dois braços.
Não comparar esse número com os antigos: a tarefa/entrada são diferentes.
**468 regressivos relevantes verdes** nesta seleção (62 na seleção focada,
com sobreposição). Não substituem a seleção anterior de 520. Artefato:
`resultados_testes/sonda_alvo_inventariado_v1_ab_primeira.jsonl`.
Sem produção, treino, integração ou escrita de vigência. Ganho pontual, não
promoção. Próxima fronteira: provar presença e escopo da operação antes de
usar uma identidade mencionada, mantendo ato de fala separado da autorização.

Diagnóstico por campo, 29/09, base limpa `90a2fb8`: relação final não pode
ocultar erro de ato/alvo. No painel v2 conhecido (14 falas), conjunta:
ato 7/14, alvo 11/14, operação 8/14; todos os campos corretos em 3/12 casos,
apesar de 9/12 relações finais alinhadas. Separada: 7/14, 2/14, 9/14 e
1/12 completo, relação 4/12. Destacar a regra na entrada conservando prompt
e schema não alterou alvo: 2/14 nos dois formatos. Nenhum candidato promovido.
API pública canônica observada com padrões reais, sem callbacks de laylay.py:
não fornece identidade de regra comparável e usa modalidade ampla. Não
contar isso como validação da composição/runtime. 520 testes didáticos verdes.
Próximo contrato: menção → identidade ancorada da regra, com ato/operação
avaliados em suas fronteiras. Saídas completas preservadas nos dois JSONL
`sonda_relacoes_dimensoes_*_diagnostico` de resultados_testes.

Comparação posterior em 29/09: candidato offline separando ato/alvo/operação
**não promovido**. Em 12 casos novos congelados, relação final alinhada em
8/12 contra 6/12 do baseline isolado; no replay dos 12 históricos, 7/12 contra
9/12. Melhora em perguntas não compensou regressões em negação, conversa
irrelevante e ambiguidade. 510 testes didáticos verdes provam contratos,
não eliminam esses erros reais. Artefatos `sonda_relacoes_fontes_v2_ab_primeira`
e `sonda_relacoes_fontes_v2_v1_ab_diagnostico`, em resultados_testes, JSONL.
Não ajustar painel/gabarito aos erros. Nenhuma guarda ou runtime alterado.
Próxima fronteira: validar ato e alvo separadamente, incluindo serviços
canônicos existentes, antes de compor uma relação ou liberar vigência.

Experimento de relações em 29/09: a fonte alvo é fixa e cada fala posterior
recebe uma relação **proposta**, sem registro de vigência ou liberação.
Painel local de 12 casos congelado antes do Qwen: saída conjunta com citações
teve 5/12 casos completos alinhados (7/12 com ancoragem correta). Separando
cópia literal no host e uma relação por chamada, replay diagnóstico ficou
em 9/12 (12/12 ancorados). Restam pergunta interpretada como revogação,
revogação de outro alvo e citação confundida com manutenção. Não generalizar
9/12 para produção: não é novo holdout, nem revisão humana independente.
Resultados exclusivos em `resultados_testes/sonda_relacoes_fontes_v1_*.jsonl`.
486 testes didáticos verdes (27 novos); três erros reais do modelo preservados.
Nenhum veto foi relaxado; modelo não escreve no registro confiável.

Continuação em 29/09: corrigida a lacuna lexical já registrada abaixo,
`maior/menor ou igual a número`. O `ou` interno é parte de um comparador,
não uma junção de condições. O mesmo sinal literal serve ao segmentador
e à auditoria do grafo; comparação inclusiva conserva a igualdade no limite.
12 REDs reproduzidos antes do candidato; controles cobrem junção real,
negação, unidade, limiar, decimais negativos e contexto revogado. Replay
diagnóstico com Qwen real: `TANQUE_INCLUSIVO` agora alinhado até o grafo;
câmara preservada; duto revogado continua bloqueado (modelo ainda erra).
**459 testes didáticos aprovados**, compilação e diff-check limpos.
Não é treino nem novo holdout. Nenhum runtime alterado. Vigência semântica,
números por extenso e efeito `classificado como` continuam pendentes.

Correção posterior (28/09): o **RED histórico passou no caminho automático**
da sonda. `conferir_qualificacao_na_conversa` agora exige cobertura do contexto
posterior à regra antes de comparar. Texto do usuário não conferido produz
`contexto_criterio_pendente`, não revogação afirmada. Leitura numérica integral
representada pela premissa pode passar; ressalva adicional não. Revisor
explícito pode decidir sobre o snapshot completo, sem autoaprovação.
**431 testes aprovados** e repetição real com Qwen: duto revogado bloqueado,
câmara/limiar negativo e rotor/condição necessária preservados. Modelo ainda
erra seleção; não contar o veto como aprendizado. Sem execução da Laylay.
Cobertura é conservadora: conversa posterior não numérica, mesmo irrelevante,
exige revisão. Não há ainda interpretação geral de revogação/substituição.
Correção validada no escopo da sonda, raiz semântica mais ampla permanece
parcial. Os parágrafos seguintes preservam o histórico anterior ao patch.

Continuação: contrato explícito de vigência implementado **offline/opt-in**
em `scripts/analises/contrato_vigencia_criterios.py`. Registro pertence ao
revisor confiável e vincula decisão ao grafo, alvo, escopo e conteúdo integral
ordenado do contexto. Mudança exige nova revisão; conflito permanece pendente.
Pergunta/negação/outra regra não são classificadas por palavras-chave.
**417 aprovados e 1 RED original ainda aberto**: rota automática não dispõe
de revisor integrado e continua baseline. A rota opt-in bloqueia sem revisão,
inclusive no caso histórico, mas isto não comprova interpretação da revogação.
Sem chamada a modelo, treino, runtime ou encerramento da raiz. A API de escrita
do registro deve ficar exclusiva de um owner confiável; não é verificador
automático da decisão humana/modelada que alguém lhe entregar.

- Painel novo de 12 casos, congelado antes da medição real: seis positivos
  (inclusive construções fora da gramática) e seis negativos/sem vínculo
  comprovado. Qwen original **0/6** positivos completos; segmentado **3/6**.
  Seleção exata **5/12** e **zero abstenções corretas** nos dois braços.
- Limites distintos: `maior ou igual` é segmentado como disjunção; `vinte`
  não é normalizado a número; `classificado como` não entra na gramática.
  Não contar veto de frase válida como acerto, nem trocar o gabarito.
- **RED aberto prioritário:** regra revogada em outra fonte do mesmo contexto
  ainda chega à comparação no grafo. Modelo erra a seleção, normalizador
  recebe só a fonte escolhida e grafo confere observação, não vigência.
  Reproduzido sem modelo/gabarito, com controle idêntico sem revogação.
  Nenhuma autorização de fala/efeito: barreiras globais permanecem falsas.
- **399 testes aprovados e 1 RED preservado**, sem xfail. Teste:
  `scripts/tests/test_criterio_revogado_nao_fundamenta_qualificacao.py`.
  Artefato real: `resultados_testes/sonda_criterios_v6_ab_primeira.jsonl`.
  Próxima prioridade: contrato de validade/contexto da fonte antes de ampliar
  gramática ou treinar. Sem patch de runtime, treino ou liberação da rede.

### P01 — comparação real da normalização segmentada, 28/09/2026

- Opção offline separa condição/consequência/direção literais dos cinco slots
  propostos pelo Qwen. Reusa os segmentadores existentes; o caminho original
  continua padrão. Fonte/gabarito não são modificados pelo proponente.
- Painel v5 congelado antes das consultas: cinco positivos e quatro negativos,
  ordem das fontes e dos braços alternada. `qwen3:4b-instruct`, temperatura 0:
  **original 0/5 positivos completos; segmentada 5/5**. Seleção exata permanece
  5/9 em ambos: modelo errou os quatro negativos. Não contar veto como acerto
  do modelo. Guardas bloquearam todos os negativos; nenhuma autorização.
- **392 testes didáticos verdes**. Artefato bruto exclusivo:
  `resultados_testes/sonda_criterios_v5_ab_primeira.jsonl`. Sem treino/runtime.
  Pequeno painel de gramática estreita e revisão local, não prova de
  generalização. Próximo passo: ampliar construções/abstenções fora destes
  exemplos, mantendo esse resultado congelado e critérios independentes.

### P01 — consequência literal no avaliador offline, 28/09/2026

Continuação — sujeito da consequência: seis REDs demonstraram que a menção
na condição validava indevidamente outro sujeito (quatro domínios), pronome
sem vínculo ou descrição duplicada. O grafo agora exige descrição ancorada
completa e única compatível com o sujeito extraído; não usa ID, grandeza ou
substring como alias. **371 testes aprovados**, inclusive fluxo composto da
sonda com proponente controlado e guardas reais. Sem modelo/runtime/treino.
A fixture que confundia sensor e solo foi corrigida e ganhou teste negativo
histórico. Painéis v1/v2 preservados: dois casos de equivalência não demonstrada
agora ficam pendentes; v4 permanece intacto e mantém os cinco controles
positivos. Compatibilidade literal ainda não certifica identidade semântica.

- Reproduzida sem modelo/gabarito uma lacuna na avaliação: rótulo pedido
  preenchia o efeito do grafo, e menções na regra inteira permitiam avançar
  a comparação numérica em ação de alarme e consequência negada. Não houve
  aprovação de fala nem efeito externo; não confundir com falha de execução.
- Seis REDs e controles positivos sustentaram uma guarda compartilhada de
  consequência qualificativa na fonte integral. Trecho, offsets, predicado,
  sujeito literal, polaridade e prefixo de escopo ficam explícitos.
- 360 regressivos didáticos verdes; replay v4 bloqueia os dois negativos e
  preserva cinco positivos. Sem novo treino/chamada ao Qwen/runtime; hashes
  congelados preservados. Detalhes em `../PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md`.
- **Parcial, não encerrado:** gramática literal limitada; identidade do
  sujeito e escopo ainda não comprovados, e propostas do modelo seguem sem
  ganho novo medido. Pertence à investigação P01, não é outro ID por frase.

### Saída estruturada da CLI versus filtro global de logs — 29/09/2026

- Base `90a2fb8698541119f523c0a22fa4de0187cbaf92`, main. No passe ampliado
  de personalidade viva/P16, 8.273 testes passaram e quatro testes da sonda OpenRouter falharam
  por saída JSON vazia. Os 12 testes daquele módulo passaram isoladamente.
- São quatro sintomas da mesma fronteira: a composição instala um `print`
  global filtrado, e a CLI publicava seu resultado estruturado por esse canal
  de logs. Um RED com `criar_print_filtrado` real e captura de stdout reproduziu
  a perda do JSON sem chamar API externa. A primeira tentativa não alcançou
  a fronteira por faltar o lock da fixture; ela foi corrigida antes do RED
  causal, sem alteração de produção.
- Owner corrigido: `scripts/analises/sonda_openrouter_fronteira.py:main`
  escreve o resultado JSON diretamente em stdout. Logs podem ser filtrados;
  o resultado consumível da ferramenta mantém seu canal observável. O teste
  conserva a supressão de logs e verifica JSON válido sem publicação da chave.
- Os controles da CLI, DEV, latência com importação da composição e emoção
  passaram juntos (313 testes). Causa separada da prioridade emocional e dos
  julgamentos do modelo: nenhuma fonte, gabarito, confiança ou autorização
  da sonda foi alterada.
- A suíte completa final passou com 8.285 aprovados, 1 ignorado, 14 xfailed
  e 56 subtestes aprovados. Os quatro sintomas desapareceram pela correção
  no canal de resultado, mantendo as expectativas dos testes existentes.

### P16 — procedência do receipt na avaliação emocional — 29/09/2026

- Base `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`, worktree paralela
  preservada. Não é um ID por frase: a responsabilidade depende de evidência
  explícita, e a fala precisa consumir o receipt da mesma ocorrência.
- Primeira divergência de transporte: `marcar_resultado` publicava contexto e
  origem `executor`; `falar_por_status` reconstruía outro resultado sem esses
  campos, embora conservasse o ID. Normalização e troca de ID foram falsificadas.
  REDs em aplicativos e IoT usam registrador, avaliador, publicador e setter
  compartilhados reais. O snapshot por invocação agora transporta contexto e
  origem só após publicação, com concordância de marcador, IDs, intent, status,
  alvo e flags. Falha/republicação invalida o snapshot; mutação externa é isolada.
- Primeira divergência de confiança: ausência, zero e valor inválido viravam
  98%, e NaN virava 100%. Confiança de atribuição agora precisa ser explícita,
  finita em `[0,1]`; booleanos não são probabilidade. Repetição não promove
  atribuição explicitamente incerta. Resultado sem origem do executor permanece
  inferência sem expressão e não alimenta nem interrompe o histórico causal.
- O primeiro roteiro real, após a guarda e antes do transporte, confirmou a
  abertura e sete receipts redundantes, mas ficou em 4/13 por estado neutro:
  a reconstrução sem origem era a primeira fronteira RED. Com transporte, 12/13;
  o restante era `app_focado`, efeito real de foco, não redundância. A preparação
  final usa maximização observada antes desse trecho, mantendo expectativas
  emocionais e sem injetar estado. O roteiro de 14 turnos passou 14/14,
  zero alertas, p95 10,947 s, em
  `resultados_testes/roteiro_teste_personalidade_viva_p16-20260929-225617-497865`.
  Auditoria dos planos confirmou nove IDs distintos, sete redundâncias reais,
  continuidade da causa na conversa/desculpa e limpeza nos três encerramentos.
- GREEN focado: 299 testes de avaliação, adaptador, P15/P16 e identidade.
  Fonte real de responsabilidade própria ainda não existe: contexto sintético
  nos controles não prova esse produtor. Voz física ficou silenciosa; projeções
  de voz/avatar foram verificadas pela sonda de composição, não por reprodução.
  O placar do roteiro não certifica toda a fala: vazamento do feedback técnico
  de autoria pertence a F2, investigado separadamente.

Continuação no mesmo contrato de conquista: outro passe real, depois de F2,
teve 5/14 porque houve efeitos de foco durante a cadeia. O plano da conquista
estava correto, mas `provocacao_afetuosa` continuava expressável. A política
encerrava apenas `bronca_brincalhona`. Nove REDs e controles do arco forte,
mais avaliador/publicador/setter reais em apps e IoT, sustentaram incluir ambos
os arcos de repetição atribuída ao usuário. A prova curta no loop real passou
3/3, sem alertas, p95 9,608 s, em
`roteiro_conquista_inicial-20260929-231252-958844`: receipt redundante real,
`debochada` 1, conquista, `calma` 1 e episódio limpo. Humor de fundo preservado
nos controles. Passe focado final: 395 testes aprovados.

Regressão completa final: 8.385 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
aprovados em 181,47 s. O passe anterior teve uma falha de fixture de P18:
timeout apresentado como receipt observado sem declarar a origem do executor.
A inclusão dessa origem mantém as expectativas e as guardas de procedência;
P18 e o avaliador passaram juntos em 83 testes antes da repetição completa.
Os resultados não encerram as pendências de runtime ou de fonte própria.

Investigação da fonte própria, somente leitura: o preparador pode substituir
ou descartar comandos antes do filtro; o contrato preparado não conserva
proveniência da proposta principal. `filtrar_comandos_pelo_turno` também não
confere IDs/textos de turno/plano/retrato. Sonda com componentes reais rejeitou
DELETE_ITEM numa criação de playlist, mas aceitou ao trocar apenas o retrato
por outro turno de exclusão. É lacuna local demonstrada, não ocorrência de
execução indevida comprovada no runtime. Antes de produzir culpa, preservar
proveniência e congelar/revalidar o snapshot. Restrição legítima, retrato stale
ou proposta reparada não provam erro da Laylay. Nenhum patch nessa fonte.

### Continuação da fonte própria — coerência e emissão preservada — 30/09/2026

- Mesma base `90a2fb8`, `main`, alterações paralelas preservadas. A primeira
  fronteira de autoridade aceitava retrato de outra ocorrência. Três REDs no
  callback instalado em `laylay.py` atingiram playlist, IoT e aplicativos;
  controles corretos passaram antes da troca. O filtro compartilhado agora
  exige seis IDs e textos coerentes no caminho moderno, incluindo referências
  e decisão. Revisões usam a visão operacional efetiva; legado sem identidade
  de retrato mantém compatibilidade. Vinte e três REDs menores precederam a
  produção. GREEN: 149 testes e 22 subtestes. Limite textual: 500 caracteres.
- Primeira perda de procedência: o preparador pode substituir a emissão
  original antes do filtro. O runtime captura `ContratoPropostaPrincipal`
  antes dessa etapa, com ID real do turno e origem fixa. Mappings, contingência,
  vazio, retorno não textual ou vínculo desconhecido não viram prova suficiente.
  O objeto interno conserva a string, sem referência aninhada, parser, nova
  chamada, publicação emocional ou autoridade. O callback segue com dois
  argumentos. Guardar emissão não comprova erro próprio nem efeito.
- Vinte e seis REDs da preservação e dois de retorno inválido do preparador
  foram reproduzidos. A guarda `Mapping` conserva diagnóstico de falha antes
  do dispatcher, enquanto o normalizador standalone continua compatível com
  `None`. GREEN: 48 testes de contratos e registro de conversa.
- O primeiro passe amplo teve 8.451 aprovados e duas falhas por bootstrap do
  teste novo no processo de pytest: ambiente e `print` globais da composição
  atingiam configuração e terminal. Controle separado 2/2, reprodução conjunta
  com dois REDs e 13/13 após isolamento do bootstrap num subprocesso. As oito
  verificações reais foram mantidas, sem alterar configuração/terminal.
  Regressão completa: **8.453 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
  aprovados em 198,46 s**.
- Fonte capturada ainda não é correlacionada ao frame atual para atribuição
  emocional. Leitura reparada publicada como principal e cópias rasas legadas
  continuam fora do candidato. Não encerrar P16 pelo GREEN intermediário.
- Pendência de correlação receipt/fala, separada da guarda de autorização:
  localmente, plano estrangeiro com comando confirmado sustenta “Apaguei”.
  O atualizador mantém comandos anteriores quando recebe lista vazia; sem
  comandos, o verificador real declara não execução/não confirmação. Ainda
  falta reprodução da composição completa do caso estrangeiro. Preservar
  receipts por omissão no mesmo plano é legítimo; não remover a regra global.
  Nenhum patch no writer ou na fala nesta rodada; nenhum commit criado.

### Correlação de evidência operacional antes da fala — 30/09/2026

- Continuação da pendência acima, mesma base `90a2fb8`, sem ID por frase. A
  reprodução passou pelo filtro, atualizador, dispatcher vazio e finalizador
  instalados na composição real. Arquivos, IoT e playlists: filtro recusou a
  proposta, atualizador publicou receipt estrangeiro em `resposta_planejada`,
  finalizador entregou alegação de sucesso. Seis REDs, três em cada fronteira.
- Controle com mesmos receipts e IDs coerentes preservou a evidência e a fala.
  Falha geral do verificador e necessidade de limpar receipts por omissão foram
  falsificadas. Recibos são estímulos sintéticos, não provas de executores
  externos; as portas de voz/persistência foram isoladas. Nenhum executor foi
  chamado. A composição não foi montada manualmente.
- Contrato público `motivo_incoerencia_contratos_turno` reutilizado pelo filtro,
  atualizador e reader. IDs bool/fração/coleções e textos modernos não string
  são recusados. Writer valida/mescla/publica plano+trilha na transação existente;
  incoerência aborta, conservando estado. Reader captura snapshot, recusa antes
  de consumir evidência e entrega conclusão segura observável. Um RED de troca
  durante o verificador demonstrou overwrite do turno novo; CAS do frame lido
  agora protege todas as publicações derivadas. Pesquisa/verificação fora do
  lock. A mescla por intent e o vínculo da fonte capturada ficam fora do patch.
  A API do writer ainda não recebe ocorrência esperada: callback tardio que
  encontre outro frame coerente continua limite. Adaptadores legados sem
  transação não ganham garantia de atomicidade. Validado somente no escopo
  de frame incoerente/trocado durante leitura; P16 permanece parcial.
- Produção: `decisao_turno.py` e `orquestrador_turno_runtime.py`. Cinquenta REDs
  locais antes das guardas, com cinco controles iniciais; resultado final:
  59 canônicos, 288 com vizinhos e 20 da composição isolada aprovados. A seleção
  manual que importou a composição antiga antes de configuração/terminal
  repetiu a interferência já diagnosticada; nenhum patch nesses módulos.
  Regressão completa: **8.521 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
  aprovados em 200,79 s**. `git diff --check` limpo; nenhum commit ou push.
- Fonte própria ainda separada: três sondas somente leitura mostraram aceitação
  ao trocar todo o frame coerentemente, falso RED de alias sem adaptação e
  extração de `open_app` de explicação solta. O owner da próxima fronteira é a
  decodificação canônica em `higiene_resposta_ia.py`, que ainda não publica o
  método de extração. Preservar API legada e distinguir campo operacional,
  recuperação e fala; não criar outro parser nem chamar o modelo novamente.
  Snapshot recebido, correlação, extração explícita, adaptação e violação
  comprovada são requisitos cumulativos antes de qualquer autoria emocional.

### Fonte própria — caminho de extração preservado antes do reparo — 30/09/2026

- Continuação da perda de procedência, mesma base `90a2fb8`, sem outro ID por
  frase. O decoder entregava candidatos explícitos e recuperados sem registrar
  qual caminho os produziu; o reparo anterior à leitura podia ocultar o caminho
  original. Menção somente na fala e recuperação textual falsificam a hipótese
  de que qualquer comando extraído prove uma proposta operacional explícita.
- Owner único: o algoritmo de `higiene_resposta_ia.py` passa a devolver resultado
  tipado; sua fachada legada continua retornando fala/lista. Extração imutável
  registra método, campo, contagem efetiva e string original; origem fixa,
  autoridade falsa. `NONE`, JSON reparado textualmente, tuplas e falhas não
  ganham o marcador explícito. Não atesta correção ou efeito de um candidato.
- `processamento_resposta_ia.py` lê antes do reparo e reutiliza essa decodificação
  sem substituição. `contratos_turno.py` transporta somente objeto tipado e,
  havendo principal, exige fonte conhecida e string exata igual. JSON da IA
  não define essa procedência. Não houve nova chamada ou parser privado.
- 27 REDs iniciais; dois REDs de coleção usada como método e controle `None`;
  30 novos GREEN. Seleção: **573 aprovados em 9,15 s**, incluindo 24 controles
  da composição. Quatro usam o preparador instalado, higiene e normalizador
  reais com serviço de modelo isolado pelo registro canônico. Trava real com
  identidade da sonda evita disputar a Laylay aberta; não inicia `main`.
  Comparação com o decoder do HEAD: 79 entradas, nenhuma divergência legada.
  Regressão ampla: **8.555 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
  aprovados em 203,93 s**, com identidade de mutex própria no pytest para
  importar a composição sem disputar a sessão aberta. Não valida seu loop.
  `git diff --check` limpo; HEAD preservado.
- Limites: string vinculada não é frame vigente; quantidade não é snapshot dos
  parâmetros; candidato explícito não é violação nem culpa. Atribuição emocional,
  adaptação original, leitura principal substituída, callback tardio e receipts
  de solicitações diferentes continuam pendentes. P16 permanece parcial.
  Produção desta continuação limitada aos três owners acima; nenhum commit.

### Fonte própria — vínculo da emissão antes da publicação — 30/09/2026

- Continuação da mesma raiz, base `90a2fb8`, `main`, sem outro ID por frase.
  Frame coerente trocado por inteiro aceitava a emissão anterior, inclusive
  repetindo a frase; troca de operação a rotulava incompatível com a intenção
  nova. Mesma fonte/frame passou: coerência interna não identifica ocorrência
  e não houve falha geral do filtro. Autoridade e procedência são separadas.
- Owner `decisao_turno.py` correlaciona principal tipada por ID e projeção da
  fala original contra o frame canônico; revisão legítima preservada. A projeção
  de 500 caracteres normaliza espaços finais igualmente, sem validar sufixos
  ou parâmetros. Validador captura um snapshot do estado real e reutiliza o
  filtro. `laylay.py` só instala esse objeto no callback existente.
- `resposta_ia_runtime.py` confere ocorrência mesmo com lista vazia, antes de
  leitura semântica/publicação/dispatcher/finalização. Troca aborta o registro
  antigo; falha técnica no mesmo frame conserva contingência sem comandos.
  Retorno moderno malformado/contraditório aborta sem repetir legado. Declaração
  positiva não promove fonte capturada insuficiente; ausência declarada de
  procedência/autorização não sustenta comandos. Veto da autoridade capturada
  permanece. Callback legado mantém um argumento e não certifica procedência.
- 23 REDs iniciais e 16 adicionais precederam os candidatos/refinamentos.
  Expectativas de ordem do receipt e ocorrência com ID reutilizado foram erros
  de teste identificados separadamente. GREEN: **72 focados**, incluindo 30 da
  composição instalada, e **722 ampliados em 11,73 s** antes dos últimos
  controles. Runtime de resposta, estado/validador reais, falha no mesmo turno
  e função legada também passaram com portas externas isoladas; uma chamada
  principal nos controles. Trava real com identidade da sonda, sem `main`.
- Regressão completa: **8.603 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
  aprovados em 195,97 s**. Mutex real com identidade própria do pytest preservou
  a sessão aberta. `git diff --check` limpo; HEAD preservado.
- Produção desta continuação: `decisao_turno.py`, `resposta_ia_runtime.py` e
  wiring de `laylay.py`. Sem parser, modelo extra, evento emocional ou patch no
  writer. Snapshot não fecha a corrida após retornar nem valida efeito externo;
  ocorrência esperada no writer e mescla de receipts continuam pendentes.
  Próxima fronteira da fonte: congelar/adaptar candidatos originais e provar
  violação antes da culpa. P16 parcial; nenhum commit ou push.

### Fonte própria — snapshot dos candidatos e visão isolada — 30/09/2026

- Mesma raiz/base `90a2fb8`, `main`, trabalho paralelo preservado. Contagem e
  string não conservavam a árvore disponível depois de mutação/reparo. Retorno
  legado compartilhava parâmetros aninhados. Sondas falsificaram normalizador
  universal flat e autoria pelo alias cru: comandos canônicos perdiam params
  ou não eram reconhecidos; playlist/IoT legítimos passaram após adaptação.
  Recuperação textual continuou não explícita após converter o nome.
- `SnapshotComandoIA` no contrato guarda JSON interno imutável, projeta cópias
  e oculta payload no repr. Tipos/ciclos/chaves não JSON e não finitos recusam
  evidência. Extração exige tupla tipada/contagem alinhada; preserva originais
  e posições de visões `None`, com gates separados de preservação/normalização.
  Vazio não vira normalização operacional; marcador explícito não substitui
  esses gates, inclusive com JSON textual contendo `NaN`.
- Decoder captura no `concluir` antes da limpeza da fala. Normalizador puro
  reconhece `intent`+`params` pelo catálogo vivo e preserva a árvore; flat reusa
  adaptador canônico sobre cópia. Campos concorrentes/desconhecidos não ganham
  visão. Lista executável e algoritmo de extração permanecem compatíveis.
  Transporte já existente retém objeto original após reparo e exige bruto exato
  da principal. Não houve parser/tabela privada/modelo extra/autoridade nova.
- 28 REDs antes do candidato, 30 controles anteriores verdes; **149 focados**
  finais: 65 procedência, 41 composição, 43 vínculo/runtime. Onze controles
  novos do preparador instalado nos três domínios, inclusive reparo/recuperação;
  outro usa runtime/preparador/estado/validador/normalizador reais e confirma
  snapshots após reparo, lista vazia e uma chamada principal. Portas externas
  isoladas; trava real com identidade da sonda, sem iniciar `main`.
- Regressão completa: **8.650 aprovados, 1 ignorado, 14 xfailed e 56 subtestes
  aprovados em 201,44 s**, com mutex real sob identidade do pytest para preservar
  a sessão aberta. `git diff --check` limpo; HEAD mantido.
- Produção: `contratos_turno.py`, `higiene_resposta_ia.py` e normalizador puro
  junto ao adaptador em `dispatcher_comandos_json.py`. Executor, writer, filtro
  e evento emocional fora do patch. Visão não comprova parâmetros/alvo efetivo
  (dispatcher ainda prepara alvo/pc_b), disponibilidade, efeito ou culpa.
  Retrato local de app sem intents delimitadas não demonstra incompatibilidade;
  cobertura do árbitro é outra fronteira, sem patch ou encerramento global.
  Próximo: violação demonstrada antes de erro próprio. P16 parcial, restantes
  do checkpoint preservados; nenhum commit ou push.

### Fonte própria — violação original demonstrada — 30/09/2026

- Mesma raiz/base `90a2fb8`, `main`, sem commit. Primeira perda restante:
  validador só recebia lista reparada, mesmo com emissão/extração preservadas.
  Oito REDs prévios provaram perda em playlist, IoT, veto e transporte.
  Alias cru e frame estrangeiro falsificaram culpa por simples rejeição;
  original correta/reparo indevido e inverso separam as duas autorias.
- `validar_proposta_original` recebe extração tipada usando o mesmo snapshot
  do filtro, mantendo fachadas legadas. Prova cumulativa: fonte/bruto/ocorrência,
  proposta explícita, originais e normalização completos, flags reais, owner
  conhecido e restrição canônica. `ViolacaoPropostaPrincipal` imutável guarda
  ID/índice/intent/motivo, sem payload, alvo inventado, receipt ou autoridade.
  Filtro canônico continua dono da decisão; lista final não é substituída.
- Veto inequívoco pode demonstrar violação de autorização; incompatibilidade
  exige operação/intents delimitadas no catálogo vivo. `MOVE_ITEM` permanece
  no retrato compatível de arquivos, ausente do catálogo; veto independe dessa
  cobertura. Arbitragem posterior com outra origem suspende prova nesta versão.
  Parâmetros/alvo, app sem cobertura, aliases, recuperações, falha técnica e
  fonte/frame insuficientes não viram erro próprio.
- Runtime publica apenas diagnóstico local sanitizado, com vínculo positivo,
  sem evento emocional/falha operacional. Metadados de culpa/prova da IA não
  materializam o objeto; construtor recusa tipos/motivos não canônicos.
  Refinamentos: dois REDs de owner/catálogo malformados e um de observabilidade
  precederam suas guardas. GREEN final: **199 focados**, incluindo posição e
  metadados (87 vínculo/runtime, 65 procedência, 47 composição);
  composição instalada/início/decoder/preparador/validador reais em três
  domínios, modelo/portas externos isolados. Uma principal no teste do runtime.
- Produção: contrato, decisão compartilhada e transporte da resposta. Nenhum
  executor, writer, estado emocional ou parser novo. Pure evaluator suspende
  restrição não coletável; filtro legado ainda lança erro em coleção numérica
  de intents (achado separado, sem prova/efeito). Próximo: produtor tipado de
  erro próprio com publicação na ocorrência vigente, sem falsificar receipt.
  P16 parcial. Candidato paralelo de writer/semântica vinculados apareceu na
  worktree durante a execução; preservado, com 47 testes próprios verdes na
  repetição focada. Não consolidar essas raízes nem encerrar por esse controle.
  Publicação emocional ainda deve conferir a restrição vigente, além do ID;
  assinatura decisória ou revalidação canônica evitará prova invalidada na
  mesma ocorrência. Demais pendências mantidas, sem commit ou push.
- Regressão final: **8.975 aprovados, 1 ignorado, 56 subtestes aprovados em
  201,73 s**, zero falhas/xfails. Hashes dos 65 Python modificados/novos iguais
  antes/depois, mutex real com identidade do pytest, HEAD mantido e diff limpo.
  Duas execuções anteriores ocorreram durante mudanças paralelas do writer:
  três falhas de controle, depois uma de conclusão técnica; passaram após
  atualizar/repetir o candidato paralelo. Não atribuir à prova original nem
  enfraquecer expectativas. O verde estável não certifica o loop/efeito físico.

### Continuação da fonte própria — evento e consumo da fala — 30/09/2026

- Mesma raiz/base `90a2fb8`, `main`, worktree preservada. Fonte original já
  produz prova; a fronteira seguinte separava quadro e episódio sem verificar
  ocorrência/restrição. Não atribuir essa perda ao executor ou ao reparo JSON.
  Produtor próprio projeta fato local tipado, sem fabricar `ResultadoAcao`.
- `EstadoContextoRuntime.publicar_erro_proposta` reexecuta a avaliação canônica
  dentro de `atualizar_dominios`: quadro, plano e conversa são preparados antes
  de qualquer atribuição. Rollback/recusa preservam ambos. Atomicidade pelo
  lock comum; leitores legados diretos continuam fora dessa garantia.
  Referência estável e consumo no plano impedem renovar TTL após replay.
- Origem reservada `contrato_proposta_principal`, `envergonhada 1/autorreparo`,
  45 s, sem payload/autoridade/receipt/memória pessoal. Aplicador exige prova
  e emissão integrais; permite interromper bronca sem mudar humor de fundo.
  Publicador genérico recusa essa origem. Estado, diagnóstico e catálogo
  reutilizam owners compartilhados, sem modelo ou parser emocional separado.
- Fala planejada conserva apenas a base. Finalizador compõe admissão limitada
  depois do guardião, revalidando tempo e fonte consumida no frame atual.
  REDs de expiração/troca motivaram esse refinamento; uma contingência de outro
  frame não recebe a admissão antiga. A fala não confirma efeito ou reparo.
  Perguntas naturais recuperam os limites pelo catálogo existente.
- RED prévio: 13 ponte, 17 transação, três origem/aplicação, um callback real,
  um finalizador e dois trocas no guardião. Casos e provas pertencem à mesma
  raiz; não são novos IDs por frase/domínio. Controles de original correta,
  aliases, fonte insuficiente, outra ocorrência e alteração da restrição
  preservados. Nenhum commit/push. P16 parcial; leitura original/reparada,
  correlação de receipts e loop/áudio físico continuam sujeitos a evidência
  própria, preservando alterações paralelas e seus checkpoints.
- GREEN: **616 focados/vizinhos + 16 na composição instalada**, com início,
  preparador, validador, publisher, writer, guardião, finalizador e orquestrador
  de fala reais. Playlist/IoT usam uma principal, filtro remove original
  incompatível, texto/voz/projeção visual concordam; confirmação falsa sem
  receipt vira contingência. Portas físicas/persistência isoladas.
- Ampla: **9.084 aprovados, 16 falhas, um ignorado e 56 subtestes em 199,05 s**;
  76 Python com hashes iguais antes/depois, HEAD mantido e diff limpo. Os 16
  pertencem ao arquivo paralelo `test_mescla_receipts_solicitacao.py`, presente
  no início. Isolado repete 16 RED/3 GREEN: 12 mescla por intent, um identidade
  host e três sondas bloqueadas na chave de porta incorreta (sem `_`). A última
  família não alcança publicação e exige corrigir a representação do contrato
  no teste antes de declarar RED de transporte. Preservados como próxima
  investigação de correlação; não são 16 roots nem regressão ampla GREEN.

### Sonda separada: desculpa seguida de comando — 27/09/2026

- Durante a validação da P16, `classificar_modalidade_turno` leu
  “Desculpa, repeti o pedido, mas agora abra o Opera.” como `conversa`.
  `planejar_turno` recebeu `pedido_desculpas` como função comunicativa e
  devolveu `requer_execucao=False`. A sondagem não passou pelo executor.
- Isto é uma suspeita de raiz na segmentação/autoridade do turno misto, não
  consequência demonstrada do decaimento emocional nem prova de que um comando
  real foi perdido. Não houve patch nessa fronteira. Próximo diagnóstico:
  comparar o classificador e o interpretador principal com comandos mistos
  equivalentes sem desculpa, em mais de um domínio, e localizar o primeiro RED.

### Complemento da observabilidade da entrada — prompts vazios, 23/09

- Evidência do Pedro às 10:30:40 confirma que o texto recebido agora aparece;
  a correção anterior estava incompleta porque `💬 Você:` e `>` vazios ainda
  eram publicados como eventos SYSTEM. Não é perda da fala nem falha da ponte.
- Base `bd94bc3e`, main, worktree compartilhada preservada (124 entradas no
  status). Arquivos de DEV/terminal envolvidos estavam sem diff antes deste patch.
- Primeira fronteira RED: captura de stdout promovia controles de apresentação
  do leitor de stdin a eventos. Leitor real + espelho real reproduzem dois
  eventos após Enter vazio e zero mensagens processadas. Cinco REDs antes
  do candidato, 19 controles verdes.
- Produção alterada somente em `dev_console_runtime.py`: marcadores completos
  sem conteúdo são ignorados na admissão de stdout (inclusive captura oculta).
  Console original, mensagens preenchidas, linhas diagnósticas e stderr
  preservados. Não há filtro por palavra solta nem alteração de entrada/execução.
- GREEN: 68 testes em DEV, canais, terminal e ponte. Transporte autenticado
  por socket real confirma snapshot/live sem prompts vazios, preservando
  `💬 Você: 'pode ligar a luz' | origem=desktop`.
- Novos registros exigem reinício para carregar o patch; sessão real do Pedro
  não reiniciada e histórico antigo não apagado. Nenhum commit criado.

### Recibo ilegível não autoriza confirmação — 23/09

- Continuação da fronteira operacional/RED 5 descrita abaixo, não nova raiz
  independente por habilidade. Base `bd94bc3e`, main; worktree paralela preservada.
- Primeira fronteira RED: falha de `como_dict()` virava `{}` e o bloco
  `if dados_resultado` pulava a validação mantendo o texto otimista. Não era
  invenção do TTS: o texto já chegava errado à publicação visual e à fila.
  Os controles de sucesso confirmado e de confirmação desconhecida passaram.
- Antes do candidato: 15 REDs e 14 controles verdes. Além do caso histórico,
  cobertos retorno vazio/tipo inválido, acesso ao serializador com exceção,
  falas de aplicativo/arquivo/IoT e reserva indevida da deduplicação por
  atributos de um objeto cujo recibo não podia ser lido.
- Produção alterada somente em `falar_resultado_operacional`, no orquestrador
  de fala: ler uma única representação antes de validar/deduplicar; se ilegível,
  informar que o resultado não pôde ser validado, sem afirmar sucesso ou falha
  do efeito externo. Recibo posterior válido continua elegível à confirmação.
  Sem alteração em executores, autorização, LLM ou correção anterior do briefing.
- GREEN: **173 testes em oito módulos**, incluindo direção e fila de voz reais
  sem reprodução física, publicação visual, memória, receipts, guardião e
  briefing. `git diff --check` sem erros. Nenhum commit criado.
- Sessão real pendente: Laylay aberta (PIDs 26928/9880), não interrompida.
  Não foi injetada corrupção na sessão do usuário; resultado integrado não
  é uma validação de áudio físico nem encerramento de toda factualidade.

### Retomada proativa e observabilidade da entrada — 23/09

- Base: `bd94bc3e3a29c49906dc603f9ca1540310ca3274`, main, worktree
  compartilhada suja preservada. Não houve commit nem reinício da sessão.
- Raiz reproduzida: canal de chat aberto era tratado como ocupação permanente,
  tanto no Porteiro quanto no callback legado composto em `laylay.py`.
  O timer retomava normalmente, mas a mesma condição impedia a liberação.
  Quatro REDs: briefing/e-mails/rotina após silêncio e callback real extraído
  da composição. Corrigido para considerar owner, turno e atividade recente;
  reunião, foco, jogo e usuário falando continuam protegidos.
- Raiz separada: timeout da espera síncrona do briefing declarava pendente=False
  sem cancelar a fila. O recibo posterior não salvava o estado diário. RED
  reproduzido; agora a pendência continua acompanhada e sucesso tardio chama
  a persistência uma vez, somente após recibo positivo.
- Raiz separada de diagnóstico: `💬 Você:` era um prompt, não registro de fala.
  Desktop/voz não produzem eco de stdin. Cinco REDs mostram texto chegando ao
  processamento sem aparecer no DEV. O coordenador registra a entrada uma vez
  no worker comum, com origem e sanitização, sem alterar o texto processado.
- Validação: 97 testes passaram em dez módulos de porteiro, fila, briefing,
  entrada, DEV, presença e prioridade. Integração com Porteiro e Voz reais usa
  relógio/timer e saída física controlados; não equivale a áudio em produção.
  A Laylay estava aberta (PIDs 29700/4716); validação ao vivo pendente.
- Achado separado a investigar: a execução de oito módulos teve 79 PASS e
  um FAIL em `test_fronteira_operacional_falha_fechada_se_resultado_nao_serializa`:
  receipt corrompido terminou em “Pronto, abri o Chrome”. O método operacional
  não foi alterado neste patch; a worktree já contém mudanças paralelas nele.
  Não atribuir automaticamente ao patch atual nem declarar regressão ampla verde.
- Fora do patch: sincronizações repetidas da lista de conversas, indisponibilidade
  HTTP do LRCLIB, momentos sensíveis persistentes e outras possíveis causas de
  silêncio. O log HTTP isolado não identifica status ou causa do provedor.

### P01 — Continuação incerta: investigação da recusa, 23/09

- Base mantida em `bd94bc3e`, branch main e worktree compartilhada preservada.
  `quero im` chega intacto ao HTTP junto da pergunta anterior. A recusa já vem
  do Qwen, antes do verificador. Isso falsifica perda literal da entrada,
  ausência da última pergunta no payload e criação da recusa pelo guardião,
  mas ainda não identifica qual instrução/comportamento da geração a causa.
- Controle local do owner de modalidade: `quero im` é conversa, sem autorização
  e sem comandos; não é classificado como comando inválido. `quero sim` é
  confirmação contextual, também sem autorização independente. Preservar
  essa distinção; não normalizar erro de digitação para autorização presumida.
- Preparada sonda `scripts/analises/diagnosticar_continuacao_incerta.py`:
  reutiliza exatamente um payload da captura, varia fala atual e retira
  separadamente contrato efêmero e instruções gerais. Mantém histórico,
  modelo, temperatura, orçamento e schema; registra seed/entrada/saída local.
  Não importa runtime, não executa propostas nem alimenta aprendizado. As
  variantes reduzidas são ablações, **não candidatos promovidos a produção**.
- Seis testes da sonda passaram: preservação das variáveis de controle,
  imutabilidade do payload original, aborto para captura ambígua/schema
  inesperado. Não são seis respostas corretas da Laylay ou prova do modelo.
- Comparação executada depois do encerramento da sessão, sem abrir a Laylay:
  `resultados_testes/continuacao_incerta-20260923-103913-389155/comparacao.jsonl`.
  Foram oito chamadas locais (`quero im`/`quero sim`, quatro variantes).
  Algumas variantes entregaram o exemplo após `quero sim`, mas as interpretações
  de `quero im` divergiram entre si. É indício de sensibilidade ao contrato,
  não prova de uma instrução causal única. Nenhuma variante foi promovida a
  produção; preservar autorização literal sem adivinhar `im = sim`.

### P01 — Ensino aberto: referência certa, conteúdo ainda não fundamentado — 23/09

- Base `main`/`bd94bc3e`, worktree paralela preservada. A sonda com geração
  real do Qwen3:4b-instruct e 21 entradas em sete assuntos está em
  `resultados_testes/roteiro_ensino_multidominio-20260923-104318-248836/`.
  Todos os turnos responderam sem comandos, mas a métrica `19/21` mede a
  rubrica operacional/latência; `fala_coerente=nao_avaliado`. O texto final
  errou tradução de idade em inglês, conceitos de força/energia, representação
  de corte arquitetônico e exemplos de plantas anuais/perenes. Os erros já
  estavam na geração HTTP. Transporte, executor e verificador não são a
  primeira fronteira desses erros de conteúdo.
- Causa de continuidade demonstrada: `esclarecimento_literal` ancorava o
  pedido `não entendi` na fala anterior da assistente, que pode estar errada,
  sem recuperar o pedido de ensino do usuário. RED em três domínios mais
  controle de expiração. O contrato agora usa a estratégia
  `reensino_didatico`, com o pedido recente como tema e a resposta anterior
  como tentativa a revisar, não como fonte ou autorização. Produção alterada
  somente em `cognicao/contrato_fala.py`, `cognicao/geracao_concreta.py`;
  a classificação de pedidos explícitos em `personalidade/proporcao_resposta.py`
  e o roteiro genérico já estavam no candidato desta investigação.
  145 testes focados passaram; sem commit.
- Validação real posterior, sem replay:
  `resultados_testes/roteiro_ensino_multidominio-20260923-123010-079343/`.
  Os sete pedidos de reexplicação chegaram com `reensino_didatico` e sem
  execução, 21/21 responderam. O placar `18/21` volta a medir operação e
  latência, **não qualidade didática**. Persistiram erros factuais nos temas
  acima. Logo o reparo do referente é GREEN no runtime; **P01/geração factual
  permanece RED**.
- Ablação `scripts/analises/comparar_contrato_ensino.py` em quatro assuntos:
  trocar a regra de evidência/definição no prompt mudou algumas respostas,
  mas não eliminou imprecisões. Uma revisão isolada pelo mesmo Qwen aprovou
  sete reexplicações como `ERRO OBJETIVO: Nenhum`, inclusive erros verificáveis
  de tradução, física e botânica. **Autoavaliação sem evidência externa não é
  guardião factual**. Não promovê-la a produção por parecer convincente.
- A pesquisa contextual atual não é ainda uma base para cinco sites de ensino:
  `pesquisa_contextual.py` tentou Wikipédia PT/EN e recebeu HTTP 403 neste
  ambiente; a busca HTML reutilizada encontrou quatro hits sobre força/energia,
  dos quais dois abriram no teste. Disponibilidade e relevância são limites
  distintos. O desenho adaptativo e critérios de ativação estão em
  `melhorias e planos/PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md`. Não ativar busca
  compulsória nem converter snippet em confirmação factual.
- Achados separados: ao ler `planta`, uma tarefa IoT tentou pesquisar RGB
  repetidas vezes sem comando; uma reescrita de realidade introduziu `nn`
  visível na fala de inglês. Investigar por suas primeiras fronteiras, sem
  atribuir esses sintomas à raiz factual ou encobri-los com o placar 21/21.
- **23/09, candidata multifonte não promovida:** foi criada recuperação de
  até cinco páginas realmente lidas, domínios independentes, URLs e trechos,
  com guarda contra URL privada/redirecionamento e sem autoridade de ação.
  Dois ensaios de 21 turnos com influência ativada ficaram em 6/21 e 7/21
  sem alertas operacionais (p95 perto de 20 s), piores que a referência 18/21.
  A inspeção das falas encontrou definição correta na fonte, mas inversão
  produzida pelo Qwen (planta baixa vista de baixo), tradução “eu sou 25”,
  código de exemplo com repetição incorreta e exemplos botânicos inventados.
  Logo a camada de leitura é GREEN local, mas **P01/geração + verificação de
  alegações continua RED no runtime**. `LAYLAY_PESQUISA_MULTIFONTE_MODO`
  fica `desativado` por padrão; `ativo` serve somente para experimento.
  `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md` registra portões restantes. Não
  somar o sintoma IoT `planta` como nova raiz factual.
- **24/09, mesma raiz P01, candidata de prompt ainda insuficiente:** no
  cenário hipotético com leitura de 15% e limiar de 20%, o Qwen recebeu os
  dados, mas sua resposta bruta omitia a comparação ou acrescentava causas
  não demonstradas; o verificador as preservou. O roteiro compacto recebeu
  o contrato premissas → relação → conclusão (RED em três assuntos).
  Depois, dois REDs mostraram que falas antigas da assistente voltavam ao
  ensino pelo histórico e por `Evite repetir`; ambas as rotas foram retiradas
  só do prompt didático, sem alterar memória nem autorização. No runtime,
  a comparação `15 < 20` melhorou, mas ainda surgiram promessas de umidade
  e explicações botânicas não ancoradas. **P01 continua RED; inventário de
  cenário segue em sombra.** 236 testes relevantes verdes; os 4/4 do roteiro
  mediam transporte/não execução, não verdade. Evidência e próxima fronteira
  de alegações atômicas em `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md`.
- **27/09, subdiagnóstico P01 ainda em sombra:** a seleção direta de
  segmentação pelo Qwen mostrou viés de ordem e saídas estruturais instáveis.
  Uma sonda POS portuguesa independente alinhou 9/13 regras planas de um
  painel inédito à revisão local, mas errou uma oração relativa e um verbo
  rotulado como adjetivo; absteve-se numa elipse e recusou uma regra plana
  cuja mistura `e/ou` era só superficial. Esses REDs pertencem às fronteiras
  de escopo sintático, POS e cobertura lexical descritas no plano de ensino;
  não são quatro novas raízes nem prova de qualidade didática no runtime.
  Nenhuma promoção para fala, treino ou execução.
- **27/09, mesma raiz P01, oração relativa:** RED focado mostrou que um
  predicado `acl:relcl` não pode fechar sozinho uma premissa
  independente. Candidato apenas na sonda POS offline: 55 testes focados
  verdes; v8 passou de 9/13 para 10/13 regras planas alinhadas à revisão
  local. Painel novo v9 congelado antes da execução: 8/8 alinhamentos de
  superfície, porém um deles usou âncora sintática errada (`escreve` em vez
  de `confirmar`), logo não é 8/8 de análise correta nem razão para promoção.
  Excluir toda a subárvore relativa foi falsificado: só 5/8 no v9; o
  candidato ficou restrito ao verbo relativo e a auxiliares diretamente
  ligados a ele.
  Parser ambíguo, POS `cessar`, elipse e mistura superficial seguem abertos;
  nenhum código de produção, fala ou executor alterado nesta etapa.
- **27/09, continuação da mesma raiz P01:** a âncora `escreve` foi aceita
  acidentalmente no v9 onde a condição principal depende de `confirmar`.
  RED focado antes do ajuste; a sonda offline agora se abstém quando uma
  relativa ainda aberta é seguida imediatamente por verbo após o conectivo.
  v9: 7 alinhamentos locais/1 abstenção. Painel v10 novo, congelado antes da
  primeira execução: 4 alinhamentos/2 abstenções; controles independentes
  preservados. 68 testes da área verdes. Nenhuma promoção ao runtime nem
  encerramento de P01; demais fronteiras continuam separadas.
- **27/09, auditoria de âncora da mesma raiz P01:** `ROOT` do parser foi
  falsificado como regra geral para o verbo principal. O confronto offline
  separa âncora, trecho e abstenção sem usar a revisão na proposta. Painel
  v11 congelado antes do parser: 6/8 casos com âncoras alinhadas à revisão
  local e 2/8 abstenções; `vapor` etiquetado `VERB` revelou outra falha POS
  sem gerar sucesso falso. 71 testes focados verdes. Não houve alteração de
  produção nem validação da fala no runtime; P01 permanece aberto.
- **27/09, mesma raiz P01, confiabilidade POS/fronteira:** `cessar` foi
  `ADJ/advcl`; variantes com `soprar` e `soar` variaram entre `ADJ/acl`,
  `ADJ/ROOT`, `ADJ/amod` e `PROPN/ROOT`. Veto por etiqueta foi falsificado
  em dois painéis novos. O contrato offline compartilhado agora se abstém
  quando há fragmento sem âncora entre fragmentos ancorados, sem inventar
  verbo. No v14, 2 fusões falsas passaram a abstenções; no v15 congelado,
  4/7 alinharam e 3/7 se abstiveram, incluindo duas frases válidas cuja
  cobertura foi perdida conscientemente. 79 testes focados verdes. Nenhuma
  promoção para produção/runtime; P01 continua aberto.
- **27/09, mesma raiz P01, continuidade nominal:** a sonda POS passou a
  registrar candidato de objeto coordenado ligado ao verbo anterior sem
  desfazer `fronteira_interna_sem_predicado_ambigua`. Painel v16 congelado:
  2/3 objetos compostos forneceram essa evidência, 0/2 controles
  problemáticos; o terceiro objeto revelou `câmera` classificada como
  `VERB` e âncora inicial errada. São 1 alinhamento e 5 abstenções no
  painel, não 5 erros equivalentes nem liberação de cobertura. 81 testes
  focados verdes. Sem produção, runtime real ou treino alterados; P01 aberto.
- **27/09, mesma raiz P01, POS verbal contraditório:** no caso `a câmera
  registrar foto e vídeo`, `câmera` foi `VERB/nsubj` com filho `a/DET/det`.
  RED focado comprovou que sua seleção como âncora ocultava a continuação
  nominal; a guarda diagnóstica a exclui e se abstém, sem aprovar a regra.
  Painel v17 congelado: evidência nominal nos 3/3 objetos compostos, nenhum
  dos dois controles problemáticos; 1 alinhamento independente, 5 abstenções.
  O controle `o vento soprar` voltou a perder o verbo no POS, logo a
  cobertura segue limitada. 82 testes focados verdes; v8–v15 sem mudança
  nas contagens. Hashes e limites no plano de ensino. Nada promovido a
  produção, fala, autorização, treino ou runtime real; P01 aberto.
- **27/09, mesma raiz P01, vínculo literal auditável:** REDs exigiram offsets
  do arco `conj` → `obj` → âncora e uma prévia separada da decisão canônica.
  A sonda registra conflito POS sem perder o arco; `VERB` com papel de
  coordenado de objeto leva à abstenção. Painel v18 congelado antes do modelo:
  prévia em 3/3 objetos compostos, 0/4 controles, mas os três continuam em
  `fronteira_interna_sem_predicado_ambigua` no reconstrutor. Dois controles
  alinharam; os demais se abstiveram. Um arco incompleto passou a ser
  descartado sem exceção após RED focado. 86 testes focados verdes; v8–v17
  conservaram as contagens de estados. Hashes, limites e próxima fronteira
  no plano de ensino. Nenhuma alteração de produção, fala, treino, autorização
  ou runtime real; P01 aberto.
- **27/09, mesma raiz P01, parser atravessa a fronteira oracional:** v19
  congelado revelou 2/3 controles de sujeito composto com **prévia falsa**:
  `conj → obj` ligou o sujeito da condição seguinte ao objeto anterior.
  Offset e POS estavam coerentes, portanto não bastavam. REDs levaram a
  abstenção conservadora quando nominal determinado precede predicado plural
  e quando `VERB` tem determinante. Repetição v19: 0/5 controles com prévia,
  1/2 objetos cobertos. V20 congelado depois do primeiro candidato: primeira
  execução 2/3 objetos e 0/3 controles. Um falso veto adicional foi revelado
  por verbo com sujeito próprio, corrigido após RED; repetição v20 3/3 e
  0/3, **não** holdout independente para o último ajuste. 90 testes focados
  verdes. A decisão canônica segue em abstenção; P01 não encerrada, sem
  mudança de produção ou runtime. Detalhes e hashes no plano de ensino.
- **27/09, mesma raiz P01, checagem sem parser:** piloto local de Qwen em
  três contrastes falhou como segundo voto (`indeterminado/anterior/anterior`
  contra `anterior/seguinte/anterior`; com partições completas, três
  `indeterminado`). Não foi integrado. RED com morfologia do parser ausente
  motivou veto textual unilateral por artigo e possíveis flexões plurais,
  validando offsets sem POS/dependência. A ausência de veto não aprova
  agrupamento e pode haver perda de cobertura em objeto legítimo seguido de
  condição plural. Painéis v15–v20 sem mudança de estados ou prévias;
  97 testes focados verdes. P01 permanece aberta, sem produção/runtime.
- **28/09, mesma raiz P01, POS e medição da prévia:** v21 foi congelado antes
  da primeira execução (hashes e casos no plano de ensino). O parser real
  marcou `falham` como `ADJ/conj` com sujeito próprio e como `PROPN/flat:name`
  em contextos distintos. RED focado tornou o primeiro caso uma abstenção
  POS explícita; o segundo permanece em `sem_predicado_suficiente`, sem
  inferir verbo a partir da palavra. Auditoria tipada da prévia distingue
  vínculo ausente, conflito POS e vetos; aferição retrospectiva separada
  compara apenas trechos ao gabarito manual local. Em v15–v21, 14/44 casos
  tiveram prévia, as 14 coincidiram com a revisão local; não é prova
  semântica independente. Um objeto legítimo do v21 perdeu cobertura pelo
  veto conservador. 106 testes focados e 230 testes das sondas de ensino
  verdes nesta etapa; P01 aberta,
  sem alteração de produção, fala, treino, autorização ou executor.
  Controle pareado com mesma topologia de arco/POS em leituras distintas
  sustenta a abstenção; `--resumo` torna a contagem local reproduzível,
  sem converter acordo com gabarito em prova semântica.
- **28/09, P01, segundo avaliador ainda não apto:** sonda independente sem
  POS/dependências/gabarito no input e painel v22 congelado (10 casos: 4
  sujeito, 4 objeto, 2 ambíguos). Primeira chamada: 3/10 citações aceitas,
  todas de sujeito. Repetição diagnóstica após expor a resposta bruta,
  sem mudar o prompt: 5/10 rótulos brutos alinhados (4/4 sujeitos, 0/4
  objetos, 1/2 ambíguos). O primeiro RED inclui classificação do objeto,
  não apenas formato da citação. Sem promoção; hashes e limites no plano
  de ensino. Não atribuir placar bruto ao primeiro uso cego.
- **28/09, P01, segunda formulação apenas diagnóstica no v22 já visto:**
  partições literais completas com ordem invertida deram 20/20 respostas
  `objeto_anterior`, mas só 4/10 rótulos alinhados à revisão (0/4 sujeitos,
  4/4 objetos, 0/2 ambíguos). Concordância à ordem do mesmo modelo não é
  voto independente; o prompt mudou o viés, não resolveu a fronteira.
  Próxima investigação: fonte de evidência diferente. P01 permanece sombra.
- **28/09, P01, tentativa de segundo modelo inconclusiva:**
  `gemma4:26b` estava instalado, mas a primeira consulta do contrato de
  citação excedeu 90 segundos (`ReadTimeout`). O restante foi interrompido
  e o modelo descarregado. Nenhum rótulo foi observado; não entra no placar
  semântico nem justifica promoção. Os 244 testes locais das sondas passaram;
  ainda falta evidência independente operacionalmente viável e runtime real.
- **28/09, P01, transporte OpenRouter comprovado em um caso:**
  sonda offline reutiliza a credencial DPAPI da Laylay sem terminal ou
  exposição da chave. `google/gemini-3.1-flash-lite` retornou um julgamento
  ancorado no primeiro caso sintético v22; recibo da API registrou custo de
  US$ 0,0001245. Isto não é placar semântico nem holdout. Nenhuma integração
  de produção foi ativada; próximo passo continua sendo painel novo cego.
- **28/09, P01, revisão local inválida em v22/v23:**
  a primeira medição externa do v23 acertou os oito casos definidos com
  citação válida, mas a revisão dos quatro "ambíguos" não era gramatical:
  último sujeito singular com verbo plural na leitura de objeto. Os dois
  "ambíguos" do v22 tinham a mesma falha. Nenhum desses seis itens conta
  como prova de calibração de incerteza. V23 foi preservado imutável;
  v24 registra explicitamente as duas leituras plausíveis antes da chamada.
  P01 continua em sombra, sem remendo para o modelo.
- **28/09, P01, abstenção ausente em ambiguidade plausível:**
  v24 registrou duas partições literais plausíveis em seis casos; Gemini
  escolheu sempre objeto e GPT-4o mini alternou quatro sujeitos/dois objetos,
  mas nenhum retornou `indeterminado`. Citação literal não prova que o lado
  oposto seja inviável. Hipótese de contrato: a instrução original não define
  quando abster. Variante explícita e v25 novo foram congelados antes da
  primeira consulta, sem mudar o gabarito anterior ou liberar P01.
- **28/09, P01, troca de viés no prompt explícito:**
  v25 novo (3 sujeito, 3 objeto, 3 ambíguo) com Gemini: 3/3 sujeitos
  ancorados, 3/3 ambíguos abstidos, mas 3/3 objetos definidos também
  abstidos. A nova instrução não é solução geral; primeira fronteira RED
  agora é verificar a viabilidade de ambas as partições, não escolher um
  rótulo pela preferência do prompt. Nenhuma alteração de produção.
- **28/09, P01, viabilidade precisa de contexto e validação tipada:**
  sonda offline avalia as duas partições separadamente, sem gabarito ou
  alternativa na mesma chamada. RED local impediu agregação de pareceres
  não validados. V25 de desenvolvimento mostrou erro de concordância
  alegado quando se removia o `Se` da frase; a reconstrução contextualizada
  corrigiu esse transporte, e somente parênteses externos adicionados pela
  própria sonda podem ser removidos da citação. V26 novo foi congelado para
  aferição; nenhuma decisão ou executor da Laylay foi modificado.
- **28/09, P01, primeira medição v26 e variação dos pareceres:**
  GPT-4o mini alinhou 6/9 casos à revisão local (2/3 sujeito, 1/3 objeto,
  3/3 ambíguo), em 18 chamadas. Os três desalinhamentos vieram da
  viabilidade atribuída às partições, antes da agregação. Repetições
  diagnósticas mudaram dois pareceres, sem alterar o placar. Mesmo com
  temperatura zero e semente 42, um caso repetido variou; o provedor não
  foi fixado, logo a causa dessa variação não está demonstrada. Citação
  literal não verifica gramática. Sonda e 275 testes locais verdes; P01
  segue offline/sombra, sem treino ou integração operacional.
- **28/09, P01, variação não depende só de roteamento:**
  observabilidade offline revelou chamadas Azure/OpenAI no mesmo caso, mas
  `provider.only=openai` com fallback desligado não estabilizou o parecer.
  Em cinco repetições diagnósticas fixadas, a leitura de sujeito oscilou
  entre viável (2) e inviável (3). Em três repetições, SHA-256 do pedido,
  provedor OpenAI, fingerprint e término `stop` foram idênticos. Diferença
  no corpo, troca de provedor e truncamento aparente foram falsificados
  como explicações suficientes; mecanismo interno ainda desconhecido.
  Parecer isolado não comprova concordância; próxima fronteira é um
  verificador independente de escopo explícito. Sem promoção ou produção.
- **28/09, P01, motivo gramatical alegado sem contraprova:**
  RED offline reproduziu exclusão falsa da leitura `sujeito_seguinte` por
  `inviavel/concordancia` embora a condição trouxesse sujeito composto
  curto e marcador verbal plural explícito. Contrato unilateral no módulo
  superficial existente marca apenas esse conflito; o agregador se abstém,
  sem converter o sinal em viabilidade comprovada. Controles de verbo
  singular, casos fora de escopo, motivo semântico e domínios distintos
  passaram; 290 testes de sonda relacionados verdes. Nenhuma mudança de
  produção, treino, promoção, fala ou executor. Verificação morfossintática
  abrangente e runtime permanecem abertos.
- **28/09, P01, verificação morfológica de escopo curto:**
  o sinal anterior por sufixo não reconhecia `forem` e aceitaria a forma
  inventada `trubarem`. Fonte externa PortiLexicon-UD congelada por commit
  e SHA gerou índice local de 368 KB (licença preservada); código da sonda
  valida o hash e compara pessoa/número em estruturas curtas. Parecer do
  modelo `inviavel/concordancia` agora requer divergência numérica
  corroborada; convergência, falta de forma/recurso ou estrutura fora do
  alcance levam à abstenção. Painel novo congelado antes da medição:
  21/21 alinhados à revisão **manual local** (8/8/5), sem alegar qualidade
  semântica ou generalização. SpaCy médio não substitui o índice nem a
  revisão da estrutura. P01 segue offline/sombra; nenhum treino ou produção.

### P01 — Perfil explicativo perdido na escolha do prompt — 23/09

- Base `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`. Conferidos HEAD,
  branch e worktree; trabalho paralelo neural/operacional preservado.
  Sem novo ID por frase: esta é uma causa demonstrada de instrução inadequada
  dentro de P01, não a explicação de todas as recusas/erros do modelo.
- Captura anterior `transporte_evidencia-20260922-173130-396574`: pedido
  `quero passo a passo usando metodos praticos` chegou com o tema da divisão
  no histórico, mas prompt rápido mandava uma ou duas frases, contrato três,
  e retrato expressivo permitia oito. O modelo só prometeu explicar, usando
  58 tokens e `finish_reason=stop`: **não foi corte por esgotar tokens**.
  Falsificadas perda do tema no transporte e mutilação desse rascunho pelo
  verificador. A hipótese de que a compressão explica toda a má geração não
  foi demonstrada e não deve ser usada para fechar P01.
- Primeira divergência: `classificar_proporcao` já dizia `explicativa`, mas
  `usar_modo_rapido_conversa` verificava só fórmulas/reexplicação e tamanho.
  Logo um pedido curto de desenvolvimento recebia rota/prompt de fala breve;
  o contrato efêmero também ignorava o perfil ao escolher o limite inicial.
- Contrato reutilizável: **necessidade da resposta governa a compactação, não
  tamanho da entrada**. Rota e contrato reutilizam a classificação existente
  em `proporcao_resposta`. Perfis explicativo/matemático não entram no rápido;
  contrato herda seu espaço, preservando teto atual de oito e as restrições
  específicas posteriores. Saudação segue rápida; autoridade e receipts não
  mudam. Não foram acrescentados gatilhos privados, modelo ou fallback.
- RED: **6 falhas causais / 82 controles verdes**, com pedido histórico,
  divisão, fotossíntese, detalhes e comparação de conceitos. Candidato de
  produção somente em `autonomia/fluxos_conversa.py` e
  `cognicao/contrato_fala.py`. Em fluxos, alterações anteriores de P03 foram
  preservadas. Testes em `test_latencia_resposta.py` e
  `test_contrato_semantico_fala.py`, incluindo o callback realmente injetado
  em `_resposta_ia_runtime` pelo `laylay.py`. Sem treino, promoção ou commit.
- Regressão final selecionada: **643 aprovados / 13 xfailed preexistentes**
  em 22 módulos, 7,12 s, incluindo os contratos de P10. `git diff --check`
  sem erro de whitespace; aviso CRLF no relato do usuário não foi corrigido
  por estar fora do escopo. Não foi executada a suíte global.
- Geração real, **sem replay**, duas sessões Qwen3:4b-instruct:
  `roteiro_ensino_divisao-20260923-100339-722094` e
  `roteiro_ensino_divisao-20260923-100458-680059`. Transporte respectivamente
  em `transporte_evidencia-20260923-100338-508086` e
  `transporte_evidencia-20260923-100457-371895`, todos em `resultados_testes/`.
  O turno 2 recebeu prompt completo, contrato de sete frases e 512 tokens
  disponíveis. Produziu e entregou três passos na primeira sessão e cinco na
  segunda. Primeira resposta consumiu 173 tokens e terminou por `stop`.
  Melhora observada, não taxa de acerto estimada nem ablação estatística.
- Ambas encerraram com código zero; nenhuma sessão do Pedro foi encerrada
  pelo agente. A tentativa anterior 10:02:48 foi bloqueada corretamente por
  instância ativa; sondas só continuaram após Pedro encerrar. Voz/UI/mic off,
  Gmail inativo, IoT simulado; observadores e memória normal ativos. Áudio
  físico não testado. Placar 4/4 mede não execução, não aprovação do ensino.
- **Ainda aberto:** em ambas, turno 3 confundiu contrário/inverso; turno 4
  interpretou `quero im` como pedido impossível/sem comprovação. Os erros já
  vieram no HTTP, com a pergunta anterior no histórico. A maior disponibilidade
  de tokens não resolve isso. Próxima investigação: contexto/instrução e
  tratamento de continuação incerta na geração, com contrastes, sem ensinar
  `im = sim` como regra autorizante. JSON literal fora do envelope e perguntas
  excessivas também ocorreram; entrega recuperou o texto, não certificou
  conformidade estrutural. Achado de resumo `principal_duplicada` reapareceu,
  segue separado e sem prova de contaminação persistida.

### P10 — Aspas indeterminadas não são evidência de obra — 22/09, continuação

- Base mantida: `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`,
  worktree suja/compartilhada preservada. Primeira fronteira: ramo residual de
  `_destaques_com_papel` atribuía `obra_candidata` a tudo que não reconhecia.
  O verificador rejeitava e o orquestrador pesquisava `desfaz`/`o contrário`.
  Capturas anteriores e RED sem modelo/provedor falsificam truncamento na
  geração e falha de pesquisa como causas desse corte específico.
- Contrato: título precisa de indício relacional (tipo, seleção, nomeação,
  enumeração tipificada ou resposta nominal ao tipo solicitado). Sem indício,
  papel `indeterminado`, não obra e não enunciado isento. Datas, medidas,
  categorias e estados continuam passando por suas verificações; contexto
  não vira fonte nem autorização. A leitura do texto completo sobrevive à
  divisão em frases. Pesquisa e validação recebem o mesmo contexto do usuário.
- RED inicial: **15 falhas / 24 verdes**, sendo **11 falhas comportamentais**
  e quatro da nova assinatura contextual ainda inexistente (estas quatro não
  contam como prova causal). O teste com `x` ficava verde pela limitação antiga
  de duas letras no scanner, não pelo papel correto; trocado por `delta`.
- Dois controles antigos de obras revelaram lacunas na primeira versão do
  candidato; mantidos e atendidos. Um controle diferente atribuía um título
  de filme a `Noite Inventada` num exemplo ambíguo de abrir aplicativo.
  Expectativa corrigida por não haver indício de obra; nova prova conserva
  a rejeição de data dentro desse trecho, sem mascará-lo como enunciado.
- Produção desta rodada: `cognicao/fundamentacao_factual.py` e passagem do
  `texto_usuario` em `cognicao/orquestrador_turno_runtime.py`. Testes ampliados
  nos arquivos de explicação didática e citações existentes. Sem mudança em
  pesos, autorização, executores, personalidade ou `laylay.py`; nenhum commit.
- Provas: **430 aprovados / 13 xfailed preexistentes**, seleção de 16 módulos,
  incluindo import da composição real, segurança e recomendação. Não é suíte
  global. Uma tentativa paralela à sonda deu três falhas de import pelo lock
  de instância única (427 verdes); repetida após saída da sonda, sem alterar
  a proteção, resultou nos 430 verdes acima.
- Runtime: `resultados_testes/roteiro_ensino_divisao-20260922-173131-509832/`;
  HTTP em `transporte_evidencia-20260922-173130-396574/`. Somente turno 3 usa
  replay explícito da captura `transporte_evidencia-20260922-171829-788015`;
  demais turnos têm geração nova. As explicações entre aspas chegaram inteiras
  sem busca de obra. O guardião de perguntas marcou `perguntas_em_excesso` e
  ajustou pontuação na saída do terminal, não removeu as cláusulas citadas.
  Sessão terminou com código zero, sem processo Laylay restante. Voz/UI/mic
  desligados, IoT simulado, Gmail inativo; observadores e persistência normais
  ativos. Placar 4/4 só certifica ausência de comandos, não qualidade didática.
- **Limites e próxima raiz:** não é classificador semântico universal nem
  verificador matemático. Mantida a distinção incorreta contrário/inverso do
  rascunho para provar preservação, não sua verdade. Nesta geração nova, turno
  2 prometeu passos sem entregá-los; turno 4 recusou `quero im` como comando
  inválido. Ambos já constam do texto bruto: **P01/geração**, próximo alvo,
  não novos remendos no extrator. Resumo com `principal_duplicada` reapareceu;
  permanece achado separado, sem prova do conteúdo persistido.

### P10 / P01 — Ensino perde passos no verificador; geração tem falhas próprias — 22/09

- Base `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`; worktree paralela
  preservada. Relato de 21/09, 10:37:02–10:37:05: o rascunho contém a divisão
  por agrupamento e seus passos; o extrator interpreta a pergunta citada
  `6 cabe quantas vezes em 18?` e o nome do método como obras. Pesquisa sem
  evidência → rejeição das frases → só enunciado e resultado chegam ao usuário.
- Falsificações: não era necessário aumentar o limite de tokens para salvar
  esses passos, pois já estavam na geração; o corte se reproduz sem modelo e
  sem provedor de pesquisa. O problema não é exclusivamente matemática: o mesmo
  classificador de papéis trata perguntas instrutivas e referências conceituais.
  A resposta a `quero im` no log histórico já era inadequada antes do guardião,
  portanto não se atribuiu toda a qualidade do ensino ao mesmo defeito.
- Contrato P10 ampliado no owner existente `fundamentacao_factual.py`:
  pergunta proposta ao interlocutor e retomada explícita do que ele quis dizer
  são enunciados; nome tipificado como método/conceito/termo é referência
  conceitual, não obra. Referência conceitual não mascara datas/medidas nem
  certifica a existência, correção ou propriedades do conceito. Citações não
  viram utterances autorizantes; obras vizinhas continuam exigindo evidência.
- RED inicial: **7 falhas / 6 controles verdes**. Primeira sonda revelou outra
  ocorrência da mesma fronteira: a geração pedia esclarecimento citando
  `quero im`, mas o verificador substituía por falta de fonte factual.
  Reproduzidos mais **3 REDs / 14 verdes** antes de incluir essa retomada.
- Produção alterada nesta rodada: somente `cognicao/fundamentacao_factual.py`.
  Novo `scripts/tests/test_explicacao_didatica_preservada.py`; roteiro
  `scripts/roteiros/roteiro_ensino_divisao.py`, aceito na sonda existente de
  transporte. Nenhum patch de pesos, executor, personalidade ou orçamento.
  Pesquisa em cinco camadas continua fora do escopo.
- Provas finais: **19 testes próprios**, incluindo o verificador ligado pelo
  `laylay.py`, com pesquisa proibida para a aula histórica; seleção ampliada
  **212 aprovados / 13 xfailed preexistentes**. Sem alteração dos xfails.
- Duas sessões completas com geração local nova, microfone/voz/UI desativados,
  Gmail inativo, IoT simulado e observadores/persistência normais ativos:
  `roteiro_ensino_divisao-20260922-171645-086047` e
  `roteiro_ensino_divisao-20260922-171831-067132`, em `resultados_testes/`.
  Capturas HTTP/preparação: `transporte_evidencia-20260922-171643-712042` e
  `transporte_evidencia-20260922-171829-788015`. Ambas preservaram integralmente
  o passo a passo gerado no turno 2, sem pesquisar sua pergunta como obra.
  Primeira tentativa 17:16:31 abortou antes dos turnos por expressão não literal
  nas expectativas do roteiro; corrigida somente a fixture para o loader.
- **Ainda RED, mesma P10:** aspas de ênfase/predicado (`a divisão 'desfaz' a
  multiplicação`, `'o contrário'`) e outras molduras (`a divisão pergunta:`)
  seguem caindo na classificação residual de obra. Não basta ir adicionando
  frases: a próxima investigação deve separar papel desconhecido de evidência
  positiva de obra, preservando os controles de títulos e fatos externos.
- **Ainda aberto, P01/geração:** as duas sondas geraram distinção confusa entre
  contrário/inverso. No último turno da segunda sessão o modelo voltou a negar
  capacidades externas, sem relação com a aula; o texto ruim já estava no HTTP.
  O esclarecimento citado pós-correção está validado localmente, mas essa última
  geração não o produziu: não alegar correção integral de `quero im` no runtime.
- A primeira sonda marcou 2 aprovações/1 falha/1 alerta; a segunda marcou 4/4,
  apesar desses defeitos visíveis. Expectativas verificam ausência de comandos,
  não qualidade didática. **4/4 não é aprovação do ensino.**
- Achado separado durante a segunda sonda: tentativa de resumo das últimas
  cinco interações recebeu `principal_duplicada` e em seguida houve log de
  memória salva. Isso não prova o conteúdo persistido; auditar o consumidor de
  sentinelas antes de atribuir contaminação a essa origem. Não corrigido aqui.
- Estado: melhoria de P10 comprovada nos passos históricos e em geração real;
  P10/P01 permanecem abertos nos limites acima. Nenhum commit criado.

### P04 — Contador observava a porta legada, não o ADD executado — 22/09

- Base `main`, HEAD `bd94bc3e3a29c49906dc603f9ca1540310ca3274`;
  alterações paralelas preservadas. Reproduzido novamente o histórico:
  a faixa correta está no arquivo, mas `add_final=0` (um RED / um controle).
- Cadeia demonstrada por código e observação: feedback chama
  `RegistroOperacoesMusicais.adicionar_faixa_resultado` →
  `OperacoesMusicaisRuntime.adicionar_faixa_resultado` →
  `PlaylistRuntime.add_and_verify_result`. O contador do teste envolvia apenas
  `add_and_verify`, o wrapper bool legado, que essa cadeia não chama.
- Duas observações independentes, uma em cada porta, confirmaram **zero chamadas
  legadas e uma detalhada**, com uma faixa persistida. A comparação com o
  contador antigo produziu outro RED, antes da correção do teste. No controle
  de CREATE falho, ambas as portas tiveram zero chamadas e nenhum alvo salvo.
  Falsificadas ausência de ADD e falha de persistência como causas de P04.
- Correção exclusivamente no harness histórico
  `scripts/tests/test_red151_runtime_canonico_c3.py`: contador envolve a porta
  detalhada, sem mudar o retorno nem a exigência de **exatamente uma** chamada.
  Removida instrumentação duplicada; bloqueio após CREATE falho segue exigindo
  zero ADD. Nenhum executor de produção foi alterado para satisfazer o teste.
- Outra lacuna de composição do mesmo harness: faltava o callback de publicação
  que `laylay.py` realmente fornece. Incluída captura de receipts e reforçadas
  as asserções de sucesso/falha, alvo musical e ordem `receipt → fala`. Não é
  prova do publicador real: essa fronteira é coberta separadamente por
  `test_root_publica_receipt_antes_da_fala_com_persistencia_real` (P03).
- Provas: **4/4** no composto e controle da medição; **24/24** incluindo P03,
  guardião e composição real importada; **352 aprovados** na seleção ampliada
  playlist/feedback/receipt/adaptador/cooperação. Escritas somente em diretórios
  temporários dos testes. Nenhuma playlist pessoal, rede ou sessão alterada.
- Estado: **P04 encerrado como defeito de instrumentação**, não como bug de
  salvamento corrigido em produção. Isso não encerra P03 no runtime completo,
  nem a qualidade geral da conversa. Próxima raiz prevista: ensino/conversa,
  separando o texto gerado da informação removida pelos verificadores.

### Verdade operacional da fala — receipt limita a certeza — 22/09

- Objetivo desta frente: impedir que personalidade, status otimista ou autoria
  da LLM aumentem a certeza acima do resultado realmente observado. Não houve
  redesenho do estilo da Laylay: repertório, emoção e personalidade foram
  preservados; a mudança atua somente na camada factual que antecede a fala.
- A arquitetura já possuía boas defesas: `planejar_resposta_acao()` separava
  sucesso/falha/incerteza, a autoria LLM recebia um contrato imutável e o
  guardião de alegações já sabia remover conclusão sem evidência. A
  investigação procurou os pontos onde essa verdade ainda podia ser
  reconstruída ou promovida antes de chegar a essas defesas.
- RED 1 — `AdaptadorResultadoOperacional.falar_por_status()`: um executor
  moderno podia publicar `confirmado=False` ou `confirmado=None` e, em
  seguida, a fala reconstruía `confirmado=True` apenas porque o status era
  otimista, como `app_aberto`. O adapter agora consome o tratamento moderno
  já publicado; inferência por status ficou restrita à compatibilidade legada.
  Resultado moderno explícito nunca perde seu `False/None` durante a fala.
- RED 2 — semântica da incerteza: `executou=None, confirmado=None` era
  verbalizado como “Enviei o comando...”, inventando até a tentativa.
  `executou=True, confirmado=None` continua podendo dizer que o comando foi
  enviado sem resultado confirmado; execução desconhecida agora diz somente
  que **não há confirmação de que a ação chegou a ser executada**.
- RED 3 — não execução por política: `nao_executado_por_politica` era
  classificado como falha e podia virar “não consegui/tentei”. O planejador
  ganhou a classe `nao_executado`: a fala-base declara “não executei”, sem
  inventar tentativa ou incapacidade. Essa classe permanece calma e não passa
  pelo estilizador de sucesso.
- RED 4 — tri-state perdido na normalização:
  `normalizar_resultado_acao()` tratava campo ausente e
  `"confirmado": None` como a mesma coisa, podendo promover `None` explícito
  a `True` por causa do status. Agora **campo ausente** mantém a inferência
  legada; **campo presente com None** preserva a incerteza moderna.
- RED 5 — última fronteira antes do TTS:
  `OrquestradorFalaRuntime.falar_resultado_operacional()` deduplicava a fala,
  mas confiava integralmente no texto recebido. Ele agora aplica o guardião
  existente usando somente o receipt atual antes de chamar a voz. Uma fala
  “Pronto, abri o Chrome” permanece idêntica quando o receipt confirma; com
  `confirmado=None` é corrigida para envio sem confirmação; com não execução
  confirmada, a alegação de sucesso é removida. O gate é exclusivo da fala
  operacional e não altera conversa/personagem.
- Auditoria de bypasses diretos: sucessos diretos encontrados em organização de
  janelas, volume/autonomia e leituras de agenda/navegador já estavam atrás de
  confirmação/releitura local. Não foram migrados desnecessariamente.
- Scanner estrutural encontrou somente dois executores não musicais capazes de
  publicar status listado como confirmado sem `confirmado=` explícito:
  `site_aberto` remoto no PC B e `remetente_silenciado` no Gmail.
  Ambos foram fechados e o scanner terminou em **0 ocorrências**.
- PC B: enviar `open_url` prova despacho, não que a aba apareceu. O resultado
  passou de `site_aberto` para `abertura_solicitada`,
  `executou=True, confirmado=None`; a fala informa que a abertura foi pedida
  e ainda não confirmada.
- Gmail: o executor descartava o bool real de
  `_gmail_silenciar_remetente()`, engolia exceção e sempre dizia sucesso.
  Agora só publica `remetente_silenciado` com retorno `True`;
  `False`/exceção viram `falha_execucao` e alvo ausente vira
  `alvo_ausente`, todos com execução/confirmação explícitas.
- Provas focadas da fronteira de fala: **161/161 aprovados**. REDs adicionais
  de adapter, tri-state, semântica de incerteza, política e último gate do TTS
  também ficaram verdes. Scanner final:
  `CONFIRMED_STATUS_WITHOUT_EXPLICIT_RECEIPT=0` fora da frente musical.
- Regressão global controlada final:
  **6.692 passed, 1 skipped, 13 deselected, 14 xfailed, 56 subtests passed**,
  zero falhas. Os mesmos oito testes de root bloqueados pela instância real
  passaram **8/8** com bypass de mutex exclusivamente no processo de pytest.
- Validação mecânica: `py_compile=0`, `git diff --check=0`. Neural continua
  em `shadow`; hashes do modelo ativo e v27 permaneceram
  `07C539...9E62` e `CAAA93...E0CF`. A frente
  `executor_musical/executor_playlists/controle_midia/playlist_runtime`
  permaneceu fora do diff desta investigação.
- Regra arquitetural consolidada: **a personalidade decide como dizer; o
  receipt decide o que ela pode afirmar. A fala nunca aumenta a certeza.**

### P03 — Publicação do resultado antes da conclusão — 22/09

- Base preservada: `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`,
  worktree suja. Nesta retomada o adaptador, o planejador e os testes da frente
  paralela já continham mudanças posteriores: os dois REDs citados em P18/P19
  passaram sem novo patch nosso nesses arquivos. A normalização preserva
  `confirmado=None` explícito; os testes agora publicam tratamento depois da
  construção do adaptador, conforme o ciclo de vida da invocação.
- P03 continuava RED: `create → add → ultima → fala → receipt`. O callback
  oficial existe tanto no teste quanto no getter real em `laylay.py`;
  `FeedbackPendenteRuntime` já o repassa. Ausência de injeção é falsificada.
  CREATE/ADD retornam sucesso e o mesmo guardião aceita a fala quando recebe
  antes o receipt: não é necessário relaxar o guardião nem corrigir o storage.
- Primeira divergência: `fluxos_conversa.handle_feedback_pendente` emitia a
  conclusão antes do bloco de publicação. Contrato compartilhado: **efeito
  observado → publicação canônica → conclusão**, não fala como prova de efeito.
  A implementação foi ajustada no orquestrador responsável, reutilizando o
  registrador e o contrato consumidos pelos demais domínios.
- RED novo: 15 casos falharam antes do patch. Incluem sucesso, idempotência,
  falha de criação/adição, faixa ausente, dois nomes e indisponibilidade do
  publicador. No ramo sem faixa, o receipt acessava `criacao` não inicializada;
  esse caminho agora publica a falha e produz uma única resposta.
- A publicação vem antes da fala; ausente, com exceção ou `False` explícito,
  impede a confirmação de sucesso. O fluxo informa a falha de registro sem
  inventar falha da escrita nem repetir o efeito. Duplicata é reconhecida como
  estado já satisfeito; criação só é anunciada se o executor informou `criada`.
- Produção alterada nesta rodada: somente `autonomia/fluxos_conversa.py`.
  Novo teste: `scripts/tests/test_feedback_publicacao_antes_fala.py`.
  Guardião, armazenador, composition root, neural e patches paralelos intactos;
  nenhum commit, alteração das playlists pessoais ou efeito em Chrome/IoT.
- Provas: histórico P03 e controles passaram; **16 testes novos verdes**.
  Um deles importa o `laylay.py` e usa os objetos reais de feedback, registro
  musical, operações, armazenamento e publicação. CREATE/ADD gravam arquivo
  temporário, a saída verifica receipt no plano antes da fala e a segunda
  confirmação mantém uma só faixa. Voz é capturada, observação do player é
  controlada e aprendizado desligado: **integração da composição real**, não
  uma sessão completa com áudio/Chrome/modelo.
- Regressão ampliada de playlist/feedback/receipts/adaptador/cooperação:
  **348 aprovados**. O teste composto P04, executado separadamente, permanece
  **1 falha / 1 aprovado**, no contador `add_final=0` em vez de 1; não foi
  removido, alterado ou considerado resolvido pela correção P03.
- Estado P03: corrigido e validado localmente e na composição com disco real;
  sessão completa ainda pendente. Próxima fronteira operacional: esclarecer a
  medição de P04 antes de mudar o executor. Ensino/conversa permanece outra raiz.

### P18 / P19 — Escopo da consulta e evidência da confirmação — 22/09

#### Continuação de F2 — feedback diagnóstico e fala transformada, 29/09

- Loop real da P16 expôs `tamanho_invalido`/narração de erro em confirmação
  de `ja_aberto_focado`, executou=False, confirmado=True, detalhe vazio.
  O retry fornecia o motivo técnico como conteúdo. Replay local sem histórico
  aprovava a fala histórica; guardião final não a continha. Receipt falho e
  histórico obrigatório foram falsificados. O HTTP histórico não foi capturado.
- O motivo permanece local; reparo usa somente fatos/restrições existentes.
  A allowlist de parâmetros é a mesma da projeção e do verificador; contexto
  diagnóstico e parâmetros arbitrários não autorizam identificadores na fala.
  Nomes legítimos e diagnósticos publicados pelo executor continuam permitidos.
- A transformação da abertura também atravessa novamente o verificador antes
  da entrega. Aprovação anterior não aprova texto alterado. O controle antigo
  mantém a expectativa de abertura variada usando recusa factual na primeira
  frase; antes dependia de transformação não validada para passar.
- Seis REDs iniciais/controles e cinco REDs da projeção antes do candidato.
  65 testes focados de confirmação/escopo aprovados; no passe conjunto final,
  395 testes aprovados. A tentativa concorrente de importar a composição foi
  repetida depois de encerrar o processo real, respeitando a trava de instância.
- Em `roteiro_teste_personalidade_viva_p16-20260929-230505-663752`, as 14 falas
  reais posteriores não continham identificadores técnicos; motivos continuam
  observáveis nos logs. Esse roteiro teve 5/14 no placar emocional por efeitos
  de foco e pela lacuna de conquista descrita na P16; não contar como sequência
  emocional verde. Sem chamada adicional ao modelo. Prosa que inventa culpa
  sem código permanece limite de cobertura: F2 não está integralmente encerrada.

- Base: `main`, HEAD `bd94bc3e3a29c49906dc603f9ca1540310ca3274`,
  worktree suja com alterações paralelas de cliente, neural, modalidade e
  contratos operacionais. Essas alterações foram preservadas; nenhum commit.
- Evidência histórica: os dois últimos relatos em `erros/erros_encontrados.md`
  (pergunta sobre garantia de chuva amanhã; clima anexado ao salvar em yago).
  São duas causas demonstradas, não uma causa única comprovada de briefing.
- **P18 / F1, escopo perdido:** o publicador canônico de continuidade removia
  `local`, `cidade` e `day_offset`; o detector tratava o aprofundamento como
  consulta nova para hoje. O executor respondia com condições atuais sem
  responder sobre certeza. A redação histórica existe nesse executor, portanto
  não é necessário atribuí-la a briefing ou alucinação do modelo. RED local
  demonstrou a perda antes de qualquer chamada ao provedor.
- Contrato: aprofundamento meteorológico herda escopo apenas de consulta
  bem-sucedida, recente, do domínio ativo e do mesmo dia. Cidade/data explícita
  vence; troca de assunto/expiração impede herança. Probabilidade não vira
  garantia, inclusive em 0%/100%; ausência de dados não vira confirmação.
- **P19 / F2, fatos alheios na autoria:** o pedido de confirmação levava falas
  anteriores completas como exemplos de não repetição. O verificador aceitava
  a paráfrase climática histórica; repetição literal e paráfrase não são o
  mesmo contrato. Reproduzido em playlist, IoT e criação de pasta. O HTTP
  histórico não foi capturado: a exposição e vulnerabilidade estão provadas,
  mas não se afirma conhecer todo o prompt daquela execução do usuário.
- Contrato: autoria operacional recebe somente dados do resultado atual,
  usando o mecanismo existente `_contexto_fechado`. Histórico permanece no
  verificador local, não no pedido ao modelo. Números novos sem evidência
  provocam reparo e, se ele falhar, a fala factual segura. A limpeza de pergunta
  opcional também repassa por toda a validação, sem atalho de aprovação.
- Hipóteses concorrentes: defeito no provedor não explica a perda local de
  parâmetros; briefing não é necessário para produzir a resposta histórica;
  problema exclusivo de playlist é falsificado pelas provas em três domínios.
  Isso não é prova geral contra toda invenção verbal sem números.
- Produção alterada somente em `continuidade_geral.py`,
  `roteador_deterministico.py`, `orquestrador_deterministico.py`,
  `executor_informacoes.py` e `confirmacao_llm.py`. Nenhuma mudança nossa em
  pesos, ativação neural, armazenamento de playlists, IoT ou `laylay.py`.
- RED inicial: **6 falhas / 5 controles verdes**. Após candidato:
  **19/19** em `scripts/tests/test_escopo_consulta_e_confirmacao.py`, incluindo
  publicação/detecção do composition root real e preparação HTTP real com
  transporte controlado. Receipts sintéticos nessa prova não certificam efeito.
- Regressão ampliada atual: **189 aprovados / 2 falhas** em dez módulos.
  Os dois REDs são `test_fala_por_status_nao_eleva_confirmacao_negada_pelo_contrato`
  e `test_fala_por_status_nao_transforma_sem_receipt_em_sucesso`, também
  reproduzidos isoladamente no adaptador (**26 aprovados / 2 falhas**).
  A primeira divergência está antes da autoria: o construtor apaga o tratamento
  que os testes publicam antes dele; há também inferência por status quando
  `confirmado=None`. Pertencem à frente paralela tratado/receipt, não foram
  corrigidos aqui nem removidos da contagem. Verificar ciclo de vida e preservar
  a distinção entre ausência legada e incerteza explícita antes de novo patch.
- Runtime real executado com voz/microfone/presença desativados e IoT simulado:
  `resultados_testes/roteiro_escopo_previsao-20260922-064429-204197/`.
  Três consultas, nenhuma escrita de playlist. Fonte primária e reserva deram
  timeout; três falhas foram informadas com `executou=False, confirmado=False`.
  O resumo automático tem **zero casos avaliados**, não três aprovações.
  **Runtime com previsão bem-sucedida ainda não validado.** O roteiro reutilizável
  está em `scripts/roteiros/roteiro_escopo_previsao.py`.
- Estado: GREEN local/integração nos contratos novos; regressão ampliada não
  totalmente verde; P18/P19 ainda não encerrados no runtime. Próxima prova:
  repetir consulta com fonte disponível e verificar confirmação operacional
  com geração real. Relatos antigos de ensino, DEV e presença continuam
  separados; esta entrada não encerra toda a pasta de erros.

### Contrato tratado ≠ executado ≠ confirmado — 21/09

- A investigação partiu de um risco sistêmico: callbacks históricos retornam
  `True` tanto para “esta camada tratou o pedido” quanto para “o efeito ocorreu”.
  O candidato já presente na worktree separava `tratado`, `executou` e
  `confirmado`, mas ainda considerava `executou=True, confirmado=None` como
  `sucesso_habilidade=True`.
- RED real reproduzido em três fronteiras do mesmo fato: uma execução moderna
  sem receipt era registrada no autoaprimoramento como **1 sucesso / 100%**,
  recebia reforço positivo e permitia que uma cadeia avançasse para a etapa
  dependente. Foco inicial: **3 falhas e 6 vizinhos verdes**.
- Contrato canônico ficou trivalente. Para resultados modernos:
  `confirmado=True` = sucesso comprovado; `confirmado=False` = não sucesso;
  `executou=True + confirmado=None` = **resultado incerto**, nunca sucesso.
  Retornos puramente legados preservam temporariamente a compatibilidade do bool
  para não quebrar executores ainda não migrados.
- `ResultadoTratamentoOperacional` ganhou `resultado_incerto`. O
  autoaprimoramento também passou a aceitar resultado neutro: incrementa
  `tentativas` e `incertos`, mas não `sucessos`, não `falhas` e não
  `cookie_reforco`. O resumo expõe “sem confirmação”; a taxa confirmada usa
  somente resultados realmente avaliados.
- O gate central de `EstadoContextoRuntime.registrar_autoaprimoramento` não
  deixa um bool externo transformar contrato moderno em sucesso: receipt
  confirmado entra como sucesso, efeito incerto entra neutro e política/falha
  não reaparece como êxito.
- A deduplicação do `CicloComandosRuntime` estava apagando a identidade de
  compatibilidade do retorno legado. O cache agora preserva `legado` e não
  “moderniza” uma segunda ocorrência de bool antigo em contrato moderno sem
  receipt.
- A caixa de entrada expôs o inverso do mesmo princípio. O helper genérico
  continua proibido de inferir `confirmado=executou`; em vez disso, operações
  que possuem evidência local real publicam seu próprio receipt: persistência
  de nota/discussão, duplicata já observada, listagem local e exclusão salva.
  **O owner que observa o efeito confirma; a camada genérica não adivinha.**
- Provas focadas: **9/9** no contrato novo; **51/51** em cadeia/deduplicação/
  publicação; **350 aprovados + 8 subtests** nos consumidores sensíveis
  (orquestração, autonomia, caixa, transferências e mente única).
- Regressão global controlada:
  `6636 passed, 1 skipped, 13 deselected, 14 xfailed, 56 subtests passed`,
  zero falhas. Dos 13 deselecionados, oito testes do root foram bloqueados pela
  instância real já aberta e passaram **8/8** com bypass de mutex somente de
  teste; os cinco restantes foram reproduzidos no HEAD limpo
  `bd94bc3e`: três REDs históricos de feedback/playlist e dois de ownership
  de presença. Portanto não são regressões desta correção.
- Nenhuma dessas provas promove modelo neural, altera pesos ou transforma
  ausência de confirmação em falha. O objetivo é impedir sucesso fictício sem
  inventar fracasso fictício.

### Migração do legado operacional e barreira sem receipt — 21/09

- Continuação da frente `tratado ≠ executado ≠ confirmado`. Após tornar
  `executou=True + confirmado=None` neutro, a próxima pergunta foi onde um
  bool puro ainda conseguia entrar no contrato moderno.
- Scanner estático dos executores não musicais encontrou quatro saídas reais
  tratadas sem publicação explícita: volume com ação inválida, IoT
  indisponível/bloqueado antes do runtime, `SUGGEST_ACTION` e o alias
  `FECHAR_PROGRAMA`. RED no roteador real: **4 falhas e 9 vizinhos verdes**;
  todos apareciam como `legado=True`.
- Volume inválido agora publica `acao_invalida`,
  `executou=False, confirmado=False`. IoT sem runtime publica
  `indisponivel`; veto de modalidade publica
  `nao_executado_por_politica`. Nenhum desses caminhos pode mais ser
  promovido a sucesso por um bool externo.
- `SUGGEST_ACTION` permanece semanticamente sem efeito operacional, conforme
  o catálogo de capacidades. Quando a sugestão local é registrada, marca
  somente tratamento (`sugestao_registrada`), com
  `executou=False, confirmado=False`; não cria receipt de ação nem
  autoaprimoramento de sucesso.
- `FECHAR_PROGRAMA` deixou de criar um segundo dict recursivo de
  `CLOSE_APP`. O alias delega diretamente à mesma habilidade usando o mesmo
  adapter, preservando a identidade original e produzindo **um único receipt**.
  Sem alvo, publica `alvo_ausente`.
- Foi adicionado um fail-closed no roteador para executores modernos não
  musicais: se um `ResultadoDespacho` disser que tratou a intenção e nenhum
  receipt/tratamento tiver sido publicado, o resultado vira
  `tratado_sem_receipt`, com `executou=None, confirmado=None`. O bool antigo
  continua apenas em `retorno_legado`; não cria sucesso, falha ou efeito
  imaginado. Música/playlist/`MEDIA_CONTROL` ficaram explicitamente fora
  dessa barreira nesta etapa para não invadir a frente paralela do Codex.
- RED específico injetou propositalmente um executor moderno de arquivos que
  retornava `True` sem receipt. Antes: `legado=True, executou=True`; depois:
  `legado=False, tratado=True, executou=None, confirmado=None,
  status=tratado_sem_receipt`.
- O `CicloComandosRuntime` ganhou telemetria de contrato sem alterar
  autoridade ou decisão: `observados`, `legados`,
  `tratados_sem_receipt`, `confirmados`, `nao_confirmados`, `incertos`,
  além de mapas `legados_por_intent` e `sem_receipt_por_intent` e as últimas
  intents observadas. Assim, a migração futura pode ser guiada por uso real.
- O diagnóstico central já consumia
  `diagnostico_linguagem_natural()`; o formatter do Terminal agora expõe uma
  linha compacta “contrato de execução” com esses contadores e as últimas
  intents legada/sem receipt. O snapshot bruto preserva os mapas completos.
  A presença de compatibilidade legada **não degrada automaticamente** a saúde:
  nesta fase a telemetria é informativa.
- Provas da etapa: **53/53** no primeiro lote de executores/contrato;
  **184/184** em todos os executores não musicais + arquivos;
  **206/206** após adicionar a telemetria; **53/53** nas regressões de
  diagnóstico/formatter. Regressão global controlada:
  **6.642 passed, 1 skipped, 13 deselected, 14 xfailed, 56 subtests passed**,
  zero falhas. Os 13 deselecionados são os mesmos já causalmente isolados:
  cinco REDs preexistentes e oito testes de root bloqueados pela instância real.
  Os oito de root passaram novamente **8/8** com bypass de mutex somente no
  processo de pytest.
- Não houve promoção neural, alteração de pesos, commit, push, merge ou
  reescrita destrutiva. A compatibilidade booleana permanece disponível apenas
  para caminhos realmente legados; executores modernos não musicais agora
  falham fechados quando esquecem o receipt.

### Cadeias dependentes exigem sucesso do contrato — 21/09

- A telemetria/migração do contrato revelou outra fronteira booleana no fluxo
  composto. `executar_fluxo_intencao()` já interpretava
  `ResultadoTratamentoOperacional`, mas devolvia `bool(retorno)`. Assim, uma
  etapa moderna podia estar `tratada_sem_receipt`, com
  `sucesso_habilidade=False`, e ainda retornar `True` para a cadeia.
- Reprodução direta antes do patch: executor marcou
  `tratado=True, executou=None, confirmado=None,
  status=tratado_sem_receipt`, retornou `True` e
  `executar_fluxo_intencao()` também devolveu **True**.
- A causalidade foi conferida no HEAD base
  `bd94bc3e3a29c49906dc603f9ca1540310ca3274`: a versão congelada fazia
  `executou = bool(_call(... executar_intencao ...))`, publicava esse bool,
  autoaprimorava quando verdadeiro e devolvia `executou`. Portanto a
  ambiguidade já existia no baseline.
- O retorno padrão foi preservado por compatibilidade: fora de composição
  dependente, `True` ainda pode significar “o turno foi consumido/tratado”.
  Foi adicionado o modo explícito
  `exigir_sucesso_habilidade=True`, que devolve somente
  `tratamento.sucesso_habilidade`.
- `CicloComandosRuntime.processar_cadeia()` é o único consumidor conectado a
  esse modo estrito. Consultas somente leitura continuam concluindo sua etapa
  pelo próprio contrato observacional; mutações passam pelo modo estrito.
- Consequência: se a etapa A for tratada mas não tiver receipt suficiente, a
  cadeia relata a falha e **não chama a etapa B dependente**. O comportamento
  standalone permanece compatível, evitando transformar “não avançar cadeia”
  em “reprocessar o turno inteiro”.
- RED de fronteira inicialmente falhou porque o modo estrito não existia.
  Após a correção, o mesmo caso preserva `True` no standalone e retorna
  `False` no contexto dependente. Teste de composição adicional prova que a
  cadeia canônica chama somente a primeira etapa com
  `exigir_sucesso_habilidade=True` quando ela falha.
- Regressão focada após a mudança: **23/23** nos contratos históricos do fluxo
  e **90/90** no conjunto coordenador/cadeia/linguagem natural/contexto.
  Regressão global controlada final: **6.645 passed, 1 skipped,
  13 deselected, 14 xfailed, 56 subtests passed**, zero falhas. Os mesmos oito
  testes de root bloqueados pela instância real passaram **8/8** com bypass de
  mutex somente no pytest.
- A compatibilidade de bool realmente legado continua temporariamente fora
  desse fechamento total; a frente musical paralela também não foi alterada.
  O objetivo desta etapa foi impedir que **resultado moderno explicitamente
  não comprovado** libere uma dependência posterior.

### Raiz de versionamento da supervisão neural — 21/09

- Base `main`, `bd94bc3e3a29c49906dc603f9ca1540310ca3274`; worktree
  paralela preservada, incluindo `modelo.py` da v29. Primeira fronteira RED:
  leitores históricos recusavam duas dependências da linguagem diferentes.
  Reprodução direta, ultrapassando apenas a leitura para diagnóstico:
  `conferir_casos` falha por **alinhamento divergente**, não por import.
- Falsificadas as hipóteses de corpus alterado e de mudança somente nos hashes:
  os lotes mantêm seus SHA-256, mas há **144 divergências** em cada lote
  (mesmos casos, não 288 casos únicos). Em 96 mudou apenas a referência de
  leitura; em 48 também mudaram segmentação e offsets relativos. O diff da
  linguagem mostra reconhecimento ampliado de recusa e moldura de necessidade.
  Os arquivos de linguagem são iguais a HEAD; não atribuir o bloqueio ao SOL.
- Contrato: **anotação independente preservada não implica leitura histórica
  equivalente**. Owner offline `revalidar_perfil_v4.py` ganhou reprojeção
  explícita, mantendo o replay estrito como padrão. Compara supervisão completa
  em coordenadas literais absolutas: atos, âncoras, alvos/papéis, relações,
  texto e metadados; valida referências, flags e spans antes da comparação.
  Normalização não literal exige outro perfil. Não utiliza previsão como gold.
- Via nova limitada aos pares de dependências revisados e ao manifesto exato
  das divergências observadas. Mudança futura, corpus modificado, reserva,
  identidade duplicada, alteração de supervisão ou corrida de arquivo abortam.
  Preserva protocolos, folds e leitores antigos; não altera resultados antigos.
  Relatório declara `compatibilidade_no_corpus=false`, supervisão preservada,
  classificador não reavaliado e runtime não validado.
- Os testes dos algoritmos atuais agora pedem a reprojeção explicitamente.
  Não enfraquecidas as asserções de comportamento; testes negativos continuam
  exigindo bloqueio dos leitores históricos. Asserções específicas protegem
  adulteração de atos, alvos, âncoras, relações, referência e autoridade.
- **53 testes focados passaram** antes dos controles adicionais. CLI offline
  real executada com sucesso, sem fit: **1.176 casos únicos**, folds idênticos.
  Evidência: `memoria/neural/experimentos/reprojecao_literal_v4_20260921/relatorio.json`.
  Regressão neural ampla após os controles adicionais: **1.425 aprovados,
  1 skipped, 5.220 deselected**, zero falhas/erros, 105,63 s
  (`pytest scripts/tests -k neural -q --tb=short`). Os 23 bloqueios anteriores
  foram resolvidos. Isso não é suíte global, runtime da assistente ou prova
  de qualidade da v29. `compileall` focado e `git diff --check` passaram.
- **Observação separada, associada à fronteira F1, ainda não diagnosticada:**
  no caso `rel_v4_necessidade_apps_e0_t0_q0_recusa_pedido`, a cláusula
  “não é para abrir o aplicativo pelvora” aparece como `conversa`, sem veto,
  enquanto a anotação mantém `recusa`. O pedido subsequente é separado.
  Não houve executor nessa prova; não concluir que a ação proibida foi executada.
  Próxima investigação deve testar recusa isolada/mista em domínios distintos
  no owner de modalidade e no consumidor de autoridade, antes de corrigir.
- **Fechamento da observação F1 — recusa declarativa “não é para…”:** o RED foi
  reproduzido em app, arquivo e IoT; 4 casos falharam com 20 vizinhos verdes.
  A raiz ficou em `analisar_protecao_operacional`: a moldura declarativa
  `não é/eh para|pra + infinitivo operacional` não possuía leitura geral.
  O contrato foi corrigido no owner de modalidade, sem regra privada por domínio.
  Interrogação continua pergunta; sem interrogação vira `recusa/cancelamento`.
  Em turno misto, o veto pertence somente ao segmento recusado, enquanto um
  pedido independente posterior continua autorizado. Teste do consumidor
  confirma que `processar_execucao_pratica_precoce` entrega somente
  `texto_operacional` do pedido permitido ao determinístico.
- O corpus histórico contém **72 nós** com essa moldura e gold `recusa`; após
  a correção, 72/72 são lidos como recusa com veto. A guarda de compatibilidade
  bloqueou a mudança de `modalidade_turno.py` antes de qualquer atualização.
  Replay explícito preservou supervisão literal e as quatro dobras: a diferença
  contra o snapshot histórico passou de 144 para **160 casos**, com as mesmas
  48 resegmentações. Os 16 deltas novos são recusas isoladas de apps/arquivos
  agora alinhadas ao gold; snapshot observado não foi promovido a gold.
- A reprojeção v1 foi preservada. Nova prova publicada em
  `memoria/neural/experimentos/reprojecao_literal_v4_recusa_declarativa_v2_20260921/relatorio.json`.
  Regressões: **25** testes focados de autorização/consumidor, **33** de
  reprojeção, **76 aprovados + 1 skipped + 22 subtests** em modalidade/autoridade,
  e **1.426 aprovados, 1 skipped, 5.226 deselected** na suíte
  `pytest scripts/tests -k neural -q --tb=short`, zero falhas/erros.
  Isso não certifica runtime completo, qualidade da v29 nem execução real.
- Escopo da etapa de reconciliação anterior: um módulo de infraestrutura
  experimental, quatro módulos de testes e documentação. Naquela etapa,
  linguagem de produção, modelo SOL, pesos ativo/v27, configuração e reserva
  v29 permaneceram intactos. A investigação F1 acima alterou depois somente o
  owner de modalidade; não houve commit, promoção ou ativação.

### Reconciliação das frentes neurais — 21/09

- Base `bd94bc3e`, mudanças paralelas preservadas. Após a cópia da v29, o
  consumidor operacional permaneceu mas perdeu a API opcional de projeção:
  **36 falhas TypeError**. Reposto `rotulos_permitidos` em
  `comparar_ocorrencias_v4.py`, sem mudar o catálogo padrão. README agora mantém
  tanto a v29 do SOL quanto a retomada de cobertura/IoT/mídia. Nenhum patch em
  `modelo.py` entregue pelo SOL; SHA-256 preservado
  `58af0476a9907870ed471e5d0e4e91e104213d32f936b199d51e34efd960ef6a`.
- Testes v29 citados no handoff ausentes da cópia local: seis casos de contrato
  escritos no teste existente para integral/híbrido, OOF, grupos, serialização,
  encoder ausente e preservação da base. Encoder sintético, sem certificar
  qualidade linguística. **75 testes focados passaram**, mais **93 regressivos**
  de coleta/revisão/protocolo/preparação. Modelos ativo/v27 com hashes preservados.
- Suíte neural ampla: **1.384 aprovados, 1 skipped, 6 falhas, 21 erros**. Quatro
  falhas vinculadas à raiz já conhecida de caminhos pós-reorganização: fixture
  de revisão contextual ainda apontava para `tests/fixtures`. Caminho ajustado,
  **32 testes do módulo passaram**, nenhuma expectativa relaxada.
- **Pendência separada de compatibilidade histórica:** 21 erros e duas falhas
  restantes param nos hashes do corpus v4. `modalidade_turno.py` e
  `normalizacao_linguagem.py` são iguais a HEAD e diferem dos hashes exigidos
  pelo protocolo antigo. Não causada pela interface reposta nem atribuída ao
  SOL. A via de revalidação existente só autoriza outra revisão antiga do
  normalizador. Falta provar compatibilidade integral do alinhamento atual;
  nenhuma guarda, baseline ou reserva foi alterada. Não declarar suíte verde.
- Sem treino de produção, promoção, interferência na sessão ou commit. Fits
  executados apenas pelos testes com dados sintéticos e artefatos temporários.

### Continuação: coleta recuperada e preservação de foco, 21/09

- Base atual `bd94bc3e3a29c49906dc603f9ca1540310ca3274`. Recuperação do
  analisador já incorporada por commit externo; AST das funções comparada com
  `c8b4c26`, sem diferenças. **85 testes aprovados**; **6.537 testes coletados
  sem erro** antes da nova regressão de foco. Não equivale a executar a suíte
  global nem a validar/promover o modelo histórico.
- Nova observação do Pedro em `../erros/erros_encontrados.md`: troca de faixa
  ativa YouTube e interrompe estudos. Registrada como **P17**, raiz própria de
  transporte da restrição de foco, sem misturar com as raízes conversacionais.
- Preservadas alterações de empacotamento e o relato do usuário. Pedro informou
  trabalho paralelo do ChatGPT: verificar sobreposição antes de editar e avisar
  imediatamente se houver evidência de risco. Nenhum conflito observado nos
  arquivos deste candidato; isso não é auditoria de todo trabalho paralelo.

### Continuação após reorganização do repositório, 21/09

- Base `d268a51`, preservada a nova organização. P09: ajustados pytest,
  imports/caminhos relativos dos testes movidos, sonda e catálogo DEV Console.
  **60 testes focados aprovados**; seleção ampliada **3.018 aprovados,
  14 xfailed e 30 subtestes**. Não é certificação da suíte global.
- Coleta global bloqueada por dependência ausente:
  `analisar_neural_v27_list_windows_caos`, importada pelo teste homônimo.
  **6.526 testes coletados e um erro**. Não removido nem enfraquecido o teste;
  analisador não restaurado sem conferir sua finalidade e versão.
- Encerramento da sonda: repetição com receipt do processo pai resultou em
  **código 0 e stderr vazio**. Código 1 histórico não reproduzido, causa aberta;
  nenhum patch especulativo no lifecycle. O log genérico que anuncia reinício
  mesmo ao concluir roteiro é impreciso, não prova reinício real.
- Evidência e limites em `../raiz/MAPA_RAIZES_CONVERSA.md`, seção de
  infraestrutura após reorganização. Documentos movidos pelo usuário preservados.

Este é o índice central dos problemas encontrados enquanto corrigimos outros
problemas. Serve para não perder achados, não misturar causas e deixar claro o
que falta. Os relatórios ligados abaixo preservam o diagnóstico detalhado.

O preenchimento inicial usa os relatórios de 12–15/09 e as validações da última
rodada. **Não é uma auditoria exaustiva nem uma nova execução dos testes.**
Uma ocorrência antiga permanece datada até ser revalidada.

## Como manter este arquivo

- Ao encontrar um problema lateral, registrar aqui antes de desviar da correção atual.
- Manter o ID do item; atualizar seu estado e acrescentar evidências, sem apagar o histórico.
- Separar sintoma de causa: várias falhas podem ter a mesma raiz; isso precisa ser provado.
- Informar se a evidência é de runtime, integração ou teste unitário.
- Só marcar uma correção como validada no escopo depois de registrar o teste e seus limites.
- Impacto indica risco, **não muda automaticamente a ordem do trabalho** nem autoriza ações destrutivas.
- Nunca copiar credenciais, tokens ou conteúdo pessoal desnecessário para este índice.
- Ideia futura não é defeito e não significa implementação aprovada.

Estados usados: **a investigar**, **reproduzido**, **parcial**, **limite não validado**,
**adiado**, **validado no escopo** e **ideia guardada**.

## Visão rápida das pendências

| ID | Assunto | Estado | Impacto |
| --- | --- | --- | --- |
| P01 | Explicações ruins sobre como usar capacidades | Parcial: catálogo preservado; qualidade ainda aberta | Coerência e confiança |
| P02 | Recomendações técnicas sem evidência suficiente | 13 REDs corrigidos no escopo de escolha/fala; runtime 30/09 | Comparação técnica completa ainda não certificada |
| P03 | Confirmação de playlist antes do receipt | Corrigido em 22/09; integração da composição real e disco temporário validada; sessão completa pendente | Alto: confirmação prematura |
| P04 | Divergência no contador de ADD do teste composto | Encerrado em 22/09: instrumentação observava o wrapper legado; porta detalhada executava e persistia | Medição corrigida sem alterar produção |
| P05 | Presença não cede na transição da entrada para o turno | Reproduzido em teste de integração | Interferência na fala do usuário |
| P06 | Ponto de extensão em nome de arquivo | Corrigido no escopo; composição e runtime 30/09 | Pontuação interna preservada sem autoridade adicional |
| P07 | Continuidade na rota exclusivamente de áudio | Limite não validado | Possíveis lacunas de histórico |
| P08 | Credencial em logs históricos do Chrome | Parcial: saída nova corrigida | Alto: artefatos sensíveis |
| P09 | Novos testes ficam ignorados pelo Git | Regra corrigida e validada em 21/09; sem staging | Revisar fontes antes de versionar; artefatos já rastreados exigem ação separada |
| P10 | Falso positivo de fundamentação em citação | F1: exemplos com “pedir para” também validados em 21/09; escopo mais amplo aberto | Proteção não deve apagar instruções válidas |
| P11 | Pedido de informação confundido com afirmação de estado | Validado no escopo; ver C08 | Fallback desnecessário corrigido nos casos cobertos |
| P12 | Pergunta de procedimento sem natureza operacional reconhecida | Classificação validada no escopo C11; resposta final ainda falha | Reparo posterior separado em P16 |
| P13 | Nome de aplicativo não recupera seu domínio no catálogo | Recuperação validada no escopo C12 | Resposta final ainda afetada por P10 |
| P14 | Resposta prioritária IoT troca ação e dispositivo | Corrigido e validado no escopo C13 | Qualidade mais ampla da autoria continua em P01 |
| P15 | Falha técnica tratada como pedido ambíguo | Validado no escopo de propagação; limites de conclusão registrados | Causa da latência não investigada |
| P16 | Reparo de explicação presume relato de ação passada | Validado no escopo C15 | Objetivo e fonte preservados; qualidade geral ainda em P01 |
| P17 | Restrição de foco perdida no transporte ao Chrome | Troca musical confirmada por Pedro; fallback compartilhado protegido e testado localmente | Preservação do foco também nas rotas alternativas |

A frente atual é **P01**. O corte do catálogo (C07) e o falso reparo P11 (C08)
foram tratados separadamente; falta melhorar a realização da explicação. A investigação
de recomendações **P02** foi retomada em 30/09 por pedido do Pedro, junto de P06,
antes da continuidade da personalidade P16. Os 14 xfails foram corrigidos por
essas duas causas; a comparação técnica completa continua limitada. A revisão
offline de compatibilidade não promove a rede neural.

## Pendências detalhadas

### Organização por contratos — diagnóstico de 20/09

O [mapa causal da conversa](MAPA_RAIZES_CONVERSA.md) passa a orientar a próxima
etapa: F1 significado, F2 capacidade/fonte/escopo e F3 causa técnica. As famílias
não substituem os IDs nem significam que todos os itens têm uma única raiz.
P01 é abrangente; evitar contá-lo novamente como causa de cada subproblema.

Nesta auditoria, nenhum patch novo de produção: quatro REDs de negativas falsas
em música/sistema/IoT/navegador e um RED de exemplos no infinitivo confundidos
com obras: **cinco REDs, oito controles aprovados** e 261 regressivos anteriores
aprovados. O bruto da retomada já negava a capacidade; o verificador ainda
cortou as instruções, agravando a fala. REDs preservados sem xfail no teste
`test_coerencia_capacidade_documentada.py`. P15 também reproduzido localmente:
três categorias técnicas chegam à contingência como se faltasse clareza.
Próxima implementação: coerência documental compartilhada (F2), depois
propagação da causa técnica (F3), sem novo remendo específico para música.

**Experimento F2, 20/09 às 17:00:** projeção ampliada de contratos operacionais
testada e retirada por não demonstrar benefício global no runtime. Doze
respostas, zero comandos; negativas/promessas inadequadas e cortes ainda
presentes. Dados extras no prompt não corrigiram a conferência da resposta.
Cinco REDs comportamentais preservados; não declarar outra correção concluída.
Detalhes e artefatos no mapa causal. A regra de organizar por raiz foi gravada
no `AGENTS.md`; nenhuma alteração permanente nova em produção nesta rodada.

**F2, 20/09 às 22:10 — conferência validada no escopo, reparo ainda aberto:**
o mesmo comparador passou nas negativas de música, aplicativos, IoT e abas,
com predicados do snapshot canônico e sem ampliar o prompt inicial. Disponibilidade
não virou receipt nem autorização. Seleção ampliada: 2.913 aprovados, um RED
F1, 14 xfailed preexistentes e 30 subtestes; controles posteriores na seleção
focada: 58 aprovados e o mesmo RED F1. No replay pelo runtime real, a negativa
histórica foi detectada; o Qwen repetiu a contradição no reparo, que foi rejeitado.
A resposta final pediu clareza indevidamente (F3). Portanto, não encerrar P01:
há prova de bloqueio, não de recuperação da explicação. Próxima fronteira F2:
isolar influência do rascunho/histórico no reparo, sem empilhar instruções.
Captura `transporte_evidencia-20260920-221039-790886`; detalhes e escopo no mapa.

### P01 — Explicações de capacidade e instruções pouco coerentes

- **F2, 20/09 às 22:18:** ablação de 21 chamadas locais isolou duas cópias do
  conteúdo refutado no reparo (rascunho e trecho de diagnóstico). Retirar só
  histórico ou só uma cópia não eliminou a negativa; retirar ambas conservando
  histórico não a repetiu nas três amostras, embora restasse imprecisão.
  Corrigida a projeção no reparador compartilhado, sem aumentar prompt/orçamento
  ou alterar os executores. Quatro REDs por domínio passaram com a mesma regra;
  ampliado: 2.929 aprovados, um RED F1, 14 xfailed e 30 subtestes. Replay real
  reparou a negativa histórica para uma instrução de retomada, sem fallback ou
  comandos; 12/12 no avaliador mínimo não significa qualidade global. Captura
  `transporte_evidencia-20260920-221832-302877`. Paráfrases ainda escapam da
  conferência, IoT ainda transferiu checagem ao usuário e uma variação de PC
  foi cortada. Detalhes no mapa causal; P01/F2 continuam parciais. Próxima raiz
  priorizada: F3, conclusão coerente para falha técnica, não nova expansão neural.
- **C18, 20/09:** descrição de controle local sustentada pela documentação do
  turno não é mais confundida com disponibilidade de obra na plataforma PC.
  Quatro REDs causais passaram; seleção ampliada: 2.873 aprovados e 14 xfailed
  preexistentes. Replay da resposta histórica de volume no runtime preservou
  a frase inteira, sem comandos. A sonda terminou com 12 respostas e 11/12 no
  avaliador mínimo: a geração nova de retomada voltou a negar controle de áudio
  (turno 3). Próxima investigação: confrontar essa negativa com a documentação
  efetivamente entregue ao modelo. P01 permanece parcial; a regra C18 cobre uma
  família gramatical delimitada, não todas as paráfrases nem qualidade global.
- **Após C17, 20/09:** exemplos de comandos sobreviveram nas duas sondas.
  Separadamente, o replay de volume ainda teve a frase sobre sistema local/PC
  removida por `plataforma_sem_evidencia`. A geração nova de retomada chegou a
  negar controle de áudio apesar do catálogo, e IoT voltou a sugerir conferência
  manual de configuração. Esses achados impedem encerrar P01 ou usar o 12/12
  mínimo como prova de qualidade global. Próxima investigação delimitada:
  distinguir descrição de capacidade local de alegação sobre plataforma externa.
- **C16, 20/09:** catálogo passa a descrever limites com escopo, condição e
  responsável. Na projeção para autoria, a regra do envio remoto não é mais
  o limite textual único do sistema. Controle local e envio a outro PC ficam
  separados; releitura IoT é responsabilidade interna da Laylay. O formato
  textual legado é derivado das mesmas regras, sem cadastro duplicado.
  Sonda com geração nova confirmou documentação no HTTP e respostas de
  calculadora/volume sem exigir PC remoto. A fala IoT não pediu ao usuário
  que relesse o dispositivo. **Resultado final ainda parcial:** P10 apagou
  exemplos didáticos em quatro turnos; a frase sobre controle local de volume
  também foi cortada por `plataforma_sem_evidencia`. O modelo ensinou abrir o
  controle de volume, em vez de só pedir o ajuste: precisão geral ainda aberta.
- **19/09, após C15:** no reparo real de volume, o Qwen manteve a explicação,
  mas ainda acrescentou requisito de PC remoto. O verificador retirou essa frase
  (`plataforma_sem_evidencia`) e preservou a instrução. Na mesma sonda, IoT
  transferiu ao usuário a responsabilidade de reler o dispositivo. Próxima
  investigação: escopo dos limites e responsabilidades na documentação por
  capacidade/rota, sem retirar a proteção factual ou criar falas fixas.
- **Encontrado durante:** validação de recusas e continuidade do histórico.
- **Exemplo:** “como eu poderia pausar a música?” recebeu explicações de acesso
  ao player e digressões desnecessárias, apesar de a pergunta direta de capacidade
  ser respondida pelo catálogo local.
- **Comprovado:** desvio no runtime em sondas de 14–15/09. Não houve comando.
- **Atualização de 15/09, tarde:** a captura nas duas fronteiras provou perda do
  catálogo na compactação HTTP: presente no pedido/preparação, ausente no envio.
  C07 preserva a evidência nas rotas normal e rápida. O contrato de não execução
  não mudou; o problema não se resume à competência do Qwen ou ao histórico.
- **Ainda aberto:** a descrição geral das capacidades, agora entregue, não bastou
  para produzir uma instrução boa. A sonda posterior chegou a um fallback por P11.
  Portanto **P01 não está encerrado**, apesar do transporte corrigido.
- **Próximo passo após C08:** reavaliar a realização de instruções com o catálogo
  vivo, inclusive disponibilidade negativa, sem converter pergunta em autorização
  nem criar uma resposta fixa por habilidade. Na sonda de 17:19 a fala não teve
  fallback, mas incluiu “não preciso te ensinar nada”: qualidade e tom ainda RED.
- **Fechar quando:** explicações úteis e verdadeiras, com capacidade disponível e
  indisponível, passarem por contrastes e runtime sem execução não solicitada.
- **15–16/09 — candidato C09:** tarefa de autoria textual separada do planejamento,
  com documentação viva ligada ao texto/ID do turno. Sem fala fixa por habilidade;
  pergunta continua sem autorização e propostas indevidas continuam bloqueadas.
  Disponibilidade parcial, vários atos e referências não recuperadas conservam
  o fluxo completo. A personalidade-base não foi reescrita.
- **Resultado intermediário:** o Qwen passou a ensinar o pedido de pausa; a primeira
  sonda revelou que P10 apagava esse exemplo após a geração. Após o candidato C10,
  os turnos 1 e 2 da sonda de 15/09 às 18:50 chegaram inteiros ao chat. Essa sonda
  foi **interrompida após 8/12 respostas**, não é uma execução concluída.
- **Limites descobertos:** P12/P13 mantêm quatro REDs (duas entradas, rotas normal
  e rápida). P14 é uma resposta fixa anterior à LLM, portanto não se resolve com
  o prompt novo. Não declarar P01 globalmente corrigido.
- **Validação final de 16/09:** seleção ampliada com **1.307 aprovados e quatro
  falhas**, todas de cobertura P12/P13. Sonda completa de 12 mensagens: dez
  aprovações mínimas, duas falhas IoT e zero comandos. Exemplos de pausa/retomada
  preservados no chat; ofertas laterais, promessas e continuação presumida ainda
  impedem considerar a qualidade globalmente aprovada.
- **Evidência:** [histórico e sondas de 15/09](RELATORIO_COLETA_DEBUG_20260914.md#histórico-de-respostas-locais-e-continuidade--15092026).
  [Diagnóstico do corte e resultado parcial](RELATORIO_COLETA_DEBUG_20260914.md#capacidades-relevantes-no-transporte--15092026).

**23/09 — ensino multifonte, mesma raiz P01:** recuperação trouxe “vista
superior”, mas a fala “de baixo para cima” passou sem alerta pelo verificador.
Uma sonda de sete alegações com o Qwen acertou os rótulos, mas somente três
tinham índice/citação literal válidos; não integrar como portão de verdade.
Separadamente, a consulta de RGB de `planta` nasceu do detector IoT, não da
pesquisa factual. A guarda de ordem direta para cor livre passou em 34 testes
IoT, inclusive composição; ainda falta conversa completa no runtime. Evidência
e próximos controles em `PLANO_ENSINO_FUNDAMENTADO_LAYLAY.md` e
`scripts/analises/sonda_verificacao_ensino_com_fonte.py`.
Repetição real mostrou outra primeira fronteira: `operacao_explicita=iot` no
retrato por menção de “luz”, vetando pesquisa. A guarda no retrato fez a fonte
voltar ao plano sem comando; o extrator separou “com um exemplo” do tema. A
última sonda expirou no Qwen, então P01 permanece aberto e sem GREEN factual.

**24/09 — P01, auditoria didática em sombra:** a fala candidata pós-verificador
agora recebe um diagnóstico de segmentos, fontes do usuário e comparações
numéricas limitadas. A fala real do sensor é coberta textualmente, mas as
caudas sobre “garantir” umidade e “equilíbrio” ficam sem âncora literal e
pendentes de revisão. Mesmo trecho literal não é tratado como implicação. A
auditoria não muda fala, executor ou autoridade; 145 regressivos focados
passaram. Ainda falta sonda do Qwen no runtime real, revisão semântica da fala
entregue e solução para a composição de alegações adicionais. **P01 segue
aberto**; não contar esta observabilidade como correção de qualidade.

**24/09, sonda real P01:** com Qwen3:4b-instruct e IoT simulado, a geração
HTTP do último turno já incluiu causas/consequências não dadas pelo usuário;
o texto entregue foi idêntico. O payload continha cenário, foco, 15% e 20%,
falsificando falta dessas premissas como raiz desse turno. Auditoria em sombra:
8 segmentos sem âncora literal, 0 comparações locais, sem veto nem efeito.
Houve timeout no primeiro turno; o placar 2 passados/1 falha/1 alerta é
limitado pelo avaliador lexical. Artefatos e limites no plano de ensino.

**24/09 — contrato formal offline P01:** cobertura integral de spans e
citações de fonte registrada passam a ser verificáveis sem conferir verdade;
papel, atomicidade, condição e implicação continuam pendentes. Cauda sem fonte,
omissão, sobreposição, citação forjada e fonte da assistente são recusadas no
envelope de oito testes novos. Seleção conjunta: 192 passed. Sem promoção à
fala do runtime, veto ou executor; falta produtor e revisão semântica
multidomínio antes de atacar a geração RED.

**24/09 — piloto de proponente P01:** Qwen3:4b-instruct recebeu segmentos
fixos e fontes registradas para cinco falas (sensor real + quatro controles).
Cobriu índices, mas inventou citação no sensor/matemática, citou condição
omitida em floricultura/programação e marcou a cópia literal positiva como
`nao_factual`. O código recusou as citações inválidas; as localizadas
continuaram semanticamente pendentes. Recibo aritmético independente protege
somente a equação, não a conclusão sobre pessoas. 199 regressivos relacionados
passaram. Sem integração do piloto ao runtime; P01 permanece aberto.

**24/09 — grafo de premissas P01, ainda offline:** nove testes novos
conferem fontes, escopo, identidade dos referentes, valores literais e
condições separadas em sensor, programação e floricultura; seleção relacionada
de 49 testes passou. Citação literal pode estar ligada ao sensor errado:
sem revisão semântica, o grafo não aprova composição nem ação. Nenhuma mudança
na fala do runtime; próxima fronteira é validar vínculos, direção e condições
independentemente em casos inéditos. P01 permanece RED.

**24/09 — pistas de vínculo P01:** após validar a estrutura do grafo, a
auditoria offline sinaliza referente textual ausente, direção numérica
invertida e negação que impede leitura simples. RED reproduzido para “não
cair abaixo” antes do ajuste; 69 regressivos relacionados passaram. Pistas
textuais não certificam implicação nem condição satisfeita; nenhum efeito na
fala real. Próxima prova: gabaritos independentes e casos novos. P01 aberto.

**24/09 — gabarito local P01:** quatro cenários inéditos, com rótulos manuais
separados do auditor, expõem falso positivo de entidade/valor na mesma frase,
abstenção em correferência correta e condição omitida que o auditor não mede.
Gabarito não é revisão externa. RED estrutural de número com unidade separada
por espaço corrigido antes da medição; nenhuma promoção à fala, pesquisa,
treino ou ação. Próxima fronteira: revisor de relações e completude de
condições, seguido de produtor automático somente em sombra. P01 segue RED.

**24/09 — cobertura condicional P01, ainda offline:** a proposta agora é
confrontada com condições de referência anotadas separadamente, após validar
fontes e escopo. Cache, sensor e cultivo reproduzem omissões; duplicatas e
efeito divergente são controles negativos. O placar do cache passou de
`nao_medida` a `condicao_omitida`. Seleção de 86 testes relacionados passou.
Revisão não autenticada, conectivo `e/ou` não representado e semântica ainda
pendente; nenhuma influência na fala ou execução. P01 permanece aberto.

**24/09 — relação lógica P01, offline:** regras passam a representar
conectivo plano e direção da implicação, com padrão indeterminado. REDs de
`e` versus `ou` e `se` versus `somente quando` ficaram distinguíveis após
confronto com regras revisadas fora dos candidatos. Gabarito local de quatro
casos contém agora condições e relação tipadas; 94 testes relacionados
passaram. Condições completas e relação correta são métricas separadas.
Conectivos aninhados, revisão semântica independente e produtor em sombra
seguem pendentes; nenhuma fala, executor ou treino alterado. P01 aberto.

**24/09 — primeiro produtor P01 em sombra, RED na entrada estruturada:**
Qwen3:4b-instruct recebeu seis fontes inéditas com referentes e efeito fixos,
sem acesso ao gabarito separado. Cinco regras propostas falharam na estrutura
(operador/citação/unidade/valor incompatíveis); na sexta, a árvore mista foi
achatada apesar da instrução de abstenção. **0/6** alinhadas, sem inferir
qualidade de ensino ou uso real. Conferidor local: 10 testes focados e 36
testes de grafo relacionados passaram. Os arquivos e hashes do painel estão
no plano de ensino fundamentado. Primeira fronteira demonstrada: produtor de
condições, não o executor nem o comparador. Próxima prova: contrato de saída
decomposto e novo painel cego. Nenhuma alteração em produção, treino, fala ou
ação; P01 continua aberto.

**27/09 — P01, dois estágios em sombra e painel v3:** o contrato separou
trechos/relação de normalização tipada. V2 foi reutilizado somente como
diagnóstico após ajuste conservador da aferição; não conta como holdout.
No v3 novo, Qwen3:4b-instruct alinhou 1/6 de ponta a ponta. Três casos
falharam em citação/limite do trecho, um em cardinalidade do conectivo,
e a árvore aninhada foi achatada; apenas o bicondicional chegou ao segundo
estágio. Portanto a primeira fronteira RED continua na seleção e relação
das condições; a generalização da normalização permanece desconhecida.
Painéis, hashes e limites estão no plano de ensino fundamentado. Nenhum
treino, executor ou fala de produção alterado. Próxima prova: candidatos
literais indexados sem gabarito no prompt e painel cego adicional. P01 aberto.

**27/09 — P01, hipótese de offsets livres falsificada em diagnóstico:**
o protótipo de intervalos reconstrói citações literais a partir da fonte e
passou cinco controles locais, mas Qwen3:4b-instruct não alinhou nenhuma das
seis propostas no painel v3 reutilizado. Os primeiros REDs foram limites de
condições, combinação inválida de abstenção/campos e direção/conectivo;
árvore aninhada ainda foi achatada. Como v3 já fora usado, este 0/6 não é
novo holdout nem prova estatística de piora. Próxima hipótese: selecionar
entre candidatos atômicos com cobertura verificável, sem entregar rótulos
revisados ao modelo. Nenhuma promoção, fala, treino ou executor alterado.

**27/09 — P01, candidatos literais e cobertura limitada:** painel v4 novo,
congelado antes da geração, expôs cinco regras planas cobertas, uma regra
com `quando` sem candidato e uma árvore mista. Na primeira sonda real com
Qwen3:4b-instruct, 4/5 regras cobertas tiveram seleção e relação alinhadas à
revisão local (4/7 do painel inteiro). `apenas se` continuou invertido em
`ARQUIVO_ONLY`; `TRAVA_MISTA` foi achatada pelo modelo e recusada no confronto.
Teste RED→GREEN acrescentou veto conservador de mistura `e/ou` antes da
consulta, sem contabilizá-lo como acerto da primeira sonda. O gerador é
lexical, pode cortar sujeitos compostos e não cobre `quando`; revisão local
não autenticada, sem avaliação da normalização, ensino, verificador ou fala
real. Detalhes e hashes estão no plano de ensino. P01 aberto, sem produção.

**27/09 — P01, marcador lógico e painel v5:** sinal lexical conservador veta
direção incompatível de `apenas/somente/só se` e bicondicional sem depender
do gabarito; `quando` simples continua indeterminado. A composição offline
agora não confunde o `se` pronominal de `se move` com `apenas se`. Painel v5,
congelado antes da geração: cinco regras planas cobertas, uma falha de
segmentação no sujeito composto e uma recusa de árvore mista. A primeira
sonda Qwen3:4b-instruct alinhou 3/5 regras cobertas (3/7 total); errou `ou`
como `e` e absteve-se da direção em `quando`. Um RED posterior provou que o
conectivo ainda dependia do gabarito; guarda textual externa RED→GREEN
acrescentada, sem contabilizar ganho retroativo. A referência é manual local,
não prova ensino, verificador ou fala final. P01 aberto; sem treino/promoção.

### P02 — Recomendação técnica sem vínculo verificável com fontes

- **Encontrado durante:** correções dos relatos do Pedro sobre hardware e pesquisa.
- **Última evidência registrada:** 13/09. O modelo ainda recomendou uma peça com
  especificações não sustentadas mesmo recebendo instrução para não escolher sem base.
- **Estado em 30/09:** retomado a pedido do Pedro; 13 reproduções corrigidas e
  xfails retirados após controles, composição instalada e prova no loop real.
  O candidato de prompt de 13/09 permanece retirado; a correção atual restringe
  planejamento e publicação ao alcance da evidência pelo owner factual.
- **Contrato entregue:** pedido → candidato observado → fonte/trecho →
  afirmação de presença na fonte. Requisitos de adequação ficam explicitamente
  `nao_comprovado`; ausência de fonte não produz uma escolha nem atributos.
- **Limite:** comparação técnica completa e qualidade de respostas introdutórias
  permanecem sem certificação. Não usar a aprovação estrutural do roteiro
  histórico como prova da correção elétrica dos outros turnos.
- **Provas e escopo:** [revisão P02/P06 de 30/09](../relatorio/RELATORIO_P02_P06_20260930.md).
- **Fechar quando:** faltas de dados, fontes contraditórias e pesquisa indisponível
  não produzirem especificações, compatibilidades ou pesquisas inventadas no runtime.
- **Evidência:** [relatório de recomendações e retirada do candidato](RELATORIO_CORRECOES_CONVERSA_20260912.md).

### P03 — Playlist: fala de confirmação anterior ao receipt

- **Encontrado durante:** regressão ampliada da correção de histórico, em 15/09.
- **Comprovado em teste:** o receipt aparece depois da chamada de voz (`4 < 3`
  falha). O teste alcança CREATE/ADD; não falha no import.
- **Contrato:** receipt confirmado antes da confirmação verbal de efeito.
- **Próximo passo:** rastrear a ordem no fluxo canônico de feedback e comparar
  a composição do teste com produção. Não afirmar que a falha de produção atual
  foi reproduzida apenas porque esse teste falhou.
- **Fechar quando:** sucesso, falha e idempotência publicarem resultados na ordem
  correta, com regressão de composição e prova no runtime.
- **Teste:** [test_red151_c3_guardiao_receipt_saida.py](../tests/test_red151_c3_guardiao_receipt_saida.py),
  `test_red151_c3_feedback_simples_registra_receipt_antes_da_fala`.
- **Controle:** a falha persistiu com o candidato de histórico desativado em memória.
  Detalhes no [relatório de 15/09](RELATORIO_COLETA_DEBUG_20260914.md).

### P04 — Playlist: contador do ADD diverge do resultado composto

- **Encontrado durante:** a mesma regressão de 15/09; relacionado a P03, mas
  **não há prova de raiz compartilhada**.
- **Comprovado em teste:** a playlist e a faixa passam pelas asserções anteriores;
  depois, `add_final` esperado como `1` vale `0`.
- **Não concluir:** que a faixa deixou de ser salva. A falha observada é no contador.
- **Próximo passo:** verificar se a instrumentação acompanha o executor real ou
  se há uma divergência de composição/fluxo. Não mudar a expectativa só para passar.
- **Fechar quando:** a cadeia materialização → ADD → receipt → contador tiver
  explicação causal e validação coerente.
- **Teste:** [test_red151_runtime_canonico_c3.py](../tests/test_red151_runtime_canonico_c3.py),
  `test_red151_c3_runtime_canonico_146_151_cria_salva_responde_sem_llm`.
- **Controle:** também persiste sem o candidato de histórico em memória.

### P05 — Presença na transição entre entrada aceita e turno criado

- **Estado em 25/09/2026:** resolvido na composição atual por
  `PrioridadeInteracaoUsuarioRuntime`: ouvido, coordenador e ponte compartilham
  o mesmo owner, e o diretor bloqueia presença enquanto há claim ativo.
  Os testes antigos omitiam esse owner na montagem manual; foram atualizados
  sem retirar as asserções de preempção. Os testes de composição real para STT
  e handoff também passaram na suíte completa (7.394 aprovados). Isso não é
  evidência de que o código histórico de 15/09 já tivesse o contrato.
- **Encontrado durante:** regressão de 15/09.
- **Comprovado em teste:** o evento de presença retorna `proposta_cognitiva`
  quando o teste espera `bloqueada`, depois da entrada aceita e antes do turno.
- **Contrato esperado:** a entrada já aceita do usuário deve ter prioridade
  nessa janela, não apenas depois da criação do plano.
- **Próximo passo:** mapear quem possui essa prioridade e sua propagação entre
  aceite da entrada, agendamento e diretor de presença; confirmar a composição real.
- **Fechar quando:** corrida controlada e runtime preservarem a prioridade sem
  silenciar definitivamente a iniciativa legítima.
- **Teste:** [test_red_p1h4_handoff_entrada_turno.py](../tests/test_red_p1h4_handoff_entrada_turno.py),
  `test_red_p1h4_entrada_aceita_preempta_presenca_antes_do_turno`.
- **Controle:** persiste sem o candidato de histórico em memória.

### P06 — Segmentação de nomes como `antonio.txt?`

- **Encontrado durante:** testes de pedidos modais e recusas, em 14/09.
- **Estado em 30/09:** RED reproduzido e corrigido no owner da fronteira entre
  atos; xfail retirado. Nomes, caminhos, URLs, números e aspas coerentes conservam
  pontuação interna, enquanto pontuação entre frases continua separando atos.
- **Prova no runtime:** `antonio.txt?` e `backup.tar.gz?` permaneceram recusas,
  sem comandos, com resposta observável. Nenhuma exclusão executada.
- **Compatibilidade:** replay integral dos dois lotes neurais preservou anotações
  e divergências; revisão exata sem alterar gold ou promover a rede.
- **Provas e limites:** [revisão P02/P06 de 30/09](../relatorio/RELATORIO_P02_P06_20260930.md).
- **Fechar quando:** nomes com extensão, caminhos, perguntas e frases compostas
  preservarem alvo e modalidade, sem regressão de segurança.
- **Evidência:** [registro de pedidos modais e xfails](RELATORIO_COLETA_DEBUG_20260914.md).

### P07 — Histórico sem publicação textual confirmada

- **Encontrado durante:** definição dos limites da correção C02, em 15/09.
- **Estado:** limite de cobertura, **não bug de áudio já reproduzido**.
  O novo registro usa confirmação dos canais textuais; aceite na fila de voz
  não prova que alguém ouviu a fala.
- **Próximo passo:** rastrear o caminho exclusivamente de áudio e o evento real
  de entrega, incluindo cancelamento, interrupção, fala tardia e troca de chat.
- **Fechar quando:** um contrato de entrega apropriado sustentar o histórico
  dessa rota sem registrar fala cancelada como entregue.
- **Evidência:** [limites da correção do histórico](RELATORIO_COLETA_DEBUG_20260914.md#histórico-de-respostas-locais-e-continuidade--15092026).

### P08 — Logs antigos podem conter credenciais

- **Encontrado durante:** sonda Chrome de 14/09.
- **Comprovado:** uma URL de callback com token foi impressa antes da sanitização.
  Não copiar seu conteúdo para este arquivo.
- **Já corrigido:** sanitização na saída do handler; ver C05.
- **Pendente:** os artefatos antigos não foram apagados nem higienizados; não
  compartilhar ou versionar logs brutos. A correção não foi uma auditoria global.
- **Próximo passo:** delimitar artefatos afetados e combinar com Pedro o tratamento
  de material sensível e eventual revogação da credencial, sem usá-la.
- **Fechar quando:** tratamento dos artefatos e da exposição estiver documentado;
  sanitizar logs novos, sozinho, não encerra esse item.
- **Evidência:** [achado de segurança e sanitização Chrome](RELATORIO_COLETA_DEBUG_20260914.md).

### P09 — Testes novos fora do versionamento

- **Verificado em 15/09:** `git check-ignore -v` aponta `.gitignore:10:tests/`
  para `test_historico_turnos_locais.py` e `test_recusas_alteracao_canonica.py`.
- **Impacto:** os arquivos existem e executam localmente, mas novos testes podem
  não entrar num commit normal. Isso não apaga os testes já rastreados.
- **Próximo passo:** revisar a política de ignore de testes separadamente, mantendo
  artefatos e dados sensíveis excluídos. Nenhuma regra foi alterada nesta organização.
- **Fechar quando:** regressões necessárias puderem ser versionadas com segurança,
  sem adicionar arquivos em massa nem expor dados de teste pessoais.
- **21/09, autorizado por Pedro:** removida a regra ampla `tests/`. Mantidos
  segredos, playlists, memória, resultados e caches ignorados; adicionados
  `*.caos-backup`, backups ocultos identificados, `/conversa.md` e diretórios
  de binários `runtime_llm/cpu/` e `runtime_llm/vulkan/`. Licença preservada.
  Retirada a exceção inoperante de terminal.log sob diretório ignorado.
  Doze contrastes `git check-ignore --no-index` provam código/exemplos visíveis
  e dados locais ignorados. Novos testes ficam visíveis, não adicionados ao Git.
- **Organização autorizada:** 21 roteiros apagados recuperados de HEAD em
  `scripts/roteiros/`; o caos restante foi movido da worktree, preservando seu
  conteúdo. Total 22. Alterações apagadas que não estavam no Git não são
  recuperáveis por esse procedimento. Loader aceita caminho legado da raiz
  somente quando ausente; arquivo explícito existente tem prioridade; caminho
  ausente fora da raiz não é substituído. Sonda usa o caminho novo; imports e
  caminho da fixture do caos ajustados, sem executar o caos.
  104 testes de organização/loader/fixture/P15 aprovados. Guia em
  `scripts/roteiros/README.md`. Outros analisadores/aplicadores apagados não
  foram restaurados fora do escopo de roteiros.
- **Limite do ignore:** continuam rastreados 306 arquivos em resultados,
  103 em runtime_llm, backup de playlists, conversa.md e três backups de código
  (estes últimos já removidos da worktree pelo usuário). Não houve `git rm`,
  staging, commit, exclusão de dados locais ou reescrita de histórico. Ignore
  não desversiona conteúdo existente; revisão do índice é trabalho separado.

### P10 — Citações confundidas com conteúdo que exige fundamentação

- **Última evidência registrada:** sonda de 13/09 tratou uma citação de estado
  emocional como obra; ainda estava aberta naquele relatório.
- **Estado atual:** requer revalidação após as mudanças posteriores nos guardiões.
  Não presumir que é a mesma raiz das recusas já corrigidas.
- **Próximo passo:** recuperar o turno e verificar a primeira classificação incorreta,
  contrastando citação, transformação textual e afirmação factual independente.
- **Fechar quando:** essas operações forem distinguidas sem liberar fatos inventados.
- **Evidência:** [limites das sondas de reparo parcial](RELATORIO_CORRECOES_CONVERSA_20260912.md).
- **Revalidação 15/09:** a resposta HTTP “Para pausar a música, basta dizer
  'pausa a música'” foi aceita na preparação, pesquisada como obra e cortada no
  verificador final. Captura `transporte_evidencia-20260915-184447-325549`;
  roteiro `roteiro_recusas_autoria-20260915-184448-437661`, turno 10.
- **Candidato C10:** extrator compartilhado distingue exemplos de enunciado de
  títulos candidatos. Validação factual continua examinando dados externos ao
  exemplo; uma citação didática não dispensa a verificação da frase inteira.
  A variante indireta “pedir para …, por exemplo” reutiliza o classificador
  canônico para reconhecer o exemplo, sem tratá-lo como fala autorizante.
- **Regressão detectada e corrigida durante validação:** retirar o título candidato
  também retirava o gatilho factual de uma data externa à citação. Separados
  `contem_citacao_destacada` e `extrair_titulos_citados`; o teste existente de
  metalinguagem/data voltou a passar sem alteração de expectativa.
- **Escopo:** citações didáticas explícitas, não toda citação emocional ou toda
  metalinguagem. O caso histórico original de 13/09 ainda requer revalidação.
- **Validação de 16/09:** 27 contrastes próprios; 42 aprovados com metalinguagem.
  Exemplos de pausa e retomada preservados na geração real e entrega ao chat da
  sonda `roteiro_explicacao_capacidades-20260916-084558-409596`.
- **Novo limite às 09:37:** “abrir o programa 'Calculadora'. Por exemplo:
  'abre a calculadora'.” retorna dois títulos no extrator; o runtime pesquisou
  Calculadora na Wikipédia e substituiu a explicação. Nome de entidade citado e
  exemplo em frase separada não são cobertos por C10. Não corrigido junto com C12.
- **C14, 19/09:** separados os papéis de exemplo de enunciado, referência
  operacional tipificada e obra candidata. Nome de recurso deixa de ser título,
  mas não tem datas/medidas mascaradas nem comprova estado. “Programa” requer
  moldura operacional para não liberar títulos de rádio/TV. Exemplo na frase
  seguinte exige orientação de pedido imediatamente anterior e leitura canônica
  do trecho como pedido/consulta; não libera qualquer citação após “por exemplo”.
- **Validação:** oito REDs causais → GREEN; 48 testes de citações ao final.
  Seleção ampliada: **2.801 aprovados, 14 xfails preexistentes, 30 subtests**.
  Replay da resposta histórica no processo real chegou inteiro ao chat;
  geração nova também preservou a instrução e manteve verificação de fatos
  adicionais. O caso emocional original de 13/09 não foi revalidado.
- **Novo limite em 20/09, durante C16:** a sonda
  `roteiro_explicacao_capacidades-20260920-085230-637670` voltou a pesquisar
  exemplos como títulos: “como em 'abre a calculadora'”, “pedir para mim:
  'ligue a lâmpada'”, “Exemplo: 'Laylay, desligue o ventilador'” e “Por exemplo:
  'Laylay, aumente o volume'”. A primeira frase da explicação da lâmpada foi
  apagada, restando apenas a condição de configuração. Captura HTTP:
  `transporte_evidencia-20260920-085228-787217`. Guardião não alterado em C16.
  Próxima fronteira: distinguir esses exemplos com contexto e vocativo, sem
  liberar títulos reais ou executar o texto citado; não ampliar listas de
  frases cegamente nem usar o placar mínimo como prova de resposta boa.
- **C17, 20/09:** 11 REDs reproduzidos antes do patch. A moldura de destinatário
  (“pedir para mim”), o conector de exemplo e a referência tipificada entre
  verbo e exemplo não eram preservados. Além disso, o exemplo citado precisava
  passar pelo classificador operacional; “aumente o volume” retorna natureza
  `nenhuma`. Reutilizado o reconhecedor canônico de vocativo, apenas sob moldura
  didática, sem alterar a gramática de execução ou conceder autorização.
- **Validação C17:** 68 testes de citação, incluindo três de integração com
  composição/estado/verificador reais e transporte de pesquisa observado;
  título real continua sendo pesquisado. Seleção ampliada: 2.849 aprovados,
  14 xfails anteriores e 30 subtestes. Dois replays no runtime completo (lâmpada
  e volume) preservaram os exemplos no chat, sem pesquisa de obra; demais
  chamadas ao Qwen tiveram geração nova. Ambas as sondas: 12 respostas e zero
  comandos. Plataforma/local é outra fronteira, não corrigida em C17.
- **F1, 21/09 — conteúdo citado de pedido:** o mesmo extrator não reconhecia
  a preposição em “pedir para 'tocar a música'”. A primeira fronteira RED era
  o papel da citação, antes da pesquisa e do corte factual. Treze REDs causais
  reproduzidos em música, aplicativos, IoT, agenda e verbos não executáveis.
  Corrigida somente a moldura compartilhada de `pedir/peça para/pra` seguida
  imediatamente do conteúdo citado; sem lista privada de ações ou autorização.
  “Pedir para tocar 'Noite Inventada'” continua candidato a título; fatos externos
  à citação continuam exigindo evidência. Não é liberação de qualquer aspas.
- **Validação F1:** 142 testes focados aprovados; seleção ampliada **3.002
  aprovados, 14 xfailed preexistentes e 30 subtestes aprovados**. Trecho
  instrucional histórico preservado inteiro no runtime:
  `roteiro_explicacao_capacidades-20260921-092057-398886`, turno 3;
  captura `transporte_evidencia-20260921-092056-114513`. É replay de recorte
  controlado, sem a negativa final de F2, não geração nova nesse turno.
  Doze respostas, zero comandos e 12/12 no avaliador mínimo. Sem pesquisa de
  títulos ou reparo nessa coleta. Qualidade global e equivalência operacional
  entre “tocar” e “retomar” não são provadas por preservar o enunciado.
  Caso emocional de 13/09 permanece pendente; ver mapa causal para limites.
- **F1 original, revalidação em 21/09 às 09:29:** localizado o turno 4 de
  `roteiro_reparo_parcial_conversa-20260913-073420-186234`. “Escutar o que você
  tá pensando — mesmo que seja só um 'estou triste' ou um 'cansado'” ainda era
  tratado como obra. Dez REDs reproduzidos; candidato no mesmo owner preserva
  exemplos de conteúdo discursivo, sem exceção para emoção ou título específico.
  Focado: **133 aprovados**. Ampliado: **3.017 aprovados, uma falha por roteiro
  ausente, 14 xfailed e 30 subtestes**. **Runtime pendente:** diversos roteiros
  foram removidos paralelamente durante a tarefa; a sonda não pôde carregar
  `roteiro_reparo_parcial_conversa.py`. Remoções preservadas, sem restauração.
  Não encerrar P10 antes da prova real; detalhes e artefatos no mapa causal.
- **Prova após reposição, 21/09 às 09:41:** sonda
  `transporte_evidencia-20260921-094144-781221`, roteiro
  `roteiro_reparo_parcial_conversa-20260921-094145-775708`. Replay integral da
  resposta histórica no turno 4: conteúdo preservado sem pesquisa de obra ou
  corte; terminal acrescentou ponto depois do emoji, conversa.md manteve original.
  Quatro respostas, zero comandos. Seleção ampliada **3.018 aprovados,
  14 xfailed e 30 subtestes**. P10 histórico validado nesse contrato, não toda F1.
  Processo retornou código 1 apesar dos relatórios completos e `atexit_concluido`;
  causa ainda não provada, sem falha nativa registrada. Não declarar encerramento
  limpo nem encobrir isso com o placar 4/4. Detalhes no mapa causal.

### P11 — Pedido de informação tratado como estado afirmado

- **Descoberto em:** 15/09, na validação real da preservação do catálogo (P01/C07).
- **Observado:** “me diga o nome da música ou o app que tá rodando, para eu te
  ajudar a localizar” foi marcado como `resultado_operacional_sem_evidencia`.
  O reparo também foi rejeitado e a resposta virou “Dá pra responder, mas agora
  seria no chute. Explica só um pouquinho melhor?”.
- **Primeira fronteira isolada:** o detector de resultados narrados em
  `cognicao/guardiao_alegacoes.py` trata o trecho subordinado “tá rodando” como
  afirmação independente. O pedido de informação não comprova um estado,
  mas também não deve ser interpretado como observação própria da Laylay.
- **Controles reproduzidos:** “me diga qual app está rodando” passa;
  “o app está rodando” continua corretamente bloqueado sem evidência.
  A formulação longa acima falha também chamando o detector diretamente,
  sem LLM, comandos propostos ou transporte. Não remover o guardião de estados.
- **Próximo passo:** RED contrastivo de escopo do pedido de informação; incluir
  orações coordenadas, afirmação posterior e efeitos realmente inventados.
  Reutilizar o contrato canônico de incerteza/pedido de informação.
- **Fechar quando:** perguntas e pedidos subordinados legítimos sobreviverem
  sem liberar alegações independentes; regressivos e runtime sem esse fallback.
- **Evidência:** [sonda e diagnóstico de 15/09](RELATORIO_COLETA_DEBUG_20260914.md#capacidades-relevantes-no-transporte--15092026).
- **Escopo:** registrado, não corrigido junto com C07. A qualidade da instrução
  sobre a capacidade continua em P01 e não será resolvida só liberando essa fala.
- **Atualização posterior — C08, 15/09:** corrigido o reconhecedor compartilhado
  para pedidos nominais (“me diga o app que…”), preservando nomes coordenados.
  O guardião delimita cada ocorrência pelo conjunto de estados/resultados já
  analisados; outra alegação não herda a permissão linguística do pedido anterior.
- **Validação:** 44 contrastes novos; seleção ampliada **918 passed**. A fala
  histórica completa passou pela preparação e verificação final sem reparo,
  tanto sem comandos como com a proposta de pausa original, que é descartada.
- **Prova da composição real:** replay explícito da resposta HTTP histórica
  no processo da Laylay entregou a fala integral sem reparo/fallback nem comando
  executado. O turno de replay **não é nova geração do Qwen**. A sonda separada
  com geração real passou 18/18, mas não repetiu a subordinada histórica.
- **Limites:** não é análise irrestrita de português nem liberação geral de
  orações coordenadas; ambiguidades continuam conservadoras. Preservar uma fala
  não certifica que sua orientação ou tom sejam bons (P01).
- **Detalhes:** [correção e validações de P11](RELATORIO_COLETA_DEBUG_20260914.md#pedido-de-informação-não-é-alegação-de-estado--p11--15092026).

### P12 — Perguntas de procedimento sem natureza reconhecida

- **Descoberto em:** testes contrastivos de C09, 15/09.
- **Reproduzido:** “como eu poderia aumentar o volume?” é `pergunta`, sem
  autorização, mas `natureza_acao=nenhuma`. “Me ensina como aumentar o volume”
  é conversa genérica. O catálogo recupera sistema, mas o contrato não tem uma
  interpretação procedural canônica para selecionar a tarefa específica.
- **Primeira fronteira:** classificação, antes da geração; nenhuma alteração
  em `modalidade_turno.py` foi feita nesta rodada.
- **Próximo passo:** estudar a moldura de explicação na classificação canônica,
  com pedidos reais, perguntas de estado, hipóteses e textos citados como controles.
  Não adicionar um parser privado de volume no preparador de prompt.
- **RED preservado:** `test_explicacao_capacidades_sem_execucao.py`, duas rotas.

- **Atualização C11, 16/09:** a moldura de procedimento seguida de infinitivo
  agora é reconhecida na proteção operacional compartilhada antes das listas
  de ações. Não adiciona verbos à autorização nem atesta capacidades. Hipóteses,
  negações e transformações conservam precedência. É uma gramática limitada,
  não um analisador irrestrito de português.
- **Prova:** 36 REDs novos na primeira fronteira → GREEN; 15 controles negativos
  e de comandos mantidos. Volume passou nas duas rotas de documentação. Seleção
  ampliada: **2.556 aprovados, duas falhas P13, 14 xfails preexistentes e 30
  subtests aprovados**. Não foi a suíte global.
- **Runtime:** turno 11 de `roteiro_explicacao_capacidades-20260916-085853-170785`
  reconheceu o procedimento e enviou documentação de sistema no HTTP real.
  A fala final ainda virou contingência após reparo rejeitado; P16 registra essa
  fronteira posterior. Corrigir a classificação não encerrou P01.

### P13 — Recuperação do catálogo perde domínio quando só há nome de app

- **Descoberto em:** testes contrastivos de C09, 15/09.
- **Reproduzido:** “como eu poderia abrir a calculadora?” já é instrução/explicação
  sem autorização, mas o seletor por termos não recupera sistema: “calculadora”
  não é “app/programa/janela” e a pergunta não contém comandos executáveis.
  “Como eu faria para abrir um programa?” serve de controle e passa.
- **Primeira fronteira:** recuperação do catálogo, não capacidade do executor.
- **Próximo passo:** reutilizar resolução de entidades/capacidades para consulta
  documental sem autorização; não cadastrar uma exceção para cada aplicativo.
- **RED preservado:** `test_explicacao_capacidades_sem_execucao.py`, duas rotas.

- **Atualização C12, 16/09:** o mapa consulta os aliases do `APPS_MAP` real por
  callback tardio, sem copiar a lista nem chamar executores. Referências completas
  selecionam sistema; não provam instalação, abertura ou disponibilidade.
  Ausência/falha da fonte mantém a recuperação anterior por termos.
- **Validação:** quatro REDs causais com a declaração/factory extraídas de
  `laylay.py` → GREEN; nove testes novos no total. As duas rotas de explicação
  usam essa composição, não um mapa isolado sem a dependência de aliases.
  Seleção ampliada: **2.567 aprovados, 14 xfails preexistentes e 30 subtests**.
- **Runtime:** captura `transporte_evidencia-20260916-093745-215501`, turno 4 de
  `roteiro_explicacao_capacidades-20260916-093746-337804`: documentação de sistema
  entregue no HTTP ao Qwen, que explicou como pedir a abertura. O verificador
  pesquisou “Calculadora” como título e substituiu a fala. Recuperação GREEN,
  fala final RED em P10; P01 continua parcial.
- **Limites:** recuperação lexical de aliases, não desambiguação universal nem
  descoberta de apps instalados. Disponibilidade e autorização não mudaram.

### P14 — Explicação prioritária IoT substitui ação e alvo

- **Descoberto em:** sonda real de explicações, 15/09, turnos 6 e 7.
- **Reproduzido:** perguntar como ligar a lâmpada ou desligar o ventilador recebe
  “É só me pedir diretamente para desligar a luz”. Nenhum comando foi executado.
- **Provado por código:** `ComandosImediatosRuntime` detecta a pergunta IoT e usa
  essa frase fixa antes da LLM. Não é uma invenção do Qwen nessa rota.
- **Próximo passo:** preservar o veto operacional e devolver a autoria da
  explicação ao contrato compartilhado, testando ligação/desligamento, alvos
  diferentes, indisponibilidade, recusa, hipótese e pedidos reais.
- **Não corrigido nesta rodada:** não remover a barreira IoT para silenciar o erro.
  O roteiro novo verifica também a inversão de ação/alvo, não só falta de comandos.
- **Atualização C13, 16/09 à noite:** mantida a mesma condição de veto, mas a
  porta prioritária retorna `False` para delegar a autoria à conversa. Não fala
  por cima do turno, não o marca como respondido e não alcança detectores ou
  executores subsequentes. Perguntas recebem documentação pelo caminho comum;
  recusas e hipóteses seguem com seu ato original, sem frase fixa sobre a luz.
- **RED/GREEN:** oito casos causais reproduzidos antes do patch; quatro controles
  de documentação/autoria já passavam. Depois, 12 aprovados, incluindo proposta
  operacional válida no JSON rejeitada pela autoridade do turno. O teste antigo
  que exigia a resposta fixa foi atualizado para o contrato de delegação; seu
  requisito de não alcançar o roteador foi preservado.
- **Runtime:** `roteiro_explicacao_capacidades-20260916-190855-889031` entregou
  explicações corretas de ligar a lâmpada/desligar o ventilador. Sonda adicional
  `roteiro_iot_explicacoes-20260916-191051-714954`: oito respostas, ações inversas,
  tomada, brilho, recusa e hipótese, zero comandos. Recusa: “Certo, não vou
  desligar o ventilador.” IoT simulado; não houve ensaio físico de dispositivos.
- **Limite restante em P01:** a LLM ainda pode explicar mal a confirmação,
  por exemplo “após o dispositivo ser refeito na configuração”, ou oferecer
  configuração sem uma capacidade comprovada. Não é o retorno da frase fixa;
  o placar automático da sonda não certifica esse conteúdo. Não alterados os
  guardiões, prompts, rede nem executores nesta correção.

### P15 — Falha técnica pede reformulação de uma pergunta clara

- **F3, 21/09 às 09:07:** recuperação vazia agora devolve fala e motivo
  separados; o cliente preserva nove razões canônicas de bloqueio em vez de
  convertê-las todas em OCUPADA. Nove REDs passaram; ampliado 2.974 aprovados,
  um RED F1, 14 xfailed e 30 subtestes. Controles posteriores: focado 108.
  Sonda concluída `transporte_evidencia-20260921-090740-395230`: replay + reparo
  vazio controlado atingiram limite de chamadas **real**, sem novo HTTP; fala
  informou limite sem pedir clareza. Doze respostas, zero comandos. Primeira
  tentativa de 20/09 interrompida após seis respostas, preservada como parcial.
  Limites: log intermediário ainda chama placeholder de reparo; sucesso da
  recuperação textual não foi reauditado amplamente. Demais categorias têm
  provas locais, não todas induzidas no runtime. Detalhes no mapa causal.
- **F3, 20/09 às 22:30:** categoria técnica chega à contingência no caminho
  principal e no reparo/autoria final, sem substituir conclusões locais válidas
  (social/observação confirmada). Quinze testes novos verdes; focado 122;
  ampliado 2.944 aprovados, um RED F1, 14 xfailed e 30 subtestes. Runtime real
  com timeout/conexão/ocupação **injetados** entregou as três causas sem pedir
  reformulação ou emitir comandos. Captura `transporte_evidencia-20260920-223000-712393`.
  Falhas em reparo/autoria ainda validadas localmente, não nessa sonda real.
  Permanecem na mesma raiz: saída vazia passando por recuperação perde motivo
  subsequente; orçamento ainda vira OCUPADA no cliente. Não inventar carga ou
  timeout a partir desse estado genérico. Detalhes no mapa causal. P15 parcial,
  não encerrado; origem física da latência segue fora desta correção.
- **Auditoria 20/09:** reprodução local com timeout, serviço indisponível e
  modelo ocupado confirmou pedidos indevidos de esclarecimento, sem comandos.
  A sentinela é reduzida a booleano; a chamada à contingência não transmite a
  categoria técnica. Primeira perda localizada nesse caminho. Origem da latência
  continua aberta; não confundir diagnóstico da conclusão com causa do timeout.
  Evidência e plano em [F3](MAPA_RAIZES_CONVERSA.md#f3-perda-de-categoria-de-falha).
- **Descoberto em:** sonda `roteiro_explicacao_capacidades-20260916-084208-340029`.
- **Observado:** timeouts de leitura nas duas primeiras chamadas (9 e 19 segundos)
  terminaram em contingências como “Faltou uma peça” e “Peguei o começo”, embora
  as perguntas de pausa fossem claras. Houve também timeout de preparação inicial.
- **Contrato necessário:** indisponibilidade técnica não é ambiguidade da entrada;
  a conclusão deve preservar a causa conhecida, sem atribuir o problema ao usuário.
- **Ainda aberto:** causa da latência e primeira perda da categoria de falha entre
  transporte e autoria da contingência. Carga ou inicialização são hipóteses, não
  causas comprovadas. A sonda posterior sem timeout não encerra esse defeito.
- **Próximo passo:** rastrear o motivo do erro até o fallback e criar contrastes de
  timeout, indisponibilidade e ambiguidade real. Nenhum prazo alterado nesta rodada.

### P16 — Reparo transforma pergunta de procedimento em relato passado

- **Descoberto em:** validação real de C11, turno 11 da sonda de 16/09 às 08:58.
- **Comprovado:** a entrada “como eu poderia aumentar o volume?” e o contrato
  `explicacao_capacidades` chegaram corretamente. A geração ensinou “ajusta o
  volume”, mas acrescentou uma condição sobre PC remoto. Após rejeição por
  `resultado_operacional_sem_evidencia`, o prompt de reparo afirmou “O usuário
  relatou um pedido” e permitiu perguntar “como foi”. O modelo terminou com
  “Como foi, dessa vez?”, foi rejeitado e houve contingência pedindo mais detalhes.
- **Dono localizado:** `qualidade_comunicacao.py`, seleção pelo indicador
  `resultado_operacional_desconhecido`. Esse indicador não prova o ato de relato.
- **Contrato necessário:** reparo deve preservar o ato e o objetivo do turno;
  desconhecer resultado não transforma pergunta em relato. O catálogo também
  não prova que uma rota remota é requisito para uma operação local.
- **Ainda aberto:** escopo exato da primeira rejeição e separação entre condição
  indevida gerada, falso positivo linguístico e reconstrução inadequada no reparo.
  Não remover o guardião para aceitar a fala. Nenhum patch dessa raiz nesta rodada.
- **Limite do avaliador:** marcou esse turno como aprovado e contou zero fallbacks,
  embora o terminal registre reparo rejeitado e contingência. Auditoria manual
  prevalece sobre esse placar mínimo; não usar 10/12 como qualidade aprovada.
- **C15, 19/09:** reproduzidos nove REDs locais antes do candidato, com um
  controle verde de relato explícito. Classificação e catálogo corretos antes
  do reparo falsificaram erro anterior como explicação dessa divergência. Além
  da premissa indevida no prompt, `_resumo_reparo` descartava a documentação.
  Agora o reparador mantém o objetivo/atos do contrato e recebe a documentação
  já selecionada quando a estratégia é `explicacao_capacidades`. Não resolve
  entidades novamente, não concede execução e não modifica o guardião.
- **Validação:** dez testes novos; 159 na seleção focada e 2.811 na ampliada,
  com 14 xfails preexistentes e 30 subtestes aprovados. Runtime completo:
  `roteiro_explicacao_capacidades-20260919-181949-614989`, captura
  `transporte_evidencia-20260919-181948-526867`. Replay somente do rascunho
  histórico de volume; reparo novo pelo `qwen3:4b-instruct` ensinou o pedido,
  sem “como foi” ou contingência. A frase adicional sobre remoto ainda foi
  removida pelo verificador: P01 permanece aberto. Houve também reparo novo
  de pergunta sobre aba, preservando o objetivo. Doze respostas, zero comandos;
  12/12 no avaliador mínimo não certifica a qualidade geral das explicações.

## Correções com validação registrada

“Validado no escopo” não significa ausência de outros defeitos naquela habilidade.
Datas e contagens abaixo descrevem cada rodada registrada, não uma suíte global.

| ID | Correção | Validação registrada | Limite restante |
| --- | --- | --- | --- |
| C01 | Recusas de alterar/mudar/ajustar reconhecidas pela base verbal canônica | 14/09: 41 testes focados; sonda de 18 turnos sem comandos | Não certifica toda interpretação de linguagem |
| C02 | Respostas locais publicadas entram no histórico do chat, com idempotência e compatibilidade com o emissor legado | 15/09: 17 testes novos, seleção de 103 aprovados e sonda final 18/18 | P07; conversa livre e demais writers não foram auditados integralmente |
| C03 | Realização de recusas e reconhecimento de perguntas não feitas sem falsos reparos em casos subordinados | 14/09: testes contrastivos e sondas reais sem contingência na rodada final | Não elimina toda invenção de estados |
| C04 | Orçamento do JSON estruturado separado do limite de fala curta; preservação do pacote fechado | 14/09: testes de geração/composição e sondas reais | Não garante universalmente JSON válido nem resolve qualidade sozinho |
| C05 | Sanitização de eventos/URLs Chrome antes da impressão, preservando dados dos handlers | 14/09: 27 testes com vizinhos e 2 subtests | P08; outros loggers não foram auditados globalmente |
| C06 | Reparo parcial preserva a resposta temática; verificador não apaga frases apenas por tamanho | 13/09: quatro turnos reais preservaram acolhimento e explicação | Preservar conteúdo não certifica sua correção factual; ver P02 |
| C07 | Catálogo vivo relevante acompanha a instrução do turno, sobrevivendo à compactação e retry | 15/09: 17 REDs → GREEN; seleção ampliada 451 passed; presença confirmada no HTTP real | P01 ainda parcial; P11 posteriormente tratado em C08; 18/18 sem execução não certificam qualidade da fala |
| C08 | Pedido nominal de informação não vira estado observado; escopo não vaza para outra alegação | 15/09: 44 contrastes; seleção ampliada 918 passed; replay histórico na composição real sem fallback | Sonda com Qwen real não repetiu a subordinada; tom e utilidade da explicação continuam em P01 |
| C09 | Autoria de explicações recebe documentação viva e tarefa textual, não planejamento genérico | Seleção conjunta: 1.307 aprovados / quatro REDs P12–P13; runtime: dez aprovações mínimas / duas falhas IoT | P01 não encerrado; cobertura, disponibilidade parcial e qualidade |
| C10 | Exemplo didático não é título pesquisável; fatos ao redor continuam exigindo evidência | 27 contrastes próprios; 42 aprovados com metalinguagem; exemplos preservados no chat real | P10 histórico mais amplo continua aberto |
| C11 | Moldura de procedimento reconhecida independentemente do vocabulário executável | 51 contrastes; seleção ampliada 2.556 aprovados / duas falhas P13; documentação de volume no HTTP real | Gramática limitada; P16 impede considerar a fala final corrigida |
| C12 | Catálogo documental consulta aliases dos aplicativos da composição | Nove testes novos; seleção ampliada 2.567 aprovados; documentação da calculadora no HTTP real | P10 corta a explicação gerada; referência não é instalação/estado |
| C13 | Veto IoT delega autoria sem substituir ação/alvo nem consumir o turno | 12 testes novos; 2.780 aprovados na seleção ampliada; duas sondas reais sem comandos, incluindo oito contrastes IoT | Não certifica hardware nem toda qualidade das explicações; P01 aberto |
| C14 | Papel da citação separa recurso, exemplo e obra; preserva contexto entre frases | 48 testes de citações; 2.801 aprovados na seleção ampliada; replay histórico no runtime e geração nova | Não prova existência/estado de recursos nem resolve toda citação ou P16 |
| C15 | Reparo preserva objetivo do turno e fonte da explicação | 10 testes novos; 2.811 aprovados na seleção ampliada; reparos novos de volume e aba no runtime | Requisitos indevidos sobre remoto ainda gerados; guardião permanece necessário |
| C16 | Limites documentados com escopo, condição e responsável | 9 testes novos; 2.829 aprovados na seleção ampliada; geração nova e HTTP real com controle local separado do remoto | Entrega final parcial: P10 ainda corta variantes didáticas; não certifica qualidade global |
| C17 | Papel de enunciado preservado com destinatário, referência intermediária e vocativo | 68 testes de citações; 2.849 aprovados na seleção ampliada; dois replays reais sem pesquisa indevida | Não amplia comandos executáveis; plataforma e qualidade geral continuam em P01 |
| C18 | Descrição de controle local usa documentação canônica do turno sem virar prova de fatos externos | 24 contrastes novos; 2.873 aprovados na seleção ampliada; frase histórica preservada no runtime | Família gramatical limitada; negativa indevida de controle de áudio continua em P01 |

Fontes: [rodadas de 14–15/09](RELATORIO_COLETA_DEBUG_20260914.md) e
[reparo parcial de 13/09](RELATORIO_CORRECOES_CONVERSA_20260912.md).

Na última seleção ampliada de C02: **605 passaram, 3 falharam e 8 subtests
passaram**. As falhas estão individualizadas em P03–P05; não foram escondidas
por uma declaração de suíte global verde.

## Ideias futuras — fora da fila de bugs

### I01 — Pesquisa em cinco sites/camadas

- Proposta do Pedro: extrair de cinco sites os pontos importantes para o pedido.
- **Somente guardada; não implementada nem ativada.** Não confundir com autorização
  para reconstruir a pesquisa durante uma correção de conversa.
- Registro original: [IDEIA_PESQUISA_CINCO_CAMADAS.md](IDEIA_PESQUISA_CINCO_CAMADAS.md).

## Modelo para o próximo achado

### P17 — Restrição de foco condicionada indevidamente ao modo jogo

- **Observado:** log do usuário às 10:49:51 registra avanço automático com
  `youtube_play`, `permitir_foco=False` e `target_tab_id` presente. Pedro relata
  que a troca ativa YouTube. Mesmo contrato ocorre no avanço manual.
- **Cadeia demonstrada:** callback real de `laylay.py` → registro do navegador
  → `NavegadorOperacoesRuntime` fornece a restrição → `chrome_comandos.py` só
  traduzia para `background=True` se jogo ativo → extensão ativa aba e janela
  quando `background` não está presente. Primeira divergência no transporte.
- **Falsificações:** alvo não estava ausente; `target_tab_id` chega ao transporte.
  Foco não é requisito do confirmador: `confirmYouTubeNavigation` lê/aciona o
  player pelo ID da aba, sem chamar ativação. Modo jogo é controle interno em
  que a restrição já funcionava. Não atribuído ao classificador ou à rede.
- **Contrato:** uma restrição explícita da operação sobrevive à tradução e
  não pode ser relaxada por contexto ou fallback. Owner: envio Chrome
  compartilhado. Aplicado a reprodução, busca e abertura de URLs; alias
  `entrar_no_site` normalizado antes da política. Foco autorizado e chamadas
  legadas sem restrição preservados. Sem extensão, operação protegida retorna
  falha em vez de abertura nativa que não garante preservação de foco.
- **Provas:** antes do candidato, **13 falhas causais e 7 controles verdes**.
  Após patch e três controles adicionais, seleção de navegador/playlist/jogo:
  **690 aprovados, 1 skipped, 9 subtestes**. Integração extrai o callback real
  de composição e usa registro, runtime e executor reais; somente a fronteira
  externa é simulada. Sucesso e falha mantêm receipt e alvo.
- **Escopo:** produção alterada somente em
  `mente_laylay/integracao/chrome_comandos.py`; teste novo
  `scripts/tests/test_chrome_preservacao_foco.py`. Extensão, playlist, rede e
  `laylay.py` não alterados. Nenhum commit ou treino pelo agente.
- **Limite:** Laylay aberta; não encerrada nem iniciada outra sessão. Ainda
  falta validar no Chrome real após reinício, com aba de estudos em foco,
  avanço manual/automático e observação do áudio/aba. Não declarar encerrada.
  A rota independente `chrome_navegacao.abrir_url_reutilizando_aba` possui
  fallback nativo sem guarda de `preservar_foco`; hipótese de outra ocorrência
  do mesmo contrato, não alterada nem certificada por estes testes.

- **Atualização após teste do Pedro, 21/09:** Pedro confirmou que a troca musical
  funcionou perfeitamente após o teste de foco/áudio. Evidência de uso real
  relatada pelo usuário, não uma nova captura feita pelo agente; não inferir
  cobertura de todos os modos a partir desse relato.
- **Complemento da mesma raiz:** demonstrado com dois REDs que o helper
  `abrir_url_reutilizando_aba`, chamado diretamente com `preservar_foco=True`
  e extensão desconectada, invocava o fallback nativo. A hipótese de falha
  inevitável na composição atual foi falsificada: `AmbienteNavegacaoRuntime`
  já injeta um callback protegido quando o modo jogo exige preservar foco.
  Portanto este complemento fortalece o contrato público, não comprova outro
  defeito da sessão do Pedro. Navegação normal fora do modo protegido permanece
  com a política anterior; não transformar todo pedido de abertura em background.
- **Patch e prova:** guarda mínima em `chrome_navegacao.py`, sem alterar o
  ambiente, rede ou extensão. Antes: **2 REDs e 28 controles aprovados**; depois:
  **56 aprovados e 2 subtestes** focados. Regressão ampliada: **697 aprovados,
  1 skipped, 9 subtestes**, 10,48 s. Protege URLs comuns e YouTube; sucesso/falha
  do fallback sem restrição e composição real do ambiente mantidos. Não houve
  desconexão da extensão ou abertura real de abas nesta etapa.
- **Trabalho paralelo:** estado Git conferido antes do patch e após os testes;
  sem diff visível em `mente_laylay/neural`, `laylay.py` ou `pyproject.toml` no
  momento das checagens. Nenhum conflito observado; não é auditoria de mudanças
  futuras, modelos ignorados pelo Git ou outra worktree. Arquivos do cliente
  e relato original preservados, nenhum commit criado.

### PXX — Título curto

- **Descoberto em / durante:** data e correção que estava em andamento.
- **Estado e impacto:** suspeita, reprodução, parcial etc.; consequência para Pedro.
- **Observado versus esperado:** exemplo mínimo, sem dados sensíveis.
- **Primeira fronteira / dono:** se conhecidos; não preencher com hipótese como fato.
- **Evidência e hipóteses falsificadas:** teste, artefato ou relatório; nível de prova.
- **Próximo passo:** menor investigação ou correção que falta.
- **Fechar quando:** contrato e validação necessários, incluindo runtime quando aplicável.
- **Atualizações:** data, alteração, resultado e limites; preservar o histórico.

## Atualizações do índice

- **15/09/2026:** criado por solicitação do Pedro; reunidos dez itens pendentes,
  seis correções com escopo validado e uma ideia futura. Somente documentação;
  nenhuma mudança de produção, treino, ativação neural, teste de runtime ou commit.
- **15/09/2026, continuação:** investigado P01; registrada C07 com prova do
  transporte. P11 separado após aparecer na sonda. Não houve treino/promoção
  neural nem mudança de autorização, executores ou guardiões nesta etapa.
- **15/09/2026, P11:** C08 altera somente a distinção/escopo linguístico nos
  validadores compartilhados. Rede, autorização, executores e personalidade
  preservados. A próxima frente permanece P01, agora sem o falso reparo histórico.
- **16/09/2026:** C09/C10 aplicados e validados com os limites acima. P12–P15
  separados; quatro REDs preservados, sem xfail. Rede e executores não alterados,
  nenhum treino, promoção ou commit criado. Próxima fronteira: P12, depois P13/P14.
- **16/09/2026, C11:** classificação P12 validada no escopo; produção alterada
  somente em `modalidade_turno.py`, preservando os patches anteriores. P16
  registrado sem desviar para outra correção. P13/P14 continuam pendentes;
  rede, catálogo, prompt, guardião, reparador e executores não alterados nesta etapa.
- **16/09/2026, C12:** alterados somente o mapa e sua injeção em `laylay.py`.
  P13 validado na recuperação; P10 reapareceu com nome de programa citado e
  exemplo em frase separada. Próxima frente planejada: P14; P10/P16 abertos.
- **16/09/2026, C13:** somente `comandos_imediatos.py` alterado em produção,
  preservando patches anteriores. P14 validado no escopo com geração real;
  nenhuma ação física, promoção neural ou commit. P01/P10/P16 continuam abertos.
- **19/09/2026, C14:** somente `fundamentacao_factual.py` alterado em produção;
  preservadas alterações anteriores. Citação histórica da calculadora validada.
  Próxima frente: P16, reparo preservando o ato e o objetivo da pergunta.
- **19/09/2026, C15:** produção alterada somente em `qualidade_comunicacao.py`
  e `validacao_contrato_fala.py`. Classificador, catálogo, guardiões, executores
  e rede preservados. Nenhum commit, treino ou promoção. Próxima fronteira:
  limites por capacidade/rota em P01; não ampliar automaticamente a correção.
- **19–20/09/2026, C16:** alterados catálogo `capacidades.py`, projeção no
  `mapa_habilidades.py` e instrução de autoria em `fala_capacidades.py`.
  Na retomada, o HEAD já era `c8b4c26f31deabd21168a458273896f398e2ddf0`,
  com o candidato de produção incorporado externamente; nada foi reaplicado
  ou revertido. Testes novos continuam ignorados pelo Git (P09). Nenhum commit
  criado pelo agente, promoção neural ou efeito físico. Guardiões preservados.
- **20/09/2026, C17:** produção alterada somente em `fundamentacao_factual.py`;
  regressões acrescentadas ao arquivo de testes existente. Execução, catálogo,
  reparador e rede preservados. A sessão do usuário não foi encerrada pelo
  agente; sondas iniciadas após Pedro fechar a Laylay. Nenhum commit criado.
- **20/09/2026, C18:** produção alterada somente em `fundamentacao_factual.py`
  e `plano_turno.py`, preservando C17. Fonte documental restrita ao contrato
  explicativo do mesmo turno; nenhum relaxamento de autorização ou receipt.
  Sonda concluída e ausência de processos Python conferida. Nenhum commit,
  treino ou promoção neural. Novo teste permanece ignorado pelo Git (P09).

### RPV17-01 — Recusa verbal sem causa da ocorrência atual

- **Descoberto em:** P17 do roadmap de personalidade, 04/10/2026. Este ID não é
  o P17 histórico de preservação de foco do Chrome.
- **Observado versus esperado:** após falhas repetidas do sistema, a autoria
  operacional instruía a Laylay a recusar retrabalho e brincar com uma suposta
  repetição do pedido pelo usuário. A fala deve preservar a falha do executor e
  dirigir qualquer irritação apenas à causa comprovada. A não execução por
  estado já satisfeito exige receipt confirmado; uma bronca sobre repetição
  atribuída ao usuário exige, além disso, evento de redundância do mesmo
  receipt com confiança suficiente.
- **Primeira fronteira / dono:** `confirmacao_llm.py`, na construção e validação
  da fala após `ResultadoAcao`. O roteador não veta por emoção e o avaliador
  separa responsabilidades; ambos foram controles para falsificar essas raízes.
- **RED e candidato:** três REDs causais e três controles antes do patch. A
  autoria passou a confrontar evento e receipt por ocorrência e alvo, retirar
  convite de recusa nas falhas e rejeitar recusa explícita contraditória. RED
  adicional mostrou uma instrução genérica de brincar com repetição mesmo na
  falha; essa instrução foi condicionada à redundância confirmada.
- **Prova e limite:** testes focados de app e IoT redundantes, app e arquivo com
  falha, evento de outra ocorrência e resultado incerto; composição pelo
  `laylay.py` com receipts controlados e componentes reais. Não há validação
  de efeito externo físico nem amostra do modelo real para esta correção.
- **Estado:** candidato parcial da P17. A resistência opcional limitada está
  em RPV17-04 e o guarda textual explícito em RPV17-03; ainda falta ampliar
  ações auditadas e linguagem pessoal. Não declarar P17 encerrada.

### RPV17-02 — Termo curto contamina seleção de capacidade

- **Descoberto em:** pergunta natural sobre recusar retrabalho redundante na
  P17 do roadmap de personalidade, 04/10/2026.
- **Observado versus esperado:** `aba` era encontrada dentro de `retrabalho`,
  selecionando navegador antes de personalidade. Uma pergunta sobre trabalho
  também recebia resposta de navegador; a pergunta real sobre aba deve
  continuar encontrando essa capacidade.
- **Primeira fronteira / dono:** três leitores de `_TERMOS_DOMINIO` em
  `mapa_habilidades.py` usavam correspondências diferentes. O catálogo, não o
  avaliador emocional, é dono da seleção documental.
- **RED e candidato:** dois REDs de pergunta natural e controles de aba;
  correspondência única de palavra inteira para termos alfanuméricos de até
  três caracteres, preservando os radicais longos. A suíte ampla revelou dois
  REDs derivados: `apps` deixou de casar com `app`. Alias explícito `apps`
  restaurou a pergunta natural e o texto variado sem recolocar `aba` dentro
  de `retrabalho`; controles afetados passaram 70/70.
- **Estado:** GREEN focado e regressão relevante; sem alteração de autorização,
  executor ou disponibilidade real de navegador.

### RPV17-03 — Ataque pessoal passava na fala operacional

- **Descoberto em:** proteção da linguagem de bronca da P17, 04/10/2026.
- **Observado versus esperado:** saídas com resultado factual correto mais
  insultos diretos (`seu idiota`, `você é incapaz`, ataque à aparência ou ao
  valor pessoal) recebiam aprovação do verificador. A bronca pode descrever o
  comportamento observado, jamais atacar atributos da pessoa.
- **Primeira fronteira / dono:** `confirmacao_llm.py`, validação da fala antes
  de expor texto à voz. O prompt já orientava evitar ofensas; isso não era
  garantia de rejeição da saída.
- **RED e candidato:** quatro REDs falharam pelo contrato certo após corrigir
  a frase factual do teste para o status `ja_aberto_focado`. Guarda localizada
  rejeita as construções de ataque direto, sem bloquear confirmação factual.
  Uma prova com geração e reparo ofensivos cai na fala local, sem publicar
  insulto como fala final.
- **Estado:** GREEN focado e regressão relevante de 265 testes aprovada. Essa
  guarda de construções explícitas não certifica toda linguagem social possível
  nem substitui avaliação de fala real. A suíte global 9.439/1 skipped/56
  subtestes passou antes deste último guarda; não foi repetida depois dele.
- **Ampliação do mesmo contrato, 04/10:** quatro REDs novos mostraram que
  depreciação direta do valor, aparência, inteligência e aceitação social da
  pessoa ainda passava como fala válida, mesmo com o receipt correto. A guarda
  de saída operacional passou a reconhecer essas construções; a geração e o
  reparo ofensivos caem na fala local. Controles factuais permanecem verdes:
  196 testes de regressão relevante, incluindo a composição instalada e
  controles de APP_OPEN e IOT_CONTROL. É cobertura explícita, não certificação
  semântica de todas as possíveis ofensas.
  Sonda sem executor nem fala física chamou o modelo local: a primeira coleta
  expirou em 8 s; outra coleta pediu 15 s, mas o orçamento rápido a limitou
  a 8 s por chamada e recebeu respostas. A validação as rejeitou e entregou
  a fala local. Outra coleta isolada mostrou
  pergunta acrescentada na primeira redação e detalhes não comprovados sobre
  “4 vezes” no reparo. Isso comprova o fallback dessa coleta, não uma fala
  gerada válida em sessão.
- **Ampliação conversacional da mesma raiz, 04/10:** o ataque explícito
  `Você é um fracasso.` atravessava `criar_fala_autoral` e
  `avaliar_qualidade_comunicacao` após um reparo da resposta principal. A
  primeira fronteira RED era a validação da fala candidata; a avaliação
  posterior também a aprovava. Cinco REDs reproduziram o problema, incluindo
  o caminho composto de `preparar_resposta_para_execucao`. A hipótese de que
  a avaliação posterior barraria a ofensa foi falsificada; uma crítica ao
  comportamento permaneceu aceita. A detecção explícita agora tem um único
  contrato em `guarda_ataque_pessoal.py`, consultado pela confirmação
  operacional, autoria conversacional e avaliação de qualidade. Uma prova
  adicional mostrou reparo seguro quando o ataque vem da resposta principal.
  Um controle vizinho revelou falso bloqueio de ofensa citada e criticada;
  a guarda agora distingue essa menção de ataque isolado, endossado ou
  acrescentado fora da citação. Regressão relevante: 292 testes aprovados;
  suíte completa após o ajuste: 9.506 aprovados, 1 ignorado e 56 subtestes.
  Esta cobertura não prova toda linguagem ofensiva possível nem áudio físico
  em sessão.
- **Ampliação da mesma raiz, 05/10:** intensificadores (`muito idiota`,
  `completamente incapaz`), a construção `uma pessoa inútil` e `fracassado`
  atravessavam autoria, qualidade e preparação final. A exceção de citação
  crítica também permitia endosso posterior (`mas também é verdade`), e a
  negação `Não acho que você é um fracasso` era bloqueada por engano.
  Nove REDs e cinco controles localizaram a divergência no detector
  compartilhado, falsificando rejeição posterior e erro de tamanho/formato.
  O candidato trata essas construções no mesmo owner, conserva crítica ao ato
  e negação local, e invalida o endosso explícito da citação. Quatorze controles
  novos ficaram verdes; 154 regressivos de autoria, operação e qualidade
  passaram. São construções explícitas, sem certificação semântica universal.

### RPV17-04 — Resistência opcional sem continuidade canônica

- **Descoberto em:** P17 do roadmap de personalidade, 04/10/2026.
- **Observado versus esperado:** o roteador executava imediatamente um controle
  de mídia que o usuário chamava de opcional mesmo após causa emocional válida;
  uma tentativa de adiar pelo roteador deixava o `sim` sem consumo no caminho
  real, pois a composição filtrava a pendência compartilhada. A reação precisa
  de decisão causal tipada, fala observável, prazo e confirmação por pendência.
- **Primeira fronteira / dono:** `roteador_intencao.py` para a decisão antes do
  executor; `composicao_entrada_interacao.py` para transportar o runtime de
  pendência à entrada prioritária. A porta booleana antiga foi falsificada
  como solução: trataria o turno sem fala nem receipt. O executor de mídia não
  decide se a personalidade adia uma ação.
- **RED e candidato:** RED de execução imediata com controles de urgência,
  acessibilidade, causa do sistema e evento vencido; após o primeiro GREEN, a
  composição real mostrou `sim` não consumido. A política admite apenas
  `MEDIA_CONTROL/repeat_toggle` com o verbo natural `alterna`, opção explícita,
  autorização e evidência ativa. O roteador cria pendência sanitizada de 90 s;
  a entrada prioritária consome a resposta antes da repetição canônica e usa
  o executor normal após aceite. Recusa, falha e novo comando direto encerram
  a pendência; comando independente respeita o ciclo de vida marcado nela.
  RED adicional mostrou segundo toggle possível quando `sim` já estava em
  processamento; conclusão condicional por status impede a substituição em
  corrida e o segundo comando recebe uma fala sem novo despacho. Comando de
  outro domínio continua pelo fluxo normal mesmo com aceite em processamento.
- **Prova e limite:** testes focados cobrem autorização, exceções protegidas,
  mesma causa, evento vencido, aceite, recusa, veto, falha do executor e troca
  de domínio. Subprocesso importa `laylay.py` e exercita composição e estado
  compartilhado, com efeito de mídia substituído por despacho controlado.
  Não há comprovação de mídia física nem fala audível neste piloto. A P17 e a
  classificação de outras ações seguem abertas. A regressão ampla passou com
  9.462 aprovados, 1 ignorado e 56 subtestes antes da última guarda focada:
  menção sem autorização não consome a pendência.
- **Fechamento da porta antiga:** um RED de `APP_OPEN` com callback legado
  retornando `True` confirmou `tratado=True` sem fala, receipt ou chamada a
  executor. A composição já fornecia uma função inerte, falsificando um veto
  ativo no caminho instalado; o teste de despacho normal falsificou falha geral
  do roteador. A porta foi removida do roteador e do contexto instalado. O
  callback antigo, mesmo injetado por outro consumidor, não encerra o turno.
  A resistência tipada permanece como único owner da decisão de adiamento e
  só consome quando criou pendência e publicou a pergunta. Prova de composição
  confirmou ausência da porta no contexto montado; sem efeito físico de mídia.
  Suíte completa após a remoção: 9.482 aprovados, 1 ignorado e 56 subtestes.
- **Transporte da mesma continuidade, 05/10:** o roteador resolvia PC B ou
  ambos e podia receber `platform=music`, mas a pendência guardava apenas
  intent e ação. No aceite, a retomada reconstruía só `repeat_toggle` a
  partir de `sim`; o resolvedor real escolhia PC A e o executor podia trocar
  o player musical por uma porta global. O teste composto falsificou destino
  padrão equivalente e recuperação do texto original. Nove REDs e um
  controle verde localizaram a perda na serialização e no consumo da
  pendência. A projeção estrita preserva o destino já resolvido e parâmetros
  auditados de ação/player; a mesma validação é usada no aceite. Campos
  não auditados não entram no adiamento, e uma pendência ausente ou inválida
  encerra com fala sem despacho. Autoridade, evento bruto e ID antigo não
  são reutilizados como parâmetros; o despacho normal cria a nova ocorrência.
  Composição instalada cobriu PC A, PC B e ambos com `platform=music`, usando
  pendência e contexto reais e fronteira externa controlada. Não há prova de
  efeito físico remoto ou áudio neste incremento.
- **Identidade e concorrência da mesma continuidade, 05/10:** a substituição
  da oferta ainda comparava só intent/ação; seis REDs mostraram que um novo
  controle para outro destino ou player encerrava uma oferta independente.
  O contrato agora compara ação, destino resolvido e rota de player. Apenas
  a mesma identidade substitui uma oferta ainda ativa ou recebe a proteção
  de aceite em processamento; outro pedido segue seu fluxo sem apagá-la.
  Os aliases musicais auditados usam a mesma rota real e a ausência de
  seletor continua distinta. Dois REDs adicionais localizaram a corrida
  entre observar a oferta A e resolver uma oferta B: a confirmação podia
  consumir B e despachar os parâmetros antigos de A. O runtime canônico
  recebeu `id_esperado`, conferido antes de classificadores ou alterações;
  seu controle transacional também preserva uma troca durante a classificação.
  O consumidor valida o registro devolvido e comunica a troca sem consumir
  ou despachar qualquer oferta. A prova canônica inclui B de outro domínio,
  protegendo um contrato compartilhado, com comportamento anterior preservado
  para consumidores que não informam o ID. Dois REDs próximos mostraram que
  um comando independente podia ser consumido nessa corrida; o gate local
  canônico de confirmação agora o deixa seguir antes do resolver. Resultado
  final focado e vizinhos: 107 aprovados, incluindo 67 da P17 e 10 de pendência
  canônica. Revisão independente: 16 controles verdes, sem novo achado
  acionável. Efeito de mídia e áudio físico continuam sem prova.
- **Base e ambiente da regressão, 05/10:** HEAD
  `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch `main`, worktree suja
  preservada. A primeira suíte completa deu 9.544 aprovados, 15 falhas,
  1 ignorado e 56 subtestes. Todas as falhas ocorreram no import de
  `laylay.py:43`, antes dos contratos testados: uma sessão real aberta ocupava
  o mutex do projeto. Esta é a colisão de ambiente já registrada, não uma nova
  raiz de personalidade. Os mesmos 15 testes passaram com root importado sob
  mutex Windows real de identidade exclusiva e SQLite temporário; as APIs
  originais foram restauradas antes do pytest. A sessão aberta foi preservada
  e a proteção de instância única continua sendo testada pela API original.
  Antecipar o import do root para esse isolamento produziu quatro falhas
  diferentes, com 9.555 aprovados: o bootstrap instala `builtins.print`, cujo
  filtro elimina logs `[CTX]` e linhas vazias, e carrega a variável específica
  do modelo antes da fixture de configuração. Isso alterava duas capturas
  Chrome, o prompt do console e o modelo esperado no teste. É o efeito de
  bootstrap/ordem já registrado; não foi tratado como regressão da P17.
  O launcher seguinte delega ao loader original e isola mutex/SQLite somente
  no primeiro import solicitado pelos próprios testes, restaurando as APIs
  no `finally`. Os quatro controles voltaram a passar com produção idêntica.
  A suíte completa final nesse isolamento, mantendo a ordem de importação,
  terminou com **9.559 aprovados, 1 ignorado e 56 subtestes aprovados**, em
  331,62 s. A regressão não produziu efeitos externos de mídia nem voz física.
- **Escopo incremental de produção, 05/10:**
  `personalidade/guarda_ataque_pessoal.py`,
  `personalidade/politica_resistencia.py`,
  `autonomia/roteador_intencao.py`, `autonomia/comandos_imediatos.py`,
  `memoria_mental/pendencia_acao.py`, `autonomia/controle_midia.py` e
  `personalidade/falas_variadas.py`. Testes e documentação preservam os IDs
  de RPV17-03/04; a divergência entre efeito e fala ficou em RPV17-07.

### RPV17-05 — Pedido de alternância morria na classificação de modalidade

- **Descoberto em:** prova completa de composição da resistência P17,
  04/10/2026; causa separada da decisão e continuidade de RPV17-04.
- **Observado versus esperado:** o detector instalado devolvia
  `MEDIA_CONTROL/repeat_toggle` para “alterna a repetição. É opcional.”, mas
  `turno_atual` ficava `modalidade=conversa` e `autoriza_execucao=False`.
  A pendência nunca nascia. Um pedido diretivo claro deve chegar ao roteador
  sem que uma pergunta ou hipótese ganhe autoridade.
- **Primeira fronteira / dono:** `gramatica_musical.py`, que prova a diretiva
  musical antes do guardião de modalidade. A frase sem “É opcional” também
  falhava, falsificando a anotação como causa única. O detector de intent já
  funcionava; alterar o roteador não consertaria esta fronteira anterior.
- **RED e candidato:** dois REDs de comando direto e um RED na composição,
  seguidos por quatro REDs de necessidade, segurança e acessibilidade.
  Controles de pergunta, negação, hipótese, relato e retirada da ordem verdes.
  Regra estreita para alternar repetição com qualificadores auditados; não há
  promoção genérica de verbos a autorização.
- **Prova e limite:** composição real inicia o planejamento, passa pela
  entrada prioritária, cria a pendência na mente compartilhada e consome
  `sim` pelo executor controlado. Regressão de modalidade e mídia posterior:
  245 aprovados e 22 subtestes. A suíte ampla de 9.462 testes passou antes
  desta mudança e não foi repetida depois. Efeito físico de mídia permanece
  sem prova neste incremento.

### RPV17-06 — Contagem emocional exposta à autora sem contrato numérico

- **Descoberto em:** sonda com o modelo local para a autoria operacional da
  P17, 04/10/2026.
- **Observado versus esperado:** uma resposta gerada referiu “4 vezes” após
  receber `repeticoes=4` no contexto causal, mas a validação numérica só admite
  números presentes no receipt e na fala factual. A fala caiu no fallback;
  o modelo não deve receber número que a própria fronteira de publicação
  considera sem prova para dizer ao usuário.
- **Primeira fronteira / dono:** `confirmacao_llm.py`, na projeção do evento
  emocional para o prompt. O avaliador continua dono da contagem usada para
  decidir o arco; o executor continua dono do efeito. Um timeout inicial de
  8 s e a pergunta gerada são problemas observados separados, não a causa da
  contradição numérica. A mesma sonda mostrou que o modelo respondeu quando
  houve tempo e que a guarda rejeitou a fala inadequada, falsificando uma
  publicação ofensiva ou um executor inexistente como explicação.
- **RED e candidato:** teste de contrato mostrou `repeticoes`, `confianca`,
  `nivel` e `provocacao_usuario` numéricos na projeção entregue à autora;
  o modelo simulado que usava a contagem retornava ao fallback. A projeção
  agora mantém autoria, emoção e arco, traduz o nível para intensidade textual
  e omite os números que não pertencem ao receipt da fala. O RED ficou GREEN.
- **Prova e limite:** 196 testes relevantes passaram, incluindo app, IoT e
  composição instalada. A coleta posterior com modelo local expirou no
  transporte rápido, entregando fallback; ela não confirma melhora da fala
  gerada nem áudio físico. A suíte completa terminou com 9.496 aprovados,
  1 ignorado e 56 subtestes. P17 permanece aberta.
- **Auditoria posterior do timeout:** a classe `rapida` limita cada chamada a
  8 s mesmo quando a autora solicita 15 s; o cliente aplica o menor prazo.
  Esta proteção de latência não foi alterada. Em composição instalada, um
  timeout simulado preservou a fala factual, a emoção causal `brava` nível 3
  e uma entrega por ocorrência. O modelo local estava descarregado e o
  Just Cause 3 aparecia como processo gráfico na checagem posterior; nenhuma
  nova fala gerada foi tomada
  como prova. Controle focado de orçamento, reação e composição: 46 aprovados.
- **Coleta local, 05/10:** `qwen3:4b-instruct` respondeu pelo cliente e
  orçamento instalados, com receipts sintéticos e SQLite isolado, sem executor
  ou áudio. Em APP_OPEN, a primeira redação levou 4,505 s e foi rejeitada;
  o reparo levou 1,134 s e foi aceito. Em CREATE_FILE, a redação levou 3,741 s
  e foi aceita pelo verificador. O limite rápido de 8 s permaneceu ativo.
  Isso comprova transporte e aceitação textual nessa coleta. A fala de falha
  incluiu `o sistema não quer nem tentar`, cuja adequação causal e social
  continua em avaliação; a amostra não encerra qualidade de linguagem nem
  sessão real. Artefato: `resultados_testes/p17_autoria_real_20261005.json`.

### RPV17-07 — Confirmação troca alternância de repetição por reinício

- **Descoberto em:** auditoria do caminho de mídia da P17, 05/10/2026.
- **Observado versus esperado:** o executor enviava `repeat_toggle` e
  confirmava `midia_repeat_toggle`, mas a fala dizia `Voltei pro começo da
  música` ou `Recomeçando essa aí`. A resposta deve descrever a alternância
  confirmada, sem alegar reinício ou estado ligado/desligado não observado.
- **Primeira fronteira / dono:** projeção da ação na chave de confirmação em
  `controle_midia.py`; o catálogo compartilhado `falas_variadas.py` é dono da
  redação local para cada chave. O código transformava `repeat_toggle` em
  `replay` antes da composição da fala.
- **Falsificações:** a asserção de envio e o receipt estavam verdes, descartando
  execução da ação errada como causa desse RED. O caminho não usava modelo,
  descartando autoria da LLM. `replay` preservava sua fala correta de reinício
  como controle interno.
- **RED e candidato:** dois REDs com diretivas naturais falharam na fala depois
  das asserções de envio, receipt e entrega única. A chave canônica agora
  permanece `repeat_toggle` e possui variações próprias no catálogo de fala.
  O controle de `replay` continua verde; regressão de mídia e autoria
  operacional: 88 aprovados. A prova usa fronteira externa controlada,
  sem execução no player ou áudio físico. É uma raiz diferente do transporte
  da pendência RPV17-04: preservação da identidade do efeito na resposta.

### RPV17-08 — Autoria transforma alternância em estado final não evidenciado

- **Descoberto em:** coleta real finita P17, 05/10/2026; artefato
  `resultados_testes/p17_real_20261005_223753`, turno 11.
- **Observado versus esperado:** o player passou de repetição ligada para
  desligada, com receipt Chrome `repeatEnabled=false`, mas a LLM publicou
  `A repetição da música foi ativada. Tá na hora de escutar de novo, sem parar!`.
  O contrato recebido pela autora confirma somente `midia_repeat_toggle`;
  essa confirmação não prova uma direção de estado.
- **Primeira fronteira / owner:** validação da proposta em `confirmacao_llm.py`.
  É distinta da antiga projeção local `repeat_toggle → replay` de RPV17-07:
  o catálogo já dizia alternância e `usada_llm=True` confirma a outra autora.
- **Falsificações:** executor errado e player antigo descartados pelo mesmo
  requestId/tab/vídeo, receipt da extensão e observação posterior ao efeito.
  A recusa não despachou, o aceite despachou uma vez e a restauração ocorreu.
- **RED / candidato:** quatro variantes passavam pelo verificador, incluindo
  o texto real. A guarda compartilhada rejeita direção ligada/desligada ou
  ativada/desativada para esse contrato de toggle; o prompt explicita a
  distinção. Autoria e reparo inválidos preservam a fala segura de alternância.
  Controle de alternância correta preservado; 95 testes relevantes verdes.
- **Estado:** GREEN focado; nova coleta real do candidato pendente. A sonda
  ganhou validação factual da fala de mídia para não declarar GREEN só pelo
  efeito correto. Nenhum novo domínio promovido ou orçamento ampliado.

### Coleta finita de P17 — evidências e limites, 05/10/2026

- `p17_real_20261005_203950`: interrompida no primeiro turno por premissa da
  sonda que confundia ID semântico da fala com ID de telemetria; TTS tinha
  sucesso. Corrigida somente a correlação da observação.
- `p17_real_20261005_204129`: cinco turnos; a bronca `brava/3` do turno 4 teve
  receipt próprio, autoria aprovada, resposta HTTP real, uma chamada de
  1,169 s dentro de 8 s e TTS do trace correto. O quinto turno usou fallback
  seguro; a exigência inicial de autoria em um número fixo foi inadequada
  quando a preparação já era redundante. `prova_autoria.json` conserva a prova.
- `p17_real_20261005_204431`: fallback no nível 3; não é nova prova positiva.
- `p17_real_20261005_223753`: 11 turnos concluídos; efeitos/recusa/continuidade/
  restauração comprovados, mas **não é GREEN global**. Avaliador canônico
  encontrou dois REDs de publicação do adiamento (mesma RPV17-04) e a fala
  final revelou RPV17-08. O veredito inicial da sonda descreve somente política
  e foi insuficiente para a correção inteira. Não apagar esses REDs ou reduzir
  as expectativas para obter 11/11. Áudio físico ainda depende de observação
  humana. O computador não foi desligado.

**Candidato de publicação de RPV17-04, 05/10, após a coleta.** A primeira
fronteira vermelha foi reproduzida antes da alteração: seis falhas e dois
controles verdes. O roteador publica `aguardando_confirmacao` com owner
`politica`, ocorrência original e evidência da pendência antes da pergunta.
Se a publicação recusar ou falhar, cancela somente a oferta criada e conserva
a autorização original para o fluxo normal. O registrador compartilhado
mantém contexto/plano e exclui esse adiamento dos consumidores de efeito,
sem fabricar falha de habilidade ou concluir correção por execução ausente.
O controle de grafia `Executor` reproduziu um RED adicional, corrigido pela
normalização do owner; receipts reais de falha continuam observados.
Produção alterada nesta fronteira: `roteador_intencao.py` e
`adaptadores_aplicacao_runtime.py`. Nove testes próprios, composição instalada
e vizinhos: **261 aprovados**. Autoria, mídia, resistência e sonda:
**203 aprovados** em outra seleção com sobreposição; não somar as contagens.
A suíte completa de 9.559 é anterior a estes candidatos.

**Coleta do candidato `p17_real_20261005_225131`.** Interrompida no segundo
turno: os dois receipts confirmaram `app_focado`, sem redundância
`ja_aberto_focado`. A causa exigida não estava presente porque a Calculadora
não foi lida em foco nos controles. Não foi provado se houve troca de janela
ou divergência entre callback de foco e releitura; essa fronteira é distinta
da política emocional. Isso não valida nem invalida o adiamento ou sua
fala; a mídia não foi alterada. Não reduzir a expectativa de redundância.
P17 permanece com prova real do candidato pendente; condições de foco foram
solicitadas ao usuário. A preparação independente da P18 pode prosseguir.

### RPV18-01 — Feedback da emissão confirmada não alcança aprendizado comum

- **Base congelada:** HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`,
  `main`, worktree suja preservada. Diagnóstico iniciado em 05/10/2026;
  fechamento dos regressivos deste candidato em 06/10/2026. A autorização
  posterior de Pedro permitiu implementar este primeiro contrato da P18;
  a coleta restante de P17 não foi promovida nem reaberta.
- **Observado / esperado:** uma presença entregue recebe aceitação ou recusa,
  o coordenador e a rede processam esse feedback, mas a tabela do aprendizado
  comum permanece vazia. Esperado: uma evidência contextual por ocorrência
  confirmada, com origem, domínio, alvo, tipo e vínculo à entrega.
- **Primeira fronteira / owner:** `PonteIniciativaAplicacaoRuntime` estava
  ligada ao motor de iniciativa, porteiro, coordenador e rede, sem porta para
  `MotorAprendizadoRuntime`. O diretor é dono da emissão e do seu feedback;
  o motor e SQLite compartilhados são donos da evidência e sua persistência.
- **Falsificações:** o motor real gravou no mesmo SQLite temporário; a fila
  real da rede foi drenada sem erro e ainda assim não alimentou o motor.
  Falha de entrega não criou emissão feedbackável. RED inicial reproduzido:
  **2 falhas causais, 2 controles aprovados**.
- **Candidato:** conexão tardia pelo adaptador de feedback já existente.
  Diretor transporta proveniência do receipt de entrega e instante do feedback;
  ponte confere os dados contra a ocorrência real. Aceitação, recusa, correção
  e silêncio qualificado chegam ao serviço canônico. Silêncio conserva a
  janela de 600 segundos; fila/agendamento não confirmam entrega.
- **Identidade:** `id_evento` opcional no armazenamento canônico, migração
  aditiva e índice único. A transação valida contrato e proveniência antes de
  confirmar duplicata. Concorrência e recriação do motor não aumentam o peso
  da mesma ocorrência; outra identidade continua acumulando evidência.
  Domínios distintos não fundem hipóteses do mesmo alvo. Chamadas legadas sem
  ID preservam a acumulação anterior. Dois REDs da revisão mostraram duplicata
  com fonte/entrega incompatível; a guarda foi corrigida sem promover contexto
  momentâneo a identidade da ocorrência.
- **Corrida demonstrada:** depois de classificar o feedback de A, a entrega B
  podia substituir `ultima_emissao` antes da ponte. A validação descartava A
  apesar de entregue; o RED canônico reproduziu zero evidências. O histórico
  existente agora conserva feedback e diagnóstico por ID; a ponte resolve
  essa ocorrência. A evidência de A chega ao motor sem alterar B ou transferir
  seu feedback. Consulta ambígua ou ocorrência ausente continua fail-closed.
- **Diagnóstico / consciência:** distingue feedback observado de persistência
  confirmada; falha/ausência do motor não anunciam aprendizado. Catálogo vivo,
  perguntas naturais e recuperação contextual descrevem somente este contrato
  e seus limites. Conteúdo pessoal da fala, erros e caminhos não são expostos
  no diagnóstico. Não foi criado outro motor, parser de confirmação ou banco.
- **Provas finais:** **182 aprovados** na seleção de presença, entrega,
  composição, aprendizado, maturidade, nove pilares, catálogo e diagnóstico.
  Inclui import do root instalado em subprocesso com mutex exclusivo e
  SQLite/resumo/pessoas próprios, observador realmente instalado em
  `RespostaIARuntime`, adaptador/motor reais e três evidências persistidas
  (aceitação, correção e silêncio). Autoridade permanece falsa e nenhuma
  evidência isolada vira preferência explícita. `git diff --check` limpo.
- **Escopo de produção:** diretor, ponte, injeção de quatro linhas no root,
  motor/SQLite compartilhados, mapa de habilidades, diagnóstico e formatação.
  Outras alterações da worktree não pertencem automaticamente a esta raiz.
  Nenhum commit, push ou desligamento efetuado.
- **Limites:** o receipt de entrega foi controlado nas provas de composição;
  não houve nova sessão com TTS/áudio físico nesta etapa. Falha de persistência
  fica diagnosticada, mas não possui retry automático do feedback consumido.
  Inicialização concorrente de banco novo pode falhar no PRAGMA WAL, também
  reproduzida no HEAD; não é regressão demonstrada deste candidato e permanece
  separada. P18 inteira continua aberta: integração emocional de produtores,
  compositor local no jogo e validação de sessão ainda não estão concluídos.

### RPV18-02 — Tipo explícito de feedback reduzido a silêncio pelo booleano

- **Raiz distinta:** `registrar_feedback_contextual` verificava `aceito=None`
  antes de verificar os tipos explícitos `correcao` e `repeticao`. Isso atribuía
  sinal -0,10 a uma correção/repetição tipada, embora a mesma regra canônica
  aplique -0,35 quando o tipo é alcançado. É precedência na ponderação do motor,
  não omissão de transporte de RPV18-01.
- **RED / candidato:** dois REDs com motor/SQLite reais reproduziram -0,10.
  A precedência do tipo explícito foi restaurada; silêncio permanece fraco,
  com -0,10, e não há promoção a preferência confirmada. Variantes legadas e
  aceitação/recusa preservadas na seleção final de 182 testes. Não representa
  implementação da calibração de tolerância futura da P20.

### RPV18-03 — Modelo visual padrão retirado pelo provedor

- **Base congelada:** `90a2fb8698541119f523c0a22fa4de0187cbaf92`, `main`,
  worktree com alterações paralelas preservadas. A composição externa estava
  sem diff antes deste candidato. Pedro autorizou abrir o Just Cause 3 para
  investigar a ausência de reações; nenhuma alteração específica pelo nome do jogo.
- **Primeira fronteira RED real:** coleta finita
  `resultados_testes/p18_jogo_real_20261006_113804`: sessão de jogo ativa,
  credencial disponível e duas chamadas visuais reais. Ambas retornaram
  HTTP 404 / `model_not_found` para `qwen/qwen3.6-27b`, antes do Diretor e da voz.
  Essa versão da sonda não registrava separadamente o retorno da captura;
  observações adicionadas depois não são atribuídas retroativamente à coleta.
- **Falsificações:** reconhecimento do executável, ativação da sessão e
  observador desligado não explicam o RED. O catálogo real da mesma credencial
  respondeu HTTP 200, confirmou `qwen/qwen3.8-27b` e não listou 3.6. Nenhuma
  configuração explícita de modelo estava presente. A documentação oficial
  da Groq informa retirada do 3.6 em 14/09/2026 e sucessor 3.8:
  <https://console.groq.com/docs/deprecations> e
  <https://console.groq.com/docs/vision>. Repetir o mesmo ID não resolveria 404.
- **Contrato / owner:** `ComposicaoInteligenciaExternaRuntime` fornece um
  padrão comum disponível às rotas visuais; configuração explícita conserva
  precedência. O erro do serviço continua impedindo análise e sucesso falsos.
- **RED / candidato:** quatro falhas canônicas na seleção padrão ausente/vazia
  das duas rotas; dois controles de override passaram. Constante única
  `MODELO_VISUAL_GROQ_PADRAO` atualizada para 3.8 e `.env.example` alinhado.
  Nenhum catálogo dinâmico, fallback, retry, orçamento ou transporte novo.
  **28 regressivos aprovados** de composição externa, Groq, conversa remota e
  composição visual. A coleta seguinte recebeu análise multimodal real válida.
- **Princípio compartilhado:** configuração comum compatível com o provedor
  beneficia visão geral e jogo. Não mascarar indisponibilidade com uma fala de
  sucesso e não confundir presença habilitada com serviço externo disponível.

### RPV18-04 — Reação de presença no jogo exigia segunda autoria de modelo

- **Lacuna P18 demonstrada por código:** após a visão e a decisão cognitiva,
  `RespostaEventoRuntime` ainda preparava prompt e chamava o modelo para jogo.
  É distinta do HTTP 404 antecedente de RPV18-03.
- **Contrato / owner:** cognição decide evento e direção social; compositor
  local materializa uma reação breve e variável; o mesmo porteiro, fila e
  callback confirmam a entrega. Cotidiano conserva autoria LLM. Nenhum
  compositor concede autoridade, despacha comandos ou confirma efeitos.
- **RED / candidato:** oito falhas e quatro controles verdes antes do
  candidato; primeira asserção encontrou uma chamada de modelo no jogo.
  `compositor_evento_local.py` reutiliza variação/higiene compartilhadas e o
  contrato já decidido. `RespostaEventoRuntime` usa esse caminho antes do
  prompt no domínio jogo. Ausência de material, sombra e recusa do porteiro
  preservam ausência de emissão confirmada. Testes legados que exigiam LLM no
  jogo foram adaptados à mudança explícita de contrato, mantendo os controles
  de autoridade, prioridade e receipt.
- **Composição / sessão:** regressão com root instalado comprovou uma fila,
  zero prompt/modelo e callback preservado. Coleta real
  `p18_jogo_real_20261006_114237` recebeu uma análise visual, materializou
  localmente uma proposta e confirmou uma entrega, sem chamada de autoria.
  O conteúdo revelou RPV18-05; esse receipt não encerrou a qualidade da fala.
- **Consciência:** catálogo e pergunta específica consultam `GAME_VISION` no
  snapshot real, informam dependência de visão/credencial/presença e reação
  local. Visão parcial ou personalidade disponível não mascaram a ausência
  desse intent. **49 controles de catálogo aprovados**, após nove REDs e três
  controles já verdes. Isso não prova publicação emocional causal ou prosódia.

### RPV18-05 — Motivo comunicativo rotulado como evidência observada

- **Primeira fronteira reproduzida:** o Coordenador visual acrescentava
  `motivo` à lista de evidências antes dos fatos. O Diretor e o contrato
  materializavam essa mistura. Na sessão `114237`, a fala entregue foi
  `Olha só. Na tela: "Comentário de companhia sobre a paisagem visualmente marcante."`.
  Era uma explicação interna da proposta, não um detalhe da cena.
- **Contrato / owners:** motivo permanece metadado; fatos explícitos
  atravessam produtor, Diretor e contrato como fatos. Seleção de material
  precede apresentação. O compositor não remove palavras para tentar
  adivinhar o papel semântico e não reutiliza a fala livre sugerida pela visão.
- **RED / candidato:** três REDs canônicos; cenário visual reproduzido e
  controle em outro domínio (janela) protegem o contrato compartilhado.
  Coordenador separa motivo; Diretor preserva seus campos; contrato produz
  âncora factual separada. Motivo sem fatos permanece sem fala; descrição
  factual legada sem motivo separado continua válida.
- **Prova de sessão:** coleta finita de 120 segundos
  `resultados_testes/p18_jogo_real_20261006_114837` confirmou análise visual
  válida, fato `ROCCA BLAU`, uma materialização local, uma entrega confirmada
  por ID e zero chamadas de autoria. Capturas registradas somente por
  tamanho/hash; imagens não foram persistidas pela sonda.
- **Revisão final:** controle longo revelou truncamento anterior à guarda do
  compositor. Três REDs adicionais e 19 controles verdes precederam a correção.
  Parser visual, Diretor e contrato conservam a fonte inteira; a propriedade
  `ancora_factual_completa` atravessa a normalização curta do roteiro. O
  compositor recusa uma oração longa inteira, sem cortar palavras ou inventar
  conclusão. Rótulos iniciais conhecidos do protocolo são removidos apenas
  da apresentação; a fonte permanece íntegra. Imperativos/primeira pessoa
  continuam citados e sem autoridade. Esses ajustes posteriores à coleta
  têm prova focada própria, sem atribuir à sessão uma versão que não executou.
- **Regressão consolidada:** **313 aprovados** em 18,07 s na seleção de
  compositor, composição instalada, transporte factual, visão, presença,
  prioridade, receipts, feedback, aprendizado, catálogo e diagnóstico.
  `regressivos_finais.xml` e `resumo_prova.json` ficam na pasta da coleta final.
  Seleções anteriores com sobreposição não são somadas a esse resultado.
- **Limites preservados:** audição física depende da observação de Pedro;
  callback de entrega comprova o caminho de software. Publicação emocional
  causal dos produtores e P18 inteira continuam abertas. Nenhuma etapa voltou
  à P16; nenhum commit, push ou desligamento foi executado nesta investigação.

### RPV18-01 — Continuação: identidade do feedback em avisos e no turno principal

- **Base:** `main`, HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`,
  worktree paralela preservada, 06/10/2026. Esta continuação mantém o ID da
  raiz de transporte/proveniência; não conta cada frase como outro problema.
- **Primeiras divergências:** repetição não era classificada pelo observador;
  citação/metalinguagem podia contar como aceitação; o receipt da central não
  fornecia ocorrência ao mesmo owner de feedback. A observação normal do turno
  ainda podia contar novamente uma correção já vinculada à entrega.
- **REDs e controles:** os primeiros contratos válidos tiveram 12 REDs e dois
  controles verdes. Um RED posterior comprovou dupla contagem entre presença
  e conversa genérica. Outros controles demonstraram colisão da identidade
  de entregas após os sete dias de deduplicação e consumo de feedback por uma
  entrada que o próprio runtime descartava como obsoleta.
- **Falsificações:** motor e SQLite reais registram repetição com sinal -0,35;
  a ingestão aceitou o segundo lote antes da colisão; callbacks falhos não
  criaram emissão; IDs/textos de outra entrada não suprimem aprendizado.
  A primeira divergência não era indisponibilidade geral do armazenamento.
- **Contrato/owners:** o interpretador compartilhado classifica feedback sem
  consumir o pedido; Diretor conserva entrega e feedback; ponte valida
  proveniência; adaptador vincula a observação ao ID e hash da entrada; motor
  conserva uma evidência. Avisos passam pelo mesmo receipt/owner e recebem
  identidade da ocorrência de ingestão, além das referências de fonte.
- **Composição instalada:** root importado em processo com SQLite, resumo,
  pessoas e central próprios. A central entregou um aviso por callback
  controlado; `RespostaIARuntime.processar` recebeu a correção e percorreu
  intérprete, plano, validador e registro de conversa instalados. Uma chamada
  principal de modelo controlada, zero comandos autorizados, uma evidência
  nova e uma causa neutra correspondente. Agendador/porteiro/voz instalados
  mantiveram um aviso adiado e uma única fala principal consolidada.
- **Consciência/limites:** catálogo e perguntas naturais incluem repetição e
  avisos recebidos pelas integrações, sem prometer captura de notificações do
  Windows. Silêncio requer entrega e 600 segundos; fila legada não confirma
  anúncio. Repetição chega ao motor comum; calibração da rede/tolerância da
  P20 não foi antecipada. A composição não certifica audição física.

### RPV18-06 — Produtores sociais e observações sem ocorrência emocional canônica

- **Lacuna demonstrada:** direção social de eventos era usada como tom sem
  publicar a mesma causa em turno/plano/quadro/episódio; prioridade de aviso
  atribuía irritação sem causa; feedback aprendido não aparecia no contrato
  emocional. São pontos do contrato de integração causal, sem transformar
  evidência de aprendizado em uma nova seleção emocional.
- **Contrato/owners:** cognição decide a direção uma vez; factory causal adapta
  essa decisão; transação compartilha a ocorrência em todos os consumidores
  elegíveis. Confiança, tempo, origem e autoridade continuam sendo guardas.
  Presença não pode substituir uma utterance concorrente. O consumidor
  revalida a causa depois da autoria e antes de enviar à fila.
- **Notificações:** prioridade conserva transporte/porteiro de segurança;
  evento registra somente recebimento do lote, intensidade zero e expressão
  desabilitada. Não atribui culpa nem altera plano de comando em andamento.
- **Feedback:** após validar tipo, entrega, fonte e janela, ponte publica
  `feedback:<id_entrega>:<tipo>` no quadro compartilhado. Os cinco tipos são
  neutros; silêncio mantém natureza inferencial. Publicação independe de
  sucesso do SQLite, sem afirmar aprendizado quando a persistência falha.
  Nenhuma fala, autorização, episódio expressivo ou preferência é criada.
- **RED/candidato:** 20 controles novos de eventos incluem a expiração durante
  autoria, fonte/autoridade incompatíveis e composição instalada em jogo,
  rotina e janela. Feedback teve sete REDs causais e 12 controles já verdes
  antes do candidato; seus 24 controles finais protegem janela, receipt,
  proveniência, replay, concorrência e composição extraída do root.
- **Identidade canônica:** publisher possui modo opcional `ocorrencia_unica`.
  Guarda transacional recusa fonte diferente com a mesma referência; replay
  válido continua idempotente e não torna causa antiga atual. O RED de replay
  foi reproduzido antes dessa guarda. O histórico efêmero existente é usado,
  sem outro estado privado de deduplicação ou nova chamada de modelo.
- **Princípio reutilizável:** contexto/tom não substituem uma causa validada;
  autoridade e confirmação de efeito continuam nos owners próprios. Provas
  de composição usam saída/modelo controlados; áudio físico permanece separado.

### RPV18-07 — Candidato tardio alterava uma fala já em reprodução

- **Primeira fronteira RED:** worker real marcou `em_reproducao=True`; uma
  chamada tardia de `falar` para a mesma chave ainda retornava True e mudava
  texto/emoção do pedido pendente. O controle anterior ao início continuava
  consolidando uma única fila. Não é a futura diferença visual de intensidade.
- **Contrato/owner:** `VozRuntime` permite substituir o candidato antes da
  reprodução e congela texto/emoção da entrega ao iniciá-la. A guarda ocorre
  sob o mesmo lock antes de retirar itens proativos, evitando sua perda.
- **RED/GREEN:** um RED do worker e um controle legítimo precederam o candidato.
  Ambos passaram depois; regressivos de filas independentes, callbacks e
  composição instalada preservam prioridade do usuário e avisos adiados.
- **Princípio compartilhado:** uma entrega possui um conteúdo consolidado;
  um novo candidato não muda retroativamente o que está sendo entregue.
  A saída de áudio deste controle é substituída; não certifica som físico.

### P18 — Consolidação dos candidatos de integração, 06/10/2026

- **Seleção final:** 609 aprovados em 27,11 s; arquivo
  `resultados_testes/p18_fechamento_20261006/regressivos_finais.xml`.
  Inclui 24 controles de feedback causal e os três controles históricos
  adequados ao novo contrato, além dos caminhos reais instalados no root.
- **Regressão ampla preservada:** 9.738 aprovados, três falhas de expectativas
  antigas, um skip e 56 subtestes aprovados, em 281,28 s. O XML original está
  preservado como `regressao_completa.xml`; não foi reclassificado como verde.
- **Primeiras guardas desses três REDs:** envelope manual sem direção/causa
  não aceita `animada/2`; fixture P2 sem IDs não fornece identidade e seu
  relógio 1000 estava expirado no relógio canônico; fixture P4 exigia uma fala
  livre da LLM no contexto em que P18 agora usa materialização local.
  P1-C mantém o input livre e exige tom neutro; P2 conserva `alegre/2` com
  IDs/relógio coerentes e causa vigente; P4 exige o detalhe factual local,
  direção causal e zero chamadas à LLM. Autoridade, descarte, receipt e
  número de emissões continuam verificados. Produção não mudou nesse ajuste.
- **Estado:** contratos de software e composição da P18 concluídos;
  audição física, sincronização perceptível e ativação final permanecem nas
  entregas próprias de P19/P21. O snapshot de fontes distingue esta versão
  da coleta real anterior. Nenhuma preferência inferida foi promovida e
  nenhuma alteração paralela da worktree foi descartada.

### RPV19-01 — Retrato da fala era reatribuído ao episódio corrente no visual

- **Base congelada:** HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`,
  branch `main`, worktree compartilhada preservada. Estado e hashes anteriores
  em `p19_expressao_20261006/baseline.json`.
- **Primeira RED:** texto, fila e parâmetros TTS conservaram `irritada/1`,
  enquanto o getter visual instalado devolveu `alegre/2` ou `calma/1` após
  troca/expiração. Sete REDs e 11 controles GREEN antes do candidato.
- **Falsificações:** seleção anterior à fila correta; setter não sobrescrevia
  causa B; divergência antecedia assets/aliases. O controle inicialmente
  surpreendente usava relógio capturado antes da porta controlada; somente a
  porta do teste foi corrigida para alcançar a fronteira desejada.
- **Contrato/owners:** orquestrador congela `RetratoEntregaFala` antes da
  publicação; lote proativo publica o mesmo ID e objeto entregue à fila.
  Voz publica uma projeção transitória durante preparação/reprodução; setter
  compartilha somente apresentação; política visual a consome nesse período.
  Ao terminar/interromper/falhar, retorna ao episódio vivo. Snapshot não
  renova causa, não autoriza efeito e fica fora da memória durável.
- **Controles adicionais:** troca no observador textual antes da fila,
  expiração antes/depois da publicação, proatividade, silêncio, interrupção,
  fallback e falha de preparação. Esta última revelou publicação anterior
  ao `try`; setup agora está no mesmo `finally` de limpeza. Leitor preserva
  rótulos aceitos pelo owner causal, inclusive `feliz`/`animada`; dois REDs
  de round-trip impediram uma segunda taxonomia no transporte.
- **Princípio compartilhado:** cada entrega conserva sua identidade e
  expressão; contexto posterior não muda retroativamente o que foi publicado.
  Contrato serve a conversas, comandos e proatividade pelo canal comum.

### RPV19-02 — Intensidade chegava ao renderer, mas não ao efeito visual

- **Primeira RED:** nativo recebeu .333 e 1.0, porém desenhou o mesmo movimento
  e tamanho; aura ainda pulsava com movimento desativado. C# `Animate` também
  ignorava intensidade da fala e mantinha aura/transição em movimento zero.
  Seis REDs e dois controles de transporte precederam o candidato visual.
- **Falsificações:** nível/intensidade já eram transportados corretamente;
  mesmo asset `brava` para `irritada` era o fallback legítimo, não a raiz.
  Quantização antes da ponderação explicava a igualdade residual de movimento.
- **Contrato/owners:** consumidores renderizam o retrato recebido sem escolher
  causa ou emoção. Intensidade pondera deslocamento antes do único round e
  escala estática 97% a 100%; preferências de movimento fixam corpo/aura/fade.
  Valores inválidos fecham em movimento zero. Transição pendente leva emoção
  e intensidade juntas, protegida por outro RED antes de corrigir a composição.
- **Produção:** `cliente/avatar_laylay.py`, `avatar_runtime.py` e
  `cliente/gamebar_laylay/LaylayWidget.xaml.cs`. PIL real, Canvas de captura
  e corpo C# compilado protegem consumo local; build UWP passou sem pacote,
  assinatura, certificado ou instalação. Pixels instalados não foram provados.
- **Princípio compartilhado:** transporte de estado não prova efeito no
  consumidor; preferência de movimento não apaga a informação estática.

### RPV19-03 — Aceitação da fila era usada como confirmação de entrega

- **Primeira RED:** falha no setup já limpava retrato, mas callback de itens
  mesclados ainda recebia True e registrava fala emitida. Falha total do TTS
  e interrupção também concluíam como sucesso. Essas conclusões são outra
  raiz, distinta da identidade emocional e da intensidade visual.
- **Contrato/owner:** reprodução devolve bool confirmado; worker escreve
  `entregue`, conclui callbacks e registra fala emitida só com esse resultado.
  `wait=True` devolve receipt, inclusive ao substituir candidato antes da
  reprodução. Aceitar sem espera continua sendo somente aceitação de fila.
- **REDs próximos:** substituição com espera retornava True antes de receipt
  negativo; fallback local usava espera que ignorava barge-in. Ambos foram
  reproduzidos antes dos respectivos candidatos. Voz neural e fallback agora
  usam a mesma espera cancelável; interrupção não confirma fala completa.
- **Provas:** sucesso, fallback confirmado, falha total, setup, interrupção,
  fallback interrompido e flush proativo com sucesso/falha em composição root.
  Proativas mescladas não entram como feedback entregue sem áudio confirmado.
- **Princípio compartilhado:** término de espera e remoção de fila não são
  receipt de efeito; cada habilidade usa a confirmação do executor de voz.

### RPV19-04 — Resposta de capacidade ignorava indisponibilidade do alvo afirmado

- **Primeira RED:** pergunta sobre avatar e intensidade alcançava domínio
  avatar indisponível + personalidade disponível; guarda geral `any` aceitava
  a pergunta e o ramo afirmava “Tenho um avatar”. Não confundir com F1, que
  trata negação falsa de capacidade na proposta da LLM.
- **Contrato/owner:** catálogo consulta disponibilidade do domínio sobre o
  qual afirma acesso. Ramo de avatar respeita estado operacional vivo; a
  descrição contextual informa a expressão por entrega sem autorizar ação.
- **Provas:** RED antes do candidato, controles positivos/negativos e root
  instalado com preferência do overlay desativada. Outros domínios e os
  limites de edição/receipts conservaram as regressões existentes.
- **Escopo:** correção aplicada no ramo demonstrado do catálogo compartilhado;
  não declarar auditoria global dos demais ramos por essa prova.

### P19 — Prova e próxima fronteira, 06/10/2026

- Seleção final: **855 aprovados em 37,35 s**, incluindo os 44 controles da
  composição instalada P19. XML final preservado; não somar execuções anteriores.
- Artefatos RED, seleção relevante final, build e hashes em
  `resultados_testes/p19_expressao_20261006`.
- Coleta real finita `p19_real_20261006`: 42,028 s, dois receipts `tts_total=True`,
  89 amostras de A/1 durante causa B/3 e 82 amostras da segunda entrega B/3.
  Sete critérios de software passaram; zero modelo; retrato liberado ao final.
- A ferramenta computer-use não expôs janela do overlay, embora o processo
  próprio tenha iniciado. Pergunta humana sobre som e aparência permanece
  pendente. Game Bar somente compilada/testada, sem atualizar pacote instalado.
- Fonte física e fonte final possuem hashes distintos: espera de substituição,
  cancelamento do fallback e catálogo foram ajustados depois da coleta e
  testados no caminho de software. Nenhuma confirmação física foi presumida.
- Próxima fronteira é aferição perceptível de P19. Sem reabrir P16, executar
  outras ações ou alargar modelo, memória ou autonomia. Nenhum commit criado;
  push autorizado continua reservado ao encerramento combinado com Pedro.

### RPV20-01 — Preferência explícita perdia escopo e efeito nos comandos

- **Primeira RED:** `pega leve hoje nos comandos` não produzia preferência;
  a postura operacional retornava antes de consultar o pedido válido.
- **Contrato/owners:** `preferencia_humor` interpreta a instrução social;
  decisão canônica fornece o contexto do turno; `perfil_amizade` consome a
  preferência sem decidir autorização. Jogo, conversa, comandos e geral têm
  escopos explícitos.
- **Provas/falsificações:** RED explícito antes do candidato, variantes
  naturais e controles de citação, contexto vizinho, vulnerabilidade e
  correção. A ausência de efeito não era ausência do serviço: o mecanismo
  explícito já existia no HEAD. Mais humor não libera execução ou provocação
  sem causa; tom leve bloqueia tirada sem perder o objetivo operacional.

### RPV20-02 — Precedência e cache durável discordavam da preferência atual

- **Primeira RED:** loader devolvia escopo específico antigo antes de comparar
  sua data com a preferência geral mais recente; turno com cache preenchido
  não relia evidência durável. Confiança textual inválida lançava exceção e
  infinita podia ser aceita.
- **Contrato/owners:** o motor compartilhado reidrata evidência explícita
  comprovada; seletor único compara pedidos válidos pela data; o orquestrador
  incorpora candidato durável mais recente sem apagar preferência temporária.
- **Provas/falsificações:** composição instalada reproduziu restart,
  atualização externa ao cache e precedência. SQLite gravou os dois escopos:
  falha de gravação não explicava a ordem errada. Cache removido ainda
  reproduzia a escolha antiga: não era apenas estado obsoleto. Leitura
  indisponível conserva pedido válido; dado expirado/corrompido não é promovido.
- **Limite:** isto reidrata pedidos explícitos com proveniência; não implementa
  inferência de personalidade ou tolerância por feedback genérico.

### RPV20-03 — Produtores ornamentavam antes de consumir a preferência

- **Primeira RED:** contexto da execução/adapter não transportava preferência;
  autores e geradores locais acrescentavam estilo apesar de tom leve válido.
  O diretor final preserva texto operacional, portanto não desfazia uma
  ornamentação que já fora produzida.
- **Contrato/owner:** seletor canônico oferece uma política única de supressão
  antes da autoria/variação. Consumidores passam a mesma preferência a
  planejador, confirmação, reação causal e respostas de arquivos, mídia e
  IoT. Nenhum parser particular de preferência ou remoção textual posterior.
- **REDs válidos:** `red_confirmacao_valido.xml` (28 falhas, 8 aprovados) e
  `red_playlist_interna.xml` (4 falhas no retorno direto de next/prev). Callback
  de autoria conta chamadas: desabilitar LLM ou capturar sua exceção não
  mascara ausência do veto. Frase/receipt/números e causa permanecem iguais.
- **Controle de candidato:** fallback de play/pause não pode derivar o fato
  do alias usado para variação (`pause`). `red_alternancia.xml` rejeitou a
  falsa frase “Pausei”; mapa factual passou a consultar o comando real.
  Esse erro do candidato não foi atribuído à raiz histórica de transporte.
- **Escopo:** supressão de ornamentação opcional nos consumidores verificados;
  não declarar remoção de qualquer metáfora preexistente no fallback factual.

### RPV20-04 — Gerador de estado reinferia confirmação apesar do receipt

- **Primeira RED instalada:** receipt `brilho_ajustado`, executou=True e
  confirmado=True, chegava ao adapter; `fala_por_estado_acao` criava outro
  ResultadoAcao pela lista de status e devolvia confirmado=None. O texto
  ganhava ausência de confirmação antes de receber o receipt real novamente.
- **Contrato/owners:** gerador consome o ResultadoAcao transportado pelo
  adaptador; status/alvo/execução/confirmação pertencem ao contrato existente.
  Compatibilidade sem contrato continua conservadora. Não ampliar a lista de
  status confirmados para transformar nome otimista em evidência.
- **Falsificações:** planner com receipt confirmado mantém o fato; a mesma
  preferência atravessava app sem ação e repetição causal corretamente;
  falho/incerto rejeitavam fallback otimista. Não era perda de número,
  indisponibilidade da LLM ou uma falha geral de entrega textual.
- **Provas:** RED em `consumidor_instalado_valido.xml` e
  `consumidor_controles_negativos.xml`; GREEN instalado em
  `green_receipt_consumidor.xml`. Controles de brilho e volume confirmados,
  falhos/incertos e sem receipt em `green_receipt_multidominio.xml`.
- **Limite:** composição instalada, memória isolada, portas executoras
  simuladas e método original de voz silenciosa. Texto e recibos são
  observados; ação externa e audição física não são certificados.

### P20 — Evidência e próxima fronteira, 06/10/2026

- Baselines distintos antes da seleção explícita e dos consumidores, hashes,
  XMLs e seleção em `resultados_testes/p20_preferencias_20261006`.
- Seleção final após todos os candidatos: **1.264 aprovados em 60,41 s**,
  81 módulos, `regressivos_expressao_finais.xml`. Resultado anterior de 952
  aprovados é intermediário; não somar gates ou declarar suíte completa.
- `red_transporte_confirmacao.xml` contém GREEN: teste e candidato chegaram
  durante a preparação. Não usá-lo como prova RED. `red_confirmacao.xml`
  tinha erros de fixture congelada; foi substituído pelo RED válido.
- Três expectativas antigas de dict/kwargs não incluíam a nova preferência
  transportada. Foram atualizadas mantendo status, alvo, tom e compromisso;
  XML original de falhas preservado, sem declarar que era totalmente verde.
- Primeira fronteira implícita ainda aberta: distinguir feedback sobre estilo
  de recusa/correção factual; vinculá-lo a entrega real e contexto da entrega,
  com deduplicação e várias ocorrências antes de alterar tolerância. A janela
  canônica de silêncio de 600 s não deve ser duplicada ou antecipada.
- Primeiro RED futuro: duas entregas registradas; “Essa piada passou do ponto”
  qualifica estilo com literal/ID/contexto da entrega, enquanto “O número da
  dica está errado” permanece correção genérica. Uma amostra não cria
  preferência. Motor só deve agregar após várias entregas distintas, sem
  contar replay nem atravessar contexto. Registrar entrega de comando pelo
  canal compartilhado; receipt de execução não prova entrega da fala.
- Preferência explícita validada; calibração implícita não ativa. P19 conserva
  sua lacuna perceptível, P16 permanece no escopo aprovado. Nenhum commit
  criado; worktree paralela e autorização histórica de push preservadas.

### RPV20-05 — Feedback genérico não qualificava o objeto humor

- Contrato: literal qualificado pelo interpretador único + fonte validada
  pela ponte antes da projeção no MotorAprendizadoRuntime. Feedback genérico
  conserva seus pesos; correção factual não vira preferência de estilo.
- RED `red_qualificacao.xml`: 29 falhas, quatro aprovados; ausência de
  qualificador e perda do contexto na ponte. Não era erro de importação.
- Classificação genérica correta e persistência genérica bem-sucedida
  falsificaram as hipóteses concorrentes de parser geral e armazenamento.
- GREEN `green_qualificacao.xml`: 33 aprovados. Citações, terceiros,
  instruções independentes e vulnerabilidade não qualificam evidência.

### RPV20-06 — Receipt de entrega e contexto social eram insuficientes

- Queue acceptance e receipt operacional não confirmam entrega comunicativa.
  Diretor reutiliza o histórico/IDs; orquestrador registra publicação textual
  aceita; worker de voz registra somente reprodução confirmada por software.
- RED `red_entrega.xml`: seis falhas, um aprovado, na porta ausente.
  RED `red_contexto_entrega.xml`: uma falha; domínio `rotina` durante jogo
  era convertido em conversa. Owner congela contexto da decisão social,
  incluindo propostas proativas antes da entrega assíncrona.
- RED `red_silencio_relacionado.xml`: uma falha; “Ainda não sei” não impedia
  silêncio indevido. Pergunta sobre estilo e resposta relacionada são
  qualificadas canonicamente. Silêncio só após 600 s, até 3.600 s, uma vez.
- Fonte emocional conserva sua projeção neutra; proveniência de aprendizado
  acrescenta contexto de humor. Expectativas de testes devem distinguir as
  duas projeções, sem ampliar a autoridade ou payload do evento emocional.

### RPV20-07 — Agregação não decidia tolerância contextual

- RED `red_agregacao.xml`: dez falhas, 14 aprovados; SQL genérico funcionava,
  mas evidência de estilo não era persistida. Não declarar raiz no SQLite.
- Motor persiste somente evidências qualificadas com fonte; Maturidade
  revalida cada registro e decide suficiência. Seletor do turno e consumidores
  de expressão reutilizados; nenhuma nova permissão ou chamada de LLM.
- Três IDs de entrega distintos no mesmo contexto, predominância ponderada
  >=75%, influência média >=0,30. Correção de estilo -0,75, recusa -0,45,
  aceitação +0,45, repetição +0,25. Decaimento individual com meia-vida de sete
  dias; validade máxima 14 dias. Registro novo não rejuvenece os anteriores.
- Silêncio -0,10 é evidência neutra: não conta para as três amostras
  direcionais nem inverte o tom; só reduz influência do padrão. Pedido
  explícito vigente vence sempre, mesmo contra inferência mais recente.
- Contextos `jogo`, `conversa`, `comandos` independentes, sem perfil pessoal.
  Preferência derivada é temporária e recalculada após reinício; fonte
  qualificada persiste. Catálogo vivo e diagnóstico explicam esses limites
  sem expor literais pessoais no diagnóstico.

### P20 implícita — Auditoria dos gates intermediários

- Baseline HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch `main`;
  hashes e worktree congelados em `p20_implicita_20261006/baseline.json`.
- `composicao_instalada.xml` tinha nove erros de fixture: porta real pertence
  ao Adaptador instalado, que delega ao Motor. Não é RED de produção.
  `composicao_instalada_valida.xml`: nove aprovados com owners corretos.
- `green_agregacao.xml`, `green_cadeia.xml`, `green_composicao_catalogo.xml`
  são gates intermediários com falhas preservadas; nomes não provam GREEN.
- `regressivos_finais.xml`: dez falhas, 1.436 aprovados. Seis expectativas
  misturavam projeção emocional com contexto de aprendizado; quatro imports
  colidiram com o mutex da aplicação aberta. Testes corrigem a separação de
  contratos; execução isolada usa mutex Windows real com namespace próprio,
  sem remover proteção ou interromper a aplicação.
- `green_contexto_causal.xml`: duas falhas, 120 aprovados, porque dois replays
  artificiais ainda não transportavam o contexto exigido. Fixtures corrigidas;
  `green_contexto_causal_final.xml`: 38 aprovados na fronteira revisada.
- Coleta instalada em `coleta_instalada.json`: dois processos, nove entregas
  textuais em três contextos, persistência, reidratação, consumo, replay,
  expiração e precedência explícita; sem modelo, fila de áudio ou execução
  externa. Não representa autoria semântica ou som físico.

### P20 implícita — Gate de encerramento da implementação

- **1.447 aprovados em 86,10 s**, 94 módulos, XML
  `resultados_testes/p20_implicita_20261006/regressivos_finais_isolados.xml`.
  Seleção, launcher de isolamento, hashes e coleta preservados. Não é suíte
  completa nem soma dos gates intermediários.
- Implementação da P20 encerrada pelos contratos RPV20-05/06/07; todos os
  itens dessa etapa no roadmap atendidos no escopo de software. Ativação
  final e validação sequencial permanecem na P21; P19 conserva a lacuna de
  observação física. P16 não foi reaberta.
- Produção alterada nesta continuação: interpretador_continuidade,
  preferencia_humor, diretor_presenca, ponte_iniciativa_aplicacao,
  motor_aprendizado, maturidade_aprendizado, orquestrador_turno_runtime,
  orquestrador_fala_runtime, voz_runtime, mapa_habilidades,
  formatacao_diagnostico e wiring/diagnóstico em laylay.py.
- SQLite/schema, executores e autorização operacional não alterados nesta
  continuação. Alterações paralelas preservadas; nenhum commit/push ou
  desligamento executado.

### P21 — Continuação de RPV18-04/05: apresentação e foco, 06/10/2026

- **Baseline:** HEAD `90a2fb8698541119f523c0a22fa4de0187cbaf92`, branch
  `main`, worktree suja preservada. Status e nove hashes anteriores ao
  candidato em `p21_reacao_jogo_20261006/baseline.json`. Esses hashes não
  cobrem todos os arquivos do diagnóstico posterior.
- **Primeiras fronteiras:** RPV18-04 materializava toda descrição como
  `Na tela: "..."`; RPV18-05 escolhia o primeiro fato mesmo quando a fonte
  propunha outro foco, que o parser descartava. São continuações das raízes
  existentes, distintas da troca de modelo por HTTP404 de RPV18-03.
- **Falsificações:** a resposta visual anterior não continha o molde citado,
  que o compositor acrescentava; portanto a origem do molde local não exige
  uma regressão do provedor. Um segundo fato válido perdeu para OCR inicial;
  havia material disponível, mas transporte/seleção estavam incorretos.
  Não há quadro histórico para provar a identidade da arma ou a direção do
  feixe: regressão semântica do modelo continua hipótese.
- **Contrato:** cognição valida foco por vínculo literal com os fatos;
  apresentação distingue descrição de citação operacional usando leitores
  canônicos. Proposta livre do modelo não confirma efeito nem vira execução.
  Ausência de fonte para foco explícito é fail-closed, mesmo sem motivo.
- **REDs:** 11 falhas/2 controles no primeiro gate; duas falhas/35 controles
  localizaram o uso de origem desconhecida na guarda de alegações, corrigido
  para a origem canônica. Um RED adicional provou o fallback indevido quando
  foco explícito não tinha fatos. Gates e falhas preservados; não somá-los.
- **Composição e regressão:** parser/Coordenador/Diretor/cognição e root
  instalado testam foco, citação, autoridade, fila e callback. Gate anterior
  ao diagnóstico: 1.536 aprovados em 89,62 s, 99 módulos; não é suíte completa.
- **Runtime:** coleta finita `p18_jogo_real_20261006_183052`, dois quadros,
  uma materialização e receipt identificado, zero chamadas de autoria.
  Nenhum quadro do laser; outro quadro coberto pelo Discord. Fonte sugeriu
  `mecânica de graviton implícita`, que não foi escolhida nem falada.
  Qualidade dessa inferência fica aberta como hipótese do produtor, sem
  agrupamento automático com apresentação. Som/naturalidade não certificados.

### RPV21-01 — Projeção incompleta e incoerente do diagnóstico emocional

- **Primeira fronteira:** snapshot omitia intensidade e projeção expressável;
  evento válido contido tinha supressão vazia, enquanto evento expirado podia
  mostrar um código otimista de expressão. O estado causal já existia; a
  divergência era na projeção de leitura, não na escrita da emoção.
- **Owner/contrato:** `diagnostico_mente` consulta os leitores canônicos de
  validade e expressão usados por voz/avatar; formatter apresenta esse
  retrato. Diagnóstico não altera memória, emoção, resultado ou autorização.
  Referência causal publicada por hash, sem o relato pessoal.
- **RED válido:** seis falhas em `red_diagnostico_valido.xml`. O primeiro
  arquivo `red_diagnostico.xml` é erro de coleção por nome de API incorreto
  no teste; não constitui prova causal. Comando com módulo inexistente também
  não executou testes. Fixtures corrigidas antes de produção, sem enfraquecer
  expectativas. O mesmo cuidado vale para a tentativa inicial de composição
  com nome de módulo inexistente.
- **GREEN:** 162 controles focados; depois 70 de diagnóstico, catálogo e
  composição; após referência causal por hash, 22 controles. Último gate
  conjunto focado de foco/diagnóstico/transporte: 28 aprovados. São níveis
  intermediários, não soma nem suíte completa.
- **Limites:** root instalado valida snapshot sem hardware. A sessão real
  de jogo importou o código antes deste candidato; não prova os campos novos.
  P21 continua em andamento, P19 mantém observação perceptível pendente e
  P16 não foi reaberta. Nenhum commit/push ou desligamento nesta continuação.
- **Gate conjunto posterior:** 1.544 aprovados em 71,04 s, 100 módulos,
  `regressivos_incremento_final.xml`. Inclui diagnóstico, catálogo e o controle
  de foco sem fatos. XML anterior de 1.536 preservado; gates não somados.
  Launcher usa memória temporária e namespace próprio no mutex Windows real.
  A chamada de ferramenta foi interrompida, mas o processo continuou; resultado
  confirmado pelo XML concluído, sem repetir a execução.

### RPV21-01 — Continuidade: causa selecionada e elegibilidade, 06/10/2026

- **Baseline desta continuação:** mesmo HEAD/branch, status e seis hashes
  preservados em `p21_validacao_final_20261006/baseline.json`. Worktree suja
  mantida. Não renomear a raiz por cada cenário do diagnóstico.
- **Primeira fronteira:** após publicar evento forte e evento fraco, o quadro
  corretamente apontava para a última proposta, enquanto o episódio mantinha
  a causa forte. Snapshot juntava expressão forte com metadados da proposta
  fraca. Elegibilidade de um evento sem episódio aplicado também aparecia
  como decisão atual de expressão, apesar da projeção canônica calma.
- **Falsificações:** a prioridade já preservava o episódio correto antes do
  snapshot; publicador registrava corretamente a proposta nova. Portanto
  não alterar prioridade, publisher, setters ou executor. Composição instalada
  confirmou a mesma primeira fronteira em entradas de terminal e chat.
- **REDs válidos:** dois em `red_transicoes_diagnostico.xml`; dois em
  `red_transicoes_instaladas_valido.xml`. A tentativa inicial de composição
  falhou ao fazer deepcopy de mapa com RLock; não é RED causal. Gates posteriores
  com 68 controles verdes ainda tiveram erro de fixture por argumento de voz
  inexistente e por campo de origem incorreto. APIs corrigidas no teste,
  preservando todas as asserções causais. Snapshot após publicar fala é
  comparado com o estado posterior à publicação, sem confundir seu ciclo
  legítimo com escrita do diagnóstico.
- **Candidato mínimo:** somente diagnóstico/formatter de produção nesta
  continuação. Causa/intensidade/responsável da expressão vêm do episódio
  escolhido pelo leitor canônico; referência separada conserva a última
  proposta. Evento elegível sem expressão atual mostra contenção. Sem
  alteração de memória emocional, prioridade, resultado, autorização ou
  fila. Dez controles focados aprovados; gate completo final registrado abaixo.
- **Coleta perceptível:** helper existente P19 ganhou somente observação
  de diagnóstico e hashes de suas fontes. Coleta real finita 35,776 s,
  250 amostras, 77 durante fala, duas falas concluídas e zero chamada ao modelo.
  Pedro confirmou diretamente som completo/inteligível, expressão estável,
  segunda mais intensa e retorno neutro. Confirmação em arquivo próprio;
  relatório bruto preservado. Não estender ao laser, naturalidade de jogo,
  pacote Game Bar ou a todos os estados operacionais.

### P21 — Suíte completa e correção de fixtures, 06/10/2026

- Primeira execução completa configurada: **10.068 aprovados, duas falhas,
  um ignorado e 56 subtestes aprovados**, 585,37 s. XML `suite_completa.xml`
  preservado em `p21_validacao_final_20261006`; não é gate verde global.
- Falha antiga do guardião TTS, antes anotada em RC-OFERTA-01, reproduzida
  isoladamente. Sua porta falsa fornecia somente `wait`, mas o contrato
  P19 de cancelamento/receipt usa `get_stream().active`. O diff confirma a
  troca anterior; código da voz não foi alterado nesta continuação.
  Fixture agora fornece stream concluído e exige que ele seja consultado.
  Controle adicional sem receipt permanece falso, sem declarar migração
  bem-sucedida. Não substituir reprodução por callback sempre verdadeiro.
- Falha do novo teste P21: `chat` foi usado como origem de entrada, mas a
  origem canônica do texto é `terminal`; chat é estado da conversa.
  Fixture usa o setter instalado de modo chat e mantém origem terminal,
  verificando tanto modo quanto origem real. Normalizador não alterado.
  Os dois REDs instalados anteriores comprovam a projeção errada, mas a
  variante então rotulada chat ainda estava no modo padrão e teve origem
  normalizada como desconhecida. A prova de modo chat ativo é a nova coleta
  `transicoes_chat.json`, com entrada terminal e `chat_ativo=True`; não atribuir
  retroativamente esse modo ao RED anterior.
- **110 controles aprovados** em `green_fixtures_canonicas.xml`; todos os
  controles de causa, plano, autoridade, número de publicações e falta de
  receipt preservados. Segunda execução completa: **10.071 aprovados, um
  ignorado e 56 subtestes aprovados em 402,44 s**, XML próprio
  `suite_completa_final.xml`, zero falhas/erros. Coleta instalada da primeira execução copiada
  para `coleta_instalada_primeira_suite.json`, sem apagar o histórico.
- Candidato desta continuação permanece restrito a diagnóstico/formatter.
  Ajustes das duas fixtures não demonstram outra raiz de produção; não
  reabrir P16 nem criar um remendo na voz ou no normalizador de origem.
- Matriz final de 17 contratos validada contra os casos do XML completo verde,
  com IDs das raízes históricas. A unidade de encerramento continua a raiz,
  não o cenário. Diagnóstico/invariantes de software concluídos; causas
  controladas e confirmação humana das duas falas/avatar não certificam toda
  a sequência real ou a qualidade semântica do jogo/laser. Limites de estados
  operacionais e Game Bar preservados. Laylay principal anterior ao candidato
  precisa recarregar o código. Nenhum commit, push ou desligamento neste gate.

### RPV18-04/05 — Continuação: OCR isolado e moldura genérica, 06/10/2026

- **Relato novo:** `Reparei nisso. Na tela: "-FLORESTA.".`. Não encerra a
  qualidade de jogo a suíte da P21 de diagnóstico ter passado. A fala literal
  não foi localizada nos campos persistidos consultados; o runtime de origem
  estava fechado na primeira inspeção, portanto não presumir seu hash.
- **Reproduzido na worktree:** o foco aceita `texto exato visível: -FLORESTA.`
  como curiosidade e o compositor acrescenta uma abertura à citação. Mesmo
  uma observação já conversacional ganhava complemento genérico. São
  continuações da seleção RPV18-05 e apresentação RPV18-04, não novos IDs por
  frase. Doze REDs de contratos antecederam o candidato.
- **Falsificações:** a moldura é produzida antes de TTS e com zero autoria de
  modelo; falha de pronúncia ou troca de provedor não explicam sozinhas essa
  transição. O texto é reconhecido como OCR corretamente; o erro é tratá-lo
  como acontecimento que justifica comentário.
- **Contrato / owners:** cognição conserva a fonte OCR, mas contém
  companhia/curiosidade quando o foco é só rótulo ou fragmento nominal. Foco
  explícito contido não é substituído por outro item para forçar fala. A
  contenção é obedecida por RespostaEventoRuntime também fora do jogo, sem
  chamar outra autora. Perguntas visuais e nomes musicais úteis conservam seus
  caminhos. O compositor entrega diretamente a observação descritiva breve;
  celebração, acolhimento, provocação e citação operacional mantêm seus limites.
- **Produção nesta continuação:** `contrato_fala.py`, `compositor_evento_local.py`,
  `resposta_evento_runtime.py` e prompt de `analise_visual.py`. A chamada visual
  pede a evidência focal em linguagem de conversa, literal e concreta. Fala
  livre, motivo, mecânica inventada e comando não ganham papel de evidência.
- **Gates:** 49 focados, quatro pela composição instalada e 271 regressivos,
  em XMLs separados de `p21_jogo_naturalidade_20261006`, sem somar contagens.
  O root real usa parser/Coordenador/Diretor/cognição/fila: OCR gera zero timers
  e zero fila; observação natural gera uma fila e um timer, sem segunda autoria
  nem confirmação física antecipada. Gate antigo da P21 não cobre este candidato.
- **Auditoria de testes:** cinco expectativas antigas pediam bordões variados
  sobre a mesma observação ou curiosidade sobre nome OCR. Foram atualizadas
  pelo novo contrato explícito: curiosidade conserva a frase concreta;
  variação continua provada em celebração e citação em nome musical útil.
  Não foram retiradas as guardas de autoridade, vulnerabilidade ou receipt.
- **Coleta real:** iniciada no Megabonk, que era o jogo aberto. Helper finito
  existente recebeu preservação opcional dos quadros e estado próprio da
  central. Resultados e limites serão vinculados após a coleta; não declarar
  naturalidade geral ou reconhecimento do laser pelo GREEN controlado.
- **Primeira coleta deste candidato:** `p18_jogo_real_20261006_192748` guardou
  quadros reais. Uma frase sem bordão chegou ao receipt identificado, mas era
  o fragmento `círculo azul brilhante no chão sob o personagem.`. Isso falsifica
  que o primeiro ajuste bastava para a naturalidade. A segunda proposta trouxe
  foco fora da própria lista; guardas existentes impediram sua fala. Associação
  do círculo ao portal era inferência visual sem prova e não foi falada.
- **Próxima fronteira do mesmo owner:** prompt da própria chamada visual
  consolidado: uma frase factual completa, em linguagem de conversa, repetida
  literalmente em evidência/foco/fala; sem prose duplicada ou bordão adicional.
  Replay do primeiro quadro produziu frase completa, mas inferiu conforto da
  pedra; regra reforçada para aparência/posição observável. Segundo replay teve
  HTTP 429 e não ganhou fala. Prompt final encurtado, 88 controles aprovados;
  coleta fresca em `p18_jogo_real_20261006_215418` preserva fonte e hashes.
- **Avaliação humana RED, decisiva:** a coleta `215418` entregou
  `Esse monstro de pedra com olhos azuis parece bem pesado ali no tronco!`.
  Pedro respondeu **`Ouvi, mas ainda ficou ruim`**. Frase completa e receipt
  verde não encerram naturalidade. A regra que forçava autoria dentro de fatos
  manteve descrição em vez de reação e foi revista; não atribuir aprovação
  humana a essa tentativa. Registro literal em `avaliacao_humana.json`.
- **Contrato revisado, mesma raiz RPV18-04:** produtor propõe `proposta_reacao`
  com fala, foco literal, trecho concreto e humor; transportadores não adotam.
  Cognição é dona da adoção, reaproveitando modalidade, alegações, aderência e
  guarda de ataque pessoal. Reação não entra na lista de fatos. Proposta
  inválida/ausente, humor contido ou vínculo incorreto ficam sem fala e sem
  fallback narrativo, em todos os domínios que usem esse contrato. Onze REDs
  antes do candidato; ajuste posterior de casing do trecho não altera a fonte.
  Vínculo textual e guardiões não são um detector universal de verdade da
  fonte visual; não promover a impressão social a receipt ou fato durável.
- **Coleta autoral `220211` concluída:** três análises, nenhuma entrega. Dois
  quadros não justificaram fala; no terceiro, `portal de chefe` não estava no
  fato focal e a cognição conteve por `reacao_sem_vinculo_factual`. Inspeção da
  captura mostrou que o objetivo do HUD não identificava aquela estrutura.
  A contenção é válida; silêncio não aprova naturalidade. Processo saiu com
  código zero e aviso Win32 ao liberar COM, sem interferir no jogo.
- **Precisão humana do RED:** Pedro explicou que o monstro foi comentado como
  um objeto ao lado do tronco, sem acompanhar a ação. Replay real de dois
  quadros preservados produziu vínculos textuais válidos, mas voltou a focar
  objetos. Isso falsifica que separar autoria/fato ou ordenar o JSON basta
  para corrigir a seleção RPV18-05. Replay não é captura nova nem áudio.
- **Primeira fronteira agora delimitada:** observador fornecia uma foto
  isolada; o produtor aceitava aparência estática como companhia. Princípio:
  uma afirmação temporal requer evidência temporal do mesmo alvo; diferença
  perceptual sozinha não prova acontecimento. Não criar ID por frase.
- **Candidato mínimo desta fronteira:** observador captura dois instantes
  próximos, com espera de 0,6 s, revalida jogo/janela/PID antes e depois e usa
  o pacote multimodal compartilhado numa análise. Sequência incompleta,
  alvo divergente, ocupado ou revogado não seguem. Runtime informa ordem
  temporal ao prompt somente para esse par rotulado; tooltip não vira vídeo.
  Prompt prioriza ações/efeitos/resultados e não catálogo de objetos, com
  reação curta em momento seguro. Não foi criado streaming ou segunda autora.
- **Gates temporais:** seis REDs antes do candidato; um RED adicional para
  troca da janela durante a segunda captura. 157 controles relevantes verdes
  incluem seis casos no root, um deles observador → visão → parser → Diretor
  → cognição → fila. 72 controles posteriores cobrem também a revalidação
  final; não somar gates. Um teste antigo falhou apenas por casing de
  `Decida`; a asserção conserva o contrato usando `casefold`.
- **Limites:** amostragem esparsa não acompanha toda ação nem prova mecânica;
  o modelo ainda pode interpretar a imagem incorretamente. Segurança e
  receipts não certificam semântica. Nova coleta finita `221226`, de 90 s,
  avaliará seleção real; aprovação perceptível permanece pendente.
- **Fechamento desta coleta, sem encerrar a raiz:** `221226` registrou dois
  pares. Primeira análise indisponível; segunda reagiu ao aparecimento de
  `REFLECT`, mas terminou em pergunta retórica e foi contida. Orientação do
  produtor corrigida para fala afirmativa, sem mudar o veto canônico. Replay
  desse par produziu `Esse REFLECT apareceu bem na hora!`, sem áudio; controle
  de quadro repetido teve HTTP 429 e é inconclusivo.
- **Custo real do par:** limite observado 7.000 tokens/minuto, pedido de 5.563,
  uso de 6.828 no controle rejeitado. Cadência de 35 s não acomoda duas dessas
  análises por minuto. Um RED de cadência antecedeu o piso de 60 s do loop;
  budgets por janela existentes preservados. Não afirmar rate limit dinâmico
  universal nem que chamadas diretas ao método têm esse mesmo espaçamento.
- **Gate final:** 160 aprovados em 50,02 s, incluindo seis casos instalados.
  Nenhuma suíte completa refeita; gates anteriores não somados.
- **Última coleta `221645`, 90 s, concluída:** um par no menu de upgrades,
  uma análise, zero entrega, nenhuma aprovação humana nova. Fonte alegou
  contador aumentando de 4 para 5, mas ambas as capturas mostram moeda=4 e
  caveira=5. É um RED semântico remanescente da fonte, não uma mudança temporal
  provada. Essa afirmação não foi falada. Não corrigir com outro bordão ou
  relaxar o vínculo factual. Relatório/manifesto em
  `p21_jogo_naturalidade_20261006`. Falta a prova perceptível de reação à ação
  e a leitura visual mantém limite explícito. Sem commit/push/desligamento.
- **Novo controle perceptível aprovado, `222605`:** após Pedro confirmar
  combate, helper antecipou um único par, com toda a composição/captura/modelo
  reais. Duas capturas, uma análise, uma entrega identificada. Pedro confirmou
  `Ouvi e a reação ficou adequada` sobre a fala do contador 33 → 35 e a festa
  ficando mais cheia. GREEN de áudio/adequação deste caso; não apagar o RED
  humano anterior nem validar cadência normal com disparo antecipado.
- **Limite preservado:** caveira=33 → 35 é visível; interpretar isso como
  mais inimigos vivos não é comprovado. Um refinamento no prompt excluindo
  contadores voltou a comentar aparência estática do círculo no replay real.
  Hipótese falsificada; só esse bloco novo foi retirado por `apply_patch`.
  Nenhuma outra mudança revertida. Fontes de produção iguais às do gate de
  160/controle aprovado; artefatos e declaração humana separados.
- `222336` havia capturado menu principal, sem fala. Controle `222605`
  concluiu a coleta mas saiu com código 1 e aviso COM após o receipt. Isso
  não revoga a audição humana nem prova saúde do teardown. Qualidade universal
  da fonte e teardown permanecem limites; não abrir patch alheio para forçar
  encerramento. Sem commit/push/desligamento; P16 preservada.

### Pedido composto — autoria por pedido a partir de receipts individuais — 08/10/2026

- Base `main`, `90a2fb8698541119f523c0a22fa4de0187cbaf92`, worktree compartilhada
  preservada. Frase humana: `liga a luz e coloca a playlist piano`.
- Primeira divergência: cada adaptador gerava e entregava sua própria autoria
  antes do TTS. Dois receipts legítimos produziam dois balões; deduplicação de
  uma mesma ocorrência não explica esse caso. RPV18-07 congela reprodução;
  esta fronteira anterior possui outra responsabilidade, sem fundir as raízes.
- Contrato/owner: orquestrador de fala acumula a apresentação por pedido;
  executores mantêm autorização, efeito, receipt e certeza próprios. Cadeia
  determinística e dispatcher JSON reutilizam a mesma porta. Uma autoria
  validada cobre os resultados; finalização preserva histórico/aprendizado sem
  pedir outra fala. Avisos sem receipt não recebem a prova de outra etapa.
- REDs e controles preservam falha parcial, idempotência, atualização de certeza,
  humor, turno antigo, estados não confirmados e texto publicado sem áudio.
  Regressão consolidada: **579 aprovados / 27 módulos / 22,31 s**. Duas autorias
  originais 4B aceitas em **1,815 s / 1,479 s**, com efeitos externos isolados.
- Após reabrir e testar o pedido, Pedro confirmou **`Uma resposta e fala mais rápida`**.
  Prova qualitativa de apresentação/audição desta ocorrência, sem cronometragem
  no jogo nem inspeção de efeitos físicos. Sem commit. Relatório/diff/hashes:
  `resultados_testes/latencia_geral_20261008/resposta_composta/`.
- Otimização temporal separada: lote Ollama 128→256, preservando pesos, contexto
  6144 e amostragem; backup e receipt no diretório pai. A compactação emocional
  foi rejeitada por perda de evidência na geração real; contrato original e voz
  preservados. A coleta nova repetiu uma resposta contextual: achado de qualidade
  permanece registrado, sem atribuir sua causa ao lote ou fechar P01.
