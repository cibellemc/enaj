"""Validação dos dados enviados pelo formulário de inscrição."""

import re

from . import opcoes

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CODIGO_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


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


def validar_inscricao(dados):
    """Devolve (dados_limpos, erros). Se `erros` estiver vazio, pode gravar."""
    erros = {}

    nome = texto(dados, "nome_presidente", 200)
    if not nome:
        erros["nome_presidente"] = "Informe o nome do presidente da Junta Comercial."

    email = normalizar_email(dados.get("email"))
    if not email_valido(email):
        erros["email"] = "Informe um e-mail válido."

    junta = texto(dados, "junta", 100)
    if junta not in opcoes.VALORES_JUNTAS:
        erros["junta"] = "Selecione a Junta Comercial que representa."

    integrantes, outro, erro_integrantes = _validar_integrantes(dados)
    if erro_integrantes:
        erros["integrantes"] = erro_integrantes

    visita = texto(dados, "visita_pirenopolis", 100)
    if visita not in opcoes.VALORES_VISITA:
        erros["visita_pirenopolis"] = "Selecione uma opção."

    limpos = {
        "nome_presidente": nome,
        "email": email,
        "junta": junta,
        "integrantes": integrantes,
        "integrantes_outro": outro,
        "visita_pirenopolis": visita,
    }
    return limpos, erros


def _validar_integrantes(dados):
    recebidos = dados.get("integrantes")
    if not isinstance(recebidos, list):
        recebidos = []

    selecionados = [i for i in opcoes.INTEGRANTES if i in recebidos]
    marcou_outro = opcoes.INTEGRANTE_OUTRO in recebidos
    outro = texto(dados, "integrantes_outro", 200) if marcou_outro else None

    if marcou_outro and not outro:
        return selecionados, None, "Descreva os outros integrantes da equipe."
    if not selecionados and not marcou_outro:
        return selecionados, None, "Selecione pelo menos um integrante da equipe."
    return selecionados, outro, None
