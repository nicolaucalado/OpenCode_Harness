# Prompt para o GitHub Copilot

Use no **Copilot Chat em modo agente** (VS Code) ou no **Copilot coding agent** (github.com).
Ele foi escrito para terminar a publicação do repositório e validar o fluxo de revisão.

## Onde cada coisa roda

| O quê | Onde | Por quê |
|---|---|---|
| Comandos `git`, `gh`, `uv`, `npm` | **terminal** (PowerShell) | precisam de acesso ao disco e à rede |
| Criar/ver a chave da Groq | **console.groq.com/keys** | a chave nasce lá; **nunca** cole a chave no chat |
| Cadastrar a chave como secret | **Settings → Secrets and variables → Actions** (web) | `gh secret set` é interativo e o Copilot não digita no prompt |
| Revisão automática de PR | **GitHub Actions** | é o workflow que roda o OpenCode |
| Colar este prompt | **Copilot Chat (agente)** ou **coding agent** | ele executa os comandos por você |

> O console da Groq **não** recebe código, prompt nem comandos. Ele só serve para gerar a API key.

Antes de colar, troque:

- `<CAMINHO>` → `C:\Users\nicol\OneDrive\Documents\Projeto Padrão\OpenCode_Harness`
- `<MODELO>` → `google/gemini-3.8-flash` (default) ou outro de [`PROVIDERS.md`](./PROVIDERS.md)
- `<FALLBACK>` → `google/gemini-3-flash-preview` (default)
- `<FALLBACK2>` → `google/gemini-3.1-flash-lite-preview` (default)
- `<SECRET>` → `GEMINI_API_KEY` (a cadeia default usa só Gemini)

---

```text
Contexto: tenho um repositório local em <CAMINHO> chamado OpenCode_Harness. Ele já contém
- opencode.jsonc (permissões restritas + MCP remoto do GitHub)
- .github/workflows/opencode-review.yml (revisão automática de PR via `opencode run`, com fallback de modelo)
- .github/workflows/opencode-task.yml (agente sob demanda, cria branch e PR)
- .github/workflows/ci.yml (ruff + pytest)
- pyproject.toml, uv.lock, src/, tests/, notebooks/, docs/

Objetivo: publicar em https://github.com/nicolaucalado/OpenCode_Harness e deixar a revisão
automática de PR funcionando de ponta a ponta.

Execute, em ordem, pedindo minha confirmação apenas nos passos marcados [CONFIRMAR].
Quando um passo exigir interação humana (login no navegador ou digitar um secret), PARE
e me peça para fazer — não tente contornar.

1. Verifique `git --version`, `python --version`, `uv --version`. Se `gh` não existir, instale com
   `winget install --id GitHub.cli -e` e peça para eu reabrir o terminal. Rode `gh auth status`
   e, se não estiver autenticado, pare e me peça para rodar `gh auth login`.
2. Rode `uv sync`, `uv run ruff check .` e `uv run pytest -q`. Corrija somente o que estiver quebrado,
   sem mudar o escopo do projeto.
3. [CONFIRMAR] Crie o repositório remoto: `gh repo create nicolaucalado/OpenCode_Harness --public
   --source . --remote origin --push`. Se eu preferir privado, use `--private`.
4. Configure as variables de modelo:
   `gh variable set OPENCODE_MODEL --body "<MODELO>"`
   `gh variable set OPENCODE_MODEL_FALLBACK --body "<FALLBACK>"`
   `gh variable set OPENCODE_MODEL_FALLBACK2 --body "<FALLBACK2>"`
   Para o secret (<SECRET>), NÃO rode `gh secret set` sem valor: ele abre um
   prompt interativo. Me avise para cadastrar em Settings → Secrets and variables → Actions,
   ou me peça para rodar no terminal com o valor vindo de uma variável de ambiente.
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
- Nunca peça para eu colar a API key no chat.
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
- Passos interativos (`gh auth login`, `gh secret set` sem `--body`, editor de commit) travam ou falham
  no agente: faça você mesmo ou use a interface web.
- O coding agent do github.com trabalha em uma branch remota e abre PR — os secrets do repositório já
  valem lá, mas ele **não** substitui a instalação local do CLI nem o login do MCP, e não tem acesso
  aos seus arquivos locais antes do primeiro push.
- Este prompt não instala nada sem passar pelo `winget`/`npm`; revise os comandos antes de aprovar.
