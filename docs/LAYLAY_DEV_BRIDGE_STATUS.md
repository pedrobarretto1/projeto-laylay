# Laylay Dev Bridge — estado funcional

Atualizado em 2026-09-22.

## Estado atual

- LaylayDevBridge para Windows: **v0.5.0**
- Relay Railway: **v0.4.0**
- Relay publico: `https://relay-production-e5a6.up.railway.app`
- Polling do agente: ~3 segundos
- MCP local do EXE: `http://127.0.0.1:8766/mcp`
- MCP publico experimental do Relay: `/mcp`
- Transporte utilizavel pelo ChatGPT atual: GitHub Issue criptografado -> GitHub Actions -> Railway -> EXE

## Caminho funcional sem Desktop Commander

```
ChatGPT
  |
  | cria issue com envelope criptografado
  v
GitHub Issues
  |
  | GitHub Actions envia somente o numero do issue
  v
Railway Relay
  |
  | valida autor + idade do issue
  | descriptografa envelope
  | coloca comando na fila
  v
LaylayDevBridge.exe
  |
  | polling autenticado
  | executa somente tools permitidas
  | workspace sandbox
  v
PC autorizado
  |
  | receipt
  v
Railway logs privados
  |
  v
ChatGPT
```

O Desktop Commander pode continuar sendo usado para desenvolvimento e manutencao,
mas nao e necessario para transportar os comandos desse caminho.

## Criptografia do comando

Protocolo externo:

`laylay-bridge-encrypted-v1`

- X25519 para acordo de chave.
- HKDF-SHA256 para derivacao.
- AES-256-GCM para confidencialidade e autenticidade.
- A chave publica fica disponivel em `GET /command-key`.
- A chave privada e derivada do segredo interno do Relay e nao e publicada.
- O GitHub publico recebe apenas ciphertext.

O Relay aceita o issue apenas quando:

1. O titulo comeca com `[LAYLAY-BRIDGE-ENC]`.
2. O issue esta aberto.
3. O autor e `pedrobarretto1`.
4. O issue foi criado dentro da janela de tempo permitida.
5. O envelope descriptografa corretamente.
6. O comando interno usa o protocolo `laylay-bridge-command-v1`.
7. A action esta na allowlist.

## Actions atualmente permitidas

- `ping`
- `system_info`
- `list_files`
- `read_text`
- `write_text`
- `run_readonly`

`run_readonly` continua limitado pela allowlist do EXE.

## Protecoes locais

- Workspace restrito.
- `../` e caminhos fora do workspace sao bloqueados.
- Comandos remotos EXE <-> Relay exigem token.
- Receipts pendentes sao persistidos localmente antes do POST.
- Request IDs evitam repeticao acidental.
- O Relay mantem resultados fora do GitHub publico.

## GitHub Actions

Workflow:

`.github/workflows/laylay-bridge-dispatch.yml`

Ao abrir um issue de comando criptografado:

1. O workflow chama `POST /github/issue/<numero>`.
2. O Relay busca o issue diretamente na API do GitHub.
3. O Relay valida autor e envelope.
4. Depois de um despacho aceito, o workflow fecha o issue automaticamente.

Nenhum segredo do Bridge e salvo no GitHub Actions.

## Testes confirmados

### Relay direto
- Ping direto Relay -> EXE -> receipt: OK.
- Tempo observado no primeiro teste v0.5.0: ~3,1 s.

### Seguranca
- Requisicao sem token: HTTP 401.
- Escrita dentro do workspace: OK.
- Escrita usando `../`: bloqueada.
- Arquivo externo nao foi criado.

### MCP publico
- Sem Bearer: HTTP 401.
- Inicializacao MCP: OK.
- 7 tools publicadas.
- `bridge_devices`: notebook detectado online.
- `bridge_ping`: OK.

### GitHub criptografado, sem Desktop Commander no transporte
- Ping criptografado: OK.
- `write_text`: OK.
- `read_text`: OK.
- Auto-close do issue: OK.

Arquivo criado no teste:
`commander_free_v1.txt`

Conteudo lido de volta pelo Bridge:
`Arquivo criado pelo LaylayDevBridge via GitHub criptografado + Railway, sem o Desktop Commander transportar o comando.`

## Limitacao atual

O maior atraso desse caminho vem da inicializacao do GitHub Actions.
Depois que o Relay recebe o issue, o EXE normalmente pega o comando em poucos segundos.

Um webhook direto GitHub -> Railway reduziria essa latencia, mas o conector GitHub
disponivel no ChatGPT nao oferece criacao de repository webhooks no momento.

## Proximo ponto recomendado

Adicionar identidade e credencial **por dispositivo**, em vez de todos os PCs
compartilharem a mesma credencial interna do Bridge.

Objetivo futuro:

```
PC novo
 -> gera device_id + segredo proprio
 -> pareamento autorizado
 -> Relay registra device
 -> cada PC pode ser revogado individualmente
```

Isso e o passo mais importante antes de tratar o EXE como instalavel em qualquer PC.
