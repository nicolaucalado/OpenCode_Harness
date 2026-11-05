# Setup — do zero ao primeiro PR revisado

Tempo estimado: 25–40 min. Comandos em PowerShell (Windows).

---

## 0. O que já vem pronto neste repositório

| Arquivo | Para que serve |
|---|---|
| `opencode.jsonc` | modelo padrão, MCP do GitHub e permissões restritas |
| `AGENTS.md` | regras do projeto que o agente lê automaticamente |
| `.github/workflows/opencode-review.yml` | revisão automática de PR |
| `.github/workflows/opencode-task.yml` | agente sob demanda (cria branch + PR) |
| `.github/workflows/ci.yml` | ruff + pytest em todo push/PR |
| `pyproject.toml` + `uv.lock` | dependências reproduzíveis (Python 3.12+) |

---

## 1. Pré-requisitos

Verifique o que já existe:

```powershell
git --version
python --version    # precisa ser 3.12+
uv --version
node --version      # necessário para o CLI do OpenCode
opencode --version
gh --version        # opcional, mas facilita muito
```

No seu ambiente atual, **git, Python e uv já estão instalados**; `node`, `opencode` e `gh` não. Instale:

```powershell
winget install --id OpenJS.NodeJS.LTS -e
winget install --id GitHub.cli -e
```

Feche e reabra o terminal (PATH só atualiza em sessões novas).

```powershell
npm install --global @opencode/cli
opencode --version   # esperado: 2.x
```

> Sem Node? O app desktop (https://opencode.ai/download) serve para o uso interativo, mas os comandos
> `opencode run`, `opencode mcp` e `opencode auth` usados aqui e no CI vêm do CLI.

---

## 2. Dependências Python

Dentro de `OpenCode_Harness`:

```powershell
uv sync
uv run pytest -q
uv run ruff check .
```

Crie o kernel dos notebooks:

```powershell
uv run python -m ipykernel install --user --name opencode-harness --display-name "Python 3 (opencode-harness)"
```

---

## 3. Autenticar o OpenCode no provider

O default do projeto é **Groq (free)**, com o modelo `groq/openai/gpt-oss-120b` (1.000 req/dia).
Crie a key em <https://console.groq.com/keys> e conecte:

```powershell
opencode auth login   # escolha Groq
```

Ou, dentro do OpenCode, `/connect` → Groq → cole a key.

Confira:

```powershell
opencode models
opencode run --model groq/openai/gpt-oss-120b "responda apenas: ok"
```

Alternativas (OpenRouter, Gemini, Zen free, Go) e seus limites: [`PROVIDERS.md`](./PROVIDERS.md).

---

## 4. MCP do GitHub (OAuth)

O servidor já está declarado no `opencode.jsonc`:

```jsonc
"mcp": {
  "servers": {
    "github": { "type": "remote", "url": "https://api.githubcopilot.com/mcp/" }
  }
}
```

Confirme a conexão **de dentro desta pasta** (a config é local do projeto):

```powershell
opencode mcp list
```

Se aparecer `needs authentication`, abra o OpenCode e rode `/mcps` → selecione `github` → conclua o login no navegador. Detalhes em [`GITHUB-MCP.md`](./GITHUB-MCP.md).

---

## 5. Publicar no GitHub

O repositório git local já foi inicializado com o commit inicial. Falta o remoto.

### Opção A — com `gh` (recomendado)

```powershell
gh auth login
gh repo create nicolaucalado/OpenCode_Harness --public --source . --remote origin --push
```

### Opção B — pela interface web

1. Crie `https://github.com/new` com o nome **OpenCode_Harness**, **sem** README/gitignore/license.
2. Depois:

```powershell
git remote add origin https://github.com/nicolaucalado/OpenCode_Harness.git
git branch -M main
git push -u origin main
```

> Repositório público é o padrão para portfólio. Se preferir privado, troque `--public` por `--private`
> (a revisão automática funciona igual; PRs de fork é que não rodam, por segurança).

---

## 6. Secrets e variable do GitHub Actions

A revisão usa o modelo definido na **variable** `OPENCODE_MODEL` e a chave no **secret** do provider.

Com `gh` (ele pergunta o valor sem deixar rastro no histórico):

```powershell
gh variable set OPENCODE_MODEL --body "groq/openai/gpt-oss-120b"
gh secret set GROQ_API_KEY
```

Pela web: **Settings → Secrets and variables → Actions**.

| Secret | Quando usar |
|---|---|
| `GROQ_API_KEY` | **default** — modelo `groq/...` (free: 1.000 req/dia) |
| `OPENCODE_API_KEY` | modelo `opencode/...` (Zen free ou Console pago) |
| `OPENROUTER_API_KEY` | modelo `openrouter/...:free` |
| `ANTHROPIC_API_KEY` | modelo `anthropic/...` (pago por token) |
| `OPENAI_API_KEY` | modelo `openai/...` (pago por token) |

Análise de custo/limite de cada opção: [`PROVIDERS.md`](./PROVIDERS.md).

Se você usar o Console em equipe/CI, prefira uma **service account key** (`oc_sk_...`) em vez de chave pessoal.

> Sem secret, o workflow não falha em silêncio: ele avisa no log e publica um comentário dizendo que a revisão não rodou.

---

## 7. Testar o fluxo completo

```powershell
git switch -c dio/teste-harness
# edite algo em docs/ ou notebooks/
git add -A
git commit -m "docs: testa a revisão automática"
git push -u origin dio/teste-harness
gh pr create --fill
```

O que deve acontecer:

1. `CI` roda ruff + pytest.
2. `opencode · revisão de PR` publica **um** comentário; a cada novo push ele é **atualizado**, não duplicado.
3. O job de review é pulado em PRs de fork e em drafts (por design).

Para pedir uma implementação ao agente: **Actions → opencode · tarefa → Run workflow**, descreva a tarefa e informe a branch. Ele abre um PR.

---

## 8. Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `opencode: command not found` | Node/npm não instalado ou PATH antigo | reabra o terminal; `npm i -g @opencode/cli` |
| review não comenta | secret ausente ou modelo sem acesso | veja o log do step “Revisar com OpenCode” |
| review em PR de fork não roda | secrets não são expostos a forks | esperado; faça review manual |
| `opencode mcp list` sem `github` | rodou fora da pasta do projeto | execute dentro de `OpenCode_Harness` |
| MCP `needs authentication` | OAuth pendente | `/mcps` → github → sign in |
| review falha com `429` | cota do provider estourada | espere o reset ou troque `OPENCODE_MODEL` (ver `PROVIDERS.md`) |
| CI falha em `uv sync --frozen` | `uv.lock` desatualizado | `uv lock` e commite |
| `git push` negado dentro do agente | permissão `deny` proposital | faça o push você mesmo |

---

## 9. Próximos passos

- [`DIO-ROADMAP.md`](./DIO-ROADMAP.md): mapa da trilha e como usar o harness em cada módulo.
- [`GITHUB-MCP.md`](./GITHUB-MCP.md): o que dá para fazer com o MCP do GitHub.
- [`PROVIDERS.md`](./PROVIDERS.md): comparação de custo/limite e como trocar de modelo.
- [`FACT-CHECK.md`](./FACT-CHECK.md): fontes e incertezas do que está configurado aqui.
