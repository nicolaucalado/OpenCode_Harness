"""Assistente Inteligente de Vendas — projeto de conclusão da trilha.

O assistente responde perguntas de negócio sobre a base de vendas que está no SQLite.
Ele tem **dois caminhos**:

1. **Roteamento por intenção** — pergunta reconhecida por palavra-chave vai direto para a
   consulta certa. É rápido, determinístico e não gasta token.
2. **Fallback por LLM** — pergunta fora do roteiro vai para o agente da aula 07, que só pode
   chamar as ferramentas registradas aqui. Sem chave, um provedor falso responde de forma
   determinística, então o projeto roda em qualquer clone.

Segurança: o modelo nunca recebe SQL livre nem a conexão. Ele pede uma ferramenta nomeada,
com argumentos validados; a consulta é parametrizada e definida neste módulo.
"""

from __future__ import annotations

import sqlite3
import unicodedata
from collections.abc import Iterable
from typing import Any

import pandas as pd

from opencode_harness.dados import para_sqlite
from opencode_harness.llm import (
    PROMPT_SISTEMA,
    Agente,
    Ferramenta,
    Provedor,
    ProvedorFalso,
)

__all__ = [
    "INTENCOES",
    "AssistenteVendas",
    "criar_banco",
    "detectar_intencao",
    "ferramentas_do_banco",
    "formatar_moeda",
    "normalizar",
    "produtos_mais_vendidos",
    "receita_por_canal",
    "receita_por_categoria",
    "receita_por_uf",
    "receita_total",
    "resumo_geral",
    "vendas_por_mes",
]

PROMPT_ASSISTENTE = (
    PROMPT_SISTEMA
    + """
Contexto: você atende o time comercial de uma loja de tecnologia.
Quando a pergunta não puder ser respondida por uma ferramenta, diga o que você sabe responder:
receita total, receita por categoria/UF/canal, produtos mais vendidos, evolução mensal e
contagem de vendas.
"""
)

# A ordem importa: o primeiro grupo que casar vence. Perguntas específicas vêm antes das
# genéricas ("receita por categoria" não pode cair em "receita total").
INTENCOES: dict[str, tuple[str, ...]] = {
    "resumo": ("resumo", "visao geral", "panorama"),
    "produtos": ("produto", "mais vendido", "top "),
    "categoria": ("categoria",),
    "uf": ("por uf", "por estado", "por regiao", "estado de", "estado", "uf "),
    "canal": ("canal", "por loja", "online"),
    "mes": ("por mes", "mensal", "sazonalidade", "mes a mes", "ao longo do ano"),
    "contagem": (
        "quantas vendas",
        "numero de vendas",
        "quantidade de vendas",
        "total de vendas",
    ),
    "receita_total": (
        "receita total",
        "faturamento",
        "total vendido",
        "quanto vendemos",
        "quanto faturei",
        "receita",
    ),
}


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento e com espaços colapsados — base do roteamento."""
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(
        caractere for caractere in decomposto if not unicodedata.combining(caractere)
    )
    return " ".join(sem_acento.lower().split())


def detectar_intencao(pergunta: str) -> str | None:
    """Devolve a intenção reconhecida ou ``None`` (aí o agente/LLM assume)."""
    texto = normalizar(pergunta)
    for intencao, palavras in INTENCOES.items():
        if any(palavra in texto for palavra in palavras):
            return intencao
    return None


def formatar_moeda(valor: float) -> str:
    """Formata em real brasileiro, sem depender de locale do sistema."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")


def criar_banco(vendas: pd.DataFrame) -> sqlite3.Connection:
    """Carrega as vendas limpas em SQLite (em memória) e devolve conexão somente leitura.

    O assistente nunca precisa escrever: depois da carga, ``query_only`` bloqueia qualquer
    ``INSERT``/``UPDATE``/``DELETE`` na conexão. É a terceira barreira, além da whitelist de
    ferramentas e da validação de argumentos.
    """
    conn = para_sqlite(vendas)
    conn.execute("PRAGMA query_only = ON")
    return conn


def receita_total(conn: sqlite3.Connection) -> dict[str, float | int]:
    """Receita somada e número de vendas."""
    linha = conn.execute(
        "SELECT COALESCE(ROUND(SUM(receita), 2), 0.0) AS receita, COUNT(*) AS vendas FROM vendas"
    ).fetchone()
    return {"receita": float(linha["receita"]), "vendas": int(linha["vendas"])}


def receita_por_categoria(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Receita por categoria, da maior para a menor."""
    sql = """
        SELECT categoria, ROUND(SUM(receita), 2) AS receita
        FROM vendas
        GROUP BY categoria
        ORDER BY receita DESC, categoria
    """
    return [
        {"categoria": linha["categoria"], "receita": float(linha["receita"])}
        for linha in conn.execute(sql)
    ]


def receita_por_uf(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Receita por UF; vendas sem UF aparecem como ``NAO_INFORMADO``."""
    sql = """
        SELECT uf, ROUND(SUM(receita), 2) AS receita
        FROM vendas
        GROUP BY uf
        ORDER BY receita DESC, uf
    """
    return [{"uf": linha["uf"], "receita": float(linha["receita"])} for linha in conn.execute(sql)]


def receita_por_canal(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Receita, número de vendas e ticket médio por canal."""
    sql = """
        SELECT canal,
               ROUND(SUM(receita), 2) AS receita,
               COUNT(*) AS vendas,
               ROUND(SUM(receita) / COUNT(*), 2) AS ticket_medio
        FROM vendas
        GROUP BY canal
        ORDER BY receita DESC, canal
    """
    return [
        {
            "canal": linha["canal"],
            "receita": float(linha["receita"]),
            "vendas": int(linha["vendas"]),
            "ticket_medio": float(linha["ticket_medio"]),
        }
        for linha in conn.execute(sql)
    ]


def produtos_mais_vendidos(
    conn: sqlite3.Connection,
    limite: int = 5,
) -> list[dict[str, Any]]:
    """Top ``limite`` produtos por unidades vendidas (``LIMIT`` parametrizado)."""
    if limite <= 0:
        raise ValueError("limite deve ser positivo")
    sql = """
        SELECT produto, SUM(quantidade) AS unidades, ROUND(SUM(receita), 2) AS receita
        FROM vendas
        GROUP BY produto
        ORDER BY unidades DESC, receita DESC, produto
        LIMIT ?
    """
    return [
        {
            "produto": linha["produto"],
            "unidades": int(linha["unidades"]),
            "receita": float(linha["receita"]),
        }
        for linha in conn.execute(sql, (limite,))
    ]


def vendas_por_mes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Receita e vendas por mês (``AAAA-MM``), em ordem cronológica."""
    sql = """
        SELECT substr(data, 1, 7) AS mes,
               ROUND(SUM(receita), 2) AS receita,
               COUNT(*) AS vendas
        FROM vendas
        GROUP BY mes
        ORDER BY mes
    """
    return [
        {
            "mes": linha["mes"],
            "receita": float(linha["receita"]),
            "vendas": int(linha["vendas"]),
        }
        for linha in conn.execute(sql)
    ]


def resumo_geral(conn: sqlite3.Connection) -> dict[str, Any]:
    """Panorama curto: total, categoria líder, canal líder e melhor mês."""
    total = receita_total(conn)
    categorias = receita_por_categoria(conn)
    canais = receita_por_canal(conn)
    meses = vendas_por_mes(conn)
    return {
        "receita": total["receita"],
        "vendas": total["vendas"],
        "categoria_lider": categorias[0] if categorias else None,
        "canal_lider": canais[0] if canais else None,
        "melhor_mes": max(meses, key=lambda item: item["receita"]) if meses else None,
    }


def ferramentas_do_banco(
    conn: sqlite3.Connection,
    limite_produtos: int = 5,
) -> list[Ferramenta]:
    """Ferramentas que o LLM pode chamar — a superfície de acesso ao banco.

    Nenhuma delas aceita SQL. As sem argumento fecham o caso de uso mais comum; a única
    com argumento (``produtos_mais_vendidos``) valida o limite antes de consultar.
    """

    def _receita_total() -> dict[str, Any]:
        return receita_total(conn)

    def _por_categoria() -> list[dict[str, Any]]:
        return receita_por_categoria(conn)

    def _por_uf() -> list[dict[str, Any]]:
        return receita_por_uf(conn)

    def _por_canal() -> list[dict[str, Any]]:
        return receita_por_canal(conn)

    def _por_mes() -> list[dict[str, Any]]:
        return vendas_por_mes(conn)

    def _produtos(limite: int) -> list[dict[str, Any]]:
        return produtos_mais_vendidos(conn, limite=int(limite))

    def _resumo() -> dict[str, Any]:
        return resumo_geral(conn)

    return [
        Ferramenta("receita_total", "Receita total e número de vendas", {}, _receita_total),
        Ferramenta(
            "receita_por_categoria",
            "Receita por categoria, da maior para a menor",
            {},
            _por_categoria,
        ),
        Ferramenta("receita_por_uf", "Receita por UF", {}, _por_uf),
        Ferramenta(
            "receita_por_canal",
            "Receita, vendas e ticket médio por canal",
            {},
            _por_canal,
        ),
        Ferramenta("vendas_por_mes", "Receita e vendas por mês", {}, _por_mes),
        Ferramenta(
            "produtos_mais_vendidos",
            "Produtos com mais unidades vendidas",
            {"limite": "integer"},
            _produtos,
        ),
        Ferramenta(
            "resumo_geral",
            "Panorama com total, categoria líder, canal líder e melhor mês",
            {},
            _resumo,
        ),
    ]


class AssistenteVendas:
    """Ponto de entrada: roteia por intenção e usa o agente só quando precisa."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        provedor: Provedor | None = None,
        limite_produtos: int = 5,
    ) -> None:
        self.conn = conn
        self.limite_produtos = limite_produtos
        self.provedor = provedor or ProvedorFalso(
            padrao=(
                "Não encontrei essa informação na base. Posso falar sobre receita total, "
                "receita por categoria, UF ou canal, produtos mais vendidos, evolução mensal "
                "e quantidade de vendas."
            )
        )
        self.agente = Agente(
            self.provedor,
            ferramentas_do_banco(conn, limite_produtos),
            max_passos=3,
            sistema=PROMPT_ASSISTENTE,
        )

    def perguntar(self, pergunta: str) -> str:
        """Responde à pergunta; intenção conhecida não chega ao provedor."""
        if not pergunta.strip():
            raise ValueError("pergunta não pode ser vazia")

        intencao = detectar_intencao(pergunta)
        if intencao is None:
            return self.agente.perguntar(pergunta)
        return self._responder(intencao)

    def _responder(self, intencao: str) -> str:
        if intencao == "resumo":
            return _texto_resumo(resumo_geral(self.conn))
        if intencao == "produtos":
            return _texto_produtos(produtos_mais_vendidos(self.conn, self.limite_produtos))
        if intencao == "categoria":
            return _texto_lista(
                "Receita por categoria", receita_por_categoria(self.conn), "categoria"
            )
        if intencao == "uf":
            return _texto_lista("Receita por UF", receita_por_uf(self.conn), "uf")
        if intencao == "canal":
            return _texto_canais(receita_por_canal(self.conn))
        if intencao == "mes":
            return _texto_meses(vendas_por_mes(self.conn))
        if intencao == "contagem":
            dados = receita_total(self.conn)
            return f"A base tem {dados['vendas']} vendas registradas."
        if intencao == "receita_total":
            dados = receita_total(self.conn)
            return (
                f"A receita total é {formatar_moeda(float(dados['receita']))} "
                f"em {dados['vendas']} vendas."
            )
        raise ValueError(f"intenção desconhecida: {intencao!r}")


def _texto_lista(titulo: str, linhas: Iterable[dict[str, Any]], chave: str) -> str:
    partes = [f"{linha[chave]}: {formatar_moeda(linha['receita'])}" for linha in linhas]
    return f"{titulo}: " + "; ".join(partes) + "."


def _texto_produtos(linhas: Iterable[dict[str, Any]]) -> str:
    partes = [f"{linha['produto']} ({linha['unidades']} un.)" for linha in linhas]
    return "Produtos mais vendidos: " + "; ".join(partes) + "."


def _texto_canais(linhas: Iterable[dict[str, Any]]) -> str:
    partes = [
        f"{linha['canal']}: {formatar_moeda(linha['receita'])} "
        f"(ticket médio {formatar_moeda(linha['ticket_medio'])})"
        for linha in linhas
    ]
    return "Receita por canal: " + "; ".join(partes) + "."


def _texto_meses(linhas: list[dict[str, Any]]) -> str:
    if not linhas:
        return "Não há vendas registradas."
    melhor = max(linhas, key=lambda item: item["receita"])
    pior = min(linhas, key=lambda item: item["receita"])
    return (
        f"Melhor mês: {melhor['mes']} com {formatar_moeda(melhor['receita'])}; "
        f"pior mês: {pior['mes']} com {formatar_moeda(pior['receita'])}. "
        f"A base cobre {len(linhas)} meses."
    )


def _texto_resumo(dados: dict[str, Any]) -> str:
    categoria = dados["categoria_lider"]
    canal = dados["canal_lider"]
    mes = dados["melhor_mes"]
    partes = [
        f"Receita total: {formatar_moeda(float(dados['receita']))}",
        f"{dados['vendas']} vendas",
    ]
    if categoria:
        partes.append(
            f"categoria líder: {categoria['categoria']} ({formatar_moeda(categoria['receita'])})"
        )
    if canal:
        partes.append(f"canal líder: {canal['canal']} ({formatar_moeda(canal['receita'])})")
    if mes:
        partes.append(f"melhor mês: {mes['mes']} ({formatar_moeda(mes['receita'])})")
    return "Resumo: " + "; ".join(partes) + "."
