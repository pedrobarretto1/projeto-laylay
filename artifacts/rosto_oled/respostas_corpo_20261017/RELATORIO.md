# Reações da IA ao corpo — investigação de 17/10/2026

Baseline: `ca592a9609dd1865b63b22c714f8d3e802fa2a5c`, branch `main`.
Worktree e hashes preservados em `baseline.json`; alterações de transporte,
companhia, firmware e documentos já existiam antes desta investigação.
Nenhum arquivo de produção foi alterado, nenhum commit criado.

## Evidência da sessão real

Sessão completa `ba710e67`, iniciada às 13:47:35. Leitura do DEV pela interface
já conectada, sem derrubar a ponte, reiniciar a Laylay ou enviar movimentos.
O modo normal ocultava os motivos de bloqueio; DEBUG tornou os registros
anteriores visíveis. Evidências sanitizadas em `dev_normal.txt` e `dev_debug.txt`.

1. **13:47:51.601:** evento corporal entrou na cognição. Payload chegou ao modelo.
2. **13:47:58.918:** resposta admitida pelo porteiro, tipo `presenca_corporal`,
   pontuação 72, status `agendada`.
3. **13:48:00.049–.050:** texto publicado na conversa:
   “Meu sensor frontal acabou de sentir algo a menos de 10 centímetros e não foi nada divertido.”
4. **13:48:00.463:** áudio falhou com `WSServerHandshakeError`, HTTP **429**,
   serviço Microsoft TTS. O texto foi preservado e a voz não foi trocada.
   Publicação textual não comprova reprodução sonora. Não sabemos por estes
   registros a causa remota do 429, nem se corresponde à ocasião ouvida pelo usuário.
5. **13:48:14.301:** outro evento corporal entrou na cognição e no modelo.
6. **13:48:20.196:** segunda geração chegou à porta de voz, mas foi descartada:
   `intervalo adaptativo de 120 segundos ainda ativo`, pontuação 37,
   `bloqueada_porteiro`. Não foi falta de percepção nem ausência de geração.
7. Persistência de aprendizagem contém 16 marcos sensoriais entre 13:47:42 e
   13:48:59. Há novos incidentes de obstáculo e de ausência de retorno inferior.
   Logo, a hipótese de ausência geral de eventos corporais é falsificada.

## Contratos que explicam o silêncio

### Intervalo de admissão — provado nesta sessão

`PorteiroProatividadeRuntime.avaliar` aplica 120 s ao tipo `presenca_corporal`.
Ele atualiza `ultima_emissao_ts` quando **admite** a fala, antes do receipt de
reprodução. Assim a falha TTS das 13:48:00 não elimina o intervalo iniciado às
13:47:58. A segunda reação foi descartada 21,278 s depois daquela admissão.

Há uma questão arquitetural a deliberar: o contador hoje representa admissão,
apesar do nome de emissão. Uma eventual alteração deve distinguir reserva da
fila, texto publicado, áudio confirmado e falha, para todas as fontes que usam
esse porteiro. Não basta mudar um número ou autorizar retentativas infinitas.

### Agrupamento de assunto — provado no código e reproduzido offline

`CoordenadorOportunidadesRuntime` deduplica por domínio, tipo, assunto, ação e
objetivo durante **300 s**. O ID individual do episódio não participa dessa
assinatura semântica. Consequentemente novos obstáculos podem ser agrupados
com um obstáculo anterior; a ausência de retorno inferior forma outro grupo.

`reproduzir_filtros.py` usa os episódios reais persistidos com produtor,
estado compartilhado, diretor, coordenador e porteiro reais. Modelo e
reprodução ficam excluídos; a falha sonora é uma entrada histórica explícita.

- Primeira seleção: incidente 10, assunto `protecao:obstaculo`.
- Segunda: incidente 13, assunto `protecao:borda_sem_retorno`; assunto distinto
  passa pelo coordenador, mas para no intervalo do porteiro.
- Ciclos aproximados seguintes selecionam incidentes 17, 19 e 21: todos são
  bloqueados por `ignorar_duplicada_semantica`, antes de nova geração.
- Controle após cinco minutos: o mesmo assunto volta a ser admitido.
- Sem receipt de áudio, o diretor conserva zero emissões sonoras.

**Limite:** ciclos posteriores são aproximações de 15 s; o DEV não registra a
decisão individual de todos os bloqueios cotidianos. O replay sustenta essa
explicação para os episódios seguintes, mas não prova cada decisão histórica.
O banco guarda marcos, não todas as leituras. Ausência de um novo marco não
significa ausência de leitura viva.

### Orçamento do diretor — existente, não demonstrado como causa desta sessão

Depois de uma entrega de presença confirmada, o perfil adaptativo limita o
domínio cotidiano a uma intervenção em 20 min, além de variedade/categoria e
orçamento global. Comentários corporais usam `categoria=companhia` e passam
por essas mesmas regras. Como a primeira reprodução falhou, não atribuímos
esse bloqueio ao caso observado sem outro receipt.

## Hipóteses distinguidas

- Ausência geral de sensor: falsificada pelos episódios persistidos e DEV.
- Modelo nunca recebe eventos: falsificada por duas gerações reais.
- Antigo bloqueio de prioridade do próprio plano: não reproduzido na sessão;
  os dois eventos passaram da cognição ao modelo e à porta de voz.
- Sombra/timeout do modelo: não explica essas duas tentativas.
- Falha sonora: demonstrada para a primeira tentativa atual.
- Segundo comentário barrado por política: demonstrado no DEV.
- Duplicação semântica nas demais: código + replay, sem prova individual viva.

## Validação e próxima fronteira

Replay executado com sucesso: `replay_filtros.json`.
Regressivos: **56 passed** em 2,14 s:
`test_manuseio_fofo`, `test_red_p1e_recibo_entrega_presenca`,
`test_porteiro_proatividade`, `test_presenca_conversa_ociosa`.
Isto confirma contratos locais existentes; não é correção nem GREEN de nova
reprodução sonora no runtime.

Recomendação: discutir uma política compartilhada de reações a episódios
observados, distinguindo mudança significativa de repetição do mesmo estado.
Coordenador e diretor continuam os donos do orçamento e variedade; o porteiro
preserva prioridade humana e validação de entrega. Evitar um canal corporal
que contorne essas proteções. A falha 429 é uma fronteira separada, a validar
com a voz atual antes de qualquer alteração de transporte ou fallback.

Calibração N20, motores, firmware, configurações de voz e música não foram
alterados. A permissão para pausar música não precisou ser usada.
