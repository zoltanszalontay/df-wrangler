import pickle
import os
from datetime import datetime
from .logging_service import logging_service


class StorageService:
    def __init__(self, storage_dir_relative_to_project_root="server/storage"):
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(current_file_dir)
        server_dir = os.path.dirname(app_dir)
        project_root = os.path.dirname(server_dir)
        self.storage_dir = os.path.join(project_root, storage_dir_relative_to_project_root)
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def log(self, message):
        if logging_service.get_logging_level("storage") == "on":
            log_file = logging_service.get_log_file("storage")
            if log_file:
                with open(log_file, "a", buffering=1) as f:  # buffering=1 for line-buffering
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')} - INFO - [StorageService] {message}\n")
            else:
                print(f"[StorageService] {message}")

    def health(self):
        # For now, we'll just check if the storage directory exists
        if os.path.exists(self.storage_dir):
            return "OK"
        else:
            return "Error: Storage directory not found"

    def save_state(self, state):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        file_path = os.path.join(self.storage_dir, f"state_{timestamp}.pkl")
        with open(file_path, "wb") as f:
            pickle.dump(state, f)

    def get_latest_state(self):
        files = sorted([f for f in os.listdir(self.storage_dir) if f.endswith(".pkl")], reverse=True)
        if not files:
            return None
        file_path = os.path.join(self.storage_dir, files[0])
        # Check if the latest path is a file indeed, not a directory
        if not os.path.isfile(file_path):
            return None
        with open(file_path, "rb") as f:
            return pickle.load(f)

    def pop_state(self):
        files = sorted([f for f in os.listdir(self.storage_dir) if f.endswith(".pkl")], reverse=True)
        if len(files) < 2:
            return None  # Cannot pop the initial state
        file_to_remove = os.path.join(self.storage_dir, files[0])
        os.remove(file_to_remove)
        return self.get_latest_state()


storage_service = StorageService()
