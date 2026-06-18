# Painel de Inscrições OIAA

Dashboard em Streamlit para visualizar os dados administrativos de inscrições da Olimpíada de Inteligência Artificial Aplicada.

O acesso ao painel é bloqueado até que o usuário faça login com credenciais administrativas válidas na API.

## Funcionalidades

- KPIs de equipes, inscrições enviadas, rascunhos e participantes.
- Gráficos por status, categoria e evolução diária das inscrições.
- Visões geográficas por UF e cidade.
- Análises de participantes por status, gênero, série escolar e tipo de escola.
- Acompanhamento de documentos enviados e pendentes.
- Filtros por status, UF, período e busca textual.
- Tabelas com exportação em CSV.
- Atualização direta pela API: login, paginação da lista e busca dos detalhes.

## Tecnologias

- **Streamlit**: Framework web interativo para dashboards em Python.
- **Pandas**: Manipulação e análise de dados estruturados (DataFrames).
- **Plotly**: Visualizações gráficas interativas (charts, mapas, scatter plots).
- **Requests**: Comunicação HTTP com a API de autenticação e dados de inscrições.
- **Python 3.8+**: Linguagem base do projeto.

**Recomendamos rodar este projeto com `uv`**, um gerenciador de pacotes Python rápido e confiável. Veja "Como rodar com uv" para instruções completas.

## Estrutura

```text
.
├── painel_inscricoes.py
├── requirements.txt
├── dados/
│   └── .gitkeep
├── run.sh
└── README.md
```

O arquivo `dados/inscricoes-detalhadas.json` não é versionado porque pode conter dados pessoais.

## Como rodar com uv (recomendado)

### 1) Instale o uv

Windows (winget):

```powershell
winget install astral-sh.uv
```

macOS e Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verifique a instalação:

```bash
uv --version
```

### 2) Entre na pasta do projeto

```bash
cd painel-inscricoes-oiaa
```

### 3) Crie o ambiente virtual

```bash
uv venv .venv
```

### 4) Ative o ambiente virtual

PowerShell (Windows):

```powershell
.\.venv\Scripts\Activate.ps1
```

CMD (Windows):

```bat
.venv\Scripts\activate.bat
```

Bash (Linux/macOS/Git Bash):

```bash
source .venv/bin/activate
```

### 5) Instale os pacotes

```bash
uv pip install -r requirements.txt
```

Isso instala as dependências do painel, incluindo `streamlit`, `pandas`, `plotly` e `requests`.

### 6) Garanta o arquivo de dados

Copie ou gere o arquivo em:

```text
dados/inscricoes-detalhadas.json
```

### 7) Rode o painel

Com o ambiente ativado (recomendado):

```bash
python -m streamlit run painel_inscricoes.py
```

Sem ativar ambiente (isolado via uv):

```bash
uv run --with streamlit --with pandas --with plotly --with requests python -m streamlit run painel_inscricoes.py
```

Atalho local (Bash/Git Bash):

```bash
bash run.sh
```

### Solução de problemas rápida

- Erro `ModuleNotFoundError: No module named 'plotly'`: execute `uv pip install -r requirements.txt` com a env ativada.
- Erro `uv trampoline failed to canonicalize script path` no Windows: use `python -m streamlit run painel_inscricoes.py` com a env ativada.

### Fallback sem uv (pip tradicional)

Se você preferir não usar `uv`, faça:

```bash
python -m venv .venv
# ative a env
pip install -r requirements.txt
python -m streamlit run painel_inscricoes.py
```

## Mantendo os dados atualizados

### Por que atualizar?

O arquivo `dados/inscricoes-detalhadas.json` é consultado localmente para renderizar o dashboard. Se você não atualizar os dados, verá informações desatualizadas (inscrições antigas, status que não mudaram, etc.).

### Como atualizar?

1. **Abra o painel** normalmente (veja seção "Como rodar com uv").
2. **Faça login** com suas credenciais administrativas.
3. No menu lateral esquerdo, procure pela seção **"Atualizar pela API"**.
4. **Clique no botão "Atualizar Inscrições"** (ou similar).
5. O painel fará login novamente, baixará todas as inscrições da API e salvará em `dados/inscricoes-detalhadas.json`.
6. **Atualize a página do navegador** (F5 ou Cmd+R) após a atualização terminar.
7. Os gráficos, tabelas e KPIs agora mostrarão dados recentes.

### Fluxo de autenticação e atualização técnico

O painel implementa o seguinte fluxo:

1. `POST /api/auth/login` com `email` e `senha`.
2. Extração do token retornado pelo login.
3. Liberação da visualização do painel somente após autenticação bem-sucedida.
4. No menu lateral, a seção **Atualizar pela API** usa a sessão autenticada para chamar `GET /api/admin/inscricoes` com paginação.
5. `GET /api/admin/inscricoes/{id}` para detalhar cada inscrição.
6. Gravação do resultado em `dados/inscricoes-detalhadas.json`.

### Dicas para melhorar a experiência

**Evitar digitar credenciais toda vez:**

Configure as variáveis de ambiente:

```bash
OIAA_EMAIL="seu-email"
OIAA_SENHA="sua-senha"
OIAA_BASE_URL="https://olimpiadadeia.ceia.digital"
```

Ou use `.streamlit/secrets.toml` (local):

```toml
OIAA_EMAIL = "seu-email"
OIAA_SENHA = "sua-senha"
OIAA_BASE_URL = "https://olimpiadadeia.ceia.digital"
```

**⚠️ Importante:** Não faça commit de `.streamlit/secrets.toml` — adicione ao `.gitignore` se necessário.

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
