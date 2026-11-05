# Prompt para o GitHub Copilot

Use no **Copilot Chat em modo agente** (VS Code) ou no **Copilot coding agent** (github.com).
Ele foi escrito para terminar a publicação do repositório e validar o fluxo de revisão.

Antes de colar, troque:

- `<CAMINHO>` → `C:\Users\nicol\OneDrive\Documents\Projeto Padrão\OpenCode_Harness`
- `<MODELO>` → ex.: `anthropic/claude-sonnet-5-5`
- `<SECRET>` → `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` ou `OPENCODE_API_KEY`

---

```text
Contexto: tenho um repositório local em <CAMINHO> chamado OpenCode_Harness. Ele já contém
- opencode.jsonc (permissões restritas + MCP remoto do GitHub)
- .github/workflows/opencode-review.yml (revisão automática de PR via `opencode run`)
- .github/workflows/opencode-task.yml (agente sob demanda, cria branch e PR)
- .github/workflows/ci.yml (ruff + pytest)
- pyproject.toml, uv.lock, src/, tests/, notebooks/, docs/

Objetivo: publicar em https://github.com/nicolaucalado/OpenCode_Harness e deixar a revisão
automática de PR funcionando de ponta a ponta.

Execute, em ordem, pedindo minha confirmação apenas nos passos marcados [CONFIRMAR]:

1. Verifique `git --version`, `python --version`, `uv --version`. Se `gh` não existir, instale com
   `winget install --id GitHub.cli -e` e peça para eu reabrir o terminal. Rode `gh auth status`.
2. Rode `uv sync`, `uv run ruff check .` e `uv run pytest -q`. Corrija somente o que estiver quebrado,
   sem mudar o escopo do projeto.
3. [CONFIRMAR] Crie o repositório remoto: `gh repo create nicolaucalado/OpenCode_Harness --public
   --source . --remote origin --push`. Se eu preferir privado, use `--private`.
4. Configure a variable e o secret do Actions, sem nunca imprimir o valor do secret:
   `gh variable set OPENCODE_MODEL --body "<MODELO>"`
   `gh secret set <SECRET>` (o valor eu digito no prompt interativo).
5. Crie a branch `dio/teste-harness`, marque uma linha da tabela de checklist em
   docs/DIO-ROADMAP.md como concluída, faça commit com mensagem convencional, push e abra PR com
   `gh pr create --fill`.
6. Acompanhe com `gh run list --limit 5` e `gh run watch`. Quando o workflow
   "opencode · revisão de PR" terminar, leia o comentário publicado no PR com
   `gh pr view --comments` e me mostre o conteúdo.
7. Se o job falhar, mostre o trecho relevante do log (`gh run view <id> --log-failed`), diga a causa
   provável e proponha a correção. Não edite .github/workflows/ nem opencode.jsonc sem eu autorizar.
8. No fim, entregue um relatório curto: URL do repositório, URL do PR, status dos workflows,
   e o que ainda falta configurar (por exemplo, autenticar o MCP do GitHub com /mcps).

Regras de segurança:
- Nunca comite .env, credenciais ou dados brutos.
- Nunca ecoe tokens, secrets ou o conteúdo de variáveis de ambiente com segredo.
- Não faça merge, não force push e não altere permissões do repositório.
- Se algo divergir da documentação oficial do OpenCode V2 (https://opencode.ai/v2/docs/),
  pare e me avise em vez de improvisar.
```

---

## Variação curta (uso diário)

Para pedir uma atividade do bootcamp ao Copilot já dentro do repositório:

```text
Leia AGENTS.md e docs/DIO-ROADMAP.md. Implemente a atividade "<NOME>" seguindo o fluxo:
branch dio/<modulo>-<tema>, notebook em notebooks/, lógica testável em src/opencode_harness/,
teste em tests/, e PR com o template. Rode uv run ruff format ., uv run ruff check . e
uv run pytest -q antes de abrir o PR. Não altere .github/ nem opencode.jsonc.
```

## Limites

- O Copilot no VS Code precisa de acesso ao terminal para rodar os comandos; no modo "ask" ele só sugere.
- O coding agent do github.com trabalha em uma branch remota e abre PR — os secrets do repositório já valem lá,
  mas ele **não** substitui a instalação local do CLI nem o login do MCP.
- Este prompt não instala nada sem passar pelo `winget`/`npm`; revise os comandos antes de aprovar.
