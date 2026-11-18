from __future__ import annotations

import sqlite3
from typing import Any

import pytest

from opencode_harness.assistente import (
    AssistenteVendas,
    criar_banco,
    detectar_intencao,
    ferramentas_do_banco,
    formatar_moeda,
    normalizar,
    produtos_mais_vendidos,
    receita_por_canal,
    receita_por_categoria,
    receita_por_uf,
    receita_total,
    resumo_geral,
    vendas_por_mes,
)
from opencode_harness.dados import gerar_vendas, limpar_vendas
from opencode_harness.llm import ChamadaFerramenta, ProvedorFalso, Resposta


@pytest.fixture(scope="module")
def conn() -> sqlite3.Connection:
    conexao = criar_banco(limpar_vendas(gerar_vendas(n=400, seed=17)))
    yield conexao
    conexao.close()


def test_normalizar_remove_acento_e_caixa() -> None:
    assert normalizar("  Receita por CATEGORIA  ") == "receita por categoria"
    assert normalizar("São Paulo, evolução") == "sao paulo, evolucao"


def test_formatar_moeda_usa_padrao_brasileiro() -> None:
    assert formatar_moeda(1234.5) == "R$ 1.234,50"
    assert formatar_moeda(0) == "R$ 0,00"
    assert formatar_moeda(1234567.891) == "R$ 1.234.567,89"
    assert formatar_moeda(-1234.5) == "R$ -1.234,50"
    assert formatar_moeda(9876543210.12) == "R$ 9.876.543.210,12"


def test_criar_banco_bloqueia_escrita(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        conn.execute("DELETE FROM vendas")
    assert receita_total(conn)["vendas"] > 0  # leitura continua funcionando


@pytest.mark.parametrize(
    ("pergunta", "esperado"),
    [
        ("Qual é a receita total?", "receita_total"),
        ("Quanto faturei no ano?", "receita_total"),
        ("Receita por categoria", "categoria"),
        ("Qual estado vende mais?", "uf"),
        ("Receita por canal", "canal"),
        ("Qual o ticket por canal?", "canal"),
        ("Como foi a evolução mensal?", "mes"),
        ("Quais os produtos mais vendidos?", "produtos"),
        ("Quantas vendas temos?", "contagem"),
        ("Me dê um resumo", "resumo"),
        ("Qual a cor do céu?", None),
        ("", None),
        ("   ", None),
        ("???", None),
    ],
)
def test_detectar_intencao(pergunta: str, esperado: str | None) -> None:
    assert detectar_intencao(pergunta) == esperado


def test_receita_total_fecha_com_a_soma(conn: sqlite3.Connection) -> None:
    dados = receita_total(conn)

    assert dados["vendas"] == conn.execute("SELECT COUNT(*) FROM vendas").fetchone()[0]
    assert dados["receita"] == pytest.approx(
        conn.execute("SELECT SUM(receita) FROM vendas").fetchone()[0], abs=0.01
    )


def test_agregacoes_somam_a_receita_total(conn: sqlite3.Connection) -> None:
    total = receita_total(conn)["receita"]

    assert sum(item["receita"] for item in receita_por_categoria(conn)) == pytest.approx(
        total, abs=0.05
    )
    assert sum(item["receita"] for item in receita_por_uf(conn)) == pytest.approx(total, abs=0.05)
    assert sum(item["receita"] for item in receita_por_canal(conn)) == pytest.approx(
        total, abs=0.05
    )


def test_receita_por_categoria_ordena_do_maior(conn: sqlite3.Connection) -> None:
    linhas = receita_por_categoria(conn)

    assert linhas
    assert [linha["receita"] for linha in linhas] == sorted(
        (linha["receita"] for linha in linhas), reverse=True
    )


def test_receita_por_canal_calcula_ticket(conn: sqlite3.Connection) -> None:
    for linha in receita_por_canal(conn):
        assert linha["ticket_medio"] == pytest.approx(linha["receita"] / linha["vendas"], abs=0.01)


def test_produtos_mais_vendidos_respeita_limite(conn: sqlite3.Connection) -> None:
    linhas = produtos_mais_vendidos(conn, limite=3)

    assert len(linhas) == 3
    assert [linha["unidades"] for linha in linhas] == sorted(
        (linha["unidades"] for linha in linhas), reverse=True
    )


def test_produtos_mais_vendidos_rejeita_limite(conn: sqlite3.Connection) -> None:
    with pytest.raises(ValueError, match="limite"):
        produtos_mais_vendidos(conn, limite=0)


def test_vendas_por_mes_e_cronologico_e_cobre_2026(conn: sqlite3.Connection) -> None:
    linhas = vendas_por_mes(conn)

    assert len(linhas) == 12
    assert [linha["mes"] for linha in linhas] == sorted(linha["mes"] for linha in linhas)
    assert all(linha["mes"].startswith("2026-") for linha in linhas)


def test_resumo_geral_tem_as_pecas(conn: sqlite3.Connection) -> None:
    resumo = resumo_geral(conn)

    assert set(resumo) == {
        "receita",
        "vendas",
        "categoria_lider",
        "canal_lider",
        "melhor_mes",
    }
    assert resumo["receita"] == pytest.approx(receita_total(conn)["receita"], abs=0.01)


def test_ferramentas_sao_whitelisted_e_sem_sql(conn: sqlite3.Connection) -> None:
    nomes = {ferramenta.nome for ferramenta in ferramentas_do_banco(conn)}

    assert nomes == {
        "receita_total",
        "receita_por_categoria",
        "receita_por_uf",
        "receita_por_canal",
        "vendas_por_mes",
        "produtos_mais_vendidos",
        "resumo_geral",
    }
    assert not any("sql" in nome or "query" in nome for nome in nomes)


def test_ferramenta_de_produtos_valida_argumento(conn: sqlite3.Connection) -> None:
    ferramenta = next(
        item for item in ferramentas_do_banco(conn) if item.nome == "produtos_mais_vendidos"
    )

    assert len(ferramenta.executar({"limite": 2})) == 2
    with pytest.raises(ValueError, match="argumentos inválidos"):
        ferramenta.executar({"limite": 2, "sql": "DROP TABLE vendas"})


def test_assistente_responde_intencao_sem_chamar_provedor(conn: sqlite3.Connection) -> None:
    # ProvedorFalso sem regra e sem padrão: se o roteamento falhar, ele levanta SemResposta.
    assistente = AssistenteVendas(conn, provedor=ProvedorFalso())

    resposta = assistente.perguntar("Qual é a receita total?")

    assert "receita total" in resposta.lower()
    assert "R$" in resposta


def test_assistente_formata_categoria_e_produtos(conn: sqlite3.Connection) -> None:
    assistente = AssistenteVendas(conn, provedor=ProvedorFalso())

    assert "Receita por categoria" in assistente.perguntar("receita por categoria")
    assert "Produtos mais vendidos" in assistente.perguntar("quais os produtos mais vendidos?")
    assert "ticket médio" in assistente.perguntar("receita por canal")
    assert "Melhor mês" in assistente.perguntar("evolução mensal")
    assert assistente.perguntar("me dê um resumo").startswith("Resumo:")
    assert "vendas registradas" in assistente.perguntar("quantas vendas temos?")


def test_assistente_usa_fallback_para_pergunta_desconhecida(conn: sqlite3.Connection) -> None:
    assistente = AssistenteVendas(conn, provedor=ProvedorFalso(padrao="não sei"))

    assert assistente.perguntar("qual a cor do céu?") == "não sei"


def test_assistente_fallback_executa_ferramenta(conn: sqlite3.Connection) -> None:
    provedor = ProvedorFalso(
        regras=[("me de um numero", Resposta(chamada=ChamadaFerramenta("receita_total")))]
    )
    assistente = AssistenteVendas(conn, provedor=provedor)

    resposta = assistente.perguntar("me de um numero")

    assert resposta.startswith("Resultado:")
    assert "receita" in resposta


def test_assistente_rejeita_pergunta_vazia(conn: sqlite3.Connection) -> None:
    assistente = AssistenteVendas(conn, provedor=ProvedorFalso(padrao="ok"))

    with pytest.raises(ValueError, match="pergunta"):
        assistente.perguntar("  ")


def test_assistente_respeita_limite_de_produtos(conn: sqlite3.Connection) -> None:
    assistente = AssistenteVendas(conn, provedor=ProvedorFalso(), limite_produtos=2)
    resposta = assistente.perguntar("produtos mais vendidos")

    assert resposta.count("un.)") == 2


def test_todas_as_ferramentas_respondem(conn: sqlite3.Connection) -> None:
    for ferramenta in ferramentas_do_banco(conn):
        argumentos: dict[str, Any] = {"limite": 2} if ferramenta.parametros else {}
        assert ferramenta.executar(argumentos) is not None
