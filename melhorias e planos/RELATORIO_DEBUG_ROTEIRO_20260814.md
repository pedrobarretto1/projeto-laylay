# Relatório de depuração — roteiro detalhado de 14/08/2026

Artefato auditado:

`resultados_testes/roteiro_teste_laylay-20260814-014103-255977`

## Leitura correta do resultado

O checkpoint terminou com 166 de 166 itens em `respondido`. Isso comprova que o
transporte recebeu uma fala ou um resultado de turno; não comprova sozinho que a
intenção foi entendida, executada ou explicada corretamente. Os campos
`intencao_correta` e `fala_coerente` permaneceram como `nao_avaliado`.

O `terminal.log` contém 168 entradas de usuário e três inicializações da ponte.
Portanto, dois comandos foram reenviados durante retomadas e a execução não foi
uma única sessão contínua. Houve 28 fallbacks de autoria; fallback não significa
necessariamente falha, mas exige validar a coerência da fala produzida.

## Falhas semânticas confirmadas no artefato

1. `Do que eu não gosto?` não possuía consulta determinística de aversões.
2. `O que você consegue identificar nela?` e `Resume o que está aparecendo agora`
   perdiam o contexto visual já capturado.
3. Um arquivo criado como `teste natural` deixava de ser reconhecido quando a
   pessoa o chamava de `teste natural.txt` depois de criar uma pasta. Isso
   quebrava mover, localizar, abrir, fechar e apagar em cascata.
4. `Tenta abrir ele` não era uma forma aceita de abertura contextual de arquivo.
5. A consulta de caminho podia receber uma reescrita criativa que removia o
   caminho real observado.
6. Duas perguntas idênticas consecutivas podiam receber exatamente a mesma fala.
7. O status `conteudo_acrescentado` não fazia parte do contrato central de
   confirmação. Assim, uma fala dizendo `criei o arquivo` podia esconder que a
   operação real apenas acrescentou uma linha.
8. Uma listagem antiga de playlist podia ser aceita como confirmação de que uma
   música acabara de ser adicionada.

## Correções aplicadas

- Consulta `LEARNING_QUERY` com polaridade negativa, mantendo somente aversões
  confirmadas e admitindo a ausência de memória sem inventar um gosto.
- Continuação `VISION_QUERY` ampliada para as duas formulações exatas do roteiro.
- Equivalência contextual segura entre `nome` e `nome.txt` somente quando um
  caminho real recente já foi observado. A política de criação sem extensão não
  foi alterada.
- Abertura contextual aceita `tenta abrir ele` e continua exigindo um arquivo
  concreto conhecido.
- `FILE_SEARCH` passou a preservar literalmente caminhos e listagens observados.
- Antirrepetição literal só atua quando o histórico prova duas entradas de
  usuário iguais; ela não reescreve respostas válidas por mera coincidência.
- `conteudo_acrescentado` passou a ser resultado confirmado e ganhou raízes de
  fala próprias, diferentes de criação e sobrescrita.
- Contrato de `playlist_musica_adicionada` agora exige verbo de adição/salvamento;
  o substantivo `playlist` sozinho não prova a operação.

## Problemas históricos já cobertos pelo código atual

As falhas de busca web seguida de `abre o primeiro resultado`, maximização e
organização de janelas, fechamento tipado de arquivo versus VS Code, perguntas
hipotéticas tratadas como comandos, restauração sem exclusão vinculada, retry em
ato social e contaminação da caixa de entrada já possuíam regressões atuais. Elas
foram revalidadas na bateria integrada, sem receber implementações duplicadas.

## Limites externos e dados legados

- Falha de controle de mídia sem confirmação do Chrome deve continuar sendo
  relatada como falha; não pode virar sucesso presumido.
- Dispositivo IoT indisponível continua dependente de rede e resposta física.
- O lembrete antigo contaminado com a pergunta sobre o presidente ainda pode
  existir na persistência do usuário. A origem da contaminação foi corrigida,
  mas este relatório não apaga dados pessoais sem autorização explícita.
- Para comparar a próxima execução, usar o checkpoint como transporte e os
  planos/resultados como evidência operacional; `respondido` isoladamente não é
  uma métrica de acerto semântico.

## Validação após as correções

- 155 testes dos módulos diretamente alterados: aprovados.
- 158 regressões integradas do roteiro e domínios vizinhos: aprovadas.
- Suíte completa: **2792 aprovados + 45 subtestes aprovados**.
- Ruff, `py_compile` e `git diff --check`: aprovados.

