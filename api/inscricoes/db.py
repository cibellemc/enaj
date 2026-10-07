"""Acesso ao banco SQLite das inscrições."""

import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS inscricoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criado_em TEXT NOT NULL,
    nome_presidente TEXT NOT NULL,
    email TEXT NOT NULL,
    junta TEXT NOT NULL,
    integrantes TEXT NOT NULL,      -- lista em JSON
    integrantes_outro TEXT,         -- texto de "Outros integrantes"
    visita_pirenopolis TEXT NOT NULL,
    codigo TEXT                     -- código secreto do card e do QR code
)
"""


class EmailJaInscrito(Exception):
    pass


def novo_codigo():
    return secrets.token_urlsafe(18)


def conectar(caminho):
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao


def get_db():
    if "db" not in g:
        g.db = conectar(current_app.config["DB_PATH"])
    return g.db


def fechar_db(_erro=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def inicializar(caminho):
    """Cria a tabela e atualiza bancos criados por versões anteriores."""
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    with sqlite3.connect(caminho) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(SCHEMA)

        colunas = {coluna[1] for coluna in db.execute("PRAGMA table_info(inscricoes)")}
        if "codigo" not in colunas:
            db.execute("ALTER TABLE inscricoes ADD COLUMN codigo TEXT")
        sem_codigo = db.execute("SELECT id FROM inscricoes WHERE codigo IS NULL").fetchall()
        for (id_,) in sem_codigo:
            db.execute("UPDATE inscricoes SET codigo = ? WHERE id = ?", (novo_codigo(), id_))

        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_inscricoes_codigo ON inscricoes(codigo)")
        try:
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_inscricoes_email ON inscricoes(email)")
        except sqlite3.IntegrityError:
            # Banco antigo com e-mails repetidos: a checagem em criar_inscricao continua valendo
            current_app.logger.warning("Há e-mails repetidos em inscricoes; índice único não criado.")


def email_inscrito(email):
    return get_db().execute("SELECT 1 FROM inscricoes WHERE email = ?", (email,)).fetchone() is not None


def criar_inscricao(dados):
    """Grava a inscrição já validada e devolve o código gerado."""
    if email_inscrito(dados["email"]):
        raise EmailJaInscrito()

    codigo = novo_codigo()
    db = get_db()
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
                dados["nome_presidente"],
                dados["email"],
                dados["junta"],
                json.dumps(dados["integrantes"], ensure_ascii=False),
                dados["integrantes_outro"],
                dados["visita_pirenopolis"],
                codigo,
            ),
        )
        db.commit()
    except sqlite3.IntegrityError as erro:
        # Duas inscrições simultâneas com o mesmo e-mail
        raise EmailJaInscrito() from erro
    return codigo


def buscar_por_codigo(codigo):
    row = get_db().execute("SELECT * FROM inscricoes WHERE codigo = ?", (codigo,)).fetchone()
    return _para_dict(row) if row else None


def codigo_por_email(email):
    row = get_db().execute(
        "SELECT codigo FROM inscricoes WHERE email = ? ORDER BY id DESC LIMIT 1", (email,)
    ).fetchone()
    return row["codigo"] if row else None


def _para_dict(row):
    return {
        "numero": row["id"],
        "criado_em": row["criado_em"],
        "nome_presidente": row["nome_presidente"],
        "email": row["email"],
        "junta": row["junta"],
        "integrantes": json.loads(row["integrantes"]),
        "integrantes_outro": row["integrantes_outro"],
        "visita_pirenopolis": row["visita_pirenopolis"],
        "codigo": row["codigo"],
    }
