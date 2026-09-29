# Checkpoint P01 — 28/09/2026, antes do desligamento

## Base e escopo

- Branch `main`, HEAD `a078360e6b694c37f981e8be11f1470dd14571d5`.
- Worktree já estava suja, com alterações paralelas em produção e testes;
  nenhuma foi restaurada, apagada, commitada ou atribuída a esta frente.
- Esta sessão alterou apenas a sonda offline P01, seus testes, o carregamento
  do painel v21 e a documentação. **Não** alterou `laylay.py`, fala, treino,
  autorização, executores ou o runtime real da Laylay.

## Estado reproduzível

- Painel v21 escrito antes da primeira execução, com cinco contrastes.
  SHA-256 entradas:
  `07335803E693BDBCFB45803DE4B39E2C290CDE899CF3A955F7D9B1E262BE7782`;
  gabarito manual local:
  `635026DFC42F899DD85964BB7202B45768E13735DE1B1979AD992B0CC891AAE4`.
- O parser `pt_core_news_sm` marcou `falham` como `PROPN/flat:name` em um
  controle e `ADJ/conj` com sujeito próprio em outro. RED focado levou a
  abstenção POS explícita no segundo caso. O primeiro continua sem predicado
  suficiente; nenhuma palavra foi promovida artificialmente a verbo.
- A sonda agora distingue motivo de ausência de prévia (vínculo ausente,
  conflito POS, veto superficial/morfológico, composição inválida) e audita
  a prévia **depois** da proposta, só contra trechos do gabarito local.
  `--resumo` emite contagens, sem transformar abstenções em acertos.
- Parser real, v15–v21: 44 casos, 14 prévias, 14 trechos alinhados à revisão
  manual local, zero divergentes nessa amostra. V21: 5 casos, 1 prévia
  alinhada e 4 sem prévia. V7–v14: 65 casos, nenhuma prévia experimental.
  Essas contagens **não** medem acurácia em produção ou qualidade do ensino.
- Um controle pareado simulado mostra que arco `conj → obj` e morfologia
  plural iguais cabem tanto em sujeito quanto em objeto composto. A
  abstenção conservadora perde cobertura, mas evita tratar sintaxe incerta
  como prova semântica.
- Regressão final: **230 testes** das sondas de ensino verdes. `py_compile`
  dos arquivos tocados e `git diff --check` dos arquivos rastreados tocados
  sem erros. Nenhum teste de runtime real foi executado nesta sessão.

## Retomada

P01 continua **aberta e em sombra**. Próxima fronteira: medir um avaliador
independente da relação do fragmento intermediário (`objeto_anterior`,
`sujeito_seguinte`, `indeterminado`) em pares mínimos novos, sem mostrar a
saída do spaCy ou o gabarito ao avaliador. Validar citações literais e
comparar desacordos; concordância de dois modelos ainda não libera ensino,
fala nem efeito. Depois, avaliar geração, verificação e fala final no runtime
real separadamente. Não retreinar nem ampliar o veto com palavras específicas
apenas para fazer v21 ficar verde.

## Encerramento solicitado

`shutdown.exe /s /t 1800` foi aceito pelo sistema às aproximadamente
02:43:55 UTC (23:43:55 BRT, 27/09). Desligamento esperado por volta de
03:13:55 UTC (00:13:55 BRT, 28/09). Este checkpoint foi gravado antes da
janela final de dois minutos. A execução futura do desligamento não pode ser
confirmada depois que este turno terminar.
