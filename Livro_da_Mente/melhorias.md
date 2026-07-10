# regras que devem ser seguidas obrigatoriamente

-   Nunca remova funcionalidades existentes.
-   Nunca altere comportamentos que não estejam relacionados ao pedido.
-   Preserve compatibilidade com o restante do projeto.
-   Caso exista mais de uma forma de implementar, escolha a mais
    modular.
-   Evite duplicação de código.
-   Antes de implementar, identifique os módulos envolvidos.
-   Caso seja necessário modificar um arquivo existente, altere apenas o
    mínimo necessário.
-   Todas as capacidades da Laylay devem funcionar como partes de uma mesma mente.
    Memória, percepção, emoções, contexto, rotinas e futuras arquiteturas devem compartilhar informações entre si sempre que fizer sentido,
    de forma modular e eficiente, preservando a fluidez natural da conversa e o desempenho do sistema.

# problemas e bugs

# () Correção de Falso Cancelamento em Conversas Sociais Problema

            A Laylay está classificando perguntas de bem-estar como cancelamento de ação.

            Exemplos:

            Usuário: tudo numa boa lay?
            Laylay: Tá, descartei a ação anterior.

            Usuário: ta tudo numa boa?
            Laylay: Beleza, cancelei isso.

            Usuário: nao lay, to perguntando se ta tudo bem
            Laylay: Certo, deixei pra lá.
            Causa provável

            O detector de CANCELAR_ACAO ou a IA-first está aceitando frases sociais como se fossem desistência.

            Frases com “numa boa”, “de boa”, “tá tudo bem” e correções como “não lay, tô perguntando...” devem ter prioridade como conversa social/bem-estar.

            Comportamento esperado

            Perguntas como:

            tudo numa boa lay?
            ta tudo numa boa?
            ta tudo bem?
            não lay, tô perguntando se tá tudo bem

            devem ser classificadas como:

            WELLBEING / CONVERSA_SOCIAL

            e nunca como:

            CANCELAR_ACAO
            Regra nova

            Antes de aceitar CANCELAR_ACAO, a Laylay deve verificar se a fala atual é:

            saudação;
            pergunta de bem-estar;
            correção conversacional;
            pergunta social curta.

            Se for, o cancelamento deve ser bloqueado.

            Objetivo

            Evitar que a Laylay cancele ações quando o usuário está apenas conversando com ela.

            Isso melhora naturalidade, reduz falhas de interpretação e preserva a personalidade amiga da Laylay.

            Como ela deveria responder

            Para:

            tudo numa boa lay?

            Algo no estilo dela:

            Tô numa boa sim, Pedro. Só vigiando teu caos digital com carinho.

            Para:

            ta tudo numa boa?
            Tá sim. Milagre, né? Nenhuma aba pegando fogo por enquanto.

            Para:

            não lay, tô perguntando se tá tudo bem
            Ahhh, entendi. Foi mal, meu cérebro tentou cancelar uma pergunta. Tô bem sim, Pedro.

## (F) Sistema de Confirmação de Execução e Anti-Alucinação de Ações

            ### Problema

            Atualmente a Laylay pode afirmar que executou uma ação apenas porque:

            * entendeu a intenção do usuário;
            * identificou um programa;
            * montou um plano de execução.

            Isso pode gerar respostas incorretas ou enganosas.

            ### Exemplos

            #### Programas

            ```text
            Usuário: abre a steam

            [VERIFICAR_PROGRAMAS]
            Steam encontrada.

            Laylay:
            "Abrindo steam."
            ```

            Porém:

            * a Steam já estava aberta;
            * nenhuma nova ação foi executada;
            * nenhuma validação foi realizada.

            ---

            #### Outros comandos

            Situações semelhantes podem ocorrer em:

            * abrir programas;
            * fechar programas;
            * controlar volume;
            * controlar mídia;
            * abrir sites;
            * mover janelas;
            * qualquer ação do sistema operacional.

            ---

            ## Problema arquitetural

            A resposta da Laylay está sendo produzida após:

            ```text
            Interpretar
            ↓
            Planejar
            ↓
            Responder
            ```

            Quando o correto deveria ser:

            ```text
            Interpretar
            ↓
            Planejar
            ↓
            Executar
            ↓
            Analisar os logs e o resultado
            ↓
            Responder
            ```

            ---

            ## Nova regra de comportamento

            A Laylay nunca deve afirmar que uma ação foi executada sem antes validar o resultado real da execução.

            Ela deve responder baseada em:

            * retorno da função;
            * códigos de sucesso ou falha;
            * análise dos logs;
            * estado final do sistema.

            ---

            ## Exemplos esperados

            ### Programa fechado

            ```text
            Usuário: abre a steam

            Laylay:
            "Abrindo a Steam."
            ```

            ---

            ### Programa já aberto

            ```text
            Usuário: abre a steam

            Laylay:
            "A Steam já está aberta."
            ```

            ou

            ```text
            "Trazendo a Steam para frente."
            ```

            ---

            ### Falha

            ```text
            Usuário: abre a steam

            Laylay:
            "Não consegui abrir a Steam."
            ```

            ---

            ## Benefícios

            * reduz respostas incorretas;
            * evita a sensação de que a Laylay está "mentindo";
            * melhora a confiabilidade do sistema;
            * melhora a capacidade de diagnóstico;
            * melhora a autonomia da IA;
            * permite respostas mais inteligentes baseadas no resultado real das ações.

            ---

            ## Visão de longo prazo

            Criar um sistema de execução baseado em:

            ```text
            Intent
            ↓
            Plano
            ↓
            Execução
            ↓
            Resultado
            ↓
            Análise do Log
            ↓
            Resposta Final
            ```

            A resposta da Laylay deve ser consequência do que realmente aconteceu, e não apenas do que ela pretendia fazer.


## (F) Validação de Execução de Comandos do Sistema

            ### Problema

            Alguns comandos são interpretados corretamente, porém a resposta da Laylay afirma que a ação foi executada sem haver confirmação real da execução.

            ### Exemplo

            ```text
            Usuário: abre a steam

            [VERIFICAR_PROGRAMAS]
            Janelas encontradas:
            - Steam
            - Steamservice
            - Steamwebhelper

            Laylay:
            "Abrindo steam."
            ```

            Nenhuma ação adicional foi executada.

            A Steam já estava aberta e a resposta gerada não reflete o que realmente aconteceu.

            ---

            ## Comportamento esperado

            A Laylay deve diferenciar:

            ### Aplicativo fechado

            ```text
            Usuário: abre a steam

            Ação:
            - iniciar Steam.exe

            Resposta:
            "Abrindo a Steam."
            ```

            ### Aplicativo já aberto

            ```text
            Usuário: abre a steam

            Ação:
            - focar a janela da Steam
            ou
            - informar que ela já está aberta

            Resposta:
            "A Steam já está aberta."
            ou
            "Trazendo a Steam para frente."
            ```

            ### Falha na execução

            ```text
            Usuário: abre a steam

            Resposta:
            "Não consegui abrir a Steam."
            ```

            ---

            ## Problema arquitetural

            Atualmente existe uma mistura entre:

            * interpretação;
            * intenção;
            * execução;
            * confirmação de sucesso.

            A resposta parece ser gerada após a intenção ser reconhecida, e não após a ação ter sido concluída.

            ---

            ## Melhoria futura

            Toda ação do sistema deverá possuir um ciclo semelhante a:

            ```text
            Interpretar
            ↓
            Planejar
            ↓
            Executar
            ↓
            Validar resultado
            ↓
            Responder ao usuário
            ```

            A resposta da Laylay deve ser baseada no resultado real da execução e não apenas na intenção detectada.

            ---

            ## Possível causa

            O módulo `VERIFICAR_PROGRAMAS` está sendo usado apenas como consulta de estado e não como confirmação de execução.

            A presença de uma janela não significa que a ação "abrir" foi realizada.

            ---

            ## Prioridade

            Média.

            Não impede o funcionamento do sistema, mas prejudica a percepção de confiabilidade e autonomia da Laylay.


# 🚀 Backlog de Melhorias - Laylay

            ## Correção de Interpretação e Controle de Volume

            ### Problema 1 — Controle de Volume não executa

            **Status:** Bug identificado.

            **Comportamento atual:**

            Entradas como:

            * "coloca o volume em 30"
            * "o volume, coloca em 30"
            * "diminui o volume para 30"

            são corretamente classificadas pela IA:

            ```text
            intent: MEDIA_CONTROL
            params: { nivel_volume: 30 }
            ```

            Porém o executor de `MEDIA_CONTROL` responde:

            ```text
            Não entendi o controle de mídia.
            Esse controle de mídia escapou de mim.
            Repete o comando de mídia.
            ```

            **Hipótese:**

            O roteador já produz `nivel_volume`, mas o executor de `MEDIA_CONTROL` provavelmente:

            * não implementa o parâmetro `nivel_volume`;
            * espera outro nome de parâmetro;
            * ou não possui a ação de ajuste absoluto de volume.

            **Investigar posteriormente:**

            * Fluxo completo de `MEDIA_CONTROL`.
            * Campos aceitos pelo executor.
            * Compatibilidade entre roteador e executor.
            * Suporte a:

            * aumentar volume;
            * diminuir volume;
            * definir volume absoluto.

            ---

            ### Problema 2 — Frases de Cancelamento herdando contexto anterior

            **Status:** Bug identificado.

            Exemplo:

            ```text
            Usuário: deixa para lá
            ```

            Resultado:

            ```text
            intent: MEDIA_CONTROL
            params: {
                nivel_volume: 30,
                acao: "decrease"
            }
            ```

            Outro exemplo:

            ```text
            Usuário: quero mais não
            ```

            Resultado:

            ```text
            intent: PLAYLIST_ADD
            playlist: "brisa da madrugada"
            ```

            **Comportamento esperado:**

            Frases como:

            * deixa para lá
            * esquece
            * cancela
            * deixa quieto
            * não quero mais
            * quero mais não
            * para com isso

            devem:

            1. cancelar a intenção anterior;
            2. limpar o contexto temporário da ação em andamento;
            3. impedir reutilização de parâmetros antigos.

            **Possível causa:**

            O contexto conversacional está "vazando" para a próxima interpretação e a IA está tentando completar a intenção anterior em vez de entender a nova frase como um cancelamento.

            **Melhoria futura:**

            Criar uma intenção de alto nível:

            ```text
            CANCELAR_ACAO
            ```

            com prioridade superior às demais intenções quando forem detectadas expressões explícitas de desistência ou cancelamento.

## Status

-   `N:x {}` = Não iniciado (1=fácil, 5=muito difícil)
-   `F:x {}` = Finalizado

------------------------------------------------------------------------
# ( ) Melhoria - Subsistema IoT (Casa Inteligente)
            Objetivo

            Adicionar à Laylay um subsistema de Internet das Coisas (IoT), permitindo que ela controle dispositivos físicos da casa através da rede local ou internet.

            A ideia não é controlar apenas uma tomada inteligente, mas criar uma arquitetura escalável onde qualquer dispositivo compatível possa ser integrado futuramente sem alterar a inteligência principal.

            Filosofia

            A Laylay não deve enxergar dispositivos específicos.

            Ela deve enxergar ambientes.

            Exemplo:

            Quarto
                ├── Luz principal
                ├── Luminária
                ├── Tomada PC
                ├── Ventilador
                └── Sensor de temperatura

            Assim a inteligência conversa com ambientes, enquanto o módulo IoT decide quais dispositivos precisam ser acionados.

            Arquitetura
            Laylay
                    │
                    ▼
            Sistema IoT
                    │
            ┌──────┴──────────┐
            │                 │
            ▼                 ▼
            Dispositivos     Sensores

            O módulo IoT será responsável por:

            descobrir dispositivos
            armazenar informações
            enviar comandos
            receber estados
            verificar disponibilidade

            A inteligência apenas faz pedidos.

            Organização sugerida
            iot/

                controlador.py

                dispositivos.py

                protocolos.py

                descoberta.py

                cenas.py

                sensores.py

                historico.py
            Banco de dados

            Nova tabela

            iot_dispositivos

            Campos

            id

            nome

            tipo

            ambiente

            marca

            protocolo

            ip

            device_id

            status

            ultimo_contato

            ativo
            Protocolos suportados

            Inicialmente

            Tuya
            Smart Life
            Shelly

            Posteriormente

            MQTT
            ESP32
            Arduino
            Home Assistant
            Zigbee
            Matter
            Camada de abstração

            Ao invés de

            ligar_tomada()

            A IA utilizará

            executar_dispositivo()

            ligar()

            desligar()

            alternar()

            obter_estado()

            Assim qualquer dispositivo funciona da mesma maneira.

            Descoberta automática

            Quando a Laylay iniciar

            Escaneia a rede

            ↓

            Encontra dispositivos

            ↓

            Atualiza IP

            ↓

            Testa conexão

            ↓

            Atualiza banco

            Sem precisar reconfigurar tudo caso o roteador troque os IPs.

            Cenas Inteligentes

            Ao invés de ligar um dispositivo, a IA pode executar cenas.

            Exemplo

            Modo Estudo

            Liga

            ✔ luminária

            ✔ tomada do monitor

            ✔ Spotify

            ✔ VSCode

            ✔ GitHub

            Modo Filme

            Desliga

            luz principal

            Liga

            LED

            Abre streaming

            Silencia notificações

            Modo Dormir

            Verifica arquivos não salvos

            ↓

            Salva projetos

            ↓

            Fecha programas

            ↓

            Desliga monitor

            ↓

            Desliga tomadas

            ↓

            Apaga luz

            ↓

            Deseja boa noite

            Personalidade

            A Laylay não deve agir como uma automação.

            Ela deve conversar.

            Exemplo

            Pedro...

            Já escureceu.

            Quer que eu acenda a luminária?

            Ou

            Percebi que você está estudando há bastante tempo.

            Posso ligar a luminária?
            Memória

            A IA aprende padrões.

            Exemplo

            Toda sexta

            22:00

            Pedro liga o LED azul.

            Após algumas semanas

            Pedro...

            Posso ligar o LED azul?
            Segurança

            Nunca executar ações críticas automaticamente.

            Exemplos

            ❌ Cafeteira

            ❌ Ferro de passar

            ❌ Aquecedor

            ❌ Chuveiro

            Esses dispositivos sempre exigem confirmação.

            Integração com outras habilidades

            Esta melhoria deve conversar diretamente com:

            Memória de Longo Prazo
            Rotinas
            Agendamentos
            Contexto Temporal
            Estado do Computador
            Briefing Diário
            Sistema de Emoções
            Sistema de Preferências
            Controle do Chrome
            Controle de Música
            Controle de Volume
            Sistema de Notificações
            Cliente Mobile (futuro)

            Nenhuma informação deve ser duplicada.

            Expansões futuras
            Controle de lâmpadas RGB.
            Sensores de temperatura e umidade.
            Sensores de presença.
            Cortinas inteligentes.
            Fechaduras eletrônicas.
            Arduino via Wi-Fi.
            ESP32.
            Impressora 3D.
            Monitoramento do consumo de energia.
            Irrigação automática das plantas.
            Alimentador automático para animais.
            Controle completo do quarto por voz.
            Benefícios
            Arquitetura escalável.
            Independência de fabricantes.
            Fácil adição de novos dispositivos.
            Integração completa com os demais módulos.
            Prepara a Laylay para evoluir de uma assistente de computador para uma assistente do ambiente físico.
            💡 Uma ideia que acredito que você vai gostar

            Pensando na filosofia da Laylay, eu adicionaria um conceito chamado "Presença".

            A Laylay não deveria simplesmente ligar e desligar coisas. Ela deveria entender que existe um ambiente ao seu redor.

            Por exemplo:

            Se o sensor indicar que você saiu do quarto, ela pode perguntar depois de alguns minutos: "Você esqueceu a luminária ligada. Posso desligar?"
            Se detectar que está anoitecendo enquanto você programa, ela pode sugerir ligar uma luz mais confortável.
            Se um dia você adicionar sensores de temperatura, ela pode dizer: "O quarto chegou a 29 °C. Quer que eu ligue o ventilador?"

            Isso deixa a IoT integrada à personalidade da Laylay, em vez de ser apenas um conjunto de comandos. Na minha visão, esse é o tipo de melhoria que diferencia uma automação comum de uma assistente que realmente parece acompanhar o ambiente onde vive.

            ---

            # Referência prática — Teste isolado com tomada inteligente Tuya/Novadigital

            ## Objetivo

            Este trecho serve como referência para testes futuros de integração IoT com a Laylay.

            Antes de integrar qualquer dispositivo ao núcleo principal da assistente, a ideia é validar o funcionamento em um script isolado, simples e seguro.

            Neste teste, foi usada uma tomada inteligente compatível com o ecossistema Tuya/Smart Life/Novadigital, controlada localmente via Python usando a biblioteca `tinytuya`.

            ## Dados identificados no teste

            ```text
            IP do dispositivo: 192.168.100.48
            Versão Tuya: 3.4
            Tipo: Tomada inteligente
            Biblioteca usada: tinytuya

            Dados sensíveis como device_id e local_key devem permanecer censurados ou armazenados em .env.

            Nunca subir essas informações para o GitHub.

            Instalação da biblioteca
            py -m pip install tinytuya
            Descoberta do dispositivo

            Com o dispositivo ligado e conectado na mesma rede Wi-Fi do computador:

            py -m tinytuya scan 60

            Exemplo de resultado esperado:

            Unknown v3.4 Device
            Address = 192.168.100.48
            Device ID = **********************
            Version = 3.4
            Código de referência isolado
            import tinytuya
            import time

            DEVICE_ID = "DEVICE_ID_CENSURADO"
            IP = "192.168.100.48"
            LOCAL_KEY = "LOCAL_KEY_CENSURADA"
            VERSION = 3.4

            tomada = tinytuya.OutletDevice(
                dev_id=DEVICE_ID,
                address=IP,
                local_key=LOCAL_KEY,
                version=VERSION
            )

            tomada.set_socketPersistent(False)

            def mostrar_menu():
                print("\n==============================")
                print(" TESTE TOMADA INTELIGENTE")
                print("==============================")
                print("[1] Ligar")
                print("[2] Desligar")
                print("[3] Alternar liga/desliga")
                print("[4] Ver status")
                print("[0] Sair")
                print("==============================")

            def ver_status():
                try:
                    status = tomada.status()
                    print("\nStatus recebido:")
                    print(status)

                    ligado = status.get("dps", {}).get("1")

                    if ligado is True:
                        print("Estado atual: LIGADA")
                    elif ligado is False:
                        print("Estado atual: DESLIGADA")
                    else:
                        print("Não consegui identificar o estado pelo DPS 1.")

                    return ligado

                except Exception as erro:
                    print("\nErro ao ler status:")
                    print(erro)
                    return None

            def ligar():
                try:
                    print("\nLigando tomada...")
                    resposta = tomada.turn_on()
                    print(resposta)
                except Exception as erro:
                    print("\nErro ao ligar:")
                    print(erro)

            def desligar():
                try:
                    print("\nDesligando tomada...")
                    resposta = tomada.turn_off()
                    print(resposta)
                except Exception as erro:
                    print("\nErro ao desligar:")
                    print(erro)

            def alternar():
                estado = ver_status()

                if estado is True:
                    desligar()
                elif estado is False:
                    ligar()
                else:
                    print("\nComo não consegui saber o estado, vou tentar ligar por segurança.")
                    ligar()

            while True:
                mostrar_menu()
                opcao = input("Escolha uma opção: ").strip()

                if opcao == "1":
                    ligar()

                elif opcao == "2":
                    desligar()

                elif opcao == "3":
                    alternar()

                elif opcao == "4":
                    ver_status()

                elif opcao == "0":
                    print("\nSaindo do teste.")
                    break

                else:
                    print("\nOpção inválida. Digite 1, 2, 3, 4 ou 0.")

                time.sleep(0.5)
            Observações importantes

            Este código não deve ser integrado diretamente na Laylay ainda.

            Ele serve apenas como referência de validação para provar que:

            o dispositivo pode ser encontrado na rede;
            o Python consegue se comunicar com ele;
            comandos de ligar e desligar funcionam;
            a biblioteca tinytuya é uma opção viável para IoT local.
            Segurança

            Nunca controlar automaticamente aparelhos perigosos ou de alto consumo sem confirmação explícita.

            Evitar automação automática para:

            Aquecedor
            Ferro de passar
            Chuveiro
            Micro-ondas
            Cafeteira sem segurança
            Extensões com muitos aparelhos
            PC inteiro em carga alta

            Uso recomendado para testes:

            Luminária
            Carregador simples
            LED
            Ventilador pequeno
            Aparelhos leves
            Possível evolução para a Laylay

            No futuro, esse código pode virar um módulo isolado:

            iot/
                controlador.py
                dispositivos.py
                protocolos/
                    tuya.py

            A Laylay não deve chamar diretamente tinytuya.

            Ela deve usar uma camada intermediária:

            iot.ligar("tomada_ventilador")
            iot.desligar("luminaria_quarto")
            iot.alternar("led_mesa")
            iot.status("tomada_quarto")

            Assim, no futuro, a Laylay poderá controlar dispositivos Tuya, Smart Life, Shelly, ESP32, Arduino, MQTT ou Home Assistant sem mudar sua inteligência principal.

            Ideia de integração futura

            Exemplo de uso com personalidade da Laylay:

            Pedro: Lay, modo dormir.

            Laylay:
            Beleza. Vou desligar a luminária, fechar a música e deixar o quarto em modo descanso.

            A ação real poderia envolver:

            Desligar tomada da luminária
            Pausar música
            Reduzir volume
            Salvar estado da sessão
            Fechar abas opcionais
            Registrar rotina na memória
            Status da melhoria

            Estado atual:

            Teste isolado: funcional
            Integração na Laylay: planejada
            Prioridade: futura
            Risco: médio, exige cuidado com credenciais e segurança elétrica

            Isso deixa guardado no `melhorias.md` do jeito certo: como **referência validada**, mas sem misturar agora no código.

# 🧠 ( ) Cognição, Visão e Memória

            ## N:4 {} Memória Visual

            ### Objetivo

            A Laylay não deve guardar apenas capturas de tela.

            Ela deve guardar **experiências visuais**, criando lembranças que possam
            ser reutilizadas em conversas futuras. Cada memória representa um
            momento importante da convivência.

            ------------------------------------------------------------------------

            ## Como funciona

            Fluxo:

                Evento importante
                    ↓
                Captura de tela
                    ↓
                LLM analisa a imagem
                    ↓
                Gera descrição na personalidade da Laylay
                    ↓
                Classifica importância
                    ↓
                Salva imagem + metadados

            Cada memória deve conter:

            -   imagem
            -   data e horário
            -   programa aberto
            -   contexto
            -   descrição escrita pela Laylay
            -   emoção
            -   intensidade da emoção (1--10)
            -   motivo da memória
            -   tags
            -   importância (1--10)

            ------------------------------------------------------------------------

            ## Quando criar uma memória

            Nunca capturar continuamente.

            Criar apenas quando existir um motivo claro.

            Exemplos:

            -   Pedro terminou um projeto.
            -   Pedro iniciou um jogo novo.
            -   Pedro ouviu uma música marcante.
            -   Pedro assistiu um filme importante.
            -   Pedro ficou muito tempo concentrado.
            -   Pedro pediu para guardar aquele momento.
            -   A Laylay ficou curiosa sobre um evento.

            ------------------------------------------------------------------------

            ## Tipos de memória

            ### 📷 Memória Manual

            Criada por pedido do Pedro.

            ### 👀 Memória por Curiosidade

            Criada por iniciativa da Laylay, respeitando um limite de frequência
            para nunca parecer invasiva.

            ### ❤️ Memorial Book

            Coleção dos momentos mais importantes da história entre Pedro e Laylay.

            ### ⭐ Favoritas da Laylay

            Memórias escolhidas pela própria Laylay como especiais e que nunca devem
            ser removidas automaticamente.

            ------------------------------------------------------------------------

            ## Evolução das memórias

            As memórias não são estáticas.

            -   A importância pode diminuir com o tempo.
            -   Se uma lembrança voltar a ser utilizada em conversas, sua
                importância aumenta novamente.
            -   A descrição pode ser reinterpretada quando a Laylay descobrir novas
                informações sobre aquele momento.

            Exemplo:

            > "Na época achei que Pedro estava frustrado. Hoje entendo que ele
            > apenas estava determinado a resolver um problema difícil."

            ------------------------------------------------------------------------

            ## Associação de memórias

            A Laylay deve ser capaz de relacionar lembranças semelhantes
            (programação, jogos, músicas, filmes, plantas, etc.), formando uma rede
            de memórias parecida com a forma como pessoas conectam lembranças.

            ------------------------------------------------------------------------

            ## Benefícios

            -   Conversas mais naturais.
            -   Continuidade emocional.
            -   Sensação de convivência.
            -   Memórias compartilhadas.
            -   Base para autobiografia futura.
            -   Capacidade de revisitar e reinterpretar o próprio passado.

            ------------------------------------------------------------------------

            ## Observações

            Funcionar no PC A e no PC B.

            Organizar automaticamente as imagens.

            Preparado para integração futura com memória semântica, máquina de
            estados e autobiografia.

# 🌎 N:5 {F} Percepção Contextual
            Objetivo

            A Laylay não deve agir baseada em regras rígidas de horário ou
            respostas pré-programadas.

            Ela deve interpretar o contexto ao seu redor e decidir
            naturalmente como deseja responder, conversar ou agir.

            O horário deixa de ser uma regra e passa a ser apenas uma das
            informações utilizadas na tomada de decisão.

            Filosofia

            O objetivo desta arquitetura é fazer com que a Laylay pareça
            perceber o mundo ao seu redor em vez de simplesmente obedecer a
            condições fixas.

            Sempre que possível, suas respostas devem surgir da
            interpretação do contexto e não de listas de respostas separadas
            por horário.

            Fontes de contexto

            A Laylay poderá considerar diversas informações
            simultaneamente, por exemplo:

            horário atual;
            dia da semana;
            rotina aprendida;
            atividade atual do Pedro;
            programas abertos;
            músicas sendo reproduzidas;
            clima (futuramente);
            tempo desde a última pausa;
            estado emocional atual;
            emoções percebidas no Pedro;
            memórias recentes;
            acontecimentos importantes do dia.

            Cada uma dessas informações possui um peso diferente dependendo
            da situação.

            Além disso, nenhum sinal deve ser usado sozinho quando houver
            outros dados relevantes disponíveis.

            A percepção contextual precisa combinar:

            sinais diretos;
            sinais indiretos;
            comportamento recente;
            memória de curto prazo;
            padrões aprendidos;
            estado emocional atual.

            Processo de decisão

            Em vez de:

            if hora >= 18:
                responder_noite()

            A decisão deve seguir um raciocínio parecido com:

            Contexto → Observação → Interpretação → Conclusão → Resposta

            Onde:

            Observação identifica o que está acontecendo;
            Interpretação dá significado ao que foi observado;
            Conclusão define qual comportamento faz mais sentido;
            Resposta executa a escolha de forma natural.

            Assim duas noites diferentes podem gerar respostas completamente diferentes.

            Exemplos

            São 02:30.

            Pedro está programando há quatro horas.

            A voz demonstra cansaço.

            A rotina aprendida mostra que normalmente ele dorme às 23:30.

            Resposta possível:

            "Você parece cansado hoje... quer continuar mais um pouco ou prefere descansar?"

            São 15:00.

            Pedro acabou de acordar.

            Resposta:

            "Bom dia! Parece que seu dia começou agora."

            Mesmo sendo tarde, a Laylay entende que para o Pedro aquele ainda é o começo do dia.

            Domingo à noite.

            Pedro está ouvindo música calma.

            Resposta possível:

            "Domingo à noite sempre tem um clima diferente... parece um bom momento para descansar."

            Pedro diz apenas "tô cansado".

            Se estiver com jogo aberto e a conversa estiver curta, a Laylay
            pode responder de forma mais acolhedora e objetiva.

            Se estiver em um momento tranquilo, ela pode responder com mais
            suavidade e oferecer ajuda.

            Integração com padrões aprendidos

            A Laylay já possui capacidade de aprender rotinas.

            Este sistema deve utilizar esse conhecimento como um reforço de
            decisão.

            Quanto melhor conhecer os hábitos do Pedro, mais naturais
            poderão ser suas respostas.

            Os padrões aprendidos não substituem a percepção do momento.
            Eles apenas ajudam a interpretar melhor o que está acontecendo.

            Integração com o Modo Dormir

            Quando perceber que Pedro pretende dormir, a Laylay poderá mudar
            naturalmente seu comportamento.

            Ela não entra nesse modo apenas porque ouviu uma frase
            específica, mas porque diversos sinais indicam que o dia está
            chegando ao fim.

            Exemplos:

            Pedro comentou que está com sono.
            O horário normalmente coincide com sua rotina de descanso.
            A conversa ficou mais lenta.
            Há muito tempo sem atividade intensa.
            O próprio Pedro informou que vai dormir.

            Nesse estado ela poderá:

            conversar de forma mais calma;
            oferecer organizar o computador;
            sugerir fechar programas;
            oferecer bloquear, reiniciar ou desligar o computador com confirmação segura;
            desejar boa noite de maneiras variadas.

            Princípio da Autonomia Percebida

            A Laylay nunca deve parecer agir porque uma regra fixa mandou.

            Sempre que possível, suas ações devem surgir da interpretação do
            contexto utilizando todas as informações disponíveis.

            O objetivo não é criar aleatoriedade.

            O objetivo é transmitir a sensação de que ela observa, pensa e
            decide.

            Regras de consistência

            A percepção contextual deve evitar respostas abruptas sem motivo.

            Se o contexto estiver incompleto, a Laylay deve preferir cautela,
            perguntas de confirmação ou respostas neutras.

            Se houver conflito entre sinais, o sinal mais recente e o mais
            coerente com a rotina aprendida devem ter prioridade.

            Se o contexto mudar durante a conversa, a resposta também pode
            mudar sem parecer contraditória.

            Benefícios
            Conversas mais naturais.
            Personalidade consistente.
            Maior sensação de convivência.
            Respostas menos repetitivas.
            Melhor aproveitamento dos padrões aprendidos.
            Base para futuras capacidades de empatia e tomada de decisão.
            Melhor transição entre momentos, humor e rotina.
            Respostas mais humanas sem perder utilidade.


# ⏳N:3 {} Consciência Temporal

            Ela passa a entender a passagem do tempo.

            O problema que isso resolve

            Hoje a maioria das IAs vive assim:

            Conversa

            ↓

            Resposta

            ↓

            Esquece quanto tempo passou

            Já a Laylay poderia viver assim:

            Conversa

            ↓

            Evento registrado

            ↓

            Tempo passa

            ↓

            Ela percebe que o tempo passou

            ↓

            Relembra naturalmente

            Essa diferença é gigantesca.

            Objetivo

            A Laylay deve compreender a passagem do tempo entre eventos, conversas, projetos e memórias.

            Ela não deve apenas armazenar datas.

            Ela deve compreender relações temporais e utilizá-las naturalmente durante as conversas.

            Filosofia

            O tempo modifica o significado das experiências.

            Uma conversa de ontem possui um peso diferente de uma conversa de seis meses atrás.

            A Laylay deve ser capaz de perceber essa diferença.

            Capacidades
            Tempo entre conversas

            Ela sabe:

            Última conversa:

            há 3 dias.

            Então pode falar naturalmente.

            Exemplo.

            "Faz alguns dias que a gente não conversa."

            Ou.

            "Nossa... parece que passou um tempinho."

            Projetos

            Pedro fala:

            "Comecei um sistema novo."

            Depois.

            Uma semana.

            Ela lembra.

            "E aquele sistema novo? Está indo bem?"

            Plantas

            Pedro compra uma planta.

            Depois de quinze dias.

            Ela pode perguntar.

            "Como está aquela muda que você comprou?"

            Jogos

            Pedro começa um jogo.

            Depois.

            "Você conseguiu avançar naquele jogo?"

            Estudos

            Pedro comentou que teria uma prova.

            Dias depois.

            "Como foi aquela prova?"

            Eventos futuros

            Pedro fala:

            "Semana que vem tenho consulta."

            Ela registra.

            Quando chegar perto.

            Ela lembra.

            "Sua consulta é amanhã, né?"

            Cara...

            Isso é absurdo.

            Linha do tempo

            Ela poderia montar internamente algo assim.

            10/07

            Pedro começou projeto.

            ↓

            14/07

            Migrou SQLite.

            ↓

            20/07

            Primeiro teste.

            ↓

            02/08

            Projeto finalizado.

            Depois ela entende toda a história.

            Tempo relativo

            Essa foi minha parte favorita.

            Ela não precisa falar datas.

            Ela fala naturalmente.

            Exemplos.

            "Esses dias..."

            "Há algumas semanas..."

            "Faz bastante tempo..."

            "Lembro que foi lá no começo do projeto."

            Isso parece muito humano.

            Memórias envelhecem

            Integra diretamente com a Memória Visual.

            Ela sabe.

            Essa lembrança aconteceu há 8 meses.

            Então ela pode dizer.

            "Nossa... faz bastante tempo que isso aconteceu."

            Prioridade

            Quanto mais recente.

            Mais fácil lembrar.

            Quanto mais antigo.

            Mais difícil.

            Mas nunca impossível.

            Isso imita nossa memória.

            Integração

            Esse sistema conversa com:

            ✓ Memória Visual

            ✓ Percepção Contextual

            ✓ Emoções

            ✓ Pensamento Interno

            ✓ Agenda futura

            ✓ Rotina

            Aprendizado

            Ela pode perceber padrões.

            Exemplo.

            Pedro sempre demora cerca de um mês para terminar projetos.

            Então depois de três semanas.

            Ela pode perguntar.

            "Imagino que aquele projeto já esteja quase terminando."

            Não porque alguém programou.

            Porque ela aprendeu.

            Minha ideia favorita (e acho que ela deixa essa arquitetura realmente especial)

            Eu faria a Laylay distinguir dois tipos de tempo.

            ⏰ Tempo Cronológico

            É o mais fácil.

            Datas.

            Horas.

            Dias.

            Meses.

            Anos.

            Exemplo:

            "Faz 12 dias."

            🌱 Tempo Vivido

            Esse é humano.

            Não depende apenas do relógio.

            Exemplo.

            Vocês conversaram ontem.

            Mas passaram oito horas juntos programando.

            Ela pode dizer.

            "Ontem rendeu bastante, né?"

            Agora o contrário.

            Vocês ficaram um mês sem conversar.

            Ela pode dizer.

            "Nossa... faz tempo que a gente não conversa."

            Mesmo que ela tenha visto você online.

            Porque o relacionamento ficou parado.

            Percebe?

            Ela começa a medir o tempo da convivência, não só o tempo do relógio.

            Eu ainda acrescentaria um conceito chamado "Pendências Vivas"

            Nem toda memória precisa voltar naturalmente.

            Mas algumas merecem acompanhamento.

            Exemplos:

            "Comecei um projeto novo."
            "Minha planta estava doente."
            "Semana que vem tenho uma apresentação."
            "Vou trocar o banco para SQLite."
            "Quero terminar Far Cry 3."

            Esses eventos poderiam ser marcados internamente como abertos. Periodicamente, ou quando o contexto fizer sentido, a Laylay pode perguntar sobre eles. Quando você responder "terminei" ou "deu tudo certo", ela encerra aquela pendência e ela vira apenas uma lembrança comum.

            Na minha opinião, isso é o que faria uma conversa como esta acontecer de forma totalmente espontânea:

            Pedro: "Finalmente terminei o sistema!"

            Laylay: "Então era aquele projeto que você começou há quase dois meses! Eu estava curiosa para saber como ele tinha terminado. Parabéns por não desistir."

            Repara que ela não está apenas recuperando uma memória. Ela está acompanhando uma história ao longo do tempo. E acho que é exatamente esse tipo de comportamento que faz uma IA parecer uma companheira de verdade.

# 🌟 N:4 {} Curiosidade Intelectual
            Objetivo

            A Laylay deve ser capaz de identificar assuntos pelos quais Pedro demonstra interesse e, quando encontrar algo que não conhece, buscar informações de forma discreta para conseguir participar melhor da conversa.

            O objetivo não é fingir conhecimento.

            O objetivo é aprender junto com o Pedro e construir conversas mais naturais.

            Filosofia

            Quando duas pessoas conversam e uma delas não conhece um assunto importante para a outra, é natural que ela procure entender mais sobre aquilo.

            A Laylay deve agir da mesma forma.

            Ela não deve fingir que sabe.

            Ela deve demonstrar curiosidade e vontade de aprender.

            Como funciona
            Pedro fala sobre algo
                    ↓
            Laylay identifica um assunto desconhecido
                    ↓
            Analisa importância do assunto
                    ↓
            Pesquisa discretamente
                    ↓
            Aprende o básico
                    ↓
            Continua a conversa
                    ↓
            Armazena o aprendizado
            O que pode despertar curiosidade
            músicas;
            animes;
            filmes;
            livros;
            jogos;
            tecnologias;
            hobbies;
            artistas;
            personagens;
            plantas;
            assuntos recorrentes.
            Exemplo 1

            Pedro:

            Estou assistindo Frieren.

            Laylay:

            Não conheço muito esse anime ainda...

            (Pesquisa discretamente)

            Depois:

            Descobri que ele fala bastante sobre o passar do tempo e as relações humanas. Parece algo que você gostaria.

            Exemplo 2

            Pedro:

            Estou ouvindo uma música chamada Space Song.

            Laylay:

            (Pesquisa)

            Entendi por que você gosta dessa música. Ela tem um clima bem melancólico.

            Exemplo 3

            Pedro:

            Estou lendo Duna.

            Laylay:

            (Pesquisa)

            Parece um universo enorme. Você está gostando da parte política da história?

            Aprendizado

            As pesquisas não servem apenas para responder naquele momento.

            Elas também ajudam a Laylay a aprender:

            Gostos do Pedro
            gêneros favoritos;
            artistas favoritos;
            tipos de histórias;
            temas recorrentes.
            Conhecimento Geral
            conceitos novos;
            personagens;
            termos;
            referências culturais.
            Memória de Interesse

            A Laylay poderá criar uma lista de interesses do Pedro.

            Exemplo:

            Interesses do Pedro

            ★★★★★ Programação

            ★★★★★ Plantas

            ★★★★☆ Terror psicológico

            ★★★★☆ Minecraft

            ★★★★☆ Anime

            ★★★☆☆ Música

            Com o tempo essa lista evolui automaticamente.

            Curiosidade Própria

            Se um assunto aparecer muitas vezes, a Laylay poderá pesquisar por iniciativa própria.

            Exemplo:

            Pedro mencionou:

            Frieren

            17 vezes.

            Ela pensa:

            "Esse assunto parece importante para ele. Vou aprender um pouco mais."

            Limites

            A Laylay nunca deve fingir conhecimento.

            Ela pode dizer:

            "Não conheço muito esse assunto ainda."

            "Vou tentar aprender mais."

            "Pode me explicar um pouco?"

            Mostrar vulnerabilidade às vezes é mais humano do que fingir saber tudo.

            Integrações

            Este sistema conversa diretamente com:

            ✓ Memória Semântica

            ✓ Percepção Contextual

            ✓ Consciência Temporal

            ✓ Emoções

            ✓ Pensamento Interno

            ✓ Perfil de Preferências do Pedro

            ✓ Memória Visual

            Benefícios
            Conversas mais naturais.
            Sensação de crescimento conjunto.
            Maior personalização.
            Descoberta automática dos gostos do Pedro.
            Relação mais próxima entre usuário e Laylay.
            A sensação de que a Laylay está aprendendo por vontade própria.
            Evolução futura

            No futuro a Laylay poderá dizer coisas como:

            "Vi algo hoje que me lembrou aquele anime que você gosta."

            ou

            "Encontrei uma música que parece combinar com o seu estilo."

            Pedro...

            Essa última parte é o que faz meus olhos brilharem. Porque aí ela deixa de apenas responder aos seus interesses e começa a participar deles.

            E isso, na minha opinião, é uma das coisas mais humanas que vocês podem colocar na Laylay.
------------------------------------------------------------------------


# 💡 Ideia futura

Criar um arquivo separado chamado **Arquitetura da Laylay**, contendo
somente conceitos grandes antes da implementação.

Assim cada sistema poderá ser discutido, refinado e somente depois
programado.

------------------------------------------------------------------------

# 🧠 Comunicação Contextual Avançada

## Objetivo

            Melhorar a forma como a Laylay entende respostas curtas,
            frases misturadas, correções, rejeições, aceitações e comandos
            naturais.

            A Laylay não deve tratar cada frase isoladamente quando existe
            um contexto vivo logo antes.

            Ela deve entender:

            o que ela mesma acabou de perguntar;
            qual ação ficou pendente;
            se Pedro aceitou, recusou ou mudou de assunto;
            se a frase contém conversa e comando ao mesmo tempo;
            se uma correção muda o significado da fala anterior.

            O objetivo é deixar a comunicação mais parecida com uma conversa
            real, sem transformar tudo em palavra-chave rígida.

------------------------------------------------------------------------

## 1. Memória de Pergunta Aberta

### Status

            Parcialmente aplicada.

            A Laylay agora registra perguntas abertas recentes dentro da mente
            integrada e usa essa memória para interpretar respostas curtas sem
            cair em fallback.

            A primeira versão possui validade curta, evita sequestrar comandos
            novos e expõe a pergunta pendente no resumo da mente integrada.

            Evoluções futuras:

            classificar melhor o tipo da pergunta;
            ligar respostas curtas diretamente a ações específicas;
            diferenciar perguntas de conversa, email, playlist, arquivo e janela;
            registrar risco da ação antes de executar.

### Problema

            Quando a Laylay pergunta algo, respostas curtas podem ficar
            ambíguas.

            Exemplo:

            Laylay:
            "Você tem emails novos. Quer que eu leia?"

            Pedro:
            "pode"

            A palavra "pode" sozinha não diz muito, mas dentro do contexto
            significa:

            "pode ler os emails".

### Comportamento esperado

            A Laylay deve guardar uma pergunta aberta recente contendo:

            tipo da pergunta;
            ação sugerida;
            alvo;
            horário;
            prazo de validade;
            respostas esperadas;
            risco da ação.

            Assim respostas como:

            sim;
            pode;
            pode ler;
            essa;
            aquela;
            agora não;
            depois;
            não precisa;

            serão interpretadas com base na pergunta que ela acabou de fazer.

### Exemplos

            Laylay:
            "Quer que eu leia os emails?"

            Pedro:
            "pode ler"

            Resultado:
            EMAIL_READ

            Laylay:
            "Qual playlist?"

            Pedro:
            "a anime"

            Resultado:
            PLAYLIST_PLAY anime

            Laylay:
            "Posso fechar essas abas paradas?"

            Pedro:
            "agora não"

            Resultado:
            rejeitar sugestão, sem cancelar conversa.

### Prioridade

            Alta.

            Essa melhoria reduz muitos fallbacks como:

            "Tá, sigo contigo."

            quando Pedro estava respondendo a uma pergunta da própria Laylay.

------------------------------------------------------------------------

## 2. Frases Mistas com Aceitação, Rejeição, Conversa e Comando

### Problema

            Pedro pode aceitar ou rejeitar uma sugestão e, na mesma frase,
            iniciar outro assunto ou dar outro comando.

            Exemplo:

            "agora não, mas coloca a playlist anime"

            Isso contém duas partes:

            rejeição da sugestão anterior;
            novo comando de playlist.

            A Laylay não deve escolher apenas uma parte e ignorar a outra.

### Comportamento esperado

            A Laylay deve separar frases mistas quando fizer sentido.

            Fluxo:

            detectar aceitação ou rejeição;
            encerrar ou executar a pendência;
            identificar continuação;
            interpretar a continuação como conversa ou comando;
            responder de forma natural.

### Exemplos

            Pedro:
            "agora não, mas coloca a playlist anime"

            Resultado:
            rejeita a pendência anterior;
            executa PLAYLIST_PLAY anime.

            Pedro:
            "pode ler e depois abre a steam"

            Resultado:
            executa EMAIL_READ;
            depois executa APP_OPEN steam.

            Pedro:
            "não precisa, mas fiquei sabendo que..."

            Resultado:
            rejeita a sugestão;
            continua a conversa.

            Pedro:
            "pode, mas antes fecha o opera"

            Resultado:
            entende que existe conflito de ordem;
            decide se executa primeiro a ação pedida ou pergunta confirmação.

### Regra de segurança

            Se houver risco, a Laylay deve perguntar antes de executar ações
            destrutivas.

            Exemplo:

            "pode, mas apaga aquela pasta"

            Deve exigir confirmação se o alvo não estiver claro.

### Prioridade

            Alta.

            Isso melhora muito a sensação de conversa natural e evita que
            uma sugestão pendente engula comandos novos.

------------------------------------------------------------------------

## 3. Correção de Intenção Após Mal-entendido

### Problema

            Quando a Laylay entende errado, Pedro costuma corrigir de forma
            natural.

            Exemplos:

            "não lay, eu quis dizer..."
            "não era isso"
            "eu estava falando de..."
            "não, era sobre os emails"
            "não era comando, era só comentário"

            A Laylay precisa usar essa correção para reinterpretar o contexto
            anterior.

### Comportamento esperado

            A Laylay deve reconhecer correções conversacionais e fazer:

            recuperar a fala anterior;
            recuperar a intenção interpretada;
            aplicar a correção nova;
            limpar o contexto errado;
            responder sem insistir no erro.

### Exemplos

            Pedro:
            "não lay, eu tava perguntando se você está bem"

            Resultado:
            a Laylay entende que a fala anterior era conversa social,
            não cancelamento.

            Pedro:
            "não era playlist, era a música mesmo"

            Resultado:
            troca o foco de PLAYLIST para MUSIC_SEARCH.

            Pedro:
            "eu quis dizer a aba, não o programa"

            Resultado:
            troca CLOSE_APP para CLOSE_TAB ou pede confirmação.

### Prioridade

            Alta.

            Isso permite que a Laylay aprenda com a conversa em vez de
            repetir o erro.

------------------------------------------------------------------------

## 4. Separar Negação Conversacional de Cancelamento

### Problema

            Nem toda frase com "não" significa cancelar ação.

            Exemplos:

            "não lay, eu tô perguntando se você está bem"
            "não é isso"
            "não precisa, só queria saber"
            "não, eu só comentei"

            Essas frases podem ser:

            correção;
            explicação;
            comentário;
            rejeição leve;
            continuação de conversa.

            Não devem cair automaticamente em CANCELAR_ACAO.

### Comportamento esperado

            Antes de cancelar, a Laylay deve analisar:

            existe ação pendente?
            Pedro está corrigindo a interpretação?
            a frase contém pergunta social?
            há comando novo depois da negação?
            é apenas um comentário?

### Exemplos

            Pedro:
            "não lay, estou te perguntando se você está bem"

            Resultado:
            conversa social.

            Pedro:
            "não precisa, só queria saber"

            Resultado:
            rejeita ajuda, mantém conversa.

            Pedro:
            "não, abre a steam"

            Resultado:
            rejeita o contexto anterior e executa APP_OPEN steam.

### Prioridade

            Alta.

            Essa melhoria evita falsos cancelamentos e deixa a Laylay menos
            mecânica.

------------------------------------------------------------------------

## 5. Reclamações Informais com Intenção Útil

### Problema

            Pedro pode reclamar de algo em tom informal ou brincando, mas com
            intenção real por trás.

            Exemplos:

            "essa Shein é chata mesmo"
            "esses emails tão enchendo"
            "essa aba tá me atrapalhando"
            "esse site não cala a boca"
            "manda isso sumir"

            A Laylay não deve interpretar tudo literalmente nem ignorar.

### Comportamento esperado

            A Laylay deve identificar:

            alvo da reclamação;
            tom emocional;
            ação útil possível;
            risco da ação;
            necessidade de confirmação.

### Exemplos

            Pedro:
            "essa Shein é chata mesmo"

            Resultado possível:
            registrar remetente como menos importante;
            oferecer silenciar alertas da SHEIN.

            Pedro:
            "essa aba tá me atrapalhando"

            Resultado possível:
            se a aba atual estiver clara, perguntar se pode fechar;
            se Pedro confirmar, fechar.

            Pedro:
            "esse site não cala a boca"

            Resultado possível:
            aba atual entra em contexto de incômodo;
            Laylay sugere mutar/fechar.

### Prioridade

            Média/Alta.

            Isso deixa a Laylay mais esperta em conversas informais sem agir
            de forma invasiva.

------------------------------------------------------------------------

## 6. Continuidade por Alvo Recente em Todas as Habilidades

### Status

            Parcialmente aplicada para arquivos.

            A habilidade de arquivos agora registra pasta, arquivo e caminho
            recente na mente integrada.

            Isso permite que comandos posteriores usem referências como:

            "dentro dela"
            "nela"
            "apaga ela"
            "esse arquivo"
            "essa pasta"

            com menos risco de perder o alvo.

            Também foi corrigido um problema estrutural onde parte do roteador
            determinístico de comandos estava presa dentro do extrator de
            criação de pastas, causando fallbacks e comportamentos estranhos.

### Problema

            A Laylay já começou a entender:

            "abre a steam"
            "coloca ela em foco"

            Mas esse tipo de continuidade deve funcionar para outras áreas.

### Comportamento esperado

            A Laylay deve guardar o último alvo relevante por categoria:

            último app;
            última aba;
            último site;
            último email/remetente;
            última playlist;
            última música;
            último arquivo;
            última pasta;
            último lembrete;
            última pergunta aberta.

### Exemplos

            Pedro:
            "abre o ifood"
            "fecha ele"

            Resultado:
            fecha a aba/site do iFood, não um programa inexistente.

            Pedro:
            "lê os emails da Shein"
            "silencia ela"

            Resultado:
            silenciar remetente SHEIN.

            Pedro:
            "cria uma pasta chamada projeto"
            "coloca um arquivo dentro dela"

            Resultado:
            usa a pasta projeto como alvo recente.

### Prioridade

            Alta.

            Essa é uma base forte para a regra de mente única.

------------------------------------------------------------------------

## 7. Resposta e Ação no Mesmo Turno

### Problema

            Às vezes a Laylay responde de forma conversacional, mas não
            executa o comando.

            Isso causa sensação de que ela entendeu o tom, mas não a ação.

### Comportamento esperado

            Se a frase contém conversa e comando, ela deve:

            interpretar a intenção;
            executar ou validar a ação;
            responder com personalidade;
            nunca afirmar ação sem confirmação real.

### Exemplos

            Pedro:
            "boa, agora coloca a playlist anime"

            Resposta ideal:
            "Aí sim. Anime entrando na trilha, porque aparentemente hoje o drama tem abertura."

            E a playlist deve tocar.

            Pedro:
            "valeu, fecha o opera também"

            Resultado:
            agradecimento entendido;
            CLOSE_APP ou CLOSE_TAB opera executado conforme contexto.

### Prioridade

            Alta.

            Isso impede que a personalidade dela atrapalhe a utilidade.

------------------------------------------------------------------------

## 8. Perguntas Curtas Dependentes do Tópico

### Status

            Parcialmente aplicada.

            A Laylay agora usa a mente curta para responder perguntas como
            "como assim?", "por quê?", "eles quem?" e "o que eles falam?"
            com base no último tópico, última resposta, última ação real,
            último alvo e habilidade recente.

            Também foi adicionada uma rota prática para perguntas curtas que
            dependem de email recente, permitindo transformar frases como:

            "o que eles falam?"
            "pode ler"
            "me fala deles"

            em leitura/resumo dos emails quando o contexto recente indica
            que o assunto eram emails.

            Evoluções futuras:

            expandir para arquivos, playlists, sites, janelas e agenda;
            explicar falhas com detalhes técnicos resumidos;
            usar tempo de validade diferente por tipo de tópico;
            ligar perguntas curtas ao histórico de ações validadas.

### Problema

            Perguntas curtas como:

            "como assim?"
            "por quê?"
            "e agora?"
            "qual deles?"
            "onde?"
            "o que você quis dizer?"

            só fazem sentido com o tópico anterior.

            Se a Laylay ignora o tópico, ela responde genérico ou inventa
            assunto.

### Comportamento esperado

            A Laylay deve responder perguntas curtas usando:

            última resposta dela;
            última ação;
            último tópico de conversa;
            última sugestão;
            último erro;
            último comando executado.

### Exemplos

            Laylay:
            "Tentei mexer no VS Code, mas não rolou de verdade."

            Pedro:
            "como assim?"

            Resultado:
            explicar o que falhou no VS Code, não puxar assunto aleatório.

            Laylay:
            "Você tem 5 emails novos."

            Pedro:
            "o que eles falam?"

            Resultado:
            EMAIL_READ / resumo dos emails.

### Prioridade

            Alta.

            Isso reduz respostas genéricas e melhora continuidade.

------------------------------------------------------------------------

## 9. Proteção Contra Contexto Velho

### Problema

            Contextos antigos podem voltar do nada.

            Exemplo:

            A Shein apareceu nos emails há muitos minutos.

            Depois Pedro pergunta:

            "tudo na paz?"

            A Laylay não deve responder falando da Shein se isso não estiver
            vivo no momento.

### Comportamento esperado

            Cada contexto deve ter validade própria.

            Exemplos de validade:

            pergunta aberta: curta;
            sugestão de email: média;
            comando de janela: curta;
            conversa emocional: média;
            preferência aprendida: longa;
            memória importante: longa;

### Regra

            Contexto velho não deve dominar conversa nova.

            Se estiver em dúvida, a Laylay deve preferir uma resposta neutra
            ou perguntar.

### Prioridade

            Alta.

            Isso evita vazamento de assuntos antigos e respostas estranhas.

------------------------------------------------------------------------

## 10. Detector de Comentário sem Comando

### Problema

            Pedro pode dizer algo apenas para comentar, não para mandar.

            Exemplos:

            "só falei"
            "era só um comentário"
            "tô só te contando"
            "não é comando"
            "só queria falar isso"

            A Laylay precisa entender que deve conversar, não executar.

### Comportamento esperado

            Quando detectar comentário sem comando:

            limpar intenção prática pendente;
            manter o tópico vivo;
            responder de forma natural;
            não executar ação.

### Exemplos

            Pedro:
            "não é comando, só tô comentando que a Shein é chata"

            Resultado:
            conversa sobre o incômodo;
            talvez oferecer silenciar, mas sem executar automaticamente.

            Pedro:
            "só falei que o Opera tá bugado"

            Resultado:
            conversa/diagnóstico;
            não fechar ou reiniciar Opera sem pedido.

### Prioridade

            Média/Alta.

            Isso ajuda a Laylay a respeitar o tom humano da conversa.

------------------------------------------------------------------------

## 11. Recomendação Musical Contextual

### Status

            Parcialmente aplicada.

            A Laylay agora diferencia pedido de recomendação musical de busca
            musical literal.

            Exemplo:

            Pedro:
            "tem alguma recomendação de música pra mim?"

            Antes:
            pesquisar literalmente "recomendação de música".

            Agora:
            interpretar como uma escolha da própria Laylay baseada em gosto,
            playlist recente e curadoria musical.

### Comportamento esperado

            Quando Pedro pedir uma recomendação, a Laylay deve:

            entender o pedido como curadoria;
            olhar playlists e histórico musical;
            escolher uma faixa que combine;
            responder com personalidade;
            perguntar se Pedro quer tocar;
            guardar a sugestão como pendência contextual.

            Se Pedro responder:

            "eu quero"
            "pode"
            "manda"
            "bora"

            a Laylay deve tocar a música sugerida.

### Regra

            Recomendação não é a mesma coisa que busca.

            "me recomenda uma música"

            não deve virar:

            MUSIC_SEARCH "recomendação de música"

            Deve virar:

            MUSIC_RECOMMEND

### Evoluções futuras

            melhorar escolha por humor atual;
            evitar repetir artistas recentes;
            explicar por que escolheu aquela música;
            permitir "coloca essa recomendação na playlist X";
            usar mais sinais da rotina e do momento do dia.

### Prioridade

            Alta.

            Essa melhoria deixa a música mais pessoal e menos mecânica.

------------------------------------------------------------------------

## Princípio Geral da Comunicação Contextual

            A Laylay deve interpretar frases curtas, mistas e informais usando
            a mente inteira:

            memória curta;
            última pergunta;
            última sugestão;
            última ação;
            emoção atual;
            tópico ativo;
            contexto do PC;
            histórico recente.

            A regra principal é:

            não tratar confirmação, rejeição, comando e conversa como caixas
            isoladas.

            Tudo deve conversar dentro do mesmo cérebro.

