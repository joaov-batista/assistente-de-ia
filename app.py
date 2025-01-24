import os
import tempfile
import streamlit as st
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders import PyPDFLoader

st.set_page_config(
    page_title='Assistente de Ia',
    layout='wide'
)

st.title("Assistente de Ia")
st.divider()

# Inserir chave API na barra lateral
st.sidebar.header("Configurações")
groq_api_key = st.sidebar.text_input("Insira sua API Key do Groq", type="password")

if groq_api_key:
    os.environ['GROQ_API_KEY'] = groq_api_key
else:
    st.sidebar.warning("Insira sua API Key (groq) para usar o aplicativo.")

st.sidebar.header("Carregar Documentos")
uploaded_file = st.sidebar.file_uploader("Envie seu arquivo PDF", type="pdf")
youtube_url = st.sidebar.text_input("Insira o link do YouTube")
site_url = st.sidebar.text_input("Insira o link do site")

# Inicializar o modelo do ChatGroq
if groq_api_key:
    chat = ChatGroq(model='llama-3.3-70b-versatile')
else:
    chat = None


def carregar_pdf(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file.read())
        temp_file_path = temp_file.name
    loader = PyPDFLoader(temp_file_path)
    lista_documentos = loader.load()
    documento = ''.join([doc.page_content for doc in lista_documentos])
    os.remove(temp_file_path)  # Remover o arquivo temporário após leitura
    return documento


def carregar_youtube(url):
    loader = YoutubeLoader.from_youtube_url(url, language=['pt'])
    lista_documentos = loader.load()
    documento = ''.join([doc.page_content for doc in lista_documentos])
    return documento


def carregar_site(url):
    loader = WebBaseLoader(url)
    lista_documentos = loader.load()
    documento = ''.join([doc.page_content for doc in lista_documentos])
    return documento


def gerar_resposta(mensagens, documento):
    if not chat:
        return "Modelo não configurado. Insira sua chave de API para continuar."
    
    mensagem_system = '''Você é um assistente IA, capaz de de ler pdfs, compreender
    videos do Youtube, e ler a pagina de um site,
    seu objetivo é facilitar a informação para o usuario.
    Você tem acesso às seguintes informações para formular respostas: {informações}
    Você pode formular respostas sem as {informações} também.'''
    mensagens_modelo = [("system", mensagem_system)] + mensagens
    template = ChatPromptTemplate.from_messages(mensagens_modelo)
    chain = template | chat
    try:
        return chain.invoke({'informações': documento}).content
    except Exception as e:
        return f"Erro ao gerar resposta: {str(e)}"


if "mensagens" not in st.session_state:
    st.session_state.mensagens = []
if "documento_cache" not in st.session_state:
    st.session_state.documento_cache = ""

if uploaded_file:
    st.session_state.documento_cache = carregar_pdf(uploaded_file)
    st.sidebar.success("PDF carregado com sucesso!")
if youtube_url:
    st.session_state.documento_cache = carregar_youtube(youtube_url)
    st.sidebar.success("Conteúdo do YouTube carregado com sucesso!")
if site_url:
    st.session_state.documento_cache = carregar_site(site_url)
    st.sidebar.success("Conteúdo do site carregado com sucesso!")

user_input = st.chat_input("Envie sua mensagem ou comando para o bot", key="user_input")

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["remetente"]):
        st.markdown(mensagem["conteudo"])

if user_input:
    st.session_state.mensagens.append({"remetente": "user", "conteudo": user_input})

    if chat and groq_api_key:
        resposta = gerar_resposta(
            [(mensagem["remetente"], mensagem["conteudo"]) for mensagem in st.session_state.mensagens if mensagem["remetente"] == "user"],
            st.session_state.documento_cache
        )
    else:
        resposta = "Por favor, insira sua chave de API na barra lateral para usar o bot."

    st.session_state.mensagens.append({"remetente": "assistant", "conteudo": resposta})
    with st.chat_message("assistant"):
        st.markdown(resposta)
