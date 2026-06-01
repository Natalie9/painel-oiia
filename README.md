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
- Atualização direta pela API: login, paginação da lista e busca dos detalhes.

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
uv run --with streamlit --with pandas --with plotly --with requests streamlit run painel_inscricoes.py
```

Também há atalhos locais:

PowerShell:

```powershell
./run.ps1
```

Bash/Git Bash:

```bash
bash run.sh
```

## Atualizar dados pela API

No menu lateral do painel, use a seção **Atualizar pela API**.

O fluxo implementado é:

1. `POST /api/auth/login` com `email` e `senha`.
2. Extração do token retornado pelo login.
3. `GET /api/admin/inscricoes` com paginação.
4. `GET /api/admin/inscricoes/{id}` para detalhar cada inscrição.
5. Gravação do resultado em `dados/inscricoes-detalhadas.json`.

Para evitar digitar credenciais toda vez, você pode usar variáveis de ambiente:

```bash
OIAA_EMAIL="seu-email"
OIAA_SENHA="sua-senha"
OIAA_BASE_URL="https://olimpiadadeia.ceia.digital"
```

Ou configurar os mesmos nomes em `.streamlit/secrets.toml`:

```toml
OIAA_EMAIL = "seu-email"
OIAA_SENHA = "sua-senha"
OIAA_BASE_URL = "https://olimpiadadeia.ceia.digital"
```

Não faça commit de `.streamlit/secrets.toml`.

## Fonte dos dados

O painel espera um JSON no formato gerado pelo fluxo da API ou pelo script de coleta das inscrições, com as chaves principais:

- `geradoEm`
- `resumo`
- `detalhes`

Dentro de `detalhes`, o painel utiliza informações de inscrição, tutor, equipe e participantes.

## Segurança e privacidade

Os dados de inscrições podem conter nome, e-mail, CPF, telefone, endereço e informações escolares. Por isso:

- não faça commit de arquivos JSON reais de inscrições;
- não publique exportações CSV com dados pessoais;
- compartilhe o painel e seus dados apenas com pessoas autorizadas.
