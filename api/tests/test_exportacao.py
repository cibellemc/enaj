import base64
import csv
import io

import pytest

from inscricoes import create_app

URL = "/api/admin/inscricoes.csv"
SENHA = "inscrição-2026"  # com acento de propósito

INSCRICAO = {
    "nome_presidente": "Maria Silva",
    "email": "maria@exemplo.com",
    "junta": "JUCEG (Goiás)",
    "integrantes": ["Presidente", "Procurador", "Outro"],
    "integrantes_outro": "Assessoria",
    "visita_pirenopolis": "Não pretendo participar",
}


@pytest.fixture
def app(tmp_path):
    return create_app(DB_PATH=str(tmp_path / "teste.db"), ADMIN_SENHA=SENHA, TESTING=True)


@pytest.fixture
def client(app):
    return app.test_client()


def login(usuario="admin", senha=SENHA):
    token = base64.b64encode(f"{usuario}:{senha}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def ler_csv(texto):
    assert texto.startswith("﻿")
    return list(csv.reader(io.StringIO(texto[1:]), delimiter=";"))


def test_exige_login(client):
    resposta = client.get(URL)
    assert resposta.status_code == 401
    assert "Basic" in resposta.headers["WWW-Authenticate"]


def test_senha_errada(client):
    assert client.get(URL, headers=login(senha="errada")).status_code == 401
    assert client.get(URL, headers=login(usuario="outro")).status_code == 401


def test_bloqueia_apos_muitas_senhas_erradas(client):
    for _ in range(10):
        client.get(URL, headers=login(senha="errada"))
    assert client.get(URL, headers=login()).status_code == 429


def test_desativada_sem_senha_configurada(tmp_path):
    app = create_app(DB_PATH=str(tmp_path / "teste.db"), ADMIN_SENHA="")
    assert app.test_client().get(URL, headers=login(senha="")).status_code == 503


def test_csv_com_as_inscricoes(client):
    client.post("/api/inscricoes", json=INSCRICAO)
    client.post("/api/inscricoes", json={**INSCRICAO, "email": "joao@x.com", "nome_presidente": "João"})

    resposta = client.get(URL, headers=login())
    assert resposta.status_code == 200
    assert resposta.mimetype == "text/csv"
    assert "attachment; filename=\"inscricoes-enaj-2026-" in resposta.headers["Content-Disposition"]
    assert resposta.headers["Cache-Control"] == "no-store"

    linhas = ler_csv(resposta.get_data(as_text=True))
    assert linhas[0] == [
        "Nº", "Data da inscrição", "Nome do presidente", "E-mail", "Junta Comercial",
        "Integrantes da equipe", "Outros integrantes", "Visita técnica a Pirenópolis",
    ]
    assert len(linhas) == 3
    assert linhas[1][0] == "1"
    assert linhas[1][2:] == [
        "Maria Silva", "maria@exemplo.com", "JUCEG (Goiás)",
        "Presidente, Procurador", "Assessoria", "Não pretendo participar",
    ]
    assert linhas[2][2] == "João"


def test_csv_nao_tem_o_codigo_do_qr(client):
    codigo = client.post("/api/inscricoes", json=INSCRICAO).get_json()["codigo"]
    assert codigo not in client.get(URL, headers=login()).get_data(as_text=True)


def test_csv_neutraliza_formulas(client):
    client.post("/api/inscricoes", json={**INSCRICAO, "nome_presidente": "=HYPERLINK(\"http://x\")"})
    linhas = ler_csv(client.get(URL, headers=login()).get_data(as_text=True))
    assert linhas[1][2] == "'=HYPERLINK(\"http://x\")"


def test_comando_de_terminal(app):
    app.test_client().post("/api/inscricoes", json=INSCRICAO)
    resultado = app.test_cli_runner().invoke(args=["exportar"])
    assert resultado.exit_code == 0
    linhas = ler_csv(resultado.output)
    assert linhas[1][2] == "Maria Silva"
