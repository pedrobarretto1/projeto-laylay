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

## Regras para executar este plano

- [ ] Trabalhar em uma fase por vez.
- [ ] Criar primeiro a regressão que demonstra o problema.
- [ ] Reutilizar os serviços compartilhados; não criar outro estado ou
      interpretador dentro da habilidade.
- [ ] Não alterar memória durável do usuário durante testes automatizados.
- [ ] Não transformar conversa, hipótese, pergunta ou negação em autorização.
- [ ] Não anunciar sucesso sem evidência observada da etapa correspondente.
- [ ] Rodar os testes focados e a suíte completa antes de concluir cada fase.
- [ ] Atualizar este documento somente depois que os critérios de aceite passarem.

## Fase 0 — Criar as invariáveis das conexões

**Prioridade:** P0
**Objetivo:** fazer a suíte detectar automaticamente as divergências encontradas
na auditoria.

### Implementação

- [ ] Criar `tests/test_integridade_conexoes_habilidades.py`.
- [ ] Verificar que toda intent pública, determinística ou produzida pela LLM
      pertence ao catálogo vivo.
- [ ] Verificar que toda intent catalogada possui uma classificação de habilidade.
- [ ] Exigir uma política de continuidade para toda intent: mapeamento canônico
      ou declaração explícita e justificada de que continuidade não se aplica.
- [ ] Verificar que cada capacidade tem exatamente um proprietário executável:
      executor central ou runtime especializado registrado.
- [ ] Verificar que aliases legados apontam para uma intent canônica e não
      aparecem como capacidades independentes incompletas.
- [ ] Exigir metadados de invocação natural, autorização, evidência, limites e
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

- [ ] A regressão falha com o estado atual pelos motivos auditados.
- [ ] Nenhuma intent executável pode ficar invisível para a consciência da Laylay.
- [ ] Nenhuma capacidade fantasma pode ser anunciada como disponível.
- [ ] O teste compara fontes independentes; não pode comparar o mapa apenas com
      o catálogo que o próprio mapa utiliza.

## Fase 1 — Corrigir catálogo, linguagem e segurança do resumo

**Prioridade:** P0
**Dependência:** Fase 0.

### Implementação

- [ ] Registrar `RESUMIR_PAGINA` no domínio do navegador.
- [ ] Definir sua classificação, política de continuidade, dependências, limites
      e evidência de confirmação.
- [ ] Fazer seus resultados alimentarem o mapa vivo e o diagnóstico.
- [ ] Substituir a busca simples por palavras-chave pela arbitragem canônica de
      modalidade e autorização.
- [ ] Bloquear execução para negação, hipótese, sugestão, pergunta instrucional e
      pergunta de capacidade.
- [ ] Preservar o comando direto e suas variantes naturais.
- [ ] Resolver `CONFIRM_INBOX_DELETE`: remover a intent fantasma ou implementar
      proprietário, detector, executor e testes completos.
- [ ] Formalizar `MOVE_ITEM` e `GAME_VISION_CONTINUE` como aliases canônicos ou
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

- [ ] `mapa.consultar("RESUMIR_PAGINA")` retorna capacidade real e contextual.
- [ ] Perguntas sobre a habilidade descrevem acesso, limites e disponibilidade
      atuais sem autorizar execução.
- [ ] Falha de Chrome, conteúdo vazio ou LLM indisponível aparece como falha ou
      resultado parcial, nunca como sucesso inventado.
- [ ] Todos os casos positivos e negativos atravessam o caminho de composição
      usado por `laylay.py`.

## Fase 2 — Unificar contexto, continuidade e ciclo de sessão

**Prioridade:** P0
**Dependência:** Fase 1.

### Implementação

- [ ] Limpar `pendencia_acao_canonica` ao renovar uma sessão.
- [ ] Incluir a pendência canônica no ciclo de expiração global, sem depender de
      uma futura chamada a `obter()`.
- [ ] Migrar `MusicaConversacionalRuntime._sugestao_pendente` para
      `PendenciaAcaoRuntime`.
- [ ] Migrar exclusão e conversão da caixa de entrada de `self._pendencia` para a
      pendência canônica já usada pelas discussões.
- [ ] Substituir a pendência privada da lixeira por uma única referência canônica.
- [ ] Publicar no contexto compartilhado apenas referência sanitizada, hash,
      operação e TTL para resultados temporários do clipboard; nunca o conteúdo
      sensível bruto.
- [ ] Eliminar leituras com `OR` entre estado privado e estado compartilhado.

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

- [ ] Abrir uma confirmação, renovar a sessão e responder `sim` não executa a
      ação antiga.
- [ ] Troca inequívoca de domínio encerra ou suspende a pendência conforme a
      política canônica.
- [ ] Música, caixa, clipboard e lixeira publicam e consomem a mesma instância de
      pendência.
- [ ] Testes não podem escrever diretamente em atributos privados para preparar
      a continuidade.
- [ ] `tenta de novo`, `continua`, `essa também`, `ele` e `ela` resolvem somente
      referências válidas da sessão atual.

## Fase 3 — Unificar aprendizado e interpretação natural

**Prioridade:** P1
**Dependência:** Fase 2.

### Implementação

- [ ] Conectar `AprendizadoRuntime` aos getters e setters do estado compartilhado
      ou absorver seu comportamento no motor de aprendizado canônico.
- [ ] Remover a ilha `_estado_local` usada por rotina e música em produção.
- [ ] Fazer cada domínio enviar aceitação, recusa, correção, repetição e silêncio
      qualificado ao mesmo motor, com origem e confiança.
- [ ] Tornar o classificador compartilhado a única fonte para confirmações e
      recusas curtas.
- [ ] Remover vocabulários particulares de `sim`, `não`, `pode ser`, `isso` e
      `confirmo` dos domínios.
- [ ] Conectar as preferências da central de notificações ao contexto e ao motor
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

- [ ] O snapshot compartilhado contém o aprendizado musical realmente usado pela
      autonomia, com proveniência e confiança.
- [ ] Uma única correção não promove automaticamente uma preferência durável.
- [ ] As mesmas respostas curtas produzem a mesma interpretação em todos os
      domínios quando o contexto é equivalente.
- [ ] `deixa para depois`, `precisa não` e agradecimentos encerram corretamente a
      pendência sem retomar um domínio antigo.

## Fase 4 — Tornar diagnóstico e consciência operacionais

**Prioridade:** P1
**Dependência:** Fases 1 a 3.

### Implementação

- [ ] Ampliar `validar_estrutura()` para conferir continuidade geral, pendências,
      classificador, motor de aprendizado e identidade dos runtimes compartilhados.
- [ ] Integrar ao diagnóstico global: resumo de página, clipboard/investigador,
      caixa de entrada, central de notificações e IoT operacional.
- [ ] Substituir disponibilidade baseada apenas em `callable()` por pré-condições
      reais: configuração, credencial, conexão, serviço e evidência recente.
- [ ] Alinhar `navegador` e `navegador_tipado` numa única fonte de saúde.
- [ ] Derivar a disponibilidade do avatar de preferência, processo e assets reais;
      um domínio com zero intents não pode ficar disponível por cálculo vazio.
- [ ] Fazer falhas e recuperações recentes atualizarem o catálogo sem desligar uma
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

- [ ] Função existente com WebSocket desconectado não aparece como navegador
      plenamente disponível.
- [ ] Credencial ou provedor ausente produz estado degradado ou indisponível.
- [ ] `/diagnostico mente` distingue saúde estrutural de disponibilidade operacional.
- [ ] A Laylay responde naturalmente o que consegue fazer agora e por que uma
      capacidade está limitada.
- [ ] O diagnóstico acusa deliberadamente uma conexão privada ou ausente criada
      por fixture de teste.

## Fase 5 — Completar a orquestração cooperativa

**Prioridade:** P1
**Dependência:** Fases 2 a 4.

### Implementação

- [ ] Publicar caixa de entrada → agenda no quadro cooperativo.
- [ ] Publicar clipboard → pesquisa → LLM no quadro cooperativo.
- [ ] Completar a prova cooperativa da curadoria musical.
- [ ] Garantir que cada etapa mantenha autorização, executor e evidência próprios.
- [ ] Fazer a governança falhar fechada quando o porteiro não estiver conectado.
- [ ] Substituir o rótulo `sombra` ou fazer o modo realmente governar a execução;
      o diagnóstico não pode anunciar sombra enquanto ações reais são executadas.
- [ ] Impedir que uma etapa confirmada transforme uma falha posterior em sucesso
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

- [ ] Caixa → agenda não anuncia lembrete criado quando a agenda falha.
- [ ] Clipboard → pesquisa → LLM identifica claramente falha parcial e preserva
      privacidade do texto copiado.
- [ ] Instanciar governança sem porteiro não autoriza nenhuma etapa.
- [ ] O quadro expõe participantes, dependências, estado, evidência e resultado
      final sem duplicar conteúdo sensível.

## Fase 6 — Fechamento e regressão completa

**Prioridade:** P2
**Dependência:** todas as fases anteriores.

### Definição de pronto por capacidade

- [ ] Contexto temporário compartilhado, mínimo e encerrado corretamente.
- [ ] Memória durável separada do contexto e acompanhada de proveniência.
- [ ] Aprendizado integrado para aceitação, recusa, correção, repetição e silêncio.
- [ ] Linguagem natural interpretada pelo contrato canônico.
- [ ] Continuidade e referências resolvidas pela pendência oficial.
- [ ] Segurança separando conversa, autorização, execução e confirmação observada.
- [ ] Diagnóstico com saúde, falha e resultado verificável.
- [ ] Consciência viva com invocação, autorização, evidência, dependências e limites.
- [ ] Cooperação testada quando houver mais de uma habilidade ou fonte de dados.

### Validação automatizada

Executar, no mínimo:

```powershell
.\.venv314\Scripts\python.exe -m pytest tests\test_integridade_conexoes_habilidades.py -q
.\.venv314\Scripts\python.exe -m pytest tests\test_mapa_habilidades.py tests\test_continuidade_geral.py tests\test_pendencia_acao_canonica.py -q
.\.venv314\Scripts\python.exe -m pytest tests\test_orquestracao_cooperativa.py tests\test_confirmacao_operacional_contrato.py -q
.\.venv314\Scripts\python.exe -m pytest -q
```

### Validação manual final

- [ ] Testar resumo de página positivo, negado, hipotético e instrucional.
- [ ] Abrir uma confirmação, reiniciar a conversa e responder `sim`.
- [ ] Confirmar e recusar ações em música, caixa de entrada, clipboard e lixeira.
- [ ] Desligar ou desconectar Chrome, Gmail e Tuya e conferir mapa e diagnóstico.
- [ ] Testar caixa → lembrete com sucesso e falha deliberada da agenda.
- [ ] Testar investigação do clipboard com pesquisa ou LLM indisponível.
- [ ] Perguntar naturalmente à Laylay o que ela pode fazer em cada domínio.

## Resultado esperado

Ao final, uma habilidade não será considerada pronta apenas porque possui um
detector e um executor. Ela deverá estar ligada à mesma mente, responder em
linguagem natural, continuar o contexto correto, aprender de forma auditável,
respeitar autorização, confirmar somente o observado, aparecer no diagnóstico e
cooperar sem criar atalhos. O catálogo, os testes e o comportamento em execução
deverão descrever a mesma Laylay.
