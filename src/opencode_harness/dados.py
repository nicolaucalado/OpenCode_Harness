"""Dataset sintético de vendas e funções de análise usadas a partir da aula 05.

O dataset é gerado por código, com semente fixa: não há arquivo de dado bruto no Git e
qualquer clone reproduz exatamente a mesma base. Os notebooks só orquestram; o que
precisa de teste mora aqui.
"""

from __future__ import annotations

import calendar
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from opencode_harness.data import require_columns

__all__ = [
    "CATALOGO",
    "COLUNAS",
    "gerar_vendas",
    "limpar_vendas",
    "outliers_iqr",
    "para_sqlite",
    "resumo_mensal",
    "ticket_por_canal",
]

# (produto, categoria, preço de tabela)
CATALOGO: tuple[tuple[str, str, float], ...] = (
    ("notebook", "hardware", 3500.0),
    ("monitor", "hardware", 1200.0),
    ("teclado", "perifericos", 150.0),
    ("mouse", "perifericos", 80.0),
    ("webcam", "perifericos", 220.0),
    ("headset", "perifericos", 320.0),
    ("licenca-office", "software", 450.0),
    ("antivirus", "software", 120.0),
    ("curso-python", "educacao", 300.0),
    ("curso-sql", "educacao", 250.0),
)

COLUNAS: tuple[str, ...] = (
    "id",
    "data",
    "cliente",
    "uf",
    "produto",
    "categoria",
    "canal",
    "quantidade",
    "preco_unitario",
    "desconto_pct",
    "receita",
)

_UFS = ("SP", "RJ", "MG", "RS", "BA", "PR")
_PESOS_UF = (0.36, 0.20, 0.14, 0.12, 0.10, 0.08)
_CANAIS = ("online", "loja")
_PESOS_CANAL = (0.62, 0.38)
_PESOS_PRODUTO = (0.10, 0.08, 0.16, 0.18, 0.10, 0.08, 0.08, 0.08, 0.07, 0.07)
_PESOS_MES = (0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.10, 0.16)


def gerar_vendas(n: int = 800, seed: int = 42) -> pd.DataFrame:
    """Gera ``n`` vendas sintéticas de 2026, com semente fixa.

    A base inclui de propósito alguns problemas de qualidade: UF/canal ausentes,
    linhas duplicadas e devoluções com quantidade negativa. ``limpar_vendas`` trata
    cada caso. Nomes de clientes são anônimos (``Cliente 001``...), sem dado pessoal.
    """
    if n <= 0:
        raise ValueError("n deve ser positivo")

    rng = np.random.default_rng(seed)
    produto_idx = rng.choice(len(CATALOGO), size=n, p=_PESOS_PRODUTO)
    produtos = [CATALOGO[i] for i in produto_idx]

    meses = rng.choice(12, size=n, p=_PESOS_MES)
    dias = np.array([calendar.monthrange(2026, mes + 1)[1] for mes in meses])
    dia = rng.integers(1, dias + 1)
    datas = pd.to_datetime(
        [f"2026-{mes + 1:02d}-{d:02d}" for mes, d in zip(meses, dia, strict=True)]
    )

    quantidade = rng.choice([1, 2, 3, 4, 5], size=n, p=(0.55, 0.25, 0.10, 0.07, 0.03))
    preco_base = np.array([preco for _, _, preco in produtos])
    preco_unitario = np.round(preco_base * np.exp(rng.normal(0, 0.06, n)), 2)
    preco_unitario[rng.random(n) < 0.005] *= 6  # poucos preços fora da curva

    desconto_pct = rng.choice([0, 5, 10, 15, 20], size=n, p=(0.55, 0.15, 0.15, 0.10, 0.05))
    uf = rng.choice(_UFS, size=n, p=_PESOS_UF).astype(object)
    canal = rng.choice(_CANAIS, size=n, p=_PESOS_CANAL).astype(object)
    uf[rng.random(n) < 0.02] = None
    canal[rng.random(n) < 0.01] = None

    vendas = pd.DataFrame(
        {
            "id": np.arange(1, n + 1),
            "data": datas,
            "cliente": [f"Cliente {i:03d}" for i in rng.integers(1, 121, n)],
            "uf": uf,
            "produto": [produto for produto, _, _ in produtos],
            "categoria": [categoria for _, categoria, _ in produtos],
            "canal": canal,
            "quantidade": quantidade,
            "preco_unitario": preco_unitario,
            "desconto_pct": desconto_pct,
        }
    )
    vendas["receita"] = _calcular_receita(vendas)

    # Devoluções: quantidade negativa, que a limpeza remove.
    devolucoes = vendas.index[:3]
    vendas.loc[devolucoes, "quantidade"] = -1
    vendas["receita"] = _calcular_receita(vendas)

    # Duplicatas exatas, para o drop_duplicates da limpeza remover.
    duplicadas = vendas.sample(4, random_state=seed)
    return pd.concat([vendas, duplicadas], ignore_index=True)


def limpar_vendas(vendas: pd.DataFrame) -> pd.DataFrame:
    """Normaliza tipos, remove duplicatas/devoluções e recalcula a receita.

    Regras: texto sem espaços e em minúsculas (UF em maiúsculas), UF/canal ausentes
    viram ``NAO_INFORMADO``/``nao_informado``, quantidade e preço precisam ser
    positivos, desconto precisa estar em ``0..100``. A receita é sempre recalculada.
    """
    require_columns(vendas, COLUNAS)
    limpo = vendas.copy()

    for coluna in ("cliente", "produto", "categoria"):
        limpo[coluna] = limpo[coluna].astype("string").str.strip().str.lower()
    limpo["uf"] = limpo["uf"].astype("string").str.strip().str.upper()
    limpo["canal"] = limpo["canal"].astype("string").str.strip().str.lower()
    limpo["data"] = pd.to_datetime(limpo["data"])

    limpo = limpo.drop_duplicates()
    limpo = limpo.dropna(
        subset=[
            "data",
            "cliente",
            "produto",
            "categoria",
            "quantidade",
            "preco_unitario",
            "desconto_pct",
        ]
    )
    limpo["uf"] = limpo["uf"].fillna("NAO_INFORMADO")
    limpo["canal"] = limpo["canal"].fillna("nao_informado")

    limpo = limpo[(limpo["quantidade"] > 0) & (limpo["preco_unitario"] > 0)]
    limpo = limpo[limpo["desconto_pct"].between(0, 100)]
    limpo["receita"] = _calcular_receita(limpo)
    return limpo.loc[:, list(COLUNAS)].reset_index(drop=True)


def resumo_mensal(vendas: pd.DataFrame) -> pd.DataFrame:
    """Receita, número de vendas, unidades e ticket médio por mês."""
    require_columns(vendas, ["data", "id", "receita", "quantidade"])
    resumo = (
        vendas.assign(mes=vendas["data"].dt.to_period("M").astype(str))
        .groupby("mes", as_index=False)
        .agg(
            receita=("receita", "sum"),
            vendas=("id", "count"),
            unidades=("quantidade", "sum"),
        )
    )
    resumo["ticket_medio"] = (resumo["receita"] / resumo["vendas"]).round(2)
    return resumo.round({"receita": 2})


def ticket_por_canal(vendas: pd.DataFrame) -> pd.DataFrame:
    """Receita, vendas e ticket médio por canal, do maior para o menor."""
    require_columns(vendas, ["canal", "id", "receita"])
    por_canal = (
        vendas.groupby("canal", as_index=False)
        .agg(receita=("receita", "sum"), vendas=("id", "count"))
        .assign(
            ticket_medio=lambda dados: (dados["receita"] / dados["vendas"]).round(2),
            receita=lambda dados: dados["receita"].round(2),
        )
        .sort_values("receita", ascending=False)
    )
    return por_canal.reset_index(drop=True)


def outliers_iqr(valores: pd.Series, fator: float = 1.5) -> pd.Series:
    """Marca outliers pela regra de Tukey (fora de ``Q1 - k*IQR`` e ``Q3 + k*IQR``)."""
    if fator <= 0:
        raise ValueError("fator deve ser positivo")
    q1, q3 = valores.quantile([0.25, 0.75])
    intervalo = q3 - q1
    if intervalo == 0:
        return pd.Series(False, index=valores.index, dtype=bool)
    return (valores < q1 - fator * intervalo) | (valores > q3 + fator * intervalo)


def para_sqlite(
    vendas: pd.DataFrame,
    caminho: str | Path = ":memory:",
) -> sqlite3.Connection:
    """Carrega as vendas em uma tabela ``vendas`` do SQLite e devolve a conexão.

    ``:memory:`` (default) serve para notebook e teste; um caminho em
    ``data/processed/`` serve para persistir entre sessões (a pasta está no gitignore).
    """
    require_columns(vendas, COLUNAS)
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    dados = vendas.copy()
    dados["data"] = pd.to_datetime(dados["data"]).dt.strftime("%Y-%m-%d")
    dados.to_sql("vendas", conn, index=False, if_exists="replace")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(data)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vendas_categoria ON vendas(categoria)")
    conn.commit()
    return conn


def _calcular_receita(vendas: pd.DataFrame) -> pd.Series:
    bruto = vendas["quantidade"] * vendas["preco_unitario"]
    return (bruto * (1 - vendas["desconto_pct"] / 100)).round(2)
