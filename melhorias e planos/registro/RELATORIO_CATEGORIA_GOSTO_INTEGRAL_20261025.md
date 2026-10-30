# Categoria de gosto não depende da moldura interrogativa — 25/10/2026

## Pedido, base e escopo

Pedro autorizou estudar por que a pergunta sobre estilo favorito escapava do
contrato de gosto, corrigir a raiz comprovada e validar na composição real,
sem remendo por frase, sem voz e com ações simuladas.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. Git, 530 hashes e cópias anteriores dos owners estão em
`resultados_testes/categoria_gosto_integral_20261025/baseline.json` e
`fontes_antes`. Nenhum commit, shutdown, mudança de modelo, configuração,
voz, executor ou persistência pessoal. Trata-se de continuação da raiz de
leitura de opinião própria, não de nova raiz de memória nem de encerramento
das demais falhas do log. Diagnóstico anterior preservado em
`DIAGNOSTICO_CONTEXTO_RECOMENDACAO_20261025.md`.

## Primeira fronteira demonstrada

O leitor compartilhado tinha duas regras desconectadas. A pergunta nominal
reconhecia a categoria composta musical. A forma existencial exigia categoria
de uma palavra do mapa de favoritos concretos. Uma variação gramatical decidia,
indevidamente, se a mesma categoria chegava ao contrato de gosto.

```text
“voce tem um estilo musical favorito?”
→ consulta_opiniao_propria retorna None
→ contrato genérico: atos=[pergunta], sem opiniao_autoral
→ autoria livre cria descrição, experiência e abstração
→ revisão genérica aceita
```

Na mesma composição/processo, `qual o seu estilo musical?` já recebia
`opiniao_autoral` e publicava uma posição curta. `você tem um jogo favorito?`
também seguia o contrato correto. O baseline atual preserva os quatro casos,
com quatro publicações/HTTP 200 e fontes estáveis: as duas formas musicais
existenciais publicaram a mesma prosa livre sobre clima, pele, indie/samba e
calor no peito; os controles publicaram `Eu prefiro trap.` e
`Ainda não escolhi um jogo favorito.`.

Não se atribui ao modelo uma decisão tomada antes da geração. O problema
primeiro é perder a categoria/ato no leitor, e não trocar uma frase depois que
ela já foi gerada. O processo histórico de Pedro não forneceu payload ou hash;
esta reprodução prova o mecanismo nos bytes congelados, sem presumir igualdade
exata com todo o runtime histórico.

## Hipóteses concorrentes falsificadas

- **Falha geral de transporte ou prazo:** quatro HTTP 200, um HTTP por
  entrada e publicação em todos os casos do baseline; nenhum timeout explica
  por que o contrato anterior à chamada fica diferente.
- **Categoria musical desconhecida ou fonte factual obrigatória:** a pergunta
  nominal equivalente funciona no mesmo processo e usa o léxico musical já
  existente. Uma posição autoral não exige inventar uma experiência nem uma
  pesquisa obrigatória sobre “Favorito”.
- **Contrato de gosto presente, mas ignorado pelo Qwen:** o snapshot mostra
  ausência de `opiniao_autoral` nas duas formas existenciais e presença nos
  controles. A primeira divergência antecede autoria e revisão.
- **É preciso aceitar qualquer categoria composta ou remover restrições:**
  negativos mantêm desconhecidos, outro sujeito, passado, negação, citação,
  condição e ações adicionais fora do recorte. Nome proposto não prova título,
  tipo, experiência ou efeito. Os oito tipos concretos continuam limitados às
  mesmas opções anteriores.

## Contrato e responsáveis

Princípio reutilizável: **moldura interrogativa e categoria nominal são decisões
distintas; formas equivalentes devem resolver a categoria pelo mesmo owner e
chegar ao mesmo contrato de autoria/revisão**.

| Responsabilidade | Owner | Critério |
| --- | --- | --- |
| Conferir a pergunta inteira e resolver categoria | `referencias_linguagem.consulta_opiniao_propria` | Formas nominal/existencial passam pela mesma resolução; categoria capturada só é aceita se já conhecida; sem extração parcial de outro pedido |
| Separar posição subjetiva de fato/experiência | `opiniao_autoral` existente | Fonte nativa vinculada a texto/turno, posições já permitidas, `prova_factual=False` e `autoriza_execucao=False` |
| Projetar ato para o contrato | `contrato_fala` existente | Opinião própria reconhecida; pergunta não cai em roteiro genérico por variação nominal |
| Evitar pesquisa incidental | `fundamentacao_factual` existente | Reutiliza o mesmo leitor antes do retrato; uma referência incidental “Favorito” não vira tema de pesquisa |
| Autoria e reparo | Pacote compartilhado de opinião, qualidade e `ContextoPromptRuntime` existentes | Mesmo enum de posições, declaração de critério e fontes vazias; rascunho refutado/contexto antigo não são base da nova autoria |
| Revisão e publicação | Owners compartilhados existentes | Texto integral pertence ao ato; vínculo de turno preservado; nenhuma causa, experiência, título ou confirmação acrescentada |

O candidato modifica **somente `mente_laylay/cognicao/referencias_linguagem.py`**.
Em vez de outro regex para a frase do log, uma moldura lê categoria/qualificador
e a mesma resolução distingue a categoria musical das categorias de favoritos
concretos já existentes. O vocabulário anterior foi mantido. Não há catálogo de
nomes novos, reescrita da saída, dispensa de revisão, novo parser por habilidade
ou alteração de personalidade para esconder a falha.

Permanecem intactos nesta correção: autores de opinião, fontes/critérios,
contrato de fala, qualidade/reparo, revisão, pesquisa, normalização, composição,
sessão, executores e voz. Os caminhos existentes recebem a correção por
reutilizarem o mesmo leitor. Música e os controles de jogos, filmes, livros,
cores, comidas e animais preservam o princípio comum. Não é uma capacidade nova
ou autorização de ação autônoma.

## RED, controles e validação

Antes de produção: **18 falhas e 34 controles aprovados** em `contrato_red.xml`.
As primeiras asserções falham por ausência de leitura/fonte, e as posteriores
mostram admissão indevida de extrapolações. Um preflight anterior teve quatro
falhas adicionais causadas por um erro na construção do possessivo no teste;
essa fixture foi corrigida antes do RED causal e do candidato. `preflight.xml`
e seu log foram preservados e não contam como prova da raiz.

`scripts/tests/test_categoria_gosto_integral.py` tem **52 casos**: três nomes
musicais, formas equivalentes, fala original de Pedro, sujeitos já suportados,
envelope de esclarecimento, envio final, reparo, causas/experiências inventadas,
tipo desconhecido, atos adicionais, fonte estrangeira e oito categorias de
favoritos concretos. Depois do candidato: **52 aprovados**. Foco inicial com
opinião/explicação: **174 aprovados**; foco ampliado: **373 aprovados e dois
ignorados**. Não foi alterada nenhuma expectativa anterior para acomodar a
correção.

O diagnóstico separado foi executado novamente, sem editar suas asserções:
agora os dois REDs de categoria ficam verdes e os dois de adequação ao usuário
continuam vermelhos (**duas falhas/quatro controles aprovados**).
`diagnostico_separado.xml` conserva essa fronteira; ela fica fora da contagem da
regressão padrão e não foi apagada para reduzir pendências.

Regressão ampla em **127 módulos**: **3.245 aprovados**, nove falhas, 44 erros,
14 ignorados, um desmarcado e 30 subtestes aprovados. A comparação por identidade
confirma exatamente as mesmas nove falhas e 44 erros anteriores: comando antigo
da Calculadora, expectativas antigas de pacote/tokens e fixtures de serialização
de `PerspectivaEnunciador`. Não foram corrigidos, removidos ou reclassificados.
Comparativo em `comparacao_regressao.json`; não declarar suíte global verde.

A auditoria final passou e gerou `manifesto.json` e `candidato.diff`, exclusivo
desta alteração contra a base suja congelada. Conferiu os textos brutos HTTP,
enums, vínculo de revisão, ausência de efeitos/voz, critérios com flags falsas,
persistência e os 530 hashes: somente o leitor declarado difere da base.

A primeira auditoria supôs um registro de chamada por HTTP. O hook de
`RegistroModeloLLM` também observa o registro interno de `ModeloLLMDiferidoRuntime`
(`registro_conversa_llm.py:197,252`); os dois registram o mesmo pedido e retorno.
Foi corrigida essa premissa, mantendo a exigência de um único HTTP por turno
focado e identidade integral da proposta publicada. Um pedido auxiliar de resumo
foi bloqueado pelo orçamento sem HTTP, preservado como tal nos dados; não foi
contado como inferência nem convertido em sucesso. Nenhuma produção ou guarda
foi alterada para ajustar a auditoria.

## Composição instalada e Qwen

Factory, planejamento, contrato, pacote de autoria, revisão, publicação e
persistência instalados, com `qwen3:4b-instruct`/Ollama reais. Somente persistência
isolada e folhas de efeitos simuladas; pesquisa externa não é necessária para
esta preferência autoral. Modelo, orçamento e configuração foram preservados.

`final_dialogo`: **12 entradas, 12 publicações e 12 HTTP 200**. Onze turnos
seguiram a revisão `opiniao_autoral_vinculada`; o último encerrou a sessão pelo
contrato já existente. A escolha inicial `Eu prefiro rock.` permaneceu nas
formas equivalentes, inclusive depois de `como assim?`, que recebeu
`Quis dizer que eu prefiro rock.`. Os favoritos concretos não receberam títulos
inventados. Nenhuma chamada de reparo ou troca silenciosa do texto nesses turnos.
As propostas HTTP têm fontes vazias, comando vazio e declaração de critério;
os critérios persistidos conservam prova factual/causal/autoridade falsas.

`historico_final`: quatro entradas originais de Pedro, quatro publicações/HTTP
200. O alvo desta correção respondeu `Não tenho um estilo musical preferido.`,
sem causa ou descrição inventada. Isso não certifica as outras três respostas:
a sugestão sobre Kamaitachi ainda recebeu uma avaliação sem fundamento e a
pergunta sobre o usuário ainda recebeu uma adequação inferida sem apoio.
Essas fronteiras continuam abertas; não alterar esta correção para compensá-las.

`seguranca_final`: três turnos separados, uma ação simulada com receipt negativo
(`executou=False`, `confirmado=False`), e pergunta posterior sem sucesso falso.
Nenhuma ação real ou áudio. Todos os perfis gravaram/releram persistência isolada;
as 530 fontes ficaram estáveis durante as coletas.

## Limites e próxima fronteira

Esta correção cobre a resolução comum das categorias já reconhecidas nas
molduras de pergunta suportadas. Não certifica toda paráfrase, categoria livre,
preferência durável ou sentimento humano. A redação ainda usa as realizações
limitadas do contrato de gosto existente; não é prova de entendimento geral.

Continuam separados: adequação ao usuário versus gosto próprio, características
de entidades sem fonte, vocativo medial, saudação elíptica `como vai?`, aquisição
de fontes e prazos. F1/C5/C7/AUT não foram fundidos ou encerrados. A próxima
fronteira do log é declarar e conferir o alvo/predicado de adequação ao usuário,
sem tratar a opinião anterior da IA ou a simples menção de um nome como prova.
