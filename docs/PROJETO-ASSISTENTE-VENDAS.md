# Projeto — Assistente Inteligente de Vendas

Assistente que responde perguntas de negócio em português sobre uma base de vendas em SQLite.
É o projeto de conclusão da trilha **Santander — Dados com Python e IA (DIO)** e reutiliza as
peças construídas nas atividades 04 (SQL), 05 (dados), 06 (ML) e 07 (agentes).

## Problema

Quem trabalha com vendas perde tempo abrindo planilha, escrevendo `SELECT` ou pedindo número para
outra pessoa. A pergunta é simples — *"qual categoria rende mais?"*, *"como foi o mês?"* — mas a
resposta exige saber onde o dado está e como consultá-lo.

O assistente resolve isso em duas camadas:

| Camada | Quando entra | Custo | Determinística |
|---|---|---|---|
| **Roteamento por intenção** | pergunta reconhecida por palavra-chave | zero token | sim |
| **Agente com ferramentas** | pergunta fora do roteiro | 1+ chamada de LLM | depende do provedor |

O roteamento resolve o caso comum sem depender de LLM. O agente cobre o resto, mas **só** pode
chamar ferramentas registradas — nunca SQL livre.

## Arquitetura

```
pergunta
   │
   ├─ normalizar (minúsculas, sem acento)
   │
   ├─ detectar_intencao ──► consulta SQL parametrizada ──► resposta formatada
   │        (receita, categoria, UF, canal, mês, produtos, contagem, resumo)
   │
   └─ None ──► Agente (llm.py)
                 ├─ ProvedorFalso (offline, determinístico)  ← default
                 └─ ProvedorOpenAI (endpoint compatível, opcional)
                        │
                        └─ pede ferramenta whitelisted ──► validar argumentos ──► consulta
```

### Arquivos

| Arquivo | Papel |
|---|---|
| `src/opencode_harness/assistente.py` | roteamento, consultas, ferramentas e `AssistenteVendas` |
| `src/opencode_harness/llm.py` | `Provedor`, `Ferramenta`, `Agente`, `ProvedorFalso`, `ProvedorOpenAI` |
| `src/opencode_harness/dados.py` | geração/limpeza da base e carga no SQLite (`para_sqlite`) |
| `tests/test_assistente.py` | testes das consultas, do roteamento e do fallback |
| `notebooks/projeto-assistente-vendas.ipynb` | demonstração ponta a ponta com saídas |

## Como rodar

```bash
# testes e lint
uv run pytest -q
uv run ruff check .
uv run ruff format --check .

# demo sem chave (provedor falso)
uv run python - <<'PY'
from opencode_harness.assistente import AssistenteVendas, criar_banco
from opencode_harness.dados import gerar_vendas, limpar_vendas

conn = criar_banco(limpar_vendas(gerar_vendas(seed=42)))
assistente = AssistenteVendas(conn)
for pergunta in [
    "Qual é a receita total?",
    "Receita por categoria",
    "Como foi a evolução mensal?",
    "Quais os produtos mais vendidos?",
]:
    print("P:", pergunta)
    print("R:", assistente.perguntar(pergunta))
    print()
PY
```

Com um endpoint compatível com OpenAI (opcional):

```bash
export OPENAI_API_KEY="..."
# opcional: outro endpoint compatível; sem ela, usa https://api.openai.com/v1
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4o-mini"
```

Sem essas variáveis, o assistente usa o provedor falso e continua funcionando — é assim que o
notebook e o CI rodam.

## Perguntas suportadas pelo roteamento

- receita total e número de vendas;
- receita por categoria, por UF e por canal (com ticket médio);
- produtos mais vendidos por unidades;
- melhor/pior mês e evolução mensal;
- resumo geral (total + líderes).

Perguntas fora dessa lista vão para o agente. Sem chave, ele responde o que sabe fazer — não
inventa número.

## Decisões e trade-offs

1. **Roteamento antes do LLM.** Pergunta comum não deve custar token nem depender de rede. O
   roteador é uma lista ordenada de palavras-chave: simples de auditar e de testar.
2. **Ferramentas, não SQL livre.** O modelo escolhe *qual* consulta rodar, não *como*. Isso elimina
   injeção de SQL e mantém o custo previsível. O preço é menos flexibilidade: pergunta fora das
   ferramentas não é respondida.
3. **Provedor falso como default.** Portfolio precisa rodar em qualquer clone. O `ProvedorFalso` é
   determinístico e cobre o loop do agente; o provedor real é opcional.
4. **SQLite em memória por padrão.** A base é sintética e recriada por `gerar_vendas(seed=42)`;
   persistir em arquivo é uma linha (`para_sqlite(caminho)`) e a pasta é gitignored.
5. **Formatação de moeda sem `locale`.** `formatar_moeda` troca separadores manualmente, porque
   `locale` varia por sistema operacional e quebra em CI.
6. **Respostas curtas e auditáveis.** Cada intenção retorna uma frase com os números usados. Isso
   facilita testar e revisar; um relatório longo esconderia erro de conta.

## Segurança

- Nenhuma ferramenta recebe SQL, caminho de arquivo ou shell.
- Argumentos são validados contra o schema da `Ferramenta` antes da execução.
- Consultas usam parâmetros (`?`), nunca interpolação de string.
- O provedor real lê a chave de ambiente e nunca a devolve em mensagem de erro.
- O agente tem `max_passos=3`: provedor teimoso não gera loop infinito.

## Limitações e próximos passos

- A base é **sintética**; os números não representam mercado real.
- O roteador não entende sinônimo fora da lista — é aí que o LLM entra.
- Não há memória entre perguntas: cada chamada começa do zero.
- O provedor real não tem retry automático: falha de rede vira `ProvedorIndisponivel` com mensagem
  clara, e quem chama decide tentar de novo.
- Próximos passos naturais: persistir o modelo da aula 06 e responder *"esta venda é alto valor?"*;
  adicionar log de ferramenta chamada; expor como CLI ou API FastAPI.

## Entrega na DIO

- [x] Código no GitHub, com testes e CI verde.
- [x] Notebook executado com saídas.
- [x] README do projeto explicando problema, dados e como rodar.
- [ ] Submissão no portal da DIO (exige login do aluno).
- [ ] Se houver repositório de referência oficial, comparar o enunciado e ajustar o que faltar.
