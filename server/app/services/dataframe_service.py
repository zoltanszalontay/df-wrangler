import pandas as pd
from .storage_service import storage_service
from .milvus_service import milvus_service
from .logging_service import logging_service
from datetime import datetime


class DataFrameService:
    def __init__(self):
        self.dataframes = {}
        self.load_from_storage()

    def log(self, message):
        if logging_service.get_logging_level("dataframe") == "on":
            log_file = logging_service.get_log_file("dataframe")
            if log_file:
                with open(log_file, "a", buffering=1) as f:  # buffering=1 for line-buffering
                    f.write(f"""{datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')} - INFO - [DataFrameService] {message}
""")
            else:
                print(f"[DataFrameService] {message}")

    def health(self):
        # For now, we'll just check if there are any dataframes loaded
        if self.dataframes:
            return "OK"
        else:
            return "No dataframes loaded"

    def load_from_storage(self):
        state = storage_service.get_latest_state()
        if state:
            self.dataframes = state

    def save_to_storage(self):
        storage_service.save_state(self.dataframes)

    def add_dataframe(self, name: str, df: pd.DataFrame):
        self.dataframes[name] = df
        self.save_to_storage()
        schema_text = f"""DataFrame: {name}
Columns and Data Types:
{df.dtypes.to_string()}

First 5 rows:
{df.head().to_string()}"""
        milvus_service.add_dataframe_schema(name, schema_text)

    def get_dataframe(self, name: str) -> pd.DataFrame:
        return self.dataframes.get(name)

    def get_all_dataframes(self):
        return self.dataframes

    def rename_dataframe(self, old_name: str, new_name: str):
        if old_name in self.dataframes:
            self.dataframes[new_name] = self.dataframes.pop(old_name)
            self.save_to_storage()

    def pop_state(self):
        state = storage_service.pop_state()
        if state:
            self.dataframes = state
        return state

    def remove_dataframe(self, name: str):
        if name in self.dataframes:
            del self.dataframes[name]
            self.save_to_storage()
            return True
        return False


dataframe_service = DataFrameService()
