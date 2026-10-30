# Perdão e confiança — continuidade observada e fronteiras de modalidade

Relato anexado por Pedro e journals examinados:

- `C:/Users/pbarr/Documents/Codex/2026-10-28/ch/work/ponte_sessoes/20261029T160228Z-418c4dda`
- `C:/Users/pbarr/Documents/Codex/2026-10-28/ch/work/ponte_sessoes/20261029T160322Z-dd0747e4`

O primeiro contém uma entrada encerrada por erro. O segundo contém 15 entradas,
15 respostas entregues e encerramento normal com `parar`. Nesse segundo journal,
há 20 retornos bem-sucedidos do serviço e nenhuma falha técnica registrada do
modelo. Nem todos esses retornos são chamadas principais: o evento não preserva
o tipo da chamada. Houve elaboração/reescrita adicional em alguns turnos.

Uma das 15 publicações foi a contingência de ação não executada. Portanto,
15 entregas e zero quedas não equivalem a 15 respostas adequadas. Também não
se deve apagar o resultado positivo de continuidade: o debate percorreu os
15 turnos sem precisar reiniciar e terminou pelo comando de parada.

## Proveniência e limite da investigação

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. Base e hashes de 536 fontes congelados em
`resultados_testes/rodada_perdao_20261029/baseline.json` e `base/`.
As duas cópias históricas contêm as mesmas 536 fontes atuais, sem divergência.
Os journals completos, hashes e logs ficam em `sessoes.json` dessa investigação.

Nenhuma fonte de produção, configuração, modelo, orçamento ou executor foi
alterado. Não houve nova conversa com Qwen, voz ou efeito externo. O trabalho
consiste em conferir a rodada, reproduzir fronteiras com funções reais e
autoria fixa, e registrar as próximas causas sem misturá-las às já corrigidas.

## 1. `perdao2-003`: perde-se o vínculo do sujeito na coordenação

Entrada relevante:

> A outra pessoa aceita as desculpas, mas continua sofrendo o prejuízo.

O journal publica `autoriza_execucao=True` e
`texto_operacional=continua sofrendo o prejuízo`. O modelo havia proposto uma
resposta sobre arrependimento e confiança; a publicação virou o aviso de ação
não executada. A proposta do modelo continua sujeita a crítica de conteúdo:
conter frases pertinentes não certifica todo o argumento como correto.

As funções reais reproduzem a cadeia antes de qualquer geração:

```text
oração com sujeito explícito + vírgula/mas + continuação com sujeito elíptico
→ a segmentação toma o trecho posterior como ato operacional independente
→ o vínculo com “a outra pessoa” deixa de participar da classificação
→ “continua ...” satisfaz pedido direto do léxico operacional geral
→ plano recebe autoridade e cobra execução/receipt não solicitados
```

Controles em `fronteiras.json`:

| Entrada | Autoriza execução |
| --- | --- |
| A outra pessoa continua sofrendo o prejuízo. | Não |
| A outra pessoa aceita as desculpas e continua sofrendo o prejuízo. | Não |
| A outra pessoa aceita as desculpas, mas continua sofrendo o prejuízo. | Sim, incorretamente |
| Continua sofrendo o prejuízo. | Sim, no recorte isolado |
| Uma pessoa continua oferecendo risco a outras pessoas. | Não |
| A pessoa sofreu, mas retoma o trabalho. | Sim; ocorrência vizinha a investigar |
| Continua a música. | Sim; controle operacional legítimo |
| Continue tocando a música. | Sim; controle operacional legítimo |

O resultado independe de usar o normalizador instalado. A gramática musical
não reconhece pedido direto na oração inteira; a autoridade surge do caminho
geral após o corte. Isso falsifica uma falha de serviço musical e diferencia
esta causa de `memoria-005`, em que o normalizador altera o infinitivo com clítico.

`controle_antes_diretiva.json` carrega em subprocesso somente os dois owners
anteriores à correção de formato, sem restaurar arquivos da worktree. A entrada
histórica recebe exatamente a mesma classificação e texto operacional antes e
depois daquele candidato. Não há evidência de regressão causada pelo patch de
`Responda em poucas frases`: a fronteira já existia.

Owner responsável pela primeira divergência: segmentação de atos em
`modalidade_turno`, em particular a admissão de fronteira forte a partir da
evidência operacional do trecho direito. O contrato faltante precisa conservar
o sujeito/papel da oração quando a continuação não demonstrar um ato independente.
Não basta remover `continua` do léxico: isso apagaria comandos reais. Também não
basta tratar qualquer gerúndio como conversa, pois `Continue tocando a música`
é um pedido legítimo. A correção não foi aplicada nesta investigação.

## 2. `perdao-001`: recusa genérica antecede o esgotamento de orçamento

A tentativa que caiu na abertura não apresenta erro de JSON ou de contrato
nos eventos do modelo. Registra duas emissões bem-sucedidas e, depois,
`orcamento_bloqueado` com `FATIA_SECUNDARIA_INSUFICIENTE`.

A primeira proposta responde à pergunta, começando por `Acho que é força.`
A segunda transforma a conversa em uma explicação de que não fará análise
ou opinião, alegando seguir o contrato de reparo. O orçamento é a última
fronteira; há uma decisão errada anterior que orienta esse reparo.

No diagnóstico controlado, o contrato de fala classifica a entrada como recusa
com saudação e seleciona `negacao_operacional_sem_efeito`, limitando-a a uma
frase. O primeiro reparo é solicitado por
`resposta_social_desproporcional` e `negacao_operacional_extrapolou`.

A investigação da classificação local demonstrou o mecanismo:

```text
uma oração contém “não”; outra pede “Quero saber o que você pensa”
→ classificar_confirmacao_local procura tokens sem preservar o escopo
→ presença de “nao” e “quero” devolve False
→ modalidade toma isso como “recusa curta explícita”
→ roteiro pede apenas reconhecer não execução, em vez de debater
→ reparos rejeitados consomem o restante do orçamento
```

A função está em `memoria_mental/aprendizado_rotina_musica`, mas é usada pela
modalidade geral. Não é uma falha exclusiva de música. Em
`abertura_confirmacao.json`, `Quero conversar sobre alguém que não pediu
desculpas` também vira recusa, enquanto controles de recusa real como
`Não agora` continuam negativos corretamente.

Algumas formulações de opinião são protegidas por leitores anteriores e não
chegam ao resultado negativo, apesar de o leitor de confirmação devolver
`False`. Esse controle mostra por que não se deve declarar toda frase com
esses tokens quebrada, nem remover os leitores corretos que hoje a protegem.

Owner e contrato a estudar: confirmação contextual versus natureza integral
do turno. Recusar uma oferta ou ação não é o mesmo que mencionar uma negação
dentro de uma conversa. O mesmo princípio exige conferir escopo antes de
conceder confirmação positiva; não adicionar apenas uma exceção para este caso.
Essa causa é distinta da perda de sujeito em `perdao2-003` e não foi corrigida.

## 3. O que a continuidade da sessão principal sustenta

Há evidência textual de continuidade temática e elaboração de objeções:

- `006 → 007`: o usuário aponta que prevenir novos danos não atende sozinho à
  vítima atual; a resposta passa a incluir reconhecimento, indenização e reparo.
- `011`: ao ser explicitamente solicitada a apresentar uma objeção, a Laylay
  questiona a ligação entre punição, proteção e controle. O argumento contrário
  específico aparece na resposta, em vez de apenas concordar com o interlocutor.
- `012 → 013 → 014`: a resposta discute restrições, dignidade e direitos; a
  pergunta solicitada pela iniciativa conversacional permanece ligada ao tema.
- `015`: a publicação responde ao princípio pedido e a sessão é encerrada
  normalmente pelo comando do operador.

Isso demonstra comportamento conversacional nessa amostra. Não prova revisão
de crença durável, validação lógica de todos os argumentos ou independência em
qualquer contexto. A solicitação explícita de objeção e os contraexemplos do
interlocutor fazem parte da evidência. A ressalva do relato sobre acomodação à
última mensagem continua pertinente; sua avaliação exige variações e controles
contrários nos testes de conversa de Pedro, sem transformar resposta da IA em
prova de um estado interno ou de fatos universais.

## Reapresentação controlada: equivalência e limites

`diagnosticar_composicao.py` examina três alvos com os componentes instalados,
respostas HTTP fixas e histórico textual anterior ao turno. Reconstitui o
texto de transporte v5 a partir das partes literais pós-codec registradas.
Não faz nova geração nem reconstrói o prazo gasto na sessão histórica.

O primeiro ensaio manteve atalhos de início/prioridade da composição geral,
que a ponte desativa. Eles responderam antes da LLM e não reproduziram a
abertura. Esse ensaio está preservado em `composicao_contexto_padrao.json` e
não é evidência sobre o comportamento da ponte.

O ensaio seguinte aplica as mesmas portas desativadas, dispatcher sem efeitos,
modo silencioso, origem e contexto de identidade usados pela ponte. Nele:

- `perdao2-003` reproduz autoridade indevida e o mesmo aviso operacional;
- `perdao-001` reproduz o roteiro errado de recusa e a tentativa de uma terceira
  chamada bloqueada. O motivo controlado é limite de chamadas, enquanto o
  histórico termina por fatia temporal insuficiente: não são tempos equivalentes;
- `perdao2-011` publica a objeção preservada em uma chamada, sem efeitos.

O journal não preserva todo o registro semântico nativo. Por isso, concordância
entre um ensaio e o original é evidência de uma fronteira, não replay integral
do processo. A falsa recusa também foi confirmada pelas funções puras antes
de qualquer chamada, e a falha de coordenação ocorre com e sem normalizador.

## Prioridades e situação final

Preservar os IDs existentes e registrar estas ocorrências nas famílias de
autoridade/escopo. Não juntar causas diferentes só porque ambas terminam em
contingência ou orçamento. Próximos contratos candidatos: confirmação com
escopo de ato e fronteira de coordenação com vínculo de sujeito. Os controles
devem proteger negações/recusas reais, pedidos musicais, ordens independentes,
terceiros e citações, com RED antes de candidato e composição real controlada.

`memoria-005`, histórico indevido, recomendação discutida e recuperação de
repetição continuam em seus próprios registros. O novo teste não encerra
essas pendências nem demonstra regressão das diretivas de formato.

Produção alterada: **nenhuma**. Somente artefatos de diagnóstico e registro,
sem commit, nova conversa, Qwen real, voz ou efeitos externos. Os testes de
conversa continuam com Pedro. Auditoria de fontes/journals em `auditoria.json`.
