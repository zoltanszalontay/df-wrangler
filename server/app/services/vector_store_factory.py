from .milvus_service import MilvusService
from .qdrant_service import QdrantService


def get_vector_store(config):
    provider = config.vector_store.provider
    if provider == "milvus":
        return MilvusService()
    elif provider == "qdrant":
        return QdrantService()
    else:
        raise ValueError(f"Unknown vector store provider: {provider}")
