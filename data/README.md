# Dados

```
data/
├── raw/        # arquivos originais (nunca versionados)
└── processed/  # dados derivados (nunca versionados)
```

Regras:

1. Nada de dado bruto no git — os dois diretórios estão no `.gitignore`.
2. Documente a origem em `docs/DADOS.md` (link, data de download, licença e como reproduzir).
3. Scripts de transformação ficam em `src/opencode_harness/` ou `scripts/` e devem ser determinísticos.
4. Se o dataset for público e pequeno (<1 MB) e você quiser versionar para portfólio, avalie caso a caso e registre a decisão.

Enquanto não houver dados, este README mantém a pasta no repositório.
