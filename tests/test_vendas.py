from __future__ import annotations

import math

import pytest

from opencode_harness.vendas import aplicar_desconto, classificar_ticket


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (0, "baixo"),
        (99.99, "baixo"),
        (100, "medio"),
        (499.99, "medio"),
        (500, "alto"),
        (1_000_000, "alto"),
    ],
)
def test_classificar_ticket_faixas(valor: float, esperado: str) -> None:
    assert classificar_ticket(valor) == esperado


@pytest.mark.parametrize("valor", [-1, -0.01, math.nan, math.inf])
def test_classificar_ticket_rejeita_entrada_invalida(valor: float) -> None:
    with pytest.raises(ValueError):
        classificar_ticket(valor)


@pytest.mark.parametrize(
    ("valor", "percentual", "esperado"),
    [
        (200, 10, 180.0),
        (100, 0, 100.0),
        (100, 100, 0.0),
        (99.99, 10, 89.99),
        (80, 12.5, 70.0),
    ],
)
def test_aplicar_desconto(valor: float, percentual: float, esperado: float) -> None:
    assert aplicar_desconto(valor, percentual) == esperado


@pytest.mark.parametrize("valor", [-1, math.nan, math.inf])
def test_aplicar_desconto_rejeita_valor_invalido(valor: float) -> None:
    with pytest.raises(ValueError, match="valor"):
        aplicar_desconto(valor, 10)


@pytest.mark.parametrize("percentual", [-0.01, 100.01, math.nan])
def test_aplicar_desconto_rejeita_percentual_invalido(percentual: float) -> None:
    with pytest.raises(ValueError, match="percentual"):
        aplicar_desconto(100, percentual)
