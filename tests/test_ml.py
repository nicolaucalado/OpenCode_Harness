from __future__ import annotations

import pandas as pd
import pytest

from opencode_harness.dados import gerar_vendas, limpar_vendas
from opencode_harness.data import SchemaError
from opencode_harness.ml import (
    ALVO,
    CATEGORICAS,
    NUMERICAS,
    avaliar,
    dividir,
    importancias,
    matriz_confusao,
    preparar_features,
    treinar_baseline,
    treinar_dummy,
)


@pytest.fixture(scope="module")
def vendas() -> pd.DataFrame:
    return limpar_vendas(gerar_vendas(n=500, seed=21))


@pytest.fixture(scope="module")
def dados(vendas: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return preparar_features(vendas)


def test_preparar_features_nao_usa_preco_nem_produto(
    dados: tuple[pd.DataFrame, pd.Series],
) -> None:
    features, alvo = dados

    assert list(features.columns) == list(CATEGORICAS) + list(NUMERICAS)
    assert "preco_unitario" not in features.columns
    assert "produto" not in features.columns
    assert alvo.name == ALVO


def test_preparar_features_alvo_e_binario(dados: tuple[pd.DataFrame, pd.Series]) -> None:
    _, alvo = dados

    assert set(alvo.unique()) == {0, 1}
    assert alvo.dtype == int


def test_preparar_features_rejeita_limite_invalido(vendas: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="positivo"):
        preparar_features(vendas, limite=0)


def test_preparar_features_rejeita_coluna_ausente() -> None:
    with pytest.raises(SchemaError, match="receita"):
        preparar_features(pd.DataFrame({"data": ["2026-01-01"]}))


def test_dividir_mantem_proporcao_do_alvo(dados: tuple[pd.DataFrame, pd.Series]) -> None:
    features, alvo = dados
    x_treino, x_teste, y_treino, y_teste = dividir(features, alvo, test_size=0.2, seed=4)

    assert len(x_treino) + len(x_teste) == len(features)
    assert len(x_teste) == pytest.approx(round(len(features) * 0.2), abs=2)
    assert abs(y_treino.mean() - alvo.mean()) < 0.05
    assert abs(y_teste.mean() - alvo.mean()) < 0.05


def test_dividir_rejeita_test_size_invalido(dados: tuple[pd.DataFrame, pd.Series]) -> None:
    features, alvo = dados
    with pytest.raises(ValueError, match="test_size"):
        dividir(features, alvo, test_size=1.5)


def test_baseline_supera_o_dummy(dados: tuple[pd.DataFrame, pd.Series]) -> None:
    features, alvo = dados
    x_treino, x_teste, y_treino, y_teste = dividir(features, alvo)

    baseline = treinar_baseline(x_treino, y_treino)
    dummy = treinar_dummy(x_treino, y_treino)
    metricas_baseline = avaliar(baseline, x_teste, y_teste)
    metricas_dummy = avaliar(dummy, x_teste, y_teste)

    assert metricas_baseline["acuracia"] > metricas_dummy["acuracia"]
    assert metricas_baseline["f1"] > metricas_dummy["f1"]


def test_avaliar_devolve_metricas_entre_zero_e_um(
    dados: tuple[pd.DataFrame, pd.Series],
) -> None:
    features, alvo = dados
    x_treino, x_teste, y_treino, y_teste = dividir(features, alvo)
    metricas = avaliar(treinar_baseline(x_treino, y_treino), x_teste, y_teste)

    assert set(metricas) == {"acuracia", "precisao", "recall", "f1", "roc_auc"}
    assert all(0 <= valor <= 1 for valor in metricas.values())


def test_treinar_e_reproduzivel(dados: tuple[pd.DataFrame, pd.Series]) -> None:
    features, alvo = dados
    x_treino, x_teste, y_treino, y_teste = dividir(features, alvo)

    primeira = avaliar(treinar_baseline(x_treino, y_treino), x_teste, y_teste)
    segunda = avaliar(treinar_baseline(x_treino, y_treino), x_teste, y_teste)

    assert primeira == segunda


def test_matriz_confusao_soma_as_linhas_do_teste(
    dados: tuple[pd.DataFrame, pd.Series],
) -> None:
    features, alvo = dados
    x_treino, x_teste, y_treino, y_teste = dividir(features, alvo)
    matriz = matriz_confusao(treinar_baseline(x_treino, y_treino), x_teste, y_teste)

    assert matriz.to_numpy().sum() == len(x_teste)
    assert list(matriz.index) == ["real_baixo", "real_alto"]
    assert list(matriz.columns) == ["previsto_baixo", "previsto_alto"]


def test_importancias_ordena_por_impacto(dados: tuple[pd.DataFrame, pd.Series]) -> None:
    features, alvo = dados
    x_treino, _, y_treino, _ = dividir(features, alvo)
    modelo = treinar_baseline(x_treino, y_treino)
    tabela = importancias(modelo, top=5)

    assert len(tabela) == 5
    assert tabela["impacto"].is_monotonic_decreasing
    assert (tabela["impacto"] >= 0).all()


def test_importancias_rejeita_modelo_nao_pipeline(
    dados: tuple[pd.DataFrame, pd.Series],
) -> None:
    features, alvo = dados
    x_treino, _, y_treino, _ = dividir(features, alvo)
    dummy = treinar_dummy(x_treino, y_treino)

    with pytest.raises(TypeError, match="Pipeline"):
        importancias(dummy)


def test_modelo_lida_com_categoria_desconhecida(
    dados: tuple[pd.DataFrame, pd.Series],
) -> None:
    features, alvo = dados
    x_treino, x_teste, y_treino, _ = dividir(features, alvo)
    modelo = treinar_baseline(x_treino, y_treino)

    novo = x_teste.head(1).copy()
    novo.loc[novo.index[0], "categoria"] = "categoria-inexistente"
    assert modelo.predict(novo).tolist() in ([0], [1])


def test_treinar_baseline_aceita_subconjunto_de_features(
    dados: tuple[pd.DataFrame, pd.Series],
) -> None:
    features, alvo = dados
    sem_quantidade = features.drop(columns=["quantidade"])
    x_treino, x_teste, y_treino, y_teste = dividir(sem_quantidade, alvo)

    modelo = treinar_baseline(x_treino, y_treino)
    metricas = avaliar(modelo, x_teste, y_teste)

    assert metricas["acuracia"] > 0.5
    assert metricas["roc_auc"] > 0.5


def test_treinar_baseline_rejeita_features_desconhecidas(
    dados: tuple[pd.DataFrame, pd.Series],
) -> None:
    _, alvo = dados
    with pytest.raises(ValueError, match="pelo menos uma coluna"):
        treinar_baseline(pd.DataFrame({"desconhecida": range(len(alvo))}), alvo)
