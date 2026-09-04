
--------------------------------------------------------------------------------------------------------------------------
filtragem de titulos, quando peco uma musica ou um video ela me fala o titulo inteiro dela e isso faz parecer que ela nao è iteligente ja que ela so leu o titulo iteiro, exemplo pratico:

💬 Você:coloca vazio constante shiny_sz
🖥️ [TERMINAL 2:CLIENTE] mensagem confirmada | id=a857520ee6dd aceito=True
Timeout na LLM local/API: HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=8)
⚠️ [MENTE:FALHA] llm_http:timeout_resposta | classe=degradacao | impacto=turno | tipo=readtimeout
⚠️ [FALA:AUTORIA] fallback local | motivo=resposta_tecnica_ou_json_invalido status=musica_reproduzindo
🧠 [PLANO:FASE] fase=tratado_prioritario | comandos=[{'id_solicitacao': '1f4f38cc21db4c4ebf4eb30e0d77690f', 'intent': 'MUSIC_SEARCH', 'alvo': 'Shiny - Vazio Constante | Bojack, Rick & Clancy | Ft. @AniRap & @AnnyTHN', 'status': 'musica_reproduzindo', 'executou': True, 'confirmado': True, 'params': {'query': 'Shiny - Vazio Constante | Bojack, Rick & Clancy | Ft. @AniRap & @AnnyTHN', 'consulta_pedida': 'vazio constante shiny sz', 'consulta_resolvida': 'vazio constante shiny sz', 'alvo_executado': 'Shiny - Vazio Constante | Bojack, Rick & Clancy | Ft. @AniRap & @AnnyTHN', 'alvo_executado_url': 'https://www.youtube.com/watch?v=JTq0Ut6XJzs', 'alvo_executado_canal': 'Shiny_sz'}, 'origem': 'executor', 'detalhe': 'playing_confirmed', 'confirmacao_oferecida': 'estado_observado', 'evidencia_confirmacao': 'a abertura da página musical é conferida'}] | erros=[]
╭─ ≧◡≦⋆ Laylay: Concluí o pedido em Shiny - Vazio Constante | Bojack, Rick & Clancy | Ft. @AniRap & @AnnyTHN e confirmei o resultado. Shiny - Vazio Constante | Bojack, Rick & Clancy | Ft. @AniRap & @AnnyTHN está tocando agora.

agora ficou bem mais visivel que filtra o titulo è importante, alem de ficar poluido ela nao passa a sensacao de inteligete, exemplo de como ficaria se tivesse:

╭─ ≧◡≦⋆ Laylay: Concluí o pedido em Shiny - Vazio Constante, a musica jà está tocando agora.

---------------------------------------------------------------------------------------------