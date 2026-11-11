"""Acesso ao SQLite usado na aula 04 (banco de dados e SQL).

O notebook mostra as consultas; aqui ficam as operações que precisam de teste: conexão
com as pragmas certas, esquema, inserções parametrizadas e agregações.

``receita_por_categoria_sql`` daqui opera em uma conexão SQL; a versão da aula 02
(``opencode_harness.vendas.receita_por_categoria``) opera em uma lista de dicionários.
O sufixo evita que duas funções de mesmo propósito disputem o mesmo nome.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

__all__ = [
    "conectar",
    "criar_esquema",
    "inserir_cliente",
    "inserir_produto",
    "receita_por_categoria_sql",
    "registrar_venda",
    "ticket_medio",
    "top_clientes",
]

ESQUEMA = """
CREATE TABLE IF NOT EXISTS clientes (
    id   INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    uf   TEXT NOT NULL CHECK (uf GLOB '[A-Z][A-Z]')
);

CREATE TABLE IF NOT EXISTS produtos (
    id        INTEGER PRIMARY KEY,
    nome      TEXT NOT NULL UNIQUE,
    categoria TEXT NOT NULL,
    preco     REAL NOT NULL CHECK (preco >= 0)
);

CREATE TABLE IF NOT EXISTS vendas (
    id         INTEGER PRIMARY KEY,
    -- CASCADE: venda sem cliente não faz sentido. RESTRICT: produto com histórico não
    -- pode ser apagado do catálogo (o padrão do SQLite já é NO ACTION, mas explícito
    -- documenta a intenção).
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE RESTRICT,
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    -- Sem isso, qualquer texto entraria em `data`. O LIKE garante o formato ISO e
    -- date() rejeita mês/dia impossível (ex.: 2026-99-99), que o LIKE sozinho aceitaria.
    data       TEXT NOT NULL CHECK (data LIKE '____-__-__' AND date(data) IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_vendas_cliente ON vendas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_vendas_data    ON vendas(data);
"""


def conectar(caminho: str | Path = ":memory:") -> sqlite3.Connection:
    """Abre a conexão com ``row_factory`` (acesso por nome) e FK ligadas.

    ``:memory:`` (o default) cria um banco que vive só enquanto a conexão existir —
    ideal para teste e para o notebook.
    """
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def criar_esquema(conn: sqlite3.Connection) -> None:
    """Cria tabelas e índices; pode rodar mais de uma vez."""
    conn.executescript(ESQUEMA)
    conn.commit()


def inserir_cliente(conn: sqlite3.Connection, id_: int, nome: str, uf: str) -> None:
    """Insere cliente com SQL parametrizado (nunca concatenando valores)."""
    conn.execute(
        "INSERT INTO clientes (id, nome, uf) VALUES (?, ?, ?)",
        (id_, nome, uf),
    )


def inserir_produto(
    conn: sqlite3.Connection,
    id_: int,
    nome: str,
    categoria: str,
    preco: float,
) -> None:
    """Insere produto; ``nome`` é único e ``preco`` não pode ser negativo (CHECK)."""
    conn.execute(
        "INSERT INTO produtos (id, nome, categoria, preco) VALUES (?, ?, ?, ?)",
        (id_, nome, categoria, preco),
    )


def registrar_venda(
    conn: sqlite3.Connection,
    cliente_id: int,
    produto_id: int,
    quantidade: int,
    data: str,
) -> None:
    """Registra uma venda (data ISO ``AAAA-MM-DD``, validada por ``CHECK``).

    Não faz ``commit``: quem chama decide a transação (``with conn:`` no notebook).
    """
    conn.execute(
        "INSERT INTO vendas (cliente_id, produto_id, quantidade, data) VALUES (?, ?, ?, ?)",
        (cliente_id, produto_id, quantidade, data),
    )


def receita_por_categoria_sql(conn: sqlite3.Connection) -> list[tuple[str, float]]:
    """Receita por categoria, da maior para a menor (``JOIN`` + ``GROUP BY``)."""
    sql = """
        SELECT p.categoria AS categoria,
               ROUND(SUM(v.quantidade * p.preco), 2) AS receita
        FROM vendas AS v
        JOIN produtos AS p ON p.id = v.produto_id
        GROUP BY p.categoria
        ORDER BY receita DESC, p.categoria
    """
    return [(linha["categoria"], linha["receita"]) for linha in conn.execute(sql)]


def ticket_medio(conn: sqlite3.Connection) -> float:
    """Valor médio por linha de venda (``AVG``); 0.0 sem venda.

    Como o esquema não tem um cabeçalho de venda/carrinho, cada linha de ``vendas`` é
    uma transação. Se o modelo ganhar ``venda_id``, a divisão passa a ser por venda.
    """
    sql = """
        SELECT COALESCE(ROUND(AVG(v.quantidade * p.preco), 2), 0.0) AS ticket
        FROM vendas AS v
        JOIN produtos AS p ON p.id = v.produto_id
    """
    return conn.execute(sql).fetchone()["ticket"]


def top_clientes(
    conn: sqlite3.Connection,
    n: int = 3,
) -> list[tuple[str, float, int]]:
    """Top ``n`` clientes por receita, com posição via ``RANK() OVER``.

    Empates dividem a mesma posição (``RANK``, diferente de ``ROW_NUMBER``) e todos
    entram: o filtro é ``posicao <= n``, não ``LIMIT n``, então a lista pode ter mais
    de ``n`` linhas quando há empate na fronteira.
    """
    if n < 0:
        raise ValueError("n não pode ser negativo")
    sql = """
        WITH receita AS (
            SELECT c.nome AS nome,
                   SUM(v.quantidade * p.preco) AS total
            FROM vendas AS v
            JOIN clientes AS c ON c.id = v.cliente_id
            JOIN produtos AS p ON p.id = v.produto_id
            GROUP BY c.id
        ),
        ranking AS (
            SELECT nome,
                   ROUND(total, 2) AS total,
                   RANK() OVER (ORDER BY total DESC) AS posicao
            FROM receita
        )
        SELECT nome, total, posicao
        FROM ranking
        WHERE posicao <= ?
        ORDER BY total DESC, nome
    """
    return [(linha["nome"], linha["total"], linha["posicao"]) for linha in conn.execute(sql, (n,))]
