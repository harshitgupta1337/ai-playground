import sys
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.2:3b")

query = "Hi!"
response = llm.invoke([{"role": "user", "content": query}])
print (response.text())
