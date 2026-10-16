# CORPO-SENSORES-DIAG-01 — dois VL53L0X, leitura inicial

14/10/2026; HEAD main d850b8c90cc5ce40bd4832e759ed991ba88cd5cc, worktree paralela
preservada. Baseline firmware/status em baseline/. Nenhum commit.

Pedro confirmou dois módulos, compartilhando3V3/GND/SDA8/SCL9 com OLED;
XSHUT0 frontal e XSHUT10 inferior. Autorizado continuar a montagem e testar a
leitura; não foi enviado movimento nem ativada concessão de companhia.

Primeira fronteira ausente: firmware não inicializava nem consultava VL53L0X.
Protocolo DIST não existia no baseline. RED de consulta no firmware congelado
compila e falha na asserção de resposta DIST; red.txt. Não atribuir problema a
pinos/motores antes da leitura; ambos produziram dados válidos após inicialização.

## Contrato

Distância é percepção bruta datada, não autorização nem prova de movimento.
Endereços distintos atribuídos sequencialmente, falha isolada mantém módulo em
shutdown. Amostra inválida ou expirada não reutiliza distância antiga. Consulta
é correlacionada por sequência, sem sessão de tração. Mesmo protocolo serial
existente; nenhuma inteligência ou parser de intenção duplicado no firmware.

## Evidência

- Adafruit_VL53L0X1.2.5/API oficial verificada. Biblioteca no artefato local devido
  a falha de criação de diretório temporário no OneDrive; sem alteração global.
- Core3.3.12, C3/CDC, flags diárias WiFi0/motores1/som simples/limite5000 mantidas;
  sensor1 habilitado.422406bytes programa,19180globais. compile.txt.
- Upload COM4 com hashes de flash verificados; upload.txt/receipt.json.
-10 amostras reais inicialmente válidas: frontal116–122mm, inferior94–104mm.
  Endereços0x30/0x31. Consultas malformadas rejeitadas sem movimento.
- Painel independente: últimas400 leituras preservadas, frontal55–189mm e
  inferior81–199mm nos registros válidos, ambos também reportaram INVALIDA.
  Pedro confirmou: “Sim, os dois respondem separadamente” e montagem definitiva
  inferior aproximadamente10cm acima da mesa. Isso comprova resposta física de
  leitura, não alcance/threshold antiqueda universal.
-81 testes Python passaram (parser diagnóstico e contratos vizinhos da porta
  rosto/motor). Correção local do parser durante desenvolvimento:15 campos e
  posições9/11 para a segunda leitura; casos de incoerência/seq/idade protegem isso.
- Host MSVC: sensores (endereço/falha isolada/idade/qualidade/sem MOTOR), sono,
  som/olhos, expressõesV3 e motor contínuo passaram. clang++ anterior ausente;
  BuildTools instalado reusado. Primeiro ensaio som usou flag de motores errada;
  a execução foi repetida no perfil esperado e o script trata código negativo
  de abort como falha. Falha não foi mascarada com patch no teste ou produção.
- Composição real laylay.py/RostoOledRuntime manteve10 FACE confirmados intercalados
  com DIST. Nenhum MOTOR enviado; encerramento STOP/GOODNIGHT; composicao.json.
- Painel fechado via pedido normal de fechamento, salvou os dados e liberou COM4.
  Nenhuma janela normal da Laylay foi aberta. Processos diagnósticos encerrados.

## Escopo e próxima fronteira

Produção firmware: rosto_laylay.ino + sensores_distancia.h. Não alterou
partituras, emoção, sono, som, pinagem de motores, autorizadores ou catálogo.
Painel scripts/diagnosticar_sensores_usb.py é diagnóstico local, não integração
de capacidade da IA. Dublês/host e testes protegem transporte/validade apenas.

Não há corte automático por obstáculo/borda nesta etapa. A referência inferior
é apenas observação inicial; política precisa validar margem, qualidade, validade,
falha do barramento e cobertura dianteira limitada. Não preencher “sensores
físicos disponíveis” na mente antes de existir entrega canônica real à cognição.
Esse incremento fecha leitura física inicial; integração mente/proteção continua
uma fronteira explicitamente pendente, sem alegação de conclusão global.
