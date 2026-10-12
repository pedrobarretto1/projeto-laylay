# Streaming local da Laylay

O streaming agora faz parte da extensão existente **Laylay Chrome Extension**.
Não exige uma segunda extensão. Depois de atualizar o código:

1. Abra `chrome://extensions` (no Edge, `edge://extensions`).
2. Ative **Modo do desenvolvedor**.
3. Clique em **Recarregar** no cartão da extensão Laylay existente.
4. Reinicie o Terminal e abra **Streaming**. As páginas já abertas recebem o
   detector automaticamente quando a extensão se conecta. Se necessário,
   recarregue a página do vídeo.

Se a versão separada **Laylay Streaming Local** ainda estiver instalada,
desative-a para evitar duas fontes duplicadas. Ela não é mais necessária.

Selecione um vídeo encontrado e clique em **Transmitir**. O recorte acompanha
posição, tamanho, proporção e zoom do player. Há janela flutuante e tela cheia;
**Esc** retorna à aba. A pausa e o áudio permanecem no navegador.

O módulo de streaming usa um canal independente da IA. Envia apenas título, identidade
temporária e geometria do vídeo ao canal local `127.0.0.1:19769`. Não envia URLs,
cookies, imagens ou áudio; não executa comandos no navegador. O serviço só
aceita conexões de extensões e a transmissão exige um clique na interface.

O navegador precisa manter o vídeo visível numa aba ativa de uma janela aberta,
sem minimizar. Vídeos HTML5 em iframes e shadow DOM abertos são detectados;
DRM, players sem elemento `<video>`, páginas internas e shadow DOM fechados
podem impedir a captura. Menus e sobreposições do próprio player podem aparecer
no vídeo. Não há promessa de compatibilidade com todo site.

Sem geometria atual, a imagem é ocultada; nunca se exibe a janela inteira como
fallback. Fechar a origem, trocar de aba ou desconectar a extensão encerra a
sessão. Alterações muito rápidas de layout podem causar uma breve espera pelo
novo enquadramento.
