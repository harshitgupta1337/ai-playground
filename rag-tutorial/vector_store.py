from langchain_postgres import PGVector

CONNECTION = "postgresql+psycopg://langchain:langchain@localhost:5432/langchain"  # Uses psycopg3!
def setup_vector_store_conn(collection_name, embeddings):
    db = None
    try:
        db = PGVector.from_existing_index(
            embedding=embeddings,
            collection_name=collection_name,
            connection=CONNECTION,
            use_jsonb=True,
        )
    except Exception as e:
        pass

    embeddings_present = True
    if db == None:
        embeddings_present = False

        db = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=CONNECTION,
            use_jsonb=True,
        )
        
    return db, embeddings_present
