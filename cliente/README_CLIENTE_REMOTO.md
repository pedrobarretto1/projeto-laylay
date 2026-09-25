# Cliente remoto da Laylay

## Executável de testes

Build: `powershell -ExecutionPolicy Bypass -File empacotamento/build_cliente.ps1`.
O `.exe` independente fica em `dist/cliente_pc_b-DATA/cliente_laylay.exe`.
Pode ser copiado para o PC B sem instalar Python; mantenha o console aberto
para acompanhar a conexão. Nenhum token ou memória pessoal é incluído.

Antes de abrir, defina `LAYLAY_PC_B_TOKEN` no ambiente com o mesmo segredo
configurado no cérebro. O cliente pergunta o IP do PC principal; grava-o em
`cerebro_ip.txt` no diretório de trabalho. Usa WebSocket na porta 8080; utilize
somente uma rede local de confiança. Fechar o console encerra o cliente.

`cliente_laylay.exe --verificar-instalacao` valida os imports e termina sem
conectar nem executar comandos. Não comprova conexão ou efeitos no outro PC.
Shell, automação de entrada e inicialização com Windows continuam opt-in.

O cliente do PC B opera em modo restrito por padrão. Ele anuncia somente as
ações realmente habilitadas e o cérebro recusa enviar uma ação que o cliente
não declarou suportar.

## Configuração obrigatória

Defina `LAYLAY_PC_B_TOKEN` nos dois computadores com o mesmo valor e pelo
menos 16 caracteres. O valor não é publicado no manifesto, no diagnóstico ou
nos heartbeats.

Por padrão, criação e remoção de arquivos ficam limitadas à pasta `Downloads`
do usuário do PC B. Para autorizar outras raízes, defina
`LAYLAY_PC_B_ALLOWED_ROOTS` com caminhos absolutos separados por ponto e
vírgula.

## Recursos privilegiados

Estas opções permanecem desligadas até serem habilitadas explicitamente:

- `LAYLAY_PC_B_ALLOW_INPUT_AUTOMATION=1`: digitação, teclas e clipboard;
- `LAYLAY_PC_B_ALLOW_SHELL=1`: execução de comandos de shell;
- `LAYLAY_PC_B_AUTO_INSTALL=1`: permite instalar dependências ausentes;
- `LAYLAY_PC_B_AUTOSTART=1`: inicialização automática da versão empacotada.

Um recurso desligado não aparece entre as capacidades do cliente e não pode
ser selecionado pelo cérebro.

## Garantias do protocolo 2

- heartbeat de saúde a cada 15 segundos;
- limite de tamanho para mensagens;
- identificador obrigatório nos pedidos do cérebro;
- proteção contra repetição e excesso de pedidos;
- resultado final correlacionado e único;
- captura bloqueada quando a janela aparenta conter login, pagamento,
  conversa privada ou dados bancários.
