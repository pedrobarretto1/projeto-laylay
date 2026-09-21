# Análises offline

`analisar_neural_v27_list_windows_caos.py` foi recuperado de `c8b4c26`, última
versão registrada antes da remoção. As funções de análise foram preservadas;
somente raiz/imports e localização do roteiro foram ajustados.

É uma ferramenta histórica específica da comparação v26/v27 LIST_WINDOWS.
Ela requer os modelos e artefatos locais daquele experimento; o hash esperado
é histórico e não foi atualizado para certificar um modelo diferente.

Não treina, não promove modelos e não executa comandos da Laylay. Importar o
módulo não inicia a análise. Executar diretamente faz leituras dos artefatos e
imprime o relatório; não interpretar restauração do script como validação atual
dos modelos. Resultados locais continuam fora do Git.
