from langchain_tavily import TavilySearch

search = TavilySearch(max_results=2)
search_results = search.invoke("What events are going on in Boston on the 4th of July 2025?")
print(search_results)

tools = [search]
