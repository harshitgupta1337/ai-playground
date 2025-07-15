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
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

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

    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query."""
        retrieved_docs = vector_db.similarity_search(query, k=2)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs

    # Step 1: Generate an AIMessage that may include a tool-call to be sent.
    def query_or_respond(state: MessagesState):
        """Generate tool call for retrieval or respond."""
        llm_with_tools = llm.bind_tools([retrieve])
        response = llm_with_tools.invoke(state["messages"])
        # MessagesState appends messages to state instead of overwriting
        return {"messages": [response]}
    
    
    # Step 2: Execute the retrieval.
    tools = ToolNode([retrieve])
    
    
    # Step 3: Generate a response using the retrieved content.
    def generate(state: MessagesState):
        """Generate answer."""
        # Get generated ToolMessages
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]
    
        # Format into prompt
        docs_content = "\n\n".join(doc.content for doc in tool_messages)
        system_message_content = (
            "You are a wise and compassionate teacher well-versed in the teachings of the Bhagavad Gita. Below is an excerpt or collection of verses from the Bhagavad Gita, possibly accompanied by commentary or contextual explanations. Use this content as your primary source of truth when answering the user's question. Your goal is to provide clear, respectful, and insightful answers that remain faithful to the original spirit and meaning of the Gita. Please keep the answer relatively short. If the question cannot be answered based on the provided context, say so politely and suggest that the question may require more verses or philosophical commentary."
            "\n\n"
            f"{docs_content}"
        )
        conversation_messages = [
            message
            for message in state["messages"]
            if message.type in ("human", "system")
            or (message.type == "ai" and not message.tool_calls)
        ]
        prompt = [SystemMessage(system_message_content)] + conversation_messages
    
        # Run
        response = llm.invoke(prompt)
        return {"messages": [response]}

    # Build the graph
    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node(query_or_respond)
    graph_builder.add_node(tools)
    graph_builder.add_node(generate)
    
    graph_builder.set_entry_point("query_or_respond")
    graph_builder.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    graph_builder.add_edge("tools", "generate")
    graph_builder.add_edge("generate", END)
    
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    # Specify an ID for the thread
    config = {"configurable": {"thread_id": "abc123"}}

    while True:
        user = input("You: ")
        if user == "quit":
            break
        
        input_message = {"role": "user", "content": user}
        for step in graph.stream(
            {"messages": [input_message]},
            stream_mode="values",
            config=config,
        ):
            step["messages"][-1].pretty_print()
