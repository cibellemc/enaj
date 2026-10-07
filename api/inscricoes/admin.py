"""Área da organização: exportação das inscrições.

Pelo navegador: GET /api/admin/inscricoes.csv (usuário e senha via HTTP Basic).
Pelo terminal:  flask --app inscricoes exportar > inscricoes.csv
"""

import hmac
import sys

from flask import Blueprint, Response, current_app, request

from . import db, exportacao
from .limite import ip_do_cliente

# cli_group=None: o comando fica "flask exportar", sem prefixo
bp = Blueprint("admin", __name__, url_prefix="/api/admin", cli_group=None)


def _iguais(recebido, esperado):
    # Comparação em tempo constante; em bytes para aceitar senhas com acento
    return hmac.compare_digest((recebido or "").encode(), esperado.encode())


def _credenciais_corretas(auth):
    config = current_app.config
    return (
        auth is not None
        and _iguais(auth.username, config["ADMIN_USUARIO"])
        and _iguais(auth.password, config["ADMIN_SENHA"])
    )


def _pedir_login(mensagem="Informe usuário e senha da organização."):
    return Response(
        mensagem,
        401,
        {"WWW-Authenticate": 'Basic realm="Inscricoes ENAJ 2026", charset="UTF-8"'},
        mimetype="text/plain",
    )


@bp.before_request
def exigir_login():
    if not current_app.config["ADMIN_SENHA"]:
        return Response("Exportação desativada: defina ADMIN_SENHA no servidor.", 503, mimetype="text/plain")

    limite = current_app.extensions["limite_logins_falhos"]
    ip = ip_do_cliente()
    if limite.excedido(ip):
        return Response("Muitas tentativas. Tente novamente mais tarde.", 429, mimetype="text/plain")

    if not _credenciais_corretas(request.authorization):
        if request.authorization is not None:
            limite.registrar(ip)
        return _pedir_login()
    return None


@bp.get("/inscricoes.csv")
def exportar_csv():
    conteudo = exportacao.gerar_csv(db.listar_inscricoes())
    return Response(
        conteudo,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{exportacao.nome_do_arquivo()}"',
            "Cache-Control": "no-store",
        },
    )


@bp.cli.command("exportar")
def exportar_terminal():
    """Escreve o CSV das inscrições na saída padrão."""
    sys.stdout.write(exportacao.gerar_csv(db.listar_inscricoes()))

