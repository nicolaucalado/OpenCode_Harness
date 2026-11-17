from __future__ import annotations

import pandas as pd
import pytest

from opencode_harness.dados import (
    COLUNAS,
    gerar_vendas,
    limpar_vendas,
    outliers_iqr,
    para_sqlite,
    resumo_mensal,
    ticket_por_canal,
)
from opencode_harness.data import SchemaError


def test_gerar_vendas_e_deterministica_e_tem_as_colunas() -> None:
    primeira = gerar_vendas(n=60, seed=7)
    segunda = gerar_vendas(n=60, seed=7)

    pd.testing.assert_frame_equal(primeira, segunda)
    assert set(COLUNAS) == set(primeira.columns)
    assert len(primeira) >= 60


def test_gerar_vendas_rejeita_n_nao_positivo() -> None:
    with pytest.raises(ValueError, match="positivo"):
        gerar_vendas(n=0)


def test_limpar_vendas_remove_duplicatas_devolucoes_e_nulos() -> None:
    limpo = limpar_vendas(gerar_vendas(n=300, seed=11))

    assert not limpo.duplicated().any()
    assert (limpo["quantidade"] > 0).all()
    assert (limpo["preco_unitario"] > 0).all()
    assert limpo["uf"].notna().all()
    assert limpo["canal"].notna().all()
    assert limpo["data"].dtype.kind == "M"


def test_limpar_vendas_normaliza_texto() -> None:
    bruto = pd.DataFrame(
        {
            "id": [1, 2],
            "data": ["2026-01-10", "2026-01-11"],
            "cliente": [" Cliente 001 ", "Cliente 002"],
            "uf": [" sp ", None],
            "produto": [" Notebook ", "MOUSE"],
            "categoria": [" HARDWARE ", "Perifericos"],
            "canal": [" LOJA ", None],
            "quantidade": [2, 1],
            "preco_unitario": [3000.0, 80.0],
            "desconto_pct": [10, 0],
            "receita": [0.0, 0.0],
        }
    )

    limpo = limpar_vendas(bruto)

    assert list(limpo["uf"]) == ["SP", "NAO_INFORMADO"]
    assert list(limpo["canal"]) == ["loja", "nao_informado"]
    assert list(limpo["produto"]) == ["notebook", "mouse"]
    assert list(limpo["categoria"]) == ["hardware", "perifericos"]
    assert list(limpo["receita"]) == [5400.0, 80.0]


def test_limpar_vendas_recalcula_receita_adulterada() -> None:
    bruto = pd.DataFrame(
        {
            "id": [1],
            "data": ["2026-01-10"],
            "cliente": ["Cliente 001"],
            "uf": ["SP"],
            "produto": ["mouse"],
            "categoria": ["perifericos"],
            "canal": ["online"],
            "quantidade": [2],
            "preco_unitario": [80.0],
            "desconto_pct": [25],
            "receita": [999_999.0],
        }
    )

    assert limpar_vendas(bruto).loc[0, "receita"] == 120.0


def test_resumo_mensal_fecha_com_o_total() -> None:
    limpo = limpar_vendas(gerar_vendas(n=400, seed=3))
    resumo = resumo_mensal(limpo)

    assert len(resumo) == 12
    assert resumo["receita"].sum() == pytest.approx(limpo["receita"].sum(), abs=0.01)
    assert resumo["vendas"].sum() == len(limpo)
    assert (resumo["ticket_medio"] >= 0).all()


def test_ticket_por_canal_ordena_por_receita() -> None:
    limpo = limpar_vendas(gerar_vendas(n=400, seed=5))
    por_canal = ticket_por_canal(limpo)

    assert set(por_canal.columns) == {"canal", "receita", "vendas", "ticket_medio"}
    assert por_canal["receita"].is_monotonic_decreasing
    assert por_canal["receita"].sum() == pytest.approx(limpo["receita"].sum(), abs=0.01)


def test_outliers_iqr_detecta_extremo_e_lida_com_serie_constante() -> None:
    valores = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 1000.0])
    marcados = outliers_iqr(valores)

    assert bool(marcados.iloc[-1])
    assert not bool(marcados.iloc[0])
    assert not outliers_iqr(pd.Series([5.0, 5.0, 5.0])).any()


def test_outliers_iqr_rejeita_fator_invalido() -> None:
    with pytest.raises(ValueError, match="positivo"):
        outliers_iqr(pd.Series([1.0, 2.0]), fator=0)


def test_para_sqlite_carrega_e_cria_indice() -> None:
    limpo = limpar_vendas(gerar_vendas(n=200, seed=9))
    conn = para_sqlite(limpo)

    total, receita = conn.execute("SELECT COUNT(*), ROUND(SUM(receita), 2) FROM vendas").fetchone()
    indices = {
        linha["name"]
        for linha in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
    }

    assert total == len(limpo)
    assert receita == pytest.approx(limpo["receita"].sum(), abs=0.01)
    assert "idx_vendas_data" in indices
    conn.close()


def test_para_sqlite_rejeita_coluna_ausente() -> None:
    with pytest.raises(SchemaError, match="receita"):
        para_sqlite(pd.DataFrame({"id": [1]}))


def _venda(**alteracoes: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": 1,
        "data": "2026-01-10",
        "cliente": "Cliente 001",
        "uf": "SP",
        "produto": "mouse",
        "categoria": "perifericos",
        "canal": "online",
        "quantidade": 1,
        "preco_unitario": 80.0,
        "desconto_pct": 0,
        "receita": 80.0,
    }
    base.update(alteracoes)
    return base


def test_limpar_vendas_descarta_desconto_e_quantidade_invalidos() -> None:
    bruto = pd.DataFrame(
        [
            _venda(id=1, desconto_pct=150),
            _venda(id=2, desconto_pct=-10),
            _venda(id=3, quantidade=0),
            _venda(id=4, preco_unitario=-5.0),
            _venda(id=5, preco_unitario=80.0),
        ]
    )

    limpo = limpar_vendas(bruto)

    assert list(limpo["id"]) == [5]


def test_limpar_vendas_descarta_linha_sem_data_ou_cliente() -> None:
    bruto = pd.DataFrame(
        [
            _venda(id=1, data=None),
            _venda(id=2, cliente=None),
            _venda(id=3),
        ]
    )

    limpo = limpar_vendas(bruto)

    assert list(limpo["id"]) == [3]


def test_limpar_vendas_aceita_dataframe_vazio() -> None:
    limpo = limpar_vendas(pd.DataFrame(columns=list(COLUNAS)))

    assert limpo.empty
    assert list(limpo.columns) == list(COLUNAS)
