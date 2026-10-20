# AUTO USB/Wi-Fi e companhia autenticada — 17/10/2026

Base: main, ca592a9609dd1865b63b22c714f8d3e802fa2a5c. Preservadas as alterações
anteriores da reativação Wi-Fi de16/10. Sem reset, regravação neste incremento,
mudança de credenciais, PWM ou limites dos sensores; nenhum commit criado.

## Primeiras fronteiras e contratos

CORPO-USB-IDENTIDADE-01: AUTO escolhia um único canal na composição. A
preferência USB impedia tentar a rede sem cabo; preparar a rede Windows dependia
do launcher especial. Inicialmente rede encerrada/nenhum aplicativo aberto.
Ao iniciá-los, o corpo na bateria voltou a responder e a UI recebeu sensores.

CORPO-DECISAO-V1: Pedro confirmou que comando manual movimentava motores;
leituras já chegavam por TCP. A recusa era _ativar_sessao, que exigia serial.
Sem concessão, autorizar_busca_obstaculos não libera SENTRY. RED:1 falhou/1 passou
(rede autenticada indevidamente recusada; não autenticada corretamente negada).
Isso falsifica falha geral de execução/sensores como explicação desse bloqueio,
sem excluir possíveis problemas elétricos independentes.

Mesmo RostoOledRuntime agora procura USB pareado e, ausente, TCP salvo. Mantém
canal saudável até desconexão; nova escolha tem nova sessão e não repete gesto.
TCP confere HEALTH do fingerprint salvo antes de FACE. Ambiguidade USB, arquivo
inválido, alvo diferente e AUTH recusado falham fechados. COM/OFF/WIFI explícitos
continuam disponíveis. Preferência de companhia não decide transporte AUTO.

Companhia aceita serial ou TCP autenticado pelo owner, ainda exigindo preferência
ou pedido humano, sessão confirmada, disponibilidade e coordenador. Recuperação
exige mesmo corpo e estabilidade; percepção e descoberta não concedem movimento.
O catálogo descreve os dois canais e conserva distinção entre receipt e efeito.

RedeLocalCorpoWindows reutiliza scripts/hotspot_corpo_windows.ps1 e seu receipt,
somente para perfil local provisionado. Tenta endpoint existente antes de criar
gerente. Apenas falha anterior ao AUTH prepara rede; rejeição de autenticação
não muda rede. Gerente alheio não é encerrado; só o iniciado por este owner.

## Provas e controles

- red_selecao.txt:1 falhou/2 passaram. Negativo depois passou a exigir alcançar
  divergência TCP, em vez de passar por ausência de USB.
- final_transportes.txt:61 passaram; fábrica, TCP socket real, identidade,
  reconexão sem replay, canais explícitos e composição instalada.
- regressivos.txt:150 passaram/2 excluídos. Um RED anterior de receipt da
  companhia permanece separado. Outro importa singleton da produção e estava
  ocupado pelo ensaio; passou depois em final_transportes.txt. Conjuntos sobrepostos.
-6 testes finais de ciclo de vida do gerente, concessão e catálogo passaram.
- Fixtures TCP antigas: falha de glitch agora nasce depois da negociação, que
  pode superar validade do overlay; produção não ganhou prazo maior. Composição
  de ESP simulado curto declara perfil bancada e não herda pareamento pessoal.

## Placa real sem USB de dados

Pedro deixou superfície sob o inferior e objeto frontal, autorizando testes
durante sua ausência. Bateria3,7V nos pinos. Root instalado, carregar_memoria,
mesmo owner/companhia/coordenador; sem UI normal ou daemon de IA. Não foi enviado
comando manual de avanço. Primeiro ensaio não esperou associação suficiente;
outro esbarrou na recusa de tomar rede hospedada já ativa. Preservado em
ensaio_preparacao_rede_falhou.json. Não removida essa proteção do script.

Ensaio final em ensaio_sensores.json:43 amostras TCP, companhia ativa em39,
vigia ativa em37. GUARD registrou OBSTACULO, RECUANDO, BUSCANDO, CONFERINDO e
ESPERA_BUSCA, tentativas1..4 e retomada. Ao final frontal34mm/inferior31mm.
Uma confirmação expirou: sessão e concessão foram renovadas automaticamente
para o mesmo corpo. Boot d4b928bb permaneceu igual; reinicios_observados=0.
Parada final teve SACK correlacionado. Nenhum processo de ensaio permaneceu.

São receipts do firmware; Pedro não observou as rodas neste ensaio. USB foi
testado com ESP simulado/HEALTH e composição; não houve troca física de cabo
nesta execução. Não prova antiqueda completa, estabilidade elétrica encerrada
ou posição/caminho medidos. CORPO-I2C-01 e comentário por voz seguem separados.

## Estado final

Companhia revogada ao terminar o teste; STOP/SACK e transporte encerrado.
Laylay fechada; companhia/passeio/perfil salvos preservados. Rede já existente
não foi tomada nem encerrada pelo novo owner. Próxima abertura normal em AUTO
considera ambos os canais. Próxima prova humana: conferir recuo/busca e troca
física de cabo em ensaio apropriado; não esperar replay do gesto interrompido.
