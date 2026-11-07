# Checagem de fatos

Verificações feitas em **04/11/2026**. Tudo que está no repositório foi conferido contra documentação
oficial; o que não deu para confirmar está marcado como incerteza.

## Confirmado

| # | Afirmação usada no projeto | Fonte | Status |
|---|---|---|---|
| 1 | O V2 configura permissões com o array `permissions` (`action`/`resource`/`effect`), avaliado em ordem, **última regra que casa vence**, padrão `ask` | <https://opencode.ai/v2/docs/permissions/> | ✅ |
| 2 | Ações de permissão do V2: `read`, `edit`, `shell`, `webfetch`, `websearch`, `subagent`, `skill`, `question`, `glob`, `grep`, `external_directory` e `<server>_<tool>` para MCP | idem | ✅ |
| 3 | Servidores MCP ficam em `mcp.servers` (V2 não aceita nome direto em `mcp`); remoto = `type: "remote"` + `url`; OAuth é o padrão e `/mcps` faz o login | <https://opencode.ai/v2/docs/mcp-servers/> | ✅ |
| 4 | No V2, o arquivo de instruções do projeto é `AGENTS.md` (não há fallback para `CLAUDE.md`) | <https://opencode.ai/v2/docs/instructions/> | ✅ |
| 5 | `opencode run` suporta `--model`, `--file`, `--auto`, `--format json`, `--continue`, `--session`, `--agent`; `--standalone` é flag **global**. A doc cita `--archived`, mas o CLI **2.2.5 instalado não aceita** (devolve o help) | <https://opencode.ai/v2/docs/cli/commands/> + saída de `opencode run --help` no CI | ⚠️ divergente — usar sem `--archived` |
| 6 | O exemplo oficial de CI instala `@opencode/cli` e roda `opencode run --standalone` com a API key em variável de ambiente | idem | ✅ |
| 7 | `@opencode/cli` publica o binário `opencode.exe`; o CI fixa **2.2.5** (latest em 06/11/2026: **2.2.6**) | <https://registry.npmjs.org/@opencode/cli> | ✅ |
| 8 | O endpoint remoto do GitHub MCP é `https://api.githubcopilot.com/mcp/` | <https://github.com/github/github-mcp-server> | ✅ |
| 9 | Últimas versões das actions usadas: `actions/checkout` **v7.0.1** (tag móvel `v7` existe), `actions/setup-node` **v7.1.0** (`v7` existe), `astral-sh/setup-uv` **v10.3.3** — **não existe tag móvel `v10`**, pinar a versão exata | API de releases e de refs do GitHub | ✅ |
| 10 | Na página de download, o CLI é distribuído por `curl`, npm, bun e brew; o app desktop tem builds Windows x64/ARM64 — não há instalador `.msi` do CLI | <https://opencode.ai/download> | ✅ |
| 11 | Modelos free-tier do Console só funcionam dentro do OpenCode; outros harnesses recebem HTTP 403 | <https://opencode.ai/v2/docs/console/harnesses/> | ✅ |
| 12 | Trilha DIO: 50 horas, 3 meses, projetos de detecção de anomalias, DataPilot e assistente virtual | <https://app.santanderopenacademy.com/pt-BR/program/dados-com-python-e-ia> | ✅ |
| 13 | Datas divulgadas: início 03/11/2026, término 31/12/2026 | idem | ✅ |

## Divergente

| # | Ponto | O que foi encontrado | Como o projeto trata |
|---|---|---|---|
| 14 | Data de início do bootcamp | A página da Santander Open Academy cita **03/11/2026–31/12/2026**; um trecho de outra chamada cita **20/10/2026–20/12/2026** | `docs/DIO-ROADMAP.md` usa 03/11–31/12 e manda confirmar no edital |
| 15 | Nome/estrutura dos módulos | A DIO não expõe a lista final de módulos em HTML estático (SPA); o conteúdo só aparece logado | Roadmap usa os pilares divulgados publicamente, não nomes oficiais de módulo |

## Providers (analisados em 04/11/2026)

| # | Afirmação | Fonte | Status |
|---|---|---|---|
| 21 | **GitHub Models foi desativado em 30/07/2026** (playground, catálogo e API) | <https://docs.github.com/en/github-models/use-github-models/prototyping-with-ai-models> | ✅ (por isso não é opção) |
| 22 | Groq free: `openai/gpt-oss-120b` tem 30 RPM · 1.000 RPD · 8K TPM · 200K TPD | <https://console.groq.com/docs/rate-limits> | ✅ |
| 23 | Groq documenta o OpenCode como cliente e recomenda `openai/gpt-oss-120b` | <https://console.groq.com/docs/coding-with-groq/opencode> | ✅ |
| 24 | Modelos `*-free` do OpenCode Console exigem o cliente OpenCode; outros harnesses recebem 403 | <https://opencode.ai/v2/docs/console/models/> | ✅ |
| 25 | Limites de requisição do free tier do Console **não estão documentados** na página de modelos | idem (busca por “rate limit” sem resultado) | ⚠️ não documentado |
| 26 | OpenRouter free: 20 RPM; 50 req/dia com menos de US$10 em créditos e 1.000/dia acima disso | <https://openrouter.ai/docs/api-reference/limits> | ⚠️ tabela não renderizou no fetch; valores usuais — confirme na página |
| 27 | Provider `google` do catálogo aceita `GEMINI_API_KEY` e o modelo `google/gemini-2.5-flash` existe (1M de contexto) | <https://models.dev/api.json> (`providers.google`) | ✅ |
| 28 | Provider `groq` aceita `GROQ_API_KEY` e expõe `openai/gpt-oss-120b` | idem (`providers.groq`) | ✅ |
| 29 | Um diff de 24 KB + system prompt/ferramentas = **13.473 tokens**, acima do TPM de 8.000 da Groq free | log real do PR #3 (07/11/2026) | ✅ medido |
| 30 | `models/gemini-2.5-flash` **não está mais disponível para contas novas**; o provider recomenda `gemini-3.8-flash` | erro real da API no log do PR #3 | ✅ |
| 31 | `google/gemini-3.8-flash` existe no catálogo: 1M de contexto, 65k de saída, tool calling | <https://models.dev/api.json> (`providers.google`) | ✅ |
| 32 | Gemini 3.8 Flash respondeu "This model is currently experiencing high demand" após ~6 min de retentativas (07/11/2026) | log do run 42333945697 | ✅ transiente |
| 33 | O fallback pediu **73.567 tokens** com diff de 6 KB — contexto herdado da tentativa anterior; corrigido isolando `XDG_*` por tentativa | idem | ✅ |

## Não verificado / decisão consciente

| # | Ponto | Situação |
|---|---|---|
| 16 | GitHub Action oficial `anomalyco/opencode/github@latest` | Ela existe no tag `latest`, instala o CLI via `curl https://opencode.ai/install` e executa **`opencode github run`**. Esse subcomando **não aparece** na lista de comandos do CLI V2 e não há página `/v2/docs/github` (404 em 04/11/2026). Por isso o review daqui **não usa a Action**: usa `opencode run`, que é documentado no V2. Se quiser testar a Action, valide em uma branch antes. |
| 17 | `opencode github install` | Documentado apenas na doc V1 (`/docs/github`), ausente da lista V2. Não é necessário para este setup. |
| 18 | Free tier do Console dentro do CI | A doc diz que modelos free exigem o cliente OpenCode; `opencode run` é o cliente, então **deve** funcionar, mas os limites não são públicos. Teste com `opencode run --model opencode/deepseek-v4.1-flash-free "ok"` antes de trocar. |
| 19 | `uv` como package-ecosystem do Dependabot | Suportado pelo Dependabot, mas pode variar por plano/conta. Se o bot não abrir PRs, troque para `pip` com `directory: "/"`. |
| 20 | Custo real por revisão | Depende do modelo e do tamanho do diff. Um PR grande pode consumir muitos tokens; o timeout do job é 20 min. |

## Como reverificar

```powershell
# versão real do CLI instalada
opencode --version

# config aceita?
opencode mcp list

# documentação V2 (fonte de verdade)
# https://opencode.ai/v2/docs/

# action oficial (se for testar)
# https://github.com/anomalyco/opencode/tree/latest/github

# versões das actions
gh api repos/actions/checkout/releases/latest --jq .tag_name
gh api repos/astral-sh/setup-uv/releases/latest --jq .tag_name
```

## Regra adotada neste repositório

Quando a documentação V2 e a V1 divergem, **V2 vence**. Quando só existe V1, o item é marcado como
não verificado e não vira dependência do fluxo principal.
