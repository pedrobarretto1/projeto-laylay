# C5/P01 — contexto da fonte antes de conferir reformulações

Base: `main`, HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, worktree já
modificada. Inventário, hashes, fonte anterior e provas em
`resultados_testes/contexto_fontes_explicacao_20261023/`.

## Raiz e primeira divergência

O estudo anterior rejeitou uma regra de reordenação porque não comprovava
atomicidade/escopo. Essa regra permanece retirada. Antes de tentar outra
transformação, foi mapeada a origem da informação disponível ao revisor.
Os grafos offline existentes ancoram papéis e condições como **propostas**;
explicitamente não certificam a interpretação. Não ativá-los como prova.

Há uma divergência anterior demonstrada: `pesquisa_multifonte._ler_fonte`
ranqueia frases e publica apenas as vencedoras como `trecho`. Ressalvas antes
e depois da frase, no mesmo parágrafo lido, desaparecem antes de fundamentação,
autoria e revisão. `_TextoPagina` também conserva só prefixo de900 caracteres,
que pode disponibilizar uma frase sem a ressalva final do bloco original.

Ranking é útil para escolher um assunto; não confere fronteiras semânticas.
A revisão literal protege somente o snapshot recebido. Ela não tem como
recuperar condições que o leitor descartou. Primeira fronteira RED:
**bloco lido → trecho individual de evidência**, no owner da coleta.

`red_composicao.xml`:35 REDs antes do candidato, incluindo16 ciclos instalados
com o serviço da factory real reconectado por identidade. Duas páginas lidas
por assunto nos controles; o snapshot chegava recortado às duas rotas.
`controles_antes.xml`:44 GREEN nas rotas existentes, seleção pertinente,
fundamentação, integridade do prompt e recuperação. Isso falsifica falta de
página, indisponibilidade geral, truncamento exclusivo do prompt e decisão da
LLM como causas necessárias **deste recorte**. A reprodução independe da IA.

Não atribuir retroativamente todos os erros históricos de conversa a esta
raiz. Integridade de snapshot já foi estudada na exposição do prompt; aqui a
perda ocorre na coleta, antes dele. Manter essa diferença e os IDs C5/P01.

## Contrato e responsáveis

**Âncora de relevância não é unidade autossuficiente de prova.** As frases
continuam orientando seleção e ranking; o snapshot transporta inteiros os
blocos que as contêm, sem duplicá-los e na ordem observada na página.
Não inferir que um parágrafo seja semanticamente independente: a preservação
é estrutural, não atestado de completude de contexto da página inteira.

| Owner | Responsabilidade e critério |
| --- | --- |
| `cognicao/pesquisa_multifonte.py` | Manter ranking/pertinência por âncora, conservar índices dos blocos, publicar blocos inteiros em ordem e rejeitar snapshot que não caiba no limite canônico850. Nunca voltar à frase isolada para fazê-lo caber. |
| Fundamentação e prompt existentes | Preservar a mesma unidade individual admitida; não alterar os limites autorais ou inventar relações semânticas. |
| Revisão existente | Citação integral continua atribuída; cópia somente da âncora perde apoio integral se o bloco contém contexto adicional. Nenhuma paráfrase livre é aprovada. |

Alternativas rejeitadas: procurar palavras como `somente`/`hipótese` para
expandir apenas algumas frases (remendo lexical); aumentar recorte até uma
distância arbitrária e chamar isso de escopo provado; usar rótulo da autora
como prova; remover a seleção de pertinência; limitar o texto cortando-o.

Mudança mínima planejada: somente o leitor compartilhado. Sem parser semântico,
buscador, grafo de autoridade ou executor novo. O teto850 já existe no próximo
contrato; o teto300 permanece na **âncora de ranking**, não deve apagar o
restante do bloco. A autoria mantém500 por unidade, portanto blocos maiores
podem ser expostos sem admitir sua cópia como unidade única. Não enfraquecer
essa guarda para obter uma aula artificialmente verde.

## Plano e aceite

- [x] Congelar a base e mapear os owners e histórico de recortes.
- [x] Reproduzir primeira perda em unidade e na composição instalada.
- [x] Falsificar causas concorrentes com controles existentes.
- [x] Aplicar candidato no leitor, preservando seleção e qualidade por âncoras.
- [x] Provar contexto anterior/posterior, crítica, blocos longos e comparação.
- [x] Conferir fonte → fundamentação → prompt → revisão → publicação.
- [x] Revisar adversarialmente o candidato; preservar contraexemplos anteriores.
- [x] Validar Qwen instalado e separar sua geração dos receipts de leitura.
- [x] Rodar regressivos pertinentes, registrar falhas anteriores e escopo final.

Um GREEN deste contrato não encerra compreensão de escopo, qualidade editorial,
pertinência semântica universal, verdade externa, explicação natural ou exemplo
didático. Contexto entre blocos e dependências remotas seguem sem comprovação.

## Revisão e fronteira HTML

A revisão independente encontrou fechamento prematuro no mesmo owner:
`<li><p>frase</p>ressalva</li>` terminava no `</p>`, descartando o restante do
`li` que iniciou a captura. O mesmo ocorria em `dd/p`; um contêiner original
maior que850 podia publicar seu filho curto. Esse comportamento era anterior,
mas deixava incompleto o novo contrato. Não foi ignorado como contexto remoto.

Quatro REDs focados e depois seis com estrutura incompleta/incoerente foram
reproduzidos antes do refinamento (`red_aninhamento.xml`,
`red_fechamento_bloco.xml`). A pilha agora aguarda o fechamento correspondente
ao contêiner iniciado. Fechamento interno não o encerra; inconsistência invalida
o bloco, sem promover prefixo. Conteúdo de tags ignoradas não muda a pilha.
Contêiner sem fechamento explícito não é publicado. Isso pode rejeitar HTML
que um navegador repararia implicitamente; o leitor conservador não presume
essa reparação como fonte comprovada.

Revisão posterior conferiu o ajuste e não trouxe nova regressão concreta.
Os testes incluem navegação ignorada, filhos com o mesmo nome, retomada após
bloco inválido, repetição da âncora em contextos diferentes, ordem inversa da
pergunta e soma de contextos fora do teto. O código segue restrito ao leitor.

## Mudança de expectativa do teste anterior

`test_pesquisa_multifonte` esperava fonte de no máximo300 caracteres mesmo
quando o parágrafo tinha513. Isso descrevia precisamente o recorte investigado.
Depois do candidato foi a única falha em119 testes vizinhos (118 GREEN,
2 skips). A expectativa foi substituída por **igualdade exata ao parágrafo
normalizado completo**, mantendo a definição e o teto canônico850. O teste
foi renomeado para declarar o contrato de contexto. Não se reduziu o controle
de segurança nem se alterou a exigência de fonte para fazer a geração passar.

## Provas instaladas e modelo real

- Primeiro ciclo:35 RED antes do candidato e35 GREEN após, incluindo16 ciclos
  instalados. Fonte recortada podia aprovar a âncora sem ressalvas, enquanto
  rejeitava a fala que preservava o contexto original.
- Ciclo ampliado:28 casos de integração, dois assuntos e duas rotas, com
  integral/fragmento/acréscimo/longos e HTML aninhado. A contraprova carregou o
  owner inicial em memória com SHA:28 REDs na primeira fronteira, sem restaurar
  a worktree (`replay_instalada.xml/json`).
- `unidade_final.xml`:31 GREEN. `foco_final.xml`:175 GREEN/2 skips antes de
  adicionar três controles de pilha; a regressão final deve incluir esses31.
- `qwen_controle/conversa.json`:três turnos e três HTTP200 do Qwen configurado,
  zero drift e efeitos. As duas fontes por turno chegaram com ressalvas antes
  e depois do parágrafo interno. A geração extrapolou ou perdeu apoio e ficou
  limitada3/3. Isso confirma a conservação da fonte no envio instalado, **não**
  uma explicação natural completa ou interpretação comprovada pelo modelo.

O isolamento reutiliza a factory real e a mesma instância de pesquisa; folhas
HTTP e geração são controladas nos testes determinísticos. As sondas Qwen usam
o backend configurado, com rede limitada à geração local e, no ensaio web,
GETs públicos conferidos. Não há voz ou execução externa observada.

`web_real/conversa.json`:dois turnos e três HTTP200 do Qwen. No primeiro,
leitura ainda pendente; no reensino, cinco fontes do cache e três expostas no
envio. A fala publicou duas citações integrais e reteve uma afirmação sem apoio.
Na rede de leitura:seis HTTP200 e um ConnectTimeout, separado da correção de
contexto. Zero drift e executores; modo amplo permaneceu desativado. É prova de
caminho real de leitura/transporte/atribuição, não de verdade das páginas.

`verificacao_transportes.json` confirma que todos os snapshots selecionados
chegaram inteiros ao envio principal e à reescrita real. A primeira tentativa
de aferição comparava a consulta com qualquer mensagem do histórico e tomou o
terceiro turno por envio do primeiro. A aferição foi corrigida para o último
user do par atual ou `mensagem_atual` da tarefa de reescrita; nenhuma alteração
de produção foi feita por esse resultado de coleta incorreto.

## Validação final e escopo de entrega

`regressao_final.xml`:**1464 aprovados,30 subtests,14 skips opcionais,
duas falhas anteriores e um teste desmarcado para import isolado**. Falhas
mantidas: `test_autoria_reescritas::test_composicao_transporta_suporte_proprio_de_reparo_e_partes[4]`
e `[6]`, primeira chamada `interpretacao` em vez da expectativa `principal`.
`reescritas_baseline.xml` reproduz as mesmas duas com o leitor anterior
carregado via SHA/import hook,30 controles GREEN. Não alterar esses testes
nem declarar a suíte global verde. `import_final.xml`:1 GREEN para
`test_latencia_resposta::test_composicao_principal_injeta_rota_que_respeita_perfil_explicativo`,
executado isoladamente pela mesma factory real.

São59 testes novos:31 de unidade/contexto e28 ciclos instalados. Um teste
anterior foi fortalecido conforme a mudança de contrato descrita acima.
Diff próprio em `candidato.diff`; base não atualizada. O manifesto de entrega
confere os527 fontes Python e os hashes das duas sondas contra a produção final.

**Produção alterada nesta tarefa: somente `pesquisa_multifonte.py`.**
Autoria, revisão, composição principal, executor, modelo, voz e configurações
não receberam alterações nesta tarefa. Candidato condicional anterior continua
retirado. Nenhum commit, reset, reinício da sessão pessoal ou shutdown; trabalho
paralelo preservado. Reabrir a Laylay para carregar o leitor alterado em disco.

Raiz encerrada somente no recorte de **integridade estrutural do bloco lido**.
Um bloco não garante completude de contexto entre parágrafos nem da página;
não fornece uma árvore semântica validada. Também não melhora por si só o Qwen
para explicar naturalmente: o controle real ainda limitou3/3 falas. A próxima
fronteira continua sendo proposição/dependências/escopo com proveniência
conferível, respeitando o contexto integral recuperado. O limite autoral500
permanece: se um bloco maior não puder ser realizado com cobertura conferível,
a resposta deve abster-se em vez de apagar ressalvas ou aprovar cada pedaço
como proposição independente. C5/P01 e compreensão geral permanecem abertos.
