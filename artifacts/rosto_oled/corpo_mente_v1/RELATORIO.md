# Corpo no plano da mente — primeira versão

Base: main, HEAD `2566b621d2c8ee88ff7086c6c36019da85c8a4cd`, worktree suja preservada.
Baseline dos arquivos alterados por esta frente em `baseline/`. Nenhum commit criado.
Registro e mapa causal consultados: a frente corporal existente já tinha dono USB,
concessão de sessão, coordenação e receipts. Não pertence aos REDs semânticos paralelos.

## Fronteira e contrato

O prompt principal não recebia um retrato compacto do corpo. O writer canônico
publicava o plano, mas descartava uma intenção corporal da emissão original.
O teste `test_writer_canonico_retem_intencao_da_emissao_original` alcançou essa
publicação e ficou RED pela ausência do campo, antes do candidato.

Modelo corporal vivo → mesma LLM principal propõe intenção finita → transação do
plano vincula à ocorrência e ao retrato da concessão → dono corporal revalida
sessão, concessão, prazo e contexto → quadro cooperativo confirma olhos antes de
motor → receipts PWM/parada → experiência transitória correlacionada na mente.

Proposta não concede movimento. Não aceita PWM, parâmetros técnicos ou permissão
no campo corporal. Codec JSON compartilhado recusa duplicatas, framing reparado
e constantes inválidas. Mudança de turno/sessão, revogação, prioridade ou prazo
interrompem/inibem. Comemoração exige confirmação de todos os comandos do mesmo
plano; sucesso parcial não basta. O nome descansar suspende o passeio durante a
validade da proposta. Receipts não provam giro, distância ou parada física.

O resultado usa CAS para concluir somente sua intenção/ocorrência. Um resultado
tardio permanece identificado como experiência de outro turno. O catálogo vivo
descreve a integração. O quadro publica IDs de turno/intenção para diagnóstico e
usa os callbacks compartilhados de continuidade e aprendizado já instalados;
ACK automático não vira aceitação humana nem preferência durável.

## Produção alterada nesta frente

- `cognicao/modelo_corporal.py`: contrato/projeção/codec finito.
- `cognicao/orquestrador_turno_runtime.py`: vinculação atômica na publicação original.
- `cognicao/decisao_corporal.py`: timing da proposta junto às prioridades reais.
- `autonomia/companhia_corporal.py`: reserva, execução, vigência e experiência.
- `autonomia/processamento_resposta_ia.py`: reescritas também recebem o retrato
  corporal do host; remove a premissa fixa de ausência de corpo físico.
- `especialistas/corpo_motor_runtime.py`: retrato factual vivo.
- `integracao/composicao_contextos_ia.py`, `autonomia/contexto_resposta_ia.py`,
  `laylay.py`: injeção no caminho real, incluindo o prompt rápido.
- `especialistas/mapa_habilidades.py`: consciência da capacidade.
- `autonomia/quadro_cooperacao.py`: IDs públicos sanitizados da cooperação.

Firmware, pinout, fonte, modelo configurado e preferências salvas não alterados.
Configurações de diagnóstico via ambiente valeram apenas nos subprocessos.
As sondas não abriram a interface. Uma instância externa da Laylay foi detectada
durante o trabalho e preservada. No encerramento do teste físico, a sonda enviou
STOP e desconexão; Pedro confirmou a parada. Não se alterou o firmware.

## Evidência

- `pytest_final.txt`: **371 passed** nos contratos novos e regressivos de corpo,
  companhia, passeio, coordenação V2, rosto, som, atividade e transporte de prompt.
- `receipt_componentes_fisico.json`: LLM configurada real em pacote diagnóstico
  fechado escolheu `expressar`; estímulo emocional de alegria explicitamente
  diagnóstico, composição/estado/plano/USB reais. EXPR/EACK, SOUNDACK,
  MOTOR2/MACK, STOP/SACK e NACK capturados. Resultado retornou ao modelo de si.
- Pedro confirmou visualmente olhos, bip, motores e parada.
- `receipt_fluxo_chat_serial_simulada.json`: fluxo completo da resposta principal
  com modelo configurado real, chat ativado pelo setter de produção e apenas a
  porta serial substituída. Entrada `gosto muito de voce`; emoção causal real
  `envergonhada` nível 2. Emissão original JSON com fala e intenção `expressar`,
  vinculada ao plano; coordenação, receipts simulados e experiência concluídos.
  Não constitui outra prova física.
- `receipt_runtime_fisico.json`: fluxo principal com chat ativo, LLM e COM4
  reais, emoção causal da conversa `envergonhada` nível 2, sem estímulo emocional
  injetado. Intenção original `expressar`, PWM/parada confirmados e experiência
  retornada à mente. A observação humana dessa execução específica ficou pendente;
  a confirmação humana anterior refere-se ao gesto de alegria diagnóstico.
- `sonda_fluxo_chat_sensacoes.log`: após a fundamentação das reescritas e a
  distinção de sensações, modelo real e caminho completo, com serial simulada,
  voltaram a concluir a intenção corporal. Não confirma nova execução física.
- `pytest_voz.txt`: 21 passed, 1 failed. O teste estático do prompt permanente
  exige a frase antiga "doce sem ser mole, firme sem ser arrogante". Ela foi
  substituída na alteração paralela preexistente de `perfil_amizade.py`; esta
  frente não alterou esse arquivo nem o teste. RED separado, preservado.

**GREEN integração com componentes/modelo/ESP reais e observação humana no
controle diagnóstico; GREEN conversa principal até receipts reais do ESP;
GREEN conversa principal com serial simulada após o ajuste das reescritas.**
A experiência pela UI e a observação humana da execução específica da conversa
normal ainda não foram verificadas. Não declarar GREEN global.

## Diagnóstico das sondas e formato da emissão

A primeira sonda recebeu `__LAYLAY_LLM_ORCAMENTO_PRINCIPAL_DUPLICADA__`.
O retrato chegou ao pedido, mas a emissão era técnica: sem proposta, sem motor.
A sonda com orçamento desativado apenas para diagnóstico encontrou erro do modelo
local: 23817 tokens para contexto de 4096; fallback/circuito depois disso.
Sonda curta também não obteve proposta válida. Logs em
`sonda_runtime*.log`, receipts negativos preservados separadamente.

Essas sondas chamavam a resposta fora de chat ativo e não reproduziam a entrada
da conversa. Com o setter real de chat ativo, a chamada principal respondeu;
por isso os bloqueios iniciais não provam um defeito na conversa de produção.
Não se mudou orçamento, modelo ou capacidade de contexto na solução.

A sonda em chat ativo primeiro recebeu prosa que narrava "Intenção corporal".
O codec recusou corretamente vincular essa prosa. A primeira fronteira era a
instrução corporal não negociar o formato JSON no preparador compartilhado.
Um RED focado confirmou ausência de `response_format`. O candidato adicionou
o marcador canônico de JSON na instrução efêmera e explicitou o campo externo,
fora de `fala`; nenhuma extração de prosa ou reparo corporal foi introduzido.

O transporte legado retira `json_object` na compactação por compatibilidade;
`json_schema` possui outro contrato. O teste preserva a instrução completa e
a negociação inicial, sem alterar essa política paralela. Após o candidato,
`sonda_fluxo_chat_json.log` e o receipt correspondente mostram JSON nativo válido,
intenção do mesmo modelo e conclusão do plano com a serial simulada.

Uma execução real posterior usou a chave acentuada `intenção_corporal`.
`receipt_chave_acentuada_fisico.json` conserva a recusa: nenhuma intenção
materializada nem movimento dessa proposta. Acrescentado exemplo JSON com chaves
literais; a sonda física seguinte vinculou a intenção e recebeu os ACKs reais.

## Sensações e reescritas: orientação aprovada

Pedro aceita sensações coerentes com o corpo robótico e pede linguagem pé no
chão. O retrato comum agora distingue emoção funcional causal, hardware observado
e sensação física dependente de sensor. Expressividade e metáfora reconhecível
são permitidas; calor, toque, dor, esforço, colisão e percepção ambiental não
viram fatos medidos sem observação. Os sensores correspondentes não existem
nesta montagem. PWM/parada não são prova de distância ou sensibilidade física.

O caminho de reescrita da realidade continha literalmente "Laylay não tem corpo
físico" e os demais autores auxiliares não recebiam o retrato novo. Isso provou
uma premissa arquitetural incompatível com o hardware conectado, sem demonstrar
que ela foi a única origem da negação na fala histórica. Um RED canônico alcançou
a reescrita de experiência física inventada e capturou a premissa fixa.
O candidato transmite o mesmo retrato vivo do owner a todas as reescritas dessa
resposta, conservando flags de chamada, orçamento e validadores existentes.
Reparo nunca escolhe outra intenção corporal nem concede autorização. Testes
cobrem corpo conectado, desconectado e origem não confiável, mantendo o bloqueio
de experiências inventadas. A intenção continua ligada à emissão principal
original, mesmo quando a fala precisa de reescrita.

Próxima validação humana disponível: iniciar a Laylay normalmente com o ESP,
conversar e acompanhar o gesto, sem estímulo emocional de diagnóstico. A sonda
equivalente usa `--chat-ativo` sem `--serial-simulada` quando a COM4 estiver livre.

O contrato é reutilizável: qualquer habilidade pode fornecer um retrato factual
ao planejamento, mantendo proposta, autorização, executor e efeito separados,
com resultados correlacionados à ocorrência que realmente os originou.
