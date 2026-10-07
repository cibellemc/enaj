import base64
import csv
import io

from conftest import INSCRICAO_VALIDA, SENHA_ADMIN

from inscricoes import create_app

URL = "/api/admin/inscricoes.csv"


def login(usuario="admin", senha=SENHA_ADMIN):
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


def test_csv_com_as_inscricoes(client, inscrever):
    inscrever()
    inscrever(email="joao@x.com", nome="João", cargo="Outro", cargo_outro="Assessor")

    resposta = client.get(URL, headers=login())
    assert resposta.status_code == 200
    assert resposta.mimetype == "text/csv"
    assert 'attachment; filename="inscricoes-enaj-2026-' in resposta.headers["Content-Disposition"]
    assert resposta.headers["Cache-Control"] == "no-store"

    linhas = ler_csv(resposta.get_data(as_text=True))
    assert linhas[0] == [
        "Nº", "Data da inscrição", "Nome", "E-mail", "Junta Comercial", "Cargo", "Já está em Goiânia",
        "Chegada - data", "Chegada - transporte", "Chegada - voo", "Chegada - companhia aérea",
        "Chegada - horário", "Saída - data", "Saída - transporte", "Saída - voo",
        "Saída - companhia aérea", "Saída - horário", "Visita técnica a Pirenópolis",
    ]
    assert len(linhas) == 3
    assert linhas[1][0] == "1"
    assert linhas[1][2:] == [
        "Maria Silva", "maria@exemplo.com", "JUCEG (Goiás)", "Procurador", "Não",
        "30/11/2026", "Transporte aéreo", "LA3456", "LATAM", "14:30",
        "03/12/2026", "Transporte terrestre", "", "", "15:00",
        "Ainda não tenho uma definição",
    ]
    assert linhas[2][2] == "João"
    assert linhas[2][5] == "Assessor"


def test_csv_nao_tem_o_codigo_do_qr(client, inscrever):
    codigo = inscrever().get_json()["codigo"]
    assert codigo not in client.get(URL, headers=login()).get_data(as_text=True)


def test_csv_neutraliza_formulas(client, inscrever):
    inscrever(nome="=HYPERLINK(\"http://x\")")
    linhas = ler_csv(client.get(URL, headers=login()).get_data(as_text=True))
    assert linhas[1][2] == "'=HYPERLINK(\"http://x\")"


def test_comando_de_terminal(app):
    app.test_client().post("/api/inscricoes", json=INSCRICAO_VALIDA)
    resultado = app.test_cli_runner().invoke(args=["exportar"])
    assert resultado.exit_code == 0
    linhas = ler_csv(resultado.output)
    assert linhas[1][2] == "Maria Silva"
