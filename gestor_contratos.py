import streamlit as st
import pandas as pd
from datetime import datetime
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuração da autenticação com o Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google-sheets-credentials.json", scope)
client = gspread.authorize(creds)

# Nome da planilha do Google Sheets
NOME_PLANILHA = "GestorContratos"
ABA = "Contratos"

# Conecta à planilha
sheet = client.open(NOME_PLANILHA).worksheet(ABA)

# Carrega contratos do Google Sheets
@st.cache_data(show_spinner=False)
def carregar_contratos():
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)
    if df.empty:
        df = pd.DataFrame(columns=['Contrato', 'DataVencimento', 'Email', 'Renovado', 'DataRenovacao', 'RenovadoPor'])
    return df

# Salva contratos no Google Sheets
def salvar_contratos(df):
    sheet.clear()
    sheet.append_row(['Contrato', 'DataVencimento', 'Email', 'Renovado', 'DataRenovacao', 'RenovadoPor'])
    for _, row in df.iterrows():
        sheet.append_row(row.fillna('').tolist())

# Autenticação simples
USUARIOS = {
    "juliano": "senha123",
    "genilson": "senha456"
}

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if st.session_state.usuario_logado is None:
    st.title("🔐 Login - Gestor de Contratos")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar", key="entrar_btn"):
        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            st.session_state.usuario_logado = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# Após login
st.title("📄 Gestor de Contratos")
st.markdown("---")

# Cadastro
st.subheader("Cadastrar Novo Contrato")
nome = st.text_input("Nome do Contrato")
data_venc = st.date_input("Data de Vencimento", format="DD/MM/YYYY")
email = st.text_input("E-mail para notificação")

if st.button("Salvar Contrato", key="salvar_btn"):
    contratos_df = carregar_contratos()
    data_venc_str = data_venc.strftime("%d/%m/%Y")
    novo = pd.DataFrame([[nome, data_venc_str, email, 'Nao', '', '']], columns=contratos_df.columns)
    contratos_df = pd.concat([contratos_df, novo], ignore_index=True)
    salvar_contratos(contratos_df)
    st.success("Contrato salvo com sucesso!")
    st.rerun()

st.markdown("---")

# Exibir lista
st.subheader("📋 Lista de Contratos")
contratos_df = carregar_contratos()

# Campo de pesquisa
with st.expander("🔍 Filtro de Busca"):
    filtro_nome = st.text_input("Buscar por nome do contrato")
    filtro_data = st.text_input("Buscar por data de vencimento (dd/mm/aaaa)")
    filtro_status = st.selectbox("Status da Renovação", ["Todos", "Renovado", "Não Renovado"])

    if filtro_nome:
        contratos_df = contratos_df[contratos_df['Contrato'].str.contains(filtro_nome, case=False, na=False)]
    if filtro_data:
        contratos_df = contratos_df[contratos_df['DataVencimento'].str.contains(filtro_data, na=False)]
    if filtro_status == "Renovado":
        contratos_df = contratos_df[contratos_df['Renovado'] == 'Sim']
    elif filtro_status == "Não Renovado":
        contratos_df = contratos_df[contratos_df['Renovado'] == 'Nao']

# Exibir contratos um por um
for i, row in contratos_df.iterrows():
    st.markdown(f"""
    **Contrato:** {row['Contrato']}  
    **Vencimento:** {row['DataVencimento']}  
    **Email:** {row['Email']}  
    **Renovado:** {row['Renovado']}  
    **Data Renovação:** {row['DataRenovacao'] if row['DataRenovacao'] else '---'}  
    **Renovado por:** {row['RenovadoPor'] if row['RenovadoPor'] else '---'}
    """)

    if row['Renovado'] == 'Nao':
        if st.button("✅ Renovar", key=f"renovar_{i}"):
            contratos_df.at[i, 'Renovado'] = 'Sim'
            contratos_df.at[i, 'DataRenovacao'] = datetime.now().strftime("%d/%m/%Y")
            contratos_df.at[i, 'RenovadoPor'] = st.session_state.usuario_logado
            salvar_contratos(contratos_df)
            st.rerun()

    if st.session_state.usuario_logado == 'juliano':
        if st.button("🗑️ Excluir", key=f"excluir_{i}"):
            contratos_df = contratos_df.drop(index=i).reset_index(drop=True)
            salvar_contratos(contratos_df)
            st.warning("Contrato excluído.")
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

# Botão de logout
st.markdown("---")
if st.button("🔓 Sair", key="logout_btn"):
    st.session_state.usuario_logado = None
    st.rerun()


