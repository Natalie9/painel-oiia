#!/usr/bin/env bash
set -euo pipefail

if command -v uv >/dev/null 2>&1; then
  uv run --with streamlit --with pandas --with plotly --with requests python -m streamlit run painel_inscricoes.py
else
  python -m streamlit run painel_inscricoes.py
fi
