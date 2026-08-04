# Terminal Laylay 2.1

O Terminal 2.0 é uma interface PySide6 em processo separado. Ele não possui
LLM, roteador, memória nem executores: recebe retratos sanitizados e envia o
texto à mesma entrada canônica usada pelo terminal original.

## Executar

```powershell
python -m pip install -r requirements.txt
python laylay.py
```

A Laylay abre a ponte local autenticada e inicia a interface automaticamente.
Fechar a janela não encerra a mente; o CMD continua disponível para depuração.
Para iniciar somente com o terminal antigo:

```powershell
$env:LAYLAY_TERMINAL_2="0"
python laylay.py
```

Atalhos: `Enter` envia, `Shift+Enter` quebra linha, `Ctrl+L` foca a caixa de
texto, `Ctrl+B` recolhe a barra lateral e `Ctrl+,` abre Configurações.

## Chat e voz

O seletor `Chat | Voz` usa a porta canônica da Laylay. Em Chat, o composer
textual fica ativo. Em Voz, a interface apenas libera o ouvido já existente no
backend; ela não cria uma segunda captura de microfone. Se o ouvido estiver
indisponível, a seleção é recusada e a interface volta ao estado confirmado.

## Modelo de linguagem

Em **Configurações** é possível escolher Ollama local, o runtime portátil ou
OpenRouter e informar o modelo. A alteração é persistida em
`configuracao.env`, arquivo privado ignorado pelo Git, e passa a valer após
reiniciar a Laylay.

A chave do OpenRouter nunca é escrita em `configuracao.env`, histórico,
diagnóstico ou memória. No Windows ela é protegida com DPAPI para o usuário
atual e armazenada em `%LOCALAPPDATA%\Laylay\credencial_openrouter.dpapi`.
Esse arquivo não é uma credencial portátil e não deve ser incluído no pacote.
O campo vazio preserva a chave existente; substituir e remover são ações
explícitas. Se DPAPI/pywin32 estiver indisponível, a interface recusa o
salvamento da credencial em vez de usar texto puro.

O empacotamento portátil do processo Qt será feito em uma spec própria. Nesta
primeira entrega, o Terminal 2.0 é suportado na execução pelo código-fonte;
isso evita misturar o loop Qt ao executável da mente antes da auditoria da
distribuição.
