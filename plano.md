# Plano — Consciência de capacidades e identidade da Laylay

## Objetivo

Corrigir a conversa observada em `teste.md` sem transformar a Laylay em um
conjunto de frases decoradas. Perguntas, hipóteses e comandos devem compartilhar
a mesma leitura de linguagem natural, mas somente um pedido direto pode chegar
a um executor. As respostas sobre a própria Laylay devem vir do catálogo vivo
de habilidades e manter sua personalidade, sem expor nomes internos do código.

## Invariáveis

- Uma pergunta ou hipótese nunca autoriza execução.
- Uma resposta sobre capacidade consulta o catálogo vivo e sua disponibilidade.
- A Laylay não pode se descrever como “apenas um chatbot” quando possui
  habilidades locais disponíveis.
- Termos como `cliente de rede`, `porteiro`, `intent` e `executor` ficam nos
  logs, não na conversa cotidiana.
- Falha da LLM não pode transformar pergunta em comando nem produzir uma falsa
  confirmação.
- As alterações atuais do usuário na interface, animações e música serão
  preservadas.

## P1 — Classificação e catálogo vivo

Status: **em execução**

- [ ] Reconhecer perguntas gerais como “quais suas habilidades?”.
- [ ] Reconhecer hipóteses naturais como “se eu falar para você criar um
  arquivo, você vai criar?”.
- [ ] Responder perguntas gerais a partir dos domínios realmente disponíveis.
- [ ] Criar respostas naturais específicas para criação de arquivos e controle
  local do computador.
- [ ] Garantir que a porta prioritária consuma essas perguntas antes da LLM e
  não publique comandos.
- [ ] Bloquear o fallback “não executei nem confirmei” em turnos de capacidade,
  hipótese e pergunta.

## P2 — Identidade operacional coerente

Status: **planejada**

- [ ] Entender `seu código`, `sua memória`, `sua voz` e `suas habilidades` como
  referências à própria Laylay.
- [ ] Levar a identidade operacional e o catálogo relevante ao prompt normal e
  ao prompt rápido.
- [ ] Rejeitar contradições como “não estou no seu PC”, “sou só um chatbot” e
  “só consigo conversar” quando o catálogo vivo provar o contrário.
- [ ] Reparar a fala de forma natural e curta, sem acrescentar execução.

## P3 — Naturalidade e variedade segura

Status: **planejada**

- [ ] Separar fatos canônicos de capacidade da redação final.
- [ ] Permitir variação de tom compatível com a personalidade sem alterar
  disponibilidade, limites ou autorização.
- [ ] Remover linguagem de arquitetura interna das respostas existentes.
- [ ] Manter um fallback local natural para timeout ou JSON inválido.

## P4 — Idempotência do Terminal

Status: **planejada**

- [ ] Confirmar no protocolo se as respostas duplicadas vieram de dois envios.
- [ ] Bloquear somente duplo clique acidental dentro de uma janela curta.
- [ ] Preservar repetição deliberada e o botão de tentar novamente.
- [ ] Garantir um recibo, um pensamento e uma resposta por ID aceito.

## Validação

### Conversa e capacidade

1. `quais suas habilidades?`
2. `o que você consegue fazer no meu PC?`
3. `você mexe no meu computador?`
4. `se eu falar para você criar um arquivo, você vai criar?`
5. `você consegue criar um arquivo?`
6. `cria um arquivo chamado teste.txt`
7. `não cria arquivo nenhum`
8. repetir os casos com a habilidade citada indisponível.
9. repetir com a LLM em timeout.

### Identidade e continuidade

1. `estou mexendo no seu código`
2. `por isso você é complicada`
3. `então o que você faz por aqui?`
4. confirmar que a resposta usa primeira pessoa e não nega capacidades reais.

### Automatização

```powershell
.\.venv314\Scripts\python.exe -m pytest tests\test_regressao_consciencia_capacidades.py -q
.\.venv314\Scripts\python.exe -m pytest tests\test_mapa_habilidades.py tests\test_identidade_conversacional.py tests\test_contrato_semantico_fala.py -q
.\.venv314\Scripts\python.exe -m pytest -q
```

Cada fase só será concluída após regressões focadas, compilação, Ruff e teste
real pelo Terminal.
