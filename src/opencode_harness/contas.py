"""Modelo de contas e transações da aula 03 (POO).

A lógica de domínio fica aqui, fora do notebook, para poder ser testada:

- ``Transacao`` é imutável e valida os próprios dados na criação;
- ``Conta`` é abstrata e concentra saldo, histórico e as operações;
- ``ContaCorrente`` e ``ContaPoupanca`` especializam regras (limite e rendimento);
- ``Carteira`` compõe contas e agrega os saldos.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date
from enum import Enum

__all__ = [
    "Carteira",
    "Conta",
    "ContaCorrente",
    "ContaPoupanca",
    "SaldoInsuficienteError",
    "TipoMovimento",
    "Transacao",
]


class TipoMovimento(Enum):
    """Direção de uma transação."""

    ENTRADA = "entrada"
    SAIDA = "saida"


class SaldoInsuficienteError(ValueError):
    """Levantado quando um saque passa do saldo disponível."""


@dataclass(frozen=True)
class Transacao:
    """Registro imutável de uma movimentação financeira."""

    descricao: str
    valor: float
    tipo: TipoMovimento
    quando: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        if self.valor <= 0:
            raise ValueError("valor da transação deve ser positivo")
        if not self.descricao.strip():
            raise ValueError("descrição não pode ser vazia")

    @property
    def assinatura(self) -> float:
        """Valor com sinal: positivo para entradas, negativo para saídas."""
        return self.valor if self.tipo is TipoMovimento.ENTRADA else -self.valor


class Conta(ABC):
    """Conta base: encapsula saldo e histórico e define o contrato das filhas."""

    def __init__(self, titular: str, saldo_inicial: float = 0.0) -> None:
        if not titular.strip():
            raise ValueError("titular não pode ser vazio")
        if saldo_inicial < 0:
            raise ValueError("saldo inicial não pode ser negativo")
        self._titular = titular
        self._saldo = round(saldo_inicial, 2)
        self._historico: list[Transacao] = []

    @property
    def titular(self) -> str:
        return self._titular

    @property
    def saldo(self) -> float:
        return round(self._saldo, 2)

    @property
    def saldo_disponivel(self) -> float:
        """Quanto pode ser sacado; a conta corrente soma o limite."""
        return self.saldo

    @property
    def historico(self) -> tuple[Transacao, ...]:
        """Cópia imutável: a lista interna não vaza para quem consulta."""
        return tuple(self._historico)

    @abstractmethod
    def tarifa_mensal(self) -> float:
        """Valor cobrado por mês, específico de cada tipo de conta."""

    def depositar(self, valor: float, descricao: str = "depósito") -> None:
        self._registrar(Transacao(descricao, valor, TipoMovimento.ENTRADA))
        self._saldo = round(self._saldo + valor, 2)

    def sacar(self, valor: float, descricao: str = "saque") -> None:
        if valor > self.saldo_disponivel:
            raise SaldoInsuficienteError(
                f"saque de R$ {valor:.2f} acima do disponível (R$ {self.saldo_disponivel:.2f})"
            )
        self._registrar(Transacao(descricao, valor, TipoMovimento.SAIDA))
        self._saldo = round(self._saldo - valor, 2)

    def _registrar(self, transacao: Transacao) -> None:
        self._historico.append(transacao)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(titular={self.titular!r}, saldo={self.saldo:.2f})"


class ContaCorrente(Conta):
    """Conta com limite de crédito e tarifa mensal."""

    def __init__(
        self,
        titular: str,
        saldo_inicial: float = 0.0,
        limite: float = 500.0,
    ) -> None:
        super().__init__(titular, saldo_inicial)
        if limite < 0:
            raise ValueError("limite não pode ser negativo")
        self._limite = limite

    @property
    def limite(self) -> float:
        return self._limite

    @property
    def saldo_disponivel(self) -> float:
        return round(self.saldo + self._limite, 2)

    def tarifa_mensal(self) -> float:
        return 12.0


class ContaPoupanca(Conta):
    """Conta com rendimento mensal e sem tarifa."""

    def __init__(
        self,
        titular: str,
        saldo_inicial: float = 0.0,
        taxa_mensal: float = 0.005,
    ) -> None:
        super().__init__(titular, saldo_inicial)
        if not 0 <= taxa_mensal < 1:
            raise ValueError("taxa mensal deve estar entre 0 e 1")
        self._taxa_mensal = taxa_mensal

    @property
    def taxa_mensal(self) -> float:
        return self._taxa_mensal

    def tarifa_mensal(self) -> float:
        return 0.0

    def render(self) -> float:
        """Credita o rendimento do mês e devolve quanto foi creditado."""
        rendimento = round(self.saldo * self._taxa_mensal, 2)
        if rendimento > 0:
            self.depositar(rendimento, descricao="rendimento")
        return rendimento


class Carteira:
    """Composição: reúne contas e agrega os saldos por titular."""

    def __init__(self, contas: Iterable[Conta] = ()) -> None:
        self._contas = list(contas)

    def adicionar(self, conta: Conta) -> None:
        self._contas.append(conta)

    @property
    def saldo_total(self) -> float:
        return round(sum(conta.saldo for conta in self._contas), 2)

    def por_titular(self) -> dict[str, float]:
        totais: dict[str, float] = {}
        for conta in self._contas:
            totais[conta.titular] = round(totais.get(conta.titular, 0.0) + conta.saldo, 2)
        return totais

    def __len__(self) -> int:
        return len(self._contas)

    def __iter__(self) -> Iterator[Conta]:
        return iter(self._contas)

    def __repr__(self) -> str:
        return f"Carteira({len(self)} contas, saldo_total={self.saldo_total:.2f})"
