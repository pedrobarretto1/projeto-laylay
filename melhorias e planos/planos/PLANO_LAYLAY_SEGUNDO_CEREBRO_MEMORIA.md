# PLANO — EVOLUÇÃO DA MEMÓRIA DA LAYLAY PARA UM “SEGUNDO CÉREBRO”

> Documento de planejamento técnico.
>
> Objetivo: evoluir a memória atual da Laylay sem destruir o que já funciona, mantendo `memoria_confiavel` como núcleo de verdade e adicionando, por etapas, memória episódica, consolidação, temporalidade, relações, recuperação contextual e proatividade baseada em memória.
>
> Este plano foi escrito pensando em implementação incremental com Codex/IA programadora, evitando mega-refatorações e mantendo compatibilidade com a arquitetura atual da Laylay.

---

# 1. Visão geral

A Laylay já possui uma base importante de memória.

Ela já é capaz de registrar e recuperar tipos de informação como:

- preferências;
- fatos pessoais;
- identidade;
- correções;
- regras;
- rotinas;
- permissões;
- apelidos;
- favoritos;
- informações confirmadas pelo usuário;
- fatos que não devem ser escolhidos silenciosamente quando há conflito.

Esse comportamento deve ser preservado.

A ideia deste plano NÃO é substituir a memória atual por um sistema completamente novo.

A proposta é transformar o que existe hoje em uma arquitetura em camadas.

A diferença conceitual é a seguinte:

```text
MEMÓRIA ATUAL

usuário fala
    ↓
interpretação
    ↓
extrator
    ↓
memória confiável
    ↓
SQLite
```

A arquitetura desejada passa a ser:

```text
usuário / voz / PC / ações / apps
                ↓
             EPISÓDIO
                ↓
        candidato de memória
                ↓
            CONSOLIDAÇÃO
          ↙       ↓       ↘
    duplicata   mudança   relação
          \       |       /
           ↓      ↓      ↓
          MEMÓRIA CANÔNICA
                │
        ┌───────┼─────────┐
        ↓       ↓         ↓
    entidades  tempo    relações
        └───────┼─────────┘
                ↓
       RECUPERAÇÃO HÍBRIDA
                ↓
        PACOTE DE CONTEXTO
                ↓
               LLM
```

O ponto central da evolução é:

> A Laylay não deve apenas armazenar frases. Ela deve conseguir transformar experiências em conhecimento estruturado, histórico e recuperável.

---

# 2. Princípio fundamental

Existem três conceitos que não devem ser confundidos.

## 2.1. “Aconteceu”

Algo apareceu na conversa ou no ambiente.

Exemplo:

```text
Pedro falou que estava pensando em usar Qwen2.5-Coder no agente programador.
```

Isso é um episódio.

Não significa necessariamente que continua sendo verdade hoje.

---

## 2.2. “Parece importante”

O sistema percebe que aquele episódio pode conter uma informação durável.

Exemplo:

```text
possível decisão de arquitetura:
modelo considerado = Qwen2.5-Coder
```

Isso é apenas um candidato de memória.

Ainda não deve ser tratado como verdade canônica.

---

## 2.3. “É verdade atual”

Depois de passar pelas regras de confiança, consolidação e conflito:

```text
entidade = laylay.agente_programador
atributo = modelo_considerado
valor = Qwen2.5-Coder
status = ativo
```

Isso é memória canônica.

---

# 3. Regra de ouro

A busca semântica NÃO decide o que é verdade.

A rede neural NÃO decide o que é verdade.

O LLM NÃO decide sozinho o que é verdade.

Eles podem responder:

> “Essa informação parece relacionada a X.”

ou:

> “Isso parece ser uma preferência.”

Mas a autoridade final deve continuar sendo a camada confiável.

Fluxo correto:

```text
LLM / neural / heurística
          ↓
    candidato
          ↓
    consolidador
          ↓
 regras de procedência
          ↓
 memória confiável
```

Nunca:

```text
neural previu preferência
          ↓
grava diretamente no banco
```

---

# 4. Objetivo final da arquitetura

A Laylay deve conseguir responder perguntas como:

```text
“como ficou aquela ideia do agente programador?”
```

sem depender da conversa original estar no contexto.

Ela deve conseguir reconstruir algo semelhante a:

```text
Projeto:
Laylay

Subprojeto:
Agente programador

Objetivo:
usar um especialista auxiliar para gerar código

Modelo considerado:
Qwen2.5-Coder 3B

Decisão atual:
o agente não possui autoridade irrestrita para alterar o projeto

Estado:
planejamento

Última atividade:
data X

Histórico:
- ideia criada
- modelo sugerido
- autonomia reduzida
```

Isso representa uma memória organizada por conceito, não apenas por texto.

---

# 5. Estrutura de módulos proposta

Sugestão:

```text
mente_laylay/
└── memoria_mental/
    ├── memoria_confiavel.py
    ├── modelos_memoria.py
    ├── episodios.py
    ├── candidatos_memoria.py
    ├── consolidacao.py
    ├── entidades.py
    ├── relacoes.py
    ├── temporalidade.py
    ├── indice_semantico.py
    ├── recuperacao_contextual.py
    ├── pacote_contexto.py
    ├── importancia.py
    ├── manutencao_memoria.py
    └── diagnostico_memoria.py
```

Não é necessário criar tudo imediatamente.

A ordem recomendada aparece mais abaixo.

---

# 6. Manter `memoria_confiavel.py`

`memoria_confiavel.py` deve continuar sendo o núcleo da memória durável.

Ele já possui conceitos importantes que NÃO devem ser perdidos:

- memória confirmada;
- tipos duráveis;
- preferência;
- fato pessoal;
- correção;
- rotina;
- regra;
- permissão;
- identidade;
- resolução conservadora de conflitos;
- rejeição de ambiguidades;
- proteção contra transformar perguntas em fatos;
- distinção entre declaração explícita e inferência.

A evolução deve ser feita AO REDOR dele.

Não é necessário reescrever essa parte de uma vez.

---

# 7. Novo contrato unificado de memória

Criar um modelo único para representar lembranças duráveis.

Exemplo conceitual:

```python
@dataclass
class MemoryRecord:
    id: str

    tipo: str

    entidade: str | None
    atributo: str | None
    valor: object

    origem_evento_id: str | None
    origem: str

    criado_em: datetime
    atualizado_em: datetime

    valido_desde: datetime | None
    valido_ate: datetime | None

    confianca: float
    importancia: float

    explicitamente_dito: bool
    confirmado_usuario: bool

    status: str

    substitui: str | None
    substituido_por: str | None
```

---

# 8. Estados de uma memória

Estados mínimos:

```text
ativo
substituido
contestado
arquivado
esquecido
```

## ativo

É considerado conhecimento atual.

## substituido

Era verdade anteriormente, mas existe uma versão mais recente.

## contestado

Existem informações incompatíveis e o sistema ainda não possui autoridade para decidir.

## arquivado

Não deve ser usado normalmente no contexto, mas continua disponível no histórico.

## esquecido

Foi explicitamente removido ou marcado para não ser recuperado.

---

# 9. Memória episódica

Criar uma camada separada para eventos.

Tabela/estrutura sugerida:

```text
episodios
```

Modelo:

```python
@dataclass
class Episodio:
    id: str
    timestamp: datetime

    origem: str
    tipo: str

    resumo: str

    texto_usuario: str | None
    texto_laylay: str | None

    contexto: dict

    importancia_inicial: float

    processado_consolidacao: bool
```

Exemplos de origem:

```text
conversa
voz
chrome
aplicativo
modo
iot
ação
erro
receipts
sistema
```

---

# 10. Episódio NÃO é verdade durável

Exemplo:

```json
{
  "tipo": "episodio",
  "origem": "conversa",
  "resumo": "Pedro disse que talvez use o Qwen2.5-Coder no agente programador",
  "processado_consolidacao": false
}
```

O sistema pode lembrar que isso aconteceu sem afirmar:

```text
modelo definitivo = Qwen2.5-Coder
```

Essa separação é fundamental.

---

# 11. Candidatos de memória

Criar uma área intermediária.

Exemplo:

```python
@dataclass
class CandidatoMemoria:
    id: str

    episodio_id: str

    tipo_sugerido: str

    entidade_sugerida: str | None
    atributo_sugerido: str | None
    valor_sugerido: object

    confianca_extracao: float

    motivo: str

    origem_detector: str
```

Exemplos de `origem_detector`:

```text
regex
heuristica
llm
neural_shadow
regra_explicita
ação_confirmada
receipt
```

---

# 12. Consolidador

O novo módulo mais importante deve ser:

```text
consolidacao.py
```

Responsabilidades:

1. receber candidatos;
2. procurar memórias semelhantes;
3. detectar duplicatas;
4. detectar atualização;
5. detectar conflito;
6. detectar informação temporária;
7. decidir se deve criar, atualizar, substituir ou ignorar;
8. preservar histórico;
9. registrar por que a decisão foi tomada.

---

# 13. Fluxo de consolidação

```text
CANDIDATO
    ↓
normalização
    ↓
qual entidade?
    ↓
já existe memória parecida?
    ↓
 ┌─────────────┬──────────────┬─────────────┐
 │ não existe  │ mesmo valor  │ valor novo  │
 ↓             ↓              ↓
criar        reforçar      verificar mudança
                               ↓
                    ┌──────────┴──────────┐
                    ↓                     ↓
              atualização válida       conflito
                    ↓                     ↓
              substituir antiga       contestar
```

---

# 14. Deduplicação

Exemplo:

```text
“eu curto Tim Maia”
“gosto bastante de Tim Maia”
“Tim Maia é um dos artistas que eu mais gosto”
```

Não devem necessariamente criar três memórias independentes.

Pode existir:

```text
entidade: Pedro
atributo: gosto_musical
valor: Tim Maia
```

com evidências associadas:

```text
evidencia_evento_1
evidencia_evento_2
evidencia_evento_3
```

---

# 15. Histórico sem destruir o passado

Nunca simplesmente sobrescrever:

```text
playlist favorita = A
```

por:

```text
playlist favorita = B
```

Melhor:

```text
A
validade:
2026-08-01 → 2026-11-12

B
validade:
2026-11-12 → atual
```

Isso permite respostas temporais.

Exemplos:

```text
“qual minha playlist favorita hoje?”
```

e:

```text
“qual playlist eu mais ouvia em agosto?”
```

---

# 16. Temporalidade

Criar campos:

```text
criado_em
atualizado_em
valido_desde
valido_ate
ultima_confirmacao
```

Opcionalmente:

```text
frequencia_observada
ultima_evidencia
```

---

# 17. Memórias que envelhecem

Nem todo conhecimento possui o mesmo tipo de validade.

Exemplo:

```text
nome do usuário
```

quase permanente.

Enquanto:

```text
playlist mais ouvida
```

pode mudar frequentemente.

Criar uma propriedade:

```text
estabilidade
```

Valores possíveis:

```text
alta
media
baixa
```

ou numérico:

```text
0.0 → 1.0
```

---

# 18. Entidades

Criar uma camada explícita de entidades.

Exemplos:

```text
Pedro
Laylay
Agente programador
Modo Estudo
Qwen2.5-Coder
Projeto Laylay
VS Code
Minecraft
Brisa da Madrugada
```

Tabela:

```text
entidades
```

Campos possíveis:

```text
id
tipo
nome_canonico
aliases
criado_em
ultima_atividade
estado
```

---

# 19. Tipos de entidade

Exemplos:

```text
pessoa
projeto
subprojeto
software
modelo_ia
jogo
playlist
música
dispositivo
modo
ideia
arquivo
serviço
rotina
```

---

# 20. Relações

Criar uma tabela simples:

```text
relacoes
```

Modelo:

```python
@dataclass
class Relacao:
    origem_id: str
    tipo: str
    destino_id: str

    criado_em: datetime
    valido_desde: datetime | None
    valido_ate: datetime | None

    confianca: float
```

Exemplos:

```text
Pedro ─desenvolve→ Laylay

Laylay ─possui→ modo jogo

Agente programador ─pertence_a→ Laylay

Agente programador ─considera_modelo→ Qwen2.5-Coder

Pedro ─gosta_de→ Minecraft
```

---

# 21. Não precisa usar banco de grafos agora

SQLite é suficiente para a primeira versão.

Exemplo:

```sql
CREATE TABLE relacoes (
    origem_id TEXT,
    tipo TEXT,
    destino_id TEXT,
    confianca REAL,
    criado_em TEXT
);
```

Um banco de grafos como Neo4j só deveria ser considerado se o projeto realmente chegar num ponto em que consultas complexas de grafo se tornem frequentes.

Não adicionar tecnologia por moda.

---

# 22. Busca semântica

A busca semântica deve entrar DEPOIS da estrutura de memória estar organizada.

Objetivo:

```text
consulta:
“aquele agente de código que a gente falou”

↓

encontrar semanticamente:
“agente programador”
```

O embedding serve para recuperar candidatos relevantes.

Não deve decidir sozinho a resposta.

---

# 23. Recuperação híbrida

O recuperador deve combinar vários sinais.

Exemplo:

```text
score_final =
    semantica
  + correspondencia_entidade
  + recencia
  + importancia
  + confianca
  + contexto_atual
```

Mais corretamente, com pesos configuráveis:

```python
score = (
    semantic_score * PESO_SEMANTICA
    + entity_score * PESO_ENTIDADE
    + recency_score * PESO_RECENCIA
    + importance_score * PESO_IMPORTANCIA
    + confidence_score * PESO_CONFIANCA
)
```

---

# 24. Recuperação por significado + estrutura

Consulta:

```text
“qual era aquele modelo que a gente pensou pro agente dela?”
```

Pode seguir:

```text
"dela"
  ↓
Laylay

"agente"
  ↓
Agente programador

"modelo"
  ↓
relação considera_modelo
```

Resultado:

```text
Qwen2.5-Coder
```

Nesse caso, nem é necessário depender exclusivamente de embedding.

---

# 25. Pacote de contexto

Criar:

```text
pacote_contexto.py
```

Objetivo:

NÃO jogar centenas de memórias no prompt.

Em vez disso:

```text
consulta
   ↓
recuperador
   ↓
top memórias relevantes
   ↓
contexto compacto
```

Exemplo:

```python
PacoteContexto(
    memorias=[
        ...,
        ...,
        ...
    ],
    episodios=[
        ...
    ],
    entidades=[
        ...
    ]
)
```

---

# 26. Limite de contexto

A memória deve obedecer um orçamento.

Exemplo conceitual:

```text
máximo:
8 memórias duráveis
3 episódios recentes
5 relações
```

Ou orçamento em tokens.

Isso evita:

- prompts enormes;
- memória irrelevante;
- ruído;
- custo desnecessário;
- comportamento inconsistente.

---

# 27. Importância

Criar um sistema separado de importância.

Exemplos de sinais:

```text
declaração explícita do usuário
correção
pedido "lembra disso"
preferência forte
decisão de projeto
evento repetido
fato utilizado frequentemente
```

Exemplo:

```python
importance = 0.95
```

---

# 28. Importância NÃO é confiança

São coisas diferentes.

Exemplo:

```text
“acho que talvez eu compre uma RTX”
```

pode ser:

```text
importancia = 0.8
confianca_como_decisao = 0.3
```

Porque é relevante, mas não está decidido.

---

# 29. Força da evidência

Uma memória pode armazenar múltiplas evidências.

Exemplo:

```text
memoria:
Pedro gosta de Tim Maia
```

evidências:

```text
2026-01: declaração explícita
2026-03: conversa musical
2026-06: playlist
```

Isso pode aumentar confiança sem criar duplicata.

---

# 30. Contradições

Nunca resolver silenciosamente contradições de alto impacto.

Exemplo:

```text
“minha música favorita é X”
```

depois:

```text
“minha música favorita é Y”
```

Se a segunda for claramente uma atualização:

```text
X → substituída
Y → ativa
```

Se houver ambiguidade:

```text
X → contestada
Y → candidata
```

e o sistema evita assumir.

---

# 31. Correções explícitas

Frases como:

```text
“não, na verdade é Y”
```

devem possuir prioridade alta.

O sistema deve armazenar:

```text
origem = correcao_usuario
```

e ligar a memória anterior:

```text
substitui = memory_id_antigo
```

---

# 32. “Sono” / consolidação ociosa

Criar um processo de consolidação executado quando apropriado.

Não é necessário ser literalmente noturno.

Pode rodar quando:

```text
Laylay fica ociosa
sessão termina
aplicação fecha
há N episódios não processados
```

---

# 33. Objetivo da consolidação ociosa

Transformar:

```text
muitos episódios
```

em:

```text
poucas memórias úteis
```

Exemplo:

```text
19:32 modo Estudo
19:33 VS Code
19:33 ChatGPT
19:34 playlist calma
19:34 volume 30%
```

Depois de várias ocorrências:

```text
possível rotina:
modo estudo costuma usar
- VS Code
- ChatGPT
- música calma
- volume ~30
```

Essa informação deve nascer como hipótese/candidato, não como regra automática.

---

# 34. Aprendizado de rotina

O sistema já possui interesse em aprender rotinas.

Essa arquitetura permite fazer isso de forma mais confiável.

Exemplo:

```text
observação recorrente
      ↓
candidato de rotina
      ↓
confiança cresce
      ↓
sugestão ao usuário
      ↓
confirmação
      ↓
memória durável
```

---

# 35. Memória ambiental

A Laylay possui uma vantagem sobre assistentes puramente textuais.

Ela pode observar, dependendo da permissão:

```text
app ativo
aba Chrome
jogo
hora
música
modo
dispositivo
ações executadas
resultado de execução
```

Isso pode gerar episódios úteis.

Mas deve existir um filtro forte.

Não guardar tudo indiscriminadamente.

---

# 36. Receipts como evidência

Receipts de execução podem servir como evidência factual.

Exemplo:

```text
pedido:
abrir VS Code

resultado:
confirmado = true
```

Isso pode gerar:

```text
episódio:
VS Code foi aberto
```

Mas não:

```text
preferência:
Pedro gosta de VS Code
```

A diferença entre ocorrência e preferência deve permanecer rígida.

---

# 37. Integração com a rede neural atual

A rede neural está em desenvolvimento e modo shadow.

Manter separação de autoridade.

Uso permitido:

```text
texto
  ↓
rede neural
  ↓
“provável intenção / ação / categoria”
  ↓
metadado auxiliar
```

Para memória:

```text
texto
  ↓
modelo semântico / LLM
  ↓
“isso parece ser uma decisão”
  ↓
CANDIDATO
```

Nunca gravação direta.

---

# 38. Compartilhar encoder ≠ compartilhar responsabilidade

No futuro, pode ser útil compartilhar um encoder semântico.

Exemplo:

```text
MiniLM
```

poderia ser reutilizado para gerar embeddings.

Mas:

```text
neural/comandos/
```

e:

```text
memoria/semantica/
```

devem continuar módulos independentes.

Um não deve controlar o outro.

---

# 39. OOD da rede neural não deve bloquear a memória

O problema de OOD na rede neural operacional é diferente do problema de recuperação semântica da memória.

Não reutilizar automaticamente:

```text
limiar OOD de comando
```

em:

```text
busca de memória
```

São distribuições e objetivos diferentes.

---

# 40. Banco de dados sugerido

Sem necessidade de abandonar SQLite.

Estrutura possível:

```text
memory_records
episodios
memory_evidence
entidades
relacoes
memory_embeddings
memory_links
```

---

# 41. `memory_records`

Exemplo:

```sql
CREATE TABLE memory_records (
    id TEXT PRIMARY KEY,
    tipo TEXT NOT NULL,

    entidade_id TEXT,
    atributo TEXT,
    valor_json TEXT,

    origem_evento_id TEXT,

    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,

    valido_desde TEXT,
    valido_ate TEXT,

    confianca REAL NOT NULL,
    importancia REAL NOT NULL,

    explicitamente_dito INTEGER NOT NULL,
    confirmado_usuario INTEGER NOT NULL,

    status TEXT NOT NULL,

    substitui TEXT,
    substituido_por TEXT
);
```

---

# 42. `episodios`

```sql
CREATE TABLE episodios (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,

    origem TEXT NOT NULL,
    tipo TEXT NOT NULL,

    resumo TEXT,

    dados_json TEXT,

    importancia_inicial REAL,

    processado_consolidacao INTEGER NOT NULL DEFAULT 0
);
```

---

# 43. `memory_evidence`

```sql
CREATE TABLE memory_evidence (
    memory_id TEXT NOT NULL,
    episodio_id TEXT NOT NULL,
    tipo_evidencia TEXT,
    peso REAL,
    criado_em TEXT NOT NULL
);
```

---

# 44. `entidades`

```sql
CREATE TABLE entidades (
    id TEXT PRIMARY KEY,
    tipo TEXT NOT NULL,
    nome_canonico TEXT NOT NULL,
    aliases_json TEXT,
    criado_em TEXT NOT NULL,
    ultima_atividade TEXT
);
```

---

# 45. `relacoes`

```sql
CREATE TABLE relacoes (
    id TEXT PRIMARY KEY,
    origem_id TEXT NOT NULL,
    tipo TEXT NOT NULL,
    destino_id TEXT NOT NULL,

    confianca REAL NOT NULL,

    valido_desde TEXT,
    valido_ate TEXT,

    criado_em TEXT NOT NULL
);
```

---

# 46. Migração sem quebrar a memória atual

Não migrar tudo de uma vez.

Estratégia:

```text
SQLite atual
   ↓
adapter
   ↓
novo contrato
```

Primeiro criar uma camada adaptadora que consiga representar as memórias antigas no novo modelo.

Só depois considerar migração física.

---

# 47. Compatibilidade

Durante a transição:

```text
memoria_confiavel existente
       ↓
grava formato atual
       ↓
adapter espelha / traduz
       ↓
nova camada de recuperação
```

Depois:

```text
novo armazenamento
       ↓
memoria_confiavel usa novo contrato
```

---

# 48. FASE 0 — Auditoria e proteção

Antes de implementar arquitetura nova:

- localizar todas as funções que gravam memória;
- localizar todas as funções que leem memória;
- listar tabelas SQLite;
- listar contratos implícitos;
- criar testes de regressão;
- congelar comportamento esperado.

Objetivo:

> saber exatamente o que não pode quebrar.

---

# 49. FASE 1 — Contrato unificado

Criar:

```text
modelos_memoria.py
```

Sem alterar ainda o armazenamento real.

Implementar:

```text
MemoryRecord
Episodio
CandidatoMemoria
Entidade
Relacao
```

Criar conversores entre objetos antigos e novos.

---

# 50. FASE 2 — Episódios

Adicionar registro episódico.

Começar pequeno.

Somente:

```text
conversas importantes
ações confirmadas
correções do usuário
decisões explícitas
```

Não guardar todo evento do PC ainda.

---

# 51. FASE 3 — Consolidador mínimo

Primeira versão deve fazer apenas:

```text
duplicata
atualização
contradição
criação
```

Sem embeddings.

Usar:

```text
chave semântica
tipo
entidade
atributo
normalização lexical
```

---

# 52. FASE 4 — Temporalidade

Adicionar:

```text
valido_desde
valido_ate
substitui
substituido_por
```

Testar casos de mudança de preferência.

---

# 53. FASE 5 — Entidades e relações

Começar com domínios de alto valor:

```text
Pedro
Laylay
projetos
subprojetos
apps
modelos IA
jogos
playlists
```

Não tentar modelar o mundo inteiro.

---

# 54. FASE 6 — Recuperador contextual

Criar API:

```python
recuperar_contexto(
    consulta,
    contexto_turno,
    limite=8,
)
```

Inicialmente sem embeddings.

Usar:

```text
chave
entidade
tipo
recência
importância
```

---

# 55. FASE 7 — Índice semântico

Somente depois.

Criar API:

```python
buscar_semanticamente(
    texto,
    limite=20,
)
```

Ela retorna candidatos.

Depois o recuperador confiável reranqueia.

---

# 56. FASE 8 — Pacote de contexto

Criar saída estruturada.

Exemplo:

```python
{
    "memorias_atuais": [...],
    "historico_relevante": [...],
    "entidades": [...],
    "relacoes": [...],
}
```

Essa saída alimenta o prompt.

---

# 57. FASE 9 — Consolidação ociosa

Criar job interno seguro.

O job:

```text
busca episódios não processados
agrupa por assunto
gera candidatos
passa pelo consolidador
marca como processado
```

O job NÃO deve promover memórias frágeis automaticamente.

---

# 58. FASE 10 — Proatividade

Somente depois da memória estar confiável.

Exemplos:

```text
“você não mexe nesse projeto há 3 semanas”
```

```text
“ontem você comentou que precisava terminar isso”
```

```text
“você costuma usar esse modo nesse horário”
```

Tudo deve passar pelas regras de proatividade da Laylay.

---

# 59. API recomendada para leitura

Evitar chamadas genéricas como:

```python
listar_aprendizados_semanticos(limit=300)
```

em fluxos onde existe uma intenção específica.

Preferir APIs direcionadas:

```python
buscar_preferencia(
    categoria="música",
    atributo="favorita",
)
```

ou:

```python
recuperar_memorias(
    consulta="minha música favorita",
    tipos={"preferencia"},
    limite=5,
)
```

---

# 60. API recomendada para escrita

Evitar módulos diferentes gravando diretamente no banco.

Criar um ponto único:

```python
propor_memoria(candidato)
```

Depois:

```text
propor_memoria
      ↓
consolidador
      ↓
memoria_confiavel
      ↓
storage
```

---

# 61. Observabilidade

Toda decisão do consolidador deve ser auditável.

Exemplo:

```json
{
  "candidato_id": "...",
  "acao": "substituir",
  "memoria_anterior": "...",
  "motivo": "correcao_explicita_usuario",
  "confianca": 0.99
}
```

Isso será extremamente útil nos testes caóticos da Laylay.

---

# 62. Diagnóstico

Criar:

```text
diagnostico_memoria.py
```

Funções:

```text
listar memórias ativas
listar conflitos
listar candidatos pendentes
listar entidades órfãs
listar memórias sem evidência
listar relações inválidas
detectar duplicatas
```

---

# 63. Testes essenciais

Criar testes para:

### Duplicata

```text
“gosto de Tim Maia”
“eu curto Tim Maia”
```

Esperado:

```text
1 memória + 2 evidências
```

---

### Atualização

```text
“minha música favorita é X”
“agora minha música favorita é Y”
```

Esperado:

```text
X substituída
Y ativa
```

---

### Pergunta não vira memória

```text
“eu gosto de sertanejo?”
```

Esperado:

```text
nenhuma nova memória
```

---

### Hipótese não vira fato

```text
“talvez eu compre uma GPU nova”
```

Esperado:

```text
episódio/candidato
não fato confirmado
```

---

### Contradição

Duas informações incompatíveis sem correção explícita.

Esperado:

```text
status contestado
```

---

### Histórico temporal

Consultar uma preferência antiga.

Esperado:

retornar valor correspondente à data.

---

# 64. Métricas

Criar métricas específicas.

Exemplos:

```text
duplicatas evitadas
memórias contestadas
memórias substituídas
memórias recuperadas corretamente
memórias irrelevantes injetadas no prompt
candidatos falsamente promovidos
```

---

# 65. Métrica especialmente importante

```text
precision_contexto
```

Pergunta:

> Das memórias enviadas ao LLM, quantas realmente eram relevantes?

Uma memória muito grande com baixa precisão de recuperação pode piorar a Laylay.

---

# 66. Evitar “memória infinita no prompt”

Nunca:

```text
SELECT * FROM memories
```

e despejar no prompt.

A arquitetura deve presumir que o banco pode chegar a:

```text
10 mil
100 mil
1 milhão
```

de eventos.

O prompt continua pequeno.

---

# 67. Memória pessoal e privacidade

Manter a política atual de ignorar arquivos locais de memória no Git.

Memória pessoal deve permanecer fora do repositório.

Versionar:

```text
schemas
migrations
fixtures artificiais
testes
```

Não versionar:

```text
memórias reais
conversas reais
preferências pessoais
embeddings pessoais
```

---

# 68. Dados de teste

Criar fixtures artificiais.

Exemplo:

```text
tests/fixtures/memoria/
```

com personagens e informações falsas.

Nunca depender da memória pessoal real de Pedro para testes automatizados.

---

# 69. Nomes sugeridos

Possível nomenclatura:

```text
episodio
memoria
evidencia
entidade
relacao
candidato
consolidacao
recuperacao
```

Evitar criar dez nomes para o mesmo conceito.

---

# 70. Regra para Codex

Ao implementar:

1. ler o módulo atual por completo;
2. localizar chamadas;
3. localizar testes existentes;
4. criar teste de regressão;
5. implementar a menor mudança;
6. rodar testes focados;
7. rodar regressivos;
8. só então prosseguir.

Não fazer refatoração “porque parece mais bonito”.

---

# 71. O que NÃO fazer agora

Não:

- trocar SQLite por banco vetorial imediatamente;
- instalar Neo4j;
- criar microserviço;
- transformar tudo em embeddings;
- deixar LLM escrever memória diretamente;
- remover `memoria_confiavel`;
- juntar memória com classificador neural operacional;
- apagar histórico quando um fato mudar;
- guardar todos os eventos do computador;
- despejar memória inteira no prompt.

---

# 72. Critério de sucesso da primeira versão

A primeira versão pode ser considerada útil quando a Laylay conseguir:

1. registrar episódios;
2. promover fatos explícitos usando as regras atuais;
3. atualizar uma memória sem destruir a anterior;
4. reconhecer entidades simples;
5. recuperar uma informação antiga por contexto;
6. responder sem precisar da conversa original;
7. explicar de onde aquela memória veio.

---

# 73. Critério de sucesso avançado

Depois:

```text
“como ficou aquela ideia que a gente discutiu meses atrás?”
```

A Laylay deve:

1. identificar projeto/contexto;
2. recuperar entidade;
3. recuperar decisões atuais;
4. recuperar histórico relevante;
5. ignorar informação obsoleta;
6. montar contexto compacto;
7. responder naturalmente.

---

# 74. Resultado esperado

A evolução deve transformar:

```text
memória = lista de fatos
```

em:

```text
memória =
    história
  + conhecimento atual
  + relações
  + tempo
  + evidências
  + recuperação contextual
```

---

# 75. Frase de arquitetura

O princípio que deve guiar toda implementação:

> Episódios registram o que aconteceu.  
> Candidatos registram o que talvez seja importante.  
> A memória confiável decide o que pode ser tratado como verdade.  
> A consolidação organiza mudanças ao longo do tempo.  
> A recuperação escolhe apenas o que importa no momento.

Esse é o caminho para a memória da Laylay deixar de ser apenas armazenamento e começar a funcionar como um verdadeiro segundo cérebro.
