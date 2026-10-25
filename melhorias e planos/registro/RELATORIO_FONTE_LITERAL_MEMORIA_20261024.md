# F1 — fonte literal preservada no refinamento da memória, 24/10/2026

## Resultado e escopo

Corrigida uma causa local da família F1, ligada às pendências de compreensão C7:
o coordenador entregava à memória a projeção normalizada de busca, em vez da
fala recebida. A pergunta perdia a interrogação e passava pelo filtro de
admissão como opinião/alegação do usuário.

Produção alterada somente em
`mente_laylay/autonomia/coordenador_intencao.py`, em `resolver_intencao`.
O callback `refinar_contexto_mental` recebe agora `texto`; `texto_norm`
continua disponível para os consumidores que já usavam normalização. Não foi
alterado o normalizador, registro semântico, classificador de modalidade,
cache, arbitragem, veto, executor, modelo, voz ou configuração.

O princípio reutilizável é: uma projeção de lookup não substitui uma fonte
observada. Vale para perguntas, limites de frase, caixa, acentos e pontuação
em qualquer domínio. Não há condição por Atlas, rock, aplicativo ou frase.
Não se demonstrou uma causa única para todas as falhas F1/C5/C7, nem se encerra
a compreensão geral.

## Base preservada e primeira fronteira

HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, branch `main`; worktree suja
preservada. Artefatos em `resultados_testes/ato_fala_memoria_20261024/`.
O baseline registra status e527hashes. O owner anterior foi copiado para
`fontes_antes/mente_laylay/autonomia/coordenador_intencao.py`; cópias dos
componentes de memória estudados também foram preservadas.

Cadeia capturada na factory instalada:

1. Entrada literal: `eu falei que prefiro Atlas?`, modalidade pergunta,
   sem autorização operacional.
2. A prioridade passa pelo resolvedor canônico do coordenador.
3. `normalizar_texto` produz `eu falei que prefiro atlas`.
4. O coordenador chama o refinamento com essa projeção de busca.
5. `EstadoContextoRuntime.refinar_contexto_mental` publica memória curta,
   que chama `registrar_interacao_semantica/registrar_alegacao`.
6. O registrador já rejeita textos com interrogação. Como ela foi removida,
   admite o texto normalizado com autor usuário, tipo/status opinião.
7. Isso ocorre ANTES do primeiro HTTP. As chamadas posteriores com o texto
   literal são rejeitadas corretamente, mas não desfazem a admissão anterior.

A pilha completa, textos, autor, fase e admissão estão em
`composicao_diagnostico.json`. O caso não depende de resposta errada do modelo.

Falsificações:
- O guardião não ignora uma interrogação presente: a pergunta literal é
  rejeitada diretamente pelo componente real.
- A resposta da IA não cria esse registro: há admissão do usuário antes do
  HTTP e com resposta controlada que não declara preferência.
- O problema não é específico de entidade ou opinião: perguntas sobre trabalho,
  posse e criação também falham, e declarações perdem sua forma original.
- Não é preciso retirar normalização dos detectores. O erro é a projeção
  correta de busca ter sido enviada à operação de observação.
- Na mesma factory, trocar apenas este owner pelo congelado reproduz a admissão
  indevida; o candidato entrega o literal e não cria a alegação.

## Contrato e responsáveis

| Owner | Responsabilidade mantida |
| --- | --- |
| Coordenador de intenção | Entrega a fonte recebida ao refinamento; conserva suas projeções específicas de lookup, decisão, veto e cache. |
| EstadoContextoRuntime e memória curta | Observam o texto recebido e mantêm seus callbacks/estado compartilhado. Não reconstroem pontuação perdida por adivinhação. |
| Registro semântico | Conserva a política atual de admissão, autoria e estados. Não transforma proposta da IA em fala do usuário. |
| Classificador canônico | Continua dono da modalidade e autorização. O patch não cria outro parser de pergunta ou comando. |
| Histórico literal | Mantém perguntas como mensagens da conversa, sem precisar promovê-las a opinião para que possam ser recuperadas. |

A mudança tem uma linha funcional e comentário sobre o contrato. A fala não é
reconstituída a partir de texto normalizado ou da resposta da IA. Não se fez
um filtro por frase no registrador, nem se apagou memória para ocultar o RED.

## RED e provas automatizadas

`scripts/tests/test_fonte_literal_refino_memoria.py` cobre perguntas em
domínios distintos, declaração válida, limites de frase, independência da
resposta da IA, preservação dos consumidores de lookup e factory real.

- `contrato_red.xml`:10REDs na primeira perda da fonte e1controle.
- `contrafactual_contrato.xml`:10REDs e2controles no owner congelado,
  com a factory explicitamente deselecionada porque usa subprocesso próprio.
- `contrato_final.xml`:118GREEN, incluindo13casos novos e os vizinhos.
- A factory permanente verifica que não há alegação do usuário promovida
  antes do HTTP nem depois da resposta; o histórico conserva a pergunta
  literal. Um comando proposto sem autorização não executa.

Um primeiro controle assumia incorretamente que todo detector externo recebia
normalizado. A contraprova mostrou que o detector composto já recebia literal;
outros consumidores, como `extrair_acao_agendada`, recebiam a projeção
normalizada. O teste foi ajustado para proteger AMBAS as interfaces existentes,
sem alteração adicional em produção. A execução intermediária foi preservada
em `contrato_green.xml`; não foi contada como regressão do candidato.

A revisão independente do único diff não encontrou bloqueio concreto e
confirmou os12testes leves antes da inclusão da factory. Não substitui o
julgamento das coletas reais, nem estende a garantia a todo tipo de ato.

## Composição e Qwen real

`composicao_baseline_final.json` e `composicao_candidato_final.json` usam a
factory instalada, mesma entrada e mesma folha HTTP controlada. Na base, a
primeira chamada do usuário é normalizada e admitida antes do HTTP; no
candidato todas as chamadas preservam a pergunta literal e não a admitem.
Somente o owner congelado é carregado em memória na contraprova, não a árvore
inteira do HEAD. A persistência raiz foi redirecionada em RAM e as folhas
externas isoladas.

A coleta `conversa_validada` usa o Qwen local configurado
`qwen3:4b-instruct`:30turnos/30conclusões,29HTTP200,13pacotes primários de
fontes conferidos contra os pedidos,527fontes sem drift,180,048s somados.
Um pedido de abrir Calculadora foi simulado com receipt negativo. Nenhuma
voz ou efeito real.

`auditoria_tipo_fala.json` confirma:
- depois do23,Atlas não aparece como opinião canônica do usuário nos oito
  planos auditados até o30;
- a pergunta literal continua disponível como mensagem histórica nos planos
  posteriores, sem apagamento da conversa;
- os snapshots após23/26não contêm as alegações indevidas dessas perguntas.

Isso não é prova de conversa coerente. Permaneceram recusas com fontes em5/6/7,
desvios e associações sem apoio, retomada operacional indevida em14/20 e limite
de tentativas em29. Em23/26a preferência não é confirmada indevidamente, mas a
resposta ainda expressa um limite de conferência. Em18e22há retomadas apoiadas
de aplicativo/bebida. As respostas da IA são resultados observados, não prova
de compreensão ou veracidade das proposições.

## Limites e próxima fronteira

Preservar a fonte não transmite seu tipo ao registro. A mesma pergunta SEM
interrogação, como `Qual aplicativo eu prefiro`, é classificada canonicamente
como pergunta, mas ainda pode ser admitida como opinião pela API atual do
registro. Essa falha foi registrada separadamente em
`auditoria_tipo_fala.json`, sem ampliar este patch ou inventar mais frases
proibidas.

A próxima investigação deve estudar como transmitir e validar o tipo canônico
do ato na admissão de proposições, incluindo falas mistas, em vez de depender
somente de pontuação ou reclassificar privadamente no domínio.

Esta mudança também não saneia registros históricos já existentes: uma
normalização antiga pode corresponder a uma declaração legítima ou a uma
pergunta mutilada. Não se apagaram alegações sem fonte/ocorrência que permitam
conferir sua origem. Não houve migração, commit ou reinício da sessão pessoal.

## Regressão ampliada e entrega

Regressão de91módulos relevantes:2.246GREEN,30subtests GREEN,14SKIP,
uma deseleção de import e as MESMAS nove falhas anteriores. A comparação por
nome de teste com a execução da base está em
`comparacao_falhas_anteriores.json`; não surgiu falha nova nesse conjunto.

As falhas preservadas são a seleção antiga de MUSIC_SEARCH para
`pode abri a calculadora para mim` e os oito casos de expectativas de pacote
literal/reserva de saída em `test_geracao_limite_sem_estado.py`. Suas contraprovas
estão, respectivamente, em
`respostas_prazos_20261024/relato_composto/falha_vizinha_baseline.xml` e
`base_canonica_rota_rapida_20261024/vizinho_orcamento_baseline.xml`, dentro de
`resultados_testes/`. Os testes não foram alterados para silenciar esses REDs.

O teste de import deselecionado foi executado na factory isolada:1GREEN em
`import_isolado.xml`. O comando amplo e o resultado estão em
`regressao_comando.json`/`regressao_ampla.xml`. Não é uma declaração de suíte
inteira verde.

`entrega.json` consolida escopo, hashes, testes e coletas;
`candidato_contra_base.patch` mostra somente a alteração deste owner contra sua
cópia congelada. Uma fonte de produção alterada entre527conferidas. As demais
alterações preexistentes da worktree foram preservadas.

