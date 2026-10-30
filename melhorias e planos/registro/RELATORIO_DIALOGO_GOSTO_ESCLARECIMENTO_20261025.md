# Diálogo curto de gosto e esclarecimento — 25/10/2026

## Base e separação causal

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. Baselines integrais, status, hashes de 528 fontes e cópias dos owners
anteriores estão em `resultados_testes/conversa_gosto_clareza_20261025/` e
`resultados_testes/esclarecimento_composto_20261025/`. O segundo baseline inclui
o primeiro candidato; não foi atualizado para apagar o histórico.

O log de Pedro não pertence à correção da categoria da preferência do usuário.
Aqui há duas fronteiras demonstradas, distintas entre si. Os outros sintomas
continuam em estudo; não consolidar F1/C5/C7/AUT por aparecerem no mesmo diálogo.

## Raiz demonstrada: contexto global captura consultas sem obrigação histórica por ato

Entrada: `como assim? voce nao tem nenhum em especifico?`, após fala publicada.
O interpretador segmenta duas perguntas conversacionais. A recuperação global
encontra a última fala e admite a rota histórica múltipla, mas o binder por ato
retorna todas as partes sem ocorrência, fala vinculada ou falha de fonte.
O contrato instala esse pacote vazio e o renderer publica dois textos internos
de pendência. A coleta baseline com Qwen reproduziu exatamente o sintoma do log.

Falsificações: a segmentação chegou íntegra; não houve comando ou executor;
não é indisponibilidade HTTP (todos os pedidos retornaram 200); fonte global
existente não prova fonte própria de cada ato. O modelo não criou os placeholders:
eles são realizações do host. Trocar modelo ou editar a personalidade não corrige
essa primeira divergência.

Contrato: o owner de explicação histórica só admite um pacote multiato quando
existe obrigação histórica em pelo menos uma parte: ocorrência, fala ou falha
de fonte. Um pacote nativo válido com todas as partes sem vínculo permanece
conversacional. `None`, referências históricas ausentes e falhas preservam a
política anterior, sem autorização operacional ou inferência de sucesso.

Produção desta raiz: `cognicao/contrato_fala.py` e
`cognicao/explicacao_fala_historica.py`. Nenhum executor, configuração, voz,
orçamento ou parser de frases de domínio alterado. O mesmo contrato vale para
conversas sobre qualquer habilidade.

Provas: três REDs antes do candidato; factory instalada sem voz/efeitos;
97 testes aprovados e um ignorado nos quatro módulos focados. Revisão independente
sem bloqueador. Qwen em cinco turnos após o candidato: desapareceu a captura
histórica e o texto interno. Porém repetiu literalmente a resposta anterior,
revelando a fronteira seguinte. Isso não é uma conversa correta integralmente.

## Raiz demonstrada: o contrato perde o esclarecimento em uma consulta composta

A mesma pergunta atômica mantém o ato de esclarecimento. Acompanhada de outra
pergunta, o `fullmatch` da entrada inteira deixa de reconhecê-lo. O contrato
passa a `resposta_direta`, descarta a âncora anterior e aceita sua repetição.
Essa perda foi reproduzida em três variantes antes do candidato. O registro
possui a publicação; não é perda da mensagem nem problema de transporte.

Contrato: o mesmo critério atômico deve alcançar cada fonte literal da
segmentação já decidida pelo interpretador. Não criar outro segmentador.
Consultas sem comandos/execução e sem citações podem projetar o esclarecimento;
segmentos sem vínculo literal não criam o ato. O owner do registro pode recuperar
a referência pelos mesmos segmentos, mas exige uma única publicação e recusa
ambiguidade ou turno estrangeiro. O snapshot continua ligado ao texto integral
e ao turno atual; ele comprova a fala entregue, não sua verdade ou seu efeito.

Produção desta raiz: `cognicao/contrato_fala.py` e
`memoria_mental/registro_semantico.py`. O candidato anterior foi preservado.
O fallback contextual preexistente `ultima_resposta` continua sendo apenas
contexto quando não há snapshot; não chamar isso de publicação comprovada.

Testes cobrem música, aplicativos e estado de IoT, além de citações, terceiro,
segmento adulterado, duas publicações e turno estrangeiro. Revisão independente
sem bloqueador. A segunda coleta Qwen mantém esclarecimento, fonte publicada e
roteiro literal na pergunta composta; não publica os placeholders nem repete
literalmente a primeira resposta nesse turno. A prosa resultante ainda contém
justificativas inadequadas. A fronteira estrutural está GREEN; adequação da
conversa livre continua RED. Não encerrar essa família geral.

## Responsabilidades e validação

- Interpretador/modalidade: segmentação e identidade do ato; nenhuma nova permissão.
- Contrato de fala: obrigações de resposta e âncora, sem fatos ou efeitos inventados.
- Explicação histórica: admissão de suas fontes por ato, sem capturar todo o diálogo.
- Registro semântico: identidade, conteúdo e validade da publicação observada.
- Revisão e autoria: ainda devem produzir uma explicação útil, concreta e apoiada;
  a seleção de um rascunho não é prova dessa adequação.

`auditar.py` registra as três coletas de cinco turnos e transcrições completas,
fontes sem drift, HTTPs, ausência de voz, comandos e efeitos. Os testes finais e
a comparação da regressão ficam nos XMLs e na auditoria de regressão da segunda
pasta. Esses artefatos distinguem histórico, candidato e resultado atual.

Foco final: **207 aprovados e um ignorado**. Regressão ampliada de 100 módulos:
**2.481 aprovados, nove falhas, 44 erros, 14 ignorados, um desmarcado e 30
subtestes aprovados**. A comparação por identidade no XML confirmou os mesmos
nove failures e 44 errors da etapa anterior; não surgiu um caso novo nesse
conjunto. Os 44 errors pertencem à mesma fixture que tenta serializar
`PerspectivaEnunciador` em JSON, com contraprova pré-candidato já preservada
na etapa de categoria. Isso não torna a suíte globalmente verde.

## Limites encontrados e próxima fronteira

O Qwen ainda responde um estilo perguntado com imagens vagas; atribui seu gosto
a causas sem fonte e oscila para negativas como não possuir memória de sons.
`estou falando da musica` não está garantido como correção da pergunta anterior.
O último `como assim?` também recebeu formulação inadequada. Nenhuma dessas
saídas foi contabilizada como acerto só porque houve HTTP 200 e publicação.

A próxima investigação é o contrato de resposta subjetiva: distinguir opinião
autoral, categoria solicitada, experiência alegada, capacidade viva e explicação
da própria fala. A personalidade já pede concretude e permite gostos sem fingir
experiência; repetir isso no prompt não demonstrou resolver o mecanismo.
Não fixar um gênero por frase nem usar o gosto do usuário como gosto da Laylay.

Clipboard ficou fora das coletas para isolar as raízes. A oferta que fala como
se o usuário tivesse citado um erro requer evento/origem/autoridade próprios.
O prazo exibido no log original não reapareceu nessas coletas e não está corrigido
por isso. Resumos diários adiados e limites de voz mantêm suas causas separadas.
Nenhum commit, alteração de modelo/configuração ou shutdown nesta etapa.
