# Contexto disponível, mas pergunta e fundamento não preservados — 25/10/2026

## Pedido e estado da investigação

Pedro trouxe o diálogo de 20:12–20:15 e perguntou se houve perda de contexto.
Esta etapa investigou a hipótese; **não aplicou patch de produção**. HEAD
`c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, `main`, worktree anterior preservada.
Estado Git, 530 hashes, cópias anteriores dos owners e o recorte do log estão em
`resultados_testes/conversa_recomendacao_20261025/`. Nenhum commit, mudança de
modelo/configuração, voz ou efeito externo. Não afirmar que o processo histórico
executava exatamente esses bytes: o log não fornece hash nem payload.

## O que a reprodução confirmou

Composição instalada, mesmo Qwen/Ollama, quatro entradas/publicações, cinco HTTP
200 (a saudação fez uma chamada de reparo). Fontes estáveis; persistência isolada;
voz suprimida e executores simulados, sem nenhuma solicitação de ação na coleta.

O contexto relevante está no HTTP final: a sugestão do usuário mencionando
Kamaitachi, a resposta anterior sobre esse nome e a pergunta atual integral.
O histórico armazenado contém as entradas anteriores. Nenhum turno renovou a
sessão. Portanto, **perda geral de armazenamento ou reset não explica a
reprodução atual**. Isso não prova retenção semântica perfeita nem reconstrói o
payload histórico.

A saída atual não repetiu todos os sintomas literalmente. Não chamou Kamaitachi
de estilo e respondeu sobre o usuário no último turno; porém inventou novamente
características e experiências, depois as reutilizou para recomendar. A pergunta
sobre estilo favorito recebeu prosa sobre violão/piano, calma e silêncio,
apesar de o contrato próprio existente já restringir perguntas equivalentes.

## Fronteiras e owners — manter causas distintas

### Lacuna da leitura de preferência própria já documentada

`consulta_opiniao_propria` reconhece `qual o seu estilo musical?`, mas não
`voce tem um estilo musical favorito?` ou `você tem um gênero musical preferido?`.
A forma existencial de favorito só admite uma categoria nominal de uma palavra
do mapa, enquanto a categoria musical composta está em outro ramo sintático.

```text
pergunta subjetiva atual
→ leitor integral retorna None
→ contrato genérico: atos=[pergunta], estratégia=resposta_direta
→ não nasce opiniao_autoral
→ autoria livre inventa descrição/experiência
→ revisão genérica admite
```

É uma nova ocorrência da fronteira de leitura de gosto, não uma nova causa de
memória apagada. Owners: `referencias_linguagem.consulta_opiniao_propria`,
`opiniao_autoral` e sua projeção em `contrato_fala`. O contrato de opinião
existente não precisa ser removido; falta chegar a ele pela forma equivalente.

### Alvo da pergunta atual de adequação não é obrigação conferida

Para `me fala lay, que estilo combina comigo?`, o contrato recebe
`atos=[conversa, pergunta]` e roteiro genérico. A perspectiva do canal distingue
falante e autora, mas não registra a relação perguntada: adequação de uma opção
**ao usuário**, diferente da preferência da assistente.

O revisor atual aceita literalmente a resposta histórica:
`Lay, não tenho estilo musical favorito, mas a ideia de algo intenso e direto me chama a atenção.`
Também aceita `Eu prefiro Firefox.` para `que aplicativo combina comigo?`.
São REDs de pertinência de alvo/predicado, não demonstração de ausência de fonte
histórica. Existir no histórico, ter sido publicado e responder à pergunta atual
são obrigações diferentes. Owners a estudar: leitura comum de referências,
projeção do núcleo em `contrato_fala`, `validacao_contrato_fala` e o reparo
compartilhado de qualidade. A correção não deve consistir em bloquear a frase do
log ou trocar pronomes no texto pronto.

### Categoria/características e vocativo: evidências separadas

O log histórico atribui categoria e características ao nome citado sem mostrar
fonte; a reprodução inventa características novamente, mas não a mesma
categoria. A fala anterior da IA não pode servir como prova dessas propriedades.
Mencionar uma opção que a Laylay talvez goste também não declara que o usuário
gosta dessa opção. Não há base para escolher seu gênero musical por essa menção.
Não classificar uma entidade por nome, snippet ou proposta da IA nesta etapa.

O leitor de identidade não reconhece o vocativo medial em `me fala lay, ...`:
`vocativo_laylay=False`, texto inalterado. Isso é uma lacuna lexical verificável;
sem o payload histórico não prova sozinho por que a saída chamou o usuário de
Lay. Não juntá-la automaticamente à decisão de adequação ou à categoria.

### Prazo e resumo diário não provam esquecimento

A primeira contingência do log não tem a entrada correspondente nem o percurso
de geração. A mensagem indica falta de orçamento para outra tentativa; não
identifica sua causa. O aviso de resumo diário informa adiamento/preservação de
lote, não demonstra exclusão do histórico da conversa. Não contar esses avisos
como a mesma raiz das respostas sem pertinência.

## REDs e falsificações preservados

`test_contratos_diagnostico.py`, fora da suíte padrão em `scripts/tests`, usa os
leitores, planejador, contrato e revisão reais, sem substituir os owners:

- Duas formas existenciais da categoria musical: RED na primeira leitura.
- Duas perguntas de adequação pessoal: RED porque a revisão aceita resposta
  sobre a preferência da assistente, em música e software.
- Duas perguntas nominais de preferência já suportadas: controles GREEN.

Resultado: **quatro falhas e dois controles aprovados**, em `contratos_red.xml`.
Esses REDs são diagnóstico, não testes verdes de uma correção. Não foram
incluídos artificialmente na contagem das falhas antigas da regressão ampla.
`diagnostico.json` audita quatro publicações, cinco HTTP 200, ausência de reset,
presença de contexto relevante no HTTP, guardas sem voz/efeitos e 530 hashes
de produção inalterados. Nenhuma nova regressão ampla foi necessária, pois
produção não foi modificada.

Falsificado na reprodução: reset/perda geral do histórico; indisponibilidade
do transporte; ausência da pergunta atual no prompt; falha geral do contrato
próprio de gosto para todas as formas. Ainda aberto: explicação exata dos tokens
do processo histórico, tipo da entidade por fonte independente, decisão de
adequação fundamentada e extensão geral das paráfrases.

## Direção causal para uma correção

Priorizar a primeira lacuna de leitura demonstrada no diálogo, preservando o
owner de gosto existente e seus controles. Separadamente, projetar e conferir
quem é o alvo e qual relação a pergunta atual exige; opinião própria, gosto do
usuário e recomendação ao usuário não podem compartilhar autoridade por mera
recência. Só então validar reparo/publicação e a conversa completa novamente.

Sem preferência do usuário suficientemente fundamentada, uma resposta natural
pode reconhecer a menção e buscar o critério: `Você mencionou Kamaitachi, mas
ainda não sei se ele representa o seu gosto. O que você mais gosta de ouvir?`
É um exemplo de comportamento esperado, não frase fixa para produção, prova da
categoria do nome ou solução já aplicada. F1/C5/C7/AUT e os contratos anteriores
de sessão continuam separados.
