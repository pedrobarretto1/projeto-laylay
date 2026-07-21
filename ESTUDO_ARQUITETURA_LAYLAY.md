# Estudo arquitetural da Laylay

## 1. Visão executiva

A Laylay é uma assistente pessoal Windows híbrida, local-first, orientada a eventos e composta por vários runtimes especializados. Ela combina conversa por LLM, regras determinísticas, memória SQLite, automação do Windows, integração Chrome por WebSocket, música/YouTube, Gmail, agenda, percepção de janelas, saúde do PC e IoT.

O conceito de **mente única** existe de verdade no código: há um contêiner central sincronizado (`EstadoCompartilhadoRuntime`) com seis domínios de estado. Porém, a decisão por turno ainda não é completamente única. Há várias camadas capazes de interpretar, executar ou emitir fala. Portanto:

- o **estado** é majoritariamente centralizado;
- a **decisão** ainda é distribuída;
- a **emissão de fala** é parcialmente centralizada;
- persistem estruturas legadas e pendências específicas por habilidade.

O projeto analisado possui aproximadamente:

- 188 módulos Python dentro de `mente_laylay`;
- aproximadamente 48 mil linhas nesses módulos;
- 2.546 linhas em `laylay.py`;
- 1.307 linhas no armazenamento SQLite;
- 49 arquivos de teste;
- 608 testes e 33 subtestes atualmente aprovados.

## 2. Papel de `laylay.py`

`laylay.py` é o **composition root** da aplicação. Ele:

1. importa implementações dos pacotes internos;
2. configura terminal, logs e encoding;
3. cria o estado compartilhado;
4. instancia os runtimes;
5. conecta callbacks entre módulos;
6. configura arquivos, variáveis de ambiente e limites;
7. inicia threads e serviços;
8. mantém o processo principal ativo.

A maior parte da lógica de negócio não está mais nele. Ainda assim, ele continua muito acoplado porque usa `globals()` como catálogo dinâmico de dependências para diversos runtimes. Isso permitiu refatorar gradualmente sem quebrar o código legado, mas reduz a verificabilidade estática.

## 3. A mente única

O núcleo é `EstadoCompartilhadoRuntime`, protegido por `threading.RLock`. Ele divide a mente em seis domínios.

### 3.1 `mental`

Guarda significado e continuidade:

- última entrada e resposta;
- última intenção, habilidade, alvo e escopo;
- última ação real, parâmetros, status e confirmação;
- pergunta aberta e promessa conversacional;
- oferta pendente;
- focos vivo, operacional e conversacional;
- focos separados por domínio;
- estrutura recente de arquivos;
- consciência temporal;
- preferências musicais;
- aprendizado de continuidade;
- leitura emocional do usuário;
- autoaprimoramento.

### 3.2 `conversacional`

Guarda estado de interação e expressão:

- emoção e intensidade atuais;
- causa, duração e decaimento emocional;
- humor;
- modo chat/conversa ativa;
- estado de fala;
- tópicos recentes;
- último tópico e horário.

### 3.3 `memoria_conversa`

Guarda o histórico usado pela LLM:

- `messages`;
- bordões;
- resumo da conversa;
- fatos e eventos;
- histórico de longo prazo.

### 3.4 `continuidades`

Guarda pendências operacionais curtas:

- sugestões de rotina;
- sugestões de playlist;
- sugestões de email;
- comando sugerido e seu estado;
- payloads pendentes.

Esse domínio é a maior exceção prática ao modelo conceitual unificado: embora esteja dentro do mesmo contêiner, cada habilidade ainda mantém contratos próprios de confirmação.

### 3.5 `musical`

Guarda:

- última playlist;
- bloqueio temporário de playlist;
- estado e índice da playlist;
- intervenção do usuário;
- fila/shuffle e URL atual.

### 3.6 `percepcao`

Guarda:

- aba ativa;
- janela/processo atual;
- último site aberto;
- logs do navegador;
- contexto do sistema;
- sinais recebidos pelo Chrome e player.

## 4. Fluxo completo de uma mensagem

O ponto central é `RespostaIARuntime.processar`, protegido por um lock para serializar entradas de voz, terminal e hotkey.

Fluxo real:

```text
entrada do usuário
  -> marca início do turno
  -> comandos prioritários objetivos
  -> pre-fluxo conversacional
  -> comandos imediatos
  -> pre-fluxos secundários (modo não rápido)
  -> construção do prompt contextual
  -> LLM principal
  -> limpeza/parse da resposta JSON
  -> nova tentativa determinística pós-LLM
  -> dispatcher de comandos JSON
  -> execução e validação
  -> finalização da resposta
  -> registro na mente/memória
  -> fila única de voz/terminal
```

### 4.1 Pre-fluxo conversacional

A ordem atual é significativa:

1. confirmação musical pendente;
2. reparação conversacional;
3. opinião sobre música atual;
4. execução prática precoce;
5. elogio/agradecimento;
6. bloqueio de playlist;
7. feedback pendente;
8. pedido musical genérico;
9. sugestão indireta;
10. pergunta curta contextual;
11. resposta a pergunta aberta;
12. conversa social curta;
13. aprendizado de apelido.

O primeiro estágio que retorna sucesso encerra o fluxo.

### 4.2 Caminho determinístico

O coordenador de intenção prioriza:

1. agendamento;
2. cancelamento/reversão;
3. detector determinístico com alvo explícito;
4. continuidade contextual;
5. repetição da última ação;
6. detector determinístico dependente de contexto;
7. classificador de intenção por LLM (`IA-first`).

### 4.3 Caminho conversacional

Conversas curtas podem ser classificadas localmente como:

- saudação;
- bem-estar;
- resposta de bem-estar;
- estado emocional;
- elogio;
- reação;
- pergunta;
- opinião;
- recusa suave;
- continuação.

Se não houver resposta local segura, a entrada segue para a LLM principal com o resumo integrado da mente.

## 5. LLM e prompt

A LLM usa API compatível com Chat Completions e suporta endpoint local ou remoto. O transporte:

- serializa chamadas locais;
- escolhe timeout local/remoto;
- compacta payloads grandes;
- tenta novamente após HTTP 400;
- entra em cooldown temporário após 400 persistente;
- produz fallback compatível com JSON quando necessário.

O prompt base exige resposta JSON com fala, tipo de interação, comandos e aprendizados. A política atual tenta separar:

- conversa;
- ação;
- aprendizado;
- confirmação.

Na carga da memória, o prompt atual substitui qualquer prompt de sistema antigo persistido. Isso é essencial para que correções de comportamento passem a valer após reiniciar.

## 6. Contexto e continuidade

Existem quatro mecanismos complementares.

### 6.1 Contexto imediato

Resolve pronomes e comandos elípticos como:

- “fecha ele”;
- “desliga ela”;
- “coloca em foco”;
- “tenta de novo”.

### 6.2 Continuidade semântica

Reconhece relações como:

- REFERENCIAR;
- REPETIR;
- REVERTER.

Ela reconstrói intenção, domínio, ação, alvo, parâmetros e confiança. Também aprende correções de domínio/operação.

### 6.3 Focos por domínio

Aplicativo, site, música, arquivo e IoT podem manter referências independentes. Isso evita que a última ação global destrua todos os outros assuntos.

### 6.4 Continuidade da própria fala

A Laylay registra:

- última afirmação;
- última pergunta;
- última opinião;
- última brincadeira;
- assunto da fala;
- resposta esperada.

Esse mecanismo responde a “como assim?” e confirmações de ofertas. O risco atual é recorrer a tópico antigo quando a última fala não possui um referente concreto.

## 7. Memória e persistência

### 7.1 Política

Há três classes conceituais:

- **durável**: conversa, emoções, tópicos, autoaprimoramento, consciência temporal, aprendizado de continuidade e preferências musicais;
- **sessão**: música, percepção, conteúdo ativo e focos;
- **efêmera**: continuidades, promessas, perguntas abertas e última ação.

Nem todos os itens listados na política são persistidos integralmente; a política funciona mais como documentação do contrato do que como serializador genérico.

### 7.2 SQLite

`MemoriaSQLite` armazena:

- estado serializado;
- fatos;
- eventos;
- preferências;
- resumos;
- aprendizados semânticos;
- dispositivos IoT;
- estado e histórico IoT.

### 7.3 Arquivos JSON paralelos

Ainda existem arquivos específicos para:

- briefing;
- Gmail;
- agenda;
- rotinas aprendidas e feedback;
- histórico/feedback musical;
- playlists;
- curadoria musical.

Eles são persistências de domínio, não necessariamente mentes paralelas, mas aumentam a possibilidade de divergência quando o mesmo conceito também existe no estado mental.

## 8. Personalidade, emoções e voz

### 8.1 Personalidade

A personalidade é aplicada por:

- prompt base;
- respostas locais;
- variações de fala;
- ajuste contextual por horário;
- proporção da resposta;
- controle de repetição;
- abertura dinâmica.

### 8.2 Emoções

O estado emocional tem causa, intensidade, duração e orçamento de interações. Existe decaimento por tempo/interação. A emoção altera tom e parâmetros de voz, mas ações continuam sujeitas a validação objetiva.

### 8.3 Voz e emissão

`VozRuntime` possui:

- fila serial;
- worker dedicado;
- batching de falas próximas;
- deduplicação por turno;
- bloqueio de proatividade durante conversa;
- barge-in por evento de interrupção;
- Edge TTS com fallback `pyttsx3`;
- ducking do volume do sistema;
- variação de abertura e uso moderado do nome.

O texto formatado no terminal é emitido quando a fala entra em reprodução, não necessariamente quando a decisão é criada.

## 9. Capacidades

### 9.1 Windows

- abrir/fechar/focar/maximizar aplicativos;
- organizar janelas;
- controlar volume e mídia;
- bloquear PC;
- observar processos/janelas;
- consultar CPU, RAM e temperatura;
- localizar executáveis.

### 9.2 Arquivos

- criar pasta/arquivo;
- editar;
- mover/renomear;
- excluir com trava de segurança;
- transações combinadas com validação e proteção contra sobrescrita.

### 9.3 Chrome

- WebSocket local na porta 8080;
- extensão conectada;
- listar e selecionar abas;
- ler conteúdo da página;
- abrir/reutilizar/fechar abas;
- controlar YouTube;
- receber contexto do usuário e player.

### 9.4 Música

- busca de faixa no YouTube;
- pontuação para evitar podcasts, compilações e resultados ruins;
- playlists do usuário e da Laylay;
- reprodução, pausa, próxima/anterior;
- recomendações conversacionais;
- confirmação pendente;
- preferências por artista/faixa;
- aprendizado por horário;
- curadoria autônoma.

### 9.5 Gmail e briefing

- IMAP por senha de aplicativo;
- leitura, sincronização e resumo;
- remetentes prioritários e palavras urgentes;
- briefing com clima;
- execução em daemon.

### 9.6 Agenda

- lembretes;
- ações futuras;
- listagem e cancelamento;
- execução contextual agendada.

### 9.7 IoT

- registro canônico de dispositivos e aliases;
- modo simulado por padrão;
- Tuya somente com autorização explícita;
- consulta antes da ação;
- validação depois da ação;
- persistência do resultado;
- reversão contextual;
- confirmação baseada em risco.

### 9.8 Percepção e memória visual

- janela/aba ativa;
- classificação de assunto;
- conteúdo atual com fonte e confiança;
- captura de tela;
- análise visual;
- limite diário de memórias visuais.

### 9.9 PC B

- roteamento de ações para um segundo computador;
- envio de payloads;
- contexto separado de destino.

## 10. Autonomia e serviços em background

No início são criadas threads para:

- WebSocket/Chrome;
- briefing;
- Gmail;
- agenda;
- aprendizado de rotina;
- porteiro de sugestões;
- saúde do PC;
- monitor de janelas;
- chat de terminal.

O gerenciador impede inicialização duplicada por nome e isola falhas. O monitor de saúde valida dependências críticas e apresenta estado saudável/degradado.

## 11. Segurança

Pontos positivos:

- validação pós-ação para IoT;
- Tuya exige autorização externa explícita;
- exclusão de arquivos possui trava;
- ações não confirmadas não devem ser narradas como sucesso;
- intenções deliberativas viram sugestão, não execução;
- lista fechada de ações no prompt;
- `pyautogui.FAILSAFE` ativo;
- segredos IoT são mascarados;
- erros externos não são persistidos integralmente.

Riscos:

- detectores baseados em regex podem perder negação ou tratar pronome como alvo;
- `globals()` permite conexões tardias difíceis de auditar;
- uma intenção incorreta pode chegar a executores reais antes da LLM principal;
- automação de janelas usa heurísticas de título/processo;
- o filtro de segurança está distribuído entre porteiro, coordenador, dispatcher e executor.

## 12. Principais conflitos arquiteturais

### 12.1 Muitos decisores por turno

Há decisões em:

- pre-fluxo;
- comandos prioritários;
- comandos imediatos;
- coordenador determinístico;
- contexto imediato;
- continuidade semântica;
- IA-first;
- LLM principal;
- dispatcher pós-LLM.

Isso explica por que correções locais frequentemente resolvem um exemplo, mas outro caminho ainda produz comportamento parecido.

### 12.2 Muitos emissores de fala

Runtimes de música, IoT, Gmail, saúde, playlist, conversa, dispatcher e proatividade podem chamar a voz. A fila reduz sobreposição, mas não substitui um contrato de “uma decisão/uma fala por turno”.

### 12.3 Confirmações heterogêneas

Há pelo menos:

- pergunta aberta;
- promessa conversacional;
- oferta pendente da mente;
- sugestão musical pendente interna;
- sugestões de rotina/playlist/email em `continuidades`;
- comando sugerido do porteiro.

Todas representam uma dívida conversacional semelhante, mas possuem formatos e TTLs diferentes.

### 12.4 Classificação lexical frágil

Diversas decisões usam substring, quantidade de palavras e regex. Falhas já observadas incluem:

- `oi` dentro de `noite`;
- `que` interpretado como aplicativo;
- perguntas novas consumidas como resposta antiga;
- conversa classificada como rejeição de sugestão invisível.

### 12.5 Histórico cresce e carrega ruído

O prompt usa mensagens persistidas e resumos contextuais. Embora haja compactação no transporte local, tópicos e respostas ruins podem continuar influenciando decisões se não forem sanitizados na gravação.

### 12.6 Política de persistência não é executável

A tabela durável/sessão/efêmero não controla automaticamente a serialização. Cada novo campo precisa ser ligado manualmente em carga e snapshot.

## 13. Pontos fortes

- Separação progressiva de `laylay.py` em runtimes testáveis.
- Estado compartilhado com lock e snapshots defensivos.
- Validação explícita de resultados de ação.
- Boa cobertura de continuidade semântica e reparação.
- IoT com desenho seguro e modo simulado.
- Chrome estruturado em transporte, contexto, eventos, comandos e estado.
- Personalidade separada da confirmação objetiva de execução.
- Testes de regressão baseados em erros reais de conversa.
- Arquitetura preparada para LLM local e remoto.
- Sistema de saúde de dependências e isolamento de threads.

## 14. Prioridades recomendadas

### Prioridade 1 — decisão única por turno

Criar um `TurnoRuntime` com um objeto único:

```python
Turno(
    id,
    texto_original,
    texto_normalizado,
    modalidade,
    contexto_snapshot,
    candidatos=[],
    decisao=None,
    execucao=None,
    fala=None,
)
```

Cada roteador apenas propõe um candidato com confiança e evidências. Um árbitro escolhe exatamente um resultado.

### Prioridade 2 — unificar pendências

Substituir pergunta, promessa e sugestões específicas por um contrato único:

```python
Pendencia(
    origem,
    tipo,
    opcoes,
    resposta_esperada,
    intencao,
    criada_em,
    expira_em,
    visivel_ao_usuario,
)
```

Somente pendências efetivamente faladas podem consumir a próxima entrada.

### Prioridade 3 — emissão única

Executores devem retornar `ResultadoAcao`, nunca falar diretamente. O finalizador do turno decide a única fala. Proatividade deve criar um turno próprio de baixa prioridade.

### Prioridade 4 — modalidade antes da intenção

Classificar primeiro:

- comando;
- pergunta;
- conversa;
- correção;
- confirmação;
- recusa;
- deliberação.

Somente a modalidade `comando` ou uma confirmação ligada a pendência executável deve alcançar executores.

### Prioridade 5 — persistência declarativa

Transformar a política em esquema executável. Campos novos devem declarar duração e serializador junto à definição do estado.

### Prioridade 6 — testes de diálogo

Além dos testes unitários, criar cenários com 5–15 turnos contendo:

- mudança de assunto;
- sugestão e recusa;
- pergunta sem `?`;
- comando negado;
- falha de executor;
- proatividade concorrente;
- reinício entre turnos;
- memória antiga incompatível.

## 15. Modelo mental correto para evoluir a Laylay

A Laylay não é apenas uma LLM com comandos. Ela é melhor entendida como:

```text
sensores/eventos
      ↓
estado compartilhado
      ↓
interpretação multimodal do turno
      ↓
arbitragem entre conversar, perguntar, aprender ou agir
      ↓
execução validada
      ↓
uma resposta proporcional
      ↓
memória com duração explícita
```

O próximo salto de qualidade não virá principalmente de novas frases ou mais regex. Virá de transformar a atual **mente única de estado** em uma **mente única de decisão e emissão**.

## 16. Conclusão

A base técnica é ambiciosa e já possui componentes maduros: estado compartilhado, validação de ações, contexto por domínio, transporte Chrome, memória SQLite, IoT seguro e runtimes especializados. Os erros conversacionais não decorrem de ausência de contexto; decorrem, em grande parte, de **contexto demais sendo interpretado por decisores demais**.

O princípio mais importante para qualquer próxima alteração é:

> Uma entrada gera um turno; um turno possui uma modalidade; uma modalidade produz uma única decisão; uma decisão pode executar no máximo uma intenção principal; o turno termina com uma única fala registrada na mesma mente.

## 17. Auditoria de limpeza de 21/07/2026

Uma auditoria estática de todos os arquivos Python do projeto confirmou que não
há funções ou classes sendo sobrescritas por outra definição de mesmo nome no
mesmo escopo. A duplicação encontrada era de responsabilidade e estado, não de
nome de função.

Foram consolidados na mente compartilhada:

- bloqueios temporários de sugestões, no domínio `continuidades`;
- contadores de falhas consecutivas de execução, no domínio `mental`;
- abas sugeridas para fechamento e estado do modo `spinning.fish`, no domínio
  `percepcao`;
- listas e dicionários legados agora permanecem ligados ao lock central, mesmo
  quando um retrato externo do Chrome é mesclado de volta ao estado.

O registro temporal do turno também deixou de ter dois escritores concorrentes.
O refinamento mental é a fonte principal; o registrador temporal isolado ficou
somente como fallback para adaptadores antigos que ainda não devolvem o evento.

Foram removidos auxiliares privados sem chamadas, uma fábrica de maturidade sem
consumidores, uma leitura semântica armazenada sem leitor e APIs SQLite antigas
que restauravam memória quente de sessão ou não possuíam qualquer consumidor.
Imports repetidos ou mortos também foram eliminados.

Continuam globais, por decisão arquitetural, apenas elementos de composição ou
infraestrutura como eventos de sincronização, runtimes, caches internos de um
único serviço, constantes e mapas de configuração. Esses objetos não representam
uma segunda memória nem competem pela interpretação do turno.

A suíte completa após a limpeza terminou com `608 passed, 33 subtests passed`.
