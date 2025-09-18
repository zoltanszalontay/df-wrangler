import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class CodeExecutionService:
    def __init__(self):
        self.results_history = []

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
            "last_result": self.results_history[-1] if self.results_history else None
        }
        
        try:
            # Execute the code
            exec(code, global_vars)
            # The result of the code is expected to be in the 'result' variable
            result = global_vars.get("result", "Code executed successfully, but no result was returned.")
            
            self.results_history.append(result)
            if len(self.results_history) > 10: # Keep the last 10 results
                self.results_history.pop(0)

            # If the result is a pandas DataFrame, return its string representation
            if isinstance(result, pd.DataFrame):
                return result.to_string()
            else:
                return result

        except Exception as e:
            return f"Error executing code: {e}"

code_execution_service = CodeExecutionService()