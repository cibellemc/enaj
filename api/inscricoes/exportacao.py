"""Exportação das inscrições em CSV (abre direto no Excel e no LibreOffice)."""

import csv
import io
from datetime import date, datetime, timedelta, timezone

from . import opcoes

# Horário de Brasília (sem horário de verão desde 2019)
FUSO_BRASILIA = timezone(timedelta(hours=-3))

# O código secreto do QR code não é exportado: ele funciona como credencial de entrada
COLUNAS = [
    ("Nº", lambda i: i["numero"]),
    ("Data da inscrição", lambda i: _data_hora_local(i["criado_em"])),
    ("Nome", lambda i: i["nome"]),
    ("E-mail", lambda i: i["email"]),
    ("Junta Comercial", lambda i: i["junta"]),
    ("Cargo", lambda i: i["cargo_exibicao"] or ""),
    ("Chegada - data", lambda i: _data(i["chegada_data"])),
    ("Chegada - transporte", lambda i: _transporte(i["chegada_transporte"])),
    ("Chegada - voo", lambda i: i["chegada_voo"] or ""),
    ("Chegada - companhia aérea", lambda i: i["chegada_operadora"] or ""),
    ("Chegada - horário", lambda i: i["chegada_horario"] or ""),
    ("Saída - data", lambda i: _data(i["saida_data"])),
    ("Saída - transporte", lambda i: _transporte(i["saida_transporte"])),
    ("Saída - voo", lambda i: i["saida_voo"] or ""),
    ("Saída - companhia aérea", lambda i: i["saida_operadora"] or ""),
    ("Saída - horário", lambda i: i["saida_horario"] or ""),
    ("Visita técnica a Pirenópolis", lambda i: i["visita_pirenopolis"]),
]


# Textos que o Excel interpretaria como fórmula (os dados vêm de um formulário público)
INICIO_DE_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def _celula_segura(valor):
    if isinstance(valor, str) and valor.startswith(INICIO_DE_FORMULA):
        return "'" + valor
    return valor


def _data_hora_local(iso_utc):
    return datetime.fromisoformat(iso_utc).astimezone(FUSO_BRASILIA).strftime("%d/%m/%Y %H:%M")


def _data(iso):
    return date.fromisoformat(iso).strftime("%d/%m/%Y") if iso else ""


def _transporte(valor):
    return opcoes.ROTULOS_TRANSPORTE.get(valor, "")


def gerar_csv(inscricoes):
    """CSV com ';' e BOM UTF-8, o formato que o Excel em português abre sem ajustes."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", lineterminator="\r\n")
    escritor.writerow([titulo for titulo, _ in COLUNAS])
    for inscricao in inscricoes:
        escritor.writerow([_celula_segura(valor(inscricao)) for _, valor in COLUNAS])
    return "﻿" + saida.getvalue()


def nome_do_arquivo(agora=None):
    agora = agora or datetime.now(FUSO_BRASILIA)
    return f"inscricoes-enaj-2026-{agora:%Y-%m-%d}.csv"
