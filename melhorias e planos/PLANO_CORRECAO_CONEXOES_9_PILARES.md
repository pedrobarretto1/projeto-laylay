# Plano de correção das conexões e dos 9 pilares

Este plano transforma a auditoria estrutural da Laylay em etapas verificáveis.
O objetivo não é reescrever as habilidades, mas fazer todas reutilizarem os
mesmos contratos de contexto, memória, aprendizado, linguagem natural,
continuidade, segurança, diagnóstico, consciência e cooperação definidos em
`AGENTS.md`.

## Linha de base da auditoria

- 72 intents catalogadas em 14 domínios executáveis.
- `avatar` aparece como domínio conversacional, mas possui zero intents.
- 21 intents catalogadas não possuem classificação de habilidade.
- 18 intents catalogadas não aparecem na continuidade canônica.
- `RESUMIR_PAGINA` é executável e somente leitura, mas está fora do catálogo.
- `CONFIRM_INBOX_DELETE` está no catálogo, mas não possui fluxo executável próprio.
- `MOVE_ITEM` e `GAME_VISION_CONTINUE` aparecem em estruturas auxiliares sem
  pertencer ao catálogo executável.
- Suíte de referência: 2.192 testes e 45 subtestes aprovados.

Os testes verdes são a linha de base, não a prova de que as conexões estão
corretas. Uma fase só termina quando os novos testes de integração demonstrarem
os pilares no caminho real da composição.

## Progresso verificado

- 10/08/2026 — Fases 0 e 1 concluídas.
- Catálogo vivo: 73 intents; todas possuem classificação, continuidade,
  proprietário importável, invocação natural, autorização, evidência, limites
  e dependências.
- `MOVE_ITEM` e `GAME_VISION_CONTINUE` ficaram declaradas como aliases internos,
  sem aparecer como capacidades públicas incompletas.
- `RESUMIR_PAGINA` passou a integrar catálogo, mapa vivo, continuidade,
  confirmação por retorno e arbitragem canônica de modalidade.
- Validação da etapa: 2.208 testes e 45 subtestes aprovados.
- 10/08/2026 — Fase 3 concluída: rotina e música usam o estado mental
  compartilhado; confirmações e recusas curtas partem do mesmo classificador;
  feedback contextual e preferências de notificações alimentam o motor
  canônico com origem, confiança e proveniência.
- Validação da Fase 3: 2.218 testes e 45 subtestes aprovados.

## Regras para executar este plano

- [x] Trabalhar em uma fase por vez.
- [x] Criar primeiro a regressão que demonstra o problema.
- [x] Reutilizar os serviços compartilhados; não criar outro estado ou
      interpretador dentro da habilidade.
- [x] Não alterar memória durável do usuário durante testes automatizados.
- [x] Não transformar conversa, hipótese, pergunta ou negação em autorização.
- [x] Não anunciar sucesso sem evidência observada da etapa correspondente.
- [x] Rodar os testes focados e a suíte completa antes de concluir cada fase.
- [x] Atualizar este documento somente depois que os critérios de aceite passarem.

## Fase 0 — Criar as invariáveis das conexões

**Prioridade:** P0
**Objetivo:** fazer a suíte detectar automaticamente as divergências encontradas
na auditoria.

### Implementação

- [x] Criar `tests/test_integridade_conexoes_habilidades.py`.
- [x] Verificar que toda intent pública, determinística ou produzida pela LLM
      pertence ao catálogo vivo.
- [x] Verificar que toda intent catalogada possui uma classificação de habilidade.
- [x] Exigir uma política de continuidade para toda intent: mapeamento canônico
      ou declaração explícita e justificada de que continuidade não se aplica.
- [x] Verificar que cada capacidade tem exatamente um proprietário executável:
      executor central ou runtime especializado registrado.
- [x] Verificar que aliases legados apontam para uma intent canônica e não
      aparecem como capacidades independentes incompletas.
- [x] Exigir metadados de invocação natural, autorização, evidência, limites e
      dependências no contrato vivo de cada capacidade.

### Arquivos principais

- `mente_laylay/especialistas/capacidades.py`
- `mente_laylay/especialistas/mapa_habilidades.py`
- `mente_laylay/autonomia/classificacao_habilidade.py`
- `mente_laylay/memoria_mental/continuidade_geral.py`
- `mente_laylay/cognicao/interpretacao_intencao.py`
- `tests/test_mapa_habilidades.py`
- `tests/test_confirmacao_operacional_contrato.py`

### Critérios de aceite

- [x] A regressão falha com o estado auditado pelos motivos registrados acima.
- [x] Nenhuma intent executável pode ficar invisível para a consciência da Laylay.
- [x] Nenhuma capacidade fantasma pode ser anunciada como disponível.
- [x] O teste compara fontes independentes; não pode comparar o mapa apenas com
      o catálogo que o próprio mapa utiliza.

## Fase 1 — Corrigir catálogo, linguagem e segurança do resumo

**Prioridade:** P0
**Dependência:** Fase 0.

### Implementação

- [x] Registrar `RESUMIR_PAGINA` no domínio do navegador.
- [x] Definir sua classificação, política de continuidade, dependências, limites
      e evidência de confirmação.
- [x] Fazer seus resultados alimentarem o mapa vivo e o diagnóstico.
- [x] Substituir a busca simples por palavras-chave pela arbitragem canônica de
      modalidade e autorização.
- [x] Bloquear execução para negação, hipótese, sugestão, pergunta instrucional e
      pergunta de capacidade.
- [x] Preservar o comando direto e suas variantes naturais.
- [x] Resolver `CONFIRM_INBOX_DELETE`: remover a intent fantasma ou implementar
      proprietário, detector, executor e testes completos.
- [x] Formalizar `MOVE_ITEM` e `GAME_VISION_CONTINUE` como aliases canônicos ou
      retirar as referências órfãs.

### Regressões obrigatórias

Devem executar:

```text
Resume a página atual.
Pode resumir esta página para mim?
Explica o conteúdo da aba atual.
```

Não podem executar:

```text
Não resume a página atual.
Como eu faria para resumir uma página?
Talvez fosse legal resumir esta página.
Você consegue resumir páginas?
```

### Critérios de aceite

- [x] `mapa.consultar("RESUMIR_PAGINA")` retorna capacidade real e contextual.
- [x] Perguntas sobre a habilidade descrevem acesso, limites e disponibilidade
      atuais sem autorizar execução.
- [x] Falha de Chrome, conteúdo vazio ou LLM indisponível aparece como falha ou
      resultado parcial, nunca como sucesso inventado.
- [x] Todos os casos positivos e negativos atravessam o caminho de composição
      usado por `laylay.py`.

## Fase 2 — Unificar contexto, continuidade e ciclo de sessão

**Prioridade:** P0
**Dependência:** Fase 1.

### Implementação

- [x] Limpar `pendencia_acao_canonica` ao renovar uma sessão.
- [x] Incluir a pendência canônica no ciclo de expiração global, sem depender de
      uma futura chamada a `obter()`.
- [x] Migrar `MusicaConversacionalRuntime._sugestao_pendente` para
      `PendenciaAcaoRuntime`.
- [x] Migrar exclusão e conversão da caixa de entrada de `self._pendencia` para a
      pendência canônica já usada pelas discussões.
- [x] Substituir a pendência privada da lixeira por uma única referência canônica.
- [x] Publicar no contexto compartilhado apenas referência sanitizada, hash,
      operação e TTL para resultados temporários do clipboard; nunca o conteúdo
      sensível bruto.
- [x] Eliminar leituras com `OR` entre estado privado e estado compartilhado.

### Arquivos principais

- `mente_laylay/memoria_mental/sessao_conversa.py`
- `mente_laylay/memoria_mental/ciclo_vida_contexto.py`
- `mente_laylay/memoria_mental/pendencia_acao.py`
- `mente_laylay/memoria_mental/musica_conversacional_runtime.py`
- `mente_laylay/especialistas/caixa_entrada_pessoal.py`
- `mente_laylay/especialistas/area_transferencia.py`
- `mente_laylay/arquivos/lixeira_laylay.py`
- `mente_laylay/autonomia/pre_fluxo_contextual.py`
- `mente_laylay/memoria_mental/contexto_compartilhado.py`

### Critérios de aceite

- [x] Abrir uma confirmação, renovar a sessão e responder `sim` não executa a
      ação antiga.
- [x] Troca inequívoca de domínio encerra ou suspende a pendência conforme a
      política canônica.
- [x] Música, caixa, clipboard e lixeira publicam e consomem a mesma instância de
      pendência.
- [x] Testes não podem escrever diretamente em atributos privados para preparar
      a continuidade.
- [x] `tenta de novo`, `continua`, `essa também`, `ele` e `ela` resolvem somente
      referências válidas da sessão atual.

## Fase 3 — Unificar aprendizado e interpretação natural

**Prioridade:** P1
**Dependência:** Fase 2.

### Implementação

- [x] Conectar `AprendizadoRuntime` aos getters e setters do estado compartilhado
      ou absorver seu comportamento no motor de aprendizado canônico.
- [x] Remover a ilha `_estado_local` usada por rotina e música em produção.
- [x] Fazer cada domínio enviar aceitação, recusa, correção, repetição e silêncio
      qualificado ao mesmo motor, com origem e confiança.
- [x] Tornar o classificador compartilhado a única fonte para confirmações e
      recusas curtas.
- [x] Remover vocabulários particulares de `sim`, `não`, `pode ser`, `isso` e
      `confirmo` dos domínios.
- [x] Conectar as preferências da central de notificações ao contexto e ao motor
      de aprendizado, mantendo persistência própria apenas para dados duráveis.

### Arquivos principais

- `mente_laylay/memoria_mental/aprendizado_runtime.py`
- `mente_laylay/memoria_mental/aprendizado_rotina_musica.py`
- `mente_laylay/integracao/adaptadores_aplicacao_runtime.py`
- `mente_laylay/cognicao/modalidade_turno.py`
- `mente_laylay/cognicao/esclarecimento_operacional.py`
- `mente_laylay/autonomia/fluxos_conversa.py`
- `mente_laylay/autonomia/pre_fluxo_contextual.py`
- `mente_laylay/autonomia/central_notificacoes.py`
- `laylay.py`

### Critérios de aceite

- [x] O snapshot compartilhado contém o aprendizado musical realmente usado pela
      autonomia, com proveniência e confiança.
- [x] Uma única correção não promove automaticamente uma preferência durável.
- [x] As mesmas respostas curtas produzem a mesma interpretação em todos os
      domínios quando o contexto é equivalente.
- [x] `deixa para depois`, `precisa não` e agradecimentos encerram corretamente a
      pendência sem retomar um domínio antigo.

## Fase 4 — Tornar diagnóstico e consciência operacionais

**Prioridade:** P1
**Dependência:** Fases 1 a 3.

### Implementação

- [x] Ampliar `validar_estrutura()` para conferir continuidade geral, pendências,
      classificador, motor de aprendizado e identidade dos runtimes compartilhados.
- [x] Integrar ao diagnóstico global: resumo de página, clipboard/investigador,
      caixa de entrada, central de notificações e IoT operacional.
- [x] Substituir disponibilidade baseada apenas em `callable()` por pré-condições
      reais: configuração, credencial, conexão, serviço e evidência recente.
- [x] Alinhar `navegador` e `navegador_tipado` numa única fonte de saúde.
- [x] Derivar a disponibilidade do avatar de preferência, processo e assets reais;
      um domínio com zero intents não pode ficar disponível por cálculo vazio.
- [x] Fazer falhas e recuperações recentes atualizarem o catálogo sem desligar uma
      habilidade inteira por causa de um único alvo inexistente.

### Arquivos principais

- `mente_laylay/memoria_mental/estado_compartilhado_runtime.py`
- `mente_laylay/memoria_mental/diagnostico_mente.py`
- `mente_laylay/memoria_mental/formatacao_diagnostico.py`
- `mente_laylay/especialistas/mapa_habilidades.py`
- `mente_laylay/integracao/adaptadores_aplicacao_runtime.py`
- `mente_laylay/integracao/registro_servicos_aplicacao.py`
- `laylay.py`

### Critérios de aceite

- [x] Função existente com WebSocket desconectado não aparece como navegador
      plenamente disponível.
- [x] Credencial ou provedor ausente produz estado degradado ou indisponível.
- [x] `/diagnostico mente` distingue saúde estrutural de disponibilidade operacional.
- [x] A Laylay responde naturalmente o que consegue fazer agora e por que uma
      capacidade está limitada.
- [x] O diagnóstico acusa deliberadamente uma conexão privada ou ausente criada
      por fixture de teste.

### Validação concluída

- 326 testes focados dos runtimes, contratos e domínios integrados passaram.
- Suíte completa: 2225 testes e 45 subtestes passaram.
- O diagnóstico permanece passivo: nenhuma verificação autoriza ou executa ações.

## Fase 5 — Completar a orquestração cooperativa

**Prioridade:** P1
**Dependência:** Fases 2 a 4.

### Implementação

- [x] Publicar caixa de entrada → agenda no quadro cooperativo.
- [x] Publicar clipboard → pesquisa → LLM no quadro cooperativo.
- [x] Completar a prova cooperativa da curadoria musical.
- [x] Garantir que cada etapa mantenha autorização, executor e evidência próprios.
- [x] Fazer a governança falhar fechada quando o porteiro não estiver conectado.
- [x] Substituir o rótulo `sombra` ou fazer o modo realmente governar a execução;
      o diagnóstico não pode anunciar sombra enquanto ações reais são executadas.
- [x] Impedir que uma etapa confirmada transforme uma falha posterior em sucesso
      completo.

### Arquivos principais

- `mente_laylay/autonomia/quadro_cooperacao.py`
- `mente_laylay/autonomia/governanca_cooperacao.py`
- `mente_laylay/autonomia/orquestracao_cooperativa.py`
- `mente_laylay/integracao/ponte_cooperacao_aplicacao.py`
- `mente_laylay/integracao/ponte_clipboard_aplicacao.py`
- `mente_laylay/especialistas/caixa_entrada_pessoal.py`
- `mente_laylay/cognicao/investigacao_erro.py`
- `laylay.py`

### Critérios de aceite

- [x] Caixa → agenda não anuncia lembrete criado quando a agenda falha.
- [x] Clipboard → pesquisa → LLM identifica claramente falha parcial e preserva
      privacidade do texto copiado.
- [x] Instanciar governança sem porteiro não autoriza nenhuma etapa.
- [x] O quadro expõe participantes, dependências, estado, evidência e resultado
      final sem duplicar conteúdo sensível.

### Validação concluída

- 63 testes focados da orquestração, linguagem natural, investigação e curadoria
  passaram.
- 274 testes e 8 subtestes dos domínios integrados passaram.
- Suíte completa: 2233 testes e 45 subtestes passaram.
- Ruff, compilação dos módulos alterados e `git diff --check` passaram; restaram
  apenas avisos de normalização CRLF já presentes na árvore de trabalho.

## Fase 6 — Fechamento e regressão completa

**Prioridade:** P2
**Dependência:** todas as fases anteriores.

### Definição de pronto por capacidade

- [x] Contexto temporário compartilhado, mínimo e encerrado corretamente.
- [x] Memória durável separada do contexto e acompanhada de proveniência.
- [x] Aprendizado integrado para aceitação, recusa, correção, repetição e silêncio.
- [x] Linguagem natural interpretada pelo contrato canônico.
- [x] Continuidade e referências resolvidas pela pendência oficial.
- [x] Segurança separando conversa, autorização, execução e confirmação observada.
- [x] Diagnóstico com saúde, falha e resultado verificável.
- [x] Consciência viva com invocação, autorização, evidência, dependências e limites.
- [x] Cooperação testada quando houver mais de uma habilidade ou fonte de dados.

### Validação automatizada

Executar, no mínimo:

```powershell
.\.venv314\Scripts\python.exe -m pytest tests\test_integridade_conexoes_habilidades.py -q
.\.venv314\Scripts\python.exe -m pytest tests\test_mapa_habilidades.py tests\test_continuidade_geral.py tests\test_pendencia_acao_canonica.py -q
.\.venv314\Scripts\python.exe -m pytest tests\test_orquestracao_cooperativa.py tests\test_confirmacao_operacional_contrato.py -q
.\.venv314\Scripts\python.exe -m pytest -q
```

### Validação final reproduzível

- [x] Resumo de página positivo, negado, hipotético e instrucional coberto por
      fixtures sem autorizar falsos pedidos.
- [x] Uma confirmação permanece na mente compartilhada ao recriar o runtime da
      conversa e `sim` é consumido pela pendência oficial.
- [x] Aceitação e recusa em música, caixa de entrada, clipboard e lixeira
      cobertas pelos respectivos executores e pendências canônicas.
- [x] Chrome desconectado e provedores/credenciais ausentes de conversa, visão,
      Gmail e IoT simulados sem executar probes nem alterar serviços reais.
- [x] Caixa → lembrete coberto com persistência confirmada e falha deliberada da
      agenda, sem transformar sucesso parcial em conclusão total.
- [x] Investigação do clipboard coberta com pesquisa indisponível, fallback
      factual, porteiro ausente e descarte da referência privada.
- [x] Perguntas naturais cobertas individualmente para música, sistema,
      navegador, visão, agenda, arquivos, email, IoT, conversa, caixa de entrada
      e área de transferência, sem autorização de execução.

### Validação concluída

- Os quatro comandos mínimos desta fase passaram: 15, 43, 46 e 2245 testes,
  respectivamente; a suíte completa também executou 45 subtestes.
- A bateria cruzada das Fases 1 a 6 e dos principais domínios passou com 269
  testes.
- Foram adicionadas 12 regressões finais para recriação da conversa e
  consciência natural por domínio.
- Ruff, compilação e `git diff --check` passaram; permaneceram somente avisos de
  normalização CRLF já existentes na árvore de trabalho.
- As indisponibilidades externas foram simuladas por diagnóstico passivo; nenhum
  dispositivo, conta ou serviço real foi desligado durante a validação.

## Resultado esperado

Ao final, uma habilidade não será considerada pronta apenas porque possui um
detector e um executor. Ela deverá estar ligada à mesma mente, responder em
linguagem natural, continuar o contexto correto, aprender de forma auditável,
respeitar autorização, confirmar somente o observado, aparecer no diagnóstico e
cooperar sem criar atalhos. O catálogo, os testes e o comportamento em execução
deverão descrever a mesma Laylay.
