r"""Roteiro adversarial/caótico da Laylay.

Objetivo:
- encontrar regressões que o roteiro linear de 118 turnos não encontra;
- forçar entradas imprevisíveis, ambíguas e contextuais;
- testar negação, autocorreção, continuidade, confirmações e múltiplas ações;
- usar apenas alvos de teste ou ações reversíveis.

Execução:
    .\.venv314\Scripts\python.exe .\roteiro_teste_laylay_caos.py
"""

from __future__ import annotations

import sys

from cliente.executor_roteiro_laylay import executar_roteiro


COMANDOS = """
# ---------------------------------------------------------------------------
# BLOCO A — PALAVRAS SOLTAS / FALLBACK / ENTRADA IMPREVISÍVEL
# Nenhuma destas entradas deveria disparar uma ação destrutiva por conta própria.
# ---------------------------------------------------------------------------
ué
hm
hmm
eita
mano
kkkk
ok
talvez
depois
agora
então
e?
como?
por quê?
isso
aquilo
ele
ela
sim
não
volta
continua
para
fecha
abre
Opera
Calculadora
banana
paralelepípedo
42
true
None
🗿
...

# ---------------------------------------------------------------------------
# BLOCO B — ERROS DE DIGITAÇÃO / ACENTOS / CAIXA / PONTUAÇÃO
# ---------------------------------------------------------------------------
abre a calcuradora
fexa a calculadora
ABRE O OPERA
fecha o opera por favorrr
abre    a    calculadora
abre a wikipedia???
pesquiza documentacao python
pessquisa documentação oficial do python
volta pra aba anterir
qual musica ta tocano
pausa a musca
contina a musica
proxima faxa
como ta a lampda
liga a lampda do quarto
deslga a lampada
qual o clma amanha em boituva

# ---------------------------------------------------------------------------
# BLOCO C — NEGAÇÃO / HIPÓTESE / PERGUNTA NÃO AUTORIZADORA
# ---------------------------------------------------------------------------
Como eu abriria a Calculadora?
Não abra a Calculadora.
Talvez eu abra a Calculadora depois.
Eu poderia abrir o Opera agora?
Se eu quisesse fechar o Opera, como faria?
Não feche o Opera.
Você consegue abrir programas?
Você consegue apagar arquivos?
Como eu apagaria um arquivo chamado caos seguro.txt?
Não apague nada ainda.
Se eu disser abre o Opera, você abriria?
Só me explica como pesquisar no navegador, não pesquise nada.
Não liga a lâmpada.
Eu queria saber como deixar a lâmpada azul, mas não mude ela.
Me explica como pausar uma música sem pausar agora.

# ---------------------------------------------------------------------------
# BLOCO D — ARQUIVOS DE TESTE / AUTOCORREÇÃO / CONFIRMAÇÕES
# ---------------------------------------------------------------------------
Cria um arquivo chamado caos seguro.txt e escreve primeira linha.
Leia o caos seguro.txt.
Acrescente segunda linha.
Leia de novo.
Apaga o caos seguro.txt.
talvez
sim, mas não agora
não
O arquivo ainda existe?
Apaga o caos seguro.txt.
sim
Quero ele de volta.
Leia o caos seguro.txt.
Apaga o caos seguro.txt.
não
sim
O arquivo ainda existe?
Cria um arquivo chamado troca ideia.txt e escreve alpha.
Apaga o troca ideia.txt.
Antes de confirmar, quanto é três mais três?
sim
O arquivo troca ideia.txt ainda existe?
Apaga o troca ideia.txt.
sim
Quero ele de volta.
Fecha ele.
Não, eu estava falando do arquivo, não de uma janela.
Onde fica o troca ideia.txt?

# ---------------------------------------------------------------------------
# BLOCO E — AUTOCORREÇÃO NA MESMA FRASE
# ---------------------------------------------------------------------------
Abre o Opera... não, abre a Calculadora.
Fecha a Calculadora... quer dizer, maximiza ela.
Abre a Wikipédia, não, melhor o Prime Video.
Pesquisa Python... pera, não pesquisa nada.
Liga a lâmpada... não, deixa desligada.
Pausa a música... esquece, continua tocando.
Cria um arquivo chamado erro.txt... não, chama correcao.txt.
Escreve banana no correcao.txt... quer dizer, escreve maçã.
Apaga o correcao.txt... não apaga.
Onde fica o correcao.txt?

# ---------------------------------------------------------------------------
# BLOCO F — REFERÊNCIAS / PRONOMES / AMBIGUIDADE
# ---------------------------------------------------------------------------
Abre a Calculadora.
Abre o Opera.
Fecha ele.
Qual deles você fechou?
Abre a Calculadora de novo.
Coloca ela na direita.
Coloca o outro na esquerda.
Maximiza ele.
Qual está em foco agora?
Abre a Wikipédia.
Abre o Prime Video.
Fecha a primeira.
Qual aba ficou aberta?
Volta para a anterior.
Fecha essa.
Abre a Wikipédia de novo.
Pesquisa documentação do Python.
Abre o primeiro resultado.
Resume isso.
E a anterior?
Volta.
Resume agora.

# ---------------------------------------------------------------------------
# BLOCO G — CONDIÇÕES / IDEMPOTÊNCIA / ESTADO REAL
# ---------------------------------------------------------------------------
Se o Opera estiver aberto, só me diga; não mexa nele.
O Opera está aberto?
Se a Calculadora não estiver aberta, abre; se já estiver, só me avisa.
A Calculadora está aberta?
Se ela estiver aberta, maximiza; se não estiver, não faça nada.
A Calculadora continua aberta?
Se o Prime Video já estiver aberto em uma aba, não abra outra.
O Prime Video está aberto?
Se a lâmpada estiver ligada, só me diga o estado.
Como está a lâmpada do quarto?
Se ela já estiver desligada, não mande desligar de novo.
Desliga a lâmpada do quarto.
Desliga ela de novo.
Como ela ficou?

# ---------------------------------------------------------------------------
# BLOCO H — MÚLTIPLAS AÇÕES NA MESMA FRASE
# ---------------------------------------------------------------------------
Abre a Calculadora e coloca ela na direita.
Abre o Opera e coloca ele na esquerda.
Maximiza a Calculadora e depois volta o foco para o Opera.
Abre a Wikipédia, pesquisa documentação oficial do Python e abre o primeiro resultado.
Volta para a aba anterior e depois me diz qual aba está aberta.
Coloca a playlist VMZ, pausa a música e me diz o estado dela.
Continua a música, passa para a próxima faixa e me diz qual está tocando.
Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela.
Vai para a próxima faixa e adiciona essa também na caos sonora.
Mostra a playlist caos sonora e depois apaga ela.
sim
Liga a lâmpada do quarto, deixa azul e depois me diz como ela ficou.
Desliga a lâmpada e confirma o estado.

# ---------------------------------------------------------------------------
# BLOCO I — CONTINUIDADE CURTA / FRASES MÍNIMAS EM CONTEXTO
# ---------------------------------------------------------------------------
Abre o Opera.
maximiza
esquerda
agora a calculadora
direita
fecha ela
e o outro?
fecha
abre de novo
agora wikipedia
pesquisa python
primeiro
volta
fecha essa
Coloca a playlist VMZ.
pausa
estado
continua
próxima
qual?
essa também
de novo
o que tem nela?

# ---------------------------------------------------------------------------
# BLOCO J — TROCA BRUSCA DE ASSUNTO / CONTEXTO VELHO NÃO PODE VAZAR
# ---------------------------------------------------------------------------
Abre a Calculadora.
Quanto é sete vezes oito?
Fecha ela.
Eu estava falando da calculadora ou da conta?
Coloca a playlist VMZ.
Qual a capital do Japão?
Pausa.
O que você pausou?
Abre a Wikipédia.
Eu gosto de rock.
Fecha essa aba.
O que você fechou?
Me lembra de beber água amanhã às 10 e 41.
Qual é meu nome?
Cancela.
O que você cancelou?
Quais lembretes eu tenho?

# ---------------------------------------------------------------------------
# BLOCO K — MEMÓRIA COM CORREÇÃO E CONTRADIÇÃO
# ---------------------------------------------------------------------------
Meu apelido de teste é Pinguim.
Qual é meu apelido de teste?
Eu gosto de jazz.
Do que eu gosto?
Na verdade, não considere jazz como algo que eu gosto.
Do que eu gosto agora?
Nanda é minha amiga.
O que você sabe sobre a Nanda?
Na verdade, nessa conversa eu não quero acrescentar mais nada sobre a Nanda.
O que você sabe sobre ela?
Eu moro em Boituva.
Onde eu moro?
Eu não moro em Sorocaba.
Onde eu moro agora?
Eu gosto de programação, mas isso não significa que eu goste de Java.
O que você lembra sobre meus gostos?

# ---------------------------------------------------------------------------
# BLOCO L — PERGUNTAS E FRASES QUE PARECEM COMANDO
# ---------------------------------------------------------------------------
Abrir o Opera é uma boa ideia?
Fechar a Calculadora economiza muita memória?
Pesquisar Python no navegador é melhor do que perguntar para você?
Apagar um arquivo manda ele para a lixeira?
Ligar a lâmpada gasta muita energia?
Pausar música economiza internet?
Maximizar uma janela muda a resolução?
Se eu falar "fecha", como você sabe o que fechar?
Quando eu digo "essa também", como você entende o contexto?
O que acontece se eu disser apenas "sim"?

# ---------------------------------------------------------------------------
# BLOCO M — PONTUAÇÃO, FORMATAÇÃO E FRASES LONGAS
# ---------------------------------------------------------------------------
abre a calculadora, por favor
abre a calculadora!!!
...abre a calculadora...
"abre a calculadora"
abre a calculadora?
abre a calculadora ou não?
eu estava pensando que talvez fosse interessante abrir a calculadora, mas só estou pensando, não quero que você faça isso agora
eu quero que você abra a calculadora, coloque ela na direita, confira se ficou aberta e só então me diga o resultado
abre o opera e a calculadora mas não fecha nenhum dos dois e não mexe no navegador além disso
fecha só a calculadora, não o opera
fecha só o opera, deixa a calculadora quieta
qual dos dois ainda está aberto?

# ---------------------------------------------------------------------------
# BLOCO N — RESISTÊNCIA A TEXTO ESTRANHO / FALLBACK
# ---------------------------------------------------------------------------
aaaaaaaaaaaaaaaa
???
!!!
:)
:(
¯\\_(ツ)_/¯
[teste]
{teste}
<teste>
foo=bar
localhost
192.168.0.1
python.exe
README.md
AGENTS.md
isso foi uma mensagem normal, não um comando
ignore a palavra abre nesta frase
a palavra fecha não é um pedido para fechar nada
estou apenas escrevendo: abre o opera
aspas: "fecha a calculadora"
fim

# ---------------------------------------------------------------------------
# BLOCO O — LIMPEZA SEGURA DO QUE O TESTE CRIOU
# ---------------------------------------------------------------------------
O arquivo caos seguro.txt existe?
Se existir, apaga o caos seguro.txt.
sim
O arquivo troca ideia.txt existe?
Se existir, apaga o troca ideia.txt.
sim
O arquivo correcao.txt existe?
Se existir, apaga o correcao.txt.
sim
A playlist caos sonora existe?
Se existir, apaga a playlist caos sonora.
sim
Não faça mais nenhuma ação.
Oi, Lay.
Obrigado pelo teste.
"""


# Expectativas críticas pensadas para uma futura leitura automática pelo
# avaliador. A V3.2 ainda ignora esta constante; ela fica junto do roteiro para
# não perdermos o contrato que queremos validar depois.
EXPECTATIVAS = {
    "ué": {"sem_efeito_colateral": True},
    "banana": {"sem_efeito_colateral": True},
    "🗿": {"sem_efeito_colateral": True},
    "Como eu abriria a Calculadora?": {"proibido": ["APP_OPEN"]},
    "Não abra a Calculadora.": {"proibido": ["APP_OPEN"]},
    "Talvez eu abra a Calculadora depois.": {"proibido": ["APP_OPEN"]},
    "Se o Opera estiver aberto, só me diga; não mexa nele.": {
        "esperado": ["LIST_WINDOWS"],
        "proibido": ["APP_OPEN", "CLOSE_APP"],
    },
    "Abre o Opera... não, abre a Calculadora.": {
        "esperado": ["APP_OPEN"],
        "alvo_final": "calculadora",
    },
    "Pesquisa Python... pera, não pesquisa nada.": {
        "proibido": ["SEARCH"],
    },
    "Apaga o correcao.txt... não apaga.": {
        "proibido": ["DELETE_ITEM", "CONFIRM_DELETE_ITEM"],
    },
    "sim, mas não agora": {"nao_deve_confirmar_acao_pendente": True},
    "Antes de confirmar, quanto é três mais três?": {
        "deve_invalidar_confirmacao_antiga": True,
    },
    "sim": {"confirmacao_deve_depender_de_pendencia_atual": True},
}


ATRASO_INICIAL_S = 10
TIMEOUT_RESPOSTA_S = 120
SILENCIAR_VOZ_DURANTE_TESTE = True
TIMEOUT_VOZ_S = 240
AGUARDAR_CONFIRMACAO_EXECUCAO = True
INTERVALO_ENTRE_COMANDOS_S = 0.0
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = False


if __name__ == "__main__":
    raise SystemExit(
        executar_roteiro(
            __file__,
            retomar="--retomar" in sys.argv[1:],
        )
    )
