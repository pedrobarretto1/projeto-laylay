# C5 — proposição integral antes das partes de transporte — 28/10/2026

Correção aplicada no contrato compartilhado de autoria livre. O host conserva
a proposição completa recebida e divide apenas sua representação de transporte.
Não completa palavras, inventa continuação ou certifica conclusão semântica.
É continuação da integridade de autoria de C5; C5/C7 não ficam globalmente encerrados.

Atualização posterior das30 falhas/44 erros aqui registrados:
`RELATORIO_REGRESSAO_74_20261028.md` confere o fechamento dos mesmos74 IDs.
Os números e artefatos abaixo permanecem como evidência histórica desta etapa.

## Base e primeira fronteira

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, `main`, worktree suja
preservada. Estado Git e hashes de 532 fontes congelados em
`resultados_testes/integridade_autoria_livre_20261028/baseline.json`.
Os dois arquivos alterados foram copiados e conferidos contra essa base.
Nenhum commit, configuração, modelo ou voz alterados.

Na coleta real anterior do cenário do robô, o HTTP contém JSON válido com
uma unidade de **exatamente 500 caracteres**, terminando em “gest”. O provedor
registrou `finish_reason=stop`, 175 tokens de conclusão e teto de 1.024 tokens.
A publicação reproduziu esses mesmos 500 caracteres. Outra amostra também
atingiu 500, mas tinha erro adicional de formato; não é usada como prova de
documento válido. Esse erro continua separado.

```text
schema exige que o texto da proposição caiba em 500 caracteres
→ modelo encerra o campo no teto, mesmo com palavra/ideia cortada
→ documento pode ser JSON válido e terminar em stop
→ captura confere forma e cobertura dos caracteres recebidos
→ revisão/publicação preservam o texto já cortado
```

Primeira fronteira demonstrada: **negociação da autoria usa o limite de uma
parte de transporte como limite da proposição**. O writer era o mesmo da
base congelada, confirmado por hash. A regra de 500 não foi apagada: continua
útil no transporte e na captura legada. O problema era seu uso antes de a
proposição estar completa.

Hipóteses falsificadas no caso principal:

- O corte não surgiu no renderer, na voz ou na publicação: já está no HTTP.
- O provedor não encerrou pelo teto de tokens naquele caso: `stop`, abaixo
  do orçamento. Não se usa essa conclusão para todos os tipos de truncamento.
- Não falta simplesmente aumentar o orçamento global: a representação anterior
  já permitia fala de 4.000 e oito partes de 500; faltava distinguir a proposição
  das suas partes sem inventar novas afirmações ou redistribuir suas fontes.
- O wrapper da sonda registra `retorno.text` integral e não corta o HTTP.

A nova coleta baseline de quatro turnos não reproduziu corte: os textos ficaram
abaixo de 500, com a orientação curta da etapa anterior. Isso não foi contado
como RED nem escondido. O diagnóstico usa a amostra histórica real, o mesmo
writer e os REDs canônicos de representação.

## Contratos e owners

| Responsabilidade | Owner | Contrato |
| --- | --- | --- |
| Negociar autoria livre | `cognicao/suporte_autoria.py` | Texto de uma proposição pode ocupar o limite global já existente; não é obrigado a caber numa parte de transporte. |
| Materializar transporte | Mesmo owner | Até oito partes totais de até 500, resposta de até 4.000, envelope de até 32.000. Divisão somente em espaços reponíveis, com reconstrução literal integral ou recusa. |
| Capturar e revisar fonte | Mesmo owner, revisão existente | Grupo continua uma proposição, com texto/intervalo completos e as mesmas fontes/ausência declarada. Revisor confere o todo, sem aprovar fragmento separado da ressalva. |
| Preservar alvos e recuperação | Mesmo owner e `autonomia/processamento_resposta_ia.py` | Codecs livres/referenciados/por ato V5 preservam inventário e IDs. Adaptador de reescrita reconhece a nova versão, sem fallback permissivo. |
| Validar execução | Owners existentes | Autoridade, validação operacional, receipts e efeito não são concedidos pela representação textual. |

No envio ao modelo, a unidade continua com `texto` e suas referências. Para
uma proposição longa, a projeção canônica do host guarda `partes` no mesmo
grupo; seu join deve reconstruir o texto exatamente. A declaração normalizada
usada pela revisão guarda o texto integral, não supostas proposições descobertas
pelo particionamento. Formato não prova verdade nem suporte semântico.

Realizações finitas dos owners conservam seus codecs e a sequência literal
contratada. A captura legada de `texto` maior que 500 continua recusada: o
limite novo da emissão não torna qualquer envelope antigo válido. Fontes fora
do inventário, partes inviáveis, ambiguidades de âncora, excesso de capacidade,
falta de cobertura e comandos fabricados permanecem recusados.

Produção alterada somente nos dois owners citados. A regra útil de proporção,
os revisores de fonte/histórico, o transportador HTTP, composition root e
executores não foram alterados. Reservas de tokens e orçamento global mantidos.

## RED e controles

RED canônico: **seis falhas e dez controles aprovados**. O codec real não podia
transportar proposições livres de 510 a 3.400, embora a fala inteira coubesse
no limite global. Os testes alcançaram a fronteira de representação correta.

O módulo novo `scripts/tests/test_integridade_autoria_livre.py` tem **18 casos**:
preservação integral, limite de partes/total, fonte/ausência intactas, revisor
vendo a proposição inteira, fragmento sem ressalva não aprovado, envelope
legado, forma inválida, montagem e inventário na recuperação.

Testes existentes foram atualizados por mudança explícita de contrato:
nomes V5 nos caminhos livres/por ato; e o snapshot de 850 antes recusado como
uma única unidade agora deve reconstruir-se integralmente em partes de até
500. As restrições de fonte e o limite de transporte continuam sendo testados.
Não se alterou o teste para admitir corte, coerção ou referência falsa.

O primeiro candidato também mostrou uma guarda do adaptador que só reconhecia
os nomes anteriores, perdendo a negociação nas reescritas. Os controles ficaram
RED até o adaptador admitir explicitamente V5; não se enfraqueceu a validação.
Foco final: **221 aprovados e oito ignorados**, incluindo fontes, reescrita
instalada, alvos por ato e restrições operacionais.

Regressão em **132 módulos**: **3.390 aprovados**, 30 falhas e 44 erros com
exatamente os mesmos IDs da execução anterior; 14 ignorados, um desmarcado,
um xfail e 30 subtestes aprovados. A suíte ampla continua sem GREEN integral.
As 21 falhas históricas adicionais já comprovadas na base da etapa anterior
continuam entre essas 30, sem reclassificação nesta etapa.

## Composição instalada

Mesma composição raiz e serviços reais, `qwen3:4b-instruct`, perfil isolado,
sem voz e com ações simuladas. Nenhuma fonte proposta pela IA vira prova.

- `baseline_dialogo`: quatro publicações/HTTP200, sem corte reproduzido nessa
  amostra curta; limitação histórica de 500 ainda presente no schema.
- `candidato_dialogo`: oito publicações/seis HTTP200, incluindo proposição
  única de **1.243 caracteres**, conservada em três partes internas. Essa
  coleta antecede apenas a correção de compatibilidade no adaptador de reescrita.
- `final_dialogo`: oito publicações/seis HTTP200. Proposições únicas de **531,
  561 e 797 caracteres** preservadas do HTTP até codec, publicação e registro
  observado, todas com final textual pontuado. Partes de até 500; referências
  intactas; uma proposição não vira várias alegações independentes.
- Controle factual conserva obrigação de fonte. Calculadora recebe receipt
  negativo simulado (`executou=False`, `confirmado=False`, `ok=False`) e fala
  de não execução. Consulta posterior mantém limite histórico, sem nova ação.

## Limites preservados

Preservação literal não é prova de que toda frase tenha sentido completo.
Uma IA pode parar antes da conclusão, repetir conteúdo ou produzir trecho
inadequado mesmo sem atingir o teto do campo. Essas fronteiras continuam abertas.
Fim por limite global de tokens também é distinto do caso comprovado com
`stop`; não se declara corrigido por esta mudança. Orçamento e tentativas
auxiliares bloqueadas observadas nas coletas permanecem registrados.

Uma proposição com palavra indivisível maior que 500, ou que não caiba em oito
partes sem alterar caracteres, é recusada. Não há corte para fazê-la passar.
Não se certificam conversa longa, consciência, áudio, ações reais ou F1/C7/AUT.

Artefatos, hashes, diffs exclusivos e auditoria reproduzível:
`resultados_testes/integridade_autoria_livre_20261028/auditar.py`.
A auditoria passou: 532 fontes conferidas, só os dois owners declarados
alterados, snapshot final estável, texto integral conservado no HTTP/codec/
publicação/registro e IDs de regressão comparados. `git diff --check` passou
nos arquivos de produção. O plano e o mapa causal foram atualizados com esse
recorte, sem encerrar compreensão geral ou outras raízes.
