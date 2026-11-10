"""Pacote de apoio às atividades do bootcamp Santander — Dados com Python e IA."""

from __future__ import annotations

from opencode_harness.data import SchemaError, profile, require_columns, split_features_target
from opencode_harness.vendas import aplicar_desconto, classificar_ticket

__all__ = [
    "SchemaError",
    "aplicar_desconto",
    "classificar_ticket",
    "profile",
    "require_columns",
    "split_features_target",
]

__version__ = "0.1.0"
