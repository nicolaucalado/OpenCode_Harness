"""Baseline de classificação da aula 06.

O alvo é ``alto_valor``: a venda passou de ``LIMITE_ALTO``. De propósito, preço e produto
ficam **fora** das features — com eles a tarefa vira quase determinística e não exercita
generalização. O notebook compara o baseline com um ``DummyClassifier``.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from opencode_harness.data import require_columns

__all__ = [
    "ALVO",
    "CATEGORICAS",
    "LIMITE_ALTO",
    "NUMERICAS",
    "avaliar",
    "dividir",
    "importancias",
    "matriz_confusao",
    "preparar_features",
    "treinar_baseline",
    "treinar_dummy",
]

ALVO = "alto_valor"
LIMITE_ALTO = 1000.0
CATEGORICAS: tuple[str, ...] = ("categoria", "canal", "uf")
NUMERICAS: tuple[str, ...] = (
    "quantidade",
    "desconto_pct",
    "mes",
    "dia_semana",
    "fim_de_semana",
)
_ENTRADA: tuple[str, ...] = (
    "data",
    "categoria",
    "canal",
    "uf",
    "quantidade",
    "desconto_pct",
    "receita",
)


def preparar_features(
    vendas: pd.DataFrame,
    limite: float = LIMITE_ALTO,
) -> tuple[pd.DataFrame, pd.Series]:
    """Monta ``X`` e ``y`` a partir das vendas limpas.

    ``y`` é 1 quando ``receita >= limite``. As features usam data (mês, dia da semana,
    fim de semana), categoria, canal, UF, quantidade e desconto. Preço e produto não
    entram, para o modelo aprender contexto em vez de repetir a conta da receita.
    """
    require_columns(vendas, _ENTRADA)
    if limite <= 0:
        raise ValueError("limite deve ser positivo")

    datas = pd.to_datetime(vendas["data"])
    dados = vendas.assign(
        mes=datas.dt.month,
        dia_semana=datas.dt.day_of_week,
        fim_de_semana=(datas.dt.day_of_week >= 5).astype(int),
    )
    features = dados.loc[:, list(CATEGORICAS) + list(NUMERICAS)]
    alvo = (dados["receita"] >= limite).astype(int).rename(ALVO)
    return features, alvo


def dividir(
    features: pd.DataFrame,
    alvo: pd.Series,
    test_size: float = 0.25,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Divide em treino/teste com estratificação (mantém a proporção do alvo)."""
    if not 0 < test_size < 1:
        raise ValueError("test_size deve estar entre 0 e 1")
    return train_test_split(
        features,
        alvo,
        test_size=test_size,
        random_state=seed,
        stratify=alvo,
    )


def treinar_baseline(
    features: pd.DataFrame,
    alvo: pd.Series,
    seed: int = 42,
) -> Pipeline:
    """Regressão logística com one-hot para categóricas e escala para numéricas.

    O pré-processador usa apenas as colunas presentes em ``features``, então dá para
    treinar com um subconjunto (a ablação do notebook tira ``quantidade``).
    """
    categoricas = [coluna for coluna in CATEGORICAS if coluna in features.columns]
    numericas = [coluna for coluna in NUMERICAS if coluna in features.columns]
    if not categoricas and not numericas:
        raise ValueError("features precisa de pelo menos uma coluna conhecida")

    modelo = Pipeline(
        [
            ("preparo", _criar_preprocessador(categoricas, numericas)),
            (
                "modelo",
                LogisticRegression(max_iter=1000, random_state=seed, solver="lbfgs"),
            ),
        ]
    )
    modelo.fit(features, alvo)
    return modelo


def treinar_dummy(features: pd.DataFrame, alvo: pd.Series, seed: int = 42) -> DummyClassifier:
    """Baseline ingênuo: prevê sempre a classe mais frequente."""
    modelo = DummyClassifier(strategy="most_frequent", random_state=seed)
    modelo.fit(features, alvo)
    return modelo


def avaliar(modelo: object, features: pd.DataFrame, alvo: pd.Series) -> dict[str, float]:
    """Acurácia, precisão, recall, F1 e ROC-AUC (quando há probabilidade)."""
    previsao = modelo.predict(features)
    metricas = {
        "acuracia": accuracy_score(alvo, previsao),
        "precisao": precision_score(alvo, previsao, zero_division=0),
        "recall": recall_score(alvo, previsao, zero_division=0),
        "f1": f1_score(alvo, previsao, zero_division=0),
    }
    if hasattr(modelo, "predict_proba") and alvo.nunique() == 2:
        probabilidade = modelo.predict_proba(features)[:, 1]
        metricas["roc_auc"] = roc_auc_score(alvo, probabilidade)
    return {nome: round(float(valor), 3) for nome, valor in metricas.items()}


def matriz_confusao(
    modelo: object,
    features: pd.DataFrame,
    alvo: pd.Series,
) -> pd.DataFrame:
    """Matriz de confusão com rótulos legíveis."""
    return pd.DataFrame(
        confusion_matrix(alvo, modelo.predict(features)),
        index=["real_baixo", "real_alto"],
        columns=["previsto_baixo", "previsto_alto"],
    )


def importancias(modelo: Pipeline, top: int = 8) -> pd.DataFrame:
    """Coeficientes da regressão logística, do maior impacto absoluto para o menor."""
    if top <= 0:
        raise ValueError("top deve ser positivo")
    if not isinstance(modelo, Pipeline):
        raise TypeError("modelo precisa ser um Pipeline treinado por treinar_baseline")

    preparo = modelo.named_steps["preparo"]
    classificador = modelo.named_steps["modelo"]
    nomes = [nome.split("__", 1)[-1] for nome in preparo.get_feature_names_out()]
    coeficientes = classificador.coef_[0]

    tabela = pd.DataFrame({"feature": nomes, "coeficiente": coeficientes})
    tabela["impacto"] = tabela["coeficiente"].abs()
    return (
        tabela.sort_values("impacto", ascending=False)
        .head(top)
        .reset_index(drop=True)
        .round({"coeficiente": 3, "impacto": 3})
    )


def _criar_preprocessador(
    categoricas: Sequence[str] = CATEGORICAS,
    numericas: Sequence[str] = NUMERICAS,
) -> ColumnTransformer:
    transformadores: list[tuple[str, object, list[str]]] = []
    if categoricas:
        transformadores.append(
            ("categoria", OneHotEncoder(handle_unknown="ignore"), list(categoricas))
        )
    if numericas:
        transformadores.append(("numero", StandardScaler(), list(numericas)))
    if not transformadores:
        raise ValueError("pré-processador precisa de pelo menos uma coluna")
    return ColumnTransformer(transformadores)
