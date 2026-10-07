"""Rotas HTTP da API de inscrições (todas sob /api)."""

from flask import Blueprint, current_app, jsonify, request

from . import db, opcoes
from .limite import ip_do_cliente
from .validacao import codigo_valido, email_valido, normalizar_email, texto, validar_inscricao

bp = Blueprint("inscricoes", __name__, url_prefix="/api")

MSG_MUITAS_TENTATIVAS = "Muitas tentativas. Tente novamente mais tarde."
MSG_NAO_ENCONTRADA = "Inscrição não encontrada."


def _json_do_corpo():
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else None


def _erro(mensagem, status, **extras):
    return jsonify(ok=False, erro=mensagem, **extras), status


@bp.get("/health")
def health():
    return jsonify(ok=True)


@bp.get("/opcoes")
def listar_opcoes():
    return jsonify(ok=True, **opcoes.como_json())


@bp.post("/inscricoes")
def criar_inscricao():
    dados = _json_do_corpo()
    if dados is None:
        return _erro("Dados inválidos.", 400)

    # Campo escondido que só robôs preenchem: responde sucesso e descarta
    if texto(dados, "site", 200):
        return jsonify(ok=True), 201

    limite = current_app.extensions["limite_inscricoes"]
    ip = ip_do_cliente()
    if limite.excedido(ip):
        return _erro(MSG_MUITAS_TENTATIVAS, 429)

    limpos, erros = validar_inscricao(dados)
    if erros:
        return jsonify(ok=False, erros=erros), 422

    try:
        codigo = db.criar_inscricao(limpos)
    except db.EmailJaInscrito:
        return _erro(
            "Este e-mail já possui uma inscrição. Acesse sua inscrição com o e-mail.",
            409,
            ja_inscrito=True,
        )

    # Só conta inscrições gravadas, para não bloquear quem errou o preenchimento
    limite.registrar(ip)
    return jsonify(ok=True, codigo=codigo), 201


@bp.get("/inscricoes/<codigo>")
def ver_inscricao(codigo):
    """Dados do card de confirmação e da validação de entrada (QR code)."""
    inscricao = db.buscar_por_codigo(codigo) if codigo_valido(codigo) else None
    if inscricao is None:
        return _erro(MSG_NAO_ENCONTRADA, 404)
    return jsonify(ok=True, inscricao=inscricao)


@bp.post("/inscricoes/acesso")
def acessar_inscricao():
    """Busca a inscrição pelo e-mail e devolve o código do card."""
    dados = _json_do_corpo()
    if dados is None:
        return _erro("Dados inválidos.", 400)

    limite = current_app.extensions["limite_acessos"]
    ip = ip_do_cliente()
    if limite.excedido(ip):
        return _erro(MSG_MUITAS_TENTATIVAS, 429)
    limite.registrar(ip)

    email = normalizar_email(dados.get("email"))
    if not email_valido(email):
        return _erro("Informe um e-mail válido.", 422)

    codigo = db.codigo_por_email(email)
    if codigo is None:
        return _erro("Não encontramos inscrição com este e-mail.", 404)
    return jsonify(ok=True, codigo=codigo)
