from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.processamento_resposta_ia import salvar_aprendizados_da_ia
from mente_laylay.memoria_mental.memoria_confiavel import (
    extrair_aprendizados_pessoais_explicitos,
    preparar_aprendizados_confirmados,
    usuario_sustenta_aprendizado,
)


class MemoriaConfiavelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.memoria = MemoriaSQLite(os.path.join(self.tmp.name, "memoria.sqlite"))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_fala_criativa_da_ia_nao_vira_memoria(self) -> None:
        item = {
            "tipo": "preferencia",
            "gatilho": "musica para noite",
            "valor": "Far From Alaska",
            "regra": "Pedro adora Far From Alaska à noite",
        }
        self.assertFalse(usuario_sustenta_aprendizado("que noite chata", item))
        self.assertEqual(preparar_aprendizados_confirmados([item], "que noite chata"), [])

    def test_preferencia_afirmada_pelo_usuario_recebe_procedencia(self) -> None:
        item = {
            "tipo": "preferencia",
            "gatilho": "gosto musical",
            "valor": "Rubel",
            "regra": "Pedro gosta de Rubel",
        }
        salvos = preparar_aprendizados_confirmados([item], "eu gosto de Rubel")
        self.assertEqual(len(salvos), 1)
        self.assertEqual(salvos[0]["origem"], "usuario")
        self.assertEqual(salvos[0]["status"], "ativo")
        self.assertTrue(salvos[0]["confirmado_usuario"])
        self.assertIn("eu gosto de Rubel", salvos[0]["evidencia"])

    def test_fatos_pessoais_estaveis_explicitos_entram_na_memoria_geral(self) -> None:
        extraidos = extrair_aprendizados_pessoais_explicitos(
            "eu moro em Boituva e trabalho como programador"
        )

        self.assertEqual(
            [(item["gatilho"], item["valor"]) for item in extraidos],
            [("local onde mora", "Boituva"), ("profissão", "programador")],
        )
        salvos = preparar_aprendizados_confirmados(
            extraidos,
            "eu moro em Boituva e trabalho como programador",
        )
        self.assertEqual(len(salvos), 2)
        self.assertTrue(all(item["confirmado_usuario"] for item in salvos))

    def test_estado_momentaneo_e_pergunta_nao_viram_fato_duravel(self) -> None:
        self.assertEqual(
            extrair_aprendizados_pessoais_explicitos("hoje estou cansado"),
            [],
        )
        self.assertEqual(
            extrair_aprendizados_pessoais_explicitos("onde eu moro?"),
            [],
        )

    def test_fato_pessoal_corrigido_substitui_o_valor_anterior(self) -> None:
        for texto in ("eu moro em Itu", "eu moro em Boituva"):
            resposta = json.dumps({"fala": "Entendi.", "comandos": []})
            salvar_aprendizados_da_ia(resposta, self.memoria, texto)

        ativos = [
            item for item in self.memoria.listar_aprendizados_semanticos()
            if item.get("tipo") == "fato_pessoal" and item.get("status") == "ativo"
        ]
        self.assertEqual(len(ativos), 1)
        self.assertEqual(ativos[0]["valor"], "Boituva")

    def test_saida_da_ia_sem_evidencia_nao_e_salva_nem_duplicada_como_fato(self) -> None:
        resposta = json.dumps({
            "fala": "Também acho a noite parada.",
            "comandos": [],
            "aprendizados": [{
                "tipo": "preferencia",
                "gatilho": "noite",
                "valor": "pão de queijo",
                "regra": "Pedro sempre quer pão de queijo à noite",
            }],
        }, ensure_ascii=False)
        resultado = salvar_aprendizados_da_ia(resposta, self.memoria, "que noite chata")
        self.assertEqual(resultado, [])
        self.assertEqual(self.memoria.listar_aprendizados_semanticos(), [])
        self.assertEqual(self.memoria.recuperar_aprendizados(limit=10), [])

    def test_memoria_confirmada_entra_no_prompt_com_origem_e_confianca(self) -> None:
        resposta = json.dumps({
            "fala": "Anotado.",
            "comandos": [],
            "aprendizados": [{
                "tipo": "preferencia",
                "gatilho": "artista preferido Rubel",
                "valor": "Rubel",
                "regra": "Pedro gosta de Rubel",
            }],
        }, ensure_ascii=False)
        resultado = salvar_aprendizados_da_ia(resposta, self.memoria, "eu gosto de Rubel")
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["gatilho"], "afinidade com Rubel")
        self.assertEqual(resultado[0]["regra"], "você gosta de Rubel")
        self.assertEqual(len(self.memoria.listar_aprendizados_semanticos()), 1)
        prompt = self.memoria.formatar_aprendizados_relevantes_para_prompt(
            "me recomenda algo do Rubel"
        )
        self.assertIn("Rubel", prompt)
        self.assertIn("origem=usuario", prompt)
        self.assertIn("confiança=", prompt)

    def test_legado_sem_procedencia_fica_fora_da_recuperacao_automatica(self) -> None:
        agora = "2026-07-13 12:00:00"
        conn = sqlite3.connect(self.memoria.db_path)
        try:
            conn.execute(
                """
                INSERT INTO aprendizados_semanticos(
                    tipo, gatilho, valor, regra, texto_original, confianca,
                    criado_em, atualizado_em
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("preferencia", "noite", "Laylay.Py", "abrir Laylay.Py", "", 0.99, agora, agora),
            )
            conn.commit()
        finally:
            conn.close()
        itens = self.memoria.listar_aprendizados_semanticos()
        self.assertEqual(itens[0]["status"], "nao_verificado")
        self.assertEqual(
            self.memoria.formatar_aprendizados_relevantes_para_prompt("noite Laylay.Py"),
            "",
        )

    def test_correcao_confirmada_invalida_nome_anterior(self) -> None:
        self.memoria.salvar_aprendizado_semantico(
            tipo="identidade",
            gatilho="nome do usuário",
            valor="Antonio",
            regra="O nome do usuário é Antonio",
            origem="usuario",
            evidencia="meu nome é Antonio",
            status="ativo",
            confirmado_usuario=True,
            confianca=0.95,
        )
        self.memoria.salvar_aprendizado_semantico(
            tipo="correcao",
            gatilho="corrigir nome",
            valor="Pedro",
            regra="O nome do usuário é Pedro",
            origem="usuario",
            evidencia="meu nome não é Antonio, é Pedro",
            status="ativo",
            confirmado_usuario=True,
            confianca=0.99,
        )
        por_valor = {item["valor"]: item for item in self.memoria.listar_aprendizados_semanticos()}
        self.assertEqual(por_valor["Antonio"]["status"], "contradito")
        self.assertTrue(por_valor["Antonio"]["contradito_em"])
        self.assertEqual(por_valor["Pedro"]["status"], "ativo")
        prompt = self.memoria.formatar_aprendizados_relevantes_para_prompt("qual é meu nome?")
        self.assertIn("Pedro", prompt)
        self.assertNotIn("Antonio", prompt)

    def test_nova_preferencia_substitui_valor_anterior_do_mesmo_assunto(self) -> None:
        self.memoria.salvar_aprendizado_semantico(
            tipo="preferencia",
            gatilho="cor preferida da luz",
            valor="azul",
            regra="Pedro prefere a luz azul",
            origem="usuario",
            evidencia="prefiro a luz azul",
            status="ativo",
            confirmado_usuario=True,
        )
        nova = self.memoria.salvar_aprendizado_semantico(
            tipo="preferencia",
            gatilho="cor da lâmpada",
            valor="vermelho",
            regra="Pedro agora prefere a lâmpada vermelha",
            origem="usuario",
            evidencia="agora prefiro a luz vermelha",
            status="ativo",
            confirmado_usuario=True,
        )
        por_valor = {item["valor"]: item for item in self.memoria.listar_aprendizados_semanticos()}
        self.assertEqual(por_valor["azul"]["status"], "contradito")
        self.assertEqual(por_valor["vermelho"]["status"], "ativo")
        self.assertEqual(nova["chave_semantica"], "preferencia:cor_luz")

    def test_preferencias_de_assuntos_diferentes_nao_se_contradizem(self) -> None:
        self.memoria.salvar_aprendizado_semantico(
            tipo="preferencia",
            gatilho="artista preferido",
            valor="Rubel",
            regra="Pedro prefere o artista Rubel",
            origem="usuario",
            evidencia="meu artista preferido é Rubel",
            status="ativo",
            confirmado_usuario=True,
        )
        self.memoria.salvar_aprendizado_semantico(
            tipo="preferencia",
            gatilho="gênero musical preferido",
            valor="rock",
            regra="Pedro prefere o gênero musical rock",
            origem="usuario",
            evidencia="meu gênero musical preferido é rock",
            status="ativo",
            confirmado_usuario=True,
        )
        ativos = [
            item for item in self.memoria.listar_aprendizados_semanticos()
            if item["status"] == "ativo"
        ]
        self.assertEqual({item["valor"] for item in ativos}, {"Rubel", "rock"})

    def test_memoria_breve_nao_injeta_aprendizado_semantico_sem_relevancia(self) -> None:
        self.memoria.salvar_aprendizado_semantico(
            tipo="preferencia",
            gatilho="receita preferida",
            valor="coxinha",
            regra="Pedro prefere receita de coxinha",
            origem="usuario",
            evidencia="prefiro coxinha",
            status="ativo",
            confirmado_usuario=True,
        )
        self.memoria.registrar_fatos(["Pedro estuda no SENAI"])
        prompt = self.memoria.formatar_memoria_para_prompt(max_eventos=0)
        self.assertIn("Pedro estuda no SENAI", prompt)
        self.assertNotIn("coxinha", prompt)


if __name__ == "__main__":
    unittest.main()
