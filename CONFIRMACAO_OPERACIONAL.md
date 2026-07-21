# Confirmação operacional da Laylay

Este contrato impede que “comando enviado” seja narrado como “ação concluída”.
O catálogo executável fica em `mente_laylay/especialistas/capacidades.py`; cada
intent declara a evidência que seu executor consegue oferecer.

## Tipos de confirmação

- `estado_observado`: o estado final é relido, como arquivo existente, aba aberta ou IoT.
- `persistencia_local`: o armazenamento confirma criação, alteração ou cancelamento.
- `retorno_dados`: uma consulta retorna dados válidos; não representa mutação do mundo.
- `estado_local`: uma pendência ou contexto interno é relido depois da alteração.
- `variavel`: algumas rotas confirmam e outras apenas enviam, especialmente PC B e teclas globais.
- `indisponivel`: o executor atual não consegue observar o resultado final.

## Regra de fala

`executou=True` significa somente que o executor aceitou ou enviou a operação.
Uma fala conclusiva exige `confirmado=True`. Sem isso, o resultado recebe
`estado_confirmacao=nao_confirmado` e a Laylay deve dizer que enviou ou tentou,
mas não conseguiu confirmar o estado final.

Essa regra vale igualmente para programas, navegador, mídia, arquivos, IoT,
agenda e serviços. Intents com confirmação `variavel` são decididos em cada
execução, de acordo com a rota e a evidência realmente recebida.
