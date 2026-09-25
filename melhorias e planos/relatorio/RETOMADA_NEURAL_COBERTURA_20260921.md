# Retomada neural — cobertura do piloto e dados atuais

## Base e escopo

21/09/2026, branch main, HEAD `bd94bc3e3a29c49906dc603f9ca1540310ca3274`.
Worktree já modificada em cliente/empacotamento, foco Chrome e documentação;
mudanças preservadas. Pedro autorizou retomar a rede enquanto outro assistente
estuda um plano. Nenhum diff neural paralelo visível nas checagens desta etapa;
isso não certifica outros checkouts nem arquivos ignorados pelo Git.

Não houve fit, troca de pesos, promoção, mudança de autorização ou execução de
comandos. Hash de `memoria/neural/modelo_ativo.joblib` antes/depois:
`07c539917eae7792b2b4ecb1f0335697802fc7f6672e920656f8c5dfc2289e62`.

## Evidência atual, não inferência a partir do README antigo

Executado o exportador existente `mente_laylay.neural.curadoria_prospectiva_encoder`.
Snapshot local: `memoria/neural/experimentos/retomada_prospectiva_20260921/`.

- Fonte SHA-256: `1bb3897935533d3c75c4f88c3e4905f6fab1f216b1d9746f744f402640cfbdea`.
- Fila SHA-256: `a1b25caa779923c40270981392c39663511e2274d7c36f9b8dc9d690b6dfe693`.
- 1.096 eventos válidos; zero linhas inválidas; zero eventos em quarentena.
- 1.044 eventos declarados de teste; 52 pendentes de revisão.
- 438 textos distintos no total; os 52 pendentes contêm 46 textos distintos
  e 12 marcadores de sessão. Não equivalem a 52 exemplos independentes.
- Em relação às 546 posições do snapshot pós-caos de 14/09, há 550 posições
  adicionais: 506 declaradas de teste e 44 pendentes de revisão. É comparação
  de contagens/posições; não foi certificada identidade integral do prefixo.
- Ausência de marcador de teste não prova autoria humana. Nenhuma revisão
  humana, partição independente ou autorização de treino foi atribuída.

O snapshot mantém todos os eventos e contextos, inclusive os declarados de
teste. Não modifica o arquivo append-only de produção. Novas mensagens após
o snapshot não fazem parte dos números acima.

## Primeira barreira: perfil experimental não cobre o uso recente

`preparar_lote_relacional_v3.VARIANTES` e o protocolo supervisionado restringem
o piloto a APP_OPEN/open, MUSIC_SEARCH/search e FILE_READ/read, cada um com
pedido/recusa/relato. A coleta é mais ampla que esse perfil.

Triagem manual **por IA**, somente para planejar cobertura, das 52 entradas:

| Família de uso | Eventos | Índices no snapshot |
| --- | ---: | --- |
| Social | 4 | 208, 867, 926, 1079 |
| Explicação e continuidade conversacional | 12 | 209–211, 213–215, 1081–1086 |
| Navegação por assunto | 1 | 212 |
| IoT, incluindo um pedido agendado | 18 | 866, 868, 869, 871–873, 875, 876, 925, 931, 933, 934, 947, 972, 997, 999, 1092, 1093 |
| E-mails e briefing | 2 | 870, 1080 |
| Sistema e janelas | 5 | 874, 927–930 |
| Playlists | 2 | 998, 1094 |
| Repetição contextual | 2 | 932, 1095 |
| Controle de reprodução | 2 | 1087, 1088 |
| Volume | 4 | 1089–1091, 1096 |

Cobertura dos índices verificada: 52, sem duplicação nem omissão. As famílias
não são rótulos operacionais, não resolvem referentes e não autorizam ações.
Pedidos agendados, negação corretiva e referências precisam de contexto/revisão.
Nada foi convertido em negativo `ausente` para caber na perda do modelo.

Nenhuma dessas 52 entradas fornece, nesta triagem, anotação supervisionada
para as três variantes atuais. Não significa ausência de comandos nem falha
da rede: significa incompatibilidade entre a amostra e o escopo do piloto.
A curadoria anterior de 14/09, com seis casos supervisionados por IA, continua
preservada; não foi apagada por esta contagem nem promovida a avaliação inédita.

### Explicações concorrentes verificadas

- **Não há dados novos:** falsificada pela exportação atual.
- **A coleta atual está corrompida:** não sustentada; leitor/curadoria não
  encontraram corrupção ou quarentena neste snapshot.
- **Basta aumentar épocas usando o lote recente:** não sustentada; as entradas
  não preenchem o perfil nem a supervisão/partições exigidas pelo protocolo.
- **A rede é inferior por causa destes números:** não demonstrado; esta etapa
  não mediu predições, acurácia ou comparação com o interpretador atual.

## Direção de continuidade por contrato

Contrato: o protocolo de avaliação deve representar as operações que pretende
melhorar, com atos, alvos e contexto separados de permissão/receipt. Não ampliar
VARIANTES apenas para fazer a contagem passar; o dono é o protocolo experimental,
não o roteador de produção nem o executor.

Próximo trabalho delimitado: preparar uma extensão versionada do piloto para
IoT on/off e controle de mídia/volume, reutilizando catálogo e supervisão
canônicos. Primeiro inventariar as representações de alvo, parâmetros numéricos,
agendamento, referência e negação corretiva; só depois definir quais casos o
perfil novo realmente representa. Preservar o protocolo de três variantes como
controle histórico, sem rebatizar dados conhecidos como reserva inédita.

O comparativo terá de manter encoder congelado versus ajustado pareados e
avaliar a composição atual separadamente. Não misturar falha de interpretação,
abstenção, parâmetro/alvo errado e falha do executor numa única taxa. Nenhum
limiar, orçamento novo ou conjunto de avaliação foi escolhido nesta etapa.

## Verificação e limites

93 testes aprovados em 6,41 s: coleta, curadoria prospectiva, revisão, protocolo
supervisionado e preparação de entrada. São regressivos locais desses contratos,
não evidência de superioridade da rede nem teste completo do runtime.

Entregas desta etapa: snapshot imutável, triagem de cobertura e direção baseada
nos dados recentes. Produção neural e modelo ativo permanecem inalterados.
