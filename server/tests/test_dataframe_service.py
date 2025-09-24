import pandas as pd
import pytest
from app.services.dataframe_service import DataFrameService
from app.services.vector_store_factory import get_vector_store
from omegaconf import OmegaConf


@pytest.fixture(params=["milvus", "qdrant"])
def vector_store_provider(request):
    return request.param


@pytest.fixture
def dataframe_service(vector_store_provider):
    cfg = OmegaConf.create({"vector_store": {"provider": vector_store_provider}})
    vector_store = get_vector_store(cfg)
    service = DataFrameService()
    service.set_vector_store(vector_store)
    return service


def test_add_and_get_dataframe(dataframe_service):
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    dataframe_service.add_dataframe("test_df", df)
    retrieved_df = dataframe_service.get_dataframe("test_df")
    assert df.equals(retrieved_df)