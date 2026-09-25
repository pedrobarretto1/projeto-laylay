"""Parte modular do tema do Terminal Laylay 3.0."""

from .tokens import PALETA

def qss_chat_components() -> str:
    """Conversa, mensagens, composer e estados auxiliares do chat."""
    return f"""
                /* =========================================
                HOME — CONVERSA
                ========================================= */






                /* =========================================
                MENSAGENS
                ========================================= */



                #messageMeta {{
                    background: transparent;
                    border: 0;

                    color: #747B84;

                    font-size: 8px;
                    font-weight: 700;

                    letter-spacing: 1px;
                }}

                #messageText {{
                    background: transparent;
                    border: 0;

                    color: #EDE9EB;

                    font-size: 14px;
                }}

                #messageStatus {{
                    background: transparent;
                    border: 0;

                    color: #686F78;

                    font-size: 9px;
                }}

                #messageStatus[delivery="pending"] {{
                    color: #D35A6E;
                }}

                #messageStatus[delivery="failed"] {{
                    color: #ED7888;
                }}





                #messageTime {{
                    background: transparent;
                    border: 0;
                    padding-left: 5px;
                    color: #747B84;
                    font-size: 10px;
                }}


                /* =========================================
                   MENSAGEM DO USUÁRIO
                   ========================================= */


                #messageTime[owner="user"] {{
                    background: transparent;
                    border: 0;
                    padding-left: 0;
                    padding-right: 5px;
                    color: #747B84;
                    font-size: 10px;
                }}






                /* =========================================
                WAVEFORM
                ========================================= */

                #microphoneWaveform {{
                    background: transparent;

                    border: 0;
                }}


                /* =========================================
                COMPOSER
                ========================================= */

                #composer {{
                    background: #11151A;

                    border: 1px solid #432B33;
                    border-radius: 18px;
                }}

                #composer:focus-within {{
                    border-color: #7A3B48;
                }}


                /* campo central */

                #composerEdit {{
                    background: #171B20;

                    border: 1px solid #272E35;
                    border-radius: 14px;

                    padding: 6px 10px;

                    color: #E7E3E5;

                    selection-background-color: #743746;

                    font-size: 14px;
                }}

                #composerEdit:focus {{
                    background: #181C21;

                    border-color: #4E333B;
                }}


                /* dica inferior */

                #composerHint {{
                    background: transparent;
                    border: 0;

                    color: #686F77;

                    font-size: 9px;
                }}


                /* microfone */

                #composerMic {{
                    background: #D7445B;

                    border: 1px solid #F06479;
                    border-radius: 23px;
                }}

                #composerMic:hover {{
                    background: #EB536A;

                    border-color: #FF7A8D;
                }}

                #composerMic:pressed {{
                    background: #BD384D;
                }}


                /* enviar */

                #sendButton {{
                    background: #21191E;

                    border: 1px solid #4A3038;
                    border-radius: 21px;
                }}

                #sendButton:hover {{
                    background: #2B1C22;

                    border-color: #85404D;
                }}

                #sendButton:pressed {{
                    background: #351D25;

                    border-color: #A94B5D;
                }}

                #sendButton:disabled {{
                    background: #171B20;

                    border-color: #292F36;
                }}
                #voiceSurface {{ background: #172123; border: 1px solid #2F5559; border-radius: 10px; }}
                #voiceDot {{ color: {PALETA['ciano']}; font-size: 17px; }}
                #voiceText {{ color: #B7DCE0; }}

    """

__all__ = ['qss_chat_components']
