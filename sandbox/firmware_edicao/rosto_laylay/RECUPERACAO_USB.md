# Sessão perdida, boot e recuperação

Um novo boot é diferente de perder a sessão FACE ou a resposta do OLED.
`HEALTH 1 <consulta>` retorna identidade efuse, nonce do boot, esp_reset_reason,
uptime, heap livre/mínimo, contador e causa da perda da sessão. Somente leitura:
não renova FACE, SENTRY, motor ou autorização. Não existe comando de reboot
remoto novo. Flash/firmware/pinos/PWM e limiares de proteção mantidos.

O owner Python publica identidade somente como fingerprint; a UI mostra causa
de boot, quantidade de reinícios/perdas e recuperação, apenas no DEV→Corpo.
Sem leitura atual não inventa queda de tensão ou reset. Memória livre não mede
uso de CPU. Boot por USB não equivale a brownout.

Ao abrir pyserial, DTR/RTS ficam inativos antes de open. O modo padrão ativo
foi observado causando reset do USB-JTAG ao abrir/fechar a COM4. Se uma sessão
ativa recebe BOOT, seus receipts ficam inválidos imediatamente.

Perda involuntária suspende a companhia identificada; não continua movimento.
Uma sessão nova do MESMO chip, FACE confirmado, saúde recente, sensores
consultáveis e conexão estável permite nova concessão pelo mesmo owner. STOP,
movimento manual, desativação e chip diferente revogam esse pedido. Firmware
antigo sem identidade conserva reativação explícita. Contexto não autoriza.

No executor, HELLO cancela o reflexo antigo. A primeira SENTRY ativa da sessão
nova pode admitir outro incidente, verificando o risco atual. SENTRY0 e FACE
sozinho não movem; SENTRY repetida da mesma sessão não reinicia o episódio.

O OLED ainda teve perdas intermitentes observadas. HEALTH distingue OLED,
NACK_OLED, TIMEOUT_OLED, I2C, TTL e TRANSPORTE quando medidos. A causa elétrica
dessas perdas permanece aberta; não foi aumentada a tolerância para esconder
erro nem removido o corte local dos motores. Provas e limites:
artifacts/rosto_oled/recuperacao_usb/RELATORIO.md.
