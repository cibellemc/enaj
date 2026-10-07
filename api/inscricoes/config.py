import os

DB_PATH = os.environ.get("DB_PATH", "/data/inscricoes.db")

# Tamanho máximo do corpo das requisições (o formulário é pequeno)
MAX_CONTENT_LENGTH = 16 * 1024

# Limites por IP dentro da janela abaixo
JANELA_LIMITE_SEGUNDOS = 3600
LIMITE_INSCRICOES = 10  # inscrições gravadas
LIMITE_ACESSOS = 30     # buscas de inscrição por e-mail

# Exportação das inscrições (GET /api/admin/inscricoes.csv, com usuário e senha).
# Sem ADMIN_SENHA definida, a exportação pelo navegador fica desligada.
ADMIN_USUARIO = os.environ.get("ADMIN_USUARIO", "admin")
ADMIN_SENHA = os.environ.get("ADMIN_SENHA", "")
LIMITE_LOGINS_FALHOS = 10  # tentativas de senha erradas por IP
