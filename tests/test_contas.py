from __future__ import annotations

import pytest

from opencode_harness.contas import (
    Carteira,
    Conta,
    ContaCorrente,
    ContaPoupanca,
    SaldoInsuficienteError,
    TipoMovimento,
    Transacao,
)


def test_transacao_rejeita_valor_nao_positivo() -> None:
    with pytest.raises(ValueError, match="positivo"):
        Transacao("teste", 0, TipoMovimento.ENTRADA)


def test_transacao_rejeita_descricao_vazia() -> None:
    with pytest.raises(ValueError, match="descrição"):
        Transacao("   ", 10, TipoMovimento.ENTRADA)


def test_transacao_assinatura() -> None:
    assert Transacao("depósito", 10, TipoMovimento.ENTRADA).assinatura == 10
    assert Transacao("saque", 10, TipoMovimento.SAIDA).assinatura == -10


def test_conta_e_abstrata() -> None:
    with pytest.raises(TypeError):
        Conta("Ana")


def test_deposito_e_saque_atualizam_saldo_e_historico() -> None:
    conta = ContaCorrente("Ana", saldo_inicial=100)
    conta.depositar(50)
    conta.sacar(30)

    assert conta.saldo == 120
    assert [transacao.tipo for transacao in conta.historico] == [
        TipoMovimento.ENTRADA,
        TipoMovimento.SAIDA,
    ]


def test_saque_acima_do_disponivel_nao_altera_saldo() -> None:
    conta = ContaCorrente("Ana", saldo_inicial=100, limite=50)

    with pytest.raises(SaldoInsuficienteError):
        conta.sacar(151)

    assert conta.saldo == 100
    assert conta.historico == ()


def test_conta_corrente_usa_limite() -> None:
    conta = ContaCorrente("Ana", saldo_inicial=100, limite=50)
    conta.sacar(140)

    assert conta.saldo == -40
    assert conta.saldo_disponivel == 10


def test_poupanca_renderiza() -> None:
    conta = ContaPoupanca("Bia", saldo_inicial=1000, taxa_mensal=0.01)

    assert conta.render() == 10
    assert conta.saldo == 1010
    assert conta.historico[-1].descricao == "rendimento"


def test_carteira_agrega_e_itera() -> None:
    carteira = Carteira(
        [
            ContaCorrente("Ana", 100),
            ContaPoupanca("Bia", 200),
        ]
    )
    carteira.adicionar(ContaCorrente("Ana", 50))

    assert len(carteira) == 3
    assert carteira.saldo_total == 350
    assert carteira.por_titular() == {"Ana": 150, "Bia": 200}
    assert len(list(carteira)) == 3
    assert "Carteira" in repr(carteira)


def test_titular_vazio() -> None:
    with pytest.raises(ValueError, match="titular"):
        ContaCorrente("   ")
