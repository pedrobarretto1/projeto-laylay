# Consulta da relação entre descrição e critério — 25/10/2026

## Escopo e base causal

Pedro autorizou continuar o plano após fundamentar critérios sem promover
proposta da IA a prova. Esta raiz é a **seleção da finalidade avaliativa da
pergunta**. O bloqueio anterior de serialização foi reproduzido e corrigido
separadamente; não considerar os dois defeitos uma única causa.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, `main`, worktree suja
preservada. Base/hashes em `resultados_testes/relacao_criterio_20261025/`;
`base_apos_projecao.json` congela a primeira correção antes deste candidato.
Sem voz, efeito externo, commit ou mudança de modelo/configuração.

## Raiz demonstrada

Após corrigir somente a projeção, `candidato_dialogo/` mostrou HTTP200 e
publicação para todos os turnos. Mas as três perguntas seguintes receberam:
"Essa fala foi entregue, mas não tem resultado operacional vinculado..."

- `essa descrição justifica o seu critério?`
- `por que esse critério?`
- `qual a relação entre essa descrição e o seu critério?`

Fonte publicada, código de critério e descrição estavam presentes. Não era
mais falha do modelo, JSON ou persistência. O construtor de contrato escolhia
o owner de causa/resultado de ações porque havia uma fala recuperada. A pergunta
era sobre a relação de uma avaliação, e não sobre execução. A fala anterior
também não continha uma regra que demonstrasse essa adequação; seria indevido
criar uma agora e chamá-la de motivo original.

`owner_red.xml` reproduziu cinco variantes da primeira transição incorreta;
cinco controles de terceiros, operação adicional, citação e execução já não
recebiam esse novo recorte. A existência da publicação foi verificada antes
do julgamento. Recuperação correta não prova finalidade correta, e ausência
de receipt operacional não responde a pergunta sobre critério.

## Contrato e responsáveis

1. `referencias_linguagem.consulta_relacao_criterio_autoral` lê a consulta
   integral: sujeito deítico de descrição/fonte/informação, predicado de
   apoio/relação e objeto de critério próprio; também lê a pergunta de porquê
   desse critério. Não resolve fonte, comprova regra ou concede autoridade.
   Não captura terceiro, citação, operação ou complemento adicional.
2. `opiniao_autoral` exige critério **nativo**, publicação e origem vigentes
   no registro canônico. Um dict serializado, fonte ausente, origem alheia ou
   snapshot expirado não escolhem esse owner. Não se usa apenas a palavra
   "critério" nem uma sugestão do modelo como evidência.
3. `contrato_fala` decide esse objeto avaliativo antes de atribuir causa/efeito
   operacional à fala observada. As guardas de autoridade, revisão de alegação
   anterior e dos demais contratos permanecem. O histórico genérico continua
   atendendo perguntas de execução com seus próprios receipts.
4. O modo `relacao_criterio` reutiliza schema fechado, autoria, reparo e
   revisores compartilhados de opinião. Preserva posição, critério e descrição
   vigente com atribuição. Informa que **não foi registrada uma regra** mostrando
   como a descrição atende ao critério; a citação não comprova essa relação ou
   uma causa psicológica. Não cria regra posterior, experiência ou propriedade.
5. Publicação e continuidade conservam a origem e o TTL do critério. Fonte
   vencida deixa de ser exibida como base vigente, mas não impede explicar o
   limite do critério. A descrição JSON continua sem poderes de credencial.

O ato integral `relação entre X e Y` contém um `e` que o segmentador pode
representar em dois fragmentos. A leitura fechada deste ato não trata essa
coordenação nominal como dois pedidos. Não foi afrouxado o segmentador geral:
o fullmatch da consulta e as guardas de autorização/comandos continuam exigidos.
O RED específico desse caso permaneceu guardado antes do ajuste.

## Provas e limites

Dezessete testes novos cobrem cinco perguntas, cinco controles de outros atos,
quatro fontes inválidas, repetição com origem preservada, expiração de base e
factory instalada em três domínios. Os onze testes da projeção anterior são
separados. Total local integrado:28 aprovados. Foco final:265 aprovados e dois
ignorados, incluindo opinião, fonte, histórico e correção. Revisão independente
rodou187 controles locais e o composto instalado; nenhum bloqueador no recorte.

Coletas finais com Qwen real e composição de `laylay.py`:

- `candidato_relacao/`: seis turnos/seis HTTP200/publicações/persistências.
  Os três turnos antes silenciosos, depois respondidos como execução, agora
  explicam o limite da relação avaliativa.
- `entrega_vizinhos/`: dez turnos/dez HTTP200/publicações/persistências em
  software e bebidas, com seis consultas avaliativas. Fonte/posição/origem
  continuam associadas à emissão original na repetição.
- `entrega_fumaca/`: três turnos separados; um APP_OPEN recebeu somente receipt
  negativo do adaptador real com executor simulado. Nenhuma aplicação foi aberta.

As páginas HTTP de pesquisa são **sintéticas**, com cenário simulado expresso
no conteúdo; coletores, Qwen, contratos, revisão, registro e armazenamento são
instalados. São16 turnos finais, nove consultas avaliativas e530 fontes de
código estáveis por coleta, sem voz/efeito externo. Não apresentar isso como
pesquisa factual real sobre indie, Linux ou chá.

Os três turnos didáticos iniciais conseguiram fontes mas publicaram o limite
de apoio. Permanecem fora do encerramento. Algumas verificações também
registraram aviso de proporção da resposta, preservando integralmente o texto
do owner; `entrega.json` conserva esses avisos. Não declarar conversa global
natural ou ausência de qualquer aviso a partir da aceitação deste contrato.

`auditar.py` compara baseline silencioso, candidato só de projeção, candidato
avaliativo, HTTP original, realização literal, publicação, origem, flags de
prova falsas e persistência gravada/relida. Diffs separados por raiz, hashes,
ampla relevante e comparação de falhas anteriores por identidade estão no
manifesto. Nenhum teste isolado substitui essas coletas.

Regressão ampla relevante em **113 módulos distintos**: **2.858 aprovados**,
nove falhas,44 erros,14 ignorados,um desmarcado e30 subtestes aprovados. A
comparação final confirmou exatamente os mesmos IDs das nove falhas e44 erros
da entrega anterior. Permanecem a falha antiga de comando natural Calculadora,
oito expectativas antigas de pacote/tokens e44 erros da fixture ao serializar
`PerspectivaEnunciador`. A lista individual está em `comparacao_regressao.json`;
nenhum desses REDs foi apagado ou contado como corrigido. Os28 testes novos
das duas raízes estão aprovados também nessa execução ampla.

Produção desta raiz: `referencias_linguagem.py`, `opiniao_autoral.py` e
`contrato_fala.py`. A outra raiz altera somente `registro_semantico.py`.
Executores, voz, modelo, pesquisa e armazenamento foram reutilizados. Nenhum
commit. F1/C5/C7/AUT, clipboard, prazo e worktree paralela preservados.

A etapa prova a interpretação dessa consulta contextual e o limite da evidência
existente. Não prova adequação do critério, sentimento ou causa; não introduz
preferência durável. A próxima fronteira para relações mais informativas é
declarar uma regra avaliativa na autoria, com condições conferíveis e alcance
explícito, sem transformar sua proposta em prova nem criá-la retrospectivamente.
