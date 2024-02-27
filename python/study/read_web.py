import os
import faiss
import openai
from dotenv import load_dotenv

from langchain.text_splitter import SpacyTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

import requests
from bs4 import BeautifulSoup

# ###############################################################

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]
# FAISS_DB_DIR = os.environ["FAISS_DB_DIR"]
FAISS_DB_DIR = "venv/apps/faiss_db"

# ###############################################################

def read_web(url):
    res = requests.get(url)

    soup = BeautifulSoup(res.text, "html.parser")
    text = soup.get_text()
    
    text_splitter = SpacyTextSplitter(
    chunk_size=1600,
    pipeline="ja_core_news_sm"
    )
    
    # splitted_documents = text_splitter.split_documents(text)
    splitted_documents = text_splitter.split_text(text)
    
    embedding = OpenAIEmbeddings(
    model="text-embedding-ada-002"
    )
    db2 = FAISS.load_local("/home/ubuntu/venv/venv/faiss_db", embedding)
    embeddings = OpenAIEmbeddings(
    model="text-embedding-ada-002"
    )
    db = FAISS.from_texts(splitted_documents, embeddings)
    
    db2.merge_from(db)
    db2.save_local("/home/ubuntu/venv/venv/faiss_db") 
    return db2
    
       
get_url = "https://solution.soloel.com/"

db = read_web(get_url)

print(db)