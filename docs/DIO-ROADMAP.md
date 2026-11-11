# Roadmap — Santander · Dados com Python e IA (DIO)

> Trilha oficial: <https://web.dio.me/track/santander-dados-com-python-e-ia>
> Este documento é um **mapa de trabalho** para usar o harness. O conteúdo oficial, a ordem e os prazos
> valem sempre mais — atualize este arquivo conforme os módulos forem liberados na DIO.

## Dados públicos da trilha

| Item | Valor divulgado |
|---|---|
| Carga horária | 50 horas |
| Duração | 3 meses |
| Início | 03/11/2026 |
| Término | 31/12/2026 |
| Formato | 100% online, mentorias ao vivo, desafios de código e de projeto |
| Pilares | Python, bancos de dados/SQL, análise de dados, Machine Learning, IA generativa/agentes |
| Projetos citados | detecção de anomalias em transações, DataPilot (agentes de IA), assistente virtual |

Datas e nomes mudam entre chamadas do programa (a página da Santander Open Academy já exibiu mais de uma
janela de inscrição). **Confirme no edital** antes de planejar férias ou entrega.

## Como o harness entra em cada atividade

```
issue (template "Atividade DIO")
   └── branch dio/<modulo>-<tema>
          └── notebook + código em src/ + teste em tests/
                 └── PR  ──► CI (ruff + pytest)
                        └── revisão automática do OpenCode
                               └── merge na main
```

Regras que valem para todas as atividades:

1. Uma atividade = uma branch = um PR. Histórico limpo é o que recrutador vê.
2. Notebook só orquestra; o que precisa de teste vai para `src/opencode_harness/`.
3. Conclusões escritas no fim do notebook (o que aprendeu, o que faria diferente).
4. Sem dados brutos no git; registre a origem em `data/README.md`.
5. Feche a atividade marcando o checklist em `docs/DIO-ROADMAP.md` (este arquivo).

## Plano de 8 semanas (ajustável)

| Semana | Foco | Entregável no repo |
|---|---|---|
| 1 | Fundamentos de Python, estruturas de dados | `notebooks/dio-01-python.ipynb` + exercícios em `src/` |
| 2 | Funções, POO, tratamento de erros | módulo testado em `src/` + `tests/` |
| 3 | SQL e bancos relacionais | notebook com queries + script de carga |
| 4 | Análise exploratória (pandas) | `notebooks/dio-03-eda-<tema>.ipynb` com `profile()` |
| 5 | Estatística e Machine Learning | notebook com baseline + `random_state` fixo |
| 6 | IA generativa, prompt engineering, agentes | chamadas de LLM isoladas em `src/` |
| 7 | Projeto: detecção de anomalias | notebook + módulo de features + teste |
| 8 | Projeto: DataPilot / assistente virtual | app ou notebook final + README de portfólio |

## Checklist de atividades

Copie a linha ao criar a issue. Marque `[x]` só depois do merge.

| # | Módulo / atividade | Branch | Status |
|---|---|---|---|
| 01 | Fundamentos de Python | `dio/01-python` | [x] |
| 02 | Estruturas de dados e funções | `dio/02-estruturas` | [x] |
| 03 | POO e organização de código | `dio/03-poo` | [x] |
| 04 | Banco de dados e SQL | `dio/04-sql` | [ ] |
| 05 | Análise exploratória de dados | `dio/05-eda` | [ ] |
| 06 | Machine Learning — baseline | `dio/06-ml-baseline` | [ ] |
| 07 | IA generativa e agentes | `dio/07-ia-agentes` | [ ] |
| 08 | Desafio: detecção de anomalias | `dio/08-anomalias` | [ ] |
| 09 | Desafio: DataPilot / assistente | `dio/09-datapilot` | [ ] |
| 10 | README de portfólio + revisão final | `dio/10-portfolio` | [ ] |

## Prompts úteis no dia a dia

```
# planejar
Leia a descrição da atividade <X> em docs/DIO-ROADMAP.md e proponha um plano
de 3 passos com critérios de aceite. Não escreva código ainda.

# implementar
Implemente o passo 1 em notebooks/dio-05-eda.ipynb, reutilizando
opencode_harness.profile. Rode ruff e pytest antes de terminar.

# revisar antes do PR
Revise o diff atual como se fosse um PR: cite arquivo:linha e classifique
os achados em bloqueante/importante/sugestão.

# explicar para entrevista
Explique este notebook como se eu fosse responder em entrevista:
decisões, trade-offs e o que eu faria com mais tempo.
```

## Critérios de "pronto para portfólio"

- [ ] README do repositório explica o problema, os dados e como rodar.
- [ ] Cada notebook tem objetivo, método e conclusão em linguagem simples.
- [ ] Pelo menos um teste automatizado por módulo de `src/`.
- [ ] CI verde e histórico de PRs revisados.
- [ ] Nenhum segredo, `.env` ou dado bruto no histórico (`git log --all -- .env`).
