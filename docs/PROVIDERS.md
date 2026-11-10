# Análise de providers para o CI

Objetivo: revisar PRs automaticamente com **custo zero ou previsível**, boa disponibilidade e limites
documentados. Análise feita em **04/11/2026**.

## Resumo da decisão

**Default do CI: cadeia Gemini** — `google/gemini-3.8-flash` → `google/gemini-3-flash-preview` →
`google/gemini-3.1-flash-lite`.

Motivos (revisados em 09/11/2026):

1. O limite de **8.000 TPM** da Groq free não cabe no harness: mesmo um diff de 3 KB passaria de
   9.000 tokens, porque o custo fixo do CLI (system prompt, `AGENTS.md`, ferramentas e MCP) é
   ≈ **7.973 tokens** — medido no PR #3.
2. O Gemini tem **1M de contexto** e TPM alto no free tier — revisa PRs grandes sem truncar.
3. Cada modelo Gemini tem **cota free separada** (medido entre 3.8 e 3 Flash em 07/11); três modelos
   dão três chances sem custo.
4. `google/gemini-2.5-flash` **não está mais disponível para contas novas** (erro real do provider);
   o substituto indicado é o `gemini-3.8-flash`.

O workflow gera **dois diffs**: `pr.diff` (até 80 KB, usado pelos Gemini) e `pr-small.diff` (3 KB, só
para modelos `groq/*`). A escolha é pelo prefixo do modelo, então trocar as variables não quebra o TPM.

## Comparativo

| Provider | Free? | Limites do free (documentados) | Qualidade p/ review | Atrito | Veredito |
|---|---|---|---|---|---|
| **Groq** | Sim | 30 RPM · 1.000 RPD · 8K TPM · 200K TPD (`gpt-oss-120b`) | Boa | Baixo (API key) | Free não cabe (custo fixo ~8k); só Dev Tier |
| **OpenCode Zen (free tier)** | Sim | **Não documentados**; modelos `*-free` | Boa (DeepSeek V4.1 Flash) | Baixo (mesma conta do uso local) | Alternativa; risco de cota opaca |
| **OpenRouter** | Sim (`:free`) | 20 RPM · 50 req/dia (< US$10 em créditos) ou 1.000/dia (≥ US$10) | Variável por modelo | Médio | Bom se já usa OpenRouter |
| **Google Gemini** | Sim | RPD na casa de centenas a 1.000 e TPM alto, **varia por modelo** | Muito boa | Médio (provider/env próprios) | **Escolhido** (cadeia de 3 modelos) |
| **OpenCode Go** | Não | US$ 10/mês com uso incluído (não é ilimitado) | Muito boa | Baixo | Recomendado se quiser previsibilidade |
| **GitHub Models** | — | **Desativado em 30/07/2026** | — | — | ❌ Indisponível |
| **Ollama local** | Sim | Ilimitado no seu hardware | Dependente do modelo | Alto no CI (runner CPU é lento) | Só para uso local |

> “Ilimitado” não existe em provider de nuvem. O que existe é cota gratuita grande (Gemini/OpenRouter)
> ou assinatura com uso incluído (Go). Para um harness pessoal, a cadeia Gemini é a que tem melhor
> relação entre contexto, cota gratuita e zero custo.

## Fallback automático (cadeia Gemini)

O workflow tenta os modelos em ordem e publica **um único comentário**, sem duplicar:

| Variable | Default |
|---|---|
| `OPENCODE_MODEL` | `google/gemini-3.8-flash` |
| `OPENCODE_MODEL_FALLBACK` | `google/gemini-3-flash-preview` |
| `OPENCODE_MODEL_FALLBACK2` | `google/gemini-3.1-flash-lite` |

```powershell
gh variable set OPENCODE_MODEL --body "google/gemini-3.8-flash"
gh variable set OPENCODE_MODEL_FALLBACK --body "google/gemini-3-flash-preview"
gh variable set OPENCODE_MODEL_FALLBACK2 --body "google/gemini-3.1-flash-lite"
gh secret set GEMINI_API_KEY
```

A cadeia é tentada em ordem. Cada tentativa roda em um **estado isolado** (`XDG_DATA_HOME`/`XDG_STATE_HOME`
próprios, `mktemp -d`), é limpa ao final e tem `timeout 360`: sem o isolamento o fallback herda a sessão
anterior e o contexto cresce até estourar o TPM (foi o que aconteceu no teste de 07/11: 73.567 tokens
pedidos mesmo com diff pequeno).

O provider `google` do catálogo do OpenCode aceita `GEMINI_API_KEY` (também aceita `GOOGLE_API_KEY` e
`GOOGLE_GENERATIVE_AI_API_KEY`). Cada modelo tem **cota free separada** — foi o que salvou o PR #1 em
07/11: o 3.8 devolveu "quota exceeded" em 9,6 s e o 3 Flash respondeu em 13 s.

### Por que a Groq saiu da cadeia

O free tier da Groq (`gpt-oss-120b`) tem **8.000 TPM**. A medição limpa do PR #3 (07/11) foi:

- diff de 15.037 bytes + prompt + stat ≈ 5.500 tokens (tokenizador o200k);
- requisição inteira: **13.473 tokens** → ~7.973 tokens de custo fixo (system prompt, `AGENTS.md`,
  definições de ferramentas e MCP).

Mesmo com diff de 3 KB a requisição passaria de 9.000 tokens. **Nenhum valor de `SMALL_DIFF_BYTES`
resolve** — por isso o terceiro modelo passou a ser outro Gemini. A Groq continua documentada como
opção para quem usar o Dev Tier; o workflow mantém `pr-small.diff` para modelos `groq/*`.

Limitação: `pr.diff` é truncado em 80 KB e o comentário avisa quando a revisão é parcial. Modelos
`groq/*`, se configurados manualmente, recebem `pr-small.diff` de 3 KB.

## Como trocar de provider

O modelo vem da variable `OPENCODE_MODEL` e a chave do secret correspondente:

| `OPENCODE_MODEL` | Secret | Observação |
|---|---|---|
| `google/gemini-3.8-flash` | `GEMINI_API_KEY` | **default**; 1M de contexto, free tier |
| `groq/openai/gpt-oss-120b` | `GROQ_API_KEY` | opcional; o free de 8K TPM não cabe (custo fixo ~8k) |
| `opencode/deepseek-v4.1-flash-free` | `OPENCODE_API_KEY` | free tier só funciona dentro do OpenCode |
| `openrouter/<modelo>:free` | `OPENROUTER_API_KEY` | cota diária baixa sem créditos |
| `anthropic/claude-sonnet-5-5` | `ANTHROPIC_API_KEY` | pago por token; melhor qualidade |

```powershell
gh variable set OPENCODE_MODEL --body "google/gemini-3.8-flash"
gh secret set GEMINI_API_KEY
```

Se o modelo for de um provider pago ou com TPM alto, ajuste `MAX_DIFF_BYTES` para cima. A cadeia default
não usa `pr-small.diff`; ele existe só para modelos `groq/*`.

## Verificação rápida antes de confiar no CI

```powershell
opencode auth login          # ou /connect → Groq
opencode run --model groq/openai/gpt-oss-120b "responda apenas: ok"
```

Se responder `ok`, o mesmo modelo funciona no workflow (que usa `--standalone` + a key em variável de
ambiente).

## Fontes

- Groq — rate limits: <https://console.groq.com/docs/rate-limits>
- Groq — OpenCode: <https://console.groq.com/docs/coding-with-groq/opencode>
- OpenRouter — limits: <https://openrouter.ai/docs/api-reference/limits>
- Gemini — rate limits: <https://ai.google.dev/gemini-api/docs/rate-limits>
- OpenCode Console — modelos free: <https://opencode.ai/v2/docs/console/models/>
- OpenCode Console — Go: <https://opencode.ai/v2/docs/console/go/>
- GitHub Models desativado: <https://docs.github.com/en/github-models/use-github-models/prototyping-with-ai-models>
