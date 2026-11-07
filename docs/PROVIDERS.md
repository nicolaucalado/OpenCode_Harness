# Análise de providers para o CI

Objetivo: revisar PRs automaticamente com **custo zero ou previsível**, boa disponibilidade e limites
documentados. Análise feita em **04/11/2026**.

## Resumo da decisão

**Default do CI: Gemini (`google/gemini-3.8-flash`) com fallback Groq (`groq/openai/gpt-oss-120b`).**

Motivos (revisados em 07/11/2026, depois do primeiro teste real):

1. O limite de **8.000 TPM** da Groq free não cabe no harness: um diff de 24 KB gerou uma requisição
   de **13.473 tokens** (o CLI envia também system prompt e definições de ferramentas) e foi rejeitada.
2. O Gemini tem **1M de contexto** e TPM alto no free tier — revisa PRs grandes sem truncar.
3. A Groq continua útil como **fallback** para diffs pequenos: 30 RPM, **1.000 req/dia**, custo zero.
4. `google/gemini-2.5-flash` **não está mais disponível para contas novas** (erro real do provider);
   o substituto indicado é o `gemini-3.8-flash`.

O workflow gera **dois diffs**: `pr.diff` (até 80 KB, usado pelo Gemini) e `pr-small.diff` (3 KB, usado
por `groq/*`). A escolha é pelo prefixo do modelo, então trocar as variables não quebra o limite de TPM.

## Comparativo

| Provider | Free? | Limites do free (documentados) | Qualidade p/ review | Atrito | Veredito |
|---|---|---|---|---|---|
| **Groq** | Sim | 30 RPM · 1.000 RPD · 8K TPM · 200K TPD (`gpt-oss-120b`) | Boa | Baixo (API key) | **Escolhido** |
| **OpenCode Zen (free tier)** | Sim | **Não documentados**; modelos `*-free` | Boa (DeepSeek V4.1 Flash) | Baixo (mesma conta do uso local) | Alternativa; risco de cota opaca |
| **OpenRouter** | Sim (`:free`) | 20 RPM · 50 req/dia (< US$10 em créditos) ou 1.000/dia (≥ US$10) | Variável por modelo | Médio | Bom se já usa OpenRouter |
| **Google Gemini** | Sim | RPD na casa de centenas a 1.000 e TPM alto, **varia por modelo** | Muito boa | Médio (provider/env próprios) | Melhor opção para diffs grandes |
| **OpenCode Go** | Não | US$ 10/mês com uso incluído (não é ilimitado) | Muito boa | Baixo | Recomendado se quiser previsibilidade |
| **GitHub Models** | — | **Desativado em 30/07/2026** | — | — | ❌ Indisponível |
| **Ollama local** | Sim | Ilimitado no seu hardware | Dependente do modelo | Alto no CI (runner CPU é lento) | Só para uso local |

> “Ilimitado” não existe em provider de nuvem. O que existe é cota gratuita grande (Groq/OpenRouter) ou
> assinatura com uso incluído (Go). Para um harness pessoal, a cota da Groq é a que tem melhor relação
> entre documentação, volume e zero custo.

## Fallback automático (Groq → Gemini)

O workflow de review tenta o modelo primário e, se ele falhar (429, indisponibilidade, timeout),
repete com o fallback **sem duplicar o comentário**:

| Variable | Default |
|---|---|
| `OPENCODE_MODEL` | `google/gemini-3.8-flash` |
| `OPENCODE_MODEL_FALLBACK` | `google/gemini-3-flash-preview` |
| `OPENCODE_MODEL_FALLBACK2` | `groq/openai/gpt-oss-120b` |

```powershell
gh variable set OPENCODE_MODEL --body "google/gemini-3.8-flash"
gh variable set OPENCODE_MODEL_FALLBACK --body "google/gemini-3-flash-preview"
gh variable set OPENCODE_MODEL_FALLBACK2 --body "groq/openai/gpt-oss-120b"
gh secret set GEMINI_API_KEY
gh secret set GROQ_API_KEY
```

A cadeia é tentada em ordem. Cada tentativa roda em um **estado isolado** (`XDG_DATA_HOME`/`XDG_STATE_HOME`
próprios, `mktemp -d`) e com `timeout 240`: sem isso o fallback herda a sessão anterior e o contexto
cresce até estourar o TPM (foi o que aconteceu no teste de 07/11: 73.567 tokens pedidos mesmo com um
diff pequeno; a causa era o contexto herdado).

O provider `google` do catálogo do OpenCode aceita `GEMINI_API_KEY` (também aceita `GOOGLE_API_KEY` e
`GOOGLE_GENERATIVE_AI_API_KEY`). O modelo `google/gemini-3.8-flash` tem 1M de contexto e é o primário.

Limitação: o Groq free **não aceita** o diff grande. Por isso o review gera `pr.diff` (até 80 KB) e
`pr-small.diff` (3 KB); modelos `groq/*` recebem o pequeno automaticamente. Se o fallback for outro
provider com TPM baixo, ajuste `SMALL_DIFF_BYTES`.

## Como trocar de provider

O modelo vem da variable `OPENCODE_MODEL` e a chave do secret correspondente:

| `OPENCODE_MODEL` | Secret | Observação |
|---|---|---|
| `google/gemini-3.8-flash` | `GEMINI_API_KEY` | **default**; 1M de contexto, free tier |
| `groq/openai/gpt-oss-120b` | `GROQ_API_KEY` | fallback; 1.000 req/dia, 8K TPM (diff pequeno) |
| `opencode/deepseek-v4.1-flash-free` | `OPENCODE_API_KEY` | free tier só funciona dentro do OpenCode |
| `openrouter/<modelo>:free` | `OPENROUTER_API_KEY` | cota diária baixa sem créditos |
| `anthropic/claude-sonnet-5-5` | `ANTHROPIC_API_KEY` | pago por token; melhor qualidade |

```powershell
gh variable set OPENCODE_MODEL --body "google/gemini-3.8-flash"
gh secret set GEMINI_API_KEY
```

Se o modelo for de um provider pago, ajuste também `MAX_DIFF_BYTES` no workflow para cima (o limite da
Groq é o que exige o truncamento).

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
