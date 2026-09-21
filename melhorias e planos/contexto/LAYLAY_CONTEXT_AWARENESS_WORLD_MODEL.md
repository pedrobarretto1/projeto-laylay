# LAYLAY — CONTEXT AWARENESS, PRESENCE ENGINE E AUTONOMIA TEMPORAL

## Sistema de percepção ambiental, presença, contexto temporal, eventos e comportamento autônomo

---

# 1. Visão geral

A ideia inicial deste sistema nasceu como um mecanismo simples de **visão computacional usando a webcam do PC como sensor de presença**.

O objetivo original era permitir que a Laylay percebesse se o usuário estava ou não em frente ao computador e reagisse automaticamente:

- usuário presente → funcionamento normal;
- usuário saiu → pausar atividades;
- bloquear a sessão;
- apagar o monitor;
- reduzir consumo;
- se ficar muito tempo ausente → suspender o computador;
- quando voltar → restaurar aquilo que estava acontecendo.

Durante a discussão, porém, ficou claro que depender somente da webcam seria uma limitação grande.

A webcam não precisa ser “a fonte da verdade”.

Ela pode ser apenas **um dos sensores do ambiente**.

A partir disso nasceu uma arquitetura muito mais ampla:

```text
webcam
microfone
mouse/teclado
celular
Wi-Fi
Bluetooth
sensores físicos
estado do Windows
horário
iluminação
atividade atual
memória
eventos temporais
```

Todos esses sinais podem ser combinados pela Laylay para formar uma interpretação do que está acontecendo.

O sistema deixa de responder apenas:

```text
Pedro está aqui?
SIM / NÃO
```

e passa a responder coisas muito mais interessantes:

```text
Pedro provavelmente está em casa.

Pedro provavelmente entrou no quarto.

Pedro está no quarto, mas não está usando o PC.

Pedro acabou de sentar na mesa.

Pedro saiu do quarto.

Pedro saiu de casa.

Pedro provavelmente está retornando.

Pedro acabou de voltar de um evento que começou há três horas.

O ambiente agora está escuro.

A luz está desligada.

Talvez seja útil ligá-la.
```

Isso transforma a Laylay de uma assistente reativa baseada em comandos em uma assistente capaz de manter um **modelo contextual do ambiente ao longo do tempo**.

---

# 2. Conceito principal

A arquitetura deve seguir este princípio:

> **Sensores percebem.  
> O sistema interpreta.  
> A política decide.  
> A Laylay age.**

Nunca:

```python
if rosto_sumiu:
    pausar_musica()
    bloquear_windows()
```

O ideal é:

```text
CAMERA
   ↓
PERCEPTION

"não há uma pessoa visível"

   ↓
PRESENCE FUSION

"existem outras evidências?"

   ↓
PRESENCE STATE

"usuário provavelmente saiu da mesa"

   ↓
CONTEXT / POLICY

"o que devemos fazer nesse estado?"

   ↓
ACTIONS
```

Essa separação é fundamental.

---

# 3. Arquitetura geral

```text
                 LAYLAY CONTEXT AWARENESS

                          SENSORES
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ↓                    ↓                    ↓
     WEBCAM               CELULAR             WINDOWS
        │                    │                    │
   pessoa/rosto        Wi-Fi / BLE / app      mouse/teclado
        │                    │                 idle/session
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ↓
                    PRESENCE FUSION ENGINE
                             │
                             ↓
                       WORLD MODEL
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ↓                ↓                ↓
         PRESENÇA         EVENTOS          AMBIENTE
            │                │                │
            ↓                ↓                ↓
         DESK/ROOM       mercado/date      luz/tempo
        HOUSE/AWAY       prova/viagem       dispositivos
            │                │                │
            └────────────────┼────────────────┘
                             ↓
                    AUTONOMY / POLICY ENGINE
                             │
                ┌────────────┼─────────────┐
                │            │             │
                ↓            ↓             ↓
              AÇÃO         FALA         SILÊNCIO
```

O último item é importante:

```text
SILÊNCIO
```

também deve ser uma decisão válida.

Uma assistente inteligente não precisa comentar tudo o tempo inteiro.

---

# 4. A webcam deixa de ser “a regra”

A webcam inicialmente seria utilizada para:

- detectar se existe uma pessoa;
- detectar rosto;
- reconhecer o usuário;
- estimar presença;
- perceber saída da cadeira;
- perceber retorno.

Porém, ela não deve determinar sozinha o estado.

Exemplo problemático:

```text
frame 1: rosto visível
frame 2: rosto não visível
```

Isso não significa:

```text
PEDRO SAIU
```

Pode significar:

- virou a cabeça;
- abaixou;
- ficou fora do enquadramento;
- câmera perdeu tracking;
- iluminação mudou;
- objeto bloqueou o rosto.

Por isso a visão computacional fornece **evidências**, não decisões finais.

---

# 5. Pipeline da webcam

```text
WEBCAM
   ↓
FRAME
   ↓
PERSON DETECTOR
   ↓
tem pessoa?
   │
   ├── NÃO
   │     ↓
   │  presence evidence = absent
   │
   └── SIM
         ↓
      FACE DETECTOR
         ↓
      tem rosto?
         │
         ├── NÃO
         │    ↓
         │  person present
         │  identity unknown
         │
         └── SIM
               ↓
           FACE IDENTITY
               ↓
          OWNER / UNKNOWN
```

---

# 6. O Python deve processar localmente

O sistema não precisa enviar vídeo constantemente para a IA.

O ideal:

```text
camera frame
    ↓
Python processa
    ↓
extrai informações
    ↓
descarta frame
```

A Laylay recebe somente dados estruturados.

Exemplo:

```json
{
  "presence": true,
  "person_count": 1,
  "face_detected": true,
  "identity": "owner",
  "confidence": 0.96
}
```

Ou:

```json
{
  "presence": false,
  "person_count": 0
}
```

Isso reduz:

- processamento do LLM;
- tráfego;
- armazenamento;
- problemas de privacidade;
- complexidade.

---

# 7. FPS necessário

Esse sistema não precisa rodar em 30 ou 60 FPS.

Presença não é um jogo.

Algo como:

```text
1 FPS
2 FPS
3 FPS
5 FPS
```

já pode ser suficiente dependendo do detector.

A frequência pode inclusive ser dinâmica.

Exemplo:

```text
DESK:
5 FPS

ROOM:
2 FPS

AWAY:
1 FPS
```

---

# 8. Reconhecimento facial

O reconhecimento facial deve servir principalmente como:

```text
provável identidade
```

e não como mecanismo único de autenticação.

Resultado conceitual:

```text
face_owner=true
confidence=0.96
```

Isso pode aumentar muito a confiança de presença.

Porém:

```text
webcam comum + reconhecimento facial
```

não deve automaticamente significar:

```text
desbloquear Windows sem autenticação
```

O retorno pode acordar o ambiente, mas o desbloqueio da sessão deve continuar protegido.

---

# 9. Pessoa desconhecida

Exemplo:

```text
person=true
identity=UNKNOWN
owner_present=false
```

Estado:

```text
UNKNOWN_PERSON
```

Possível política:

```text
keep_session_locked        ✓
restore_private_context    ✗
show_private_notifications ✗
resume_personal_media      ✗
```

O objetivo é proteger a sessão, não criar um sistema de vigilância.

---

# 10. Histerese de presença

O sistema nunca deve reagir a um único frame.

Errado:

```text
frame sem rosto
     ↓
PEDRO SUMIU
```

Correto:

```text
face lost
   ↓
person lost
   ↓
timer
   ↓
continua ausente?
   ↓
confirmar mudança
```

Exemplo:

```text
0s    pessoa perdida
2s    ainda ausente
5s    ainda ausente
10s   ausência confirmada
```

Da mesma forma no retorno:

```text
person detected
      ↓
face detected
      ↓
owner candidate
      ↓
múltiplas confirmações
      ↓
OWNER PRESENT
```

Isso evita comportamento maluco:

```text
bloqueando...
desbloqueando...
bloqueando...
desbloqueando...
```

---

# 11. Presence Manager

A webcam envia sinais para um módulo maior:

```text
Presence Manager
```

Sugestão de estrutura:

```text
mente_laylay/
│
├── presence/
│   ├── camera_runtime.py
│   ├── person_detector.py
│   ├── face_identity.py
│   ├── presence_state.py
│   ├── presence_fusion.py
│   ├── presence_manager.py
│   ├── activity_snapshot.py
│   ├── away_policy.py
│   └── restore_manager.py
```

---

# 12. Estados iniciais de presença

Versão simples:

```text
PRESENT
   ↓
AWAY_GRACE
   ↓
AWAY
   ↓
LONG_AWAY
   ↓
DEEP_AWAY
```

## PRESENT

Usuário confirmado no PC.

## AWAY_GRACE

Ausência momentânea.

Nenhuma ação ainda.

## AWAY

Usuário provavelmente saiu da mesa.

## LONG_AWAY

Ausência prolongada.

Pode reduzir recursos.

## DEEP_AWAY

Usuário claramente está fora por longo período.

Pode permitir suspensão/hibernação se houver mecanismo externo de retorno.

---

# 13. Snapshot antes de agir

Quando a Laylay detectar saída real, ela não deve simplesmente pausar tudo.

Primeiro cria um snapshot.

Exemplo:

```json
{
  "music": {
    "playing": true,
    "track": "Tim Maia",
    "position": 132
  },

  "game": {
    "process": "minecraft.exe",
    "was_active": true,
    "paused_by_laylay": false
  },

  "browser": {
    "youtube_playing": false
  },

  "lights": {
    "room": true
  },

  "system": {
    "screen_locked": false
  }
}
```

Depois decide o que fazer.

---

# 14. Regra fundamental de restauração

A Laylay deve restaurar **somente aquilo que ela mesma interrompeu**.

Exemplo:

Antes de sair:

```text
music.playing=false
```

Então no retorno:

```text
não tocar música
```

Se:

```text
music.playing=true
```

e a Laylay pausou:

```text
paused_by_laylay=true
```

então pode restaurar.

Mesma regra para:

- vídeo;
- música;
- jogo;
- luz;
- monitor;
- modos;
- outros estados.

---

# 15. Exemplo de saída

Você está usando o PC:

```text
[PRESENCE]
state=DESK
identity=owner
```

Você levanta.

```text
[15:30:01] [VISION]
person_lost

[15:30:11] [PRESENCE]
DESK → AWAY
```

A Laylay verifica:

```text
music.playing       = true
game.running        = true
youtube.playing     = false
download.active     = true
```

Cria snapshot.

Depois:

```text
pause music       ✓
pause game        ✓
lock PC           ✓
screen off        ✓
sleep PC          ✗
reason:
active download
```

Comentário DEV:

```text
[LAYLAY/DEV]
ele sumiu. vou cuidar daqui.
```

---

# 16. O problema da suspensão

Se o próprio PC suspender:

```text
Python dorme
CPU dorme
webcam deixa de ser processada
Laylay dorme
```

Então existe um paradoxo:

```text
Laylay suspende PC
      ↓
precisa perceber retorno
      ↓
mas está suspensa
```

---

# 17. Solução versão 1

Sem hardware adicional:

```text
WINDOWS LOCKED
MONITOR OFF
PYTHON RUNNING
LAYLAY RUNNING
WEBCAM RUNNING
```

O computador continua ligado, porém protegido e podendo trabalhar em modo reduzido.

Quando o usuário retorna:

```text
camera detects owner
        ↓
monitor wakes
        ↓
Windows lock screen
        ↓
usuário autentica
        ↓
restore snapshot
```

---

# 18. Solução versão 2 — observador externo

Futuramente:

```text
           PRESENCE NODE
                │
          sempre ligado
                │
           detecta retorno
                │
                ↓
             WAKE PC
                │
                ↓
          LAYLAY STARTS
                │
                ↓
           RESTORE STATE
```

O Presence Node pode ser:

- pequeno computador;
- microcontrolador mais avançado;
- roteador;
- dispositivo IoT;
- serviço do celular;
- outro nó da rede.

---

# 19. O celular como sensor

Durante a discussão surgiu uma melhoria extremamente importante:

> o celular pode ser um dos sensores principais da presença.

Hoje é raro sair de casa sem o celular.

Portanto:

```text
celular presente
```

é uma forte evidência de:

```text
usuário provavelmente presente naquela região
```

Mas nunca uma confirmação absoluta.

---

# 20. Zonas de presença

Em vez de somente:

```text
PRESENT / AWAY
```

o sistema pode entender zonas:

```text
AWAY
HOUSE
ROOM
DESK
```

Fluxo:

```text
           ┌─────────────────┐
           │      AWAY       │
           │ fora de casa    │
           └────────┬────────┘
                    │
               celular aparece
                    ↓
           ┌─────────────────┐
           │      HOUSE      │
           │ provavelmente   │
           │ em casa         │
           └────────┬────────┘
                    │
          rede/AP do quarto
                    ↓
           ┌─────────────────┐
           │      ROOM       │
           │ provavelmente   │
           │ no quarto       │
           └────────┬────────┘
                    │
          camera + identidade
          mouse / teclado
                    ↓
           ┌─────────────────┐
           │      DESK       │
           │ usando o PC     │
           └─────────────────┘
```

---

# 21. Por que isso é melhor?

Porque:

```text
celular no quarto
```

não significa necessariamente:

```text
Pedro na cadeira
```

Talvez o celular esteja:

- na cama;
- carregando;
- esquecido;
- enquanto o usuário está em outro lugar.

Portanto:

```text
Wi-Fi do quarto
```

significa:

> provável presença na zona ROOM.

Já:

```text
Wi-Fi do quarto
+
webcam owner
+
mouse ativo
```

significa:

> altíssima probabilidade de DESK.

---

# 22. Presence Fusion Engine

A arquitetura fica:

```text
                 ┌──────────────┐
                 │ ROOM WI-FI   │
                 └──────┬───────┘
                        │
 ┌───────────┐          │          ┌────────────┐
 │  WEBCAM   │──────────┼──────────│ BLUETOOTH  │
 └───────────┘          │          └────────────┘
                        ↓
                PRESENCE FUSION
                        ↑
 ┌───────────┐          │          ┌────────────┐
 │ MOUSE/KB  │──────────┼──────────│ MICROPHONE │
 └───────────┘          │          └────────────┘
                        │
                 ┌──────┴───────┐
                 │ PHONE AGENT  │
                 └──────────────┘
```

---

# 23. Saída do Fusion Engine

Não:

```json
{
  "present": true
}
```

Mas:

```json
{
  "state": "ROOM",

  "evidence": {
    "phone_wifi": true,
    "phone_ble": true,
    "camera_person": false,
    "camera_owner": false,
    "recent_input": false
  }
}
```

---

# 24. Hierarquia de evidências

## Evidências fortes

```text
rosto reconhecido
atividade recente de mouse/teclado
app do celular confirmando proximidade
sessão Windows desbloqueada
```

## Evidências médias

```text
celular na rede do quarto
Bluetooth próximo
pessoa na webcam
```

## Evidências fracas

```text
som no ambiente
movimento genérico
última presença recente
```

Nenhuma fonte precisa mandar sozinha.

---

# 25. App do celular

Em vez de depender somente de IP/MAC/ping, futuramente o app da Laylay pode ter um pequeno agente.

Exemplo:

```json
{
  "device": "phone_owner",
  "online": true,
  "wifi_zone": "bedroom",
  "bluetooth_pc": true,
  "heartbeat": true
}
```

A Laylay teria:

```text
PHONE_AGENT

online       ✓
zone         bedroom
last_seen    2s
```

---

# 26. Heartbeat do celular

O celular poderia enviar pequenos heartbeats:

```text
PHONE HEARTBEAT
every N seconds
```

Conteúdo mínimo:

```json
{
  "device_id": "owner_phone",
  "zone": "room",
  "online": true
}
```

Não precisa enviar:

- fotos;
- GPS;
- áudio;
- dados privados.

---

# 27. Bluetooth

Bluetooth pode servir como uma pista adicional de proximidade.

Não como distância exata.

Categorias aproximadas:

```text
NOT_VISIBLE
FAR
NEAR
VERY_NEAR
```

Exemplo:

```text
Wi-Fi room    ✓
Bluetooth     VERY_NEAR
camera owner  ✓
```

Resultado:

```text
DESK_CONFIRMED
```

---

# 28. Mouse e teclado

O Windows fornece uma pista excelente:

```text
mouse movement
keyboard input
idle time
active window
session lock
session unlock
```

Exemplo:

```text
camera owner=true
phone room=true
windows_idle=0s
```

Conclusão:

```text
DESK
```

Já:

```text
camera=false
phone room=true
windows_idle=17min
```

Conclusão provável:

```text
ROOM
```

---

# 29. Microfone como sensor

O microfone não precisa necessariamente transcrever.

Pode fornecer apenas:

```text
ambient_activity=true
voice_activity=true
```

Exemplo:

```text
phone room=true
voice_activity=true
camera=false
```

Conclusão:

> provavelmente existe atividade humana no quarto, mas o usuário não está confirmado na mesa.

---

# 30. Sensores futuros

O Context Awareness pode futuramente receber:

```text
webcam
microfone
mouse
teclado
celular
Wi-Fi
Bluetooth
sensor PIR
sensor de porta
sensor de luz
dispositivos Tuya
smartwatch
outro PC
roteador
```

---

# 31. Memória temporal de presença

Mudanças não devem ser analisadas de maneira isolada.

Exemplo:

```text
23:40:00 DESK
23:40:12 camera lost
23:40:13 camera detected
```

Conclusão:

```text
ruído
```

Não:

```text
PEDRO DESAPARECEU
```

Já:

```text
23:40 DESK
23:41 camera absent
23:42 input absent
23:43 phone leaves room
```

Forma uma sequência coerente:

```text
DESK → ROOM → HOUSE
```

---

# 32. Arrival Prediction

Uma evolução interessante é a Laylay **antecipar o retorno**.

Exemplo:

```text
18:27:01
phone network = HOME

18:27:14
phone network = ROOM

18:27:16
bluetooth_pc = detected

[PRESENCE]
arrival_probability rising
```

A Laylay pode começar a preparar o ambiente:

```text
wake PC
load lightweight services
restore network agents
prepare microphone
prepare camera
prepare memory
```

Sem abrir a sessão pessoal ainda.

Quando:

```text
ROOM ✓
CAMERA OWNER ✓
```

entra em:

```text
DESK
```

---

# 33. Saída gradual

O inverso também funciona.

```text
DESK
 ↓
sem input
 ↓
camera lost
 ↓
ROOM
```

Ainda existe celular na rede do quarto.

Então ela não precisa imediatamente suspender tudo.

Depois:

```text
phone leaves ROOM
+
camera absent
+
input absent
```

Então:

```text
ROOM → HOUSE
```

Depois:

```text
phone leaves HOUSE
```

Então:

```text
HOUSE → AWAY
```

---

# 34. Políticas por zona

## DESK

```text
LLM ativo
voz ativa
tela ativa
contexto completo
música normal
```

## ROOM

```text
usuário próximo
monitor pode apagar
música pode continuar
Laylay continua atenta
serviços principais ativos
```

## HOUSE

```text
sessão bloqueada
mídia pode ser pausada
recursos reduzidos
privacidade reforçada
```

## AWAY

```text
snapshot persistido
sessão protegida
modo economia
suspensão permitida
```

---

# 35. Wake-on-LAN / nó de rede

Uma evolução futura:

```text
       ROUTER / ROOM NODE
              │
         phone appears
              │
              ↓
          WAKE SIGNAL
              │
              ↓
             PC
              │
              ↓
          Laylay starts
              │
              ↓
      camera confirmation
              │
              ↓
            DESK
```

O próprio ambiente pode se tornar o “sentinela” enquanto o computador principal está dormindo.

---

# 36. Context Awareness

Com tudo isso, presença passa a ser somente uma parte de algo maior.

```text
CONTEXT AWARENESS
│
├── Presence
│   ├── webcam
│   ├── phone
│   ├── network
│   ├── Bluetooth
│   └── input
│
├── Environment
│   ├── time
│   ├── daylight
│   ├── room light
│   ├── audio
│   └── devices
│
├── Activity
│   ├── gaming
│   ├── coding
│   ├── study
│   ├── music
│   └── idle
│
└── State
    ├── DESK
    ├── ROOM
    ├── HOUSE
    └── AWAY
```

---

# 37. Evolução para compreensão temporal

A segunda grande evolução é:

> a Laylay não entender somente onde o usuário está, mas **o que aconteceu antes e quanto tempo se passou**.

Exemplo:

```text
15:27
Pedro:
"tô saindo para um encontro"

15:30
DESK → ROOM → HOUSE → AWAY
```

A Laylay cria um evento temporal.

---

# 38. Open Events

Quando o usuário declara uma atividade relevante que vai acontecer fora daquele contexto, a Laylay pode criar um:

```text
OPEN EVENT
```

Exemplo:

```json
{
  "event_id": "EVT_4932",
  "type": "outing",
  "subtype": "date",
  "status": "open",

  "declared_at": "15:27",
  "departure_at": "15:30",

  "return_at": null,

  "expected_duration": {
    "confidence": "low"
  }
}
```

---

# 39. Estados de um evento

```text
DECLARED
    ↓
DEPARTING
    ↓
AWAY
    ↓
RETURNING
    ↓
ARRIVED
    ↓
FOLLOW_UP
    ↓
CLOSED
```

---

# 40. Declaração

Usuário:

```text
"vou sair para um encontro"
```

Evento:

```text
DECLARED
```

Ainda não necessariamente começou.

---

# 41. Confirmação física

Depois:

```text
phone leaves ROOM
phone leaves HOUSE
```

Agora:

```text
EVENT CONFIRMED
```

A conversa foi confirmada pelo mundo físico.

Esse conceito é muito importante:

> **o mundo pode confirmar ou contradizer a linguagem.**

---

# 42. Intenção não é evento

Usuário:

```text
"acho que vou no mercado mais tarde"
```

Isso não cria imediatamente:

```text
MARKET_EVENT OPEN
```

Cria talvez:

```text
INTENTION
maybe_market
```

Agora:

```text
"vou no mercado agora"
```

+

```text
phone leaves house
```

→ evento confirmado.

---

# 43. Expectativa temporal flexível

A Laylay não deve usar temporizadores rígidos.

Errado:

```python
if event == "market":
    expected_duration = 30_minutes
```

ou:

```python
if event == "date":
    expected_duration = 2_hours
```

A realidade varia demais.

---

# 44. Duração como distribuição plausível

Exemplo conceitual para mercado:

```text
0–20 min      possível
20–90 min     bastante plausível
1–3 h         ainda plausível
3h+           menos comum
```

Isso não representa regra absoluta.

Representa uma expectativa com incerteza.

---

# 45. Exemplo — encontro curto

Usuário:

```text
"vou para um encontro"
```

Sai às:

```text
15:30
```

Volta:

```text
16:01
```

A Laylay não deve pensar:

```text
ERRO
UM ENCONTRO TEM QUE DURAR MAIS
```

Ela pode interpretar:

```text
duration=31min
shorter_than_typical=true
still_plausible=true
```

E falar naturalmente:

```text
"ué, já voltou? como foi?"
```

Sem assumir que houve problema.

---

# 46. Exemplo — mercado demorado

Usuário:

```text
"vou no mercado"
```

Sai às:

```text
14:00
```

Retorna às:

```text
17:00
```

A Laylay pode perceber:

```text
duration=3h
longer_than_usual=true
```

Mas não deve concluir automaticamente:

```text
algo ruim aconteceu
```

Quando o usuário retorna, pode perguntar:

```text
"demorou dessa vez, aconteceu alguma coisa?"
```

---

# 47. Aprender duração pessoal

Com o tempo:

```text
market trip #1   38m
market trip #2   52m
market trip #3   1h14
market trip #4   44m
market trip #5   2h03
```

A Laylay pode aprender:

```text
personal pattern:
typical ~50m

variance:
high
```

Isso é superior a usar expectativas genéricas.

---

# 48. Expectativa = semântica + histórico

Conceitualmente:

```text
tipo do evento
+
histórico pessoal
+
horário
+
dia
+
tempo transcorrido
+
contexto atual
=
expectativa temporal
```

---

# 49. Níveis de atraso

Não:

```text
expected=1h
elapsed=1h01
ALERTA
```

Mas:

```text
EXPECTED
   ↓
SLIGHTLY LONG
   ↓
UNUSUALLY LONG
   ↓
SIGNIFICANTLY OUTSIDE PATTERN
```

---

# 50. Contexto altera expectativa

Exemplo:

```text
"vou comprar pão"
```

4 horas fora:

```text
bastante incomum
```

Já:

```text
"vou sair com uns amigos"
```

4 horas:

```text
totalmente plausível
```

---

# 51. Nem atraso gera intervenção

A Laylay não deve mandar mensagens ou alertas só porque uma duração passou da média.

Ela deve avaliar:

```text
evento incomum
      ↓
há razão concreta para intervir?
```

Se não:

```text
aguardar
```

Quando o usuário retornar, pode mencionar naturalmente.

---

# 52. Importância do evento

Nem todo evento merece acompanhamento.

Exemplo:

```text
pegar água
importance=0.03
```

```text
banho
importance=0.10
```

```text
mercado
importance=0.30
```

```text
encontro
importance=0.65
```

```text
prova
importance=0.85
```

```text
entrevista
importance=0.90
```

```text
viagem
importance=0.95
```

Os números são apenas conceituais.

---

# 53. Relevância conversacional

Nem todo retorno precisa produzir pergunta.

Exemplo:

```text
pegar água
→ silêncio

lavar mãos
→ silêncio

banho
→ normalmente silêncio

mercado
→ talvez

encontro
→ provavelmente perguntar

prova
→ provavelmente perguntar

entrevista
→ provavelmente perguntar

viagem
→ quase certamente perguntar
```

---

# 54. Silêncio inteligente

Isso é essencial.

A Laylay pode perceber:

```text
Pedro saiu da cadeira.
Foi buscar água.
Voltou três minutos depois.
```

E decidir:

```text
NO_ACTION
NO_SPEECH
```

Isso é inteligência.

Se ela comentar cada movimento, rapidamente ficaria irritante.

---

# 55. Exemplo completo — encontro

Usuário:

```text
15:27
"tô saindo para um encontro"
```

Evento:

```text
EVT_4932
type=date
state=DECLARED
```

Depois:

```text
15:30
DESK → ROOM

15:31
ROOM → HOUSE

15:32
HOUSE → AWAY
```

Evento:

```text
state=AWAY
start=15:30
```

---

# 56. Retorno às 18:30

Sinais:

```text
18:27
phone network=HOME

18:28
phone network=ROOM

18:28
Bluetooth PC=NEAR

18:29
camera owner=true
```

Presence:

```text
AWAY → HOUSE → ROOM → DESK
```

Temporal Context:

```text
away_since        15:30
returned_at       18:29
duration          2h59
declared_event    date
```

---

# 57. Ambiente no retorno

Agora:

```text
time             18:29
daylight         low
room_light       off
owner_returned   true
```

A Laylay pode inferir:

```text
usuário voltou
+
ambiente escuro
+
luz desligada
+
ação simples e reversível
=
ligar luz
```

---

# 58. Autonomia ambiental

```text
[18:29:12] [AUTONOMY]

action:
room_light_on

reason:
OWNER_RETURNED
+
LOW_LIGHT
+
ROOM_OCCUPIED
```

Depois:

```text
[LAYLAY]
"bem-vindo de volta."
```

E:

```text
"e aí, como foi o encontro?"
```

---

# 59. Contexto ganha de regra simples

Não usar:

```python
if hour >= 18:
    light_on()
```

Usar algo parecido conceitualmente com:

```text
owner returned
+
room occupied
+
ambient light low
+
light off
+
no conflicting mode
=
LIGHT_ON
```

---

# 60. Exceções ambientais

Exemplo:

```text
owner returned
+
ambient light low
+
movie mode active
```

Resultado:

```text
não ligar luz principal
```

Ou:

```text
owner returned
+
sleep mode active
```

Resultado:

```text
usar iluminação fraca
```

---

# 61. Follow-up contextual

O evento anterior permanece aberto até haver um possível fechamento.

Exemplo:

```text
OPEN EVENT:
date
```

No retorno:

```text
FOLLOW_UP CANDIDATE
"como foi o encontro?"
```

Usuário:

```text
"foi muito bom"
```

Evento pode virar:

```text
status=CLOSED
outcome=positive
```

---

# 62. Outro exemplo

Usuário:

```text
"vou fazer uma prova"
```

Evento:

```text
importance=high
```

Ao retornar:

```text
"e aí, como foi a prova?"
```

Isso demonstra continuidade da conversa ao longo de horas.

---

# 63. Não precisa guardar tudo permanentemente

Eventos podem ter diferentes níveis de retenção.

Exemplo:

```text
pegar água
→ descartável

mercado
→ curto prazo

prova
→ possivelmente memória relevante

entrevista
→ possivelmente memória relevante
```

---

# 64. Event Understanding

Novo módulo conceitual:

```text
event_understanding/
│
├── event_detector.py
├── event_tracker.py
├── event_timeline.py
├── event_expectation.py
├── event_importance.py
├── followup_manager.py
└── temporal_context.py
```

---

# 65. Contexto temporal

A Laylay precisa entender:

```text
quando algo começou
quanto tempo passou
o que aconteceu durante esse período
qual evento estava aberto
como o ambiente mudou
```

---

# 66. Temporal Context

Exemplo:

```json
{
  "current_time": "18:29",

  "recent_transition": {
    "from": "AWAY",
    "to": "DESK"
  },

  "absence": {
    "started": "15:30",
    "duration_minutes": 179
  },

  "open_event": {
    "type": "date"
  }
}
```

---

# 67. World Model

Toda essa informação pode alimentar algo conceitualmente chamado:

```text
LAYLAY WORLD MODEL
```

Não precisa ser necessariamente uma rede neural ou modelo gigantesco.

Pode ser simplesmente a representação estruturada do estado atual.

---

# 68. Exemplo de World Model

```text
WORLD MODEL

USER
├── presence: DESK
├── identity: owner
├── recently_returned: true
├── away_duration: 2h59
└── current_activity: none

ENVIRONMENT
├── time: 18:29
├── daylight: low
├── room_light: off
└── PC: awake

OPEN EVENTS
└── EVT_4932
    ├── type: date
    ├── duration: 2h59
    ├── importance: medium_high
    └── state: arrived

DEVICES
├── phone: room
├── chrome: connected
├── lamp: off
└── PC: unlocked

PREVIOUS ACTIVITY
├── coding
├── music
└── interrupted_by: outing
```

---

# 69. Decisão a partir do World Model

Entrada:

```text
recently_returned=true
event=date
ambient_light=low
previous_activity=coding
```

Possível decisão:

```text
1. ligar luz;
2. cumprimentar;
3. perguntar sobre encontro;
4. não restaurar tudo imediatamente;
5. depois perguntar se quer continuar o que estava fazendo.
```

Isso é muito mais natural do que simplesmente:

```text
RETURN → RUN MACRO
```

---

# 70. Autonomia em níveis

Para a Laylay ser autônoma sem ficar perigosa ou irritante, ações podem ter níveis.

---

## NÍVEL 1 — autonomia segura

Ações:

```text
ligar luz quando está escuro
pausar mídia quando usuário sai
restaurar mídia que ela mesma pausou
apagar monitor
preparar PC no retorno
reduzir serviços
ajustar contexto
```

Características:

```text
baixo risco
reversível
impacto pequeno
```

---

## NÍVEL 2 — sugestão

Exemplos:

```text
"quer que eu volte a música?"

"quer continuar o projeto?"

"você demorou dessa vez, aconteceu alguma coisa?"

"quer que eu abra o que você estava usando?"
```

---

## NÍVEL 3 — alto impacto

Exemplos:

```text
fechar programas
encerrar tarefas importantes
desligar PC
alterar arquivos
ações externas irreversíveis
```

Devem respeitar políticas específicas e permissões.

---

# 71. Exemplo — retorno normal

```text
18:28 phone room ✓
18:29 camera owner ✓
18:29 DESK ✓
18:29 ambient light low ✓
```

Ações:

```text
wake display
light on
restore Laylay full mode
```

Conversa:

```text
"voltou."
```

Se evento relevante aberto:

```text
"e aí, como foi?"
```

---

# 72. Exemplo — retorno rápido

Evento:

```text
date
```

Duração:

```text
31 minutos
```

A Laylay não assume problema.

Possível reação:

```text
"ué, já voltou? como foi?"
```

---

# 73. Exemplo — retorno muito demorado

Evento:

```text
market
```

Histórico:

```text
normalmente 40–70 minutos
```

Duração atual:

```text
3h20
```

Ao retornar:

```text
"demorou dessa vez, aconteceu alguma coisa?"
```

Não:

```text
"VOCÊ ESTÁ 2 HORAS E 10 MINUTOS ATRASADO."
```

---

# 74. Exemplo — banho

Usuário:

```text
"vou tomar banho"
```

Presence:

```text
DESK → ROOM
```

Phone:

```text
still room
```

Tempo:

```text
15 min
```

Retorno:

```text
ROOM → DESK
```

Ação:

```text
restore monitor
```

Fala:

```text
nenhuma
```

Porque:

```text
event_importance=low
followup_relevance=low
```

---

# 75. Exemplo — prova

Usuário:

```text
"vou fazer uma prova"
```

Evento:

```text
importance=high
followup_relevance=high
```

Quando retorna:

```text
"e aí, como foi a prova?"
```

Isso produz continuidade real.

---

# 76. Reatividade baseada no passado

A Laylay não reage somente ao presente.

Ela combina:

```text
PASSADO
+
TEMPO
+
PRESENTE
+
AMBIENTE
+
MEMÓRIA
```

Exemplo:

```text
PASSADO
"vou para um encontro"

TEMPO
3 horas passaram

PRESENTE
Pedro voltou

AMBIENTE
está escuro

MEMÓRIA
evento ainda aberto
```

Resultado:

```text
ligar luz
cumprimentar
perguntar sobre encontro
```

---

# 77. World Model como centro

Arquitetura evoluída:

```text
                         SENSORS
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ↓              ↓              ↓
         PRESENCE       ENVIRONMENT      SYSTEM
             │              │              │
             └──────────────┼──────────────┘
                            ↓
                       WORLD MODEL
                            ↑
                            │
                    TEMPORAL CONTEXT
                            ↑
                            │
                        OPEN EVENTS
                            ↑
                            │
                         MEMORY
                            │
                            ↓
                      POLICY ENGINE
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
           ACTION          SPEECH         SILENCE
```

---

# 78. Mudança filosófica da Laylay

Assistente tradicional:

```text
COMANDO
   ↓
RESPOSTA
```

Laylay com Context Awareness:

```text
PERCEPÇÃO
   ↓
MEMÓRIA
   ↓
TEMPO
   ↓
CONTEXTO
   ↓
EXPECTATIVAS
   ↓
EVENTOS
   ↓
WORLD MODEL
   ↓
DECISÃO
   ↓
AÇÃO / FALA / SILÊNCIO
```

---

# 79. O mundo físico confirma a conversa

Exemplo:

Usuário:

```text
"tô indo"
```

Contexto anterior:

```text
falando sobre mercado
```

Sensores:

```text
phone leaves room
phone leaves house
```

Inferência:

```text
declared intention
+
physical departure
=
market outing started
```

Isso conecta linguagem e ambiente.

---

# 80. O mundo físico também pode contradizer

Usuário:

```text
"vou sair agora"
```

Mas:

```text
30 minutos depois
phone still room
camera owner still present
keyboard active
```

Então o sistema não deve registrar:

```text
OUTING STARTED
```

Talvez o evento continue apenas como:

```text
DECLARED / NOT_CONFIRMED
```

---

# 81. Estado do evento

Possíveis estados:

```text
DECLARED
CONFIRMED
IN_PROGRESS
RETURN_CANDIDATE
ARRIVED
FOLLOW_UP
CLOSED
CANCELLED
EXPIRED
```

---

# 82. Eventos podem ser cancelados

Usuário:

```text
"acho que vou sair"
```

Depois:

```text
"deixa pra lá"
```

Evento/intenção:

```text
CANCELLED
```

---

# 83. Evento expirado

Se uma intenção nunca for confirmada:

```text
"talvez eu vá no mercado"
```

e horas passam sem saída:

```text
EXPIRED
```

Não vira memória permanente importante.

---

# 84. Reatividade e preocupação

A Laylay pode perceber duração incomum.

Mas isso não significa preocupação automática.

Existe diferença entre:

```text
NOTABLE
```

e:

```text
ACTIONABLE
```

Exemplo:

```text
market trip unusually long
```

→ notable.

Mas sem motivo adicional:

```text
do nothing
```

No retorno:

```text
natural follow-up
```

---

# 85. Contexto do horário

O horário influencia ações.

Exemplo:

```text
saída 15:30
retorno 18:30
```

Durante a ausência:

```text
daylight changed:
bright → low
```

No retorno:

```text
room now dark
```

Isso pode gerar:

```text
LIGHT_ON
```

---

# 86. Mudança do ambiente durante ausência

Outros exemplos:

```text
temperatura aumentou
luz natural diminuiu
música ainda está pausada
ventilador desligado
PC entrou em modo reduzido
```

O retorno pode reavaliar tudo com base no **estado atual**, não somente restaurar cegamente o snapshot antigo.

---

# 87. Snapshot não é ordem absoluta

Importante:

```text
snapshot antigo
```

representa como as coisas estavam.

Não significa:

```text
restaurar obrigatoriamente tudo igual
```

Porque o mundo pode ter mudado.

Exemplo:

Antes:

```text
luz off
15:30
ambiente claro
```

Retorno:

```text
18:30
ambiente escuro
```

Restaurar:

```text
luz off
```

seria burro.

Então:

```text
snapshot
+
current environment
=
restore decision
```

---

# 88. Restore Manager inteligente

```text
RESTORE MANAGER
│
├── previous state
├── current world state
├── user presence
├── current environment
├── policies
└── conflicting modes
```

Saída:

```text
restore
modify
ask
ignore
```

---

# 89. Exemplo de restauração

Antes:

```text
music=true
light=false
coding=true
```

Depois de três horas:

```text
ambient_dark=true
user_recently_returned=true
```

Resultado:

```text
light → ON
music → maybe restore
coding → do not immediately force
```

Pode perguntar:

```text
"quer voltar pro projeto?"
```

---

# 90. Activity Context

O World Model também acompanha a atividade.

Exemplo:

```text
ACTIVITY

type              coding
app               VS Code
project            Laylay
music              playing
started_at         14:20
interrupted_at     15:30
reason             outing
```

Ao retornar:

```text
previous_activity available
```

Então a Laylay pode perguntar:

```text
"quer continuar de onde parou?"
```

---

# 91. Eventos e atividades são diferentes

Atividade:

```text
coding
gaming
watching video
studying
```

Evento:

```text
market trip
date
exam
appointment
outing
```

Os dois se relacionam.

Exemplo:

```text
activity coding
   ↓
interrupted by
   ↓
event date
```

---

# 92. Contexto reativo

A Laylay deve conseguir agir porque algo mudou.

Não apenas porque o usuário mandou um comando.

Exemplos:

```text
owner leaves desk
→ pause media

owner returns at night
→ light on

phone reconnects room
→ prepare PC

unknown person appears
→ maintain privacy

user returns from relevant event
→ contextual follow-up
```

---

# 93. Autonomia não significa ação constante

A arquitetura deve sempre considerar:

```text
NO_ACTION
```

como opção.

Exemplo:

```text
owner moved from desk to bed
phone room=true
camera person=true
```

Talvez:

```text
NO_ACTION
```

se não houver motivo para interferir.

---

# 94. Autonomia e personalidade

A Laylay também pode usar sua personalidade nos retornos.

Sem ficar repetitiva.

Exemplo casual:

```text
"olha quem voltou."
```

Evento relevante:

```text
"e aí, como foi o encontro?"
```

Retorno rápido:

```text
"ué, já voltou?"
```

Ausência longa:

```text
"demorou dessa vez."
```

Mas isso precisa variar e respeitar o contexto.

---

# 95. DEV Console

Todo esse sistema deve aparecer no DEV Console criado anteriormente.

Categorias adicionais:

```text
[VISION]
[PRESENCE]
[PRESENCE/FUSION]
[PHONE]
[BLUETOOTH]
[INPUT]
[ENVIRONMENT]
[EVENT]
[TEMPORAL]
[WORLD_MODEL]
[AUTONOMY]
[RESTORE]
```

---

# 96. Exemplo DEV — saída

```text
[15:27:44.103] [USER]
> "tô saindo para um encontro"

[15:27:44.221] [EVENT]
created EVT_4932
type=outing
subtype=date
state=DECLARED
importance=0.72

[15:30:01.208] [VISION]
owner_lost

[15:30:11.211] [PRESENCE]
DESK → ROOM

[15:30:16.513] [PHONE]
zone ROOM → HOUSE

[15:31:42.082] [PHONE]
zone HOUSE → AWAY

[15:31:42.085] [EVENT]
EVT_4932
state=IN_PROGRESS

[15:31:42.090] [SNAPSHOT]
activity=coding
music=true
game=false

[15:31:42.102] [AUTONOMY]
pause_media=true
lock_pc=true
screen_off=true

[15:31:42.109] [LAYLAY/DEV]
certo. a casa é minha agora.
```

---

# 97. Exemplo DEV — retorno

```text
[18:27:51.401] [PHONE]
zone AWAY → HOUSE

[18:28:10.222] [PRESENCE/FUSION]
return_probability=0.63

evidence:
phone_home=true

[18:28:20.183] [PHONE]
zone HOUSE → ROOM

[18:28:20.190] [BLUETOOTH]
owner_phone=NEAR

[18:28:20.194] [PRESENCE/FUSION]
return_probability=0.86

[18:28:21.003] [AUTONOMY]
prepare_workstation=true

[18:29:11.550] [VISION]
owner_detected
confidence=0.96

[18:29:11.561] [PRESENCE]
ROOM → DESK

[18:29:11.570] [TEMPORAL]
absence_duration=2h59m

[18:29:11.577] [EVENT]
EVT_4932
state=ARRIVED

[18:29:11.591] [ENVIRONMENT]
ambient_light=LOW
room_light=OFF

[18:29:11.601] [WORLD_MODEL]
recent_return=true
open_event=date
environment_dark=true

[18:29:11.615] [AUTONOMY]
decision=LIGHT_ON
reason=OWNER_RETURNED + LOW_LIGHT

[18:29:11.711] [DEVICE][TUYA]
lampada_quarto
state=ON
confirmed=true

[18:29:12.001] [CONVERSATION]
followup_candidate=true
topic=EVT_4932

[18:29:12.010] [LAYLAY/DEV]
três horas. parece que o cidadão teve assunto.
```

---

# 98. World Model no DEV Console

Comando:

```text
laylay.dev > world
```

Resultado:

```text
LAYLAY WORLD MODEL

USER
presence             DESK
identity             OWNER
recently_returned    true
away_duration        2h59m

ENVIRONMENT
time                 18:29
daylight             LOW
room_light           ON

PHONE
state                ONLINE
zone                 ROOM
bluetooth            NEAR

OPEN EVENT
id                   EVT_4932
type                 date
state                ARRIVED
duration             2h59m
importance           HIGH

PREVIOUS ACTIVITY
type                 coding
app                  VS Code
restorable           true

AUTONOMY
last_action          room_light_on
reason               OWNER_RETURNED + LOW_LIGHT
```

---

# 99. Trace de presença

```text
laylay.dev > trace presence
```

Resultado:

```text
════════════ PRESENCE TRACE ════════════

18:27:51 PHONE HOME
             ↓
HOUSE

18:28:20 PHONE ROOM
             ↓
ROOM candidate

18:28:20 BLE NEAR
             ↓
ROOM high confidence

18:29:11 CAMERA OWNER
             ↓
DESK candidate

18:29:12 INPUT ACTIVE
             ↓
DESK confirmed

FINAL:
DESK

════════════════════════════════════════
```

---

# 100. Trace de decisão autônoma

```text
laylay.dev > trace autonomy last
```

```text
══════════ AUTONOMY TRACE ══════════

TRIGGER
owner_returned

WORLD STATE
presence        DESK
time            18:29
ambient_light   LOW
room_light      OFF

CANDIDATES

NO_ACTION          valid
LIGHT_ON           preferred
RESTORE_ALL        rejected
ASK_FIRST          unnecessary

DECISION
LIGHT_ON

RISK
LOW

REVERSIBLE
YES

RESULT
CONFIRMED

════════════════════════════════════
```

---

# 101. Módulos sugeridos

Arquitetura futura:

```text
mente_laylay/
│
├── awareness/
│   │
│   ├── presence/
│   │   ├── camera_runtime.py
│   │   ├── person_detector.py
│   │   ├── face_identity.py
│   │   ├── phone_presence.py
│   │   ├── bluetooth_presence.py
│   │   ├── windows_activity.py
│   │   ├── microphone_activity.py
│   │   ├── presence_fusion.py
│   │   └── presence_manager.py
│   │
│   ├── environment/
│   │   ├── time_context.py
│   │   ├── light_context.py
│   │   ├── device_context.py
│   │   └── environment_state.py
│   │
│   ├── events/
│   │   ├── event_detector.py
│   │   ├── event_tracker.py
│   │   ├── event_timeline.py
│   │   ├── event_importance.py
│   │   ├── event_expectation.py
│   │   └── followup_manager.py
│   │
│   ├── temporal/
│   │   ├── temporal_context.py
│   │   ├── duration_model.py
│   │   └── pattern_learning.py
│   │
│   ├── activity/
│   │   ├── activity_detector.py
│   │   ├── activity_snapshot.py
│   │   └── restore_manager.py
│   │
│   └── world_model/
│       ├── world_state.py
│       ├── world_model.py
│       └── context_fusion.py
│
└── autonomy/
    ├── autonomy_engine.py
    ├── policy_engine.py
    ├── action_risk.py
    ├── decision_candidates.py
    └── autonomy_trace.py
```

---

# 102. JSON conceitual do World Model

```json
{
  "user": {
    "presence": "DESK",
    "identity": "owner",
    "recently_returned": true
  },

  "presence": {
    "confidence": 0.97,

    "evidence": {
      "camera_owner": true,
      "phone_room": true,
      "bluetooth_near": true,
      "recent_input": true
    }
  },

  "environment": {
    "time": "18:29",
    "daylight": "low",
    "room_light": true
  },

  "activity": {
    "current": null,

    "previous": {
      "type": "coding",
      "app": "Visual Studio Code",
      "restorable": true
    }
  },

  "events": {
    "open": [
      {
        "event_id": "EVT_4932",
        "type": "outing",
        "subtype": "date",
        "state": "arrived",
        "duration_minutes": 179,
        "importance": 0.72
      }
    ]
  }
}
```

---

# 103. Primeira versão realista

O sistema inteiro é grande.

A implementação deve crescer em fases.

## Fase 1

```text
webcam
person detection
owner detection
Windows idle
PRESENT / AWAY
snapshot
pause media
lock workstation
restore
```

---

# 104. Fase 2

Adicionar:

```text
phone presence
Wi-Fi zone
ROOM / DESK / AWAY
Bluetooth
Presence Fusion
```

---

# 105. Fase 3

Adicionar:

```text
HOUSE
arrival prediction
Wake-on-LAN
environment context
light automation
```

---

# 106. Fase 4

Adicionar:

```text
Open Events
Temporal Context
Event Importance
Follow-up Manager
```

---

# 107. Fase 5

Adicionar:

```text
expectativas temporais aprendidas
personal patterns
World Model
autonomy policies
decision traces
```

---

# 108. Fase 6

Adicionar:

```text
external presence node
PC sleep/wake
full environmental autonomy
additional physical sensors
```

---

# 109. Princípios essenciais

## 1. Sensores não decidem

Eles fornecem evidências.

## 2. Uma única fonte não deve dominar tudo

Combinar sinais sempre que possível.

## 3. Contexto atual ganha de regra rígida

Não usar automações burras baseadas somente em horário.

## 4. Snapshot não é ordem de restauração

O ambiente pode ter mudado.

## 5. Restaurar somente aquilo que a Laylay alterou

Evitar comportamento inesperado.

## 6. Silêncio é uma decisão válida

Nem tudo merece fala.

## 7. Eventos têm incerteza

Não usar durações rígidas.

## 8. Aprender o padrão pessoal é melhor que usar médias genéricas

## 9. Intenção não significa evento confirmado

O mundo físico pode confirmar.

## 10. Autonomia deve considerar impacto e reversibilidade

---

# 110. Resultado final desejado

A Laylay deixa de funcionar somente assim:

```text
Pedro:
"liga a luz"

Laylay:
liga a luz
```

E começa a funcionar assim:

```text
Pedro saiu às 15:30.

Antes de sair:
"vou para um encontro."

Laylay percebeu a saída.

Protegeu o computador.

Pausou apenas aquilo que precisava.

Manteve o evento em aberto.

Três horas depois:

o celular entrou na rede de casa.

depois entrou na rede do quarto.

Bluetooth apareceu.

o PC começou a se preparar.

a câmera reconheceu o usuário.

a presença mudou para DESK.

a Laylay percebeu:

18:30
ambiente escuro
luz desligada
usuário acabou de voltar

Ela liga a luz.

Restaura os serviços.

Não força imediatamente o trabalho anterior.

E lembra:

"ele tinha ido para um encontro."

Então pergunta:

"e aí, como foi?"
```

Sem macro fixa.

Sem timer burro.

Sem depender somente da webcam.

Sem precisar receber um comando para cada coisa.

---

# 111. Conceito final

A webcam é apenas:

> **os olhos.**

O celular é:

> **um beacon pessoal.**

O Wi-Fi ajuda a entender:

> **a zona.**

Bluetooth ajuda a entender:

> **a proximidade.**

Mouse e teclado mostram:

> **atividade real.**

O microfone fornece:

> **atividade ambiental.**

O relógio fornece:

> **tempo.**

A memória fornece:

> **passado.**

Os eventos fornecem:

> **continuidade.**

O World Model fornece:

> **interpretação do presente.**

E o sistema de autonomia decide:

> **agir, perguntar ou simplesmente ficar quieto.**

---

# 112. Frase que resume todo o sistema

> **A Laylay não deve apenas saber que algo aconteceu.  
> Ela deve perceber o que está acontecendo, lembrar o que aconteceu antes, entender quanto tempo passou e usar tudo isso para decidir o que faz sentido fazer agora.**

---

# 113. Mudança fundamental

Antes:

```text
COMANDO
   ↓
INTERPRETAÇÃO
   ↓
AÇÃO
```

Depois:

```text
MUNDO
   ↓
PERCEPÇÃO
   ↓
PRESENÇA
   ↓
MEMÓRIA
   ↓
TEMPO
   ↓
EVENTOS
   ↓
AMBIENTE
   ↓
ATIVIDADE
   ↓
WORLD MODEL
   ↓
AUTONOMIA
   ↓
┌──────────┬───────────┬──────────┐
↓          ↓           ↓
AÇÃO      FALA       SILÊNCIO
```

Esse é o ponto onde a Laylay começa a deixar de parecer apenas um assistente que recebe comandos e passa a parecer um sistema que **acompanha o ambiente e entende a continuidade do dia**.

---

# 114. Status do conceito

**Status:** conceito definido / ideia aprovada para evolução futura.

Componentes principais definidos:

```text
✓ webcam como sensor
✓ person detection
✓ reconhecimento de identidade
✓ processamento local
✓ histerese de presença
✓ Presence Manager
✓ snapshot de atividade
✓ restauração seletiva
✓ problema da suspensão identificado
✓ Presence Node futuro
✓ celular como sensor
✓ Wi-Fi como zona
✓ Bluetooth como proximidade
✓ Windows input como evidência
✓ microfone como atividade
✓ Presence Fusion Engine
✓ DESK / ROOM / HOUSE / AWAY
✓ Arrival Prediction
✓ Context Awareness
✓ eventos temporais
✓ intenções vs eventos confirmados
✓ Open Events
✓ expectativa temporal flexível
✓ aprendizado de padrões pessoais
✓ importância de eventos
✓ relevância de follow-up
✓ silêncio como decisão
✓ contexto ambiental
✓ autonomia de iluminação
✓ World Model
✓ níveis de autonomia
✓ integração com DEV Console
✓ arquitetura em fases
```

---

# 115. Nome conceitual do sistema

Nome maior sugerido:

```text
LAYLAY CONTEXT AWARENESS
```

Subsistemas:

```text
Presence Engine
Presence Fusion
Environment Context
Activity Context
Temporal Context
Event Understanding
World Model
Autonomy Engine
Restore Manager
```

O nome interno da arquitetura poderia ficar:

```text
Laylay Awareness System
```

ou simplesmente:

```text
Awareness
```

Estrutura:

```text
Laylay
│
├── Mind
├── Memory
├── Skills
├── DEV Console
│
└── Awareness
    ├── Perception
    ├── Presence
    ├── Environment
    ├── Temporal Context
    ├── Events
    ├── World Model
    └── Autonomy
```

Esse módulo representaria, essencialmente, a capacidade da Laylay de **ter consciência contextual do que está acontecendo ao redor dela**. 