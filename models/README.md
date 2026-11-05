# Licenciamento

Este repositório usa **duas licenças**, com escopo bem separado:

| Escopo | Licença | Arquivo |
|---|---|---|
| Código-fonte, notebooks, scripts, workflows, documentação | **MIT** | [`LICENSE`](../LICENSE) |
| Pesos de modelos treinados, artefatos de modelo (`.joblib`, `.pkl`, `.onnx`, `.pt`, `.safetensors`) e datasets derivados publicados em `models/` | **Apache 2.0** | [`LICENSE-MODELS`](../LICENSE-MODELS) |

## Por que separar

- **MIT** no código facilita reutilização e leitura por recrutadores e pela comunidade.
- **Apache 2.0** nos modelos agrega uma concessão explícita de patentes e deixa claro o que acontece ao
  redistribuir pesos — algo que a MIT não trata bem.
- Um arquivo sem cabeçalho em `models/` é considerado Apache 2.0 por padrão.

## O que **não** é licenciado por nós

- Dependências (`pandas`, `numpy`, `scikit-learn`, `ruff`…) mantêm suas próprias licenças.
- Datasets de terceiros mantêm a licença da origem — registre em [`docs/DADOS.md`](../docs/DADOS.md).
- Modelos pré-treinados baixados de terceiros (ex.: Hugging Face) mantêm a licença do publicador, mesmo que
  o fine-tuning seja nosso. Nesse caso, registre a licença original no card do modelo.
- O código do OpenCode e do GitHub MCP não fazem parte deste repositório.

## Boas práticas ao publicar um modelo

0. Copie `models/_template/` para `models/<nome-do-modelo>/` e preencha o card.
1. Crie `models/<nome-do-modelo>/` com `README.md` contendo: dataset usado, hiperparâmetros, métricas e a
   licença do modelo base.
2. Não versione arquivos grandes no git comum — use **Git LFS** ou publique como *release* e referencie a URL.
3. Inclua o aviso de que o artefato é fornecido "AS IS", sem garantia de adequação a produção.
4. Se o modelo for treinado com dados pessoais, documente a base legal e a anonimização antes de publicar.

## Como citar

```text
OpenCode_Harness — Nicolau Calado (2026)
Código: MIT · Modelos: Apache-2.0
https://github.com/nicolaucalado/OpenCode_Harness
```
