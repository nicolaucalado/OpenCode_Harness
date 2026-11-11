from __future__ import annotations

import sqlite3

import pytest

from opencode_harness.banco import (
    conectar,
    criar_esquema,
    inserir_cliente,
    inserir_produto,
    receita_por_categoria_sql,
    registrar_venda,
    ticket_medio,
    top_clientes,
)


@pytest.fixture()
def conn() -> sqlite3.Connection:
    conexao = conectar()
    criar_esquema(conexao)
    with conexao:
        inserir_cliente(conexao, 1, "Ana", "SP")
        inserir_cliente(conexao, 2, "Bia", "RJ")
        inserir_produto(conexao, 1, "notebook", "hardware", 3500.0)
        inserir_produto(conexao, 2, "mouse", "periferico", 80.0)
        inserir_produto(conexao, 3, "teclado", "periferico", 150.0)
        inserir_produto(conexao, 4, "monitor", "hardware", 1200.0)

        registrar_venda(conexao, 1, 1, 2, "2026-08-01")
        registrar_venda(conexao, 1, 2, 10, "2026-08-02")
        registrar_venda(conexao, 2, 4, 1, "2026-09-05")
        registrar_venda(conexao, 2, 3, 4, "2026-09-06")
        registrar_venda(conexao, 1, 3, 2, "2026-10-10")
    yield conexao
    conexao.close()


def test_conectar_liga_fk_e_row_factory() -> None:
    conexao = conectar()
    assert conexao.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert conexao.row_factory is sqlite3.Row
    conexao.close()


def test_criar_esquema_e_idempotente() -> None:
    conexao = conectar()
    criar_esquema(conexao)
    criar_esquema(conexao)
    tabelas = {
        linha["name"]
        for linha in conexao.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    conexao.close()

    assert {"clientes", "produtos", "vendas"} <= tabelas


def test_venda_com_cliente_inexistente_viola_fk(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError), conn:
        registrar_venda(conn, 99, 1, 1, "2026-11-01")


def test_quantidade_zero_viola_check(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError), conn:
        registrar_venda(conn, 1, 1, 0, "2026-11-01")

    assert conn.execute("SELECT COUNT(*) FROM vendas").fetchone()[0] == 5


def test_produto_duplicado_viola_unique(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError), conn:
        inserir_produto(conn, 9, "mouse", "periferico", 90.0)


@pytest.mark.parametrize("data", ["11/11/2026", "2026-99-99", "banana"])
def test_data_invalida_viola_check(conn: sqlite3.Connection, data: str) -> None:
    with pytest.raises(sqlite3.IntegrityError), conn:
        registrar_venda(conn, 1, 1, 1, data)


def test_mesmo_cliente_produto_e_dia_em_duas_vendas_e_permitido(
    conn: sqlite3.Connection,
) -> None:
    # sem UNIQUE (cliente_id, produto_id, data): duas compras no mesmo dia são legítimas
    with conn:
        registrar_venda(conn, 1, 1, 1, "2026-08-01")

    assert conn.execute("SELECT COUNT(*) FROM vendas").fetchone()[0] == 6


def test_produto_com_preco_negativo_viola_check(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError), conn:
        inserir_produto(conn, 9, "cabo", "periferico", -1.0)


def test_receita_por_categoria_ordena_por_receita(conn: sqlite3.Connection) -> None:
    assert receita_por_categoria_sql(conn) == [
        ("hardware", 8200.0),
        ("periferico", 1700.0),
    ]


def test_uf_invalida_viola_check(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError), conn:
        inserir_cliente(conn, 9, "Caio", "11")


def test_remover_cliente_apaga_vendas_em_cascata(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute("DELETE FROM clientes WHERE id = 1")

    assert conn.execute("SELECT COUNT(*) FROM vendas").fetchone()[0] == 2
    assert {linha["cliente_id"] for linha in conn.execute("SELECT cliente_id FROM vendas")} == {2}


def test_produto_com_venda_nao_pode_ser_removido(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError), conn:
        conn.execute("DELETE FROM produtos WHERE id = 1")


def test_ticket_medio(conn: sqlite3.Connection) -> None:
    assert ticket_medio(conn) == 1980.0


def test_ticket_medio_sem_vendas() -> None:
    conexao = conectar()
    criar_esquema(conexao)
    assert ticket_medio(conexao) == 0.0
    conexao.close()


def test_top_clientes_usa_rank(conn: sqlite3.Connection) -> None:
    assert top_clientes(conn, n=1) == [("Ana", 8100.0, 1)]
    assert [linha[0] for linha in top_clientes(conn)] == ["Ana", "Bia"]
    assert [linha[2] for linha in top_clientes(conn)] == [1, 2]


def test_top_clientes_inclui_empate_na_fronteira() -> None:
    conexao = conectar()
    criar_esquema(conexao)
    with conexao:
        inserir_cliente(conexao, 1, "Ana", "SP")
        inserir_cliente(conexao, 2, "Bia", "RJ")
        inserir_produto(conexao, 1, "curso", "servico", 100.0)
        registrar_venda(conexao, 1, 1, 1, "2026-08-01")
        registrar_venda(conexao, 2, 1, 1, "2026-08-01")

    # as duas empatam em 1º; LIMIT 1 cortaria uma delas, o filtro por posicao não
    assert top_clientes(conexao, n=1) == [("Ana", 100.0, 1), ("Bia", 100.0, 1)]
    conexao.close()


def test_top_clientes_rejeita_n_negativo(conn: sqlite3.Connection) -> None:
    with pytest.raises(ValueError, match="negativo"):
        top_clientes(conn, n=-1)


def test_parametro_impede_injecao(conn: sqlite3.Connection) -> None:
    ataque = "x'); DROP TABLE clientes;--"
    linhas = conn.execute("SELECT * FROM clientes WHERE nome = ?", (ataque,)).fetchall()

    assert linhas == []
    assert conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 2
