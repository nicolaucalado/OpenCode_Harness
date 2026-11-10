"""Regras de preço da análise de vendas da aula 01.

Antes viviam no notebook; viraram módulo para ter teste automatizado e poderem ser
reaproveitadas por outros notebooks. Os casos de aceite estão em ``tests/test_vendas.py``.
"""

from __future__ import annotations

import math

__all__ = ["aplicar_desconto", "classificar_ticket"]

LIMITE_BAIXO = 100.0
LIMITE_MEDIO = 500.0


def classificar_ticket(valor: float) -> str:
    """Classifica um ticket em ``'baixo'`` (< 100), ``'medio'`` (< 500) ou ``'alto'``.

    Levanta ``ValueError`` para valor negativo ou não finito (``NaN``/``inf``),
    que aparecem com frequência quando a coluna vem de um CSV.
    """
    if not math.isfinite(valor):
        raise ValueError("valor deve ser um número finito")
    if valor < 0:
        raise ValueError("valor não pode ser negativo")
    if valor < LIMITE_BAIXO:
        return "baixo"
    if valor < LIMITE_MEDIO:
        return "medio"
    return "alto"


def aplicar_desconto(valor: float, percentual: float) -> float:
    """Aplica desconto percentual (0 a 100) e devolve o valor final com 2 casas.

    Levanta ``ValueError`` para valor negativo, percentual fora de ``0..100``
    ou entrada não finita.
    """
    if not math.isfinite(valor):
        raise ValueError("valor deve ser um número finito")
    if valor < 0:
        raise ValueError("valor não pode ser negativo")
    if not 0 <= percentual <= 100:
        raise ValueError("percentual deve estar entre 0 e 100")
    return round(valor * (1 - percentual / 100), 2)
