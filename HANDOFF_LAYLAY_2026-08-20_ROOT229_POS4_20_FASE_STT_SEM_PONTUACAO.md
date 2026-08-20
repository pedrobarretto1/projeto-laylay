# HANDOFF LAYLAY — 2026-08-20 — ROOT 229 / PÓS 4.20 / FASE STT SEM PONTUAÇÃO

> **SNAPSHOT OPERACIONAL DOMINANTE PARA TROCA DE CHAT**
>
> Este arquivo deve ser lido **antes de continuar qualquer investigação**.
>
> Ele preserva integralmente o handoff anterior como apêndice histórico.
>
> Produção continua **INALTERADA** em:
>
> `3e3d9027c56b442770fd60bffe81a1c857197879` — `teste 4.9`
>
> Nenhum patch do turno 229 foi aplicado.
>
> **ATENÇÃO:** embora o candidato refinado 4.20 tenha saído `exit 2`,
> o patch literal foi novamente SUSPENSO antes de aplicação porque surgiu
> uma fronteira linguística nova e relevante:
>
> ```text
> fala humana / STT sem pontuação
> "fecha a microsoft store nao o opera"
> ```
>
> O próximo passo correto NÃO é patch.
>
> O próximo passo é um **RED/falsificação específica para negação sem pontuação/STT**.

---

# 0. ESTADO OFICIAL — UMA TELA

```text
C1-B2 ................................ CLOSED / PRESERVADO
C1-C ................................. CLOSED / PRESERVADO
C1-D Microsoft Store CLOSE ........... CLOSED / PRESERVADO
TURN 92-A ............................ CLOSED BEHAVIORALLY
TURN 92-C ............................ CLOSED BEHAVIORALLY
TURN 180 ............................. CLOSED BEHAVIORALLY

TURN 229 root original ............... CLOSED DIAGNOSTICAMENTE
FIRST RED original ................... resolver_revisao_intra_turno()
RED 4.18 ............................. EXIT 2 / AUTORITATIVO

4.19 candidato inicial ............... EXIT 2
4.19 literal ......................... REJEITADO NA 2ª REVISÃO

4.20 candidato refinado .............. EXIT 2
precedência .......................... SUSTENTADA
cancelamentos ........................ PRESERVADOS
reticências / "não," ................. PRESERVADAS
bare "não" em , / ; / mas ........... NÃO PROMOVIDO
IoT / criação / aspas / 230 .......... ISOLADOS

CANDIDATO 4.20 ....................... APROVADO CONCEITUALMENTE
PATCH LITERAL ........................ SUSPENSO

NOVA FRONTEIRA:
negação sem pontuação/STT ............ NÃO ESTUDADA
"fecha Store nao Opera" .............. SEM PROVA
"fecha Store nao feche Opera" ........ SEM PROVA

4.21 ................................ RESERVADO PARA FALSIFICAÇÃO STT
patch ................................ DEPOIS DISSO
chaos ................................ BLOQUEADO
```

---

# 1. REGRAS SOBERANAS ADICIONAIS DESTA FASE

Além de todas as regras históricas preservadas no apêndice:

53. **Pontuação é evidência, não autoridade.**  
    Vírgula, reticências e ponto-e-vírgula podem aumentar a confiança de uma leitura,
    mas uma proteção destrutiva não pode depender exclusivamente de pontuação correta.

54. **STT deve ser tratado como fonte de texto linguisticamente degradado.**  
    Voz pode remover vírgulas, reticências, acentos e capitalização sem alterar a intenção.

55. **Não generalizar uma correção escrita para fala transcrita sem prova.**  
    `fecha Store, não Opera` e `fecha Store nao Opera` podem atravessar caminhos
    arquiteturais diferentes.

56. **Se a primeira camada causal não dispara, o root pode migrar downstream.**  
    No caso sem pontuação, `_REVISAO` pode nem reconhecer a frase. Isso NÃO prova segurança;
    apenas significa que a investigação precisa seguir para modalidade/segmentação/roteador.

57. **Nunca ampliar regex para “pegar STT” sem primeiro observar o caminho real.**  
    Adicionar `\bnao\b` sem separador à revisão poderia fazer o módulo invadir nomes,
    citações, frases negativas e comandos legítimos.

58. **Negação destrutiva deve sobreviver à perda de pontuação.**  
    A semântica de `não feche Opera` não pode desaparecer porque o transcritor omitiu uma vírgula.

59. **Ambiguidade deve falhar para o lado seguro.**  
    Se a Laylay não consegue distinguir autocorreção de restrição sem pontuação,
    ela não deve transformar o conteúdo negativo em ação positiva.

60. **Não misturar root 229 escrito com root STT até a primeira fronteira ser provada.**  
    Eles podem compartilhar a mesma regra linguística, mas podem nascer em módulos diferentes.

---

# 2. RECAP — O INCIDENTE 229 ORIGINAL

Fala do chaos:

```text
fecha só a microsoft store, não o opera
```

Runtime:

```text
intent=CLOSE_APP
nome_app=opera
status=app_fechado
executou=True
confirmado=True
```

Ação física:

```text
alvo positivo ........ Microsoft Store
alvo proibido ........ Opera
alvo executado ....... Opera
```

Classificação:

```text
P1 / efeito físico no alvo negado
```

---

# 3. ROOT 229 ORIGINAL — FECHADO DIAGNOSTICAMENTE

Arquivo causal:

```text
mente_laylay/cognicao/revisao_turno.py
blob:
222d92624899ed55cc74628869b376075b7e6a1c
```

A regex `_REVISAO` exige um separador anterior:

```text
...
…
;
,
mas
```

e depois um marcador:

```text
não
esquece
quer dizer
na verdade
melhor
```

No 229 pontuado:

```text
"fecha só a microsoft store, não o opera"
                            ↑
                       ", não"
```

A revisão interpreta:

```text
proposta = "fecha só a microsoft store"
marker   = "não"
correcao = "o opera"
```

Depois:

```text
operacao_antiga = fechar
nova_op         = nenhuma
```

e o branch genérico de `substituicao_alvo` sintetiza:

```text
"fecha" + "o opera"
        ↓
"fecha o opera"
```

A polaridade negativa é destruída antes da autoridade.

---

# 4. RED 4.18 — PROVA SOBERANA DO ROOT ORIGINAL

Artefato:

```text
red_turno229_negacao_contrastiva_revisao_teste4_18.py
```

SHA-256:

```text
8cff55555806ead781738c56cff9ede6a76924daf9119ea880dba486e8e06494
```

Resultado:

```text
exit 2
```

Provas:

```text
correção legítima .............. PASS
cancelamento legítimo ......... PASS

229 exato:
"não o Opera"
→ "fecha o Opera" .............. RED

sem "só":
"fecha Store, não Opera"
→ "fecha o Opera" .............. RED

negação explícita original:
"fecha Store, não feche Opera"
→ modalidade original .......... recusa / autoriza=False

mesma frase após revisão:
→ "feche o Opera"
→ modalidade revisada .......... comando / autoriza=True
```

Conclusão:

> a autoridade sabe respeitar a proibição quando recebe a fala original;
> a revisão destrói a polaridade antes dela.

---

# 5. 4.19 — PRIMEIRO CANDIDATO

Conceito:

> bare `não` em fronteira fraca não recebe promoção de revisão.

Resultado:

```text
exit 2
```

Sustentou:

```text
229 ................................ NÃO PROMOVIDO
Store positivo ..................... PRESERVADO
negação explícita .................. FAIL-CLOSED
correções com reticências .......... PRESERVADAS
"não," ............................. PRESERVADO
cancelamentos principais ........... PRESERVADOS
IoT ................................ PRESERVADO
criação ............................ PRESERVADA
230 ................................ ISOLADO
```

Mas a segunda revisão encontrou lacunas:

```text
"fecha Store, não"
→ cancelamento vazio histórico

"fecha Store mas não, Opera"
→ pausa depois do "não" pode indicar autocorreção
```

Logo:

```text
conceito 4.19 ............ sustentado
literal 4.19 ............. NÃO APROVADO
```

---

# 6. 4.20 — CANDIDATO REFINADO

Artefato:

```text
falsificacao_turno229_precedencia_nao_refinado_teste4_20.py
```

Resultado real:

```text
exit 2
```

O baseline continuou RED:

```text
229 baseline
→ "fecha o opera"
```

Portanto o teste não passou por mudança acidental do baseline.

---

# 7. 4.20 — MATRIZ RESTRITIVA

Todas ficaram sem revisão:

```text
fecha só Store, não Opera
fecha Store, não Opera
fecha Store, não feche Opera
fecha Store; não Opera
fecha Store; não feche Opera
fecha Store mas não Opera
fecha Store mas não feche Opera
abre Opera e Store mas não fecha nenhum dos dois
```

Contrato:

```text
detectada=False
resolvida=False
cancelada=False
texto_operacional_efetivo=""
```

---

# 8. 4.20 — 229 APÓS NÃO-PROMOÇÃO

Modalidade recebeu a fala original:

```text
fecha só a microsoft store, não o opera
```

Resultado:

```text
modalidade_geral='misto'
autoriza=True
texto_operacional='fecha só a microsoft store'
```

Isto prova apenas:

```text
Store permanece positivo
Opera não vira alvo positivo
```

Não prova um parser negativo completo.

---

# 9. 4.20 — CANCELAMENTO VAZIO PRESERVADO

Casos:

```text
fecha Store, não
fecha Store; não
fecha Store mas não
```

Todos:

```text
detectada=True
resolvida=True
cancelada=True
tipo=cancelamento
texto_operacional_efetivo=""
```

Esta lacuna era o motivo principal para não aplicar literalmente o 4.19.

---

# 10. 4.20 — PRECEDÊNCIA DE `"NÃO,"`

Casos:

```text
fecha Store, não, Opera
fecha Store; não, Opera
fecha Store mas não, Opera
fecha Store mas não, melhor Opera
```

Todos continuam:

```text
→ fecha Opera
```

Conclusão:

```text
"mas não Opera" ........ restrição
"mas não, Opera" ....... autocorreção

"; não Opera" .......... restrição
"; não, Opera" ......... autocorreção
```

A pausa depois do marcador vence o separador anterior.

---

# 11. 4.20 — RETICÊNCIAS

Preservadas:

```text
fecha Store... não Opera
→ fecha Opera

fecha Store... não, Opera
→ fecha Opera

Abre Wikipédia... não, melhor Prime Video
→ Abre Prime Video
```

Contrato atual:

```text
reticências = moldura forte de revisão
```

---

# 12. 4.20 — CANCELAMENTOS SEMÂNTICOS

Preservados:

```text
Pesquisa Python... pera, não pesquisa nada.
→ cancelamento

Apaga segredo.txt... não apaga.
→ cancelamento
```

---

# 13. 4.20 — IoT FORTE × FRACO

Forte:

```text
Liga a lâmpada... não, deixa desligada.
→ desliga lâmpada
```

Fracos:

```text
Liga a lâmpada, não deixa desligada.
Liga a lâmpada; não deixa desligada.
Liga a lâmpada mas não deixa desligada.
```

Todos:

```text
sem revisão
```

---

# 14. 4.20 — CRIAÇÃO FORTE × FRACA

Forte:

```text
Cria erro.txt... não, chama correcao.txt.
→ Cria correcao.txt
```

Fracos:

```text
Cria erro.txt, não chama correcao.txt.
Cria erro.txt; não chama correcao.txt.
Cria erro.txt mas não chama correcao.txt.
```

Todos:

```text
sem revisão
```

---

# 15. 4.20 — MARCADORES NÃO-"NÃO"

Preservados no baseline:

```text
quer dizer
na verdade
esquece
```

Exemplos:

```text
Fecha Calculadora... quer dizer, maximiza ela.
→ maximiza Calculadora

Abre Opera... na verdade abre Discord.
→ abre Discord

Pausa música... esquece, continua tocando.
→ continua música
```

Patch 229 deve permanecer exclusivo ao papel do marker `"não"`.

---

# 16. 4.20 — ASPAS

Não invadidas:

```text
Pesquisa por "não apaga".
Cria um arquivo chamado não.txt.
Abre o arquivo chamado "não feche o opera".
```

Baseline e candidato:

```text
detectada=False
```

Não confundir com o turno 251, que é outro root de metalinguagem.

---

# 17. 4.20 — TURN 230 ISOLADO

```text
fecha só o opera, deixa a microsoft store quieta
```

Baseline:

```text
detectada=False
```

Candidato:

```text
detectada=False
```

Portanto:

```text
230 continua root separado
```

---

# 18. SEGUNDA REVISÃO PÓS-4.20

O conceito refinado foi considerado sólido para os casos pontuados.

Precedência conceitual:

```text
marker != "não"
    → baseline

marker == "não"
    ↓
correção vazia
    → cancelamento

same-op + vazio/nada/mais nada
    → cancelamento

reticências
    → revisão

"não, ..."
    → revisão

senão:
vírgula / ; / mas + bare "não"
    → não promover revisão
```

Neste ponto o patch literal parecia próximo.

---

# 19. NOVA DESCOBERTA — PORTUGUÊS SEM PONTUAÇÃO / STT

Antes de gerar o patch, surgiu a pergunta:

> E quem escreve ou fala sem vírgula?

Exemplos:

```text
fecha a microsoft store nao o opera
fecha a microsoft store não o opera
fecha só a microsoft store nao o opera
fecha a microsoft store nao feche o opera
abre o opera e a microsoft store nao fecha nenhum
liga a lampada nao deixa desligada
cria erro.txt nao chama correcao.txt
```

Isto é especialmente relevante para STT.

Whisper/transcritores podem devolver:

```text
sem vírgula
sem reticências
sem acento
sem capitalização
```

A segurança destrutiva não pode depender de o transcritor reconstruir pontuação perfeita.

---

# 20. POR QUE O ROOT ORIGINAL PODE NÃO DISPARAR SEM PONTUAÇÃO

A regex `_REVISAO` atual exige:

```text
...
…
;
,
mas
```

antes do marcador.

Logo:

```text
fecha Store, não Opera
           ↑
_REVISAO encontra
```

mas:

```text
fecha Store nao Opera
            ↑
sem separador aceito
```

pode resultar em:

```text
resolver_revisao_intra_turno()
→ detectada=False
```

Isto NÃO significa que a frase está segura.

Só significa:

```text
root 229 original talvez não participe
        ↓
fala inteira segue downstream
        ↓
modalidade / segmentação / roteador / detector
precisam ser estudados
```

---

# 21. HIPÓTESE ATUAL PARA SEM PONTUAÇÃO — NÃO PROVADA

Estrutura linguística:

```text
[operação positiva] [alvo A] [não] [alvo B]
```

Exemplo:

```text
fecha Store nao Opera
```

Semântica humana provável:

```text
Store = alvo positivo
Opera = exclusão
```

Forma mais explícita:

```text
fecha Store nao feche Opera
```

Semântica:

```text
fecha Store
+
não feche Opera
```

Mas NÃO assumir que o código atual lê assim.

---

# 22. REGRA DE SEGURANÇA DESEJADA — AINDA CONCEITUAL

Pontuação deve ser apenas sinal.

O contrato desejado tende a:

```text
NÃO
 │
 ├─ há sinal forte de autocorreção?
 │      "... não..."
 │      "não, ..."
 │      "quer dizer"
 │      "na verdade"
 │      "melhor"
 │
 │      → autocorreção
 │
 └─ não há sinal forte
        e o "não" introduz:
        - alvo
        - verbo
        - nenhum / nenhum dos dois
        - estado negativo
        - exclusão

        → restrição / não promover como ação positiva
```

Mas isto ainda NÃO é patch.

---

# 23. PERIGO DE AMPLIAR `_REVISAO` AGORA

Uma correção ingênua seria permitir:

```regex
\bnao\b
```

sem separador.

NÃO FAZER.

Isso poderia invadir:

```text
nomes
conteúdo citado
arquivos
pesquisas
frases negativas
negações dentro de parâmetros
fala casual
metalinguagem
```

Exemplos:

```text
Pesquisa por nao apaga
Cria arquivo nao.txt
Abre arquivo chamado nao feche o opera
```

A investigação deve observar primeiro o caminho real.

---

# 24. 4.21 — NOVO OBJETIVO OFICIAL

**4.21 NÃO É MAIS PATCH.**

4.21 deve ser:

```text
FALSIFICAÇÃO / DIAGNÓSTICO
NEGAÇÃO SEM PONTUAÇÃO + STT
```

Objetivos:

1. provar se `_REVISAO` realmente não detecta as formas sem pontuação;
2. executar a modalidade real sobre essas falas;
3. observar `texto_operacional`;
4. chamar o detector/roteador determinístico seguro, sem executor físico;
5. descobrir se Opera vira candidato;
6. localizar a primeira fronteira real;
7. separar:
   - caso sem pontuação;
   - caso sem acento;
   - caso com `mas`;
   - negação explícita;
8. manter produção intacta.

---

# 25. MATRIZ OBRIGATÓRIA PARA 4.21

## A — restrição sem pontuação

```text
fecha a microsoft store nao o opera
fecha a microsoft store não o opera
fecha só a microsoft store nao o opera
fecha a microsoft store nao feche o opera
fecha só a microsoft store nao feche o opera
```

## B — plural / nenhum

```text
abre o opera e a microsoft store nao fecha nenhum
abre o opera e a microsoft store nao fecha nenhum dos dois
```

## C — `mas` sem vírgula

```text
fecha a microsoft store mas nao o opera
fecha a microsoft store mas nao feche o opera
```

Este grupo já possui separador textual `mas` e pode continuar entrando na revisão.

## D — IoT sem pontuação

```text
liga a lampada nao deixa desligada
liga a lâmpada não deixa desligada
```

## E — criação sem pontuação

```text
cria um arquivo chamado erro.txt nao chama correcao.txt
```

## F — autocorreção degradada / ambígua

```text
fecha a microsoft store nao opera
```

Sem pausa explícita, não assumir automaticamente que significa correção.

A política segura deve evitar:

```text
"não Opera"
→ "fecha Opera"
```

## G — controles positivos

```text
fecha a microsoft store
fecha o opera
nao feche o opera
não feche o opera
```

## H — conteúdo literal

```text
pesquisa por nao apaga
cria arquivo nao.txt
```

---

# 26. PERGUNTAS QUE O 4.21 PRECISA RESPONDER

```text
Q1. revisão detecta sem pontuação?
Q2. modalidade autoriza?
Q3. modalidade preserva qual trecho operacional?
Q4. detector CLOSE_APP escolhe Store ou Opera?
Q5. negação explícita sem pontuação fail-close?
Q6. "nao" sem acento muda o caminho?
Q7. "mas nao" continua dentro do root 229?
Q8. IoT/criação abrem roots semelhantes?
Q9. o patch 229 precisa conhecer STT?
Q10. ou existe um segundo root downstream?
```

Só depois destas respostas decidir se:

```text
A) ampliar patch 229
B) criar guard compartilhado de polaridade
C) corrigir modalidade
D) corrigir detector
E) manter roots separados
```

---

# 27. ESTADO DO PATCH 4.21

Anteriormente:

```text
4.21 = patch literal mínimo
```

AGORA:

```text
4.21 = FALSIFICAÇÃO STT / SEM PONTUAÇÃO
```

O patch deve ser renumerado para depois da investigação, provavelmente:

```text
4.22 ou posterior
```

Não fixar número definitivo até ver o resultado do 4.21.

---

# 28. ESTADO FORMAL PARA O PRÓXIMO CHAT

```text
ROOT 229 pontuado .................... CLOSED DIAGNOSTICAMENTE
4.18 ................................ EXIT 2
4.19 ................................ EXIT 2
4.20 ................................ EXIT 2

candidato pontuado ................... SUSTENTADO
patch pontuado ....................... NÃO APLICADO

nova questão:
sem pontuação/STT .................... OPEN
primeira fronteira ................... DESCONHECIDA
root compartilhado? .................. DESCONHECIDO

produção ............................. INALTERADA
HEAD ................................. 3e3d9027...
chaos ................................ BLOQUEADO
```

---

# 29. O QUE O PRÓXIMO CHAT NÃO DEVE FAZER

```text
NÃO aplicar patch 4.20 direto
NÃO ampliar _REVISAO com \bnao\b no chute
NÃO assumir que sem pontuação cai no mesmo root
NÃO mexer no executor
NÃO mexer na Store
NÃO reabrir 92
NÃO reabrir 180
NÃO misturar 230
NÃO misturar 251
NÃO rodar chaos ainda
```

---

# 30. PRÓXIMA AÇÃO EXATA

Começar por:

```text
falsificacao_turno229_negacao_sem_pontuacao_stt_teste4_21.py
```

Sem patch.

O harness deve:

```text
HEAD lock
blobs lock
baseline 4.18/4.20 preservados
revisao real
modalidade real
roteador/detector seguro
zero executor físico
zero LLM
zero rede
Git antes/depois
```

Semântica sugerida:

```text
exit 2 = nova fronteira sem pontuação provada e isolada
exit 1 = inconclusivo / harness ou hipótese parcial
exit 0 = caminho sem pontuação já seguro na matriz
```

---

# 31. RESUMO ULTRACURTO PARA RETOMADA

```text
229 pontuado:
", não Opera"
→ revisão transforma em "fecha Opera"
→ ROOT CLOSED DIAGNOSTICAMENTE

4.18 RED = exit 2
4.19 candidato = exit 2
4.20 refinamento = exit 2

MAS:
usuário percebeu caso sem pontuação/STT

"fecha Store nao Opera"

_REVISAO pode nem disparar
→ não sabemos o que downstream faz

ENTÃO:
PATCH SUSPENSO

PRÓXIMO:
4.21 diagnóstico/falsificação sem pontuação/STT
```

---

# 32. APÊNDICE — HANDOFF PÓS-4.20 PRESERVADO INTEGRALMENTE

> O conteúdo abaixo é o snapshot anterior completo.
> Onde ele diz que o próximo passo seria o patch literal, isso representa
> corretamente o estado ANTES da descoberta sobre STT sem pontuação.

# HANDOFF LAYLAY — 2026-08-20 — ROOT 229 / PÓS 4.20 / CANDIDATO REFINADO APROVADO CONCEITUALMENTE

> **SNAPSHOT OPERACIONAL DOMINANTE**
>
> Este arquivo preserva integralmente o handoff anterior como apêndice.
> O estado desta seção é o mais novo.
>
> Produção continua **INALTERADA** em:
>
> `3e3d9027c56b442770fd60bffe81a1c857197879` — `teste 4.9`
>
> Nenhum patch do turno 229 foi aplicado.
>
> O candidato refinado sobreviveu ao 4.20, mas ainda não existe patch de produção aplicado.

---

# 0. ESTADO OFICIAL ATUAL

```text
C1-B2 ................................ CLOSED / PRESERVADO
C1-C ................................. CLOSED / PRESERVADO
C1-D Microsoft Store CLOSE ........... CLOSED / PRESERVADO
TURN 92-A ............................ CLOSED BEHAVIORALLY
TURN 92-C ............................ CLOSED BEHAVIORALLY
TURN 180 ............................. CLOSED BEHAVIORALLY

TURN 229 root causal ................. CLOSED DIAGNOSTICAMENTE
FIRST RED ............................ resolver_revisao_intra_turno()
RED 4.18 ............................. EXIT 2 / AUTORITATIVO

4.19 candidato inicial ............... EXIT 2 / SUSTENTADO
4.19 literal patch ................... NÃO APROVADO
motivo ............................... segunda revisão achou lacunas de precedência

4.20 candidato refinado .............. EXIT 2 / SUSTENTADO
cancelamento vazio ................... PRESERVADO
cancelamento semântico ............... PRESERVADO
reticências .......................... PRESERVADAS
"não," ............................... PRESERVADO
bare "não" em , / ; / mas ........... NÃO PROMOVIDO
IoT forte/fraco ...................... ISOLADO
criação forte/fraco .................. ISOLADO
aspas ................................ PRESERVADAS
turno 230 ............................ ISOLADO
Git/blobs ............................ PRESERVADOS

CANDIDATO REFINADO ................... APROVADO CONCEITUALMENTE
PATCH LITERAL ........................ AINDA NÃO GERADO
PATCH APLICADO ....................... NÃO
CHAOS ................................ BLOQUEADO
```

---

# 1. RESULTADO AUTORITATIVO DO 4.20

Artefato:

```text
falsificacao_turno229_precedencia_nao_refinado_teste4_20.py
```

Resultado:

```text
exit 2
```

HEAD:

```text
3e3d9027c56b442770fd60bffe81a1c857197879
```

Blobs causais:

```text
revisao_turno.py ..................... PASS
modalidade_turno.py .................. PASS
porteiro_acoes.py .................... PASS
test_revisao_intra_turno_v1.py ...... PASS
```

Produção:

```text
INALTERADA
```

---

# 2. BASELINE 229 CONTINUA RED

Baseline histórico confirmado:

```text
"fecha só a microsoft store, não o opera"
        ↓
resolver_revisao_intra_turno()
        ↓
detectada=True
resolvida=True
cancelada=False
tipo=substituicao_alvo
texto_operacional_efetivo="fecha o opera"
```

Logo, a falsificação não passou porque o baseline mudou.

---

# 3. MATRIZ RESTRITIVA — RESULTADO

Todas ficaram em **sem revisão**:

```text
fecha só Store, não Opera
fecha Store, não Opera
fecha Store, não feche Opera
fecha Store; não Opera
fecha Store; não feche Opera
fecha Store mas não Opera
fecha Store mas não feche Opera
abre Opera e Store mas não fecha nenhum dos dois
```

Contrato obtido:

```text
detectada=False
resolvida=False
cancelada=False
texto_operacional_efetivo=""
```

Interpretação:

> bare `não` ligado ao conteúdo negativo em fronteira fraca não recebe promoção
> de revisão.

---

# 4. 229 APÓS NÃO-PROMOÇÃO

Quando a revisão deixa a fala original seguir:

```text
fecha só a microsoft store, não o opera
```

a modalidade real produz:

```text
modalidade_geral='misto'
autoriza_execucao=True
texto_operacional='fecha só a microsoft store'
```

Portanto:

```text
Store continua no polo operacional positivo
Opera não vira alvo operacional positivo
```

Isto elimina a cadeia causal específica do 229:

```text
"não Opera" -> "fecha Opera"
```

Sem afirmar que a modalidade já possui um contrato negativo completo.

---

# 5. NEGAÇÃO EXPLÍCITA CONTINUA FAIL-CLOSED

Frase:

```text
fecha a microsoft store, não feche o opera
```

Depois da não-promoção:

```text
modalidade='recusa'
modalidade_geral='recusa'
autoriza_execucao=False
```

Isto reforça a prova do 4.18:

> quando a revisão não destrói a polaridade, a autoridade sabe bloquear a
> proibição explícita.

---

# 6. LACUNA DO 4.19 QUE O 4.20 FECHOU — CANCELAMENTO VAZIO

Contrato histórico real:

```text
fecha a microsoft store, não
fecha a microsoft store; não
fecha a microsoft store mas não
```

Todos continuam:

```text
detectada=True
resolvida=True
cancelada=True
tipo=cancelamento
texto_operacional_efetivo=""
```

Logo, o patch não pode aplicar a regra de não-promoção cedo demais.

Precedência obrigatória:

```text
marker="não" + correção vazia
        ↓
CANCELAMENTO
        ↓
não cai no bloqueio de bare "não"
```

---

# 7. PRECEDÊNCIA DE `"NÃO,"` — FECHADA

Frases:

```text
fecha Store, não, Opera
fecha Store; não, Opera
fecha Store mas não, Opera
fecha Store mas não, melhor Opera
```

Todas continuam autocorreções legítimas:

```text
→ fecha Opera
```

Conclusão:

> a pausa **depois do `não`** tem precedência sobre o separador anterior.

Portanto:

```text
"mas não Opera" ........ restrição
"mas não, Opera" ....... autocorreção

"; não Opera" .......... restrição
"; não, Opera" ......... autocorreção
```

---

# 8. RETICÊNCIAS — SINAL FORTE PRESERVADO

Continuam válidas:

```text
fecha Store... não Opera
→ fecha Opera

fecha Store... não, Opera
→ fecha Opera

Abre Wikipédia... não, melhor Prime Video
→ Abre Prime Video
```

Conclusão:

```text
... + não
```

continua moldura forte de revisão no contrato atual.

---

# 9. CANCELAMENTOS SEMÂNTICOS — PRESERVADOS

```text
Pesquisa Python... pera, não pesquisa nada.
→ cancelamento

Apaga segredo.txt... não apaga.
→ cancelamento
```

O candidato refinado não bloqueia estes casos antes que o branch semântico existente
possa avaliá-los.

---

# 10. IoT — FORTE × FRACO

## Forte corretivo

```text
Liga a lâmpada... não, deixa desligada.
→ desliga lâmpada
```

Preservado.

## Fraco restritivo

```text
Liga a lâmpada, não deixa desligada.
Liga a lâmpada; não deixa desligada.
Liga a lâmpada mas não deixa desligada.
```

Todos ficam:

```text
sem revisão
```

Isto é crucial porque o branch IoT ocorre antes do branch genérico de nova operação
na implementação atual.

---

# 11. CRIAÇÃO — FORTE × FRACO

## Forte corretivo

```text
Cria erro.txt... não, chama correcao.txt.
→ Cria correcao.txt
```

Preservado.

## Fraco negativo

```text
Cria erro.txt, não chama correcao.txt.
Cria erro.txt; não chama correcao.txt.
Cria erro.txt mas não chama correcao.txt.
```

Todos ficam:

```text
sem revisão
```

Assim, o patch não pode depender apenas de `_nome_parametro()` ou de presença de um
novo nome.

---

# 12. MARCADORES NÃO-"NÃO" — INALTERADOS

Preservados exatamente no baseline:

```text
quer dizer
na verdade
esquece
```

Exemplos:

```text
Fecha a Calculadora... quer dizer, maximiza ela.
→ maximiza Calculadora

Abre o Opera... na verdade abre o Discord.
→ abre Discord

Pausa a música... esquece, continua tocando.
→ continua a música
```

O patch 229 deve ser **exclusivo para marker == "nao"**.

---

# 13. ASPAS — ISOLAMENTO

Continuam fora da revisão:

```text
Pesquisa por "não apaga".
Cria um arquivo chamado não.txt.
Abre o arquivo chamado "não feche o opera".
```

Baseline e candidato iguais:

```text
detectada=False
```

Não misturar este root com o turno 251 de metalinguagem.

---

# 14. TURN 230 — ISOLAMENTO CONFIRMADO

```text
fecha só o opera, deixa a microsoft store quieta
```

Baseline:

```text
detectada=False
```

Candidato:

```text
detectada=False
```

Logo:

```text
230 NÃO pertence automaticamente ao root 229
```

---

# 15. SEGUNDA REVISÃO PÓS-4.20 — APROVAÇÃO CONCEITUAL

Depois do `exit 2`, o código real de `resolver_revisao_intra_turno()` foi revisto
novamente.

A ordem atual relevante é:

```text
1. localizar marker/separador
2. extrair proposta/correção
3. cancelamento vazio
4. tratar "melhor"
5. branch IoT
6. detectar nova operação
7. cancelamento same-op + nada
8. substituição de ação/comando
9. nome de criação
10. substituição genérica de alvo
```

Risco central:

> colocar o guard depois do branch IoT deixa `"Liga X, não deixa desligada"` escapar;
> colocar o guard antes do cancelamento same-op quebra
> `"Pesquisa Python... pera, não pesquisa nada"`.

Portanto o patch literal precisa classificar **a força do `não` antes dos branches
destrutivos**, mas preservar os contratos de cancelamento.

---

# 16. DESENHO LITERAL RECOMENDADO — AINDA NÃO APLICADO

O patch mínimo deve usar dados já disponíveis no mesmo match:

```text
achado.group("sep")
bruto[achado.end():]
correcao
operacao_antiga
```

Fluxo conceitual recomendado:

```text
marker != "não"
    → baseline intacto

marker == "não"
    ↓
correção vazia?
    → deixar baseline cancelar

same-op + vazio/nada/mais nada?
    → deixar baseline cancelar

sep == "..." ou "…"?
    → deixar baseline corrigir

cauda crua começa com ","?
    → "não, ..."
    → deixar baseline corrigir

senão:
sep é vírgula / ; / mas?
    → retornar BASE SEM REVISÃO

senão:
    → baseline
```

## Observação de implementação importante

Para saber se há `não, ...`, o patch precisa olhar a **cauda crua**:

```python
cauda_crua = bruto[achado.end():]
```

Não pode depender apenas de `correcao`, porque `_limpar_inicio_correcao()` já remove
a vírgula inicial.

## Observação sobre cancelamento same-op

A implementação precisa reconhecer o cancelamento same-op antes do bloqueio de
fronteira fraca.

Isso pode ser feito calculando uma `nova_op` preliminar apenas para decidir a
precedência, sem alterar o contrato downstream.

---

# 17. O QUE AINDA NÃO ESTÁ AUTORIZADO

```text
não editar produção diretamente
não aplicar patch ainda
não rodar chaos
não mexer em modalidade_turno
não resolver 230 junto
não resolver 251 junto
```

Próximo passo:

```text
desenhar patch literal mínimo 4.21
        ↓
revisão integral do diff
        ↓
falsificações estáticas/sintéticas
        ↓
git apply --check
        ↓
somente depois aplicar
```

---

# 18. ESTADO FORMAL

```text
ROOT 229 ........................ CLOSED DIAGNOSTICAMENTE
RED 4.18 ....................... EXIT 2 AUTORITATIVO

4.19 ........................... EXIT 2
conceito 4.19 .................. SUSTENTADO
literal 4.19 ................... REJEITADO NA SEGUNDA REVISÃO

4.20 ........................... EXIT 2
conceito refinado .............. SUSTENTADO
precedência .................... PROVADA
cancelamento vazio ............. PROVADO
cancelamento semântico ......... PROVADO
IoT ............................ ISOLADO
criação ........................ ISOLADA
aspas .......................... ISOLADAS
230 ............................ ISOLADO
Git/blobs ...................... PRESERVADOS

CANDIDATO REFINADO ............. APROVADO CONCEITUALMENTE
PATCH LITERAL .................. PRÓXIMO PASSO
PRODUÇÃO ....................... INALTERADA
BEHAVIOR 229 ................... OPEN
CHAOS .......................... BLOQUEADO
```

---

# 19. APÊNDICE — HANDOFF PRÉ-4.19 PRESERVADO INTEGRALMENTE

> O conteúdo abaixo permanece histórico e válido para reconstrução da investigação.
> Onde ele diz `4.19 PREPARADA`, isso descreve corretamente o estado anterior à execução.

# HANDOFF LAYLAY — 2026-08-20 — ROOT 229 / NEGAÇÃO CONTRASTIVA — PÓS RED 4.18 / PRÉ 4.19

> **SNAPSHOT OPERACIONAL DOMINANTE**
>
> Este arquivo preserva integralmente o handoff pós-chaos `TESTE4_9_POS_CHAOS_92_180_CLOSED`
> como apêndice histórico. As seções deste topo são o estado mais novo da investigação.
>
> Produção continua **INALTERADA** desde o commit:
>
> `3e3d9027c56b442770fd60bffe81a1c857197879` — `teste 4.9`
>
> Nenhum patch do turno 229 foi aplicado.
>
> O chaos continua bloqueado até falsificação, segunda revisão, patch focado,
> regressões e nova prova runtime.

---

# 0. ESTADO OFICIAL AGORA

```text
C1-B2 ................................ CLOSED / PRESERVADO
C1-C ................................. CLOSED / PRESERVADO
C1-D Microsoft Store CLOSE ........... CLOSED / PRESERVADO
TURN 92-A ............................ CLOSED BEHAVIORALLY
TURN 92-C ............................ CLOSED BEHAVIORALLY
TURN 180 ............................. CLOSED BEHAVIORALLY
TURN 189 ............................. NÃO REPRODUZIDO / PASS

TURN 229 root causal ................. CLOSED DIAGNOSTICAMENTE
TURN 229 first RED ................... resolver_revisao_intra_turno()
TURN 229 classe ...................... polaridade / negação contrastiva
TURN 229 efeito ...................... alvo proibido vira alvo positivo
TURN 229 RED 4.18 .................... EXIT 2 / AUTORITATIVO
TURN 229 comportamento ............... OPEN / NÃO CORRIGIDO

gap secundário modalidade ............ PROVADO / DOWNSTREAM
TURN 230 ............................. ROOT SEPARADO POR ENQUANTO
TURN 251 aspas/metalinguagem ......... ROOT SEPARADO P1

candidato linguístico 4.19 ........... PREPARADO / NÃO EXECUTADO
patch produção ....................... NÃO EXISTE
chaos ................................ BLOQUEADO
```

---

# 1. TURNO 229 — INCIDENTE SOBERANO

Fala:

```text
fecha só a microsoft store, não o opera
```

Runtime do chaos `teste 4.9`:

```text
intent=CLOSE_APP
nome_app=opera
status=app_fechado
executou=True
confirmado=True
```

A Laylay fechou fisicamente o aplicativo que estava explicitamente no polo negativo
da frase.

Este incidente é P1 porque:

```text
alvo positivo ........ Microsoft Store
alvo proibido ........ Opera
alvo executado ....... Opera
efeito físico ........ confirmado
```

---

# 2. ROOT CAUSAL 229 — FECHADO DIAGNOSTICAMENTE

Arquivo:

```text
mente_laylay/cognicao/revisao_turno.py
blob 222d92624899ed55cc74628869b376075b7e6a1c
```

A regex `_REVISAO` aceita, entre outros:

```text
separadores:
...
…
;
,
mas

marcadores:
não
esquece
quer dizer
na verdade
melhor
```

No 229:

```text
entrada:
fecha só a microsoft store, não o opera
```

A revisão lê:

```text
proposta_anterior = "fecha só a microsoft store"
marker            = "não"
correcao          = "o opera"
operacao_antiga   = fechar
nova_op           = nenhuma
```

Depois o branch genérico de `substituicao_alvo` aceita `marker == "nao"` e sintetiza:

```text
verbo antigo + correção
        ↓
"fecha" + "o opera"
        ↓
"fecha o opera"
```

A polaridade negativa deixa de existir **antes** da modalidade e da autoridade.

Cadeia:

```text
USUÁRIO
"fecha só Store, não Opera"
        ↓
resolver_revisao_intra_turno()
        ↓
interpreta "não Opera" como:
"não, quis dizer Opera"
        ↓
texto_operacional_efetivo
"fecha o Opera"
        ↓
modalidade
comando / autoriza=True
        ↓
roteadores
CLOSE_APP opera
        ↓
executor
fecha Opera
```

## Formulação oficial da causa

> `resolver_revisao_intra_turno()` não distingue o **"não" discursivo de autocorreção**
> do **"não" sintático/restritivo**. Em contraste do tipo `ação A, não B`, a camada
> reaproveita o verbo da proposta anterior e promove o conteúdo proibido B a novo
> alvo positivo antes da autoridade.

---

# 3. O QUE FOI FALSIFICADO COMO ROOT

```text
executor_janelas .................... NÃO É ROOT
CLOSE_APP ........................... NÃO É ROOT
Microsoft Store identity ............ NÃO É ROOT
Opera identity ...................... NÃO É ROOT
referência contextual ............... NÃO É ROOT
splitter de cadeia .................. NÃO É ROOT
LLM ................................. NÃO PARTICIPA DA FIRST FRONTIER

modalidade pós-revisão .............. DOWNSTREAM
roteador determinístico ............. DOWNSTREAM
```

O executor recebeu `nome_app=opera` já legitimado e executou corretamente aquilo que
a camada cognitiva errada havia produzido.

O splitter não explica a troca Store → Opera.

Se o detector de fechamento recebesse a frase original intacta, não existe evidência
de que ele naturalmente transformaria o alvo positivo Store em Opera. A troca surge
antes, no texto sintetizado pela revisão.

---

# 4. RED 4.18 — PROVA AUTORITATIVA

Artefato:

```text
red_turno229_negacao_contrastiva_revisao_teste4_18.py
SHA-256:
8cff55555806ead781738c56cff9ede6a76924daf9119ea880dba486e8e06494
```

HEAD travado:

```text
3e3d9027c56b442770fd60bffe81a1c857197879
```

Blobs travados:

```text
revisao_turno.py
222d92624899ed55cc74628869b376075b7e6a1c

modalidade_turno.py
80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241

orquestrador_turno_runtime.py
9ea071daf1dbdc40e9677f5d65515e0ee4ec4c99

porteiro_acoes.py
19b5eaa9ddafd483eab92d46e92cca30813adbb6

coordenador_intencao.py
de8a893cd60ab44ad9bc3437d01db15ba54fb367

tests/test_revisao_intra_turno_v1.py
a5b64017c62a7cb90a20824ddeca0bcaa79bce04
```

Resultado do usuário:

```text
exit 2
```

## 4.1 Controles históricos

```text
"Abre Wikipédia... não, melhor Prime Video."
→ substituicao_alvo
→ "Abre Prime Video"
→ PASS

"Pesquisa Python... pera, não pesquisa nada."
→ cancelamento
→ texto efetivo vazio
→ PASS
```

Logo, o RED não é “qualquer uso do não quebra revisão”.

## 4.2 Turno 229 exato

```text
"fecha só a microsoft store, não o opera"
→ detectada=True
→ resolvida=True
→ cancelada=False
→ tipo=substituicao_alvo
→ efetivo="fecha o opera"

RED ESPERADO
```

## 4.3 Falsificação do `"só"`

```text
"fecha a microsoft store, não o opera"
→ efetivo="fecha o opera"

RED ESPERADO
```

Portanto `"só"` não é a causa.

## 4.4 Prova forte de polaridade

Frase:

```text
fecha a microsoft store, não feche o opera
```

### Direto para modalidade

```text
modalidade=recusa
modalidade_geral=recusa
autoriza_execucao=False

GREEN SEGURANÇA
```

### Passando primeiro pela revisão

```text
tipo=substituicao_comando
efetivo="feche o opera"

RED
```

### Modalidade recebe a versão falsificada

```text
"feche o opera"
→ modalidade=comando
→ autoriza_execucao=True

RED
```

Esta é a prova mais forte do root:

> A camada de autoridade sabe respeitar a proibição original, mas a revisão
> remove a polaridade antes que a autoridade possa vê-la.

## 4.5 Wiring real

4.18 também provou:

```text
orquestrador chama resolver_revisao_intra_turno .... PASS
orquestrador constrói texto_cognitivo .............. PASS
coordenador reconhece revisão resolvida ............ PASS
coordenador consome texto_operacional_efetivo ...... PASS
Git/worktree ........................................ PRESERVADO
```

Estado:

```text
FIRST RED ........................ resolver_revisao_intra_turno()
ROOT 229 ......................... CLOSED DIAGNOSTICAMENTE
PATCH ............................ NÃO APLICADO
```

---

# 5. GAP SECUNDÁRIO — MODALIDADE

Quando a fala 229 original é entregue diretamente à modalidade, sem revisão:

```text
fecha só a microsoft store, não o opera
```

o resultado observado no 4.18 foi:

```text
modalidade='comando'
modalidade_geral='misto'
autoriza_execucao=True
texto_operacional='fecha só a microsoft store'
```

Isto é um **gap downstream**, mas não a first frontier.

Importante:

```text
modalidade preserva Store como trecho operacional
não transforma Opera em alvo positivo
```

Portanto ela não explica o efeito físico errado do chaos.

Para o root 229, impedir a promoção errada na revisão já devolve a fala ao estado
seguro conhecido:

```text
ação positiva reconhecida ........ Store
Opera ............................ não promovido a comando
```

A evolução futura pode representar restrições negativas explicitamente no contrato do
turno, mas isto não precisa ser misturado ao patch causal mínimo do root 229.

---

# 6. ESTUDO DA DISTINÇÃO LINGUÍSTICA — RESULTADO

A pergunta de engenharia depois do 4.18 passou a ser:

> Qual é a menor regra que separa `não` corretivo de `não` restritivo sem quebrar
> os contratos legítimos da revisão intra-turno?

## 6.1 Candidatos simplistas REJEITADOS

### A. Remover `"não"` da regex de revisão

REJEITADO.

Quebraria:

```text
"Abre Wikipédia... não, melhor Prime Video."
"Liga a lâmpada... não, deixa desligada."
"Cria ... erro.txt... não, chama correcao.txt."
"Apaga segredo.txt... não apaga."
```

### B. Corrigir apenas quando houver `"só"`

REJEITADO.

4.18 D provou:

```text
"fecha Store, não Opera"
```

falha igual.

### C. Só permitir correção se a cauda tiver verbo explícito

REJEITADO.

Correções legítimas de alvo são elípticas:

```text
"Abre Wikipédia... não, melhor Prime Video."
"fecha Store... não, Opera"
```

Além disso:

```text
"fecha Store, não feche Opera"
```

tem verbo explícito e é justamente uma restrição que não pode virar comando positivo.

### D. Todo `", não"` é restrição

REJEITADO.

Existe contrato histórico:

```text
"Pesquisa Python... pera, não pesquisa nada."
```

O match efetivo ocorre por vírgula antes de `"não"` e precisa continuar cancelando a
operação.

Também uma fala natural:

```text
"fecha Store, não, Opera"
```

pode ser uma autocorreção legítima devido à pausa depois do `"não"`.

### E. Toda reticência é suficiente sozinha para decidir qualquer semântica

NÃO USAR COMO REGRA ÚNICA.

Reticências são um sinal forte de interrupção/reparo, mas o contrato final ainda deve
preservar cancelamentos e marcadores explícitos.

---

# 7. DISTINÇÃO CANDIDATA MAIS FORTE

A análise convergiu para separar dois papéis do token `"não"`.

## 7.1 `"não"` discursivo / corretivo

Sinais fortes:

```text
interrupção:
"... não ..."

pausa do próprio marcador:
"não, ..."

marcadores semânticos de reparo:
"quer dizer"
"na verdade"
"melhor"

cancelamento reconhecível:
mesma operação + vazio/nada/mais nada
```

Exemplos que devem continuar válidos:

```text
"Abre Wikipédia... não, melhor Prime Video."
→ Abre Prime Video

"Liga a lâmpada... não, deixa desligada."
→ desliga lâmpada

"Cria erro.txt... não, chama correcao.txt."
→ criação com novo nome

"fecha Store... não, Opera"
→ fecha Opera

"fecha Store... não Opera"
→ fecha Opera
  (reticência fornece moldura forte de autocorreção)

"fecha Store, não, Opera"
→ fecha Opera
  (vírgula depois de "não" funciona como pausa corretiva)

"fecha Store, não, feche Opera"
→ feche Opera

"Pesquisa Python... pera, não pesquisa nada."
→ cancelamento

"Apaga segredo.txt... não apaga."
→ cancelamento
```

## 7.2 `"não"` sintático / restritivo

Sinais:

```text
"não" ligado diretamente ao alvo:
", não o Opera"

"não" ligado diretamente ao verbo negativo:
", não feche o Opera"

contraste:
"mas não ..."

fronteira fraca:
"; não ..."
```

Exemplos que NÃO devem virar revisão positiva:

```text
"fecha só Store, não Opera"
"fecha Store, não Opera"
"fecha Store, não feche Opera"
"fecha Store; não Opera"
"fecha Store mas não feche Opera"
"abre A e B mas não fecha nenhum"
```

## 7.3 Regra candidata

> **Bare `não` em fronteira fraca não recebe promoção de revisão.**
>
> Em vez de sintetizar um novo comando, a revisão devolve **sem revisão** e deixa
> a fala original seguir para modalidade/autoridade.
>
> Autocorreções com moldura forte e cancelamentos reconhecidos continuam no
> mecanismo de revisão.

Isto é propositalmente uma regra de **não-promoção**, não um novo parser universal de
negação.

---

# 8. POR QUE "NÃO-PROMOVER" É MAIS SEGURO QUE "REINTERPRETAR"

O patch causal não precisa decidir toda a semântica de:

```text
fecha Store, não Opera
```

Ele só precisa impedir esta camada de fazer o que não tem autoridade para fazer:

```text
NÃO PODE:
"não Opera"
    ↓
"fecha Opera"
```

Se a revisão disser:

```text
não é uma revisão segura
→ preserve a fala original
```

então as camadas já existentes podem decidir:

```text
229 elíptico:
modalidade mantém "fecha Store"

negação explícita:
modalidade fail-close

outros casos:
seguem pelo contrato normal
```

Vantagem:

```text
mudança causal mínima
sem novo executor
sem novo resolvedor de app
sem nova autoridade
sem parser destrutivo paralelo
```

---

# 9. FALSIFICAÇÃO 4.19 — PREPARADA, AINDA NÃO EXECUTADA

Artefato:

```text
falsificacao_turno229_distincao_nao_corretivo_restritivo_teste4_19.py
```

SHA-256 final após segunda revisão do harness:

```text
f01db3d874047aa4def2e7ec3296ed763253bf2ac055a980fa6ecd675f69e1f4
```

A segunda revisão encontrou e corrigiu apenas uma deficiência do harness:

```text
antes:
comparava git status antes/depois

depois:
compara git status + blobs causais antes/depois
```

O candidato linguístico não mudou.

## 9.1 O que 4.19 exige do baseline

```text
229 baseline
→ ainda precisa produzir "fecha o opera"

senão:
exit 0
→ baseline mudou
→ não interpretar candidato
```

## 9.2 Matriz restritiva

O candidato deve produzir **sem revisão** para:

```text
fecha só Store, não Opera
fecha Store, não Opera
fecha Store, não feche Opera
fecha Store; não Opera
fecha Store mas não feche Opera
abre Opera e Store mas não fecha nenhum dos dois
```

## 9.3 229 depois da não-promoção

A modalidade real precisa receber a fala original e continuar com:

```text
autoriza_execucao=True
texto_operacional contendo Microsoft Store
texto_operacional NÃO contendo Opera como alvo separado
```

Isto não é “fix completo de negação”; é prova de que o root Store→Opera desaparece.

## 9.4 Negação explícita

```text
fecha Store, não feche Opera
```

depois da não-promoção deve permanecer:

```text
autoriza_execucao=False
```

## 9.5 Matriz corretiva preservada

4.19 exige:

```text
Abre Wikipédia... não, melhor Prime Video. .... GREEN
Liga lâmpada... não, deixa desligada. .......... GREEN
Cria erro.txt... não, chama correcao.txt. ...... GREEN
fecha Store... não, Opera ....................... GREEN
fecha Store... não Opera ........................ GREEN
fecha Store, não, Opera ......................... GREEN
fecha Store, não, feche Opera ................... GREEN
```

## 9.6 Cancelamentos preservados

```text
Pesquisa Python... pera, não pesquisa nada. ..... GREEN
Apaga segredo.txt... não apaga. ................. GREEN
```

## 9.7 Marcadores fortes

```text
quer dizer ....................................... GREEN
na verdade ....................................... GREEN
```

## 9.8 Isolamento do 230

```text
fecha só o opera, deixa a microsoft store quieta
```

deve continuar:

```text
detectada=False
mesmo resultado baseline/candidato
```

Logo, 4.19 não pode “resolver” o 230 por acidente.

## 9.9 Semântica

```text
exit 2 = candidato sustentado
exit 1 = candidato falsificado/inconclusivo
exit 0 = baseline histórico deixou de reproduzir
```

Mesmo com exit 2:

```text
NÃO aplicar patch ainda
→ segunda revisão do resultado/candidato
→ só depois desenhar patch literal
```

---

# 10. CANDIDATO DE PATCH — AINDA NÃO AUTORIZADO

Não existe patch de produção neste snapshot.

Se 4.19 sustentar o conceito, a segunda revisão deverá decidir a colocação literal
mais estreita dentro de `resolver_revisao_intra_turno()`.

A localização conceitual é:

```text
depois de identificar:
- marker
- separator
- correction
- operação antiga

mas antes de:
- substituicao_comando genérica
- substituicao_alvo genérica
```

O patch literal deverá evitar duplicar parser e preservar primeiro:

```text
cancelamento vazio por "não"
cancelamento same-op + nada
estado final IoT
reticência corretiva
"não, ..."
marcadores fortes
```

Não aplicar uma regex externa no executor ou no roteador.

---

# 11. RISCOS LATERAIS A MANTER NA SEGUNDA REVISÃO

## R1 — fala corretiva sem pontuação perfeita

STT pode produzir:

```text
fecha Store não Opera
```

Sem separador, `_REVISAO` atual pode nem detectar.

Não ampliar o patch 229 para resolver STT sem RED específico.

## R2 — semicolon ambíguo

```text
fecha Store; não Opera
```

Candidato fail-safe trata como restrição.

Se houver contrato histórico contrário, precisa aparecer em falsificação antes do patch.

## R3 — `mas não`

Sempre tratar como contraste no candidato atual.

Não permitir que cancelamento/target-substitution transforme o lado negativo em alvo
positivo.

## R4 — cancelamento por `"nada"`

Preservar explicitamente:

```text
não pesquisa nada
não apaga
```

O caso `Pesquisa Python... pera, não pesquisa nada.` é particularmente importante
porque o match de `"não"` pode ser precedido por vírgula, apesar de a fala ter
reticências antes de `"pera"`.

## R5 — 230

```text
fecha só o opera, deixa a microsoft store quieta
```

não usa marker `"não"` e não pertence automaticamente ao root 229.

## R6 — 251 / aspas

```text
aspas: "fecha a microsoft store"
```

é P1 de metalinguagem/autoridade, não corrigido pelo candidato 229.

## R7 — gap da modalidade

O patch 229 não deve criar uma nova autoridade negativa completa.

Se após o root patch surgirem ações erradas mesmo com a fala original preservada,
abrir investigação própria da modalidade.

---

# 12. PRÓXIMA SEQUÊNCIA SOBERANA

```text
4.18 RED histórico ........................ EXIT 2 / FROZEN
        ↓
estudo linguístico profundo ............... FEITO
        ↓
candidato de não-promoção ................. DEFINIDO
        ↓
4.19 falsificação ......................... PREPARADA
        ↓
USUÁRIO EXECUTA 4.19
        ↓
se exit 2:
    segunda revisão integral do resultado
        ↓
    desenhar patch literal mínimo
        ↓
    git apply --check
        ↓
    aplicar somente após revisão
        ↓
    pós-patch focado
        ↓
    regressão histórica revisao_turno
        ↓
    regressão autoridade/modalidade
        ↓
    chaos soberano
```

Se 4.19 der exit 1:

```text
NÃO adaptar teste para caber no candidato
→ primeira falsificação que falhou manda
→ reabrir desenho do candidato
```

---

# 13. AVISO PARA A PRÓXIMA CONVERSA

Não voltar a hipóteses já falsificadas:

```text
"é o executor" .................... NÃO
"é a Store" ....................... NÃO
"é o só" .......................... NÃO
"é só bloquear qualquer não" ...... NÃO
"é só exigir verbo na correção" ... NÃO
"é só corrigir modalidade" ........ NÃO
```

Começar daqui:

```text
ROOT 229:
revisão intra-turno promove não restritivo a autocorreção

RED 4.18:
exit 2 autoritativo

CANDIDATO:
não-promover bare "não" em fronteira fraca;
preservar reticência / "não," / cancelamentos / marcadores fortes

4.19:
PRONTO / NÃO EXECUTADO
```

---

# 14. APÊNDICE — HANDOFF PÓS-CHAOS 4.9 (PRESERVADO INTEGRALMENTE)

> O conteúdo abaixo é o snapshot dominante anterior.
> Seus estados sobre 92, 180 e C1-D continuam válidos.
> A investigação 229 acima apenas avança o P1 seguinte.

# HANDOFF LAYLAY — 2026-08-20 — TESTE 4.9 / PÓS-CHAOS / 92 + 180 CLOSED

> **Este é o snapshot operacional dominante.**
>
> Ele substitui o estado operacional do handoff de 19/08, mas **não apaga nem reescreve a história anterior**.
> O handoff 4.0 original foi preservado integralmente no apêndice histórico ao final deste arquivo.
>
> Projeto: `pedrobarretto1/projeto-laylay`
>
> Commit do novo chaos: `3e3d9027c56b442770fd60bffe81a1c857197879`
>
> Mensagem: `teste 4.9`
>
> Parent: `95be16751d678180a8ede2a22ea04b1aef6cbf8d`
>
> Resultado soberano:
> `resultados_testes/roteiro_teste_laylay_caos-20260819-233751-109946`

---

# 0. LEIA PRIMEIRO — ESTADO OFICIAL ATUAL

```text
C1-B2 bare maximiza ........................ CLOSED / PRESERVADO
C1-C esquerda .............................. CLOSED / PRESERVADO

C1-D CLOSE Microsoft Store ................. CLOSED
C1-D turno 159 runtime real ................ GREEN FÍSICO
C1-D turno 179 repetição ................... GREEN FÍSICO

TURN 92-A domínio/carrier arquivo .......... CLOSED BEHAVIORALLY
TURN 92-C falso app_fechado ................ CLOSED BEHAVIORALLY
TURN 92 ação física solicitada ............. SAFE FAIL
                                             nenhuma janela correspondente existia
                                             NÃO chamar isso de physical GREEN

TURN 180 autoridade herdada em reparação ... CLOSED BEHAVIORALLY
TURN 180 chaos real ........................ GREEN / ZERO COMANDOS

TURN 189 anomalia anterior ................. NÃO REPRODUZIDA / PASS

gate regressivo 4.17 V2 .................... 55/55 GREEN
chaos final ................................ 267/267 respostas
semanticamente avaliados ................... 51
pass ....................................... 30
fail ....................................... 19
alerts ..................................... 2
taxa semântica ............................. 58.82%

PRÓXIMA RAIZ P1 ............................ turnos 228–230
P1 adicional ............................... turno 251 / comando entre aspas
P2 ......................................... MAXIMIZE Microsoft Store
```

## Regra de continuidade

**Não reabrir 92, 180 ou C1-D por causa das raízes novas abaixo sem prova causal nova.**

Os próximos bugs são laterais e devem nascer como investigações próprias.

---

# 1. REGRAS SOBERANAS DE INVESTIGAÇÃO — CONSOLIDADO ATÉ TESTE 4.9

As regras 1–39 do handoff anterior continuam obrigatórias e aparecem no apêndice histórico.

Acrescentam-se:

40. **Safe failure pode fechar uma raiz antiga sem provar sucesso físico da ação pedida.**  
    Se o bug original era escolher domínio/alvo errado ou declarar falso sucesso, e o runtime novo chega ao carrier correto, usa o executor seguro e falha honestamente porque o efeito físico não estava disponível, a raiz original pode estar CLOSED mesmo com `executou=False`.

41. **Falha física esperada ≠ regressão cognitiva.**  
    Exemplo soberano: turno 92 agora resolve arquivo corretamente e tenta fechar a janela do documento. Se nenhuma janela existe, `falha_execucao` é comportamento seguro, não retorno do bug `"janela"`.

42. **Regressivo antigo pode ficar incompleto depois de uma correção correta.**  
    Quando produção passa a publicar metadado canônico novo, atualizar teste somente com delta auditado exato. Nunca remover assert para fazê-lo passar.

43. **Reparação operacional é exceção estreita à autoridade normal.**  
    Algumas correções legítimas podem executar mesmo com `autoriza_execucao=False`, mas apenas quando a própria fala atual carrega evidência operacional corrigida.

44. **Intent anterior nunca recria autoridade por si só.**  
    Reconhecer alvo na fala atual + lembrar `CLOSE_APP` anterior não autoriza repetir `CLOSE_APP`.

45. **Pergunta vence operação herdada.**  
    Para intents sensíveis, `modalidade_atual == "pergunta"` bloqueia despacho de reparação mesmo se o detector enxergar operação corrigida.

46. **Negação e contraste são parte da autoridade destrutiva, não decoração textual.**  
    `"fecha A, não B"` precisa fixar alvo positivo e alvo explicitamente proibido antes do dispatch.

47. **Alvo negativo nunca pode vencer alvo positivo.**  
    `"fecha só a microsoft store, não o opera"` fechar Opera é falha P1, ainda que o executor físico tenha funcionado perfeitamente.

48. **Aspas/metalinguagem devem sobreviver até o gate de autoridade.**  
    `"aspas: \"fecha a microsoft store\""` é citação, não autorização para `CLOSE_APP`.

49. **Evaluator GREEN ou `não_avaliado` não absolve runtime inseguro.**  
    O terminal do chaos pode revelar ação errada séria fora da matriz semântica.

50. **Resultado do executor não valida parsing.**  
    `status=app_fechado, confirmado=True` pode ser gravíssimo se o app fechado era justamente o alvo negado.

51. **Separar identidade por operação.**  
    O fechamento da Store está CLOSED; falhas de `MAXIMIZE_WINDOW` com `ms-windows-store:` são outra raiz e não reabrem `CLOSE_APP`.

52. **O conjunto de falhas do chaos é sinal, não mapa completo de risco.**  
    Comparar a lista de failures ajuda regressão, mas sempre revisar corredores de negação, metalinguagem e ações destrutivas no terminal.

---

# 2. LINHA DO TEMPO — TURNOS 92 E 180

## 2.1 Turno 92 — bug original

Baseline:

```text
"Fecha ele."
→ referência de arquivo existia
→ resolvedor geral produzia carrier seguro CLOSE_APP/referencia_arquivo
→ filtro domínio×intent rejeitava o próprio carrier
→ LLM inventava fecha/janela
→ executor tentava "janela"
→ ausência posterior podia gerar falso app_fechado
```

Duas raízes independentes:

```text
92-A = compatibilidade de domínio rejeita carrier seguro de arquivo
92-C = executor confundia "está ausente" com "eu fechei"
```

### Patch 92-A

Carrier pode atravessar somente quando:

```text
rota == GERAL
dominio_restrito == arquivo
intent == CLOSE_APP
referencia_arquivo is True
nome_app não vazio
janela_titulo não vazio
```

Não existe exceção global para `CLOSE_APP`.

### Patch 92-C

```python
fechou = bool(fechar_programa(...))
ok = bool(
    fechou
    and callable(esperar_programa)
    and esperar_programa(nome)
)
```

Portanto:

```text
closer=False + alvo ausente depois ≠ sucesso
exception + alvo ausente depois ≠ sucesso
closer=True + pós-condição=True = sucesso
closer=True + pós-condição=False = falha
```

## 2.2 Provas focadas do 92

```text
4.4 RED ................................ exit 2
4.6 falsificação ....................... exit 2
4.8 escopo por rota .................... exit 2
4.10 V2 pós-patch real ................. exit 0
4.17 V2 regressão final ................ 55/55 GREEN
```

## 2.3 Turno 92 no chaos final

Runtime real:

```text
> Fecha ele.

intent=CLOSE_APP
alvo=C:\Users\pbarr\Downloads\troca ideia.txt
params.nome_app=C:\Users\pbarr\Downloads\troca ideia.txt
params.janela_titulo=C:\Users\pbarr\Downloads\troca ideia.txt
params.referencia_arquivo=True

executor:
Nenhuma janela de arquivo encontrada para fechar

status=falha_execucao
executou=False
confirmado=False
```

### O que isto prova

```text
não virou "janela" genérica .................... PASS
referente continua arquivo ..................... PASS
carrier seguro chegou à produção ............... PASS
referencia_arquivo=True ........................ PASS
executor de arquivo foi usado .................. PASS
processo genérico não foi morto ................ PASS
falso app_fechado foi eliminado ................ PASS
falha foi reportada como falha ................ PASS
```

### O que isto NÃO prova

```text
janela do arquivo fechada fisicamente .......... NÃO
```

Não havia uma janela correspondente para fechar.

### Estado oficial do 92

```text
ROOT 92-A ........................ CLOSED BEHAVIORALLY
ROOT 92-C ........................ CLOSED BEHAVIORALLY
efeito físico solicitado ......... SAFE FAIL
```

A presença de `falha_execucao` no turno 92 **não reabre as raízes originais**.

---

# 3. TURN 180 — AUTORIDADE HERDADA EM REPARAÇÃO

## 3.1 Baseline perigoso

Sequência:

```text
179:
"Fecha ela."
→ CLOSE_APP microsoft store
→ app_fechado

180:
"Eu estava falando da microsoft store ou da conta?"
```

Antes:

```text
detector reconhecia microsoft store
→ herdava CLOSE_APP do turno anterior
→ reparação pre-IA despachava CLOSE_APP
→ pergunta ganhava efeito destrutivo por contexto
```

Root:

> **reparação operacional materializava intent anterior sensível mesmo sem autoridade operacional atual.**

## 3.2 Primeiro patch e regressão lateral

Guard 4.9 inicial:

```python
if not bool(decisao_turno.get("autoriza_execucao")):
    return False, ""
```

Turno 180 focado ficou seguro, mas o guard era amplo demais.

O regressivo tracked provou contrato legítimo:

```text
MUSIC_SEARCH corrigida
modalidade=correcao
autoriza_execucao=False
→ deve continuar executando a correção contextualizada
```

Resultado 4.12:

```text
regressão lateral REAL ........... PROVADA
culpa ............................ guard universal do 180
```

## 3.3 Refinamento final 4.15

Contrato final:

```python
if (
    not autoriza_execucao
    and intent_reparada in intents_sensiveis
    and (
        modalidade_atual == "pergunta"
        or not operacao_corrigida
    )
):
    return False, ""
```

Intents sensíveis atuais:

```text
APP_OPEN
OPEN_URL
MAXIMIZE_WINDOW
CLOSE_APP
CLOSE_TAB
```

Interpretação:

```text
pergunta + CLOSE_APP herdado ............. BLOQUEIA
muda alvo sem operação atual ............. BLOQUEIA
MAXIMIZE explícito na correção ........... PRESERVA
MUSIC_SEARCH corrigido ................... PRESERVA
SEARCH corrigido ......................... PRESERVA
FILE_SEARCH corrigido .................... PRESERVA
MEDIA_CONTROL corrigido .................. PRESERVA
VOLUME explícito ......................... early-return determinístico preservado
CLOSE_APP com autoridade=True ............ PRESERVA
```

## 3.4 Provas do 180

```text
4.5 RED .................................. exit 2
4.7 V2 falsificação ...................... exit 2
4.12 regressão lateral ................... exit 1 / RED real
4.13 intent-only ......................... exit 2, mas rejeitado na 2ª revisão
4.14 V2 operação atual ................... exit 2
4.15 patch de produção ................... aplicado
4.16 pós-patch real ...................... exit 0
4.17 V2 regressão final .................. 55/55 GREEN
```

## 3.5 Turno 180 no chaos final

```text
> Eu estava falando da microsoft store ou da conta?

[IA] Gerando resposta...
[PLANO] resposta_planejada | comandos=[]
[PLANO] executado | comandos=[]

Laylay:
Você estava falando da Microsoft Store — o app que fechou sem reclamar.
O que quer saber sobre ele?
```

Não houve:

```text
ROTEADOR REPARAÇÃO operacional
CLOSE_APP
dispatch
ação física
```

### Estado oficial

```text
ROOT 180 ............................ CLOSED BEHAVIORALLY
runtime real ....................... GREEN
autoridade atual=False ............. PRESERVADA
intent anterior destrutivo ......... NÃO RECRIADO
zero comandos ...................... PROVADO
```

---

# 4. C1-D / MICROSOFT STORE — FECHAMENTO CONTINUA CLOSED

Não confundir com MAXIMIZE.

## Turno 159

```text
> fecha ela

intent=CLOSE_APP
nome_app=microsoft store
referencia_contextual=True
status=app_fechado
executou=True
confirmado=True
```

## Turno 179

```text
> Fecha ela.

intent=CLOSE_APP
nome_app=microsoft store
referencia_contextual=True
status=app_fechado
executou=True
confirmado=True
```

### Estado

```text
C1-D target-only 157 ..................... PRESERVADO
C1-D direção 158 ......................... PRESERVADO
C1-D CLOSE 159 ........................... GREEN FÍSICO
C1-D repetição 179 ....................... GREEN FÍSICO
C1-D ..................................... CLOSED
```

**Falhas de `MAXIMIZE_WINDOW microsoft store` não reabrem C1-D CLOSE.**

---

# 5. GATE REGRESSIVO FINAL 4.17 V2

Artefato:

```text
regressao_final_pre_caos_teste4_17_v2.py
SHA-256:
3990a10732bda201a99822a67452c23f010d916e1cc85c66aa3167e33c78fc32
```

Allowlist fixa, sem discovery fuzzy.

Resultado:

```text
55 collected
55 passed
0 failed
```

Cobertura:

```text
C1-B2 / cadeia navegador ................. GREEN
C1-C / autoridade + aba anterior ......... GREEN
C1-D Store canary ........................ GREEN
92-A contexto arquivo .................... GREEN
92-C causalidade ......................... GREEN
janelas / arquivo tipado ................. GREEN
autoridade / decisão ..................... GREEN
180 / reparação .......................... GREEN
regressão 4.12 ........................... GREEN
Git/worktree ............................. PRESERVADO
```

## Ajuste auditado no regressivo do 92-A

O 4.17 V1 encontrou expectativa tracked incompleta.

Produção real agora devolve também:

```python
"_dominio_contextual": "arquivo"
```

O teste foi atualizado com **exatamente uma linha**.

Blob final:

```text
tests/test_continuidade_geral.py
c4f019ec6e6fab967748a2462d380533b6aaea88
```

`git diff --check` limpo.

Não houve enfraquecimento do teste; ele passou a exigir mais proveniência.

---

# 6. CHAOS FINAL — TESTE 4.9

Commit:

```text
3e3d9027c56b442770fd60bffe81a1c857197879
mensagem: teste 4.9
```

Diretório:

```text
resultados_testes/roteiro_teste_laylay_caos-20260819-233751-109946
```

## 6.1 Placar

```text
Transporte .......................... 267/267

Semanticamente avaliados ........... 51
Pass ............................... 30
Fail ............................... 19
Alerts ............................. 2
Não avaliados ...................... 216
Taxa semântica ..................... 58.82%

p50 ................................ 2.634 s
p95 ................................ 23.037 s
max ................................ 44.158 s
mean ............................... 4.793 s

confirmado=None .................... 15
```

Domínios:

```text
apps ............................... 5 pass / 0 fail
agenda ............................. 2 pass / 0 fail
browser ............................ 8 pass / 0 fail
security ........................... 9 pass / 0 fail
files .............................. 3 pass / 3 fail
music .............................. 0 pass / 3 fail / 2 alerts
conversation ....................... 0 pass / 13 fail
```

## 6.2 Failure set

Novo:

```text
22,44,68,69,70,78,79,85,89,91,
113,116,123,126,133,171,174,227,257
```

Baseline 4.0:

```text
22,44,68,69,70,78,79,85,89,91,92,
113,116,123,126,133,171,174,227,257
```

Diferença:

```text
92 saiu da lista de falhas semânticas
nenhum novo failure semântico apareceu
```

Além disso, a anomalia posterior do turno 189 também não reapareceu.

## 6.3 Comparação com chaos anterior pós-Store

Anterior em `95be...`:

```text
52 avaliados
28 pass
21 fail
3 alerts
53.85%
16 confirmado=None
```

Agora:

```text
51 avaliados
30 pass
19 fail
2 alerts
58.82%
15 confirmado=None
```

Delta observado:

```text
pass ............................... +2
fail ............................... -2
alerts ............................. -1
taxa semântica ..................... +4.97 p.p.
confirmado=None .................... -1
```

Cuidado: o número avaliado mudou 52→51. Não atribuir toda melhora aos patches 92/180.

---

# 7. TURN 189 — ANOMALIA ANTERIOR NÃO REPRODUZIDA

Runtime:

```text
> Me lembra de beber água amanhã às 10 e 41.

status=lembrete_ja_agendado
executou=False
confirmado=True
```

Resposta:

```text
O lembrete de beber agua já estava agendado; mantive uma só cópia.
```

Relatório: PASS.

Estado:

```text
anomalia 189 anterior .............. NÃO REPRODUZIDA
duplicate guard .................... FUNCIONOU NESTE CHAOS
```

Não atribuir automaticamente ao patch 92/180.

---

# 8. NOVAS RAÍZES — NÃO MISTURAR COM 92/180

## P1 — TURNOS 228–230: NEGAÇÃO / CONTRASTE / ALVO DESTRUTIVO

### 228

Usuário:

```text
abre o opera e a microsoft store
mas não fecha nenhum dos dois
e não mexe no navegador além disso
```

Runtime indevido:

```text
intent=CLOSE_APP
nome_app="nenhum dos dois e nao mexe no navegador alem disso"
status=falha_execucao
```

Problema:

```text
negação virou comando destrutivo
conteúdo negativo virou alvo
```

### 229 — MAIS GRAVE

Usuário:

```text
fecha só a microsoft store, não o opera
```

Runtime:

```text
intent=CLOSE_APP
nome_app=opera
status=app_fechado
executou=True
confirmado=True
```

A Laylay fechou exatamente o app que o usuário explicitamente proibiu fechar.

Classificação:

```text
P1
autoridade/negação/contraste/alvo
efeito físico REAL no alvo proibido
```

Este deve ser o **próximo root prioritário**.

### 230

Usuário:

```text
fecha só o opera, deixa a microsoft store quieta
```

Primeiro:

```text
CLOSE_APP
nome_app="so o opera"
status=falha_execucao
```

Depois, lateralmente:

```text
APP_OPEN microsoft store
modo=focus
status=ja_aberto_focado
```

Problemas:

```text
"so o" contaminou nome do app
"deixa X quieta" virou ação contextual em X
```

## Hipótese de família — NÃO PATCHADA

Provavelmente há interação entre:

```text
segmentação de cadeia
negação
contraste
extração de alvo
comando explícito
resolver contextual
```

Não aplicar regex pontual antes de RED isolado.

---

# 9. P1 — TURNO 251: ASPAS / METALINGUAGEM EXECUTA COMANDO

Usuário:

```text
aspas: "fecha a microsoft store"
```

Runtime:

```text
CLOSE_APP microsoft store
status=app_fechado
executou=True
confirmado=True
```

Isto é um bug sério de autoridade/metalinguagem.

A frase descreve/cita um comando; não deveria autorizar o efeito.

Relaciona-se conceitualmente a autoridade atual, mas é **root novo**.

Próxima investigação pode decidir se 228–230 e 251 compartilham a primeira fronteira ou apenas princípios.

---

# 10. P2 — MICROSOFT STORE MAXIMIZE

Turnos como 96/112/143 ainda mostram:

```text
MAXIMIZE_WINDOW microsoft store
mapped=ms-windows-store:

nenhum PID encontrado para 'ms-windows-store:'
nenhuma janela encontrada...
status=maximizacao_nao_confirmada
executou=False
confirmado=False
```

Isto é outra manifestação de identidade por operação:

```text
open locator != maximize/window matcher
```

Não reabrir o fechamento da Store.

Estado:

```text
CLOSE_APP Store ..................... CLOSED
MAXIMIZE Store ...................... OPEN / P2
```

---

# 11. OUTRAS DÍVIDAS OBSERVADAS NO CHAOS

## P2 — resultado operacional não lembrado — turno 188

Após `CLOSE_TAB wikipedia` confirmado:

```text
status=aba_fechada
executou=True
confirmado=True
```

Pergunta:

```text
O que você fechou?
```

Resposta errada:

```text
Nada, só estou aqui. Não fechei nada.
```

Root provável: memória/relato de resultado operacional, não execução.

## P2 — contexto contaminado — turno 137

Conversa sobre estado da lâmpada responde sobre Prime Video.

Manter separada.

## P2 — consulta de par — turno 231

```text
qual dos dois ainda está aberto?
```

vira:

```text
LIST_WINDOWS
alvo="qual dos dois ainda"
```

Parser de referência plural/par comparativa.

## P2 — memória de gostos — turno 209

```text
O que você lembra sobre meus gostos?
```

vira `PEOPLE_QUERY` com alvo `"Meus Gostos"`.

Domínio de memória/pessoas roubando pergunta de preferências.

## Autoridade ambígua a estudar

Também observar:

```text
"abre a microsoft store?"
"abre a microsoft store ou não?"
```

No chaos atual ambas podem chegar a `APP_OPEN`.

Não classificar automaticamente como bug sem definir contrato linguístico para pergunta imperativa/interrogativa.

---

# 12. ARTEFATOS E HASHES DESTA INVESTIGAÇÃO

```text
red_turno92_contexto_arquivo_falso_close_teste4_4.py
adeb0850c6889756f3ce9ce1b3eca988cdf356dd29d5296c2da41265dc454f66

red_turno180_autoridade_reparacao_teste4_5.py
c3e583c52a0ceb7c7e343986a0eb69bf5ec52d6b355beaec7bde52ba2be4a509

falsificacao_turno92_candidatos_teste4_6.py
1cdc97ae666f01f593f7c7d2d23c200cab8cb84564ba37780bde200668c5d92a

falsificacao_turno180_autoridade_reparacao_teste4_7_v2.py
6ce2460973b209d549a02a71bc0f84b5781b22c7c4cc2ec18546311bec7c98f9

falsificacao_turno92_escopo_rota_teste4_8.py
cf319bc218b8a970817070e1aff57cae15fdaff0562fbfe2b5fbfe7bc7dc85c0

patch_minimo_turnos92_180_teste4_9.patch
06b4c02d757330094fd2e69c0cb22d22696a098bb1ee437ad3aeae4a02ab1928

pos_patch_turnos92_180_teste4_10_v2.py
477ee0bc339b04a5dbc1506c61d0e0c08627db632515573bdc7d2610f61b4ce3

regressao_lateral_patch180_teste4_12.py
48ab95d58ea47d119b0644e892bfd9995888ed9e5f4c9c2654200a523e1b77bb

falsificacao_turno180_guard_refinado_intent_teste4_13.py
e6f7b7c9a3d55cb5f6ea283558e20a2203261e190f5232b46b72f361c9c607c1

falsificacao_turno180_guard_operacao_atual_teste4_14_v2.py
a41c819150128e628eaf32676b3b28f3e1f28e082fb1c89e65ca9c3c94a4444f

patch_refinamento_turno180_operacao_atual_teste4_15.patch
d8fa3c1d4592bc68fa55623a1f374068dbe819522d795fe028bae82b6293fe69

pos_patch_turno180_regressao_teste4_16.py
decf52beb49aafe76c99d313b74e5a5e5111ce376476a54149e18e9efbc55e4e

regressao_final_pre_caos_teste4_17_v2.py
3990a10732bda201a99822a67452c23f010d916e1cc85c66aa3167e33c78fc32
```

Históricos inconclusivos preservados:

```text
4.7 V1 ............ invalid control "fecha ele" intraturn
4.10 V1 ........... auditor Git global incorreto
4.11 V1 ........... discovery/exclusion architecture incorreta
4.14 V1 ........... controle VOLUME inválido
4.17 V1 ........... expectativa tracked sem _dominio_contextual
```

Nunca reclassificá-los retroativamente como provas que não foram.

---

# 13. BLOBS CAUSAIS DO PATCH ANTES DO COMMIT FINAL

No worktree real provado antes do commit `3e3d902...`:

```text
mente_laylay/autonomia/executor_janelas.py
72526e6...

mente_laylay/memoria_mental/contexto_imediato.py
921053c...

mente_laylay/autonomia/pre_fluxo_contextual.py
8b75bed...

tests/test_continuidade_geral.py
c4f019ec6e6fab967748a2462d380533b6aaea88
```

Essas mudanças estão incorporadas no commit final `3e3d902...`.

---

# 14. ESTADO FORMAL — O QUE ESTÁ FECHADO

```text
C1-B2 ................................ CLOSED
C1-C ................................. CLOSED

C1-D target-only ..................... CLOSED
C1-D promoção confirmada ............. CLOSED
C1-D referência contextual ........... CLOSED
C1-D Store CLOSE identity ............ CLOSED
C1-D Store CLOSE físico 159 .......... GREEN
C1-D Store CLOSE físico 179 .......... GREEN

92-A carrier arquivo ................. CLOSED BEHAVIORALLY
92-C causal success .................. CLOSED BEHAVIORALLY
92 false "app_fechado" ............... ELIMINADO
92 generic "janela" .................. ELIMINADO
92 physical window outcome ........... SAFE FAIL / sem janela correspondente

180 pergunta herdando CLOSE_APP ....... CLOSED BEHAVIORALLY
180 zero dispatch no chaos ............ GREEN

189 duplicate reminder anomaly ........ NÃO REPRODUZIDA / PASS
```

---

# 15. ESTADO FORMAL — O QUE ESTÁ ABERTO

```text
P1 — 228 negação vira CLOSE_APP ........ OPEN
P1 — 229 fecha alvo explicitamente negado OPEN / PRIORIDADE MÁXIMA
P1 — 230 contraste + "deixa quieta" ..... OPEN

P1 — 251 aspas executam CLOSE_APP ....... OPEN

P2 — MAXIMIZE Microsoft Store ........... OPEN
P2 — relato "o que você fechou?" ........ OPEN
P2 — contexto lâmpada/Prime Video ....... OPEN
P2 — consulta "qual dos dois" ........... OPEN
P2 — "meus gostos" -> PEOPLE_QUERY ...... OPEN

K0 retry público genérico ............... RED LATERAL HISTÓRICO
K1 E2 ................................... RED LATERAL HISTÓRICO
```

---

# 16. PRÓXIMA ETAPA CORRETA

## Prioridade 1 — turnos 228–230

Começar pelo 229 porque houve efeito físico confirmado no alvo proibido:

```text
"fecha só a microsoft store, não o opera"
                 ↓
           FECHOU OPERA
```

Ordem:

1. congelar commit `3e3d9027...`;
2. congelar result dir do chaos;
3. reconstruir exatamente os turnos 228–230;
4. estudar parser/segmentador/negação/contraste/extração de app;
5. localizar a **primeira fronteira** em que `"não o opera"` passa de restrição para candidato;
6. RED isolado sem processo físico;
7. falsificações:
   - `fecha A, não B`;
   - `fecha só A`;
   - `não fecha B`;
   - `deixa B quieto`;
   - `abre A e B mas não fecha nenhum`;
   - pergunta/metalinguagem;
8. somente depois candidato;
9. segunda revisão integral;
10. patch;
11. regressão focada;
12. chaos real.

## Prioridade 2 — turno 251

Depois, ou em falsificação conjunta se a primeira fronteira provar ser a mesma:

```text
aspas: "fecha a microsoft store"
```

Deve permanecer metalinguagem/zero efeito.

## Prioridade 3 — MAXIMIZE Store

Investigar identidades por operação para maximização sem tocar o CLOSE já fechado.

---

# 17. AVISO PARA A PRÓXIMA CONVERSA

Se um novo chat começar daqui:

```text
NÃO reabrir o 92 porque ele teve falha_execucao.
A falha foi SAFE FAIL no executor correto.

NÃO reabrir o 180.
O chaos real provou comandos=[].

NÃO reabrir C1-D Store CLOSE.
159 e 179 fecharam fisicamente com confirmação.

COMEÇAR pelo 229:
"fecha só a microsoft store, não o opera"
→ Opera foi fechado de verdade.
```

Esta é a fronteira prioritária atual.

---

# 18. RESUMO DE UMA TELA

```text
BASELINE 4.0:
28 pass / 20 fail / 4 alerts / 53.85%

PÓS STORE 4.1:
28 pass / 21 fail / 3 alerts / 53.85%
(+189 lateral)

PATCHES 92/180:
92-A domain carrier
92-C causal close
180 repair authority refinement

REGRESSÃO:
4.12 pegou guard amplo demais
4.14 V2 refinou por operação atual
4.16 GREEN
4.17 V2 = 55/55 GREEN

CHAOS FINAL teste 4.9:
30 pass / 19 fail / 2 alerts / 58.82%

92:
root antigo CLOSED
runtime = arquivo correto + safe fail

180:
CLOSED
runtime = pergunta + comandos=[]

Store CLOSE:
CLOSED
159 GREEN
179 GREEN

NOVO P1:
228–230 negação/contraste
229 fechou exatamente o app negado

NOVO P1:
251 aspas executaram CLOSE_APP
```

---

# 19. APÊNDICE HISTÓRICO — HANDOFF TESTE 4.0 (IMUTÁVEL)

> O conteúdo abaixo é o handoff anterior preservado integralmente.
> Onde ele diz que C1-D/Store ainda estava OPEN, isso descreve corretamente **a fotografia histórica do teste 4.0**, não o estado atual.

# HANDOFF LAYLAY — 2026-08-19 — TESTE 4.0 / C1-D PÓS-CHAOS / EVENTO DA ESCOLA

> Continuação operacional dos handoffs anteriores. Os handoffs históricos permanecem imutáveis; este arquivo consolida o estado atual, as provas novas e as regras aprendidas.
>
> Projeto: `pedrobarretto1/projeto-laylay`
>
> Estado desta fotografia: após o chaos **teste 4.0**, commit `47b7f0c98efafd73e8034c2e11654b73f3d9831b`.

---

## 0. CONTEXTO NOVO DE PRODUTO: APRESENTAÇÃO NA ESCOLA

Pedro vai apresentar a Laylay em um pequeno evento da escola. Mesmo sendo um evento pequeno, a partir daqui isso muda a prioridade operacional do projeto:

1. **estabilidade de demo > ampliar escopo na pressa**;
2. manter fechados os roots já provados;
3. evitar mega-patches perto da apresentação;
4. preferir fluxos observáveis, confirmáveis e reproduzíveis;
5. separar defeito de inteligência de defeito físico/integrador;
6. preparar uma lista curta de habilidades demonstráveis e uma lista explícita de integrações ainda não confiáveis;
7. não usar Microsoft Store como exemplo de `CLOSE_APP` até a nova raiz de identidade física ser resolvida;
8. antes do evento, executar um preflight de Chrome/extensão, apps usados na demo, áudio, IoT, rede e executor de janelas.

A apresentação deve mostrar a Laylay como **sistema integrado**, não como coleção de truques isolados: continuidade de contexto, controle de apps, browser, IoT, memória e personalidade podem ser demonstrados em uma sequência curta e segura.

---

# 1. REGRAS SOBERANAS DE INVESTIGAÇÃO — VERSÃO CONSOLIDADA

Estas regras continuam obrigatórias.

1. **Estudar antes de criar arquivo ou patch.** Ordem: estudar → provar RED → localizar primeira fronteira causal → falsificar hipótese → candidato em espelho → auditoria → patch de produção → runtime real/chaos.
2. **“Runtime real” não é nome de runner.** Só é real se atravessa o mesmo caminho causal do chaos. Funções reais com gates/callbacks sintéticos continuam sendo integração intermediária.
3. Caminho completo: `entrada → turno congelado → porta pública → gates reais → ciclo canônico → árbitro → executor → publicação`.
4. **A primeira fronteira RED manda no diagnóstico.** Não corrigir a camada mais barulhenta se a quebra nasceu antes ou depois dela.
5. Harness e produção são raízes diferentes.
6. Nunca atualizar HEAD lock só para o runner aceitar uma baseline nova.
7. HEAD lock sozinho não basta: travar blobs causais e, quando possível, working tree/index causal.
8. **Contexto, referência linguística, alvo e autoridade são contratos diferentes.**
9. **Contexto nunca aumenta autoridade:** `child_authority <= parent_authority`.
10. Elipse operacional estreita não deve contaminar a linguagem global.
11. Antes de candidato: falsificar sem contexto, contexto errado, alvo falho/não confirmado, negação, pergunta, citação/metalinguagem e formas próximas.
12. Dívida lateral descoberta durante uma raiz continua lateral; não fazer mega-patch.
13. Runner diagnóstico deve ser read-only por padrão.
14. Segunda auditoria integral antes da escrita é obrigatória.
15. Chaos físico/runtime real é evidência soberana de fechamento.
16. Nunca enfraquecer teste para obter verde.
17. Nunca fazer `git add`, `commit`, `push`, `reset`, `checkout`, `restore` etc. automaticamente.
18. Caçar gates escondidos; presumir candidato errado até falsificá-lo.
19. Preservar artefatos históricos de diagnóstico.
20. Patch de produção só depois de diff exato auditado.
21. Se harness falhar, provar harness × candidato antes de tocar produção.
22. Roots fechados são território fechado até existir regressão causal nova.
23. Não inferir resultados de casos pulados após falha anterior.
24. Aliases importados diretamente podem invalidar monkeypatch pós-import.
25. `somente_alvo=True` nunca pode virar referente genérico de pronome.
26. Materialização de referência deve preservar proveniência; nome concreto nascido de pronome não vira “explícito” automaticamente.
27. Domínio diagnóstico vazio/None tem semântica dependente do caller; provar cada uso.
28. Estar em catálogo não significa ser aceitável como fallback de detector.
29. Inventariar resolvers paralelos que transformam referência em concreto antes do patch.
30. **Conservação de referência:** se o alvo original é referencial, nenhuma camada anterior ao sink canônico `resolver_referencias_da_intencao` pode apagar o demonstrativo, materializar por saliência histórica, trocar o domínio por causa dessa perda ou criar autoridade sem evidência canônica do turno atual.
31. Runner grande: AST/compile não bastam; auditar globais, dependências não-função, fidelidade de aliases e construção real do runtime.
32. Memória operacional confirmada, retarget target-only e elegibilidade dêitica linguística são contratos separados.

## 1.1 Regras novas aprendidas no teste 4.0

33. **Verde semântico não prova executor físico.** O relatório semântico pode reconhecer intent/alvo corretos enquanto a ação final falha. Para fechamento, olhar também `planos.jsonl`, `terminal.log`, resultado do executor e confirmação.
34. **Intent correta + alvo correto + executor chamado + falha física = nova raiz em camada inferior.** Não reabrir referência/autoridade já provadas por causa de um erro de executor.
35. **Identidade de app é multilayer:** alias falado ≠ chave de catálogo ≠ launch locator/URI ≠ identidade de janela ≠ nome/PID de processo. Uma URI válida para abrir não deve ser presumida válida para fechar por processo.
36. **Resultado confirmado é a fronteira de promoção.** Um alvo novo pode ser conhecido, planejado e até tentado; só entra como referente operacional válido quando o efeito que sustenta essa promoção foi confirmado.
37. **Auditor pós-patch deve usar produção, não replay de candidato.** Para fechamento forte: implementação candidata embutida = ZERO; monkeypatch causal = ZERO.
38. **Não dar crédito causal por coincidência.** Um teste lateral que melhorou (ex.: agenda) só é atribuído ao patch se houver caminho causal demonstrado.
39. Em período pré-demo, novas raízes laterais devem ser isoladas e priorizadas por risco de apresentação; não desestabilizar roots fechados.

---

# 2. TERRITÓRIO FECHADO ANTES DO C1-D

## C1-B2 — `maximiza` puro — CLOSED

Contrato final:

```text
fala atual: "maximiza"
→ autoridade estreita vem da fala atual
→ contexto pode fornecer app confirmado
→ reconciliador só aceita se:
   ultimo_app_janela == retrato.entidades["app"].nome
→ MAXIMIZE_WINDOW(app confirmado)
```

Princípio preservado:

```text
contexto fornece alvo
contexto NÃO fornece autoridade
```

No chaos 4.0, turno 155 voltou a provar fisicamente:

```text
MAXIMIZE_WINDOW opera
status=janela_maximizada
confirmado=True
```

Portanto C1-B2 continua CLOSED.

## C1-C — turno 156 `esquerda` — CLOSED

Contrato:

```text
"esquerda"
→ autoridade atual estreita
→ exige alvo app confirmado
→ ORGANIZAR_DESKTOP(left=app)
→ confirmação por geometria real
```

No chaos 4.0:

```text
156 esquerda
→ ORGANIZAR_DESKTOP(left=opera)
→ layout_confirmado
→ executou=True
→ confirmado=True
```

C1-C continua CLOSED.

---

# 3. C1-D — O “155: 2.0”

O corredor que abriu C1-D parecia simples:

```text
157 agora a calculadora / agora a microsoft store
158 direita
159 fecha ela
```

Mas ele repetiu a lição do 155 original em escala maior.

## 3.1 Contrato desejado

```text
157 novo alvo app
    target-only
    sem efeito
    sem autoridade

158 direita
    efeito/direção vem da fala atual
    autoridade vem da fala atual
    alvo vem SOMENTE do receipt imediatamente anterior
    → ORGANIZAR_DESKTOP(right=novo_app)

se 158 confirmado:
    novo_app vira referente operacional válido

159 fecha ela
    → CLOSE_APP novo_app
```

Se 158 falhar ou ficar não confirmado:

```text
novo app NÃO é promovido
Opera confirmado continua histórico válido
layout falho pode continuar disponível para retry explícito
pronome/dêitico não pode cair silenciosamente no alvo antigo
```

---

# 4. ARQUITETURA FINAL DO C1-D

## D1 — target-only como receipt de turno

Foi rejeitado o desenho antigo de guardar o alvo isolado em `entidades_recentes["app"]`.

O contrato correto virou receipt local do turno:

```python
turno_atual["retarget_operacional"] = {
    "tipo": "app",
    "nome": "calculadora",
    "origem": "retarget_operacional_explicito",
    "somente_alvo": True,
    "autoriza_execucao": False,
    "retarget_turno_id": 157,
}
```

Isto impede:

- target-only virar memória global;
- target-only virar referente genérico;
- target-only criar autoridade;
- 157 executar qualquer ação sozinho.

## D2 — `direita` consome receipt imediato

`direita` ganha somente a autoridade espacial da fala atual.

O reconciliador aceita o alvo novo apenas se o receipt anterior possuir shape exato, origem correta, `somente_alvo=True`, `autoriza_execucao=False` e `retarget_turno_id` consistente.

Sem receipt:

```text
direita
→ requer_esclarecimento
→ zero ação
→ NÃO cai em ultimo_app_janela
```

## D3 — promoção somente após confirmação

`ORGANIZAR_DESKTOP` passou a promover referência operacional apenas quando `contrato_confirma_referencia_operacional(...)` confirma a ação.

Quando um layout single-side é confirmado, o alvo também pode atualizar o foco operacional de janela.

Assim:

```text
receipt != referente
intent planejada != referente
execução tentada != referente
resultado confirmado = pode virar referente
```

## Quarentena derivada

Se um `ORGANIZAR_DESKTOP` contextual tentou alvo diferente do último app confirmado e falhou/não confirmou dentro do TTL, deriva-se uma quarentena temporária.

Ela não é persistida como nova memória global.

Durante a quarentena, referências curtas de app como:

```text
fecha ela
fecha esse app
fecha esse programa
fecha esse aplicativo
fecha essa janela
maximiza ela
maximiza esse app
maximiza essa janela
coloca esse app na direita
coloca essa janela na direita
abre esse app
abre esse programa
abre essa janela
```

não podem ser resolvidas silenciosamente contra o app antigo.

Controles preservados:

```text
fecha essa aba
abre esse arquivo
fecha o Opera
abre a calculadora
maximiza
 direita (sem receipt continua fail-closed)
```

---

# 5. F1–F4 — CONSERVAÇÃO DE REFERÊNCIA

Quatro bypasses paralelos foram encontrados.

## F1 — `fecha esse app`

Antes, o demonstrativo podia ser apagado e a intenção chegar como `CLOSE_APP("app")`.

Correção: preservar a referência tipada crua até o sink canônico.

## F2 — `abre esse app`

O extrator de app podia recusar a referência e outro domínio roubar a frase.

Correção: reconhecer forma tipada de app sem materializá-la historicamente.

## F3 — `maximiza esse app`

O detector contextual podia materializar cedo demais via `ultimo_app_janela`.

Correção: referência contextual permanece referência até o sink.

## F4 — layout pós-processado

O pós-processamento de layout consultava saliência de app antes do sink canônico.

Correção estreita: remover somente essa materialização `dominio="app"`; saliências de outros domínios não foram apagadas.

---

# 6. CAMINHO DOS MIRRORS ATÉ PRODUÇÃO

## V6 FIX3 — pré-patch integrado

Artefato:

```text
mirror_integrado_c1d_v6_FIX3_FINAL_PRE_PATCH_teste3_9_1.py
SHA-256 32a96e2e7fc5c3b7e9f54fe033e5a07af637dbf47710e162c6ba87103392018f
```

Resultado do usuário:

```text
baseline ................................ PASS
snapshot ................................ PASS
F4 ...................................... PASS
APPS_MAP ................................ PASS
arquitetura ............................. PASS
direita sem receipt .................... PASS
corredor confirmado .................... PASS
falha ................................... PASS
não-confirmado ......................... PASS
retry público genérico ................. RED LATERAL PRESERVADO
C1-B2/C1-C .............................. PASS
E2 ...................................... RED LATERAL PRESERVADO
HEAD/tree ............................... PASS
```

## Patch V1 — rejeitado antes da escrita

Erro do harness: auditor F4 contava todas as chamadas de saliência, embora só a saliência de app devesse desaparecer.

Lição: auditor estrutural deve provar o contrato específico, não contar tokens cegamente.

## Patch V2 — rejeitado antes da escrita

Primeiro houve falso negativo do próprio auditor ao exigir literal `"left"` dentro de função que delegava a `_forma_elipse_espacial_exata`.

Lição: **execução comportamental > presença textual de literal**.

Depois a análise profunda encontrou uma falha REAL de construção do runtime:

```text
APPS_MAP não atravessava DEPENDENCIAS_ORQUESTRACAO_TURNO
```

Mirrors alimentavam `APPS_MAP` diretamente e podiam mascarar isso.

Lição: testar não apenas funções, mas o caminho de construção dos serviços.

## Patch final V3 FIX3

Aplicador:

```text
patch_c1d_producao_v3_fix3_FINAL_AUDITADO.py
SHA-256 59b61c71f7f98ff8ee7abf63b86d998e8637e6d2e0e424c2474b6cd000a123ca
```

Diff de produção congelado:

```text
2bacaaeb6377ee65abaa65f63b7b4ccb9146099ca592eaea732a4962482148a4
```

Arquivos alterados:

1. `mente_laylay/cognicao/composicao_turno.py`
2. `mente_laylay/cognicao/orquestrador_turno_runtime.py`
3. `mente_laylay/autonomia/roteador_deterministico.py`
4. `mente_laylay/autonomia/orquestrador_deterministico.py`
5. `mente_laylay/autonomia/coordenador_intencao.py`
6. `mente_laylay/memoria_mental/contexto_compartilhado.py`
7. `mente_laylay/memoria_mental/contexto_imediato.py`

Check real do usuário:

```text
A HEAD + 23 blobs causais + tree/index ........ PASS
B 7 arquivos + AST/compile .................... PASS
C runtime construction + C1-B2/C1-C/D1/D2/D3  PASS
```

Apply real do usuário:

```text
D escrita transacional + compile pós-write .... PASS
E git diff --check ............................. PASS
Git add/commit/push ............................ NÃO executados pelo aplicador
```

---

# 7. AUDITOR PÓS-PATCH — PRODUÇÃO REAL

Artefato:

```text
auditor_pos_patch_c1d_PRODUCAO_REAL_teste3_9_1.py
SHA-256 647f962eb18383c69308347595428b931b1f6b3ece20b431b4a7e6daeaa3bb56
```

Propriedades:

```text
implementação candidata no runner ........ ZERO
monkeypatch causal ....................... ZERO
porta pública ............................ REAL
detector ................................ REAL
ciclo ................................... REAL
coordenador ............................. REAL
memória ................................. REAL
executor final .......................... SPY
```

Resultado do usuário:

```text
A baseline pós-patch + diff exato ........ PASS
B integração real ....................... PASS
C snapshot .............................. PASS
D C1-B2/C1-C/D1/D2 ...................... PASS
E D3-D + quarentena + foco .............. PASS
F F1-F4 + sink + cross-domain ........... PASS
G direita sem receipt ................... PASS
H corredor público confirmado ........... PASS
I corredor público falha ................ PASS
J corredor público não-confirmado ....... PASS
K0 retry genérico ....................... RED LATERAL PRESERVADO
K1 E2 ................................... RED LATERAL PRESERVADO
Z estado preservado ..................... PASS
```

Isto autorizou o chaos físico.

---

# 8. CHAOS TESTE 4.0 — RESULTADO REAL

Commit:

```text
47b7f0c98efafd73e8034c2e11654b73f3d9831b
mensagem: teste 4.0
```

Diretório:

```text
resultados_testes/roteiro_teste_laylay_caos-20260819-094420-687379
```

## 8.1 Placar

```text
267/267 respostas
52 avaliados semanticamente
28 passaram
20 falharam
4 alertas
53.85% taxa semântica
119 comandos observados
14 confirmações indeterminadas
```

Comparação estrita com o chaos 3.9 salvo:

```text
3.9: 26 pass / 24 fail / 48.15% / 26 confirmado=None
4.0: 28 pass / 20 fail / 53.85% / 14 confirmado=None

delta: +2 pass, -4 fail, +5.70 p.p., 26→14 confirmações indeterminadas
```

No domínio apps:

```text
3.9: 4 pass / 4 fail
4.0: 5 pass / 0 fail semanticamente avaliadas
```

Turnos que saíram da lista de erros entre 3.9 e 4.0:

```text
96
112 — Maximiza ele.
179 — Fecha ela.
189 — lembrete
```

Cuidado causal:
- 112 e 179 são coerentes com a melhora estrutural de referência operacional;
- 189 não deve ser creditado ao C1-D sem prova específica;
- 96 também precisa de análise própria antes de atribuição causal.

---

# 9. CORREDOR 154–159 — PROVA PÓS-CHAOS

## 154 — Opera

```text
APP_OPEN opera
confirmado=True
```

## 155 — `maximiza`

```text
MAXIMIZE_WINDOW opera
status=janela_maximizada
confirmado=True
```

C1-B2 preservado.

## 156 — `esquerda`

```text
ORGANIZAR_DESKTOP
left=opera
status=layout_confirmado
executou=True
confirmado=True
```

C1-C preservado.

## 157 — `agora a microsoft store`

Relatório:

```text
sem intent
```

Isto é CORRETO.

O turno só muda o target receipt; não publica ação física e não cria autoridade.

## 158 — `direita`

Resultado físico:

```text
intent=ORGANIZAR_DESKTOP
right=microsoft store
referencia_contextual=True
referencia_contextual_fonte=turno_atual.referencia_resolvida
direcao_original=direita
status=layout_confirmado
executou=True
confirmado=True
```

Isto prova D2 e D3: receipt consumido, alvo correto, efeito atual autorizado, resultado confirmado e promoção operacional permitida.

## 159 — `fecha ela`

### Camada semântica/referencial — GREEN

A Laylay escolheu corretamente:

```text
intent=CLOSE_APP
alvo=microsoft store
params.nome_app=microsoft store
referencia_contextual=True
```

Portanto o objetivo cognitivo do 155:2.0 foi atingido: o pronome se refere ao novo app confirmado, não ao Opera antigo.

### Camada física — RED

O executor retornou:

```text
Nenhum processo seguro e exato encontrado para fechar: 'ms-windows-store:'
status=falha_execucao
executou=False
confirmado=False
```

A Laylay respondeu corretamente sem fingir sucesso.

Consequência:

```text
C1-D autoridade/retarget/referência ........ GREEN
C1-D 158 efeito/promoção ................... GREEN
C1-D 159 escolha CLOSE_APP Store ........... GREEN
C1-D 159 efeito físico fechar Store ......... RED
C1-D full closure .......................... OPEN
```

Primeira fronteira RED atual:

```text
executor físico CLOSE_APP / identidade física do app
```

Não reabrir D1/D2/D3/F1–F4 por causa desse RED.

---

# 10. NOVA RAIZ DE EXECUTOR — IDENTIDADE DA MICROSOFT STORE

O terminal oferece evidência forte de uma separação de identidade ainda não modelada corretamente no fechamento.

Para abrir a Microsoft Store, o sistema usa um locator de protocolo:

```text
microsoft store → ms-windows-store:
```

Esse locator é adequado como mecanismo de launch/reativação.

No `CLOSE_APP`, porém, o executor tenta localizar processo/janela usando esse mesmo valor e registra:

```text
Nenhum processo seguro e exato encontrado para fechar: 'ms-windows-store:'
```

Hipótese estrutural forte, AINDA NÃO PATCHADA:

```text
spoken alias       = microsoft store
catalog identity   = microsoft store
launch identity    = ms-windows-store:
window identity    = outra representação
process identity   = outra representação
```

Regra nova:

> `open_locator` não é automaticamente `close_locator`.

Antes de qualquer patch dessa nova raiz:

1. estudar o executor de janelas/processos;
2. localizar exatamente onde `nome_app` vira locator físico;
3. inventariar apps especiais/UWP/protocol handlers;
4. provar RED isolado Microsoft Store sem mexer em C1-D;
5. falsificar Opera/Win32 e outros apps comuns;
6. só depois desenhar contrato de identidade de app por operação.

Não fazer `if microsoft store: mata processo X` no escuro.

---

# 11. “155 ORIGINAL” × “155: 2.0” — LIÇÕES PERMANENTES

## 11.1 Por que são parentes

### 155 original

Fala:

```text
maximiza
```

Parecia “falta uma regex”, mas expôs:

```text
autoridade
≠ referência linguística
≠ elipse operacional
≠ alvo contextual
≠ candidato
≠ caminho real do runtime
```

### 155: 2.0

Falas:

```text
agora a microsoft store
 direita
 fecha ela
```

Parecia “lembrar o app e usar direita”, mas expôs:

```text
novo alvo conhecido
≠ referente operacional confirmado
≠ autoridade
≠ memória global
≠ receipt local
≠ efeito confirmado
≠ identidade física do app
```

## 11.2 A diferença mais importante

No 155 original, o alvo útil já era um **app confirmado anterior**.

No 155:2.0, o usuário introduz um **alvo novo sem pedir efeito**.

Portanto o sistema precisa distinguir:

```text
"eu mencionei este app agora"
```

de:

```text
"este app realizou um efeito confirmado e agora pode ser usado como referente operacional"
```

Essa distinção originou o receipt target-only e a promoção confirmada.

## 11.3 O que foi aprendido com a dificuldade

1. **Falas curtas são testes de arquitetura.** Uma palavra pode atravessar mais contratos que uma frase completa.
2. **Não resolver elipse com saliência frouxa.** `ultimo_alvo` não é contrato suficiente.
3. **Target-only é protocolo, não memória.** Receipt de turno tem lifecycle diferente de entidade global.
4. **Autoridade pertence à fala atual.** Contexto só pode preencher dados permitidos.
5. **Referência deve ser conservada.** Demonstrativo/pronome não pode desaparecer antes do sink canônico.
6. **Falha precisa de quarentena, não de mentira.** Depois de uma tentativa não confirmada, nem alvo novo nem alvo antigo devem ser escolhidos silenciosamente para dêiticos ambíguos.
7. **Confirmação promove; tentativa não.** Isso evita contaminar continuidade com estados imaginados.
8. **Construção de runtime é parte da funcionalidade.** `APPS_MAP` ausente da composição teria deixado um mirror verde e a produção vermelha.
9. **Auditoria comportamental vence busca textual.** O incidente do literal `left` provou isso.
10. **Focus publication é gate causal.** Um efeito confirmado precisa publicar contexto compatível para o próximo turno.
11. **Auditor pós-patch não pode trazer o candidato escondido.** Zero candidato/zero monkeypatch causal.
12. **Verde semântico não é fechamento físico.** O 159 do teste 4.0 é a prova definitiva dessa regra.
13. **Não reabrir camada certa por erro abaixo.** CLOSE_APP recebeu o alvo certo; agora o bug está no executor/identidade.
14. **Identidade de app precisa ser por capacidade/operação.** Launch URI, window handle e PID são objetos diferentes.
15. **Ganhos laterais são sinais, não prova causal.** 112/179 são plausíveis; agenda 189 não deve ser atribuída sem investigação.
16. **Perto de uma demo, preservar arquitetura ganha da pressa.** Corrigir nova raiz isoladamente; não mexer em closed territory.

## 11.3.1 Lição nova do auditor pós-chaos: stdout ≠ artefato persistido

O pós-chaos acrescentou uma lição ao mesmo padrão dos dois 155:

```text
o que apareceu no console durante o teste
≠
o que foi persistido em terminal.log
```

O V1 viu no console marcadores `ROTEIRO:NNN` e presumiu que eles existiam para
todos os turnos dentro do arquivo. Não existiam.

Regra:

> **Auditar a estrutura real do artefato antes de construir o parser do auditor.**

Isso é o equivalente, na infraestrutura de testes, da regra de runtime fiel:
um harness que modela um formato que o runtime não produz pode gerar RED falso
mesmo quando produção está correta.

## 11.4 Regra-resumo dos dois 155

```text
FALA ATUAL fornece autoridade.
CONTEXTO fornece somente dados permitidos.
RECEIPT guarda alvo novo sem promovê-lo.
SINK CANÔNICO resolve referência sem perder proveniência.
RESULTADO CONFIRMADO permite promoção.
EXECUTOR FÍSICO ainda precisa entender a identidade correta do alvo.
```

---

# 12. DÍVIDAS LATERAIS PRESERVADAS

## K0 — retry público genérico

```text
tenta de novo
```

O resolver encontra o ORG retryável, mas modalidade/P0 ainda bloqueiam antes da rota pública.

Status:

```text
RED LATERAL PRESERVADO
```

Não corrigir dentro do root de identidade física da Store sem causalidade.

## K1 — E2

Permanece fora do corredor C1-D.

```text
RED LATERAL PRESERVADO
```

## Nova raiz — CLOSE_APP Microsoft Store

Não é “referência errada”.

```text
CLOSE_APP alvo correto
→ executor físico não encontra identidade segura/exata
```

Status:

```text
RED FÍSICO / BLOQUEIA FECHAMENTO FULL C1-D
```

---

# 13. AUDITOR PÓS-CHAOS 4.0

## 13.1 Auditor V1 — REJEITADO POR FALSO NEGATIVO DO HARNESS

Artefato histórico:

```text
auditor_pos_chaos_c1d_teste4_0.py
SHA-256 f5db10141bf976569fc645a42fb408091c1db8112afce9c991b51884939c6578
```

Execução real no clone do Pedro:

```text
A HEAD + artefatos + placar 4.0 ........ PASS
B comparação 3.9→4.0 ................... PASS
C matriz semântica 154→159 ............. PASS

AUDITOR INCONCLUSIVO:
terminal sem marcador ROTEIRO:154
estado Git preservado
```

**Classificação:** falha do harness, não do candidato nem da produção.

Raiz do V1:

```text
o auditor assumiu:
cada turno em terminal.log termina em [ROTEIRO:NNN]

mas o artefato real garante:
💬 Você:
> comando

e [ROTEIRO:NNN] é ESPARSO.
```

Os marcadores `ROTEIRO:NNN` aparecem apenas em determinados caminhos do runner
(falha registrada, avaliação especial etc.). Portanto eles não podem ser usados
como fronteira universal de turno.

Esta é uma nova regra permanente:

> **A fronteira usada por um auditor deve existir no artefato que ele realmente
> lê, não apenas no stdout visto durante a execução.**

E outra:

> **Marcador esparso de erro/telemetria não é identificador canônico de turno.**

O V1 fica congelado como evidência histórica de harness incorreto. Não “consertar
o resultado” alterando produção.

## 13.2 Auditor V2 — FRONTEIRA FIEL AO ARTEFATO

Novo artefato:

```text
auditor_pos_chaos_c1d_teste4_0_v2.py
SHA-256 5a0c5000148e3d06f4461c8b66dbcb3e95ab5fa5ae4da68149e30512aa7aa7a3
```

Mudança causal única do auditor:

```text
ANTES:
turn_block() buscava [ROTEIRO:154], [ROTEIRO:155]...

AGORA:
1. conta exatamente 267 blocos iniciados por `💬 Você:`;
2. indexa esses blocos em ordem 1..267;
3. extrai o comando real após `>`;
4. cruza o comando da posição N com o comando da linha N do relatorio_semantico.md;
5. só então audita o conteúdo físico daquele bloco.
```

Isso cria uma prova de alinhamento em duas fontes independentes:

```text
posição no terminal real
        ↕
número + comando na matriz semântica
```

Se houver um turno ausente, extra ou deslocado, o V2 falha antes de interpretar
154–159.

Propriedades preservadas:

```text
read-only .......................... SIM
executor chamado .................. NÃO
Git mutation ...................... NÃO
HEAD travado ...................... 47b7f0c98efafd73e8034c2e11654b73f3d9831b
result dir travado ................ chaos-20260819-094420-687379
AST/compile ....................... PASS
fixture marcador ROTEIRO esparso .. PASS
```

Ele exige:

- placar 4.0 exato;
- exatamente 267 blocos reais `💬 Você:`;
- alinhamento terminal↔matriz nos turnos 154→159;
- C1-B2 físico 155 verde;
- C1-C físico 156 verde;
- D1 157 target-only/zero executor;
- D2/D3 158 ORG right Store confirmado;
- 159 `CLOSE_APP microsoft store` semanticamente correto;
- 159 `falha_execucao`, `executou=False`, `confirmado=False` fisicamente;
- assinatura `ms-windows-store:` no erro;
- working tree/index preservados.

Contrato de exit code:

```text
0 = corredor físico inteiro fechado
2 = auditor saudável confirmou o RED físico já conhecido
1 = auditor/harness falhou ou baseline divergiu
```

Nesta fotografia, **exit 2 continua sendo o resultado esperado**, mas somente
depois de A..Z passarem e o RED físico aparecer na fronteira correta.

---

# 14. ESTADO OFICIAL ATUAL

```text
C1-B2 bare maximiza ........................ CLOSED
C1-C esquerda .............................. CLOSED

C1-D D1 target-only receipt ................ GREEN / PROVADO
C1-D D2 direita + receipt .................. GREEN / PROVADO
C1-D D3 promoção só confirmada ............. GREEN / PROVADO
C1-D F1-F4 conservação ..................... GREEN / PROVADO
C1-D quarentena falha/não-confirmado ....... GREEN / PROVADO
C1-D produção real pós-patch ............... GREEN
C1-D chaos 157→158 referência .............. GREEN
C1-D chaos 159 CLOSE_APP alvo .............. GREEN
C1-D chaos 159 efeito físico Store ......... RED

C1-D FULL CLOSED ........................... NÃO
primeira fronteira RED atual ............... executor CLOSE_APP / identidade física

K0 retry público genérico .................. RED LATERAL PRESERVADO
K1 E2 ...................................... RED LATERAL PRESERVADO

Teste 4.0 .................................. 28 pass / 20 fail
apps semanticamente avaliadas .............. 5 pass / 0 fail
confirmacoes_indeterminadas ................ 14 (antes 26 no 3.9)
```

---

# 15. PRÓXIMA ETAPA CORRETA

1. Manter `auditor_pos_chaos_c1d_teste4_0.py` V1 congelado como falso negativo histórico.
2. Rodar `auditor_pos_chaos_c1d_teste4_0_v2.py`.
3. Esperar **exit code 2** somente após o alinhamento terminal↔matriz e todas as provas físicas passarem.
4. Não reabrir C1-B2/C1-C/D1/D2/D3/F1–F4.
5. Abrir investigação isolada de **identidade física para CLOSE_APP Microsoft Store**.
6. Estudar profundamente o caminho:

```text
CLOSE_APP(nome_app="microsoft store")
→ catálogo/mapping
→ locator usado pelo executor
→ descoberta de janela/PID
→ política de fechamento seguro
→ releitura/confirmacao
```

7. Provar em RED isolado por que `ms-windows-store:` serve para launch mas não para fechamento seguro por processo/janela.
8. Falsificar com Opera e outros apps Win32 antes de candidato.
8. Só depois decidir se o contrato correto precisa de identidades separadas, por exemplo:

```text
alias
open_locator
window_match
process_match
close_strategy
```

Isto é hipótese de arquitetura, não patch aprovado ainda.

---

# 16. NOTA PARA A APRESENTAÇÃO

O teste 4.0 é um resultado forte para a apresentação porque mostra evolução real:

```text
3.9 → 4.0
26 → 28 passes
24 → 20 falhas
48.15% → 53.85%
26 → 14 confirmações indeterminadas
apps: 4 pass/4 fail → 5 pass/0 fail semanticamente avaliadas
```

Mas para demo ao vivo:

- usar Opera/Chrome/apps Win32 conhecidos para `maximiza`, organização e fechamento;
- Microsoft Store pode ser usada para mostrar abertura/organização se pré-testada, mas evitar `CLOSE_APP` até a raiz física ser corrigida;
- priorizar fluxos 144/145 de browser, C1-B2/C1-C, IoT confirmado e memória/conversa que já estejam estáveis;
- ter um roteiro curto de 5–8 interações e um preflight antes da apresentação;
- manter logs/terminal acessíveis para mostrar que a Laylay confirma estados em vez de fingir sucesso.

O fato de o turno 159 ter respondido que **não conseguiu fechar**, em vez de declarar falso sucesso, também é uma qualidade arquitetural importante: observabilidade e honestidade de execução estão funcionando mesmo quando uma integração física falha.

---

## Fim do handoff

Este snapshot substitui apenas o **estado operacional atual**. Ele não apaga nem reescreve a história dos handoffs anteriores.
