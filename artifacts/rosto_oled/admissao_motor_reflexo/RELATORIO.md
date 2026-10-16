# CORPO-ADMISSAO-PROTECAO-01 — disputa entre reflexo e MOTOR

Data local: 14/10/2026. HEAD/main d850b8c90cc5ce40bd4832e759ed991ba88cd5cc. Estado inicial completo em status_inicial.txt e fontes causais em baseline/. Worktree paralela preservada; nenhum commit.

## Falha real e primeira fronteira

Depois da correção específica de cancelamento de fala, Pedro refez os testes e informou que o corpo ainda deixava de reagir. A sessão f52f01ed registrou às 23:06:20 sem_confirmacao_pwm, zero movimentos confirmados nessa ocorrência e parada confirmada. A companhia revogou a concessão, retirando também SENTRY. Não era apenas descanso: leituras e alertas continuavam, mas não havia autorização para novas reações. Evidência em sessao_usuario.json.

A regra de revogar diante de falha elétrica não foi removida: o erro começa antes, na admissão do comando pelo firmware, que não distinguia a ocupação por proteção de uma falha de confirmação.

Reprodução real antes de alterar produção: COM4, mesmo root/owner e rodas suspensas; GUARD mostrava BUSCANDO, incidente 15. MOTOR foi transmitido em 3,171s. Não houve MACK, HAZARD ou outra resposta até STOP em 3,718s; SACK chegou. Rosto devolveu sem_confirmacao_pwm. O firmware retornava false silenciosamente em admitirMovimentoProtegido quando o reflexo estava ativo. RED C++ alcançou essa função e falhou por ausência de HAZARD correlacionado.

Primeiro candidato corrigiu a pausa, mas o ensaio físico seguinte mostrou ERROR 1 MOTOR_OCUPADO durante PWM local ativo. Essa rejeição acontecia antes da função de admissão, e o PC também a tratava como ausência de MACK. Artefato runtime_depois.json preserva esse resultado intermediário. Estendido o RED para a fase com motorAtivo: falhou pelo receipt ausente na sequência 2. Não foi declarado GREEN final a partir do primeiro teste.

## Contrato canônico e candidato final

Owner: admissão de MOTOR no firmware. Quando a proteção local já controla o corpo, qualquer novo MOTOR validado deve receber recusa HAZARD correlacionada à sessão/sequência. Não pode receber MACK do PWM local nem reiniciar o incidente. A sequência recusada é consumida, impedindo replay posterior. STOP e verificações de sessão/origem/TTL/argumentos mantêm precedência.

Produção alterada nesta raiz:

- firmware/rosto_laylay/protecao_corporal.h: recusa correlacionada durante reflexo, inclusive se o risco atual já desapareceu mas a reação ainda termina; mantém o episódio e PWM locais.
- firmware/rosto_laylay/rosto_laylay.ino: ocupação por reflexo usa essa mesma admissão. Ocupação por MOTOR normal continua MOTOR_OCUPADO. Declaração e stub mantêm builds sem proteção.

Não foram alterados os gates do PC, duração/PWM, limites dos sensores, preferências persistentes ou recuperação de falha elétrica. O owner existente do PC já preservava a companhia para um receipt de proteção; faltava esse receipt em todas as fases do executor. O contrato atende movimentos de conversa, emoções e qualquer habilidade que use o mesmo transporte, sem regra por texto ou gesto.

Hipóteses concorrentes: logs brutos e C++ mostram rejeição antes de aplicar o MOTOR, não apenas uma demora de MACK ou filtro do parser. Durante a reprodução, FACE/GUARD/SACK funcionavam; uma falha geral da USB/motores não explica o silêncio seletivo. O primeiro ensaio de controle anterior já confirmara três movimentos. Isso não encerra possíveis falhas elétricas/I2C independentes.

## Validação final

- C++ RED→GREEN usando firmware real: reflexo em pausa e com PWM, risco desaparecido, sequência repetida, STOP e ocupação por MOTOR normal. Sem MACK emprestado ou novo incidente.
- Regressivos host: proteção, sensores, saúde, reconexão, sono, sons, olhos, limite curto e PWM de referência passaram.
- Python: 61 testes de proteção, recuperação, transporte e cancelamento passaram; inclui recusa atual versus outra sessão/sequência. Receipt estrangeiro não preserva autoridade nem produz confirmação falsa.
- Core ESP32 3.3.12, USB/CDC, Wi-Fi OFF, motores ON, GPIO1/2/3/4, sleep7, som6 e sensores0/10 mantidos. Flash 432800 bytes, globais19356. Gravação final COM4 com hash verificado; hashes/flags em build_verificado.json.
- runtime_final.json: MOTOR 1 de sequência1 recebeu HAZARD da mesma sequência, incidente1, OBSTACULO. Receipt mudou de sem_confirmacao_pwm para interrompido_por_protecao:OBSTACULO. PWM do comando recusado não confirmado; parada confirmada. Portas/serviços encerrados.
- main_real.json: main, serviços, modelo e interface normais, sem substitutos dos executores ou leituras. Única adaptação do diagnóstico foi observação dos resultados e encerramento finito após65s. Um passeio real teve dois movimentos completos e o terceiro interrompido pelo obstáculo, retornando experiência interrompida. Companhia permaneceu ativa, SENTRY continuou e incidentes3–8 produziram novas reações na mesma sessão/boot. Nenhuma retomada de gesto antigo; reação posterior é episódio novo.
- Pedro confirmou durante o main: “Sim, continua reagindo”. Main encerrou normalmente, companhia=aplicacao_encerrada, transporte desconectado e nenhum processo Laylay/interface/ensaio remanescente. verificacao_final.json valida esses pontos.

Limites: rodas suspensas e sensores em teste; não comprova navegação/antiqueda em movimento sobre mesa nem estabilidade de horas. A rejeição silenciosa e a ocupação pelo reflexo foram reproduzidas/corrigidas; o receipt bruto da sessão histórica das23:06 não foi capturado, portanto não se pode atribuir toda falta de PWM passada a este único mecanismo. CORPO-I2C-01 permanece independente e aberta.
