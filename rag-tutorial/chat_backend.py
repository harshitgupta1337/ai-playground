# backend/main.py
from langchain import hub
from langchain_openai import OpenAIEmbeddings
from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, MessagesState, StateGraph, END
from typing_extensions import List, TypedDict
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import uuid

import prompt
import vector_store

PGVECTOR_COLLECTION = "my_docs"

app = FastAPI()

# CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = init_chat_model("gpt-4o-mini", model_provider="openai")

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
vector_db, embeddings_present = vector_store.setup_vector_store_conn(PGVECTOR_COLLECTION, embeddings)

if not embeddings_present:
    loader = DirectoryLoader("./data", glob="**/*.txt")
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)

    # Index chunks
    _ = vector_db.add_documents(documents=all_splits)

@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_db.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

memory = MemorySaver()

agent_executor = create_react_agent(llm, [retrieve], checkpointer=memory)

class ChatQuery(BaseModel):
    thread_id: str
    question: str

# 🔁 Memory of agents by thread_id
thread_agents = {}

def get_agent_for_thread(thread_id: str):
    if thread_id not in thread_agents:
        # Create new chain with memory
        memory = ConversationBufferMemory(return_messages=True)
        llm = ChatOpenAI(temperature=0.7)
        agent = ConversationChain(llm=llm, memory=memory, verbose=False)
        thread_agents[thread_id] = agent
    return thread_agents[thread_id]

@app.post("/chat")
async def chat(query: ChatQuery):
    config = {"configurable": {"thread_id": query.thread_id}}
    input_message = {"role": "user", "content": query.question}
    response = agent_executor.invoke({"messages": [input_message]},
        config=config,
    )

    return {"answer": response["messages"][-1].content}

