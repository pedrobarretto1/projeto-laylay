import json
import os
import re
import sqlite3
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional


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

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
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
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    UNIQUE(tipo, gatilho)
                )
                """
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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
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
        except Exception:
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

        if isinstance(fatos, list):
            self.registrar_fatos(fatos)
        if isinstance(eventos, list):
            self.registrar_eventos(eventos)
        if isinstance(preferencias, dict):
            for chave, valor in preferencias.items():
                self.salvar_preferencia(chave, valor)
        if resumo:
            self.salvar_resumo(resumo)

        conn = sqlite3.connect(self.db_path)
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

    def registrar_fatos(self, fatos: List[str], categoria: str = "geral") -> None:
        if not fatos:
            return
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
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

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO aprendizados_semanticos(
                    tipo, gatilho, valor, regra, texto_original, confianca, criado_em, atualizado_em
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tipo, gatilho) DO UPDATE SET
                    valor = excluded.valor,
                    regra = excluded.regra,
                    texto_original = excluded.texto_original,
                    confianca = excluded.confianca,
                    atualizado_em = excluded.atualizado_em
                """,
                (
                    tipo_limpo,
                    gatilho_limpo,
                    valor_limpo,
                    regra_limpa,
                    str(texto_original or "").strip(),
                    confianca_float,
                    agora,
                    agora,
                ),
            )
            conn.commit()
            row = cur.execute(
                """
                SELECT id, tipo, gatilho, valor, regra, texto_original, confianca, criado_em, atualizado_em
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
            "criado_em": row[7],
            "atualizado_em": row[8],
        }

    def listar_aprendizados_semanticos(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            rows = cur.execute(
                """
                SELECT id, tipo, gatilho, valor, regra, texto_original, confianca, criado_em, atualizado_em
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
            score += float(item.get("confianca") or 0.0) * 0.1
            ranqueados.append((score, item))
        ranqueados.sort(key=lambda par: par[0], reverse=True)
        return [item for _, item in ranqueados[:limit]]

    def formatar_aprendizados_relevantes_para_prompt(self, texto: str, limit: int = 5) -> str:
        itens = self.buscar_aprendizados_relevantes(texto, limit=limit)
        if not itens:
            return ""
        linhas = ["MEMÓRIAS RELEVANTES PARA ESTA FALA:"]
        for item in itens:
            partes = [f"tipo={item.get('tipo')}", f"gatilho={item.get('gatilho')}"]
            if item.get("valor"):
                partes.append(f"valor={item.get('valor')}")
            if item.get("regra"):
                partes.append(f"regra={item.get('regra')}")
            linhas.append("- " + " | ".join(partes))
        return "\n".join(linhas)

    def carregar_fatos(self, limit: int = 50) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT texto FROM fatos ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [row[0] for row in rows]
        finally:
            conn.close()

    def carregar_eventos(self, limit: int = 50) -> List[str]:
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            rows = cur.execute("SELECT chave, valor FROM preferencias ORDER BY chave").fetchall()
            return {chave: valor for chave, valor in rows}
        finally:
            conn.close()

    def carregar_resumos(self, limit: int = 10) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT texto FROM resumos ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [row[0] for row in rows]
        finally:
            conn.close()

    def buscar_contexto(self, termo: str, limit: int = 10) -> List[str]:
        if not termo or not termo.strip():
            return []
        termo_like = f"%{termo.strip().lower()}%"
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT texto FROM (SELECT texto FROM fatos UNION ALL SELECT texto FROM eventos) WHERE lower(texto) LIKE ? ORDER BY 1 LIMIT ?",
                (termo_like, limit),
            ).fetchall()
            return [row[0] for row in rows]
        finally:
            conn.close()

    def recuperar_aprendizados(self, limit: int = 5) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT texto FROM fatos WHERE categoria = 'aprendizado' ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [row[0] for row in rows]
        finally:
            conn.close()

    def formatar_memoria_quente_para_prompt(self, limit: int = 6, max_chars: int = 1200) -> str:
        estado = self.carregar_estado()
        mensagens = estado.get("messages") or []
        if not isinstance(mensagens, list) or not mensagens:
            return ""

        relevantes: List[str] = []
        for msg in reversed(mensagens):
            if len(relevantes) >= limit:
                break
            if not isinstance(msg, dict):
                continue
            role = str(msg.get("role") or "").lower().strip()
            if role not in {"user", "assistant"}:
                continue
            content = str(msg.get("content") or "").strip()
            if not content:
                continue
            label = "Usuário" if role == "user" else "Laylay"
            conteudo = re.sub(r"\s+", " ", content).strip()
            if len(conteudo) > 220:
                conteudo = conteudo[:217] + "..."
            relevantes.append(f"- {label}: {conteudo}")

        if not relevantes:
            return ""

        relevantes.reverse()
        bloco = "MEMÓRIA QUENTE (últimas trocas):\n" + "\n".join(relevantes)
        if len(bloco) > max_chars:
            bloco = bloco[:max_chars].rstrip()
        return bloco

    def formatar_topicos_conversa_para_prompt(self, limit: int = 5, max_chars: int = 1000) -> str:
        estado = self.carregar_estado()
        topicos = estado.get("topicos_conversa_recente") or []
        ultimo_topico = str(estado.get("ultimo_topico_conversa") or "").strip()
        ultimo_ts = estado.get("ultimo_topico_ts")

        linhas: List[str] = []
        if ultimo_topico:
            linhas.append(f"TÓPICO ATIVO: {ultimo_topico}")
            if ultimo_ts:
                try:
                    dt = datetime.fromtimestamp(float(ultimo_ts))
                    linhas[-1] += f" | atualizado em {dt.strftime('%H:%M')}"
                except Exception:
                    pass
        if isinstance(topicos, list) and topicos:
            recentes = [str(x).strip() for x in topicos if str(x).strip()]
            if recentes:
                linhas.append("TÓPICOS RECENTES: " + "; ".join(recentes[-limit:]))

        if not linhas:
            return ""
        bloco = "\n".join(linhas)
        if len(bloco) > max_chars:
            bloco = bloco[:max_chars].rstrip()
        return bloco

    def formatar_memoria_para_prompt(self, max_fatos: int = 8, max_eventos: int = 3, max_preferencias: int = 6) -> str:
        estado = self.carregar_estado()

        fatos = estado.get("memoria_fatos") or []
        eventos = estado.get("memoria_eventos") or []
        preferencias = estado.get("preferencias") or {}
        resumos = estado.get("resumos") or []

        linhas: List[str] = ["MEMÓRIA BREVE:"]

        aprendizados = self.recuperar_aprendizados(limit=12)
        if aprendizados:
            linhas.append("- Aprendizados: " + "; ".join(str(x) for x in aprendizados))

        semanticos = self.listar_aprendizados_semanticos(limit=8)
        if semanticos:
            resumo_semantico = []
            for item in semanticos:
                regra = item.get("regra") or item.get("valor") or item.get("gatilho")
                resumo_semantico.append(f"{item.get('tipo')}:{item.get('gatilho')} => {regra}")
            linhas.append("- Aprendizados semânticos: " + "; ".join(resumo_semantico))

        if fatos:
            linhas.append("- Fatos: " + "; ".join(str(x) for x in fatos[:max_fatos]))
        if eventos:
            linhas.append("- Eventos: " + "; ".join(str(x) for x in eventos[:max_eventos]))
        if preferencias:
            pref_texto = ", ".join(f"{k}={v}" for k, v in list(preferencias.items())[:max_preferencias])
            linhas.append("- Preferências: " + pref_texto)
        if resumos:
            linhas.append("- Resumo: " + str(resumos[0])[:220])

        if len(linhas) == 1:
            return ""
        return "\n".join(linhas)

    def registrar_aprendizado(self, texto: str, categoria: str = "aprendizado") -> List[str]:
        if not isinstance(texto, str) or not texto.strip():
            return []

        texto_limpo = texto.strip()
        texto_lower = texto_limpo.lower()

        fatos = [texto_limpo]
        self.registrar_fatos(fatos, categoria=categoria)
        return fatos
