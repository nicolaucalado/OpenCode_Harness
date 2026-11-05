# Análise de providers para o CI

Objetivo: revisar PRs automaticamente com **custo zero ou previsível**, boa disponibilidade e limites
documentados. Análise feita em **04/11/2026**.

## Resumo da decisão

**Default do CI: Groq (plano free) com `groq/openai/gpt-oss-120b`.**

Motivos:

1. Limites **públicos e generosos** para uso pessoal: 30 req/min, **1.000 req/dia**, 8.000 tokens/min,
   200.000 tokens/dia.
2. Provider **nativo** no OpenCode (a própria Groq documenta o OpenCode como cliente).
3. Sem cartão de crédito e sem custo por token.
4. Uma revisão por push consome 1 requisição — 1.000/dia cobre com folga um portfólio ativo.

O gargalo é o **TPM de 8.000**: por isso o workflow trunca o diff em 24 KB (~6 mil tokens) e avisa no
comentário quando isso acontece. PRs gigantes recebem revisão parcial.

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

## Como trocar de provider

O modelo vem da variable `OPENCODE_MODEL` e a chave do secret correspondente:

| `OPENCODE_MODEL` | Secret | Observação |
|---|---|---|
| `groq/openai/gpt-oss-120b` | `GROQ_API_KEY` | default; 1.000 req/dia |
| `opencode/deepseek-v4.1-flash-free` | `OPENCODE_API_KEY` | free tier só funciona dentro do OpenCode |
| `openrouter/<modelo>:free` | `OPENROUTER_API_KEY` | cota diária baixa sem créditos |
| `google/gemini-...` | `GOOGLE_GENERATIVE_AI_API_KEY` | confirme o nome da variável no seu provider |
| `anthropic/claude-sonnet-5-5` | `ANTHROPIC_API_KEY` | pago por token; melhor qualidade |

```powershell
gh variable set OPENCODE_MODEL --body "groq/openai/gpt-oss-120b"
gh secret set GROQ_API_KEY
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
