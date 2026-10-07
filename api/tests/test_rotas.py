import sqlite3

import pytest

from inscricoes import create_app, db

INSCRICAO_VALIDA = {
    "nome_presidente": "Maria Silva",
    "email": "Maria@Exemplo.com",
    "junta": "JUCEG (Goiás)",
    "integrantes": ["Presidente", "Outro"],
    "integrantes_outro": "Assessoria",
    "visita_pirenopolis": "Ainda não tenho uma definição",
}


@pytest.fixture
def client(tmp_path):
    app = create_app(DB_PATH=str(tmp_path / "teste.db"), TESTING=True)
    return app.test_client()


def inscrever(client, **campos):
    return client.post("/api/inscricoes", json={**INSCRICAO_VALIDA, **campos})


def test_opcoes_do_formulario(client):
    dados = client.get("/api/opcoes").get_json()
    assert len(dados["juntas"]) == 27
    assert dados["juntas"][0] == {"valor": "JUCEAC (Acre)", "sigla": "JUCEAC", "estado": "Acre"}
    assert "Gerente de REDESIM" in dados["integrantes"]
    assert len(dados["visita_pirenopolis"]) == 3


def test_inscricao_valida_gera_codigo_e_card(client):
    resposta = inscrever(client)
    assert resposta.status_code == 201
    codigo = resposta.get_json()["codigo"]

    card = client.get(f"/api/inscricoes/{codigo}").get_json()["inscricao"]
    assert card["numero"] == 1
    assert card["email"] == "maria@exemplo.com"
    assert card["integrantes"] == ["Presidente"]
    assert card["integrantes_outro"] == "Assessoria"


@pytest.mark.parametrize(
    "campos, campo_com_erro",
    [
        ({"nome_presidente": "  "}, "nome_presidente"),
        ({"email": "sem-arroba"}, "email"),
        ({"junta": "XPTO"}, "junta"),
        ({"integrantes": []}, "integrantes"),
        ({"integrantes": ["Outro"], "integrantes_outro": ""}, "integrantes"),
        ({"integrantes": "Presidente"}, "integrantes"),
        ({"visita_pirenopolis": "talvez"}, "visita_pirenopolis"),
    ],
)
def test_campos_invalidos(client, campos, campo_com_erro):
    resposta = inscrever(client, **campos)
    assert resposta.status_code == 422
    assert campo_com_erro in resposta.get_json()["erros"]


def test_corpo_que_nao_e_json(client):
    assert client.post("/api/inscricoes", data="x").status_code == 400


def test_email_repetido_ignorando_maiusculas(client):
    inscrever(client)
    resposta = inscrever(client, email="maria@EXEMPLO.com")
    assert resposta.status_code == 409
    assert resposta.get_json()["ja_inscrito"] is True


def test_robo_e_descartado(client):
    resposta = inscrever(client, email="robo@x.com", site="http://spam")
    assert resposta.status_code == 201
    assert "codigo" not in resposta.get_json()


def test_limite_conta_so_inscricoes_gravadas(client):
    for _ in range(15):
        client.post("/api/inscricoes", json={})
    for i in range(10):
        assert inscrever(client, email=f"p{i}@x.com").status_code == 201
    assert inscrever(client, email="p11@x.com").status_code == 429


def test_codigo_invalido_ou_inexistente(client):
    assert client.get("/api/inscricoes/curto").status_code == 404
    assert client.get("/api/inscricoes/" + "A" * 24).status_code == 404


def test_acesso_pelo_email(client):
    codigo = inscrever(client).get_json()["codigo"]

    resposta = client.post("/api/inscricoes/acesso", json={"email": "  MARIA@exemplo.com "})
    assert resposta.get_json()["codigo"] == codigo
    assert client.post("/api/inscricoes/acesso", json={"email": "ninguem@x.com"}).status_code == 404
    assert client.post("/api/inscricoes/acesso", json={"email": "invalido"}).status_code == 422


def test_limite_de_acessos(client):
    for _ in range(30):
        client.post("/api/inscricoes/acesso", json={"email": "x@x.com"})
    assert client.post("/api/inscricoes/acesso", json={"email": "x@x.com"}).status_code == 429


def test_banco_antigo_ganha_coluna_codigo(tmp_path):
    caminho = tmp_path / "antigo.db"
    with sqlite3.connect(caminho) as antigo:
        antigo.execute(
            "CREATE TABLE inscricoes (id INTEGER PRIMARY KEY AUTOINCREMENT, criado_em TEXT NOT NULL,"
            " nome_presidente TEXT NOT NULL, email TEXT NOT NULL, junta TEXT NOT NULL,"
            " integrantes TEXT NOT NULL, integrantes_outro TEXT, visita_pirenopolis TEXT NOT NULL)"
        )
        antigo.execute(
            "INSERT INTO inscricoes VALUES (NULL, '2026-10-07T10:00:00+00:00', 'Antigo',"
            " 'antigo@x.com', 'JUCEPI (Piauí)', '[\"Presidente\"]', NULL, 'Não pretendo participar')"
        )

    app = create_app(DB_PATH=str(caminho))
    with app.app_context():
        assert len(db.codigo_por_email("antigo@x.com")) == 24
