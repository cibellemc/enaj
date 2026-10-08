import base64
import re

from conftest import SENHA_ADMIN

from inscricoes import relatorio_pdf

URL = "/api/admin/inscricoes.pdf"


def login(senha=SENHA_ADMIN):
    return {"Authorization": "Basic " + base64.b64encode(f"admin:{senha}".encode()).decode()}


def paginas(pdf):
    return len(re.findall(rb"/Type /Page[^s]", pdf))


def test_pdf_exige_login(client):
    assert client.get(URL).status_code == 401
    assert client.get(URL, headers=login("errada")).status_code == 401


def test_pdf_com_inscricoes(client, inscrever):
    inscrever()
    inscrever(email="joao@x.com", nome="João & <Cia>", junta="JUCEPI (Piauí)", mora_em_goiania=True)

    resposta = client.get(URL, headers=login())
    assert resposta.status_code == 200
    assert resposta.mimetype == "application/pdf"
    assert 'filename="inscricoes-enaj-2026-' in resposta.headers["Content-Disposition"]
    assert resposta.data.startswith(b"%PDF")
    assert paginas(resposta.data) >= 1


def test_pdf_sem_inscricoes(app):
    with app.app_context():
        pdf = relatorio_pdf.gerar_pdf([])
    assert pdf.startswith(b"%PDF") and paginas(pdf) == 1


def test_pdf_com_muitas_inscricoes_quebra_paginas(client, inscrever):
    for i in range(10):
        inscrever(email=f"p{i}@x.com", nome=f"Pessoa {i}")
    # o limite de 10 inscrições por IP vale para a rota; aqui basta passar de uma página
    pdf = client.get(URL, headers=login()).data
    assert paginas(pdf) >= 2


def test_comando_de_terminal_pdf(app, inscrever):
    inscrever()
    resultado = app.test_cli_runner().invoke(args=["exportar-pdf"])
    assert resultado.exit_code == 0
