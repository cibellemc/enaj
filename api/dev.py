"""Roda o site e a API juntos para testes locais, sem Docker.

Uso (na pasta enaj):
    python3 api/dev.py

Depois abra http://localhost:8000/enaj-2026/inscricao.html

O banco de teste fica em enaj/data/inscricoes.db (ignorado pelo git).
Em produção vale o docker-compose (nginx + gunicorn).
"""

import os
from pathlib import Path

from flask import abort, send_from_directory

from inscricoes import create_app

PASTA_SITE = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("DB_PATH", str(PASTA_SITE / "data" / "inscricoes.db"))

app = create_app(DB_PATH=DB_PATH)


@app.get("/", defaults={"caminho": ""})
@app.get("/<path:caminho>")
def site(caminho):
    # Mesmas regras do nginx: nada de arquivos ocultos nem do código da API
    if caminho.startswith("api/") or any(parte.startswith(".") for parte in caminho.split("/")):
        abort(404)
    if caminho == "" or caminho.endswith("/"):
        caminho += "index.html"
    return send_from_directory(PASTA_SITE, caminho)


if __name__ == "__main__":
    print(f"Banco de teste: {DB_PATH}")
    print("Abra http://localhost:8000/enaj-2026/inscricao.html")
    app.run(host="127.0.0.1", port=8000, debug=True)
