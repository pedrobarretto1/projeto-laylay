# Laylay

A Laylay é uma assistente pessoal para Windows. Este repositório contém o
código, o avatar, a extensão do Chrome, o firmware e a bancada virtual.

## Abrir a partir do GitHub

1. Instale o Python 3.14 com o inicializador `py` e o Ollama.
2. Abra o Ollama e prepare o modelo com `ollama pull qwen3:4b-instruct`.
3. Depois de extrair o ZIP do GitHub ou clonar o repositório, execute na pasta
   da Laylay:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\empacotamento\iniciar_codigo.ps1 -Preparar
   ```

Nas próximas aberturas, use o mesmo comando sem `-Preparar`. O ambiente Python
fica em `%LOCALAPPDATA%\Laylay\python314`. Para reutilizar um ambiente existente,
informe a pasta dele em `-AmbientePython`. Use `-SomentePreparar` para instalar
as dependências sem abrir a Laylay.

O código usa o Ollama local por padrão. O repositório contém o código-fonte e
o script de preparação. O Ollama baixa o modelo de conversa separadamente.
Na primeira preparação, o script cria `configuracao.env` se ainda não existir.
Consulte `.env.example` para opções de integração. Ao atualizar sua
instalação, guarde `configuracao.env`, `memoria` e `playlists.json`.

## Modelo neural de comandos

A implementação está em `mente_laylay/neural`. Os modelos treinados, dados
pessoais e ambientes de treinamento ficam fora da distribuição. O modelo
neural de comandos é independente do modelo de conversa no Ollama.

Para carregar uma rede treinada de fora do projeto, use um caminho absoluto
no seu `configuracao.env`:

```dotenv
LAYLAY_NEURAL_MODE=shadow
LAYLAY_NEURAL_MODEL_PATH=C:\Laylay-Dados\neural\modelo_ativo.joblib
```

Use um artefato treinado por você ou de uma origem confiável. Um modelo
semântico híbrido também precisa dos arquivos ONNX e do tokenizer no caminho
registrado no próprio modelo e das dependências `onnxruntime` e `tokenizers`
no ambiente Python. O modo `shadow` coleta previsões para comparação.

## Distribuição portátil

O [guia portátil](empacotamento/README_PORTATIL.md) explica a montagem do
`Laylay.exe`. O empacotador prepara o llama.cpp separadamente. Builds antigos
do ESP32 e relatórios brutos de teste continuam no histórico do Git.
