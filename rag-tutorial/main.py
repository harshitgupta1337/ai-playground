from langchain import hub
from langchain_openai import OpenAIEmbeddings
from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

import prompt
import vector_store

PGVECTOR_COLLECTION = "my_docs"

if __name__ == "__main__":
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

    rag_prompt = prompt.build_prompt()

    # Define state for application
    class State(TypedDict):
        question: str
        context: List[Document]
        answer: str
    
    # Define application steps
    def retrieve(state: State):
        retrieved_docs = vector_db.similarity_search(state["question"])
        return {"context": retrieved_docs}
    
    def generate(state: State):
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])
        messages = rag_prompt.invoke({"question": state["question"], "context": docs_content})
        response = llm.invoke(messages)
        return {"answer": response.content}

    # Compile application and test
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()

    question = input("Enter your question: ")
    response = graph.invoke({"question": question})
    print(response["answer"])
