"""Pacote de apoio às atividades do bootcamp Santander — Dados com Python e IA."""

from __future__ import annotations

from opencode_harness.banco import (
    conectar,
    criar_esquema,
    inserir_cliente,
    inserir_produto,
    registrar_venda,
    ticket_medio,
    top_clientes,
)
from opencode_harness.contas import (
    Carteira,
    Conta,
    ContaCorrente,
    ContaPoupanca,
    SaldoInsuficienteError,
    TipoMovimento,
    Transacao,
)
from opencode_harness.data import SchemaError, profile, require_columns, split_features_target
from opencode_harness.texto import agrupar_por, slug, top_n
from opencode_harness.vendas import (
    aplicar_desconto,
    classificar_ticket,
    receita_por_categoria,
)

__all__ = [
    "Carteira",
    "Conta",
    "ContaCorrente",
    "ContaPoupanca",
    "SaldoInsuficienteError",
    "SchemaError",
    "TipoMovimento",
    "Transacao",
    "agrupar_por",
    "aplicar_desconto",
    "classificar_ticket",
    "conectar",
    "criar_esquema",
    "inserir_cliente",
    "inserir_produto",
    "profile",
    "receita_por_categoria",
    "registrar_venda",
    "require_columns",
    "slug",
    "split_features_target",
    "ticket_medio",
    "top_clientes",
    "top_n",
]

__version__ = "0.1.0"
