"""Utilitários de dados usados nas atividades do bootcamp.

A ideia é manter aqui o código que merece teste; notebooks apenas orquestram.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

__all__ = ["SchemaError", "profile", "require_columns", "split_features_target"]


class SchemaError(ValueError):
    """Erro de esquema: o DataFrame não tem as colunas esperadas."""


def require_columns(df: pd.DataFrame, required: Iterable[str]) -> pd.DataFrame:
    """Garante que ``df`` contém todas as colunas de ``required``.

    Retorna o próprio DataFrame para permitir encadeamento.
    """
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SchemaError(f"Colunas ausentes: {', '.join(missing)}")
    return df


def split_features_target(
    df: pd.DataFrame,
    target: str,
) -> tuple[pd.DataFrame, pd.Series]:
    """Separa features (X) e alvo (y) a partir do nome da coluna alvo."""
    require_columns(df, [target])
    return df.drop(columns=[target]), df[target]


def profile(df: pd.DataFrame) -> pd.DataFrame:
    """Resumo por coluna: tipo, nulos, percentual de nulos e cardinalidade."""
    return pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "nulos": df.isna().sum(),
            "nulos_pct": (df.isna().mean() * 100).round(2),
            "unicos": df.nunique(dropna=True),
        }
    )
