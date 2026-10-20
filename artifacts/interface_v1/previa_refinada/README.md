# Laylay · prévia de refinamento

Prévia independente da interface oficial. Todas as nove abas, o painel rápido e a ilha usam dados de demonstração. Nenhum botão se conecta à Laylay, salva preferências reais, toca áudio, captura janelas ou controla dispositivos.

Abra `index.html` diretamente no navegador, inclusive sem internet. Para a mesma navegação via HTTP, execute na pasta desta prévia:

```powershell
python -m http.server 8792 --bind 127.0.0.1
```

Depois abra http://127.0.0.1:8792/.

Use a barra superior para experimentar os três formatos e os estados com dados e vazio. O tema ciano, movimento reduzido, busca, playlists, diálogo, console e configurações funcionam apenas na memória da prévia. Recarregar restaura o cenário inicial.

Derivada do bundle visual da V1, com maior legibilidade, hierarquia por página e continuidade de rolagem. O mascote mantém os componentes estáveis, piscadas, olhar do mouse e suporte a movimento reduzido.
