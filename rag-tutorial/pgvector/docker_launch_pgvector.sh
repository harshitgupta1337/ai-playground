#!/bin/bash

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
mkdir -p $SCRIPT_DIR

docker run -d --name pgvector \
    -e POSTGRES_USER=langchain \
    -e POSTGRES_PASSWORD=langchain \
    -e POSTGRES_DB=langchain \
    -v $SCRIPT_DIR/pgvector_data:/var/lib/postgresql/data \
    -p 5432:5432 -d pgvector/pgvector:pg16
