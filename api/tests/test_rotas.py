import json
import sqlite3

import pytest

from inscricoes import create_app, db


def test_opcoes_do_formulario(client):
    dados = client.get("/api/opcoes").get_json()
    assert len(dados["juntas"]) == 27
    assert dados["juntas"][0] == {"valor": "JUCEAC (Acre)", "sigla": "JUCEAC", "estado": "Acre"}
    assert dados["cargos"][-2:] == ["Convidado", "Acompanhante"]
    assert [t["valor"] for t in dados["transportes"]] == ["aereo", "terrestre"]
    assert len(dados["visita_pirenopolis"]) == 3


def test_inscricao_valida_gera_codigo_e_card(client, inscrever):
    resposta = inscrever()
    assert resposta.status_code == 201
    codigo = resposta.get_json()["codigo"]

    card = client.get(f"/api/inscricoes/{codigo}").get_json()["inscricao"]
    assert card["numero"] == 1
    assert card["nome"] == "Maria Silva"
    assert card["email"] == "maria@exemplo.com"
    assert card["cargo_exibicao"] == "Procurador"
    assert card["chegada_voo"] == "LA3456"
    assert card["saida_transporte"] == "terrestre"
    # Dados de voo não são gravados para o trecho terrestre
    assert card["saida_voo"] is None and card["saida_operadora"] is None


def test_cargo_outro_usa_o_texto_digitado(client, inscrever):
    codigo = inscrever(cargo="Outro", cargo_outro="Assessor de comunicação").get_json()["codigo"]
    card = client.get(f"/api/inscricoes/{codigo}").get_json()["inscricao"]
    assert card["cargo"] == "Outro"
    assert card["cargo_exibicao"] == "Assessor de comunicação"


@pytest.mark.parametrize(
    "campos, campo_com_erro",
    [
        ({"nome": "  "}, "nome"),
        ({"email": "sem-arroba"}, "email"),
        ({"junta": "XPTO"}, "junta"),
        ({"cargo": ""}, "cargo"),
        ({"cargo": "Rei"}, "cargo"),
        ({"cargo": "Outro", "cargo_outro": ""}, "cargo_outro"),
        ({"visita_pirenopolis": "talvez"}, "visita_pirenopolis"),
        ({"chegada_data": ""}, "chegada_data"),
        ({"chegada_data": "2025-12-01"}, "chegada_data"),
        ({"chegada_data": "31/11/2026"}, "chegada_data"),
        ({"chegada_transporte": "navio"}, "chegada_transporte"),
        ({"chegada_voo": ""}, "chegada_voo"),
        ({"chegada_operadora": ""}, "chegada_operadora"),
        ({"chegada_horario": "25:00"}, "chegada_horario"),
        ({"saida_horario": ""}, "saida_horario"),
        ({"saida_data": "2026-11-29"}, "saida_data"),
    ],
)
def test_campos_invalidos(inscrever, campos, campo_com_erro):
    resposta = inscrever(**campos)
    assert resposta.status_code == 422
    assert campo_com_erro in resposta.get_json()["erros"]


def test_terrestre_nao_exige_voo(inscrever):
    resposta = inscrever(chegada_transporte="terrestre", chegada_voo="", chegada_operadora="")
    assert resposta.status_code == 201


def test_corpo_que_nao_e_json(client):
    assert client.post("/api/inscricoes", data="x").status_code == 400


def test_email_repetido_ignorando_maiusculas(inscrever):
    inscrever()
    resposta = inscrever(email="maria@EXEMPLO.com")
    assert resposta.status_code == 409
    assert resposta.get_json()["ja_inscrito"] is True


def test_robo_e_descartado(inscrever):
    resposta = inscrever(email="robo@x.com", site="http://spam")
    assert resposta.status_code == 201
    assert "codigo" not in resposta.get_json()


def test_limite_conta_so_inscricoes_gravadas(client, inscrever):
    for _ in range(15):
        client.post("/api/inscricoes", json={})
    for i in range(10):
        assert inscrever(email=f"p{i}@x.com").status_code == 201
    assert inscrever(email="p11@x.com").status_code == 429


def test_codigo_invalido_ou_inexistente(client):
    assert client.get("/api/inscricoes/curto").status_code == 404
    assert client.get("/api/inscricoes/" + "A" * 24).status_code == 404


def test_acesso_pelo_email(client, inscrever):
    codigo = inscrever().get_json()["codigo"]

    resposta = client.post("/api/inscricoes/acesso", json={"email": "  MARIA@exemplo.com "})
    assert resposta.get_json()["codigo"] == codigo
    assert client.post("/api/inscricoes/acesso", json={"email": "ninguem@x.com"}).status_code == 404
    assert client.post("/api/inscricoes/acesso", json={"email": "invalido"}).status_code == 422


def test_limite_de_acessos(client):
    for _ in range(30):
        client.post("/api/inscricoes/acesso", json={"email": "x@x.com"})
    assert client.post("/api/inscricoes/acesso", json={"email": "x@x.com"}).status_code == 429


def criar_banco_versao_1(caminho, com_codigo=True):
    """Banco no formato anterior: inscrição do presidente com lista de integrantes."""
    with sqlite3.connect(caminho) as antigo:
        antigo.execute(
            "CREATE TABLE inscricoes (id INTEGER PRIMARY KEY AUTOINCREMENT, criado_em TEXT NOT NULL,"
            " nome_presidente TEXT NOT NULL, email TEXT NOT NULL, junta TEXT NOT NULL,"
            " integrantes TEXT NOT NULL, integrantes_outro TEXT, visita_pirenopolis TEXT NOT NULL"
            + (", codigo TEXT" if com_codigo else "") + ")"
        )
        linhas = [
            ("antigo@x.com", ["Procurador", "Presidente"], None),
            ("outro@x.com", [], "Assessoria"),
        ]
        for email, integrantes, outro in linhas:
            antigo.execute(
                "INSERT INTO inscricoes (criado_em, nome_presidente, email, junta, integrantes,"
                " integrantes_outro, visita_pirenopolis) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("2026-10-07T10:00:00+00:00", "Antigo", email, "JUCEPI (Piauí)",
                 json.dumps(integrantes), outro, "Não pretendo participar"),
            )


@pytest.mark.parametrize("com_codigo", [True, False])
def test_migracao_do_banco_antigo(tmp_path, com_codigo):
    caminho = tmp_path / "antigo.db"
    criar_banco_versao_1(caminho, com_codigo)

    app = create_app(DB_PATH=str(caminho))
    with app.app_context():
        inscricoes = db.listar_inscricoes()

    assert [i["nome"] for i in inscricoes] == ["Antigo", "Antigo"]
    assert inscricoes[0]["cargo_exibicao"] == "Procurador"
    assert (inscricoes[1]["cargo"], inscricoes[1]["cargo_exibicao"]) == ("Outro", "Assessoria")
    assert inscricoes[0]["chegada_data"] is None
    assert all(len(i["codigo"]) >= 24 for i in inscricoes)

    # Depois de migrado, o banco aceita inscrições novas normalmente
    resposta = app.test_client().post("/api/inscricoes", json={
        "nome": "Nova", "email": "nova@x.com", "junta": "JUCEPI (Piauí)", "cargo": "Convidado",
        "visita_pirenopolis": "Não pretendo participar",
        "chegada_data": "2026-12-01", "chegada_transporte": "terrestre", "chegada_horario": "08:00",
        "saida_data": "2026-12-03", "saida_transporte": "terrestre", "saida_horario": "18:00",
    })
    assert resposta.status_code == 201
