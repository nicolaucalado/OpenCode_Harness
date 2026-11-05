# Notebooks

Um notebook por atividade, nomeado `dio-<modulo>-<tema>.ipynb`.

- `00_template.ipynb` é o ponto de partida; copie em vez de editar o template.
- Kernel: `opencode-harness` (veja `docs/SETUP.md`).
- Antes de comitar: **Kernel → Restart & Run All** e confira se não há erro nem saída gigante.
- Notebook não é biblioteca: lógica reaproveitável vai para `src/opencode_harness/` e ganha teste em `tests/`.
- Dados ficam em `data/raw/` (fora do git). Cite a origem do arquivo no próprio notebook.
