import os
import faiss
import openai
from dotenv import load_dotenv

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import SpacyTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

# ###############################################################

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]
# FAISS_DB_DIR = os.environ["FAISS_DB_DIR"]
FAISS_DB_DIR = "venv/apps/faiss_db"

# ###############################################################

def to_vec(pdf):
    loader = PyMuPDFLoader(pdf)
    documents = loader.load()

    text_splitter = SpacyTextSplitter(
        chunk_size=1600,
        pipeline="ja_core_news_sm"
    )
    splitted_documents = text_splitter.split_documents(documents)
    
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002"
    )

    db = FAISS.from_documents(splitted_documents, embeddings)
    return db

to_vec("/home/ubuntu/venv/venv/article/【新】もみかる_オーナーマニュアル.pdf .pdf")
