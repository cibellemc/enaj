"""Opções do formulário de inscrição.

Fonte única: a API valida com estas listas e a página de inscrição as
recebe pela rota GET /api/opcoes para montar o formulário.
"""

JUNTAS = [
    {"valor": "JUCEAC (Acre)", "sigla": "JUCEAC", "estado": "Acre"},
    {"valor": "JUCEAL (Alagoas)", "sigla": "JUCEAL", "estado": "Alagoas"},
    {"valor": "JUCAP (Amapá)", "sigla": "JUCAP", "estado": "Amapá"},
    {"valor": "JUCEA (Amazonas)", "sigla": "JUCEA", "estado": "Amazonas"},
    {"valor": "JUCEB (Bahia)", "sigla": "JUCEB", "estado": "Bahia"},
    {"valor": "JUCEC (Ceará)", "sigla": "JUCEC", "estado": "Ceará"},
    {"valor": "JUCIS-DF (Distrito Federal)", "sigla": "JUCIS-DF", "estado": "Distrito Federal"},
    {"valor": "JUCEES (Espírito Santo)", "sigla": "JUCEES", "estado": "Espírito Santo"},
    {"valor": "JUCEG (Goiás)", "sigla": "JUCEG", "estado": "Goiás"},
    {"valor": "JUCEMA (Maranhão)", "sigla": "JUCEMA", "estado": "Maranhão"},
    {"valor": "JUCEMAT (Mato Grosso)", "sigla": "JUCEMAT", "estado": "Mato Grosso"},
    {"valor": "JUCEMS (Mato Grosso do Sul)", "sigla": "JUCEMS", "estado": "Mato Grosso do Sul"},
    {"valor": "JUCEMG (Minas Gerais)", "sigla": "JUCEMG", "estado": "Minas Gerais"},
    {"valor": "JUCEPA (Pará)", "sigla": "JUCEPA", "estado": "Pará"},
    {"valor": "JUCEP (Paraíba)", "sigla": "JUCEP", "estado": "Paraíba"},
    {"valor": "JUCEPAR (Paraná)", "sigla": "JUCEPAR", "estado": "Paraná"},
    {"valor": "JUCEPE (Pernambuco)", "sigla": "JUCEPE", "estado": "Pernambuco"},
    {"valor": "JUCEPI (Piauí)", "sigla": "JUCEPI", "estado": "Piauí"},
    {"valor": "JUCERJA (Rio de Janeiro)", "sigla": "JUCERJA", "estado": "Rio de Janeiro"},
    {"valor": "JUCERN (Rio Grande do Norte)", "sigla": "JUCERN", "estado": "Rio Grande do Norte"},
    {"valor": "JUCISRS (Rio Grande do Sul)", "sigla": "JUCISRS", "estado": "Rio Grande do Sul"},
    {"valor": "JUCER (Rondônia)", "sigla": "JUCER", "estado": "Rondônia"},
    {"valor": "JUCERR (Roraima)", "sigla": "JUCERR", "estado": "Roraima"},
    {"valor": "JUCESC (Santa Catarina)", "sigla": "JUCESC", "estado": "Santa Catarina"},
    {"valor": "JUCESP (São Paulo)", "sigla": "JUCESP", "estado": "São Paulo"},
    {"valor": "JUCESE (Sergipe)", "sigla": "JUCESE", "estado": "Sergipe"},
    {"valor": "JUCETINS (Tocantins)", "sigla": "JUCETINS", "estado": "Tocantins"},
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

# Valor marcado quando a pessoa preenche "Outros integrantes"
INTEGRANTE_OUTRO = "Outro"

VISITA_PIRENOPOLIS = [
    {"valor": "Sim, tenho interesse em participar", "rotulo": "Sim, tenho interesse", "icone": "event_available"},
    {"valor": "Não pretendo participar", "rotulo": "Não pretendo participar", "icone": "event_busy"},
    {"valor": "Ainda não tenho uma definição", "rotulo": "Ainda não sei", "icone": "help"},
]

VALORES_JUNTAS = {j["valor"] for j in JUNTAS}
VALORES_VISITA = {v["valor"] for v in VISITA_PIRENOPOLIS}


def como_json():
    return {
        "juntas": JUNTAS,
        "integrantes": INTEGRANTES,
        "visita_pirenopolis": VISITA_PIRENOPOLIS,
    }
