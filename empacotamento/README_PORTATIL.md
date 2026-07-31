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
