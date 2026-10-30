# Uma identidade de entrega não admite dois players — 25/10/2026

Base HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`;
worktree preservada e fonte anterior em
`resultados_testes/dialogo_jogos_musica_20261025/fontes_antes/voz_runtime.py`.
Este contrato não atribui a causa do episódio físico relatado por Pedro.

## Raiz demonstrada

O log histórico contém uma publicação textual; Pedro ouviu repetição depois de
alguns segundos. Sem identidade do item e recibo do player daquela execução,
não existe prova de qual publicação provocou o segundo áudio.

O teste controlado encontrou uma vulnerabilidade independente e reproduzível:
`falar()` deduplicava por texto, janela curta e chave ambiente. A mesma
`RetratoEntregaFala.mensagem_id`, já reproduzida, podia ser readmitida após mudar
`ultima_entrada_ts`. Avançar apenas o relógio, mantendo a chave, não bastava.

Falsificadas como explicações gerais: uma única emissão duplicar necessariamente
o worker; o bloqueio falhar com chave ambiente estável; necessidade de proibir
todo texto repetido. Retry 429 ocorre na síntese antes do player; a thread do
restante sintetiza, não reproduz; o caminho instalado não habilita fallback local.
Essas leituras não substituem correlação do evento físico histórico.

## Contrato e owner

Owner único: `mente_laylay/personalidade/voz_runtime.py`. A identidade nativa
fica admitida uma vez durante a vida do runtime, a partir da retirada pelo
worker. `_turno_lock` protege admissão, congelamento da candidata e revalidações
antes da fila. Mudança da chave ambiente não cria outra ocorrência.

Uma duplicata concorrente já enfileirada não chama player ou callback novamente,
mas libera `done_event`. Uma candidata pode ser substituída antes da admissão.
Cancelamento antes do worker não consome a identidade; repetição explicitamente
pedida com nova identidade continua válida. Falha conserva receipt negativo.

## Validação

`test_voz_repeticao_tardia_diagnostico.py` usa `VozRuntime`, fila, worker e
`reproduzir_fala` reais, com transporte, dispositivo, decodificador e relógio
controlados. Não importa main nem toca áudio. São conferidos síntese, player e
callback separadamente; texto repetido com nova identidade é controle positivo.

RED expandido: seis falhas e quatro controles. GREEN: **63 testes**, incluindo
recuperação 429, filas isoladas, configuração e regressivos P18/P19. O foco
conjunto posterior também executa esta raiz. XMLs `voz_red.xml`, `voz_green.xml`,
`foco_final.xml`; diff separado `voz.diff`. Sem trocar voz, fallback ou modelo.

Alcance: prova de idempotência do pipeline com portas controladas. Não prova
áudio físico, não cobre publicações com nova identidade nem reinício do runtime.
Repetição histórica continua sem causa atribuída. Nenhum commit ou efeito real.
