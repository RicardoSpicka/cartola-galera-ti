
name: Atualizar histórico do Cartola

on:
  schedule:
    - cron: "0 12 * * 2,4"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  atualizar:
    runs-on: ubuntu-latest

    steps:
      - name: Baixar repositório
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Instalar dependências
        run: pip install requests

      - name: Atualizar histórico
        run: python atualizar_historico.py

      - name: Salvar alterações no GitHub
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add historico_cartola.csv
          if git diff --cached --quiet; then
            echo "Nenhuma alteração no histórico."
          else
            git commit -m "Atualiza histórico do Cartola"
            git push
          fi
