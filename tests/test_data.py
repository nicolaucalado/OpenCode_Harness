from __future__ import annotations

import pandas as pd
import pytest

from opencode_harness import SchemaError, profile, require_columns, split_features_target


@pytest.fixture
def df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cliente_id": [1, 2, 3, 4],
            "valor": [10.0, None, 30.0, 40.0],
            "churn": [0, 1, 0, 1],
        }
    )


def test_require_columns_ok(df: pd.DataFrame) -> None:
    assert require_columns(df, ["cliente_id", "churn"]) is df


def test_require_columns_erro(df: pd.DataFrame) -> None:
    with pytest.raises(SchemaError, match="valor_total"):
        require_columns(df, ["cliente_id", "valor_total"])


def test_split_features_target(df: pd.DataFrame) -> None:
    x, y = split_features_target(df, "churn")
    assert "churn" not in x.columns
    assert list(y) == [0, 1, 0, 1]


def test_split_features_target_sem_alvo(df: pd.DataFrame) -> None:
    with pytest.raises(SchemaError):
        split_features_target(df, "target_inexistente")


def test_profile(df: pd.DataFrame) -> None:
    resumo = profile(df)
    assert list(resumo.index) == list(df.columns)
    assert resumo.loc["valor", "nulos"] == 1
    assert resumo.loc["valor", "nulos_pct"] == 25.0
    assert resumo.loc["churn", "unicos"] == 2
