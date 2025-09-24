from qdrant_client.http.models import Distance, VectorParams, PointStruct


class QdrantService:
    def __init__(self, db_path=":memory:"):
        self.client = QdrantClient(db_path)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")  # A good default model
        self.vector_dim = 384  # Dimension of the embeddings from all-MiniLM-L6-v2
        self.create_collections()

    def create_collections(self):
        self.client.recreate_collection(
            collection_name="code_examples",
            vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE),
        )
        self.client.recreate_collection(
            collection_name="conversation_history",
            vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE),
        )
        self.client.recreate_collection(
            collection_name="dataframe_schemas",
            vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE),
        )

    def add_example(self, example_text: str):
        embedding = self.model.encode(example_text)
        self.client.upsert(
            collection_name="code_examples",
            points=[PointStruct(vector=embedding, payload={"example_text": example_text})],
        )

    def search_examples(self, query_text: str, top_k: int = 3) -> list:
        query_embedding = self.model.encode(query_text)
        search_result = self.client.search(
            collection_name="code_examples",
            query_vector=query_embedding,
            limit=top_k,
        )
        return [hit.payload["example_text"] for hit in search_result]

    def add_conversation_turn(self, prompt: str, code: str, result: str):
        embedding = self.model.encode(prompt)
        self.client.upsert(
            collection_name="conversation_history",
            points=[
                PointStruct(
                    vector=embedding,
                    payload={"prompt": prompt, "code": code, "result": result},
                )
            ],
        )

    def search_conversation_history(self, query_text: str, top_k: int = 3) -> list:
        query_embedding = self.model.encode(query_text)
        search_result = self.client.search(
            collection_name="conversation_history",
            query_vector=query_embedding,
            limit=top_k,
        )
        return [hit.payload for hit in search_result]

    def add_dataframe_schema(self, df_name: str, schema_text: str):
        embedding = self.model.encode(schema_text)
        self.client.upsert(
            collection_name="dataframe_schemas",
            points=[
                PointStruct(
                    vector=embedding,
                    payload={"df_name": df_name, "schema_text": schema_text},
                )
            ],
        )

    def search_dataframe_schemas(self, query_text: str, top_k: int = 1) -> list:
        query_embedding = self.model.encode(query_text)
        search_result = self.client.search(
            collection_name="dataframe_schemas",
            query_vector=query_embedding,
            limit=top_k,
        )
        return [hit.payload for hit in search_result]

    def health(self):
        return "OK"
