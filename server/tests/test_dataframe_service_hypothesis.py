from hypothesis import given, strategies as st
from app.services.dataframe_service import DataFrameService
import pandas as pd

class TestDataFrameServiceWithHypothesis:

    @given(st.text(), st.lists(st.integers()), st.lists(st.integers()))
    def test_add_and_get_dataframe(self, name, col1, col2):
        if len(col1) != len(col2):
            return # Skip tests where columns have different lengths
        service = DataFrameService()
        df = pd.DataFrame({'a': col1, 'b': col2})
        service.add_dataframe(name, df)
        retrieved_df = service.get_dataframe(name)
        assert df.equals(retrieved_df)
