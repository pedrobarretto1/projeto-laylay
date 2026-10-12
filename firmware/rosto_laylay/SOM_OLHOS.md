# Expressão com olhos e sons curtos

Montagem validada por Pedro: GPIO6 → resistor de 220 Ω → falante de 8 Ω
e aproximadamente 0,2 W → GND. GPIO5 não é utilizado. Esta montagem
tem volume baixo; nenhum aumento de corrente foi aplicado.

O perfil diário usa USB, `LAYLAY_WIFI=0`, `LAYLAY_SOM_PONTE=0` e motores
conforme a configuração existente. O antigo bip de 2 segundos saiu do
boot normal; permanece disponível apenas no build de diagnóstico
`LAYLAY_BIP_TESTE_INICIO=1`.

O rosto não desenha boca. O campo legado de fala no pacote FACE permanece
por compatibilidade, mas a Laylay envia zero. A voz no PC continua normal.
Os gestos de companhia leem a fala diretamente da mente; não dependem
de uma boca renderizada. Olhos, sono, rubor, lágrima, hack e glitch mantidos.

`SCAPS 1 <sessao>` negocia `SOM1`. Depois de um FACE confirmado, a saída
expressiva envia `SOUND 1 <sessao> <sequencia> <tipo>`:

| Tipo | Momento | Som |
|---|---|---|
| 0 | Primeiro despertar/conexão no processo | Duas notas ascendentes |
| 1 | Sucesso recente publicado pelo owner canônico | Três notas ascendentes |
| 2 | Falha recente observada de execução | Duas notas descendentes |
| 3 | Alegria/deboche marcante | Par agudo |
| 4 | Tristeza marcante | Par descendente suave |
| 5 | Raiva/irritação marcante | Três notas curtas |
| 6 | Vergonha marcante | Dois piados com pausa maior |
| 7 | Surpresa marcante | Par agudo curto |

A seleção usa os sinais certificados de AtividadeOperacionalRuntime e a
projeção emocional causal existente. Não interpreta a resposta da LLM.
Falha prevalece sobre sucesso na mesma amostra. Mudanças emocionais exigem
nível 2 ou 3; calma/retorno à calma não emite bip. Eventos são consumidos
antes do envio, com intervalo de 2 segundos e sem fila/replay na reconexão.

O firmware valida sessão/FACE vigente, sequência e tipo; limita o intervalo
também localmente, usa canal4 separado dos motores, termina em até450ms
e deixa GPIO6 em LOW. Falha de som não transforma uma ação em falha nem
invalida o rosto. SOUNDACK confirma aceitação e início da sequência,
não conclusão auditiva nem receipt da ação externa.

O diagnóstico vivo `mental.rosto_oled.som` e o catálogo descrevem o suporte.
Não há novo comando verbal privado de som, memória durável de eventos ou
concessão de movimento. Mudanças solicitadas de emoção continuam passando
pelo canal canônico; os bips são uma saída dessa emoção.
