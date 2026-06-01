$ErrorActionPreference = "Stop"

if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv run --with streamlit --with pandas --with plotly streamlit run painel_inscricoes.py
} else {
    streamlit run painel_inscricoes.py
}
