"""Acesso ao banco SQLite das inscrições."""

import os
import secrets
import sqlite3
from datetime import datetime, timezone

from flask import current_app, g

from . import opcoes

# Versão do esquema guardada em PRAGMA user_version (ver _migrar)
VERSAO_ESQUEMA = 2

CRIAR_TABELA = """
CREATE TABLE {tabela} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criado_em TEXT NOT NULL,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    junta TEXT NOT NULL,
    cargo TEXT NOT NULL,
    cargo_outro TEXT,                 -- preenchido quando cargo = "Outro"
    visita_pirenopolis TEXT NOT NULL,
    chegada_data TEXT,                -- AAAA-MM-DD
    chegada_transporte TEXT,          -- "aereo" ou "terrestre"
    chegada_voo TEXT,
    chegada_operadora TEXT,
    chegada_horario TEXT,             -- horário do voo ou horário previsto (HH:MM)
    saida_data TEXT,
    saida_transporte TEXT,
    saida_voo TEXT,
    saida_operadora TEXT,
    saida_horario TEXT,
    codigo TEXT NOT NULL              -- código secreto do card e do QR code
)
"""

# Colunas gravadas a partir dos dados validados (validacao.validar_inscricao)
COLUNAS_DADOS = (
    "nome", "email", "junta", "cargo", "cargo_outro", "visita_pirenopolis",
    "chegada_data", "chegada_transporte", "chegada_voo", "chegada_operadora", "chegada_horario",
    "saida_data", "saida_transporte", "saida_voo", "saida_operadora", "saida_horario",
)


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


# ===== Criação e migração =====

def inicializar(caminho):
    """Cria a tabela ou atualiza bancos de versões anteriores."""
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    with sqlite3.connect(caminho) as db:
        db.execute("PRAGMA journal_mode=WAL")
        existe = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'inscricoes'"
        ).fetchone()
        if not existe:
            db.execute(CRIAR_TABELA.format(tabela="inscricoes"))
        elif db.execute("PRAGMA user_version").fetchone()[0] < VERSAO_ESQUEMA:
            _migrar(db)
        db.execute(f"PRAGMA user_version = {VERSAO_ESQUEMA}")

        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_inscricoes_codigo ON inscricoes(codigo)")
        try:
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_inscricoes_email ON inscricoes(email)")
        except sqlite3.IntegrityError:
            # Banco antigo com e-mails repetidos: a checagem em criar_inscricao continua valendo
            current_app.logger.warning("Há e-mails repetidos em inscricoes; índice único não criado.")


def _migrar(db):
    """Versão 1 (inscrição do presidente, vários integrantes) -> versão 2.

    - nome_presidente vira nome
    - a lista de integrantes vira um único cargo (o primeiro marcado; sem
      nenhum, "Outro" com o texto de "outros integrantes")
    - colunas de transporte ficam vazias nas inscrições antigas
    """
    colunas = {coluna[1] for coluna in db.execute("PRAGMA table_info(inscricoes)")}
    if "codigo" not in colunas:
        db.execute("ALTER TABLE inscricoes ADD COLUMN codigo TEXT")
    for (id_,) in db.execute("SELECT id FROM inscricoes WHERE codigo IS NULL").fetchall():
        db.execute("UPDATE inscricoes SET codigo = ? WHERE id = ?", (novo_codigo(), id_))

    db.execute(CRIAR_TABELA.format(tabela="inscricoes_v2"))
    db.execute(
        """
        INSERT INTO inscricoes_v2
            (id, criado_em, nome, email, junta, cargo, cargo_outro, visita_pirenopolis, codigo)
        SELECT
            id, criado_em, nome_presidente, email, junta,
            COALESCE(json_extract(integrantes, '$[0]'), ?),
            CASE WHEN json_extract(integrantes, '$[0]') IS NULL THEN integrantes_outro END,
            visita_pirenopolis, codigo
        FROM inscricoes
        """,
        (opcoes.CARGO_OUTRO,),
    )
    db.execute("DROP TABLE inscricoes")
    db.execute("ALTER TABLE inscricoes_v2 RENAME TO inscricoes")


# ===== Consultas =====

def email_inscrito(email):
    return get_db().execute("SELECT 1 FROM inscricoes WHERE email = ?", (email,)).fetchone() is not None


def criar_inscricao(dados):
    """Grava a inscrição já validada e devolve o código gerado."""
    if email_inscrito(dados["email"]):
        raise EmailJaInscrito()

    codigo = novo_codigo()
    colunas = ("criado_em", *COLUNAS_DADOS, "codigo")
    valores = (
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        *(dados[coluna] for coluna in COLUNAS_DADOS),
        codigo,
    )
    db = get_db()
    try:
        db.execute(
            f"INSERT INTO inscricoes ({', '.join(colunas)}) VALUES ({', '.join('?' * len(colunas))})",
            valores,
        )
        db.commit()
    except sqlite3.IntegrityError as erro:
        # Duas inscrições simultâneas com o mesmo e-mail
        raise EmailJaInscrito() from erro
    return codigo


def buscar_por_codigo(codigo):
    row = get_db().execute("SELECT * FROM inscricoes WHERE codigo = ?", (codigo,)).fetchone()
    return _para_dict(row) if row else None


def listar_inscricoes():
    rows = get_db().execute("SELECT * FROM inscricoes ORDER BY id").fetchall()
    return [_para_dict(row) for row in rows]


def codigo_por_email(email):
    row = get_db().execute(
        "SELECT codigo FROM inscricoes WHERE email = ? ORDER BY id DESC LIMIT 1", (email,)
    ).fetchone()
    return row["codigo"] if row else None


def _para_dict(row):
    inscricao = {coluna: row[coluna] for coluna in COLUNAS_DADOS}
    inscricao.update(
        numero=row["id"],
        criado_em=row["criado_em"],
        codigo=row["codigo"],
        # Cargo como deve ser exibido (o texto digitado, quando a pessoa escolheu "Outro")
        cargo_exibicao=row["cargo_outro"] if row["cargo"] == opcoes.CARGO_OUTRO else row["cargo"],
    )
    return inscricao
