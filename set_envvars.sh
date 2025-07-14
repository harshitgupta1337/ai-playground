SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

export LANGSMITH_TRACING="true"
export LANGSMITH_API_KEY=$(cat $SCRIPT_DIR/.keys/langsmith-key1)

export OPENAI_API_KEY=$(cat $SCRIPT_DIR/.keys/openai)

export TAVILY_API_KEY=$(cat $SCRIPT_DIR/.keys/tavilysearch-default)
