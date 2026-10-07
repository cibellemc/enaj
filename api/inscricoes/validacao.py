"""Validação dos dados enviados pelo formulário de inscrição."""

import re
from datetime import date

from . import opcoes

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CODIGO_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
HORARIO_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

# Datas aceitas para chegada e saída de Goiânia (o evento é de 1º a 3/12/2026)
DATA_MINIMA = date(2026, 11, 1)
DATA_MAXIMA = date(2026, 12, 31)

TRECHOS = {
    "chegada": "chegada a Goiânia",
    "saida": "saída de Goiânia",
}


def texto(dados, campo, maximo):
    """Lê um campo de texto do JSON, sem espaços nas pontas e com tamanho máximo."""
    valor = dados.get(campo)
    if not isinstance(valor, str):
        return ""
    return valor.strip()[:maximo]


def normalizar_email(valor):
    return valor.strip().lower()[:254] if isinstance(valor, str) else ""


def email_valido(email):
    return bool(EMAIL_RE.match(email))


def codigo_valido(codigo):
    return bool(CODIGO_RE.match(codigo))


def ler_data(valor):
    try:
        lida = date.fromisoformat(valor)
    except ValueError:
        return None
    return lida if DATA_MINIMA <= lida <= DATA_MAXIMA else None


def validar_inscricao(dados):
    """Devolve (dados_limpos, erros). Se `erros` estiver vazio, pode gravar."""
    erros = {}

    nome = texto(dados, "nome", 200)
    if not nome:
        erros["nome"] = "Informe seu nome."

    email = normalizar_email(dados.get("email"))
    if not email_valido(email):
        erros["email"] = "Informe um e-mail válido."

    junta = texto(dados, "junta", 100)
    if junta not in opcoes.VALORES_JUNTAS:
        erros["junta"] = "Selecione a Junta Comercial que representa."

    cargo, cargo_outro = _validar_cargo(dados, erros)

    visita = texto(dados, "visita_pirenopolis", 100)
    if visita not in opcoes.VALORES_VISITA:
        erros["visita_pirenopolis"] = "Selecione uma opção."

    limpos = {
        "nome": nome,
        "email": email,
        "junta": junta,
        "cargo": cargo,
        "cargo_outro": cargo_outro,
        "visita_pirenopolis": visita,
    }
    # Quem já está em Goiânia não informa chegada nem saída
    limpos["mora_em_goiania"] = dados.get("mora_em_goiania") is True
    for trecho in TRECHOS:
        if limpos["mora_em_goiania"]:
            limpos.update(_trecho_vazio(trecho))
        else:
            limpos.update(_validar_trecho(dados, trecho, erros))

    chegada, saida = ler_data(limpos["chegada_data"] or ""), ler_data(limpos["saida_data"] or "")
    if chegada and saida and saida < chegada:
        erros["saida_data"] = "A saída não pode ser antes da chegada."

    return limpos, erros


def _validar_cargo(dados, erros):
    cargo = texto(dados, "cargo", 100)
    if cargo == opcoes.CARGO_OUTRO:
        cargo_outro = texto(dados, "cargo_outro", 100)
        if not cargo_outro:
            erros["cargo_outro"] = "Informe qual é o seu cargo."
        return cargo, cargo_outro or None
    if cargo not in opcoes.CARGOS:
        erros["cargo"] = "Selecione o seu cargo."
    return cargo, None


def _trecho_vazio(trecho):
    return {f"{trecho}_{campo}": None for campo in ("data", "transporte", "voo", "operadora", "horario")}


def _validar_trecho(dados, trecho, erros):
    """Valida a chegada ou a saída: data, meio de transporte e dados do voo/horário."""
    descricao = TRECHOS[trecho]

    def campo(nome):
        return f"{trecho}_{nome}"

    data_texto = texto(dados, campo("data"), 10)
    if not ler_data(data_texto):
        erros[campo("data")] = f"Informe a data de {descricao} (novembro ou dezembro de 2026)."

    transporte = texto(dados, campo("transporte"), 20)
    if transporte not in opcoes.VALORES_TRANSPORTE:
        erros[campo("transporte")] = "Selecione o meio de transporte."

    horario = texto(dados, campo("horario"), 5)
    if transporte and not HORARIO_RE.match(horario):
        erros[campo("horario")] = "Informe o horário (ex.: 14:30)."

    voo = operadora = None
    if transporte == "aereo":
        voo = texto(dados, campo("voo"), 20)
        operadora = texto(dados, campo("operadora"), 60)
        if not voo:
            erros[campo("voo")] = "Informe o número do voo."
        if not operadora:
            erros[campo("operadora")] = "Informe a companhia aérea."

    return {
        campo("data"): data_texto,
        campo("transporte"): transporte,
        campo("voo"): voo or None,
        campo("operadora"): operadora or None,
        campo("horario"): horario,
    }
