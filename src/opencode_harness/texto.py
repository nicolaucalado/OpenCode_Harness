"""Normalização de texto e agrupamento usados na aula 02.

As funções viviam no notebook; agora são módulo com teste em ``tests/test_texto.py``.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable

__all__ = ["agrupar_por", "slug", "top_n"]


def slug(texto: str) -> str:
    """Transforma texto livre em chave: ``'Análise de Dados'`` → ``'analise-de-dados'``.

    Remove acentos, baixa a caixa e troca qualquer sequência de caracteres não
    alfanuméricos por um único hífen (``'A/B'`` → ``'a-b'``, não ``'a--b'``).
    """
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")


def agrupar_por(
    itens: Iterable[dict],
    chave: str,
    normalizar: Callable[[str], str] | None = None,
) -> dict[str, list[dict]]:
    """Agrupa registros pelo valor de ``chave``.

    ``normalizar`` é aplicado à chave (ex.: ``slug``) para unir grafias diferentes.
    Item sem a chave levanta ``KeyError`` com a posição, em vez de virar grupo ``None``.
    """
    grupos: dict[str, list[dict]] = {}
    for indice, item in enumerate(itens):
        if chave not in item:
            raise KeyError(f"chave {chave!r} ausente no item {indice}")
        valor = item[chave]
        if normalizar is not None:
            valor = normalizar(valor)
        grupos.setdefault(valor, []).append(item)
    return grupos


def top_n(contagem: dict[str, float], n: int = 3) -> list[tuple[str, float]]:
    """Top ``n`` por valor, do maior para o menor (empates mantêm a ordem de entrada)."""
    if n < 0:
        raise ValueError("n não pode ser negativo")
    return sorted(contagem.items(), key=lambda par: par[1], reverse=True)[:n]
