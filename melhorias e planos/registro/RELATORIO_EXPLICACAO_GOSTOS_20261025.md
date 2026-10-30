# Explicação de gostos sem causa inventada — 25/10/2026

## Pedido e base

Pedro autorizou estudar como explicar gostos sem inventar causas, corrigir a
raiz no contrato compartilhado e validar a composição instalada, sem voz e com
ações simuladas. HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, `main`,
worktree suja preservada. Nenhum commit, shutdown, troca de modelo/voz/configuração.

Baseline, status e hashes de 529 fontes estão em
`resultados_testes/explicacao_gostos_20261025/baseline.json`; cópias dos owners
anteriores em `fontes_antes/`. O diff acumulado do HEAD não é este candidato.
As correções anteriores de opinião simples, categoria e esclarecimento foram
preservadas. Não consolidar F1/C5/C7/AUT por semelhança de sintomas.

## Raiz reproduzida

O contrato de opinião anterior sabia declarar uma posição, mas não vinculava
a pergunta posterior sobre o motivo a essa declaração. Na composição real:

1. `você gosta de indie?` → `Eu não gosto de indie.`
2. `por que você não gosta de indie?` →
   `Eu não gosto de indie porque não tenho opinião sobre gêneros musicais.`
3. `você prefere Windows ou Linux?` → `Eu prefiro linux.`
4. `por que você prefere Linux?` → uma explicação afirmando que seria mais leve,
   mais seguro e daria maior controle.

Nenhuma dessas justificativas acompanhava a escolha original. Descrever uma
suposta propriedade de Linux tampouco prova o motivo da escolha. O fluxo
aceitava a explicação livre com base apenas no contexto da preferência.
Um `por quê?` após a escolha de chá apenas repetia a preferência, sem dizer que
não havia motivo vinculado. `baseline_dialogo/` preserva os seis turnos.

Primeira divergência: a leitura/contrato da pergunta de motivo não carregava a
distinção entre a declaração publicada e o apoio de sua causa. O código
retornava à autoria livre. A emissão anterior e o registro de fala estavam
presentes; não era perda da memória, falha HTTP ou indisponibilidade de Qwen.
Todos os pedidos do baseline receberam HTTP 200.

O inventário encontrou posição autoral e publicação qualificada, mas nenhum
owner que registrasse um motivo confiável dessa escolha. Não criar um motivo
a posteriori e chamá-lo de causa histórica. Critério avaliativo adotado agora,
propriedade factual do objeto e motivo original continuam sendo claims distintos.

## Contrato corrigido

`referencias_linguagem` lê a consulta de motivo presente, reaproveitando o
mesmo leitor de opinião para alvo, predicado e negação. Não resolve a fonte nem
decide a causa. Referências pessoais, terceiros, citações, comandos compostos
e perguntas sobre efeitos permanecem nos owners anteriores.

`opiniao_autoral` acrescenta um modo de explicação. A seleção da publicação
continua sendo do registro canônico, com snapshot nativo de texto, identidade
e TTL. A preferência publicada é só a preferência; não comprova sua causa.
Alvo, predicado e polaridade da pergunta devem corresponder à declaração.
Quando correspondem e a fala é uma declaração simples sem motivo, a resposta
preserva a posição e informa que aquela fala não trouxe um motivo.

Exemplo do limite realizado: `Eu prefiro linux. Essa fala não trouxe um motivo
para a preferência.` Isso não afirma que a Laylay não possua causas ou
preferências; delimita o que a publicação examinada permite explicar.

Se a pergunta pressupõe outro gosto, o contrato não cria a preferência nem seu
motivo. Se uma causa livre aparece em uma fala antiga, ela não recebe validade
por ter sido entregue pela IA. O recorte não extrai uma frase parcial desse
texto como se fosse opinião qualificada. Uma pergunta elíptica sem opinião
vinculada permanece com o owner contextual, inclusive após ação/receipt.

Autoria primária, reparo, revisão de qualidade, revisão direta e factual já
consomem esse owner comum. A integração foi reutilizada; não há um parser
particular para indie, Linux ou chá, nem outra isenção factual. Uma explicação
inteira precisa corresponder à realização do contrato. Uma causa acrescentada
continua bloqueada mesmo que contenha um nome ou uma declaração verdadeira.

## REDs e ajustes de diagnóstico

Os testes iniciais reproduziram 11 falhas nas fronteiras e seis controles
aprovados. A expectativa inicial de capturar `por quê?` sem publicação foi
revisada antes do patch: ela confundia elipse com autorização para selecionar
um gosto. O contrato correto não captura um porquê que pode pertencer a outro
ato. Há controles de ausência de contexto e falas sobre luz/arquivo.

A primeira coleta do candidato não ficou GREEN. Qwen entregou a realização
correta, mas o texto novo terminava em `não vou inventar um.`. A higiene
interpretou o pronome final como fragmento incompleto e removeu a segunda frase;
a revisão então rejeitou a preferência sozinha e consumiu as tentativas.
`candidato_dialogo/`, `factory_red.xml` e `factory_diagnostico.json` mostram
HTTP/schema corretos e a primeira fala mutilada que chegou à revisão.

A proteção de higiene não foi alterada nem recebeu exceção por frase. A nova
realização foi formulada com objeto nominal explícito e sem pronome pendurado.
Um teste confere sua passagem integral pela higiene compartilhada; a factory
instalada voltou a publicar a resposta completa. Não misturar essa fronteira
de representabilidade do candidato com indisponibilidade do transporte.

O teste também tenta falsificar a admissão histórica com orações causais curtas.
Uma sequência como `indie porque sim` não deve ser tratada como nome nominal
de gênero nem como prova de uma causa. A mesma qualificação do operando deve
valer na consulta, na produção e na leitura da publicação.

Três REDs mostraram que a gramática anterior aceitava uma oração causal curta
no slot nominal. A qualificação literal foi centralizada no leitor comum e
reutilizada pela leitura da publicação. Conectores de oração e referências
pessoais não recebem a cobertura de um nome nesse recorte; isso não julga a
verdade da possível causa. Controles com nomes compostos e opiniões anteriores
continuam passando. Grafias por que/por quê/porque/porquê compartilham o mesmo
contrato; três REDs dessas variantes foram reproduzidos antes do ajuste.

Outra contraprova com `jazz por relaxar` e `chá para relaxar` falsificou a ideia
de que excluir alguns conectores bastaria. A qualificação para explicar motivo
ficou limitada a objeto nominal simples ou tipo composto já conhecido pelo
léxico existente. Demais nomes compostos continuam sem cobertura para esse
julgamento; não declarar ausência de motivo a partir de uma gramática aberta.
O controle `heavy metal` conserva a declaração e o limite; as duas orações
de finalidade não recebem cobertura (`contraprovas_nominais.json`). Não se trata
de cadastrar cada nova frase causal como exceção.

Produção deste candidato: somente `referencias_linguagem.py` e
`opiniao_autoral.py`. A composição, executores, transporte, higiene e demais
revisores foram reutilizados. O motivo ausente não é completado por pesquisa
de atributos do gênero ou aplicativo: atributo do objeto não comprova o motivo
da escolha da autora.

## Responsabilidades, validação e limites

- Leitor canônico: finalidade e operandos da consulta, sem selecionar causa.
- Registro de fala: identidade e conteúdo realmente publicados, sem verdade externa.
- Contrato autoral: vínculo da preferência e limite de apoio, nunca uma causa psicológica.
- Transporte/captura: preservar a realização integral e sua declaração de suporte.
- Revisores compartilhados: aceitar somente o ato conferido, mantendo as guardas de fatos e efeitos.

As coletas usam `laylay.py` e os componentes instalados de interpretação,
contexto, autoria, revisão e publicação. Persistência isolada, voz bloqueada e
executor simulado. Os resultados não provam recarga da sessão desktop nem
entrega de áudio. Coletas intermediárias permanecem guardadas, sem regravá-las
para parecerem finais.

No candidato final, `entrega_dialogo/` reproduz os seis turnos do baseline.
`entrega_vizinhos/` acrescenta dez turnos: jazz, repetição do porquê, pedido de
clareza, premissa divergente sobre rock, chá e programação. Somam **16 respostas
publicadas e 16 HTTP 200**, uma geração por turno, sem causas inventadas nesse
recorte, sem voz ou ação externa e com as mesmas 529 fontes estáveis durante
cada coleta. A preferência por rock pressuposta pela pergunta não foi adotada como fato:
foi publicado o limite de declaração correspondente ausente.

`entrega_fumaca/` executa três turnos separados de segurança, incluindo o pedido
de abrir Calculadora. O adaptador simulado publicou receipt negativo:
`executou=False`, `confirmado=False`, `ok=False`, `simulacao=True` e
`efeito_real=False`. A resposta posterior conservou a falta de efeito confirmado;
nenhuma janela foi aberta. Não contar esses três turnos como explicações de gosto.

Teste novo: **31 casos**. Foco final: **425 aprovados e um ignorado**, incluindo
os contratos anteriores de opinião, fundamentação, fontes e esclarecimento.
As causas curtas por finalidade, snapshots expirados e as diferentes grafias
da pergunta mantêm controles. Não foi necessária mudança em executor ou voz.

Regressão final em **102 módulos distintos**: **2.565 aprovados, nove falhas,
44 erros, 14 ignorados, um desmarcado e 30 subtestes aprovados**. A comparação
por IDs em `comparacao_regressao.json` confirmou os mesmos nove failures e 44
errors da etapa anterior. Os nomes completos e logs estão preservados: uma
falha conhecida do comando de Calculadora, oito expectativas antigas de pacote/
tokens e os 44 erros da fixture anterior que serializa `PerspectivaEnunciador`.
Não transformar esse resultado em suíte global GREEN nem corrigir outra raiz
para reduzir a contagem.

`auditar.py` verifica schema efetivamente enviado, enum, resposta publicada,
revisão sem prova factual/semântica/autoridade, fonte estável e recibo simulado.
`entrega.json` sela o candidato de dois arquivos. As transcrições finais estão
em `entrega_dialogo/TRANSCRICAO.md` e `entrega_vizinhos/TRANSCRICAO.md`.

Esta correção permite responder honestamente à falta de motivo associado.
Ela não cria retrospectivamente um critério original. Explicações mais ricas
dependem de registrar um critério na própria autoria e conferir o apoio dos
fatos empregados; isso continua separado da preferência escolhida pela IA.
Não alegar compreensão causal universal ou encerramento de coerência geral.
Clipboard, resumos diários e prazos históricos mantêm suas pendências próprias.
