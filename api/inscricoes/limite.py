"""Limite simples de requisições por IP, em memória.

Funciona porque a API roda com um único processo (ver Dockerfile).
"""

import time
from collections import defaultdict, deque
from threading import Lock

from flask import request


def ip_do_cliente():
    # O nginx repassa o IP real no cabeçalho X-Real-IP
    return request.headers.get("X-Real-IP") or request.remote_addr or "?"


class LimitePorIP:
    def __init__(self, maximo, janela_segundos):
        self.maximo = maximo
        self.janela = janela_segundos
        self._registros = defaultdict(deque)
        self._lock = Lock()

    def excedido(self, ip):
        agora = time.monotonic()
        with self._lock:
            fila = self._registros[ip]
            while fila and agora - fila[0] > self.janela:
                fila.popleft()
            return len(fila) >= self.maximo

    def registrar(self, ip):
        with self._lock:
            self._registros[ip].append(time.monotonic())
