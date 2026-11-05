# OpenCode_Harness

Harness de desenvolvimento com [OpenCode](https://opencode.ai) para o bootcamp
**Santander — Dados com Python e IA (DIO)** e para uso profissional depois dele.

Não é só um repositório de estudos: é a estrutura que faz cada atividade passar por
branch → PR → CI → revisão automática → merge, com permissões restritas e um agente MCP
conectado ao GitHub.

[![CI](https://github.com/nicolaucalado/OpenCode_Harness/actions/workflows/ci.yml/badge.svg)](https://github.com/nicolaucalado/OpenCode_Harness/actions/workflows/ci.yml)
[![Revisão de PR](https://github.com/nicolaucalado/OpenCode_Harness/actions/workflows/opencode-review.yml/badge.svg)](https://github.com/nicolaucalado/OpenCode_Harness/actions/workflows/opencode-review.yml)

---

## O que tem aqui

| Camada | O que faz | Onde |
|---|---|---|
| **Local** | agente no seu clone, com permissões restritas e instruções do projeto | `opencode.jsonc`, `AGENTS.md` |
| **GitHub MCP** | issues, PRs, Actions e busca de código como ferramentas do agente | `opencode.jsonc` |
| **CI** | lint, formatação e testes em todo push/PR | `.github/workflows/ci.yml` |
| **Revisão automática** | comenta o PR com achados classificados por severidade | `.github/workflows/opencode-review.yml` |
| **Agente sob demanda** | você descreve a tarefa; ele edita, commita e abre PR | `.github/workflows/opencode-task.yml` |
| **Template Python** | `uv`, `src/`, notebooks, testes, ruff | `pyproject.toml`, `src/`, `tests/` |

## Estrutura

```text
OpenCode_Harness/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # ruff + pytest
│   │   ├── opencode-review.yml     # revisão automática de PR
│   │   └── opencode-task.yml       # agente sob demanda (cria PR)
│   ├── ISSUE_TEMPLATE/atividade-dio.yml
│   ├── pull_request_template.md
│   └── dependabot.yml
├── docs/
│   ├── SETUP.md                    # passo a passo completo
│   ├── GITHUB-MCP.md               # MCP do GitHub
│   ├── DIO-ROADMAP.md              # mapa da trilha + checklist
│   ├── FACT-CHECK.md               # fontes e incertezas
│   └── COPILOT-PROMPT.md           # prompt pronto para o Copilot
├── notebooks/                      # entregas da DIO
├── src/opencode_harness/           # código testável
├── tests/
├── models/                         # pesos/artefatos (Apache 2.0)
├── data/                           # dados (fora do git)
├── AGENTS.md                       # regras que o agente lê
├── LICENSE                         # MIT (código e docs)
├── LICENSE-MODELS                  # Apache 2.0 (modelos treinados)
├── opencode.jsonc                  # modelo, MCP e permissões
└── pyproject.toml
```

## Quickstart

```powershell
# 1. dependências
uv sync
uv run pytest -q

# 2. CLI do OpenCode (precisa de Node LTS)
npm install --global @opencode/cli

# 3. autenticar provider e MCP
opencode auth login
opencode mcp list        # se pedir auth: abra o OpenCode e rode /mcps

# 4. usar
opencode
```

Publicação no GitHub, secrets e teste do fluxo: **[docs/SETUP.md](docs/SETUP.md)**.

## Como o fluxo funciona

```text
issue ──► branch dio/<modulo>-<tema> ──► notebook + src/ + tests/
                                              │
                                              ▼
                                            PR  ──► CI (ruff + pytest)
                                              │
                                              ▼
                                 revisão automática (OpenCode)
                                              │
                                              ▼
                                            merge
```

- A revisão usa `opencode run --standalone` (caminho documentado no V2), com o modelo da variable
  `OPENCODE_MODEL` — default `groq/openai/gpt-oss-120b`, free com 1.000 req/dia — e a chave no secret
  `GROQ_API_KEY`.
- O diff é truncado em 24 KB para caber no limite de tokens/minuto do free tier; o comentário avisa quando
  a revisão é parcial.
- O comentário é **único**: cada push atualiza o mesmo comentário (marcador `<!-- opencode-review -->`).
- PRs de fork e drafts são pulados de propósito — fork não recebe secrets.

## Comandos

```powershell
uv sync                                # instala tudo (inclui dev)
uv run pytest -q                       # testes
uv run ruff check .                    # lint
uv run ruff format .                   # formatação
uv add <pacote>                        # nova dependência (atualiza uv.lock)
opencode                               # TUI
opencode run "resuma este repositório" # one-shot
opencode mcp list                      # status do MCP
```

## Segurança

O `opencode.jsonc` foi escrito para **falhar fechado**:

| Recurso | Regra |
|---|---|
| `.env`, `*.pem`, `*.key`, `id_rsa*` | leitura **negada** |
| `.github/`, `opencode.jsonc`, `pyproject.toml`, `.env` | edição **negada** |
| `git push`, `git reset --hard`, `git clean`, `git rebase` | shell **negado** |
| `rm -rf`, `sudo`, `curl`, `wget`, `env`, `printenv` | shell **negado** |
| `gh pr merge`, `gh secret` | shell **negado** |
| resto do shell | **pergunta** |
| ferramentas MCP (`github_*`) | **pergunta** |

No CI, o job roda com `--auto` (aprova o que não está negado) e token `contents: read`; o push de branch
no fluxo de tarefa é feito pelo **workflow**, não pelo agente.

## Limitações conhecidas

- Não há sandbox gerenciado: o isolamento é o runner efêmero do GitHub Actions ou a sua máquina.
- PR vindo de fork não recebe revisão automática (sem secrets).
- A GitHub Action oficial (`anomalyco/opencode/github`) não foi usada: ela executa `opencode github run`,
  comando ausente na lista do CLI V2. Detalhes em [docs/FACT-CHECK.md](docs/FACT-CHECK.md).
- Licença dupla: **MIT** para código/documentação e **Apache 2.0** para modelos treinados — veja abaixo.

## Bootcamp

- Trilha: <https://web.dio.me/track/santander-dados-com-python-e-ia>
- Mapa de atividades, cronograma de 8 semanas e checklist: [docs/DIO-ROADMAP.md](docs/DIO-ROADMAP.md)
- Cada atividade vira uma issue (template *Atividade DIO*) e um PR.

## Documentação

| Documento | Conteúdo |
|---|---|
| [SETUP.md](docs/SETUP.md) | instalação, secrets, publicação, troubleshooting |
| [GITHUB-MCP.md](docs/GITHUB-MCP.md) | MCP do GitHub, OAuth vs PAT, exemplos |
| [DIO-ROADMAP.md](docs/DIO-ROADMAP.md) | trilha, plano de 8 semanas, critérios de portfólio |
| [PROVIDERS.md](docs/PROVIDERS.md) | comparação de custo/limite e troca de modelo |
| [DADOS.md](docs/DADOS.md) | origem e licença dos datasets |
| [FACT-CHECK.md](docs/FACT-CHECK.md) | o que foi verificado, o que é incerteza |
| [COPILOT-PROMPT.md](docs/COPILOT-PROMPT.md) | prompt para terminar o setup com o Copilot |

## Licença

- **Código-fonte, notebooks, workflows e documentação:** [MIT](LICENSE).
- **Pesos/artefatos de modelos treinados (`models/`):** [Apache 2.0](LICENSE-MODELS).

Os detalhes de escopo e as obrigações ao publicar um modelo estão em [models/README.md](models/README.md).
