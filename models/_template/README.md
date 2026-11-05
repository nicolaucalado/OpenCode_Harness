# <nome-do-modelo>

> **Licença deste artefato:** Apache 2.0 (ver [`LICENSE-MODELS`](../../LICENSE-MODELS)).
> **Licença do modelo base:** <ex.: Apache-2.0 / MIT / Llama Community License — verificar no card original>.
> **Versão:** `0.1.0` · **Data:** AAAA-MM-DD · **Autor:** Nicolau Calado

## Resumo

Uma frase sobre o que o modelo faz e para quem. Ex.: "Classificador binário de churn para uma base
sintética de telecom, treinado como atividade do módulo de Machine Learning da trilha DIO."

## Problema

- **Tipo de tarefa:** classificação / regressão / clustering / NLP / LLM
- **Variável alvo:** `<nome>`
- **Métrica principal:** `<f1 / rmse / silhouette / ...>`
- **Baseline usado:** `<regressão logística / média / heurística>`
- **Critério de sucesso:** `<ex.: f1 >= 0.75 no conjunto de teste>`

## Dados

| Item | Valor |
|---|---|
| Dataset | `<nome>` |
| Origem | `<URL ou "sintético">` |
| Licença dos dados | `<...>` |
| Linhas / colunas | `<n>` / `<n>` |
| Período | `<...>` |
| Dados pessoais? | `<não / sim — anonimizado com ...>` |

Registre também em [`docs/DADOS.md`](../../docs/DADOS.md).

## Treino

| Item | Valor |
|---|---|
| Algoritmo | `<...>` |
| Hiperparâmetros | `<...>` |
| Seed | `42` |
| Split | `<70/15/15 estratificado>` |
| Ambiente | `uv run python`, Python 3.12, scikit-learn `<versão>` |
| Tempo de treino | `<...>` |

Script reproduzível: `<scripts/train_<nome>.py ou notebooks/...>`

```powershell
uv sync
uv run python scripts/train_<nome>.py
```

## Métricas

| Conjunto | Métrica | Valor |
|---|---|---|
| Validação | `<...>` | `<...>` |
| Teste | `<...>` | `<...>` |

Matriz de confusão / curvas: `<caminho da imagem ou link>`

## Limitações e riscos

- O que o modelo **não** faz.
- Vieses conhecidos na base.
- Cenários em que não deve ser usado (produção, decisão de crédito, saúde…).
- Deriva esperada: `<...>`

## Uso

```python
import joblib

modelo = joblib.load("models/<nome>/model.joblib")
predicao = modelo.predict(X)
```

## Arquivos

```
models/<nome>/
├── README.md          # este card
├── model.joblib       # ou .onnx / .safetensors (via Git LFS ou release)
├── metrics.json
└── confusion_matrix.png
```

## Citação

```text
<nome-do-modelo> (2026) — Nicolau Calado.
Licença: Apache-2.0. https://github.com/nicolaucalado/OpenCode_Harness
```
