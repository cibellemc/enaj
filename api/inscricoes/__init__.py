"""API de inscrição do 43º ENAJ (Goiânia 2026).

Grava as inscrições em SQLite. Cada inscrição recebe um código secreto que
identifica o card de confirmação (enaj-2026/confirmacao.html?c=...) e vai no
QR code, que abre a validação de entrada (enaj-2026/validar.html?c=...).
"""

from flask import Flask

from . import admin, config, db, rotas
from .limite import LimitePorIP


def create_app(**sobrescritas):
    app = Flask(__name__)
    app.config.update(
        DB_PATH=config.DB_PATH,
        MAX_CONTENT_LENGTH=config.MAX_CONTENT_LENGTH,
        ADMIN_USUARIO=config.ADMIN_USUARIO,
        ADMIN_SENHA=config.ADMIN_SENHA,
    )
    app.config.update(sobrescritas)

    app.extensions["limite_inscricoes"] = LimitePorIP(
        config.LIMITE_INSCRICOES, config.JANELA_LIMITE_SEGUNDOS
    )
    app.extensions["limite_acessos"] = LimitePorIP(
        config.LIMITE_ACESSOS, config.JANELA_LIMITE_SEGUNDOS
    )
    app.extensions["limite_logins_falhos"] = LimitePorIP(
        config.LIMITE_LOGINS_FALHOS, config.JANELA_LIMITE_SEGUNDOS
    )

    app.teardown_appcontext(db.fechar_db)
    app.register_blueprint(rotas.bp)
    app.register_blueprint(admin.bp)

    with app.app_context():
        db.inicializar(app.config["DB_PATH"])

    return app
