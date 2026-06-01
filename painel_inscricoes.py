import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import plotly.express as px
import streamlit as st


DATA_PADRAO = Path("dados/inscricoes-detalhadas.json")
BASE_URL_PADRAO = "https://olimpiadadeia.ceia.digital"


st.set_page_config(
    page_title="Painel de Inscrições OIAA",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def carregar_json(caminho: str) -> dict:
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def request_json(session: requests.Session, method: str, url: str, **kwargs):
    resposta = session.request(method, url, timeout=30, **kwargs)
    try:
        payload = resposta.json()
    except ValueError:
        payload = resposta.text

    if not resposta.ok:
        detalhe = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        raise RuntimeError(f"HTTP {resposta.status_code} em {url}: {detalhe}")

    return payload


def encontrar_token(payload):
    if isinstance(payload, str):
        if payload.count(".") == 2 and len(payload) > 40:
            return payload
        return None

    if isinstance(payload, dict):
        for chave in ["token", "accessToken", "access_token", "jwt", "idToken", "id_token"]:
            valor = payload.get(chave)
            if isinstance(valor, str) and valor:
                return valor.replace("Bearer ", "")

        for valor in payload.values():
            token = encontrar_token(valor)
            if token:
                return token

    if isinstance(payload, list):
        for item in payload:
            token = encontrar_token(item)
            if token:
                return token

    return None


def extrair_itens_lista(resultado_lista):
    if isinstance(resultado_lista, list):
        return resultado_lista

    if not isinstance(resultado_lista, dict):
        return []

    for chave in ["content", "conteudo", "items", "itens", "data", "dados", "results", "resultado"]:
        valor = resultado_lista.get(chave)
        if isinstance(valor, list):
            return valor

    return []


def extrair_id_inscricao(item):
    if not isinstance(item, dict):
        return None
    return item.get("id") or item.get("inscricaoId") or item.get("inscricao_id") or item.get("codigo")


def tem_proxima_pagina(resultado_lista, pagina_atual, tamanho, itens):
    if not isinstance(resultado_lista, dict):
        return len(itens) == tamanho

    if isinstance(resultado_lista.get("last"), bool):
        return not resultado_lista["last"]
    if isinstance(resultado_lista.get("ultima"), bool):
        return not resultado_lista["ultima"]
    if isinstance(resultado_lista.get("totalPages"), int):
        return pagina_atual + 1 < resultado_lista["totalPages"]
    if isinstance(resultado_lista.get("totalPaginas"), int):
        return pagina_atual + 1 < resultado_lista["totalPaginas"]
    if isinstance(resultado_lista.get("totalElements"), int):
        return (pagina_atual + 1) * tamanho < resultado_lista["totalElements"]
    if isinstance(resultado_lista.get("totalElementos"), int):
        return (pagina_atual + 1) * tamanho < resultado_lista["totalElementos"]

    return len(itens) == tamanho


def autenticar_admin(base_url: str, email: str, senha: str):
    session = requests.Session()
    session.headers.update(
        {
            "accept": "application/json, text/plain, */*",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "referer": f"{base_url}/login",
        }
    )

    payload = request_json(
        session,
        "POST",
        f"{base_url}/api/auth/login",
        json={"email": email, "senha": senha},
        headers={"content-type": "application/json"},
    )
    token = encontrar_token(payload)
    if not token:
        raise RuntimeError("Login realizado, mas não encontrei o token na resposta da API.")

    session.headers.update({"authorization": f"Bearer {token}"})
    return session


def baixar_inscricoes_api(base_url: str, email: str, senha: str, tamanho: int = 100, max_paginas: int = 100):
    session = autenticar_admin(base_url.rstrip("/"), email, senha)
    base_url = base_url.rstrip("/")
    paginas = []
    resumo = []
    detalhes = []
    pagina = 0

    for _ in range(max_paginas):
        lista = request_json(
            session,
            "GET",
            f"{base_url}/api/admin/inscricoes",
            params={"pagina": pagina, "tamanho": tamanho, "ordenar": "mais_recente"},
            headers={"referer": f"{base_url}/admin/dashboard"},
        )
        itens = extrair_itens_lista(lista)
        paginas.append(lista)
        resumo.extend(itens)

        for item in itens:
            inscricao_id = extrair_id_inscricao(item)
            if not inscricao_id:
                continue
            detalhe = request_json(
                session,
                "GET",
                f"{base_url}/api/admin/inscricoes/{inscricao_id}",
                headers={"referer": f"{base_url}/admin/inscricoes/{inscricao_id}"},
            )
            detalhes.append(detalhe)

        if not tem_proxima_pagina(lista, pagina, tamanho, itens):
            break
        pagina += 1

    return {
        "geradoEm": datetime.now(timezone.utc).isoformat(),
        "totalResumo": len(resumo),
        "totalDetalhes": len(detalhes),
        "resumo": resumo,
        "detalhes": detalhes,
        "paginasOriginais": paginas,
    }


def salvar_json(caminho: Path, data: dict):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def valor_secreto(nome: str, padrao: str = ""):
    try:
        return st.secrets.get(nome, os.getenv(nome, padrao))
    except Exception:
        return os.getenv(nome, padrao)


def valor_aninhado(obj: dict, caminho: str, padrao=None):
    atual = obj or {}
    for parte in caminho.split("."):
        if not isinstance(atual, dict):
            return padrao
        atual = atual.get(parte)
        if atual is None:
            return padrao
    return atual


def documento_enviado(obj: dict, campo: str):
    valor = valor_aninhado(obj, f"{campo}.enviado")
    if valor is None:
        return None
    return bool(valor)


def calcular_idade(data_nascimento):
    if pd.isna(data_nascimento):
        return None
    hoje = date.today()
    nascimento = data_nascimento.date() if hasattr(data_nascimento, "date") else data_nascimento
    return hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))


def rotulo(valor):
    if pd.isna(valor) or valor is None or valor == "":
        return "Não informado"
    return str(valor).replace("_", " ").title()


def montar_dataframes(data: dict):
    detalhes = data.get("detalhes") or []
    resumo = data.get("resumo") or []

    equipes = []
    participantes = []

    # Se o endpoint de detalhe não estiver presente, usa o resumo como fallback.
    if not detalhes and resumo:
        detalhes = [
            {
                "id": item.get("id"),
                "status": item.get("status"),
                "enviadaEm": item.get("enviadaEm"),
                "criadoEm": item.get("criadoEm"),
                "tutor": {
                    "nome": item.get("tutorNome"),
                    "email": item.get("tutorEmail"),
                },
                "equipe": {
                    "nome": item.get("equipeNome"),
                    "participantes": [],
                },
            }
            for item in resumo
        ]

    for inscricao in detalhes:
        tutor = inscricao.get("tutor") or {}
        equipe = inscricao.get("equipe") or {}
        endereco_tutor = tutor.get("endereco") or {}
        lista_participantes = equipe.get("participantes") or []

        equipes.append(
            {
                "inscricao_id": inscricao.get("id"),
                "status": inscricao.get("status"),
                "criado_em": inscricao.get("criadoEm"),
                "enviada_em": inscricao.get("enviadaEm"),
                "equipe_id": equipe.get("id"),
                "equipe_nome": equipe.get("nome"),
                "categoria": equipe.get("categoria"),
                "total_participantes": len(lista_participantes),
                "tutor_id": tutor.get("id"),
                "tutor_nome": tutor.get("nome"),
                "tutor_email": tutor.get("email"),
                "tutor_genero": tutor.get("genero"),
                "tutor_status": tutor.get("status"),
                "tutor_nivel_formacao": tutor.get("nivelFormacao"),
                "tutor_area_formacao": tutor.get("areaFormacao"),
                "tutor_eh_professor": tutor.get("ehProfessor"),
                "tutor_nome_escola": tutor.get("nomeEscola"),
                "tutor_cidade": endereco_tutor.get("cidade"),
                "tutor_estado": endereco_tutor.get("estado"),
                "tutor_doc_identidade": documento_enviado(tutor, "documentoIdentidade"),
                "tutor_doc_formacao": documento_enviado(tutor, "documentoFormacao"),
                "tutor_doc_vinculo": documento_enviado(tutor, "documentoVinculo"),
            }
        )

        for participante in lista_participantes:
            dados = participante.get("dados") or {}
            endereco = dados.get("endereco") or {}

            participantes.append(
                {
                    "inscricao_id": inscricao.get("id"),
                    "inscricao_status": inscricao.get("status"),
                    "equipe_nome": equipe.get("nome"),
                    "categoria": equipe.get("categoria"),
                    "slot_id": participante.get("slotId"),
                    "nome_convidado": participante.get("nomeConvidado"),
                    "email_convidado": participante.get("emailConvidado"),
                    "status_participante": participante.get("status"),
                    "cadastro_preenchido": bool(dados),
                    "participante_id": dados.get("id"),
                    "participante_nome": dados.get("nome") or participante.get("nomeConvidado"),
                    "genero": dados.get("genero"),
                    "data_nascimento": dados.get("dataNascimento"),
                    "serie_escolar": dados.get("serieEscolar"),
                    "tipo_escola": dados.get("tipoEscola"),
                    "nome_escola": dados.get("nomeEscola"),
                    "cidade": endereco.get("cidade"),
                    "estado": endereco.get("estado"),
                    "doc_identidade": documento_enviado(dados, "documentoIdentidade"),
                    "doc_matricula": documento_enviado(dados, "documentoMatricula"),
                }
            )

    df_equipes = pd.DataFrame(equipes)
    df_participantes = pd.DataFrame(participantes)

    for df in [df_equipes, df_participantes]:
        if df.empty:
            continue
        for col in df.columns:
            if col.endswith("_em") or col == "data_nascimento":
                df[col] = pd.to_datetime(df[col], errors="coerce")

    if not df_equipes.empty:
        df_equipes["data_criacao"] = df_equipes["criado_em"].dt.date
        df_equipes["status_rotulo"] = df_equipes["status"].map(rotulo)
        df_equipes["categoria_rotulo"] = df_equipes["categoria"].map(rotulo)
        df_equipes["tutor_estado"] = df_equipes["tutor_estado"].fillna("Não informado")
        df_equipes["tutor_cidade"] = df_equipes["tutor_cidade"].fillna("Não informado")

    if not df_participantes.empty:
        df_participantes["idade"] = df_participantes["data_nascimento"].apply(calcular_idade)
        df_participantes["status_participante_rotulo"] = df_participantes["status_participante"].map(rotulo)
        df_participantes["genero_rotulo"] = df_participantes["genero"].map(rotulo)
        df_participantes["serie_rotulo"] = df_participantes["serie_escolar"].map(rotulo)
        df_participantes["tipo_escola_rotulo"] = df_participantes["tipo_escola"].map(rotulo)
        df_participantes["estado"] = df_participantes["estado"].fillna("Não informado")
        df_participantes["cidade"] = df_participantes["cidade"].fillna("Não informado")

    return df_equipes, df_participantes


def grafico_contagem(df, coluna, titulo, orientacao="v", top=None):
    if df.empty or coluna not in df.columns:
        st.info(f"Sem dados para {titulo.lower()}.")
        return

    contagem = df[coluna].fillna("Não informado").value_counts().reset_index()
    contagem.columns = [coluna, "total"]
    if top:
        contagem = contagem.head(top)

    if orientacao == "h":
        fig = px.bar(contagem, x="total", y=coluna, orientation="h", text="total", title=titulo)
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
    else:
        fig = px.bar(contagem, x=coluna, y="total", text="total", title=titulo)
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)


def aplicar_filtros(df_equipes, df_participantes):
    st.sidebar.header("Filtros")

    if df_equipes.empty:
        return df_equipes, df_participantes

    status_opcoes = sorted(df_equipes["status"].dropna().unique().tolist())
    status_sel = st.sidebar.multiselect("Status da inscrição", status_opcoes, default=status_opcoes)

    uf_opcoes = sorted(df_equipes["tutor_estado"].dropna().unique().tolist())
    uf_sel = st.sidebar.multiselect("UF do tutor", uf_opcoes, default=uf_opcoes)

    termo = st.sidebar.text_input("Buscar equipe/tutor", "").strip().lower()

    datas_validas = df_equipes["criado_em"].dropna()
    if not datas_validas.empty:
        data_min = datas_validas.min().date()
        data_max = datas_validas.max().date()
        intervalo = st.sidebar.date_input("Data de criação", value=(data_min, data_max), min_value=data_min, max_value=data_max)
    else:
        intervalo = None

    filtrado = df_equipes.copy()
    if status_sel:
        filtrado = filtrado[filtrado["status"].isin(status_sel)]
    if uf_sel:
        filtrado = filtrado[filtrado["tutor_estado"].isin(uf_sel)]
    if termo:
        mask = (
            filtrado["equipe_nome"].fillna("").str.lower().str.contains(termo, regex=False)
            | filtrado["tutor_nome"].fillna("").str.lower().str.contains(termo, regex=False)
            | filtrado["tutor_email"].fillna("").str.lower().str.contains(termo, regex=False)
        )
        filtrado = filtrado[mask]
    if intervalo and len(intervalo) == 2:
        inicio, fim = intervalo
        filtrado = filtrado[
            (filtrado["criado_em"].dt.date >= inicio)
            & (filtrado["criado_em"].dt.date <= fim)
        ]

    ids = set(filtrado["inscricao_id"].dropna().tolist())
    participantes_filtrado = df_participantes[df_participantes["inscricao_id"].isin(ids)].copy()
    return filtrado, participantes_filtrado


def main():
    st.title("📊 Painel de Inscrições OIAA")
    st.caption("Dashboard local gerado a partir de `dados/inscricoes-detalhadas.json`.")

    with st.sidebar:
        st.header("Fonte")
        caminho = st.text_input("Arquivo JSON", str(DATA_PADRAO))
        if st.button("Recarregar dados"):
            carregar_json.clear()

        st.divider()
        st.header("Atualizar pela API")
        st.caption("Faz login no endpoint `/api/auth/login`, baixa a lista e busca o detalhe de cada inscrição.")
        with st.form("form_atualizar_api"):
            base_url = st.text_input("Base URL", valor_secreto("OIAA_BASE_URL", BASE_URL_PADRAO))
            email = st.text_input("E-mail", valor_secreto("OIAA_EMAIL"))
            senha = st.text_input("Senha", valor_secreto("OIAA_SENHA"), type="password")
            tamanho = st.number_input("Tamanho da página", min_value=1, max_value=500, value=100, step=10)
            max_paginas = st.number_input("Máx. páginas", min_value=1, max_value=500, value=100, step=10)
            atualizar_api = st.form_submit_button("Login e atualizar JSON")

        if atualizar_api:
            if not email or not senha:
                st.error("Informe e-mail e senha para atualizar pela API.")
            else:
                try:
                    with st.spinner("Autenticando e baixando inscrições..."):
                        dados_api = baixar_inscricoes_api(base_url, email, senha, int(tamanho), int(max_paginas))
                        salvar_json(Path(caminho), dados_api)
                        carregar_json.clear()
                    st.success(f"Dados atualizados: {dados_api['totalDetalhes']} inscrições detalhadas.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Falha ao atualizar pela API: {exc}")

    caminho_path = Path(caminho)
    if not caminho_path.exists():
        st.error(f"Arquivo não encontrado: {caminho}")
        st.stop()

    data = carregar_json(str(caminho_path))
    df_equipes, df_participantes = montar_dataframes(data)

    st.sidebar.caption(f"Gerado em: {data.get('geradoEm', 'não informado')}")

    df_equipes_f, df_participantes_f = aplicar_filtros(df_equipes, df_participantes)

    total_equipes = len(df_equipes_f)
    total_enviadas = int((df_equipes_f["status"] == "ENVIADA").sum()) if not df_equipes_f.empty else 0
    total_rascunho = int((df_equipes_f["status"] == "RASCUNHO").sum()) if not df_equipes_f.empty else 0
    total_participantes = len(df_participantes_f)
    participantes_cadastrados = int(df_participantes_f["cadastro_preenchido"].sum()) if not df_participantes_f.empty else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Equipes", total_equipes)
    c2.metric("Enviadas", total_enviadas)
    c3.metric("Rascunhos", total_rascunho)
    c4.metric("Participantes", total_participantes)
    c5.metric("Cadastros completos", participantes_cadastrados)

    abas = st.tabs(["Visão geral", "Geografia", "Participantes", "Documentos", "Tabelas"])

    with abas[0]:
        col1, col2 = st.columns(2)
        with col1:
            grafico_contagem(df_equipes_f, "status_rotulo", "Inscrições por status")
        with col2:
            grafico_contagem(df_equipes_f, "categoria_rotulo", "Equipes por categoria")

        if not df_equipes_f.empty:
            serie = (
                df_equipes_f.dropna(subset=["data_criacao"])
                .groupby("data_criacao")
                .size()
                .reset_index(name="inscricoes")
                .sort_values("data_criacao")
            )
            fig = px.line(serie, x="data_criacao", y="inscricoes", markers=True, title="Inscrições criadas por dia")
            fig.update_traces(mode="lines+markers+text", text=serie["inscricoes"], textposition="top center")
            st.plotly_chart(fig, use_container_width=True)

    with abas[1]:
        col1, col2 = st.columns(2)
        with col1:
            grafico_contagem(df_equipes_f, "tutor_estado", "Equipes por UF do tutor")
        with col2:
            grafico_contagem(df_equipes_f, "tutor_cidade", "Top cidades dos tutores", orientacao="h", top=15)

        if not df_participantes_f.empty:
            col3, col4 = st.columns(2)
            with col3:
                grafico_contagem(df_participantes_f, "estado", "Participantes por UF")
            with col4:
                grafico_contagem(df_participantes_f, "cidade", "Top cidades dos participantes", orientacao="h", top=15)

    with abas[2]:
        col1, col2 = st.columns(2)
        with col1:
            grafico_contagem(df_participantes_f, "status_participante_rotulo", "Participantes por status")
        with col2:
            grafico_contagem(df_participantes_f, "genero_rotulo", "Participantes por gênero")

        col3, col4 = st.columns(2)
        with col3:
            grafico_contagem(df_participantes_f, "serie_rotulo", "Participantes por série", orientacao="h")
        with col4:
            grafico_contagem(df_participantes_f, "tipo_escola_rotulo", "Participantes por tipo de escola")

        if not df_participantes_f.empty and df_participantes_f["idade"].notna().any():
            fig = px.histogram(df_participantes_f.dropna(subset=["idade"]), x="idade", nbins=12, title="Distribuição de idade dos participantes")
            st.plotly_chart(fig, use_container_width=True)

    with abas[3]:
        st.subheader("Documentos dos tutores")
        docs_tutor = ["tutor_doc_identidade", "tutor_doc_formacao", "tutor_doc_vinculo"]
        if not df_equipes_f.empty:
            tutor_docs = pd.DataFrame(
                {
                    "documento": ["Identidade", "Formação", "Vínculo"],
                    "enviados": [int(df_equipes_f[col].fillna(False).sum()) for col in docs_tutor],
                    "pendentes": [int((~df_equipes_f[col].fillna(False)).sum()) for col in docs_tutor],
                }
            )
            fig = px.bar(tutor_docs, x="documento", y=["enviados", "pendentes"], barmode="group", title="Documentos dos tutores")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Documentos dos participantes")
        docs_part = ["doc_identidade", "doc_matricula"]
        if not df_participantes_f.empty:
            part_docs = pd.DataFrame(
                {
                    "documento": ["Identidade", "Matrícula"],
                    "enviados": [int(df_participantes_f[col].fillna(False).sum()) for col in docs_part],
                    "pendentes": [int((~df_participantes_f[col].fillna(False)).sum()) for col in docs_part],
                }
            )
            fig = px.bar(part_docs, x="documento", y=["enviados", "pendentes"], barmode="group", title="Documentos dos participantes")
            st.plotly_chart(fig, use_container_width=True)

    with abas[4]:
        st.subheader("Equipes")
        colunas_equipes = [
            "inscricao_id",
            "status",
            "criado_em",
            "enviada_em",
            "equipe_nome",
            "categoria",
            "total_participantes",
            "tutor_nome",
            "tutor_email",
            "tutor_estado",
            "tutor_cidade",
            "tutor_status",
        ]
        st.dataframe(df_equipes_f[colunas_equipes], use_container_width=True, hide_index=True)
        st.download_button(
            "Baixar equipes filtradas (CSV)",
            df_equipes_f.to_csv(index=False).encode("utf-8-sig"),
            file_name="equipes_filtradas.csv",
            mime="text/csv",
        )

        st.subheader("Participantes")
        colunas_part = [
            "inscricao_id",
            "equipe_nome",
            "status_participante",
            "cadastro_preenchido",
            "participante_nome",
            "nome_convidado",
            "estado",
            "cidade",
            "genero",
            "idade",
            "serie_escolar",
            "tipo_escola",
            "nome_escola",
        ]
        if not df_participantes_f.empty:
            st.dataframe(df_participantes_f[colunas_part], use_container_width=True, hide_index=True)
            st.download_button(
                "Baixar participantes filtrados (CSV)",
                df_participantes_f.to_csv(index=False).encode("utf-8-sig"),
                file_name="participantes_filtrados.csv",
                mime="text/csv",
            )
        else:
            st.info("Nenhum participante encontrado para os filtros atuais.")

    with st.expander("Aviso sobre dados pessoais"):
        st.write(
            "Este painel usa dados administrativos que podem conter informações pessoais. "
            "Compartilhe arquivos exportados apenas com pessoas autorizadas."
        )


if __name__ == "__main__":
    main()
