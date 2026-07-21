# Diagnóstico evoluído da Laylay

O comando `/diagnostico` continua mostrando um retrato textual seguro da mente. Agora o
retrato também inclui observabilidade recente, sem copiar conversas ou dados pessoais.

## Informações apresentadas

- latência mais recente, média e quantidade de amostras da interpretação, execução,
  dispatcher, síntese TTS e turno completo;
- até vinte falhas técnicas recentes, mostrando somente componente, código controlado
  pelo sistema e classe da exceção;
- até vinte decisões recentes de bloqueio, descarte ou adiamento, com a categoria e os
  motivos técnicos;
- saúde dos módulos, estado do turno, última ação e quantidade de pendências.

## Privacidade

A telemetria é mantida somente durante a sessão e não entra na memória durável. Ela não
guarda texto do usuário, resposta da IA, texto falado, URL, caminho de arquivo, conteúdo
de exceções, credenciais ou memória de conversa. URLs e caminhos que apareçam
acidentalmente em códigos técnicos são removidos antes do registro.

## Pontos medidos

- `interpretacao`: construção semântica e contextual do turno;
- `execucao`: execução central de uma intenção;
- `dispatcher`: distribuição dos comandos planejados pela resposta;
- `tts_sintese`: geração do arquivo de voz;
- `tts_total`: síntese e reprodução de áudio;
- `turno_total`: ciclo serializado completo de uma entrada.

Um painel gráfico continua deliberadamente adiado. O retrato textual deve ser usado e
estabilizado primeiro, evitando criar outra interface em cima de métricas ainda em ajuste.
