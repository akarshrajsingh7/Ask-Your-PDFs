import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from app_style import css, bot_template, user_template
from langchain.llms import HuggingFaceHub

class RAG_PDF:
    '''
    Class for implementing RAGs for answer questions from PDFs
    '''
    def __init__(self, pdf_docs, model = "open-source"):
        '''
        Initializing the constructor
        '''
        self.pdf_docs = pdf_docs
        if model=="open-source":
            # Open Source model to generate embeddings for the text
            self.embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
            # Open Source model to generate response (Current model used is T5-XXL)
            self.llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})
        elif model=="openai":
            # OpenAI model to generate embeddings for the text
            self.embeddings = OpenAIEmbeddings()
            # OpenAI model to generate response
            self.llm = ChatOpenAI()


    def pdf_extract_text(self):
        '''
        Extracting text from the PDFs
        '''
        text = ""
        for pdf in self.pdf_docs:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    
    def pdf_chunkize(self, text):
        '''
        Chunking the text into smaller chunks
        '''
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200, #context aware chunking
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        return chunks
    
    def pdf_vectorstore(self, text_chunks):
        '''
        Creating vector store for the text chunks
        '''
        vectorstore = FAISS.from_texts(texts=text_chunks, embedding=self.embeddings)
        return vectorstore
    
    def pdf_conversation_chain(self, vectorstore):
        memory = ConversationBufferMemory(
            memory_key='chat_history', return_messages=True)
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vectorstore.as_retriever(),
            memory=memory
        )
        return conversation_chain
    
    def activate_RAG_pipeline(self):
        # get pdf text
        raw_text = self.pdf_extract_text()

        # get the text chunks
        text_chunks = self.pdf_chunkize(raw_text)

        # create vector store
        vectorstore = self.pdf_vectorstore(text_chunks)

        # create conversation chain
        conversation_chain = self.pdf_conversation_chain(vectorstore)
        return conversation_chain