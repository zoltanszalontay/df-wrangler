from hypothesis import given, strategies as st
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


@given(st.text(), st.lists(st.integers()), st.lists(st.integers()))
def test_add_and_get_dataframe_hypothesis(dataframe_service, name, col1, col2):
    if len(col1) != len(col2):
        return  # Skip tests where columns have different lengths
    df = pd.DataFrame({'a': col1, 'b': col2})
    dataframe_service.add_dataframe(name, df)
    retrieved_df = dataframe_service.get_dataframe(name)
    assert df.equals(retrieved_df)