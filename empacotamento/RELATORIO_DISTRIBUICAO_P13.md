# Relatório de distribuição — P13

Data da validação: 02/08/2026.

## Resultado

A distribuição portátil completa foi gerada e aprovada pelo auditor e pelo
smoke test executado dentro do `Laylay.exe` congelado. A montagem padrão é limpa,
não depende de Python ou Ollama instalados e não contém memória nem credenciais
do ambiente de desenvolvimento.

Artefato validado:

- pasta: `build_portatil/dist/Laylay`;
- tamanho aproximado: 2,79 GB;
- arquivos: 1.887;
- modelo: `laylay-qwen3-4b-q4_k_m.gguf`, 2.497.280.480 bytes;
- motores: llama.cpp Vulkan e CPU;
- SHA-256 de `Laylay.exe`:
  `5EF63C0F54CDC44F2EFFE13B649D6E10D297E0D86FF5F03E4CFADE7D1AE85B00`.

O hash identifica esta montagem local e muda quando o código é recompilado.

## Evidências automatizadas

- o versionamento foi inspecionado e não contém memória, playlists pessoais,
  amostras de voz, configuração privada ou arquivos TinyTuya;
- o pacote contém `Laylay.exe`, inicializador CMD, avatar, extensão do Chrome,
  assets visuais, configuração segura, modelo e os dois motores locais;
- a configuração distribuída mantém credenciais vazias, IoT em modo simulado e
  controle físico não autorizado;
- o pacote foi inspecionado contra caminhos pessoais em arquivos de configuração
  e documentação;
- o smoke congelado carregou chat de terminal, atalhos, voz, avatar, navegador e
  modo jogo sem usar rede;
- a memória do pacote aceitou escrita e limpeza da sentinela de teste;
- o backend selecionado foi o portátil, demonstrando degradação independente de
  Ollama;
- a migração de uma memória JSON legada para SQLite possui teste automatizado;
- a auditoria de dependências não encontrou vulnerabilidades conhecidas.
- o portão final aprovou Ruff, mypy em 20 fontes, 1.808 testes, 45 subtestes e
  cobertura global de 64% com mínimo obrigatório de 60%.

## Segurança da montagem

O diretório `dist` e a área de trabalho do PyInstaller são removidos antes de
cada build. Isso impede que uma montagem privada deixe memória ou credenciais
residuais numa montagem limpa posterior. Playlists acompanham apenas a opção de
memória pessoal; arquivos Tuya e amostras de voz exigem explicitamente a opção
de configurações privadas.

O auditor `verificar_pacote.py` é executado pelo próprio build e faz a montagem
falhar se encontrar uma violação. O smoke também é obrigatório e faz o build
falhar se um componente crítico não puder ser carregado.

## Limitações conhecidas

- a cópia e abertura em um segundo computador físico não podem ser automatizadas
  neste repositório; a portabilidade foi validada por estrutura, caminhos
  relativos e execução congelada no Windows de desenvolvimento;
- microfone, saída de áudio, aceleração Vulkan e automação de janelas dependem de
  drivers e permissões do computador de destino;
- a extensão do Chrome e o widget da Xbox Game Bar precisam de instalação
  separada;
- Gmail, Groq, clima, YouTube e Tuya dependem de rede e, quando aplicável,
  credenciais privadas;
- avisos do PyInstaller relativos a módulos de outros sistemas operacionais são
  esperados no Windows; os módulos críticos da Laylay passaram no smoke real.

## Recuperação

1. Preserve a pasta portátil inteira; não mova somente os executáveis.
2. Consulte `logs/llama-server.log` quando a conversa local não carregar.
3. Restaure `configuracao.env` a partir do exemplo para desativar integrações
   externas sem afetar os comandos locais.
4. Faça backup de `memoria/` e `playlists.json` antes de substituir a instalação.
5. Remova apenas `memoria/laylay_memoria.sqlite` quando desejar reiniciar toda a
   memória; essa ação é destrutiva e não deve ser feita sem backup.
6. Reinstale a extensão do navegador ou a Game Bar separadamente quando apenas
   esses componentes falharem.

## Comandos reproduzíveis

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verificar_qualidade.ps1
powershell -ExecutionPolicy Bypass -File .\empacotamento\build_portatil.ps1 -SemDownloadRuntime -PularInstalacaoDependencias
.\.venv314\Scripts\python.exe .\empacotamento\verificar_pacote.py .\build_portatil\dist\Laylay --raiz-projeto .
```
