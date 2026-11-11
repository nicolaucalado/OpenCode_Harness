"""Regras de preço da análise de vendas da aula 01.

Antes viviam no notebook; viraram módulo para ter teste automatizado e poderem ser
reaproveitadas por outros notebooks. Os casos de aceite estão em ``tests/test_vendas.py``.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal

from opencode_harness.texto import agrupar_por, slug

__all__ = [
    "LIMITE_BAIXO",
    "LIMITE_MEDIO",
    "aplicar_desconto",
    "classificar_ticket",
    "receita_por_categoria",
]

LIMITE_BAIXO = 100.0
LIMITE_MEDIO = 500.0

_DUAS_CASAS = Decimal("0.01")


def _validar_valor_monetario(valor: float) -> None:
    """Barra valor negativo e ``NaN``/``inf`` (comuns em coluna vinda de CSV)."""
    if not math.isfinite(valor):
        raise ValueError("valor deve ser um número finito")
    if valor < 0:
        raise ValueError("valor não pode ser negativo")


def classificar_ticket(valor: float) -> str:
    """Classifica um ticket em ``'baixo'`` (< 100), ``'medio'`` (< 500) ou ``'alto'``.

    Levanta ``ValueError`` para valor negativo ou não finito (``NaN``/``inf``),
    que aparecem com frequência quando a coluna vem de um CSV.
    """
    _validar_valor_monetario(valor)
    if valor < LIMITE_BAIXO:
        return "baixo"
    if valor < LIMITE_MEDIO:
        return "medio"
    return "alto"


def aplicar_desconto(valor: float, percentual: float) -> float:
    """Aplica desconto percentual (0 a 100) e devolve o valor final com 2 casas.

    O cálculo é feito em ``Decimal`` (o float de entrada é convertido uma única vez) e
    arredondado com ``ROUND_HALF_UP``, o "meio para cima" esperado em preço.
    Levanta ``ValueError`` para valor negativo, percentual fora de ``0..100`` ou
    entrada não finita.
    """
    _validar_valor_monetario(valor)
    if not math.isfinite(percentual):
        raise ValueError("percentual deve ser um número finito")
    if not 0 <= percentual <= 100:
        raise ValueError("percentual deve estar entre 0 e 100")

    fator = 1 - Decimal(str(percentual)) / 100
    return float((Decimal(str(valor)) * fator).quantize(_DUAS_CASAS, rounding=ROUND_HALF_UP))


def receita_por_categoria(vendas: Iterable[dict]) -> dict[str, float]:
    """Soma ``valor * qtd`` por categoria normalizada com ``slug``.

    A normalização na chave do agrupamento é o que impede ``'Periférico'`` e
    ``'periferico'`` de virarem grupos diferentes.
    """
    receita: dict[str, float] = {}
    for categoria, itens in agrupar_por(vendas, "categoria", normalizar=slug).items():
        receita[categoria] = round(sum(item["valor"] * item["qtd"] for item in itens), 2)
    return receita
