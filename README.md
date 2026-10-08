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
│   │   ├── opcoes.py                  Juntas, cargos, transportes e opções da visita
│   │   ├── validacao.py               Validação dos dados do formulário
│   │   ├── limite.py                  Limite de requisições por IP
│   │   ├── rotas.py                   Rotas públicas /api/...
│   │   ├── admin.py                   Exportação (rotas com senha e comandos de terminal)
│   │   ├── exportacao.py              Geração do CSV
│   │   ├── relatorio_pdf.py           Geração do relatório em PDF
│   │   └── recursos/                  Logo usada no PDF
│   ├── tests/                         Testes automatizados (pytest)
│   ├── dev.py                         Servidor local (site + API) sem Docker
│   └── Dockerfile
├── ferramentas/
│   └── gerar_slides_apoiadores.py     Gera as artes dos slides de apoiadores do carrossel
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

## Slides de apoiadores do carrossel

As artes dos slides "Realização" e "Nossos Apoiadores" (versão para telas grandes
e para celular) são geradas a partir das logos em `enaj-2026/assets/logos/`.
Para incluir ou trocar um apoiador, coloque a logo nessa pasta, edite a lista
`SLIDES` no topo do script e rode:

```bash
python3 ferramentas/gerar_slides_apoiadores.py
```

As artes ficam em `enaj-2026/assets/img/carrossel/`. Se criar um slide novo,
acrescente o bloco correspondente no carrossel do `enaj-2026/index.html`.

## Testes da API

```bash
cd api
docker run --rm -v "$PWD":/app -w /app python:3.12-slim \
    sh -c "pip install -q -r requirements-dev.txt && python -m pytest -q"
```

## Publicar

```bash
cp .env.example .env    # na primeira vez: defina ADMIN_SENHA no .env
docker compose up -d --build
```

O site fica na porta 8081. O banco de inscrições fica no volume `enaj_data`.

## Exportar as inscrições

Duas opções, com o mesmo usuário e senha definidos no `.env`
(`ADMIN_USUARIO` / `ADMIN_SENHA`). Sem `ADMIN_SENHA` definida, a exportação pelo
navegador fica desligada. Localmente, com `api/dev.py`, a senha é `dev`.

| Formato | Endereço | Uso |
|---------|----------|-----|
| PDF | `/api/admin/inscricoes.pdf` | Relatório formatado: resumo, inscritos por Junta e lista agrupada por Junta |
| CSV | `/api/admin/inscricoes.csv` | Planilha (separada por `;`, UTF-8), abre direto no Excel e no LibreOffice |

Exemplo: https://eventos.jucepi.pi.gov.br/api/admin/inscricoes.pdf

O código secreto do QR code não é exportado.

**Pelo terminal do servidor:**

```bash
docker exec enaj_api flask --app inscricoes exportar > inscricoes.csv
docker exec enaj_api flask --app inscricoes exportar-pdf > inscricoes.pdf
```

## API

| Método | Rota                         | Uso                                              |
|--------|------------------------------|--------------------------------------------------|
| GET    | `/api/opcoes`                | Opções do formulário                             |
| POST   | `/api/inscricoes`            | Cria a inscrição e devolve o código do card      |
| GET    | `/api/inscricoes/<codigo>`   | Dados do card e da validação de entrada          |
| POST   | `/api/inscricoes/acesso`     | Busca o código do card pelo e-mail               |
| GET    | `/api/health`                | Verificação de funcionamento                     |
| GET    | `/api/admin/inscricoes.csv`  | Exportação em CSV (usuário e senha)              |
| GET    | `/api/admin/inscricoes.pdf`  | Relatório em PDF (usuário e senha)               |
