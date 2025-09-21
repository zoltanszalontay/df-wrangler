import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import uuid  # Import uuid for unique filenames
import urllib.parse  # Import urllib.parse for URL encoding
from .logging_service import logging_service
from datetime import datetime


class CodeExecutionService:
    def __init__(self):
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

    def execute(self, code: str, dataframe_service) -> any:
        """
        Executes the given Python code in a restricted environment.
        """
        # Create a restricted global environment
        global_vars = {
            "dataframe_service": dataframe_service,
            "pd": pd,
            "np": np,
            "plt": plt,
            "results_history": self.results_history,
            "last_result": self.results_history[-1] if self.results_history else None,
            "plots_dir": self.plots_dir,
        }

        try:
            # Get the number of figures before execution
            initial_fignums = plt.get_fignums()

            # Execute the code
            exec(code, global_vars)

            # Check if any new figures were created or existing ones modified
            current_fignums = plt.get_fignums()

            plot_url = None
            if current_fignums:  # If there are any open figures
                # Assuming the last created figure is the one we want to save
                # This might need refinement if multiple plots are generated
                fig = plt.figure(current_fignums[-1])

                # Generate a unique filename for the plot
                plot_filename = f"plot_{uuid.uuid4().hex}.jpg"
                plot_filepath = os.path.join(self.plots_dir, plot_filename)

                # Save the plot
                fig.savefig(plot_filepath)
                plt.close(fig)  # Close the figure to free memory

                # Construct the URL for the plot
                # Assuming the server is running on localhost:8000 and static files are served from /plots
                encoded_plot_filename = urllib.parse.quote(plot_filename)
                plot_url = f"http://localhost:8000/plots/{encoded_plot_filename}"

            final_result = None
            if plot_url:
                final_result = {"plot_url": plot_url}
            else:
                result = global_vars.get("result")
                if isinstance(result, (pd.Series, pd.DataFrame)):
                    final_result = result
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

        except Exception as e:
            return f"Error executing code: {e}"


code_execution_service = CodeExecutionService()
