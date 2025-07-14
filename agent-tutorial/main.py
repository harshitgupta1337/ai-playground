import sys
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch

from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

def invoke_model(model, query):
    response = model.invoke([{"role": "user", "content": query}])
    print (response)
    return response.text()

if __name__ == "__main__":
    search = TavilySearch(max_results=2)
    tools = [search]
    
    memory = MemorySaver()

    model = init_chat_model("llama3.2:3b", model_provider="ollama")
    #model = init_chat_model("gpt-4.1", model_provider="openai")
    agent_executor = create_react_agent(model, tools, checkpointer=memory)

    config = {"configurable": {"thread_id": "threadid123"}}


    # # Simple model invocation
    # response = agent_executor.invoke({"messages": [input_message]})
    #for message in response["messages"]:
    #    message.pretty_print()

    while True:
        user_input = input("You (enter QUIT to exit): ")
        if user_input == "QUIT":
            break

        input_message = {"role": "user", "content": user_input}

        # Streaming messages
        for step in agent_executor.stream({"messages": [input_message]}, config, stream_mode="values"):
            step["messages"][-1].pretty_print()
