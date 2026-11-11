from __future__ import annotations

import pytest

from opencode_harness.texto import agrupar_por, slug, top_n


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Análise de Dados", "analise-de-dados"),
        ("  Python  ", "python"),
        ("Preço / Valor (R$)", "preco-valor-r"),
        # o `+` na regex colapsa a sequência de símbolos em um único hífen
        ("A/B", "a-b"),
        ("A -- B", "a-b"),
        ("já-é-slug", "ja-e-slug"),
        ("", ""),
    ],
)
def test_slug(texto: str, esperado: str) -> None:
    assert slug(texto) == esperado


def test_agrupar_por_sem_normalizar_separa_grafias() -> None:
    itens = [{"categoria": "periferico"}, {"categoria": "Periférico"}]
    assert set(agrupar_por(itens, "categoria")) == {"periferico", "Periférico"}


def test_agrupar_por_com_normalizar_une_grafias() -> None:
    itens = [
        {"categoria": "hardware", "produto": "notebook"},
        {"categoria": "Periférico", "produto": "teclado"},
        {"categoria": "periferico", "produto": "mouse"},
    ]
    grupos = agrupar_por(itens, "categoria", normalizar=slug)

    assert set(grupos) == {"hardware", "periferico"}
    assert [item["produto"] for item in grupos["periferico"]] == ["teclado", "mouse"]


def test_agrupar_por_lista_vazia() -> None:
    assert agrupar_por([], "categoria") == {}


def test_agrupar_por_chave_ausente_indica_posicao() -> None:
    itens = [{"categoria": "hardware"}, {"produto": "mouse"}]

    with pytest.raises(KeyError, match="item 1"):
        agrupar_por(itens, "categoria")


def test_top_n_ordena_e_limita() -> None:
    contagem = {"hardware": 8200.0, "periferico": 1400.0, "software": 300.0}

    assert top_n(contagem, n=2) == [("hardware", 8200.0), ("periferico", 1400.0)]
    assert top_n(contagem) == [("hardware", 8200.0), ("periferico", 1400.0), ("software", 300.0)]
    assert top_n(contagem, n=10) == top_n(contagem)
    assert top_n(contagem, n=0) == []


def test_top_n_empate_mantem_ordem_de_entrada() -> None:
    assert top_n({"a": 10.0, "b": 10.0}, n=2) == [("a", 10.0), ("b", 10.0)]


def test_top_n_rejeita_n_negativo() -> None:
    with pytest.raises(ValueError, match="negativo"):
        top_n({"a": 1.0}, n=-1)
