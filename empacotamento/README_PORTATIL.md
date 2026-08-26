# Laylay portátil

Abra **`Iniciar Laylay.exe`**. Ele cria uma janela real do CMD na pasta
portátil e executa `Laylay.exe` dentro dela, mantendo a digitação, os atalhos
de chat/voz e os diagnósticos visíveis. Não é necessário instalar Python,
Ollama ou VS Code. O `Laylay.exe` também pode ser iniciado diretamente por
quem já estiver usando um terminal.

Na primeira conversa, o modelo local pode levar alguns segundos para entrar na memória. A Laylay tenta Vulkan primeiro para aproveitar a GPU e cai automaticamente para CPU quando o driver ou hardware não aceita esse caminho. O processo local é fechado junto com a Laylay e também é descarregado durante jogos quando o modo jogo pede VRAM.

## Arquivos importantes

- `modelos/`: contém o modelo GGUF da conversa.
- `runtime_llm/`: contém os motores Vulkan e CPU do llama.cpp.
- `memoria/`: identidade, aprendizado, agenda e histórico local.
- `avatar/`: quadros visuais.
- `configuracao.env`: opções e credenciais privadas desta instalação.
- `logs/llama-server.log`: diagnóstico do motor local.

## Serviços opcionais

A conversa e os comandos locais funcionam sem Ollama. Visão Groq, clima, YouTube, Gmail e Tuya continuam dependendo de internet e das respectivas credenciais. Nunca compartilhe uma distribuição que contenha sua memória, senha de aplicativo do Gmail ou chaves da Tuya.

O widget da Xbox Game Bar e a extensão do Chrome são componentes separados porque o Windows e o navegador exigem instalação própria.

## Privacidade e montagem

O build padrão sempre apaga a saída anterior e cria uma instalação limpa. Ele
não leva memória, playlists, amostras de voz, configuração privada nem arquivos
Tuya. As opções `-IncluirMemoriaPessoal` e `-IncluirConfiguracoesPrivadas`
existem apenas para uma cópia destinada ao próprio dono e não devem ser usadas
num pacote compartilhável.

Ao final da montagem, o script audita arquivos privados, credenciais preenchidas,
caminhos pessoais e componentes obrigatórios. Depois ele inicia `Laylay.exe` em
modo de diagnóstico, sem microfone nem rede, para conferir chat, atalhos, voz,
avatar, navegador, modo jogo, memória gravável e motor local.

## Recuperação

- Se a conversa local não iniciar, confira `logs/llama-server.log`, mantenha
  `modelos/` e `runtime_llm/` ao lado de `Laylay.exe` e tente novamente. O motor
  cai de Vulkan para CPU automaticamente.
- Se uma integração externa falhar, revise apenas sua cópia de
  `configuracao.env`. Deixar uma credencial vazia desativa a integração sem
  impedir os comandos locais.
- Antes de substituir uma instalação existente, faça backup da pasta `memoria/`
  e de `playlists.json`. Ao restaurá-los, a memória JSON legada é migrada para
  SQLite na primeira abertura.
- Se o microfone ou áudio falhar, confirme o dispositivo padrão e o driver do
  Windows. O chat de terminal continua disponível.
- Se navegador ou Game Bar não responderem, reinstale separadamente a pasta
  `extensao_chrome/` ou o widget; eles não são registrados automaticamente pelo
  executável portátil.

## Limitações conhecidas

O smoke test confirma que os componentes foram empacotados e podem ser
carregados sem Ollama e sem rede, mas não substitui um teste físico de cada
microfone, GPU, navegador e versão do Windows. Gmail, Groq, clima, YouTube e Tuya
continuam sujeitos à internet, credenciais, drivers e serviços de terceiros.
Consulte `RELATORIO_DISTRIBUICAO_P13.md` para a evidência da versão verificada.
