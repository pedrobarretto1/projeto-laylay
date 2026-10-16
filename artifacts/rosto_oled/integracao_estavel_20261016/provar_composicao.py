"""Root instalado, placa real sem motores e modelo configurado: nenhuma fala física."""
import json
import pathlib
import sys
import time

ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))


def main():
    import laylay as app
    from mente_laylay.especialistas.rosto_oled_runtime import _abrir_serial
    from mente_laylay.integracao.registro_conversa_llm import PedidoModelo
    from mente_laylay.cognicao.decisao_corporal import IntencaoCorporal
    resultado={}
    r=app._rosto_oled_runtime
    class Porta:
        def __init__(self,p):self.serial=_abrir_serial(p)
        def write(self,d):
            p=d.decode().split()
            assert p[0] not in {'MOTOR','TURN','DEMO'}
            assert p[0]!='SENTRY' or p[4]=='0'
            return self.serial.write(d)
        def read(self,n):return self.serial.read(n)
        def close(self):self.serial.close()
    r.abrir_serial=Porta
    estado=app._estado_compartilhado_runtime
    try:
        estado.atualizar_campos('conversacional',modo_chat=True,conversa_ativa=True,is_speaking=False)
        estado.atualizar_campos('mental',ultima_entrada_ts=time.time()-90,
            ultima_fala_emitida_ts=0,interacao_em_andamento=False,plano_turno_atual={})
        cliente=app._composicao_inteligencia_externa_runtime._transporte
        assert not cliente.interacao_ativa()
        claim=app._prioridade_interacao_usuario_runtime.adquirir('diagnostico')
        try:assert cliente.interacao_ativa()
        finally:app._prioridade_interacao_usuario_runtime.liberar(claim)
        assert app._corpo_motor_runtime.transporte is r
        assert r.sincronizar()
        app._corpo_motor_runtime.companhia._registrar_intencao(
            IntencaoCorporal('descansar','diagnostico_sem_movimento',40,0,1))
        modelo=app._corpo_motor_runtime.modelo_para_mente()
        assert modelo['intencao_em_curso']['objetivo_curto']['proposito']=='ficar_quietinha'
        resultado['modelo_corporal']=modelo
        resultado['prioridade']={'chat_ocioso_bloqueia':False,'claim_real_bloqueia':True}
        fatos={'inercial':modelo['percepcao_fisica']['inercial'],
               'distancias':modelo['percepcao_fisica']['distancias'].get('leituras',{}),
               'motor_em_andamento':modelo['motor_em_andamento']}
        pedido=PedidoModelo.criar([
            {'role':'system','content':'Diagnóstico com leitura real do corpo da Laylay. Retorne JSON {"fala":"uma frase curta","comandos":[]}. Não execute. Diga somente o que estes dados permitem; leitura inválida é desconhecida, nunca caminho livre. Sem bateria, dor, caminho ou movimento inventados. Dados: '+json.dumps(fatos,ensure_ascii=False)},
            {'role':'user','content':'Como seu corpo estava nessa leitura?'}],
            com_tools=False,max_tokens=150,modo_rapido=True,tipo_chamada='presenca_evento',
            prioridade_interativa=False,permitir_durante_interacao=False,classe_timeout='rapida')
        m=app._resposta_evento_runtime.modelo_llm.executar(pedido)
        resultado['modelo_real']={'sucesso':m.sucesso,'rota':m.rota,'texto':m.texto,
                                  'emissao_fisica':False,'efeitos_executados':False}
        print(json.dumps(resultado['modelo_real'],ensure_ascii=False))
    finally:
        r.encerrar()
        resultado['final']=r.diagnostico()
        (pathlib.Path(__file__).parent/'composicao_real.json').write_text(
            json.dumps(resultado,ensure_ascii=False,indent=2),encoding='utf8')


if __name__=='__main__':main()
