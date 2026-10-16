# Expressividade da mesma intenção corporal

Base: main, d850b8c90cc5ce40bd4832e759ed991ba88cd5cc. Worktree modificada antes do pedido, incluindo correção de bips e investigação paralela de comandos. Baseline dos três arquivos em baseline/. Nenhum commit criado.

## Contrato e evidência inicial

Pedido de Pedro: mais expressão nos olhos, bips e gestos juntos. A intenção e a concessão existentes continuam sendo a fonte; esta evolução aumenta a variedade de sua apresentação, sem criar emoções, autorização ou receipts novos.

O renderer de EXPR usava o estilo sobretudo para alegria e o restante recebia quase apenas altura/olhar lateral. As variações de gesto mantinham a mesma sequência, escalando duração ou espelhando os lados. REDs antes do candidato: expressão de vergonha recebida/renderizada não alterava rubor/altura; assinaturas da primeira e terceira variação de alegria eram idênticas. A base emocional e os receipts funcionavam, portanto não foi alterada a cognição nem o contrato de execução.

## Produção alterada

- firmware/rosto_laylay/rosto_laylay.ino: detalhes visuais distintos por estilo recebido, ênfases temporais, olhar vertical e assimetria. Envelope finito e suavização mantêm continuidade; não redesenha boca nem lê voz.
- firmware/rosto_laylay/som_expressivo.h: pequenas inflexões de frequência nas melodias emocionais. Melodias de acordar/sucesso/falha, duty, duração máxima, intervalo, canal PWM e corte permanecem preservados.
- mente_laylay/autonomia/companhia_corporal.py: terceira variante recebe uma frase distinta de movimento para cada emoção/intenção. Mantém limites, revalidação de causa/concessão, parada e coordenação cooperativa existentes.

Mecanismo reutilizável: uma causa da mente → partitura finita → confirmação por canal → acomodação. Resultados continuam vindo do owner de atividade para ações de todos os domínios; apresentação não concede motores e não confirma o efeito da ação.

## Validação

- EXPRESSOES_V3_OK no firmware real compilado em host: estilos distintos, suavização por frame, retorno por TTL, nenhum motor por EXPR, variação sonora e duty preservado. Hardware gráfico simulado; preview.png/preview.gif são frames desse renderer, sem comprovação óptica física.
- Regressivos host: presença/sono gradual, som/olhos sem boca, motor longo, glitch e STOP passaram. O teste de som precisa ser compilado com o perfil de motores habilitado para sua asserção de timer de tração; a primeira execução sem esse perfil parou nessa asserção, antes de verificar as mudanças.
- 197 testes de som, presença, corpo na mente, companhia, comemoração/passeio e transporte passaram (pytest_regressao.txt), incluindo testes da composição instalada, concessão, coordenação, falha parcial e catálogo vivo existentes.
- A seleção inicial com decisão corporal teve 43 passes e um RED de default de configuração após import da raiz carregar a preferência pessoal de rodas suspensas. Esse teste passa isolado; configuração e sua asserção não foram alteradas.
- Arduino C3/core 3.3.12 compilou: 395282 bytes de programa, 17444 globais. USB, motores habilitados, limite 5000 ms, falante apenas GPIO6. Upload COM4 com hash verificado; receipt_build.json guarda hashes do código.
- Sonda na composição instalada, sem interface: quatro emoções explicitamente diagnósticas, usando a terceira variação, mesma concessão e coordenador de produção; EXPR/EACK, SOUND/SOUNDACK, MOTOR/MACK e STOP/SACK reais registrados em receipt_fisico.json. Quatro coreografias terminaram sem falha e a parada foi recebida. Não prova rotação/deslocamento nem audição/semântica visual humana; feedback físico de Pedro ainda pendente.

Teste novo em scripts/tests/test_presenca_corporal_v2.py; verificação host em firmware/rosto_laylay/validacao_host/validar_expressoes_v3.cpp; sonda em scripts/validar_expressoes_v3_fisico.py. As preferências do usuário não foram modificadas e a interface não foi reaberta automaticamente.

## Avaliação após repetição

Pedro pediu para repetir porque não acompanhou a primeira demonstração. A repetição terminou com quatro coreografias, cinco SOUNDACKs (incluindo acordar), STOP/SACK e GOODNIGHT/NACK, sem falha. A trilha atual está em receipt_fisico.json; a primeira foi preservada em receipt_primeira_demonstracao.json.

Após a repetição, Pedro avaliou: "achei otimo chat, ta muito bom". Essa é a aprovação qualitativa do conjunto expressivo. Não representa calibração de ângulo, distância, intensidade sonora ou sensores.
