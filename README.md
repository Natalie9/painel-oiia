# Painel de Inscrições OIAA

Dashboard em Streamlit para visualizar os dados administrativos de inscrições da Olimpíada de Inteligência Artificial Aplicada.

## Funcionalidades

- KPIs de equipes, inscrições enviadas, rascunhos e participantes.
- Gráficos por status, categoria e evolução diária das inscrições.
- Visões geográficas por UF e cidade.
- Análises de participantes por status, gênero, série escolar e tipo de escola.
- Acompanhamento de documentos enviados e pendentes.
- Filtros por status, UF, período e busca textual.
- Tabelas com exportação em CSV.

## Estrutura

```text
.
├── painel_inscricoes.py
├── requirements-streamlit.txt
├── dados/
│   └── .gitkeep
└── README.md
```

O arquivo `dados/inscricoes-detalhadas.json` não é versionado porque pode conter dados pessoais.

## Como rodar

1. Copie ou gere o arquivo de dados em:

```text
dados/inscricoes-detalhadas.json
```

2. Instale as dependências:

```bash
pip install -r requirements-streamlit.txt
```

3. Inicie o painel:

```bash
streamlit run painel_inscricoes.py
```

Alternativa usando `uv`:

```bash
uv run --with streamlit --with pandas --with plotly streamlit run painel_inscricoes.py
```

## Fonte dos dados

O painel espera um JSON no formato gerado pelo script de coleta das inscrições, com as chaves principais:

- `geradoEm`
- `resumo`
- `detalhes`

Dentro de `detalhes`, o painel utiliza informações de inscrição, tutor, equipe e participantes.

## Segurança e privacidade

Os dados de inscrições podem conter nome, e-mail, CPF, telefone, endereço e informações escolares. Por isso:

- não faça commit de arquivos JSON reais de inscrições;
- não publique exportações CSV com dados pessoais;
- compartilhe o painel e seus dados apenas com pessoas autorizadas.
