"""Relatório das inscrições em PDF (A4 deitado), agrupado por Junta Comercial."""

import io
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from . import opcoes
from .exportacao import FUSO_BRASILIA

LOGO = Path(__file__).parent / "recursos" / "logo-enaj.png"

AZUL = colors.HexColor("#0a3a9a")
AMARELO = colors.HexColor("#ffdd00")
LARANJA = colors.HexColor("#f7941d")
VERDE = colors.HexColor("#2e9e3e")
CINZA_TEXTO = colors.HexColor("#4b5563")
CINZA_LINHA = colors.HexColor("#e5e7eb")
FUNDO_ZEBRA = colors.HexColor("#f3f5fa")

PAGINA = landscape(A4)
MARGEM = 1.5 * cm
LARGURA_UTIL = PAGINA[0] - 2 * MARGEM

ROTULOS_VISITA = {v["valor"]: v["rotulo"] for v in opcoes.VISITA_PIRENOPOLIS}

# Colunas da lista de inscritos: (título, largura relativa)
COLUNAS = [
    ("Nº", 0.045),
    ("Nome", 0.17),
    ("Cargo", 0.13),
    ("E-mail", 0.18),
    ("Chegada", 0.165),
    ("Saída", 0.165),
    ("Visita técnica", 0.145),
]


def _estilo(nome, **atributos):
    base = {"fontName": "Helvetica", "fontSize": 8.5, "leading": 10.5, "textColor": colors.black}
    return ParagraphStyle(nome, **{**base, **atributos})


ESTILOS = {
    "titulo": _estilo("titulo", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=AZUL),
    "subtitulo": _estilo("subtitulo", fontSize=10, leading=13, textColor=CINZA_TEXTO),
    "secao": _estilo("secao", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=AZUL),
    "junta": _estilo("junta", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=AZUL),
    "celula": _estilo("celula"),
    "cabecalho": _estilo("cabecalho", fontName="Helvetica-Bold", textColor=colors.white),
    "numero_card": _estilo("numero_card", fontName="Helvetica-Bold", fontSize=24, leading=28,
                           textColor=AZUL, alignment=TA_CENTER),
    "rotulo_card": _estilo("rotulo_card", fontSize=8.5, leading=11, textColor=CINZA_TEXTO,
                           alignment=TA_CENTER),
    "vazio": _estilo("vazio", fontSize=11, leading=14, textColor=CINZA_TEXTO),
}


# ===== Textos das células =====

def _escapar(texto):
    return (texto or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _trecho(inscricao, prefixo):
    if inscricao["mora_em_goiania"]:
        return "Já está em Goiânia"
    data = inscricao[f"{prefixo}_data"]
    if not data:
        return "Não informado"
    dia = datetime.fromisoformat(data).strftime("%d/%m")
    horario = inscricao[f"{prefixo}_horario"] or ""
    if inscricao[f"{prefixo}_transporte"] == "aereo":
        voo = f'{inscricao[f"{prefixo}_voo"]} ({inscricao[f"{prefixo}_operadora"]})'
        return f"{dia} · Aéreo · {horario}<br/>{_escapar(voo)}"
    return f"{dia} · Terrestre · {horario}"


def _linha(inscricao):
    celula = ESTILOS["celula"]
    textos = [
        str(inscricao["numero"]).zfill(4),
        f'<b>{_escapar(inscricao["nome"])}</b>',
        _escapar(inscricao["cargo_exibicao"]),
        _escapar(inscricao["email"]),
        _trecho(inscricao, "chegada"),
        _trecho(inscricao, "saida"),
        ROTULOS_VISITA.get(inscricao["visita_pirenopolis"], ""),
    ]
    return [Paragraph(texto, celula) for texto in textos]


# ===== Blocos do relatório =====

def _estilo_tabela(linhas_de_dados):
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, CINZA_LINHA),
    ]
    for i in range(1, linhas_de_dados + 1):
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), FUNDO_ZEBRA))
    return TableStyle(estilo)


def _cards_resumo(inscricoes):
    visita_sim = sum(1 for i in inscricoes if i["visita_pirenopolis"] == opcoes.VISITA_PIRENOPOLIS[0]["valor"])
    numeros = [
        (len(inscricoes), "Inscritos"),
        (len({i["junta"] for i in inscricoes}), "Juntas representadas"),
        (visita_sim, "Interesse na visita técnica"),
    ]
    celulas = [[
        [Paragraph(str(valor), ESTILOS["numero_card"]), Paragraph(rotulo, ESTILOS["rotulo_card"])]
        for valor, rotulo in numeros
    ]]
    largura = LARGURA_UTIL / len(numeros)
    tabela = Table(celulas, colWidths=[largura] * len(numeros))
    tabela.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, CINZA_LINHA),
        ("INNERGRID", (0, 0), (-1, -1), 0.8, CINZA_LINHA),
        ("BACKGROUND", (0, 0), (-1, -1), FUNDO_ZEBRA),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return tabela


def _tabela_por_junta(por_junta):
    celula = ESTILOS["celula"]
    linhas = [[Paragraph("Junta Comercial", ESTILOS["cabecalho"]), Paragraph("Inscritos", ESTILOS["cabecalho"])]]
    for junta, quantidade in sorted(por_junta.items(), key=lambda item: (-item[1], item[0])):
        linhas.append([Paragraph(_escapar(junta), celula), Paragraph(str(quantidade), celula)])
    tabela = Table(linhas, colWidths=[9 * cm, 3 * cm], repeatRows=1, hAlign="LEFT")
    tabela.setStyle(_estilo_tabela(len(linhas) - 1))
    return tabela


def _lista_da_junta(junta, inscritos):
    cabecalho = [Paragraph(titulo, ESTILOS["cabecalho"]) for titulo, _ in COLUNAS]
    linhas = [cabecalho] + [_linha(i) for i in inscritos]
    tabela = Table(linhas, colWidths=[LARGURA_UTIL * fracao for _, fracao in COLUNAS], repeatRows=1)
    tabela.setStyle(_estilo_tabela(len(inscritos)))
    plural = "inscrito" if len(inscritos) == 1 else "inscritos"
    titulo = Paragraph(f"{_escapar(junta)} <font color='#4b5563' size='9'>· {len(inscritos)} {plural}</font>",
                       ESTILOS["junta"])
    # Mantém o nome da Junta junto do começo da tabela
    return [KeepTogether([titulo, Spacer(1, 4), tabela]), Spacer(1, 14)]


# ===== Cabeçalho e rodapé de cada página =====

class _CanvasNumerado(canvas.Canvas):
    """Desenha cabeçalho e rodapé depois de saber o total de páginas ("Página X de Y")."""

    gerado_em = ""  # definido em _canvas_gerado_em

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas = []

    def showPage(self):
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas)
        for estado in self._paginas:
            self.__dict__.update(estado)
            self._desenhar_moldura(total)
            super().showPage()
        super().save()

    def _desenhar_moldura(self, total):
        largura, altura = PAGINA
        topo = altura - MARGEM

        if LOGO.exists():
            self.drawImage(str(LOGO), MARGEM, topo - 1.25 * cm, height=1.25 * cm, width=0.9 * cm,
                           preserveAspectRatio=True, mask="auto")
        self.setFillColor(AZUL)
        self.setFont("Helvetica-Bold", 11)
        self.drawString(MARGEM + 1.2 * cm, topo - 0.55 * cm, "43º ENAJ · Encontro Nacional das Juntas Comerciais")
        self.setFillColor(CINZA_TEXTO)
        self.setFont("Helvetica", 8.5)
        self.drawString(MARGEM + 1.2 * cm, topo - 1.0 * cm, "Goiânia (GO) · 1º a 3 de dezembro de 2026")
        self.drawRightString(largura - MARGEM, topo - 0.55 * cm, "Relatório de inscrições")
        self.drawRightString(largura - MARGEM, topo - 1.0 * cm, f"Gerado em {self.gerado_em}")

        # Faixa com as cores da identidade visual
        y = topo - 1.45 * cm
        faixas = [(AZUL, 0.4), (AMARELO, 0.2), (LARANJA, 0.2), (VERDE, 0.2)]
        x = MARGEM
        for cor, fracao in faixas:
            self.setFillColor(cor)
            self.rect(x, y, LARGURA_UTIL * fracao, 3, stroke=0, fill=1)
            x += LARGURA_UTIL * fracao

        self.setFillColor(CINZA_TEXTO)
        self.setFont("Helvetica", 8)
        self.drawString(MARGEM, MARGEM - 0.6 * cm, "eventos.jucepi.pi.gov.br · Documento de uso interno da organização")
        self.drawRightString(largura - MARGEM, MARGEM - 0.6 * cm, f"Página {self._pageNumber} de {total}")


def _canvas_gerado_em(texto):
    """Classe de canvas com a data de geração (uma por relatório, sem estado compartilhado)."""
    return type("CanvasDoRelatorio", (_CanvasNumerado,), {"gerado_em": texto})


# ===== Montagem =====

def gerar_pdf(inscricoes, agora=None):
    agora = agora or datetime.now(FUSO_BRASILIA)
    saida = io.BytesIO()
    documento = SimpleDocTemplate(
        saida,
        pagesize=PAGINA,
        leftMargin=MARGEM,
        rightMargin=MARGEM,
        topMargin=MARGEM + 2 * cm,
        bottomMargin=MARGEM + 0.4 * cm,
        title="Inscrições - 43º ENAJ",
        author="43º ENAJ",
    )

    elementos = [
        Paragraph("Inscrições", ESTILOS["titulo"]),
        Paragraph("Lista de participantes inscritos no 43º ENAJ, agrupados por Junta Comercial.",
                  ESTILOS["subtitulo"]),
        Spacer(1, 14),
        _cards_resumo(inscricoes),
        Spacer(1, 20),
    ]

    if not inscricoes:
        elementos.append(Paragraph("Ainda não há inscrições.", ESTILOS["vazio"]))
    else:
        por_junta = defaultdict(list)
        for inscricao in inscricoes:
            por_junta[inscricao["junta"]].append(inscricao)

        elementos += [
            Paragraph("Inscritos por Junta Comercial", ESTILOS["secao"]),
            Spacer(1, 8),
            _tabela_por_junta(Counter({j: len(i) for j, i in por_junta.items()})),
            # A lista detalhada começa sempre numa página nova
            PageBreak(),
            Paragraph("Lista de inscritos", ESTILOS["secao"]),
            Spacer(1, 10),
        ]
        for junta in sorted(por_junta):
            elementos += _lista_da_junta(junta, sorted(por_junta[junta], key=lambda i: i["nome"].lower()))

    documento.build(elementos, canvasmaker=_canvas_gerado_em(agora.strftime("%d/%m/%Y às %H:%M")))
    return saida.getvalue()


def nome_do_arquivo(agora=None):
    agora = agora or datetime.now(FUSO_BRASILIA)
    return f"inscricoes-enaj-2026-{agora:%Y-%m-%d}.pdf"
