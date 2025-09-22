import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import uuid  # Import uuid for unique filenames
import urllib.parse  # Import urllib.parse for URL encoding
import pickle
import shutil
from .logging_service import logging_service
from datetime import datetime
from . import safe_exec


class CodeExecutionService:
    def __init__(self, config):
        self.config = config
        self.results_history = []
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(current_file_dir)
        server_dir = os.path.dirname(app_dir)
        project_root = os.path.dirname(server_dir)
        self.plots_dir = os.path.join(project_root, "server", "storage", "plots")
        if not os.path.exists(self.plots_dir):
            os.makedirs(self.plots_dir)

    def log(self, message):
        if logging_service.get_logging_level("code_execution") == "on":
            log_file = logging_service.get_log_file("code_execution")
            if log_file:
                with open(log_file, "a", buffering=1) as f:  # buffering=1 for line-buffering
                    f.write(
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')} - INFO - [CodeExecutionService] {message}"
                    )
            else:
                print(f"[CodeExecutionService] {message}")

    def health(self):
        # For now, this service is always considered healthy
        return "OK"

    def execute(self, code: str, dataframe_service, df_name: str = None) -> any:
        """
        Executes the given Python code in a restricted environment.
        """
        original_df_name = df_name # Store the original df_name
        df = None
        if df_name:
            df = dataframe_service.get_dataframe(df_name)
        else:
            all_dfs = dataframe_service.get_all_dataframes()
            if all_dfs:
                original_df_name = list(all_dfs.keys())[0] # Get the name of the first dataframe
                df = all_dfs[original_df_name]

        if df is None:
            # Create an empty dataframe if none are loaded
            df = pd.DataFrame()
        df_pickle = pickle.dumps(df)

        execution_result = safe_exec.run_user_code(code, df_pickle, self.config)

        if not execution_result["ok"]:
            error_message = execution_result.get('err') or execution_result.get('error')
            return f"Error executing code: {error_message}"

        final_result = None
        plot_urls = []

        if execution_result.get("plots"):
            for plot_path in execution_result["plots"]:
                plot_filename = os.path.basename(plot_path)
                new_plot_path = os.path.join(self.plots_dir, plot_filename)
                shutil.move(plot_path, new_plot_path)
                encoded_plot_filename = urllib.parse.quote(plot_filename)
                plot_urls.append(f"http://localhost:8000/plots/{encoded_plot_filename}")

        if plot_urls:
            final_result = {"plot_url": plot_urls[0]} # Support multiple plots in the future
        else:
            result = execution_result.get("result")
            if isinstance(result, (pd.Series, pd.DataFrame)):
                final_result = result
                # Update the dataframe in dataframe_service if the user code returned a dataframe
                if original_df_name:
                    dataframe_service.set_dataframe(original_df_name, final_result)
            else:
                final_result = (
                    result if result is not None else "Code executed successfully, but no result was returned."
                )

        self.results_history.append(final_result)
        if len(self.results_history) > 10:  # Keep the last 10 results
            self.results_history.pop(0)

        # If the result is a pandas DataFrame, return its string representation
        if isinstance(final_result, (pd.DataFrame, pd.Series)):
            return final_result.to_string()
        elif isinstance(final_result, list):
            return "\n".join(map(str, final_result))
        else:
            return final_result
