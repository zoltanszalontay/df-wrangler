import unittest
import pandas as pd
from app.services.dataframe_service import DataFrameService

class TestDataFrameService(unittest.TestCase):

    def test_add_and_get_dataframe(self):
        service = DataFrameService()
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        service.add_dataframe("test_df", df)
        retrieved_df = service.get_dataframe("test_df")
        self.assertTrue(df.equals(retrieved_df))

if __name__ == '__main__':
    unittest.main()
