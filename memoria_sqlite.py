import json
import logging
import os
import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from mente_laylay.memoria_mental.memoria_confiavel import (
    extrair_aprendizados_pessoais_explicitos,
)


_LOG = logging.getLogger(__name__)


class MemoriaSQLite:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "memoria", "laylay_memoria.sqlite")
        self.json_candidates = [
            os.path.join(os.path.dirname(self.db_path), "laylay_memoria.json"),
            os.path.join(os.path.dirname(__file__), "memoria.json"),
            os.path.join(os.path.dirname(__file__), "laylay_memoria.json"),
        ]
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _conectar(self) -> sqlite3.Connection:
        """Abre uma conexão tolerante às escritas concorrentes dos serviços."""
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.execute("PRAGMA busy_timeout = 15000")
        return conn

    def _init_db(self):
        conn = self._conectar()
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode = WAL")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS estado (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS fatos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    texto TEXT NOT NULL UNIQUE,
                    categoria TEXT NOT NULL DEFAULT 'geral',
                    criado_em TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    texto TEXT NOT NULL UNIQUE,
                    criado_em TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS preferencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chave TEXT NOT NULL UNIQUE,
                    valor TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS resumos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL DEFAULT 'geral',
                    texto TEXT NOT NULL,
                    criado_em TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS aprendizados_semanticos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL DEFAULT 'regra',
                    gatilho TEXT NOT NULL,
                    valor TEXT NOT NULL DEFAULT '',
                    regra TEXT NOT NULL DEFAULT '',
                    texto_original TEXT NOT NULL DEFAULT '',
                    confianca REAL NOT NULL DEFAULT 0.8,
                    origem TEXT NOT NULL DEFAULT 'legado',
                    evidencia TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'nao_verificado',
                    confirmado_usuario INTEGER NOT NULL DEFAULT 0,
                    chave_semantica TEXT NOT NULL DEFAULT '',
                    contradito_em TEXT NOT NULL DEFAULT '',
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    UNIQUE(tipo, gatilho)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS iot_dispositivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    nome_amigavel TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    ambiente TEXT NOT NULL,
                    protocolo TEXT NOT NULL,
                    aliases_json TEXT NOT NULL DEFAULT '[]',
                    capacidades_json TEXT NOT NULL DEFAULT '[]',
                    risco TEXT NOT NULL DEFAULT 'moderado',
                    configuracao_json TEXT NOT NULL DEFAULT '{}',
                    ultimo_estado_json TEXT NOT NULL DEFAULT '{}',
                    ultimo_contato TEXT NOT NULL DEFAULT '',
                    ativo INTEGER NOT NULL DEFAULT 1,
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            colunas_aprendizado = {
                row[1] for row in cur.execute("PRAGMA table_info(aprendizados_semanticos)").fetchall()
            }
            migracoes_aprendizado = {
                "origem": "TEXT NOT NULL DEFAULT 'legado'",
                "evidencia": "TEXT NOT NULL DEFAULT ''",
                "status": "TEXT NOT NULL DEFAULT 'nao_verificado'",
                "confirmado_usuario": "INTEGER NOT NULL DEFAULT 0",
                "chave_semantica": "TEXT NOT NULL DEFAULT ''",
                "contradito_em": "TEXT NOT NULL DEFAULT ''",
            }
            for coluna, definicao in migracoes_aprendizado.items():
                if coluna not in colunas_aprendizado:
                    cur.execute(
                        f"ALTER TABLE aprendizados_semanticos ADD COLUMN {coluna} {definicao}"
                    )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS iot_historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dispositivo_id INTEGER,
                    acao TEXT NOT NULL,
                    estado_anterior TEXT,
                    estado_resultante TEXT,
                    status TEXT NOT NULL,
                    origem TEXT NOT NULL DEFAULT 'usuario',
                    detalhes_json TEXT NOT NULL DEFAULT '{}',
                    criado_em TEXT NOT NULL,
                    FOREIGN KEY(dispositivo_id) REFERENCES iot_dispositivos(id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS aprendizado_eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chave TEXT NOT NULL,
                    tipo TEXT NOT NULL DEFAULT 'padrao',
                    escopo TEXT NOT NULL DEFAULT 'geral',
                    valor_json TEXT NOT NULL DEFAULT '{}',
                    contexto_json TEXT NOT NULL DEFAULT '{}',
                    evidencia TEXT NOT NULL DEFAULT '',
                    sinal REAL NOT NULL DEFAULT 0.0,
                    origem TEXT NOT NULL DEFAULT 'observacao',
                    confirmado_usuario INTEGER NOT NULL DEFAULT 0,
                    criado_em TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS aprendizado_hipoteses (
                    chave TEXT PRIMARY KEY,
                    tipo TEXT NOT NULL DEFAULT 'padrao',
                    escopo TEXT NOT NULL DEFAULT 'geral',
                    valor_json TEXT NOT NULL DEFAULT '{}',
                    confianca REAL NOT NULL DEFAULT 0.5,
                    evidencias_positivas INTEGER NOT NULL DEFAULT 0,
                    evidencias_negativas INTEGER NOT NULL DEFAULT 0,
                    contradicoes INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'candidata',
                    primeira_evidencia_em TEXT NOT NULL,
                    ultima_evidencia_em TEXT NOT NULL,
                    ultima_pergunta_em TEXT NOT NULL DEFAULT '',
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_aprendizado_eventos_chave "
                "ON aprendizado_eventos(chave, id DESC)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_aprendizado_hipoteses_revisao "
                "ON aprendizado_hipoteses(status, confianca, atualizado_em)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_iot_dispositivos_ambiente "
                "ON iot_dispositivos(ambiente, ativo)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_iot_historico_dispositivo "
                "ON iot_historico(dispositivo_id, id DESC)"
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _normalizar_texto(texto: Any) -> str:
        bruto = str(texto or "").lower()
        sem_acento = unicodedata.normalize("NFKD", bruto)
        sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", sem_acento).strip()

    @classmethod
    def _tokens_relevancia(cls, texto: Any) -> List[str]:
        normalizado = cls._normalizar_texto(texto)
        tokens = re.findall(r"[a-z0-9_:/.-]{3,}", normalizado)
        stop = {
            "para", "quando", "pedro", "voce", "você", "usar", "esse", "essa",
            "isso", "aqui", "com", "uma", "uns", "das", "dos", "que", "qual",
            "link", "abre", "abrir", "entra", "entrar", "minha", "meu",
        }
        filtrados = [t for t in tokens if t not in stop]
        expandidos = list(filtrados)
        sinonimos = {
            "insta": ["instagram"],
            "instagram": ["insta"],
            "conversa": ["direct", "chat"],
            "direct": ["conversa", "chat"],
            "namorada": ["dela"],
        }
        for token in filtrados:
            expandidos.extend(sinonimos.get(token, []))
        return expandidos

    def _estado_vazio(self) -> Dict[str, Any]:
        return {
            "messages": [{"role": "system", "content": ""}],
            "bordoes": [],
            "resumo_conversa": "",
            "memoria_fatos": [],
            "memoria_eventos": [],
            "historico_long_term": "",
            "current_emotion": "calma",
            "emotion_level": 1,
            "humor_level": 0,
        }

    def _migrar_json_para_sqlite(self) -> bool:
        for caminho in self.json_candidates:
            if not os.path.exists(caminho):
                continue
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                if isinstance(dados, dict):
                    self.salvar_estado(**dados)
                    return True
            except Exception:
                continue
        return False

    def _persistir_estado_payload(self, data: Dict[str, Any]) -> None:
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        conn = self._conectar()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO estado(id, payload, atualizado_em) VALUES(1, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload = excluded.payload, atualizado_em = excluded.atualizado_em",
                (payload, datetime.now().isoformat(" ")),
            )
            conn.commit()
        finally:
            conn.close()

    def carregar_estado(self) -> Dict[str, Any]:
        conn = self._conectar()
        try:
            cur = conn.cursor()
            row = cur.execute("SELECT payload FROM estado WHERE id = 1").fetchone()
            if row is None:
                if self._migrar_json_para_sqlite():
                    return self.carregar_estado()
                data = self._estado_vazio()
                data["memoria_fatos"] = self.carregar_fatos(limit=50)
                data["memoria_eventos"] = self.carregar_eventos(limit=50)
                data["preferencias"] = self.carregar_preferencias()
                data["resumos"] = self.carregar_resumos(limit=10)
                self._persistir_estado_payload(data)
                return data
            data = json.loads(row[0])
            if not isinstance(data, dict):
                return self._estado_vazio()
            data["memoria_fatos"] = self.carregar_fatos(limit=50) or data.get("memoria_fatos", [])
            data["memoria_eventos"] = self.carregar_eventos(limit=50) or data.get("memoria_eventos", [])
            data["preferencias"] = self.carregar_preferencias() or data.get("preferencias", {})
            data["resumos"] = self.carregar_resumos(limit=10) or data.get("resumos", [])
            return data
        except Exception as erro:
            _LOG.exception("Falha ao carregar a memória SQLite; tentando recuperação: %s", erro)
            if self._migrar_json_para_sqlite():
                return self.carregar_estado()
            return self._estado_vazio()
        finally:
            conn.close()

    def salvar_estado(self, **kwargs: Any) -> None:
        data = self._estado_vazio()
        data.update(kwargs)
        payload = json.dumps(data, ensure_ascii=False, indent=2)

        fatos = data.get("memoria_fatos") or []
        eventos = data.get("memoria_eventos") or []
        resumo = data.get("resumo_conversa") or ""
        preferencias = data.get("preferencias") or {}

        conn = self._conectar()
        try:
            cur = conn.cursor()
            agora = datetime.now().isoformat(" ")
            if isinstance(fatos, list):
                cur.executemany(
                    "INSERT OR IGNORE INTO fatos(texto, categoria, criado_em) "
                    "VALUES(?, ?, ?)",
                    [
                        (texto.strip(), "geral", agora)
                        for texto in fatos
                        if isinstance(texto, str) and texto.strip()
                    ],
                )
            if isinstance(eventos, list):
                cur.executemany(
                    "INSERT OR IGNORE INTO eventos(texto, criado_em) VALUES(?, ?)",
                    [
                        (texto.strip(), agora)
                        for texto in eventos
                        if isinstance(texto, str) and texto.strip()
                    ],
                )
            if isinstance(preferencias, dict):
                cur.executemany(
                    "INSERT INTO preferencias(chave, valor, atualizado_em) "
                    "VALUES(?, ?, ?) ON CONFLICT(chave) DO UPDATE SET "
                    "valor = excluded.valor, atualizado_em = excluded.atualizado_em",
                    [
                        (str(chave).strip(), str(valor), agora)
                        for chave, valor in preferencias.items()
                        if isinstance(chave, str) and chave.strip()
                    ],
                )
            if isinstance(resumo, str) and resumo.strip():
                cur.execute(
                    "INSERT INTO resumos(tipo, texto, criado_em) VALUES(?, ?, ?)",
                    ("geral", resumo.strip(), agora),
                )
            cur.execute(
                "INSERT INTO estado(id, payload, atualizado_em) VALUES(1, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload = excluded.payload, atualizado_em = excluded.atualizado_em",
                (payload, agora),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def registrar_fatos(self, fatos: List[str], categoria: str = "geral") -> None:
        if not fatos:
            return
        conn = self._conectar()
        try:
            cur = conn.cursor()
            for texto in fatos:
                if not isinstance(texto, str) or not texto.strip():
                    continue
                cur.execute(
                    "INSERT OR IGNORE INTO fatos(texto, categoria, criado_em) VALUES(?, ?, ?)",
                    (texto.strip(), categoria, datetime.now().isoformat(" ")),
                )
            conn.commit()
        finally:
            conn.close()

    def registrar_eventos(self, eventos: List[str]) -> None:
        if not eventos:
            return
        conn = self._conectar()
        try:
            cur = conn.cursor()
            for texto in eventos:
                if not isinstance(texto, str) or not texto.strip():
                    continue
                cur.execute(
                    "INSERT OR IGNORE INTO eventos(texto, criado_em) VALUES(?, ?)",
                    (texto.strip(), datetime.now().isoformat(" ")),
                )
            conn.commit()
        finally:
            conn.close()

    def salvar_preferencia(self, chave: str, valor: Any) -> None:
        if not isinstance(chave, str) or not chave.strip():
            return
        conn = self._conectar()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO preferencias(chave, valor, atualizado_em) VALUES(?, ?, ?) "
                "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor, atualizado_em = excluded.atualizado_em",
                (chave.strip(), str(valor), datetime.now().isoformat(" ")),
            )
            conn.commit()
        finally:
            conn.close()

    def salvar_resumo(self, texto: str, tipo: str = "geral") -> None:
        if not isinstance(texto, str) or not texto.strip():
            return
        conn = self._conectar()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO resumos(tipo, texto, criado_em) VALUES(?, ?, ?)",
                (tipo, texto.strip(), datetime.now().isoformat(" ")),
            )
            conn.commit()
        finally:
            conn.close()

    def salvar_aprendizado_semantico(
        self,
        tipo: str = "regra",
        gatilho: str = "",
        valor: Any = "",
        regra: str = "",
        texto_original: str = "",
        confianca: float = 0.8,
        origem: str = "sistema",
        evidencia: str = "",
        status: str = "ativo",
        confirmado_usuario: bool = False,
    ) -> Optional[Dict[str, Any]]:
        gatilho_limpo = str(gatilho or "").strip()
        regra_limpa = str(regra or "").strip()
        valor_limpo = str(valor or "").strip()
        if not gatilho_limpo and not regra_limpa and not valor_limpo:
            return None
        if not gatilho_limpo:
            gatilho_limpo = regra_limpa or valor_limpo
        tipo_limpo = self._normalizar_texto(tipo or "regra") or "regra"
        agora = datetime.now().isoformat(" ")
        try:
            confianca_float = float(confianca)
        except Exception:
            confianca_float = 0.8
        confianca_float = max(0.0, min(1.0, confianca_float))
        origem_limpa = self._normalizar_texto(origem or "sistema") or "sistema"
        status_limpo = self._normalizar_texto(status or "nao_verificado").replace(" ", "_")
        if status_limpo not in {"ativo", "nao_verificado", "contradito", "expirado"}:
            status_limpo = "nao_verificado"
        evidencia_limpa = str(evidencia or texto_original or "").strip()[:1000]
        base_chave = self._normalizar_texto(
            " ".join((gatilho_limpo, valor_limpo, regra_limpa))
        )
        if "nome" in base_chave and tipo_limpo in {"correcao", "identidade", "preferencia", "regra"}:
            chave_semantica = "identidade:nome_usuario"
        elif tipo_limpo == "preferencia":
            chave_semantica = self._chave_semantica_preferencia(
                gatilho_limpo, valor_limpo, regra_limpa
            )
        else:
            chave_semantica = f"{tipo_limpo}:{self._normalizar_texto(gatilho_limpo)}"

        conn = self._conectar()
        try:
            cur = conn.cursor()
            if confirmado_usuario and chave_semantica:
                # Compatibilidade com preferências gravadas antes de a chave
                # representar o assunto (elas usavam o próprio valor). Assim,
                # uma escolha nova também invalida a preferência legada do
                # mesmo assunto.
                if tipo_limpo == "preferencia":
                    preferencias_ativas = cur.execute(
                        """
                        SELECT id, gatilho, valor, regra
                        FROM aprendizados_semanticos
                        WHERE tipo = 'preferencia' AND status = 'ativo'
                        """
                    ).fetchall()
                    ids_contraditos = [
                        int(row[0])
                        for row in preferencias_ativas
                        if self._chave_semantica_preferencia(row[1], row[2], row[3]) == chave_semantica
                        and str(row[1] or "").strip() != gatilho_limpo
                    ]
                    if ids_contraditos:
                        marcadores = ",".join("?" for _ in ids_contraditos)
                        cur.execute(
                            f"""
                            UPDATE aprendizados_semanticos
                            SET status = 'contradito', contradito_em = ?, atualizado_em = ?
                            WHERE id IN ({marcadores})
                            """,
                            (agora, agora, *ids_contraditos),
                        )
                cur.execute(
                    """
                    UPDATE aprendizados_semanticos
                    SET status = 'contradito', contradito_em = ?, atualizado_em = ?
                    WHERE chave_semantica = ? AND status = 'ativo'
                      AND NOT (tipo = ? AND gatilho = ?)
                    """,
                    (agora, agora, chave_semantica, tipo_limpo, gatilho_limpo),
                )
            cur.execute(
                """
                INSERT INTO aprendizados_semanticos(
                    tipo, gatilho, valor, regra, texto_original, confianca,
                    origem, evidencia, status, confirmado_usuario, chave_semantica, contradito_em,
                    criado_em, atualizado_em
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?)
                ON CONFLICT(tipo, gatilho) DO UPDATE SET
                    valor = excluded.valor,
                    regra = excluded.regra,
                    texto_original = excluded.texto_original,
                    confianca = excluded.confianca,
                    origem = excluded.origem,
                    evidencia = excluded.evidencia,
                    status = excluded.status,
                    confirmado_usuario = excluded.confirmado_usuario,
                    chave_semantica = excluded.chave_semantica,
                    contradito_em = '',
                    atualizado_em = excluded.atualizado_em
                """,
                (
                    tipo_limpo,
                    gatilho_limpo,
                    valor_limpo,
                    regra_limpa,
                    str(texto_original or "").strip(),
                    confianca_float,
                    origem_limpa,
                    evidencia_limpa,
                    status_limpo,
                    1 if confirmado_usuario else 0,
                    chave_semantica,
                    agora,
                    agora,
                ),
            )
            conn.commit()
            row = cur.execute(
                """
                SELECT id, tipo, gatilho, valor, regra, texto_original, confianca,
                       origem, evidencia, status, confirmado_usuario, chave_semantica, contradito_em,
                       criado_em, atualizado_em
                FROM aprendizados_semanticos WHERE tipo = ? AND gatilho = ?
                """,
                (tipo_limpo, gatilho_limpo),
            ).fetchone()
            return self._row_aprendizado_semantico(row)
        finally:
            conn.close()

    def salvar_aprendizados_semanticos(self, aprendizados: List[Any]) -> List[Dict[str, Any]]:
        salvos: List[Dict[str, Any]] = []
        for item in aprendizados or []:
            if isinstance(item, dict):
                salvo = self.salvar_aprendizado_semantico(
                    tipo=str(item.get("tipo") or "regra"),
                    gatilho=str(item.get("gatilho") or item.get("chave") or item.get("quando") or ""),
                    valor=item.get("valor") or item.get("url") or item.get("link") or "",
                    regra=str(item.get("regra") or item.get("texto") or item.get("descricao") or ""),
                    texto_original=str(item.get("texto_original") or item.get("original") or ""),
                    confianca=item.get("confianca") or 0.8,
                    origem=str(item.get("origem") or "sistema"),
                    evidencia=str(item.get("evidencia") or ""),
                    status=str(item.get("status") or "ativo"),
                    confirmado_usuario=bool(item.get("confirmado_usuario", False)),
                )
            else:
                texto = str(item or "").strip()
                salvo = self.salvar_aprendizado_semantico(
                    tipo="regra",
                    gatilho=texto[:140],
                    regra=texto,
                    texto_original=texto,
                    confianca=0.75,
                )
            if salvo:
                salvos.append(salvo)
        return salvos

    @staticmethod
    def _row_hipotese_aprendizado(row) -> Optional[Dict[str, Any]]:
        if not row:
            return None
        try:
            valor = json.loads(row[3])
        except Exception:
            valor = row[3]
        return {
            "chave": row[0], "tipo": row[1], "escopo": row[2], "valor": valor,
            "confianca": float(row[4] or 0.0),
            "evidencias_positivas": int(row[5] or 0),
            "evidencias_negativas": int(row[6] or 0),
            "contradicoes": int(row[7] or 0), "status": row[8],
            "primeira_evidencia_em": row[9], "ultima_evidencia_em": row[10],
            "ultima_pergunta_em": row[11], "atualizado_em": row[12],
        }

    def registrar_evidencia_aprendizado(
        self,
        *,
        chave: str,
        tipo: str,
        escopo: str,
        valor: Any,
        sinal: float,
        origem: str,
        evidencia: str = "",
        contexto: Dict[str, Any] | None = None,
        confirmado_usuario: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Registra evidência e atualiza uma hipótese sem aprender da própria IA."""
        chave = str(chave or "").strip()
        origem_norm = self._normalizar_texto(origem).replace(" ", "_")
        if not chave or origem_norm in {"ia", "assistente", "resposta_ia", "fala_ia"}:
            return None
        try:
            sinal = max(-1.0, min(1.0, float(sinal)))
        except Exception:
            sinal = 0.0
        agora = datetime.now().isoformat(" ")
        valor_json = json.dumps(valor, ensure_ascii=False, sort_keys=True)
        contexto_json = json.dumps(dict(contexto or {}), ensure_ascii=False, sort_keys=True)
        conn = self._conectar()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            cur.execute(
                """
                INSERT INTO aprendizado_eventos(
                    chave, tipo, escopo, valor_json, contexto_json, evidencia,
                    sinal, origem, confirmado_usuario, criado_em
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chave, str(tipo or "padrao"), str(escopo or "geral"), valor_json,
                    contexto_json, str(evidencia or "")[:1000], sinal, origem_norm,
                    1 if confirmado_usuario else 0, agora,
                ),
            )
            row = cur.execute(
                """
                SELECT chave, tipo, escopo, valor_json, confianca,
                       evidencias_positivas, evidencias_negativas, contradicoes,
                       status, primeira_evidencia_em, ultima_evidencia_em,
                       ultima_pergunta_em, atualizado_em
                FROM aprendizado_hipoteses WHERE chave = ?
                """,
                (chave,),
            ).fetchone()
            atual = self._row_hipotese_aprendizado(row)
            positivos = int((atual or {}).get("evidencias_positivas") or 0)
            negativos = int((atual or {}).get("evidencias_negativas") or 0)
            contradicoes = int((atual or {}).get("contradicoes") or 0)
            confianca = float((atual or {}).get("confianca") or 0.5)
            valor_anterior = (atual or {}).get("valor")
            mesmo_valor = atual is None or valor_anterior == valor
            if atual is not None and not mesmo_valor and sinal > 0:
                contradicoes += 1
                if confirmado_usuario or sinal >= 0.85:
                    confianca = 0.68
                    valor_anterior = valor
                else:
                    sinal = -abs(sinal) * 0.5
            elif atual is None:
                valor_anterior = valor

            peso = 1.35 if confirmado_usuario else 1.0
            if sinal > 0:
                positivos += 1
                confianca += (1.0 - confianca) * min(0.42, 0.22 * sinal * peso)
            elif sinal < 0:
                negativos += 1
                confianca -= confianca * min(0.5, 0.28 * abs(sinal) * peso)
            confianca = max(0.05, min(0.99, confianca))
            if confirmado_usuario:
                confianca = max(confianca, 0.9)
                status = "ativa"
            elif confianca >= 0.74 and positivos >= 2:
                status = "ativa"
            elif confianca < 0.3:
                status = "enfraquecida"
            else:
                status = "candidata"
            primeira = str((atual or {}).get("primeira_evidencia_em") or agora)
            ultima_pergunta = str((atual or {}).get("ultima_pergunta_em") or "")
            cur.execute(
                """
                INSERT INTO aprendizado_hipoteses(
                    chave, tipo, escopo, valor_json, confianca,
                    evidencias_positivas, evidencias_negativas, contradicoes,
                    status, primeira_evidencia_em, ultima_evidencia_em,
                    ultima_pergunta_em, atualizado_em
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chave) DO UPDATE SET
                    tipo=excluded.tipo, escopo=excluded.escopo,
                    valor_json=excluded.valor_json, confianca=excluded.confianca,
                    evidencias_positivas=excluded.evidencias_positivas,
                    evidencias_negativas=excluded.evidencias_negativas,
                    contradicoes=excluded.contradicoes, status=excluded.status,
                    ultima_evidencia_em=excluded.ultima_evidencia_em,
                    atualizado_em=excluded.atualizado_em
                """,
                (
                    chave, str(tipo or "padrao"), str(escopo or "geral"),
                    json.dumps(valor_anterior, ensure_ascii=False, sort_keys=True),
                    confianca, positivos, negativos, contradicoes, status,
                    primeira, agora, ultima_pergunta, agora,
                ),
            )
            conn.commit()
            return self.obter_hipotese_aprendizado(chave, _conn=conn)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def obter_hipotese_aprendizado(
        self, chave: str, *, _conn: sqlite3.Connection | None = None
    ) -> Optional[Dict[str, Any]]:
        conn = _conn or self._conectar()
        try:
            row = conn.execute(
                """
                SELECT chave, tipo, escopo, valor_json, confianca,
                       evidencias_positivas, evidencias_negativas, contradicoes,
                       status, primeira_evidencia_em, ultima_evidencia_em,
                       ultima_pergunta_em, atualizado_em
                FROM aprendizado_hipoteses WHERE chave = ?
                """,
                (str(chave or "").strip(),),
            ).fetchone()
            return self._row_hipotese_aprendizado(row)
        finally:
            if _conn is None:
                conn.close()

    def listar_eventos_aprendizado(
        self, chave: str, *, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Expõe as evidências de uma hipótese para avaliação de maturidade."""
        conn = self._conectar()
        try:
            rows = conn.execute(
                """
                SELECT chave, tipo, escopo, valor_json, contexto_json, evidencia,
                       sinal, origem, confirmado_usuario, criado_em
                FROM aprendizado_eventos
                WHERE chave = ? ORDER BY id DESC LIMIT ?
                """,
                (str(chave or "").strip(), max(1, int(limit))),
            ).fetchall()
            eventos = []
            for row in rows:
                try:
                    valor = json.loads(row[3])
                except Exception:
                    valor = row[3]
                try:
                    contexto = json.loads(row[4])
                except Exception:
                    contexto = {}
                eventos.append({
                    "chave": row[0], "tipo": row[1], "escopo": row[2],
                    "valor": valor, "contexto": contexto if isinstance(contexto, dict) else {},
                    "evidencia": row[5], "sinal": float(row[6] or 0.0),
                    "origem": row[7], "confirmado_usuario": bool(row[8]),
                    "criado_em": row[9],
                })
            return eventos
        finally:
            conn.close()

    def listar_hipoteses_aprendizado(
        self, *, status: str = "", limit: int = 100
    ) -> List[Dict[str, Any]]:
        conn = self._conectar()
        try:
            where = "WHERE status = ?" if status else ""
            params: tuple[Any, ...] = (status, int(limit)) if status else (int(limit),)
            rows = conn.execute(
                f"""
                SELECT chave, tipo, escopo, valor_json, confianca,
                       evidencias_positivas, evidencias_negativas, contradicoes,
                       status, primeira_evidencia_em, ultima_evidencia_em,
                       ultima_pergunta_em, atualizado_em
                FROM aprendizado_hipoteses {where}
                ORDER BY confianca DESC, atualizado_em DESC LIMIT ?
                """,
                params,
            ).fetchall()
            return [item for item in (self._row_hipotese_aprendizado(row) for row in rows) if item]
        finally:
            conn.close()

    def responder_hipotese_aprendizado(self, chave: str, aceito: bool) -> Optional[Dict[str, Any]]:
        atual = self.obter_hipotese_aprendizado(chave)
        if not atual:
            return None
        return self.registrar_evidencia_aprendizado(
            chave=chave,
            tipo=atual["tipo"], escopo=atual["escopo"], valor=atual["valor"],
            sinal=1.0 if aceito else -1.0,
            origem="confirmacao_usuario", evidencia="confirmação direta da hipótese",
            confirmado_usuario=bool(aceito),
        )

    def marcar_pergunta_hipotese(self, chave: str) -> None:
        agora = datetime.now().isoformat(" ")
        conn = self._conectar()
        try:
            conn.execute(
                "UPDATE aprendizado_hipoteses SET ultima_pergunta_em = ?, atualizado_em = ? WHERE chave = ?",
                (agora, agora, str(chave or "").strip()),
            )
            conn.commit()
        finally:
            conn.close()

    def definir_status_hipotese_aprendizado(self, chave: str, status: str) -> None:
        permitido = {"candidata", "ativa", "enfraquecida", "resolvida"}
        status = str(status or "").strip().lower()
        if status not in permitido:
            raise ValueError("status de hipótese inválido")
        conn = self._conectar()
        try:
            conn.execute(
                "UPDATE aprendizado_hipoteses SET status = ?, atualizado_em = ? WHERE chave = ?",
                (status, datetime.now().isoformat(" "), str(chave or "").strip()),
            )
            conn.commit()
        finally:
            conn.close()

    def esquecer_aprendizado_por_prefixo(self, prefixo: str) -> int:
        """Remove hipótese e eventos pertencentes a um perfil revogado."""
        prefixo = str(prefixo or "").strip()
        if not prefixo:
            return 0
        # LIKE trata %, _ e \\ como operadores; escapamos todos para que o
        # chamador só consiga remover o namespace literal informado.
        padrao = (
            prefixo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            + "%"
        )
        conn = self._conectar()
        try:
            eventos = int(conn.execute(
                "DELETE FROM aprendizado_eventos WHERE chave LIKE ? ESCAPE '\\'", (padrao,),
            ).rowcount or 0)
            hipoteses = int(conn.execute(
                "DELETE FROM aprendizado_hipoteses WHERE chave LIKE ? ESCAPE '\\'", (padrao,),
            ).rowcount or 0)
            conn.commit()
            return eventos + hipoteses
        finally:
            conn.close()

    def revisar_hipoteses_aprendizado(
        self, *, agora: datetime | None = None, inatividade_dias: int = 30
    ) -> int:
        """Reduz lentamente a certeza de padrões que deixaram de aparecer."""
        atual = agora or datetime.now()
        limite = atual - timedelta(days=max(1, int(inatividade_dias)))
        hipoteses = self.listar_hipoteses_aprendizado(limit=500)
        alteradas = 0
        conn = self._conectar()
        try:
            for item in hipoteses:
                try:
                    ultima = datetime.fromisoformat(str(item.get("ultima_evidencia_em") or ""))
                except Exception:
                    continue
                if ultima >= limite:
                    continue
                try:
                    revisada = datetime.fromisoformat(str(item.get("atualizado_em") or ""))
                except Exception:
                    revisada = ultima
                referencia = max(ultima, revisada)
                dias_desde_revisao = max(0, (atual - referencia).days)
                blocos = int(dias_desde_revisao / max(1, inatividade_dias))
                if blocos <= 0:
                    continue
                reforcos = max(0, int(item.get("evidencias_positivas") or 0))
                resistencia = 1.0 + min(3.0, reforcos ** 0.5)
                confianca = max(
                    0.05,
                    float(item.get("confianca") or 0.0) * (0.97 ** (blocos / resistencia)),
                )
                status = str(item.get("status") or "candidata")
                if confianca < 0.3:
                    status = "enfraquecida"
                elif status == "ativa" and confianca < 0.68:
                    status = "candidata"
                conn.execute(
                    "UPDATE aprendizado_hipoteses SET confianca = ?, status = ?, atualizado_em = ? WHERE chave = ?",
                    (confianca, status, atual.isoformat(" "), item["chave"]),
                )
                alteradas += 1
            conn.commit()
            return alteradas
        finally:
            conn.close()

    @staticmethod
    def _row_aprendizado_semantico(row) -> Optional[Dict[str, Any]]:
        if not row:
            return None
        return {
            "id": row[0],
            "tipo": row[1],
            "gatilho": row[2],
            "valor": row[3],
            "regra": row[4],
            "texto_original": row[5],
            "confianca": row[6],
            "origem": row[7],
            "evidencia": row[8],
            "status": row[9],
            "confirmado_usuario": bool(row[10]),
            "chave_semantica": row[11],
            "contradito_em": row[12],
            "criado_em": row[13],
            "atualizado_em": row[14],
        }

    def listar_aprendizados_semanticos(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._conectar()
        try:
            cur = conn.cursor()
            rows = cur.execute(
                """
                SELECT id, tipo, gatilho, valor, regra, texto_original, confianca,
                       origem, evidencia, status, confirmado_usuario, chave_semantica, contradito_em,
                       criado_em, atualizado_em
                FROM aprendizados_semanticos
                ORDER BY atualizado_em DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [item for item in (self._row_aprendizado_semantico(row) for row in rows) if item]
        finally:
            conn.close()

    def buscar_aprendizados_relevantes(self, texto: str, limit: int = 5) -> List[Dict[str, Any]]:
        consulta_tokens = set(self._tokens_relevancia(texto))
        if not consulta_tokens:
            return []
        candidatos = self.listar_aprendizados_semanticos(limit=200)
        ranqueados = []
        for item in candidatos:
            if str(item.get("status") or "") != "ativo":
                continue
            confianca_base = float(item.get("confianca") or 0.0)
            confianca_efetiva = confianca_base
            tipo_item = str(item.get("tipo") or "").casefold()
            if tipo_item in {"preferencia", "regra"}:
                try:
                    atualizado = datetime.fromisoformat(str(item.get("atualizado_em") or ""))
                    idade_dias = max(0.0, (datetime.now() - atualizado).total_seconds() / 86400.0)
                except Exception:
                    idade_dias = 0.0
                meia_vida = 365.0 if bool(item.get("confirmado_usuario")) else 120.0
                confianca_efetiva = confianca_base * (0.5 ** (idade_dias / meia_vida))
            if confianca_efetiva < 0.72:
                continue
            item = dict(item)
            item["confianca_efetiva"] = round(confianca_efetiva, 3)
            alvo = " ".join(
                str(item.get(k) or "") for k in ("tipo", "gatilho", "valor", "regra", "texto_original")
            )
            alvo_tokens = set(self._tokens_relevancia(alvo))
            if not alvo_tokens:
                continue
            inter = consulta_tokens & alvo_tokens
            if not inter:
                continue
            score = len(inter) / max(1, len(consulta_tokens))
            score += min(0.25, len(inter) * 0.05)
            score += confianca_efetiva * 0.1
            ranqueados.append((score, item))
        ranqueados.sort(key=lambda par: par[0], reverse=True)
        return [item for _, item in ranqueados[:limit]]

    def formatar_aprendizados_relevantes_para_prompt(self, texto: str, limit: int = 5) -> str:
        itens = self.buscar_aprendizados_relevantes(texto, limit=limit)
        if not itens:
            return ""
        linhas = ["MEMÓRIAS RELEVANTES PARA ESTA FALA:"]
        for item in itens:
            partes = [
                f"tipo={item.get('tipo')}", f"gatilho={item.get('gatilho')}",
                f"origem={item.get('origem')}",
                f"confiança={float(item.get('confianca_efetiva', item.get('confianca')) or 0):.2f}",
            ]
            if item.get("valor"):
                partes.append(f"valor={item.get('valor')}")
            if item.get("regra"):
                partes.append(f"regra={item.get('regra')}")
            linhas.append("- " + " | ".join(partes))
        return "\n".join(linhas)

    def carregar_fatos(self, limit: int = 50, incluir_aprendizados: bool = True) -> List[str]:
        conn = self._conectar()
        try:
            cur = conn.cursor()
            if incluir_aprendizados:
                rows = cur.execute(
                    "SELECT texto FROM fatos ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                rows = cur.execute(
                    "SELECT texto FROM fatos WHERE categoria != 'aprendizado' ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [row[0] for row in rows]
        finally:
            conn.close()

    def carregar_eventos(self, limit: int = 50) -> List[str]:
        conn = self._conectar()
        try:
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT texto FROM eventos ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [row[0] for row in rows]
        finally:
            conn.close()

    def carregar_preferencias(self) -> Dict[str, str]:
        conn = self._conectar()
        try:
            cur = conn.cursor()
            rows = cur.execute("SELECT chave, valor FROM preferencias ORDER BY chave").fetchall()
            return {chave: valor for chave, valor in rows}
        finally:
            conn.close()

    def carregar_resumos(self, limit: int = 10) -> List[str]:
        conn = self._conectar()
        try:
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT texto FROM resumos ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [row[0] for row in rows]
        finally:
            conn.close()

    @staticmethod
    def _texto_aprendizado_semantico(item: Dict[str, Any]) -> str:
        """Produz uma descrição humana sem expor o registro bruto da memória."""
        regra = str(item.get("regra") or "").strip()
        original = str(item.get("texto_original") or "").strip()
        gatilho = str(item.get("gatilho") or "").strip()
        valor = str(item.get("valor") or "").strip()
        if regra:
            return regra
        if original:
            return original
        if gatilho and valor and valor.casefold() not in gatilho.casefold():
            return f"{gatilho}: {valor}"
        return valor or gatilho

    @staticmethod
    def _texto_hipotese_aprendizado(item: Dict[str, Any]) -> str:
        valor = item.get("valor")
        if isinstance(valor, dict):
            for chave in ("descricao_humana", "descricao", "regra", "valor"):
                texto = str(valor.get(chave) or "").strip()
                if texto:
                    return texto
            return ""
        if isinstance(valor, (list, tuple)):
            return ", ".join(str(parte).strip() for parte in valor if str(parte).strip())
        return str(valor or "").strip()

    def consultar_aprendizados(
        self,
        *,
        consulta: str = "",
        limit: int = 5,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Lê a memória aprendida por uma visão única, segura e deduplicada.

        Aprendizados semânticos explícitos, hipóteses realmente maduras e
        fatos legados continuam em tabelas distintas por proveniência. Esta
        consulta apenas os reúne para leitura; não promove uma hipótese nem
        grava uma nova memória.
        """
        try:
            limite = max(1, min(20, int(limit or 5)))
        except (TypeError, ValueError):
            limite = 5
        try:
            deslocamento = max(0, int(offset or 0))
        except (TypeError, ValueError):
            deslocamento = 0
        tokens_consulta = set(self._tokens_relevancia(consulta))
        candidatos: List[Dict[str, Any]] = []

        for item_original in self.listar_aprendizados_semanticos(limit=500):
            item = dict(item_original)
            status = str(item.get("status") or "").casefold()
            origem = self._normalizar_texto(item.get("origem"))
            confianca = float(item.get("confianca") or 0.0)
            confirmado = bool(item.get("confirmado_usuario"))
            if status != "ativo" or origem in {
                "ia", "assistente", "resposta ia", "fala ia",
            }:
                continue
            # Sem confirmação direta, apenas registros de alta confiança podem
            # ser relatados como aprendizado. Os demais continuam guardados,
            # mas não viram afirmação sobre a pessoa.
            if not confirmado and confianca < 0.85:
                continue
            # Compatibilidade segura com registros antigos nos quais a LLM
            # inventou uma regra, embora a evidência guardada contenha uma
            # preferência direta. Reconstruímos apenas a visão de leitura;
            # o banco original permanece intacto e auditável.
            if confirmado and str(item.get("tipo") or "").casefold() == "preferencia":
                explicitos = extrair_aprendizados_pessoais_explicitos(
                    str(item.get("evidencia") or "")
                )
                if explicitos:
                    texto_item = self._normalizar_texto(" ".join((
                        str(item.get("gatilho") or ""),
                        str(item.get("valor") or ""),
                        str(item.get("regra") or ""),
                    )))
                    explicito = next((
                        candidato for candidato in explicitos
                        if self._normalizar_texto(candidato.get("valor")) in texto_item
                    ), explicitos[0])
                    item.update(explicito)
                    item["chave_semantica"] = self._chave_semantica_preferencia(
                        explicito.get("gatilho"), explicito.get("valor"),
                        explicito.get("regra"),
                    )
            texto = self._texto_aprendizado_semantico(item)
            if not texto:
                continue
            candidatos.append({
                "texto": texto,
                "fonte": "aprendizado_semantico",
                "natureza": "confirmado" if confirmado else "observado_confiavel",
                "tipo": str(item.get("tipo") or "regra"),
                "confianca": round(confianca, 3),
                "confirmado_usuario": confirmado,
                "chave": str(item.get("chave_semantica") or ""),
                "gatilho": str(item.get("gatilho") or ""),
                "valor": str(item.get("valor") or ""),
                "regra": str(item.get("regra") or ""),
                "atualizado_em": str(item.get("atualizado_em") or ""),
            })

        for item in self.listar_hipoteses_aprendizado(status="ativa", limit=500):
            confianca = float(item.get("confianca") or 0.0)
            positivos = int(item.get("evidencias_positivas") or 0)
            if confianca < 0.68 or positivos < 2:
                continue
            texto = self._texto_hipotese_aprendizado(item)
            if not texto:
                continue
            candidatos.append({
                "texto": texto,
                "fonte": "hipotese_madura",
                "natureza": "padrao_percebido",
                "tipo": str(item.get("tipo") or "padrao"),
                "confianca": round(confianca, 3),
                "confirmado_usuario": False,
                "chave": str(item.get("chave") or ""),
                "atualizado_em": str(item.get("atualizado_em") or ""),
            })

        conn = self._conectar()
        try:
            rows = conn.execute(
                "SELECT texto, criado_em FROM fatos "
                "WHERE categoria = 'aprendizado' ORDER BY id DESC LIMIT 500"
            ).fetchall()
        finally:
            conn.close()
        for texto, criado_em in rows:
            texto_limpo = str(texto or "").strip()
            if texto_limpo:
                candidatos.append({
                    "texto": texto_limpo,
                    "fonte": "fato_legado",
                    "natureza": "registro_antigo",
                    "tipo": "legado",
                    "confianca": 0.7,
                    "confirmado_usuario": False,
                    "chave": "",
                    "atualizado_em": str(criado_em or ""),
                })

        def pontuar(item: Dict[str, Any]) -> tuple[float, str]:
            alvo = " ".join((
                str(item.get("texto") or ""), str(item.get("tipo") or ""),
                str(item.get("chave") or ""),
            ))
            tokens_alvo = set(self._tokens_relevancia(alvo))
            intersecao = tokens_consulta.intersection(tokens_alvo)
            relevancia = (
                len(intersecao) / max(1, len(tokens_consulta))
                if tokens_consulta else 1.0
            )
            confirmado = 0.25 if item.get("confirmado_usuario") else 0.0
            fonte = 0.12 if item.get("fonte") == "aprendizado_semantico" else 0.0
            chave = str(item.get("chave") or "").casefold()
            tipo = str(item.get("tipo") or "").casefold()
            pessoal = 0.0
            if not tokens_consulta:
                if chave.startswith("preferencia:afinidade:"):
                    pessoal = 0.50
                elif tipo == "identidade":
                    pessoal = 0.35
                elif tipo == "apelido":
                    pessoal = 0.25
            return (
                relevancia + confirmado + fonte + pessoal
                + float(item.get("confianca") or 0.0) * 0.1,
                str(item.get("atualizado_em") or ""),
            )

        if tokens_consulta:
            candidatos = [
                item for item in candidatos
                if tokens_consulta.intersection(set(self._tokens_relevancia(
                    " ".join((
                        str(item.get("texto") or ""), str(item.get("tipo") or ""),
                        str(item.get("chave") or ""),
                    ))
                )))
            ]
        candidatos.sort(key=pontuar, reverse=True)

        vistos: set[str] = set()
        unicos: List[Dict[str, Any]] = []
        for item in candidatos:
            chave = str(item.get("chave") or "").strip().casefold()
            assinatura = chave or self._normalizar_texto(item.get("texto"))
            if not assinatura or assinatura in vistos:
                continue
            vistos.add(assinatura)
            unicos.append(item)
        return unicos[deslocamento:deslocamento + limite]

    def diagnostico_aprendizados(self) -> Dict[str, Any]:
        """Retorna somente contagens e saúde, nunca o conteúdo memorizado."""
        conn = self._conectar()
        try:
            semanticos = {
                str(status or "desconhecido"): int(total or 0)
                for status, total in conn.execute(
                    "SELECT status, COUNT(*) FROM aprendizados_semanticos GROUP BY status"
                ).fetchall()
            }
            hipoteses = {
                str(status or "desconhecido"): int(total or 0)
                for status, total in conn.execute(
                    "SELECT status, COUNT(*) FROM aprendizado_hipoteses GROUP BY status"
                ).fetchall()
            }
            legados = int(conn.execute(
                "SELECT COUNT(*) FROM fatos WHERE categoria = 'aprendizado'"
            ).fetchone()[0] or 0)
        finally:
            conn.close()
        return {
            "disponivel": True,
            "semanticos": semanticos,
            "hipoteses": hipoteses,
            "legados": legados,
            "persistencia_local": True,
            "conteudo_exposto": False,
            "autoriza_execucao": False,
        }

    def recuperar_aprendizados(self, limit: int = 5) -> List[str]:
        """Compatibilidade legada; novas consultas usam a visão estruturada."""
        itens = self.consultar_aprendizados(limit=limit)
        return [str(item.get("texto") or "") for item in itens if item.get("texto")]

    @classmethod
    def _chave_semantica_preferencia(cls, gatilho: Any, valor: Any, regra: Any = "") -> str:
        """Identifica o assunto da preferência, sem usar a escolha como chave."""
        gatilho_norm = cls._normalizar_texto(gatilho)
        valor_norm = cls._normalizar_texto(valor)
        regra_norm = cls._normalizar_texto(regra)
        base = " ".join(x for x in (gatilho_norm, regra_norm) if x).strip()

        # Gostar de rock e gostar de programação são afinidades independentes,
        # não duas opções exclusivas do mesmo campo. A chave pelo objeto evita
        # que uma declaração apague a outra e permite corrigir exatamente a
        # afinidade citada depois.
        if gatilho_norm.startswith("afinidade com "):
            objeto = gatilho_norm.removeprefix("afinidade com ").strip()
            if objeto:
                return f"preferencia:afinidade:{objeto}"

        tokens = set(cls._tokens_relevancia(base))
        if "cor" in tokens and tokens.intersection({"luz", "lampada", "iluminacao"}):
            return "preferencia:cor_luz"
        if tokens.intersection({"artista", "cantor", "cantora", "banda"}):
            return "preferencia:artista_musical"
        if tokens.intersection({"genero", "estilo"}) and tokens.intersection({"musica", "musical"}):
            return "preferencia:genero_musical"
        if "playlist" in tokens:
            return "preferencia:playlist"

        assunto = gatilho_norm
        if valor_norm:
            assunto = re.sub(rf"\b{re.escape(valor_norm)}\b", " ", assunto)
        assunto = re.sub(
            r"\b(?:eu|meu|minha|pedro|gosto|gosta|prefiro|prefere|preferido|preferida|favorito|favorita)\b",
            " ",
            assunto,
        )
        assunto = re.sub(r"\s+", " ", assunto).strip()
        return f"preferencia:{assunto or gatilho_norm or 'geral'}"

    def formatar_memoria_para_prompt(self, max_fatos: int = 8, max_eventos: int = 3, max_preferencias: int = 6) -> str:
        """Formata somente memória duradoura; nunca restaura a sessão salva."""
        fatos = self.carregar_fatos(limit=max_fatos, incluir_aprendizados=False) if max_fatos > 0 else []
        eventos = self.carregar_eventos(limit=max_eventos) if max_eventos > 0 else []
        preferencias = self.carregar_preferencias() if max_preferencias > 0 else {}

        linhas: List[str] = ["MEMÓRIA BREVE:"]

        if fatos:
            linhas.append("- Fatos: " + "; ".join(str(x) for x in fatos[:max_fatos]))
        if eventos:
            linhas.append("- Eventos: " + "; ".join(str(x) for x in eventos[:max_eventos]))
        if preferencias:
            pref_texto = ", ".join(f"{k}={v}" for k, v in list(preferencias.items())[:max_preferencias])
            linhas.append("- Preferências: " + pref_texto)
        if len(linhas) == 1:
            return ""
        return "\n".join(linhas)

    @staticmethod
    def _validar_configuracao_iot(configuracao: Dict[str, Any]) -> Dict[str, Any]:
        """Impede que credenciais reais sejam persistidas no cadastro IoT."""
        sensiveis = {"local_key", "device_id", "token", "password", "senha", "secret", "chave"}

        def validar(valor: Any, chave: str = "") -> Any:
            chave_norm = str(chave or "").strip().lower()
            if isinstance(valor, dict):
                return {str(k): validar(v, str(k)) for k, v in valor.items()}
            if isinstance(valor, list):
                return [validar(item, chave) for item in valor]
            if chave_norm in sensiveis:
                referencia = str(valor or "").strip()
                if not re.fullmatch(r"IOT_[A-Z0-9_]+", referencia):
                    raise ValueError(
                        f"Configuração IoT sensível '{chave}' deve referenciar uma variável IOT_*, nunca guardar o valor."
                    )
                return referencia
            return valor

        return validar(dict(configuracao or {}))

    @staticmethod
    def _sanitizar_detalhes_iot(detalhes: Dict[str, Any] | None) -> Dict[str, Any]:
        sensiveis = {"local_key", "device_id", "token", "password", "senha", "secret", "chave"}

        def limpar(valor: Any, chave: str = "") -> Any:
            if str(chave or "").strip().lower() in sensiveis:
                return "[REDACTED]"
            if isinstance(valor, dict):
                return {str(k): limpar(v, str(k)) for k, v in valor.items()}
            if isinstance(valor, list):
                return [limpar(item, chave) for item in valor]
            return valor

        return limpar(dict(detalhes or {}))

    @staticmethod
    def _row_iot_dispositivo(row) -> Optional[Dict[str, Any]]:
        if not row:
            return None
        return {
            "id": row[0],
            "nome": row[1],
            "nome_amigavel": row[2],
            "tipo": row[3],
            "ambiente": row[4],
            "protocolo": row[5],
            "aliases": json.loads(row[6] or "[]"),
            "capacidades": json.loads(row[7] or "[]"),
            "risco": row[8],
            "configuracao": json.loads(row[9] or "{}"),
            "ultimo_estado": json.loads(row[10] or "{}"),
            "ultimo_contato": row[11],
            "ativo": bool(row[12]),
            "atualizado_em": row[13],
        }

    def salvar_dispositivo_iot(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        item = dict(dados or {})
        nome = str(item.get("nome") or "").strip()
        if not nome:
            raise ValueError("Cadastro IoT precisa de nome.")
        configuracao = self._validar_configuracao_iot(item.get("configuracao") or {})
        agora = datetime.now().isoformat(" ")
        conn = self._conectar()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO iot_dispositivos(
                    nome, nome_amigavel, tipo, ambiente, protocolo,
                    aliases_json, capacidades_json, risco, configuracao_json,
                    ultimo_estado_json, ultimo_contato, ativo, atualizado_em
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(nome) DO UPDATE SET
                    nome_amigavel=excluded.nome_amigavel,
                    tipo=excluded.tipo,
                    ambiente=excluded.ambiente,
                    protocolo=excluded.protocolo,
                    aliases_json=excluded.aliases_json,
                    capacidades_json=excluded.capacidades_json,
                    risco=excluded.risco,
                    configuracao_json=excluded.configuracao_json,
                    ativo=excluded.ativo,
                    atualizado_em=excluded.atualizado_em
                """,
                (
                    nome,
                    str(item.get("nome_amigavel") or nome),
                    str(item.get("tipo") or "dispositivo"),
                    str(item.get("ambiente") or "desconhecido"),
                    str(item.get("protocolo") or ""),
                    json.dumps(list(item.get("aliases") or []), ensure_ascii=False),
                    json.dumps(sorted(set(item.get("capacidades") or [])), ensure_ascii=False),
                    str(item.get("risco") or "moderado"),
                    json.dumps(configuracao, ensure_ascii=False),
                    json.dumps(dict(item.get("ultimo_estado") or {}), ensure_ascii=False),
                    str(item.get("ultimo_contato") or ""),
                    1 if item.get("ativo", True) else 0,
                    agora,
                ),
            )
            conn.commit()
            row = cur.execute(
                """
                SELECT id, nome, nome_amigavel, tipo, ambiente, protocolo,
                       aliases_json, capacidades_json, risco, configuracao_json,
                       ultimo_estado_json, ultimo_contato, ativo, atualizado_em
                FROM iot_dispositivos WHERE nome = ?
                """,
                (nome,),
            ).fetchone()
            return self._row_iot_dispositivo(row) or {}
        finally:
            conn.close()

    def listar_dispositivos_iot(self, ambiente: str = "", *, somente_ativos: bool = True) -> List[Dict[str, Any]]:
        clausulas = []
        params: List[Any] = []
        if ambiente:
            clausulas.append("lower(ambiente) = lower(?)")
            params.append(str(ambiente).strip())
        if somente_ativos:
            clausulas.append("ativo = 1")
        where = " WHERE " + " AND ".join(clausulas) if clausulas else ""
        conn = self._conectar()
        try:
            rows = conn.execute(
                """
                SELECT id, nome, nome_amigavel, tipo, ambiente, protocolo,
                       aliases_json, capacidades_json, risco, configuracao_json,
                       ultimo_estado_json, ultimo_contato, ativo, atualizado_em
                FROM iot_dispositivos
                """ + where + " ORDER BY ambiente, nome_amigavel",
                tuple(params),
            ).fetchall()
            return [item for item in (self._row_iot_dispositivo(row) for row in rows) if item]
        finally:
            conn.close()

    def atualizar_estado_iot(
        self,
        nome: str,
        estado: Dict[str, Any],
        *,
        ultimo_contato: Optional[str] = None,
    ) -> bool:
        agora = datetime.now().isoformat(" ")
        conn = self._conectar()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE iot_dispositivos
                SET ultimo_estado_json = ?,
                    ultimo_contato = COALESCE(?, ultimo_contato),
                    atualizado_em = ?
                WHERE nome = ?
                """,
                (
                    json.dumps(dict(estado or {}), ensure_ascii=False),
                    str(ultimo_contato).strip() if ultimo_contato is not None else None,
                    agora,
                    str(nome or "").strip(),
                ),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def registrar_historico_iot(
        self,
        nome_dispositivo: str,
        *,
        acao: str,
        estado_anterior: Any = None,
        estado_resultante: Any = None,
        status: str,
        origem: str = "usuario",
        detalhes: Dict[str, Any] | None = None,
        limite: int = 1000,
    ) -> int:
        detalhes_limpos = self._sanitizar_detalhes_iot(detalhes)
        agora = datetime.now().isoformat(" ")
        conn = self._conectar()
        try:
            cur = conn.cursor()
            row = cur.execute(
                "SELECT id FROM iot_dispositivos WHERE nome = ?",
                (str(nome_dispositivo or "").strip(),),
            ).fetchone()
            dispositivo_id = row[0] if row else None
            cur.execute(
                """
                INSERT INTO iot_historico(
                    dispositivo_id, acao, estado_anterior, estado_resultante,
                    status, origem, detalhes_json, criado_em
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dispositivo_id,
                    str(acao or ""),
                    json.dumps(estado_anterior, ensure_ascii=False),
                    json.dumps(estado_resultante, ensure_ascii=False),
                    str(status or ""),
                    str(origem or "usuario"),
                    json.dumps(detalhes_limpos, ensure_ascii=False),
                    agora,
                ),
            )
            historico_id = int(cur.lastrowid)
            cur.execute(
                "DELETE FROM iot_historico WHERE id NOT IN "
                "(SELECT id FROM iot_historico ORDER BY id DESC LIMIT ?)",
                (max(10, int(limite or 1000)),),
            )
            conn.commit()
            return historico_id
        finally:
            conn.close()
