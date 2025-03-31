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
COLUNAS_PADRAO = ['Contrato', 'DataVencimento', 'Email', 'Renovado', 'DataRenovacao', 'RenovadoPor']

# Função para enviar e-mail
def enviar_email(destinatario, assunto, conteudo_html):
    msg = EmailMessage()
    msg['Subject'] = assunto
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg.set_content("Este e-mail requer um cliente compatível com HTML.")
    msg.add_alternative(conteudo_html, subtype='html')

    with smtplib.SMTP('smtp.office365.com', 587) as smtp:
        smtp.starttls()
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
        df = pd.read_csv(ARQUIVO_CSV)
        for col in COLUNAS_PADRAO:
            if col not in df.columns:
                df[col] = ''
        return df[COLUNAS_PADRAO]
    else:
        return pd.DataFrame(columns=COLUNAS_PADRAO)

# Função para salvar contratos
def salvar_contratos(df):
    df.to_csv(ARQUIVO_CSV, index=False)

# Cadastro
st.subheader("Cadastrar Novo Contrato")
nome = st.text_input("Nome do Contrato")
data_venc = st.date_input("Data de Vencimento", format="DD/MM/YYYY")
email = st.text_input("E-mail para notificação")

if st.button("Salvar Contrato", key="salvar_btn"):
    contratos_df = carregar_contratos()
    data_venc_str = data_venc.strftime("%d/%m/%Y")
    novo = pd.DataFrame([[nome, data_venc_str, email, 'Nao', None, '']], columns=contratos_df.columns)
    contratos_df = pd.concat([contratos_df, novo], ignore_index=True)
    salvar_contratos(contratos_df)

    html = f"""
    <h3>Contrato Cadastrado com Sucesso</h3>
    <p><strong>Contrato:</strong> {nome}</p>
    <p><strong>Data de Vencimento:</strong> {data_venc_str}</p>
    <p>Este contrato foi cadastrado no sistema Gestor de Contratos.</p>
    """
    enviar_email(email, "[Gestor de Contratos] Confirmação de Cadastro", html)
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

# Exportação
with st.expander("📤 Exportar Contratos"):
    formato = st.selectbox("Formato", ["Excel", "CSV"])
    if st.button("Exportar"):
        if formato == "Excel":
            contratos_df.to_excel("contratos_exportados.xlsx", index=False)
            with open("contratos_exportados.xlsx", "rb") as f:
                st.download_button("📥 Baixar Excel", f, file_name="contratos.xlsx")
        elif formato == "CSV":
            contratos_df.to_csv("contratos_exportados.csv", index=False)
            with open("contratos_exportados.csv", "rb") as f:
                st.download_button("📥 Baixar CSV", f, file_name="contratos.csv")

# Corrigir formatação de data
def formatar_data(data):
    try:
        return datetime.strptime(str(data), "%d/%m/%Y").strftime("%d/%m/%Y")
    except:
        try:
            return datetime.strptime(str(data), "%Y-%m-%d").strftime("%d/%m/%Y")
        except:
            return data

# Tabela com ações
st.markdown("<style>div[data-testid=column] button {margin-top: 5px;} .stDataFrame {width: 100% !important;}</style>", unsafe_allow_html=True)

# Exibir a tabela sem os botões nela
st.dataframe(contratos_df)

# Mostrar botões fora da tabela, alinhados corretamente
for i, row in contratos_df.iterrows():
    col1, col2 = st.columns([10, 1])
    with col1:
        if row['Renovado'] == 'Nao':
            if st.button("✅ Renovar", key=f"renovar_{i}"):
                contratos_df.at[i, 'Renovado'] = 'Sim'
                contratos_df.at[i, 'DataRenovacao'] = datetime.now().strftime("%d/%m/%Y")
                contratos_df.at[i, 'RenovadoPor'] = st.session_state.usuario_logado
                salvar_contratos(contratos_df)

                html = f"""
                <h3>Contrato Renovado com Sucesso</h3>
                <p><strong>Contrato:</strong> {row['Contrato']}</p>
                <p><strong>Data de Vencimento:</strong> {row['DataVencimento']}</p>
                <p><strong>Data da Renovação:</strong> {datetime.now().strftime('%d/%m/%Y')}</p>
                <p>O contrato foi renovado no sistema Gestor de Contratos por <strong>{st.session_state.usuario_logado}</strong>.</p>
                """
                enviar_email(row['Email'], "[Gestor de Contratos] Renovação Concluída", html)
                st.rerun()

    with col2:
        if st.session_state.usuario_logado == 'juliano':
            if st.button("🗑️ Excluir", key=f"excluir_{i}"):
                contratos_df = contratos_df.drop(index=i).reset_index(drop=True)
                salvar_contratos(contratos_df)
                st.warning("Contrato excluído.")
                st.rerun()

# Agendamento para envio de lembretes
def verificar_lembretes():
    df = carregar_contratos()
    hoje = datetime.now().date()
    for _, row in df.iterrows():
        if row['Renovado'] == 'Nao':
            try:
                data_venc = datetime.strptime(row['DataVencimento'], "%d/%m/%Y").date()
                if (data_venc - hoje).days == 30:
                    html = f"""
                    <h3>Lembrete: Contrato prestes a vencer</h3>
                    <p><strong>Contrato:</strong> {row['Contrato']}</p>
                    <p><strong>Data de Vencimento:</strong> {data_venc.strftime('%d/%m/%Y')}</p>
                    <p>O prazo para vencimento deste contrato está se aproximando. Por favor, avalie a renovação.</p>
                    """
                    enviar_email(row['Email'], "[Gestor de Contratos] Alerta de Vencimento", html)
            except:
                pass

schedule.every().day.at("06:00").do(verificar_lembretes)

def agendador():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=agendador, daemon=True).start()

# Botão de logout
st.markdown("---")
if st.button("🔓 Sair", key="logout_btn"):
    st.session_state.usuario_logado = None
    st.rerun()


