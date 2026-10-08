"""Área da organização: exportação das inscrições.

Pelo navegador (usuário e senha via HTTP Basic):
    GET /api/admin/inscricoes.csv   planilha
    GET /api/admin/inscricoes.pdf   relatório formatado
Pelo terminal:
    flask --app inscricoes exportar > inscricoes.csv
    flask --app inscricoes exportar-pdf > inscricoes.pdf
"""

import hmac
import sys

from flask import Blueprint, Response, current_app, request

from . import db, exportacao, relatorio_pdf
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


@bp.get("/inscricoes.pdf")
def exportar_pdf():
    return Response(
        relatorio_pdf.gerar_pdf(db.listar_inscricoes()),
        mimetype="application/pdf",
        headers={
            # inline: abre no navegador, com opção de baixar
            "Content-Disposition": f'inline; filename="{relatorio_pdf.nome_do_arquivo()}"',
            "Cache-Control": "no-store",
        },
    )


@bp.cli.command("exportar")
def exportar_terminal():
    """Escreve o CSV das inscrições na saída padrão."""
    sys.stdout.write(exportacao.gerar_csv(db.listar_inscricoes()))


@bp.cli.command("exportar-pdf")
def exportar_pdf_terminal():
    """Escreve o relatório em PDF na saída padrão."""
    sys.stdout.buffer.write(relatorio_pdf.gerar_pdf(db.listar_inscricoes()))
