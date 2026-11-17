# Dados

Registro de origem dos datasets usados nas atividades. Atualize a cada atividade.

| Atividade | Arquivo | Origem (URL) | Licença | Baixado em | Como reproduzir |
|---|---|---|---|---|---|
| 05–09 | `vendas` (DataFrame e tabela SQLite) | sintético, gerado em código | MIT (dados sintéticos) | — | `uv run python -c "from opencode_harness.dados import gerar_vendas; print(gerar_vendas(seed=42).shape)"` |

## Boas práticas

- Guarde o arquivo original em `data/raw/` e **não** comite (está no `.gitignore`).
- Derivados vão para `data/processed/`; o script que gera deve estar no repo.
- Se o dataset for público e pequeno, você pode versionar — registre a decisão na tabela acima.
- Dados pessoais ou sensíveis: anonimize antes de qualquer commit e nunca publique amostras identificáveis.
- Registre a licença: usar dados sem checar licença é problema comum em portfólio.
