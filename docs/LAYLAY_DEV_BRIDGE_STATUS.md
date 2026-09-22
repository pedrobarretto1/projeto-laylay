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


---

## Marco v0.8.0 — 22/09/2026

O agente local passou a operar em modo de acesso amplo controlado à máquina, mantendo bloqueios independentes de sistema e credenciais.

### Agente local

Versão ativa: `Laylay Dev Bridge 0.8.0`, executada pelo Python da `.venv313` em CMD visível.

O executável PyInstaller v0.6 foi bloqueado pela política/antivírus do notebook do SENAI; por isso a linha atual usa Python + venv, sem desativar antivírus.

Workspace padrão:

`C:\Users\47796476817\Downloads\pasta organizada\projeto lay\projeto-laylay\projeto-laylay-bridge-current`

A pasta antiga da Laylay foi preservada sem atualização forçada.

### Política de acesso

Leitura pode abranger o volume `C:\`, mas o Bridge bloqueia zonas sensíveis antes da operação.

Exemplos de zonas bloqueadas:
- Windows, Program Files, ProgramData, Recovery, System Volume Information, Boot/EFI e Config.Msi;
- arquivos críticos da raiz como pagefile.sys, hiberfil.sys e swapfile.sys;
- .ssh, .gnupg, .aws, .azure;
- cofres de credenciais do Windows;
- perfis sensíveis de Chrome, Edge e Opera;
- arquivos secretos do próprio Bridge.

Escrita é mais restrita que leitura. AppData e a pasta do próprio LaylayDevBridge ficam sem escrita remota.

Alteração, sobrescrita, movimentação ou exclusão de arquivo existente fora do workspace padrão exige SHA-256 atual quando aplicável.

### Arquivos

Actions disponíveis incluem:
- list_files, find_files, search_text, stat_path;
- read_text, read_text_range, tail_file e read_binary;
- write_text e patch_text com proteção;
- create_directory;
- copy_file e copy_directory;
- move_path;
- delete_file e delete_directory;
- backup_file e restore_backup;
- check_python_syntax.

### Desenvolvimento e Git

Actions:
- git_diff;
- git_log;
- run_readonly;
- run_named_command;
- run_tests.

Comandos nomeados incluem operações Git de inspeção, versão do Python, Ruff e mypy.

O Python de projeto usa o launcher `py -3.14` com ambiente limpo das variáveis herdadas da venv do Bridge.

### Sessões de processo

A v0.8 introduziu processos gerenciados persistentes:
- process_start;
- process_sessions;
- process_output;
- process_input;
- process_stop.

Perfis atualmente permitidos:
- laylay;
- pytest;
- vscode.

Não existe shell remoto genérico. Isso é deliberado: uma sessão arbitrária de cmd.exe/PowerShell permitiria contornar as barreiras de arquivo da própria ponte.

A leitura de saída usa cursor incremental, permitindo acompanhar apenas linhas novas.

Teste remoto validado:
- uma chamada process_start iniciou pytest;
- session_id: `ps_9f79e33251b048cc`;
- outra chamada process_output leu a mesma sessão;
- resultado: `23 passed in 6.71s`.

### Windows e observabilidade

Actions:
- system_status: CPU, RAM, swap, disco, rede, bateria e boot time;
- list_processes sem expor command line;
- list_windows;
- focus_window;
- capture_screen.

Screenshots são salvos como JPEG reduzido em `.bridge_artifacts/screenshots`; leitura binária pequena permite transportar artefatos controlados.

Teste local de screenshot:
- origem: 1920x1080;
- saída: 960x540;
- aproximadamente 52 KB.

### Relay

Relay atual: linha v0.6.x.

Foi implementado long-poll em `/command/next` com janela de até 20–25 segundos. O agente mantém a requisição aberta e recebe comando assim que ele aparece, eliminando o atraso fixo de polling de ~3 segundos.

Também foi implementado lease de comando para reduzir corrida entre agentes concorrentes.

O Relay possui código para persistir commands, receipts e leases em `/data/relay_state.json`.

Um volume Railway `relay-data` foi criado para `/data`, mas o mount permanece em mudança staged não aplicada, porque o delta completo do patch não pôde ser auditado com segurança pelas ferramentas disponíveis. Portanto, não considerar a fila persistentemente garantida até o mount ser aplicado/verificado.

### Testes remotos v0.8

`system_status` foi executado pelo caminho criptografado completo e retornou receipt confirmado do agente 0.8.0.

Fluxo validado:

ChatGPT -> GitHub Issue criptografada -> GitHub Actions -> Railway Relay -> long-poll -> LaylayDevBridge 0.8.0 -> receipt -> Relay -> ChatGPT.

### Código preservado

O código sem segredos do agente v0.8 foi versionado na branch `laylay-bridge-relay` em:

- `tools/laylay_dev_bridge/server.py`
- `tools/laylay_dev_bridge/bridge_runtime.py`
- `tools/laylay_dev_bridge/requirements.txt`
- `tools/laylay_dev_bridge/bridge_remote.example.json`
- `tools/laylay_dev_bridge/README.md`

O arquivo real `bridge_remote.json` não deve ser versionado.

### Pendências conhecidas

- aplicar/verificar com segurança o volume persistente do Relay;
- substituir o transporte GitHub Actions por um controlador direto quando houver autenticação nativa adequada, pois o startup do GitHub Actions ainda é a maior parte da latência;
- adicionar identidade/credencial individual por dispositivo antes de escalar para muitos PCs;
- empacotar/assinar uma distribuição Windows que não seja bloqueada pelo antivírus;
- manter interação GUI de teclado/mouse restrita até existir uma política que impeça bypass das proteções por meio de terminais/janelas.
