"""API de inscrição do 43º ENAJ (Goiânia 2026).

Recebe o formulário da página enaj-2026/inscricao.html e grava as respostas
em um banco SQLite. O caminho do banco vem da variável DB_PATH (no Docker,
fica no volume montado em /data para não se perder ao recriar o container).

Cada inscrição recebe um código secreto aleatório. Ele identifica o card de
confirmação (enaj-2026/confirmacao.html?c=...) e vai no QR code, que abre a
página de validação de entrada (enaj-2026/validar.html?c=...).
"""

import json
import os
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock

from flask import Flask, g, jsonify, request

DB_PATH = os.environ.get("DB_PATH", "/data/inscricoes.db")

JUNTAS = [
    "JUCEAC (Acre)",
    "JUCEAL (Alagoas)",
    "JUCAP (Amapá)",
    "JUCEA (Amazonas)",
    "JUCEB (Bahia)",
    "JUCEC (Ceará)",
    "JUCIS-DF (Distrito Federal)",
    "JUCEES (Espírito Santo)",
    "JUCEG (Goiás)",
    "JUCEMA (Maranhão)",
    "JUCEMAT (Mato Grosso)",
    "JUCEMS (Mato Grosso do Sul)",
    "JUCEMG (Minas Gerais)",
    "JUCEPA (Pará)",
    "JUCEP (Paraíba)",
    "JUCEPAR (Paraná)",
    "JUCEPE (Pernambuco)",
    "JUCEPI (Piauí)",
    "JUCERJA (Rio de Janeiro)",
    "JUCERN (Rio Grande do Norte)",
    "JUCISRS (Rio Grande do Sul)",
    "JUCER (Rondônia)",
    "JUCERR (Roraima)",
    "JUCESC (Santa Catarina)",
    "JUCESP (São Paulo)",
    "JUCESE (Sergipe)",
    "JUCETINS (Tocantins)",
]

INTEGRANTES = [
    "Presidente",
    "Vice-Presidente",
    "Procurador",
    "Secretária-Geral",
    "Diretoria Técnica",
    "Gerente de Tecnologia",
    "Gerente de REDESIM",
    "Gerente de Cadastro",
]

VISITA = [
    "Sim, tenho interesse em participar",
    "Não pretendo participar",
    "Ainda não tenho uma definição",
]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CODIGO_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")

# Limites simples por IP (o serviço roda com 1 processo)
JANELA_SEGUNDOS = 3600
LIMITES = {
    "inscricao": 10,  # inscrições gravadas por hora
    "acesso": 30,     # buscas por e-mail por hora
}
_envios = defaultdict(deque)
_envios_lock = Lock()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def novo_codigo():
    return secrets.token_urlsafe(18)


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS inscricoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criado_em TEXT NOT NULL,
                nome_presidente TEXT NOT NULL,
                email TEXT NOT NULL,
                junta TEXT NOT NULL,
                integrantes TEXT NOT NULL,      -- lista em JSON
                integrantes_outro TEXT,         -- texto da opção "Outro"
                visita_pirenopolis TEXT NOT NULL,
                codigo TEXT                     -- código secreto do card/QR code
            )
            """
        )
        # Bancos criados antes do card de confirmação não têm a coluna codigo
        colunas = {c[1] for c in db.execute("PRAGMA table_info(inscricoes)")}
        if "codigo" not in colunas:
            db.execute("ALTER TABLE inscricoes ADD COLUMN codigo TEXT")
        for (id_,) in db.execute("SELECT id FROM inscricoes WHERE codigo IS NULL").fetchall():
            db.execute("UPDATE inscricoes SET codigo = ? WHERE id = ?", (novo_codigo(), id_))
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_inscricoes_codigo ON inscricoes(codigo)")
        try:
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_inscricoes_email ON inscricoes(email)")
        except sqlite3.IntegrityError:
            # Já existem e-mails repetidos no banco; a checagem na inscrição continua valendo
            app.logger.warning("Há e-mails repetidos em inscricoes; índice único não criado.")


def ip_do_cliente():
    # O nginx repassa o IP real no cabeçalho X-Real-IP
    return request.headers.get("X-Real-IP") or request.remote_addr or "?"


def excedeu_limite(tipo, ip):
    agora = time.monotonic()
    with _envios_lock:
        fila = _envios[(tipo, ip)]
        while fila and agora - fila[0] > JANELA_SEGUNDOS:
            fila.popleft()
        return len(fila) >= LIMITES[tipo]


def registrar_envio(tipo, ip):
    with _envios_lock:
        _envios[(tipo, ip)].append(time.monotonic())


def texto(dados, campo, maximo):
    valor = dados.get(campo)
    if not isinstance(valor, str):
        return ""
    return valor.strip()[:maximo]


def validar(dados):
    erros = {}

    nome = texto(dados, "nome_presidente", 200)
    if not nome:
        erros["nome_presidente"] = "Informe o nome do presidente da Junta Comercial."

    email = texto(dados, "email", 254).lower()
    if not EMAIL_RE.match(email):
        erros["email"] = "Informe um e-mail válido."

    junta = texto(dados, "junta", 100)
    if junta not in JUNTAS:
        erros["junta"] = "Selecione a Junta Comercial que representa."

    integrantes = dados.get("integrantes")
    if not isinstance(integrantes, list):
        integrantes = []
    integrantes = [i for i in integrantes if isinstance(i, str)]
    outro = texto(dados, "integrantes_outro", 200)
    marcou_outro = "Outro" in integrantes
    selecionados = [i for i in INTEGRANTES if i in integrantes]
    if marcou_outro and not outro:
        erros["integrantes"] = "Descreva os outros integrantes da equipe."
    elif not selecionados and not marcou_outro:
        erros["integrantes"] = "Selecione pelo menos um integrante da equipe."

    visita = texto(dados, "visita_pirenopolis", 100)
    if visita not in VISITA:
        erros["visita_pirenopolis"] = "Selecione uma opção."

    limpo = {
        "nome_presidente": nome,
        "email": email,
        "junta": junta,
        "integrantes": selecionados,
        "integrantes_outro": outro if marcou_outro else None,
        "visita_pirenopolis": visita,
    }
    return limpo, erros


def resposta_ja_inscrito():
    return jsonify(
        ok=False,
        ja_inscrito=True,
        erro="Este e-mail já possui uma inscrição. Acesse sua inscrição com o e-mail.",
    ), 409


@app.post("/api/inscricoes")
def criar_inscricao():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify(ok=False, erro="Dados inválidos."), 400

    # Campo escondido: só robôs preenchem. Responde como sucesso e descarta.
    if texto(dados, "site", 200):
        return jsonify(ok=True), 201

    ip = ip_do_cliente()
    if excedeu_limite("inscricao", ip):
        return jsonify(ok=False, erro="Muitas tentativas. Tente novamente mais tarde."), 429

    limpo, erros = validar(dados)
    if erros:
        return jsonify(ok=False, erros=erros), 422

    db = get_db()
    if db.execute("SELECT 1 FROM inscricoes WHERE email = ?", (limpo["email"],)).fetchone():
        return resposta_ja_inscrito()

    codigo = novo_codigo()
    try:
        db.execute(
            """
            INSERT INTO inscricoes
                (criado_em, nome_presidente, email, junta, integrantes,
                 integrantes_outro, visita_pirenopolis, codigo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                limpo["nome_presidente"],
                limpo["email"],
                limpo["junta"],
                json.dumps(limpo["integrantes"], ensure_ascii=False),
                limpo["integrantes_outro"],
                limpo["visita_pirenopolis"],
                codigo,
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        # Duas inscrições simultâneas com o mesmo e-mail
        return resposta_ja_inscrito()

    # Só conta inscrições gravadas, para não bloquear quem errou o preenchimento
    registrar_envio("inscricao", ip)
    return jsonify(ok=True, codigo=codigo), 201


@app.get("/api/inscricoes/<codigo>")
def ver_inscricao(codigo):
    """Dados do card de confirmação e da validação de entrada (QR code)."""
    if not CODIGO_RE.match(codigo):
        return jsonify(ok=False, erro="Inscrição não encontrada."), 404

    row = get_db().execute("SELECT * FROM inscricoes WHERE codigo = ?", (codigo,)).fetchone()
    if row is None:
        return jsonify(ok=False, erro="Inscrição não encontrada."), 404

    return jsonify(
        ok=True,
        inscricao={
            "numero": row["id"],
            "criado_em": row["criado_em"],
            "nome_presidente": row["nome_presidente"],
            "email": row["email"],
            "junta": row["junta"],
            "integrantes": json.loads(row["integrantes"]),
            "integrantes_outro": row["integrantes_outro"],
            "visita_pirenopolis": row["visita_pirenopolis"],
            "codigo": row["codigo"],
        },
    )


@app.post("/api/inscricoes/acesso")
def acessar_inscricao():
    """Busca a inscrição pelo e-mail e devolve o código do card."""
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify(ok=False, erro="Dados inválidos."), 400

    ip = ip_do_cliente()
    if excedeu_limite("acesso", ip):
        return jsonify(ok=False, erro="Muitas tentativas. Tente novamente mais tarde."), 429
    registrar_envio("acesso", ip)

    email = texto(dados, "email", 254).lower()
    if not EMAIL_RE.match(email):
        return jsonify(ok=False, erro="Informe um e-mail válido."), 422

    row = get_db().execute(
        "SELECT codigo FROM inscricoes WHERE email = ? ORDER BY id DESC LIMIT 1", (email,)
    ).fetchone()
    if row is None:
        return jsonify(ok=False, erro="Não encontramos inscrição com este e-mail."), 404

    return jsonify(ok=True, codigo=row["codigo"])


@app.get("/api/health")
def health():
    return jsonify(ok=True)


init_db()
