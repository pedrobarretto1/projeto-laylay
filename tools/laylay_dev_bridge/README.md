# Laylay Dev Bridge Agent v0.9

Agente Windows local usado pela Laylay/ChatGPT para desenvolvimento remoto controlado.

## Arquivos

- `server.py`: MCP local, politica de acesso, transporte Relay e actions.
- `bridge_runtime.py`: sessoes de processo, processos do Windows, janelas e screenshot.
- `requirements.txt`: dependencias do agente.
- `bridge_remote.example.json`: configuracao sem segredos.
- `device_identity.example.json`: exemplo do sidecar local de identidade por PC.\n- `enroll_device.py`: cria/reutiliza identidade, protege o segredo com DPAPI e emite somente o registro seguro para o Relay.

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
- UI Automation por perfil autorizado (VS Code, Arduino IDE, Android Studio e Laylay)
- Risk Gate para controles sensiveis; sem clique por coordenada e sem texto livre

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

Cada PC usa um `device_identity.json` local com `device_id` + `device_secret_dpapi`. O segredo real fica protegido pelo Windows DPAPI e e aberto somente em memoria pelo agente. O Relay recebe apenas o SHA-256 em `DEVICE_CREDENTIALS_JSON`, permitindo revogacao individual por dispositivo.

O token global legado continua apenas como fallback de migracao; novos agentes devem preferir identidade por dispositivo.

Nunca versione os arquivos reais `bridge_remote.json` ou `device_identity.json`.
