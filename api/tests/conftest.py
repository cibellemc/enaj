import pytest

from inscricoes import create_app

SENHA_ADMIN = "inscrição-2026"  # com acento de propósito

INSCRICAO_VALIDA = {
    "nome": "Maria Silva",
    "email": "Maria@Exemplo.com",
    "junta": "JUCEG (Goiás)",
    "cargo": "Procurador",
    "visita_pirenopolis": "Ainda não tenho uma definição",
    "chegada_data": "2026-11-30",
    "chegada_transporte": "aereo",
    "chegada_voo": "LA3456",
    "chegada_operadora": "LATAM",
    "chegada_horario": "14:30",
    "saida_data": "2026-12-03",
    "saida_transporte": "terrestre",
    "saida_horario": "15:00",
}


@pytest.fixture
def app(tmp_path):
    return create_app(DB_PATH=str(tmp_path / "teste.db"), ADMIN_SENHA=SENHA_ADMIN, TESTING=True)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def inscrever(client):
    def _inscrever(**campos):
        return client.post("/api/inscricoes", json={**INSCRICAO_VALIDA, **campos})
    return _inscrever
