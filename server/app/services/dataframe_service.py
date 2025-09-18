import pandas as pd
from app.services.storage_service import storage_service

class DataFrameService:
    def __init__(self):
        self.dataframes = {}
        self.load_from_storage()

    def load_from_storage(self):
        state = storage_service.get_latest_state()
        if state:
            self.dataframes = state

    def save_to_storage(self):
        storage_service.save_state(self.dataframes)

    def add_dataframe(self, name: str, df: pd.DataFrame):
        self.dataframes[name] = df
        self.save_to_storage()

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