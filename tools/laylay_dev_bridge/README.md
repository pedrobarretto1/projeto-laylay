# Laylay Dev Bridge Agent v0.8

Agente Windows local usado pela Laylay/ChatGPT para desenvolvimento remoto controlado.

## Arquivos

- `server.py`: MCP local, politica de acesso, transporte Relay e actions.
- `bridge_runtime.py`: sessoes de processo, processos do Windows, janelas e screenshot.
- `requirements.txt`: dependencias do agente.
- `bridge_remote.example.json`: configuracao sem segredos.

## Capacidades principais

Arquivos:
- listar, localizar, buscar texto, ler por faixa
- criar/editar com SHA-256
- copiar/mover/apagar
- backup e restauracao
- tail de logs
- leitura binaria pequena

Desenvolvimento:
- git status/diff/log/check
- validacao de sintaxe Python
- pytest em sessao persistente
- comandos nomeados (sem shell generico)

Processos:
- sessoes gerenciadas com session_id
- leitura incremental por cursor
- stdin para sessoes permitidas
- stop somente de sessoes iniciadas pelo Bridge
- perfis atuais: Laylay, pytest e VS Code

Windows:
- lista de processos sem command line
- CPU/RAM/disco/rede/bateria
- lista/foco de janelas
- screenshot JPEG em artefato local

## Seguranca

O Bridge nao oferece `cmd.exe`/PowerShell arbitrario pela interface remota.

A politica separa:
- raizes de leitura
- raizes de escrita
- zonas proibidas
- zonas sem escrita
- arquivos protegidos

Arquivos existentes fora do workspace padrao exigem SHA atual para alteracao/exclusao.
Pastas de sistema, credenciais, perfis de navegador e configuracoes secretas do proprio Bridge podem ser bloqueadas independentemente da raiz liberada.

## Transporte

O agente usa long-poll autenticado com o Relay. Comandos publicos via GitHub usam envelopes X25519 + HKDF-SHA256 + AES-256-GCM; o corpo do comando nao fica em plaintext na Issue.

Nunca versione o arquivo real `bridge_remote.json`.
