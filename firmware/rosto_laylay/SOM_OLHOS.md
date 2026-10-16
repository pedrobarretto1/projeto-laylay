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
| 8 | Envio sem observação do efeito, com ENVIO1 | Uma nota neutra de 80 ms |

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
`SENCAPS 1 <sessao>` negocia `ENVIO1`. Só após essa resposta o cliente pode
enviar `SOUND 1 <sessao> <sequencia> 8`: uma nota neutra de 1550 Hz por 80 ms.
Ela sinaliza receipt de execução enviada sem estado final observado; não
confirma sucesso. Firmware sem ENVIO1 continua com os sons anteriores.
Não há novo comando verbal privado de som, memória durável de eventos ou
concessão de movimento. Mudanças solicitadas de emoção continuam passando
pelo canal canônico; os bips são uma saída dessa emoção.

## Sono com variações locais

O reflexo local dos sensores usa quatro contornos internos adicionais: susto,
medo hesitante, resmungo de irritação e pergunta de busca. Não são novos tipos
aceitos pelo comando SOUND (que conserva0..8). A afinação varia até4%, com
o mesmo duty128/255, canal4, resistor220Ω e duração absoluta450ms. Não aumenta
a corrente para dar personalidade. Som de sono permanece com duty10/255.

`sono_vivo.h` alterna sono tranquilo com sorrisos de olhos fechados,
pálpebras assimétricas e pequenos movimentos de olhar sob as pálpebras.
Os intervalos, a respiração e as viagens dos Zs variam. São animações
decorativas: não representam sonhos narrados, novas emoções mentais ou
sensações medidas. O morph de acordar/adormecer mantém seus três segundos.
Pálpebras usam cobertura fracionária com dither espacial estável; Zs têm
entrada/saída gradual. Repouso solicita frames a cada 20 ms, respeitando
o tempo real do display; o modo diurno conserva seus 33 ms.

Sem FACE/sessão, o firmware pode emitir um único murmúrio de 65 ms no GPIO6:
primeiro após 55–90 s, depois a cada 65–120 s. Duty 10/255, comparado a
128/255 nas melodias diurnas; o volume percebido precisa de conferência no
falante. Não modifica o circuito ou o resistor. HELLO interrompe esse som,
e ele não consome sequências/receipts nem ocupa o cooldown das ações.
Nenhum sonho chama o executor de movimento. A ponte permanece em repouso.

Validação: `validacao_host/validar_sono_vivo.cpp` executa o loop real por
quatro minutos com o dublê de hardware, verifica ausência de PWM nos motores,
sons finitos/espaçados, reconexão prioritária e passagem pelo wrap de millis.
Som/olhos, expressões diurnas e transições de presença têm regressivos próprios.
