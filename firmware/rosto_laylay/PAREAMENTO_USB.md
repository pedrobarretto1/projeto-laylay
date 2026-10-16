# Corpo reconhecido por identidade USB

O corpo de Pedro está pareado como **Corpo da Laylay**. O nome é exibido no
DEV → CORPO; a seleção usa o fingerprint estável do chip devolvido por HEALTH,
não o número COM nem o nome. O firmware instalado já fornece essa informação.

O owner de configuração salva `LAYLAY_CORPO_USB_ID` e `LAYLAY_CORPO_USB_NOME`
em `configuracao.env`. Ao levar a Laylay para outro PC, levar esse arquivo junto
com a instalação. Manter a porta em AUTO permite encontrá-la mesmo se COM4
virar COM8. Uma porta fixada manualmente continua fixa e também precisa
corresponder à identidade pareada. O pareamento atua na conexão USB; as
preferências existentes de transporte Wi-Fi continuam separadas.

Ao conectar pela USB, o mesmo owner do corpo sonda HEALTH nas portas Espressif,
sem HELLO/FACE nos candidatos diferentes. Só admite o alvo esperado e único.
Identidade duplicada, ausente ou configuração inválida bloqueiam a conexão;
não há adoção automática de outra placa. Antes de FACE, a identidade é
conferida novamente. Reconectar não repete movimentos anteriores.

Sem pareamento permanece a detecção anterior: um único candidato USB e
handshake do firmware. O nome amigável não autoriza motores. A identidade
declarada pelo firmware não é autenticação criptográfica contra falsificação.
Uma instalação nova sem o arquivo não possui a lembrança do corpo pareado.

Validação desta versão: chip real reconhecido,17 sincronizações na composição
instalada e identidade divergente recusada antes de HELLO/FACE. Portas variáveis
e múltiplas placas foram verificadas com portas simuladas; outro PC físico não
foi usado no ensaio. Sem motores, voz ou aplicação principal iniciada. Evidências
e regressivos em `artifacts/rosto_oled/identidade_usb/RELATORIO.md`.
