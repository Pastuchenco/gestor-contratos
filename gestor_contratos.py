import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import schedule
import time
import threading

# Carrega variáveis de ambiente
load_dotenv()

EMAIL_REMETENTE = 'julianooliveira@sescms.com.br'
SENHA_REMETENTE = os.getenv("EMAIL_SENHA")
ARQUIVO_CSV = 'contratos.csv'

# Função para enviar e-mail
def enviar_email(destinatario, assunto, conteudo_html):
    msg = EmailMessage()
    msg['Subject'] = assunto
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg.set_content("Este e-mail requer um cliente compatível com HTML.")
    msg.add_alternative(conteudo_html, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_REMETENTE, SENHA_REMETENTE)
        smtp.send_message(msg)

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

if st.button("Salvar Contrato", key="salvar_btn"):
    contratos_df = carregar_contratos()
    novo = pd.DataFrame([[nome, data_venc, email, 'Nao', None, '']], columns=contratos_df.columns)
    contratos_df = pd.concat([contratos_df, novo], ignore_index=True)
    salvar_contratos(contratos_df)

    html = f"""
    <h3>Contrato Cadastrado com Sucesso</h3>
    <p><strong>Contrato:</strong> {nome}</p>
    <p><strong>Data de Vencimento:</strong> {data_venc}</p>
    <p>Este contrato foi cadastrado no sistema Gestor de Contratos.</p>
    """
    enviar_email(email, "[Gestor de Contratos] Confirmação de Cadastro", html)
    st.success("Contrato salvo com sucesso!")
    st.rerun()

st.markdown("---")

# Exibir lista
st.subheader("📋 Lista de Contratos")
contratos_df = carregar_contratos()

for i, row in contratos_df.iterrows():
    st.markdown(f"**{row['Contrato']}** - Vencimento: {row['DataVencimento']} - Email: {row['Email']} - Renovado: {row['Renovado']} - Data Renovação: {row['DataRenovacao']} - Renovado por: {row['RenovadoPor']}")
    col1, col2 = st.columns([1, 1])
    with col1:
        if row['Renovado'] == 'Nao':
            if st.button("Renovar", key=f"renovar_{i}"):
                contratos_df.at[i, 'Renovado'] = 'Sim'
                contratos_df.at[i, 'DataRenovacao'] = datetime.now().strftime("%Y-%m-%d")
                contratos_df.at[i, 'RenovadoPor'] = st.session_state.usuario_logado
                salvar_contratos(contratos_df)

                html = f"""
                <h3>Contrato Renovado com Sucesso</h3>
                <p><strong>Contrato:</strong> {row['Contrato']}</p>
                <p><strong>Data de Vencimento:</strong> {row['DataVencimento']}</p>
                <p>O contrato foi renovado no sistema Gestor de Contratos por <strong>{st.session_state.usuario_logado}</strong>.</p>
                """
                enviar_email(row['Email'], "[Gestor de Contratos] Renovação Concluída", html)
                st.rerun()
    with col2:
        if st.button("Excluir", key=f"excluir_{i}"):
            contratos_df = contratos_df.drop(index=i).reset_index(drop=True)
            salvar_contratos(contratos_df)
            st.warning("Contrato excluído.")
            st.rerun()

st.dataframe(contratos_df)

# Agendamento para envio de lembretes
def verificar_lembretes():
    df = carregar_contratos()
    hoje = datetime.now().date()
    for _, row in df.iterrows():
        if row['Renovado'] == 'Nao':
            data_venc = pd.to_datetime(row['DataVencimento']).date()
            if (data_venc - hoje).days == 30:
                html = f"""
                <h3>Lembrete: Contrato prestes a vencer</h3>
                <p><strong>Contrato:</strong> {row['Contrato']}</p>
                <p><strong>Data de Vencimento:</strong> {row['DataVencimento']}</p>
                <p>O prazo para vencimento deste contrato está se aproximando. Por favor, avalie a renovação.</p>
                """
                enviar_email(row['Email'], "[Gestor de Contratos] Alerta de Vencimento", html)

schedule.every().day.at("06:00").do(verificar_lembretes)

def agendador():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=agendador, daemon=True).start()

# Botão de logout (com chave única)
st.markdown("---")
if st.button("🔓 Sair", key="logout_btn"):
    st.session_state.usuario_logado = None
    st.rerun()
