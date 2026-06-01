#!/usr/bin/env bash
set -euo pipefail

if command -v uv >/dev/null 2>&1; then
  uv run --with streamlit --with pandas --with plotly streamlit run painel_inscricoes.py
else
  streamlit run painel_inscricoes.py
fi
