# MCP do GitHub

O [GitHub MCP Server](https://github.com/github/github-mcp-server) expõe repositórios, issues, PRs, Actions e
buscas de código como ferramentas MCP. É o que dá ao OpenCode acesso estruturado ao GitHub — sem `gh` e sem
colar token no prompt.

## Configuração usada aqui

Já está no `opencode.jsonc`:

```jsonc
"mcp": {
  "servers": {
    "github": {
      "type": "remote",
      "url": "https://api.githubcopilot.com/mcp/",
    },
  },
},
```

É o endpoint remoto oficial. A autenticação é **OAuth**: o OpenCode abre o fluxo e guarda o token fora da
configuração do projeto.

```powershell
opencode mcp list           # dentro de OpenCode_Harness
```

`needs authentication` → abra o OpenCode, rode `/mcps`, escolha `github` e conclua no navegador.
`✓ github connected` → pronto.

## Alternativa: token pessoal (PAT)

Use quando não quiser OAuth (CI, máquina compartilhada, conta de serviço).

1. Crie um **fine-grained PAT** em <https://github.com/settings/tokens?type=beta>.
2. Escopos mínimos: *Public repositories* (ou o repo específico) + `Contents: Read`, `Issues: Read`,
   `Pull requests: Read`. Só adicione escrita se o agente for abrir PRs/comentários.
3. Troque a entrada do `opencode.jsonc`:

```jsonc
"github": {
  "type": "remote",
  "url": "https://api.githubcopilot.com/mcp/",
  "headers": { "Authorization": "Bearer {env:GITHUB_PERSONAL_ACCESS_TOKEN}" },
}
```

`{env:...}` evita segredo no arquivo. Exporte a variável só na sessão:

```powershell
$env:GITHUB_PERSONAL_ACCESS_TOKEN = "github_pat_..."
```

> Prefira OAuth no dia a dia: token em variável de ambiente vaza em print de tela, log e histórico do shell.

## Alternativa: servidor local via Docker

Útil quando você quer rodar o servidor na sua máquina (ou usar uma versão específica):

```powershell
opencode mcp add github-local -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server
```

Confirme a imagem e os argumentos no README oficial antes de usar; o servidor remoto é o caminho recomendado
e não exige Docker.

## O que pedir ao agente

Com o MCP conectado, o agente consegue (respeitando as permissões `ask` padrão):

- “Liste meus PRs abertos e diga quais estão sem revisão.”
- “Leia a issue #12 e proponha um plano de implementação.”
- “Comente no PR #7 com o resultado do `pytest`.”
- “Compare a branch atual com a `main` e resuma o que mudou.”
- “Crie uma issue para o TODO que você encontrou em `src/`.”

Toda chamada de ferramenta MCP cai em `ask` (não há regra liberando `github_*` no `opencode.jsonc`).
Aprove caso a caso — é a barreira que impede escrita acidental no repositório.

## Segurança

- Comece com PAT **somente leitura**; conceda escrita apenas se precisar.
- `github_*` não passa pelo `git push` bloqueado: o bloqueio do `opencode.jsonc` vale para o shell, não para MCP.
  Por isso a permissão padrão de MCP é `ask`.
- Em repositório de portfólio, cuidado com o que o agente publica em issues/comentários (conteúdo gerado é público).
- Revogue tokens antigos em <https://github.com/settings/tokens>.

## Verificação

```powershell
opencode mcp list
opencode api get /api/info   # se quiser confirmar que o servidor local está saudável
```

Referências:

- Endpoint remoto e headers: <https://github.com/github/github-mcp-server>
- Configuração MCP no OpenCode V2: <https://opencode.ai/v2/docs/mcp-servers/>
