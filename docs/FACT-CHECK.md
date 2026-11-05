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
| 5 | `opencode run` suporta `--model`, `--file`, `--standalone`, `--archived`, `--auto`, `--format json`, `--continue`, `--session`, `--agent` | <https://opencode.ai/v2/docs/cli/commands/> | ✅ |
| 6 | O exemplo oficial de CI instala `@opencode/cli` e roda `opencode run --standalone` com a API key em variável de ambiente | idem | ✅ |
| 7 | `@opencode/cli` está na versão **2.2.5** e publica o binário `opencode.exe` (funciona no Windows) | <https://registry.npmjs.org/@opencode/cli/latest> | ✅ |
| 8 | O endpoint remoto do GitHub MCP é `https://api.githubcopilot.com/mcp/` | <https://github.com/github/github-mcp-server> | ✅ |
| 9 | Últimas versões das actions usadas: `actions/checkout` **v7.0.1**, `actions/setup-node` **v7.1.0**, `astral-sh/setup-uv` **v10.3.3**, `actions/setup-python` v7.1.0 | API de releases do GitHub | ✅ |
| 10 | Na página de download, o CLI é distribuído por `curl`, npm, bun e brew; o app desktop tem builds Windows x64/ARM64 — não há instalador `.msi` do CLI | <https://opencode.ai/download> | ✅ |
| 11 | Modelos free-tier do Console só funcionam dentro do OpenCode; outros harnesses recebem HTTP 403 | <https://opencode.ai/v2/docs/console/harnesses/> | ✅ |
| 12 | Trilha DIO: 50 horas, 3 meses, projetos de detecção de anomalias, DataPilot e assistente virtual | <https://app.santanderopenacademy.com/pt-BR/program/dados-com-python-e-ia> | ✅ |
| 13 | Datas divulgadas: início 03/11/2026, término 31/12/2026 | idem | ✅ |

## Divergente

| # | Ponto | O que foi encontrado | Como o projeto trata |
|---|---|---|---|
| 14 | Data de início do bootcamp | A página da Santander Open Academy cita **03/11/2026–31/12/2026**; um trecho de outra chamada cita **20/10/2026–20/12/2026** | `docs/DIO-ROADMAP.md` usa 03/11–31/12 e manda confirmar no edital |
| 15 | Nome/estrutura dos módulos | A DIO não expõe a lista final de módulos em HTML estático (SPA); o conteúdo só aparece logado | Roadmap usa os pilares divulgados publicamente, não nomes oficiais de módulo |

## Não verificado / decisão consciente

| # | Ponto | Situação |
|---|---|---|
| 16 | GitHub Action oficial `anomalyco/opencode/github@latest` | Ela existe no tag `latest`, instala o CLI via `curl https://opencode.ai/install` e executa **`opencode github run`**. Esse subcomando **não aparece** na lista de comandos do CLI V2 e não há página `/v2/docs/github` (404 em 04/11/2026). Por isso o review daqui **não usa a Action**: usa `opencode run`, que é documentado no V2. Se quiser testar a Action, valide em uma branch antes. |
| 17 | `opencode github install` | Documentado apenas na doc V1 (`/docs/github`), ausente da lista V2. Não é necessário para este setup. |
| 18 | Nome exato da variável de ambiente por provider | `ANTHROPIC_API_KEY` é o caso documentado no exemplo de CI do V2. Para `openai/...` e `opencode/...` o workflow passa `OPENAI_API_KEY` e `OPENCODE_API_KEY`, mas **confirme no seu provider** antes de confiar no job. |
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
