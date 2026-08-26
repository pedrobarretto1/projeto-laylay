# Laylay para Xbox Game Bar

Este projeto é somente a camada visual da Laylay. A mente, a captura global do
atalho e o envio por Enter/Esc continuam no processo Python. O widget recebe em
`127.0.0.1:18766` um estado JSON como:

```json
{
  "type": "state",
  "version": 2,
  "emotion": "feliz",
  "speaking": true,
  "activity": "speaking",
  "intensity": 0.8,
  "command_bar": { "visible": false, "text": "" }
}
```

## Compilar e instalar

1. Execute `powershell -ExecutionPolicy Bypass -File .\install-uwp-build-tools.ps1`
   para instalar **UWP Build Tools** no Build Tools 2022 (uma única vez).
2. Abra PowerShell nesta pasta.
3. Execute `powershell -ExecutionPolicy Bypass -File .\build.ps1`.
4. Execute `powershell -ExecutionPolicy Bypass -File .\install.ps1`.
5. Inicie a Laylay, abra `Win + G`, escolha **Laylay** e fixe o widget.
6. No menu do widget fixado, ative **click-through**.
7. Para personalizar, abra o menu de três pontos do widget e escolha
   **Configurações**. O clique é tratado pelo widget e abre a janela filha da
   Game Bar sem depender do processo Python.

O script cria um certificado local de desenvolvimento, assina o MSIX, instala o
certificado apenas em `TrustedPeople` do usuário atual e libera loopback somente
para a identidade do widget.

Na máquina de destino basta distribuir o `.msix` e o `.cer` da pasta
`artifacts`, confiar no certificado e instalar o pacote. A compilação não exige
Python na máquina de destino; a aplicação final completa ainda precisa incluir o
executável empacotado da Laylay que fornece a ponte local.

Referências: [projeto e pacote oficial](https://learn.microsoft.com/en-us/xbox/game-bar/guide/proj-reference),
[primeiro widget](https://learn.microsoft.com/en-us/xbox/game-bar/quickstart/introduction) e
[click-through](https://learn.microsoft.com/en-us/xbox/game-bar/guide/click-through).
