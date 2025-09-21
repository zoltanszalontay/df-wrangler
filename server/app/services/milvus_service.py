from pymilvus import MilvusClient, DataType
from sentence_transformers import SentenceTransformer
from .logging_service import logging_service

class MilvusService:
    def __init__(self, db_path="./milvus_app.db"):
        self.client = MilvusClient(db_path)
        self.model = SentenceTransformer('all-MiniLM-L6-v2') # A good default model
        self.vector_dim = 384 # Dimension of the embeddings from all-MiniLM-L6-v2
        self.create_collections()

    def log(self, message):
        if logging_service.get_logging_level("milvus") == "on":
            log_file = logging_service.get_log_file("milvus")
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"[MilvusService] {message}\n")
            else:
                print(f"[MilvusService] {message}")

    def health(self):
        try:
            self.client.list_collections()
            return "OK"
        except Exception as e:
            return f"Error: {e}"

    def create_collections(self):
        """
        Creates the necessary collections in Milvus if they don't exist.
        """
        collection_names = ["code_examples", "conversation_history", "dataframe_schemas"]
        for collection_name in collection_names:
            if self.client.has_collection(collection_name) and len(self.client.list_indexes(collection_name)) == 0:
                self.client.drop_collection(collection_name)

        # Schema for code examples
        if not self.client.has_collection("code_examples"):
            schema = MilvusClient.create_schema(
                auto_id=True,
                enable_dynamic_field=False,
            )
            schema.add_field("id", DataType.INT64, is_primary=True)
            schema.add_field("vector", DataType.FLOAT_VECTOR, dim=self.vector_dim)
            schema.add_field("example_text", DataType.VARCHAR, max_length=5000)
            self.client.create_collection(collection_name="code_examples", schema=schema)

            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="IVF_FLAT",
                metric_type="L2",
                params={"nlist": 128}
            )
            self.client.create_index(collection_name="code_examples", index_params=index_params)

        # Schema for conversation history
        if not self.client.has_collection("conversation_history"):
            schema = MilvusClient.create_schema(
                auto_id=True,
                enable_dynamic_field=False,
            )
            schema.add_field("id", DataType.INT64, is_primary=True)
            schema.add_field("vector", DataType.FLOAT_VECTOR, dim=self.vector_dim)
            schema.add_field("prompt", DataType.VARCHAR, max_length=5000)
            schema.add_field("code", DataType.VARCHAR, max_length=5000)
            schema.add_field("result", DataType.VARCHAR, max_length=5000)
            self.client.create_collection(collection_name="conversation_history", schema=schema)

            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="IVF_FLAT",
                metric_type="L2",
                params={"nlist": 128}
            )
            self.client.create_index(collection_name="conversation_history", index_params=index_params)

        # Schema for dataframe schemas
        if not self.client.has_collection("dataframe_schemas"):
            schema = MilvusClient.create_schema(
                auto_id=True,
                enable_dynamic_field=False,
            )
            schema.add_field("id", DataType.INT64, is_primary=True)
            schema.add_field("vector", DataType.FLOAT_VECTOR, dim=self.vector_dim)
            schema.add_field("df_name", DataType.VARCHAR, max_length=255)
            schema.add_field("schema_text", DataType.VARCHAR, max_length=5000)
            self.client.create_collection(collection_name="dataframe_schemas", schema=schema)

            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="IVF_FLAT",
                metric_type="L2",
                params={"nlist": 128}
            )
            self.client.create_index(collection_name="dataframe_schemas", index_params=index_params)

    def add_example(self, example_text: str):
        """
        Adds a code generation example to the Milvus collection.
        """
        embedding = self.model.encode(example_text)
        data = [{"vector": embedding, "example_text": example_text}]
        self.client.insert(collection_name="code_examples", data=data)

    def search_examples(self, query_text: str, top_k: int = 3) -> list:
        """
        Searches for the most relevant code generation examples.
        """
        query_embedding = self.model.encode(query_text)
        results = self.client.search(
            collection_name="code_examples",
            data=[query_embedding],
            limit=top_k,
            output_fields=["example_text"]
        )
        return [res['entity']['example_text'] for res in results[0]]

    def add_conversation_turn(self, prompt: str, code: str, result: str):
        """
        Adds a turn of the conversation to the history collection.
        """
        embedding = self.model.encode(prompt)
        data = [{"vector": embedding, "prompt": prompt, "code": code, "result": result}]
        self.client.insert(collection_name="conversation_history", data=data)

    def search_conversation_history(self, query_text: str, top_k: int = 3) -> list:
        """
        Searches for relevant turns in the conversation history.
        """
        query_embedding = self.model.encode(query_text)
        results = self.client.search(
            collection_name="conversation_history",
            data=[query_embedding],
            limit=top_k,
            output_fields=["prompt", "code", "result"]
        )
        return [res['entity'] for res in results[0]]

    def add_dataframe_schema(self, df_name: str, schema_text: str):
        """
        Adds the schema of a dataframe to the Milvus collection.
        """
        embedding = self.model.encode(schema_text)
        data = [{"vector": embedding, "df_name": df_name, "schema_text": schema_text}]
        self.client.insert(collection_name="dataframe_schemas", data=data)

    def search_dataframe_schemas(self, query_text: str, top_k: int = 1) -> list:
        """
        Searches for the most relevant dataframe schema.
        """
        query_embedding = self.model.encode(query_text)
        results = self.client.search(
            collection_name="dataframe_schemas",
            data=[query_embedding],
            limit=top_k,
            output_fields=["df_name", "schema_text"]
        )
        return [res['entity'] for res in results[0]]

milvus_service = MilvusService()
