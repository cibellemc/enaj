# Eventos JUCEPI

Site com o histórico de eventos da JUCEPI (eventos.jucepi.pi.gov.br) e a API de
inscrição do 43º ENAJ.

## Estrutura

```
enaj/
├── index.html, style.css, script.js   Lista de todos os eventos (página principal)
├── logo/                              Logos usadas na página principal
├── enaj-2025/                         Página do 42º ENAJ (Foz do Iguaçu)
├── enaj-2026/                         Página do 43º ENAJ (Goiânia)
│   ├── index.html                     Início (carrossel, evento, FENAJU, local, apoiadores)
│   ├── programacao.html
│   ├── orientacoes-gerais.html        Guia de Goiânia em PDF
│   ├── inscricao.html                 Formulário de inscrição
│   ├── confirmacao.html               Card de confirmação com QR code
│   ├── validar.html                   Validação de entrada (aberta pelo QR code)
│   ├── css/style.css
│   ├── js/
│   │   ├── api.js                     Chamadas à API e utilidades compartilhadas
│   │   ├── menu.js                    Menu do celular (todas as páginas)
│   │   ├── carrossel.js · inscricao.js · confirmacao.js · validar.js
│   │   ├── tailwind.config.js
│   │   └── vendor/                    qrcode-generator e html2canvas
│   └── assets/
│       ├── img/ · logos/ · docs/
├── api/                               API de inscrições (Flask + SQLite)
│   ├── inscricoes/
│   │   ├── __init__.py                create_app()
│   │   ├── config.py                  Variáveis de configuração e limites
│   │   ├── db.py                      Banco SQLite (tabela, migração, consultas)
│   │   ├── opcoes.py                  Juntas, integrantes e opções da visita técnica
│   │   ├── validacao.py               Validação dos dados do formulário
│   │   ├── limite.py                  Limite de requisições por IP
│   │   └── rotas.py                   Rotas /api/...
│   ├── tests/                         Testes automatizados (pytest)
│   ├── dev.py                         Servidor local (site + API) sem Docker
│   └── Dockerfile
├── Dockerfile, nginx.conf             Imagem do site (nginx)
└── docker-compose.yml                 Site + API
```

## Rodar localmente (sem Docker)

```bash
sudo apt install python3-flask    # uma vez
python3 api/dev.py
```

Abra http://localhost:8000/enaj-2026/inscricao.html. O banco de teste fica em
`data/inscricoes.db` (ignorado pelo git); apague o arquivo para zerar.

## Testes da API

```bash
cd api
docker run --rm -v "$PWD":/app -w /app python:3.12-slim \
    sh -c "pip install -q -r requirements-dev.txt && python -m pytest -q"
```

## Publicar

```bash
docker compose up -d --build
```

O site fica na porta 8081. O banco de inscrições fica no volume `enaj_data`.

Ver as inscrições gravadas:

```bash
docker exec enaj_api python -c "import sqlite3; [print(r) for r in sqlite3.connect('/data/inscricoes.db').execute('select * from inscricoes')]"
```

## API

| Método | Rota                         | Uso                                              |
|--------|------------------------------|--------------------------------------------------|
| GET    | `/api/opcoes`                | Opções do formulário                             |
| POST   | `/api/inscricoes`            | Cria a inscrição e devolve o código do card      |
| GET    | `/api/inscricoes/<codigo>`   | Dados do card e da validação de entrada          |
| POST   | `/api/inscricoes/acesso`     | Busca o código do card pelo e-mail               |
| GET    | `/api/health`                | Verificação de funcionamento                     |
