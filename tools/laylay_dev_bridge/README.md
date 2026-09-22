# Laylay Dev Bridge Agent v0.9.1

Agente Windows local usado pela Laylay/ChatGPT para desenvolvimento remoto controlado.

## Arquivos

- `server.py`: MCP local, politica de acesso, transporte Relay e actions.
- `bridge_runtime.py`: sessoes de processo, processos do Windows, janelas e screenshot.
- `requirements.txt`: dependencias do agente.
- `bridge_remote.example.json`: configuracao sem segredos.
- `device_identity.example.json`: exemplo do sidecar local de identidade por PC.
- `enroll_device.py`: cria/reutiliza identidade, protege o segredo com DPAPI e emite somente o registro seguro para o Relay.

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


## Operacao v0.9.1

A v0.9.1 endurece a operacao sem ampliar privilegios:

- mutex de instancia no Windows: uma segunda copia do mesmo Bridge e bloqueada antes de competir por porta/comandos;
- `bridge_status.json`: heartbeat local com PID, versao, device/device_id, workspace, auth, transport, ultimo comando/receipt/erro e uptime;
- action `bridge_status`: permite diagnosticar o agente remotamente sem revelar segredos;
- `bridge_audit.jsonl`: auditoria rotativa (5 MiB) apenas com metadados seguros; conteudo de arquivos, texto digitado e tokens nao sao gravados;
- o estado muda para `degraded` em erro de transporte e volta para `online` quando o Relay responde;
- o launcher de casa usa `.venv_home`, criada especificamente para a maquina local.

O transporte estavel permanece GitHub criptografado -> Railway Relay -> Bridge. O GitHub envia um webhook assinado para o Relay quando a Issue criptografada e aberta, reduzindo a latencia de entrega. O workflow de GitHub Actions continua disponivel como fallback/idempotencia.

O endpoint experimental de controller dispatch permanece desativado por padrao (`DIRECT_DISPATCH_ENABLED=0`) e sua credencial nao e necessaria para a operacao estavel.
