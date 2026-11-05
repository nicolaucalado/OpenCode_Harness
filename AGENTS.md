# OpenCode_Harness — instruções do projeto

Este repositório é um **harness de desenvolvimento** com OpenCode, usado para:

1. estudar e entregar as atividades do bootcamp **Santander — Dados com Python e IA (DIO)**;
2. servir de modelo profissional de repositório Python com revisão automática de PR.

Responda sempre em **português do Brasil** no chat. Código, nomes de arquivos e commits em inglês quando fizer sentido técnico.

## Comandos

```bash
uv sync                      # instala dependências (inclui grupo dev)
uv run pytest -q             # testes
uv run ruff check .          # lint
uv run ruff format .         # formatação
uv run python -m ipykernel install --user --name opencode-harness  # kernel dos notebooks
```

Nunca use `pip install` direto: o projeto usa **uv** e `uv.lock`.

## Estrutura

```
src/opencode_harness/   código reutilizável (testável, sem dependência de notebook)
tests/                  testes unitários (pytest)
notebooks/              exploração e entregas da DIO (não é biblioteca)
data/raw/               dados originais — fora do git
data/processed/         dados derivados — fora do git
docs/                   documentação do harness e do bootcamp
.github/workflows/      CI e revisão automática (mudanças exigem revisão humana)
```

## Convenções

- **Python 3.12+**, tipagem moderna (`list[str]`, `X | None`).
- Lógica que precisa de teste vive em `src/opencode_harness/`; notebook só orquestra.
- Funções públicas com docstring curta e type hints.
- Dados **nunca** entram no git: `data/raw/` e `data/processed/` são ignorados.
- Notebooks: executar em ordem, saídas enxutas, sem prints gigantes de DataFrame inteiro.
- Experimento de ML: fixar `random_state` e registrar no notebook qual seed foi usada.

## Regras de segurança

- Não leia nem escreva `.env`, chaves, tokens ou credenciais. Use `.env.example` para documentar variáveis.
- Não altere `.github/`, `opencode.jsonc` nem `pyproject.toml` sem pedir autorização explícita.
- Não rode `git push`, `git reset --hard`, `git clean` ou `gh pr merge`.
- Antes de concluir uma tarefa, rode `uv run pytest -q` e `uv run ruff check .`.

## Contexto do bootcamp

- Trilha: <https://web.dio.me/track/santander-dados-com-python-e-ia>
- Período divulgado: 03/11/2026 a 31/12/2026, 50 horas.
- Pilares: Python, estrutura de dados, SQL/bancos, análise de dados, Machine Learning e IA generativa/agentes.
- Projetos citados publicamente: detecção de anomalias em transações, DataPilot e assistente virtual com IA.
- Ao criar uma atividade, use branch `dio/<modulo>-<tema>` e abra PR (o PR dispara a revisão automática).
