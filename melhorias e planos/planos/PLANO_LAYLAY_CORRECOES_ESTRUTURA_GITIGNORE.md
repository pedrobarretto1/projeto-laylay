# PLANO — CORREÇÕES ESTRUTURAIS DO PROJETO LAYLAY

> Documento de planejamento técnico.
>
> Objetivo: corrigir problemas estruturais encontrados durante a análise do projeto sem transformar isso em uma mega-refatoração. O foco é preservar o comportamento atual, melhorar previsibilidade, proteger testes e reduzir dependências invisíveis.
>
> As correções descritas aqui são separadas da evolução da memória para evitar misturar arquitetura nova com manutenção básica do repositório.

---

# 1. Filosofia desta manutenção

O projeto Laylay já cresceu bastante.

Isso significa que o maior risco agora não é apenas “um bug em uma função”.

Também existem riscos de manutenção:

- teste novo não entrar no Git;
- dependência escondida em dicionário;
- módulo depender de chave mágica;
- artefato local virar comportamento implícito;
- refatoração grande quebrar contratos antigos;
- erro aparecer apenas em fluxo integrado.

A regra para esta fase deve ser:

> Corrigir estrutura aos poucos, com teste de regressão antes de alterar comportamento.

---

# 2. Problema nº 1 — `tests/` no `.gitignore`

Foi encontrado:

```gitignore
tests/
```

Esse é um problema estrutural real.

O repositório possui testes versionados.

Arquivos que já estão rastreados continuam existindo no Git normalmente.

Porém, novos arquivos dentro de `tests/` podem ser ignorados.

Exemplo:

```text
criado:
tests/test_memoria_segundo_cerebro.py

git status
```

Pode não mostrar o novo arquivo.

Isso gera um risco silencioso:

```text
teste foi criado localmente
↓
desenvolvedor acha que ele está no commit
↓
arquivo nunca foi enviado
↓
CI / outro PC / Codex não possuem o teste
```

---

# 3. Correção

Remover:

```gitignore
tests/
```

do `.gitignore`.

---

# 4. Regra desejada

A pasta:

```text
tests/
```

deve ser versionada normalmente.

Somente artefatos gerados dentro dela devem ser ignorados, se necessário.

Exemplos:

```gitignore
tests/**/__pycache__/
tests/**/*.tmp
tests/**/*.log
```

Mas não a pasta inteira.

---

# 5. Problema nº 2 — `.gitignore` ignorando ele mesmo

Foi encontrado:

```gitignore
.gitignore
```

Isso não costuma quebrar o arquivo já rastreado.

Porém é desnecessário.

Pode criar comportamento confuso caso o arquivo deixe de ser rastreado em algum momento.

Remover:

```gitignore
.gitignore
```

---

# 6. Problema nº 3 — `resultados_testes/`

Existe uma intenção parecida com:

```gitignore
resultados_testes/
!resultados_testes/**/terminal.log
```

O objetivo aparente é:

```text
ignorar resultados de teste
mas preservar terminal.log
```

Porém regras de negação do Git podem falhar quando o diretório pai inteiro já está ignorado.

A recomendação é não ignorar a pasta pai dessa forma.

---

# 7. Estratégia recomendada para `resultados_testes/`

Em vez de:

```gitignore
resultados_testes/
```

usar regras específicas.

Exemplo conceitual:

```gitignore
resultados_testes/**/*.json
resultados_testes/**/*.tmp
resultados_testes/**/*.html
resultados_testes/**/*.csv

!resultados_testes/**/terminal.log
```

A lista exata deve ser montada depois de auditar quais artefatos são gerados.

---

# 8. Alternativa

Se praticamente tudo deve ser ignorado, usar:

```gitignore
resultados_testes/*
!resultados_testes/**/
!resultados_testes/**/terminal.log
```

Mas isso deve ser testado com:

```powershell
git check-ignore -v caminho\arquivo
```

antes de ser considerado correto.

---

# 9. Não corrigir `.gitignore` no escuro

Antes da alteração:

```powershell
git ls-files tests
git ls-files resultados_testes
```

Depois:

```powershell
git status
git check-ignore -v tests\novo_teste.py
git check-ignore -v resultados_testes\...\terminal.log
```

Objetivo:

confirmar comportamento real.

---

# 10. Problema nº 4 — dependências implícitas por dicionários

Foi observado na arquitetura um padrão semelhante a:

```python
ns.get("_alguma_coisa_runtime")
ns["_estado_compartilhado_runtime"]
_get(ctx, "resolver_referencia_pessoal")
```

Esse padrão pode ser útil durante refatorações grandes.

Ele reduz acoplamento de importação.

Mas possui um custo:

> a assinatura da função não mostra tudo que ela precisa para funcionar.

---

# 11. Problema causado por dependência invisível

Exemplo:

```python
def processar(ctx):
    memoria = ctx.get("memoria")
    resolver = ctx.get("resolver")
    estado = ctx.get("_estado_runtime")
```

Quem lê:

```python
processar(ctx)
```

não sabe quais chaves são obrigatórias.

Erros comuns:

```text
None inesperado
KeyError
fluxo funciona num lugar e quebra em outro
teste precisa montar dict gigante
nome de chave muda silenciosamente
```

---

# 12. Não fazer mega-refatoração

Não converter o projeto inteiro para classes agora.

Isso seria perigoso.

A estratégia deve ser incremental.

---

# 13. Criar contratos para módulos novos

Todo módulo novo deve evitar depender de dezenas de chaves mágicas.

Usar:

```python
@dataclass
class ContextoMemoria:
    memoria: MemoriaSQLite
    estado: EstadoCompartilhado
    relogio: Relogio
```

ou:

```python
class MemoriaPort(Protocol):
    ...
```

---

# 14. `Protocol` pode ser melhor em alguns casos

Exemplo:

```python
from typing import Protocol

class MemoriaRepository(Protocol):
    def listar_aprendizados_semanticos(self, limit: int):
        ...
```

Isso permite que:

```text
SQLite
mock
fake de teste
adapter
```

implementem o mesmo contrato.

---

# 15. Adapter para legado

Caso o runtime atual forneça um dicionário:

```python
class ContextoMemoriaAdapter:
    def __init__(self, ns):
        self.memoria = ns["_memoria"]
        self.estado = ns["_estado"]
```

Assim o novo módulo recebe:

```python
ContextoMemoria
```

sem exigir que o sistema inteiro seja alterado.

---

# 16. Regra de migração

```text
legado com dict
      ↓
adapter
      ↓
contrato tipado
      ↓
módulo novo
```

Não:

```text
alterar todos os módulos do projeto de uma vez
```

---

# 17. Problema nº 5 — armazenamento local ignorado

O `.gitignore` ignora:

```text
*.db
*.sqlite
*.sqlite3
```

Isso é correto para memória pessoal.

Porém existe uma consequência:

migrações e schemas precisam estar versionados separadamente.

---

# 18. Regra para SQLite

Não versionar:

```text
memoria_real.sqlite
dados_pessoais.db
```

Versionar:

```text
schema.sql
migrations/
fixtures artificiais
```

---

# 19. Estrutura sugerida

```text
mente_laylay/
└── storage/
    ├── schema/
    │   └── memoria.sql
    └── migrations/
        ├── 0001_base.sql
        ├── 0002_temporalidade.sql
        └── ...
```

Ou migrações Python.

---

# 20. Benefício

Dois PCs diferentes conseguem criar o mesmo banco a partir do código.

Isso também ajuda:

- testes;
- CI;
- Codex;
- instalação limpa;
- rollback;
- depuração.

---

# 21. Problema nº 6 — testes precisam ser tratados como patrimônio do projeto

A Laylay depende fortemente de comportamento integrado.

Portanto os testes não devem ser tratados como artefato descartável.

Separar:

```text
tests/
```

de:

```text
resultados_testes/
```

---

# 22. Regra

```text
tests/
→ código de teste
→ versionado

resultados_testes/
→ saída de execução
→ normalmente não versionada
```

Exceções:

```text
fixtures
baselines congelados
logs canônicos explicitamente escolhidos
```

---

# 23. Estrutura recomendada

```text
tests/
├── unit/
├── integration/
├── regression/
├── fixtures/
└── frozen/
```

Não é necessário mover tudo imediatamente.

Essa é uma direção futura.

---

# 24. Frozen / challenge

Como o projeto já usa conjuntos congelados na área neural, preservar uma regra forte:

```text
dados frozen versionados
```

não devem ser misturados com:

```text
resultados de execução locais
```

---

# 25. Problema nº 7 — nomes de arquivo e artefatos históricos

Projetos longos acumulam arquivos como:

```text
teste2.py
teste3_6.py
final2.py
backup_novo.py
```

Nem todo arquivo assim precisa ser removido.

Alguns podem representar provas importantes.

A recomendação é classificar.

---

# 26. Categorias

### Código canônico

Usado pelo runtime.

### Teste automatizado

Deve ficar em `tests/`.

### Experimento

Pode ficar em:

```text
experiments/
```

### Ferramenta de diagnóstico

Pode ficar em:

```text
tools/
```

### Histórico morto

Pode ser removido depois de confirmar que não possui valor.

---

# 27. Nunca apagar experimento sem entender a função

Antes:

```powershell
git grep "nome_do_arquivo"
```

e verificar:

- imports;
- documentação;
- comandos manuais;
- dependências;
- referências em handoff.

---

# 28. Problema nº 8 — logging e observabilidade

A Laylay possui muitos fluxos de execução.

Quando um módulo depende de estado implícito, logs ajudam a localizar divergência.

A recomendação é criar logs estruturados em áreas críticas.

---

# 29. Exemplo

```python
logger.info(
    "memory_resolution",
    extra={
        "query": referencia,
        "category": categoria,
        "candidate_count": len(candidatos),
        "resolved": escolhido is not None,
    }
)
```

Sem registrar conteúdo sensível quando não for necessário.

---

# 30. IDs de correlação

Fluxos complexos podem receber:

```text
turn_id
action_id
memory_event_id
```

Assim:

```text
usuário
↓
interpretação
↓
ação
↓
receipt
↓
memória
```

pode ser reconstruído.

---

# 31. Problema nº 9 — exceções silenciosas

Em áreas como memória, padrões como:

```python
try:
    ...
except Exception:
    return None
```

podem ser úteis para não quebrar o assistente.

Mas também escondem bugs.

---

# 32. Estratégia

Manter fail-safe no runtime.

Porém registrar diagnóstico.

Exemplo:

```python
try:
    ...
except Exception:
    logger.exception("falha_ao_resolver_memoria")
    return None
```

---

# 33. Runtime resiliente + diagnóstico forte

Essa combinação é ideal para a Laylay.

```text
usuário não perde a sessão
```

e:

```text
desenvolvedor ainda consegue descobrir o bug
```

---

# 34. Problema nº 10 — contratos de retorno

Funções antigas podem retornar:

```text
None
dict
bool
string
```

dependendo do caminho.

Isso aumenta complexidade.

Para módulos novos, usar retornos estáveis.

---

# 35. Exemplo

```python
@dataclass
class ResultadoResolucao:
    encontrado: bool
    valor: str | None
    motivo: str
    confianca: float
```

Em vez de:

```text
dict ou None
```

quando for possível.

---

# 36. Não mudar contratos antigos sem necessidade

Se uma função pública existente retorna `dict | None`, não alterar imediatamente.

Criar wrapper:

```python
resolver_v2(...)
```

ou adapter.

Depois migrar chamadas.

---

# 37. Problema nº 11 — configuração espalhada

O projeto já iniciou uma boa refatoração de preferências/configuração.

Continuar essa direção.

Separar claramente:

```text
configuração do sistema
preferência do usuário
estado runtime
segredo
```

---

# 38. Quatro categorias

### Configuração estática

Exemplo:

```text
porta websocket
timeout
caminho padrão
```

### Preferência do usuário

Exemplo:

```text
cidade
playlists
comportamento desejado
```

### Estado runtime

Exemplo:

```text
app atual
modo ativo
turno atual
```

### Segredo

Exemplo:

```text
token
senha
API key
```

---

# 39. Não misturar

Evitar:

```python
CONFIG = {
    "cidade": ...,
    "api_key": ...,
    "app_ativo": ...
}
```

---

# 40. Problema nº 12 — imports opcionais

A área neural já adota carregamento tardio para algumas dependências experimentais.

Esse padrão é bom e deve ser preservado.

Dependência opcional não deve quebrar o runtime principal.

---

# 41. Regra

```text
feature não usada
↓
dependência opcional não é importada
```

---

# 42. Dependências

Criar, se ainda não existir, grupos claros:

```text
requirements-core.txt
requirements-neural.txt
requirements-dev.txt
```

ou extras no `pyproject.toml`.

Não precisa ser feito agora se o projeto ainda não usa essa estrutura.

Mas deve ser considerado.

---

# 43. Problema nº 13 — comportamento neural incompleto

A parte neural ainda está em desenvolvimento.

Isso NÃO deve ser classificado automaticamente como defeito.

Separar sempre:

```text
experimental/incompleto por projeto
```

de:

```text
bug estrutural
```

---

# 44. Regra de análise

Toda descoberta neural deve receber uma classificação:

```text
EXPECTED_EXPERIMENTAL
BUG
RISK
TODO
```

Isso evita abrir issue para algo que conscientemente ainda está em shadow.

---

# 45. Proteção do shadow

Manter:

```text
autoriza_execucao=false
```

como regra padrão enquanto os gates não forem aprovados.

Nenhuma refatoração estrutural deve acidentalmente transformar observação em autoridade.

---

# 46. Problema nº 14 — autoridade deve permanecer explícita

Na Laylay existem várias fontes de informação:

```text
LLM
neural
heurística
receipt
memória
extensão Chrome
sistema operacional
usuário
```

Nunca misturar “previsão” com “confirmação”.

---

# 47. Modelo mental

```text
previu
observou
executou
confirmou
```

são estados diferentes.

Exemplo:

```text
neural:
previu OPEN_APP

runtime:
tentou OPEN_APP

Windows:
processo apareceu

receipt:
confirmado
```

Somente a última evidência pode afirmar sucesso real.

---

# 48. Contratos por autoridade

Pode ser útil definir:

```python
class EvidenceLevel(Enum):
    PREDICTED = ...
    INFERRED = ...
    OBSERVED = ...
    CONFIRMED = ...
```

Não precisa ser aplicado ao projeto inteiro imediatamente.

Pode começar em módulos novos.

---

# 49. Problema nº 15 — dependência circular futura

À medida que memória, neural, runtime e proatividade crescerem, aumenta o risco:

```text
memória importa neural
neural importa runtime
runtime importa memória
```

Evitar.

---

# 50. Arquitetura recomendada

```text
domínio
↑
interfaces
↑
infraestrutura
```

Exemplo:

```text
memoria/core/
```

não importa:

```text
laylay2.5.py
```

O runtime é quem injeta dependências.

---

# 51. Regra

Módulo de baixo nível não deve importar o orquestrador principal.

Se precisar de comportamento externo:

```text
Protocol
callback
adapter
```

---

# 52. Problema nº 16 — arquivo principal como service locator

Projetos grandes frequentemente passam a usar o arquivo principal como lugar onde tudo vive.

Isso cria dependência implícita.

A solução NÃO é apagar o arquivo principal.

A solução é fazê-lo virar gradualmente:

```text
composition root
```

---

# 53. Composition root

Responsabilidade:

```text
criar serviços
injetar dependências
iniciar runtime
```

Não concentrar regras de domínio.

---

# 54. Exemplo

```python
memoria = MemoriaSQLite(...)
recuperador = Recuperador(memoria)
neural = NeuralShadow(...)
runtime = Runtime(
    memoria=memoria,
    recuperador=recuperador,
    neural=neural,
)
```

---

# 55. Migração lenta

Cada nova feature deve nascer já com esse estilo.

O legado pode continuar usando namespace/dict.

A proporção de código estruturado aumenta naturalmente.

---

# 56. Problema nº 17 — testes de contrato

Para módulos que dependem de adapters, criar testes de contrato.

Exemplo:

```text
MemoriaRepository
```

deve possuir testes que rodem contra:

```text
fake
SQLite
```

---

# 57. Benefício

Evita descobrir meses depois que:

```text
fake de teste
```

e:

```text
implementação real
```

possuem comportamentos diferentes.

---

# 58. Problema nº 18 — migrações de banco

Quando a memória ganhar novas colunas, não usar lógica improvisada espalhada.

Criar versão de schema.

Exemplo:

```text
schema_version = 3
```

---

# 59. Migração

```text
v1
↓
v2 adiciona temporalidade
↓
v3 adiciona entidades
```

Cada migração deve ser:

```text
determinística
idempotente quando possível
testada
```

---

# 60. Backup antes de migration real

Banco pessoal deve ser copiado antes de migração.

Exemplo:

```text
memoria.sqlite
↓
memoria.sqlite.backup-2026-09-04
```

Backups continuam ignorados pelo Git.

---

# 61. Problema nº 19 — arquivos gerados e artefatos

O `.gitignore` deve possuir categorias claras.

Sugestão de organização:

```gitignore
# dependencies
# build
# runtime state
# logs
# test outputs
# secrets
# local memory
# models
# IDE
# OS
```

Isso torna manutenção mais simples.

---

# 62. Exemplo de `.gitignore` reorganizado

IMPORTANTE:

isso é apenas modelo.

Deve ser ajustado ao repositório real antes do commit.

```gitignore
# -----------------------------
# Dependencies
# -----------------------------
node_modules/
.venv*/
venv*/

# -----------------------------
# Build
# -----------------------------
dist/
build/
*.egg-info/

# -----------------------------
# Python cache
# -----------------------------
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/

# -----------------------------
# Logs
# -----------------------------
*.log

# -----------------------------
# Test outputs
# -----------------------------
resultados_testes/**/*.json
resultados_testes/**/*.csv
resultados_testes/**/*.html

# Preserved canonical logs
!resultados_testes/**/terminal.log

# -----------------------------
# Databases / personal memory
# -----------------------------
*.db
*.sqlite
*.sqlite3
memoria/
contexto.txt
contexto-*.txt

# -----------------------------
# Secrets
# -----------------------------
.env
.env.*
!.env.example
*.pem
*.key
credentials*.json
token*.json

# -----------------------------
# Models
# -----------------------------
*.gguf
*.onnx
*.safetensors
*.pt
*.pth

# -----------------------------
# IDE
# -----------------------------
.vscode/
.idea/

# -----------------------------
# OS
# -----------------------------
.DS_Store
Thumbs.db
```

Novamente:

não substituir o `.gitignore` atual automaticamente por isso.

Primeiro auditar.

---

# 63. Regra específica para testes

NÃO deve existir:

```gitignore
tests/
```

a menos que `tests/` seja realmente uma pasta de output, o que não é o caso atual.

---

# 64. Checklist de correção do `.gitignore`

1. remover `tests/`;
2. remover `.gitignore`;
3. revisar `resultados_testes/`;
4. testar exceção de `terminal.log`;
5. conferir arquivos sensíveis;
6. conferir modelos locais;
7. conferir memória pessoal;
8. rodar `git status`;
9. rodar `git check-ignore`;
10. garantir que nenhum segredo aparece como untracked.

---

# 65. Teste de segurança após editar `.gitignore`

Usar:

```powershell
git status --ignored
```

e revisar cuidadosamente.

Especialmente:

```text
.env
credenciais
memoria
tokens
modelos
áudios pessoais
```

---

# 66. Nunca usar `git add .` imediatamente após grande mudança no `.gitignore`

Primeiro:

```powershell
git status
```

Revisar.

Depois adicionar seletivamente.

Exemplo:

```powershell
git add .gitignore
git add tests/novo_teste.py
```

Isso reduz risco de subir credencial ou memória pessoal.

---

# 67. Plano de execução estrutural

## FASE A — Git hygiene

- corrigir `.gitignore`;
- testar regras;
- conferir arquivos ignorados;
- garantir versionamento de novos testes.

---

# 68. FASE B — inventário de dependências implícitas

Pesquisar padrões:

```text
ns.get(
ctx.get(
_get(ctx
["_...runtime"]
```

Gerar uma lista.

Não corrigir tudo.

Classificar por módulo.

---

# 69. FASE C — contratos para módulos novos

Criar:

```text
Protocol
dataclass
adapter
```

especialmente para:

```text
memória
runtime
estado
relógio
ações
```

---

# 70. FASE D — logging de exceções silenciosas

Prioridade:

```text
memória
autoridade
ação
receipts
neural
```

Manter fallback.

Adicionar diagnóstico.

---

# 71. FASE E — storage versionado

Criar:

```text
schema
migrations
fixtures
```

Sem versionar banco pessoal.

---

# 72. FASE F — organização gradual

Somente depois:

```text
experiments/
tools/
tests/
```

Não mover arquivos por estética.

Mover quando houver benefício concreto.

---

# 73. Regra para Codex

Ao corrigir estrutura:

```text
NÃO:
“refatore o projeto para clean architecture”
```

Isso é amplo demais.

Preferir:

```text
“localize todas as chamadas deste módulo, crie um contrato tipado sem alterar o comportamento externo, adicione adapter para o namespace atual, rode os testes X/Y/Z e mostre qualquer incompatibilidade”
```

---

# 74. Prompt recomendado para Codex — `.gitignore`

```text
Analise o `.gitignore` atual antes de alterar.

Objetivos:
1. novos arquivos em `tests/` precisam ser versionáveis;
2. memória pessoal, bancos SQLite, modelos, áudios e segredos continuam ignorados;
3. revisar a exceção de `resultados_testes/**/terminal.log`;
4. remover regras redundantes ou perigosas apenas quando houver prova;
5. não adicionar nenhum arquivo sensível ao Git.

Antes do patch:
- execute `git ls-files tests`;
- execute `git check-ignore -v` em exemplos relevantes.

Depois do patch:
- execute novamente os comandos;
- rode `git status --ignored`;
- descreva exatamente o comportamento que mudou.

Não faça outras refatorações.
```

---

# 75. Prompt recomendado para Codex — contexto tipado

```text
Escolha apenas um módulo novo ou um módulo de memória de baixo risco.

Objetivo:
reduzir dependência de chaves mágicas de `ctx/ns` sem alterar o runtime global.

Etapas:
1. identifique todas as chaves lidas pelo módulo;
2. crie um `dataclass` ou `Protocol` representando somente essas dependências;
3. crie um adapter para o namespace atual;
4. preserve a API externa;
5. adicione testes;
6. rode regressivos focados.

Não migre outros módulos no mesmo patch.
```

---

# 76. Prompt recomendado para Codex — exceções silenciosas

```text
Audite somente o módulo informado.

Localize blocos:
`except Exception: return None`
ou equivalentes.

Não remova o comportamento fail-safe.

Adicione logging diagnóstico sem expor segredos ou conteúdo pessoal desnecessário.

Crie teste comprovando:
1. a exceção não derruba o runtime;
2. o caminho de erro continua retornando o mesmo contrato;
3. a falha fica observável.

Não altere regras de negócio.
```

---

# 77. Critério de sucesso

A fase estrutural será bem-sucedida quando:

- novos testes aparecem no Git;
- artefatos locais continuam protegidos;
- memória pessoal continua fora do repositório;
- módulos novos possuem dependências explícitas;
- exceções críticas ficam observáveis;
- banco possui schema/migração reproduzível;
- nenhuma alteração muda autoridade operacional;
- regressivos continuam verdes.

---

# 78. O que NÃO fazer

Não:

- reescrever toda a Laylay;
- trocar arquitetura inteira;
- mover centenas de arquivos;
- converter tudo para classe;
- remover fallbacks sem testes;
- misturar correção estrutural com feature nova;
- mudar a rede neural junto com `.gitignore`;
- alterar autoridade de execução;
- adicionar banco pessoal ao Git;
- versionar modelos locais grandes sem decisão explícita.

---

# 79. Ordem recomendada

```text
1. `.gitignore`
2. proteção de testes
3. observabilidade
4. contratos novos
5. adapters
6. migrations
7. organização de pastas
8. refatorações maiores apenas se ainda forem necessárias
```

---

# 80. Princípio final

A Laylay já passou da fase em que “funciona” é o único critério.

Agora também importa:

```text
consigo entender?
consigo testar?
consigo reproduzir?
consigo saber por que falhou?
consigo mudar uma parte sem quebrar outra?
```

A manutenção estrutural deve aumentar essas respostas positivas sem tirar a característica mais importante do projeto:

> continuar funcionando enquanto evolui.
