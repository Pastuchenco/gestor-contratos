import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

EMAIL_REMETENTE = 'julianooliveira@sescms.com.br'
SENHA_REMETENTE = os.getenv("EMAIL_SENHA")

ARQUIVO_CSV = 'contratos.csv'

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
    if st.button("Entrar"):
        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            st.session_state.usuario_logado = usuario
            st.success(f"Bem-vindo, {usuario}!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# Após login
st.title("📄 Gestor de Contratos")
st.markdown("---")

# Função para carregar contratos
def carregar_contratos():
    if os.path.exists(ARQUIVO_CSV):
        return pd.read_csv(ARQUIVO_CSV)
    else:
        return pd.DataFrame(columns=['Contrato', 'DataVencimento', 'Email', 'Renovado', 'DataRenovacao', 'RenovadoPor'])

# Função para salvar contratos
def salvar_contratos(df):
    df.to_csv(ARQUIVO_CSV, index=False)

# Cadastro
st.subheader("Cadastrar Novo Contrato")
nome = st.text_input("Nome do Contrato")
data_venc = st.date_input("Data de Vencimento", format="YYYY-MM-DD")
email = st.text_input("E-mail para notificação")

if st.button("Salvar Contrato"):
    contratos_df = carregar_contratos()
    novo = pd.DataFrame([[nome, data_venc, email, 'Nao', None, '']], columns=contratos_df.columns)
    contratos_df = pd.concat([contratos_df, novo], ignore_index=True)
    salvar_contratos(contratos_df)
    st.success("Contrato salvo com sucesso!")
    st.experimental_rerun()

st.markdown("---")

# Exibir lista
st.subheader("📋 Lista de Contratos")
contratos_df = carregar_contratos()

for i, row in contratos_df.iterrows():
    st.markdown(f"**{row['Contrato']}** - Vencimento: {row['DataVencimento']} - Email: {row['Email']} - Renovado: {row['Renovado']} - Data Renovação: {row['DataRenovacao']}")
    col1, col2 = st.columns([1, 1])
    with col1:
        if row['Renovado'] == 'Nao':
            if st.button("Renovar", key=f"renovar_{i}"):
                contratos_df.at[i, 'Renovado'] = 'Sim'
                contratos_df.at[i, 'DataRenovacao'] = datetime.now().strftime("%Y-%m-%d")
                contratos_df.at[i, 'RenovadoPor'] = st.session_state.usuario_logado
                salvar_contratos(contratos_df)
                st.experimental_rerun()
    with col2:
        if st.button("Excluir", key=f"excluir_{i}"):
            contratos_df = contratos_df.drop(index=i).reset_index(drop=True)
            salvar_contratos(contratos_df)
            st.warning("Contrato excluído.")
            st.experimental_rerun()

st.dataframe(contratos_df)

# Botão de logout
st.markdown("---")
if st.button("🔓 Sair"):
    st.session_state.usuario_logado = None
    st.experimental_rerun()

