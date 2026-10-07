"""Gera as artes dos slides de apoiadores do carrossel do ENAJ 2026.

Cada slide sai em duas versões (como no ENAJ 2025): horizontal para telas
grandes e vertical para o celular. As logos ficam na parte de cima; a parte de
baixo fica livre para o título, escrito no HTML.

Uso (na pasta enaj):
    python3 ferramentas/gerar_slides_apoiadores.py

Requisitos: Pillow (python3-pil) e, para logos em SVG, o Google Chrome.
Para mudar os apoiadores, edite a lista SLIDES e rode de novo.
"""

import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

RAIZ = Path(__file__).resolve().parent.parent
PASTA_LOGOS = RAIZ / "enaj-2026" / "assets" / "logos"
PASTA_SAIDA = RAIZ / "enaj-2026" / "assets" / "img" / "carrossel"

# nome do arquivo de saída -> logos do slide (arquivos em assets/logos)
SLIDES = {
    "realizacao": ["fenaju.png", "juceg.png"],
    "apoiadores-1": ["vox.webp", "logo_regin_tributos.png", "grupoA2.png"],
    "apoiadores-2": ["nuclea.png", "nic.png", "altura.png"],
    "apoiadores-3": ["logor2da-escura.svg", "lcm.png", "contabilizei.svg"],
}

# (largura, altura) da arte e área ocupada pelas logos: (x, y, largura, altura)
FORMATOS = {
    "": {"tamanho": (1920, 1080), "area": (140, 110, 1640, 620), "direcao": "linha"},
    # No celular o slide fica alto (acompanha o banner); as logos ficam no centro
    # para não serem cortadas nas laterais pelo object-cover
    "-mobile": {"tamanho": (900, 1600), "area": (170, 140, 560, 980), "direcao": "coluna"},
}

FUNDO = (255, 255, 255)


def rasterizar_svg(caminho):
    """Converte SVG em PNG transparente usando o Chrome em modo headless."""
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        raise SystemExit(f"Para converter {caminho.name} é preciso o Google Chrome instalado.")
    with tempfile.TemporaryDirectory() as tmp:
        pagina = Path(tmp) / "logo.html"
        png = Path(tmp) / "logo.png"
        pagina.write_text(
            f'<body style="margin:0;background:transparent">'
            f'<img src="{caminho.as_uri()}" style="width:1600px;height:1600px;object-fit:contain"></body>'
        )
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--default-background-color=00000000", "--allow-file-access-from-files",
             "--window-size=1600,1600", f"--screenshot={png}", pagina.as_uri()],
            check=True, capture_output=True,
        )
        return Image.open(png).convert("RGBA").copy()


def sem_fundo_branco(imagem):
    """Logos sem transparência: o branco do fundo vira transparente."""
    if imagem.getextrema()[3][0] < 255:
        return imagem
    r, g, b, _ = imagem.split()
    mais_escuro = ImageChops.darker(ImageChops.darker(r, g), b)
    imagem.putalpha(mais_escuro.point(lambda v: 0 if v > 245 else 255))
    return imagem


def carregar_logo(nome):
    caminho = PASTA_LOGOS / nome
    imagem = rasterizar_svg(caminho) if caminho.suffix == ".svg" else Image.open(caminho).convert("RGBA")
    imagem = sem_fundo_branco(imagem)
    return imagem.crop(imagem.getbbox())


def redimensionar(logo, largura_max, altura_max):
    """Equilibra o peso visual: logos largas e quadradas ocupam áreas parecidas."""
    area_alvo = largura_max * altura_max * 0.42
    escala = min(
        largura_max / logo.width,
        altura_max / logo.height,
        math.sqrt(area_alvo / (logo.width * logo.height)),
    )
    return logo.resize((round(logo.width * escala), round(logo.height * escala)), Image.LANCZOS)


def montar_slide(logos, formato):
    arte = Image.new("RGB", formato["tamanho"], FUNDO)
    x0, y0, largura, altura = formato["area"]
    quantidade = len(logos)

    for i, logo in enumerate(logos):
        if formato["direcao"] == "linha":
            celula = (x0 + i * largura / quantidade, y0, largura / quantidade, altura)
            logo = redimensionar(logo, celula[2] * 0.82, altura * 0.62)
        else:
            celula = (x0, y0 + i * altura / quantidade, largura, altura / quantidade)
            logo = redimensionar(logo, largura * 0.82, celula[3] * 0.72)
        cx, cy, cl, ca = celula
        posicao = (round(cx + (cl - logo.width) / 2), round(cy + (ca - logo.height) / 2))
        arte.paste(logo, posicao, logo)
    return arte


def main():
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    cache = {}
    for nome_slide, arquivos in SLIDES.items():
        logos = [cache.setdefault(a, carregar_logo(a)) for a in arquivos]
        for sufixo, formato in FORMATOS.items():
            destino = PASTA_SAIDA / f"{nome_slide}{sufixo}.jpg"
            montar_slide(logos, formato).save(destino, quality=88, optimize=True, progressive=True)
            print(f"gerado: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
