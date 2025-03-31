import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (senha segura)
load_dotenv()

EMAIL_REMETENTE = 'julianooliveira@sescms.com.br'
SENHA_REMETENTE = os.getenv("EMAIL_SENHA")

ARQUIVO_CSV = 'contratos.csv'

# Inicializa o arquivo CSV se não existir
if not os.path.exists(ARQUIVO_CSV):
    df_init = pd.DataFrame(columns=['Contrato', 'DataVencimento', 'Email', 'Renovado', 'DataRenovacao'])
    df_init.to_csv(ARQUIVO_CSV, index=False)

def carregar_dados():
    return pd.read_csv(ARQUIVO_CSV)

def salvar_dados(df):
    df.to_csv(ARQUIVO_CSV, index=False)

def enviar_email(destinatario, contrato):
    msg = EmailMessage()
    msg['Subject'] = f"Alerta de Vencimento do Contrato: {contrato}"
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg.set_content(f"O contrato '{contrato}' está a 30 dias ou menos de vencer. Por favor, inicie a renovação.")

    try:
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_REMETENTE, SENHA_REMETENTE)
            smtp.send_message(msg)
            print(f"E-mail enviado para {destinatario} sobre o contrato '{contrato}'")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

def verificar_envios(df):
    hoje = datetime.today().date()
    for index, row in df.iterrows():
        if row['Renovado'] == 'Nao':
            vencimento = datetime.strptime(row['DataVencimento'], '%Y-%m-%d').date()
            if hoje >= vencimento - timedelta(days=30):
                enviar_email(row['Email'], row['Contrato'])

# Streamlit UI
st.set_page_config(page_title="Gestor de Contratos", layout="wide")
st.title("📄 Gestor de Contratos")

with st.form("form_contrato"):
    st.subheader("Cadastrar Novo Contrato")
    contrato = st.text_input("Nome do Contrato")
    data_venc = st.date_input("Data de Vencimento", format="YYYY-MM-DD")
    email = st.text_input("E-mail para notificação")
    submitted = st.form_submit_button("Salvar Contrato")

    if submitted:
        if not contrato or not email:
            st.warning("Preencha todos os campos obrigatórios.")
        else:
            df = carregar_dados()
            novo = pd.DataFrame([[contrato, data_venc.strftime('%Y-%m-%d'), email, 'Nao', '']],
                                columns=['Contrato', 'DataVencimento', 'Email', 'Renovado', 'DataRenovacao'])
            df = pd.concat([df, novo], ignore_index=True)
            salvar_dados(df)
            st.success("Contrato salvo com sucesso!")

st.divider()
st.subheader("📋 Lista de Contratos")
df = carregar_dados()
verificar_envios(df)

# Exibição da lista com botão de renovação
for i, row in df.iterrows():
    col1, col2 = st.columns([6, 1])
    with col1:
        st.write(f"**{row['Contrato']}** - Vencimento: {row['DataVencimento']} - Email: {row['Email']} - Renovado: {row['Renovado']} - Data Renovação: {row['DataRenovacao']}")
    with col2:
        if row['Renovado'] == 'Nao':
            if st.button("Renovar", key=f"renovar_{i}"):
                df.loc[i, 'Renovado'] = 'Sim'
                df.loc[i, 'DataRenovacao'] = datetime.today().strftime('%Y-%m-%d')
                salvar_dados(df)
                st.rerun()

st.dataframe(df, use_container_width=True)
