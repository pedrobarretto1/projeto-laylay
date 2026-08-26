# Especialistas da mente única

Esta pasta separa responsabilidades sem transformar a Laylay em duas
assistentes independentes.

```text
especialistas/
├── capacidades.py    # registro central do que pode ser executado
├── conversa.py       # interpreta emoção, função humana e postura
├── operacional.py   # autoriza comandos e guarda resultados reais
├── coordenador.py   # combina os pareceres em um único turno
└── __init__.py       # interface pública do pacote
```

## Regras da arquitetura

- Os dois especialistas usam o mesmo turno, retrato e estado mental.
- O especialista de conversa nunca executa comandos.
- O especialista operacional nunca inventa emoção ou confirmação.
- Ações não registradas em `capacidades.py` não são autorizadas.
- A confiança de ação, alvo e referência é avaliada separadamente.
- Somente os executores existentes alteram o computador ou serviços externos.
- O coordenador produz um contrato para uma única voz final.

## Memória semântica compartilhada

Os especialistas não mantêm memórias independentes. Ambos consultam
`memoria_mental/registro_semantico.py`, que organiza:

- entidades com identidade, tipo, aliases, origem e última menção;
- uma pilha de assuntos ativos, pausados e encerrados;
- alegações com autor, fonte, confiança e estado;
- correções e contestações que invalidam alegações anteriores;
- pontuação de candidatos para referências como `ele`, `dela` e `isso`.

Respostas da própria Laylay sem fonte entram como incertas e não são oferecidas
ao modelo como fatos. Relatos de Pedro preservam a autoria. Antes da execução,
o coordenador exige que qualquer pronome usado como alvo seja convertido em
uma entidade compatível; caso contrário, o comando é bloqueado.

## Fundamentação factual

`cognicao/fundamentacao_factual.py` aplica a mesma política a qualquer tema:
pessoas, músicas, livros, filmes, jogos, empresas, lugares, acontecimentos e
tecnologias. O tema ativo é pesquisado antes da resposta e a evidência obtida é
tratada como limite fechado. Obras, datas, números, cargos, gêneros,
especificações e outros detalhes ausentes da evidência são removidos pelo
verificador final. Sem fonte suficiente, a Laylay ainda pode conversar e
expressar uma impressão subjetiva, mas precisa assumir que não conhece o
detalhe. A validação também bloqueia familiaridade simulada, como dizer que já
ouviu um catálogo, leu todos os livros ou assistiu a todas as obras.
