# Checkpoint de manutenção da Laylay

Este documento descreve como criar, validar e recuperar uma versão de
manutenção sem incluir memória pessoal ou credenciais.

## Fronteiras do checkpoint

- código e testes ficam no Git;
- configuração pública usa `.env.example` e
  `configuracao.portatil.example.env`;
- `memoria/`, `playlists.json`, dados da Tuya, credenciais, áudios pessoais,
  modelos locais, logs, builds e ambientes virtuais ficam fora do checkpoint;
- uma mudança estrutural não deve carregar junto uma habilidade nova, alteração
  de personalidade ou migração de dados pessoais.

## Retrato sanitizado

Para imprimir o retrato no terminal:

```powershell
.\.venv314\Scripts\python.exe scripts\gerar_checkpoint_manutencao.py
```

Para guardar uma cópia local ignorada pelo Git:

```powershell
.\.venv314\Scripts\python.exe scripts\gerar_checkpoint_manutencao.py --saida logs\checkpoint_manutencao.json
```

O relatório contém somente métricas, ambiente público, commit, quantidade de
alterações e nomes de arquivos potencialmente sensíveis que tenham sido
versionados por engano. O conteúdo desses arquivos nunca é aberto.

## Verificações antes de marcar uma fase

Verificação rápida dos fluxos de inicialização, conversa, comando, modo jogo e
encerramento:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verificar_smoke_manutencao.ps1
```

Portão completo de qualidade:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verificar_qualidade.ps1
```

O segundo comando inclui compilação, Ruff, tipagem gradual, suíte completa,
cobertura e auditoria das dependências. Durante trabalho sem rede, a opção
`-SemAuditoria` permite executar todas as verificações locais, mas não conclui
sozinha uma versão final.

## Build portátil sem dados pessoais

O ensaio estrutural pode omitir modelo e download para ser mais rápido:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File empacotamento\build_portatil.ps1 -SemModelo -SemDownloadRuntime -PularInstalacaoDependencias
```

A versão final deve repetir o build sem `-SemModelo`. As opções
`-IncluirMemoriaPessoal` e `-IncluirConfiguracoesPrivadas` permanecem proibidas
em um pacote destinado a outra pessoa ou a uma máquina não confiável.

## Identificação e recuperação

1. registre no roadmap a data, o commit e as métricas aprovadas;
2. crie o commit ou a tag somente depois de conferir que não há dados privados;
3. para comparar uma regressão, gere um novo retrato e compare as métricas e os
   testes com o checkpoint anterior;
4. recupere código por um commit conhecido usando o fluxo normal do Git, sem
   apagar a árvore de trabalho atual;
5. restaure memória e configurações apenas a partir de backup pessoal separado;
6. nunca use um pacote portátil como backup da memória da Laylay.

O checkpoint prova a qualidade do código daquele estado. Ele não substitui o
backup dos dados pessoais nem autoriza uma atualização automática.
