# Inventário de Fluxos Atuais da Laylay

## Objetivo

Este inventário registra, de forma curta e objetiva, quais pontos do projeto
hoje:

- recebem a fala do usuário;
- interpretam intenção;
- executam ação;
- alteram contexto e estado mental;
- montam o prompt;
- geram a resposta final;
- ainda representam risco de competição entre fluxos.

Ele existe para cumprir a Fase 0 do `plano_refatoracao.md` antes de novas
extrações maiores.

---

## 1. Onde a fala do usuário entra

### Chat principal

- [laylay.py#L10018](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L10018)
  `gerar_resposta_exec_ia(texto)`
- [laylay.py#L10031](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L10031)
  `_gerar_resposta_exec_ia_sync(texto)`

Esses dois pontos são hoje a porta principal do modo conversa/chat com
comandos misturados.

### Conversa direta sem execução prática

- [laylay.py#L9748](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L9748)
  `gerar_resposta_ia(texto)`

Esse fluxo ainda existe como trilha mais “conversa livre”.

---

## 2. Onde a intenção nasce hoje

### Pré-fluxo conversacional central

- [mente_laylay/autonomia/fluxo_resposta_ia.py#L15](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/mente_laylay/autonomia/fluxo_resposta_ia.py#L15)
  `processar_inicio_fluxo_resposta_ia(ctx, texto)`

Hoje esse é o principal portão inicial para:

- elogios;
- conversa curta;
- resposta a pergunta aberta;
- feedback pendente;
- bloqueio de playlist;
- continuidade contextual de janela/mídia;
- direção musical genérica;
- determinístico pré-IA;
- comando local rápido.

### Coordenador único de intenção

- [mente_laylay/autonomia/coordenador_intencao.py#L45](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/mente_laylay/autonomia/coordenador_intencao.py#L45)
  `resolver_intencao(texto, origem, ctx)`
- [mente_laylay/autonomia/coordenador_intencao.py#L76](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/mente_laylay/autonomia/coordenador_intencao.py#L76)
  `executar_fluxo_intencao(texto, origem, ctx)`

Ordem atual de prioridade:

1. cancelamento;
2. continuidade de mídia;
3. repetição da última ação;
4. determinístico;
5. IA-first.

### Roteadores locais ainda ativos no `laylay.py`

- [laylay.py#L9004](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L9004)
  `detectar_intencao_deterministica(texto)`
- [laylay.py#L9356](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L9356)
  `_tentar_intencao_ai_primeiro(texto)`
- [laylay.py#L8269](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L8269)
  `processar_comandos_imediatos(texto)`

Esses pontos ainda vivem no arquivo principal e continuam sendo um dos maiores
focos de peso arquitetural.

---

## 3. Onde a ação prática é executada

### Casca compatível no `laylay.py`

- [laylay.py#L8689](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L8689)
  `executar_intencao(resultado, texto_original)`

Essa função já é majoritariamente uma ponte para o executor modular.

### Executor real de intenção

- [mente_laylay/autonomia/roteador_intencao.py#L42](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/mente_laylay/autonomia/roteador_intencao.py#L42)
  `executar_intencao(resultado, texto_original, ctx)`

Esse é o centro prático real de execução hoje.

Ele ainda concentra muita responsabilidade:

- abrir/fechar app;
- abrir site/aba;
- volume;
- mídia;
- playlists;
- arquivos;
- email;
- notificações;
- agendamentos;
- clima;
- foco/maximização/organização de janelas.

---

## 4. Onde o estado mental é alterado

### Registro de memória curta e ação real

- [laylay.py#L1430](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L1430)
  `_registrar_mente_curta(...)`
- [laylay.py#L1600](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L1600)
  `_registrar_resultado_execucao(...)`
- [laylay.py#L1725](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L1725)
  `_refinar_contexto_mental(...)`

### Estados compartilhados já extraídos

- `mente_laylay/memoria_mental/contexto_compartilhado.py`
- `mente_laylay/memoria_mental/estado_continuidades.py`
- `mente_laylay/memoria_mental/estado_musical.py`
- `mente_laylay/memoria_mental/estado_percepcao.py`

### Leitura de repetição da última ação

- [laylay.py#L1691](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L1691)
  `_resolver_repeticao_ultima_acao(texto)`

---

## 5. Onde o contexto entra

### Contexto conversacional

- [laylay.py#L1023](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L1023)
  `_contexto_conversa_natural()`

Esse ponto hoje monta um grande dicionário de integração para:

- personalidade;
- respostas curtas;
- fallback;
- pesquisa contextual;
- confirmação variada;
- tom emocional;
- memória curta;
- foco vivo.

Esse é um forte candidato de extração futura.

### Contexto perceptivo vivo

- [laylay.py#L1351](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L1351)
  `_obter_contexto_perceptivo()`
- [laylay.py#L1375](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L1375)
  `_interpretar_contexto_vivo(...)`
- [laylay.py#L1389](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L1389)
  `_resumo_mente_integrada_para_prompt(...)`

Esses pontos já usam módulos extraídos, mas ainda são coordenados do
`laylay.py`.

### Montagem final do contexto para a IA

- [mente_laylay/autonomia/contexto_resposta_ia.py#L12](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/mente_laylay/autonomia/contexto_resposta_ia.py#L12)
  `preparar_contexto_resposta_ia(...)`

Esse módulo hoje é o montador real do prompt contextual final.

---

## 6. Onde a resposta final é decidida

### Fala curta e conversa local

- [laylay.py#L1323](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L1323)
  `_resposta_conversa_local(texto_usuario)`
- [laylay.py#L1331](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L1331)
  `_resposta_conversa_rapida_local(texto_usuario)`

As decisões reais vivem em:

- `mente_laylay/personalidade/conversa_natural.py`

### Fluxo de fallback conversacional

- [laylay.py#L9674](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/laylay.py#L9674)
  `_handle_llm_fallback_flow(texto)`
- [mente_laylay/autonomia/fluxos_conversa.py#L481](C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay2.5.py/mente_laylay/autonomia/fluxos_conversa.py#L481)
  `handle_llm_fallback_flow(contexto, texto)`

### Montagem da fala final após a IA

- `limpar_resposta_da_ia(...)`
- `extrair_tipo_interacao_da_ia(...)`
- `_construir_fala_conversa(...)`
- `falar_com_lipsync(...)`

Hoje a decisão da frase final ainda está distribuída entre:

- executor de intenção;
- conversa natural;
- fallbacks locais;
- confirmações variáveis;
- resposta pós-IA.

Isso aponta diretamente para a futura Fase 5 do plano.

---

## 7. Pontos que ainda usam contexto antigo para decidir

### Continuidade e repetição

- `resolver_repeticao_ultima_acao`
- `resolver_comando_midia_contextual_forcado`
- `resolver_comando_janela_contextual_forcado`
- `texto_conversa_contextual_sem_comando`
- `retomar_topico_quando_fluido`

### Feedback pendente

- `handle_feedback_pendente`
- `handle_feedback_pendente_misto`

### Riscos atuais

- um contexto recente ainda pode “ganhar força demais” quando a frase atual é
  curta;
- o `laylay.py` ainda é o principal integrador dessa continuidade;
- o estado mental e o resultado da última ação ainda convivem perto demais no
  arquivo principal, mesmo já estando conceitualmente separados.

---

## 8. Pontos que ainda executam sem contrato forte padronizado

Mesmo com melhora grande, ainda existem retornos baseados em `bool` em vez de
um contrato forte completo:

- `executar_intencao(...)`
- `processar_comandos_imediatos(...)`
- `processar_comando_deterministico(...)`
- vários ramos internos de `roteador_intencao.py`

Isso significa que a intenção já foi parcialmente separada da fala, mas ainda
não totalmente.

---

## 9. Principais hotspots para a próxima fase

### Hotspot A — contexto conversacional

- `_contexto_conversa_natural()`

Hoje ele é um grande hub de dependências do chat.

### Hotspot B — segunda camada de comando

- `processar_comandos_imediatos()`

Já foi enxugado, mas ainda mora no `laylay.py`.

### Hotspot C — resposta final

- `construir_fala_conversa(...)`
- `_falar_falha_contextual(...)`
- `_falar_por_status(...)` dentro de `roteador_intencao.py`

Ainda existem múltiplos lugares decidindo fala.

### Hotspot D — executor real

- `mente_laylay/autonomia/roteador_intencao.py`

Continua muito central e denso.

---

## 10. Conclusão da Fase 0

Hoje, os verdadeiros centros de poder do sistema são:

1. `laylay.py` como orquestrador híbrido;
2. `mente_laylay/autonomia/fluxo_resposta_ia.py` como pré-fluxo conversacional;
3. `mente_laylay/autonomia/coordenador_intencao.py` como coordenador de intenção;
4. `mente_laylay/autonomia/roteador_intencao.py` como executor prático central;
5. `mente_laylay/autonomia/contexto_resposta_ia.py` como montador do prompt contextual;
6. `mente_laylay/personalidade/conversa_natural.py` como núcleo de conversa curta.

Com isso, o próximo passo seguro não é “mover qualquer coisa”.

O próximo passo seguro é extrair o integrador do contexto conversacional e do
retrato mental de chat, reduzindo a quantidade de contexto montado
diretamente no `laylay.py`.
